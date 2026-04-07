# Canvas Learning System - Sync Service
# Story 1.5: Canvas Data Sync to Backend KG (AC-4, AC-7, AC-8)
"""
Neo4j idempotent write service for canvas data synchronization.

Processes batches of sync operations from the frontend Outbox,
using MERGE for create/update and DETACH DELETE for removals.

All writes are idempotent: replaying the same batch produces the same
Neo4j state without duplicating data.

[Source: _bmad-output/implementation-artifacts/1-5-canvas-data-sync-backend-kg.md#Task 6]
[Source: Architecture — Outbox pattern, last-write-wins]
"""

import logging
from datetime import datetime, timezone

import structlog
from neo4j import AsyncDriver, AsyncGraphDatabase
from pydantic import ValidationError

from app.config import get_settings
from app.models.sync_models import (
    SyncBatchRequest,
    SyncBatchResponse,
    SyncDependencyError,
    SyncErrorClass,
    SyncOperation,
    SyncOperationResult,
)

logger = structlog.get_logger(__name__)

# FR-KG-04 Phase 11: Entity types ordered for Segment Commit dependency resolution.
# Board must exist before Node; Node must exist before Edge. Delete runs in reverse.
_SEGMENT_ORDER_UPSERT = ("board", "node", "edge")
_SEGMENT_ORDER_DELETE = ("edge", "node", "board")


class SyncService:
    """Processes canvas sync batches against Neo4j.

    Uses Neo4j MERGE for idempotent create/update and DETACH DELETE
    for removal operations. Each batch is processed in a single
    Neo4j transaction for atomicity (AC-7).

    [Source: Story 1.5 AC-4 — Neo4j MERGE idempotent writes]
    """

    def __init__(self) -> None:
        self._driver: AsyncDriver | None = None

    async def _get_driver(self) -> AsyncDriver:
        """Lazily create and cache the Neo4j async driver."""
        if self._driver is None:
            settings = get_settings()
            self._driver = AsyncGraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
            )
        return self._driver

    async def close(self) -> None:
        """Close the Neo4j driver connection."""
        if self._driver is not None:
            await self._driver.close()
            self._driver = None

    @staticmethod
    def _deduplicate_by_operation_id(
        ops: list[SyncOperation],
    ) -> tuple[list[SyncOperation], list[SyncOperationResult]]:
        """FR-KG-04 Phase 11 Task 11.2: deduplicate operations by operation_id.

        Returns ``(unique_ops, duplicate_results)``. The first occurrence of
        each operation_id is kept; subsequent duplicates get a skipped result
        with ``error="duplicate_operation_id_skipped"`` and are NOT executed.

        This guarantees that retries which accidentally include already-
        processed entries do not cause double writes at the Neo4j level.
        """
        seen: set[str] = set()
        unique: list[SyncOperation] = []
        duplicates: list[SyncOperationResult] = []
        for op in ops:
            if op.operation_id in seen:
                duplicates.append(
                    SyncOperationResult(
                        operation_id=op.operation_id,
                        success=False,
                        error="duplicate_operation_id_skipped",
                        error_class=SyncErrorClass.VALIDATION_ERROR,
                    )
                )
                continue
            seen.add(op.operation_id)
            unique.append(op)
        return unique, duplicates

    @staticmethod
    def _partition_by_entity_type(
        ops: list[SyncOperation],
    ) -> list[list[SyncOperation]]:
        """FR-KG-04 Phase 11 Task 11.3: split ops into ordered Segments.

        Segment order:
            create/update operations: board → node → edge
            delete operations:        edge → node → board

        Edge is a dependency on Node; Node is a dependency on Board.
        Delete must reverse the order so edges are removed before nodes,
        preventing Neo4j's DETACH DELETE from cascading surprises.

        A batch is considered "upsert" if *any* op is create/update; a
        pure-delete batch uses the reverse order. Mixed batches are
        discouraged but still handled — we default to the upsert order.
        """
        all_delete = ops and all(op.operation == "delete" for op in ops)
        order = _SEGMENT_ORDER_DELETE if all_delete else _SEGMENT_ORDER_UPSERT
        segments: list[list[SyncOperation]] = []
        for entity_type in order:
            bucket = [op for op in ops if op.entity_type == entity_type]
            if bucket:
                segments.append(bucket)
        return segments

    @staticmethod
    def _classify_exception(exc: BaseException) -> SyncErrorClass:
        """FR-KG-04 Phase 12 Task 12.3: map an exception to SyncErrorClass.

        The frontend retry strategy depends on this classification, so the
        mapping is strict and explicit — never fall through to a default.
        """
        if isinstance(exc, SyncDependencyError):
            return SyncErrorClass.DEPENDENCY_MISSING
        if isinstance(exc, (ValidationError, ValueError)):
            return SyncErrorClass.VALIDATION_ERROR
        # Everything else (Neo4jError, ConnectionError, RuntimeError, etc.)
        # is treated as transient because per-op retries might succeed.
        return SyncErrorClass.TRANSIENT_ERROR

    @staticmethod
    def _sanitize_error_message(exc: BaseException, error_class: SyncErrorClass) -> str:
        """Return a short, non-leaky error message for the client.

        TRANSIENT_ERROR hides the underlying exception text (which often
        contains driver state), while VALIDATION_ERROR and DEPENDENCY_MISSING
        are safe to surface because they describe the client's own payload.
        """
        if error_class is SyncErrorClass.TRANSIENT_ERROR:
            return "Neo4j transient error"
        return str(exc)[:200]

    async def process_sync_batch(self, request: SyncBatchRequest) -> SyncBatchResponse:
        """Process a batch of sync operations using Segment Commit.

        FR-KG-04 Phase 11 (Task 11.4) rewrites the original single-transaction
        ``for op in request.operations:`` into three independent transactional
        segments ordered by dependency (Board → Node → Edge for upsert, reverse
        for delete). See the openspec change design.md D7 section for the full
        rationale; the short version is:

        - Segments 1 and 2 (Board and Node) are **strictly atomic**: any
          failure rolls the segment back and every subsequent segment is
          returned to the client as ``error_class=DEPENDENCY_MISSING``
          (early return).
        - Segment 3 (Edge) **tolerates partial failures**: each edge runs in
          its own try/except; the transaction commits as long as at least one
          edge succeeded. This preserves the Story 1.5 AC-7 "partial success"
          semantics for the high-frequency edge-drawing path while eliminating
          the "orphan edge after node failure" bug in the original design.

        Additionally:
        - Duplicate operation_ids within the batch are skipped at the top
          with a VALIDATION_ERROR result (Phase 11 Task 11.2).
        - Every per-op failure gets an ``error_class`` field on its result
          so the frontend sync-engine can pick a retry strategy without
          parsing the human-readable error string (Phase 12).

        Args:
            request: The batch sync request with canvas_id and operations.

        Returns:
            SyncBatchResponse with per-operation results.

        Raises:
            Exception: If the Neo4j driver itself fails (bubbles up to the
                endpoint layer for HTTP 503 classification). Per-operation
                errors are captured in the response and do NOT raise.
        """
        driver = await self._get_driver()
        settings = get_settings()
        start_time = datetime.now(timezone.utc)

        # Step 1: deduplicate by operation_id — skipped ops get a result now.
        unique_ops, duplicate_results = self._deduplicate_by_operation_id(
            list(request.operations)
        )
        results: list[SyncOperationResult] = list(duplicate_results)

        # Step 2: partition into dependency-ordered segments.
        segments = self._partition_by_entity_type(unique_ops)

        async with driver.session(database=settings.NEO4J_DATABASE) as session:
            for idx, segment in enumerate(segments):
                is_edge_segment = all(op.entity_type == "edge" for op in segment)

                segment_results: list[SyncOperationResult] = []
                segment_all_ok = True

                async with await session.begin_transaction() as tx:
                    for op in segment:
                        try:
                            await self._execute_operation(
                                tx, op, request.canvas_id, request.subject_id
                            )
                            segment_results.append(
                                SyncOperationResult(
                                    operation_id=op.operation_id, success=True
                                )
                            )
                        except Exception as e:  # noqa: BLE001 — per-op isolation
                            error_class = self._classify_exception(e)
                            sanitized = self._sanitize_error_message(e, error_class)
                            logger.warning(
                                "sync_op_failed",
                                op_id=op.operation_id,
                                entity=f"{op.entity_type}/{op.entity_id}",
                                error_class=error_class.value,
                                error=sanitized,
                            )
                            segment_results.append(
                                SyncOperationResult(
                                    operation_id=op.operation_id,
                                    success=False,
                                    error=sanitized,
                                    error_class=error_class,
                                )
                            )
                            segment_all_ok = False

                    # Segment atomicity rule
                    if is_edge_segment:
                        # Edge segment tolerates partial failures: commit
                        # whenever at least one edge succeeded.
                        if any(r.success for r in segment_results):
                            await tx.commit()
                        else:
                            await tx.rollback()
                    else:
                        # Board / Node segment is strictly atomic.
                        if segment_all_ok:
                            await tx.commit()
                        else:
                            await tx.rollback()

                results.extend(segment_results)

                # If a strict segment (Board/Node) failed, mark every op in
                # the remaining segments as DEPENDENCY_MISSING and early return.
                if not is_edge_segment and not segment_all_ok:
                    for remaining_segment in segments[idx + 1 :]:
                        for op in remaining_segment:
                            results.append(
                                SyncOperationResult(
                                    operation_id=op.operation_id,
                                    success=False,
                                    error="upstream segment failed",
                                    error_class=SyncErrorClass.DEPENDENCY_MISSING,
                                )
                            )
                    break

        synced = sum(1 for r in results if r.success)
        failed = len(results) - synced
        elapsed_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        logger.info(
            "sync_batch_processed",
            canvas_id=request.canvas_id,
            ops=len(request.operations),
            segments=len(segments),
            synced=synced,
            failed=failed,
            elapsed_ms=round(elapsed_ms, 1),
        )

        return SyncBatchResponse(
            results=results, synced_count=synced, failed_count=failed
        )

    async def _execute_operation(
        self,
        tx,
        op: SyncOperation,
        canvas_id: str,
        subject_id: str | None,
    ) -> None:
        """Dispatch a single sync operation to the appropriate Cypher query.

        [Source: Story 1.5 AC-4 — MERGE for create/update, DETACH DELETE for delete]
        [Source: Story 1.5 AC-8 — subjectId and canvasId properties]
        """
        if op.entity_type == "node":
            if op.operation in ("create", "update"):
                await self._upsert_node(tx, op, canvas_id, subject_id)
            elif op.operation == "delete":
                await self._delete_node(tx, op)
        elif op.entity_type == "edge":
            if op.operation in ("create", "update"):
                await self._upsert_edge(tx, op, canvas_id)
            elif op.operation == "delete":
                await self._delete_edge(tx, op)
        elif op.entity_type == "board":
            if op.operation in ("create", "update"):
                await self._upsert_board(tx, op, subject_id)
            elif op.operation == "delete":
                await self._delete_board(tx, op)

    # ═══════════════════════════════════════════════════════════════════════════
    # Node operations
    # ═══════════════════════════════════════════════════════════════════════════

    async def _upsert_node(
        self, tx, op: SyncOperation, canvas_id: str, subject_id: str | None
    ) -> None:
        """Idempotent node create/update via MERGE.

        [Source: Story 1.5 Task 6.3 — Node sync Cypher]
        """
        payload = op.payload
        timestamp = op.timestamp.isoformat()

        await tx.run(
            """
            MERGE (n:CanvasNode {id: $entity_id})
            SET n.title = $title,
                n.content = $content,
                n.x = $x,
                n.y = $y,
                n.width = $width,
                n.height = $height,
                n.canvasId = $canvas_id,
                n.subjectId = $subject_id,
                n.type = $type,
                n.updatedAt = $timestamp
            ON CREATE SET n.createdAt = $timestamp
            """,
            entity_id=op.entity_id,
            title=payload.get("title", ""),
            content=payload.get("content", ""),
            x=payload.get("x", 0),
            y=payload.get("y", 0),
            width=payload.get("width", 200),
            height=payload.get("height", 120),
            canvas_id=canvas_id,
            subject_id=subject_id,
            type=payload.get("type", "text"),
            timestamp=timestamp,
        )

    async def _delete_node(self, tx, op: SyncOperation) -> None:
        """Delete a node and all connected edges (DETACH DELETE).

        [Source: Story 1.5 Task 6.3 — Node delete Cypher]
        [Source: Story 1.5 AC-4 — cascade delete associated edges]
        """
        await tx.run(
            """
            MATCH (n:CanvasNode {id: $entity_id})
            DETACH DELETE n
            """,
            entity_id=op.entity_id,
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # Edge operations
    # ═══════════════════════════════════════════════════════════════════════════

    async def _upsert_edge(self, tx, op: SyncOperation, canvas_id: str) -> None:
        """Idempotent edge create/update via MERGE with fail-fast dependency
        check.

        FR-KG-04 Phase 11 (Tasks 11.7, 11.8) + Phase 3 (original Tasks 3.3,
        3.4, 3.5): the original implementation used MATCH-MATCH-MERGE, which
        silently did nothing when either endpoint was missing (Neo4j returned
        an empty result instead of an error). That produced "orphan edges" in
        the outbox — the op was marked successful but no edge existed.

        The fix has two layers:

        1. Pre-Cypher payload validation: if source_node_id or target_node_id
           is empty in the payload, raise SyncDependencyError immediately
           WITHOUT touching Neo4j. This is the cheapest check.

        2. OPTIONAL MATCH + status return: the Cypher query uses OPTIONAL
           MATCH so that missing endpoints are returned as a status marker
           instead of silently dropping the MERGE. On status="missing" we
           raise SyncDependencyError; on status="ok" the result includes
           the edge id for observability.

        Both failure modes surface as ``error_class=DEPENDENCY_MISSING`` in
        the SyncOperationResult, signalling the frontend to retry with
        priority once upstream nodes sync.

        [Source: Story 1.5 Task 6.4 — Edge sync Cypher]
        """
        payload = op.payload
        timestamp = op.timestamp.isoformat()
        source_node_id = payload.get("source_node_id") or payload.get("sourceNodeId")
        target_node_id = payload.get("target_node_id") or payload.get("targetNodeId")

        # Layer 1: pre-Cypher payload validation (Task 11.8)
        if not source_node_id:
            raise SyncDependencyError(
                f"edge {op.entity_id} missing source_node_id/sourceNodeId in payload"
            )
        if not target_node_id:
            raise SyncDependencyError(
                f"edge {op.entity_id} missing target_node_id/targetNodeId in payload"
            )

        # Layer 2: OPTIONAL MATCH + status return (Task 11.7)
        # The query returns status="missing" when either endpoint doesn't
        # exist in Neo4j; status="ok" when both exist and the MERGE succeeded.
        result = await tx.run(
            """
            OPTIONAL MATCH (source:CanvasNode {id: $source_node_id})
            OPTIONAL MATCH (target:CanvasNode {id: $target_node_id})
            WITH source, target
            CALL (source, target) {
                WITH source, target
                WHERE source IS NULL OR target IS NULL
                RETURN 'missing' AS status, null AS edge_id
                UNION
                WITH source, target
                WHERE source IS NOT NULL AND target IS NOT NULL
                MERGE (source)-[e:CANVAS_EDGE {id: $entity_id}]->(target)
                SET e.label = $label,
                    e.canvasId = $canvas_id,
                    e.updatedAt = $timestamp
                ON CREATE SET e.createdAt = $timestamp
                RETURN 'ok' AS status, e.id AS edge_id
            }
            RETURN status, edge_id
            """,
            entity_id=op.entity_id,
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            label=payload.get("label", ""),
            canvas_id=canvas_id,
            timestamp=timestamp,
        )
        record = await result.single()
        if record is None or record.get("status") == "missing":
            raise SyncDependencyError(
                f"edge {op.entity_id} upsert no-op: missing endpoint "
                f"source={source_node_id} target={target_node_id}"
            )

    async def _delete_edge(self, tx, op: SyncOperation) -> None:
        """Delete a single edge relationship.

        [Source: Story 1.5 Task 6.4 — Edge delete Cypher]
        """
        await tx.run(
            """
            MATCH ()-[e:CANVAS_EDGE {id: $entity_id}]->()
            DELETE e
            """,
            entity_id=op.entity_id,
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # Board operations
    # ═══════════════════════════════════════════════════════════════════════════

    async def _upsert_board(
        self, tx, op: SyncOperation, subject_id: str | None
    ) -> None:
        """Idempotent board create/update via MERGE.

        [Source: Story 1.5 Task 6.5 — Board sync Cypher]
        """
        payload = op.payload
        timestamp = op.timestamp.isoformat()

        await tx.run(
            """
            MERGE (b:CanvasBoard {id: $entity_id})
            SET b.name = $name,
                b.subjectId = $subject_id,
                b.updatedAt = $timestamp
            ON CREATE SET b.createdAt = $timestamp
            """,
            entity_id=op.entity_id,
            name=payload.get("name", ""),
            subject_id=subject_id,
            timestamp=timestamp,
        )

    async def _delete_board(self, tx, op: SyncOperation) -> None:
        """Delete a board and all its nodes (cascade).

        [Source: Story 1.5 Task 6.5 — Board delete Cypher]
        """
        await tx.run(
            """
            MATCH (b:CanvasBoard {id: $entity_id})
            OPTIONAL MATCH (n:CanvasNode {canvasId: $entity_id})
            DETACH DELETE b, n
            """,
            entity_id=op.entity_id,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Singleton
# ═══════════════════════════════════════════════════════════════════════════════

_sync_service: SyncService | None = None


def get_sync_service() -> SyncService:
    """Get or create the singleton SyncService instance."""
    global _sync_service
    if _sync_service is None:
        _sync_service = SyncService()
    return _sync_service


async def cleanup_sync_service() -> None:
    """Cleanup the SyncService singleton (shutdown hook)."""
    global _sync_service
    if _sync_service is not None:
        await _sync_service.close()
        _sync_service = None
