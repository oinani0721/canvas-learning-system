"""
RRF (Reciprocal Rank Fusion) 融合算法

✅ Verified from docs/architecture/FUSION-ALGORITHM-DESIGN.md Section 2

公式: RRF_score(d) = Σ(1/(k+rank_i(d)))
其中:
    k = 60 (常数，防止高排名文档分数过高)
    rank_i(d) = 文档d在源i中的排名 (从1开始)

Author: Canvas Learning System Team
Version: 1.0.0
Created: 2025-11-29
"""

from collections import defaultdict
from typing import Any, Dict, List, Optional

from .unified_result import ResultType, SearchSource, UnifiedResult

# ✅ Verified from FUSION-ALGORITHM-DESIGN.md - k=60 is standard
DEFAULT_RRF_K = 60


def reciprocal_rank_fusion(
    graphiti_results: List[Dict[str, Any]],
    lancedb_results: List[Dict[str, Any]],
    k: int = DEFAULT_RRF_K,
    top_n: Optional[int] = None
) -> List[UnifiedResult]:
    """
    使用RRF算法融合Graphiti和LanceDB检索结果

    ✅ Verified from docs/architecture/FUSION-ALGORITHM-DESIGN.md Section 2

    RRF公式: RRF_score(d) = Σ(1/(k+rank_i(d)))

    优点:
    - 不依赖原始分数的归一化
    - 对异构检索系统友好
    - 计算简单，O(n)复杂度

    Args:
        graphiti_results: Graphiti检索结果列表，每项包含:
            - id: 节点/边/情节ID
            - content: 内容文本
            - score: 检索分数
            - type: "node" | "edge" | "episode"
        lancedb_results: LanceDB检索结果列表，每项包含:
            - doc_id: 文档ID
            - content: 内容文本
            - distance: 向量距离 (越小越好)
        k: RRF常数 (默认60)
        top_n: 返回前N个结果 (None表示全部)

    Returns:
        按RRF分数排序的UnifiedResult列表

    Example:
        >>> graphiti = [{"id": "n1", "content": "...", "score": 0.9, "type": "node"}]
        >>> lancedb = [{"doc_id": "d1", "content": "...", "distance": 0.2}]
        >>> results = reciprocal_rank_fusion(graphiti, lancedb)
        >>> results[0].fused_score  # RRF score
    """
    # 存储每个文档的RRF分数
    rrf_scores: Dict[str, float] = defaultdict(float)
    # 存储文档详情
    doc_details: Dict[str, UnifiedResult] = {}

    # 处理Graphiti结果
    for rank, item in enumerate(graphiti_results, start=1):
        doc_id = _get_graphiti_id(item)
        rrf_scores[doc_id] += 1.0 / (k + rank)

        if doc_id not in doc_details:
            doc_details[doc_id] = _create_graphiti_result(item)

    # 处理LanceDB结果
    for rank, item in enumerate(lancedb_results, start=1):
        doc_id = _get_lancedb_id(item)
        rrf_scores[doc_id] += 1.0 / (k + rank)

        if doc_id not in doc_details:
            doc_details[doc_id] = _create_lancedb_result(item)

    # 按RRF分数排序
    sorted_ids = sorted(
        rrf_scores.keys(),
        key=lambda x: rrf_scores[x],
        reverse=True
    )

    # 构建最终结果
    results: List[UnifiedResult] = []
    for final_rank, doc_id in enumerate(sorted_ids, start=1):
        result = doc_details[doc_id]
        result.fused_score = rrf_scores[doc_id]
        result.rank = final_rank
        results.append(result)

    # 限制返回数量
    if top_n is not None:
        results = results[:top_n]

    return results


def _get_graphiti_id(item: Dict[str, Any]) -> str:
    """获取Graphiti结果的唯一ID"""
    item_type = item.get("type", "node")
    item_id = item.get("id", item.get("uuid", "unknown"))
    return f"graphiti_{item_type}_{item_id}"


def _get_lancedb_id(item: Dict[str, Any]) -> str:
    """获取LanceDB结果的唯一ID"""
    doc_id = item.get("doc_id", item.get("id", "unknown"))
    return f"lancedb_{doc_id}"


def _create_graphiti_result(item: Dict[str, Any]) -> UnifiedResult:
    """从Graphiti结果创建UnifiedResult"""
    item_type = item.get("type", "node")
    type_map = {
        "node": ResultType.NODE,
        "edge": ResultType.EDGE,
        "episode": ResultType.EPISODE
    }

    return UnifiedResult(
        id=_get_graphiti_id(item),
        content=item.get("content", item.get("fact", "")),
        source=SearchSource.GRAPHITI,
        result_type=type_map.get(item_type, ResultType.NODE),
        original_score=item.get("score", 0.0),
        metadata={
            "original_id": item.get("id", item.get("uuid")),
            "original_type": item_type,
            **{k: v for k, v in item.items()
               if k not in ["id", "uuid", "content", "fact", "score", "type"]}
        }
    )


def _create_lancedb_result(item: Dict[str, Any]) -> UnifiedResult:
    """从LanceDB结果创建UnifiedResult"""
    distance = item.get("distance", item.get("_distance", 0.0))
    # 将distance转换为score: score = 1 / (1 + distance)
    score = 1.0 / (1.0 + distance) if distance >= 0 else 0.0

    return UnifiedResult(
        id=_get_lancedb_id(item),
        content=item.get("content", item.get("text", "")),
        source=SearchSource.LANCEDB,
        result_type=ResultType.DOCUMENT,
        original_score=score,
        metadata={
            "original_distance": distance,
            "doc_id": item.get("doc_id", item.get("id")),
            **{k: v for k, v in item.items()
               if k not in ["doc_id", "id", "content", "text", "distance", "_distance"]}
        }
    )


def calculate_rrf_contribution(rank: int, k: int = DEFAULT_RRF_K) -> float:
    """
    计算单个排名的RRF贡献分数

    Args:
        rank: 文档排名 (从1开始)
        k: RRF常数

    Returns:
        RRF贡献分数 1/(k+rank)
    """
    return 1.0 / (k + rank)


# ============================================================================
# Story 6.8: 多模态RRF融合扩展
# ⚠️ DEPRECATED: 此 3 源权重配置已被 5 源设计替代。
# 规范权重见 agentic_rag.nodes.DEFAULT_SOURCE_WEIGHTS (Story 23.4 / 35.8)
# 此函数仅保留用于向后兼容，主管线使用 nodes._fuse_rrf_multi_source()
# ============================================================================

# ⚠️ DEPRECATED - 规范权重: agentic_rag.nodes.DEFAULT_SOURCE_WEIGHTS
# Story 35.8 AC 35.8.4: multimodal 规范权重 = 0.15 (5 源设计)
DEFAULT_MULTIMODAL_WEIGHTS = {
    "text": 0.425,     # LanceDB文本检索权重 (调整以匹配 multimodal=0.15)
    "graph": 0.425,    # Graphiti图谱检索权重
    "multimodal": 0.15  # 多模态检索权重 (与 nodes.DEFAULT_SOURCE_WEIGHTS 一致)
}


def rrf_fusion_with_multimodal(
    text_results: List[Dict[str, Any]],
    graph_results: List[Dict[str, Any]],
    multimodal_results: List[Dict[str, Any]],
    k: int = DEFAULT_RRF_K,
    weights: Optional[Dict[str, float]] = None,
    top_n: Optional[int] = None
) -> List[UnifiedResult]:
    """
    扩展RRF支持多模态融合 (Story 6.8 - AC 6.8.2)

    ✅ Verified from Story 6.8 Dev Notes

    融合三个检索源的结果:
    - text_results: LanceDB文本向量检索
    - graph_results: Graphiti知识图谱检索
    - multimodal_results: 多模态内容检索 (图片、PDF)

    加权RRF公式:
        Weighted_RRF_score(d) = Σ(weight_i * 1/(k+rank_i(d)))

    Args:
        text_results: LanceDB文本检索结果
        graph_results: Graphiti图谱检索结果
        multimodal_results: 多模态检索结果，每项包含:
            - id: 媒体ID
            - content: 描述/OCR文本
            - score: 相似度分数
            - media_type: "image" | "pdf" | "audio" | "video"
            - metadata: 附加元数据 (thumbnail_url, page_number等)
        k: RRF常数 (默认60)
        weights: 各检索源权重，默认 {"text": 0.4, "graph": 0.3, "multimodal": 0.3}
        top_n: 返回前N个结果 (None表示全部)

    Returns:
        按加权RRF分数排序的UnifiedResult列表

    Example:
        >>> text = [{"doc_id": "d1", "content": "...", "distance": 0.2}]
        >>> graph = [{"id": "n1", "content": "...", "score": 0.9, "type": "node"}]
        >>> multimodal = [{"id": "img1", "content": "...", "score": 0.8, "media_type": "image"}]
        >>> results = rrf_fusion_with_multimodal(text, graph, multimodal)
    """
    # 使用默认权重或自定义权重
    w = weights or DEFAULT_MULTIMODAL_WEIGHTS.copy()

    # 确保权重归一化
    total_weight = sum(w.values())
    if abs(total_weight - 1.0) > 0.001:
        w = {k: v / total_weight for k, v in w.items()}

    # 存储每个文档的加权RRF分数
    rrf_scores: Dict[str, float] = defaultdict(float)
    # 存储文档详情
    doc_details: Dict[str, UnifiedResult] = {}

    # 处理LanceDB文本结果
    text_weight = w.get("text", 0.4)
    for rank, item in enumerate(text_results, start=1):
        doc_id = _get_lancedb_id(item)
        rrf_scores[doc_id] += text_weight * (1.0 / (k + rank))

        if doc_id not in doc_details:
            doc_details[doc_id] = _create_lancedb_result(item)

    # 处理Graphiti图谱结果
    graph_weight = w.get("graph", 0.3)
    for rank, item in enumerate(graph_results, start=1):
        doc_id = _get_graphiti_id(item)
        rrf_scores[doc_id] += graph_weight * (1.0 / (k + rank))

        if doc_id not in doc_details:
            doc_details[doc_id] = _create_graphiti_result(item)

    # 处理多模态结果 (Story 6.8)
    multimodal_weight = w.get("multimodal", 0.3)
    for rank, item in enumerate(multimodal_results, start=1):
        doc_id = _get_multimodal_id(item)
        rrf_scores[doc_id] += multimodal_weight * (1.0 / (k + rank))

        if doc_id not in doc_details:
            doc_details[doc_id] = _create_multimodal_result(item)

    # 按加权RRF分数排序
    sorted_ids = sorted(
        rrf_scores.keys(),
        key=lambda x: rrf_scores[x],
        reverse=True
    )

    # 构建最终结果
    results: List[UnifiedResult] = []
    for final_rank, doc_id in enumerate(sorted_ids, start=1):
        result = doc_details[doc_id]
        result.fused_score = rrf_scores[doc_id]
        result.rank = final_rank
        results.append(result)

    # 限制返回数量
    if top_n is not None:
        results = results[:top_n]

    return results


def _get_multimodal_id(item: Dict[str, Any]) -> str:
    """获取多模态结果的唯一ID (Story 6.8)"""
    media_type = item.get("media_type", item.get("type", "unknown"))
    item_id = item.get("id", item.get("media_id", "unknown"))
    return f"multimodal_{media_type}_{item_id}"


def _create_multimodal_result(item: Dict[str, Any]) -> UnifiedResult:
    """从多模态结果创建UnifiedResult (Story 6.8)"""
    media_type = item.get("media_type", item.get("type", "image"))
    type_map = {
        "image": ResultType.IMAGE,
        "pdf": ResultType.PDF,
        "audio": ResultType.AUDIO,
        "video": ResultType.VIDEO
    }

    # 构建元数据，包含格式化信息 (AC 6.8.3)
    metadata = {
        "original_id": item.get("id", item.get("media_id")),
        "media_type": media_type,
    }

    # 添加可选的格式化字段 (AC 6.8.3)
    if "thumbnail_url" in item:
        metadata["thumbnail_url"] = item["thumbnail_url"]
    if "page_number" in item:
        metadata["page_number"] = item["page_number"]
    if "chapter" in item or "section" in item:
        metadata["chapter"] = item.get("chapter", item.get("section"))
    if "file_path" in item:
        metadata["file_path"] = item["file_path"]

    # 复制其他元数据
    excluded_keys = {
        "id", "media_id", "content", "text", "score", "distance",
        "media_type", "type", "thumbnail_url", "page_number",
        "chapter", "section", "file_path"
    }
    for k, v in item.items():
        if k not in excluded_keys:
            metadata[k] = v

    return UnifiedResult(
        id=_get_multimodal_id(item),
        content=item.get("content", item.get("text", item.get("description", ""))),
        source=SearchSource.MULTIMODAL,
        result_type=type_map.get(media_type, ResultType.IMAGE),
        original_score=item.get("score", 0.0),
        metadata=metadata
    )


def weighted_rrf_fusion(
    result_sources: Dict[str, List[Dict[str, Any]]],
    weights: Dict[str, float],
    k: int = DEFAULT_RRF_K,
    top_n: Optional[int] = None
) -> List[UnifiedResult]:
    """
    通用加权RRF融合，支持任意数量的检索源 (Story 6.8扩展)

    ✅ Verified from Story 6.8 architecture design

    Args:
        result_sources: 检索源字典，格式:
            {
                "text": [...],      # LanceDB结果
                "graph": [...],     # Graphiti结果
                "multimodal": [...] # 多模态结果
            }
        weights: 对应权重字典，必须与result_sources键一致
        k: RRF常数
        top_n: 返回前N个结果

    Returns:
        按加权RRF分数排序的UnifiedResult列表

    Example:
        >>> sources = {
        ...     "text": text_results,
        ...     "graph": graph_results,
        ...     "multimodal": multimodal_results
        ... }
        >>> weights = {"text": 0.4, "graph": 0.3, "multimodal": 0.3}
        >>> results = weighted_rrf_fusion(sources, weights)
    """
    # 归一化权重
    total_weight = sum(weights.values())
    normalized_weights = {k: v / total_weight for k, v in weights.items()}

    # ID生成器和结果创建器映射
    id_generators = {
        "text": _get_lancedb_id,
        "graph": _get_graphiti_id,
        "multimodal": _get_multimodal_id
    }

    result_creators = {
        "text": _create_lancedb_result,
        "graph": _create_graphiti_result,
        "multimodal": _create_multimodal_result
    }

    # 存储RRF分数和文档详情
    rrf_scores: Dict[str, float] = defaultdict(float)
    doc_details: Dict[str, UnifiedResult] = {}

    # 处理每个检索源
    for source_name, results in result_sources.items():
        weight = normalized_weights.get(source_name, 0.0)
        if weight <= 0 or not results:
            continue

        # 获取ID生成器和结果创建器
        get_id = id_generators.get(source_name, lambda x: f"{source_name}_{x.get('id', 'unknown')}")
        create_result = result_creators.get(source_name)

        for rank, item in enumerate(results, start=1):
            doc_id = get_id(item)
            rrf_scores[doc_id] += weight * (1.0 / (k + rank))

            if doc_id not in doc_details and create_result:
                doc_details[doc_id] = create_result(item)

    # 排序并构建结果
    sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)

    results: List[UnifiedResult] = []
    for final_rank, doc_id in enumerate(sorted_ids, start=1):
        if doc_id in doc_details:
            result = doc_details[doc_id]
            result.fused_score = rrf_scores[doc_id]
            result.rank = final_rank
            results.append(result)

    if top_n is not None:
        results = results[:top_n]

    return results
