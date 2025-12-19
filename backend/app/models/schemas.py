# Canvas Learning System - Pydantic Schemas
# Story 15.2: Routing System and APIRouter Configuration
# Source: specs/api/fastapi-backend-api.openapi.yml
"""
Pydantic Models for Canvas Learning System API.

All models are derived from the OpenAPI specification:
[Source: specs/api/fastapi-backend-api.openapi.yml]
"""

from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

# ═══════════════════════════════════════════════════════════════════════════════
# Common Schemas
# ═══════════════════════════════════════════════════════════════════════════════

class HealthStatus(str, Enum):
    """Health status enum."""
    healthy = "healthy"
    unhealthy = "unhealthy"


class HealthCheckResponse(BaseModel):
    """
    Health check response model.

    [Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/HealthCheckResponse]
    """
    status: HealthStatus = Field(..., description="Application health status")
    app_name: str = Field(..., description="Application name")
    version: str = Field(..., description="Application version")
    timestamp: datetime = Field(..., description="Check timestamp")


# ═══════════════════════════════════════════════════════════════════════════════
# Story 12.G.3: Agent Health Check Response Models
# [Source: docs/stories/story-12.G.3-api-health-check.md]
# [Source: specs/data/health-check-response.schema.json]
# ═══════════════════════════════════════════════════════════════════════════════

class AgentHealthStatus(str, Enum):
    """
    Agent system health status enum.

    - healthy: All checks pass
    - degraded: Configuration OK but some templates missing
    - unhealthy: API Key not configured or GeminiClient not initialized

    [Source: specs/data/health-check-response.schema.json#L20-22]
    [Source: specs/api/agent-api.openapi.yml#AgentHealthCheckResponse]
    """
    healthy = "healthy"
    degraded = "degraded"
    unhealthy = "unhealthy"


class PromptTemplateCheck(BaseModel):
    """
    Prompt template check result.

    [Source: specs/data/health-check-response.schema.json#L37-58]
    """
    total: int = Field(..., ge=0, description="Expected total number of templates")
    available: int = Field(..., ge=0, description="Number of available templates")
    missing: List[str] = Field(default_factory=list, description="List of missing template names")


class ApiTestResult(BaseModel):
    """
    Optional API call test result.

    [Source: specs/data/health-check-response.schema.json#L61-74]
    """
    enabled: bool = Field(..., description="Whether API call test was enabled")
    result: Optional[str] = Field(None, description="Test result: 'success' or error message")


class AgentHealthChecks(BaseModel):
    """
    Individual health check results.

    [Source: specs/data/health-check-response.schema.json#L24-75]
    """
    api_key_configured: bool = Field(
        ...,
        description="Whether API Key is configured (does not return actual key value)"
    )
    gemini_client_initialized: bool = Field(
        ...,
        description="Whether GeminiClient is successfully initialized"
    )
    prompt_templates: PromptTemplateCheck = Field(
        ...,
        description="Prompt template check results"
    )
    api_test: Optional[ApiTestResult] = Field(
        None,
        description="Optional API call test result"
    )


class AgentHealthCheckResponse(BaseModel):
    """
    Agent system health check response.

    [Source: docs/stories/story-12.G.3-api-health-check.md]
    [Source: specs/data/health-check-response.schema.json]
    [Source: specs/api/agent-api.openapi.yml#AgentHealthCheckResponse]
    """
    status: AgentHealthStatus = Field(
        ...,
        description="Overall health status: healthy=all checks pass, "
                    "degraded=some templates missing, unhealthy=critical components unavailable"
    )
    checks: AgentHealthChecks = Field(..., description="Individual check results")
    cached: bool = Field(
        default=False,
        description="Whether this is a cached result (cache TTL: 60s, ref: ADR-007)"
    )
    timestamp: datetime = Field(..., description="Check timestamp (ISO 8601 format)")


class ErrorResponse(BaseModel):
    """
    Standard error response model.

    [Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/ErrorResponse]
    """
    code: int = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


# ═══════════════════════════════════════════════════════════════════════════════
# Canvas Schemas
# ═══════════════════════════════════════════════════════════════════════════════

class NodeType(str, Enum):
    """Node type enum."""
    text = "text"
    file = "file"
    group = "group"
    link = "link"


class NodeColor(str, Enum):
    """
    Node color codes (Obsidian Canvas actual display).

    Verified from docs/issues/canvas-layout-lessons-learned.md:
    - "1" = gray (灰白色)
    - "2" = green (绿色) - 完全理解/已通过
    - "3" = purple (紫色) - 似懂非懂/待检验
    - "4" = red (红色) - 不理解/未通过
    - "5" = blue (蓝色) - AI解释
    - "6" = yellow (黄色) - 个人理解输出区

    PRD语义映射:
    - 红色(不理解) → "4"
    - 绿色(完全理解) → "2"
    - 紫色(似懂非懂) → "3"
    - 黄色(个人理解) → "6"
    """
    gray = "1"      # 灰白色
    green = "2"     # 完全理解/已通过
    purple = "3"    # 似懂非懂/待检验
    red = "4"       # 不理解/未通过 (PRD红色语义)
    blue = "5"      # AI解释
    yellow = "6"    # 个人理解输出区 (PRD定义正确)


class EdgeSide(str, Enum):
    """Edge connection side."""
    top = "top"
    bottom = "bottom"
    left = "left"
    right = "right"


class NodeCreate(BaseModel):
    """
    Request model for creating a new node.

    [Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/NodeCreate]
    """
    type: NodeType = Field(..., description="Node type")
    text: Optional[str] = Field(None, description="Text content (required for type=text)")
    file: Optional[str] = Field(None, description="File path (required for type=file)")
    url: Optional[str] = Field(None, description="Link URL (required for type=link)")
    x: int = Field(..., description="X position")
    y: int = Field(..., description="Y position")
    width: int = Field(default=250, description="Node width")
    height: int = Field(default=60, description="Node height")
    color: Optional[NodeColor] = Field(None, description="Node color code")


class NodeUpdate(BaseModel):
    """
    Request model for updating a node.

    [Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/NodeUpdate]
    """
    text: Optional[str] = Field(None, description="Text content")
    x: Optional[int] = Field(None, description="X position")
    y: Optional[int] = Field(None, description="Y position")
    width: Optional[int] = Field(None, description="Node width")
    height: Optional[int] = Field(None, description="Node height")
    color: Optional[NodeColor] = Field(None, description="Node color code")


class NodeRead(BaseModel):
    """
    Response model for a node.

    [Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/NodeRead]
    """
    # Pattern relaxed to accept semantic prefixes (vq-, qd-, explain-, etc.)
    # ✅ Verified from Epic 12.K.1: NodeRead Schema Pattern Fix
    id: str = Field(..., description="Node ID", pattern=r"^[a-zA-Z0-9][-a-zA-Z0-9]*$")
    type: NodeType = Field(..., description="Node type")
    text: Optional[str] = Field(None, description="Text content")
    file: Optional[str] = Field(None, description="File path")
    url: Optional[str] = Field(None, description="Link URL")
    x: int = Field(..., description="X position")
    y: int = Field(..., description="Y position")
    width: Optional[int] = Field(None, description="Node width")
    height: Optional[int] = Field(None, description="Node height")
    color: Optional[NodeColor] = Field(None, description="Node color code")


class EdgeCreate(BaseModel):
    """
    Request model for creating an edge.

    [Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/EdgeCreate]
    """
    fromNode: str = Field(..., description="Source node ID")
    toNode: str = Field(..., description="Target node ID")
    fromSide: Optional[EdgeSide] = Field(None, description="Source side")
    toSide: Optional[EdgeSide] = Field(None, description="Target side")
    label: Optional[str] = Field(None, description="Edge label")


class EdgeRead(BaseModel):
    """
    Response model for an edge.

    [Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/EdgeRead]
    """
    id: str = Field(..., description="Edge ID")
    fromNode: str = Field(..., description="Source node ID")
    toNode: str = Field(..., description="Target node ID")
    fromSide: Optional[str] = Field(None, description="Source side")
    toSide: Optional[str] = Field(None, description="Target side")
    label: Optional[str] = Field(None, description="Edge label")


class CanvasResponse(BaseModel):
    """
    Response model for a Canvas.

    [Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/CanvasResponse]
    """
    name: str = Field(..., description="Canvas file name")
    nodes: List[NodeRead] = Field(..., description="List of nodes")
    edges: List[EdgeRead] = Field(..., description="List of edges")


# ═══════════════════════════════════════════════════════════════════════════════
# Agent Schemas
# ═══════════════════════════════════════════════════════════════════════════════

class DecomposeRequest(BaseModel):
    """
    Request model for concept decomposition.

    [Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/DecomposeRequest]
    [Source: specs/data/decompose-request.schema.json]
    """
    canvas_name: str = Field(..., description="Canvas file name")
    node_id: str = Field(..., description="Target node ID")


class DecomposeResponse(BaseModel):
    """
    Response model for concept decomposition.

    [Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/DecomposeResponse]
    [Source: specs/data/decompose-response.schema.json]
    [Story 12.M.2: Added created_edges for Canvas edge connections]
    """
    questions: List[str] = Field(..., description="Generated guiding questions")
    created_nodes: List[NodeRead] = Field(..., description="Created nodes")
    created_edges: List[EdgeRead] = Field(default_factory=list, description="Created edges connecting nodes")


class ScoreRequest(BaseModel):
    """
    Request model for scoring understanding.

    [Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/ScoreRequest]
    """
    canvas_name: str = Field(..., description="Canvas file name")
    node_ids: List[str] = Field(..., description="Node IDs to score")


class NodeScore(BaseModel):
    """
    Score result for a single node.

    [Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/NodeScore]
    [Source: specs/data/node-score.schema.json]
    """
    node_id: str = Field(..., description="Node ID")
    accuracy: float = Field(..., ge=0, le=10, description="Accuracy score")
    imagery: float = Field(..., ge=0, le=10, description="Imagery score")
    completeness: float = Field(..., ge=0, le=10, description="Completeness score")
    originality: float = Field(..., ge=0, le=10, description="Originality score")
    total: float = Field(..., ge=0, le=40, description="Total score")
    new_color: str = Field(..., description="New node color: 2=green(>=32), 3=yellow(24-31), 4=red(<24)")


class ScoreResponse(BaseModel):
    """
    Response model for scoring.

    [Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/ScoreResponse]
    """
    scores: List[NodeScore] = Field(..., description="Score results")


class ExplainRequest(BaseModel):
    """
    Request model for explanation generation.

    [Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/ExplainRequest]
    [Story 12.B.2: 节点内容实时传递]
    """
    canvas_name: str = Field(..., description="Canvas file name")
    node_id: str = Field(..., description="Target node ID")
    node_content: Optional[str] = Field(
        None,
        description="Real-time node content from plugin (Story 12.B.2). "
                    "If provided, used directly instead of reading from disk."
    )


class ExplainResponse(BaseModel):
    """
    Response model for explanation generation.

    [Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/ExplainResponse]
    """
    explanation: str = Field(..., description="Generated explanation")
    created_node_id: str = Field(..., description="Created explanation node ID")


# ═══════════════════════════════════════════════════════════════════════════════
# Story 12.A.6: verification-question and question-decomposition Agents
# [Source: docs/stories/story-12.A.6-complete-agents.md]
# ═══════════════════════════════════════════════════════════════════════════════

class VerificationQuestionRequest(BaseModel):
    """
    Request model for generating verification questions.

    [Source: docs/stories/story-12.A.6-complete-agents.md#AC1]
    [Source: .claude/agents/verification-question-agent.md]
    """
    canvas_name: str = Field(..., description="Canvas file name")
    node_id: str = Field(..., description="Target node ID")


class VerificationQuestion(BaseModel):
    """
    Single verification question item.

    [Source: .claude/agents/verification-question-agent.md#Output-Format]
    """
    source_node_id: str = Field(..., description="Source node ID this question refers to")
    question_text: str = Field(..., description="The verification question text")
    question_type: str = Field(..., description="Question type: 突破型/检验型/应用型/综合型")
    difficulty: str = Field(..., description="Difficulty level: 基础/深度")
    guidance: Optional[str] = Field(None, description="Optional hint starting with 💡")
    rationale: str = Field(..., description="Why this question was generated")


class VerificationQuestionResponse(BaseModel):
    """
    Response model for verification question generation.

    [Source: docs/stories/story-12.A.6-complete-agents.md#AC1]
    [Source: .claude/agents/verification-question-agent.md#Output-Format]
    """
    questions: List[VerificationQuestion] = Field(..., description="Generated verification questions")
    concept: str = Field(..., description="The concept being verified")
    generated_at: datetime = Field(..., description="Generation timestamp")
    created_nodes: List[NodeRead] = Field(default_factory=list, description="Created question nodes on Canvas")


class QuestionDecomposeRequest(BaseModel):
    """
    Request model for question decomposition.

    [Source: docs/stories/story-12.A.6-complete-agents.md#AC2]
    [Source: .claude/agents/question-decomposition.md]
    """
    canvas_name: str = Field(..., description="Canvas file name")
    node_id: str = Field(..., description="Target node ID")


class SubQuestion(BaseModel):
    """
    Single sub-question from decomposition.

    [Source: .claude/agents/question-decomposition.md#Output-Format]
    """
    text: str = Field(..., description="The sub-question text")
    type: str = Field(..., description="Question type: 检验型/应用型/对比型/推理型")
    guidance: str = Field(..., description="Guidance hint starting with 💡 提示:")


class QuestionDecomposeResponse(BaseModel):
    """
    Response model for question decomposition.

    [Source: docs/stories/story-12.A.6-complete-agents.md#AC2]
    [Source: .claude/agents/question-decomposition.md#Output-Format]
    """
    questions: List[SubQuestion] = Field(..., description="Decomposed verification questions (2-5)")
    created_nodes: List[NodeRead] = Field(default_factory=list, description="Created question nodes on Canvas")


# ═══════════════════════════════════════════════════════════════════════════════
# Review Schemas
# ═══════════════════════════════════════════════════════════════════════════════

class ReviewItem(BaseModel):
    """
    Single review item in schedule.

    [Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/ReviewItem]
    [Source: specs/data/review-item.schema.json]
    """
    canvas_name: str = Field(..., description="Canvas file name")
    node_id: str = Field(..., description="Node ID")
    concept: str = Field(..., description="Concept name")
    due_date: date = Field(..., description="Due date for review")
    interval_days: int = Field(..., description="Current review interval (1/7/30 days)")


class ReviewScheduleResponse(BaseModel):
    """
    Response model for review schedule.

    [Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/ReviewScheduleResponse]
    """
    items: List[ReviewItem] = Field(..., description="Review items")
    total_count: int = Field(..., description="Total item count")


class GenerateReviewRequest(BaseModel):
    """
    Request model for generating verification canvas.

    [Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/GenerateReviewRequest]
    [Source: specs/data/review-generate-request.schema.json - Story 24.1]
    """
    source_canvas: str = Field(..., description="Source Canvas file name")
    node_ids: Optional[List[str]] = Field(
        None,
        description="Specific node IDs (optional, defaults to all green nodes)"
    )
    # ✅ Verified from Story 24.1 Dev Notes (lines 167-178)
    mode: Literal["fresh", "targeted"] = Field(
        default="fresh",
        description="Review mode: fresh=blind test, targeted=weakness-focused"
    )
    weak_weight: float = Field(
        default=0.7,
        ge=0,
        le=1,
        description="Weight for weak concepts in targeted mode"
    )
    mastered_weight: float = Field(
        default=0.3,
        ge=0,
        le=1,
        description="Weight for mastered concepts in targeted mode"
    )


class WeakConceptData(BaseModel):
    """
    Data for a weak concept in targeted review.

    [Source: Story 24.3 - Weight Algorithm Implementation]
    """
    concept_name: str = Field(..., description="Name of the weak concept")
    weakness_score: float = Field(..., ge=0, le=1, description="Calculated weakness score")
    failure_count: int = Field(..., ge=0, description="Historical failure count")
    avg_rating: float = Field(..., ge=0, le=4, description="Average review rating")


class WeightConfig(BaseModel):
    """
    Weight configuration for targeted review.

    [Source: Story 24.3 - Weight Algorithm Implementation]
    """
    weak_weight: float = Field(..., ge=0, le=1, description="Weight for weak concepts")
    mastered_weight: float = Field(..., ge=0, le=1, description="Weight for mastered concepts")
    applied: bool = Field(..., description="Whether weights were applied")


class GenerateReviewResponse(BaseModel):
    """
    Response model for generated verification canvas.

    [Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/GenerateReviewResponse]
    [Source: specs/data/review-generate-response.schema.json - Story 24.1]
    [Source: Story 24.3 - Added weak_concepts and weight_config fields]
    """
    verification_canvas_name: str = Field(..., description="Generated verification canvas name")
    node_count: int = Field(..., description="Number of verification nodes")
    # ✅ Verified from Story 24.1 Dev Notes - Response Enhancement
    mode_used: Optional[str] = Field(None, description="Mode used for generation (fresh/targeted)")
    # ✅ Story 24.3 additions - Weight Algorithm Response Enhancement
    weak_concepts: List["WeakConceptData"] = Field(
        default_factory=list,
        description="Weak concepts identified in targeted mode"
    )
    weight_config: Optional["WeightConfig"] = Field(
        None,
        description="Weight configuration used in targeted mode"
    )


class RecordReviewRequest(BaseModel):
    """
    Request model for recording review result.

    [Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/RecordReviewRequest]
    """
    canvas_name: str = Field(..., description="Canvas file name")
    node_id: str = Field(..., description="Node ID")
    score: float = Field(..., ge=0, le=40, description="Review score (0-40)")


class RecordReviewResponse(BaseModel):
    """
    Response model for recorded review result.

    [Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/RecordReviewResponse]
    """
    next_review_date: date = Field(..., description="Next review date")
    new_interval: int = Field(..., description="New review interval in days")


# ═══════════════════════════════════════════════════════════════════════════════
# Multi-Review Progress Schemas (Story 24.2)
# ═══════════════════════════════════════════════════════════════════════════════

class ReviewSessionSummary(BaseModel):
    """
    Single review session summary.

    [Source: specs/api/review-api.openapi.yml#L725-805]
    [Source: docs/stories/24.2.story.md - Dev Notes]
    """
    review_canvas_path: str = Field(..., description="Path to review canvas file")
    date: datetime = Field(..., description="Review session date")
    mode: str = Field(..., description="Review mode: fresh or targeted")
    pass_rate: float = Field(..., ge=0, le=1, description="Pass rate (0-1)")
    total_concepts: int = Field(..., description="Total concepts reviewed")
    passed_concepts: int = Field(..., description="Concepts passed (≥80%)")


class PassRateTrendPoint(BaseModel):
    """
    Single point in pass rate trend.

    [Source: specs/api/review-api.openapi.yml#L725-805]
    [Source: docs/stories/24.2.story.md - Dev Notes]
    """
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    pass_rate: float = Field(..., ge=0, le=1, description="Pass rate (0-1)")


class WeakConceptImprovement(BaseModel):
    """
    Weak concept improvement tracking.

    [Source: specs/api/review-api.openapi.yml#L725-805]
    [Source: docs/stories/24.2.story.md - Dev Notes]
    """
    concept_name: str = Field(..., description="Concept name")
    improvement_rate: float = Field(..., description="Improvement rate (current-first)/first")
    current_status: str = Field(
        ...,
        description="Current status: weak (<60), improving (60-79), mastered (≥80)"
    )


class OverallProgress(BaseModel):
    """
    Overall progress metrics.

    [Source: specs/api/review-api.openapi.yml#L725-805]
    [Source: docs/stories/24.2.story.md - Dev Notes]
    """
    progress_rate: float = Field(..., description="Progress rate (latest-first)/first")
    trend_direction: str = Field(
        ...,
        description="Trend direction: up (>0.1), stable (-0.1 to 0.1), down (<-0.1)"
    )


class TrendsData(BaseModel):
    """
    Trend analysis data.

    [Source: specs/api/review-api.openapi.yml#L725-805]
    [Source: docs/stories/24.2.story.md - Dev Notes]
    """
    pass_rate_trend: List[PassRateTrendPoint] = Field(..., description="Pass rate trend over time")
    weak_concepts_improvement: List[WeakConceptImprovement] = Field(
        ...,
        description="Weak concepts improvement tracking"
    )
    overall_progress: OverallProgress = Field(..., description="Overall progress metrics")


class MultiReviewProgressResponse(BaseModel):
    """
    Full multi-review progress response.

    [Source: specs/api/review-api.openapi.yml#L346-378, L725-805]
    [Source: docs/stories/24.2.story.md - AC1]
    """
    original_canvas_path: str = Field(..., description="Original canvas file path")
    review_count: int = Field(..., description="Total number of reviews")
    reviews: List[ReviewSessionSummary] = Field(..., description="List of review sessions")
    trends: Optional[TrendsData] = Field(None, description="Trend analysis (only if ≥2 reviews)")
