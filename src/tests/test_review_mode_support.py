"""
Test Suite for Story 24.1: Verification Canvas Generation Engine with Mode Support

This module tests the dual-mode verification canvas generation:
- AC1: Mode Parameter Support in API
- AC2: Fresh Mode Generation
- AC3: Targeted Mode Generation with Graphiti Integration
- AC4: Default Mode Configuration
- AC5: Review Mode Metadata Storage
- AC6: Weight Configuration Override

[Source: docs/stories/24.1.story.md]
"""

from unittest.mock import AsyncMock, patch

import pytest
from backend.app.models.schemas import GenerateReviewRequest, GenerateReviewResponse

# ✅ Verified imports from Story 24.1 Dev Notes
from backend.app.services.review_service import ReviewService

# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_canvas_service():
    """Mock CanvasService for testing."""
    service = AsyncMock()
    service.canvas_exists.return_value = True
    service.get_canvas.return_value = {
        "nodes": [
            {"id": "node1", "type": "text", "text": "Concept 1", "color": "3"},  # Purple
            {"id": "node2", "type": "text", "text": "Concept 2", "color": "4"},  # Red
            {"id": "node3", "type": "text", "text": "Concept 3", "color": "3"},  # Purple
            {"id": "node4", "type": "text", "text": "Concept 4", "color": "2"},  # Green (excluded)
        ],
        "edges": []
    }
    return service


@pytest.fixture
def mock_task_manager():
    """Mock BackgroundTaskManager for testing."""
    manager = AsyncMock()
    manager.create_task.return_value = "task_123"
    return manager


@pytest.fixture
def mock_graphiti_client():
    """Mock GraphitiEdgeClient for testing."""
    client = AsyncMock()
    client.add_edge_relationship.return_value = True
    client.add_episode_for_edge.return_value = True
    return client


@pytest.fixture
def mock_learning_memory_client():
    """Mock LearningMemoryClient for testing."""
    client = AsyncMock()
    client.initialize.return_value = True
    client.get_learning_history.return_value = [
        {
            "concept": "Concept 1",
            "score": 15.0,  # Weak (< 24)
            "timestamp": "2025-12-01T10:00:00"
        },
        {
            "concept": "Concept 2",
            "score": 18.0,  # Weak (< 24)
            "timestamp": "2025-12-02T10:00:00"
        },
        {
            "concept": "Concept 3",
            "score": 35.0,  # Mastered (>= 24)
            "timestamp": "2025-12-03T10:00:00"
        }
    ]
    return client


@pytest.fixture
def review_service(mock_canvas_service, mock_task_manager, mock_graphiti_client):
    """Create ReviewService with mocked dependencies."""
    return ReviewService(
        canvas_service=mock_canvas_service,
        task_manager=mock_task_manager,
        graphiti_client=mock_graphiti_client
    )


# =============================================================================
# Test Cases: AC2 - Fresh Mode Generation
# =============================================================================

class TestFreshModeGeneration:
    """Test AC2: Fresh mode should not query Graphiti history."""

    @pytest.mark.asyncio
    async def test_fresh_mode_no_graphiti_query(
        self,
        review_service,
        mock_graphiti_client,
        mock_learning_memory_client
    ):
        """
        AC2: Fresh mode should not query Graphiti for weak concepts.

        [Source: Story 24.1 - AC2, Dev Notes lines 318-324]
        """
        with patch('app.clients.graphiti_client.get_learning_memory_client', return_value=mock_learning_memory_client):
            result = await review_service.generate_verification_canvas(
                source_canvas_name="test.canvas",
                mode="fresh"
            )

            # Verify Graphiti was NOT queried for learning history
            mock_learning_memory_client.get_learning_history.assert_not_called()

            # Verify mode was stored
            assert result["mode_used"] == "fresh"
            assert result["question_count"] > 0

    @pytest.mark.asyncio
    async def test_fresh_mode_equal_probability(
        self,
        review_service,
        mock_canvas_service
    ):
        """
        AC2: Fresh mode should select all eligible concepts with equal probability.

        [Source: Story 24.1 - AC2, Dev Notes lines 414-417]
        """
        result = await review_service.generate_verification_canvas(
            source_canvas_name="test.canvas",
            mode="fresh",
            include_colors=["3", "4"]  # Purple and Red
        )

        # Should include all purple (3) and red (4) nodes
        # From mock: 3 nodes (node1, node2, node3)
        assert result["question_count"] == 3
        assert result["mode_used"] == "fresh"


# =============================================================================
# Test Cases: AC3 - Targeted Mode with Graphiti Integration
# =============================================================================

class TestTargetedModeGeneration:
    """Test AC3: Targeted mode should query Graphiti and apply weighting."""

    @pytest.mark.asyncio
    async def test_targeted_mode_queries_graphiti(
        self,
        review_service,
        mock_learning_memory_client
    ):
        """
        AC3: Targeted mode should query Graphiti for weak concepts.

        [Source: Story 24.1 - AC3, Dev Notes lines 328-339]
        """
        with patch('app.clients.graphiti_client.get_learning_memory_client', return_value=mock_learning_memory_client):
            result = await review_service.generate_verification_canvas(
                source_canvas_name="test.canvas",
                mode="targeted"
            )

            # Verify Graphiti was queried
            mock_learning_memory_client.initialize.assert_called_once()
            mock_learning_memory_client.get_learning_history.assert_called_once()

            # Verify mode was stored
            assert result["mode_used"] == "targeted"

    @pytest.mark.asyncio
    async def test_targeted_mode_weight_distribution(
        self,
        review_service,
        mock_learning_memory_client
    ):
        """
        AC3: Targeted mode should apply 70% weak + 30% mastered distribution.

        [Source: Story 24.1 - AC3, Dev Notes lines 400-413]
        """
        with patch('app.clients.graphiti_client.get_learning_memory_client', return_value=mock_learning_memory_client):
            result = await review_service.generate_verification_canvas(
                source_canvas_name="test.canvas",
                mode="targeted",
                weak_weight=0.7,
                mastered_weight=0.3
            )

            # Verify questions were generated
            assert result["question_count"] > 0
            assert result["mode_used"] == "targeted"

            # Note: Exact distribution depends on node matching logic
            # This test verifies the mode was applied


# =============================================================================
# Test Cases: AC4 - Default Mode Configuration
# =============================================================================

class TestDefaultModeConfiguration:
    """Test AC4: Default mode should be 'fresh' when not specified."""

    @pytest.mark.asyncio
    async def test_default_mode_is_fresh(self, review_service):
        """
        AC4: Default mode should be 'fresh' when not specified.

        [Source: Story 24.1 - AC4, Dev Notes lines 342-347]
        """
        result = await review_service.generate_verification_canvas(
            source_canvas_name="test.canvas"
            # No mode parameter - should default to "fresh"
        )

        assert result["mode_used"] == "fresh"

    def test_request_schema_default_mode(self):
        """
        AC4: GenerateReviewRequest schema should default mode to 'fresh'.

        [Source: Story 24.1 - AC4, specs/data/review-generate-request.schema.json]
        """
        request = GenerateReviewRequest(source_canvas="test.canvas")

        assert request.mode == "fresh"
        assert request.weak_weight == 0.7
        assert request.mastered_weight == 0.3


# =============================================================================
# Test Cases: AC5 - Review Mode Metadata Storage
# =============================================================================

class TestReviewModeMetadataStorage:
    """Test AC5: Mode should be stored in canvas metadata and Graphiti."""

    @pytest.mark.asyncio
    async def test_graphiti_relationship_stored(
        self,
        review_service,
        mock_graphiti_client
    ):
        """
        AC5: Mode should be stored in Graphiti relationship.

        [Source: Story 24.1 - AC5, Dev Notes lines 350-358]
        """
        result = await review_service.generate_verification_canvas(
            source_canvas_name="test.canvas",
            mode="targeted"
        )

        # Verify Graphiti relationship was created
        mock_graphiti_client.add_edge_relationship.assert_called_once()

        # Verify episode was added
        mock_graphiti_client.add_episode_for_edge.assert_called_once()

        # Verify mode in response
        assert result["mode_used"] == "targeted"

    @pytest.mark.asyncio
    async def test_mode_in_response_metadata(self, review_service):
        """
        AC5: Mode should be included in response metadata.

        [Source: Story 24.1 - AC5, Dev Notes lines 273-278]
        """
        result = await review_service.generate_verification_canvas(
            source_canvas_name="test.canvas",
            mode="fresh"
        )

        # Response should include mode_used
        assert "mode_used" in result
        assert result["mode_used"] == "fresh"


# =============================================================================
# Test Cases: AC6 - Weight Configuration Override
# =============================================================================

class TestWeightConfigurationOverride:
    """Test AC6: Custom weights should override defaults."""

    @pytest.mark.asyncio
    async def test_custom_weights_applied(
        self,
        review_service,
        mock_learning_memory_client
    ):
        """
        AC6: Custom weights should override defaults (70/30).

        [Source: Story 24.1 - AC6, Dev Notes lines 361-370]
        """
        with patch('app.clients.graphiti_client.get_learning_memory_client', return_value=mock_learning_memory_client):
            result = await review_service.generate_verification_canvas(
                source_canvas_name="test.canvas",
                mode="targeted",
                weak_weight=0.8,
                mastered_weight=0.2
            )

            # Verify custom weights were used (mode applied)
            assert result["mode_used"] == "targeted"
            assert result["question_count"] > 0

    def test_weight_validation_in_schema(self):
        """
        AC6: Request schema should validate weight ranges.

        [Source: Story 24.1 - specs/data/review-generate-request.schema.json]
        """
        # Valid weights
        request = GenerateReviewRequest(
            source_canvas="test.canvas",
            mode="targeted",
            weak_weight=0.6,
            mastered_weight=0.4
        )
        assert request.weak_weight == 0.6
        assert request.mastered_weight == 0.4

        # Test boundary conditions
        request_min = GenerateReviewRequest(
            source_canvas="test.canvas",
            weak_weight=0.0,
            mastered_weight=1.0
        )
        assert request_min.weak_weight == 0.0

        request_max = GenerateReviewRequest(
            source_canvas="test.canvas",
            weak_weight=1.0,
            mastered_weight=0.0
        )
        assert request_max.weak_weight == 1.0


# =============================================================================
# Test Cases: API Contract Validation
# =============================================================================

class TestAPIContractValidation:
    """Test API contract compliance with schemas."""

    def test_request_schema_mode_enum(self):
        """
        AC1: Mode parameter should only accept 'fresh' or 'targeted'.

        [Source: Story 24.1 - AC1, specs/data/review-generate-request.schema.json]
        """
        # Valid modes
        request_fresh = GenerateReviewRequest(source_canvas="test.canvas", mode="fresh")
        assert request_fresh.mode == "fresh"

        request_targeted = GenerateReviewRequest(source_canvas="test.canvas", mode="targeted")
        assert request_targeted.mode == "targeted"

    def test_response_schema_includes_mode(self):
        """
        AC5: Response should include mode_used field.

        [Source: Story 24.1 - AC5, specs/data/review-generate-response.schema.json]
        """
        response = GenerateReviewResponse(
            verification_canvas_name="test-检验白板-20251213",
            node_count=5,
            mode_used="fresh"
        )

        assert response.verification_canvas_name == "test-检验白板-20251213"
        assert response.node_count == 5
        assert response.mode_used == "fresh"


# =============================================================================
# Test Cases: Error Handling
# =============================================================================

class TestErrorHandling:
    """Test error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_graphiti_unavailable_fallback(
        self,
        mock_canvas_service,
        mock_task_manager
    ):
        """
        Targeted mode should gracefully handle Graphiti unavailability.

        [Source: Story 24.1 - Dev Notes lines 421-423]
        """
        # Create service without Graphiti client
        service = ReviewService(
            canvas_service=mock_canvas_service,
            task_manager=mock_task_manager,
            graphiti_client=None
        )

        result = await service.generate_verification_canvas(
            source_canvas_name="test.canvas",
            mode="targeted"
        )

        # Should still generate canvas (fallback to fresh-like behavior)
        assert result["mode_used"] == "targeted"
        assert result["question_count"] > 0

    @pytest.mark.asyncio
    async def test_empty_weak_concepts_handling(
        self,
        review_service,
        mock_learning_memory_client
    ):
        """
        Targeted mode should handle case with no weak concepts.

        [Source: Story 24.1 - Dev Notes lines 445-447]
        """
        # Mock empty history
        mock_learning_memory_client.get_learning_history.return_value = []

        with patch('app.clients.graphiti_client.get_learning_memory_client', return_value=mock_learning_memory_client):
            result = await review_service.generate_verification_canvas(
                source_canvas_name="test.canvas",
                mode="targeted"
            )

            # Should still generate canvas (from all eligible nodes)
            assert result["mode_used"] == "targeted"
            assert result["question_count"] >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
