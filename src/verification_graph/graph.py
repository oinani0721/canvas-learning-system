"""
LangGraph StateGraph构建 - Verification Canvas 2.0

Epic 24: Verification Canvas Redesign (智能引导模式)
Story 24.1: Smart Guidance Architecture Design
Story 24.2: Socratic Q&A Flow (integration)

构建Socratic式问答循环的StateGraph，包含:
- 问题生成节点 (Socratic templates)
- 等待用户回答节点
- 回答评估节点 (scoring integration)
- 质量路由
- 提示引导节点 (dynamic agent selection)

✅ Verified from LangGraph Context7 (topic: StateGraph):
- Pattern: StateGraph(State) construction
- add_node(name, function)
- add_edge for sequential flow
- add_conditional_edges for routing
- compile() to build graph

✅ Verified from agentic_rag/state_graph.py (项目现有模式):
- 使用builder模式构建StateGraph
- 条件边使用Literal返回值
- RetryPolicy用于节点重试

Story 24.1 AC:
- ✅ AC 2: 实现 LangGraph StateGraph 骨架
- ✅ AC 3: 支持概念队列管理 (通过state)
- ✅ AC 4: 支持进度状态跟踪 (通过state)

Story 24.2 AC:
- ✅ AC 1: 问题生成逻辑 (nodes.py)
- ✅ AC 2: 回答评估逻辑 (nodes.py)
- ✅ AC 3: 提示引导逻辑 (nodes.py)
- ✅ AC 4: 概念完成逻辑 (nodes.py)

Author: Canvas Learning System Team
Version: 1.1.0
Created: 2025-12-13
Updated: 2025-12-13 (Story 24.2 integration)
"""

import logging
from typing import Literal

from langgraph.graph import END, START, StateGraph

from verification_graph.nodes import (
    advance_to_next_concept,
    complete_verification,
    evaluate_answer,
    finalize_concept,
    generate_question,
    provide_hint,
    wait_for_answer,
)
from verification_graph.state import VerificationState

# ✅ Story 24.1: 配置日志
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Node Functions imported from nodes.py (Story 24.2)
# ═══════════════════════════════════════════════════════════════════════════════
# generate_question - 生成Socratic式引导问题
# wait_for_answer - 等待用户回答
# evaluate_answer - 评估回答质量
# provide_hint - 提供动态Agent引导提示
# finalize_concept - 完成概念验证
# advance_to_next_concept - 前进到下一概念
# complete_verification - 完成验证会话


# ═══════════════════════════════════════════════════════════════════════════════
# Conditional Edge: Quality-based Routing
# ═══════════════════════════════════════════════════════════════════════════════

def route_after_evaluation(state: VerificationState) -> Literal["provide_hint", "finalize_concept"]:
    """
    评估后路由

    根据回答质量和提示次数决定下一步：
    - 高分(85+) 或 已达最大提示次数: → finalize_concept
    - 低分且还有提示机会: → provide_hint

    ✅ Verified from LangGraph Context7 (topic: conditional edges):
    - Routing function returns Literal of possible destinations

    Returns:
        "provide_hint" or "finalize_concept"
    """
    answer_quality = state.get("answer_quality", "wrong")
    answer_score = state.get("answer_score", 0.0)
    hints_given = state.get("hints_given", 0)
    max_hints = state.get("max_hints", 3)
    user_action = state.get("user_action", "continue")

    logger.debug(f"[route_after_evaluation] quality={answer_quality}, score={answer_score}, hints={hints_given}/{max_hints}")

    # 用户选择跳过
    if user_action == "skip":
        logger.debug("[route_after_evaluation] → finalize_concept (user skipped)")
        return "finalize_concept"

    # 高分，掌握
    if answer_quality == "excellent" or answer_score >= 85:
        logger.debug("[route_after_evaluation] → finalize_concept (mastered)")
        return "finalize_concept"

    # 已达最大提示次数
    if hints_given >= max_hints:
        logger.debug("[route_after_evaluation] → finalize_concept (max hints reached)")
        return "finalize_concept"

    # 还有提示机会，继续引导
    logger.debug("[route_after_evaluation] → provide_hint (needs guidance)")
    return "provide_hint"


def route_after_hint(state: VerificationState) -> Literal["wait_for_answer", "finalize_concept"]:
    """
    提示后路由

    提供提示后，通常返回等待用户重新回答。
    如果用户选择放弃，则finalize。

    Returns:
        "wait_for_answer" or "finalize_concept"
    """
    user_action = state.get("user_action", "continue")

    if user_action == "end" or user_action == "skip":
        logger.debug("[route_after_hint] → finalize_concept (user action)")
        return "finalize_concept"

    logger.debug("[route_after_hint] → wait_for_answer (continue guidance)")
    return "wait_for_answer"


def route_after_finalize(state: VerificationState) -> Literal["advance_to_next_concept", "complete_verification"]:
    """
    概念完成后路由

    检查是否还有更多概念需要验证。

    Returns:
        "advance_to_next_concept" or "complete_verification"
    """
    concept_queue = state.get("concept_queue", [])
    current_concept_idx = state.get("current_concept_idx", 0)
    user_action = state.get("user_action", "continue")

    # 用户选择结束
    if user_action == "end":
        logger.debug("[route_after_finalize] → complete_verification (user ended)")
        return "complete_verification"

    # 还有更多概念
    if current_concept_idx + 1 < len(concept_queue):
        logger.debug("[route_after_finalize] → advance_to_next_concept")
        return "advance_to_next_concept"

    # 所有概念已完成
    logger.debug("[route_after_finalize] → complete_verification (all done)")
    return "complete_verification"


# ═══════════════════════════════════════════════════════════════════════════════
# Build StateGraph
# ═══════════════════════════════════════════════════════════════════════════════

def build_verification_graph() -> StateGraph:
    """
    构建Verification Canvas StateGraph

    ✅ Verified from LangGraph Context7:
    - Pattern: StateGraph construction
    - add_node, add_edge, add_conditional_edges
    - compile()

    Graph Structure (Socratic Loop):
    ```
    START
      ↓
    generate_question
      ↓
    wait_for_answer (checkpoint - external input)
      ↓
    evaluate_answer
      ↓
    route_after_evaluation (conditional)
      ├──→ provide_hint (if needs guidance)
      │      ↓
      │    route_after_hint (conditional)
      │      ├──→ wait_for_answer (loop back)
      │      └──→ finalize_concept (if give up)
      │
      └──→ finalize_concept (if mastered or max hints)
             ↓
           route_after_finalize (conditional)
             ├──→ advance_to_next_concept → generate_question (loop)
             └──→ complete_verification → END
    ```

    Returns:
        StateGraph builder (not compiled)
    """
    # 创建StateGraph
    builder = StateGraph(VerificationState)

    # ════════════════════════════════════════════════════════════════════════════
    # Add Nodes
    # ════════════════════════════════════════════════════════════════════════════

    builder.add_node("generate_question", generate_question)
    builder.add_node("wait_for_answer", wait_for_answer)
    builder.add_node("evaluate_answer", evaluate_answer)
    builder.add_node("provide_hint", provide_hint)
    builder.add_node("finalize_concept", finalize_concept)
    builder.add_node("advance_to_next_concept", advance_to_next_concept)
    builder.add_node("complete_verification", complete_verification)

    # ════════════════════════════════════════════════════════════════════════════
    # Add Edges
    # ════════════════════════════════════════════════════════════════════════════

    # START → generate_question
    builder.add_edge(START, "generate_question")

    # generate_question → wait_for_answer
    builder.add_edge("generate_question", "wait_for_answer")

    # wait_for_answer → evaluate_answer
    builder.add_edge("wait_for_answer", "evaluate_answer")

    # evaluate_answer → route_after_evaluation (conditional)
    builder.add_conditional_edges(
        "evaluate_answer",
        route_after_evaluation,
        {
            "provide_hint": "provide_hint",
            "finalize_concept": "finalize_concept",
        }
    )

    # provide_hint → route_after_hint (conditional)
    builder.add_conditional_edges(
        "provide_hint",
        route_after_hint,
        {
            "wait_for_answer": "wait_for_answer",
            "finalize_concept": "finalize_concept",
        }
    )

    # finalize_concept → route_after_finalize (conditional)
    builder.add_conditional_edges(
        "finalize_concept",
        route_after_finalize,
        {
            "advance_to_next_concept": "advance_to_next_concept",
            "complete_verification": "complete_verification",
        }
    )

    # advance_to_next_concept → generate_question (loop back)
    builder.add_edge("advance_to_next_concept", "generate_question")

    # complete_verification → END
    builder.add_edge("complete_verification", END)

    return builder


# ═══════════════════════════════════════════════════════════════════════════════
# Compile Graph
# ═══════════════════════════════════════════════════════════════════════════════

# Build and compile the graph
_builder = build_verification_graph()
verification_graph = _builder.compile()

# Export for use
__all__ = ["verification_graph", "build_verification_graph"]
