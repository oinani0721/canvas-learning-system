"""
Grade Documents Node

LangGraph node for grading document quality using QualityChecker.

Story 12.9 AC 9.1: Quality checker正确分级
- high: Top-3平均分 ≥ 0.7
- medium: Top-3平均分 0.5-0.7
- low: Top-3平均分 < 0.5

✅ Verified from LangGraph Skill:
- Node signature: async def node(state: State, runtime: Runtime) -> dict
- Return dict with state updates

Author: Canvas Learning System Team
Version: 1.0.0
Created: 2025-11-29
"""

from typing import Dict, Any
from langgraph.runtime import Runtime

from agentic_rag.state import CanvasRAGState
from agentic_rag.config import CanvasRAGConfig
from agentic_rag.quality import QualityChecker


# Initialize QualityChecker instance
# ✅ Singleton pattern for shared checker across invocations
_quality_checker = QualityChecker(
    weights={
        "weak_point_coverage": 0.4,
        "relevance": 0.3,
        "diversity": 0.2,
        "sufficiency": 0.1,
    },
    high_threshold=0.7,
    medium_threshold=0.5
)


async def grade_documents(
    state: CanvasRAGState,
    runtime: Runtime[CanvasRAGConfig]
) -> Dict[str, Any]:
    """
    Grade document quality using 4-dimension scoring

    ✅ Verified from LangGraph Skill:
    - Async node pattern
    - Access runtime config via runtime.context
    - Return dict with state updates

    Story 12.9 AC 9.1: Quality checker正确分级

    Args:
        state: Current state containing reranked_results
        runtime: Runtime configuration

    Returns:
        State updates:
        - quality_grade: Literal["high", "medium", "low"]
        - quality_metrics: Optional detailed metrics
    """
    # Get reranked results from state
    reranked_results = state.get("reranked_results", [])

    # Get weak concepts from temporal memory (if available)
    # TODO: Story 12.4 integration - fetch from TemporalMemory
    weak_concepts = state.get("weak_concepts") or []

    # Get canvas file for context
    canvas_file = state.get("canvas_file")

    # Grade documents using QualityChecker
    quality_grade = _quality_checker.grade_documents(
        results=reranked_results,
        weak_concepts=weak_concepts,
        canvas_file=canvas_file
    )

    # Get detailed metrics (optional, for debugging/monitoring)
    quality_metrics = _quality_checker.get_quality_metrics(
        results=reranked_results,
        weak_concepts=weak_concepts,
        canvas_file=canvas_file
    )

    # Return state updates
    return {
        "quality_grade": quality_grade,
        # Store metrics in metadata for LangSmith tracking
        "quality_metrics": quality_metrics
    }
