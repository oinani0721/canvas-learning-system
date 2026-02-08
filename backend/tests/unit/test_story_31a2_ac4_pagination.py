# Canvas Learning System - Story 31.A.2 AC-31.A.2.4 Tests
# Story 31.A.2: 学习历史读取修复
# [Source: docs/stories/31.A.2.story.md]
"""
Tests for AC-31.A.2.4: Pagination and filtering.

[Source: docs/stories/31.A.2.story.md#AC-31.A.2.4]
"""

from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from tests.unit.test_story_31a2_helpers import _make_neo4j_mock, _make_service


# =============================================================================
# AC-31.A.2.4: Pagination and Filtering
# [Source: docs/stories/31.A.2.story.md#AC-31.A.2.4]
# =============================================================================

class TestAC31A24_PaginationAndFiltering:
    """AC-31.A.2.4: page, page_size, concept, subject, dates must work."""

    @pytest.fixture
    def neo4j_with_data(self):
        """Neo4j mock returning 5 items."""
        data = [
            {"concept": f"Concept-{i}", "score": 80 + i,
             "timestamp": f"2026-02-0{5-i}T10:00:00", "user_id": "u1"}
            for i in range(5)
        ]
        return _make_neo4j_mock(
            get_learning_history=AsyncMock(return_value=data)
        )

    # --- Pagination ---

    @pytest.mark.asyncio
    async def test_page_1_returns_first_items(self, neo4j_with_data):
        """page=1 returns first page_size items."""
        service = _make_service(neo4j_with_data)
        await service.initialize()

        result = await service.get_learning_history(
            user_id="u1", page=1, page_size=2
        )

        assert result["page"] == 1
        assert result["page_size"] == 2
        assert len(result["items"]) == 2
        assert result["items"][0]["concept"] == "Concept-0"
        assert result["items"][1]["concept"] == "Concept-1"

    @pytest.mark.asyncio
    async def test_page_2_returns_next_items(self, neo4j_with_data):
        """page=2 returns the next batch of items."""
        service = _make_service(neo4j_with_data)
        await service.initialize()

        result = await service.get_learning_history(
            user_id="u1", page=2, page_size=2
        )

        assert result["page"] == 2
        assert len(result["items"]) == 2
        assert result["items"][0]["concept"] == "Concept-2"
        assert result["items"][1]["concept"] == "Concept-3"

    @pytest.mark.asyncio
    async def test_total_count_reflects_all_items(self, neo4j_with_data):
        """total should reflect total items, not paginated count."""
        service = _make_service(neo4j_with_data)
        await service.initialize()

        result = await service.get_learning_history(
            user_id="u1", page=1, page_size=2
        )

        assert result["total"] == 5
        assert len(result["items"]) == 2

    @pytest.mark.asyncio
    async def test_pages_count_calculated_correctly(self, neo4j_with_data):
        """pages field: ceil(total / page_size)."""
        service = _make_service(neo4j_with_data)
        await service.initialize()

        result = await service.get_learning_history(
            user_id="u1", page=1, page_size=2
        )

        # 5 items / 2 per page = 3 pages
        assert result["pages"] == 3

    @pytest.mark.asyncio
    async def test_last_page_has_remaining_items(self, neo4j_with_data):
        """Last page returns remaining items only."""
        service = _make_service(neo4j_with_data)
        await service.initialize()

        result = await service.get_learning_history(
            user_id="u1", page=3, page_size=2
        )

        # 5 items, page 3 with size 2 → only 1 item
        assert len(result["items"]) == 1
        assert result["items"][0]["concept"] == "Concept-4"

    @pytest.mark.asyncio
    async def test_empty_result_has_zero_pages(self):
        """Empty result should have pages=0."""
        mock_neo4j = _make_neo4j_mock(
            get_learning_history=AsyncMock(return_value=[])
        )
        service = _make_service(mock_neo4j)
        service._episodes = []  # no memory fallback data either
        await service.initialize()

        result = await service.get_learning_history(user_id="nobody")

        assert result["total"] == 0
        assert result["pages"] == 0
        assert result["items"] == []

    # --- Concept Filter ---

    @pytest.mark.asyncio
    async def test_concept_filter_forwarded_to_neo4j(self):
        """concept param must be passed to Neo4j client."""
        mock_neo4j = _make_neo4j_mock()
        service = _make_service(mock_neo4j)
        await service.initialize()

        await service.get_learning_history(user_id="u1", concept="矩阵")

        kwargs = mock_neo4j.get_learning_history.call_args.kwargs
        assert kwargs["concept"] == "矩阵"

    # --- Subject Filter ---

    @pytest.mark.asyncio
    async def test_subject_filter_converts_to_group_id(self):
        """subject='数学' must be converted to group_id via build_group_id."""
        mock_neo4j = _make_neo4j_mock()
        service = _make_service(mock_neo4j)
        await service.initialize()

        await service.get_learning_history(user_id="u1", subject="数学")

        kwargs = mock_neo4j.get_learning_history.call_args.kwargs
        assert kwargs["group_id"] is not None
        assert isinstance(kwargs["group_id"], str)
        assert len(kwargs["group_id"]) > 0

    @pytest.mark.asyncio
    async def test_no_subject_means_no_group_id(self):
        """Without subject, group_id should be None."""
        mock_neo4j = _make_neo4j_mock()
        service = _make_service(mock_neo4j)
        await service.initialize()

        await service.get_learning_history(user_id="u1")

        kwargs = mock_neo4j.get_learning_history.call_args.kwargs
        assert kwargs["group_id"] is None

    # --- Date Filters ---

    @pytest.mark.asyncio
    async def test_start_date_forwarded_to_neo4j(self):
        """start_date must be passed to Neo4j client."""
        mock_neo4j = _make_neo4j_mock()
        service = _make_service(mock_neo4j)
        await service.initialize()

        start = datetime(2026, 1, 15)
        await service.get_learning_history(user_id="u1", start_date=start)

        kwargs = mock_neo4j.get_learning_history.call_args.kwargs
        assert kwargs["start_date"] == start

    @pytest.mark.asyncio
    async def test_end_date_forwarded_to_neo4j(self):
        """end_date must be passed to Neo4j client."""
        mock_neo4j = _make_neo4j_mock()
        service = _make_service(mock_neo4j)
        await service.initialize()

        end = datetime(2026, 2, 28)
        await service.get_learning_history(user_id="u1", end_date=end)

        kwargs = mock_neo4j.get_learning_history.call_args.kwargs
        assert kwargs["end_date"] == end

    # --- Memory Fallback Filtering ---

    @pytest.mark.asyncio
    async def test_memory_fallback_concept_filter(self):
        """In memory fallback, concept filter still works."""
        mock_neo4j = _make_neo4j_mock(
            get_learning_history=AsyncMock(return_value=[])
        )
        service = _make_service(mock_neo4j)
        await service.initialize()

        service._episodes = [
            {"user_id": "u1", "concept": "矩阵乘法", "score": 90,
             "timestamp": "2026-02-05T10:00:00"},
            {"user_id": "u1", "concept": "概率论", "score": 80,
             "timestamp": "2026-02-05T09:00:00"},
        ]

        result = await service.get_learning_history(
            user_id="u1", concept="矩阵"
        )

        assert result["total"] == 1
        assert result["items"][0]["concept"] == "矩阵乘法"

    @pytest.mark.asyncio
    async def test_memory_fallback_subject_filter(self):
        """In memory fallback, subject filter works."""
        mock_neo4j = _make_neo4j_mock(
            get_learning_history=AsyncMock(return_value=[])
        )
        service = _make_service(mock_neo4j)
        await service.initialize()

        service._episodes = [
            {"user_id": "u1", "concept": "矩阵", "subject": "数学",
             "score": 90, "timestamp": "2026-02-05T10:00:00"},
            {"user_id": "u1", "concept": "量子力学", "subject": "物理",
             "score": 80, "timestamp": "2026-02-05T09:00:00"},
        ]

        result = await service.get_learning_history(
            user_id="u1", subject="数学"
        )

        assert result["total"] == 1
        assert result["items"][0]["concept"] == "矩阵"

    @pytest.mark.asyncio
    async def test_memory_fallback_date_filter(self):
        """In memory fallback, date range filters work."""
        mock_neo4j = _make_neo4j_mock(
            get_learning_history=AsyncMock(return_value=[])
        )
        service = _make_service(mock_neo4j)
        await service.initialize()

        service._episodes = [
            {"user_id": "u1", "concept": "Old",
             "timestamp": "2026-01-01T10:00:00"},
            {"user_id": "u1", "concept": "Current",
             "timestamp": "2026-02-05T10:00:00"},
            {"user_id": "u1", "concept": "Future",
             "timestamp": "2026-03-01T10:00:00"},
        ]

        result = await service.get_learning_history(
            user_id="u1",
            start_date=datetime(2026, 2, 1),
            end_date=datetime(2026, 2, 28)
        )

        assert result["total"] == 1
        assert result["items"][0]["concept"] == "Current"

    @pytest.mark.asyncio
    async def test_memory_fallback_sorts_newest_first(self):
        """Memory fallback sorts by timestamp DESC."""
        mock_neo4j = _make_neo4j_mock(
            get_learning_history=AsyncMock(return_value=[])
        )
        service = _make_service(mock_neo4j)
        await service.initialize()

        service._episodes = [
            {"user_id": "u1", "concept": "Oldest",
             "timestamp": "2026-02-01T10:00:00"},
            {"user_id": "u1", "concept": "Newest",
             "timestamp": "2026-02-05T10:00:00"},
            {"user_id": "u1", "concept": "Middle",
             "timestamp": "2026-02-03T10:00:00"},
        ]

        result = await service.get_learning_history(user_id="u1")

        assert result["items"][0]["concept"] == "Newest"
        assert result["items"][-1]["concept"] == "Oldest"

    @pytest.mark.asyncio
    async def test_memory_fallback_filters_by_user_id(self):
        """Memory fallback only returns current user's data."""
        mock_neo4j = _make_neo4j_mock(
            get_learning_history=AsyncMock(return_value=[])
        )
        service = _make_service(mock_neo4j)
        await service.initialize()

        service._episodes = [
            {"user_id": "u1", "concept": "Mine",
             "timestamp": "2026-02-05T10:00:00"},
            {"user_id": "u2", "concept": "NotMine",
             "timestamp": "2026-02-05T10:00:00"},
        ]

        result = await service.get_learning_history(user_id="u1")

        assert result["total"] == 1
        assert result["items"][0]["concept"] == "Mine"
