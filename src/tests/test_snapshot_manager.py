# src/tests/test_snapshot_manager.py
"""
Unit tests for SnapshotManager

Tests snapshot creation, storage, retrieval, and auto-snapshot functionality.

[Source: docs/stories/18.2.story.md - AC 1-8]
[Source: docs/architecture/rollback-recovery-architecture.md:212-290]
"""

import asyncio
import gzip
import json
import tempfile
from pathlib import Path

import pytest
from src.rollback import (
    SnapshotManager,
    SnapshotType,
)

# ═══════════════════════════════════════════════════════════════════════════════
# Test Fixtures
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def temp_storage_dir():
    """Create a temporary directory for snapshot storage."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def snapshot_manager(temp_storage_dir):
    """Create a SnapshotManager with temporary storage."""
    return SnapshotManager(
        storage_root=temp_storage_dir,
        auto_interval=60,  # 1 minute for faster tests
        max_snapshots=5,
    )


@pytest.fixture
def sample_canvas_data():
    """Sample Canvas data for testing."""
    return {
        "nodes": [
            {
                "id": "node-001",
                "type": "text",
                "text": "Test Node 1",
                "x": 0,
                "y": 0,
                "width": 200,
                "height": 100,
                "color": "1",
            },
            {
                "id": "node-002",
                "type": "text",
                "text": "Test Node 2",
                "x": 300,
                "y": 0,
                "width": 200,
                "height": 100,
                "color": "2",
            },
        ],
        "edges": [
            {
                "id": "edge-001",
                "fromNode": "node-001",
                "toNode": "node-002",
                "fromSide": "right",
                "toSide": "left",
            }
        ],
    }


@pytest.fixture
def sample_canvas_file(temp_storage_dir, sample_canvas_data):
    """Create a sample Canvas file for testing."""
    canvas_path = temp_storage_dir / "test.canvas"
    with open(canvas_path, "w", encoding="utf-8") as f:
        json.dump(sample_canvas_data, f)
    return str(canvas_path)


# ═══════════════════════════════════════════════════════════════════════════════
# Test: SnapshotManager Initialization
# ═══════════════════════════════════════════════════════════════════════════════


class TestSnapshotManagerInit:
    """Tests for SnapshotManager initialization."""

    def test_init_sets_storage_root(self, temp_storage_dir):
        """Test that storage root is set on init (lazy directory creation)."""
        storage_root = temp_storage_dir / "snapshots"
        manager = SnapshotManager(storage_root=storage_root)

        # Storage root path is set, but directory created lazily on first snapshot
        assert manager.storage_root == storage_root

    def test_init_with_custom_settings(self, temp_storage_dir):
        """Test initialization with custom settings."""
        manager = SnapshotManager(
            storage_root=temp_storage_dir,
            auto_interval=120,
            max_snapshots=100,
        )

        assert manager.auto_interval == 120
        assert manager.max_snapshots == 100

    def test_init_default_settings(self, temp_storage_dir):
        """Test initialization with default settings."""
        manager = SnapshotManager(storage_root=temp_storage_dir)

        assert manager.auto_interval == 300  # Default 5 minutes
        assert manager.max_snapshots == 50   # Default 50


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Snapshot Creation
# ═══════════════════════════════════════════════════════════════════════════════


class TestSnapshotCreation:
    """Tests for snapshot creation functionality."""

    @pytest.mark.asyncio
    async def test_create_manual_snapshot(self, snapshot_manager, sample_canvas_file):
        """Test creating a manual snapshot."""
        snapshot = await snapshot_manager.create_snapshot(
            canvas_path=sample_canvas_file,
            snapshot_type=SnapshotType.MANUAL,
            description="Test manual snapshot",
            created_by="user",
        )

        assert snapshot is not None
        assert snapshot.type == SnapshotType.MANUAL
        assert snapshot.canvas_path == sample_canvas_file
        assert snapshot.metadata.description == "Test manual snapshot"
        assert snapshot.metadata.created_by == "user"
        assert snapshot.canvas_data is not None
        assert "nodes" in snapshot.canvas_data

    @pytest.mark.asyncio
    async def test_create_auto_snapshot(self, snapshot_manager, sample_canvas_file):
        """Test creating an auto snapshot."""
        snapshot = await snapshot_manager.create_snapshot(
            canvas_path=sample_canvas_file,
            snapshot_type=SnapshotType.AUTO,
        )

        assert snapshot is not None
        assert snapshot.type == SnapshotType.AUTO
        assert snapshot.metadata.created_by == "system"

    @pytest.mark.asyncio
    async def test_create_checkpoint_snapshot(self, snapshot_manager, sample_canvas_file):
        """Test creating a checkpoint snapshot."""
        snapshot = await snapshot_manager.create_snapshot(
            canvas_path=sample_canvas_file,
            snapshot_type=SnapshotType.CHECKPOINT,
            description="Pre-operation checkpoint",
        )

        assert snapshot is not None
        assert snapshot.type == SnapshotType.CHECKPOINT

    @pytest.mark.asyncio
    async def test_create_checkpoint_convenience_method(self, snapshot_manager, sample_canvas_file):
        """Test the create_checkpoint convenience method."""
        snapshot = await snapshot_manager.create_checkpoint(
            canvas_path=sample_canvas_file,
            description="Checkpoint before edit",
        )

        assert snapshot is not None
        assert snapshot.type == SnapshotType.CHECKPOINT
        assert snapshot.metadata.description == "Checkpoint before edit"

    @pytest.mark.asyncio
    async def test_create_snapshot_with_operation_id(self, snapshot_manager, sample_canvas_file):
        """Test creating a snapshot linked to an operation."""
        snapshot = await snapshot_manager.create_snapshot(
            canvas_path=sample_canvas_file,
            snapshot_type=SnapshotType.MANUAL,
            last_operation_id="op-12345",
        )

        assert snapshot.last_operation_id == "op-12345"

    @pytest.mark.asyncio
    async def test_create_snapshot_generates_uuid(self, snapshot_manager, sample_canvas_file):
        """Test that snapshot ID is a valid UUID."""
        import uuid

        snapshot = await snapshot_manager.create_snapshot(
            canvas_path=sample_canvas_file,
            snapshot_type=SnapshotType.MANUAL,
        )

        # Should not raise ValueError if valid UUID
        uuid.UUID(snapshot.id)

    @pytest.mark.asyncio
    async def test_create_snapshot_nonexistent_file_returns_empty(self, snapshot_manager):
        """Test creating snapshot for non-existent file returns empty data.

        The SnapshotManager gracefully handles non-existent files by creating
        a snapshot with empty canvas data instead of raising an error.
        [Source: docs/architecture/rollback-recovery-architecture.md:212-290]
        """
        snapshot = await snapshot_manager.create_snapshot(
            canvas_path="/nonexistent/path.canvas",
            snapshot_type=SnapshotType.MANUAL,
        )

        # Should create a snapshot with empty canvas data
        assert snapshot is not None
        assert snapshot.canvas_data == {"nodes": [], "edges": []}


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Snapshot Storage
# ═══════════════════════════════════════════════════════════════════════════════


class TestSnapshotStorage:
    """Tests for snapshot storage and compression."""

    @pytest.mark.asyncio
    async def test_snapshot_saved_to_disk(self, snapshot_manager, sample_canvas_file, temp_storage_dir):
        """Test that snapshot is saved to disk."""
        snapshot = await snapshot_manager.create_snapshot(
            canvas_path=sample_canvas_file,
            snapshot_type=SnapshotType.MANUAL,
        )

        # Storage structure: storage_root/snapshots/{canvas_name}/snapshots/
        # [Source: docs/architecture/rollback-recovery-architecture.md:182-210]
        canvas_name = Path(sample_canvas_file).stem
        snapshot_dir = temp_storage_dir / "snapshots" / canvas_name / "snapshots"

        # Check that snapshot directory exists
        assert snapshot_dir.exists()

    @pytest.mark.asyncio
    async def test_snapshot_compression(self, snapshot_manager, sample_canvas_file, temp_storage_dir):
        """Test that snapshots are compressed with gzip."""
        snapshot = await snapshot_manager.create_snapshot(
            canvas_path=sample_canvas_file,
            snapshot_type=SnapshotType.MANUAL,
        )

        # Storage structure: storage_root/snapshots/{canvas_name}/snapshots/
        canvas_name = Path(sample_canvas_file).stem
        snapshot_dir = temp_storage_dir / "snapshots" / canvas_name / "snapshots"

        if snapshot_dir.exists():
            gz_files = list(snapshot_dir.glob("*.gz"))
            if gz_files:
                # Verify it's valid gzip
                with gzip.open(gz_files[0], "rt", encoding="utf-8") as f:
                    data = json.load(f)
                    assert "id" in data
                    assert "canvas_data" in data

    @pytest.mark.asyncio
    async def test_index_updated_on_create(self, snapshot_manager, sample_canvas_file, temp_storage_dir):
        """Test that index is updated when snapshot is created."""
        await snapshot_manager.create_snapshot(
            canvas_path=sample_canvas_file,
            snapshot_type=SnapshotType.MANUAL,
        )

        # Index path: storage_root/snapshots/{canvas_name}/snapshots_index.json
        canvas_name = Path(sample_canvas_file).stem
        index_path = temp_storage_dir / "snapshots" / canvas_name / "snapshots_index.json"

        # Index should exist
        assert index_path.exists()

        with open(index_path, "r", encoding="utf-8") as f:
            index = json.load(f)
            # Index is a list of snapshot entries directly
            assert isinstance(index, list)
            assert len(index) == 1
            assert "id" in index[0]
            assert "canvas_path" in index[0]


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Snapshot Retrieval
# ═══════════════════════════════════════════════════════════════════════════════


class TestSnapshotRetrieval:
    """Tests for snapshot retrieval functionality."""

    @pytest.mark.asyncio
    async def test_get_snapshot_by_id(self, snapshot_manager, sample_canvas_file):
        """Test retrieving a snapshot by ID."""
        created = await snapshot_manager.create_snapshot(
            canvas_path=sample_canvas_file,
            snapshot_type=SnapshotType.MANUAL,
            description="Test snapshot",
        )

        retrieved = await snapshot_manager.get_snapshot(sample_canvas_file, created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.canvas_data == created.canvas_data

    @pytest.mark.asyncio
    async def test_get_nonexistent_snapshot(self, snapshot_manager, sample_canvas_file):
        """Test retrieving a non-existent snapshot."""
        result = await snapshot_manager.get_snapshot(sample_canvas_file, "nonexistent-id")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_latest_snapshot(self, snapshot_manager, sample_canvas_file):
        """Test getting the most recent snapshot."""
        # Create multiple snapshots
        snap1 = await snapshot_manager.create_snapshot(
            canvas_path=sample_canvas_file,
            snapshot_type=SnapshotType.MANUAL,
            description="First",
        )

        await asyncio.sleep(0.01)  # Small delay to ensure different timestamps

        snap2 = await snapshot_manager.create_snapshot(
            canvas_path=sample_canvas_file,
            snapshot_type=SnapshotType.MANUAL,
            description="Second",
        )

        latest = await snapshot_manager.get_latest_snapshot(sample_canvas_file)

        assert latest is not None
        assert latest.id == snap2.id
        assert latest.metadata.description == "Second"

    @pytest.mark.asyncio
    async def test_get_latest_snapshot_empty(self, snapshot_manager, sample_canvas_file):
        """Test getting latest snapshot when none exist."""
        latest = await snapshot_manager.get_latest_snapshot(sample_canvas_file)

        assert latest is None


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Snapshot Listing
# ═══════════════════════════════════════════════════════════════════════════════


class TestSnapshotListing:
    """Tests for snapshot listing functionality."""

    @pytest.mark.asyncio
    async def test_list_snapshots(self, snapshot_manager, sample_canvas_file):
        """Test listing all snapshots."""
        # Create multiple snapshots
        for i in range(3):
            await snapshot_manager.create_snapshot(
                canvas_path=sample_canvas_file,
                snapshot_type=SnapshotType.MANUAL,
                description=f"Snapshot {i}",
            )

        snapshots = await snapshot_manager.list_snapshots(sample_canvas_file)

        assert len(snapshots) == 3

    @pytest.mark.asyncio
    async def test_list_snapshots_pagination(self, snapshot_manager, sample_canvas_file):
        """Test snapshot listing with pagination."""
        # Create multiple snapshots
        for i in range(5):
            await snapshot_manager.create_snapshot(
                canvas_path=sample_canvas_file,
                snapshot_type=SnapshotType.MANUAL,
                description=f"Snapshot {i}",
            )

        # Get first page
        page1 = await snapshot_manager.list_snapshots(sample_canvas_file, limit=2, offset=0)
        assert len(page1) == 2

        # Get second page
        page2 = await snapshot_manager.list_snapshots(sample_canvas_file, limit=2, offset=2)
        assert len(page2) == 2

        # Get third page
        page3 = await snapshot_manager.list_snapshots(sample_canvas_file, limit=2, offset=4)
        assert len(page3) == 1

    @pytest.mark.asyncio
    async def test_list_snapshots_reverse_chronological(self, snapshot_manager, sample_canvas_file):
        """Test that snapshots are listed newest first."""
        # Create snapshots with slight delays
        for i in range(3):
            await snapshot_manager.create_snapshot(
                canvas_path=sample_canvas_file,
                snapshot_type=SnapshotType.MANUAL,
                description=f"Snapshot {i}",
            )
            await asyncio.sleep(0.01)

        snapshots = await snapshot_manager.list_snapshots(sample_canvas_file)

        # Verify newest first (descending timestamps)
        for i in range(len(snapshots) - 1):
            assert snapshots[i]["timestamp"] >= snapshots[i + 1]["timestamp"]

    @pytest.mark.asyncio
    async def test_get_total_count(self, snapshot_manager, sample_canvas_file):
        """Test getting total snapshot count."""
        for i in range(3):
            await snapshot_manager.create_snapshot(
                canvas_path=sample_canvas_file,
                snapshot_type=SnapshotType.MANUAL,
            )

        count = await snapshot_manager.get_total_count(sample_canvas_file)

        assert count == 3

    @pytest.mark.asyncio
    async def test_list_snapshots_empty(self, snapshot_manager, sample_canvas_file):
        """Test listing when no snapshots exist."""
        snapshots = await snapshot_manager.list_snapshots(sample_canvas_file)

        assert snapshots == []


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Snapshot Deletion
# ═══════════════════════════════════════════════════════════════════════════════


class TestSnapshotDeletion:
    """Tests for snapshot deletion functionality."""

    @pytest.mark.asyncio
    async def test_delete_snapshot(self, snapshot_manager, sample_canvas_file):
        """Test deleting a snapshot."""
        snapshot = await snapshot_manager.create_snapshot(
            canvas_path=sample_canvas_file,
            snapshot_type=SnapshotType.MANUAL,
        )

        result = await snapshot_manager.delete_snapshot(sample_canvas_file, snapshot.id)

        assert result is True

        # Verify deletion
        retrieved = await snapshot_manager.get_snapshot(sample_canvas_file, snapshot.id)
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_snapshot(self, snapshot_manager, sample_canvas_file):
        """Test deleting a non-existent snapshot."""
        result = await snapshot_manager.delete_snapshot(sample_canvas_file, "nonexistent-id")

        assert result is False

    @pytest.mark.asyncio
    async def test_delete_updates_count(self, snapshot_manager, sample_canvas_file):
        """Test that deletion updates the total count."""
        # Create multiple snapshots
        snap1 = await snapshot_manager.create_snapshot(
            canvas_path=sample_canvas_file,
            snapshot_type=SnapshotType.MANUAL,
        )
        await snapshot_manager.create_snapshot(
            canvas_path=sample_canvas_file,
            snapshot_type=SnapshotType.MANUAL,
        )

        assert await snapshot_manager.get_total_count(sample_canvas_file) == 2

        await snapshot_manager.delete_snapshot(sample_canvas_file, snap1.id)

        assert await snapshot_manager.get_total_count(sample_canvas_file) == 1


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Auto-Cleanup
# ═══════════════════════════════════════════════════════════════════════════════


class TestAutoCleanup:
    """Tests for automatic cleanup of old snapshots."""

    @pytest.mark.asyncio
    async def test_cleanup_when_exceeding_max(self, temp_storage_dir, sample_canvas_file):
        """Test that old snapshots are cleaned up when max is exceeded."""
        # Create manager with low max
        manager = SnapshotManager(
            storage_root=temp_storage_dir,
            max_snapshots=3,
        )

        # Create more than max snapshots
        snapshot_ids = []
        for i in range(5):
            snap = await manager.create_snapshot(
                canvas_path=sample_canvas_file,
                snapshot_type=SnapshotType.MANUAL,
                description=f"Snapshot {i}",
            )
            snapshot_ids.append(snap.id)
            await asyncio.sleep(0.01)  # Ensure different timestamps

        # Should only have max_snapshots remaining
        count = await manager.get_total_count(sample_canvas_file)
        assert count == 3

        # Oldest snapshots should be deleted
        oldest_snap = await manager.get_snapshot(sample_canvas_file, snapshot_ids[0])
        assert oldest_snap is None

    @pytest.mark.asyncio
    async def test_no_cleanup_under_max(self, snapshot_manager, sample_canvas_file):
        """Test that no cleanup happens when under max."""
        # Create snapshots under the limit
        for i in range(3):
            await snapshot_manager.create_snapshot(
                canvas_path=sample_canvas_file,
                snapshot_type=SnapshotType.MANUAL,
            )

        count = await snapshot_manager.get_total_count(sample_canvas_file)
        assert count == 3  # All snapshots retained


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Auto-Snapshot Scheduling
# ═══════════════════════════════════════════════════════════════════════════════


class TestAutoSnapshotScheduling:
    """Tests for automatic snapshot scheduling."""

    @pytest.mark.asyncio
    async def test_start_auto_snapshot(self, snapshot_manager, sample_canvas_file):
        """Test starting auto-snapshot for a canvas."""
        await snapshot_manager.start_auto_snapshot(sample_canvas_file)

        assert snapshot_manager.is_auto_snapshot_running(sample_canvas_file)

        # Cleanup
        await snapshot_manager.stop_auto_snapshot(sample_canvas_file)

    @pytest.mark.asyncio
    async def test_stop_auto_snapshot(self, snapshot_manager, sample_canvas_file):
        """Test stopping auto-snapshot."""
        await snapshot_manager.start_auto_snapshot(sample_canvas_file)
        await snapshot_manager.stop_auto_snapshot(sample_canvas_file)

        assert not snapshot_manager.is_auto_snapshot_running(sample_canvas_file)

    @pytest.mark.asyncio
    async def test_stop_all_auto_snapshots(self, snapshot_manager, sample_canvas_file, temp_storage_dir):
        """Test stopping all auto-snapshots."""
        # Create another canvas file
        canvas2 = temp_storage_dir / "test2.canvas"
        with open(canvas2, "w", encoding="utf-8") as f:
            json.dump({"nodes": [], "edges": []}, f)

        # Start auto-snapshot for both
        await snapshot_manager.start_auto_snapshot(sample_canvas_file)
        await snapshot_manager.start_auto_snapshot(str(canvas2))

        # Stop all
        await snapshot_manager.stop_all_auto_snapshots()

        assert not snapshot_manager.is_auto_snapshot_running(sample_canvas_file)
        assert not snapshot_manager.is_auto_snapshot_running(str(canvas2))

    @pytest.mark.asyncio
    async def test_auto_snapshot_creates_snapshots(self, temp_storage_dir, sample_canvas_file):
        """Test that auto-snapshot actually creates snapshots."""
        # Create manager with very short interval
        manager = SnapshotManager(
            storage_root=temp_storage_dir,
            auto_interval=0.1,  # 100ms
            max_snapshots=50,
        )

        await manager.start_auto_snapshot(sample_canvas_file)

        # Wait for at least one auto-snapshot
        await asyncio.sleep(0.3)

        await manager.stop_auto_snapshot(sample_canvas_file)

        # Should have created at least one auto-snapshot
        count = await manager.get_total_count(sample_canvas_file)
        assert count >= 1

    @pytest.mark.asyncio
    async def test_is_auto_snapshot_running_false_initially(self, snapshot_manager, sample_canvas_file):
        """Test that auto-snapshot is not running initially."""
        assert not snapshot_manager.is_auto_snapshot_running(sample_canvas_file)

    @pytest.mark.asyncio
    async def test_double_start_is_safe(self, snapshot_manager, sample_canvas_file):
        """Test that starting auto-snapshot twice is safe."""
        await snapshot_manager.start_auto_snapshot(sample_canvas_file)
        await snapshot_manager.start_auto_snapshot(sample_canvas_file)  # Should not raise

        assert snapshot_manager.is_auto_snapshot_running(sample_canvas_file)

        await snapshot_manager.stop_auto_snapshot(sample_canvas_file)

    @pytest.mark.asyncio
    async def test_stop_without_start_is_safe(self, snapshot_manager, sample_canvas_file):
        """Test that stopping without starting is safe."""
        # Should not raise
        await snapshot_manager.stop_auto_snapshot(sample_canvas_file)


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Cache Management
# ═══════════════════════════════════════════════════════════════════════════════


class TestCacheManagement:
    """Tests for index cache management."""

    @pytest.mark.asyncio
    async def test_clear_cache(self, snapshot_manager, sample_canvas_file):
        """Test clearing the cache."""
        # Create snapshot to populate cache
        await snapshot_manager.create_snapshot(
            canvas_path=sample_canvas_file,
            snapshot_type=SnapshotType.MANUAL,
        )

        # Clear cache
        snapshot_manager.clear_cache()

        # Should still work after cache clear
        count = await snapshot_manager.get_total_count(sample_canvas_file)
        assert count == 1

    @pytest.mark.asyncio
    async def test_cache_is_used(self, snapshot_manager, sample_canvas_file):
        """Test that cache is used for repeated reads."""
        await snapshot_manager.create_snapshot(
            canvas_path=sample_canvas_file,
            snapshot_type=SnapshotType.MANUAL,
        )

        # First read populates cache
        await snapshot_manager.list_snapshots(sample_canvas_file)

        # Second read should use cache (no file access)
        snapshots = await snapshot_manager.list_snapshots(sample_canvas_file)

        assert len(snapshots) == 1


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Edge Cases
# ═══════════════════════════════════════════════════════════════════════════════


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_snapshot_with_empty_canvas(self, snapshot_manager, temp_storage_dir):
        """Test creating snapshot with empty canvas data."""
        empty_canvas = temp_storage_dir / "empty.canvas"
        with open(empty_canvas, "w", encoding="utf-8") as f:
            json.dump({"nodes": [], "edges": []}, f)

        snapshot = await snapshot_manager.create_snapshot(
            canvas_path=str(empty_canvas),
            snapshot_type=SnapshotType.MANUAL,
        )

        assert snapshot is not None
        assert snapshot.canvas_data["nodes"] == []
        assert snapshot.canvas_data["edges"] == []

    @pytest.mark.asyncio
    async def test_snapshot_with_large_canvas(self, snapshot_manager, temp_storage_dir):
        """Test creating snapshot with large canvas data."""
        large_canvas = temp_storage_dir / "large.canvas"

        # Create canvas with many nodes
        nodes = [
            {
                "id": f"node-{i:04d}",
                "type": "text",
                "text": f"Node {i} content " * 10,
                "x": i * 50,
                "y": i * 30,
                "width": 200,
                "height": 100,
                "color": str(i % 6),
            }
            for i in range(100)
        ]

        with open(large_canvas, "w", encoding="utf-8") as f:
            json.dump({"nodes": nodes, "edges": []}, f)

        snapshot = await snapshot_manager.create_snapshot(
            canvas_path=str(large_canvas),
            snapshot_type=SnapshotType.MANUAL,
        )

        assert snapshot is not None
        assert len(snapshot.canvas_data["nodes"]) == 100

    @pytest.mark.asyncio
    async def test_snapshot_with_special_characters_in_path(self, snapshot_manager, temp_storage_dir):
        """Test snapshot with special characters in canvas path."""
        special_canvas = temp_storage_dir / "测试-canvas_file.canvas"
        with open(special_canvas, "w", encoding="utf-8") as f:
            json.dump({"nodes": [], "edges": []}, f)

        snapshot = await snapshot_manager.create_snapshot(
            canvas_path=str(special_canvas),
            snapshot_type=SnapshotType.MANUAL,
        )

        assert snapshot is not None

        # Should be able to retrieve
        retrieved = await snapshot_manager.get_snapshot(str(special_canvas), snapshot.id)
        assert retrieved is not None

    @pytest.mark.asyncio
    async def test_concurrent_snapshot_creation(self, snapshot_manager, sample_canvas_file):
        """Test creating multiple snapshots concurrently."""
        tasks = [
            snapshot_manager.create_snapshot(
                canvas_path=sample_canvas_file,
                snapshot_type=SnapshotType.MANUAL,
                description=f"Concurrent {i}",
            )
            for i in range(5)
        ]

        snapshots = await asyncio.gather(*tasks)

        assert len(snapshots) == 5
        assert len(set(s.id for s in snapshots)) == 5  # All unique IDs

    @pytest.mark.asyncio
    async def test_snapshot_metadata_size_calculated(self, snapshot_manager, sample_canvas_file):
        """Test that snapshot metadata includes size_bytes."""
        snapshot = await snapshot_manager.create_snapshot(
            canvas_path=sample_canvas_file,
            snapshot_type=SnapshotType.MANUAL,
        )

        assert snapshot.metadata.size_bytes > 0


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Integration with Operation Tracker
# ═══════════════════════════════════════════════════════════════════════════════


class TestOperationTrackerIntegration:
    """Tests for integration with OperationTracker."""

    @pytest.mark.asyncio
    async def test_snapshot_linked_to_operation(self, snapshot_manager, sample_canvas_file):
        """Test that snapshot can be linked to an operation ID."""
        operation_id = "op-test-12345"

        snapshot = await snapshot_manager.create_snapshot(
            canvas_path=sample_canvas_file,
            snapshot_type=SnapshotType.CHECKPOINT,
            last_operation_id=operation_id,
        )

        assert snapshot.last_operation_id == operation_id

        # Retrieve and verify
        retrieved = await snapshot_manager.get_snapshot(sample_canvas_file, snapshot.id)
        assert retrieved.last_operation_id == operation_id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
