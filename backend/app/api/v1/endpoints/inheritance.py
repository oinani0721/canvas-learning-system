"""
Conversation Inheritance Endpoints — F9 distillation trigger.

PRD: "Edge 标签语义检索 + LLM 摘要的分层継承方案"

Provides an endpoint for the frontend to trigger conversation distillation
after a dialogue session ends. The distillation result is stored in MemoryService
and becomes available for future Edge-based context inheritance.

Callers:
- Frontend chat-store.ts — triggers distillation on conversation 'done' event
"""

import logging
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

inheritance_router = APIRouter()


class DistillMessage(BaseModel):
    """A single message in a conversation to be distilled."""

    role: str = Field(..., description="Message role: user, assistant, or error")
    content: str = Field(..., description="Message text content")


class DistillRequest(BaseModel):
    """Request body for conversation distillation."""

    messages: list[DistillMessage] = Field(
        ..., min_length=1, description="Conversation messages to distill"
    )
    # CARD-G2-2 (2026-08-28): 加 vault_id (推荐); raw group_id 降级为
    # deprecated legacy 输入, 不再直通持久化链 (Codex round-1 HIGH-8)。
    vault_id: Optional[str] = Field(
        None, description="Vault 身份 (推荐必填; 与 active vault 不一致时 409)"
    )
    group_id: Optional[str] = Field(
        None, deprecated=True, description="Deprecated — 改用 vault_id"
    )


class DistillResponse(BaseModel):
    """Response from conversation distillation."""

    success: bool
    summary: str = ""
    tip_count: int = 0
    error_count: int = 0
    qa_count: int = 0


@inheritance_router.post(
    "/chat/{node_id}/distill",
    response_model=DistillResponse,
    summary="Trigger conversation distillation for a node",
    description="Distill a conversation into summary, tips, errors, and Q&A highlights. "
    "Results are persisted to MemoryService for future Edge-based inheritance.",
)
async def distill_conversation(
    node_id: str, request: DistillRequest
) -> DistillResponse:
    """Distill a conversation and persist results for Edge inheritance.

    Called by frontend after a dialogue session ends. The distillation result
    is stored in MemoryService with episode_type="conversation_distillation"
    and becomes queryable by ConversationInheritanceService.

    Non-blocking design: returns quickly even if distillation takes time.
    Failure returns success=false with empty results (graceful degradation).
    """
    # CARD-G2-2 Codex round-1 HIGH-8 整改: raw group_id 不再直通持久化链 —
    # 显式 vault_id 走 409 门, 旧 group 作 legacy 输入归一化, 双缺失推导
    # active vault。解析在 try 之外 (409 不得被宽 except 吞成 success=false)。
    from app.core.vault_scope import resolve_vault_group_id

    group_id = resolve_vault_group_id(
        request.vault_id, legacy_group_id=request.group_id
    )

    try:
        from app.services.conversation_distiller import ConversationDistiller
        messages = [{"role": m.role, "content": m.content} for m in request.messages]

        distiller = ConversationDistiller()
        result = await distiller.distill_and_persist(
            messages=messages,
            node_id=node_id,
            group_id=group_id,
        )

        return DistillResponse(
            success=True,
            summary=result.summary or "",
            tip_count=len(result.tips) if result.tips else 0,
            error_count=len(result.errors) if result.errors else 0,
            qa_count=len(result.qa_highlights) if result.qa_highlights else 0,
        )

    except Exception as e:
        logger.warning("Distillation failed for node %s: %s", node_id, e)
        return DistillResponse(success=False)
