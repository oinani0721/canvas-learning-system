"""
融合算法评估器

实现MRR@K (Mean Reciprocal Rank) 评估指标

✅ Verified from docs/architecture/FUSION-ALGORITHM-DESIGN.md Section 6

目标: MRR@10 ≥ 0.350 (Story 12.7 AC5)

Author: Canvas Learning System Team
Version: 1.0.0
Created: 2025-11-29
"""

import statistics
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Set

from .unified_result import UnifiedResult

# Story 12.7 AC5: MRR@10 ≥ 0.350
MRR_TARGET = 0.350


@dataclass
class EvaluationResult:
    """评估结果"""
    mrr_at_k: float
    num_queries: int
    k: int
    individual_rrs: List[float] = field(default_factory=list)
    hits_at_1: int = 0
    hits_at_5: int = 0
    hits_at_10: int = 0

    @property
    def hit_rate_at_1(self) -> float:
        """命中率@1"""
        return self.hits_at_1 / self.num_queries if self.num_queries > 0 else 0.0

    @property
    def hit_rate_at_5(self) -> float:
        """命中率@5"""
        return self.hits_at_5 / self.num_queries if self.num_queries > 0 else 0.0

    @property
    def hit_rate_at_10(self) -> float:
        """命中率@10"""
        return self.hits_at_10 / self.num_queries if self.num_queries > 0 else 0.0

    @property
    def passes_target(self) -> bool:
        """是否达到目标"""
        return self.mrr_at_k >= MRR_TARGET

    def summary(self) -> Dict[str, Any]:
        """获取摘要"""
        return {
            "mrr_at_k": round(self.mrr_at_k, 4),
            "k": self.k,
            "num_queries": self.num_queries,
            "target": MRR_TARGET,
            "passes_target": self.passes_target,
            "hit_rate_at_1": round(self.hit_rate_at_1, 4),
            "hit_rate_at_5": round(self.hit_rate_at_5, 4),
            "hit_rate_at_10": round(self.hit_rate_at_10, 4),
            "rr_std": round(statistics.stdev(self.individual_rrs), 4)
                     if len(self.individual_rrs) > 1 else 0.0
        }


def calculate_mrr_at_k(
    results: List[UnifiedResult],
    relevant_ids: Set[str],
    k: int = 10
) -> float:
    """
    计算单个查询的Reciprocal Rank@K

    ✅ Verified from FUSION-ALGORITHM-DESIGN.md Section 6

    公式: RR@K = 1/rank 如果在top-K中找到相关文档，否则为0

    Args:
        results: 排序后的检索结果列表
        relevant_ids: 相关文档ID集合
        k: 计算的截断位置

    Returns:
        Reciprocal Rank分数 (0到1之间)

    Example:
        >>> results = [UnifiedResult(id="doc1", ...), UnifiedResult(id="doc2", ...)]
        >>> relevant = {"doc2"}
        >>> rr = calculate_mrr_at_k(results, relevant, k=10)
        >>> rr  # 0.5 (doc2在第2位)
    """
    for i, result in enumerate(results[:k]):
        if result.id in relevant_ids:
            return 1.0 / (i + 1)
    return 0.0


def calculate_hit_at_k(
    results: List[UnifiedResult],
    relevant_ids: Set[str],
    k: int
) -> bool:
    """检查top-K中是否有相关文档"""
    for result in results[:k]:
        if result.id in relevant_ids:
            return True
    return False


def evaluate_fusion(
    test_queries: List[Dict[str, Any]],
    fusion_func: Callable[[str], List[UnifiedResult]],
    k: int = 10
) -> EvaluationResult:
    """
    评估融合算法性能

    使用测试数据集计算MRR@K

    Args:
        test_queries: 测试查询列表，每项包含:
            - query: 查询文本
            - relevant_ids: 相关文档ID集合
        fusion_func: 融合函数，接收查询返回结果列表
        k: MRR计算的K值

    Returns:
        EvaluationResult: 评估结果

    Example:
        >>> test_data = [
        ...     {"query": "逆否命题", "relevant_ids": {"doc1", "doc2"}},
        ...     {"query": "充分条件", "relevant_ids": {"doc3"}}
        ... ]
        >>> result = evaluate_fusion(test_data, my_fusion_func, k=10)
        >>> result.mrr_at_k  # 0.xxx
    """
    individual_rrs: List[float] = []
    hits_1 = 0
    hits_5 = 0
    hits_10 = 0

    for query_data in test_queries:
        query = query_data["query"]
        relevant_ids = set(query_data["relevant_ids"])

        # 执行融合
        results = fusion_func(query)

        # 计算RR
        rr = calculate_mrr_at_k(results, relevant_ids, k)
        individual_rrs.append(rr)

        # 计算Hits
        if calculate_hit_at_k(results, relevant_ids, 1):
            hits_1 += 1
        if calculate_hit_at_k(results, relevant_ids, 5):
            hits_5 += 1
        if calculate_hit_at_k(results, relevant_ids, 10):
            hits_10 += 1

    # 计算MRR
    mrr = sum(individual_rrs) / len(individual_rrs) if individual_rrs else 0.0

    return EvaluationResult(
        mrr_at_k=mrr,
        num_queries=len(test_queries),
        k=k,
        individual_rrs=individual_rrs,
        hits_at_1=hits_1,
        hits_at_5=hits_5,
        hits_at_10=hits_10
    )


def evaluate_fusion_with_results(
    test_queries: List[Dict[str, Any]],
    k: int = 10
) -> EvaluationResult:
    """
    评估预计算的融合结果

    用于测试场景，结果已预先计算

    Args:
        test_queries: 测试数据，每项包含:
            - results: List[UnifiedResult] 融合结果
            - relevant_ids: 相关文档ID集合
        k: MRR计算的K值

    Returns:
        EvaluationResult
    """
    individual_rrs: List[float] = []
    hits_1 = 0
    hits_5 = 0
    hits_10 = 0

    for query_data in test_queries:
        results = query_data["results"]
        relevant_ids = set(query_data["relevant_ids"])

        rr = calculate_mrr_at_k(results, relevant_ids, k)
        individual_rrs.append(rr)

        if calculate_hit_at_k(results, relevant_ids, 1):
            hits_1 += 1
        if calculate_hit_at_k(results, relevant_ids, 5):
            hits_5 += 1
        if calculate_hit_at_k(results, relevant_ids, 10):
            hits_10 += 1

    mrr = sum(individual_rrs) / len(individual_rrs) if individual_rrs else 0.0

    return EvaluationResult(
        mrr_at_k=mrr,
        num_queries=len(test_queries),
        k=k,
        individual_rrs=individual_rrs,
        hits_at_1=hits_1,
        hits_at_5=hits_5,
        hits_at_10=hits_10
    )


def compare_strategies(
    test_queries: List[Dict[str, Any]],
    strategies: Dict[str, Callable[[str], List[UnifiedResult]]],
    k: int = 10
) -> Dict[str, EvaluationResult]:
    """
    比较多个融合策略

    Args:
        test_queries: 测试查询
        strategies: 策略名称 -> 融合函数的映射
        k: MRR计算的K值

    Returns:
        策略名称 -> 评估结果的映射
    """
    results = {}
    for name, fusion_func in strategies.items():
        results[name] = evaluate_fusion(test_queries, fusion_func, k)
    return results
