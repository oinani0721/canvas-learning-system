"""
MCP记忆客户端测试
Canvas Learning System - Story 8.8

测试语义记忆存储、搜索、压缩等核心功能。
"""

import os
import tempfile
from unittest.mock import Mock, patch

import pytest

# 导入测试目标
from mcp_memory_client import (
    AccessMetadata,
    CompressionMetadata,
    ConceptInfo,
    HardwareDetector,
    MCPSemanticMemory,
    SemanticRelationship,
)


class TestHardwareDetector:
    """硬件检测器测试"""

    def test_detect_gpu_available(self):
        """测试GPU可用情况"""
        with patch('mcp_memory_client.torch') as mock_torch:
            mock_torch.cuda.is_available.return_value = True
            mock_torch.cuda.device_count.return_value = 2
            mock_torch.cuda.get_device_properties.return_value = Mock(total_memory=8*1024*1024*1024)

            detector = HardwareDetector()
            result = detector.detect_gpu()

            assert result["has_gpu"] is True
            assert result["gpu_count"] == 2
            assert result["gpu_memory_mb"] == 8192
            assert result["cuda_available"] is True
            assert result["recommended_device"] == "cuda"

    def test_detect_gpu_unavailable(self):
        """测试GPU不可用情况"""
        with patch('mcp_memory_client.torch', None):
            detector = HardwareDetector()
            result = detector.detect_gpu()

            assert result["has_gpu"] is False
            assert result["gpu_count"] == 0
            assert result["gpu_memory_mb"] == 0
            assert result["cuda_available"] is False
            assert result["recommended_device"] == "cpu"

    def test_get_system_memory(self):
        """测试系统内存检测"""
        with patch('mcp_memory_client.psutil') as mock_psutil:
            mock_psutil.virtual_memory.return_value = Mock(total=16*1024*1024*1024)

            detector = HardwareDetector()
            result = detector.get_system_memory()

            assert result == 16384  # 16GB in MB


@pytest.fixture
def temp_config_file():
    """临时配置文件fixture"""
    config_content = """
mcp_service:
  vector_database:
    type: "chromadb"
    persist_directory: "./test_memory_db"
    collection_name: "test_memories"
  embedding_model:
    model_name: "sentence-transformers/all-MiniLM-L6-v2"
    device: "cpu"
  hardware_detection:
    auto_detect_gpu: true
    fallback_to_cpu: true
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(config_content)
        temp_path = f.name

    yield temp_path

    # 清理
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def mock_memory_client():
    """模拟记忆客户端fixture"""
    with patch('mcp_memory_client.CHROMADB_AVAILABLE', True), \
         patch('mcp_memory_client.SENTENCE_TRANSFORMERS_AVAILABLE', True), \
         patch('mcp_memory_client.NUMPY_AVAILABLE', True):

        # Mock dependencies
        with patch('mcp_memory_client.chromadb'), \
             patch('mcp_memory_client.sentence_transformers'), \
             patch('mcp_memory_client.torch'):

            client = MCPSemanticMemory(config_path="dummy_config.yaml")
            return client


class TestMCPSemanticMemory:
    """MCP语义记忆客户端测试"""

    def test_load_config_file_exists(self, temp_config_file):
        """测试加载存在的配置文件"""
        with patch('mcp_memory_client.CHROMADB_AVAILABLE', True), \
             patch('mcp_memory_client.SENTENCE_TRANSFORMERS_AVAILABLE', True), \
             patch('mcp_memory_client.NUMPY_AVAILABLE', True):

            with patch('mcp_memory_client.chromadb'), \
                 patch('mcp_memory_client.sentence_transformers'), \
                 patch('mcp_memory_client.torch'):

                client = MCPSemanticMemory(config_path=temp_config_file)
                assert client.config["mcp_service"]["vector_database"]["type"] == "chromadb"

    def test_load_config_file_not_exists(self):
        """测试加载不存在的配置文件"""
        with patch('mcp_memory_client.CHROMADB_AVAILABLE', True), \
             patch('mcp_memory_client.SENTENCE_TRANSFORMERS_AVAILABLE', True), \
             patch('mcp_memory_client.NUMPY_AVAILABLE', True):

            with patch('mcp_memory_client.chromadb'), \
                 patch('mcp_memory_client.sentence_transformers'), \
                 patch('mcp_memory_client.torch'):

                client = MCPSemanticMemory(config_path="nonexistent_config.yaml")
                assert "mcp_service" in client.config

    def test_determine_device_auto_cpu(self, mock_memory_client):
        """测试设备自动选择（CPU）"""
        mock_memory_client.hardware_info = {
            "has_gpu": False,
            "cuda_available": False
        }

        device = mock_memory_client._determine_device()
        assert device == "cpu"

    def test_determine_device_auto_gpu(self, mock_memory_client):
        """测试设备自动选择（GPU）"""
        mock_memory_client.hardware_info = {
            "has_gpu": True,
            "cuda_available": True,
            "gpu_memory_mb": 8192
        }

        device = mock_memory_client._determine_device()
        assert device == "cuda"

    def test_store_semantic_memory(self, mock_memory_client):
        """测试存储语义记忆"""
        # Mock embedding model
        mock_memory_client.embedding_model.encode.return_value = [0.1, 0.2, 0.3]

        # Mock collection
        mock_memory_client.collection = Mock()
        mock_memory_client.collection.add.return_value = None

        content = "测试内容"
        metadata = {"source": "test"}

        memory_id = mock_memory_client.store_semantic_memory(content, metadata)

        assert memory_id.startswith("memory-")
        assert len(memory_id) == 23  # "memory-" + 16 chars

        # 验证collection.add被调用
        mock_memory_client.collection.add.assert_called_once()

    def test_search_semantic_memory(self, mock_memory_client):
        """测试语义搜索"""
        # Mock embedding model
        mock_memory_client.embedding_model.encode.return_value = [0.1, 0.2, 0.3]

        # Mock collection query result
        mock_result = {
            "ids": [["memory-abc123", "memory-def456"]],
            "documents": [["内容1", "内容2"]],
            "metadatas": [[{"source": "test1"}, {"source": "test2"}]],
            "distances": [[0.1, 0.2]]
        }
        mock_memory_client.collection = Mock()
        mock_memory_client.collection.query.return_value = mock_result

        results = mock_memory_client.search_semantic_memory("测试查询", limit=10)

        assert len(results) == 2
        assert results[0]["similarity_score"] == 0.9  # 1 - 0.1
        assert results[1]["similarity_score"] == 0.8  # 1 - 0.2

    def test_search_semantic_memory_empty_result(self, mock_memory_client):
        """测试搜索空结果"""
        mock_memory_client.embedding_model.encode.return_value = [0.1, 0.2, 0.3]
        mock_memory_client.collection = Mock()
        mock_memory_client.collection.query.return_value = {
            "ids": [[]],
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]]
        }

        results = mock_memory_client.search_semantic_memory("测试查询")

        assert len(results) == 0

    def test_auto_generate_tags(self, mock_memory_client):
        """测试自动生成标签"""
        content = "数学逻辑中的逆否命题是一个重要概念，它涉及命题的真假性变换"

        tags = mock_memory_client.auto_generate_tags(content, max_tags=5)

        assert isinstance(tags, list)
        assert len(tags) <= 5
        # 应该包含一些关键词
        for tag in tags:
            assert isinstance(tag, str)
            assert len(tag) > 0

    def test_find_related_concepts(self, mock_memory_client):
        """测试查找相关概念"""
        mock_results = [
            {
                "memory_id": "memory-abc123",
                "content": "逆否命题的内容...",
                "similarity_score": 0.8,
                "metadata": {"category": "logic"}
            },
            {
                "memory_id": "memory-def456",
                "content": "逻辑推理的内容...",
                "similarity_score": 0.6,  # 低于阈值
                "metadata": {"category": "logic"}
            }
        ]

        with patch.object(mock_memory_client, 'search_semantic_memory', return_value=mock_results):
            concepts = mock_memory_client.find_related_concepts("逆否命题", similarity_threshold=0.7)

        assert len(concepts) == 1
        assert concepts[0]["memory_id"] == "memory-abc123"
        assert concepts[0]["similarity_score"] == 0.8

    def test_get_memory_stats(self, mock_memory_client):
        """测试获取记忆统计"""
        mock_memory_client.collection = Mock()
        mock_memory_client.collection.count.return_value = 42
        mock_memory_client.embedding_model = Mock()
        mock_memory_client.embedding_model._modules = {
            '0': Mock(auto_model=Mock(name_or_path="test-model"))
        }

        stats = mock_memory_client.get_memory_stats()

        assert stats["total_memories"] == 42
        assert "device" in stats
        assert "model_name" in stats
        assert "hardware_info" in stats
        assert "last_updated" in stats

    def test_delete_memory(self, mock_memory_client):
        """测试删除记忆"""
        mock_memory_client.collection = Mock()
        mock_memory_client.collection.delete.return_value = None

        result = mock_memory_client.delete_memory("memory-abc123")

        assert result is True
        mock_memory_client.collection.delete.assert_called_once_with(ids=["memory-abc123"])


class TestDependencyValidation:
    """依赖验证测试"""

    def test_missing_chromadb(self):
        """测试缺少ChromaDB"""
        with patch('mcp_memory_client.CHROMADB_AVAILABLE', False):
            with pytest.raises(ImportError, match="需要安装ChromaDB"):
                MCPSemanticMemory(config_path="dummy_config.yaml")

    def test_missing_sentence_transformers(self):
        """测试缺少Sentence Transformers"""
        with patch('mcp_memory_client.CHROMADB_AVAILABLE', True), \
             patch('mcp_memory_client.SENTENCE_TRANSFORMERS_AVAILABLE', False):

            with pytest.raises(ImportError, match="需要安装Sentence Transformers"):
                MCPSemanticMemory(config_path="dummy_config.yaml")

    def test_missing_numpy(self):
        """测试缺少NumPy"""
        with patch('mcp_memory_client.CHROMADB_AVAILABLE', True), \
             patch('mcp_memory_client.SENTENCE_TRANSFORMERS_AVAILABLE', True), \
             patch('mcp_memory_client.NUMPY_AVAILABLE', False):

            with pytest.raises(ImportError, match="需要安装NumPy"):
                MCPSemanticMemory(config_path="dummy_config.yaml")


class TestDataClasses:
    """数据类测试"""

    def test_concept_info(self):
        """测试ConceptInfo数据类"""
        concept = ConceptInfo(
            concept="逆否命题",
            confidence=0.95,
            category="逻辑概念",
            related_fields=["数学", "计算机科学"]
        )

        assert concept.concept == "逆否命题"
        assert concept.confidence == 0.95
        assert concept.category == "逻辑概念"
        assert len(concept.related_fields) == 2

    def test_semantic_relationship(self):
        """测试SemanticRelationship数据类"""
        relationship = SemanticRelationship(
            related_memory_id="memory-abc123",
            relationship_type="is_similar_to",
            similarity_score=0.82,
            relationship_context="两个记忆都涉及命题逻辑"
        )

        assert relationship.related_memory_id == "memory-abc123"
        assert relationship.relationship_type == "is_similar_to"
        assert relationship.similarity_score == 0.82

    def test_compression_metadata(self):
        """测试CompressionMetadata数据类"""
        metadata = CompressionMetadata(
            original_size_bytes=2048,
            compressed_size_bytes=512,
            compression_ratio=0.25,
            compression_method="semantic_embedding",
            information_retention_score=0.91
        )

        assert metadata.original_size_bytes == 2048
        assert metadata.compression_ratio == 0.25
        assert metadata.information_retention_score == 0.91

    def test_access_metadata(self):
        """测试AccessMetadata数据类"""
        metadata = AccessMetadata(
            created_at="2025-01-22T10:45:00Z",
            last_accessed="2025-01-22T15:30:00Z",
            access_count=5,
            retrieval_context=["复习查询", "关联搜索"]
        )

        assert metadata.access_count == 5
        assert len(metadata.retrieval_context) == 2


@pytest.fixture
def mock_dependencies():
    """模拟所有依赖的fixture"""
    patches = [
        patch('mcp_memory_client.CHROMADB_AVAILABLE', True),
        patch('mcp_memory_client.SENTENCE_TRANSFORMERS_AVAILABLE', True),
        patch('mcp_memory_client.NUMPY_AVAILABLE', True),
        patch('mcp_memory_client.chromadb'),
        patch('mcp_memory_client.sentence_transformers'),
        patch('mcp_memory_client.torch'),
        patch('mcp_memory_client.uuid.uuid4', return_value=Mock(hex='abc123def4567890'))
    ]

    for p in patches:
        p.start()

    yield

    for p in patches:
        p.stop()


class TestIntegrationScenarios:
    """集成场景测试"""

    def test_memory_lifecycle(self, mock_dependencies):
        """测试记忆生命周期"""
        with patch('mcp_memory_client.yaml.safe_load', return_value={
            "mcp_service": {
                "vector_database": {
                    "type": "chromadb",
                    "persist_directory": "./test_db",
                    "collection_name": "test_collection"
                },
                "embedding_model": {
                    "model_name": "test-model",
                    "device": "cpu"
                }
            }
        }):
            # 创建客户端
            client = MCPSemanticMemory(config_path="dummy_config.yaml")

            # Mock collection
            mock_collection = Mock()
            client.collection = mock_collection

            # Mock embedding
            client.embedding_model = Mock()
            client.embedding_model.encode.return_value = [0.1, 0.2, 0.3]

            # 测试存储
            memory_id = client.store_semantic_memory("测试内容", {"source": "test"})
            assert memory_id == "memory-abc123def4567890"

            # 测试搜索
            mock_collection.query.return_value = {
                "ids": [[memory_id]],
                "documents": [["测试内容"]],
                "metadatas": [[{"source": "test"}]],
                "distances": [[0.1]]
            }

            results = client.search_semantic_memory("测试")
            assert len(results) == 1
            assert results[0]["memory_id"] == memory_id

            # 测试删除
            result = client.delete_memory(memory_id)
            assert result is True

            # 验证方法调用
            assert mock_collection.add.call_count == 1
            assert mock_collection.query.call_count == 1
            assert mock_collection.delete.call_count == 1

    def test_error_handling(self, mock_dependencies):
        """测试错误处理"""
        with patch('mcp_memory_client.yaml.safe_load', side_effect=Exception("Config error")):
            # 配置文件读取错误应该使用默认配置
            with patch('mcp_memory_client.open', side_effect=FileNotFoundError):
                client = MCPSemanticMemory(config_path="nonexistent.yaml")
                assert "mcp_service" in client.config


if __name__ == "__main__":
    # 简单测试运行
    pytest.main([__file__, "-v", "--tb=short"])
