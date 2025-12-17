# Canvas Learning System - Agent Dedup API Integration Tests
# Story 12.H.5: Backend Dedup - API Integration Tests
# [Source: docs/stories/story-12.H.5-backend-dedup.md]
"""
API integration tests for request deduplication.

Tests the 409 Conflict response and dedup behavior at the API level.

[Source: docs/stories/story-12.H.5-backend-dedup.md#Task-5]
"""

from typing import Generator
from unittest.mock import patch

import pytest
from app.core.request_cache import request_cache
from app.main import app
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient


@pytest.fixture(autouse=True)
def clear_request_cache():
    """Clear request cache before and after each test."""
    request_cache.clear()
    yield
    request_cache.clear()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Create a test client."""
    with TestClient(app) as c:
        yield c


class TestDedupEndpointResponses:
    """Tests for 409 Conflict responses (AC2)."""

    @pytest.mark.asyncio
    async def test_duplicate_request_returns_409(self):
        """AC2: Duplicate request should return HTTP 409 Conflict."""
        # Mark request as in-progress
        cache_key = request_cache.get_key("test.canvas", "node123", "explain_oral")
        request_cache.mark_in_progress(cache_key)

        # Mock dependencies to avoid actual service calls
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            with patch("app.api.v1.endpoints.agents.check_duplicate_request") as mock_check:
                # Simulate 409 from check_duplicate_request
                from fastapi import HTTPException
                mock_check.side_effect = HTTPException(
                    status_code=409,
                    detail={
                        "error": "Duplicate request",
                        "message": "相同请求正在处理中，请稍候",
                        "canvas_name": "test.canvas",
                        "node_id": "node123",
                        "agent_type": "explain_oral",
                        "is_retryable": False
                    }
                )

                response = await ac.post(
                    "/api/v1/agents/explain/oral",
                    json={
                        "canvas_name": "test.canvas",
                        "node_id": "node123"
                    }
                )

                assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_409_response_detail_format(self):
        """AC2: 409 response should have correct detail format."""
        cache_key = request_cache.get_key("test.canvas", "node123", "explain_oral")
        request_cache.mark_in_progress(cache_key)

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            with patch("app.api.v1.endpoints.agents.check_duplicate_request") as mock_check:
                from fastapi import HTTPException
                mock_check.side_effect = HTTPException(
                    status_code=409,
                    detail={
                        "error": "Duplicate request",
                        "message": "相同请求正在处理中，请稍候",
                        "canvas_name": "test.canvas",
                        "node_id": "node123",
                        "agent_type": "explain_oral",
                        "is_retryable": False
                    }
                )

                response = await ac.post(
                    "/api/v1/agents/explain/oral",
                    json={
                        "canvas_name": "test.canvas",
                        "node_id": "node123"
                    }
                )

                assert response.status_code == 409
                detail = response.json()["detail"]
                assert detail["error"] == "Duplicate request"
                assert detail["is_retryable"] is False
                assert "canvas_name" in detail
                assert "node_id" in detail
                assert "agent_type" in detail


class TestDedupConfigToggle:
    """Tests for config-based dedup enable/disable (AC6)."""

    def test_dedup_disabled_allows_duplicate(self):
        """AC6: When ENABLE_REQUEST_DEDUP=false, duplicates should be allowed."""
        from app.api.v1.endpoints.agents import check_duplicate_request
        from app.config import settings

        # Save original value
        original_value = settings.ENABLE_REQUEST_DEDUP

        try:
            # Temporarily disable dedup
            object.__setattr__(settings, 'ENABLE_REQUEST_DEDUP', False)

            request_cache.clear()
            # Should return empty string (dedup disabled)
            result = check_duplicate_request("test.canvas", "node123", "oral")
            assert result == ""
        finally:
            # Restore original value
            object.__setattr__(settings, 'ENABLE_REQUEST_DEDUP', original_value)

    def test_dedup_enabled_by_default(self):
        """Dedup should be enabled by default."""
        from app.config import settings
        assert settings.ENABLE_REQUEST_DEDUP is True


class TestDedupHelperFunctions:
    """Tests for dedup helper functions in agents.py."""

    def test_check_duplicate_request_returns_cache_key(self):
        """check_duplicate_request should return cache key when enabled."""
        from app.api.v1.endpoints.agents import check_duplicate_request

        with patch("app.api.v1.endpoints.agents.settings") as mock_settings:
            mock_settings.ENABLE_REQUEST_DEDUP = True

            # Clear cache and test
            request_cache.clear()
            key = check_duplicate_request("test.canvas", "node123", "oral")

            assert key != ""
            assert len(key) == 32  # MD5 hash length

    def test_check_duplicate_request_marks_in_progress(self):
        """check_duplicate_request should mark request as in-progress."""
        from app.api.v1.endpoints.agents import check_duplicate_request

        with patch("app.api.v1.endpoints.agents.settings") as mock_settings:
            mock_settings.ENABLE_REQUEST_DEDUP = True

            request_cache.clear()
            key = check_duplicate_request("test.canvas", "node123", "oral")

            # Should be marked as duplicate now
            assert request_cache.is_duplicate(key) is True

    def test_check_duplicate_request_raises_409_on_duplicate(self):
        """check_duplicate_request should raise 409 for duplicate."""
        from app.api.v1.endpoints.agents import check_duplicate_request
        from fastapi import HTTPException

        with patch("app.api.v1.endpoints.agents.settings") as mock_settings:
            mock_settings.ENABLE_REQUEST_DEDUP = True

            request_cache.clear()
            # First call should succeed
            check_duplicate_request("test.canvas", "node123", "oral")

            # Second call should raise 409
            with pytest.raises(HTTPException) as exc_info:
                check_duplicate_request("test.canvas", "node123", "oral")

            assert exc_info.value.status_code == 409
            assert exc_info.value.detail["error"] == "Duplicate request"

    def test_complete_request_marks_completed(self):
        """complete_request should mark request as completed."""
        from app.api.v1.endpoints.agents import check_duplicate_request, complete_request

        with patch("app.api.v1.endpoints.agents.settings") as mock_settings:
            mock_settings.ENABLE_REQUEST_DEDUP = True

            request_cache.clear()
            key = check_duplicate_request("test.canvas", "node123", "oral")
            complete_request(key)

            # Entry should still exist (refreshed TTL)
            assert len(request_cache) == 1

    def test_cancel_request_removes_entry(self):
        """cancel_request should remove entry from cache."""
        from app.api.v1.endpoints.agents import cancel_request, check_duplicate_request

        with patch("app.api.v1.endpoints.agents.settings") as mock_settings:
            mock_settings.ENABLE_REQUEST_DEDUP = True

            request_cache.clear()
            key = check_duplicate_request("test.canvas", "node123", "oral")
            cancel_request(key)

            # Entry should be removed
            assert len(request_cache) == 0

    def test_cancel_request_allows_retry(self):
        """After cancel_request, same request should be allowed."""
        from app.api.v1.endpoints.agents import cancel_request, check_duplicate_request

        with patch("app.api.v1.endpoints.agents.settings") as mock_settings:
            mock_settings.ENABLE_REQUEST_DEDUP = True

            request_cache.clear()
            key = check_duplicate_request("test.canvas", "node123", "oral")
            cancel_request(key)

            # Should not raise 409 (retry allowed)
            key2 = check_duplicate_request("test.canvas", "node123", "oral")
            assert key2 != ""


class TestDedupAcrossEndpoints:
    """Tests for dedup across different agent types."""

    def test_different_agent_types_not_duplicate(self):
        """Different agent types should not be considered duplicates."""
        from app.api.v1.endpoints.agents import check_duplicate_request

        with patch("app.api.v1.endpoints.agents.settings") as mock_settings:
            mock_settings.ENABLE_REQUEST_DEDUP = True

            request_cache.clear()

            # First agent type
            key1 = check_duplicate_request("test.canvas", "node123", "oral")
            # Different agent type - should not raise
            key2 = check_duplicate_request("test.canvas", "node123", "four-level")

            assert key1 != key2
            assert len(request_cache) == 2

    def test_different_nodes_not_duplicate(self):
        """Different nodes should not be considered duplicates."""
        from app.api.v1.endpoints.agents import check_duplicate_request

        with patch("app.api.v1.endpoints.agents.settings") as mock_settings:
            mock_settings.ENABLE_REQUEST_DEDUP = True

            request_cache.clear()

            key1 = check_duplicate_request("test.canvas", "node123", "oral")
            key2 = check_duplicate_request("test.canvas", "node456", "oral")

            assert key1 != key2
            assert len(request_cache) == 2

    def test_different_canvases_not_duplicate(self):
        """Different canvases should not be considered duplicates."""
        from app.api.v1.endpoints.agents import check_duplicate_request

        with patch("app.api.v1.endpoints.agents.settings") as mock_settings:
            mock_settings.ENABLE_REQUEST_DEDUP = True

            request_cache.clear()

            key1 = check_duplicate_request("math.canvas", "node123", "oral")
            key2 = check_duplicate_request("physics.canvas", "node123", "oral")

            assert key1 != key2
            assert len(request_cache) == 2


class TestDedupEmptyKeyHandling:
    """Tests for empty cache key handling."""

    def test_complete_request_with_empty_key(self):
        """complete_request with empty key should be no-op."""
        from app.api.v1.endpoints.agents import complete_request

        request_cache.clear()
        # Should not raise
        complete_request("")
        assert len(request_cache) == 0

    def test_cancel_request_with_empty_key(self):
        """cancel_request with empty key should be no-op."""
        from app.api.v1.endpoints.agents import cancel_request

        request_cache.clear()
        # Should not raise
        cancel_request("")
        assert len(request_cache) == 0
