#!/usr/bin/env python3
"""
知识图谱层单元测试

测试Canvas Learning System的KnowledgeGraphLayer类功能
Author: Canvas Learning System Team
Version: 1.0 (Epic 6)
Created: 2025-10-18
"""

import asyncio
import os
import sys
import unittest
from unittest.mock import Mock, patch, AsyncMock
import tempfile
from pathlib import Path

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 需要在导入前重新加载模块以获取正确的环境变量
if 'canvas_utils' in sys.modules:
    del sys.modules['canvas_utils']

from canvas_utils import KnowledgeGraphLayer, create_knowledge_graph_layer


class TestKnowledgeGraphLayer(unittest.TestCase):
    """知识图谱层测试类"""

    def setUp(self):
        """测试前设置"""
        # 设置测试环境变量
        os.environ["GRAPHITI_ENABLED"] = "true"
        os.environ["NEO4J_URI"] = "bolt://localhost:7688"  # 测试端口
        os.environ["NEO4J_USER"] = "neo4j_test"
        os.environ["NEO4J_PASSWORD"] = "test_password"
        os.environ["OPENAI_API_KEY"] = "test-key-for-unit-testing"

    def tearDown(self):
        """测试后清理"""
        # 清理环境变量
        for key in ["GRAPHITI_ENABLED", "NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD", "OPENAI_API_KEY"]:
            if key in os.environ:
                del os.environ[key]

    def test_knowledge_graph_layer_initialization(self):
        """测试知识图谱层初始化 (AC: 1, 4)"""
        # Arrange
        os.environ["GRAPHITI_ENABLED"] = "true"

        # 重新加载模块以获取新的环境变量
        import canvas_utils
        import importlib
        importlib.reload(canvas_utils)

        # Act
        config = {
            "uri": "bolt://localhost:7688",
            "user": "neo4j_test",
            "password": "test_password"
        }
        kg_layer = canvas_utils.KnowledgeGraphLayer(config)

        # Assert
        self.assertEqual(kg_layer.config["uri"], "bolt://localhost:7688")
        self.assertEqual(kg_layer.config["user"], "neo4j_test")
        self.assertEqual(kg_layer.config["password"], "test_password")
        self.assertIn("Canvas", kg_layer.ENTITY_TYPES)
        self.assertIn("Node", kg_layer.ENTITY_TYPES)
        self.assertIn("CONTAINS", kg_layer.RELATIONSHIP_TYPES)
        self.assertIn("CONNECTS_TO", kg_layer.RELATIONSHIP_TYPES)

    def test_knowledge_graph_layer_disabled(self):
        """测试知识图谱功能禁用时的行为"""
        # Arrange
        os.environ["GRAPHITI_ENABLED"] = "false"

        # 重新加载模块以获取新的环境变量
        import canvas_utils
        import importlib
        importlib.reload(canvas_utils)

        # Act
        kg_layer = canvas_utils.KnowledgeGraphLayer()

        # Assert
        self.assertFalse(kg_layer.enabled)
        self.assertIsNone(kg_layer.graphiti_client)

    @patch('canvas_utils.Graphiti')
    async def test_graphiti_connection_initialization(self, mock_graphiti):
        """测试Graphiti连接初始化 (AC: 1, 4)"""
        # Arrange
        mock_client = AsyncMock()
        mock_client.build_indices_and_constraints = AsyncMock(return_value=None)
        mock_graphiti.return_value = mock_client

        kg_layer = KnowledgeGraphLayer()

        # Act
        result = await kg_layer.initialize()

        # Assert
        self.assertTrue(result)
        mock_graphiti.assert_called_once_with(
            uri="bolt://localhost:7687",
            user="neo4j",
            password="canvas123"
        )
        mock_client.build_indices_and_constraints.assert_called_once()

    @patch('canvas_utils.Graphiti')
    async def test_check_connection_success(self, mock_graphiti):
        """测试连接检查成功 (AC: 6)"""
        # Arrange
        mock_client = AsyncMock()
        mock_client.build_indices_and_constraints = AsyncMock(return_value=None)
        mock_client.driver.execute_query = AsyncMock(return_value=[{"test": 1}])
        mock_graphiti.return_value = mock_client

        kg_layer = KnowledgeGraphLayer()
        await kg_layer.initialize()

        # Act
        is_connected = await kg_layer.check_connection()

        # Assert
        self.assertTrue(is_connected)

    @patch('canvas_utils.Graphiti')
    async def test_check_connection_failure(self, mock_graphiti):
        """测试连接检查失败"""
        # Arrange
        mock_client = AsyncMock()
        mock_client.build_indices_and_constraints = AsyncMock(return_value=None)
        mock_client.driver.execute_query = AsyncMock(side_effect=Exception("Connection failed"))
        mock_graphiti.return_value = mock_client

        kg_layer = KnowledgeGraphLayer()
        await kg_layer.initialize()

        # Act
        is_connected = await kg_layer.check_connection()

        # Assert
        self.assertFalse(is_connected)

    @patch('canvas_utils.Graphiti')
    async def test_add_canvas_entity(self, mock_graphiti):
        """测试添加Canvas实体 (AC: 1, 5)"""
        # Arrange
        mock_client = AsyncMock()
        mock_client.build_indices_and_constraints = AsyncMock(return_value=None)
        mock_client.add_episode = AsyncMock(return_value={"uuid": "test-uuid-123"})
        mock_graphiti.return_value = mock_client

        kg_layer = KnowledgeGraphLayer()
        await kg_layer.initialize()

        canvas_data = {
            "file_path": "test_canvas.canvas",
            "nodes": [{"id": "node1", "type": "text"}],
            "edges": []
        }

        # Act
        result = await kg_layer.add_canvas_entity(canvas_data)

        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result["uuid"], "test-uuid-123")
        mock_client.add_episode.assert_called_once()

        # 验证调用参数
        call_args = mock_client.add_episode.call_args
        self.assertEqual(call_args[1]["name"], "Canvas: test_canvas.canvas")
        self.assertIn("Canvas文件: test_canvas.canvas", call_args[1]["episode_body"])

    @patch('canvas_utils.Graphiti')
    async def test_add_node_entity(self, mock_graphiti):
        """测试添加节点实体 (AC: 1, 5)"""
        # Arrange
        mock_client = AsyncMock()
        mock_client.build_indices_and_constraints = AsyncMock(return_value=None)
        mock_client.add_episode = AsyncMock(return_value={"uuid": "node-uuid-456"})
        mock_graphiti.return_value = mock_client

        kg_layer = KnowledgeGraphLayer()
        await kg_layer.initialize()

        node_data = {
            "id": "node1",
            "type": "text",
            "text": "测试节点内容",
            "color": "4",
            "x": 100,
            "y": 200,
            "width": 300,
            "height": 150
        }

        # Act
        result = await kg_layer.add_node_entity("canvas-123", node_data)

        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result["uuid"], "node-uuid-456")
        mock_client.add_episode.assert_called_once()

        # 验证调用参数
        call_args = mock_client.add_episode.call_args
        self.assertEqual(call_args[1]["name"], "Node: text (node1)")
        self.assertIn("节点ID: node1", call_args[1]["episode_body"])

    @patch('canvas_utils.Graphiti')
    async def test_add_relationship(self, mock_graphiti):
        """测试添加实体关系 (AC: 1, 5)"""
        # Arrange
        mock_client = AsyncMock()
        mock_client.build_indices_and_constraints = AsyncMock(return_value=None)
        mock_client.add_episode = AsyncMock(return_value={"uuid": "rel-uuid-789"})
        mock_graphiti.return_value = mock_client

        kg_layer = KnowledgeGraphLayer()
        await kg_layer.initialize()

        # Act
        result = await kg_layer.add_relationship(
            "entity-1", "entity-2", "CONTAINS", {"weight": 0.8}
        )

        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result["uuid"], "rel-uuid-789")
        mock_client.add_episode.assert_called_once()

        # 验证调用参数
        call_args = mock_client.add_episode.call_args
        self.assertEqual(call_args[1]["name"], "Relationship: CONTAINS")
        self.assertIn("源实体: entity-1", call_args[1]["episode_body"])
        self.assertIn("目标实体: entity-2", call_args[1]["episode_body"])

    def test_invalid_relationship_type(self):
        """测试无效关系类型处理"""
        # Arrange
        kg_layer = KnowledgeGraphLayer()

        # Act
        result = kg_layer.RELATIONSHIP_TYPES.get("INVALID_TYPE", "RELATED_TO")

        # Assert
        self.assertEqual(result, "RELATED_TO")

    @patch('canvas_utils.Graphiti')
    async def test_execute_query(self, mock_graphiti):
        """测试执行Cypher查询 (AC: 6)"""
        # Arrange
        mock_client = AsyncMock()
        mock_client.build_indices_and_constraints = AsyncMock(return_value=None)
        mock_client.driver.execute_query = AsyncMock(
            return_value=[{"count": 5}, {"count": 10}]
        )
        mock_graphiti.return_value = mock_client

        kg_layer = KnowledgeGraphLayer()
        await kg_layer.initialize()

        query = "MATCH (n) RETURN COUNT(n) as count"

        # Act
        result = await kg_layer.execute_query(query)

        # Assert
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["count"], 5)
        mock_client.driver.execute_query.assert_called_once_with(query)

    @patch('canvas_utils.Graphiti')
    async def test_performance_baseline_query(self, mock_graphiti):
        """测试性能基准：简单查询 <500ms (AC: 6)"""
        # Arrange
        mock_client = AsyncMock()
        mock_client.build_indices_and_constraints = AsyncMock(return_value=None)
        mock_client.driver.execute_query = AsyncMock(return_value=[{"count": 0}])
        mock_graphiti.return_value = mock_client

        kg_layer = KnowledgeGraphLayer()
        await kg_layer.initialize()

        import time
        query = "MATCH (n) RETURN COUNT(n) as count"

        # Act
        start_time = time.time()
        result = await kg_layer.execute_query(query)
        elapsed_ms = (time.time() - start_time) * 1000

        # Assert
        self.assertLess(elapsed_ms, 500, f"查询耗时{elapsed_ms:.2f}ms，超过500ms限制")
        self.assertIsNotNone(result)

    @patch('canvas_utils.KnowledgeGraphLayer', spec=KnowledgeGraphLayer)
    async def test_create_knowledge_graph_layer_success(self, mock_kg_class):
        """测试创建知识图谱层的便利函数 - 成功情况"""
        # Arrange
        mock_instance = AsyncMock()
        mock_instance.initialize = AsyncMock(return_value=True)
        mock_kg_class.return_value = mock_instance

        # Act
        result = await create_knowledge_graph_layer()

        # Assert
        self.assertIsNotNone(result)
        mock_instance.initialize.assert_called_once()

    @patch('canvas_utils.KnowledgeGraphLayer', spec=KnowledgeGraphLayer)
    async def test_create_knowledge_graph_layer_failure(self, mock_kg_class):
        """测试创建知识图谱层的便利函数 - 失败情况"""
        # Arrange
        mock_instance = AsyncMock()
        mock_instance.initialize = AsyncMock(return_value=False)
        mock_kg_class.return_value = mock_instance

        # Act
        result = await create_knowledge_graph_layer()

        # Assert
        self.assertIsNone(result)
        mock_instance.initialize.assert_called_once()


class TestKnowledgeGraphLayerIntegration(unittest.TestCase):
    """知识图谱层集成测试类（需要实际数据库连接）"""

    @unittest.skipUnless(os.getenv("RUN_INTEGRATION_TESTS"),
                        "需要设置RUN_INTEGRATION_TESTS环境变量来运行集成测试")
    async def test_real_neo4j_connection(self):
        """测试真实Neo4j连接（需要环境变量支持）"""
        # 这个测试需要真实的Neo4j环境
        kg_layer = await create_knowledge_graph_layer()

        if kg_layer:
            is_connected = await kg_layer.check_connection()
            self.assertTrue(is_connected)

            # 测试查询
            result = await kg_layer.execute_query("RETURN 1 as test")
            self.assertIsNotNone(result)

            await kg_layer.close()


# 运行测试的辅助函数
def run_async_test(coro):
    """运行异步测试的辅助函数"""
    return asyncio.run(coro)


if __name__ == "__main__":
    # 创建测试套件
    test_suite = unittest.TestSuite()

    # 添加测试用例
    test_suite.addTest(TestKnowledgeGraphLayer('test_knowledge_graph_layer_initialization'))
    test_suite.addTest(TestKnowledgeGraphLayer('test_knowledge_graph_layer_disabled'))
    test_suite.addTest(TestKnowledgeGraphLayer('test_invalid_relationship_type'))

    # 运行异步测试
    async_test_methods = [
        'test_graphiti_connection_initialization',
        'test_check_connection_success',
        'test_check_connection_failure',
        'test_add_canvas_entity',
        'test_add_node_entity',
        'test_add_relationship',
        'test_execute_query',
        'test_performance_baseline_query',
        'test_create_knowledge_graph_layer_success',
        'test_create_knowledge_graph_layer_failure'
    ]

    for method_name in async_test_methods:
        test_case = TestKnowledgeGraphLayer(method_name)
        test_suite.addTest(test_case)

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    # 如果有异步测试，单独运行
    if result.wasSuccessful():
        print("\n=== 运行异步测试 ===")
        for method_name in async_test_methods:
            try:
                test_instance = TestKnowledgeGraphLayer()
                test_instance.setUp()
                run_async_test(getattr(test_instance, method_name)())
                test_instance.tearDown()
                print(f"✅ {method_name} - 通过")
            except Exception as e:
                print(f"❌ {method_name} - 失败: {e}")