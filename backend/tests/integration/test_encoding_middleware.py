# Canvas Learning System - Encoding Validation Middleware Integration Tests
# Story 12.J.3: 后端请求编码验证中间件
# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: testing)
"""
Integration tests for EncodingValidationMiddleware.

Tests verify that:
- AC1: Invalid UTF-8 requests return HTTP 400, not 500
- AC2: Valid UTF-8 requests pass through normally
- AC3: Error response contains ENCODING_ERROR type

[Source: docs/stories/story-12.J.3-encoding-validation-middleware.md]
[Source: specs/data/error-response.schema.json]
[Source: ADR-008-TESTING-FRAMEWORK-PYTEST-ECOSYSTEM.md]
"""

import pytest
from app.config import Settings, get_settings
from app.main import app
from httpx import ASGITransport, AsyncClient


def get_settings_override() -> Settings:
    """Override settings for testing."""
    return Settings(
        PROJECT_NAME="Canvas Learning System API (Test)",
        VERSION="1.0.0-test",
        DEBUG=True,
        LOG_LEVEL="DEBUG",
        CORS_ORIGINS="http://localhost:3000,http://127.0.0.1:3000",
        CANVAS_BASE_PATH="./test_canvas",
    )


@pytest.fixture
async def client():
    """
    Create async HTTP client for API testing.

    ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: async testing httpx)
    """
    app.dependency_overrides[get_settings] = get_settings_override

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


class TestEncodingValidationMiddleware:
    """
    Story 12.J.3: EncodingValidationMiddleware integration tests.

    Tests the middleware's ability to detect invalid UTF-8 encoding
    and return proper 400 responses before Pydantic validation.
    """

    @pytest.mark.asyncio
    async def test_invalid_utf8_returns_400(self, client: AsyncClient):
        """
        AC1: Invalid UTF-8 request should return HTTP 400, not 500.

        The middleware should catch invalid UTF-8 bytes before Pydantic
        attempts to parse them, preventing 500 errors.

        [Source: specs/data/error-response.schema.json]
        """
        # Construct invalid UTF-8 byte sequence
        # \xff\xfe are not valid UTF-8 continuation bytes
        invalid_body = b'{"canvas_name": "\xff\xfe"}'

        response = await client.post(
            "/api/v1/agents/decompose/basic",
            content=invalid_body,
            headers={"Content-Type": "application/json"}
        )

        # Should return 400, not 500
        assert response.status_code == 400, (
            f"Expected 400 for invalid UTF-8, got {response.status_code}"
        )

        data = response.json()
        # Verify response structure matches error-response.schema.json
        assert "code" in data, "Response must include 'code' (required by schema)"
        assert data["code"] == 400
        assert "message" in data, "Response must include 'message' (required by schema)"

    @pytest.mark.asyncio
    async def test_error_response_has_encoding_error_type(self, client: AsyncClient):
        """
        AC3: Error response should contain ENCODING_ERROR type.

        The middleware must set error_type to ENCODING_ERROR for
        encoding-related failures.

        [Source: specs/data/error-response.schema.json#error_type]
        [Source: specs/api/agent-api.openapi.yml#AgentErrorType]
        """
        # Invalid UTF-8: \x80 is not valid as first byte
        invalid_body = b'{"node_id": "\x80\x81\x82"}'

        response = await client.post(
            "/api/v1/agents/decompose/basic",
            content=invalid_body,
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 400
        data = response.json()

        # AC3: error_type must be ENCODING_ERROR
        assert "error_type" in data, "Response must include 'error_type'"
        assert data["error_type"] == "ENCODING_ERROR", (
            f"Expected error_type=ENCODING_ERROR, got {data['error_type']}"
        )

        # Verify uses 'details' (plural) not 'detail' (singular)
        # [Source: specs/data/error-response.schema.json - uses 'details' plural]
        assert "details" in data, "Response must include 'details' (plural)"
        assert "position" in data["details"], "details must include 'position'"
        assert "path" in data["details"], "details must include 'path'"

    @pytest.mark.asyncio
    async def test_valid_utf8_passes(self, client: AsyncClient):
        """
        AC2: Valid UTF-8 request should pass through normally.

        The middleware should not interfere with valid requests.
        The request may fail for other reasons (e.g., canvas not found),
        but should NOT return 400 ENCODING_ERROR.

        Note: The request may return 500 due to business logic errors
        (e.g., CanvasNotFoundException caught by CORSExceptionMiddleware),
        but this is NOT an encoding error - the encoding validation passed.

        [Source: docs/stories/story-12.J.3-encoding-validation-middleware.md#性能考虑]
        """
        response = await client.post(
            "/api/v1/agents/decompose/basic",
            json={"canvas_name": "测试Canvas.canvas", "node_id": "abc123"}
        )

        # Key assertion: Should NOT return 400 with ENCODING_ERROR
        # Other errors (404, 422, 500) are OK - they mean encoding passed
        if response.status_code == 400:
            data = response.json()
            assert data.get("error_type") != "ENCODING_ERROR", (
                "Valid UTF-8 should not trigger ENCODING_ERROR"
            )

    @pytest.mark.asyncio
    async def test_get_request_skips_validation(self, client: AsyncClient):
        """
        AC2: GET request should skip encoding validation.

        The middleware should only validate POST/PUT/PATCH requests
        that have request bodies.
        """
        response = await client.get("/api/v1/health")

        # GET requests should work normally
        # Health endpoint should return 200
        assert response.status_code == 200, (
            f"GET request should not be affected by encoding middleware, "
            f"got {response.status_code}"
        )

    @pytest.mark.asyncio
    async def test_non_json_content_type_skips_validation(self, client: AsyncClient):
        """
        AC2: Non-JSON content types should skip encoding validation.

        The middleware should only validate application/json requests.
        """
        # Send invalid UTF-8 but with non-JSON content type
        invalid_body = b'\xff\xfe\x00\x01'

        response = await client.post(
            "/api/v1/health",  # This endpoint may not accept POST, that's OK
            content=invalid_body,
            headers={"Content-Type": "application/octet-stream"}
        )

        # Should NOT return 400 encoding error
        # (may return 405 Method Not Allowed or other errors)
        assert response.status_code != 400 or response.json().get("error_type") != "ENCODING_ERROR", (
            "Non-JSON content type should skip encoding validation"
        )

    @pytest.mark.asyncio
    async def test_mixed_valid_invalid_utf8_in_json(self, client: AsyncClient):
        """
        Test JSON with mix of valid and invalid UTF-8 sequences.

        Ensures the middleware detects any invalid bytes in the body.
        """
        # Valid JSON structure but with embedded invalid UTF-8
        # \xc0\xc1 are overlong encodings (invalid in UTF-8)
        invalid_body = b'{"text": "valid start \xc0\xc1 invalid end"}'

        response = await client.post(
            "/api/v1/agents/decompose/basic",
            content=invalid_body,
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 400
        data = response.json()
        assert data["error_type"] == "ENCODING_ERROR"

    @pytest.mark.asyncio
    async def test_empty_json_body_passes(self, client: AsyncClient):
        """
        Test that empty JSON body passes validation.

        Empty body is valid UTF-8 (zero bytes to validate).
        """
        response = await client.post(
            "/api/v1/agents/decompose/basic",
            content=b"{}",
            headers={"Content-Type": "application/json"}
        )

        # Should NOT be 400 encoding error (empty is valid UTF-8)
        # May be 422 validation error (missing required fields) or other
        assert response.status_code != 400 or response.json().get("error_type") != "ENCODING_ERROR", (
            "Empty JSON body should pass encoding validation"
        )

    @pytest.mark.asyncio
    async def test_unicode_emoji_passes(self, client: AsyncClient):
        """
        Test that valid Unicode including emoji passes.

        Emoji are valid UTF-8 encoded characters and should pass.
        """
        # Request with emoji (valid UTF-8)
        response = await client.post(
            "/api/v1/agents/decompose/basic",
            json={"canvas_name": "测试🎉学习📚系统.canvas", "node_id": "node-123"}
        )

        # Should NOT be 400 encoding error
        # May fail for other reasons (404 canvas not found, etc.)
        assert response.status_code != 400 or response.json().get("error_type") != "ENCODING_ERROR", (
            "Valid Unicode with emoji should pass encoding validation"
        )
