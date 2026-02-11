# Canvas Learning System - BatchOrchestrator Unit Tests
# Story 33.6: Batch Processing Orchestrator
# [Source: docs/stories/33.6.story.md#Task-8]
"""
Unit tests for BatchOrchestrator service.

Test coverage targets:
- AC1: Session validation and state transitions
- AC2: Semaphore(12) concurrency control
- AC3: Progress broadcasting
- AC4: Partial failure and cancellation handling
- AC5: Result aggregation and metrics
- AC6: Fire-and-forget memory integration
- Target: ≥90% coverage
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.conftest import simulate_async_delay

from app.models.session_models import (
    NodeResult,
    SessionInfo,
    SessionStatus,
)
from app.services.batch_orchestrator import (
    BatchOrchestrator,
    GroupConfig,
    GroupExecutionResult,
    NodeExecutionResult,
    PerformanceMetrics,
    ProgressEvent,
    ProgressEventType,
    DEFAULT_MAX_CONCURRENT,
)
from app.services.session_manager import (
    SessionManager,
    SessionNotFoundError,
    InvalidStateTransitionError,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class MockAgentResult:
    """Mock agent result for testing."""
    success: bool = True
    content: str = "Test content"
    file_path: Optional[str] = None
    error: Optional[str] = None


@pytest.fixture
def mock_session_manager():
    """Create a mock SessionManager."""
    manager = MagicMock(spec=SessionManager)
    manager.get_session = AsyncMock()
    manager.transition_state = AsyncMock()
    manager.update_progress = AsyncMock()
    manager.add_node_result = AsyncMock()
    return manager


## mock_agent_service: use shared fixture from conftest.py
## [Source: Story 31.A.10 AC-2 — Fixture deduplication]


@pytest.fixture
def mock_session_info():
    """Create a mock SessionInfo in pending state."""
    return SessionInfo(
        session_id="test-session-001",
        canvas_path="test.canvas",
        node_count=10,
        status=SessionStatus.PENDING,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


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


@pytest.fixture
def orchestrator(mock_session_manager, mock_agent_service):
    """Create BatchOrchestrator with mocks."""
    return BatchOrchestrator(
        session_manager=mock_session_manager,
        agent_service=mock_agent_service,
        max_concurrent=12,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Initialization
# ═══════════════════════════════════════════════════════════════════════════════

class TestBatchOrchestratorInit:
    """Test BatchOrchestrator initialization."""

    def test_init_default_concurrent(self, mock_session_manager, mock_agent_service):
        """Test default max_concurrent is 12."""
        orchestrator = BatchOrchestrator(
            session_manager=mock_session_manager,
            agent_service=mock_agent_service,
        )
        assert orchestrator.max_concurrent == DEFAULT_MAX_CONCURRENT
        assert orchestrator.semaphore._value == 12

    def test_init_custom_concurrent(self, mock_session_manager, mock_agent_service):
        """Test custom max_concurrent value."""
        orchestrator = BatchOrchestrator(
            session_manager=mock_session_manager,
            agent_service=mock_agent_service,
            max_concurrent=5,
        )
        assert orchestrator.max_concurrent == 5
        assert orchestrator.semaphore._value == 5

    def test_init_with_progress_callback(self, mock_session_manager, mock_agent_service):
        """Test initialization with progress callback."""
        callback = MagicMock()
        orchestrator = BatchOrchestrator(
            session_manager=mock_session_manager,
            agent_service=mock_agent_service,
            progress_callback=callback,
        )
        assert orchestrator.progress_callback == callback


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Session Validation (AC:1)
# ═══════════════════════════════════════════════════════════════════════════════

class TestSessionValidation:
    """Test session validation (AC:1)."""

    @pytest.mark.asyncio
    async def test_validate_session_success(
        self, orchestrator, mock_session_manager, mock_session_info
    ):
        """Test successful session validation."""
        mock_session_manager.get_session.return_value = mock_session_info

        result = await orchestrator._validate_session("test-session-001")

        assert result.session_id == "test-session-001"
        assert result.status == SessionStatus.PENDING
        mock_session_manager.get_session.assert_called_once_with("test-session-001")

    @pytest.mark.asyncio
    async def test_validate_session_not_found(self, orchestrator, mock_session_manager):
        """Test validation fails when session not found."""
        mock_session_manager.get_session.side_effect = SessionNotFoundError("not-found")

        with pytest.raises(SessionNotFoundError):
            await orchestrator._validate_session("not-found")

    @pytest.mark.asyncio
    async def test_validate_session_wrong_state(
        self, orchestrator, mock_session_manager, mock_session_info
    ):
        """Test validation fails when session is not pending."""
        mock_session_info.status = SessionStatus.RUNNING
        mock_session_manager.get_session.return_value = mock_session_info

        with pytest.raises(InvalidStateTransitionError):
            await orchestrator._validate_session("test-session-001")


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Semaphore Concurrency Control (AC:2)
# ═══════════════════════════════════════════════════════════════════════════════

class TestSemaphoreConcurrency:
    """Test Semaphore(12) concurrency control (AC:2)."""

    @pytest.mark.asyncio
    async def test_semaphore_limits_concurrent_executions(
        self, mock_session_manager, mock_agent_service
    ):
        """Test that semaphore limits concurrent executions to max_concurrent."""
        # Create orchestrator with max_concurrent=3
        orchestrator = BatchOrchestrator(
            session_manager=mock_session_manager,
            agent_service=mock_agent_service,
            max_concurrent=3,
        )

        # Track concurrent executions
        max_concurrent_seen = 0
        current_concurrent = 0
        lock = asyncio.Lock()

        original_call_agent = mock_agent_service.call_agent

        async def tracked_call_agent(*args, **kwargs):
            nonlocal max_concurrent_seen, current_concurrent
            async with lock:
                current_concurrent += 1
                if current_concurrent > max_concurrent_seen:
                    max_concurrent_seen = current_concurrent

            # Simulate some work
            await simulate_async_delay(0.1)

            async with lock:
                current_concurrent -= 1

            return MockAgentResult()

        mock_agent_service.call_agent = AsyncMock(side_effect=tracked_call_agent)

        # Execute multiple nodes (more than max_concurrent)
        session_id = "test-session"
        canvas_path = "test.canvas"

        tasks = [
            orchestrator._execute_node_with_semaphore(
                session_id=session_id,
                canvas_path=canvas_path,
                node_id=f"node-{i}",
                agent_type="oral-explanation",
            )
            for i in range(10)
        ]

        await asyncio.gather(*tasks)

        # Should never exceed max_concurrent
        assert max_concurrent_seen <= 3, f"Max concurrent was {max_concurrent_seen}, expected <= 3"

    @pytest.mark.asyncio
    async def test_peak_concurrent_tracking(
        self, mock_session_manager, mock_agent_service
    ):
        """Test that peak concurrent is tracked correctly."""
        orchestrator = BatchOrchestrator(
            session_manager=mock_session_manager,
            agent_service=mock_agent_service,
            max_concurrent=5,
        )

        # Reset tracking
        orchestrator._peak_concurrent = 0

        async def slow_call(*args, **kwargs):
            await simulate_async_delay(0.05)
            return MockAgentResult()

        mock_agent_service.call_agent = AsyncMock(side_effect=slow_call)

        tasks = [
            orchestrator._execute_node_with_semaphore(
                session_id="test",
                canvas_path="test.canvas",
                node_id=f"node-{i}",
                agent_type="test",
            )
            for i in range(8)
        ]

        await asyncio.gather(*tasks)

        # Peak should be tracked
        assert orchestrator._peak_concurrent <= 5


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Progress Broadcasting (AC:3)
# ═══════════════════════════════════════════════════════════════════════════════

class TestProgressBroadcasting:
    """Test progress broadcasting (AC:3)."""

    @pytest.mark.asyncio
    async def test_broadcast_calls_sync_callback(
        self, mock_session_manager, mock_agent_service
    ):
        """Test that sync callback is called."""
        callback = MagicMock()
        orchestrator = BatchOrchestrator(
            session_manager=mock_session_manager,
            agent_service=mock_agent_service,
            progress_callback=callback,
        )

        await orchestrator._broadcast_progress(
            ProgressEventType.PROGRESS_UPDATE,
            "test-session",
            {"progress_percent": 50}
        )

        callback.assert_called_once()
        event = callback.call_args[0][0]
        assert isinstance(event, ProgressEvent)
        assert event.event_type == ProgressEventType.PROGRESS_UPDATE
        assert event.data["progress_percent"] == 50

    @pytest.mark.asyncio
    async def test_broadcast_calls_async_callback(
        self, mock_session_manager, mock_agent_service
    ):
        """Test that async callback is awaited."""
        callback = AsyncMock()
        orchestrator = BatchOrchestrator(
            session_manager=mock_session_manager,
            agent_service=mock_agent_service,
            progress_callback=callback,
        )

        await orchestrator._broadcast_progress(
            ProgressEventType.TASK_COMPLETED,
            "test-session",
            {"node_id": "node-001"}
        )

        callback.assert_called_once()

    @pytest.mark.asyncio
    async def test_broadcast_handles_callback_error(
        self, mock_session_manager, mock_agent_service
    ):
        """Test that callback errors don't break execution."""
        callback = MagicMock(side_effect=Exception("Callback error"))
        orchestrator = BatchOrchestrator(
            session_manager=mock_session_manager,
            agent_service=mock_agent_service,
            progress_callback=callback,
        )

        # Should not raise
        await orchestrator._broadcast_progress(
            ProgressEventType.ERROR,
            "test-session",
            {"error": "test"}
        )

    @pytest.mark.asyncio
    async def test_broadcast_without_callback(self, orchestrator):
        """Test broadcast when no callback is set."""
        orchestrator.progress_callback = None

        # Should not raise
        await orchestrator._broadcast_progress(
            ProgressEventType.PROGRESS_UPDATE,
            "test-session",
            {}
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Partial Failure Handling (AC:4)
# ═══════════════════════════════════════════════════════════════════════════════

class TestPartialFailureHandling:
    """Test partial failure handling (AC:4)."""

    @pytest.mark.asyncio
    async def test_partial_failure_continues_other_tasks(
        self, mock_session_manager, mock_agent_service, mock_session_info
    ):
        """Test that partial failures don't interrupt other tasks."""
        call_count = 0

        async def mixed_results(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                return MockAgentResult(success=False, error="Test error")
            return MockAgentResult(success=True)

        mock_agent_service.call_agent = AsyncMock(side_effect=mixed_results)
        mock_session_manager.get_session.return_value = mock_session_info

        orchestrator = BatchOrchestrator(
            session_manager=mock_session_manager,
            agent_service=mock_agent_service,
        )

        group = GroupConfig(
            group_id="group-1",
            agent_type="test",
            node_ids=["node-1", "node-2", "node-3"],
        )

        result = await orchestrator._execute_group(
            session_id="test",
            canvas_path="test.canvas",
            group=group,
        )

        # Should have processed all 3 nodes
        assert len(result.node_results) == 3
        assert result.completed_count == 2
        assert result.failed_count == 1
        assert result.status == "partial_failure"

    @pytest.mark.asyncio
    async def test_all_failed_status(
        self, mock_session_manager, mock_agent_service
    ):
        """Test that all failures result in 'failed' status."""
        mock_agent_service.call_agent = AsyncMock(
            return_value=MockAgentResult(success=False, error="Failed")
        )

        orchestrator = BatchOrchestrator(
            session_manager=mock_session_manager,
            agent_service=mock_agent_service,
        )

        group = GroupConfig(
            group_id="group-1",
            agent_type="test",
            node_ids=["node-1", "node-2"],
        )

        result = await orchestrator._execute_group(
            session_id="test",
            canvas_path="test.canvas",
            group=group,
        )

        assert result.status == "failed"
        assert result.completed_count == 0
        assert result.failed_count == 2

    @pytest.mark.asyncio
    async def test_all_success_status(
        self, mock_session_manager, mock_agent_service
    ):
        """Test that all successes result in 'completed' status."""
        mock_agent_service.call_agent = AsyncMock(
            return_value=MockAgentResult(success=True)
        )

        orchestrator = BatchOrchestrator(
            session_manager=mock_session_manager,
            agent_service=mock_agent_service,
        )

        group = GroupConfig(
            group_id="group-1",
            agent_type="test",
            node_ids=["node-1", "node-2"],
        )

        result = await orchestrator._execute_group(
            session_id="test",
            canvas_path="test.canvas",
            group=group,
        )

        assert result.status == "completed"
        assert result.completed_count == 2
        assert result.failed_count == 0


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Cancellation Support (AC:4)
# ═══════════════════════════════════════════════════════════════════════════════

class TestCancellationSupport:
    """Test cancellation support (AC:4)."""

    @pytest.mark.asyncio
    async def test_cancel_session_success(
        self, orchestrator, mock_session_manager, mock_session_info
    ):
        """Test successful cancellation request."""
        mock_session_info.status = SessionStatus.RUNNING
        mock_session_info.completed_nodes = 5
        mock_session_manager.get_session.return_value = mock_session_info

        result = await orchestrator.cancel_session("test-session-001")

        assert result["success"] is True
        assert result["completed_count"] == 5
        assert orchestrator.is_cancelled("test-session-001") is True

    @pytest.mark.asyncio
    async def test_cancel_session_not_found(self, orchestrator, mock_session_manager):
        """Test cancellation when session not found."""
        mock_session_manager.get_session.side_effect = SessionNotFoundError("not-found")

        result = await orchestrator.cancel_session("not-found")

        assert result["success"] is False
        assert "not found" in result["message"]

    @pytest.mark.asyncio
    async def test_cancel_session_already_terminal(
        self, orchestrator, mock_session_manager, mock_session_info
    ):
        """Test cancellation when session already completed."""
        mock_session_info.status = SessionStatus.COMPLETED
        mock_session_info.completed_nodes = 10
        mock_session_manager.get_session.return_value = mock_session_info

        result = await orchestrator.cancel_session("test-session-001")

        assert result["success"] is False
        assert "terminal state" in result["message"]
        assert result["completed_count"] == 10

    @pytest.mark.asyncio
    async def test_cancelled_nodes_return_early(
        self, orchestrator, mock_session_manager, mock_agent_service
    ):
        """Test that nodes return early when cancelled."""
        orchestrator._cancel_requested["test-session"] = True

        result = await orchestrator._execute_node_with_semaphore(
            session_id="test-session",
            canvas_path="test.canvas",
            node_id="node-001",
            agent_type="test",
        )

        assert result.success is False
        assert result.error_message == "Cancelled"
        # Agent should not have been called
        mock_agent_service.call_agent.assert_not_called()


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Result Aggregation (AC:5)
# ═══════════════════════════════════════════════════════════════════════════════

class TestResultAggregation:
    """Test result aggregation (AC:5)."""

    @pytest.mark.asyncio
    async def test_aggregate_results_basic(
        self, orchestrator, mock_session_manager, mock_session_info
    ):
        """Test basic result aggregation."""
        mock_session_info.status = SessionStatus.COMPLETED
        mock_session_manager.get_session.return_value = mock_session_info

        start_time = datetime.now()
        end_time = datetime.now()

        groups = [
            GroupConfig(group_id="g1", agent_type="test", node_ids=["n1", "n2"]),
        ]

        group_results = [
            GroupExecutionResult(
                group_id="g1",
                agent_type="test",
                status="completed",
                node_results=[
                    NodeExecutionResult(node_id="n1", success=True, execution_time_ms=100),
                    NodeExecutionResult(node_id="n2", success=True, execution_time_ms=150),
                ],
                completed_count=2,
                failed_count=0,
            ),
        ]

        result = await orchestrator._aggregate_results(
            session_id="test",
            groups=groups,
            group_results=group_results,
            start_time=start_time,
            end_time=end_time,
            final_status=SessionStatus.COMPLETED,
        )

        assert result["task_id"] == "test"
        assert result["status"] == "completed"
        assert result["total_nodes"] == 2
        assert result["completed_nodes"] == 2
        assert result["failed_nodes"] == 0
        assert "performance_metrics" in result
        assert result["performance_metrics"]["peak_concurrent"] >= 0

    @pytest.mark.asyncio
    async def test_aggregate_results_with_failures(
        self, orchestrator, mock_session_manager, mock_session_info
    ):
        """Test aggregation with mixed results."""
        mock_session_info.status = SessionStatus.PARTIAL_FAILURE
        mock_session_manager.get_session.return_value = mock_session_info

        start_time = datetime.now()
        end_time = datetime.now()

        groups = [
            GroupConfig(group_id="g1", agent_type="test", node_ids=["n1", "n2", "n3"]),
        ]

        group_results = [
            GroupExecutionResult(
                group_id="g1",
                agent_type="test",
                status="partial_failure",
                node_results=[
                    NodeExecutionResult(node_id="n1", success=True, execution_time_ms=100),
                    NodeExecutionResult(node_id="n2", success=False, error_message="Error"),
                    NodeExecutionResult(node_id="n3", success=True, execution_time_ms=150),
                ],
                completed_count=2,
                failed_count=1,
            ),
        ]

        result = await orchestrator._aggregate_results(
            session_id="test",
            groups=groups,
            group_results=group_results,
            start_time=start_time,
            end_time=end_time,
            final_status=SessionStatus.PARTIAL_FAILURE,
        )

        assert result["status"] == "partial_failure"
        assert result["completed_nodes"] == 2
        assert result["failed_nodes"] == 1
        assert len(result["groups"][0]["errors"]) == 1


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Fire-and-Forget Memory Integration (AC:6)
# ═══════════════════════════════════════════════════════════════════════════════

class TestMemoryIntegration:
    """Test fire-and-forget memory integration (AC:6)."""

    @pytest.mark.asyncio
    async def test_memory_write_triggered_on_success(
        self, orchestrator, mock_agent_service
    ):
        """Test that memory write is triggered for successful agents."""
        result = MockAgentResult(success=True, content="Test content")

        await orchestrator._trigger_memory_write(
            session_id="test",
            agent_type="oral-explanation",
            canvas_path="test/canvas.canvas",
            node_id="node-001",
            result=result,
        )

        mock_agent_service._trigger_memory_write.assert_called_once()
        call_kwargs = mock_agent_service._trigger_memory_write.call_args[1]
        assert call_kwargs["agent_type"] == "oral-explanation"
        assert call_kwargs["node_id"] == "node-001"

    @pytest.mark.asyncio
    async def test_memory_write_extracts_canvas_name(
        self, orchestrator, mock_agent_service
    ):
        """Test that canvas name is correctly extracted."""
        result = MockAgentResult(success=True)

        await orchestrator._trigger_memory_write(
            session_id="test",
            agent_type="test",
            canvas_path="path/to/my-canvas.canvas",
            node_id="node-001",
            result=result,
        )

        call_kwargs = mock_agent_service._trigger_memory_write.call_args[1]
        assert call_kwargs["canvas_name"] == "my-canvas"

    @pytest.mark.asyncio
    async def test_memory_write_failure_does_not_raise(
        self, orchestrator, mock_agent_service
    ):
        """Test that memory write failures don't raise exceptions."""
        mock_agent_service._trigger_memory_write.side_effect = Exception("Memory error")

        # Should not raise
        await orchestrator._trigger_memory_write(
            session_id="test",
            agent_type="test",
            canvas_path="test.canvas",
            node_id="node-001",
            result=MockAgentResult(),
        )

    @pytest.mark.asyncio
    async def test_memory_write_without_method(
        self, mock_session_manager
    ):
        """Test handling when agent_service doesn't have _trigger_memory_write."""
        agent_service = MagicMock()
        # Remove the method
        del agent_service._trigger_memory_write

        orchestrator = BatchOrchestrator(
            session_manager=mock_session_manager,
            agent_service=agent_service,
        )

        # Should not raise
        await orchestrator._trigger_memory_write(
            session_id="test",
            agent_type="test",
            canvas_path="test.canvas",
            node_id="node-001",
            result=MockAgentResult(),
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Full Session Execution
# ═══════════════════════════════════════════════════════════════════════════════

class TestFullSessionExecution:
    """Test complete session execution flow."""

    @pytest.mark.asyncio
    async def test_start_batch_session_success(
        self, orchestrator, mock_session_manager, mock_session_info, mock_agent_service, sample_groups
    ):
        """Test successful batch session execution."""
        mock_session_manager.get_session.return_value = mock_session_info

        result = await orchestrator.start_batch_session(
            session_id="test-session-001",
            canvas_path="test.canvas",
            groups=sample_groups,
            timeout=60,
        )

        assert result["task_id"] == "test-session-001"
        assert "performance_metrics" in result
        # Session should have transitioned to running then to final state
        assert mock_session_manager.transition_state.call_count >= 2

    @pytest.mark.asyncio
    async def test_start_batch_session_timeout(
        self, mock_session_manager, mock_agent_service, mock_session_info, sample_groups
    ):
        """Test batch session timeout handling."""
        async def slow_agent(*args, **kwargs):
            await simulate_async_delay(10)
            return MockAgentResult()

        mock_agent_service.call_agent = AsyncMock(side_effect=slow_agent)
        mock_session_manager.get_session.return_value = mock_session_info

        orchestrator = BatchOrchestrator(
            session_manager=mock_session_manager,
            agent_service=mock_agent_service,
        )

        with pytest.raises(asyncio.TimeoutError):
            await orchestrator.start_batch_session(
                session_id="test-session-001",
                canvas_path="test.canvas",
                groups=sample_groups,
                timeout=0.1,  # Very short timeout
            )

        # Should have transitioned to failed
        transition_calls = mock_session_manager.transition_state.call_args_list
        # Last call should be to FAILED
        last_call_status = transition_calls[-1][0][1]
        assert last_call_status == SessionStatus.FAILED


# ═══════════════════════════════════════════════════════════════════════════════
# Test: ProgressEvent Data Class
# ═══════════════════════════════════════════════════════════════════════════════

class TestProgressEvent:
    """Test ProgressEvent data class."""

    def test_progress_event_to_dict(self):
        """Test ProgressEvent serialization."""
        event = ProgressEvent(
            event_type=ProgressEventType.PROGRESS_UPDATE,
            session_id="test-123",
            data={"progress_percent": 50},
        )

        result = event.to_dict()

        assert result["type"] == "progress_update"
        assert result["task_id"] == "test-123"
        assert result["data"]["progress_percent"] == 50
        assert "timestamp" in result


# ═══════════════════════════════════════════════════════════════════════════════
# Test: GroupConfig and NodeExecutionResult
# ═══════════════════════════════════════════════════════════════════════════════

class TestDataClasses:
    """Test data class functionality."""

    def test_group_config_defaults(self):
        """Test GroupConfig default values."""
        config = GroupConfig(
            group_id="g1",
            agent_type="test",
            node_ids=["n1", "n2"],
        )
        assert config.status == "pending"

    def test_node_execution_result_defaults(self):
        """Test NodeExecutionResult default values."""
        result = NodeExecutionResult(node_id="n1", success=True)
        assert result.file_path is None
        assert result.error_message is None
        assert result.execution_time_ms == 0

    def test_performance_metrics_defaults(self):
        """Test PerformanceMetrics default values."""
        metrics = PerformanceMetrics()
        assert metrics.total_duration_seconds == 0.0
        assert metrics.parallel_efficiency == 0.0
        assert metrics.peak_concurrent == 0


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Exception Handling in Group Execution
# ═══════════════════════════════════════════════════════════════════════════════

class TestExceptionHandling:
    """Test exception handling scenarios."""

    @pytest.mark.asyncio
    async def test_group_execution_handles_exceptions(
        self, mock_session_manager, mock_agent_service
    ):
        """Test that group execution converts exceptions to failed results."""
        mock_agent_service.call_agent = AsyncMock(side_effect=Exception("Agent error"))

        orchestrator = BatchOrchestrator(
            session_manager=mock_session_manager,
            agent_service=mock_agent_service,
        )

        group = GroupConfig(
            group_id="g1",
            agent_type="test",
            node_ids=["n1", "n2"],
        )

        result = await orchestrator._execute_group(
            session_id="test",
            canvas_path="test.canvas",
            group=group,
        )

        assert result.failed_count == 2
        assert result.status == "failed"
        for nr in result.node_results:
            assert nr.success is False
            assert "Agent error" in nr.error_message

    @pytest.mark.asyncio
    async def test_execute_all_groups_handles_group_exception(
        self, mock_session_manager, mock_agent_service
    ):
        """Test that execute_all_groups handles group-level exceptions."""
        orchestrator = BatchOrchestrator(
            session_manager=mock_session_manager,
            agent_service=mock_agent_service,
        )

        # Mock _execute_group to raise for second group
        call_count = 0
        original_execute = orchestrator._execute_group

        async def mock_execute_group(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise Exception("Group execution failed")
            return GroupExecutionResult(
                group_id="g1",
                agent_type="test",
                status="completed",
                completed_count=1,
                failed_count=0,
            )

        orchestrator._execute_group = mock_execute_group

        groups = [
            GroupConfig(group_id="g1", agent_type="test", node_ids=["n1"]),
            GroupConfig(group_id="g2", agent_type="test", node_ids=["n2"]),
        ]

        results = await orchestrator._execute_all_groups(
            session_id="test",
            canvas_path="test.canvas",
            groups=groups,
        )

        assert len(results) == 2
        assert results[0].status == "completed"
        assert results[1].status == "failed"
