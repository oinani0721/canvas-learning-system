"""
Story 23.4: Multi-Source Fusion Tests

Tests for:
- AC 1: 教材上下文注入 (TextbookContextService)
- AC 2: 学习历史检索 + 时间衰减
- AC 3: 跨Canvas关联检索 (CrossCanvasService)
- AC 4: 数据源权重配置
- AC 5: 融合结果source标注

Author: Canvas Learning System Team
Version: 1.0.0
Created: 2025-12-12
"""

import math
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Import modules under test
from agentic_rag.config import (
    DEFAULT_SOURCE_WEIGHTS,
    CanvasRAGConfig,
    merge_config,
)
from agentic_rag.nodes import (
    _apply_time_decay,
    _fuse_cascade_multi_source,
    _fuse_rrf_multi_source,
    _fuse_weighted_multi_source,
    fuse_results,
)
from agentic_rag.retrievers import (
    CrossCanvasService,
    TextbookContextService,
    textbook_retrieval_node,
)
from agentic_rag.state import SearchResult

# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def sample_search_results() -> Dict[str, List[SearchResult]]:
    """Sample search results from 5 sources"""
    return {
        "graphiti": [
            {"doc_id": "g1", "content": "Graphiti result 1", "score": 0.9, "metadata": {"source": "graphiti"}},
            {"doc_id": "g2", "content": "Graphiti result 2", "score": 0.8, "metadata": {"source": "graphiti"}},
        ],
        "lancedb": [
            {"doc_id": "l1", "content": "LanceDB result 1", "score": 0.85, "metadata": {"source": "lancedb"}},
            {"doc_id": "l2", "content": "LanceDB result 2", "score": 0.75, "metadata": {"source": "lancedb"}},
        ],
        "textbook": [
            {"doc_id": "t1", "content": "Textbook result 1", "score": 0.88, "metadata": {"source": "textbook"}},
        ],
        "cross_canvas": [
            {"doc_id": "c1", "content": "Cross-canvas result 1", "score": 0.7, "metadata": {"source": "cross_canvas"}},
        ],
        "multimodal": [
            {"doc_id": "m1", "content": "Multimodal result 1", "score": 0.6, "metadata": {"source": "multimodal"}},
        ],
    }


@pytest.fixture
def mock_lancedb_client():
    """Mock LanceDB client for testing"""
    client = AsyncMock()
    client.search = AsyncMock(return_value=[
        {"doc_id": "test1", "content": "Test content", "score": 0.9, "metadata": {}}
    ])
    client.initialize = AsyncMock(return_value=True)
    return client


# ============================================================
# AC 1: Textbook Context Injection Tests
# ============================================================

class TestTextbookContextService:
    """AC 1: 教材上下文注入测试"""

    @pytest.mark.asyncio
    async def test_textbook_service_initialization(self, mock_lancedb_client):
        """Test TextbookContextService initialization"""
        service = TextbookContextService(mock_lancedb_client)
        result = await service.initialize()
        assert result is True
        assert service._initialized is True

    @pytest.mark.asyncio
    async def test_textbook_search_adds_source_annotation(self, mock_lancedb_client):
        """AC 1: 检索结果包含source='textbook'标注"""
        mock_lancedb_client.search.return_value = [
            {"doc_id": "tb1", "content": "教材内容", "score": 0.9, "metadata": {}}
        ]

        service = TextbookContextService(mock_lancedb_client)
        await service.initialize()

        results = await service.search(
            query="什么是逆否命题",
            canvas_file="离散数学.canvas",
            num_results=5
        )

        assert len(results) == 1
        assert results[0]["metadata"]["source"] == "textbook"

    @pytest.mark.asyncio
    async def test_textbook_retrieval_node_returns_correct_state(self, mock_lancedb_client):
        """AC 1: textbook_retrieval_node返回正确的state更新"""
        state = {
            "messages": [{"role": "user", "content": "什么是逆否命题"}],
            "canvas_file": "离散数学.canvas"
        }

        with patch("agentic_rag.retrievers.textbook_retriever._get_textbook_service") as mock_get_service:
            mock_service = AsyncMock()
            mock_service.search.return_value = [
                {"doc_id": "tb1", "content": "教材内容", "score": 0.9, "metadata": {"source": "textbook"}}
            ]
            mock_get_service.return_value = mock_service

            result = await textbook_retrieval_node(state)

            assert "textbook_results" in result
            assert "textbook_latency_ms" in result
            assert isinstance(result["textbook_latency_ms"], float)


# ============================================================
# AC 2: Time Decay Tests
# ============================================================

class TestTimeDecay:
    """AC 2: 学习历史时间衰减测试"""

    def test_time_decay_formula(self):
        """AC 2: 验证时间衰减公式 weight = base_score * exp(-decay * days_ago)"""
        # 创建测试数据：7天前的结果
        now = datetime.now(timezone.utc)
        seven_days_ago = (now - timedelta(days=7)).isoformat()

        results = [
            {
                "doc_id": "test1",
                "content": "Test content",
                "score": 1.0,
                "metadata": {"timestamp": seven_days_ago}
            }
        ]

        decay_factor = 0.05
        decayed = _apply_time_decay(results, decay_factor)

        # 验证衰减公式
        expected_decay = math.exp(-decay_factor * 7)
        assert abs(decayed[0]["score"] - expected_decay) < 0.01
        assert decayed[0]["metadata"]["time_decay_applied"] is True
        assert decayed[0]["metadata"]["days_ago"] == 7

    def test_time_decay_no_timestamp(self):
        """AC 2: 无时间戳时保持原分数"""
        results = [
            {"doc_id": "test1", "content": "Test", "score": 0.8, "metadata": {}}
        ]

        decayed = _apply_time_decay(results, 0.05)
        assert decayed[0]["score"] == 0.8

    def test_time_decay_recent_results_higher(self):
        """AC 2: 最近的结果分数更高"""
        now = datetime.now(timezone.utc)
        results = [
            {"doc_id": "old", "content": "Old", "score": 1.0,
             "metadata": {"timestamp": (now - timedelta(days=30)).isoformat()}},
            {"doc_id": "new", "content": "New", "score": 1.0,
             "metadata": {"timestamp": (now - timedelta(days=1)).isoformat()}},
        ]

        decayed = _apply_time_decay(results, 0.05)

        # 新结果分数应该更高
        new_result = next(r for r in decayed if r["doc_id"] == "new")
        old_result = next(r for r in decayed if r["doc_id"] == "old")
        assert new_result["score"] > old_result["score"]


# ============================================================
# AC 3: Cross-Canvas Association Tests
# ============================================================

class TestCrossCanvasService:
    """AC 3: 跨Canvas关联检索测试"""

    @pytest.mark.asyncio
    async def test_cross_canvas_service_initialization(self, mock_lancedb_client):
        """Test CrossCanvasService initialization"""
        service = CrossCanvasService(mock_lancedb_client)
        result = await service.initialize()
        assert result is True
        assert service._initialized is True

    @pytest.mark.asyncio
    async def test_cross_canvas_search_adds_source_annotation(self, mock_lancedb_client):
        """AC 3: 检索结果包含source='cross_canvas'标注"""
        mock_lancedb_client.search.return_value = [
            {"doc_id": "cc1", "content": "跨Canvas内容", "score": 0.8, "metadata": {}}
        ]

        service = CrossCanvasService(mock_lancedb_client)
        await service.initialize()

        results = await service.search(
            query="什么是命题逻辑",
            canvas_file="离散数学.canvas",
            num_results=5
        )

        assert len(results) == 1
        assert results[0]["metadata"]["source"] == "cross_canvas"

    @pytest.mark.asyncio
    async def test_find_related_canvases(self, mock_lancedb_client):
        """AC 3: 查找关联Canvas"""
        service = CrossCanvasService(mock_lancedb_client)
        await service.initialize()

        related = await service.find_related_canvases("离散数学.canvas")
        # 目前返回空列表 (待实现)
        assert isinstance(related, list)


# ============================================================
# AC 4: Source Weights Configuration Tests
# ============================================================

class TestSourceWeightsConfiguration:
    """AC 4: 数据源权重配置测试"""

    def test_default_source_weights(self):
        """AC 4: 验证默认权重配置"""
        assert DEFAULT_SOURCE_WEIGHTS["graphiti"] == 0.25
        assert DEFAULT_SOURCE_WEIGHTS["lancedb"] == 0.25
        assert DEFAULT_SOURCE_WEIGHTS["textbook"] == 0.20
        assert DEFAULT_SOURCE_WEIGHTS["cross_canvas"] == 0.15
        assert DEFAULT_SOURCE_WEIGHTS["multimodal"] == 0.15

        # 权重总和应为1.0
        total = sum(DEFAULT_SOURCE_WEIGHTS.values())
        assert abs(total - 1.0) < 0.01

    def test_merge_config_preserves_custom_weights(self):
        """AC 4: 自定义权重配置被保留"""
        custom_weights = {
            "graphiti": 0.4,
            "lancedb": 0.3,
            "textbook": 0.15,
            "cross_canvas": 0.1,
            "multimodal": 0.05
        }

        user_config = CanvasRAGConfig(source_weights=custom_weights)
        merged = merge_config(user_config)

        assert merged["source_weights"]["graphiti"] == 0.4
        assert merged["source_weights"]["lancedb"] == 0.3

    def test_weighted_fusion_uses_source_weights(self, sample_search_results):
        """AC 4: 加权融合使用source_weights"""
        custom_weights = {
            "graphiti": 0.5,
            "lancedb": 0.2,
            "textbook": 0.15,
            "cross_canvas": 0.1,
            "multimodal": 0.05
        }

        results = _fuse_weighted_multi_source(sample_search_results, custom_weights)

        # 应该返回结果
        assert len(results) > 0

        # 验证fusion_method标注
        for r in results:
            assert r["metadata"]["fusion_method"] == "weighted"


# ============================================================
# AC 5: Source Annotation Tests
# ============================================================

class TestSourceAnnotation:
    """AC 5: 融合结果source标注测试"""

    def test_rrf_fusion_preserves_source(self, sample_search_results):
        """AC 5: RRF融合保留source标注"""
        results = _fuse_rrf_multi_source(sample_search_results)

        for r in results:
            assert "source" in r["metadata"]
            assert r["metadata"]["source"] in [
                "graphiti", "lancedb", "textbook", "cross_canvas", "multimodal"
            ]

    def test_weighted_fusion_preserves_source(self, sample_search_results):
        """AC 5: Weighted融合保留source标注"""
        results = _fuse_weighted_multi_source(sample_search_results, DEFAULT_SOURCE_WEIGHTS)

        for r in results:
            assert "source" in r["metadata"]

    def test_cascade_fusion_includes_tier(self, sample_search_results):
        """AC 5: Cascade融合包含tier标注"""
        results = _fuse_cascade_multi_source(sample_search_results)

        for r in results:
            assert "fusion_tier" in r["metadata"]
            assert r["metadata"]["fusion_tier"] in [1, 2]


# ============================================================
# Integration Tests
# ============================================================

class MockContext:
    """Mock context that supports .get() method"""
    def __init__(self, data: Dict[str, Any]):
        self._data = data

    def get(self, key: str, default=None):
        return self._data.get(key, default)


class TestFuseResultsIntegration:
    """fuse_results节点集成测试"""

    @pytest.mark.asyncio
    async def test_fuse_results_with_5_sources(self, sample_search_results):
        """测试5源融合完整流程"""
        state = {
            "graphiti_results": sample_search_results["graphiti"],
            "lancedb_results": sample_search_results["lancedb"],
            "multimodal_results": sample_search_results["multimodal"],
            "textbook_results": sample_search_results["textbook"],
            "cross_canvas_results": sample_search_results["cross_canvas"],
            "is_review_canvas": False,
        }

        # Mock runtime with proper context
        runtime = MagicMock()
        runtime.context = MockContext({
            "fusion_strategy": "rrf",
            "source_weights": DEFAULT_SOURCE_WEIGHTS,
            "time_decay_factor": 0.05
        })

        result = await fuse_results(state, runtime)

        assert "fused_results" in result
        assert "fusion_latency_ms" in result
        assert len(result["fused_results"]) <= 10

    @pytest.mark.asyncio
    async def test_fuse_results_with_weighted_strategy(self, sample_search_results):
        """测试加权融合策略"""
        state = {
            "graphiti_results": sample_search_results["graphiti"],
            "lancedb_results": sample_search_results["lancedb"],
            "multimodal_results": sample_search_results["multimodal"],
            "textbook_results": sample_search_results["textbook"],
            "cross_canvas_results": sample_search_results["cross_canvas"],
            "is_review_canvas": False,
        }

        runtime = MagicMock()
        runtime.context = MockContext({
            "fusion_strategy": "weighted",
            "source_weights": DEFAULT_SOURCE_WEIGHTS,
            "time_decay_factor": 0.05
        })

        result = await fuse_results(state, runtime)

        # 验证所有结果都有weighted标注
        for r in result["fused_results"]:
            assert r["metadata"]["fusion_method"] == "weighted"


# ============================================================
# State Graph Integration Tests
# ============================================================

class TestStateGraphIntegration:
    """StateGraph集成测试"""

    def test_fan_out_retrieval_returns_5_sends(self):
        """测试fan_out_retrieval返回5个Send"""
        from agentic_rag.state_graph import fan_out_retrieval

        state = {"messages": [{"role": "user", "content": "test"}]}
        sends = fan_out_retrieval(state)

        assert len(sends) == 5

        # 验证5个目标节点
        node_names = [s.node for s in sends]
        assert "retrieve_graphiti" in node_names
        assert "retrieve_lancedb" in node_names
        assert "retrieve_multimodal" in node_names
        assert "retrieve_textbook" in node_names
        assert "retrieve_cross_canvas" in node_names


# ============================================================
# Performance Tests
# ============================================================

class TestPerformance:
    """性能测试"""

    @pytest.mark.asyncio
    async def test_fusion_latency_under_100ms(self, sample_search_results):
        """融合延迟应 < 100ms"""
        import time

        state = {
            "graphiti_results": sample_search_results["graphiti"] * 10,  # 扩大数据量
            "lancedb_results": sample_search_results["lancedb"] * 10,
            "multimodal_results": sample_search_results["multimodal"] * 10,
            "textbook_results": sample_search_results["textbook"] * 10,
            "cross_canvas_results": sample_search_results["cross_canvas"] * 10,
            "is_review_canvas": False,
        }

        runtime = MagicMock()
        runtime.context = MockContext({
            "fusion_strategy": "rrf",
            "source_weights": DEFAULT_SOURCE_WEIGHTS,
            "time_decay_factor": 0.05
        })

        start = time.perf_counter()
        result = await fuse_results(state, runtime)
        latency = (time.perf_counter() - start) * 1000

        assert latency < 100, f"Fusion latency {latency}ms exceeds 100ms"
        assert result["fusion_latency_ms"] < 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
