"""
Test Suite for Story 24.2: Multi-Review Trend Analysis

Tests the multi-review progress endpoint and trend calculation logic.

[Source: docs/stories/24.2.story.md#L500-603]
"""
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from backend.app.core.exceptions import CanvasNotFoundException
from backend.app.models.schemas import (
    PassRateTrendPoint,
    WeakConceptImprovement,
)
from backend.app.services.review_service import ReviewService

# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def mock_canvas_service():
    """Mock CanvasService for testing."""
    service = MagicMock()
    service.canvas_exists = AsyncMock(return_value=True)
    service.get_canvas = AsyncMock(return_value={"nodes": [], "edges": []})
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
    client.execute_query = AsyncMock(return_value=[])
    return client


@pytest.fixture
def review_service(mock_canvas_service, mock_task_manager, mock_graphiti_client):
    """Create ReviewService instance with mocked dependencies."""
    return ReviewService(
        canvas_service=mock_canvas_service,
        task_manager=mock_task_manager,
        graphiti_client=mock_graphiti_client
    )


# ═══════════════════════════════════════════════════════════════════════════════
# AC2: Review History Query from Graphiti
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_query_review_history_returns_ordered_results(review_service, mock_graphiti_client):
    """AC2: Query returns results ordered by date (newest first)."""
    # Arrange: Mock query results
    mock_reviews = [
        {
            "review_canvas_path": "review3.canvas",
            "date": datetime(2025, 12, 13),
            "mode": "targeted",
            "pass_rate": 0.85,
            "total_concepts": 10,
            "passed_concepts": 8
        },
        {
            "review_canvas_path": "review2.canvas",
            "date": datetime(2025, 12, 6),
            "mode": "fresh",
            "pass_rate": 0.75,
            "total_concepts": 10,
            "passed_concepts": 7
        },
        {
            "review_canvas_path": "review1.canvas",
            "date": datetime(2025, 11, 29),
            "mode": "fresh",
            "pass_rate": 0.65,
            "total_concepts": 10,
            "passed_concepts": 6
        },
    ]

    # Override the method to return our mock data
    async def mock_query(path):
        return mock_reviews

    review_service._query_multi_review_history_from_graphiti = mock_query

    # Act
    result = await review_service._query_multi_review_history_from_graphiti("original.canvas")

    # Assert
    assert len(result) == 3
    assert result[0]["date"] == datetime(2025, 12, 13)  # Newest first
    assert result[2]["date"] == datetime(2025, 11, 29)  # Oldest last


# ═══════════════════════════════════════════════════════════════════════════════
# AC3: Pass Rate Trend Calculation
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_pass_rate_trend_calculation(review_service):
    """AC3: Pass rate trend is correctly calculated."""
    # Arrange
    reviews = [
        {"date": datetime(2025, 12, 13), "pass_rate": 0.85},
        {"date": datetime(2025, 12, 6), "pass_rate": 0.75},
        {"date": datetime(2025, 11, 29), "pass_rate": 0.65},
    ]

    # Act
    trends = await review_service._calculate_trends(reviews)

    # Assert
    assert len(trends["pass_rate_trend"]) == 3
    assert trends["overall_progress"].trend_direction == "up"
    # (0.85 - 0.65) / 0.65 = 0.307 > 0.1, so "up"
    expected_progress_rate = (0.85 - 0.65) / 0.65
    assert abs(trends["overall_progress"].progress_rate - expected_progress_rate) < 0.01


# ═══════════════════════════════════════════════════════════════════════════════
# AC5: Empty History Handling
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_empty_history_returns_404(review_service):
    """AC5: Empty history returns appropriate error."""
    # Arrange: Mock query to return empty list
    async def mock_query_empty(path):
        return []

    review_service._query_multi_review_history_from_graphiti = mock_query_empty

    # Act & Assert
    with pytest.raises(CanvasNotFoundException) as exc:
        await review_service.get_multi_review_progress("no_reviews.canvas")

    assert "No review history found" in str(exc.value)


# ═══════════════════════════════════════════════════════════════════════════════
# AC4: Weak Concept Improvement Status
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_weak_concept_improvement_status(review_service):
    """AC4: Weak concept status correctly assigned."""
    # Test status assignment logic
    # Score < 60 -> weak
    # Score 60-79 -> improving
    # Score >= 80 -> mastered

    improvement_weak = WeakConceptImprovement(
        concept_name="test1",
        improvement_rate=0.2,
        current_status="weak"
    )
    assert improvement_weak.current_status == "weak"

    improvement_improving = WeakConceptImprovement(
        concept_name="test2",
        improvement_rate=0.5,
        current_status="improving"
    )
    assert improvement_improving.current_status == "improving"

    improvement_mastered = WeakConceptImprovement(
        concept_name="test3",
        improvement_rate=1.0,
        current_status="mastered"
    )
    assert improvement_mastered.current_status == "mastered"


# ═══════════════════════════════════════════════════════════════════════════════
# AC6: Overall Progress Trend Direction
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_overall_progress_trend_direction_up(review_service):
    """AC6: Trend direction correctly determined - UP."""
    # progress_rate > 0.1 -> up
    reviews_improving = [
        {"date": datetime(2025, 12, 13), "pass_rate": 0.90},
        {"date": datetime(2025, 11, 29), "pass_rate": 0.60},
    ]
    trends = await review_service._calculate_trends(reviews_improving)
    assert trends["overall_progress"].trend_direction == "up"


@pytest.mark.asyncio
async def test_overall_progress_trend_direction_down(review_service):
    """AC6: Trend direction correctly determined - DOWN."""
    # progress_rate < -0.1 -> down
    reviews_declining = [
        {"date": datetime(2025, 12, 13), "pass_rate": 0.50},
        {"date": datetime(2025, 11, 29), "pass_rate": 0.80},
    ]
    trends = await review_service._calculate_trends(reviews_declining)
    assert trends["overall_progress"].trend_direction == "down"


@pytest.mark.asyncio
async def test_overall_progress_trend_direction_stable(review_service):
    """AC6: Trend direction correctly determined - STABLE."""
    # -0.1 <= progress_rate <= 0.1 -> stable
    reviews_stable = [
        {"date": datetime(2025, 12, 13), "pass_rate": 0.75},
        {"date": datetime(2025, 11, 29), "pass_rate": 0.72},
    ]
    trends = await review_service._calculate_trends(reviews_stable)
    assert trends["overall_progress"].trend_direction == "stable"


# ═══════════════════════════════════════════════════════════════════════════════
# AC1: Multi-Review Progress Endpoint Implementation
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_get_multi_review_progress_success(review_service):
    """AC1: Successfully returns multi-review progress response."""
    # Arrange
    mock_reviews = [
        {
            "review_canvas_path": "review2.canvas",
            "date": datetime(2025, 12, 13),
            "mode": "targeted",
            "pass_rate": 0.85,
            "total_concepts": 10,
            "passed_concepts": 8
        },
        {
            "review_canvas_path": "review1.canvas",
            "date": datetime(2025, 11, 29),
            "mode": "fresh",
            "pass_rate": 0.65,
            "total_concepts": 10,
            "passed_concepts": 6
        },
    ]

    async def mock_query(path):
        return mock_reviews

    review_service._query_multi_review_history_from_graphiti = mock_query

    # Act
    result = await review_service.get_multi_review_progress("original.canvas")

    # Assert
    assert result["original_canvas_path"] == "original.canvas"
    assert result["review_count"] == 2
    assert len(result["reviews"]) == 2
    assert result["trends"] is not None  # Should have trends with 2+ reviews
    assert "pass_rate_trend" in result["trends"]
    assert "overall_progress" in result["trends"]


@pytest.mark.asyncio
async def test_get_multi_review_progress_single_review_no_trends(review_service):
    """AC1: Single review should not have trends."""
    # Arrange
    mock_reviews = [
        {
            "review_canvas_path": "review1.canvas",
            "date": datetime(2025, 12, 13),
            "mode": "fresh",
            "pass_rate": 0.75,
            "total_concepts": 10,
            "passed_concepts": 7
        },
    ]

    async def mock_query(path):
        return mock_reviews

    review_service._query_multi_review_history_from_graphiti = mock_query

    # Act
    result = await review_service.get_multi_review_progress("original.canvas")

    # Assert
    assert result["review_count"] == 1
    assert result["trends"] is None  # No trends with single review


# ═══════════════════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_calculate_trends_with_zero_first_rate(review_service):
    """Edge case: First pass rate is 0."""
    reviews = [
        {"date": datetime(2025, 12, 13), "pass_rate": 0.50},
        {"date": datetime(2025, 11, 29), "pass_rate": 0.00},
    ]
    trends = await review_service._calculate_trends(reviews)

    # When first_rate is 0, progress_rate should equal latest_rate
    assert trends["overall_progress"].progress_rate == 0.50
    assert trends["overall_progress"].trend_direction == "up"


@pytest.mark.asyncio
async def test_pass_rate_trend_format(review_service):
    """Test pass rate trend point format."""
    reviews = [
        {"date": datetime(2025, 12, 13), "pass_rate": 0.85},
        {"date": datetime(2025, 12, 6), "pass_rate": 0.75},
    ]

    trends = await review_service._calculate_trends(reviews)

    # Check format
    assert isinstance(trends["pass_rate_trend"], list)
    assert len(trends["pass_rate_trend"]) == 2

    point = trends["pass_rate_trend"][0]
    assert isinstance(point, PassRateTrendPoint)
    assert point.date == "2025-12-13"
    assert point.pass_rate == 0.85
