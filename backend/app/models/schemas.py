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

from pydantic import BaseModel, ConfigDict, Field

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
# Story 36.5: Canvas Association Models
# [Source: docs/stories/36.5.story.md]
# [Source: specs/data/canvas-association.schema.json]
# ═══════════════════════════════════════════════════════════════════════════════

class AssociationType(str, Enum):
    """
    Canvas association type enum.

    Story 36.5 AC-2, AC-5: Schema-defined association types.

    [Source: specs/data/canvas-association.schema.json#/properties/association_type/enum]
    """
    prerequisite = "prerequisite"
    related = "related"
    extends = "extends"
    references = "references"


class CanvasAssociationCreate(BaseModel):
    """
    Request model for creating a canvas association.

    Story 36.5 Task 4.1: Pydantic model validation.

    [Source: specs/data/canvas-association.schema.json]
    [Source: docs/stories/36.5.story.md#Task-4.1]
    """
    source_canvas: str = Field(
        ...,
        description="Source canvas file path",
        min_length=1
    )
    target_canvas: str = Field(
        ...,
        description="Target canvas file path",
        min_length=1
    )
    association_type: AssociationType = Field(
        ...,
        description="Type of association: prerequisite, related, extends, references"
    )
    shared_concepts: Optional[List[str]] = Field(
        default=None,
        description="List of shared concept names"
    )
    relevance_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Relevance score (0-1)"
    )
    bidirectional: bool = Field(
        default=False,
        description="Whether association is bidirectional"
    )
    auto_generated: bool = Field(
        default=False,
        description="Whether association was auto-generated"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "source_canvas": "exercises/math_exam.canvas",
                "target_canvas": "lectures/calculus_intro.canvas",
                "association_type": "prerequisite",
                "shared_concepts": ["derivatives", "integrals"],
                "relevance_score": 0.85,
                "bidirectional": False,
                "auto_generated": False
            }
        }
    )


class CanvasAssociationResponse(BaseModel):
    """
    Response model for a canvas association.

    Story 36.5 Task 4.1: Pydantic model validation.

    [Source: specs/data/canvas-association.schema.json]
    [Source: docs/stories/36.5.story.md#Task-4.2]
    """
    association_id: str = Field(
        ...,
        description="Unique association identifier (UUID)"
    )
    source_canvas: str = Field(
        ...,
        description="Source canvas file path"
    )
    target_canvas: str = Field(
        ...,
        description="Target canvas file path"
    )
    association_type: AssociationType = Field(
        ...,
        description="Type of association"
    )
    shared_concepts: List[str] = Field(
        default_factory=list,
        description="List of shared concept names"
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence score (0-1)"
    )
    bidirectional: bool = Field(
        default=False,
        description="Whether association is bidirectional"
    )
    auto_generated: bool = Field(
        default=False,
        description="Whether association was auto-generated"
    )
    created_at: Optional[datetime] = Field(
        default=None,
        description="Creation timestamp"
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        description="Last update timestamp"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "association_id": "cca-a1b2c3d4e5f6",
                "source_canvas": "exercises/math_exam.canvas",
                "target_canvas": "lectures/calculus_intro.canvas",
                "association_type": "prerequisite",
                "shared_concepts": ["derivatives", "integrals"],
                "confidence": 0.85,
                "bidirectional": False,
                "auto_generated": False,
                "created_at": "2026-01-20T10:30:00Z",
                "updated_at": "2026-01-20T10:30:00Z"
            }
        }
    )


class CanvasAssociationUpdate(BaseModel):
    """
    Request model for updating a canvas association.

    Story 36.5 Task 4.1: Pydantic model validation.

    [Source: docs/stories/36.5.story.md#Task-4.1]
    """
    association_type: Optional[AssociationType] = Field(
        default=None,
        description="New association type"
    )
    shared_concepts: Optional[List[str]] = Field(
        default=None,
        description="New list of shared concepts"
    )
    confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="New confidence score (0-1)"
    )
    bidirectional: Optional[bool] = Field(
        default=None,
        description="New bidirectional flag"
    )


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
    [Story 2.8: Added node_content for real-time content passing]
    """
    canvas_name: str = Field(..., description="Canvas file name")
    node_ids: List[str] = Field(..., description="Node IDs to score")
    node_content: Optional[str] = Field(None, description="Node content to score (passed from plugin)")


class NodeScore(BaseModel):
    """
    Score result for a single node.

    [Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/NodeScore]
    [Source: specs/data/node-score.schema.json]
    [Source: .claude/agents/scoring.md - Output Format]
    """
    node_id: str = Field(..., description="Node ID")
    accuracy: float = Field(..., ge=0, le=25, description="Accuracy score (0-25)")
    imagery: float = Field(..., ge=0, le=25, description="Imagery score (0-25)")
    completeness: float = Field(..., ge=0, le=25, description="Completeness score (0-25)")
    originality: float = Field(..., ge=0, le=25, description="Originality score (0-25)")
    total: float = Field(..., ge=0, le=100, description="Total score (0-100)")
    new_color: str = Field(..., description="New node color: 2=green(>=80), 3=purple(60-79), 4=red(<60)")
    feedback: Optional[str] = Field(None, description="Specific improvement suggestions (100-200 chars)")
    color_action: Optional[str] = Field(None, description="Color action: change_to_green/change_to_purple/keep_red")


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

    Story 32.2 AC-32.2.2: Accepts FSRS ratings (1-4) in addition to legacy score.
    Story 32.2 AC-32.2.4: Backward compatible - either rating OR score must be provided.

    [Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/RecordReviewRequest]
    [Source: specs/api/review-api.openapi.yml#L542-L563]
    [Source: docs/stories/32.2.story.md]
    """
    canvas_name: str = Field(..., description="Canvas file name")
    node_id: str = Field(..., description="Node ID (maps to concept_id)")
    # Story 32.2: FSRS rating field (primary)
    rating: Optional[int] = Field(
        None,
        ge=1,
        le=4,
        description="FSRS rating: 1=Again (forgot), 2=Hard, 3=Good, 4=Easy"
    )
    # Story 32.2 AC-32.2.4: Legacy score field (backward compatibility)
    score: Optional[float] = Field(
        None,
        ge=0,
        le=100,
        description="Legacy score (0-100). Auto-converted to rating: <40=Again, 40-59=Hard, 60-84=Good, >=85=Easy"
    )
    # Optional card state for persistence
    card_state: Optional[str] = Field(
        None,
        description="Serialized FSRS card JSON from previous review (for card state continuity)"
    )
    review_duration: Optional[int] = Field(
        None,
        description="Review time in seconds (for metrics)"
    )

    @property
    def concept_id(self) -> str:
        """Alias node_id as concept_id for FSRS integration."""
        return self.node_id


class FSRSStateResponse(BaseModel):
    """
    FSRS card state in response.

    Story 32.2: Exposes FSRS algorithm internal state for transparency.
    Story 32.3: Extended with retrievability and due for plugin priority calculation.

    [Source: specs/data/fsrs-card.schema.json]
    [Source: docs/stories/32.3.story.md]
    """
    stability: float = Field(..., description="Memory stability (days)")
    difficulty: float = Field(..., ge=1, le=10, description="Card difficulty (1-10)")
    state: int = Field(..., description="Card state: 0=New, 1=Learning, 2=Review, 3=Relearning")
    reps: int = Field(0, description="Successful review count")
    lapses: int = Field(0, description="Failed review count (rating=1)")
    # Story 32.3: Additional fields for plugin priority calculation
    retrievability: Optional[float] = Field(
        None,
        ge=0,
        le=1,
        description="Current retrievability probability (0-1)"
    )
    due: Optional[datetime] = Field(
        None,
        description="Next due date/time for review"
    )


class FSRSStateQueryResponse(BaseModel):
    """
    Response model for GET /api/v1/review/fsrs-state/{concept_id} endpoint.

    Story 32.3: Plugin queries this endpoint to get FSRS state for priority calculation.

    [Source: specs/api/review-api.openapi.yml#FSRSStateQueryResponse]
    [Source: docs/stories/32.3.story.md#Task-1]
    """
    concept_id: str = Field(..., description="Concept identifier")
    fsrs_state: Optional[FSRSStateResponse] = Field(
        None,
        description="FSRS algorithm state (None if no card exists)"
    )
    card_state: Optional[str] = Field(
        None,
        description="Serialized FSRS card JSON for plugin to deserialize"
    )
    found: bool = Field(
        True,
        description="Whether a card was found for this concept"
    )


class RecordReviewResponse(BaseModel):
    """
    Response model for recorded review result.

    Story 32.2: Enhanced with FSRS state and dynamic interval.

    [Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/RecordReviewResponse]
    [Source: specs/api/review-api.openapi.yml#L565-L594]
    [Source: docs/stories/32.2.story.md]
    """
    next_review_date: date = Field(..., description="Next review date (FSRS calculated)")
    new_interval: int = Field(..., description="New review interval in days (dynamic)")
    # Story 32.2: FSRS state for client persistence
    fsrs_state: Optional[FSRSStateResponse] = Field(
        None,
        description="FSRS algorithm state (stability, difficulty, etc.)"
    )
    card_data: Optional[str] = Field(
        None,
        description="Serialized FSRS card JSON for next review"
    )
    algorithm: str = Field(
        "fsrs-4.5",
        description="Algorithm used: 'fsrs-4.5' or 'ebbinghaus-fallback'"
    )


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


# ═══════════════════════════════════════════════════════════════════════════════
# Story 31.3: Intelligent Action Recommendation Schemas
# [Source: specs/data/recommend-action-request.schema.json]
# [Source: specs/data/recommend-action-response.schema.json]
# ═══════════════════════════════════════════════════════════════════════════════

class ActionType(str, Enum):
    """
    Recommended action type based on score thresholds.

    [Source: specs/data/recommend-action-response.schema.json#action]
    [Source: docs/stories/31.3.story.md#AC-31.3.3]

    Thresholds (0-100 scale):
    - decompose: score < 60
    - explain: score 60-79
    - next: score >= 80
    """
    decompose = "decompose"
    explain = "explain"
    next = "next"


class ActionTrend(str, Enum):
    """
    Score trend direction for history analysis.

    [Source: specs/data/recommend-action-response.schema.json#history_context.trend]
    """
    improving = "improving"
    stable = "stable"
    declining = "declining"


class HistoryContext(BaseModel):
    """
    Historical score context for recommendation.

    [Source: specs/data/recommend-action-response.schema.json#history_context]
    [Source: docs/stories/31.3.story.md#AC-31.3.4]
    """
    recent_scores: List[int] = Field(
        default_factory=list,
        description="Recent score history (most recent first, up to 5)",
        max_length=5
    )
    average_score: Optional[float] = Field(
        None,
        ge=0,
        le=100,
        description="Average of recent scores"
    )
    trend: Optional[ActionTrend] = Field(
        None,
        description="Score trend direction"
    )
    consecutive_low_count: int = Field(
        default=0,
        ge=0,
        description="Number of consecutive scores below 60"
    )


class AlternativeAgent(BaseModel):
    """
    Alternative agent recommendation.

    [Source: specs/data/recommend-action-response.schema.json#alternative_agents]
    """
    agent: str = Field(..., description="Agent endpoint path")
    reason: str = Field(..., description="Reason for this alternative")


class RecommendActionRequest(BaseModel):
    """
    Request model for intelligent action recommendation.

    [Source: specs/data/recommend-action-request.schema.json]
    [Source: docs/stories/31.3.story.md#AC-31.3.1, AC-31.3.2]
    """
    score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Current total score (0-100 scale)"
    )
    node_id: str = Field(
        ...,
        min_length=1,
        description="Canvas node ID being evaluated"
    )
    canvas_name: str = Field(
        ...,
        min_length=1,
        description="Canvas file name"
    )
    include_history: bool = Field(
        default=True,
        description="Whether to include historical score analysis"
    )
    concept: Optional[str] = Field(
        None,
        description="Concept name (optional, used for history lookup)"
    )


class RecommendActionResponse(BaseModel):
    """
    Response model for intelligent action recommendation.

    [Source: specs/data/recommend-action-response.schema.json]
    [Source: docs/stories/31.3.story.md#AC-31.3.3, AC-31.3.4]

    Recommendation Logic (0-100 scale):
    - score < 60: decompose (basic-decomposition)
    - score 60-79: explain (oral-explanation)
    - score >= 80: next (mastered)
    """
    action: ActionType = Field(
        ...,
        description="Recommended action type"
    )
    agent: Optional[str] = Field(
        None,
        description="Recommended agent endpoint path, null for 'next' action"
    )
    reason: str = Field(
        ...,
        min_length=1,
        description="Human-readable explanation for the recommendation"
    )
    priority: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Recommendation priority (1=highest, 5=lowest)"
    )
    review_suggested: bool = Field(
        default=False,
        description="Whether additional review is suggested based on declining trend"
    )
    history_context: Optional[HistoryContext] = Field(
        None,
        description="Historical score context (when include_history=true)"
    )
    alternative_agents: List[AlternativeAgent] = Field(
        default_factory=list,
        description="Alternative agent recommendations",
        max_length=3
    )
