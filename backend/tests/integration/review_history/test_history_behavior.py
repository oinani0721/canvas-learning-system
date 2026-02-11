# Story 34.4 + 34.7: Pagination behavior, filters, and error handling
"""
Tests for pagination behavior (has_more logic, show_all, custom limit),
filtering by canvas_path/concept_name, and graceful error degradation.
"""

import pytest

from .helpers import mock_review_history


class TestReviewHistoryPaginationBehavior:
    """Test pagination behavior and has_more logic."""

    def test_has_more_true_when_more_records(self, client):
        """
        Test has_more is True when more records exist beyond limit.

        [Source: backend/app/api/v1/endpoints/review.py#L333-L338]
        """
        with mock_review_history(has_more=True):
            response = client.get("/api/v1/review/history?limit=5")

            assert response.status_code == 200
            data = response.json()
            assert data["pagination"]["has_more"] is True

    def test_has_more_false_when_all_returned(self, client):
        """
        Test has_more is False when all records are returned.

        [Source: backend/app/api/v1/endpoints/review.py#L333-L338]
        """
        with mock_review_history():
            response = client.get("/api/v1/review/history?limit=5")

            assert response.status_code == 200
            data = response.json()
            assert data["pagination"]["has_more"] is False

    def test_show_all_bypasses_limit(self, client):
        """
        Test show_all=true returns all records (Story 34.4 AC2).

        [Source: docs/stories/34.4.story.md#AC-34.4.2]
        """
        with mock_review_history() as mock_service:
            response = client.get("/api/v1/review/history?show_all=true")

            assert response.status_code == 200

            # Story 34.8 AC3: show_all now passes MAX_HISTORY_RECORDS instead of None
            from app.services.review_service import MAX_HISTORY_RECORDS
            mock_service.get_history.assert_called_once()
            call_kwargs = mock_service.get_history.call_args.kwargs
            assert call_kwargs.get("limit") == MAX_HISTORY_RECORDS

    def test_custom_limit_parameter(self, client):
        """
        Test custom limit parameter is passed to service.

        [Source: docs/stories/34.4.story.md#AC-34.4.3]
        """
        with mock_review_history() as mock_service:
            response = client.get("/api/v1/review/history?limit=10")

            assert response.status_code == 200

            mock_service.get_history.assert_called_once()
            call_kwargs = mock_service.get_history.call_args.kwargs
            assert call_kwargs.get("limit") == 10


class TestReviewHistoryFilters:
    """Test filtering by canvas_path and concept_name."""

    def test_filter_by_canvas_path(self, client):
        """
        Test filtering by canvas_path parameter.

        [Source: specs/api/review-api.openapi.yml#L196-L199]
        """
        with mock_review_history() as mock_service:
            response = client.get("/api/v1/review/history?canvas_path=离散数学.canvas")

            assert response.status_code == 200

            mock_service.get_history.assert_called_once()
            call_kwargs = mock_service.get_history.call_args.kwargs
            assert call_kwargs.get("canvas_path") == "离散数学.canvas"

    def test_filter_by_concept_name(self, client):
        """
        Test filtering by concept_name parameter.

        [Source: specs/api/review-api.openapi.yml#L200-L203]
        """
        with mock_review_history() as mock_service:
            response = client.get("/api/v1/review/history?concept_name=逆否命题")

            assert response.status_code == 200

            mock_service.get_history.assert_called_once()
            call_kwargs = mock_service.get_history.call_args.kwargs
            assert call_kwargs.get("concept_name") == "逆否命题"

    def test_combined_filters(self, client):
        """
        Test combining multiple filter parameters.

        [Source: docs/stories/34.4.story.md#Testing]
        """
        with mock_review_history() as mock_service:
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
        """
        Test service errors result in empty response (graceful degradation).

        [Source: backend/app/api/v1/endpoints/review.py#L351-L363]
        """
        with mock_review_history(side_effect=Exception("Service error")):
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
        with mock_review_history():
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
