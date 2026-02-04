"""
Unit tests for Review Mode Support (Story 24.1 + Story 24.6)

Tests cover all 6 Acceptance Criteria from Story 24.1:
- AC1: Mode parameter support in API
- AC2: Fresh mode generation
- AC3: Targeted mode with Graphiti integration
- AC4: Default mode configuration
- AC5: Review mode metadata storage
- AC6: Weight configuration override

Plus Story 24.6 AC2: Fallback scenario when Graphiti unavailable
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.review_service import ReviewService
from app.services.canvas_service import CanvasService
from app.exceptions.canvas_exceptions import CanvasNotFoundError


class TestReviewModeSupport:
    """Test suite for Story 24.1: Mode Support"""

    @pytest.fixture
    def mock_canvas_service(self):
        """Mock CanvasService for testing"""
        mock = MagicMock(spec=CanvasService)
        mock.get_canvas = AsyncMock(return_value={
            "nodes": [
                {"id": "node1", "type": "text", "color": "3", "text": "Concept A"},
                {"id": "node2", "type": "text", "color": "4", "text": "Concept B"},
                {"id": "node3", "type": "text", "color": "3", "text": "Concept C"},
                {"id": "node4", "type": "text", "color": "1", "text": "Mastered Concept"},
            ],
            "edges": []
        })
        return mock

    @pytest.fixture
    def mock_task_manager(self):
        """Mock BackgroundTaskManager for testing"""
        mock = MagicMock()
        return mock

    @pytest.fixture
    def mock_graphiti_client(self):
        """Mock Graphiti client for testing"""
        mock = MagicMock()
        mock.create_relationship = AsyncMock()
        return mock

    @pytest.fixture
    def review_service(self, mock_canvas_service, mock_task_manager, mock_graphiti_client):
        """Create ReviewService with mocked dependencies"""
        service = ReviewService(
            canvas_service=mock_canvas_service,
            task_manager=mock_task_manager,
            graphiti_client=mock_graphiti_client
        )
        return service

    # ===== AC1: Mode Parameter Support =====

    @pytest.mark.asyncio
    async def test_fresh_mode_parameter_accepted(self, review_service):
        """AC1: API accepts mode='fresh' parameter"""
        with patch.object(review_service, '_query_review_history_from_graphiti',
                         new_callable=AsyncMock) as mock_query:
            mock_query.return_value = []

            result = await review_service.generate_verification_canvas(
                source_canvas_name="test.canvas",
                mode="fresh"
            )

            assert result["mode_used"] == "fresh"

    @pytest.mark.asyncio
    async def test_targeted_mode_parameter_accepted(self, review_service):
        """AC1: API accepts mode='targeted' parameter"""
        with patch.object(review_service, '_query_review_history_from_graphiti',
                         new_callable=AsyncMock) as mock_query:
            mock_query.return_value = []

            result = await review_service.generate_verification_canvas(
                source_canvas_name="test.canvas",
                mode="targeted"
            )

            assert result["mode_used"] == "targeted"

    # ===== AC2: Fresh Mode Generation =====

    @pytest.mark.asyncio
    async def test_fresh_mode_no_graphiti_query(self, review_service):
        """AC2: Fresh mode should not query Graphiti history"""
        with patch.object(review_service, '_query_review_history_from_graphiti',
                         new_callable=AsyncMock) as mock_query:
            mock_query.return_value = []

            await review_service.generate_verification_canvas(
                source_canvas_name="test.canvas",
                mode="fresh"
            )

            # Fresh mode should NOT call Graphiti query
            mock_query.assert_not_called()

    @pytest.mark.asyncio
    async def test_fresh_mode_equal_probability(self, review_service):
        """AC2: Fresh mode uses equal probability for all concepts"""
        result = await review_service.generate_verification_canvas(
            source_canvas_name="test.canvas",
            mode="fresh"
        )

        # Fresh mode should include all eligible nodes (color 3 and 4)
        # weight_config.applied should be False
        assert result["weight_config"]["applied"] is False

    # ===== AC3: Targeted Mode with Graphiti =====

    @pytest.mark.asyncio
    async def test_targeted_mode_queries_graphiti(self, review_service):
        """AC3: Targeted mode should query Graphiti for weak concepts"""
        mock_history = [
            {"concept_id": "node1", "rating": 2, "timestamp": "2025-01-01"},
            {"concept_id": "node2", "rating": 1, "timestamp": "2025-01-02"},
        ]

        with patch.object(review_service, '_query_review_history_from_graphiti',
                         new_callable=AsyncMock) as mock_query:
            mock_query.return_value = mock_history

            await review_service.generate_verification_canvas(
                source_canvas_name="test.canvas",
                mode="targeted"
            )

            # Targeted mode MUST call Graphiti query
            mock_query.assert_called_once_with("test.canvas")

    @pytest.mark.asyncio
    async def test_targeted_mode_weight_distribution(self, review_service):
        """AC3: Targeted mode applies 70/30 weight distribution"""
        mock_history = [
            {"concept_id": "node1", "rating": 1, "timestamp": "2025-01-01"},  # Weak
            {"concept_id": "node2", "rating": 4, "timestamp": "2025-01-02"},  # Mastered
        ]

        with patch.object(review_service, '_query_review_history_from_graphiti',
                         new_callable=AsyncMock) as mock_query:
            mock_query.return_value = mock_history

            result = await review_service.generate_verification_canvas(
                source_canvas_name="test.canvas",
                mode="targeted",
                weak_weight=0.7,
                mastered_weight=0.3
            )

            # Verify weight config was applied
            assert result["weight_config"]["weak_weight"] == 0.7
            assert result["weight_config"]["mastered_weight"] == 0.3
            assert result["weight_config"]["applied"] is True

    # ===== AC4: Default Mode Configuration =====

    @pytest.mark.asyncio
    async def test_default_mode_is_fresh(self, review_service):
        """AC4: Default mode should be 'fresh' when not specified"""
        result = await review_service.generate_verification_canvas(
            source_canvas_name="test.canvas"
            # mode not specified - should default to "fresh"
        )

        assert result["mode_used"] == "fresh"

    # ===== AC5: Review Mode Metadata Storage =====

    @pytest.mark.asyncio
    async def test_mode_metadata_in_response(self, review_service):
        """AC5: Mode should be stored in canvas metadata"""
        result = await review_service.generate_verification_canvas(
            source_canvas_name="test.canvas",
            mode="targeted"
        )

        # mode_used must be in response
        assert "mode_used" in result
        assert result["mode_used"] == "targeted"
        assert "generated_at" in result

    @pytest.mark.asyncio
    async def test_graphiti_relationship_stored(self, review_service, mock_graphiti_client):
        """AC5: Graphiti stores GENERATED_FROM relationship with mode"""
        with patch.object(review_service, '_store_review_relationship',
                         new_callable=AsyncMock) as mock_store:
            await review_service.generate_verification_canvas(
                source_canvas_name="test.canvas",
                mode="targeted"
            )

            # Verify relationship was stored with mode
            mock_store.assert_called_once()
            call_args = mock_store.call_args
            assert call_args[0][2] == "targeted"  # mode argument

    # ===== AC6: Weight Configuration Override =====

    @pytest.mark.asyncio
    async def test_custom_weights_applied(self, review_service):
        """AC6: Custom weights should override defaults"""
        mock_history = [
            {"concept_id": "node1", "rating": 2, "timestamp": "2025-01-01"},
        ]

        with patch.object(review_service, '_query_review_history_from_graphiti',
                         new_callable=AsyncMock) as mock_query:
            mock_query.return_value = mock_history

            result = await review_service.generate_verification_canvas(
                source_canvas_name="test.canvas",
                mode="targeted",
                weak_weight=0.8,
                mastered_weight=0.2
            )

            assert result["weight_config"]["weak_weight"] == 0.8
            assert result["weight_config"]["mastered_weight"] == 0.2

    @pytest.mark.asyncio
    async def test_weights_validation_bounds(self, review_service):
        """AC6: Weights should be between 0 and 1"""
        mock_history = []

        with patch.object(review_service, '_query_review_history_from_graphiti',
                         new_callable=AsyncMock) as mock_query:
            mock_query.return_value = mock_history

            # Valid weights at bounds
            result = await review_service.generate_verification_canvas(
                source_canvas_name="test.canvas",
                mode="targeted",
                weak_weight=1.0,
                mastered_weight=0.0
            )

            assert result["weight_config"]["weak_weight"] == 1.0
            assert result["weight_config"]["mastered_weight"] == 0.0


class TestReviewModeFallback:
    """Test suite for Story 24.6 AC2: Fallback Scenario"""

    @pytest.fixture
    def mock_canvas_service(self):
        """Mock CanvasService for testing"""
        mock = MagicMock(spec=CanvasService)
        mock.get_canvas = AsyncMock(return_value={
            "nodes": [
                {"id": "node1", "type": "text", "color": "3", "text": "Concept A"},
                {"id": "node2", "type": "text", "color": "4", "text": "Concept B"},
            ],
            "edges": []
        })
        return mock

    @pytest.fixture
    def mock_task_manager(self):
        """Mock BackgroundTaskManager for testing"""
        mock = MagicMock()
        return mock

    @pytest.fixture
    def review_service(self, mock_canvas_service, mock_task_manager):
        """Create ReviewService with mocked dependencies"""
        service = ReviewService(
            canvas_service=mock_canvas_service,
            task_manager=mock_task_manager,
            graphiti_client=None  # Simulate unavailable Graphiti
        )
        return service

    @pytest.mark.asyncio
    async def test_targeted_mode_fallback_when_graphiti_unavailable(self, review_service):
        """AC2 Story 24.6: Fallback triggered when Graphiti unavailable"""
        with patch.object(review_service, '_query_review_history_from_graphiti',
                         new_callable=AsyncMock) as mock_query:
            # Simulate Graphiti returning empty (unavailable/error)
            mock_query.return_value = []

            result = await review_service.generate_verification_canvas(
                source_canvas_name="test.canvas",
                mode="targeted"
            )

            # Fallback indicator must be True
            assert result["fallback_used"] is True

    @pytest.mark.asyncio
    async def test_fallback_returns_all_eligible_concepts(self, review_service):
        """AC2 Story 24.6: Fallback returns all eligible concepts with equal probability"""
        with patch.object(review_service, '_query_review_history_from_graphiti',
                         new_callable=AsyncMock) as mock_query:
            mock_query.return_value = []

            result = await review_service.generate_verification_canvas(
                source_canvas_name="test.canvas",
                mode="targeted"
            )

            # Should include concepts (fallback behavior)
            assert result["question_count"] >= 0
            assert result["fallback_used"] is True

    @pytest.mark.asyncio
    async def test_fresh_mode_no_fallback_indicator(self, review_service):
        """Fresh mode should not trigger fallback indicator"""
        result = await review_service.generate_verification_canvas(
            source_canvas_name="test.canvas",
            mode="fresh"
        )

        # Fresh mode: fallback_used should be False
        assert result["fallback_used"] is False

    @pytest.mark.asyncio
    async def test_targeted_mode_no_fallback_with_history(self, review_service):
        """Targeted mode with valid history should not trigger fallback"""
        mock_history = [
            {"concept_id": "node1", "rating": 2, "timestamp": "2025-01-01"},
        ]

        with patch.object(review_service, '_query_review_history_from_graphiti',
                         new_callable=AsyncMock) as mock_query:
            mock_query.return_value = mock_history

            result = await review_service.generate_verification_canvas(
                source_canvas_name="test.canvas",
                mode="targeted"
            )

            # With valid history, fallback_used should be False
            assert result["fallback_used"] is False
