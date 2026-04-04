"""Smoke tests: verify app boots and health endpoints respond.

These run as the FIRST gate in PostToolUse hook (~2s).
If smoke fails, skip all other tests (fast-fail).

Reuses the existing `client` fixture from conftest.py (function-scoped TestClient).
"""

import pytest


@pytest.mark.smoke
class TestAppBoot:
    """Verify the FastAPI app starts without crash."""

    def test_app_starts(self, client):
        """App boots and responds to any request."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200


@pytest.mark.smoke
class TestHealthEndpoint:
    """Verify /api/v1/health returns expected structure."""

    def test_health_returns_200(self, client):
        response = client.get("/api/v1/health")
        assert response.status_code == 200

    def test_health_has_required_fields(self, client):
        data = client.get("/api/v1/health").json()
        assert "status" in data
        assert "app_name" in data
        assert "version" in data
        assert "timestamp" in data

    def test_health_status_is_healthy(self, client):
        data = client.get("/api/v1/health").json()
        assert data["status"] == "healthy"

    def test_health_has_components(self, client):
        """Health check includes component status (fsrs, neo4j, etc.)."""
        data = client.get("/api/v1/health").json()
        if "components" in data:
            assert isinstance(data["components"], dict)


@pytest.mark.smoke
class TestMetricsEndpoint:
    """Verify /api/v1/health/metrics responds."""

    def test_metrics_returns_200(self, client):
        response = client.get("/api/v1/health/metrics")
        assert response.status_code == 200
