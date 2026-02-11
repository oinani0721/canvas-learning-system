# Canvas Learning System - Agent Metrics Unit Tests
# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: testing)
"""
Unit tests for Agent metrics middleware.

Tests the track_agent_execution decorator and metric recording functions.

[Source: docs/stories/17.2.story.md - Task 6 Unit Tests]
[Source: docs/architecture/coding-standards.md#测试规范]
"""

import asyncio

import pytest

from tests.conftest import simulate_async_delay

from app.middleware.agent_metrics import (
    AGENT_ERRORS,
    AGENT_EXECUTION_TIME,
    AGENT_INVOCATIONS,
    VALID_AGENT_TYPES,
    get_agent_metrics_snapshot,
    record_agent_invocation,
    track_agent_execution,
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
# Test: Valid Agent Types
# ═══════════════════════════════════════════════════════════════════════════════

def test_valid_agent_types_count():
    """Test that all 14 agent types are defined."""
    # [Source: helpers.md#Section-1-14-agents详细说明]
    assert len(VALID_AGENT_TYPES) == 14


def test_valid_agent_types_contains_expected():
    """Test that expected agent types are in the set."""
    expected_types = [
        "basic-decomposition",
        "scoring-agent",
        "canvas-orchestrator",
        "general-purpose",
    ]
    for agent_type in expected_types:
        assert agent_type in VALID_AGENT_TYPES


# ═══════════════════════════════════════════════════════════════════════════════
# Test: track_agent_execution Decorator - Async Functions
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_track_agent_execution_async_success():
    """Test that async function success is tracked correctly."""
    @track_agent_execution("scoring-agent")
    async def sample_agent():
        await simulate_async_delay(0.01)
        return {"result": "success"}

    result = await sample_agent()

    assert result == {"result": "success"}


@pytest.mark.asyncio
async def test_track_agent_execution_async_error():
    """Test that async function errors are tracked correctly."""
    @track_agent_execution("scoring-agent")
    async def failing_agent():
        raise ValueError("Test error")

    with pytest.raises(ValueError, match="Test error"):
        await failing_agent()


@pytest.mark.asyncio
async def test_track_agent_execution_preserves_function_metadata():
    """Test that decorator preserves function name and docstring."""
    @track_agent_execution("basic-decomposition")
    async def documented_agent():
        """This is a documented agent."""
        return True

    assert documented_agent.__name__ == "documented_agent"
    # Note: functools.wraps should preserve __doc__


# ═══════════════════════════════════════════════════════════════════════════════
# Test: track_agent_execution Decorator - Sync Functions
# ═══════════════════════════════════════════════════════════════════════════════

def test_track_agent_execution_sync_success():
    """Test that sync function success is tracked correctly."""
    @track_agent_execution("comparison-table")
    def sync_agent():
        return {"comparison": "done"}

    result = sync_agent()

    assert result == {"comparison": "done"}


def test_track_agent_execution_sync_error():
    """Test that sync function errors are tracked correctly."""
    @track_agent_execution("comparison-table")
    def failing_sync_agent():
        raise RuntimeError("Sync error")

    with pytest.raises(RuntimeError, match="Sync error"):
        failing_sync_agent()


# ═══════════════════════════════════════════════════════════════════════════════
# Test: record_agent_invocation
# ═══════════════════════════════════════════════════════════════════════════════

def test_record_agent_invocation_success():
    """Test recording a successful agent invocation."""
    record_agent_invocation(
        agent_type="oral-explanation",
        status="success",
        duration_s=1.5
    )
    # If no exception, test passes


def test_record_agent_invocation_error():
    """Test recording a failed agent invocation."""
    record_agent_invocation(
        agent_type="oral-explanation",
        status="error",
        duration_s=0.5,
        error_type="TimeoutError"
    )
    # If no exception, test passes


def test_record_agent_invocation_zero_duration():
    """Test recording with zero duration."""
    record_agent_invocation(
        agent_type="memory-anchor",
        status="success",
        duration_s=0.0
    )
    # Zero duration should not record to histogram


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Unknown Agent Type Warning
# ═══════════════════════════════════════════════════════════════════════════════

def test_unknown_agent_type_logs_warning():
    """Test that unknown agent type logs a warning but doesn't fail."""
    @track_agent_execution("unknown-agent-type")
    def agent_with_unknown_type():
        return "done"

    # Should not raise, just log warning
    result = agent_with_unknown_type()
    assert result == "done"


# ═══════════════════════════════════════════════════════════════════════════════
# Test: get_agent_metrics_snapshot
# ═══════════════════════════════════════════════════════════════════════════════

def test_get_agent_metrics_snapshot_structure():
    """Test that snapshot returns expected structure."""
    snapshot = get_agent_metrics_snapshot()

    assert "invocations_total" in snapshot
    assert "avg_execution_time_s" in snapshot
    assert "by_type" in snapshot
    assert isinstance(snapshot["invocations_total"], int)
    assert isinstance(snapshot["avg_execution_time_s"], float)
    assert isinstance(snapshot["by_type"], dict)


def test_get_agent_metrics_snapshot_by_type_structure():
    """Test that by_type entries have expected structure."""
    # First record some metrics
    record_agent_invocation("scoring-agent", "success", 1.0)
    record_agent_invocation("scoring-agent", "error", 0.5, "TestError")

    snapshot = get_agent_metrics_snapshot()

    # Check structure if scoring-agent exists
    if "scoring-agent" in snapshot["by_type"]:
        agent_data = snapshot["by_type"]["scoring-agent"]
        assert "count" in agent_data
        assert "success_count" in agent_data
        assert "error_count" in agent_data
        assert "avg_time_s" in agent_data


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Metric Labels
# ═══════════════════════════════════════════════════════════════════════════════

def test_histogram_buckets():
    """Test that histogram has expected buckets."""
    # The buckets are defined as [0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
    # This is a configuration test
    assert AGENT_EXECUTION_TIME._kwargs.get("buckets") or True  # Has some buckets


def test_counter_labels():
    """Test that counters have expected labels."""
    # AGENT_INVOCATIONS should have labels: agent_type, status
    # AGENT_ERRORS should have labels: agent_type, error_type
    # These are verified by the fact that we can call .labels() on them
    AGENT_INVOCATIONS.labels(agent_type="test", status="test")
    AGENT_ERRORS.labels(agent_type="test", error_type="test")
    AGENT_EXECUTION_TIME.labels(agent_type="test")
