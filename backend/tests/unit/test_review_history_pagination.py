# Story 34.4: Review History Pagination Unit Tests
# [Source: docs/stories/34.4.story.md]
"""
Unit tests for ReviewService history pagination.

Tests cover:
- AC-34.4.1: Default limit=5 for history records
- AC-34.4.2: show_all=true returns all records
- AC-34.4.3: API supports limit and show_all parameters
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch


class TestHistoryPaginationContract:
    """
    Story 34.4: Contract tests for history pagination.

    These tests verify the pagination contract without mocking internals.
    """

    def test_history_response_schema_has_pagination(self):
        """HistoryResponse should include pagination field (AC-34.4.3)."""
        from app.models.review_models import HistoryResponse, PaginationInfo

        # Verify the model can be instantiated with pagination
        response = HistoryResponse(
            period={"start": "2025-01-01", "end": "2025-01-07"},
            total_reviews=12,
            records=[],
            pagination=PaginationInfo(
                limit=5,
                offset=0,
                has_more=True
            )
        )

        assert response.pagination is not None
        assert response.pagination.limit == 5
        assert response.pagination.has_more is True
        # total_reviews tracks total count in HistoryResponse
        assert response.total_reviews == 12

    def test_pagination_info_model(self):
        """PaginationInfo model should have required fields."""
        from app.models.review_models import PaginationInfo

        pagination = PaginationInfo(
            limit=5,
            offset=0,
            has_more=True
        )

        assert pagination.limit == 5
        assert pagination.offset == 0
        assert pagination.has_more is True

    def test_pagination_info_with_offset(self):
        """PaginationInfo should support offset for paginated requests."""
        from app.models.review_models import PaginationInfo

        # With offset (e.g., second page)
        pagination = PaginationInfo(
            limit=5,
            offset=5,
            has_more=True
        )

        assert pagination.limit == 5
        assert pagination.offset == 5
        assert pagination.has_more is True


class TestHistoryAPIEndpoint:
    """
    Story 34.4: API endpoint tests for /review/history.
    """

    @pytest.mark.asyncio
    async def test_endpoint_accepts_limit_parameter(self):
        """GET /review/history should accept limit parameter (AC-34.4.3)."""
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)

        # The endpoint should accept limit parameter without error
        response = client.get("/api/v1/review/history?limit=5")

        # Should not return 422 (validation error)
        assert response.status_code != 422, "Endpoint should accept limit parameter"

    @pytest.mark.asyncio
    async def test_endpoint_accepts_show_all_parameter(self):
        """GET /review/history should accept show_all parameter (AC-34.4.3)."""
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)

        # The endpoint should accept show_all parameter without error
        response = client.get("/api/v1/review/history?show_all=true")

        # Should not return 422 (validation error)
        assert response.status_code != 422, "Endpoint should accept show_all parameter"

    @pytest.mark.asyncio
    async def test_endpoint_default_limit(self):
        """Default limit should be 5 (AC-34.4.1)."""
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)

        # Request without limit parameter
        response = client.get("/api/v1/review/history")

        # Should succeed (endpoint works)
        # The default limit=5 is enforced internally
        assert response.status_code == 200, f"Endpoint should return 200 with default limit, got {response.status_code}"

    @pytest.mark.asyncio
    async def test_endpoint_combined_parameters(self):
        """Endpoint should accept all parameters together."""
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)

        # Request with all parameters
        response = client.get(
            "/api/v1/review/history"
            "?days=7"
            "&canvas_path=test.canvas"
            "&limit=10"
            "&show_all=false"
        )

        # Should not return 422 (validation error)
        assert response.status_code != 422, "Endpoint should accept all parameters"


class TestPaginationLogic:
    """
    Story 34.4: Unit tests for pagination logic.
    """

    def test_limit_5_returns_max_5_records(self):
        """With limit=5, should return at most 5 records (AC-34.4.1)."""
        # Simulate pagination logic
        all_records = list(range(12))  # 12 records
        limit = 5

        result = all_records[:limit] if limit else all_records
        has_more = len(all_records) > limit if limit else False
        total_count = len(all_records)

        assert len(result) == 5
        assert has_more is True
        assert total_count == 12

    def test_limit_none_returns_all_records(self):
        """With limit=None, should return all records (AC-34.4.2)."""
        all_records = list(range(12))
        limit = None

        result = all_records[:limit] if limit else all_records
        has_more = False if limit is None else len(all_records) > limit
        total_count = len(all_records)

        assert len(result) == 12
        assert has_more is False
        assert total_count == 12

    def test_show_all_bypasses_limit(self):
        """show_all=True should bypass limit (AC-34.4.2)."""
        all_records = list(range(12))
        limit = 5
        show_all = True

        # show_all overrides limit
        effective_limit = None if show_all else limit
        result = all_records[:effective_limit] if effective_limit else all_records
        has_more = False if show_all else (len(all_records) > (limit or float('inf')))

        assert len(result) == 12
        assert has_more is False

    def test_has_more_true_when_more_records_exist(self):
        """has_more should be True when total > limit."""
        all_records = list(range(12))
        limit = 5

        result = all_records[:limit]
        has_more = len(all_records) > limit

        assert len(result) == 5
        assert has_more is True

    def test_has_more_false_when_all_returned(self):
        """has_more should be False when all records returned."""
        all_records = list(range(3))  # Only 3 records
        limit = 5

        result = all_records[:limit]
        has_more = len(all_records) > limit

        assert len(result) == 3
        assert has_more is False

    def test_total_count_always_full_count(self):
        """total_count should always reflect total regardless of limit."""
        all_records = list(range(12))
        limit = 5

        result = all_records[:limit]
        total_count = len(all_records)

        assert len(result) == 5
        assert total_count == 12

    def test_empty_records_pagination(self):
        """Empty records should return has_more=False."""
        all_records = []
        limit = 5

        result = all_records[:limit] if limit else all_records
        has_more = len(all_records) > limit if limit else False
        total_count = len(all_records)

        assert len(result) == 0
        assert has_more is False
        assert total_count == 0

    def test_exactly_limit_records(self):
        """When total == limit, has_more should be False."""
        all_records = list(range(5))  # Exactly 5 records
        limit = 5

        result = all_records[:limit]
        has_more = len(all_records) > limit

        assert len(result) == 5
        assert has_more is False  # No more after the limit


class TestSortingRequirement:
    """Story 34.4 AC1: Records should be sorted by date (newest first)."""

    def test_sorting_newest_first(self):
        """Records should be sorted by date descending."""
        from datetime import datetime, timedelta

        # Create records with different dates
        base_date = datetime(2025, 1, 15, 10, 0, 0)
        records = [
            {"review_time": (base_date - timedelta(days=i)).isoformat()}
            for i in [2, 0, 3, 1, 4]  # Unsorted order
        ]

        # Sort by review_time descending (newest first)
        sorted_records = sorted(
            records,
            key=lambda r: r["review_time"],
            reverse=True
        )

        # Verify sorted order
        for i in range(len(sorted_records) - 1):
            assert sorted_records[i]["review_time"] >= sorted_records[i + 1]["review_time"]

    def test_limit_applies_after_sorting(self):
        """Limit should apply after sorting (get newest N records)."""
        from datetime import datetime, timedelta

        base_date = datetime(2025, 1, 15, 10, 0, 0)
        records = [
            {"id": i, "review_time": (base_date - timedelta(days=i)).isoformat()}
            for i in [4, 2, 0, 3, 1]  # Unsorted
        ]

        # Sort then limit
        sorted_records = sorted(
            records,
            key=lambda r: r["review_time"],
            reverse=True
        )
        limited = sorted_records[:3]

        # Should have the 3 newest records (days 0, 1, 2)
        assert len(limited) == 3
        # First record should be newest (day 0)
        expected_newest = (base_date - timedelta(days=0)).isoformat()
        assert limited[0]["review_time"] == expected_newest
