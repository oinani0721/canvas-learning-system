"""
Story 10.4: 自动节点生成和连接系统 - 单元测试

测试AutoNodeGenerator及其相关组件的功能

Author: Canvas Learning System Team
Story: 10.4
Date: 2025-10-27
"""

import json
import os
import tempfile
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch
import pytest

# 导入要测试的模块
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auto_node_generator import (
    AutoNodeGenerator,
    NodeIDGenerator,
    NodeConnectionRules,
    NodeContentGenerator,
    IntelligentLayoutOptimizer
)


class TestNodeIDGenerator(unittest.TestCase):
    """测试节点ID生成器"""

    def test_generate_explanation_node_id(self):
        """测试生成解释节点ID"""
        node_id = NodeIDGenerator.generate_explanation_node_id()
        self.assertTrue(node_id.startswith("exp-"))
        self.assertEqual(len(node_id), 12)  # exp- + 8字符

    def test_generate_summary_node_id(self):
        """测试生成总结节点ID"""
        node_id = NodeIDGenerator.generate_summary_node_id()
        self.assertTrue(node_id.startswith("sum-"))
        self.assertEqual(len(node_id), 12)  # sum- + 8字符

    def test_id_uniqueness(self):
        """测试ID唯一性"""
        ids = set()
        for _ in range(100):
            exp_id = NodeIDGenerator.generate_explanation_node_id()
            sum_id = NodeIDGenerator.generate_summary_node_id()
            self.assertNotIn(exp_id, ids)
            self.assertNotIn(sum_id, ids)
            ids.add(exp_id)
            ids.add(sum_id)


class TestNodeConnectionRules(unittest.TestCase):
    """测试节点连接规则"""

    def setUp(self):
        self.rules = NodeConnectionRules()

    def test_create_explanation_connection(self):
        """测试创建解释连接"""
        connection = self.rules.create_connection(
            "node1",
            "node2",
            "explanation"
        )

        self.assertIn("id", connection)
        self.assertEqual(connection["fromNode"], "node1")
        self.assertEqual(connection["toNode"], "node2")
        self.assertEqual(connection["label"], "AI解释")
        self.assertEqual(connection["color"], "#4A90E2")
        self.assertEqual(connection["style"], "dashed")

    def test_create_summary_connection(self):
        """测试创建总结连接"""
        connection = self.rules.create_connection(
            "exp_node",
            "sum_node",
            "summary"
        )

        self.assertIn("id", connection)
        self.assertEqual(connection["fromNode"], "exp_node")
        self.assertEqual(connection["toNode"], "sum_node")
        self.assertEqual(connection["label"], "学习总结")
        self.assertEqual(connection["color"], "#F5A623")
        self.assertEqual(connection["style"], "solid")

    def test_connection_with_context(self):
        """测试带上下文的连接创建"""
        context = {"additional_info": "test"}
        connection = self.rules.create_connection(
            "node1",
            "node2",
            "explanation",
            context
        )
        # 上下文目前不影响连接创建，但为未来扩展保留
        self.assertIsNotNone(connection)


class TestNodeContentGenerator(unittest.TestCase):
    """测试节点内容生成器"""

    def setUp(self):
        self.generator = NodeContentGenerator()

    def test_generate_clarification_content(self):
        """测试生成澄清解释内容"""
        agent_result = {
            "content": "这是一个核心概念的详细解释",
            "key_points": ["要点1", "要点2", "要点3"],
            "examples": ["示例1", "示例2"],
            "confidence": 0.95
        }

        content = self.generator.generate_explanation_content(
            agent_result,
            "clarification-path"
        )

        self.assertIn("深度澄清解释", content)
        self.assertIn("核心概念解析", content)
        self.assertIn("这是一个核心概念的详细解释", content)
        self.assertIn("要点1", content)
        self.assertIn("示例1", content)
        self.assertIn("0.95", content)

    def test_generate_comparison_content(self):
        """测试生成对比分析内容"""
        agent_result = {
            "content": "概念A与概念B的对比表格",
            "key_points": ["区别1", "区别2"],
            "examples": ["场景1", "场景2"],
            "confidence": 0.88
        }

        content = self.generator.generate_explanation_content(
            agent_result,
            "comparison-table"
        )

        self.assertIn("概念对比分析", content)
        self.assertIn("对比表格", content)
        self.assertIn("概念A与概念B的对比表格", content)
        self.assertIn("区别1", content)

    def test_generate_summary_prompt(self):
        """测试生成总结提示"""
        explanation_content = "这是AI生成的详细解释"
        original_understanding = "我原来的理解"
        agent_type = "clarification-path"

        prompt = self.generator.generate_summary_prompt(
            explanation_content,
            original_understanding,
            agent_type
        )

        self.assertIn("学习总结", prompt)
        self.assertIn("核心要点", prompt)
        self.assertIn("个人理解", prompt)
        self.assertIn("疑问之处", prompt)
        self.assertIn("应用思考", prompt)
        self.assertIn("Clarification Path", prompt)  # 转换后的格式

    def test_unknown_agent_type_fallback(self):
        """测试未知Agent类型的回退机制"""
        agent_result = {
            "content": "测试内容",
            "key_points": ["要点"],
            "examples": ["示例"],
            "confidence": 0.75
        }

        content = self.generator.generate_explanation_content(
            agent_result,
            "unknown-agent-type"
        )

        # 应该使用默认的clarification-path模板
        self.assertIn("深度澄清解释", content)

    def test_content_formatting_with_lists(self):
        """测试列表格式化"""
        agent_result = {
            "content": "测试内容",
            "key_points": ["第一个要点", "第二个要点", "第三个要点"],
            "examples": ["第一个示例", "第二个示例"],
            "confidence": 0.85
        }

        content = self.generator.generate_explanation_content(
            agent_result,
            "oral-explanation"
        )

        self.assertIn("• 第一个要点", content)
        self.assertIn("• 第二个要点", content)
        self.assertIn("• 第一个示例", content)


class TestIntelligentLayoutOptimizer(unittest.TestCase):
    """测试智能布局优化器"""

    def setUp(self):
        self.optimizer = IntelligentLayoutOptimizer()

    def test_calculate_optimal_position_explanation(self):
        """测试计算解释节点的最优位置"""
        reference_node = {
            "id": "ref1",
            "x": 100,
            "y": 100,
            "width": 300,
            "height": 200
        }

        position = self.optimizer.calculate_optimal_position(
            reference_node,
            "explanation",
            [],
            0
        )

        # 解释节点应该在参考节点右侧
        self.assertEqual(position[0], 100 + 300 + 50)  # x + width + offset
        self.assertEqual(position[1], 100)  # y保持不变

    def test_calculate_optimal_position_summary(self):
        """测试计算总结节点的最优位置"""
        reference_node = {
            "id": "ref1",
            "x": 100,
            "y": 100,
            "width": 300,
            "height": 200
        }

        position = self.optimizer.calculate_optimal_position(
            reference_node,
            "summary",
            [],
            0
        )

        # 总结节点应该在参考节点下方
        self.assertEqual(position[0], 100 + 50)  # x + offset
        self.assertEqual(position[1], 100 + 200 + 50)  # y + height + spacing

    def test_resolve_overlap_detection(self):
        """测试重叠检测和解决"""
        position = (200, 200)
        existing_positions = {
            (200, 200): "node1",  # 完全重叠
            (500, 500): "node2"   # 不重叠
        }
        new_nodes = []

        final_pos = self.optimizer.resolve_overlap(
            position,
            existing_positions,
            new_nodes
        )

        # 应该向下移动避免重叠
        self.assertGreater(final_pos[1], 200)

    def test_is_overlapping(self):
        """测试矩形重叠判断"""
        # 测试重叠情况
        self.assertTrue(self.optimizer._is_overlapping(
            (0, 0), (50, 50), 100, 100, 100, 100
        ))

        # 测试不重叠情况
        self.assertFalse(self.optimizer._is_overlapping(
            (0, 0), (200, 200), 100, 100, 100, 100
        ))

    def test_align_to_grid(self):
        """测试网格对齐"""
        # 测试已经对齐的位置
        aligned = self.optimizer.align_to_grid((100, 150))
        self.assertEqual(aligned, (100, 150))

        # 测试需要对齐的位置
        aligned = self.optimizer.align_to_grid((123, 167))
        self.assertEqual(aligned, (100, 150))

        # 测试四舍五入 - 125会四舍五入到100，175会四舍五入到200
        aligned = self.optimizer.align_to_grid((125, 175))
        self.assertEqual(aligned, (100, 200))

    def test_optimize_new_nodes_layout(self):
        """测试优化新节点布局"""
        canvas_data = {
            "nodes": [
                {
                    "id": "ref1",
                    "x": 100,
                    "y": 100,
                    "width": 300,
                    "height": 200
                }
            ]
        }

        new_nodes = [
            {
                "id": "exp1",
                "metadata": {"node_type": "explanation"}
            },
            {
                "id": "sum1",
                "metadata": {"node_type": "summary"}
            }
        ]

        reference_nodes = ["ref1"]

        optimized = self.optimizer.optimize_new_nodes_layout(
            canvas_data,
            new_nodes,
            reference_nodes
        )

        self.assertIn("exp1", optimized)
        self.assertIn("sum1", optimized)
        self.assertIsInstance(optimized["exp1"]["x"], int)
        self.assertIsInstance(optimized["exp1"]["y"], int)


class TestAutoNodeGenerator(unittest.TestCase):
    """测试自动节点生成器主类"""

    def setUp(self):
        self.generator = AutoNodeGenerator()
        # 创建临时Canvas文件
        self.temp_dir = tempfile.mkdtemp()
        self.canvas_path = os.path.join(self.temp_dir, "test.canvas")

        # 创建初始Canvas数据
        initial_canvas = {
            "nodes": [
                {
                    "id": "yellow1",
                    "type": "text",
                    "text": "我的理解",
                    "x": 100,
                    "y": 100,
                    "width": 300,
                    "height": 200,
                    "color": "6"
                }
            ],
            "edges": []
        }

        with open(self.canvas_path, 'w', encoding='utf-8') as f:
            json.dump(initial_canvas, f, ensure_ascii=False, indent=2)

    def tearDown(self):
        # 清理临时文件
        if os.path.exists(self.canvas_path):
            os.remove(self.canvas_path)
        os.rmdir(self.temp_dir)

    def test_create_explanation_node(self):
        """测试创建解释节点"""
        agent_result = {
            "agent_type": "clarification-path",
            "content": "这是AI的解释内容",
            "key_points": ["要点1", "要点2"],
            "examples": ["示例1"]
        }

        reference_node = {
            "id": "yellow1",
            "text": "我的理解"
        }

        explanation_node = self.generator.create_explanation_node(
            agent_result,
            reference_node
        )

        self.assertEqual(explanation_node["type"], "text")
        self.assertEqual(explanation_node["color"], "5")  # 蓝色
        self.assertIn("这是AI的解释内容", explanation_node["text"])
        self.assertIn("深度澄清解释", explanation_node["text"])  # 使用实际的标题
        self.assertEqual(explanation_node["metadata"]["node_type"], "ai_explanation")
        self.assertEqual(explanation_node["metadata"]["agent_name"], "clarification-path")

    def test_create_summary_node(self):
        """测试创建总结节点"""
        explanation_node = {
            "id": "exp1",
            "text": "AI的解释内容",
            "metadata": {
                "agent_name": "clarification-path"
            }
        }

        reference_node = {
            "id": "yellow1",
            "text": "我的理解"
        }

        summary_node = self.generator.create_summary_node(
            explanation_node,
            reference_node
        )

        self.assertEqual(summary_node["type"], "text")
        self.assertEqual(summary_node["color"], "6")  # 黄色
        self.assertIn("学习总结", summary_node["text"])
        self.assertIn("核心要点", summary_node["text"])
        self.assertIn("个人理解", summary_node["text"])
        self.assertEqual(summary_node["metadata"]["node_type"], "user_summary")

    @pytest.mark.asyncio
    async def test_generate_nodes_from_agent_results(self):
        """测试从Agent结果生成节点的完整流程"""
        agent_results = [
            {
                "agent_type": "clarification-path",
                "content": "这是第一个AI解释",
                "key_points": ["要点1", "要点2"],
                "examples": ["示例1"],
                "confidence": 0.9
            },
            {
                "agent_type": "comparison-table",
                "content": "这是对比分析",
                "key_points": ["区别1", "区别2"],
                "examples": ["场景1"],
                "confidence": 0.85
            }
        ]

        reference_nodes = ["yellow1"]

        result = await self.generator.generate_nodes_from_agent_results(
            self.canvas_path,
            agent_results,
            reference_nodes
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["added_nodes"], 2)  # 1个解释节点 + 1个总结节点
        self.assertEqual(result["added_edges"], 2)  # 2个连接

        # 验证Canvas文件已更新
        with open(self.canvas_path, 'r', encoding='utf-8') as f:
            updated_canvas = json.load(f)

        self.assertEqual(len(updated_canvas["nodes"]), 3)  # 原来1个 + 新增2个
        self.assertEqual(len(updated_canvas["edges"]), 2)  # 新增2个连接

        # 验证节点颜色
        exp_node = next(n for n in updated_canvas["nodes"] if n["id"].startswith("exp-"))
        sum_node = next(n for n in updated_canvas["nodes"] if n["id"].startswith("sum-"))
        self.assertEqual(exp_node["color"], "5")  # 蓝色
        self.assertEqual(sum_node["color"], "6")  # 黄色

    @pytest.mark.asyncio
    async def test_generate_nodes_with_missing_reference(self):
        """测试处理缺失参考节点的情况"""
        agent_results = [
            {
                "agent_type": "clarification-path",
                "content": "测试内容"
            }
        ]

        reference_nodes = ["nonexistent_node"]

        result = await self.generator.generate_nodes_from_agent_results(
            self.canvas_path,
            agent_results,
            reference_nodes
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["added_nodes"], 0)  # 没有参考节点，不应创建节点
        self.assertEqual(result["added_edges"], 0)

    @pytest.mark.asyncio
    async def test_generate_nodes_large_batch(self):
        """测试大规模节点生成（性能测试）"""
        # 创建20个Agent结果
        agent_results = [
            {
                "agent_type": "clarification-path",
                "content": f"解释内容 {i}",
                "key_points": [f"要点{i}-1", f"要点{i}-2"],
                "examples": [f"示例{i}"],
                "confidence": 0.9
            }
            for i in range(20)
        ]

        # 创建20个参考节点
        initial_nodes = [
            {
                "id": f"yellow{i}",
                "type": "text",
                "text": f"理解{i}",
                "x": 100,
                "y": 100 + i * 300,
                "width": 300,
                "height": 200,
                "color": "6"
            }
            for i in range(20)
        ]

        initial_canvas = {
            "nodes": initial_nodes,
            "edges": []
        }

        with open(self.canvas_path, 'w', encoding='utf-8') as f:
            json.dump(initial_canvas, f, ensure_ascii=False, indent=2)

        reference_nodes = [f"yellow{i}" for i in range(20)]

        import time
        start_time = time.time()

        result = await self.generator.generate_nodes_from_agent_results(
            self.canvas_path,
            agent_results,
            reference_nodes
        )

        end_time = time.time()
        duration = end_time - start_time

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["added_nodes"], 40)  # 20个解释节点 + 20个总结节点
        self.assertEqual(result["added_edges"], 40)  # 40个连接

        # 性能断言：应该在合理时间内完成（比如10秒内）
        self.assertLess(duration, 10, f"生成40个节点耗时过长: {duration}秒")

        # 验证没有重叠（简单的位置唯一性检查）
        with open(self.canvas_path, 'r', encoding='utf-8') as f:
            final_canvas = json.load(f)

        positions = [(n["x"], n["y"]) for n in final_canvas["nodes"]]
        unique_positions = set(positions)
        self.assertEqual(len(positions), len(unique_positions), "存在节点位置重复")


if __name__ == "__main__":
    # 运行所有测试
    unittest.main(verbosity=2)