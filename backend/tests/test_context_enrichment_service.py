# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: testing)
"""
Integration tests for Story 25.3: Cross-Canvas Context Enrichment
[Source: docs/stories/25.3.story.md#Testing]
[Source: docs/stories/25.2.story.md#TextbookContextService-Integration]

Tests:
- ContextEnrichmentService with cross-canvas context
- Agent prompts include lecture references
- Timeout fallback behavior
"""
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.services.canvas_service import CanvasService
from app.services.context_enrichment_service import (
    AdjacentNode,
    ContextEnrichmentService,
    EnrichedContext,
)
from app.services.cross_canvas_service import (
    CrossCanvasAssociation,
    CrossCanvasService,
)
from app.services.textbook_context_service import TextbookContextService

# String constant for relationship type (matches cross_canvas_service.py)
EXERCISE_LECTURE = "exercise_lecture"


# ============================================================================
# ContextEnrichmentService with CrossCanvasService Tests
# ============================================================================

class TestContextEnrichmentWithCrossCanvas:
    """Tests for ContextEnrichmentService cross-canvas integration (Story 25.3 AC2, AC3)"""

    @pytest.fixture
    def mock_canvas_service(self) -> MagicMock:
        """Create mock CanvasService."""
        mock = MagicMock(spec=CanvasService)
        # Story 12.D.3: Add canvas_base_path for get_node_content() logging
        mock.canvas_base_path = "/mock/vault/path"
        mock.read_canvas = AsyncMock(return_value={
            "nodes": [
                {
                    "id": "node1",
                    "type": "text",
                    "text": "逆否命题",
                    "color": "1",  # Gray (Obsidian: "1"=gray, "4"=red)
                    "x": 0,
                    "y": 0,
                    "width": 200,
                    "height": 100,
                },
                {
                    "id": "node2",
                    "type": "text",
                    "text": "定义: 如果p则q的逆否命题是如果非q则非p",
                    "color": "4",  # Red (Obsidian: "2"=green, "4"=red)
                    "x": 200,
                    "y": 0,
                    "width": 200,
                    "height": 100,
                },
            ],
            "edges": []
        })
        return mock

    @pytest.fixture
    def mock_textbook_service(self) -> MagicMock:
        """Create mock TextbookContextService."""
        mock = MagicMock(spec=TextbookContextService)
        mock.get_textbook_context = AsyncMock(return_value=None)
        return mock

    @pytest.fixture
    def mock_cross_canvas_service(self) -> MagicMock:
        """Create mock CrossCanvasService with exercise-lecture association."""
        mock = MagicMock(spec=CrossCanvasService)

        # Mock get_lecture_for_exercise to return an association
        mock.get_lecture_for_exercise = AsyncMock(return_value=CrossCanvasAssociation(
            id="test-assoc-id",
            source_canvas_path="exercises/discrete-math-题目.canvas",
            source_canvas_title="离散数学题目",
            target_canvas_path="lectures/discrete-math-lecture.canvas",
            target_canvas_title="离散数学讲座",
            relationship_type=EXERCISE_LECTURE,
            common_concepts=["逆否命题", "命题逻辑"],
            confidence=0.85,
        ))

        return mock

    @pytest.fixture
    def context_enrichment_service(
        self,
        mock_canvas_service: MagicMock,
        mock_textbook_service: MagicMock,
        mock_cross_canvas_service: MagicMock,
    ) -> ContextEnrichmentService:
        """Create ContextEnrichmentService with mocked dependencies."""
        return ContextEnrichmentService(
            canvas_service=mock_canvas_service,
            textbook_service=mock_textbook_service,
            cross_canvas_service=mock_cross_canvas_service,
        )

    @pytest.mark.asyncio
    async def test_enrich_includes_cross_canvas_context(
        self,
        context_enrichment_service: ContextEnrichmentService,
        mock_cross_canvas_service: MagicMock,
        mock_canvas_service: MagicMock,
    ):
        """Test that enrichment includes cross-canvas context (AC2)."""
        # Arrange
        mock_canvas_service.read_canvas.side_effect = [
            # First call: exercise canvas
            {
                "nodes": [{"id": "node1", "type": "text", "text": "问题1", "x": 0, "y": 0}],
                "edges": []
            },
            # Second call: lecture canvas
            {
                "nodes": [
                    {"id": "lec1", "type": "text", "text": "逆否命题定义", "x": 0, "y": 0},
                    {"id": "lec2", "type": "text", "text": "逆否命题示例", "x": 0, "y": 100},
                ],
                "edges": []
            },
        ]

        # Act
        result = await context_enrichment_service.enrich_with_adjacent_nodes(
            canvas_name="exercises/discrete-math-题目",
            node_id="node1",
        )

        # Assert
        assert result is not None
        assert result.cross_canvas_context is not None
        mock_cross_canvas_service.get_lecture_for_exercise.assert_called_once()

    @pytest.mark.asyncio
    async def test_cross_canvas_context_format(
        self,
        context_enrichment_service: ContextEnrichmentService,
        mock_canvas_service: MagicMock,
    ):
        """Test cross-canvas context is formatted correctly (AC3)."""
        # Arrange
        mock_canvas_service.read_canvas.side_effect = [
            # Exercise canvas
            {
                "nodes": [{"id": "node1", "type": "text", "text": "问题1", "x": 0, "y": 0}],
                "edges": []
            },
            # Lecture canvas
            {
                "nodes": [
                    {"id": "lec1", "type": "text", "text": "逆否命题定义: 如果p则q", "x": 0, "y": 0},
                ],
                "edges": []
            },
        ]

        # Act
        result = await context_enrichment_service.enrich_with_adjacent_nodes(
            canvas_name="exercises/discrete-math-题目",
            node_id="node1",
        )

        # Assert
        assert result.cross_canvas_context is not None
        # Should contain the formatted reference (参见讲座 or lecture name)
        assert "参见讲座" in result.cross_canvas_context or "离散数学讲座" in result.cross_canvas_context

    @pytest.mark.asyncio
    async def test_no_cross_canvas_context_when_no_association(
        self,
        mock_canvas_service: MagicMock,
        mock_textbook_service: MagicMock,
    ):
        """Test that no cross-canvas context is added when no association exists."""
        # Arrange
        mock_cross_canvas = MagicMock(spec=CrossCanvasService)
        mock_cross_canvas.get_lecture_for_exercise = AsyncMock(return_value=None)

        service = ContextEnrichmentService(
            canvas_service=mock_canvas_service,
            textbook_service=mock_textbook_service,
            cross_canvas_service=mock_cross_canvas,
        )

        mock_canvas_service.read_canvas.return_value = {
            "nodes": [{"id": "node1", "type": "text", "text": "test", "x": 0, "y": 0}],
            "edges": []
        }

        # Act
        result = await service.enrich_with_adjacent_nodes(
            canvas_name="standalone/canvas",
            node_id="node1",
        )

        # Assert
        assert result.cross_canvas_context is None or result.cross_canvas_context == ""
        assert result.has_cross_canvas_refs is False

    @pytest.mark.asyncio
    async def test_cross_canvas_graceful_fallback_on_error(
        self,
        mock_canvas_service: MagicMock,
        mock_textbook_service: MagicMock,
    ):
        """Test graceful fallback when cross-canvas service fails."""
        # Arrange
        mock_cross_canvas = MagicMock(spec=CrossCanvasService)
        mock_cross_canvas.get_lecture_for_exercise = AsyncMock(
            side_effect=Exception("Service error")
        )

        service = ContextEnrichmentService(
            canvas_service=mock_canvas_service,
            textbook_service=mock_textbook_service,
            cross_canvas_service=mock_cross_canvas,
        )

        mock_canvas_service.read_canvas.return_value = {
            "nodes": [{"id": "node1", "type": "text", "text": "test", "x": 0, "y": 0}],
            "edges": []
        }

        # Act - should not raise exception
        result = await service.enrich_with_adjacent_nodes(
            canvas_name="exercises/test",
            node_id="node1",
        )

        # Assert - should complete without error
        assert result is not None
        assert result.has_cross_canvas_refs is False


# ============================================================================
# Agent Prompt Integration Tests
# ============================================================================

class TestAgentPromptWithCrossCanvas:
    """Tests for agent prompts including lecture references (AC3)"""

    @pytest.fixture
    def enriched_context_with_cross_canvas(self) -> EnrichedContext:
        """Create EnrichedContext with cross-canvas data."""
        return EnrichedContext(
            target_node={"id": "node1", "type": "text", "text": "练习: 证明逆否命题"},
            adjacent_nodes=[],
            enriched_context="[目标节点] 练习: 证明逆否命题",
            textbook_context="教材第3章: 命题逻辑",
            has_textbook_refs=True,
            cross_canvas_context="参见讲座: 离散数学讲座 > 逆否命题定义",
            has_cross_canvas_refs=True,
            lecture_canvas_path="lectures/discrete-math-lecture.canvas",
            lecture_canvas_title="离散数学讲座",
        )

    def test_enriched_context_contains_lecture_reference(
        self,
        enriched_context_with_cross_canvas: EnrichedContext,
    ):
        """Test EnrichedContext contains properly formatted lecture reference."""
        context = enriched_context_with_cross_canvas

        # Assert
        assert context.cross_canvas_context is not None
        assert "参见讲座:" in context.cross_canvas_context
        assert "离散数学讲座" in context.cross_canvas_context

    def test_enriched_context_can_be_used_in_prompt(
        self,
        enriched_context_with_cross_canvas: EnrichedContext,
    ):
        """Test that EnrichedContext can be formatted for agent prompts."""
        context = enriched_context_with_cross_canvas

        # Build a sample prompt like agents would
        prompt_parts = []
        if context.textbook_context:
            prompt_parts.append(f"教材参考: {context.textbook_context}")
        if context.cross_canvas_context:
            prompt_parts.append(f"讲座参考: {context.cross_canvas_context}")

        prompt = "\n".join(prompt_parts)

        # Assert
        assert "教材参考:" in prompt
        assert "讲座参考:" in prompt
        assert "离散数学讲座" in prompt

    def test_enriched_context_has_lecture_metadata(
        self,
        enriched_context_with_cross_canvas: EnrichedContext,
    ):
        """Test that EnrichedContext has lecture canvas metadata."""
        context = enriched_context_with_cross_canvas

        # Assert
        assert context.lecture_canvas_path == "lectures/discrete-math-lecture.canvas"
        assert context.lecture_canvas_title == "离散数学讲座"
        assert context.has_cross_canvas_refs is True


# ============================================================================
# EnrichedContext Dataclass Tests
# ============================================================================

class TestEnrichedContextDataclass:
    """Tests for EnrichedContext dataclass structure."""

    def test_enriched_context_required_fields(self):
        """Test that EnrichedContext can be created with required fields only."""
        # Act
        context = EnrichedContext(
            target_node={"id": "node1", "text": "test"},
            adjacent_nodes=[],
            enriched_context="[目标节点] test",
        )

        # Assert
        assert context.target_node == {"id": "node1", "text": "test"}
        assert context.adjacent_nodes == []
        assert context.enriched_context == "[目标节点] test"

    def test_enriched_context_optional_fields_defaults(self):
        """Test that optional fields have correct defaults."""
        # Act
        context = EnrichedContext(
            target_node={"id": "node1"},
            adjacent_nodes=[],
            enriched_context="",
        )

        # Assert
        assert context.textbook_context is None
        assert context.has_textbook_refs is False
        assert context.cross_canvas_context is None
        assert context.has_cross_canvas_refs is False
        assert context.lecture_canvas_path is None
        assert context.lecture_canvas_title is None

    def test_enriched_context_with_all_fields(self):
        """Test that EnrichedContext works with all fields populated."""
        # Act
        context = EnrichedContext(
            target_node={"id": "node1", "text": "test", "color": "1"},
            adjacent_nodes=[
                AdjacentNode(
                    node={"id": "parent1", "text": "parent node"},
                    relation="parent",
                    edge_label="prerequisite"
                )
            ],
            enriched_context="[目标节点] test\n[parent|prerequisite] parent node",
            textbook_context="教材参考内容",
            has_textbook_refs=True,
            target_content="test",
            x=100,
            y=200,
            width=400,
            height=200,
            incoming_edges=[{"fromNode": "parent1", "toNode": "node1"}],
            outgoing_edges=[],
            edge_labels=["prerequisite"],
            parent_nodes=[{"id": "parent1", "text": "parent node"}],
            child_nodes=[],
            sibling_nodes=[],
            cross_canvas_context="参见讲座: 讲座名 > 节点名",
            has_cross_canvas_refs=True,
            lecture_canvas_path="lectures/lecture.canvas",
            lecture_canvas_title="讲座名",
        )

        # Assert - all fields should be accessible
        assert context.target_node["id"] == "node1"
        assert len(context.adjacent_nodes) == 1
        assert context.adjacent_nodes[0].relation == "parent"
        assert context.textbook_context == "教材参考内容"
        assert context.has_textbook_refs is True
        assert context.x == 100
        assert context.y == 200
        assert len(context.incoming_edges) == 1
        assert context.cross_canvas_context is not None
        assert context.has_cross_canvas_refs is True
        assert context.lecture_canvas_path == "lectures/lecture.canvas"


# ============================================================================
# Story 12.A.3: Graphiti Integration Tests
# [Source: docs/stories/story-12.A.3-node-context-deep-read.md#AC4]
# ============================================================================

class TestContextEnrichmentWithGraphiti:
    """Tests for ContextEnrichmentService Graphiti integration (Story 12.A.3 AC4)"""

    @pytest.fixture
    def mock_canvas_service(self) -> MagicMock:
        """Create mock CanvasService."""
        mock = MagicMock(spec=CanvasService)
        # Story 12.D.3: Add canvas_base_path for get_node_content() logging
        mock.canvas_base_path = "/mock/vault/path"
        mock.read_canvas = AsyncMock(return_value={
            "nodes": [
                {
                    "id": "node1",
                    "type": "text",
                    "text": "逆否命题\n\n定义: 如果 p → q，则逆否命题是 ¬q → ¬p",
                    "color": "6",  # Yellow (Obsidian: "3"=purple, "6"=yellow)
                    "x": 100,
                    "y": 200,
                    "width": 300,
                    "height": 150,
                },
            ],
            "edges": []
        })
        return mock

    @pytest.fixture
    def mock_graphiti_service(self) -> MagicMock:
        """Create mock LearningMemoryClient (graphiti_service)."""
        from app.clients.graphiti_client import LearningMemoryClient

        mock = MagicMock(spec=LearningMemoryClient)
        mock.initialize = AsyncMock(return_value=True)
        mock.search_memories = AsyncMock(return_value=[
            {
                "concept": "逆否命题",
                "relevance": 0.9,
                "timestamp": "2025-12-01T10:00:00",
                "score": 32.5,
                "user_understanding": "如果p则q的逆否命题是如果非q则非p",
            },
            {
                "concept": "命题逻辑",
                "relevance": 0.7,
                "timestamp": "2025-11-28T14:30:00",
                "score": 28.0,
                "user_understanding": "命题是可以判断真假的陈述句",
            },
        ])
        return mock

    @pytest.fixture
    def context_enrichment_service_with_graphiti(
        self,
        mock_canvas_service: MagicMock,
        mock_graphiti_service: MagicMock,
    ) -> ContextEnrichmentService:
        """Create ContextEnrichmentService with Graphiti service."""
        return ContextEnrichmentService(
            canvas_service=mock_canvas_service,
            graphiti_service=mock_graphiti_service,
        )

    @pytest.mark.asyncio
    async def test_enrich_includes_graphiti_relations(
        self,
        context_enrichment_service_with_graphiti: ContextEnrichmentService,
        mock_graphiti_service: MagicMock,
    ):
        """Test that enrichment includes Graphiti relations (AC4)."""
        # Act
        result = await context_enrichment_service_with_graphiti.enrich_with_adjacent_nodes(
            canvas_name="离散数学",
            node_id="node1",
            include_graphiti=True,
        )

        # Assert
        assert result is not None
        assert result.graphiti_relations is not None
        assert len(result.graphiti_relations) == 2
        assert result.has_graphiti_refs is True
        mock_graphiti_service.search_memories.assert_called_once()

    @pytest.mark.asyncio
    async def test_graphiti_context_format(
        self,
        context_enrichment_service_with_graphiti: ContextEnrichmentService,
    ):
        """Test Graphiti context is formatted correctly (AC4)."""
        # Act
        result = await context_enrichment_service_with_graphiti.enrich_with_adjacent_nodes(
            canvas_name="离散数学",
            node_id="node1",
            include_graphiti=True,
        )

        # Assert - enriched_context should include Graphiti section
        assert "历史学习记忆" in result.enriched_context or "Graphiti Relations" in result.enriched_context
        assert "逆否命题" in result.enriched_context

    @pytest.mark.asyncio
    async def test_include_graphiti_false_skips_search(
        self,
        mock_canvas_service: MagicMock,
        mock_graphiti_service: MagicMock,
    ):
        """Test that include_graphiti=False skips Graphiti search."""
        # Arrange
        service = ContextEnrichmentService(
            canvas_service=mock_canvas_service,
            graphiti_service=mock_graphiti_service,
        )

        # Act
        result = await service.enrich_with_adjacent_nodes(
            canvas_name="离散数学",
            node_id="node1",
            include_graphiti=False,  # Explicitly disable
        )

        # Assert
        assert result.graphiti_relations == []
        assert result.has_graphiti_refs is False
        mock_graphiti_service.search_memories.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_graphiti_relations_when_service_unavailable(
        self,
        mock_canvas_service: MagicMock,
    ):
        """Test that no Graphiti relations are added when service is not available."""
        # Arrange - no graphiti_service provided
        service = ContextEnrichmentService(
            canvas_service=mock_canvas_service,
            graphiti_service=None,
        )

        # Act
        result = await service.enrich_with_adjacent_nodes(
            canvas_name="离散数学",
            node_id="node1",
            include_graphiti=True,
        )

        # Assert
        assert result.graphiti_relations == []
        assert result.has_graphiti_refs is False

    @pytest.mark.asyncio
    async def test_graphiti_graceful_fallback_on_error(
        self,
        mock_canvas_service: MagicMock,
    ):
        """Test graceful fallback when Graphiti service fails."""
        # Arrange
        from app.clients.graphiti_client import LearningMemoryClient

        mock_graphiti = MagicMock(spec=LearningMemoryClient)
        mock_graphiti.initialize = AsyncMock(return_value=True)
        mock_graphiti.search_memories = AsyncMock(
            side_effect=Exception("Graphiti connection error")
        )

        service = ContextEnrichmentService(
            canvas_service=mock_canvas_service,
            graphiti_service=mock_graphiti,
        )

        # Act - should not raise exception
        result = await service.enrich_with_adjacent_nodes(
            canvas_name="离散数学",
            node_id="node1",
            include_graphiti=True,
        )

        # Assert - should complete without error, graceful degradation
        assert result is not None
        assert result.graphiti_relations == []
        assert result.has_graphiti_refs is False

    @pytest.mark.asyncio
    async def test_graphiti_empty_results(
        self,
        mock_canvas_service: MagicMock,
    ):
        """Test handling of empty Graphiti search results."""
        # Arrange
        from app.clients.graphiti_client import LearningMemoryClient

        mock_graphiti = MagicMock(spec=LearningMemoryClient)
        mock_graphiti.initialize = AsyncMock(return_value=True)
        mock_graphiti.search_memories = AsyncMock(return_value=[])  # Empty results

        service = ContextEnrichmentService(
            canvas_service=mock_canvas_service,
            graphiti_service=mock_graphiti,
        )

        # Act
        result = await service.enrich_with_adjacent_nodes(
            canvas_name="离散数学",
            node_id="node1",
            include_graphiti=True,
        )

        # Assert
        assert result.graphiti_relations == []
        assert result.has_graphiti_refs is False


class TestEnrichedContextWithGraphiti:
    """Tests for EnrichedContext with Graphiti fields."""

    def test_enriched_context_graphiti_fields_defaults(self):
        """Test that Graphiti fields have correct defaults."""
        # Act
        context = EnrichedContext(
            target_node={"id": "node1"},
            adjacent_nodes=[],
            enriched_context="",
        )

        # Assert
        assert context.graphiti_relations is None
        assert context.has_graphiti_refs is False

    def test_enriched_context_with_graphiti_data(self):
        """Test EnrichedContext with Graphiti data populated."""
        # Act
        context = EnrichedContext(
            target_node={"id": "node1", "text": "逆否命题"},
            adjacent_nodes=[],
            enriched_context="[目标节点] 逆否命题",
            graphiti_relations=[
                {"concept": "逆否命题", "relevance": 0.9, "score": 32.5},
                {"concept": "命题逻辑", "relevance": 0.7, "score": 28.0},
            ],
            has_graphiti_refs=True,
        )

        # Assert
        assert context.graphiti_relations is not None
        assert len(context.graphiti_relations) == 2
        assert context.graphiti_relations[0]["concept"] == "逆否命题"
        assert context.has_graphiti_refs is True


class TestFormatGraphitiContext:
    """Tests for _format_graphiti_context method."""

    @pytest.fixture
    def mock_canvas_service(self) -> MagicMock:
        """Create mock CanvasService."""
        mock = MagicMock(spec=CanvasService)
        return mock

    @pytest.fixture
    def service(self, mock_canvas_service: MagicMock) -> ContextEnrichmentService:
        """Create ContextEnrichmentService instance."""
        return ContextEnrichmentService(canvas_service=mock_canvas_service)

    def test_format_empty_results(self, service: ContextEnrichmentService):
        """Test formatting empty Graphiti results."""
        # Act
        result = service._format_graphiti_context([])

        # Assert
        assert result == ""

    def test_format_with_memories(self, service: ContextEnrichmentService):
        """Test formatting Graphiti memories."""
        # Arrange
        memories = [
            {
                "concept": "逆否命题",
                "relevance": 0.9,
                "timestamp": "2025-12-01T10:00:00",
                "score": 32.5,
                "user_understanding": "如果p则q的逆否命题是如果非q则非p",
            },
        ]

        # Act
        result = service._format_graphiti_context(memories)

        # Assert
        assert "历史学习记忆" in result
        assert "逆否命题" in result
        assert "90%" in result  # relevance formatted as percentage
        assert "32.5" in result  # score
        assert "2025-12-01" in result  # timestamp date part

    def test_format_without_understanding(self, service: ContextEnrichmentService):
        """Test formatting memory without user understanding."""
        # Arrange
        memories = [
            {
                "concept": "测试概念",
                "relevance": 0.5,
            },
        ]

        # Act
        result = service._format_graphiti_context(memories)

        # Assert
        assert "测试概念" in result
        assert "历史理解" not in result  # No understanding section
