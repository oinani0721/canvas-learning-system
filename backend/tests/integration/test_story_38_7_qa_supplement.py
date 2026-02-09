"""
Story 38.7 QA Supplement Tests — Fill gaps found by QA automate audit.

Gap 1: Health endpoint must be tested via HTTP (TestClient), not simulated logic
Gap 2: AC-4 degraded dual-write must verify actual data persistence
Gap 3: Health endpoint uses FSRS_AVAILABLE not _fsrs_init_ok — test real endpoint
Gap 4: Scoring write integration path (score → failed_writes.jsonl → recovery)
"""
import json
import pytest
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from app.config import Settings, get_settings
from app.main import app
from fastapi.testclient import TestClient


# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════════


def _test_settings():
    return Settings(
        PROJECT_NAME="Canvas Learning System API (QA Test)",
        VERSION="1.0.0-qa",
        DEBUG=True,
        LOG_LEVEL="DEBUG",
        CORS_ORIGINS="http://localhost:3000",
        CANVAS_BASE_PATH="./test_canvas",
    )


@pytest.fixture
def qa_client():
    """TestClient with overridden settings for QA tests."""
    app.dependency_overrides[get_settings] = _test_settings
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ═══════════════════════════════════════════════════════════════════════════════
# Gap 1: Health endpoint HTTP tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestHealthEndpointHTTP:
    """Test /health endpoint via actual HTTP requests."""

    def test_health_returns_200_and_status_healthy(self, qa_client):
        """
        [P0] AC-4/AC-5: GET /api/v1/health returns 200 with status=healthy.
        """
        resp = qa_client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert "app_name" in data
        assert "version" in data
        assert "timestamp" in data

    def test_health_includes_fsrs_component(self, qa_client):
        """
        [P0] Story 38.3 AC-3: /health response includes components.fsrs field.
        Actual endpoint checks FSRS_AVAILABLE module flag.
        """
        resp = qa_client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "components" in data
        assert data["components"] is not None
        assert "fsrs" in data["components"]
        # Value must be "ok" or "degraded"
        assert data["components"]["fsrs"] in ("ok", "degraded")

    def test_health_fsrs_ok_when_library_available(self, qa_client, monkeypatch):
        """
        [P0] Story 38.3: When py-fsrs is installed, /health shows fsrs: "ok".
        Patches FSRS flags to True to ensure deterministic assertion.
        """
        import app.services.review_service as review_mod

        monkeypatch.setattr(review_mod, "FSRS_AVAILABLE", True)
        monkeypatch.setattr(review_mod, "FSRS_RUNTIME_OK", True)
        resp = qa_client.get("/api/v1/health")
        data = resp.json()
        assert data["components"]["fsrs"] == "ok"

    def test_health_fsrs_degraded_when_library_unavailable(self, qa_client, monkeypatch):
        """
        [P0] Story 38.3 AC-3: /health shows fsrs: "degraded" when
        FSRS is unavailable.

        health.py uses FSRS_RUNTIME_OK (priority) then FSRS_AVAILABLE (fallback).
        Must patch both to simulate unavailable state.
        """
        import app.services.review_service as review_mod

        monkeypatch.setattr(review_mod, "FSRS_AVAILABLE", False)
        monkeypatch.setattr(review_mod, "FSRS_RUNTIME_OK", False)
        resp = qa_client.get("/api/v1/health")
        data = resp.json()
        assert data["components"]["fsrs"] == "degraded"


# ═══════════════════════════════════════════════════════════════════════════════
# Gap 2: Strengthened AC-4 degraded dual-write assertions
# ═══════════════════════════════════════════════════════════════════════════════


class TestDegradedDualWriteStrengthened:
    """Stronger assertions for AC-4 degraded mode data persistence."""

    @pytest.mark.asyncio
    async def test_record_learning_event_raises_on_neo4j_failure_state_consistent(self):
        """
        [P0] Story 38.4/38.2 AC-4 (strengthened): When Neo4j
        create_learning_relationship fails, record_learning_event raises
        and service state remains consistent — no partial writes.

        Note: record_learning_event → _create_neo4j_learning_relationship
        → neo4j.create_learning_relationship (NOT record_episode_to_neo4j).
        """
        from app.services.memory_service import MemoryService

        neo4j = AsyncMock()
        neo4j.initialize = AsyncMock()
        neo4j.health_check = AsyncMock(return_value=True)
        neo4j.stats = {"initialized": True}
        neo4j.get_all_recent_episodes = AsyncMock(return_value=[])
        neo4j.get_learning_history = AsyncMock(return_value=[])
        # Mock the ACTUAL method called by record_learning_event
        neo4j.create_learning_relationship = AsyncMock(
            side_effect=Exception("Neo4j connection refused")
        )

        learning_mem = MagicMock()
        learning_mem.add_memory = MagicMock()
        learning_mem.save = MagicMock()

        ms = MemoryService(neo4j_client=neo4j, learning_memory_client=learning_mem)
        await ms.initialize()

        initial_count = len(ms._episodes)

        # Neo4j write fails → function raises → episode not appended
        with pytest.raises(Exception, match="Neo4j connection refused"):
            await ms.record_learning_event(
                user_id="u1",
                canvas_path="test-canvas",
                node_id="n1",
                concept="Math",
                agent_type="test",
                score=70,
            )

        # State consistency: episodes should not be corrupted
        assert len(ms._episodes) == initial_count, (
            "Episode count should stay the same when Neo4j write fails "
            "(episode append is after Neo4j call in the try block)"
        )

    @pytest.mark.asyncio
    async def test_canvas_crud_fallback_file_contains_correct_event_structure(self, tmp_path):
        """
        [P0] Story 38.5 AC-1 (strengthened): JSON fallback file contains
        properly structured event with all required fields.
        """
        from app.services.canvas_service import CanvasService

        canvas_dir = tmp_path / "canvases"
        canvas_dir.mkdir()
        (canvas_dir / "verify.canvas").write_text(
            json.dumps({"nodes": [], "edges": []}),
            encoding="utf-8"
        )

        svc = CanvasService(canvas_base_path=str(canvas_dir), memory_client=None)
        svc._fallback_file_path = tmp_path / "canvas_events_fallback.json"

        with patch("app.services.canvas_service.settings") as mock_settings:
            mock_settings.ENABLE_GRAPHITI_JSON_DUAL_WRITE = True
            mock_settings.ENABLE_LANCEDB_AUTO_INDEX = False

            await svc.add_node("verify", {
                "id": "qa-node", "type": "text", "text": "QA test",
                "x": 100, "y": 200
            })

        assert svc._fallback_file_path.exists()
        content = json.loads(svc._fallback_file_path.read_text(encoding="utf-8"))
        assert len(content) >= 1

        event = content[0]
        # Verify required fields exist
        assert "event_type" in event
        assert event["event_type"] == "node_created"
        assert "canvas_name" in event
        assert event["canvas_name"] == "verify"
        assert "timestamp" in event
        assert "node_data" in event or "node_id" in event


# ═══════════════════════════════════════════════════════════════════════════════
# Gap 3: Scoring write → failed_writes → recovery integration
# ═══════════════════════════════════════════════════════════════════════════════


class TestScoringWriteRecoveryFlow:
    """Test the full scoring write → failure → recovery pipeline."""

    def test_failed_write_contains_all_required_fields(self, tmp_path):
        """
        [P0] Story 38.6 AC-2 (strengthened): failed_writes.jsonl entry
        contains all fields needed for successful replay.
        """
        from app.services.agent_service import _record_failed_write

        failed_file = tmp_path / "failed_writes.jsonl"

        with patch("app.services.agent_service.FAILED_WRITES_FILE", Path(failed_file)):
            _record_failed_write(
                event_type="score_write",
                concept_id="qa-concept-1",
                canvas_name="qa-canvas",
                score=92.5,
                error_reason="Connection timeout after 15s",
                concept="Integration Testing",
                user_understanding="I think it's about testing modules together",
                agent_feedback="Good understanding of integration concepts",
            )

        assert failed_file.exists()
        lines = failed_file.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 1

        entry = json.loads(lines[0])
        # All required fields for replay
        assert entry["event_type"] == "score_write"
        assert entry["concept_id"] == "qa-concept-1"
        assert entry["canvas_name"] == "qa-canvas"
        assert entry["score"] == 92.5
        assert entry["error_reason"] == "Connection timeout after 15s"
        assert entry["concept"] == "Integration Testing"
        assert "timestamp" in entry
        # Optional fields that help replay
        assert entry.get("user_understanding") == "I think it's about testing modules together"
        assert entry.get("agent_feedback") == "Good understanding of integration concepts"

    def test_multiple_failed_writes_are_appended_not_overwritten(self, tmp_path):
        """
        [P0] Story 38.6 AC-2: Multiple failures append to the same file.
        """
        from app.services.agent_service import _record_failed_write

        failed_file = tmp_path / "failed_writes.jsonl"

        with patch("app.services.agent_service.FAILED_WRITES_FILE", Path(failed_file)):
            for i in range(3):
                _record_failed_write(
                    event_type="score_write",
                    concept_id=f"c{i}",
                    canvas_name="multi-test",
                    score=float(70 + i * 10),
                    error_reason="timeout",
                    concept=f"Concept {i}",
                )

        lines = failed_file.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 3

        concepts = [json.loads(line)["concept_id"] for line in lines]
        assert concepts == ["c0", "c1", "c2"]


# ═══════════════════════════════════════════════════════════════════════════════
# Gap 4: Config defaults cross-validation
# ═══════════════════════════════════════════════════════════════════════════════


class TestConfigDefaultsSafety:
    """Additional config default safety checks."""

    def test_memory_write_timeout_field_default(self):
        """
        [P0] Story 38.6: MEMORY_WRITE_TIMEOUT constant is safe (>= 10s).
        Validates at import level, not runtime.
        """
        from app.services.agent_service import MEMORY_WRITE_TIMEOUT
        assert isinstance(MEMORY_WRITE_TIMEOUT, (int, float))
        assert MEMORY_WRITE_TIMEOUT >= 10.0, (
            f"MEMORY_WRITE_TIMEOUT={MEMORY_WRITE_TIMEOUT} is too low, must be >= 10s"
        )

    def test_enable_lancedb_auto_index_field_default(self):
        """
        [P0] Story 38.1: ENABLE_LANCEDB_AUTO_INDEX defaults to True.
        """
        field_info = Settings.model_fields["ENABLE_LANCEDB_AUTO_INDEX"]
        assert field_info.default is True

    def test_verification_ai_timeout_is_sane(self):
        """
        [P1] VERIFICATION_AI_TIMEOUT must be >= 5s for Gemini API calls.
        Fixed: config.py default changed from 0.5s to 15.0s.
        """
        field_info = Settings.model_fields.get("VERIFICATION_AI_TIMEOUT")
        assert field_info is not None, "VERIFICATION_AI_TIMEOUT field should exist in Settings"
        assert field_info.default >= 5.0, (
            f"VERIFICATION_AI_TIMEOUT default={field_info.default}s is too low (should be >= 5s)"
        )
