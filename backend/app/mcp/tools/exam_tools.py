# Canvas Learning System - MCP Exam Tools
# Story 3.2: MCP Tool Exposure (AC-2, AC-3)
#
# Tools: generate_question, score_answer, assemble_acp
# These tools provide Agent access to the examination and scoring pipeline.
#
# Pipeline token flow:
#   generate_question -> returns token_A
#   score_answer(token_A) -> returns token_B
#   update_fsrs/update_bkt(token_B) -> completes pipeline
#
# [Source: _bmad-output/implementation-artifacts/3-2-mcp-tool-exposure-backend-api.md#Task 2.3]

import asyncio
import logging
import uuid
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.audit.guardian import get_audit_guardian
from app.mcp.pipeline_token import (
    PipelineTokenError,
    get_pipeline_token_manager,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Pydantic Models
# ═══════════════════════════════════════════════════════════════════════════════


class GenerateQuestionInput(BaseModel):
    """Input schema for generate_question tool."""

    node_id: str = Field(..., description="The canvas node to generate a question for.")
    session_id: str = Field(..., description="The dialogue session identifier.")
    difficulty: Optional[str] = Field(
        None,
        description="Target difficulty level: 'easy', 'medium', 'hard'. "
        "If not provided, auto-selects based on mastery level.",
    )
    question_type: Optional[str] = Field(
        None,
        description="Question type: 'recall', 'comprehension', 'application', 'analysis'. "
        "If not provided, auto-selects based on learning stage.",
    )


class GenerateQuestionOutput(BaseModel):
    """Output schema for generate_question tool."""

    question_id: str = Field(..., description="Unique question identifier")
    question_text: str = Field(..., description="The generated question")
    question_type: str = Field(..., description="Question type")
    difficulty: str = Field(..., description="Question difficulty level")
    reference_answer: Optional[str] = Field(None, description="Reference answer for scoring")
    pipeline_token: str = Field(..., description="Pipeline token for the next step (score_answer)")
    status: str = "ok"
    message: str = ""


class ScoreAnswerInput(BaseModel):
    """Input schema for score_answer tool."""

    node_id: str = Field(..., description="The canvas node identifier.")
    session_id: str = Field(..., description="The dialogue session identifier.")
    question_id: str = Field(..., description="The question identifier from generate_question.")
    student_answer: str = Field(..., description="The student's answer text.")
    pipeline_token: str = Field(
        ...,
        description="Pipeline token from generate_question (required for step ordering).",
    )


class ScoreAnswerOutput(BaseModel):
    """Output schema for score_answer tool."""

    question_id: str
    score: float = Field(..., ge=0.0, le=1.0, description="Score from 0.0 to 1.0")
    grade: int = Field(..., ge=1, le=4, description="Grade: 1=Forgot, 2=Struggled, 3=Correct, 4=Fluent")
    feedback: str = Field(..., description="Detailed feedback for the student")
    is_correct: bool = Field(..., description="Whether the answer is considered correct")
    pipeline_token: str = Field(..., description="Pipeline token for the next step (update_fsrs/update_bkt)")
    status: str = "ok"
    message: str = ""


class AssembleAcpInput(BaseModel):
    """Input schema for assemble_acp tool."""

    node_id: str = Field(..., description="The canvas node identifier.")
    include_related: bool = Field(True, description="Whether to include related nodes' context.")


class AssembleAcpOutput(BaseModel):
    """Output schema for assemble_acp tool."""

    node_id: str
    concept_name: str = Field(..., description="The concept/topic name")
    concept_content: str = Field(..., description="The concept content text")
    related_concepts: List[str] = Field(default_factory=list, description="Related concept names")
    mastery_level: Optional[float] = Field(None, description="Current mastery level (0.0 - 1.0)")
    learning_history_summary: Optional[str] = Field(None, description="Brief summary of learning history")
    status: str = "ok"
    message: str = ""


# ═══════════════════════════════════════════════════════════════════════════════
# Tool Implementation Functions
# ═══════════════════════════════════════════════════════════════════════════════


async def generate_question(
    node_id: str,
    session_id: str,
    difficulty: Optional[str] = None,
    question_type: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate a question for a canvas node based on its content and mastery level.

    This is the entry point of the pipeline. Returns a pipeline_token (token_A)
    that must be passed to score_answer.

    Args:
        node_id: The canvas node to generate a question for.
        session_id: The dialogue session identifier.
        difficulty: Target difficulty level (optional, auto-selects if not provided).
        question_type: Question type (optional, auto-selects if not provided).

    Returns:
        Dict with question data and pipeline_token.
    """
    guardian = get_audit_guardian()
    asyncio.create_task(guardian.record_tool_call("generate_question", session_id, node_id))

    question_id = str(uuid.uuid4())
    token_mgr = get_pipeline_token_manager()

    try:
        # Get node content for question generation
        from app.services.canvas_service import CanvasService

        canvas_svc = CanvasService()
        node_data = await canvas_svc.get_node(node_id)

        if node_data is None:
            return GenerateQuestionOutput(
                question_id=question_id,
                question_text="",
                question_type=question_type or "recall",
                difficulty=difficulty or "medium",
                pipeline_token="",
                status="not_found",
                message=f"Node {node_id} not found",
            ).model_dump()

        # Get mastery data for difficulty matching
        mastery_data = None
        try:
            from app.api.v1.endpoints.mastery import _get_store

            store = _get_store()
            mastery_data = await store.get_concept(node_id)
        except (ImportError, Exception):
            pass

        # Auto-select difficulty based on mastery if not specified
        if difficulty is None:
            if mastery_data and hasattr(mastery_data, "p_mastery"):
                p = mastery_data.p_mastery
                if p < 0.3:
                    difficulty = "easy"
                elif p < 0.7:
                    difficulty = "medium"
                else:
                    difficulty = "hard"
            else:
                difficulty = "medium"

        if question_type is None:
            question_type = "comprehension"

        # Use the Agent/LLM service to generate the question
        node_title = node_data.get("text", node_data.get("title", "Unknown"))
        node_content = node_data.get("content", node_data.get("text", ""))

        try:
            from app.dependencies import get_agent_service

            agent_svc = await get_agent_service()
            # Use the agent's question generation capability
            question_result = await agent_svc.generate_question(
                concept=node_title,
                context=node_content,
                difficulty=difficulty,
                question_type=question_type,
            )
            q_text = question_result.get("question", "")
            ref_answer = question_result.get("reference_answer")
        except (ImportError, AttributeError):
            # Fallback: generate a basic question from the content
            q_text = f"Please explain the concept of '{node_title}' in your own words."
            ref_answer = None

        # Generate pipeline token
        pipeline_token = token_mgr.generate_token(
            step_name="generate_question",
            session_id=session_id,
            node_id=node_id,
            question_id=question_id,
        )

        return GenerateQuestionOutput(
            question_id=question_id,
            question_text=q_text,
            question_type=question_type,
            difficulty=difficulty,
            reference_answer=ref_answer,
            pipeline_token=pipeline_token,
            status="ok",
        ).model_dump()

    except Exception as e:
        logger.error(f"[Story 3.2] generate_question error: {e}")
        return GenerateQuestionOutput(
            question_id=question_id,
            question_text="",
            question_type=question_type or "recall",
            difficulty=difficulty or "medium",
            pipeline_token="",
            status="error",
            message=str(e),
        ).model_dump()


async def score_answer(
    node_id: str,
    session_id: str,
    question_id: str,
    student_answer: str,
    pipeline_token: str,
) -> Dict[str, Any]:
    """
    Score a student's answer using the AutoSCORE evaluation system.

    Requires pipeline_token from generate_question (AC-3: step ordering).
    Returns a new pipeline_token (token_B) for update_fsrs/update_bkt.

    Args:
        node_id: The canvas node identifier.
        session_id: The dialogue session identifier.
        question_id: The question identifier.
        student_answer: The student's answer text.
        pipeline_token: Token from generate_question.

    Returns:
        Dict with score, grade, feedback, and new pipeline_token.
    """
    guardian = get_audit_guardian()
    asyncio.create_task(guardian.record_tool_call("score_answer", session_id, node_id))

    # Validate pipeline token (AC-3)
    token_mgr = get_pipeline_token_manager()
    try:
        token_mgr.validate_token(pipeline_token, expected_previous_step="generate_question")
    except PipelineTokenError as e:
        return ScoreAnswerOutput(
            question_id=question_id,
            score=0.0,
            grade=1,
            feedback="",
            is_correct=False,
            pipeline_token="",
            status=e.code,
            message=e.message,
        ).model_dump()

    try:
        # Story 6.4: Use AutoSCORE two-stage evaluation
        from app.services.autoscore import get_auto_scorer

        scorer = get_auto_scorer()
        autoscore_result = await scorer.evaluate(
            exam_id=session_id,
            node_id=node_id,
            question_text="",  # Question text not stored in this flow
            conversation_segment=student_answer,
            question_id=question_id,
        )

        grade = autoscore_result.grade
        score = autoscore_result.overall_score / 12.0  # Normalize to 0-1
        feedback = autoscore_result.feedback_summary
        is_correct = grade >= 3

        # Story 6.4 AC-4: Emit SCORE_SUBMITTED event for BKT/FSRS update
        try:
            from app.models.canvas_events import LearningEvent, LearningEventType
            from app.services.event_bus import get_event_bus

            event_bus = get_event_bus()
            score_event = LearningEvent(
                event_type=LearningEventType.SCORE_SUBMITTED,
                payload={
                    "node_id": node_id,
                    "session_id": session_id,
                    "grade": grade,
                    "is_correct": is_correct,
                    "source": "autoscore",
                },
                source="autoscore",
            )
            await event_bus.publish(score_event)
        except Exception as evt_err:
            logger.warning(f"[Story 6.4] SCORE_SUBMITTED event failed: {evt_err}")

    except ImportError as e:
        # Fallback to AgentService if AutoScorer not available
        logger.info(f"[Story 6.4] AutoScorer not available, falling back to AgentService: {e}")
        try:
            from app.dependencies import get_agent_service

            agent_svc = await get_agent_service()
            score_result = await agent_svc.score_answer(
                question_id=question_id,
                student_answer=student_answer,
                node_id=node_id,
            )
            score = score_result.get("score", 0.0)
            feedback = score_result.get("feedback", "")
            if score >= 0.9:
                grade = 4
            elif score >= 0.6:
                grade = 3
            elif score >= 0.3:
                grade = 2
            else:
                grade = 1
            is_correct = grade >= 3
        except (ImportError, AttributeError) as fallback_err:
            logger.warning(f"[Story 3.2] score_answer: no scoring service available: {fallback_err}")
            return ScoreAnswerOutput(
                question_id=question_id,
                score=0.0,
                grade=1,
                feedback="Scoring service is not available",
                is_correct=False,
                pipeline_token="",
                status="service_unavailable",
                message=str(fallback_err),
            ).model_dump()
    except Exception as e:
        logger.error(f"[Story 6.4] score_answer error: {e}")
        return ScoreAnswerOutput(
            question_id=question_id,
            score=0.0,
            grade=1,
            feedback="",
            is_correct=False,
            pipeline_token="",
            status="error",
            message=str(e),
        ).model_dump()

    # Generate next pipeline token (token_B)
    next_token = token_mgr.generate_token(
        step_name="score_answer",
        session_id=session_id,
        node_id=node_id,
        question_id=question_id,
    )

    return ScoreAnswerOutput(
        question_id=question_id,
        score=score,
        grade=grade,
        feedback=feedback,
        is_correct=is_correct,
        pipeline_token=next_token,
        status="ok",
    ).model_dump()


async def assemble_acp(
    node_id: str,
    include_related: bool = True,
) -> Dict[str, Any]:
    """
    Assemble an ACP (Assessment Context Package) data bundle for a node.

    The ACP contains the concept content, related concepts, mastery level,
    and learning history — everything needed for question generation.

    This tool does not require a pipeline token.

    Args:
        node_id: The canvas node identifier.
        include_related: Whether to include related nodes' context.

    Returns:
        Dict with assembled ACP data.
    """
    guardian = get_audit_guardian()
    asyncio.create_task(guardian.record_tool_call("assemble_acp", "", node_id))

    try:
        from app.services.canvas_service import CanvasService

        canvas_svc = CanvasService()
        node_data = await canvas_svc.get_node(node_id)

        if node_data is None:
            return AssembleAcpOutput(
                node_id=node_id,
                concept_name="",
                concept_content="",
                status="not_found",
                message=f"Node {node_id} not found",
            ).model_dump()

        concept_name = node_data.get("text", node_data.get("title", "Unknown"))
        concept_content = node_data.get("content", node_data.get("text", ""))

        # Get related concepts
        related_concepts: List[str] = []
        if include_related:
            try:
                edges = await canvas_svc.get_edges_for_node(node_id)
                for edge in edges:
                    target_id = edge.get("toNode", edge.get("target_node_id", ""))
                    source_id = edge.get("fromNode", edge.get("source_node_id", ""))
                    related_id = target_id if target_id != node_id else source_id
                    if related_id:
                        related_node = await canvas_svc.get_node(related_id)
                        if related_node:
                            related_concepts.append(related_node.get("text", related_node.get("title", "")))
            except Exception as e:
                logger.debug(f"[Story 3.2] assemble_acp: failed to get related nodes: {e}")

        # Get mastery level
        mastery_level = None
        try:
            from app.api.v1.endpoints.mastery import _get_store

            store = _get_store()
            concept_state = await store.get_concept(node_id)
            if concept_state:
                mastery_level = concept_state.p_mastery
        except (ImportError, Exception):
            pass

        return AssembleAcpOutput(
            node_id=node_id,
            concept_name=concept_name,
            concept_content=concept_content,
            related_concepts=related_concepts,
            mastery_level=mastery_level,
            status="ok",
        ).model_dump()

    except ImportError as e:
        logger.warning(f"[Story 3.2] assemble_acp: service not available: {e}")
        return AssembleAcpOutput(
            node_id=node_id,
            concept_name="",
            concept_content="",
            status="service_unavailable",
            message=str(e),
        ).model_dump()
    except Exception as e:
        logger.error(f"[Story 3.2] assemble_acp error: {e}")
        return AssembleAcpOutput(
            node_id=node_id,
            concept_name="",
            concept_content="",
            status="error",
            message=str(e),
        ).model_dump()
