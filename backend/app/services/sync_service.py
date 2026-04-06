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

from app.config import get_settings
from app.models.sync_models import (
    SyncBatchRequest,
    SyncBatchResponse,
    SyncOperation,
    SyncOperationResult,
)

logger = structlog.get_logger(__name__)


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

    async def process_sync_batch(self, request: SyncBatchRequest) -> SyncBatchResponse:
        """Process a batch of sync operations in a single Neo4j transaction.

        All operations are executed within one transaction for atomicity.
        Individual operation failures are caught and reported without
        aborting the entire batch (AC-7: partial success).

        [Source: Story 1.5 AC-7 — single Neo4j transaction, partial success]

        Args:
            request: The batch sync request with canvas_id and operations.

        Returns:
            SyncBatchResponse with per-operation results.

        Raises:
            Exception: If the Neo4j connection itself fails (503 at API level).
        """
        driver = await self._get_driver()
        settings = get_settings()
        results: list[SyncOperationResult] = []
        synced = 0
        failed = 0
        start_time = datetime.now(timezone.utc)

        async with driver.session(database=settings.NEO4J_DATABASE) as session:
            async with await session.begin_transaction() as tx:
                for op in request.operations:
                    try:
                        await self._execute_operation(
                            tx, op, request.canvas_id, request.subject_id
                        )
                        results.append(
                            SyncOperationResult(
                                operation_id=op.operation_id, success=True
                            )
                        )
                        synced += 1
                    except (RuntimeError, ConnectionError) as e:
                        logger.warning(
                            "[Story 1.5] Sync operation failed: op_id=%s entity=%s/%s error=%s",
                            op.operation_id,
                            op.entity_type,
                            op.entity_id,
                            str(e)[:200],
                        )
                        results.append(
                            SyncOperationResult(
                                operation_id=op.operation_id,
                                success=False,
                                error=str(e)[:200],
                            )
                        )
                        failed += 1

                # Commit the transaction if any operations succeeded
                if synced > 0:
                    await tx.commit()

        elapsed_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        logger.info(
            "[Story 1.5] Sync batch processed: canvas_id=%s ops=%d synced=%d failed=%d elapsed=%.0fms",
            request.canvas_id,
            len(request.operations),
            synced,
            failed,
            elapsed_ms,
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
        """Idempotent edge create/update via MERGE.

        [Source: Story 1.5 Task 6.4 — Edge sync Cypher]
        """
        payload = op.payload
        timestamp = op.timestamp.isoformat()
        source_node_id = payload.get("source_node_id") or payload.get(
            "sourceNodeId", ""
        )
        target_node_id = payload.get("target_node_id") or payload.get(
            "targetNodeId", ""
        )

        await tx.run(
            """
            MATCH (source:CanvasNode {id: $source_node_id})
            MATCH (target:CanvasNode {id: $target_node_id})
            MERGE (source)-[e:CANVAS_EDGE {id: $entity_id}]->(target)
            SET e.label = $label,
                e.canvasId = $canvas_id,
                e.updatedAt = $timestamp
            ON CREATE SET e.createdAt = $timestamp
            """,
            entity_id=op.entity_id,
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            label=payload.get("label", ""),
            canvas_id=canvas_id,
            timestamp=timestamp,
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
