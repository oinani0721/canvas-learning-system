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

# Fixed timestamp for deterministic tests (avoid datetime.now() flakiness)
_FIXED_REVIEW_TIME = datetime(2025, 1, 15, 10, 30, 0)

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
from app.services.review_service import ReviewService

# The correct patch target: review.py imports get_review_service as _get_review_service_singleton
# (Story 38.9 canonical singleton pattern). NOT the old _get_or_create_review_service.
REVIEW_SERVICE_PATCH = "app.api.v1.endpoints.review._get_review_service_singleton"


@pytest.fixture(autouse=True)
def _reset_review_service_singleton():
    """Reset ReviewService singleton between tests to prevent contamination.

    Story 34.10 AC1: Updated to use canonical reset function from Story 38.9.
    Reference: tests/integration/review_history/conftest.py
    """
    from app.services.review_service import reset_review_service_singleton
    reset_review_service_singleton()
    try:
        yield
    finally:
        reset_review_service_singleton()


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
        with patch(REVIEW_SERVICE_PATCH) as mock_get:
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
        with patch(REVIEW_SERVICE_PATCH) as mock_get:
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
        with patch(REVIEW_SERVICE_PATCH) as mock_get:
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
        with patch(REVIEW_SERVICE_PATCH) as mock_get:
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

    def test_history_custom_days_15_is_valid(self, client):
        """
        Test days=15 is now valid (Story 34.8 AC4: days range [1, 365]).

        Previously days=15 was silently changed to 7 because of
        hardcoded [7, 30, 90] whitelist. Now any value in [1, 365] is accepted.
        """
        with patch(REVIEW_SERVICE_PATCH) as mock_get:
            mock_service = AsyncMock()
            mock_service.get_history = AsyncMock(return_value={
                "records": [],
                "has_more": False
            })
            mock_get.return_value = mock_service

            # days=15 is now valid (not silently changed to 7)
            response = client.get("/api/v1/review/history?days=15")

            assert response.status_code == 200
            data = response.json()

            # Verify period is 15 days (not 7)
            period = data["period"]
            start_date = datetime.fromisoformat(period["start"]).date()
            end_date = datetime.fromisoformat(period["end"]).date()

            assert (end_date - start_date).days == 15

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
                        "review_time": _FIXED_REVIEW_TIME
                    },
                    {
                        "concept_id": "c2",
                        "concept_name": "充分条件",
                        "canvas_path": "离散数学.canvas",
                        "rating": 3,
                        "review_time": _FIXED_REVIEW_TIME
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
                        "review_time": _FIXED_REVIEW_TIME
                    }
                ]
            }
        ]

        with patch(REVIEW_SERVICE_PATCH) as mock_get:
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
                        "review_time": _FIXED_REVIEW_TIME
                    }
                ]
            }
        ]

        with patch(REVIEW_SERVICE_PATCH) as mock_get:
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
                    {"concept_id": "c1", "concept_name": "A", "canvas_path": "a.canvas", "rating": 4, "review_time": _FIXED_REVIEW_TIME},
                    {"concept_id": "c2", "concept_name": "B", "canvas_path": "a.canvas", "rating": 2, "review_time": _FIXED_REVIEW_TIME},
                    {"concept_id": "c3", "concept_name": "C", "canvas_path": "a.canvas", "rating": 3, "review_time": _FIXED_REVIEW_TIME},
                ]
            }
        ]

        with patch(REVIEW_SERVICE_PATCH) as mock_get:
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
                    {"concept_id": "c1", "concept_name": "A", "canvas_path": "离散数学.canvas", "rating": 4, "review_time": _FIXED_REVIEW_TIME},
                    {"concept_id": "c2", "concept_name": "B", "canvas_path": "离散数学.canvas", "rating": 3, "review_time": _FIXED_REVIEW_TIME},
                    {"concept_id": "c3", "concept_name": "C", "canvas_path": "线性代数.canvas", "rating": 4, "review_time": _FIXED_REVIEW_TIME},
                ]
            }
        ]

        with patch(REVIEW_SERVICE_PATCH) as mock_get:
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
        with patch(REVIEW_SERVICE_PATCH) as mock_get:
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
        with patch(REVIEW_SERVICE_PATCH) as mock_get:
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
        with patch(REVIEW_SERVICE_PATCH) as mock_get:
            mock_service = AsyncMock()
            mock_service.get_history = AsyncMock(return_value={
                "records": [],
                "has_more": False,
                "streak_days": 0
            })
            mock_get.return_value = mock_service

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
        with patch(REVIEW_SERVICE_PATCH) as mock_get:
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
        with patch(REVIEW_SERVICE_PATCH) as mock_get:
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
        with patch(REVIEW_SERVICE_PATCH) as mock_get:
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
        with patch(REVIEW_SERVICE_PATCH) as mock_get:
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
        with patch(REVIEW_SERVICE_PATCH) as mock_get:
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
        with patch(REVIEW_SERVICE_PATCH) as mock_get:
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
                        "review_time": _FIXED_REVIEW_TIME
                    }
                ]
            }
        ]

        with patch(REVIEW_SERVICE_PATCH) as mock_get:
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
                        "review_time": _FIXED_REVIEW_TIME
                    }
                ]
            }
        ]

        with patch(REVIEW_SERVICE_PATCH) as mock_get:
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


# ═══════════════════════════════════════════════════════════════════════════════
# Story 34.8 AC1: Real Integration Tests (NOT mocking ReviewService)
# These tests create a real ReviewService instance and test get_history()
# directly, validating sorting, filtering, pagination, and limiting logic.
# ═══════════════════════════════════════════════════════════════════════════════


def _make_real_review_service(card_states: Dict[str, Any] = None):
    """Create a real ReviewService with mock CanvasService but real business logic.

    Story 34.8 AC1: The key difference from mock tests is that
    ReviewService.get_history() runs its real implementation (sorting,
    filtering, pagination) — only CanvasService and TaskManager are mocked
    since they are infrastructure dependencies, not the SUT.
    """
    from unittest.mock import MagicMock
    from app.services.background_task_manager import BackgroundTaskManager

    mock_canvas_service = MagicMock()
    mock_canvas_service.cleanup = AsyncMock()
    mock_canvas_service.canvas_exists = AsyncMock(return_value=True)
    mock_canvas_service.get_canvas = AsyncMock(return_value={"nodes": [], "edges": []})

    task_manager = BackgroundTaskManager()

    service = ReviewService(
        canvas_service=mock_canvas_service,
        task_manager=task_manager,
        graphiti_client=None,  # No Graphiti — tests use _card_states fallback
        fsrs_manager=None  # No FSRS for history tests
    )

    # Inject test card states (this is the FSRS card data fallback path)
    if card_states:
        service._card_states = card_states

    return service


def _build_card_states_for_history(count: int, canvas_prefix: str = "math") -> Dict[str, Any]:
    """Build fake _card_states entries with last_review dates for get_history() to read.

    ReviewService.get_history() uses _card_states as fallback when Graphiti
    is unavailable (lines 1041-1076). Each entry needs 'last_review' as an
    ISO string, and the key format is 'canvas:concept'.

    Uses fixed date to avoid midnight boundary flakiness (test-review H3 fix).
    """
    # Fixed date instead of date.today() for deterministic tests
    base_date = date(2025, 6, 15)
    states = {}
    for i in range(count):
        review_date = base_date - timedelta(days=i % 5)  # Spread across last 5 days
        key = f"{canvas_prefix}.canvas:concept_{i}"
        states[key] = {
            "last_review": datetime(
                review_date.year, review_date.month, review_date.day, 10, 0, 0
            ).isoformat(),
            "rating": (i % 4) + 1  # Ratings 1-4 cycling
        }
    return states


@pytest.mark.asyncio
class TestRealReviewServiceHistory:
    """Story 34.8 AC1: Real integration tests using actual ReviewService instance.

    These tests validate the REAL sorting, filtering, and pagination logic
    inside ReviewService.get_history() — NOT a mock.

    Uses fixed dates for determinism (test-review H3 fix): test data uses
    date(2025, 6, 15) as base, so we patch datetime.now() in the service
    module to match, ensuring records fall within the query date range.
    """

    @pytest.fixture(autouse=True)
    def _patch_service_datetime(self):
        """Patch datetime.now() in review_service to match fixed test dates."""
        _fixed_now = datetime(2025, 6, 15, 23, 59, 0)
        with patch("app.services.review_service.datetime") as mock_dt:
            mock_dt.now.return_value = _fixed_now
            mock_dt.fromisoformat = datetime.fromisoformat
            yield

    async def test_default_limit_returns_max_5_records(self):
        """AC1: Default limit=5 returns at most 5 individual review records."""
        card_states = _build_card_states_for_history(10, "math")
        service = _make_real_review_service(card_states)

        result = await service.get_history(days=7, limit=5)

        # Count total individual reviews across all day records
        total_reviews = sum(len(day["reviews"]) for day in result["records"])
        assert total_reviews <= 5
        assert result["has_more"] is True  # 10 records > limit 5
        assert result["total_count"] == 10

    async def test_show_all_returns_all_records_within_cap(self):
        """AC1+AC3: Large limit returns all records when count < limit."""
        card_states = _build_card_states_for_history(8, "physics")
        service = _make_real_review_service(card_states)

        from app.services.review_service import MAX_HISTORY_RECORDS
        result = await service.get_history(days=7, limit=MAX_HISTORY_RECORDS)

        total_reviews = sum(len(day["reviews"]) for day in result["records"])
        assert total_reviews == 8
        assert result["has_more"] is False

    async def test_limit_parameter_slices_correctly(self):
        """AC1: Custom limit slices records correctly."""
        card_states = _build_card_states_for_history(12, "chem")
        service = _make_real_review_service(card_states)

        result = await service.get_history(days=7, limit=3)

        total_reviews = sum(len(day["reviews"]) for day in result["records"])
        assert total_reviews <= 3
        assert result["has_more"] is True
        assert result["total_count"] == 12

    async def test_records_sorted_by_time_descending(self):
        """AC1: Records are sorted by review_time descending (newest first)."""
        card_states = _build_card_states_for_history(6, "bio")
        service = _make_real_review_service(card_states)

        # Code Review M1 Fix: Use explicit large limit instead of None
        # (AC3: limit=None should not be used to mean "unlimited")
        from app.services.review_service import MAX_HISTORY_RECORDS
        result = await service.get_history(days=7, limit=MAX_HISTORY_RECORDS)

        # Collect all review_time values in the order returned
        all_times = []
        for day_record in result["records"]:
            for review in day_record["reviews"]:
                all_times.append(review["review_time"])

        # Verify descending order (newest first)
        for i in range(len(all_times) - 1):
            assert all_times[i] >= all_times[i + 1], (
                f"Records not sorted descending: {all_times[i]} < {all_times[i+1]}"
            )

    async def test_filter_by_canvas_path(self):
        """AC1: canvas_path filter works with real service."""
        states = {}
        # Fixed date for determinism (test-review H3 fix)
        fixed = date(2025, 6, 15)
        # 3 math records + 2 physics records
        for i in range(3):
            states[f"math.canvas:concept_{i}"] = {
                "last_review": datetime(fixed.year, fixed.month, fixed.day, 10, 0, 0).isoformat(),
                "rating": 3
            }
        for i in range(2):
            states[f"physics.canvas:concept_{i}"] = {
                "last_review": datetime(fixed.year, fixed.month, fixed.day, 11, 0, 0).isoformat(),
                "rating": 4
            }

        service = _make_real_review_service(states)
        from app.services.review_service import MAX_HISTORY_RECORDS
        result = await service.get_history(days=7, canvas_path="math", limit=MAX_HISTORY_RECORDS)

        total_reviews = sum(len(d["reviews"]) for d in result["records"])
        assert total_reviews == 3  # Only math records

    async def test_filter_by_concept_name(self):
        """AC1: concept_name filter works with real service."""
        states = {}
        # Fixed date for determinism (test-review H3 fix)
        fixed = date(2025, 6, 15)
        states["math.canvas:逆否命题"] = {
            "last_review": datetime(fixed.year, fixed.month, fixed.day, 10, 0, 0).isoformat(),
            "rating": 4
        }
        states["math.canvas:充分条件"] = {
            "last_review": datetime(fixed.year, fixed.month, fixed.day, 11, 0, 0).isoformat(),
            "rating": 3
        }

        service = _make_real_review_service(states)
        from app.services.review_service import MAX_HISTORY_RECORDS
        result = await service.get_history(days=7, concept_name="逆否命题", limit=MAX_HISTORY_RECORDS)

        total_reviews = sum(len(d["reviews"]) for d in result["records"])
        assert total_reviews == 1

    async def test_streak_days_calculation(self):
        """AC1: Streak days are calculated from consecutive review days."""
        states = {}
        # Fixed date for determinism (test-review H3 fix)
        fixed = date(2025, 6, 15)
        # Reviews on fixed date and day before (streak=2), skip day before that
        for day_offset in [0, 1]:
            review_date = fixed - timedelta(days=day_offset)
            states[f"math.canvas:concept_{day_offset}"] = {
                "last_review": datetime(
                    review_date.year, review_date.month, review_date.day, 10, 0, 0
                ).isoformat(),
                "rating": 3
            }

        service = _make_real_review_service(states)
        from app.services.review_service import MAX_HISTORY_RECORDS
        result = await service.get_history(days=7, limit=MAX_HISTORY_RECORDS)

        assert result["streak_days"] == 2


# ═══════════════════════════════════════════════════════════════════════════════
# Story 34.8 AC2: DI Completeness Test — graphiti_client injection
# ═══════════════════════════════════════════════════════════════════════════════


class TestReviewServiceDICompleteness:
    """Story 34.8 AC2: Verify canonical singleton handles graphiti_client.

    Story 34.10 AC1: Updated for Story 38.9 canonical singleton pattern.
    After 38.9, both dependencies.py and review.py delegate to
    review_service.get_review_service() which owns the graphiti_client injection.
    """

    def test_canonical_singleton_injects_graphiti_client(self):
        """AC2: review_service.get_review_service() must explicitly inject graphiti_client.

        Story 38.9 moved singleton creation to review_service.py.
        The graphiti_client injection now happens there, not in dependencies.py or review.py.
        """
        import inspect
        from app.services.review_service import get_review_service

        source = inspect.getsource(get_review_service)
        assert "graphiti_client" in source, (
            "Canonical get_review_service() does not mention graphiti_client — "
            "it must explicitly inject or handle this parameter"
        )
        assert "graphiti_client=graphiti_client" in source, (
            "Canonical get_review_service() does not pass graphiti_client= to ReviewService()"
        )

    def test_dependencies_delegates_to_canonical_singleton(self):
        """AC2: dependencies.py get_review_service() must delegate to canonical singleton.

        Story 38.9 AC2: dependencies.py no longer creates ReviewService directly.
        It delegates to review_service.get_review_service() which handles all DI.
        """
        import inspect
        from app.dependencies import get_review_service

        source = inspect.getsource(get_review_service)
        assert "_get_rs_singleton" in source or "get_review_service" in source, (
            "dependencies.py get_review_service() does not delegate to canonical singleton"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Story 34.8 AC3: show_all hard cap tests (MAX_HISTORY_RECORDS=1000)
# ═══════════════════════════════════════════════════════════════════════════════


class TestShowAllHardCap:
    """Story 34.8 AC3: Verify show_all=True uses MAX_HISTORY_RECORDS cap."""

    @pytest.fixture(autouse=True)
    def _patch_service_datetime(self):
        """Patch datetime.now() in review_service to match fixed test dates."""
        _fixed_now = datetime(2025, 6, 15, 23, 59, 0)
        with patch("app.services.review_service.datetime") as mock_dt:
            mock_dt.now.return_value = _fixed_now
            mock_dt.fromisoformat = datetime.fromisoformat
            yield

    def test_max_history_records_constant_exists(self):
        """AC3: MAX_HISTORY_RECORDS constant must be defined."""
        from app.services.review_service import MAX_HISTORY_RECORDS
        assert MAX_HISTORY_RECORDS == 1000

    def test_show_all_uses_max_cap_in_endpoint(self):
        """AC3: show_all=True in endpoint must use MAX_HISTORY_RECORDS, not None."""
        from pathlib import Path
        review_path = Path(__file__).resolve().parents[2] / "app" / "api" / "v1" / "endpoints" / "review.py"
        source = review_path.read_text(encoding="utf-8")

        # Must NOT have "effective_limit = None if show_all"
        assert "effective_limit = None if show_all" not in source, (
            "show_all=True still uses effective_limit=None — must use MAX_HISTORY_RECORDS"
        )
        # Must use MAX_HISTORY_RECORDS for show_all
        assert "MAX_HISTORY_RECORDS" in source, (
            "review.py endpoint does not reference MAX_HISTORY_RECORDS"
        )

    @pytest.mark.asyncio
    async def test_show_all_truncates_above_cap(self):
        """AC3: When records > MAX_HISTORY_RECORDS, truncate and set has_more=True."""
        # Use a small cap for testing — we test the logic, not 1000 records
        card_states = _build_card_states_for_history(15, "large")
        service = _make_real_review_service(card_states)

        # Simulate what the endpoint does: pass a small cap
        result = await service.get_history(days=7, limit=8)

        total_reviews = sum(len(d["reviews"]) for d in result["records"])
        assert total_reviews <= 8
        assert result["has_more"] is True
        assert result["total_count"] == 15  # Real total unaffected by limit

    @pytest.mark.asyncio
    async def test_show_all_no_truncation_below_cap(self):
        """AC3: When records < MAX_HISTORY_RECORDS, return all with has_more=False."""
        card_states = _build_card_states_for_history(5, "small")
        service = _make_real_review_service(card_states)

        from app.services.review_service import MAX_HISTORY_RECORDS
        result = await service.get_history(days=7, limit=MAX_HISTORY_RECORDS)

        total_reviews = sum(len(d["reviews"]) for d in result["records"])
        assert total_reviews == 5
        assert result["has_more"] is False


# ═══════════════════════════════════════════════════════════════════════════════
# Story 34.8 AC4: days parameter validation — Query(ge=1, le=365)
# ═══════════════════════════════════════════════════════════════════════════════


class TestDaysParameterValidation:
    """Story 34.8 AC4: days must be validated via Query(ge=1, le=365)."""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_days_1_is_valid(self, client):
        """AC4: days=1 should work (lower boundary)."""
        with patch(REVIEW_SERVICE_PATCH) as mock_get:
            mock_service = AsyncMock()
            mock_service.get_history = AsyncMock(return_value={
                "records": [], "has_more": False, "streak_days": 0
            })
            mock_get.return_value = mock_service

            response = client.get("/api/v1/review/history?days=1")
            assert response.status_code == 200

    def test_days_365_is_valid(self, client):
        """AC4: days=365 should work (upper boundary)."""
        with patch(REVIEW_SERVICE_PATCH) as mock_get:
            mock_service = AsyncMock()
            mock_service.get_history = AsyncMock(return_value={
                "records": [], "has_more": False, "streak_days": 0
            })
            mock_get.return_value = mock_service

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
            mock_service = AsyncMock()
            mock_service.get_history = AsyncMock(return_value={
                "records": [], "has_more": False, "streak_days": 0
            })
            mock_get.return_value = mock_service

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


# ═══════════════════════════════════════════════════════════════════════════════
# Story 34.9 AC1: limit parameter validation — Query(ge=1, le=100)
# ═══════════════════════════════════════════════════════════════════════════════


class TestLimitParameterValidation:
    """Story 34.9 AC1: limit must be validated via Query(ge=1, le=100)."""

    @pytest.fixture
    def client(self):
        return TestClient(app)

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
            mock_service = AsyncMock()
            mock_service.get_history = AsyncMock(return_value={
                "records": [], "has_more": False, "streak_days": 0
            })
            mock_get.return_value = mock_service

            response = client.get("/api/v1/review/history?limit=1")
            assert response.status_code == 200

    def test_limit_100_is_valid(self, client):
        """AC1: limit=100 should work (upper boundary)."""
        with patch(REVIEW_SERVICE_PATCH) as mock_get:
            mock_service = AsyncMock()
            mock_service.get_history = AsyncMock(return_value={
                "records": [], "has_more": False, "streak_days": 0
            })
            mock_get.return_value = mock_service

            response = client.get("/api/v1/review/history?limit=100")
            assert response.status_code == 200

    def test_limit_50_is_valid(self, client):
        """AC1: limit=50 should work (middle value)."""
        with patch(REVIEW_SERVICE_PATCH) as mock_get:
            mock_service = AsyncMock()
            mock_service.get_history = AsyncMock(return_value={
                "records": [], "has_more": False, "streak_days": 0
            })
            mock_get.return_value = mock_service

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
