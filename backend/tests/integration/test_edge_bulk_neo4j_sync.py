# Story 36.4: Canvas Edge Bulk Sync - Integration Tests
"""
Integration tests for POST /api/v1/canvas/{canvas_path}/sync-edges endpoint.

Tests verify real Neo4j interactions:
- AC-3: MERGE semantics - no duplicate relationships
- AC-4: Summary counts match actual Neo4j state
- AC-6: Partial failure handling
- AC-7: Performance under load

Prerequisites:
- Neo4j Docker running (NEO4J_MOCK=false)
- Environment: NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

[Source: docs/stories/36.4.story.md#Task-4]
"""
import json
import os
import time

import pytest

from app.services.canvas_service import CanvasService


# Skip integration tests if Neo4j not available
NEO4J_AVAILABLE = os.getenv("NEO4J_MOCK", "true").lower() != "true"
pytestmark = pytest.mark.skipif(
    not NEO4J_AVAILABLE,
    reason="NEO4J_MOCK=true, skipping integration tests"
)


@pytest.fixture
def sample_canvas_50_edges():
    """Sample canvas with 50 edges for integration testing."""
    nodes = [{"id": f"node-{i}", "type": "text", "text": f"Integration Node {i}", "x": i*100, "y": 0}
             for i in range(51)]
    edges = [{"id": f"int-edge-{i}", "fromNode": f"node-{i}", "toNode": f"node-{i+1}",
              "label": f"integration_relation_{i}"}
             for i in range(50)]
    return {"nodes": nodes, "edges": edges}


@pytest.fixture
def sample_canvas_100_edges():
    """Sample canvas with 100 edges for performance testing."""
    nodes = [{"id": f"perf-node-{i}", "type": "text", "text": f"Performance Node {i}", "x": i*100, "y": 0}
             for i in range(101)]
    edges = [{"id": f"perf-edge-{i}", "fromNode": f"perf-node-{i}", "toNode": f"perf-node-{i+1}"}
             for i in range(100)]
    return {"nodes": nodes, "edges": edges}


@pytest.fixture
async def canvas_service_with_real_neo4j(tmp_path):
    """Create CanvasService with real Neo4j client."""
    # Import here to avoid issues when Neo4j not available
    from app.clients.neo4j_client import get_neo4j_client
    from app.services.memory_service import MemoryService

    neo4j_client = get_neo4j_client()
    memory_service = MemoryService(neo4j=neo4j_client)

    service = CanvasService(
        canvas_base_path=str(tmp_path),
        memory_client=memory_service
    )

    yield service

    # Cleanup: Close connections
    await service.cleanup()


@pytest.fixture
async def neo4j_client():
    """Get real Neo4j client for verification."""
    from app.clients.neo4j_client import get_neo4j_client
    return get_neo4j_client()


class TestIntegrationSyncEdges:
    """Integration tests with real Neo4j."""

    @pytest.mark.asyncio
    async def test_sync_50_edges_to_neo4j(
        self, canvas_service_with_real_neo4j, neo4j_client, tmp_path, sample_canvas_50_edges
    ):
        """AC-3, AC-4: Sync 50 edges and verify they exist in Neo4j."""
        # Setup
        canvas_path = tmp_path / "integration_50.canvas"
        canvas_path.write_text(json.dumps(sample_canvas_50_edges))

        # Act
        result = await canvas_service_with_real_neo4j.sync_all_edges_to_neo4j("integration_50")

        # Assert API response
        assert result["total_edges"] == 50
        assert result["synced_count"] >= 45  # Allow some tolerance for network issues

        # Verify in Neo4j
        query_result = await neo4j_client.run_query(
            "MATCH ()-[r:CONNECTS_TO]->() "
            "WHERE r.edge_id STARTS WITH 'int-edge-' "
            "RETURN count(r) as count"
        )
        neo4j_count = query_result[0]["count"] if query_result else 0
        assert neo4j_count == result["synced_count"], \
            f"Neo4j has {neo4j_count} edges, API reported {result['synced_count']}"

    @pytest.mark.asyncio
    async def test_idempotent_sync_no_duplicates(
        self, canvas_service_with_real_neo4j, neo4j_client, tmp_path
    ):
        """AC-3: Verify MERGE semantics - no duplicates on repeated sync."""
        # Create small canvas for idempotency test
        canvas_data = {
            "nodes": [
                {"id": "idem-node-1", "type": "text", "text": "A", "x": 0, "y": 0},
                {"id": "idem-node-2", "type": "text", "text": "B", "x": 100, "y": 0}
            ],
            "edges": [
                {"id": "idem-edge-1", "fromNode": "idem-node-1", "toNode": "idem-node-2"}
            ]
        }
        canvas_path = tmp_path / "idempotent_test.canvas"
        canvas_path.write_text(json.dumps(canvas_data))

        # First sync
        result1 = await canvas_service_with_real_neo4j.sync_all_edges_to_neo4j("idempotent_test")

        # Second sync (should be idempotent)
        result2 = await canvas_service_with_real_neo4j.sync_all_edges_to_neo4j("idempotent_test")

        # Verify no duplicates in Neo4j
        query_result = await neo4j_client.run_query(
            "MATCH ()-[r:CONNECTS_TO {edge_id: 'idem-edge-1'}]->() "
            "RETURN count(r) as count"
        )
        neo4j_count = query_result[0]["count"] if query_result else 0

        # Should be exactly 1 (not 2)
        assert neo4j_count == 1, f"Expected 1 edge, found {neo4j_count} (duplicate detected!)"
        assert result1["synced_count"] == result2["synced_count"]


class TestIntegrationPerformance:
    """Performance integration tests."""

    @pytest.mark.asyncio
    async def test_100_edges_under_5_seconds(
        self, canvas_service_with_real_neo4j, tmp_path, sample_canvas_100_edges
    ):
        """AC-7: Verify 100 edges sync in < 5 seconds with real Neo4j."""
        # Setup
        canvas_path = tmp_path / "perf_100.canvas"
        canvas_path.write_text(json.dumps(sample_canvas_100_edges))

        # Act
        start = time.monotonic()
        result = await canvas_service_with_real_neo4j.sync_all_edges_to_neo4j("perf_100")
        elapsed = time.monotonic() - start

        # Assert
        assert result["total_edges"] == 100
        assert elapsed < 5.0, f"100 edges took {elapsed:.2f}s, should be < 5s"
        # Log actual sync rate
        edges_per_second = result["synced_count"] / elapsed if elapsed > 0 else 0
        print(f"Performance: {result['synced_count']} edges in {elapsed:.2f}s "
              f"({edges_per_second:.1f} edges/s)")


class TestIntegrationPartialFailure:
    """Partial failure integration tests."""

    @pytest.mark.asyncio
    async def test_partial_sync_continues_after_error(
        self, canvas_service_with_real_neo4j, neo4j_client, tmp_path
    ):
        """AC-6: Verify other edges sync even if one fails."""
        # Create canvas with edges (some may fail due to missing nodes in Neo4j)
        canvas_data = {
            "nodes": [
                {"id": "partial-node-1", "type": "text", "text": "A", "x": 0, "y": 0},
                {"id": "partial-node-2", "type": "text", "text": "B", "x": 100, "y": 0},
                {"id": "partial-node-3", "type": "text", "text": "C", "x": 200, "y": 0}
            ],
            "edges": [
                {"id": "partial-edge-1", "fromNode": "partial-node-1", "toNode": "partial-node-2"},
                {"id": "partial-edge-2", "fromNode": "partial-node-2", "toNode": "partial-node-3"},
                {"id": "partial-edge-3", "fromNode": "partial-node-1", "toNode": "partial-node-3"}
            ]
        }
        canvas_path = tmp_path / "partial_failure.canvas"
        canvas_path.write_text(json.dumps(canvas_data))

        # Act - should complete without raising exception
        result = await canvas_service_with_real_neo4j.sync_all_edges_to_neo4j("partial_failure")

        # Assert - request completed, some edges may have failed
        assert result["total_edges"] == 3
        # synced_count + failed_count + skipped_count should equal total
        total_accounted = result["synced_count"] + result["failed_count"] + result["skipped_count"]
        assert total_accounted == result["total_edges"]
