# ✅ Verified structure from docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层
# ✅ Epic 20 Story 20.4: AgentService重写 - 使用真实Gemini API调用
# ✅ Verified from Context7:/googleapis/python-genai (topic: async generate content)
"""
Agent Service - Business logic for Agent operations.

This service provides async methods for Agent calls,
wrapping the Gemini API functionality with async support.

[Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层]
[Source: docs/prd/sprint-change-proposal-20251208.md - Story 20.4]
[Source: Gemini Migration - Using google.genai instead of anthropic]
"""
import asyncio
import json
import logging
import os
import re
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from cachetools import TTLCache

from app.core.failed_writes_constants import FAILED_WRITES_FILE, failed_writes_lock

# Story 12.G.2: Agent Error Type Enum
# [Source: specs/api/agent-api.openapi.yml:617-627]
from app.models.enums import AgentErrorType

# ✅ Story 12.C.1: 环境变量开关 - 上下文增强开关
# [Source: docs/plans/epic-12.C-agent-context-pollution-fix.md#Story-12.C.1]
# ✅ Fixed 2025-12-24: Default to False - enable context enrichment to fix hallucination
DISABLE_CONTEXT_ENRICHMENT = os.getenv("DISABLE_CONTEXT_ENRICHMENT", "false").lower() == "true"

if TYPE_CHECKING:
    from app.clients.gemini_client import GeminiClient
    from app.clients.graphiti_client import LearningMemoryClient

logger = logging.getLogger(__name__)

# Story 38.6: Scoring write reliability — outer timeout for fire-and-forget memory writes
# Must be >= sum of inner retry backoffs (1+2+4=7s) + 3 × per-attempt timeout (2s) + margin
MEMORY_WRITE_TIMEOUT = 15.0

# Story 38.6: FAILED_WRITES_FILE and failed_writes_lock imported from
# app.core.failed_writes_constants (shared with memory_service.py)


def _record_failed_write(
    event_type: str,
    concept_id: str,
    canvas_name: str,
    score: Optional[float],
    error_reason: str,
    concept: str = "",
    user_understanding: Optional[str] = None,
    agent_feedback: Optional[str] = None,
) -> None:
    """
    Story 38.6 AC-2: Record a failed memory write to data/failed_writes.jsonl.

    Each entry includes timestamp, event_type, concept_id, canvas_name, score, error_reason,
    plus concept, user_understanding, agent_feedback for complete recovery.
    Uses append mode so multiple failures accumulate for later recovery.
    Thread-safe via failed_writes_lock (shared with memory_service).
    """
    try:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "concept_id": concept_id,
            "canvas_name": canvas_name,
            "score": score,
            "error_reason": error_reason,
            "concept": concept,
            "user_understanding": user_understanding,
            "agent_feedback": agent_feedback,
        }
        FAILED_WRITES_FILE.parent.mkdir(parents=True, exist_ok=True)
        with failed_writes_lock:
            with open(FAILED_WRITES_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        logger.warning(
            f"[Story 38.6] Score write failed after retries, saved to fallback: {concept_id}"
        )
    except Exception as e:
        logger.error(f"[Story 38.6] Failed to write to fallback file: {e}")


class AgentType(str, Enum):
    """
    Agent类型枚举
    [Source: helpers.md#Section-1-14-agents详细说明]
    """
    BASIC_DECOMPOSITION = "basic-decomposition"
    DEEP_DECOMPOSITION = "deep-decomposition"
    QUESTION_DECOMPOSITION = "question-decomposition"
    ORAL_EXPLANATION = "oral-explanation"
    FOUR_LEVEL_EXPLANATION = "four-level-explanation"
    FOUR_LEVEL = "four-level"  # Alias for FOUR_LEVEL_EXPLANATION
    CLARIFICATION_PATH = "clarification-path"
    COMPARISON_TABLE = "comparison-table"
    EXAMPLE_TEACHING = "example-teaching"
    MEMORY_ANCHOR = "memory-anchor"
    SCORING_AGENT = "scoring-agent"
    SCORING = "scoring"  # Alias for SCORING_AGENT
    VERIFICATION_QUESTION = "verification-question-agent"
    HINT_GENERATION = "hint-generation"
    CANVAS_ORCHESTRATOR = "canvas-orchestrator"


@dataclass
class AgentResult:
    """
    Agent调用结果数据类
    [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层]
    [Enhanced: Story 12.G.2 - error_type field for classified errors]
    """
    agent_type: AgentType
    node_id: str = ""
    success: bool = True
    result: Optional[Dict[str, Any]] = None
    data: Optional[Dict[str, Any]] = None  # Alias for result
    error: Optional[str] = None
    # Story 12.G.2: Classified error type (aligned with ADR-009)
    error_type: Optional[AgentErrorType] = None
    # Story 12.G.2: Bug tracking ID (format: BUG-XXXXXXXX)
    bug_id: Optional[str] = None
    duration_ms: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Ensure data and result are synchronized"""
        if self.data is None and self.result is not None:
            self.data = self.result
        elif self.result is None and self.data is not None:
            self.result = self.data

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典

        Story 12.G.2: 包含error_type和bug_id字段用于错误追踪
        """
        return {
            "agent_type": self.agent_type.value,
            "node_id": self.node_id,
            "success": self.success,
            "result": self.result,
            "data": self.data,
            "error": self.error,
            # Story 12.G.2: 错误类型和追踪ID
            "error_type": self.error_type.value if self.error_type else None,
            "bug_id": self.bug_id,
            "duration_ms": self.duration_ms,
            "created_at": self.created_at.isoformat(),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# Story 21.3: 多重fallback文本提取和友好错误处理
# [Source: docs/prd/EPIC-21-AGENT-E2E-FLOW-FIX.md#story-21-3]
# ═══════════════════════════════════════════════════════════════════════════════

def extract_explanation_text(response: Any) -> Tuple[str, bool]:
    """
    提取explanation_text，带多重fallback机制。

    使用多个提取器按优先级尝试提取文本内容，确保即使
    API响应格式不完全匹配也能尽最大努力提取有效内容。

    支持的格式 (Story 12.G.4):
    - Gemini 原生: {"response": "..."}
    - OpenAI 兼容: {"choices": [{"message": {"content": "..."}}]}
    - 嵌套 response: {"response": {"text": "..."}} 或 {"response": {"content": "..."}}
    - Markdown JSON: ```json\\n{...}\\n```
    - 纯文本: "直接文本"

    Args:
        response: AI API响应对象（可能是dict、对象或字符串）

    Returns:
        Tuple[str, bool]: (提取的文本, 是否成功)
            - text: 提取的文本内容（去除首尾空白）
            - success: True如果成功提取到非空文本

    [Source: docs/prd/EPIC-21-AGENT-E2E-FLOW-FIX.md#story-21-3]
    [Enhanced: Story 12.G.4 - 响应格式自适应]
    """
    if response is None:
        logger.warning("extract_explanation_text: response is None")
        return "", False

    # ✅ Story 12.G.1: 条件性详细提取器日志 (AC 2)
    # [Source: docs/stories/story-12.G.1-api-response-logging.md#Task-3]
    # ✅ Verified from ADR-010: structlog dual-format logging
    from app.config import settings
    debug_enabled = settings.DEBUG_AGENT_RESPONSE

    if debug_enabled:
        logger.debug(
            "[Story 12.G.1] extract_attempt_start",
            extra={
                "input_type": type(response).__name__,
                "input_preview": str(response)[:200] if response else "None",
            }
        )

    extractors = [
        # === 精确匹配 (高优先级) ===
        # 优先级1: response字段（Gemini常用格式）
        ("response", lambda r: r.get("response") if isinstance(r, dict) and isinstance(r.get("response"), str) else None),
        # 优先级2: 嵌套 response.text (Story 12.G.4 AC2)
        # ✅ Verified from Epic 12.G definition
        ("nested_response_text", lambda r: _extract_nested_response_text(r)),
        # 优先级3: 嵌套 response.content (Story 12.G.4 AC2)
        ("nested_response_content", lambda r: _extract_nested_response_content(r)),
        # 优先级4: OpenAI 兼容格式 choices[0].message.content (Story 12.G.4 AC1)
        # ✅ Verified from Context7: OpenAI API response format
        ("openai_choices", lambda r: _extract_openai_choices(r)),
        # 优先级5: text属性（某些SDK的响应对象）
        ("text_attr", lambda r: r.text if hasattr(r, "text") and r.text else None),
        # 优先级6: dict的text字段
        ("text_key", lambda r: r.get("text") if isinstance(r, dict) else None),
        # 优先级7: dict的content字段
        ("content", lambda r: r.get("content") if isinstance(r, dict) else None),
        # 优先级8: dict的explanation字段
        ("explanation", lambda r: r.get("explanation") if isinstance(r, dict) else None),
        # 优先级9: dict的message字段
        ("message", lambda r: r.get("message") if isinstance(r, dict) else None),
        # 优先级10: dict的output字段
        ("output", lambda r: r.get("output") if isinstance(r, dict) else None),
        # === 模糊匹配 (低优先级) ===
        # 优先级11: Markdown JSON 代码块 (Story 12.G.4 AC3)
        # ✅ Verified from Python re module documentation
        ("markdown_json", lambda r: _extract_json_from_markdown(r)),
        # 优先级12: 如果response本身是字符串
        ("direct_str", lambda r: r if isinstance(r, str) else None),
        # 优先级13: 字符串化（最终fallback）
        ("stringify", lambda r: str(r) if r else None),
    ]

    for name, extractor in extractors:
        try:
            text = extractor(response)

            # ✅ Story 12.G.1: 每个提取器尝试后记录结果 (AC 2)
            # [Source: docs/stories/story-12.G.1-api-response-logging.md#Task-3.1]
            if debug_enabled:
                logger.debug(
                    "[Story 12.G.1] extractor_attempt",
                    extra={
                        "extractor_name": name,
                        "success": text is not None and len(str(text).strip()) > 0 if text else False,
                        "result_length": len(str(text)) if text else 0,
                        "result_preview": str(text)[:100] if text else None,
                    }
                )

            if text and isinstance(text, str) and text.strip():
                # Story 12.G.4 AC4: 成功时记录提取器名称
                logger.info(
                    "extraction_success",
                    extra={
                        "extractor_name": name,
                        "result_length": len(text.strip()),
                        "response_type": type(response).__name__,
                    }
                )
                return text.strip(), True
        except Exception as e:
            # ✅ Story 12.G.1: 提取器异常时记录详情 (AC 2)
            if debug_enabled:
                logger.warning(
                    "[Story 12.G.1] extractor_failed",
                    extra={
                        "extractor_name": name,
                        "error": str(e),
                    }
                )
            logger.debug(f"extract_explanation_text: Extractor '{name}' failed: {e}")

    # Story 12.G.4 AC5: 全部失败时记录原始响应 (截断至1000字符)
    # ✅ Story 12.G.1: 提取失败时记录完整原始响应内容 (AC 2, Task 3.2)
    # [Source: docs/stories/story-12.G.1-api-response-logging.md#Task-3.2]
    if debug_enabled:
        logger.error(
            "[Story 12.G.1] all_extractors_failed_debug",
            extra={
                "input_type": type(response).__name__,
                "input_content": str(response)[:1000] if response else "None",
                "extractors_tried": len(extractors),
            }
        )

    logger.warning(
        "all_extractors_failed",
        extra={
            "response_type": type(response).__name__,
            "response_preview": str(response)[:1000] if response else "None",
        }
    )
    return "", False


# ═══════════════════════════════════════════════════════════════════════════════
# Story 12.G.4: 响应格式自适应 - 辅助提取函数
# [Source: docs/stories/story-12.G.4-response-format-adaptive.md]
# ═══════════════════════════════════════════════════════════════════════════════

def _extract_nested_response_text(r: Any) -> Optional[str]:
    """
    提取嵌套格式: response.text

    支持格式: {"response": {"text": "..."}}

    [Source: Story 12.G.4 AC2]
    """
    if not isinstance(r, dict):
        return None
    response = r.get("response")
    if isinstance(response, dict):
        text = response.get("text")
        if text and isinstance(text, str):
            return text
    return None


def _extract_nested_response_content(r: Any) -> Optional[str]:
    """
    提取嵌套格式: response.content

    支持格式: {"response": {"content": "..."}}

    [Source: Story 12.G.4 AC2]
    """
    if not isinstance(r, dict):
        return None
    response = r.get("response")
    if isinstance(response, dict):
        content = response.get("content")
        if content and isinstance(content, str):
            return content
    return None


def _extract_openai_choices(r: Any) -> Optional[str]:
    """
    提取 OpenAI 兼容格式: choices[0].message.content 或 choices[0].delta.content

    支持格式:
    - 标准格式: {"choices": [{"message": {"content": "..."}}]}
    - Streaming格式: {"choices": [{"delta": {"content": "..."}}]}

    [Source: Story 12.G.4 AC1]
    ✅ Verified from Context7: OpenAI API response format
    """
    if not isinstance(r, dict):
        return None
    choices = r.get("choices")
    if not choices or not isinstance(choices, list) or len(choices) == 0:
        return None
    first_choice = choices[0]
    if not isinstance(first_choice, dict):
        return None
    # 标准格式: message.content
    message = first_choice.get("message")
    if isinstance(message, dict):
        content = message.get("content")
        if content and isinstance(content, str):
            return content
    # Streaming 格式: delta.content
    delta = first_choice.get("delta")
    if isinstance(delta, dict):
        content = delta.get("content")
        if content and isinstance(content, str):
            return content
    return None


def _extract_json_from_markdown(r: Any) -> Optional[str]:
    """
    提取 Markdown JSON 代码块中的内容

    支持格式:
    - ```json\\n{"response": "..."}\\n```
    - ```JSON\\n{...}\\n```
    - ```\\n{...}\\n```

    解析 JSON 后尝试提取常见字段: response, text, content, explanation, output

    [Source: Story 12.G.4 AC3]
    ✅ Verified from Python re module documentation
    """
    if not isinstance(r, str):
        return None

    # 匹配 ```json ... ``` 或 ```JSON ... ``` 或 ``` ... ```
    pattern = r'```(?:json|JSON)?\s*\n([\s\S]*?)\n```'
    match = re.search(pattern, r)
    if not match:
        return None

    json_str = match.group(1).strip()
    try:
        parsed = json.loads(json_str)
        # 递归提取: 如果解析出的是 dict，尝试常见字段
        if isinstance(parsed, dict):
            for key in ["response", "text", "content", "explanation", "output"]:
                if key in parsed and parsed[key]:
                    value = parsed[key]
                    if isinstance(value, str):
                        return value
            # 如果没有找到常见字段，返回整个 JSON 字符串
            return json.dumps(parsed, ensure_ascii=False)
        elif isinstance(parsed, str):
            return parsed
        return json.dumps(parsed, ensure_ascii=False)
    except json.JSONDecodeError:
        return None


def _generate_bug_id() -> str:
    """
    生成Bug追踪ID (格式: BUG-XXXXXXXX)

    Story 12.G.2 AC2: 错误响应包含bug_id便于追踪
    [Source: specs/api/agent-api.openapi.yml:648-652]

    Returns:
        str: Bug ID in format BUG-XXXXXXXX
    """
    return f"BUG-{uuid.uuid4().hex[:8].upper()}"


def create_error_response(
    error_message: str,
    source_node_id: str,
    agent_type: str,
    error_type: Optional[AgentErrorType] = None,
    details: Optional[Dict[str, Any]] = None,
    bug_id: Optional[str] = None,
    source_x: int = 0,
    source_y: int = 0,
    source_width: int = 400,
    source_height: int = 200,
) -> Dict[str, Any]:
    """
    创建友好的错误响应，在Canvas中显示错误提示节点。

    当Agent处理失败时，创建一个红色错误节点而不是返回空结果，
    让用户清楚地知道发生了什么问题。

    Story 12.G.2 增强:
    - 支持错误类型分类 (AgentErrorType)
    - 显示是否可重试
    - 包含bug_id便于追踪
    - debug模式下包含调试信息

    Args:
        error_message: 错误描述信息 (用户友好消息)
        source_node_id: 源节点ID
        agent_type: Agent类型
        error_type: AgentErrorType枚举值 (对齐ADR-009)
        details: 调试信息 (仅debug模式返回)
        bug_id: Bug追踪ID (格式: BUG-XXXXXXXX, 自动生成若未提供)
        source_x, source_y: 源节点位置
        source_width, source_height: 源节点尺寸

    Returns:
        包含错误节点和元数据的响应字典, 颜色为红色(color="1")

    [Source: docs/prd/EPIC-21-AGENT-E2E-FLOW-FIX.md#story-21-3]
    [Enhanced: Story 12.G.2 - 增强错误处理与友好提示]
    """
    # Story 12.G.2: 自动生成bug_id
    if bug_id is None:
        bug_id = _generate_bug_id()

    error_node_id = f"error-{agent_type}-{uuid.uuid4().hex[:8]}"

    # 位置在源节点右侧
    error_x = source_x + source_width + 50
    error_y = source_y

    # Story 12.G.2: 构建增强的错误节点文本
    error_type_str = error_type.value if error_type else "UNKNOWN"
    is_retryable = error_type.is_retryable if error_type else False
    retry_hint = "请重试" if is_retryable else "请检查配置后重试"

    # Story 12.G.2 AC3: 更友好的错误节点格式
    # [Story 12.I.4] Removed emoji to fix Windows GBK encoding issue
    error_text = f"""[ERROR] Agent 调用失败

**错误类型**: {error_type_str}
**错误信息**: {error_message}

**时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**请求ID**: {bug_id}

{retry_hint}"""

    logger.warning(
        f"create_error_response: Creating error node for {agent_type}",
        extra={
            "source_node_id": source_node_id,
            "agent_type": agent_type,
            "error_message": error_message,
            "error_type": error_type_str,
            "bug_id": bug_id,
            "is_retryable": is_retryable,
        }
    )

    response = {
        "created_nodes": [{
            "id": error_node_id,
            "type": "text",
            "text": error_text,
            "color": "1",  # 红色表示错误 (Story 12.G.2 AC4)
            "x": error_x,
            "y": error_y,
            "width": 400,
            "height": 250  # 增加高度以显示更多信息
        }],
        "created_edges": [{
            "id": f"edge-error-{uuid.uuid4().hex[:8]}",
            "fromNode": source_node_id,
            "toNode": error_node_id,
            "fromSide": "right",
            "toSide": "left",
            "label": "错误",
            "color": "1"  # 红色
        }],
        "error": True,
        "error_message": error_message,
        "agent_type": agent_type,
        "source_node_id": source_node_id,
        # Story 12.G.2: 新增字段
        "error_type": error_type_str,
        "is_retryable": is_retryable,
        "bug_id": bug_id,
    }

    # Story 12.G.2 AC2 & AC5: 仅在debug模式下返回详细信息
    from app.config import settings
    if settings.DEBUG_AGENT_RESPONSE and details:
        # AC5: 安全处理 - 不暴露敏感信息
        safe_details = {k: v for k, v in details.items()
                       if not any(sensitive in k.lower()
                                 for sensitive in ['key', 'secret', 'password', 'token'])}
        response["details"] = safe_details

    return response


# ═══════════════════════════════════════════════════════════════════════════════
# Story 21.4: 结构化日志记录器
# [Source: docs/prd/EPIC-21-AGENT-E2E-FLOW-FIX.md#story-21-4]
# ═══════════════════════════════════════════════════════════════════════════════

# 日志配置（可通过环境变量覆盖）
AGENT_LOG_TRUNCATE_LENGTH = int(os.getenv("AGENT_LOG_TRUNCATE_LENGTH", "500"))


class AgentCallLogger:
    """
    Agent调用日志记录器。

    提供结构化日志记录，追踪每次Agent调用的完整流程，
    包括请求参数、响应内容、延迟时间和错误信息。

    Attributes:
        agent_type: Agent类型（如 "decompose_basic"）
        node_id: 目标节点ID
        canvas_name: Canvas文件名
        start_time: 调用开始时间

    [Source: docs/prd/EPIC-21-AGENT-E2E-FLOW-FIX.md#story-21-4]
    """

    def __init__(self, agent_type: str, node_id: str, canvas_name: str = ""):
        """初始化日志记录器。"""
        self.agent_type = agent_type
        self.node_id = node_id
        self.canvas_name = canvas_name
        self.start_time = time.time()
        self.extra = {
            "agent_type": agent_type,
            "node_id": node_id,
            "canvas_name": canvas_name,
        }

    def log_request(self, request_params: Dict[str, Any]) -> None:
        """
        记录请求信息。

        Args:
            request_params: 请求参数字典（自动截断长文本）
        """
        logger.info(
            f"[Agent Call START] {self.agent_type} for node {self.node_id}",
            extra={
                **self.extra,
                "event": "agent_call_start",
                "request_params": self._summarize(request_params)
            }
        )

    def log_response(
        self,
        response: Any,
        success: bool,
        response_length: int = 0
    ) -> None:
        """
        记录响应信息。

        Args:
            response: API响应对象
            success: 是否成功
            response_length: 响应文本长度
        """
        latency_ms = int((time.time() - self.start_time) * 1000)

        log_data = {
            **self.extra,
            "event": "agent_call_end",
            "success": success,
            "latency_ms": latency_ms,
            "response_length": response_length
        }

        if success:
            logger.info(
                f"[Agent Call SUCCESS] {self.agent_type} completed in {latency_ms}ms",
                extra=log_data
            )
        else:
            # 失败时记录更多详情
            log_data["response_preview"] = self._truncate(str(response))
            logger.warning(
                f"[Agent Call FAILED] {self.agent_type} failed after {latency_ms}ms",
                extra=log_data
            )

    def log_error(self, error: Exception) -> None:
        """
        记录异常信息。

        Args:
            error: 捕获的异常对象
        """
        latency_ms = int((time.time() - self.start_time) * 1000)

        logger.error(
            f"[Agent Call ERROR] {self.agent_type} raised {type(error).__name__}",
            extra={
                **self.extra,
                "event": "agent_call_error",
                "latency_ms": latency_ms,
                "error_type": type(error).__name__,
                "error_message": str(error)[:500]
            },
            exc_info=True
        )

    @staticmethod
    def _summarize(data: Dict[str, Any], max_length: int = 200) -> str:
        """生成数据摘要。"""
        summary = str(data)
        if len(summary) > max_length:
            return summary[:max_length] + "..."
        return summary

    @staticmethod
    def _truncate(text: str, max_length: int = None) -> str:
        """截断文本。"""
        if max_length is None:
            max_length = AGENT_LOG_TRUNCATE_LENGTH
        if len(text) > max_length:
            return text[:max_length] + "... [truncated]"
        return text


# ═══════════════════════════════════════════════════════════════════════════════
# Story 21.5: 个人理解节点自动创建
# [Source: docs/prd/EPIC-21-AGENT-E2E-FLOW-FIX.md#story-21-5]
# ═══════════════════════════════════════════════════════════════════════════════

# 配置常量（可通过环境变量覆盖）
AUTO_CREATE_PERSONAL_NODE = os.getenv("AUTO_CREATE_PERSONAL_NODE", "true").lower() == "true"
PERSONAL_NODE_VERTICAL_OFFSET = int(os.getenv("PERSONAL_NODE_VERTICAL_OFFSET", "50"))
PERSONAL_NODE_PROMPT_TEXT = os.getenv(
    "PERSONAL_NODE_PROMPT_TEXT",
    "在此填写你的个人理解...\n\n💡 提示：用自己的话解释这个概念"
)

# 个人理解节点模板
PERSONAL_UNDERSTANDING_TEMPLATE = {
    "type": "text",
    "text": PERSONAL_NODE_PROMPT_TEXT,
    "width": 400,
    "height": 150,
    "color": "6"  # 黄色 - 表示待填写的个人理解区域 (修复: '6'=Yellow, '3'=Purple)
}


def create_personal_understanding_node(
    explanation_node_id: str,
    explanation_x: int,
    explanation_y: int,
    explanation_height: int,
    vertical_offset: int = None,
    custom_prompt: str = None
) -> Tuple[Dict[str, Any], str]:
    """
    创建个人理解节点。

    在解释节点下方创建一个黄色的个人理解区域，用于用户填写自己的理解，
    践行费曼学习法"用自己的话解释"的核心原则。

    Args:
        explanation_node_id: 解释节点ID (用于命名和关联)
        explanation_x: 解释节点X坐标
        explanation_y: 解释节点Y坐标
        explanation_height: 解释节点高度
        vertical_offset: 垂直间距 (默认使用配置值)
        custom_prompt: 自定义提示文字 (默认使用配置值)

    Returns:
        Tuple[node_dict, node_id]: 节点数据字典和节点ID

    [Source: docs/prd/EPIC-21-AGENT-E2E-FLOW-FIX.md#story-21-5]
    """
    if vertical_offset is None:
        vertical_offset = PERSONAL_NODE_VERTICAL_OFFSET

    personal_node_id = f"personal-{explanation_node_id[:12]}-{uuid.uuid4().hex[:6]}"

    node = {
        "id": personal_node_id,
        **PERSONAL_UNDERSTANDING_TEMPLATE,
        "x": explanation_x,  # 与解释节点水平对齐
        "y": explanation_y + explanation_height + vertical_offset  # 在解释节点下方
    }

    # 使用自定义提示文字
    if custom_prompt:
        node["text"] = custom_prompt

    logger.debug(f"Created personal understanding node {personal_node_id} at ({node['x']}, {node['y']})")
    return node, personal_node_id


def create_personal_understanding_edge(
    explanation_node_id: str,
    personal_node_id: str,
    label: str = "个人理解"
) -> Dict[str, Any]:
    """
    创建解释节点到个人理解节点的Edge连接。

    Args:
        explanation_node_id: 解释节点ID (fromNode)
        personal_node_id: 个人理解节点ID (toNode)
        label: Edge标签 (默认"个人理解")

    Returns:
        Edge数据字典

    [Source: docs/prd/EPIC-21-AGENT-E2E-FLOW-FIX.md#story-21-5]
    """
    edge = {
        "id": f"edge-personal-{uuid.uuid4().hex[:8]}",
        "fromNode": explanation_node_id,
        "toNode": personal_node_id,
        "fromSide": "bottom",
        "toSide": "top",
        "label": label,
        "color": "6"  # 黄色，与个人理解节点匹配 (修复: '6'=Yellow)
    }

    logger.debug(f"Created personal understanding edge: {explanation_node_id} → {personal_node_id}")
    return edge


# ═══════════════════════════════════════════════════════════════════════════════
# Story 21.6: Edge连接逻辑修复 - 统一Edge创建函数
# [Source: docs/prd/EPIC-21-AGENT-E2E-FLOW-FIX.md#story-21-6]
# ═══════════════════════════════════════════════════════════════════════════════

class EdgeLabels:
    """
    Edge标签常量类。

    定义所有Agent类型对应的Edge标签，确保一致性。

    [Source: docs/prd/EPIC-21-AGENT-E2E-FLOW-FIX.md#story-21-6]
    """
    BASIC_DECOMPOSE = "基础拆解"
    DEEP_DECOMPOSE = "深度拆解"
    ORAL_EXPLANATION = "口语解释"
    FOUR_LEVEL = "四层解释"
    CLARIFICATION = "澄清路径"
    COMPARISON = "对比表格"
    MEMORY_ANCHOR = "记忆锚点"
    EXAMPLE = "例题教学"
    PERSONAL_UNDERSTANDING = "个人理解"
    QUESTION = "问题拆解"
    VERIFICATION = "检验问题"

    @classmethod
    def get_label_for_type(cls, explanation_type: str) -> str:
        """
        根据解释类型获取对应的Edge标签。

        Args:
            explanation_type: Agent解释类型 (如 "oral", "four-level", "clarification")

        Returns:
            对应的中文Edge标签
        """
        type_label_map = {
            "oral": cls.ORAL_EXPLANATION,
            "four-level": cls.FOUR_LEVEL,
            "four_level": cls.FOUR_LEVEL,
            "four-level-explanation": cls.FOUR_LEVEL,
            "clarification": cls.CLARIFICATION,
            "comparison": cls.COMPARISON,
            "memory": cls.MEMORY_ANCHOR,
            "example": cls.EXAMPLE,
            "basic": cls.BASIC_DECOMPOSE,
            "deep": cls.DEEP_DECOMPOSE,
            "question": cls.QUESTION,
            "verification": cls.VERIFICATION,
        }
        return type_label_map.get(explanation_type.lower(), explanation_type)


class EdgeColors:
    """
    Edge颜色常量类。

    Obsidian Canvas颜色代码:
    - "1": 红色 (错误/问题)
    - "2": 橙色
    - "3": 黄色 (待处理/个人理解)
    - "4": 绿色 (解释/完成)
    - "5": 蓝色 (默认)
    - "6": 紫色 (部分理解)

    [Source: docs/prd/EPIC-21-AGENT-E2E-FLOW-FIX.md#story-21-6]
    """
    DEFAULT = "5"       # 蓝色 - 默认
    EXPLANATION = "4"   # 绿色 - 解释类Edge
    PERSONAL = "3"      # 黄色 - 个人理解Edge
    ERROR = "1"         # 红色 - 错误/问题
    PURPLE = "6"        # 紫色 - 部分理解


def create_edge(
    from_node_id: str,
    to_node_id: str,
    label: str = "",
    color: str = EdgeColors.DEFAULT,
    from_side: str = "right",
    to_side: str = "left"
) -> Dict[str, Any]:
    """
    统一的Edge创建函数。

    创建符合Obsidian Canvas格式的Edge数据。

    Args:
        from_node_id: 源节点ID
        to_node_id: 目标节点ID
        label: Edge标签文字
        color: Edge颜色代码 (使用EdgeColors常量)
        from_side: 源节点连接点 ("top", "bottom", "left", "right")
        to_side: 目标节点连接点 ("top", "bottom", "left", "right")

    Returns:
        Edge数据字典，可直接添加到Canvas的edges数组

    [Source: docs/prd/EPIC-21-AGENT-E2E-FLOW-FIX.md#story-21-6]
    """
    edge = {
        "id": f"edge-{uuid.uuid4().hex[:8]}",
        "fromNode": from_node_id,
        "toNode": to_node_id,
        "fromSide": from_side,
        "toSide": to_side,
    }

    # 只在有值时添加可选字段
    if label:
        edge["label"] = label
    if color and color != EdgeColors.DEFAULT:
        edge["color"] = color

    logger.debug(f"Created edge: {from_node_id} → {to_node_id} [{label}]")
    return edge


def edge_exists(
    edges: List[Dict[str, Any]],
    from_node_id: str,
    to_node_id: str,
    label: Optional[str] = None
) -> bool:
    """
    检查Edge是否已存在。

    用于避免创建重复的Edge连接。

    Args:
        edges: 现有Edge列表
        from_node_id: 源节点ID
        to_node_id: 目标节点ID
        label: Edge标签 (可选，如果提供则同时检查标签匹配)

    Returns:
        True如果存在相同的Edge，False否则

    [Source: docs/prd/EPIC-21-AGENT-E2E-FLOW-FIX.md#story-21-6]
    """
    for edge in edges:
        if (edge.get("fromNode") == from_node_id and
            edge.get("toNode") == to_node_id):
            # 如果不检查标签，或标签匹配，则认为存在
            if label is None or edge.get("label") == label:
                return True
    return False


def create_edge_if_not_exists(
    existing_edges: List[Dict[str, Any]],
    from_node_id: str,
    to_node_id: str,
    label: str = "",
    color: str = EdgeColors.DEFAULT,
    from_side: str = "right",
    to_side: str = "left"
) -> Optional[Dict[str, Any]]:
    """
    如果Edge不存在则创建。

    防止重复Edge的安全创建函数。

    Args:
        existing_edges: 现有Edge列表
        from_node_id: 源节点ID
        to_node_id: 目标节点ID
        label: Edge标签
        color: Edge颜色
        from_side: 源节点连接点
        to_side: 目标节点连接点

    Returns:
        新创建的Edge数据字典，如果Edge已存在则返回None

    [Source: docs/prd/EPIC-21-AGENT-E2E-FLOW-FIX.md#story-21-6]
    """
    if edge_exists(existing_edges, from_node_id, to_node_id, label if label else None):
        logger.debug(f"Edge already exists: {from_node_id} → {to_node_id} [{label}], skipping")
        return None

    return create_edge(
        from_node_id=from_node_id,
        to_node_id=to_node_id,
        label=label,
        color=color,
        from_side=from_side,
        to_side=to_side
    )


class AgentService:
    """
    Agent call business logic service.

    Provides async methods for invoking various learning agents
    (basic-decomposition, scoring, oral-explanation, etc.).

    [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层]
    [Source: docs/prd/sprint-change-proposal-20251208.md - Story 20.4]
    """

    def __init__(
        self,
        gemini_client: Optional["GeminiClient"] = None,
        memory_client: Optional["LearningMemoryClient"] = None,
        canvas_service: Optional[Any] = None,  # ✅ FIX: Canvas写入支持
        neo4j_client: Optional[Any] = None,  # Story 36.7: Neo4j学习记忆注入
        max_concurrent: int = 10,
        ai_config: Optional[Any] = None  # AIConfig from dependencies.py
    ):
        """
        Initialize AgentService with optional GeminiClient and LearningMemoryClient.

        ✅ Verified from Context7:/googleapis/python-genai (topic: async generate content)

        Args:
            gemini_client: GeminiClient instance for real Gemini API calls.
                          If None or not configured, raises error (no mock fallback).
            memory_client: LearningMemoryClient for querying historical learning memories.
                          If None, historical context is not included.
            canvas_service: CanvasService instance for writing nodes to Canvas.
                           If None, nodes are returned but not written to Canvas.
            neo4j_client: Neo4jClient instance for querying learning memories from Neo4j.
                         Story 36.7: Enables Neo4j-based memory queries with fallback.
                         If None, uses memory_client for historical context.
            max_concurrent: Maximum concurrent agent calls (default: 10)
            ai_config: AIConfig dataclass with provider, model, base_url, api_key.
                      Used for future multi-provider support.

        [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#依赖注入设计]
        [Source: docs/prd/sprint-change-proposal-20251208.md - Story 20.4]
        [Source: FIX-4.2 Agent调用时查询历史]
        [Source: Multi-Provider AI Architecture]
        [Source: FIX-Canvas-Write: Backend直接写入Canvas文件]
        [Source: docs/stories/36.7.story.md - AC1 Neo4jClient注入]
        """
        self._gemini_client = gemini_client
        self._memory_client = memory_client
        self._canvas_service = canvas_service  # ✅ FIX: Store canvas_service
        self._neo4j_client = neo4j_client  # Story 36.7: Store Neo4jClient
        self._max_concurrent = max_concurrent
        self._ai_config = ai_config  # Store for future multi-provider support
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._total_calls = 0
        self._active_calls = 0
        self._initialized = True
        self._use_real_api = gemini_client is not None and gemini_client.is_configured()
        # Story 12.A.4: Memory cache for AC6 (30s TTL)
        # [Source: docs/stories/story-12.A.4-memory-injection.md#Task-6]
        # NFR-P0: Bounded TTLCache replaces bare dict to prevent unbounded memory growth
        self._memory_cache: TTLCache = TTLCache(maxsize=1000, ttl=30)
        # NFR-P0: Lock for cache stampede protection
        self._memory_cache_lock = asyncio.Lock()

        # Log AI configuration
        if ai_config:
            provider = getattr(ai_config, 'provider', 'unknown')
            model = getattr(ai_config, 'model_name', 'unknown')
            logger.info(f"AgentService AI config: provider={provider}, model={model}")

        if self._use_real_api:
            logger.info("AgentService initialized with REAL AI API calls")
        else:
            logger.warning("AgentService initialized without configured AI client - API calls will fail")

        if self._memory_client:
            logger.info("AgentService will use LearningMemoryClient for historical context")
        else:
            logger.warning(
                "AgentService initialized without LearningMemoryClient - "
                "historical context fallback unavailable when Neo4j is down"
            )

        # Story 36.7: Log Neo4jClient injection status
        if self._neo4j_client:
            logger.info("AgentService will use Neo4jClient for learning memory queries")
        else:
            logger.debug("AgentService initialized without Neo4jClient - will fallback to memory_client")

        if self._canvas_service:
            logger.info("AgentService will use CanvasService for writing nodes to Canvas")
        else:
            logger.warning("AgentService initialized without CanvasService - nodes will not be written to Canvas")

        logger.debug(f"AgentService max_concurrent={max_concurrent}")

    @property
    def total_calls(self) -> int:
        """Total number of agent calls made"""
        return self._total_calls

    @property
    def active_calls(self) -> int:
        """Current number of active agent calls"""
        return self._active_calls

    # ═══════════════════════════════════════════════════════════════════════════════
    # Story 12.A.4 + Story 36.7: Learning Memory Injection with Neo4j Support
    # [Source: docs/stories/story-12.A.4-memory-injection.md]
    # [Source: docs/stories/36.7.story.md - Neo4j数据源]
    # ═══════════════════════════════════════════════════════════════════════════════

    async def _get_learning_memories(
        self,
        content: str,
        canvas_name: Optional[str] = None,
        node_id: Optional[str] = None
    ) -> str:
        """
        Get learning history with cache and timeout support.

        Story 36.7: Neo4j-based memory queries with fallback to JSON storage.
        - AC1: Uses Neo4jClient via dependency injection
        - AC2: Real Neo4j Cypher queries
        - AC3: Relevance-sorted, top 5 results
        - AC4: 30-second cache to reduce redundant queries
        - AC5: 500ms timeout to ensure responsiveness
        - AC6: Fallback to memory_client when Neo4j unavailable

        Args:
            content: The concept/content to search memories for
            canvas_name: Optional Canvas name to filter memories
            node_id: Optional node ID for context

        Returns:
            Formatted memory context string, or empty string on failure/timeout

        [Source: docs/stories/story-12.A.4-memory-injection.md#Task-4-5-6]
        [Source: docs/stories/36.7.story.md - AC1-AC6]
        [Source: ADR-0003 Graphiti Memory - 3-layer architecture]
        """
        if not content:
            return ""

        # Story 36.7 AC4: Build cache key
        cache_key = f"{canvas_name}:{node_id}:{content[:50]}"

        # NFR-P0: Check cache (TTLCache auto-evicts expired entries)
        cached_data = self._memory_cache.get(cache_key)
        if cached_data is not None:
            logger.debug(f"[Story 36.7] Memory cache HIT for key: {cache_key[:30]}...")
            if isinstance(cached_data, str):
                return cached_data
            return self._format_learning_memories(cached_data)

        # NFR-P0: Double-check locking for cache stampede protection
        async with self._memory_cache_lock:
            cached_data = self._memory_cache.get(cache_key)
            if cached_data is not None:
                logger.debug(f"[Story 36.7] Memory cache HIT (after lock) for key: {cache_key[:30]}...")
                if isinstance(cached_data, str):
                    return cached_data
                return self._format_learning_memories(cached_data)

        # Story 36.7: Determine which data source to use
        use_neo4j = self._neo4j_client and not getattr(self._neo4j_client, '_use_json_fallback', True)

        # Story 36.7 AC5: Query with 500ms timeout
        try:
            if use_neo4j:
                # Story 36.7 AC2: Real Neo4j query path
                result = await asyncio.wait_for(
                    self._query_neo4j_memories(content, canvas_name),
                    timeout=0.5  # 500ms timeout
                )
                logger.debug(f"[Story 36.7] Neo4j query returned {len(result) if result else 0} memories")
            elif self._memory_client:
                # Story 36.7 AC6: Fallback to memory_client (JSON storage)
                logger.debug("[Story 36.7] Fallback to memory_client (NEO4J_MOCK=true or Neo4j unavailable)")
                memories = await asyncio.wait_for(
                    self._memory_client.search_memories(
                        query=content[:100],
                        canvas_name=canvas_name,
                        node_id=node_id,
                        limit=5
                    ),
                    timeout=0.5
                )
                result = self._memory_client.format_for_context(memories) if memories else ""
            else:
                logger.debug("[Story 36.7] No memory source available (no Neo4jClient or memory_client)")
                return ""

            # Story 36.7 AC4: Store in cache
            if result:
                self._memory_cache[cache_key] = result
                logger.debug(f"[Story 36.7] Cached memories for key: {cache_key[:30]}...")
                return result

            return ""

        except asyncio.TimeoutError:
            logger.warning(f"[Story 36.7] Memory query timeout (500ms) for: {content[:30]}...")
            return ""
        except Exception as e:
            logger.warning(f"[Story 36.7] Memory query failed: {e}")
            return ""

    async def _query_neo4j_memories(
        self,
        content: str,
        canvas_name: Optional[str] = None
    ) -> str:
        """
        Query learning memories from Neo4j.

        Story 36.7 AC2/AC3: Executes Cypher query with relevance sorting.

        Args:
            content: Query text to search for
            canvas_name: Optional Canvas name filter

        Returns:
            Formatted memory context string

        [Source: docs/stories/36.7.story.md - Task 2]
        """
        if not self._neo4j_client:
            return ""

        # Story 36.7: Cypher query with relevance ordering (AC3)
        # [Source: docs/stories/36.7.story.md#Dev-Notes - Neo4j Cypher查询参考]
        cypher_query = """
        MATCH (m:LearningMemory)
        WHERE m.content CONTAINS $query_text
        """

        # Add canvas filter if provided
        if canvas_name:
            cypher_query += " AND m.canvas_name = $canvas_name"

        # Story 36.7 AC3: ORDER BY relevance DESC LIMIT 5
        cypher_query += """
        RETURN m.concept AS concept,
               m.timestamp AS timestamp,
               m.relevance AS relevance,
               m.score AS score,
               m.user_understanding AS user_understanding
        ORDER BY m.relevance DESC
        LIMIT 5
        """

        # Execute query
        params = {"query_text": content[:100]}
        if canvas_name:
            params["canvas_name"] = canvas_name

        try:
            results = await self._neo4j_client.run_query(cypher_query, **params)

            if not results:
                return ""

            # Format results for Agent context
            return self._format_learning_memories(results)

        except Exception as e:
            logger.warning(f"[Story 36.7] Neo4j query error: {e}")
            return ""

    def _format_learning_memories(self, memories: List[Dict[str, Any]]) -> str:
        """
        Format learning memories for Agent prompt context.

        Story 36.7: Converts Neo4j query results to formatted context string.

        Args:
            memories: List of memory dicts from Neo4j

        Returns:
            Formatted string for Agent prompt

        [Source: docs/stories/36.7.story.md#Dev-Notes - LearningMemory数据结构]
        """
        if not memories:
            return ""

        lines = ["## 历史学习记忆"]

        for m in memories:
            concept = m.get("concept", "Unknown")
            timestamp = m.get("timestamp", "")
            relevance = m.get("relevance", 0.0)
            score = m.get("score")

            # Format timestamp if present
            if timestamp:
                try:
                    from datetime import datetime
                    if isinstance(timestamp, str):
                        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                        timestamp_str = dt.strftime("%Y-%m-%d")
                    else:
                        timestamp_str = str(timestamp)[:10]
                except Exception:
                    timestamp_str = str(timestamp)[:10]
            else:
                timestamp_str = "N/A"

            # Format relevance as percentage
            relevance_str = f"{relevance * 100:.0f}%" if isinstance(relevance, (int, float)) else "N/A"

            # Format score
            score_str = str(score) if score is not None else "N/A"

            lines.append(f"- [{timestamp_str}] {concept}: 相关度{relevance_str}, 评分{score_str}")

        return "\n".join(lines)

    # ═══════════════════════════════════════════════════════════════════════════════
    # FIX-Canvas-Write: 后端直接写入节点到Canvas文件
    # [Source: Plan cozy-sniffing-shamir.md - 修复Agent结果无法显示在Canvas上的问题]
    # ═══════════════════════════════════════════════════════════════════════════════

    async def _write_nodes_to_canvas(
        self,
        canvas_name: str,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]]
    ) -> bool:
        """
        将生成的节点和边写入 Canvas 文件。

        这是解决 "Agent 生成成功但 Canvas 不显示任何节点" 问题的核心修复。
        后端直接写入 Canvas 文件，而不是依赖前端处理返回的节点数据。

        Args:
            canvas_name: Canvas 文件名 (不含 .canvas 扩展名)
            nodes: 要添加的节点列表
            edges: 要添加的边列表

        Returns:
            True 如果写入成功，False 如果失败或无 canvas_service

        [Source: Plan cozy-sniffing-shamir.md]
        [Source: FIX-Canvas-Write: Backend直接写入Canvas文件]
        """
        if not self._canvas_service:
            logger.warning("[FIX-Canvas-Write] No canvas_service available, nodes will not be written to Canvas")
            return False

        if not nodes and not edges:
            logger.debug("[FIX-Canvas-Write] No nodes or edges to write")
            return True

        try:
            # 读取现有 Canvas 数据
            canvas_data = await self._canvas_service.read_canvas(canvas_name)
            logger.debug(f"[FIX-Canvas-Write] Read canvas {canvas_name}, has {len(canvas_data.get('nodes', []))} existing nodes")

            # 添加新节点
            if nodes:
                canvas_data.setdefault("nodes", []).extend(nodes)
                logger.info(f"[FIX-Canvas-Write] Adding {len(nodes)} new nodes to {canvas_name}")

            # 添加新边
            if edges:
                canvas_data.setdefault("edges", []).extend(edges)
                logger.info(f"[FIX-Canvas-Write] Adding {len(edges)} new edges to {canvas_name}")

            # 写回 Canvas 文件
            await self._canvas_service.write_canvas(canvas_name, canvas_data)
            # [Story 12.I.4] Removed emoji to fix Windows GBK encoding
            logger.info(f"[FIX-Canvas-Write] SUCCESS: Written {len(nodes)} nodes and {len(edges)} edges to {canvas_name}")

            return True

        except Exception as e:
            # [Story 12.I.4] Removed emoji to fix Windows GBK encoding
            logger.error(f"[FIX-Canvas-Write] FAILED: Could not write nodes to canvas {canvas_name}: {e}")
            return False

    async def _call_gemini_api(
        self,
        agent_type: AgentType,
        prompt: str,
        context: Optional[str] = None,
        canvas_name: Optional[str] = None,
        node_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Call Gemini API through GeminiClient.

        ✅ Verified from Context7:/googleapis/python-genai (topic: async generate content)

        Makes a real Gemini API call. No mock fallback - raises error if not configured.

        FIX-4.2: Now queries historical learning memories and enriches context.

        Args:
            agent_type: Type of agent to invoke
            prompt: User prompt to send
            context: Optional additional context (e.g., adjacent nodes, textbook refs)
            canvas_name: Optional Canvas name for memory lookup
            node_id: Optional node ID for memory lookup

        Returns:
            Dict with agent response

        [Source: docs/prd/sprint-change-proposal-20251208.md - Story 20.4]
        [Source: FIX-4.2 Agent调用时查询历史]
        [Source: Gemini Migration - Using google.genai instead of anthropic]
        """
        # Story 12.A.4: Use refactored _get_learning_memories() with timeout and cache
        # [Source: docs/stories/story-12.A.4-memory-injection.md#Task-4]
        # ✅ Story 12.C.1: 可禁用上下文增强以消除污染
        # [Source: docs/plans/epic-12.C-agent-context-pollution-fix.md#Story-12.C.1]
        enriched_context = context or ""

        if DISABLE_CONTEXT_ENRICHMENT:
            logger.warning(
                "[Story 12.C.1] Context enrichment DISABLED - skipping memory injection. "
                "Set DISABLE_CONTEXT_ENRICHMENT=false to re-enable."
            )
        else:
            memory_context = await self._get_learning_memories(
                content=prompt or "",
                canvas_name=canvas_name,
                node_id=node_id
            )
            if memory_context:
                enriched_context = f"{enriched_context}\n\n{memory_context}" if enriched_context else memory_context
                logger.debug("Added historical memories to context via _get_learning_memories()")

        # Phase 1 FIX: 强制真实API调用，不再回退到Mock
        # [Source: C:\Users\ROG\.claude\plans\wild-purring-umbrella.md - Phase 1]
        # [Gemini Migration] Now uses GOOGLE_API_KEY instead of ANTHROPIC_API_KEY
        if not self._use_real_api:
            # FIX: Provide diagnostic information in error message
            ai_config_info = ""
            if self._ai_config:
                ai_config_info = (
                    f" (Received config: provider={getattr(self._ai_config, 'provider', 'unknown')}, "
                    f"model={getattr(self._ai_config, 'model_name', 'unknown')}, "
                    f"has_api_key={bool(getattr(self._ai_config, 'api_key', ''))}, "
                    f"base_url={getattr(self._ai_config, 'base_url', 'none')!r})"
                )
            raise RuntimeError(
                f"AI API not configured!{ai_config_info} "
                "For custom providers, ensure base_url is set. "
                "Check: 1) API key in plugin settings, 2) base_url for custom providers, "
                "3) Headers being sent (browser dev tools)."
            )

        if not self._gemini_client:
            raise RuntimeError(
                "GeminiClient not initialized. "
                "This is a configuration error - check backend startup logs."
            )

        # Real Gemini API call - 不再有Mock回退
        # ✅ Verified from Context7:/googleapis/python-genai (topic: async generate content)
        logger.info(f"Making REAL Gemini API call for agent: {agent_type.value}")

        # ✅ Story 12.C.2: 添加调试日志追踪实际发送给AI的内容
        # [Source: docs/plans/epic-12.C-agent-context-pollution-fix.md#Story-12.C.2]
        logger.info(
            f"[Story 12.C.2] _call_gemini_api DEBUG:\n"
            f"  - agent_type: {agent_type.value}\n"
            f"  - prompt length: {len(prompt) if prompt else 0} chars\n"
            f"  - prompt preview: {(prompt[:300] if prompt else 'None')}...\n"
            f"  - enriched_context length: {len(enriched_context) if enriched_context else 0} chars\n"
            f"  - enriched_context preview: {(enriched_context[:300] if enriched_context else 'None')}..."
        )
        if enriched_context and len(enriched_context) > 0:
            # [Story 12.I.4] Removed emoji to fix Windows GBK encoding
            logger.warning(
                f"[Story 12.C.2] WARNING: CONTEXT BEING INJECTED ({len(enriched_context)} chars). "
                f"If content is unrelated to topic, this is the pollution source!"
            )

        try:
            result = await self._gemini_client.call_agent(
                agent_type=agent_type.value,
                user_prompt=prompt,
                context=enriched_context if enriched_context else None,
                temperature=0.7
            )

            # ✅ FIX: Parse AI response JSON from string
            # [Source: Plan - unified-knitting-crane.md - Root Cause Analysis]
            # GeminiClient returns {"response": "JSON_STRING", ...}
            # We need to parse the JSON string and merge it into result
            if "response" in result and isinstance(result["response"], str):
                response_text = result["response"]
                try:
                    json_text = response_text.strip()

                    # Handle markdown code block wrappers
                    if "```json" in json_text:
                        json_text = json_text.split("```json")[1].split("```")[0].strip()
                    elif "```" in json_text:
                        # Handle code blocks without language marker
                        parts = json_text.split("```")
                        if len(parts) >= 3:
                            json_text = parts[1].strip()

                    # Parse JSON (json module imported at file top, line 15)
                    parsed = json.loads(json_text)

                    # Merge parsed data into result
                    if isinstance(parsed, dict):
                        result.update(parsed)
                        logger.debug(f"Parsed AI response JSON keys: {list(parsed.keys())}")
                except (json.JSONDecodeError, IndexError, ValueError) as e:
                    # Catch more exception types for robustness
                    logger.warning(f"Failed to parse AI response as JSON: {e}")
                    logger.debug(f"Raw response (first 500 chars): {response_text[:500] if response_text else 'empty'}...")

            # 添加来源标记，便于验证是真实API调用
            result["_source"] = "gemini_api"
            result["_mock"] = False
            logger.info(f"Gemini API success: {result.get('usage', {})}")

            # ✅ Story 12.G.1: 条件性详细响应日志 (AC 1, 3)
            # [Source: docs/stories/story-12.G.1-api-response-logging.md#Task-2]
            # ✅ Verified from ADR-010: structlog dual-format logging
            from app.config import settings
            if settings.DEBUG_AGENT_RESPONSE:
                response_preview = str(result)[:500] if result else "None"
                logger.debug(
                    "[Story 12.G.1] gemini_api_response_received",
                    extra={
                        "agent_type": agent_type.value,
                        "response_type": type(result).__name__,
                        "response_keys": list(result.keys()) if isinstance(result, dict) else "N/A",
                        "response_preview": response_preview,
                        "has_response_field": "response" in result if isinstance(result, dict) else False,
                    }
                )

            return result
        except FileNotFoundError as e:
            # Prompt template not found - 不再回退到Mock，直接报错
            logger.error(f"Prompt template not found for {agent_type.value}: {e}")
            raise FileNotFoundError(
                f"Agent prompt template missing: {agent_type.value}. "
                f"Please ensure .claude/agents/{agent_type.value}.md exists."
            ) from e
        except Exception as e:
            logger.error(f"Gemini API error for {agent_type.value}: {e}")
            raise

    # Phase 1 FIX: _mock_response removed - all calls must use real Gemini API
    # [Source: C:\Users\ROG\.claude\plans\wild-purring-umbrella.md - Phase 1]
    # [Source: Gemini Migration - Using google.genai instead of anthropic]

    def _enrich_prompt_with_neighbors(
        self,
        original_content: str,
        adjacent_data: Dict[str, Any],
        max_context_length: int = 200
    ) -> str:
        """
        Enrich agent prompt with adjacent node content.

        Phase 4.1: Option A - Adjacent Node Enrichment
        Injects parent and child node context into the Agent prompt.

        Args:
            original_content: Original node content
            adjacent_data: Result from CanvasService.get_adjacent_nodes()
            max_context_length: Maximum characters per adjacent node

        Returns:
            Enriched prompt with neighbor context

        [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Phase-4-Edge-Enhancement]
        """
        if not adjacent_data:
            return original_content

        parents = adjacent_data.get("parents", [])
        children = adjacent_data.get("children", [])

        # If no neighbors, return original
        if not parents and not children:
            return original_content

        context_parts = [original_content, "\n\n### Adjacent Concept Context (相邻概念上下文):"]

        # Add parent context
        for parent_info in parents:
            parent_node = parent_info.get("node", {})
            label = parent_info.get("label", "related")
            text = parent_node.get("text", "")[:max_context_length]
            node_type = parent_node.get("type", "text")

            if text:
                context_parts.append(f"\n- Parent [{label or 'prerequisite'}] ({node_type}): {text}")

        # Add child context
        for child_info in children:
            child_node = child_info.get("node", {})
            label = child_info.get("label", "related")
            text = child_node.get("text", "")[:max_context_length]
            node_type = child_node.get("type", "text")

            if text:
                context_parts.append(f"\n- Child [{label or 'extends'}] ({node_type}): {text}")

        return "\n".join(context_parts)

    def _extract_topic_from_content(self, content: str, max_length: int = 50) -> str:
        """
        Extract topic/concept name from content.

        Strategy:
        1. Use first line as topic (most common: "概念名" or "# 标题")
        2. Clean markdown markers and whitespace
        3. Truncate if too long

        [Source: Story 12.B.3 - Agent Prompt格式统一]

        Args:
            content: Raw node content
            max_length: Maximum topic length

        Returns:
            Extracted topic string
        """
        if not content or not content.strip():
            return "Unknown"

        # Get first line
        first_line = content.strip().split('\n')[0].strip()

        # Remove markdown heading markers
        if first_line.startswith('#'):
            first_line = first_line.lstrip('#').strip()

        # Remove bold/italic markers
        first_line = first_line.replace('**', '').replace('*', '').replace('_', ' ')

        # Clean up extra whitespace
        first_line = ' '.join(first_line.split())

        # Truncate if too long
        if len(first_line) > max_length:
            first_line = first_line[:max_length].rsplit(' ', 1)[0] + '...'

        return first_line if first_line else "Unknown"

    def _extract_comparison_concepts(self, content: str, topic: str) -> List[str]:
        """
        Extract comparison concepts list from content (for comparison-table Agent).

        [Source: Story 12.E.1 - 提示词格式对齐]
        [Source: .claude/agents/comparison-table.md:14-21 - Agent expects concepts array]

        Extraction Strategy:
        1. From Markdown table headers (e.g., | 概念A | 概念B | 概念C |)
        2. From Markdown lists (e.g., - 概念A, - 概念B)
        3. From ## headings (e.g., ## 概念A)
        4. Fallback: Return [topic] single element array

        Args:
            content: Raw node content
            topic: Extracted topic as fallback

        Returns:
            List of at least 1 concept (ideally 2+ for comparison)
        """
        import re
        concepts: List[str] = []

        if not content or not content.strip():
            return [topic] if topic else ["Unknown"]

        # Strategy 1: Extract from Markdown table header row
        # Pattern: | 概念A | 概念B | 概念C | (first row with |)
        table_header_match = re.search(r'^\|(.+)\|', content, re.MULTILINE)
        if table_header_match:
            header_cells = table_header_match.group(1).split('|')
            for cell in header_cells:
                cell = cell.strip()
                # Skip separator rows (---, :--:, etc.) and empty cells
                if cell and not re.match(r'^[-:]+$', cell):
                    # Skip common header labels like "对比维度", "维度"
                    if cell not in ['对比维度', '维度', '比较', '项目', '属性']:
                        concepts.append(cell)

        # Strategy 2: Extract from Markdown lists (- item or * item)
        if len(concepts) < 2:
            list_matches = re.findall(r'^[\-\*]\s+(.+)$', content, re.MULTILINE)
            for item in list_matches[:5]:  # Limit to first 5 items
                item = item.strip()
                if item and item not in concepts:
                    concepts.append(item)

        # Strategy 3: Extract from ## headings (level 2-3 headings)
        if len(concepts) < 2:
            heading_matches = re.findall(r'^#{2,3}\s+(.+)$', content, re.MULTILINE)
            for heading in heading_matches[:5]:  # Limit to first 5
                heading = heading.strip().lstrip('#').strip()
                if heading and heading not in concepts:
                    concepts.append(heading)

        # Deduplicate while preserving order
        seen = set()
        unique_concepts = []
        for c in concepts:
            if c not in seen:
                seen.add(c)
                unique_concepts.append(c)
        concepts = unique_concepts

        # If we got at least 2 concepts, return them
        if len(concepts) >= 2:
            logger.debug(f"[Story 12.E.1] Extracted {len(concepts)} comparison concepts: {concepts}")
            return concepts[:5]  # Limit to max 5 concepts

        # Fallback: Return [topic] as single element array
        fallback = [topic] if topic and topic != "Unknown" else ["Unknown"]
        logger.debug(f"[Story 12.E.1] Fallback to single concept: {fallback}")
        return fallback

    async def call_agent(
        self,
        agent_type: AgentType,
        prompt: str,
        timeout: Optional[float] = None,
        context: Optional[str] = None
    ) -> AgentResult:
        """
        Call a single agent with concurrency control.

        Uses real Claude API if ClaudeClient is configured, otherwise mock.

        Story 12.G.2 增强:
        - 分类错误类型 (AgentErrorType)
        - 生成bug_id便于追踪
        - 返回用户友好错误消息

        Args:
            agent_type: Type of agent to call
            prompt: Input prompt for the agent
            timeout: Optional timeout in seconds
            context: Optional additional context for the agent

        Returns:
            AgentResult with the response

        [Source: docs/prd/sprint-change-proposal-20251208.md - Story 20.4]
        [Enhanced: Story 12.G.2 - 增强错误处理与友好提示]
        """
        start_time = datetime.now()
        bug_id = _generate_bug_id()  # Story 12.G.2: 生成bug_id

        async with self._semaphore:
            self._active_calls += 1
            self._total_calls += 1
            try:
                if timeout:
                    data = await asyncio.wait_for(
                        self._call_gemini_api(agent_type, prompt, context),
                        timeout=timeout
                    )
                else:
                    data = await self._call_gemini_api(agent_type, prompt, context)

                duration_ms = (datetime.now() - start_time).total_seconds() * 1000
                return AgentResult(
                    agent_type=agent_type,
                    success=True,
                    result=data,
                    data=data,
                    duration_ms=duration_ms,
                )

            # Story 12.G.2: 分类错误处理 (对齐ADR-009)
            except asyncio.TimeoutError:
                # LLM_TIMEOUT (1002) - RETRYABLE
                error_type = AgentErrorType.LLM_TIMEOUT
                logger.warning(
                    f"Agent call timed out: {agent_type.value}",
                    extra={"bug_id": bug_id, "error_type": error_type.value}
                )
                return AgentResult(
                    agent_type=agent_type,
                    success=False,
                    error=error_type.user_message,
                    error_type=error_type,
                    bug_id=bug_id,
                )

            except FileNotFoundError as e:
                # FILE_NOT_FOUND (3001) - FATAL
                error_type = AgentErrorType.FILE_NOT_FOUND
                logger.error(
                    f"Agent template missing: {agent_type.value}",
                    extra={"bug_id": bug_id, "error_type": error_type.value, "error": str(e)}
                )
                return AgentResult(
                    agent_type=agent_type,
                    success=False,
                    error=f"{error_type.user_message}: {agent_type.value}",
                    error_type=error_type,
                    bug_id=bug_id,
                )

            except KeyError:
                # CONFIG_MISSING (2001) - NON_RETRYABLE (API Key未配置)
                error_type = AgentErrorType.CONFIG_MISSING
                # Story 12.G.2 AC5: 不记录敏感信息
                logger.error(
                    f"Configuration missing for agent: {agent_type.value}",
                    extra={"bug_id": bug_id, "error_type": error_type.value}
                )
                return AgentResult(
                    agent_type=agent_type,
                    success=False,
                    error=error_type.user_message,
                    error_type=error_type,
                    bug_id=bug_id,
                )

            except ConnectionError:
                # NETWORK_TIMEOUT (4001) - RETRYABLE
                error_type = AgentErrorType.NETWORK_TIMEOUT
                logger.warning(
                    f"Network error for agent: {agent_type.value}",
                    extra={"bug_id": bug_id, "error_type": error_type.value}
                )
                return AgentResult(
                    agent_type=agent_type,
                    success=False,
                    error=error_type.user_message,
                    error_type=error_type,
                    bug_id=bug_id,
                )

            except ValueError as e:
                # LLM_INVALID_RESPONSE (1004) - NON_RETRYABLE
                error_type = AgentErrorType.LLM_INVALID_RESPONSE
                logger.error(
                    f"Invalid response from agent: {agent_type.value}",
                    extra={"bug_id": bug_id, "error_type": error_type.value, "error": str(e)[:200]}
                )
                return AgentResult(
                    agent_type=agent_type,
                    success=False,
                    error=f"{error_type.user_message}: {str(e)[:100]}",
                    error_type=error_type,
                    bug_id=bug_id,
                )

            except Exception as e:
                # UNKNOWN (9999) - 未知错误
                error_type = AgentErrorType.UNKNOWN
                # 检查是否是速率限制错误
                error_str = str(e).lower()
                if "rate" in error_str and "limit" in error_str:
                    error_type = AgentErrorType.LLM_RATE_LIMIT
                elif "timeout" in error_str:
                    error_type = AgentErrorType.LLM_TIMEOUT
                elif "connection" in error_str or "network" in error_str:
                    error_type = AgentErrorType.NETWORK_TIMEOUT

                logger.error(
                    f"Agent call failed: {agent_type.value} - {type(e).__name__}",
                    extra={"bug_id": bug_id, "error_type": error_type.value}
                )
                return AgentResult(
                    agent_type=agent_type,
                    success=False,
                    error=error_type.user_message,
                    error_type=error_type,
                    bug_id=bug_id,
                )
            finally:
                self._active_calls -= 1

    async def call_agent_with_images(
        self,
        agent_type: AgentType,
        prompt: str,
        images: Optional[List[Dict[str, Any]]] = None,
        timeout: Optional[float] = None,
        context: Optional[str] = None
    ) -> AgentResult:
        """
        Call a single agent with images (multimodal support).

        Uses real Claude API with vision capabilities.

        Args:
            agent_type: Type of agent to call
            prompt: Input prompt for the agent
            images: List of image dicts with 'data' (base64) and 'media_type'
            timeout: Optional timeout in seconds
            context: Optional additional context for the agent

        Returns:
            AgentResult with the response

        [Source: FIX-2.1 实现Claude Vision多模态支持]
        """
        start_time = datetime.now()
        async with self._semaphore:
            self._active_calls += 1
            self._total_calls += 1
            try:
                if self._gemini_client:
                    # ✅ Verified from Context7:/googleapis/python-genai
                    # Gemini natively supports multimodal input
                    agent_type_str = agent_type.value if isinstance(agent_type, AgentType) else agent_type

                    if timeout:
                        data = await asyncio.wait_for(
                            self._gemini_client.call_agent_with_images(
                                agent_type_str, prompt, images=images, context=context
                            ),
                            timeout=timeout
                        )
                    else:
                        data = await self._gemini_client.call_agent_with_images(
                            agent_type_str, prompt, images=images, context=context
                        )
                else:
                    # Phase 1 FIX: No fallback to mock - raise error if not configured
                    # [Source: C:\Users\ROG\.claude\plans\wild-purring-umbrella.md - Phase 1]
                    # [Gemini Migration] Now uses GOOGLE_API_KEY
                    raise RuntimeError(
                        "GeminiClient not configured for multimodal! "
                        "Please set GOOGLE_API_KEY in backend/.env or plugin settings."
                    )

                duration_ms = (datetime.now() - start_time).total_seconds() * 1000
                return AgentResult(
                    agent_type=agent_type,
                    success=True,
                    result=data,
                    data=data,
                    duration_ms=duration_ms,
                )
            except asyncio.TimeoutError:
                return AgentResult(
                    agent_type=agent_type,
                    success=False,
                    error="Agent call with images timed out",
                )
            except Exception as e:
                logger.error(f"Agent call with images failed: {agent_type.value} - {e}")
                return AgentResult(
                    agent_type=agent_type,
                    success=False,
                    error=str(e),
                )
            finally:
                self._active_calls -= 1

    async def call_agents_batch(
        self,
        requests: List[Dict[str, Any]],
        return_exceptions: bool = False
    ) -> List[AgentResult]:
        """
        Call multiple agents concurrently.

        Args:
            requests: List of dicts with 'agent_type' and 'prompt' keys
            return_exceptions: If True, return exceptions as results

        Returns:
            List of AgentResult objects
        """
        tasks = [
            self.call_agent(req["agent_type"], req["prompt"])
            for req in requests
        ]

        if return_exceptions:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            # Convert exceptions to AgentResult with error
            processed = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    processed.append(AgentResult(
                        agent_type=requests[i]["agent_type"],
                        success=False,
                        error=str(result),
                    ))
                else:
                    processed.append(result)
            return processed
        else:
            return await asyncio.gather(*tasks)

    async def call_decomposition(
        self,
        content: str,
        deep: bool = False,
        context: Optional[str] = None,  # Story 12.A.2: RAG context
        user_understanding: Optional[str] = None
    ) -> AgentResult:
        """
        Call decomposition agent.

        Args:
            content: Content to decompose
            deep: If True, use deep decomposition
            context: Optional RAG context for enhanced prompts (Story 12.A.2)
            user_understanding: Optional user understanding for deep decomposition

        Returns:
            AgentResult with decomposition

        [Source: Story 12.B.3 - Agent Prompt格式统一]
        """
        agent_type = AgentType.DEEP_DECOMPOSITION if deep else AgentType.BASIC_DECOMPOSITION

        # ✅ Story 12.B.3: Construct JSON-formatted prompt
        topic = self._extract_topic_from_content(content)
        json_prompt = json.dumps({
            "material_content": content,
            "topic": topic,
            "user_understanding": user_understanding
        }, ensure_ascii=False, indent=2)

        logger.debug(f"[Story 12.B.3] Constructed JSON prompt for {agent_type.value}: topic={topic}")
        return await self.call_agent(agent_type, json_prompt, context=context)

    async def call_scoring(
        self,
        node_content: str,
        user_understanding: str,
        context: Optional[str] = None,  # Story 12.A.2: RAG context support
        question_text: Optional[str] = None
    ) -> AgentResult:
        """
        Call scoring agent.

        Args:
            node_content: Original node content (reference material)
            user_understanding: User's explanation
            context: Optional RAG context (Story 12.A.2)
            question_text: Optional question text for context

        Returns:
            AgentResult with scores

        [Source: Story 12.B.3 - Agent Prompt格式统一]
        """
        # ✅ Story 12.B.3: Construct JSON-formatted prompt for scoring agent
        json_prompt = json.dumps({
            "question_text": question_text or self._extract_topic_from_content(node_content),
            "user_understanding": user_understanding,
            "reference_material": node_content
        }, ensure_ascii=False, indent=2)

        logger.debug("[Story 12.B.3] Constructed JSON prompt for scoring agent")
        return await self.call_agent(AgentType.SCORING, json_prompt, context=context)

    async def call_explanation(
        self,
        content: str,
        explanation_type: str = "oral",
        context: Optional[str] = None,
        images: Optional[List[Dict[str, Any]]] = None,
        user_understanding: Optional[str] = None
    ) -> AgentResult:
        """
        Call explanation agent with optional multimodal support.

        Args:
            content: Content to explain
            explanation_type: Type of explanation (oral, clarification, comparison, memory, four_level, example)
            context: Optional additional context (adjacent nodes, textbook refs, user understanding text, RAG context)
            images: Optional list of images for multimodal analysis
            user_understanding: Optional[str] - User's understanding from yellow nodes.
                This is passed to the JSON prompt's `user_understanding` field for Agents
                that require it (deep-decomposition, question-decomposition).
                When None, the JSON field will be null (not empty string).
                [Story 12.E.2: Dual-channel delivery - also appears in context]

        Returns:
            AgentResult with explanation

        [Source: FIX-1.1 修复上下文传递链]
        [Source: FIX-2.1 实现Claude Vision多模态支持]
        [Source: Story 12.B.3 统一Agent Prompt为JSON格式]
        [Source: Story 12.E.2 user_understanding双通道传递]
        """
        type_map = {
            "oral": AgentType.ORAL_EXPLANATION,
            "clarification": AgentType.CLARIFICATION_PATH,
            "comparison": AgentType.COMPARISON_TABLE,
            "memory": AgentType.MEMORY_ANCHOR,
            "four_level": AgentType.FOUR_LEVEL,
            "four-level": AgentType.FOUR_LEVEL,  # ✅ Support both formats
            "example": AgentType.EXAMPLE_TEACHING,
        }
        agent_type = type_map.get(explanation_type, AgentType.ORAL_EXPLANATION)

        # ✅ Story 12.B.3: Construct JSON-formatted prompt for agent templates
        # Agent templates expect JSON input with material_content, topic, etc.
        topic = self._extract_topic_from_content(content)

        # ✅ Story 12.E.1: comparison-table Agent expects 'concepts' array, not 'concept' string
        # [Source: .claude/agents/comparison-table.md:14-21 - Agent expects concepts array]
        if agent_type == AgentType.COMPARISON_TABLE:
            concepts = self._extract_comparison_concepts(content, topic)
            json_prompt = json.dumps({
                "material_content": content,
                "topic": topic,
                "concepts": concepts,  # ✅ Array for comparison-table Agent
                "user_understanding": user_understanding
            }, ensure_ascii=False, indent=2)
            logger.info(f"[Story 12.E.1] comparison-table concepts: {concepts}")
        else:
            # Other agents use 'concept' string (backward compatibility)
            json_prompt = json.dumps({
                "material_content": content,
                "topic": topic,
                "concept": topic,  # Some agents use 'concept' instead of 'topic'
                "user_understanding": user_understanding
            }, ensure_ascii=False, indent=2)

        # ✅ Story 12.C.2: 添加调试日志追踪实际发送的内容
        # [Source: docs/plans/epic-12.C-agent-context-pollution-fix.md#Story-12.C.2]
        # ✅ Story 12.E.2: 添加 user_understanding 字段追踪
        logger.info(
            f"[Story 12.C.2] call_explanation DEBUG:\n"
            f"  - explanation_type: {explanation_type}\n"
            f"  - agent_type: {agent_type.value}\n"
            f"  - content length: {len(content)} chars\n"
            f"  - content preview: {content[:200]}...\n"
            f"  - extracted topic: '{topic}'\n"
            f"  - context length: {len(context) if context else 0} chars\n"
            f"  - user_understanding: {type(user_understanding).__name__} ({len(user_understanding) if user_understanding else 'null'})\n"
            f"  - json_prompt preview: {json_prompt[:300]}..."
        )
        logger.debug(f"[Story 12.B.3] Constructed JSON prompt for {agent_type.value}: topic={topic}")

        # ✅ FIX-2.1: Use multimodal call if images are provided
        if images and len(images) > 0:
            logger.info(f"Calling {agent_type.value} with {len(images)} images")
            return await self.call_agent_with_images(
                agent_type, json_prompt, images=images, context=context
            )

        # ✅ FIX-1.1: Pass context to call_agent for adjacent node enrichment
        return await self.call_agent(agent_type, json_prompt, context=context)

    async def decompose_basic(
        self,
        canvas_name: str,
        node_id: str,
        content: str,
        source_x: float = 0,
        source_y: float = 0,
        rag_context: Optional[str] = None  # Story 12.A.2: RAG context injection
    ) -> Dict[str, Any]:
        """
        Perform basic decomposition on a concept node.

        Args:
            canvas_name: Target canvas name
            node_id: ID of node to decompose
            content: Node content to decompose
            source_x: X coordinate of source node (for positioning new nodes)
            source_y: Y coordinate of source node (for positioning new nodes)
            rag_context: Optional RAG context from 5-source fusion (Story 12.A.2)

        Returns:
            Decomposition result with guiding questions and created_nodes for Canvas

        [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层]
        [FIX: Return created_nodes array for frontend to write to Canvas]
        [Story 12.A.2: Agent-RAG Bridge Layer - RAG context injection]
        """
        import uuid

        logger.debug(f"Basic decomposition for node {node_id}, has_rag_context={rag_context is not None}")
        result = await self.call_decomposition(content, deep=False, context=rag_context)

        # Extract questions from AI result
        questions = []
        created_nodes = []
        created_edges = []  # Story 12.M.2: Add edges connecting questions to source node

        if result.success and result.data:
            sub_questions = result.data.get("sub_questions", [])

            # Generate Canvas nodes for each question
            # Position nodes below and to the right of source node
            node_width = 280
            node_height = 100
            gap_x = 20
            gap_y = 30
            nodes_per_row = 2

            for idx, q in enumerate(sub_questions):
                question_text = q.get("text", "")
                question_type = q.get("type", "")
                guidance = q.get("guidance", "")

                # Format node text with type and guidance
                node_text = question_text
                if question_type:
                    node_text = f"[{question_type}] {node_text}"
                if guidance:
                    node_text = f"{node_text}\n\n{guidance}"

                questions.append(question_text)

                # Calculate position (grid layout below source node)
                row = idx // nodes_per_row
                col = idx % nodes_per_row
                x = source_x + col * (node_width + gap_x)
                y = source_y + 150 + row * (node_height + gap_y)  # 150px below source

                # Create node object matching frontend NodeRead type
                question_node_id = f"q-{node_id}-{idx}-{uuid.uuid4().hex[:8]}"
                created_nodes.append({
                    "id": question_node_id,
                    "type": "text",
                    "text": node_text,
                    "x": x,
                    "y": y,
                    "width": node_width,
                    "height": node_height,
                    "color": "6",  # Yellow - indicates question/understanding area (修复: '6'=Yellow)
                })

                # Story 12.M.2: Create edge from source node to question node
                created_edges.append({
                    "id": f"edge-basic-{uuid.uuid4().hex[:8]}",
                    "fromNode": node_id,
                    "toNode": question_node_id,
                    "fromSide": "bottom",
                    "toSide": "top"
                })

        logger.info(f"Basic decomposition created {len(created_nodes)} nodes and {len(created_edges)} edges")

        # Story 30.4: Fire-and-forget memory write for basic-decomposition
        await self._trigger_memory_write(
            agent_type="basic-decomposition",
            canvas_name=canvas_name,
            node_id=node_id,
            concept=content[:50] if content else "Unknown",
            user_understanding=content,
            agent_feedback=f"Decomposed into {len(questions)} basic questions"
        )

        return {
            "node_id": node_id,
            "questions": questions,
            "created_nodes": created_nodes,
            "created_edges": created_edges,  # Story 12.M.2: Include edges in response
            "status": "completed",
            "result": result.data,
        }

    async def decompose_deep(
        self,
        canvas_name: str,
        node_id: str,
        content: str,
        source_x: float = 0,
        source_y: float = 0,
        rag_context: Optional[str] = None  # Story 12.F.1: RAG context injection (was missing)
    ) -> Dict[str, Any]:
        """
        Perform deep decomposition for verification questions.

        Args:
            canvas_name: Target canvas name
            node_id: ID of node to decompose
            content: Node content to decompose
            source_x: X coordinate of source node for positioning
            source_y: Y coordinate of source node for positioning
            rag_context: Optional RAG context from 5-source fusion (Story 12.F.1)

        Returns:
            Deep verification questions and created nodes

        [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层]
        [Story 12.F.1: Fixed missing rag_context parameter that caused HTTP 500]
        """
        import uuid
        logger.debug(f"Deep decomposition for node {node_id}, has_rag_context={rag_context is not None}")
        result = await self.call_decomposition(content, deep=True, context=rag_context)

        verification_questions = []
        created_nodes = []
        created_edges = []  # Story 12.M.2: Add edges connecting questions to source node

        if result.success and result.data:
            # Extract sub_questions from AI result
            sub_questions = result.data.get("sub_questions", [])

            # Node positioning parameters
            node_width = 300
            node_height = 120
            gap_x = 20
            gap_y = 40
            nodes_per_row = 2

            for idx, q in enumerate(sub_questions):
                question_text = q.get("text", "")
                question_type = q.get("type", "")
                guidance = q.get("guidance", "")

                # Build node text with type and guidance
                node_text = question_text
                if question_type:
                    node_text = f"[{question_type}] {node_text}"
                if guidance:
                    node_text = f"{node_text}\n\n{guidance}"

                verification_questions.append(question_text)

                # Calculate position (grid layout below source node)
                row = idx // nodes_per_row
                col = idx % nodes_per_row
                x = source_x + col * (node_width + gap_x)
                y = source_y + 180 + row * (node_height + gap_y)  # 180px below source

                # Create node object matching frontend NodeRead type
                # Deep decomposition uses purple color (indicating "partially understood")
                question_node_id = f"vq-{node_id}-{idx}-{uuid.uuid4().hex[:8]}"
                created_nodes.append({
                    "id": question_node_id,
                    "type": "text",
                    "text": node_text,
                    "x": x,
                    "y": y,
                    "width": node_width,
                    "height": node_height,
                    "color": "3",  # Purple - indicates verification/deep question
                })

                # Story 12.M.2: Create edge from source node to question node
                created_edges.append({
                    "id": f"edge-deep-{uuid.uuid4().hex[:8]}",
                    "fromNode": node_id,
                    "toNode": question_node_id,
                    "fromSide": "bottom",
                    "toSide": "top"
                })

        logger.info(f"Deep decomposition created {len(created_nodes)} nodes and {len(created_edges)} edges")

        # Story 30.4: Fire-and-forget memory write for deep-decomposition
        await self._trigger_memory_write(
            agent_type="deep-decomposition",
            canvas_name=canvas_name,
            node_id=node_id,
            concept=content[:50] if content else "Unknown",
            user_understanding=content,
            agent_feedback=f"Deep decomposed into {len(verification_questions)} verification questions"
        )

        return {
            "node_id": node_id,
            "verification_questions": verification_questions,
            "created_nodes": created_nodes,
            "created_edges": created_edges,  # Story 12.M.2: Include edges in response
            "status": "completed",
            "result": result.data,
        }

    async def score_node(
        self,
        canvas_name: str,
        node_ids: List[str],
        node_contents: Optional[Dict[str, str]] = None,
        rag_context: Optional[str] = None  # Story 12.A.2: RAG context injection
    ) -> Dict[str, Any]:
        """
        Score multiple nodes' understanding.

        Args:
            canvas_name: Target canvas name
            node_ids: List of node IDs to score
            node_contents: Dict mapping node_id to content text (optional)
            rag_context: Optional RAG context for enhanced scoring (Story 12.A.2)

        Returns:
            {"scores": [{"node_id": ..., "accuracy": ..., ...}]}

        [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层]
        [Source: FIX-4.2 记录学习历程]
        [Source: FIX-5.1 修复score_node签名不匹配]
        [Source: Story 12.A.2 Agent-RAG Bridge Layer]
        """
        logger.debug(f"Scoring {len(node_ids)} nodes, has_rag_context={rag_context is not None}")

        # Story 12.A.2: Handle node_contents being None
        if node_contents is None:
            node_contents = {}

        scores = []
        for node_id in node_ids:
            content = node_contents.get(node_id, "")

            # Call scoring for each node
            # Story 12.A.2: Pass rag_context to call_scoring
            result = await self.call_scoring("", content, context=rag_context)

            # Debug: Log Agent response for troubleshooting
            logger.info(f"[Story 2.8] Scoring Agent response: success={result.success}, data_keys={list(result.data.keys()) if result.data else 'None'}")
            if result.data:
                logger.info(f"[Story 2.8] Scoring data: total_score={result.data.get('total_score')}, feedback_len={len(result.data.get('feedback', ''))}")

            # Determine color based on score
            # scoring.md template uses "total_score" (0-100 scale), fallback to "total" for compatibility
            total_score = 0.0
            if result.success and result.data:
                # Try both field names for compatibility
                total_score = result.data.get("total_score", result.data.get("total", 0.0))
                # Ensure score is in 0-100 range (normalize if needed)
                if total_score <= 1.0 and total_score > 0:
                    total_score = total_score * 100  # Convert 0-1 to 0-100

            # Color mapping: scoring.md defines ≥80=green, 60-79=purple, <60=red (0-100 scale)
            if total_score >= 80:
                new_color = "2"  # green (完全理解/已通过)
            elif total_score >= 60:
                new_color = "3"  # purple (似懂非懂/待检验)
            else:
                new_color = "4"  # red (不理解/未通过)

            # Extract feedback from Agent response (scoring.md defines 100-200 char feedback)
            feedback = ""
            color_action = ""
            if result.success and result.data:
                feedback = result.data.get("feedback", "")
                color_action = result.data.get("color_action", "")
                # Also check breakdown structure from scoring.md template
                breakdown = result.data.get("breakdown", {})
                if breakdown:
                    # Use breakdown values if available (0-25 scale per dimension)
                    accuracy = breakdown.get("accuracy", result.data.get("accuracy", 0.0))
                    imagery = breakdown.get("imagery", result.data.get("imagery", 0.0))
                    completeness = breakdown.get("completeness", result.data.get("completeness", 0.0))
                    originality = breakdown.get("originality", result.data.get("originality", 0.0))
                else:
                    accuracy = result.data.get("accuracy", 0.0)
                    imagery = result.data.get("imagery", 0.0)
                    completeness = result.data.get("completeness", 0.0)
                    originality = result.data.get("originality", 0.0)
            else:
                accuracy = imagery = completeness = originality = 0.0

            scores.append({
                "node_id": node_id,
                "accuracy": accuracy,
                "imagery": imagery,
                "completeness": completeness,
                "originality": originality,
                "total": total_score,
                "new_color": new_color,
                "feedback": feedback,  # Story 2.8: Pass feedback to frontend
                "color_action": color_action,  # Story 2.8: Pass color_action to frontend
            })

            # Record learning episode (Story 30.4: fire-and-forget pattern)
            await self._trigger_memory_write(
                agent_type="scoring-agent",
                canvas_name=canvas_name,
                node_id=node_id,
                concept=content[:50] if content else "Unknown",
                user_understanding=content,
                score=total_score,
                agent_feedback=str(result.data) if result.data else None
            )

        return {"scores": scores}

    async def find_related_understanding_content(
        self,
        canvas_name: str,
        source_node_id: str,
        canvas_data: Dict[str, Any]
    ) -> List[str]:
        """
        FIX-4.4: 查找与源节点关联的所有黄色理解节点内容。

        通过 Canvas 的 edges 追踪：
        源节点 → 解释节点 → 黄色理解节点

        用于在生成新解释时，结合用户之前填写的个人理解，
        实现个性化、渐进式的学习解释。

        Args:
            canvas_name: Canvas 文件名
            source_node_id: 源节点 ID
            canvas_data: Canvas 数据字典

        Returns:
            用户填写的理解内容列表（排除空内容和占位符）
        """
        understanding_contents = []

        # 遍历所有 edges，找到从源节点出发的解释链
        edges = canvas_data.get("edges", [])
        nodes = {n["id"]: n for n in canvas_data.get("nodes", [])}

        # 查找所有与源节点相关的节点（通过 edge 关系，BFS遍历）
        related_node_ids = set()
        queue = [source_node_id]
        visited = {source_node_id}

        while queue:
            current_id = queue.pop(0)
            for edge in edges:
                if edge.get("fromNode") == current_id:
                    to_node_id = edge.get("toNode")
                    if to_node_id and to_node_id not in visited:
                        related_node_ids.add(to_node_id)
                        visited.add(to_node_id)
                        queue.append(to_node_id)

        logger.info(f"[FIX-4.4] Found {len(related_node_ids)} related nodes for {source_node_id}")

        # 从关联节点中找出黄色节点（color: "6"）并读取内容
        # 颜色定义与前端一致：Yellow="6", Purple="3", Red="4", Green="2", Blue="5"
        for node_id in related_node_ids:
            node = nodes.get(node_id)
            if node and node.get("color") == "6":  # Yellow node (个人理解)
                logger.debug(f"[FIX-4.4] Found yellow node: {node_id}, type={node.get('type')}")

                if node.get("type") == "file" and node.get("file"):
                    # FIX-4.4: Read file content from vault
                    content = await self.canvas_service.read_file_content(node["file"])
                    if content:
                        understanding_contents.append(content)
                        logger.info(f"[FIX-4.4] Read understanding from file: {node['file']}")
                elif node.get("type") == "text" and node.get("text"):
                    text = node["text"].strip()
                    if text and "[请在此填写" not in text:
                        understanding_contents.append(text)
                        logger.info(f"[FIX-4.4] Read understanding from text node: {node_id}")

        logger.info(f"[FIX-4.4] Total user understandings found: {len(understanding_contents)}")
        return understanding_contents

    def _find_adjacent_content_nodes(
        self,
        node_id: str,
        canvas_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        FIX-4.5: 查找与指定节点直接相连的内容节点（非黄色节点）。

        用于当用户从黄色理解节点调用Agent时，找到相邻的教材节点作为 material_content。
        搜索双向边（fromNode 和 toNode），但只返回非黄色节点（教材/解释节点）。

        Args:
            node_id: 当前节点 ID（黄色理解节点）
            canvas_data: Canvas 数据字典

        Returns:
            相邻的非黄色内容节点列表
        """
        edges = canvas_data.get("edges", [])
        nodes = {n["id"]: n for n in canvas_data.get("nodes", [])}
        adjacent_nodes = []

        # 查找所有与当前节点直接相连的节点（双向）
        for edge in edges:
            connected_node_id = None
            if edge.get("fromNode") == node_id:
                connected_node_id = edge.get("toNode")
            elif edge.get("toNode") == node_id:
                connected_node_id = edge.get("fromNode")

            if connected_node_id and connected_node_id in nodes:
                connected_node = nodes[connected_node_id]
                # 只返回非黄色节点（教材/解释节点）
                if connected_node.get("color") != "6":
                    adjacent_nodes.append(connected_node)
                    logger.debug(f"[FIX-4.5] Found adjacent content node: {connected_node_id}, color={connected_node.get('color')}")

        logger.info(f"[FIX-4.5] Found {len(adjacent_nodes)} adjacent content nodes for yellow node {node_id}")
        return adjacent_nodes

    async def generate_explanation(
        self,
        canvas_name: str,
        node_id: str,
        content: str,
        explanation_type: str = "oral",
        adjacent_context: Optional[str] = None,
        images: Optional[List[Dict[str, Any]]] = None,
        source_x: float = 0,
        source_y: float = 0,
        source_width: float = 400,
        source_height: float = 200,
        rag_context: Optional[str] = None  # Story 12.A.2: RAG context injection
    ) -> Dict[str, Any]:
        """
        Generate an explanation for a concept with adjacent node context and optional images.

        Args:
            canvas_name: Target canvas name
            node_id: ID of node to explain
            content: Node content to explain
            explanation_type: Type of explanation (oral, four-level, etc.)
            adjacent_context: Context from adjacent nodes (1-hop neighbors)
            images: Optional list of images for multimodal analysis
            source_x: X coordinate of source node (for positioning new nodes)
            source_y: Y coordinate of source node (for positioning new nodes)
            source_width: Width of source node
            source_height: Height of source node
            rag_context: Optional RAG context from 5-source fusion (Story 12.A.2)

        Returns:
            Generated explanation with created_nodes for Canvas

        [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层]
        [Source: FIX-1.1 修复上下文传递链 - adjacent_context now flows through]
        [Source: FIX-2.1 实现Claude Vision多模态支持]
        [Source: FIX-3.0 返回created_nodes数组用于Canvas写入]
        [Source: Story 12.A.2 Agent-RAG Bridge Layer]
        """
        import json as json_module  # Avoid conflict with local variables
        import uuid

        context_len = len(adjacent_context) if adjacent_context else 0
        images_count = len(images) if images else 0
        rag_len = len(rag_context) if rag_context else 0  # Story 12.A.2
        logger.debug(f"Generating {explanation_type} explanation for node {node_id}, context_len={context_len}, images={images_count}, rag_context_len={rag_len}")

        # ✅ FIX-4.4: 读取用户之前填写的个人理解
        user_understandings = []
        try:
            from app.config import settings
            canvas_path = os.path.join(settings.CANVAS_BASE_PATH, canvas_name)
            if not canvas_path.endswith('.canvas'):
                canvas_path += '.canvas'

            if os.path.exists(canvas_path):
                with open(canvas_path, 'r', encoding='utf-8') as f:
                    canvas_data = json_module.load(f)

                # ✅ FIX-4.5: 检测当前节点是否为黄色节点（用户理解节点）
                # 当用户右键黄色节点调用Agent时，黄色节点内容应作为user_understanding
                current_node = next((n for n in canvas_data.get("nodes", []) if n.get("id") == node_id), None)
                is_yellow_node = current_node and current_node.get("color") == "6"
                logger.info(f"[FIX-4.5] Node {node_id} is_yellow={is_yellow_node}, color={current_node.get('color') if current_node else 'N/A'}")

                if is_yellow_node:
                    # ✅ FIX-4.5: 当前节点是黄色理解节点
                    # 将当前节点内容作为 user_understanding，从邻接节点获取教材内容
                    logger.info("[FIX-4.5] Yellow node detected! content will be treated as user_understanding")
                    user_understandings = [content]  # 黄色节点内容作为用户理解

                    # 从邻接节点中查找教材内容（非黄色节点）
                    adjacent_content_nodes = self._find_adjacent_content_nodes(node_id, canvas_data)
                    if adjacent_content_nodes:
                        # 用邻接教材节点内容替换 content
                        material_texts = [n.get("text", "") for n in adjacent_content_nodes if n.get("type") == "text" and n.get("text")]
                        if material_texts:
                            # 更新 content 为教材内容，用于后续 topic 提取和 call_explanation
                            content = "\n\n---\n\n".join(material_texts)
                            logger.info(f"[FIX-4.5] Replaced content with {len(adjacent_content_nodes)} adjacent teaching nodes ({len(content)} chars)")
                        else:
                            logger.warning("[FIX-4.5] Adjacent nodes found but no text content")
                    else:
                        logger.warning(f"[FIX-4.5] No adjacent content nodes found for yellow node {node_id}")
                else:
                    # 原有逻辑：当前节点是教材节点，从邻居查找黄色节点
                    # 查找关联的黄色理解节点内容
                    user_understandings = await self.find_related_understanding_content(
                        canvas_name, node_id, canvas_data
                    )
                logger.info(f"[FIX-4.4] Found {len(user_understandings)} user understandings for node {node_id}")
        except Exception as e:
            logger.warning(f"[FIX-4.4] Failed to read user understandings: {e}")

        # ✅ Story 12.E.2: 构建 user_understanding 字符串用于 JSON 字段
        # 将 user_understandings 列表合并为单一字符串，用于双通道传递
        user_understanding: Optional[str] = None
        if user_understandings:
            user_understanding = "\n\n".join(user_understandings)
            logger.info(f"[Story 12.E.2] user_understanding prepared: {len(user_understanding)} chars")

        # ✅ FIX-4.4: 构建包含用户理解的增强上下文
        # ✅ Story 12.C.1: 可禁用上下文增强以消除污染
        # [Source: docs/plans/epic-12.C-agent-context-pollution-fix.md#Story-12.C.1]
        if DISABLE_CONTEXT_ENRICHMENT:
            logger.warning(
                f"[Story 12.C.1] Context enrichment DISABLED for generate_explanation. "
                f"Skipping: adjacent_context ({len(adjacent_context) if adjacent_context else 0} chars), "
                f"user_understandings ({len(user_understandings)}), "
                f"rag_context ({len(rag_context) if rag_context else 0} chars). "
                f"Node content will be used directly."
            )
            enhanced_context = ""  # 完全禁用上下文，只使用节点原文
        else:
            enhanced_context = adjacent_context or ""
            if user_understandings:
                user_context = "\n\n## 用户之前的个人理解\n\n"
                for i, understanding in enumerate(user_understandings, 1):
                    user_context += f"### 理解 {i}\n{understanding}\n\n"
                user_context += "请结合用户的这些理解，生成更贴合用户认知水平的解释。如果用户理解有误，请在解释中委婉纠正。\n"
                enhanced_context = (enhanced_context + user_context) if enhanced_context else user_context
                logger.info(f"[FIX-4.4] Enhanced context with {len(user_understandings)} user understandings")

            # ✅ Story 12.A.2: 添加 RAG 上下文到增强上下文
            if rag_context:
                enhanced_context = f"{enhanced_context}\n\n{rag_context}" if enhanced_context else rag_context
                logger.info(f"[Story 12.A.2] Enhanced context with RAG ({len(rag_context)} chars)")

        # ✅ FIX-1.1: Pass adjacent_context to call_explanation
        # ✅ FIX-2.1: Pass images for multimodal support
        # ✅ FIX-4.4: Pass enhanced_context with user understandings
        # ✅ Story 12.A.2: Pass enhanced_context with RAG context
        # ✅ Story 12.E.2: Pass user_understanding for dual-channel delivery (JSON + context)
        logger.info(
            f"[Story 12.E.2] Dual-channel user_understanding:\n"
            f"  - JSON field: {'set' if user_understanding else 'null'}\n"
            f"  - enhanced_context: {'contains' if enhanced_context and '用户之前的个人理解' in enhanced_context else 'empty'}\n"
            f"  - content length: {len(user_understanding) if user_understanding else 0}"
        )
        result = await self.call_explanation(
            content, explanation_type, context=enhanced_context, images=images,
            user_understanding=user_understanding  # ✅ Story 12.E.2: Pass to JSON field
        )

        # ✅ Story 21.3: Use multi-fallback extraction with friendly error handling
        # [Source: docs/prd/EPIC-21-AGENT-E2E-FLOW-FIX.md#story-21-3]
        explanation_text, extraction_success = extract_explanation_text(result.data)

        if not extraction_success or not explanation_text:
            logger.error(
                f"generate_explanation: Failed to extract text for {explanation_type}",
                extra={
                    "node_id": node_id,
                    "explanation_type": explanation_type,
                    "result_data_type": type(result.data).__name__ if result.data else "None"
                }
            )
            # ✅ FIX: Create error response and write to Canvas before returning
            error_response = create_error_response(
                error_message="无法从AI响应中提取有效内容",
                source_node_id=node_id,
                agent_type=explanation_type,
                source_x=source_x,
                source_y=source_y,
                source_width=source_width,
                source_height=source_height,
            )

            # ✅ FIX: Write error nodes to Canvas so user can see the error
            if canvas_name:
                await self._write_nodes_to_canvas(
                    canvas_name=canvas_name,
                    nodes=error_response.get("created_nodes", []),
                    edges=error_response.get("created_edges", [])
                )

            return error_response

        # ✅ FIX: Generate created_node_id (required by ExplainResponse)
        created_node_id = f"explain-{explanation_type}-{node_id}-{uuid.uuid4().hex[:8]}"

        # ✅ FIX-4.3: Create file nodes instead of text nodes
        # All explanation nodes will be .md files stored in {canvas}-explanations/ folder
        created_nodes = []
        created_edges = []

        # ✅ FIX-4.3: Calculate explanations directory path
        from datetime import datetime

        from app.config import settings

        vault_path = settings.CANVAS_BASE_PATH  # e.g., "C:/Users/ROG/托福/Canvas/笔记库"
        # canvas_name is relative path like "Canvas/Math53/Lecture5.canvas"
        canvas_dir = os.path.dirname(canvas_name)  # "Canvas/Math53"
        canvas_basename = os.path.splitext(os.path.basename(canvas_name))[0]  # "Lecture5"
        explanations_dir = f"{canvas_dir}/{canvas_basename}-explanations"  # "Canvas/Math53/Lecture5-explanations"

        # Create explanations directory if it doesn't exist
        full_explanations_dir = os.path.join(vault_path, explanations_dir)
        os.makedirs(full_explanations_dir, exist_ok=True)
        logger.info(f"[FIX-4.3] Explanations directory: {full_explanations_dir}")

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

        if explanation_text:
            # Check if this is a four-level explanation (contains level headers)
            is_four_level = explanation_type in ["four-level", "four_level", "four-level-explanation"]
            level_pattern = r'##\s*(新手层|进阶层|专家层|创新层).*?\n'

            if is_four_level and re.search(level_pattern, explanation_text):
                # ✅ FIX-4.8: Create ONE .md file containing ALL 4 levels
                # (User feedback: should be 1 file, not 4 separate files)

                # Layout configuration
                node_width = 500
                node_height = 600  # Taller to accommodate all 4 levels
                yellow_height = 150
                gap_y = 40

                # Position below source node
                node_x = source_x
                node_y = source_y + source_height + gap_y

                # ✅ FIX-4.8: Create single .md file with all 4 levels
                explain_node_id = f"explain-four-level-{node_id[:8]}-{uuid.uuid4().hex[:4]}"
                explain_filename = f"四层次解释-{node_id[:8]}-{timestamp}.md"
                explain_file_path = f"{explanations_dir}/{explain_filename}"
                explain_full_path = os.path.join(vault_path, explain_file_path)

                # Write ALL levels to single .md file
                with open(explain_full_path, 'w', encoding='utf-8') as f:
                    f.write(f"# 四层次解释\n\n{explanation_text}")
                logger.info(f"[FIX-4.8] Created SINGLE four-level explanation file: {explain_file_path}")

                # Create file type node (green for explanation)
                created_nodes.append({
                    "id": explain_node_id,
                    "type": "file",
                    "file": explain_file_path,
                    "x": node_x,
                    "y": node_y,
                    "width": node_width,
                    "height": node_height,
                    "color": "4",  # Green - explanation
                })
                logger.info(f"[FIX-4.8] Created four-level file node {explain_node_id}")

                # Create edge: Source → Explanation
                edge1_id = f"edge-src-explain-{uuid.uuid4().hex[:8]}"
                created_edges.append({
                    "id": edge1_id,
                    "fromNode": node_id,
                    "toNode": explain_node_id,
                    "fromSide": "bottom",
                    "toSide": "top",
                    "label": "四层次解释",
                })

                # ✅ Story 21.5: Conditionally create personal understanding node
                # [Source: docs/prd/EPIC-21-AGENT-E2E-FLOW-FIX.md#story-21-5]
                if AUTO_CREATE_PERSONAL_NODE:
                    # ✅ FIX-4.9: Create ONE yellow understanding node
                    yellow_node_id = f"understand-four-level-{node_id[:8]}-{uuid.uuid4().hex[:4]}"
                    yellow_y = node_y + node_height + gap_y
                    created_nodes.append({
                        "id": yellow_node_id,
                        "type": "text",
                        "text": "# 💡 我的理解\n\n[请在此填写你对四层次解释的整体理解...]\n\n## 新手层理解\n\n\n## 进阶层理解\n\n\n## 专家层理解\n\n\n## 创新层理解\n\n",
                        "x": node_x,
                        "y": yellow_y,
                        "width": node_width,
                        "height": yellow_height,
                        "color": "3",  # Purple node (验证问题/待检验) - 修复: "3"=Purple
                    })
                    logger.info(f"[Story 21.5] Created PURPLE understanding node {yellow_node_id}")

                    # Create edge: Explanation → Personal Understanding
                    edge2_id = f"edge-explain-yellow-{uuid.uuid4().hex[:8]}"
                    created_edges.append({
                        "id": edge2_id,
                        "fromNode": explain_node_id,
                        "toNode": yellow_node_id,
                        "fromSide": "bottom",
                        "toSide": "top",
                        "label": "个人理解",  # ✅ FIX-4.10: Add edge label
                        "color": "3",  # Purple edge - 修复: "3"=Purple
                    })
                else:
                    logger.debug("[Story 21.5] AUTO_CREATE_PERSONAL_NODE=False, skipping personal node")

                created_node_id = explain_node_id
                logger.info("[FIX-4.8/4.9] Four-level explanation complete: 1 file, 1 yellow node, 2 edges")

            else:
                # ✅ FIX-4.3: Standard single-node explanation (oral, basic, etc.) - create .md files
                node_width = 500
                node_height = max(300, min(800, len(explanation_text) // 3))

                # Position below source node
                gap_y = 50
                node_x = source_x
                node_y = source_y + source_height + gap_y

                # ✅ FIX-4.3: Create .md file for explanation node
                explain_filename = f"{explanation_type}-解释-{node_id[:8]}-{timestamp}.md"
                explain_file_path = f"{explanations_dir}/{explain_filename}"
                explain_full_path = os.path.join(vault_path, explain_file_path)

                # Write explanation content to .md file
                with open(explain_full_path, 'w', encoding='utf-8') as f:
                    f.write(f"# {explanation_type.title()} 解释\n\n{explanation_text}")
                logger.info(f"[FIX-4.3] Created explanation file: {explain_file_path}")

                # Create file type node
                created_nodes.append({
                    "id": created_node_id,
                    "type": "file",
                    "file": explain_file_path,  # Relative to vault
                    "x": node_x,
                    "y": node_y,
                    "width": node_width,
                    "height": node_height,
                    "color": "4",  # Green - indicates explanation
                })
                logger.info(f"[FIX-4.3] Created explanation file node {created_node_id} at ({node_x}, {node_y})")

                # Create edge: Source → Explanation
                edge1_id = f"edge-{node_id[:8]}-{created_node_id[:8]}-{uuid.uuid4().hex[:4]}"
                created_edges.append({
                    "id": edge1_id,
                    "fromNode": node_id,
                    "toNode": created_node_id,
                    "fromSide": "bottom",
                    "toSide": "top",
                    "label": explanation_type,
                })

                # ✅ Story 21.5: Conditionally create personal understanding node
                # [Source: docs/prd/EPIC-21-AGENT-E2E-FLOW-FIX.md#story-21-5]
                if AUTO_CREATE_PERSONAL_NODE:
                    # ✅ FIX-4.5: Create text type yellow understanding node (directly editable in Canvas)
                    yellow_node_id = f"understand-{node_id[:8]}-{uuid.uuid4().hex[:4]}"
                    yellow_y = node_y + node_height + PERSONAL_NODE_VERTICAL_OFFSET
                    created_nodes.append({
                        "id": yellow_node_id,
                        "type": "text",
                        "text": PERSONAL_NODE_PROMPT_TEXT,  # ✅ Story 21.5: Use configurable prompt
                        "x": node_x,
                        "y": yellow_y,
                        "width": node_width,
                        "height": 120,
                        "color": "6",  # Yellow - 待填写的个人理解区域 (修复: '6'=Yellow)
                    })
                    logger.info(f"[Story 21.5] Created yellow text node {yellow_node_id}")

                    # Create edge: Explanation → Personal Understanding
                    edge2_id = f"edge-{created_node_id[:8]}-{yellow_node_id[:8]}-{uuid.uuid4().hex[:4]}"
                    created_edges.append({
                        "id": edge2_id,
                        "fromNode": created_node_id,
                        "toNode": yellow_node_id,
                        "fromSide": "bottom",
                        "toSide": "top",
                        "label": "个人理解",  # ✅ Story 21.5: Add edge label
                        "color": "6",  # Yellow edge matches node (修复: '6'=Yellow)
                    })
                    logger.info("[Story 21.5] Created edges for standard explanation with personal node")
                else:
                    logger.debug("[Story 21.5] AUTO_CREATE_PERSONAL_NODE=False, skipping personal node")

        # ✅ FIX-Canvas-Write: 写入节点到 Canvas 文件（核心修复）
        # [Source: Plan cozy-sniffing-shamir.md]
        # 这是解决 "Agent 生成成功但 Canvas 不显示任何节点" 问题的关键
        write_success = await self._write_nodes_to_canvas(
            canvas_name=canvas_name,
            nodes=created_nodes,
            edges=created_edges
        )
        if write_success:
            # [Story 12.I.4] Removed emoji to fix Windows GBK encoding
            logger.info(f"[FIX-Canvas-Write] SUCCESS: Canvas {canvas_name} updated with {len(created_nodes)} nodes and {len(created_edges)} edges")
        else:
            # [Story 12.I.4] Removed emoji to fix Windows GBK encoding
            logger.warning(f"[FIX-Canvas-Write] WARNING: Failed to write to Canvas {canvas_name}, nodes returned in response but not persisted")

        # Story 30.4: Fire-and-forget memory write for explanation agents
        # Map explanation_type to proper agent name for memory tracking
        explanation_type_to_agent = {
            "oral": "oral-explanation",
            "four-level": "four-level-explanation",
            "four_level": "four-level-explanation",
            "four-level-explanation": "four-level-explanation",
            "example": "example-teaching",
            "comparison": "comparison-table",
            "memory": "memory-anchor",
            "clarification": "clarification-path",
        }
        agent_name = explanation_type_to_agent.get(explanation_type, f"{explanation_type}-explanation")
        await self._trigger_memory_write(
            agent_type=agent_name,
            canvas_name=canvas_name,
            node_id=node_id,
            concept=content[:50] if content else "Unknown",
            user_understanding=user_understanding,
            agent_feedback=f"Generated {explanation_type} explanation ({len(explanation_text)} chars)"
        )

        return {
            "node_id": node_id,
            "explanation_type": explanation_type,
            "explanation": explanation_text,  # ✅ Now contains actual AI response
            "created_node_id": created_node_id,  # ✅ Required by ExplainResponse
            "created_nodes": created_nodes,  # ✅ FIX-3.0: Nodes for Canvas
            "created_edges": created_edges,  # ✅ FIX-4.1: Edges for Canvas
            "canvas_write_success": write_success,  # ✅ FIX-Canvas-Write: Indicate if canvas was updated
            "status": "completed",
            "result": result.data,
            "context_used": context_len > 0,  # Track if context was provided
            "images_processed": images_count,  # Track images processed
        }

    async def record_learning_episode(
        self,
        canvas_name: str,
        node_id: str,
        concept: str,
        user_understanding: Optional[str] = None,
        score: Optional[float] = None,
        agent_feedback: Optional[str] = None
    ) -> bool:
        """
        Record a learning episode to the memory system.

        This method should be called after any Agent analysis to track
        the user's learning progress over time.

        Args:
            canvas_name: Canvas file name
            node_id: Node ID that was analyzed
            concept: Concept name or summary
            user_understanding: User's answer or understanding text
            score: Score from scoring agent (0-40)
            agent_feedback: Feedback from the agent

        Returns:
            True if successfully recorded, False otherwise

        [Source: FIX-4.2 Agent调用时查询历史]
        """
        if not self._memory_client:
            logger.debug("Memory client not available, skipping episode recording")
            return False

        try:
            from app.clients.graphiti_client import LearningMemory

            memory = LearningMemory(
                canvas_name=canvas_name,
                node_id=node_id,
                concept=concept,
                user_understanding=user_understanding,
                score=score,
                agent_feedback=agent_feedback
            )

            success = await self._memory_client.add_learning_episode(memory)
            if success:
                logger.debug(f"Recorded learning episode: {canvas_name}/{node_id}")
            return success

        except Exception as e:
            logger.warning(f"Failed to record learning episode: {e}")
            return False

    # ═══════════════════════════════════════════════════════════════════════════════
    # Story 30.4: Agent Memory Write Trigger Mechanism
    # [Source: docs/stories/30.4.story.md]
    # ═══════════════════════════════════════════════════════════════════════════════

    async def _trigger_memory_write(
        self,
        agent_type: str,
        canvas_name: str,
        node_id: str,
        concept: str,
        user_understanding: Optional[str] = None,
        score: Optional[float] = None,
        agent_feedback: Optional[str] = None
    ) -> None:
        """
        Fire-and-forget memory write trigger for post-agent execution.

        This method implements async non-blocking memory write with:
        - AC-30.4.2: asyncio.create_task() for fire-and-forget pattern
        - AC-30.4.3: Silent degradation on failure (log error but don't raise)
        - Story 38.6: 15s timeout protection aligned with inner retry budget

        The method wraps record_learning_episode() and fires it asynchronously
        so the agent response can return immediately.

        Args:
            agent_type: Name of the agent that completed (e.g., "scoring-agent")
            canvas_name: Canvas file name
            node_id: Node ID that was processed
            concept: Concept name or summary
            user_understanding: Optional user's understanding text
            score: Optional score from scoring agent
            agent_feedback: Optional feedback from agent

        Returns:
            None (fire-and-forget, no return value)

        [Source: docs/stories/30.4.story.md#Task-2-3-4]
        [Source: docs/architecture/decisions/0004-async-execution-engine.md]
        """
        from app.core.agent_memory_mapping import get_memory_type_for_agent

        # AC-30.4.4: Check if this agent has memory write enabled
        memory_type = get_memory_type_for_agent(agent_type)
        if memory_type is None:
            logger.debug(f"[Story 30.4] Agent {agent_type} not in memory mapping, skipping")
            return

        # AC-30.4.2: Fire-and-forget async pattern
        # Story 38.6 AC-1: Timeout aligned with inner retry mechanism
        async def _write_with_timeout():
            """Inner coroutine with timeout protection."""
            try:
                await asyncio.wait_for(
                    self.record_learning_episode(
                        canvas_name=canvas_name,
                        node_id=node_id,
                        concept=concept,
                        user_understanding=user_understanding,
                        score=score,
                        agent_feedback=agent_feedback
                    ),
                    timeout=MEMORY_WRITE_TIMEOUT  # Story 38.6: 15s to allow inner retries
                )
                logger.debug(
                    f"[Story 30.4] Memory write completed for {agent_type}",
                    extra={"agent_type": agent_type, "memory_type": memory_type.value}
                )
            except asyncio.TimeoutError:
                # AC-30.4.3 + Story 38.6 AC-2: Log and track failed write
                logger.warning(
                    f"[Story 38.6] Memory write timeout for {agent_type} after {MEMORY_WRITE_TIMEOUT}s",
                    extra={"agent_type": agent_type, "timeout_s": MEMORY_WRITE_TIMEOUT}
                )
                _record_failed_write(
                    event_type=agent_type,
                    concept_id=node_id,
                    canvas_name=canvas_name,
                    score=score,
                    error_reason=f"timeout after {MEMORY_WRITE_TIMEOUT}s",
                    concept=concept,
                    user_understanding=user_understanding,
                    agent_feedback=agent_feedback,
                )
            except Exception as e:
                # AC-30.4.3 + Story 38.6 AC-2: Log and track failed write
                logger.warning(
                    f"[Story 38.6] Memory write failed for {agent_type}: {e}",
                    extra={"agent_type": agent_type, "error": str(e)[:200]}
                )
                _record_failed_write(
                    event_type=agent_type,
                    concept_id=node_id,
                    canvas_name=canvas_name,
                    score=score,
                    error_reason=str(e)[:200],
                    concept=concept,
                    user_understanding=user_understanding,
                    agent_feedback=agent_feedback,
                )

        # Fire-and-forget: create task but don't await it
        try:
            asyncio.create_task(_write_with_timeout())
            logger.debug(f"[Story 30.4] Memory write task created for {agent_type}")
        except Exception as e:
            # Even task creation failure should be silent
            logger.error(f"[Story 30.4] Failed to create memory write task: {e}")

    def trigger_memory_write_sync(
        self,
        agent_type: str,
        canvas_name: str,
        node_id: str,
        concept: str,
        user_understanding: Optional[str] = None,
        score: Optional[float] = None,
        agent_feedback: Optional[str] = None
    ) -> None:
        """
        Synchronous wrapper for triggering memory write.

        This method can be called from non-async contexts to trigger
        a fire-and-forget memory write. It schedules the async task
        on the current event loop.

        Args:
            agent_type: Name of the agent that completed
            canvas_name: Canvas file name
            node_id: Node ID that was processed
            concept: Concept name or summary
            user_understanding: Optional user's understanding text
            score: Optional score from scoring agent
            agent_feedback: Optional feedback from agent

        [Source: docs/stories/30.4.story.md#Task-2]
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Schedule in running loop
                asyncio.ensure_future(
                    self._trigger_memory_write(
                        agent_type=agent_type,
                        canvas_name=canvas_name,
                        node_id=node_id,
                        concept=concept,
                        user_understanding=user_understanding,
                        score=score,
                        agent_feedback=agent_feedback
                    )
                )
            else:
                # Create new loop if none running
                loop.run_until_complete(
                    self._trigger_memory_write(
                        agent_type=agent_type,
                        canvas_name=canvas_name,
                        node_id=node_id,
                        concept=concept,
                        user_understanding=user_understanding,
                        score=score,
                        agent_feedback=agent_feedback
                    )
                )
        except Exception as e:
            # Silent degradation
            logger.error(f"[Story 30.4] Sync memory trigger failed: {e}")

    # ═══════════════════════════════════════════════════════════════════════════════
    # Story 21.5.4: AI Connection Health Check
    # [Source: docs/stories/21.5.4.story.md]
    # ═══════════════════════════════════════════════════════════════════════════════

    async def test_ai_connection(self) -> Dict[str, Any]:
        """
        Test AI API connection with a minimal request.

        Sends a simple test prompt to verify:
        1. API key is valid
        2. Network connectivity is working
        3. Model is available

        Returns:
            Dict with connection status:
            - status: "ok" or "error"
            - model: Current model name
            - provider: Current provider (google/anthropic/openai/custom)
            - latency_ms: Response time (if successful)
            - error: Error message (if failed)
            - error_code: Error code for diagnosis

        [Source: docs/stories/21.5.4.story.md#AC-21.5.4.2]
        [Source: docs/prd/EPIC-21.5-AGENT-RELIABILITY-FIX.md#story-21-5-4]
        """
        import time

        from app.config import settings

        # Get current AI configuration
        provider = getattr(settings, 'AI_PROVIDER', 'google')
        model = getattr(settings, 'AI_MODEL_NAME', 'gemini-2.0-flash-exp')

        # Check if client is configured
        if not self._use_real_api or not self._gemini_client:
            return {
                "status": "error",
                "model": model,
                "provider": provider,
                "error": "AI client not configured. Check API key settings.",
                "error_code": "LLM_AUTH_FAILED"
            }

        start_time = time.time()

        # [FIX] Bug #4: 400ms was too short for actual AI API calls (typically 2-10s)
        # Changed from 0.4s to 15s to allow real API response
        # Health check latency will be reported separately for monitoring
        AI_HEALTH_CHECK_TIMEOUT = 15.0  # 15s timeout for AI API call

        try:
            # Send minimal test request with timeout
            # ✅ Verified from Context7:/googleapis/python-genai (topic: async generate content)
            # ✅ Verified from Python docs: asyncio.wait_for() for Python 3.9+ timeout
            # [FIX] Bug #2: Method name was 'generate' but should be 'call_agent'
            # [FIX] Bug #3: Parameter name was 'prompt' but should be 'user_prompt'
            response = await asyncio.wait_for(
                self._gemini_client.call_agent(
                    agent_type="basic-decomposition",  # Use simplest agent
                    user_prompt="Reply with exactly: OK",
                    context=None
                ),
                timeout=AI_HEALTH_CHECK_TIMEOUT
            )

            latency_ms = (time.time() - start_time) * 1000

            # Check if we got a valid response
            if response and (response.get("response") or response.get("text")):
                logger.info(
                    f"AI connection test successful: provider={provider}, "
                    f"model={model}, latency={latency_ms:.0f}ms"
                )
                return {
                    "status": "ok",
                    "model": model,
                    "provider": provider,
                    "latency_ms": round(latency_ms, 2)
                }
            else:
                return {
                    "status": "error",
                    "model": model,
                    "provider": provider,
                    "error": "Empty response from AI API",
                    "error_code": "LLM_EMPTY_RESPONSE"
                }

        except asyncio.TimeoutError:
            # P0 Fix: Explicit timeout handling for NFR-3 compliance
            # [Source: docs/qa/gates/21.5.4-agent-health-check-enhancement.yml#PERF-001]
            latency_ms = (time.time() - start_time) * 1000
            logger.warning(
                f"AI connection test timeout: provider={provider}, "
                f"model={model}, timeout={AI_HEALTH_CHECK_TIMEOUT}s, "
                f"latency={latency_ms:.0f}ms"
            )
            return {
                "status": "error",
                "model": model,
                "provider": provider,
                "error": f"AI health check timeout ({AI_HEALTH_CHECK_TIMEOUT}s exceeded)",
                "error_code": "LLM_TIMEOUT",
                "latency_ms": round(latency_ms, 2)
            }

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            error_message = str(e)

            # Classify error type
            error_code = "LLM_UNKNOWN_ERROR"
            if "api key" in error_message.lower() or "authentication" in error_message.lower():
                error_code = "LLM_AUTH_FAILED"
            elif "timeout" in error_message.lower():
                error_code = "LLM_TIMEOUT"
            elif "rate limit" in error_message.lower():
                error_code = "LLM_RATE_LIMITED"
            elif "quota" in error_message.lower():
                error_code = "LLM_QUOTA_EXCEEDED"

            logger.warning(
                f"AI connection test failed: provider={provider}, "
                f"model={model}, error={error_message}, code={error_code}"
            )

            return {
                "status": "error",
                "model": model,
                "provider": provider,
                "error": error_message,
                "error_code": error_code,
                "latency_ms": round(latency_ms, 2)
            }

    # ═══════════════════════════════════════════════════════════════════════════════
    # Story 12.A.6: verification-question and question-decomposition Agents
    # [Source: docs/stories/story-12.A.6-complete-agents.md]
    # ═══════════════════════════════════════════════════════════════════════════════

    async def generate_verification_questions(
        self,
        canvas_name: str,
        node_id: str,
        content: str,
        node_type: str = "red",
        related_yellow: Optional[List[str]] = None,
        parent_content: Optional[str] = None,
        adjacent_context: Optional[str] = None,
        source_x: float = 0,
        source_y: float = 0,
        source_width: float = 400,
        source_height: float = 200,
        rag_context: Optional[str] = None,  # Story 12.A.2: RAG context injection
    ) -> Dict[str, Any]:
        """
        Generate verification questions for a concept node.

        This method implements AC1 and AC3 of Story 12.A.6:
        - Calls ContextEnrichmentService.enrich_with_adjacent_nodes() for context
        - Calls LearningMemoryClient.search_memories() for historical memory
        - Calls record_learning_episode() after generation

        Args:
            canvas_name: Canvas file name
            node_id: Target node ID
            content: Node content to generate questions for
            node_type: Node type ("red" for not understood, "purple" for partially understood)
            related_yellow: List of related yellow node contents (user's understanding)
            parent_content: Optional parent node content for context
            adjacent_context: Context from adjacent nodes
            source_x, source_y: Source node position for new node placement
            source_width, source_height: Source node dimensions
            rag_context: Optional RAG context from 5-source fusion (Story 12.A.2)

        Returns:
            Dict with questions list, concept, generated_at, and created_nodes

        [Source: docs/stories/story-12.A.6-complete-agents.md#AC1]
        [Source: .claude/agents/verification-question-agent.md]
        [Source: Story 12.A.2 Agent-RAG Bridge Layer]
        """
        from datetime import datetime

        call_logger = AgentCallLogger(
            agent_type="verification-question",
            node_id=node_id,
            canvas_name=canvas_name
        )

        # Build input for the verification-question agent
        input_data = {
            "nodes": [{
                "id": node_id,
                "content": content,
                "type": node_type,
                "related_yellow": related_yellow or [],
                "parent_content": parent_content or ""
            }]
        }

        prompt = json.dumps(input_data, ensure_ascii=False, indent=2)
        call_logger.log_request({"content_length": len(content), "node_type": node_type})

        try:
            # AC3a: Adjacent context is passed via adjacent_context parameter
            # AC3b: Query historical memories
            enriched_context = adjacent_context or ""

            # Story 12.A.2: Add RAG context to enriched context
            if rag_context:
                enriched_context = f"{enriched_context}\n\n{rag_context}" if enriched_context else rag_context
                logger.info(f"[Story 12.A.2] Enhanced verification questions context with RAG ({len(rag_context)} chars)")

            result = await self._call_gemini_api(
                agent_type=AgentType.VERIFICATION_QUESTION,
                prompt=prompt,
                context=enriched_context,
                canvas_name=canvas_name,
                node_id=node_id
            )

            # Parse questions from result
            questions = result.get("questions", [])
            call_logger.log_response(result, success=True, response_length=len(str(questions)))

            # Generate Canvas nodes for questions
            created_nodes = []
            created_edges = []
            node_width = 350
            node_height = 150
            gap_y = 40

            for idx, q in enumerate(questions):
                question_node_id = f"vq-{node_id[:8]}-{idx}-{uuid.uuid4().hex[:6]}"

                # Build node text
                node_text = q.get("question_text", "")
                q_type = q.get("question_type", "")
                guidance = q.get("guidance", "")

                if q_type:
                    node_text = f"[{q_type}] {node_text}"
                if guidance:
                    node_text = f"{node_text}\n\n{guidance}"

                # Position nodes vertically below source
                node_x = source_x
                node_y = source_y + source_height + gap_y + idx * (node_height + gap_y)

                created_nodes.append({
                    "id": question_node_id,
                    "type": "text",
                    "text": node_text,
                    "x": node_x,
                    "y": node_y,
                    "width": node_width,
                    "height": node_height,
                    "color": "3",  # Purple - verification question (修复: "3"=Purple)
                })

                # Create edge from source to question
                created_edges.append({
                    "id": f"edge-vq-{uuid.uuid4().hex[:8]}",
                    "fromNode": node_id,
                    "toNode": question_node_id,
                    "fromSide": "bottom",
                    "toSide": "top",
                    "label": EdgeLabels.VERIFICATION,
                })

            # Write nodes to Canvas
            if created_nodes:
                await self._write_nodes_to_canvas(canvas_name, created_nodes, created_edges)

            # AC3c: Record learning episode (Story 30.4: fire-and-forget pattern)
            await self._trigger_memory_write(
                agent_type="verification-question-agent",
                canvas_name=canvas_name,
                node_id=node_id,
                concept=content[:50] if content else "Unknown",
                user_understanding=str(related_yellow) if related_yellow else None,
                agent_feedback=f"Generated {len(questions)} verification questions"
            )

            return {
                "questions": questions,
                "concept": content[:100] if content else "",
                "generated_at": datetime.now().isoformat(),
                "created_nodes": created_nodes,
                "created_edges": created_edges,
                "status": "completed"
            }

        except Exception as e:
            call_logger.log_error(e)
            logger.error(f"generate_verification_questions failed: {e}", exc_info=True)
            raise

    async def decompose_question(
        self,
        canvas_name: str,
        node_id: str,
        content: str,
        user_understanding: str,
        topic: Optional[str] = None,
        adjacent_context: Optional[str] = None,
        source_x: float = 0,
        source_y: float = 0,
        source_width: float = 400,
        source_height: float = 200,
        rag_context: Optional[str] = None,  # Story 12.A.2: RAG context injection
    ) -> Dict[str, Any]:
        """
        Decompose a question into verification sub-questions.

        This method implements AC2 and AC3 of Story 12.A.6:
        - Calls ContextEnrichmentService.enrich_with_adjacent_nodes() for context
        - Calls LearningMemoryClient.search_memories() for historical memory
        - Calls record_learning_episode() after generation

        Args:
            canvas_name: Canvas file name
            node_id: Target node ID
            content: Original material content
            user_understanding: User's understanding (from yellow node)
            topic: Topic name (optional, extracted from content if not provided)
            adjacent_context: Context from adjacent nodes
            source_x, source_y: Source node position for new node placement
            source_width, source_height: Source node dimensions
            rag_context: Optional RAG context from 5-source fusion (Story 12.A.2)

        Returns:
            Dict with questions list and created_nodes

        [Source: docs/stories/story-12.A.6-complete-agents.md#AC2]
        [Source: .claude/agents/question-decomposition.md]
        [Source: Story 12.A.2 Agent-RAG Bridge Layer]
        """
        call_logger = AgentCallLogger(
            agent_type="question-decomposition",
            node_id=node_id,
            canvas_name=canvas_name
        )

        # Build input for the question-decomposition agent
        input_data = {
            "material_content": content,
            "topic": topic or content[:50] if content else "Unknown",
            "user_understanding": user_understanding
        }

        prompt = json.dumps(input_data, ensure_ascii=False, indent=2)
        call_logger.log_request({"content_length": len(content), "understanding_length": len(user_understanding)})

        try:
            # AC3a: Adjacent context is passed via adjacent_context parameter
            # AC3b: Query historical memories via _call_gemini_api
            enriched_context = adjacent_context or ""

            # Story 12.A.2: Add RAG context to enriched context
            if rag_context:
                enriched_context = f"{enriched_context}\n\n{rag_context}" if enriched_context else rag_context
                logger.info(f"[Story 12.A.2] Enhanced question decomposition context with RAG ({len(rag_context)} chars)")

            result = await self._call_gemini_api(
                agent_type=AgentType.QUESTION_DECOMPOSITION,
                prompt=prompt,
                context=enriched_context,
                canvas_name=canvas_name,
                node_id=node_id
            )

            # Parse questions from result
            questions = result.get("questions", [])
            call_logger.log_response(result, success=True, response_length=len(str(questions)))

            # Generate Canvas nodes for questions
            created_nodes = []
            created_edges = []
            node_width = 320
            node_height = 120
            gap_x = 30
            gap_y = 40
            nodes_per_row = 2

            for idx, q in enumerate(questions):
                question_node_id = f"qd-{node_id[:8]}-{idx}-{uuid.uuid4().hex[:6]}"

                # Build node text
                node_text = q.get("text", "")
                q_type = q.get("type", "")
                guidance = q.get("guidance", "")

                if q_type:
                    node_text = f"[{q_type}] {node_text}"
                if guidance:
                    node_text = f"{node_text}\n\n{guidance}"

                # Position nodes in grid below source
                row = idx // nodes_per_row
                col = idx % nodes_per_row
                node_x = source_x + col * (node_width + gap_x)
                node_y = source_y + source_height + gap_y + row * (node_height + gap_y)

                created_nodes.append({
                    "id": question_node_id,
                    "type": "text",
                    "text": node_text,
                    "x": node_x,
                    "y": node_y,
                    "width": node_width,
                    "height": node_height,
                    "color": "3",  # Purple - verification question (修复: "3"=Purple)
                })

                # Create edge from source to question
                created_edges.append({
                    "id": f"edge-qd-{uuid.uuid4().hex[:8]}",
                    "fromNode": node_id,
                    "toNode": question_node_id,
                    "fromSide": "bottom",
                    "toSide": "top",
                    "label": EdgeLabels.QUESTION,
                })

            # Write nodes to Canvas
            if created_nodes:
                await self._write_nodes_to_canvas(canvas_name, created_nodes, created_edges)

            # AC3c: Record learning episode (Story 30.4: fire-and-forget pattern)
            await self._trigger_memory_write(
                agent_type="question-decomposition",
                canvas_name=canvas_name,
                node_id=node_id,
                concept=topic or content[:50] if content else "Unknown",
                user_understanding=user_understanding,
                agent_feedback=f"Decomposed into {len(questions)} verification questions"
            )

            return {
                "questions": questions,
                "created_nodes": created_nodes,
                "created_edges": created_edges,
                "status": "completed"
            }

        except Exception as e:
            call_logger.log_error(e)
            logger.error(f"decompose_question failed: {e}", exc_info=True)
            raise

    # ═══════════════════════════════════════════════════════════════════════════
    # Story 12.G.3: Agent Health Check
    # [Source: docs/stories/story-12.G.3-agent-health-check-endpoint.md]
    # ═══════════════════════════════════════════════════════════════════════════

    async def health_check(self, include_api_test: bool = False) -> Dict[str, Any]:
        """
        Perform health check on Agent system components.

        ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: health check)
        [Source: docs/stories/story-12.G.3-agent-health-check-endpoint.md]
        [Source: specs/api/agent-api.openapi.yml#/paths/~1agents~1health]

        Health Status Logic:
        - unhealthy: API key not configured OR GeminiClient not initialized
        - degraded: Some prompt templates missing
        - healthy: All checks pass

        Args:
            include_api_test: Whether to perform actual API call test (default: False)

        Returns:
            Dict containing health status, checks details, and timestamp
        """
        from datetime import datetime, timezone
        from pathlib import Path

        from app.config import settings

        # Check 1: API key configured (don't expose actual key)
        api_key_configured = bool(settings.AI_API_KEY)

        # Check 2: GeminiClient initialized
        gemini_client_initialized = self._use_real_api

        # Check 3: Prompt templates availability
        # List of expected templates (excluding aliases like FOUR_LEVEL and SCORING)
        expected_templates = [
            "basic-decomposition",
            "deep-decomposition",
            "question-decomposition",
            "oral-explanation",
            "four-level-explanation",
            "clarification-path",
            "comparison-table",
            "example-teaching",
            "memory-anchor",
            "scoring-agent",
            "verification-question-agent",
            "canvas-orchestrator",
        ]

        prompt_path = Path(settings.AGENT_PROMPT_PATH)
        available_templates = []
        missing_templates = []

        for template_name in expected_templates:
            template_file = prompt_path / f"{template_name}.md"
            if template_file.exists():
                available_templates.append(template_name)
            else:
                missing_templates.append(template_name)

        prompt_template_check = {
            "total": len(expected_templates),
            "available": len(available_templates),
            "missing": missing_templates,
        }

        # Check 4: Optional API test
        api_test_result = None
        if include_api_test and self._gemini_client and gemini_client_initialized:
            try:
                # Simple API ping test - just verify connectivity
                # ✅ Verified from gemini_client.py:508 - call_raw method
                test_response = await self._gemini_client.call_raw(
                    system_prompt="You are a test assistant.",
                    user_prompt="Say 'OK' if you can read this.",
                )
                api_test_result = {
                    "enabled": True,
                    "result": "success" if test_response else "empty_response",
                }
            except Exception as e:
                api_test_result = {
                    "enabled": True,
                    "result": str(e),
                }
        else:
            api_test_result = {
                "enabled": False,
                "result": None,
            }

        # Determine overall health status
        # ✅ Verified from Story 12.G.3 AC-1.1, AC-1.2, AC-1.3
        if not api_key_configured or not gemini_client_initialized:
            status = "unhealthy"
        elif len(missing_templates) > 0:
            status = "degraded"
        else:
            status = "healthy"

        return {
            "status": status,
            "checks": {
                "api_key_configured": api_key_configured,
                "gemini_client_initialized": gemini_client_initialized,
                "prompt_templates": prompt_template_check,
                "api_test": api_test_result,
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def cleanup(self) -> None:
        """
        Cleanup resources when service is no longer needed.

        Waits for all active calls to complete before cleanup.

        [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#依赖注入设计]
        """
        # Wait for active calls to complete
        while self._active_calls > 0:
            await asyncio.sleep(0.01)

        self._initialized = False
        logger.debug("AgentService cleanup completed")
