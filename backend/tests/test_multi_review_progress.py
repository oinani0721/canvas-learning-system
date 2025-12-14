# Canvas Learning System - Multi-Review Progress Tests
# Story 24.4: Multi-Review Trend Analysis and History Visualization
"""
Unit tests for multi-review progress tracking.

[Source: docs/stories/24.4.story.md#Testing-Requirements]
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.core.exceptions import CanvasNotFoundException
from app.services.review_service import ReviewService

# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def mock_canvas_service():
    """Mock CanvasService for testing."""
    service = MagicMock()
    service.canvas_exists = AsyncMock(return_value=True)
    return service


@pytest.fixture
def mock_task_manager():
    """Mock BackgroundTaskManager for testing."""
    manager = MagicMock()
    return manager


@pytest.fixture
def mock_graphiti_client():
    """Mock GraphitiEdgeClient for testing."""
    client = MagicMock()
    return client


@pytest.fixture
def review_service(mock_canvas_service, mock_task_manager, mock_graphiti_client):
    """ReviewService instance with mocked dependencies."""
    return ReviewService(
        canvas_service=mock_canvas_service,
        task_manager=mock_task_manager,
        graphiti_client=mock_graphiti_client
    )


@pytest.fixture
def sample_review_history() -> List[Dict[str, Any]]:
    """Sample review history data for testing."""
    base_date = datetime(2025, 1, 15, 10, 0, 0)
    return [
        {
            "review_canvas_path": "离散数学-检验白板-20250121.canvas",
            "date": base_date + timedelta(days=6),
            "mode": "targeted",
            "pass_rate": 0.9,
            "total_concepts": 10,
            "passed_concepts": 9
        },
        {
            "review_canvas_path": "离散数学-检验白板-20250118.canvas",
            "date": base_date + timedelta(days=3),
            "mode": "fresh",
            "pass_rate": 0.75,
            "total_concepts": 8,
            "passed_concepts": 6
        },
        {
            "review_canvas_path": "离散数学-检验白板-20250115.canvas",
            "date": base_date,
            "mode": "fresh",
            "pass_rate": 0.5,
            "total_concepts": 8,
            "passed_concepts": 4
        }
    ]


# ═══════════════════════════════════════════════════════════════════════════════
# Test Cases
# ═══════════════════════════════════════════════════════════════════════════════

class TestMultiReviewProgress:
    """Test cases for multi-review progress tracking."""

    @pytest.mark.asyncio
    async def test_multi_review_returns_all_sessions(
        self,
        review_service,
        sample_review_history
    ):
        """
        AC1: Endpoint returns all verification canvases for original.

        [Source: docs/stories/24.4.story.md#AC1]
        """
        # Mock the query method
        review_service._query_review_history_from_graphiti = AsyncMock(
            return_value=sample_review_history
        )

        result = await review_service.get_multi_review_progress("离散数学.canvas")

        assert result["original_canvas_path"] == "离散数学.canvas"
        assert result["review_count"] == 3
        assert len(result["reviews"]) == 3
        assert result["reviews"][0]["mode"] == "targeted"  # Most recent first

    @pytest.mark.asyncio
    async def test_pass_rate_trend_calculation(
        self,
        review_service,
        sample_review_history
    ):
        """
        AC2: Pass rate trend data is chart-ready.

        [Source: docs/stories/24.4.story.md#AC2]
        """
        review_service._query_review_history_from_graphiti = AsyncMock(
            return_value=sample_review_history
        )

        result = await review_service.get_multi_review_progress("离散数学.canvas")

        trend = result["trends"]["pass_rate_trend"]
        assert len(trend) == 3
        assert trend[0]["date"] == "2025-01-15"  # Chronological order
        assert trend[0]["pass_rate"] == 0.5
        assert trend[2]["date"] == "2025-01-21"
        assert trend[2]["pass_rate"] == 0.9

    @pytest.mark.asyncio
    async def test_overall_progress_up_trend(
        self,
        review_service,
        sample_review_history
    ):
        """
        AC4: Overall progress correctly identifies upward trend.

        [Source: docs/stories/24.4.story.md#AC4]
        """
        review_service._query_review_history_from_graphiti = AsyncMock(
            return_value=sample_review_history
        )

        result = await review_service.get_multi_review_progress("离散数学.canvas")

        overall = result["trends"]["overall_progress"]
        assert overall["trend_direction"] == "up"
        assert overall["progress_rate"] == 0.4  # 0.9 - 0.5

    @pytest.mark.asyncio
    async def test_overall_progress_stable_trend(
        self,
        review_service
    ):
        """
        Test overall progress identifies stable trend.

        [Source: docs/stories/24.4.story.md#AC4]
        """
        stable_history = [
            {
                "review_canvas_path": "test-检验白板-20250118.canvas",
                "date": datetime(2025, 1, 18),
                "mode": "fresh",
                "pass_rate": 0.73,
                "total_concepts": 10,
                "passed_concepts": 7
            },
            {
                "review_canvas_path": "test-检验白板-20250115.canvas",
                "date": datetime(2025, 1, 15),
                "mode": "fresh",
                "pass_rate": 0.75,
                "total_concepts": 10,
                "passed_concepts": 7
            }
        ]

        review_service._query_review_history_from_graphiti = AsyncMock(
            return_value=stable_history
        )

        result = await review_service.get_multi_review_progress("test.canvas")

        overall = result["trends"]["overall_progress"]
        assert overall["trend_direction"] == "stable"  # -0.02 is within ±0.05 threshold

    @pytest.mark.asyncio
    async def test_overall_progress_down_trend(
        self,
        review_service
    ):
        """
        Test overall progress identifies downward trend.

        [Source: docs/stories/24.4.story.md#AC4]
        """
        down_history = [
            {
                "review_canvas_path": "test-检验白板-20250118.canvas",
                "date": datetime(2025, 1, 18),
                "mode": "fresh",
                "pass_rate": 0.5,
                "total_concepts": 10,
                "passed_concepts": 5
            },
            {
                "review_canvas_path": "test-检验白板-20250115.canvas",
                "date": datetime(2025, 1, 15),
                "mode": "fresh",
                "pass_rate": 0.8,
                "total_concepts": 10,
                "passed_concepts": 8
            }
        ]

        review_service._query_review_history_from_graphiti = AsyncMock(
            return_value=down_history
        )

        result = await review_service.get_multi_review_progress("test.canvas")

        overall = result["trends"]["overall_progress"]
        assert overall["trend_direction"] == "down"
        assert round(overall["progress_rate"], 2) == -0.3  # 0.5 - 0.8 (rounded for floating point precision)

    @pytest.mark.asyncio
    async def test_no_history_returns_404(
        self,
        review_service
    ):
        """
        AC6: Empty history returns CanvasNotFoundException.

        [Source: docs/stories/24.4.story.md#AC6]
        """
        review_service._query_review_history_from_graphiti = AsyncMock(
            return_value=[]
        )

        with pytest.raises(CanvasNotFoundException) as exc_info:
            await review_service.get_multi_review_progress("nonexistent.canvas")

        assert "No review history" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_single_review_session(
        self,
        review_service
    ):
        """
        Test handling of single review session (trend calculation edge case).
        """
        single_history = [
            {
                "review_canvas_path": "test-检验白板-20250115.canvas",
                "date": datetime(2025, 1, 15),
                "mode": "fresh",
                "pass_rate": 0.75,
                "total_concepts": 8,
                "passed_concepts": 6
            }
        ]

        review_service._query_review_history_from_graphiti = AsyncMock(
            return_value=single_history
        )

        result = await review_service.get_multi_review_progress("test.canvas")

        assert result["review_count"] == 1
        assert len(result["trends"]["pass_rate_trend"]) == 1
        assert result["trends"]["overall_progress"]["trend_direction"] == "stable"
        assert result["trends"]["overall_progress"]["progress_rate"] == 0.0

    @pytest.mark.asyncio
    async def test_graphiti_client_unavailable(
        self,
        mock_canvas_service,
        mock_task_manager
    ):
        """
        Test graceful degradation when Graphiti client is not available.
        """
        # Create service without graphiti_client
        service = ReviewService(
            canvas_service=mock_canvas_service,
            task_manager=mock_task_manager,
            graphiti_client=None
        )

        with pytest.raises(CanvasNotFoundException):
            await service.get_multi_review_progress("test.canvas")


class TestTrendAnalysisCalculation:
    """Test cases for trend analysis calculation logic."""

    def test_calculate_trend_with_empty_reviews(self, review_service):
        """Test trend calculation with no reviews."""
        result = review_service._calculate_trend_analysis([])
        assert result is None

    def test_calculate_trend_with_multiple_reviews(
        self,
        review_service,
        sample_review_history
    ):
        """Test trend calculation with multiple review sessions."""
        result = review_service._calculate_trend_analysis(sample_review_history)

        assert result is not None
        assert "pass_rate_trend" in result
        assert "overall_progress" in result
        assert len(result["pass_rate_trend"]) == 3

    def test_pass_rate_trend_chronological_order(
        self,
        review_service,
        sample_review_history
    ):
        """Test that pass_rate_trend is in chronological order (oldest to newest)."""
        result = review_service._calculate_trend_analysis(sample_review_history)

        trend = result["pass_rate_trend"]
        dates = [t["date"] for t in trend]

        # Verify chronological order
        assert dates == sorted(dates)
        assert trend[0]["pass_rate"] == 0.5  # Oldest
        assert trend[-1]["pass_rate"] == 0.9  # Newest

    def test_date_format_string_handling(self, review_service):
        """Test handling of string date format in trend calculation."""
        reviews_with_string_dates = [
            {
                "review_canvas_path": "test-1.canvas",
                "date": "2025-01-15T10:00:00Z",
                "mode": "fresh",
                "pass_rate": 0.5,
                "total_concepts": 10,
                "passed_concepts": 5
            },
            {
                "review_canvas_path": "test-2.canvas",
                "date": "2025-01-18T10:00:00Z",
                "mode": "fresh",
                "pass_rate": 0.8,
                "total_concepts": 10,
                "passed_concepts": 8
            }
        ]

        result = review_service._calculate_trend_analysis(reviews_with_string_dates)

        assert result["pass_rate_trend"][0]["date"] == "2025-01-18"
        assert result["pass_rate_trend"][1]["date"] == "2025-01-15"


# ═══════════════════════════════════════════════════════════════════════════════
# Integration-like Tests (with mocked Graphiti)
# ═══════════════════════════════════════════════════════════════════════════════

class TestGraphitiQueryIntegration:
    """Test Graphiti query integration with mocked client."""

    @pytest.mark.asyncio
    async def test_query_review_history_filters_verification_canvases(
        self,
        review_service
    ):
        """
        Test that query correctly filters for verification canvas pattern.
        """
        mock_memory_client = MagicMock()
        mock_memory_client.initialize = AsyncMock()
        mock_memory_client.get_learning_history = AsyncMock(return_value=[
            {
                "source_canvas": "离散数学-检验白板-20250115.canvas",
                "timestamp": datetime(2025, 1, 15),
                "mode": "fresh",
                "concept": "逆否命题",
                "score": 30
            },
            {
                "source_canvas": "离散数学.canvas",  # Not a verification canvas
                "timestamp": datetime(2025, 1, 14),
                "mode": "fresh",
                "concept": "集合运算",
                "score": 35
            },
            {
                "source_canvas": "离散数学-检验白板-20250115.canvas",
                "timestamp": datetime(2025, 1, 15),
                "mode": "fresh",
                "concept": "集合运算",
                "score": 25
            }
        ])

        with patch('app.clients.graphiti_client.get_learning_memory_client', return_value=mock_memory_client):
            result = await review_service._query_review_history_from_graphiti("离散数学.canvas")

        # Should only include verification canvas sessions
        assert len(result) == 1
        assert "-检验白板-" in result[0]["review_canvas_path"]
        assert result[0]["total_concepts"] == 2
        assert result[0]["passed_concepts"] == 2  # Both 30 and 25 are >= 24

    @pytest.mark.asyncio
    async def test_pass_rate_calculation_accuracy(
        self,
        review_service
    ):
        """
        Test accurate pass rate calculation (threshold >= 24/40 = 60%).
        """
        mock_memory_client = MagicMock()
        mock_memory_client.initialize = AsyncMock()
        mock_memory_client.get_learning_history = AsyncMock(return_value=[
            {"source_canvas": "test-检验白板-1.canvas", "timestamp": datetime.now(), "mode": "fresh", "concept": "C1", "score": 24},
            {"source_canvas": "test-检验白板-1.canvas", "timestamp": datetime.now(), "mode": "fresh", "concept": "C2", "score": 23},
            {"source_canvas": "test-检验白板-1.canvas", "timestamp": datetime.now(), "mode": "fresh", "concept": "C3", "score": 30},
            {"source_canvas": "test-检验白板-1.canvas", "timestamp": datetime.now(), "mode": "fresh", "concept": "C4", "score": 10},
        ])

        with patch('app.clients.graphiti_client.get_learning_memory_client', return_value=mock_memory_client):
            result = await review_service._query_review_history_from_graphiti("test.canvas")

        assert result[0]["total_concepts"] == 4
        assert result[0]["passed_concepts"] == 2  # 24 and 30 are >= 24
        assert result[0]["pass_rate"] == 0.5
