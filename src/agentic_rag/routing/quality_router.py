"""
Quality-based Routing for Conditional Edges

Implements routing logic after quality check:
- Low quality + retry available → rewrite_query → re-retrieve
- Medium/High quality OR max retries → END

Story 12.9 AC 9.3, 9.5: 循环逻辑正确
- 最多2次迭代后强制返回
- 防止死循环: rewrite_count ≥ 2 → END

✅ Verified from LangGraph Skill (Pattern: Conditional edges):
```python
def should_continue(state: MessagesState):
    if condition:
        return "node_name"
    return END
```

Author: Canvas Learning System Team
Version: 1.0.0
Created: 2025-11-29
"""

from typing import Literal
from langgraph.graph import END

from agentic_rag.state import CanvasRAGState


def route_after_quality_check(state: CanvasRAGState) -> Literal["rewrite_query", END]:
    """
    Route based on quality grade after check_quality node

    ✅ Verified from LangGraph Skill (Pattern: Conditional edges)

    Story 12.9 AC 9.3: 最多2次迭代后强制返回
    Story 12.9 AC 9.5: 循环逻辑正确

    Routing logic:
    - quality_grade == "low" AND rewrite_count < max_rewrite_iterations:
        → "rewrite_query" (trigger query rewriting)
    - quality_grade in ["medium", "high"]:
        → END (accept results, exit graph)
    - rewrite_count >= max_rewrite_iterations:
        → END (force return to prevent infinite loop)

    Args:
        state: Current state containing quality_grade, rewrite_count

    Returns:
        "rewrite_query" or END
    """
    # Extract state fields
    quality_grade = state.get("quality_grade")
    rewrite_count = state.get("rewrite_count", 0)

    # Get max rewrite iterations from config or default to 2
    # Story 12.9 AC 9.3: 最多2次迭代
    max_rewrite_iterations = 2  # TODO: Could be runtime config

    # ========================================
    # Routing Decision Tree
    # ========================================

    # Case 1: Low quality AND retry budget available
    if quality_grade == "low" and rewrite_count < max_rewrite_iterations:
        return "rewrite_query"

    # Case 2: Medium/High quality → Accept results
    if quality_grade in ["medium", "high"]:
        return END

    # Case 3: Max retries reached → Force return
    if rewrite_count >= max_rewrite_iterations:
        return END

    # Default: END (safety fallback)
    return END


def get_routing_metrics(state: CanvasRAGState) -> dict:
    """
    Get routing decision metrics for debugging/monitoring

    Returns:
        Dictionary with:
        - decision: "rewrite_query" or "END"
        - quality_grade: Current quality grade
        - rewrite_count: Current rewrite count
        - max_retries_reached: Boolean
    """
    decision = route_after_quality_check(state)
    quality_grade = state.get("quality_grade")
    rewrite_count = state.get("rewrite_count", 0)
    max_rewrite_iterations = 2

    return {
        "decision": decision,
        "quality_grade": quality_grade,
        "rewrite_count": rewrite_count,
        "max_retries_reached": rewrite_count >= max_rewrite_iterations,
        "reason": _get_routing_reason(state)
    }


def _get_routing_reason(state: CanvasRAGState) -> str:
    """
    Get human-readable reason for routing decision

    Returns:
        Reason string for logging/debugging
    """
    quality_grade = state.get("quality_grade")
    rewrite_count = state.get("rewrite_count", 0)
    max_rewrite_iterations = 2

    if quality_grade == "low" and rewrite_count < max_rewrite_iterations:
        return f"Low quality (rewrite {rewrite_count + 1}/{max_rewrite_iterations})"
    elif quality_grade in ["medium", "high"]:
        return f"Quality {quality_grade} - accepting results"
    elif rewrite_count >= max_rewrite_iterations:
        return f"Max retries reached ({rewrite_count}/{max_rewrite_iterations})"
    else:
        return "Default END"
