# Canvas Learning System - Health Endpoint E2E Tests
# Story 20.6 + Story 36.10: E2E Tests for Health API
"""
End-to-end tests for health endpoints.

Only tests verified-to-exist routes. Previous /health/providers tests
were removed (route does not exist — EPIC-36 adversarial review Issue 6b).

Endpoints tested:
- GET /api/v1/health — basic health check
- GET /api/v1/health/storage — unified storage health (Story 36.10)
- GET /api/v1/health/metrics — Prometheus metrics

[Source: docs/stories/20.6.story.md]
[Source: docs/stories/36.10.story.md]
"""

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Tests for health endpoints that actually exist."""

    def test_basic_health_check(self, client: TestClient):
        """Test basic /health endpoint (verified to exist)."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"

    def test_health_storage_endpoint(self, client: TestClient):
        """Test /health/storage endpoint returns storage backend status (Story 36.10)."""
        response = client.get("/api/v1/health/storage")
        assert response.status_code == 200
        data = response.json()
        # Verify response structure per AC-36.10.6
        assert "status" in data
        assert data["status"] in ("healthy", "degraded", "unhealthy")
        assert "storage_backends" in data
        assert isinstance(data["storage_backends"], list)
        assert "latency_metrics" in data
        assert "cached" in data

    def test_health_metrics_endpoint(self, client: TestClient):
        """Test /health/metrics returns Prometheus metrics."""
        response = client.get("/api/v1/health/metrics")
        assert response.status_code == 200
        # Prometheus metrics are text/plain
        assert "text/plain" in response.headers.get("content-type", "")
        # Should contain at least one metric line
        assert len(response.text) > 0

    def test_health_degraded_scenario(self, client: TestClient):
        """Test that /health/storage returns valid status even when backends unavailable."""
        # In test environment, backends (Neo4j, MCP) are typically not running,
        # so storage health should report degraded or unhealthy — but never crash
        response = client.get("/api/v1/health/storage")
        assert response.status_code == 200
        data = response.json()
        # Must be one of the valid statuses, regardless of backend availability
        assert data["status"] in ("healthy", "degraded", "unhealthy")
        # Storage backends list should always be present
        assert len(data["storage_backends"]) >= 1
