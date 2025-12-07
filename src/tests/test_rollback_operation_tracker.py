# Canvas Learning System - Rollback Operation Tracker Tests
# ✅ Verified from Context7:/pytest-dev/pytest (topic: fixtures, parametrize)
"""
Tests for the rollback operation tracker module.

These tests verify the Operation model, OperationTracker, and TrackedCanvasOperator
function correctly for tracking and persisting Canvas operations.

[Source: docs/stories/18.1.story.md - AC 1-7]
[Source: docs/architecture/rollback-recovery-architecture.md:68-180]
"""

import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from src.rollback.models import (
    Operation,
    OperationData,
    OperationMetadata,
    OperationType,
    Snapshot,
    SnapshotMetadata,
    SnapshotType,
)
from src.rollback.operation_tracker import OperationTracker
from src.rollback.tracked_operator import TrackedCanvasOperator

# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def temp_storage_root():
    """Create a temporary directory for storage."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def operation_tracker(temp_storage_root):
    """Create an OperationTracker instance for testing."""
    return OperationTracker(
        storage_root=temp_storage_root,
        max_history_per_canvas=10,
    )


@pytest.fixture
def sample_operation():
    """Create a sample Operation for testing."""
    return Operation(
        id="test-op-001",
        type=OperationType.NODE_ADD,
        canvas_path="test.canvas",
        timestamp=datetime.now(timezone.utc),
        user_id="test-user",
        data=OperationData(
            before=None,
            after={"id": "node1", "text": "Test Node", "color": "1"},
            node_ids=["node1"],
            edge_ids=None,
        ),
        metadata=OperationMetadata(
            description="Add node: Test Node",
            agent_id="basic-decomposition",
            request_id="req-123",
        ),
    )


@pytest.fixture
def mock_canvas_service():
    """Create a mock CanvasService for testing TrackedCanvasOperator."""
    mock = MagicMock()
    mock.add_node.return_value = {"id": "node1", "text": "New Node", "color": "1"}
    mock.delete_node.return_value = True
    mock.get_node.return_value = {"id": "node1", "text": "Old Node", "color": "2"}
    mock.update_node.return_value = {"id": "node1", "text": "Updated Node", "color": "3"}
    mock.add_edge.return_value = {"id": "edge1", "fromNode": "node1", "toNode": "node2"}
    mock.delete_edge.return_value = True
    mock.get_edge.return_value = {"id": "edge1", "fromNode": "node1", "toNode": "node2"}
    mock.get_canvas_data.return_value = {"nodes": [], "edges": []}
    mock.batch_update.return_value = {"success": True}
    return mock


# ═══════════════════════════════════════════════════════════════════════════════
# Operation Model Tests
# [Source: docs/architecture/rollback-recovery-architecture.md:38-66]
# ═══════════════════════════════════════════════════════════════════════════════


class TestOperationType:
    """Test suite for OperationType enum."""

    def test_all_operation_types_exist(self):
        """
        Test that all 7 operation types are defined.

        [Source: docs/stories/18.1.story.md - AC 1]
        """
        expected_types = [
            "node_add",
            "node_delete",
            "node_modify",
            "node_color_change",
            "edge_add",
            "edge_delete",
            "batch_operation",
        ]
        actual_types = [t.value for t in OperationType]
        assert sorted(actual_types) == sorted(expected_types)

    @pytest.mark.parametrize("op_type", list(OperationType))
    def test_operation_type_is_string_enum(self, op_type):
        """Test that each operation type is a string enum."""
        assert isinstance(op_type.value, str)
        assert op_type.value == str(op_type.value)


class TestOperationData:
    """Test suite for OperationData dataclass."""

    def test_create_operation_data_with_defaults(self):
        """Test creating OperationData with default values."""
        data = OperationData()
        assert data.before is None
        assert data.after is None
        assert data.node_ids is None
        assert data.edge_ids is None

    def test_create_operation_data_with_values(self):
        """Test creating OperationData with explicit values."""
        data = OperationData(
            before={"text": "old"},
            after={"text": "new"},
            node_ids=["node1", "node2"],
            edge_ids=["edge1"],
        )
        assert data.before == {"text": "old"}
        assert data.after == {"text": "new"}
        assert data.node_ids == ["node1", "node2"]
        assert data.edge_ids == ["edge1"]

    def test_to_dict(self):
        """Test OperationData serialization to dict."""
        data = OperationData(
            before={"x": 1},
            after={"x": 2},
            node_ids=["n1"],
            edge_ids=None,
        )
        result = data.to_dict()
        assert result["before"] == {"x": 1}
        assert result["after"] == {"x": 2}
        assert result["node_ids"] == ["n1"]
        assert result["edge_ids"] is None

    def test_from_dict(self):
        """Test OperationData deserialization from dict."""
        data_dict = {
            "before": {"text": "old"},
            "after": {"text": "new"},
            "node_ids": ["node1"],
            "edge_ids": ["edge1"],
        }
        data = OperationData.from_dict(data_dict)
        assert data.before == {"text": "old"}
        assert data.after == {"text": "new"}
        assert data.node_ids == ["node1"]
        assert data.edge_ids == ["edge1"]


class TestOperationMetadata:
    """Test suite for OperationMetadata dataclass."""

    def test_create_metadata_with_defaults(self):
        """Test creating OperationMetadata with default values."""
        meta = OperationMetadata()
        assert meta.description == ""
        assert meta.agent_id is None
        assert meta.request_id is None

    def test_to_dict(self):
        """Test OperationMetadata serialization."""
        meta = OperationMetadata(
            description="Test operation",
            agent_id="scoring-agent",
            request_id="req-456",
        )
        result = meta.to_dict()
        assert result["description"] == "Test operation"
        assert result["agent_id"] == "scoring-agent"
        assert result["request_id"] == "req-456"

    def test_from_dict(self):
        """Test OperationMetadata deserialization."""
        meta_dict = {
            "description": "Delete node",
            "agent_id": "deep-decomposition",
            "request_id": None,
        }
        meta = OperationMetadata.from_dict(meta_dict)
        assert meta.description == "Delete node"
        assert meta.agent_id == "deep-decomposition"
        assert meta.request_id is None


class TestOperation:
    """Test suite for Operation dataclass."""

    def test_create_operation(self, sample_operation):
        """
        Test creating a complete Operation record.

        [Source: docs/stories/18.1.story.md - AC 2]
        """
        op = sample_operation
        assert op.id == "test-op-001"
        assert op.type == OperationType.NODE_ADD
        assert op.canvas_path == "test.canvas"
        assert op.user_id == "test-user"
        assert op.data.after["id"] == "node1"
        assert op.metadata.agent_id == "basic-decomposition"

    def test_operation_to_dict(self, sample_operation):
        """Test Operation serialization to dict."""
        result = sample_operation.to_dict()
        assert result["id"] == "test-op-001"
        assert result["type"] == "node_add"
        assert result["canvas_path"] == "test.canvas"
        assert result["user_id"] == "test-user"
        assert "timestamp" in result
        assert "data" in result
        assert "metadata" in result

    def test_operation_from_dict(self, sample_operation):
        """Test Operation deserialization from dict."""
        op_dict = sample_operation.to_dict()
        restored = Operation.from_dict(op_dict)
        assert restored.id == sample_operation.id
        assert restored.type == sample_operation.type
        assert restored.canvas_path == sample_operation.canvas_path
        assert restored.user_id == sample_operation.user_id

    def test_operation_timestamp_serialization(self, sample_operation):
        """Test that timestamp is properly serialized as ISO format."""
        result = sample_operation.to_dict()
        timestamp_str = result["timestamp"]
        # Should be parseable as ISO 8601
        parsed = datetime.fromisoformat(timestamp_str)
        assert parsed is not None


# ═══════════════════════════════════════════════════════════════════════════════
# OperationTracker Tests
# [Source: docs/architecture/rollback-recovery-architecture.md:68-120]
# ═══════════════════════════════════════════════════════════════════════════════


class TestOperationTracker:
    """Test suite for OperationTracker class."""

    def test_track_operation(self, operation_tracker, sample_operation):
        """Test tracking a single operation."""
        op_id = operation_tracker.track_operation(sample_operation)
        assert op_id == sample_operation.id

    def test_get_history_empty(self, operation_tracker):
        """Test getting history for canvas with no operations."""
        history = operation_tracker.get_history("nonexistent.canvas")
        assert history == []

    def test_get_history_returns_operations(self, operation_tracker, sample_operation):
        """Test getting history returns tracked operations."""
        operation_tracker.track_operation(sample_operation)
        history = operation_tracker.get_history("test.canvas")
        assert len(history) == 1
        assert history[0].id == sample_operation.id

    def test_get_history_reverse_chronological(self, operation_tracker):
        """
        Test that history is returned in reverse chronological order.

        [Source: docs/stories/18.1.story.md - AC 6]
        """
        for i in range(5):
            op = Operation(
                id=f"op-{i}",
                type=OperationType.NODE_ADD,
                canvas_path="test.canvas",
                timestamp=datetime.now(timezone.utc),
                user_id="user",
            )
            operation_tracker.track_operation(op)

        history = operation_tracker.get_history("test.canvas")
        # Most recent first
        assert history[0].id == "op-4"
        assert history[4].id == "op-0"

    def test_get_history_pagination(self, operation_tracker):
        """Test pagination of history results."""
        for i in range(10):
            op = Operation(
                id=f"op-{i}",
                type=OperationType.NODE_ADD,
                canvas_path="test.canvas",
                timestamp=datetime.now(timezone.utc),
                user_id="user",
            )
            operation_tracker.track_operation(op)

        # Get first page
        page1 = operation_tracker.get_history("test.canvas", limit=3, offset=0)
        assert len(page1) == 3
        assert page1[0].id == "op-9"

        # Get second page
        page2 = operation_tracker.get_history("test.canvas", limit=3, offset=3)
        assert len(page2) == 3
        assert page2[0].id == "op-6"

    def test_max_history_limit(self, operation_tracker):
        """
        Test that history is limited to max_history_per_canvas.

        [Source: docs/stories/18.1.story.md - AC 3]
        """
        # Tracker is configured with max_history=10
        for i in range(15):
            op = Operation(
                id=f"op-{i}",
                type=OperationType.NODE_ADD,
                canvas_path="test.canvas",
                timestamp=datetime.now(timezone.utc),
                user_id="user",
            )
            operation_tracker.track_operation(op)

        total = operation_tracker.get_total_count("test.canvas")
        assert total == 10  # Limited to max

    def test_get_operation_by_id(self, operation_tracker, sample_operation):
        """Test retrieving a single operation by ID."""
        operation_tracker.track_operation(sample_operation)
        found = operation_tracker.get_operation(sample_operation.id)
        assert found is not None
        assert found.id == sample_operation.id

    def test_get_operation_not_found(self, operation_tracker):
        """Test retrieving non-existent operation returns None."""
        result = operation_tracker.get_operation("nonexistent-id")
        assert result is None

    def test_get_total_count(self, operation_tracker, sample_operation):
        """Test getting total operation count."""
        assert operation_tracker.get_total_count("test.canvas") == 0
        operation_tracker.track_operation(sample_operation)
        assert operation_tracker.get_total_count("test.canvas") == 1

    def test_clear_history(self, operation_tracker, sample_operation):
        """Test clearing history for a canvas."""
        operation_tracker.track_operation(sample_operation)
        assert operation_tracker.get_total_count("test.canvas") == 1

        operation_tracker.clear_history("test.canvas")
        assert operation_tracker.get_total_count("test.canvas") == 0

    def test_persistence_to_disk(self, temp_storage_root):
        """
        Test that operations are persisted to disk.

        [Source: docs/stories/18.1.story.md - AC 4]
        """
        tracker1 = OperationTracker(storage_root=temp_storage_root)
        op = Operation(
            id="persistent-op",
            type=OperationType.NODE_MODIFY,
            canvas_path="persist.canvas",
            timestamp=datetime.now(timezone.utc),
            user_id="user",
        )
        tracker1.track_operation(op)

        # Create new tracker instance (simulates restart)
        tracker2 = OperationTracker(storage_root=temp_storage_root)
        history = tracker2.get_history("persist.canvas")
        assert len(history) == 1
        assert history[0].id == "persistent-op"

    def test_history_directory_structure(self, operation_tracker, sample_operation):
        """
        Test that history is stored in correct directory structure.

        [Source: docs/stories/18.1.story.md - AC 4]
        Expected: .canvas-learning/history/{canvas_name}/
        """
        operation_tracker.track_operation(sample_operation)

        history_dir = operation_tracker.storage_root / "history" / "test"
        assert history_dir.exists()
        assert (history_dir / "operations.json").exists()

    def test_create_operation_helper(self, operation_tracker):
        """Test the create_operation convenience method."""
        op = operation_tracker.create_operation(
            operation_type=OperationType.EDGE_ADD,
            canvas_path="helper.canvas",
            user_id="helper-user",
            before=None,
            after={"id": "edge1"},
            edge_ids=["edge1"],
            agent_id="test-agent",
            description="Add edge",
        )
        assert op.type == OperationType.EDGE_ADD
        assert op.canvas_path == "helper.canvas"
        assert op.user_id == "helper-user"
        assert op.data.after == {"id": "edge1"}
        assert op.metadata.agent_id == "test-agent"


# ═══════════════════════════════════════════════════════════════════════════════
# TrackedCanvasOperator Tests
# [Source: docs/architecture/rollback-recovery-architecture.md:122-180]
# ═══════════════════════════════════════════════════════════════════════════════


class TestTrackedCanvasOperator:
    """Test suite for TrackedCanvasOperator wrapper class."""

    @pytest.fixture
    def tracked_operator(self, mock_canvas_service, operation_tracker):
        """Create a TrackedCanvasOperator for testing."""
        return TrackedCanvasOperator(
            canvas_service=mock_canvas_service,
            tracker=operation_tracker,
            user_id="test-user",
        )

    def test_add_node_tracks_operation(self, tracked_operator, operation_tracker):
        """
        Test that add_node tracks the operation.

        [Source: docs/stories/18.1.story.md - AC 5]
        """
        result = tracked_operator.add_node(
            canvas_path="test.canvas",
            node_data={"text": "New Node"},
            agent_id="basic-decomposition",
        )

        assert result["id"] == "node1"
        history = operation_tracker.get_history("test.canvas")
        assert len(history) == 1
        assert history[0].type == OperationType.NODE_ADD

    def test_delete_node_tracks_operation(self, tracked_operator, operation_tracker):
        """Test that delete_node tracks the operation."""
        result = tracked_operator.delete_node(
            canvas_path="test.canvas",
            node_id="node1",
            agent_id="cleanup-agent",
        )

        assert result is True
        history = operation_tracker.get_history("test.canvas")
        assert len(history) == 1
        assert history[0].type == OperationType.NODE_DELETE
        assert history[0].data.before is not None

    def test_modify_node_tracks_operation(self, tracked_operator, operation_tracker):
        """Test that modify_node tracks the operation."""
        result = tracked_operator.modify_node(
            canvas_path="test.canvas",
            node_id="node1",
            updates={"text": "Updated Text"},
            agent_id="scoring-agent",
        )

        assert result["text"] == "Updated Node"
        history = operation_tracker.get_history("test.canvas")
        assert len(history) == 1
        assert history[0].type == OperationType.NODE_MODIFY
        assert history[0].data.before is not None
        assert history[0].data.after is not None

    def test_change_node_color_tracks_operation(self, tracked_operator, operation_tracker):
        """Test that change_node_color tracks with NODE_COLOR_CHANGE type."""
        result = tracked_operator.change_node_color(
            canvas_path="test.canvas",
            node_id="node1",
            new_color="3",
            agent_id="scoring-agent",
        )

        history = operation_tracker.get_history("test.canvas")
        assert len(history) == 1
        assert history[0].type == OperationType.NODE_COLOR_CHANGE
        assert history[0].data.before == {"color": "2"}  # From mock
        assert history[0].data.after == {"color": "3"}

    def test_add_edge_tracks_operation(self, tracked_operator, operation_tracker):
        """Test that add_edge tracks the operation."""
        result = tracked_operator.add_edge(
            canvas_path="test.canvas",
            edge_data={"fromNode": "node1", "toNode": "node2"},
            agent_id="graph-agent",
        )

        assert result["id"] == "edge1"
        history = operation_tracker.get_history("test.canvas")
        assert len(history) == 1
        assert history[0].type == OperationType.EDGE_ADD

    def test_delete_edge_tracks_operation(self, tracked_operator, operation_tracker):
        """Test that delete_edge tracks the operation."""
        result = tracked_operator.delete_edge(
            canvas_path="test.canvas",
            edge_id="edge1",
            agent_id="cleanup-agent",
        )

        assert result is True
        history = operation_tracker.get_history("test.canvas")
        assert len(history) == 1
        assert history[0].type == OperationType.EDGE_DELETE

    def test_batch_operation_tracks_operation(self, tracked_operator, operation_tracker):
        """Test that batch_operation tracks with BATCH_OPERATION type."""
        operations = [
            {"type": "add_node", "node_id": "n1"},
            {"type": "add_edge", "edge_id": "e1"},
        ]
        result = tracked_operator.batch_operation(
            canvas_path="test.canvas",
            operations=operations,
            agent_id="bulk-agent",
        )

        assert result["success"] is True
        history = operation_tracker.get_history("test.canvas")
        assert len(history) == 1
        assert history[0].type == OperationType.BATCH_OPERATION

    def test_passthrough_read_operations(self, tracked_operator, mock_canvas_service):
        """Test that read operations pass through without tracking."""
        # These should not create any history entries
        tracked_operator.get_node("test.canvas", "node1")
        tracked_operator.get_edge("test.canvas", "edge1")
        tracked_operator.get_canvas_data("test.canvas")

        mock_canvas_service.get_node.assert_called_once()
        mock_canvas_service.get_edge.assert_called_once()
        mock_canvas_service.get_canvas_data.assert_called_once()

    def test_operation_includes_metadata(self, tracked_operator, operation_tracker):
        """Test that operations include agent_id and request_id."""
        tracked_operator.add_node(
            canvas_path="test.canvas",
            node_data={"text": "Test"},
            agent_id="test-agent",
            request_id="req-999",
        )

        history = operation_tracker.get_history("test.canvas")
        op = history[0]
        assert op.metadata.agent_id == "test-agent"
        assert op.metadata.request_id == "req-999"
        assert "Add node" in op.metadata.description


# ═══════════════════════════════════════════════════════════════════════════════
# Snapshot Model Tests (Story 18.2 preparation)
# ═══════════════════════════════════════════════════════════════════════════════


class TestSnapshotModel:
    """Test suite for Snapshot model (preparation for Story 18.2)."""

    def test_snapshot_type_enum(self):
        """Test SnapshotType enum values."""
        assert SnapshotType.AUTO.value == "auto"
        assert SnapshotType.MANUAL.value == "manual"
        assert SnapshotType.CHECKPOINT.value == "checkpoint"

    def test_create_snapshot(self):
        """Test creating a Snapshot instance."""
        snapshot = Snapshot(
            id="snap-001",
            canvas_path="test.canvas",
            timestamp=datetime.now(timezone.utc),
            type=SnapshotType.MANUAL,
            canvas_data={"nodes": [], "edges": []},
            last_operation_id="op-001",
            metadata=SnapshotMetadata(
                description="Manual snapshot",
                created_by="user",
                tags=["backup"],
                size_bytes=1024,
            ),
        )
        assert snapshot.id == "snap-001"
        assert snapshot.type == SnapshotType.MANUAL
        assert snapshot.metadata.tags == ["backup"]

    def test_snapshot_to_dict(self):
        """Test Snapshot serialization."""
        snapshot = Snapshot(
            id="snap-002",
            canvas_path="test.canvas",
            timestamp=datetime.now(timezone.utc),
            type=SnapshotType.AUTO,
            canvas_data={"nodes": [{"id": "n1"}], "edges": []},
        )
        result = snapshot.to_dict()
        assert result["id"] == "snap-002"
        assert result["type"] == "auto"
        assert result["canvas_data"]["nodes"][0]["id"] == "n1"

    def test_snapshot_from_dict(self):
        """Test Snapshot deserialization."""
        snapshot_dict = {
            "id": "snap-003",
            "canvas_path": "restore.canvas",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "checkpoint",
            "canvas_data": {"nodes": [], "edges": []},
            "last_operation_id": "op-last",
            "metadata": {"description": "Before rollback"},
        }
        snapshot = Snapshot.from_dict(snapshot_dict)
        assert snapshot.id == "snap-003"
        assert snapshot.type == SnapshotType.CHECKPOINT
        assert snapshot.last_operation_id == "op-last"
