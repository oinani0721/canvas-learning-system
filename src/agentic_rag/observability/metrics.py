"""
性能指标和成本追踪

Story 12.12: 性能监控和成本追踪

提供:
- MetricsCollector: 指标收集器
- 延迟追踪
- Token使用追踪
- 成本计算

Author: Canvas Learning System Team
Version: 1.0.0
Created: 2025-11-29
"""

import threading
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class LatencyMetric:
    """延迟指标"""
    node_name: str
    duration_ms: float
    timestamp: datetime = field(default_factory=datetime.now)
    success: bool = True
    error: Optional[str] = None


@dataclass
class TokenUsage:
    """Token 使用记录"""
    node_name: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    model: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class CostRecord:
    """成本记录"""
    node_name: str
    cost_usd: float
    source: str  # "openai", "cohere", "local"
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


# 模型定价 (USD per 1K tokens)
MODEL_PRICING = {
    # OpenAI
    "gpt-4": {"input": 0.03, "output": 0.06},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "gpt-4o": {"input": 0.005, "output": 0.015},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
    # Embedding
    "text-embedding-3-small": {"input": 0.00002, "output": 0.0},
    "text-embedding-3-large": {"input": 0.00013, "output": 0.0},
    # Cohere
    "rerank-english-v3.0": {"input": 0.001, "output": 0.0},  # per 1K search units
    "rerank-multilingual-v3.0": {"input": 0.001, "output": 0.0},
    # Local (free)
    "bge-reranker-base": {"input": 0.0, "output": 0.0},
    "bge-reranker-large": {"input": 0.0, "output": 0.0},
}


class MetricsCollector:
    """
    指标收集器

    线程安全的指标收集和聚合

    Usage:
        collector = MetricsCollector()
        collector.track_latency("retrieve_graphiti", 45.2)
        collector.track_token_usage("rerank_cohere", 1000, 0, "rerank-english-v3.0")
        stats = collector.get_summary()
    """

    def __init__(self, max_history: int = 1000):
        """
        初始化收集器

        Args:
            max_history: 保留的最大历史记录数
        """
        self.max_history = max_history
        self._latencies: List[LatencyMetric] = []
        self._token_usages: List[TokenUsage] = []
        self._costs: List[CostRecord] = []
        self._lock = threading.Lock()

        # Aggregated stats
        self._latency_stats: Dict[str, List[float]] = defaultdict(list)
        self._total_tokens: Dict[str, int] = defaultdict(int)
        self._total_cost: float = 0.0

    def track_latency(
        self,
        node_name: str,
        duration_ms: float,
        success: bool = True,
        error: Optional[str] = None,
    ) -> LatencyMetric:
        """
        记录延迟指标

        Args:
            node_name: 节点名称
            duration_ms: 延迟(毫秒)
            success: 是否成功
            error: 错误信息

        Returns:
            LatencyMetric: 记录的指标
        """
        metric = LatencyMetric(
            node_name=node_name,
            duration_ms=duration_ms,
            success=success,
            error=error,
        )

        with self._lock:
            self._latencies.append(metric)
            self._latency_stats[node_name].append(duration_ms)

            # Trim history
            if len(self._latencies) > self.max_history:
                self._latencies = self._latencies[-self.max_history:]

        return metric

    def track_token_usage(
        self,
        node_name: str,
        prompt_tokens: int,
        completion_tokens: int,
        model: str,
    ) -> TokenUsage:
        """
        记录 Token 使用

        Args:
            node_name: 节点名称
            prompt_tokens: 输入 token 数
            completion_tokens: 输出 token 数
            model: 模型名称

        Returns:
            TokenUsage: 使用记录
        """
        usage = TokenUsage(
            node_name=node_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            model=model,
        )

        # Calculate cost
        cost = self._calculate_cost(prompt_tokens, completion_tokens, model)

        with self._lock:
            self._token_usages.append(usage)
            self._total_tokens[model] += usage.total_tokens

            if cost > 0:
                self._costs.append(CostRecord(
                    node_name=node_name,
                    cost_usd=cost,
                    source="api",
                    details={
                        "model": model,
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                    }
                ))
                self._total_cost += cost

            # Trim history
            if len(self._token_usages) > self.max_history:
                self._token_usages = self._token_usages[-self.max_history:]

        return usage

    def track_cost(
        self,
        node_name: str,
        cost_usd: float,
        source: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> CostRecord:
        """
        直接记录成本

        Args:
            node_name: 节点名称
            cost_usd: 成本(USD)
            source: 成本来源
            details: 详细信息

        Returns:
            CostRecord: 成本记录
        """
        record = CostRecord(
            node_name=node_name,
            cost_usd=cost_usd,
            source=source,
            details=details or {},
        )

        with self._lock:
            self._costs.append(record)
            self._total_cost += cost_usd

            if len(self._costs) > self.max_history:
                self._costs = self._costs[-self.max_history:]

        return record

    def get_latency_stats(self, node_name: Optional[str] = None) -> Dict[str, Any]:
        """
        获取延迟统计

        Args:
            node_name: 可选节点名称过滤

        Returns:
            统计数据 (count, mean, p50, p95, p99)
        """
        with self._lock:
            if node_name:
                latencies = self._latency_stats.get(node_name, [])
            else:
                latencies = [lat for ls in self._latency_stats.values() for lat in ls]

        if not latencies:
            return {"count": 0}

        sorted_latencies = sorted(latencies)
        count = len(sorted_latencies)

        return {
            "count": count,
            "mean_ms": sum(latencies) / count,
            "min_ms": sorted_latencies[0],
            "max_ms": sorted_latencies[-1],
            "p50_ms": self._percentile(sorted_latencies, 50),
            "p95_ms": self._percentile(sorted_latencies, 95),
            "p99_ms": self._percentile(sorted_latencies, 99),
        }

    def get_token_stats(self) -> Dict[str, Any]:
        """获取 Token 使用统计"""
        with self._lock:
            return {
                "total_tokens_by_model": dict(self._total_tokens),
                "total_tokens": sum(self._total_tokens.values()),
                "record_count": len(self._token_usages),
            }

    def get_cost_stats(self) -> Dict[str, Any]:
        """获取成本统计"""
        with self._lock:
            cost_by_source = defaultdict(float)
            cost_by_node = defaultdict(float)

            for record in self._costs:
                cost_by_source[record.source] += record.cost_usd
                cost_by_node[record.node_name] += record.cost_usd

            return {
                "total_cost_usd": self._total_cost,
                "cost_by_source": dict(cost_by_source),
                "cost_by_node": dict(cost_by_node),
                "record_count": len(self._costs),
            }

    def get_summary(self) -> Dict[str, Any]:
        """
        获取完整统计摘要

        Returns:
            包含延迟、Token、成本统计的字典
        """
        return {
            "latency": self.get_latency_stats(),
            "tokens": self.get_token_stats(),
            "costs": self.get_cost_stats(),
            "timestamp": datetime.now().isoformat(),
        }

    def reset(self) -> None:
        """重置所有指标"""
        with self._lock:
            self._latencies.clear()
            self._token_usages.clear()
            self._costs.clear()
            self._latency_stats.clear()
            self._total_tokens.clear()
            self._total_cost = 0.0

    def _calculate_cost(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        model: str,
    ) -> float:
        """计算成本"""
        pricing = MODEL_PRICING.get(model)
        if not pricing:
            return 0.0

        input_cost = (prompt_tokens / 1000) * pricing["input"]
        output_cost = (completion_tokens / 1000) * pricing["output"]

        return input_cost + output_cost

    @staticmethod
    def _percentile(sorted_data: List[float], percentile: float) -> float:
        """计算百分位数"""
        if not sorted_data:
            return 0.0

        k = (len(sorted_data) - 1) * (percentile / 100)
        f = int(k)
        c = f + 1 if f < len(sorted_data) - 1 else f

        if f == c:
            return sorted_data[f]

        return sorted_data[f] * (c - k) + sorted_data[c] * (k - f)


# Global metrics collector instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """获取全局指标收集器"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def track_latency(node_name: str, duration_ms: float, **kwargs) -> LatencyMetric:
    """便捷函数: 记录延迟"""
    return get_metrics_collector().track_latency(node_name, duration_ms, **kwargs)


def track_token_usage(
    node_name: str,
    prompt_tokens: int,
    completion_tokens: int,
    model: str,
) -> TokenUsage:
    """便捷函数: 记录 Token 使用"""
    return get_metrics_collector().track_token_usage(
        node_name, prompt_tokens, completion_tokens, model
    )


def track_cost(node_name: str, cost_usd: float, source: str, **kwargs) -> CostRecord:
    """便捷函数: 记录成本"""
    return get_metrics_collector().track_cost(node_name, cost_usd, source, **kwargs)
