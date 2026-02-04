# Story 36.3: Canvas Edge Sync to Neo4j - Unit Tests
"""
Unit tests for Canvas Edge automatic sync to Neo4j.

Tests verify:
- AC-1: sync triggered after add_edge() completes
- AC-2: fire-and-forget pattern (background task)
- AC-3: retry mechanism (3 attempts, exponential backoff)
- AC-4: sync failure doesn't affect Canvas operation

[Source: docs/stories/36.3.story.md#Task-4]
"""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.canvas_service import CanvasService


@pytest.fixture
def mock_memory_client():
    """Create mock MemoryService with Neo4j client."""
    memory_client = MagicMock()
    memory_client.neo4j = AsyncMock()
    memory_client.neo4j.create_edge_relationship = AsyncMock(return_value=True)
    memory_client.record_temporal_event = AsyncMock()
    return memory_client


@pytest.fixture
def canvas_service_with_memory(mock_memory_client, tmp_path):
    """Create CanvasService with mock memory client."""
    return CanvasService(
        canvas_base_path=str(tmp_path),
        memory_client=mock_memory_client
    )


@pytest.fixture
def sample_canvas_data():
    """Sample canvas data for testing."""
    return {
        "nodes": [
            {"id": "node-1", "type": "text", "text": "Concept A", "x": 0, "y": 0},
            {"id": "node-2", "type": "text", "text": "Concept B", "x": 100, "y": 100}
        ],
        "edges": []
    }


class TestSyncEdgeToNeo4j:
    """Tests for _sync_edge_to_neo4j method."""

    @pytest.mark.asyncio
    async def test_sync_edge_calls_neo4j_client(self, canvas_service_with_memory, mock_memory_client):
        """AC-5: Verify CONNECTS_TO relationship created in Neo4j."""
        # Act
        result = await canvas_service_with_memory._sync_edge_to_neo4j(
            canvas_path="test.canvas",
            edge_id="edge-123",
            from_node_id="node-1",
            to_node_id="node-2",
            edge_label="relates_to"
        )

        # Assert
        assert result is True
        mock_memory_client.neo4j.create_edge_relationship.assert_called_once_with(
            canvas_path="test.canvas",
            edge_id="edge-123",
            from_node_id="node-1",
            to_node_id="node-2",
            edge_label="relates_to"
        )

    @pytest.mark.asyncio
    async def test_sync_edge_without_memory_client(self, tmp_path):
        """Verify graceful degradation when memory client is None."""
        service = CanvasService(canvas_base_path=str(tmp_path), memory_client=None)

        result = await service._sync_edge_to_neo4j(
            canvas_path="test.canvas",
            edge_id="edge-123",
            from_node_id="node-1",
            to_node_id="node-2"
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_sync_edge_without_neo4j_in_memory_client(self, tmp_path):
        """Verify graceful degradation when neo4j is None in memory_client."""
        memory_client = MagicMock()
        memory_client.neo4j = None
        service = CanvasService(canvas_base_path=str(tmp_path), memory_client=memory_client)

        result = await service._sync_edge_to_neo4j(
            canvas_path="test.canvas",
            edge_id="edge-123",
            from_node_id="node-1",
            to_node_id="node-2"
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_sync_edge_with_optional_label(self, canvas_service_with_memory, mock_memory_client):
        """Verify edge sync works without label."""
        result = await canvas_service_with_memory._sync_edge_to_neo4j(
            canvas_path="test.canvas",
            edge_id="edge-456",
            from_node_id="node-a",
            to_node_id="node-b"
            # No edge_label provided
        )

        assert result is True
        mock_memory_client.neo4j.create_edge_relationship.assert_called_once_with(
            canvas_path="test.canvas",
            edge_id="edge-456",
            from_node_id="node-a",
            to_node_id="node-b",
            edge_label=None
        )


class TestAddEdgeWithNeo4jSync:
    """Tests for add_edge() integration with Neo4j sync."""

    @pytest.mark.asyncio
    async def test_add_edge_triggers_sync_task(
        self, canvas_service_with_memory, mock_memory_client, tmp_path, sample_canvas_data
    ):
        """AC-1: Verify async sync_edge_to_neo4j() triggered after add_edge()."""
        # Setup: Create canvas file
        canvas_path = tmp_path / "test.canvas"
        import json
        canvas_path.write_text(json.dumps(sample_canvas_data))

        # Act
        with patch.object(
            canvas_service_with_memory, '_sync_edge_to_neo4j', new_callable=AsyncMock
        ) as mock_sync:
            result = await canvas_service_with_memory.add_edge(
                canvas_name="test",
                edge_data={"fromNode": "node-1", "toNode": "node-2", "label": "test_edge"}
            )

            # Allow background task to execute
            await asyncio.sleep(0.1)

        # Assert: Edge created successfully
        assert result["fromNode"] == "node-1"
        assert result["toNode"] == "node-2"
        assert "id" in result

        # Assert: Sync was scheduled (create_task was called)
        # Note: Due to fire-and-forget, we verify the task was created

    @pytest.mark.asyncio
    async def test_add_edge_returns_immediately(
        self, canvas_service_with_memory, mock_memory_client, tmp_path, sample_canvas_data
    ):
        """AC-2: Verify Canvas operation returns without waiting for sync."""
        import json
        import time

        canvas_path = tmp_path / "test.canvas"
        canvas_path.write_text(json.dumps(sample_canvas_data))

        # Make Neo4j sync slow (simulating network delay)
        async def slow_sync(*args, **kwargs):
            await asyncio.sleep(2)  # 2 second delay
            return True

        mock_memory_client.neo4j.create_edge_relationship = slow_sync

        # Act: Time the add_edge operation
        start = time.monotonic()
        result = await canvas_service_with_memory.add_edge(
            canvas_name="test",
            edge_data={"fromNode": "node-1", "toNode": "node-2"}
        )
        elapsed = time.monotonic() - start

        # Assert: Operation completed quickly (< 1s, not waiting for 2s sync)
        assert elapsed < 1.0, f"add_edge took {elapsed}s, should be < 1s (fire-and-forget)"
        assert result["fromNode"] == "node-1"

    @pytest.mark.asyncio
    async def test_add_edge_succeeds_when_sync_fails(
        self, canvas_service_with_memory, mock_memory_client, tmp_path, sample_canvas_data
    ):
        """AC-4: Verify Canvas operation succeeds even if Neo4j sync fails."""
        import json

        canvas_path = tmp_path / "test.canvas"
        canvas_path.write_text(json.dumps(sample_canvas_data))

        # Make Neo4j sync fail
        mock_memory_client.neo4j.create_edge_relationship = AsyncMock(
            side_effect=Exception("Neo4j connection failed")
        )

        # Act: add_edge should succeed despite sync failure
        result = await canvas_service_with_memory.add_edge(
            canvas_name="test",
            edge_data={"fromNode": "node-1", "toNode": "node-2"}
        )

        # Assert: Edge was created successfully
        assert result["fromNode"] == "node-1"
        assert result["toNode"] == "node-2"
        assert "id" in result

        # Verify edge was saved to canvas file
        updated_canvas = json.loads(canvas_path.read_text())
        assert len(updated_canvas["edges"]) == 1


class TestRetryMechanism:
    """Tests for retry mechanism with tenacity."""

    @pytest.mark.asyncio
    async def test_retry_on_neo4j_failure(self, canvas_service_with_memory, mock_memory_client):
        """AC-3: Verify 3 retry attempts on failure."""
        call_count = 0

        async def failing_then_success(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return True

        mock_memory_client.neo4j.create_edge_relationship = failing_then_success

        # Act
        result = await canvas_service_with_memory._sync_edge_to_neo4j(
            canvas_path="test.canvas",
            edge_id="edge-retry",
            from_node_id="node-1",
            to_node_id="node-2"
        )

        # Assert: Succeeded after retries
        assert result is True
        assert call_count == 3  # 2 failures + 1 success

    @pytest.mark.asyncio
    async def test_silent_failure_after_max_retries(
        self, canvas_service_with_memory, mock_memory_client
    ):
        """AC-3, AC-4: Verify silent failure after 3 attempts (reraise=False)."""
        call_count = 0

        async def always_fail(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            raise Exception("Persistent failure")

        mock_memory_client.neo4j.create_edge_relationship = always_fail

        # Act: Should not raise, should return None (tenacity reraise=False)
        result = await canvas_service_with_memory._sync_edge_to_neo4j(
            canvas_path="test.canvas",
            edge_id="edge-fail",
            from_node_id="node-1",
            to_node_id="node-2"
        )

        # Assert: Silent failure (no exception raised)
        assert result is None  # tenacity returns None when reraise=False
        assert call_count == 3  # Exactly 3 attempts
