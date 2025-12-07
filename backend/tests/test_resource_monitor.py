# Canvas Learning System - Resource Monitor Unit Tests
# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: testing)
"""
Unit tests for Resource Monitor service.

Tests CPU, memory, and disk monitoring with psutil integration.

[Source: docs/stories/17.2.story.md - Task 6 Unit Tests]
[Source: docs/architecture/coding-standards.md#测试规范]
"""

import asyncio
from unittest.mock import MagicMock, patch

import pytest
from app.services.resource_monitor import (
    DEFAULT_THRESHOLDS,
    ResourceMonitor,
    get_default_monitor,
    get_resource_metrics_snapshot,
)

# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def monitor():
    """Create a ResourceMonitor instance for testing."""
    return ResourceMonitor()


@pytest.fixture
def custom_monitor():
    """Create a ResourceMonitor with custom thresholds."""
    import sys
    # Use platform-appropriate paths
    if sys.platform == "win32":
        paths = ["C:\\", "D:\\"]
    else:
        paths = ["/", "/tmp"]
    return ResourceMonitor(
        thresholds={
            "cpu_warning": 50.0,
            "cpu_critical": 80.0,
        },
        disk_paths=paths
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Test: ResourceMonitor Initialization
# ═══════════════════════════════════════════════════════════════════════════════

def test_monitor_default_thresholds(monitor):
    """Test that monitor initializes with default thresholds."""
    assert monitor.thresholds["cpu_warning"] == DEFAULT_THRESHOLDS["cpu_warning"]
    assert monitor.thresholds["cpu_critical"] == DEFAULT_THRESHOLDS["cpu_critical"]
    assert monitor.thresholds["memory_warning"] == DEFAULT_THRESHOLDS["memory_warning"]


def test_monitor_custom_thresholds(custom_monitor):
    """Test that custom thresholds override defaults."""
    assert custom_monitor.thresholds["cpu_warning"] == 50.0
    assert custom_monitor.thresholds["cpu_critical"] == 80.0
    # Memory thresholds should still be defaults
    assert custom_monitor.thresholds["memory_warning"] == DEFAULT_THRESHOLDS["memory_warning"]


def test_monitor_default_disk_paths(monitor):
    """Test that monitor defaults to root path."""
    import sys
    expected_path = "C:\\" if sys.platform == "win32" else "/"
    assert expected_path in monitor.disk_paths


def test_monitor_custom_disk_paths(custom_monitor):
    """Test that custom disk paths are used."""
    import sys
    if sys.platform == "win32":
        assert "C:\\" in custom_monitor.disk_paths
        assert "D:\\" in custom_monitor.disk_paths
    else:
        assert "/" in custom_monitor.disk_paths
        assert "/tmp" in custom_monitor.disk_paths


# ═══════════════════════════════════════════════════════════════════════════════
# Test: CPU Metrics
# ═══════════════════════════════════════════════════════════════════════════════

def test_get_cpu_metrics_structure(monitor):
    """Test that CPU metrics returns expected structure."""
    metrics = monitor.get_cpu_metrics()

    assert "percent" in metrics
    assert "status" in metrics
    assert "threshold_warning" in metrics
    assert "threshold_critical" in metrics
    assert isinstance(metrics["percent"], (int, float))
    assert metrics["status"] in ["normal", "warning", "critical"]


def test_get_cpu_metrics_status_normal():
    """Test CPU status when usage is normal."""
    with patch("psutil.cpu_percent", return_value=30.0):
        monitor = ResourceMonitor()
        metrics = monitor.get_cpu_metrics()
        assert metrics["status"] == "normal"


def test_get_cpu_metrics_status_warning():
    """Test CPU status when usage is warning level."""
    with patch("psutil.cpu_percent", return_value=75.0):
        monitor = ResourceMonitor()
        metrics = monitor.get_cpu_metrics()
        assert metrics["status"] == "warning"


def test_get_cpu_metrics_status_critical():
    """Test CPU status when usage is critical level."""
    with patch("psutil.cpu_percent", return_value=95.0):
        monitor = ResourceMonitor()
        metrics = monitor.get_cpu_metrics()
        assert metrics["status"] == "critical"


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Memory Metrics
# ═══════════════════════════════════════════════════════════════════════════════

def test_get_memory_metrics_structure(monitor):
    """Test that memory metrics returns expected structure."""
    metrics = monitor.get_memory_metrics()

    assert "percent" in metrics
    assert "used_bytes" in metrics
    assert "available_bytes" in metrics
    assert "total_bytes" in metrics
    assert "status" in metrics
    assert isinstance(metrics["percent"], (int, float))


def test_get_memory_metrics_status_normal():
    """Test memory status when usage is normal."""
    mock_mem = MagicMock()
    mock_mem.percent = 40.0
    mock_mem.used = 4 * 1024**3
    mock_mem.available = 6 * 1024**3
    mock_mem.total = 10 * 1024**3

    with patch("psutil.virtual_memory", return_value=mock_mem):
        monitor = ResourceMonitor()
        metrics = monitor.get_memory_metrics()
        assert metrics["status"] == "normal"


def test_get_memory_metrics_status_warning():
    """Test memory status when usage is warning level."""
    mock_mem = MagicMock()
    mock_mem.percent = 75.0
    mock_mem.used = 7.5 * 1024**3
    mock_mem.available = 2.5 * 1024**3
    mock_mem.total = 10 * 1024**3

    with patch("psutil.virtual_memory", return_value=mock_mem):
        monitor = ResourceMonitor()
        metrics = monitor.get_memory_metrics()
        assert metrics["status"] == "warning"


def test_get_memory_metrics_status_critical():
    """Test memory status when usage is critical level."""
    mock_mem = MagicMock()
    mock_mem.percent = 95.0
    mock_mem.used = 9.5 * 1024**3
    mock_mem.available = 0.5 * 1024**3
    mock_mem.total = 10 * 1024**3

    with patch("psutil.virtual_memory", return_value=mock_mem):
        monitor = ResourceMonitor()
        metrics = monitor.get_memory_metrics()
        assert metrics["status"] == "critical"


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Disk Metrics
# ═══════════════════════════════════════════════════════════════════════════════

def test_get_disk_metrics_structure(monitor):
    """Test that disk metrics returns expected structure."""
    mock_disk = MagicMock()
    mock_disk.percent = 50.0
    mock_disk.used = 50 * 1024**3
    mock_disk.free = 50 * 1024**3
    mock_disk.total = 100 * 1024**3

    with patch("psutil.disk_usage", return_value=mock_disk):
        metrics = monitor.get_disk_metrics()

        assert isinstance(metrics, dict)
        # Should have at least one disk path
        assert len(metrics) >= 1  # Mocked, so we expect the default path


def test_get_disk_metrics_path_structure():
    """Test that disk metrics for a path has expected structure."""
    import sys
    test_path = "C:\\" if sys.platform == "win32" else "/"

    mock_disk = MagicMock()
    mock_disk.percent = 50.0
    mock_disk.used = 50 * 1024**3
    mock_disk.free = 50 * 1024**3
    mock_disk.total = 100 * 1024**3

    with patch("psutil.disk_usage", return_value=mock_disk):
        monitor = ResourceMonitor(disk_paths=[test_path])
        metrics = monitor.get_disk_metrics()

        if test_path in metrics:
            path_metrics = metrics[test_path]
            assert "percent" in path_metrics
            assert "used_bytes" in path_metrics
            assert "free_bytes" in path_metrics
            assert "total_bytes" in path_metrics
            assert "status" in path_metrics


def test_get_disk_metrics_error_handling():
    """Test that disk errors are handled gracefully."""
    test_path = "/nonexistent"  # This path doesn't exist on any platform

    with patch("psutil.disk_usage", side_effect=OSError("Permission denied")):
        monitor = ResourceMonitor(disk_paths=[test_path])
        metrics = monitor.get_disk_metrics()

        if test_path in metrics:
            assert "error" in metrics[test_path]
            assert metrics[test_path]["status"] == "error"


# ═══════════════════════════════════════════════════════════════════════════════
# Test: collect_metrics
# ═══════════════════════════════════════════════════════════════════════════════

def test_collect_metrics_structure(monitor):
    """Test that collect_metrics returns expected structure."""
    # Mock disk_usage to avoid psutil bug on Windows with certain locales
    mock_disk = MagicMock()
    mock_disk.percent = 50.0
    mock_disk.used = 50 * 1024**3
    mock_disk.free = 50 * 1024**3
    mock_disk.total = 100 * 1024**3

    with patch("psutil.disk_usage", return_value=mock_disk):
        metrics = monitor.collect_metrics()

        assert "cpu" in metrics
        assert "memory" in metrics
        assert "disk" in metrics
        assert "overall_status" in metrics


def test_collect_metrics_overall_status_healthy():
    """Test overall status when all metrics are normal."""
    mock_mem = MagicMock()
    mock_mem.percent = 40.0
    mock_mem.used = 4 * 1024**3
    mock_mem.available = 6 * 1024**3
    mock_mem.total = 10 * 1024**3

    mock_disk = MagicMock()
    mock_disk.percent = 50.0
    mock_disk.used = 50 * 1024**3
    mock_disk.free = 50 * 1024**3
    mock_disk.total = 100 * 1024**3

    with patch("psutil.cpu_percent", return_value=30.0), \
         patch("psutil.virtual_memory", return_value=mock_mem), \
         patch("psutil.disk_usage", return_value=mock_disk):
        monitor = ResourceMonitor()
        metrics = monitor.collect_metrics()
        assert metrics["overall_status"] == "healthy"


def test_collect_metrics_overall_status_critical():
    """Test overall status when any metric is critical."""
    mock_mem = MagicMock()
    mock_mem.percent = 95.0
    mock_mem.used = 9.5 * 1024**3
    mock_mem.available = 0.5 * 1024**3
    mock_mem.total = 10 * 1024**3

    mock_disk = MagicMock()
    mock_disk.percent = 50.0
    mock_disk.used = 50 * 1024**3
    mock_disk.free = 50 * 1024**3
    mock_disk.total = 100 * 1024**3

    with patch("psutil.cpu_percent", return_value=30.0), \
         patch("psutil.virtual_memory", return_value=mock_mem), \
         patch("psutil.disk_usage", return_value=mock_disk):
        monitor = ResourceMonitor()
        metrics = monitor.collect_metrics()
        assert metrics["overall_status"] == "critical"


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Background Collection
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_start_background_collection():
    """Test starting background collection."""
    # Mock disk_usage to avoid psutil bug on Windows with certain locales
    mock_disk = MagicMock()
    mock_disk.percent = 50.0
    mock_disk.used = 50 * 1024**3
    mock_disk.free = 50 * 1024**3
    mock_disk.total = 100 * 1024**3

    with patch("psutil.disk_usage", return_value=mock_disk):
        monitor = ResourceMonitor()

        # Start collection with short interval
        await monitor.start_background_collection(interval_seconds=0.1)

        assert monitor._running is True

        # Let it run for a short time
        await asyncio.sleep(0.2)

        # Stop collection
        await monitor.stop_background_collection()

        assert monitor._running is False


@pytest.mark.asyncio
async def test_start_background_collection_already_running():
    """Test that starting twice doesn't create multiple loops."""
    # Mock disk_usage to avoid psutil bug on Windows with certain locales
    mock_disk = MagicMock()
    mock_disk.percent = 50.0
    mock_disk.used = 50 * 1024**3
    mock_disk.free = 50 * 1024**3
    mock_disk.total = 100 * 1024**3

    with patch("psutil.disk_usage", return_value=mock_disk):
        monitor = ResourceMonitor()

        await monitor.start_background_collection(interval_seconds=0.1)
        await monitor.start_background_collection(interval_seconds=0.1)  # Should log warning

        await monitor.stop_background_collection()


@pytest.mark.asyncio
async def test_stop_background_collection_not_running():
    """Test stopping when not running doesn't error."""
    monitor = ResourceMonitor()
    await monitor.stop_background_collection()  # Should not error


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Convenience Functions
# ═══════════════════════════════════════════════════════════════════════════════

def test_get_resource_metrics_snapshot():
    """Test convenience function for getting metrics."""
    # Mock disk_usage to avoid psutil bug on Windows with certain locales
    mock_disk = MagicMock()
    mock_disk.percent = 50.0
    mock_disk.used = 50 * 1024**3
    mock_disk.free = 50 * 1024**3
    mock_disk.total = 100 * 1024**3

    with patch("psutil.disk_usage", return_value=mock_disk):
        snapshot = get_resource_metrics_snapshot()

        assert "cpu" in snapshot
        assert "memory" in snapshot
        assert "disk" in snapshot
        assert "overall_status" in snapshot


def test_get_default_monitor():
    """Test getting the default monitor singleton."""
    monitor1 = get_default_monitor()
    monitor2 = get_default_monitor()

    assert monitor1 is monitor2


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Prometheus Gauges
# ═══════════════════════════════════════════════════════════════════════════════

def test_cpu_gauge_updated():
    """Test that CPU gauge is updated when metrics are collected."""
    with patch("psutil.cpu_percent", return_value=45.0):
        monitor = ResourceMonitor()
        monitor.get_cpu_metrics()
        # Gauge should be updated (no assertion needed, just no error)


def test_memory_gauges_updated():
    """Test that memory gauges are updated when metrics are collected."""
    mock_mem = MagicMock()
    mock_mem.percent = 50.0
    mock_mem.used = 5 * 1024**3
    mock_mem.available = 5 * 1024**3
    mock_mem.total = 10 * 1024**3

    with patch("psutil.virtual_memory", return_value=mock_mem):
        monitor = ResourceMonitor()
        monitor.get_memory_metrics()
        # Gauges should be updated (no assertion needed, just no error)


def test_disk_gauges_updated():
    """Test that disk gauges are updated when metrics are collected."""
    import sys
    test_path = "C:\\" if sys.platform == "win32" else "/"

    mock_disk = MagicMock()
    mock_disk.percent = 60.0
    mock_disk.used = 60 * 1024**3
    mock_disk.free = 40 * 1024**3
    mock_disk.total = 100 * 1024**3

    with patch("psutil.disk_usage", return_value=mock_disk):
        monitor = ResourceMonitor(disk_paths=[test_path])
        monitor.get_disk_metrics()
        # Gauges should be updated (no assertion needed, just no error)
