# Canvas Learning System - MCP Memory Tools
# Story 3.2: MCP Tool Exposure (AC-2)
#
# Tools: search_memories, record_calibration
# These tools provide Agent access to the Graphiti learning memory system.
#
# [Source: _bmad-output/implementation-artifacts/3-2-mcp-tool-exposure-backend-api.md#Task 2.4]

import asyncio
import logging
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.audit.guardian import get_audit_guardian

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Pydantic Models
# ═══════════════════════════════════════════════════════════════════════════════


class SearchMemoriesInput(BaseModel):
    """Input schema for search_memories tool."""

    query: str = Field(..., description="Natural language search query.")
    node_id: Optional[str] = Field(None, description="Filter by canvas node ID (optional).")
    group_id: Optional[str] = Field(None, description="Graphiti group_id for memory isolation (optional).")
    max_results: int = Field(10, ge=1, le=50, description="Maximum number of results to return.")


class MemoryItem(BaseModel):
    """A single memory search result."""

    fact: str = Field(..., description="The memory fact content")
    source: Optional[str] = Field(None, description="Source of the memory")
    timestamp: Optional[str] = Field(None, description="When the memory was created")
    relevance_score: Optional[float] = Field(None, description="Search relevance score")


class SearchMemoriesOutput(BaseModel):
    """Output schema for search_memories tool."""

    query: str
    results: List[MemoryItem] = Field(default_factory=list)
    total_count: int = 0
    status: str = "ok"
    message: str = ""


class RecordCalibrationInput(BaseModel):
    """Input schema for record_calibration tool."""

    node_id: str = Field(..., description="The canvas node identifier.")
    session_id: str = Field(..., description="The dialogue session identifier.")
    predicted_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="The predicted/expected score before answering.",
    )
    actual_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="The actual score after answering.",
    )
    question_type: Optional[str] = Field(None, description="Type of question that was asked.")
    difficulty: Optional[str] = Field(None, description="Difficulty level of the question.")


class RecordCalibrationOutput(BaseModel):
    """Output schema for record_calibration tool."""

    node_id: str
    recorded: bool
    calibration_gap: float = Field(..., description="Absolute gap between predicted and actual score")
    status: str = "ok"
    message: str = ""


# ═══════════════════════════════════════════════════════════════════════════════
# Tool Implementation Functions
# ═══════════════════════════════════════════════════════════════════════════════


async def search_memories(
    query: str,
    node_id: Optional[str] = None,
    group_id: Optional[str] = None,
    max_results: int = 10,
) -> Dict[str, Any]:
    """
    Search the Graphiti learning memory knowledge graph.

    Returns relevant learning memories (facts, events, associations)
    matching the natural language query.

    This tool does not require a pipeline token.

    Args:
        query: Natural language search query.
        node_id: Optional filter by canvas node ID.
        group_id: Optional Graphiti group_id for memory isolation.
        max_results: Maximum number of results to return.

    Returns:
        Dict with search results.
    """
    guardian = get_audit_guardian()
    asyncio.create_task(guardian.record_tool_call("search_memories", "", node_id or ""))

    try:
        from app.services.memory_service import get_memory_service

        memory_svc = await get_memory_service()

        # Use the default group_id if not specified
        if group_id is None:
            from app.config import DEFAULT_GROUP_ID

            group_id = DEFAULT_GROUP_ID

        # Search memories via the memory service
        search_result = await memory_svc.search_memories(
            query=query,
            group_id=group_id,
            max_results=max_results,
        )

        # Convert results to MemoryItem format
        items: List[MemoryItem] = []
        raw_results = search_result if isinstance(search_result, list) else []

        for item in raw_results[:max_results]:
            if isinstance(item, dict):
                items.append(
                    MemoryItem(
                        fact=item.get("fact", item.get("content", str(item))),
                        source=item.get("source"),
                        timestamp=item.get("timestamp", item.get("created_at")),
                        relevance_score=item.get("score", item.get("relevance_score")),
                    )
                )
            else:
                # Handle Graphiti entity objects
                items.append(
                    MemoryItem(
                        fact=getattr(item, "fact", str(item)),
                        source=getattr(item, "source", None),
                        timestamp=str(getattr(item, "created_at", "")),
                        relevance_score=getattr(item, "score", None),
                    )
                )

        return SearchMemoriesOutput(
            query=query,
            results=items,
            total_count=len(items),
            status="ok",
        ).model_dump()

    except ImportError as e:
        logger.warning(f"[Story 3.2] search_memories: service not available: {e}")
        return SearchMemoriesOutput(
            query=query,
            status="service_unavailable",
            message=str(e),
        ).model_dump()
    except Exception as e:
        logger.error(f"[Story 3.2] search_memories error: {e}")
        return SearchMemoriesOutput(
            query=query,
            status="error",
            message=str(e),
        ).model_dump()


async def record_calibration(
    node_id: str,
    session_id: str,
    predicted_score: float,
    actual_score: float,
    question_type: Optional[str] = None,
    difficulty: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Record a calibration data point for metacognitive tracking.

    Captures the gap between a student's predicted performance and actual
    performance, which is used to track self-assessment accuracy over time.

    This tool does not require a pipeline token.

    Args:
        node_id: The canvas node identifier.
        session_id: The dialogue session identifier.
        predicted_score: The predicted/expected score before answering.
        actual_score: The actual score after answering.
        question_type: Type of question (optional).
        difficulty: Difficulty level (optional).

    Returns:
        Dict with recording status and calibration gap.
    """
    guardian = get_audit_guardian()
    asyncio.create_task(guardian.record_tool_call("record_calibration", session_id, node_id))

    calibration_gap = abs(predicted_score - actual_score)

    try:
        from app.config import DEFAULT_GROUP_ID
        from app.services.memory_service import get_memory_service

        memory_svc = await get_memory_service()

        # Record calibration as a learning event
        calibration_data = {
            "event_type": "calibration",
            "node_id": node_id,
            "session_id": session_id,
            "predicted_score": predicted_score,
            "actual_score": actual_score,
            "calibration_gap": calibration_gap,
        }
        if question_type:
            calibration_data["question_type"] = question_type
        if difficulty:
            calibration_data["difficulty"] = difficulty

        await memory_svc.record_knowledge_entity(
            event_type="calibration",
            content=f"Calibration: predicted={predicted_score:.2f} actual={actual_score:.2f} gap={calibration_gap:.2f}",
            metadata=calibration_data,
            group_id=DEFAULT_GROUP_ID,
        )

        return RecordCalibrationOutput(
            node_id=node_id,
            recorded=True,
            calibration_gap=calibration_gap,
            status="ok",
            message=f"Calibration recorded: gap={calibration_gap:.2f}",
        ).model_dump()

    except ImportError as e:
        logger.warning(f"[Story 3.2] record_calibration: service not available: {e}")
        return RecordCalibrationOutput(
            node_id=node_id,
            recorded=False,
            calibration_gap=calibration_gap,
            status="service_unavailable",
            message=str(e),
        ).model_dump()
    except Exception as e:
        logger.error(f"[Story 3.2] record_calibration error: {e}")
        return RecordCalibrationOutput(
            node_id=node_id,
            recorded=False,
            calibration_gap=calibration_gap,
            status="error",
            message=str(e),
        ).model_dump()
