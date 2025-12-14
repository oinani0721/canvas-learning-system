# ✅ Verified from Story 24.3 Testing Requirements (lines 686-761)
"""
Unit tests for weighted selection in ReviewService.

Tests AC2 (Configurable Weight Distribution), AC3 (Weighted Concept Selection).

Story: 24.3 - Intelligent Weight Algorithm for Targeted Review
"""
from unittest.mock import MagicMock

import pytest
from backend.app.services.review_service import ReviewService
from backend.app.services.weight_calculator import ConceptWeightData


class TestWeightedSelection:

    @pytest.fixture
    def review_service(self):
        """Provide a ReviewService instance with mocked dependencies."""
        canvas_service = MagicMock()
        task_manager = MagicMock()
        graphiti_client = MagicMock()
        return ReviewService(canvas_service, task_manager, graphiti_client)

    @pytest.mark.asyncio
    async def test_default_weights_70_30(self, review_service):
        """AC2: Default weights are 70% weak, 30% mastered."""
        # Create a balanced dataset with clear weak/mastered separation
        weight_data = [
            ConceptWeightData("c1", "Weak1", 0.9, 5, 1.2, 6, 15, "weak"),
            ConceptWeightData("c2", "Weak2", 0.85, 4, 1.5, 5, 12, "weak"),
            ConceptWeightData("c3", "Weak3", 0.8, 4, 1.6, 5, 10, "weak"),
            ConceptWeightData("c4", "Weak4", 0.75, 3, 1.8, 4, 9, "weak"),
            ConceptWeightData("c5", "Weak5", 0.7, 3, 1.9, 4, 8, "weak"),
            ConceptWeightData("c6", "Weak6", 0.65, 2, 2.0, 4, 7, "weak"),
            ConceptWeightData("c7", "Weak7", 0.62, 2, 2.1, 4, 7, "weak"),
            ConceptWeightData("c8", "Mastered1", 0.2, 0, 3.9, 6, 2, "mastered"),
            ConceptWeightData("c9", "Mastered2", 0.25, 0, 3.8, 6, 3, "mastered"),
            ConceptWeightData("c10", "Mastered3", 0.3, 0, 3.7, 5, 4, "mastered"),
        ]

        # Test single selection to verify target counts
        selected = await review_service._apply_weighted_selection(
            weight_data,
            question_count=10,
            weak_weight=0.7,
            mastered_weight=0.3
        )

        # Count actual distribution
        weak_selected = sum(1 for c in selected if c.category == "weak")
        mastered_selected = sum(1 for c in selected if c.category == "mastered")

        # With 10 questions, should get 7 weak + 3 mastered
        assert weak_selected == 7, f"Expected 7 weak, got {weak_selected}"
        assert mastered_selected == 3, f"Expected 3 mastered, got {mastered_selected}"
        assert len(selected) == 10

    @pytest.mark.asyncio
    async def test_custom_weights_applied(self, review_service):
        """AC2: Custom weights override defaults."""
        weight_data = [
            ConceptWeightData("c1", "Weak1", 0.8, 3, 1.5, 5, 10, "weak"),
            ConceptWeightData("c2", "Weak2", 0.7, 2, 2.0, 4, 8, "weak"),
            ConceptWeightData("c3", "Mastered1", 0.2, 0, 3.8, 6, 5, "mastered"),
            ConceptWeightData("c4", "Mastered2", 0.3, 0, 3.5, 5, 7, "mastered"),
        ]

        selected = await review_service._apply_weighted_selection(
            weight_data,
            question_count=4,
            weak_weight=0.5,
            mastered_weight=0.5
        )

        # With 50/50 split and 4 questions, should get 2 weak + 2 mastered
        assert len(selected) == 4

        weak_selected = sum(1 for c in selected if c.category == "weak")
        mastered_selected = sum(1 for c in selected if c.category == "mastered")

        # Should be approximately 2 and 2
        assert weak_selected == 2
        assert mastered_selected == 2

    @pytest.mark.asyncio
    async def test_weight_sum_validation(self, review_service):
        """AC2: Weights must sum to 1.0."""
        weight_data = [
            ConceptWeightData("c1", "Weak1", 0.8, 3, 1.5, 5, 10, "weak"),
        ]

        with pytest.raises(ValueError, match="must equal 1.0"):
            await review_service._apply_weighted_selection(
                weight_data,
                question_count=2,
                weak_weight=0.6,
                mastered_weight=0.6  # Sum = 1.2, invalid
            )

    @pytest.mark.asyncio
    async def test_weight_sum_with_tolerance(self, review_service):
        """AC2: Weights with small floating point error are accepted."""
        weight_data = [
            ConceptWeightData("c1", "Weak1", 0.8, 3, 1.5, 5, 10, "weak"),
            ConceptWeightData("c2", "Mastered1", 0.2, 0, 3.8, 6, 5, "mastered"),
        ]

        # Should not raise (within 0.01 tolerance)
        selected = await review_service._apply_weighted_selection(
            weight_data,
            question_count=2,
            weak_weight=0.701,
            mastered_weight=0.299  # Sum = 1.0 within tolerance
        )

        assert len(selected) <= 2

    @pytest.mark.asyncio
    async def test_insufficient_weak_concepts(self, review_service):
        """AC3: Handles case when not enough weak concepts available."""
        weight_data = [
            ConceptWeightData("c1", "Weak1", 0.8, 3, 1.5, 5, 10, "weak"),  # Only 1 weak
            ConceptWeightData("c2", "Mastered1", 0.2, 0, 3.8, 6, 5, "mastered"),
            ConceptWeightData("c3", "Mastered2", 0.3, 0, 3.5, 5, 7, "mastered"),
            ConceptWeightData("c4", "Mastered3", 0.25, 0, 3.7, 6, 6, "mastered"),
        ]

        # Request 10 questions with 70% weak (7 weak needed, but only 1 available)
        selected = await review_service._apply_weighted_selection(
            weight_data,
            question_count=4,  # Reduced to match available concepts
            weak_weight=0.7,
            mastered_weight=0.3
        )

        # Should still select 4 concepts, filling from available
        assert len(selected) == 4

        # Should have selected the 1 weak concept
        weak_selected = sum(1 for c in selected if c.category == "weak")
        assert weak_selected == 1

    @pytest.mark.asyncio
    async def test_all_borderline_concepts(self, review_service):
        """AC4: New concepts (borderline) are included correctly."""
        weight_data = [
            ConceptWeightData("c1", "New1", 0.5, 0, 0.0, 0, 0, "borderline"),
            ConceptWeightData("c2", "New2", 0.5, 0, 0.0, 0, 0, "borderline"),
            ConceptWeightData("c3", "New3", 0.5, 0, 0.0, 0, 0, "borderline"),
            ConceptWeightData("c4", "New4", 0.5, 0, 0.0, 0, 0, "borderline"),
        ]

        selected = await review_service._apply_weighted_selection(
            weight_data,
            question_count=2,
            weak_weight=0.7,
            mastered_weight=0.3
        )

        # Should select 2 concepts from borderline
        assert len(selected) == 2
        assert all(c.category == "borderline" for c in selected)

    @pytest.mark.asyncio
    async def test_weighted_sampling_probability(self, review_service):
        """AC3: Higher weakness_score has higher selection probability."""
        # Create concepts with very different weakness scores
        concepts = [
            ConceptWeightData("c1", "VeryWeak", 0.9, 5, 1.2, 6, 15, "weak"),
            ConceptWeightData("c2", "SlightlyWeak", 0.6, 2, 2.5, 4, 8, "weak"),
        ]

        # Sample many times and count selections
        c1_count = 0
        c2_count = 0
        iterations = 1000

        for _ in range(iterations):
            selected = review_service._weighted_sample(concepts, 1)
            if selected:
                if selected[0].concept_id == "c1":
                    c1_count += 1
                elif selected[0].concept_id == "c2":
                    c2_count += 1

        # c1 (0.9 score) should be selected more often than c2 (0.6 score)
        # Expected ratio: 0.9 / (0.9 + 0.6) = 0.6 (60% for c1)
        c1_ratio = c1_count / iterations

        assert c1_ratio > 0.5, f"VeryWeak concept selected {c1_ratio:.1%}, expected >50%"
        assert c1_ratio < 0.7, f"VeryWeak concept selected {c1_ratio:.1%}, expected <70%"

    @pytest.mark.asyncio
    async def test_empty_concepts_list(self, review_service):
        """Edge case: Empty concepts list returns empty selection."""
        selected = await review_service._apply_weighted_selection(
            [],
            question_count=5,
            weak_weight=0.7,
            mastered_weight=0.3
        )

        assert selected == []

    @pytest.mark.asyncio
    async def test_question_count_larger_than_available(self, review_service):
        """Edge case: Requesting more questions than concepts available."""
        weight_data = [
            ConceptWeightData("c1", "Weak1", 0.8, 3, 1.5, 5, 10, "weak"),
            ConceptWeightData("c2", "Mastered1", 0.2, 0, 3.8, 6, 5, "mastered"),
        ]

        selected = await review_service._apply_weighted_selection(
            weight_data,
            question_count=10,  # More than 2 available
            weak_weight=0.7,
            mastered_weight=0.3
        )

        # Should return all available concepts
        assert len(selected) == 2

    @pytest.mark.asyncio
    async def test_zero_weakness_scores(self, review_service):
        """Edge case: All concepts have zero weakness score (equal probability)."""
        concepts = [
            ConceptWeightData("c1", "Zero1", 0.0, 0, 4.0, 5, 2, "mastered"),
            ConceptWeightData("c2", "Zero2", 0.0, 0, 4.0, 5, 2, "mastered"),
            ConceptWeightData("c3", "Zero3", 0.0, 0, 4.0, 5, 2, "mastered"),
        ]

        # Should fall back to random.sample (equal probability)
        selected = review_service._weighted_sample(concepts, 2)

        assert len(selected) == 2
        # All have equal chance, no assertion on specific selection
