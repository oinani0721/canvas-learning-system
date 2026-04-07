# Sprint 1.2 — Phase 13: Sync payload Pydantic validation
# Story: openspec change fix-fr-kg-04-schema-drift-and-sync-hardening
#
# TDD: tests written FIRST, before implementation.
"""
Tests for the Pydantic ``model_validator`` on ``SyncOperation`` and the
``max_length`` constraint on ``SyncBatchRequest.operations``.

These guards exist so the backend rejects malformed payloads at the boundary
instead of dispatching them to the segment-commit pipeline only to fail with
a less helpful error halfway through. They also prevent unbounded resource
consumption by capping batch size and individual field length.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.models.sync_models import SyncBatchRequest, SyncOperation


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_op(**overrides: object) -> dict:
    base: dict = {
        "operation_id": "00000000-0000-0000-0000-000000000001",
        "entity_type": "node",
        "entity_id": "node_1",
        "operation": "create",
        "payload": {"title": "x", "content": "y"},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Edge endpoint validation
# ---------------------------------------------------------------------------


class TestEdgeEndpointValidation:
    """Edge create/update operations MUST carry source_node_id and target_node_id."""

    def test_edge_missing_source_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError) as excinfo:
            SyncOperation(
                **_make_op(
                    entity_type="edge",
                    entity_id="edge_1",
                    operation="create",
                    payload={"target_node_id": "node_b", "label": "rel"},
                )
            )
        assert "source" in str(excinfo.value).lower()

    def test_edge_missing_target_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError) as excinfo:
            SyncOperation(
                **_make_op(
                    entity_type="edge",
                    entity_id="edge_1",
                    operation="create",
                    payload={"source_node_id": "node_a", "label": "rel"},
                )
            )
        assert "target" in str(excinfo.value).lower()

    def test_edge_with_both_endpoints_passes(self) -> None:
        op = SyncOperation(
            **_make_op(
                entity_type="edge",
                entity_id="edge_1",
                operation="create",
                payload={
                    "source_node_id": "node_a",
                    "target_node_id": "node_b",
                    "label": "rel",
                },
            )
        )
        assert op.payload["source_node_id"] == "node_a"

    def test_edge_with_camelcase_endpoints_passes(self) -> None:
        """Frontend uses camelCase field names — backend MUST accept both."""
        op = SyncOperation(
            **_make_op(
                entity_type="edge",
                entity_id="edge_1",
                operation="create",
                payload={
                    "sourceNodeId": "node_a",
                    "targetNodeId": "node_b",
                    "label": "rel",
                },
            )
        )
        # Validation passes when either snake_case or camelCase is present
        assert (
            op.payload.get("sourceNodeId") == "node_a"
            or op.payload.get("source_node_id") == "node_a"
        )

    def test_edge_delete_does_not_require_endpoints(self) -> None:
        """Delete operations only need entity_id, not the endpoint fields."""
        op = SyncOperation(
            **_make_op(
                entity_type="edge",
                entity_id="edge_1",
                operation="delete",
                payload={},
            )
        )
        assert op.operation == "delete"


# ---------------------------------------------------------------------------
# Payload size limits
# ---------------------------------------------------------------------------


class TestPayloadSizeLimits:
    """Individual field sizes MUST be capped to prevent unbounded consumption."""

    def test_node_content_at_limit_passes(self) -> None:
        """Exactly 20000 chars should pass (boundary)."""
        op = SyncOperation(
            **_make_op(
                entity_type="node",
                payload={"title": "x", "content": "a" * 20000},
            )
        )
        assert len(op.payload["content"]) == 20000

    def test_node_content_oversize_raises(self) -> None:
        with pytest.raises(ValidationError) as excinfo:
            SyncOperation(
                **_make_op(
                    entity_type="node",
                    payload={"title": "x", "content": "a" * 20001},
                )
            )
        assert "20000" in str(excinfo.value) or "content" in str(excinfo.value).lower()

    def test_edge_label_oversize_raises(self) -> None:
        with pytest.raises(ValidationError) as excinfo:
            SyncOperation(
                **_make_op(
                    entity_type="edge",
                    entity_id="edge_1",
                    operation="create",
                    payload={
                        "source_node_id": "node_a",
                        "target_node_id": "node_b",
                        "label": "x" * 2001,
                    },
                )
            )
        assert "2000" in str(excinfo.value) or "label" in str(excinfo.value).lower()


# ---------------------------------------------------------------------------
# Batch size limit
# ---------------------------------------------------------------------------


class TestBatchSizeLimit:
    """A single batch MUST be capped at 500 operations."""

    def test_batch_with_500_ops_passes(self) -> None:
        ops = [
            _make_op(operation_id=f"op-{i:04d}", entity_id=f"n-{i}") for i in range(500)
        ]
        req = SyncBatchRequest(
            canvas_id="c1", operations=[SyncOperation(**op) for op in ops]
        )
        assert len(req.operations) == 500

    def test_batch_with_501_ops_raises(self) -> None:
        ops = [
            SyncOperation(**_make_op(operation_id=f"op-{i:04d}", entity_id=f"n-{i}"))
            for i in range(501)
        ]
        with pytest.raises(ValidationError) as excinfo:
            SyncBatchRequest(canvas_id="c1", operations=ops)
        assert "500" in str(excinfo.value) or "max_length" in str(excinfo.value).lower()

    def test_empty_batch_still_raises(self) -> None:
        """The existing min_length=1 guard MUST be preserved."""
        with pytest.raises(ValidationError):
            SyncBatchRequest(canvas_id="c1", operations=[])
