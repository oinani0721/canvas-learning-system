"""
模型兼容性适配器集成测试

测试模型适配器与Canvas系统的集成

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-10-28
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from canvas_utils import CanvasBusinessLogic, CanvasJSONOperator


class TestModelAdapterIntegration(unittest.TestCase):
    """测试模型适配器与Canvas系统集成"""

    def setUp(self):
        # 创建临时测试Canvas文件
        self.test_canvas_data = {
            "nodes": [
                {
                    "id": "material-1",
                    "type": "text",
                    "text": "逆否命题的定义和性质",
                    "x": 100,
                    "y": 100,
                    "width": 400,
                    "height": 300,
                    "color": "1"  # 红色
                },
                {
                    "id": "question-1",
                    "type": "text",
                    "text": "什么是逆否命题？",
                    "x": 600,
                    "y": 100,
                    "width": 350,
                    "height": 150,
                    "color": "1"  # 红色
                },
                {
                    "id": "yellow-1",
                    "type": "text",
                    "text": "我认为逆否命题是原命题的逻辑等价形式，即将条件和结论都否定并交换位置",
                    "x": 600,
                    "y": 280,
                    "width": 350,
                    "height": 150,
                    "color": "6"  # 黄色
                },
                {
                    "id": "material-2",
                    "type": "text",
                    "text": "逻辑蕴含的概念",
                    "x": 100,
                    "y": 500,
                    "width": 400,
                    "height": 300,
                    "color": "3"  # 紫色
                },
                {
                    "id": "yellow-2",
                    "type": "text",
                    "text": "My understanding: A implies B means if A is true, B must be true",
                    "x": 600,
                    "y": 500,
                    "width": 350,
                    "height": 150,
                    "color": "6"  # 黄色
                },
                {
                    "id": "empty-yellow",
                    "type": "text",
                    "text": "",
                    "x": 1000,
                    "y": 100,
                    "width": 350,
                    "height": 150,
                    "color": "6"  # 黄色但为空
                }
            ],
            "edges": [
                {
                    "id": "edge-1",
                    "fromNode": "material-1",
                    "toNode": "question-1",
                    "fromSide": "right",
                    "toSide": "left"
                },
                {
                    "id": "edge-2",
                    "fromNode": "question-1",
                    "toNode": "yellow-1",
                    "fromSide": "bottom",
                    "toSide": "top"
                },
                {
                    "id": "edge-3",
                    "fromNode": "material-2",
                    "toNode": "yellow-2",
                    "fromSide": "right",
                    "toSide": "left"
                }
            ]
        }

        # 创建临时文件
        self.temp_file = tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.canvas',
            delete=False,
            encoding='utf-8'
        )
        json.dump(self.test_canvas_data, self.temp_file, ensure_ascii=False, indent=2)
        self.temp_file.close()

    def tearDown(self):
        # 清理临时文件
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)

    def test_canvas_business_logic_integration(self):
        """测试与CanvasBusinessLogic的集成"""
        # 初始化业务逻辑层
        logic = CanvasBusinessLogic(self.temp_file.name)

        # 验证模型适配器已初始化
        self.assertIsNotNone(logic.model_adapter)
        self.assertIsInstance(logic.model_adapter, object)

        # 测试使用模型适配器的黄色节点检测
        result = logic.detect_yellow_nodes_enhanced()

        self.assertIsNotNone(result)
        self.assertGreater(len(result.nodes), 0)
        self.assertIn("confidence_score", result.__dict__)
        self.assertIn("detection_method", result.__dict__)

    def test_extract_verification_nodes_with_adapter(self):
        """测试使用适配器的验证节点提取"""
        logic = CanvasBusinessLogic(self.temp_file.name)

        # 提取验证节点
        result = logic.extract_verification_nodes()

        # 验证结果结构
        self.assertIn("red_nodes", result)
        self.assertIn("purple_nodes", result)
        self.assertIn("stats", result)

        # 验证检测到的节点
        self.assertGreater(len(result["red_nodes"]), 0)
        self.assertGreater(len(result["purple_nodes"]), 0)

        # 验证关联的黄色节点被正确检测
        for node in result["red_nodes"]:
            self.assertIn("related_yellow", node)
            # 应该检测到黄色的理解内容
            if node["id"] == "question-1":
                self.assertGreater(len(node["related_yellow"]), 0)

    def test_process_with_model_adapter(self):
        """测试使用模型适配器处理操作"""
        logic = CanvasBusinessLogic(self.temp_file.name)

        # 模拟AI响应
        mock_response = {"model": "opus-4.1"}

        # 使用模型适配器处理
        result = logic.process_with_model_adapter(
            "intelligent_parallel",
            self.temp_file.name,
            response=mock_response,
            options={"optimize": True}
        )

        self.assertIsInstance(result, dict)
        self.assertIn("status", result)

    def test_get_model_adapter_info(self):
        """测试获取模型适配器信息"""
        logic = CanvasBusinessLogic(self.temp_file.name)

        info = logic.get_model_adapter_info()

        self.assertIn("available", info)
        if info["available"]:
            self.assertIn("current_model", info)
            self.assertIn("supported_models", info)
            self.assertIn("stats", info)

    def test_fallback_without_adapter(self):
        """测试没有适配器时的降级处理"""
        # 临时禁用适配器
        with patch('canvas_utils.MODEL_ADAPTER_AVAILABLE', False):
            logic = CanvasBusinessLogic(self.temp_file.name)

            # 应该降级到基础处理
            result = logic.detect_yellow_nodes_enhanced()

            self.assertIsNotNone(result)
            self.assertEqual(result.detection_method, "basic_fallback")

    def test_canvas_json_operator_with_adapter(self):
        """测试CanvasJSONOperator与适配器的协同"""
        # 读取Canvas数据
        canvas_data = CanvasJSONOperator.read_canvas(self.temp_file.name)

        # 使用适配器检测黄色节点
        if hasattr(CanvasBusinessLogic(self.temp_file.name), 'model_adapter'):
            adapter = CanvasBusinessLogic(self.temp_file.name).model_adapter
            if adapter:
                detection_result = adapter.detect_yellow_nodes(canvas_data)

                # 验证检测结果
                self.assertIsInstance(detection_result.nodes, list)
                self.assertGreater(len(detection_result.nodes), 0)

    def test_model_switching(self):
        """测试模型切换场景"""
        logic = CanvasBusinessLogic(self.temp_file.name)

        # 模拟不同的模型响应
        responses = [
            {"model": "opus-4.1"},
            {"model": "glm-4.6"},
            {"model": "sonnet-3.5"}
        ]

        for response in responses:
            result = logic.process_with_model_adapter(
                "test_operation",
                response=response
            )
            self.assertIsNotNone(result)

    def test_performance_with_large_canvas(self):
        """测试大型Canvas的性能"""
        # 创建包含大量节点的Canvas
        large_canvas = {
            "nodes": [],
            "edges": []
        }

        # 添加1000个节点
        for i in range(1000):
            node = {
                "id": f"node-{i}",
                "type": "text",
                "text": f"这是第{i}个节点的理解内容，I think this is important",
                "x": (i % 10) * 500,
                "y": (i // 10) * 400,
                "width": 400,
                "height": 200,
                "color": "6" if i % 2 == 0 else "1"
            }
            large_canvas["nodes"].append(node)

        # 保存大型Canvas
        large_temp_file = tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.canvas',
            delete=False,
            encoding='utf-8'
        )
        json.dump(large_canvas, large_temp_file, ensure_ascii=False)
        large_temp_file.close()

        try:
            import time
            start_time = time.time()

            # 测试处理性能
            logic = CanvasBusinessLogic(large_temp_file.name)
            result = logic.detect_yellow_nodes_enhanced()

            end_time = time.time()
            processing_time = end_time - start_time

            # 验证性能要求（< 1秒）
            self.assertLess(
                processing_time,
                1.0,
                f"处理大型Canvas耗时 {processing_time:.2f}s，超过1秒限制"
            )

            # 验证检测结果
            self.assertGreater(len(result.nodes), 0)

        finally:
            # 清理大型文件
            if os.path.exists(large_temp_file.name):
                os.unlink(large_temp_file.name)

    def test_edge_cases(self):
        """测试边缘情况"""
        # 测试空Canvas
        empty_canvas = {"nodes": [], "edges": []}
        empty_temp = tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.canvas',
            delete=False,
            encoding='utf-8'
        )
        json.dump(empty_canvas, empty_temp)
        empty_temp.close()

        try:
            logic = CanvasBusinessLogic(empty_temp.name)
            result = logic.detect_yellow_nodes_enhanced()
            self.assertEqual(len(result.nodes), 0)
        finally:
            if os.path.exists(empty_temp.name):
                os.unlink(empty_temp.name)

        # 测试只有非黄色节点的Canvas
        no_yellow_canvas = {
            "nodes": [
                {
                    "id": "red-1",
                    "type": "text",
                    "text": "红色节点",
                    "color": "1"
                },
                {
                    "id": "green-1",
                    "type": "text",
                    "text": "绿色节点",
                    "color": "2"
                }
            ],
            "edges": []
        }

        no_yellow_temp = tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.canvas',
            delete=False,
            encoding='utf-8'
        )
        json.dump(no_yellow_canvas, no_yellow_temp)
        no_yellow_temp.close()

        try:
            logic = CanvasBusinessLogic(no_yellow_temp.name)
            result = logic.detect_yellow_nodes_enhanced()
            self.assertEqual(len(result.nodes), 0)
        finally:
            if os.path.exists(no_yellow_temp.name):
                os.unlink(no_yellow_temp.name)


if __name__ == "__main__":
    # 运行集成测试
    unittest.main(verbosity=2)
