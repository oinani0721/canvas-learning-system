# Canvas Learning System - Story 30.11 Tests
# 批量端点真批量改造
"""
Story 30.11 - Batch True Parallel Tests

Tests that record_batch_learning_events() uses asyncio.gather for parallel
Neo4j writes with Semaphore concurrency control.

[Source: docs/stories/30.11.batch-true-parallel.story.md]
"""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.conftest import simulate_async_delay


# ============================================================================
# Task 1: Parallel execution
# ============================================================================

class TestBatchParallelExecution:
    """AC-30.11.1: asyncio.gather parallel writes."""

    @pytest.fixture
    def mock_neo4j(self):
        neo4j = MagicMock()
        neo4j.initialize = AsyncMock()
        neo4j.stats = {"initialized": True, "connected": True}
        neo4j.record_episode = AsyncMock()
        neo4j.create_learning_relationship = AsyncMock()
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

    def _make_events(self, count):
        return [
            {
                "event_type": f"scoring_{i}",
                "timestamp": f"2026-02-09T10:{i:02d}:00",
                "canvas_path": f"test/canvas_{i}.canvas",
                "node_id": f"node_{i}",
                "metadata": {"concept": f"concept_{i}"}
            }
            for i in range(count)
        ]

    @pytest.mark.asyncio
    async def test_50_events_all_processed(self, memory_service, mock_neo4j):
        """50 events should all be processed successfully."""
        events = self._make_events(50)

        with patch("app.services.memory_service.settings") as mock_settings:
            mock_settings.BATCH_NEO4J_CONCURRENCY = 10
            mock_settings.ENABLE_GRAPHITI_JSON_DUAL_WRITE = False
            result = await memory_service.record_batch_learning_events(events)

        assert result["processed"] == 50
        assert result["failed"] == 0
        assert result["success"] is True
        assert len(result["episode_ids"]) == 50
        assert "batch_avg_latency_ms" in result

    @pytest.mark.asyncio
    async def test_neo4j_called_for_each_event(self, memory_service, mock_neo4j):
        """Neo4j record_episode is called once per valid event."""
        events = self._make_events(5)

        with patch("app.services.memory_service.settings") as mock_settings:
            mock_settings.BATCH_NEO4J_CONCURRENCY = 10
            mock_settings.ENABLE_GRAPHITI_JSON_DUAL_WRITE = False
            await memory_service.record_batch_learning_events(events)

        assert mock_neo4j.record_episode.call_count == 5

    @pytest.mark.asyncio
    async def test_parallel_faster_than_sequential(self, memory_service, mock_neo4j):
        """Parallel batch should complete significantly faster than N * delay."""
        delay = 0.02  # 20ms per call

        async def slow_record(payload):
            await simulate_async_delay(delay)

        mock_neo4j.record_episode = AsyncMock(side_effect=slow_record)
        events = self._make_events(10)

        with patch("app.services.memory_service.settings") as mock_settings:
            mock_settings.BATCH_NEO4J_CONCURRENCY = 10
            mock_settings.ENABLE_GRAPHITI_JSON_DUAL_WRITE = False

            start = time.monotonic()
            result = await memory_service.record_batch_learning_events(events)
            elapsed = time.monotonic() - start

        assert result["processed"] == 10
        # Sequential would take 10 * 20ms = 200ms
        # Parallel should take ~20ms + overhead < 150ms
        assert elapsed < 0.15, f"Took {elapsed:.3f}s, should be < 0.15s for parallel"

    @pytest.mark.asyncio
    async def test_performance_stats_recorded(self, memory_service, mock_neo4j):
        """batch_avg_latency_ms is recorded in stats."""
        events = self._make_events(3)

        with patch("app.services.memory_service.settings") as mock_settings:
            mock_settings.BATCH_NEO4J_CONCURRENCY = 10
            mock_settings.ENABLE_GRAPHITI_JSON_DUAL_WRITE = False
            result = await memory_service.record_batch_learning_events(events)

        assert result["batch_avg_latency_ms"] >= 0
        assert memory_service._batch_stats["batch_avg_latency_ms"] >= 0
        assert memory_service._batch_stats["last_batch_size"] == 3


# ============================================================================
# Task 2: Partial failure isolation
# ============================================================================

class TestBatchPartialFailure:
    """AC-30.11.2: Partial failure isolation."""

    @pytest.fixture
    def mock_neo4j(self):
        neo4j = MagicMock()
        neo4j.initialize = AsyncMock()
        neo4j.stats = {"initialized": True, "connected": True}
        neo4j.record_episode = AsyncMock()
        neo4j.create_learning_relationship = AsyncMock()
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

    @pytest.mark.asyncio
    async def test_neo4j_failure_does_not_block_processing(self, memory_service, mock_neo4j):
        """Neo4j write failures don't affect processed count (data is in memory)."""
        mock_neo4j.record_episode = AsyncMock(side_effect=Exception("Neo4j timeout"))

        events = [
            {"event_type": "scoring", "timestamp": "2026-02-09T10:00:00",
             "canvas_path": "test/a.canvas", "node_id": "n1", "metadata": {}},
            {"event_type": "scoring", "timestamp": "2026-02-09T10:01:00",
             "canvas_path": "test/b.canvas", "node_id": "n2", "metadata": {}},
        ]

        with patch("app.services.memory_service.settings") as mock_settings:
            mock_settings.BATCH_NEO4J_CONCURRENCY = 10
            mock_settings.ENABLE_GRAPHITI_JSON_DUAL_WRITE = False
            result = await memory_service.record_batch_learning_events(events)

        # Events are processed (stored in memory) even if Neo4j fails
        # C3 fix: Neo4j errors are now surfaced in failed count and success flag
        assert result["processed"] == 2
        assert result["failed"] == 2  # Neo4j errors counted
        assert result["success"] is False  # failed > 0 means success=False

    @pytest.mark.asyncio
    async def test_validation_failure_isolated(self, memory_service, mock_neo4j):
        """Validation failures don't affect other events."""
        events = [
            {"event_type": "scoring", "timestamp": "2026-02-09T10:00:00",
             "canvas_path": "test/a.canvas", "node_id": "n1"},
            {"event_type": "scoring"},  # Missing required fields
            {"event_type": "scoring", "timestamp": "2026-02-09T10:02:00",
             "canvas_path": "test/c.canvas", "node_id": "n3"},
        ]

        with patch("app.services.memory_service.settings") as mock_settings:
            mock_settings.BATCH_NEO4J_CONCURRENCY = 10
            mock_settings.ENABLE_GRAPHITI_JSON_DUAL_WRITE = False
            result = await memory_service.record_batch_learning_events(events)

        assert result["processed"] == 2
        assert result["failed"] == 1
        assert len(result["errors"]) == 1
        assert result["errors"][0]["index"] == 1

    @pytest.mark.asyncio
    async def test_episode_ids_only_for_successful(self, memory_service, mock_neo4j):
        """episode_ids list only contains IDs for successfully processed events."""
        events = [
            {"event_type": "scoring", "timestamp": "2026-02-09T10:00:00",
             "canvas_path": "test/a.canvas", "node_id": "n1"},
            {"event_type": "bad"},  # Missing fields
        ]

        with patch("app.services.memory_service.settings") as mock_settings:
            mock_settings.BATCH_NEO4J_CONCURRENCY = 10
            mock_settings.ENABLE_GRAPHITI_JSON_DUAL_WRITE = False
            result = await memory_service.record_batch_learning_events(events)

        assert len(result["episode_ids"]) == 1  # Only 1 successful


# ============================================================================
# Task 3: Semaphore concurrency control
# ============================================================================

class TestBatchSemaphore:
    """AC-30.11.3: Semaphore limits concurrent Neo4j connections."""

    @pytest.fixture
    def mock_neo4j(self):
        neo4j = MagicMock()
        neo4j.initialize = AsyncMock()
        neo4j.stats = {"initialized": True, "connected": True}
        neo4j.create_learning_relationship = AsyncMock()
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

    @pytest.mark.asyncio
    async def test_concurrency_limited_by_semaphore(self, memory_service, mock_neo4j):
        """At most BATCH_NEO4J_CONCURRENCY tasks run simultaneously."""
        max_concurrent = 0
        current_concurrent = 0
        lock = asyncio.Lock()

        async def tracked_record(payload):
            nonlocal max_concurrent, current_concurrent
            async with lock:
                current_concurrent += 1
                max_concurrent = max(max_concurrent, current_concurrent)
            await simulate_async_delay(0.01)
            async with lock:
                current_concurrent -= 1

        mock_neo4j.record_episode = AsyncMock(side_effect=tracked_record)

        events = [
            {"event_type": f"score_{i}", "timestamp": f"2026-02-09T10:{i:02d}:00",
             "canvas_path": f"test/c_{i}.canvas", "node_id": f"n_{i}"}
            for i in range(20)
        ]

        with patch("app.services.memory_service.settings") as mock_settings:
            mock_settings.BATCH_NEO4J_CONCURRENCY = 3
            mock_settings.ENABLE_GRAPHITI_JSON_DUAL_WRITE = False
            await memory_service.record_batch_learning_events(events)

        assert max_concurrent <= 3, f"Max concurrent was {max_concurrent}, expected <= 3"
        assert max_concurrent >= 2, f"Max concurrent was {max_concurrent}, expected >= 2 (parallel)"


# ============================================================================
# Task 4: Neo4j unavailable degradation
# ============================================================================

class TestBatchNeo4jDegradation:
    """AC-30.11.3: Neo4j unavailable degrades to memory-only."""

    @pytest.fixture
    def mock_neo4j(self):
        neo4j = MagicMock()
        neo4j.initialize = AsyncMock()
        neo4j.stats = {"initialized": False}  # Neo4j NOT available
        neo4j.record_episode = AsyncMock()
        neo4j.create_learning_relationship = AsyncMock()
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

    @pytest.mark.asyncio
    async def test_neo4j_unavailable_still_processes_to_memory(self, memory_service, mock_neo4j):
        """When Neo4j is not initialized, events are still stored in _episodes."""
        events = [
            {"event_type": "scoring", "timestamp": "2026-02-09T10:00:00",
             "canvas_path": "test/a.canvas", "node_id": "n1"},
        ]

        with patch("app.services.memory_service.settings") as mock_settings:
            mock_settings.BATCH_NEO4J_CONCURRENCY = 10
            mock_settings.ENABLE_GRAPHITI_JSON_DUAL_WRITE = False
            result = await memory_service.record_batch_learning_events(events)

        assert result["processed"] == 1
        assert result["success"] is True
        # Neo4j record_episode should NOT be called
        mock_neo4j.record_episode.assert_not_called()
        # But event should be in memory
        assert len(memory_service._episodes) >= 1


# ============================================================================
# Task 5: Idempotency compatibility (Story 30.10)
# ============================================================================

class TestBatchIdempotencyCompat:
    """AC-30.11.4: Compatible with Story 30.10 deterministic IDs."""

    @pytest.fixture
    def mock_neo4j(self):
        neo4j = MagicMock()
        neo4j.initialize = AsyncMock()
        neo4j.stats = {"initialized": True, "connected": True}
        neo4j.record_episode = AsyncMock()
        neo4j.create_learning_relationship = AsyncMock()
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

    @pytest.mark.asyncio
    async def test_duplicate_batch_no_duplicates(self, memory_service, mock_neo4j):
        """Submitting the same batch twice should not create duplicates in _episodes."""
        events = [
            {"event_type": "scoring", "timestamp": "2026-02-09T10:00:00",
             "canvas_path": "test/a.canvas", "node_id": "n1"},
        ]

        with patch("app.services.memory_service.settings") as mock_settings:
            mock_settings.BATCH_NEO4J_CONCURRENCY = 10
            mock_settings.ENABLE_GRAPHITI_JSON_DUAL_WRITE = False

            result1 = await memory_service.record_batch_learning_events(events)
            result2 = await memory_service.record_batch_learning_events(events)

        # Both calls succeed
        assert result1["processed"] == 1
        assert result2["processed"] == 1
        # Same episode_id
        assert result1["episode_ids"] == result2["episode_ids"]

        # _episodes should have exactly 1 entry (dedup)
        matching = [ep for ep in memory_service._episodes if ep.get("episode_id") == result1["episode_ids"][0]]
        assert len(matching) == 1

    @pytest.mark.asyncio
    async def test_config_batch_neo4j_concurrency_exists(self):
        """BATCH_NEO4J_CONCURRENCY config field exists in Settings."""
        from app.config import Settings
        s = Settings()
        assert hasattr(s, "BATCH_NEO4J_CONCURRENCY")
        assert s.BATCH_NEO4J_CONCURRENCY == 10  # default
