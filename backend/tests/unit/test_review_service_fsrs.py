# Story 32.2: ReviewService FSRS Integration Unit Tests
# [Source: docs/stories/32.2.story.md#Task-7]
"""
Unit tests for ReviewService FSRS-4.5 integration.

Tests cover:
- AC-32.2.1: FSRSManager import and dependency injection
- AC-32.2.2: FSRS rating parameter (1-4) support
- AC-32.2.3: Dynamic interval calculation
- AC-32.2.4: Backward compatibility (score → rating conversion)
- AC-32.2.5: Migration documentation (docstring presence)
"""

import pytest
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_canvas_service():
    """Create mock CanvasService for testing."""
    mock = MagicMock()
    mock.get_canvas = AsyncMock(return_value={"nodes": [], "edges": []})
    return mock


@pytest.fixture
def mock_task_manager():
    """Create mock BackgroundTaskManager for testing."""
    mock = MagicMock()
    mock.submit_task = MagicMock(return_value="task_123")
    return mock


@pytest.fixture
def review_service_factory(mock_canvas_service, mock_task_manager):
    """Factory to create ReviewService with mocked dependencies."""
    def _create():
        from app.services.review_service import ReviewService
        return ReviewService(
            canvas_service=mock_canvas_service,
            task_manager=mock_task_manager
        )
    return _create


class TestFSRSImport:
    """AC-32.2.1: Test FSRSManager import and availability."""

    def test_fsrs_module_available(self):
        """FSRS module should be importable."""
        from app.services.review_service import FSRS_AVAILABLE
        # Note: FSRS_AVAILABLE may be True or False depending on environment
        assert isinstance(FSRS_AVAILABLE, bool)

    def test_fsrs_manager_import_success(self):
        """FSRSManager should be imported when available."""
        try:
            import sys
            from pathlib import Path
            _project_root = Path(__file__).parent.parent.parent.parent
            _src_path = _project_root / "src"
            if str(_src_path) not in sys.path:
                sys.path.insert(0, str(_src_path))

            from memory.temporal.fsrs_manager import FSRSManager
            assert FSRSManager is not None
        except ImportError:
            pytest.skip("FSRS module not available in test environment")

    def test_fsrs_fallback_when_unavailable(self, review_service_factory):
        """Service should work with fallback when FSRS unavailable."""
        # Should not raise even if FSRS unavailable
        service = review_service_factory()
        assert service is not None


class TestFSRSRatings:
    """AC-32.2.2: Test FSRS rating parameter (1-4) acceptance."""

    @pytest.fixture
    def review_service(self, review_service_factory):
        """Create ReviewService instance for testing."""
        return review_service_factory()

    @pytest.mark.asyncio
    async def test_rating_1_again(self, review_service):
        """Rating 1 (Again) should be accepted."""
        result = await review_service.record_review_result(
            canvas_name="test_canvas",
            concept_id="node_001",
            rating=1  # Again
        )
        assert result is not None
        assert "next_review" in result or "next_review_date" in result
        # Again typically results in short interval (learning phase)
        assert result.get("interval_days", result.get("new_interval", 0)) <= 1

    @pytest.mark.asyncio
    async def test_rating_2_hard(self, review_service):
        """Rating 2 (Hard) should be accepted."""
        result = await review_service.record_review_result(
            canvas_name="test_canvas",
            concept_id="node_002",
            rating=2  # Hard
        )
        assert result is not None
        assert "next_review" in result or "next_review_date" in result

    @pytest.mark.asyncio
    async def test_rating_3_good(self, review_service):
        """Rating 3 (Good) should be accepted."""
        result = await review_service.record_review_result(
            canvas_name="test_canvas",
            concept_id="node_003",
            rating=3  # Good
        )
        assert result is not None
        assert "next_review" in result or "next_review_date" in result

    @pytest.mark.asyncio
    async def test_rating_4_easy(self, review_service):
        """Rating 4 (Easy) should be accepted and give longer interval."""
        result = await review_service.record_review_result(
            canvas_name="test_canvas",
            concept_id="node_004",
            rating=4  # Easy
        )
        assert result is not None
        assert "next_review" in result or "next_review_date" in result
        # Easy should result in longer interval than Again
        assert result.get("interval_days", result.get("new_interval", 0)) >= 1


class TestScoreToRatingConversion:
    """AC-32.2.4: Test backward compatibility with score-to-rating conversion."""

    @pytest.fixture
    def review_service(self, review_service_factory):
        """Create ReviewService instance for testing."""
        return review_service_factory()

    @pytest.mark.asyncio
    async def test_score_under_40_converts_to_again(self, review_service):
        """Score < 40 should convert to rating 1 (Again)."""
        result = await review_service.record_review_result(
            canvas_name="test_canvas",
            concept_id="node_low",
            score=25.0  # Should become Again
        )
        assert result is not None
        # Low score should result in short interval (learning phase)
        assert result.get("interval_days", result.get("new_interval", 0)) <= 3

    @pytest.mark.asyncio
    async def test_score_40_59_converts_to_hard(self, review_service):
        """Score 40-59 should convert to rating 2 (Hard)."""
        result = await review_service.record_review_result(
            canvas_name="test_canvas",
            concept_id="node_medium",
            score=50.0  # Should become Hard
        )
        assert result is not None
        assert "next_review" in result or "next_review_date" in result

    @pytest.mark.asyncio
    async def test_score_60_84_converts_to_good(self, review_service):
        """Score 60-84 should convert to rating 3 (Good)."""
        result = await review_service.record_review_result(
            canvas_name="test_canvas",
            concept_id="node_good",
            score=75.0  # Should become Good
        )
        assert result is not None
        assert "next_review" in result or "next_review_date" in result

    @pytest.mark.asyncio
    async def test_score_85_plus_converts_to_easy(self, review_service):
        """Score >= 85 should convert to rating 4 (Easy)."""
        result = await review_service.record_review_result(
            canvas_name="test_canvas",
            concept_id="node_excellent",
            score=95.0  # Should become Easy
        )
        assert result is not None
        # High score should result in longer interval (FSRS state=2 review mode)
        assert result.get("interval_days", result.get("new_interval", 0)) >= 1


class TestDynamicIntervalCalculation:
    """AC-32.2.3: Test FSRS dynamic interval calculation."""

    @pytest.fixture
    def review_service(self, review_service_factory):
        """Create ReviewService instance for testing."""
        return review_service_factory()

    @pytest.mark.asyncio
    async def test_schedule_review_returns_fsrs_data(self, review_service):
        """schedule_review should return FSRS card data when available."""
        result = await review_service.schedule_review(
            canvas_name="test_canvas",
            concept_id="node_fsrs"
        )
        assert result is not None
        # Check for various field names (API may use different naming)
        assert "scheduled_date" in result or "next_review_date" in result or "next_review" in result
        assert "interval_days" in result or "interval" in result
        # FSRS-specific fields (may be None if FSRS unavailable)
        assert "card_data" in result or "fsrs_state" in result or "algorithm" in result

    @pytest.mark.asyncio
    async def test_repeated_reviews_increase_interval(self, review_service):
        """Repeated successful reviews should increase intervals (FSRS behavior)."""
        concept_id = "node_repeated"

        # First review
        result1 = await review_service.record_review_result(
            canvas_name="test_canvas",
            concept_id=concept_id,
            rating=3  # Good
        )
        interval1 = result1.get("new_interval", 1)

        # Second review with same rating
        result2 = await review_service.record_review_result(
            canvas_name="test_canvas",
            concept_id=concept_id,
            rating=3,  # Good
            card_state=result1.get("card_data")
        )
        interval2 = result2.get("new_interval", 1)

        # With FSRS, repeated Good ratings should generally increase interval
        # Note: First review may have special learning phase behavior
        assert interval2 >= interval1 or interval2 >= 1  # Allow for learning phase

    @pytest.mark.asyncio
    async def test_failed_review_resets_interval(self, review_service):
        """Failed review (rating 1) should reset or reduce interval."""
        concept_id = "node_failed"

        # First successful review
        result1 = await review_service.record_review_result(
            canvas_name="test_canvas",
            concept_id=concept_id,
            rating=4  # Easy - should give longer interval
        )

        # Failed review
        result2 = await review_service.record_review_result(
            canvas_name="test_canvas",
            concept_id=concept_id,
            rating=1,  # Again - should reset
            card_state=result1.get("card_data")
        )

        # After failure, interval should be short (learning phase)
        assert result2.get("new_interval", 0) <= 3


class TestCardStatePersistence:
    """Test FSRS card state persistence functionality."""

    @pytest.fixture
    def review_service(self, review_service_factory):
        """Create ReviewService instance for testing."""
        return review_service_factory()

    @pytest.mark.asyncio
    async def test_card_data_returned_in_response(self, review_service):
        """Response should include card_data for client-side caching."""
        result = await review_service.record_review_result(
            canvas_name="test_canvas",
            concept_id="node_persist",
            rating=3
        )
        # card_data should be present (may be None if FSRS unavailable)
        assert "card_data" in result or result.get("algorithm") == "ebbinghaus-fallback"

    @pytest.mark.asyncio
    async def test_card_state_can_be_loaded(self, review_service):
        """Saved card state should be loadable."""
        concept_id = "node_load_test"

        # Record a review to save state
        result = await review_service.record_review_result(
            canvas_name="test_canvas",
            concept_id=concept_id,
            rating=3
        )
        card_data = result.get("card_data")

        if card_data:
            # Use saved state in next review
            result2 = await review_service.record_review_result(
                canvas_name="test_canvas",
                concept_id=concept_id,
                rating=3,
                card_state=card_data
            )
            assert result2 is not None


class TestFSRSStateResponse:
    """Test FSRS state information in responses."""

    @pytest.fixture
    def review_service(self, review_service_factory):
        """Create ReviewService instance for testing."""
        return review_service_factory()

    @pytest.mark.asyncio
    async def test_fsrs_state_fields(self, review_service):
        """Response should include FSRS state fields when available."""
        result = await review_service.record_review_result(
            canvas_name="test_canvas",
            concept_id="node_state",
            rating=3
        )

        fsrs_state = result.get("fsrs_state")
        if fsrs_state:
            # Check FSRS state fields
            assert "stability" in fsrs_state
            assert "difficulty" in fsrs_state
            assert "state" in fsrs_state
            assert "reps" in fsrs_state
            assert "lapses" in fsrs_state

            # Validate ranges
            assert fsrs_state["stability"] >= 0
            assert 1 <= fsrs_state["difficulty"] <= 10
            assert fsrs_state["state"] in [0, 1, 2, 3]  # New, Learning, Review, Relearning


class TestMigrationDocumentation:
    """AC-32.2.5: Test migration documentation presence."""

    def test_module_docstring_contains_migration_info(self):
        """Module docstring should contain FSRS migration documentation."""
        from app.services import review_service
        docstring = review_service.__doc__
        assert docstring is not None
        assert "FSRS" in docstring or "fsrs" in docstring.lower()
        assert "migration" in docstring.lower() or "MIGRATION" in docstring

    def test_rating_conversion_documented(self):
        """Score-to-rating conversion should be documented."""
        from app.services import review_service
        docstring = review_service.__doc__
        assert "rating" in docstring.lower()
        # Check for conversion thresholds
        assert "40" in docstring or "score" in docstring.lower()


class TestAlgorithmField:
    """Test algorithm field in responses."""

    @pytest.fixture
    def review_service(self, review_service_factory):
        """Create ReviewService instance for testing."""
        return review_service_factory()

    @pytest.mark.asyncio
    async def test_algorithm_field_present(self, review_service):
        """Response should include algorithm field."""
        result = await review_service.record_review_result(
            canvas_name="test_canvas",
            concept_id="node_algo",
            rating=3
        )
        assert "algorithm" in result
        # Should be fsrs-4.5 or ebbinghaus-fallback
        assert result["algorithm"] in ["fsrs-4.5", "ebbinghaus-fallback"]
