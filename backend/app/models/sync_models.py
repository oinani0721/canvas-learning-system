# Canvas Learning System - Sync Models
# Story 1.5: Canvas Data Sync to Backend KG (AC-7)
"""
Pydantic models for the canvas-to-Neo4j sync API.

Defines the request/response schemas for batch sync operations
that replicate IndexedDB canvas data into Neo4j.

[Source: _bmad-output/implementation-artifacts/1-5-canvas-data-sync-backend-kg.md#Task 5]
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class SyncOperation(BaseModel):
    """A single sync operation from the frontend Outbox.

    Each operation carries an idempotent UUID (entity_id) so that
    duplicate submissions produce the same result.

    [Source: Story 1.5 AC-4 — idempotent UUID]
    """

    operation_id: str = Field(..., description="Idempotent UUID for this operation")
    entity_type: Literal["node", "edge", "board"] = Field(
        ..., description="Type of entity being synced"
    )
    entity_id: str = Field(
        ..., description="Entity UUID (matches IndexedDB primary key)"
    )
    operation: Literal["create", "update", "delete"] = Field(
        ..., description="CRUD operation type"
    )
    payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Entity properties (create/update) or minimal id (delete)",
    )
    timestamp: datetime = Field(..., description="Frontend operation timestamp")


class SyncBatchRequest(BaseModel):
    """Batch of sync operations from a single canvas.

    [Source: Story 1.5 AC-7 — POST /api/v1/sync/batch]
    """

    canvas_id: str = Field(..., description="Canvas board UUID")
    subject_id: str | None = Field(
        default=None, description="Subject UUID for multi-subject isolation (Story 1.9)"
    )
    operations: list[SyncOperation] = Field(
        ..., min_length=1, description="Non-empty list of sync operations"
    )


class SyncOperationResult(BaseModel):
    """Result of a single sync operation.

    [Source: Story 1.5 AC-7 — partial success support]
    """

    operation_id: str = Field(..., description="Matches the request operation_id")
    success: bool = Field(..., description="Whether the operation succeeded")
    error: str | None = Field(default=None, description="Error message if failed")


class SyncBatchResponse(BaseModel):
    """Response for a batch sync request.

    [Source: Story 1.5 AC-7 — SyncBatchResponse]
    """

    results: list[SyncOperationResult] = Field(..., description="Per-operation results")
    synced_count: int = Field(..., description="Number of successful operations")
    failed_count: int = Field(..., description="Number of failed operations")
