"""
S33 Migration: Real Neo4j integration tests for GraphitiEdgeClient.

Each test creates its own Neo4jClient to avoid event-loop-scope conflicts.

[Source: S33 Phase1 — Real-Neo4j migration]
"""

import os
import uuid

import pytest

from app.clients.graphiti_client import GraphitiEdgeClient
from app.clients.graphiti_client_base import EdgeRelationship
from app.clients.neo4j_client import Neo4jClient

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]

NEO4J_TEST_URI = os.getenv("NEO4J_TEST_URI", "bolt://localhost:7692")
NEO4J_TEST_USER = os.getenv("NEO4J_TEST_USER", "neo4j")
NEO4J_TEST_PASSWORD = os.getenv("NEO4J_TEST_PASSWORD", "testpassword")
NEO4J_TEST_DATABASE = os.getenv("NEO4J_TEST_DATABASE", "neo4j")


def _make_client() -> Neo4jClient:
    return Neo4jClient(
        uri=NEO4J_TEST_URI,
        user=NEO4J_TEST_USER,
        password=NEO4J_TEST_PASSWORD,
        database=NEO4J_TEST_DATABASE,
    )


async def _cleanup_prefix(client: Neo4jClient, prefix: str) -> None:
    try:
        await client.run_query(
            "MATCH (n) WHERE n.id STARTS WITH $prefix DETACH DELETE n",
            prefix=prefix,
        )
        await client.run_query(
            "MATCH (c:Concept) WHERE c.name STARTS WITH $prefix DETACH DELETE c",
            prefix=prefix,
        )
        await client.run_query(
            "MATCH (cv:Canvas) WHERE cv.path STARTS WITH $prefix DETACH DELETE cv",
            prefix=prefix,
        )
    except Exception:
        pass


class TestRealGraphitiEdgeClientDI:
    """DI wiring tests against real Neo4j."""

    async def test_injection_with_real_client(self):
        """GraphitiEdgeClient receives and exposes the injected Neo4jClient."""
        client = _make_client()
        try:
            await client.initialize()
            graphiti = GraphitiEdgeClient(neo4j_client=client)

            assert graphiti._neo4j is client
            assert graphiti.is_neo4j_enabled is True
            assert graphiti.is_fallback_mode is False
            assert graphiti.neo4j_client is client
        finally:
            await client.cleanup()


class TestRealGraphitiEdgeClientMethods:
    """Functional tests against real Neo4j."""

    async def test_initialize_real(self):
        """initialize() succeeds against a live Neo4j."""
        client = _make_client()
        try:
            await client.initialize()
            graphiti = GraphitiEdgeClient(neo4j_client=client)
            result = await graphiti.initialize()

            assert result is True
            assert graphiti._initialized is True
        finally:
            await client.cleanup()

    async def test_add_edge_relationship_persists_to_neo4j(self):
        """add_edge_relationship() creates real nodes and edge in Neo4j."""
        client = _make_client()
        prefix = f"test_{uuid.uuid4().hex[:8]}_"
        try:
            await client.initialize()
            graphiti = GraphitiEdgeClient(neo4j_client=client)
            await graphiti.initialize()

            relationship = EdgeRelationship(
                canvas_path=f"{prefix}test.canvas",
                from_node_id=f"{prefix}nodeA",
                to_node_id=f"{prefix}nodeB",
                edge_label="RELATED_TO",
                edge_id=f"{prefix}edge001",
            )

            success = await graphiti.add_edge_relationship(relationship)

            assert success is True
            assert graphiti._sync_count >= 1

            # Verify the edge actually persisted
            results = await client.run_query(
                "MATCH (from:Node {id: $fromId})-[r:CONNECTS_TO]->(to:Node {id: $toId}) "
                "RETURN r.edge_id as edge_id, r.label as label",
                fromId=f"{prefix}nodeA",
                toId=f"{prefix}nodeB",
            )

            assert len(results) >= 1
            assert results[0]["edge_id"] == f"{prefix}edge001"
        finally:
            await _cleanup_prefix(client, prefix)
            await client.cleanup()

    async def test_search_nodes_returns_results(self):
        """search_nodes() finds nodes by text content in real Neo4j."""
        client = _make_client()
        prefix = f"test_{uuid.uuid4().hex[:8]}_"
        try:
            await client.initialize()

            # Seed a searchable node
            await client.run_query(
                "CREATE (n:Node {id: $nodeId, name: $name, text: $text, "
                "canvas_path: $canvas})",
                nodeId=f"{prefix}search_node",
                name=f"{prefix}graph_theory",
                text="graph theory foundations",
                canvas=f"{prefix}test.canvas",
            )

            graphiti = GraphitiEdgeClient(neo4j_client=client)
            await graphiti.initialize()

            results = await graphiti.search_nodes(
                "graph theory", canvas_path=f"{prefix}test.canvas"
            )

            assert len(results) >= 1
            assert any("graph theory" in r.get("content", "") for r in results)
        finally:
            await _cleanup_prefix(client, prefix)
            await client.cleanup()

    async def test_health_check_real(self):
        """health_check() returns True against a live Neo4j."""
        client = _make_client()
        try:
            await client.initialize()
            graphiti = GraphitiEdgeClient(neo4j_client=client)
            result = await graphiti.health_check()

            assert result is True
        finally:
            await client.cleanup()

    async def test_get_stats_real(self):
        """stats property returns correct shape with real Neo4j backend."""
        client = _make_client()
        try:
            await client.initialize()
            graphiti = GraphitiEdgeClient(neo4j_client=client)
            await graphiti.initialize()

            stats = graphiti.stats

            assert stats["class_name"] == "GraphitiEdgeClient"
            assert stats["is_neo4j_enabled"] is True
            assert stats["is_fallback_mode"] is False
            assert "neo4j_stats" in stats
            assert isinstance(stats["neo4j_stats"], dict)
        finally:
            await client.cleanup()


class TestRealConnectionPool:
    """Connection pool sharing: multiple GraphitiEdgeClient instances reuse one Neo4jClient."""

    async def test_multiple_clients_share_pool(self):
        """Three GraphitiEdgeClient instances share the same Neo4jClient."""
        client = _make_client()
        try:
            await client.initialize()
            g1 = GraphitiEdgeClient(neo4j_client=client)
            g2 = GraphitiEdgeClient(neo4j_client=client)
            g3 = GraphitiEdgeClient(neo4j_client=client)

            assert g1._neo4j is g2._neo4j is g3._neo4j

            assert await g1.health_check() is True
            assert await g2.health_check() is True
            assert await g3.health_check() is True
        finally:
            await client.cleanup()
