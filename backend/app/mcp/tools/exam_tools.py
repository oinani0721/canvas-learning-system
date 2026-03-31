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

# Note: asyncio.TimeoutError is used for narrowed exception handling in service calls
from pydantic import BaseModel, Field

from app.audit.guardian import get_audit_guardian
from app.mcp.pipeline_token import (
    PipelineTokenError,
    get_pipeline_token_manager,
)
from app.middleware.prompt_injection_guard import (
    SAFETY_BLOCK_INPUT_MESSAGE,
    check_input,
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
    # Story 6.3: Exam context for full ACP pipeline
    exam_id: Optional[str] = Field(
        None,
        description="Exam session ID. When provided, uses the full Story 6.3 FSRS+BKT+KG "
        "selection + ACP + 5-layer prompt pipeline instead of template-based generation.",
    )
    exam_mode: Optional[str] = Field(
        None,
        description="Exam mode: 'point_to_point', 'comprehensive', 'mixed'. Only used when exam_id is provided.",
    )
    source_canvas_id: Optional[str] = Field(
        None,
        description="Source canvas board ID for target node selection. Only used when exam_id is provided.",
    )


class GenerateQuestionOutput(BaseModel):
    """Output schema for generate_question tool."""

    question_id: str = Field(..., description="Unique question identifier")
    question_text: str = Field(..., description="The generated question")
    question_type: str = Field(..., description="Question type")
    difficulty: str = Field(..., description="Question difficulty level")
    reference_answer: Optional[str] = Field(
        None, description="Reference answer for scoring"
    )
    pipeline_token: str = Field(
        ..., description="Pipeline token for the next step (score_answer)"
    )
    status: str = "ok"
    message: str = ""


class ScoreAnswerInput(BaseModel):
    """Input schema for score_answer tool."""

    node_id: str = Field(..., description="The canvas node identifier.")
    session_id: str = Field(..., description="The dialogue session identifier.")
    question_id: str = Field(
        ..., description="The question identifier from generate_question."
    )
    student_answer: str = Field(..., description="The student's answer text.")
    pipeline_token: str = Field(
        ...,
        description="Pipeline token from generate_question (required for step ordering).",
    )


class ScoreAnswerOutput(BaseModel):
    """Output schema for score_answer tool."""

    question_id: str
    score: float = Field(..., ge=0.0, le=1.0, description="Score from 0.0 to 1.0")
    grade: int = Field(
        ..., ge=1, le=4, description="Grade: 1=Forgot, 2=Struggled, 3=Correct, 4=Fluent"
    )
    feedback: str = Field(..., description="Detailed feedback for the student")
    is_correct: bool = Field(
        ..., description="Whether the answer is considered correct"
    )
    pipeline_token: str = Field(
        ..., description="Pipeline token for the next step (update_fsrs/update_bkt)"
    )
    status: str = "ok"
    message: str = ""


class AssembleAcpInput(BaseModel):
    """Input schema for assemble_acp tool."""

    node_id: str = Field(..., description="The canvas node identifier.")
    include_related: bool = Field(
        True, description="Whether to include related nodes' context."
    )


class AssembleAcpOutput(BaseModel):
    """Output schema for assemble_acp tool."""

    node_id: str
    concept_name: str = Field(..., description="The concept/topic name")
    concept_content: str = Field(..., description="The concept content text")
    related_concepts: List[str] = Field(
        default_factory=list, description="Related concept names"
    )
    mastery_level: Optional[float] = Field(
        None, description="Current mastery level (0.0 - 1.0)"
    )
    learning_history_summary: Optional[str] = Field(
        None, description="Brief summary of learning history"
    )
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
    exam_id: Optional[str] = None,
    exam_mode: Optional[str] = None,
    source_canvas_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate a question for a canvas node based on its content and mastery level.

    When exam_id is provided, uses the full Story 6.3 pipeline:
    FSRS+BKT+KG target selection -> ACP assembly -> 5-layer prompt -> LLM.
    Otherwise falls back to template-based generation (Story 4.2).

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
    asyncio.create_task(
        guardian.record_tool_call("generate_question", session_id, node_id)
    )

    question_id = str(uuid.uuid4())
    token_mgr = get_pipeline_token_manager()

    try:
        # Story 6.3: When exam_id is provided, use the full ACP pipeline
        if exam_id and source_canvas_id:
            from app.models.exam_models import ExamMode
            from app.services.exam_service import get_exam_service
            from app.services.question_generator import QuestionGenerator

            generator = QuestionGenerator()
            mode = ExamMode(exam_mode) if exam_mode else ExamMode.MIXED

            # Get examined nodes from the exam session
            exam_svc = get_exam_service()
            session = await exam_svc.get_session(exam_id)
            examined = session.examined_nodes if session else list()

            result = await generator.generate_exam_question(
                exam_id=exam_id,
                source_canvas_id=source_canvas_id,
                exam_mode=mode,
                target_node_id=node_id if node_id else None,
                examined_nodes=examined,
            )

            # Record node as examined
            if session and result.target_node_id:
                await exam_svc.record_node_examined(exam_id, result.target_node_id)

            pipeline_token = token_mgr.generate_token(
                step_name="generate_question",
                session_id=session_id,
                node_id=result.target_node_id or node_id,
                question_id=question_id,
            )

            return GenerateQuestionOutput(
                question_id=question_id,
                question_text=result.question_text,
                question_type=result.question_type,
                difficulty=result.difficulty_level,
                pipeline_token=pipeline_token,
                status="ok",
            ).model_dump()

        # Legacy path: template-based generation (Story 4.2)
        # Get node content for question generation
        from app.config import settings
        from app.services.canvas_service import CanvasService

        canvas_svc = CanvasService(canvas_base_path=settings.canvas_base_path)
        canvas_name, node_data = await canvas_svc.find_node_across_canvases(node_id)

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
            from app.services.mastery_store import get_mastery_store

            store = get_mastery_store()
            mastery_data = await store.get_concept(node_id)
        except (RuntimeError, AttributeError, asyncio.TimeoutError) as e:
            logger.debug(
                f"[Story 3.2] Mastery data not available for difficulty selection: {e}"
            )

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

        # Use QuestionGenerator service to generate the question
        node_title = node_data.get("text", node_data.get("title", "Unknown"))

        try:
            from app.services.question_generator import QuestionGenerator

            generator = QuestionGenerator()
            proficiency = None
            if mastery_data and hasattr(mastery_data, "p_mastery"):
                proficiency = mastery_data.p_mastery
            questions = generator.generate_questions(
                node=node_data,
                effective_proficiency=proficiency,
            )
            q_text = (
                questions[0]
                if questions
                else f"Please explain the concept of '{node_title}' in your own words."
            )
            ref_answer = None
        except (RuntimeError, ValueError, AttributeError) as e:
            # Fallback: generate a basic question from the content
            logger.warning(f"[Story 3.2] QuestionGenerator failed, using fallback: {e}")
            q_text = f"Please explain the concept of '{node_title}' in your own words."
            ref_answer = None

        # Generate pipeline token
        pipeline_token = token_mgr.generate_token(
            step_name="generate_question",
            session_id=session_id,
            node_id=node_id,
            question_id=question_id,
        )

        # Story 6.10 AC-1: Fire-and-forget difficulty matching evaluation
        # Never blocks question delivery. Failure is silently logged.
        try:
            from app.services.difficulty_matcher import get_difficulty_matcher

            matcher = get_difficulty_matcher()
            effective_prof = 0.5  # Default proficiency
            if mastery_data and hasattr(mastery_data, "p_mastery"):
                effective_prof = mastery_data.p_mastery

            async def _evaluate_difficulty() -> None:
                try:
                    await matcher.evaluate(
                        node_id=node_id,
                        question=q_text,
                        proficiency=effective_prof,
                    )
                except (RuntimeError, ValueError, asyncio.TimeoutError) as diff_err:
                    logger.error(
                        f"[Story 6.10] Difficulty evaluation failed: {diff_err}"
                    )

            asyncio.create_task(_evaluate_difficulty())
        except (ImportError, AttributeError) as diff_setup_err:
            logger.debug(
                f"[Story 6.10] Difficulty matcher not available: {diff_setup_err}"
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

    # Story 3.13 AC-5: Input injection check on student answer
    injection_check = check_input(student_answer)
    if injection_check.is_blocked:
        logger.warning(
            f"[Story 3.13] score_answer input blocked: "
            f"risk_score={injection_check.risk_score}, "
            f"patterns={injection_check.matched_patterns}"
        )
        return ScoreAnswerOutput(
            question_id=question_id,
            score=0.0,
            grade=1,
            feedback=SAFETY_BLOCK_INPUT_MESSAGE,
            is_correct=False,
            pipeline_token="",
            status="safety_blocked",
            message="Input blocked by injection detection",
        ).model_dump()

    # Validate pipeline token (AC-3)
    token_mgr = get_pipeline_token_manager()
    try:
        token_mgr.validate_token(
            pipeline_token, expected_previous_step="generate_question"
        )
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

        # Story 3.2 fix: Retrieve question text from node content for scoring context.
        # The pipeline token contains question_id but not question_text.
        # Fetch concept content from canvas as scoring context.
        question_context = ""
        try:
            from app.config import settings as app_settings
            from app.services.canvas_service import CanvasService

            ctx_canvas_svc = CanvasService(
                canvas_base_path=app_settings.canvas_base_path
            )
            _, ctx_node_data = await ctx_canvas_svc.find_node_across_canvases(node_id)
            if ctx_node_data:
                question_context = ctx_node_data.get(
                    "text", ctx_node_data.get("content", "")
                )
        except (OSError, ValueError, AttributeError) as ctx_err:
            logger.debug(
                f"[Story 3.2] Failed to get question context for scoring: {ctx_err}"
            )

        autoscore_result = await scorer.evaluate(
            exam_id=session_id,
            node_id=node_id,
            question_text=question_context,
            conversation_segment=student_answer,
            question_id=question_id,
        )

        grade = autoscore_result.grade
        score = autoscore_result.overall_score / 12.0  # Normalize to 0-1
        feedback = autoscore_result.feedback_summary
        is_correct = grade >= 3

        # Story 6.9 AC-4: Faithfulness gate — only emit SCORE_SUBMITTED if verified
        # If faithfulness_passed is False or overall low confidence, don't update mastery.
        faithfulness_passed = getattr(autoscore_result, "faithfulness_passed", True)

        if faithfulness_passed:
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
            except (RuntimeError, AttributeError, asyncio.TimeoutError) as evt_err:
                logger.warning(f"[Story 6.4] SCORE_SUBMITTED event failed: {evt_err}")
        else:
            # Story 6.9 AC-4: Low faithfulness — record but don't update mastery
            logger.warning(
                f"[Story 6.9] SCORE_SUBMITTED suppressed for node={node_id}: "
                f"faithfulness_passed=False (score={getattr(autoscore_result, 'faithfulness_score', 'N/A')})"
            )

    except ImportError as e:
        logger.warning(f"[Story 3.2] score_answer: AutoScorer not available: {e}")
        return ScoreAnswerOutput(
            question_id=question_id,
            score=0.0,
            grade=1,
            feedback="Scoring service is not available",
            is_correct=False,
            pipeline_token="",
            status="service_unavailable",
            message=str(e),
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
        from app.config import settings
        from app.services.canvas_service import CanvasService

        canvas_svc = CanvasService(canvas_base_path=settings.canvas_base_path)
        canvas_name, node_data = await canvas_svc.find_node_across_canvases(node_id)

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

        # Get related concepts — batch fetch to avoid N+1 queries
        related_concepts: List[str] = []
        if include_related:
            try:
                edges = await canvas_svc.find_edges_for_node(
                    node_id, canvas_name=canvas_name
                )
                # Collect all related node IDs first
                related_ids: List[str] = []
                for edge in edges:
                    target_id = edge.get("toNode", "")
                    source_id = edge.get("fromNode", "")
                    related_id = target_id if target_id != node_id else source_id
                    if related_id and related_id not in related_ids:
                        related_ids.append(related_id)

                # Batch fetch: try to get all nodes from the same canvas first
                if related_ids and canvas_name:
                    try:
                        canvas_data = await canvas_svc.read_canvas(canvas_name)
                        nodes_by_id = {
                            n.get("id"): n for n in canvas_data.get("nodes", [])
                        }
                        for rid in related_ids:
                            node_found = nodes_by_id.get(rid)
                            if node_found:
                                related_concepts.append(
                                    node_found.get("text", node_found.get("title", ""))
                                )
                            # Skip cross-canvas lookup to avoid N+1
                    except (OSError, ValueError, KeyError) as batch_err:
                        logger.debug(
                            f"[Story 3.2] assemble_acp batch fetch failed: {batch_err}"
                        )
                        # Fallback: individual lookups for remaining
                        for rid in related_ids:
                            if len(related_concepts) >= 10:
                                break
                            try:
                                (
                                    _,
                                    related_node,
                                ) = await canvas_svc.find_node_across_canvases(rid)
                                if related_node:
                                    related_concepts.append(
                                        related_node.get(
                                            "text", related_node.get("title", "")
                                        )
                                    )
                            except (OSError, ValueError):
                                pass
            except (RuntimeError, AttributeError, OSError) as e:
                logger.debug(
                    f"[Story 3.2] assemble_acp: failed to get related nodes: {e}"
                )

        # Get mastery level
        mastery_level = None
        try:
            from app.services.mastery_store import get_mastery_store

            store = get_mastery_store()
            concept_state = await store.get_concept(node_id)
            if concept_state:
                mastery_level = concept_state.p_mastery
        except (ImportError, RuntimeError, AttributeError, asyncio.TimeoutError):
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
