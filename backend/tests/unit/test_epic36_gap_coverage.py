# EPIC-36 Gap Coverage - Unit Tests
# Covers traceability matrix P1 gaps requiring unit-level tests
"""
Unit tests to close EPIC-36 traceability gaps:
- 36.2-UNIT-004: get_related_memories() return structure and edge cases (AC-36.2.4)
- 36.8-UNIT-001: extract_top_knowledge_points() algorithm in isolation (AC-36.8.2)
- 36.8-UNIT-002: Cross-canvas degradation path (AC-36.8.6)

[Source: _bmad-output/test-artifacts/traceability-matrix-epic36.md - Gap Analysis]
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.clients.graphiti_client import GraphitiEdgeClient
from app.clients.graphiti_client_base import EdgeRelationship
from app.clients.neo4j_client import Neo4jClient
from app.services.context_enrichment_service import ContextEnrichmentService


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_neo4j_client():
    """Create a mock Neo4jClient for GraphitiEdgeClient tests."""
    mock = MagicMock(spec=Neo4jClient)
    mock.stats = {"mode": "BOLT", "uri": "bolt://localhost:7687"}
    mock.enabled = True
    mock.is_fallback_mode = False
    mock.initialize = AsyncMock(return_value=True)
    mock.create_edge_relationship = AsyncMock(return_value=True)
    mock.run_query = AsyncMock(return_value=[])
    mock.health_check = AsyncMock(return_value=True)
    return mock


@pytest.fixture
def graphiti_client(mock_neo4j_client):
    """Create GraphitiEdgeClient with mock Neo4jClient."""
    return GraphitiEdgeClient(neo4j_client=mock_neo4j_client)


@pytest.fixture
def context_enrichment_service():
    """Create a minimal ContextEnrichmentService for testing."""
    mock_canvas_service = MagicMock()
    mock_canvas_service.canvas_base_path = "/tmp/test"
    return ContextEnrichmentService(canvas_service=mock_canvas_service)


@pytest.fixture
def context_enrichment_with_cross_canvas():
    """Create ContextEnrichmentService with mock cross-canvas service."""
    mock_canvas_service = MagicMock()
    mock_canvas_service.canvas_base_path = "/tmp/test"
    mock_cross_canvas = MagicMock()
    return ContextEnrichmentService(
        canvas_service=mock_canvas_service,
        cross_canvas_service=mock_cross_canvas,
    )


# =============================================================================
# 36.2-UNIT-004: get_related_memories() return structure and edge cases
# AC-36.2.4
# =============================================================================

class TestGetRelatedMemoriesReturnStructure:
    """
    Gap: AC-36.2.4 had INTEGRATION-ONLY coverage.
    These unit tests verify return structure and edge cases in isolation.
    """

    @pytest.mark.asyncio
    async def test_return_structure_keys(self, graphiti_client, mock_neo4j_client):
        """Verify each result dict has node_id, content, relationship, canvas_path."""
        mock_neo4j_client.run_query.return_value = [
            {
                "node_id": "node-abc",
                "content": "微积分基础概念",
                "relationship": "DEPENDS_ON",
                "canvas_path": "数学/线性代数.canvas",
            }
        ]

        results = await graphiti_client.get_related_memories(
            node_id="concept-1",
            canvas_path="数学/线性代数.canvas",
        )

        assert len(results) == 1
        result = results[0]
        assert set(result.keys()) == {"node_id", "content", "relationship", "canvas_path"}
        assert result["node_id"] == "node-abc"
        assert result["content"] == "微积分基础概念"
        assert result["relationship"] == "DEPENDS_ON"
        assert result["canvas_path"] == "数学/线性代数.canvas"

    @pytest.mark.asyncio
    async def test_empty_results_returns_empty_list(self, graphiti_client, mock_neo4j_client):
        """Verify empty Neo4j results returns empty list."""
        mock_neo4j_client.run_query.return_value = []

        results = await graphiti_client.get_related_memories(
            node_id="nonexistent-node",
        )

        assert results == []

    @pytest.mark.asyncio
    async def test_nonexistent_node_returns_empty(self, graphiti_client, mock_neo4j_client):
        """Verify querying a non-existent node returns empty list."""
        mock_neo4j_client.run_query.return_value = []

        results = await graphiti_client.get_related_memories(
            node_id="does-not-exist-99999",
            canvas_path="不存在.canvas",
        )

        assert results == []
        mock_neo4j_client.run_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_missing_fields_use_defaults(self, graphiti_client, mock_neo4j_client):
        """Verify missing fields in Neo4j response get default values."""
        mock_neo4j_client.run_query.return_value = [
            {
                # node_id missing, content missing, relationship missing
                "canvas_path": "test.canvas",
            }
        ]

        results = await graphiti_client.get_related_memories(node_id="node-1")

        assert len(results) == 1
        result = results[0]
        assert result["node_id"] == ""
        assert result["content"] == ""
        assert result["relationship"] == "CONNECTED_TO"  # default
        assert result["canvas_path"] == "test.canvas"

    @pytest.mark.asyncio
    async def test_query_exception_returns_empty(self, graphiti_client, mock_neo4j_client):
        """Verify Neo4j query exception is caught and returns empty list."""
        mock_neo4j_client.run_query.side_effect = Exception("Connection lost")

        results = await graphiti_client.get_related_memories(node_id="node-1")

        assert results == []

    @pytest.mark.asyncio
    async def test_limit_parameter_passed(self, graphiti_client, mock_neo4j_client):
        """Verify limit parameter is passed to the Cypher query."""
        mock_neo4j_client.run_query.return_value = []

        await graphiti_client.get_related_memories(node_id="n1", limit=3)

        call_args = mock_neo4j_client.run_query.call_args
        # Verify limit=3 passed as keyword argument
        assert call_args[1].get("limit") == 3 or "3" in str(call_args)

    @pytest.mark.asyncio
    async def test_canvas_path_filter_in_query(self, graphiti_client, mock_neo4j_client):
        """Verify canvas_path parameter triggers path-filtered Cypher query."""
        mock_neo4j_client.run_query.return_value = []

        await graphiti_client.get_related_memories(
            node_id="n1",
            canvas_path="数学/代数.canvas",
        )

        call_args = mock_neo4j_client.run_query.call_args
        query = call_args[0][0]
        # Should contain canvas_path filter
        assert "canvasPath" in str(call_args) or "canvas_path" in query.lower()

    @pytest.mark.asyncio
    async def test_no_canvas_path_uses_unfiltered_query(self, graphiti_client, mock_neo4j_client):
        """Verify no canvas_path uses unfiltered Cypher query."""
        mock_neo4j_client.run_query.return_value = []

        await graphiti_client.get_related_memories(node_id="n1")

        call_args = mock_neo4j_client.run_query.call_args
        # Should NOT contain canvasPath parameter
        assert "canvasPath" not in call_args[1]


# =============================================================================
# 36.8-UNIT-001: extract_top_knowledge_points() algorithm in isolation
# AC-36.8.2
# =============================================================================

class TestExtractTopKnowledgePointsAlgorithm:
    """
    Gap: AC-36.8.2 had INTEGRATION-ONLY coverage.
    These unit tests verify the extraction algorithm logic in isolation.
    """

    def test_returns_top_5_by_default(self, context_enrichment_service):
        """Verify default max_nodes=5 returns at most 5 results."""
        nodes = [
            {"type": "text", "text": f"概念{i}", "id": f"n{i}", "color": "4", "x": 0, "y": i * 100}
            for i in range(10)
        ]

        result = context_enrichment_service.extract_top_knowledge_points(
            lecture_nodes=nodes,
            exercise_content="概念",
        )

        assert len(result) <= 5

    def test_empty_nodes_returns_empty(self, context_enrichment_service):
        """Verify empty input returns empty list."""
        result = context_enrichment_service.extract_top_knowledge_points(
            lecture_nodes=[],
            exercise_content="test",
        )
        assert result == []

    def test_non_text_nodes_filtered_out(self, context_enrichment_service):
        """Verify non-text nodes (group, file, link) are excluded."""
        nodes = [
            {"type": "group", "text": "Group node", "id": "g1", "x": 0, "y": 0},
            {"type": "file", "file": "test.md", "id": "f1", "x": 0, "y": 0},
            {"type": "text", "text": "Real concept", "id": "t1", "color": "4", "x": 0, "y": 0},
        ]

        result = context_enrichment_service.extract_top_knowledge_points(
            lecture_nodes=nodes,
            exercise_content="concept",
        )

        # Only the text node should be returned
        assert len(result) == 1
        assert result[0]["id"] == "t1"

    def test_nodes_without_text_filtered(self, context_enrichment_service):
        """Verify text nodes with empty text are excluded."""
        nodes = [
            {"type": "text", "text": "", "id": "empty", "x": 0, "y": 0},
            {"type": "text", "text": "有内容", "id": "full", "color": "4", "x": 0, "y": 0},
        ]

        result = context_enrichment_service.extract_top_knowledge_points(
            lecture_nodes=nodes,
            exercise_content="内容",
        )

        assert len(result) == 1
        assert result[0]["id"] == "full"

    def test_result_structure_keys(self, context_enrichment_service):
        """Verify each result has required keys: id, text, color, x, y, relevance_score."""
        nodes = [
            {"type": "text", "text": "矩阵乘法", "id": "n1", "color": "4", "x": 100, "y": 200},
        ]

        result = context_enrichment_service.extract_top_knowledge_points(
            lecture_nodes=nodes,
            exercise_content="矩阵",
        )

        assert len(result) == 1
        item = result[0]
        assert "id" in item
        assert "text" in item
        assert "color" in item
        assert "x" in item
        assert "y" in item
        assert "relevance_score" in item
        assert isinstance(item["relevance_score"], float)

    def test_green_nodes_prioritized(self, context_enrichment_service):
        """Verify green (color=4) nodes score higher than red (color=1)."""
        nodes = [
            {"type": "text", "text": "Same content", "id": "red", "color": "1", "x": 0, "y": 0},
            {"type": "text", "text": "Same content", "id": "green", "color": "4", "x": 0, "y": 0},
        ]

        result = context_enrichment_service.extract_top_knowledge_points(
            lecture_nodes=nodes,
            exercise_content="Same content",
        )

        # Green should be first (higher score)
        assert result[0]["id"] == "green"
        assert result[0]["relevance_score"] >= result[1]["relevance_score"]

    def test_content_truncated_to_max_length(self, context_enrichment_service):
        """Verify content is truncated to max_content_length."""
        long_text = "A" * 500
        nodes = [
            {"type": "text", "text": long_text, "id": "n1", "color": "4", "x": 0, "y": 0},
        ]

        result = context_enrichment_service.extract_top_knowledge_points(
            lecture_nodes=nodes,
            exercise_content="A",
            max_content_length=200,
        )

        assert len(result[0]["text"]) == 200

    def test_sorted_by_relevance_descending(self, context_enrichment_service):
        """Verify results are sorted by relevance_score in descending order."""
        nodes = [
            {"type": "text", "text": "Low relevance node", "id": "n1", "color": "1", "x": 0, "y": 900},
            {"type": "text", "text": "矩阵乘法和线性变换", "id": "n2", "color": "4", "x": 0, "y": 0},
            {"type": "text", "text": "中等相关概念", "id": "n3", "color": "6", "x": 0, "y": 300},
        ]

        result = context_enrichment_service.extract_top_knowledge_points(
            lecture_nodes=nodes,
            exercise_content="矩阵乘法",
        )

        scores = [r["relevance_score"] for r in result]
        assert scores == sorted(scores, reverse=True)

    def test_custom_max_nodes(self, context_enrichment_service):
        """Verify custom max_nodes parameter limits output."""
        nodes = [
            {"type": "text", "text": f"Node {i}", "id": f"n{i}", "color": "4", "x": 0, "y": i * 50}
            for i in range(10)
        ]

        result = context_enrichment_service.extract_top_knowledge_points(
            lecture_nodes=nodes,
            exercise_content="Node",
            max_nodes=3,
        )

        assert len(result) <= 3


# =============================================================================
# 36.8-UNIT-002: Cross-canvas degradation path
# AC-36.8.6
# =============================================================================

class TestCrossCanvasDegradationPath:
    """
    Gap: AC-36.8.6 had INTEGRATION-ONLY coverage.
    These unit tests verify the degradation logic when Neo4j is unavailable.
    """

    def test_no_cross_canvas_service_returns_none(self):
        """Verify get_cross_canvas_context returns None when service not injected."""
        mock_canvas = MagicMock()
        mock_canvas.canvas_base_path = "/tmp"
        service = ContextEnrichmentService(
            canvas_service=mock_canvas,
            cross_canvas_service=None,
        )

        result = asyncio.get_event_loop().run_until_complete(
            service.get_cross_canvas_context("习题-线性代数.canvas")
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_cross_canvas_service_exception_caught_by_caller(
        self, context_enrichment_with_cross_canvas
    ):
        """Verify exception in cross-canvas service propagates from get_cross_canvas_context
        but is caught gracefully by enrich_with_adjacent_nodes (AC-36.8.6)."""
        service = context_enrichment_with_cross_canvas
        service._cross_canvas_service.get_lecture_for_exercise = AsyncMock(
            side_effect=Exception("Neo4j connection lost")
        )

        # get_cross_canvas_context does NOT catch this exception (by design)
        with pytest.raises(Exception, match="Neo4j connection lost"):
            await service.get_cross_canvas_context("习题-数学.canvas")

    @pytest.mark.asyncio
    async def test_enrich_catches_cross_canvas_exception(self):
        """Verify enrich_with_adjacent_nodes catches cross-canvas exceptions gracefully."""
        mock_canvas = MagicMock()
        mock_canvas.canvas_base_path = "/tmp/test"
        mock_canvas.read_canvas = AsyncMock(return_value={
            "nodes": [
                {"id": "target", "type": "text", "text": "Target", "x": 0, "y": 0, "width": 200, "height": 100},
            ],
            "edges": [],
        })
        mock_cross = MagicMock()
        mock_cross.get_lecture_for_exercise = AsyncMock(
            side_effect=Exception("Neo4j down")
        )

        service = ContextEnrichmentService(
            canvas_service=mock_canvas,
            cross_canvas_service=mock_cross,
        )

        # Should NOT raise — exception caught at enrich level (line 834-836)
        result = await service.enrich_with_adjacent_nodes(
            canvas_name="习题-数学",
            node_id="target",
        )

        assert result is not None
        assert result.has_cross_canvas_refs is False

    @pytest.mark.asyncio
    async def test_no_association_found_returns_none(
        self, context_enrichment_with_cross_canvas
    ):
        """Verify no association returns None."""
        service = context_enrichment_with_cross_canvas
        service._cross_canvas_service.get_lecture_for_exercise = AsyncMock(
            return_value=None
        )

        result = await service.get_cross_canvas_context("习题-物理.canvas")

        assert result is None

    @pytest.mark.asyncio
    async def test_enrichment_continues_without_cross_canvas(self):
        """Verify enrich_with_adjacent_nodes succeeds even when cross-canvas fails."""
        mock_canvas = MagicMock()
        mock_canvas.canvas_base_path = "/tmp/test"
        mock_canvas.read_canvas = AsyncMock(return_value={
            "nodes": [
                {"id": "target", "type": "text", "text": "Target node", "x": 0, "y": 0, "width": 200, "height": 100},
            ],
            "edges": [],
        })

        service = ContextEnrichmentService(
            canvas_service=mock_canvas,
            cross_canvas_service=None,  # No cross-canvas service
        )

        result = await service.enrich_with_adjacent_nodes(
            canvas_name="test",
            node_id="target",
        )

        # Should succeed with empty cross-canvas context
        assert result is not None
        assert result.cross_canvas_context is None
        assert result.has_cross_canvas_refs is False

    def test_should_inject_returns_false_for_non_exercise(
        self, context_enrichment_with_cross_canvas
    ):
        """Verify non-exercise canvas paths are rejected."""
        service = context_enrichment_with_cross_canvas
        assert service._should_inject_cross_canvas_context("讲座-线性代数.canvas", 0.9) is False

    def test_should_inject_returns_false_for_low_confidence(
        self, context_enrichment_with_cross_canvas
    ):
        """Verify confidence below threshold is rejected."""
        service = context_enrichment_with_cross_canvas
        # exercise pattern but low confidence
        assert service._should_inject_cross_canvas_context("习题-线性代数.canvas", 0.3) is False

    def test_should_inject_returns_true_for_valid(
        self, context_enrichment_with_cross_canvas
    ):
        """Verify exercise canvas with high confidence is accepted."""
        service = context_enrichment_with_cross_canvas
        assert service._should_inject_cross_canvas_context("习题-线性代数.canvas", 0.8) is True
