# Canvas Learning System - Test Configuration
# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: testing)
"""
pytest configuration and shared fixtures for the Canvas Learning System tests.

This module provides test fixtures and configuration for the test suite.

[Source: docs/architecture/coding-standards.md#测试规范]
[Source: ADR-008 - Testing Framework pytest]
"""

import asyncio
import json
import tempfile
from pathlib import Path
from typing import Generator

import pytest
from app.config import Settings, get_settings
from app.main import app

# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: testing TestClient)
from fastapi.testclient import TestClient


# ============================================================================
# Shared Test Utilities
# ============================================================================


async def wait_for_mock_call(
    mock_method,
    *,
    timeout: float = 2.0,
    interval: float = 0.05,
    expected_count: int = 1,
):
    """Poll until mock is called expected number of times or timeout.

    Use instead of asyncio.sleep() to wait for fire-and-forget background tasks.

    Args:
        mock_method: The mock to check call_count on.
        timeout: Maximum wait time in seconds.
        interval: Polling interval in seconds.
        expected_count: Minimum call_count to wait for.

    Raises:
        TimeoutError: If mock not called within timeout.
    """
    loop = asyncio.get_event_loop()
    start = loop.time()
    while (loop.time() - start) < timeout:
        if mock_method.call_count >= expected_count:
            return
        await asyncio.sleep(interval)
    raise TimeoutError(
        f"{mock_method} not called {expected_count} time(s) within {timeout}s "
        f"(actual: {mock_method.call_count})"
    )


async def wait_for_condition(
    condition_fn,
    *,
    timeout: float = 2.0,
    interval: float = 0.05,
    description: str = "condition",
):
    """Poll until condition_fn returns truthy or timeout.

    Use for integration tests where there is no mock to wait on
    (e.g., waiting for a file to be written by a real service).

    Args:
        condition_fn: Callable returning truthy when done. May be sync or async.
        timeout: Maximum wait time in seconds.
        interval: Polling interval in seconds.
        description: Human-readable label for error messages.

    Raises:
        TimeoutError: If condition not met within timeout.
    """
    loop = asyncio.get_event_loop()
    start = loop.time()
    last_error = None
    while (loop.time() - start) < timeout:
        try:
            result = condition_fn()
            if asyncio.iscoroutine(result):
                result = await result
            if result:
                return result
        except (AssertionError, Exception) as e:
            last_error = e
        await asyncio.sleep(interval)
    msg = f"{description} not met within {timeout}s"
    if last_error:
        msg += f" (last error: {last_error})"
    raise TimeoutError(msg)


async def yield_to_event_loop(iterations: int = 5):
    """Yield control to the event loop for pending tasks.

    Use instead of asyncio.sleep(0.1) when you just need to let
    fire-and-forget tasks run but have nothing specific to wait for
    (e.g., assert_not_called scenarios).
    """
    for _ in range(iterations):
        await asyncio.sleep(0)


@pytest.fixture
def wait_for_call():
    """Provide wait_for_mock_call as a pytest fixture.

    Usage:
        async def test_something(wait_for_call):
            await service.do_something()
            await wait_for_call(mock.method)
            mock.method.assert_called_once()
    """
    return wait_for_mock_call


@pytest.fixture
def wait_condition():
    """Provide wait_for_condition as a pytest fixture.

    Usage:
        async def test_something(wait_condition):
            await service.write_file()
            await wait_condition(lambda: path.exists(), description="file written")
    """
    return wait_for_condition


# ============================================================================
# Prometheus Metrics Isolation
# ============================================================================


def clear_prometheus_metrics():
    """Clear accumulated state from all Canvas Prometheus metrics.

    Prometheus Counters/Histograms/Gauges are module-level singletons.
    Without clearing, values accumulate across tests, causing
    non-deterministic snapshot assertions and parallel-test races.

    Uses internal ``_metrics`` dict (labeled metrics) and ``_value``
    (unlabeled Gauge). This is the accepted pattern for testing with
    prometheus_client — there is no public reset API.
    """
    from app.middleware.agent_metrics import (
        AGENT_ERRORS,
        AGENT_EXECUTION_TIME,
        AGENT_INVOCATIONS,
    )
    from app.middleware.memory_metrics import (
        MEMORY_ERRORS,
        MEMORY_QUERIES,
        MEMORY_QUERY_LATENCY,
    )
    from app.middleware.metrics import (
        CONCURRENT_REQUESTS,
        REQUEST_COUNT,
        REQUEST_LATENCY,
    )

    labeled_metrics = [
        AGENT_EXECUTION_TIME, AGENT_ERRORS, AGENT_INVOCATIONS,
        MEMORY_QUERY_LATENCY, MEMORY_ERRORS, MEMORY_QUERIES,
        REQUEST_COUNT, REQUEST_LATENCY,
    ]
    for metric in labeled_metrics:
        if hasattr(metric, '_metrics'):
            metric._metrics.clear()

    # Unlabeled Gauge — reset value to 0
    if hasattr(CONCURRENT_REQUESTS, '_value'):
        CONCURRENT_REQUESTS._value.set(0)


@pytest.fixture
def reset_prometheus():
    """Fixture that clears Prometheus metrics before and after the test.

    Not autouse — apply explicitly or as autouse in metrics test files:

        pytestmark = pytest.mark.usefixtures("reset_prometheus")
    """
    clear_prometheus_metrics()
    yield
    clear_prometheus_metrics()


# ============================================================================
# Autouse Isolation Fixtures
# ============================================================================


@pytest.fixture(autouse=True)
def isolate_dependency_overrides():
    """Save and restore app.dependency_overrides for each test.

    Prevents dependency override leaks between tests. Module-scoped
    overrides (e.g., from the `client` fixture) are preserved because
    this fixture captures the state AFTER module fixtures have run.
    """
    original = app.dependency_overrides.copy()
    yield
    app.dependency_overrides.clear()
    app.dependency_overrides.update(original)


@pytest.fixture
async def isolate_memory_singleton():
    """Safely reset and restore the memory service singleton.

    Use with autouse=True in test files that modify _memory_service_instance.
    Ensures the singleton is always restored even if the test fails mid-execution.
    """
    from app.services import memory_service as memory_module

    original = memory_module._memory_service_instance
    memory_module._memory_service_instance = None
    try:
        yield
    finally:
        memory_module._memory_service_instance = original


def get_settings_override() -> Settings:
    """
    Override settings for testing.

    ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: testing dependency override)

    Returns:
        Settings: Test configuration settings.
    """
    return Settings(
        PROJECT_NAME="Canvas Learning System API (Test)",
        VERSION="1.0.0-test",
        DEBUG=True,
        LOG_LEVEL="DEBUG",
        CORS_ORIGINS="http://localhost:3000,http://127.0.0.1:3000",
        CANVAS_BASE_PATH="./test_canvas",
    )


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    """
    Create a test client with overridden settings.

    ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: testing TestClient)

    Yields:
        TestClient: FastAPI test client.
    """
    # Override the get_settings dependency
    app.dependency_overrides[get_settings] = get_settings_override

    with TestClient(app) as test_client:
        yield test_client

    # Clean up dependency overrides
    app.dependency_overrides.clear()


@pytest.fixture
def test_settings() -> Settings:
    """
    Get test settings instance.

    Returns:
        Settings: Test configuration settings.
    """
    return get_settings_override()


# ============================================================================
# Story 15.5 Fixtures - Service Layer Tests
# ============================================================================

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_canvas_data() -> dict:
    """Sample canvas data for testing."""
    return {
        "nodes": [
            {
                "id": "node1",
                "type": "text",
                "text": "Test Node 1",
                "x": 0,
                "y": 0,
                "width": 250,
                "height": 60,
                "color": "1"  # Gray (Obsidian Canvas: "1"=gray)
            },
            {
                "id": "node2",
                "type": "text",
                "text": "Test Node 2",
                "x": 300,
                "y": 0,
                "width": 250,
                "height": 60,
                "color": "3"  # Purple (Obsidian Canvas: "3"=purple)
            },
            {
                "id": "node3",
                "type": "text",
                "text": "递归：一个函数调用自身",
                "x": 600,
                "y": 0,
                "width": 250,
                "height": 60,
                "color": "4"  # Red (Obsidian Canvas: "4"=red)
            }
        ],
        "edges": [
            {
                "id": "edge1",
                "fromNode": "node1",
                "toNode": "node2"
            }
        ]
    }


@pytest.fixture
def canvas_file(temp_dir: Path, sample_canvas_data: dict) -> Path:
    """Create a test canvas file."""
    canvas_path = temp_dir / "test.canvas"
    with open(canvas_path, 'w', encoding='utf-8') as f:
        json.dump(sample_canvas_data, f)
    return canvas_path


@pytest.fixture
def canvas_service(temp_dir: Path):
    """Create a CanvasService instance for testing."""
    from app.services.canvas_service import CanvasService
    return CanvasService(canvas_base_path=str(temp_dir))


@pytest.fixture
def agent_service():
    """Create an AgentService instance for testing."""
    from app.services.agent_service import AgentService
    return AgentService()


@pytest.fixture
def task_manager():
    """Create a BackgroundTaskManager instance for testing."""
    from app.services.background_task_manager import BackgroundTaskManager
    # Reset singleton to ensure clean state for each test
    BackgroundTaskManager.reset_instance()
    return BackgroundTaskManager.get_instance()


@pytest.fixture
def review_service(canvas_service, task_manager):
    """Create a ReviewService instance for testing."""
    from app.services.review_service import ReviewService
    return ReviewService(canvas_service=canvas_service, task_manager=task_manager)


# ============================================================================
# Story 20.6 Fixtures - Multi-Provider Integration Tests
# ============================================================================

@pytest.fixture
def mock_settings_multi_provider():
    """
    Mock settings with multi-provider configuration.

    ✅ Verified from Story 20.1 - Multi-Provider Architecture
    """
    from unittest.mock import MagicMock

    settings = MagicMock(spec=Settings)
    settings.AI_PROVIDER = "google"
    settings.AI_MODEL_NAME = "gemini-2.0-flash-exp"

    # Provider 1: Google (primary)
    settings.AI_PROVIDER_1_NAME = "google"
    settings.AI_PROVIDER_1_API_KEY = "test-google-api-key"
    settings.AI_PROVIDER_1_MODEL = "gemini-2.0-flash-exp"
    settings.AI_PROVIDER_1_PRIORITY = "1"
    settings.AI_PROVIDER_1_ENABLED = "true"

    # Provider 2: OpenAI (backup 1)
    settings.AI_PROVIDER_2_NAME = "openai"
    settings.AI_PROVIDER_2_API_KEY = "test-openai-api-key"
    settings.AI_PROVIDER_2_MODEL = "gpt-4o"
    settings.AI_PROVIDER_2_PRIORITY = "2"
    settings.AI_PROVIDER_2_ENABLED = "true"

    # Provider 3: Anthropic (backup 2)
    settings.AI_PROVIDER_3_NAME = "anthropic"
    settings.AI_PROVIDER_3_API_KEY = "test-anthropic-api-key"
    settings.AI_PROVIDER_3_MODEL = "claude-3-5-sonnet-20241022"
    settings.AI_PROVIDER_3_PRIORITY = "3"
    settings.AI_PROVIDER_3_ENABLED = "true"

    # Direct provider keys
    settings.GOOGLE_API_KEY = "test-google-api-key"
    settings.OPENAI_API_KEY = "test-openai-api-key"
    settings.ANTHROPIC_API_KEY = "test-anthropic-api-key"
    settings.GEMINI_MODEL = "gemini-2.0-flash-exp"

    return settings


@pytest.fixture
def mock_healthy_provider():
    """
    Mock healthy AI Provider.

    ✅ Verified from Story 20.1 - base_provider.py interface
    """
    from unittest.mock import AsyncMock, MagicMock

    from app.clients.base_provider import (
        BaseProvider,
        ProviderConfig,
        ProviderHealth,
        ProviderResponse,
        ProviderStatus,
    )

    provider = MagicMock(spec=BaseProvider)
    provider.name = "test-google"
    provider.priority = 1
    provider.is_enabled = True
    provider.health = ProviderHealth(
        status=ProviderStatus.HEALTHY,
        latency_ms=100.0,
        consecutive_failures=0
    )
    provider.is_available = True
    provider.config = ProviderConfig(
        name="test-google",
        api_key="test-api-key",
        model="gemini-2.0-flash-exp",
        priority=1
    )

    # Mock async methods
    provider.initialize = AsyncMock(return_value=True)
    provider.health_check = AsyncMock(return_value=provider.health)
    provider.complete = AsyncMock(return_value=ProviderResponse(
        text="Test response",
        model="gemini-2.0-flash-exp",
        provider="test-google",
        latency_ms=100.0
    ))
    provider.close = AsyncMock()

    return provider


@pytest.fixture
def mock_unhealthy_provider():
    """
    Mock unhealthy AI Provider.

    ✅ Verified from Story 20.1 - Provider failure scenarios
    """
    from unittest.mock import AsyncMock, MagicMock

    from app.clients.base_provider import (
        BaseProvider,
        ProviderConfig,
        ProviderHealth,
        ProviderStatus,
    )

    provider = MagicMock(spec=BaseProvider)
    provider.name = "test-unhealthy"
    provider.priority = 2
    provider.is_enabled = True
    provider.health = ProviderHealth(
        status=ProviderStatus.UNHEALTHY,
        latency_ms=None,
        error_message="Connection timeout",
        consecutive_failures=3
    )
    provider.is_available = False
    provider.config = ProviderConfig(
        name="test-unhealthy",
        api_key="test-api-key",
        model="gpt-4o",
        priority=2
    )

    # Mock async methods - health_check fails
    provider.initialize = AsyncMock(return_value=False)
    provider.health_check = AsyncMock(return_value=provider.health)
    provider.close = AsyncMock()

    return provider


@pytest.fixture
async def async_client():
    """
    Async HTTP client for API testing.

    ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: async testing)
    """
    from httpx import ASGITransport, AsyncClient

    app.dependency_overrides[get_settings] = get_settings_override

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def provider_factory_clean():
    """
    Get a clean ProviderFactory instance for testing.

    ✅ Verified from Story 20.2 - ProviderFactory singleton reset
    """
    from app.clients.provider_factory import ProviderFactory

    # Reset singleton before test
    ProviderFactory.reset_instance()

    yield ProviderFactory

    # Cleanup after test
    ProviderFactory.reset_instance()


# ============================================================================
# Story 31.A.5 Fixtures - Integration Test with Real Neo4j
# [Source: docs/stories/31.A.5.story.md#AC-31.A.5.1]
# ============================================================================

import os

@pytest.fixture(scope="module")
async def real_neo4j_client():
    """
    Real Neo4j client for integration tests.

    Story 31.A.5 AC-31.A.5.1: Requires Docker Neo4j service.

    Environment variables (with defaults for CI):
        NEO4J_URI: bolt://localhost:7687
        NEO4J_USER: neo4j
        NEO4J_PASSWORD: test_password

    Usage:
        @pytest.mark.integration
        @pytest.mark.asyncio
        async def test_something(real_neo4j_client):
            await real_neo4j_client.run_query("...")

    [Source: docs/stories/31.A.5.story.md#3.2-测试基础设施]
    """
    from app.clients.neo4j_client import Neo4jClient

    # Get config from environment (CI-compatible)
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "test_password")

    client = Neo4jClient(
        uri=uri,
        user=user,
        password=password,
        database="neo4j",
    )

    try:
        await client.initialize()

        # Clean up test data before tests
        await client.run_query(
            "MATCH (n) WHERE n.id STARTS WITH 'test_' DETACH DELETE n"
        )

        yield client

    finally:
        # Clean up test data after tests
        try:
            await client.run_query(
                "MATCH (n) WHERE n.id STARTS WITH 'test_' DETACH DELETE n"
            )
        except Exception:
            pass  # Ignore cleanup errors


@pytest.fixture(scope="module")
async def real_memory_service(real_neo4j_client):
    """
    Real MemoryService with Neo4j for integration tests.

    Story 31.A.5: Creates a fresh MemoryService instance with real Neo4j.

    [Source: docs/stories/31.A.5.story.md#AC-31.A.5.1]
    """
    from app.services.memory_service import MemoryService

    service = MemoryService(neo4j_client=real_neo4j_client)
    await service.initialize()
    yield service


@pytest.fixture
def test_user_id():
    """Generate unique test user ID to prevent data collision."""
    import uuid
    return f"test_user_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def test_canvas_path():
    """Test canvas path for memory service tests."""
    return "test/integration/test.canvas"


@pytest.fixture
def test_node_id():
    """Generate unique test node ID."""
    import uuid
    return f"test_node_{uuid.uuid4().hex[:8]}"
