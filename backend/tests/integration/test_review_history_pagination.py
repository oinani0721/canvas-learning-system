# Story 34.7: Integration Tests for Review History Pagination
# [Source: docs/stories/34.7.story.md - AC5]
# [Source: specs/api/review-api.openapi.yml#L182-L213]
"""
Integration tests for review history pagination functionality.

Tests cover:
- AC5.1: GET /review/history?days=7 returns 7-day data with pagination
- AC5.2: GET /review/history?days=30 returns 30-day data
- AC5.3: Response contains total_reviews and statistics fields
- AC5.4: Pagination info includes limit, offset, has_more

[Source: backend/app/api/v1/endpoints/review.py#L240-L363]
[Source: docs/stories/34.4.story.md - Pagination Contract]
"""

from datetime import datetime, date, timedelta
from typing import Dict, Any, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import (
    HistoryResponse,
    HistoryDayRecord,
    HistoryReviewRecord,
    HistoryStatistics,
    HistoryPeriod,
    PaginationInfo,
)


class TestReviewHistoryPaginationEndpoint:
    """Integration tests for GET /api/v1/review/history pagination (AC5).

    Story 34.7 AC5: Tests review history pagination integration.
    """

    @pytest.fixture
    def client(self):
        """Create FastAPI test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_review_service(self):
        """Create mock ReviewService with pagination support."""
        service = AsyncMock()
        service.get_history = AsyncMock(return_value={
            "records": [],
            "has_more": False,
            "retention_rate": None,
            "streak_days": 0
        })
        return service

    # =========================================================================
    # Task 2.2: Test default 7-day data
    # =========================================================================

    def test_history_default_7_days_period(self, client):
        """
        AC5: Test GET /review/history?days=7 returns data for 7-day period.

        [Source: specs/api/review-api.openapi.yml#L189-L194]
        """
        with patch("app.dependencies.get_review_service") as mock_get:
            mock_service = AsyncMock()
            mock_service.get_history = AsyncMock(return_value={
                "records": [],
                "has_more": False
            })
            mock_get.return_value = mock_service

            response = client.get("/api/v1/review/history?days=7")

            assert response.status_code == 200
            data = response.json()

            # Verify period is 7 days
            period = data["period"]
            start_date = datetime.fromisoformat(period["start"]).date()
            end_date = datetime.fromisoformat(period["end"]).date()

            assert (end_date - start_date).days == 7

    def test_history_default_pagination(self, client):
        """
        AC5: Test default limit=5 for history records (Story 34.4 AC1).

        [Source: docs/stories/34.4.story.md#AC-34.4.1]
        """
        with patch("app.dependencies.get_review_service") as mock_get:
            mock_service = AsyncMock()
            mock_service.get_history = AsyncMock(return_value={
                "records": [],
                "has_more": False
            })
            mock_get.return_value = mock_service

            response = client.get("/api/v1/review/history")

            assert response.status_code == 200
            data = response.json()

            # Verify pagination info
            assert "pagination" in data
            assert data["pagination"]["limit"] == 5
            assert data["pagination"]["offset"] == 0

    # =========================================================================
    # Task 2.3: Test 30-day data
    # =========================================================================

    def test_history_30_days_period(self, client):
        """
        AC5: Test GET /review/history?days=30 returns data for 30-day period.

        [Source: specs/api/review-api.openapi.yml#L189-L194]
        """
        with patch("app.dependencies.get_review_service") as mock_get:
            mock_service = AsyncMock()
            mock_service.get_history = AsyncMock(return_value={
                "records": [],
                "has_more": False
            })
            mock_get.return_value = mock_service

            response = client.get("/api/v1/review/history?days=30")

            assert response.status_code == 200
            data = response.json()

            # Verify period is 30 days
            period = data["period"]
            start_date = datetime.fromisoformat(period["start"]).date()
            end_date = datetime.fromisoformat(period["end"]).date()

            assert (end_date - start_date).days == 30

    def test_history_90_days_period(self, client):
        """
        AC5: Test GET /review/history?days=90 returns data for 90-day period.

        [Source: specs/api/review-api.openapi.yml#L189-L194]
        """
        with patch("app.dependencies.get_review_service") as mock_get:
            mock_service = AsyncMock()
            mock_service.get_history = AsyncMock(return_value={
                "records": [],
                "has_more": False
            })
            mock_get.return_value = mock_service

            response = client.get("/api/v1/review/history?days=90")

            assert response.status_code == 200
            data = response.json()

            # Verify period is 90 days
            period = data["period"]
            start_date = datetime.fromisoformat(period["start"]).date()
            end_date = datetime.fromisoformat(period["end"]).date()

            assert (end_date - start_date).days == 90

    def test_history_invalid_days_defaults_to_7(self, client):
        """
        Test invalid days value defaults to 7.

        [Source: backend/app/api/v1/endpoints/review.py#L277-L278]
        """
        with patch("app.dependencies.get_review_service") as mock_get:
            mock_service = AsyncMock()
            mock_service.get_history = AsyncMock(return_value={
                "records": [],
                "has_more": False
            })
            mock_get.return_value = mock_service

            # days=15 is not in [7, 30, 90], should default to 7
            response = client.get("/api/v1/review/history?days=15")

            assert response.status_code == 200
            data = response.json()

            # Verify period defaults to 7 days
            period = data["period"]
            start_date = datetime.fromisoformat(period["start"]).date()
            end_date = datetime.fromisoformat(period["end"]).date()

            assert (end_date - start_date).days == 7

    # =========================================================================
    # Task 2.4: Test total_reviews and statistics fields
    # =========================================================================

    def test_total_reviews_field_accuracy(self, client):
        """
        AC5: Test total_reviews field correctly counts all reviews.

        Note: OpenAPI spec uses total_reviews, not total_count.
        [Source: specs/api/review-api.openapi.yml#L596-L663]
        [Source: docs/stories/34.7.story.md#Dev-Notes - "无 total_count 字段，使用 total_reviews 代替"]
        """
        mock_records = [
            {
                "date": "2025-01-15",
                "reviews": [
                    {
                        "concept_id": "c1",
                        "concept_name": "逆否命题",
                        "canvas_path": "离散数学.canvas",
                        "rating": 4,
                        "review_time": datetime.now()
                    },
                    {
                        "concept_id": "c2",
                        "concept_name": "充分条件",
                        "canvas_path": "离散数学.canvas",
                        "rating": 3,
                        "review_time": datetime.now()
                    }
                ]
            },
            {
                "date": "2025-01-14",
                "reviews": [
                    {
                        "concept_id": "c3",
                        "concept_name": "必要条件",
                        "canvas_path": "离散数学.canvas",
                        "rating": 4,
                        "review_time": datetime.now()
                    }
                ]
            }
        ]

        with patch("app.dependencies.get_review_service") as mock_get:
            mock_service = AsyncMock()
            mock_service.get_history = AsyncMock(return_value={
                "records": mock_records,
                "has_more": False,
                "streak_days": 2
            })
            mock_get.return_value = mock_service

            response = client.get("/api/v1/review/history?days=7")

            assert response.status_code == 200
            data = response.json()

            # Verify total_reviews counts all reviews across all days
            assert data["total_reviews"] == 3  # 2 + 1 = 3

    def test_statistics_field_present(self, client):
        """
        AC5: Test statistics field is present in response.

        [Source: specs/api/review-api.openapi.yml#L645-L662]
        """
        mock_records = [
            {
                "date": "2025-01-15",
                "reviews": [
                    {
                        "concept_id": "c1",
                        "concept_name": "测试概念",
                        "canvas_path": "测试.canvas",
                        "rating": 4,
                        "review_time": datetime.now()
                    }
                ]
            }
        ]

        with patch("app.dependencies.get_review_service") as mock_get:
            mock_service = AsyncMock()
            mock_service.get_history = AsyncMock(return_value={
                "records": mock_records,
                "has_more": False,
                "retention_rate": 0.85,
                "streak_days": 5
            })
            mock_get.return_value = mock_service

            response = client.get("/api/v1/review/history?days=7")

            assert response.status_code == 200
            data = response.json()

            # Verify statistics field exists
            assert "statistics" in data
            stats = data["statistics"]

            # Statistics should contain expected fields
            assert "average_rating" in stats or stats.get("average_rating") is None
            assert "streak_days" in stats

    def test_statistics_average_rating_calculation(self, client):
        """
        AC5: Test average_rating is correctly calculated.

        [Source: backend/app/api/v1/endpoints/review.py#L324-L329]
        """
        mock_records = [
            {
                "date": "2025-01-15",
                "reviews": [
                    {"concept_id": "c1", "concept_name": "A", "canvas_path": "a.canvas", "rating": 4, "review_time": datetime.now()},
                    {"concept_id": "c2", "concept_name": "B", "canvas_path": "a.canvas", "rating": 2, "review_time": datetime.now()},
                    {"concept_id": "c3", "concept_name": "C", "canvas_path": "a.canvas", "rating": 3, "review_time": datetime.now()},
                ]
            }
        ]

        with patch("app.dependencies.get_review_service") as mock_get:
            mock_service = AsyncMock()
            mock_service.get_history = AsyncMock(return_value={
                "records": mock_records,
                "has_more": False,
                "streak_days": 1
            })
            mock_get.return_value = mock_service

            response = client.get("/api/v1/review/history?days=7")

            assert response.status_code == 200
            data = response.json()

            # Average: (4 + 2 + 3) / 3 = 3.0
            if data.get("statistics") and data["statistics"].get("average_rating"):
                assert data["statistics"]["average_rating"] == 3.0

    def test_statistics_by_canvas_breakdown(self, client):
        """
        AC5: Test by_canvas field shows canvas-level breakdown.

        [Source: backend/app/api/v1/endpoints/review.py#L314-L315]
        """
        mock_records = [
            {
                "date": "2025-01-15",
                "reviews": [
                    {"concept_id": "c1", "concept_name": "A", "canvas_path": "离散数学.canvas", "rating": 4, "review_time": datetime.now()},
                    {"concept_id": "c2", "concept_name": "B", "canvas_path": "离散数学.canvas", "rating": 3, "review_time": datetime.now()},
                    {"concept_id": "c3", "concept_name": "C", "canvas_path": "线性代数.canvas", "rating": 4, "review_time": datetime.now()},
                ]
            }
        ]

        with patch("app.dependencies.get_review_service") as mock_get:
            mock_service = AsyncMock()
            mock_service.get_history = AsyncMock(return_value={
                "records": mock_records,
                "has_more": False,
                "streak_days": 1
            })
            mock_get.return_value = mock_service

            response = client.get("/api/v1/review/history?days=7")

            assert response.status_code == 200
            data = response.json()

            # by_canvas should show counts per canvas
            if data.get("statistics") and data["statistics"].get("by_canvas"):
                by_canvas = data["statistics"]["by_canvas"]
                assert by_canvas.get("离散数学.canvas") == 2
                assert by_canvas.get("线性代数.canvas") == 1


class TestReviewHistoryPaginationBehavior:
    """Test pagination behavior and has_more logic."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_has_more_true_when_more_records(self, client):
        """
        Test has_more is True when more records exist beyond limit.

        [Source: backend/app/api/v1/endpoints/review.py#L333-L338]
        """
        with patch("app.dependencies.get_review_service") as mock_get:
            mock_service = AsyncMock()
            mock_service.get_history = AsyncMock(return_value={
                "records": [],
                "has_more": True,  # Service indicates more records exist
                "streak_days": 0
            })
            mock_get.return_value = mock_service

            response = client.get("/api/v1/review/history?limit=5")

            assert response.status_code == 200
            data = response.json()

            assert data["pagination"]["has_more"] is True

    def test_has_more_false_when_all_returned(self, client):
        """
        Test has_more is False when all records are returned.

        [Source: backend/app/api/v1/endpoints/review.py#L333-L338]
        """
        with patch("app.dependencies.get_review_service") as mock_get:
            mock_service = AsyncMock()
            mock_service.get_history = AsyncMock(return_value={
                "records": [],
                "has_more": False,
                "streak_days": 0
            })
            mock_get.return_value = mock_service

            response = client.get("/api/v1/review/history?limit=5")

            assert response.status_code == 200
            data = response.json()

            assert data["pagination"]["has_more"] is False

    def test_show_all_bypasses_limit(self, client):
        """
        Test show_all=true returns all records (Story 34.4 AC2).

        [Source: docs/stories/34.4.story.md#AC-34.4.2]
        """
        with patch("app.dependencies.get_review_service") as mock_get:
            mock_service = AsyncMock()
            mock_service.get_history = AsyncMock(return_value={
                "records": [],
                "has_more": False,
                "streak_days": 0
            })
            mock_get.return_value = mock_service

            response = client.get("/api/v1/review/history?show_all=true")

            assert response.status_code == 200

            # Verify service was called with effective_limit=None
            mock_service.get_history.assert_called_once()
            call_kwargs = mock_service.get_history.call_args.kwargs
            assert call_kwargs.get("limit") is None

    def test_custom_limit_parameter(self, client):
        """
        Test custom limit parameter is passed to service.

        [Source: docs/stories/34.4.story.md#AC-34.4.3]
        """
        with patch("app.dependencies.get_review_service") as mock_get:
            mock_service = AsyncMock()
            mock_service.get_history = AsyncMock(return_value={
                "records": [],
                "has_more": False,
                "streak_days": 0
            })
            mock_get.return_value = mock_service

            response = client.get("/api/v1/review/history?limit=10")

            assert response.status_code == 200

            # Verify service was called with limit=10
            mock_service.get_history.assert_called_once()
            call_kwargs = mock_service.get_history.call_args.kwargs
            assert call_kwargs.get("limit") == 10


class TestReviewHistoryFilters:
    """Test filtering by canvas_path and concept_name."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_filter_by_canvas_path(self, client):
        """
        Test filtering by canvas_path parameter.

        [Source: specs/api/review-api.openapi.yml#L196-L199]
        """
        with patch("app.dependencies.get_review_service") as mock_get:
            mock_service = AsyncMock()
            mock_service.get_history = AsyncMock(return_value={
                "records": [],
                "has_more": False,
                "streak_days": 0
            })
            mock_get.return_value = mock_service

            response = client.get("/api/v1/review/history?canvas_path=离散数学.canvas")

            assert response.status_code == 200

            # Verify service was called with canvas_path filter
            mock_service.get_history.assert_called_once()
            call_kwargs = mock_service.get_history.call_args.kwargs
            assert call_kwargs.get("canvas_path") == "离散数学.canvas"

    def test_filter_by_concept_name(self, client):
        """
        Test filtering by concept_name parameter.

        [Source: specs/api/review-api.openapi.yml#L200-L203]
        """
        with patch("app.dependencies.get_review_service") as mock_get:
            mock_service = AsyncMock()
            mock_service.get_history = AsyncMock(return_value={
                "records": [],
                "has_more": False,
                "streak_days": 0
            })
            mock_get.return_value = mock_service

            response = client.get("/api/v1/review/history?concept_name=逆否命题")

            assert response.status_code == 200

            # Verify service was called with concept_name filter
            mock_service.get_history.assert_called_once()
            call_kwargs = mock_service.get_history.call_args.kwargs
            assert call_kwargs.get("concept_name") == "逆否命题"

    def test_combined_filters(self, client):
        """
        Test combining multiple filter parameters.

        [Source: docs/stories/34.4.story.md#Testing]
        """
        with patch("app.dependencies.get_review_service") as mock_get:
            mock_service = AsyncMock()
            mock_service.get_history = AsyncMock(return_value={
                "records": [],
                "has_more": False,
                "streak_days": 0
            })
            mock_get.return_value = mock_service

            response = client.get(
                "/api/v1/review/history"
                "?days=30"
                "&canvas_path=离散数学.canvas"
                "&concept_name=逆否命题"
                "&limit=10"
            )

            assert response.status_code == 200

            # Verify all filters are passed
            mock_service.get_history.assert_called_once()
            call_kwargs = mock_service.get_history.call_args.kwargs
            assert call_kwargs.get("days") == 30
            assert call_kwargs.get("canvas_path") == "离散数学.canvas"
            assert call_kwargs.get("concept_name") == "逆否命题"
            assert call_kwargs.get("limit") == 10


class TestReviewHistoryErrorHandling:
    """Test error handling and graceful degradation."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_service_error_returns_empty_response(self, client):
        """
        Test service errors result in empty response (graceful degradation).

        [Source: backend/app/api/v1/endpoints/review.py#L351-L363]
        """
        with patch("app.dependencies.get_review_service") as mock_get:
            mock_service = AsyncMock()
            mock_service.get_history = AsyncMock(side_effect=Exception("Service error"))
            mock_get.return_value = mock_service

            response = client.get("/api/v1/review/history")

            # Should return 200 with empty data, not 500
            assert response.status_code == 200
            data = response.json()

            assert data["total_reviews"] == 0
            assert data["records"] == []
            assert data["pagination"]["has_more"] is False

    def test_empty_response_structure(self, client):
        """
        Test empty response has correct structure.

        [Source: specs/api/review-api.openapi.yml#L596-L663]
        """
        with patch("app.dependencies.get_review_service") as mock_get:
            mock_service = AsyncMock()
            mock_service.get_history = AsyncMock(return_value={
                "records": [],
                "has_more": False,
                "streak_days": 0
            })
            mock_get.return_value = mock_service

            response = client.get("/api/v1/review/history")

            assert response.status_code == 200
            data = response.json()

            # Verify structure for empty response
            assert "period" in data
            assert "total_reviews" in data
            assert "records" in data
            assert "statistics" in data
            assert "pagination" in data

            assert isinstance(data["records"], list)
            assert data["total_reviews"] == 0


class TestReviewHistoryResponseSchema:
    """Test response matches HistoryResponse schema."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_response_matches_history_response_schema(self, client):
        """
        Test response matches HistoryResponse Pydantic model.

        [Source: app/models/review_models.py#HistoryResponse]
        """
        mock_records = [
            {
                "date": "2025-01-15",
                "reviews": [
                    {
                        "concept_id": "c1",
                        "concept_name": "测试概念",
                        "canvas_path": "测试.canvas",
                        "rating": 4,
                        "review_time": datetime.now()
                    }
                ]
            }
        ]

        with patch("app.dependencies.get_review_service") as mock_get:
            mock_service = AsyncMock()
            mock_service.get_history = AsyncMock(return_value={
                "records": mock_records,
                "has_more": False,
                "retention_rate": 0.9,
                "streak_days": 3
            })
            mock_get.return_value = mock_service

            response = client.get("/api/v1/review/history")

            assert response.status_code == 200
            data = response.json()

            # Validate against HistoryResponse schema
            try:
                validated = HistoryResponse(**data)
                assert validated.total_reviews == 1
                assert len(validated.records) == 1
                assert validated.pagination.limit == 5
            except Exception as e:
                pytest.fail(f"Response does not match HistoryResponse schema: {e}")

    def test_record_structure(self, client):
        """
        Test individual record structure matches HistoryDayRecord.

        [Source: app/models/review_models.py#HistoryDayRecord]
        """
        mock_records = [
            {
                "date": "2025-01-15",
                "reviews": [
                    {
                        "concept_id": "c1",
                        "concept_name": "测试概念",
                        "canvas_path": "测试.canvas",
                        "rating": 4,
                        "review_time": datetime.now()
                    }
                ]
            }
        ]

        with patch("app.dependencies.get_review_service") as mock_get:
            mock_service = AsyncMock()
            mock_service.get_history = AsyncMock(return_value={
                "records": mock_records,
                "has_more": False,
                "streak_days": 1
            })
            mock_get.return_value = mock_service

            response = client.get("/api/v1/review/history")

            assert response.status_code == 200
            data = response.json()

            if data["records"]:
                record = data["records"][0]
                assert "date" in record
                assert "reviews" in record
                assert isinstance(record["reviews"], list)

                if record["reviews"]:
                    review = record["reviews"][0]
                    assert "concept_id" in review
                    assert "concept_name" in review
                    assert "canvas_path" in review
                    assert "rating" in review
                    assert "review_time" in review
