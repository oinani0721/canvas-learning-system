# Canvas Learning System - Review Models
# Story 24.4: Multi-Review Trend Analysis and History Visualization
"""
Pydantic Models for Multi-Review Progress Tracking.

All models are derived from the OpenAPI specification:
[Source: specs/api/review-api.openapi.yml#L725-805]
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

# ═══════════════════════════════════════════════════════════════════════════════
# Enums
# ═══════════════════════════════════════════════════════════════════════════════

class ReviewMode(str, Enum):
    """
    Review mode enum.

    [Source: specs/api/review-api.openapi.yml#L346-378]
    """
    fresh = "fresh"
    targeted = "targeted"


class TrendDirection(str, Enum):
    """
    Overall progress trend direction.

    [Source: specs/api/review-api.openapi.yml#L785-789]
    """
    up = "up"
    stable = "stable"
    down = "down"


class ConceptStatus(str, Enum):
    """
    Concept mastery status.

    [Source: specs/api/review-api.openapi.yml#L771-775]
    """
    weak = "weak"
    improving = "improving"
    mastered = "mastered"


# ═══════════════════════════════════════════════════════════════════════════════
# Individual Review Entry
# ═══════════════════════════════════════════════════════════════════════════════

class ReviewEntry(BaseModel):
    """
    Single review session entry.

    [Source: specs/api/review-api.openapi.yml#L737-762]
    """
    review_canvas_path: str = Field(
        ...,
        description="Path to verification canvas file",
        example="离散数学-检验白板-20250115.canvas"
    )
    date: datetime = Field(
        ...,
        description="Review session timestamp",
        example="2025-01-15T10:00:00Z"
    )
    mode: ReviewMode = Field(
        ...,
        description="Review mode (fresh or targeted)"
    )
    pass_rate: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Pass rate for this session (0-1 scale)",
        example=0.75
    )
    total_concepts: int = Field(
        ...,
        ge=0,
        description="Total concepts reviewed",
        example=8
    )
    passed_concepts: int = Field(
        ...,
        ge=0,
        description="Concepts with passing score (>=60)",
        example=6
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Trend Analysis Data
# ═══════════════════════════════════════════════════════════════════════════════

class PassRateTrend(BaseModel):
    """
    Single data point in pass rate trend chart.

    [Source: specs/api/review-api.openapi.yml#L765-769]
    """
    date: str = Field(
        ...,
        description="ISO date string (YYYY-MM-DD)",
        example="2025-01-15"
    )
    pass_rate: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Pass rate at this date",
        example=0.75
    )


class WeakConceptImprovement(BaseModel):
    """
    Improvement tracking for a weak concept.

    [Source: specs/api/review-api.openapi.yml#L771-780]
    """
    concept_name: str = Field(
        ...,
        description="Name of the concept",
        example="逆否命题"
    )
    improvement_rate: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Improvement rate (0-1 scale)",
        example=0.4
    )
    current_status: ConceptStatus = Field(
        ...,
        description="Current mastery status"
    )


class OverallProgress(BaseModel):
    """
    Overall learning progress metrics.

    [Source: specs/api/review-api.openapi.yml#L782-791]
    """
    progress_rate: float = Field(
        ...,
        description="Overall progress rate (-1 to 1 scale)",
        example=0.25
    )
    trend_direction: TrendDirection = Field(
        ...,
        description="Trend direction (up/stable/down)"
    )


class TrendAnalysis(BaseModel):
    """
    Trend analysis container.

    [Source: specs/api/review-api.openapi.yml#L763-805]
    """
    pass_rate_trend: List[PassRateTrend] = Field(
        ...,
        description="Time-series data for pass rate visualization"
    )
    weak_concepts_improvement: List[WeakConceptImprovement] = Field(
        default_factory=list,
        description="Weak concept improvement tracking"
    )
    overall_progress: OverallProgress = Field(
        ...,
        description="Overall progress metrics"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Multi-Review Progress Response
# ═══════════════════════════════════════════════════════════════════════════════

class MultiReviewProgressResponse(BaseModel):
    """
    Multi-review progress response with trend analysis.

    [Source: specs/api/review-api.openapi.yml#L725-805]
    """
    original_canvas_path: str = Field(
        ...,
        description="Path to original canvas file",
        example="离散数学.canvas"
    )
    review_count: int = Field(
        ...,
        ge=0,
        description="Total number of review sessions",
        example=3
    )
    reviews: List[ReviewEntry] = Field(
        ...,
        description="List of all review sessions (newest first)"
    )
    trends: Optional[TrendAnalysis] = Field(
        None,
        description="Trend analysis data (null if <2 reviews)"
    )
