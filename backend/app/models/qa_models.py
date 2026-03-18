# Canvas Learning System - QA Quality Models
# Story 7.4: 出题难度匹配与提取质量验证
# [Source: _bmad-output/implementation-artifacts/7-4-difficulty-matching-extraction-validation.md]
"""
Pydantic models for QA quality metrics, extraction validation,
difficulty matching, pipeline health, and error aggregation.

[Source: Story 7.4 Task 5.6 — All API request/response models]
[Source: architecture.md#FR能力域→文件映射 — 9.质量保证]
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional  # noqa: UP035

from pydantic import BaseModel, Field

# ═══════════════════════════════════════════════════════════════════════════════
# Difficulty Matching Models (AC #1, #2)
# ═══════════════════════════════════════════════════════════════════════════════


class DifficultyMatchRecord(BaseModel):
    """Single difficulty match evaluation record.

    [Source: Story 7.4 AC-1 — structured log fields]
    """

    node_id: str = Field(..., description="Canvas node identifier")
    proficiency: float = Field(..., ge=0.0, le=1.0, description="User effective_proficiency at evaluation time")
    estimated_difficulty: float = Field(..., ge=0.0, le=1.0, description="LLM-estimated question difficulty")
    is_matched: bool = Field(..., description="Whether difficulty fell within acceptable range")
    lower_bound: float = Field(..., ge=0.0, le=1.0, description="Lower bound of acceptable range")
    upper_bound: float = Field(..., ge=0.0, le=1.0, description="Upper bound of acceptable range")
    question_preview: str = Field("", description="First 100 chars of the question text")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 timestamp",
    )


class DifficultyMatchStats(BaseModel):
    """Sliding window statistics for difficulty matching.

    [Source: Story 7.4 AC-2 — sliding window of 50 questions]
    """

    window_size: int = Field(50, description="Sliding window size")
    total_in_window: int = Field(0, description="Number of records in current window")
    matched_count: int = Field(0, description="Number of matched records in window")
    match_rate: float = Field(0.0, ge=0.0, le=1.0, description="matched / total ratio")
    is_healthy: bool = Field(True, description="True if match_rate >= 0.7")
    recent_records: List[DifficultyMatchRecord] = Field(
        default_factory=list, description="Recent match records (last 10)"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Extraction Validation Models (AC #3, #4)
# ═══════════════════════════════════════════════════════════════════════════════


class ExtractionRecord(BaseModel):
    """Single extraction record for human review.

    [Source: Story 7.4 AC-3 — extraction record data model]
    """

    id: str = Field(..., description="Record UUID")
    source_session_id: str = Field(..., description="Source conversation session ID")
    source_node_id: str = Field(..., description="Source canvas node ID")
    original_text: str = Field(..., description="Original conversation fragment used for extraction")
    extracted_content: str = Field(..., description="Extracted structured content")
    extraction_type: str = Field(..., description="Extraction type: 'error' | 'tip' | 'key_qa'")
    extraction_subtype: Optional[str] = Field(
        None,
        description="Error subtype: 'breakthrough' | 'reasoning' | 'knowledge_gap' | 'pseudo_understanding'",
    )
    created_at: str = Field(..., description="ISO 8601 creation timestamp")
    annotation: Optional[str] = Field(None, description="Annotation: 'correct' | 'incorrect' | 'partial' | None")
    annotated_at: Optional[str] = Field(None, description="ISO 8601 annotation timestamp")


class AnnotationRequest(BaseModel):
    """Request body for submitting an annotation.

    [Source: Story 7.4 AC-3 — annotation submission]
    """

    annotation: str = Field(..., description="Annotation value: 'correct' | 'incorrect' | 'partial'")


class UpdateExtractionRequest(BaseModel):
    """Request body for updating extraction content.

    [Source: Story 5.8 Task 2.5]
    """

    extracted_content: str = Field(..., min_length=1, description="Updated extracted content")


class TypeStats(BaseModel):
    """Per-type extraction accuracy statistics."""

    total: int = Field(0, description="Total annotated records of this type")
    correct: int = Field(0, description="Correctly extracted count")
    accuracy: float = Field(0.0, description="Accuracy ratio")


class ExtractionStats(BaseModel):
    """Aggregated extraction quality statistics.

    [Source: Story 7.4 AC-4 — extraction quality statistics]
    """

    total_records: int = Field(0, description="Total extraction records")
    annotated_count: int = Field(0, description="Number of annotated records")
    accuracy: float = Field(0.0, description="Overall accuracy (correct / annotated)")
    by_type: Dict[str, TypeStats] = Field(default_factory=dict, description="Per-type accuracy breakdown")


class ExtractionRecordPage(BaseModel):
    """Paginated extraction records response."""

    records: List[ExtractionRecord] = Field(default_factory=list)
    total: int = Field(0, description="Total matching records")
    page: int = Field(1, description="Current page number")
    page_size: int = Field(20, description="Records per page")


# ═══════════════════════════════════════════════════════════════════════════════
# Pipeline Health Models (AC #5)
# ═══════════════════════════════════════════════════════════════════════════════


class HealthMetric(BaseModel):
    """Single pipeline health metric.

    [Source: Story 7.4 AC-5 — 7 health indicators]
    """

    name: str = Field(..., description="Metric identifier")
    status: str = Field("healthy", description="Status: 'healthy' | 'warning' | 'critical'")
    value: str = Field("", description="Current metric value (stringified)")
    threshold: str = Field("", description="Health threshold description")
    message: Optional[str] = Field(None, description="Warning/error message when unhealthy")


class ErrorCategoryCounts(BaseModel):
    """Error counts for a single time window."""

    llm_errors: int = Field(0)
    network_errors: int = Field(0)
    algorithm_errors: int = Field(0)
    data_errors: int = Field(0)
    uncategorized: int = Field(0)


class ErrorAggregation(BaseModel):
    """Error classification aggregation across time windows.

    [Source: Story 7.4 AC-6 — 4 error categories, 3 time windows]
    """

    last_24h: ErrorCategoryCounts = Field(default_factory=ErrorCategoryCounts)
    last_7d: ErrorCategoryCounts = Field(default_factory=ErrorCategoryCounts)
    last_30d: ErrorCategoryCounts = Field(default_factory=ErrorCategoryCounts)


class PipelineHealthStatus(BaseModel):
    """Full pipeline health status response.

    [Source: Story 7.4 AC-5 — GET /api/v1/system/pipeline-health]
    """

    overall: str = Field("healthy", description="Overall: 'healthy' | 'degraded' | 'critical'")
    metrics: List[HealthMetric] = Field(default_factory=list, description="Individual metrics")
    last_updated: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 timestamp",
    )
    error_summary: ErrorAggregation = Field(
        default_factory=ErrorAggregation, description="Error classification summary"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# QA Metrics Response (AC #2, #4)
# ═══════════════════════════════════════════════════════════════════════════════


class QAMetricsResponse(BaseModel):
    """Combined QA metrics: difficulty matching + extraction quality.

    [Source: Story 7.4 Task 5.1 — GET /api/v1/system/qa-metrics]
    """

    difficulty_match: DifficultyMatchStats = Field(
        default_factory=DifficultyMatchStats, description="Difficulty matching statistics"
    )
    extraction_quality: ExtractionStats = Field(
        default_factory=ExtractionStats, description="Extraction quality statistics"
    )
