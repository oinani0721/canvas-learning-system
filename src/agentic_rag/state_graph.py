"""
LangGraph StateGraph构建 - Canvas Agentic RAG

构建完整的Agentic RAG StateGraph，包含:
- 并行检索 (Send模式)
- 融合算法
- Reranking
- 质量控制循环

✅ Verified from LangGraph Skill:
- Pattern: StateGraph(State, context_schema=ContextSchema)
- add_node(name, function)
- add_conditional_edges with Send for parallel execution
- compile() to build graph

Story 12.5 AC 5.4, 5.5:
- ✅ StateGraph compile成功
- ✅ 端到端运行测试

Author: Canvas Learning System Team
Version: 1.0.0
Created: 2025-11-29
"""

from typing import Literal
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send, RetryPolicy

from agentic_rag.state import CanvasRAGState
from agentic_rag.config import CanvasRAGConfig
from agentic_rag.nodes import (
    retrieve_graphiti,
    retrieve_lancedb,
    fuse_results,
    rerank_results,
    check_quality,
)


# ========================================
# Conditional Edge: Fan-out to Parallel Retrieval
# ========================================

def fan_out_retrieval(state: CanvasRAGState) -> list[Send]:
    """
    Fan-out to parallel retrieval nodes

    ✅ Verified from LangGraph Skill (Pattern: Send for parallel execution):
    ```python
    def continue_to_jokes(state: OverallState):
        return [Send("generate_joke", {"subject": s}) for s in state['subjects']]
    ```

    Returns:
        List[Send]: Send objects for parallel execution
    """
    # Send to both Graphiti and LanceDB in parallel
    return [
        Send("retrieve_graphiti", state),
        Send("retrieve_lancedb", state),
    ]


# ========================================
# Conditional Edge: Quality-based Routing
# ========================================

def route_after_quality_check(state: CanvasRAGState) -> Literal["rewrite_query", END]:
    """
    Route based on quality grade

    - low quality + rewrite_count < 2: rewrite_query → START (重新检索)
    - medium/high quality OR rewrite_count >= 2: END (返回结果)

    ✅ Verified from LangGraph Skill (Pattern: Conditional edges)
    ```python
    def should_continue(state: MessagesState):
        if condition:
            return "node_name"
        return END
    ```

    Returns:
        "rewrite_query" or END
    """
    quality_grade = state.get("quality_grade")
    rewrite_count = state.get("rewrite_count", 0)
    max_rewrite = 2  # TODO: 从runtime config获取

    # Low quality且未超过重写次数限制
    if quality_grade == "low" and rewrite_count < max_rewrite:
        return "rewrite_query"

    # Medium/High quality 或 已达重写上限
    return END


# ========================================
# Node: Query Rewrite
# ========================================

async def rewrite_query(state: CanvasRAGState) -> dict:
    """
    Query重写节点

    使用LLM重写query，从不同角度提问。

    ✅ Verified from LangGraph Skill:
    - Node returns dict with state updates

    TODO: Story 12.9 完成详细实现 (调用gpt-3.5-turbo)

    Returns:
        State updates:
        - messages: 添加重写后的query
        - query_rewritten: True
        - rewrite_count: +1
    """
    messages = state.get("messages", [])
    if messages:
        last_msg = messages[-1]
        original_query = last_msg.get("content", "") if isinstance(last_msg, dict) else getattr(last_msg, "content", "")
    else:
        original_query = ""

    # Placeholder: 简单添加"请详细解释"
    rewritten_query = f"请详细解释: {original_query}"

    # 更新state
    return {
        "messages": [{"role": "user", "content": rewritten_query}],
        "query_rewritten": True,
        "rewrite_count": state.get("rewrite_count", 0) + 1,
    }


# ========================================
# Build StateGraph
# ========================================

def rewrite_loop_routing(state: CanvasRAGState) -> list[Send]:
    """
    After query rewriting, fan out to parallel retrieval again

    Returns:
        List[Send]: Send objects for parallel execution
    """
    return fan_out_retrieval(state)


def build_canvas_agentic_rag_graph() -> StateGraph:
    """
    构建Canvas Agentic RAG StateGraph

    ✅ Verified from LangGraph Skill:
    - Pattern: StateGraph construction with context_schema
    - add_node, add_conditional_edges, add_edge
    - compile()

    Graph Structure:
    ```
    START
      ↓
    fan_out_retrieval (conditional edge)
      ├──→ retrieve_graphiti (parallel)
      └──→ retrieve_lancedb (parallel)
           ↓ (converge)
         fuse_results
           ↓
         rerank_results
           ↓
         check_quality
           ↓
         route_after_quality_check (conditional edge)
           ├──→ rewrite_query → fan_out_retrieval (if low quality)
           └──→ END (if medium/high quality or max rewrite)
    ```

    Returns:
        Compiled StateGraph
    """
    # 创建StateGraph with context schema
    builder = StateGraph(
        state_schema=CanvasRAGState,
        context_schema=CanvasRAGConfig
    )

    # ========================================
    # Add Nodes
    # ========================================

    # Retrieval nodes (with retry policy for resilience)
    builder.add_node(
        "retrieve_graphiti",
        retrieve_graphiti,
        retry_policy=RetryPolicy(
            retry_on=Exception,  # TODO: 细化为ConnectionError
            max_attempts=3,
            backoff_factor=2.0,
        )
    )

    builder.add_node(
        "retrieve_lancedb",
        retrieve_lancedb,
        retry_policy=RetryPolicy(
            retry_on=Exception,
            max_attempts=3,
            backoff_factor=2.0,
        )
    )

    # Processing nodes
    builder.add_node("fuse_results", fuse_results)
    builder.add_node("rerank_results", rerank_results)
    builder.add_node("check_quality", check_quality)

    # Quality control node
    builder.add_node("rewrite_query", rewrite_query)

    # ========================================
    # Add Edges
    # ========================================

    # START → fan_out_retrieval (parallel dispatch)
    builder.add_conditional_edges(
        START,
        fan_out_retrieval,
        # No path_map needed - Send objects specify destinations
    )

    # retrieve_graphiti → fuse_results
    # retrieve_lancedb → fuse_results
    # (Both parallel nodes converge to fuse_results automatically)
    builder.add_edge("retrieve_graphiti", "fuse_results")
    builder.add_edge("retrieve_lancedb", "fuse_results")

    # fuse_results → rerank_results
    builder.add_edge("fuse_results", "rerank_results")

    # rerank_results → check_quality
    builder.add_edge("rerank_results", "check_quality")

    # check_quality → route_after_quality_check (conditional)
    builder.add_conditional_edges(
        "check_quality",
        route_after_quality_check,
        # path_map for routing
        {
            "rewrite_query": "rewrite_query",
            END: END,
        }
    )

    # rewrite_query → fan_out_retrieval (loop back for re-retrieval)
    builder.add_conditional_edges(
        "rewrite_query",
        rewrite_loop_routing,
        # No path_map needed - Send objects specify destinations
    )

    return builder


# ========================================
# Compile Graph
# ========================================

# Build and compile the graph
_builder = build_canvas_agentic_rag_graph()
canvas_agentic_rag = _builder.compile()

# Export for use
__all__ = ["canvas_agentic_rag", "build_canvas_agentic_rag_graph"]
