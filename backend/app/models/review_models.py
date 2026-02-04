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
        json_schema_extra={"example": "离散数学-检验白板-20250115.canvas"}
    )
    date: datetime = Field(
        ...,
        description="Review session timestamp",
        json_schema_extra={"example": "2025-01-15T10:00:00Z"}
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
        json_schema_extra={"example": 0.75}
    )
    total_concepts: int = Field(
        ...,
        ge=0,
        description="Total concepts reviewed",
        json_schema_extra={"example": 8}
    )
    passed_concepts: int = Field(
        ...,
        ge=0,
        description="Concepts with passing score (>=60)",
        json_schema_extra={"example": 6}
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
        json_schema_extra={"example": "2025-01-15"}
    )
    pass_rate: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Pass rate at this date",
        json_schema_extra={"example": 0.75}
    )


class WeakConceptImprovement(BaseModel):
    """
    Improvement tracking for a weak concept.

    [Source: specs/api/review-api.openapi.yml#L771-780]
    """
    concept_name: str = Field(
        ...,
        description="Name of the concept",
        json_schema_extra={"example": "逆否命题"}
    )
    improvement_rate: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Improvement rate (0-1 scale)",
        json_schema_extra={"example": 0.4}
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
        json_schema_extra={"example": 0.25}
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
        json_schema_extra={"example": "离散数学.canvas"}
    )
    review_count: int = Field(
        ...,
        ge=0,
        description="Total number of review sessions",
        json_schema_extra={"example": 3}
    )
    reviews: List[ReviewEntry] = Field(
        ...,
        description="List of all review sessions (newest first)"
    )
    trends: Optional[TrendAnalysis] = Field(
        None,
        description="Trend analysis data (null if <2 reviews)"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Story 31.4: Verification Question History Models
# ═══════════════════════════════════════════════════════════════════════════════

class QuestionType(str, Enum):
    """
    Verification question angle type.

    Story 31.4 AC-31.4.2: Different question angles for diverse coverage.

    [Source: specs/data/verification-history-response.schema.json#L61-64]
    [Source: docs/stories/31.4.story.md#Task-3]
    """
    standard = "standard"
    application = "application"
    comparison = "comparison"
    counterexample = "counterexample"
    synthesis = "synthesis"


class VerificationHistoryItem(BaseModel):
    """
    Single verification question history record.

    Story 31.4 AC-31.4.4: History data includes question, answer, score, timestamp.

    [Source: specs/data/verification-history-response.schema.json#L48-86]
    [Source: specs/api/review-api.openapi.yml#/verification/history/{concept}]
    """
    question_id: str = Field(
        ...,
        description="Unique question identifier",
        json_schema_extra={"example": "vq_abc123"}
    )
    question_text: str = Field(
        ...,
        description="The verification question content",
        json_schema_extra={"example": "请解释什么是「逆否命题」？"}
    )
    question_type: QuestionType = Field(
        default=QuestionType.standard,
        description="Question angle type (standard, application, comparison, etc.)"
    )
    user_answer: Optional[str] = Field(
        None,
        description="User's answer to the question (if answered)"
    )
    score: Optional[int] = Field(
        None,
        ge=0,
        le=100,
        description="Score for the answer (0-100, if evaluated)",
        json_schema_extra={"example": 75}
    )
    canvas_name: str = Field(
        ...,
        description="Source canvas name",
        json_schema_extra={"example": "离散数学"}
    )
    asked_at: datetime = Field(
        ...,
        description="Timestamp when the question was asked",
        json_schema_extra={"example": "2025-01-15T10:30:00Z"}
    )


class PaginationInfo(BaseModel):
    """
    Pagination metadata for list responses.

    [Source: specs/data/verification-history-response.schema.json#L26-44]
    """
    limit: int = Field(
        ...,
        ge=1,
        le=100,
        description="Number of items per page",
        json_schema_extra={"example": 20}
    )
    offset: int = Field(
        ...,
        ge=0,
        description="Offset from the start",
        json_schema_extra={"example": 0}
    )
    has_more: bool = Field(
        ...,
        description="Whether there are more items available",
        json_schema_extra={"example": False}
    )


class VerificationHistoryResponse(BaseModel):
    """
    Verification question history response.

    Story 31.4 AC-31.4.3: New GET /verification/history/{concept} endpoint.
    Story 31.4 AC-31.4.4: Returns question, answer, score, timestamp for each record.

    [Source: specs/data/verification-history-response.schema.json]
    [Source: specs/api/review-api.openapi.yml#/verification/history/{concept}]
    [Source: docs/stories/31.4.story.md#Task-4]
    """
    concept: str = Field(
        ...,
        description="The concept being queried",
        json_schema_extra={"example": "逆否命题"}
    )
    total_count: int = Field(
        ...,
        ge=0,
        description="Total number of history records",
        json_schema_extra={"example": 5}
    )
    items: List[VerificationHistoryItem] = Field(
        ...,
        description="List of verification history records"
    )
    pagination: Optional[PaginationInfo] = Field(
        None,
        description="Pagination metadata (included when paginated)"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Story 34.4: Review History Models with Pagination
# [Source: specs/api/review-api.openapi.yml#L663-729]
# ═══════════════════════════════════════════════════════════════════════════════

class HistoryPeriod(BaseModel):
    """
    Time period for history query.

    [Source: specs/api/review-api.openapi.yml#L668-677]
    """
    start: str = Field(
        ...,
        description="Start date (ISO format)",
        json_schema_extra={"example": "2025-01-11"}
    )
    end: str = Field(
        ...,
        description="End date (ISO format)",
        json_schema_extra={"example": "2025-01-18"}
    )


class HistoryReviewRecord(BaseModel):
    """
    Single review record within a day.

    [Source: specs/api/review-api.openapi.yml#L693-706]
    """
    concept_id: str = Field(..., description="Concept identifier")
    concept_name: str = Field(..., description="Concept name")
    canvas_path: str = Field(..., description="Canvas file path")
    rating: int = Field(..., ge=1, le=4, description="FSRS rating (1-4)")
    review_time: datetime = Field(..., description="Review timestamp")


class HistoryDayRecord(BaseModel):
    """
    Daily review history record.

    [Source: specs/api/review-api.openapi.yml#L682-706]
    """
    date: str = Field(..., description="Date (YYYY-MM-DD)", json_schema_extra={"example": "2025-01-18"})
    reviews: List[HistoryReviewRecord] = Field(
        default_factory=list,
        description="Reviews completed on this date"
    )


class HistoryStatistics(BaseModel):
    """
    Review history statistics.

    [Source: specs/api/review-api.openapi.yml#L707-728]
    """
    average_rating: Optional[float] = Field(
        None,
        description="Average FSRS rating",
        json_schema_extra={"example": 3.2}
    )
    retention_rate: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Memory retention rate",
        json_schema_extra={"example": 0.85}
    )
    streak_days: int = Field(
        default=0,
        ge=0,
        description="Consecutive review days",
        json_schema_extra={"example": 7}
    )
    by_canvas: Optional[dict] = Field(
        None,
        description="Review count by canvas",
        json_schema_extra={"example": {"离散数学.canvas": 15, "线性代数.canvas": 10}}
    )


class HistoryResponse(BaseModel):
    """
    Review history response with pagination support.

    Story 34.4: Default limit=5, show_all=False for pagination.

    [Source: specs/api/review-api.openapi.yml#L663-729]
    [Source: docs/stories/34.4.story.md]
    """
    period: HistoryPeriod = Field(..., description="Query time period")
    total_reviews: int = Field(
        ...,
        ge=0,
        description="Total review count",
        json_schema_extra={"example": 45}
    )
    records: List[HistoryDayRecord] = Field(
        default_factory=list,
        description="Daily review records (newest first)"
    )
    statistics: Optional[HistoryStatistics] = Field(
        None,
        description="Aggregate statistics"
    )
    pagination: Optional[PaginationInfo] = Field(
        None,
        description="Pagination info (Story 34.4)"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Story 31.6: Session Progress Models
# [Source: docs/stories/31.6.story.md]
# ═══════════════════════════════════════════════════════════════════════════════

class VerificationStatusEnum(str, Enum):
    """
    Verification session status.

    Story 31.6 AC-31.6.4: Support pause/resume session.

    [Source: backend/app/services/verification_service.py:VerificationStatus]
    """
    pending = "pending"
    in_progress = "in_progress"
    paused = "paused"
    completed = "completed"
    cancelled = "cancelled"


class SessionProgressResponse(BaseModel):
    """
    Real-time verification session progress response.

    Story 31.6 AC-31.6.1: Frontend displays "已验证 X/Y 个概念" progress.
    Story 31.6 AC-31.6.2: Color distribution real-time updates.
    Story 31.6 AC-31.6.3: Mastery percentage = green / total * 100%.

    [Source: docs/stories/31.6.story.md#Task-2]
    [Source: backend/app/services/verification_service.py:VerificationProgress]
    """
    session_id: str = Field(
        ...,
        description="Unique session identifier",
        json_schema_extra={"example": "sess_abc123"}
    )
    canvas_name: str = Field(
        ...,
        description="Source canvas name",
        json_schema_extra={"example": "离散数学"}
    )
    total_concepts: int = Field(
        ...,
        ge=0,
        description="Total concepts to verify",
        json_schema_extra={"example": 10}
    )
    completed_concepts: int = Field(
        ...,
        ge=0,
        description="Concepts completed so far",
        json_schema_extra={"example": 5}
    )
    current_concept: str = Field(
        ...,
        description="Current concept being verified",
        json_schema_extra={"example": "逆否命题"}
    )
    current_concept_idx: int = Field(
        ...,
        ge=0,
        description="Index of current concept (0-based)",
        json_schema_extra={"example": 5}
    )
    green_count: int = Field(
        default=0,
        ge=0,
        description="Concepts marked as mastered (green)"
    )
    yellow_count: int = Field(
        default=0,
        ge=0,
        description="Concepts partially understood (yellow)"
    )
    purple_count: int = Field(
        default=0,
        ge=0,
        description="Concepts need decomposition (purple)"
    )
    red_count: int = Field(
        default=0,
        ge=0,
        description="Concepts not understood (red)"
    )
    status: VerificationStatusEnum = Field(
        default=VerificationStatusEnum.pending,
        description="Current session status"
    )
    progress_percentage: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Completion percentage (completed/total * 100)",
        json_schema_extra={"example": 50.0}
    )
    mastery_percentage: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Mastery rate (green/completed * 100)",
        json_schema_extra={"example": 60.0}
    )
    hints_given: int = Field(
        default=0,
        ge=0,
        description="Hints given for current concept"
    )
    max_hints: int = Field(
        default=3,
        ge=0,
        description="Maximum hints allowed per concept"
    )
    started_at: datetime = Field(
        ...,
        description="Session start timestamp"
    )
    updated_at: datetime = Field(
        ...,
        description="Last update timestamp"
    )


class SessionPauseResumeResponse(BaseModel):
    """
    Response for session pause/resume operations.

    Story 31.6 AC-31.6.4: Support pause/resume session.

    [Source: docs/stories/31.6.story.md#Task-3]
    """
    session_id: str = Field(
        ...,
        description="Session identifier",
        json_schema_extra={"example": "sess_abc123"}
    )
    status: VerificationStatusEnum = Field(
        ...,
        description="New session status after operation"
    )
    message: str = Field(
        ...,
        description="Operation result message",
        json_schema_extra={"example": "Session paused successfully"}
    )
