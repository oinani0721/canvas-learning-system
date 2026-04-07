"""FR-KG-04 Phase 4 Task 4.6: HTTP exception classification at /sync/batch.

Story: openspec change fix-fr-kg-04-schema-drift-and-sync-hardening.

The previous endpoint returned 503 for every exception, masking logic bugs
behind a "Neo4j unavailable" message. This test suite verifies the new
classification:

- ServiceUnavailable / AuthError / ConnectionError → 503
- Neo4jError (non-service) / ValueError / TypeError / anything else → 500

Response bodies must NOT contain raw exception text (no internal paths,
driver state, or stack traces leaked to the client).
"""

from __future__ import annotations

from typing import Any, Generator
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from neo4j.exceptions import AuthError, ServiceUnavailable

from app.config import Settings, get_settings
from app.main import app


SAMPLE_PAYLOAD = {
    "canvas_id": "test-canvas",
    "subject_id": "test-subject",
    "operations": [
        {
            "operation_id": "00000000-0000-0000-0000-000000000001",
            "entity_type": "node",
            "entity_id": "node-1",
            "operation": "create",
            "payload": {"title": "t", "content": "c"},
            "timestamp": "2026-04-07T00:00:00Z",
        }
    ],
}


def _dev_settings() -> Settings:
    """Dev-mode settings so the auth dependency lets the request through."""
    return Settings(
        PROJECT_NAME="Test",
        VERSION="1.0.0-test",
        DEBUG=True,
        LOG_LEVEL="DEBUG",
        CORS_ORIGINS="http://localhost:3000",
        CANVAS_BASE_PATH="./test_canvas",
        INTERNAL_API_KEY="",
    )


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """TestClient that cleans overrides between tests."""
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _override_sync_service_raising(exc: BaseException) -> Any:
    """Return a patch context manager that makes SyncService raise ``exc``."""

    async def raiser(*args: Any, **kwargs: Any) -> None:
        raise exc

    return patch(
        "app.services.sync_service.SyncService.process_sync_batch",
        new=AsyncMock(side_effect=raiser),
    )


# ---------------------------------------------------------------------------
# 503 branch: infrastructure failures
# ---------------------------------------------------------------------------


class TestInfrastructureErrors:
    """ServiceUnavailable, AuthError, ConnectionError → 503."""

    def test_service_unavailable_returns_503(self, client: TestClient) -> None:
        app.dependency_overrides[get_settings] = _dev_settings
        with _override_sync_service_raising(ServiceUnavailable("neo4j down")):
            response = client.post("/api/v1/sync/batch", json=SAMPLE_PAYLOAD)
        assert response.status_code == 503
        body = response.json()
        # Fixed, non-leaky message
        assert body["detail"] == "Neo4j unavailable"
        # Raw exception text must not appear in the response
        assert "neo4j down" not in str(body)

    def test_auth_error_returns_503(self, client: TestClient) -> None:
        app.dependency_overrides[get_settings] = _dev_settings
        with _override_sync_service_raising(AuthError("bad creds")):
            response = client.post("/api/v1/sync/batch", json=SAMPLE_PAYLOAD)
        assert response.status_code == 503
        assert response.json()["detail"] == "Neo4j unavailable"

    def test_connection_error_returns_503(self, client: TestClient) -> None:
        app.dependency_overrides[get_settings] = _dev_settings
        with _override_sync_service_raising(ConnectionError("refused")):
            response = client.post("/api/v1/sync/batch", json=SAMPLE_PAYLOAD)
        assert response.status_code == 503
        assert response.json()["detail"] == "Neo4j unavailable"


# ---------------------------------------------------------------------------
# 500 branch: logic errors
# ---------------------------------------------------------------------------


class TestLogicErrors:
    """Logic bugs (ValueError, TypeError, unexpected exceptions) → 500."""

    def test_value_error_returns_500(self, client: TestClient) -> None:
        app.dependency_overrides[get_settings] = _dev_settings
        with _override_sync_service_raising(ValueError("unexpected payload shape")):
            response = client.post("/api/v1/sync/batch", json=SAMPLE_PAYLOAD)
        assert response.status_code == 500
        body = response.json()
        # Fixed, generic message — no raw exception content
        assert body["detail"] == "Sync batch failed unexpectedly"
        assert "unexpected payload shape" not in str(body)

    def test_type_error_returns_500(self, client: TestClient) -> None:
        app.dependency_overrides[get_settings] = _dev_settings
        with _override_sync_service_raising(TypeError("int has no len()")):
            response = client.post("/api/v1/sync/batch", json=SAMPLE_PAYLOAD)
        assert response.status_code == 500
        assert response.json()["detail"] == "Sync batch failed unexpectedly"

    def test_generic_exception_returns_500(self, client: TestClient) -> None:
        app.dependency_overrides[get_settings] = _dev_settings

        class UnknownError(Exception):
            """A custom exception never seen before."""

        with _override_sync_service_raising(UnknownError("mystery")):
            response = client.post("/api/v1/sync/batch", json=SAMPLE_PAYLOAD)
        assert response.status_code == 500
        body = response.json()
        assert body["detail"] == "Sync batch failed unexpectedly"
        assert "mystery" not in str(body)
