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


@pytest.mark.p1
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

    @pytest.mark.parametrize("scores,expected_level", [
        # EASY: average < 60
        ([30, 40, 50], DifficultyLevel.EASY),
        ([59], DifficultyLevel.EASY),
        ([0, 0, 0], DifficultyLevel.EASY),
        ([55, 58, 52], DifficultyLevel.EASY),
        # MEDIUM: 60 <= average < 80
        ([60, 65, 70], DifficultyLevel.MEDIUM),
        ([79], DifficultyLevel.MEDIUM),
        ([60], DifficultyLevel.MEDIUM),
        ([70, 75, 72], DifficultyLevel.MEDIUM),
        # HARD: average >= 80
        ([80, 85, 90], DifficultyLevel.HARD),
        ([80], DifficultyLevel.HARD),
        ([100, 95, 92], DifficultyLevel.HARD),
        ([85, 88, 82], DifficultyLevel.HARD),
        # Boundary values
        ([59], DifficultyLevel.EASY),     # just below 60
        ([60], DifficultyLevel.MEDIUM),   # exactly 60
        ([79], DifficultyLevel.MEDIUM),   # just below 80
        ([80], DifficultyLevel.HARD),     # exactly 80
    ])
    def test_calculate_difficulty_level(self, scores, expected_level):
        """AC-31.5.2: Scores map to correct difficulty level."""
        assert calculate_difficulty_level(scores) == expected_level


class TestQuestionType:
    """Tests for QuestionType enum and get_question_type_for_difficulty function."""

    def test_question_type_enum_values(self):
        """AC-31.5.3: Verify enum values match schema."""
        assert QuestionType.BREAKTHROUGH.value == "breakthrough"
        assert QuestionType.VERIFICATION.value == "verification"
        assert QuestionType.APPLICATION.value == "application"

    @pytest.mark.parametrize("difficulty,expected_type", [
        (DifficultyLevel.EASY, QuestionType.BREAKTHROUGH),
        (DifficultyLevel.MEDIUM, QuestionType.VERIFICATION),
        (DifficultyLevel.HARD, QuestionType.APPLICATION),
    ])
    def test_difficulty_maps_to_question_type(self, difficulty, expected_type):
        """AC-31.5.3: Each difficulty level maps to correct question type."""
        assert get_question_type_for_difficulty(difficulty) == expected_type


@pytest.mark.p1
class TestMasteryDetection:
    """Tests for is_concept_mastered function."""

    def test_mastery_threshold_constant(self):
        """AC-31.5.4: Verify mastery threshold is 80."""
        assert MASTERY_THRESHOLD == 80
        assert MASTERY_CONSECUTIVE_COUNT == 3

    @pytest.mark.parametrize("scores,expected", [
        # Insufficient scores (< 3) → not mastered
        ([], False),
        ([90], False),
        ([85, 90], False),
        # Low scores → not mastered
        ([70, 75, 78], False),
        ([79, 79, 79], False),
        ([85, 90, 70], False),  # last one too low
        # 3 consecutive >= 80 → mastered
        ([80, 85, 90], True),
        ([100, 100, 100], True),
        ([80, 80, 80], True),
        # Only last 3 matter
        ([50, 60, 85, 90, 88], True),   # low early, last 3 high
        ([90, 95, 85, 70, 85], False),  # high early, last 3 include low
        # Boundary at exactly 80
        ([79, 80, 80], False),  # first of last 3 is 79
    ])
    def test_is_concept_mastered(self, scores, expected):
        """AC-31.5.4: Mastery requires last 3 scores all >= 80."""
        assert is_concept_mastered(scores) is expected


@pytest.mark.p1
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
        assert result.average_score == pytest.approx(88.33, rel=1e-2)
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

    @pytest.mark.parametrize("scores,expected_level,expected_type", [
        ([30, 40, 50], DifficultyLevel.EASY, QuestionType.BREAKTHROUGH),
        ([65, 70, 75], DifficultyLevel.MEDIUM, QuestionType.VERIFICATION),
        ([85, 90, 88], DifficultyLevel.HARD, QuestionType.APPLICATION),
    ])
    def test_question_type_matches_difficulty(self, scores, expected_level, expected_type):
        """Test that question type always matches difficulty level."""
        result = calculate_full_difficulty_result(scores)
        assert result.level == expected_level
        assert result.question_type == expected_type


@pytest.mark.p2
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
