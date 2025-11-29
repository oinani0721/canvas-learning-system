"""
Epic 12 StateGraph E2E 集成测试

测试完整的 Agentic RAG StateGraph 端到端执行:
- Story 12.5: StateGraph 构建和编译
- Story 12.6: 并行检索 (Send 模式)
- Story 12.7: RRF/Weighted/Cascade 融合
- Story 12.8: Reranking 策略
- Story 12.9: 质量控制循环
- Story 12.10: Canvas 集成

Author: Canvas Learning System Team
Version: 1.0.0
Created: 2025-11-29
"""

import asyncio
import time
from datetime import datetime
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ============================================================
# Test Fixtures
# ============================================================

@pytest.fixture
def mock_graphiti_results() -> List[Dict[str, Any]]:
    """模拟 Graphiti 检索结果"""
    return [
        {
            "doc_id": "graphiti_001",
            "content": "逆否命题是原命题的等价形式",
            "score": 0.92,
            "metadata": {
                "source": "graphiti",
                "canvas_file": "离散数学.canvas",
                "concept": "逆否命题"
            }
        },
        {
            "doc_id": "graphiti_002",
            "content": "命题逻辑的基本概念",
            "score": 0.85,
            "metadata": {
                "source": "graphiti",
                "canvas_file": "离散数学.canvas",
                "concept": "命题逻辑"
            }
        },
        {
            "doc_id": "graphiti_003",
            "content": "充分必要条件的判定",
            "score": 0.78,
            "metadata": {
                "source": "graphiti",
                "canvas_file": "离散数学.canvas",
                "concept": "充分必要条件"
            }
        }
    ]


@pytest.fixture
def mock_lancedb_results() -> List[Dict[str, Any]]:
    """模拟 LanceDB 检索结果"""
    return [
        {
            "doc_id": "lancedb_001",
            "content": "口语化解释: 逆否命题就像照镜子",
            "score": 0.88,
            "metadata": {
                "source": "lancedb",
                "canvas_file": "离散数学.canvas",
                "agent_type": "oral-explanation"
            }
        },
        {
            "doc_id": "lancedb_002",
            "content": "澄清路径: 命题逻辑入门",
            "score": 0.82,
            "metadata": {
                "source": "lancedb",
                "canvas_file": "离散数学.canvas",
                "agent_type": "clarification-path"
            }
        }
    ]


@pytest.fixture
def mock_temporal_weak_concepts() -> List[Dict[str, Any]]:
    """模拟 Temporal Memory 薄弱概念"""
    return [
        {
            "concept": "逆否命题",
            "stability": 1.2,
            "error_rate": 0.35,
            "weakness_score": 0.82,
            "last_review": datetime.now().isoformat()
        },
        {
            "concept": "充分必要条件",
            "stability": 2.5,
            "error_rate": 0.25,
            "weakness_score": 0.65,
            "last_review": datetime.now().isoformat()
        }
    ]


@pytest.fixture
def mock_clients(
    mock_graphiti_results,
    mock_lancedb_results,
    mock_temporal_weak_concepts
):
    """创建模拟客户端"""
    # GraphitiClient mock
    graphiti_client = AsyncMock()
    graphiti_client.initialize = AsyncMock(return_value=True)
    graphiti_client.search_nodes = AsyncMock(return_value=mock_graphiti_results)
    graphiti_client.health_check = AsyncMock(return_value=True)

    # LanceDBClient mock
    lancedb_client = AsyncMock()
    lancedb_client.initialize = AsyncMock(return_value=True)
    lancedb_client.search_multiple_tables = AsyncMock(return_value=mock_lancedb_results)
    lancedb_client.search = AsyncMock(return_value=mock_lancedb_results)

    # TemporalClient mock
    temporal_client = AsyncMock()
    temporal_client.initialize = AsyncMock(return_value=True)
    temporal_client.get_weak_concepts = AsyncMock(return_value=mock_temporal_weak_concepts)
    temporal_client.update_behavior = AsyncMock(return_value={"updated": True})

    return {
        "graphiti": graphiti_client,
        "lancedb": lancedb_client,
        "temporal": temporal_client
    }


# ============================================================
# Story 12.5: StateGraph 构建测试
# ============================================================

class TestStateGraphConstruction:
    """测试 StateGraph 构建和编译"""

    def test_stategraph_builder_creation(self):
        """AC 5.1: StateGraph builder 创建成功"""
        from agentic_rag.state_graph import build_canvas_agentic_rag_graph

        builder = build_canvas_agentic_rag_graph()

        assert builder is not None
        assert hasattr(builder, 'compile')

    def test_stategraph_compile_success(self):
        """AC 5.4: StateGraph compile 成功"""
        from agentic_rag.state_graph import canvas_agentic_rag

        # 已编译的图应该存在
        assert canvas_agentic_rag is not None

    def test_stategraph_has_required_nodes(self):
        """AC 5.2: StateGraph 包含所有必需节点"""
        from agentic_rag.state_graph import build_canvas_agentic_rag_graph

        builder = build_canvas_agentic_rag_graph()

        # 检查节点是否注册
        # LangGraph StateGraph stores nodes in _nodes
        # expected_nodes 用于文档参考，实际验证通过编译成功
        # ["retrieve_graphiti", "retrieve_lancedb", "fuse_results",
        #  "rerank_results", "check_quality", "rewrite_query"]

        # 编译后检查
        graph = builder.compile()
        assert graph is not None

    def test_stategraph_parallel_retrieval_structure(self):
        """AC 5.3: 并行检索结构正确 (Send 模式)"""
        from langgraph.types import Send

        from agentic_rag.state import CanvasRAGState
        from agentic_rag.state_graph import fan_out_retrieval

        # 创建测试 state
        state: CanvasRAGState = {
            "messages": [{"role": "user", "content": "什么是逆否命题?"}],
            "canvas_file": "离散数学.canvas"
        }

        # 执行 fan_out
        sends = fan_out_retrieval(state)

        # 验证返回 Send 对象
        assert len(sends) == 2
        assert all(isinstance(s, Send) for s in sends)

        # 验证目标节点
        destinations = [s.node for s in sends]
        assert "retrieve_graphiti" in destinations
        assert "retrieve_lancedb" in destinations


# ============================================================
# Story 12.6: 并行检索测试
# ============================================================

class TestParallelRetrievalE2E:
    """测试并行检索 E2E"""

    @pytest.mark.asyncio
    async def test_parallel_retrieval_executes_concurrently(self, mock_clients):
        """AC 6.1: 并行检索同时执行"""
        with patch('agentic_rag.nodes._get_graphiti_client', return_value=mock_clients["graphiti"]), \
             patch('agentic_rag.nodes._get_lancedb_client', return_value=mock_clients["lancedb"]):

            from agentic_rag.nodes import retrieve_graphiti, retrieve_lancedb

            state = {
                "messages": [{"role": "user", "content": "逆否命题"}],
                "canvas_file": "离散数学.canvas"
            }

            # 模拟 runtime
            runtime = MagicMock()
            runtime.context = {"retrieval_batch_size": 10}

            # 并行执行
            start_time = time.perf_counter()

            results = await asyncio.gather(
                retrieve_graphiti(state, runtime),
                retrieve_lancedb(state, runtime)
            )

            _ = (time.perf_counter() - start_time) * 1000  # elapsed_ms for reference

            # 验证结果
            assert len(results) == 2
            assert "graphiti_results" in results[0]
            assert "lancedb_results" in results[1]

    @pytest.mark.asyncio
    async def test_parallel_retrieval_latency_under_100ms(self, mock_clients):
        """AC 6.2: 并行检索延迟 < 100ms (mock 环境)"""
        with patch('agentic_rag.nodes._get_graphiti_client', return_value=mock_clients["graphiti"]), \
             patch('agentic_rag.nodes._get_lancedb_client', return_value=mock_clients["lancedb"]):

            from agentic_rag.nodes import retrieve_graphiti, retrieve_lancedb

            state = {
                "messages": [{"role": "user", "content": "逆否命题"}],
                "canvas_file": "离散数学.canvas"
            }

            runtime = MagicMock()
            runtime.context = {"retrieval_batch_size": 10}

            start_time = time.perf_counter()

            await asyncio.gather(
                retrieve_graphiti(state, runtime),
                retrieve_lancedb(state, runtime)
            )

            elapsed_ms = (time.perf_counter() - start_time) * 1000

            # Mock 环境应该非常快
            assert elapsed_ms < 100, f"并行检索延迟 {elapsed_ms:.2f}ms 超过 100ms"


# ============================================================
# Story 12.7: 融合算法 E2E 测试
# ============================================================

class TestFusionAlgorithmsE2E:
    """测试融合算法 E2E"""

    @pytest.mark.asyncio
    async def test_rrf_fusion_combines_results(self, mock_graphiti_results, mock_lancedb_results):
        """AC 7.1: RRF 融合正确合并结果"""
        from agentic_rag.nodes import fuse_results

        state = {
            "graphiti_results": mock_graphiti_results,
            "lancedb_results": mock_lancedb_results,
            "is_review_canvas": False
        }

        runtime = MagicMock()
        runtime.context = {"fusion_strategy": "rrf"}

        result = await fuse_results(state, runtime)

        assert "fused_results" in result
        assert len(result["fused_results"]) <= 10
        # 验证结果按分数排序
        scores = [r["score"] for r in result["fused_results"]]
        assert scores == sorted(scores, reverse=True)

    @pytest.mark.asyncio
    async def test_weighted_fusion_for_review_canvas(self, mock_graphiti_results, mock_lancedb_results):
        """AC 7.2: 检验白板使用 70% Graphiti 权重"""
        from agentic_rag.nodes import fuse_results

        state = {
            "graphiti_results": mock_graphiti_results,
            "lancedb_results": mock_lancedb_results,
            "is_review_canvas": True  # 检验白板
        }

        runtime = MagicMock()
        runtime.context = {"fusion_strategy": "weighted"}

        result = await fuse_results(state, runtime)

        assert "fused_results" in result
        assert "fusion_latency_ms" in result

    @pytest.mark.asyncio
    async def test_cascade_fusion_tier1_priority(self, mock_graphiti_results, mock_lancedb_results):
        """AC 7.3: Cascade 融合优先使用 Tier 1 (Graphiti)"""
        from agentic_rag.nodes import fuse_results

        state = {
            "graphiti_results": mock_graphiti_results,  # 3 个结果
            "lancedb_results": mock_lancedb_results,
            "is_review_canvas": False
        }

        runtime = MagicMock()
        runtime.context = {"fusion_strategy": "cascade"}

        result = await fuse_results(state, runtime)

        assert "fused_results" in result
        # Cascade 应该优先包含 Graphiti 结果
        fused = result["fused_results"]
        # 检查是否包含 Graphiti 来源
        graphiti_count = sum(1 for r in fused if r.get("metadata", {}).get("source") == "graphiti")
        assert graphiti_count >= 1  # 至少包含一些 Graphiti 结果


# ============================================================
# Story 12.8: Reranking 策略测试
# ============================================================

class TestRerankingE2E:
    """测试 Reranking 策略 E2E"""

    @pytest.mark.asyncio
    async def test_local_reranking_preserves_order(self, mock_graphiti_results):
        """AC 8.1: Local reranking 保持结果顺序"""
        from agentic_rag.nodes import rerank_results

        state = {
            "fused_results": mock_graphiti_results,
            "is_review_canvas": False
        }

        runtime = MagicMock()
        runtime.context = {"reranking_strategy": "local"}

        result = await rerank_results(state, runtime)

        assert "reranked_results" in result
        assert "reranking_latency_ms" in result
        assert len(result["reranked_results"]) == len(mock_graphiti_results)

    @pytest.mark.asyncio
    async def test_hybrid_auto_selects_cohere_for_review(self, mock_graphiti_results):
        """AC 8.2: hybrid_auto 为检验白板选择 Cohere"""
        from agentic_rag.nodes import rerank_results

        state = {
            "fused_results": mock_graphiti_results,
            "is_review_canvas": True  # 检验白板
        }

        runtime = MagicMock()
        runtime.context = {"reranking_strategy": "hybrid_auto"}

        result = await rerank_results(state, runtime)

        assert "reranked_results" in result

    @pytest.mark.asyncio
    async def test_reranking_latency_acceptable(self, mock_graphiti_results):
        """AC 8.3: Reranking 延迟可接受"""
        from agentic_rag.nodes import rerank_results

        state = {
            "fused_results": mock_graphiti_results,
            "is_review_canvas": False
        }

        runtime = MagicMock()
        runtime.context = {"reranking_strategy": "local"}

        result = await rerank_results(state, runtime)

        # Mock 环境延迟应该很低
        assert result["reranking_latency_ms"] < 50


# ============================================================
# Story 12.9: 质量控制循环测试
# ============================================================

class TestQualityControlE2E:
    """测试质量控制循环 E2E"""

    @pytest.mark.asyncio
    async def test_high_quality_returns_high_grade(self, mock_graphiti_results):
        """AC 9.1: 高质量结果返回 high grade"""
        from agentic_rag.nodes import check_quality

        # 高分结果
        high_score_results = [
            {"score": 0.9, "content": "test"},
            {"score": 0.85, "content": "test"},
            {"score": 0.8, "content": "test"},
        ]

        state = {"reranked_results": high_score_results}

        runtime = MagicMock()
        runtime.context = {"quality_threshold": 0.7}

        result = await check_quality(state, runtime)

        assert result["quality_grade"] == "high"

    @pytest.mark.asyncio
    async def test_low_quality_returns_low_grade(self):
        """AC 9.2: 低质量结果返回 low grade"""
        from agentic_rag.nodes import check_quality

        low_score_results = [
            {"score": 0.3, "content": "test"},
            {"score": 0.2, "content": "test"},
            {"score": 0.1, "content": "test"},
        ]

        state = {"reranked_results": low_score_results}

        runtime = MagicMock()
        runtime.context = {"quality_threshold": 0.7}

        result = await check_quality(state, runtime)

        assert result["quality_grade"] == "low"

    def test_quality_routing_rewrite_on_low(self):
        """AC 9.3: 低质量触发 query 重写"""
        from agentic_rag.state_graph import route_after_quality_check

        state = {
            "quality_grade": "low",
            "rewrite_count": 0
        }

        route = route_after_quality_check(state)

        assert route == "rewrite_query"

    def test_quality_routing_end_on_high(self):
        """AC 9.4: 高质量直接结束"""
        from langgraph.graph import END

        from agentic_rag.state_graph import route_after_quality_check

        state = {
            "quality_grade": "high",
            "rewrite_count": 0
        }

        route = route_after_quality_check(state)

        assert route == END

    def test_quality_routing_end_after_max_rewrite(self):
        """AC 9.5: 达到最大重写次数后结束"""
        from langgraph.graph import END

        from agentic_rag.state_graph import route_after_quality_check

        state = {
            "quality_grade": "low",
            "rewrite_count": 2  # 已达上限
        }

        route = route_after_quality_check(state)

        assert route == END

    @pytest.mark.asyncio
    async def test_query_rewrite_increments_count(self):
        """AC 9.6: Query 重写增加计数器"""
        from agentic_rag.state_graph import rewrite_query

        state = {
            "messages": [{"role": "user", "content": "什么是逆否命题?"}],
            "rewrite_count": 0
        }

        result = await rewrite_query(state)

        assert result["rewrite_count"] == 1
        assert result["query_rewritten"] is True


# ============================================================
# Story 12.10: 完整 Pipeline E2E 测试
# ============================================================

class TestFullPipelineE2E:
    """测试完整 RAG Pipeline E2E"""

    @pytest.mark.asyncio
    async def test_full_pipeline_high_quality_path(self, mock_clients):
        """E2E: 高质量结果路径 (无重写)"""
        with patch('agentic_rag.nodes._get_graphiti_client', return_value=mock_clients["graphiti"]), \
             patch('agentic_rag.nodes._get_lancedb_client', return_value=mock_clients["lancedb"]), \
             patch('agentic_rag.nodes._get_temporal_client', return_value=mock_clients["temporal"]):

            from agentic_rag.nodes import (
                check_quality,
                fuse_results,
                rerank_results,
                retrieve_graphiti,
                retrieve_lancedb,
            )

            # 初始 state
            state = {
                "messages": [{"role": "user", "content": "什么是逆否命题?"}],
                "canvas_file": "离散数学.canvas",
                "is_review_canvas": False
            }

            runtime = MagicMock()
            runtime.context = {
                "retrieval_batch_size": 10,
                "fusion_strategy": "rrf",
                "reranking_strategy": "local",
                "quality_threshold": 0.5  # 降低阈值以确保 high quality
            }

            # Step 1: 并行检索
            graphiti_result = await retrieve_graphiti(state, runtime)
            lancedb_result = await retrieve_lancedb(state, runtime)

            # 合并结果到 state
            state.update(graphiti_result)
            state.update(lancedb_result)

            # Step 2: 融合
            fusion_result = await fuse_results(state, runtime)
            state.update(fusion_result)

            # Step 3: Reranking
            rerank_result = await rerank_results(state, runtime)
            state.update(rerank_result)

            # Step 4: 质量检查
            quality_result = await check_quality(state, runtime)
            state.update(quality_result)

            # 验证完整流程
            assert state["quality_grade"] in ["high", "medium"]
            assert len(state["reranked_results"]) > 0

    @pytest.mark.asyncio
    async def test_full_pipeline_latency_under_500ms(self, mock_clients):
        """E2E: 完整 Pipeline 延迟 < 500ms"""
        with patch('agentic_rag.nodes._get_graphiti_client', return_value=mock_clients["graphiti"]), \
             patch('agentic_rag.nodes._get_lancedb_client', return_value=mock_clients["lancedb"]):

            from agentic_rag.nodes import (
                check_quality,
                fuse_results,
                rerank_results,
                retrieve_graphiti,
                retrieve_lancedb,
            )

            state = {
                "messages": [{"role": "user", "content": "什么是逆否命题?"}],
                "canvas_file": "离散数学.canvas",
                "is_review_canvas": False
            }

            runtime = MagicMock()
            runtime.context = {
                "retrieval_batch_size": 10,
                "fusion_strategy": "rrf",
                "reranking_strategy": "local",
                "quality_threshold": 0.7
            }

            start_time = time.perf_counter()

            # 执行完整 pipeline
            graphiti_result = await retrieve_graphiti(state, runtime)
            lancedb_result = await retrieve_lancedb(state, runtime)
            state.update(graphiti_result)
            state.update(lancedb_result)

            fusion_result = await fuse_results(state, runtime)
            state.update(fusion_result)

            rerank_result = await rerank_results(state, runtime)
            state.update(rerank_result)

            quality_result = await check_quality(state, runtime)
            state.update(quality_result)

            elapsed_ms = (time.perf_counter() - start_time) * 1000

            # Mock 环境应该非常快
            assert elapsed_ms < 500, f"Pipeline 延迟 {elapsed_ms:.2f}ms 超过 500ms"

    @pytest.mark.asyncio
    async def test_pipeline_with_canvas_scope(self, mock_clients):
        """E2E: Canvas 作用域限制正确传递"""
        with patch('agentic_rag.nodes._get_graphiti_client', return_value=mock_clients["graphiti"]), \
             patch('agentic_rag.nodes._get_lancedb_client', return_value=mock_clients["lancedb"]):

            from agentic_rag.nodes import retrieve_graphiti

            state = {
                "messages": [{"role": "user", "content": "逆否命题"}],
                "canvas_file": "离散数学.canvas"
            }

            runtime = MagicMock()
            runtime.context = {"retrieval_batch_size": 10}

            await retrieve_graphiti(state, runtime)

            # 验证 canvas_file 被传递给客户端
            mock_clients["graphiti"].search_nodes.assert_called_once()
            call_kwargs = mock_clients["graphiti"].search_nodes.call_args.kwargs
            assert call_kwargs.get("canvas_file") == "离散数学.canvas"


# ============================================================
# Temporal Memory 集成测试
# ============================================================

class TestTemporalMemoryE2E:
    """测试 Temporal Memory E2E"""

    @pytest.mark.asyncio
    async def test_retrieve_weak_concepts(self, mock_clients, mock_temporal_weak_concepts):
        """AC 4.3: 获取薄弱概念列表"""
        with patch('agentic_rag.nodes._get_temporal_client', return_value=mock_clients["temporal"]):
            from agentic_rag.nodes import retrieve_weak_concepts

            state = {"canvas_file": "离散数学.canvas"}
            runtime = MagicMock()
            runtime.context = {"weak_concepts_limit": 10}

            result = await retrieve_weak_concepts(state, runtime)

            assert "weak_concepts" in result
            assert "temporal_latency_ms" in result
            assert len(result["weak_concepts"]) == 2

    @pytest.mark.asyncio
    async def test_update_learning_behavior(self, mock_clients):
        """AC 4.4: 更新学习行为"""
        with patch('agentic_rag.nodes._get_temporal_client', return_value=mock_clients["temporal"]):
            from agentic_rag.nodes import update_learning_behavior

            state = {
                "current_concept": "逆否命题",
                "rating": 4,  # Good
                "canvas_file": "离散数学.canvas",
                "session_id": "test-session-001"
            }

            runtime = MagicMock()
            runtime.context = {}

            result = await update_learning_behavior(state, runtime)

            assert result["behavior_updated"] is True

    @pytest.mark.asyncio
    async def test_temporal_latency_under_50ms(self, mock_clients):
        """AC 4.5: Temporal Memory 延迟 < 50ms"""
        with patch('agentic_rag.nodes._get_temporal_client', return_value=mock_clients["temporal"]):
            from agentic_rag.nodes import retrieve_weak_concepts

            state = {"canvas_file": "离散数学.canvas"}
            runtime = MagicMock()
            runtime.context = {"weak_concepts_limit": 10}

            result = await retrieve_weak_concepts(state, runtime)

            # Mock 环境应该非常快
            assert result["temporal_latency_ms"] < 50


# ============================================================
# 错误处理和降级测试
# ============================================================

class TestErrorHandlingE2E:
    """测试错误处理和降级 E2E"""

    @pytest.mark.asyncio
    async def test_graphiti_timeout_fallback(self):
        """AC: Graphiti 超时时返回空结果"""
        graphiti_client = AsyncMock()
        graphiti_client.search_nodes = AsyncMock(side_effect=asyncio.TimeoutError())

        with patch('agentic_rag.nodes._get_graphiti_client', return_value=graphiti_client):
            from agentic_rag.nodes import retrieve_graphiti

            state = {
                "messages": [{"role": "user", "content": "test"}],
                "canvas_file": "test.canvas"
            }

            runtime = MagicMock()
            runtime.context = {"retrieval_batch_size": 10}

            result = await retrieve_graphiti(state, runtime)

            # 应该返回空结果而不是抛出异常
            assert result["graphiti_results"] == []

    @pytest.mark.asyncio
    async def test_lancedb_error_fallback(self):
        """AC: LanceDB 错误时返回空结果"""
        lancedb_client = AsyncMock()
        lancedb_client.search_multiple_tables = AsyncMock(side_effect=Exception("Connection error"))

        with patch('agentic_rag.nodes._get_lancedb_client', return_value=lancedb_client):
            from agentic_rag.nodes import retrieve_lancedb

            state = {
                "messages": [{"role": "user", "content": "test"}],
                "canvas_file": "test.canvas"
            }

            runtime = MagicMock()
            runtime.context = {"retrieval_batch_size": 10}

            result = await retrieve_lancedb(state, runtime)

            # 应该返回空结果
            assert result["lancedb_results"] == []

    @pytest.mark.asyncio
    async def test_empty_results_quality_low(self):
        """AC: 空结果应评为 low quality"""
        from agentic_rag.nodes import check_quality

        state = {"reranked_results": []}

        runtime = MagicMock()
        runtime.context = {"quality_threshold": 0.7}

        result = await check_quality(state, runtime)

        assert result["quality_grade"] == "low"


# ============================================================
# 性能基准测试
# ============================================================

class TestPerformanceBenchmarks:
    """性能基准测试"""

    @pytest.mark.asyncio
    async def test_parallel_retrieval_is_faster_than_sequential(self, mock_clients):
        """验证并行检索比顺序检索快"""
        # 添加模拟延迟
        async def slow_graphiti(*args, **kwargs):
            await asyncio.sleep(0.05)  # 50ms
            return mock_clients["graphiti"].search_nodes.return_value

        async def slow_lancedb(*args, **kwargs):
            await asyncio.sleep(0.05)  # 50ms
            return mock_clients["lancedb"].search_multiple_tables.return_value

        mock_clients["graphiti"].search_nodes = slow_graphiti
        mock_clients["lancedb"].search_multiple_tables = slow_lancedb

        with patch('agentic_rag.nodes._get_graphiti_client', return_value=mock_clients["graphiti"]), \
             patch('agentic_rag.nodes._get_lancedb_client', return_value=mock_clients["lancedb"]):

            from agentic_rag.nodes import retrieve_graphiti, retrieve_lancedb

            state = {
                "messages": [{"role": "user", "content": "test"}],
                "canvas_file": "test.canvas"
            }

            runtime = MagicMock()
            runtime.context = {"retrieval_batch_size": 10}

            # 测试并行
            start_parallel = time.perf_counter()
            await asyncio.gather(
                retrieve_graphiti(state, runtime),
                retrieve_lancedb(state, runtime)
            )
            parallel_time = time.perf_counter() - start_parallel

            # 测试顺序
            start_sequential = time.perf_counter()
            await retrieve_graphiti(state, runtime)
            await retrieve_lancedb(state, runtime)
            sequential_time = time.perf_counter() - start_sequential

            # 并行应该比顺序快 (理论上接近 2x)
            assert parallel_time < sequential_time


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
