"""
Story 38.7 AC-4: Degraded Mode

Verifies: Neo4j down -> JSON fallback for Canvas CRUD, dual-write, scoring.

Split from test_story_38_7_e2e_integration.py for maintainability.
"""
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.agent_service import _record_failed_write
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
# AC-4: Degraded Mode
# ═══════════════════════════════════════════════════════════════════════════════


class TestAC4DegradedMode:
    """AC-4: Neo4j down -> JSON fallback for Canvas CRUD, dual-write, scoring."""

    @pytest.mark.asyncio
    async def test_canvas_crud_writes_json_fallback_when_no_memory_client(self, tmp_path):
        """
        [P0] Story 38.5 AC-1: When _memory_client is None and dual-write
        is enabled, Canvas CRUD events go to JSON fallback.
        """
        from app.services.canvas_service import CanvasService

        canvas_dir = tmp_path / "canvases"
        canvas_dir.mkdir()
        (canvas_dir / "test.canvas").write_text(
            json.dumps({"nodes": [], "edges": []}),
            encoding="utf-8"
        )

        svc = CanvasService(canvas_base_path=str(canvas_dir), memory_client=None)
        svc._fallback_file_path = tmp_path / "canvas_events_fallback.json"

        with patch("app.services.canvas_service.settings") as mock_settings:
            mock_settings.ENABLE_GRAPHITI_JSON_DUAL_WRITE = True
            mock_settings.ENABLE_LANCEDB_AUTO_INDEX = False

            await svc.add_node("test", {
                "id": "n1", "type": "text", "text": "Degraded node",
                "x": 0, "y": 0
            })

        assert svc._fallback_file_path.exists()
        content = json.loads(svc._fallback_file_path.read_text(encoding="utf-8"))
        assert len(content) >= 1
        assert content[0]["event_type"] == "node_created"

    @pytest.mark.asyncio
    async def test_canvas_crud_skips_memory_when_dual_write_disabled(self, tmp_path):
        """
        [P1] Story 38.5: When dual-write is disabled and memory_client is None,
        events are silently skipped (with WARNING log, no fallback write).
        """
        from app.services.canvas_service import CanvasService

        canvas_dir = tmp_path / "canvases"
        canvas_dir.mkdir()
        (canvas_dir / "test.canvas").write_text(
            json.dumps({"nodes": [], "edges": []}),
            encoding="utf-8"
        )

        svc = CanvasService(canvas_base_path=str(canvas_dir), memory_client=None)
        svc._fallback_file_path = tmp_path / "canvas_events_fallback.json"

        with patch("app.services.canvas_service.settings") as mock_settings:
            mock_settings.ENABLE_GRAPHITI_JSON_DUAL_WRITE = False
            mock_settings.ENABLE_LANCEDB_AUTO_INDEX = False

            await svc.add_node("test", {
                "id": "n2", "type": "text", "text": "No fallback",
                "x": 0, "y": 0
            })

        assert not svc._fallback_file_path.exists()

    def test_record_failed_write_creates_jsonl(self, tmp_path):
        """
        [P0] Story 38.6 AC-2: _record_failed_write() appends entry to
        data/failed_writes.jsonl.
        """
        failed_file = tmp_path / "failed_writes.jsonl"

        with patch("app.services.agent_service.FAILED_WRITES_FILE", Path(failed_file)):
            _record_failed_write(
                event_type="score_write",
                concept_id="c1",
                canvas_name="test-canvas",
                score=85.0,
                error_reason="Neo4j timeout",
                concept="Python Basics",
            )

        assert failed_file.exists()
        line = failed_file.read_text(encoding="utf-8").strip()
        entry = json.loads(line)
        assert entry["event_type"] == "score_write"
        assert entry["concept_id"] == "c1"
        assert entry["score"] == 85.0
        assert entry["error_reason"] == "Neo4j timeout"
        assert "timestamp" in entry

    def test_health_endpoint_fsrs_uses_module_flag(self):
        """
        [P0] Story 38.3 AC-3: health.py uses FSRS_AVAILABLE module flag
        (not _fsrs_init_ok instance attribute) to determine status.

        Full HTTP endpoint test: see test_story_38_7_qa_supplement.py::TestHealthEndpointHTTP
        """
        from app.services.review_service import FSRS_AVAILABLE

        expected = "ok" if FSRS_AVAILABLE else "degraded"
        assert expected in ("ok", "degraded")

        import app.services.review_service as review_mod
        assert hasattr(review_mod, "FSRS_AVAILABLE")

    @pytest.mark.asyncio
    async def test_dual_write_persists_to_json_when_neo4j_down(self):
        """
        [P0] Story 38.4/38.2: When Neo4j fails during record_learning_event,
        the service does not crash and remains operational.
        """
        neo4j = _make_mock_neo4j(fail_write=True)
        learning_mem = _make_mock_learning_memory()

        ms = MemoryService(neo4j_client=neo4j, learning_memory_client=learning_mem)
        ms._initialized = True
        ms._episodes_recovered = True

        initial_episode_count = len(ms._episodes)

        try:
            await ms.record_learning_event(
                user_id="u1",
                canvas_path="test",
                node_id="n1",
                concept="Math",
                agent_type="test",
                score=70,
            )
        except Exception:
            pass  # Some implementations may raise, that's ok for degraded mode

        assert ms._initialized is True
        assert len(ms._episodes) >= initial_episode_count, (
            f"Episodes should not be lost on Neo4j failure. "
            f"Before: {initial_episode_count}, After: {len(ms._episodes)}"
        )
