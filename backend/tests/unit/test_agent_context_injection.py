# Story 36.7: Agent Context Injection - AC Coverage Tests
"""
Tests for AC-36.7.2 (Neo4j query delegation) and AC-36.7.3 (relevance sorting).

Verifies:
- _search_graphiti_relations() delegates to graphiti_service.search_memories()
- Results are limited to top 5 and sorted by relevance

[Source: docs/stories/36.7.story.md]
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.context_enrichment_service import ContextEnrichmentService


@pytest.fixture
def mock_canvas_service():
    """Create mock canvas service."""
    service = MagicMock()
    service.canvas_base_path = "/test/vault"
    return service


@pytest.fixture
def mock_graphiti_service():
    """Create mock LearningMemoryClient (graphiti_service)."""
    service = AsyncMock()
    service.initialize = AsyncMock(return_value=True)
    service.search_memories = AsyncMock(return_value=[])
    return service


@pytest.fixture
def enrichment_service(mock_canvas_service, mock_graphiti_service):
    """Create ContextEnrichmentService with graphiti_service."""
    return ContextEnrichmentService(
        canvas_service=mock_canvas_service,
        graphiti_service=mock_graphiti_service,
    )


class TestGraphitiSearchDelegation:
    """AC-36.7.2: Verify _search_graphiti_relations delegates to graphiti_service."""

    @pytest.mark.asyncio
    async def test_search_calls_graphiti_service(
        self, enrichment_service, mock_graphiti_service
    ):
        """AC-36.7.2: _search_graphiti_relations calls graphiti_service.search_memories()."""
        mock_graphiti_service.search_memories = AsyncMock(return_value=[
            {"concept": "矩阵乘法", "relevance": 0.9, "timestamp": "2026-02-10"},
        ])

        results = await enrichment_service._search_graphiti_relations(
            query="矩阵乘法定义",
            canvas_name="test.canvas",
            node_id="node-1",
        )

        mock_graphiti_service.search_memories.assert_called_once_with(
            query="矩阵乘法定义",
            canvas_name="test.canvas",
            node_id="node-1",
            limit=5,
        )
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_returns_empty_without_graphiti_service(
        self, mock_canvas_service
    ):
        """AC-36.7.2: Returns empty list when graphiti_service is None."""
        service = ContextEnrichmentService(
            canvas_service=mock_canvas_service,
            graphiti_service=None,
        )

        results = await service._search_graphiti_relations(query="test")

        assert results == []


class TestRelevanceSorting:
    """AC-36.7.3: Verify results sorted by relevance, top 5."""

    @pytest.mark.asyncio
    async def test_search_limits_to_top_5(
        self, enrichment_service, mock_graphiti_service
    ):
        """AC-36.7.3: Search passes limit=5 to graphiti_service."""
        mock_graphiti_service.search_memories = AsyncMock(return_value=[])

        await enrichment_service._search_graphiti_relations(query="test query")

        # Verify limit=5 was passed
        call_kwargs = mock_graphiti_service.search_memories.call_args.kwargs
        assert call_kwargs["limit"] == 5

    @pytest.mark.asyncio
    async def test_search_graceful_on_exception(
        self, enrichment_service, mock_graphiti_service
    ):
        """AC-36.7.3: Returns empty list on exception (graceful degradation)."""
        mock_graphiti_service.search_memories = AsyncMock(
            side_effect=Exception("Connection failed")
        )

        results = await enrichment_service._search_graphiti_relations(
            query="test query"
        )

        assert results == []
