"""
Weighted (加权) 融合算法

✅ Verified from docs/architecture/FUSION-ALGORITHM-DESIGN.md Section 3

公式: Weighted_score(d) = α * norm(graphiti_score) + β * norm(lancedb_score)
其中:
    α + β = 1
    α = Graphiti权重 (默认0.7)
    β = LanceDB权重 (默认0.3)

支持的归一化方法:
    - min_max: (x - min) / (max - min)
    - z_score: (x - μ) / σ

Author: Canvas Learning System Team
Version: 1.0.0
Created: 2025-11-29
"""

import math
from enum import Enum
from typing import Any, Dict, List, Optional

from .unified_result import UnifiedResult

# ✅ Verified from FUSION-ALGORITHM-DESIGN.md Section 3.1
DEFAULT_GRAPHITI_WEIGHT = 0.7
DEFAULT_LANCEDB_WEIGHT = 0.3


class NormalizationMethod(Enum):
    """归一化方法"""
    MIN_MAX = "min_max"
    Z_SCORE = "z_score"


def weighted_fusion(
    graphiti_results: List[Dict[str, Any]],
    lancedb_results: List[Dict[str, Any]],
    graphiti_weight: float = DEFAULT_GRAPHITI_WEIGHT,
    lancedb_weight: float = DEFAULT_LANCEDB_WEIGHT,
    normalization: NormalizationMethod = NormalizationMethod.MIN_MAX,
    top_n: Optional[int] = None
) -> List[UnifiedResult]:
    """
    使用加权平均融合Graphiti和LanceDB检索结果

    ✅ Verified from docs/architecture/FUSION-ALGORITHM-DESIGN.md Section 3

    公式: score(d) = α * norm(graphiti) + β * norm(lancedb)

    Args:
        graphiti_results: Graphiti检索结果列表
        lancedb_results: LanceDB检索结果列表
        graphiti_weight: Graphiti权重α (默认0.7)
        lancedb_weight: LanceDB权重β (默认0.3)
        normalization: 归一化方法 (默认min_max)
        top_n: 返回前N个结果

    Returns:
        按加权分数排序的UnifiedResult列表

    Raises:
        ValueError: 如果权重之和不为1

    Example:
        >>> results = weighted_fusion(graphiti, lancedb, graphiti_weight=0.7)
        >>> results[0].fused_score  # Weighted score
    """
    # 验证权重
    if abs(graphiti_weight + lancedb_weight - 1.0) > 1e-6:
        raise ValueError(
            f"Weights must sum to 1.0, got {graphiti_weight + lancedb_weight}"
        )

    # 提取并归一化分数
    graphiti_scores = _extract_graphiti_scores(graphiti_results)
    lancedb_scores = _extract_lancedb_scores(lancedb_results)

    # 归一化
    norm_graphiti = _normalize_scores(
        graphiti_scores, normalization
    )
    norm_lancedb = _normalize_scores(
        lancedb_scores, normalization
    )

    # 计算加权分数
    weighted_scores: Dict[str, float] = {}
    doc_details: Dict[str, UnifiedResult] = {}

    # 处理Graphiti结果
    for item in graphiti_results:
        doc_id = _get_graphiti_id(item)
        weighted_scores[doc_id] = graphiti_weight * norm_graphiti.get(doc_id, 0.0)
        doc_details[doc_id] = _create_graphiti_result(item)

    # 处理LanceDB结果
    for item in lancedb_results:
        doc_id = _get_lancedb_id(item)
        if doc_id in weighted_scores:
            # 文档在两个源中都存在
            weighted_scores[doc_id] += lancedb_weight * norm_lancedb.get(doc_id, 0.0)
        else:
            weighted_scores[doc_id] = lancedb_weight * norm_lancedb.get(doc_id, 0.0)
            doc_details[doc_id] = _create_lancedb_result(item)

    # 按加权分数排序
    sorted_ids = sorted(
        weighted_scores.keys(),
        key=lambda x: weighted_scores[x],
        reverse=True
    )

    # 构建最终结果
    results: List[UnifiedResult] = []
    for final_rank, doc_id in enumerate(sorted_ids, start=1):
        result = doc_details[doc_id]
        result.fused_score = weighted_scores[doc_id]
        result.rank = final_rank
        results.append(result)

    if top_n is not None:
        results = results[:top_n]

    return results


def _extract_graphiti_scores(results: List[Dict[str, Any]]) -> Dict[str, float]:
    """提取Graphiti结果的分数"""
    scores = {}
    for item in results:
        doc_id = _get_graphiti_id(item)
        scores[doc_id] = item.get("score", 0.0)
    return scores


def _extract_lancedb_scores(results: List[Dict[str, Any]]) -> Dict[str, float]:
    """提取LanceDB结果的分数 (distance转score)"""
    scores = {}
    for item in results:
        doc_id = _get_lancedb_id(item)
        distance = item.get("distance", item.get("_distance", 0.0))
        # 转换: score = 1 / (1 + distance)
        scores[doc_id] = 1.0 / (1.0 + distance) if distance >= 0 else 0.0
    return scores


def _normalize_scores(
    scores: Dict[str, float],
    method: NormalizationMethod
) -> Dict[str, float]:
    """归一化分数"""
    if not scores:
        return {}

    values = list(scores.values())

    if method == NormalizationMethod.MIN_MAX:
        return _min_max_normalize(scores, values)
    elif method == NormalizationMethod.Z_SCORE:
        return _z_score_normalize(scores, values)
    else:
        raise ValueError(f"Unknown normalization method: {method}")


def _min_max_normalize(
    scores: Dict[str, float],
    values: List[float]
) -> Dict[str, float]:
    """
    Min-Max归一化

    ✅ Verified from FUSION-ALGORITHM-DESIGN.md Section 3.2
    公式: norm(x) = (x - min) / (max - min)
    """
    min_val = min(values)
    max_val = max(values)

    if max_val == min_val:
        # 所有分数相同，归一化为0.5
        return {k: 0.5 for k in scores}

    return {
        k: (v - min_val) / (max_val - min_val)
        for k, v in scores.items()
    }


def _z_score_normalize(
    scores: Dict[str, float],
    values: List[float]
) -> Dict[str, float]:
    """
    Z-Score归一化

    ✅ Verified from FUSION-ALGORITHM-DESIGN.md Section 3.2
    公式: norm(x) = (x - μ) / σ
    然后缩放到[0,1]区间
    """
    n = len(values)
    mean = sum(values) / n
    variance = sum((x - mean) ** 2 for x in values) / n
    std = math.sqrt(variance) if variance > 0 else 1.0

    # Z-Score
    z_scores = {k: (v - mean) / std for k, v in scores.items()}

    # 缩放到[0,1]
    z_values = list(z_scores.values())
    z_min = min(z_values)
    z_max = max(z_values)

    if z_max == z_min:
        return {k: 0.5 for k in z_scores}

    return {
        k: (v - z_min) / (z_max - z_min)
        for k, v in z_scores.items()
    }


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
    from .rrf_fusion import _create_graphiti_result as create_graphiti
    return create_graphiti(item)


def _create_lancedb_result(item: Dict[str, Any]) -> UnifiedResult:
    """从LanceDB结果创建UnifiedResult"""
    from .rrf_fusion import _create_lancedb_result as create_lancedb
    return create_lancedb(item)
