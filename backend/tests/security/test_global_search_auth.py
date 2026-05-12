"""Round-23 wave-2 hotfix — POST /api/v1/chat/global-search auth regression.

Verifies that the chat_router-level ``Depends(require_internal_api_key)``
correctly enforces the INTERNAL_API_KEY fail-closed matrix on the
``/global-search`` endpoint (Story 2.2+2.9 global search).

This test does NOT depend on the BE-A multi-vault hotfix nor the BE-B
supplementary metadata sanitizer — it validates the auth wrapper alone.

Fail-closed matrix (mirrors test_sync_batch_auth.py):
    DEBUG  INTERNAL_API_KEY  request_key   expected
    True   ""                missing       200 (dev convenience)
    False  "secret-key"      missing       403
    False  "secret-key"      "secret-key"  200
"""

from __future__ import annotations

from typing import Generator
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.main import app


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


SAMPLE_PAYLOAD = {
    "user_question": "what is dynamic programming",
    "vault_id": "test_vault",
    "subject_id": "test_subject",
    "top_k_max": 5,
    "hard_cap": 5,
}


def _settings_factory(*, debug: bool, key: str):
    """Build a get_settings override returning the requested DEBUG/key combo."""

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


@pytest.fixture
def auth_client() -> Generator[TestClient, None, None]:
    """A TestClient that bypasses the real supplementary search so we test auth alone.

    Patches:
    - ``_get_supp_lancedb_client`` → returns ``None`` so the endpoint short-circuits
      into the empty-materials path without needing a real LanceDB.
    - ``search_supplementary`` → returns an empty materials dict (defensive).
    """
    empty_supp = {
        "materials": [],
        "degraded": True,
        "reason": "lancedb_unavailable",
    }
    with (
        patch(
            "app.api.v1.endpoints.chat._get_supp_lancedb_client",
            new=AsyncMock(return_value=None),
        ),
        patch(
            "app.api.v1.endpoints.chat.search_supplementary",
            new=AsyncMock(return_value=empty_supp),
        ),
    ):
        with TestClient(app) as test_client:
            yield test_client
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Production (DEBUG=False) — strict fail-closed matrix
# ---------------------------------------------------------------------------


class TestGlobalSearchAuth:
    """Round-23 wave-2 — `/global-search` MUST honour the require_internal_api_key dependency."""

    def test_global_search_requires_internal_key_in_production_mode(
        self, auth_client: TestClient
    ) -> None:
        """DEBUG=False + INTERNAL_API_KEY configured + no header → 403."""
        app.dependency_overrides[get_settings] = _settings_factory(
            debug=False, key="secret-key"
        )
        response = auth_client.post("/api/v1/chat/global-search", json=SAMPLE_PAYLOAD)
        assert response.status_code == 403, (
            "DEBUG=False with a configured INTERNAL_API_KEY must require the "
            "X-CLS-Internal-Key header on /global-search (chat_router has "
            "Depends(require_internal_api_key) at router scope)."
        )
        assert "invalid" in response.json()["detail"].lower()

    def test_global_search_accepts_valid_internal_key(
        self, auth_client: TestClient
    ) -> None:
        """DEBUG=False + INTERNAL_API_KEY=secret-key + matching header → 200."""
        app.dependency_overrides[get_settings] = _settings_factory(
            debug=False, key="secret-key"
        )
        response = auth_client.post(
            "/api/v1/chat/global-search",
            json=SAMPLE_PAYLOAD,
            headers={"X-CLS-Internal-Key": "secret-key"},
        )
        assert response.status_code == 200, (
            f"Expected 200 with valid key, got {response.status_code}: "
            f"{response.text[:200]}"
        )
        body = response.json()
        # Endpoint should still produce a manifest even with degraded supp.
        assert "enriched_context" in body
        assert "Global Search Manifest" in body["enriched_context"]
        # 0 materials expected because we patched _get_supp_lancedb_client → None.
        assert body["supplementary_count"] == 0

    def test_global_search_allows_no_key_in_debug_mode(
        self, auth_client: TestClient
    ) -> None:
        """DEBUG=True + INTERNAL_API_KEY unconfigured + no header → 200 (dev transparency).

        This matches the dev convenience branch in app/security.py: when a
        developer has not set INTERNAL_API_KEY locally, the endpoint should
        not block plugin/hook requests (a warning is logged instead).
        """
        app.dependency_overrides[get_settings] = _settings_factory(debug=True, key="")
        response = auth_client.post("/api/v1/chat/global-search", json=SAMPLE_PAYLOAD)
        assert response.status_code == 200, (
            f"Expected 200 in DEBUG mode with unconfigured key, got "
            f"{response.status_code}: {response.text[:200]}"
        )
        body = response.json()
        assert body["supplementary_count"] == 0
