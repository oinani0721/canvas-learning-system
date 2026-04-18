"""Tests for Story 1.10: Detailed health endpoint with 3-level status."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.main import app

    return TestClient(app, raise_server_exceptions=False)


class TestDetailedHealthEndpoint:
    def test_returns_components(self, client):
        resp = client.get("/api/v1/system/health/detailed")
        assert resp.status_code in (200, 503)
        data = resp.json()["data"]
        assert "overall_status" in data
        assert "components" in data
        assert len(data["components"]) >= 3
        assert data["overall_status"] in ("ready", "degraded", "unavailable")

    def test_component_has_required_fields(self, client):
        resp = client.get("/api/v1/system/health/detailed")
        for comp in resp.json()["data"]["components"]:
            assert "name" in comp
            assert "status" in comp
            assert comp["status"] in ("ready", "degraded", "unavailable")
            assert "latency_ms" in comp
            assert "fix_hint" in comp

    def test_unavailable_core_returns_503(self, client):
        resp = client.get("/api/v1/system/health/detailed")
        data = resp.json()["data"]
        neo4j = next((c for c in data["components"] if c["name"] == "neo4j"), None)
        assert neo4j is not None
        if neo4j["status"] == "unavailable":
            assert resp.status_code == 503


class TestAggregateStatus:
    def test_all_ready(self):
        from app.api.v1.system import ComponentHealth, _aggregate_status

        components = [
            ComponentHealth(name="neo4j", status="ready"),
            ComponentHealth(name="ollama", status="ready"),
        ]
        assert _aggregate_status(components) == "ready"

    def test_non_core_unavailable_is_degraded(self):
        from app.api.v1.system import ComponentHealth, _aggregate_status

        components = [
            ComponentHealth(name="neo4j", status="ready"),
            ComponentHealth(name="ollama", status="unavailable"),
        ]
        assert _aggregate_status(components) == "degraded"

    def test_core_unavailable_is_unavailable(self):
        from app.api.v1.system import ComponentHealth, _aggregate_status

        components = [
            ComponentHealth(name="neo4j", status="unavailable"),
            ComponentHealth(name="ollama", status="ready"),
        ]
        assert _aggregate_status(components) == "unavailable"
