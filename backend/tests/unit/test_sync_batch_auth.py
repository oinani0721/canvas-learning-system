# Sprint 1.2 — Phase 2: /sync/batch internal API key authentication
# Story: openspec change fix-fr-kg-04-schema-drift-and-sync-hardening
#
# TDD: tests written FIRST, before implementation.
"""
Tests for the internal API key dependency on POST /api/v1/sync/batch.

Fail-closed matrix:
    DEBUG  INTERNAL_API_KEY  request_key   expected
    True   ""                missing       200 (dev convenience, warning logged)
    True   "tk"              missing       403 (key configured, must match)
    True   "tk"              "tk"          200
    False  ""                missing       503 (fail-closed, no key configured)
    False  "tk"              missing       403
    False  "tk"              "wrong"       403
    False  "tk"              "tk"          200
"""

from __future__ import annotations

from typing import Generator
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.main import app
from app.models.sync_models import SyncBatchResponse


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


SAMPLE_PAYLOAD = {
    "canvas_id": "test_canvas",
    "subject_id": "test_subject",
    "operations": [
        {
            "operation_id": "00000000-0000-0000-0000-000000000001",
            "entity_type": "board",
            "entity_id": "test_canvas",
            "operation": "create",
            "payload": {"name": "Test Board"},
            "timestamp": "2026-04-06T00:00:00Z",
        }
    ],
}

# A successful sync response object — used as the canned return value of the
# patched SyncService so the auth tests do not depend on Neo4j being up.
EMPTY_OK_RESPONSE = SyncBatchResponse(results=[], synced_count=0, failed_count=0)


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


@pytest.fixture
def auth_client() -> Generator[TestClient, None, None]:
    """A TestClient that bypasses the real SyncService so we test auth alone."""
    with patch(
        "app.services.sync_service.SyncService.process_sync_batch",
        new=AsyncMock(return_value=EMPTY_OK_RESPONSE),
    ):
        with TestClient(app) as test_client:
            yield test_client
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Production (DEBUG=False) — strict fail-closed matrix
# ---------------------------------------------------------------------------


class TestProductionFailClosed:
    """When DEBUG=False, missing or wrong keys MUST be rejected."""

    def test_no_key_configured_fails_closed_503(self, auth_client: TestClient) -> None:
        app.dependency_overrides[get_settings] = _settings_factory(debug=False, key="")
        response = auth_client.post("/api/v1/sync/batch", json=SAMPLE_PAYLOAD)
        assert response.status_code == 503, (
            "DEBUG=False with empty INTERNAL_API_KEY must fail closed (503), "
            "not silently allow"
        )
        assert "not configured" in response.json()["detail"].lower()

    def test_missing_header_returns_403(self, auth_client: TestClient) -> None:
        app.dependency_overrides[get_settings] = _settings_factory(
            debug=False, key="real-key"
        )
        response = auth_client.post("/api/v1/sync/batch", json=SAMPLE_PAYLOAD)
        assert response.status_code == 403
        assert "invalid" in response.json()["detail"].lower()

    def test_wrong_key_returns_403(self, auth_client: TestClient) -> None:
        app.dependency_overrides[get_settings] = _settings_factory(
            debug=False, key="real-key"
        )
        response = auth_client.post(
            "/api/v1/sync/batch",
            json=SAMPLE_PAYLOAD,
            headers={"X-CLS-Internal-Key": "wrong-key"},
        )
        assert response.status_code == 403

    def test_correct_key_grants_access(self, auth_client: TestClient) -> None:
        app.dependency_overrides[get_settings] = _settings_factory(
            debug=False, key="real-key"
        )
        response = auth_client.post(
            "/api/v1/sync/batch",
            json=SAMPLE_PAYLOAD,
            headers={"X-CLS-Internal-Key": "real-key"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["synced_count"] == 0
        assert body["failed_count"] == 0


# ---------------------------------------------------------------------------
# Development (DEBUG=True) — convenience: allow missing key with warning
# ---------------------------------------------------------------------------


class TestDevelopmentConvenience:
    """When DEBUG=True, missing INTERNAL_API_KEY is allowed (with warning)."""

    def test_dev_mode_no_key_allows_missing_header(
        self, auth_client: TestClient
    ) -> None:
        """DEBUG=True + empty key should allow the request and emit a warning.

        security.py uses a module-level structlog logger. The most reliable
        way to verify it emitted a warning during the request is to spy on
        ``security.logger.warning`` directly.
        """
        from app import security as security_mod

        app.dependency_overrides[get_settings] = _settings_factory(debug=True, key="")
        with patch.object(security_mod.logger, "warning") as warning_spy:
            response = auth_client.post("/api/v1/sync/batch", json=SAMPLE_PAYLOAD)

        assert response.status_code == 200
        # The dev-bypass branch must emit at least one warning so the bypass
        # is observable. Either the event name or any kwarg should mention
        # the dev-mode condition.
        assert warning_spy.called, (
            "DEBUG mode bypass should emit at least one structured warning"
        )

        # Inspect the call args for the dev-bypass signature. security.py
        # may use either structlog kwargs or stdlib %-format positional args,
        # so accept both styles.
        def _flatten(call) -> str:
            args, kwargs = call.args, call.kwargs
            return " ".join(
                [str(a) for a in args] + [f"{k}={v}" for k, v in kwargs.items()]
            )

        bypass_call_found = any(
            ("INTERNAL_API_KEY" in _flatten(call) and "DEBUG" in _flatten(call))
            or "auth_dev_bypass" in _flatten(call)
            or "unconfigured_in_dev" in _flatten(call)
            for call in warning_spy.call_args_list
        )
        assert bypass_call_found, (
            f"None of the warning calls match the dev-bypass event signature: "
            f"{warning_spy.call_args_list}"
        )

    def test_dev_mode_with_key_still_enforces(self, auth_client: TestClient) -> None:
        """Even in DEBUG mode, if a key IS configured, it must match."""
        app.dependency_overrides[get_settings] = _settings_factory(
            debug=True, key="dev-key"
        )
        # Missing key → 403 (key was configured, so it must match)
        response = auth_client.post("/api/v1/sync/batch", json=SAMPLE_PAYLOAD)
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# Header parsing
# ---------------------------------------------------------------------------


class TestHeaderParsing:
    """The header name MUST be exactly X-CLS-Internal-Key (case-insensitive)."""

    def test_canonical_header_name(self, auth_client: TestClient) -> None:
        app.dependency_overrides[get_settings] = _settings_factory(
            debug=False, key="abc"
        )
        response = auth_client.post(
            "/api/v1/sync/batch",
            json=SAMPLE_PAYLOAD,
            headers={"X-CLS-Internal-Key": "abc"},
        )
        assert response.status_code == 200
