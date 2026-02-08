# Canvas Learning System - Canvas Memory Trigger Unit Tests
# Story 30.5: Canvas CRUD Operations Memory Trigger
# [Source: docs/stories/30.5.story.md#Task-6]
"""
Unit tests for Canvas CRUD memory trigger mechanism.

Test Coverage:
- Task 6.1: canvas_events.py models validate correctly
- Task 6.2: _trigger_memory_event() is called after add_node()
- Task 6.3: _trigger_memory_event() is called after update_node()
- Task 6.4: _trigger_memory_event() is called after add_edge()
- Task 6.5: Async write doesn't block CRUD response
- Task 6.6: Silent degradation on memory write failure

Testing Standards:
- Framework: pytest + pytest-asyncio
- Mock: unittest.mock.AsyncMock for MemoryService
"""

import asyncio
import json
import pytest
import tempfile
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.canvas_events import CanvasEvent, CanvasEventContext, CanvasEventType
from app.services.canvas_service import CanvasService


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def temp_canvas_dir(tmp_path):
    """Create temporary directory with a test canvas file."""
    canvas_data = {
        "nodes": [
            {"id": "node1", "type": "text", "text": "Test Node 1", "x": 100, "y": 100}
        ],
        "edges": []
    }
    canvas_file = tmp_path / "test-canvas.canvas"
    canvas_file.write_text(json.dumps(canvas_data), encoding="utf-8")
    return tmp_path


@pytest.fixture
def mock_memory_client():
    """Create mock MemoryService with AsyncMock methods."""
    mock = AsyncMock()
    mock.record_temporal_event = AsyncMock(return_value="event-123")
    mock.initialize = AsyncMock(return_value=True)
    return mock


@pytest.fixture
def canvas_service_with_memory(temp_canvas_dir, mock_memory_client):
    """Create CanvasService with mock memory client."""
    return CanvasService(
        canvas_base_path=str(temp_canvas_dir),
        memory_client=mock_memory_client,
        session_id="test-session-123"
    )


@pytest.fixture
def canvas_service_no_memory(temp_canvas_dir):
    """Create CanvasService without memory client (mock mode)."""
    return CanvasService(
        canvas_base_path=str(temp_canvas_dir),
        memory_client=None
    )


# =============================================================================
# Task 6.1: Test canvas_events.py models validate correctly
# =============================================================================

class TestCanvasEventModels:
    """Test CanvasEvent and related model validation."""

    def test_canvas_event_type_enum_values(self):
        """Test CanvasEventType enum contains expected values."""
        assert CanvasEventType.NODE_CREATED.value == "node_created"
        assert CanvasEventType.NODE_UPDATED.value == "node_updated"
        assert CanvasEventType.EDGE_CREATED.value == "edge_created"

    def test_canvas_event_creation_with_required_fields(self):
        """Test CanvasEvent can be created with required fields."""
        event = CanvasEvent(
            session_id="test-session",
            event_type=CanvasEventType.NODE_CREATED,
            canvas_path="test.canvas"
        )
        assert event.session_id == "test-session"
        assert event.event_type == CanvasEventType.NODE_CREATED
        assert event.canvas_path == "test.canvas"
        assert event.event_id is not None  # Auto-generated
        assert event.timestamp is not None  # Auto-generated

    def test_canvas_event_with_optional_fields(self):
        """Test CanvasEvent with optional node_id, edge_id, metadata."""
        event = CanvasEvent(
            session_id="test-session",
            event_type=CanvasEventType.NODE_CREATED,
            canvas_path="test.canvas",
            node_id="node123",
            edge_id=None,
            metadata={"concept": "Test Concept"}
        )
        assert event.node_id == "node123"
        assert event.edge_id is None
        assert event.metadata == {"concept": "Test Concept"}

    def test_canvas_event_context_to_metadata(self):
        """Test CanvasEventContext.to_metadata() extracts node/edge data."""
        context = CanvasEventContext(
            canvas_name="test-canvas",
            node_id="node123",
            node_data={
                "text": "Machine Learning",
                "type": "text",
                "color": "4"
            }
        )
        metadata = context.to_metadata()
        assert metadata["node_text"] == "Machine Learning"
        assert metadata["node_type"] == "text"
        assert metadata["node_color"] == "4"

    def test_canvas_event_context_edge_metadata(self):
        """Test CanvasEventContext extracts edge data for edges."""
        context = CanvasEventContext(
            canvas_name="test-canvas",
            edge_id="edge123",
            edge_data={
                "fromNode": "node1",
                "toNode": "node2",
                "label": "relates_to"
            }
        )
        metadata = context.to_metadata()
        assert metadata["from_node"] == "node1"
        assert metadata["to_node"] == "node2"
        assert metadata["edge_label"] == "relates_to"


# =============================================================================
# Task 6.2: Test _trigger_memory_event() is called after add_node()
# =============================================================================

class TestAddNodeMemoryTrigger:
    """Test add_node() triggers node_created memory event."""

    @pytest.mark.asyncio
    async def test_add_node_triggers_memory_event(
        self, canvas_service_with_memory, mock_memory_client, wait_for_call
    ):
        """Test that add_node triggers node_created memory event (AC-30.5.1)."""
        # Act
        result = await canvas_service_with_memory.add_node(
            "test-canvas",
            {
                "type": "text",
                "text": "New Concept Node",
                "x": 200,
                "y": 200
            }
        )

        # Assert - CRUD succeeded
        assert result["id"] is not None
        assert result["type"] == "text"
        assert result["text"] == "New Concept Node"

        # Assert - Memory event was triggered (poll for async task)
        await wait_for_call(mock_memory_client.record_temporal_event)
        mock_memory_client.record_temporal_event.assert_called()

        # Verify call arguments
        call_args = mock_memory_client.record_temporal_event.call_args
        assert call_args.kwargs["event_type"] == "node_created"
        assert call_args.kwargs["canvas_path"] == "test-canvas.canvas"
        assert call_args.kwargs["node_id"] == result["id"]

    @pytest.mark.asyncio
    async def test_add_node_without_memory_client(self, canvas_service_no_memory):
        """Test add_node works when memory client is None (mock mode)."""
        # Act - should not raise
        result = await canvas_service_no_memory.add_node(
            "test-canvas",
            {"type": "text", "text": "Test", "x": 0, "y": 0}
        )

        # Assert - CRUD still works
        assert result["id"] is not None
        assert result["text"] == "Test"


# =============================================================================
# Task 6.3: Test _trigger_memory_event() is called after update_node()
# =============================================================================

class TestUpdateNodeMemoryTrigger:
    """Test update_node() triggers node_updated memory event."""

    @pytest.mark.asyncio
    async def test_update_node_triggers_memory_event(
        self, canvas_service_with_memory, mock_memory_client, wait_for_call
    ):
        """Test that update_node triggers node_updated memory event (AC-30.5.3)."""
        # Act
        result = await canvas_service_with_memory.update_node(
            "test-canvas",
            "node1",
            {"text": "Updated Text", "color": "2"}
        )

        # Assert - CRUD succeeded
        assert result["id"] == "node1"
        assert result["text"] == "Updated Text"
        assert result["color"] == "2"

        # Assert - Memory event was triggered
        await wait_for_call(mock_memory_client.record_temporal_event)
        mock_memory_client.record_temporal_event.assert_called()

        # Verify call arguments
        call_args = mock_memory_client.record_temporal_event.call_args
        assert call_args.kwargs["event_type"] == "node_updated"
        assert call_args.kwargs["node_id"] == "node1"


# =============================================================================
# Task 6.4: Test _trigger_memory_event() is called after add_edge()
# =============================================================================

class TestAddEdgeMemoryTrigger:
    """Test add_edge() triggers edge_created memory event."""

    @pytest.mark.asyncio
    async def test_add_edge_triggers_memory_event(
        self, canvas_service_with_memory, mock_memory_client, temp_canvas_dir,
        wait_for_call
    ):
        """Test that add_edge triggers edge_created memory event (AC-30.5.2)."""
        # First add a second node for the edge
        await canvas_service_with_memory.add_node(
            "test-canvas",
            {"id": "node2", "type": "text", "text": "Node 2", "x": 300, "y": 100}
        )

        # Reset mock to isolate edge test
        mock_memory_client.record_temporal_event.reset_mock()

        # Act
        result = await canvas_service_with_memory.add_edge(
            "test-canvas",
            {
                "fromNode": "node1",
                "toNode": "node2",
                "fromSide": "right",
                "toSide": "left"
            }
        )

        # Assert - CRUD succeeded
        assert result["id"] is not None
        assert result["fromNode"] == "node1"
        assert result["toNode"] == "node2"

        # Assert - Memory event was triggered
        await wait_for_call(mock_memory_client.record_temporal_event)
        mock_memory_client.record_temporal_event.assert_called()

        # Verify call arguments
        call_args = mock_memory_client.record_temporal_event.call_args
        assert call_args.kwargs["event_type"] == "edge_created"
        assert call_args.kwargs["edge_id"] == result["id"]


# =============================================================================
# Task 6.5: Test async write doesn't block CRUD response
# =============================================================================

class TestAsyncNonBlocking:
    """Test that memory write doesn't block CRUD response."""

    @pytest.mark.asyncio
    async def test_slow_memory_write_does_not_block_crud(
        self, temp_canvas_dir
    ):
        """Test CRUD returns immediately even if memory write is slow."""
        # Create a slow memory client (1 second delay)
        slow_memory_client = AsyncMock()

        async def slow_record(*args, **kwargs):
            await asyncio.sleep(1.0)  # 1 second delay
            return "event-slow"

        slow_memory_client.record_temporal_event = slow_record

        service = CanvasService(
            canvas_base_path=str(temp_canvas_dir),
            memory_client=slow_memory_client,
            session_id="test-session"
        )

        # Act - time the operation
        start = time.time()
        result = await service.add_node(
            "test-canvas",
            {"type": "text", "text": "Test", "x": 0, "y": 0}
        )
        elapsed = time.time() - start

        # Assert - CRUD should complete much faster than 1 second
        # (fire-and-forget pattern means we don't wait)
        assert result["id"] is not None
        assert elapsed < 0.5, f"CRUD took {elapsed:.2f}s, should be < 0.5s"


# =============================================================================
# Task 6.6: Test silent degradation on memory write failure
# =============================================================================

class TestSilentDegradation:
    """Test that memory write failures don't affect CRUD operations."""

    @pytest.mark.asyncio
    async def test_memory_failure_does_not_block_crud(self, temp_canvas_dir):
        """Test that memory write failure doesn't block CRUD response."""
        # Create a failing memory client
        failing_memory_client = AsyncMock()
        failing_memory_client.record_temporal_event = AsyncMock(
            side_effect=Exception("Neo4j connection failed")
        )

        service = CanvasService(
            canvas_base_path=str(temp_canvas_dir),
            memory_client=failing_memory_client,
            session_id="test-session"
        )

        # Act - should not raise despite memory failure
        result = await service.add_node(
            "test-canvas",
            {"type": "text", "text": "Test", "x": 0, "y": 0}
        )

        # Assert - CRUD still succeeds
        assert result["id"] is not None
        assert result["type"] == "text"

    @pytest.mark.asyncio
    async def test_memory_timeout_handled_gracefully(self, temp_canvas_dir):
        """Test that memory write timeout is handled gracefully (500ms timeout)."""
        # Create a timeout-causing memory client
        timeout_memory_client = AsyncMock()

        async def timeout_record(*args, **kwargs):
            await asyncio.sleep(2.0)  # 2 second delay (will timeout at 500ms)
            return "event-timeout"

        timeout_memory_client.record_temporal_event = timeout_record

        service = CanvasService(
            canvas_base_path=str(temp_canvas_dir),
            memory_client=timeout_memory_client,
            session_id="test-session"
        )

        # Act - should not raise despite timeout
        result = await service.add_node(
            "test-canvas",
            {"type": "text", "text": "Test Timeout", "x": 0, "y": 0}
        )

        # Assert - CRUD still succeeds
        assert result["id"] is not None
        assert result["text"] == "Test Timeout"


# =============================================================================
# Additional Edge Case Tests
# =============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_multiple_consecutive_operations(
        self, canvas_service_with_memory, mock_memory_client, wait_for_call
    ):
        """Test multiple CRUD operations trigger correct events."""
        # Add node
        node1 = await canvas_service_with_memory.add_node(
            "test-canvas",
            {"type": "text", "text": "Node A", "x": 0, "y": 0}
        )

        # Update node
        await canvas_service_with_memory.update_node(
            "test-canvas",
            "node1",
            {"color": "3"}
        )

        # Add another node
        node2 = await canvas_service_with_memory.add_node(
            "test-canvas",
            {"type": "text", "text": "Node B", "x": 100, "y": 0}
        )

        # Add edge
        edge = await canvas_service_with_memory.add_edge(
            "test-canvas",
            {"fromNode": node1["id"], "toNode": node2["id"]}
        )

        # Wait for async tasks (poll until all 4 events are recorded)
        await wait_for_call(mock_memory_client.record_temporal_event, expected_count=4)

        # Should have 4 memory event calls
        assert mock_memory_client.record_temporal_event.call_count >= 4

    @pytest.mark.asyncio
    async def test_session_id_is_passed_to_memory_event(
        self, canvas_service_with_memory, mock_memory_client, wait_for_call
    ):
        """Test that session_id is correctly passed to memory events."""
        await canvas_service_with_memory.add_node(
            "test-canvas",
            {"type": "text", "text": "Test", "x": 0, "y": 0}
        )

        await wait_for_call(mock_memory_client.record_temporal_event)

        call_args = mock_memory_client.record_temporal_event.call_args
        assert call_args.kwargs["session_id"] == "test-session-123"


# =============================================================================
# Story 30.6: Color metadata extraction tests
# =============================================================================

class TestColorMetadataExtraction:
    """Test CanvasEventContext color metadata extraction for Story 30.6."""

    def test_to_metadata_extracts_node_color(self):
        """Test that to_metadata() extracts node_color from node_data (AC-30.6.1)."""
        context = CanvasEventContext(
            canvas_name="test-canvas",
            node_id="node1",
            node_data={"color": "1", "text": "Concept", "type": "text"}
        )
        metadata = context.to_metadata()
        assert metadata["node_color"] == "1"

    def test_to_metadata_no_color_field(self):
        """Test that to_metadata() omits node_color when color is absent."""
        context = CanvasEventContext(
            canvas_name="test-canvas",
            node_id="node1",
            node_data={"text": "No color node", "type": "text"}
        )
        metadata = context.to_metadata()
        assert "node_color" not in metadata

    def test_to_metadata_color_with_text(self):
        """Test that both node_color and node_text are extracted together."""
        context = CanvasEventContext(
            canvas_name="test-canvas",
            node_id="node1",
            node_data={"color": "4", "text": "Yellow concept", "type": "text"}
        )
        metadata = context.to_metadata()
        assert metadata["node_color"] == "4"
        assert metadata["node_text"] == "Yellow concept"

    def test_color_changed_event_type_exists(self):
        """Test that COLOR_CHANGED event type is defined (AC-30.6.1)."""
        assert CanvasEventType.COLOR_CHANGED.value == "color_changed"

    def test_color_removed_event_type_exists(self):
        """Test that COLOR_REMOVED event type is defined (AC-30.6.1)."""
        assert CanvasEventType.COLOR_REMOVED.value == "color_removed"
