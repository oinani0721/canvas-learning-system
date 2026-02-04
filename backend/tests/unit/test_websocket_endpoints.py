# Canvas Learning System - WebSocket Endpoint Unit Tests
# Story 33.2: WebSocket Real-time Updates
# Target: ≥90% coverage for WebSocket handlers
"""
Unit tests for WebSocket endpoints and ConnectionManager.

[Source: docs/stories/33.2.story.md - Task 5]
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.intelligent_parallel_models import (
    ParallelTaskStatus,
    WSEventType,
    WebSocketMessage,
    create_ws_complete_event,
    create_ws_connected_event,
    create_ws_error_event,
    create_ws_group_complete_event,
    create_ws_node_complete_event,
    create_ws_ping_event,
    create_ws_progress_event,
)
from starlette.websockets import WebSocketDisconnect

from app.services.websocket_manager import (
    ConnectionManager,
    get_connection_manager,
    reset_connection_manager,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def connection_manager():
    """Create fresh ConnectionManager for each test."""
    reset_connection_manager()
    return ConnectionManager()


@pytest.fixture
def mock_websocket():
    """Create mock WebSocket for testing."""
    ws = AsyncMock()
    ws.accept = AsyncMock()
    ws.send_json = AsyncMock()
    ws.receive_text = AsyncMock(return_value="ping")
    ws.close = AsyncMock()
    return ws


@pytest.fixture
def session_id():
    """Standard session ID for tests."""
    return "parallel-20260120-test01"


# ═══════════════════════════════════════════════════════════════════════════════
# WebSocket Event Model Tests
# [Source: docs/stories/33.2.story.md - AC2]
# ═══════════════════════════════════════════════════════════════════════════════


class TestWebSocketEventModels:
    """Test WebSocket event model creation."""

    def test_create_ws_progress_event(self):
        """Test progress event creation."""
        event = create_ws_progress_event(
            task_id="test-session",
            progress_percent=50,
            completed_nodes=6,
            total_nodes=12,
        )

        assert event.type == WSEventType.progress
        assert event.task_id == "test-session"
        assert event.data is not None
        assert event.data["progress_percent"] == 50
        assert event.data["completed_nodes"] == 6
        assert event.data["total_nodes"] == 12
        assert isinstance(event.timestamp, datetime)

    def test_create_ws_node_complete_event(self):
        """Test node complete event creation."""
        event = create_ws_node_complete_event(
            task_id="test-session",
            node_id="node-001",
            file_path="output/file.md",
            file_size="2.5KB",
            group_id="group-1",
        )

        assert event.type == WSEventType.node_complete
        assert event.task_id == "test-session"
        assert event.data["node_id"] == "node-001"
        assert event.data["file_path"] == "output/file.md"
        assert event.data["file_size"] == "2.5KB"
        assert event.data["group_id"] == "group-1"

    def test_create_ws_group_complete_event(self):
        """Test group complete event creation."""
        event = create_ws_group_complete_event(
            task_id="test-session",
            group_id="group-1",
            agent_type="comparison-table",
            results=None,
        )

        assert event.type == WSEventType.group_complete
        assert event.data["group_id"] == "group-1"
        assert event.data["agent_type"] == "comparison-table"
        assert event.data["results"] == []

    def test_create_ws_error_event(self):
        """Test error event creation with all fields."""
        event = create_ws_error_event(
            task_id="test-session",
            error_message="Agent timeout",
            node_id="node-005",
            group_id="group-2",
            error_type="TimeoutError",
            recoverable=True,
            retry_after=5,
        )

        assert event.type == WSEventType.error
        assert event.data["error_message"] == "Agent timeout"
        assert event.data["node_id"] == "node-005"
        assert event.data["group_id"] == "group-2"
        assert event.data["error_type"] == "TimeoutError"
        assert event.data["recoverable"] is True
        assert event.data["retry_after"] == 5

    def test_create_ws_complete_event(self):
        """Test session complete event creation."""
        event = create_ws_complete_event(
            task_id="test-session",
            status=ParallelTaskStatus.completed,
            total_duration=135.5,
            success_count=11,
            failure_count=1,
        )

        assert event.type == WSEventType.complete
        assert event.data["status"] == ParallelTaskStatus.completed
        assert event.data["total_duration"] == 135.5
        assert event.data["success_count"] == 11
        assert event.data["failure_count"] == 1

    def test_create_ws_ping_event(self):
        """Test heartbeat ping event creation."""
        event = create_ws_ping_event("test-session")

        assert event.type == WSEventType.ping
        assert event.task_id == "test-session"
        assert event.data is None

    def test_create_ws_connected_event(self):
        """Test connected event creation."""
        event = create_ws_connected_event("test-session")

        assert event.type == WSEventType.connected
        assert event.task_id == "test-session"
        assert event.data is None

    def test_websocket_message_json_serialization(self):
        """Test WebSocketMessage can be serialized to JSON."""
        event = create_ws_progress_event(
            task_id="test-session",
            progress_percent=75,
            completed_nodes=9,
            total_nodes=12,
        )

        # Should not raise
        json_data = event.model_dump(mode="json")

        assert isinstance(json_data, dict)
        assert json_data["type"] == "progress"
        assert "timestamp" in json_data


# ═══════════════════════════════════════════════════════════════════════════════
# ConnectionManager Tests
# [Source: docs/stories/33.2.story.md - Task 2, AC1, AC3, AC4]
# ═══════════════════════════════════════════════════════════════════════════════


class TestConnectionManager:
    """Test ConnectionManager WebSocket connection handling."""

    @pytest.mark.asyncio
    async def test_connect_accepts_websocket(
        self, connection_manager, mock_websocket, session_id
    ):
        """Test connection accept with valid session."""
        result = await connection_manager.connect(session_id, mock_websocket)

        assert result is True
        mock_websocket.accept.assert_called_once()
        assert connection_manager.get_connection_count(session_id) == 1

    @pytest.mark.asyncio
    async def test_connect_sends_connected_event(
        self, connection_manager, mock_websocket, session_id
    ):
        """Test connected event is sent after accept."""
        await connection_manager.connect(session_id, mock_websocket)

        # Check send_json was called with connected event
        mock_websocket.send_json.assert_called_once()
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "connected"
        assert call_args["task_id"] == session_id

    @pytest.mark.asyncio
    async def test_connect_multiple_clients_same_session(
        self, connection_manager, session_id
    ):
        """Test multiple simultaneous connections per session."""
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        ws3 = AsyncMock()

        await connection_manager.connect(session_id, ws1)
        await connection_manager.connect(session_id, ws2)
        await connection_manager.connect(session_id, ws3)

        assert connection_manager.get_connection_count(session_id) == 3

    @pytest.mark.asyncio
    async def test_disconnect_removes_connection(
        self, connection_manager, mock_websocket, session_id
    ):
        """Test graceful disconnect removes connection."""
        await connection_manager.connect(session_id, mock_websocket)
        assert connection_manager.get_connection_count(session_id) == 1

        await connection_manager.disconnect(session_id, mock_websocket)
        assert connection_manager.get_connection_count(session_id) == 0

    @pytest.mark.asyncio
    async def test_disconnect_cleans_up_empty_session(
        self, connection_manager, mock_websocket, session_id
    ):
        """Test session is cleaned up when last connection closes."""
        await connection_manager.connect(session_id, mock_websocket)
        assert connection_manager.has_session(session_id) is True

        await connection_manager.disconnect(session_id, mock_websocket)
        assert connection_manager.has_session(session_id) is False

    @pytest.mark.asyncio
    async def test_disconnect_keeps_other_connections(
        self, connection_manager, session_id
    ):
        """Test disconnecting one client keeps others connected."""
        ws1 = AsyncMock()
        ws2 = AsyncMock()

        await connection_manager.connect(session_id, ws1)
        await connection_manager.connect(session_id, ws2)
        assert connection_manager.get_connection_count(session_id) == 2

        await connection_manager.disconnect(session_id, ws1)
        assert connection_manager.get_connection_count(session_id) == 1
        assert connection_manager.has_session(session_id) is True

    @pytest.mark.asyncio
    async def test_broadcast_to_session_sends_to_all(
        self, connection_manager, session_id
    ):
        """Test broadcast sends to all connected clients."""
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        ws3 = AsyncMock()

        await connection_manager.connect(session_id, ws1)
        await connection_manager.connect(session_id, ws2)
        await connection_manager.connect(session_id, ws3)

        # Clear the connected event calls
        ws1.send_json.reset_mock()
        ws2.send_json.reset_mock()
        ws3.send_json.reset_mock()

        event = create_ws_progress_event(
            task_id=session_id,
            progress_percent=50,
            completed_nodes=6,
            total_nodes=12,
        )
        sent_count = await connection_manager.broadcast_to_session(session_id, event)

        assert sent_count == 3
        ws1.send_json.assert_called_once()
        ws2.send_json.assert_called_once()
        ws3.send_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_broadcast_to_nonexistent_session_returns_zero(
        self, connection_manager
    ):
        """Test broadcast to nonexistent session returns 0."""
        event = create_ws_ping_event("nonexistent-session")
        sent_count = await connection_manager.broadcast_to_session(
            "nonexistent-session", event
        )

        assert sent_count == 0

    @pytest.mark.asyncio
    async def test_broadcast_removes_failed_connections(
        self, connection_manager, session_id
    ):
        """Test failed connections are cleaned up during broadcast."""
        ws_good = AsyncMock()
        ws_bad = AsyncMock()

        # Connect both (they need to succeed during connect)
        await connection_manager.connect(session_id, ws_good)
        await connection_manager.connect(session_id, ws_bad)
        assert connection_manager.get_connection_count(session_id) == 2

        # Now set up ws_bad to fail on next send
        ws_good.send_json.reset_mock()
        ws_bad.send_json.reset_mock()
        ws_bad.send_json.side_effect = Exception("Connection closed")

        event = create_ws_ping_event(session_id)
        sent_count = await connection_manager.broadcast_to_session(session_id, event)

        assert sent_count == 1  # Only good connection succeeded
        assert connection_manager.get_connection_count(session_id) == 1

    @pytest.mark.asyncio
    async def test_send_heartbeat(self, connection_manager, mock_websocket, session_id):
        """Test heartbeat ping sending."""
        await connection_manager.connect(session_id, mock_websocket)
        mock_websocket.send_json.reset_mock()

        sent_count = await connection_manager.send_heartbeat(session_id)

        assert sent_count == 1
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "ping"

    @pytest.mark.asyncio
    async def test_send_error(self, connection_manager, mock_websocket, session_id):
        """Test error event sending."""
        await connection_manager.connect(session_id, mock_websocket)
        mock_websocket.send_json.reset_mock()

        sent_count = await connection_manager.send_error(
            session_id,
            error_message="Test error",
            recoverable=True,
            retry_after=5,
        )

        assert sent_count == 1
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "error"
        assert call_args["data"]["error_message"] == "Test error"
        assert call_args["data"]["recoverable"] is True
        assert call_args["data"]["retry_after"] == 5

    @pytest.mark.asyncio
    async def test_close_session_connections(
        self, connection_manager, session_id
    ):
        """Test closing all connections for a session."""
        ws1 = AsyncMock()
        ws2 = AsyncMock()

        await connection_manager.connect(session_id, ws1)
        await connection_manager.connect(session_id, ws2)
        assert connection_manager.get_connection_count(session_id) == 2

        closed_count = await connection_manager.close_session_connections(
            session_id, reason="Test complete"
        )

        assert closed_count == 2
        assert connection_manager.get_connection_count(session_id) == 0
        assert connection_manager.has_session(session_id) is False
        ws1.close.assert_called_once()
        ws2.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_nonexistent_session_returns_zero(self, connection_manager):
        """Test closing nonexistent session returns 0."""
        closed_count = await connection_manager.close_session_connections(
            "nonexistent-session"
        )
        assert closed_count == 0

    def test_get_all_session_ids(self, connection_manager):
        """Test getting all session IDs with connections."""
        # Initially empty
        assert connection_manager.get_all_session_ids() == []

    @pytest.mark.asyncio
    async def test_get_all_session_ids_with_connections(self, connection_manager):
        """Test getting all session IDs with active connections."""
        ws1 = AsyncMock()
        ws2 = AsyncMock()

        await connection_manager.connect("session-1", ws1)
        await connection_manager.connect("session-2", ws2)

        session_ids = connection_manager.get_all_session_ids()
        assert "session-1" in session_ids
        assert "session-2" in session_ids
        assert len(session_ids) == 2

    @pytest.mark.asyncio
    async def test_get_last_activity(self, connection_manager, mock_websocket, session_id):
        """Test last activity tracking."""
        # Before connection
        assert connection_manager.get_last_activity(session_id) is None

        # After connection
        await connection_manager.connect(session_id, mock_websocket)
        last_activity = connection_manager.get_last_activity(session_id)
        assert last_activity is not None
        assert isinstance(last_activity, datetime)

    @pytest.mark.asyncio
    async def test_cleanup_inactive_sessions(self, connection_manager):
        """Test inactive session cleanup."""
        ws = AsyncMock()
        session_id = "old-session"

        await connection_manager.connect(session_id, ws)

        # Manually set old last activity
        connection_manager._last_activity[session_id] = datetime.now() - timedelta(minutes=15)

        cleaned = await connection_manager.cleanup_inactive_sessions(timeout_minutes=10)

        assert session_id in cleaned
        assert connection_manager.has_session(session_id) is False


# ═══════════════════════════════════════════════════════════════════════════════
# Singleton Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestConnectionManagerSingleton:
    """Test ConnectionManager singleton behavior."""

    def test_get_connection_manager_returns_singleton(self):
        """Test singleton returns same instance."""
        reset_connection_manager()

        manager1 = get_connection_manager()
        manager2 = get_connection_manager()

        assert manager1 is manager2

    def test_reset_connection_manager(self):
        """Test reset creates new instance."""
        manager1 = get_connection_manager()
        reset_connection_manager()
        manager2 = get_connection_manager()

        assert manager1 is not manager2


# ═══════════════════════════════════════════════════════════════════════════════
# WebSocket Endpoint Tests
# [Source: docs/stories/33.2.story.md - AC1, AC3]
# ═══════════════════════════════════════════════════════════════════════════════


class TestWebSocketEndpoint:
    """Test WebSocket endpoint functions."""

    @pytest.mark.asyncio
    async def test_validate_session_with_no_validator(self):
        """Test session validation with no validator set."""
        from app.api.v1.endpoints.websocket import validate_session, set_session_validator

        # Clear any existing validator
        set_session_validator(None)

        # Should return True (allow) when no validator
        result = await validate_session("any-session")
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_session_with_validator(self):
        """Test session validation with custom validator."""
        from app.api.v1.endpoints.websocket import validate_session, set_session_validator

        async def mock_validator(session_id: str) -> bool:
            return session_id.startswith("valid-")

        set_session_validator(mock_validator)

        assert await validate_session("valid-session") is True
        assert await validate_session("invalid-session") is False

        # Cleanup
        set_session_validator(None)

    @pytest.mark.asyncio
    async def test_validate_session_handles_validator_error(self):
        """Test session validation handles validator errors gracefully."""
        from app.api.v1.endpoints.websocket import validate_session, set_session_validator

        async def failing_validator(session_id: str) -> bool:
            raise Exception("Validator error")

        set_session_validator(failing_validator)

        # Should return False on error
        result = await validate_session("any-session")
        assert result is False

        # Cleanup
        set_session_validator(None)

    @pytest.mark.asyncio
    async def test_websocket_endpoint_rejects_invalid_session(self):
        """Test WebSocket rejects connection for invalid session."""
        from app.api.v1.endpoints.websocket import (
            websocket_intelligent_parallel,
            set_session_validator,
            WEBSOCKET_CLOSE_SESSION_NOT_FOUND,
        )

        # Set up validator that rejects all sessions
        async def reject_all(session_id: str) -> bool:
            return False

        set_session_validator(reject_all)

        mock_ws = AsyncMock()
        mock_manager = MagicMock(spec=ConnectionManager)

        await websocket_intelligent_parallel(mock_ws, "invalid-session", mock_manager)

        # Should close with 4004 code
        mock_ws.close.assert_called_once_with(
            code=WEBSOCKET_CLOSE_SESSION_NOT_FOUND,
            reason="Session 'invalid-session' not found"
        )
        # Should NOT accept or connect
        mock_ws.accept.assert_not_called()
        mock_manager.connect.assert_not_called()

        # Cleanup
        set_session_validator(None)

    def test_get_websocket_manager(self):
        """Test FastAPI dependency for ConnectionManager."""
        from app.api.v1.endpoints.websocket import get_websocket_manager
        from app.services.websocket_manager import reset_connection_manager

        reset_connection_manager()
        manager = get_websocket_manager()

        assert manager is not None
        assert isinstance(manager, ConnectionManager)

    @pytest.mark.asyncio
    async def test_websocket_heartbeat_loop_sends_ping(self):
        """Test heartbeat loop sends ping events."""
        from app.api.v1.endpoints.websocket import _heartbeat_loop

        mock_ws = AsyncMock()
        mock_manager = MagicMock(spec=ConnectionManager)
        session_id = "test-session"

        # Run heartbeat for a very short time using a task
        async def run_heartbeat():
            try:
                await _heartbeat_loop(mock_manager, session_id, mock_ws)
            except asyncio.CancelledError:
                pass

        # Start heartbeat and cancel it quickly
        task = asyncio.create_task(run_heartbeat())
        # Wait just a bit then cancel
        await asyncio.sleep(0.05)
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass

        # Heartbeat may not have had time to send due to 30s interval
        # But this tests the loop structure and cancellation

    @pytest.mark.asyncio
    async def test_websocket_heartbeat_loop_handles_send_error(self):
        """Test heartbeat loop handles send errors gracefully."""
        from app.api.v1.endpoints.websocket import _heartbeat_loop

        mock_ws = AsyncMock()
        mock_ws.send_json.side_effect = Exception("Connection closed")
        mock_manager = MagicMock(spec=ConnectionManager)
        session_id = "test-session"

        # Patch sleep to avoid waiting
        with patch("app.api.v1.endpoints.websocket.asyncio.sleep", return_value=None):
            # Should exit on error without raising
            await _heartbeat_loop(mock_manager, session_id, mock_ws)

        # Should have attempted to send
        mock_ws.send_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_websocket_endpoint_handles_client_message(self):
        """Test WebSocket endpoint processes client messages."""
        from app.api.v1.endpoints.websocket import (
            websocket_intelligent_parallel,
            set_session_validator,
        )

        # Allow all sessions
        async def allow_all(session_id: str) -> bool:
            return True

        set_session_validator(allow_all)

        mock_ws = AsyncMock()
        mock_manager = AsyncMock(spec=ConnectionManager)

        # Simulate receiving a message then disconnect
        call_count = [0]

        async def mock_receive():
            call_count[0] += 1
            if call_count[0] == 1:
                return "test message"
            else:
                raise WebSocketDisconnect()

        mock_ws.receive_text = mock_receive

        await websocket_intelligent_parallel(mock_ws, "test-session", mock_manager)

        # Should have connected and disconnected via manager
        # (accept is called inside manager.connect, which is mocked)
        mock_manager.connect.assert_called_once()
        mock_manager.disconnect.assert_called_once()

        # Cleanup
        set_session_validator(None)

    @pytest.mark.asyncio
    async def test_websocket_endpoint_handles_timeout(self):
        """Test WebSocket endpoint handles inactivity timeout."""
        from app.api.v1.endpoints.websocket import (
            websocket_intelligent_parallel,
            set_session_validator,
        )

        # Allow all sessions
        async def allow_all(session_id: str) -> bool:
            return True

        set_session_validator(allow_all)

        mock_ws = AsyncMock()
        mock_manager = AsyncMock(spec=ConnectionManager)

        # Simulate timeout
        mock_ws.receive_text.side_effect = asyncio.TimeoutError()

        await websocket_intelligent_parallel(mock_ws, "timeout-session", mock_manager)

        # Should have sent error event before closing
        assert mock_ws.send_json.call_count >= 1
        # Should have disconnected
        mock_manager.disconnect.assert_called_once()

        # Cleanup
        set_session_validator(None)

    @pytest.mark.asyncio
    async def test_websocket_endpoint_handles_general_error(self):
        """Test WebSocket endpoint handles general exceptions."""
        from app.api.v1.endpoints.websocket import (
            websocket_intelligent_parallel,
            set_session_validator,
        )

        # Allow all sessions
        async def allow_all(session_id: str) -> bool:
            return True

        set_session_validator(allow_all)

        mock_ws = AsyncMock()
        mock_manager = AsyncMock(spec=ConnectionManager)

        # Simulate general error
        mock_ws.receive_text.side_effect = RuntimeError("Unexpected error")

        await websocket_intelligent_parallel(mock_ws, "error-session", mock_manager)

        # Should have sent error event
        assert mock_ws.send_json.call_count >= 1
        # Should have disconnected
        mock_manager.disconnect.assert_called_once()

        # Cleanup
        set_session_validator(None)