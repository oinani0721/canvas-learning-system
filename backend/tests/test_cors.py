# Canvas Learning System - CORS Configuration Tests
# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: CORSMiddleware)
"""
Tests for CORS middleware configuration.

These tests verify that CORS is properly configured to allow
Obsidian plugin access.

[Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#CORS配置]
[Source: docs/stories/15.1.story.md#AC4]
"""

from fastapi.testclient import TestClient


class TestCORSConfiguration:
    """Test suite for CORS middleware configuration."""

    def test_cors_allows_localhost(self, client: TestClient):
        """
        Test that CORS allows requests from localhost.

        [Source: docs/stories/15.1.story.md#AC4]
        """
        response = client.options(
            "/api/v1/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET"
            }
        )

        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
        assert response.headers["access-control-allow-origin"] == "http://localhost:3000"

    def test_cors_allows_127_0_0_1(self, client: TestClient):
        """Test that CORS allows requests from 127.0.0.1."""
        response = client.options(
            "/api/v1/health",
            headers={
                "Origin": "http://127.0.0.1:3000",
                "Access-Control-Request-Method": "GET"
            }
        )

        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
        assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:3000"

    def test_cors_allows_credentials(self, client: TestClient):
        """Test that CORS allows credentials."""
        response = client.options(
            "/api/v1/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET"
            }
        )

        assert "access-control-allow-credentials" in response.headers
        assert response.headers["access-control-allow-credentials"] == "true"

    def test_cors_allows_all_methods(self, client: TestClient):
        """Test that CORS allows all HTTP methods."""
        for method in ["GET", "POST", "PUT", "DELETE", "OPTIONS"]:
            response = client.options(
                "/api/v1/health",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": method
                }
            )
            assert response.status_code == 200

    def test_cors_headers_in_response(self, client: TestClient):
        """Test that CORS headers are included in regular responses."""
        response = client.get(
            "/api/v1/health",
            headers={"Origin": "http://localhost:3000"}
        )

        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
