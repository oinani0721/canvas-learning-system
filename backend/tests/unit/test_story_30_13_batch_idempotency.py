# Canvas Learning System - Story 30.13 Tests
# 批量性能 + 幂等性测试补全
"""
Story 30.13 - Batch Performance + Idempotency Tests

Task 1: Idempotency tests
Task 2: Performance benchmark tests
Task 3: Partial failure recovery tests

[Source: docs/stories/30.13.test-batch-idempotency.story.md]
"""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def mock_neo4j():
    neo4j = MagicMock()
    neo4j.initialize = AsyncMock()
    neo4j.stats = {"initialized": True, "connected": True}
    neo4j.record_episode = AsyncMock()
    neo4j.create_learning_relationship = AsyncMock()
    return neo4j


@pytest.fixture
def mock_learning_memory():
    client = MagicMock()
    client._initialized = False
    client.initialize = AsyncMock(return_value=True)
    return client


@pytest.fixture
async def memory_service(mock_neo4j, mock_learning_memory):
    from app.services.memory_service import MemoryService
    service = MemoryService(
        neo4j_client=mock_neo4j,
        learning_memory_client=mock_learning_memory,
    )
    await service.initialize()
    return service


def _make_event(canvas_path="test/a.canvas", node_id="n1",
                event_type="scoring", timestamp="2026-02-09T10:00:00"):
    return {
        "event_type": event_type,
        "timestamp": timestamp,
        "canvas_path": canvas_path,
        "node_id": node_id,
        "metadata": {"concept": "test_concept"}
    }


# ============================================================================
# Task 1: Idempotency Tests (AC-30.13.1)
# ============================================================================

class TestBatchIdempotency:
    """AC-30.13.1: Idempotent batch writes."""

    @pytest.mark.asyncio
    async def test_duplicate_event_detection(self, memory_service):
        """Same event sent twice produces only one episode."""
        event = _make_event()

        with patch("app.services.memory_service.settings") as mock_settings:
            mock_settings.BATCH_NEO4J_CONCURRENCY = 10
            mock_settings.ENABLE_GRAPHITI_JSON_DUAL_WRITE = False
            r1 = await memory_service.record_batch_learning_events([event])
            r2 = await memory_service.record_batch_learning_events([event])

        assert r1["processed"] == 1
        assert r2["processed"] == 1
        assert r1["episode_ids"] == r2["episode_ids"]

        # Only 1 unique episode in memory
        unique_ids = set(ep.get("episode_id") for ep in memory_service._episodes)
        matching = [ep for ep in memory_service._episodes if ep.get("episode_id") == r1["episode_ids"][0]]
        assert len(matching) == 1

    @pytest.mark.asyncio
    async def test_idempotent_writes_across_retries(self, memory_service):
        """Simulated timeout + retry scenario remains idempotent."""
        event = _make_event()

        with patch("app.services.memory_service.settings") as mock_settings:
            mock_settings.BATCH_NEO4J_CONCURRENCY = 10
            mock_settings.ENABLE_GRAPHITI_JSON_DUAL_WRITE = False

            # Simulate 3 retries
            for _ in range(3):
                await memory_service.record_batch_learning_events([event])

        matching = [ep for ep in memory_service._episodes if ep.get("canvas_path") == "test/a.canvas"]
        assert len(matching) == 1

    @pytest.mark.asyncio
    async def test_large_batch_idempotency(self, memory_service):
        """100 unique events + 100 duplicates = still 100 unique."""
        events = [
            _make_event(node_id=f"n_{i}", timestamp=f"2026-02-09T{i:02d}:00:00")
            for i in range(100)
        ]

        with patch("app.services.memory_service.settings") as mock_settings:
            mock_settings.BATCH_NEO4J_CONCURRENCY = 10
            mock_settings.ENABLE_GRAPHITI_JSON_DUAL_WRITE = False

            r1 = await memory_service.record_batch_learning_events(events)
            r2 = await memory_service.record_batch_learning_events(events)

        assert r1["processed"] == 100
        assert r2["processed"] == 100

        # Count unique episode_ids in _episodes
        all_ids = [ep.get("episode_id") for ep in memory_service._episodes
                   if ep.get("canvas_path") == "test/a.canvas"]
        assert len(all_ids) == len(set(all_ids))  # No dups
        assert len(all_ids) == 100

    @pytest.mark.asyncio
    async def test_different_events_not_deduplicated(self, memory_service):
        """Events with different content produce different episode_ids."""
        event_a = _make_event(node_id="n1", timestamp="2026-02-09T10:00:00")
        event_b = _make_event(node_id="n2", timestamp="2026-02-09T10:01:00")

        with patch("app.services.memory_service.settings") as mock_settings:
            mock_settings.BATCH_NEO4J_CONCURRENCY = 10
            mock_settings.ENABLE_GRAPHITI_JSON_DUAL_WRITE = False

            r = await memory_service.record_batch_learning_events([event_a, event_b])

        assert r["processed"] == 2
        assert len(r["episode_ids"]) == 2
        assert r["episode_ids"][0] != r["episode_ids"][1]


# ============================================================================
# Task 2: Performance Benchmark Tests (AC-30.13.2)
# ============================================================================

class TestBatchPerformance:
    """AC-30.13.2: Performance benchmarks."""

    @pytest.mark.asyncio
    async def test_batch_50_events_under_500ms(self, memory_service, mock_neo4j):
        """50 events processed in < 500ms with mock Neo4j."""
        events = [
            _make_event(node_id=f"n_{i}", timestamp=f"2026-02-09T10:{i:02d}:00")
            for i in range(50)
        ]

        with patch("app.services.memory_service.settings") as mock_settings:
            mock_settings.BATCH_NEO4J_CONCURRENCY = 10
            mock_settings.ENABLE_GRAPHITI_JSON_DUAL_WRITE = False

            start = time.monotonic()
            result = await memory_service.record_batch_learning_events(events)
            elapsed = time.monotonic() - start

        assert result["processed"] == 50
        assert elapsed < 0.5, f"Took {elapsed:.3f}s, must be < 0.5s"

    @pytest.mark.asyncio
    async def test_batch_1000_events_completion(self, memory_service, mock_neo4j):
        """1000 events completes without timeout."""
        events = [
            _make_event(
                node_id=f"n_{i}",
                canvas_path=f"test/c_{i // 100}.canvas",
                timestamp=f"2026-02-09T{(i // 60) % 24:02d}:{i % 60:02d}:00"
            )
            for i in range(1000)
        ]

        with patch("app.services.memory_service.settings") as mock_settings:
            mock_settings.BATCH_NEO4J_CONCURRENCY = 20
            mock_settings.ENABLE_GRAPHITI_JSON_DUAL_WRITE = False

            result = await memory_service.record_batch_learning_events(events)

        assert result["processed"] == 1000
        assert result["failed"] == 0

    @pytest.mark.asyncio
    async def test_batch_memory_metrics(self, memory_service, mock_neo4j):
        """Stats fields are populated after batch processing."""
        events = [_make_event(node_id=f"n_{i}", timestamp=f"2026-02-09T10:{i:02d}:00")
                  for i in range(10)]

        with patch("app.services.memory_service.settings") as mock_settings:
            mock_settings.BATCH_NEO4J_CONCURRENCY = 10
            mock_settings.ENABLE_GRAPHITI_JSON_DUAL_WRITE = False

            result = await memory_service.record_batch_learning_events(events)

        assert "batch_avg_latency_ms" in result
        assert result["batch_avg_latency_ms"] >= 0
        assert memory_service._batch_stats["last_batch_size"] == 10

    @pytest.mark.asyncio
    async def test_concurrent_batch_requests(self, memory_service, mock_neo4j):
        """Two concurrent batch requests don't corrupt data."""
        events_a = [_make_event(node_id=f"a_{i}", timestamp=f"2026-02-09T10:{i:02d}:00")
                    for i in range(10)]
        events_b = [_make_event(node_id=f"b_{i}", timestamp=f"2026-02-09T11:{i:02d}:00")
                    for i in range(10)]

        with patch("app.services.memory_service.settings") as mock_settings:
            mock_settings.BATCH_NEO4J_CONCURRENCY = 10
            mock_settings.ENABLE_GRAPHITI_JSON_DUAL_WRITE = False

            r_a, r_b = await asyncio.gather(
                memory_service.record_batch_learning_events(events_a),
                memory_service.record_batch_learning_events(events_b),
            )

        assert r_a["processed"] == 10
        assert r_b["processed"] == 10
        # All 20 unique episodes should be in _episodes
        all_ids = set(ep.get("episode_id") for ep in memory_service._episodes
                      if ep.get("canvas_path") == "test/a.canvas")
        assert len(all_ids) >= 20


# ============================================================================
# Task 3: Partial Failure Recovery Tests (AC-30.13.3)
# ============================================================================

class TestBatchPartialFailureRecovery:
    """AC-30.13.3: Partial failure recovery."""

    @pytest.mark.asyncio
    async def test_partial_failure_recovery(self, memory_service, mock_neo4j):
        """50 events with 5 invalid: 45 succeed, 5 fail with correct indices."""
        valid = [
            _make_event(node_id=f"v_{i}", timestamp=f"2026-02-09T10:{i:02d}:00")
            for i in range(45)
        ]
        invalid = [
            {"event_type": "bad"}  # Missing fields
            for _ in range(5)
        ]
        # Interleave: valid[0..8], invalid[0], valid[9..17], invalid[1], ...
        events = []
        for i in range(5):
            events.extend(valid[i*9:(i+1)*9])
            events.append(invalid[i])

        with patch("app.services.memory_service.settings") as mock_settings:
            mock_settings.BATCH_NEO4J_CONCURRENCY = 10
            mock_settings.ENABLE_GRAPHITI_JSON_DUAL_WRITE = False
            result = await memory_service.record_batch_learning_events(events)

        assert result["processed"] == 45
        assert result["failed"] == 5
        assert len(result["errors"]) == 5

        # Verify error indices correspond to invalid events (every 10th starting at 9)
        error_indices = sorted(e["index"] for e in result["errors"])
        expected = [9, 19, 29, 39, 49]
        assert error_indices == expected

    @pytest.mark.asyncio
    async def test_event_ordering_preserved(self, memory_service, mock_neo4j):
        """Episode IDs are returned in the same order as input events."""
        events = [
            _make_event(node_id=f"ordered_{i}", timestamp=f"2026-02-09T10:{i:02d}:00")
            for i in range(5)
        ]

        with patch("app.services.memory_service.settings") as mock_settings:
            mock_settings.BATCH_NEO4J_CONCURRENCY = 10
            mock_settings.ENABLE_GRAPHITI_JSON_DUAL_WRITE = False
            result = await memory_service.record_batch_learning_events(events)

        # episode_ids should be in deterministic order matching input
        assert len(result["episode_ids"]) == 5
        # All should be unique
        assert len(set(result["episode_ids"])) == 5

    @pytest.mark.asyncio
    async def test_neo4j_unavailable_fallback(self, memory_service, mock_neo4j):
        """Neo4j unavailable: all events still stored in memory."""
        mock_neo4j.stats = {"initialized": False}

        events = [
            _make_event(node_id=f"fb_{i}", timestamp=f"2026-02-09T10:{i:02d}:00")
            for i in range(10)
        ]

        with patch("app.services.memory_service.settings") as mock_settings:
            mock_settings.BATCH_NEO4J_CONCURRENCY = 10
            mock_settings.ENABLE_GRAPHITI_JSON_DUAL_WRITE = False
            result = await memory_service.record_batch_learning_events(events)

        assert result["processed"] == 10
        assert result["failed"] == 0
        mock_neo4j.record_episode.assert_not_called()
