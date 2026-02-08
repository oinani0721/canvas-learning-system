# Canvas Learning System - Strict Tests for Story 31.A.2
# Story 31.A.2: 学习历史读取修复
# [Source: docs/stories/31.A.2.story.md]
"""
Strict unit tests for Story 31.A.2: Learning history read fix.

Tests all 5 Acceptance Criteria:
- AC-31.A.2.1: Neo4j query priority with memory fallback
- AC-31.A.2.2: Neo4jClient.get_learning_history() method
- AC-31.A.2.3: Cross-session data persistence
- AC-31.A.2.4: Pagination and filtering
- AC-31.A.2.5: API endpoint dependency injection fix

[Source: docs/stories/31.A.2.story.md]
"""

import logging
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.clients.neo4j_client import Neo4jClient
from app.services.memory_service import MemoryService


# =============================================================================
# Shared Fixtures
# =============================================================================

@pytest.fixture
def mock_graphiti_memory():
    """Mock LearningMemoryClient to prevent side effects."""
    memory = MagicMock()
    memory.add_learning_episode = AsyncMock()
    return memory


def _make_service(neo4j_client, graphiti_memory=None):
    """Helper to create MemoryService with mocked dependencies."""
    service = MemoryService(neo4j_client=neo4j_client)
    if graphiti_memory is None:
        graphiti_memory = MagicMock()
        graphiti_memory.add_learning_episode = AsyncMock()
    service._learning_memory = graphiti_memory
    return service


def _make_neo4j_mock(**overrides) -> MagicMock:
    """Helper to create a standard Neo4jClient mock."""
    client = MagicMock(spec=Neo4jClient)
    client._initialized = True
    client._use_json_fallback = False
    client.initialize = AsyncMock()
    client.cleanup = AsyncMock()
    client.close = AsyncMock()
    client.get_learning_history = AsyncMock(return_value=[])
    client.create_learning_relationship = AsyncMock(return_value=True)
    client.stats = {"initialized": True, "mode": "NEO4J", "health_status": True}
    for key, val in overrides.items():
        setattr(client, key, val)
    return client


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


# =============================================================================
# AC-31.A.2.3: Cross-Session Data Persistence
# [Source: docs/stories/31.A.2.story.md#AC-31.A.2.3]
# =============================================================================

class TestAC31A23_CrossSessionPersistence:
    """AC-31.A.2.3: Data must persist across service restarts."""

    @pytest.fixture
    def persistent_neo4j(self):
        """Neo4j mock with shared persistent storage."""
        storage: List[Dict[str, Any]] = []

        mock = _make_neo4j_mock()

        async def mock_create_rel(user_id, concept, score=None, group_id=None):
            storage.append({
                "user_id": user_id,
                "concept": concept,
                "score": score,
                "group_id": group_id,
                "timestamp": datetime.now().isoformat(),
                "review_count": 0,
            })
            return True

        async def mock_get_history(user_id, start_date=None, end_date=None,
                                   concept=None, group_id=None, limit=100):
            return [
                item for item in storage
                if item.get("user_id") == user_id
            ][:limit]

        mock.create_learning_relationship = AsyncMock(side_effect=mock_create_rel)
        mock.get_learning_history = AsyncMock(side_effect=mock_get_history)
        mock._storage = storage
        return mock

    @pytest.mark.asyncio
    async def test_session1_write_session2_read(self, persistent_neo4j):
        """Data written in session 1 is readable in session 2."""
        # Session 1: Write
        svc1 = _make_service(persistent_neo4j)
        await svc1.initialize()
        await svc1.record_learning_event(
            user_id="u1", canvas_path="test/a.canvas", node_id="n1",
            concept="线性代数", agent_type="scoring", score=85
        )
        await svc1.cleanup()

        # Session 2: Read (fresh instance, empty _episodes)
        svc2 = _make_service(persistent_neo4j)
        await svc2.initialize()
        assert len(svc2._episodes) == 0, "Memory should be empty on new instance"

        result = await svc2.get_learning_history(user_id="u1")

        assert result["total"] >= 1
        found = any(i["concept"] == "线性代数" for i in result["items"])
        assert found, "Session 1 data should be accessible in session 2"

    @pytest.mark.asyncio
    async def test_data_fields_complete(self, persistent_neo4j):
        """All critical fields survive cross-session read."""
        svc1 = _make_service(persistent_neo4j)
        await svc1.initialize()
        await svc1.record_learning_event(
            user_id="u1", canvas_path="test/b.canvas", node_id="n2",
            concept="概率论", agent_type="oral-explanation",
            score=92, subject="数学"
        )
        await svc1.cleanup()

        svc2 = _make_service(persistent_neo4j)
        await svc2.initialize()
        result = await svc2.get_learning_history(user_id="u1")

        item = next(
            (i for i in result["items"] if i["concept"] == "概率论"), None
        )
        assert item is not None
        assert item["score"] == 92
        assert "timestamp" in item

    @pytest.mark.asyncio
    async def test_multiple_events_persist(self, persistent_neo4j):
        """Multiple events from session 1 all persist to session 2."""
        svc1 = _make_service(persistent_neo4j)
        await svc1.initialize()

        concepts = ["微积分", "线性代数", "离散数学"]
        for c in concepts:
            await svc1.record_learning_event(
                user_id="u1", canvas_path="test/c.canvas", node_id="n3",
                concept=c, agent_type="scoring", score=80
            )
        await svc1.cleanup()

        svc2 = _make_service(persistent_neo4j)
        await svc2.initialize()
        result = await svc2.get_learning_history(user_id="u1")

        found_concepts = {i["concept"] for i in result["items"]}
        for c in concepts:
            assert c in found_concepts, f"Missing concept: {c}"


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
    async def test_concurrent_neo4j_and_memory_isolation(self):
        """Memory written during current session doesn't contaminate Neo4j results."""
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

        # get_learning_history should use Neo4j data only (not merge with _episodes)
        result = await service.get_learning_history(user_id="u1")

        # Should only have Neo4j data since neo4j returned non-empty
        assert result["total"] == 1
        assert result["items"][0]["concept"] == "FromDB"

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
