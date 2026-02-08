# Canvas Learning System - Story 31.A.2 AC-31.A.2.1 Tests
# Story 31.A.2: 学习历史读取修复
# [Source: docs/stories/31.A.2.story.md]
"""
Tests for AC-31.A.2.1: Neo4j query priority with memory fallback.

[Source: docs/stories/31.A.2.story.md#AC-31.A.2.1]
"""

import logging
from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from tests.unit.test_story_31a2_helpers import _make_neo4j_mock, _make_service


# =============================================================================
# AC-31.A.2.1: Neo4j Query Priority (from Neo4j, fallback to memory)
# [Source: docs/stories/31.A.2.story.md#AC-31.A.2.1]
# =============================================================================

class TestAC31A21_Neo4jQueryPriority:
    """AC-31.A.2.1: get_learning_history() must query Neo4j first."""

    @pytest.mark.asyncio
    async def test_queries_neo4j_not_memory_when_neo4j_has_data(self):
        """When Neo4j returns data, memory should NOT be used."""
        neo4j_data = [
            {"concept": "Neo4j-矩阵", "score": 95, "timestamp": "2026-02-05T10:00:00",
             "user_id": "u1"}
        ]
        mock_neo4j = _make_neo4j_mock(
            get_learning_history=AsyncMock(return_value=neo4j_data)
        )
        service = _make_service(mock_neo4j)
        await service.initialize()

        # Inject memory data that should NOT appear
        service._episodes.append({
            "user_id": "u1", "concept": "Memory-向量",
            "score": 50, "timestamp": "2026-02-05T09:00:00"
        })

        result = await service.get_learning_history(user_id="u1")

        mock_neo4j.get_learning_history.assert_called_once()
        assert result["total"] == 1
        assert result["items"][0]["concept"] == "Neo4j-矩阵"
        # Memory data should NOT be present
        concepts = [i["concept"] for i in result["items"]]
        assert "Memory-向量" not in concepts

    @pytest.mark.asyncio
    async def test_neo4j_called_with_all_parameters(self):
        """Verify all filter params are forwarded to Neo4j."""
        mock_neo4j = _make_neo4j_mock()
        service = _make_service(mock_neo4j)
        await service.initialize()

        start = datetime(2026, 1, 1)
        end = datetime(2026, 2, 1)

        await service.get_learning_history(
            user_id="u1",
            start_date=start,
            end_date=end,
            concept="矩阵",
            subject="数学",
            page=2,
            page_size=10
        )

        call_kwargs = mock_neo4j.get_learning_history.call_args.kwargs
        assert call_kwargs["user_id"] == "u1"
        assert call_kwargs["start_date"] == start
        assert call_kwargs["end_date"] == end
        assert call_kwargs["concept"] == "矩阵"
        assert call_kwargs["group_id"] is not None  # built from subject
        assert call_kwargs["limit"] == 20  # page_size * page = 10 * 2

    @pytest.mark.asyncio
    async def test_fallback_to_memory_on_neo4j_exception(self):
        """When Neo4j raises exception, fall back to in-memory data."""
        mock_neo4j = _make_neo4j_mock(
            get_learning_history=AsyncMock(
                side_effect=Exception("Neo4j connection refused")
            )
        )
        service = _make_service(mock_neo4j)
        await service.initialize()

        service._episodes.append({
            "user_id": "u1", "concept": "内存数据",
            "score": 70, "timestamp": "2026-02-05T08:00:00"
        })

        result = await service.get_learning_history(user_id="u1")

        assert result["total"] == 1
        assert result["items"][0]["concept"] == "内存数据"

    @pytest.mark.asyncio
    async def test_fallback_logs_warning_on_neo4j_failure(self, caplog):
        """AC-31.A.2.1: Fallback must log a warning."""
        mock_neo4j = _make_neo4j_mock(
            get_learning_history=AsyncMock(
                side_effect=ConnectionError("timeout")
            )
        )
        service = _make_service(mock_neo4j)
        await service.initialize()

        with caplog.at_level(logging.WARNING):
            await service.get_learning_history(user_id="u1")

        assert any(
            "Neo4j query failed" in record.message and "falling back" in record.message
            for record in caplog.records
        ), "Should log warning about Neo4j failure and fallback"

    @pytest.mark.asyncio
    async def test_fallback_to_memory_when_neo4j_returns_empty(self):
        """When Neo4j returns empty list, fall back to memory."""
        mock_neo4j = _make_neo4j_mock(
            get_learning_history=AsyncMock(return_value=[])
        )
        service = _make_service(mock_neo4j)
        await service.initialize()

        service._episodes.append({
            "user_id": "u1", "concept": "内存回退",
            "score": 60, "timestamp": "2026-02-05T07:00:00"
        })

        result = await service.get_learning_history(user_id="u1")

        assert result["total"] == 1
        assert result["items"][0]["concept"] == "内存回退"

    @pytest.mark.asyncio
    async def test_no_double_data_when_neo4j_succeeds(self):
        """Neo4j data and memory data should NOT be merged."""
        mock_neo4j = _make_neo4j_mock(
            get_learning_history=AsyncMock(return_value=[
                {"concept": "A", "score": 90, "timestamp": "2026-02-05T10:00:00"}
            ])
        )
        service = _make_service(mock_neo4j)
        await service.initialize()

        service._episodes.append({
            "user_id": "u1", "concept": "B",
            "score": 50, "timestamp": "2026-02-05T09:00:00"
        })

        result = await service.get_learning_history(user_id="u1")

        # Only Neo4j data, no memory contamination
        assert result["total"] == 1
        assert result["items"][0]["concept"] == "A"

    @pytest.mark.asyncio
    async def test_auto_initialize_when_not_initialized(self):
        """Service should auto-initialize if not yet initialized."""
        mock_neo4j = _make_neo4j_mock(
            get_learning_history=AsyncMock(return_value=[])
        )
        service = _make_service(mock_neo4j)
        # NOT calling initialize()

        await service.get_learning_history(user_id="u1")

        mock_neo4j.initialize.assert_called()
