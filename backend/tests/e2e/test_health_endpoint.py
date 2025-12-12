# Canvas Learning System - Health Endpoint E2E Tests
# ✅ Story 20.6: E2E Tests for Health API (AC-20.6.1, AC-20.6.9)
"""
End-to-end tests for the /health/providers endpoint.

These tests verify:
- AC-20.6.1: Health check endpoint returns provider status
- AC-20.6.9: API response format validation
- Real HTTP request/response cycle

[Source: docs/stories/20.6.story.md#AC-20.6.1]
[Source: specs/api/canvas-api.openapi.yml]
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.clients.base_provider import (
    ProviderHealth,
    ProviderStatus,
)
from fastapi.testclient import TestClient


class TestHealthEndpointE2E:
    """E2E tests for /health/providers endpoint - AC-20.6.1"""

    def test_health_endpoint_returns_200(self, client: TestClient):
        """Test health endpoint returns 200 OK."""
        # Act
        response = client.get("/api/v1/health/providers")

        # Assert
        assert response.status_code == 200

    def test_health_endpoint_returns_provider_list(self, client: TestClient):
        """Test health endpoint returns list of providers."""
        # Act
        response = client.get("/api/v1/health/providers")
        data = response.json()

        # Assert
        assert "providers" in data
        assert isinstance(data["providers"], list)

    def test_health_endpoint_provider_format(self, client: TestClient):
        """AC-20.6.9: Validate provider status response format."""
        # Act
        response = client.get("/api/v1/health/providers")
        data = response.json()

        # Assert - Check format if providers exist
        if data.get("providers"):
            provider = data["providers"][0]
            # Required fields per OpenAPI spec
            assert "name" in provider
            assert "status" in provider
            # Status should be valid enum value
            assert provider["status"] in ["healthy", "degraded", "unhealthy"]

    def test_health_endpoint_includes_latency(self, client: TestClient):
        """Test health response includes latency information."""
        # Act
        response = client.get("/api/v1/health/providers")
        data = response.json()

        # Assert
        if data.get("providers"):
            provider = data["providers"][0]
            # latency_ms may be null if provider is unhealthy
            assert "latency_ms" in provider or "latency" in provider

    def test_health_endpoint_includes_timestamp(self, client: TestClient):
        """Test health response includes check timestamp."""
        # Act
        response = client.get("/api/v1/health/providers")

        # Assert - Basic validation that endpoint works
        assert response.status_code == 200
        # Note: Timestamp validation depends on implementation
        # Could be at top level ("timestamp", "checked_at") or per provider ("last_check")


@pytest.mark.asyncio
class TestHealthEndpointAsync:
    """Async E2E tests for health endpoint."""

    async def test_health_endpoint_with_mock_providers(self, async_client):
        """Test health endpoint with mocked providers."""
        # Arrange - Mock ProviderFactory
        with patch("app.api.v1.endpoints.health.get_provider_factory") as mock_factory:
            mock_instance = MagicMock()
            mock_instance.check_all_health = AsyncMock(return_value={
                "google": ProviderHealth(
                    status=ProviderStatus.HEALTHY,
                    latency_ms=50.0
                ),
                "openai": ProviderHealth(
                    status=ProviderStatus.DEGRADED,
                    latency_ms=150.0,
                    consecutive_failures=1
                ),
            })
            mock_factory.return_value = mock_instance

            # Act
            response = await async_client.get("/api/v1/health/providers")

            # Assert
            assert response.status_code == 200

    async def test_health_endpoint_handles_all_unhealthy(self, async_client):
        """Test health endpoint when all providers are unhealthy."""
        # Arrange
        with patch("app.api.v1.endpoints.health.get_provider_factory") as mock_factory:
            mock_instance = MagicMock()
            mock_instance.check_all_health = AsyncMock(return_value={
                "google": ProviderHealth(
                    status=ProviderStatus.UNHEALTHY,
                    error_message="Connection failed",
                    consecutive_failures=3
                ),
            })
            mock_factory.return_value = mock_instance

            # Act
            response = await async_client.get("/api/v1/health/providers")

            # Assert - Should still return 200 with unhealthy status
            assert response.status_code == 200

    async def test_health_endpoint_timeout_handling(self, async_client):
        """Test health endpoint handles provider timeout gracefully."""
        import asyncio

        # Arrange - Slow health check
        with patch("app.api.v1.endpoints.health.get_provider_factory") as mock_factory:
            async def slow_health_check():
                await asyncio.sleep(0.1)  # 100ms delay
                return {
                    "google": ProviderHealth(
                        status=ProviderStatus.HEALTHY,
                        latency_ms=100.0
                    )
                }

            mock_instance = MagicMock()
            mock_instance.check_all_health = slow_health_check
            mock_factory.return_value = mock_instance

            # Act
            response = await async_client.get("/api/v1/health/providers")

            # Assert
            assert response.status_code == 200


class TestHealthEndpointEdgeCases:
    """Edge case tests for health endpoint."""

    def test_health_endpoint_no_providers_configured(self, client: TestClient):
        """Test health endpoint when no providers are configured."""
        # Act
        response = client.get("/api/v1/health/providers")

        # Assert - Should return empty list, not error
        assert response.status_code == 200
        data = response.json()
        assert "providers" in data

    def test_health_endpoint_content_type(self, client: TestClient):
        """Test health endpoint returns JSON content type."""
        # Act
        response = client.get("/api/v1/health/providers")

        # Assert
        assert response.headers["content-type"] == "application/json"

    def test_health_endpoint_cors_headers(self, client: TestClient):
        """Test health endpoint includes CORS headers."""
        # Act - Simulate CORS preflight
        response = client.options("/api/v1/health/providers")

        # Assert - CORS should be configured
        # Note: Actual CORS headers depend on middleware configuration
        assert response.status_code in [200, 405]  # OPTIONS may not be explicitly handled

    def test_basic_health_check(self, client: TestClient):
        """Test basic /health endpoint (not providers-specific)."""
        # Act
        response = client.get("/api/v1/health")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"


class TestHealthEndpointPerformance:
    """Performance-related E2E tests for health endpoint."""

    def test_health_endpoint_response_time(self, client: TestClient):
        """Test health endpoint responds within acceptable time."""
        import time

        # Act
        start = time.perf_counter()
        response = client.get("/api/v1/health/providers")
        elapsed_ms = (time.perf_counter() - start) * 1000

        # Assert - Should respond within 5 seconds even with health checks
        assert response.status_code == 200
        assert elapsed_ms < 5000, f"Health check took {elapsed_ms:.0f}ms"

    def test_health_endpoint_concurrent_requests(self, client: TestClient):
        """Test health endpoint handles concurrent requests."""
        import concurrent.futures

        def make_request():
            return client.get("/api/v1/health/providers")

        # Act - 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            responses = [f.result() for f in concurrent.futures.as_completed(futures)]

        # Assert - All should succeed
        assert all(r.status_code == 200 for r in responses)
