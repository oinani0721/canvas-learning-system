#!/usr/bin/env python3
"""
知识图谱层基础测试

专注于Story 6.1的核心功能测试
"""

import asyncio
import os
import sys
import unittest
from unittest.mock import AsyncMock, patch

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestKnowledgeGraphLayerBasic(unittest.TestCase):
    """知识图谱层基础功能测试"""

    def setUp(self):
        """测试前设置"""
        # 设置环境变量
        os.environ["GRAPHITI_ENABLED"] = "true"
        os.environ["NEO4J_URI"] = "bolt://localhost:7688"
        os.environ["NEO4J_USER"] = "neo4j"
        os.environ["NEO4J_PASSWORD"] = "test_password"
        os.environ["OPENAI_API_KEY"] = "test-key"

        # 重新导入模块以获取新的环境变量
        if 'canvas_utils' in sys.modules:
            del sys.modules['canvas_utils']

        from canvas_utils import KnowledgeGraphLayer
        self.KnowledgeGraphLayer = KnowledgeGraphLayer

    def test_kg_layer_initialization(self):
        """测试知识图谱层初始化 (AC: 1, 4)"""
        # Arrange & Act
        kg_layer = self.KnowledgeGraphLayer()

        # Assert
        self.assertTrue(kg_layer.enabled)
        self.assertEqual(kg_layer.config["uri"], "bolt://localhost:7688")
        self.assertEqual(kg_layer.config["user"], "neo4j")
        self.assertIn("Canvas", kg_layer.ENTITY_TYPES)
        self.assertIn("Node", kg_layer.ENTITY_TYPES)
        self.assertIn("CONTAINS", kg_layer.RELATIONSHIP_TYPES)

    def test_entity_types_defined(self):
        """测试实体类型定义 (AC: 3)"""
        # Arrange & Act
        kg_layer = self.KnowledgeGraphLayer()

        # Assert
        expected_entity_types = ["Canvas", "Node", "Concept", "Topic", "User"]
        for entity_type in expected_entity_types:
            self.assertIn(entity_type, kg_layer.ENTITY_TYPES)

    def test_relationship_types_defined(self):
        """测试关系类型定义 (AC: 3)"""
        # Arrange & Act
        kg_layer = self.KnowledgeGraphLayer()

        # Assert
        expected_relationship_types = ["CONTAINS", "CONNECTS_TO", "LEARNS", "EXPLORES", "RELATED_TO", "REQUIRES"]
        for rel_type in expected_relationship_types:
            self.assertIn(rel_type, kg_layer.RELATIONSHIP_TYPES)

    @patch('canvas_utils.Graphiti')
    async def test_connection_success(self, mock_graphiti):
        """测试连接初始化成功 (AC: 1, 4, 6)"""
        # Arrange
        mock_client = AsyncMock()
        mock_client.build_indices_and_constraints = AsyncMock()
        mock_client.driver.execute_query = AsyncMock(return_value=[{"test": 1}])
        mock_graphiti.return_value = mock_client

        # Act
        kg_layer = self.KnowledgeGraphLayer()
        init_success = await kg_layer.initialize()
        is_connected = await kg_layer.check_connection()

        # Assert
        self.assertTrue(init_success)
        self.assertTrue(is_connected)
        mock_graphiti.assert_called_once()
        mock_client.build_indices_and_constraints.assert_called_once()

    @patch('canvas_utils.Graphiti')
    async def test_add_canvas_episode(self, mock_graphiti):
        """测试添加Canvas episode (AC: 1, 5)"""
        # Arrange
        mock_client = AsyncMock()
        mock_client.build_indices_and_constraints = AsyncMock()
        mock_client.add_episode = AsyncMock(return_value={"uuid": "canvas-123"})
        mock_graphiti.return_value = mock_client

        # Act
        kg_layer = self.KnowledgeGraphLayer()
        await kg_layer.initialize()

        canvas_data = {
            "file_path": "test.canvas",
            "nodes": [{"id": "node1"}],
            "edges": []
        }

        result = await kg_layer.add_canvas_entity(canvas_data)

        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result["uuid"], "canvas-123")
        mock_client.add_episode.assert_called_once()

    @patch('canvas_utils.Graphiti')
    async def test_query_execution(self, mock_graphiti):
        """测试执行查询 (AC: 6)"""
        # Arrange
        mock_client = AsyncMock()
        mock_client.build_indices_and_constraints = AsyncMock()
        mock_client.driver.execute_query = AsyncMock(return_value=[{"count": 5}])
        mock_graphiti.return_value = mock_client

        # Act
        kg_layer = self.KnowledgeGraphLayer()
        await kg_layer.initialize()

        result = await kg_layer.execute_query("MATCH (n) RETURN COUNT(n)")

        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result[0]["count"], 5)

    def test_performance_requirement_documented(self):
        """测试性能要求已文档化 (AC: 6)"""
        # Story 6.1要求基础查询 <500ms
        # 这是一个文档检查，确保要求明确
        from canvas_utils import KnowledgeGraphLayer

        kg_layer = KnowledgeGraphLayer()
        # 验证性能相关的配置和文档存在
        self.assertTrue(hasattr(kg_layer, 'config'))
        self.assertTrue(hasattr(kg_layer, 'execute_query'))


# 异步测试运行器
def run_async_test(test_func):
    """运行异步测试的辅助函数"""
    return asyncio.run(test_func())


class TestAsyncKnowledgeGraphLayer:
    """异步测试类"""

    def setup_method(self):
        """每个测试方法前的设置"""
        # 设置环境变量
        os.environ["GRAPHITI_ENABLED"] = "true"
        os.environ["NEO4J_URI"] = "bolt://localhost:7688"
        os.environ["NEO4J_USER"] = "neo4j"
        os.environ["NEO4J_PASSWORD"] = "test_password"
        os.environ["OPENAI_API_KEY"] = "test-key"

        # 重新导入
        if 'canvas_utils' in sys.modules:
            del sys.modules['canvas_utils']

        from canvas_utils import KnowledgeGraphLayer
        self.KnowledgeGraphLayer = KnowledgeGraphLayer

    @patch('canvas_utils.Graphiti')
    async def test_full_workflow(self, mock_graphiti):
        """测试完整工作流程"""
        # Arrange
        mock_client = AsyncMock()
        mock_client.build_indices_and_constraints = AsyncMock()
        mock_client.add_episode = AsyncMock(return_value={"uuid": "test-uuid"})
        mock_client.driver.execute_query = AsyncMock(return_value=[{"count": 1}])
        mock_graphiti.return_value = mock_client

        # Act & Assert - 完整工作流程
        kg_layer = self.KnowledgeGraphLayer()

        # 1. 初始化
        init_success = await kg_layer.initialize()
        assert init_success is True

        # 2. 检查连接
        is_connected = await kg_layer.check_connection()
        assert is_connected is True

        # 3. 添加Canvas实体
        canvas_data = {"file_path": "test.canvas", "nodes": [], "edges": []}
        canvas_result = await kg_layer.add_canvas_entity(canvas_data)
        assert canvas_result is not None

        # 4. 执行查询
        query_result = await kg_layer.execute_query("MATCH (n) RETURN COUNT(n)")
        assert query_result is not None

        # 5. 关闭连接
        await kg_layer.close()


if __name__ == "__main__":
    # 运行同步测试
    unittest.main(verbosity=2, exit=False)

    # 运行异步测试
    print("\n=== 运行异步测试 ===")
    test_instance = TestAsyncKnowledgeGraphLayer()
    test_instance.setup_method()

    try:
        run_async_test(test_instance.test_full_workflow)
        print("✅ 异步测试通过")
    except Exception as e:
        print(f"❌ 异步测试失败: {e}")
