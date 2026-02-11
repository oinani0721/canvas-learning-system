# Canvas Learning System - BatchOrchestrator Integration Tests
# Story 33.6: Batch Processing Orchestrator
# [Source: docs/stories/33.6.story.md#Task-9]
"""
Integration tests for BatchOrchestrator with real SessionManager.

Tests full workflow: session creation → groups → parallel execution → results
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.conftest import simulate_async_delay

from app.models.session_models import (
    SessionInfo,
    SessionStatus,
)
from app.services.batch_orchestrator import (
    BatchOrchestrator,
    GroupConfig,
    ProgressEvent,
    ProgressEventType,
)
from app.services.session_manager import (
    SessionManager,
    SessionNotFoundError,
    InMemoryStorageAdapter,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class MockAgentResult:
    """Mock agent result for testing."""
    success: bool = True
    content: str = "Generated content"
    file_path: Optional[str] = "output/test.md"
    error: Optional[str] = None


@pytest.fixture
def real_session_manager():
    """Create a real SessionManager with in-memory storage."""
    # Reset singleton for clean state
    SessionManager.reset_instance()
    manager = SessionManager(storage_adapter=InMemoryStorageAdapter())
    yield manager
    # Cleanup
    SessionManager.reset_instance()


## mock_agent_service: use shared fixture from conftest.py
## [Source: Story 31.A.10 AC-2 — Fixture deduplication]


@pytest.fixture
def progress_events():
    """Capture progress events during tests."""
    events: List[ProgressEvent] = []
    return events


@pytest.fixture
def progress_callback(progress_events):
    """Create a progress callback that captures events."""
    def callback(event: ProgressEvent):
        progress_events.append(event)
    return callback


@pytest.fixture
def sample_groups():
    """Create sample group configurations."""
    return [
        GroupConfig(
            group_id="group-1",
            agent_type="oral-explanation",
            node_ids=["node-001", "node-002", "node-003"],
        ),
        GroupConfig(
            group_id="group-2",
            agent_type="comparison-table",
            node_ids=["node-004", "node-005"],
        ),
    ]


# ═══════════════════════════════════════════════════════════════════════════════
# Integration Test: Full Workflow
# ═══════════════════════════════════════════════════════════════════════════════

class TestFullWorkflow:
    """Test complete batch processing workflow."""

    @pytest.mark.asyncio
    async def test_full_workflow_success(
        self,
        real_session_manager,
        mock_agent_service,
        progress_callback,
        progress_events,
        sample_groups,
    ):
        """Test complete successful workflow: session → execution → results."""
        # Step 1: Create session
        total_nodes = sum(len(g.node_ids) for g in sample_groups)
        session_id = await real_session_manager.create_session(
            canvas_path="test.canvas",
            node_count=total_nodes,
            metadata={"test": True},
        )

        # Verify session created in pending state
        session = await real_session_manager.get_session(session_id)
        assert session.status == SessionStatus.PENDING
        assert session.node_count == 5

        # Step 2: Create orchestrator and execute
        orchestrator = BatchOrchestrator(
            session_manager=real_session_manager,
            agent_service=mock_agent_service,
            progress_callback=progress_callback,
        )

        result = await orchestrator.start_batch_session(
            session_id=session_id,
            canvas_path="test.canvas",
            groups=sample_groups,
        )

        # Step 3: Verify results
        assert result["task_id"] == session_id
        assert result["completed_nodes"] == 5
        assert result["failed_nodes"] == 0
        assert result["status"] == "completed"

        # Step 4: Verify session final state
        final_session = await real_session_manager.get_session(session_id)
        assert final_session.status == SessionStatus.COMPLETED

        # Step 5: Verify progress events
        event_types = [e.event_type for e in progress_events]
        assert ProgressEventType.PROGRESS_UPDATE in event_types
        assert ProgressEventType.SESSION_COMPLETED in event_types

    @pytest.mark.asyncio
    async def test_full_workflow_partial_failure(
        self,
        real_session_manager,
        mock_agent_service,
        sample_groups,
    ):
        """Test workflow with partial failures."""
        call_count = 0

        async def mixed_results(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count in [2, 4]:  # Fail 2nd and 4th calls
                return MockAgentResult(success=False, error="Test error")
            return MockAgentResult(success=True)

        mock_agent_service.call_agent = AsyncMock(side_effect=mixed_results)

        # Create session
        session_id = await real_session_manager.create_session(
            canvas_path="test.canvas",
            node_count=5,
        )

        orchestrator = BatchOrchestrator(
            session_manager=real_session_manager,
            agent_service=mock_agent_service,
        )

        result = await orchestrator.start_batch_session(
            session_id=session_id,
            canvas_path="test.canvas",
            groups=sample_groups,
        )

        # Should have partial failure
        assert result["status"] == "partial_failure"
        assert result["completed_nodes"] == 3
        assert result["failed_nodes"] == 2

        # Session should reflect partial failure
        session = await real_session_manager.get_session(session_id)
        assert session.status == SessionStatus.PARTIAL_FAILURE

    @pytest.mark.asyncio
    async def test_full_workflow_all_failed(
        self,
        real_session_manager,
        mock_agent_service,
        sample_groups,
    ):
        """Test workflow where all nodes fail."""
        mock_agent_service.call_agent = AsyncMock(
            return_value=MockAgentResult(success=False, error="All failed")
        )

        session_id = await real_session_manager.create_session(
            canvas_path="test.canvas",
            node_count=5,
        )

        orchestrator = BatchOrchestrator(
            session_manager=real_session_manager,
            agent_service=mock_agent_service,
        )

        result = await orchestrator.start_batch_session(
            session_id=session_id,
            canvas_path="test.canvas",
            groups=sample_groups,
        )

        assert result["status"] == "failed"
        assert result["completed_nodes"] == 0
        assert result["failed_nodes"] == 5

        session = await real_session_manager.get_session(session_id)
        assert session.status == SessionStatus.FAILED


# ═══════════════════════════════════════════════════════════════════════════════
# Integration Test: Session Lifecycle
# ═══════════════════════════════════════════════════════════════════════════════

class TestSessionLifecycle:
    """Test session lifecycle transitions."""

    @pytest.mark.asyncio
    async def test_session_transitions_pending_to_running(
        self,
        real_session_manager,
        mock_agent_service,
    ):
        """Test session transitions from pending to running."""
        session_id = await real_session_manager.create_session(
            canvas_path="test.canvas",
            node_count=1,
        )

        # Capture state transitions
        states_observed = []

        original_transition = real_session_manager.transition_state

        async def tracking_transition(session_id, status, error_message=None):
            states_observed.append(status)
            return await original_transition(session_id, status, error_message)

        real_session_manager.transition_state = tracking_transition

        orchestrator = BatchOrchestrator(
            session_manager=real_session_manager,
            agent_service=mock_agent_service,
        )

        groups = [GroupConfig(group_id="g1", agent_type="test", node_ids=["n1"])]

        await orchestrator.start_batch_session(
            session_id=session_id,
            canvas_path="test.canvas",
            groups=groups,
        )

        # Should have transitioned: PENDING → RUNNING → COMPLETED
        assert SessionStatus.RUNNING in states_observed
        assert SessionStatus.COMPLETED in states_observed

    @pytest.mark.asyncio
    async def test_node_results_recorded(
        self,
        real_session_manager,
        mock_agent_service,
    ):
        """Test that node results are recorded in session."""
        session_id = await real_session_manager.create_session(
            canvas_path="test.canvas",
            node_count=3,
        )

        orchestrator = BatchOrchestrator(
            session_manager=real_session_manager,
            agent_service=mock_agent_service,
        )

        groups = [
            GroupConfig(
                group_id="g1",
                agent_type="test",
                node_ids=["n1", "n2", "n3"],
            )
        ]

        await orchestrator.start_batch_session(
            session_id=session_id,
            canvas_path="test.canvas",
            groups=groups,
        )

        session = await real_session_manager.get_session(session_id)

        # All nodes should have results
        assert len(session.node_results) == 3
        assert all(nr.status == "success" for nr in session.node_results.values())


# ═══════════════════════════════════════════════════════════════════════════════
# Integration Test: Cancellation
# ═══════════════════════════════════════════════════════════════════════════════

class TestCancellationWorkflow:
    """Test cancellation workflow end-to-end."""

    @pytest.mark.asyncio
    async def test_cancellation_mid_execution(
        self,
        real_session_manager,
        mock_agent_service,
    ):
        """Test cancellation during execution."""
        completed_before_cancel = 0
        execution_started = asyncio.Event()

        async def slow_agent(*args, **kwargs):
            nonlocal completed_before_cancel
            execution_started.set()
            await simulate_async_delay(0.5)  # Slow execution
            completed_before_cancel += 1
            return MockAgentResult(success=True)

        mock_agent_service.call_agent = AsyncMock(side_effect=slow_agent)

        session_id = await real_session_manager.create_session(
            canvas_path="test.canvas",
            node_count=10,
        )

        orchestrator = BatchOrchestrator(
            session_manager=real_session_manager,
            agent_service=mock_agent_service,
            max_concurrent=2,  # Limit concurrent to test cancellation
        )

        groups = [
            GroupConfig(
                group_id="g1",
                agent_type="test",
                node_ids=[f"n{i}" for i in range(10)],
            )
        ]

        # Start execution in background
        execution_task = asyncio.create_task(
            orchestrator.start_batch_session(
                session_id=session_id,
                canvas_path="test.canvas",
                groups=groups,
            )
        )

        # Wait for execution to start
        await execution_started.wait()
        await simulate_async_delay(0.1)

        # Request cancellation
        cancel_result = await orchestrator.cancel_session(session_id)
        assert cancel_result["success"] is True

        # Wait for execution to finish
        try:
            result = await execution_task
            # Verify some nodes completed before cancellation
            assert result["completed_nodes"] >= 0
        except asyncio.CancelledError:
            pass


# ═══════════════════════════════════════════════════════════════════════════════
# Integration Test: Progress Events
# ═══════════════════════════════════════════════════════════════════════════════

class TestProgressEventFlow:
    """Test progress event emission flow."""

    @pytest.mark.asyncio
    async def test_progress_events_sequence(
        self,
        real_session_manager,
        mock_agent_service,
        progress_callback,
        progress_events,
    ):
        """Test that progress events are emitted in correct sequence."""
        session_id = await real_session_manager.create_session(
            canvas_path="test.canvas",
            node_count=2,
        )

        orchestrator = BatchOrchestrator(
            session_manager=real_session_manager,
            agent_service=mock_agent_service,
            progress_callback=progress_callback,
        )

        groups = [
            GroupConfig(group_id="g1", agent_type="test", node_ids=["n1", "n2"]),
        ]

        await orchestrator.start_batch_session(
            session_id=session_id,
            canvas_path="test.canvas",
            groups=groups,
        )

        # Verify event sequence
        event_types = [e.event_type for e in progress_events]

        # Should start with progress update
        assert event_types[0] == ProgressEventType.PROGRESS_UPDATE

        # Should have task completed events
        task_completed_count = sum(
            1 for e in progress_events
            if e.event_type == ProgressEventType.TASK_COMPLETED
        )
        assert task_completed_count == 2  # 2 nodes

        # Should have group completed
        group_completed = [
            e for e in progress_events
            if e.event_type == ProgressEventType.GROUP_COMPLETED
        ]
        assert len(group_completed) == 1

        # Should end with session completed
        assert event_types[-1] == ProgressEventType.SESSION_COMPLETED

    @pytest.mark.asyncio
    async def test_async_progress_callback(
        self,
        real_session_manager,
        mock_agent_service,
    ):
        """Test that async progress callbacks work correctly."""
        events_received = []

        async def async_callback(event: ProgressEvent):
            await simulate_async_delay(0.01)  # Simulate async work
            events_received.append(event)

        session_id = await real_session_manager.create_session(
            canvas_path="test.canvas",
            node_count=1,
        )

        orchestrator = BatchOrchestrator(
            session_manager=real_session_manager,
            agent_service=mock_agent_service,
            progress_callback=async_callback,
        )

        groups = [GroupConfig(group_id="g1", agent_type="test", node_ids=["n1"])]

        await orchestrator.start_batch_session(
            session_id=session_id,
            canvas_path="test.canvas",
            groups=groups,
        )

        assert len(events_received) > 0


# ═══════════════════════════════════════════════════════════════════════════════
# Integration Test: Concurrency Control
# ═══════════════════════════════════════════════════════════════════════════════

class TestConcurrencyControl:
    """Test concurrency control integration."""

    @pytest.mark.asyncio
    async def test_concurrent_execution_respects_limit(
        self,
        real_session_manager,
        mock_agent_service,
    ):
        """Test that concurrent execution respects max_concurrent limit."""
        max_concurrent_observed = 0
        current_concurrent = 0
        lock = asyncio.Lock()

        async def tracking_agent(*args, **kwargs):
            nonlocal max_concurrent_observed, current_concurrent
            async with lock:
                current_concurrent += 1
                if current_concurrent > max_concurrent_observed:
                    max_concurrent_observed = current_concurrent
            await simulate_async_delay(0.05)
            async with lock:
                current_concurrent -= 1
            return MockAgentResult(success=True)

        mock_agent_service.call_agent = AsyncMock(side_effect=tracking_agent)

        session_id = await real_session_manager.create_session(
            canvas_path="test.canvas",
            node_count=20,
        )

        orchestrator = BatchOrchestrator(
            session_manager=real_session_manager,
            agent_service=mock_agent_service,
            max_concurrent=5,
        )

        groups = [
            GroupConfig(
                group_id="g1",
                agent_type="test",
                node_ids=[f"n{i}" for i in range(20)],
            )
        ]

        await orchestrator.start_batch_session(
            session_id=session_id,
            canvas_path="test.canvas",
            groups=groups,
        )

        assert max_concurrent_observed <= 5


# ═══════════════════════════════════════════════════════════════════════════════
# Integration Test: Memory Integration
# ═══════════════════════════════════════════════════════════════════════════════

class TestMemoryIntegration:
    """Test memory write integration."""

    @pytest.mark.asyncio
    async def test_memory_write_called_for_each_success(
        self,
        real_session_manager,
        mock_agent_service,
    ):
        """Test that memory write is triggered for each successful node."""
        session_id = await real_session_manager.create_session(
            canvas_path="test.canvas",
            node_count=3,
        )

        orchestrator = BatchOrchestrator(
            session_manager=real_session_manager,
            agent_service=mock_agent_service,
        )

        groups = [
            GroupConfig(group_id="g1", agent_type="oral-explanation", node_ids=["n1", "n2", "n3"]),
        ]

        await orchestrator.start_batch_session(
            session_id=session_id,
            canvas_path="test.canvas",
            groups=groups,
        )

        # Memory write: 1 session-start (Story 30.12) + 3 node completions = 4
        assert mock_agent_service._trigger_memory_write.call_count == 4

    @pytest.mark.asyncio
    async def test_memory_write_not_called_on_failure(
        self,
        real_session_manager,
        mock_agent_service,
    ):
        """Test that memory write is not triggered for failed nodes."""
        mock_agent_service.call_agent = AsyncMock(
            return_value=MockAgentResult(success=False, error="Failed")
        )

        session_id = await real_session_manager.create_session(
            canvas_path="test.canvas",
            node_count=2,
        )

        orchestrator = BatchOrchestrator(
            session_manager=real_session_manager,
            agent_service=mock_agent_service,
        )

        groups = [
            GroupConfig(group_id="g1", agent_type="test", node_ids=["n1", "n2"]),
        ]

        await orchestrator.start_batch_session(
            session_id=session_id,
            canvas_path="test.canvas",
            groups=groups,
        )

        # Memory write: only 1 session-start call (Story 30.12), none for failed nodes
        assert mock_agent_service._trigger_memory_write.call_count == 1


# ═══════════════════════════════════════════════════════════════════════════════
# Integration Test: Performance Metrics
# ═══════════════════════════════════════════════════════════════════════════════

class TestPerformanceMetrics:
    """Test performance metrics calculation."""

    @pytest.mark.asyncio
    async def test_performance_metrics_calculated(
        self,
        real_session_manager,
        mock_agent_service,
    ):
        """Test that performance metrics are calculated correctly."""
        async def timed_agent(*args, **kwargs):
            await simulate_async_delay(0.1)  # 100ms per call
            return MockAgentResult(success=True)

        mock_agent_service.call_agent = AsyncMock(side_effect=timed_agent)

        session_id = await real_session_manager.create_session(
            canvas_path="test.canvas",
            node_count=4,
        )

        orchestrator = BatchOrchestrator(
            session_manager=real_session_manager,
            agent_service=mock_agent_service,
            max_concurrent=4,  # All parallel
        )

        groups = [
            GroupConfig(group_id="g1", agent_type="test", node_ids=["n1", "n2", "n3", "n4"]),
        ]

        result = await orchestrator.start_batch_session(
            session_id=session_id,
            canvas_path="test.canvas",
            groups=groups,
        )

        metrics = result["performance_metrics"]

        # Total duration should be close to 100ms (parallel)
        assert metrics["total_duration_seconds"] < 1.0

        # Average should be around 25ms per node when parallel
        assert metrics["average_duration_per_node"] > 0

        # Parallel efficiency should be > 1 (speedup)
        assert metrics["parallel_efficiency"] > 0

        # Peak concurrent should be up to 4
        assert metrics["peak_concurrent"] <= 4


# ═══════════════════════════════════════════════════════════════════════════════
# Integration Test: Error Scenarios
# ═══════════════════════════════════════════════════════════════════════════════

class TestErrorScenarios:
    """Test error handling in integration scenarios."""

    @pytest.mark.asyncio
    async def test_session_not_found_error(
        self,
        real_session_manager,
        mock_agent_service,
    ):
        """Test handling of non-existent session."""
        orchestrator = BatchOrchestrator(
            session_manager=real_session_manager,
            agent_service=mock_agent_service,
        )

        with pytest.raises(SessionNotFoundError):
            await orchestrator.start_batch_session(
                session_id="non-existent-session",
                canvas_path="test.canvas",
                groups=[],
            )

    @pytest.mark.asyncio
    async def test_timeout_handling(
        self,
        real_session_manager,
        mock_agent_service,
    ):
        """Test timeout handling in integration."""
        async def very_slow_agent(*args, **kwargs):
            await simulate_async_delay(10)  # Very slow
            return MockAgentResult()

        mock_agent_service.call_agent = AsyncMock(side_effect=very_slow_agent)

        session_id = await real_session_manager.create_session(
            canvas_path="test.canvas",
            node_count=1,
        )

        orchestrator = BatchOrchestrator(
            session_manager=real_session_manager,
            agent_service=mock_agent_service,
        )

        with pytest.raises(asyncio.TimeoutError):
            await orchestrator.start_batch_session(
                session_id=session_id,
                canvas_path="test.canvas",
                groups=[GroupConfig(group_id="g1", agent_type="test", node_ids=["n1"])],
                timeout=0.2,  # Very short timeout
            )

        # Session should be marked as failed
        session = await real_session_manager.get_session(session_id)
        assert session.status == SessionStatus.FAILED
        assert "Timeout" in (session.error_message or "")
