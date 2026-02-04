# Canvas Learning System - WebSocket Endpoints
# Story 33.2: WebSocket Real-time Updates
# ✅ Verified from docs/architecture/decisions/ADR-007-WEBSOCKET-BATCH-PROCESSING.md
# ✅ Verified from specs/api/parallel-api.openapi.yml#L523-L559
"""
WebSocket endpoints for real-time progress updates.

Provides WebSocket endpoint for intelligent parallel batch processing:
- WS /ws/intelligent-parallel/{session_id} - Subscribe to session progress

Key Features:
- Session validation before connection accept
- Heartbeat ping every 30 seconds
- Auto-close on session completion
- Connection timeout after 10 minutes of inactivity

[Source: docs/stories/33.2.story.md - Task 1]
[Source: specs/api/parallel-api.openapi.yml#L523-L559]
"""

import asyncio
import logging
from typing import Optional

from fastapi import WebSocket, WebSocketDisconnect, status

from app.models.intelligent_parallel_models import create_ws_error_event
from app.services.websocket_manager import ConnectionManager, get_connection_manager

logger = logging.getLogger(__name__)

# Configuration constants
# [Source: docs/stories/33.2.story.md - AC3]
HEARTBEAT_INTERVAL_SECONDS = 30  # Heartbeat ping every 30 seconds
INACTIVITY_TIMEOUT_MINUTES = 10  # Connection timeout after 10 minutes
WEBSOCKET_CLOSE_NORMAL = 1000
WEBSOCKET_CLOSE_SESSION_NOT_FOUND = 4004


# Session validator function - to be injected from intelligent_parallel_service
# This allows checking if a session exists before accepting connection
_session_validator: Optional[callable] = None


def set_session_validator(validator: callable) -> None:
    """
    Set the session validator function.

    Called from IntelligentParallelService to inject session validation.

    [Source: docs/stories/33.2.story.md - AC1]

    Args:
        validator: Async function that takes session_id and returns bool
    """
    global _session_validator
    _session_validator = validator
    logger.info("Session validator set for WebSocket endpoint")


async def validate_session(session_id: str) -> bool:
    """
    Validate that a session exists.

    [Source: docs/stories/33.2.story.md - AC1]

    Args:
        session_id: Session ID to validate

    Returns:
        bool: True if session exists, False otherwise
    """
    if _session_validator is None:
        # No validator set - allow all connections (for testing)
        logger.warning("No session validator set, allowing connection")
        return True

    try:
        return await _session_validator(session_id)
    except Exception as e:
        logger.error(f"Session validation error: {e}")
        return False


async def websocket_intelligent_parallel(
    websocket: WebSocket,
    session_id: str,
    manager: Optional[ConnectionManager] = None,
) -> None:
    """
    WebSocket endpoint for intelligent parallel batch processing progress.

    [Source: docs/stories/33.2.story.md - Task 1, AC1, AC3]
    [Source: specs/api/parallel-api.openapi.yml#L523-L559]

    Connection Lifecycle:
    1. Validate session_id exists
    2. Accept WebSocket connection
    3. Send 'connected' event
    4. Start heartbeat task (ping every 30s)
    5. Listen for client messages (keep alive)
    6. Handle disconnect gracefully
    7. Auto-close on session completion

    Args:
        websocket: WebSocket connection
        session_id: Session ID to subscribe to
        manager: ConnectionManager instance (optional, uses singleton if None)
    """
    if manager is None:
        manager = get_connection_manager()

    # AC1: Validate session exists before accepting
    session_valid = await validate_session(session_id)
    if not session_valid:
        logger.warning(f"WebSocket rejected: session not found: {session_id}")
        # Close with custom code 4004 for session not found
        await websocket.close(
            code=WEBSOCKET_CLOSE_SESSION_NOT_FOUND,
            reason=f"Session '{session_id}' not found"
        )
        return

    # Accept connection and register
    await manager.connect(session_id, websocket)
    logger.info(f"WebSocket accepted for session: {session_id}")

    # AC3: Start heartbeat task
    heartbeat_task = asyncio.create_task(
        _heartbeat_loop(manager, session_id, websocket)
    )

    try:
        # Main message receive loop
        while True:
            try:
                # Wait for client messages with timeout
                # This keeps the connection alive and allows detection of client disconnect
                message = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=float(INACTIVITY_TIMEOUT_MINUTES * 60)
                )
                # Update activity timestamp is handled in manager
                logger.debug(f"Received message from client: {message[:100]}")

            except asyncio.TimeoutError:
                # AC3: Connection timeout after 10 minutes of inactivity
                logger.info(
                    f"WebSocket timeout for session {session_id} "
                    f"(inactive for {INACTIVITY_TIMEOUT_MINUTES} minutes)"
                )
                # Send error event before closing
                error_event = create_ws_error_event(
                    task_id=session_id,
                    error_message=f"Connection timeout after {INACTIVITY_TIMEOUT_MINUTES} minutes of inactivity",
                    recoverable=True,
                    retry_after=5,
                )
                try:
                    await websocket.send_json(error_event.model_dump(mode="json"))
                except Exception:
                    pass
                break

    except WebSocketDisconnect:
        # AC3: Graceful disconnect on client close
        logger.info(f"WebSocket client disconnected: session={session_id}")

    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
        # Try to send error event
        try:
            error_event = create_ws_error_event(
                task_id=session_id,
                error_message=str(e),
                error_type=type(e).__name__,
                recoverable=True,
                retry_after=5,
            )
            await websocket.send_json(error_event.model_dump(mode="json"))
        except Exception:
            pass

    finally:
        # Cleanup
        heartbeat_task.cancel()
        try:
            await heartbeat_task
        except asyncio.CancelledError:
            pass

        await manager.disconnect(session_id, websocket)
        logger.info(f"WebSocket cleanup complete for session: {session_id}")


async def _heartbeat_loop(
    manager: ConnectionManager,
    session_id: str,
    websocket: WebSocket,
) -> None:
    """
    Send heartbeat pings at regular intervals.

    [Source: docs/stories/33.2.story.md - AC3, Implementation Notes #2]

    Args:
        manager: ConnectionManager instance
        session_id: Session ID
        websocket: WebSocket connection
    """
    try:
        while True:
            await asyncio.sleep(HEARTBEAT_INTERVAL_SECONDS)

            # Send ping to this specific connection
            try:
                from app.models.intelligent_parallel_models import create_ws_ping_event
                ping_event = create_ws_ping_event(session_id)
                await websocket.send_json(ping_event.model_dump(mode="json"))
                logger.debug(f"Heartbeat sent for session: {session_id}")
            except Exception as e:
                logger.warning(f"Heartbeat failed for session {session_id}: {e}")
                break

    except asyncio.CancelledError:
        logger.debug(f"Heartbeat loop cancelled for session: {session_id}")
        raise


# Dependency injection helper for FastAPI
def get_websocket_manager() -> ConnectionManager:
    """
    FastAPI dependency for ConnectionManager.

    [Source: docs/stories/33.2.story.md - Implementation Notes #1]

    Returns:
        ConnectionManager: Singleton instance
    """
    return get_connection_manager()
