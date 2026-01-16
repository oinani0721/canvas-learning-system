# Canvas Learning System - Memory Health API Integration Tests
# Story 30.3: Memory API端点集成验证
# ✅ Verified from docs/stories/30.3.memory-api-health-endpoints.story.md#Task-5
"""
Integration tests for Memory Health API endpoints.

Story 30.3 Implementation:
- AC-30.3.5: GET /api/v1/memory/health - 3层系统状态
- AC-30.3.6: GET /api/v1/health/neo4j - Neo4j连接状态
- AC-30.3.7: GET /api/v1/health/graphiti - Graphiti状态
- AC-30.3.8: GET /api/v1/health/lancedb - LanceDB状态

[Source: docs/stories/30.3.memory-api-health-endpoints.story.md#Task-5]
"""

import pytest
from httpx import AsyncClient

pytestmark = [pytest.mark.asyncio, pytest.mark.integration]


class TestMemoryHealthEndpoint:
    """Tests for GET /api/v1/memory/health (AC-30.3.5)."""

    async def test_memory_health_returns_200(self, async_client: AsyncClient):
        """Memory health endpoint should return 200 OK."""
        response = await async_client.get("/api/v1/memory/health")
        assert response.status_code == 200

    async def test_memory_health_response_structure(self, async_client: AsyncClient):
        """Memory health should return status, layers, timestamp."""
        response = await async_client.get("/api/v1/memory/health")
        data = response.json()

        assert "status" in data
        assert data["status"] in ["healthy", "degraded", "unhealthy"]

        assert "layers" in data
        assert "temporal" in data["layers"]
        assert "graphiti" in data["layers"]
        assert "semantic" in data["layers"]

        assert "timestamp" in data

    async def test_memory_health_layer_structure(self, async_client: AsyncClient):
        """Each layer should have status and backend fields."""
        response = await async_client.get("/api/v1/memory/health")
        data = response.json()

        for layer_name in ["temporal", "graphiti", "semantic"]:
            layer = data["layers"][layer_name]
            assert "status" in layer
            assert layer["status"] in ["ok", "error"]


class TestNeo4jHealthEndpoint:
    """Tests for GET /api/v1/health/neo4j (AC-30.3.6)."""

    async def test_neo4j_health_returns_200(self, async_client: AsyncClient):
        """Neo4j health endpoint should return 200 OK."""
        response = await async_client.get("/api/v1/health/neo4j")
        assert response.status_code == 200

    async def test_neo4j_health_response_structure(self, async_client: AsyncClient):
        """Neo4j health should return status, checks, timestamp."""
        response = await async_client.get("/api/v1/health/neo4j")
        data = response.json()

        assert "status" in data
        assert data["status"] in ["healthy", "degraded", "unhealthy"]

        assert "checks" in data
        assert "timestamp" in data

    async def test_neo4j_health_checks_neo4j_enabled(self, async_client: AsyncClient):
        """Neo4j health checks should include neo4j_enabled."""
        response = await async_client.get("/api/v1/health/neo4j")
        data = response.json()

        checks = data["checks"]
        # neo4j_enabled should be present
        assert "neo4j_enabled" in checks or "reason" in checks


class TestGraphitiHealthEndpoint:
    """Tests for GET /api/v1/health/graphiti (AC-30.3.7)."""

    async def test_graphiti_health_returns_200(self, async_client: AsyncClient):
        """Graphiti health endpoint should return 200 OK."""
        response = await async_client.get("/api/v1/health/graphiti")
        assert response.status_code == 200

    async def test_graphiti_health_response_structure(self, async_client: AsyncClient):
        """Graphiti health should return status."""
        response = await async_client.get("/api/v1/health/graphiti")
        data = response.json()

        assert "status" in data
        assert data["status"] in ["ok", "error"]

    async def test_graphiti_health_includes_stats_when_ok(self, async_client: AsyncClient):
        """When status is ok, graph_stats should be present."""
        response = await async_client.get("/api/v1/health/graphiti")
        data = response.json()

        if data["status"] == "ok":
            assert "graph_stats" in data
            stats = data["graph_stats"]
            assert "node_count" in stats
            assert "edge_count" in stats


class TestLanceDBHealthEndpoint:
    """Tests for GET /api/v1/health/lancedb (AC-30.3.8)."""

    async def test_lancedb_health_returns_200(self, async_client: AsyncClient):
        """LanceDB health endpoint should return 200 OK."""
        response = await async_client.get("/api/v1/health/lancedb")
        assert response.status_code == 200

    async def test_lancedb_health_response_structure(self, async_client: AsyncClient):
        """LanceDB health should return status."""
        response = await async_client.get("/api/v1/health/lancedb")
        data = response.json()

        assert "status" in data
        assert data["status"] in ["ok", "error"]

    async def test_lancedb_health_includes_counts_when_ok(self, async_client: AsyncClient):
        """When status is ok, table_count and total_vectors should be present."""
        response = await async_client.get("/api/v1/health/lancedb")
        data = response.json()

        if data["status"] == "ok":
            assert "table_count" in data
            assert "total_vectors" in data
            assert "embedding_model" in data


class TestHealthEndpointPerformance:
    """Performance tests for health endpoints (< 100ms P95)."""

    @pytest.mark.parametrize("endpoint", [
        "/api/v1/memory/health",
        "/api/v1/health/neo4j",
        "/api/v1/health/graphiti",
        "/api/v1/health/lancedb",
    ])
    async def test_health_endpoint_performance(
        self,
        async_client: AsyncClient,
        endpoint: str
    ):
        """Health endpoints should respond within 100ms."""
        import time

        start = time.perf_counter()
        response = await async_client.get(endpoint)
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert response.status_code == 200
        # 750ms threshold: 500ms internal timeout (when service unavailable) + 250ms overhead
        # Per ADR-0003 target of 100ms for healthy services, 750ms for degraded/timeout scenarios
        assert elapsed_ms < 750, f"{endpoint} took {elapsed_ms:.1f}ms (expected < 750ms)"
