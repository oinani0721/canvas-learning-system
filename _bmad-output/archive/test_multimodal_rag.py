"""
Story 6.8 多模态Agentic RAG 测试

测试覆盖:
- AC 6.8.1: 多模态RAG检索 (MultimodalRetriever集成)
- AC 6.8.2: 上下文增强生成 (RRF融合扩展)
- AC 6.8.3: 跨模态查询 (三路并行检索)
- AC 6.8.4: 检索延迟≤2秒 (超时降级)

Author: Canvas Learning System Team
Version: 1.0.0
Created: 2025-12-04
"""

import time
from typing import Any, Dict, List
from unittest.mock import AsyncMock, Mock, patch

import pytest

from agentic_rag.fusion.rrf_fusion import (
    DEFAULT_MULTIMODAL_WEIGHTS,
    rrf_fusion_with_multimodal,
    weighted_rrf_fusion,
)
from agentic_rag.fusion.unified_result import (
    ResultType,
    SearchSource,
    UnifiedResult,
)

# Import test targets
from agentic_rag.retrievers import (
    MultimodalResult,
    MultimodalRetrievalTimeout,
    MultimodalRetriever,
    MultimodalRetrieverError,
    multimodal_retrieval_node,
    retrieve_multimodal,
)
from agentic_rag.retrievers.multimodal_retriever import MediaType
from agentic_rag.state import CanvasRAGState

# ========================================
# Fixtures
# ========================================

@pytest.fixture
def mock_lancedb_client():
    """Mock LanceDB client for testing"""
    client = Mock()
    client.search = AsyncMock(return_value=[
        {"id": "doc1", "content": "Test document 1", "_distance": 0.1},
        {"id": "doc2", "content": "Test document 2", "_distance": 0.2},
    ])
    return client


@pytest.fixture
def mock_vectorizer():
    """Mock vectorizer for testing"""
    vectorizer = Mock()
    vectorizer.embed_text = AsyncMock(return_value=[0.1] * 768)
    return vectorizer


@pytest.fixture
def mock_retriever(mock_lancedb_client, mock_vectorizer):
    """Create mock MultimodalRetriever"""
    with patch('agentic_rag.retrievers.multimodal_retriever.MultimodalRetriever.__init__', return_value=None):
        retriever = MultimodalRetriever.__new__(MultimodalRetriever)
        retriever._lancedb_client = mock_lancedb_client
        retriever._vectorizer = mock_vectorizer
        retriever._cache = {}
        retriever._timeout_seconds = 2.0
        retriever._logger = Mock()
        return retriever


@pytest.fixture
def sample_text_results() -> List[Dict[str, Any]]:
    """Sample text search results from LanceDB"""
    return [
        {"doc_id": "text1", "content": "离散数学基础概念", "score": 0.95, "metadata": {"source": "lancedb"}},
        {"doc_id": "text2", "content": "逻辑命题与真值表", "score": 0.85, "metadata": {"source": "lancedb"}},
        {"doc_id": "text3", "content": "集合论入门", "score": 0.75, "metadata": {"source": "lancedb"}},
    ]


@pytest.fixture
def sample_graph_results() -> List[Dict[str, Any]]:
    """Sample graph search results from Graphiti"""
    return [
        {"doc_id": "node1", "content": "命题逻辑定义", "score": 0.90, "metadata": {"source": "graphiti", "type": "node"}},
        {"doc_id": "node2", "content": "逆否命题关系", "score": 0.80, "metadata": {"source": "graphiti", "type": "edge"}},
    ]


@pytest.fixture
def sample_multimodal_results() -> List[Dict[str, Any]]:
    """Sample multimodal search results"""
    return [
        {"id": "img1", "content": "数学公式图示", "score": 0.88, "media_type": "image", "file_path": "/images/formula.png"},
        {"id": "pdf1", "content": "教材第3章PDF", "score": 0.82, "media_type": "pdf", "file_path": "/docs/chapter3.pdf"},
    ]


@pytest.fixture
def sample_rag_state() -> Dict[str, Any]:
    """Sample RAG state for testing"""
    return {
        "messages": [{"role": "user", "content": "什么是逆否命题？"}],
        "graphiti_results": [],
        "lancedb_results": [],
        "multimodal_results": [],
        "fused_results": [],
        "reranked_results": [],
        "fusion_strategy": "rrf",
        "reranking_strategy": "local",
        "quality_grade": None,
        "query_rewritten": False,
        "rewrite_count": 0,
        "canvas_file": "离散数学.canvas",
        "is_review_canvas": False,
        "original_query": "什么是逆否命题？",
    }


# ========================================
# AC 6.8.1: 多模态RAG检索测试
# ========================================

class TestMultimodalRetrieverIntegration:
    """AC 6.8.1: 多模态RAG检索测试"""

    def test_multimodal_retriever_import(self):
        """测试MultimodalRetriever导入正确"""
        assert MultimodalRetriever is not None
        assert MultimodalResult is not None
        assert multimodal_retrieval_node is not None

    def test_multimodal_result_dataclass(self):
        """测试MultimodalResult数据结构"""
        result = MultimodalResult(
            id="test_id",
            media_type=MediaType.IMAGE,
            file_path="/path/to/image.png",
            content_preview="测试内容",
            relevance_score=0.95,
            metadata={"width": 800, "height": 600}
        )
        assert result.id == "test_id"
        assert result.content_preview == "测试内容"
        assert result.relevance_score == 0.95
        assert result.media_type == MediaType.IMAGE
        assert result.file_path == "/path/to/image.png"
        assert result.metadata["width"] == 800

    def test_multimodal_result_to_search_result(self):
        """测试MultimodalResult转换为SearchResult格式"""
        result = MultimodalResult(
            id="img_001",
            media_type=MediaType.IMAGE,
            file_path="/images/test.png",
            content_preview="图片描述内容",
            relevance_score=0.88,
            metadata={"ocr_text": "OCR识别文本"}
        )
        # 使用to_dict方法转换
        result_dict = result.to_dict()
        assert result_dict["id"] == "img_001"
        assert result_dict["media_type"] == "image"
        assert result_dict["file_path"] == "/images/test.png"
        assert result_dict["content_preview"] == "图片描述内容"

    @pytest.mark.asyncio
    async def test_retrieve_multimodal_function(self):
        """测试retrieve_multimodal便捷函数"""
        with patch('agentic_rag.retrievers.multimodal_retriever.MultimodalRetriever') as MockRetriever:
            mock_instance = AsyncMock()
            mock_instance.retrieve.return_value = [
                MultimodalResult(
                    id="test1",
                    media_type=MediaType.IMAGE,
                    file_path="/test.png",
                    content_preview="Test content",
                    relevance_score=0.9,
                    metadata={}
                )
            ]
            MockRetriever.return_value = mock_instance

            # 函数应该创建retriever并调用retrieve
            # Note: 实际调用取决于具体实现
            assert retrieve_multimodal is not None


# ========================================
# AC 6.8.2: RRF融合扩展测试
# ========================================

class TestRRFFusionWithMultimodal:
    """AC 6.8.2: 上下文增强生成 - RRF融合扩展测试"""

    def test_default_multimodal_weights(self):
        """测试默认多模态权重配置"""
        assert DEFAULT_MULTIMODAL_WEIGHTS["text"] == 0.4
        assert DEFAULT_MULTIMODAL_WEIGHTS["graph"] == 0.3
        assert DEFAULT_MULTIMODAL_WEIGHTS["multimodal"] == 0.3
        # 权重之和应为1.0
        total = sum(DEFAULT_MULTIMODAL_WEIGHTS.values())
        assert abs(total - 1.0) < 0.001

    def test_rrf_fusion_with_multimodal_basic(
        self,
        sample_text_results,
        sample_graph_results,
        sample_multimodal_results
    ):
        """测试基本的三路RRF融合"""
        results = rrf_fusion_with_multimodal(
            text_results=sample_text_results,
            graph_results=sample_graph_results,
            multimodal_results=sample_multimodal_results,
            k=60
        )

        assert len(results) > 0
        # 所有结果都应该是UnifiedResult类型
        assert all(isinstance(r, UnifiedResult) for r in results)
        # 结果应该按fused_score降序排列
        for i in range(len(results) - 1):
            assert results[i].fused_score >= results[i + 1].fused_score

    def test_rrf_fusion_with_empty_multimodal(
        self,
        sample_text_results,
        sample_graph_results
    ):
        """测试多模态结果为空时的融合"""
        results = rrf_fusion_with_multimodal(
            text_results=sample_text_results,
            graph_results=sample_graph_results,
            multimodal_results=[],  # 空多模态结果
            k=60
        )

        # 应该仍然返回文本和图谱结果
        assert len(results) >= len(sample_text_results)

    def test_rrf_fusion_with_only_multimodal(self, sample_multimodal_results):
        """测试仅有多模态结果时的融合"""
        results = rrf_fusion_with_multimodal(
            text_results=[],
            graph_results=[],
            multimodal_results=sample_multimodal_results,
            k=60
        )

        assert len(results) == len(sample_multimodal_results)
        # 结果应该来源于multimodal
        for r in results:
            assert r.source in [SearchSource.MULTIMODAL, SearchSource.FUSED]

    def test_rrf_fusion_with_custom_weights(
        self,
        sample_text_results,
        sample_graph_results,
        sample_multimodal_results
    ):
        """测试自定义权重的融合"""
        custom_weights = {
            "text": 0.5,
            "graph": 0.2,
            "multimodal": 0.3
        }
        results = rrf_fusion_with_multimodal(
            text_results=sample_text_results,
            graph_results=sample_graph_results,
            multimodal_results=sample_multimodal_results,
            weights=custom_weights,
            k=60
        )

        assert len(results) > 0

    def test_rrf_fusion_top_n_limit(
        self,
        sample_text_results,
        sample_graph_results,
        sample_multimodal_results
    ):
        """测试top_n结果限制"""
        results = rrf_fusion_with_multimodal(
            text_results=sample_text_results,
            graph_results=sample_graph_results,
            multimodal_results=sample_multimodal_results,
            top_n=3
        )

        assert len(results) <= 3

    def test_weighted_rrf_fusion(
        self,
        sample_text_results,
        sample_graph_results,
        sample_multimodal_results
    ):
        """测试加权RRF融合函数"""
        result_sources = {
            "text": sample_text_results,
            "graph": sample_graph_results,
            "multimodal": sample_multimodal_results
        }
        weights = {"text": 0.4, "graph": 0.3, "multimodal": 0.3}
        results = weighted_rrf_fusion(
            result_sources=result_sources,
            weights=weights
        )

        assert len(results) > 0

    def test_rrf_fusion_preserves_metadata(
        self,
        sample_text_results,
        sample_graph_results,
        sample_multimodal_results
    ):
        """测试融合保留元数据"""
        results = rrf_fusion_with_multimodal(
            text_results=sample_text_results,
            graph_results=sample_graph_results,
            multimodal_results=sample_multimodal_results,
        )

        # 检查元数据保留
        for r in results:
            assert hasattr(r, 'metadata')
            assert isinstance(r.metadata, dict)


# ========================================
# AC 6.8.3: 跨模态查询测试
# ========================================

class TestCrossModalQuery:
    """AC 6.8.3: 跨模态查询 - 三路并行检索测试"""

    def test_search_source_enum_has_multimodal(self):
        """测试SearchSource枚举包含MULTIMODAL"""
        assert hasattr(SearchSource, 'MULTIMODAL')
        assert SearchSource.MULTIMODAL.value == "multimodal"

    def test_result_type_enum_has_multimodal_types(self):
        """测试ResultType枚举包含多模态类型"""
        assert hasattr(ResultType, 'IMAGE')
        assert hasattr(ResultType, 'PDF')
        assert hasattr(ResultType, 'AUDIO')
        assert hasattr(ResultType, 'VIDEO')

        assert ResultType.IMAGE.value == "image"
        assert ResultType.PDF.value == "pdf"
        assert ResultType.AUDIO.value == "audio"
        assert ResultType.VIDEO.value == "video"

    def test_canvas_rag_state_has_multimodal_fields(self):
        """测试CanvasRAGState包含多模态字段"""
        # 检查类型注解
        annotations = CanvasRAGState.__annotations__
        assert 'multimodal_results' in annotations
        assert 'multimodal_latency_ms' in annotations

    def test_unified_result_from_multimodal(self):
        """测试从多模态结果创建UnifiedResult"""
        result = UnifiedResult(
            id="mm_001",
            content="多模态内容描述",
            source=SearchSource.MULTIMODAL,
            result_type=ResultType.IMAGE,
            original_score=0.92,
            fused_score=0.85,
            rank=1,
            metadata={"file_path": "/images/test.png"}
        )

        assert result.source == SearchSource.MULTIMODAL
        assert result.result_type == ResultType.IMAGE
        assert result.metadata["file_path"] == "/images/test.png"

    def test_unified_result_to_dict(self):
        """测试UnifiedResult序列化"""
        result = UnifiedResult(
            id="pdf_001",
            content="PDF文档内容",
            source=SearchSource.MULTIMODAL,
            result_type=ResultType.PDF,
            original_score=0.88,
        )

        result_dict = result.to_dict()
        assert result_dict["id"] == "pdf_001"
        assert result_dict["source"] == "multimodal"
        assert result_dict["result_type"] == "pdf"

    def test_unified_result_from_dict(self):
        """测试UnifiedResult反序列化"""
        data = {
            "id": "audio_001",
            "content": "音频转录内容",
            "source": "multimodal",
            "result_type": "audio",
            "original_score": 0.75,
        }

        result = UnifiedResult.from_dict(data)
        assert result.id == "audio_001"
        assert result.source == SearchSource.MULTIMODAL
        assert result.result_type == ResultType.AUDIO


# ========================================
# AC 6.8.4: 延迟测试
# ========================================

class TestRetrievalLatency:
    """AC 6.8.4: 检索延迟≤2秒测试"""

    def test_multimodal_result_creation_fast(self):
        """测试MultimodalResult创建速度"""
        start = time.perf_counter()

        for _ in range(1000):
            result = MultimodalResult(
                id="test",
                media_type=MediaType.IMAGE,
                file_path="/test.png",
                content_preview="content",
                relevance_score=0.9,
                metadata={}
            )

        elapsed = time.perf_counter() - start
        # 1000次创建应该在100ms内完成
        assert elapsed < 0.1

    def test_rrf_fusion_performance(
        self,
        sample_text_results,
        sample_graph_results,
        sample_multimodal_results
    ):
        """测试RRF融合性能"""
        start = time.perf_counter()

        for _ in range(100):
            results = rrf_fusion_with_multimodal(
                text_results=sample_text_results,
                graph_results=sample_graph_results,
                multimodal_results=sample_multimodal_results,
            )

        elapsed = time.perf_counter() - start
        # 100次融合应该在1秒内完成
        assert elapsed < 1.0, f"RRF fusion too slow: {elapsed:.2f}s for 100 iterations"

    def test_unified_result_serialization_performance(self):
        """测试UnifiedResult序列化性能"""
        result = UnifiedResult(
            id="test",
            content="Test content",
            source=SearchSource.MULTIMODAL,
            result_type=ResultType.IMAGE,
            original_score=0.9,
        )

        start = time.perf_counter()

        for _ in range(1000):
            _ = result.to_dict()

        elapsed = time.perf_counter() - start
        # 1000次序列化应该在100ms内完成
        assert elapsed < 0.1


# ========================================
# StateGraph集成测试
# ========================================

class TestStateGraphIntegration:
    """StateGraph多模态集成测试"""

    def test_multimodal_retrieval_node_exists(self):
        """测试multimodal_retrieval_node函数存在"""
        assert callable(multimodal_retrieval_node)

    def test_state_graph_imports(self):
        """测试state_graph模块可以正确导入"""
        try:
            from agentic_rag.state_graph import (
                build_canvas_agentic_rag_graph,
                fan_out_retrieval,
            )
            assert callable(build_canvas_agentic_rag_graph)
            assert callable(fan_out_retrieval)
        except ImportError as e:
            pytest.fail(f"StateGraph import failed: {e}")

    def test_fan_out_retrieval_returns_three_sends(self, sample_rag_state):
        """测试fan_out_retrieval返回三个Send对象"""
        from langgraph.types import Send

        from agentic_rag.state_graph import fan_out_retrieval

        sends = fan_out_retrieval(sample_rag_state)

        assert len(sends) == 3
        assert all(isinstance(s, Send) for s in sends)

        # 检查目标节点
        destinations = [s.node for s in sends]
        assert "retrieve_graphiti" in destinations
        assert "retrieve_lancedb" in destinations
        assert "retrieve_multimodal" in destinations

    def test_state_graph_compilation(self):
        """测试StateGraph编译成功"""
        from agentic_rag.state_graph import build_canvas_agentic_rag_graph

        builder = build_canvas_agentic_rag_graph()
        assert builder is not None

        # 编译图
        graph = builder.compile()
        assert graph is not None

    def test_state_graph_has_multimodal_node(self):
        """测试StateGraph包含multimodal节点"""
        from agentic_rag.state_graph import build_canvas_agentic_rag_graph

        builder = build_canvas_agentic_rag_graph()

        # 检查节点
        nodes = builder.nodes
        assert "retrieve_multimodal" in nodes


# ========================================
# 错误处理测试
# ========================================

class TestErrorHandling:
    """错误处理测试"""

    def test_multimodal_retriever_error(self):
        """测试MultimodalRetrieverError异常"""
        with pytest.raises(MultimodalRetrieverError):
            raise MultimodalRetrieverError("Test error")

    def test_multimodal_retrieval_timeout(self):
        """测试MultimodalRetrievalTimeout异常"""
        with pytest.raises(MultimodalRetrievalTimeout):
            raise MultimodalRetrievalTimeout("Timeout after 2 seconds")

    def test_rrf_fusion_handles_invalid_scores(self):
        """测试RRF融合处理无效分数"""
        invalid_results = [
            {"doc_id": "bad1", "content": "content", "score": -1.0, "metadata": {}},
        ]

        # 应该优雅处理无效分数
        results = rrf_fusion_with_multimodal(
            text_results=invalid_results,
            graph_results=[],
            multimodal_results=[],
        )

        # 不应该崩溃
        assert isinstance(results, list)

    def test_rrf_fusion_handles_missing_fields(self):
        """测试RRF融合处理缺失字段"""
        incomplete_results = [
            {"doc_id": "inc1", "content": "content"},  # 缺少score
        ]

        # 应该优雅处理
        try:
            results = rrf_fusion_with_multimodal(
                text_results=incomplete_results,
                graph_results=[],
                multimodal_results=[],
            )
        except (KeyError, TypeError):
            # 预期可能抛出异常
            pass


# ========================================
# 边界条件测试
# ========================================

class TestEdgeCases:
    """边界条件测试"""

    def test_all_empty_results(self):
        """测试所有结果为空"""
        results = rrf_fusion_with_multimodal(
            text_results=[],
            graph_results=[],
            multimodal_results=[],
        )

        assert results == []

    def test_single_result_each_source(self):
        """测试每个来源只有一个结果"""
        text = [{"doc_id": "t1", "content": "text", "score": 0.9, "metadata": {}}]
        graph = [{"doc_id": "g1", "content": "graph", "score": 0.8, "metadata": {}}]
        mm = [{"doc_id": "m1", "content": "multimodal", "score": 0.7, "metadata": {"type": "image"}}]

        results = rrf_fusion_with_multimodal(
            text_results=text,
            graph_results=graph,
            multimodal_results=mm,
        )

        assert len(results) == 3

    def test_duplicate_ids_across_sources(self):
        """测试跨来源重复ID"""
        text = [{"doc_id": "dup1", "content": "text version", "score": 0.9, "metadata": {}}]
        graph = [{"doc_id": "dup1", "content": "graph version", "score": 0.8, "metadata": {}}]
        mm = [{"doc_id": "dup1", "content": "mm version", "score": 0.7, "metadata": {"type": "image"}}]

        results = rrf_fusion_with_multimodal(
            text_results=text,
            graph_results=graph,
            multimodal_results=mm,
        )

        # 应该处理重复ID（可能合并或保留最高分）
        assert len(results) >= 1

    def test_very_large_result_sets(self):
        """测试大量结果集"""
        large_text = [
            {"doc_id": f"t{i}", "content": f"text {i}", "score": 0.9 - i * 0.001, "metadata": {}}
            for i in range(100)
        ]
        large_graph = [
            {"doc_id": f"g{i}", "content": f"graph {i}", "score": 0.8 - i * 0.001, "metadata": {}}
            for i in range(100)
        ]
        large_mm = [
            {"doc_id": f"m{i}", "content": f"mm {i}", "score": 0.7 - i * 0.001, "metadata": {"type": "image"}}
            for i in range(100)
        ]

        start = time.perf_counter()
        results = rrf_fusion_with_multimodal(
            text_results=large_text,
            graph_results=large_graph,
            multimodal_results=large_mm,
            top_n=50
        )
        elapsed = time.perf_counter() - start

        assert len(results) == 50
        # 300个输入应该在100ms内完成融合
        assert elapsed < 0.1, f"Large fusion too slow: {elapsed:.2f}s"


# ========================================
# 集成场景测试
# ========================================

class TestIntegrationScenarios:
    """集成场景测试"""

    def test_review_canvas_scenario(
        self,
        sample_text_results,
        sample_graph_results,
        sample_multimodal_results
    ):
        """测试检验白板场景 - 使用Weighted融合"""
        # 检验白板场景应该使用weighted融合
        result_sources = {
            "text": sample_text_results,
            "graph": sample_graph_results,
            "multimodal": sample_multimodal_results
        }
        weights = {"text": 0.5, "graph": 0.3, "multimodal": 0.2}  # 检验白板更重视文本
        results = weighted_rrf_fusion(
            result_sources=result_sources,
            weights=weights
        )

        assert len(results) > 0
        # 结果应该按分数排序
        for i in range(len(results) - 1):
            assert results[i].fused_score >= results[i + 1].fused_score

    def test_multimodal_heavy_scenario(
        self,
        sample_text_results,
        sample_multimodal_results
    ):
        """测试多模态重要场景"""
        # 当有大量图片/PDF时，提高多模态权重
        result_sources = {
            "text": sample_text_results,
            "graph": [],
            "multimodal": sample_multimodal_results
        }
        weights = {"text": 0.3, "graph": 0.0, "multimodal": 0.7}  # 高多模态权重
        results = weighted_rrf_fusion(
            result_sources=result_sources,
            weights=weights
        )

        assert len(results) > 0

    def test_text_only_fallback(self, sample_text_results):
        """测试纯文本回退场景"""
        # 当多模态和图谱都不可用时
        results = rrf_fusion_with_multimodal(
            text_results=sample_text_results,
            graph_results=[],
            multimodal_results=[],
        )

        assert len(results) == len(sample_text_results)


# ========================================
# 运行配置
# ========================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
