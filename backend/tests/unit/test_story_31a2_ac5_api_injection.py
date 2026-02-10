# Canvas Learning System - Story 31.A.2 AC-31.A.2.5 + Edge Cases Tests
# Story 31.A.2: 学习历史读取修复
# [Source: docs/stories/31.A.2.story.md]
"""
Tests for AC-31.A.2.5: API endpoint dependency injection fix.
Also includes edge case and regression tests.

[Source: docs/stories/31.A.2.story.md#AC-31.A.2.5]
"""

from unittest.mock import AsyncMock

import pytest

from tests.unit.test_story_31a2_helpers import _make_neo4j_mock, _make_service


# =============================================================================
# AC-31.A.2.5: API Endpoint Dependency Injection Fix
# [Source: docs/stories/31.A.2.story.md#AC-31.A.2.5]
# =============================================================================

class TestAC31A25_ApiDependencyInjection:
    """AC-31.A.2.5: GET endpoints must not have `= None` default for MemoryServiceDep."""

    def test_get_learning_history_endpoint_no_default_none(self):
        """GET /episodes endpoint should not have memory_service=None."""
        import inspect
        from app.api.v1.endpoints.memory import get_learning_history

        sig = inspect.signature(get_learning_history)
        param = sig.parameters.get("memory_service")

        assert param is not None, "memory_service parameter must exist"
        # The default should be an Annotated/Depends, NOT None
        assert param.default is not None or param.default is inspect.Parameter.empty, \
            "memory_service must not default to None"

    def test_get_concept_history_endpoint_no_default_none(self):
        """GET /concepts/{id}/history endpoint should not have memory_service=None."""
        import inspect
        from app.api.v1.endpoints.memory import get_concept_history

        sig = inspect.signature(get_concept_history)
        param = sig.parameters.get("memory_service")

        assert param is not None, "memory_service parameter must exist"
        assert param.default is not None or param.default is inspect.Parameter.empty, \
            "memory_service must not default to None"

    def test_get_review_suggestions_endpoint_no_default_none(self):
        """GET /review-suggestions endpoint should not have memory_service=None."""
        import inspect
        from app.api.v1.endpoints.memory import get_review_suggestions

        sig = inspect.signature(get_review_suggestions)
        param = sig.parameters.get("memory_service")

        assert param is not None, "memory_service parameter must exist"
        assert param.default is not None or param.default is inspect.Parameter.empty, \
            "memory_service must not default to None"

    def test_memory_service_dep_uses_annotated_depends(self):
        """MemoryServiceDep must be Annotated[MemoryService, Depends(...)]."""
        from app.api.v1.endpoints.memory import MemoryServiceDep
        import typing

        # MemoryServiceDep should be an Annotated type
        origin = typing.get_origin(MemoryServiceDep)
        assert origin is typing.Annotated, \
            "MemoryServiceDep should be Annotated type"


# =============================================================================
# Edge Cases and Regression Tests
# =============================================================================

class TestEdgeCases:
    """Regression and edge case tests for learning history read."""

    @pytest.mark.asyncio
    async def test_neo4j_returns_none_treated_as_empty(self):
        """If Neo4j client somehow returns None, treat as empty."""
        mock_neo4j = _make_neo4j_mock(
            get_learning_history=AsyncMock(return_value=None)
        )
        service = _make_service(mock_neo4j)
        await service.initialize()

        service._episodes.append({
            "user_id": "u1", "concept": "Fallback",
            "timestamp": "2026-02-05T10:00:00"
        })

        result = await service.get_learning_history(user_id="u1")

        # None should trigger fallback (falsy check)
        assert result["total"] == 1
        assert result["items"][0]["concept"] == "Fallback"

    @pytest.mark.asyncio
    async def test_page_beyond_total_returns_empty(self):
        """Requesting page beyond available data returns empty items."""
        mock_neo4j = _make_neo4j_mock(
            get_learning_history=AsyncMock(return_value=[
                {"concept": "A", "score": 90, "timestamp": "2026-02-05T10:00:00"}
            ])
        )
        service = _make_service(mock_neo4j)
        await service.initialize()

        result = await service.get_learning_history(
            user_id="u1", page=99, page_size=50
        )

        assert result["total"] == 1
        assert len(result["items"]) == 0

    @pytest.mark.asyncio
    async def test_concurrent_neo4j_and_memory_merge(self):
        """[Code Review C2]: Memory episodes are merged with Neo4j results
        for complete score history (enables consecutive_low tracking)."""
        neo4j_data = [
            {"concept": "FromDB", "score": 90, "timestamp": "2026-02-05T10:00:00"}
        ]
        mock_neo4j = _make_neo4j_mock(
            get_learning_history=AsyncMock(return_value=neo4j_data)
        )
        service = _make_service(mock_neo4j)
        await service.initialize()

        # Record event (adds to _episodes AND Neo4j)
        await service.record_learning_event(
            user_id="u1", canvas_path="test.canvas", node_id="n1",
            concept="JustRecorded", agent_type="scoring"
        )

        # get_learning_history merges Neo4j + in-memory episodes (deduped)
        result = await service.get_learning_history(user_id="u1")

        # Both Neo4j and newly recorded in-memory episode present
        assert result["total"] == 2
        concepts = [it["concept"] for it in result["items"]]
        assert "FromDB" in concepts
        assert "JustRecorded" in concepts

    @pytest.mark.asyncio
    async def test_large_dataset_pagination(self):
        """Pagination works correctly with large datasets."""
        data = [
            {"concept": f"C-{i:03d}", "score": 70 + (i % 30),
             "timestamp": f"2026-02-05T{10 + (i % 12):02d}:{i % 60:02d}:00"}
            for i in range(150)
        ]
        mock_neo4j = _make_neo4j_mock(
            get_learning_history=AsyncMock(return_value=data)
        )
        service = _make_service(mock_neo4j)
        await service.initialize()

        result = await service.get_learning_history(
            user_id="u1", page=3, page_size=50
        )

        assert result["total"] == 150
        assert result["page"] == 3
        assert result["page_size"] == 50
        assert len(result["items"]) == 50  # items 100-149
        assert result["pages"] == 3

    @pytest.mark.asyncio
    async def test_unicode_concept_handling(self):
        """Chinese/Unicode concepts work in both Neo4j and memory paths."""
        neo4j_data = [
            {"concept": "线性代数-特征值分解", "score": 88,
             "timestamp": "2026-02-05T10:00:00"}
        ]
        mock_neo4j = _make_neo4j_mock(
            get_learning_history=AsyncMock(return_value=neo4j_data)
        )
        service = _make_service(mock_neo4j)
        await service.initialize()

        result = await service.get_learning_history(user_id="u1")

        assert result["items"][0]["concept"] == "线性代数-特征值分解"
