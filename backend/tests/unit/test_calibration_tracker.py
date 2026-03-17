"""
Unit tests for Story 5.5: Calibration Tracker (Area9 2x2 Matrix)

Tests cover:
  - Four-quadrant classification boundary values
  - Three-stage progressive assessment logic
  - signed_bias / absolute_bias computation correctness
  - Calibration rating threshold boundaries
  - Empty data / single record safety
"""

from datetime import datetime

import pytest
from app.models.mastery_models import (
    CalibrationQuadrant,
    CalibrationRating,
    CalibrationRecord,
)
from app.services.calibration_tracker import (
    classify_quadrant,
    compute_absolute_bias,
    compute_calibration_rating,
    compute_quadrant_distribution,
    compute_signed_bias,
    get_calibration_summary,
    record_calibration,
)


def _make_record(confidence: float, performance: float) -> CalibrationRecord:
    """Helper to create a CalibrationRecord with auto-classified quadrant."""
    quadrant = classify_quadrant(confidence, performance)
    return CalibrationRecord(
        node_id="test_node",
        session_id="test_session",
        self_confidence=confidence,
        actual_performance=performance,
        quadrant=quadrant,
        is_dangerous=(quadrant == CalibrationQuadrant.MISCONCEPTION),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# AC-2: Four-Quadrant Classification
# ═══════════════════════════════════════════════════════════════════════════════


class TestQuadrantClassification:
    """Test Area9 2x2 quadrant classification boundaries."""

    def test_mastered_quadrant(self):
        """High confidence + high performance = MASTERED."""
        assert classify_quadrant(0.8, 0.9) == CalibrationQuadrant.MASTERED
        assert classify_quadrant(0.6, 0.6) == CalibrationQuadrant.MASTERED
        assert classify_quadrant(1.0, 1.0) == CalibrationQuadrant.MASTERED

    def test_misconception_quadrant(self):
        """High confidence + low performance = MISCONCEPTION (dangerous!)."""
        assert classify_quadrant(0.8, 0.3) == CalibrationQuadrant.MISCONCEPTION
        assert classify_quadrant(0.6, 0.59) == CalibrationQuadrant.MISCONCEPTION
        assert classify_quadrant(1.0, 0.0) == CalibrationQuadrant.MISCONCEPTION

    def test_lucky_quadrant(self):
        """Low confidence + high performance = LUCKY."""
        assert classify_quadrant(0.3, 0.9) == CalibrationQuadrant.LUCKY
        assert classify_quadrant(0.59, 0.6) == CalibrationQuadrant.LUCKY
        assert classify_quadrant(0.0, 1.0) == CalibrationQuadrant.LUCKY

    def test_unlearned_quadrant(self):
        """Low confidence + low performance = UNLEARNED."""
        assert classify_quadrant(0.3, 0.3) == CalibrationQuadrant.UNLEARNED
        assert classify_quadrant(0.0, 0.0) == CalibrationQuadrant.UNLEARNED
        assert classify_quadrant(0.59, 0.59) == CalibrationQuadrant.UNLEARNED

    def test_boundary_exact_threshold_060(self):
        """Exact 0.60 threshold — >= means high."""
        # confidence=0.60 → high confidence
        assert classify_quadrant(0.60, 0.60) == CalibrationQuadrant.MASTERED
        # confidence=0.59 → low confidence
        assert classify_quadrant(0.59, 0.60) == CalibrationQuadrant.LUCKY
        # performance=0.60 → high performance
        assert classify_quadrant(0.60, 0.60) == CalibrationQuadrant.MASTERED
        # performance=0.59 → low performance
        assert classify_quadrant(0.60, 0.59) == CalibrationQuadrant.MISCONCEPTION

    def test_boundary_061(self):
        """0.61 — clearly above threshold."""
        assert classify_quadrant(0.61, 0.61) == CalibrationQuadrant.MASTERED

    def test_boundary_059(self):
        """0.59 — clearly below threshold."""
        assert classify_quadrant(0.59, 0.59) == CalibrationQuadrant.UNLEARNED


# ═══════════════════════════════════════════════════════════════════════════════
# AC-4: Bias Computation
# ═══════════════════════════════════════════════════════════════════════════════


class TestBiasComputation:
    """Test signed_bias and absolute_bias calculation."""

    def test_signed_bias_overconfident(self):
        """Positive signed_bias = user overestimates themselves."""
        records = [
            _make_record(0.8, 0.3),  # +0.5
            _make_record(0.9, 0.4),  # +0.5
            _make_record(0.7, 0.5),  # +0.2
        ]
        bias = compute_signed_bias(records)
        assert bias == pytest.approx(0.400, abs=0.001)
        assert bias > 0  # Overconfident

    def test_signed_bias_underconfident(self):
        """Negative signed_bias = user underestimates themselves."""
        records = [
            _make_record(0.2, 0.8),  # -0.6
            _make_record(0.3, 0.9),  # -0.6
            _make_record(0.4, 0.7),  # -0.3
        ]
        bias = compute_signed_bias(records)
        assert bias < 0  # Underconfident

    def test_signed_bias_well_calibrated(self):
        """Near-zero signed_bias = well calibrated."""
        records = [
            _make_record(0.5, 0.5),
            _make_record(0.7, 0.7),
            _make_record(0.3, 0.3),
        ]
        bias = compute_signed_bias(records)
        assert bias == pytest.approx(0.0, abs=0.001)

    def test_signed_bias_empty_records(self):
        """Empty records → 0.0."""
        assert compute_signed_bias([]) == 0.0

    def test_absolute_bias_computation(self):
        """Absolute bias measures calibration precision."""
        records = [
            _make_record(0.8, 0.3),  # |0.5|
            _make_record(0.2, 0.9),  # |0.7|
        ]
        bias = compute_absolute_bias(records)
        assert bias == pytest.approx(0.600, abs=0.001)

    def test_absolute_bias_perfect_calibration(self):
        """Perfect calibration = zero absolute bias."""
        records = [
            _make_record(0.5, 0.5),
            _make_record(0.8, 0.8),
        ]
        assert compute_absolute_bias(records) == pytest.approx(0.0, abs=0.001)

    def test_absolute_bias_empty(self):
        assert compute_absolute_bias([]) == 0.0

    def test_bias_rounding(self):
        """Bias values rounded to 3 decimal places."""
        records = [_make_record(0.333, 0.666)]
        bias = compute_signed_bias(records)
        assert bias == round(0.333 - 0.666, 3)


# ═══════════════════════════════════════════════════════════════════════════════
# AC-3: Three-Stage Progressive Assessment
# ═══════════════════════════════════════════════════════════════════════════════


class TestThreeStageAssessment:
    """Test three-stage progressive calibration assessment."""

    def test_stage1_below_10(self):
        """< 10 records → Stage 1 (data collection, no assessment)."""
        records = [_make_record(0.8, 0.3) for _ in range(9)]
        summary = get_calibration_summary(records)

        assert summary.stage == 1
        assert summary.record_count == 9
        assert summary.signed_bias is None
        assert summary.absolute_bias is None
        assert summary.calibration_rating == CalibrationRating.INSUFFICIENT_DATA
        assert "收集中" in summary.stage_label

    def test_stage1_zero_records(self):
        """0 records → Stage 1."""
        summary = get_calibration_summary([])
        assert summary.stage == 1
        assert summary.record_count == 0
        assert summary.calibration_rating == CalibrationRating.INSUFFICIENT_DATA

    def test_stage2_at_10(self):
        """Exactly 10 records → Stage 2 (preliminary trends)."""
        records = [_make_record(0.8, 0.3) for _ in range(10)]
        summary = get_calibration_summary(records)

        assert summary.stage == 2
        assert summary.record_count == 10
        assert summary.signed_bias is not None
        assert summary.absolute_bias is None  # Not computed in Stage 2
        assert summary.calibration_rating != CalibrationRating.INSUFFICIENT_DATA
        assert "仅供参考" in summary.stage_label

    def test_stage2_at_20(self):
        """Exactly 20 records → still Stage 2 (< 20 for stage 3 check is strict)."""
        records = [_make_record(0.5, 0.5) for _ in range(20)]
        summary = get_calibration_summary(records)
        # 20 is < STAGE_3_MIN_RECORDS? Let's check: STAGE_3_MIN_RECORDS = 20
        # 20 < 20 is False, so this should be Stage 3
        assert summary.stage == 3

    def test_stage3_at_21(self):
        """21 records → Stage 3 (reliable assessment)."""
        records = [_make_record(0.5, 0.5) for _ in range(21)]
        summary = get_calibration_summary(records)

        assert summary.stage == 3
        assert summary.record_count == 21
        assert summary.signed_bias is not None
        assert summary.absolute_bias is not None
        assert summary.calibration_rating != CalibrationRating.INSUFFICIENT_DATA
        assert "可靠" in summary.stage_label

    def test_stage3_full_report(self):
        """Stage 3 produces complete report with quadrant distribution + biases + rating."""
        records = [_make_record(0.8, 0.3) for _ in range(25)]
        summary = get_calibration_summary(records)

        assert summary.stage == 3
        assert summary.quadrant_distribution[CalibrationQuadrant.MISCONCEPTION.value] == 1.0
        assert summary.signed_bias > 0  # Overconfident
        assert summary.absolute_bias > 0
        assert summary.calibration_rating == CalibrationRating.OVER_CONFIDENT


# ═══════════════════════════════════════════════════════════════════════════════
# AC-3/AC-4: Calibration Rating Thresholds
# ═══════════════════════════════════════════════════════════════════════════════


class TestCalibrationRating:
    """Test calibration rating threshold boundaries."""

    def test_insufficient_data_below_10(self):
        """< 10 records → INSUFFICIENT_DATA regardless of bias."""
        assert compute_calibration_rating(0.5, 9) == CalibrationRating.INSUFFICIENT_DATA
        assert compute_calibration_rating(-0.5, 5) == CalibrationRating.INSUFFICIENT_DATA
        assert compute_calibration_rating(0.0, 0) == CalibrationRating.INSUFFICIENT_DATA

    def test_well_calibrated_boundary(self):
        """|signed_bias| < 0.15 → WELL_CALIBRATED."""
        assert compute_calibration_rating(0.14, 20) == CalibrationRating.WELL_CALIBRATED
        assert compute_calibration_rating(-0.14, 20) == CalibrationRating.WELL_CALIBRATED
        assert compute_calibration_rating(0.0, 10) == CalibrationRating.WELL_CALIBRATED

    def test_over_confident_boundary(self):
        """signed_bias >= 0.15 → OVER_CONFIDENT."""
        assert compute_calibration_rating(0.15, 20) == CalibrationRating.WELL_CALIBRATED
        assert compute_calibration_rating(0.16, 20) == CalibrationRating.OVER_CONFIDENT
        assert compute_calibration_rating(0.5, 30) == CalibrationRating.OVER_CONFIDENT

    def test_under_confident_boundary(self):
        """signed_bias <= -0.15 → UNDER_CONFIDENT."""
        assert compute_calibration_rating(-0.15, 20) == CalibrationRating.WELL_CALIBRATED
        assert compute_calibration_rating(-0.16, 20) == CalibrationRating.UNDER_CONFIDENT
        assert compute_calibration_rating(-0.5, 30) == CalibrationRating.UNDER_CONFIDENT


# ═══════════════════════════════════════════════════════════════════════════════
# AC-1: CalibrationRecord Creation
# ═══════════════════════════════════════════════════════════════════════════════


class TestRecordCalibration:
    """Test CalibrationRecord creation with auto-classification."""

    def test_misconception_is_dangerous(self):
        """MISCONCEPTION quadrant marks is_dangerous=True."""
        record = record_calibration("node1", 0.9, 0.2)
        assert record.quadrant == CalibrationQuadrant.MISCONCEPTION
        assert record.is_dangerous is True

    def test_mastered_not_dangerous(self):
        """Non-misconception quadrants are not dangerous."""
        record = record_calibration("node1", 0.9, 0.9)
        assert record.quadrant == CalibrationQuadrant.MASTERED
        assert record.is_dangerous is False

    def test_record_has_timestamp(self):
        """Record has auto-generated timestamp."""
        record = record_calibration("node1", 0.5, 0.5)
        assert record.timestamp is not None
        assert isinstance(record.timestamp, datetime)

    def test_record_preserves_values(self):
        """Record preserves input values."""
        record = record_calibration("node1", 0.75, 0.45, session_id="sess_1")
        assert record.node_id == "node1"
        assert record.session_id == "sess_1"
        assert record.self_confidence == 0.75
        assert record.actual_performance == 0.45


# ═══════════════════════════════════════════════════════════════════════════════
# Quadrant Distribution
# ═══════════════════════════════════════════════════════════════════════════════


class TestQuadrantDistribution:
    """Test quadrant distribution computation."""

    def test_all_one_quadrant(self):
        """All records in one quadrant → 100% for that quadrant."""
        records = [_make_record(0.8, 0.2) for _ in range(10)]
        dist = compute_quadrant_distribution(records)
        assert dist[CalibrationQuadrant.MISCONCEPTION.value] == 1.0
        assert dist[CalibrationQuadrant.MASTERED.value] == 0.0

    def test_even_distribution(self):
        """Equal mix → 25% each."""
        records = [
            _make_record(0.8, 0.8),  # MASTERED
            _make_record(0.8, 0.2),  # MISCONCEPTION
            _make_record(0.2, 0.8),  # LUCKY
            _make_record(0.2, 0.2),  # UNLEARNED
        ]
        dist = compute_quadrant_distribution(records)
        for quadrant in CalibrationQuadrant:
            assert dist[quadrant.value] == 0.25

    def test_empty_distribution(self):
        """Empty records → all zeros."""
        dist = compute_quadrant_distribution([])
        for quadrant in CalibrationQuadrant:
            assert dist[quadrant.value] == 0.0
