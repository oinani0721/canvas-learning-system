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

Story 23.3 Update:
- ✅ 添加DEBUG日志 (AC 1-5)
- ✅ 节点入口/出口日志
- ✅ 执行时间监控

Author: Canvas Learning System Team
Version: 1.3.0
Created: 2025-11-29
Updated: 2025-12-12
"""

import logging
import time
from typing import Any, Dict, List, Optional

from langgraph.runtime import Runtime

# ✅ Story 23.3: 配置节点日志
logger = logging.getLogger(__name__)

# ✅ Story 12.1-12.4: 使用真实客户端
from agentic_rag.clients import GraphitiClient, LanceDBClient, TemporalClient  # noqa: E402
from agentic_rag.config import CanvasRAGConfig  # noqa: E402
from agentic_rag.state import CanvasRAGState, SearchResult  # noqa: E402

# 全局客户端实例 (懒加载)
_graphiti_client: Optional[GraphitiClient] = None
_lancedb_client: Optional[LanceDBClient] = None
_temporal_client: Optional[TemporalClient] = None


def _safe_get_config(
    runtime: Runtime[CanvasRAGConfig],
    key: str,
    default: Any = None
) -> Any:
    """
    Safely access runtime context with None protection.

    Story 12.K.2: Prevents 'NoneType' object has no attribute 'get' errors
    when runtime.context is None (e.g., when config is not properly passed).

    Args:
        runtime: LangGraph Runtime object
        key: Config key to retrieve
        default: Default value if key not found or context is None

    Returns:
        Config value or default
    """
    if runtime is None:
        logger.warning(f"[_safe_get_config] runtime is None, using default for '{key}'")
        return default
    if runtime.context is None:
        logger.warning(f"[_safe_get_config] runtime.context is None, using default for '{key}'")
        return default
    return runtime.context.get(key, default)


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

    # ✅ Story 23.3: 节点入口日志
    logger.debug(f"[retrieve_graphiti] START - query='{query[:50]}...' canvas={state.get('canvas_file')}")

    # 获取配置 (Story 12.K.2: Safe config access)
    batch_size = _safe_get_config(runtime, "graphiti_batch_size") or _safe_get_config(runtime, "retrieval_batch_size", 10)
    canvas_file = state.get("canvas_file")

    # ✅ Story 12.1: 使用真实Graphiti客户端
    try:
        client = await _get_graphiti_client()
        graphiti_results = await client.search_nodes(
            query=query,
            canvas_file=canvas_file,
            num_results=batch_size
        )
    except Exception as e:
        # Fallback: 返回空结果
        logger.warning(f"[retrieve_graphiti] Fallback triggered: {e}")
        graphiti_results = []

    latency_ms = (time.perf_counter() - start_time) * 1000

    # ✅ Story 23.3: 节点出口日志
    logger.debug(f"[retrieve_graphiti] END - results={len(graphiti_results)}, latency={latency_ms:.2f}ms")

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

    # ✅ Story 23.3: 节点入口日志
    logger.debug(f"[retrieve_lancedb] START - query='{query[:50]}...' canvas={state.get('canvas_file')}")

    # 获取配置 (Story 12.K.2: Safe config access)
    batch_size = _safe_get_config(runtime, "lancedb_batch_size") or _safe_get_config(runtime, "retrieval_batch_size", 10)
    canvas_file = state.get("canvas_file")
    subject = state.get("subject")

    # ✅ Story 12.2: 使用真实LanceDB客户端
    try:
        client = await _get_lancedb_client()

        # 搜索多个表并合并结果
        lancedb_results = await client.search_multiple_tables(
            query=query,
            canvas_file=canvas_file,
            subject=subject,
            num_results_per_table=batch_size // 2 + 1  # 每个表返回一半结果
        )

        # 限制总结果数
        lancedb_results = lancedb_results[:batch_size]

    except Exception as e:
        # Fallback: 返回空结果
        logger.warning(f"[retrieve_lancedb] Fallback triggered: {e}")
        lancedb_results = []

    latency_ms = (time.perf_counter() - start_time) * 1000

    # ✅ Story 23.3: 节点出口日志
    logger.debug(f"[retrieve_lancedb] END - results={len(lancedb_results)}, latency={latency_ms:.2f}ms")

    return {
        "lancedb_results": lancedb_results,
        "lancedb_latency_ms": latency_ms
    }


# ========================================
# Node 3: 融合算法 (Story 23.4 扩展为5源融合)
# ========================================

# Story 23.4: 默认权重配置
DEFAULT_SOURCE_WEIGHTS = {
    "graphiti": 0.25,
    "lancedb": 0.25,
    "textbook": 0.20,
    "cross_canvas": 0.15,
    "multimodal": 0.15
}


async def fuse_results(
    state: CanvasRAGState,
    runtime: Runtime[CanvasRAGConfig]
) -> Dict[str, Any]:
    """
    融合算法节点 (Story 23.4: 五源加权融合)

    根据fusion_strategy选择融合算法:
    - rrf: Reciprocal Rank Fusion (5源)
    - weighted: 加权融合 (使用source_weights配置)
    - cascade: 级联融合 (Tier 1: Graphiti, Tier 2: others)

    ✅ Verified from LangGraph Skill:
    - Access runtime config: runtime.context["fusion_strategy"]

    ✅ Story 23.4:
    - AC 4: 支持数据源权重配置
    - AC 5: 融合结果包含source标注

    Args:
        state: 当前状态
        runtime: 运行时配置

    Returns:
        State更新字典:
        - fused_results: List[SearchResult]
    """
    start_time = time.perf_counter()

    # Story 23.4: 获取5个数据源的结果
    graphiti_results = state.get("graphiti_results", [])
    lancedb_results = state.get("lancedb_results", [])
    # ✅ Story 23.3: 获取多模态结果
    multimodal_results = state.get("multimodal_results", [])
    # Story 23.4: 获取教材和跨Canvas结果
    textbook_results = state.get("textbook_results", [])
    cross_canvas_results = state.get("cross_canvas_results", [])

    # 获取配置 (Story 12.K.2: Safe config access)
    fusion_strategy = _safe_get_config(runtime, "fusion_strategy", "rrf")
    source_weights = _safe_get_config(runtime, "source_weights", DEFAULT_SOURCE_WEIGHTS)
    time_decay_factor = _safe_get_config(runtime, "time_decay_factor", 0.05)

    # Story 23.4 AC 2: 对Graphiti结果应用时间衰减
    graphiti_results = _apply_time_decay(graphiti_results, time_decay_factor)

    # 构建5源结果字典
    all_source_results = {
        "graphiti": graphiti_results,
        "lancedb": lancedb_results,
        "multimodal": multimodal_results,
        "textbook": textbook_results,
        "cross_canvas": cross_canvas_results
    }

    # ✅ Story 23.3: 节点入口日志
    logger.debug(
        f"[fuse_results] START - strategy={fusion_strategy}, "
        f"graphiti={len(graphiti_results)}, lancedb={len(lancedb_results)}, "
        f"multimodal={len(multimodal_results)}"
    )

    # ✅ Story 23.3 AC 3: 多模态结果已包含在 all_source_results 中
    # Story 23.4: 使用多源融合，所有结果通过 all_source_results 处理

    if fusion_strategy == "rrf":
        # RRF算法: score = Σ(1/(k+rank)), k=60
        # Story 23.4: 使用多源融合函数
        fused_results = _fuse_rrf_multi_source(all_source_results)
    elif fusion_strategy == "weighted":
        # Story 23.4 AC 4: Weighted融合使用source_weights
        fused_results = _fuse_weighted_multi_source(all_source_results, source_weights)
    elif fusion_strategy == "cascade":
        # Cascade融合: Tier 1 → Tier 2
        fused_results = _fuse_cascade_multi_source(all_source_results)
    else:
        raise ValueError(f"Unknown fusion_strategy: {fusion_strategy}")

    latency_ms = (time.perf_counter() - start_time) * 1000

    # ✅ Story 23.3: 节点出口日志
    logger.debug(f"[fuse_results] END - strategy={fusion_strategy}, results={len(fused_results)}, latency={latency_ms:.2f}ms")

    return {
        "fused_results": fused_results,
        "fusion_latency_ms": latency_ms
    }


def _apply_time_decay(
    results: List[SearchResult],
    decay_factor: float = 0.05
) -> List[SearchResult]:
    """
    Story 23.4 AC 2: 对学习历史结果应用时间衰减

    公式: weight = base_score * exp(-decay * days_ago)

    Args:
        results: 检索结果列表
        decay_factor: 时间衰减因子 (默认0.05)

    Returns:
        应用时间衰减后的结果
    """
    import math
    from datetime import datetime, timezone

    decayed_results = []
    now = datetime.now(timezone.utc)

    for r in results:
        result = dict(r)  # 创建副本
        metadata = result.get("metadata", {})

        # 获取时间戳 (如果有)
        timestamp_str = metadata.get("timestamp") or metadata.get("created_at")
        if timestamp_str:
            try:
                # 尝试解析ISO格式时间
                if isinstance(timestamp_str, str):
                    timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                else:
                    timestamp = timestamp_str

                # 计算天数差
                delta = now - timestamp
                days_ago = delta.days

                # 应用衰减公式
                original_score = result.get("score", 0.5)
                decay_weight = math.exp(-decay_factor * days_ago)
                result["score"] = original_score * decay_weight

                # 记录衰减信息
                if "metadata" not in result:
                    result["metadata"] = {}
                result["metadata"]["time_decay_applied"] = True
                result["metadata"]["days_ago"] = days_ago
                result["metadata"]["decay_weight"] = decay_weight

            except (ValueError, TypeError):
                # 解析失败，保持原分数
                pass

        decayed_results.append(result)

    return decayed_results


def _fuse_rrf_multi_source(
    all_source_results: Dict[str, List[SearchResult]],
    k: int = 60
) -> List[SearchResult]:
    """
    RRF (Reciprocal Rank Fusion) 多源算法

    score = Σ(1/(k+rank))

    Story 23.4: 支持5个数据源
    """
    # 收集所有文档及其rank
    doc_scores: Dict[str, float] = {}
    doc_data: Dict[str, SearchResult] = {}

    for source_name, results in all_source_results.items():
        for rank, result in enumerate(results, start=1):
            doc_id = result.get("doc_id", f"{source_name}_{rank}")

            # RRF分数累加
            rrf_score = 1.0 / (k + rank)
            doc_scores[doc_id] = doc_scores.get(doc_id, 0.0) + rrf_score

            # 保存文档数据 (首次出现)
            if doc_id not in doc_data:
                doc_data[doc_id] = dict(result)
                # Story 23.4 AC 5: 确保source标注
                if "metadata" not in doc_data[doc_id]:
                    doc_data[doc_id]["metadata"] = {}
                if "source" not in doc_data[doc_id]["metadata"]:
                    doc_data[doc_id]["metadata"]["source"] = source_name

    # 按RRF分数排序
    sorted_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)

    # 构建最终结果
    fused_results = []
    for doc_id, rrf_score in sorted_docs[:10]:
        result = doc_data[doc_id]
        result["score"] = rrf_score  # 使用RRF分数
        result["metadata"]["fusion_method"] = "rrf"
        fused_results.append(result)

    return fused_results


def _fuse_weighted_multi_source(
    all_source_results: Dict[str, List[SearchResult]],
    source_weights: Dict[str, float]
) -> List[SearchResult]:
    """
    Story 23.4 AC 4: 加权融合算法 (多源)

    score = Σ(weight[source] * norm(score))

    支持source_weights配置:
    - graphiti: 0.25
    - lancedb: 0.25
    - textbook: 0.20
    - cross_canvas: 0.15
    - multimodal: 0.15
    """
    doc_scores: Dict[str, float] = {}
    doc_data: Dict[str, SearchResult] = {}

    for source_name, results in all_source_results.items():
        weight = source_weights.get(source_name, 0.0)

        # 归一化源内分数 (min-max归一化)
        if results:
            scores = [r.get("score", 0.0) for r in results]
            min_score = min(scores)
            max_score = max(scores)
            score_range = max_score - min_score if max_score > min_score else 1.0

            for result in results:
                doc_id = result.get("doc_id", f"{source_name}_{id(result)}")

                # 归一化分数
                original_score = result.get("score", 0.0)
                normalized_score = (original_score - min_score) / score_range

                # 加权累加
                weighted_score = weight * normalized_score
                doc_scores[doc_id] = doc_scores.get(doc_id, 0.0) + weighted_score

                # 保存文档数据
                if doc_id not in doc_data:
                    doc_data[doc_id] = dict(result)
                    if "metadata" not in doc_data[doc_id]:
                        doc_data[doc_id]["metadata"] = {}
                    if "source" not in doc_data[doc_id]["metadata"]:
                        doc_data[doc_id]["metadata"]["source"] = source_name

    # 按加权分数排序
    sorted_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)

    # 构建最终结果
    fused_results = []
    for doc_id, weighted_score in sorted_docs[:10]:
        result = doc_data[doc_id]
        result["score"] = weighted_score
        result["metadata"]["fusion_method"] = "weighted"
        fused_results.append(result)

    return fused_results


def _fuse_cascade_multi_source(
    all_source_results: Dict[str, List[SearchResult]],
    tier1_threshold: int = 5,
    score_threshold: float = 0.7
) -> List[SearchResult]:
    """
    Cascade融合算法 (多源)

    Tier 1: Graphiti + Textbook (权威来源)
    Tier 2触发条件: len(Tier1) < 5 OR max(score) < 0.7

    Story 23.4: 教材作为权威来源加入Tier1
    """
    # Tier 1: 权威来源 (Graphiti + Textbook)
    tier1_results = []
    for source in ["graphiti", "textbook"]:
        results = all_source_results.get(source, [])
        for r in results:
            result = dict(r)
            if "metadata" not in result:
                result["metadata"] = {}
            if "source" not in result["metadata"]:
                result["metadata"]["source"] = source
            result["metadata"]["fusion_tier"] = 1
            tier1_results.append(result)

    # 检查是否需要Tier 2
    tier1_scores = [r.get("score", 0.0) for r in tier1_results]
    max_tier1_score = max(tier1_scores) if tier1_scores else 0.0

    if len(tier1_results) >= tier1_threshold and max_tier1_score >= score_threshold:
        # Tier 1足够，直接返回
        tier1_results.sort(key=lambda x: x["score"], reverse=True)
        for r in tier1_results:
            r["metadata"]["fusion_method"] = "cascade"
        return tier1_results[:10]

    # Tier 2: 补充来源 (LanceDB, Multimodal, CrossCanvas)
    tier2_results = []
    for source in ["lancedb", "multimodal", "cross_canvas"]:
        results = all_source_results.get(source, [])
        for r in results:
            result = dict(r)
            if "metadata" not in result:
                result["metadata"] = {}
            if "source" not in result["metadata"]:
                result["metadata"]["source"] = source
            result["metadata"]["fusion_tier"] = 2
            tier2_results.append(result)

    # 合并并排序
    all_results = tier1_results + tier2_results
    all_results.sort(key=lambda x: x["score"], reverse=True)

    for r in all_results:
        r["metadata"]["fusion_method"] = "cascade"

    return all_results[:10]


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
    # Story 12.K.2: Safe config access
    reranking_strategy = _safe_get_config(runtime, "reranking_strategy", "hybrid_auto")

    # ✅ Story 23.3: 节点入口日志
    logger.debug(f"[rerank_results] START - strategy={reranking_strategy}, input_count={len(fused_results)}")

    # 自动选择策略
    if reranking_strategy == "hybrid_auto":
        if state.get("is_review_canvas"):
            reranking_strategy = "cohere"
        else:
            reranking_strategy = "local"
        logger.debug(f"[rerank_results] hybrid_auto resolved to: {reranking_strategy}")

    if reranking_strategy == "local":
        # Local Cross-Encoder reranking
        reranked_results = await _rerank_local(fused_results, state)
    elif reranking_strategy == "cohere":
        # Cohere API reranking
        reranked_results = await _rerank_cohere(fused_results, state)
    else:
        raise ValueError(f"Unknown reranking_strategy: {reranking_strategy}")

    latency_ms = (time.perf_counter() - start_time) * 1000

    # ✅ Story 23.3: 节点出口日志
    logger.debug(f"[rerank_results] END - strategy={reranking_strategy}, results={len(reranked_results)}, latency={latency_ms:.2f}ms")

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
    rewrite_count = state.get("rewrite_count", 0)

    # ✅ Story 23.3: 节点入口日志
    logger.debug(f"[check_quality] START - results_count={len(reranked_results)}, rewrite_count={rewrite_count}")

    if not reranked_results:
        logger.debug("[check_quality] END - empty results, grade=low")
        return {"quality_grade": "low"}

    # 计算Top-3平均分
    top3_scores = [r["score"] for r in reranked_results[:3]]
    avg_score = sum(top3_scores) / len(top3_scores) if top3_scores else 0.0

    # Story 12.K.2: Safe config access
    quality_threshold_high = _safe_get_config(runtime, "quality_threshold", 0.7)
    quality_threshold_medium = quality_threshold_high - 0.2  # 0.5

    if avg_score >= quality_threshold_high:
        quality_grade = "high"
    elif avg_score >= quality_threshold_medium:
        quality_grade = "medium"
    else:
        quality_grade = "low"

    # ✅ Story 23.3: 节点出口日志
    logger.debug(f"[check_quality] END - avg_score={avg_score:.3f}, grade={quality_grade}")

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
    # Story 12.K.2: Safe config access
    limit = _safe_get_config(runtime, "weak_concepts_limit", 10)

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
