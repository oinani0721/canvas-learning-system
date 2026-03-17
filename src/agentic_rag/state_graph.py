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

# Story 7.1: Faithfulness check node (RAGAS claim-level NLI)
from agentic_rag.faithfulness_check import (  # noqa: E402
    faithfulness_check as faithfulness_check_node,
)

# Story 6.8: 导入多模态检索节点
# Story 23.4: 导入教材和跨Canvas检索节点
from agentic_rag.retrievers import (  # noqa: E402
    cross_canvas_retrieval_node,
    multimodal_retrieval_node,
    textbook_retrieval_node,
    vault_notes_retrieval_node,
)
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
    Story 23.4 扩展: 添加教材和跨Canvas检索节点，五路并行检索

    Returns:
        List[Send]: Send objects for parallel execution
    """
    # 六路并行检索日志
    logger.debug("[fan_out_retrieval] Dispatching to 6 parallel retrieval nodes")

    # Send to all 6 retrieval sources in parallel
    sends = [
        Send("retrieve_graphiti", state),
        Send("retrieve_lancedb", state),
        Send("retrieve_multimodal", state),  # Story 6.8: 多模态检索
        Send("retrieve_textbook", state),  # Story 23.4: 教材上下文
        Send("retrieve_cross_canvas", state),  # Story 23.4: 跨Canvas关联
        Send("retrieve_vault_notes", state),  # Vault Notes: .md 笔记检索
    ]

    logger.debug(f"[fan_out_retrieval] Created {len(sends)} Send objects: all 6 retrieval nodes")
    return sends


# ========================================
# Conditional Edge: Quality-based Routing
# ========================================


def route_after_quality_check(state: CanvasRAGState) -> Literal["rewrite_query", "faithfulness_check"]:
    """
    Route based on quality grade

    - low quality + rewrite_count < 2: rewrite_query (loop back for re-retrieval)
    - medium/high quality OR rewrite_count >= 2: faithfulness_check (final gate)

    Story 7.1: Routes to faithfulness_check instead of END for final quality gate.

    Returns:
        "rewrite_query" or "faithfulness_check"
    """
    quality_grade = state.get("quality_grade")
    rewrite_count = state.get("rewrite_count", 0)
    max_rewrite = 2

    logger.debug(
        f"[route_after_quality_check] quality={quality_grade}, rewrite_count={rewrite_count}, max={max_rewrite}"
    )

    # Low quality and rewrite budget remaining
    if quality_grade == "low" and rewrite_count < max_rewrite:
        logger.debug("[route_after_quality_check] -> rewrite_query (low quality, can retry)")
        return "rewrite_query"

    # Acceptable quality or max rewrites reached -> faithfulness check
    if rewrite_count >= max_rewrite:
        logger.debug(f"[route_after_quality_check] -> faithfulness_check (max rewrite reached: {rewrite_count})")
    else:
        logger.debug(f"[route_after_quality_check] -> faithfulness_check (quality acceptable: {quality_grade})")
    return "faithfulness_check"


# ========================================
# Node: Query Rewrite
# ========================================


async def rewrite_query(state: CanvasRAGState) -> dict:
    """
    Query重写节点

    Story 2.2 Task 3: 接入LLM进行真正的查询改写。
    - 使用LiteLLM SDK调用配置的LLM
    - 3秒超时保护
    - LLM不可用时降级为关键词扩展

    Returns:
        State updates:
        - messages: 添加重写后的query
        - query_rewritten: True
        - rewrite_count: +1
    """
    import asyncio
    import os

    current_rewrite_count = state.get("rewrite_count", 0)

    logger.debug(f"[rewrite_query] START - rewrite_count={current_rewrite_count}")

    messages = state.get("messages", [])
    if messages:
        last_msg = messages[-1]
        original_query = last_msg.get("content", "") if isinstance(last_msg, dict) else getattr(last_msg, "content", "")
    else:
        original_query = ""

    rewritten_query = original_query  # default: keep original

    # Story 2.2 Task 3.2: Try LLM-based rewrite via LiteLLM
    llm_rewrite_success = False
    try:
        import litellm

        litellm.set_verbose = False

        # Use configured model (same pattern as faithfulness_check.py)
        model_name = os.getenv("AI_MODEL_NAME", "gemini-2.0-flash-exp")
        litellm_prefix = os.getenv("FAITHFULNESS_LITELLM_PREFIX", "")
        if litellm_prefix and not model_name.startswith(litellm_prefix):
            model_name = f"{litellm_prefix}{model_name}"

        rewrite_prompt = (
            "你是搜索查询优化专家。请将以下查询改写为更精确的搜索查询，"
            "以获得更相关的检索结果。\n"
            f"原始查询：{original_query}\n"
            "请用不同的关键词和角度重写，直接返回改写后的查询，不要解释。"
        )

        # Story 2.2 Task 3.3: 3秒超时保护
        response = await asyncio.wait_for(
            litellm.acompletion(
                model=model_name,
                messages=[{"role": "user", "content": rewrite_prompt}],
                max_tokens=150,
                temperature=0.7,
            ),
            timeout=3.0,
        )

        llm_rewritten = response.choices[0].message.content.strip()
        if llm_rewritten and llm_rewritten != original_query:
            rewritten_query = llm_rewritten
            llm_rewrite_success = True
            logger.info(
                f"[rewrite_query] LLM rewrite success: '{original_query[:40]}...' -> '{rewritten_query[:40]}...'"
            )

    except asyncio.TimeoutError:
        logger.warning("[rewrite_query] LLM rewrite timed out (3s), using keyword fallback")
    except ImportError:
        logger.warning("[rewrite_query] litellm not installed, using keyword fallback")
    except Exception as e:
        logger.warning(f"[rewrite_query] LLM rewrite failed: {e}, using keyword fallback")

    # Story 2.2 Task 3.3/3.4: Fallback - keyword expansion
    if not llm_rewrite_success:
        try:
            import jieba

            # Extract top-5 keywords via jieba and append to query
            keywords = jieba.analyse.extract_tags(original_query, topK=5)
            if keywords:
                rewritten_query = f"{original_query} {' '.join(keywords)}"
            else:
                rewritten_query = f"{original_query} 关键概念 定义 解释"
        except ImportError:
            # jieba not available, use simple expansion
            rewritten_query = f"{original_query} 关键概念 定义 解释"

    new_rewrite_count = current_rewrite_count + 1

    # Story 2.2 Task 3.5: Log before/after query
    logger.info(
        f"[rewrite_query] END - rewrite_count={new_rewrite_count}, "
        f"llm_success={llm_rewrite_success}, "
        f"original='{original_query[:50]}', rewritten='{rewritten_query[:50]}'"
    )

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

    Graph Structure (六路并行检索 + faithfulness gate):
    ```
    START
      |
    fan_out_retrieval (conditional edge)
      |--- retrieve_graphiti (parallel)
      |--- retrieve_lancedb (parallel)
      |--- retrieve_multimodal (parallel) [Story 6.8]
      |--- retrieve_textbook (parallel) [Story 23.4]
      |--- retrieve_cross_canvas (parallel) [Story 23.4]
      +--- retrieve_vault_notes (parallel) [Vault Notes]
           | (converge)
         fuse_results (6-source weighted fusion)
           |
         rerank_results
           |
         check_quality
           |
         route_after_quality_check (conditional edge)
           |--- rewrite_query -> fan_out_retrieval (if low quality)
           +--- faithfulness_check [Story 7.1] (if acceptable quality)
                  |
                 END
    ```

    Returns:
        Compiled StateGraph
    """
    # 创建StateGraph with context schema
    builder = StateGraph(state_schema=CanvasRAGState, context_schema=CanvasRAGConfig)

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
        ),
    )

    builder.add_node(
        "retrieve_lancedb",
        retrieve_lancedb,
        retry_policy=RetryPolicy(
            retry_on=Exception,
            max_attempts=3,
            backoff_factor=2.0,
        ),
    )

    # Story 6.8: 多模态检索节点 (with timeout degradation per AC 6.8.4)
    builder.add_node(
        "retrieve_multimodal",
        multimodal_retrieval_node,
        retry_policy=RetryPolicy(
            retry_on=Exception,
            max_attempts=2,  # 较少重试，以满足2秒延迟要求
            backoff_factor=1.5,
        ),
    )

    # Story 23.4: 教材上下文检索节点
    builder.add_node(
        "retrieve_textbook",
        textbook_retrieval_node,
        retry_policy=RetryPolicy(
            retry_on=Exception,
            max_attempts=2,
            backoff_factor=1.5,
        ),
    )

    # Story 23.4: 跨Canvas关联检索节点
    builder.add_node(
        "retrieve_cross_canvas",
        cross_canvas_retrieval_node,
        retry_policy=RetryPolicy(
            retry_on=Exception,
            max_attempts=2,
            backoff_factor=1.5,
        ),
    )

    # Vault Notes: .md 笔记检索节点
    builder.add_node(
        "retrieve_vault_notes",
        vault_notes_retrieval_node,
        retry_policy=RetryPolicy(
            retry_on=Exception,
            max_attempts=2,
            backoff_factor=1.5,
        ),
    )

    # Processing nodes
    builder.add_node("fuse_results", fuse_results)
    builder.add_node("rerank_results", rerank_results)
    builder.add_node("check_quality", check_quality)

    # Story 7.1: Faithfulness check (RAGAS claim-level NLI) - last quality gate
    builder.add_node("faithfulness_check", faithfulness_check_node)

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
    # retrieve_textbook → fuse_results (Story 23.4)
    # retrieve_cross_canvas → fuse_results (Story 23.4)
    # (All parallel nodes converge to fuse_results automatically)
    builder.add_edge("retrieve_graphiti", "fuse_results")
    builder.add_edge("retrieve_lancedb", "fuse_results")
    builder.add_edge("retrieve_multimodal", "fuse_results")  # Story 6.8
    builder.add_edge("retrieve_textbook", "fuse_results")  # Story 23.4
    builder.add_edge("retrieve_cross_canvas", "fuse_results")  # Story 23.4
    builder.add_edge("retrieve_vault_notes", "fuse_results")  # Vault Notes

    # fuse_results → rerank_results
    builder.add_edge("fuse_results", "rerank_results")

    # rerank_results → check_quality
    builder.add_edge("rerank_results", "check_quality")

    # check_quality → route_after_quality_check (conditional)
    # Story 7.1: Routes to faithfulness_check instead of END
    builder.add_conditional_edges(
        "check_quality",
        route_after_quality_check,
        {
            "rewrite_query": "rewrite_query",
            "faithfulness_check": "faithfulness_check",
        },
    )

    # Story 7.1: faithfulness_check → END (final quality gate)
    builder.add_edge("faithfulness_check", END)

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
