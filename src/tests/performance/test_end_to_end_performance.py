"""
端到端性能测试套件

测试完整的Canvas学习工作流的性能，包括：
- Canvas文件操作 + Agent系统 + 记忆系统的集成性能
- 完整学习工作流的端到端验证
- 异常情况下的系统稳定性测试

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
from unittest.mock import MagicMock, patch

import pytest

sys.path.append(str(Path(__file__).parent.parent.parent))
from canvas_utils import CanvasBusinessLogic, CanvasJSONOperator, CanvasOrchestrator

# Mock imports for systems that may not be fully implemented
sys.modules['graphiti'] = MagicMock()
sys.modules['mcp'] = MagicMock()


class TestEndToEndPerformance:
    """端到端性能测试类"""

    @pytest.fixture
    def complete_workflow_canvas(self):
        """创建完整工作流测试用的Canvas"""
        canvas_data = {
            "nodes": [
                {
                    "id": "material-calculus",
                    "type": "text",
                    "text": "微积分是研究函数的微分、积分以及有关概念和应用的数学分支。它是现代数学的重要基础，广泛应用于物理、工程、经济等领域。",
                    "x": 100,
                    "y": 100,
                    "width": 450,
                    "height": 200,
                    "color": "1"  # 红色，不理解
                },
                {
                    "id": "material-linear-algebra",
                    "type": "text",
                    "text": "线性代数是研究向量空间与线性映射的数学分支。包括向量、矩阵、行列式、线性方程组等内容。",
                    "x": 600,
                    "y": 100,
                    "width": 450,
                    "height": 200,
                    "color": "3"  # 紫色，似懂非懂
                },
                {
                    "id": "material-probability",
                    "type": "text",
                    "text": "概率论是研究随机现象数量规律的数学分支。它为统计学、机器学习、金融等领域提供理论基础。",
                    "x": 100,
                    "y": 400,
                    "width": 450,
                    "height": 200,
                    "color": "1"  # 红色，不理解
                }
            ],
            "edges": [
                {
                    "id": "edge-1",
                    "fromNode": "material-calculus",
                    "toNode": "material-linear-algebra",
                    "fromSide": "right",
                    "toSide": "left",
                    "label": "相关数学基础"
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.canvas', delete=False) as f:
            json.dump(canvas_data, f)
            temp_path = f.name

        yield temp_path

        if os.path.exists(temp_path):
            os.unlink(temp_path)

    @patch('canvas_utils.Task')
    @patch('mcp.graphiti_memory__add_memory')
    def test_complete_learning_workflow_performance(self, mock_memory, mock_task, complete_workflow_canvas):
        """测试完整学习工作流的性能 (< 2分钟)"""
        # Mock agent responses
        mock_task.side_effect = [
            # Basic decomposition response
            {
                "sub_questions": [
                    {"text": "微积分的核心概念是什么？", "type": "定义型", "difficulty": "基础"},
                    {"text": "微积分有哪些实际应用？", "type": "应用型", "difficulty": "中等"}
                ],
                "total_count": 2
            },
            # Deep decomposition response
            {
                "deep_questions": [
                    {"text": "线性代数与微积分的本质区别是什么？", "type": "对比型", "difficulty": "中等"},
                    {"text": "为什么线性代数在现代数学中如此重要？", "type": "原因型", "difficulty": "困难"}
                ],
                "total_count": 2
            },
            # Scoring response
            {
                "accuracy_score": 20,
                "imagery_score": 18,
                "completeness_score": 22,
                "originality_score": 19,
                "total_score": 79,
                "color_transition": "purple"
            },
            # Explanation response
            {
                "explanation_content": "微积分是研究变化的数学工具...",
                "generated_at": time.time()
            }
        ]

        # Mock memory storage
        mock_memory.return_value = {"status": "success", "memory_id": "test-memory"}

        orchestrator = CanvasOrchestrator(complete_workflow_canvas)

        start_time = time.time()

        # Step 1: 基础拆解 (红色节点)
        orchestrator.handle_basic_decomposition(
            node_id="material-calculus",
            agent_result=mock_task.side_effect[0]
        )

        # Step 2: 深度拆解 (紫色节点)
        orchestrator.handle_deep_decomposition(
            node_id="material-linear-algebra",
            user_understanding="我知道线性代数是关于向量和矩阵的，但不清楚具体应用",
            agent_result=mock_task.side_effect[1]
        )

        # Step 3: 评分 (添加黄色节点后评分)
        business_logic = orchestrator.business_logic
        question_id, yellow_id = business_logic.add_sub_question_with_yellow_node(
            "material-calculus",
            "请解释微积分的核心概念",
            "💡 提示：从微分和积分两个方面思考"
        )
        business_logic.update_node_text(yellow_id, "微积分是研究函数变化的数学分支...")

        orchestrator.handle_scoring(
            node_id=yellow_id,
            agent_result=mock_task.side_effect[2]
        )

        # Step 4: 补充解释
        orchestrator.handle_explanation_generation(
            node_id="material-calculus",
            agent_result=mock_task.side_effect[3]
        )

        # Step 5: 记忆存储
        mock_memory(
            key="learning-session-math",
            content=json.dumps({
                "session_type": "complete_workflow",
                "concepts": ["calculus", "linear_algebra"],
                "timestamp": time.time()
            }),
            metadata={"importance": 9}
        )

        end_time = time.time()

        execution_time = end_time - start_time

        # 性能断言: 完整学习工作流应该在2分钟内完成
        assert execution_time < 120.0, f"完整学习工作流耗时 {execution_time:.1f}s，超过2分钟限制"

        # 验证工作流完成状态
        final_canvas = orchestrator.business_logic.canvas_data
        question_nodes = [n for n in final_canvas["nodes"] if "问题" in n.get("text", "")]
        yellow_nodes = [n for n in final_canvas["nodes"] if n.get("color") == "6"]
        assert len(question_nodes) >= 4, "应该生成至少4个问题节点"
        assert len(yellow_nodes) >= 1, "应该有至少1个黄色理解节点"

    @patch('canvas_utils.Task')
    def test_review_canvas_generation_performance(self, mock_task, complete_workflow_canvas):
        """测试检验白板生成性能 (< 40秒)"""
        # Mock agent responses for review questions
        mock_task.return_value = {
            "verification_questions": [
                {
                    "question": "用自己的话解释什么是微积分？",
                    "type": "基础型",
                    "difficulty": "基础",
                    "target_node": "material-calculus"
                },
                {
                    "question": "线性代数的核心概念有哪些？它们之间有什么关系？",
                    "type": "检验型",
                    "difficulty": "中等",
                    "target_node": "material-linear-algebra"
                }
            ],
            "total_questions": 2
        }

        orchestrator = CanvasOrchestrator(complete_workflow_canvas)

        start_time = time.time()

        # 生成检验白板
        review_canvas_data = orchestrator.business_logic.generate_review_canvas(
            original_canvas_path=complete_workflow_canvas,
            target_nodes=["material-calculus", "material-linear-algebra", "material-probability"]
        )

        end_time = time.time()

        execution_time = end_time - start_time

        # 性能断言: 检验白板生成应该在40秒内完成
        assert execution_time < 40.0, f"检验白板生成耗时 {execution_time:.1f}s，超过40秒限制"

        # 验证检验白板内容
        assert "nodes" in review_canvas_data
        assert len(review_canvas_data["nodes"]) > 0

        # 验证检验问题是否正确生成
        verification_nodes = [n for n in review_canvas_data["nodes"]
                            if "检验" in n.get("text", "") or "问题" in n.get("text", "")]
        assert len(verification_nodes) >= 2, "应该生成至少2个检验问题节点"

    def test_canvas_file_operations_stress_test(self):
        """测试Canvas文件操作压力测试"""
        # 创建大规模Canvas数据
        large_canvas_data = {"nodes": [], "edges": []}

        # 创建500个节点
        for i in range(500):
            large_canvas_data["nodes"].append({
                "id": f"stress-node-{i}",
                "type": "text",
                "text": f"压力测试节点 {i} 的内容",
                "x": (i % 20) * 300,
                "y": (i // 20) * 250,
                "width": 280,
                "height": 200,
                "color": str((i % 5) + 1)
            })

        # 创建连接边
        for i in range(0, 480, 20):
            for j in range(min(19, 500 - i - 1)):
                large_canvas_data["edges"].append({
                    "id": f"stress-edge-{i}-{j}",
                    "fromNode": f"stress-node-{i}",
                    "toNode": f"stress-node-{i + j + 1}",
                    "fromSide": "right",
                    "toSide": "left"
                })

        with tempfile.NamedTemporaryFile(mode='w', suffix='.canvas', delete=False) as f:
            json.dump(large_canvas_data, f)
            temp_path = f.name

        try:
            start_time = time.time()

            # 测试读取性能
            read_data = CanvasJSONOperator.read_canvas(temp_path)
            read_time = time.time()
            read_duration = read_time - start_time

            # 测试写入性能
            CanvasJSONOperator.write_canvas(temp_path + ".copy", read_data)
            write_time = time.time()
            write_duration = write_time - read_time

            # 测试节点操作性能
            business_logic = CanvasBusinessLogic(temp_path)
            for i in range(10):  # 对前10个节点进行操作
                business_logic.add_sub_question_with_yellow_node(
                    f"stress-node-{i}",
                    f"压力测试问题 {i}",
                    "💡 提示：这是性能测试"
                )

            operation_time = time.time()
            operation_duration = operation_time - write_time

            total_time = operation_time - start_time

            # 性能断言
            assert read_duration < 5.0, f"读取500节点Canvas耗时 {read_duration:.3f}s，超过5秒限制"
            assert write_duration < 8.0, f"写入500节点Canvas耗时 {write_duration:.3f}s，超过8秒限制"
            assert operation_duration < 15.0, f"10次节点操作耗时 {operation_duration:.3f}s，超过15秒限制"
            assert total_time < 30.0, f"总压力测试耗时 {total_time:.3f}s，超过30秒限制"

            # 验证数据完整性
            assert len(read_data["nodes"]) == 500
            assert len(read_data["edges"]) > 0

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            if os.path.exists(temp_path + ".copy"):
                os.unlink(temp_path + ".copy")

    @patch('canvas_utils.Task')
    def test_error_handling_system_stability(self, mock_task, complete_workflow_canvas):
        """测试错误处理下的系统稳定性"""
        # Mock agent failures
        call_count = 0
        def mock_task_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count % 3 == 0:
                raise Exception(f"Agent execution failed (call {call_count})")
            return {
                "sub_questions": [{"text": f"问题 {call_count}", "type": "定义型"}],
                "total_count": 1
            }

        mock_task.side_effect = mock_task_side_effect

        orchestrator = CanvasOrchestrator(complete_workflow_canvas)

        start_time = time.time()
        successful_operations = 0
        failed_operations = 0

        # 尝试执行10次操作，其中会有一些失败
        for i in range(10):
            try:
                orchestrator.handle_basic_decomposition(
                    node_id="material-calculus",
                    agent_result={}  # Empty result to trigger agent call
                )
                successful_operations += 1
            except Exception:
                failed_operations += 1
                # 系统应该能继续运行
                continue

        end_time = time.time()
        execution_time = end_time - start_time

        # 验证系统稳定性
        assert execution_time < 60.0, f"错误处理测试耗时 {execution_time:.1f}s，超过60秒限制"
        assert successful_operations > 0, "应该有成功的操作"
        assert failed_operations > 0, "应该有失败的操作被正确处理"

        # 验证系统仍然可用
        final_canvas = orchestrator.business_logic.canvas_data
        assert "nodes" in final_canvas
        assert len(final_canvas["nodes"]) > 0

    def test_concurrent_workflow_performance(self, complete_workflow_canvas):
        """测试并发工作流性能"""
        async def run_concurrent_workflows():
            """运行多个并发工作流"""
            tasks = []

            for i in range(3):  # 3个并发工作流
                task = asyncio.create_task(
                    asyncio.to_thread(self._single_workflow_test, complete_workflow_canvas, i)
                )
                tasks.append(task)

            start_time = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()

            successful_results = [r for r in results if not isinstance(r, Exception)]
            return len(successful_results), end_time - start_time

        def _single_workflow_test(self, canvas_path, workflow_id):
            """单个工作流测试"""
            orchestrator = CanvasOrchestrator(canvas_path)
            business_logic = orchestrator.business_logic

            # 模拟工作流操作
            for i in range(5):
                question_id, yellow_id = business_logic.add_sub_question_with_yellow_node(
                    "material-calculus",
                    f"并发工作流 {workflow_id} 问题 {i}",
                    f"💡 提示 {workflow_id}-{i}"
                )
                business_logic.update_node_text(yellow_id, f"理解内容 {workflow_id}-{i}")

            return workflow_id

        # 运行并发测试
        success_count, execution_time = asyncio.run(run_concurrent_workflows())

        # 性能断言: 3个并发工作流应该在45秒内完成
        assert execution_time < 45.0, f"3个并发工作流耗时 {execution_time:.1f}s，超过45秒限制"
        assert success_count >= 2, "至少2个并发工作流应该成功完成"

    def test_system_resource_usage_monitoring(self, complete_workflow_canvas):
        """测试系统资源使用监控"""
        import gc

        import psutil

        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        initial_cpu = process.cpu_percent()

        orchestrator = CanvasOrchestrator(complete_workflow_canvas)
        business_logic = orchestrator.business_logic

        # 执行资源密集型操作
        for i in range(20):
            question_id, yellow_id = business_logic.add_sub_question_with_yellow_node(
                "material-calculus",
                f"资源测试问题 {i}",
                f"💡 提示 {i}"
            )
            business_logic.update_node_text(yellow_id, "A" * 1000)  # 较大的文本内容

            # 每5次操作强制垃圾回收
            if i % 5 == 0:
                gc.collect()

        gc.collect()  # 最终垃圾回收

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        final_cpu = process.cpu_percent()

        memory_increase = final_memory - initial_memory
        cpu_usage = max(initial_cpu, final_cpu)

        # 资源使用断言
        assert memory_increase < 100, f"内存使用增长 {memory_increase:.1f}MB，超过100MB限制"
        assert cpu_usage < 80, f"CPU使用率 {cpu_usage:.1f}%，超过80%限制"

        # 验证操作完成
        final_canvas = business_logic.canvas_data
        yellow_nodes = [n for n in final_canvas["nodes"] if n.get("color") == "6"]
        assert len(yellow_nodes) >= 20, "应该创建至少20个黄色节点"

    def test_data_integrity_under_stress(self, complete_workflow_canvas):
        """测试压力下的数据完整性"""
        orchestrator = CanvasOrchestrator(complete_workflow_canvas)
        business_logic = orchestrator.business_logic

        # 记录初始状态
        initial_node_count = len(business_logic.canvas_data["nodes"])
        initial_edge_count = len(business_logic.canvas_data["edges"])

        # 执行大量操作
        operations_performed = 0
        for i in range(50):
            try:
                question_id, yellow_id = business_logic.add_sub_question_with_yellow_node(
                    "material-calculus",
                    f"完整性测试 {i}",
                    f"💡 提示 {i}"
                )
                business_logic.update_node_text(yellow_id, f"内容 {i}")
                operations_performed += 1
            except Exception:
                continue

        # 验证数据完整性
        final_canvas = business_logic.canvas_data
        final_node_count = len(final_canvas["nodes"])
        final_edge_count = len(final_canvas["edges"])

        # 完整性断言
        assert final_node_count == initial_node_count + (operations_performed * 2), "节点数量应该正确增长"
        assert final_edge_count == initial_edge_count, "边数量不应该意外改变"

        # 验证节点数据完整性
        for node in final_canvas["nodes"]:
            assert "id" in node, "节点必须有ID"
            assert "type" in node, "节点必须有类型"
            assert "x" in node and "y" in node, "节点必须有坐标"
            assert "color" in node, "节点必须有颜色"

        # 验证文件可以正确保存和加载
        with tempfile.NamedTemporaryFile(mode='w', suffix='.canvas', delete=False) as f:
            temp_path = f.name

        try:
            CanvasJSONOperator.write_canvas(temp_path, final_canvas)
            reloaded_data = CanvasJSONOperator.read_canvas(temp_path)

            assert len(reloaded_data["nodes"]) == final_node_count, "重新加载的节点数量应该匹配"
            assert len(reloaded_data["edges"]) == final_edge_count, "重新加载的边数量应该匹配"

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
