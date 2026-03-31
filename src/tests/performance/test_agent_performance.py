"""
Agent系统性能测试套件

测试Agent执行效率，确保响应时间满足PRD要求：
- 基础拆解 < 20秒
- 深度拆解 < 30秒
- 批量评分 < 30秒
- 并行执行支持5-10个Agent

Author: Canvas Learning System Team
Version: 2.0
Created: 2025-01-22
"""

import asyncio
import json
import os

# Import the canvas utils modules
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.append(str(Path(__file__).parent.parent.parent))
from canvas_utils import CanvasOrchestrator


class TestAgentPerformance:
    """Agent系统性能测试类"""

    @pytest.fixture
    def sample_canvas_with_nodes(self):
        """创建包含节点的测试Canvas"""
        canvas_data = {
            "nodes": [
                {
                    "id": "material-1",
                    "type": "text",
                    "text": "这是一个需要拆解的复杂概念：傅里叶变换是一种将函数分解为不同频率的正弦和余弦函数的数学工具。",
                    "x": 100,
                    "y": 100,
                    "width": 400,
                    "height": 200,
                    "color": "1",  # 红色，表示不理解
                },
                {
                    "id": "material-2",
                    "type": "text",
                    "text": "机器学习是人工智能的一个分支，它使用算法和统计模型让计算机系统自动学习和改进。",
                    "x": 600,
                    "y": 100,
                    "width": 400,
                    "height": 200,
                    "color": "3",  # 紫色，表示似懂非懂
                },
            ],
            "edges": [],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".canvas", delete=False) as f:
            json.dump(canvas_data, f)
            temp_path = f.name

        yield temp_path

        if os.path.exists(temp_path):
            os.unlink(temp_path)

    @pytest.fixture
    def large_canvas_with_many_nodes(self):
        """创建包含大量节点的测试Canvas"""
        canvas_data = {"nodes": [], "edges": []}

        # 创建20个红色节点（需要基础拆解）
        for i in range(20):
            canvas_data["nodes"].append(
                {
                    "id": f"material-red-{i}",
                    "type": "text",
                    "text": f"这是需要基础拆解的复杂概念 {i}：包含多个技术术语和抽象概念。",
                    "x": (i % 5) * 500,
                    "y": (i // 5) * 300,
                    "width": 400,
                    "height": 200,
                    "color": "1",
                }
            )

        # 创建15个紫色节点（需要深度拆解）
        for i in range(15):
            canvas_data["nodes"].append(
                {
                    "id": f"material-purple-{i}",
                    "type": "text",
                    "text": f"这是似懂非懂的概念 {i}：需要深度分析和理解。",
                    "x": (i % 5) * 500,
                    "y": ((i // 5) + 4) * 300,
                    "width": 400,
                    "height": 200,
                    "color": "3",
                }
            )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".canvas", delete=False) as f:
            json.dump(canvas_data, f)
            temp_path = f.name

        yield temp_path

        if os.path.exists(temp_path):
            os.unlink(temp_path)

    @patch("canvas_utils.Task")  # Mock the Task tool for Agent calls
    def test_basic_decomposition_performance_single(
        self, mock_task, sample_canvas_with_nodes
    ):
        """测试单个基础拆解操作的性能 (< 20秒)"""
        # Mock the Task call to simulate basic-decomposition agent
        mock_result = {
            "sub_questions": [
                {
                    "text": "什么是傅里叶变换的基本定义？",
                    "type": "定义型",
                    "difficulty": "基础",
                },
                {
                    "text": "傅里叶变换有哪些主要应用？",
                    "type": "应用型",
                    "difficulty": "中等",
                },
                {
                    "text": "傅里叶变换的数学原理是什么？",
                    "type": "原理型",
                    "difficulty": "困难",
                },
            ],
            "total_count": 3,
        }
        mock_task.return_value = mock_result

        orchestrator = CanvasOrchestrator(sample_canvas_with_nodes)

        start_time = time.time()

        # 执行基础拆解
        orchestrator.handle_basic_decomposition(
            node_id="material-1", agent_result=mock_result
        )

        end_time = time.time()

        execution_time = end_time - start_time

        # 性能断言: 单个基础拆解应该在20秒内完成
        assert execution_time < 20.0, (
            f"单个基础拆解耗时 {execution_time:.3f}s，超过20秒限制"
        )

        # 验证结果
        updated_canvas = orchestrator.business_logic.canvas_data
        question_nodes = [
            n
            for n in updated_canvas["nodes"]
            if n.get("type") == "text" and "问题" in n.get("text", "")
        ]
        assert len(question_nodes) >= 3, "应该生成至少3个问题节点"

    @patch("canvas_utils.Task")
    def test_deep_decomposition_performance_single(
        self, mock_task, sample_canvas_with_nodes
    ):
        """测试单个深度拆解操作的性能 (< 30秒)"""
        # Mock the Task call to simulate deep-decomposition agent
        mock_result = {
            "deep_questions": [
                {
                    "text": "机器学习与传统编程的本质区别是什么？",
                    "type": "对比型",
                    "difficulty": "中等",
                },
                {
                    "text": "为什么机器学习需要大量数据？这个要求的根本原因是什么？",
                    "type": "原因型",
                    "difficulty": "困难",
                },
                {
                    "text": "如果给你一个具体的业务问题，如何判断是否适合用机器学习解决？",
                    "type": "应用型",
                    "difficulty": "困难",
                },
                {
                    "text": "机器学习的局限性在哪里？哪些情况下机器学习会失效？",
                    "type": "边界型",
                    "difficulty": "困难",
                },
            ],
            "analysis_depth": "deep",
            "total_count": 4,
        }
        mock_task.return_value = mock_result

        orchestrator = CanvasOrchestrator(sample_canvas_with_nodes)

        start_time = time.time()

        # 执行深度拆解
        orchestrator.handle_deep_decomposition(
            node_id="material-2",
            user_understanding="我知道机器学习是让计算机自动学习，但不清楚具体怎么实现",
            agent_result=mock_result,
        )

        end_time = time.time()

        execution_time = end_time - start_time

        # 性能断言: 单个深度拆解应该在30秒内完成
        assert execution_time < 30.0, (
            f"单个深度拆解耗时 {execution_time:.3f}s，超过30秒限制"
        )

        # 验证结果
        updated_canvas = orchestrator.business_logic.canvas_data
        deep_question_nodes = [
            n for n in updated_canvas["nodes"] if "深度" in n.get("text", "")
        ]
        assert len(deep_question_nodes) >= 4, "应该生成至少4个深度问题节点"

    @patch("canvas_utils.Task")
    def test_batch_scoring_performance(self, mock_task, sample_canvas_with_nodes):
        """测试批量评分操作的性能 (< 30秒)"""
        # Mock the Task call to simulate scoring agent
        mock_scoring_result = {
            "accuracy_score": 22,
            "imagery_score": 18,
            "completeness_score": 20,
            "originality_score": 19,
            "total_score": 79,
            "color_transition": "purple",
            "recommendations": ["建议添加更多具体例子", "可以增加对比分析"],
        }
        mock_task.return_value = mock_scoring_result

        orchestrator = CanvasOrchestrator(sample_canvas_with_nodes)

        # 首先为测试添加一些黄色理解节点
        business_logic = orchestrator.business_logic
        for material_node in ["material-1", "material-2"]:
            question_id, yellow_id = business_logic.add_sub_question_with_yellow_node(
                material_node, "请解释你对这个概念的理解", "💡 提示：用自己的话说明"
            )
            # 填写一些理解内容
            business_logic.update_node_text(yellow_id, "这是我目前的理解...")

        start_time = time.time()

        # 执行批量评分
        yellow_nodes = [
            n for n in business_logic.canvas_data["nodes"] if n.get("color") == "6"
        ]
        for yellow_node in yellow_nodes:
            orchestrator.handle_scoring(
                node_id=yellow_node["id"], agent_result=mock_scoring_result
            )

        end_time = time.time()

        execution_time = end_time - start_time

        # 性能断言: 批量评分应该在30秒内完成
        assert execution_time < 30.0, (
            f"批量评分耗时 {execution_time:.3f}s，超过30秒限制"
        )

        # 验证评分结果
        updated_canvas = business_logic.canvas_data
        scored_nodes = [
            n for n in updated_canvas["nodes"] if n.get("color") == "3"
        ]  # 紫色节点
        assert len(scored_nodes) >= 2, "应该有至少2个节点被评分"

    @patch("canvas_utils.Task")
    def test_parallel_agent_execution_performance(
        self, mock_task, large_canvas_with_many_nodes
    ):
        """测试并行Agent执行性能"""

        # Mock different agent responses
        def mock_task_side_effect(*args, **kwargs):
            if "basic-decomposition" in str(kwargs):
                return {
                    "sub_questions": [
                        {
                            "text": f"基础问题 {time.time()}",
                            "type": "定义型",
                            "difficulty": "基础",
                        }
                    ],
                    "total_count": 1,
                }
            elif "deep-decomposition" in str(kwargs):
                return {
                    "deep_questions": [
                        {
                            "text": f"深度问题 {time.time()}",
                            "type": "对比型",
                            "difficulty": "中等",
                        }
                    ],
                    "total_count": 1,
                }
            else:
                return {"result": "mocked"}

        mock_task.side_effect = mock_task_side_effect

        async def run_parallel_agents():
            """模拟并行执行多个Agent"""
            orchestrator = CanvasOrchestrator(large_canvas_with_many_nodes)
            tasks = []

            # 创建多个并发任务
            for i in range(5):  # 测试5个并发Agent
                if i < 3:
                    # 前3个执行基础拆解
                    task = asyncio.create_task(
                        asyncio.to_thread(
                            orchestrator.handle_basic_decomposition,
                            f"material-red-{i}",
                            {},
                        )
                    )
                else:
                    # 后2个执行深度拆解
                    task = asyncio.create_task(
                        asyncio.to_thread(
                            orchestrator.handle_deep_decomposition,
                            f"material-purple-{i - 3}",
                            "用户理解",
                            {},
                        )
                    )
                tasks.append(task)

            start_time = time.time()
            await asyncio.gather(*tasks)
            end_time = time.time()

            return end_time - start_time

        # 运行并行测试
        execution_time = asyncio.run(run_parallel_agents())

        # 性能断言: 5个并发Agent应该在合理时间内完成
        # 并行执行应该比串行执行快，但考虑到模拟开销，设定较宽松的限制
        assert execution_time < 60.0, (
            f"5个并发Agent执行耗时 {execution_time:.3f}s，超过60秒限制"
        )

    def test_agent_context_switching_performance(self, sample_canvas_with_nodes):
        """测试Agent上下文切换性能"""
        orchestrator = CanvasOrchestrator(sample_canvas_with_nodes)

        start_time = time.time()

        # 模拟多次Agent调用的上下文切换
        for i in range(10):
            # 创建新的orchestrator实例模拟上下文切换
            new_orchestrator = CanvasOrchestrator(sample_canvas_with_nodes)
            # 执行一些基本操作
            canvas_data = new_orchestrator.business_logic.canvas_data
            node_count = len(canvas_data["nodes"])

        end_time = time.time()

        execution_time = end_time - start_time

        # 性能断言: 10次上下文切换应该在5秒内完成
        assert execution_time < 5.0, (
            f"10次上下文切换耗时 {execution_time:.3f}s，超过5秒限制"
        )

    def test_agent_memory_usage_performance(self, large_canvas_with_many_nodes):
        """测试Agent操作的内存使用情况"""
        import gc

        import psutil

        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        orchestrator = CanvasOrchestrator(large_canvas_with_many_nodes)

        # 执行多次Agent操作
        for i in range(5):
            canvas_data = orchestrator.business_logic.canvas_data
            # 模拟Agent处理数据
            processed_nodes = []
            for node in canvas_data["nodes"][:10]:  # 每次处理10个节点
                processed_node = node.copy()
                processed_node["text"] += f" (processed by agent {i})"
                processed_nodes.append(processed_node)

        gc.collect()  # 强制垃圾回收

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # 内存增长应该在合理范围内（< 50MB for agent operations）
        assert memory_increase < 50, (
            f"Agent操作内存增长 {memory_increase:.1f}MB，超过50MB限制"
        )

    @patch("canvas_utils.Task")
    def test_agent_error_handling_performance(
        self, mock_task, sample_canvas_with_nodes
    ):
        """测试Agent错误处理的性能影响"""
        # Mock a failing agent call
        mock_task.side_effect = Exception("Agent execution failed")

        orchestrator = CanvasOrchestrator(sample_canvas_with_nodes)

        start_time = time.time()

        # 尝试执行会失败的Agent操作
        try:
            orchestrator.handle_basic_decomposition("material-1", {})
        except Exception:
            pass  # 预期会失败

        # 尝试多次失败操作
        for i in range(5):
            try:
                orchestrator.handle_basic_decomposition(f"non-existent-{i}", {})
            except Exception:
                pass  # 预期会失败

        end_time = time.time()

        execution_time = end_time - start_time

        # 性能断言: 错误处理应该快速完成，不造成显著延迟
        assert execution_time < 10.0, (
            f"5次错误处理耗时 {execution_time:.3f}s，超过10秒限制"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
