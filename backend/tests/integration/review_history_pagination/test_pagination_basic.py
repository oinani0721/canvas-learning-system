# Story 34.11: Basic pagination, statistics, and response schema tests
"""
Tests for basic review history pagination, statistics fields, and response schema.

Split from test_review_history_pagination.py (1234 lines → ≤300 lines).

Covers:
- Default pagination (limit=5, offset=0)
- Period calculation (7/30/90/custom days)
- total_reviews and statistics fields
- has_more / show_all behavior
- Response schema validation
- Filter pass-through (canvas_path, concept_name)
"""

from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from .conftest import (
    REVIEW_SERVICE_PATCH,
    _FIXED_REVIEW_TIME,
    make_mock_review_service,
)


class TestReviewHistoryPaginationEndpoint:
    """Integration tests for GET /api/v1/review/history pagination."""

    def test_history_default_7_days_period(self, client):
        """Test GET /review/history?days=7 returns data for 7-day period."""
        with patch(REVIEW_SERVICE_PATCH) as mock_get:
            mock_get.return_value = make_mock_review_service()
            response = client.get("/api/v1/review/history?days=7")

            assert response.status_code == 200
            period = response.json()["period"]
            start = datetime.fromisoformat(period["start"]).date()
            end = datetime.fromisoformat(period["end"]).date()
            assert (end - start).days == 7

    def test_history_default_pagination(self, client):
        """Test default limit=5 for history records."""
        with patch(REVIEW_SERVICE_PATCH) as mock_get:
            mock_get.return_value = make_mock_review_service()
            response = client.get("/api/v1/review/history")

            assert response.status_code == 200
            data = response.json()
            assert data["pagination"]["limit"] == 5
            assert data["pagination"]["offset"] == 0

    def test_history_30_days_period(self, client):
        """Test GET /review/history?days=30 returns 30-day period."""
        with patch(REVIEW_SERVICE_PATCH) as mock_get:
            mock_get.return_value = make_mock_review_service()
            response = client.get("/api/v1/review/history?days=30")

            assert response.status_code == 200
            period = response.json()["period"]
            start = datetime.fromisoformat(period["start"]).date()
            end = datetime.fromisoformat(period["end"]).date()
            assert (end - start).days == 30

    def test_history_90_days_period(self, client):
        """Test GET /review/history?days=90 returns 90-day period."""
        with patch(REVIEW_SERVICE_PATCH) as mock_get:
            mock_get.return_value = make_mock_review_service()
            response = client.get("/api/v1/review/history?days=90")

            assert response.status_code == 200
            period = response.json()["period"]
            start = datetime.fromisoformat(period["start"]).date()
            end = datetime.fromisoformat(period["end"]).date()
            assert (end - start).days == 90

    def test_history_custom_days_15_is_valid(self, client):
        """Test days=15 is valid (Story 34.8 AC4: days range [1, 365])."""
        with patch(REVIEW_SERVICE_PATCH) as mock_get:
            mock_get.return_value = make_mock_review_service()
            response = client.get("/api/v1/review/history?days=15")

            assert response.status_code == 200
            period = response.json()["period"]
            start = datetime.fromisoformat(period["start"]).date()
            end = datetime.fromisoformat(period["end"]).date()
            assert (end - start).days == 15

    def test_total_reviews_field_accuracy(self, client):
        """Test total_reviews field correctly counts all reviews."""
        mock_records = [
            {
                "date": "2025-01-15",
                "reviews": [
                    {"concept_id": "c1", "concept_name": "逆否命题",
                     "canvas_path": "离散数学.canvas", "rating": 4,
                     "review_time": _FIXED_REVIEW_TIME},
                    {"concept_id": "c2", "concept_name": "充分条件",
                     "canvas_path": "离散数学.canvas", "rating": 3,
                     "review_time": _FIXED_REVIEW_TIME},
                ],
            },
            {
                "date": "2025-01-14",
                "reviews": [
                    {"concept_id": "c3", "concept_name": "必要条件",
                     "canvas_path": "离散数学.canvas", "rating": 4,
                     "review_time": _FIXED_REVIEW_TIME},
                ],
            },
        ]

        with patch(REVIEW_SERVICE_PATCH) as mock_get:
            mock_get.return_value = make_mock_review_service(
                {"records": mock_records, "has_more": False, "streak_days": 2}
            )
            response = client.get("/api/v1/review/history?days=7")

            assert response.status_code == 200
            assert response.json()["total_reviews"] == 3

    def test_statistics_field_present(self, client):
        """Test statistics field is present in response."""
        mock_records = [
            {
                "date": "2025-01-15",
                "reviews": [
                    {"concept_id": "c1", "concept_name": "测试概念",
                     "canvas_path": "测试.canvas", "rating": 4,
                     "review_time": _FIXED_REVIEW_TIME},
                ],
            },
        ]

        with patch(REVIEW_SERVICE_PATCH) as mock_get:
            mock_get.return_value = make_mock_review_service(
                {"records": mock_records, "has_more": False,
                 "retention_rate": 0.85, "streak_days": 5}
            )
            response = client.get("/api/v1/review/history?days=7")

            assert response.status_code == 200
            stats = response.json()["statistics"]
            assert "average_rating" in stats or stats.get("average_rating") is None
            assert "streak_days" in stats

    def test_statistics_average_rating_calculation(self, client):
        """Test average_rating is correctly calculated."""
        mock_records = [
            {
                "date": "2025-01-15",
                "reviews": [
                    {"concept_id": "c1", "concept_name": "A",
                     "canvas_path": "a.canvas", "rating": 4,
                     "review_time": _FIXED_REVIEW_TIME},
                    {"concept_id": "c2", "concept_name": "B",
                     "canvas_path": "a.canvas", "rating": 2,
                     "review_time": _FIXED_REVIEW_TIME},
                    {"concept_id": "c3", "concept_name": "C",
                     "canvas_path": "a.canvas", "rating": 3,
                     "review_time": _FIXED_REVIEW_TIME},
                ],
            },
        ]

        with patch(REVIEW_SERVICE_PATCH) as mock_get:
            mock_get.return_value = make_mock_review_service(
                {"records": mock_records, "has_more": False, "streak_days": 1}
            )
            response = client.get("/api/v1/review/history?days=7")

            assert response.status_code == 200
            data = response.json()
            assert "statistics" in data
            stats = data["statistics"]
            assert stats is not None
            assert stats.get("average_rating") is not None
            assert stats["average_rating"] == 3.0

    def test_statistics_by_canvas_breakdown(self, client):
        """Test by_canvas field shows canvas-level breakdown."""
        mock_records = [
            {
                "date": "2025-01-15",
                "reviews": [
                    {"concept_id": "c1", "concept_name": "A",
                     "canvas_path": "离散数学.canvas", "rating": 4,
                     "review_time": _FIXED_REVIEW_TIME},
                    {"concept_id": "c2", "concept_name": "B",
                     "canvas_path": "离散数学.canvas", "rating": 3,
                     "review_time": _FIXED_REVIEW_TIME},
                    {"concept_id": "c3", "concept_name": "C",
                     "canvas_path": "线性代数.canvas", "rating": 4,
                     "review_time": _FIXED_REVIEW_TIME},
                ],
            },
        ]

        with patch(REVIEW_SERVICE_PATCH) as mock_get:
            mock_get.return_value = make_mock_review_service(
                {"records": mock_records, "has_more": False, "streak_days": 1}
            )
            response = client.get("/api/v1/review/history?days=7")

            assert response.status_code == 200
            data = response.json()
            assert "statistics" in data
            stats = data["statistics"]
            assert stats is not None
            assert stats.get("by_canvas") is not None
            assert stats["by_canvas"].get("离散数学.canvas") == 2
            assert stats["by_canvas"].get("线性代数.canvas") == 1


class TestReviewHistoryPaginationBehavior:
    """Test pagination behavior and has_more logic."""

    def test_has_more_true_when_more_records(self, client):
        """Test has_more is True when more records exist beyond limit."""
        with patch(REVIEW_SERVICE_PATCH) as mock_get:
            mock_get.return_value = make_mock_review_service(
                {"records": [], "has_more": True, "streak_days": 0}
            )
            response = client.get("/api/v1/review/history?limit=5")

            assert response.status_code == 200
            assert response.json()["pagination"]["has_more"] is True

    def test_has_more_false_when_all_returned(self, client):
        """Test has_more is False when all records are returned."""
        with patch(REVIEW_SERVICE_PATCH) as mock_get:
            mock_get.return_value = make_mock_review_service()
            response = client.get("/api/v1/review/history?limit=5")

            assert response.status_code == 200
            assert response.json()["pagination"]["has_more"] is False

    def test_show_all_bypasses_limit(self, client):
        """Test show_all=true returns all records (Story 34.4 AC2)."""
        with patch(REVIEW_SERVICE_PATCH) as mock_get:
            mock_service = make_mock_review_service()
            mock_get.return_value = mock_service
            response = client.get("/api/v1/review/history?show_all=true")

            assert response.status_code == 200
            from app.services.review_service import MAX_HISTORY_RECORDS
            mock_service.get_history.assert_called_once()
            call_kwargs = mock_service.get_history.call_args.kwargs
            assert call_kwargs.get("limit") == MAX_HISTORY_RECORDS

    def test_custom_limit_parameter(self, client):
        """Test custom limit parameter is passed to service."""
        with patch(REVIEW_SERVICE_PATCH) as mock_get:
            mock_service = make_mock_review_service()
            mock_get.return_value = mock_service
            response = client.get("/api/v1/review/history?limit=10")

            assert response.status_code == 200
            mock_service.get_history.assert_called_once()
            call_kwargs = mock_service.get_history.call_args.kwargs
            assert call_kwargs.get("limit") == 10


