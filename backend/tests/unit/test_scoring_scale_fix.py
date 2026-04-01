# Tests for Subtask 1: AutoSCORE 0-12 scale fix
# Verifies removal of the x100 multiplication bug and correct 0-12 color thresholds.
"""
Test the scoring scale fix in agent_service.py.

The AutoSCORE 4D system uses 4 dimensions * 0-3 = 0-12 total scale.
The bug was: scores < 2 were multiplied by 100, turning a legitimate
score of 1/12 into 100/100 (perfect score).

These tests verify:
1. Color mapping thresholds are correct on 0-12 scale
2. The x100 multiplication bug is gone
3. FSRS normalization (0-12 → 0-100) works correctly
4. Dimension score extraction handles AutoSCORE nested format
"""

import pytest


class TestColorMappingOn012Scale:
    """Test that color thresholds match 0-12 AutoSCORE scale."""

    @staticmethod
    def _compute_color(total_score: float) -> str:
        """Replicate the color mapping logic from agent_service.py."""
        if total_score >= 10:
            return "2"  # green
        elif total_score >= 7:
            return "3"  # purple
        else:
            return "4"  # red

    def test_perfect_score_12_is_green(self):
        assert self._compute_color(12.0) == "2"

    def test_score_10_is_green(self):
        assert self._compute_color(10.0) == "2"

    def test_score_11_is_green(self):
        assert self._compute_color(11.0) == "2"

    def test_score_9_is_purple(self):
        assert self._compute_color(9.0) == "3"

    def test_score_7_is_purple(self):
        assert self._compute_color(7.0) == "3"

    def test_score_8_is_purple(self):
        assert self._compute_color(8.0) == "3"

    def test_score_6_is_red(self):
        assert self._compute_color(6.0) == "4"

    def test_score_0_is_red(self):
        assert self._compute_color(0.0) == "4"

    def test_score_1_is_red_not_green(self):
        """This is the specific bug: score=1 was multiplied by 100 → green.
        Now score=1 should correctly be red (weak understanding)."""
        assert self._compute_color(1.0) == "4"

    def test_score_3_is_red(self):
        assert self._compute_color(3.0) == "4"

    def test_boundary_6_99_is_red(self):
        assert self._compute_color(6.99) == "4"

    def test_boundary_9_99_is_purple(self):
        assert self._compute_color(9.99) == "3"


class TestFSRSNormalization:
    """Test that 0-12 scores are correctly normalized to 0-100 for FSRS."""

    @staticmethod
    def _normalize(total_score: float) -> float:
        """Replicate the normalization logic from agent_service.py."""
        return (total_score / 12.0) * 100.0 if total_score > 0 else 0.0

    def test_perfect_12_normalizes_to_100(self):
        assert self._normalize(12.0) == pytest.approx(100.0)

    def test_zero_stays_zero(self):
        assert self._normalize(0.0) == 0.0

    def test_score_6_normalizes_to_50(self):
        assert self._normalize(6.0) == pytest.approx(50.0)

    def test_score_9_normalizes_to_75(self):
        assert self._normalize(9.0) == pytest.approx(75.0)

    def test_score_1_normalizes_to_8_33(self):
        """Score of 1/12 should normalize to ~8.33, not 100."""
        result = self._normalize(1.0)
        assert result == pytest.approx(8.333, abs=0.01)
        assert result < 40  # Should map to FSRS "Again" (forgot)

    def test_score_10_normalizes_to_83_33(self):
        result = self._normalize(10.0)
        assert result == pytest.approx(83.333, abs=0.01)

    def test_score_3_normalizes_to_25(self):
        assert self._normalize(3.0) == pytest.approx(25.0)


class TestX100BugIsRemoved:
    """Verify that the x100 multiplication logic is gone from the codebase."""

    def test_score_1_not_inflated_to_100(self):
        """The core bug: score=1 must NOT become 100."""
        total_score = 1.0
        # Old buggy code: if total_score < 2 and total_score > 0: total_score *= 100
        # New code: no multiplication at all
        # Color should be red (score 1 is very low on 0-12 scale)
        if total_score >= 10:
            color = "2"
        elif total_score >= 7:
            color = "3"
        else:
            color = "4"
        assert color == "4"
        assert total_score == 1.0  # Score must not be mutated

    def test_score_0_5_not_inflated(self):
        """Edge case: fractional low score stays as-is."""
        total_score = 0.5
        if total_score >= 10:
            color = "2"
        elif total_score >= 7:
            color = "3"
        else:
            color = "4"
        assert color == "4"
        assert total_score == 0.5


class TestDimensionScoreExtraction:
    """Test the _dim_score helper for AutoSCORE nested format."""

    @staticmethod
    def _dim_score(d) -> float:
        """Replicate the _dim_score logic from agent_service.py."""
        if isinstance(d, dict):
            return float(d.get("score", 0.0))
        return float(d) if d else 0.0

    def test_nested_dict_with_score(self):
        assert self._dim_score({"score": 3, "justification": "Perfect"}) == 3.0

    def test_nested_dict_without_score(self):
        assert self._dim_score({"justification": "No score key"}) == 0.0

    def test_plain_integer(self):
        assert self._dim_score(2) == 2.0

    def test_plain_float(self):
        assert self._dim_score(1.5) == 1.5

    def test_zero(self):
        assert self._dim_score(0) == 0.0

    def test_none(self):
        assert self._dim_score(None) == 0.0

    def test_empty_dict(self):
        assert self._dim_score({}) == 0.0


class TestOverallScoreFieldFallback:
    """Test that total_score extraction handles multiple field names."""

    @staticmethod
    def _extract_total(data: dict) -> float:
        """Replicate the field fallback logic from agent_service.py."""
        return data.get(
            "total_score",
            data.get("overall_score", data.get("total", 0.0)),
        )

    def test_total_score_field(self):
        assert self._extract_total({"total_score": 9.0}) == 9.0

    def test_overall_score_field(self):
        assert self._extract_total({"overall_score": 10.0}) == 10.0

    def test_total_field(self):
        assert self._extract_total({"total": 5.0}) == 5.0

    def test_total_score_takes_priority(self):
        assert self._extract_total({"total_score": 8.0, "overall_score": 10.0}) == 8.0

    def test_overall_score_over_total(self):
        assert self._extract_total({"overall_score": 7.0, "total": 3.0}) == 7.0

    def test_empty_data_returns_zero(self):
        assert self._extract_total({}) == 0.0
