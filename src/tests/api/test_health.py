"""
Health Endpoint Tests for Canvas Learning System API

Tests for GET /api/v1/health endpoint.

Story 15.6: API文档和测试框架
✅ Verified from Context7:/websites/fastapi_tiangolo (topic: TestClient testing)
"""

import pytest
from datetime import datetime


@pytest.mark.api
class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check_success(self, client, api_v1_prefix):
        """
        Test health check returns healthy status.

        AC: GET /api/v1/health returns 200 with correct schema.
        Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1health
        """
        response = client.get(f"{api_v1_prefix}/health")

        assert response.status_code == 200
        data = response.json()

        # Verify required fields
        assert "status" in data
        assert "app_name" in data
        assert "version" in data
        assert "timestamp" in data

        # Verify values
        assert data["status"] == "healthy"
        assert data["app_name"] == "Canvas Learning System API"
        assert data["version"] == "1.0.0"

    def test_health_check_timestamp_format(self, client, api_v1_prefix):
        """
        Test health check returns valid ISO timestamp.

        AC: timestamp field is valid ISO 8601 format.
        """
        response = client.get(f"{api_v1_prefix}/health")

        assert response.status_code == 200
        data = response.json()

        # Verify timestamp is valid ISO format
        timestamp = data["timestamp"]
        try:
            # Parse ISO format timestamp
            datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except ValueError:
            pytest.fail(f"Invalid timestamp format: {timestamp}")


@pytest.mark.api
class TestRootEndpoint:
    """Tests for root endpoint."""

    def test_root_returns_api_info(self, client):
        """
        Test root endpoint returns API information.

        AC: GET / returns message, version, and docs URLs.
        """
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()

        assert "message" in data
        assert "version" in data
        assert "docs" in data
        assert "redoc" in data
        assert "openapi" in data

    def test_docs_accessible(self, client):
        """
        Test Swagger UI docs are accessible.

        AC: /docs returns HTML page.
        """
        response = client.get("/docs")

        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    def test_redoc_accessible(self, client):
        """
        Test ReDoc documentation is accessible.

        AC: /redoc returns HTML page.
        """
        response = client.get("/redoc")

        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    def test_openapi_spec_accessible(self, client, api_v1_prefix):
        """
        Test OpenAPI spec is accessible.

        AC: /api/v1/openapi.json returns valid OpenAPI spec.
        """
        response = client.get(f"{api_v1_prefix}/openapi.json")

        assert response.status_code == 200
        data = response.json()

        # Verify OpenAPI structure
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data
