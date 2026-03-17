"""
融合算法模块 (Story 12.7)

实现三种融合算法:
- RRF (Reciprocal Rank Fusion)
- Weighted (加权融合)
- Cascade (级联检索)

Author: Canvas Learning System Team
Version: 1.0.0
Created: 2025-11-29
"""

from .cascade_retrieval import DEFAULT_GRAPHITI_MIN_SCORE, DEFAULT_GRAPHITI_THRESHOLD, CascadeResult, cascade_retrieval
from .evaluator import calculate_mrr_at_k, evaluate_fusion
from .rrf_fusion import DEFAULT_RRF_K, reciprocal_rank_fusion
from .strategy_selector import (
    CanvasOperation,
    FusionStrategy,
    execute_fusion,
    get_strategy_config,
    select_fusion_algorithm,
)
from .unified_result import ResultType, SearchSource, UnifiedResult
from .weighted_fusion import DEFAULT_GRAPHITI_WEIGHT, DEFAULT_LANCEDB_WEIGHT, NormalizationMethod, weighted_fusion

__all__ = [
    # Data models
    "UnifiedResult",
    "SearchSource",
    "ResultType",
    "CascadeResult",

    # RRF
    "reciprocal_rank_fusion",
    "DEFAULT_RRF_K",

    # Weighted
    "weighted_fusion",
    "NormalizationMethod",
    "DEFAULT_GRAPHITI_WEIGHT",
    "DEFAULT_LANCEDB_WEIGHT",

    # Cascade
    "cascade_retrieval",
    "DEFAULT_GRAPHITI_THRESHOLD",
    "DEFAULT_GRAPHITI_MIN_SCORE",

    # Strategy
    "FusionStrategy",
    "CanvasOperation",
    "select_fusion_algorithm",
    "execute_fusion",
    "get_strategy_config",

    # Evaluation
    "calculate_mrr_at_k",
    "evaluate_fusion",
]
