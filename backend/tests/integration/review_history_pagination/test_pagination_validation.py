# Story 34.11: Parameter validation, filters, error handling, and schema tests
"""
Tests for parameter validation (days, limit), filters, error handling,
and response schema validation.

Split from test_review_history_pagination.py (1234 lines → ≤300 lines).

Covers:
- days parameter validation (ge=1, le=365) — Story 34.8 AC4
- limit parameter validation (ge=1, le=100) — Story 34.9 AC1
- Filter pass-through (canvas_path, concept_name)
- Error handling and graceful degradation
- Response schema validation (HistoryResponse)
"""

from unittest.mock import AsyncMock, patch

import pytest

from app.models import HistoryResponse

from .conftest import (
    REVIEW_SERVICE_PATCH,
    _FIXED_REVIEW_TIME,
    make_mock_review_service,
)


class TestReviewHistoryFilters:
    """Test filtering by canvas_path and concept_name."""

    def test_filter_by_canvas_path(self, client):
        """Test filtering by canvas_path parameter."""
        with patch(REVIEW_SERVICE_PATCH) as mock_get:
            mock_service = make_mock_review_service()
            mock_get.return_value = mock_service
            response = client.get(
                "/api/v1/review/history?canvas_path=离散数学.canvas"
            )

            assert response.status_code == 200
            mock_service.get_history.assert_called_once()
            call_kwargs = mock_service.get_history.call_args.kwargs
            assert call_kwargs.get("canvas_path") == "离散数学.canvas"

    def test_filter_by_concept_name(self, client):
        """Test filtering by concept_name parameter."""
        with patch(REVIEW_SERVICE_PATCH) as mock_get:
            mock_service = make_mock_review_service()
            mock_get.return_value = mock_service
            response = client.get(
                "/api/v1/review/history?concept_name=逆否命题"
            )

            assert response.status_code == 200
            mock_service.get_history.assert_called_once()
            call_kwargs = mock_service.get_history.call_args.kwargs
            assert call_kwargs.get("concept_name") == "逆否命题"

    def test_combined_filters(self, client):
        """Test combining multiple filter parameters."""
        with patch(REVIEW_SERVICE_PATCH) as mock_get:
            mock_service = make_mock_review_service()
            mock_get.return_value = mock_service
            response = client.get(
                "/api/v1/review/history"
                "?days=30"
                "&canvas_path=离散数学.canvas"
                "&concept_name=逆否命题"
                "&limit=10"
            )

            assert response.status_code == 200
            mock_service.get_history.assert_called_once()
            call_kwargs = mock_service.get_history.call_args.kwargs
            assert call_kwargs.get("days") == 30
            assert call_kwargs.get("canvas_path") == "离散数学.canvas"
            assert call_kwargs.get("concept_name") == "逆否命题"
            assert call_kwargs.get("limit") == 10


class TestReviewHistoryErrorHandling:
    """Test error handling and graceful degradation."""

    def test_service_error_returns_empty_response(self, client):
        """Test service errors result in empty response (graceful degradation)."""
        with patch(REVIEW_SERVICE_PATCH) as mock_get:
            mock_service = AsyncMock()
            mock_service.get_history = AsyncMock(
                side_effect=Exception("Service error")
            )
            mock_get.return_value = mock_service
            response = client.get("/api/v1/review/history")

            assert response.status_code == 200
            data = response.json()
            assert data["total_reviews"] == 0
            assert data["records"] == []
            assert data["pagination"]["has_more"] is False

    def test_empty_response_structure(self, client):
        """Test empty response has correct structure."""
        with patch(REVIEW_SERVICE_PATCH) as mock_get:
            mock_get.return_value = make_mock_review_service()
            response = client.get("/api/v1/review/history")

            assert response.status_code == 200
            data = response.json()
            assert "period" in data
            assert "total_reviews" in data
            assert "records" in data
            assert "statistics" in data
            assert "pagination" in data
            assert isinstance(data["records"], list)
            assert data["total_reviews"] == 0


class TestDaysParameterValidation:
    """Story 34.8 AC4: days must be validated via Query(ge=1, le=365)."""

    def test_days_1_is_valid(self, client):
        """AC4: days=1 should work (lower boundary)."""
        with patch(REVIEW_SERVICE_PATCH) as mock_get:
            mock_get.return_value = make_mock_review_service()
            response = client.get("/api/v1/review/history?days=1")
            assert response.status_code == 200

    def test_days_365_is_valid(self, client):
        """AC4: days=365 should work (upper boundary)."""
        with patch(REVIEW_SERVICE_PATCH) as mock_get:
            mock_get.return_value = make_mock_review_service()
            response = client.get("/api/v1/review/history?days=365")
            assert response.status_code == 200

    def test_days_0_returns_422(self, client):
        """AC4: days=0 must return 422 Validation Error."""
        response = client.get("/api/v1/review/history?days=0")
        assert response.status_code == 422

    def test_days_negative_returns_422(self, client):
        """AC4: days=-1 must return 422 Validation Error."""
        response = client.get("/api/v1/review/history?days=-1")
        assert response.status_code == 422

    def test_days_400_returns_422(self, client):
        """AC4: days=400 (> 365) must return 422 Validation Error."""
        response = client.get("/api/v1/review/history?days=400")
        assert response.status_code == 422

    def test_days_14_is_valid(self, client):
        """AC4: days=14 should work (was previously silently changed to 7)."""
        with patch(REVIEW_SERVICE_PATCH) as mock_get:
            mock_service = make_mock_review_service()
            mock_get.return_value = mock_service
            response = client.get("/api/v1/review/history?days=14")

            assert response.status_code == 200
            mock_service.get_history.assert_called_once()
            call_kwargs = mock_service.get_history.call_args.kwargs
            assert call_kwargs.get("days") == 14

    def test_days_non_integer_returns_422(self, client):
        """AC4: days=abc (non-integer) must return 422 Validation Error."""
        response = client.get("/api/v1/review/history?days=abc")
        assert response.status_code == 422


class TestLimitParameterValidation:
    """Story 34.9 AC1: limit must be validated via Query(ge=1, le=100)."""

    def test_limit_0_returns_422(self, client):
        """AC1: limit=0 must return 422 Validation Error."""
        response = client.get("/api/v1/review/history?limit=0")
        assert response.status_code == 422

    def test_limit_negative_returns_422(self, client):
        """AC1: limit=-1 must return 422 Validation Error."""
        response = client.get("/api/v1/review/history?limit=-1")
        assert response.status_code == 422

    def test_limit_101_returns_422(self, client):
        """AC1: limit=101 (> 100) must return 422 Validation Error."""
        response = client.get("/api/v1/review/history?limit=101")
        assert response.status_code == 422

    def test_limit_1_is_valid(self, client):
        """AC1: limit=1 should work (lower boundary)."""
        with patch(REVIEW_SERVICE_PATCH) as mock_get:
            mock_get.return_value = make_mock_review_service()
            response = client.get("/api/v1/review/history?limit=1")
            assert response.status_code == 200

    def test_limit_100_is_valid(self, client):
        """AC1: limit=100 should work (upper boundary)."""
        with patch(REVIEW_SERVICE_PATCH) as mock_get:
            mock_get.return_value = make_mock_review_service()
            response = client.get("/api/v1/review/history?limit=100")
            assert response.status_code == 200

    def test_limit_50_is_valid(self, client):
        """AC1: limit=50 should work (middle value)."""
        with patch(REVIEW_SERVICE_PATCH) as mock_get:
            mock_get.return_value = make_mock_review_service()
            response = client.get("/api/v1/review/history?limit=50")
            assert response.status_code == 200

    def test_limit_non_integer_returns_422(self, client):
        """AC1: limit=abc (non-integer) must return 422 Validation Error."""
        response = client.get("/api/v1/review/history?limit=abc")
        assert response.status_code == 422

    def test_limit_very_large_returns_422(self, client):
        """AC1: limit=99999999 must return 422 Validation Error."""
        response = client.get("/api/v1/review/history?limit=99999999")
        assert response.status_code == 422


class TestReviewHistoryResponseSchema:
    """Test response matches HistoryResponse schema."""

    def test_response_matches_history_response_schema(self, client):
        """Test response matches HistoryResponse Pydantic model."""
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
                 "retention_rate": 0.9, "streak_days": 3}
            )
            response = client.get("/api/v1/review/history")

            assert response.status_code == 200
            data = response.json()
            try:
                validated = HistoryResponse(**data)
                assert validated.total_reviews == 1
                assert len(validated.records) == 1
                assert validated.pagination.limit == 5
            except Exception as e:
                pytest.fail(
                    f"Response does not match HistoryResponse schema: {e}"
                )

    def test_record_structure(self, client):
        """Test individual record structure matches HistoryDayRecord."""
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
                {"records": mock_records, "has_more": False, "streak_days": 1}
            )
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
