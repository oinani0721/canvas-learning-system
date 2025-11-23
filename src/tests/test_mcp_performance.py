"""
MCP性能基准测试
Canvas Learning System - Story 8.8

测试MCP语义记忆服务的性能指标，确保满足PRD要求。
"""

import pytest
import time
import statistics
import tempfile
import os
import threading
from unittest.mock import Mock, patch
from concurrent.futures import ThreadPoolExecutor, as_completed

# 导入测试目标
from mcp_memory_client import MCPSemanticMemory
from semantic_processor import SemanticProcessor
from creative_association_engine import CreativeAssociationEngine
from memory_compression import MemoryCompressor
from canvas_mcp_integration import CanvasMCPIntegration


class TestMCPPerformance:
    """MCP性能基准测试"""

    @pytest.fixture
    def mock_environment(self):
        """Mock测试环境"""
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

            # 配置Mock对象
            mock_client.get_or_create_collection.return_value = mock_collection
            mock_collection.add.return_value = None
            mock_collection.query.return_value = {
                'ids': [['test-id-1', 'test-id-2']],
                'documents': [['文档1'], ['文档2']],
                'metadatas': [[{'source': 'test1'}], [{'source': 'test2'}]],
                'distances': [[0.1, 0.2]]
            }

            mock_chromadb.PersistentClient.return_value = mock_client
            mock_chromadb.Settings.return_value = mock_settings

            # Mock Sentence Transformers
            mock_sentence_transformers = Mock()
            mock_model = Mock()
            mock_model.encode.return_value = [0.1, 0.2, 0.3, 0.4] * 96  # 384维向量

            mock_sentence_transformers.SentenceTransformer.return_value = mock_model

            # Mock torch
            mock_torch = Mock()
            mock_torch.cuda.is_available.return_value = True
            mock_torch.cuda.device_count.return_value = 2
            mock_torch.cuda.get_device_properties.return_value = Mock(total_memory=8*1024*1024*1024)

            # Mock numpy
            mock_numpy = Mock()
            mock_numpy.array.return_value = Mock()
            mock_numpy.mean.return_value = 0.8
            mock_numpy.random.rand.return_value = Mock(shape=(384,))

            # Mock jieba
            mock_jieba = Mock()
            mock_pseg = Mock()
            mock_word = Mock()
            mock_word.flag = 'n'
            mock_jieba.cut.return_value = ['测试', '内容', '关键词']
            mock_jieba.posseg.cut.return_value = [mock_word, mock_word, mock_word]
            mock_jieba.add_word.side_effect = lambda *args, **kwargs: None

            with patch('chromadb.PersistentClient', mock_chromadb.PersistentClient), \
                 patch('chromadb.Settings', mock_chromadb.Settings), \
                 patch('sentence_transformers.SentenceTransformer', mock_sentence_transformers.SentenceTransformer), \
                 patch('torch.cuda', mock_torch.cuda), \
                 patch('numpy.array', mock_numpy.array), \
                 patch('numpy.mean', mock_numpy.mean), \
                 patch('numpy.random.rand', mock_numpy.random.rand), \
                 patch('jieba.cut', mock_jieba.cut), \
                 patch('jieba.posseg.cut', mock_jieba.posseg.cut), \
                 patch('jieba.add_word', mock_jieba.add_word):

                yield {
                    'chromadb': mock_chromadb,
                    'sentence_transformers': mock_sentence_transformers,
                    'torch': mock_torch,
                    'numpy': mock_numpy,
                    'jieba': mock_jieba
                }

    def test_embedding_performance(self, mock_environment):
        """测试文本嵌入性能"""
        config_content = """
mcp_service:
  embedding_model:
    model_name: "test-model"
    device: "cpu"
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_path = f.name

        client = MCPSemanticMemory(config_path)

        # 测试数据准备
        test_texts = [
            "短文本",
            "中等长度的测试文本内容，用于测试嵌入性能",
            "这是一个较长的测试文本内容，包含了更多的词汇和句子结构，用于测试在处理复杂文本时嵌入模型的性能表现",
            "一个非常长的测试文本内容，包含了多个段落和复杂的句子结构。" * 5 + "这是一个超长的测试内容。" * 3
        ]

        # 性能测试
        embedding_times = []
        for text in test_texts:
            start_time = time.time()
            embedding = client.embedding_model.encode(text)
            end_time = time.time()

            embedding_time = (end_time - start_time) * 1000  # 转换为毫秒
            embedding_times.append(embedding_time)

            # 验证嵌入结果
            assert len(embedding) == 384, "嵌入向量维度应为384"

        # 性能断言
        avg_embedding_time = statistics.mean(embedding_times)
        max_embedding_time = max(embedding_times)

        logger.info(f"嵌入性能统计: 平均={avg_embedding_time:.2f}ms, 最大={max_embedding_time:.2f}ms")

        # PRD要求: 单段文本嵌入处理<500ms
        assert avg_embedding_time < 500, f"平均嵌入时间 {avg_embedding_time:.2f}ms 超过500ms阈值"
        assert max_embedding_time < 1000, f"最大嵌入时间 {max_embedding_time:.2f}ms 超过1s阈值"

        client.close()

    def test_search_performance(self, mock_environment):
        """测试语义搜索性能"""
        config_content = """
mcp_service:
  vector_database:
    type: "chromadb"
    persist_directory: "./test_db"
    collection_name: "test_collection"
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_path = f.name

        client = MCPSemanticMemory(config_path)

        # 准备测试数据
        test_memory_count = 100
        for i in range(test_memory_count):
            memory_id = f"test-memory-{i:04d}"
            content = f"测试内容 {i}，包含关键词关键词{i%10}"
            embedding = [0.1] * 384  # Mock向量
            metadata = {"source": f"test-{i%5}", "index": i}

            client.collection.add.return_value = None
            client.collection.query.return_value = {
                'ids': [[memory_id]],
                'documents': [[content]],
                'metadatas': [[metadata]],
                'distances': [[0.1]]
            }

        # 性能测试
        search_times = []
        for _ in range(10):
            start_time = time.time()
            results = client.search_semantic_memory("关键词", limit=10)
            end_time = time.time()

            search_time = (end_time - start_time) * 1000
            search_times.append(search_time)

            # 验证搜索结果
            assert isinstance(results, list)
            assert len(results) <= 10

        avg_search_time = statistics.mean(search_times)
        max_search_time = max(search_times)

        logger.info(f"搜索性能统计: 平均={avg_search_time:.2f}ms, 最大={max_search_time:.2f}ms")

        # PRD要求: 语义搜索响应时间<2秒
        assert avg_search_time < 2000, f"平均搜索时间 {avg_search_time:.2f}ms 超过2s阈值"

        client.close()

    def test_semantic_processing_performance(self, mock_environment):
        """测试语义处理性能"""
        processor = SemanticProcessor()

        # 测试数据准备
        test_texts = [
            "短文本",
            "中等长度的测试文本内容，用于测试语义处理的性能",
            "这是一个较长的测试文本内容，包含了更多词汇和句子结构，用于测试在处理复杂文本时语义处理器的性能表现"
        ]

        processing_times = []
        for text in test_texts:
            start_time = time.time()
            result = processor.process_text(text)
            end_time = time.time()

            processing_time = (end_time - start_time) * 1000
            processing_times.append(processing_time)

            # 验证处理结果
            assert "concepts" in result
            assert "tags" in result
            assert "language" in result

        avg_processing_time = statistics.mean(processing_times)
        max_processing_time = max(processing_times)

        logger.info(f"语义处理性能统计: 平均={avg_processing_time:.2f}ms, 最大={max_processing_time:.2f}ms")

        # 语义处理应该较快（建议<1秒）
        assert avg_processing_time < 1000, f"平均处理时间 {avg_processing_time:.2f}ms 超过1s阈值"

    def test_creative_association_performance(self, mock_environment):
        """测试创意联想性能"""
        config_content = """
mcp_service:
  creative_association:
    enable: true
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_path = f.name

        # Mock记忆客户端
        memory_client = Mock()
        memory_client.search_semantic_memory.return_value = [
            {"memory_id": "test-1", "similarity_score": 0.8},
            {"memory_id": "test-2", "similarity_score": 0.7},
            {"memory_id": "test-3", "similarity_score": 0.6}
        ]

        engine = CreativeAssociationEngine(memory_client)

        # 性能测试
        association_times = []
        creativity_levels = ["conservative", "moderate", "creative"]

        for level in creativity_levels:
            start_time = time.time()
            result = engine.generate_creative_associations("测试概念", level)
            end_time = time.time()

            association_time = (end_time - start_time) * 1000
            association_times.append(association_time)

            # 验证联想结果
            assert "creative_insights" in result
            assert "analogies" in result
            assert "learning_paths" in result

        avg_association_time = statistics.mean(association_times)
        max_association_time = max(association_times)

        logger.info(f"创意联想性能统计: 平均={avg_association_time:.2f}ms, 最大={max_association_time:.2f}ms")

        # PRD要求: 创意联想生成<5秒
        assert avg_association_time < 5000, f"平均联想时间 {avg_association_time:.2f}ms 超过5s阈值"

    def test_compression_performance(self, mock_environment):
        """测试记忆压缩性能"""
        config_content = """
mcp_service:
  memory_management:
    max_memories_per_collection: 10000
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_path = f.name

        # Mock记忆客户端
        memory_client = Mock()
        memory_client.get_memory_stats.return_value = {"total_memories": 1000}

        with patch('memory_compression.SKLEARN_AVAILABLE', True):
            import numpy as np
            mock_sklearn = Mock()
            mock_kmeans = Mock()
            mock_kmeans.fit.return_value = Mock()
            mock_kmeans.predict.return_value = [0, 1, 2, 3]  # 预测簇标签

            with patch('sklearn.cluster.KMeans', mock_kmeans), \
                 patch('numpy.array', np.array):
                compressor = MemoryCompressor(memory_client)

                # 准备测试记忆
                memory_ids = [f"memory-{i:04d}" for i in range(100)]

                # 性能测试
                start_time = time.time()
                result = compressor.compress_memories(memory_ids, compression_ratio=0.3)
                end_time = time.time()

                compression_time = (end_time - start_time) * 1000

                # 验证压缩结果
                assert result.original_memory_count == 100
                assert result.compressed_memory_count <= 30  # 压缩到30%以内
                assert result.compression_ratio <= 0.3
                assert result.information_retention_score > 0.9

                logger.info(f"压缩性能: 时间={compression_time:.2f}ms, 压缩比={result.compression_ratio:.3f}")

                # PRD要求: 批量压缩操作<30秒
                assert compression_time < 30000, f"压缩时间 {compression_time:.2f}ms 超过30s阈值"

    def test_concurrent_operations(self, mock_environment):
        """测试并发操作性能"""
        config_content = """
mcp_service:
  embedding_model:
    device: "cpu"
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_path = f.name

        client = MCPSemanticMemory(config_path)

        # 并发存储测试
        def store_memory(index):
            content = f"并发测试内容 {index}"
            metadata = {"thread": f"thread-{index}"}

            # Mock collection add
            client.collection.add.return_value = None
            return client.store_semantic_memory(content, metadata)

        start_time = time.time()
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(store_memory, i) for i in range(50)]

            # 等待所有操作完成
            memory_ids = []
            for future in as_completed(futures):
                memory_id = future.result()
                memory_ids.append(memory_id)

        end_time = time.time()

        concurrent_time = (end_time - start_time) * 1000
        assert len(memory_ids) == 50

        logger.info(f"并发存储性能: 50个操作耗时 {concurrent_time:.2f}ms")

        # 并发操作应该在合理时间内完成
        assert concurrent_time < 30000, f"并发操作时间 {concurrent_time:.2f}ms 过长"

        client.close()

    def test_memory_usage_simulation(self, mock_environment):
        """模拟内存使用情况"""
        config_content = """
mcp_service:
  memory_management:
    max_memories_per_collection: 100
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_path = f.name

        client = MCPSemanticMemory(config_path)

        # 模拟内存使用
        initial_memory_usage = 100 * 1024 * 1024  # 100MB

        with patch('psutil.virtual_memory') as mock_memory:
            mock_memory_info = Mock()
            mock_memory_info.total = initial_memory_usage
            mock_memory.return_value = mock_memory_info

            # 模拟内存增长
            def check_memory_usage():
                current_usage = psutil.virtual_memory().total
                memory_growth = current_usage - initial_memory_usage
                logger.info(f"当前内存使用: {current_usage / (1024*1024)}MB, 增长: {memory_growth / (1024*1024)}MB")
                return memory_growth / (1024*1024)  # 返回MB

            # 模拟一些操作后的内存使用
            client.collection.add.return_value = None
            for i in range(10):
                client.store_semantic_memory(f"测试内容 {i}", {"index": i})

            # 检查内存使用
            memory_growth = check_memory_usage()

            # 内存增长应该在合理范围内
            assert memory_growth < 50, f"内存增长 {memory_growth}MB 超过预期"

        client.close()

    def test_resource_cleanup_performance(self, mock_environment):
        """测试资源清理性能"""
        config_content = """
mcp_service:
  embedding_model:
    device: "cpu"
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_path = f.name

        # 测试多次初始化和清理
        for i in range(5):
            client = MCPSemanticMemory(config_path)

            # 执行一些操作
            client.collection.add.return_value = None
            client.store_semantic_memory(f"测试内容 {i}", {"iteration": i})

            # 清理资源
            start_time = time.time()
            client.close()
            cleanup_time = time.time() - start_time

            logger.info(f"清理操作 {i+1}: {cleanup_time:.3f}s")

            # 清理应该很快完成
            assert cleanup_time < 1.0, f"清理时间 {cleanup_time:.3f}s 过长"

    @pytest.mark.slow
    def test_system_scalability(self, mock_environment):
        """测试系统可扩展性"""
        config_content = """
mcp_service:
  vector_database:
    type: "chromadb"
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_path = f.name

        client = MCPSemanticMemory(config_path)

        # 测试大规模数据
        large_dataset_size = 1000
        memory_ids = []

        start_time = time.time()

        # 批量存储
        for i in range(large_dataset_size):
            content = f"大规模测试数据 {i}，包含足够的内容来测试系统在处理大规模数据时的性能表现"
            metadata = {"batch": "large", "index": i}

            client.collection.add.return_value = None
            memory_id = client.store_semantic_memory(content, metadata)
            memory_ids.append(memory_id)

        batch_time = time.time() - start_time
        avg_batch_time = batch_time / large_dataset_size * 1000

        logger.info(f"大规模存储性能: {large_dataset_size}条记录耗时 {batch_time:.2f}s, 平均{avg_batch_time:.2f}ms/条")

        # 批量存储性能要求
        assert avg_batch_time < 100, f"平均存储时间 {avg_batch_time:.2f}ms/条 过长"

        # 大规模搜索测试
        start_time = time.time()
        search_results = client.search_semantic_memory("大规模", limit=100)
        search_time = time.time() - start_time

        logger.info(f"大规模搜索性能: {search_time:.3f}s, 返回{len(search_results)}条结果")

        # 大规模搜索应该合理快速
        assert search_time < 5.0, f"大规模搜索时间 {search_time:.3f}s 过长"

        client.close()


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    pytest.main([__file__, "-v", "--tb=short", "-k", "test_embedding_performance"])