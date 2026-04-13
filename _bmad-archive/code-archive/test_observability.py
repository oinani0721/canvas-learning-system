"""
LangSmith可观测性模块单元测试

Story 12.12: LangSmith集成测试

测试覆盖:
- 配置管理
- 追踪装饰器
- 性能指标收集
- 成本计算

Author: Canvas Learning System Team
Version: 1.0.0
Created: 2025-11-29
"""

import asyncio
import os
from unittest.mock import patch

import pytest

# Import modules under test
from agentic_rag.observability.config import (
    LangSmithConfig,
    _parse_bool_env,
    configure_langsmith,
    get_langsmith_config,
)
from agentic_rag.observability.metrics import (
    MODEL_PRICING,
    CostRecord,
    LatencyMetric,
    MetricsCollector,
    TokenUsage,
    get_metrics_collector,
    track_cost,
    track_latency,
    track_token_usage,
)
from agentic_rag.observability.tracing import (
    _is_async_function,
    trace_context,
    traceable_fusion,
    traceable_node,
    traceable_reranking,
    traceable_retrieval,
)

# ========================================
# Test Configuration Module
# ========================================

class TestLangSmithConfig:
    """测试LangSmithConfig配置类"""

    def test_default_config(self):
        """测试默认配置"""
        config = LangSmithConfig()

        assert config.enabled is True
        assert config.api_key is None
        assert config.api_url == "https://api.smith.langchain.com"
        assert config.project_name == "canvas-agentic-rag"
        assert config.workspace_id is None
        assert config.sampling_rate == 1.0
        assert "canvas" in config.tags
        assert "agentic-rag" in config.tags

    def test_custom_config(self):
        """测试自定义配置"""
        config = LangSmithConfig(
            enabled=False,
            api_key="test-key",
            project_name="test-project",
            sampling_rate=0.5,
            tags=["custom"],
        )

        assert config.enabled is False
        assert config.api_key == "test-key"
        assert config.project_name == "test-project"
        assert config.sampling_rate == 0.5
        assert config.tags == ["custom"]


class TestConfigureLangsmith:
    """测试configure_langsmith函数"""

    def setup_method(self):
        """清理全局状态"""
        import agentic_rag.observability.config as config_module
        config_module._config = None
        config_module._client = None

    def test_configure_with_params(self):
        """测试通过参数配置"""
        config = configure_langsmith(
            enabled=True,
            api_key="test-api-key",
            project_name="my-project",
            sampling_rate=0.8,
        )

        assert config.enabled is True
        assert config.api_key == "test-api-key"
        assert config.project_name == "my-project"
        assert config.sampling_rate == 0.8

    def test_configure_from_env(self):
        """测试从环境变量配置"""
        with patch.dict(os.environ, {
            "LANGSMITH_TRACING": "true",
            "LANGSMITH_API_KEY": "env-api-key",
            "LANGSMITH_PROJECT": "env-project",
        }):
            # Reset config
            import agentic_rag.observability.config as config_module
            config_module._config = None

            config = configure_langsmith()

            assert config.enabled is True
            assert config.api_key == "env-api-key"
            assert config.project_name == "env-project"

    def test_get_langsmith_config_lazy_init(self):
        """测试懒加载配置"""
        import agentic_rag.observability.config as config_module
        config_module._config = None

        config = get_langsmith_config()

        assert config is not None
        assert isinstance(config, LangSmithConfig)


class TestParseBoolEnv:
    """测试环境变量布尔值解析"""

    @pytest.mark.parametrize("value,expected", [
        ("true", True),
        ("True", True),
        ("TRUE", True),
        ("1", True),
        ("yes", True),
        ("on", True),
        ("false", False),
        ("False", False),
        ("FALSE", False),
        ("0", False),
        ("no", False),
        ("off", False),
    ])
    def test_parse_bool_values(self, value, expected):
        """测试各种布尔值解析"""
        with patch.dict(os.environ, {"TEST_BOOL": value}):
            result = _parse_bool_env("TEST_BOOL")
            assert result == expected

    def test_parse_bool_default(self):
        """测试默认值"""
        result = _parse_bool_env("NON_EXISTENT_VAR", default=True)
        assert result is True

        result = _parse_bool_env("NON_EXISTENT_VAR", default=False)
        assert result is False


# ========================================
# Test Metrics Module
# ========================================

class TestMetricsCollector:
    """测试MetricsCollector类"""

    def setup_method(self):
        """创建新的收集器"""
        self.collector = MetricsCollector(max_history=100)

    def test_track_latency(self):
        """测试延迟追踪"""
        metric = self.collector.track_latency(
            node_name="retrieve_graphiti",
            duration_ms=45.5,
            success=True,
        )

        assert isinstance(metric, LatencyMetric)
        assert metric.node_name == "retrieve_graphiti"
        assert metric.duration_ms == 45.5
        assert metric.success is True
        assert metric.error is None

    def test_track_latency_with_error(self):
        """测试带错误的延迟追踪"""
        metric = self.collector.track_latency(
            node_name="retrieve_lancedb",
            duration_ms=100.0,
            success=False,
            error="Connection timeout",
        )

        assert metric.success is False
        assert metric.error == "Connection timeout"

    def test_track_token_usage(self):
        """测试Token使用追踪"""
        usage = self.collector.track_token_usage(
            node_name="rerank_cohere",
            prompt_tokens=500,
            completion_tokens=0,
            model="rerank-english-v3.0",
        )

        assert isinstance(usage, TokenUsage)
        assert usage.prompt_tokens == 500
        assert usage.completion_tokens == 0
        assert usage.total_tokens == 500
        assert usage.model == "rerank-english-v3.0"

    def test_track_cost(self):
        """测试成本追踪"""
        record = self.collector.track_cost(
            node_name="rerank_cohere",
            cost_usd=0.005,
            source="cohere",
            details={"documents": 50},
        )

        assert isinstance(record, CostRecord)
        assert record.cost_usd == 0.005
        assert record.source == "cohere"
        assert record.details["documents"] == 50

    def test_get_latency_stats(self):
        """测试延迟统计"""
        # 添加多个延迟记录
        for i in range(10):
            self.collector.track_latency(
                node_name="test_node",
                duration_ms=float(i * 10 + 10),  # 10, 20, 30, ..., 100
            )

        stats = self.collector.get_latency_stats("test_node")

        assert stats["count"] == 10
        assert stats["mean_ms"] == 55.0  # (10+20+...+100)/10 = 55
        assert stats["min_ms"] == 10.0
        assert stats["max_ms"] == 100.0
        assert "p50_ms" in stats
        assert "p95_ms" in stats
        assert "p99_ms" in stats

    def test_get_latency_stats_empty(self):
        """测试空统计"""
        stats = self.collector.get_latency_stats("nonexistent")
        assert stats["count"] == 0

    def test_get_token_stats(self):
        """测试Token统计"""
        self.collector.track_token_usage("node1", 100, 50, "gpt-4o")
        self.collector.track_token_usage("node2", 200, 100, "gpt-4o")

        stats = self.collector.get_token_stats()

        assert stats["total_tokens"] == 450  # 150 + 300
        assert stats["total_tokens_by_model"]["gpt-4o"] == 450
        assert stats["record_count"] == 2

    def test_get_cost_stats(self):
        """测试成本统计"""
        self.collector.track_cost("node1", 0.01, "openai")
        self.collector.track_cost("node2", 0.005, "cohere")
        self.collector.track_cost("node1", 0.02, "openai")

        stats = self.collector.get_cost_stats()

        assert stats["total_cost_usd"] == pytest.approx(0.035)
        assert stats["cost_by_source"]["openai"] == pytest.approx(0.03)
        assert stats["cost_by_source"]["cohere"] == pytest.approx(0.005)
        assert stats["cost_by_node"]["node1"] == pytest.approx(0.03)

    def test_get_summary(self):
        """测试完整摘要"""
        self.collector.track_latency("node1", 50.0)
        self.collector.track_token_usage("node1", 100, 50, "gpt-4o")
        self.collector.track_cost("node1", 0.01, "openai")

        summary = self.collector.get_summary()

        assert "latency" in summary
        assert "tokens" in summary
        assert "costs" in summary
        assert "timestamp" in summary

    def test_reset(self):
        """测试重置"""
        self.collector.track_latency("node1", 50.0)
        self.collector.track_token_usage("node1", 100, 50, "gpt-4o")

        self.collector.reset()

        stats = self.collector.get_latency_stats()
        assert stats["count"] == 0

        token_stats = self.collector.get_token_stats()
        assert token_stats["total_tokens"] == 0

    def test_max_history_limit(self):
        """测试历史记录限制"""
        collector = MetricsCollector(max_history=5)

        for i in range(10):
            collector.track_latency("node", float(i))

        # 应该只保留最后5条
        assert len(collector._latencies) == 5


class TestModelPricing:
    """测试模型定价"""

    def test_pricing_exists(self):
        """测试定价数据存在"""
        assert "gpt-4o" in MODEL_PRICING
        assert "gpt-4o-mini" in MODEL_PRICING
        assert "text-embedding-3-small" in MODEL_PRICING
        assert "rerank-english-v3.0" in MODEL_PRICING
        assert "bge-reranker-base" in MODEL_PRICING

    def test_local_model_free(self):
        """测试本地模型免费"""
        assert MODEL_PRICING["bge-reranker-base"]["input"] == 0.0
        assert MODEL_PRICING["bge-reranker-base"]["output"] == 0.0


class TestCostCalculation:
    """测试成本计算"""

    def test_calculate_gpt4o_cost(self):
        """测试GPT-4o成本计算"""
        collector = MetricsCollector()

        # 1000 input tokens, 500 output tokens
        collector.track_token_usage(
            "test", 1000, 500, "gpt-4o"
        )

        # Check cost was recorded
        cost_stats = collector.get_cost_stats()

        # gpt-4o: input=0.005/1K, output=0.015/1K
        # Expected: 1000*0.005/1000 + 500*0.015/1000 = 0.005 + 0.0075 = 0.0125
        assert cost_stats["total_cost_usd"] == pytest.approx(0.0125)


# ========================================
# Test Tracing Decorators
# ========================================

class TestTracingDecorators:
    """测试追踪装饰器"""

    def test_is_async_function(self):
        """测试异步函数检测"""
        async def async_func():
            pass

        def sync_func():
            pass

        assert _is_async_function(async_func) is True
        assert _is_async_function(sync_func) is False

    def test_traceable_node_sync(self):
        """测试同步函数装饰器"""
        @traceable_node(name="test_sync")
        def sync_function(x):
            return x * 2

        result = sync_function(5)
        assert result == 10

    def test_traceable_node_async(self):
        """测试异步函数装饰器"""
        @traceable_node(name="test_async")
        async def async_function(x):
            await asyncio.sleep(0.01)
            return x * 2

        result = asyncio.run(async_function(5))
        assert result == 10

    def test_traceable_retrieval(self):
        """测试检索装饰器"""
        @traceable_retrieval(source="graphiti")
        async def retrieve(query):
            return [{"content": query}]

        result = asyncio.run(retrieve("test query"))
        assert result == [{"content": "test query"}]

    def test_traceable_fusion(self):
        """测试融合装饰器"""
        @traceable_fusion(algorithm="rrf")
        def fuse(results):
            return results

        result = fuse([1, 2, 3])
        assert result == [1, 2, 3]

    def test_traceable_reranking(self):
        """测试重排序装饰器"""
        @traceable_reranking(strategy="local")
        def rerank(results):
            return sorted(results)

        result = rerank([3, 1, 2])
        assert result == [1, 2, 3]


class TestTraceContext:
    """测试追踪上下文管理器"""

    def test_trace_context_basic(self):
        """测试基本上下文"""
        with trace_context(name="test_operation") as ctx:
            assert ctx["name"] == "test_operation"
            assert "start_time" in ctx

    def test_trace_context_with_inputs(self):
        """测试带输入的上下文"""
        with trace_context(
            name="test_op",
            run_type="retriever",
            inputs={"query": "test"},
            tags=["test"],
        ) as ctx:
            assert ctx["run_type"] == "retriever"
            assert ctx["inputs"]["query"] == "test"
            assert "test" in ctx["tags"]

    def test_trace_context_records_duration(self):
        """测试记录持续时间"""
        import time

        with trace_context(name="timed_op") as ctx:
            time.sleep(0.05)

        assert "end_time" in ctx
        assert "duration_ms" in ctx
        assert ctx["duration_ms"] >= 50  # At least 50ms


# ========================================
# Test Global Functions
# ========================================

class TestGlobalFunctions:
    """测试全局便捷函数"""

    def setup_method(self):
        """重置全局收集器"""
        import agentic_rag.observability.metrics as metrics_module
        metrics_module._metrics_collector = None

    def test_get_metrics_collector_singleton(self):
        """测试单例模式"""
        collector1 = get_metrics_collector()
        collector2 = get_metrics_collector()

        assert collector1 is collector2

    def test_track_latency_global(self):
        """测试全局延迟追踪"""
        metric = track_latency("global_node", 25.0)

        assert metric.node_name == "global_node"
        assert metric.duration_ms == 25.0

    def test_track_token_usage_global(self):
        """测试全局Token追踪"""
        usage = track_token_usage("global_node", 100, 50, "gpt-4o")

        assert usage.total_tokens == 150

    def test_track_cost_global(self):
        """测试全局成本追踪"""
        record = track_cost("global_node", 0.01, "api")

        assert record.cost_usd == 0.01


# ========================================
# Test Traced Nodes
# ========================================

class TestTracedNodes:
    """测试带追踪的节点"""

    def test_traced_nodes_import(self):
        """测试导入追踪节点"""
        from agentic_rag.traced_nodes import (
            traced_check_quality,
            traced_fuse_results,
            traced_rerank_results,
            traced_retrieve_graphiti,
            traced_retrieve_lancedb,
        )

        # 确保都是可调用的
        assert callable(traced_retrieve_graphiti)
        assert callable(traced_retrieve_lancedb)
        assert callable(traced_fuse_results)
        assert callable(traced_rerank_results)
        assert callable(traced_check_quality)


# ========================================
# Test Thread Safety
# ========================================

class TestThreadSafety:
    """测试线程安全性"""

    def test_concurrent_latency_tracking(self):
        """测试并发延迟追踪"""
        import threading

        collector = MetricsCollector()
        errors = []

        def track_many():
            try:
                for i in range(100):
                    collector.track_latency(f"node_{i % 5}", float(i))
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=track_many) for _ in range(5)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0

        # 应该有500条记录 (5 threads * 100 each)
        stats = collector.get_latency_stats()
        assert stats["count"] == 500


# ========================================
# Integration Tests
# ========================================

class TestObservabilityIntegration:
    """可观测性模块集成测试"""

    def test_full_workflow(self):
        """测试完整工作流"""
        # 1. Configure
        configure_langsmith(
            enabled=True,
            api_key="test-key",
            sampling_rate=1.0,
        )

        # 2. Track metrics
        collector = MetricsCollector()

        # Simulate retrieval
        collector.track_latency("retrieve_graphiti", 45.0)
        collector.track_latency("retrieve_lancedb", 30.0)

        # Simulate fusion
        collector.track_latency("fuse_results", 10.0)

        # Simulate reranking with token usage
        collector.track_latency("rerank_cohere", 150.0)
        collector.track_token_usage("rerank_cohere", 500, 0, "rerank-english-v3.0")

        # 3. Get summary
        summary = collector.get_summary()

        assert summary["latency"]["count"] == 4
        assert summary["tokens"]["total_tokens"] == 500
        assert "costs" in summary

    def test_disabled_tracing(self):
        """测试禁用追踪"""
        configure_langsmith(enabled=False)

        @traceable_node(name="test_disabled")
        def test_func(x):
            return x * 2

        # 应该正常工作，不会因为禁用追踪而出错
        result = test_func(5)
        assert result == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
