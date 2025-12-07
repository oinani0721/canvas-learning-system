#!/usr/bin/env python3
"""
Story 6.2 Canvas Memory Functionality 单元测试

测试Canvas Learning System的Story 6.2功能实现：
- Canvas结构解析
- Canvas实体记忆功能
- 多Canvas知识关联算法
- 同步机制
- 查询接口
- 性能优化和错误处理

Author: Canvas Learning System Team
Version: 1.0 (Epic 6 - Story 6.2)
Created: 2025-10-18
"""

import asyncio
import json
import os
import sys
import tempfile
import unittest
from unittest.mock import AsyncMock, patch

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 需要在导入前重新加载模块以获取正确的环境变量
if 'canvas_utils' in sys.modules:
    del sys.modules['canvas_utils']

from canvas_utils import CanvasJSONOperator, KnowledgeGraphLayer


class TestCanvasMemoryFunctionality(unittest.TestCase):
    """Story 6.2 Canvas记忆功能测试类"""

    def setUp(self):
        """测试前设置"""
        # 设置测试环境变量
        os.environ["GRAPHITI_ENABLED"] = "true"
        os.environ["NEO4J_URI"] = "bolt://localhost:7688"
        os.environ["NEO4J_USER"] = "neo4j_test"
        os.environ["NEO4J_PASSWORD"] = "test_password"
        os.environ["OPENAI_API_KEY"] = "test-key-for-unit-testing"

        # 创建测试Canvas数据
        self.test_canvas_data = {
            "nodes": [
                {
                    "id": "node-1234567890abcdef",
                    "type": "text",
                    "text": "测试节点内容",
                    "x": 100,
                    "y": 200,
                    "width": 400,
                    "height": 300,
                    "color": "1"
                },
                {
                    "id": "node-abcdef1234567890",
                    "type": "text",
                    "text": "黄色理解节点",
                    "x": 100,
                    "y": 550,
                    "width": 350,
                    "height": 150,
                    "color": "6"
                }
            ],
            "edges": [
                {
                    "id": "edge-1234567890abcdef",
                    "fromNode": "node-1234567890abcdef",
                    "toNode": "node-abcdef1234567890",
                    "label": "个人理解"
                }
            ]
        }

    def tearDown(self):
        """测试后清理"""
        # 清理环境变量
        for key in ["GRAPHITI_ENABLED", "NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD", "OPENAI_API_KEY"]:
            if key in os.environ:
                del os.environ[key]

    def test_parse_canvas_structure_success(self):
        """测试Canvas结构解析成功 (Task 1)"""
        # Act
        result = CanvasJSONOperator.parse_canvas_structure(self.test_canvas_data)

        # Assert
        self.assertIsInstance(result, dict)
        self.assertIn("nodes", result)
        self.assertIn("edges", result)
        self.assertIn("hierarchy", result)
        self.assertIn("metadata", result)

        # 验证节点解析
        self.assertEqual(len(result["nodes"]), 2)
        node = result["nodes"][0]
        self.assertEqual(node["id"], "node-1234567890abcdef")
        self.assertEqual(node["type"], "text")
        self.assertEqual(node["content"], "测试节点内容")
        self.assertEqual(node["color"], "1")

        # 验证元数据
        metadata = result["metadata"]
        self.assertEqual(metadata["node_count"], 2)
        self.assertEqual(metadata["edge_count"], 1)
        self.assertIn("color_distribution", metadata)
        self.assertIn("node_types", metadata)

    def test_parse_canvas_structure_empty_canvas(self):
        """测试解析空Canvas (Task 1)"""
        # Arrange
        empty_canvas = {"nodes": [], "edges": []}

        # Act
        result = CanvasJSONOperator.parse_canvas_structure(empty_canvas)

        # Assert
        self.assertEqual(result["metadata"]["node_count"], 0)
        self.assertEqual(result["metadata"]["edge_count"], 0)
        self.assertEqual(len(result["nodes"]), 0)
        self.assertEqual(len(result["edges"]), 0)

    def test_parse_canvas_structure_invalid_data(self):
        """测试解析无效Canvas数据 (Task 1)"""
        # Arrange & Act & Assert
        with self.assertRaises(ValueError):
            CanvasJSONOperator.parse_canvas_structure("invalid data")

        with self.assertRaises(ValueError):
            CanvasJSONOperator.parse_canvas_structure(None)

    @patch('canvas_utils.Graphiti')
    async def test_memorize_canvas_success(self, mock_graphiti):
        """测试Canvas记忆功能成功 (Task 2)"""
        # Arrange
        mock_client = AsyncMock()
        mock_client.build_indices_and_constraints = AsyncMock(return_value=None)
        mock_client.add_episode = AsyncMock(return_value={"uuid": "canvas-uuid-123"})
        mock_graphiti.return_value = mock_client

        kg_layer = KnowledgeGraphLayer()
        await kg_layer.initialize()

        with patch('canvas_utils.CanvasJSONOperator.read_canvas', return_value=self.test_canvas_data):
            # Act
            result = await kg_layer.memorize_canvas("test_canvas.canvas")

            # Assert
            self.assertTrue(result["success"])
            self.assertEqual(result["canvas_path"], "test_canvas.canvas")
            self.assertEqual(result["nodes_memorized"], 2)
            self.assertEqual(result["edges_memorized"], 1)
            self.assertIn("processing_time_ms", result)
            self.assertIn("metadata", result)

    @patch('canvas_utils.Graphiti')
    async def test_memorize_canvas_disabled(self, mock_graphiti):
        """测试知识图谱禁用时的Canvas记忆 (Task 2)"""
        # Arrange
        os.environ["GRAPHITI_ENABLED"] = "false"
        import importlib

        import canvas_utils
        importlib.reload(canvas_utils)

        kg_layer = canvas_utils.KnowledgeGraphLayer()

        # Act
        result = await kg_layer.memorize_canvas("test_canvas.canvas")

        # Assert
        self.assertFalse(result["success"])
        self.assertIn("error", result)
        self.assertEqual(result["error"], "知识图谱未启用或未初始化")

    @patch('canvas_utils.Graphiti')
    async def test_sync_canvas_changes_new_canvas(self, mock_graphiti):
        """测试同步Canvas变更 - 新Canvas (Task 4)"""
        # Arrange
        mock_client = AsyncMock()
        mock_client.build_indices_and_constraints = AsyncMock(return_value=None)
        mock_client.add_episode = AsyncMock(return_value={"uuid": "sync-uuid-123"})
        mock_client.driver.execute_query = AsyncMock(return_value=[])  # 没有找到现有Canvas
        mock_graphiti.return_value = mock_client

        kg_layer = KnowledgeGraphLayer()
        await kg_layer.initialize()

        with patch('canvas_utils.CanvasJSONOperator.read_canvas', return_value=self.test_canvas_data):
            # Act
            result = await kg_layer.sync_canvas_changes("new_canvas.canvas")

            # Assert
            self.assertTrue(result["success"])
            self.assertEqual(result["sync_type"], "full_create")
            self.assertEqual(result["nodes_added"], 2)
            self.assertEqual(result["edges_added"], 1)

    @patch('canvas_utils.Graphiti')
    async def test_sync_canvas_changes_existing_canvas(self, mock_graphiti):
        """测试同步Canvas变更 - 存在Canvas (Task 4)"""
        # Arrange
        mock_client = AsyncMock()
        mock_client.build_indices_and_constraints = AsyncMock(return_value=None)
        mock_client.add_episode = AsyncMock(return_value={"uuid": "update-uuid-123"})

        # 模拟找到现有Canvas
        mock_client.driver.execute_query.side_effect = [
            [{"file_path": "existing_canvas.canvas"}],  # 找到Canvas
            [],  # 没有删除的节点
            []   # 没有删除的边
        ]
        mock_graphiti.return_value = mock_client

        kg_layer = KnowledgeGraphLayer()
        await kg_layer.initialize()

        with patch('canvas_utils.CanvasJSONOperator.read_canvas', return_value=self.test_canvas_data):
            # Act
            result = await kg_layer.sync_canvas_changes("existing_canvas.canvas")

            # Assert
            self.assertTrue(result["success"])
            self.assertEqual(result["sync_type"], "incremental_update")
            self.assertIn("processing_time_ms", result)

    @patch('canvas_utils.Graphiti')
    async def test_find_related_canvases(self, mock_graphiti):
        """测试查找相关Canvas (Task 3)"""
        # Arrange
        mock_client = AsyncMock()
        mock_client.build_indices_and_constraints = AsyncMock(return_value=None)

        # 模拟相关Canvas查询结果
        mock_client.driver.execute_query.return_value = [
            {
                "canvas_path": "related_canvas1.canvas",
                "similarity_score": 0.85,
                "shared_concepts": ["数学", "逻辑"]
            },
            {
                "canvas_path": "related_canvas2.canvas",
                "similarity_score": 0.72,
                "shared_concepts": ["推理"]
            }
        ]
        mock_graphiti.return_value = mock_client

        kg_layer = KnowledgeGraphLayer()
        await kg_layer.initialize()

        # Act
        result = await kg_layer.find_related_canvases("target_canvas.canvas", limit=10)

        # Assert
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)

        # 验证返回格式
        related_canvas = result[0]
        self.assertIn("canvas_path", related_canvas)
        self.assertIn("similarity_score", related_canvas)
        self.assertIn("shared_concepts", related_canvas)
        self.assertGreaterEqual(related_canvas["similarity_score"], 0.0)
        self.assertLessEqual(related_canvas["similarity_score"], 1.0)

    @patch('canvas_utils.Graphiti')
    async def test_batch_memorize_canvases(self, mock_graphiti):
        """测试批量记忆Canvas (Task 6)"""
        # Arrange
        mock_client = AsyncMock()
        mock_client.build_indices_and_constraints = AsyncMock(return_value=None)
        mock_client.add_episode = AsyncMock(return_value={"uuid": "batch-uuid-123"})
        mock_graphiti.return_value = mock_client

        kg_layer = KnowledgeGraphLayer()
        await kg_layer.initialize()

        canvas_paths = ["canvas1.canvas", "canvas2.canvas", "canvas3.canvas"]

        with patch('canvas_utils.CanvasJSONOperator.read_canvas', return_value=self.test_canvas_data):
            # Act
            result = await kg_layer.batch_memorize_canvases(canvas_paths, max_concurrent=2)

            # Assert
            self.assertTrue(result["success"])
            self.assertEqual(result["total_canvases"], 3)
            self.assertEqual(result["successful_canvases"], 3)
            self.assertEqual(result["failed_canvases"], 0)
            self.assertIn("processing_time_ms", result)
            self.assertIn("results", result)

    @patch('canvas_utils.Graphiti')
    async def test_performance_benchmark(self, mock_graphiti):
        """测试性能基准测试 (Task 6)"""
        # Arrange
        mock_client = AsyncMock()
        mock_client.build_indices_and_constraints = AsyncMock(return_value=None)
        mock_client.add_episode = AsyncMock(return_value={"uuid": "benchmark-uuid"})
        mock_client.driver.execute_query = AsyncMock(return_value=[{"count": 1}])
        mock_graphiti.return_value = mock_client

        kg_layer = KnowledgeGraphLayer()
        await kg_layer.initialize()

        with patch('canvas_utils.CanvasJSONOperator.read_canvas', return_value=self.test_canvas_data):
            # Act
            result = await kg_layer.performance_benchmark("benchmark_canvas.canvas", iterations=3)

            # Assert
            self.assertIsInstance(result, dict)
            self.assertEqual(result["canvas_path"], "benchmark_canvas.canvas")
            self.assertEqual(result["iterations"], 3)
            self.assertEqual(result["node_count"], 2)
            self.assertEqual(result["edge_count"], 1)
            self.assertIn("tests", result)

            # 验证解析测试结果
            self.assertIn("parsing", result["tests"])
            parsing_test = result["tests"]["parsing"]
            self.assertIn("average_ms", parsing_test)
            self.assertIn("min_ms", parsing_test)
            self.assertIn("max_ms", parsing_test)

            # 验证记忆测试结果（如果启用）
            if kg_layer.enabled:
                self.assertIn("memory", result["tests"])

    def test_calculate_canvas_similarity_identical(self):
        """测试Canvas相似度计算 - 相同Canvas (Task 3)"""
        # Arrange
        kg_layer = KnowledgeGraphLayer()
        canvas1 = {"metadata": {"subjects": ["数学"], "node_types": {"text": 2}, "color_distribution": {"1": 1, "6": 1}}}
        canvas2 = {"metadata": {"subjects": ["数学"], "node_types": {"text": 2}, "color_distribution": {"1": 1, "6": 1}}}

        # Act
        result = asyncio.run(kg_layer._calculate_canvas_similarity(canvas1, canvas2))

        # Assert
        self.assertIsInstance(result, float)
        self.assertGreater(result, 0.8)  # 相同Canvas应该有很高相似度

    def test_calculate_canvas_similarity_different(self):
        """测试Canvas相似度计算 - 不同Canvas (Task 3)"""
        # Arrange
        kg_layer = KnowledgeGraphLayer()
        canvas1 = {"metadata": {"subjects": ["数学"], "node_types": {"text": 2}, "color_distribution": {"1": 2}}}
        canvas2 = {"metadata": {"subjects": ["历史"], "node_types": {"file": 1}, "color_distribution": {"2": 1}}}

        # Act
        result = asyncio.run(kg_layer._calculate_canvas_similarity(canvas1, canvas2))

        # Assert
        self.assertIsInstance(result, float)
        self.assertLess(result, 0.5)  # 不同Canvas应该有较低相似度

    @patch('canvas_utils.Graphiti')
    async def test_get_canvas_memory_status_existing(self, mock_graphiti):
        """测试获取Canvas记忆状态 - 存在的Canvas (Task 5)"""
        # Arrange
        mock_client = AsyncMock()
        mock_client.build_indices_and_constraints = AsyncMock(return_value=None)

        # 模拟找到Canvas记忆状态
        mock_client.driver.execute_query.return_value = [
            {
                "file_path": "existing_canvas.canvas",
                "last_sync": "2025-10-18T10:00:00Z",
                "node_count": 5,
                "relationship_count": 3
            }
        ]
        mock_graphiti.return_value = mock_client

        kg_layer = KnowledgeGraphLayer()
        await kg_layer.initialize()

        # Act
        result = await kg_layer.get_canvas_memory_status("existing_canvas.canvas")

        # Assert
        self.assertTrue(result["is_memorized"])
        self.assertEqual(result["canvas_path"], "existing_canvas.canvas")
        self.assertIn("last_sync", result)
        self.assertIn("knowledge_graph_nodes", result)
        self.assertIn("knowledge_graph_relationships", result)

    @patch('canvas_utils.Graphiti')
    async def test_get_canvas_memory_status_nonexistent(self, mock_graphiti):
        """测试获取Canvas记忆状态 - 不存在的Canvas (Task 5)"""
        # Arrange
        mock_client = AsyncMock()
        mock_client.build_indices_and_constraints = AsyncMock(return_value=None)
        mock_client.driver.execute_query.return_value = []  # 没有找到Canvas
        mock_graphiti.return_value = mock_client

        kg_layer = KnowledgeGraphLayer()
        await kg_layer.initialize()

        with patch('canvas_utils.CanvasJSONOperator.read_canvas', return_value=self.test_canvas_data):
            # Act
            result = await kg_layer.get_canvas_memory_status("nonexistent_canvas.canvas")

            # Assert
            self.assertFalse(result["is_memorized"])
            self.assertEqual(result["canvas_path"], "nonexistent_canvas.canvas")
            self.assertIn("total_nodes", result)
            self.assertIn("total_edges", result)
            self.assertIn("suggested_type", result)

    @patch('canvas_utils.Graphiti')
    async def test_search_canvas_content(self, mock_graphiti):
        """测试搜索Canvas内容 (Task 5)"""
        # Arrange
        mock_client = AsyncMock()
        mock_client.build_indices_and_constraints = AsyncMock(return_value=None)

        # 模拟搜索结果
        mock_client.driver.execute_query.return_value = [
            {
                "node_type": "Node",
                "name": "测试节点内容",
                "content": "这是关于数学的测试内容",
                "relevance_score": 0.9
            },
            {
                "node_type": "Concept",
                "name": "数学概念",
                "content": "数学相关概念解释",
                "relevance_score": 0.8
            }
        ]
        mock_graphiti.return_value = mock_client

        kg_layer = KnowledgeGraphLayer()
        await kg_layer.initialize()

        # Act
        result = await kg_layer.search_canvas_content("数学", limit=10)

        # Assert
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)

        # 验证搜索结果格式
        search_result = result[0]
        self.assertIn("node_type", search_result)
        self.assertIn("name", search_result)
        self.assertIn("content", search_result)
        self.assertIn("relevance_score", search_result)
        self.assertGreaterEqual(search_result["relevance_score"], 0.0)
        self.assertLessEqual(search_result["relevance_score"], 1.0)

    def test_determine_canvas_type_mathematics(self):
        """测试Canvas类型判断 - 数学类型 (Task 1)"""
        # Arrange
        kg_layer = KnowledgeGraphLayer()
        metadata = {
            "subjects": ["数学", "代数"],
            "node_types": {"text": 5, "file": 2}
        }

        # Act
        result = kg_layer._determine_canvas_type("test_canvas.canvas", metadata)

        # Assert
        self.assertEqual(result, "数学")

    def test_determine_canvas_type_unknown(self):
        """测试Canvas类型判断 - 未知类型 (Task 1)"""
        # Arrange
        kg_layer = KnowledgeGraphLayer()
        metadata = {
            "subjects": [],
            "node_types": {"text": 1}
        }

        # Act
        result = kg_layer._determine_canvas_type("test_canvas.canvas", metadata)

        # Assert
        self.assertEqual(result, "综合")

    @patch('canvas_utils.Graphiti')
    async def test_error_handling_file_not_found(self, mock_graphiti):
        """测试错误处理 - Canvas文件不存在 (Task 7)"""
        # Arrange
        mock_client = AsyncMock()
        mock_client.build_indices_and_constraints = AsyncMock(return_value=None)
        mock_graphiti.return_value = mock_client

        kg_layer = KnowledgeGraphLayer()
        await kg_layer.initialize()

        # Act & Assert
        result = await kg_layer.memorize_canvas("nonexistent_canvas.canvas")

        self.assertFalse(result["success"])
        self.assertIn("error", result)
        self.assertIn("文件不存在", result["error"])

    @patch('canvas_utils.Graphiti')
    async def test_error_handling_invalid_json(self, mock_graphiti):
        """测试错误处理 - 无效JSON (Task 7)"""
        # Arrange
        mock_client = AsyncMock()
        mock_client.build_indices_and_constraints = AsyncMock(return_value=None)
        mock_graphiti.return_value = mock_client

        kg_layer = KnowledgeGraphLayer()
        await kg_layer.initialize()

        with patch('canvas_utils.CanvasJSONOperator.read_canvas', side_effect=json.JSONDecodeError("Invalid JSON", "", 0)):
            # Act
            result = await kg_layer.memorize_canvas("invalid_canvas.canvas")

            # Assert
            self.assertFalse(result["success"])
            self.assertIn("error", result)


class TestCanvasMemoryIntegration(unittest.TestCase):
    """Story 6.2 Canvas记忆功能集成测试类"""

    @unittest.skipUnless(os.getenv("RUN_INTEGRATION_TESTS"),
                         "需要设置RUN_INTEGRATION_TESTS环境变量来运行集成测试")
    async def test_full_canvas_memory_workflow(self):
        """测试完整Canvas记忆工作流程（需要实际数据库）"""
        # 这个测试需要真实的Neo4j环境
        kg_layer = KnowledgeGraphLayer()
        success = await kg_layer.initialize()

        if success:
            # 创建临时Canvas文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.canvas', delete=False) as f:
                temp_canvas_path = f.name
                test_data = {
                    "nodes": [
                        {"id": "test-node-1", "type": "text", "text": "集成测试节点", "x": 0, "y": 0, "width": 300, "height": 200, "color": "1"}
                    ],
                    "edges": []
                }
                json.dump(test_data, f)

            try:
                # 测试完整工作流程
                # 1. 记忆Canvas
                result = await kg_layer.memorize_canvas(temp_canvas_path)
                self.assertTrue(result["success"])

                # 2. 检查记忆状态
                status = await kg_layer.get_canvas_memory_status(temp_canvas_path)
                self.assertTrue(status["is_memorized"])

                # 3. 搜索内容
                search_results = await kg_layer.search_canvas_content("集成测试")
                self.assertIsInstance(search_results, list)

                # 4. 同步变更
                test_data["nodes"][0]["text"] = "更新后的测试节点"
                with open(temp_canvas_path, 'w') as f:
                    json.dump(test_data, f)

                sync_result = await kg_layer.sync_canvas_changes(temp_canvas_path)
                self.assertTrue(sync_result["success"])

            finally:
                # 清理临时文件
                os.unlink(temp_canvas_path)
                await kg_layer.close()


# 运行测试的辅助函数
def run_async_test(coro):
    """运行异步测试的辅助函数"""
    return asyncio.run(coro)


if __name__ == "__main__":
    # 创建测试套件
    test_suite = unittest.TestSuite()

    # 添加测试用例
    test_methods = [
        'test_parse_canvas_structure_success',
        'test_parse_canvas_structure_empty_canvas',
        'test_parse_canvas_structure_invalid_data',
        'test_determine_canvas_type_mathematics',
        'test_determine_canvas_type_unknown',
        'test_calculate_canvas_similarity_identical',
        'test_calculate_canvas_similarity_different'
    ]

    for method_name in test_methods:
        test_suite.addTest(TestCanvasMemoryFunctionality(method_name))

    # 运行同步测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    # 运行异步测试
    async_test_methods = [
        'test_memorize_canvas_success',
        'test_memorize_canvas_disabled',
        'test_sync_canvas_changes_new_canvas',
        'test_sync_canvas_changes_existing_canvas',
        'test_find_related_canvases',
        'test_batch_memorize_canvases',
        'test_performance_benchmark',
        'test_get_canvas_memory_status_existing',
        'test_get_canvas_memory_status_nonexistent',
        'test_search_canvas_content',
        'test_error_handling_file_not_found',
        'test_error_handling_invalid_json'
    ]

    print("\n=== 运行异步测试 ===")
    for method_name in async_test_methods:
        try:
            test_instance = TestCanvasMemoryFunctionality()
            test_instance.setUp()
            run_async_test(getattr(test_instance, method_name)())
            test_instance.tearDown()
            print(f"✅ {method_name} - 通过")
        except Exception as e:
            print(f"❌ {method_name} - 失败: {e}")
            import traceback
            traceback.print_exc()
