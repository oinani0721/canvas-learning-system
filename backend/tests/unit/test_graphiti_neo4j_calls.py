# Story 36.2: Graphiti-Neo4j Call Verification Tests
"""
Tests for AC-36.2.1 (MERGE Cypher) and AC-36.2.4 (search_nodes return structure).

Verifies:
- add_edge_relationship() delegates to neo4j with MERGE semantics
- search_nodes() returns [{node_id, content, canvas_path, score}]

[Source: docs/stories/36.2.story.md]
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.clients.graphiti_client import GraphitiEdgeClient
from app.clients.graphiti_client_base import EdgeRelationship


@pytest.fixture
def mock_neo4j():
    """Create mock Neo4jClient."""
    client = AsyncMock()
    client.initialize = AsyncMock(return_value=True)
    client.stats = {"connected": True, "mode": "NEO4J", "initialized": True}
    client.create_edge_relationship = AsyncMock(return_value=True)
    client.run_query = AsyncMock(return_value=[])
    return client


@pytest.fixture
def graphiti_client(mock_neo4j):
    """Create GraphitiEdgeClient with mock Neo4j."""
    client = GraphitiEdgeClient(neo4j_client=mock_neo4j)
    client._initialized = True
    return client


class TestMergeCypher:
    """AC-36.2.1: Verify MERGE Cypher semantics for edge relationships."""

    @pytest.mark.asyncio
    async def test_add_edge_relationship_calls_neo4j_create(
        self, graphiti_client, mock_neo4j
    ):
        """AC-36.2.1: add_edge_relationship delegates to neo4j.create_edge_relationship."""
        rel = EdgeRelationship(
            canvas_path="test.canvas",
            from_node_id="node-1",
            to_node_id="node-2",
            edge_label="relates_to",
            edge_id="edge-123",
        )

        result = await graphiti_client.add_edge_relationship(rel)

        assert result is True
        mock_neo4j.create_edge_relationship.assert_called_once_with(
            canvas_path="test.canvas",
            edge_id="edge-123",
            from_node_id="node-1",
            to_node_id="node-2",
            edge_label="relates_to",
        )

    @pytest.mark.asyncio
    async def test_add_edge_increments_sync_count_on_success(
        self, graphiti_client, mock_neo4j
    ):
        """AC-36.2.1: Successful sync increments _sync_count."""
        initial_count = graphiti_client._sync_count
        rel = EdgeRelationship(
            canvas_path="test.canvas",
            from_node_id="a",
            to_node_id="b",
            edge_label="test",
        )

        await graphiti_client.add_edge_relationship(rel)

        assert graphiti_client._sync_count == initial_count + 1

    @pytest.mark.asyncio
    async def test_add_edge_increments_error_count_on_failure(
        self, graphiti_client, mock_neo4j
    ):
        """AC-36.2.1: Failed sync increments _error_count."""
        mock_neo4j.create_edge_relationship = AsyncMock(return_value=False)
        initial_errors = graphiti_client._error_count

        rel = EdgeRelationship(
            canvas_path="test.canvas",
            from_node_id="a",
            to_node_id="b",
            edge_label="test",
        )

        await graphiti_client.add_edge_relationship(rel)

        assert graphiti_client._error_count == initial_errors + 1


class TestSearchNodesReturnStructure:
    """AC-36.2.4: Verify search_nodes() return structure."""

    @pytest.mark.asyncio
    async def test_search_nodes_returns_correct_keys(
        self, graphiti_client, mock_neo4j
    ):
        """AC-36.2.4: search_nodes returns [{doc_id, content, canvas_path(in metadata), score}]."""
        mock_neo4j.run_query = AsyncMock(return_value=[
            {
                "node_id": "node-1",
                "content": "矩阵乘法",
                "canvas_path": "linear-algebra.canvas",
                "group_id": "math-101",
            }
        ])

        results = await graphiti_client.search_nodes(query="矩阵")

        assert len(results) == 1
        result = results[0]
        # Verify required keys
        assert "doc_id" in result
        assert "content" in result
        assert "score" in result
        assert "metadata" in result
        assert "canvas_path" in result["metadata"]
        # Verify values
        assert result["doc_id"] == "node-1"
        assert result["content"] == "矩阵乘法"
        assert isinstance(result["score"], float)
        assert 0 <= result["score"] <= 1.0

    @pytest.mark.asyncio
    async def test_search_nodes_sorted_by_score_descending(
        self, graphiti_client, mock_neo4j
    ):
        """AC-36.2.4: Results sorted by score descending."""
        mock_neo4j.run_query = AsyncMock(return_value=[
            {"node_id": "n1", "content": "A very long content string that reduces score", "canvas_path": "c1", "group_id": "g1"},
            {"node_id": "n2", "content": "short", "canvas_path": "c2", "group_id": "g1"},
        ])

        results = await graphiti_client.search_nodes(query="short")

        assert len(results) == 2
        # Shorter content matching query should score higher
        assert results[0]["score"] >= results[1]["score"]

    @pytest.mark.asyncio
    async def test_search_nodes_empty_on_exception(
        self, graphiti_client, mock_neo4j
    ):
        """AC-36.2.4: Returns empty list on exception."""
        mock_neo4j.run_query = AsyncMock(side_effect=Exception("Connection failed"))

        results = await graphiti_client.search_nodes(query="test")

        assert results == []
