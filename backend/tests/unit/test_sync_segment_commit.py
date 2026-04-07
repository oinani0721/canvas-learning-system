"""FR-KG-04 Phase 3 + 11: Segment Commit architecture for SyncService.

Story: openspec change fix-fr-kg-04-schema-drift-and-sync-hardening.

Covers:
- Deduplication of operation_id within a batch (Task 11.2)
- Partition into Board → Node → Edge segments for upsert (Task 11.3)
- Reverse segment order for delete batches (Task 11.3)
- Board/Node segment strict atomicity: any failure rolls back + early return
  marks remaining ops as DEPENDENCY_MISSING (Task 11.5, 11.10)
- Edge segment tolerates partial failures: commit as long as any op succeeded
  (Task 11.6, 11.11)
- Out-of-order batch [edge, node] is still executed Node first, Edge second,
  so edge succeeds (Task 11.9)
- _upsert_edge raises SyncDependencyError on missing endpoint payload
  (Task 11.8 + original Phase 3 Tasks 3.3, 3.7)
- _upsert_edge raises SyncDependencyError on OPTIONAL MATCH status='missing'
  (Task 11.7 + original Phase 3 Task 3.5)
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from neo4j.exceptions import ConstraintError

from app.models.sync_models import (
    SyncBatchRequest,
    SyncDependencyError,
    SyncErrorClass,
    SyncOperation,
)
from app.services.sync_service import SyncService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_op(
    *,
    entity_type: str,
    entity_id: str,
    operation: str = "create",
    operation_id: str | None = None,
    payload: dict[str, Any] | None = None,
) -> SyncOperation:
    """Build a SyncOperation with sensible defaults."""
    default_payload: dict[str, Any] = {}
    if entity_type == "node":
        default_payload = {"title": "t", "content": "c"}
    elif entity_type == "edge":
        default_payload = {
            "source_node_id": "node_a",
            "target_node_id": "node_b",
            "label": "rel",
        }
    elif entity_type == "board":
        default_payload = {"name": "board"}

    return SyncOperation(
        operation_id=operation_id or f"op-{entity_type}-{entity_id}",
        entity_type=entity_type,  # type: ignore[arg-type]
        entity_id=entity_id,
        operation=operation,  # type: ignore[arg-type]
        payload=payload or default_payload,
        timestamp=datetime.now(timezone.utc),
    )


class _StubTransaction:
    """Stand-in for an async Neo4j transaction in unit tests.

    Tracks committed/rolled-back state and lets the test install a custom
    tx.run handler so individual ops can raise or return stub records.
    """

    def __init__(self) -> None:
        self.committed = False
        self.rolled_back = False
        self.run_calls: list[dict[str, Any]] = []
        self._run_handler: Any = None

    def set_run_handler(self, handler: Any) -> None:
        self._run_handler = handler

    async def run(self, query: str, **kwargs: Any):
        self.run_calls.append({"query": query, "kwargs": kwargs})
        if self._run_handler is not None:
            return await self._run_handler(query, **kwargs)
        # Default success: returns a stub ok status
        result = MagicMock()
        result.single = AsyncMock(return_value={"status": "ok", "edge_id": "e"})
        return result

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        self.rolled_back = True


class _StubSessionContext:
    """Async context manager that returns a stub Neo4j session."""

    def __init__(self, session: "_StubSession") -> None:
        self._session = session

    async def __aenter__(self) -> "_StubSession":
        return self._session

    async def __aexit__(self, *args: Any) -> None:
        return None


class _StubTransactionContext:
    def __init__(self, tx: _StubTransaction) -> None:
        self._tx = tx

    async def __aenter__(self) -> _StubTransaction:
        return self._tx

    async def __aexit__(self, *args: Any) -> None:
        return None


class _StubSession:
    def __init__(self) -> None:
        self.transactions: list[_StubTransaction] = []
        self._tx_factory: Any = None

    def set_tx_factory(self, factory: Any) -> None:
        self._tx_factory = factory

    async def begin_transaction(self) -> _StubTransactionContext:
        tx = self._tx_factory() if self._tx_factory else _StubTransaction()
        self.transactions.append(tx)
        return _StubTransactionContext(tx)


class _StubDriver:
    def __init__(self, session: _StubSession) -> None:
        self._session = session

    def session(self, database: str | None = None) -> _StubSessionContext:
        return _StubSessionContext(self._session)


@pytest.fixture
def stub_driver_and_session() -> tuple[_StubDriver, _StubSession]:
    session = _StubSession()
    driver = _StubDriver(session)
    return driver, session


@pytest.fixture
def sync_service(stub_driver_and_session) -> SyncService:
    driver, _ = stub_driver_and_session
    svc = SyncService()
    svc._driver = driver  # type: ignore[assignment]
    return svc


# ---------------------------------------------------------------------------
# Deduplication (Task 11.2, 11.12)
# ---------------------------------------------------------------------------


class TestDeduplication:
    """Operations with duplicate operation_id are skipped as VALIDATION_ERROR."""

    def test_duplicate_op_id_marked_skipped(self) -> None:
        op1 = _make_op(entity_type="node", entity_id="n1", operation_id="dup")
        op2 = _make_op(entity_type="node", entity_id="n2", operation_id="dup")
        unique, duplicates = SyncService._deduplicate_by_operation_id([op1, op2])
        assert len(unique) == 1
        assert unique[0].entity_id == "n1"
        assert len(duplicates) == 1
        assert duplicates[0].success is False
        assert duplicates[0].error_class == SyncErrorClass.VALIDATION_ERROR
        assert "duplicate_operation_id_skipped" in (duplicates[0].error or "")

    def test_all_unique_keeps_all(self) -> None:
        ops = [
            _make_op(entity_type="node", entity_id=f"n{i}", operation_id=f"op-{i}")
            for i in range(3)
        ]
        unique, duplicates = SyncService._deduplicate_by_operation_id(ops)
        assert len(unique) == 3
        assert len(duplicates) == 0


# ---------------------------------------------------------------------------
# Partition (Task 11.3, 11.13)
# ---------------------------------------------------------------------------


class TestPartitionByEntityType:
    """Upsert uses Board→Node→Edge; delete uses Edge→Node→Board."""

    def test_upsert_order_is_board_node_edge(self) -> None:
        ops = [
            _make_op(entity_type="edge", entity_id="e1"),
            _make_op(entity_type="node", entity_id="n1"),
            _make_op(entity_type="board", entity_id="b1"),
        ]
        segments = SyncService._partition_by_entity_type(ops)
        assert len(segments) == 3
        assert segments[0][0].entity_type == "board"
        assert segments[1][0].entity_type == "node"
        assert segments[2][0].entity_type == "edge"

    def test_delete_order_is_edge_node_board(self) -> None:
        ops = [
            _make_op(entity_type="board", entity_id="b1", operation="delete"),
            _make_op(entity_type="node", entity_id="n1", operation="delete"),
            _make_op(entity_type="edge", entity_id="e1", operation="delete"),
        ]
        segments = SyncService._partition_by_entity_type(ops)
        assert len(segments) == 3
        assert segments[0][0].entity_type == "edge"
        assert segments[1][0].entity_type == "node"
        assert segments[2][0].entity_type == "board"

    def test_out_of_order_edge_first_still_partitioned_correctly(self) -> None:
        """Task 11.9: [edge, node] input must yield Node segment before Edge."""
        ops = [
            _make_op(entity_type="edge", entity_id="e1"),
            _make_op(entity_type="node", entity_id="n1"),
        ]
        segments = SyncService._partition_by_entity_type(ops)
        assert segments[0][0].entity_type == "node"
        assert segments[1][0].entity_type == "edge"


# ---------------------------------------------------------------------------
# _upsert_edge fail-fast (Tasks 11.7, 11.8 + Phase 3 Tasks 3.3, 3.5)
# ---------------------------------------------------------------------------


class TestUpsertEdgeFailFast:
    """_upsert_edge raises SyncDependencyError on missing endpoints."""

    @pytest.mark.asyncio
    async def test_missing_source_in_payload_raises_before_cypher(
        self, sync_service: SyncService
    ) -> None:
        op = _make_op(entity_type="edge", entity_id="e1")
        # Force payload to drop source_node_id after construction — bypasses
        # the model_validator so we can test the SyncService-level guard
        # directly.
        op.payload = {"target_node_id": "nb", "label": "r"}

        tx = _StubTransaction()
        with pytest.raises(SyncDependencyError) as excinfo:
            await sync_service._upsert_edge(tx, op, canvas_id="c1")

        assert (
            "source_node_id" in str(excinfo.value).lower()
            or "source" in str(excinfo.value).lower()
        )
        # Critical: Neo4j was never touched
        assert len(tx.run_calls) == 0

    @pytest.mark.asyncio
    async def test_missing_target_in_payload_raises_before_cypher(
        self, sync_service: SyncService
    ) -> None:
        op = _make_op(entity_type="edge", entity_id="e1")
        op.payload = {"source_node_id": "na", "label": "r"}

        tx = _StubTransaction()
        with pytest.raises(SyncDependencyError):
            await sync_service._upsert_edge(tx, op, canvas_id="c1")
        assert len(tx.run_calls) == 0

    @pytest.mark.asyncio
    async def test_optional_match_missing_status_raises(
        self, sync_service: SyncService
    ) -> None:
        """When Cypher returns status='missing' (endpoint not in Neo4j)."""
        op = _make_op(entity_type="edge", entity_id="e1")

        tx = _StubTransaction()

        async def missing_handler(query: str, **kwargs: Any):
            result = MagicMock()
            result.single = AsyncMock(
                return_value={"status": "missing", "edge_id": None}
            )
            return result

        tx.set_run_handler(missing_handler)

        with pytest.raises(SyncDependencyError) as excinfo:
            await sync_service._upsert_edge(tx, op, canvas_id="c1")
        assert "missing" in str(excinfo.value).lower()

    @pytest.mark.asyncio
    async def test_optional_match_ok_status_succeeds(
        self, sync_service: SyncService
    ) -> None:
        """Happy path: status='ok' returns without raising."""
        op = _make_op(entity_type="edge", entity_id="e1")
        tx = _StubTransaction()

        async def ok_handler(query: str, **kwargs: Any):
            result = MagicMock()
            result.single = AsyncMock(return_value={"status": "ok", "edge_id": "e1"})
            return result

        tx.set_run_handler(ok_handler)

        # Should not raise
        await sync_service._upsert_edge(tx, op, canvas_id="c1")
        assert len(tx.run_calls) == 1


# ---------------------------------------------------------------------------
# Segment Commit atomicity (Tasks 11.5, 11.6, 11.10, 11.11)
# ---------------------------------------------------------------------------


class TestSegmentCommitAtomicity:
    """Board/Node segments are atomic; Edge segment tolerates partial failure."""

    @pytest.mark.asyncio
    async def test_node_segment_failure_aborts_edge_segment(
        self, sync_service: SyncService, stub_driver_and_session
    ) -> None:
        """Task 11.5 + 11.10: Node segment failure → Edge segment DEPENDENCY_MISSING."""
        _, session = stub_driver_and_session

        def tx_factory() -> _StubTransaction:
            tx = _StubTransaction()

            async def handler(query: str, **kwargs: Any):
                if "MERGE (n:CanvasNode" in query:
                    raise ValueError("simulated node failure")
                result = MagicMock()
                result.single = AsyncMock(return_value={"status": "ok", "edge_id": "e"})
                return result

            tx.set_run_handler(handler)
            return tx

        session.set_tx_factory(tx_factory)

        request = SyncBatchRequest(
            canvas_id="c1",
            operations=[
                _make_op(entity_type="node", entity_id="n1"),
                _make_op(entity_type="edge", entity_id="e1"),
            ],
        )
        response = await sync_service.process_sync_batch(request)

        node_result = next(
            r for r in response.results if r.operation_id == "op-node-n1"
        )
        assert node_result.success is False
        assert node_result.error_class == SyncErrorClass.VALIDATION_ERROR

        edge_result = next(
            r for r in response.results if r.operation_id == "op-edge-e1"
        )
        assert edge_result.success is False
        assert edge_result.error_class == SyncErrorClass.DEPENDENCY_MISSING

        # Node segment rolled back, Edge segment never opened
        assert session.transactions[0].rolled_back is True
        assert len(session.transactions) == 1
        assert response.synced_count == 0
        assert response.failed_count == 2

    @pytest.mark.asyncio
    async def test_edge_segment_partial_failure_still_commits(
        self, sync_service: SyncService, stub_driver_and_session
    ) -> None:
        """Task 11.6 + 11.11: Edge segment tolerates partial failure and commits."""
        _, session = stub_driver_and_session

        def tx_factory() -> _StubTransaction:
            tx = _StubTransaction()
            edge_count = {"n": 0}

            async def handler(query: str, **kwargs: Any):
                if "MERGE (n:CanvasNode" in query:
                    result = MagicMock()
                    result.single = AsyncMock(
                        return_value={"status": "ok", "edge_id": None}
                    )
                    return result
                edge_count["n"] += 1
                if edge_count["n"] == 3:
                    # Third edge: simulate OPTIONAL MATCH missing status
                    result = MagicMock()
                    result.single = AsyncMock(
                        return_value={"status": "missing", "edge_id": None}
                    )
                    return result
                result = MagicMock()
                result.single = AsyncMock(return_value={"status": "ok", "edge_id": "e"})
                return result

            tx.set_run_handler(handler)
            return tx

        session.set_tx_factory(tx_factory)

        request = SyncBatchRequest(
            canvas_id="c1",
            operations=[
                _make_op(entity_type="node", entity_id="n1"),
                _make_op(entity_type="node", entity_id="n2"),
                _make_op(entity_type="edge", entity_id="e1"),
                _make_op(entity_type="edge", entity_id="e2"),
                _make_op(entity_type="edge", entity_id="e3"),
            ],
        )
        response = await sync_service.process_sync_batch(request)

        assert response.synced_count == 4
        assert response.failed_count == 1

        # Both transactions committed (Node + Edge)
        assert session.transactions[0].committed is True
        assert session.transactions[1].committed is True

        failed = [r for r in response.results if not r.success]
        assert len(failed) == 1
        assert failed[0].error_class == SyncErrorClass.DEPENDENCY_MISSING

    @pytest.mark.asyncio
    async def test_out_of_order_batch_executes_node_before_edge(
        self, sync_service: SyncService, stub_driver_and_session
    ) -> None:
        """Task 11.9: [edge, node] input → Node runs first, Edge runs second."""
        _, session = stub_driver_and_session

        query_order: list[str] = []

        def tx_factory() -> _StubTransaction:
            tx = _StubTransaction()

            async def handler(query: str, **kwargs: Any):
                if "MERGE (n:CanvasNode" in query:
                    query_order.append("node")
                elif "CANVAS_EDGE" in query:
                    query_order.append("edge")
                result = MagicMock()
                result.single = AsyncMock(return_value={"status": "ok", "edge_id": "e"})
                return result

            tx.set_run_handler(handler)
            return tx

        session.set_tx_factory(tx_factory)

        request = SyncBatchRequest(
            canvas_id="c1",
            operations=[
                _make_op(entity_type="edge", entity_id="e1"),
                _make_op(entity_type="node", entity_id="n1"),
            ],
        )
        response = await sync_service.process_sync_batch(request)

        assert "node" in query_order
        assert "edge" in query_order
        assert query_order.index("node") < query_order.index("edge")
        assert response.synced_count == 2


# ---------------------------------------------------------------------------
# Full flow with duplicates (Task 11.12 integration)
# ---------------------------------------------------------------------------


class TestConstraintErrorClassification:
    """FR-KG-04 Phase 8: Neo4j ConstraintError → VALIDATION_ERROR (permanent)."""

    @pytest.mark.asyncio
    async def test_constraint_error_maps_to_validation_error(
        self, sync_service: SyncService, stub_driver_and_session
    ) -> None:
        """A (subjectId, name) composite constraint violation on a board
        upsert must be classified as VALIDATION_ERROR so the frontend marks
        the outbox entry permanently failed (retry cannot succeed)."""
        _, session = stub_driver_and_session

        def tx_factory() -> _StubTransaction:
            tx = _StubTransaction()

            async def handler(query: str, **kwargs: Any):
                if "MERGE (b:CanvasBoard" in query:
                    raise ConstraintError(
                        "Node already exists with label `CanvasBoard` "
                        "and property `(subjectId, name)`"
                    )
                result = MagicMock()
                result.single = AsyncMock(return_value={"status": "ok", "edge_id": "e"})
                return result

            tx.set_run_handler(handler)
            return tx

        session.set_tx_factory(tx_factory)

        request = SyncBatchRequest(
            canvas_id="c1",
            operations=[
                _make_op(entity_type="board", entity_id="b1"),
            ],
        )
        response = await sync_service.process_sync_batch(request)

        assert response.synced_count == 0
        assert response.failed_count == 1
        board_result = response.results[0]
        assert board_result.success is False
        assert board_result.error_class == SyncErrorClass.VALIDATION_ERROR


class TestFullFlowWithDuplicates:
    """Duplicate operation_ids are skipped in the top-level dedup step."""

    @pytest.mark.asyncio
    async def test_duplicate_op_id_in_batch_skipped_not_executed(
        self, sync_service: SyncService, stub_driver_and_session
    ) -> None:
        _, _session = stub_driver_and_session

        request = SyncBatchRequest(
            canvas_id="c1",
            operations=[
                _make_op(entity_type="node", entity_id="n1", operation_id="dup-op"),
                _make_op(entity_type="node", entity_id="n2", operation_id="dup-op"),
            ],
        )
        response = await sync_service.process_sync_batch(request)

        assert len(response.results) == 2
        assert response.synced_count == 1
        assert response.failed_count == 1
        dup_result = response.results[0]
        assert dup_result.success is False
        assert dup_result.error_class == SyncErrorClass.VALIDATION_ERROR
        assert "duplicate_operation_id_skipped" in (dup_result.error or "")
