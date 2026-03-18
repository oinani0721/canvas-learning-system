# Canvas Learning System - MCP Conversation Tools
# Story 3.2: MCP Tool Exposure (AC-2)
#
# Tools: archive_conversation, create_exam_node
# These tools provide Agent access to conversation archiving and canvas operations.
#
# [Source: _bmad-output/implementation-artifacts/3-2-mcp-tool-exposure-backend-api.md#Task 2.5]

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.audit.guardian import get_audit_guardian

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Pydantic Models
# ═══════════════════════════════════════════════════════════════════════════════


class ArchiveConversationInput(BaseModel):
    """Input schema for archive_conversation tool."""

    node_id: str = Field(..., description="The canvas node identifier.")
    session_id: str = Field(..., description="The dialogue session identifier.")
    summary: str = Field(..., description="Summary of the conversation to archive.")
    key_insights: List[str] = Field(
        default_factory=list,
        description="Key learning insights extracted from the conversation.",
    )
    mastery_change: Optional[float] = Field(
        None,
        description="Change in mastery level during this conversation (-1.0 to 1.0).",
    )


class ArchiveConversationOutput(BaseModel):
    """Output schema for archive_conversation tool."""

    node_id: str
    archived: bool
    archive_id: Optional[str] = None
    status: str = "ok"
    message: str = ""


class CreateExamNodeInput(BaseModel):
    """Input schema for create_exam_node tool."""

    canvas_id: str = Field(..., description="The canvas board identifier.")
    source_node_id: str = Field(..., description="The source concept node to create an exam for.")
    exam_title: str = Field(..., description="Title for the exam node.")
    position_x: Optional[float] = Field(None, description="X position on canvas (auto-placed if not specified).")
    position_y: Optional[float] = Field(None, description="Y position on canvas (auto-placed if not specified).")


class CreateExamNodeOutput(BaseModel):
    """Output schema for create_exam_node tool."""

    node_id: str = Field(..., description="The created exam node identifier")
    canvas_id: str
    edge_id: Optional[str] = Field(None, description="Edge connecting exam node to source node")
    status: str = "ok"
    message: str = ""


# ═══════════════════════════════════════════════════════════════════════════════
# Tool Implementation Functions
# ═══════════════════════════════════════════════════════════════════════════════


async def archive_conversation(
    node_id: str,
    session_id: str,
    summary: str,
    key_insights: Optional[List[str]] = None,
    mastery_change: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Archive a completed conversation session to the learning memory system.

    Stores the conversation summary and key insights as a learning event
    in the Graphiti knowledge graph for future retrieval.

    This tool does not require a pipeline token.

    Args:
        node_id: The canvas node identifier.
        session_id: The dialogue session identifier.
        summary: Summary of the conversation.
        key_insights: Key learning insights extracted.
        mastery_change: Change in mastery level during the conversation.

    Returns:
        Dict with archive status.
    """
    guardian = get_audit_guardian()
    asyncio.create_task(guardian.record_tool_call("archive_conversation", session_id, node_id))

    if key_insights is None:
        key_insights = []

    archive_id = str(uuid.uuid4())

    try:
        from app.config import DEFAULT_GROUP_ID
        from app.services.memory_service import get_memory_service

        memory_svc = await get_memory_service()

        # Build the archive content
        content_parts = [f"Conversation summary for node {node_id}: {summary}"]
        if key_insights:
            content_parts.append("Key insights: " + "; ".join(key_insights))
        if mastery_change is not None:
            direction = "improved" if mastery_change > 0 else "decreased"
            content_parts.append(f"Mastery {direction} by {abs(mastery_change):.2f}")

        archive_content = " | ".join(content_parts)

        # Record as learning event
        await memory_svc.record_learning_event(
            event_type="conversation_archive",
            content=archive_content,
            metadata={
                "archive_id": archive_id,
                "node_id": node_id,
                "session_id": session_id,
                "summary": summary,
                "key_insights": key_insights,
                "mastery_change": mastery_change,
                "archived_at": datetime.now(timezone.utc).isoformat(),
            },
            group_id=DEFAULT_GROUP_ID,
        )

        return ArchiveConversationOutput(
            node_id=node_id,
            archived=True,
            archive_id=archive_id,
            status="ok",
            message="Conversation archived successfully",
        ).model_dump()

    except ImportError as e:
        logger.warning(f"[Story 3.2] archive_conversation: service not available: {e}")
        return ArchiveConversationOutput(
            node_id=node_id,
            archived=False,
            status="service_unavailable",
            message=str(e),
        ).model_dump()
    except Exception as e:
        logger.error(f"[Story 3.2] archive_conversation error: {e}")
        return ArchiveConversationOutput(
            node_id=node_id,
            archived=False,
            status="error",
            message=str(e),
        ).model_dump()


async def create_exam_node(
    canvas_id: str,
    source_node_id: str,
    exam_title: str,
    position_x: Optional[float] = None,
    position_y: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Create a new exam/verification node on the canvas linked to a source concept node.

    The exam node is placed near the source node and connected via an edge.
    This enables the visual representation of the exam-concept relationship
    on the canvas board.

    This tool does not require a pipeline token.

    Args:
        canvas_id: The canvas board identifier.
        source_node_id: The source concept node to create an exam for.
        exam_title: Title for the exam node.
        position_x: X position on canvas (auto-placed if not specified).
        position_y: Y position on canvas (auto-placed if not specified).

    Returns:
        Dict with created node and edge identifiers.
    """
    guardian = get_audit_guardian()
    asyncio.create_task(guardian.record_tool_call("create_exam_node", "", source_node_id))

    exam_node_id = str(uuid.uuid4())

    try:
        from app.config import settings
        from app.services.canvas_service import CanvasService

        canvas_svc = CanvasService(canvas_base_path=settings.canvas_base_path)

        # Get source node position for auto-placement
        if position_x is None or position_y is None:
            _, source_node = await canvas_svc.find_node_across_canvases(source_node_id)
            if source_node:
                # Place the exam node below and to the right of the source
                position_x = source_node.get("x", 0) + 300
                position_y = source_node.get("y", 0) + 100
            else:
                position_x = position_x or 0
                position_y = position_y or 0

        # Create the exam node via CanvasService.add_node
        await canvas_svc.add_node(
            canvas_name=canvas_id,
            node_data={
                "id": exam_node_id,
                "type": "text",
                "text": exam_title,
                "x": position_x,
                "y": position_y,
                "width": 250,
                "height": 60,
                "color": "4",  # Exam node color
            },
        )

        # Create edge from source to exam node via CanvasService.add_edge
        edge_id = str(uuid.uuid4())
        await canvas_svc.add_edge(
            canvas_name=canvas_id,
            edge_data={
                "id": edge_id,
                "fromNode": source_node_id,
                "toNode": exam_node_id,
                "fromSide": "bottom",
                "toSide": "top",
                "label": "exam",
            },
        )

        return CreateExamNodeOutput(
            node_id=exam_node_id,
            canvas_id=canvas_id,
            edge_id=edge_id,
            status="ok",
            message=f"Exam node '{exam_title}' created and linked",
        ).model_dump()

    except ImportError as e:
        logger.warning(f"[Story 3.2] create_exam_node: service not available: {e}")
        return CreateExamNodeOutput(
            node_id=exam_node_id,
            canvas_id=canvas_id,
            status="service_unavailable",
            message=str(e),
        ).model_dump()
    except Exception as e:
        logger.error(f"[Story 3.2] create_exam_node error: {e}")
        return CreateExamNodeOutput(
            node_id=exam_node_id,
            canvas_id=canvas_id,
            status="error",
            message=str(e),
        ).model_dump()
