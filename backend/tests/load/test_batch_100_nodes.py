# Canvas Learning System - 100-Node Batch Load Test
# NFR Evidence: EPIC-33 Core Requirement Validation
"""
Load test for BatchOrchestrator with 100 nodes.

Validates EPIC-33 NFR requirements:
- 100 nodes processed within acceptable time
- p95 per-node latency < 2s
- Peak memory usage < 2GB
- Semaphore(12) concurrency works correctly

Uses mock AgentService (simulates 50-200ms per node) to isolate
orchestrator performance from AI API latency.
"""

import asyncio
import statistics
import time
import tracemalloc
from dataclasses import dataclass
from typing import List
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.session_models import SessionStatus
from app.services.batch_orchestrator import (
    BatchOrchestrator,
    GroupConfig,
)
from app.services.session_manager import SessionManager


# ═══════════════════════════════════════════════════════════════════════════════
# Test Configuration
# ═══════════════════════════════════════════════════════════════════════════════

NODE_COUNT = 100
GROUPS = 5  # 5 groups of 20 nodes each
NODES_PER_GROUP = NODE_COUNT // GROUPS
SIMULATED_AGENT_DELAY_MS = 100  # 100ms simulated agent call
MAX_CONCURRENT = 12  # Default semaphore size
P95_THRESHOLD_MS = 2000  # 2s per node maximum
MEMORY_THRESHOLD_MB = 2048  # 2GB maximum


@dataclass
class LoadTestResults:
    """Results from the 100-node load test."""
    total_duration_s: float
    node_durations_ms: List[float]
    p50_ms: float
    p95_ms: float
    p99_ms: float
    avg_ms: float
    peak_concurrent: int
    success_count: int
    failure_count: int
    peak_memory_mb: float
    throughput_nodes_per_sec: float


# ═══════════════════════════════════════════════════════════════════════════════
# Mock Agent Service
# ═══════════════════════════════════════════════════════════════════════════════

def create_mock_agent_service(delay_ms: int = SIMULATED_AGENT_DELAY_MS):
    """Create a mock AgentService that simulates processing delay."""
    mock = AsyncMock()

    async def mock_call_agent(agent_type: str, prompt: str, **kwargs):
        """Simulate agent processing with configurable delay."""
        await asyncio.sleep(delay_ms / 1000.0)
        result = MagicMock()
        result.success = True
        result.content = f"Mock result for {agent_type}"
        result.file_path = f"/mock/output/{agent_type}.md"
        return result

    mock.call_agent = mock_call_agent
    return mock


# ═══════════════════════════════════════════════════════════════════════════════
# Test Fixtures
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(autouse=True)
def reset_session_manager_singleton():
    """Reset SessionManager singleton before each test to avoid state leakage."""
    SessionManager.reset_instance()
    yield
    SessionManager.reset_instance()


@pytest.fixture
def session_manager():
    """Create a fresh SessionManager for load testing."""
    return SessionManager()


@pytest.fixture
def mock_agent_service():
    """Create mock agent service with simulated delay."""
    return create_mock_agent_service()


@pytest.fixture
def orchestrator(session_manager, mock_agent_service):
    """Create BatchOrchestrator with mock dependencies."""
    return BatchOrchestrator(
        session_manager=session_manager,
        agent_service=mock_agent_service,
        max_concurrent=MAX_CONCURRENT,
    )


def make_groups(num_groups: int = GROUPS, nodes_per_group: int = NODES_PER_GROUP) -> List[GroupConfig]:
    """Generate test group configurations."""
    groups = []
    for g in range(num_groups):
        node_ids = [f"node-{g * nodes_per_group + n}" for n in range(nodes_per_group)]
        groups.append(GroupConfig(
            group_id=f"group-{g}",
            agent_type="basic-decomposition",
            node_ids=node_ids,
        ))
    return groups


# ═══════════════════════════════════════════════════════════════════════════════
# Load Test
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_100_node_batch_performance(orchestrator, session_manager):
    """
    NFR Load Test: 100 nodes processed with acceptable performance.

    Validates:
    - Total completion time is reasonable
    - p95 per-node latency < 2s threshold
    - Peak concurrent stays within Semaphore(12) limit
    - All 100 nodes complete successfully
    """
    # Create session
    session_id = await session_manager.create_session(
        canvas_path="test/load-test.canvas",
        node_count=NODE_COUNT,
        metadata={"test": "100-node-load-test"},
    )

    groups = make_groups()

    # Start memory tracking
    tracemalloc.start()
    baseline_memory = tracemalloc.get_traced_memory()[1]

    # Execute batch
    start_time = time.perf_counter()

    result = await orchestrator.start_batch_session(
        session_id=session_id,
        canvas_path="test/load-test.canvas",
        groups=groups,
        timeout=300,  # 5 minute timeout
    )

    total_duration = time.perf_counter() - start_time

    # Get peak memory
    _, peak_memory = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    peak_memory_mb = (peak_memory - baseline_memory) / (1024 * 1024)

    # Extract results from the actual result dict structure
    success_count = result.get("completed_nodes", 0)
    failure_count = result.get("failed_nodes", 0)
    peak_concurrent = result.get("performance_metrics", {}).get("peak_concurrent", 0)

    # Get per-node execution times from session node_results
    session = await session_manager.get_session(session_id)
    node_durations = []
    for node_id, nr in session.node_results.items():
        if nr.execution_time_ms is not None:
            node_durations.append(float(nr.execution_time_ms))

    # Calculate statistics
    if node_durations:
        node_durations.sort()
        p50 = statistics.median(node_durations)
        p95_idx = int(len(node_durations) * 0.95)
        p95 = node_durations[min(p95_idx, len(node_durations) - 1)]
        p99_idx = int(len(node_durations) * 0.99)
        p99 = node_durations[min(p99_idx, len(node_durations) - 1)]
        avg = statistics.mean(node_durations)
    else:
        p50 = p95 = p99 = avg = 0.0

    throughput = NODE_COUNT / total_duration if total_duration > 0 else 0

    results = LoadTestResults(
        total_duration_s=total_duration,
        node_durations_ms=node_durations,
        p50_ms=p50,
        p95_ms=p95,
        p99_ms=p99,
        avg_ms=avg,
        peak_concurrent=peak_concurrent,
        success_count=success_count,
        failure_count=failure_count,
        peak_memory_mb=peak_memory_mb,
        throughput_nodes_per_sec=throughput,
    )

    # ═══════════════════════════════════════════════════════════════════════
    # Print Results (for NFR evidence)
    # ═══════════════════════════════════════════════════════════════════════
    print("\n" + "=" * 70)
    print("  EPIC-33 NFR LOAD TEST RESULTS: 100-Node Batch")
    print("=" * 70)
    print(f"  Total Duration:      {results.total_duration_s:.2f}s")
    print(f"  Throughput:          {results.throughput_nodes_per_sec:.1f} nodes/sec")
    print(f"  Avg per-node:        {results.avg_ms:.1f}ms")
    print(f"  p50 per-node:        {results.p50_ms:.1f}ms")
    print(f"  p95 per-node:        {results.p95_ms:.1f}ms")
    print(f"  p99 per-node:        {results.p99_ms:.1f}ms")
    print(f"  Peak Concurrent:     {results.peak_concurrent}")
    print(f"  Success/Fail:        {results.success_count}/{results.failure_count}")
    print(f"  Peak Memory Delta:   {results.peak_memory_mb:.2f}MB")
    print("=" * 70)

    # ═══════════════════════════════════════════════════════════════════════
    # Assertions (NFR thresholds)
    # ═══════════════════════════════════════════════════════════════════════

    # All nodes must complete
    assert success_count == NODE_COUNT, (
        f"Expected {NODE_COUNT} successful nodes, got {success_count}"
    )
    assert failure_count == 0, f"Expected 0 failures, got {failure_count}"

    # p95 per-node latency < 2s
    assert results.p95_ms < P95_THRESHOLD_MS, (
        f"p95 latency {results.p95_ms:.1f}ms exceeds {P95_THRESHOLD_MS}ms threshold"
    )

    # Peak concurrent should not exceed semaphore limit
    assert results.peak_concurrent <= MAX_CONCURRENT, (
        f"Peak concurrent {results.peak_concurrent} exceeds "
        f"semaphore limit {MAX_CONCURRENT}"
    )

    # Memory usage should be reasonable
    assert results.peak_memory_mb < MEMORY_THRESHOLD_MB, (
        f"Peak memory delta {results.peak_memory_mb:.2f}MB exceeds "
        f"{MEMORY_THRESHOLD_MB}MB threshold"
    )

    # Verify session state
    assert session.status in (SessionStatus.COMPLETED, SessionStatus.PARTIAL_FAILURE), (
        f"Expected COMPLETED status, got {session.status}"
    )


@pytest.mark.asyncio
async def test_100_node_batch_with_partial_failures(session_manager):
    """
    NFR Load Test: 100 nodes with 10% simulated failures.

    Validates:
    - Partial failures don't crash the batch
    - Healthy nodes still complete
    - Final status is PARTIAL_FAILURE
    """
    call_count = 0

    async def flaky_call_agent(agent_type: str, prompt: str, **kwargs):
        nonlocal call_count
        call_count += 1
        await asyncio.sleep(0.05)  # 50ms

        # Fail every 10th call (10% failure rate)
        if call_count % 10 == 0:
            result = MagicMock()
            result.success = False
            result.content = None
            result.file_path = None
            result.error = "Simulated failure"
            return result

        result = MagicMock()
        result.success = True
        result.content = f"Result {call_count}"
        result.file_path = f"/mock/{call_count}.md"
        return result

    mock_agent = MagicMock()
    mock_agent.call_agent = flaky_call_agent

    orchestrator = BatchOrchestrator(
        session_manager=session_manager,
        agent_service=mock_agent,
        max_concurrent=MAX_CONCURRENT,
    )

    session_id = await session_manager.create_session(
        canvas_path="test/flaky-test.canvas",
        node_count=NODE_COUNT,
    )

    groups = make_groups()

    start_time = time.perf_counter()
    result = await orchestrator.start_batch_session(
        session_id=session_id,
        canvas_path="test/flaky-test.canvas",
        groups=groups,
        timeout=120,
    )
    duration = time.perf_counter() - start_time

    # Extract counts from actual result dict
    success = result.get("completed_nodes", 0)
    failed = result.get("failed_nodes", 0)

    print(f"\n  Partial Failure Test: {success} success, {failed} failed in {duration:.2f}s")

    # At least 80% should succeed (10% failure rate → ~90 success)
    assert success >= 80, f"Too many failures: only {success}/{NODE_COUNT} succeeded"
    assert failed >= 1, "Expected at least some failures in flaky test"

    # Session should be PARTIAL_FAILURE
    session = await session_manager.get_session(session_id)
    assert session.status == SessionStatus.PARTIAL_FAILURE, (
        f"Expected PARTIAL_FAILURE, got {session.status}"
    )


@pytest.mark.asyncio
async def test_concurrent_sessions_isolation(session_manager, mock_agent_service):
    """
    NFR Load Test: Two concurrent 50-node sessions don't interfere.

    Validates:
    - Session isolation under concurrent load
    - Semaphore is respected across sessions
    """
    orchestrator = BatchOrchestrator(
        session_manager=session_manager,
        agent_service=mock_agent_service,
        max_concurrent=MAX_CONCURRENT,
    )

    # Create two sessions
    sid1 = await session_manager.create_session("test/s1.canvas", 50)
    sid2 = await session_manager.create_session("test/s2.canvas", 50)

    groups1 = [GroupConfig(
        group_id=f"s1-g{i}",
        agent_type="basic-decomposition",
        node_ids=[f"s1-node-{i * 10 + j}" for j in range(10)],
    ) for i in range(5)]

    groups2 = [GroupConfig(
        group_id=f"s2-g{i}",
        agent_type="oral-explanation",
        node_ids=[f"s2-node-{i * 10 + j}" for j in range(10)],
    ) for i in range(5)]

    start = time.perf_counter()

    # Run both sessions concurrently
    r1, r2 = await asyncio.gather(
        orchestrator.start_batch_session(sid1, "test/s1.canvas", groups1, timeout=120),
        orchestrator.start_batch_session(sid2, "test/s2.canvas", groups2, timeout=120),
    )

    duration = time.perf_counter() - start

    # Both sessions should complete
    s1 = await session_manager.get_session(sid1)
    s2 = await session_manager.get_session(sid2)

    # Get peak_concurrent from whichever result captured a higher value
    # Note: _peak_concurrent is reset in _aggregate_results, so the last
    # session to complete will have its value. We check both results.
    peak1 = r1.get("performance_metrics", {}).get("peak_concurrent", 0)
    peak2 = r2.get("performance_metrics", {}).get("peak_concurrent", 0)
    observed_peak = max(peak1, peak2)

    print(f"\n  Concurrent Sessions: completed in {duration:.2f}s")
    print(f"  Session 1: {s1.status.value} ({r1.get('completed_nodes', 0)} nodes)")
    print(f"  Session 2: {s2.status.value} ({r2.get('completed_nodes', 0)} nodes)")
    print(f"  Peak concurrent (max of both): {observed_peak}")

    assert s1.status == SessionStatus.COMPLETED
    assert s2.status == SessionStatus.COMPLETED
    assert observed_peak <= MAX_CONCURRENT
