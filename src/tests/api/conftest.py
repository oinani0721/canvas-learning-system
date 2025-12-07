"""
API Test Fixtures for Canvas Learning System

Provides shared fixtures for FastAPI integration testing.

✅ Verified from Context7:/websites/fastapi_tiangolo (topic: TestClient testing)
"""

import pytest
from fastapi.testclient import TestClient

from api.config import Settings
from api.main import create_app


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """
    Test settings with overrides for testing.

    Returns:
        Settings: Test configuration
    """
    return Settings(
        DEBUG=True,
        LOG_LEVEL="DEBUG",
        CANVAS_BASE_PATH="./test_data"
    )


@pytest.fixture(scope="session")
def test_app():
    """
    Create test application instance.

    ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: TestClient)

    Returns:
        FastAPI: Test application
    """
    return create_app()


@pytest.fixture(scope="function")
def client(test_app) -> TestClient:
    """
    Create TestClient for API testing.

    ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: TestClient testing)

    Yields:
        TestClient: HTTP client for testing
    """
    with TestClient(test_app) as client:
        yield client


@pytest.fixture(scope="session")
def session_client(test_app) -> TestClient:
    """
    Create session-scoped TestClient for tests that need persistent state.

    Returns:
        TestClient: Session-scoped HTTP client
    """
    return TestClient(test_app)


# ============================================================================
# Test Data Factories
# ============================================================================

@pytest.fixture
def valid_text_node():
    """Factory for creating valid text node data."""
    def _create(text="测试节点", color="1", x=100, y=200):
        return {
            "type": "text",
            "text": text,
            "x": x,
            "y": y,
            "width": 300,
            "height": 100,
            "color": color
        }
    return _create


@pytest.fixture
def valid_file_node():
    """Factory for creating valid file node data."""
    def _create(file_path="笔记库/test.md", x=100, y=200):
        return {
            "type": "file",
            "file": file_path,
            "x": x,
            "y": y,
            "width": 300,
            "height": 400
        }
    return _create


@pytest.fixture
def valid_edge():
    """Factory for creating valid edge data."""
    def _create(from_node="a1b2c3d4", to_node="e5f6g7h8"):
        return {
            "fromNode": from_node,
            "toNode": to_node,
            "fromSide": "bottom",
            "toSide": "top"
        }
    return _create


@pytest.fixture
def valid_decompose_request():
    """Factory for creating valid decompose request."""
    def _create(canvas_name="test-canvas", node_id="a1b2c3d4"):
        return {
            "canvas_name": canvas_name,
            "node_id": node_id
        }
    return _create


@pytest.fixture
def valid_score_request():
    """Factory for creating valid score request."""
    def _create(canvas_name="test-canvas", node_ids=None):
        return {
            "canvas_name": canvas_name,
            "node_ids": node_ids or ["a1b2c3d4", "e5f6g7h8"]
        }
    return _create


@pytest.fixture
def valid_explain_request():
    """Factory for creating valid explain request."""
    def _create(canvas_name="test-canvas", node_id="a1b2c3d4"):
        return {
            "canvas_name": canvas_name,
            "node_id": node_id
        }
    return _create


@pytest.fixture
def valid_generate_review_request():
    """Factory for creating valid generate review request."""
    def _create(source_canvas="test-canvas", node_ids=None):
        return {
            "source_canvas": source_canvas,
            "node_ids": node_ids
        }
    return _create


@pytest.fixture
def valid_record_review_request():
    """Factory for creating valid record review request."""
    def _create(canvas_name="test-canvas", node_id="a1b2c3d4", score=30.0):
        return {
            "canvas_name": canvas_name,
            "node_id": node_id,
            "score": score
        }
    return _create


# ============================================================================
# Test Data Constants
# ============================================================================

@pytest.fixture(scope="session")
def api_v1_prefix():
    """API version 1 prefix."""
    return "/api/v1"


@pytest.fixture(scope="session")
def test_canvas_name():
    """Test canvas name that exists in mock data."""
    return "test-canvas"


@pytest.fixture(scope="session")
def test_node_id():
    """Test node ID that exists in mock data."""
    return "a1b2c3d4"


@pytest.fixture(scope="session")
def nonexistent_canvas():
    """Non-existent canvas name for error testing."""
    return "nonexistent-canvas"


@pytest.fixture(scope="session")
def nonexistent_node_id():
    """Non-existent node ID for error testing."""
    return "zzz99999"
