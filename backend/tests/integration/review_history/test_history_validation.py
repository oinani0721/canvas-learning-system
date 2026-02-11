# Story 34.8 AC4 + Story 34.9 AC1: Parameter validation tests
"""
Tests for days and limit parameter validation.

- Story 34.8 AC4: days must be validated via Query(ge=1, le=365)
- Story 34.9 AC1: limit must be validated via Query(ge=1, le=100)
"""

import pytest
from unittest.mock import AsyncMock

from .helpers import mock_review_history


class TestDaysParameterValidation:
    """Story 34.8 AC4: days must be validated via Query(ge=1, le=365)."""

    def test_days_1_is_valid(self, client):
        """AC4: days=1 should work (lower boundary)."""
        with mock_review_history():
            response = client.get("/api/v1/review/history?days=1")
            assert response.status_code == 200

    def test_days_365_is_valid(self, client):
        """AC4: days=365 should work (upper boundary)."""
        with mock_review_history():
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
        with mock_review_history() as mock_service:
            response = client.get("/api/v1/review/history?days=14")
            assert response.status_code == 200

            # Verify days=14 was actually passed (not silently changed to 7)
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
        with mock_review_history():
            response = client.get("/api/v1/review/history?limit=1")
            assert response.status_code == 200

    def test_limit_100_is_valid(self, client):
        """AC1: limit=100 should work (upper boundary)."""
        with mock_review_history():
            response = client.get("/api/v1/review/history?limit=100")
            assert response.status_code == 200

    def test_limit_50_is_valid(self, client):
        """AC1: limit=50 should work (middle value)."""
        with mock_review_history():
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
