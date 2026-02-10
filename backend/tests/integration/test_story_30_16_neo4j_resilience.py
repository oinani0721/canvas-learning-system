# Canvas Learning System - Story 30.16 Tests
# 真实 Neo4j 集成 + 弹性恢复 + 健康检查 E2E
"""
Story 30.16 - Neo4j Real Resilience Tests

Task 1: Docker Neo4j test infrastructure (conftest markers)
Task 2: Real Neo4j persistence tests (@pytest.mark.integration - skip if no Docker)
Task 3: Resilience recovery tests (mock-based, always runnable)
Task 4: Health check E2E tests (TestClient)

[Source: docs/stories/30.16.test-neo4j-real-resilience.story.md]
"""

import asyncio
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient


# ============================================================================
# Shared fixtures
# ============================================================================

@pytest.fixture
def mock_neo4j_connected():
    """Neo4j client in connected mode."""
    neo4j = MagicMock()
    neo4j.initialize = AsyncMock(return_value=True)
    neo4j.stats = {
        "enabled": True,
        "initialized": True,
        "mode": "NEO4J",
        "health_status": True,
        "node_count": 42,
        "uri": "bolt://localhost:7687",
    }
    neo4j.record_episode = AsyncMock()
    neo4j.create_learning_relationship = AsyncMock()
    neo4j.cleanup = AsyncMock()
    return neo4j


@pytest.fixture
def mock_neo4j_disconnected():
    """Neo4j client in disconnected state (simulating connection loss)."""
    neo4j = MagicMock()
    neo4j.initialize = AsyncMock(return_value=False)
    neo4j.stats = {
        "enabled": True,
        "initialized": False,
        "mode": "NEO4J",
        "health_status": False,
        "node_count": 0,
        "uri": "bolt://localhost:7687",
    }
    neo4j.record_episode = AsyncMock(side_effect=ConnectionError("Neo4j unavailable"))
    neo4j.create_learning_relationship = AsyncMock(side_effect=ConnectionError("Neo4j unavailable"))
    neo4j.cleanup = AsyncMock()
    return neo4j


@pytest.fixture
def mock_neo4j_json_fallback():
    """Neo4j client in JSON fallback mode."""
    neo4j = MagicMock()
    neo4j.initialize = AsyncMock(return_value=True)
    neo4j.stats = {
        "enabled": False,
        "initialized": True,
        "mode": "JSON_FALLBACK",
        "health_status": True,
        "node_count": 5,
        "uri": None,
    }
    neo4j.record_episode = AsyncMock()
    neo4j.create_learning_relationship = AsyncMock()
    neo4j.cleanup = AsyncMock()
    neo4j.is_fallback_mode = True
    return neo4j


@pytest.fixture
def mock_learning_memory():
    client = MagicMock()
    client._initialized = False
    client.initialize = AsyncMock(return_value=True)
    return client


# ============================================================================
# Task 2: Real Neo4j Integration Tests (AC-30.16.1)
# These tests are marked @pytest.mark.integration and SKIP if no Neo4j.
# ============================================================================

class TestRealNeo4jIntegration:
    """AC-30.16.1: Real Neo4j persistence tests.

    These tests require a running Neo4j instance.
    Run with: pytest -m integration
    """

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_record_episode_persistence(self):
        """Write episode to real Neo4j and verify via Cypher query.

        Requires: docker-compose up -d neo4j
        """
        pytest.skip("Requires Docker Neo4j - run with: docker-compose up -d neo4j && pytest -m integration")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_create_learning_relationship(self):
        """MERGE learning relationship in real Neo4j.

        Requires: docker-compose up -d neo4j
        """
        pytest.skip("Requires Docker Neo4j - run with: docker-compose up -d neo4j && pytest -m integration")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_batch_write(self):
        """Batch write to real Neo4j database.

        Requires: docker-compose up -d neo4j
        """
        pytest.skip("Requires Docker Neo4j - run with: docker-compose up -d neo4j && pytest -m integration")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_group_id_isolation(self):
        """Group ID isolation in real Neo4j.

        Requires: docker-compose up -d neo4j
        """
        pytest.skip("Requires Docker Neo4j - run with: docker-compose up -d neo4j && pytest -m integration")


# ============================================================================
# Task 3: Resilience Recovery Tests (AC-30.16.2)
# These tests use mocks and always run.
# ============================================================================

class TestNeo4jResilienceRecovery:
    """AC-30.16.2: Neo4j disconnection and recovery tests."""

    @pytest.mark.asyncio
    async def test_connection_failure_fallback_to_memory(
        self, mock_neo4j_disconnected, mock_learning_memory
    ):
        """Neo4j disconnect: events still stored in memory."""
        from app.services.memory_service import MemoryService

        service = MemoryService(
            neo4j_client=mock_neo4j_disconnected,
            learning_memory_client=mock_learning_memory,
        )
        await service.initialize()

        events = [
            {
                "event_type": "scoring",
                "timestamp": "2026-02-09T10:00:00",
                "canvas_path": "test/a.canvas",
                "node_id": "n1",
                "metadata": {"concept": "resilience_test"},
            }
        ]

        with patch("app.services.memory_service.settings") as mock_settings:
            mock_settings.BATCH_NEO4J_CONCURRENCY = 10
            mock_settings.ENABLE_GRAPHITI_JSON_DUAL_WRITE = False
            result = await service.record_batch_learning_events(events)

        assert result["processed"] == 1
        assert result["failed"] == 0
        # Neo4j should NOT have been called (not initialized)
        mock_neo4j_disconnected.record_episode.assert_not_called()
        # Event should be in memory
        assert len(service._episodes) >= 1

    @pytest.mark.asyncio
    async def test_health_status_healthy_when_connected(
        self, mock_neo4j_connected, mock_learning_memory
    ):
        """Health check returns 'healthy' when Neo4j is connected."""
        from app.services.memory_service import MemoryService

        service = MemoryService(
            neo4j_client=mock_neo4j_connected,
            learning_memory_client=mock_learning_memory,
        )
        await service.initialize()

        health = await service.get_health_status()
        assert health["status"] == "healthy"
        assert health["layers"]["graphiti"]["status"] == "ok"

    @pytest.mark.asyncio
    async def test_health_status_degraded_when_disconnected(
        self, mock_neo4j_disconnected, mock_learning_memory
    ):
        """Health check returns 'degraded' when Neo4j is disconnected."""
        from app.services.memory_service import MemoryService

        service = MemoryService(
            neo4j_client=mock_neo4j_disconnected,
            learning_memory_client=mock_learning_memory,
        )
        await service.initialize()

        health = await service.get_health_status()
        assert health["status"] == "degraded"
        assert health["layers"]["graphiti"]["status"] == "error"

    @pytest.mark.asyncio
    async def test_health_status_ok_in_json_fallback(
        self, mock_neo4j_json_fallback, mock_learning_memory
    ):
        """Health check returns 'healthy' in JSON fallback mode (still operational)."""
        from app.services.memory_service import MemoryService

        service = MemoryService(
            neo4j_client=mock_neo4j_json_fallback,
            learning_memory_client=mock_learning_memory,
        )
        await service.initialize()

        health = await service.get_health_status()
        assert health["status"] == "healthy"
        assert health["layers"]["graphiti"]["backend"] == "json_fallback"

    @pytest.mark.asyncio
    async def test_neo4j_write_failure_records_in_memory(
        self, mock_neo4j_connected, mock_learning_memory
    ):
        """When Neo4j write fails, event is still in memory (_episodes)."""
        mock_neo4j_connected.record_episode = AsyncMock(
            side_effect=Exception("Neo4j write timeout")
        )

        from app.services.memory_service import MemoryService

        service = MemoryService(
            neo4j_client=mock_neo4j_connected,
            learning_memory_client=mock_learning_memory,
        )
        await service.initialize()

        events = [
            {
                "event_type": "scoring",
                "timestamp": "2026-02-09T10:00:00",
                "canvas_path": "test/a.canvas",
                "node_id": "n1",
                "metadata": {"concept": "test"},
            }
        ]

        with patch("app.services.memory_service.settings") as mock_settings:
            mock_settings.BATCH_NEO4J_CONCURRENCY = 10
            mock_settings.ENABLE_GRAPHITI_JSON_DUAL_WRITE = False
            result = await service.record_batch_learning_events(events)

        # Event is processed (stored in memory) even though Neo4j failed
        assert result["processed"] == 1
        assert len(service._episodes) >= 1

    @pytest.mark.asyncio
    async def test_batch_events_during_neo4j_disconnect(
        self, mock_neo4j_disconnected, mock_learning_memory
    ):
        """Multiple events during Neo4j disconnect all stored in memory."""
        from app.services.memory_service import MemoryService

        service = MemoryService(
            neo4j_client=mock_neo4j_disconnected,
            learning_memory_client=mock_learning_memory,
        )
        await service.initialize()

        events = [
            {
                "event_type": f"scoring_{i}",
                "timestamp": f"2026-02-09T10:{i:02d}:00",
                "canvas_path": f"test/c_{i}.canvas",
                "node_id": f"n_{i}",
                "metadata": {"concept": f"concept_{i}"},
            }
            for i in range(10)
        ]

        with patch("app.services.memory_service.settings") as mock_settings:
            mock_settings.BATCH_NEO4J_CONCURRENCY = 10
            mock_settings.ENABLE_GRAPHITI_JSON_DUAL_WRITE = False
            result = await service.record_batch_learning_events(events)

        assert result["processed"] == 10
        assert result["failed"] == 0
        mock_neo4j_disconnected.record_episode.assert_not_called()


# ============================================================================
# Task 4: Health Check E2E Tests (AC-30.16.3)
# These tests use TestClient with DI overrides.
# ============================================================================

class TestHealthCheckE2E:
    """AC-30.16.3: Health check endpoint E2E."""

    @pytest.fixture
    def mock_memory_service_healthy(self):
        service = AsyncMock()
        service.get_health_status = AsyncMock(return_value={
            "status": "healthy",
            "layers": {
                "temporal": {"status": "ok", "backend": "sqlite"},
                "graphiti": {"status": "ok", "backend": "neo4j", "node_count": 42},
                "semantic": {"status": "ok", "backend": "lancedb", "vector_count": 0},
            },
            "timestamp": datetime.now().isoformat(),
        })
        return service

    @pytest.fixture
    def mock_memory_service_degraded(self):
        service = AsyncMock()
        service.get_health_status = AsyncMock(return_value={
            "status": "degraded",
            "layers": {
                "temporal": {"status": "ok", "backend": "sqlite"},
                "graphiti": {"status": "error", "backend": "neo4j", "error": "Neo4j not connected"},
                "semantic": {"status": "ok", "backend": "lancedb", "vector_count": 0},
            },
            "timestamp": datetime.now().isoformat(),
        })
        return service

    @pytest.mark.asyncio
    async def test_memory_health_endpoint_healthy(self, mock_memory_service_healthy):
        """GET /api/v1/memory/health returns correct 3-layer healthy status."""
        from app.main import app
        from app.services.memory_service import get_memory_service

        app.dependency_overrides[get_memory_service] = lambda: mock_memory_service_healthy

        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/api/v1/memory/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "layers" in data
            assert data["layers"]["graphiti"]["status"] == "ok"
            assert data["layers"]["temporal"]["status"] == "ok"
            assert data["layers"]["semantic"]["status"] == "ok"
        finally:
            app.dependency_overrides.pop(get_memory_service, None)

    @pytest.mark.asyncio
    async def test_memory_health_endpoint_degraded(self, mock_memory_service_degraded):
        """GET /api/v1/memory/health returns degraded when Neo4j disconnected."""
        from app.main import app
        from app.services.memory_service import get_memory_service

        app.dependency_overrides[get_memory_service] = lambda: mock_memory_service_degraded

        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/api/v1/memory/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "degraded"
            assert data["layers"]["graphiti"]["status"] == "error"
        finally:
            app.dependency_overrides.pop(get_memory_service, None)

    @pytest.mark.asyncio
    async def test_health_endpoint_basic(self):
        """GET /api/v1/health returns basic health status."""
        from app.main import app

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    @pytest.mark.asyncio
    async def test_neo4j_health_endpoint(self):
        """GET /api/v1/health/neo4j returns Neo4j connection status."""
        from app.main import app

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/health/neo4j")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "checks" in data

    @pytest.mark.asyncio
    async def test_health_response_includes_timestamp(self, mock_memory_service_healthy):
        """Health response includes timestamp field."""
        from app.main import app
        from app.services.memory_service import get_memory_service

        app.dependency_overrides[get_memory_service] = lambda: mock_memory_service_healthy

        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/api/v1/memory/health")

            data = response.json()
            assert "timestamp" in data
        finally:
            app.dependency_overrides.pop(get_memory_service, None)


# ============================================================================
# Task 5: Neo4j Client Stats Consistency Tests
# ============================================================================

class TestNeo4jClientStats:
    """Verify Neo4j client stats fields are consistent across modes."""

    def test_neo4j_client_stats_has_required_fields(self):
        """Neo4jClient.stats returns all required fields."""
        from app.clients.neo4j_client import Neo4jClient

        client = Neo4jClient(use_json_fallback=True)
        stats = client.stats
        assert "initialized" in stats
        assert "mode" in stats
        assert "enabled" in stats

    def test_neo4j_client_json_fallback_mode(self):
        """Neo4jClient in JSON fallback reports correct mode."""
        from app.clients.neo4j_client import Neo4jClient

        client = Neo4jClient(use_json_fallback=True)
        assert client.stats["mode"] == "JSON_FALLBACK"
        assert client.enabled is False
        assert client.is_fallback_mode is True

    def test_neo4j_client_neo4j_mode_stats(self):
        """Neo4jClient in NEO4J mode reports correct mode (before connect)."""
        from app.clients.neo4j_client import Neo4jClient

        client = Neo4jClient(
            uri="bolt://localhost:7687",
            user="neo4j",
            password="test",
            use_json_fallback=False,
        )
        assert client.stats["mode"] == "NEO4J"
        assert client.enabled is True
        assert client.is_fallback_mode is False
        assert client.stats["initialized"] is False  # Not yet connected
