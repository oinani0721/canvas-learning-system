"""FR-KG-04 prompt-injection-and-auth-completion Phase 2 —
/system/config and /system/test-llm internal API key enforcement.

Extends the fail-closed matrix from ``test_sync_batch_auth.py`` to the two
previously-unauthenticated system endpoints. The matrix is:

    DEBUG  INTERNAL_API_KEY  request_key   expected
    True   ""                missing       200 (dev bypass, warning logged)
    True   "tk"              missing       403
    False  ""                missing       503 (production fail-closed)
    False  "tk"              missing       403
    False  "tk"              "wrong"       403
    False  "tk"              "tk"          200

The LiteLLM side of ``/test-llm`` is stubbed out so the tests only exercise
auth — the point is to prove the dependency runs BEFORE the body handler.
"""

from __future__ import annotations

from typing import Generator
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.main import app


# ---------------------------------------------------------------------------
# Request payloads
# ---------------------------------------------------------------------------


CONFIG_PAYLOAD = {
    "chat": {
        "provider": "ollama",
        "model_name": "qwen2.5:7b",
        "api_key": "",
    },
    "scoring": None,
}

TEST_LLM_PAYLOAD = {
    "provider": "ollama",
    "model_name": "qwen2.5:7b",
    "api_key": "",
}


def _settings_factory(*, debug: bool, key: str):
    """Build a get_settings override that returns the requested DEBUG/key combo."""

    def override() -> Settings:
        return Settings(
            PROJECT_NAME="Canvas Learning System API (Test)",
            VERSION="1.0.0-test",
            DEBUG=debug,
            LOG_LEVEL="DEBUG",
            CORS_ORIGINS="http://localhost:3000",
            CANVAS_BASE_PATH="./test_canvas",
            INTERNAL_API_KEY=key,
        )

    return override


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def auth_client() -> Generator[TestClient, None, None]:
    """TestClient with LiteLLM patched so tests only measure auth behavior.

    - ``litellm.acompletion`` is replaced with a no-op AsyncMock so that
      ``/test-llm`` does not actually hit a provider when auth passes.
    - ``get_runtime_model_config`` is patched so ``/config`` does not mutate
      shared process-wide state across tests.
    """
    with patch(
        "litellm.acompletion",
        new=AsyncMock(return_value=None),
    ):
        with patch(
            "app.core.litellm_config.get_runtime_model_config"
        ) as mock_get_runtime:
            # The endpoint calls mgr.update(sys_config). We just want a
            # no-op manager so the call doesn't blow up or leak state.
            mock_mgr = AsyncMock()
            mock_mgr.update = lambda *args, **kwargs: None
            mock_get_runtime.return_value = mock_mgr

            with TestClient(app) as test_client:
                yield test_client

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Production (DEBUG=False) — strict fail-closed matrix
# ---------------------------------------------------------------------------


class TestSystemConfigAuth:
    """POST /api/v1/system/config must require the internal API key."""

    def test_prod_no_key_configured_503(self, auth_client: TestClient) -> None:
        app.dependency_overrides[get_settings] = _settings_factory(debug=False, key="")
        response = auth_client.post("/api/v1/system/config", json=CONFIG_PAYLOAD)
        assert response.status_code == 503
        assert "not configured" in response.json()["detail"].lower()

    def test_prod_wrong_key_403(self, auth_client: TestClient) -> None:
        app.dependency_overrides[get_settings] = _settings_factory(
            debug=False, key="real-key"
        )
        response = auth_client.post(
            "/api/v1/system/config",
            json=CONFIG_PAYLOAD,
            headers={"X-CLS-Internal-Key": "wrong"},
        )
        assert response.status_code == 403

    def test_prod_missing_header_403(self, auth_client: TestClient) -> None:
        app.dependency_overrides[get_settings] = _settings_factory(
            debug=False, key="real-key"
        )
        response = auth_client.post("/api/v1/system/config", json=CONFIG_PAYLOAD)
        assert response.status_code == 403

    def test_prod_correct_key_200(self, auth_client: TestClient) -> None:
        app.dependency_overrides[get_settings] = _settings_factory(
            debug=False, key="real-key"
        )
        response = auth_client.post(
            "/api/v1/system/config",
            json=CONFIG_PAYLOAD,
            headers={"X-CLS-Internal-Key": "real-key"},
        )
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "ok"

    def test_dev_mode_empty_key_allows_200(self, auth_client: TestClient) -> None:
        """DEBUG=True + empty key should allow the request (dev convenience)."""
        app.dependency_overrides[get_settings] = _settings_factory(debug=True, key="")
        response = auth_client.post("/api/v1/system/config", json=CONFIG_PAYLOAD)
        assert response.status_code == 200


class TestSystemTestLLMAuth:
    """POST /api/v1/system/test-llm must require the internal API key."""

    def test_prod_no_key_configured_503(self, auth_client: TestClient) -> None:
        app.dependency_overrides[get_settings] = _settings_factory(debug=False, key="")
        response = auth_client.post("/api/v1/system/test-llm", json=TEST_LLM_PAYLOAD)
        assert response.status_code == 503

    def test_prod_wrong_key_403(self, auth_client: TestClient) -> None:
        app.dependency_overrides[get_settings] = _settings_factory(
            debug=False, key="real-key"
        )
        response = auth_client.post(
            "/api/v1/system/test-llm",
            json=TEST_LLM_PAYLOAD,
            headers={"X-CLS-Internal-Key": "wrong"},
        )
        assert response.status_code == 403

    def test_prod_missing_header_403(self, auth_client: TestClient) -> None:
        app.dependency_overrides[get_settings] = _settings_factory(
            debug=False, key="real-key"
        )
        response = auth_client.post("/api/v1/system/test-llm", json=TEST_LLM_PAYLOAD)
        assert response.status_code == 403

    def test_prod_correct_key_200(self, auth_client: TestClient) -> None:
        app.dependency_overrides[get_settings] = _settings_factory(
            debug=False, key="real-key"
        )
        response = auth_client.post(
            "/api/v1/system/test-llm",
            json=TEST_LLM_PAYLOAD,
            headers={"X-CLS-Internal-Key": "real-key"},
        )
        assert response.status_code == 200
        # LiteLLM is mocked to no-op; success path returns status=success.
        assert response.json()["data"]["status"] == "success"

    def test_dev_mode_empty_key_allows_200(self, auth_client: TestClient) -> None:
        """DEBUG=True + empty key should allow (dev convenience)."""
        app.dependency_overrides[get_settings] = _settings_factory(debug=True, key="")
        response = auth_client.post("/api/v1/system/test-llm", json=TEST_LLM_PAYLOAD)
        assert response.status_code == 200
