"""Story 1.1 Task 4-5: Startup health check and setup wizard tests.

Verifies the startup_health_check endpoint returns structured results
for each component, and the setup-wizard orchestrates initialization.
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.main import app

    return TestClient(app)


class TestStartupCheck:
    """Task 4: GET /api/v1/system/startup-check."""

    def test_endpoint_exists(self, client: TestClient):
        resp = client.get("/api/v1/system/startup-check")
        assert resp.status_code != 404, "startup-check endpoint must exist"

    def test_returns_structured_response(self, client: TestClient):
        resp = client.get("/api/v1/system/startup-check")
        data = resp.json()
        assert "data" in data
        assert "checks" in data["data"]

    def test_each_check_has_required_fields(self, client: TestClient):
        resp = client.get("/api/v1/system/startup-check")
        checks = resp.json()["data"]["checks"]
        for check in checks:
            assert "service" in check
            assert "status" in check
            assert "latency_ms" in check

    def test_checks_neo4j_ollama_fastapi_mcp(self, client: TestClient):
        resp = client.get("/api/v1/system/startup-check")
        checks = resp.json()["data"]["checks"]
        service_names = [c["service"] for c in checks]
        assert "neo4j" in service_names
        assert "ollama" in service_names
        assert "fastapi" in service_names
        assert "mcp" in service_names


class TestSetupWizard:
    """Task 5: POST /api/v1/system/setup-wizard."""

    def test_endpoint_exists(self, client: TestClient):
        resp = client.post(
            "/api/v1/system/setup-wizard", json={"vault_path": "/tmp/test-vault"}
        )
        assert resp.status_code != 404, "setup-wizard endpoint must exist"

    def test_returns_structured_report(self, client: TestClient):
        resp = client.post(
            "/api/v1/system/setup-wizard", json={"vault_path": "/tmp/test-vault-wizard"}
        )
        data = resp.json()
        assert "data" in data
        report = data["data"]
        assert "vault_ready" in report
        assert "plugins" in report
        assert "backend" in report
        assert "overall_status" in report
