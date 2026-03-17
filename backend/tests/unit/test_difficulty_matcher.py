# Canvas Learning System - Difficulty Matcher Unit Tests
# Story 7.4: 出题难度匹配与提取质量验证
# [Source: _bmad-output/implementation-artifacts/7-4-difficulty-matching-extraction-validation.md]
"""
Unit tests for DifficultyMatcher:
  - Difficulty range computation (proficiency +/- 0.2, clamped)
  - Match judgment logic
  - Sliding window statistics
  - Alert threshold (< 70%)

[Source: Story 7.4 Task 8.1]
"""

import os

import pytest
from app.services.difficulty_matcher import (
    DIFFICULTY_MARGIN,
    WINDOW_SIZE,
    DifficultyMatcher,
)

# ═══════════════════════════════════════════════════════════════════════════════
# Difficulty Range Computation
# ═══════════════════════════════════════════════════════════════════════════════


class TestComputeDifficultyRange:
    """Test difficulty range calculation with clamping."""

    def test_mid_range_proficiency(self):
        lower, upper = DifficultyMatcher.compute_difficulty_range(0.5)
        assert lower == pytest.approx(0.3, abs=0.01)
        assert upper == pytest.approx(0.7, abs=0.01)

    def test_low_proficiency_clamped(self):
        """proficiency=0.05 -> lower clamped to 0.0"""
        lower, upper = DifficultyMatcher.compute_difficulty_range(0.05)
        assert lower == 0.0
        assert upper == pytest.approx(0.25, abs=0.01)

    def test_high_proficiency_clamped(self):
        """proficiency=0.95 -> upper clamped to 1.0"""
        lower, upper = DifficultyMatcher.compute_difficulty_range(0.95)
        assert lower == pytest.approx(0.75, abs=0.01)
        assert upper == 1.0

    def test_zero_proficiency(self):
        lower, upper = DifficultyMatcher.compute_difficulty_range(0.0)
        assert lower == 0.0
        assert upper == pytest.approx(DIFFICULTY_MARGIN, abs=0.01)

    def test_one_proficiency(self):
        lower, upper = DifficultyMatcher.compute_difficulty_range(1.0)
        assert lower == pytest.approx(1.0 - DIFFICULTY_MARGIN, abs=0.01)
        assert upper == 1.0

    def test_proficiency_030(self):
        """Example from spec: proficiency=0.3 -> [0.1, 0.5]"""
        lower, upper = DifficultyMatcher.compute_difficulty_range(0.3)
        assert lower == pytest.approx(0.1, abs=0.01)
        assert upper == pytest.approx(0.5, abs=0.01)

    def test_proficiency_070(self):
        """Example from spec: proficiency=0.7 -> [0.5, 0.9]"""
        lower, upper = DifficultyMatcher.compute_difficulty_range(0.7)
        assert lower == pytest.approx(0.5, abs=0.01)
        assert upper == pytest.approx(0.9, abs=0.01)


# ═══════════════════════════════════════════════════════════════════════════════
# Match Judgment
# ═══════════════════════════════════════════════════════════════════════════════


class TestIsDifficultyMatched:
    """Test match judgment logic."""

    def test_within_range_matched(self):
        assert DifficultyMatcher.is_difficulty_matched(0.5, 0.3, 0.7) is True

    def test_at_lower_boundary_matched(self):
        assert DifficultyMatcher.is_difficulty_matched(0.3, 0.3, 0.7) is True

    def test_at_upper_boundary_matched(self):
        assert DifficultyMatcher.is_difficulty_matched(0.7, 0.3, 0.7) is True

    def test_below_range_not_matched(self):
        assert DifficultyMatcher.is_difficulty_matched(0.2, 0.3, 0.7) is False

    def test_above_range_not_matched(self):
        assert DifficultyMatcher.is_difficulty_matched(0.8, 0.3, 0.7) is False


# ═══════════════════════════════════════════════════════════════════════════════
# Sliding Window Statistics
# ═══════════════════════════════════════════════════════════════════════════════


class TestSlidingWindowStats:
    """Test sliding window statistics and alerting."""

    def _make_matcher(self, tmp_path: str) -> DifficultyMatcher:
        db_path = os.path.join(tmp_path, "test_matcher.db")
        return DifficultyMatcher(db_path)

    def test_empty_window_stats(self, tmp_path):
        matcher = self._make_matcher(str(tmp_path))
        stats = matcher.get_stats()
        assert stats.total_in_window == 0
        assert stats.matched_count == 0
        assert stats.match_rate == 0.0
        assert stats.is_healthy is True  # No data -> no alert

    def test_window_tracks_matches(self, tmp_path):
        matcher = self._make_matcher(str(tmp_path))
        # Manually populate window
        for _ in range(7):
            matcher._window.append(True)
        for _ in range(3):
            matcher._window.append(False)

        stats = matcher.get_stats()
        assert stats.total_in_window == 10
        assert stats.matched_count == 7
        assert stats.match_rate == pytest.approx(0.7, abs=0.01)
        assert stats.is_healthy is True

    def test_below_threshold_not_healthy(self, tmp_path):
        matcher = self._make_matcher(str(tmp_path))
        for _ in range(6):
            matcher._window.append(True)
        for _ in range(4):
            matcher._window.append(False)

        stats = matcher.get_stats()
        assert stats.match_rate == pytest.approx(0.6, abs=0.01)
        assert stats.is_healthy is False

    def test_window_size_capped(self, tmp_path):
        matcher = self._make_matcher(str(tmp_path))
        # Fill beyond window size
        for _i in range(WINDOW_SIZE + 20):
            matcher._window.append(True)

        stats = matcher.get_stats()
        assert stats.total_in_window == WINDOW_SIZE
        assert stats.window_size == WINDOW_SIZE


# ═══════════════════════════════════════════════════════════════════════════════
# Async evaluate with SQLite persistence
# ═══════════════════════════════════════════════════════════════════════════════


class TestEvaluatePersistence:
    """Test that evaluate persists to SQLite and updates window."""

    @pytest.mark.asyncio
    async def test_evaluate_persists_and_updates_window(self, tmp_path):
        db_path = str(tmp_path / "test_eval.db")
        matcher = DifficultyMatcher(db_path)

        # Monkey-patch estimate_difficulty to avoid LLM call
        async def mock_estimate(question: str) -> float:
            return 0.5

        matcher.estimate_difficulty = mock_estimate

        record = await matcher.evaluate(
            node_id="node_1",
            question="What is photosynthesis?",
            proficiency=0.5,
        )

        assert record.node_id == "node_1"
        assert record.proficiency == pytest.approx(0.5, abs=0.01)
        assert record.estimated_difficulty == pytest.approx(0.5, abs=0.01)
        # 0.5 is within [0.3, 0.7] -> matched
        assert record.is_matched is True

        stats = matcher.get_stats()
        assert stats.total_in_window == 1
        assert stats.matched_count == 1

    @pytest.mark.asyncio
    async def test_evaluate_unmatched(self, tmp_path):
        db_path = str(tmp_path / "test_eval2.db")
        matcher = DifficultyMatcher(db_path)

        async def mock_estimate(question: str) -> float:
            return 0.95  # Way above range for proficiency 0.3

        matcher.estimate_difficulty = mock_estimate

        record = await matcher.evaluate(
            node_id="node_2",
            question="Complex question",
            proficiency=0.3,
        )

        assert record.is_matched is False
        assert record.lower_bound == pytest.approx(0.1, abs=0.01)
        assert record.upper_bound == pytest.approx(0.5, abs=0.01)

    @pytest.mark.asyncio
    async def test_hydration_from_db(self, tmp_path):
        """Test that a new matcher instance hydrates its window from DB."""
        db_path = str(tmp_path / "test_hydrate.db")

        # First instance: add some records
        matcher1 = DifficultyMatcher(db_path)

        async def mock_estimate(question: str) -> float:
            return 0.5

        matcher1.estimate_difficulty = mock_estimate

        for i in range(5):
            await matcher1.evaluate(f"node_{i}", f"Question {i}", 0.5)

        assert matcher1.get_stats().total_in_window == 5

        # Second instance: should hydrate from DB
        matcher2 = DifficultyMatcher(db_path)
        await matcher2._ensure_init()

        assert matcher2.get_stats().total_in_window == 5
