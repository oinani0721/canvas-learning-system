# Canvas Learning System - Session Manager Service
# Story 33.3: Session Management Service
# Source: specs/api/parallel-api.openapi.yml:133-168
# Source: specs/data/parallel-task.schema.json
"""
SessionManager - Manages batch processing session lifecycle.

Features:
- Session creation with UUID4 identifiers (AC:1)
- State machine: pending → running → completed/failed/cancelled (AC:2)
- In-memory progress persistence with optional Redis adapter interface (AC:3)
- 30-minute session timeout with automatic cleanup (AC:4)
- Thread-safe session state updates (AC:5)
- Session metadata storage (AC:6)
- Progress percentage tracking (0-100%) (AC:7)
- Per-node result storage (AC:8)
"""

import asyncio
import structlog
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Protocol

from ..models.session_models import (
    NodeResult,
    SessionInfo,
    SessionStatus,
    VALID_TRANSITIONS,
    is_valid_transition,
)

logger = structlog.get_logger(__name__)

# Constants
SESSION_TIMEOUT_MINUTES = 30
CLEANUP_INTERVAL_SECONDS = 60  # Check every minute for expired sessions


class SessionStorageAdapter(Protocol):
    """
    Storage adapter interface for future Redis support.
    [Source: Story 33.3 Task 3.4]
    """

    async def save_session(self, session: SessionInfo) -> None:
        """Save session to storage."""
        ...

    async def get_session(self, session_id: str) -> Optional[SessionInfo]:
        """Get session from storage."""
        ...

    async def delete_session(self, session_id: str) -> bool:
        """Delete session from storage."""
        ...

    async def list_sessions(self) -> List[SessionInfo]:
        """List all sessions."""
        ...


class InMemoryStorageAdapter:
    """
    In-memory storage adapter (default implementation).
    [Source: Story 33.3 AC:3 - Progress persistence using in-memory dictionary]
    """

    def __init__(self):
        self._sessions: Dict[str, SessionInfo] = {}

    async def save_session(self, session: SessionInfo) -> None:
        """Save session to memory."""
        self._sessions[session.session_id] = session

    async def get_session(self, session_id: str) -> Optional[SessionInfo]:
        """Get session from memory."""
        return self._sessions.get(session_id)

    async def delete_session(self, session_id: str) -> bool:
        """Delete session from memory."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    async def list_sessions(self) -> List[SessionInfo]:
        """List all sessions."""
        return list(self._sessions.values())

    def clear(self) -> None:
        """Clear all sessions (for testing)."""
        self._sessions.clear()


class InvalidStateTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""

    def __init__(self, from_status: SessionStatus, to_status: SessionStatus):
        self.from_status = from_status
        self.to_status = to_status
        super().__init__(
            f"Invalid state transition from {from_status.value} to {to_status.value}"
        )


class SessionNotFoundError(Exception):
    """Raised when a session is not found."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        super().__init__(f"Session not found: {session_id}")


class SessionManager:
    """
    Session Manager for batch processing sessions.
    [Source: Story 33.3 - Singleton pattern from BackgroundTaskManager]

    Thread-safe session management with:
    - Singleton pattern
    - asyncio.Lock for concurrent access
    - Automatic cleanup of expired sessions
    """

    _instance: Optional["SessionManager"] = None
    _lock: asyncio.Lock = asyncio.Lock()

    def __new__(cls, *args, **kwargs):
        """
        Singleton pattern.
        [Source: Story 33.3 Task 2.1 - Follow BackgroundTaskManager pattern]
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, storage_adapter: Optional[SessionStorageAdapter] = None):
        """
        Initialize session manager.

        Args:
            storage_adapter: Optional storage adapter (defaults to in-memory)
        """
        # Avoid re-initialization
        if hasattr(self, "_initialized") and self._initialized:
            return

        self._storage = storage_adapter or InMemoryStorageAdapter()
        self._session_lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None
        self._initialized = True

        logger.info("session_manager_initialized")

    @classmethod
    def get_instance(cls) -> "SessionManager":
        """
        Get singleton instance.
        [Source: Story 33.3 Task 2.1]
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """
        Reset singleton (for testing only).
        [Source: BackgroundTaskManager pattern]
        """
        if cls._instance is not None:
            if isinstance(cls._instance._storage, InMemoryStorageAdapter):
                cls._instance._storage.clear()
            cls._instance._initialized = False
        cls._instance = None

    async def create_session(
        self,
        canvas_path: str,
        node_count: int,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Create a new session.
        [Source: Story 33.3 AC:1 - UUID4 generation]
        [Source: Story 33.3 AC:6 - Session metadata storage]

        Args:
            canvas_path: Path to the Canvas file
            node_count: Total number of nodes to process
            metadata: Additional session metadata

        Returns:
            str: Session ID (UUID4)
        """
        session_id = str(uuid.uuid4())
        now = datetime.now()

        session = SessionInfo(
            session_id=session_id,
            canvas_path=canvas_path,
            node_count=node_count,
            status=SessionStatus.PENDING,
            created_at=now,
            updated_at=now,
            metadata=metadata or {},
        )

        async with self._session_lock:
            await self._storage.save_session(session)

        logger.info("session_created", session_id=session_id, canvas_path=canvas_path, node_count=node_count)
        return session_id

    async def get_session(self, session_id: str) -> SessionInfo:
        """
        Get session by ID.
        [Source: Story 33.3 Task 3.3]

        Args:
            session_id: Session ID

        Returns:
            SessionInfo: Session information

        Raises:
            SessionNotFoundError: If session not found
        """
        async with self._session_lock:
            session = await self._storage.get_session(session_id)

        if session is None:
            raise SessionNotFoundError(session_id)

        return session

    async def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """
        Get session status as dictionary.
        [Source: Story 33.3 Task 3.3]

        Args:
            session_id: Session ID

        Returns:
            Dict: Session status dictionary
        """
        session = await self.get_session(session_id)
        return session.to_dict()

    async def transition_state(
        self,
        session_id: str,
        new_status: SessionStatus,
        error_message: Optional[str] = None,
    ) -> SessionInfo:
        """
        Transition session to a new state.
        [Source: Story 33.3 AC:2 - State machine implementation]
        [Source: Story 33.3 Task 2.3 - State machine transitions with validation]

        Args:
            session_id: Session ID
            new_status: Target status
            error_message: Error message (for failed states)

        Returns:
            SessionInfo: Updated session

        Raises:
            SessionNotFoundError: If session not found
            InvalidStateTransitionError: If transition is invalid
        """
        async with self._session_lock:
            session = await self._storage.get_session(session_id)

            if session is None:
                raise SessionNotFoundError(session_id)

            if not is_valid_transition(session.status, new_status):
                raise InvalidStateTransitionError(session.status, new_status)

            # Update session state
            now = datetime.now()
            session.status = new_status
            session.updated_at = now

            # Set timestamps based on transition
            if new_status == SessionStatus.RUNNING and session.started_at is None:
                session.started_at = now

            if new_status.is_terminal:
                session.completed_at = now

            if error_message:
                session.error_message = error_message

            await self._storage.save_session(session)

        logger.info("session_state_transitioned", session_id=session_id, new_status=new_status.value)
        return session

    async def update_progress(
        self,
        session_id: str,
        progress_percent: float,
    ) -> SessionInfo:
        """
        Update session progress.
        [Source: Story 33.3 AC:7 - Progress percentage tracking (0-100%)]
        [Source: Story 33.3 Task 3.1]

        Args:
            session_id: Session ID
            progress_percent: Progress percentage (0-100)

        Returns:
            SessionInfo: Updated session

        Raises:
            SessionNotFoundError: If session not found
        """
        async with self._session_lock:
            session = await self._storage.get_session(session_id)

            if session is None:
                raise SessionNotFoundError(session_id)

            # Only update progress if session is in running state
            if not session.status.allows_progress_update:
                logger.warning("progress_update_rejected", session_id=session_id, status=session.status.value)
                return session

            # Clamp progress to 0-100
            session.progress_percent = min(max(progress_percent, 0.0), 100.0)
            session.updated_at = datetime.now()

            await self._storage.save_session(session)

        logger.debug("session_progress_updated", session_id=session_id, progress_percent=progress_percent)
        return session

    async def add_node_result(
        self,
        session_id: str,
        node_id: str,
        status: str,
        result: Optional[Any] = None,
        error: Optional[str] = None,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
    ) -> SessionInfo:
        """
        Add a node result to the session.
        [Source: Story 33.3 AC:8 - Per-node result storage]
        [Source: Story 33.3 Task 3.2]

        Args:
            session_id: Session ID
            node_id: Node ID
            status: Node execution status ("success", "failed", "skipped")
            result: Node execution result
            error: Error message (if failed)
            started_at: When node execution started
            completed_at: When node execution completed

        Returns:
            SessionInfo: Updated session

        Raises:
            SessionNotFoundError: If session not found
        """
        async with self._session_lock:
            session = await self._storage.get_session(session_id)

            if session is None:
                raise SessionNotFoundError(session_id)

            now = datetime.now()

            # Calculate execution time
            execution_time_ms = None
            if started_at and completed_at:
                execution_time_ms = int((completed_at - started_at).total_seconds() * 1000)

            node_result = NodeResult(
                node_id=node_id,
                status=status,
                result=result,
                error=error,
                started_at=started_at,
                completed_at=completed_at,
                execution_time_ms=execution_time_ms,
            )

            session.node_results[node_id] = node_result
            session.updated_at = now

            # Update completed/failed counts
            if status == "success":
                session.completed_nodes = sum(
                    1 for r in session.node_results.values() if r.status == "success"
                )
            elif status == "failed":
                session.failed_nodes = sum(
                    1 for r in session.node_results.values() if r.status == "failed"
                )

            # Auto-calculate progress based on node results
            total_processed = len(session.node_results)
            if session.node_count > 0:
                session.progress_percent = (total_processed / session.node_count) * 100.0

            await self._storage.save_session(session)

        logger.debug("node_result_added", session_id=session_id, node_id=node_id, status=status)
        return session

    async def cancel_session(self, session_id: str) -> SessionInfo:
        """
        Cancel a session.

        Args:
            session_id: Session ID

        Returns:
            SessionInfo: Updated session
        """
        return await self.transition_state(session_id, SessionStatus.CANCELLED)

    def is_session_expired(self, session: SessionInfo) -> bool:
        """
        Check if session has expired.
        [Source: Story 33.3 AC:4 - Session timeout (30 minutes)]
        [Source: Story 33.3 Task 4.1]

        Args:
            session: Session info

        Returns:
            bool: True if session is expired
        """
        # Terminal sessions are considered expired based on completion time
        if session.status.is_terminal:
            reference_time = session.completed_at or session.updated_at
        else:
            # Running/pending sessions based on last update
            reference_time = session.updated_at

        timeout = timedelta(minutes=SESSION_TIMEOUT_MINUTES)
        return datetime.now() - reference_time > timeout

    async def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions.
        [Source: Story 33.3 AC:4 - Automatic cleanup of expired sessions]
        [Source: Story 33.3 Task 4.2]

        Returns:
            int: Number of sessions cleaned up
        """
        cleaned = 0

        async with self._session_lock:
            sessions = await self._storage.list_sessions()

            for session in sessions:
                if self.is_session_expired(session):
                    await self._storage.delete_session(session.session_id)
                    cleaned += 1
                    logger.debug("expired_session_cleaned", session_id=session.session_id)

        if cleaned > 0:
            logger.info("expired_sessions_cleanup_complete", cleaned_count=cleaned)

        return cleaned

    async def start_cleanup_scheduler(self) -> None:
        """
        Start the background cleanup scheduler.
        [Source: Story 33.3 Task 4.3 - Async background cleanup scheduler]
        [Source: Story 33.3 Task 4.4]
        """
        async def cleanup_loop():
            while True:
                try:
                    await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)
                    await self.cleanup_expired_sessions()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error("session_cleanup_error", error=str(e))

        self._cleanup_task = asyncio.create_task(cleanup_loop())
        logger.info("cleanup_scheduler_started")

    async def stop_cleanup_scheduler(self) -> None:
        """
        Stop the background cleanup scheduler.
        [Source: Story 33.3 Task 4.4]
        """
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
            logger.info("cleanup_scheduler_stopped")

    async def list_sessions(
        self,
        status: Optional[SessionStatus] = None,
    ) -> List[SessionInfo]:
        """
        List all sessions, optionally filtered by status.

        Args:
            status: Filter by status (optional)

        Returns:
            List of sessions
        """
        async with self._session_lock:
            sessions = await self._storage.list_sessions()

        if status is not None:
            sessions = [s for s in sessions if s.status == status]

        return sessions

    async def get_stats(self) -> dict:
        """
        Get session statistics for health monitoring.

        Returns:
            Dict with active_sessions and total_sessions counts.
        """
        async with self._session_lock:
            sessions = await self._storage.list_sessions()
        active = sum(
            1 for s in sessions
            if s.status in (SessionStatus.PENDING, SessionStatus.RUNNING)
        )
        return {"active_sessions": active, "total_sessions": len(sessions)}

    async def cleanup(self) -> None:
        """
        Clean up resources.
        [Source: Story 33.3 Dev Notes - Must support graceful shutdown]
        """
        await self.stop_cleanup_scheduler()

        async with self._session_lock:
            if isinstance(self._storage, InMemoryStorageAdapter):
                self._storage.clear()

        self._initialized = False
        logger.info("session_manager_cleanup_completed")
