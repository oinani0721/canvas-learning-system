# Canvas Learning System - Test Configuration
# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: testing)
"""
pytest configuration and shared fixtures for the Canvas Learning System tests.

This module provides test fixtures and configuration for the test suite.

[Source: docs/architecture/coding-standards.md#测试规范]
[Source: ADR-008 - Testing Framework pytest]
"""

import pytest
from typing import Generator

# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: testing TestClient)
from fastapi.testclient import TestClient

from app.main import app
from app.config import Settings, get_settings


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
