"""
Cascade (级联) 检索算法

✅ Verified from docs/architecture/FUSION-ALGORITHM-DESIGN.md Section 4

级联策略:
    - Tier 1: Graphiti检索 (图结构优先)
    - Tier 2: LanceDB检索 (向量回退)
    - 决策: 当Tier 1结果不足时触发Tier 2

Author: Canvas Learning System Team
Version: 1.0.0
Created: 2025-11-29
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List

from .rrf_fusion import reciprocal_rank_fusion
from .unified_result import UnifiedResult

# ✅ Verified from FUSION-ALGORITHM-DESIGN.md Section 4.1
DEFAULT_GRAPHITI_THRESHOLD = 5
DEFAULT_GRAPHITI_MIN_SCORE = 0.7


class CascadeTier(Enum):
    """级联层级"""
    TIER_1_GRAPHITI = "tier_1_graphiti"
    TIER_2_LANCEDB = "tier_2_lancedb"
    TIER_FUSION = "tier_fusion"


@dataclass
class CascadeResult:
    """
    级联检索结果

    包含检索结果和决策元数据
    """
    results: List[UnifiedResult]
    tier_used: CascadeTier
    graphiti_count: int
    high_quality_count: int
    lancedb_triggered: bool
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def tier_description(self) -> str:
        """获取层级描述"""
        if self.tier_used == CascadeTier.TIER_1_GRAPHITI:
            return "Tier 1 Only (Graphiti sufficient)"
        elif self.tier_used == CascadeTier.TIER_2_LANCEDB:
            return "Tier 2 Only (LanceDB fallback)"
        else:
            return "Tier Fusion (Graphiti + LanceDB)"


def cascade_retrieval(
    graphiti_results: List[Dict[str, Any]],
    lancedb_results: List[Dict[str, Any]],
    graphiti_threshold: int = DEFAULT_GRAPHITI_THRESHOLD,
    graphiti_min_score: float = DEFAULT_GRAPHITI_MIN_SCORE,
    use_lancedb_fallback: bool = True,
    top_n: int = 10
) -> CascadeResult:
    """
    级联检索: Graphiti优先，不足时回退到LanceDB

    ✅ Verified from docs/architecture/FUSION-ALGORITHM-DESIGN.md Section 4

    决策逻辑:
        if high_quality_graphiti >= threshold:
            return graphiti_results  # Tier 1足够
        else:
            # Tier 2: LanceDB回退 + RRF融合
            return rrf_fusion(graphiti_results, lancedb_results)

    Args:
        graphiti_results: Graphiti检索结果
        lancedb_results: LanceDB检索结果
        graphiti_threshold: 高质量结果阈值 (默认5)
        graphiti_min_score: 高质量分数阈值 (默认0.7)
        use_lancedb_fallback: 是否启用LanceDB回退 (默认True)
        top_n: 返回结果数量 (默认10)

    Returns:
        CascadeResult: 包含结果和元数据

    Example:
        >>> result = cascade_retrieval(graphiti, lancedb)
        >>> result.tier_used  # CascadeTier.TIER_1_GRAPHITI or TIER_FUSION
        >>> result.results    # List[UnifiedResult]
    """
    # 统计Graphiti高质量结果
    high_quality_graphiti = _filter_high_quality(
        graphiti_results,
        graphiti_min_score
    )
    high_quality_count = len(high_quality_graphiti)
    graphiti_count = len(graphiti_results)

    # 决策: Tier 1是否足够
    tier_1_sufficient = high_quality_count >= graphiti_threshold

    if tier_1_sufficient:
        # Tier 1足够，只使用Graphiti结果
        results = _convert_graphiti_results(high_quality_graphiti, top_n)
        return CascadeResult(
            results=results,
            tier_used=CascadeTier.TIER_1_GRAPHITI,
            graphiti_count=graphiti_count,
            high_quality_count=high_quality_count,
            lancedb_triggered=False,
            metadata={
                "decision": "tier_1_sufficient",
                "threshold": graphiti_threshold,
                "min_score": graphiti_min_score
            }
        )

    # Tier 1不足
    if not use_lancedb_fallback or not lancedb_results:
        # 不启用回退或无LanceDB结果
        results = _convert_graphiti_results(graphiti_results, top_n)
        return CascadeResult(
            results=results,
            tier_used=CascadeTier.TIER_1_GRAPHITI,
            graphiti_count=graphiti_count,
            high_quality_count=high_quality_count,
            lancedb_triggered=False,
            metadata={
                "decision": "tier_1_only_no_fallback",
                "reason": "fallback_disabled" if not use_lancedb_fallback
                          else "no_lancedb_results"
            }
        )

    # Tier 2: 触发LanceDB回退，使用RRF融合
    fused_results = reciprocal_rank_fusion(
        graphiti_results,
        lancedb_results,
        top_n=top_n
    )

    return CascadeResult(
        results=fused_results,
        tier_used=CascadeTier.TIER_FUSION,
        graphiti_count=graphiti_count,
        high_quality_count=high_quality_count,
        lancedb_triggered=True,
        metadata={
            "decision": "tier_2_triggered",
            "reason": f"high_quality_count ({high_quality_count}) < threshold ({graphiti_threshold})",
            "lancedb_count": len(lancedb_results),
            "fusion_method": "rrf"
        }
    )


async def cascade_retrieval_async(
    graphiti_retriever: Callable,
    lancedb_retriever: Callable,
    query: str,
    graphiti_threshold: int = DEFAULT_GRAPHITI_THRESHOLD,
    graphiti_min_score: float = DEFAULT_GRAPHITI_MIN_SCORE,
    num_results: int = 10
) -> CascadeResult:
    """
    异步级联检索

    实际调用检索函数，而不是接收预检索的结果。

    Args:
        graphiti_retriever: Graphiti检索函数
        lancedb_retriever: LanceDB检索函数
        query: 查询字符串
        graphiti_threshold: 高质量结果阈值
        graphiti_min_score: 高质量分数阈值
        num_results: 返回结果数量

    Returns:
        CascadeResult
    """
    # Tier 1: Graphiti检索
    graphiti_results = await graphiti_retriever(query, num_results=num_results)

    # 检查高质量结果
    high_quality = _filter_high_quality(graphiti_results, graphiti_min_score)

    if len(high_quality) >= graphiti_threshold:
        # Tier 1足够
        results = _convert_graphiti_results(high_quality, num_results)
        return CascadeResult(
            results=results,
            tier_used=CascadeTier.TIER_1_GRAPHITI,
            graphiti_count=len(graphiti_results),
            high_quality_count=len(high_quality),
            lancedb_triggered=False
        )

    # Tier 2: LanceDB回退
    lancedb_results = await lancedb_retriever(query, num_results=num_results)

    # RRF融合
    fused = reciprocal_rank_fusion(graphiti_results, lancedb_results, top_n=num_results)

    return CascadeResult(
        results=fused,
        tier_used=CascadeTier.TIER_FUSION,
        graphiti_count=len(graphiti_results),
        high_quality_count=len(high_quality),
        lancedb_triggered=True,
        metadata={"lancedb_count": len(lancedb_results)}
    )


def _filter_high_quality(
    results: List[Dict[str, Any]],
    min_score: float
) -> List[Dict[str, Any]]:
    """筛选高质量结果"""
    return [
        r for r in results
        if r.get("score", 0.0) >= min_score
    ]


def _convert_graphiti_results(
    results: List[Dict[str, Any]],
    top_n: int
) -> List[UnifiedResult]:
    """转换Graphiti结果为UnifiedResult"""
    from .rrf_fusion import _create_graphiti_result

    unified = []
    for rank, item in enumerate(results[:top_n], start=1):
        result = _create_graphiti_result(item)
        result.fused_score = item.get("score", 0.0)
        result.rank = rank
        unified.append(result)

    return unified
