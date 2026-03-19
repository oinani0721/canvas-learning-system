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

    messages: list[DistillMessage] = Field(..., min_length=1, description="Conversation messages to distill")
    group_id: Optional[str] = Field(None, description="Subject isolation namespace")


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
async def distill_conversation(node_id: str, request: DistillRequest) -> DistillResponse:
    """Distill a conversation and persist results for Edge inheritance.

    Called by frontend after a dialogue session ends. The distillation result
    is stored in MemoryService with episode_type="conversation_distillation"
    and becomes queryable by ConversationInheritanceService.

    Non-blocking design: returns quickly even if distillation takes time.
    Failure returns success=false with empty results (graceful degradation).
    """
    try:
        from app.config import DEFAULT_GROUP_ID
        from app.services.conversation_distiller import ConversationDistiller

        group_id = request.group_id or DEFAULT_GROUP_ID
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
