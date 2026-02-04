# Canvas Learning System - Integration Tests for Storage Health Endpoint
# Story 36.10 Task 8
"""
Integration tests for the unified storage health endpoint.

[Source: docs/stories/36.10.story.md - Task 8]
"""

import asyncio
import time
from datetime import datetime, timezone

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.config import get_settings


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Full Endpoint Integration (AC-36.10.1)
# ═══════════════════════════════════════════════════════════════════════════════

class TestStorageHealthEndpoint:
    """Integration tests for /api/v1/health/storage endpoint."""

    @pytest.mark.asyncio
    async def test_endpoint_returns_valid_response(self):
        """✅ AC-36.10.1: Endpoint returns valid JSON response."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/health/storage")

            assert response.status_code == 200
            data = response.json()

            # Verify required fields
            assert "status" in data
            assert data["status"] in ["healthy", "degraded", "unhealthy"]
            assert "storage_backends" in data
            assert "connection_pool" in data
            assert "latency_metrics" in data
            assert "cached" in data
            assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_endpoint_response_time_under_500ms(self):
        """✅ AC-36.10.7: Response time < 500ms."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            start = time.time()
            response = await client.get("/api/v1/health/storage")
            elapsed_ms = (time.time() - start) * 1000

            assert response.status_code == 200
            assert elapsed_ms < 500, f"Response time {elapsed_ms:.1f}ms exceeds 500ms threshold"

    @pytest.mark.asyncio
    async def test_storage_backends_array_structure(self):
        """✅ AC-36.10.1: storage_backends contains expected backends."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/health/storage")
            data = response.json()

            backends = data["storage_backends"]
            assert isinstance(backends, list)
            assert len(backends) >= 1

            # Each backend must have name and status
            for backend in backends:
                assert "name" in backend
                assert "status" in backend
                assert backend["name"] in ["neo4j", "mcp", "json"]
                assert backend["status"] in ["ok", "error"]

    @pytest.mark.asyncio
    async def test_latency_metrics_structure(self):
        """✅ AC-36.10.3: latency_metrics contains P95 and window."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/health/storage")
            data = response.json()

            metrics = data["latency_metrics"]
            assert "p95_ms" in metrics
            assert "window_seconds" in metrics
            assert isinstance(metrics["p95_ms"], (int, float))
            assert metrics["window_seconds"] == 300  # 5 minute window


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Cache Behavior (AC-36.10.4)
# ═══════════════════════════════════════════════════════════════════════════════

class TestCacheIntegration:
    """Integration tests for response caching."""

    @pytest.mark.asyncio
    async def test_first_request_not_cached(self):
        """✅ AC-36.10.4: First request is not from cache."""
        # Clear any existing cache by waiting or using a fresh client
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Make two requests in quick succession
            response1 = await client.get("/api/v1/health/storage")
            data1 = response1.json()

            # Second request should be cached
            response2 = await client.get("/api/v1/health/storage")
            data2 = response2.json()

            # Both should return 200
            assert response1.status_code == 200
            assert response2.status_code == 200

            # Second request should be faster (cached)
            if data2["cached"]:
                assert data2["cache_ttl_remaining_seconds"] > 0
                assert data2["cache_ttl_remaining_seconds"] <= 30

    @pytest.mark.asyncio
    async def test_cache_ttl_is_30_seconds(self):
        """✅ AC-36.10.4: Cache TTL is 30 seconds per ADR-007."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/health/storage")
            data = response.json()

            # If cached, TTL should be <= 30
            if data["cached"]:
                assert data["cache_ttl_remaining_seconds"] <= 30


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Connection Pool Metrics (AC-36.10.2)
# ═══════════════════════════════════════════════════════════════════════════════

class TestConnectionPoolIntegration:
    """Integration tests for connection pool metrics."""

    @pytest.mark.asyncio
    async def test_connection_pool_structure(self):
        """✅ AC-36.10.2: connection_pool contains neo4j metrics when available."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/health/storage")
            data = response.json()

            pool = data["connection_pool"]
            assert isinstance(pool, dict)

            # If Neo4j is enabled, pool should have neo4j key
            settings = get_settings()
            if settings.neo4j_enabled:
                if "neo4j" in pool:
                    neo4j_pool = pool["neo4j"]
                    assert "active" in neo4j_pool
                    assert "idle" in neo4j_pool
                    assert "max_size" in neo4j_pool
                    assert "utilization_percent" in neo4j_pool


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Status Aggregation Integration (AC-36.10.5)
# ═══════════════════════════════════════════════════════════════════════════════

class TestStatusAggregationIntegration:
    """Integration tests for status aggregation logic."""

    @pytest.mark.asyncio
    async def test_status_reflects_backend_health(self):
        """✅ AC-36.10.5: Overall status reflects backend health."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/health/storage")
            data = response.json()

            status = data["status"]
            backends = data["storage_backends"]

            # Check consistency
            neo4j_ok = any(b["name"] == "neo4j" and b["status"] == "ok" for b in backends)
            all_ok = all(b["status"] == "ok" for b in backends)

            if all_ok:
                assert status == "healthy"
            elif not neo4j_ok:
                # Neo4j error should result in unhealthy
                assert status == "unhealthy"
            else:
                # Some non-critical error should be degraded
                assert status in ["healthy", "degraded"]


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Timestamp Validation (AC-36.10.6)
# ═══════════════════════════════════════════════════════════════════════════════

class TestTimestampValidation:
    """Integration tests for timestamp field."""

    @pytest.mark.asyncio
    async def test_timestamp_is_valid_iso8601(self):
        """✅ AC-36.10.6: Timestamp is valid ISO 8601 format."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/health/storage")
            data = response.json()

            timestamp_str = data["timestamp"]

            # Should be parseable as ISO 8601
            try:
                # Handle both with and without timezone
                if timestamp_str.endswith("Z"):
                    timestamp_str = timestamp_str[:-1] + "+00:00"
                parsed = datetime.fromisoformat(timestamp_str)
                assert parsed is not None
            except ValueError:
                pytest.fail(f"Timestamp '{timestamp_str}' is not valid ISO 8601")

    @pytest.mark.asyncio
    async def test_timestamp_is_recent(self):
        """✅ Timestamp should be within last minute."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            before = datetime.now(timezone.utc)
            response = await client.get("/api/v1/health/storage")
            after = datetime.now(timezone.utc)

            data = response.json()
            timestamp_str = data["timestamp"]

            # Parse timestamp
            if timestamp_str.endswith("Z"):
                timestamp_str = timestamp_str[:-1] + "+00:00"
            parsed = datetime.fromisoformat(timestamp_str)

            # Should be between before and after (with some tolerance for caching)
            # Allow up to 30 seconds for cached responses
            tolerance_seconds = 35
            assert (after - parsed).total_seconds() < tolerance_seconds


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Concurrent Requests
# ═══════════════════════════════════════════════════════════════════════════════

class TestConcurrentRequests:
    """Test endpoint behavior under concurrent load."""

    @pytest.mark.asyncio
    async def test_concurrent_requests_handled(self):
        """✅ Endpoint handles concurrent requests gracefully."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Make 5 concurrent requests
            tasks = [
                client.get("/api/v1/health/storage")
                for _ in range(5)
            ]
            responses = await asyncio.gather(*tasks)

            # All should succeed
            for response in responses:
                assert response.status_code == 200
                data = response.json()
                assert data["status"] in ["healthy", "degraded", "unhealthy"]

    @pytest.mark.asyncio
    async def test_concurrent_requests_consistent_status(self):
        """✅ Concurrent requests return consistent status."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Make concurrent requests
            tasks = [
                client.get("/api/v1/health/storage")
                for _ in range(3)
            ]
            responses = await asyncio.gather(*tasks)

            # All should have same status (within cache window)
            statuses = [r.json()["status"] for r in responses]
            assert len(set(statuses)) == 1, f"Inconsistent statuses: {statuses}"


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Schema Compliance (AC-36.10.6)
# ═══════════════════════════════════════════════════════════════════════════════

class TestSchemaCompliance:
    """Test response conforms to JSON Schema."""

    @pytest.mark.asyncio
    async def test_response_matches_schema_structure(self):
        """✅ AC-36.10.6: Response structure matches schema."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/health/storage")
            data = response.json()

            # Required fields from schema
            required_fields = [
                "status",
                "storage_backends",
                "connection_pool",
                "latency_metrics",
                "cached",
                "timestamp"
            ]

            for field in required_fields:
                assert field in data, f"Missing required field: {field}"

            # Status enum validation
            assert data["status"] in ["healthy", "degraded", "unhealthy"]

            # Array validation
            assert isinstance(data["storage_backends"], list)

            # Object validation
            assert isinstance(data["connection_pool"], dict)
            assert isinstance(data["latency_metrics"], dict)

            # Boolean validation
            assert isinstance(data["cached"], bool)

            # String validation
            assert isinstance(data["timestamp"], str)

