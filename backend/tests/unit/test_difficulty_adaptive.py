"""
Unit tests for Story 31.5: Difficulty Adaptive Algorithm

Tests the difficulty calculation, question type mapping, mastery detection,
and forgetting detection functions.

[Source: docs/stories/31.5.story.md]
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.verification_service import (
    DifficultyLevel,
    QuestionType,
    ForgettingStatus,
    DifficultyResult,
    calculate_difficulty_level,
    get_question_type_for_difficulty,
    is_concept_mastered,
    detect_forgetting,
    calculate_full_difficulty_result,
    DIFFICULTY_THRESHOLDS,
    MASTERY_THRESHOLD,
    MASTERY_CONSECUTIVE_COUNT,
    FORGETTING_DECAY_THRESHOLD,
)


class TestDifficultyLevel:
    """Tests for DifficultyLevel enum and calculate_difficulty_level function."""

    def test_difficulty_level_enum_values(self):
        """AC-31.5.2: Verify enum values match schema."""
        assert DifficultyLevel.EASY.value == "easy"
        assert DifficultyLevel.MEDIUM.value == "medium"
        assert DifficultyLevel.HARD.value == "hard"

    def test_calculate_difficulty_empty_scores(self):
        """AC-31.5.2: Empty scores should return MEDIUM (default)."""
        result = calculate_difficulty_level([])
        assert result == DifficultyLevel.MEDIUM

    def test_calculate_difficulty_easy_level(self):
        """AC-31.5.2: Average < 60 should return EASY."""
        # Test various easy score combinations
        assert calculate_difficulty_level([30, 40, 50]) == DifficultyLevel.EASY
        assert calculate_difficulty_level([59]) == DifficultyLevel.EASY
        assert calculate_difficulty_level([0, 0, 0]) == DifficultyLevel.EASY
        assert calculate_difficulty_level([55, 58, 52]) == DifficultyLevel.EASY

    def test_calculate_difficulty_medium_level(self):
        """AC-31.5.2: 60 <= average < 80 should return MEDIUM."""
        assert calculate_difficulty_level([60, 65, 70]) == DifficultyLevel.MEDIUM
        assert calculate_difficulty_level([79]) == DifficultyLevel.MEDIUM
        assert calculate_difficulty_level([60]) == DifficultyLevel.MEDIUM
        assert calculate_difficulty_level([70, 75, 72]) == DifficultyLevel.MEDIUM

    def test_calculate_difficulty_hard_level(self):
        """AC-31.5.2: Average >= 80 should return HARD."""
        assert calculate_difficulty_level([80, 85, 90]) == DifficultyLevel.HARD
        assert calculate_difficulty_level([80]) == DifficultyLevel.HARD
        assert calculate_difficulty_level([100, 95, 92]) == DifficultyLevel.HARD
        assert calculate_difficulty_level([85, 88, 82]) == DifficultyLevel.HARD

    def test_calculate_difficulty_boundary_values(self):
        """AC-31.5.2: Test boundary conditions."""
        # Exactly 60 -> MEDIUM
        assert calculate_difficulty_level([60]) == DifficultyLevel.MEDIUM
        # Just below 60 -> EASY
        assert calculate_difficulty_level([59]) == DifficultyLevel.EASY
        # Exactly 80 -> HARD
        assert calculate_difficulty_level([80]) == DifficultyLevel.HARD
        # Just below 80 -> MEDIUM
        assert calculate_difficulty_level([79]) == DifficultyLevel.MEDIUM


class TestQuestionType:
    """Tests for QuestionType enum and get_question_type_for_difficulty function."""

    def test_question_type_enum_values(self):
        """AC-31.5.3: Verify enum values match schema."""
        assert QuestionType.BREAKTHROUGH.value == "breakthrough"
        assert QuestionType.VERIFICATION.value == "verification"
        assert QuestionType.APPLICATION.value == "application"

    def test_easy_maps_to_breakthrough(self):
        """AC-31.5.3: EASY difficulty should map to BREAKTHROUGH questions."""
        result = get_question_type_for_difficulty(DifficultyLevel.EASY)
        assert result == QuestionType.BREAKTHROUGH

    def test_medium_maps_to_verification(self):
        """AC-31.5.3: MEDIUM difficulty should map to VERIFICATION questions."""
        result = get_question_type_for_difficulty(DifficultyLevel.MEDIUM)
        assert result == QuestionType.VERIFICATION

    def test_hard_maps_to_application(self):
        """AC-31.5.3: HARD difficulty should map to APPLICATION questions."""
        result = get_question_type_for_difficulty(DifficultyLevel.HARD)
        assert result == QuestionType.APPLICATION


class TestMasteryDetection:
    """Tests for is_concept_mastered function."""

    def test_mastery_threshold_constant(self):
        """AC-31.5.4: Verify mastery threshold is 80."""
        assert MASTERY_THRESHOLD == 80
        assert MASTERY_CONSECUTIVE_COUNT == 3

    def test_not_mastered_insufficient_scores(self):
        """AC-31.5.4: Less than 3 scores should not be mastered."""
        assert is_concept_mastered([]) is False
        assert is_concept_mastered([90]) is False
        assert is_concept_mastered([85, 90]) is False

    def test_not_mastered_low_scores(self):
        """AC-31.5.4: Scores below 80 should not indicate mastery."""
        assert is_concept_mastered([70, 75, 78]) is False
        assert is_concept_mastered([79, 79, 79]) is False
        assert is_concept_mastered([85, 90, 70]) is False  # Last one too low

    def test_mastered_three_consecutive_high(self):
        """AC-31.5.4: 3 consecutive scores >= 80 should indicate mastery."""
        assert is_concept_mastered([80, 85, 90]) is True
        assert is_concept_mastered([100, 100, 100]) is True
        assert is_concept_mastered([80, 80, 80]) is True

    def test_mastered_checks_last_three(self):
        """AC-31.5.4: Only last 3 scores matter for mastery check."""
        # Low early scores, but last 3 are high
        assert is_concept_mastered([50, 60, 85, 90, 88]) is True
        # High early scores, but last 3 include low
        assert is_concept_mastered([90, 95, 85, 70, 85]) is False

    def test_mastered_boundary_at_80(self):
        """AC-31.5.4: Exactly 80 should count toward mastery."""
        assert is_concept_mastered([80, 80, 80]) is True
        assert is_concept_mastered([79, 80, 80]) is False  # First of last 3 is 79


class TestForgettingDetection:
    """Tests for detect_forgetting function."""

    def test_forgetting_threshold_constant(self):
        """AC-31.5.5: Verify forgetting threshold is 30%."""
        assert FORGETTING_DECAY_THRESHOLD == 0.3

    def test_no_forgetting_when_score_stable(self):
        """AC-31.5.5: No forgetting when recent score is similar to average."""
        result = detect_forgetting(recent_score=75, historical_avg=80.0)
        assert result.needs_review is False
        assert result.decay_percentage < 30.0

    def test_no_forgetting_when_score_improved(self):
        """AC-31.5.5: No forgetting when recent score is higher than average."""
        result = detect_forgetting(recent_score=90, historical_avg=70.0)
        assert result.needs_review is False
        assert result.decay_percentage == 0.0  # Clamped to non-negative

    def test_forgetting_when_significant_decline(self):
        """AC-31.5.5: Forgetting detected when decline > 30%."""
        # 50 vs 80 = 37.5% decline
        result = detect_forgetting(recent_score=50, historical_avg=80.0)
        assert result.needs_review is True
        assert result.decay_percentage == 37.5

    def test_forgetting_boundary_at_30_percent(self):
        """AC-31.5.5: Exactly 30% decline should not trigger review."""
        # 70 vs 100 = 30% decline (boundary)
        result = detect_forgetting(recent_score=70, historical_avg=100.0)
        assert result.needs_review is False
        assert result.decay_percentage == 30.0

        # Just over 30% decline
        result = detect_forgetting(recent_score=69, historical_avg=100.0)
        assert result.needs_review is True
        assert result.decay_percentage == 31.0

    def test_forgetting_with_zero_average(self):
        """AC-31.5.5: Zero average should not cause division error."""
        result = detect_forgetting(recent_score=50, historical_avg=0.0)
        assert result.needs_review is False
        assert result.decay_percentage == 0.0


class TestDifficultyResult:
    """Tests for DifficultyResult dataclass and calculate_full_difficulty_result."""

    def test_difficulty_result_to_dict(self):
        """AC-31.5.2: DifficultyResult.to_dict() should match schema format."""
        result = DifficultyResult(
            level=DifficultyLevel.MEDIUM,
            average_score=72.5,
            sample_size=5,
            question_type=QuestionType.VERIFICATION,
            forgetting_status=ForgettingStatus(needs_review=False, decay_percentage=5.0),
            is_mastered=False
        )

        result_dict = result.to_dict()

        assert result_dict["level"] == "medium"
        assert result_dict["average_score"] == 72.5
        assert result_dict["sample_size"] == 5
        assert result_dict["question_type"] == "verification"
        assert result_dict["forgetting_status"]["needs_review"] is False
        assert result_dict["forgetting_status"]["decay_percentage"] == 5.0
        assert result_dict["is_mastered"] is False

    def test_difficulty_result_to_dict_no_forgetting(self):
        """AC-31.5.2: to_dict() handles None forgetting_status."""
        result = DifficultyResult(
            level=DifficultyLevel.EASY,
            average_score=45.0,
            sample_size=3,
            question_type=QuestionType.BREAKTHROUGH,
            forgetting_status=None,
            is_mastered=False
        )

        result_dict = result.to_dict()
        assert result_dict["forgetting_status"] is None

    def test_calculate_full_result_empty_scores(self):
        """calculate_full_difficulty_result with empty scores."""
        result = calculate_full_difficulty_result([])

        assert result.level == DifficultyLevel.MEDIUM
        assert result.average_score == 0.0
        assert result.sample_size == 0
        assert result.question_type == QuestionType.VERIFICATION
        assert result.is_mastered is False

    def test_calculate_full_result_easy_not_mastered(self):
        """calculate_full_difficulty_result for easy difficulty, not mastered."""
        scores = [45, 50, 55]
        result = calculate_full_difficulty_result(scores)

        assert result.level == DifficultyLevel.EASY
        assert result.average_score == 50.0
        assert result.sample_size == 3
        assert result.question_type == QuestionType.BREAKTHROUGH
        assert result.is_mastered is False

    def test_calculate_full_result_hard_mastered(self):
        """calculate_full_difficulty_result for hard difficulty, mastered."""
        scores = [85, 88, 92]
        result = calculate_full_difficulty_result(scores)

        assert result.level == DifficultyLevel.HARD
        assert result.average_score == 88.33
        assert result.sample_size == 3
        assert result.question_type == QuestionType.APPLICATION
        assert result.is_mastered is True

    def test_calculate_full_result_with_forgetting(self):
        """calculate_full_difficulty_result with forgetting detection."""
        scores = [80, 85, 82]  # avg = 82.33
        recent_score = 50  # significant decline

        result = calculate_full_difficulty_result(scores, recent_score=recent_score)

        assert result.forgetting_status is not None
        assert result.forgetting_status.needs_review is True
        assert result.forgetting_status.decay_percentage > 30.0

    def test_calculate_full_result_no_forgetting_without_recent(self):
        """calculate_full_difficulty_result without recent_score has no forgetting."""
        scores = [70, 75, 72]
        result = calculate_full_difficulty_result(scores)

        assert result.forgetting_status is None


class TestIntegration:
    """Integration tests for difficulty adaptive algorithm."""

    def test_full_workflow_easy_to_mastery(self):
        """Test progression from easy to mastery."""
        # Initial: low scores
        scores_initial = [40, 45, 50]
        result = calculate_full_difficulty_result(scores_initial)
        assert result.level == DifficultyLevel.EASY
        assert result.is_mastered is False

        # Progress: medium scores
        scores_medium = [40, 45, 50, 65, 70, 75]
        result = calculate_full_difficulty_result(scores_medium)
        # Average is now higher, might be medium
        assert result.level in [DifficultyLevel.EASY, DifficultyLevel.MEDIUM]

        # Mastery: high scores at end
        scores_mastery = [40, 45, 50, 65, 70, 85, 88, 90]
        result = calculate_full_difficulty_result(scores_mastery)
        assert result.is_mastered is True

    def test_forgetting_triggers_review(self):
        """Test that forgetting triggers review recommendation."""
        # Student had good scores
        historical_scores = [80, 85, 82, 88, 85]  # avg = 84

        # Recent score dropped significantly
        recent_score = 55  # ~35% decline

        result = calculate_full_difficulty_result(historical_scores, recent_score)

        assert result.forgetting_status is not None
        assert result.forgetting_status.needs_review is True
        # Should still show HARD based on historical average
        assert result.level == DifficultyLevel.HARD

    def test_question_type_matches_difficulty(self):
        """Test that question type always matches difficulty level."""
        test_cases = [
            ([30, 40, 50], DifficultyLevel.EASY, QuestionType.BREAKTHROUGH),
            ([65, 70, 75], DifficultyLevel.MEDIUM, QuestionType.VERIFICATION),
            ([85, 90, 88], DifficultyLevel.HARD, QuestionType.APPLICATION),
        ]

        for scores, expected_level, expected_type in test_cases:
            result = calculate_full_difficulty_result(scores)
            assert result.level == expected_level
            assert result.question_type == expected_type


class TestEdgeCases:
    """Edge case tests for difficulty adaptive algorithm."""

    def test_single_score(self):
        """Test with single score."""
        result = calculate_full_difficulty_result([75])
        assert result.level == DifficultyLevel.MEDIUM
        assert result.sample_size == 1
        assert result.is_mastered is False  # Can't be mastered with 1 score

    def test_perfect_scores(self):
        """Test with all perfect scores."""
        result = calculate_full_difficulty_result([100, 100, 100, 100, 100])
        assert result.level == DifficultyLevel.HARD
        assert result.average_score == 100.0
        assert result.is_mastered is True

    def test_zero_scores(self):
        """Test with all zero scores."""
        result = calculate_full_difficulty_result([0, 0, 0])
        assert result.level == DifficultyLevel.EASY
        assert result.average_score == 0.0
        assert result.is_mastered is False

    def test_max_sample_size(self):
        """Test with many scores (sample_size tracking)."""
        scores = [70 + i for i in range(20)]  # 70 to 89
        result = calculate_full_difficulty_result(scores)
        assert result.sample_size == 20

    def test_forgetting_with_zero_recent(self):
        """Test forgetting detection with zero recent score."""
        result = detect_forgetting(recent_score=0, historical_avg=80.0)
        assert result.needs_review is True
        assert result.decay_percentage == 100.0
