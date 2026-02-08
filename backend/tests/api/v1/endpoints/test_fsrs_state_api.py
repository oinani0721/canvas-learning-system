# Story 38.3: FSRS State Initialization Guarantee - API Tests
"""
API-level tests for Story 38.3: FSRS State Initialization Guarantee.

Tests the HTTP endpoints:
- GET /api/v1/review/fsrs-state/{concept_id} — AC-1: reason codes via HTTP
- GET /health — AC-3: components.fsrs field

[Source: docs/implementation-artifacts/story-38.3.md]
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.config import Settings, get_settings


def get_settings_override() -> Settings:
    return Settings(
        PROJECT_NAME="Canvas Test",
        VERSION="1.0.0-test",
        DEBUG=True,
        LOG_LEVEL="DEBUG",
        CORS_ORIGINS="http://localhost:3000",
        CANVAS_BASE_PATH="./test_canvas",
    )


@pytest.fixture(autouse=True)
def override_settings():
    app.dependency_overrides[get_settings] = get_settings_override
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


# ═══════════════════════════════════════════════════════════════════════════════
# AC-1 + AC-4: GET /api/v1/review/fsrs-state/{concept_id}
# ═══════════════════════════════════════════════════════════════════════════════


class TestFSRSStateEndpoint:
    """API tests for FSRS state query endpoint."""

    def test_returns_auto_created_card(self, client):
        """AC-4: When no card exists, endpoint auto-creates and returns found=True."""
        mock_service = MagicMock()
        mock_service.get_fsrs_state = AsyncMock(return_value={
            "found": True,
            "stability": 1.0,
            "difficulty": 5.0,
            "state": 0,
            "reps": 0,
            "lapses": 0,
            "retrievability": 1.0,
            "due": None,
            "last_review": None,
            "card_state": '{"stability":1.0}',
        })

        with patch(
            "app.dependencies.get_review_service",
            return_value=mock_service,
        ):
            resp = client.get("/api/v1/review/fsrs-state/test-concept-1")

        assert resp.status_code == 200
        data = resp.json()
        assert data["found"] is True
        assert data["concept_id"] == "test-concept-1"
        assert data["fsrs_state"]["stability"] == 1.0
        assert data["fsrs_state"]["difficulty"] == 5.0
        assert data["card_state"] == '{"stability":1.0}'
        assert data["reason"] is None

    def test_returns_reason_fsrs_not_initialized(self, client):
        """AC-1: When FSRS not initialized, endpoint returns reason code."""
        mock_service = MagicMock()
        mock_service.get_fsrs_state = AsyncMock(return_value={
            "found": False,
            "reason": "fsrs_not_initialized",
        })

        with patch(
            "app.dependencies.get_review_service",
            return_value=mock_service,
        ):
            resp = client.get("/api/v1/review/fsrs-state/concept-no-fsrs")

        assert resp.status_code == 200
        data = resp.json()
        assert data["found"] is False
        assert data["reason"] == "fsrs_not_initialized"
        assert data["fsrs_state"] is None

    def test_returns_reason_on_service_exception(self, client):
        """AC-1: When service raises, endpoint returns error reason gracefully."""
        mock_service = MagicMock()
        mock_service.get_fsrs_state = AsyncMock(
            side_effect=RuntimeError("db connection failed")
        )

        with patch(
            "app.dependencies.get_review_service",
            return_value=mock_service,
        ):
            resp = client.get("/api/v1/review/fsrs-state/concept-err")

        assert resp.status_code == 200
        data = resp.json()
        assert data["found"] is False
        assert "error" in data["reason"]

    def test_returns_reason_no_card_created(self, client):
        """AC-1: When service returns no_card_created reason."""
        mock_service = MagicMock()
        mock_service.get_fsrs_state = AsyncMock(return_value={
            "found": False,
            "reason": "no_card_created",
        })

        with patch(
            "app.dependencies.get_review_service",
            return_value=mock_service,
        ):
            resp = client.get("/api/v1/review/fsrs-state/concept-new")

        assert resp.status_code == 200
        data = resp.json()
        assert data["found"] is False
        assert data["reason"] == "no_card_created"

    def test_found_true_has_null_reason(self, client):
        """AC-1: When found=True, reason should be null in response."""
        mock_service = MagicMock()
        mock_service.get_fsrs_state = AsyncMock(return_value={
            "found": True,
            "stability": 2.5,
            "difficulty": 4.0,
            "state": 1,
            "reps": 3,
            "lapses": 1,
            "retrievability": 0.85,
            "due": None,
            "last_review": None,
            "card_state": '{"s":2.5}',
        })

        with patch(
            "app.dependencies.get_review_service",
            return_value=mock_service,
        ):
            resp = client.get("/api/v1/review/fsrs-state/existing-concept")

        data = resp.json()
        assert data["found"] is True
        assert data["reason"] is None
        assert data["fsrs_state"]["reps"] == 3
        assert data["fsrs_state"]["lapses"] == 1


# ═══════════════════════════════════════════════════════════════════════════════
# AC-3: GET /health — FSRS component status
# ═══════════════════════════════════════════════════════════════════════════════


class TestHealthEndpointFSRS:
    """API tests for FSRS status in health endpoint."""

    def test_health_includes_fsrs_ok(self, client):
        """AC-3: When FSRS initialized, health shows fsrs=ok."""
        mock_service = MagicMock()
        mock_service._fsrs_init_ok = True

        with patch(
            "app.dependencies.get_review_service",
            return_value=mock_service,
        ):
            resp = client.get("/api/v1/health")

        assert resp.status_code == 200
        data = resp.json()
        assert "components" in data
        assert data["components"]["fsrs"] == "ok"

    def test_health_includes_fsrs_degraded(self, client):
        """AC-3: When FSRS not initialized, health shows fsrs=degraded."""
        mock_service = MagicMock()
        mock_service._fsrs_init_ok = False

        with patch(
            "app.dependencies.get_review_service",
            return_value=mock_service,
        ):
            resp = client.get("/api/v1/health")

        assert resp.status_code == 200
        data = resp.json()
        assert data["components"]["fsrs"] == "degraded"

    def test_health_fsrs_degraded_when_service_none(self, client):
        """AC-3: When review service is None, health shows fsrs=degraded."""
        with patch(
            "app.dependencies.get_review_service",
            return_value=None,
        ):
            resp = client.get("/api/v1/health")

        assert resp.status_code == 200
        data = resp.json()
        assert data["components"]["fsrs"] == "degraded"

    def test_health_fsrs_degraded_on_exception(self, client):
        """AC-3: When get_review_service raises, health shows fsrs=degraded."""
        with patch(
            "app.dependencies.get_review_service",
            side_effect=RuntimeError("service unavailable"),
        ):
            resp = client.get("/api/v1/health")

        assert resp.status_code == 200
        data = resp.json()
        assert data["components"]["fsrs"] == "degraded"
