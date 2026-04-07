# Canvas Learning System - Sync API Endpoint
# Story 1.5: Canvas Data Sync to Backend KG (AC-7)
"""
REST endpoint for batch-syncing canvas data from IndexedDB to Neo4j.

POST /api/v1/sync/batch — Receives a batch of create/update/delete
operations and applies them idempotently to Neo4j.

[Source: _bmad-output/implementation-artifacts/1-5-canvas-data-sync-backend-kg.md#Task 5]
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from neo4j.exceptions import AuthError, Neo4jError, ServiceUnavailable

from app.models.sync_models import SyncBatchRequest, SyncBatchResponse
from app.security import require_internal_api_key

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
        "Requires the X-CLS-Internal-Key header (FR-KG-04 Phase 2). "
        "(Story 1.5 AC-7)"
    ),
    dependencies=[Depends(require_internal_api_key)],
    responses={
        403: {"description": "Invalid or missing internal API key"},
        500: {"description": "Unexpected logic error in sync pipeline"},
        503: {
            "description": (
                "Neo4j connection unavailable, OR internal API key not "
                "configured in production mode (fail-closed)"
            )
        },
    },
)
async def sync_batch(request: SyncBatchRequest) -> SyncBatchResponse:
    """Process a batch of canvas sync operations.

    FR-KG-04 Phase 4 Task 4.1: exception classification.

    The previous implementation caught every exception and returned 503
    "Neo4j unreachable". This hid logic bugs (ValueError, TypeError,
    KeyError from malformed payloads) behind a "service degraded" veneer.
    The new classification:

    - ``ServiceUnavailable`` / ``AuthError`` / ``ConnectionError`` → 503
      (genuine infrastructure issue — retrying might help)
    - ``Neo4jError`` (non-service) / anything else → 500
      (logic bug; retrying will not help, client should give up)

    Neither response body contains the raw exception text because that
    may leak driver state or internal paths. Only fixed strings like
    "Neo4j unavailable" / "Sync batch failed unexpectedly" are returned.

    [Source: Story 1.5 AC-7 — POST /api/v1/sync/batch]
    [Source: Story 1.5 AC-4 — idempotent Neo4j writes]
    """
    from app.services.sync_service import get_sync_service

    try:
        service = get_sync_service()
        return await service.process_sync_batch(request)
    except (ServiceUnavailable, AuthError, ConnectionError) as e:
        # Infrastructure-level failures → 503
        logger.error(
            "sync_batch_neo4j_unavailable: type=%s detail=%s",
            type(e).__name__,
            str(e)[:200],
        )
        raise HTTPException(
            status_code=503,
            detail="Neo4j unavailable",
        ) from e
    except Exception as e:
        # Everything else (logic bugs, unexpected Neo4jError) → 500
        # Use logger.exception to capture the full traceback for debugging,
        # but return a generic message so no internal state leaks.
        logger.exception(
            "sync_batch_unexpected_error: type=%s",
            type(e).__name__,
        )
        raise HTTPException(
            status_code=500,
            detail="Sync batch failed unexpectedly",
        ) from e
