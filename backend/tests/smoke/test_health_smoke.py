"""Smoke tests: verify health endpoints respond.

These run as the FIRST gate in PostToolUse hook (~2s).
If smoke fails, skip all other tests (fast-fail).

Reuses the existing `client` fixture from conftest.py (function-scoped TestClient).

CARD-TEST-isolate-lifespan (2026-09-01): the root `client` fixture is now
lifespan-free — these tests exercise the **route layer only** and no longer
prove that the app's startup sequence runs. Real-startup coverage lives in
tests/integration/ and tests/e2e/ (the advisory-exempt files that still run
the real lifespan). Do not describe these tests as boot verification.
"""

import pytest


@pytest.mark.smoke
class TestRouteAvailability:
    """Verify the route layer responds (lifespan-free; NOT a boot test)."""

    def test_health_route_responds(self, client):
        """Health route responds (routing + middleware healthy)."""
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
