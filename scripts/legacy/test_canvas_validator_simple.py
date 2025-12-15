"""
简化的Canvas验证器测试
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import Mock, MagicMock

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 直接导入Canvas验证器模块
from canvas_utils_pkg.canvas_validator import (
    CanvasValidator,
    ValidationResult,
    OperationResult
)

# 导入Canvas操作器
from canvas_utils import CanvasJSONOperator


class TestCanvasValidatorSimple(unittest.TestCase):
    """简化的Canvas验证器测试"""

    def setUp(self):
        """设置测试环境"""
        # 创建模拟的Canvas操作器
        self.mock_canvas_operator = Mock(spec=CanvasJSONOperator)
        self.validator = CanvasValidator(self.mock_canvas_operator)

        # 创建测试Canvas数据
        self.test_canvas_data = {
            "nodes": [
                {
                    "id": "node-1",
                    "type": "text",
                    "x": 100,
                    "y": 100,
                    "width": 200,
                    "height": 100,
                    "color": "1",
                    "text": "Test node 1"
                }
            ],
            "edges": []
        }

        # 配置模拟操作器的行为
        self.mock_canvas_operator.read_canvas.return_value = self.test_canvas_data
        self.mock_canvas_operator.find_node_by_id.side_effect = self._mock_find_node

    def _mock_find_node(self, canvas_data, node_id):
        """模拟查找节点"""
        for node in canvas_data.get("nodes", []):
            if node["id"] == node_id:
                return node
        return None

    def test_validate_valid_node(self):
        """测试有效节点验证"""
        node_data = {
            "id": "new-node",
            "type": "text",
            "x": 300,
            "y": 300,
            "width": 200,
            "height": 100,
            "color": "6",
            "text": "New node"
        }

        result = self.validator.validate_operation("add_node", node_data, "test.canvas")

        self.assertTrue(result.success)
        self.assertEqual(result.message, "Node validation passed")

    def test_validate_node_missing_field(self):
        """测试缺少字段的节点验证"""
        node_data = {
            "type": "text",
            "x": 300,
            "y": 300,
            # 缺少 id, width, height, color
        }

        result = self.validator.validate_operation("add_node", node_data, "test.canvas")

        self.assertFalse(result.success)
        self.assertIn("Missing required field", result.error)

    def test_validate_node_invalid_color(self):
        """测试无效颜色验证"""
        node_data = {
            "id": "new-node",
            "type": "text",
            "x": 300,
            "y": 300,
            "width": 200,
            "height": 100,
            "color": "9"  # 无效颜色
        }

        result = self.validator.validate_operation("add_node", node_data, "test.canvas")

        self.assertFalse(result.success)
        self.assertIn("Invalid color", result.error)

    def test_validate_valid_edge(self):
        """测试有效边验证"""
        edge_data = {
            "id": "edge-1",
            "fromNode": "node-1",
            "toNode": "node-2",
            "color": "6"
        }

        # 模拟两个节点都存在
        def mock_find_two_nodes(canvas_data, node_id):
            if node_id in ["node-1", "node-2"]:
                return {"id": node_id, "type": "text"}
            return None

        self.mock_canvas_operator.find_node_by_id.side_effect = mock_find_two_nodes

        result = self.validator.validate_operation("add_edge", edge_data, "test.canvas")

        self.assertTrue(result.success)
        self.assertEqual(result.message, "Edge validation passed")

    def test_validate_edge_missing_field(self):
        """测试缺少字段的边验证"""
        edge_data = {
            "fromNode": "node-1",
            # 缺少 toNode, id, color
        }

        result = self.validator.validate_operation("add_edge", edge_data, "test.canvas")

        self.assertFalse(result.success)
        self.assertIn("Missing required field", result.error)

    def test_validation_stats(self):
        """测试验证统计"""
        # 执行一些验证
        self.validator.validate_operation("add_node", {
            "id": "test1",
            "type": "text",
            "x": 100,
            "y": 100,
            "width": 200,
            "height": 100,
            "color": "6"
        }, "test.canvas")

        # 执行一个会失败的验证（无效颜色）
        self.validator.validate_operation("add_node", {
            "id": "test2",
            "type": "text",
            "x": 200,
            "y": 200,
            "width": 200,
            "height": 100,
            "color": "9"  # 无效颜色
        }, "test.canvas")

        stats = self.validator.get_validation_stats()

        self.assertEqual(stats["total_validations"], 2)
        self.assertEqual(stats["successful_validations"], 1)
        self.assertEqual(stats["failed_validations"], 1)
        self.assertEqual(stats["success_rate"], 50.0)

    def test_reset_stats(self):
        """测试重置统计"""
        # 执行验证操作
        self.validator.validate_operation("add_node", {
            "id": "test1",
            "type": "text",
            "x": 100,
            "y": 100,
            "width": 200,
            "height": 100,
            "color": "6"
        }, "test.canvas")

        # 重置统计
        self.validator.reset_stats()

        stats = self.validator.get_validation_stats()
        self.assertEqual(stats["total_validations"], 0)
        self.assertEqual(stats["successful_validations"], 0)
        self.assertEqual(stats["failed_validations"], 0)


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)