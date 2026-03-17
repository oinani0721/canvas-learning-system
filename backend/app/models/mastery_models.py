"""
Mastery Models - Calibration, Fusion, and EventBus Models

Story 5.5: Calibration tracking (Area9 2x2 matrix)
Story 5.6: Multi-signal fusion (5 core signals -> single mastery)
Story 5.7: EventBus event models (LearningEvent, EventTier)

[Source: _bmad-output/planning-artifacts/architecture.md#能力域5]
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Protocol, runtime_checkable

from pydantic import BaseModel, Field

# ═══════════════════════════════════════════════════════════════════════════════
# Story 5.5: Calibration Models (Area9 2x2 Matrix)
# ═══════════════════════════════════════════════════════════════════════════════


class CalibrationQuadrant(str, Enum):
    """Area9 2x2 confidence matrix quadrants.

    Reference: Area9 Rhapsode adaptive learning platform.

                     Actual High         Actual Low
    Confidence High  MASTERED            MISCONCEPTION (dangerous!)
    Confidence Low   LUCKY               UNLEARNED
    """

    MASTERED = "mastered"  # High confidence + High performance
    MISCONCEPTION = "misconception"  # High confidence + Low performance (DANGEROUS)
    LUCKY = "lucky"  # Low confidence + High performance
    UNLEARNED = "unlearned"  # Low confidence + Low performance


class CalibrationRating(str, Enum):
    """Overall calibration quality rating.

    Based on signed_bias with |threshold| = 0.15.
    """

    WELL_CALIBRATED = "well_calibrated"  # |signed_bias| < 0.15
    OVER_CONFIDENT = "over_confident"  # signed_bias > 0.15
    UNDER_CONFIDENT = "under_confident"  # signed_bias < -0.15
    INSUFFICIENT_DATA = "insufficient_data"  # < 10 records


class CalibrationRecord(BaseModel):
    """Single calibration data point: (self_confidence, actual_performance).

    Recorded after each exam interaction where user self-assesses confidence.
    """

    node_id: str = Field(..., description="Concept node ID")
    session_id: str = Field(default="", description="Exam session ID")
    self_confidence: float = Field(..., ge=0.0, le=1.0, description="User's self-assessed confidence (0.0-1.0)")
    actual_performance: float = Field(..., ge=0.0, le=1.0, description="AutoSCORE 4-dim average normalized (0.0-1.0)")
    quadrant: CalibrationQuadrant = Field(
        default=CalibrationQuadrant.UNLEARNED, description="Area9 quadrant classification"
    )
    is_dangerous: bool = Field(
        default=False, description="True if MISCONCEPTION quadrant (high confidence + low performance)"
    )
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Record creation time")


class CalibrationRequest(BaseModel):
    """API request to record a calibration data point."""

    self_confidence: float = Field(..., ge=0.0, le=1.0, description="User's self-assessed confidence (0.0-1.0)")
    actual_performance: float = Field(..., ge=0.0, le=1.0, description="AutoSCORE 4-dim average normalized (0.0-1.0)")
    session_id: str = Field(default="", description="Exam session ID")


class CalibrationSummary(BaseModel):
    """Calibration assessment summary for a concept node.

    Three-stage progressive assessment:
      Stage 1 (< 10 records): Data collection only
      Stage 2 (10-20 records): Preliminary trends
      Stage 3 (20+ records): Reliable assessment
    """

    stage: int = Field(..., ge=1, le=3, description="Assessment stage (1-3)")
    record_count: int = Field(..., ge=0, description="Total calibration records")
    quadrant_distribution: Dict[str, float] = Field(
        default_factory=dict,
        description="Percentage distribution across 4 quadrants",
    )
    signed_bias: Optional[float] = Field(
        default=None,
        description="mean(confidence - performance), positive=overconfident",
    )
    absolute_bias: Optional[float] = Field(
        default=None,
        description="mean(|confidence - performance|), calibration precision",
    )
    calibration_rating: CalibrationRating = Field(
        default=CalibrationRating.INSUFFICIENT_DATA,
        description="Overall calibration quality",
    )
    stage_label: str = Field(
        default="数据收集中",
        description="Human-readable stage description",
    )


class DangerousNodeInfo(BaseModel):
    """Info about a node in the MISCONCEPTION quadrant."""

    node_id: str
    misconception_count: int = Field(default=0, description="Number of MISCONCEPTION records")
    total_records: int = Field(default=0, description="Total calibration records")
    misconception_ratio: float = Field(default=0.0, description="Ratio of misconception records")


# ═══════════════════════════════════════════════════════════════════════════════
# Story 5.6: Multi-Signal Fusion Models
# ═══════════════════════════════════════════════════════════════════════════════


@runtime_checkable
class MasterySignal(Protocol):
    """Protocol for pluggable mastery signal sources.

    Any class implementing this protocol can be registered with SignalRegistry
    to contribute to the fused mastery score.

    Architecture: N-signal dynamic registration for Phase 2+ Beta-Bayesian upgrade.
    """

    @property
    def signal_name(self) -> str:
        """Unique signal identifier (e.g., 'bkt', 'fsrs', 'exam_score')."""
        ...

    def get_value(self, node_id: str) -> Optional[float]:
        """Return 0.0-1.0 normalized signal value, or None if no data."""
        ...

    def get_weight(self, node_id: str) -> float:
        """Return base weight for this signal at the given node."""
        ...

    def get_reliability(self, node_id: str) -> float:
        """Return signal reliability 0.0-1.0 (more data = more reliable)."""
        ...


class SignalDetail(BaseModel):
    """Detail of a single signal's contribution to the fused mastery."""

    signal_name: str
    value: Optional[float] = None
    weight: float = 0.0
    normalized_weight: float = 0.0
    reliability: float = 0.0


class FusionResult(BaseModel):
    """Result of multi-signal mastery fusion.

    fused_mastery replaces the old min(p_mastery, R) from Story 5.1.
    """

    fused_mastery: float = Field(..., ge=0.0, le=1.0, description="Fused single-dimension mastery score")
    signal_details: List[SignalDetail] = Field(default_factory=list, description="Per-signal contribution details")
    active_signal_count: int = Field(default=0, description="Number of signals with data")
    is_fallback: bool = Field(default=False, description="True if using min(p_mastery, R) fallback")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Phase 3+ multi-dimensional mastery (schema reserved, not computed)
    conceptual_mastery: Optional[float] = Field(
        default=None, description="Reserved: conceptual understanding dimension"
    )
    procedural_mastery: Optional[float] = Field(default=None, description="Reserved: procedural skill dimension")
    metacognitive_mastery: Optional[float] = Field(
        default=None, description="Reserved: metacognitive awareness dimension"
    )


class SignalCorrelationResult(BaseModel):
    """Result of Pearson correlation between two signals."""

    signal_a: str
    signal_b: str
    pearson_r: float
    sample_count: int
    is_redundant: bool = Field(default=False, description="True if |r| >= 0.7 (high correlation warning)")
