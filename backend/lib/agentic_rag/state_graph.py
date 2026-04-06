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
from agentic_rag.faithfulness_check import (  # noqa: E402
    faithfulness_check as faithfulness_check_node,
)
from agentic_rag.nodes import (  # noqa: E402
    check_quality,
    compress_context_node,
    fuse_results,
    multi_query_rewrite_node,
    rerank_results,
    retrieve_graphiti,
    retrieve_lancedb,
)
from agentic_rag.retrievers import (  # noqa: E402
    cross_canvas_retrieval_node,
    multimodal_retrieval_node,
    vault_notes_retrieval_node,
)
from agentic_rag.state import CanvasRAGState  # noqa: E402

# ========================================
# Conditional Edge: Fan-out to Parallel Retrieval
# ========================================


def classify_query_intent(query: str) -> str:
    """
    Story 2.6 AC-5: L1 路由 — 规则分类查询意图

    通过关键词匹配将查询分类为四种意图之一:
    - knowledge_point: 知识点查询 → 优先 Dense + Sparse
    - learning_history: 学习历史查询 → 优先 Graphiti
    - file_locate: 文件定位查询 → 优先 Vault + CLI
    - comprehensive: 综合/未分类 → 全部 6 路

    规则分类延迟 <1ms，满足 L1 < 200ms 要求。
    MVP 阶段使用规则分类，LLM 分类为远期增强。

    Args:
        query: 用户查询文本

    Returns:
        意图分类字符串
    """
    q = query.lower().strip()

    # File/note locate keywords
    file_keywords = [
        "笔记",
        "文件",
        "文档",
        "在哪",
        "哪个文件",
        "找到",
        "note",
        "file",
        "document",
        "where",
        "locate",
        "find",
    ]
    for kw in file_keywords:
        if kw in q:
            return "file_locate"

    # Learning history keywords
    history_keywords = [
        "之前",
        "上次",
        "复习",
        "历史",
        "学过",
        "记录",
        "进度",
        "回顾",
        "以前",
        "学习过",
        "掌握",
        "previous",
        "history",
        "review",
        "progress",
        "learned",
    ]
    for kw in history_keywords:
        if kw in q:
            return "learning_history"

    # Default: comprehensive (knowledge_point is also handled by full retrieval)
    return "comprehensive"


def _build_sends_for_intent(intent: str, state: CanvasRAGState) -> list[Send]:
    """
    Story 2.6 AC-5: Build Send list based on query intent.

    Args:
        intent: Query intent classification
        state: Current state to pass to retrieval nodes

    Returns:
        List of Send objects for parallel retrieval
    """
    all_sends = [
        Send("retrieve_graphiti", state),
        Send("retrieve_lancedb", state),
        Send("retrieve_multimodal", state),
        Send("retrieve_cross_canvas", state),
        Send("retrieve_vault_notes", state),
    ]

    if intent == "file_locate":
        # Prioritize vault + lancedb, skip graphiti/multimodal
        return [
            Send("retrieve_lancedb", state),
            Send("retrieve_vault_notes", state),
            Send("retrieve_cross_canvas", state),
        ]
    elif intent == "learning_history":
        # Prioritize graphiti + lancedb
        return [
            Send("retrieve_graphiti", state),
            Send("retrieve_lancedb", state),
            Send("retrieve_vault_notes", state),
        ]
    else:
        # comprehensive / knowledge_point: all 5 routes
        return all_sends


def fan_out_retrieval(state: CanvasRAGState) -> list[Send]:
    """
    Fan-out to parallel retrieval nodes — Story 2.6 AC-5: L1 智能路由

    Uses classify_query_intent to determine which retrieval channels to activate.
    Falls back to all 6 routes if routing fails.

    Story 2.10 fix: When multi_queries is populated by multi_query_rewrite_node,
    creates Send objects for each rewritten query (broadening recall). Otherwise
    uses the original query from messages.

    Returns:
        List[Send]: Send objects for parallel execution
    """
    # Story 2.10 fix: Check for multi-query rewrites first
    multi_queries = state.get("multi_queries")

    # Extract original query for intent classification
    messages = state.get("messages", [])
    query = ""
    if messages:
        last_msg = messages[-1]
        query = (
            last_msg.get("content", "")
            if isinstance(last_msg, dict)
            else getattr(last_msg, "content", "")
        )

    # L1 routing with exception safety
    try:
        intent = classify_query_intent(query)
    except Exception as e:
        logger.warning(
            f"[fan_out_retrieval] L1 routing failed: {e}, falling back to comprehensive"
        )
        intent = "comprehensive"

    # Story 2.10: If multi_queries exist, create Sends for each query variant
    # Each query variant gets its own set of retrieval channels based on intent
    if multi_queries and len(multi_queries) > 1:
        all_sends: list[Send] = []
        for mq in multi_queries:
            # Create a state copy with the rewritten query as the last message
            query_state = {**state, "messages": [{"role": "user", "content": mq}]}
            sends_for_query = _build_sends_for_intent(intent, query_state)
            all_sends.extend(sends_for_query)
        logger.info(
            f"[fan_out_retrieval] Multi-query L1 routing: intent={intent}, "
            f"queries={len(multi_queries)}, total_sends={len(all_sends)}"
        )
        return all_sends

    # Single query path (original behavior)
    try:
        sends = _build_sends_for_intent(intent, state)
        logger.info(
            f"[fan_out_retrieval] L1 routing: intent={intent}, channels={len(sends)}, query='{query[:50]}'"
        )
    except Exception as e:
        logger.warning(
            f"[fan_out_retrieval] L1 routing failed: {e}, falling back to all 5 channels"
        )
        sends = [
            Send("retrieve_graphiti", state),
            Send("retrieve_lancedb", state),
            Send("retrieve_multimodal", state),
            Send("retrieve_cross_canvas", state),
            Send("retrieve_vault_notes", state),
        ]

    logger.debug(
        f"[fan_out_retrieval] Created {len(sends)} Send objects for intent={intent}"
    )
    return sends


# ========================================
# Conditional Edge: Quality-based Routing
# ========================================


def route_after_quality_check(
    state: CanvasRAGState,
) -> Literal["rewrite_query", "faithfulness_check"]:
    """
    Route based on quality grade — Story 2.6 AC-3/AC-4

    - low quality + NOT safe_degradation: rewrite_query (loop back for re-retrieval)
    - medium/high quality OR safe_degradation set: faithfulness_check (final gate)
    - safe_degradation is set in check_quality node (not here, per LangGraph convention)

    Uses safe_degradation flag from state (set by check_quality based on config-driven
    max_rewrite_iterations) rather than hardcoding max_rewrite here, so the router
    stays in sync with runtime config.

    Story 7.1: Routes to faithfulness_check instead of END for final quality gate.

    Returns:
        "rewrite_query" or "faithfulness_check"
    """
    quality_grade = state.get("quality_grade")
    rewrite_count = state.get("rewrite_count", 0)
    safe_degradation = state.get("safe_degradation", False)

    logger.debug(
        f"[route_after_quality_check] quality={quality_grade}, "
        f"rewrite_count={rewrite_count}, safe_degradation={safe_degradation}"
    )

    # Low quality and NOT yet degraded -> rewrite and retry
    if quality_grade == "low" and not safe_degradation:
        logger.debug(
            "[route_after_quality_check] -> rewrite_query (low quality, can retry)"
        )
        return "rewrite_query"

    # Acceptable quality or safe degradation triggered -> faithfulness check
    if safe_degradation:
        logger.debug(
            f"[route_after_quality_check] -> faithfulness_check (safe_degradation=True after {rewrite_count} rewrites)"
        )
    else:
        logger.debug(
            f"[route_after_quality_check] -> faithfulness_check (quality acceptable: {quality_grade})"
        )
    return "faithfulness_check"


# ========================================
# Node: Query Rewrite
# ========================================


async def rewrite_query(state: CanvasRAGState) -> dict:
    """
    Query 重写节点 — Story 2.6 AC-2: LLM 语义改写 + 双策略

    第 1 次（rewrite_count=0）：添加澄清性上下文 + 领域关键词 + 明确意图
    第 2 次（rewrite_count=1）：完全不同角度重述 + 子问题分解 + 同义词替换

    3 秒超时保护，超时/异常降级为 jieba 关键词拼接或简单扩展。

    Returns:
        State updates:
        - messages: 添加重写后的 query
        - query_rewritten: True
        - rewrite_count: +1
        - original_query: 首次改写时保存原始查询
    """
    import asyncio

    current_rewrite_count = state.get("rewrite_count", 0)

    logger.debug(f"[rewrite_query] START - rewrite_count={current_rewrite_count}")

    messages = state.get("messages", [])
    if messages:
        last_msg = messages[-1]
        current_query = (
            last_msg.get("content", "")
            if isinstance(last_msg, dict)
            else getattr(last_msg, "content", "")
        )
    else:
        current_query = ""

    # Preserve original_query (only set on first rewrite)
    original_query = state.get("original_query") or current_query

    rewritten_query = current_query  # default: keep current

    # Story 2.6 AC-2: Dual-strategy LLM rewrite via LiteLLM
    llm_rewrite_success = False
    try:
        import litellm

        litellm.set_verbose = False

        # Read model from runtime config or environment
        from agentic_rag.config import DEFAULT_CONFIG

        rewrite_model = DEFAULT_CONFIG.get("rewrite_model", "gemini/gemini-2.0-flash")

        # Strategy-based prompt
        if current_rewrite_count == 0:
            # Strategy 1: Clarification + domain keywords + explicit intent
            rewrite_prompt = (
                "你是搜索优化专家。请保持核心意图，添加澄清上下文和领域关键词。"
                "只输出改写后的查询，不要解释。\n"
                f"原始查询：{current_query}"
            )
        else:
            # Strategy 2: Different angle + sub-question decomposition + synonyms
            rewrite_prompt = (
                "请从完全不同的角度重述此查询，或将其分解为更具体的子问题。"
                "使用同义词替换关键术语。只输出改写后的查询，不要解释。\n"
                f"原始查询：{current_query}"
            )

        # 3 秒超时保护
        response = await asyncio.wait_for(
            litellm.acompletion(
                model=rewrite_model,
                messages=[{"role": "user", "content": rewrite_prompt}],
                max_tokens=150,
                temperature=0.7,
            ),
            timeout=3.0,
        )

        llm_rewritten = response.choices[0].message.content.strip()
        if llm_rewritten and llm_rewritten != current_query:
            rewritten_query = llm_rewritten
            llm_rewrite_success = True

    except asyncio.TimeoutError:
        logger.warning(
            "[rewrite_query] LLM rewrite timed out (3s), using keyword fallback"
        )
    except ImportError:
        logger.warning("[rewrite_query] litellm not installed, using keyword fallback")
    except Exception as e:
        logger.warning(
            f"[rewrite_query] LLM rewrite failed: {e}, using keyword fallback"
        )

    # Fallback: jieba keyword extraction or simple expansion
    # Story 2-6 M6: `import jieba` does not auto-import `jieba.analyse`;
    # explicitly import `jieba.analyse` for extract_tags to work.
    if not llm_rewrite_success:
        try:
            import jieba.analyse

            keywords = jieba.analyse.extract_tags(current_query, topK=5)
            if keywords:
                rewritten_query = f"{current_query} {' '.join(keywords)}"
            else:
                rewritten_query = f"{current_query} 关键概念 定义 解释"
        except (ImportError, AttributeError):
            rewritten_query = f"{current_query} 关键概念 定义 解释"

    new_rewrite_count = current_rewrite_count + 1

    # Story 2.6 AC-6: Structured logging
    logger.info(
        f"[CRAG-RETRY] iteration={new_rewrite_count}, "
        f"original='{original_query[:60]}', rewritten='{rewritten_query[:60]}', "
        f"llm_success={llm_rewrite_success}, strategy={'clarify' if current_rewrite_count == 0 else 'rephrase'}"
    )

    return {
        "messages": [{"role": "user", "content": rewritten_query}],
        "query_rewritten": True,
        "rewrite_count": new_rewrite_count,
        "original_query": original_query,
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

    Graph Structure (五路并行检索 + faithfulness gate, Feature 2.2: textbook removed):
    ```
    START
      |
    fan_out_retrieval (conditional edge)
      |--- retrieve_graphiti (parallel)
      |--- retrieve_lancedb (parallel)
      |--- retrieve_multimodal (parallel) [Story 6.8]
      |--- retrieve_cross_canvas (parallel) [Story 23.4]
      +--- retrieve_vault_notes (parallel) [Vault Notes]
           | (converge)
         fuse_results (5-source weighted fusion)
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

    # Story 23.4: 跨Canvas关联检索节点 (Feature 2.2: textbook node removed per GDA-2)
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

    # Story 2.10: Multi-query rewrite (optional, before retrieval)
    builder.add_node("multi_query_rewrite", multi_query_rewrite_node)

    # Story 2.10: Context compression + mastery injection
    builder.add_node("compress_context", compress_context_node)

    # Story 7.1: Faithfulness check (RAGAS claim-level NLI) - last quality gate
    builder.add_node("faithfulness_check", faithfulness_check_node)

    # Quality control node
    builder.add_node("rewrite_query", rewrite_query)

    # ========================================
    # Add Edges
    # ========================================

    # START → multi_query_rewrite → fan_out_retrieval (parallel dispatch)
    builder.add_edge(START, "multi_query_rewrite")
    builder.add_conditional_edges(
        "multi_query_rewrite",
        fan_out_retrieval,
        # No path_map needed - Send objects specify destinations
    )

    # retrieve_graphiti → fuse_results
    # retrieve_lancedb → fuse_results
    # retrieve_multimodal → fuse_results (Story 6.8)
    # retrieve_cross_canvas → fuse_results (Story 23.4)
    # (All parallel nodes converge to fuse_results automatically)
    # Feature 2.2: retrieve_textbook edge removed per GDA-2
    builder.add_edge("retrieve_graphiti", "fuse_results")
    builder.add_edge("retrieve_lancedb", "fuse_results")
    builder.add_edge("retrieve_multimodal", "fuse_results")  # Story 6.8
    builder.add_edge("retrieve_cross_canvas", "fuse_results")  # Story 23.4
    builder.add_edge("retrieve_vault_notes", "fuse_results")  # Vault Notes

    # fuse_results → rerank_results
    builder.add_edge("fuse_results", "rerank_results")

    # rerank_results → check_quality
    builder.add_edge("rerank_results", "check_quality")

    # check_quality → route_after_quality_check (conditional)
    # Story 2.10: Routes to compress_context instead of faithfulness_check
    builder.add_conditional_edges(
        "check_quality",
        route_after_quality_check,
        {
            "rewrite_query": "rewrite_query",
            "faithfulness_check": "compress_context",
        },
    )

    # Story 2.10: compress_context → faithfulness_check
    builder.add_edge("compress_context", "faithfulness_check")

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
