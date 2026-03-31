# Canvas Learning System - Archive API Endpoints
# Story 3.8: Conversation Archive REST API (AC-1)
#
# POST /api/v1/archive/trigger   - Manual trigger archive check
# GET  /api/v1/archive/status/{node_id} - Query node archive status
# GET  /api/v1/archive/summary/{node_id} - Get Warm stage summary
#
# [Source: _bmad-output/implementation-artifacts/3-8-dialog-archive-async-generation.md#Task 6]

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

archive_router = APIRouter()


# ═══════════════════════════════════════════════════════════════════════════════
# Response Models
# ═══════════════════════════════════════════════════════════════════════════════


class ArchiveTriggerResponse(BaseModel):
    """Response from manual archive trigger."""

    checked: int = 0
    archived: int = 0
    results: list = Field(default_factory=list)
    error: Optional[str] = None


class NodeArchiveStatusResponse(BaseModel):
    """Archive status for a specific node."""

    node_id: str
    tier: str = "hot"
    message_count: int = 0
    estimated_tokens: int = 0
    has_summary: bool = False
    has_structured_data: bool = False
    last_archived_at: Optional[str] = None


class ArchiveSummaryResponse(BaseModel):
    """Conversation summary from Warm archive."""

    node_id: str
    summary: str = ""
    tip_count: int = 0
    error_count: int = 0
    qa_count: int = 0
    distilled_at: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════════════════════════════


@archive_router.post(
    "/trigger",
    response_model=ArchiveTriggerResponse,
    summary="Manually trigger archive check",
    description="Trigger an immediate archive check for all active conversation nodes. "
    "Normally this runs automatically every 24 hours.",
)
async def trigger_archive() -> Dict[str, Any]:
    """
    Manually trigger an archive check.

    Story 3.8 AC-1: Checks all active nodes for archiving needs.

    Returns:
        ArchiveTriggerResponse with check results.
    """
    try:
        from app.services.archive_scheduler import get_archive_scheduler

        scheduler = get_archive_scheduler()
        result = await scheduler.trigger_manual_check()

        return ArchiveTriggerResponse(**result).model_dump()

    except Exception as e:
        logger.error(f"[Story 3.8] Manual archive trigger failed: {e}")
        return ArchiveTriggerResponse(
            error=str(e),
        ).model_dump()


@archive_router.get(
    "/status/{node_id}",
    response_model=NodeArchiveStatusResponse,
    summary="Get node archive status",
    description="Query the archive status (Hot/Warm/Cold tier) for a specific node.",
)
async def get_archive_status(node_id: str) -> Dict[str, Any]:
    """
    Get the archive status for a node.

    Args:
        node_id: The canvas node identifier.

    Returns:
        NodeArchiveStatusResponse with tier and metadata.
    """
    try:
        from app.services.conversation_archive import get_archive_manager

        manager = get_archive_manager()
        status = manager.get_status(node_id)

        if status:
            return NodeArchiveStatusResponse(
                node_id=status.node_id,
                tier=status.tier.value,
                message_count=status.message_count,
                estimated_tokens=status.estimated_tokens,
                has_summary=status.has_summary,
                has_structured_data=status.has_structured_data,
                last_archived_at=status.last_archived_at,
            ).model_dump()

        # Default: Hot tier (no archiving has occurred)
        return NodeArchiveStatusResponse(
            node_id=node_id,
            tier="hot",
        ).model_dump()

    except Exception as e:
        logger.error(f"[Story 3.8] Archive status query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@archive_router.get(
    "/summary/{node_id}",
    response_model=ArchiveSummaryResponse,
    summary="Get Warm stage conversation summary",
    description="Get the LLM-generated conversation summary for a node "
    "that has been archived to Warm tier.",
)
async def get_archive_summary(node_id: str) -> Dict[str, Any]:
    """
    Get the archive summary for a Warm-tier node.

    Args:
        node_id: The canvas node identifier.

    Returns:
        ArchiveSummaryResponse with summary and extraction counts.
    """
    try:
        from app.config import DEFAULT_GROUP_ID
        from app.services.memory_service import get_memory_service

        memory_svc = await get_memory_service()

        # Search for distillation results for this node
        results = await memory_svc.search_memories(
            query=f"distillation summary node:{node_id}",
            group_id=DEFAULT_GROUP_ID,
            max_results=5,
        )

        summary = ""
        tip_count = 0
        error_count = 0
        qa_count = 0
        distilled_at = None

        if isinstance(results, list):
            for item in results:
                if isinstance(item, dict):
                    metadata = item.get("metadata", {})
                    if (
                        isinstance(metadata, dict)
                        and metadata.get("node_id") == node_id
                    ):
                        summary = item.get("content", item.get("fact", ""))
                        tip_count = metadata.get("tip_count", 0)
                        error_count = metadata.get("error_count", 0)
                        qa_count = metadata.get("qa_count", 0)
                        distilled_at = metadata.get("distilled_at")
                        break

        return ArchiveSummaryResponse(
            node_id=node_id,
            summary=summary,
            tip_count=tip_count,
            error_count=error_count,
            qa_count=qa_count,
            distilled_at=distilled_at,
        ).model_dump()

    except Exception as e:
        logger.error(f"[Story 3.8] Archive summary query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e
