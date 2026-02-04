"""
Unit tests for Neo4jClient with AsyncGraphDatabase driver.

Story 30.2: Neo4jClient真实驱动实现
- AC-1: AsyncGraphDatabase connection replaces JSON storage
- AC-2: Connection pool (50 connections, 30s timeout, 3600s lifetime)
- AC-3: JSON Fallback mode preserved (NEO4J_ENABLED=false)
- AC-4: Write latency < 200ms P95
- AC-5: Retry mechanism (3 times, exponential backoff 1s, 2s, 4s)

[Source: docs/stories/30.2.story.md]
"""

import asyncio
import json
import pytest
import tempfile
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest_asyncio

from app.clients.neo4j_client import (
    Neo4jClient,
    get_neo4j_client,
    reset_neo4j_client,
    DEFAULT_STORAGE_PATH,
    RETRYABLE_EXCEPTIONS,
)


class TestNeo4jClientInitialization:
    """Test Neo4jClient initialization modes."""

    def test_init_with_default_params(self):
        """Test initialization with default parameters."""
        client = Neo4jClient()

        assert client._uri == "bolt://localhost:7687"
        assert client._user == "neo4j"
        assert client._database == "neo4j"
        assert client._max_connection_pool_size == 50
        assert client._connection_acquisition_timeout == 30
        assert client._max_connection_lifetime == 3600
        assert client._retry_attempts == 3
        assert client._retry_delay_base == 1.0
        assert client._initialized is False
        assert client._use_json_fallback is False

    def test_init_with_json_fallback(self):
        """Test initialization with JSON fallback mode."""
        client = Neo4jClient(use_json_fallback=True)

        assert client._use_json_fallback is True
        assert client.is_fallback_mode is True
        assert client.enabled is False  # enabled=False when in fallback

    def test_init_with_custom_params(self):
        """Test initialization with custom parameters - AC-2."""
        client = Neo4jClient(
            uri="bolt://custom:7687",
            user="custom_user",
            password="custom_pass",
            database="custom_db",
            max_connection_pool_size=100,
            connection_acquisition_timeout=60,
            max_connection_lifetime=7200,
            retry_attempts=5,
            retry_delay_base=2.0,
            retry_max_delay=20.0,
        )

        assert client._uri == "bolt://custom:7687"
        assert client._user == "custom_user"
        assert client._password == "custom_pass"
        assert client._database == "custom_db"
        assert client._max_connection_pool_size == 100
        assert client._connection_acquisition_timeout == 60
        assert client._max_connection_lifetime == 7200
        assert client._retry_attempts == 5
        assert client._retry_delay_base == 2.0
        assert client._retry_max_delay == 20.0

    def test_stats_property(self):
        """Test stats property returns correct structure."""
        client = Neo4jClient(use_json_fallback=True)
        stats = client.stats

        assert "enabled" in stats
        assert "initialized" in stats
        assert "mode" in stats
        assert "metrics" in stats
        assert stats["mode"] == "JSON_FALLBACK"


class TestNeo4jClientJsonFallback:
    """Test Neo4jClient JSON fallback mode - AC-3."""

    @pytest.fixture
    def temp_storage_path(self, tmp_path):
        """Create temporary storage path for tests."""
        return tmp_path / "test_neo4j_memory.json"

    @pytest.mark.asyncio
    async def test_json_fallback_initialization(self, temp_storage_path):
        """Test JSON fallback mode initialization creates storage file."""
        client = Neo4jClient(
            use_json_fallback=True,
            storage_path=temp_storage_path
        )

        result = await client.initialize()

        assert result is True
        assert client._initialized is True
        assert temp_storage_path.exists()

    @pytest.mark.asyncio
    async def test_json_fallback_loads_existing_data(self, temp_storage_path):
        """Test JSON fallback mode loads existing data."""
        # Create existing data
        existing_data = {
            "users": [{"id": "user-1", "created_at": "2024-01-01T00:00:00"}],
            "concepts": [{"id": "concept-1", "name": "Test Concept"}],
            "relationships": []
        }
        temp_storage_path.parent.mkdir(parents=True, exist_ok=True)
        with open(temp_storage_path, "w") as f:
            json.dump(existing_data, f)

        client = Neo4jClient(
            use_json_fallback=True,
            storage_path=temp_storage_path
        )
        await client.initialize()

        assert len(client._data["users"]) == 1
        assert client._data["users"][0]["id"] == "user-1"

    @pytest.mark.asyncio
    async def test_create_learning_relationship_json_fallback(self, temp_storage_path):
        """Test creating learning relationship in JSON fallback mode."""
        client = Neo4jClient(
            use_json_fallback=True,
            storage_path=temp_storage_path
        )
        await client.initialize()

        result = await client.create_learning_relationship(
            user_id="test-user",
            concept="Test Concept",
            score=85
        )

        assert result is True
        assert len(client._data["users"]) == 1
        assert len(client._data["concepts"]) == 1
        assert len(client._data["relationships"]) == 1

        rel = client._data["relationships"][0]
        assert rel["user_id"] == "test-user"
        assert rel["concept_name"] == "Test Concept"
        assert rel["last_score"] == 85

    @pytest.mark.asyncio
    async def test_get_review_suggestions_json_fallback(self, temp_storage_path):
        """Test getting review suggestions in JSON fallback mode."""
        # Create data with past due review
        past_date = "2024-01-01T00:00:00"
        existing_data = {
            "users": [{"id": "user-1", "created_at": "2024-01-01T00:00:00"}],
            "concepts": [{"id": "concept-1", "name": "Test Concept"}],
            "relationships": [{
                "id": "rel-1",
                "user_id": "user-1",
                "concept_id": "concept-1",
                "concept_name": "Test Concept",
                "timestamp": past_date,
                "last_score": 80,
                "next_review": past_date,
                "review_count": 1
            }]
        }
        temp_storage_path.parent.mkdir(parents=True, exist_ok=True)
        with open(temp_storage_path, "w") as f:
            json.dump(existing_data, f)

        client = Neo4jClient(
            use_json_fallback=True,
            storage_path=temp_storage_path
        )
        await client.initialize()

        suggestions = await client.get_review_suggestions("user-1")

        assert len(suggestions) == 1
        assert suggestions[0]["concept"] == "Test Concept"
        assert suggestions[0]["priority"] == "high"  # review_count < 3

    @pytest.mark.asyncio
    async def test_get_concept_history_json_fallback(self, temp_storage_path):
        """Test getting concept history in JSON fallback mode."""
        existing_data = {
            "users": [{"id": "user-1"}],
            "concepts": [{"id": "concept-1", "name": "Test Concept"}],
            "relationships": [{
                "id": "rel-1",
                "user_id": "user-1",
                "concept_id": "concept-1",
                "concept_name": "Test Concept",
                "timestamp": "2024-01-01T00:00:00",
                "last_score": 90,
                "review_count": 3
            }]
        }
        temp_storage_path.parent.mkdir(parents=True, exist_ok=True)
        with open(temp_storage_path, "w") as f:
            json.dump(existing_data, f)

        client = Neo4jClient(
            use_json_fallback=True,
            storage_path=temp_storage_path
        )
        await client.initialize()

        history = await client.get_concept_history("concept-1", user_id="user-1")

        assert len(history) == 1
        assert history[0]["concept"] == "Test Concept"
        assert history[0]["score"] == 90


class TestNeo4jClientDriver:
    """Test Neo4jClient with real Neo4j driver - AC-1, AC-2."""

    @pytest.mark.asyncio
    async def test_driver_initialization_success(self):
        """Test successful driver initialization with mocked Neo4j."""
        client = Neo4jClient(
            uri="bolt://localhost:7687",
            user="neo4j",
            password="test_password"
        )

        # Mock the AsyncGraphDatabase.driver
        with patch("app.clients.neo4j_client.AsyncGraphDatabase") as mock_agd:
            mock_driver = AsyncMock()
            mock_driver.verify_connectivity = AsyncMock(return_value=None)
            mock_agd.driver.return_value = mock_driver

            result = await client.initialize()

            assert result is True
            assert client._initialized is True
            assert client._use_json_fallback is False

            # Verify driver was created with correct pool config - AC-2
            mock_agd.driver.assert_called_once()
            call_kwargs = mock_agd.driver.call_args[1]
            assert call_kwargs["max_connection_pool_size"] == 50
            assert call_kwargs["connection_acquisition_timeout"] == 30
            assert call_kwargs["max_connection_lifetime"] == 3600

    @pytest.mark.asyncio
    async def test_driver_initialization_fallback_on_failure(self, tmp_path):
        """Test fallback to JSON when Neo4j connection fails - AC-3."""
        storage_path = tmp_path / "fallback_test.json"
        client = Neo4jClient(
            uri="bolt://localhost:7687",
            user="neo4j",
            password="wrong_password",
            storage_path=storage_path
        )

        # Mock driver creation to raise AuthError
        with patch("app.clients.neo4j_client.AsyncGraphDatabase") as mock_agd:
            from neo4j.exceptions import AuthError
            mock_agd.driver.side_effect = AuthError("Authentication failed")

            result = await client.initialize()

            assert result is True  # Should succeed via fallback
            assert client._use_json_fallback is True
            assert storage_path.exists()

    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Test health check returns True when Neo4j is healthy."""
        client = Neo4jClient()

        with patch("app.clients.neo4j_client.AsyncGraphDatabase") as mock_agd:
            mock_driver = AsyncMock()
            mock_driver.verify_connectivity = AsyncMock(return_value=None)
            mock_agd.driver.return_value = mock_driver

            await client.initialize()
            result = await client.health_check()

            assert result is True
            assert client._health_status is True
            assert client._last_health_check is not None

    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        """Test health check returns False when Neo4j is unhealthy."""
        client = Neo4jClient()

        with patch("app.clients.neo4j_client.AsyncGraphDatabase") as mock_agd:
            mock_driver = AsyncMock()
            mock_driver.verify_connectivity = AsyncMock(return_value=None)
            mock_agd.driver.return_value = mock_driver

            await client.initialize()

            # Now make health check fail
            mock_driver.verify_connectivity = AsyncMock(
                side_effect=Exception("Connection lost")
            )

            result = await client.health_check()

            assert result is False
            assert client._health_status is False

    @pytest.mark.asyncio
    async def test_health_check_json_fallback(self, tmp_path):
        """Test health check always returns True in JSON fallback mode."""
        storage_path = tmp_path / "health_test.json"
        client = Neo4jClient(
            use_json_fallback=True,
            storage_path=storage_path
        )
        await client.initialize()

        result = await client.health_check()

        assert result is True
        assert client._health_status is True


class TestNeo4jClientRetry:
    """Test Neo4jClient retry mechanism - AC-5."""

    @pytest.mark.asyncio
    async def test_retry_on_transient_error(self):
        """Test retry mechanism on transient errors - AC-5."""
        client = Neo4jClient(
            retry_attempts=3,
            retry_delay_base=0.1,  # Fast retries for test
            retry_max_delay=1.0
        )

        with patch("app.clients.neo4j_client.AsyncGraphDatabase") as mock_agd:
            mock_driver = AsyncMock()
            mock_driver.verify_connectivity = AsyncMock(return_value=None)

            # Create mock result
            mock_result = AsyncMock()
            mock_result.data = AsyncMock(return_value=[{"count": 1}])

            from neo4j.exceptions import TransientError
            call_count = [0]

            async def mock_run(query, params):
                call_count[0] += 1
                if call_count[0] < 3:
                    raise TransientError("Transient error")
                return mock_result

            # Create async context manager mock for session
            mock_session = AsyncMock()
            mock_session.run = mock_run

            # Session returns an async context manager
            async def session_context_manager(*args, **kwargs):
                return mock_session

            mock_driver.session = MagicMock(return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=mock_session),
                __aexit__=AsyncMock(return_value=None)
            ))

            mock_agd.driver.return_value = mock_driver

            await client.initialize()

            # This should retry and eventually succeed
            result = await client.run_query("RETURN 1 as count")

            assert call_count[0] == 3  # Failed twice, succeeded on third try
            assert result == [{"count": 1}]

    @pytest.mark.asyncio
    async def test_fallback_after_max_retries(self, tmp_path):
        """Test fallback to JSON after max retries exhausted."""
        storage_path = tmp_path / "retry_fallback.json"
        client = Neo4jClient(
            retry_attempts=2,
            retry_delay_base=0.1,
            storage_path=storage_path
        )

        with patch("app.clients.neo4j_client.AsyncGraphDatabase") as mock_agd:
            mock_driver = AsyncMock()
            mock_driver.verify_connectivity = AsyncMock(return_value=None)
            mock_driver.close = AsyncMock()

            from neo4j.exceptions import ServiceUnavailable

            # Create async context manager mock for session that always fails
            mock_session = AsyncMock()
            mock_session.run = AsyncMock(side_effect=ServiceUnavailable("Service down"))

            mock_driver.session = MagicMock(return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=mock_session),
                __aexit__=AsyncMock(return_value=None)
            ))

            mock_agd.driver.return_value = mock_driver

            await client.initialize()

            # Run query that will fail and trigger fallback
            # Use a query that JSON fallback can handle
            result = await client.run_query(
                "MERGE (u:User {id: $userId}) MERGE (c:Concept {name: $concept})",
                userId="test-user",
                concept="Test Concept"
            )

            # Should have fallen back to JSON mode
            assert client._use_json_fallback is True


class TestNeo4jClientMetrics:
    """Test Neo4jClient performance metrics - AC-4."""

    @pytest.mark.asyncio
    async def test_metrics_tracking(self, tmp_path):
        """Test query metrics are tracked correctly."""
        storage_path = tmp_path / "metrics_test.json"
        client = Neo4jClient(
            use_json_fallback=True,
            storage_path=storage_path
        )
        await client.initialize()

        # Execute a few queries
        await client.create_learning_relationship("user-1", "concept-1", 80)
        await client.create_learning_relationship("user-1", "concept-2", 90)

        metrics = client._metrics

        assert metrics["total_queries"] == 2
        assert metrics["successful_queries"] == 2
        assert metrics["failed_queries"] == 0
        assert metrics["total_latency_ms"] > 0

    @pytest.mark.asyncio
    async def test_latency_warning(self, tmp_path, caplog):
        """Test warning is logged when latency exceeds 200ms - AC-4."""
        import logging

        storage_path = tmp_path / "latency_test.json"
        client = Neo4jClient(
            use_json_fallback=True,
            storage_path=storage_path
        )
        await client.initialize()

        # Mock time.perf_counter to simulate slow query
        original_perf_counter = time.perf_counter
        call_count = [0]

        def mock_perf_counter():
            call_count[0] += 1
            if call_count[0] == 1:
                return 0  # Start time
            return 0.25  # 250ms later (exceeds 200ms threshold)

        with patch("app.clients.neo4j_client.time.perf_counter", mock_perf_counter):
            with caplog.at_level(logging.WARNING):
                await client.create_learning_relationship("user-1", "concept-1", 80)

        # Check warning was logged
        assert any("exceeded 200ms" in record.message for record in caplog.records)


class TestNeo4jClientSingleton:
    """Test Neo4jClient singleton pattern."""

    def setup_method(self):
        """Reset singleton before each test."""
        reset_neo4j_client()

    def teardown_method(self):
        """Reset singleton after each test."""
        reset_neo4j_client()

    def test_get_neo4j_client_singleton(self):
        """Test get_neo4j_client returns singleton."""
        with patch("app.config.settings") as mock_settings:
            mock_settings.neo4j_enabled = False  # Force JSON fallback
            mock_settings.neo4j_uri = "bolt://localhost:7687"
            mock_settings.neo4j_user = "neo4j"
            mock_settings.neo4j_password = ""
            mock_settings.neo4j_database = "neo4j"
            mock_settings.neo4j_max_connection_pool_size = 50
            mock_settings.neo4j_connection_timeout = 30
            mock_settings.neo4j_max_connection_lifetime = 3600
            mock_settings.neo4j_retry_attempts = 3
            mock_settings.neo4j_retry_delay_base = 1.0
            mock_settings.neo4j_retry_max_delay = 10.0

            client1 = get_neo4j_client()
            client2 = get_neo4j_client()

            assert client1 is client2

    def test_reset_neo4j_client(self):
        """Test reset_neo4j_client clears singleton."""
        with patch("app.config.settings") as mock_settings:
            mock_settings.neo4j_enabled = False
            mock_settings.neo4j_uri = "bolt://localhost:7687"
            mock_settings.neo4j_user = "neo4j"
            mock_settings.neo4j_password = ""
            mock_settings.neo4j_database = "neo4j"
            mock_settings.neo4j_max_connection_pool_size = 50
            mock_settings.neo4j_connection_timeout = 30
            mock_settings.neo4j_max_connection_lifetime = 3600
            mock_settings.neo4j_retry_attempts = 3
            mock_settings.neo4j_retry_delay_base = 1.0
            mock_settings.neo4j_retry_max_delay = 10.0

            client1 = get_neo4j_client()
            reset_neo4j_client()
            client2 = get_neo4j_client()

            assert client1 is not client2


class TestNeo4jClientCleanup:
    """Test Neo4jClient cleanup."""

    @pytest.mark.asyncio
    async def test_cleanup_json_fallback(self, tmp_path):
        """Test cleanup in JSON fallback mode."""
        storage_path = tmp_path / "cleanup_test.json"
        client = Neo4jClient(
            use_json_fallback=True,
            storage_path=storage_path
        )
        await client.initialize()

        await client.cleanup()

        assert client._initialized is False

    @pytest.mark.asyncio
    async def test_cleanup_neo4j_driver(self):
        """Test cleanup closes Neo4j driver."""
        client = Neo4jClient()

        with patch("app.clients.neo4j_client.AsyncGraphDatabase") as mock_agd:
            mock_driver = AsyncMock()
            mock_driver.verify_connectivity = AsyncMock(return_value=None)
            mock_driver.close = AsyncMock()
            mock_agd.driver.return_value = mock_driver

            await client.initialize()
            await client.cleanup()

            mock_driver.close.assert_called_once()
            assert client._initialized is False
