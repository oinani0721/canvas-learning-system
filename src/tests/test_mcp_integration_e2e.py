"""
MCP集成端到端测试
Canvas Learning System - Story 8.8

测试完整的MCP语义记忆服务工作流和集成场景。
"""

import pytest
import tempfile
import json
import os
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# 导入测试目标
from mcp_memory_client import MCPSemanticMemory
from semantic_processor import SemanticProcessor
from creative_association_engine import CreativeAssociationEngine
from memory_compression import MemoryCompressor
from canvas_mcp_integration import CanvasMCPIntegration
from mcp_commands import MCPCommandInterface


class TestMCPIntegrationE2E:
    """MCP集成端到端测试"""

    @pytest.fixture
    def temp_workspace(self):
        """临时工作空间fixture"""
        workspace_dir = tempfile.mkdtemp(prefix="mcp_test_")

        # 创建必要的目录结构
        os.makedirs(os.path.join(workspace_dir, "config"), exist_ok=True)
        os.makedirs(os.path.join(workspace_dir, "data"), exist_ok=True)
        os.makedirs(os.path.join(workspace_dir, "models"), exist_ok=True)

        yield workspace_dir

        # 清理
        shutil.rmtree(workspace_dir, ignore_errors=True)

    @pytest.fixture
    def temp_config_file(self, temp_workspace):
        """临时配置文件fixture"""
        config_content = """
mcp_service:
  vector_database:
    type: "chromadb"
    persist_directory: "{workspace}/data/memory_db"
    collection_name: "test_memories"
  embedding_model:
    model_name: "sentence-transformers/all-MiniLM-L6-v2"
    device: "cpu"
    hardware_detection:
    auto_detect_gpu: false
    fallback_to_cpu: true
  semantic_processing:
    extract_concepts: true
    generate_tags: true
    chunk_size: 512
  creative_association:
    enable: true
    creativity_levels:
      conservative:
        temperature: 0.7
        max_associations: 5
      moderate:
        temperature: 0.9
        max_associations: 8
  memory_management:
    max_memories_per_collection: 1000
    auto_compress_threshold: 100
    compression_ratio: 0.3
""".format(workspace=temp_workspace)

        config_path = os.path.join(temp_workspace, "config", "mcp_config.yaml")
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(config_content)

        return config_path

    @pytest.fixture
    def temp_canvas_file(self, temp_workspace):
        """临时Canvas文件fixture"""
        canvas_data = {
            "nodes": [
                {
                    "id": "node-question-1",
                    "type": "text",
                    "text": "什么是逆否命题？请解释其定义和基本性质。",
                    "x": 100,
                    "y": 100,
                    "width": 400,
                    "height": 200,
                    "color": "1"
                },
                {
                    "id": "node-explanation-1",
                    "type": "text",
                    "text": "逆否命题是逻辑学中的一个重要概念，表示原命题的否定形式。",
                    "x": 600,
                    "y": 100,
                    "width": 500,
                    "height": 300,
                    "color": "5"
                },
                {
                    "id": "node-understanding-1",
                    "type": "text",
                    "text": "逆否命题与原命题在真假性上是等价的，这个性质在逻辑证明中很有用。",
                    "x": 1200,
                    "y": 100,
                    "width": 450,
                    "height": 250,
                    "color": "6"
                }
            ],
            "edges": [
                {
                    "id": "edge-1",
                    "fromNode": "node-question-1",
                    "toNode": "node-explanation-1",
                    "fromSide": "right",
                    "toSide": "left"
                }
            ]
        }

        canvas_path = os.path.join(temp_workspace, "test_canvas.canvas")
        with open(canvas_path, 'w', encoding='utf-8') as f:
            json.dump(canvas_data, f, ensure_ascii=False, indent=2)

        return canvas_path

    @pytest.fixture
    def mock_dependencies(self):
        """Mock所有外部依赖"""
        with patch('mcp_memory_client.CHROMADB_AVAILABLE', True), \
             patch('mcp_memory_client.SENTENCE_TRANSFORMERS_AVAILABLE', True), \
             patch('mcp_memory_client.NUMPY_AVAILABLE', True), \
             patch('semantic_processor.JIEBA_AVAILABLE', True), \
             patch('creative_association_engine.NUMPY_AVAILABLE', True):

            # Mock ChromaDB
            mock_chromadb = Mock()
            mock_settings = Mock()
            mock_client = Mock()
            mock_collection = Mock()

            mock_chromadb.PersistentClient.return_value = mock_client
            mock_chromadb.Settings.return_value = mock_settings
            mock_client.get_or_create_collection.return_value = mock_collection

            # Mock Sentence Transformers
            mock_sentence_transformers = Mock()
            mock_torch = Mock()
            mock_model = Mock()
            mock_model.encode.return_value = [0.1, 0.2, 0.3, 0.4, 0.5]  # 5维向量
            mock_sentence_transformers.SentenceTransformer.return_value = mock_model
            mock_torch.cuda.is_available.return_value = False

            # Mock NumPy
            mock_numpy = Mock()
            mock_numpy.array = Mock(return_value=Mock())
            mock_numpy.mean = Mock(return_value=0.8)
            mock_numpy.random.rand = Mock(return_value=Mock(shape=(384,)))

            # Mock jieba
            mock_jieba = Mock()
            mock_pseg = Mock()
            mock_word = Mock()
            mock_word.flag = 'n'
            mock_jieba.cut.return_value = ['逆否', '命题', '逻辑学', '重要', '概念']
            mock_jieba.posseg.cut.return_value = [mock_word, mock_word, mock_word, mock_word, mock_word]

            # Apply patches
            patches = [
                patch('chromadb.PersistentClient', mock_chromadb.PersistentClient),
                patch('chromadb.Settings', mock_chromadb.Settings),
                patch('sentence_transformers.SentenceTransformer', mock_sentence_transformers.SentenceTransformer),
                patch('torch.cuda.is_available', mock_torch.cuda.is_available),
                patch('numpy.array', mock_numpy.array),
                patch('numpy.mean', mock_numpy.mean),
                patch('numpy.random.rand', mock_numpy.random.rand),
                patch('jieba.cut', mock_jieba.cut),
                patch('jieba.posseg.cut', mock_jieba.posseg.cut),
                patch('jieba.add_word', lambda *args, **kwargs: None)
            ]

            for p in patches:
                p.start()

            yield {
                'chromadb': mock_chromadb,
                'sentence_transformers': mock_sentence_transformers,
                'torch': mock_torch,
                'numpy': mock_numpy,
                'jieba': mock_jieba
            }

            for p in patches:
                p.stop()

    def test_complete_workflow(self, temp_config_file, temp_canvas_file, mock_dependencies):
        """测试完整工作流程"""
        with patch('canvas_utils.CanvasJSONOperator') as mock_canvas_operator:
            # Mock Canvas操作
            mock_canvas_operator.read_canvas.return_value = {
                "nodes": [
                    {
                        "id": "node-question-1",
                        "type": "text",
                        "text": "什么是逆否命题？",
                        "color": "1"
                    }
                ]
            }

            # 1. 初始化MCP集成
            integration = CanvasMCPIntegration(temp_config_file)
            assert integration.memory_client is not None
            assert integration.semantic_processor is not None
            assert integration.creative_engine is not None
            assert integration.memory_compressor is not None

            # 2. 集成Canvas
            result = integration.integrate_canvas_with_mcp(temp_canvas_file)
            assert result["success"] is True
            assert result["processed_nodes"] == 1
            assert len(result["memory_ids"]) == 1

            # 3. 语义搜索
            search_results = integration.semantic_search_canvas("逆否命题")
            assert isinstance(search_results, list)
            assert len(search_results) >= 0

            # 4. 跨Canvas洞察
            insights = integration.generate_cross_canvas_insights("逻辑")
            assert "concept" in insights
            assert "canvas_insights" in insights

            # 5. 获取统计
            stats = integration.get_integration_statistics()
            assert "memory_statistics" in stats
            assert "integration_health" in stats

            # 6. 清理
            integration.close()

    def test_memory_lifecycle(self, temp_config_file, mock_dependencies):
        """测试记忆生命周期"""
        # 初始化
        memory_client = MCPSemanticMemory(temp_config_file)

        # 测试存储
        content = "测试内容：逆否命题是逻辑学的重要概念"
        metadata = {"source": "test", "content_type": "concept"}
        memory_id = memory_client.store_semantic_memory(content, metadata)
        assert memory_id.startswith("memory-")

        # 测试搜索
        search_results = memory_client.search_semantic_memory("逆否命题")
        assert isinstance(search_results, list)

        # 测试标签生成
        tags = memory_client.auto_generate_tags(content)
        assert isinstance(tags, list)
        assert len(tags) > 0

        # 测试统计
        stats = memory_client.get_memory_stats()
        assert "total_memories" in stats
        assert "device" in stats

        # 清理
        memory_client.close()

    def test_semantic_processing_workflow(self, mock_dependencies):
        """测试语义处理工作流程"""
        processor = SemanticProcessor()

        # 测试文本处理
        text = "逆否命题是逻辑学中的重要概念，它与原命题在真假性上等价。"
        result = processor.process_text(text)

        assert "concepts" in result
        assert "tags" in result
        assert "language" in result
        assert "processing_time" in result

        # 验证结果
        assert len(result["concepts"]) > 0
        assert len(result["tags"]) > 0
        assert result["language"] in ["zh", "en"]

    def test_creative_association_workflow(self, temp_config_file, mock_dependencies):
        """测试创意联想工作流程"""
        memory_client = MCPSemanticMemory(temp_config_file)
        engine = CreativeAssociationEngine(memory_client)

        # 测试不同创意级别
        levels = ["conservative", "moderate", "creative"]

        for level in levels:
            result = engine.generate_creative_associations("逆否命题", level)

            assert "query_concept" in result
            assert "creative_insights" in result
            assert "analogies" in result
            assert "learning_paths" in result
            assert "overall_creativity_score" in result

            # 验证创意级别影响
            if level == "creative":
                assert result["overall_creativity_score"] > 0.7
            elif level == "conservative":
                assert result["overall_creativity_score"] < 0.5

        memory_client.close()

    def test_memory_compression_workflow(self, temp_config_file, mock_dependencies):
        """测试记忆压缩工作流程"""
        memory_client = MCPSemanticMemory(temp_config_file)
        compressor = MemoryCompressor(memory_client)

        # 创建测试记忆ID列表
        memory_ids = [f"memory-{i:016d}" for i in range(10)]

        # 测试压缩
        result = compressor.compress_memories(memory_ids, compression_ratio=0.3)

        assert result.original_memory_count == 10
        assert result.compressed_memory_count <= 10
        assert 0 <= result.compression_ratio <= 1.0
        assert result.information_retention_score > 0.8
        assert len(result.clusters) > 0

        memory_client.close()

    def test_command_interface_workflow(self, temp_config_file, mock_dependencies):
        """测试命令行接口工作流程"""
        with patch('canvas_utils.CanvasJSONOperator') as mock_canvas_operator:
            # Mock Canvas操作
            mock_canvas_operator.read_canvas.return_value = {
                "nodes": [
                    {
                        "id": "node-1",
                        "type": "text",
                        "text": "测试内容",
                        "color": "6"
                    }
                ]
            }

            # 初始化命令接口
            cmd_interface = MCPCommandInterface(temp_config_file)

            # 测试存储命令
            store_result = cmd_interface.store_memory_command(
                "测试记忆内容",
                {"source": "command_test"}
            )
            assert store_result["success"] is True
            assert "memory_id" in store_result

            # 测试搜索命令
            search_result = cmd_interface.search_memory_command("测试", limit=5)
            assert search_result["success"] is True
            assert "results" in search_result

            # 测试创意洞察命令
            creative_result = cmd_interface.creative_insights_command("概念", "moderate")
            assert creative_result["success"] is True
            assert "result" in creative_result

            # 测试统计命令
            stats_result = cmd_interface.get_statistics_command()
            assert stats_result["success"] is True
            assert "statistics" in stats_result

    def test_error_handling(self, temp_config_file, mock_dependencies):
        """测试错误处理"""
        # 测试无效配置文件
        with pytest.raises(Exception):
            MCPSemanticMemory("nonexistent_config.yaml")

        # 测试空内容存储
        memory_client = MCPSemanticMemory(temp_config_file)

        with pytest.raises(ValueError):
            memory_client.store_semantic_memory("", {})

        with pytest.raises(ValueError):
            memory_client.search_semantic_memory("", limit=10)

        memory_client.close()

    def test_performance_benchmarks(self, temp_config_file, mock_dependencies):
        """测试性能基准"""
        import time

        memory_client = MCPSemanticMemory(temp_config_file)
        processor = SemanticProcessor()

        # 测试存储性能
        start_time = time.time()
        for i in range(10):
            content = f"测试内容 {i}"
            memory_id = memory_client.store_semantic_memory(content, {"test": i})
        store_time = time.time() - start_time

        assert store_time < 5.0  # 应在5秒内完成10次存储

        # 测试搜索性能
        start_time = time.time()
        for i in range(5):
            results = memory_client.search_semantic_memory(f"测试 {i}", limit=10)
        search_time = time.time() - start_time

        assert search_time < 2.0  # 应在2秒内完成5次搜索

        # 测试语义处理性能
        start_time = time.time()
        text = "这是一个较长的测试文本，用于测试语义处理的性能。" * 10
        result = processor.process_text(text)
        process_time = time.time() - start_time

        assert process_time < 1.0  # 应在1秒内完成处理
        assert result["processing_time"] > 0

        memory_client.close()

    def test_configuration_validation(self, temp_workspace, mock_dependencies):
        """测试配置验证"""
        # 测试无效YAML配置
        invalid_config_path = os.path.join(temp_workspace, "config", "invalid_config.yaml")
        with open(invalid_config_path, 'w', encoding='utf-8') as f:
            f.write("invalid: yaml: content: [")

        with pytest.raises(Exception):
            MCPSemanticMemory(invalid_config_path)

        # 测试缺少必要字段
        minimal_config_path = os.path.join(temp_workspace, "config", "minimal_config.yaml")
        with open(minimal_config_path, 'w', encoding='utf-8') as f:
            f.write("mcp_service: {}")

        # 这应该使用默认配置
        memory_client = MCPSemanticMemory(minimal_config_path)
        assert memory_client.config is not None
        memory_client.close()

    def test_data_integrity(self, temp_config_file, temp_canvas_file, mock_dependencies):
        """测试数据完整性"""
        with patch('canvas_utils.CanvasJSONOperator') as mock_canvas_operator:
            # Mock Canvas操作
            mock_canvas_operator.read_canvas.return_value = {
                "nodes": [
                    {
                        "id": "node-1",
                        "type": "text",
                        "text": "测试内容",
                        "color": "1"
                    },
                    {
                        "id": "node-2",
                        "type": "text",
                        "text": "",  # 空内容节点
                        "color": "1"
                    },
                    {
                        "id": "node-3",
                        "type": "file",  # 非文本节点
                        "file": "test.pdf",
                        "color": "1"
                    }
                ]
            }

            # 集成Canvas
            integration = CanvasMCPIntegration(temp_config_file)
            result = integration.integrate_canvas_with_mcp(temp_canvas_file)

            # 验证只处理有效的文本节点
            assert result["processed_nodes"] == 1  # 只处理了一个有效文本节点
            assert result["skipped_nodes"] == 2    # 跳过了2个节点
            assert len(result["memory_ids"]) == 1   # 只创建了1个记忆

            # 验证错误处理
            assert len(result["processing_errors"]) == 0

            integration.close()

    def test_concurrent_operations(self, temp_config_file, mock_dependencies):
        """测试并发操作"""
        import threading
        import time

        memory_client = MCPSemanticMemory(temp_config_file)
        results = []
        errors = []

        def store_memory(index):
            try:
                content = f"并发测试内容 {index}"
                memory_id = memory_client.store_semantic_memory(content, {"thread": index})
                results.append(memory_id)
            except Exception as e:
                errors.append((index, str(e)))

        # 创建多个并发线程
        threads = []
        for i in range(5):
            thread = threading.Thread(target=store_memory, args=(i,))
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join(timeout=10)

        # 验证结果
        assert len(results) == 5
        assert len(errors) == 0
        assert len(set(results)) == 5  # 所有memory_id应该不同

        memory_client.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])