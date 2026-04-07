# Canvas Learning System - Exam Models
# Story 6.1-6.8: Examination Whiteboard system models
#
# Pydantic models for exam session lifecycle management.
# [Source: _bmad-output/implementation-artifacts/6-1 through 6-8]
"""
Exam session and scoring Pydantic models.

Story 6.1: ExamSession, ExamNode lifecycle
Story 6.2: CanvasAnalysis, ContentType, ExamMode
Story 6.3: ACP, QuestionGeneration, NodePriority
Story 6.4: AutoSCORE, RubricDimension
Story 6.5: DiscoveredNode, ExamNodeSync
Story 6.6: HintRequest/Response, SkipRecord
Story 6.7: CognitiveLoad thresholds, pause/resume
Story 6.8: ExamRecord persistence, ExamRecordSummary/Detail
"""

from datetime import datetime, timezone
from enum import Enum, IntEnum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class ExamMode(str, Enum):
    """Examination mode (Story 6.2 AC-1)."""

    POINT_TO_POINT = "point_to_point"
    COMPREHENSIVE = "comprehensive"
    MIXED = "mixed"


class ExamStatus(str, Enum):
    """Exam session lifecycle status (Story 6.1 AC-5)."""

    IDLE = "idle"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"


class ContentType(str, Enum):
    """Canvas content classification for mode recommendation (Story 6.2 AC-2)."""

    KNOWLEDGE = "knowledge"
    PROBLEM = "problem"
    MIXED = "mixed"


# ═══════════════════════════════════════════════════════════════════════════════
# Exam Session Models
# ═══════════════════════════════════════════════════════════════════════════════


class ExamSessionCreate(BaseModel):
    """Request body for POST /api/v1/exam/start (Story 6.1 AC-1)."""

    source_canvas_id: str = Field(..., description="Original canvas board ID")
    exam_mode: ExamMode = Field(default=ExamMode.MIXED, description="Examination mode")
    target_node_id: Optional[str] = Field(
        None, description="Single-node exam target (Story 6.2 AC-6)"
    )


class ExamSessionResponse(BaseModel):
    """Full exam session record (Story 6.1 AC-6)."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    source_canvas_id: str
    exam_mode: ExamMode = ExamMode.MIXED
    status: ExamStatus = ExamStatus.IDLE
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    examined_nodes: List[str] = Field(default_factory=list)
    discovered_nodes: List[str] = Field(default_factory=list)
    score_history: List[Dict[str, Any]] = Field(default_factory=list)
    target_node_id: Optional[str] = None
    current_node_id: Optional[str] = None
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class ExamStatusUpdate(BaseModel):
    """Request body for PATCH /api/v1/exam/{exam_id}/status (Story 6.1 AC-6)."""

    status: ExamStatus
    current_node_id: Optional[str] = None
    exam_mode: Optional[ExamMode] = None


class ExamSessionListResponse(BaseModel):
    """Response for GET /api/v1/exam/by-canvas/{canvas_id}."""

    sessions: List[ExamSessionResponse]
    total: int


# ═══════════════════════════════════════════════════════════════════════════════
# Content Analysis Models (Story 6.2)
# ═══════════════════════════════════════════════════════════════════════════════


class CanvasAnalysisRequest(BaseModel):
    """Request body for POST /api/v1/exam/analyze-canvas (Story 6.2 AC-2)."""

    canvas_id: str = Field(..., description="Canvas board to analyze")
    target_node_id: Optional[str] = Field(
        None, description="Analyze single node instead of full canvas"
    )


class CanvasAnalysisResponse(BaseModel):
    """Response for canvas content type analysis (Story 6.2 AC-2)."""

    content_type: ContentType
    recommended_mode: ExamMode
    confidence: float = Field(ge=0.0, le=1.0)
    analysis_detail: str = ""


# ═══════════════════════════════════════════════════════════════════════════════
# Exam Score Models (Story 6.4)
# ═══════════════════════════════════════════════════════════════════════════════


class RubricDimension(BaseModel):
    """Single rubric dimension score (Story 6.4 AC-2)."""

    score: int = Field(ge=0, le=3, description="0-3 SOLO-anchored score")
    justification: str = ""
    low_confidence: bool = False


class AutoScoreResult(BaseModel):
    """AutoSCORE evaluation result (Story 6.4 AC-2, AC-3, Story 6.9 faithfulness)."""

    node_id: str
    exam_id: str
    question_id: str = ""
    evidence_points: List[str] = Field(default_factory=list)
    concept_accuracy: RubricDimension = Field(default_factory=RubricDimension)
    reasoning_quality: RubricDimension = Field(default_factory=RubricDimension)
    knowledge_coverage: RubricDimension = Field(default_factory=RubricDimension)
    knowledge_integration: RubricDimension = Field(default_factory=RubricDimension)
    overall_score: int = Field(ge=0, le=12)
    grade: int = Field(ge=1, le=4, description="1=Again, 2=Hard, 3=Good, 4=Easy")
    confidence: str = Field(default="high", description="high | medium | low")
    low_confidence_dimensions: List[str] = Field(default_factory=list)
    feedback_summary: str = ""
    scored_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    # Story 6.9: Scoring Faithfulness fields (AC-1, AC-2)
    faithfulness_score: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Combined faithfulness score (grounding + consistency) / 2",
    )
    faithfulness_passed: bool = Field(
        default=True,
        description="True if faithfulness_score >= 0.85 and not overall low confidence",
    )
    evidence_grounding_score: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Stage 1 evidence grounding score"
    )
    score_consistency_score: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Stage 2 score-evidence consistency score",
    )
    faithfulness_details: Dict[str, Any] = Field(
        default_factory=dict, description="Detailed faithfulness check results"
    )
    verified: bool = Field(
        default=True,
        description="False if faithfulness check failed; score pending re-verification",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# ACP Models (Story 6.3)
# ═══════════════════════════════════════════════════════════════════════════════


class ACPData(BaseModel):
    """Assessment Context Package for question generation (Story 6.3 AC-2).

    Assembled from Graphiti + mastery_engine + SQLite.
    Token budget: 3K tokens max.
    """

    node_id: str
    node_content: str = ""
    node_type: str = Field(
        default="knowledge_point", description="knowledge_point | problem_type"
    )
    student_tips: List[str] = Field(default_factory=list)
    error_history: List[Dict[str, str]] = Field(default_factory=list)
    edge_reasons: List[str] = Field(default_factory=list)
    mastery_level: float = 0.0
    mastery_label: str = "Not Assessed"
    effective_proficiency: float = 0.0
    conversation_summary: str = ""
    retrievability: float = 1.0
    p_mastery: float = 0.1
    kg_relevance: float = 0.0


class QuestionGenerationResult(BaseModel):
    """Result from question_generator (Story 6.3 AC-5)."""

    question_text: str
    question_type: str = "explanation"
    target_bloom_level: str = "understand"
    target_error_type: Optional[str] = None
    difficulty_rationale: str = ""
    scoring_hints: str = ""
    target_node_id: str = ""
    difficulty_level: str = "medium"
    token_a: str = ""


class NodePriority(BaseModel):
    """Node priority for exam target selection (Story 6.3 AC-1).

    FR-KG-04 (openspec change fix-fr-kg-04-schema-drift-and-sync-hardening):
    ``kg_relevance_degraded`` records *why* the knowledge-graph relevance
    factor fell back to the moderate default (0.5), preventing the silent
    degradation that hid the original schema-drift bug. Possible values:

    - ``None``: kg_relevance was computed from real graph data
    - ``"empty_graph"``: query ran but found no CANVAS_EDGE/RELATES_TO neighbors
    - ``"neo4j_unavailable"``: query raised ConnectionError/RuntimeError/timeout
    """

    node_id: str
    priority_score: float
    p_mastery: float
    retrievability: float
    kg_relevance: float
    kg_relevance_degraded: Optional[str] = None
    already_examined: bool = False


# ═══════════════════════════════════════════════════════════════════════════════
# Story 6.5: Recursive Exam — Discovered Node Tracking
# ═══════════════════════════════════════════════════════════════════════════════


class DiscoveredNode(BaseModel):
    """A node discovered during recursive examination.

    Tracks the provenance chain: which node's dialogue led to this discovery,
    at what recursion depth, and when.

    [Source: Story 6.5 AC-7]
    """

    node_id: str = Field(..., description="ID of the newly discovered node")
    source_node_id: str = Field(
        ..., description="Node whose dialogue led to this discovery"
    )
    depth: int = Field(
        ..., ge=1, description="Recursion depth (1 = pulled from original exam node)"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the node was discovered",
    )
    source_exam_id: str = Field(
        "", description="ID of the exam whiteboard where discovered"
    )


class ExamNodeSyncRequest(BaseModel):
    """Request to sync a new node from exam whiteboard back to source canvas.

    [Source: Story 6.5 AC-2]
    """

    exam_id: str = Field(..., description="Exam whiteboard ID")
    source_canvas_id: str = Field(..., description="Original canvas to sync back to")
    node_id: str = Field(..., description="New node ID")
    node_text: str = Field(..., description="Node text content")
    source_node_id: str = Field(..., description="Parent node in exam context")
    suggested_relation: str = Field(
        "related_to", description="LLM-suggested relation type"
    )
    position_x: Optional[float] = Field(None, description="X position on source canvas")
    position_y: Optional[float] = Field(None, description="Y position on source canvas")


class ExamNodeSyncResponse(BaseModel):
    """Response after syncing a node back to source canvas.

    [Source: Story 6.5 AC-2, AC-3]
    """

    node_id: str
    synced_to_canvas: bool = True
    synced_to_neo4j: bool = True
    edge_created: bool = True
    status: str = "ok"
    message: str = ""


# ═══════════════════════════════════════════════════════════════════════════════
# Story 6.6: 4-Level Progressive Hints + Skip
# ═══════════════════════════════════════════════════════════════════════════════


class HintLevel(IntEnum):
    """4-level Chain-of-Hints progression.

    Reference: Chain-of-Hints (2025) — progressive hints from vague to specific.
    [Source: Story 6.6 AC-1]
    """

    DIRECTION = 1  # Point thinking direction, no answer revealed
    KEYWORD = 2  # Key terms or concept names
    PARTIAL_FRAMEWORK = 3  # Partial answer framework / step skeleton
    SCAFFOLDED_GUIDE = 4  # Detailed step-by-step guide, near-complete


class HintRequest(BaseModel):
    """Request for a progressive hint.

    [Source: Story 6.6 AC-6]
    """

    exam_id: str = Field(..., description="Exam session ID")
    node_id: str = Field(..., description="Node being examined")
    hint_level: int = Field(
        ..., ge=1, le=4, description="Hint level 1-4 (direction -> scaffolded)"
    )
    question_context: str = Field(
        ..., description="Current question text for hint generation"
    )
    question_id: str = Field("", description="Question ID if available")


class HintResponse(BaseModel):
    """Response containing the generated hint.

    [Source: Story 6.6 AC-6]
    """

    hint_text: str = Field(..., description="Generated hint text")
    current_level: int = Field(..., ge=1, le=4, description="Current hint level")
    remaining_levels: int = Field(
        ..., ge=0, le=3, description="How many hint levels remain"
    )
    status: str = "ok"
    message: str = ""
    # F12: Scaffolding gradual deprecation
    hint_available: bool = Field(
        True, description="Whether hints are available (F12 mastery fade-out)"
    )
    max_allowed_level: int = Field(
        4, ge=0, le=4, description="Highest hint level allowed by mastery"
    )


class HintUsage(BaseModel):
    """Tracks hint usage for a node during an exam session.

    [Source: Story 6.6 AC-7]
    """

    node_id: str
    max_hint_level_used: int = Field(
        0, ge=0, le=4, description="Highest hint level used (0 = no hints)"
    )
    hint_texts: List[str] = Field(
        default_factory=list, description="Hint texts provided at each level"
    )


class SkipRecord(BaseModel):
    """Record of a skipped question — no BKT/FSRS penalty.

    Skipping != wrong answer. p_mastery stays unchanged.
    [Source: Story 6.6 AC-4]
    """

    node_id: str = Field(..., description="Node that was skipped")
    question_id: str = Field("", description="Question that was skipped")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )


class SkipRequest(BaseModel):
    """Request to skip the current question.

    [Source: Story 6.6 AC-4]
    """

    exam_id: str = Field(..., description="Exam session ID")
    node_id: str = Field(..., description="Node being examined")
    question_id: str = Field("", description="Question being skipped")


class SkipResponse(BaseModel):
    """Response after skipping a question.

    [Source: Story 6.6 AC-4]
    """

    skipped: bool = True
    bkt_penalized: bool = Field(
        False, description="Always False — skip never penalizes BKT"
    )
    fsrs_updated: bool = Field(
        False, description="Always False — skip never triggers FSRS update"
    )
    status: str = "ok"
    message: str = ""


# ═══════════════════════════════════════════════════════════════════════════════
# Story 6.7: Cognitive Load Control
# ═══════════════════════════════════════════════════════════════════════════════

# Cognitive load thresholds (minutes) — progressive rest reminders
# [Source: Story 6.7 AC-1, PRD FR-EXAM-08]
COGNITIVE_LOAD_THRESHOLDS = [15, 25, 35, 45]

COGNITIVE_LOAD_MESSAGES: Dict[int, str] = {
    15: "你已经考察了 15 分钟，可以休息一下",
    25: "连续考察 25 分钟了，建议休息 5 分钟",
    35: "已持续 35 分钟，大脑需要休息才能更好吸收",
    45: "连续 45 分钟了，强烈建议休息。休息后回来效果更好",
}


class ExamStatusUpdateResponse(BaseModel):
    """Response after updating exam status (pause/resume).

    [Source: Story 6.7 AC-6]
    """

    exam_id: str
    status: ExamStatus
    updated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    message: str = ""


# ═══════════════════════════════════════════════════════════════════════════════
# Story 6.8: Exam Record Persistence
# ═══════════════════════════════════════════════════════════════════════════════


class NodeScoreRecord(BaseModel):
    """Score record for a single node within an exam.

    [Source: Story 6.8 AC-1]
    """

    node_id: str
    node_text: str = ""
    concept_accuracy: int = Field(0, ge=0, le=3)
    reasoning_quality: int = Field(0, ge=0, le=3)
    knowledge_coverage: int = Field(0, ge=0, le=3)
    knowledge_integration: int = Field(0, ge=0, le=3)
    overall_score: int = Field(0, ge=0, le=12)
    grade: int = Field(
        0, ge=0, le=4, description="1=Forgot, 2=Struggled, 3=Correct, 4=Fluent"
    )
    confidence: str = Field("medium", description="high|medium|low")
    hint_usage: Optional[HintUsage] = None
    proficiency_before: float = Field(0.0, ge=0.0, le=1.0)
    proficiency_after: float = Field(0.0, ge=0.0, le=1.0)


class ConversationMessage(BaseModel):
    """A single message in exam conversation replay.

    [Source: Story 6.8 AC-3]
    """

    role: str = Field(
        ..., description="user | assistant | system | hint | rest_reminder"
    )
    content: str = Field(..., description="Message text")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    node_id: str = Field("", description="Associated node if applicable")


class MasteryChange(BaseModel):
    """Mastery change for a node before/after exam.

    [Source: Story 6.8 AC-1]
    """

    node_id: str
    node_text: str = ""
    proficiency_before: float = Field(0.0, ge=0.0, le=1.0)
    proficiency_after: float = Field(0.0, ge=0.0, le=1.0)
    trend: str = Field("stable", description="up | down | stable")


class ExamCompleteRequest(BaseModel):
    """Request to finalize and save a complete exam record.

    [Source: Story 6.8 AC-1, AC-8]
    """

    exam_id: str = Field(..., description="Exam session ID")
    source_canvas_id: str = Field(..., description="Original canvas board ID")
    source_canvas_name: str = Field("", description="Original canvas board name")
    exam_mode: str = Field(
        "comprehensive",
        description="point_to_point | comprehensive | mixed",
    )
    start_time: str = Field(..., description="Exam start time ISO string")
    end_time: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Exam end time",
    )
    active_duration_seconds: int = Field(
        0, ge=0, description="Active exam time (excluding pauses/inactive)"
    )
    score_history: List[NodeScoreRecord] = Field(
        default_factory=list, description="Per-node scoring records"
    )
    discovered_nodes: List[DiscoveredNode] = Field(
        default_factory=list, description="Nodes discovered via recursive exam"
    )
    skipped_nodes: List[SkipRecord] = Field(
        default_factory=list, description="Skipped questions"
    )
    conversation_log: List[ConversationMessage] = Field(
        default_factory=list, description="Full conversation replay data"
    )
    mastery_changes: List[MasteryChange] = Field(
        default_factory=list, description="Per-node mastery deltas"
    )


class ExamCompleteResponse(BaseModel):
    """Response after saving exam record.

    [Source: Story 6.8 AC-8]
    """

    exam_id: str
    saved: bool = True
    record_id: str = Field("", description="Persistent record ID in Neo4j")
    status: str = "ok"
    message: str = ""


class ExamRecordSummary(BaseModel):
    """Summary view of an exam record for dashboard listing.

    [Source: Story 6.8 AC-2, AC-5]
    """

    exam_id: str
    source_canvas_id: str = ""
    source_canvas_name: str = ""
    exam_mode: str = "comprehensive"
    created_at: str = ""
    active_duration_seconds: int = 0
    nodes_examined: int = 0
    discovered_nodes_count: int = 0
    skipped_nodes_count: int = 0
    mastery_trend: str = Field("stable", description="up | down | stable")
    status: str = "completed"


class ExamRecordDetail(BaseModel):
    """Full exam record detail including conversation replay.

    [Source: Story 6.8 AC-3, AC-4]
    """

    exam_id: str
    source_canvas_id: str = ""
    source_canvas_name: str = ""
    exam_mode: str = "comprehensive"
    start_time: str = ""
    end_time: str = ""
    active_duration_seconds: int = 0
    status: str = "completed"
    score_history: List[NodeScoreRecord] = Field(default_factory=list)
    discovered_nodes: List[DiscoveredNode] = Field(default_factory=list)
    skipped_nodes: List[SkipRecord] = Field(default_factory=list)
    conversation_log: List[ConversationMessage] = Field(default_factory=list)
    mastery_changes: List[MasteryChange] = Field(default_factory=list)
    nodes_examined: int = 0


class ExamRecordListResponse(BaseModel):
    """Paginated list of exam records.

    [Source: Story 6.8 AC-7]
    """

    records: List[ExamRecordSummary] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    limit: int = 20
