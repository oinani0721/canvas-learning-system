"""
Story 38.7 AC-2: Full Learning Flow Integration

Verifies: Canvas CRUD -> LanceDB index -> learning event -> score -> FSRS.

Split from test_story_38_7_e2e_integration.py for maintainability.
"""
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.agent_service import MEMORY_WRITE_TIMEOUT
from app.services.memory_service import MemoryService


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════


def _make_mock_neo4j(*, episodes=None, health_ok=True, fail_write=False):
    """Create a mock Neo4jClient with configurable behavior."""
    mock = AsyncMock()
    mock.initialize = AsyncMock()
    mock.health_check = AsyncMock(return_value=health_ok)
    mock.stats = {"initialized": True, "node_count": 10, "edge_count": 5, "episode_count": 3}
    mock.get_all_recent_episodes = AsyncMock(return_value=episodes or [])
    mock.get_learning_history = AsyncMock(return_value=[])
    if fail_write:
        mock.record_episode_to_neo4j = AsyncMock(side_effect=Exception("Neo4j connection refused"))
    else:
        mock.record_episode_to_neo4j = AsyncMock(return_value=True)
    return mock


def _make_mock_learning_memory():
    """Create a mock LearningMemoryClient."""
    mock = MagicMock()
    mock.add_memory = MagicMock()
    mock.save = MagicMock()
    return mock


# ═══════════════════════════════════════════════════════════════════════════════
# AC-2: Full Learning Flow Integration
# ═══════════════════════════════════════════════════════════════════════════════


class TestAC2FullLearningFlow:
    """AC-2: Canvas CRUD -> LanceDB index -> learning event -> score -> FSRS."""

    @pytest.mark.asyncio
    async def test_canvas_add_node_triggers_lancedb_index(self, tmp_path):
        """
        [P0] Story 38.1 AC-1: CanvasService.add_node() calls
        _trigger_lancedb_index() which calls schedule_index().
        """
        from app.services.canvas_service import CanvasService

        canvas_dir = tmp_path / "canvases"
        canvas_dir.mkdir()
        canvas_file = canvas_dir / "test.canvas"
        canvas_file.write_text(
            json.dumps({"nodes": [], "edges": []}),
            encoding="utf-8"
        )

        svc = CanvasService(
            canvas_base_path=str(canvas_dir),
            memory_client=None
        )

        with patch.object(svc, "_trigger_lancedb_index") as mock_idx:
            await svc.add_node("test", {
                "id": "node-1",
                "type": "text",
                "text": "Test concept",
                "x": 0, "y": 0
            })
            mock_idx.assert_called_once_with("test")

    @pytest.mark.asyncio
    async def test_canvas_update_node_triggers_lancedb_index(self, tmp_path):
        """
        [P0] Story 38.1 AC-1: CanvasService.update_node() also triggers
        LanceDB auto-indexing.
        """
        from app.services.canvas_service import CanvasService

        canvas_dir = tmp_path / "canvases"
        canvas_dir.mkdir()
        canvas_file = canvas_dir / "test.canvas"
        canvas_file.write_text(
            json.dumps({"nodes": [{"id": "n1", "type": "text", "text": "Old", "x": 0, "y": 0}], "edges": []}),
            encoding="utf-8"
        )

        svc = CanvasService(canvas_base_path=str(canvas_dir), memory_client=None)

        with patch.object(svc, "_trigger_lancedb_index") as mock_idx:
            await svc.update_node("test", "n1", {"text": "Updated"})
            mock_idx.assert_called_once_with("test")

    @pytest.mark.asyncio
    async def test_lancedb_schedule_index_creates_debounced_task(self):
        """
        [P0] Story 38.1 AC-1: schedule_index() creates an asyncio task
        that is stored in _pending_tasks.
        """
        from app.services.lancedb_index_service import LanceDBIndexService

        svc = LanceDBIndexService()

        with patch.object(svc, "_debounced_index", new_callable=AsyncMock) as mock_debounce:
            svc.schedule_index("test-canvas", "/tmp/canvases")
            assert "test-canvas" in svc._pending_tasks
            # Cleanup: cancel the created task
            svc._pending_tasks["test-canvas"].cancel()

    @pytest.mark.asyncio
    async def test_learning_event_appended_to_episodes(self):
        """
        [P0] Story 38.2: record_learning_event appends to self._episodes.
        """
        neo4j = _make_mock_neo4j()
        learning_mem = _make_mock_learning_memory()

        ms = MemoryService(neo4j_client=neo4j, learning_memory_client=learning_mem)
        await ms.initialize()

        await ms.record_learning_event(
            user_id="user1",
            canvas_path="test-canvas",
            node_id="n1",
            concept="Python",
            agent_type="test",
            score=90,
        )

        assert len(ms._episodes) > 0
        last = ms._episodes[-1]
        assert last.get("concept") == "Python" or last.get("node_id") == "n1"

    def test_memory_write_timeout_is_at_least_10s(self):
        """
        [P0] Story 38.6 AC-1: MEMORY_WRITE_TIMEOUT >= 10s.
        Cross-verify from Story 38.7 integration perspective.
        """
        assert MEMORY_WRITE_TIMEOUT >= 10.0

    @pytest.mark.asyncio
    async def test_fsrs_get_state_returns_real_data_after_card_creation(self):
        """
        [P0] Story 38.3 AC-4: After card creation, get_fsrs_state()
        returns {found: True} with real FSRS data.
        """
        from app.services.review_service import ReviewService, FSRS_AVAILABLE

        if not FSRS_AVAILABLE:
            pytest.skip("py-fsrs not installed")

        canvas_svc = MagicMock()
        task_mgr = MagicMock()
        rs = ReviewService(canvas_service=canvas_svc, task_manager=task_mgr)

        card_json = json.dumps({
            "due": datetime.now().isoformat(),
            "stability": 1.0,
            "difficulty": 5.0,
            "state": 1,
            "reps": 1,
            "lapses": 0,
            "last_review": datetime.now().isoformat(),
        })
        rs._card_states["test-concept"] = card_json

        result = await rs.get_fsrs_state("test-concept")
        assert result is not None
        assert result.get("found") is True
        assert "stability" in result
        assert "difficulty" in result

    @pytest.mark.asyncio
    async def test_fsrs_get_state_returns_not_initialized_when_no_manager(self):
        """
        [P1] Story 38.3 AC-1: When _fsrs_manager is None,
        get_fsrs_state returns {found: False, reason: "fsrs_not_initialized"}.
        """
        from app.services.review_service import ReviewService

        with patch("app.services.review_service.FSRS_AVAILABLE", False), \
             patch("app.services.review_service.FSRSManager", None):
            canvas_svc = MagicMock()
            task_mgr = MagicMock()
            rs = ReviewService(canvas_service=canvas_svc, task_manager=task_mgr)

            result = await rs.get_fsrs_state("test-concept")
            assert result is not None
            assert result.get("found") is False
            assert "not_initialized" in result.get("reason", "")
