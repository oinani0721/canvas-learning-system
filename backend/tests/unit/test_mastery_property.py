"""Property-based tests for mastery domain models.

Uses Hypothesis to verify invariants that must hold for all valid inputs:
- CalibrationRecord accepts any (confidence, performance) in [0,1]
- FusionResult.fused_mastery always in [0,1], is_fallback is bool
- CalibrationSummary.stage always 1-3
- MASTERY_LABELS and MASTERY_COLORS cover levels 0-4
"""

from hypothesis import given, settings, strategies as st

from app.models.mastery_models import (
    CalibrationRecord,
    CalibrationSummary,
    FusionResult,
)
from app.models.mastery_state import (
    DEFAULT_BKT_PARAMS,
    MASTERY_COLORS,
    MASTERY_LABELS,
)
from tests.strategies import mastery_scores, node_ids


@given(confidence=mastery_scores, performance=mastery_scores, nid=node_ids)
@settings(max_examples=20)
def test_calibration_record_valid_range(
    confidence: float, performance: float, nid: str
) -> None:
    """Any valid (confidence, performance) pair in [0,1] creates a valid CalibrationRecord."""
    record = CalibrationRecord(
        node_id=nid,
        self_confidence=confidence,
        actual_performance=performance,
    )
    assert 0.0 <= record.self_confidence <= 1.0
    assert 0.0 <= record.actual_performance <= 1.0
    assert isinstance(record.node_id, str)
    assert len(record.node_id) > 0


@given(mastery=mastery_scores)
@settings(max_examples=20)
def test_fusion_result_invariants(mastery: float) -> None:
    """FusionResult.fused_mastery always in [0,1] and is_fallback is bool."""
    result = FusionResult(fused_mastery=mastery)
    assert 0.0 <= result.fused_mastery <= 1.0
    assert isinstance(result.is_fallback, bool)
    assert result.active_signal_count >= 0


@given(mastery=mastery_scores)
@settings(max_examples=20)
def test_fusion_result_fallback_flag(mastery: float) -> None:
    """FusionResult with is_fallback=True is still valid."""
    result = FusionResult(fused_mastery=mastery, is_fallback=True)
    assert result.is_fallback is True
    assert 0.0 <= result.fused_mastery <= 1.0


@given(
    stage=st.integers(min_value=1, max_value=3),
    count=st.integers(min_value=0, max_value=1000),
)
@settings(max_examples=20)
def test_calibration_summary_stage_range(stage: int, count: int) -> None:
    """CalibrationSummary.stage always 1-3."""
    summary = CalibrationSummary(stage=stage, record_count=count)
    assert 1 <= summary.stage <= 3
    assert summary.record_count >= 0


def test_mastery_labels_cover_0_to_4() -> None:
    """MASTERY_LABELS must have entries for levels 0 through 4."""
    for level in range(5):
        assert level in MASTERY_LABELS, f"MASTERY_LABELS missing level {level}"
        assert isinstance(MASTERY_LABELS[level], str)


def test_mastery_colors_cover_0_to_4() -> None:
    """MASTERY_COLORS must have entries for levels 0 through 4."""
    for level in range(5):
        assert level in MASTERY_COLORS, f"MASTERY_COLORS missing level {level}"
        assert MASTERY_COLORS[level].startswith("#")


def test_default_bkt_params_all_difficulties() -> None:
    """DEFAULT_BKT_PARAMS must cover easy, medium, hard."""
    for difficulty in ["easy", "medium", "hard"]:
        assert difficulty in DEFAULT_BKT_PARAMS, f"Missing BKT params for {difficulty}"
        params = DEFAULT_BKT_PARAMS[difficulty]
        for key in ["P_L0", "P_T", "P_G", "P_S"]:
            assert key in params, f"Missing {key} in {difficulty} BKT params"
            assert 0.0 <= params[key] <= 1.0
