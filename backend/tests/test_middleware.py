# Canvas Learning System - Middleware Tests
# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: testing)
"""
Test suite for middleware and exception handling.

Tests:
- LoggingMiddleware request/response logging
- ErrorHandlerMiddleware exception catching
- Exception handlers for various error types
- Error response format compliance with schema

[Source: specs/data/error-response.schema.json - Error response format]
"""

import pytest
from app.core.exception_handlers import register_exception_handlers
from app.exceptions import (
    AgentExecutionError,
    CanvasException,
    CanvasNotFoundError,
    NodeNotFoundError,
    ValidationError,
)
from app.middleware import ErrorHandlerMiddleware, LoggingMiddleware
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

# ══════════════════════════════════════════════════════════════════
# Test Fixtures
# ══════════════════════════════════════════════════════════════════


@pytest.fixture
def test_app():
    """
    Create a test FastAPI application with middleware configured.

    # ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: testing)
    """
    app = FastAPI()

    # Add middleware in correct order
    app.add_middleware(ErrorHandlerMiddleware)
    app.add_middleware(LoggingMiddleware)

    # Register exception handlers
    register_exception_handlers(app)

    # Add test endpoints
    @app.get("/success")
    async def success_endpoint():
        return {"status": "ok"}

    @app.get("/canvas-error")
    async def canvas_error_endpoint():
        raise CanvasNotFoundError("test_canvas")

    @app.get("/node-error")
    async def node_error_endpoint():
        raise NodeNotFoundError("node-123", "test_canvas")

    @app.get("/validation-error")
    async def validation_error_endpoint():
        raise ValidationError("Invalid value", field="test_field", value="bad")

    @app.get("/agent-error")
    async def agent_error_endpoint():
        raise AgentExecutionError(
            "Agent timed out",
            agent_type="decomposition",
            node_id="node-456",
        )

    @app.get("/http-error")
    async def http_error_endpoint():
        raise HTTPException(status_code=403, detail="Forbidden")

    @app.get("/generic-error")
    async def generic_error_endpoint():
        raise RuntimeError("Unexpected error")

    return app


@pytest.fixture
def client(test_app):
    """
    Create a test client for the test app.

    # ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: testing)
    """
    return TestClient(test_app)


# ══════════════════════════════════════════════════════════════════
# Exception Class Tests
# ══════════════════════════════════════════════════════════════════


class TestCanvasException:
    """Tests for CanvasException base class."""

    def test_basic_exception(self):
        """Test basic exception creation."""
        exc = CanvasException("Test error", code=500)
        assert exc.message == "Test error"
        assert exc.code == 500
        assert exc.details is None

    def test_exception_with_details(self):
        """Test exception with details."""
        exc = CanvasException(
            "Test error",
            code=400,
            details={"field": "test"},
        )
        assert exc.details == {"field": "test"}

    def test_to_dict_basic(self):
        """Test to_dict conversion without details."""
        exc = CanvasException("Test error", code=404)
        result = exc.to_dict()

        assert result == {"code": 404, "message": "Test error"}

    def test_to_dict_with_details(self):
        """Test to_dict conversion with details."""
        exc = CanvasException(
            "Test error",
            code=400,
            details={"reason": "invalid"},
        )
        result = exc.to_dict()

        assert result == {
            "code": 400,
            "message": "Test error",
            "details": {"reason": "invalid"},
        }


class TestCanvasNotFoundError:
    """Tests for CanvasNotFoundError."""

    def test_exception_message(self):
        """Test exception message format."""
        exc = CanvasNotFoundError("my_canvas")
        assert exc.message == "Canvas 'my_canvas' not found"
        assert exc.code == 404
        assert exc.canvas_name == "my_canvas"

    def test_exception_details(self):
        """Test exception includes canvas_name in details."""
        exc = CanvasNotFoundError("my_canvas")
        assert exc.details == {"canvas_name": "my_canvas"}


class TestNodeNotFoundError:
    """Tests for NodeNotFoundError."""

    def test_exception_message(self):
        """Test exception message format."""
        exc = NodeNotFoundError("node-123", "my_canvas")
        assert exc.message == "Node 'node-123' not found in canvas 'my_canvas'"
        assert exc.code == 404

    def test_exception_details(self):
        """Test exception includes node_id and canvas_name."""
        exc = NodeNotFoundError("node-123", "my_canvas")
        assert exc.details == {
            "node_id": "node-123",
            "canvas_name": "my_canvas",
        }


class TestValidationError:
    """Tests for ValidationError."""

    def test_basic_validation_error(self):
        """Test basic validation error."""
        exc = ValidationError("Invalid value")
        assert exc.message == "Invalid value"
        assert exc.code == 400

    def test_validation_error_with_field(self):
        """Test validation error with field info."""
        exc = ValidationError("Invalid color", field="color", value="invalid")
        assert exc.field == "color"
        assert exc.value == "invalid"
        assert exc.details == {"field": "color", "value": "invalid"}


class TestAgentExecutionError:
    """Tests for AgentExecutionError."""

    def test_agent_error(self):
        """Test agent execution error."""
        exc = AgentExecutionError(
            "Agent timed out",
            agent_type="decomposition",
            node_id="node-123",
        )
        assert exc.message == "Agent timed out"
        assert exc.code == 500
        assert exc.agent_type == "decomposition"
        assert exc.node_id == "node-123"


# ══════════════════════════════════════════════════════════════════
# Middleware Integration Tests
# ══════════════════════════════════════════════════════════════════


class TestLoggingMiddleware:
    """Tests for LoggingMiddleware."""

    def test_adds_request_id_header(self, client):
        """Test that logging middleware adds X-Request-ID header."""
        response = client.get("/success")
        assert "X-Request-ID" in response.headers
        # Request ID should be a valid UUID format
        request_id = response.headers["X-Request-ID"]
        assert len(request_id) == 36  # UUID format: 8-4-4-4-12

    def test_adds_process_time_header(self, client):
        """Test that logging middleware adds X-Process-Time header."""
        response = client.get("/success")
        assert "X-Process-Time" in response.headers
        # Process time should be in ms format
        process_time = response.headers["X-Process-Time"]
        assert process_time.endswith("ms")


class TestErrorHandlerMiddleware:
    """Tests for ErrorHandlerMiddleware."""

    def test_catches_unhandled_exception(self, client):
        """Test middleware catches unhandled exceptions."""
        response = client.get("/generic-error")
        assert response.status_code == 500

    def test_error_response_has_request_id(self, client):
        """Test error response includes X-Request-ID header."""
        response = client.get("/generic-error")
        assert "X-Request-ID" in response.headers


# ══════════════════════════════════════════════════════════════════
# Exception Handler Integration Tests
# ══════════════════════════════════════════════════════════════════


class TestExceptionHandlers:
    """Tests for global exception handlers."""

    def test_canvas_not_found_error(self, client):
        """
        Test CanvasNotFoundError returns 404 with correct format.

        [Source: specs/data/error-response.schema.json]
        """
        response = client.get("/canvas-error")
        assert response.status_code == 404

        data = response.json()
        assert data["code"] == 404
        assert "Canvas 'test_canvas' not found" in data["message"]
        assert data["details"]["canvas_name"] == "test_canvas"

    def test_node_not_found_error(self, client):
        """
        Test NodeNotFoundError returns 404 with correct format.

        [Source: specs/data/error-response.schema.json]
        """
        response = client.get("/node-error")
        assert response.status_code == 404

        data = response.json()
        assert data["code"] == 404
        assert "node-123" in data["message"]
        assert data["details"]["node_id"] == "node-123"
        assert data["details"]["canvas_name"] == "test_canvas"

    def test_validation_error(self, client):
        """
        Test ValidationError returns 400 with correct format.

        [Source: specs/data/error-response.schema.json]
        """
        response = client.get("/validation-error")
        assert response.status_code == 400

        data = response.json()
        assert data["code"] == 400
        assert "Invalid value" in data["message"]

    def test_agent_execution_error(self, client):
        """
        Test AgentExecutionError returns 500 with correct format.

        [Source: specs/data/error-response.schema.json]
        """
        response = client.get("/agent-error")
        assert response.status_code == 500

        data = response.json()
        assert data["code"] == 500
        assert "Agent timed out" in data["message"]

    def test_http_exception(self, client):
        """
        Test HTTPException returns correct status with format.

        [Source: specs/data/error-response.schema.json]
        """
        response = client.get("/http-error")
        assert response.status_code == 403

        data = response.json()
        assert data["code"] == 403
        assert data["message"] == "Forbidden"

    def test_generic_exception(self, client):
        """
        Test unhandled exception returns 500 with safe message.

        [Source: specs/data/error-response.schema.json]
        """
        response = client.get("/generic-error")
        assert response.status_code == 500

        data = response.json()
        assert data["code"] == 500
        # Should NOT expose internal error message
        assert data["message"] == "Internal server error"


# ══════════════════════════════════════════════════════════════════
# Error Response Schema Compliance Tests
# ══════════════════════════════════════════════════════════════════


class TestErrorResponseSchema:
    """
    Tests to verify error responses comply with error-response.schema.json.

    Schema requirements:
    - Required: code (int), message (str)
    - Optional: details (object)

    [Source: specs/data/error-response.schema.json]
    """

    def test_error_response_has_required_fields(self, client):
        """Test error response contains required fields."""
        response = client.get("/canvas-error")
        data = response.json()

        # Required fields
        assert "code" in data
        assert "message" in data
        assert isinstance(data["code"], int)
        assert isinstance(data["message"], str)

    def test_error_response_details_optional(self, client):
        """Test that details field is optional."""
        response = client.get("/http-error")
        data = response.json()

        # code and message are required
        assert "code" in data
        assert "message" in data
        # details can be absent or present
        if "details" in data:
            assert isinstance(data["details"], dict)

    def test_all_error_responses_consistent(self, client):
        """Test all error types return consistent format."""
        error_endpoints = [
            "/canvas-error",
            "/node-error",
            "/validation-error",
            "/agent-error",
            "/http-error",
            "/generic-error",
        ]

        for endpoint in error_endpoints:
            response = client.get(endpoint)
            data = response.json()

            # All should have code and message
            assert "code" in data, f"Missing 'code' for {endpoint}"
            assert "message" in data, f"Missing 'message' for {endpoint}"
            assert isinstance(data["code"], int), f"'code' not int for {endpoint}"
            assert isinstance(data["message"], str), f"'message' not str for {endpoint}"


# ══════════════════════════════════════════════════════════════════
# Health Endpoint Test
# ══════════════════════════════════════════════════════════════════


class TestHealthEndpoint:
    """Tests for health check endpoint via main app."""

    def test_health_endpoint(self):
        """Test health endpoint returns correct format."""
        from app.main import app

        client = TestClient(app)
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert "app_name" in data
        assert "version" in data
        assert "timestamp" in data

    def test_root_endpoint(self):
        """Test root endpoint returns API info."""
        from app.main import app

        client = TestClient(app)
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        # Root endpoint returns: message, version, docs, health
        assert "message" in data
        assert "Canvas Learning System API" in data["message"]
