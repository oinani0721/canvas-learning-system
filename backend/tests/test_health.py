# Canvas Learning System - Health Check Endpoint Tests
# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: testing)
"""
Tests for the health check endpoint.

These tests verify that the health check endpoint returns correct data
and adheres to the API specification.

[Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1health]
[Source: specs/data/health-check-response.schema.json]
[Source: docs/architecture/coding-standards.md#测试规范]
"""

import pytest
from datetime import datetime
from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Test suite for GET /api/v1/health endpoint."""

    def test_health_check_returns_200(self, client: TestClient):
        """
        Test that health check returns HTTP 200 OK.

        [Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1health]
        """
        response = client.get("/api/v1/health")
        assert response.status_code == 200

    def test_health_check_response_structure(self, client: TestClient):
        """
        Test that health check response has correct structure.

        [Source: specs/data/health-check-response.schema.json]
        Schema requires: status, app_name, version, timestamp
        """
        response = client.get("/api/v1/health")
        data = response.json()

        # Verify all required fields are present
        assert "status" in data
        assert "app_name" in data
        assert "version" in data
        assert "timestamp" in data

    def test_health_check_status_is_healthy(self, client: TestClient):
        """
        Test that health check returns "healthy" status.

        [Source: specs/data/health-check-response.schema.json]
        status enum: ["healthy", "unhealthy"]
        """
        response = client.get("/api/v1/health")
        data = response.json()

        assert data["status"] == "healthy"

    def test_health_check_app_name(self, client: TestClient):
        """
        Test that health check returns correct app name.
        """
        response = client.get("/api/v1/health")
        data = response.json()

        assert data["app_name"] == "Canvas Learning System API (Test)"

    def test_health_check_version(self, client: TestClient):
        """
        Test that health check returns valid version string.
        """
        response = client.get("/api/v1/health")
        data = response.json()

        assert data["version"] == "1.0.0-test"

    def test_health_check_timestamp_format(self, client: TestClient):
        """
        Test that health check returns valid ISO 8601 timestamp.

        [Source: specs/data/health-check-response.schema.json]
        timestamp format: date-time (ISO 8601)
        """
        response = client.get("/api/v1/health")
        data = response.json()

        # Verify timestamp can be parsed as ISO 8601
        timestamp_str = data["timestamp"]
        # FastAPI serializes datetime as ISO format
        parsed = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        assert parsed is not None

    def test_health_check_content_type(self, client: TestClient):
        """
        Test that health check returns JSON content type.
        """
        response = client.get("/api/v1/health")
        assert response.headers["content-type"] == "application/json"


class TestRootEndpoint:
    """Test suite for GET / root endpoint."""

    def test_root_returns_200(self, client: TestClient):
        """Test that root endpoint returns HTTP 200 OK."""
        response = client.get("/")
        assert response.status_code == 200

    def test_root_response_structure(self, client: TestClient):
        """Test that root response has correct structure."""
        response = client.get("/")
        data = response.json()

        assert "message" in data
        assert "version" in data
        assert "docs" in data
        assert "health" in data

    def test_root_message(self, client: TestClient):
        """Test that root returns correct message."""
        response = client.get("/")
        data = response.json()

        assert data["message"] == "Canvas Learning System API"

    def test_root_docs_status(self, client: TestClient):
        """
        Test that docs status is correctly reported.

        Note: The root endpoint uses the global settings object directly,
        which is loaded at module import time. Default DEBUG=False.
        """
        response = client.get("/")
        data = response.json()

        # Global settings has DEBUG=False by default
        # docs is either "/docs" or "disabled" depending on DEBUG setting
        assert data["docs"] in ["/docs", "disabled"]

    def test_root_health_path(self, client: TestClient):
        """Test that root returns correct health endpoint path."""
        response = client.get("/")
        data = response.json()

        assert data["health"] == "/api/v1/health"
