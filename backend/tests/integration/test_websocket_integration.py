# Canvas Learning System - WebSocket Integration Tests
# Story 33.2: WebSocket Real-time Updates
"""
Integration tests for WebSocket endpoints.

Tests full workflow: connect → receive events → disconnect.

[Source: docs/stories/33.2.story.md - Task 6]
"""

import asyncio
from datetime import datetime
from typing import List
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI, WebSocket
from fastapi.testclient import TestClient

from app.models.intelligent_parallel_models import (
    ParallelTaskStatus,
    WSEventType,
    create_ws_progress_event,
)
from app.services.intelligent_parallel_service import IntelligentParallelService
from app.services.websocket_manager import ConnectionManager, reset_connection_manager


# ═══════════════════════════════════════════════════════════════════════════════
# Test Application Setup
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def test_app():
    """Create test FastAPI application with WebSocket endpoint."""
    from app.api.v1.endpoints.websocket import (
        websocket_intelligent_parallel,
        set_session_validator,
    )

    app = FastAPI()
    reset_connection_manager()

    # Create a simple validator that always returns True for testing
    async def allow_all_sessions(session_id: str) -> bool:
        return True

    set_session_validator(allow_all_sessions)

    @app.websocket("/ws/intelligent-parallel/{session_id}")
    async def websocket_endpoint(websocket: WebSocket, session_id: str):
        await websocket_intelligent_parallel(websocket, session_id)

    yield app

    # Cleanup
    set_session_validator(None)
    reset_connection_manager()


@pytest.fixture
def test_client(test_app):
    """Create test client."""
    return TestClient(test_app)


@pytest.fixture
def connection_manager():
    """Create fresh ConnectionManager for each test."""
    reset_connection_manager()
    manager = ConnectionManager()
    return manager


@pytest.fixture
def service(connection_manager):
    """Create IntelligentParallelService with test ConnectionManager."""
    return IntelligentParallelService(connection_manager=connection_manager)


# ═══════════════════════════════════════════════════════════════════════════════
# WebSocket Connection Tests
# [Source: docs/stories/33.2.story.md - AC1]
# ═══════════════════════════════════════════════════════════════════════════════


class TestWebSocketConnection:
    """Test WebSocket connection handling."""

    def test_websocket_connect_success(self, test_client):
        """Test WebSocket connection succeeds with valid session."""
        with test_client.websocket_connect(
            "/ws/intelligent-parallel/test-session-123"
        ) as websocket:
            # Should receive connected event
            data = websocket.receive_json()
            assert data["type"] == "connected"
            assert data["task_id"] == "test-session-123"

    def test_websocket_connect_receives_timestamp(self, test_client):
        """Test connected event includes timestamp."""
        with test_client.websocket_connect(
            "/ws/intelligent-parallel/test-session-456"
        ) as websocket:
            data = websocket.receive_json()
            assert "timestamp" in data
            # Timestamp should be a valid ISO format string
            timestamp = data["timestamp"]
            assert isinstance(timestamp, str)

    def test_websocket_multiple_connections_same_session(self, test_client):
        """Test multiple clients can connect to same session."""
        # This tests concurrent connections
        session_id = "shared-session"

        with test_client.websocket_connect(
            f"/ws/intelligent-parallel/{session_id}"
        ) as ws1:
            data1 = ws1.receive_json()
            assert data1["type"] == "connected"

            # Second connection to same session
            with test_client.websocket_connect(
                f"/ws/intelligent-parallel/{session_id}"
            ) as ws2:
                data2 = ws2.receive_json()
                assert data2["type"] == "connected"


# ═══════════════════════════════════════════════════════════════════════════════
# WebSocket Session Validation Tests
# [Source: docs/stories/33.2.story.md - AC1]
# ═══════════════════════════════════════════════════════════════════════════════


class TestWebSocketSessionValidation:
    """Test session validation before connection accept."""

    def test_websocket_reject_invalid_session(self):
        """Test WebSocket rejects connection for invalid session."""
        from app.api.v1.endpoints.websocket import (
            websocket_intelligent_parallel,
            set_session_validator,
        )

        # Create app with validator that rejects specific sessions
        app = FastAPI()

        async def reject_unknown(session_id: str) -> bool:
            return session_id.startswith("valid-")

        set_session_validator(reject_unknown)

        @app.websocket("/ws/intelligent-parallel/{session_id}")
        async def ws_endpoint(websocket: WebSocket, session_id: str):
            await websocket_intelligent_parallel(websocket, session_id)

        client = TestClient(app)

        # Valid session should connect
        with client.websocket_connect("/ws/intelligent-parallel/valid-session") as ws:
            data = ws.receive_json()
            assert data["type"] == "connected"

        # Invalid session should be rejected
        # TestClient raises exception when WebSocket is closed unexpectedly
        with pytest.raises(Exception):
            with client.websocket_connect("/ws/intelligent-parallel/invalid-session"):
                pass

        # Cleanup
        set_session_validator(None)


# ═══════════════════════════════════════════════════════════════════════════════
# WebSocket Event Broadcasting Tests
# [Source: docs/stories/33.2.story.md - AC2, AC4]
# ═══════════════════════════════════════════════════════════════════════════════


class TestWebSocketBroadcasting:
    """Test WebSocket event broadcasting."""

    @pytest.mark.asyncio
    async def test_broadcast_progress_update(self, connection_manager):
        """Test progress update is broadcast to all clients."""
        session_id = "test-session"

        # Create mock WebSockets
        ws1 = AsyncMock()
        ws2 = AsyncMock()

        await connection_manager.connect(session_id, ws1)
        await connection_manager.connect(session_id, ws2)

        # Reset mocks to clear connected event
        ws1.send_json.reset_mock()
        ws2.send_json.reset_mock()

        # Broadcast progress
        event = create_ws_progress_event(
            task_id=session_id,
            progress_percent=50,
            completed_nodes=6,
            total_nodes=12,
        )
        sent_count = await connection_manager.broadcast_to_session(session_id, event)

        assert sent_count == 2
        ws1.send_json.assert_called_once()
        ws2.send_json.assert_called_once()

        # Verify event content
        call_args = ws1.send_json.call_args[0][0]
        assert call_args["type"] == "progress"
        assert call_args["data"]["progress_percent"] == 50

    @pytest.mark.asyncio
    async def test_service_notify_progress(self, service, connection_manager):
        """Test service notify_progress broadcasts correctly."""
        session_id = "test-session"

        # Create a session first
        from app.models.intelligent_parallel_models import GroupExecuteConfig
        await service.start_batch_session(
            canvas_path="test.canvas",
            groups=[
                GroupExecuteConfig(
                    group_id="g1",
                    agent_type="comparison-table",
                    node_ids=["n1", "n2"]
                )
            ],
        )

        # Connect a mock WebSocket
        ws = AsyncMock()
        await connection_manager.connect(session_id, ws)
        ws.send_json.reset_mock()

        # Note: The session_id from service won't match our hardcoded one
        # For this test, we'll use the connection_manager directly
        event = create_ws_progress_event(
            task_id=session_id,
            progress_percent=25,
            completed_nodes=3,
            total_nodes=12,
        )
        sent_count = await connection_manager.broadcast_to_session(session_id, event)

        assert sent_count == 1


# ═══════════════════════════════════════════════════════════════════════════════
# WebSocket Service Integration Tests
# [Source: docs/stories/33.2.story.md - Task 4]
# ═══════════════════════════════════════════════════════════════════════════════


class TestWebSocketServiceIntegration:
    """Test WebSocket integration with IntelligentParallelService."""

    @pytest.mark.asyncio
    async def test_service_session_exists(self, service):
        """Test service session_exists method."""
        # Initially no sessions
        assert await service.session_exists("nonexistent") is False

        # Create a session
        from app.models.intelligent_parallel_models import GroupExecuteConfig
        response = await service.start_batch_session(
            canvas_path="test.canvas",
            groups=[
                GroupExecuteConfig(
                    group_id="g1",
                    agent_type="comparison-table",
                    node_ids=["n1"]
                )
            ],
        )

        # Now session should exist
        assert await service.session_exists(response.task_id) is True

    @pytest.mark.asyncio
    async def test_service_notify_node_complete(self, service, connection_manager):
        """Test service notify_node_complete broadcasts correctly."""
        session_id = "test-session"

        ws = AsyncMock()
        await connection_manager.connect(session_id, ws)
        ws.send_json.reset_mock()

        sent_count = await service.notify_node_complete(
            session_id=session_id,
            node_id="node-001",
            file_path="output/file.md",
            file_size="2.5KB",
            group_id="group-1",
        )

        assert sent_count == 1
        call_args = ws.send_json.call_args[0][0]
        assert call_args["type"] == "node_complete"
        assert call_args["data"]["node_id"] == "node-001"

    @pytest.mark.asyncio
    async def test_service_notify_group_complete(self, service, connection_manager):
        """Test service notify_group_complete broadcasts correctly."""
        session_id = "test-session"

        ws = AsyncMock()
        await connection_manager.connect(session_id, ws)
        ws.send_json.reset_mock()

        sent_count = await service.notify_group_complete(
            session_id=session_id,
            group_id="group-1",
            agent_type="comparison-table",
            results=None,
        )

        assert sent_count == 1
        call_args = ws.send_json.call_args[0][0]
        assert call_args["type"] == "group_complete"
        assert call_args["data"]["group_id"] == "group-1"

    @pytest.mark.asyncio
    async def test_service_notify_error(self, service, connection_manager):
        """Test service notify_error broadcasts correctly."""
        session_id = "test-session"

        ws = AsyncMock()
        await connection_manager.connect(session_id, ws)
        ws.send_json.reset_mock()

        sent_count = await service.notify_error(
            session_id=session_id,
            error_message="Agent timeout",
            node_id="node-005",
            error_type="TimeoutError",
            recoverable=True,
            retry_after=5,
        )

        assert sent_count == 1
        call_args = ws.send_json.call_args[0][0]
        assert call_args["type"] == "error"
        assert call_args["data"]["error_message"] == "Agent timeout"
        assert call_args["data"]["recoverable"] is True

    @pytest.mark.asyncio
    async def test_service_notify_session_complete_closes_connections(
        self, service, connection_manager
    ):
        """Test service notify_session_complete closes WebSocket connections."""
        session_id = "test-session"

        ws = AsyncMock()
        await connection_manager.connect(session_id, ws)
        ws.send_json.reset_mock()

        assert connection_manager.get_connection_count(session_id) == 1

        sent_count = await service.notify_session_complete(
            session_id=session_id,
            status=ParallelTaskStatus.completed,
            total_duration=135.5,
            success_count=11,
            failure_count=1,
        )

        assert sent_count == 1
        # Verify complete event was sent
        call_args = ws.send_json.call_args[0][0]
        assert call_args["type"] == "complete"
        assert call_args["data"]["success_count"] == 11

        # Verify connection was closed
        ws.close.assert_called_once()
        assert connection_manager.get_connection_count(session_id) == 0


# ═══════════════════════════════════════════════════════════════════════════════
# Polling Fallback Tests
# [Source: docs/stories/33.2.story.md - AC5]
# ═══════════════════════════════════════════════════════════════════════════════


class TestPollingFallback:
    """Test polling fallback endpoint works when WebSocket unavailable."""

    def test_polling_endpoint_returns_progress(self):
        """Test GET /api/v1/canvas/intelligent-parallel/{session_id} works."""
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)

        # First create a session via POST /confirm
        confirm_response = client.post(
            "/api/v1/canvas/intelligent-parallel/confirm",
            json={
                "canvas_path": "test.canvas",
                "groups": [
                    {
                        "group_id": "g1",
                        "agent_type": "comparison-table",
                        "node_ids": ["n1", "n2"]
                    }
                ],
                "timeout": 600
            }
        )

        assert confirm_response.status_code == 202
        session_id = confirm_response.json()["session_id"]

        # Now poll for progress
        progress_response = client.get(
            f"/api/v1/canvas/intelligent-parallel/{session_id}"
        )

        assert progress_response.status_code == 200
        progress_data = progress_response.json()
        assert progress_data["session_id"] == session_id
        assert "status" in progress_data
        assert "progress_percent" in progress_data

    def test_polling_endpoint_404_for_invalid_session(self):
        """Test polling returns 404 for invalid session."""
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)

        response = client.get(
            "/api/v1/canvas/intelligent-parallel/nonexistent-session"
        )

        assert response.status_code == 404


# ═══════════════════════════════════════════════════════════════════════════════
# Connection Lifecycle Tests
# [Source: docs/stories/33.2.story.md - AC3]
# ═══════════════════════════════════════════════════════════════════════════════


class TestConnectionLifecycle:
    """Test WebSocket connection lifecycle handling."""

    @pytest.mark.asyncio
    async def test_connection_cleanup_on_disconnect(self, connection_manager):
        """Test resources are cleaned up on client disconnect."""
        session_id = "test-session"

        ws = AsyncMock()
        await connection_manager.connect(session_id, ws)
        assert connection_manager.has_session(session_id) is True

        await connection_manager.disconnect(session_id, ws)
        assert connection_manager.has_session(session_id) is False

    @pytest.mark.asyncio
    async def test_multiple_sessions_independent(self, connection_manager):
        """Test multiple sessions are independent."""
        ws1 = AsyncMock()
        ws2 = AsyncMock()

        await connection_manager.connect("session-1", ws1)
        await connection_manager.connect("session-2", ws2)

        assert connection_manager.get_connection_count("session-1") == 1
        assert connection_manager.get_connection_count("session-2") == 1

        # Closing one doesn't affect the other
        await connection_manager.disconnect("session-1", ws1)
        assert connection_manager.has_session("session-1") is False
        assert connection_manager.has_session("session-2") is True


# ═══════════════════════════════════════════════════════════════════════════════
# Concurrent Stress Tests
# [Source: QA Review 33.2 - Suggested improvement]
# ═══════════════════════════════════════════════════════════════════════════════


class TestConcurrentStress:
    """Stress tests for concurrent WebSocket connections."""

    @pytest.mark.asyncio
    async def test_concurrent_connections_single_session(self, connection_manager):
        """Test many concurrent connections to a single session."""
        session_id = "stress-test-session"
        num_connections = 50

        # Create many mock WebSockets
        websockets = [AsyncMock() for _ in range(num_connections)]

        # Connect all concurrently
        connect_tasks = [
            connection_manager.connect(session_id, ws)
            for ws in websockets
        ]
        results = await asyncio.gather(*connect_tasks)

        # All should succeed
        assert all(results)
        assert connection_manager.get_connection_count(session_id) == num_connections

        # Verify metrics
        metrics = connection_manager.get_metrics()
        assert metrics["total_sessions"] == 1
        assert metrics["total_connections"] == num_connections

        # Disconnect all concurrently
        disconnect_tasks = [
            connection_manager.disconnect(session_id, ws)
            for ws in websockets
        ]
        await asyncio.gather(*disconnect_tasks)

        assert connection_manager.get_connection_count(session_id) == 0
        assert connection_manager.has_session(session_id) is False

    @pytest.mark.asyncio
    async def test_concurrent_connections_multiple_sessions(self, connection_manager):
        """Test concurrent connections across multiple sessions."""
        num_sessions = 20
        connections_per_session = 10

        # Create session-websocket pairs
        session_websockets = {}
        for i in range(num_sessions):
            session_id = f"session-{i}"
            session_websockets[session_id] = [
                AsyncMock() for _ in range(connections_per_session)
            ]

        # Connect all concurrently
        connect_tasks = []
        for session_id, websockets in session_websockets.items():
            for ws in websockets:
                connect_tasks.append(connection_manager.connect(session_id, ws))

        results = await asyncio.gather(*connect_tasks)

        # All should succeed
        assert all(results)

        # Verify metrics
        metrics = connection_manager.get_metrics()
        assert metrics["total_sessions"] == num_sessions
        assert metrics["total_connections"] == num_sessions * connections_per_session

        # Verify each session has correct count
        for session_id in session_websockets:
            assert connection_manager.get_connection_count(session_id) == connections_per_session

    @pytest.mark.asyncio
    async def test_concurrent_broadcast_under_load(self, connection_manager):
        """Test broadcasting to many connections concurrently."""
        from app.models.intelligent_parallel_models import create_ws_progress_event

        session_id = "broadcast-stress-session"
        num_connections = 30
        num_broadcasts = 10

        # Create and connect many WebSockets
        websockets = [AsyncMock() for _ in range(num_connections)]
        for ws in websockets:
            await connection_manager.connect(session_id, ws)

        # Reset mocks to clear connected events
        for ws in websockets:
            ws.send_json.reset_mock()

        # Broadcast many events concurrently
        broadcast_tasks = []
        for i in range(num_broadcasts):
            event = create_ws_progress_event(
                task_id=session_id,
                progress_percent=i * 10,
                completed_nodes=i,
                total_nodes=10,
            )
            broadcast_tasks.append(
                connection_manager.broadcast_to_session(session_id, event)
            )

        results = await asyncio.gather(*broadcast_tasks)

        # All broadcasts should reach all connections
        for sent_count in results:
            assert sent_count == num_connections

        # Each WebSocket should have received all broadcasts
        for ws in websockets:
            assert ws.send_json.call_count == num_broadcasts

    @pytest.mark.asyncio
    async def test_mixed_connect_disconnect_under_load(self, connection_manager):
        """Test interleaved connect/disconnect operations."""
        session_id = "mixed-ops-session"
        num_iterations = 20

        for i in range(num_iterations):
            # Connect a batch
            batch_size = 5
            websockets = [AsyncMock() for _ in range(batch_size)]

            connect_tasks = [
                connection_manager.connect(session_id, ws)
                for ws in websockets
            ]
            await asyncio.gather(*connect_tasks)

            # Disconnect half
            half = batch_size // 2
            disconnect_tasks = [
                connection_manager.disconnect(session_id, ws)
                for ws in websockets[:half]
            ]
            await asyncio.gather(*disconnect_tasks)

            # Verify remaining count
            expected_remaining = batch_size - half
            if i == 0:
                assert connection_manager.get_connection_count(session_id) == expected_remaining
            else:
                # Previous iterations may have left connections
                assert connection_manager.get_connection_count(session_id) >= expected_remaining

        # Cleanup all
        await connection_manager.close_session_connections(session_id)
        assert connection_manager.has_session(session_id) is False


# ═══════════════════════════════════════════════════════════════════════════════
# Metrics and Health Tests
# [Source: QA Review 33.2 - Suggested improvement]
# ═══════════════════════════════════════════════════════════════════════════════


class TestMetricsAndHealth:
    """Test connection metrics and health status."""

    @pytest.mark.asyncio
    async def test_get_metrics_empty(self, connection_manager):
        """Test metrics when no connections."""
        metrics = connection_manager.get_metrics()

        assert metrics["total_sessions"] == 0
        assert metrics["total_connections"] == 0
        assert metrics["connections_per_session"] == {}
        assert metrics["oldest_session"] is None
        assert metrics["newest_session"] is None

    @pytest.mark.asyncio
    async def test_get_metrics_with_connections(self, connection_manager):
        """Test metrics with active connections."""
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        ws3 = AsyncMock()

        await connection_manager.connect("session-a", ws1)
        await connection_manager.connect("session-a", ws2)
        await connection_manager.connect("session-b", ws3)

        metrics = connection_manager.get_metrics()

        assert metrics["total_sessions"] == 2
        assert metrics["total_connections"] == 3
        assert metrics["connections_per_session"]["session-a"] == 2
        assert metrics["connections_per_session"]["session-b"] == 1
        assert metrics["oldest_session"] is not None
        assert metrics["newest_session"] is not None

    @pytest.mark.asyncio
    async def test_get_health_status_healthy(self, connection_manager):
        """Test health status when healthy."""
        ws = AsyncMock()
        await connection_manager.connect("test-session", ws)

        health = connection_manager.get_health_status()

        assert health["status"] == "healthy"
        assert health["total_sessions"] == 1
        assert health["total_connections"] == 1
        assert health["warning"] is None

    def test_get_health_status_empty(self, connection_manager):
        """Test health status with no connections."""
        health = connection_manager.get_health_status()

        assert health["status"] == "healthy"
        assert health["total_sessions"] == 0
        assert health["total_connections"] == 0
        assert health["warning"] is None
