# Story 38.2: Learning History Persistence & Restart Recovery
# Tests for episode recovery from Neo4j on startup and lazy recovery
"""
Test coverage:
- AC-1: Episodes recoverable from Neo4j on restart
- AC-2: self._episodes populated from Neo4j (limit 1000), startup log
- AC-3: Neo4j unavailable → graceful degradation, lazy recovery
"""

import asyncio
import logging
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from app.clients.neo4j_client import Neo4jClient
from app.services.memory_service import MemoryService


# ---- Fixtures ----

@pytest.fixture
def mock_neo4j_client():
    """Create a mock Neo4jClient."""
    client = MagicMock(spec=Neo4jClient)
    client.initialize = AsyncMock(return_value=True)
    client.stats = {"initialized": True, "mode": "NEO4J", "health_status": True}
    client.get_all_recent_episodes = AsyncMock(return_value=[])
    client.get_learning_history = AsyncMock(return_value=[])
    client.cleanup = AsyncMock()
    return client


@pytest.fixture
def mock_learning_memory_client():
    """Create a mock LearningMemoryClient."""
    client = MagicMock()
    client.add_learning_episode = AsyncMock(return_value=None)
    return client


@pytest.fixture
def memory_service(mock_neo4j_client, mock_learning_memory_client):
    """Create MemoryService with mocked dependencies."""
    return MemoryService(
        neo4j_client=mock_neo4j_client,
        learning_memory_client=mock_learning_memory_client,
    )


def _make_episodes(count: int):
    """Helper: generate N fake episode records from Neo4j."""
    return [
        {
            "user_id": f"user-{i}",
            "concept": f"concept-{i}",
            "concept_id": f"cid-{i}",
            "score": 80 + i,
            "timestamp": f"2026-02-0{min(i+1, 9)}T10:00:00",
            "group_id": "math",
            "review_count": i,
        }
        for i in range(count)
    ]


# ---- Neo4jClient.get_all_recent_episodes tests ----

class TestGetAllRecentEpisodes:
    """Task 1: Neo4jClient.get_all_recent_episodes()"""

    @pytest.mark.asyncio
    async def test_json_fallback_returns_relationships(self):
        """Task 1.2: JSON fallback returns relationships as episodes."""
        client = Neo4jClient(use_json_fallback=True)
        client._data = {
            "users": [],
            "concepts": [],
            "relationships": [
                {
                    "user_id": "u1",
                    "concept_name": "algebra",
                    "concept_id": "c1",
                    "last_score": 90,
                    "timestamp": "2026-02-05T10:00:00",
                    "group_id": "math",
                    "review_count": 3,
                },
                {
                    "user_id": "u2",
                    "concept_name": "calculus",
                    "concept_id": "c2",
                    "last_score": 75,
                    "timestamp": "2026-02-06T12:00:00",
                    "group_id": "math",
                    "review_count": 1,
                },
            ],
        }
        client._initialized = True

        results = await client.get_all_recent_episodes(limit=10)

        assert len(results) == 2
        # Sorted by timestamp DESC — c2 first
        assert results[0]["concept"] == "calculus"
        assert results[1]["concept"] == "algebra"
        assert results[0]["user_id"] == "u2"
        assert results[0]["score"] == 75

    @pytest.mark.asyncio
    async def test_json_fallback_respects_limit(self):
        """Task 1.2: JSON fallback respects limit parameter."""
        client = Neo4jClient(use_json_fallback=True)
        client._data = {
            "users": [],
            "concepts": [],
            "relationships": [
                {"user_id": f"u{i}", "concept_name": f"c{i}", "timestamp": f"2026-01-{10+i:02d}T00:00:00"}
                for i in range(20)
            ],
        }
        client._initialized = True

        results = await client.get_all_recent_episodes(limit=5)
        assert len(results) == 5

    @pytest.mark.asyncio
    async def test_json_fallback_empty_data(self):
        """Task 1.2: JSON fallback with no relationships."""
        client = Neo4jClient(use_json_fallback=True)
        client._data = {"users": [], "concepts": [], "relationships": []}
        client._initialized = True

        results = await client.get_all_recent_episodes()
        assert results == []


# ---- MemoryService recovery tests ----

class TestEpisodeRecovery:
    """Task 2: MemoryService episode recovery."""

    @pytest.mark.asyncio
    async def test_recover_episodes_on_init(self, memory_service, mock_neo4j_client):
        """AC-2: Episodes populated from Neo4j on initialize()."""
        episodes = _make_episodes(5)
        mock_neo4j_client.get_all_recent_episodes = AsyncMock(return_value=episodes)

        await memory_service.initialize()

        assert len(memory_service._episodes) == 5
        assert memory_service._episodes_recovered is True
        assert memory_service._episodes[0]["concept"] == "concept-0"
        assert memory_service._episodes[0]["episode_type"] == "recovered"

    @pytest.mark.asyncio
    async def test_recover_episodes_startup_log(self, memory_service, mock_neo4j_client, caplog):
        """AC-2: Startup log shows 'recovered N episodes from Neo4j'."""
        mock_neo4j_client.get_all_recent_episodes = AsyncMock(return_value=_make_episodes(3))

        with caplog.at_level(logging.INFO):
            await memory_service.initialize()

        assert "MemoryService: recovered 3 episodes from Neo4j" in caplog.text

    @pytest.mark.asyncio
    async def test_recover_neo4j_unavailable(self, memory_service, mock_neo4j_client, caplog):
        """AC-3: Neo4j unavailable → empty episodes + WARNING log."""
        mock_neo4j_client.get_all_recent_episodes = AsyncMock(
            side_effect=Exception("Connection refused")
        )

        with caplog.at_level(logging.WARNING):
            await memory_service.initialize()

        assert memory_service._episodes == []
        assert memory_service._episodes_recovered is False
        assert "MemoryService: Neo4j unavailable, starting with empty history" in caplog.text

    @pytest.mark.asyncio
    async def test_new_episodes_during_degradation(self, memory_service, mock_neo4j_client):
        """AC-3: New episodes still appendable during degraded mode."""
        mock_neo4j_client.get_all_recent_episodes = AsyncMock(
            side_effect=Exception("Connection refused")
        )
        mock_neo4j_client.create_learning_relationship = AsyncMock(return_value=True)

        await memory_service.initialize()
        assert memory_service._episodes == []

        # Record a new event — should still work
        episode_id = await memory_service.record_learning_event(
            user_id="test-user",
            canvas_path="test/canvas.canvas",
            node_id="node-1",
            concept="test concept",
            agent_type="test",
        )

        assert len(memory_service._episodes) == 1
        assert memory_service._episodes[0]["concept"] == "test concept"

    @pytest.mark.asyncio
    async def test_recover_zero_episodes(self, memory_service, mock_neo4j_client, caplog):
        """AC-2: Neo4j available but no episodes returns empty list + log."""
        mock_neo4j_client.get_all_recent_episodes = AsyncMock(return_value=[])

        with caplog.at_level(logging.INFO):
            await memory_service.initialize()

        assert memory_service._episodes == []
        assert memory_service._episodes_recovered is True
        assert "MemoryService: recovered 0 episodes from Neo4j" in caplog.text


# ---- Lazy recovery tests ----

class TestLazyRecovery:
    """Task 3: Lazy recovery on first query."""

    @pytest.mark.asyncio
    async def test_lazy_recovery_on_first_query(self, memory_service, mock_neo4j_client):
        """AC-3: Lazy recovery when Neo4j becomes available after failed startup."""
        # Simulate startup failure
        mock_neo4j_client.get_all_recent_episodes = AsyncMock(
            side_effect=Exception("Connection refused")
        )
        await memory_service.initialize()
        assert memory_service._episodes_recovered is False

        # Now Neo4j is available — get_learning_history will trigger lazy recovery
        recovered_episodes = _make_episodes(3)
        mock_neo4j_client.get_all_recent_episodes = AsyncMock(return_value=recovered_episodes)
        # Main query returns empty to trigger fallback path
        mock_neo4j_client.get_learning_history = AsyncMock(return_value=[])

        result = await memory_service.get_learning_history(user_id="user-0")

        # Lazy recovery should have populated _episodes
        assert memory_service._episodes_recovered is True
        assert len(memory_service._episodes) == 3

    @pytest.mark.asyncio
    async def test_no_double_recovery(self, memory_service, mock_neo4j_client):
        """Recovery should not run twice if already recovered."""
        mock_neo4j_client.get_all_recent_episodes = AsyncMock(return_value=_make_episodes(2))
        await memory_service.initialize()

        assert memory_service._episodes_recovered is True
        call_count = mock_neo4j_client.get_all_recent_episodes.call_count
        assert call_count == 1

        # Query — should NOT trigger recovery again
        mock_neo4j_client.get_learning_history = AsyncMock(return_value=[])
        await memory_service.get_learning_history(user_id="user-0")

        # get_all_recent_episodes should NOT be called again
        assert mock_neo4j_client.get_all_recent_episodes.call_count == 1


# ---- Integration-like tests ----

class TestRecoveryIntegration:
    """Task 4: Integration tests for full recovery flow."""

    @pytest.mark.asyncio
    async def test_full_restart_recovery_flow(self, mock_neo4j_client, mock_learning_memory_client):
        """AC-1/AC-2: Full restart recovery — episodes survive across service instances."""
        # Session 1: Record events
        svc1 = MemoryService(
            neo4j_client=mock_neo4j_client,
            learning_memory_client=mock_learning_memory_client,
        )
        mock_neo4j_client.get_all_recent_episodes = AsyncMock(return_value=[])
        mock_neo4j_client.create_learning_relationship = AsyncMock(return_value=True)
        await svc1.initialize()

        await svc1.record_learning_event(
            user_id="u1", canvas_path="math.canvas",
            node_id="n1", concept="algebra", agent_type="test",
        )
        assert len(svc1._episodes) == 1

        # Session 2: New service instance, Neo4j has the data
        svc2 = MemoryService(
            neo4j_client=mock_neo4j_client,
            learning_memory_client=mock_learning_memory_client,
        )
        mock_neo4j_client.get_all_recent_episodes = AsyncMock(return_value=[
            {
                "user_id": "u1",
                "concept": "algebra",
                "concept_id": "cid-1",
                "score": None,
                "timestamp": "2026-02-06T10:00:00",
                "group_id": "math",
                "review_count": 1,
            }
        ])
        await svc2.initialize()

        assert len(svc2._episodes) == 1
        assert svc2._episodes[0]["concept"] == "algebra"
        assert svc2._episodes_recovered is True

    @pytest.mark.asyncio
    async def test_degraded_startup_then_lazy_recovery(
        self, mock_neo4j_client, mock_learning_memory_client
    ):
        """AC-3: Degraded startup → lazy recovery on first query."""
        svc = MemoryService(
            neo4j_client=mock_neo4j_client,
            learning_memory_client=mock_learning_memory_client,
        )

        # Startup: Neo4j down
        mock_neo4j_client.get_all_recent_episodes = AsyncMock(
            side_effect=Exception("Connection refused")
        )
        await svc.initialize()
        assert svc._episodes_recovered is False
        assert svc._episodes == []

        # First query: Neo4j recovered
        mock_neo4j_client.get_all_recent_episodes = AsyncMock(
            return_value=_make_episodes(2)
        )
        mock_neo4j_client.get_learning_history = AsyncMock(return_value=[])
        await svc.get_learning_history(user_id="user-0")

        assert svc._episodes_recovered is True
        assert len(svc._episodes) == 2
