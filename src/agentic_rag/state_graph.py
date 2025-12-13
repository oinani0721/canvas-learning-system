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

Story 23.3 Update:
- ✅ 添加DEBUG日志 (AC 1-5)
- ✅ 验证三路并行检索
- ✅ 验证质量控制循环

Author: Canvas Learning System Team
Version: 1.1.0
Created: 2025-11-29
Updated: 2025-12-12
"""

import logging
from typing import Literal

from langgraph.graph import END, START, StateGraph
from langgraph.types import RetryPolicy, Send

# ✅ Story 23.3: 配置日志
logger = logging.getLogger(__name__)

from agentic_rag.config import CanvasRAGConfig  # noqa: E402
from agentic_rag.nodes import (  # noqa: E402
    check_quality,
    fuse_results,
    rerank_results,
    retrieve_graphiti,
    retrieve_lancedb,
)

# Story 6.8: 导入多模态检索节点
from agentic_rag.retrievers import multimodal_retrieval_node  # noqa: E402
from agentic_rag.state import CanvasRAGState  # noqa: E402

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

    ✅ Verified from Context7 (langgraph - Dynamic Parallel Processing with Send):
    - Conditional edges return list[Send] to enable parallel execution
    - Send objects specify target node and state

    Story 6.8 扩展: 添加多模态检索节点，三路并行检索

    Returns:
        List[Send]: Send objects for parallel execution
    """
    # ✅ Story 23.3 AC 2: 三路并行检索日志
    logger.debug("[fan_out_retrieval] Dispatching to 3 parallel retrieval nodes")

    # Send to Graphiti, LanceDB, and Multimodal in parallel (Story 6.8)
    sends = [
        Send("retrieve_graphiti", state),
        Send("retrieve_lancedb", state),
        Send("retrieve_multimodal", state),  # Story 6.8: 多模态检索
    ]

    logger.debug(f"[fan_out_retrieval] Created {len(sends)} Send objects: retrieve_graphiti, retrieve_lancedb, retrieve_multimodal")
    return sends


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

    # ✅ Story 23.3 AC 4: 质量控制循环日志
    logger.debug(f"[route_after_quality_check] quality={quality_grade}, rewrite_count={rewrite_count}, max={max_rewrite}")

    # Low quality且未超过重写次数限制
    if quality_grade == "low" and rewrite_count < max_rewrite:
        logger.debug("[route_after_quality_check] → rewrite_query (low quality, can retry)")
        return "rewrite_query"

    # Medium/High quality 或 已达重写上限
    if rewrite_count >= max_rewrite:
        logger.debug(f"[route_after_quality_check] → END (max rewrite reached: {rewrite_count})")
    else:
        logger.debug(f"[route_after_quality_check] → END (quality acceptable: {quality_grade})")
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
    current_rewrite_count = state.get("rewrite_count", 0)

    # ✅ Story 23.3 AC 4: 节点入口日志
    logger.debug(f"[rewrite_query] START - rewrite_count={current_rewrite_count}")

    messages = state.get("messages", [])
    if messages:
        last_msg = messages[-1]
        original_query = last_msg.get("content", "") if isinstance(last_msg, dict) else getattr(last_msg, "content", "")
    else:
        original_query = ""

    # Placeholder: 简单添加"请详细解释"
    rewritten_query = f"请详细解释: {original_query}"

    new_rewrite_count = current_rewrite_count + 1

    # ✅ Story 23.3 AC 4: 节点出口日志
    logger.debug(f"[rewrite_query] END - new_rewrite_count={new_rewrite_count}, query='{rewritten_query[:50]}...'")

    # 更新state
    return {
        "messages": [{"role": "user", "content": rewritten_query}],
        "query_rewritten": True,
        "rewrite_count": new_rewrite_count,
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

    Graph Structure (Story 6.8 扩展):
    ```
    START
      ↓
    fan_out_retrieval (conditional edge)
      ├──→ retrieve_graphiti (parallel)
      ├──→ retrieve_lancedb (parallel)
      └──→ retrieve_multimodal (parallel) [Story 6.8]
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

    # Story 6.8: 多模态检索节点 (with timeout degradation per AC 6.8.4)
    builder.add_node(
        "retrieve_multimodal",
        multimodal_retrieval_node,
        retry_policy=RetryPolicy(
            retry_on=Exception,
            max_attempts=2,  # 较少重试，以满足2秒延迟要求
            backoff_factor=1.5,
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
    # retrieve_multimodal → fuse_results (Story 6.8)
    # (All parallel nodes converge to fuse_results automatically)
    builder.add_edge("retrieve_graphiti", "fuse_results")
    builder.add_edge("retrieve_lancedb", "fuse_results")
    builder.add_edge("retrieve_multimodal", "fuse_results")  # Story 6.8

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
