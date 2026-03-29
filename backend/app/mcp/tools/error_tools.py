# Canvas Learning System - MCP Error Tools
# Story 3.6: Error Classification MCP Tool (AC-3, AC-4)
#
# Tools: record_error
# Provides Agent access to the 4-type error classification system.
# Agent calls this tool when it detects a student understanding error.
#
# [Source: _bmad-output/implementation-artifacts/3-6-tips-annotation-error-archiving.md#Task 3.1]

import asyncio
import logging
from typing import Any, Dict, Optional

# Note: asyncio.TimeoutError is used for narrowed exception handling in service calls

from pydantic import BaseModel, Field

from app.audit.guardian import get_audit_guardian

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Pydantic Models
# ═══════════════════════════════════════════════════════════════════════════════


class RecordErrorInput(BaseModel):
    """Input schema for record_error tool."""

    node_id: str = Field(..., description="The canvas node identifier.")
    session_id: str = Field(..., description="The dialogue session identifier.")
    error_description: str = Field(..., description="Description of the student's understanding error.")
    context: str = Field(
        default="",
        description="Dialogue context where the error was detected.",
    )


class RecordErrorOutput(BaseModel):
    """Output schema for record_error tool."""

    node_id: str
    recorded: bool
    misconception_id: Optional[str] = None
    error_type: Optional[str] = None
    error_type_label: Optional[str] = None
    remedy_strategy: Optional[str] = None
    remedy_description: Optional[str] = None
    status: str = "ok"
    message: str = ""


# ═══════════════════════════════════════════════════════════════════════════════
# Tool Implementation
# ═══════════════════════════════════════════════════════════════════════════════


async def record_error(
    node_id: str,
    session_id: str,
    error_description: str,
    context: str = "",
) -> Dict[str, Any]:
    """
    Record and classify a student understanding error.

    Story 3.6 AC-3: Agent calls this tool when detecting user errors.
    The error is automatically classified into 4 types and a remedy
    strategy is mapped.

    Story 3.6 AC-4: Classification result + remedy stored in Graphiti
    as a Misconception entity.

    This tool does not require a pipeline token.

    Args:
        node_id: The canvas node identifier.
        session_id: The dialogue session identifier.
        error_description: Description of the understanding error.
        context: Dialogue context where the error occurred.

    Returns:
        Dict with classification result and storage status.
    """
    guardian = get_audit_guardian()
    asyncio.create_task(guardian.record_tool_call("record_error", session_id, node_id))

    try:
        from app.graphiti.entity_types import ERROR_TYPE_DESCRIPTIONS
        from app.services.error_classifier import get_error_classifier

        classifier = get_error_classifier()

        # Classify the error
        result = await classifier.classify(
            error_description=error_description,
            node_id=node_id,
            session_id=session_id,
            context=context,
        )

        # Get human-readable descriptions
        type_info = ERROR_TYPE_DESCRIPTIONS.get(result.error_type, {})

        # Write to Graphiti via memory service
        try:
            from app.config import DEFAULT_GROUP_ID
            from app.services.memory_service import get_memory_service

            memory_svc = await get_memory_service()

            # Record the misconception as a knowledge entity
            await memory_svc.record_knowledge_entity(
                event_type="misconception",
                content=(
                    f"Error type: {type_info.get('label_zh', result.error_type.value)} | "
                    f"Description: {error_description} | "
                    f"Remedy: {type_info.get('remedy_zh', result.remedy_strategy.value)}"
                ),
                metadata={
                    "misconception_id": result.misconception.misconception_id,
                    "error_type": result.error_type.value,
                    "error_type_label": type_info.get("label_zh", ""),
                    "remedy_strategy": result.remedy_strategy.value,
                    "remedy_description": type_info.get("remedy_zh", ""),
                    "node_id": node_id,
                    "session_id": session_id,
                    "context": context,
                },
                group_id=DEFAULT_GROUP_ID,
            )
            logger.info(f"[Story 3.6] Misconception recorded: type={result.error_type.value} node={node_id}")
        except (RuntimeError, AttributeError, asyncio.TimeoutError) as e:
            logger.warning(f"[Story 3.6] Graphiti write failed (non-fatal): {e}")

        return RecordErrorOutput(
            node_id=node_id,
            recorded=True,
            misconception_id=result.misconception.misconception_id,
            error_type=result.error_type.value,
            error_type_label=type_info.get("label_zh", ""),
            remedy_strategy=result.remedy_strategy.value,
            remedy_description=type_info.get("remedy_zh", ""),
            status="ok",
            message=f"Error classified as {type_info.get('label_zh', result.error_type.value)}",
        ).model_dump()

    except ImportError as e:
        logger.warning(f"[Story 3.6] record_error: service not available: {e}")
        return RecordErrorOutput(
            node_id=node_id,
            recorded=False,
            status="service_unavailable",
            message=str(e),
        ).model_dump()
    except Exception as e:
        logger.error(f"[Story 3.6] record_error error: {e}")
        return RecordErrorOutput(
            node_id=node_id,
            recorded=False,
            status="error",
            message=str(e),
        ).model_dump()
