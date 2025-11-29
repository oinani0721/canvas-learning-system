"""
Agentic RAG 核心节点实现

实现7个核心节点:
1. retrieve_graphiti: Graphiti知识图谱检索 (Story 12.1)
2. retrieve_lancedb: LanceDB向量检索 (Story 12.2)
3. fuse_results: 融合算法 (Story 12.7)
4. rerank_results: Reranking (Story 12.8)
5. check_quality: 质量评估 (Story 12.9)
6. retrieve_weak_concepts: Temporal Memory薄弱概念检索 (Story 12.4)
7. update_learning_behavior: 更新学习行为 (Story 12.4)

✅ Verified from LangGraph Skill:
- Nodes are async functions: async def node(state: State) -> dict
- Return dict with state updates
- Access runtime config via runtime parameter

Story 12.1-12.4 Update:
- ✅ 使用真实 GraphitiClient (Story 12.1)
- ✅ 使用真实 LanceDBClient (Story 12.2)
- ✅ 使用真实 TemporalClient (Story 12.4)
- ✅ 移除 placeholder mock 数据

Author: Canvas Learning System Team
Version: 1.2.0
Created: 2025-11-29
Updated: 2025-11-29
"""

import time
from typing import Any, Dict, List, Optional

from langgraph.runtime import Runtime

# ✅ Story 12.1-12.4: 使用真实客户端
from agentic_rag.clients import GraphitiClient, LanceDBClient, TemporalClient
from agentic_rag.config import CanvasRAGConfig
from agentic_rag.state import CanvasRAGState, SearchResult

# 全局客户端实例 (懒加载)
_graphiti_client: Optional[GraphitiClient] = None
_lancedb_client: Optional[LanceDBClient] = None
_temporal_client: Optional[TemporalClient] = None


async def _get_graphiti_client() -> GraphitiClient:
    """获取Graphiti客户端单例"""
    global _graphiti_client
    if _graphiti_client is None:
        _graphiti_client = GraphitiClient(
            timeout_ms=200,  # Story 12.1 AC 1.3: 200ms超时
            batch_size=10,
            enable_fallback=True
        )
        await _graphiti_client.initialize()
    return _graphiti_client


async def _get_lancedb_client() -> LanceDBClient:
    """获取LanceDB客户端单例"""
    global _lancedb_client
    if _lancedb_client is None:
        _lancedb_client = LanceDBClient(
            db_path="~/.lancedb",
            timeout_ms=400,  # Story 12.2 AC 2.3: P95 < 400ms
            batch_size=10,
            enable_fallback=True
        )
        await _lancedb_client.initialize()
    return _lancedb_client


async def _get_temporal_client() -> TemporalClient:
    """获取Temporal Memory客户端单例"""
    global _temporal_client
    if _temporal_client is None:
        _temporal_client = TemporalClient(
            db_path="learning_behavior.db",
            timeout_ms=50,  # Story 12.4 AC 4.5: < 50ms
            enable_fallback=True
        )
        await _temporal_client.initialize()
    return _temporal_client


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

    ✅ Story 12.1: 使用真实GraphitiClient
    - AC 1.1: 初始化Graphiti MCP客户端
    - AC 1.2: search_nodes()接口
    - AC 1.3: 200ms超时自动取消
    - AC 1.4: 结果转换为SearchResult

    Args:
        state: 当前状态 (包含messages, canvas_file等)
        runtime: 运行时配置

    Returns:
        State更新字典:
        - graphiti_results: List[SearchResult]
        - graphiti_latency_ms: float
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
    canvas_file = state.get("canvas_file")

    # ✅ Story 12.1: 使用真实Graphiti客户端
    try:
        client = await _get_graphiti_client()
        graphiti_results = await client.search_nodes(
            query=query,
            canvas_file=canvas_file,
            num_results=batch_size
        )
    except Exception:
        # Fallback: 返回空结果
        graphiti_results = []

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

    ✅ Story 12.2: 使用真实LanceDBClient
    - AC 2.1: LanceDB连接测试
    - AC 2.2: 向量检索接口
    - AC 2.3: P95 < 400ms
    - AC 2.4: 结果转换为SearchResult

    Args:
        state: 当前状态
        runtime: 运行时配置

    Returns:
        State更新字典:
        - lancedb_results: List[SearchResult]
        - lancedb_latency_ms: float
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
    canvas_file = state.get("canvas_file")

    # ✅ Story 12.2: 使用真实LanceDB客户端
    try:
        client = await _get_lancedb_client()

        # 搜索多个表并合并结果
        lancedb_results = await client.search_multiple_tables(
            query=query,
            canvas_file=canvas_file,
            num_results_per_table=batch_size // 2 + 1  # 每个表返回一半结果
        )

        # 限制总结果数
        lancedb_results = lancedb_results[:batch_size]

    except Exception:
        # Fallback: 返回空结果
        lancedb_results = []

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


# ========================================
# Node 6: Temporal Memory 薄弱概念检索
# ========================================

async def retrieve_weak_concepts(
    state: CanvasRAGState,
    runtime: Runtime[CanvasRAGConfig]
) -> Dict[str, Any]:
    """
    Temporal Memory 薄弱概念检索节点

    ✅ Story 12.4: Temporal Memory实现
    - AC 4.3: get_weak_concepts() 返回低稳定性概念
    - AC 4.5: 延迟 < 50ms

    用于检验白板生成时，获取需要重点复习的薄弱概念。

    Args:
        state: 当前状态 (包含canvas_file)
        runtime: 运行时配置

    Returns:
        State更新字典:
        - weak_concepts: List[Dict] 薄弱概念列表
        - temporal_latency_ms: float 延迟时间
    """
    start_time = time.perf_counter()

    canvas_file = state.get("canvas_file", "")
    limit = runtime.context.get("weak_concepts_limit", 10)

    try:
        client = await _get_temporal_client()
        weak_concepts = await client.get_weak_concepts(
            canvas_file=canvas_file,
            limit=limit
        )
    except Exception:
        # Fallback: 返回空结果
        weak_concepts = []

    latency_ms = (time.perf_counter() - start_time) * 1000

    return {
        "weak_concepts": weak_concepts,
        "temporal_latency_ms": latency_ms
    }


async def update_learning_behavior(
    state: CanvasRAGState,
    runtime: Runtime[CanvasRAGConfig]
) -> Dict[str, Any]:
    """
    更新学习行为节点

    ✅ Story 12.4: Temporal Memory实现
    - AC 4.2: 学习行为时序追踪
    - AC 4.4: update_behavior() 更新FSRS卡片

    在用户完成学习活动后更新FSRS卡片。

    Args:
        state: 当前状态 (包含concept, rating, canvas_file)
        runtime: 运行时配置

    Returns:
        State更新字典:
        - behavior_updated: bool 是否更新成功
        - updated_card: Dict FSRS卡片状态
    """
    concept = state.get("current_concept", "")
    rating = state.get("rating", 3)  # 默认Good
    canvas_file = state.get("canvas_file", "")
    session_id = state.get("session_id")

    if not concept or not canvas_file:
        return {
            "behavior_updated": False,
            "updated_card": {}
        }

    try:
        client = await _get_temporal_client()
        updated_card = await client.update_behavior(
            concept=concept,
            rating=rating,
            canvas_file=canvas_file,
            session_id=session_id
        )
        return {
            "behavior_updated": True,
            "updated_card": updated_card
        }
    except Exception:
        return {
            "behavior_updated": False,
            "updated_card": {}
        }
