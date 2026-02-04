# Canvas Learning System - Canvas Memory Integration Tests
# Story 30.5: Canvas CRUD Operations Memory Trigger
# [Source: docs/stories/30.5.story.md#Task-7]
"""
Integration tests for Canvas CRUD memory trigger with MemoryService.

Test Coverage:
- Task 7.1: Test full CRUD flow triggers memory write
- Task 7.2: Test memory write persists to MemoryService (mock Neo4j)
- Task 7.3: Test concurrent CRUD operations with memory writes
- Task 7.4: Test Canvas-Concept relationship is created

Testing Standards:
- Framework: pytest + pytest-asyncio
- Uses real MemoryService with mocked Neo4jClient
"""

import asyncio
import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.canvas_service import CanvasService
from app.services.memory_service import MemoryService, reset_memory_service
from app.clients.neo4j_client import Neo4jClient, reset_neo4j_client


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def temp_canvas_dir(tmp_path):
    """Create temporary directory with test canvas files."""
    # Main test canvas
    canvas_data = {
        "nodes": [
            {"id": "existing-node", "type": "text", "text": "Existing Node", "x": 100, "y": 100}
        ],
        "edges": []
    }
    canvas_file = tmp_path / "test-canvas.canvas"
    canvas_file.write_text(json.dumps(canvas_data), encoding="utf-8")

    # Secondary canvas for concurrent tests
    canvas2_data = {
        "nodes": [
            {"id": "node-a", "type": "text", "text": "Node A", "x": 0, "y": 0}
        ],
        "edges": []
    }
    canvas2_file = tmp_path / "concurrent-canvas.canvas"
    canvas2_file.write_text(json.dumps(canvas2_data), encoding="utf-8")

    return tmp_path


@pytest.fixture
def mock_neo4j_client():
    """Create mock Neo4jClient for integration tests."""
    mock = MagicMock(spec=Neo4jClient)
    mock._use_json_fallback = True
    mock.stats = {"connected": False}  # Simulates JSON fallback mode
    mock.initialize = AsyncMock(return_value=True)
    mock.record_episode = AsyncMock(return_value=True)
    mock.create_canvas_node_relationship = AsyncMock(return_value=True)
    mock.create_edge_relationship = AsyncMock(return_value=True)
    mock.cleanup = AsyncMock()
    return mock


@pytest.fixture
def memory_service(mock_neo4j_client):
    """Create MemoryService with mocked Neo4jClient."""
    reset_memory_service()
    service = MemoryService(neo4j_client=mock_neo4j_client)
    return service


@pytest.fixture
def integrated_canvas_service(temp_canvas_dir, memory_service):
    """Create CanvasService integrated with MemoryService."""
    return CanvasService(
        canvas_base_path=str(temp_canvas_dir),
        memory_client=memory_service,
        session_id="integration-test-session"
    )


# =============================================================================
# Task 7.1: Test full CRUD flow triggers memory write
# =============================================================================

class TestFullCRUDFlow:
    """Test full CRUD flow with memory integration."""

    @pytest.mark.asyncio
    async def test_add_node_full_flow(self, integrated_canvas_service, memory_service):
        """Test add_node triggers complete memory flow."""
        # Arrange
        await memory_service.initialize()
        initial_episode_count = len(memory_service._episodes)

        # Act
        result = await integrated_canvas_service.add_node(
            "test-canvas",
            {
                "type": "text",
                "text": "Integration Test Node",
                "x": 200,
                "y": 200
            }
        )

        # Wait for async task
        await asyncio.sleep(0.2)

        # Assert - CRUD succeeded
        assert result["id"] is not None
        assert result["text"] == "Integration Test Node"

        # Assert - Memory event was recorded
        assert len(memory_service._episodes) > initial_episode_count

        # Find the recorded event
        recorded_event = None
        for ep in memory_service._episodes:
            if ep.get("event_type") == "node_created":
                recorded_event = ep
                break

        assert recorded_event is not None
        assert recorded_event["session_id"] == "integration-test-session"
        assert recorded_event["canvas_path"] == "test-canvas.canvas"
        assert recorded_event["node_id"] == result["id"]

    @pytest.mark.asyncio
    async def test_update_node_full_flow(self, integrated_canvas_service, memory_service):
        """Test update_node triggers complete memory flow."""
        await memory_service.initialize()

        # Act
        result = await integrated_canvas_service.update_node(
            "test-canvas",
            "existing-node",
            {"text": "Updated Text", "color": "3"}
        )

        await asyncio.sleep(0.2)

        # Assert - CRUD succeeded
        assert result["text"] == "Updated Text"
        assert result["color"] == "3"

        # Find the recorded event
        node_updated_events = [
            ep for ep in memory_service._episodes
            if ep.get("event_type") == "node_updated"
        ]
        assert len(node_updated_events) > 0

    @pytest.mark.asyncio
    async def test_add_edge_full_flow(self, integrated_canvas_service, memory_service):
        """Test add_edge triggers complete memory flow."""
        await memory_service.initialize()

        # First create a second node
        await integrated_canvas_service.add_node(
            "test-canvas",
            {"id": "target-node", "type": "text", "text": "Target", "x": 300, "y": 100}
        )

        # Clear to isolate edge test
        initial_count = len(memory_service._episodes)

        # Act
        result = await integrated_canvas_service.add_edge(
            "test-canvas",
            {
                "fromNode": "existing-node",
                "toNode": "target-node",
                "fromSide": "right",
                "toSide": "left"
            }
        )

        await asyncio.sleep(0.2)

        # Assert - CRUD succeeded
        assert result["id"] is not None
        assert result["fromNode"] == "existing-node"
        assert result["toNode"] == "target-node"

        # Find edge_created event
        edge_events = [
            ep for ep in memory_service._episodes
            if ep.get("event_type") == "edge_created"
        ]
        assert len(edge_events) > 0


# =============================================================================
# Task 7.2: Test memory write persists to MemoryService
# =============================================================================

class TestMemoryPersistence:
    """Test that memory writes persist correctly."""

    @pytest.mark.asyncio
    async def test_episode_structure_matches_schema(
        self, integrated_canvas_service, memory_service
    ):
        """Test recorded episode matches temporal-event.schema.json structure."""
        await memory_service.initialize()

        await integrated_canvas_service.add_node(
            "test-canvas",
            {"type": "text", "text": "Schema Test", "x": 0, "y": 0}
        )

        await asyncio.sleep(0.2)

        # Get latest episode
        latest = memory_service._episodes[-1]

        # Verify required fields from temporal-event.schema.json
        assert "event_id" in latest
        assert "session_id" in latest
        assert "event_type" in latest
        assert "timestamp" in latest

        # Verify optional fields present for node events
        assert "canvas_path" in latest
        assert "node_id" in latest
        assert "metadata" in latest

    @pytest.mark.asyncio
    async def test_multiple_events_accumulated(
        self, integrated_canvas_service, memory_service
    ):
        """Test multiple events are accumulated in memory."""
        await memory_service.initialize()
        initial_count = len(memory_service._episodes)

        # Perform multiple operations
        node1 = await integrated_canvas_service.add_node(
            "test-canvas",
            {"type": "text", "text": "Node 1", "x": 0, "y": 0}
        )

        await integrated_canvas_service.update_node(
            "test-canvas",
            node1["id"],
            {"color": "2"}
        )

        node2 = await integrated_canvas_service.add_node(
            "test-canvas",
            {"type": "text", "text": "Node 2", "x": 100, "y": 0}
        )

        await asyncio.sleep(0.3)

        # Should have at least 3 new events
        new_events = len(memory_service._episodes) - initial_count
        assert new_events >= 3


# =============================================================================
# Task 7.3: Test concurrent CRUD operations with memory writes
# =============================================================================

class TestConcurrentOperations:
    """Test concurrent CRUD operations with memory writes."""

    @pytest.mark.asyncio
    async def test_concurrent_add_nodes(
        self, integrated_canvas_service, memory_service
    ):
        """Test concurrent node additions don't cause race conditions."""
        await memory_service.initialize()

        # Create multiple nodes concurrently
        tasks = []
        for i in range(5):
            tasks.append(
                integrated_canvas_service.add_node(
                    "test-canvas",
                    {"type": "text", "text": f"Concurrent Node {i}", "x": i * 100, "y": 0}
                )
            )

        # Execute all concurrently
        results = await asyncio.gather(*tasks)

        await asyncio.sleep(0.3)

        # All should succeed
        assert len(results) == 5
        for i, result in enumerate(results):
            assert result["id"] is not None
            assert result["text"] == f"Concurrent Node {i}"

        # Should have 5 node_created events
        node_created_events = [
            ep for ep in memory_service._episodes
            if ep.get("event_type") == "node_created"
        ]
        assert len(node_created_events) >= 5

    @pytest.mark.asyncio
    async def test_concurrent_operations_different_canvases(
        self, temp_canvas_dir, memory_service
    ):
        """Test concurrent operations on different canvases."""
        await memory_service.initialize()

        # Create two services for different canvases
        service1 = CanvasService(
            canvas_base_path=str(temp_canvas_dir),
            memory_client=memory_service,
            session_id="session-1"
        )
        service2 = CanvasService(
            canvas_base_path=str(temp_canvas_dir),
            memory_client=memory_service,
            session_id="session-2"
        )

        # Concurrent operations on different canvases
        task1 = service1.add_node(
            "test-canvas",
            {"type": "text", "text": "Canvas 1 Node", "x": 0, "y": 0}
        )
        task2 = service2.add_node(
            "concurrent-canvas",
            {"type": "text", "text": "Canvas 2 Node", "x": 0, "y": 0}
        )

        results = await asyncio.gather(task1, task2)

        await asyncio.sleep(0.2)

        # Both should succeed
        assert results[0]["text"] == "Canvas 1 Node"
        assert results[1]["text"] == "Canvas 2 Node"

        # Should have events for both canvases
        canvas_paths = [ep.get("canvas_path") for ep in memory_service._episodes]
        assert "test-canvas.canvas" in canvas_paths
        assert "concurrent-canvas.canvas" in canvas_paths


# =============================================================================
# Task 7.4: Test Canvas-Concept relationship is created
# =============================================================================

class TestCanvasConceptRelationship:
    """Test Canvas-Concept relationship graph creation."""

    @pytest.mark.asyncio
    async def test_node_relationship_created_on_connected_neo4j(
        self, temp_canvas_dir, mock_neo4j_client
    ):
        """Test Canvas-Node relationship created when Neo4j is connected."""
        # Configure mock to simulate connected Neo4j
        mock_neo4j_client.stats = {"connected": True}

        memory_service = MemoryService(neo4j_client=mock_neo4j_client)
        await memory_service.initialize()

        service = CanvasService(
            canvas_base_path=str(temp_canvas_dir),
            memory_client=memory_service,
            session_id="relationship-test"
        )

        # Act
        result = await service.add_node(
            "test-canvas",
            {"type": "text", "text": "Concept: Machine Learning", "x": 0, "y": 0}
        )

        await asyncio.sleep(0.2)

        # Assert - relationship creation was attempted
        mock_neo4j_client.create_canvas_node_relationship.assert_called()

        # Verify call arguments
        call_args = mock_neo4j_client.create_canvas_node_relationship.call_args
        assert call_args.kwargs["canvas_path"] == "test-canvas.canvas"
        assert call_args.kwargs["node_id"] == result["id"]

    @pytest.mark.asyncio
    async def test_edge_relationship_created_on_connected_neo4j(
        self, temp_canvas_dir, mock_neo4j_client
    ):
        """Test edge relationship created when Neo4j is connected."""
        # Configure mock to simulate connected Neo4j
        mock_neo4j_client.stats = {"connected": True}

        memory_service = MemoryService(neo4j_client=mock_neo4j_client)
        await memory_service.initialize()

        service = CanvasService(
            canvas_base_path=str(temp_canvas_dir),
            memory_client=memory_service,
            session_id="edge-relationship-test"
        )

        # Create target node
        await service.add_node(
            "test-canvas",
            {"id": "node-b", "type": "text", "text": "Node B", "x": 200, "y": 0}
        )

        # Reset mock to isolate edge test
        mock_neo4j_client.create_edge_relationship.reset_mock()

        # Act - add edge
        result = await service.add_edge(
            "test-canvas",
            {
                "fromNode": "existing-node",
                "toNode": "node-b",
                "fromSide": "right",
                "toSide": "left"
            }
        )

        await asyncio.sleep(0.2)

        # Assert - edge relationship creation was attempted
        mock_neo4j_client.create_edge_relationship.assert_called()

    @pytest.mark.asyncio
    async def test_relationship_not_created_when_neo4j_disconnected(
        self, temp_canvas_dir, mock_neo4j_client
    ):
        """Test no relationship creation attempted when Neo4j is disconnected."""
        # Configure mock to simulate disconnected Neo4j
        mock_neo4j_client.stats = {"connected": False}

        memory_service = MemoryService(neo4j_client=mock_neo4j_client)
        await memory_service.initialize()

        service = CanvasService(
            canvas_base_path=str(temp_canvas_dir),
            memory_client=memory_service,
            session_id="disconnected-test"
        )

        # Act
        await service.add_node(
            "test-canvas",
            {"type": "text", "text": "Test Node", "x": 0, "y": 0}
        )

        await asyncio.sleep(0.2)

        # Assert - no Neo4j relationship calls made
        mock_neo4j_client.create_canvas_node_relationship.assert_not_called()


# =============================================================================
# Performance Tests
# =============================================================================

class TestPerformance:
    """Test performance characteristics."""

    @pytest.mark.asyncio
    async def test_crud_response_time_under_threshold(
        self, integrated_canvas_service, memory_service
    ):
        """Test CRUD response time is under 50ms overhead from memory trigger."""
        import time

        await memory_service.initialize()

        # Measure without memory client
        service_no_memory = CanvasService(
            canvas_base_path=integrated_canvas_service.canvas_base_path,
            memory_client=None
        )

        start = time.time()
        await service_no_memory.add_node(
            "test-canvas",
            {"type": "text", "text": "Baseline", "x": 0, "y": 0}
        )
        baseline_time = time.time() - start

        # Measure with memory client
        start = time.time()
        await integrated_canvas_service.add_node(
            "test-canvas",
            {"type": "text", "text": "With Memory", "x": 100, "y": 0}
        )
        with_memory_time = time.time() - start

        # Overhead should be minimal (memory trigger is fire-and-forget)
        overhead = with_memory_time - baseline_time
        assert overhead < 0.05, f"Memory overhead {overhead:.3f}s should be < 50ms"
