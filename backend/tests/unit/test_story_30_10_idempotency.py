# Canvas Learning System - Story 30.10 Tests
# 学习事件写入幂等性修复
"""
Story 30.10 - Idempotency Fix Tests

Tests for deterministic episode IDs, dedup in _episodes list,
dedup in Graphiti JSON writes, and batch idempotency.

[Source: docs/stories/30.10.idempotency-fix.story.md]
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ============================================================================
# Task 1: Deterministic Episode ID Generation
# ============================================================================

class TestDeterministicEpisodeId:
    """AC-30.10.1: Deterministic episode ID from content hash."""

    def test_same_input_same_id(self):
        """Same (user_id, canvas_path, node_id, concept) → same episode_id."""
        from app.services.memory_service import _generate_deterministic_episode_id

        id1 = _generate_deterministic_episode_id("user1", "math/algebra.canvas", "node-1", "二次方程")
        id2 = _generate_deterministic_episode_id("user1", "math/algebra.canvas", "node-1", "二次方程")
        assert id1 == id2

    def test_different_input_different_id(self):
        """Different inputs → different episode_ids."""
        from app.services.memory_service import _generate_deterministic_episode_id

        id1 = _generate_deterministic_episode_id("user1", "math/algebra.canvas", "node-1", "二次方程")
        id2 = _generate_deterministic_episode_id("user1", "math/algebra.canvas", "node-2", "二次方程")
        assert id1 != id2

    def test_different_user_different_id(self):
        """Different user_id → different episode_ids."""
        from app.services.memory_service import _generate_deterministic_episode_id

        id1 = _generate_deterministic_episode_id("user1", "math.canvas", "node-1", "概念A")
        id2 = _generate_deterministic_episode_id("user2", "math.canvas", "node-1", "概念A")
        assert id1 != id2

    def test_id_format(self):
        """Episode ID format is episode-{hash16}."""
        from app.services.memory_service import _generate_deterministic_episode_id

        eid = _generate_deterministic_episode_id("u", "c", "n", "concept")
        assert eid.startswith("episode-")
        # 16 hex chars after "episode-"
        assert len(eid) == len("episode-") + 16

    def test_empty_inputs_no_crash(self):
        """Empty strings don't crash, still produce deterministic output."""
        from app.services.memory_service import _generate_deterministic_episode_id

        id1 = _generate_deterministic_episode_id("", "", "", "")
        id2 = _generate_deterministic_episode_id("", "", "", "")
        assert id1 == id2
        assert id1.startswith("episode-")


# ============================================================================
# Task 2: Batch Deterministic Episode ID
# ============================================================================

class TestBatchDeterministicEpisodeId:
    """AC-30.10.4: Deterministic batch episode ID from event content."""

    def test_same_event_same_id(self):
        """Same event content → same batch episode_id."""
        from app.services.memory_service import _generate_batch_episode_id

        id1 = _generate_batch_episode_id("math.canvas", "node-1", "color_change", "2026-02-09T10:00:00")
        id2 = _generate_batch_episode_id("math.canvas", "node-1", "color_change", "2026-02-09T10:00:00")
        assert id1 == id2

    def test_different_event_different_id(self):
        """Different event content → different batch episode_ids."""
        from app.services.memory_service import _generate_batch_episode_id

        id1 = _generate_batch_episode_id("math.canvas", "node-1", "color_change", "2026-02-09T10:00:00")
        id2 = _generate_batch_episode_id("math.canvas", "node-1", "color_change", "2026-02-09T10:00:01")
        assert id1 != id2

    def test_batch_id_format(self):
        """Batch episode ID format is batch-{hash16}."""
        from app.services.memory_service import _generate_batch_episode_id

        bid = _generate_batch_episode_id("c", "n", "t", "ts")
        assert bid.startswith("batch-")
        assert len(bid) == len("batch-") + 16


# ============================================================================
# Task 3 & 4: _episodes Dedup in record_learning_event
# ============================================================================

class TestEpisodesDedup:
    """AC-30.10.3: _episodes list dedup on record_learning_event."""

    @pytest.fixture
    def mock_neo4j(self):
        neo4j = MagicMock()
        neo4j.initialize = AsyncMock()
        neo4j.stats = {"initialized": True, "connected": True}
        neo4j.execute_query = AsyncMock(return_value=[])
        neo4j.create_learning_relationship = AsyncMock()
        return neo4j

    @pytest.fixture
    def mock_learning_memory(self):
        client = MagicMock()
        client._initialized = False
        client.initialize = AsyncMock(return_value=True)
        client.search_memories = AsyncMock(return_value=[])
        client.add_learning_episode = AsyncMock(return_value=True)
        return client

    @pytest.fixture
    async def memory_service(self, mock_neo4j, mock_learning_memory):
        from app.services.memory_service import MemoryService
        service = MemoryService(
            neo4j_client=mock_neo4j,
            learning_memory_client=mock_learning_memory,
        )
        await service.initialize()
        return service

    @pytest.mark.asyncio
    async def test_duplicate_event_single_episode(self, memory_service):
        """Calling record_learning_event twice with same params → only 1 episode in _episodes."""
        with patch("app.services.memory_service.settings") as mock_settings:
            mock_settings.ENABLE_GRAPHITI_JSON_DUAL_WRITE = False

            await memory_service.record_learning_event(
                user_id="user1", canvas_path="math.canvas",
                node_id="node-1", concept="二次方程", agent_type="scoring-agent"
            )
            await memory_service.record_learning_event(
                user_id="user1", canvas_path="math.canvas",
                node_id="node-1", concept="二次方程", agent_type="scoring-agent"
            )

            # Should only have 1 episode (dedup by deterministic ID)
            matching = [
                ep for ep in memory_service._episodes
                if ep.get("concept") == "二次方程" and ep.get("node_id") == "node-1"
            ]
            assert len(matching) == 1

    @pytest.mark.asyncio
    async def test_different_events_both_stored(self, memory_service):
        """Different events → both stored in _episodes."""
        with patch("app.services.memory_service.settings") as mock_settings:
            mock_settings.ENABLE_GRAPHITI_JSON_DUAL_WRITE = False

            await memory_service.record_learning_event(
                user_id="user1", canvas_path="math.canvas",
                node_id="node-1", concept="二次方程", agent_type="scoring-agent"
            )
            await memory_service.record_learning_event(
                user_id="user1", canvas_path="math.canvas",
                node_id="node-2", concept="一次方程", agent_type="scoring-agent"
            )

            assert len(memory_service._episodes) == 2

    @pytest.mark.asyncio
    async def test_skip_existing_episode_on_dup(self, memory_service):
        """Duplicate call skips (does not overwrite) existing episode (C4 fix: skip-if-exists)."""
        with patch("app.services.memory_service.settings") as mock_settings:
            mock_settings.ENABLE_GRAPHITI_JSON_DUAL_WRITE = False

            await memory_service.record_learning_event(
                user_id="user1", canvas_path="math.canvas",
                node_id="node-1", concept="二次方程", agent_type="scoring-agent",
                score=60
            )
            await memory_service.record_learning_event(
                user_id="user1", canvas_path="math.canvas",
                node_id="node-1", concept="二次方程", agent_type="scoring-agent",
                score=80
            )

            matching = [
                ep for ep in memory_service._episodes
                if ep.get("concept") == "二次方程"
            ]
            assert len(matching) == 1
            assert matching[0]["score"] == 60  # C4 fix: skip-if-exists keeps original


# ============================================================================
# Task 4: Batch _episodes Dedup
# ============================================================================

class TestBatchEpisodesDedup:
    """AC-30.10.4: Batch episodes dedup."""

    @pytest.fixture
    def mock_neo4j(self):
        neo4j = MagicMock()
        neo4j.initialize = AsyncMock()
        neo4j.stats = {"initialized": False, "connected": False}
        return neo4j

    @pytest.fixture
    def mock_learning_memory(self):
        client = MagicMock()
        client._initialized = False
        client.initialize = AsyncMock(return_value=True)
        return client

    @pytest.fixture
    async def memory_service(self, mock_neo4j, mock_learning_memory):
        from app.services.memory_service import MemoryService
        service = MemoryService(
            neo4j_client=mock_neo4j,
            learning_memory_client=mock_learning_memory,
        )
        await service.initialize()
        return service

    def _make_event(self, node_id="node-1", event_type="color_change", timestamp="2026-02-09T10:00:00"):
        return {
            "event_type": event_type,
            "timestamp": timestamp,
            "canvas_path": "math.canvas",
            "node_id": node_id,
            "metadata": {"concept": "test"}
        }

    @pytest.mark.asyncio
    async def test_batch_duplicate_submission_dedup(self, memory_service):
        """Same batch submitted twice → no duplicate episodes."""
        events = [self._make_event(node_id="n1"), self._make_event(node_id="n2")]

        await memory_service.record_batch_learning_events(events)
        count_after_first = len(memory_service._episodes)

        await memory_service.record_batch_learning_events(events)
        count_after_second = len(memory_service._episodes)

        assert count_after_first == count_after_second == 2

    @pytest.mark.asyncio
    async def test_batch_deterministic_ids(self, memory_service):
        """Batch episode IDs are deterministic based on content."""
        events = [self._make_event()]

        await memory_service.record_batch_learning_events(events)
        id1 = memory_service._episodes[-1]["episode_id"]

        # Clear and re-run
        memory_service._episodes.clear()
        await memory_service.record_batch_learning_events(events)
        id2 = memory_service._episodes[-1]["episode_id"]

        assert id1 == id2
        assert id1.startswith("batch-")


# ============================================================================
# Task 3: Graphiti JSON Write Dedup
# ============================================================================

class TestGraphitiJsonWriteDedup:
    """AC-30.10.2: Graphiti JSON write dedup via search check."""

    @pytest.fixture
    def mock_neo4j(self):
        neo4j = MagicMock()
        neo4j.initialize = AsyncMock()
        neo4j.stats = {"initialized": True}
        return neo4j

    @pytest.fixture
    def mock_learning_memory(self):
        client = MagicMock()
        client._initialized = True
        client.initialize = AsyncMock(return_value=True)
        client.search_memories = AsyncMock(return_value=[])
        client.add_learning_episode = AsyncMock(return_value=True)
        return client

    @pytest.fixture
    async def memory_service(self, mock_neo4j, mock_learning_memory):
        from app.services.memory_service import MemoryService
        service = MemoryService(
            neo4j_client=mock_neo4j,
            learning_memory_client=mock_learning_memory,
        )
        await service.initialize()
        return service

    @pytest.mark.asyncio
    async def test_skips_write_when_exists(self, memory_service, mock_learning_memory):
        """If concept+canvas+node already in memories, skip write."""
        mock_learning_memory.search_memories = AsyncMock(return_value=[
            {"concept": "二次方程", "canvas_name": "math.canvas", "node_id": "n1"}
        ])

        result = await memory_service._write_to_graphiti_json_with_retry(
            episode_id="ep-123",
            canvas_name="math.canvas",
            node_id="n1",
            concept="二次方程",
        )

        assert result is True
        mock_learning_memory.add_learning_episode.assert_not_called()

    @pytest.mark.asyncio
    async def test_writes_when_not_exists(self, memory_service, mock_learning_memory):
        """If concept not found, proceed with write."""
        mock_learning_memory.search_memories = AsyncMock(return_value=[])

        result = await memory_service._write_to_graphiti_json_with_retry(
            episode_id="ep-123",
            canvas_name="math.canvas",
            node_id="n1",
            concept="新概念",
        )

        assert result is True
        mock_learning_memory.add_learning_episode.assert_called_once()

    @pytest.mark.asyncio
    async def test_degrades_gracefully_on_search_error(self, memory_service, mock_learning_memory):
        """AC-30.10.5: If dedup check fails, fall back to normal write."""
        mock_learning_memory.search_memories = AsyncMock(side_effect=Exception("DB error"))

        result = await memory_service._write_to_graphiti_json_with_retry(
            episode_id="ep-123",
            canvas_name="math.canvas",
            node_id="n1",
            concept="概念",
        )

        assert result is True
        mock_learning_memory.add_learning_episode.assert_called_once()

    @pytest.mark.asyncio
    async def test_degrades_when_learning_memory_uninitialized(self, memory_service, mock_learning_memory):
        """AC-30.10.5: If _learning_memory not initialized, skip dedup, write normally."""
        mock_learning_memory._initialized = False

        result = await memory_service._write_to_graphiti_json_with_retry(
            episode_id="ep-123",
            canvas_name="math.canvas",
            node_id="n1",
            concept="概念",
        )

        assert result is True
        mock_learning_memory.add_learning_episode.assert_called_once()
