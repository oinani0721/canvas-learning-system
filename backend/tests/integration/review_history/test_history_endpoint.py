# Story 34.7 AC5: Period/pagination endpoint tests + response schema validation
"""
Integration tests for GET /api/v1/review/history period and pagination,
plus response schema validation against HistoryResponse model.

Tests cover:
- AC5.1: GET /review/history?days=7 returns 7-day data with pagination
- AC5.2: GET /review/history?days=30 returns 30-day data
- AC5.4: Pagination info includes limit, offset, has_more
- Response matches HistoryResponse Pydantic schema
"""

from datetime import datetime

import pytest

from app.models import HistoryResponse

from .helpers import FIXED_REVIEW_TIME, mock_review_history


class TestReviewHistoryPeriod:
    """Integration tests for GET /api/v1/review/history period and pagination (AC5)."""

    def test_history_default_7_days_period(self, client):
        """
        AC5: Test GET /review/history?days=7 returns data for 7-day period.

        [Source: specs/api/review-api.openapi.yml#L189-L194]
        """
        with mock_review_history():
            response = client.get("/api/v1/review/history?days=7")

            assert response.status_code == 200
            data = response.json()

            period = data["period"]
            start_date = datetime.fromisoformat(period["start"]).date()
            end_date = datetime.fromisoformat(period["end"]).date()
            assert (end_date - start_date).days == 7

    def test_history_default_pagination(self, client):
        """
        AC5: Test default limit=5 for history records (Story 34.4 AC1).

        [Source: docs/stories/34.4.story.md#AC-34.4.1]
        """
        with mock_review_history():
            response = client.get("/api/v1/review/history")

            assert response.status_code == 200
            data = response.json()

            assert "pagination" in data
            assert data["pagination"]["limit"] == 5
            assert data["pagination"]["offset"] == 0

    def test_history_30_days_period(self, client):
        """
        AC5: Test GET /review/history?days=30 returns data for 30-day period.

        [Source: specs/api/review-api.openapi.yml#L189-L194]
        """
        with mock_review_history():
            response = client.get("/api/v1/review/history?days=30")

            assert response.status_code == 200
            data = response.json()

            period = data["period"]
            start_date = datetime.fromisoformat(period["start"]).date()
            end_date = datetime.fromisoformat(period["end"]).date()
            assert (end_date - start_date).days == 30

    def test_history_90_days_period(self, client):
        """
        AC5: Test GET /review/history?days=90 returns data for 90-day period.

        [Source: specs/api/review-api.openapi.yml#L189-L194]
        """
        with mock_review_history():
            response = client.get("/api/v1/review/history?days=90")

            assert response.status_code == 200
            data = response.json()

            period = data["period"]
            start_date = datetime.fromisoformat(period["start"]).date()
            end_date = datetime.fromisoformat(period["end"]).date()
            assert (end_date - start_date).days == 90

    def test_history_custom_days_15_is_valid(self, client):
        """
        Test days=15 is now valid (Story 34.8 AC4: days range [1, 365]).

        Previously days=15 was silently changed to 7 because of
        hardcoded [7, 30, 90] whitelist. Now any value in [1, 365] is accepted.
        """
        with mock_review_history():
            response = client.get("/api/v1/review/history?days=15")

            assert response.status_code == 200
            data = response.json()

            period = data["period"]
            start_date = datetime.fromisoformat(period["start"]).date()
            end_date = datetime.fromisoformat(period["end"]).date()
            assert (end_date - start_date).days == 15


class TestReviewHistoryResponseSchema:
    """Test response matches HistoryResponse schema."""

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
                        "review_time": FIXED_REVIEW_TIME,
                    }
                ],
            }
        ]

        with mock_review_history(records=mock_records, retention_rate=0.9, streak_days=3):
            response = client.get("/api/v1/review/history")

            assert response.status_code == 200
            data = response.json()

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
                        "review_time": FIXED_REVIEW_TIME,
                    }
                ],
            }
        ]

        with mock_review_history(records=mock_records, streak_days=1):
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
