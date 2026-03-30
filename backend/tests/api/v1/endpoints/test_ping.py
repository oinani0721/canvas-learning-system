"""
Tests for GET /api/v1/ping endpoint.

Acceptance Criteria:
- GET /api/v1/ping returns 200
- Response body is {"status": "pong"}
"""

from fastapi.testclient import TestClient


class TestPingEndpoint:
    """Tests for the ping endpoint."""

    def test_ping_returns_200(self, client: TestClient):
        """GET /api/v1/ping should return HTTP 200."""
        response = client.get("/api/v1/ping")
        assert response.status_code == 200

    def test_ping_returns_pong(self, client: TestClient):
        """GET /api/v1/ping should return {"status": "pong"}."""
        response = client.get("/api/v1/ping")
        assert response.json() == {"status": "pong"}
