# Canvas Learning System - MCP Mastery Tools
# Story 3.2: MCP Tool Exposure (AC-2)
#
# Tools: query_mastery, update_fsrs, update_bkt
# These tools provide Agent access to the BKT+FSRS mastery tracking system.
#
# [Source: _bmad-output/implementation-artifacts/3-2-mcp-tool-exposure-backend-api.md#Task 2.2]
# [Source: architecture.md#MCP-tool-naming — snake_case convention]

import asyncio
import logging
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from app.audit.guardian import get_audit_guardian
from app.mcp.pipeline_token import (
    PipelineTokenError,
    get_pipeline_token_manager,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Pydantic Models (JSON Schema for MCP tool parameters)
# ═══════════════════════════════════════════════════════════════════════════════


class QueryMasteryInput(BaseModel):
    """Input schema for query_mastery tool."""

    node_id: str = Field(
        ...,
        description="The canvas node identifier to query mastery for.",
    )


class QueryMasteryOutput(BaseModel):
    """Output schema for query_mastery tool.

    A10 Phase 0 Hardening #2: ``mastery_degraded`` mirrors the cross-layer
    observability pattern established on ``NodePriority`` and ``ACPData``.
    Possible values:

    - ``None``: mastery values came from the fusion happy path
    - ``"concept_not_found"``: ``mastery_store.get_concept`` returned None
    - ``"exception"``: mastery lookup raised a non-fatal error
    - ``"fusion_fallback"``: the engine fell through to ``min(p_mastery, R)``
      (either because no fusion engine is attached, or because
      ``compute_fused_mastery`` returned ``active_signal_count == 0``)
    """

    node_id: str
    p_mastery: Optional[float] = Field(
        None, description="BKT mastery probability (0.0 - 1.0)"
    )
    fsrs_stability: Optional[float] = Field(
        None, description="FSRS stability parameter"
    )
    fsrs_difficulty: Optional[float] = Field(
        None, description="FSRS difficulty parameter"
    )
    fsrs_retrievability: Optional[float] = Field(
        None, description="FSRS retrievability R (0.0 - 1.0)"
    )
    effective_proficiency: Optional[float] = Field(
        None, description="Combined effective proficiency (0.0 - 1.0)"
    )
    interaction_count: int = Field(0, description="Total interaction count")
    last_interaction_ts: Optional[str] = Field(
        None, description="Last interaction timestamp (ISO 8601)"
    )
    status: str = Field("ok", description="Query status")
    mastery_degraded: Optional[str] = Field(
        None,
        description=(
            "Cross-layer observability marker. None on happy path; "
            "'concept_not_found' / 'exception' / 'fusion_fallback' otherwise."
        ),
    )


class UpdateFsrsInput(BaseModel):
    """Input schema for update_fsrs tool."""

    node_id: str = Field(..., description="The canvas node identifier.")
    grade: int = Field(
        ...,
        ge=1,
        le=4,
        description="Student response grade: 1=Forgot, 2=Struggled, 3=Correct, 4=Fluent",
    )
    session_id: str = Field(..., description="The dialogue session identifier.")
    pipeline_token: str = Field(
        ...,
        description="Pipeline token from score_answer (required for step ordering).",
    )


class UpdateFsrsOutput(BaseModel):
    """Output schema for update_fsrs tool."""

    node_id: str
    updated: bool
    new_stability: Optional[float] = None
    new_difficulty: Optional[float] = None
    next_review: Optional[str] = None
    status: str = "ok"
    message: str = ""


class UpdateBktInput(BaseModel):
    """Input schema for update_bkt tool."""

    node_id: str = Field(..., description="The canvas node identifier.")
    is_correct: bool = Field(
        ..., description="Whether the student's response was correct."
    )
    session_id: str = Field(..., description="The dialogue session identifier.")
    pipeline_token: str = Field(
        ...,
        description="Pipeline token from score_answer (required for step ordering).",
    )


class UpdateBktOutput(BaseModel):
    """Output schema for update_bkt tool."""

    node_id: str
    updated: bool
    new_p_mastery: Optional[float] = None
    status: str = "ok"
    message: str = ""


# ═══════════════════════════════════════════════════════════════════════════════
# Tool Implementation Functions
# ═══════════════════════════════════════════════════════════════════════════════


async def query_mastery(node_id: str) -> Dict[str, Any]:
    """
    Query the mastery state for a specific canvas node.

    Returns BKT mastery probability, FSRS parameters, and effective proficiency.
    This tool does not require a pipeline token.

    Args:
        node_id: The canvas node identifier.

    Returns:
        Dict with mastery data (p_mastery, FSRS params, effective_proficiency).
    """
    guardian = get_audit_guardian()
    asyncio.create_task(guardian.record_tool_call("query_mastery", "", node_id))

    try:
        from app.services.mastery_engine import get_mastery_engine
        from app.services.mastery_store import get_mastery_store

        engine = get_mastery_engine()

        # Query the concept state from the mastery store
        store = get_mastery_store()
        concept = await store.get_concept(node_id)

        if concept is None:
            return QueryMasteryOutput(
                node_id=node_id,
                status="not_found",
            ).model_dump()

        result = QueryMasteryOutput(
            node_id=node_id,
            p_mastery=concept.p_mastery,
            interaction_count=concept.interaction_count,
            last_interaction_ts=(
                concept.last_interaction_ts.isoformat()
                if concept.last_interaction_ts
                else None
            ),
            status="ok",
        )

        # Add FSRS data if available
        if concept.fsrs_stability is not None:
            result.fsrs_stability = concept.fsrs_stability
        if concept.fsrs_difficulty is not None:
            result.fsrs_difficulty = concept.fsrs_difficulty

        # Compute effective proficiency
        if hasattr(engine, "effective_proficiency"):
            result.effective_proficiency = engine.effective_proficiency(concept)

        return result.model_dump()

    except ImportError as e:
        logger.warning(f"[Story 3.2] query_mastery: service not available: {e}")
        return QueryMasteryOutput(
            node_id=node_id,
            status="service_unavailable",
        ).model_dump()
    except Exception as e:
        logger.error(f"[Story 3.2] query_mastery error: {e}")
        return QueryMasteryOutput(
            node_id=node_id,
            status="error",
        ).model_dump()


async def update_fsrs(
    node_id: str,
    grade: int,
    session_id: str,
    pipeline_token: str,
) -> Dict[str, Any]:
    """
    Update FSRS spaced repetition parameters for a node after scoring.

    Requires a pipeline token from score_answer (AC-3: step ordering enforcement).

    Args:
        node_id: The canvas node identifier.
        grade: Student response grade (1-4).
        session_id: The dialogue session identifier.
        pipeline_token: Token from score_answer step.

    Returns:
        Dict with updated FSRS parameters.
    """
    guardian = get_audit_guardian()
    asyncio.create_task(guardian.record_tool_call("update_fsrs", session_id, node_id))

    # Validate pipeline token (AC-3)
    token_mgr = get_pipeline_token_manager()
    try:
        token_mgr.validate_token(pipeline_token, expected_previous_step="score_answer")
    except PipelineTokenError as e:
        return UpdateFsrsOutput(
            node_id=node_id,
            updated=False,
            status=e.code,
            message=e.message,
        ).model_dump()

    try:
        from app.services.mastery_engine import get_mastery_engine
        from app.services.mastery_store import get_mastery_store

        engine = get_mastery_engine()
        store = get_mastery_store()

        concept = await store.get_concept(node_id)
        if concept is None:
            return UpdateFsrsOutput(
                node_id=node_id,
                updated=False,
                status="not_found",
                message=f"No mastery state found for node {node_id}",
            ).model_dump()

        # Run the update
        updated = engine.update_on_interaction(concept, grade)
        await store.save_concept(updated)

        result = UpdateFsrsOutput(
            node_id=node_id,
            updated=True,
            status="ok",
            message=f"FSRS updated with grade={grade}",
        )

        if updated.fsrs_stability is not None:
            result.new_stability = updated.fsrs_stability
        if updated.fsrs_difficulty is not None:
            result.new_difficulty = updated.fsrs_difficulty

        return result.model_dump()

    except ImportError as e:
        logger.warning(f"[Story 3.2] update_fsrs: service not available: {e}")
        return UpdateFsrsOutput(
            node_id=node_id,
            updated=False,
            status="service_unavailable",
            message=str(e),
        ).model_dump()
    except Exception as e:
        logger.error(f"[Story 3.2] update_fsrs error: {e}")
        return UpdateFsrsOutput(
            node_id=node_id,
            updated=False,
            status="error",
            message=str(e),
        ).model_dump()


async def update_bkt(
    node_id: str,
    is_correct: bool,
    session_id: str,
    pipeline_token: str,
) -> Dict[str, Any]:
    """
    Update BKT (Bayesian Knowledge Tracing) mastery probability for a node.

    Requires a pipeline token from score_answer (AC-3: step ordering enforcement).

    Args:
        node_id: The canvas node identifier.
        is_correct: Whether the student's response was correct.
        session_id: The dialogue session identifier.
        pipeline_token: Token from score_answer step.

    Returns:
        Dict with updated BKT mastery probability.
    """
    guardian = get_audit_guardian()
    asyncio.create_task(guardian.record_tool_call("update_bkt", session_id, node_id))

    # Validate pipeline token (AC-3)
    token_mgr = get_pipeline_token_manager()
    try:
        token_mgr.validate_token(pipeline_token, expected_previous_step="score_answer")
    except PipelineTokenError as e:
        return UpdateBktOutput(
            node_id=node_id,
            updated=False,
            status=e.code,
            message=e.message,
        ).model_dump()

    try:
        from app.services.mastery_engine import get_mastery_engine
        from app.services.mastery_store import get_mastery_store

        engine = get_mastery_engine()
        store = get_mastery_store()

        concept = await store.get_concept(node_id)
        if concept is None:
            return UpdateBktOutput(
                node_id=node_id,
                updated=False,
                status="not_found",
                message=f"No mastery state found for node {node_id}",
            ).model_dump()

        # Map is_correct to grade for the unified update API
        grade = 3 if is_correct else 1
        updated = engine.update_on_interaction(concept, grade)
        await store.save_concept(updated)

        return UpdateBktOutput(
            node_id=node_id,
            updated=True,
            new_p_mastery=updated.p_mastery,
            status="ok",
            message=f"BKT updated: correct={is_correct}",
        ).model_dump()

    except ImportError as e:
        logger.warning(f"[Story 3.2] update_bkt: service not available: {e}")
        return UpdateBktOutput(
            node_id=node_id,
            updated=False,
            status="service_unavailable",
            message=str(e),
        ).model_dump()
    except Exception as e:
        logger.error(f"[Story 3.2] update_bkt error: {e}")
        return UpdateBktOutput(
            node_id=node_id,
            updated=False,
            status="error",
            message=str(e),
        ).model_dump()
