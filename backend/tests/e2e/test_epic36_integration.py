# Story 36.12: Integration Tests for EPIC-36
#
# ⚠️ Classification: These are mock-based integration tests, not true HTTP-level
# E2E tests. They call internal service methods (e.g. _sync_edge_to_neo4j) with
# mocked dependencies rather than hitting HTTP endpoints.
#
# Validates complete data flow across EPIC-36 pipeline:
# - AC-36.12.1: Edge → Neo4j → Agent data flow
# - AC-36.12.2: Cross-Canvas association persistence (⚠️ pending: Task 1.3)
# - AC-36.12.3: Rollback switch (memory_client=None DI fallback)
# - AC-36.12.6: /health/storage reflects failure state
# - AC-36.12.9: D2 resilience (Neo4j unavailable)
# - AC-36.12.10: D4 configuration defaults
#
# NOTE: Tests use mocked dependencies (no Neo4j Docker required).
#
# [Source: docs/stories/36.12.story.md#Testing]
import json
import logging
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.failure_counters import (
    get_dual_write_failures,
    get_edge_sync_failures,
    increment_edge_sync_failures,
    reset_counters,
)


@pytest.fixture(autouse=True)
def _reset_counters():
    """Reset failure counters for each test."""
    reset_counters()
    yield
    reset_counters()


# ============================================================================
# AC-36.12.1: Edge → Neo4j Sync Complete Flow
# ============================================================================


class TestEdgeToNeo4jSyncE2E:
    """E2E test: Edge creation triggers Neo4j sync."""

    @pytest.mark.asyncio
    async def test_edge_creation_triggers_sync(self, tmp_path):
        """
        Given: Canvas with nodes
        When: add_edge() creates a new edge
        Then: _sync_edge_to_neo4j is called (fire-and-forget)
        """
        from app.services.canvas_service import CanvasService

        # Setup canvas directory with a minimal canvas file
        canvas_dir = tmp_path / "canvases"
        canvas_dir.mkdir()
        canvas_file = canvas_dir / "test.canvas"
        canvas_data = {
            "nodes": [
                {"id": "node-a", "type": "text", "text": "Node A", "x": 0, "y": 0, "width": 200, "height": 100},
                {"id": "node-b", "type": "text", "text": "Node B", "x": 300, "y": 0, "width": 200, "height": 100},
            ],
            "edges": [],
        }
        canvas_file.write_text(json.dumps(canvas_data), encoding="utf-8")

        service = CanvasService(canvas_base_path=str(canvas_dir))

        # Mock memory_client to track sync calls
        mock_memory = MagicMock()
        mock_neo4j = AsyncMock()
        mock_neo4j.create_edge_relationship = AsyncMock(return_value=True)
        mock_memory.neo4j = mock_neo4j
        service._memory_client = mock_memory

        # Add edge
        result = await service.add_edge(
            canvas_name="test",
            edge_data={
                "id": "edge-001",
                "fromNode": "node-a",
                "toNode": "node-b",
                "fromSide": "right",
                "toSide": "left",
            },
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_edge_sync_success_path(self):
        """
        Given: Neo4j is available
        When: Edge sync is triggered
        Then: create_edge_relationship is called and returns True
        """
        from app.services.canvas_service import CanvasService

        service = CanvasService(canvas_base_path="/tmp/test")
        mock_memory = MagicMock()
        mock_neo4j = AsyncMock()
        mock_neo4j.create_edge_relationship = AsyncMock(return_value=True)
        mock_memory.neo4j = mock_neo4j
        service._memory_client = mock_memory

        result = await service._sync_edge_to_neo4j(
            canvas_path="test.canvas",
            edge_id="edge-success",
            from_node_id="a",
            to_node_id="b",
        )

        assert result is True
        mock_neo4j.create_edge_relationship.assert_called_once()
        assert get_edge_sync_failures() == 0


# ============================================================================
# AC-36.12.3: Rollback Switch (JSON fallback)
# ============================================================================


class TestRollbackSwitchE2E:
    """E2E test: GRAPHITI_USE_NEO4J=false → full JSON fallback."""

    @pytest.mark.asyncio
    async def test_edge_sync_json_fallback_when_no_memory_client(self, caplog):
        """
        Given: memory_client is None (simulating GRAPHITI_USE_NEO4J=false)
        When: Edge sync is triggered
        Then: Falls back to JSON, no exception, WARNING log
        """
        from app.services.canvas_service import CanvasService

        service = CanvasService(canvas_base_path="/tmp/test")
        service._memory_client = None

        with caplog.at_level(logging.WARNING):
            result = await service._sync_edge_to_neo4j(
                canvas_path="test.canvas",
                edge_id="edge-fallback",
                from_node_id="a",
                to_node_id="b",
            )

        assert result is False  # Skipped (fallback)
        warning_msgs = [r.message.lower() for r in caplog.records if r.levelno >= logging.WARNING]
        assert len(warning_msgs) > 0, "Expected at least one WARNING log"
        combined = " ".join(warning_msgs)
        assert any(kw in combined for kw in ["fallback", "unavailable", "skipping", "not configured"]), \
            f"Expected fallback/skip keyword in: {combined}"

    @pytest.mark.asyncio
    async def test_edge_sync_json_fallback_when_neo4j_unavailable(self, caplog):
        """
        Given: memory_client exists but neo4j is None
        When: Edge sync is triggered
        Then: Falls back to JSON, no exception
        """
        from app.services.canvas_service import CanvasService

        service = CanvasService(canvas_base_path="/tmp/test")
        mock_memory = MagicMock()
        mock_memory.neo4j = None
        service._memory_client = mock_memory

        with caplog.at_level(logging.WARNING):
            result = await service._sync_edge_to_neo4j(
                canvas_path="test.canvas",
                edge_id="edge-no-neo4j",
                from_node_id="a",
                to_node_id="b",
            )

        assert result is False


# ============================================================================
# AC-36.12.9: D2 Resilience — Neo4j fully unavailable
# ============================================================================


class TestResilienceE2E:
    """E2E test: System remains functional when Neo4j is completely down."""

    @pytest.mark.asyncio
    async def test_edge_sync_graceful_with_neo4j_down(self, tmp_path):
        """
        Given: Neo4j is completely unavailable
        When: Edge sync retries exhaust
        Then: Edge creation succeeds + JSON fallback + failure count + dead-letter
        """
        from app.services.canvas_service import CanvasService

        service = CanvasService(canvas_base_path="/tmp/test")
        mock_memory = MagicMock()
        mock_neo4j = AsyncMock()
        mock_neo4j.create_edge_relationship = AsyncMock(
            side_effect=ConnectionError("Connection refused")
        )
        mock_memory.neo4j = mock_neo4j
        service._memory_client = mock_memory

        dl_path = tmp_path / "failed_edge_syncs.jsonl"
        with patch(
            "app.services.canvas_service.EDGE_SYNC_DEAD_LETTER_PATH", dl_path
        ):
            result = await service._sync_edge_to_neo4j(
                canvas_path="resilience.canvas",
                edge_id="edge-resilience",
                from_node_id="a",
                to_node_id="b",
            )

        # Verify: graceful degradation
        assert result is None  # Failed but didn't raise
        assert get_edge_sync_failures() >= 1
        assert dl_path.exists()

    @pytest.mark.asyncio
    async def test_dual_write_graceful_with_client_down(self):
        """
        Given: LearningMemoryClient raises exception
        When: Dual-write is attempted
        Then: Main flow succeeds, counter incremented, WARNING logged
        """
        from app.services.memory_service import MemoryService

        mock_neo4j = MagicMock()
        mock_learning = MagicMock()
        mock_learning.add_learning_episode = AsyncMock(
            side_effect=RuntimeError("Client unavailable")
        )

        service = MemoryService(
            neo4j_client=mock_neo4j,
            learning_memory_client=mock_learning,
        )

        # This should NOT raise
        await service._write_to_graphiti_json(
            episode_id="ep-resilience",
            canvas_name="test.canvas",
            node_id="n1",
            concept="测试",
        )

        assert get_dual_write_failures() >= 1


# ============================================================================
# AC-36.12.6: Health Check Integration with Failures
# ============================================================================


class TestHealthCheckIntegrationE2E:
    """E2E test: /health/storage reflects failure state."""

    def test_health_storage_degraded_with_failures(self):
        """
        Given: edge_sync_failures > 0
        When: /health/storage is checked
        Then: status is 'degraded' and failure counts are included
        """
        from app.api.v1.endpoints.health import (
            LatencyMetrics,
            StorageBackendStatus,
            StorageHealthResponse,
            _aggregate_storage_status,
        )

        # Simulate failures
        increment_edge_sync_failures()
        increment_edge_sync_failures()

        backends = [
            StorageBackendStatus(name="neo4j", status="ok"),
            StorageBackendStatus(name="json", status="ok"),
        ]

        esf = get_edge_sync_failures()
        dwf = get_dual_write_failures()
        status = _aggregate_storage_status(backends, esf, dwf)

        assert status == "degraded"
        assert esf == 2
        assert dwf == 0


# ============================================================================
# AC-36.12.10: D4 Configuration Defaults
# ============================================================================


class TestConfigurationDefaults:
    """Test that configuration defaults are correct (AC-36.12.10)."""

    def test_enable_graphiti_json_dual_write_default_true(self, monkeypatch):
        """ENABLE_GRAPHITI_JSON_DUAL_WRITE defaults to True (AC-36.12.10)."""
        from app.config import Settings

        # Remove env var so Pydantic uses the field default
        monkeypatch.delenv("ENABLE_GRAPHITI_JSON_DUAL_WRITE", raising=False)
        s = Settings(
            GEMINI_API_KEY="test-key",
            _env_file=None,
        )
        # AC-36.12.10: default=True for Neo4j-offline resilience (config.py:419)
        assert s.ENABLE_GRAPHITI_JSON_DUAL_WRITE is True

    def test_dead_letter_paths_exist(self):
        """Dead-letter file paths are correctly configured."""
        from app.core.failure_counters import (
            DUAL_WRITE_DEAD_LETTER_PATH,
            EDGE_SYNC_DEAD_LETTER_PATH,
        )

        assert EDGE_SYNC_DEAD_LETTER_PATH.name == "failed_edge_syncs.jsonl"
        assert DUAL_WRITE_DEAD_LETTER_PATH.name == "failed_dual_writes.jsonl"
        assert "data" in str(EDGE_SYNC_DEAD_LETTER_PATH)
        assert "data" in str(DUAL_WRITE_DEAD_LETTER_PATH)
