"""
融合策略选择器

✅ Verified from docs/architecture/FUSION-ALGORITHM-DESIGN.md Section 5.2

根据Canvas操作类型自动选择最优融合算法:
    - 检验白板生成 → RRF (平衡)
    - 薄弱点聚类 → Weighted (α=0.7)
    - 概念关联检索 → Cascade (图优先)
    - 文档检索 → Weighted (β=0.7)

Author: Canvas Learning System Team
Version: 1.0.0
Created: 2025-11-29
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from .cascade_retrieval import DEFAULT_GRAPHITI_MIN_SCORE, DEFAULT_GRAPHITI_THRESHOLD, CascadeResult, cascade_retrieval
from .rrf_fusion import DEFAULT_RRF_K, reciprocal_rank_fusion
from .unified_result import UnifiedResult
from .weighted_fusion import DEFAULT_GRAPHITI_WEIGHT, DEFAULT_LANCEDB_WEIGHT, NormalizationMethod, weighted_fusion


class FusionStrategy(Enum):
    """融合策略枚举"""
    RRF = "rrf"
    WEIGHTED_GRAPHITI = "weighted_graphiti"  # α=0.7
    WEIGHTED_LANCEDB = "weighted_lancedb"    # β=0.7
    WEIGHTED_BALANCED = "weighted_balanced"   # α=0.5, β=0.5
    CASCADE = "cascade"


class CanvasOperation(Enum):
    """Canvas操作类型"""
    VERIFICATION_CANVAS = "verification_canvas"      # 检验白板生成
    WEAK_POINT_CLUSTERING = "weak_point_clustering"  # 薄弱点聚类
    CONCEPT_RELATION = "concept_relation"            # 概念关联检索
    DOCUMENT_RETRIEVAL = "document_retrieval"        # 文档检索
    GENERAL_QUERY = "general_query"                  # 通用查询


@dataclass
class StrategyConfig:
    """策略配置"""
    strategy: FusionStrategy
    graphiti_weight: float = DEFAULT_GRAPHITI_WEIGHT
    lancedb_weight: float = DEFAULT_LANCEDB_WEIGHT
    rrf_k: int = DEFAULT_RRF_K
    cascade_threshold: int = DEFAULT_GRAPHITI_THRESHOLD
    cascade_min_score: float = DEFAULT_GRAPHITI_MIN_SCORE
    normalization: NormalizationMethod = NormalizationMethod.MIN_MAX


# ✅ Verified from FUSION-ALGORITHM-DESIGN.md Section 5.2
OPERATION_STRATEGY_MAPPING: Dict[CanvasOperation, StrategyConfig] = {
    CanvasOperation.VERIFICATION_CANVAS: StrategyConfig(
        strategy=FusionStrategy.RRF,
        rrf_k=60
    ),
    CanvasOperation.WEAK_POINT_CLUSTERING: StrategyConfig(
        strategy=FusionStrategy.WEIGHTED_GRAPHITI,
        graphiti_weight=0.7,
        lancedb_weight=0.3
    ),
    CanvasOperation.CONCEPT_RELATION: StrategyConfig(
        strategy=FusionStrategy.CASCADE,
        cascade_threshold=3,
        cascade_min_score=0.6
    ),
    CanvasOperation.DOCUMENT_RETRIEVAL: StrategyConfig(
        strategy=FusionStrategy.WEIGHTED_LANCEDB,
        graphiti_weight=0.3,
        lancedb_weight=0.7
    ),
    CanvasOperation.GENERAL_QUERY: StrategyConfig(
        strategy=FusionStrategy.RRF,
        rrf_k=60
    ),
}


def select_fusion_algorithm(operation: CanvasOperation) -> FusionStrategy:
    """
    根据Canvas操作类型选择融合算法

    ✅ Verified from docs/architecture/FUSION-ALGORITHM-DESIGN.md Section 5.2

    决策树:
        - 检验白板生成 → RRF (平衡两源)
        - 薄弱点聚类 → Weighted (α=0.7, 图优先)
        - 概念关联检索 → Cascade (图优先)
        - 文档检索 → Weighted (β=0.7, 向量优先)
        - 通用查询 → RRF (默认)

    Args:
        operation: Canvas操作类型

    Returns:
        推荐的融合策略

    Example:
        >>> strategy = select_fusion_algorithm(CanvasOperation.VERIFICATION_CANVAS)
        >>> strategy  # FusionStrategy.RRF
    """
    config = OPERATION_STRATEGY_MAPPING.get(
        operation,
        OPERATION_STRATEGY_MAPPING[CanvasOperation.GENERAL_QUERY]
    )
    return config.strategy


def get_strategy_config(operation: CanvasOperation) -> StrategyConfig:
    """
    获取操作对应的完整策略配置

    Args:
        operation: Canvas操作类型

    Returns:
        策略配置
    """
    return OPERATION_STRATEGY_MAPPING.get(
        operation,
        OPERATION_STRATEGY_MAPPING[CanvasOperation.GENERAL_QUERY]
    )


def execute_fusion(
    strategy: FusionStrategy,
    graphiti_results: List[Dict[str, Any]],
    lancedb_results: List[Dict[str, Any]],
    config: Optional[StrategyConfig] = None,
    top_n: int = 10
) -> Union[List[UnifiedResult], CascadeResult]:
    """
    执行融合算法

    根据指定的策略执行对应的融合算法。

    Args:
        strategy: 融合策略
        graphiti_results: Graphiti检索结果
        lancedb_results: LanceDB检索结果
        config: 策略配置 (可选)
        top_n: 返回结果数量

    Returns:
        UnifiedResult列表 (RRF/Weighted) 或 CascadeResult (Cascade)

    Example:
        >>> results = execute_fusion(
        ...     FusionStrategy.RRF,
        ...     graphiti,
        ...     lancedb,
        ...     top_n=10
        ... )
    """
    # 使用默认配置
    if config is None:
        config = StrategyConfig(strategy=strategy)

    if strategy == FusionStrategy.RRF:
        return reciprocal_rank_fusion(
            graphiti_results,
            lancedb_results,
            k=config.rrf_k,
            top_n=top_n
        )

    elif strategy in [
        FusionStrategy.WEIGHTED_GRAPHITI,
        FusionStrategy.WEIGHTED_LANCEDB,
        FusionStrategy.WEIGHTED_BALANCED
    ]:
        # 根据策略类型设置权重
        if strategy == FusionStrategy.WEIGHTED_GRAPHITI:
            g_weight, l_weight = 0.7, 0.3
        elif strategy == FusionStrategy.WEIGHTED_LANCEDB:
            g_weight, l_weight = 0.3, 0.7
        else:  # BALANCED
            g_weight, l_weight = 0.5, 0.5

        return weighted_fusion(
            graphiti_results,
            lancedb_results,
            graphiti_weight=g_weight,
            lancedb_weight=l_weight,
            normalization=config.normalization,
            top_n=top_n
        )

    elif strategy == FusionStrategy.CASCADE:
        return cascade_retrieval(
            graphiti_results,
            lancedb_results,
            graphiti_threshold=config.cascade_threshold,
            graphiti_min_score=config.cascade_min_score,
            top_n=top_n
        )

    else:
        raise ValueError(f"Unknown fusion strategy: {strategy}")


def execute_fusion_for_operation(
    operation: CanvasOperation,
    graphiti_results: List[Dict[str, Any]],
    lancedb_results: List[Dict[str, Any]],
    top_n: int = 10
) -> Union[List[UnifiedResult], CascadeResult]:
    """
    根据Canvas操作执行融合

    自动选择策略并执行融合。

    Args:
        operation: Canvas操作类型
        graphiti_results: Graphiti检索结果
        lancedb_results: LanceDB检索结果
        top_n: 返回结果数量

    Returns:
        融合结果
    """
    config = get_strategy_config(operation)
    return execute_fusion(
        strategy=config.strategy,
        graphiti_results=graphiti_results,
        lancedb_results=lancedb_results,
        config=config,
        top_n=top_n
    )


def get_all_strategies() -> List[FusionStrategy]:
    """获取所有支持的融合策略"""
    return list(FusionStrategy)


def get_all_operations() -> List[CanvasOperation]:
    """获取所有支持的Canvas操作"""
    return list(CanvasOperation)
