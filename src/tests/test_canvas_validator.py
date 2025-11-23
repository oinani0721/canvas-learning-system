"""
Canvas验证器单元测试 - Canvas Learning System v2.0

测试CanvasValidator的所有功能：
- 节点创建验证
- 边创建验证
- 批量操作验证
- 自动修复机制
- 验证报告生成

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-10-28
"""

import json
import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# 导入被测试的模块 - 直接导入避免canvas_utils包冲突
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 添加canvas_utils目录到path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "canvas_utils"))

from canvas_validator import (
    CanvasValidator,
    ValidationResult,
    CanvasUpdateResult,
    ValidationReport,
    OperationResult
)

# 导入Canvas操作器 (从主canvas_utils.py文件)
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 直接导入canvas_utils.py而不是包
import importlib.util
spec = importlib.util.spec_from_file_location("canvas_utils_module",
                                             os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                                        "canvas_utils.py"))
canvas_utils_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(canvas_utils_module)
CanvasJSONOperator = canvas_utils_module.CanvasJSONOperator


class TestValidationResult(unittest.TestCase):
    """测试ValidationResult数据类"""

    def test_validation_result_creation(self):
        """测试验证结果创建"""
        result = ValidationResult(
            success=True,
            message="Validation passed",
            operation_type="add_node"
        )

        self.assertTrue(result.success)
        self.assertEqual(result.message, "Validation passed")
        self.assertEqual(result.operation_type, "add_node")
        self.assertIsInstance(result.timestamp, datetime)

    def test_validation_result_with_error(self):
        """测试带错误的验证结果"""
        result = ValidationResult(
            success=False,
            error="Invalid color",
            details={"color": "9"},
            operation_type="add_node"
        )

        self.assertFalse(result.success)
        self.assertEqual(result.error, "Invalid color")
        self.assertEqual(result.details["color"], "9")


class TestOperationResult(unittest.TestCase):
    """测试OperationResult数据类"""

    def test_operation_result_creation(self):
        """测试操作结果创建"""
        result = OperationResult(
            type="add_node",
            node_id="test-123",
            success=True
        )

        self.assertEqual(result.type, "add_node")
        self.assertEqual(result.node_id, "test-123")
        self.assertTrue(result.success)
        self.assertEqual(result.retry_count, 0)
        self.assertIsInstance(result.timestamp, datetime)

    def test_operation_result_retry(self):
        """测试操作结果重试计数"""
        result = OperationResult(
            type="add_edge",
            edge_id="edge-456",
            success=False,
            retry_count=2
        )

        self.assertEqual(result.type, "add_edge")
        self.assertEqual(result.edge_id, "edge-456")
        self.assertFalse(result.success)
        self.assertEqual(result.retry_count, 2)


class TestCanvasUpdateResult(unittest.TestCase):
    """测试CanvasUpdateResult数据类"""

    def test_successful_update(self):
        """测试成功的更新"""
        result = CanvasUpdateResult(
            nodes_before=10,
            nodes_after=12,
            edges_before=5,
            edges_after=6,
            expected_nodes=2,
            expected_edges=1
        )

        self.assertTrue(result.success())
        self.assertEqual(result.nodes_after - result.nodes_before, 2)
        self.assertEqual(result.edges_after - result.edges_before, 1)

    def test_failed_update(self):
        """测试失败的更新"""
        result = CanvasUpdateResult(
            nodes_before=10,
            nodes_after=11,  # 只增加了1个，但期望2个
            edges_before=5,
            edges_after=6,
            expected_nodes=2,
            expected_edges=1
        )

        self.assertFalse(result.success())

    def test_get_summary(self):
        """测试获取摘要"""
        result = CanvasUpdateResult(
            nodes_before=10,
            nodes_after=12,
            edges_before=5,
            edges_after=6,
            expected_nodes=2,
            expected_edges=1,
            repair_attempts=1
        )

        summary = result.get_summary()
        self.assertTrue(summary["success"])
        self.assertEqual(summary["nodes_added"], 2)
        self.assertEqual(summary["edges_added"], 1)
        self.assertEqual(summary["repair_attempts"], 1)


class TestCanvasValidator(unittest.TestCase):
    """测试CanvasValidator类"""

    def setUp(self):
        """设置测试环境"""
        # 创建模拟的Canvas操作器
        self.mock_canvas_operator = Mock(spec=CanvasJSONOperator)
        self.validator = CanvasValidator(self.mock_canvas_operator)

        # 创建临时目录用于测试
        self.temp_dir = tempfile.mkdtemp()
        self.test_canvas_path = os.path.join(self.temp_dir, "test.canvas")

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
                },
                {
                    "id": "node-2",
                    "type": "text",
                    "x": 400,
                    "y": 100,
                    "width": 200,
                    "height": 100,
                    "color": "2",
                    "text": "Test node 2"
                }
            ],
            "edges": [
                {
                    "id": "edge-1",
                    "fromNode": "node-1",
                    "toNode": "node-2",
                    "color": "6"
                }
            ]
        }

        # 写入测试Canvas文件
        with open(self.test_canvas_path, 'w', encoding='utf-8') as f:
            json.dump(self.test_canvas_data, f, indent=2)

        # 配置模拟操作器的行为
        self.mock_canvas_operator.read_canvas.return_value = self.test_canvas_data
        self.mock_canvas_operator.find_node_by_id.side_effect = self._mock_find_node

    def tearDown(self):
        """清理测试环境"""
        # 删除临时文件
        if os.path.exists(self.test_canvas_path):
            os.remove(self.test_canvas_path)
        os.rmdir(self.temp_dir)

    def _mock_find_node(self, canvas_data, node_id):
        """模拟查找节点"""
        for node in canvas_data.get("nodes", []):
            if node["id"] == node_id:
                return node
        return None

    def test_validator_initialization(self):
        """测试验证器初始化"""
        self.assertIsNotNone(self.validator.validation_rules)
        self.assertIn("node_creation", self.validator.validation_rules)
        self.assertIn("edge_creation", self.validator.validation_rules)
        self.assertEqual(self.validator.retry_config["max_retries"], 3)
        self.assertEqual(self.validator.validation_stats["total_validations"], 0)

    def test_validate_valid_node_creation(self):
        """测试有效节点创建验证"""
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

        result = self.validator.validate_operation("add_node", node_data, self.test_canvas_path)

        self.assertTrue(result.success)
        self.assertEqual(result.message, "Node validation passed")
        self.assertEqual(result.operation_type, "add_node")

    def test_validate_node_missing_required_field(self):
        """测试缺少必需字段的节点验证"""
        node_data = {
            "type": "text",
            "x": 300,
            "y": 300,
            # 缺少 id, width, height, color
        }

        result = self.validator.validate_operation("add_node", node_data, self.test_canvas_path)

        self.assertFalse(result.success)
        self.assertIn("Missing required field", result.error)
        self.assertEqual(result.operation_type, "add_node")

    def test_validate_node_invalid_type(self):
        """测试无效节点类型验证"""
        node_data = {
            "id": "new-node",
            "type": "invalid_type",
            "x": 300,
            "y": 300,
            "width": 200,
            "height": 100,
            "color": "6"
        }

        result = self.validator.validate_operation("add_node", node_data, self.test_canvas_path)

        self.assertFalse(result.success)
        self.assertIn("Invalid node type", result.error)

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

        result = self.validator.validate_operation("add_node", node_data, self.test_canvas_path)

        self.assertFalse(result.success)
        self.assertIn("Invalid color", result.error)

    def test_validate_node_already_exists(self):
        """测试节点已存在验证"""
        node_data = {
            "id": "node-1",  # 已存在的节点ID
            "type": "text",
            "x": 300,
            "y": 300,
            "width": 200,
            "height": 100,
            "color": "6"
        }

        result = self.validator.validate_operation("add_node", node_data, self.test_canvas_path)

        self.assertFalse(result.success)
        self.assertIn("Node already exists", result.error)

    def test_validate_node_invalid_position(self):
        """测试无效位置验证"""
        node_data = {
            "id": "new-node",
            "type": "text",
            "x": 50000,  # 超出边界
            "y": 300,
            "width": 200,
            "height": 100,
            "color": "6"
        }

        result = self.validator.validate_operation("add_node", node_data, self.test_canvas_path)

        self.assertFalse(result.success)
        self.assertIn("Invalid position or size", result.error)

    def test_validate_valid_edge_creation(self):
        """测试有效边创建验证"""
        edge_data = {
            "id": "edge-2",
            "fromNode": "node-1",
            "toNode": "node-2",
            "color": "6"
        }

        result = self.validator.validate_operation("add_edge", edge_data, self.test_canvas_path)

        self.assertTrue(result.success)
        self.assertEqual(result.message, "Edge validation passed")
        self.assertEqual(result.operation_type, "add_edge")

    def test_validate_edge_missing_required_field(self):
        """测试缺少必需字段的边验证"""
        edge_data = {
            "fromNode": "node-1",
            # 缺少 toNode, id, color
        }

        result = self.validator.validate_operation("add_edge", edge_data, self.test_canvas_path)

        self.assertFalse(result.success)
        self.assertIn("Missing required field", result.error)

    def test_validate_edge_source_node_not_found(self):
        """测试源节点不存在验证"""
        edge_data = {
            "id": "edge-3",
            "fromNode": "nonexistent-node",
            "toNode": "node-2",
            "color": "6"
        }

        result = self.validator.validate_operation("add_edge", edge_data, self.test_canvas_path)

        self.assertFalse(result.success)
        self.assertIn("Source node not found", result.error)

    def test_validate_edge_target_node_not_found(self):
        """测试目标节点不存在验证"""
        edge_data = {
            "id": "edge-3",
            "fromNode": "node-1",
            "toNode": "nonexistent-node",
            "color": "6"
        }

        result = self.validator.validate_operation("add_edge", edge_data, self.test_canvas_path)

        self.assertFalse(result.success)
        self.assertIn("Target node not found", result.error)

    def test_validate_edge_self_loop(self):
        """测试自循环验证"""
        edge_data = {
            "id": "edge-self",
            "fromNode": "node-1",
            "toNode": "node-1",  # 自循环
            "color": "6"
        }

        result = self.validator.validate_operation("add_edge", edge_data, self.test_canvas_path)

        self.assertFalse(result.success)
        self.assertIn("Self-loops are not allowed", result.error)

    def test_validate_valid_batch_operation(self):
        """测试有效批量操作验证"""
        batch_data = {
            "operations": [
                {
                    "type": "add_node",
                    "data": {
                        "id": "batch-node-1",
                        "type": "text",
                        "x": 100,
                        "y": 400,
                        "width": 200,
                        "height": 100,
                        "color": "6"
                    }
                },
                {
                    "type": "add_edge",
                    "data": {
                        "id": "batch-edge-1",
                        "fromNode": "batch-node-1",
                        "toNode": "node-1",
                        "color": "6"
                    }
                }
            ]
        }

        # 需要模拟新节点不存在
        def mock_find_node_new(canvas_data, node_id):
            if node_id.startswith("batch-"):
                return None
            return self._mock_find_node(canvas_data, node_id)

        self.mock_canvas_operator.find_node_by_id.side_effect = mock_find_node_new

        result = self.validator.validate_operation("batch_operation", batch_data, self.test_canvas_path)

        self.assertTrue(result.success)
        self.assertIn("Batch validation passed", result.message)

    def test_validate_batch_too_large(self):
        """测试批量操作过大验证"""
        # 创建超过最大批量大小的操作列表
        operations = []
        for i in range(150):  # 超过100的限制
            operations.append({
                "type": "add_node",
                "data": {
                    "id": f"batch-node-{i}",
                    "type": "text",
                    "x": 100,
                    "y": 100,
                    "width": 200,
                    "height": 100,
                    "color": "6"
                }
            })

        batch_data = {"operations": operations}

        result = self.validator.validate_operation("batch_operation", batch_data, self.test_canvas_path)

        self.assertFalse(result.success)
        self.assertIn("Batch size too large", result.error)

    def test_validate_node_update(self):
        """测试节点更新验证"""
        update_data = {
            "id": "node-1",
            "color": "2"  # 更新颜色
        }

        result = self.validator.validate_operation("update_node", update_data, self.test_canvas_path)

        self.assertTrue(result.success)
        self.assertEqual(result.message, "Node update validation passed")

    def test_validate_node_update_not_found(self):
        """测试更新不存在的节点"""
        update_data = {
            "id": "nonexistent-node",
            "color": "2"
        }

        result = self.validator.validate_operation("update_node", update_data, self.test_canvas_path)

        self.assertFalse(result.success)
        self.assertIn("Node not found", result.error)

    def test_validate_node_deletion(self):
        """测试节点删除验证"""
        delete_data = {
            "id": "node-1"
        }

        result = self.validator.validate_operation("delete_node", delete_data, self.test_canvas_path)

        self.assertTrue(result.success)
        self.assertEqual(result.message, "Node deletion validation passed")

    def test_validate_unknown_operation(self):
        """测试未知操作类型验证"""
        result = self.validator.validate_operation("unknown_op", {}, self.test_canvas_path)

        self.assertFalse(result.success)
        self.assertIn("Unknown operation", result.error)

    def test_ensure_canvas_update_success(self):
        """测试确保Canvas更新成功"""
        operations = [
            OperationResult(type="add_node", node_id="new-node", success=True),
            OperationResult(type="add_edge", edge_id="new-edge", success=True)
        ]

        # 模拟更新后的Canvas数据
        updated_canvas = self.test_canvas_data.copy()
        updated_canvas["nodes"].append({
            "id": "new-node",
            "type": "text",
            "x": 100,
            "y": 400,
            "width": 200,
            "height": 100,
            "color": "6"
        })
        updated_canvas["edges"].append({
            "id": "new-edge",
            "fromNode": "new-node",
            "toNode": "node-1",
            "color": "6"
        })

        # 配置模拟返回更新后的数据
        def mock_read_updated(path):
            if path == self.test_canvas_path:
                return updated_canvas
            return self.test_canvas_data

        self.mock_canvas_operator.read_canvas.side_effect = mock_read_updated

        result = self.validator.ensure_canvas_update(operations, self.test_canvas_path)

        self.assertTrue(result.success())
        self.assertEqual(result.nodes_after - result.nodes_before, 1)
        self.assertEqual(result.edges_after - result.edges_before, 1)

    def test_generate_validation_report(self):
        """测试生成验证报告"""
        operations = [
            OperationResult(type="add_node", node_id="node-1", success=True),
            OperationResult(type="add_edge", edge_id="edge-1", success=True),
            OperationResult(type="add_node", node_id="node-2", success=False, error="Test error")
        ]

        report = self.validator.generate_validation_report(operations, self.test_canvas_path)

        self.assertEqual(report.canvas_path, self.test_canvas_path)
        self.assertEqual(report.total_operations, 3)
        self.assertEqual(report.successful_operations, 2)
        self.assertEqual(report.failed_operations, 1)
        self.assertIsInstance(report.timestamp, datetime)

        # 检查按类型统计
        self.assertIn("add_node", report.operations_by_type)
        self.assertIn("add_edge", report.operations_by_type)
        self.assertEqual(report.operations_by_type["add_node"]["total"], 2)
        self.assertEqual(report.operations_by_type["add_node"]["success"], 1)
        self.assertEqual(report.operations_by_type["add_edge"]["total"], 1)
        self.assertEqual(report.operations_by_type["add_edge"]["success"], 1)

    def test_save_validation_report(self):
        """测试保存验证报告"""
        operations = [
            OperationResult(type="add_node", node_id="node-1", success=True)
        ]

        report = self.validator.generate_validation_report(operations, self.test_canvas_path)

        # 保存报告
        report_path = self.validator.save_validation_report(report)

        # 验证文件存在
        self.assertTrue(os.path.exists(report_path))

        # 验证文件内容
        with open(report_path, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)

        self.assertEqual(saved_data["canvas_path"], self.test_canvas_path)
        self.assertEqual(saved_data["total_operations"], 1)
        self.assertEqual(saved_data["successful_operations"], 1)

        # 清理
        os.remove(report_path)

    def test_get_validation_stats(self):
        """测试获取验证统计"""
        # 执行一些验证操作
        self.validator.validate_operation("add_node", {
            "id": "test1",
            "type": "text",
            "x": 100,
            "y": 100,
            "width": 200,
            "height": 100,
            "color": "6"
        }, self.test_canvas_path)

        self.validator.validate_operation("add_node", {
            "id": "node-1",  # 已存在，会失败
            "type": "text",
            "x": 100,
            "y": 100,
            "width": 200,
            "height": 100,
            "color": "6"
        }, self.test_canvas_path)

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
        }, self.test_canvas_path)

        # 重置统计
        self.validator.reset_stats()

        stats = self.validator.get_validation_stats()
        self.assertEqual(stats["total_validations"], 0)
        self.assertEqual(stats["successful_validations"], 0)
        self.assertEqual(stats["failed_validations"], 0)


class TestValidationReport(unittest.TestCase):
    """测试ValidationReport类"""

    def test_generate_summary(self):
        """测试生成报告摘要"""
        operations = [
            OperationResult(type="add_node", success=True),
            OperationResult(type="add_node", success=True),
            OperationResult(type="add_edge", success=False)
        ]

        report = ValidationReport(
            canvas_path="test.canvas",
            timestamp=datetime.now(),
            operations=operations
        )

        report.total_operations = len(operations)
        report.successful_operations = 2
        report.failed_operations = 1
        report.operations_by_type = {
            "add_node": {"total": 2, "success": 2},
            "add_edge": {"total": 1, "success": 0}
        }

        summary = report.generate_summary()

        self.assertEqual(summary["total_operations"], 3)
        self.assertEqual(summary["success_rate"], 66.67)
        self.assertEqual(summary["successful_operations"], 2)
        self.assertEqual(summary["failed_operations"], 1)


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)