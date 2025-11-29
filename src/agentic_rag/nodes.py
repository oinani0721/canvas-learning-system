"""
Agentic RAG 核心节点实现

实现5个核心节点:
1. retrieve_graphiti: Graphiti知识图谱检索
2. retrieve_lancedb: LanceDB向量检索
3. fuse_results: 融合算法
4. rerank_results: Reranking
5. check_quality: 质量评估

✅ Verified from LangGraph Skill:
- Nodes are async functions: async def node(state: State) -> dict
- Return dict with state updates
- Access runtime config via runtime parameter

Story 12.5 AC 5.3:
- ✅ 5个核心节点实现

Author: Canvas Learning System Team
Version: 1.0.0
Created: 2025-11-29
"""

import asyncio
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

from langgraph.runtime import Runtime

from agentic_rag.state import CanvasRAGState, SearchResult
from agentic_rag.config import CanvasRAGConfig


# ========================================
# Node 1: Graphiti知识图谱检索
# ========================================

async def retrieve_graphiti(
    state: CanvasRAGState,
    runtime: Runtime[CanvasRAGConfig]
) -> Dict[str, Any]:
    """
    Graphiti知识图谱检索节点

    ✅ Verified from LangGraph Skill:
    - Node signature: async def node(state: State, runtime: Runtime) -> dict
    - Return dict with state updates

    Args:
        state: 当前状态 (包含messages, canvas_file等)
        runtime: 运行时配置

    Returns:
        State更新字典:
        - graphiti_results: List[SearchResult]
        - retrieval_latency_ms: Dict[str, float]
    """
    start_time = time.perf_counter()

    # 获取查询 (从messages中提取最后一条用户消息)
    messages = state.get("messages", [])
    if messages:
        last_msg = messages[-1]
        query = last_msg.get("content", "") if isinstance(last_msg, dict) else getattr(last_msg, "content", "")
    else:
        query = ""

    # 获取配置
    batch_size = runtime.context.get("graphiti_batch_size") or runtime.context.get("retrieval_batch_size", 10)

    # TODO: Story 12.1 完成后，调用实际Graphiti client
    # ✅ Placeholder: 返回mock结果
    graphiti_results: List[SearchResult] = [
        {
            "doc_id": f"graphiti_{i}",
            "content": f"Graphiti result {i} for query: {query}",
            "score": 0.9 - i * 0.05,
            "metadata": {
                "source": "graphiti",
                "timestamp": datetime.now().isoformat(),
                "canvas_file": state.get("canvas_file"),
            }
        }
        for i in range(batch_size)
    ]

    latency_ms = (time.perf_counter() - start_time) * 1000

    return {
        "graphiti_results": graphiti_results,
        "graphiti_latency_ms": latency_ms
    }


# ========================================
# Node 2: LanceDB向量检索
# ========================================

async def retrieve_lancedb(
    state: CanvasRAGState,
    runtime: Runtime[CanvasRAGConfig]
) -> Dict[str, Any]:
    """
    LanceDB向量检索节点

    ✅ Verified from LangGraph Skill:
    - Async node pattern

    Args:
        state: 当前状态
        runtime: 运行时配置

    Returns:
        State更新字典:
        - lancedb_results: List[SearchResult]
        - retrieval_latency_ms: Dict[str, float]
    """
    start_time = time.perf_counter()

    # 获取查询
    messages = state.get("messages", [])
    if messages:
        last_msg = messages[-1]
        query = last_msg.get("content", "") if isinstance(last_msg, dict) else getattr(last_msg, "content", "")
    else:
        query = ""

    # 获取配置
    batch_size = runtime.context.get("lancedb_batch_size") or runtime.context.get("retrieval_batch_size", 10)

    # TODO: Story 12.3 完成后，调用实际LanceDB client
    # ✅ Placeholder: 返回mock结果
    lancedb_results: List[SearchResult] = [
        {
            "doc_id": f"lancedb_{i}",
            "content": f"LanceDB result {i} for query: {query}",
            "score": 0.85 - i * 0.05,
            "metadata": {
                "source": "lancedb",
                "timestamp": datetime.now().isoformat(),
                "canvas_file": state.get("canvas_file"),
            }
        }
        for i in range(batch_size)
    ]

    latency_ms = (time.perf_counter() - start_time) * 1000

    return {
        "lancedb_results": lancedb_results,
        "lancedb_latency_ms": latency_ms
    }


# ========================================
# Node 3: 融合算法
# ========================================

async def fuse_results(
    state: CanvasRAGState,
    runtime: Runtime[CanvasRAGConfig]
) -> Dict[str, Any]:
    """
    融合算法节点

    根据fusion_strategy选择融合算法:
    - rrf: Reciprocal Rank Fusion
    - weighted: 加权融合 (检验白板: 70% Graphiti + 30% LanceDB)
    - cascade: 级联融合 (Tier 1: Graphiti, Tier 2: LanceDB)

    ✅ Verified from LangGraph Skill:
    - Access runtime config: runtime.context["fusion_strategy"]

    Args:
        state: 当前状态
        runtime: 运行时配置

    Returns:
        State更新字典:
        - fused_results: List[SearchResult]
    """
    start_time = time.perf_counter()

    graphiti_results = state.get("graphiti_results", [])
    lancedb_results = state.get("lancedb_results", [])

    fusion_strategy = runtime.context.get("fusion_strategy", "rrf")

    if fusion_strategy == "rrf":
        # RRF算法: score = Σ(1/(k+rank)), k=60
        fused_results = _fuse_rrf(graphiti_results, lancedb_results)
    elif fusion_strategy == "weighted":
        # Weighted融合: score = alpha * norm(graphiti) + beta * norm(lancedb)
        alpha = 0.7 if state.get("is_review_canvas") else 0.5
        beta = 1.0 - alpha
        fused_results = _fuse_weighted(graphiti_results, lancedb_results, alpha, beta)
    elif fusion_strategy == "cascade":
        # Cascade融合: Tier 1 → Tier 2
        fused_results = _fuse_cascade(graphiti_results, lancedb_results)
    else:
        raise ValueError(f"Unknown fusion_strategy: {fusion_strategy}")

    latency_ms = (time.perf_counter() - start_time) * 1000

    return {
        "fused_results": fused_results,
        "fusion_latency_ms": latency_ms
    }


def _fuse_rrf(
    graphiti_results: List[SearchResult],
    lancedb_results: List[SearchResult],
    k: int = 60
) -> List[SearchResult]:
    """
    RRF (Reciprocal Rank Fusion) 算法

    score = Σ(1/(k+rank))

    TODO: Story 12.7 完成详细实现
    """
    # Placeholder: 简单合并并排序
    all_results = graphiti_results + lancedb_results
    all_results.sort(key=lambda x: x["score"], reverse=True)
    return all_results[:10]


def _fuse_weighted(
    graphiti_results: List[SearchResult],
    lancedb_results: List[SearchResult],
    alpha: float,
    beta: float
) -> List[SearchResult]:
    """
    Weighted融合算法

    score = alpha * norm(graphiti) + beta * norm(lancedb)

    TODO: Story 12.7 完成详细实现
    """
    # Placeholder: 简单合并并排序
    all_results = graphiti_results + lancedb_results
    all_results.sort(key=lambda x: x["score"], reverse=True)
    return all_results[:10]


def _fuse_cascade(
    graphiti_results: List[SearchResult],
    lancedb_results: List[SearchResult],
    tier1_threshold: int = 5,
    score_threshold: float = 0.7
) -> List[SearchResult]:
    """
    Cascade融合算法

    Tier 1: 仅Graphiti
    Tier 2触发条件: len(Tier1) < 5 OR max(score) < 0.7

    TODO: Story 12.7 完成详细实现
    """
    # Placeholder: 使用Graphiti结果
    if len(graphiti_results) < tier1_threshold:
        return (graphiti_results + lancedb_results)[:10]
    return graphiti_results[:10]


# ========================================
# Node 4: Reranking
# ========================================

async def rerank_results(
    state: CanvasRAGState,
    runtime: Runtime[CanvasRAGConfig]
) -> Dict[str, Any]:
    """
    Reranking节点

    根据reranking_strategy选择Reranker:
    - local: bge-reranker-base (本地Cross-Encoder)
    - cohere: Cohere Rerank API
    - hybrid_auto: 自动选择 (检验白板→Cohere, 其他→Local)

    ✅ Verified from LangGraph Skill:
    - Access runtime config

    Args:
        state: 当前状态
        runtime: 运行时配置

    Returns:
        State更新字典:
        - reranked_results: List[SearchResult]
    """
    start_time = time.perf_counter()

    fused_results = state.get("fused_results", [])
    reranking_strategy = runtime.context.get("reranking_strategy", "hybrid_auto")

    # 自动选择策略
    if reranking_strategy == "hybrid_auto":
        if state.get("is_review_canvas"):
            reranking_strategy = "cohere"
        else:
            reranking_strategy = "local"

    if reranking_strategy == "local":
        # Local Cross-Encoder reranking
        reranked_results = await _rerank_local(fused_results, state)
    elif reranking_strategy == "cohere":
        # Cohere API reranking
        reranked_results = await _rerank_cohere(fused_results, state)
    else:
        raise ValueError(f"Unknown reranking_strategy: {reranking_strategy}")

    latency_ms = (time.perf_counter() - start_time) * 1000

    return {
        "reranked_results": reranked_results,
        "reranking_latency_ms": latency_ms
    }


async def _rerank_local(
    results: List[SearchResult],
    state: CanvasRAGState
) -> List[SearchResult]:
    """
    Local Cross-Encoder Reranking

    TODO: Story 12.8 完成详细实现 (使用bge-reranker-base)
    """
    # Placeholder: 保持原有排序
    return results


async def _rerank_cohere(
    results: List[SearchResult],
    state: CanvasRAGState
) -> List[SearchResult]:
    """
    Cohere API Reranking

    TODO: Story 12.8 完成详细实现 (调用Cohere rerank API)
    """
    # Placeholder: 保持原有排序
    return results


# ========================================
# Node 5: 质量评估
# ========================================

async def check_quality(
    state: CanvasRAGState,
    runtime: Runtime[CanvasRAGConfig]
) -> Dict[str, Any]:
    """
    质量评估节点

    评估reranked_results的质量，分级:
    - high: Top-3平均分 ≥ 0.7
    - medium: Top-3平均分 0.5-0.7
    - low: Top-3平均分 < 0.5

    ✅ Verified from LangGraph Skill:
    - Return dict with quality_grade

    Args:
        state: 当前状态
        runtime: 运行时配置

    Returns:
        State更新字典:
        - quality_grade: Literal["high", "medium", "low"]
    """
    reranked_results = state.get("reranked_results", [])

    if not reranked_results:
        return {"quality_grade": "low"}

    # 计算Top-3平均分
    top3_scores = [r["score"] for r in reranked_results[:3]]
    avg_score = sum(top3_scores) / len(top3_scores) if top3_scores else 0.0

    quality_threshold_high = runtime.context.get("quality_threshold", 0.7)
    quality_threshold_medium = quality_threshold_high - 0.2  # 0.5

    if avg_score >= quality_threshold_high:
        quality_grade = "high"
    elif avg_score >= quality_threshold_medium:
        quality_grade = "medium"
    else:
        quality_grade = "low"

    return {"quality_grade": quality_grade}
