# Story 38.3: FSRS State Initialization Guarantee - API Tests
"""
API-level tests for Story 38.3: FSRS State Initialization Guarantee.

Tests the HTTP endpoints:
- GET /api/v1/review/fsrs-state/{concept_id} — AC-1: reason codes via HTTP
- GET /health — AC-3: components.fsrs field
- AC-2: Frontend contract — default score 50 when fsrs_state is null

[Source: docs/implementation-artifacts/story-38.3.md]

Story 38.9: Patch targets use services-layer singleton via
_get_review_service_singleton (imported in review.py from services layer)
and module-level FSRS flags (FSRS_AVAILABLE, FSRS_RUNTIME_OK).
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.config import Settings, get_settings
from app.main import app
from fastapi.testclient import TestClient
from tests.support.lifespan import no_lifespan


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
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_settings, None)


@pytest.fixture
def client():
    with no_lifespan(app), TestClient(app) as c:
        yield c


@pytest.fixture
def mock_review_singleton():
    """Inject a mock into the services-layer ReviewService singleton.

    Story 38.9: The FSRS state endpoint uses await _get_review_service_singleton()
    which delegates to services.review_service.get_review_service(). We patch
    the imported name in review.py to inject our mock.
    """
    mock_service = MagicMock()
    with patch(
        "app.api.v1.endpoints.review._get_review_service_singleton",
        new_callable=AsyncMock,
        return_value=mock_service,
    ):
        yield mock_service


# ═══════════════════════════════════════════════════════════════════════════════
# AC-1 + AC-4: GET /api/v1/review/fsrs-state/{concept_id}
# ═══════════════════════════════════════════════════════════════════════════════


class TestFSRSStateEndpoint:
    """API tests for FSRS state query endpoint."""

    def test_returns_auto_created_card(self, client, mock_review_singleton):
        """AC-4: When no card exists, endpoint auto-creates and returns found=True."""
        mock_review_singleton.get_fsrs_state = AsyncMock(
            return_value={
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
            }
        )

        resp = client.get("/api/v1/review/fsrs-state/test-concept-1")

        assert resp.status_code == 200
        data = resp.json()
        assert data["found"] is True
        assert data["concept_id"] == "test-concept-1"
        assert data["fsrs_state"]["stability"] == 1.0
        assert data["fsrs_state"]["difficulty"] == 5.0
        assert data["card_state"] == '{"stability":1.0}'
        assert data["reason"] is None

    def test_returns_reason_fsrs_not_initialized(self, client, mock_review_singleton):
        """AC-1: When FSRS not initialized, endpoint returns reason code."""
        mock_review_singleton.get_fsrs_state = AsyncMock(
            return_value={
                "found": False,
                "reason": "fsrs_not_initialized",
            }
        )

        resp = client.get("/api/v1/review/fsrs-state/concept-no-fsrs")

        assert resp.status_code == 200
        data = resp.json()
        assert data["found"] is False
        assert data["reason"] == "fsrs_not_initialized"
        assert data["fsrs_state"] is None

    def test_returns_reason_on_service_exception(self, client, mock_review_singleton):
        """AC-1: When service raises, endpoint returns error reason gracefully."""
        mock_review_singleton.get_fsrs_state = AsyncMock(side_effect=RuntimeError("db connection failed"))

        resp = client.get("/api/v1/review/fsrs-state/concept-err")

        assert resp.status_code == 200
        data = resp.json()
        assert data["found"] is False
        assert "error" in data["reason"]

    def test_returns_reason_auto_creation_failed(self, client, mock_review_singleton):
        """AC-1: When auto-creation fails, endpoint returns reason code."""
        mock_review_singleton.get_fsrs_state = AsyncMock(
            return_value={
                "found": False,
                "reason": "auto_creation_failed",
            }
        )

        resp = client.get("/api/v1/review/fsrs-state/concept-new")

        assert resp.status_code == 200
        data = resp.json()
        assert data["found"] is False
        assert data["reason"] == "auto_creation_failed"

    def test_found_true_has_null_reason(self, client, mock_review_singleton):
        """AC-1: When found=True, reason should be null in response."""
        mock_review_singleton.get_fsrs_state = AsyncMock(
            return_value={
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
            }
        )

        resp = client.get("/api/v1/review/fsrs-state/existing-concept")

        data = resp.json()
        assert data["found"] is True
        assert data["reason"] is None
        assert data["fsrs_state"]["reps"] == 3
        assert data["fsrs_state"]["lapses"] == 1


# ═══════════════════════════════════════════════════════════════════════════════
# AC-3: GET /health — FSRS component status
# Health endpoint reads FSRS_AVAILABLE and FSRS_RUNTIME_OK module-level vars
# from review_service.py, NOT get_review_service from dependencies.
# ═══════════════════════════════════════════════════════════════════════════════


class TestHealthEndpointFSRS:
    """API tests for FSRS status in health endpoint."""

    def test_health_includes_fsrs_ok(self, client, monkeypatch):
        """AC-3: When FSRS initialized, health shows fsrs=ok."""
        import app.services.review_service as review_mod

        monkeypatch.setattr(review_mod, "FSRS_AVAILABLE", True)
        monkeypatch.setattr(review_mod, "FSRS_RUNTIME_OK", True)
        resp = client.get("/api/v1/health")

        assert resp.status_code == 200
        data = resp.json()
        assert "components" in data
        assert data["components"]["fsrs"] == "ok"

    def test_health_includes_fsrs_degraded(self, client, monkeypatch):
        """AC-3: When FSRS not initialized, health shows fsrs=degraded."""
        import app.services.review_service as review_mod

        monkeypatch.setattr(review_mod, "FSRS_AVAILABLE", False)
        monkeypatch.setattr(review_mod, "FSRS_RUNTIME_OK", False)
        resp = client.get("/api/v1/health")

        assert resp.status_code == 200
        data = resp.json()
        assert data["components"]["fsrs"] == "degraded"

    def test_health_fsrs_degraded_when_runtime_false(self, client, monkeypatch):
        """AC-3: When FSRS_RUNTIME_OK is False, health shows fsrs=degraded."""
        import app.services.review_service as review_mod

        monkeypatch.setattr(review_mod, "FSRS_AVAILABLE", True)
        monkeypatch.setattr(review_mod, "FSRS_RUNTIME_OK", False)
        resp = client.get("/api/v1/health")

        assert resp.status_code == 200
        data = resp.json()
        assert data["components"]["fsrs"] == "degraded"

    def test_health_fsrs_ok_when_runtime_none_but_available(self, client, monkeypatch):
        """AC-3: When FSRS_RUNTIME_OK is None (not yet instantiated), falls back to FSRS_AVAILABLE."""
        import app.services.review_service as review_mod

        monkeypatch.setattr(review_mod, "FSRS_AVAILABLE", True)
        monkeypatch.setattr(review_mod, "FSRS_RUNTIME_OK", None)
        resp = client.get("/api/v1/health")

        assert resp.status_code == 200
        data = resp.json()
        assert data["components"]["fsrs"] == "ok"


# ═══════════════════════════════════════════════════════════════════════════════
# AC-2: Frontend Contract — default score 50 when fsrs_state is null
# Closes gap identified in traceability-matrix-epic38.md
# ═══════════════════════════════════════════════════════════════════════════════


class TestFrontendContractDefaultScore:
    """
    AC-2 (D3: Input Validation — Frontend Contract):
    When fsrs_state is null, the frontend uses default score=50.

    These tests verify the backend half of this contract:
    - found=false → fsrs_state is null (frontend then applies score=50)
    - Auto-created cards return non-null fsrs_state with valid defaults
    """

    def test_not_found_returns_null_fsrs_state(self, client, mock_review_singleton):
        """
        [P1] AC-2 Contract: When found=false, fsrs_state MUST be null.
        Frontend relies on this to trigger default score=50 fallback.
        (PriorityCalculatorService.ts L282-287: if (!state) → score: 50)
        """
        mock_review_singleton.get_fsrs_state = AsyncMock(
            return_value={
                "found": False,
                "reason": "fsrs_not_initialized",
            }
        )

        resp = client.get("/api/v1/review/fsrs-state/new-concept")

        data = resp.json()
        assert data["found"] is False
        assert data["fsrs_state"] is None, (
            "Frontend contract: fsrs_state must be null when found=false, "
            "so PriorityCalculatorService falls back to score=50"
        )

    def test_auto_created_card_returns_non_null_fsrs_state(self, client, mock_review_singleton):
        """
        [P1] AC-2 + AC-4: Auto-created card must return found=true with
        non-null fsrs_state, so frontend uses real FSRS data instead of
        default score=50.
        """
        mock_review_singleton.get_fsrs_state = AsyncMock(
            return_value={
                "found": True,
                "stability": 1.0,
                "difficulty": 5.0,
                "state": 0,
                "reps": 0,
                "lapses": 0,
                "retrievability": 1.0,
                "due": None,
                "last_review": None,
                "card_state": '{"stability":1.0,"difficulty":5.0}',
            }
        )

        resp = client.get("/api/v1/review/fsrs-state/auto-created-concept")

        data = resp.json()
        assert data["found"] is True
        assert data["fsrs_state"] is not None, (
            "Auto-created card must have non-null fsrs_state so frontend "
            "uses real FSRS values, not the default score=50"
        )
        assert data["fsrs_state"]["stability"] == 1.0
        assert data["fsrs_state"]["difficulty"] == 5.0
        assert data["fsrs_state"]["state"] == 0

    def test_error_returns_null_fsrs_state(self, client, mock_review_singleton):
        """
        [P1] AC-2 Contract: Service error → found=false, fsrs_state=null.
        Frontend falls back to score=50.
        """
        mock_review_singleton.get_fsrs_state = AsyncMock(side_effect=RuntimeError("unexpected error"))

        resp = client.get("/api/v1/review/fsrs-state/error-concept")

        data = resp.json()
        assert data["found"] is False
        assert data["fsrs_state"] is None, "Frontend contract: on error, fsrs_state=null → score=50"


# ═══════════════════════════════════════════════════════════════════════════════
# CARD-D3: 持久化失败信号必须穿透到 HTTP 响应 (加性可选字段, 200 语义不变)
# ═══════════════════════════════════════════════════════════════════════════════


class TestPersistHonestyForwardingD3:
    """CARD-D3: service 层的持久化诚实信号需由端点原样转发, 不得在
    响应模型处再次丢弃。"""

    def test_fsrs_state_forwards_persisted_and_reason(self, client, mock_review_singleton):
        """auto-create 写失败: found=True + persisted=False + reason 透传。"""
        mock_review_singleton.get_fsrs_state = AsyncMock(
            return_value={
                "found": True,
                "stability": 1.0,
                "difficulty": 5.0,
                "state": 0,
                "reps": 0,
                "lapses": 0,
                "retrievability": None,
                "due": None,
                "last_review": None,
                "card_state": "{}",
                "persisted": False,
                "reason": "auto_created_not_persisted",
            }
        )
        resp = client.get("/api/v1/review/fsrs-state/d3-concept")
        assert resp.status_code == 200
        body = resp.json()
        assert body["found"] is True
        assert body["persisted"] is False
        assert body["reason"] == "auto_created_not_persisted"

    def test_record_forwards_card_state_persisted(self, client, mock_review_singleton):
        """评分持久化失败: card_state_persisted=False + degraded_reason 透传,
        status 仍 200 (语义不变, 仅加性字段)。"""
        mock_review_singleton.record_review_result = AsyncMock(
            return_value={
                "next_review": "2026-09-01T00:00:00+00:00",
                "interval_days": 3,
                "status": "recorded",
                "algorithm": "fsrs-4.5",
                "card_data": "{}",
                "card_state_persisted": False,
                "degraded_reason": "card_state_write_failed",
            }
        )
        resp = client.put(
            "/api/v1/review/record",
            json={"canvas_name": "d3.canvas", "node_id": "d3-node", "rating": 3},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["card_state_persisted"] is False
        assert body["degraded_reason"] == "card_state_write_failed"
