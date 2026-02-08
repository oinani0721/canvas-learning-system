# Canvas Learning System - Story 31.A.2 AC-31.A.2.2 Tests
# Story 31.A.2: 学习历史读取修复
# [Source: docs/stories/31.A.2.story.md]
"""
Tests for AC-31.A.2.2: Neo4jClient.get_learning_history() method.

[Source: docs/stories/31.A.2.story.md#AC-31.A.2.2]
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.clients.neo4j_client import Neo4jClient


# =============================================================================
# AC-31.A.2.2: Neo4jClient.get_learning_history() Method
# [Source: docs/stories/31.A.2.story.md#AC-31.A.2.2]
# =============================================================================

class TestAC31A22_Neo4jClientMethod:
    """AC-31.A.2.2: Neo4jClient must have get_learning_history()."""

    def test_method_exists(self):
        """get_learning_history must exist on Neo4jClient."""
        assert hasattr(Neo4jClient, "get_learning_history")
        assert callable(getattr(Neo4jClient, "get_learning_history"))

    def test_method_signature_params(self):
        """Method must support required parameters."""
        import inspect
        sig = inspect.signature(Neo4jClient.get_learning_history)
        param_names = list(sig.parameters.keys())

        assert "self" in param_names
        assert "user_id" in param_names
        assert "start_date" in param_names
        assert "end_date" in param_names
        assert "concept" in param_names
        assert "group_id" in param_names
        assert "limit" in param_names

    @pytest.mark.asyncio
    async def test_json_fallback_filters_by_user_id(self):
        """JSON fallback filters results by user_id."""
        client = Neo4jClient(use_json_fallback=True)
        await client.initialize()

        # Inject test data
        client._data["relationships"] = [
            {"user_id": "u1", "concept_name": "A", "timestamp": "2026-02-05T10:00:00",
             "last_score": 90},
            {"user_id": "u2", "concept_name": "B", "timestamp": "2026-02-05T10:00:00",
             "last_score": 80},
        ]

        results = await client.get_learning_history(user_id="u1")

        assert len(results) == 1
        assert results[0]["concept"] == "A"

    @pytest.mark.asyncio
    async def test_json_fallback_filters_by_concept(self):
        """JSON fallback filters by concept (partial match)."""
        client = Neo4jClient(use_json_fallback=True)
        await client.initialize()

        client._data["relationships"] = [
            {"user_id": "u1", "concept_name": "线性代数-矩阵乘法",
             "timestamp": "2026-02-05T10:00:00", "last_score": 90},
            {"user_id": "u1", "concept_name": "概率论-贝叶斯",
             "timestamp": "2026-02-05T10:00:00", "last_score": 80},
        ]

        results = await client.get_learning_history(user_id="u1", concept="矩阵")

        assert len(results) == 1
        assert "矩阵" in results[0]["concept"]

    @pytest.mark.asyncio
    async def test_json_fallback_filters_by_group_id(self):
        """JSON fallback filters by group_id."""
        client = Neo4jClient(use_json_fallback=True)
        await client.initialize()

        client._data["relationships"] = [
            {"user_id": "u1", "concept_name": "A", "group_id": "math-001",
             "timestamp": "2026-02-05T10:00:00", "last_score": 90},
            {"user_id": "u1", "concept_name": "B", "group_id": "physics-001",
             "timestamp": "2026-02-05T10:00:00", "last_score": 80},
        ]

        results = await client.get_learning_history(
            user_id="u1", group_id="math-001"
        )

        assert len(results) == 1
        assert results[0]["concept"] == "A"

    @pytest.mark.asyncio
    async def test_json_fallback_filters_by_date_range(self):
        """JSON fallback filters by start_date and end_date."""
        client = Neo4jClient(use_json_fallback=True)
        await client.initialize()

        client._data["relationships"] = [
            {"user_id": "u1", "concept_name": "Old",
             "timestamp": "2026-01-01T10:00:00", "last_score": 70},
            {"user_id": "u1", "concept_name": "Current",
             "timestamp": "2026-02-05T10:00:00", "last_score": 85},
            {"user_id": "u1", "concept_name": "Future",
             "timestamp": "2026-03-01T10:00:00", "last_score": 95},
        ]

        results = await client.get_learning_history(
            user_id="u1",
            start_date=datetime(2026, 2, 1),
            end_date=datetime(2026, 2, 28)
        )

        assert len(results) == 1
        assert results[0]["concept"] == "Current"

    @pytest.mark.asyncio
    async def test_json_fallback_limits_results(self):
        """JSON fallback respects limit parameter."""
        client = Neo4jClient(use_json_fallback=True)
        await client.initialize()

        client._data["relationships"] = [
            {"user_id": "u1", "concept_name": f"C{i}",
             "timestamp": f"2026-02-05T{10+i}:00:00", "last_score": 80}
            for i in range(10)
        ]

        results = await client.get_learning_history(user_id="u1", limit=3)

        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_json_fallback_sorts_newest_first(self):
        """JSON fallback returns results sorted by timestamp DESC."""
        client = Neo4jClient(use_json_fallback=True)
        await client.initialize()

        client._data["relationships"] = [
            {"user_id": "u1", "concept_name": "Oldest",
             "timestamp": "2026-02-01T10:00:00", "last_score": 70},
            {"user_id": "u1", "concept_name": "Newest",
             "timestamp": "2026-02-05T10:00:00", "last_score": 90},
            {"user_id": "u1", "concept_name": "Middle",
             "timestamp": "2026-02-03T10:00:00", "last_score": 80},
        ]

        results = await client.get_learning_history(user_id="u1")

        assert results[0]["concept"] == "Newest"
        assert results[-1]["concept"] == "Oldest"

    @pytest.mark.asyncio
    async def test_json_fallback_returns_correct_fields(self):
        """JSON fallback returns all expected fields."""
        client = Neo4jClient(use_json_fallback=True)
        await client.initialize()

        client._data["relationships"] = [
            {"user_id": "u1", "concept_name": "Test", "concept_id": "c-1",
             "group_id": "math-001", "agent_type": "scoring",
             "timestamp": "2026-02-05T10:00:00", "last_score": 90,
             "review_count": 3},
        ]

        results = await client.get_learning_history(user_id="u1")

        assert len(results) == 1
        item = results[0]
        assert item["user_id"] == "u1"
        assert item["concept"] == "Test"
        assert item["concept_id"] == "c-1"
        assert item["score"] == 90
        assert item["timestamp"] == "2026-02-05T10:00:00"
        assert item["group_id"] == "math-001"
        assert item["review_count"] == 3

    @pytest.mark.asyncio
    async def test_neo4j_mode_calls_run_query(self):
        """In Neo4j mode, get_learning_history calls run_query with Cypher."""
        client = Neo4jClient(use_json_fallback=False)
        client._initialized = True
        client._driver = MagicMock()

        # Mock run_query to capture the Cypher
        captured_queries = []

        async def mock_run_query(query, **params):
            captured_queries.append(query)
            return []

        client.run_query = mock_run_query

        await client.get_learning_history(user_id="u1")

        assert len(captured_queries) == 1
        query = captured_queries[0]
        assert "MATCH" in query
        assert "User" in query
        assert "LEARNED" in query
        assert "Concept" in query
        assert "ORDER BY" in query
        assert "LIMIT" in query
