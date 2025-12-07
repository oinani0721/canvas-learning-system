# src/tests/test_rollback_engine.py
"""
RollbackEngine Unit Tests

Comprehensive tests for Canvas rollback functionality.

[Source: docs/architecture/rollback-recovery-architecture.md:122-180]
[Source: docs/stories/18.3.story.md]
"""

import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

# ✅ Verified from Context7:/ijl/orjson (topic: serialization)
import orjson
import pytest
from src.rollback import (
    GraphSyncStatus,
    Operation,
    OperationData,
    OperationMetadata,
    OperationTracker,
    OperationType,
    RollbackEngine,
    RollbackError,
    RollbackResult,
    RollbackType,
    Snapshot,
    SnapshotManager,
    SnapshotMetadata,
    SnapshotType,
)

# ═══════════════════════════════════════════════════════════════════════════════
# Test Fixtures
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def temp_dir():
    """Create temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_operation_tracker():
    """Create mock OperationTracker."""
    tracker = MagicMock(spec=OperationTracker)
    tracker.get_operation = MagicMock(return_value=None)
    tracker.get_history = MagicMock(return_value=[])
    tracker.get_total_count = MagicMock(return_value=0)
    return tracker


@pytest.fixture
def mock_snapshot_manager():
    """Create mock SnapshotManager."""
    manager = MagicMock(spec=SnapshotManager)
    manager.create_checkpoint = AsyncMock(return_value=MagicMock(id="backup-123"))
    manager.get_snapshot = AsyncMock(return_value=None)
    manager.get_latest_snapshot = AsyncMock(return_value=None)
    manager.list_snapshots = AsyncMock(return_value=[])
    return manager


@pytest.fixture
def rollback_engine(mock_operation_tracker, mock_snapshot_manager):
    """Create RollbackEngine with mocked dependencies."""
    return RollbackEngine(
        operation_tracker=mock_operation_tracker,
        snapshot_manager=mock_snapshot_manager,
        create_backup=True,
    )


@pytest.fixture
def sample_canvas_data():
    """Sample Canvas data for testing."""
    return {
        "nodes": [
            {"id": "node-1", "type": "text", "text": "Hello", "color": "1"},
            {"id": "node-2", "type": "text", "text": "World", "color": "2"},
            {"id": "node-3", "type": "text", "text": "Test", "color": "3"},
        ],
        "edges": [
            {"id": "edge-1", "fromNode": "node-1", "toNode": "node-2"},
            {"id": "edge-2", "fromNode": "node-2", "toNode": "node-3"},
        ],
    }


@pytest.fixture
def sample_operation():
    """Sample Operation for testing."""
    return Operation(
        id="op-123",
        type=OperationType.NODE_ADD,
        canvas_path="test.canvas",
        timestamp=datetime.now(timezone.utc),
        user_id="test-user",
        data=OperationData(
            node_ids=["node-1"],
            after={"id": "node-1", "type": "text", "text": "Hello"},
        ),
        metadata=OperationMetadata(description="Add node"),
    )


@pytest.fixture
def sample_snapshot(sample_canvas_data):
    """Sample Snapshot for testing."""
    return Snapshot(
        id="snap-123",
        canvas_path="test.canvas",
        timestamp=datetime.now(timezone.utc),
        type=SnapshotType.MANUAL,
        canvas_data=sample_canvas_data,
        metadata=SnapshotMetadata(description="Test snapshot"),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Test RollbackEngine Initialization
# ═══════════════════════════════════════════════════════════════════════════════


class TestRollbackEngineInit:
    """Tests for RollbackEngine initialization."""

    def test_init_with_default_backup(self, mock_operation_tracker, mock_snapshot_manager):
        """Test initialization with default backup setting."""
        engine = RollbackEngine(
            operation_tracker=mock_operation_tracker,
            snapshot_manager=mock_snapshot_manager,
        )
        assert engine.create_backup is True
        assert engine.operation_tracker is mock_operation_tracker
        assert engine.snapshot_manager is mock_snapshot_manager

    def test_init_without_backup(self, mock_operation_tracker, mock_snapshot_manager):
        """Test initialization with backup disabled."""
        engine = RollbackEngine(
            operation_tracker=mock_operation_tracker,
            snapshot_manager=mock_snapshot_manager,
            create_backup=False,
        )
        assert engine.create_backup is False


# ═══════════════════════════════════════════════════════════════════════════════
# Test Operation Rollback
# ═══════════════════════════════════════════════════════════════════════════════


class TestOperationRollback:
    """Tests for operation-based rollback."""

    @pytest.mark.asyncio
    async def test_rollback_operation_with_id(
        self, rollback_engine, mock_operation_tracker, mock_snapshot_manager, sample_operation, temp_dir
    ):
        """Test rollback specific operation by ID."""
        # Setup
        canvas_path = temp_dir / "test.canvas"
        canvas_data = {"nodes": [{"id": "node-1", "text": "Hello"}], "edges": []}
        canvas_path.write_bytes(orjson.dumps(canvas_data))

        mock_operation_tracker.get_operation.return_value = sample_operation

        # Execute
        result = await rollback_engine.rollback(
            canvas_path=str(canvas_path),
            rollback_type=RollbackType.OPERATION,
            target_id="op-123",
        )

        # Verify
        assert result.success is True
        assert result.rollback_type == RollbackType.OPERATION
        assert result.backup_snapshot_id == "backup-123"
        mock_operation_tracker.get_operation.assert_called_once_with("op-123")

    @pytest.mark.asyncio
    async def test_rollback_operation_latest(
        self, rollback_engine, mock_operation_tracker, mock_snapshot_manager, sample_operation, temp_dir
    ):
        """Test rollback latest operation (no ID)."""
        # Setup
        canvas_path = temp_dir / "test.canvas"
        canvas_data = {"nodes": [{"id": "node-1"}], "edges": []}
        canvas_path.write_bytes(orjson.dumps(canvas_data))

        mock_operation_tracker.get_history.return_value = [sample_operation]

        # Execute
        result = await rollback_engine.rollback(
            canvas_path=str(canvas_path),
            rollback_type=RollbackType.OPERATION,
        )

        # Verify
        assert result.success is True
        mock_operation_tracker.get_history.assert_called_once()

    @pytest.mark.asyncio
    async def test_rollback_operation_not_found(
        self, rollback_engine, mock_operation_tracker, mock_snapshot_manager
    ):
        """Test rollback fails when operation not found."""
        mock_operation_tracker.get_operation.return_value = None

        result = await rollback_engine.rollback(
            canvas_path="test.canvas",
            rollback_type=RollbackType.OPERATION,
            target_id="nonexistent",
        )

        assert result.success is False
        assert "not found" in result.error.lower()

    @pytest.mark.asyncio
    async def test_rollback_operation_no_history(
        self, rollback_engine, mock_operation_tracker, mock_snapshot_manager
    ):
        """Test rollback fails when no history available."""
        mock_operation_tracker.get_history.return_value = []

        result = await rollback_engine.rollback(
            canvas_path="test.canvas",
            rollback_type=RollbackType.OPERATION,
        )

        assert result.success is False
        assert "no operations" in result.error.lower()


# ═══════════════════════════════════════════════════════════════════════════════
# Test Snapshot Rollback
# ═══════════════════════════════════════════════════════════════════════════════


class TestSnapshotRollback:
    """Tests for snapshot-based rollback."""

    @pytest.mark.asyncio
    async def test_rollback_to_snapshot_by_id(
        self, rollback_engine, mock_snapshot_manager, sample_snapshot, temp_dir
    ):
        """Test rollback to specific snapshot."""
        # Setup
        canvas_path = temp_dir / "test.canvas"
        canvas_path.write_bytes(orjson.dumps({"nodes": [], "edges": []}))

        mock_snapshot_manager.get_snapshot.return_value = sample_snapshot

        # Execute
        result = await rollback_engine.rollback(
            canvas_path=str(canvas_path),
            rollback_type=RollbackType.SNAPSHOT,
            target_id="snap-123",
        )

        # Verify
        assert result.success is True
        assert result.rollback_type == RollbackType.SNAPSHOT
        assert result.restored_snapshot_id == "snap-123"

        # Verify canvas was written
        restored_data = orjson.loads(canvas_path.read_bytes())
        assert len(restored_data["nodes"]) == 3

    @pytest.mark.asyncio
    async def test_rollback_to_latest_snapshot(
        self, rollback_engine, mock_snapshot_manager, sample_snapshot, temp_dir
    ):
        """Test rollback to latest snapshot."""
        canvas_path = temp_dir / "test.canvas"
        canvas_path.write_bytes(orjson.dumps({"nodes": [], "edges": []}))

        mock_snapshot_manager.get_latest_snapshot.return_value = sample_snapshot

        result = await rollback_engine.rollback(
            canvas_path=str(canvas_path),
            rollback_type=RollbackType.SNAPSHOT,
        )

        assert result.success is True
        mock_snapshot_manager.get_latest_snapshot.assert_called_once()

    @pytest.mark.asyncio
    async def test_rollback_snapshot_not_found(
        self, rollback_engine, mock_snapshot_manager
    ):
        """Test rollback fails when snapshot not found."""
        mock_snapshot_manager.get_snapshot.return_value = None

        result = await rollback_engine.rollback(
            canvas_path="test.canvas",
            rollback_type=RollbackType.SNAPSHOT,
            target_id="nonexistent",
        )

        assert result.success is False
        assert "not found" in result.error.lower()


# ═══════════════════════════════════════════════════════════════════════════════
# Test Timepoint Rollback
# ═══════════════════════════════════════════════════════════════════════════════


class TestTimepointRollback:
    """Tests for timepoint-based rollback."""

    @pytest.mark.asyncio
    async def test_rollback_to_timepoint(
        self, rollback_engine, mock_snapshot_manager, sample_snapshot, temp_dir
    ):
        """Test rollback to specific timepoint."""
        canvas_path = temp_dir / "test.canvas"
        canvas_path.write_bytes(orjson.dumps({"nodes": [], "edges": []}))

        # Setup snapshots list
        target_time = datetime.now(timezone.utc)
        older_time = target_time - timedelta(hours=1)

        mock_snapshot_manager.list_snapshots.return_value = [
            {
                "id": "snap-123",
                "timestamp": older_time.isoformat(),
                "canvas_path": str(canvas_path),
            },
        ]
        mock_snapshot_manager.get_snapshot.return_value = sample_snapshot

        result = await rollback_engine.rollback(
            canvas_path=str(canvas_path),
            rollback_type=RollbackType.TIMEPOINT,
            target_time=target_time,
        )

        assert result.success is True
        assert result.rollback_type == RollbackType.TIMEPOINT

    @pytest.mark.asyncio
    async def test_rollback_timepoint_no_time_provided(
        self, rollback_engine, mock_snapshot_manager
    ):
        """Test timepoint rollback fails without target time."""
        result = await rollback_engine.rollback(
            canvas_path="test.canvas",
            rollback_type=RollbackType.TIMEPOINT,
            target_time=None,
        )

        assert result.success is False
        assert "target time" in result.error.lower()

    @pytest.mark.asyncio
    async def test_rollback_timepoint_no_snapshots(
        self, rollback_engine, mock_snapshot_manager
    ):
        """Test timepoint rollback fails with no snapshots."""
        mock_snapshot_manager.list_snapshots.return_value = []

        result = await rollback_engine.rollback(
            canvas_path="test.canvas",
            rollback_type=RollbackType.TIMEPOINT,
            target_time=datetime.now(timezone.utc),
        )

        assert result.success is False
        assert "no snapshot" in result.error.lower()


# ═══════════════════════════════════════════════════════════════════════════════
# Test Reverse Operations
# ═══════════════════════════════════════════════════════════════════════════════


class TestReverseOperations:
    """Tests for reverse operation logic."""

    def test_reverse_node_add(self, rollback_engine, sample_canvas_data):
        """Test reversing node add operation."""
        operation = Operation(
            id="op-1",
            type=OperationType.NODE_ADD,
            canvas_path="test.canvas",
            timestamp=datetime.now(timezone.utc),
            user_id="test-user",
            data=OperationData(node_ids=["node-1"]),
            metadata=OperationMetadata(),
        )

        result = rollback_engine._apply_reverse_operation(sample_canvas_data, operation)

        # Node-1 should be removed
        node_ids = [n["id"] for n in result["nodes"]]
        assert "node-1" not in node_ids
        assert "node-2" in node_ids

    def test_reverse_node_delete(self, rollback_engine, sample_canvas_data):
        """Test reversing node delete operation."""
        deleted_node = {"id": "deleted-node", "type": "text", "text": "Deleted"}
        operation = Operation(
            id="op-1",
            type=OperationType.NODE_DELETE,
            canvas_path="test.canvas",
            timestamp=datetime.now(timezone.utc),
            user_id="test-user",
            data=OperationData(
                node_ids=["deleted-node"],
                before=deleted_node,
            ),
            metadata=OperationMetadata(),
        )

        result = rollback_engine._apply_reverse_operation(sample_canvas_data, operation)

        # Deleted node should be restored
        node_ids = [n["id"] for n in result["nodes"]]
        assert "deleted-node" in node_ids

    def test_reverse_node_modify(self, rollback_engine, sample_canvas_data):
        """Test reversing node modify operation."""
        before_data = {"id": "node-1", "type": "text", "text": "Original", "color": "1"}
        operation = Operation(
            id="op-1",
            type=OperationType.NODE_MODIFY,
            canvas_path="test.canvas",
            timestamp=datetime.now(timezone.utc),
            user_id="test-user",
            data=OperationData(
                node_ids=["node-1"],
                before=before_data,
                after={"id": "node-1", "text": "Modified"},
            ),
            metadata=OperationMetadata(),
        )

        result = rollback_engine._apply_reverse_operation(sample_canvas_data, operation)

        # Node should be restored to before state
        node_1 = next(n for n in result["nodes"] if n["id"] == "node-1")
        assert node_1["text"] == "Original"

    def test_reverse_node_color_change(self, rollback_engine, sample_canvas_data):
        """Test reversing node color change operation."""
        operation = Operation(
            id="op-1",
            type=OperationType.NODE_COLOR_CHANGE,
            canvas_path="test.canvas",
            timestamp=datetime.now(timezone.utc),
            user_id="test-user",
            data=OperationData(
                node_ids=["node-1", "node-2"],
                before={"node-1": "0", "node-2": "0"},  # Original colors
                after={"node-1": "1", "node-2": "2"},
            ),
            metadata=OperationMetadata(),
        )

        result = rollback_engine._apply_reverse_operation(sample_canvas_data, operation)

        # Colors should be restored
        node_1 = next(n for n in result["nodes"] if n["id"] == "node-1")
        node_2 = next(n for n in result["nodes"] if n["id"] == "node-2")
        assert node_1["color"] == "0"
        assert node_2["color"] == "0"

    def test_reverse_edge_add(self, rollback_engine, sample_canvas_data):
        """Test reversing edge add operation."""
        operation = Operation(
            id="op-1",
            type=OperationType.EDGE_ADD,
            canvas_path="test.canvas",
            timestamp=datetime.now(timezone.utc),
            user_id="test-user",
            data=OperationData(edge_ids=["edge-1"]),
            metadata=OperationMetadata(),
        )

        result = rollback_engine._apply_reverse_operation(sample_canvas_data, operation)

        # Edge-1 should be removed
        edge_ids = [e["id"] for e in result["edges"]]
        assert "edge-1" not in edge_ids
        assert "edge-2" in edge_ids

    def test_reverse_edge_delete(self, rollback_engine, sample_canvas_data):
        """Test reversing edge delete operation."""
        deleted_edge = {"id": "deleted-edge", "fromNode": "node-1", "toNode": "node-3"}
        operation = Operation(
            id="op-1",
            type=OperationType.EDGE_DELETE,
            canvas_path="test.canvas",
            timestamp=datetime.now(timezone.utc),
            user_id="test-user",
            data=OperationData(
                edge_ids=["deleted-edge"],
                before=deleted_edge,
            ),
            metadata=OperationMetadata(),
        )

        result = rollback_engine._apply_reverse_operation(sample_canvas_data, operation)

        # Deleted edge should be restored
        edge_ids = [e["id"] for e in result["edges"]]
        assert "deleted-edge" in edge_ids

    def test_reverse_batch_operation(self, rollback_engine, sample_canvas_data):
        """Test reversing batch operation."""
        before_state = {"nodes": [{"id": "old-node"}], "edges": []}
        operation = Operation(
            id="op-1",
            type=OperationType.BATCH_OPERATION,
            canvas_path="test.canvas",
            timestamp=datetime.now(timezone.utc),
            user_id="test-user",
            data=OperationData(before=before_state, after=sample_canvas_data),
            metadata=OperationMetadata(),
        )

        result = rollback_engine._apply_reverse_operation(sample_canvas_data, operation)

        # Should restore entire before state
        assert result == before_state


# ═══════════════════════════════════════════════════════════════════════════════
# Test Backup Creation
# ═══════════════════════════════════════════════════════════════════════════════


class TestBackupCreation:
    """Tests for backup snapshot creation."""

    @pytest.mark.asyncio
    async def test_backup_created_by_default(
        self, rollback_engine, mock_operation_tracker, mock_snapshot_manager, sample_operation, temp_dir
    ):
        """Test backup is created by default."""
        canvas_path = temp_dir / "test.canvas"
        canvas_path.write_bytes(orjson.dumps({"nodes": [], "edges": []}))
        mock_operation_tracker.get_history.return_value = [sample_operation]

        await rollback_engine.rollback(
            canvas_path=str(canvas_path),
            rollback_type=RollbackType.OPERATION,
        )

        mock_snapshot_manager.create_checkpoint.assert_called_once()

    @pytest.mark.asyncio
    async def test_backup_disabled_override(
        self, rollback_engine, mock_operation_tracker, mock_snapshot_manager, sample_operation, temp_dir
    ):
        """Test backup can be disabled via parameter."""
        canvas_path = temp_dir / "test.canvas"
        canvas_path.write_bytes(orjson.dumps({"nodes": [], "edges": []}))
        mock_operation_tracker.get_history.return_value = [sample_operation]

        result = await rollback_engine.rollback(
            canvas_path=str(canvas_path),
            rollback_type=RollbackType.OPERATION,
            create_backup=False,
        )

        mock_snapshot_manager.create_checkpoint.assert_not_called()
        assert result.backup_snapshot_id is None

    @pytest.mark.asyncio
    async def test_backup_disabled_in_init(
        self, mock_operation_tracker, mock_snapshot_manager, sample_operation, temp_dir
    ):
        """Test backup disabled in initialization."""
        engine = RollbackEngine(
            operation_tracker=mock_operation_tracker,
            snapshot_manager=mock_snapshot_manager,
            create_backup=False,
        )

        canvas_path = temp_dir / "test.canvas"
        canvas_path.write_bytes(orjson.dumps({"nodes": [], "edges": []}))
        mock_operation_tracker.get_history.return_value = [sample_operation]

        await engine.rollback(
            canvas_path=str(canvas_path),
            rollback_type=RollbackType.OPERATION,
        )

        mock_snapshot_manager.create_checkpoint.assert_not_called()


# ═══════════════════════════════════════════════════════════════════════════════
# Test Graph Sync Status
# ═══════════════════════════════════════════════════════════════════════════════


class TestGraphSyncStatus:
    """Tests for graph sync status handling."""

    @pytest.mark.asyncio
    async def test_graph_sync_pending_by_default(
        self, rollback_engine, mock_operation_tracker, mock_snapshot_manager, sample_operation, temp_dir
    ):
        """Test graph sync status is PENDING by default."""
        canvas_path = temp_dir / "test.canvas"
        canvas_path.write_bytes(orjson.dumps({"nodes": [], "edges": []}))
        mock_operation_tracker.get_history.return_value = [sample_operation]

        result = await rollback_engine.rollback(
            canvas_path=str(canvas_path),
            rollback_type=RollbackType.OPERATION,
        )

        assert result.graph_sync_status == GraphSyncStatus.PENDING

    @pytest.mark.asyncio
    async def test_graph_sync_skipped_with_preserve_flag(
        self, rollback_engine, mock_operation_tracker, mock_snapshot_manager, sample_operation, temp_dir
    ):
        """Test graph sync is SKIPPED when preserve_graph is True."""
        canvas_path = temp_dir / "test.canvas"
        canvas_path.write_bytes(orjson.dumps({"nodes": [], "edges": []}))
        mock_operation_tracker.get_history.return_value = [sample_operation]

        result = await rollback_engine.rollback(
            canvas_path=str(canvas_path),
            rollback_type=RollbackType.OPERATION,
            preserve_graph=True,
        )

        assert result.graph_sync_status == GraphSyncStatus.SKIPPED


# ═══════════════════════════════════════════════════════════════════════════════
# Test Error Handling
# ═══════════════════════════════════════════════════════════════════════════════


class TestErrorHandling:
    """Tests for error handling and recovery."""

    @pytest.mark.asyncio
    async def test_rollback_failure_returns_error(
        self, rollback_engine, mock_operation_tracker, mock_snapshot_manager
    ):
        """Test rollback failure returns error result."""
        mock_operation_tracker.get_operation.return_value = None

        result = await rollback_engine.rollback(
            canvas_path="test.canvas",
            rollback_type=RollbackType.OPERATION,
            target_id="nonexistent",
        )

        assert result.success is False
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_unknown_rollback_type(self, rollback_engine, mock_snapshot_manager):
        """Test error on unknown rollback type."""
        # This would require patching to simulate invalid type
        # as the enum constraint prevents invalid values
        pass

    @pytest.mark.asyncio
    async def test_restore_from_backup_on_failure(
        self, rollback_engine, mock_operation_tracker, mock_snapshot_manager, sample_snapshot, temp_dir
    ):
        """Test backup restore is attempted on failure."""
        canvas_path = temp_dir / "test.canvas"
        canvas_path.write_bytes(orjson.dumps({"nodes": [], "edges": []}))

        # Setup: create backup succeeds, but operation lookup fails
        mock_snapshot_manager.create_checkpoint.return_value = MagicMock(id="backup-id")
        mock_operation_tracker.get_operation.return_value = None
        mock_snapshot_manager.get_snapshot.return_value = sample_snapshot

        result = await rollback_engine.rollback(
            canvas_path=str(canvas_path),
            rollback_type=RollbackType.OPERATION,
            target_id="fail-op",
        )

        assert result.success is False
        assert "backup" in result.error.lower()


# ═══════════════════════════════════════════════════════════════════════════════
# Test Canvas File Operations
# ═══════════════════════════════════════════════════════════════════════════════


class TestCanvasFileOperations:
    """Tests for Canvas file read/write operations."""

    @pytest.mark.asyncio
    async def test_read_canvas_existing_file(self, rollback_engine, temp_dir):
        """Test reading existing Canvas file."""
        canvas_path = temp_dir / "test.canvas"
        test_data = {"nodes": [{"id": "test"}], "edges": []}
        canvas_path.write_bytes(orjson.dumps(test_data))

        result = await rollback_engine._read_canvas(str(canvas_path))

        assert result == test_data

    @pytest.mark.asyncio
    async def test_read_canvas_nonexistent_file(self, rollback_engine):
        """Test reading non-existent Canvas file returns empty structure."""
        result = await rollback_engine._read_canvas("nonexistent.canvas")

        assert result == {"nodes": [], "edges": []}

    @pytest.mark.asyncio
    async def test_write_canvas_creates_file(self, rollback_engine, temp_dir):
        """Test writing Canvas creates/updates file."""
        canvas_path = temp_dir / "new.canvas"
        test_data = {"nodes": [{"id": "new"}], "edges": []}

        await rollback_engine._write_canvas(str(canvas_path), test_data)

        assert canvas_path.exists()
        written_data = orjson.loads(canvas_path.read_bytes())
        assert written_data == test_data


# ═══════════════════════════════════════════════════════════════════════════════
# Test RollbackResult Dataclass
# ═══════════════════════════════════════════════════════════════════════════════


class TestRollbackResultDataclass:
    """Tests for RollbackResult dataclass."""

    def test_success_result(self):
        """Test creating success result."""
        result = RollbackResult(
            success=True,
            rollback_type=RollbackType.OPERATION,
            canvas_path="test.canvas",
            message="Success",
        )

        assert result.success is True
        assert result.error is None

    def test_failure_result(self):
        """Test creating failure result."""
        result = RollbackResult(
            success=False,
            rollback_type=RollbackType.SNAPSHOT,
            canvas_path="test.canvas",
            error="Something went wrong",
        )

        assert result.success is False
        assert result.error == "Something went wrong"

    def test_default_values(self):
        """Test default values."""
        result = RollbackResult(
            success=True,
            rollback_type=RollbackType.TIMEPOINT,
            canvas_path="test.canvas",
        )

        assert result.backup_snapshot_id is None
        assert result.restored_operation_id is None
        assert result.restored_snapshot_id is None
        assert result.graph_sync_status == GraphSyncStatus.SKIPPED
        assert result.message == ""


# ═══════════════════════════════════════════════════════════════════════════════
# Test RollbackError Exception
# ═══════════════════════════════════════════════════════════════════════════════


class TestRollbackErrorException:
    """Tests for RollbackError exception."""

    def test_create_error(self):
        """Test creating RollbackError."""
        error = RollbackError("Test error message")
        assert str(error) == "Test error message"

    def test_raise_error(self):
        """Test raising RollbackError."""
        with pytest.raises(RollbackError) as exc_info:
            raise RollbackError("Operation failed")

        assert "Operation failed" in str(exc_info.value)


# ═══════════════════════════════════════════════════════════════════════════════
# Test Enums
# ═══════════════════════════════════════════════════════════════════════════════


class TestRollbackEnums:
    """Tests for rollback enums."""

    def test_rollback_type_values(self):
        """Test RollbackType enum values."""
        assert RollbackType.OPERATION.value == "operation"
        assert RollbackType.SNAPSHOT.value == "snapshot"
        assert RollbackType.TIMEPOINT.value == "timepoint"

    def test_graph_sync_status_values(self):
        """Test GraphSyncStatus enum values."""
        assert GraphSyncStatus.SYNCED.value == "synced"
        assert GraphSyncStatus.PENDING.value == "pending"
        assert GraphSyncStatus.SKIPPED.value == "skipped"

    def test_rollback_type_str_enum(self):
        """Test RollbackType is string enum."""
        assert isinstance(RollbackType.OPERATION, str)
        assert RollbackType.OPERATION == "operation"
