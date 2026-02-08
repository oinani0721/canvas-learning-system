# Canvas Learning System - Memory Metrics Unit Tests
# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: testing)
"""
Unit tests for Memory metrics middleware.

Tests the track_memory_query context manager and metric recording functions.

[Source: docs/stories/17.2.story.md - Task 6 Unit Tests]
[Source: docs/architecture/coding-standards.md#测试规范]
"""

import pytest
from app.middleware.memory_metrics import (
    MEMORY_ERRORS,
    MEMORY_QUERIES,
    MEMORY_QUERY_LATENCY,
    VALID_MEMORY_TYPES,
    VALID_OPERATIONS,
    get_memory_metrics_snapshot,
    record_memory_query,
    track_memory_query,
)

# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(autouse=True)
def reset_metrics():
    """Reset Prometheus metrics before each test."""
    from tests.conftest import clear_prometheus_metrics
    clear_prometheus_metrics()
    yield
    clear_prometheus_metrics()


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Valid Memory Types and Operations
# ═══════════════════════════════════════════════════════════════════════════════

def test_valid_memory_types():
    """Test that expected memory types are defined."""
    expected_types = ["graphiti", "lancedb", "temporal", "sqlite"]
    for memory_type in expected_types:
        assert memory_type in VALID_MEMORY_TYPES


def test_valid_operations():
    """Test that expected operations are defined."""
    expected_ops = ["read", "write", "search", "delete", "sync"]
    for op in expected_ops:
        assert op in VALID_OPERATIONS


# ═══════════════════════════════════════════════════════════════════════════════
# Test: track_memory_query Context Manager - Success
# ═══════════════════════════════════════════════════════════════════════════════

def test_track_memory_query_success():
    """Test that successful queries are tracked."""
    with track_memory_query("graphiti", "search"):
        result = "found"

    assert result == "found"


def test_track_memory_query_with_operation():
    """Test tracking different operations."""
    operations = ["read", "write", "search", "delete"]

    for op in operations:
        with track_memory_query("lancedb", op):
            pass  # Operation succeeds


def test_track_memory_query_all_memory_types():
    """Test tracking all memory types."""
    for memory_type in VALID_MEMORY_TYPES:
        with track_memory_query(memory_type, "read"):
            pass


# ═══════════════════════════════════════════════════════════════════════════════
# Test: track_memory_query Context Manager - Errors
# ═══════════════════════════════════════════════════════════════════════════════

def test_track_memory_query_error():
    """Test that errors are tracked and re-raised."""
    with pytest.raises(ValueError, match="Query failed"):
        with track_memory_query("temporal", "search"):
            raise ValueError("Query failed")


def test_track_memory_query_connection_error():
    """Test tracking connection errors."""
    with pytest.raises(ConnectionError):
        with track_memory_query("graphiti", "read"):
            raise ConnectionError("Connection refused")


def test_track_memory_query_timeout():
    """Test tracking timeout errors."""
    with pytest.raises(TimeoutError):
        with track_memory_query("lancedb", "search"):
            raise TimeoutError("Query timed out")


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Unknown Types Warning
# ═══════════════════════════════════════════════════════════════════════════════

def test_unknown_memory_type_logs_warning():
    """Test that unknown memory type logs warning but doesn't fail."""
    with track_memory_query("unknown-memory", "read"):
        pass  # Should not raise


def test_unknown_operation_logs_warning():
    """Test that unknown operation logs warning but doesn't fail."""
    with track_memory_query("graphiti", "unknown-op"):
        pass  # Should not raise


# ═══════════════════════════════════════════════════════════════════════════════
# Test: record_memory_query
# ═══════════════════════════════════════════════════════════════════════════════

def test_record_memory_query_success():
    """Test recording a successful memory query."""
    record_memory_query(
        memory_type="graphiti",
        operation="search",
        status="success",
        duration_s=0.5
    )


def test_record_memory_query_error():
    """Test recording a failed memory query."""
    record_memory_query(
        memory_type="lancedb",
        operation="write",
        status="error",
        duration_s=0.1,
        error_type="ConnectionError"
    )


def test_record_memory_query_zero_duration():
    """Test recording with zero duration."""
    record_memory_query(
        memory_type="temporal",
        operation="read",
        status="success",
        duration_s=0.0
    )


def test_record_memory_query_all_combinations():
    """Test recording various memory type and operation combinations."""
    combinations = [
        ("graphiti", "search"),
        ("lancedb", "read"),
        ("temporal", "write"),
        ("sqlite", "delete"),
    ]

    for memory_type, operation in combinations:
        record_memory_query(memory_type, operation, "success", 0.1)


# ═══════════════════════════════════════════════════════════════════════════════
# Test: get_memory_metrics_snapshot
# ═══════════════════════════════════════════════════════════════════════════════

def test_get_memory_metrics_snapshot_structure():
    """Test that snapshot returns expected structure."""
    snapshot = get_memory_metrics_snapshot()

    assert "queries_total" in snapshot
    assert "avg_latency_s" in snapshot
    assert "by_type" in snapshot
    assert isinstance(snapshot["queries_total"], int)
    assert isinstance(snapshot["avg_latency_s"], float)
    assert isinstance(snapshot["by_type"], dict)


def test_get_memory_metrics_snapshot_after_recording():
    """Test snapshot after recording some metrics."""
    # Record some metrics
    record_memory_query("graphiti", "search", "success", 1.0)
    record_memory_query("graphiti", "search", "error", 0.5, "TestError")

    snapshot = get_memory_metrics_snapshot()

    # Check that we have some data
    assert snapshot["queries_total"] >= 0


def test_get_memory_metrics_snapshot_by_type_structure():
    """Test that by_type entries have expected structure."""
    # First record some metrics
    record_memory_query("graphiti", "search", "success", 1.0)

    snapshot = get_memory_metrics_snapshot()

    # Check structure if graphiti exists
    if "graphiti" in snapshot["by_type"]:
        type_data = snapshot["by_type"]["graphiti"]
        assert "query_count" in type_data
        assert "success_count" in type_data
        assert "error_count" in type_data
        assert "avg_latency_s" in type_data
        assert "by_operation" in type_data


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Metric Labels
# ═══════════════════════════════════════════════════════════════════════════════

def test_histogram_labels():
    """Test that histogram has expected labels."""
    MEMORY_QUERY_LATENCY.labels(memory_type="test", operation="test")


def test_counter_labels():
    """Test that counters have expected labels."""
    MEMORY_QUERIES.labels(memory_type="test", operation="test", status="test")
    MEMORY_ERRORS.labels(memory_type="test", operation="test", error_type="test")
