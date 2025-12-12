# Canvas Learning System - Test Configuration
# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: testing)
"""
pytest configuration and shared fixtures for the Canvas Learning System tests.

This module provides test fixtures and configuration for the test suite.

[Source: docs/architecture/coding-standards.md#测试规范]
[Source: ADR-008 - Testing Framework pytest]
"""

import json
import tempfile
from pathlib import Path
from typing import Generator

import pytest
from app.config import Settings, get_settings
from app.main import app

# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: testing TestClient)
from fastapi.testclient import TestClient


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
                "color": "1"  # Red
            },
            {
                "id": "node2",
                "type": "text",
                "text": "Test Node 2",
                "x": 300,
                "y": 0,
                "width": 250,
                "height": 60,
                "color": "3"  # Green
            },
            {
                "id": "node3",
                "type": "text",
                "text": "递归：一个函数调用自身",
                "x": 600,
                "y": 0,
                "width": 250,
                "height": 60,
                "color": "4"  # Purple
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
