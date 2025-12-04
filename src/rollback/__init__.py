# src/rollback/__init__.py
"""
Canvas Learning System - Rollback Module

This module provides operation tracking, snapshot management, and rollback
functionality for Canvas files.

[Source: docs/architecture/rollback-recovery-architecture.md]
"""

from .graph_sync_service import (
    GraphSyncService,
    SyncResult,
)
from .models import (
    Operation,
    OperationData,
    OperationMetadata,
    OperationType,
    Snapshot,
    SnapshotMetadata,
    SnapshotType,
)
from .operation_tracker import OperationTracker
from .rollback_engine import (
    GraphSyncStatus,
    RollbackEngine,
    RollbackError,
    RollbackResult,
    RollbackType,
)
from .snapshot_manager import SnapshotManager
from .tracked_operator import TrackedCanvasOperator

__all__ = [
    # Operation models (Story 18.1)
    "Operation",
    "OperationType",
    "OperationData",
    "OperationMetadata",
    "OperationTracker",
    "TrackedCanvasOperator",
    # Snapshot models (Story 18.2)
    "Snapshot",
    "SnapshotType",
    "SnapshotMetadata",
    "SnapshotManager",
    # Rollback engine (Story 18.3)
    "RollbackEngine",
    "RollbackType",
    "RollbackResult",
    "RollbackError",
    "GraphSyncStatus",
    # Graph sync service (Story 18.4)
    "GraphSyncService",
    "SyncResult",
]
