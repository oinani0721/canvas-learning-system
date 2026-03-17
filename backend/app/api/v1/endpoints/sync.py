# Canvas Learning System - Sync API Endpoint
# Story 1.5: Canvas Data Sync to Backend KG (AC-7)
"""
REST endpoint for batch-syncing canvas data from IndexedDB to Neo4j.

POST /api/v1/sync/batch — Receives a batch of create/update/delete
operations and applies them idempotently to Neo4j.

[Source: _bmad-output/implementation-artifacts/1-5-canvas-data-sync-backend-kg.md#Task 5]
"""

import logging

from fastapi import APIRouter, HTTPException

from app.models.sync_models import SyncBatchRequest, SyncBatchResponse

logger = logging.getLogger(__name__)

sync_router = APIRouter()


@sync_router.post(
    "/batch",
    response_model=SyncBatchResponse,
    summary="Batch sync canvas data to Neo4j",
    description=(
        "Receives a batch of canvas sync operations (create/update/delete) "
        "from the frontend Outbox and applies them idempotently to Neo4j. "
        "Individual operation failures are reported without aborting the batch. "
        "(Story 1.5 AC-7)"
    ),
    responses={
        503: {"description": "Neo4j connection unavailable"},
    },
)
async def sync_batch(request: SyncBatchRequest) -> SyncBatchResponse:
    """Process a batch of canvas sync operations.

    [Source: Story 1.5 AC-7 — POST /api/v1/sync/batch]
    [Source: Story 1.5 AC-4 — idempotent Neo4j writes]

    Args:
        request: Batch of sync operations for a single canvas.

    Returns:
        SyncBatchResponse with per-operation results.

    Raises:
        HTTPException 503: If Neo4j is unreachable.
    """
    from app.services.sync_service import get_sync_service

    try:
        service = get_sync_service()
        return await service.process_sync_batch(request)
    except Exception as e:
        # Neo4j connection failure -> 503 Service Unavailable
        logger.error(
            "[Story 1.5] Sync batch failed — Neo4j unreachable: %s",
            str(e)[:200],
        )
        raise HTTPException(
            status_code=503,
            detail=f"Neo4j connection failed: {str(e)[:200]}",
        ) from e
