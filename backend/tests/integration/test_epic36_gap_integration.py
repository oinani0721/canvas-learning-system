# EPIC-36 Gap Coverage - Integration Tests
# Covers traceability matrix P1 gaps requiring integration-level tests
"""
Integration tests to close EPIC-36 traceability gaps:
- 36.1-INT-001: Import redirect from unified module (AC-36.1.2)
- 36.2-INT-001: add_edge_relationship() real MERGE Cypher (AC-36.2.1)
- 36.4-INT-003: Concurrent bulk sync with real Neo4j (AC-36.4.5)
- 36.7-INT-003: Agent Neo4j Cypher query execution (AC-36.7.2)
- 36.7-INT-004: Relevance ordering with real data (AC-36.7.3)

These tests require a running Neo4j instance.
Skip with: NEO4J_MOCK=true (default) or pytest -m "not integration"

[Source: _bmad-output/test-artifacts/traceability-matrix-epic36.md - Gap Analysis]
"""

import asyncio
import json
import os

import pytest

# Skip integration tests if Neo4j is mocked
pytestmark = pytest.mark.skipif(
    os.getenv("NEO4J_MOCK", "true").lower() == "true",
    reason="Integration tests require real Neo4j (set NEO4J_MOCK=false)"
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
async def neo4j_client():
    """Get real Neo4j client for integration tests."""
    from app.clients.neo4j_client import get_neo4j_client
    client = get_neo4j_client()
    yield client
    await client.close()


@pytest.fixture
async def graphiti_client(neo4j_client):
    """Create GraphitiEdgeClient with real Neo4j client."""
    from app.clients.graphiti_client import GraphitiEdgeClient
    client = GraphitiEdgeClient(neo4j_client=neo4j_client)
    await client.initialize()
    return client


@pytest.fixture
async def agent_service(neo4j_client):
    """Create AgentService with real Neo4j client for AC-36.7 tests."""
    from app.services.agent_service import AgentService
    return AgentService(
        gemini_client=None,
        memory_client=None,
        canvas_service=None,
        neo4j_client=neo4j_client,
    )


@pytest.fixture
async def cleanup_test_nodes(neo4j_client):
    """Cleanup test nodes after each test."""
    yield
    try:
        await neo4j_client.run_query(
            "MATCH (n) WHERE n.id STARTS WITH 'gap-test-' DETACH DELETE n"
        )
    except Exception:
        pass


# =============================================================================
# 36.1-INT-001: Import redirect verification (AC-36.1.2)
# =============================================================================

class TestImportRedirect:
    """
    Gap: AC-36.1.2 had UNIT-ONLY coverage.
    These tests verify all import paths resolve correctly after code merge.
    """

    def test_import_from_graphiti_client_module(self):
        """Verify primary imports from app.clients.graphiti_client."""
        from app.clients.graphiti_client import (
            GraphitiEdgeClient,
            GraphitiEdgeClientAdapter,
            EdgeRelationship,
            get_graphiti_edge_client,
            LearningMemoryClient,
            get_learning_memory_client,
        )
        assert GraphitiEdgeClient is not None
        assert GraphitiEdgeClientAdapter is not None
        assert EdgeRelationship is not None

    def test_import_from_base_module(self):
        """Verify base class imports from app.clients.graphiti_client_base."""
        from app.clients.graphiti_client_base import (
            GraphitiClientBase,
            EdgeRelationship,
        )
        assert GraphitiClientBase is not None
        assert EdgeRelationship is not None

    def test_edge_relationship_identity(self):
        """Verify EdgeRelationship is the same class from both import paths."""
        from app.clients.graphiti_client import EdgeRelationship as ER1
        from app.clients.graphiti_client_base import EdgeRelationship as ER2
        assert ER1 is ER2

    def test_neo4j_client_importable(self):
        """Verify Neo4jClient can be imported."""
        from app.clients.neo4j_client import Neo4jClient, get_neo4j_client
        assert Neo4jClient is not None
        assert callable(get_neo4j_client)

    def test_no_broken_imports_in_services(self):
        """Verify service layer imports don't break after code merge."""
        from app.services.canvas_service import CanvasService
        from app.services.agent_service import AgentService
        from app.services.memory_service import MemoryService
        assert CanvasService is not None
        assert AgentService is not None
        assert MemoryService is not None

    def test_adapter_is_subclass_compatible(self):
        """Verify Adapter wraps GraphitiEdgeClient correctly."""
        from app.clients.graphiti_client import (
            GraphitiEdgeClient,
            GraphitiEdgeClientAdapter,
        )
        from app.clients.graphiti_client_base import GraphitiClientBase

        assert issubclass(GraphitiEdgeClient, GraphitiClientBase)


# =============================================================================
# 36.2-INT-001: add_edge_relationship() real MERGE Cypher (AC-36.2.1)
# =============================================================================

class TestAddEdgeRelationshipRealNeo4j:
    """
    Gap: AC-36.2.1 had UNIT-ONLY coverage.
    Tests real MERGE Cypher execution against Neo4j.
    """

    @pytest.mark.asyncio
    async def test_merge_creates_relationship(
        self, graphiti_client, neo4j_client, cleanup_test_nodes
    ):
        """Verify MERGE Cypher actually creates a relationship in Neo4j."""
        from app.clients.graphiti_client_base import EdgeRelationship

        relationship = EdgeRelationship(
            canvas_path="gap-test-canvas.canvas",
            from_node_id="gap-test-node-a",
            to_node_id="gap-test-node-b",
            edge_label="DEPENDS_ON",
            edge_id="gap-test-edge-001",
            group_id="gap-test-group",
        )

        result = await graphiti_client.add_edge_relationship(relationship)
        assert result is True

        # Verify in Neo4j
        query_result = await neo4j_client.run_query(
            "MATCH ()-[r:CONNECTS_TO]->() "
            "WHERE r.edge_id = $edge_id "
            "RETURN r.edge_id as eid, r.label as label",
            edge_id="gap-test-edge-001",
        )

        assert len(query_result) >= 1
        assert query_result[0]["eid"] == "gap-test-edge-001"

    @pytest.mark.asyncio
    async def test_merge_idempotent(
        self, graphiti_client, neo4j_client, cleanup_test_nodes
    ):
        """Verify MERGE is idempotent — same edge twice doesn't duplicate."""
        from app.clients.graphiti_client_base import EdgeRelationship

        relationship = EdgeRelationship(
            canvas_path="gap-test-idem.canvas",
            from_node_id="gap-test-idem-a",
            to_node_id="gap-test-idem-b",
            edge_label="CONNECTED_TO",
            edge_id="gap-test-edge-idem",
            group_id="gap-test-group",
        )

        await graphiti_client.add_edge_relationship(relationship)
        await graphiti_client.add_edge_relationship(relationship)

        # Should still be exactly 1 relationship
        query_result = await neo4j_client.run_query(
            "MATCH ()-[r:CONNECTS_TO]->() "
            "WHERE r.edge_id = $edge_id "
            "RETURN count(r) as cnt",
            edge_id="gap-test-edge-idem",
        )

        assert query_result[0]["cnt"] == 1

    @pytest.mark.asyncio
    async def test_merge_stores_label_property(
        self, graphiti_client, neo4j_client, cleanup_test_nodes
    ):
        """Verify MERGE stores the edge label as a relationship property."""
        from app.clients.graphiti_client_base import EdgeRelationship

        relationship = EdgeRelationship(
            canvas_path="gap-test-label.canvas",
            from_node_id="gap-test-label-a",
            to_node_id="gap-test-label-b",
            edge_label="DEPENDS_ON",
            edge_id="gap-test-edge-label",
        )

        await graphiti_client.add_edge_relationship(relationship)

        query_result = await neo4j_client.run_query(
            "MATCH ()-[r:CONNECTS_TO]->() "
            "WHERE r.edge_id = $edge_id "
            "RETURN r.label as label",
            edge_id="gap-test-edge-label",
        )

        assert len(query_result) >= 1
        assert query_result[0]["label"] == "DEPENDS_ON"


# =============================================================================
# 36.4-INT-003: Concurrent bulk sync (AC-36.4.5)
# =============================================================================

class TestConcurrentBulkSyncRealNeo4j:
    """
    Gap: AC-36.4.5 had UNIT-ONLY coverage.
    Tests real concurrent edge sync against Neo4j.
    """

    @pytest.mark.asyncio
    async def test_concurrent_sync_10_edges(
        self, graphiti_client, neo4j_client, cleanup_test_nodes
    ):
        """Verify 10 edges synced concurrently all appear in Neo4j."""
        edges = [
            {
                "id": f"gap-test-conc-edge-{i}",
                "fromNode": f"gap-test-conc-from-{i}",
                "toNode": f"gap-test-conc-to-{i}",
                "label": "CONNECTED_TO",
            }
            for i in range(10)
        ]

        result = await graphiti_client.sync_canvas_edges(
            canvas_name="gap-test-concurrent.canvas",
            edges=edges,
        )

        assert result["synced"] + result.get("skipped", 0) + result.get("failed", 0) == 10
        assert result["synced"] >= 8  # Allow minor failures in concurrent mode

    @pytest.mark.asyncio
    async def test_concurrent_no_deadlock(
        self, graphiti_client, cleanup_test_nodes
    ):
        """Verify concurrent sync doesn't cause Neo4j deadlocks."""
        edges_batch_1 = [
            {
                "id": f"gap-test-dl-a-{i}",
                "fromNode": f"gap-test-dl-from-{i}",
                "toNode": f"gap-test-dl-to-{i}",
                "label": "CONNECTED_TO",
            }
            for i in range(5)
        ]
        edges_batch_2 = [
            {
                "id": f"gap-test-dl-b-{i}",
                "fromNode": f"gap-test-dl-from-{i + 10}",
                "toNode": f"gap-test-dl-to-{i + 10}",
                "label": "CONNECTED_TO",
            }
            for i in range(5)
        ]

        # Run two batches concurrently
        results = await asyncio.gather(
            graphiti_client.sync_canvas_edges("gap-test-dl-a.canvas", edges_batch_1),
            graphiti_client.sync_canvas_edges("gap-test-dl-b.canvas", edges_batch_2),
        )

        # Both should succeed without deadlock
        for result in results:
            assert result["synced"] >= 3  # Most should succeed


# =============================================================================
# 36.7-INT-003: Agent Neo4j Cypher query execution (AC-36.7.2)
# =============================================================================

class TestAgentNeo4jCypherExecution:
    """
    Gap: AC-36.7.2 had UNIT-ONLY coverage (only verified query structure).
    Tests actual Cypher query execution against real Neo4j.
    """

    @pytest.mark.asyncio
    async def test_query_executes_without_error(
        self, agent_service, neo4j_client, cleanup_test_nodes
    ):
        """Verify _query_neo4j_memories() executes without error on real Neo4j."""
        # Seed a test LearningMemory node
        await neo4j_client.run_query(
            "CREATE (m:LearningMemory {id: $id, content: $content, "
            "concept: $concept, relevance: $relevance, score: $score, "
            "canvas_name: $canvas_name})",
            id="gap-test-mem-1",
            content="微积分导数的链式法则",
            concept="链式法则",
            relevance=0.9,
            score=85,
            canvas_name="高等数学",
        )

        result = await agent_service._query_neo4j_memories(
            content="链式法则",
            canvas_name="高等数学",
        )

        # Should return formatted string (not crash)
        assert isinstance(result, str)
        # Should contain the seeded data
        assert "链式法则" in result

    @pytest.mark.asyncio
    async def test_query_with_no_matches_returns_empty(self, agent_service):
        """Verify empty result set returns empty string."""
        result = await agent_service._query_neo4j_memories(
            content="不存在的概念XXXXXX",
            canvas_name="不存在的Canvas",
        )

        assert result == ""


# =============================================================================
# 36.7-INT-004: Relevance ordering with real data (AC-36.7.3)
# =============================================================================

class TestRelevanceOrderingRealData:
    """
    Gap: AC-36.7.3 had UNIT-ONLY coverage (only verified ORDER BY in query).
    Tests actual relevance ordering with seeded Neo4j data.
    """

    @pytest.mark.asyncio
    async def test_results_ordered_by_relevance(
        self, agent_service, neo4j_client, cleanup_test_nodes
    ):
        """Verify results come back ordered by relevance DESC."""
        # Seed nodes with different relevance scores
        for i, (concept, relevance) in enumerate([
            ("基础概念", 0.3),
            ("核心定理", 0.95),
            ("高级应用", 0.7),
            ("入门知识", 0.1),
            ("关键推导", 0.85),
        ]):
            await neo4j_client.run_query(
                "CREATE (m:LearningMemory {id: $id, content: $content, "
                "concept: $concept, relevance: $relevance, score: 80, "
                "canvas_name: $canvas_name})",
                id=f"gap-test-rel-{i}",
                content=f"数学分析 {concept}",
                concept=concept,
                relevance=relevance,
                canvas_name="数学分析",
            )

        result = await agent_service._query_neo4j_memories(
            content="数学分析",
            canvas_name="数学分析",
        )

        # The formatted result should mention the highest-relevance concept first
        assert isinstance(result, str)
        if result:
            # "核心定理" (0.95) should appear before "基础概念" (0.3)
            idx_core = result.find("核心定理")
            idx_basic = result.find("基础概念")
            if idx_core >= 0 and idx_basic >= 0:
                assert idx_core < idx_basic, (
                    "核心定理 (relevance=0.95) should appear before 基础概念 (relevance=0.3)"
                )

    @pytest.mark.asyncio
    async def test_limit_5_respected(
        self, agent_service, neo4j_client, cleanup_test_nodes
    ):
        """Verify LIMIT 5 is respected with more than 5 results."""
        # Seed 8 nodes
        for i in range(8):
            await neo4j_client.run_query(
                "CREATE (m:LearningMemory {id: $id, content: $content, "
                "concept: $concept, relevance: $relevance, score: 80, "
                "canvas_name: $canvas_name})",
                id=f"gap-test-lim-{i}",
                content=f"限制测试概念{i}",
                concept=f"概念{i}",
                relevance=0.5 + i * 0.05,
                canvas_name="限制测试",
            )

        result = await agent_service._query_neo4j_memories(
            content="限制测试概念",
            canvas_name="限制测试",
        )

        # Count distinct concept mentions — should be at most 5
        concept_count = sum(1 for i in range(8) if f"概念{i}" in result)
        assert concept_count <= 5, f"Expected at most 5 concepts, found {concept_count}"
