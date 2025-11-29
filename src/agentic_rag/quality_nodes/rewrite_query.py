"""
Rewrite Query Node

LangGraph node for rewriting queries using QueryRewriter when quality is low.

Story 12.9 AC 9.2: Query rewriter在low质量时触发
- Condition: quality_grade=="low" AND rewrite_count < 2
- LLM: gpt-3.5-turbo
- Prompt: "原始问题未找到高质量结果，请从不同角度重写问题"

Story 12.9 AC 9.3: 最多2次迭代后强制返回
- rewrite_count ≥ 2: 直接返回END
- 防止死循环: 最大总延迟<10秒

✅ Verified from LangGraph Skill:
- Node signature: async def node(state: State, runtime: Runtime) -> dict
- Return dict with state updates
- Access messages from MessagesState

Author: Canvas Learning System Team
Version: 1.0.0
Created: 2025-11-29
"""

from typing import Dict, Any, Optional
from langgraph.runtime import Runtime

from agentic_rag.state import CanvasRAGState
from agentic_rag.config import CanvasRAGConfig
from agentic_rag.quality import QueryRewriter


# Initialize QueryRewriter instance
# ✅ Singleton pattern for shared rewriter
_query_rewriter = QueryRewriter(
    model="gpt-3.5-turbo",
    temperature=0.7,
    max_tokens=150
)


async def rewrite_query(
    state: CanvasRAGState,
    runtime: Runtime[CanvasRAGConfig]
) -> Dict[str, Any]:
    """
    Rewrite query using LLM when quality is low

    ✅ Verified from LangGraph Skill:
    - Async node pattern
    - MessagesState provides messages list
    - Return dict with state updates

    Story 12.9 AC 9.2, 9.3: Query rewriting implementation

    Args:
        state: Current state containing messages, rewrite_count
        runtime: Runtime configuration

    Returns:
        State updates:
        - messages: Appended rewritten query
        - query_rewritten: True
        - rewrite_count: +1
    """
    # Get current rewrite count
    rewrite_count = state.get("rewrite_count", 0)

    # Extract original query from messages
    # ✅ Verified from LangGraph MessagesState pattern
    messages = state.get("messages", [])
    original_query = state.get("original_query")

    if not original_query and messages:
        # Extract from last user message
        last_msg = messages[-1]
        if isinstance(last_msg, dict):
            original_query = last_msg.get("content", "")
        else:
            original_query = getattr(last_msg, "content", "")

    if not original_query:
        # Fallback: cannot rewrite empty query
        return {
            "query_rewritten": False,
            "rewrite_count": rewrite_count
        }

    # Build context for rewriter
    context = {
        "canvas_file": state.get("canvas_file"),
        "weak_concepts": state.get("weak_concepts"),
        "quality_grade": state.get("quality_grade")
    }

    # Rewrite query using LLM
    # Story 12.9 AC 9.2: LLM调用 gpt-3.5-turbo
    rewritten_query = await _query_rewriter.rewrite_query(
        original_query=original_query,
        context=context,
        rewrite_count=rewrite_count
    )

    # Update messages with rewritten query
    # ✅ Verified from LangGraph MessagesState:
    # - Return list of messages to append
    new_messages = [{"role": "user", "content": rewritten_query}]

    # Return state updates
    return {
        "messages": new_messages,
        "query_rewritten": True,
        "rewrite_count": rewrite_count + 1,
        # Store original query if first rewrite
        "original_query": original_query if rewrite_count == 0 else state.get("original_query")
    }


def should_rewrite_query(state: CanvasRAGState) -> bool:
    """
    Helper function to check if query should be rewritten

    Story 12.9 AC 9.2: Condition check
    - quality_grade=="low" AND rewrite_count < 2

    Args:
        state: Current state

    Returns:
        True if should rewrite, False otherwise
    """
    quality_grade = state.get("quality_grade")
    rewrite_count = state.get("rewrite_count", 0)
    max_rewrite_iterations = state.get("max_rewrite_iterations", 2)

    return quality_grade == "low" and rewrite_count < max_rewrite_iterations
