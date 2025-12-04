# backend/app/services/rollback_service.py
"""
Rollback Service - 回滚系统业务逻辑层

Encapsulates all rollback functionality including operation tracking,
snapshot management, and rollback execution.

[Source: docs/architecture/rollback-recovery-architecture.md]
[Source: docs/stories/18.5.story.md - AC 4-5]

Author: Canvas Learning System Team
Version: 1.0.0
Created: 2025-12-04
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# ✅ Verified from Context7:/pydantic/pydantic (topic: BaseModel)
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class RollbackServiceConfig(BaseModel):
    """RollbackService configuration model.

    [Source: docs/architecture/rollback-recovery-architecture.md:100-150]
    """

    storage_path: str = ".canvas-learning"
    history_limit: int = 100
    snapshot_interval: int = 300
    max_snapshots: int = 50
    graphiti_timeout_ms: int = 200
    enable_graphiti_sync: bool = True
    enable_auto_backup: bool = True


class RollbackService:
    """
    Rollback Service - Encapsulates all rollback functionality.

    This service provides a unified interface for:
    - Operation history tracking (Story 18.1)
    - Snapshot management (Story 18.2)
    - Rollback execution (Story 18.3)
    - Graph synchronization (Story 18.4)
    - Diff computation (Story 18.5)

    [Source: docs/architecture/rollback-recovery-architecture.md]
    [Source: docs/stories/18.5.story.md - AC 4-5]

    Usage:
        >>> service = RollbackService(
        ...     storage_path=".canvas-learning",
        ...     history_limit=100,
        ... )
        >>> history = service.get_operation_history("canvas.canvas")
        >>> await service.cleanup()
    """

    def __init__(
        self,
        storage_path: str = ".canvas-learning",
        history_limit: int = 100,
        snapshot_interval: int = 300,
        max_snapshots: int = 50,
        graphiti_timeout_ms: int = 200,
        enable_graphiti_sync: bool = True,
        enable_auto_backup: bool = True,
    ):
        """
        Initialize RollbackService.

        [Source: docs/architecture/rollback-recovery-architecture.md:100-150]
        [Source: docs/stories/18.5.story.md - AC 4]

        Args:
            storage_path: Base path for rollback data storage
            history_limit: Maximum operation history records per Canvas
            snapshot_interval: Auto snapshot interval in seconds
            max_snapshots: Maximum snapshots per Canvas
            graphiti_timeout_ms: Graphiti sync timeout in milliseconds
            enable_graphiti_sync: Enable Graphiti knowledge graph sync
            enable_auto_backup: Create backup snapshot before rollback
        """
        self._storage_path = Path(storage_path)
        self._history_limit = history_limit
        self._snapshot_interval = snapshot_interval
        self._max_snapshots = max_snapshots
        self._graphiti_timeout_ms = graphiti_timeout_ms
        self._enable_graphiti_sync = enable_graphiti_sync
        self._enable_auto_backup = enable_auto_backup

        # Core components (lazy initialized)
        self._operation_tracker = None
        self._snapshot_manager = None
        self._rollback_engine = None
        self._graph_sync_service = None

        self._initialized = False

        logger.debug(
            f"RollbackService created with storage_path={storage_path}, "
            f"history_limit={history_limit}, max_snapshots={max_snapshots}"
        )

    def _ensure_initialized(self) -> None:
        """Ensure all components are initialized.

        [Source: docs/architecture/rollback-recovery-architecture.md:602-640]
        """
        if self._initialized:
            return

        # Import rollback module components
        from src.rollback import (
            GraphSyncService,
            OperationTracker,
            RollbackEngine,
            SnapshotManager,
        )

        # Initialize OperationTracker (Story 18.1)
        self._operation_tracker = OperationTracker(
            storage_root=self._storage_path,
            max_history_per_canvas=self._history_limit,
        )

        # Initialize SnapshotManager (Story 18.2)
        self._snapshot_manager = SnapshotManager(
            storage_root=self._storage_path,
            auto_interval=self._snapshot_interval,
            max_snapshots=self._max_snapshots,
        )

        # Initialize GraphSyncService (Story 18.4)
        if self._enable_graphiti_sync:
            self._graph_sync_service = GraphSyncService(
                timeout_ms=self._graphiti_timeout_ms,
                enable_fallback=True,
            )

        # Initialize RollbackEngine (Story 18.3)
        self._rollback_engine = RollbackEngine(
            operation_tracker=self._operation_tracker,
            snapshot_manager=self._snapshot_manager,
            graph_sync_service=self._graph_sync_service,
            create_backup=self._enable_auto_backup,
        )

        self._initialized = True
        logger.info("RollbackService initialized successfully")

    # ═══════════════════════════════════════════════════════════════════════════
    # Operation History (Story 18.1)
    # ═══════════════════════════════════════════════════════════════════════════

    def get_operation_history(
        self,
        canvas_path: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Any]:
        """
        Get operation history for a Canvas.

        [Source: docs/architecture/rollback-recovery-architecture.md:296-310]
        [Source: docs/stories/18.1.story.md - AC 6]

        Args:
            canvas_path: Canvas file path
            limit: Maximum records to return
            offset: Records to skip

        Returns:
            List of Operation objects
        """
        self._ensure_initialized()
        return self._operation_tracker.get_history(
            canvas_path, limit=limit, offset=offset
        )

    def get_operation_count(self, canvas_path: str) -> int:
        """
        Get total operation count for a Canvas.

        [Source: docs/stories/18.1.story.md - AC 6]

        Args:
            canvas_path: Canvas file path

        Returns:
            Total operation count
        """
        self._ensure_initialized()
        return self._operation_tracker.get_total_count(canvas_path)

    def get_operation(self, operation_id: str) -> Optional[Any]:
        """
        Get a single operation by ID.

        [Source: docs/architecture/rollback-recovery-architecture.md:296-310]

        Args:
            operation_id: Operation UUID

        Returns:
            Operation object or None
        """
        self._ensure_initialized()
        return self._operation_tracker.get_operation(operation_id)

    # ═══════════════════════════════════════════════════════════════════════════
    # Snapshot Management (Story 18.2)
    # ═══════════════════════════════════════════════════════════════════════════

    async def list_snapshots(
        self,
        canvas_path: str,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        List snapshots for a Canvas.

        [Source: docs/architecture/rollback-recovery-architecture.md:312-326]
        [Source: docs/stories/18.2.story.md - AC 6]

        Args:
            canvas_path: Canvas file path
            limit: Maximum snapshots to return
            offset: Snapshots to skip

        Returns:
            List of snapshot metadata dicts
        """
        self._ensure_initialized()
        return await self._snapshot_manager.list_snapshots(
            canvas_path, limit=limit, offset=offset
        )

    async def get_snapshot_count(self, canvas_path: str) -> int:
        """
        Get total snapshot count for a Canvas.

        [Source: docs/stories/18.2.story.md - AC 6]

        Args:
            canvas_path: Canvas file path

        Returns:
            Total snapshot count
        """
        self._ensure_initialized()
        return await self._snapshot_manager.get_total_count(canvas_path)

    async def create_snapshot(
        self,
        canvas_path: str,
        description: Optional[str] = None,
        created_by: str = "user",
    ) -> Any:
        """
        Create a manual snapshot.

        [Source: docs/architecture/rollback-recovery-architecture.md:328-342]
        [Source: docs/stories/18.2.story.md - AC 7]

        Args:
            canvas_path: Canvas file path
            description: Snapshot description
            created_by: Creator identifier

        Returns:
            Created Snapshot object
        """
        from src.rollback import SnapshotType

        self._ensure_initialized()
        return await self._snapshot_manager.create_snapshot(
            canvas_path=canvas_path,
            snapshot_type=SnapshotType.MANUAL,
            description=description,
            created_by=created_by,
        )

    async def get_snapshot(
        self, canvas_path: str, snapshot_id: str
    ) -> Optional[Any]:
        """
        Get a single snapshot by ID.

        [Source: docs/architecture/rollback-recovery-architecture.md:312-326]

        Args:
            canvas_path: Canvas file path
            snapshot_id: Snapshot UUID

        Returns:
            Snapshot object or None
        """
        self._ensure_initialized()
        return await self._snapshot_manager.get_snapshot(canvas_path, snapshot_id)

    # ═══════════════════════════════════════════════════════════════════════════
    # Rollback Execution (Story 18.3)
    # ═══════════════════════════════════════════════════════════════════════════

    async def rollback(
        self,
        canvas_path: str,
        rollback_type: str,
        target_id: Optional[str] = None,
        target_time: Optional[datetime] = None,
        create_backup: bool = True,
        preserve_graph: bool = False,
    ) -> Any:
        """
        Execute a rollback operation.

        [Source: docs/architecture/rollback-recovery-architecture.md:122-180]
        [Source: docs/stories/18.3.story.md - AC 6]

        Args:
            canvas_path: Canvas file path
            rollback_type: Type of rollback (operation/snapshot/timepoint)
            target_id: Target operation or snapshot ID
            target_time: Target timepoint (for timepoint rollback)
            create_backup: Create backup before rollback
            preserve_graph: Skip graph synchronization

        Returns:
            RollbackResult object
        """
        from src.rollback import RollbackType

        self._ensure_initialized()

        rb_type = RollbackType(rollback_type)

        return await self._rollback_engine.rollback(
            canvas_path=canvas_path,
            rollback_type=rb_type,
            target_id=target_id,
            target_time=target_time,
            create_backup=create_backup,
            preserve_graph=preserve_graph,
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # Diff Computation (Story 18.5)
    # ═══════════════════════════════════════════════════════════════════════════

    async def compute_diff(
        self,
        canvas_path: str,
        snapshot_id: str,
    ) -> Dict[str, Any]:
        """
        Compute diff between snapshot and current Canvas state.

        [Source: docs/architecture/rollback-recovery-architecture.md:382-400]
        [Source: docs/stories/18.5.story.md - AC 1]

        Args:
            canvas_path: Canvas file path
            snapshot_id: Snapshot ID to compare against

        Returns:
            Dict with nodes_diff and edges_diff
        """
        import json

        self._ensure_initialized()

        # Get snapshot
        snapshot = await self._snapshot_manager.get_snapshot(canvas_path, snapshot_id)
        if snapshot is None:
            raise ValueError(f"Snapshot {snapshot_id} not found")

        # Read current Canvas
        canvas_file = Path(canvas_path)
        if not canvas_file.exists():
            raise FileNotFoundError(f"Canvas file not found: {canvas_path}")

        with open(canvas_file, "r", encoding="utf-8") as f:
            current_data = json.load(f)

        # Get snapshot data
        snapshot_data = snapshot.canvas_data

        # Compute diff
        return self._compute_canvas_diff(snapshot_data, current_data)

    def _compute_canvas_diff(
        self,
        snapshot_data: Dict[str, Any],
        current_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Compute difference between two Canvas states.

        [Source: docs/architecture/rollback-recovery-architecture.md:382-400]

        Args:
            snapshot_data: Snapshot Canvas data
            current_data: Current Canvas data

        Returns:
            Dict with nodes_diff and edges_diff
        """
        # Extract nodes and edges
        snap_nodes = {n["id"]: n for n in snapshot_data.get("nodes", [])}
        curr_nodes = {n["id"]: n for n in current_data.get("nodes", [])}

        snap_edges = {e["id"]: e for e in snapshot_data.get("edges", [])}
        curr_edges = {e["id"]: e for e in current_data.get("edges", [])}

        # Compute node diff
        nodes_added = []
        nodes_removed = []
        nodes_modified = []

        for node_id, node in curr_nodes.items():
            if node_id not in snap_nodes:
                nodes_added.append({
                    "id": node_id,
                    "text": node.get("text"),
                    "color": node.get("color"),
                })
            elif snap_nodes[node_id] != node:
                nodes_modified.append({
                    "id": node_id,
                    "before": {
                        k: v for k, v in snap_nodes[node_id].items()
                        if snap_nodes[node_id].get(k) != node.get(k)
                    },
                    "after": {
                        k: v for k, v in node.items()
                        if snap_nodes[node_id].get(k) != node.get(k)
                    },
                })

        for node_id, node in snap_nodes.items():
            if node_id not in curr_nodes:
                nodes_removed.append({
                    "id": node_id,
                    "text": node.get("text"),
                    "color": node.get("color"),
                })

        # Compute edge diff
        edges_added = []
        edges_removed = []

        for edge_id, edge in curr_edges.items():
            if edge_id not in snap_edges:
                edges_added.append({
                    "id": edge_id,
                    "from_node": edge.get("fromNode"),
                    "to_node": edge.get("toNode"),
                })

        for edge_id, edge in snap_edges.items():
            if edge_id not in curr_edges:
                edges_removed.append({
                    "id": edge_id,
                    "from_node": edge.get("fromNode"),
                    "to_node": edge.get("toNode"),
                })

        return {
            "nodes_diff": {
                "added": nodes_added,
                "removed": nodes_removed,
                "modified": nodes_modified,
            },
            "edges_diff": {
                "added": edges_added,
                "removed": edges_removed,
            },
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # Service Lifecycle
    # ═══════════════════════════════════════════════════════════════════════════

    async def cleanup(self) -> None:
        """
        Cleanup service resources.

        [Source: docs/stories/18.5.story.md - AC 5]

        Should be called when the service is no longer needed.
        """
        logger.debug("RollbackService cleanup started")

        if self._graph_sync_service is not None:
            # GraphSyncService may have async cleanup
            if hasattr(self._graph_sync_service, "cleanup"):
                try:
                    await self._graph_sync_service.cleanup()
                except Exception as e:
                    logger.warning(f"GraphSyncService cleanup error: {e}")

        if self._snapshot_manager is not None:
            # Stop auto snapshot scheduler if running
            if hasattr(self._snapshot_manager, "stop_auto_scheduler"):
                try:
                    await self._snapshot_manager.stop_auto_scheduler()
                except Exception as e:
                    logger.warning(f"SnapshotManager cleanup error: {e}")

        self._initialized = False
        logger.debug("RollbackService cleanup completed")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get service statistics.

        Returns:
            Dict with service configuration and status
        """
        return {
            "initialized": self._initialized,
            "storage_path": str(self._storage_path),
            "history_limit": self._history_limit,
            "snapshot_interval": self._snapshot_interval,
            "max_snapshots": self._max_snapshots,
            "graphiti_timeout_ms": self._graphiti_timeout_ms,
            "enable_graphiti_sync": self._enable_graphiti_sync,
            "enable_auto_backup": self._enable_auto_backup,
        }


# Export for dependency injection
__all__ = ["RollbackService", "RollbackServiceConfig"]
