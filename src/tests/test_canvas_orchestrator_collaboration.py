"""
Canvas Orchestrator协同机制测试
Story 7.3 Task 3 - 实现与canvas-orchestrator协同机制 (AC: 4)

测试CanvasClaudeOrchestratorBridge和canvas_orchestrator_collaboration工具的功能
"""

import asyncio
import json
import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

# 导入pytest
try:
    import pytest
except ImportError:
    pytest = None

# 导入被测试的模块
try:
    from canvas_utils import (
        CanvasClaudeOrchestratorBridge,
        CanvasOrchestrator,
        CLAUDE_CODE_ENABLED
    )
    from claude_canvas_tools import canvas_orchestrator_collaboration
except ImportError as e:
    print(f"警告: 无法导入测试模块 - {e}")
    CLAUDE_CODE_ENABLED = False


class TestCanvasClaudeOrchestratorBridge(unittest.TestCase):
    """测试CanvasClaudeOrchestratorBridge"""

    def setUp(self):
        """测试设置"""
        if not CLAUDE_CODE_ENABLED:
            self.skipTest("Claude Code SDK未安装")

        # 创建测试Canvas文件
        self.test_canvas_data = {
            "nodes": [
                {
                    "id": "red_node_1",
                    "type": "text",
                    "text": "测试红色节点内容",
                    "x": 100,
                    "y": 100,
                    "width": 200,
                    "height": 80,
                    "color": "4"  # 红色
                },
                {
                    "id": "yellow_node_1",
                    "type": "text",
                    "text": "我的理解内容",
                    "x": 100,
                    "y": 250,
                    "width": 200,
                    "height": 80,
                    "color": "6"  # 黄色
                }
            ],
            "edges": [
                {
                    "id": "edge_1",
                    "fromNode": "red_node_1",
                    "toNode": "yellow_node_1"
                }
            ]
        }

        self.temp_canvas = self.create_temp_canvas_file(self.test_canvas_data)
        self.bridge = CanvasClaudeOrchestratorBridge(self.temp_canvas)

    def create_temp_canvas_file(self, canvas_data):
        """创建临时Canvas文件"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.canvas', delete=False, encoding='utf-8')
        json.dump(canvas_data, temp_file, ensure_ascii=False, indent=2)
        temp_file.close()
        return temp_file.name

    def tearDown(self):
        """清理测试文件"""
        if os.path.exists(self.temp_canvas):
            os.unlink(self.temp_canvas)

    def test_bridge_initialization(self):
        """测试桥接器初始化"""
        self.assertIsNotNone(self.bridge)
        self.assertEqual(self.bridge.canvas_path, self.temp_canvas)
        self.assertIsNotNone(self.bridge.orchestrator)
        self.assertIsNotNone(self.bridge.scheduler)
        self.assertIsInstance(self.bridge.task_queue, list)
        self.assertIsInstance(self.bridge.execution_history, list)

    def test_get_available_agents(self):
        """测试获取可用Agent列表"""
        agents = self.bridge.get_available_agents()

        self.assertIsInstance(agents, list)
        self.assertGreater(len(agents), 0)
        self.assertIn("basic-decomposition", agents)
        self.assertIn("scoring-agent", agents)
        self.assertIn("oral-explanation", agents)

    def test_get_execution_history(self):
        """测试获取执行历史"""
        history = self.bridge.get_execution_history()
        self.assertIsInstance(history, list)

        # 测试限制数量
        # 先添加一些历史记录
        self.bridge.execution_history = [
            {"timestamp": datetime.now().isoformat(), "result": {"success": True}}
        ] * 5

        limited_history = self.bridge.get_execution_history(limit=3)
        self.assertEqual(len(limited_history), 3)

    def test_translate_claude_recommendations_to_tasks(self):
        """测试Claude推荐转换为任务"""
        from canvas_utils import AgentRecommendation

        # 创建测试推荐
        recommendations = [
            AgentRecommendation(
                agent_type="basic-decomposition",
                confidence=0.8,
                reason="测试推荐",
                target_nodes=["red_node_1"],
                priority=1,
                estimated_time=15.0
            ),
            AgentRecommendation(
                agent_type="scoring-agent",
                confidence=0.7,
                reason="测试推荐2",
                target_nodes=["yellow_node_1"],
                priority=3,
                estimated_time=10.0
            )
        ]

        tasks = self.bridge._translate_claude_recommendations_to_tasks(
            recommendations, "decompose", ["red_node_1"]
        )

        self.assertIsInstance(tasks, list)
        self.assertGreater(len(tasks), 0)

        # 验证任务结构
        for task in tasks:
            self.assertIn("type", task)
            self.assertIn("agent_type", task)
            self.assertIn("target_nodes", task)
            self.assertIn("confidence", task)
            self.assertIn("reason", task)
            self.assertIn("estimated_time", task)

    def test_mock_basic_decomposition(self):
        """测试模拟基础拆解"""
        questions = self.bridge._mock_basic_decomposition("测试概念内容")
        self.assertIsInstance(questions, list)
        self.assertGreater(len(questions), 0)

    def test_mock_oral_explanation(self):
        """测试模拟口语化解释"""
        explanation = self.bridge._mock_oral_explanation("测试概念内容")
        self.assertIsInstance(explanation, str)
        self.assertGreater(len(explanation), 0)

    def test_generate_workflow_summary(self):
        """测试工作流摘要生成"""
        # 创建成功的工作流结果
        success_result = {
            "success": True,
            "agent_calls": [
                {
                    "execution_time": 2.5
                },
                {
                    "execution_time": 1.8
                }
            ],
            "canvas_updates": [
                {"action": "create_node"},
                {"action": "update_node_color"}
            ]
        }

        summary = self.bridge._generate_workflow_summary(success_result)
        self.assertIn("智能工作流执行成功", summary)
        self.assertIn("2个Agent任务", summary)
        self.assertIn("2个Canvas更新", summary)

        # 创建失败的工作流结果
        failure_result = {
            "success": False,
            "error": "测试错误"
        }

        failure_summary = self.bridge._generate_workflow_summary(failure_result)
        self.assertIn("工作流执行失败", failure_summary)
        self.assertIn("测试错误", failure_summary)


class TestCanvasOrchestratorCollaborationTool(unittest.TestCase):
    """测试canvas_orchestrator_collaboration工具"""

    def setUp(self):
        """测试设置"""
        if not CLAUDE_CODE_ENABLED:
            self.skipTest("Claude Code SDK未安装")

        # 创建测试Canvas文件
        self.test_canvas_data = {
            "nodes": [
                {
                    "id": "test_node",
                    "type": "text",
                    "text": "测试节点",
                    "x": 100,
                    "y": 100,
                    "width": 200,
                    "height": 80,
                    "color": "4"
                }
            ],
            "edges": []
        }

        self.temp_canvas = self.create_temp_canvas_file(self.test_canvas_data)

    def create_temp_canvas_file(self, canvas_data):
        """创建临时Canvas文件"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.canvas', delete=False, encoding='utf-8')
        json.dump(canvas_data, temp_file, ensure_ascii=False, indent=2)
        temp_file.close()
        return temp_file.name

    def tearDown(self):
        """清理测试文件"""
        if os.path.exists(self.temp_canvas):
            os.unlink(self.temp_canvas)

    def test_canvas_orchestrator_collaboration_missing_parameter(self):
        """测试缺少必需参数的情况"""
        async def run_test():
            result = await canvas_orchestrator_collaboration({})
            content = result.get("content", [])
            self.assertGreater(len(content), 0)
            self.assertIn("缺少必需参数", content[0]["text"])

        asyncio.run(run_test())

    def test_canvas_orchestrator_collaboration_file_not_found(self):
        """测试文件不存在的情况"""
        async def run_test():
            result = await canvas_orchestrator_collaboration({
                "canvas_path": "nonexistent.canvas"
            })
            content = result.get("content", [])
            self.assertGreater(len(content), 0)
            self.assertIn("不存在", content[0]["text"])

        asyncio.run(run_test())

    def test_canvas_orchestrator_collaboration_file_not_canvas(self):
        """测试非Canvas文件的情况"""
        async def run_test():
            # 创建非Canvas文件
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
            temp_file.write("Not a canvas file")
            temp_file.close()

            try:
                result = await canvas_orchestrator_collaboration({
                    "canvas_path": temp_file.name
                })

                content = result.get("content", [])
                self.assertGreater(len(content), 0)
                # 这里应该返回关于Canvas格式不支持的信息，或者尝试处理
            finally:
                os.unlink(temp_file.name)

        asyncio.run(run_test())

    def test_canvas_orchestrator_collaboration_basic_params(self):
        """测试基本参数"""
        async def run_test():
            result = await canvas_orchestrator_collaboration({
                "canvas_path": self.temp_canvas,
                "operation": "decompose",
                "user_intent": "测试用户意图"
            })

            content = result.get("content", [])
            self.assertGreater(len(content), 0)
            # 由于需要实际的Claude集成，这里可能返回初始化失败信息
            # 但至少应该有响应内容

        asyncio.run(run_test())

    def test_canvas_orchestrator_collaboration_with_claude_guidance(self):
        """测试带Claude指导的协同"""
        async def run_test():
            result = await canvas_orchestrator_collaboration({
                "canvas_path": self.temp_canvas,
                "operation": "explain",
                "target_nodes": ["test_node"],
                "claude_guidance": "请重点关注基础概念的理解"
            })

            content = result.get("content", [])
            self.assertGreater(len(content), 0)

        asyncio.run(run_test())


class TestCollaborationResultFormatting(unittest.TestCase):
    """测试协同结果格式化"""

    def test_format_collaboration_result_success(self):
        """测试成功结果的格式化"""
        from claude_canvas_tools import _format_collaboration_result

        result = {
            "canvas_path": "/path/to/test.canvas",
            "operation": "decompose",
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "steps_executed": ["claude_analysis_completed", "orchestrator_task_1_completed"],
            "agent_calls": [
                {
                    "step": 1,
                    "agent_type": "basic-decomposition",
                    "target_nodes": ["node1", "node2"],
                    "result": {
                        "success": True,
                        "execution_time": 2.5,
                        "details": "成功创建了2个理解节点"
                    }
                }
            ],
            "canvas_updates": [
                {
                    "action": "create_node",
                    "node_id": "new_node_1",
                    "node_type": "yellow_understanding"
                }
            ],
            "claude_recommendations": [
                {
                    "source": "user_input",
                    "guidance": "重点关注基础概念"
                }
            ],
            "execution_summary": "✅ 智能工作流执行成功\n- 执行了1个Agent任务"
        }

        formatted = _format_collaboration_result(result)

        self.assertIsInstance(formatted, str)
        self.assertIn("Canvas Orchestrator协同执行报告", formatted)
        self.assertIn("✅ 成功", formatted)
        self.assertIn("basic-decomposition", formatted)
        self.assertIn("Canvas更新统计", formatted)

    def test_format_collaboration_result_failure(self):
        """测试失败结果的格式化"""
        from claude_canvas_tools import _format_collaboration_result

        result = {
            "canvas_path": "/path/to/test.canvas",
            "operation": "decompose",
            "success": False,
            "error": "测试错误信息",
            "steps_executed": ["claude_analysis_completed"]
        }

        formatted = _format_collaboration_result(result)

        self.assertIsInstance(formatted, str)
        self.assertIn("❌ 失败", formatted)
        self.assertIn("测试错误信息", formatted)
        self.assertIn("错误详情", formatted)


if __name__ == "__main__":
    # 运行所有测试
    unittest.main(verbosity=2)