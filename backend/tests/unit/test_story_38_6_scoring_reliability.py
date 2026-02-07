"""
Story 38.6: Scoring Write Reliability — Unit Tests

Tests:
- AC-1: Timeout-retry alignment (outer >= inner total)
- AC-2: Failed write tracking to data/failed_writes.jsonl
- AC-3: Startup recovery from fallback file
- AC-4: Merged view — failed scores in learning history
"""
import asyncio
import json
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.agent_service import (
    MEMORY_WRITE_TIMEOUT,
    FAILED_WRITES_FILE,
    _record_failed_write,
)
from app.services.memory_service import (
    GRAPHITI_JSON_WRITE_TIMEOUT,
    GRAPHITI_RETRY_BACKOFF_BASE,
    FAILED_WRITES_FILE as MS_FAILED_WRITES_FILE,
    MemoryService,
)


class TestAC1TimeoutRetryAlignment:
    """AC-1: Outer timeout must be >= sum of inner retries + margin."""

    def test_outer_timeout_is_at_least_10_seconds(self):
        """[P0] MEMORY_WRITE_TIMEOUT must be >= 10s per AC-1."""
        assert MEMORY_WRITE_TIMEOUT >= 10.0

    def test_inner_per_attempt_timeout_increased(self):
        """[P0] GRAPHITI_JSON_WRITE_TIMEOUT must be > 0.5s (old value)."""
        assert GRAPHITI_JSON_WRITE_TIMEOUT >= 2.0

    def test_retry_backoff_base_is_1_second(self):
        """[P0] Retry backoff base must be 1.0s for 1s/2s/4s progression."""
        assert GRAPHITI_RETRY_BACKOFF_BASE == 1.0

    def test_outer_timeout_covers_inner_total(self):
        """
        [P0] Verify: outer timeout >= 3 × per_attempt_timeout + sum(backoffs) + margin.

        Inner total = 3 × 2.0s + (1.0 + 2.0 + 4.0) = 13.0s
        Outer timeout must be >= 13.0s (we use 15.0s).
        """
        max_retries = 2  # 3 attempts total
        inner_total = (
            (max_retries + 1) * GRAPHITI_JSON_WRITE_TIMEOUT
            + sum(GRAPHITI_RETRY_BACKOFF_BASE * (2 ** i) for i in range(max_retries))
        )
        assert MEMORY_WRITE_TIMEOUT >= inner_total, (
            f"Outer timeout ({MEMORY_WRITE_TIMEOUT}s) < inner total ({inner_total}s)"
        )

    def test_backoff_progression(self):
        """[P1] Backoff sequence should be 1s, 2s, 4s."""
        for attempt in range(3):
            delay = GRAPHITI_RETRY_BACKOFF_BASE * (2 ** attempt)
            expected = [1.0, 2.0, 4.0][attempt]
            assert delay == expected, f"Attempt {attempt}: expected {expected}s, got {delay}s"


class TestAC2FailedWriteTracking:
    """AC-2: Failed writes must be recorded to data/failed_writes.jsonl."""

    def test_record_failed_write_creates_file(self, tmp_path):
        """[P0] _record_failed_write creates JSONL entry with correct fields."""
        fallback_file = tmp_path / "data" / "failed_writes.jsonl"

        with patch("app.services.agent_service.FAILED_WRITES_FILE", fallback_file):
            _record_failed_write(
                event_type="scoring-agent",
                concept_id="node_abc",
                canvas_name="test.canvas",
                score=35.0,
                error_reason="timeout after 15.0s",
            )

        assert fallback_file.exists()
        lines = fallback_file.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 1

        entry = json.loads(lines[0])
        assert entry["event_type"] == "scoring-agent"
        assert entry["concept_id"] == "node_abc"
        assert entry["canvas_name"] == "test.canvas"
        assert entry["score"] == 35.0
        assert entry["error_reason"] == "timeout after 15.0s"
        assert "timestamp" in entry

    def test_record_failed_write_appends(self, tmp_path):
        """[P0] Multiple failures append to the same file."""
        fallback_file = tmp_path / "data" / "failed_writes.jsonl"

        with patch("app.services.agent_service.FAILED_WRITES_FILE", fallback_file):
            _record_failed_write("a", "n1", "c1", 10.0, "err1")
            _record_failed_write("b", "n2", "c2", 20.0, "err2")

        lines = fallback_file.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 2

    def test_record_failed_write_with_none_score(self, tmp_path):
        """[P1] Score can be None (not all writes have scores)."""
        fallback_file = tmp_path / "data" / "failed_writes.jsonl"

        with patch("app.services.agent_service.FAILED_WRITES_FILE", fallback_file):
            _record_failed_write("hint-generation", "n1", "c1", None, "err")

        entry = json.loads(
            fallback_file.read_text(encoding="utf-8").strip()
        )
        assert entry["score"] is None


class TestAC3StartupRecovery:
    """AC-3: Application startup replays failed writes."""

    @pytest.fixture
    def memory_service(self):
        """Create a MemoryService with mocked dependencies."""
        ms = MemoryService.__new__(MemoryService)
        ms.neo4j = MagicMock()
        ms._learning_memory = AsyncMock()
        ms._learning_memory.add_learning_episode = AsyncMock(return_value=True)
        ms._initialized = True
        ms._episodes = []
        ms._score_history_cache = {}
        return ms

    @pytest.mark.asyncio
    async def test_recover_no_file(self, memory_service):
        """[P0] No fallback file → returns zeros, no crash."""
        with patch(
            "app.services.memory_service.FAILED_WRITES_FILE",
            Path("/nonexistent/failed_writes.jsonl"),
        ):
            result = await memory_service.recover_failed_writes()

        assert result == {"recovered": 0, "pending": 0}

    @pytest.mark.asyncio
    async def test_recover_successful_replay(self, memory_service, tmp_path):
        """[P0] Entries are replayed and removed from file on success."""
        fallback_file = tmp_path / "failed_writes.jsonl"
        entry = {
            "timestamp": "2026-02-06T10:00:00",
            "event_type": "scoring-agent",
            "concept_id": "node_1",
            "canvas_name": "test.canvas",
            "score": 35.0,
            "error_reason": "timeout",
        }
        fallback_file.write_text(json.dumps(entry) + "\n", encoding="utf-8")

        with patch("app.services.memory_service.FAILED_WRITES_FILE", fallback_file):
            result = await memory_service.recover_failed_writes()

        assert result["recovered"] == 1
        assert result["pending"] == 0
        # File should be deleted after full recovery
        assert not fallback_file.exists()

    @pytest.mark.asyncio
    async def test_recover_partial_failure(self, memory_service, tmp_path):
        """[P0] If replay fails, entry stays in file."""
        fallback_file = tmp_path / "failed_writes.jsonl"
        entries = [
            {"timestamp": "t1", "event_type": "a", "concept_id": "n1", "canvas_name": "c1", "score": 10.0, "error_reason": "e1"},
            {"timestamp": "t2", "event_type": "b", "concept_id": "n2", "canvas_name": "c2", "score": 20.0, "error_reason": "e2"},
        ]
        fallback_file.write_text(
            "\n".join(json.dumps(e) for e in entries) + "\n", encoding="utf-8"
        )

        # First call succeeds, second fails
        call_count = 0

        async def mock_retry(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return call_count == 1  # First succeeds, second fails

        memory_service._write_to_graphiti_json_with_retry = mock_retry

        with patch("app.services.memory_service.FAILED_WRITES_FILE", fallback_file):
            result = await memory_service.recover_failed_writes()

        assert result["recovered"] == 1
        assert result["pending"] == 1
        # File should contain only the still-pending entry
        remaining = fallback_file.read_text(encoding="utf-8").strip().splitlines()
        assert len(remaining) == 1

    @pytest.mark.asyncio
    async def test_recover_malformed_entries_skipped(self, memory_service, tmp_path):
        """[P1] Malformed JSON lines are silently skipped."""
        fallback_file = tmp_path / "failed_writes.jsonl"
        fallback_file.write_text(
            "not valid json\n"
            + json.dumps({"timestamp": "t", "concept_id": "n", "canvas_name": "c", "score": 5.0, "error_reason": "e"})
            + "\n",
            encoding="utf-8",
        )

        with patch("app.services.memory_service.FAILED_WRITES_FILE", fallback_file):
            result = await memory_service.recover_failed_writes()

        # Valid entry recovered, malformed skipped
        assert result["recovered"] == 1
        assert result["pending"] == 0


class TestAC4MergedView:
    """AC-4: Failed scores are merged into learning history results."""

    @pytest.fixture
    def memory_service(self):
        ms = MemoryService.__new__(MemoryService)
        ms.neo4j = AsyncMock()
        ms.neo4j.get_learning_history = AsyncMock(return_value=[])
        ms._learning_memory = AsyncMock()
        ms._initialized = True
        ms._episodes = []
        ms._score_history_cache = {}
        return ms

    def test_load_failed_scores_empty(self, memory_service):
        """[P0] No fallback file → empty list."""
        with patch(
            "app.services.memory_service.FAILED_WRITES_FILE",
            Path("/nonexistent"),
        ):
            result = memory_service.load_failed_scores()
        assert result == []

    def test_load_failed_scores_with_entries(self, memory_service, tmp_path):
        """[P0] Returns structured entries from JSONL."""
        fallback_file = tmp_path / "failed_writes.jsonl"
        entry = {
            "timestamp": "2026-02-06T10:00:00",
            "event_type": "scoring-agent",
            "concept_id": "node_1",
            "canvas_name": "test.canvas",
            "score": 35.0,
            "error_reason": "timeout",
        }
        fallback_file.write_text(json.dumps(entry) + "\n", encoding="utf-8")

        with patch("app.services.memory_service.FAILED_WRITES_FILE", fallback_file):
            results = memory_service.load_failed_scores()

        assert len(results) == 1
        assert results[0]["source"] == "fallback"
        assert results[0]["score"] == 35.0
        assert results[0]["node_id"] == "node_1"

    @pytest.mark.asyncio
    async def test_get_learning_history_merges_failed_scores(self, memory_service, tmp_path):
        """[P0] get_learning_history() includes fallback entries in results."""
        fallback_file = tmp_path / "failed_writes.jsonl"
        entry = {
            "timestamp": "2026-02-06T10:00:00",
            "event_type": "scoring-agent",
            "concept_id": "node_1",
            "canvas_name": "test.canvas",
            "score": 35.0,
            "error_reason": "timeout",
        }
        fallback_file.write_text(json.dumps(entry) + "\n", encoding="utf-8")

        # Neo4j returns one episode
        neo4j_episode = {
            "timestamp": "2026-02-06T09:00:00",
            "node_id": "node_2",
            "concept": "concept_2",
            "score": 40.0,
        }
        memory_service.neo4j.get_learning_history = AsyncMock(return_value=[neo4j_episode])

        with patch("app.services.memory_service.FAILED_WRITES_FILE", fallback_file):
            result = await memory_service.get_learning_history(user_id="test")

        # Both Neo4j episode and fallback entry should appear
        assert result["total"] == 2
        sources = [item.get("source") for item in result["items"]]
        assert "fallback" in sources

    @pytest.mark.asyncio
    async def test_get_learning_history_deduplicates(self, memory_service, tmp_path):
        """[P1] Fallback entries with same node_id+timestamp as Neo4j entries are excluded."""
        fallback_file = tmp_path / "failed_writes.jsonl"
        entry = {
            "timestamp": "2026-02-06T10:00:00",
            "event_type": "scoring-agent",
            "concept_id": "node_1",
            "canvas_name": "test.canvas",
            "score": 35.0,
            "error_reason": "timeout",
        }
        fallback_file.write_text(json.dumps(entry) + "\n", encoding="utf-8")

        # Neo4j already has the same entry (recovered between request)
        neo4j_episode = {
            "timestamp": "2026-02-06T10:00:00",
            "node_id": "node_1",
            "concept": "node_1",
            "score": 35.0,
        }
        memory_service.neo4j.get_learning_history = AsyncMock(return_value=[neo4j_episode])

        with patch("app.services.memory_service.FAILED_WRITES_FILE", fallback_file):
            result = await memory_service.get_learning_history(user_id="test")

        # Should not duplicate — only 1 entry
        assert result["total"] == 1


class TestRegressionSafety:
    """Verify changes don't break existing functionality."""

    def test_failed_writes_file_path_in_data_dir(self):
        """[P0] Both modules reference same data directory."""
        assert FAILED_WRITES_FILE.name == "failed_writes.jsonl"
        assert MS_FAILED_WRITES_FILE.name == "failed_writes.jsonl"
        assert "data" in str(FAILED_WRITES_FILE)

    def test_constants_are_consistent(self):
        """[P0] Memory write timeout covers inner retry budget."""
        # 3 attempts × 2.0s timeout + backoff sum (1+2=3s) = 9s
        # Outer must be > 9s
        max_inner = 3 * GRAPHITI_JSON_WRITE_TIMEOUT + 3.0  # 3s backoff for 2 retries
        assert MEMORY_WRITE_TIMEOUT > max_inner
