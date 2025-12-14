# Canvas Learning System - Debug Endpoint Tests
# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: testing)
"""
Integration tests for Debug API endpoints.

Tests cover:
- GET /api/v1/debug/bugs endpoint
- GET /api/v1/debug/bugs/{bug_id} endpoint
- GET /api/v1/debug/bugs/stats endpoint
- Query parameter validation
- Error handling

[Source: docs/stories/21.5.3.story.md - AC-3, AC-4]
[Source: docs/prd/EPIC-21.5-AGENT-RELIABILITY-FIX.md#story-21-5-3]
"""

from pathlib import Path
from typing import Generator
from unittest.mock import patch

import pytest
from app.core.bug_tracker import BugTracker
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture
def test_bug_tracker(tmp_path: Path) -> Generator[BugTracker, None, None]:
    """
    Create a test BugTracker with temporary log file.

    Yields:
        BugTracker: Configured for testing.
    """
    log_path = tmp_path / "test_bug_log.jsonl"
    tracker = BugTracker(log_path=str(log_path))
    yield tracker


@pytest.fixture
def client_with_bugs(test_bug_tracker: BugTracker) -> Generator[TestClient, None, None]:
    """
    Create test client with mocked bug_tracker containing sample bugs.

    ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: testing dependency override)
    """
    # Pre-populate with test bugs
    test_bug_tracker.log_error(
        endpoint="/api/v1/agents/scoring",
        error=ValueError("Invalid canvas path"),
        request_params={"canvas_path": "test.canvas"}
    )
    test_bug_tracker.log_error(
        endpoint="/api/v1/canvas/nodes",
        error=KeyError("node_id"),
        request_params={"node_id": "missing"}
    )
    test_bug_tracker.log_error(
        endpoint="/api/v1/review/generate",
        error=TypeError("Expected dict, got list"),
        request_params={"format": "json"}
    )

    # Patch the global bug_tracker
    with patch("app.api.v1.endpoints.debug.bug_tracker", test_bug_tracker):
        with TestClient(app) as client:
            yield client


@pytest.fixture
def client_empty_bugs(test_bug_tracker: BugTracker) -> Generator[TestClient, None, None]:
    """
    Create test client with empty bug_tracker.
    """
    with patch("app.api.v1.endpoints.debug.bug_tracker", test_bug_tracker):
        with TestClient(app) as client:
            yield client


class TestGetRecentBugs:
    """Tests for GET /api/v1/debug/bugs endpoint."""

    def test_get_bugs_success(self, client_with_bugs: TestClient):
        """
        Test successful retrieval of recent bugs.

        [Source: docs/stories/21.5.3.story.md - AC-3]
        """
        response = client_with_bugs.get("/api/v1/debug/bugs")

        assert response.status_code == 200
        bugs = response.json()
        assert isinstance(bugs, list)
        assert len(bugs) == 3

    def test_get_bugs_empty(self, client_empty_bugs: TestClient):
        """
        Test retrieval when no bugs exist.

        [Source: docs/stories/21.5.3.story.md - AC-3]
        """
        response = client_empty_bugs.get("/api/v1/debug/bugs")

        assert response.status_code == 200
        bugs = response.json()
        assert bugs == []

    def test_get_bugs_with_limit(self, client_with_bugs: TestClient):
        """
        Test limit query parameter.

        [Source: docs/stories/21.5.3.story.md - AC-4]
        """
        response = client_with_bugs.get("/api/v1/debug/bugs?limit=2")

        assert response.status_code == 200
        bugs = response.json()
        assert len(bugs) == 2

    def test_get_bugs_default_limit(self, client_with_bugs: TestClient):
        """
        Test default limit is 50.

        [Source: docs/stories/21.5.3.story.md - AC-4]
        """
        response = client_with_bugs.get("/api/v1/debug/bugs")

        assert response.status_code == 200
        # With only 3 bugs, all should be returned
        bugs = response.json()
        assert len(bugs) == 3

    def test_get_bugs_limit_validation_min(self, client_with_bugs: TestClient):
        """
        Test limit minimum validation (ge=1).

        ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: Query validation)
        """
        response = client_with_bugs.get("/api/v1/debug/bugs?limit=0")

        assert response.status_code == 422  # Validation error

    def test_get_bugs_limit_validation_max(self, client_with_bugs: TestClient):
        """
        Test limit maximum validation (le=200).

        ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: Query validation)
        """
        response = client_with_bugs.get("/api/v1/debug/bugs?limit=201")

        assert response.status_code == 422  # Validation error

    def test_get_bugs_response_format(self, client_with_bugs: TestClient):
        """
        Test response contains required fields.

        [Source: docs/stories/21.5.3.story.md - AC-2]
        """
        response = client_with_bugs.get("/api/v1/debug/bugs?limit=1")

        assert response.status_code == 200
        bugs = response.json()
        assert len(bugs) == 1

        bug = bugs[0]
        # Required fields per AC-2
        assert "bug_id" in bug
        assert "timestamp" in bug
        assert "endpoint" in bug
        assert "error_type" in bug
        assert "error_message" in bug
        assert "request_params" in bug

        # Verify bug_id format
        assert bug["bug_id"].startswith("BUG-")

    def test_get_bugs_newest_first(self, client_with_bugs: TestClient):
        """
        Test bugs are returned newest first.

        [Source: docs/stories/21.5.3.story.md - AC-3]
        """
        response = client_with_bugs.get("/api/v1/debug/bugs")

        assert response.status_code == 200
        bugs = response.json()

        # Last logged bug (review/generate) should be first
        assert bugs[0]["endpoint"] == "/api/v1/review/generate"
        # First logged bug (agents/scoring) should be last
        assert bugs[2]["endpoint"] == "/api/v1/agents/scoring"


class TestGetBugById:
    """Tests for GET /api/v1/debug/bugs/{bug_id} endpoint."""

    def test_get_bug_by_id_success(self, client_with_bugs: TestClient):
        """Test successful retrieval of bug by ID."""
        # First get list to find a bug_id
        list_response = client_with_bugs.get("/api/v1/debug/bugs")
        bugs = list_response.json()
        bug_id = bugs[0]["bug_id"]

        # Get specific bug
        response = client_with_bugs.get(f"/api/v1/debug/bugs/{bug_id}")

        assert response.status_code == 200
        bug = response.json()
        assert bug["bug_id"] == bug_id

    def test_get_bug_by_id_not_found(self, client_with_bugs: TestClient):
        """Test 404 when bug_id doesn't exist."""
        response = client_with_bugs.get("/api/v1/debug/bugs/BUG-NOTFOUND")

        assert response.status_code == 404
        error = response.json()
        assert "not found" in error["detail"].lower()


class TestGetBugStats:
    """Tests for GET /api/v1/debug/bugs/stats endpoint."""

    def test_get_stats_success(self, client_with_bugs: TestClient):
        """Test successful retrieval of bug statistics."""
        response = client_with_bugs.get("/api/v1/debug/bugs/stats")

        assert response.status_code == 200
        stats = response.json()

        assert "total_bugs" in stats
        assert "by_error_type" in stats
        assert "by_endpoint" in stats

        assert stats["total_bugs"] == 3

    def test_get_stats_empty(self, client_empty_bugs: TestClient):
        """Test stats when no bugs exist."""
        response = client_empty_bugs.get("/api/v1/debug/bugs/stats")

        assert response.status_code == 200
        stats = response.json()

        assert stats["total_bugs"] == 0
        assert stats["by_error_type"] == {}
        assert stats["by_endpoint"] == {}

    def test_get_stats_by_error_type(self, client_with_bugs: TestClient):
        """Test stats grouped by error type."""
        response = client_with_bugs.get("/api/v1/debug/bugs/stats")

        stats = response.json()
        by_error_type = stats["by_error_type"]

        # We logged ValueError, KeyError, TypeError
        assert "ValueError" in by_error_type
        assert "KeyError" in by_error_type
        assert "TypeError" in by_error_type

    def test_get_stats_by_endpoint(self, client_with_bugs: TestClient):
        """Test stats grouped by endpoint."""
        response = client_with_bugs.get("/api/v1/debug/bugs/stats")

        stats = response.json()
        by_endpoint = stats["by_endpoint"]

        assert "/api/v1/agents/scoring" in by_endpoint
        assert "/api/v1/canvas/nodes" in by_endpoint
        assert "/api/v1/review/generate" in by_endpoint


class TestDebugRouterRegistration:
    """Tests for debug router registration."""

    def test_debug_routes_registered(self):
        """Test debug routes are registered in the app."""
        with TestClient(app) as client:
            # Check OpenAPI schema includes debug endpoints
            # Note: OpenAPI is served at /api/v1/openapi.json per main.py config
            response = client.get("/api/v1/openapi.json")
            assert response.status_code == 200

            openapi = response.json()
            paths = openapi.get("paths", {})

            assert "/api/v1/debug/bugs" in paths
            assert "/api/v1/debug/bugs/{bug_id}" in paths
            assert "/api/v1/debug/bugs/stats" in paths

    def test_debug_tag_in_openapi(self):
        """Test Debug tag is in OpenAPI schema."""
        with TestClient(app) as client:
            # Note: OpenAPI is served at /api/v1/openapi.json per main.py config
            response = client.get("/api/v1/openapi.json")
            openapi = response.json()

            tags = [tag["name"] for tag in openapi.get("tags", [])]
            assert "Debug" in tags or any(
                "Debug" in path_item.get("get", {}).get("tags", [])
                for path_item in openapi.get("paths", {}).values()
            )
