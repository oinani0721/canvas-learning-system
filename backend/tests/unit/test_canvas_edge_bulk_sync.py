# Story 36.4: Canvas Edge Bulk Sync to Neo4j - Unit Tests
"""
Unit tests for sync_all_edges_to_neo4j() method and sync-edges endpoint.

Tests verify:
- AC-1: POST /api/v1/canvas/{canvas_path}/sync-edges endpoint
- AC-2: Reads all edges from Canvas and syncs each to Neo4j
- AC-3: Idempotent - MERGE semantics (verified via mock)
- AC-4: Returns summary with total, synced, failed counts
- AC-5: Async processing - concurrent edge syncs
- AC-6: Partial failure handling
- AC-7: Performance (100 edges < 5s)

[Source: docs/stories/36.4.story.md#Task-4]
"""
import asyncio
import json
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.conftest import simulate_async_delay

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
def sample_canvas_with_edges():
    """Sample canvas data with multiple edges for testing."""
    return {
        "nodes": [
            {"id": "node-1", "type": "text", "text": "Concept A", "x": 0, "y": 0},
            {"id": "node-2", "type": "text", "text": "Concept B", "x": 100, "y": 100},
            {"id": "node-3", "type": "text", "text": "Concept C", "x": 200, "y": 200},
            {"id": "node-4", "type": "text", "text": "Concept D", "x": 300, "y": 300},
        ],
        "edges": [
            {"id": "edge-1", "fromNode": "node-1", "toNode": "node-2", "label": "relates_to"},
            {"id": "edge-2", "fromNode": "node-2", "toNode": "node-3", "label": "depends_on"},
            {"id": "edge-3", "fromNode": "node-1", "toNode": "node-3"},
            {"id": "edge-4", "fromNode": "node-3", "toNode": "node-4", "label": "follows"},
        ]
    }


@pytest.fixture
def sample_canvas_no_edges():
    """Sample canvas data without edges."""
    return {
        "nodes": [
            {"id": "node-1", "type": "text", "text": "Concept A", "x": 0, "y": 0}
        ],
        "edges": []
    }


class TestSyncAllEdgesToNeo4j:
    """Tests for sync_all_edges_to_neo4j method."""

    @pytest.mark.asyncio
    async def test_sync_all_edges_success(
        self, canvas_service_with_memory, mock_memory_client, tmp_path, sample_canvas_with_edges
    ):
        """AC-2, AC-4: Verify all edges synced and summary returned."""
        # Setup: Create canvas file
        canvas_path = tmp_path / "test.canvas"
        canvas_path.write_text(json.dumps(sample_canvas_with_edges))

        # Act
        result = await canvas_service_with_memory.sync_all_edges_to_neo4j("test")

        # Assert
        assert result["canvas_path"] == "test"
        assert result["total_edges"] == 4
        assert result["synced_count"] == 4
        assert result["failed_count"] == 0
        assert result["skipped_count"] == 0
        assert result["sync_time_ms"] >= 0

        # Verify Neo4j client was called for each edge
        assert mock_memory_client.neo4j.create_edge_relationship.call_count == 4

    @pytest.mark.asyncio
    async def test_sync_all_edges_empty_canvas(
        self, canvas_service_with_memory, mock_memory_client, tmp_path, sample_canvas_no_edges
    ):
        """AC-4: Verify empty canvas returns zero counts."""
        # Setup
        canvas_path = tmp_path / "empty.canvas"
        canvas_path.write_text(json.dumps(sample_canvas_no_edges))

        # Act
        result = await canvas_service_with_memory.sync_all_edges_to_neo4j("empty")

        # Assert
        assert result["total_edges"] == 0
        assert result["synced_count"] == 0
        assert result["failed_count"] == 0
        assert result["skipped_count"] == 0
        assert result["sync_time_ms"] == 0.0

        # No Neo4j calls
        mock_memory_client.neo4j.create_edge_relationship.assert_not_called()

    @pytest.mark.asyncio
    async def test_sync_all_edges_partial_failure(
        self, canvas_service_with_memory, mock_memory_client, tmp_path, sample_canvas_with_edges
    ):
        """AC-6: Verify partial failure handling - one edge fails, others succeed."""
        # Setup
        canvas_path = tmp_path / "partial.canvas"
        canvas_path.write_text(json.dumps(sample_canvas_with_edges))

        # Track which edges have been processed to ensure consistent failure
        failed_edge_id = "edge-2"

        async def selective_failure(*args, **kwargs):
            # Fail specifically for edge-2, always (persist across retries)
            edge_id = kwargs.get("edge_id", args[1] if len(args) > 1 else None)
            if edge_id == failed_edge_id:
                raise Exception("Simulated Neo4j failure for edge-2")
            return True

        mock_memory_client.neo4j.create_edge_relationship = selective_failure

        # Act
        result = await canvas_service_with_memory.sync_all_edges_to_neo4j("partial")

        # Assert: 3 success, 1 failure (edge-2 fails after retries exhausted)
        assert result["total_edges"] == 4
        # Due to retry mechanism, edge-2 becomes None after 3 retries
        # So synced_count = 3, failed_count = 1
        assert result["synced_count"] == 3
        assert result["failed_count"] == 1

    @pytest.mark.asyncio
    async def test_sync_all_edges_concurrent_execution(
        self, canvas_service_with_memory, mock_memory_client, tmp_path
    ):
        """AC-5: Verify edges are synced concurrently."""
        # Create canvas with many edges
        nodes = [{"id": f"node-{i}", "type": "text", "text": f"Node {i}", "x": i*100, "y": 0}
                 for i in range(20)]
        edges = [{"id": f"edge-{i}", "fromNode": f"node-{i}", "toNode": f"node-{i+1}"}
                 for i in range(19)]

        canvas_data = {"nodes": nodes, "edges": edges}
        canvas_path = tmp_path / "concurrent.canvas"
        canvas_path.write_text(json.dumps(canvas_data))

        # Track concurrent execution
        max_concurrent = 0
        current_concurrent = 0
        lock = asyncio.Lock()

        async def track_concurrency(*args, **kwargs):
            nonlocal max_concurrent, current_concurrent
            async with lock:
                current_concurrent += 1
                max_concurrent = max(max_concurrent, current_concurrent)
            await simulate_async_delay(0.05)  # Simulate some work
            async with lock:
                current_concurrent -= 1
            return True

        mock_memory_client.neo4j.create_edge_relationship = track_concurrency

        # Act
        result = await canvas_service_with_memory.sync_all_edges_to_neo4j("concurrent")

        # Assert: Concurrent execution happened
        assert result["synced_count"] == 19
        # Should have had multiple concurrent executions (limited by semaphore to 12)
        assert max_concurrent > 1, "Expected concurrent execution"
        assert max_concurrent <= 12, f"Expected max 12 concurrent, got {max_concurrent}"

    @pytest.mark.asyncio
    async def test_sync_all_edges_without_memory_client(self, tmp_path, sample_canvas_with_edges):
        """Verify graceful degradation when memory client is None."""
        service = CanvasService(canvas_base_path=str(tmp_path), memory_client=None)
        canvas_path = tmp_path / "no_memory.canvas"
        canvas_path.write_text(json.dumps(sample_canvas_with_edges))

        # Act
        result = await service.sync_all_edges_to_neo4j("no_memory")

        # Assert: All edges skipped (memory client not available)
        assert result["total_edges"] == 4
        assert result["synced_count"] == 0
        assert result["skipped_count"] == 4


class TestSyncEdgesEndpoint:
    """Tests for POST /api/v1/canvas/{canvas_path}/sync-edges endpoint."""

    @pytest.mark.asyncio
    async def test_endpoint_returns_correct_format(
        self, canvas_service_with_memory, mock_memory_client, tmp_path, sample_canvas_with_edges
    ):
        """AC-1, AC-4: Verify endpoint response format."""
        # Setup
        canvas_path = tmp_path / "format_test.canvas"
        canvas_path.write_text(json.dumps(sample_canvas_with_edges))

        # Act
        result = await canvas_service_with_memory.sync_all_edges_to_neo4j("format_test")

        # Assert response format matches SyncEdgesSummaryResponse
        assert "canvas_path" in result
        assert "total_edges" in result
        assert "synced_count" in result
        assert "failed_count" in result
        assert "skipped_count" in result
        assert "sync_time_ms" in result

        # Type checks
        assert isinstance(result["canvas_path"], str)
        assert isinstance(result["total_edges"], int)
        assert isinstance(result["synced_count"], int)
        assert isinstance(result["failed_count"], int)
        assert isinstance(result["skipped_count"], int)
        assert isinstance(result["sync_time_ms"], float)


class TestIdempotentSync:
    """Tests for idempotent sync behavior (AC-3)."""

    @pytest.mark.asyncio
    async def test_repeated_sync_calls_same_result(
        self, canvas_service_with_memory, mock_memory_client, tmp_path, sample_canvas_with_edges
    ):
        """AC-3: Verify idempotency - repeated calls return same counts."""
        # Setup
        canvas_path = tmp_path / "idempotent.canvas"
        canvas_path.write_text(json.dumps(sample_canvas_with_edges))

        # Act: Call twice
        result1 = await canvas_service_with_memory.sync_all_edges_to_neo4j("idempotent")
        result2 = await canvas_service_with_memory.sync_all_edges_to_neo4j("idempotent")

        # Assert: Same edge counts (MERGE doesn't create duplicates)
        assert result1["total_edges"] == result2["total_edges"]
        assert result1["synced_count"] == result2["synced_count"]


class TestPerformance:
    """Performance tests (AC-7)."""

    @pytest.mark.asyncio
    async def test_100_edges_under_5_seconds(
        self, canvas_service_with_memory, mock_memory_client, tmp_path
    ):
        """AC-7: Verify 100 edges sync in < 5 seconds."""
        # Create canvas with 100 edges
        nodes = [{"id": f"node-{i}", "type": "text", "text": f"Node {i}", "x": i*100, "y": 0}
                 for i in range(101)]
        edges = [{"id": f"edge-{i}", "fromNode": f"node-{i}", "toNode": f"node-{i+1}"}
                 for i in range(100)]

        canvas_data = {"nodes": nodes, "edges": edges}
        canvas_path = tmp_path / "performance.canvas"
        canvas_path.write_text(json.dumps(canvas_data))

        # Fast mock (no real network)
        mock_memory_client.neo4j.create_edge_relationship = AsyncMock(return_value=True)

        # Act
        start = time.monotonic()
        result = await canvas_service_with_memory.sync_all_edges_to_neo4j("performance")
        elapsed = time.monotonic() - start

        # Assert
        assert result["total_edges"] == 100
        assert result["synced_count"] == 100
        assert elapsed < 5.0, f"100 edges took {elapsed:.2f}s, should be < 5s"
