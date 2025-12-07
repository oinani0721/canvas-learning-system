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
