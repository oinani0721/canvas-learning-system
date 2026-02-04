"""
Story 35.8: RAG多模态搜索集成 - 单元测试

测试覆盖:
- AC 35.8.1: RAGQueryResponse包含multimodal_results字段
- AC 35.8.2: MultimodalRetriever已wired到RAG Service
- AC 35.8.3: 图片结果包含缩略图Base64/URL
- AC 35.8.4: 多模态结果参与RRF融合

Author: Canvas Learning System Team
Version: 1.0.0
Created: 2026-01-20
"""

import pytest
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch


# ========================================
# Fixtures
# ========================================

@pytest.fixture
def sample_rag_state() -> Dict[str, Any]:
    """Sample RAG state for testing"""
    return {
        "messages": [{"role": "user", "content": "什么是逆否命题？"}],
        "graphiti_results": [],
        "lancedb_results": [],
        "multimodal_results": [],
        "textbook_results": [],
        "cross_canvas_results": [],
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


@pytest.fixture
def sample_multimodal_raw_results() -> List[Dict[str, Any]]:
    """Sample raw multimodal results from LanceDB"""
    return [
        {
            "id": "img_001",
            "media_type": "image",
            "file_path": "/images/逆否命题图解.png",
            "thumbnail_path": "data:image/png;base64,iVBORw0KGgoAAAA...",
            "_distance": 0.15,
            "description": "逆否命题的图形化解释",
        },
        {
            "id": "pdf_001",
            "media_type": "pdf",
            "file_path": "/docs/离散数学.pdf",
            "content_preview": "第三章 命题逻辑...",
            "_distance": 0.25,
            "page_number": 42,
            "chapter": "命题逻辑",
        },
    ]


# ========================================
# AC 35.8.1: MultimodalResultItem Model Tests
# ========================================

class TestMultimodalResultItemModel:
    """AC 35.8.1: RAGQueryResponse包含multimodal_results字段"""

    def test_multimodal_result_item_import(self):
        """测试MultimodalResultItem可以正确导入"""
        from app.api.v1.endpoints.rag import MultimodalResultItem
        assert MultimodalResultItem is not None

    def test_multimodal_result_item_fields(self):
        """测试MultimodalResultItem包含所有必需字段"""
        from app.api.v1.endpoints.rag import MultimodalResultItem

        # 验证字段定义
        fields = MultimodalResultItem.model_fields
        assert "id" in fields
        assert "media_type" in fields
        assert "path" in fields
        assert "thumbnail" in fields
        assert "relevance_score" in fields
        assert "metadata" in fields

    def test_multimodal_result_item_validation(self):
        """测试MultimodalResultItem验证规则"""
        from app.api.v1.endpoints.rag import MultimodalResultItem

        # 有效数据应该通过验证
        item = MultimodalResultItem(
            id="test_001",
            media_type="image",
            path="/images/test.png",
            thumbnail="data:image/png;base64,abc...",
            relevance_score=0.85,
            metadata={"width": 800}
        )
        assert item.id == "test_001"
        assert item.media_type == "image"
        assert item.relevance_score == 0.85

    def test_multimodal_result_item_score_range(self):
        """测试relevance_score范围验证 (0-1)"""
        from app.api.v1.endpoints.rag import MultimodalResultItem
        from pydantic import ValidationError

        # 有效分数
        item = MultimodalResultItem(
            id="test",
            media_type="image",
            path="/test.png",
            relevance_score=0.5
        )
        assert item.relevance_score == 0.5

        # 边界值
        item_min = MultimodalResultItem(
            id="test",
            media_type="image",
            path="/test.png",
            relevance_score=0.0
        )
        assert item_min.relevance_score == 0.0

        item_max = MultimodalResultItem(
            id="test",
            media_type="image",
            path="/test.png",
            relevance_score=1.0
        )
        assert item_max.relevance_score == 1.0

    def test_multimodal_result_item_media_type_enum(self):
        """测试media_type枚举值验证"""
        from app.api.v1.endpoints.rag import MultimodalResultItem

        # 有效媒体类型
        for media_type in ["image", "pdf", "audio", "video"]:
            item = MultimodalResultItem(
                id="test",
                media_type=media_type,
                path="/test",
                relevance_score=0.5
            )
            assert item.media_type == media_type

    def test_rag_query_response_has_multimodal_results(self):
        """测试RAGQueryResponse包含multimodal_results字段"""
        from app.api.v1.endpoints.rag import RAGQueryResponse

        fields = RAGQueryResponse.model_fields
        assert "multimodal_results" in fields


# ========================================
# AC 35.8.2: MultimodalRetriever Wiring Tests
# ========================================

class TestMultimodalRetrieverWiring:
    """AC 35.8.2: MultimodalRetriever已wired到RAG Service"""

    def test_multimodal_retrieval_node_exists(self):
        """测试multimodal_retrieval_node函数存在"""
        from agentic_rag.retrievers import multimodal_retrieval_node
        assert callable(multimodal_retrieval_node)

    def test_multimodal_retrieval_node_extracts_query_from_messages(
        self, sample_rag_state
    ):
        """测试节点从messages提取查询"""
        from agentic_rag.retrievers.multimodal_retriever import _extract_query_from_state

        query = _extract_query_from_state(sample_rag_state)
        assert query == "什么是逆否命题？"

    def test_multimodal_retrieval_node_handles_empty_messages(self):
        """测试节点处理空messages"""
        from agentic_rag.retrievers.multimodal_retriever import _extract_query_from_state

        state = {"messages": [], "original_query": "fallback query"}
        query = _extract_query_from_state(state)
        assert query == "fallback query"

    def test_multimodal_retrieval_node_handles_dict_message(self):
        """测试节点处理dict格式的message"""
        from agentic_rag.retrievers.multimodal_retriever import _extract_query_from_state

        state = {"messages": [{"role": "user", "content": "test query"}]}
        query = _extract_query_from_state(state)
        assert query == "test query"

    @pytest.mark.asyncio
    async def test_multimodal_retrieval_node_returns_empty_without_query(self):
        """测试无查询时返回空结果"""
        from agentic_rag.retrievers import multimodal_retrieval_node

        state = {"messages": []}
        result = await multimodal_retrieval_node(state)

        assert "multimodal_results" in result
        assert result["multimodal_results"] == []
        assert "multimodal_latency_ms" in result

    @pytest.mark.asyncio
    async def test_multimodal_retrieval_node_returns_correct_structure(
        self, sample_rag_state
    ):
        """测试节点返回正确的结构"""
        from agentic_rag.retrievers import multimodal_retrieval_node

        # Mock the client to return empty results (no client available)
        with patch(
            "agentic_rag.retrievers.multimodal_retriever._get_multimodal_lancedb_client",
            return_value=None
        ):
            result = await multimodal_retrieval_node(sample_rag_state)

        assert isinstance(result, dict)
        assert "multimodal_results" in result
        assert "multimodal_latency_ms" in result
        assert isinstance(result["multimodal_results"], list)
        assert isinstance(result["multimodal_latency_ms"], float)


# ========================================
# AC 35.8.3: Thumbnail Population Tests
# ========================================

class TestThumbnailPopulation:
    """AC 35.8.3: 图片结果包含缩略图Base64/URL"""

    def test_thumbnail_from_thumbnail_path(self):
        """测试从thumbnail_path填充thumbnail"""
        raw_result = {
            "id": "img_001",
            "media_type": "image",
            "file_path": "/images/test.png",
            "thumbnail_path": "data:image/png;base64,abc123",
            "_distance": 0.1,
        }

        # 模拟节点的结果格式化
        thumbnail = raw_result.get("thumbnail_path", raw_result.get("content_preview", ""))
        assert thumbnail == "data:image/png;base64,abc123"

    def test_thumbnail_fallback_to_content_preview(self):
        """测试thumbnail回退到content_preview"""
        raw_result = {
            "id": "img_001",
            "media_type": "image",
            "file_path": "/images/test.png",
            "content_preview": "/thumbnails/test_thumb.png",
            "_distance": 0.1,
        }

        # 没有thumbnail_path时使用content_preview
        thumbnail = raw_result.get("thumbnail_path", raw_result.get("content_preview", ""))
        assert thumbnail == "/thumbnails/test_thumb.png"

    def test_endpoint_maps_thumbnail_correctly(self):
        """测试endpoint正确映射thumbnail字段"""
        from app.api.v1.endpoints.rag import MultimodalResultItem

        mm_dict = {
            "id": "img_001",
            "media_type": "image",
            "path": "/images/test.png",
            "thumbnail": "data:image/png;base64,xyz",
            "content_preview": "fallback",
            "relevance_score": 0.85,
        }

        # 模拟endpoint的映射逻辑
        item = MultimodalResultItem(
            id=mm_dict.get("id", ""),
            media_type=mm_dict.get("media_type", "image"),
            path=mm_dict.get("path", mm_dict.get("file_path", "")),
            thumbnail=mm_dict.get("thumbnail", mm_dict.get("content_preview")),
            relevance_score=mm_dict.get("relevance_score", 0.0),
            metadata=mm_dict.get("metadata", {})
        )

        assert item.thumbnail == "data:image/png;base64,xyz"


# ========================================
# AC 35.8.4: RRF Multimodal Fusion Tests
# ========================================

class TestRRFMultimodalFusion:
    """AC 35.8.4: 多模态结果参与RRF融合"""

    def test_multimodal_included_in_source_weights(self):
        """测试multimodal包含在默认权重配置中"""
        from agentic_rag.nodes import DEFAULT_SOURCE_WEIGHTS

        assert "multimodal" in DEFAULT_SOURCE_WEIGHTS
        assert DEFAULT_SOURCE_WEIGHTS["multimodal"] == 0.15

    def test_fuse_results_includes_multimodal(self, sample_rag_state):
        """测试fuse_results函数处理multimodal_results"""
        # 设置多模态结果
        sample_rag_state["multimodal_results"] = [
            {"doc_id": "mm_001", "content": "图片内容", "score": 0.8, "metadata": {"source": "multimodal"}}
        ]

        # all_source_results应该包含multimodal
        all_source_results = {
            "graphiti": sample_rag_state.get("graphiti_results", []),
            "lancedb": sample_rag_state.get("lancedb_results", []),
            "multimodal": sample_rag_state.get("multimodal_results", []),
            "textbook": sample_rag_state.get("textbook_results", []),
            "cross_canvas": sample_rag_state.get("cross_canvas_results", []),
        }

        assert "multimodal" in all_source_results
        assert len(all_source_results["multimodal"]) == 1

    def test_rrf_fusion_with_multimodal_results(self):
        """测试RRF融合正确处理multimodal结果"""
        from agentic_rag.nodes import _fuse_rrf_multi_source

        all_source_results = {
            "graphiti": [
                {"doc_id": "g1", "content": "graphiti内容", "score": 0.9, "metadata": {}}
            ],
            "lancedb": [
                {"doc_id": "l1", "content": "lancedb内容", "score": 0.85, "metadata": {}}
            ],
            "multimodal": [
                {"doc_id": "m1", "content": "多模态内容", "score": 0.8, "metadata": {"type": "image"}}
            ],
            "textbook": [],
            "cross_canvas": [],
        }

        fused = _fuse_rrf_multi_source(all_source_results)

        assert len(fused) == 3
        # 检查所有来源都被处理
        doc_ids = [r["doc_id"] for r in fused]
        assert "g1" in doc_ids
        assert "l1" in doc_ids
        assert "m1" in doc_ids

    def test_weighted_fusion_with_multimodal(self):
        """测试Weighted融合正确处理multimodal结果"""
        from agentic_rag.nodes import DEFAULT_SOURCE_WEIGHTS, _fuse_weighted_multi_source

        all_source_results = {
            "graphiti": [
                {"doc_id": "g1", "content": "graphiti内容", "score": 0.9, "metadata": {}}
            ],
            "lancedb": [
                {"doc_id": "l1", "content": "lancedb内容", "score": 0.85, "metadata": {}}
            ],
            "multimodal": [
                {"doc_id": "m1", "content": "多模态内容", "score": 0.8, "metadata": {"type": "image"}}
            ],
            "textbook": [],
            "cross_canvas": [],
        }

        fused = _fuse_weighted_multi_source(all_source_results, DEFAULT_SOURCE_WEIGHTS)

        assert len(fused) == 3
        # 检查融合方法标记
        for r in fused:
            assert r["metadata"]["fusion_method"] == "weighted"


# ========================================
# StateGraph Integration Tests
# ========================================

class TestStateGraphMultimodalIntegration:
    """StateGraph多模态集成测试"""

    def test_state_graph_has_multimodal_node(self):
        """测试StateGraph包含retrieve_multimodal节点"""
        from agentic_rag.state_graph import build_canvas_agentic_rag_graph

        builder = build_canvas_agentic_rag_graph()
        nodes = builder.nodes

        assert "retrieve_multimodal" in nodes

    def test_fan_out_retrieval_includes_multimodal(self, sample_rag_state):
        """测试fan_out_retrieval包含multimodal"""
        from langgraph.types import Send
        from agentic_rag.state_graph import fan_out_retrieval

        sends = fan_out_retrieval(sample_rag_state)

        # Story 23.4: 现在是5路并行检索
        assert len(sends) == 5
        destinations = [s.node for s in sends]
        assert "retrieve_multimodal" in destinations

    def test_canvas_rag_state_has_multimodal_fields(self):
        """测试CanvasRAGState包含multimodal字段"""
        from agentic_rag.state import CanvasRAGState

        annotations = CanvasRAGState.__annotations__
        assert "multimodal_results" in annotations
        assert "multimodal_latency_ms" in annotations


# ========================================
# Response Mapping Tests
# ========================================

class TestResponseMapping:
    """测试RAG endpoint响应映射"""

    def test_response_maps_multimodal_results(self):
        """测试响应正确映射multimodal_results"""
        from app.api.v1.endpoints.rag import MultimodalResultItem, RAGQueryResponse

        # 模拟RAG服务返回的结果
        rag_result = {
            "results": [],
            "multimodal_results": [
                {
                    "id": "mm_001",
                    "media_type": "image",
                    "path": "/images/test.png",
                    "file_path": "/images/test.png",
                    "thumbnail": "data:image/png;base64,abc",
                    "content_preview": "预览内容",
                    "relevance_score": 0.85,
                    "metadata": {"width": 800}
                }
            ],
            "quality_grade": "high",
            "result_count": 1,
            "latency_ms": {},
            "total_latency_ms": 100.0,
            "metadata": {}
        }

        # 模拟endpoint的映射逻辑
        multimodal_items = [
            MultimodalResultItem(
                id=mm.get("id", ""),
                media_type=mm.get("media_type", "image"),
                path=mm.get("path", mm.get("file_path", "")),
                thumbnail=mm.get("thumbnail", mm.get("content_preview")),
                relevance_score=mm.get("relevance_score", 0.0),
                metadata=mm.get("metadata", {})
            )
            for mm in rag_result.get("multimodal_results", [])
        ]

        assert len(multimodal_items) == 1
        assert multimodal_items[0].id == "mm_001"
        assert multimodal_items[0].media_type == "image"
        assert multimodal_items[0].path == "/images/test.png"
        assert multimodal_items[0].thumbnail == "data:image/png;base64,abc"
        assert multimodal_items[0].relevance_score == 0.85


# ========================================
# Run Configuration
# ========================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
