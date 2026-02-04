"""
Unit tests for Neo4j Health Check Endpoint.

Story 30.1 - AC 4: Neo4j健康检查端点测试

[Source: docs/stories/30.1.story.md - AC 4]
[Source: specs/data/neo4j-health-response.schema.json]
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest_asyncio

from app.api.v1.endpoints.health import (
    Neo4jHealthChecks,
    Neo4jHealthResponse,
    check_neo4j_health,
    _test_neo4j_connection,
)


class TestNeo4jHealthResponse:
    """Test Neo4jHealthResponse model."""

    def test_healthy_response(self):
        """Test healthy status response structure."""
        response = Neo4jHealthResponse(
            status="healthy",
            checks=Neo4jHealthChecks(
                neo4j_enabled=True,
                neo4j_connection=True,
                driver_initialized=True,
                database_accessible=True,
                uri="bolt://localhost:7687"
            ),
            cached=False,
            timestamp=datetime.now(timezone.utc)
        )

        assert response.status == "healthy"
        assert response.checks.neo4j_enabled is True
        assert response.checks.neo4j_connection is True
        assert response.checks.uri == "bolt://localhost:7687"
        assert response.cached is False

    def test_degraded_response(self):
        """Test degraded status response structure."""
        response = Neo4jHealthResponse(
            status="degraded",
            checks=Neo4jHealthChecks(
                neo4j_enabled=False,
                reason="Neo4j is disabled in configuration"
            ),
            cached=False,
            timestamp=datetime.now(timezone.utc)
        )

        assert response.status == "degraded"
        assert response.checks.neo4j_enabled is False
        assert response.checks.reason == "Neo4j is disabled in configuration"

    def test_unhealthy_response(self):
        """Test unhealthy status response structure."""
        response = Neo4jHealthResponse(
            status="unhealthy",
            checks=Neo4jHealthChecks(
                neo4j_enabled=True,
                neo4j_connection=False,
                error="Connection timeout (>500ms)"
            ),
            cached=False,
            timestamp=datetime.now(timezone.utc)
        )

        assert response.status == "unhealthy"
        assert response.checks.neo4j_enabled is True
        assert response.checks.neo4j_connection is False
        assert response.checks.error == "Connection timeout (>500ms)"


class TestNeo4jHealthEndpoint:
    """Test check_neo4j_health endpoint."""

    @pytest.mark.asyncio
    async def test_neo4j_disabled(self):
        """Test response when Neo4j is disabled in configuration."""
        # Mock settings with NEO4J_ENABLED=False
        mock_settings = MagicMock()
        mock_settings.neo4j_enabled = False

        response = await check_neo4j_health(settings=mock_settings)

        assert response.status == "degraded"
        assert response.checks.neo4j_enabled is False
        assert response.checks.reason == "Neo4j is disabled in configuration"

    @pytest.mark.asyncio
    async def test_neo4j_connection_success(self):
        """Test response when Neo4j connection succeeds."""
        mock_settings = MagicMock()
        mock_settings.neo4j_enabled = True
        mock_settings.neo4j_uri = "bolt://localhost:7687"

        with patch(
            "app.api.v1.endpoints.health._test_neo4j_connection",
            new_callable=AsyncMock
        ) as mock_test:
            mock_test.return_value = True

            response = await check_neo4j_health(settings=mock_settings)

            assert response.status == "healthy"
            assert response.checks.neo4j_enabled is True
            assert response.checks.neo4j_connection is True
            assert response.checks.database_accessible is True
            assert response.checks.uri == "bolt://localhost:7687"

    @pytest.mark.asyncio
    async def test_neo4j_connection_timeout(self):
        """Test response when Neo4j connection times out."""
        import asyncio

        mock_settings = MagicMock()
        mock_settings.neo4j_enabled = True

        with patch(
            "app.api.v1.endpoints.health._test_neo4j_connection",
            new_callable=AsyncMock
        ) as mock_test:
            mock_test.side_effect = asyncio.TimeoutError()

            response = await check_neo4j_health(settings=mock_settings)

            assert response.status == "unhealthy"
            assert response.checks.neo4j_enabled is True
            assert response.checks.neo4j_connection is False
            assert response.checks.error == "Connection timeout (>500ms)"

    @pytest.mark.asyncio
    async def test_neo4j_connection_error(self):
        """Test response when Neo4j connection fails with error."""
        mock_settings = MagicMock()
        mock_settings.neo4j_enabled = True

        with patch(
            "app.api.v1.endpoints.health._test_neo4j_connection",
            new_callable=AsyncMock
        ) as mock_test:
            mock_test.side_effect = Exception("Connection refused")

            response = await check_neo4j_health(settings=mock_settings)

            assert response.status == "unhealthy"
            assert response.checks.neo4j_enabled is True
            assert response.checks.neo4j_connection is False
            assert "Connection refused" in response.checks.error


class TestNeo4jHealthResponseSchema:
    """Test response conforms to neo4j-health-response.schema.json."""

    def test_status_enum_values(self):
        """Test status field accepts only valid enum values."""
        # Valid values
        for status in ["healthy", "degraded", "unhealthy"]:
            response = Neo4jHealthResponse(
                status=status,
                checks=Neo4jHealthChecks(),
                cached=False,
                timestamp=datetime.now(timezone.utc)
            )
            assert response.status == status

    def test_timestamp_format(self):
        """Test timestamp is in ISO 8601 format."""
        response = Neo4jHealthResponse(
            status="healthy",
            checks=Neo4jHealthChecks(neo4j_enabled=True),
            cached=False,
            timestamp=datetime.now(timezone.utc)
        )

        # Should be able to serialize to ISO format
        timestamp_str = response.timestamp.isoformat()
        assert "T" in timestamp_str

    def test_checks_optional_fields(self):
        """Test checks object handles optional fields correctly."""
        # All fields are optional
        checks = Neo4jHealthChecks()
        assert checks.neo4j_enabled is None
        assert checks.neo4j_connection is None
        assert checks.uri is None
        assert checks.error is None

        # Can set individual fields
        checks_with_data = Neo4jHealthChecks(
            neo4j_enabled=True,
            neo4j_connection=True
        )
        assert checks_with_data.neo4j_enabled is True
        assert checks_with_data.neo4j_connection is True
        assert checks_with_data.uri is None
