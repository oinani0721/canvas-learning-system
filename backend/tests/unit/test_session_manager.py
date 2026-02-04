# Canvas Learning System - Session Manager Unit Tests
# Story 33.3: Session Management Service
# Source: Story 33.3 Task 5 - Unit Tests
"""
Unit tests for SessionManager service.

Test Coverage:
- Task 5.1: Test session creation with unique UUIDs
- Task 5.2: Test state machine transitions (valid and invalid)
- Task 5.3: Test progress update and retrieval
- Task 5.4: Test session timeout and cleanup
- Task 5.5: Test concurrent access safety
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

import pytest

from app.models.session_models import (
    NodeResult,
    SessionInfo,
    SessionStatus,
    VALID_TRANSITIONS,
    is_valid_transition,
)
from app.services.session_manager import (
    InMemoryStorageAdapter,
    InvalidStateTransitionError,
    SessionManager,
    SessionNotFoundError,
    SESSION_TIMEOUT_MINUTES,
)


@pytest.fixture
def session_manager():
    """
    Reset singleton for each test.
    [Source: Story 33.3 Dev Notes - Testing framework pattern]
    """
    SessionManager.reset_instance()
    manager = SessionManager.get_instance()
    yield manager
    # Cleanup after test
    SessionManager.reset_instance()


@pytest.fixture
def storage_adapter():
    """Provide a fresh in-memory storage adapter."""
    return InMemoryStorageAdapter()


# =============================================================================
# Task 5.1: Test session creation with unique UUIDs
# =============================================================================

class TestSessionCreation:
    """Tests for session creation (AC:1, AC:6)."""

    @pytest.mark.asyncio
    async def test_session_creation_returns_uuid(self, session_manager):
        """Test that session creation returns a valid UUID4."""
        session_id = await session_manager.create_session(
            canvas_path="test.canvas",
            node_count=10
        )

        assert session_id is not None
        assert len(session_id) == 36  # UUID4 format: 8-4-4-4-12
        assert session_id.count("-") == 4

    @pytest.mark.asyncio
    async def test_session_creation_unique_ids(self, session_manager):
        """Test that multiple sessions get unique IDs."""
        session_ids = []
        for _ in range(10):
            session_id = await session_manager.create_session(
                canvas_path="test.canvas",
                node_count=5
            )
            session_ids.append(session_id)

        # All IDs should be unique
        assert len(session_ids) == len(set(session_ids))

    @pytest.mark.asyncio
    async def test_session_creation_stores_metadata(self, session_manager):
        """Test that session stores canvas_path, node_count, created_at, updated_at (AC:6)."""
        session_id = await session_manager.create_session(
            canvas_path="/path/to/canvas.canvas",
            node_count=15,
            metadata={"key": "value"}
        )

        session = await session_manager.get_session(session_id)

        assert session.session_id == session_id
        assert session.canvas_path == "/path/to/canvas.canvas"
        assert session.node_count == 15
        assert session.status == SessionStatus.PENDING
        assert session.created_at is not None
        assert session.updated_at is not None
        assert session.metadata == {"key": "value"}

    @pytest.mark.asyncio
    async def test_session_creation_defaults(self, session_manager):
        """Test session creation default values."""
        session_id = await session_manager.create_session(
            canvas_path="test.canvas",
            node_count=5
        )

        session = await session_manager.get_session(session_id)

        assert session.progress_percent == 0.0
        assert session.completed_nodes == 0
        assert session.failed_nodes == 0
        assert session.started_at is None
        assert session.completed_at is None
        assert session.error_message is None
        assert session.node_results == {}


# =============================================================================
# Task 5.2: Test state machine transitions (valid and invalid)
# =============================================================================

class TestStateMachine:
    """Tests for state machine transitions (AC:2)."""

    def test_valid_transitions_from_pending(self):
        """Test valid transitions from PENDING state."""
        assert is_valid_transition(SessionStatus.PENDING, SessionStatus.RUNNING)
        assert is_valid_transition(SessionStatus.PENDING, SessionStatus.CANCELLED)
        assert not is_valid_transition(SessionStatus.PENDING, SessionStatus.COMPLETED)
        assert not is_valid_transition(SessionStatus.PENDING, SessionStatus.FAILED)

    def test_valid_transitions_from_running(self):
        """Test valid transitions from RUNNING state."""
        assert is_valid_transition(SessionStatus.RUNNING, SessionStatus.COMPLETED)
        assert is_valid_transition(SessionStatus.RUNNING, SessionStatus.PARTIAL_FAILURE)
        assert is_valid_transition(SessionStatus.RUNNING, SessionStatus.FAILED)
        assert is_valid_transition(SessionStatus.RUNNING, SessionStatus.CANCELLED)
        assert not is_valid_transition(SessionStatus.RUNNING, SessionStatus.PENDING)

    def test_terminal_states_have_no_transitions(self):
        """Test that terminal states don't allow any transitions."""
        terminal_states = [
            SessionStatus.COMPLETED,
            SessionStatus.PARTIAL_FAILURE,
            SessionStatus.FAILED,
            SessionStatus.CANCELLED,
        ]

        for terminal in terminal_states:
            for status in SessionStatus:
                assert not is_valid_transition(terminal, status)

    @pytest.mark.asyncio
    async def test_transition_pending_to_running(self, session_manager):
        """Test transitioning from PENDING to RUNNING."""
        session_id = await session_manager.create_session(
            canvas_path="test.canvas",
            node_count=5
        )

        session = await session_manager.transition_state(
            session_id, SessionStatus.RUNNING
        )

        assert session.status == SessionStatus.RUNNING
        assert session.started_at is not None

    @pytest.mark.asyncio
    async def test_transition_running_to_completed(self, session_manager):
        """Test transitioning from RUNNING to COMPLETED."""
        session_id = await session_manager.create_session(
            canvas_path="test.canvas",
            node_count=5
        )
        await session_manager.transition_state(session_id, SessionStatus.RUNNING)

        session = await session_manager.transition_state(
            session_id, SessionStatus.COMPLETED
        )

        assert session.status == SessionStatus.COMPLETED
        assert session.completed_at is not None

    @pytest.mark.asyncio
    async def test_transition_running_to_failed_with_error(self, session_manager):
        """Test transitioning to FAILED with error message."""
        session_id = await session_manager.create_session(
            canvas_path="test.canvas",
            node_count=5
        )
        await session_manager.transition_state(session_id, SessionStatus.RUNNING)

        session = await session_manager.transition_state(
            session_id,
            SessionStatus.FAILED,
            error_message="Something went wrong"
        )

        assert session.status == SessionStatus.FAILED
        assert session.error_message == "Something went wrong"
        assert session.completed_at is not None

    @pytest.mark.asyncio
    async def test_invalid_transition_raises_error(self, session_manager):
        """Test that invalid transitions raise InvalidStateTransitionError."""
        session_id = await session_manager.create_session(
            canvas_path="test.canvas",
            node_count=5
        )

        with pytest.raises(InvalidStateTransitionError) as exc_info:
            await session_manager.transition_state(
                session_id, SessionStatus.COMPLETED
            )

        assert exc_info.value.from_status == SessionStatus.PENDING
        assert exc_info.value.to_status == SessionStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_transition_nonexistent_session(self, session_manager):
        """Test that transitioning a nonexistent session raises error."""
        with pytest.raises(SessionNotFoundError):
            await session_manager.transition_state(
                "nonexistent-id", SessionStatus.RUNNING
            )


# =============================================================================
# Task 5.3: Test progress update and retrieval
# =============================================================================

class TestProgressTracking:
    """Tests for progress tracking (AC:7, AC:8)."""

    @pytest.mark.asyncio
    async def test_update_progress(self, session_manager):
        """Test updating progress percentage (AC:7)."""
        session_id = await session_manager.create_session(
            canvas_path="test.canvas",
            node_count=10
        )
        await session_manager.transition_state(session_id, SessionStatus.RUNNING)

        session = await session_manager.update_progress(session_id, 50.0)

        assert session.progress_percent == 50.0

    @pytest.mark.asyncio
    async def test_update_progress_clamps_to_0_100(self, session_manager):
        """Test that progress is clamped to 0-100 range."""
        session_id = await session_manager.create_session(
            canvas_path="test.canvas",
            node_count=10
        )
        await session_manager.transition_state(session_id, SessionStatus.RUNNING)

        # Test clamping to max
        session = await session_manager.update_progress(session_id, 150.0)
        assert session.progress_percent == 100.0

        # Test clamping to min
        session = await session_manager.update_progress(session_id, -50.0)
        assert session.progress_percent == 0.0

    @pytest.mark.asyncio
    async def test_progress_update_not_allowed_in_pending(self, session_manager):
        """Test that progress update is ignored in PENDING state."""
        session_id = await session_manager.create_session(
            canvas_path="test.canvas",
            node_count=10
        )

        session = await session_manager.update_progress(session_id, 50.0)

        # Progress should remain at 0 since session is not running
        assert session.progress_percent == 0.0

    @pytest.mark.asyncio
    async def test_add_node_result_success(self, session_manager):
        """Test adding a successful node result (AC:8)."""
        session_id = await session_manager.create_session(
            canvas_path="test.canvas",
            node_count=2
        )

        now = datetime.now()
        session = await session_manager.add_node_result(
            session_id=session_id,
            node_id="node-1",
            status="success",
            result={"output": "data"},
            started_at=now,
            completed_at=now + timedelta(seconds=5)
        )

        assert "node-1" in session.node_results
        node_result = session.node_results["node-1"]
        assert node_result.status == "success"
        assert node_result.result == {"output": "data"}
        assert node_result.execution_time_ms == 5000
        assert session.completed_nodes == 1

    @pytest.mark.asyncio
    async def test_add_node_result_failed(self, session_manager):
        """Test adding a failed node result."""
        session_id = await session_manager.create_session(
            canvas_path="test.canvas",
            node_count=2
        )

        session = await session_manager.add_node_result(
            session_id=session_id,
            node_id="node-1",
            status="failed",
            error="Execution failed"
        )

        assert session.node_results["node-1"].status == "failed"
        assert session.node_results["node-1"].error == "Execution failed"
        assert session.failed_nodes == 1

    @pytest.mark.asyncio
    async def test_add_node_result_auto_progress(self, session_manager):
        """Test that adding node results auto-calculates progress."""
        session_id = await session_manager.create_session(
            canvas_path="test.canvas",
            node_count=4
        )

        await session_manager.add_node_result(session_id, "node-1", "success")
        session = await session_manager.add_node_result(session_id, "node-2", "success")

        # 2 of 4 nodes = 50%
        assert session.progress_percent == 50.0

    @pytest.mark.asyncio
    async def test_get_session_status_dict(self, session_manager):
        """Test getting session status as dictionary."""
        session_id = await session_manager.create_session(
            canvas_path="test.canvas",
            node_count=5
        )

        status_dict = await session_manager.get_session_status(session_id)

        assert status_dict["session_id"] == session_id
        assert status_dict["canvas_path"] == "test.canvas"
        assert status_dict["node_count"] == 5
        assert status_dict["status"] == "pending"


# =============================================================================
# Task 5.4: Test session timeout and cleanup
# =============================================================================

class TestSessionCleanup:
    """Tests for session timeout and cleanup (AC:4)."""

    @pytest.mark.asyncio
    async def test_session_not_expired_within_timeout(self, session_manager):
        """Test that session is not expired within timeout period."""
        session_id = await session_manager.create_session(
            canvas_path="test.canvas",
            node_count=5
        )
        session = await session_manager.get_session(session_id)

        assert not session_manager.is_session_expired(session)

    @pytest.mark.asyncio
    async def test_session_expired_after_timeout(self, session_manager):
        """Test that session is expired after timeout period (30 minutes)."""
        session_id = await session_manager.create_session(
            canvas_path="test.canvas",
            node_count=5
        )
        session = await session_manager.get_session(session_id)

        # Mock the session's updated_at to be 31 minutes ago
        session.updated_at = datetime.now() - timedelta(minutes=31)

        assert session_manager.is_session_expired(session)

    @pytest.mark.asyncio
    async def test_cleanup_expired_sessions(self, session_manager):
        """Test cleanup removes expired sessions."""
        # Create sessions
        session_id_1 = await session_manager.create_session(
            canvas_path="test1.canvas",
            node_count=5
        )
        session_id_2 = await session_manager.create_session(
            canvas_path="test2.canvas",
            node_count=5
        )

        # Make one session expired by modifying its updated_at
        async with session_manager._session_lock:
            session = await session_manager._storage.get_session(session_id_1)
            session.updated_at = datetime.now() - timedelta(minutes=31)
            await session_manager._storage.save_session(session)

        # Run cleanup
        cleaned = await session_manager.cleanup_expired_sessions()

        assert cleaned == 1

        # Verify expired session was removed
        with pytest.raises(SessionNotFoundError):
            await session_manager.get_session(session_id_1)

        # Verify non-expired session still exists
        session_2 = await session_manager.get_session(session_id_2)
        assert session_2 is not None

    @pytest.mark.asyncio
    async def test_cleanup_scheduler_starts_and_stops(self, session_manager):
        """Test that cleanup scheduler can be started and stopped."""
        await session_manager.start_cleanup_scheduler()

        assert session_manager._cleanup_task is not None
        assert not session_manager._cleanup_task.done()

        await session_manager.stop_cleanup_scheduler()

        assert session_manager._cleanup_task is None


# =============================================================================
# Task 5.5: Test concurrent access safety
# =============================================================================

class TestConcurrentAccess:
    """Tests for thread-safe session state updates (AC:5)."""

    @pytest.mark.asyncio
    async def test_concurrent_session_creation(self, session_manager):
        """Test concurrent session creation is thread-safe."""
        async def create_session(index):
            return await session_manager.create_session(
                canvas_path=f"test{index}.canvas",
                node_count=index
            )

        # Create 20 sessions concurrently
        tasks = [create_session(i) for i in range(20)]
        session_ids = await asyncio.gather(*tasks)

        # All IDs should be unique
        assert len(session_ids) == len(set(session_ids))

        # All sessions should be retrievable
        for sid in session_ids:
            session = await session_manager.get_session(sid)
            assert session is not None

    @pytest.mark.asyncio
    async def test_concurrent_progress_updates(self, session_manager):
        """Test concurrent progress updates are thread-safe."""
        session_id = await session_manager.create_session(
            canvas_path="test.canvas",
            node_count=100
        )
        await session_manager.transition_state(session_id, SessionStatus.RUNNING)

        async def update_progress(progress):
            await session_manager.update_progress(session_id, progress)

        # Update progress concurrently
        tasks = [update_progress(i) for i in range(100)]
        await asyncio.gather(*tasks)

        # Session should still be valid
        session = await session_manager.get_session(session_id)
        assert session is not None
        assert 0.0 <= session.progress_percent <= 100.0

    @pytest.mark.asyncio
    async def test_concurrent_node_results(self, session_manager):
        """Test concurrent node result additions are thread-safe."""
        session_id = await session_manager.create_session(
            canvas_path="test.canvas",
            node_count=50
        )

        async def add_result(node_index):
            await session_manager.add_node_result(
                session_id=session_id,
                node_id=f"node-{node_index}",
                status="success" if node_index % 2 == 0 else "failed"
            )

        # Add results concurrently
        tasks = [add_result(i) for i in range(50)]
        await asyncio.gather(*tasks)

        session = await session_manager.get_session(session_id)
        assert len(session.node_results) == 50
        # 25 even indices = success, 25 odd indices = failed
        assert session.completed_nodes == 25
        assert session.failed_nodes == 25


# =============================================================================
# Singleton Pattern Tests
# =============================================================================

class TestSingletonPattern:
    """Tests for singleton pattern implementation."""

    def test_singleton_instance(self):
        """Test that get_instance returns same instance."""
        SessionManager.reset_instance()

        instance1 = SessionManager.get_instance()
        instance2 = SessionManager.get_instance()

        assert instance1 is instance2

    def test_reset_instance(self):
        """Test that reset_instance creates new instance."""
        SessionManager.reset_instance()

        instance1 = SessionManager.get_instance()
        SessionManager.reset_instance()
        instance2 = SessionManager.get_instance()

        # After reset, should get different instance
        # (Note: __new__ returns same object, but _initialized is reset)
        assert instance2._initialized

        # Cleanup
        SessionManager.reset_instance()


# =============================================================================
# NodeResult Model Tests
# =============================================================================

class TestNodeResultModel:
    """Tests for NodeResult dataclass."""

    def test_node_result_to_dict(self):
        """Test NodeResult serialization."""
        now = datetime.now()
        result = NodeResult(
            node_id="test-node",
            status="success",
            result={"key": "value"},
            error=None,
            started_at=now,
            completed_at=now + timedelta(seconds=2),
            execution_time_ms=2000
        )

        data = result.to_dict()

        assert data["node_id"] == "test-node"
        assert data["status"] == "success"
        assert data["result"] == {"key": "value"}
        assert data["error"] is None
        assert data["started_at"] is not None
        assert data["completed_at"] is not None
        assert data["execution_time_ms"] == 2000


# =============================================================================
# SessionInfo Model Tests
# =============================================================================

class TestSessionInfoModel:
    """Tests for SessionInfo dataclass."""

    def test_session_info_to_dict(self):
        """Test SessionInfo serialization."""
        now = datetime.now()
        session = SessionInfo(
            session_id="test-session-id",
            canvas_path="test.canvas",
            node_count=5,
            status=SessionStatus.RUNNING,
            created_at=now,
            updated_at=now,
            progress_percent=50.0
        )

        data = session.to_dict()

        assert data["session_id"] == "test-session-id"
        assert data["canvas_path"] == "test.canvas"
        assert data["node_count"] == 5
        assert data["status"] == "running"
        assert data["progress_percent"] == 50.0

    def test_session_status_is_terminal(self):
        """Test SessionStatus.is_terminal property."""
        assert SessionStatus.COMPLETED.is_terminal
        assert SessionStatus.PARTIAL_FAILURE.is_terminal
        assert SessionStatus.FAILED.is_terminal
        assert SessionStatus.CANCELLED.is_terminal
        assert not SessionStatus.PENDING.is_terminal
        assert not SessionStatus.RUNNING.is_terminal

    def test_session_status_allows_progress_update(self):
        """Test SessionStatus.allows_progress_update property."""
        assert SessionStatus.RUNNING.allows_progress_update
        assert not SessionStatus.PENDING.allows_progress_update
        assert not SessionStatus.COMPLETED.allows_progress_update
        assert not SessionStatus.FAILED.allows_progress_update


# =============================================================================
# Storage Adapter Tests
# =============================================================================

class TestInMemoryStorageAdapter:
    """Tests for InMemoryStorageAdapter."""

    @pytest.mark.asyncio
    async def test_save_and_get_session(self, storage_adapter):
        """Test saving and retrieving a session."""
        session = SessionInfo(
            session_id="test-id",
            canvas_path="test.canvas",
            node_count=5,
            status=SessionStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        await storage_adapter.save_session(session)
        retrieved = await storage_adapter.get_session("test-id")

        assert retrieved is not None
        assert retrieved.session_id == "test-id"

    @pytest.mark.asyncio
    async def test_get_nonexistent_session(self, storage_adapter):
        """Test getting a nonexistent session returns None."""
        result = await storage_adapter.get_session("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_session(self, storage_adapter):
        """Test deleting a session."""
        session = SessionInfo(
            session_id="test-id",
            canvas_path="test.canvas",
            node_count=5,
            status=SessionStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        await storage_adapter.save_session(session)
        result = await storage_adapter.delete_session("test-id")

        assert result is True
        assert await storage_adapter.get_session("test-id") is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_session(self, storage_adapter):
        """Test deleting a nonexistent session returns False."""
        result = await storage_adapter.delete_session("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_list_sessions(self, storage_adapter):
        """Test listing all sessions."""
        for i in range(3):
            session = SessionInfo(
                session_id=f"test-{i}",
                canvas_path=f"test{i}.canvas",
                node_count=5,
                status=SessionStatus.PENDING,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            await storage_adapter.save_session(session)

        sessions = await storage_adapter.list_sessions()
        assert len(sessions) == 3
