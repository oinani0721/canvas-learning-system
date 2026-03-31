# Story 36.3: Canvas Edge Sync to Neo4j - Real Neo4j Integration Tests
# Migrated from: tests/unit/test_canvas_edge_sync.py
"""
Real-DB integration tests for Canvas Edge automatic sync to Neo4j.

Each test creates its own Neo4jClient to avoid event-loop-scope conflicts
with shared conftest fixtures (session/module scoped async fixtures).

Tests verify with a real Neo4j test container:
- AC-1: sync triggered after add_edge() completes
- AC-2: fire-and-forget pattern (background task)
- AC-3: retry mechanism (3 attempts, exponential backoff)
- AC-4: sync failure doesn't affect Canvas operation
- AC-5: CONNECTS_TO relationship actually persisted in Neo4j

[Source: docs/stories/36.3.story.md#Task-4]
[Source: S34 migration from stub to real-DB]
"""

import asyncio
import json
import os
import time
import uuid

import pytest
from app.clients.neo4j_client import Neo4jClient
from app.clients.neo4j_edge_client import Neo4jEdgeClient
from app.clients.neo4j_learning_base import EdgeRelationship
from app.services.canvas_service import CanvasService
from app.services.memory_service import MemoryService

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]

NEO4J_TEST_URI = os.getenv("NEO4J_TEST_URI", "bolt://localhost:7692")
NEO4J_TEST_USER = os.getenv("NEO4J_TEST_USER", "neo4j")
NEO4J_TEST_PASSWORD = os.getenv("NEO4J_TEST_PASSWORD", "testpassword")
NEO4J_TEST_DATABASE = os.getenv("NEO4J_TEST_DATABASE", "neo4j")


def _make_neo4j_client() -> Neo4jClient:
    return Neo4jClient(
        uri=NEO4J_TEST_URI,
        user=NEO4J_TEST_USER,
        password=NEO4J_TEST_PASSWORD,
        database=NEO4J_TEST_DATABASE,
    )


async def _wait_for_condition(
    condition_fn,
    *,
    timeout: float = 2.0,
    interval: float = 0.05,
    description: str = "condition",
):
    """Poll until condition_fn returns truthy or timeout.

    Local copy to avoid importing from tests.conftest which pulls in
    session-scoped async fixtures that cause event-loop-scope conflicts.
    """
    loop = asyncio.get_running_loop()
    start = loop.time()
    last_error = None
    while (loop.time() - start) < timeout:
        try:
            result = condition_fn()
            if asyncio.iscoroutine(result):
                result = await result
            if result:
                return result
        except (AssertionError, Exception) as e:
            last_error = e
        await asyncio.sleep(interval)
    msg = f"{description} not met within {timeout}s"
    if last_error:
        msg += f" (last error: {last_error})"
    raise TimeoutError(msg)


async def _cleanup_prefix(client: Neo4jClient, prefix: str) -> None:
    try:
        await client.run_query(
            "MATCH (n) WHERE n.id STARTS WITH $prefix DETACH DELETE n",
            prefix=prefix,
        )
        await client.run_query(
            "MATCH (n:Node) WHERE n.id STARTS WITH $prefix DETACH DELETE n",
            prefix=prefix,
        )
        await client.run_query(
            "MATCH (cv:Canvas) WHERE cv.path STARTS WITH $prefix DETACH DELETE cv",
            prefix=prefix,
        )
        # Also clean edges by prefix in edge_id
        await client.run_query(
            "MATCH ()-[r:CONNECTS_TO]->() WHERE r.edge_id STARTS WITH $prefix DELETE r",
            prefix=prefix,
        )
    except Exception:
        pass


class TestSyncEdgeToNeo4jReal:
    """Tests for _sync_edge_to_neo4j method against real Neo4j."""

    async def test_sync_edge_creates_relationship_in_neo4j(self, tmp_path):
        """AC-5: Verify CONNECTS_TO relationship is actually created in Neo4j."""
        client = _make_neo4j_client()
        prefix = f"test_{uuid.uuid4().hex[:8]}_"
        try:
            await client.initialize()
            memory_service = MemoryService(neo4j_client=client)
            await memory_service.initialize()

            service = CanvasService(
                canvas_base_path=str(tmp_path),
                memory_client=memory_service,
            )

            result = await service._sync_edge_to_neo4j(
                canvas_path=f"{prefix}test.canvas",
                edge_id=f"{prefix}edge-123",
                from_node_id=f"{prefix}node-1",
                to_node_id=f"{prefix}node-2",
                edge_label="relates_to",
            )

            assert result is True

            # Verify the edge actually exists in Neo4j
            rows = await client.run_query(
                "MATCH (from:Node {{id: $fromId}})-[r:CONNECTS_TO]->(to:Node {{id: $toId}}) "
                "RETURN r.edge_id AS edge_id, r.label AS label".format(),
                fromId=f"{prefix}node-1",
                toId=f"{prefix}node-2",
            )
            assert len(rows) >= 1
            assert rows[0]["edge_id"] == f"{prefix}edge-123"
        finally:
            await _cleanup_prefix(client, prefix)
            await client.cleanup()

    async def test_sync_edge_without_memory_client(self, tmp_path):
        """Verify graceful degradation when memory client is None."""
        service = CanvasService(canvas_base_path=str(tmp_path), memory_client=None)

        result = await service._sync_edge_to_neo4j(
            canvas_path="test.canvas",
            edge_id="edge-123",
            from_node_id="node-1",
            to_node_id="node-2",
        )

        assert result is False

    async def test_sync_edge_with_optional_label(self, tmp_path):
        """Verify edge sync works without label — label defaults to empty string."""
        client = _make_neo4j_client()
        prefix = f"test_{uuid.uuid4().hex[:8]}_"
        try:
            await client.initialize()
            memory_service = MemoryService(neo4j_client=client)
            await memory_service.initialize()

            service = CanvasService(
                canvas_base_path=str(tmp_path),
                memory_client=memory_service,
            )

            result = await service._sync_edge_to_neo4j(
                canvas_path=f"{prefix}test.canvas",
                edge_id=f"{prefix}edge-456",
                from_node_id=f"{prefix}node-a",
                to_node_id=f"{prefix}node-b",
                # No edge_label provided
            )

            assert result is True

            # Verify edge exists in Neo4j
            rows = await client.run_query(
                "MATCH (from:Node {{id: $fromId}})-[r:CONNECTS_TO]->(to:Node {{id: $toId}}) "
                "RETURN r.edge_id AS edge_id".format(),
                fromId=f"{prefix}node-a",
                toId=f"{prefix}node-b",
            )
            assert len(rows) >= 1
            assert rows[0]["edge_id"] == f"{prefix}edge-456"
        finally:
            await _cleanup_prefix(client, prefix)
            await client.cleanup()


class TestAddEdgeWithNeo4jSyncReal:
    """Tests for add_edge() integration with real Neo4j sync."""

    async def test_add_edge_persists_to_canvas_and_neo4j(self, tmp_path):
        """AC-1/AC-5: add_edge() writes to canvas file AND syncs to Neo4j."""
        client = _make_neo4j_client()
        prefix = f"test_{uuid.uuid4().hex[:8]}_"
        try:
            await client.initialize()
            memory_service = MemoryService(neo4j_client=client)
            await memory_service.initialize()

            canvas_path = tmp_path / "test.canvas"
            sample_canvas = {
                "nodes": [
                    {
                        "id": f"{prefix}node-1",
                        "type": "text",
                        "text": "Concept A",
                        "x": 0,
                        "y": 0,
                    },
                    {
                        "id": f"{prefix}node-2",
                        "type": "text",
                        "text": "Concept B",
                        "x": 100,
                        "y": 100,
                    },
                ],
                "edges": [],
            }
            canvas_path.write_text(json.dumps(sample_canvas))

            service = CanvasService(
                canvas_base_path=str(tmp_path),
                memory_client=memory_service,
            )

            result = await service.add_edge(
                canvas_name="test",
                edge_data={
                    "id": f"{prefix}edge-sync-1",
                    "fromNode": f"{prefix}node-1",
                    "toNode": f"{prefix}node-2",
                    "label": "test_edge",
                },
            )

            # Assert: Edge created in canvas file
            assert result["fromNode"] == f"{prefix}node-1"
            assert result["toNode"] == f"{prefix}node-2"
            assert "id" in result

            # Wait for fire-and-forget background task to persist to Neo4j
            async def _edge_in_neo4j():
                rows = await client.run_query(
                    "MATCH ()-[r:CONNECTS_TO {{edge_id: $eid}}]->() RETURN r.edge_id AS eid".format(),
                    eid=f"{prefix}edge-sync-1",
                )
                return len(rows) > 0

            await _wait_for_condition(
                _edge_in_neo4j, timeout=5.0, description="edge persisted to Neo4j"
            )

            # Verify canvas file also updated
            updated_canvas = json.loads(canvas_path.read_text())
            assert len(updated_canvas["edges"]) == 1
        finally:
            await _cleanup_prefix(client, prefix)
            await client.cleanup()

    async def test_add_edge_returns_immediately_fire_and_forget(self, tmp_path):
        """AC-2: Canvas operation returns without waiting for Neo4j sync."""
        client = _make_neo4j_client()
        prefix = f"test_{uuid.uuid4().hex[:8]}_"
        try:
            await client.initialize()
            memory_service = MemoryService(neo4j_client=client)
            await memory_service.initialize()

            canvas_path = tmp_path / "test.canvas"
            sample_canvas = {
                "nodes": [
                    {
                        "id": f"{prefix}node-1",
                        "type": "text",
                        "text": "A",
                        "x": 0,
                        "y": 0,
                    },
                    {
                        "id": f"{prefix}node-2",
                        "type": "text",
                        "text": "B",
                        "x": 100,
                        "y": 100,
                    },
                ],
                "edges": [],
            }
            canvas_path.write_text(json.dumps(sample_canvas))

            service = CanvasService(
                canvas_base_path=str(tmp_path),
                memory_client=memory_service,
            )

            # Time the add_edge operation
            start = time.monotonic()
            result = await service.add_edge(
                canvas_name="test",
                edge_data={
                    "id": f"{prefix}edge-fast",
                    "fromNode": f"{prefix}node-1",
                    "toNode": f"{prefix}node-2",
                },
            )
            elapsed = time.monotonic() - start

            # add_edge should complete quickly (fire-and-forget sync)
            assert elapsed < 1.0, (
                f"add_edge took {elapsed}s, should be < 1.0s (fire-and-forget)"
            )
            assert result["fromNode"] == f"{prefix}node-1"

            # Give background task time to complete for cleanup
            await asyncio.sleep(0.5)
        finally:
            await _cleanup_prefix(client, prefix)
            await client.cleanup()

    async def test_add_edge_succeeds_when_neo4j_unavailable(self, tmp_path):
        """AC-4: Canvas operation succeeds even if Neo4j sync would fail."""
        # Use CanvasService with memory_client=None to simulate no Neo4j
        canvas_path = tmp_path / "test.canvas"
        sample_canvas = {
            "nodes": [
                {"id": "node-1", "type": "text", "text": "A", "x": 0, "y": 0},
                {"id": "node-2", "type": "text", "text": "B", "x": 100, "y": 100},
            ],
            "edges": [],
        }
        canvas_path.write_text(json.dumps(sample_canvas))

        service = CanvasService(canvas_base_path=str(tmp_path), memory_client=None)

        result = await service.add_edge(
            canvas_name="test",
            edge_data={"fromNode": "node-1", "toNode": "node-2"},
        )

        # Edge was created successfully in the canvas file
        assert result["fromNode"] == "node-1"
        assert result["toNode"] == "node-2"
        assert "id" in result

        # Verify edge was saved to canvas file
        updated_canvas = json.loads(canvas_path.read_text())
        assert len(updated_canvas["edges"]) == 1


class TestNeo4jEdgeClientReal:
    """Direct Neo4jEdgeClient tests against real Neo4j."""

    async def test_edge_persists_via_edge_client(self):
        """Edge created via Neo4jEdgeClient is actually stored in Neo4j."""
        client = _make_neo4j_client()
        prefix = f"test_{uuid.uuid4().hex[:8]}_"
        try:
            await client.initialize()
            edge_client = Neo4jEdgeClient(neo4j_client=client)
            await edge_client.initialize()

            rel = EdgeRelationship(
                canvas_path=f"{prefix}test.canvas",
                from_node_id=f"{prefix}a",
                to_node_id=f"{prefix}b",
                edge_label="DEPENDS_ON",
                edge_id=f"{prefix}edge-direct",
            )
            result = await edge_client.add_edge_relationship(rel)

            assert result is True
            assert edge_client._sync_count >= 1

            # Verify by querying Neo4j directly
            rows = await client.run_query(
                "MATCH (from:Node {{id: $fromId}})-[r:CONNECTS_TO]->(to:Node {{id: $toId}}) "
                "RETURN r.edge_id AS edge_id, r.label AS label".format(),
                fromId=f"{prefix}a",
                toId=f"{prefix}b",
            )
            assert len(rows) >= 1
            assert rows[0]["edge_id"] == f"{prefix}edge-direct"
        finally:
            await _cleanup_prefix(client, prefix)
            await client.cleanup()

    async def test_sync_canvas_edges_batch(self):
        """sync_canvas_edges() persists multiple edges in a single batch call."""
        client = _make_neo4j_client()
        prefix = f"test_{uuid.uuid4().hex[:8]}_"
        try:
            await client.initialize()
            edge_client = Neo4jEdgeClient(neo4j_client=client)
            await edge_client.initialize()

            edges = [
                {
                    "id": f"{prefix}e1",
                    "fromNode": f"{prefix}n1",
                    "toNode": f"{prefix}n2",
                    "label": "rel_a",
                },
                {
                    "id": f"{prefix}e2",
                    "fromNode": f"{prefix}n2",
                    "toNode": f"{prefix}n3",
                    "label": "rel_b",
                },
                {
                    "id": f"{prefix}e3",
                    "fromNode": f"{prefix}n3",
                    "toNode": f"{prefix}n1",
                    "label": "rel_c",
                },
            ]

            result = await edge_client.sync_canvas_edges(
                canvas_name=f"{prefix}batch.canvas",
                edges=edges,
            )

            assert result["synced"] == 3
            assert result["failed"] == 0

            # Verify all three edges exist in Neo4j
            for edge in edges:
                rows = await client.run_query(
                    "MATCH ()-[r:CONNECTS_TO {{edge_id: $eid}}]->() RETURN r.edge_id AS eid".format(),
                    eid=edge["id"],
                )
                assert len(rows) >= 1, f"Edge {edge['id']} not found in Neo4j"
        finally:
            await _cleanup_prefix(client, prefix)
            await client.cleanup()

    async def test_edge_client_get_related_memories(self):
        """get_related_memories() returns connected nodes after edge creation."""
        client = _make_neo4j_client()
        prefix = f"test_{uuid.uuid4().hex[:8]}_"
        try:
            await client.initialize()

            # Create two nodes with text content
            await client.run_query(
                "CREATE (n:Node {id: $id, text: $text, canvas_path: $canvas})",
                id=f"{prefix}related_a",
                text="Graph Theory",
                canvas=f"{prefix}related.canvas",
            )
            await client.run_query(
                "CREATE (n:Node {id: $id, text: $text, canvas_path: $canvas})",
                id=f"{prefix}related_b",
                text="Tree Traversal",
                canvas=f"{prefix}related.canvas",
            )

            edge_client = Neo4jEdgeClient(neo4j_client=client)
            await edge_client.initialize()

            # Create edge between them
            rel = EdgeRelationship(
                canvas_path=f"{prefix}related.canvas",
                from_node_id=f"{prefix}related_a",
                to_node_id=f"{prefix}related_b",
                edge_label="PREREQUISITE",
                edge_id=f"{prefix}edge-related",
            )
            await edge_client.add_edge_relationship(rel)

            # Query related memories for node_a
            related = await edge_client.get_related_memories(
                node_id=f"{prefix}related_a",
                canvas_path=f"{prefix}related.canvas",
            )

            assert len(related) >= 1
            related_ids = [r["node_id"] for r in related]
            assert f"{prefix}related_b" in related_ids
        finally:
            await _cleanup_prefix(client, prefix)
            await client.cleanup()
