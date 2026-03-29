# Canvas Learning System - Real Neo4j Client Integration Tests
# S33 Migration: Synthetic stubs replaced with real Neo4j test container (port 7692)
"""
Integration tests for Neo4jClient against a REAL Neo4j test container.

Each test creates its own client to avoid event-loop-scope conflicts
with module-scoped fixtures (Python 3.14 / pytest-asyncio 1.3).

Container setup: docker compose --profile test up -d neo4j-test

[Source: S33 test migration]
"""

import os
import uuid

import pytest
from app.clients.neo4j_client import Neo4jClient

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]

NEO4J_TEST_URI = os.getenv("NEO4J_TEST_URI", "bolt://localhost:7692")
NEO4J_TEST_USER = os.getenv("NEO4J_TEST_USER", "neo4j")
NEO4J_TEST_PASSWORD = os.getenv("NEO4J_TEST_PASSWORD", "testpassword")
NEO4J_TEST_DATABASE = os.getenv("NEO4J_TEST_DATABASE", "neo4j")


def _make_client(
    password: str = NEO4J_TEST_PASSWORD,
    use_json_fallback: bool = False,
    storage_path=None,
) -> Neo4jClient:
    """Create a Neo4jClient pointed at the test container."""
    return Neo4jClient(
        uri=NEO4J_TEST_URI,
        user=NEO4J_TEST_USER,
        password=password,
        database=NEO4J_TEST_DATABASE,
        use_json_fallback=use_json_fallback,
        storage_path=storage_path,
    )


async def _cleanup_prefix(client: Neo4jClient, prefix: str) -> None:
    """Remove all test nodes/relationships matching prefix."""
    try:
        await client.run_query(
            "MATCH (n) WHERE n.id STARTS WITH $prefix DETACH DELETE n",
            prefix=prefix,
        )
        await client.run_query(
            "MATCH (c:Concept) WHERE c.name STARTS WITH $prefix DETACH DELETE c",
            prefix=prefix,
        )
    except Exception:
        pass


# =============================================================================
# Connection & Driver Lifecycle
# =============================================================================


class TestRealNeo4jClientConnection:
    """Tests for driver initialization, fallback, and health check."""

    async def test_driver_initialization_and_connectivity(self):
        """Fresh client can initialize, connect, and execute a trivial query."""
        client = _make_client()
        try:
            result = await client.initialize()
            assert result is True
            assert client._initialized is True
            assert client._use_json_fallback is False
            assert client._driver is not None

            rows = await client.run_query("RETURN 1 AS n")
            assert len(rows) >= 1
            assert rows[0]["n"] == 1
        finally:
            await client.cleanup()

    async def test_driver_fallback_on_wrong_credentials(self, tmp_path):
        """Auth failure triggers automatic JSON fallback mode."""
        fallback_path = tmp_path / "fallback.json"
        client = _make_client(
            password="wrong_password_xxx",
            storage_path=fallback_path,
        )
        try:
            result = await client.initialize()
            assert result is True
            assert client._use_json_fallback is True
            assert fallback_path.exists()
        finally:
            await client.cleanup()

    async def test_health_check_real(self):
        """health_check() succeeds and updates internal status fields."""
        client = _make_client()
        try:
            await client.initialize()
            result = await client.health_check()

            assert result is True
            assert client._health_status is True
            assert client._last_health_check is not None
        finally:
            await client.cleanup()


# =============================================================================
# Operations & Metrics
# =============================================================================


class TestRealNeo4jClientOperations:
    """Tests for create/query operations and metrics tracking."""

    async def test_metrics_increment_on_real_queries(self):
        """Metrics counters advance after real write + read operations."""
        client = _make_client()
        prefix = f"test_{uuid.uuid4().hex[:8]}_"
        try:
            await client.initialize()
            initial_queries = client._metrics["total_queries"]

            ok1 = await client.create_learning_relationship(
                user_id=f"{prefix}user1",
                concept=f"{prefix}concept1",
                score=85,
            )
            assert ok1 is True

            ok2 = await client.create_learning_relationship(
                user_id=f"{prefix}user1",
                concept=f"{prefix}concept2",
                score=90,
            )
            assert ok2 is True

            assert client._metrics["total_queries"] >= initial_queries + 2
            assert client._metrics["successful_queries"] >= initial_queries + 2
            assert client._metrics["total_latency_ms"] > 0

            results = await client.get_learning_history(
                user_id=f"{prefix}user1",
            )
            assert len(results) >= 2
        finally:
            await _cleanup_prefix(client, prefix)
            await client.cleanup()

    async def test_cleanup_closes_driver(self):
        """cleanup() closes the driver and resets _initialized."""
        client = _make_client()
        await client.initialize()
        assert client._initialized is True
        assert client._driver is not None

        await client.cleanup()
        assert client._initialized is False
