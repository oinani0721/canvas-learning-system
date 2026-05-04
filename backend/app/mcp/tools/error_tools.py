# Canvas Learning System - MCP Error Tools
# Story 3.6: Error Classification MCP Tool (AC-3, AC-4)
#
# Tools: record_error
# Provides Agent access to the 4-type error classification system.
# Agent calls this tool when it detects a student understanding error.
#
# [Source: _bmad-output/implementation-artifacts/3-6-tips-annotation-error-archiving.md#Task 3.1]

import asyncio
import logging
from typing import Any, Dict, Optional

# Note: asyncio.TimeoutError is used for narrowed exception handling in service calls
from pydantic import BaseModel, Field

from app.audit.guardian import get_audit_guardian

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Pydantic Models
# ═══════════════════════════════════════════════════════════════════════════════


class RecordErrorInput(BaseModel):
    """Input schema for record_error tool.

    Story 2.5 (2026-05-04): 加可选 sub_tags 字段支持 SUPERFICIAL 二义消解.
    """

    node_id: str = Field(..., description="The canvas node identifier.")
    session_id: str = Field(..., description="The dialogue session identifier.")
    error_description: str = Field(
        ..., description="Description of the student's understanding error."
    )
    context: str = Field(
        default="",
        description="Dialogue context where the error was detected.",
    )
    sub_tags: list[str] = Field(
        default_factory=list,
        description=(
            "Story 2.5 — Optional sub-tags (e.g. transfer_failure, "
            "synonym_confusion) for SUPERFICIAL pedagogy disambiguation."
        ),
    )


class RecordErrorOutput(BaseModel):
    """Output schema for record_error tool.

    Story 2.5 (2026-05-04): 加 pedagogy_type / pedagogy_remedies / confidence
    / frontmatter_written / graphiti_written 字段, 向后兼容地保留 Story 3.6 字段.
    """

    node_id: str
    recorded: bool
    misconception_id: Optional[str] = None
    # Story 3.6 legacy fields (保留向后兼容)
    error_type: Optional[str] = None  # legacy ErrorType (problem_framing 等)
    error_type_label: Optional[str] = None
    remedy_strategy: Optional[str] = None  # legacy RemedyStrategy
    remedy_description: Optional[str] = None
    # Story 2.5 — D 方案双标签新增字段
    pedagogy_type: Optional[str] = Field(
        default=None,
        description="Story 2.5 PRD §FR-CONV-06 4 主类 (conceptual_confusion / "
        "procedural_error / careless_slip / metacognitive_error).",
    )
    pedagogy_remedies: list[str] = Field(
        default_factory=list,
        description="Story 2.5 PRD AC #3 补救策略列表 (1+ 项).",
    )
    confidence: Optional[float] = Field(
        default=None,
        description="LLM 分类置信度 [0,1]. < 0.6 视为 AMBIGUOUS (PRD AC #2).",
    )
    is_ambiguous: bool = Field(
        default=False,
        description="confidence < 0.6 时为 True.",
    )
    frontmatter_written: bool = Field(
        default=False,
        description="Story 2.5 Task 4: 是否成功写入 .md frontmatter errors[].",
    )
    graphiti_status: str = Field(
        default="not_attempted",
        description="Story 2.5 Task 4: scheduled / ok / failed / "
        "skipped_frontmatter_failed / not_attempted.",
    )
    status: str = "ok"
    message: str = ""


# ═══════════════════════════════════════════════════════════════════════════════
# Tool Implementation
# ═══════════════════════════════════════════════════════════════════════════════


def _resolve_node_file_path(node_id: str) -> Optional[str]:
    """Story 2.5 — 从 node_id 推断 .md 文件绝对路径.

    node_id 形式可能是:
    - "节点/X" → vault_root/节点/X.md
    - "节点/X.md" → vault_root/节点/X.md
    - "X" → vault_root/X.md (vault root level)
    - 已经是绝对路径 → 直接返回

    返回 None 表示无法解析 (vault_root 不存在 / settings 不可用).
    """
    from pathlib import Path

    try:
        from app.config import settings

        vault_root_str = getattr(settings, "canvas_base_path", None)
        if not vault_root_str:
            return None
        vault_root = Path(vault_root_str)
        if not vault_root.exists():
            return None

        candidate = Path(node_id)
        if not candidate.is_absolute():
            candidate = vault_root / node_id
        if not str(candidate).endswith(".md"):
            candidate = candidate.with_suffix(".md")
        return str(candidate)
    except (ImportError, AttributeError, OSError):
        return None


async def record_error(
    node_id: str,
    session_id: str,
    error_description: str,
    context: str = "",
    sub_tags: Optional[list[str]] = None,
) -> Dict[str, Any]:
    """Record and classify a student understanding error (Story 2.5 Task 5 升级).

    Story 3.6 AC-3 (legacy): Agent calls this tool when detecting user errors.
    Story 2.5 (2026-05-04 D 方案 + Task 4 双写):
    - 调 classify_with_pedagogy() 拿双标签 (legacy + pedagogy)
    - 调 write_error_dual() 同步写 frontmatter + fire-and-forget Graphiti
    - confidence < 0.6 → is_ambiguous=True (PRD AC #2)
    - 向后兼容: input/output schema 旧字段保留, 新字段都是 optional

    AC #4 + #6: frontmatter 本地优先, Graphiti 失败仍 recorded=True (本地成功).

    Args:
        node_id: Canvas 节点 ID (作为 vault-relative path 使用, 推断 .md file).
        session_id: 对话 session ID.
        error_description: 学习者错误描述.
        context: 对话上下文.
        sub_tags: 可选 sub_tags (Story 2.5 SUPERFICIAL 二义消解用).

    Returns:
        RecordErrorOutput (含双标签 + frontmatter/graphiti 状态).
    """
    guardian = get_audit_guardian()
    asyncio.create_task(guardian.record_tool_call("record_error", session_id, node_id))

    try:
        from app.graphiti.entity_types import ERROR_TYPE_DESCRIPTIONS
        from app.services.error_classifier import get_error_classifier
        from app.services.error_writer import (
            write_error_dual,
            write_error_to_graphiti,
        )

        classifier = get_error_classifier()

        # Story 2.5 — 双标签分类
        classified = await classifier.classify_with_pedagogy(
            error_description=error_description,
            node_id=node_id,
            session_id=session_id,
            context=context,
            sub_tags=sub_tags or [],
        )
        legacy_type_info = ERROR_TYPE_DESCRIPTIONS.get(classified.legacy_type, {})

        # Story 2.5 Task 4 — 双写 (frontmatter + Graphiti fire-and-forget)
        file_path = _resolve_node_file_path(node_id)
        if file_path:
            dual_result = await write_error_dual(
                file_path=file_path,
                error=classified,
                node_id=node_id,
                session_id=session_id,
                fire_and_forget_graphiti=True,
            )
            fm_written = dual_result["frontmatter"]
            graphiti_status = dual_result["graphiti"]
        else:
            # vault_root 不可用 → 跳过 frontmatter, Graphiti 同步尝试
            logger.warning(
                f"[Story 2.5] record_error: vault_root unavailable for "
                f"node_id={node_id}, skipping frontmatter; trying Graphiti only"
            )
            fm_written = False
            graphiti_ok = await write_error_to_graphiti(
                classified, node_id, session_id
            )
            graphiti_status = "ok" if graphiti_ok else "failed"

        # 生成 misconception_id (向后兼容 Story 3.6 输出 schema)
        import uuid

        misconception_id = str(uuid.uuid4())

        logger.info(
            f"[Story 2.5] record_error: pedagogy={classified.pedagogy_type.value} "
            f"legacy={classified.legacy_type.value} node={node_id} "
            f"fm_written={fm_written} graphiti={graphiti_status}"
        )

        return RecordErrorOutput(
            node_id=node_id,
            recorded=fm_written or graphiti_status in ("ok", "scheduled"),
            misconception_id=misconception_id,
            # Story 3.6 legacy fields (保持向后兼容)
            error_type=classified.legacy_type.value,
            error_type_label=legacy_type_info.get("label_zh", ""),
            remedy_strategy=classified.legacy_remedy.value,
            remedy_description=legacy_type_info.get("remedy_zh", ""),
            # Story 2.5 D 方案新字段
            pedagogy_type=classified.pedagogy_type.value,
            pedagogy_remedies=[r.value for r in classified.pedagogy_remedies],
            confidence=classified.confidence,
            is_ambiguous=classified.is_ambiguous,
            frontmatter_written=fm_written,
            graphiti_status=graphiti_status,
            status="ok",
            message=(
                f"Error classified pedagogy={classified.pedagogy_type.value} "
                f"(legacy={classified.legacy_type.value}, "
                f"confidence={classified.confidence:.2f})"
            ),
        ).model_dump()

    except ImportError as e:
        logger.warning(f"[Story 2.5] record_error: service not available: {e}")
        return RecordErrorOutput(
            node_id=node_id,
            recorded=False,
            status="service_unavailable",
            message=str(e),
        ).model_dump()
    except Exception as e:
        logger.error(f"[Story 2.5] record_error error: {e}")
        return RecordErrorOutput(
            node_id=node_id,
            recorded=False,
            status="error",
            message=str(e),
        ).model_dump()
