"""
Calibration Tracker - Area9 2x2 Confidence Matrix + Three-Stage Progressive Assessment

Story 5.5: Tracks metacognitive calibration — identifies "thinks they know but don't"
dangerous misconception blind spots.

Architecture Reference:
  - Area9 Rhapsode adaptive learning platform (metacognitive calibration tracking)
  - Three-stage progressive assessment (statistical reliability thresholds)

[Source: _bmad-output/implementation-artifacts/5-5-calibration-tracking.md]
[Source: _bmad-output/planning-artifacts/architecture.md#能力域5]
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List

from app.models.mastery_models import (
    CalibrationQuadrant,
    CalibrationRating,
    CalibrationRecord,
    CalibrationSummary,
)

logger = logging.getLogger(__name__)

# Quadrant classification thresholds (configurable via mastery_config.json
# "calibration_thresholds" section; these are the defaults)
CONFIDENCE_THRESHOLD = 0.6
PERFORMANCE_THRESHOLD = 0.6

# Three-stage data thresholds
STAGE_2_MIN_RECORDS = 10
STAGE_3_MIN_RECORDS = 20

# Calibration rating threshold
CALIBRATION_BIAS_THRESHOLD = 0.15


def _load_calibration_thresholds() -> None:
    """Load calibration thresholds from mastery_config.json if present.

    Updates module-level constants from the "calibration_thresholds" section.
    Falls back to hardcoded defaults when no config file is found.
    """
    global CONFIDENCE_THRESHOLD, PERFORMANCE_THRESHOLD
    global STAGE_2_MIN_RECORDS, STAGE_3_MIN_RECORDS, CALIBRATION_BIAS_THRESHOLD

    import json
    from pathlib import Path

    candidates = [
        Path(__file__).parent.parent.parent.parent / "mastery_config.json",
        Path(__file__).parent.parent.parent / "mastery_config.json",
    ]
    for config_path in candidates:
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                cal = data.get("calibration_thresholds", {})
                if cal:
                    CONFIDENCE_THRESHOLD = cal.get("confidence", CONFIDENCE_THRESHOLD)
                    PERFORMANCE_THRESHOLD = cal.get("performance", PERFORMANCE_THRESHOLD)
                    STAGE_2_MIN_RECORDS = cal.get("stage_2_min_records", STAGE_2_MIN_RECORDS)
                    STAGE_3_MIN_RECORDS = cal.get("stage_3_min_records", STAGE_3_MIN_RECORDS)
                    CALIBRATION_BIAS_THRESHOLD = cal.get("bias_threshold", CALIBRATION_BIAS_THRESHOLD)
                    logger.info(
                        "Loaded calibration thresholds from %s: confidence=%.2f performance=%.2f",
                        config_path,
                        CONFIDENCE_THRESHOLD,
                        PERFORMANCE_THRESHOLD,
                    )
                break
            except (json.JSONDecodeError, OSError) as e:
                logger.warning("Failed to load calibration config from %s: %s", config_path, e)


_load_calibration_thresholds()


def classify_quadrant(self_confidence: float, actual_performance: float) -> CalibrationQuadrant:
    """Classify a (confidence, performance) pair into Area9 quadrant.

    Area9 2x2 Matrix:
                         Actual >= 0.6       Actual < 0.6
    Confidence >= 0.6    MASTERED            MISCONCEPTION (dangerous!)
    Confidence < 0.6     LUCKY               UNLEARNED

    Args:
        self_confidence: User's self-assessed confidence (0.0-1.0)
        actual_performance: AutoSCORE normalized score (0.0-1.0)

    Returns:
        CalibrationQuadrant enum value
    """
    high_confidence = self_confidence >= CONFIDENCE_THRESHOLD
    high_performance = actual_performance >= PERFORMANCE_THRESHOLD

    if high_confidence and high_performance:
        return CalibrationQuadrant.MASTERED
    elif high_confidence and not high_performance:
        return CalibrationQuadrant.MISCONCEPTION
    elif not high_confidence and high_performance:
        return CalibrationQuadrant.LUCKY
    else:
        return CalibrationQuadrant.UNLEARNED


def compute_signed_bias(records: List[CalibrationRecord]) -> float:
    """Compute signed bias: mean(confidence - performance).

    Positive value = systematic overconfidence (user overestimates themselves)
    Negative value = systematic underconfidence (user underestimates themselves)

    Formula: signed_bias = (1/N) * Σ(c_i - p_i)

    Args:
        records: List of calibration records (must be non-empty)

    Returns:
        Signed bias value, rounded to 3 decimal places
    """
    if not records:
        return 0.0
    total = sum(r.self_confidence - r.actual_performance for r in records)
    return round(total / len(records), 3)


def compute_absolute_bias(records: List[CalibrationRecord]) -> float:
    """Compute absolute bias: mean(|confidence - performance|).

    Measures calibration precision — lower is better.

    Formula: absolute_bias = (1/N) * Σ|c_i - p_i|

    Args:
        records: List of calibration records (must be non-empty)

    Returns:
        Absolute bias value, rounded to 3 decimal places
    """
    if not records:
        return 0.0
    total = sum(abs(r.self_confidence - r.actual_performance) for r in records)
    return round(total / len(records), 3)


def compute_calibration_rating(signed_bias: float, record_count: int) -> CalibrationRating:
    """Determine calibration quality rating.

    Three-stage progressive logic:
      Stage 1 (< 10 records): INSUFFICIENT_DATA
      Stage 2 (10-20 records): Preliminary — same thresholds, still computed
      Stage 3 (20+ records): Reliable assessment

    Thresholds:
      |signed_bias| < 0.15  → WELL_CALIBRATED
      signed_bias > 0.15    → OVER_CONFIDENT
      signed_bias < -0.15   → UNDER_CONFIDENT

    Args:
        signed_bias: Computed signed bias value
        record_count: Number of calibration records

    Returns:
        CalibrationRating enum value
    """
    if record_count < STAGE_2_MIN_RECORDS:
        return CalibrationRating.INSUFFICIENT_DATA

    if abs(signed_bias) < CALIBRATION_BIAS_THRESHOLD:
        return CalibrationRating.WELL_CALIBRATED
    elif signed_bias > 0:
        return CalibrationRating.OVER_CONFIDENT
    else:
        return CalibrationRating.UNDER_CONFIDENT


def compute_quadrant_distribution(records: List[CalibrationRecord]) -> Dict[str, float]:
    """Compute percentage distribution across 4 quadrants.

    Args:
        records: List of calibration records

    Returns:
        Dict mapping quadrant name to percentage (0.0-1.0)
    """
    if not records:
        return {q.value: 0.0 for q in CalibrationQuadrant}

    counts: Dict[str, int] = {q.value: 0 for q in CalibrationQuadrant}
    for r in records:
        counts[r.quadrant.value] = counts.get(r.quadrant.value, 0) + 1

    total = len(records)
    return {k: round(v / total, 3) for k, v in counts.items()}


def record_calibration(
    node_id: str,
    self_confidence: float,
    actual_performance: float,
    session_id: str = "",
) -> CalibrationRecord:
    """Create a CalibrationRecord with auto-classified quadrant.

    Args:
        node_id: Concept node ID
        self_confidence: User confidence (0.0-1.0)
        actual_performance: AutoSCORE score normalized (0.0-1.0)
        session_id: Optional exam session ID

    Returns:
        Fully populated CalibrationRecord
    """
    quadrant = classify_quadrant(self_confidence, actual_performance)
    is_dangerous = quadrant == CalibrationQuadrant.MISCONCEPTION

    record = CalibrationRecord(
        node_id=node_id,
        session_id=session_id,
        self_confidence=self_confidence,
        actual_performance=actual_performance,
        quadrant=quadrant,
        is_dangerous=is_dangerous,
        timestamp=datetime.now(timezone.utc),
    )

    if is_dangerous:
        logger.warning(
            f"MISCONCEPTION detected: node={node_id} confidence={self_confidence:.2f} "
            f"performance={actual_performance:.2f} — user thinks they know but doesn't"
        )

    return record


def get_calibration_summary(records: List[CalibrationRecord]) -> CalibrationSummary:
    """Compute calibration summary with three-stage progressive assessment.

    Stage 1 (< 10): Data collection only, no assessment
    Stage 2 (10-20): Preliminary trends (signed_bias + quadrant distribution)
    Stage 3 (20+): Reliable assessment (full report + absolute_bias + rating)

    Args:
        records: All calibration records for a node

    Returns:
        CalibrationSummary with stage-appropriate data
    """
    count = len(records)

    if count < STAGE_2_MIN_RECORDS:
        # Stage 1: Data collection only
        return CalibrationSummary(
            stage=1,
            record_count=count,
            quadrant_distribution=compute_quadrant_distribution(records),
            signed_bias=None,
            absolute_bias=None,
            calibration_rating=CalibrationRating.INSUFFICIENT_DATA,
            stage_label=f"数据收集中（{count}/{STAGE_2_MIN_RECORDS}）",
        )

    signed_bias = compute_signed_bias(records)
    quadrant_dist = compute_quadrant_distribution(records)

    if count < STAGE_3_MIN_RECORDS:
        # Stage 2: Preliminary trends
        rating = compute_calibration_rating(signed_bias, count)
        return CalibrationSummary(
            stage=2,
            record_count=count,
            quadrant_distribution=quadrant_dist,
            signed_bias=signed_bias,
            absolute_bias=None,
            calibration_rating=rating,
            stage_label="初步趋势，仅供参考",
        )

    # Stage 3: Reliable assessment
    absolute_bias = compute_absolute_bias(records)
    rating = compute_calibration_rating(signed_bias, count)

    return CalibrationSummary(
        stage=3,
        record_count=count,
        quadrant_distribution=quadrant_dist,
        signed_bias=signed_bias,
        absolute_bias=absolute_bias,
        calibration_rating=rating,
        stage_label="可靠评估",
    )
