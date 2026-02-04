# Canvas Learning System - WebSocket Connection Manager
# Story 33.2: WebSocket Real-time Updates
# ✅ Verified from docs/architecture/decisions/ADR-007-WEBSOCKET-BATCH-PROCESSING.md
# ✅ Verified from docs/stories/33.2.story.md
"""
WebSocket Connection Manager for intelligent parallel batch processing.

Manages WebSocket connections for real-time progress updates.
Supports multiple simultaneous connections per session.

Key Features:
- Thread-safe connection management via asyncio.Lock
- Per-session connection tracking
- Broadcast events to all connected clients
- Graceful disconnect handling

[Source: docs/stories/33.2.story.md - Task 2]
[Source: docs/architecture/decisions/ADR-007-WEBSOCKET-BATCH-PROCESSING.md]
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Set

from fastapi import WebSocket

from app.models.intelligent_parallel_models import (
    WebSocketMessage,
    create_ws_connected_event,
    create_ws_error_event,
    create_ws_ping_event,
)

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    WebSocket connection manager for intelligent parallel processing.

    Thread-safe management of WebSocket connections per session.
    Supports broadcasting events to all connected clients for a session.

    [Source: docs/stories/33.2.story.md - Task 2]
    [Source: docs/architecture/decisions/ADR-007-WEBSOCKET-BATCH-PROCESSING.md]

    Usage:
        manager = ConnectionManager()
        await manager.connect(session_id, websocket)
        await manager.broadcast_to_session(session_id, event)
        await manager.disconnect(session_id, websocket)
    """

    def __init__(self) -> None:
        """Initialize connection manager with empty connection registry."""
        # Dict[session_id, Set[WebSocket]] - multiple clients per session
        self._connections: Dict[str, Set[WebSocket]] = {}
        # Lock for thread-safe access
        self._lock = asyncio.Lock()
        # Track connection timestamps for timeout handling
        self._last_activity: Dict[str, datetime] = {}
        logger.info("ConnectionManager initialized")

    async def connect(
        self,
        session_id: str,
        websocket: WebSocket,
    ) -> bool:
        """
        Accept and register a new WebSocket connection.

        [Source: docs/stories/33.2.story.md - AC1, AC3]

        Args:
            session_id: Session ID to associate with connection
            websocket: WebSocket connection to register

        Returns:
            bool: True if connection accepted, False otherwise
        """
        async with self._lock:
            # Accept the WebSocket connection
            await websocket.accept()

            # Initialize session connection set if needed
            if session_id not in self._connections:
                self._connections[session_id] = set()

            # Add connection to session
            self._connections[session_id].add(websocket)
            self._last_activity[session_id] = datetime.now()

            connection_count = len(self._connections[session_id])
            logger.info(
                f"WebSocket connected: session={session_id}, "
                f"total_connections={connection_count}"
            )

        # Send connected event
        connected_event = create_ws_connected_event(session_id)
        await self._send_message(websocket, connected_event)

        return True

    async def disconnect(
        self,
        session_id: str,
        websocket: WebSocket,
    ) -> None:
        """
        Remove a WebSocket connection from the registry.

        [Source: docs/stories/33.2.story.md - AC3]

        Args:
            session_id: Session ID associated with connection
            websocket: WebSocket connection to remove
        """
        async with self._lock:
            if session_id in self._connections:
                self._connections[session_id].discard(websocket)

                # Clean up empty session
                if not self._connections[session_id]:
                    del self._connections[session_id]
                    if session_id in self._last_activity:
                        del self._last_activity[session_id]
                    logger.info(f"All connections closed for session: {session_id}")
                else:
                    connection_count = len(self._connections[session_id])
                    logger.info(
                        f"WebSocket disconnected: session={session_id}, "
                        f"remaining_connections={connection_count}"
                    )

    async def broadcast_to_session(
        self,
        session_id: str,
        message: WebSocketMessage,
    ) -> int:
        """
        Broadcast a message to all connected clients for a session.

        [Source: docs/stories/33.2.story.md - AC2, AC4]

        Args:
            session_id: Session ID to broadcast to
            message: WebSocketMessage to send

        Returns:
            int: Number of clients that received the message
        """
        async with self._lock:
            if session_id not in self._connections:
                logger.debug(f"No connections for session: {session_id}")
                return 0

            connections = list(self._connections[session_id])
            self._last_activity[session_id] = datetime.now()

        # Send to all connections (outside lock for better concurrency)
        sent_count = 0
        failed_connections: List[WebSocket] = []

        for websocket in connections:
            try:
                await self._send_message(websocket, message)
                sent_count += 1
            except Exception as e:
                logger.warning(
                    f"Failed to send to WebSocket in session {session_id}: {e}"
                )
                failed_connections.append(websocket)

        # Clean up failed connections
        if failed_connections:
            async with self._lock:
                if session_id in self._connections:
                    for ws in failed_connections:
                        self._connections[session_id].discard(ws)

        logger.debug(
            f"Broadcast to session {session_id}: "
            f"sent={sent_count}, failed={len(failed_connections)}"
        )
        return sent_count

    async def send_heartbeat(self, session_id: str) -> int:
        """
        Send heartbeat ping to all connections for a session.

        [Source: docs/stories/33.2.story.md - AC3]

        Args:
            session_id: Session ID to send heartbeat to

        Returns:
            int: Number of clients that received the ping
        """
        ping_event = create_ws_ping_event(session_id)
        return await self.broadcast_to_session(session_id, ping_event)

    async def send_error(
        self,
        session_id: str,
        error_message: str,
        recoverable: bool = True,
        retry_after: Optional[int] = None,
    ) -> int:
        """
        Send error event to all connections for a session.

        [Source: docs/stories/33.2.story.md - AC2, AC5]

        Args:
            session_id: Session ID to send error to
            error_message: Error message
            recoverable: Whether error is recoverable
            retry_after: Seconds to wait before retry

        Returns:
            int: Number of clients that received the error
        """
        error_event = create_ws_error_event(
            task_id=session_id,
            error_message=error_message,
            recoverable=recoverable,
            retry_after=retry_after,
        )
        return await self.broadcast_to_session(session_id, error_event)

    async def close_session_connections(
        self,
        session_id: str,
        reason: str = "Session completed",
    ) -> int:
        """
        Close all WebSocket connections for a session.

        [Source: docs/stories/33.2.story.md - AC3]

        Args:
            session_id: Session ID to close connections for
            reason: Reason for closing

        Returns:
            int: Number of connections closed
        """
        async with self._lock:
            if session_id not in self._connections:
                return 0

            connections = list(self._connections[session_id])
            del self._connections[session_id]
            if session_id in self._last_activity:
                del self._last_activity[session_id]

        # Close all connections
        closed_count = 0
        for websocket in connections:
            try:
                await websocket.close(code=1000, reason=reason)
                closed_count += 1
            except Exception as e:
                logger.warning(f"Error closing WebSocket: {e}")

        logger.info(
            f"Closed all connections for session {session_id}: count={closed_count}"
        )
        return closed_count

    def get_connection_count(self, session_id: str) -> int:
        """
        Get number of active connections for a session.

        Args:
            session_id: Session ID to check

        Returns:
            int: Number of active connections
        """
        return len(self._connections.get(session_id, set()))

    def get_all_session_ids(self) -> List[str]:
        """
        Get all session IDs with active connections.

        Returns:
            List[str]: List of session IDs
        """
        return list(self._connections.keys())

    def has_session(self, session_id: str) -> bool:
        """
        Check if a session has any active connections.

        Args:
            session_id: Session ID to check

        Returns:
            bool: True if session has connections
        """
        return session_id in self._connections

    def get_last_activity(self, session_id: str) -> Optional[datetime]:
        """
        Get last activity timestamp for a session.

        Args:
            session_id: Session ID to check

        Returns:
            Optional[datetime]: Last activity time or None
        """
        return self._last_activity.get(session_id)

    def get_metrics(self) -> dict:
        """
        Get connection metrics for monitoring.

        Returns comprehensive metrics for observability dashboards.

        [Source: QA Review 33.2 - Suggested improvement]

        Returns:
            dict: Metrics including:
                - total_sessions: Number of active sessions
                - total_connections: Total WebSocket connections across all sessions
                - connections_per_session: Dict of session_id -> connection count
                - oldest_session: Oldest active session info
                - newest_session: Newest active session info
        """
        total_connections = sum(
            len(conns) for conns in self._connections.values()
        )

        connections_per_session = {
            session_id: len(conns)
            for session_id, conns in self._connections.items()
        }

        oldest_session = None
        newest_session = None

        if self._last_activity:
            oldest_id = min(self._last_activity, key=self._last_activity.get)
            newest_id = max(self._last_activity, key=self._last_activity.get)

            oldest_session = {
                "session_id": oldest_id,
                "last_activity": self._last_activity[oldest_id].isoformat(),
                "connection_count": self.get_connection_count(oldest_id),
            }
            newest_session = {
                "session_id": newest_id,
                "last_activity": self._last_activity[newest_id].isoformat(),
                "connection_count": self.get_connection_count(newest_id),
            }

        return {
            "total_sessions": len(self._connections),
            "total_connections": total_connections,
            "connections_per_session": connections_per_session,
            "oldest_session": oldest_session,
            "newest_session": newest_session,
        }

    def get_health_status(self) -> dict:
        """
        Get health status for WebSocket subsystem.

        [Source: QA Review 33.2 - Suggested improvement]

        Returns:
            dict: Health status including:
                - status: "healthy" | "degraded" | "unhealthy"
                - total_sessions: Number of active sessions
                - total_connections: Total connections
                - warning: Optional warning message
        """
        metrics = self.get_metrics()
        total_sessions = metrics["total_sessions"]
        total_connections = metrics["total_connections"]

        # Define thresholds
        MAX_SESSIONS_WARNING = 100
        MAX_CONNECTIONS_WARNING = 500

        status = "healthy"
        warning = None

        if total_sessions > MAX_SESSIONS_WARNING:
            status = "degraded"
            warning = f"High session count: {total_sessions} (threshold: {MAX_SESSIONS_WARNING})"

        if total_connections > MAX_CONNECTIONS_WARNING:
            status = "degraded"
            warning = f"High connection count: {total_connections} (threshold: {MAX_CONNECTIONS_WARNING})"

        return {
            "status": status,
            "total_sessions": total_sessions,
            "total_connections": total_connections,
            "warning": warning,
        }

    async def cleanup_inactive_sessions(
        self,
        timeout_minutes: int = 10,
    ) -> List[str]:
        """
        Close connections for sessions inactive beyond timeout.

        [Source: docs/stories/33.2.story.md - AC3]

        Args:
            timeout_minutes: Inactivity timeout in minutes (default 10)

        Returns:
            List[str]: List of cleaned up session IDs
        """
        now = datetime.now()
        cleaned_sessions: List[str] = []

        async with self._lock:
            sessions_to_cleanup = []
            for session_id, last_activity in self._last_activity.items():
                inactive_minutes = (now - last_activity).total_seconds() / 60
                if inactive_minutes >= timeout_minutes:
                    sessions_to_cleanup.append(session_id)

        # Close connections outside lock
        for session_id in sessions_to_cleanup:
            await self.close_session_connections(
                session_id,
                reason=f"Inactivity timeout ({timeout_minutes} minutes)"
            )
            cleaned_sessions.append(session_id)

        if cleaned_sessions:
            logger.info(f"Cleaned up inactive sessions: {cleaned_sessions}")

        return cleaned_sessions

    async def _send_message(
        self,
        websocket: WebSocket,
        message: WebSocketMessage,
    ) -> None:
        """
        Send a message to a single WebSocket connection.

        Args:
            websocket: Target WebSocket
            message: Message to send
        """
        await websocket.send_json(message.model_dump(mode="json"))


# Singleton instance for dependency injection
# [Source: docs/stories/33.2.story.md - Implementation Notes #1]
_connection_manager: Optional[ConnectionManager] = None


def get_connection_manager() -> ConnectionManager:
    """
    Get singleton ConnectionManager instance.

    [Source: docs/stories/33.2.story.md - Implementation Notes #1]

    Returns:
        ConnectionManager: Singleton instance
    """
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = ConnectionManager()
    return _connection_manager


def reset_connection_manager() -> None:
    """
    Reset singleton for testing purposes.

    Warning: Only use in tests!
    """
    global _connection_manager
    _connection_manager = None
