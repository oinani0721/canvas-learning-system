# Canvas Learning System - Tips API Endpoint
# Story 3.6: Tips Writing to Graphiti (AC-2)
#
# POST /api/v1/tips - Save a user-annotated tip to Graphiti
#
# The tip contains selected text from dialogue, a user-provided title,
# and classification tags. It is written to Graphiti via the
# Agent self-report channel for future context injection (Story 3.4).
#
# [Source: _bmad-output/implementation-artifacts/3-6-tips-annotation-error-archiving.md#Task 2.4]

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

tips_router = APIRouter()


# ═══════════════════════════════════════════════════════════════════════════════
# Request / Response Models
# ═══════════════════════════════════════════════════════════════════════════════


class SaveTipRequest(BaseModel):
    """Request body for saving a tip annotation."""

    content: str = Field(..., min_length=1, description="The selected text content")
    title: str = Field(..., min_length=1, description="User-provided title for the tip")
    tags: List[str] = Field(
        default_factory=list,
        description="Classification tags: important, confused, inspiration, review",
    )
    node_id: str = Field(..., description="Source canvas node ID")
    source_timestamp: str = Field(
        ..., description="ISO timestamp of the source dialogue message"
    )


class SaveTipResponse(BaseModel):
    """Response after saving a tip."""

    tip_id: str
    saved: bool
    status: str = "ok"
    message: str = ""


# ═══════════════════════════════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════════════════════════════


class TipItem(BaseModel):
    """A single tip in the GET response."""

    tip_id: str
    content: str
    title: str
    tags: List[str] = Field(default_factory=list)
    node_id: str
    created_at: str = ""


class GetTipsResponse(BaseModel):
    """Response from GET /tips endpoint."""

    tips: List[TipItem]
    total: int


@tips_router.get(
    "",
    response_model=GetTipsResponse,
    summary="Get tips for a node from Graphiti",
    description="Retrieve all tip annotations for a given canvas node.",
)
async def get_tips(
    node_id: str,
) -> Dict[str, Any]:
    """
    Retrieve tips for a canvas node from Graphiti memory.

    Story 3.6: GET endpoint for frontend to read saved tips.

    Args:
        node_id: The canvas node ID to fetch tips for.

    Returns:
        GetTipsResponse with list of tips and total count.
    """
    try:
        from app.config import DEFAULT_GROUP_ID
        from app.services.memory_service import get_memory_service

        memory_svc = await get_memory_service()

        # Search for tips related to this node
        results = await memory_svc.search_memories(
            query=f"learning_tip node_id:{node_id}",
            group_id=DEFAULT_GROUP_ID,
            limit=50,
        )

        tips: List[Dict[str, Any]] = []
        seen_tip_ids: set = set()
        for item in results:
            metadata = item.get("metadata", {})
            tip_id = metadata.get("tip_id")
            if metadata.get("node_id") == node_id and tip_id:
                # Deduplicate by tip_id to avoid repeated content
                if tip_id in seen_tip_ids:
                    continue
                seen_tip_ids.add(tip_id)
                tips.append(
                    TipItem(
                        tip_id=tip_id,
                        content=metadata.get("content", ""),
                        title=metadata.get("title", "Untitled"),
                        tags=metadata.get("tags", []),
                        node_id=node_id,
                        created_at=metadata.get("created_at", ""),
                    ).model_dump()
                )

        return GetTipsResponse(
            tips=tips,
            total=len(tips),
        ).model_dump()

    except Exception as e:
        logger.warning(f"[Story 3.6] Failed to get tips for node {node_id}: {e}")
        return GetTipsResponse(tips=[], total=0).model_dump()


@tips_router.post(
    "",
    response_model=SaveTipResponse,
    summary="Save a tip annotation to Graphiti",
    description="Save a user-annotated tip (selected dialogue text) to the "
    "Graphiti learning memory. The tip becomes available for future "
    "context injection (Story 3.4).",
)
async def save_tip(request: SaveTipRequest) -> Dict[str, Any]:
    """
    Save a tip annotation to Graphiti.

    Story 3.6 AC-2: User clicks "Write Tips" -> tip saved to Graphiti.
    The tip data includes: content (selected text), title (user input),
    tags, source node ID, and source dialogue timestamp.

    Args:
        request: The tip data to save.

    Returns:
        SaveTipResponse with tip_id and status.
    """
    tip_id = str(uuid.uuid4())

    try:
        from app.config import DEFAULT_GROUP_ID
        from app.services.memory_service import get_memory_service

        memory_svc = await get_memory_service()

        # Build tip content for Graphiti
        tags_str = ", ".join(request.tags) if request.tags else "none"

        await memory_svc.record_knowledge_entity(
            event_type="learning_tip",
            content=(
                f"Tip: {request.title} | Content: {request.content} | "
                f"Tags: {tags_str}"
            ),
            metadata={
                "tip_id": tip_id,
                "title": request.title,
                "content": request.content,
                "tags": request.tags,
                "node_id": request.node_id,
                "source_timestamp": request.source_timestamp,
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
            group_id=DEFAULT_GROUP_ID,
        )

        logger.info(
            f"[Story 3.6] Tip saved: id={tip_id} node={request.node_id} "
            f"title={request.title[:50]}"
        )

        return SaveTipResponse(
            tip_id=tip_id,
            saved=True,
            status="ok",
            message="Tips saved successfully",
        ).model_dump()

    except Exception as e:
        logger.error(f"[Story 3.6] Failed to save tip: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save tip: {str(e)}",
        ) from e
