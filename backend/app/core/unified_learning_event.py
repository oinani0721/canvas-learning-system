# Canvas Learning System - Unified Learning Event Data Model
# Closed-loop Technical Design: Cross-pipeline data model unification
#
# Ensures consistent data format across all three pipelines:
#   - Write path: Canvas plugin -> MemoryService -> GraphitiBridge -> Neo4j
#   - Read path:  LearningContextService -> Tier1/Tier2 -> ACP -> Prompt
#   - Feedback path: ExamScoring -> AnswerQuality -> AgentSelector -> Memory
#
# Design decisions:
#   - Bloom 4-category knowledge_type (Factual/Conceptual/Procedural/Metacognitive)
#     replaces the old 5-category weakness classification
#   - Multi-label tags replace single-label classification
#   - Severity is a 0.0-1.0 float aligned with FSRS grade mapping
#   - episode_body uses structured JSON for machine readability
#   - Backward compatible with existing ENTITY_TYPES in memory_format.py
#
# References:
#   - Anderson & Krathwohl (2001) Revised Bloom Taxonomy knowledge dimension
#   - memory_format.py ENTITY_TYPES (existing 10 entity types)
#   - agent_selector.py AnswerQuality (8 enum values)
#   - entity_types.py ErrorType (4 error categories)
#   - exam_models.py ACPData (ACP data package)
#   - canvas_events.py LearningEventType (EventBus 8 event types)

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# =============================================================================
# Bloom 4-Category Knowledge Type
# =============================================================================
# Anderson & Krathwohl (2001) Revised Bloom Taxonomy — Knowledge Dimension
# Replaces the old ad-hoc 5-category weakness classification with a
# pedagogically grounded, internationally recognized taxonomy.


class KnowledgeType(str, Enum):
    """Bloom Revised Taxonomy — Knowledge Dimension (4 categories).

    Each learning event is tagged with the type of knowledge involved.
    Multi-label is supported via LearningEvent.tags for cross-category items.

    Mapping from old ErrorType (entity_types.py):
      - PROBLEM_FRAMING  -> PROCEDURAL  (procedural error in problem approach)
      - REASONING_FALLACY -> CONCEPTUAL (flawed conceptual reasoning)
      - KNOWLEDGE_GAP    -> FACTUAL     (missing factual knowledge)
      - SUPERFICIAL      -> METACOGNITIVE (inability to self-monitor understanding)
    """

    FACTUAL = "factual"
    """Factual knowledge: terminology, specific details, elements.
    E.g., definitions, formulas, dates, vocabulary.
    Old mapping: KNOWLEDGE_GAP (knowledge_gap)."""

    CONCEPTUAL = "conceptual"
    """Conceptual knowledge: classifications, principles, theories, models.
    E.g., understanding relationships between concepts, cause-and-effect.
    Old mapping: REASONING_FALLACY (reasoning_fallacy)."""

    PROCEDURAL = "procedural"
    """Procedural knowledge: techniques, methods, algorithms, criteria.
    E.g., how to solve a type of problem, step-by-step procedures.
    Old mapping: PROBLEM_FRAMING (problem_framing)."""

    METACOGNITIVE = "metacognitive"
    """Metacognitive knowledge: self-knowledge, strategic knowledge, cognitive tasks.
    E.g., knowing when to apply which strategy, self-assessment accuracy.
    Old mapping: SUPERFICIAL (superficial)."""


# =============================================================================
# Unified Event Type
# =============================================================================


class UnifiedEventType(str, Enum):
    """Unified event types spanning all three pipelines.

    Consolidates:
      - memory_format.py ENTITY_TYPES (write path)
      - canvas_events.py LearningEventType (EventBus)
      - agent_selector.py AnswerQuality (feedback path)

    Grouped by pipeline phase:
      WRITE_*   : Events from the write path (canvas interaction -> memory)
      SCORE_*   : Events from the feedback path (exam scoring -> model update)
      REVIEW_*  : Events from the read path (context retrieval -> prompt)
    """

    # --- Write path events ---
    MISCONCEPTION_DETECTED = "misconception_detected"
    PROBLEM_TRAP_DETECTED = "problem_trap_detected"
    LOGICAL_FALLACY_DETECTED = "logical_fallacy_detected"
    GUIDED_THINKING_COMPLETED = "guided_thinking_completed"
    TIP_ANNOTATED = "tip_annotated"
    CONCEPT_RECORDED = "concept_recorded"
    COLOR_TRANSITION = "color_transition"
    SELF_ASSESSMENT = "self_assessment"

    # --- Feedback path events ---
    SCORE_SUBMITTED = "score_submitted"
    MASTERY_UPDATED = "mastery_updated"
    CALIBRATION_RECORDED = "calibration_recorded"

    # --- Read/review path events ---
    REVIEW_SCHEDULED = "review_scheduled"
    CONTEXT_ASSEMBLED = "context_assembled"


# =============================================================================
# Severity Level
# =============================================================================
# Aligned with FSRS grade mapping:
#   grade 1 (Again/Forgot)   -> severity 1.0 (critical)
#   grade 2 (Hard/Struggled) -> severity 0.7
#   grade 3 (Good/Correct)   -> severity 0.3
#   grade 4 (Easy/Fluent)    -> severity 0.0 (no issue)
#
# Also aligned with AnswerQuality:
#   NO_IDEA/SKIPPED    -> 1.0
#   WRONG              -> 0.85
#   CONFUSED           -> 0.7
#   REASONING_ERROR    -> 0.6
#   PARTIAL            -> 0.4
#   GOOD               -> 0.15
#   EXCELLENT          -> 0.0

ANSWER_QUALITY_TO_SEVERITY: Dict[str, float] = {
    "no_idea": 1.0,
    "skipped": 1.0,
    "wrong": 0.85,
    "confused": 0.7,
    "reasoning_error": 0.6,
    "partial": 0.4,
    "good": 0.15,
    "excellent": 0.0,
}

FSRS_GRADE_TO_SEVERITY: Dict[int, float] = {
    1: 1.0,  # Again/Forgot
    2: 0.7,  # Hard/Struggled
    3: 0.3,  # Good/Correct
    4: 0.0,  # Easy/Fluent
}


# =============================================================================
# Unified Learning Event
# =============================================================================


class LearningEventContext(BaseModel):
    """Contextual information for a learning event.

    Captures the environment and provenance of the event,
    enabling downstream services to understand the full picture.
    """

    session_id: str = Field(default="", description="Dialogue/exam session ID")
    canvas_path: str = Field(default="", description="Source canvas file path")
    group_id: str = Field(
        default="", description="Subject isolation namespace (e.g., math-高一)"
    )
    source: str = Field(
        default="",
        description="Originator: 'canvas_plugin', 'exam_pipeline', 'react_agent', 'mcp_tool'",
    )
    question_id: str = Field(default="", description="Exam question ID if from scoring")
    exam_id: str = Field(
        default="", description="Exam session ID if from exam pipeline"
    )
    student_answer: str = Field(
        default="", description="Student's original answer text"
    )
    reference_answer: str = Field(default="", description="Reference/correct answer")
    agent_feedback: str = Field(default="", description="Agent's feedback text")
    conversation_summary: str = Field(
        default="", description="Distilled conversation summary"
    )
    related_node_ids: List[str] = Field(
        default_factory=list,
        description="IDs of related/connected nodes for graph context",
    )
    extra: Dict[str, Any] = Field(
        default_factory=dict,
        description="Extension point for pipeline-specific metadata",
    )


class LearningEvent(BaseModel):
    """Unified learning event data model for cross-pipeline consistency.

    This is the canonical format for all learning events in the system.
    Every write path, read path, and feedback path event is normalized
    to this format before storage or query.

    Fields:
        event_id: UUID, auto-generated for deduplication
        node_id: Canvas node ID this event relates to
        event_type: What happened (UnifiedEventType)
        knowledge_type: Bloom 4-category classification
        severity: 0.0 (no issue) to 1.0 (critical gap)
        tags: Multi-label tags for flexible classification
        content: Human-readable description of the event
        context: Structured context information
        created_at: ISO timestamp
        schema_version: For forward-compatible migration
    """

    event_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique event ID for idempotent deduplication",
    )
    node_id: str = Field(
        ...,
        description="Canvas node ID this event relates to",
    )
    event_type: UnifiedEventType = Field(
        ...,
        description="Type of learning event",
    )
    knowledge_type: KnowledgeType = Field(
        default=KnowledgeType.CONCEPTUAL,
        description="Bloom 4-category knowledge dimension",
    )
    severity: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Severity: 0.0 = no issue, 1.0 = critical gap",
    )
    tags: List[str] = Field(
        default_factory=list,
        description=(
            "Multi-label tags for flexible classification. "
            "Examples: ['misconception', 'reasoning', 'high_priority', 'needs_review']"
        ),
    )
    content: str = Field(
        default="",
        description="Human-readable description of the event",
    )
    context: LearningEventContext = Field(
        default_factory=LearningEventContext,
        description="Structured context/provenance information",
    )
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 timestamp",
    )
    schema_version: int = Field(
        default=1,
        description="Schema version for forward-compatible migration",
    )

    # -------------------------------------------------------------------------
    # Derived properties
    # -------------------------------------------------------------------------

    @property
    def is_negative(self) -> bool:
        """Whether this event indicates a learning difficulty."""
        return self.severity >= 0.4

    @property
    def priority_score(self) -> float:
        """Priority for review scheduling: higher = more urgent.

        Combines severity with recency decay (not implemented here;
        the caller should apply time decay on top of this base score).
        """
        return self.severity


# =============================================================================
# Graphiti Storage Format
# =============================================================================


class GraphitiEpisodePayload(BaseModel):
    """Structured JSON payload for Graphiti episode_body.

    Replaces the old text-template approach in memory_format.py with
    machine-parseable JSON. The episode_body stored in Neo4j will be
    json.dumps(GraphitiEpisodePayload.model_dump()).

    This format is designed for:
      1. Machine readability by downstream services (ACP assembly, context retrieval)
      2. Human readability when browsing Neo4j directly
      3. Forward compatibility via schema_version field
    """

    schema_version: int = Field(default=1, description="Payload schema version")
    event_type: str = Field(..., description="UnifiedEventType value")
    knowledge_type: str = Field(..., description="KnowledgeType value")
    severity: float = Field(..., ge=0.0, le=1.0)
    tags: List[str] = Field(default_factory=list)
    content: str = Field(default="")
    node_id: str = Field(default="")
    session_id: str = Field(default="")
    source: str = Field(default="")
    timestamp: str = Field(default="")

    # Optional enrichment fields (populated by specific pipelines)
    error_description: str = Field(default="", description="For misconception events")
    correct_understanding: str = Field(
        default="", description="For misconception events"
    )
    student_answer: str = Field(default="", description="For scoring events")
    score: Optional[float] = Field(
        default=None, description="For scoring events (0.0-1.0)"
    )
    grade: Optional[int] = Field(default=None, description="FSRS grade 1-4")


def learning_event_to_graphiti_payload(event: LearningEvent) -> GraphitiEpisodePayload:
    """Convert a LearningEvent to Graphiti storage payload."""
    return GraphitiEpisodePayload(
        schema_version=event.schema_version,
        event_type=event.event_type.value,
        knowledge_type=event.knowledge_type.value,
        severity=event.severity,
        tags=event.tags,
        content=event.content,
        node_id=event.node_id,
        session_id=event.context.session_id,
        source=event.context.source,
        timestamp=event.created_at,
        student_answer=event.context.student_answer,
    )


# =============================================================================
# Graphiti Entity Naming Convention
# =============================================================================
# Entity name format: "{KnowledgeType}:{EventType}:{concept_name}"
# Example: "conceptual:misconception_detected:逆否命题"
#
# This replaces the old ENTITY_TYPES prefix approach while remaining
# searchable via Graphiti's search_nodes.

GRAPHITI_SOURCE_DESCRIPTION = "unified-learning-event"


def build_unified_entity_name(
    knowledge_type: KnowledgeType,
    event_type: UnifiedEventType,
    concept: str,
) -> str:
    """Build standardized Graphiti entity name.

    Format: "{knowledge_type}:{event_type_short}:{concept}"
    Examples:
      - "conceptual:misconception:逆否命题"
      - "procedural:score:二次方程求解"
    """
    # Shorten event_type for readability
    short_type = event_type.value.replace("_detected", "").replace("_completed", "")
    return f"{knowledge_type.value}:{short_type}:{concept}"


# =============================================================================
# Mapping: Old Entity Types -> Unified Model
# =============================================================================
# Backward compatibility layer for migrating existing records.

ENTITY_TYPE_TO_UNIFIED: Dict[str, Dict[str, Any]] = {
    "Misconception": {
        "event_type": UnifiedEventType.MISCONCEPTION_DETECTED,
        "knowledge_type": KnowledgeType.CONCEPTUAL,
        "default_severity": 0.8,
        "default_tags": ["misconception", "needs_review"],
    },
    "ProblemTrap": {
        "event_type": UnifiedEventType.PROBLEM_TRAP_DETECTED,
        "knowledge_type": KnowledgeType.PROCEDURAL,
        "default_severity": 0.7,
        "default_tags": ["problem_trap", "needs_practice"],
    },
    "LogicalFallacy": {
        "event_type": UnifiedEventType.LOGICAL_FALLACY_DETECTED,
        "knowledge_type": KnowledgeType.CONCEPTUAL,
        "default_severity": 0.75,
        "default_tags": ["logical_fallacy", "reasoning"],
    },
    "GuidedThinking": {
        "event_type": UnifiedEventType.GUIDED_THINKING_COMPLETED,
        "knowledge_type": KnowledgeType.METACOGNITIVE,
        "default_severity": 0.5,
        "default_tags": ["guided_thinking"],
    },
    "Concept": {
        "event_type": UnifiedEventType.CONCEPT_RECORDED,
        "knowledge_type": KnowledgeType.FACTUAL,
        "default_severity": 0.0,
        "default_tags": ["concept"],
    },
    "MasteryUpdate": {
        "event_type": UnifiedEventType.MASTERY_UPDATED,
        "knowledge_type": KnowledgeType.CONCEPTUAL,
        "default_severity": 0.3,
        "default_tags": ["mastery_update"],
    },
    "SelfAssessment": {
        "event_type": UnifiedEventType.SELF_ASSESSMENT,
        "knowledge_type": KnowledgeType.METACOGNITIVE,
        "default_severity": 0.4,
        "default_tags": ["self_assessment"],
    },
    "ColorTransition": {
        "event_type": UnifiedEventType.COLOR_TRANSITION,
        "knowledge_type": KnowledgeType.METACOGNITIVE,
        "default_severity": 0.3,
        "default_tags": ["color_transition"],
    },
}


# =============================================================================
# Mapping: ErrorType (entity_types.py) -> KnowledgeType
# =============================================================================
# Used by ErrorClassifier to tag classified errors with Bloom dimension.

ERROR_TYPE_TO_KNOWLEDGE_TYPE: Dict[str, KnowledgeType] = {
    "problem_framing": KnowledgeType.PROCEDURAL,
    "reasoning_fallacy": KnowledgeType.CONCEPTUAL,
    "knowledge_gap": KnowledgeType.FACTUAL,
    "superficial": KnowledgeType.METACOGNITIVE,
}


# =============================================================================
# Mapping: AnswerQuality -> Unified Event Properties
# =============================================================================
# Used by the feedback path to convert exam scoring results.

ANSWER_QUALITY_TO_EVENT_PROPERTIES: Dict[str, Dict[str, Any]] = {
    "excellent": {
        "default_tags": ["mastery_confirmed"],
        "severity": 0.0,
    },
    "good": {
        "default_tags": ["mostly_correct"],
        "severity": 0.15,
    },
    "partial": {
        "default_tags": ["partial_understanding", "needs_review"],
        "severity": 0.4,
    },
    "wrong": {
        "default_tags": ["incorrect", "needs_review"],
        "severity": 0.85,
    },
    "confused": {
        "default_tags": ["concept_confusion", "needs_clarification"],
        "severity": 0.7,
    },
    "no_idea": {
        "default_tags": ["no_understanding", "needs_reteaching"],
        "severity": 1.0,
    },
    "reasoning_error": {
        "default_tags": ["reasoning_error", "needs_practice"],
        "severity": 0.6,
    },
    "skipped": {
        "default_tags": ["skipped"],
        "severity": 1.0,
    },
}


# =============================================================================
# Cross-Pipeline Query Interface
# =============================================================================


class LearningEventQuery(BaseModel):
    """Unified query parameters for cross-pipeline event retrieval.

    Supports filtering by node, event type, knowledge type, time range,
    severity threshold, and tags. Results are returned in a format
    compatible with the ACP data package assembly.
    """

    node_id: Optional[str] = Field(
        default=None,
        description="Filter by specific canvas node ID",
    )
    node_ids: List[str] = Field(
        default_factory=list,
        description="Filter by multiple node IDs (OR logic)",
    )
    event_types: List[UnifiedEventType] = Field(
        default_factory=list,
        description="Filter by event types (OR logic). Empty = all types.",
    )
    knowledge_types: List[KnowledgeType] = Field(
        default_factory=list,
        description="Filter by knowledge types (OR logic). Empty = all types.",
    )
    min_severity: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Minimum severity threshold (inclusive)",
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Filter by tags (AND logic: event must have ALL listed tags)",
    )
    time_from: Optional[str] = Field(
        default=None,
        description="ISO 8601 timestamp — events on or after this time",
    )
    time_to: Optional[str] = Field(
        default=None,
        description="ISO 8601 timestamp — events on or before this time",
    )
    group_id: Optional[str] = Field(
        default=None,
        description="Subject isolation namespace",
    )
    limit: int = Field(
        default=50,
        ge=1,
        le=200,
        description="Maximum number of results",
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Pagination offset",
    )


class LearningEventResult(BaseModel):
    """Single result item from a cross-pipeline query.

    Aligned with ACPData format for seamless ACP assembly:
      - error_history maps from events with is_negative=True
      - student_tips maps from TIP_ANNOTATED events
      - mastery_level maps from MASTERY_UPDATED events
    """

    event: LearningEvent
    relevance_score: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Search relevance (1.0 for exact match queries)",
    )


class LearningEventQueryResponse(BaseModel):
    """Response for cross-pipeline event queries."""

    items: List[LearningEventResult] = Field(default_factory=list)
    total_count: int = Field(
        default=0, description="Total matching events (before pagination)"
    )
    query: LearningEventQuery = Field(
        default_factory=LearningEventQuery,
        description="Echo of the query parameters",
    )


# =============================================================================
# ACP Bridging: LearningEvent -> ACPData fields
# =============================================================================


def events_to_acp_error_history(events: List[LearningEvent]) -> List[Dict[str, str]]:
    """Convert negative LearningEvents to ACP error_history format.

    ACPData.error_history is List[Dict[str, str]] with keys:
      - error_type: string classification
      - description: human-readable description

    This bridges the unified model to the existing ACP assembly pipeline.
    """
    history: List[Dict[str, str]] = []
    for e in events:
        if not e.is_negative:
            continue
        history.append(
            {
                "error_type": e.knowledge_type.value,
                "description": e.content,
                "severity": str(e.severity),
                "event_type": e.event_type.value,
                "timestamp": e.created_at,
            }
        )
    return history


def events_to_acp_tips(events: List[LearningEvent]) -> List[str]:
    """Convert TIP_ANNOTATED events to ACP student_tips format.

    ACPData.student_tips is List[str].
    """
    return [
        e.content
        for e in events
        if e.event_type == UnifiedEventType.TIP_ANNOTATED and e.content
    ]


# =============================================================================
# Factory Functions: Create LearningEvents from existing pipeline data
# =============================================================================


def from_score_result(
    node_id: str,
    score: float,
    grade: int,
    answer_quality: str,
    question_id: str = "",
    exam_id: str = "",
    session_id: str = "",
    content: str = "",
    student_answer: str = "",
    group_id: str = "",
) -> LearningEvent:
    """Create a LearningEvent from exam scoring result.

    Maps AnswerQuality -> severity and tags via ANSWER_QUALITY_TO_EVENT_PROPERTIES.
    Maps FSRS grade -> severity via FSRS_GRADE_TO_SEVERITY.

    The final severity is the max of both mappings to capture the worst signal.
    """
    aq_props = ANSWER_QUALITY_TO_EVENT_PROPERTIES.get(
        answer_quality, {"default_tags": [], "severity": 0.5}
    )
    fsrs_severity = FSRS_GRADE_TO_SEVERITY.get(grade, 0.5)

    severity = max(aq_props["severity"], fsrs_severity)
    tags = list(aq_props["default_tags"])

    return LearningEvent(
        node_id=node_id,
        event_type=UnifiedEventType.SCORE_SUBMITTED,
        knowledge_type=KnowledgeType.CONCEPTUAL,  # Refined by caller if known
        severity=severity,
        tags=tags,
        content=content
        or f"Score: {score:.2f}, Grade: {grade}, Quality: {answer_quality}",
        context=LearningEventContext(
            session_id=session_id,
            group_id=group_id,
            source="exam_pipeline",
            question_id=question_id,
            exam_id=exam_id,
            student_answer=student_answer,
        ),
    )


def from_error_classification(
    node_id: str,
    error_type: str,
    description: str,
    context_text: str = "",
    session_id: str = "",
    group_id: str = "",
) -> LearningEvent:
    """Create a LearningEvent from ErrorClassifier result.

    Maps ErrorType -> KnowledgeType via ERROR_TYPE_TO_KNOWLEDGE_TYPE.
    """
    knowledge_type = ERROR_TYPE_TO_KNOWLEDGE_TYPE.get(
        error_type, KnowledgeType.CONCEPTUAL
    )

    # Map error types to unified event types
    event_type_map = {
        "problem_framing": UnifiedEventType.PROBLEM_TRAP_DETECTED,
        "reasoning_fallacy": UnifiedEventType.LOGICAL_FALLACY_DETECTED,
        "knowledge_gap": UnifiedEventType.MISCONCEPTION_DETECTED,
        "superficial": UnifiedEventType.MISCONCEPTION_DETECTED,
    }
    event_type = event_type_map.get(error_type, UnifiedEventType.MISCONCEPTION_DETECTED)

    return LearningEvent(
        node_id=node_id,
        event_type=event_type,
        knowledge_type=knowledge_type,
        severity=0.75,
        tags=[error_type, "error_classified", "needs_review"],
        content=description,
        context=LearningEventContext(
            session_id=session_id,
            group_id=group_id,
            source="error_classifier",
            agent_feedback=context_text,
        ),
    )


def from_legacy_entity_type(
    entity_type: str,
    node_id: str,
    concept: str,
    content: str = "",
    session_id: str = "",
    group_id: str = "",
    color: str = "",
    score: Optional[float] = None,
) -> LearningEvent:
    """Create a LearningEvent from legacy memory_format.py ENTITY_TYPES.

    Used for backward-compatible migration of existing records.
    """
    mapping = ENTITY_TYPE_TO_UNIFIED.get(entity_type, {})

    event_type = mapping.get("event_type", UnifiedEventType.CONCEPT_RECORDED)
    knowledge_type = mapping.get("knowledge_type", KnowledgeType.CONCEPTUAL)
    default_severity = mapping.get("default_severity", 0.5)
    tags = list(mapping.get("default_tags", []))

    # Adjust severity based on color if available
    if color == "4":  # Red = critical gap
        default_severity = max(default_severity, 0.9)
        tags.append("red_node")
    elif color == "3":  # Purple = partial understanding
        default_severity = max(default_severity, 0.6)
        tags.append("purple_node")
    elif color == "2":  # Green = mastered
        default_severity = min(default_severity, 0.1)
        tags.append("green_node")

    return LearningEvent(
        node_id=node_id,
        event_type=event_type,
        knowledge_type=knowledge_type,
        severity=default_severity,
        tags=tags,
        content=content or f"{entity_type}: {concept}",
        context=LearningEventContext(
            session_id=session_id,
            group_id=group_id,
            source="canvas_plugin",
            extra={"legacy_entity_type": entity_type, "color": color},
        ),
    )


def from_tip_annotation(
    node_id: str,
    tip_content: str,
    tip_title: str = "",
    tags: Optional[List[str]] = None,
    session_id: str = "",
    group_id: str = "",
) -> LearningEvent:
    """Create a LearningEvent from a user tip annotation."""
    return LearningEvent(
        node_id=node_id,
        event_type=UnifiedEventType.TIP_ANNOTATED,
        knowledge_type=KnowledgeType.FACTUAL,  # Tips are usually factual
        severity=0.0,  # Tips are positive signals
        tags=tags or ["tip", "user_annotated"],
        content=f"{tip_title}: {tip_content}" if tip_title else tip_content,
        context=LearningEventContext(
            session_id=session_id,
            group_id=group_id,
            source="canvas_plugin",
        ),
    )


# =============================================================================
# Migration Helper
# =============================================================================


def parse_legacy_episode_body(episode_body: str, entity_type: str) -> Dict[str, str]:
    """Parse old template-based episode_body into structured fields.

    Old format example:
      "[Topic: 逆否命题] 误解内容: X | 正确理解: Y | 来源: Z"

    Returns dict with extracted fields (best-effort parsing).
    """
    result: Dict[str, str] = {}

    # Extract [Topic: X] pattern
    import re

    topic_match = re.search(r"\[Topic:\s*(.+?)\]", episode_body)
    if topic_match:
        result["topic"] = topic_match.group(1).strip()

    # Extract pipe-separated key-value pairs
    # Remove brackets first
    clean = re.sub(r"\[.*?\]", "", episode_body).strip()
    parts = [p.strip() for p in clean.split("|") if p.strip()]
    for part in parts:
        if ":" in part:
            key, _, value = part.partition(":")
            result[key.strip()] = value.strip()

    return result


def is_unified_format(episode_body: str) -> bool:
    """Check if an episode_body is in the new JSON format (schema_version present)."""
    if not episode_body or not episode_body.strip().startswith("{"):
        return False
    try:
        import json

        data = json.loads(episode_body)
        return "schema_version" in data
    except (json.JSONDecodeError, TypeError):
        return False
