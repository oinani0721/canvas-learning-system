#!/usr/bin/env python3
"""
Canvas工作流集成测试
Story 8.13: 提升测试覆盖率和系统稳定性

测试Canvas学习系统的完整工作流程，包括：
- Canvas文件操作
- 节点和边的管理
- 颜色流转逻辑
- 错误处理和恢复

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-22
"""

import json
import os
import tempfile
import unittest
from datetime import datetime
from typing import Dict
from unittest.mock import patch

# 尝试导入主要模块
try:
    from error_recovery_advisor import ErrorRecoveryAdvisor
    from system_health_monitor import SystemHealthMonitor

    from canvas_utils import CanvasBusinessLogic, CanvasJSONOperator, CanvasOrchestrator
    CORE_MODULES_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Core modules not available: {e}")
    CORE_MODULES_AVAILABLE = False


@unittest.skipUnless(CORE_MODULES_AVAILABLE, "Core modules not available")
class TestCanvasWorkflowIntegration(unittest.TestCase):
    """Canvas工作流集成测试"""

    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_canvas_path = os.path.join(self.temp_dir, "test_canvas.canvas")
        self.json_operator = CanvasJSONOperator()
        self.business_logic = CanvasBusinessLogic()
        self.orchestrator = CanvasOrchestrator()
        self.error_advisor = ErrorRecoveryAdvisor()
        self.health_monitor = SystemHealthMonitor()

        # 创建测试Canvas数据
        self.test_canvas_data = self._create_test_canvas()

    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_complete_learning_workflow(self):
        """测试完整的学习工作流程"""
        print("Testing complete learning workflow...")

        # Step 1: 创建初始Canvas
        canvas_path = self._create_initial_canvas()
        self.assertTrue(os.path.exists(canvas_path), "Canvas文件应该被创建")

        # Step 2: 添加问题节点
        question_node = self._add_question_node(canvas_path, "测试问题")
        self.assertIsNotNone(question_node, "问题节点应该被添加")

        # Step 3: 添加对应的黄色理解节点
        understanding_node = self._add_understanding_node(canvas_path, question_node["id"])
        self.assertIsNotNone(understanding_node, "理解节点应该被添加")

        # Step 4: 模拟理解填写和评分
        self._fill_understanding(canvas_path, understanding_node["id"], "我的理解内容")
        score_result = self._score_understanding(canvas_path, understanding_node["id"])
        self.assertIsNotNone(score_result, "评分应该被生成")

        # Step 5: 验证颜色流转逻辑
        self._verify_color_flow(canvas_path, question_node["id"], understanding_node["id"])

        # Step 6: 生成检验白板
        review_canvas = self._generate_review_canvas(canvas_path)
        self.assertIsNotNone(review_canvas, "检验白板应该被生成")

        print("Complete learning workflow test passed!")

    def test_error_handling_workflow(self):
        """测试错误处理工作流程"""
        print("Testing error handling workflow...")

        # 测试文件不存在的错误处理
        with self.assertRaises(FileNotFoundError):
            self.json_operator.read_canvas("nonexistent_file.canvas")

        # 测试无效JSON的错误处理
        invalid_canvas_path = os.path.join(self.temp_dir, "invalid.canvas")
        with open(invalid_canvas_path, 'w', encoding='utf-8') as f:
            f.write('{"invalid": json content}')  # 故意的JSON语法错误

        with self.assertRaises(json.JSONDecodeError):
            self.json_operator.read_canvas(invalid_canvas_path)

        # 测试错误恢复建议
        error = FileNotFoundError("No such file or directory")
        context = {"canvas_path": "test.canvas"}
        recovery_advice = self.error_advisor.get_recovery_advice(error, context)
        self.assertIn("recovery_plan", recovery_advice, "应该提供恢复建议")

        print("Error handling workflow test passed!")

    def test_performance_workflow(self):
        """测试性能相关工作流程"""
        print("Testing performance workflow...")

        # 测试大文件处理性能
        large_canvas_path = self._create_large_canvas(1000)  # 1000个节点

        start_time = datetime.now()
        canvas_data = self.json_operator.read_canvas(large_canvas_path)
        end_time = datetime.now()

        processing_time = (end_time - start_time).total_seconds()
        self.assertLess(processing_time, 5.0, "大文件读取应该在5秒内完成")

        # 测试批量节点操作性能
        start_time = datetime.now()
        for i in range(100):
            self.business_logic.add_node(canvas_data, {
                "id": f"perf_test_{i}",
                "type": "text",
                "x": i * 50,
                "y": i * 30,
                "width": 200,
                "height": 100,
                "color": "1",
                "text": f"Performance test node {i}"
            })
        end_time = datetime.now()

        batch_processing_time = (end_time - start_time).total_seconds()
        self.assertLess(batch_processing_time, 2.0, "批量节点操作应该在2秒内完成")

        print("Performance workflow test passed!")

    def test_system_health_monitoring(self):
        """测试系统健康监控"""
        print("Testing system health monitoring...")

        # 模拟系统操作
        self._perform_system_operations()

        # 获取健康状态
        health_status = self.health_monitor.get_system_health()
        self.assertIsNotNone(health_status, "健康状态应该被获取")
        self.assertIn("overall_status", health_status, "应该包含整体状态")
        self.assertIn("components", health_status, "应该包含组件状态")

        # 验证关键组件状态
        components = health_status["components"]
        critical_components = ["canvas_operations", "error_handling", "memory_usage"]
        for component in critical_components:
            self.assertIn(component, components, f"应该包含{component}组件状态")
            self.assertIn(components[component], ["healthy", "warning", "error"],
                         f"{component}状态应该有效")

        print("System health monitoring test passed!")

    def test_agent_integration_workflow(self):
        """测试Agent集成工作流程"""
        print("Testing agent integration workflow...")

        # 创建包含问题节点的Canvas
        canvas_path = self._create_canvas_with_problems()

        # 模拟Agent调用（使用Mock）
        with patch('canvas_orchestrator.call_subagent') as mock_agent:
            mock_agent.return_value = {
                "status": "success",
                "result": {"questions": ["Q1", "Q2", "Q3"]},
                "explanation": "Decomposition successful"
            }

            # 调用基础拆解Agent
            result = self.orchestrator.decompose_problem(
                canvas_path, "test_problem_node_id"
            )

            self.assertIsNotNone(result, "拆解结果应该被返回")
            mock_agent.assert_called_once()

        print("Agent integration workflow test passed!")

    def _create_test_canvas(self) -> Dict:
        """创建测试Canvas数据"""
        return {
            "nodes": [
                {
                    "id": "test_question_1",
                    "type": "text",
                    "x": 100,
                    "y": 100,
                    "width": 200,
                    "height": 100,
                    "color": "1",  # 红色 - 不理解
                    "text": "什么是逆否命题？",
                    "content": "这是一个关于逻辑学的问题"
                }
            ],
            "edges": []
        }

    def _create_initial_canvas(self) -> str:
        """创建初始Canvas文件"""
        self.json_operator.write_canvas(self.test_canvas_path, self.test_canvas_data)
        return self.test_canvas_path

    def _add_question_node(self, canvas_path: str, question_text: str) -> Dict:
        """添加问题节点"""
        canvas_data = self.json_operator.read_canvas(canvas_path)

        question_node = {
            "id": f"question_{len(canvas_data['nodes'])}",
            "type": "text",
            "x": 200,
            "y": 100,
            "width": 250,
            "height": 120,
            "color": "1",  # 红色
            "text": question_text,
            "content": f"问题内容: {question_text}"
        }

        self.business_logic.add_node(canvas_data, question_node)
        self.json_operator.write_canvas(canvas_path, canvas_data)

        return question_node

    def _add_understanding_node(self, canvas_path: str, question_node_id: str) -> Dict:
        """添加理解节点（黄色）"""
        canvas_data = self.json_operator.read_canvas(canvas_path)
        question_node = self.business_logic.find_node_by_id(canvas_data, question_node_id)

        understanding_node = {
            "id": f"understanding_{question_node_id}",
            "type": "text",
            "x": question_node["x"],
            "y": question_node["y"] + question_node["height"] + 30,
            "width": question_node["width"],
            "height": 80,
            "color": "6",  # 黄色 - 个人理解输出区
            "text": "我的理解：",
            "content": ""
        }

        self.business_logic.add_node(canvas_data, understanding_node)

        # 添加连接边
        edge = {
            "id": f"edge_{question_node_id}_{understanding_node['id']}",
            "from": question_node_id,
            "to": understanding_node["id"],
            "color": "6"
        }
        self.business_logic.add_edge(canvas_data, edge)

        self.json_operator.write_canvas(canvas_path, canvas_data)
        return understanding_node

    def _fill_understanding(self, canvas_path: str, understanding_node_id: str, content: str):
        """填写理解内容"""
        canvas_data = self.json_operator.read_canvas(canvas_path)
        understanding_node = self.business_logic.find_node_by_id(canvas_data, understanding_node_id)

        understanding_node["content"] = content
        understanding_node["text"] = f"我的理解：{content[:50]}..."

        self.json_operator.write_canvas(canvas_path, canvas_data)

    def _score_understanding(self, canvas_path: str, understanding_node_id: str) -> Dict:
        """对理解进行评分"""
        canvas_data = self.json_operator.read_canvas(canvas_path)
        understanding_node = self.business_logic.find_node_by_id(canvas_data, understanding_node_id)

        # 模拟评分逻辑
        content = understanding_node.get("content", "")
        score = min(100, max(0, len(content) // 10))  # 简化的评分逻辑

        scoring_result = {
            "node_id": understanding_node_id,
            "score": score,
            "accuracy": min(100, score),
            "imagery": min(100, score // 2),
            "completeness": min(100, len(content) // 5),
            "originality": min(100, score // 3),
            "recommended_color": "2" if score >= 80 else "3" if score >= 60 else "1"
        }

        # 更新节点颜色
        understanding_node["color"] = scoring_result["recommended_color"]
        self.json_operator.write_canvas(canvas_path, canvas_data)

        return scoring_result

    def _verify_color_flow(self, canvas_path: str, question_node_id: str, understanding_node_id: str):
        """验证颜色流转逻辑"""
        canvas_data = self.json_operator.read_canvas(canvas_path)
        understanding_node = self.business_logic.find_node_by_id(canvas_data, understanding_node_id)

        # 验证颜色变化
        self.assertIn(understanding_node["color"], ["1", "2", "3"],
                     "理解节点颜色应该是有效值")

        # 如果是绿色（完全理解），问题节点也应该是绿色
        if understanding_node["color"] == "2":
            question_node = self.business_logic.find_node_by_id(canvas_data, question_node_id)
            # 这里可以添加问题节点颜色同步的逻辑

    def _generate_review_canvas(self, original_canvas_path: str) -> str:
        """生成检验白板"""
        canvas_data = self.json_operator.read_canvas(original_canvas_path)

        # 提取需要检验的节点（红色和紫色）
        verification_nodes = self.business_logic.extract_verification_nodes(canvas_data)

        if not verification_nodes:
            return None

        # 创建检验白板
        review_canvas_path = os.path.join(self.temp_dir, "review_canvas.canvas")
        review_canvas_data = self.business_logic.generate_review_canvas_file(
            original_canvas_path, verification_nodes
        )

        self.json_operator.write_canvas(review_canvas_path, review_canvas_data)
        return review_canvas_path

    def _create_large_canvas(self, node_count: int) -> str:
        """创建大型Canvas用于性能测试"""
        large_canvas_path = os.path.join(self.temp_dir, "large_canvas.canvas")

        large_canvas_data = {
            "nodes": [
                {
                    "id": f"node_{i}",
                    "type": "text",
                    "x": (i % 20) * 100,
                    "y": (i // 20) * 150,
                    "width": 200,
                    "height": 100,
                    "color": str(i % 6 + 1),
                    "text": f"Node {i}",
                    "content": f"Content for node {i}"
                }
                for i in range(node_count)
            ],
            "edges": [
                {
                    "id": f"edge_{i}",
                    "from": f"node_{i}",
                    "to": f"node_{(i + 1) % node_count}",
                    "color": "6"
                }
                for i in range(min(node_count, node_count // 2))
            ]
        }

        self.json_operator.write_canvas(large_canvas_path, large_canvas_data)
        return large_canvas_path

    def _perform_system_operations(self):
        """执行系统操作以测试健康监控"""
        # 模拟各种系统操作
        for i in range(10):
            canvas_path = self._create_initial_canvas()
            self._add_question_node(canvas_path, f"Test question {i}")
            understanding_node = self._add_understanding_node(canvas_path, f"question_{i}")
            self._fill_understanding(canvas_path, understanding_node["id"], f"Test understanding {i}")

            # 记录操作
            self.health_monitor.record_operation("canvas_node_add", {"success": True})
            self.health_monitor.record_operation("canvas_file_write", {"success": True})

    def _create_canvas_with_problems(self) -> str:
        """创建包含问题的Canvas用于Agent测试"""
        canvas_path = os.path.join(self.temp_dir, "agent_test_canvas.canvas")

        canvas_data = {
            "nodes": [
                {
                    "id": "problem_node_1",
                    "type": "text",
                    "x": 100,
                    "y": 100,
                    "width": 300,
                    "height": 150,
                    "color": "1",  # 红色 - 需要拆解
                    "text": "如何理解费曼学习法的核心原理？",
                    "content": "这是一个复杂的概念理解问题"
                }
            ],
            "edges": []
        }

        self.json_operator.write_canvas(canvas_path, canvas_data)
        return canvas_path


class TestCanvasWorkflowEdgeCases(unittest.TestCase):
    """Canvas工作流边界情况测试"""

    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @unittest.skipUnless(CORE_MODULES_AVAILABLE, "Core modules not available")
    def test_empty_canvas_handling(self):
        """测试空Canvas处理"""
        from canvas_utils import CanvasJSONOperator

        json_operator = CanvasJSONOperator()
        empty_canvas_path = os.path.join(self.temp_dir, "empty.canvas")

        # 创建空Canvas
        empty_canvas = {"nodes": [], "edges": []}
        json_operator.write_canvas(empty_canvas_path, empty_canvas)

        # 读取空Canvas应该正常
        canvas_data = json_operator.read_canvas(empty_canvas_path)
        self.assertEqual(canvas_data["nodes"], [])
        self.assertEqual(canvas_data["edges"], [])

    @unittest.skipUnless(CORE_MODULES_AVAILABLE, "Core modules not available")
    def test_corrupted_canvas_recovery(self):
        """测试损坏Canvas的恢复"""
        from error_recovery_advisor import get_recovery_advice

        from canvas_utils import CanvasJSONOperator

        json_operator = CanvasJSONOperator()
        corrupted_canvas_path = os.path.join(self.temp_dir, "corrupted.canvas")

        # 创建损坏的Canvas文件
        with open(corrupted_canvas_path, 'w', encoding='utf-8') as f:
            f.write('{"nodes": [invalid_json}, "edges": []}')

        # 尝试读取应该失败
        with self.assertRaises(json.JSONDecodeError):
            json_operator.read_canvas(corrupted_canvas_path)

        # 获取恢复建议
        error = json.JSONDecodeError("Expecting value", "invalid_json", 10)
        context = {"canvas_path": corrupted_canvas_path}
        recovery_advice = get_recovery_advice(error, context)

        self.assertIn("recovery_plan", recovery_advice)

    @unittest.skipUnless(CORE_MODULES_AVAILABLE, "Core modules not available")
    def test_concurrent_canvas_operations(self):
        """测试并发Canvas操作"""
        import threading

        from canvas_utils import CanvasBusinessLogic, CanvasJSONOperator

        json_operator = CanvasJSONOperator()
        business_logic = CanvasBusinessLogic()

        canvas_path = os.path.join(self.temp_dir, "concurrent.canvas")
        canvas_data = {"nodes": [], "edges": []}
        json_operator.write_canvas(canvas_path, canvas_data)

        results = []
        errors = []

        def add_node_worker(node_id):
            try:
                data = json_operator.read_canvas(canvas_path)
                node = {
                    "id": node_id,
                    "type": "text",
                    "x": 100,
                    "y": 100,
                    "width": 200,
                    "height": 100,
                    "color": "1",
                    "text": f"Node {node_id}"
                }
                business_logic.add_node(data, node)
                json_operator.write_canvas(canvas_path, data)
                results.append(node_id)
            except Exception as e:
                errors.append(str(e))

        # 创建多个线程同时添加节点
        threads = []
        for i in range(5):
            thread = threading.Thread(target=add_node_worker, args=(f"node_{i}",))
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 验证结果
        final_data = json_operator.read_canvas(canvas_path)
        # 注意：由于并发写入可能导致数据竞争，这里我们只验证文件没有损坏
        self.assertIsInstance(final_data, dict)
        self.assertIn("nodes", final_data)


if __name__ == "__main__":
    # 运行集成测试
    unittest.main(verbosity=2)
