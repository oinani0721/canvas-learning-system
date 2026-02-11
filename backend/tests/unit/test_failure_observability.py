# Story 36.12: Failure Observability Unit Tests
#
# Tests for AC-36.12.4 (edge sync failures), AC-36.12.5 (dual-write failures),
# AC-36.12.6 (health check degradation), AC-36.12.8 (dead-letter persistence).
#
# [Source: docs/stories/36.12.story.md#Testing]
import asyncio
import json
import logging
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.conftest import simulate_async_delay

from app.core.failure_counters import (
    DUAL_WRITE_DEAD_LETTER_PATH,
    EDGE_SYNC_DEAD_LETTER_PATH,
    get_dual_write_failures,
    get_edge_sync_failures,
    increment_dual_write_failures,
    increment_edge_sync_failures,
    reset_counters,
    write_dead_letter,
)


# ============================================================================
# Fixture: Reset counters before each test
# ============================================================================


@pytest.fixture(autouse=True)
def _reset_counters():
    """Reset failure counters before each test to prevent cross-contamination."""
    reset_counters()
    yield
    reset_counters()


# ============================================================================
# AC-36.12.4: Edge Sync Failure Counter Tests
# ============================================================================


class TestEdgeSyncFailureCounter:
    """Tests for edge_sync_failures_total counter (AC-36.12.4)."""

    def test_initial_count_is_zero(self):
        """Counter starts at zero after reset."""
        assert get_edge_sync_failures() == 0

    def test_increment_returns_new_count(self):
        """increment_edge_sync_failures returns the new count."""
        assert increment_edge_sync_failures() == 1
        assert increment_edge_sync_failures() == 2
        assert increment_edge_sync_failures() == 3

    def test_get_reflects_increments(self):
        """get_edge_sync_failures returns accumulated count."""
        increment_edge_sync_failures()
        increment_edge_sync_failures()
        assert get_edge_sync_failures() == 2

    def test_reset_clears_counter(self):
        """reset_counters clears edge sync failure count."""
        increment_edge_sync_failures()
        increment_edge_sync_failures()
        prev = reset_counters()
        assert prev["edge_sync_failures"] == 2
        assert get_edge_sync_failures() == 0


# ============================================================================
# AC-36.12.5: Dual-Write Failure Counter Tests
# ============================================================================


class TestDualWriteFailureCounter:
    """Tests for dual_write_failures_total counter (AC-36.12.5)."""

    def test_initial_count_is_zero(self):
        assert get_dual_write_failures() == 0

    def test_increment_returns_new_count(self):
        assert increment_dual_write_failures() == 1
        assert increment_dual_write_failures() == 2

    def test_reset_clears_counter(self):
        increment_dual_write_failures()
        prev = reset_counters()
        assert prev["dual_write_failures"] == 1
        assert get_dual_write_failures() == 0


# ============================================================================
# AC-36.12.8: Dead-Letter File Tests
# ============================================================================


class TestDeadLetterWrite:
    """Tests for dead-letter JSONL file writes (AC-36.12.8)."""

    def test_write_edge_sync_dead_letter(self, tmp_path):
        """Edge sync failure is written to dead-letter JSONL."""
        dl_path = tmp_path / "failed_edge_syncs.jsonl"
        write_dead_letter(
            dl_path,
            "edge_sync",
            "ConnectionRefused",
            edge_id="edge-123",
            canvas_name="test.canvas",
            retry_count=3,
        )
        lines = dl_path.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 1
        entry = json.loads(lines[0])
        assert entry["type"] == "edge_sync"
        assert entry["edge_id"] == "edge-123"
        assert entry["canvas_name"] == "test.canvas"
        assert entry["error"] == "ConnectionRefused"
        assert entry["retry_count"] == 3
        assert "timestamp" in entry

    def test_write_dual_write_dead_letter(self, tmp_path):
        """Dual-write failure is written to dead-letter JSONL."""
        dl_path = tmp_path / "failed_dual_writes.jsonl"
        write_dead_letter(
            dl_path,
            "dual_write",
            "TimeoutError after 2.0s",
            episode_id="ep-456",
            timeout_ms=2000,
        )
        lines = dl_path.read_text(encoding="utf-8").strip().split("\n")
        entry = json.loads(lines[0])
        assert entry["type"] == "dual_write"
        assert entry["episode_id"] == "ep-456"
        assert entry["timeout_ms"] == 2000

    def test_dead_letter_append_mode(self, tmp_path):
        """Multiple writes append to the same file (AC-36.12.8)."""
        dl_path = tmp_path / "test.jsonl"
        write_dead_letter(dl_path, "edge_sync", "err1", edge_id="e1")
        write_dead_letter(dl_path, "edge_sync", "err2", edge_id="e2")
        lines = dl_path.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 2
        assert json.loads(lines[0])["edge_id"] == "e1"
        assert json.loads(lines[1])["edge_id"] == "e2"

    def test_dead_letter_creates_parent_directory(self, tmp_path):
        """write_dead_letter creates parent dirs if missing."""
        dl_path = tmp_path / "sub" / "dir" / "test.jsonl"
        write_dead_letter(dl_path, "edge_sync", "err", edge_id="e1")
        assert dl_path.exists()

    def test_dead_letter_survives_utf8(self, tmp_path):
        """Dead-letter handles Chinese canvas names (AC-36.12.8)."""
        dl_path = tmp_path / "test.jsonl"
        write_dead_letter(
            dl_path,
            "edge_sync",
            "连接拒绝",
            edge_id="e1",
            canvas_name="离散数学.canvas",
        )
        entry = json.loads(dl_path.read_text(encoding="utf-8").strip())
        assert entry["canvas_name"] == "离散数学.canvas"
        assert entry["error"] == "连接拒绝"


# ============================================================================
# AC-36.12.4: Edge Sync in CanvasService Integration
# ============================================================================


class TestCanvasServiceEdgeSyncFailure:
    """Test that _sync_edge_to_neo4j increments counter + writes dead-letter on failure."""

    @pytest.mark.asyncio
    async def test_edge_sync_failure_increments_counter(self):
        """When Neo4j sync fails after retries, edge_sync_failures counter increments."""
        from app.services.canvas_service import CanvasService

        service = CanvasService(canvas_base_path="/tmp/test")

        # Create a mock memory_client with a neo4j that always fails
        mock_memory = MagicMock()
        mock_neo4j = AsyncMock()
        mock_neo4j.create_edge_relationship = AsyncMock(
            side_effect=ConnectionError("Neo4j down")
        )
        mock_memory.neo4j = mock_neo4j
        service._memory_client = mock_memory

        result = await service._sync_edge_to_neo4j(
            canvas_path="test.canvas",
            edge_id="edge-001",
            from_node_id="node-a",
            to_node_id="node-b",
        )

        assert result is None  # Failed
        assert get_edge_sync_failures() >= 1

    @pytest.mark.asyncio
    async def test_edge_sync_failure_writes_dead_letter(self, tmp_path):
        """When Neo4j sync fails, a dead-letter entry is written."""
        from app.services.canvas_service import CanvasService

        service = CanvasService(canvas_base_path="/tmp/test")
        mock_memory = MagicMock()
        mock_neo4j = AsyncMock()
        mock_neo4j.create_edge_relationship = AsyncMock(
            side_effect=ConnectionError("refused")
        )
        mock_memory.neo4j = mock_neo4j
        service._memory_client = mock_memory

        dl_path = tmp_path / "failed_edge_syncs.jsonl"
        with patch(
            "app.services.canvas_service.EDGE_SYNC_DEAD_LETTER_PATH", dl_path
        ):
            await service._sync_edge_to_neo4j(
                canvas_path="数学.canvas",
                edge_id="edge-002",
                from_node_id="n1",
                to_node_id="n2",
            )

        assert dl_path.exists()
        entry = json.loads(dl_path.read_text(encoding="utf-8").strip())
        assert entry["edge_id"] == "edge-002"
        assert entry["type"] == "edge_sync"

    @pytest.mark.asyncio
    async def test_edge_sync_failure_logs_warning(self, caplog):
        """WARNING log includes edge_id, canvas, error, total_failures (AC-36.12.4)."""
        from app.services.canvas_service import CanvasService

        service = CanvasService(canvas_base_path="/tmp/test")
        mock_memory = MagicMock()
        mock_neo4j = AsyncMock()
        mock_neo4j.create_edge_relationship = AsyncMock(
            side_effect=ConnectionError("connection refused")
        )
        mock_memory.neo4j = mock_neo4j
        service._memory_client = mock_memory

        with caplog.at_level(logging.WARNING):
            await service._sync_edge_to_neo4j(
                canvas_path="test.canvas",
                edge_id="edge-log-test",
                from_node_id="a",
                to_node_id="b",
            )

        warning_msgs = [r.message for r in caplog.records if r.levelno >= logging.WARNING]
        combined = " ".join(warning_msgs)
        assert "edge-log-test" in combined
        assert "test.canvas" in combined
        assert "total_failures" in combined


# ============================================================================
# AC-36.12.5: Dual-Write Failure in MemoryService Integration
# ============================================================================


class TestMemoryServiceDualWriteFailure:
    """Test that dual-write failures increment counter + write dead-letter."""

    @pytest.mark.asyncio
    async def test_dual_write_timeout_increments_counter(self):
        """When dual-write times out, dual_write_failures counter increments."""
        from app.services.memory_service import MemoryService

        mock_neo4j = MagicMock()
        mock_neo4j.initialize = AsyncMock()
        mock_learning = MagicMock()

        async def slow_write(*args, **kwargs):
            await simulate_async_delay(10)  # Will timeout

        mock_learning.add_learning_episode = slow_write

        service = MemoryService(
            neo4j_client=mock_neo4j,
            learning_memory_client=mock_learning,
        )

        await service._write_to_graphiti_json(
            episode_id="ep-timeout",
            canvas_name="test.canvas",
            node_id="n1",
            concept="测试概念",
        )

        assert get_dual_write_failures() >= 1

    @pytest.mark.asyncio
    async def test_dual_write_exception_increments_counter(self):
        """When dual-write raises exception, counter increments."""
        from app.services.memory_service import MemoryService

        mock_neo4j = MagicMock()
        mock_learning = MagicMock()
        mock_learning.add_learning_episode = AsyncMock(
            side_effect=RuntimeError("disk full")
        )

        service = MemoryService(
            neo4j_client=mock_neo4j,
            learning_memory_client=mock_learning,
        )

        await service._write_to_graphiti_json(
            episode_id="ep-error",
            canvas_name="test.canvas",
            node_id="n1",
            concept="概念",
        )

        assert get_dual_write_failures() >= 1

    @pytest.mark.asyncio
    async def test_dual_write_retry_failure_writes_dead_letter(self, tmp_path):
        """When _write_to_graphiti_json_with_retry exhausts retries, dead-letter is written."""
        from app.services.memory_service import MemoryService

        mock_neo4j = MagicMock()
        mock_learning = MagicMock()
        mock_learning._initialized = False
        mock_learning.add_learning_episode = AsyncMock(
            side_effect=RuntimeError("persistent error")
        )

        service = MemoryService(
            neo4j_client=mock_neo4j,
            learning_memory_client=mock_learning,
        )

        dl_path = tmp_path / "failed_dual_writes.jsonl"
        with patch(
            "app.services.memory_service.DUAL_WRITE_DEAD_LETTER_PATH", dl_path
        ), patch(
            "app.services.memory_service.GRAPHITI_RETRY_BACKOFF_BASE", 0.01
        ):
            result = await service._write_to_graphiti_json_with_retry(
                episode_id="ep-retry-fail",
                canvas_name="test.canvas",
                node_id="n1",
                concept="概念",
                max_retries=1,
            )

        assert result is False
        assert dl_path.exists()
        entry = json.loads(dl_path.read_text(encoding="utf-8").strip())
        assert entry["episode_id"] == "ep-retry-fail"
        assert entry["retry_count"] == 2  # max_retries(1) + 1


# ============================================================================
# AC-36.12.6: Health Check Reflects Failure State
# ============================================================================


class TestHealthStorageReflectsFailures:
    """Test that /health/storage returns degraded when failures > 0."""

    def test_aggregate_status_healthy_when_no_failures(self):
        """Status is healthy when all backends ok and no failures."""
        from app.api.v1.endpoints.health import (
            StorageBackendStatus,
            _aggregate_storage_status,
        )

        backends = [
            StorageBackendStatus(name="neo4j", status="ok"),
            StorageBackendStatus(name="mcp", status="ok"),
            StorageBackendStatus(name="json", status="ok"),
        ]
        assert _aggregate_storage_status(backends, 0, 0) == "healthy"

    def test_aggregate_status_degraded_when_edge_sync_failures(self):
        """Status is degraded when edge_sync_failures > 0 (AC-36.12.6)."""
        from app.api.v1.endpoints.health import (
            StorageBackendStatus,
            _aggregate_storage_status,
        )

        backends = [
            StorageBackendStatus(name="neo4j", status="ok"),
            StorageBackendStatus(name="mcp", status="ok"),
            StorageBackendStatus(name="json", status="ok"),
        ]
        assert _aggregate_storage_status(backends, edge_sync_failures=3, dual_write_failures=0) == "degraded"

    def test_aggregate_status_degraded_when_dual_write_failures(self):
        """Status is degraded when dual_write_failures > 0 (AC-36.12.6)."""
        from app.api.v1.endpoints.health import (
            StorageBackendStatus,
            _aggregate_storage_status,
        )

        backends = [
            StorageBackendStatus(name="neo4j", status="ok"),
            StorageBackendStatus(name="mcp", status="ok"),
            StorageBackendStatus(name="json", status="ok"),
        ]
        assert _aggregate_storage_status(backends, 0, 5) == "degraded"

    def test_aggregate_status_unhealthy_overrides_failures(self):
        """Neo4j down = unhealthy regardless of failure counters."""
        from app.api.v1.endpoints.health import (
            StorageBackendStatus,
            _aggregate_storage_status,
        )

        backends = [
            StorageBackendStatus(name="neo4j", status="error"),
            StorageBackendStatus(name="mcp", status="ok"),
            StorageBackendStatus(name="json", status="ok"),
        ]
        assert _aggregate_storage_status(backends, 10, 10) == "unhealthy"

    def test_storage_health_response_has_failure_fields(self):
        """StorageHealthResponse includes edge_sync_failures and dual_write_failures."""
        from app.api.v1.endpoints.health import (
            LatencyMetrics,
            StorageHealthResponse,
        )

        resp = StorageHealthResponse(
            status="degraded",
            storage_backends=[],
            latency_metrics=LatencyMetrics(p95_ms=10.0, window_seconds=300),
            cached=False,
            timestamp="2026-02-10T12:00:00Z",
            edge_sync_failures=5,
            dual_write_failures=3,
        )
        assert resp.edge_sync_failures == 5
        assert resp.dual_write_failures == 3


# ============================================================================
# Counter Reset Tests
# ============================================================================


class TestResetCounters:
    """Test the POST /health/storage/reset-counters behavior."""

    def test_reset_returns_previous_values(self):
        """reset_counters returns previous values."""
        increment_edge_sync_failures()
        increment_edge_sync_failures()
        increment_dual_write_failures()
        prev = reset_counters()
        assert prev == {"edge_sync_failures": 2, "dual_write_failures": 1}

    def test_reset_zeroes_all_counters(self):
        """After reset, all counters are zero."""
        increment_edge_sync_failures()
        increment_dual_write_failures()
        reset_counters()
        assert get_edge_sync_failures() == 0
        assert get_dual_write_failures() == 0
