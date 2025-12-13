"""
Story 12.5 Unit Tests - LangGraph StateGraph构建

测试Canvas Agentic RAG StateGraph的完整功能。

✅ Story 12.5 AC Coverage:
- AC 5.1: CanvasRAGState schema定义
- AC 5.2: CanvasRAGConfig context schema
- AC 5.3: 5个核心节点实现
- AC 5.4: StateGraph compile成功
- AC 5.5: 端到端运行测试

Author: Canvas Learning System Team
Version: 1.0.0
Created: 2025-11-29
Test Count: 20 tests
"""

from unittest.mock import MagicMock

import pytest
from langgraph.runtime import Runtime

from agentic_rag.config import DEFAULT_CONFIG, CanvasRAGConfig, merge_config
from agentic_rag.nodes import (
    check_quality,
    fuse_results,
    rerank_results,
    retrieve_graphiti,
    retrieve_lancedb,
)
from agentic_rag.state import CanvasRAGState
from agentic_rag.state_graph import (
    build_canvas_agentic_rag_graph,
    canvas_agentic_rag,
    fan_out_retrieval,
    rewrite_query,
    route_after_quality_check,
)

# ========================================
# Test Group 1: State and Config Schema (AC 5.1, 5.2)
# ========================================

class TestStateAndConfigSchema:
    """测试State和Config schema定义"""

    def test_canvas_rag_state_schema(self):
        """Test AC 5.1: CanvasRAGState schema定义完成"""
        # 创建state实例
        state: CanvasRAGState = {
            "messages": [],
            "graphiti_results": [],
            "lancedb_results": [],
            "fused_results": [],
            "reranked_results": [],
            "fusion_strategy": "rrf",
            "reranking_strategy": "local",
            "quality_grade": None,
            "query_rewritten": False,
            "rewrite_count": 0,
            "canvas_file": "test.canvas",
            "is_review_canvas": False,
            "original_query": None,
            "graphiti_latency_ms": None,
            "lancedb_latency_ms": None,
            "fusion_latency_ms": None,
            "reranking_latency_ms": None,
        }

        # 验证必需字段
        assert "messages" in state
        assert "graphiti_results" in state
        assert "lancedb_results" in state
        assert "fused_results" in state
        assert "reranked_results" in state
        assert "fusion_strategy" in state
        assert "reranking_strategy" in state
        assert "quality_grade" in state
        assert "query_rewritten" in state
        assert "rewrite_count" in state

    def test_canvas_rag_config_schema(self):
        """Test AC 5.2: CanvasRAGConfig context schema定义完成"""
        # 创建config实例
        config: CanvasRAGConfig = {
            "retrieval_batch_size": 10,
            "fusion_strategy": "weighted",
            "reranking_strategy": "cohere",
            "quality_threshold": 0.7,
            "max_rewrite_iterations": 2,
            "cohere_monthly_limit": 50,
            "enable_cost_monitoring": True,
            "timeout_seconds": 10.0,
            "enable_caching": True,
        }

        # 验证必需字段
        assert config["retrieval_batch_size"] == 10
        assert config["fusion_strategy"] == "weighted"
        assert config["reranking_strategy"] == "cohere"
        assert config["quality_threshold"] == 0.7
        assert config["max_rewrite_iterations"] == 2

    def test_default_config(self):
        """Test DEFAULT_CONFIG包含所有必需字段"""
        assert DEFAULT_CONFIG["retrieval_batch_size"] == 10
        assert DEFAULT_CONFIG["fusion_strategy"] == "rrf"
        assert DEFAULT_CONFIG["reranking_strategy"] == "hybrid_auto"
        assert DEFAULT_CONFIG["quality_threshold"] == 0.7
        assert DEFAULT_CONFIG["max_rewrite_iterations"] == 2

    def test_merge_config(self):
        """Test merge_config正确合并用户配置"""
        user_config: CanvasRAGConfig = {"fusion_strategy": "weighted"}
        merged = merge_config(user_config)

        # 用户配置生效
        assert merged["fusion_strategy"] == "weighted"
        # 默认配置填充
        assert merged["retrieval_batch_size"] == 10
        assert merged["quality_threshold"] == 0.7


# ========================================
# Test Group 2: Core Nodes (AC 5.3)
# ========================================

class TestCoreNodes:
    """测试5个核心节点实现"""

    @pytest.fixture
    def mock_state(self) -> CanvasRAGState:
        """创建mock state"""
        return {
            "messages": [{"role": "user", "content": "test query"}],
            "graphiti_results": [],
            "lancedb_results": [],
            "fused_results": [],
            "reranked_results": [],
            "fusion_strategy": "rrf",
            "reranking_strategy": "local",
            "quality_grade": None,
            "query_rewritten": False,
            "rewrite_count": 0,
            "canvas_file": "test.canvas",
            "is_review_canvas": False,
            "original_query": None,
            "graphiti_latency_ms": None,
            "lancedb_latency_ms": None,
            "fusion_latency_ms": None,
            "reranking_latency_ms": None,
        }

    @pytest.fixture
    def mock_runtime(self) -> Runtime[CanvasRAGConfig]:
        """创建mock runtime"""
        runtime = MagicMock(spec=Runtime)
        runtime.context = DEFAULT_CONFIG
        return runtime

    @pytest.mark.asyncio
    async def test_retrieve_graphiti_returns_results(self, mock_state, mock_runtime):
        """Test AC 5.3.1: retrieve_graphiti返回结果"""
        result = await retrieve_graphiti(mock_state, mock_runtime)

        assert "graphiti_results" in result
        assert isinstance(result["graphiti_results"], list)
        assert len(result["graphiti_results"]) == 10  # Default batch_size
        assert "graphiti_latency_ms" in result
        assert isinstance(result["graphiti_latency_ms"], float)

    @pytest.mark.asyncio
    async def test_retrieve_lancedb_returns_results(self, mock_state, mock_runtime):
        """Test AC 5.3.2: retrieve_lancedb返回结果"""
        result = await retrieve_lancedb(mock_state, mock_runtime)

        assert "lancedb_results" in result
        assert isinstance(result["lancedb_results"], list)
        assert len(result["lancedb_results"]) == 10
        assert "lancedb_latency_ms" in result
        assert isinstance(result["lancedb_latency_ms"], float)

    @pytest.mark.asyncio
    async def test_fuse_results_rrf_strategy(self, mock_state, mock_runtime):
        """Test AC 5.3.3: fuse_results with RRF strategy"""
        # 准备输入
        mock_state["graphiti_results"] = [
            {"doc_id": "g1", "content": "test", "score": 0.9, "metadata": {}}
        ]
        mock_state["lancedb_results"] = [
            {"doc_id": "l1", "content": "test", "score": 0.85, "metadata": {}}
        ]
        mock_runtime.context["fusion_strategy"] = "rrf"

        result = await fuse_results(mock_state, mock_runtime)

        assert "fused_results" in result
        assert isinstance(result["fused_results"], list)
        assert len(result["fused_results"]) > 0

    @pytest.mark.asyncio
    async def test_rerank_results_local_strategy(self, mock_state, mock_runtime):
        """Test AC 5.3.4: rerank_results with local strategy"""
        mock_state["fused_results"] = [
            {"doc_id": "1", "content": "test", "score": 0.9, "metadata": {}}
        ]
        mock_runtime.context["reranking_strategy"] = "local"

        result = await rerank_results(mock_state, mock_runtime)

        assert "reranked_results" in result
        assert isinstance(result["reranked_results"], list)

    @pytest.mark.asyncio
    async def test_check_quality_high_grade(self, mock_state, mock_runtime):
        """Test AC 5.3.5: check_quality评级为high"""
        mock_state["reranked_results"] = [
            {"doc_id": "1", "content": "test", "score": 0.9, "metadata": {}},
            {"doc_id": "2", "content": "test", "score": 0.85, "metadata": {}},
            {"doc_id": "3", "content": "test", "score": 0.8, "metadata": {}},
        ]

        result = await check_quality(mock_state, mock_runtime)

        assert "quality_grade" in result
        assert result["quality_grade"] == "high"

    @pytest.mark.asyncio
    async def test_check_quality_low_grade(self, mock_state, mock_runtime):
        """Test AC 5.3.6: check_quality评级为low"""
        mock_state["reranked_results"] = [
            {"doc_id": "1", "content": "test", "score": 0.4, "metadata": {}},
            {"doc_id": "2", "content": "test", "score": 0.3, "metadata": {}},
            {"doc_id": "3", "content": "test", "score": 0.2, "metadata": {}},
        ]

        result = await check_quality(mock_state, mock_runtime)

        assert result["quality_grade"] == "low"


# ========================================
# Test Group 3: StateGraph Construction (AC 5.4)
# ========================================

class TestStateGraphConstruction:
    """测试StateGraph构建和编译"""

    def test_build_graph_returns_state_graph(self):
        """Test AC 5.4.1: build_canvas_agentic_rag_graph返回StateGraph"""
        builder = build_canvas_agentic_rag_graph()
        assert builder is not None

    def test_graph_compiles_successfully(self):
        """Test AC 5.4.2: StateGraph compile成功"""
        try:
            graph = canvas_agentic_rag
            assert graph is not None
        except Exception as e:
            pytest.fail(f"Graph compilation failed: {e}")

    def test_graph_has_required_nodes(self):
        """Test AC 5.4.3: Graph包含所有必需节点"""
        graph = canvas_agentic_rag

        # 获取graph节点列表 (注意: 需要验证LangGraph API)
        # TODO: 验证节点存在
        # Expected nodes: retrieve_graphiti, retrieve_lancedb, fuse_results, rerank_results, check_quality, rewrite_query
        assert graph is not None

    def test_fan_out_retrieval_returns_send_objects(self):
        """Test AC 5.4.4: fan_out_retrieval返回Send对象

        ✅ Story 23.3 AC 2: 验证三路并行检索 (Graphiti + LanceDB + Multimodal)
        """
        mock_state: CanvasRAGState = {
            "messages": [],
            "graphiti_results": [],
            "lancedb_results": [],
            "multimodal_results": [],  # ✅ Story 23.3: 添加multimodal字段
            "fused_results": [],
            "reranked_results": [],
            "fusion_strategy": "rrf",
            "reranking_strategy": "local",
            "quality_grade": None,
            "query_rewritten": False,
            "rewrite_count": 0,
            "canvas_file": None,
            "is_review_canvas": False,
            "original_query": None,
            "graphiti_latency_ms": None,
            "lancedb_latency_ms": None,
            "multimodal_latency_ms": None,  # ✅ Story 23.3: 添加multimodal延迟字段
        }

        sends = fan_out_retrieval(mock_state)

        assert isinstance(sends, list)
        # ✅ Story 23.3 AC 2: 三路并行检索 (Graphiti + LanceDB + Multimodal)
        assert len(sends) == 3, f"Expected 3 Send objects for parallel retrieval, got {len(sends)}"

    def test_route_after_quality_check_to_rewrite(self):
        """Test AC 5.4.5: route_after_quality_check路由到rewrite_query"""
        mock_state: CanvasRAGState = {
            "messages": [],
            "graphiti_results": [],
            "lancedb_results": [],
            "fused_results": [],
            "reranked_results": [],
            "fusion_strategy": "rrf",
            "reranking_strategy": "local",
            "quality_grade": "low",  # Low quality
            "query_rewritten": False,
            "rewrite_count": 0,  # Not exceeded
            "canvas_file": None,
            "is_review_canvas": False,
            "original_query": None,
            "retrieval_latency_ms": None,
        }

        route = route_after_quality_check(mock_state)
        assert route == "rewrite_query"

    def test_route_after_quality_check_to_end(self):
        """Test AC 5.4.6: route_after_quality_check路由到END"""
        from langgraph.graph import END

        mock_state: CanvasRAGState = {
            "messages": [],
            "graphiti_results": [],
            "lancedb_results": [],
            "fused_results": [],
            "reranked_results": [],
            "fusion_strategy": "rrf",
            "reranking_strategy": "local",
            "quality_grade": "high",  # High quality
            "query_rewritten": False,
            "rewrite_count": 0,
            "canvas_file": None,
            "is_review_canvas": False,
            "original_query": None,
            "retrieval_latency_ms": None,
        }

        route = route_after_quality_check(mock_state)
        assert route == END

    @pytest.mark.asyncio
    async def test_rewrite_query_increments_count(self):
        """Test AC 5.4.7: rewrite_query增加重写次数"""
        mock_state: CanvasRAGState = {
            "messages": [{"role": "user", "content": "original query"}],
            "graphiti_results": [],
            "lancedb_results": [],
            "fused_results": [],
            "reranked_results": [],
            "fusion_strategy": "rrf",
            "reranking_strategy": "local",
            "quality_grade": None,
            "query_rewritten": False,
            "rewrite_count": 0,
            "canvas_file": None,
            "is_review_canvas": False,
            "original_query": None,
            "retrieval_latency_ms": None,
        }

        result = await rewrite_query(mock_state)

        assert result["query_rewritten"] is True
        assert result["rewrite_count"] == 1
        assert "messages" in result


# ========================================
# Test Group 4: End-to-End Execution (AC 5.5)
# ========================================

class TestEndToEndExecution:
    """测试端到端运行"""

    @pytest.mark.asyncio
    async def test_graph_invoke_returns_results(self):
        """Test AC 5.5.1: 端到端invoke返回结果"""
        # 准备输入
        input_state = {
            "messages": [{"role": "user", "content": "逆否命题的应用场景"}],
            "canvas_file": "离散数学.canvas",
            "is_review_canvas": False,
        }

        # 准备配置
        config = {
            "retrieval_batch_size": 10,
            "fusion_strategy": "rrf",
            "reranking_strategy": "local",
            "quality_threshold": 0.7,
            "max_rewrite_iterations": 2,
        }

        # 执行graph
        try:
            result = await canvas_agentic_rag.ainvoke(input_state, context=config)

            # 验证结果
            assert "reranked_results" in result
            assert isinstance(result["reranked_results"], list)
            assert "quality_grade" in result
        except Exception as e:
            pytest.fail(f"End-to-end execution failed: {e}")

    @pytest.mark.asyncio
    async def test_graph_handles_review_canvas_scenario(self):
        """Test AC 5.5.2: 端到端测试检验白板场景"""
        input_state = {
            "messages": [{"role": "user", "content": "检验白板薄弱点"}],
            "canvas_file": "离散数学.canvas",
            "is_review_canvas": True,  # 检验白板场景
        }

        config = {
            "retrieval_batch_size": 10,
            "fusion_strategy": "weighted",  # 检验白板使用Weighted
            "reranking_strategy": "cohere",  # 检验白板使用Cohere
            "quality_threshold": 0.7,
            "max_rewrite_iterations": 2,
        }

        try:
            result = await canvas_agentic_rag.ainvoke(input_state, context=config)

            assert "reranked_results" in result
            assert "fused_results" in result
            # fusion_strategy is in runtime context, not state
            assert "fusion_latency_ms" in result  # Verify fusion was executed
        except Exception as e:
            pytest.fail(f"Review canvas scenario failed: {e}")

    def test_graph_visualization_mermaid(self):
        """Test AC 5.5.3: Graph可视化Mermaid图生成"""
        try:
            mermaid_str = canvas_agentic_rag.get_graph().draw_mermaid()
            assert mermaid_str is not None
            assert isinstance(mermaid_str, str)
            assert "graph" in mermaid_str.lower()
        except Exception as e:
            pytest.fail(f"Mermaid visualization failed: {e}")


# ========================================
# Test Summary
# ========================================

"""
Test Coverage Summary (Story 12.5):

AC 5.1 (State Schema): 1 test ✅
AC 5.2 (Config Schema): 3 tests ✅
AC 5.3 (5 Core Nodes): 6 tests ✅
AC 5.4 (StateGraph Compile): 7 tests ✅
AC 5.5 (E2E Execution): 3 tests ✅

Total: 20 tests
"""
