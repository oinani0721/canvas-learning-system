"""
Story 38.7 AC-5: Recovery + Cross-Story Data Flow Verification

AC-5: Failed write replay, LanceDB pending replay, health restored.
Cross-Story: Verify data flows correctly across Story boundaries.

Split from test_story_38_7_e2e_integration.py for maintainability.
"""
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.config import Settings
from app.services.agent_service import MEMORY_WRITE_TIMEOUT
from app.services.memory_service import (
    FAILED_WRITES_FILE,
    MemoryService,
)

from tests.integration.conftest import make_mock_neo4j, make_mock_learning_memory


# ═══════════════════════════════════════════════════════════════════════════════
# AC-5: Recovery
# ═══════════════════════════════════════════════════════════════════════════════


class TestAC5Recovery:
    """AC-5: Failed write replay, LanceDB pending replay, health restored."""

    @pytest.mark.asyncio
    async def test_recover_failed_writes_replays_entries(self, tmp_path):
        """
        [P0] Story 38.6 AC-3: recover_failed_writes() reads
        data/failed_writes.jsonl and replays entries.
        """
        failed_file = tmp_path / "failed_writes.jsonl"
        entry = {
            "timestamp": "2026-02-07T10:00:00",
            "event_type": "score_write",
            "concept_id": "c1",
            "canvas_name": "math-canvas",
            "score": 85.0,
            "error_reason": "timeout",
            "concept": "Calculus",
            "user_understanding": "I think it's about limits",
            "agent_feedback": "Correct",
        }
        failed_file.write_text(json.dumps(entry) + "\n", encoding="utf-8")

        neo4j = make_mock_neo4j()
        learning_mem = make_mock_learning_memory()
        ms = MemoryService(neo4j_client=neo4j, learning_memory_client=learning_mem)
        ms._initialized = True
        ms._episodes_recovered = True

        with patch.object(ms, "_write_to_graphiti_json_with_retry", new_callable=AsyncMock, return_value=True):
            with patch("app.services.memory_service.FAILED_WRITES_FILE", Path(failed_file)):
                result = await ms.recover_failed_writes()

        assert result["recovered"] >= 1

    @pytest.mark.asyncio
    async def test_recover_failed_writes_keeps_still_pending(self, tmp_path):
        """
        [P1] Story 38.6 AC-3: Entries that fail replay remain in the file.
        """
        failed_file = tmp_path / "failed_writes.jsonl"
        entries = [
            {"timestamp": "2026-02-07T10:00:00", "event_type": "score_write",
             "concept_id": "c1", "canvas_name": "math", "score": 85.0,
             "error_reason": "timeout", "concept": "Calc",
             "user_understanding": None, "agent_feedback": None},
            {"timestamp": "2026-02-07T10:01:00", "event_type": "score_write",
             "concept_id": "c2", "canvas_name": "physics", "score": 70.0,
             "error_reason": "timeout", "concept": "Force",
             "user_understanding": None, "agent_feedback": None},
        ]
        failed_file.write_text(
            "\n".join(json.dumps(e) for e in entries) + "\n",
            encoding="utf-8"
        )

        neo4j = make_mock_neo4j()
        learning_mem = make_mock_learning_memory()
        ms = MemoryService(neo4j_client=neo4j, learning_memory_client=learning_mem)
        ms._initialized = True
        ms._episodes_recovered = True

        with patch.object(
            ms, "_write_to_graphiti_json_with_retry",
            new_callable=AsyncMock,
            side_effect=Exception("Still failing")
        ):
            with patch("app.services.memory_service.FAILED_WRITES_FILE", Path(failed_file)):
                result = await ms.recover_failed_writes()

        assert result["pending"] == 2

    @pytest.mark.asyncio
    async def test_lancedb_recover_pending_with_partial_failure(self, tmp_path):
        """
        [P0] Story 38.1 AC-3: recover_pending() handles partial failure —
        successfully recovered entries are removed, failed entries persist.
        """
        from app.services.lancedb_index_service import LanceDBIndexService

        svc = LanceDBIndexService()
        pending_file = tmp_path / "lancedb_pending_index.jsonl"
        entries = [
            json.dumps({"canvas_name": "ok-canvas", "timestamp": "2026-02-07T10:00:00"}),
            json.dumps({"canvas_name": "fail-canvas", "timestamp": "2026-02-07T10:01:00"}),
        ]
        pending_file.write_text("\n".join(entries) + "\n", encoding="utf-8")
        svc._pending_file = pending_file

        call_count = 0

        async def mock_do_index(canvas_name, base_path):
            nonlocal call_count
            call_count += 1
            if canvas_name == "fail-canvas":
                raise Exception("Index failed")

        svc._do_index = mock_do_index

        result = await svc.recover_pending(str(tmp_path))
        assert result["recovered"] == 1
        assert result["pending"] == 1

        assert pending_file.exists()
        remaining = pending_file.read_text(encoding="utf-8").strip()
        assert "fail-canvas" in remaining

    @pytest.mark.asyncio
    async def test_load_failed_scores_merges_into_learning_history(self):
        """
        [P0] Story 38.6 AC-4: load_failed_scores() returns entries
        from failed_writes.jsonl for merging into learning history.
        """
        neo4j = make_mock_neo4j()
        learning_mem = make_mock_learning_memory()
        ms = MemoryService(neo4j_client=neo4j, learning_memory_client=learning_mem)
        ms._initialized = True

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False, encoding="utf-8"
        ) as f:
            entry = {
                "timestamp": "2026-02-07T10:00:00",
                "event_type": "score_write",
                "concept_id": "c1",
                "canvas_name": "test",
                "score": 85.0,
                "error_reason": "timeout",
                "concept": "Python",
                "user_understanding": "Decorators",
                "agent_feedback": "Good",
            }
            f.write(json.dumps(entry) + "\n")
            f.flush()
            tmp_file = f.name

        try:
            with patch("app.services.memory_service.FAILED_WRITES_FILE", Path(tmp_file)):
                scores = ms.load_failed_scores()
            assert len(scores) >= 1
            assert scores[0].get("source") == "fallback"
            assert scores[0].get("concept") == "Python"
        finally:
            Path(tmp_file).unlink(missing_ok=True)

    def test_health_check_response_model_has_components_field(self):
        """
        [P0] AC-5 cross-check: HealthCheckResponse model supports
        components dict for FSRS and other status reporting.
        """
        from app.models.schemas import HealthCheckResponse

        resp = HealthCheckResponse(
            status="healthy",
            app_name="test",
            version="1.0.0",
            timestamp=datetime.now(timezone.utc),
            components={"fsrs": "ok"},
        )
        assert resp.components["fsrs"] == "ok"

        resp2 = HealthCheckResponse(
            status="healthy",
            app_name="test",
            version="1.0.0",
            timestamp=datetime.now(timezone.utc),
            components={"fsrs": "degraded"},
        )
        assert resp2.components["fsrs"] == "degraded"


# ═══════════════════════════════════════════════════════════════════════════════
# Cross-Story Integration: Data Flow Verification
# ═══════════════════════════════════════════════════════════════════════════════


class TestCrossStoryDataFlow:
    """Verify data flows correctly across Story boundaries."""

    @pytest.mark.asyncio
    async def test_full_flow_canvas_to_history(self, tmp_path):
        """
        [P0] End-to-end: Canvas node create -> memory event trigger ->
        episode cache -> learning history query.
        """
        from app.services.canvas_service import CanvasService

        canvas_dir = tmp_path / "canvases"
        canvas_dir.mkdir()
        (canvas_dir / "flow-test.canvas").write_text(
            json.dumps({"nodes": [], "edges": []}),
            encoding="utf-8"
        )

        neo4j = make_mock_neo4j()
        learning_mem = make_mock_learning_memory()
        ms = MemoryService(neo4j_client=neo4j, learning_memory_client=learning_mem)
        ms._initialized = True
        ms._episodes_recovered = True

        canvas_svc = CanvasService(
            canvas_base_path=str(canvas_dir),
            memory_client=None
        )
        canvas_svc._fallback_file_path = tmp_path / "fallback.json"

        with patch("app.services.canvas_service.settings") as mock_settings:
            mock_settings.ENABLE_GRAPHITI_JSON_DUAL_WRITE = True
            mock_settings.ENABLE_LANCEDB_AUTO_INDEX = False

            result = await canvas_svc.add_node("flow-test", {
                "id": "flow-n1", "type": "text", "text": "Integration Test",
                "x": 0, "y": 0
            })
            assert result["id"] == "flow-n1"

        assert canvas_svc._fallback_file_path.exists()

        await ms.record_learning_event(
            user_id="user1",
            canvas_path="flow-test",
            node_id="flow-n1",
            concept="Integration Concept",
            agent_type="test",
            score=92,
        )

        matching = [e for e in ms._episodes if e.get("node_id") == "flow-n1"]
        assert len(matching) == 1, f"Expected exactly 1 episode with node_id=flow-n1, got {len(matching)}"
        assert matching[0]["concept"] == "Integration Concept"

    @pytest.mark.asyncio
    async def test_timeout_constants_are_aligned_across_services(self):
        """
        [P0] Cross-Story 38.1/38.6: Verify timeout constants are
        properly aligned across services.
        """
        from app.services.memory_service import (
            GRAPHITI_JSON_WRITE_TIMEOUT,
            GRAPHITI_RETRY_BACKOFF_BASE,
        )

        max_retries = 2  # 3 total attempts
        inner_total = (
            (max_retries + 1) * GRAPHITI_JSON_WRITE_TIMEOUT
            + sum(GRAPHITI_RETRY_BACKOFF_BASE * (2 ** i) for i in range(max_retries))
        )

        assert MEMORY_WRITE_TIMEOUT > inner_total, (
            f"Outer ({MEMORY_WRITE_TIMEOUT}s) must exceed inner total ({inner_total}s)"
        )

    def test_all_config_defaults_are_safe(self):
        """
        [P0] Story 38.4: All infrastructure config flags have safe defaults.
        Verify Field definitions directly, bypassing .env overrides.
        """
        fields = Settings.model_fields

        assert fields["ENABLE_GRAPHITI_JSON_DUAL_WRITE"].default is True, (
            "ENABLE_GRAPHITI_JSON_DUAL_WRITE must default to True"
        )

        assert fields["ENABLE_LANCEDB_AUTO_INDEX"].default is True, (
            "ENABLE_LANCEDB_AUTO_INDEX must default to True"
        )

    def test_failed_writes_file_path_consistency(self):
        """
        [P1] Story 38.6: FAILED_WRITES_FILE is consistent between
        agent_service and memory_service.
        """
        from app.services.agent_service import FAILED_WRITES_FILE as AS_FILE
        from app.services.memory_service import FAILED_WRITES_FILE as MS_FILE

        assert Path(AS_FILE).name == Path(MS_FILE).name
