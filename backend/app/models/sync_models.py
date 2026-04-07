# Canvas Learning System - Sync Models
# Story 1.5: Canvas Data Sync to Backend KG (AC-7)
# FR-KG-04 Phase 13: payload validation guards
"""
Pydantic models for the canvas-to-Neo4j sync API.

Defines the request/response schemas for batch sync operations
that replicate IndexedDB canvas data into Neo4j.

FR-KG-04 Phase 13 (openspec change fix-fr-kg-04-schema-drift-and-sync-hardening)
adds boundary validation that rejects malformed payloads at ingress instead of
letting them flow through the segment-commit pipeline. This prevents resource
exhaustion (oversized fields, oversized batches) and gives the frontend a clear,
actionable error.

[Source: _bmad-output/implementation-artifacts/1-5-canvas-data-sync-backend-kg.md#Task 5]
"""

from datetime import datetime
from enum import Enum
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, model_validator


# FR-KG-04 Phase 11: exception class for missing upstream entities
# Raised by SyncService._upsert_edge when source/target CanvasNode is absent.
class SyncDependencyError(Exception):
    """Raised when a sync operation depends on an entity that is missing
    or failed upstream in the Segment Commit pipeline."""


# FR-KG-04 Phase 12: per-operation error classification enum.
# The frontend sync-engine.ts uses this to decide retry strategy:
#   VALIDATION_ERROR   → permanently failed, never retry
#   DEPENDENCY_MISSING → retry with priority 1 after upstream succeeds
#   TRANSIENT_ERROR    → exponential backoff retry
class SyncErrorClass(str, Enum):
    """Three-value classification of per-operation sync failures.

    Values are str-backed so JSON serialization is straightforward and
    the frontend can switch on them as string literals.
    """

    VALIDATION_ERROR = "VALIDATION_ERROR"
    DEPENDENCY_MISSING = "DEPENDENCY_MISSING"
    TRANSIENT_ERROR = "TRANSIENT_ERROR"


# FR-KG-04 Phase 13 size budgets — chosen to match real-world canvas use cases
# and bounded so a malicious or buggy client cannot exhaust Neo4j memory.
MAX_NODE_CONTENT_CHARS = 20000  # Task 13.3
MAX_EDGE_LABEL_CHARS = 2000  # Task 13.4
MAX_OPERATIONS_PER_BATCH = 500  # Task 13.5


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

    @model_validator(mode="after")
    def _validate_payload(self) -> "SyncOperation":
        """FR-KG-04 Phase 13 boundary validation.

        Rules:
        - edge create/update MUST carry source_node_id/target_node_id
          (snake_case OR camelCase, since the frontend uses camelCase)
        - node payload content length MUST be <= MAX_NODE_CONTENT_CHARS
        - edge payload label length MUST be <= MAX_EDGE_LABEL_CHARS
        - delete operations are exempt from endpoint requirements
        """
        payload = self.payload or {}

        # Edge endpoint validation (Tasks 13.1, 13.2, 13.9)
        if self.entity_type == "edge" and self.operation in ("create", "update"):
            source = payload.get("source_node_id") or payload.get("sourceNodeId")
            target = payload.get("target_node_id") or payload.get("targetNodeId")
            if not source:
                raise ValueError(
                    "edge create/update payload missing source_node_id "
                    "(also accepts camelCase sourceNodeId)"
                )
            if not target:
                raise ValueError(
                    "edge create/update payload missing target_node_id "
                    "(also accepts camelCase targetNodeId)"
                )

        # Node content length cap (Task 13.3)
        if self.entity_type == "node":
            content = payload.get("content") or ""
            if isinstance(content, str) and len(content) > MAX_NODE_CONTENT_CHARS:
                raise ValueError(
                    f"node content exceeds {MAX_NODE_CONTENT_CHARS} character limit "
                    f"(got {len(content)})"
                )

        # Edge label length cap (Task 13.4)
        if self.entity_type == "edge":
            label = payload.get("label") or ""
            if isinstance(label, str) and len(label) > MAX_EDGE_LABEL_CHARS:
                raise ValueError(
                    f"edge label exceeds {MAX_EDGE_LABEL_CHARS} character limit "
                    f"(got {len(label)})"
                )

        return self


class SyncBatchRequest(BaseModel):
    """Batch of sync operations from a single canvas.

    [Source: Story 1.5 AC-7 — POST /api/v1/sync/batch]
    """

    canvas_id: str = Field(..., description="Canvas board UUID")
    subject_id: str | None = Field(
        default=None, description="Subject UUID for multi-subject isolation (Story 1.9)"
    )
    operations: list[SyncOperation] = Field(
        ...,
        min_length=1,
        max_length=MAX_OPERATIONS_PER_BATCH,
        description=(
            f"Sync operations list (1..{MAX_OPERATIONS_PER_BATCH}). "
            "FR-KG-04 Phase 13 Task 13.5: cap at 500 to prevent unbounded "
            "consumption."
        ),
    )


class SyncOperationResult(BaseModel):
    """Result of a single sync operation.

    FR-KG-04 Phase 12 (Task 12.2): ``error_class`` is attached whenever
    ``success=False`` so the frontend sync-engine can pick a retry strategy
    without inspecting the human-readable ``error`` string. When
    ``success=True`` the field is omitted/null.

    [Source: Story 1.5 AC-7 — partial success support]
    """

    operation_id: str = Field(..., description="Matches the request operation_id")
    success: bool = Field(..., description="Whether the operation succeeded")
    error: str | None = Field(default=None, description="Error message if failed")
    error_class: Optional[SyncErrorClass] = Field(
        default=None,
        description=(
            "FR-KG-04 Phase 12: classification of the failure. "
            "VALIDATION_ERROR → permanently failed; "
            "DEPENDENCY_MISSING → retry with priority; "
            "TRANSIENT_ERROR → exponential backoff. "
            "Null/absent when success=True."
        ),
    )


class SyncBatchResponse(BaseModel):
    """Response for a batch sync request.

    [Source: Story 1.5 AC-7 — SyncBatchResponse]
    """

    results: list[SyncOperationResult] = Field(..., description="Per-operation results")
    synced_count: int = Field(..., description="Number of successful operations")
    failed_count: int = Field(..., description="Number of failed operations")
