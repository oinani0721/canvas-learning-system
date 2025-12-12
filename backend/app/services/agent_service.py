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
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    from app.clients.gemini_client import GeminiClient
    from app.clients.graphiti_client import LearningMemoryClient

logger = logging.getLogger(__name__)


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
    CANVAS_ORCHESTRATOR = "canvas-orchestrator"


@dataclass
class AgentResult:
    """
    Agent调用结果数据类
    [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层]
    """
    agent_type: AgentType
    node_id: str = ""
    success: bool = True
    result: Optional[Dict[str, Any]] = None
    data: Optional[Dict[str, Any]] = None  # Alias for result
    error: Optional[str] = None
    duration_ms: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Ensure data and result are synchronized"""
        if self.data is None and self.result is not None:
            self.data = self.result
        elif self.result is None and self.data is not None:
            self.result = self.data

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "agent_type": self.agent_type.value,
            "node_id": self.node_id,
            "success": self.success,
            "result": self.result,
            "data": self.data,
            "error": self.error,
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

    Args:
        response: AI API响应对象（可能是dict、对象或字符串）

    Returns:
        Tuple[str, bool]: (提取的文本, 是否成功)
            - text: 提取的文本内容（去除首尾空白）
            - success: True如果成功提取到非空文本

    [Source: docs/prd/EPIC-21-AGENT-E2E-FLOW-FIX.md#story-21-3]
    """
    if response is None:
        logger.warning("extract_explanation_text: response is None")
        return "", False

    extractors = [
        # 优先级1: response字段（Gemini常用格式）
        ("response", lambda r: r.get("response") if isinstance(r, dict) else None),
        # 优先级2: text属性（某些SDK的响应对象）
        ("text_attr", lambda r: r.text if hasattr(r, "text") and r.text else None),
        # 优先级3: dict的text字段
        ("text_key", lambda r: r.get("text") if isinstance(r, dict) else None),
        # 优先级4: dict的content字段
        ("content", lambda r: r.get("content") if isinstance(r, dict) else None),
        # 优先级5: dict的explanation字段
        ("explanation", lambda r: r.get("explanation") if isinstance(r, dict) else None),
        # 优先级6: dict的message字段
        ("message", lambda r: r.get("message") if isinstance(r, dict) else None),
        # 优先级7: dict的output字段
        ("output", lambda r: r.get("output") if isinstance(r, dict) else None),
        # 优先级8: 如果response本身是字符串
        ("direct_str", lambda r: r if isinstance(r, str) else None),
        # 优先级9: 字符串化（最终fallback）
        ("stringify", lambda r: str(r) if r else None),
    ]

    for name, extractor in extractors:
        try:
            text = extractor(response)
            if text and isinstance(text, str) and text.strip():
                if name != "response" and name != "text_attr":
                    logger.info(
                        f"extract_explanation_text: Used fallback extractor '{name}' "
                        f"for response type: {type(response).__name__}"
                    )
                return text.strip(), True
        except Exception as e:
            logger.debug(f"extract_explanation_text: Extractor '{name}' failed: {e}")

    # 所有提取器都失败
    logger.error(
        f"extract_explanation_text: All extractors failed for response type: {type(response).__name__}",
        extra={
            "response_type": type(response).__name__,
            "response_preview": str(response)[:500] if response else "None"
        }
    )
    return "", False


def create_error_response(
    error_message: str,
    source_node_id: str,
    agent_type: str,
    source_x: int = 0,
    source_y: int = 0,
    source_width: int = 400,
    source_height: int = 200,
) -> Dict[str, Any]:
    """
    创建友好的错误响应，在Canvas中显示错误提示节点。

    当Agent处理失败时，创建一个红色错误节点而不是返回空结果，
    让用户清楚地知道发生了什么问题。

    Args:
        error_message: 错误描述信息
        source_node_id: 源节点ID
        agent_type: Agent类型
        source_x, source_y: 源节点位置
        source_width, source_height: 源节点尺寸

    Returns:
        包含错误节点和元数据的响应字典

    [Source: docs/prd/EPIC-21-AGENT-E2E-FLOW-FIX.md#story-21-3]
    """
    error_node_id = f"error-{agent_type}-{uuid.uuid4().hex[:8]}"

    # 位置在源节点右侧
    error_x = source_x + source_width + 50
    error_y = source_y

    logger.warning(
        f"create_error_response: Creating error node for {agent_type}",
        extra={
            "source_node_id": source_node_id,
            "agent_type": agent_type,
            "error_message": error_message
        }
    )

    return {
        "created_nodes": [{
            "id": error_node_id,
            "type": "text",
            "text": f"⚠️ Agent处理失败\n\n**错误**: {error_message}\n\n**Agent类型**: {agent_type}\n\n请检查输入内容后重试。",
            "color": "1",  # 红色表示错误
            "x": error_x,
            "y": error_y,
            "width": 400,
            "height": 200
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
        "source_node_id": source_node_id
    }


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
    "color": "3"  # 黄色 - 表示待填写的个人理解区域
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
        "color": "3"  # 黄色，与个人理解节点匹配
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
            max_concurrent: Maximum concurrent agent calls (default: 10)
            ai_config: AIConfig dataclass with provider, model, base_url, api_key.
                      Used for future multi-provider support.

        [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#依赖注入设计]
        [Source: docs/prd/sprint-change-proposal-20251208.md - Story 20.4]
        [Source: FIX-4.2 Agent调用时查询历史]
        [Source: Multi-Provider AI Architecture]
        """
        self._gemini_client = gemini_client
        self._memory_client = memory_client
        self._max_concurrent = max_concurrent
        self._ai_config = ai_config  # Store for future multi-provider support
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._total_calls = 0
        self._active_calls = 0
        self._initialized = True
        self._use_real_api = gemini_client is not None and gemini_client.is_configured()

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

        logger.debug(f"AgentService max_concurrent={max_concurrent}")

    @property
    def total_calls(self) -> int:
        """Total number of agent calls made"""
        return self._total_calls

    @property
    def active_calls(self) -> int:
        """Current number of active agent calls"""
        return self._active_calls

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
        # FIX-4.2: Query historical memories before calling Claude
        enriched_context = context or ""

        if self._memory_client and (canvas_name or prompt):
            try:
                # Search for relevant memories
                query = prompt[:100] if prompt else ""
                memories = await self._memory_client.search_memories(
                    query=query,
                    canvas_name=canvas_name,
                    node_id=node_id,
                    limit=5
                )

                if memories:
                    memory_context = self._memory_client.format_for_context(memories)
                    if memory_context:
                        enriched_context = f"{enriched_context}\n\n{memory_context}" if enriched_context else memory_context
                        logger.debug(f"Added {len(memories)} historical memories to context")

            except Exception as e:
                logger.warning(f"Failed to query historical memories: {e}")
                # Continue without memories - graceful degradation

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

        Args:
            agent_type: Type of agent to call
            prompt: Input prompt for the agent
            timeout: Optional timeout in seconds
            context: Optional additional context for the agent

        Returns:
            AgentResult with the response

        [Source: docs/prd/sprint-change-proposal-20251208.md - Story 20.4]
        """
        start_time = datetime.now()
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
            except asyncio.TimeoutError:
                return AgentResult(
                    agent_type=agent_type,
                    success=False,
                    error="Agent call timed out",
                )
            except Exception as e:
                logger.error(f"Agent call failed: {agent_type.value} - {e}")
                return AgentResult(
                    agent_type=agent_type,
                    success=False,
                    error=str(e),
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
        deep: bool = False
    ) -> AgentResult:
        """
        Call decomposition agent.

        Args:
            content: Content to decompose
            deep: If True, use deep decomposition

        Returns:
            AgentResult with decomposition
        """
        agent_type = AgentType.DEEP_DECOMPOSITION if deep else AgentType.BASIC_DECOMPOSITION
        return await self.call_agent(agent_type, content)

    async def call_scoring(
        self,
        node_content: str,
        user_understanding: str
    ) -> AgentResult:
        """
        Call scoring agent.

        Args:
            node_content: Original node content
            user_understanding: User's explanation

        Returns:
            AgentResult with scores
        """
        prompt = f"Content: {node_content}\nUser: {user_understanding}"
        return await self.call_agent(AgentType.SCORING, prompt)

    async def call_explanation(
        self,
        content: str,
        explanation_type: str = "oral",
        context: Optional[str] = None,
        images: Optional[List[Dict[str, Any]]] = None
    ) -> AgentResult:
        """
        Call explanation agent with optional multimodal support.

        Args:
            content: Content to explain
            explanation_type: Type of explanation
            context: Optional additional context (adjacent nodes, textbook refs, etc.)
            images: Optional list of images for multimodal analysis

        Returns:
            AgentResult with explanation

        [Source: FIX-1.1 修复上下文传递链]
        [Source: FIX-2.1 实现Claude Vision多模态支持]
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

        # ✅ FIX-2.1: Use multimodal call if images are provided
        if images and len(images) > 0:
            logger.info(f"Calling {agent_type.value} with {len(images)} images")
            return await self.call_agent_with_images(
                agent_type, content, images=images, context=context
            )

        # ✅ FIX-1.1: Pass context to call_agent for adjacent node enrichment
        return await self.call_agent(agent_type, content, context=context)

    async def decompose_basic(
        self,
        canvas_name: str,
        node_id: str,
        content: str,
        source_x: float = 0,
        source_y: float = 0
    ) -> Dict[str, Any]:
        """
        Perform basic decomposition on a concept node.

        Args:
            canvas_name: Target canvas name
            node_id: ID of node to decompose
            content: Node content to decompose
            source_x: X coordinate of source node (for positioning new nodes)
            source_y: Y coordinate of source node (for positioning new nodes)

        Returns:
            Decomposition result with guiding questions and created_nodes for Canvas

        [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层]
        [FIX: Return created_nodes array for frontend to write to Canvas]
        """
        import uuid

        logger.debug(f"Basic decomposition for node {node_id}")
        result = await self.call_decomposition(content, deep=False)

        # Extract questions from AI result
        questions = []
        created_nodes = []

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
                created_nodes.append({
                    "id": f"q-{node_id}-{idx}-{uuid.uuid4().hex[:8]}",
                    "type": "text",
                    "text": node_text,
                    "x": x,
                    "y": y,
                    "width": node_width,
                    "height": node_height,
                    "color": "3",  # Yellow - indicates question/understanding area
                })

        logger.info(f"Basic decomposition created {len(created_nodes)} nodes")
        return {
            "node_id": node_id,
            "questions": questions,
            "created_nodes": created_nodes,
            "status": "completed",
            "result": result.data,
        }

    async def decompose_deep(
        self,
        canvas_name: str,
        node_id: str,
        content: str,
        source_x: float = 0,
        source_y: float = 0
    ) -> Dict[str, Any]:
        """
        Perform deep decomposition for verification questions.

        Args:
            canvas_name: Target canvas name
            node_id: ID of node to decompose
            content: Node content to decompose
            source_x: X coordinate of source node for positioning
            source_y: Y coordinate of source node for positioning

        Returns:
            Deep verification questions and created nodes

        [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层]
        """
        import uuid
        logger.debug(f"Deep decomposition for node {node_id}")
        result = await self.call_decomposition(content, deep=True)

        verification_questions = []
        created_nodes = []

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
                created_nodes.append({
                    "id": f"vq-{node_id}-{idx}-{uuid.uuid4().hex[:8]}",
                    "type": "text",
                    "text": node_text,
                    "x": x,
                    "y": y,
                    "width": node_width,
                    "height": node_height,
                    "color": "6",  # Purple - indicates verification/deep question
                })

        logger.info(f"Deep decomposition created {len(created_nodes)} nodes")
        return {
            "node_id": node_id,
            "verification_questions": verification_questions,
            "created_nodes": created_nodes,
            "status": "completed",
            "result": result.data,
        }

    async def score_node(
        self,
        canvas_name: str,
        node_ids: List[str],
        node_contents: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Score multiple nodes' understanding.

        Args:
            canvas_name: Target canvas name
            node_ids: List of node IDs to score
            node_contents: Dict mapping node_id to content text

        Returns:
            {"scores": [{"node_id": ..., "accuracy": ..., ...}]}

        [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层]
        [Source: FIX-4.2 记录学习历程]
        [Source: FIX-5.1 修复score_node签名不匹配]
        """
        logger.debug(f"Scoring {len(node_ids)} nodes")

        scores = []
        for node_id in node_ids:
            content = node_contents.get(node_id, "")

            # Call scoring for each node
            result = await self.call_scoring("", content)

            # Determine color based on score
            total_score = 0.0
            if result.success and result.data:
                total_score = result.data.get("total", 0.0)

            # Color mapping: 0-40% red, 40-70% yellow, 70%+ green
            if total_score >= 0.7:
                new_color = "4"  # green
            elif total_score >= 0.4:
                new_color = "3"  # yellow
            else:
                new_color = "1"  # red

            scores.append({
                "node_id": node_id,
                "accuracy": result.data.get("accuracy", 0.0) if result.data else 0.0,
                "imagery": result.data.get("imagery", 0.0) if result.data else 0.0,
                "completeness": result.data.get("completeness", 0.0) if result.data else 0.0,
                "originality": result.data.get("originality", 0.0) if result.data else 0.0,
                "total": total_score,
                "new_color": new_color,
            })

            # Record learning episode
            await self.record_learning_episode(
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

        # 从关联节点中找出黄色节点（color: "3"）并读取内容
        for node_id in related_node_ids:
            node = nodes.get(node_id)
            if node and node.get("color") == "3":  # Yellow node
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
        source_height: float = 200
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

        Returns:
            Generated explanation with created_nodes for Canvas

        [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层]
        [Source: FIX-1.1 修复上下文传递链 - adjacent_context now flows through]
        [Source: FIX-2.1 实现Claude Vision多模态支持]
        [Source: FIX-3.0 返回created_nodes数组用于Canvas写入]
        """
        import json as json_module  # Avoid conflict with local variables
        import uuid

        context_len = len(adjacent_context) if adjacent_context else 0
        images_count = len(images) if images else 0
        logger.debug(f"Generating {explanation_type} explanation for node {node_id}, context_len={context_len}, images={images_count}")

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

                # 查找关联的黄色理解节点内容
                user_understandings = await self.find_related_understanding_content(
                    canvas_name, node_id, canvas_data
                )
                logger.info(f"[FIX-4.4] Found {len(user_understandings)} user understandings for node {node_id}")
        except Exception as e:
            logger.warning(f"[FIX-4.4] Failed to read user understandings: {e}")

        # ✅ FIX-4.4: 构建包含用户理解的增强上下文
        enhanced_context = adjacent_context or ""
        if user_understandings:
            user_context = "\n\n## 用户之前的个人理解\n\n"
            for i, understanding in enumerate(user_understandings, 1):
                user_context += f"### 理解 {i}\n{understanding}\n\n"
            user_context += "请结合用户的这些理解，生成更贴合用户认知水平的解释。如果用户理解有误，请在解释中委婉纠正。\n"
            enhanced_context = (enhanced_context + user_context) if enhanced_context else user_context
            logger.info(f"[FIX-4.4] Enhanced context with {len(user_understandings)} user understandings")

        # ✅ FIX-1.1: Pass adjacent_context to call_explanation
        # ✅ FIX-2.1: Pass images for multimodal support
        # ✅ FIX-4.4: Pass enhanced_context with user understandings
        result = await self.call_explanation(
            content, explanation_type, context=enhanced_context, images=images
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
            # Return error response instead of empty result
            return create_error_response(
                error_message="无法从AI响应中提取有效内容",
                source_node_id=node_id,
                agent_type=explanation_type,
                source_x=source_x,
                source_y=source_y,
                source_width=source_width,
                source_height=source_height,
            )

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
                        "color": "6",  # ✅ FIX-4.11: Purple (matches user's reference node)
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
                        "color": "6",  # ✅ Purple edge (matches user's reference)
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
                        "color": "3",  # Yellow - 待填写的个人理解区域
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
                        "color": "3",  # Yellow edge matches node
                    })
                    logger.info("[Story 21.5] Created edges for standard explanation with personal node")
                else:
                    logger.debug("[Story 21.5] AUTO_CREATE_PERSONAL_NODE=False, skipping personal node")

        return {
            "node_id": node_id,
            "explanation_type": explanation_type,
            "explanation": explanation_text,  # ✅ Now contains actual AI response
            "created_node_id": created_node_id,  # ✅ Required by ExplainResponse
            "created_nodes": created_nodes,  # ✅ FIX-3.0: Nodes for Canvas
            "created_edges": created_edges,  # ✅ FIX-4.1: Edges for Canvas
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
