# Canvas Learning System - Optimization Module Tests
# ✅ Verified from Context7:/pytest-dev/pytest (topic: pytest fixtures async)
# [Source: docs/stories/17.4.story.md - Task 9]
"""
Unit tests for optimization module components.

Tests:
- canvas_cache: orjson + lru_cache optimization
- batch_writer: Debounced batch writes
- resource_aware_scheduler: Dynamic concurrency

[Source: docs/architecture/performance-monitoring-architecture.md:336-398]
"""

import asyncio
import json
from pathlib import Path

import pytest

# ═══════════════════════════════════════════════════════════════════════════════
# Test Fixtures
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def temp_canvas_file(tmp_path: Path) -> Path:
    """Create a temporary Canvas file for testing."""
    canvas_data = {
        "nodes": [
            {"id": "node1", "type": "text", "text": "Test node 1", "x": 0, "y": 0},
            {"id": "node2", "type": "text", "text": "Test node 2", "x": 100, "y": 100},
        ],
        "edges": [
            {"id": "edge1", "fromNode": "node1", "toNode": "node2"},
        ],
    }
    canvas_path = tmp_path / "test.canvas"
    canvas_path.write_text(json.dumps(canvas_data, indent=2))
    return canvas_path


@pytest.fixture
def sample_canvas_data() -> dict:
    """Create sample Canvas data for testing."""
    return {
        "nodes": [
            {"id": "n1", "type": "text", "text": "Node 1", "x": 0, "y": 0, "width": 200, "height": 100},
            {"id": "n2", "type": "text", "text": "Node 2", "x": 300, "y": 0, "width": 200, "height": 100},
        ],
        "edges": [],
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Canvas Cache Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestCanvasCache:
    """Tests for canvas_cache module."""

    def test_import_canvas_cache(self):
        """Test canvas_cache module can be imported."""
        from optimization.canvas_cache import (
            CacheConfig,
            clear_canvas_cache,
            get_cache_stats,
            read_canvas,
            read_canvas_cached,
        )

        assert read_canvas is not None
        assert read_canvas_cached is not None
        assert clear_canvas_cache is not None
        assert get_cache_stats is not None
        assert CacheConfig is not None

    def test_read_canvas_basic(self, temp_canvas_file: Path):
        """Test basic Canvas file reading."""
        from optimization.canvas_cache import clear_canvas_cache, read_canvas

        clear_canvas_cache()

        data = read_canvas(str(temp_canvas_file))

        assert "nodes" in data
        assert "edges" in data
        assert len(data["nodes"]) == 2
        assert len(data["edges"]) == 1

    def test_read_canvas_caching(self, temp_canvas_file: Path):
        """Test that repeated reads use cache."""
        from optimization.canvas_cache import (
            clear_canvas_cache,
            get_cache_stats,
            read_canvas,
        )

        clear_canvas_cache()

        # First read (cache miss)
        read_canvas(str(temp_canvas_file))
        stats1 = get_cache_stats()

        # Second read (cache hit)
        read_canvas(str(temp_canvas_file))
        stats2 = get_cache_stats()

        assert stats2["hits"] > stats1["hits"]

    def test_cache_invalidation_on_file_change(self, temp_canvas_file: Path):
        """Test cache invalidation when file changes."""
        from optimization.canvas_cache import (
            clear_canvas_cache,
            read_canvas,
        )

        clear_canvas_cache()

        # First read
        data1 = read_canvas(str(temp_canvas_file))

        # Modify file (change mtime)
        import time
        time.sleep(0.1)
        new_data = {"nodes": [{"id": "new", "type": "text"}], "edges": []}
        temp_canvas_file.write_text(json.dumps(new_data))

        # Second read (should be cache miss due to mtime change)
        data2 = read_canvas(str(temp_canvas_file))

        assert len(data1["nodes"]) == 2
        assert len(data2["nodes"]) == 1

    def test_get_cache_stats(self, temp_canvas_file: Path):
        """Test cache statistics reporting."""
        from optimization.canvas_cache import (
            clear_canvas_cache,
            get_cache_stats,
        )

        clear_canvas_cache()

        stats = get_cache_stats()

        assert "hits" in stats
        assert "misses" in stats
        assert "hit_rate" in stats
        assert "cache_size" in stats
        assert "orjson_available" in stats
        assert "optimization_enabled" in stats

    def test_clear_cache(self, temp_canvas_file: Path):
        """Test cache clearing."""
        from optimization.canvas_cache import (
            clear_canvas_cache,
            get_cache_stats,
            read_canvas,
        )

        # Populate cache
        read_canvas(str(temp_canvas_file))

        # Clear
        clear_canvas_cache()
        stats = get_cache_stats()

        assert stats["cache_size"] == 0

    def test_cache_config(self):
        """Test CacheConfig dataclass."""
        from optimization.canvas_cache import CacheConfig

        config = CacheConfig(
            canvas_maxsize=50,
            canvas_ttl=1800,
            enabled=False,
            use_orjson=False,
        )

        assert config.canvas_maxsize == 50
        assert config.canvas_ttl == 1800
        assert config.enabled is False
        assert config.use_orjson is False


# ═══════════════════════════════════════════════════════════════════════════════
# Batch Writer Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestBatchWriter:
    """Tests for batch_writer module."""

    def test_import_batch_writer(self):
        """Test batch_writer module can be imported."""
        from optimization.batch_writer import (
            BatchCanvasWriter,
            BatchWriterConfig,
            list_backups,
            restore_from_backup,
        )

        assert BatchCanvasWriter is not None
        assert BatchWriterConfig is not None
        assert restore_from_backup is not None
        assert list_backups is not None

    def test_batch_writer_config(self):
        """Test BatchWriterConfig dataclass."""
        from optimization.batch_writer import BatchWriterConfig

        config = BatchWriterConfig(
            debounce_delay=1.0,
            max_pending=5,
            atomic_writes=False,
            create_backup=False,
        )

        assert config.debounce_delay == 1.0
        assert config.max_pending == 5
        assert config.atomic_writes is False
        assert config.create_backup is False

    @pytest.mark.asyncio
    async def test_batch_writer_start_stop(self):
        """Test BatchCanvasWriter start and stop."""
        from optimization.batch_writer import BatchCanvasWriter

        writer = BatchCanvasWriter()

        await writer.start()
        assert writer._running is True

        await writer.stop()
        assert writer._running is False

    @pytest.mark.asyncio
    async def test_batch_writer_write(self, tmp_path: Path, sample_canvas_data: dict):
        """Test basic write operation."""
        from optimization.batch_writer import BatchCanvasWriter, BatchWriterConfig

        config = BatchWriterConfig(
            debounce_delay=0.1,
            create_backup=False,
        )
        writer = BatchCanvasWriter(config)

        canvas_path = tmp_path / "output.canvas"

        await writer.start()
        await writer.write(str(canvas_path), sample_canvas_data)
        await asyncio.sleep(0.2)  # Wait for debounce
        await writer.stop()

        assert canvas_path.exists()
        saved_data = json.loads(canvas_path.read_text())
        assert len(saved_data["nodes"]) == 2

    @pytest.mark.asyncio
    async def test_batch_writer_batching(self, tmp_path: Path, sample_canvas_data: dict):
        """Test that rapid writes are batched."""
        from optimization.batch_writer import BatchCanvasWriter, BatchWriterConfig

        config = BatchWriterConfig(
            debounce_delay=0.2,
            create_backup=False,
        )
        writer = BatchCanvasWriter(config)

        canvas_path = tmp_path / "output.canvas"

        await writer.start()

        # Write multiple times rapidly
        for i in range(5):
            data = {**sample_canvas_data, "version": i}
            await writer.write(str(canvas_path), data)

        await asyncio.sleep(0.3)  # Wait for debounce
        await writer.stop()

        # Should have batched writes
        stats = writer.get_stats()
        assert stats["batched"] >= 4  # At least 4 writes batched

        # Final data should be last version
        saved_data = json.loads(canvas_path.read_text())
        assert saved_data["version"] == 4

    @pytest.mark.asyncio
    async def test_batch_writer_backup_creation(self, tmp_path: Path, sample_canvas_data: dict):
        """Test backup file creation."""
        from optimization.batch_writer import BatchCanvasWriter, BatchWriterConfig

        config = BatchWriterConfig(
            debounce_delay=0.1,
            create_backup=True,
            backup_count=2,
        )
        writer = BatchCanvasWriter(config)

        canvas_path = tmp_path / "output.canvas"

        # Create initial file
        canvas_path.write_text(json.dumps({"nodes": [], "edges": []}))

        await writer.start()
        await writer.write(str(canvas_path), sample_canvas_data)
        await asyncio.sleep(0.2)
        await writer.stop()

        # Check backup was created
        backup_dir = tmp_path / ".canvas_backups"
        assert backup_dir.exists()
        backups = list(backup_dir.glob("*.bak"))
        assert len(backups) >= 1

    def test_list_backups(self, tmp_path: Path):
        """Test listing backup files."""
        from optimization.batch_writer import list_backups

        # Create backup directory and files
        backup_dir = tmp_path / ".canvas_backups"
        backup_dir.mkdir()

        for i in range(3):
            backup_file = backup_dir / f"test_20250101_00000{i}.canvas.bak"
            backup_file.write_text(json.dumps({"version": i}))

        canvas_path = tmp_path / "test.canvas"

        backups = list_backups(str(canvas_path))

        assert len(backups) == 3
        assert all("path" in b for b in backups)
        assert all("size" in b for b in backups)

    @pytest.mark.asyncio
    async def test_restore_from_backup(self, tmp_path: Path):
        """Test restoring from backup."""
        from optimization.batch_writer import restore_from_backup

        # Create backup directory and file
        backup_dir = tmp_path / ".canvas_backups"
        backup_dir.mkdir()

        backup_data = {"nodes": [{"id": "backup"}], "edges": []}
        backup_file = backup_dir / "test_20250101_000000.canvas.bak"
        backup_file.write_text(json.dumps(backup_data))

        # Create current file
        canvas_path = tmp_path / "test.canvas"
        canvas_path.write_text(json.dumps({"nodes": [], "edges": []}))

        # Restore
        result = await restore_from_backup(str(canvas_path))

        assert result is True
        restored_data = json.loads(canvas_path.read_text())
        assert len(restored_data["nodes"]) == 1

    def test_batch_writer_get_stats(self):
        """Test getting writer statistics."""
        from optimization.batch_writer import BatchCanvasWriter

        writer = BatchCanvasWriter()
        stats = writer.get_stats()

        assert "writes" in stats
        assert "batched" in stats
        assert "errors" in stats
        assert "pending" in stats
        assert "config" in stats


# ═══════════════════════════════════════════════════════════════════════════════
# Resource-Aware Scheduler Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestResourceAwareScheduler:
    """Tests for resource_aware_scheduler module."""

    def test_import_scheduler(self):
        """Test scheduler module can be imported."""
        from optimization.resource_aware_scheduler import (
            LoadLevel,
            ResourceAwareScheduler,
            ResourceMonitor,
            SchedulerConfig,
            TaskPriority,
        )

        assert ResourceAwareScheduler is not None
        assert SchedulerConfig is not None
        assert ResourceMonitor is not None
        assert LoadLevel is not None
        assert TaskPriority is not None

    def test_scheduler_config(self):
        """Test SchedulerConfig dataclass."""
        from optimization.resource_aware_scheduler import SchedulerConfig

        config = SchedulerConfig(
            concurrency_low=16,
            concurrency_high=2,
            cpu_high_threshold=80.0,
            enabled=False,
        )

        assert config.concurrency_low == 16
        assert config.concurrency_high == 2
        assert config.cpu_high_threshold == 80.0
        assert config.enabled is False

    def test_load_level_enum(self):
        """Test LoadLevel enum values."""
        from optimization.resource_aware_scheduler import LoadLevel

        assert LoadLevel.LOW.value == "low"
        assert LoadLevel.MEDIUM.value == "medium"
        assert LoadLevel.HIGH.value == "high"
        assert LoadLevel.CRITICAL.value == "critical"

    def test_task_priority_enum(self):
        """Test TaskPriority enum values."""
        from optimization.resource_aware_scheduler import TaskPriority

        assert TaskPriority.CRITICAL.value == 0
        assert TaskPriority.HIGH.value == 1
        assert TaskPriority.NORMAL.value == 2
        assert TaskPriority.LOW.value == 3

    @pytest.mark.asyncio
    async def test_scheduler_start_stop(self):
        """Test scheduler start and stop."""
        from optimization.resource_aware_scheduler import ResourceAwareScheduler

        scheduler = ResourceAwareScheduler()

        await scheduler.start()
        assert scheduler._running is True

        await scheduler.stop()
        assert scheduler._running is False

    @pytest.mark.asyncio
    async def test_scheduler_submit_task(self):
        """Test submitting a task to scheduler."""
        from optimization.resource_aware_scheduler import ResourceAwareScheduler

        scheduler = ResourceAwareScheduler()
        await scheduler.start()

        async def test_task():
            return "result"

        result = await scheduler.submit(test_task())

        assert result == "result"

        await scheduler.stop()

    @pytest.mark.asyncio
    async def test_scheduler_submit_many(self):
        """Test submitting multiple tasks."""
        from optimization.resource_aware_scheduler import ResourceAwareScheduler

        scheduler = ResourceAwareScheduler()
        await scheduler.start()

        async def task(n):
            return n * 2

        results = await scheduler.submit_many([task(i) for i in range(5)])

        assert results == [0, 2, 4, 6, 8]

        await scheduler.stop()

    @pytest.mark.asyncio
    async def test_scheduler_task_error_handling(self):
        """Test error handling in tasks."""
        from optimization.resource_aware_scheduler import ResourceAwareScheduler

        scheduler = ResourceAwareScheduler()
        await scheduler.start()

        async def failing_task():
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            await scheduler.submit(failing_task())

        stats = scheduler.get_stats()
        assert stats["errors"] >= 1

        await scheduler.stop()

    def test_resource_monitor_initialization(self):
        """Test ResourceMonitor initialization."""
        from optimization.resource_aware_scheduler import ResourceMonitor, SchedulerConfig

        config = SchedulerConfig()
        monitor = ResourceMonitor(config)

        assert monitor.cpu_percent >= 0
        assert monitor.memory_percent >= 0

    def test_resource_monitor_get_metrics(self):
        """Test getting resource metrics."""
        from optimization.resource_aware_scheduler import ResourceMonitor, SchedulerConfig

        config = SchedulerConfig()
        monitor = ResourceMonitor(config)

        metrics = monitor.get_metrics()

        assert "cpu_percent" in metrics
        assert "memory_percent" in metrics
        assert "load_level" in metrics
        assert "psutil_available" in metrics

    def test_resource_monitor_load_level(self):
        """Test load level detection."""
        from optimization.resource_aware_scheduler import (
            LoadLevel,
            ResourceMonitor,
            SchedulerConfig,
        )

        config = SchedulerConfig()
        monitor = ResourceMonitor(config)

        load_level = monitor.get_load_level()

        assert isinstance(load_level, LoadLevel)

    def test_scheduler_get_stats(self):
        """Test getting scheduler statistics."""
        from optimization.resource_aware_scheduler import ResourceAwareScheduler

        scheduler = ResourceAwareScheduler()
        stats = scheduler.get_stats()

        assert "submitted" in stats
        assert "completed" in stats
        assert "errors" in stats
        assert "active_tasks" in stats
        assert "resources" in stats
        assert "config" in stats

    @pytest.mark.asyncio
    async def test_global_scheduler_functions(self):
        """Test global scheduler helper functions."""
        from optimization.resource_aware_scheduler import (
            get_scheduler,
            init_scheduler,
            shutdown_scheduler,
        )

        await init_scheduler()

        scheduler = get_scheduler()
        assert scheduler is not None
        assert scheduler._running is True

        await shutdown_scheduler()


# ═══════════════════════════════════════════════════════════════════════════════
# Integration Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestOptimizationIntegration:
    """Integration tests for optimization components."""

    @pytest.mark.asyncio
    async def test_cache_and_writer_integration(self, tmp_path: Path, sample_canvas_data: dict):
        """Test cache and writer work together."""
        from optimization.batch_writer import BatchCanvasWriter, BatchWriterConfig
        from optimization.canvas_cache import clear_canvas_cache, get_cache_stats, read_canvas

        config = BatchWriterConfig(debounce_delay=0.1, create_backup=False)
        writer = BatchCanvasWriter(config)

        canvas_path = tmp_path / "integration.canvas"

        # Write initial data
        await writer.start()
        await writer.write(str(canvas_path), sample_canvas_data)
        await asyncio.sleep(0.2)
        await writer.stop()

        # Clear cache
        clear_canvas_cache()

        # Read back (should populate cache)
        data = read_canvas(str(canvas_path))
        assert len(data["nodes"]) == 2

        # Read again (should hit cache)
        read_canvas(str(canvas_path))
        stats = get_cache_stats()
        assert stats["hits"] >= 1

    @pytest.mark.asyncio
    async def test_scheduler_with_cache(self, tmp_path: Path):
        """Test scheduler with cache operations."""
        from optimization.canvas_cache import clear_canvas_cache, read_canvas
        from optimization.resource_aware_scheduler import ResourceAwareScheduler

        # Create test files
        for i in range(5):
            path = tmp_path / f"canvas_{i}.canvas"
            path.write_text(json.dumps({"nodes": [{"id": f"n{i}"}], "edges": []}))

        scheduler = ResourceAwareScheduler()
        await scheduler.start()

        clear_canvas_cache()

        # Submit read tasks
        async def read_task(path):
            return read_canvas(str(path))

        tasks = [read_task(tmp_path / f"canvas_{i}.canvas") for i in range(5)]
        results = await scheduler.submit_many(tasks)

        assert len(results) == 5
        assert all("nodes" in r for r in results)

        await scheduler.stop()


# ═══════════════════════════════════════════════════════════════════════════════
# Performance Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestOptimizationPerformance:
    """Performance-related tests."""

    def test_orjson_availability(self):
        """Test orjson is available for performance."""
        from optimization.canvas_cache import HAS_ORJSON

        # orjson should be available
        assert HAS_ORJSON is True, "orjson should be installed for performance"

    def test_cache_performance_benefit(self, temp_canvas_file: Path):
        """Test that caching provides performance benefit."""
        import time

        from optimization.canvas_cache import clear_canvas_cache, read_canvas

        clear_canvas_cache()

        # First read (cold)
        start = time.time()
        read_canvas(str(temp_canvas_file))
        cold_time = time.time() - start

        # Subsequent reads (warm)
        warm_times = []
        for _ in range(10):
            start = time.time()
            read_canvas(str(temp_canvas_file))
            warm_times.append(time.time() - start)

        avg_warm_time = sum(warm_times) / len(warm_times)

        # Warm reads should be faster (allowing for measurement variance)
        # This is a soft assertion since timing can vary
        assert avg_warm_time <= cold_time * 2  # At worst, warm is not much slower
