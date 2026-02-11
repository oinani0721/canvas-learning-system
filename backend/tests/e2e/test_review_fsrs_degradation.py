# Canvas Learning System - E2E FSRS Degradation Tests
# Story 32.11: E2E 降级测试 + 并发安全验证
"""
End-to-end tests for FSRS→Ebbinghaus fallback degradation path.

Verifies that when USE_FSRS=False:
- PUT /record returns algorithm=ebbinghaus-fallback with 200
- GET /schedule returns 200 (empty or Ebbinghaus intervals)
- GET /fsrs-state/{id} returns found=false, reason=fsrs_not_initialized
- GET /health returns components.fsrs=degraded
- Ebbinghaus next_review timing is accurate (score→interval→next_review)

[Source: docs/stories/32.11.story.md]
[Source: _bmad-output/test-artifacts/epic-32-adversarial-comprehensive-20260210.md]
"""

from datetime import timedelta
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.main import app


# =============================================================================
# Degraded Settings Override
# =============================================================================

def _degraded_settings() -> Settings:
    """Settings with USE_FSRS=False to force Ebbinghaus fallback.

    AC-32.11.1: USE_FSRS=False triggers Ebbinghaus fallback path.
    """
    return Settings(
        PROJECT_NAME="Canvas Test (FSRS Degraded)",
        VERSION="1.0.0-test",
        USE_FSRS=False,
        CANVAS_BASE_PATH="./test_canvas",
    )


_DEGRADED = _degraded_settings()


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(autouse=True)
def _reset_review_singleton_and_fsrs_runtime():
    """Reset ReviewService singleton and FSRS_RUNTIME_OK before/after each test.

    Ensures each test starts with clean state:
    - No cached ReviewService singleton
    - FSRS_RUNTIME_OK reset to None (unset)
    """
    import app.services.review_service as rsmod

    rsmod.reset_review_service_singleton()
    original_runtime_ok = rsmod.FSRS_RUNTIME_OK
    rsmod.FSRS_RUNTIME_OK = None

    yield

    rsmod.reset_review_service_singleton()
    rsmod.FSRS_RUNTIME_OK = original_runtime_ok


@pytest.fixture(autouse=True)
def _override_settings_degraded():
    """Patch get_settings at module level so ALL code paths use USE_FSRS=False.

    FastAPI dependency_overrides only affects route handler DI.
    The ReviewService singleton factory calls get_settings() directly,
    so we must patch it at the source (app.config.get_settings).
    """
    with patch("app.config.get_settings", return_value=_DEGRADED):
        app.dependency_overrides[get_settings] = lambda: _DEGRADED
        yield
        app.dependency_overrides.pop(get_settings, None)


@pytest.fixture
def client():
    """Sync TestClient with degraded FSRS settings."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def isolate_card_states(tmp_path):
    """Isolate card states file to tmp_path."""
    tmp_file = tmp_path / "fsrs_card_states.json"
    with patch("app.services.review_service._CARD_STATES_FILE", tmp_file):
        yield tmp_file


# =============================================================================
# AC-32.11.1: E2E Ebbinghaus 降级测试
# =============================================================================

class TestEbbinghausFallbackE2E:
    """E2E: Full HTTP request → Ebbinghaus fallback response."""

    def test_record_review_uses_ebbinghaus(self, client, isolate_card_states):
        """T1.2: PUT /record with USE_FSRS=False returns ebbinghaus-fallback.

        AC-32.11.1: record returns algorithm=ebbinghaus-fallback + interval + next_review.
        Score 50 → rating 2 (Hard) → interval 3 days (Ebbinghaus fallback).
        """
        resp = client.put("/api/v1/review/record", json={
            "canvas_name": "test-degradation",
            "node_id": "e2e-concept-degraded",
            "score": 50,
        })
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["algorithm"] == "ebbinghaus-fallback", (
            f"Expected ebbinghaus-fallback, got {data.get('algorithm')}"
        )
        # AC-32.11.1: Verify interval_days is reasonable (score 40-59 → 3 days)
        assert data["new_interval"] == 3, (
            f"Expected new_interval=3 for score=50, got {data.get('new_interval')}"
        )
        # AC-32.11.1: Verify next_review_date is a future date
        from datetime import date as date_cls
        next_date = date_cls.fromisoformat(data["next_review_date"])
        assert next_date > date_cls.today(), (
            f"next_review_date {next_date} should be in the future"
        )

    def test_schedule_review_ebbinghaus_fallback(self, client):
        """T1.3: GET /schedule with USE_FSRS=False returns 200.

        AC-32.11.1: schedule endpoint returns valid response (not 500).
        Note: Cannot verify Ebbinghaus intervals in schedule items because
        schedule scans canvas files on disk. Without real canvas files in
        the test environment, items will be empty. The key verification is
        that the endpoint doesn't crash (500) when FSRS is unavailable.
        """
        resp = client.get("/api/v1/review/schedule")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "items" in data
        assert "total_count" in data
        assert isinstance(data["items"], list)
        assert isinstance(data["total_count"], int)
        assert data["total_count"] >= 0

    def test_fsrs_state_not_initialized(self, client, isolate_card_states):
        """T1.4: GET /fsrs-state returns found=false when FSRS not initialized.

        AC-32.11.1: fsrs-state returns found=false, reason=fsrs_not_initialized.
        """
        resp = client.get("/api/v1/review/fsrs-state/e2e-concept-degraded")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["found"] is False
        assert data["reason"] == "fsrs_not_initialized"


# =============================================================================
# AC-32.11.2: Health endpoint FSRS 降级状态
# =============================================================================

class TestHealthFSRSDegraded:
    """E2E: Health endpoint reports FSRS as degraded."""

    def test_health_fsrs_degraded(self, client, isolate_card_states):
        """T1.5: GET /health shows components.fsrs=degraded.

        AC-32.11.2: When FSRS_RUNTIME_OK=False, health reports degraded.
        """
        # First, trigger ReviewService singleton creation to set FSRS_RUNTIME_OK=False
        # by calling any review endpoint
        client.get("/api/v1/review/fsrs-state/trigger-init")

        # Now check health
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "components" in data, f"Health response missing 'components': {data}"
        assert data["components"].get("fsrs") == "degraded", (
            f"Expected fsrs=degraded, got {data['components'].get('fsrs')}"
        )


# =============================================================================
# AC-32.11.4: Ebbinghaus fallback next_review 时间正确性
# =============================================================================

class TestEbbinghausNextReviewTiming:
    """E2E: Verify Ebbinghaus fallback timing accuracy through HTTP."""

    def test_ebbinghaus_next_review_timing(self, client, isolate_card_states):
        """T1.6: score=50 → interval=3 days → next_review_date = today + 3 days.

        AC-32.11.4: E2E verification through HTTP endpoint.
        Response model uses `date` (not datetime), so we verify date accuracy
        with ±1 day tolerance for timezone edge cases (UTC midnight).
        """
        from datetime import date as date_cls

        resp = client.put("/api/v1/review/record", json={
            "canvas_name": "timing-test",
            "node_id": "timing-concept-e2e",
            "score": 50,
        })
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()

        # Verify algorithm is fallback
        assert data["algorithm"] == "ebbinghaus-fallback"
        # Verify interval = 3 days (score 40-59 → 3 days)
        assert data["new_interval"] == 3

        # Verify next_review_date is approximately today + 3 days
        expected_date = date_cls.today() + timedelta(days=3)
        actual_date = date_cls.fromisoformat(data["next_review_date"])
        # ±1 day tolerance for UTC midnight edge cases
        assert abs((actual_date - expected_date).days) <= 1, (
            f"Expected ~{expected_date}, got {actual_date}"
        )
