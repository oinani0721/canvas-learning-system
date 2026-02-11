# Story 34.7 AC5: Statistics field validation
"""
Tests for total_reviews and statistics fields in history response.

- AC5.3: Response contains total_reviews and statistics fields
- Statistics include average_rating, streak_days, by_canvas breakdown
"""

import pytest

from .helpers import FIXED_REVIEW_TIME, mock_review_history


class TestReviewHistoryStatistics:
    """Test total_reviews and statistics fields (AC5.3)."""

    def test_total_reviews_field_accuracy(self, client):
        """
        AC5: Test total_reviews field correctly counts all reviews.

        Note: OpenAPI spec uses total_reviews, not total_count.
        [Source: specs/api/review-api.openapi.yml#L596-L663]
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
                        "review_time": FIXED_REVIEW_TIME,
                    },
                    {
                        "concept_id": "c2",
                        "concept_name": "充分条件",
                        "canvas_path": "离散数学.canvas",
                        "rating": 3,
                        "review_time": FIXED_REVIEW_TIME,
                    },
                ],
            },
            {
                "date": "2025-01-14",
                "reviews": [
                    {
                        "concept_id": "c3",
                        "concept_name": "必要条件",
                        "canvas_path": "离散数学.canvas",
                        "rating": 4,
                        "review_time": FIXED_REVIEW_TIME,
                    }
                ],
            },
        ]

        with mock_review_history(records=mock_records, streak_days=2):
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
                        "review_time": FIXED_REVIEW_TIME,
                    }
                ],
            }
        ]

        with mock_review_history(records=mock_records, retention_rate=0.85, streak_days=5):
            response = client.get("/api/v1/review/history?days=7")

            assert response.status_code == 200
            data = response.json()

            assert "statistics" in data
            stats = data["statistics"]
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
                    {"concept_id": "c1", "concept_name": "A", "canvas_path": "a.canvas", "rating": 4, "review_time": FIXED_REVIEW_TIME},
                    {"concept_id": "c2", "concept_name": "B", "canvas_path": "a.canvas", "rating": 2, "review_time": FIXED_REVIEW_TIME},
                    {"concept_id": "c3", "concept_name": "C", "canvas_path": "a.canvas", "rating": 3, "review_time": FIXED_REVIEW_TIME},
                ],
            }
        ]

        with mock_review_history(records=mock_records, streak_days=1):
            response = client.get("/api/v1/review/history?days=7")

            assert response.status_code == 200
            data = response.json()

            # Average: (4 + 2 + 3) / 3 = 3.0
            # Story 34.9 AC5: Unconditional assertion — no conditional skip
            assert "statistics" in data, "Response must contain statistics field"
            stats = data["statistics"]
            assert stats is not None, "statistics must not be None when reviews exist"
            assert stats.get("average_rating") is not None, (
                "average_rating must be computed when reviews exist"
            )
            assert stats["average_rating"] == 3.0

    def test_statistics_by_canvas_breakdown(self, client):
        """
        AC5: Test by_canvas field shows canvas-level breakdown.

        [Source: backend/app/api/v1/endpoints/review.py#L314-L315]
        """
        mock_records = [
            {
                "date": "2025-01-15",
                "reviews": [
                    {"concept_id": "c1", "concept_name": "A", "canvas_path": "离散数学.canvas", "rating": 4, "review_time": FIXED_REVIEW_TIME},
                    {"concept_id": "c2", "concept_name": "B", "canvas_path": "离散数学.canvas", "rating": 3, "review_time": FIXED_REVIEW_TIME},
                    {"concept_id": "c3", "concept_name": "C", "canvas_path": "线性代数.canvas", "rating": 4, "review_time": FIXED_REVIEW_TIME},
                ],
            }
        ]

        with mock_review_history(records=mock_records, streak_days=1):
            response = client.get("/api/v1/review/history?days=7")

            assert response.status_code == 200
            data = response.json()

            # Story 34.9 AC5: Unconditional assertion — no conditional skip
            assert "statistics" in data, "Response must contain statistics field"
            stats = data["statistics"]
            assert stats is not None, "statistics must not be None when reviews exist"
            assert stats.get("by_canvas") is not None, (
                "by_canvas must be computed when canvas-specific reviews exist"
            )
            by_canvas = stats["by_canvas"]
            assert by_canvas.get("离散数学.canvas") == 2
            assert by_canvas.get("线性代数.canvas") == 1
