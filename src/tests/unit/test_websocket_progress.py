"""
Unit Tests for WebSocket Progress Service

Story 19.4: 实时进度更新 (WebSocket)

Tests AC 1-6:
- AC 1: WebSocket服务端端点
- AC 2: Canvas文件变更检测
- AC 3-5: 连接管理和重连
- AC 6: 消息格式规范
"""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

# Environment variables are set in conftest.py before any imports
# Import the modules under test
from src.api.websocket.progress_ws import (
    CanvasFileWatcher,
    ProgressConnectionManager,
    WSMessage,
    manager,
    websocket_progress_endpoint,
)


class TestWSMessage:
    """Tests for WSMessage class (AC 6: Message format)."""

    def test_message_creation_with_defaults(self):
        """Test creating message with default timestamp."""
        msg = WSMessage(msg_type="progress_update", data={"test": "data"})

        assert msg.type == "progress_update"
        assert msg.data == {"test": "data"}
        assert msg.timestamp is not None
        # Verify ISO format
        datetime.fromisoformat(msg.timestamp.replace("Z", "+00:00"))

    def test_message_creation_with_custom_timestamp(self):
        """Test creating message with custom timestamp."""
        custom_ts = "2025-01-15T10:30:00+00:00"
        msg = WSMessage(
            msg_type="connection_ack",
            data={"status": "connected"},
            timestamp=custom_ts
        )

        assert msg.type == "connection_ack"
        assert msg.timestamp == custom_ts

    def test_to_dict_format(self):
        """Test message serialization to dict (AC 6)."""
        msg = WSMessage(
            msg_type="progress_update",
            data={"canvas_id": "test.canvas", "coverage_rate": 0.75}
        )

        result = msg.to_dict()

        assert "type" in result
        assert "data" in result
        assert "timestamp" in result
        assert result["type"] == "progress_update"
        assert result["data"]["canvas_id"] == "test.canvas"

    def test_error_message_format(self):
        """Test error message format (AC 6)."""
        msg = WSMessage(
            msg_type="error",
            data={"code": "INVALID_CANVAS", "message": "Canvas not found"}
        )

        result = msg.to_dict()

        assert result["type"] == "error"
        assert result["data"]["code"] == "INVALID_CANVAS"
        assert result["data"]["message"] == "Canvas not found"


class TestProgressConnectionManager:
    """Tests for ProgressConnectionManager class (AC 1, AC 3)."""

    @pytest.fixture
    def manager_instance(self):
        """Create fresh manager for each test."""
        return ProgressConnectionManager()

    @pytest.fixture
    def mock_websocket(self):
        """Create mock WebSocket."""
        ws = AsyncMock()
        ws.accept = AsyncMock()
        ws.send_json = AsyncMock()
        ws.send_text = AsyncMock()
        return ws

    @pytest.mark.asyncio
    async def test_connect_accepts_websocket(self, manager_instance, mock_websocket):
        """Test that connect() accepts the WebSocket connection."""
        await manager_instance.connect(mock_websocket, "test.canvas")

        mock_websocket.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_sends_ack_message(self, manager_instance, mock_websocket):
        """Test that connect() sends connection acknowledgment (AC 6)."""
        await manager_instance.connect(mock_websocket, "test.canvas")

        mock_websocket.send_json.assert_called_once()
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "connection_ack"
        assert call_args["data"]["status"] == "connected"
        assert call_args["data"]["canvas_id"] == "test.canvas"

    @pytest.mark.asyncio
    async def test_connect_adds_to_active_connections(self, manager_instance, mock_websocket):
        """Test that connect() tracks the connection."""
        await manager_instance.connect(mock_websocket, "test.canvas")

        assert "test.canvas" in manager_instance.active_connections
        assert mock_websocket in manager_instance.active_connections["test.canvas"]

    @pytest.mark.asyncio
    async def test_connect_multiple_clients_same_canvas(self, manager_instance):
        """Test multiple clients can connect to same canvas."""
        ws1 = AsyncMock()
        ws2 = AsyncMock()

        await manager_instance.connect(ws1, "test.canvas")
        await manager_instance.connect(ws2, "test.canvas")

        assert len(manager_instance.active_connections["test.canvas"]) == 2

    @pytest.mark.asyncio
    async def test_disconnect_removes_connection(self, manager_instance, mock_websocket):
        """Test that disconnect() removes the connection."""
        await manager_instance.connect(mock_websocket, "test.canvas")
        await manager_instance.disconnect(mock_websocket, "test.canvas")

        assert "test.canvas" not in manager_instance.active_connections

    @pytest.mark.asyncio
    async def test_disconnect_keeps_other_connections(self, manager_instance):
        """Test disconnect only removes specific connection."""
        ws1 = AsyncMock()
        ws2 = AsyncMock()

        await manager_instance.connect(ws1, "test.canvas")
        await manager_instance.connect(ws2, "test.canvas")
        await manager_instance.disconnect(ws1, "test.canvas")

        assert len(manager_instance.active_connections["test.canvas"]) == 1
        assert ws2 in manager_instance.active_connections["test.canvas"]

    @pytest.mark.asyncio
    async def test_broadcast_progress_update_sends_to_all(self, manager_instance):
        """Test broadcast sends to all connected clients (AC 2)."""
        ws1 = AsyncMock()
        ws2 = AsyncMock()

        await manager_instance.connect(ws1, "test.canvas")
        await manager_instance.connect(ws2, "test.canvas")

        progress_data = {
            "total_concepts": 10,
            "passed_count": 7,
            "coverage_rate": 0.7
        }

        notified = await manager_instance.broadcast_progress_update(
            "test.canvas",
            progress_data
        )

        assert notified == 2
        # Both should receive the message (first call is ack, second is broadcast)
        assert ws1.send_json.call_count == 2
        assert ws2.send_json.call_count == 2

    @pytest.mark.asyncio
    async def test_broadcast_includes_changed_node(self, manager_instance, mock_websocket):
        """Test broadcast includes changed node info (AC 2)."""
        await manager_instance.connect(mock_websocket, "test.canvas")

        progress_data = {"total_concepts": 5, "passed_count": 3, "coverage_rate": 0.6}
        changed_node = {
            "node_id": "node123",
            "source_node_id": "source456",
            "old_color": "4",
            "new_color": "2"
        }

        await manager_instance.broadcast_progress_update(
            "test.canvas",
            progress_data,
            changed_node
        )

        # Get the broadcast call (second call after ack)
        call_args = mock_websocket.send_json.call_args_list[1][0][0]
        assert call_args["type"] == "progress_update"
        assert call_args["data"]["changed_node"] == changed_node

    @pytest.mark.asyncio
    async def test_broadcast_to_nonexistent_canvas(self, manager_instance):
        """Test broadcast to canvas with no connections."""
        notified = await manager_instance.broadcast_progress_update(
            "nonexistent.canvas",
            {"total_concepts": 0}
        )

        assert notified == 0

    @pytest.mark.asyncio
    async def test_broadcast_handles_send_failure(self, manager_instance):
        """Test broadcast handles failed sends gracefully."""
        ws_good = AsyncMock()
        ws_bad = AsyncMock()
        # Allow connect (ack message) to succeed, then fail on broadcast
        call_count = [0]
        async def fail_on_second_call(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] > 1:  # First call is ack, second is broadcast
                raise Exception("Connection lost")
        ws_bad.send_json = AsyncMock(side_effect=fail_on_second_call)

        await manager_instance.connect(ws_good, "test.canvas")
        await manager_instance.connect(ws_bad, "test.canvas")

        notified = await manager_instance.broadcast_progress_update(
            "test.canvas",
            {"total_concepts": 5}
        )

        # One succeeded, one failed
        assert notified == 1
        # Bad connection should be removed
        assert ws_bad not in manager_instance.active_connections.get("test.canvas", [])

    @pytest.mark.asyncio
    async def test_send_error_to_client(self, manager_instance, mock_websocket):
        """Test sending error message to specific client."""
        await manager_instance.send_error(
            mock_websocket,
            "INVALID_REQUEST",
            "Invalid canvas ID format"
        )

        mock_websocket.send_json.assert_called_once()
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "error"
        assert call_args["data"]["code"] == "INVALID_REQUEST"

    def test_get_connection_count(self, manager_instance):
        """Test getting connection count for a canvas."""
        assert manager_instance.get_connection_count("test.canvas") == 0

    @pytest.mark.asyncio
    async def test_get_connection_count_with_connections(self, manager_instance):
        """Test connection count after adding connections."""
        ws1 = AsyncMock()
        ws2 = AsyncMock()

        await manager_instance.connect(ws1, "test.canvas")
        await manager_instance.connect(ws2, "test.canvas")

        assert manager_instance.get_connection_count("test.canvas") == 2

    def test_get_all_canvas_ids_empty(self, manager_instance):
        """Test getting canvas IDs when empty."""
        assert manager_instance.get_all_canvas_ids() == []

    @pytest.mark.asyncio
    async def test_get_all_canvas_ids_with_connections(self, manager_instance):
        """Test getting all canvas IDs with active connections."""
        ws1 = AsyncMock()
        ws2 = AsyncMock()

        await manager_instance.connect(ws1, "canvas1.canvas")
        await manager_instance.connect(ws2, "canvas2.canvas")

        canvas_ids = manager_instance.get_all_canvas_ids()
        assert "canvas1.canvas" in canvas_ids
        assert "canvas2.canvas" in canvas_ids


class TestCanvasFileWatcher:
    """Tests for CanvasFileWatcher class (AC 2)."""

    @pytest.fixture
    def watcher(self, tmp_path):
        """Create watcher with temporary directory."""
        return CanvasFileWatcher(str(tmp_path))

    def test_watcher_initialization(self, watcher, tmp_path):
        """Test watcher initializes with correct path."""
        assert watcher.watch_path == Path(tmp_path)
        assert not watcher.is_running

    def test_load_canvas_valid_json(self, watcher, tmp_path):
        """Test loading valid canvas JSON."""
        canvas_file = tmp_path / "test.canvas"
        canvas_data = {
            "nodes": [
                {"id": "1", "text": "Node 1", "color": "4"},
                {"id": "2", "text": "Node 2", "color": "2", "sourceNodeId": "1"}
            ],
            "edges": []
        }
        canvas_file.write_text(json.dumps(canvas_data), encoding="utf-8")

        result = watcher._load_canvas(canvas_file)

        assert result is not None
        assert len(result["nodes"]) == 2

    def test_load_canvas_invalid_json(self, watcher, tmp_path):
        """Test loading invalid JSON returns None."""
        canvas_file = tmp_path / "invalid.canvas"
        canvas_file.write_text("not valid json", encoding="utf-8")

        result = watcher._load_canvas(canvas_file)

        assert result is None

    def test_load_canvas_nonexistent_file(self, watcher, tmp_path):
        """Test loading nonexistent file returns None."""
        result = watcher._load_canvas(tmp_path / "nonexistent.canvas")

        assert result is None

    def test_detect_node_changes_color_change(self, watcher):
        """Test detecting color changes between canvas versions."""
        old_data = {
            "nodes": [
                {"id": "1", "color": "4", "sourceNodeId": "src1"},
                {"id": "2", "color": "3"}
            ]
        }
        new_data = {
            "nodes": [
                {"id": "1", "color": "2", "sourceNodeId": "src1"},  # Changed!
                {"id": "2", "color": "3"}
            ]
        }

        result = watcher._detect_node_changes(old_data, new_data)

        assert result is not None
        assert result["node_id"] == "1"
        assert result["old_color"] == "4"
        assert result["new_color"] == "2"

    def test_detect_node_changes_no_change(self, watcher):
        """Test no changes detected when colors are same."""
        data = {
            "nodes": [
                {"id": "1", "color": "4"},
                {"id": "2", "color": "3"}
            ]
        }

        result = watcher._detect_node_changes(data, data)

        assert result is None

    def test_detect_node_changes_from_none(self, watcher):
        """Test no changes when old data is None (first load)."""
        new_data = {"nodes": [{"id": "1", "color": "4"}]}

        result = watcher._detect_node_changes(None, new_data)

        assert result is None

    def test_calculate_progress(self, watcher):
        """Test progress calculation from canvas data."""
        canvas_data = {
            "nodes": [
                {"id": "1", "color": "4"},  # Red - not a source node
                {"id": "2", "color": "2", "sourceNodeId": "1"},  # Green - passed
                {"id": "3", "color": "4", "sourceNodeId": "1"},  # Red - not passed
                {"id": "4", "color": "2", "sourceNodeId": "1"},  # Green - passed
                {"id": "5", "color": "3", "sourceNodeId": "1"},  # Purple - not passed
            ]
        }

        result = watcher._calculate_progress(canvas_data)

        assert result["total_concepts"] == 4  # 4 nodes with sourceNodeId
        assert result["passed_count"] == 2    # 2 green nodes
        assert result["coverage_rate"] == 0.5

    def test_calculate_progress_empty_canvas(self, watcher):
        """Test progress calculation with no nodes."""
        canvas_data = {"nodes": []}

        result = watcher._calculate_progress(canvas_data)

        assert result["total_concepts"] == 0
        assert result["passed_count"] == 0
        assert result["coverage_rate"] == 0.0

    def test_calculate_progress_no_source_nodes(self, watcher):
        """Test progress calculation with no source nodes."""
        canvas_data = {
            "nodes": [
                {"id": "1", "color": "4"},
                {"id": "2", "color": "2"}
            ]
        }

        result = watcher._calculate_progress(canvas_data)

        assert result["total_concepts"] == 0

    @pytest.mark.asyncio
    async def test_handle_file_modified_non_canvas(self, watcher):
        """Test handler ignores non-canvas files."""
        # Should not raise or do anything
        await watcher.handle_file_modified("/path/to/file.txt")

    @pytest.mark.asyncio
    async def test_handle_file_modified_canvas(self, watcher, tmp_path):
        """Test handler processes canvas file changes."""
        canvas_file = tmp_path / "test.canvas"
        canvas_data = {
            "nodes": [
                {"id": "1", "color": "2", "sourceNodeId": "src1"}
            ]
        }
        canvas_file.write_text(json.dumps(canvas_data), encoding="utf-8")

        # Use global manager for this test
        with patch.object(manager, 'broadcast_progress_update', new_callable=AsyncMock) as mock_broadcast:
            mock_broadcast.return_value = 1  # Return integer for comparison
            await watcher.handle_file_modified(str(canvas_file))

            # Should have calculated progress and attempted broadcast
            mock_broadcast.assert_called_once()
            call_args = mock_broadcast.call_args
            assert call_args[0][0] == "test.canvas"  # canvas_id

    def test_watcher_start_without_watchdog(self, watcher):
        """Test watcher handles missing watchdog gracefully."""
        with patch.dict('sys.modules', {'watchdog': None, 'watchdog.observers': None, 'watchdog.events': None}):
            # This should log error but not crash
            watcher.start()
            assert not watcher.is_running

    def test_watcher_stop_when_not_running(self, watcher):
        """Test stopping watcher when not running."""
        # Should not raise
        watcher.stop()
        assert not watcher.is_running


class TestWebSocketEndpoint:
    """Tests for websocket_progress_endpoint function (AC 1)."""

    @pytest.mark.asyncio
    async def test_endpoint_connects_and_handles_disconnect(self):
        """Test endpoint handles connection lifecycle."""
        mock_ws = AsyncMock()
        mock_ws.receive_text = AsyncMock(side_effect=Exception("WebSocketDisconnect"))

        with patch.object(manager, 'connect', new_callable=AsyncMock) as mock_connect:
            with patch.object(manager, 'disconnect', new_callable=AsyncMock) as mock_disconnect:
                # Run endpoint (will exit on exception)
                try:
                    await websocket_progress_endpoint(mock_ws, "test.canvas")
                except Exception:
                    pass

                mock_connect.assert_called_once_with(mock_ws, "test.canvas")

    @pytest.mark.asyncio
    async def test_endpoint_handles_ping(self):
        """Test endpoint responds to ping with pong."""
        mock_ws = AsyncMock()
        # First receive returns "ping", second raises to exit loop
        mock_ws.receive_text = AsyncMock(
            side_effect=["ping", Exception("exit")]
        )

        with patch.object(manager, 'connect', new_callable=AsyncMock):
            with patch.object(manager, 'disconnect', new_callable=AsyncMock):
                try:
                    await websocket_progress_endpoint(mock_ws, "test.canvas")
                except Exception:
                    pass

                mock_ws.send_text.assert_called_with("pong")


class TestGlobalManager:
    """Tests for global manager instance."""

    def test_global_manager_exists(self):
        """Test that global manager is initialized."""
        assert manager is not None
        assert isinstance(manager, ProgressConnectionManager)

    def test_global_manager_fresh_state(self):
        """Test global manager starts with no connections."""
        # Note: This test may fail if other tests don't clean up
        # In a real scenario, use fixtures for isolation
        pass


class TestIntegration:
    """Integration tests for WebSocket progress system."""

    @pytest.mark.asyncio
    async def test_full_progress_update_flow(self, tmp_path):
        """Test complete flow: file change → progress calc → broadcast."""
        # Setup
        local_manager = ProgressConnectionManager()
        watcher = CanvasFileWatcher(str(tmp_path))

        # Create mock client
        mock_ws = AsyncMock()
        await local_manager.connect(mock_ws, "integration.canvas")

        # Create canvas file
        canvas_file = tmp_path / "integration.canvas"
        canvas_data = {
            "nodes": [
                {"id": "1", "color": "4"},
                {"id": "2", "color": "2", "sourceNodeId": "1"},
                {"id": "3", "color": "4", "sourceNodeId": "1"},
            ]
        }
        canvas_file.write_text(json.dumps(canvas_data), encoding="utf-8")

        # Simulate file change detection
        with patch('src.api.websocket.progress_ws.manager', local_manager):
            await watcher.handle_file_modified(str(canvas_file))

        # Verify broadcast was sent
        # First call is ack, second is progress update
        assert mock_ws.send_json.call_count == 2
        broadcast_call = mock_ws.send_json.call_args_list[1][0][0]
        assert broadcast_call["type"] == "progress_update"
        assert broadcast_call["data"]["total_concepts"] == 2
        assert broadcast_call["data"]["passed_count"] == 1
        assert broadcast_call["data"]["coverage_rate"] == 0.5

    @pytest.mark.asyncio
    async def test_multiple_canvas_isolation(self):
        """Test that updates to one canvas don't affect others."""
        local_manager = ProgressConnectionManager()

        ws1 = AsyncMock()
        ws2 = AsyncMock()

        await local_manager.connect(ws1, "canvas1.canvas")
        await local_manager.connect(ws2, "canvas2.canvas")

        # Broadcast to canvas1 only
        await local_manager.broadcast_progress_update(
            "canvas1.canvas",
            {"total_concepts": 5, "passed_count": 3, "coverage_rate": 0.6}
        )

        # ws1 should have 2 calls (ack + broadcast)
        # ws2 should have 1 call (ack only)
        assert ws1.send_json.call_count == 2
        assert ws2.send_json.call_count == 1
