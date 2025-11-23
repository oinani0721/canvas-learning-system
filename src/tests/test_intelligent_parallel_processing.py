"""
Story 10.1: ReviewBoardAgentSelector并行处理集成测试套件

测试多Agent推荐、并行执行、批量处理等核心功能。
测试覆盖率目标: >90%
"""

import asyncio
import pytest
import time
import uuid
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from canvas_utils import (
    # 核心类
    ReviewBoardAgentSelector,
    ConcurrentAgentProcessor,
    CanvasOrchestrator,
    CanvasJSONOperator,
    CanvasBusinessLogic,

    # 全局实例
    ultrathink_canvas_integration,
    concurrent_agent_processor,

    # 颜色常量
    COLOR_YELLOW
)


class TestReviewBoardAgentSelector:
    """测试ReviewBoardAgentSelector的多Agent推荐功能"""

    @pytest.fixture
    def selector(self):
        """创建ReviewBoardAgentSelector实例"""
        return ReviewBoardAgentSelector()

    @pytest.mark.asyncio
    async def test_analyze_understanding_quality_advanced(self, selector):
        """测试高级理解质量分析功能"""
        # 准备测试数据
        node_text = "我对逆否命题的理解是：如果P→Q，那么¬Q→¬P"
        context = {"node_id": "test-node-123"}

        # 执行分析
        result = await selector.analyze_understanding_quality_advanced(
            node_text,
            context=context
        )

        # 验证结果
        assert result is not None
        assert "accuracy_score" in result
        assert "completeness_score" in result
        assert "clarity_score" in result
        assert "originality_score" in result
        assert "overall_quality" in result
        assert "analysis_time_ms" in result

        # 验证分数范围
        assert 0 <= result["accuracy_score"] <= 1
        assert 0 <= result["completeness_score"] <= 1
        assert 0 <= result["clarity_score"] <= 1
        assert 0 <= result["originality_score"] <= 1
        assert 0 <= result["overall_quality"] <= 1

        # 验证分析时间为正数
        assert result["analysis_time_ms"] > 0

    @pytest.mark.asyncio
    async def test_recommend_multiple_agents(self, selector):
        """测试多Agent推荐功能"""
        # 准备质量分析数据
        quality_analysis = {
            "accuracy_score": 0.75,
            "completeness_score": 0.68,
            "clarity_score": 0.82,
            "originality_score": 0.60,
            "overall_quality": 0.71
        }

        # 执行推荐
        result = await selector.recommend_multiple_agents(
            quality_analysis,
            max_recommendations=3
        )

        # 验证结果结构
        assert result is not None
        assert "analysis_id" in result
        assert "node_id" in result
        assert "understanding_quality" in result
        assert "recommended_agents" in result
        assert "processing_strategy" in result

        # 验证推荐数量
        assert len(result["recommended_agents"]) <= 3
        assert len(result["recommended_agents"]) > 0

        # 验证每个推荐的结构
        for agent in result["recommended_agents"]:
            assert "agent_name" in agent
            assert "confidence_score" in agent
            assert "reasoning" in agent
            assert "priority" in agent
            assert "estimated_duration" in agent

            # 验证置信度范围
            assert 0 <= agent["confidence_score"] <= 1

        # 验证处理策略
        strategy = result["processing_strategy"]
        assert "execution_mode" in strategy
        assert "max_concurrent" in strategy
        assert "total_estimated_duration" in strategy

    @pytest.mark.asyncio
    async def test_recommend_multiple_agents_with_low_quality(self, selector):
        """测试低质量理解的多Agent推荐"""
        # 准备低质量分析数据
        quality_analysis = {
            "accuracy_score": 0.3,
            "completeness_score": 0.4,
            "clarity_score": 0.2,
            "originality_score": 0.3,
            "overall_quality": 0.3
        }

        # 执行推荐
        result = await selector.recommend_multiple_agents(
            quality_analysis,
            max_recommendations=5
        )

        # 验证推荐了基础拆解类型的Agent
        agent_names = [agent["agent_name"] for agent in result["recommended_agents"]]
        assert "basic-decomposition" in agent_names

        # 验证置信度较低
        for agent in result["recommended_agents"]:
            assert agent["confidence_score"] < 0.8

    @pytest.mark.asyncio
    async def test_recommend_multiple_agents_with_high_quality(self, selector):
        """测试高质量理解的多Agent推荐"""
        # 准备高质量分析数据
        quality_analysis = {
            "accuracy_score": 0.95,
            "completeness_score": 0.90,
            "clarity_score": 0.92,
            "originality_score": 0.88,
            "overall_quality": 0.91
        }

        # 执行推荐
        result = await selector.recommend_multiple_agents(
            quality_analysis,
            max_recommendations=3
        )

        # 验证推荐了应用类型的Agent
        agent_names = [agent["agent_name"] for agent in result["recommended_agents"]]
        assert "example-teaching" in agent_names or "verification-question-agent" in agent_names

        # 验证置信度较高
        for agent in result["recommended_agents"]:
            assert agent["confidence_score"] > 0.7

    def test_backward_compatibility_single_agent(self, selector):
        """测试向后兼容的单Agent推荐功能"""
        # 测试原有方法是否仍然存在
        assert hasattr(selector, 'analyze_understanding_quality')
        assert hasattr(selector, 'recommend_agents')

        # 执行单Agent推荐
        node_text = "测试文本内容"
        analysis = selector.analyze_understanding_quality(node_text)

        assert analysis is not None
        assert "quality_score" in analysis


class TestConcurrentAgentProcessor:
    """测试ConcurrentAgentProcessor的并行执行功能"""

    @pytest.fixture
    def processor(self):
        """创建ConcurrentAgentProcessor实例"""
        return ConcurrentAgentProcessor(max_concurrent=5)

    @pytest.mark.asyncio
    async def test_execute_parallel_success(self, processor):
        """测试成功的并行执行"""
        # 准备测试任务
        agent_tasks = [
            {
                "agent_name": "oral-explanation",
                "node_id": "node-1",
                "node_text": "测试内容1"
            },
            {
                "agent_name": "clarification-path",
                "node_id": "node-2",
                "node_text": "测试内容2"
            },
            {
                "agent_name": "comparison-table",
                "node_id": "node-3",
                "node_text": "测试内容3"
            }
        ]

        canvas_path = "test_canvas.canvas"

        # 执行并行任务
        result = await processor.execute_parallel(
            agent_tasks,
            canvas_path,
            timeout=10
        )

        # 验证结果
        assert result["status"] == "completed"
        assert "execution_id" in result
        assert "results" in result
        assert "execution_summary" in result

        # 验证结果数量
        assert len(result["results"]) == len(agent_tasks)

        # 验证执行摘要
        summary = result["execution_summary"]
        assert summary["total_tasks"] == len(agent_tasks)
        assert summary["successful_tasks"] >= 0
        assert summary["failed_tasks"] >= 0
        assert summary["success_rate"] >= 0
        assert summary["total_execution_time"] > 0

    @pytest.mark.asyncio
    async def test_execute_parallel_with_timeout(self, processor):
        """测试并行执行超时处理"""
        # 准备耗时任务
        agent_tasks = [
            {
                "agent_name": "slow-agent",
                "node_id": "node-1",
                "node_text": "测试内容"
            }
        ]

        # 使用短超时时间
        with patch('asyncio.sleep', side_effect=asyncio.sleep(2)):
            result = await processor.execute_parallel(
                agent_tasks,
                "test_canvas.canvas",
                timeout=1
            )

        # 验证超时错误
        assert result["status"] == "error"
        assert "超时" in result["error"]

    @pytest.mark.asyncio
    async def test_concurrent_limit_enforcement(self, processor):
        """测试并发限制强制执行"""
        # 创建超过并发限制的任务数量
        agent_tasks = []
        for i in range(10):  # 10个任务，超过max_concurrent=5
            agent_tasks.append({
                "agent_name": f"agent-{i}",
                "node_id": f"node-{i}",
                "node_text": f"测试内容{i}"
            })

        # 执行并行任务
        start_time = time.time()
        result = await processor.execute_parallel(
            agent_tasks,
            "test_canvas.canvas",
            timeout=30
        )
        execution_time = time.time() - start_time

        # 验证所有任务都完成了
        assert result["status"] == "completed"
        assert len(result["results"]) == 10

        # 验证并发限制生效（执行时间应该大于单个任务时间）
        assert execution_time > 1.0  # 至少需要一些时间来处理并发

    def test_performance_metrics_tracking(self, processor):
        """测试性能指标跟踪"""
        # 初始指标应该为0
        metrics = processor.get_performance_metrics()
        assert metrics["total_executions"] == 0
        assert metrics["successful_executions"] == 0
        assert metrics["failed_executions"] == 0

        # 更新指标
        processor._update_performance_metrics(
            total_tasks=5,
            successful_tasks=4,
            execution_time=2.5
        )

        # 验证指标更新
        metrics = processor.get_performance_metrics()
        assert metrics["total_executions"] == 5
        assert metrics["successful_executions"] == 4
        assert metrics["failed_executions"] == 1
        assert metrics["overall_success_rate"] == 80.0

    def test_execution_history_management(self, processor):
        """测试执行历史管理"""
        # 添加执行历史
        execution_id = f"test-{uuid.uuid4().hex[:8]}"
        processor.execution_history.append({
            "execution_id": execution_id,
            "summary": {"test": "data"},
            "timestamp": datetime.now().isoformat()
        })

        # 验证历史记录
        history = processor.get_execution_history(limit=5)
        assert len(history) > 0
        assert history[-1]["execution_id"] == execution_id

    @pytest.mark.asyncio
    async def test_cancel_all_tasks(self, processor):
        """测试取消所有任务"""
        # 创建一些模拟任务
        async def mock_task():
            await asyncio.sleep(10)
            return "completed"

        # 添加活动任务
        task_id = f"task-{uuid.uuid4().hex[:8]}"
        processor.active_tasks[task_id] = asyncio.create_task(mock_task())

        # 取消所有任务
        result = await processor.cancel_all_tasks()

        # 验证取消结果
        assert result["status"] == "all_tasks_cancelled"
        assert len(processor.active_tasks) == 0


class TestCanvasOrchestratorIntegration:
    """测试CanvasOrchestrator的集成功能"""

    @pytest.fixture
    def mock_canvas_data(self):
        """创建模拟Canvas数据"""
        return {
            "nodes": [
                {
                    "id": "test-node-123",
                    "type": "text",
                    "text": "我对逆否命题的理解是：如果P→Q，那么¬Q→¬P，这是一个基本的逻辑等价关系。",
                    "x": 100,
                    "y": 200,
                    "width": 300,
                    "height": 150,
                    "color": COLOR_YELLOW
                }
            ],
            "edges": []
        }

    @pytest.fixture
    def orchestrator(self):
        """创建CanvasOrchestrator实例"""
        with patch('canvas_utils.CanvasJSONOperator.read_canvas') as mock_read:
            mock_read.return_value = {
                "nodes": [],
                "edges": []
            }
            return CanvasOrchestrator("test_canvas.canvas")

    @pytest.mark.asyncio
    async def test_process_multiple_agents_for_node(self, orchestrator, mock_canvas_data):
        """测试单个节点的多Agent处理"""
        # 模拟Canvas数据读取
        with patch.object(orchestrator.operator, 'read_canvas', return_value=mock_canvas_data), \
             patch.object(orchestrator.operator, 'find_node_by_id') as mock_find:

            mock_find.return_value = mock_canvas_data["nodes"][0]

            # 执行处理
            result = await orchestrator.process_multiple_agents_for_node(
                "test_canvas.canvas",
                "test-node-123",
                max_concurrent=3
            )

            # 验证结果结构
            assert result is not None
            assert "execution_id" in result
            assert "status" in result
            assert "node_id" in result
            assert "quality_analysis" in result
            assert "recommendations" in result
            assert "results" in result
            assert "execution_summary" in result

            # 验证节点ID匹配
            assert result["node_id"] == "test-node-123"

    @pytest.mark.asyncio
    async def test_process_multiple_agents_for_node_not_found(self, orchestrator):
        """测试处理不存在的节点"""
        # 模拟节点不存在
        with patch.object(orchestrator.operator, 'find_node_by_id', return_value=None):
            result = await orchestrator.process_multiple_agents_for_node(
                "test_canvas.canvas",
                "non-existent-node",
                max_concurrent=3
            )

            # 验证错误状态
            assert result["status"] == "error"
            assert "不存在" in result["error"]

    @pytest.mark.asyncio
    async def test_process_multiple_agents_for_node_empty_text(self, orchestrator, mock_canvas_data):
        """测试处理空文本节点"""
        # 修改节点为空文本
        mock_canvas_data["nodes"][0]["text"] = ""

        with patch.object(orchestrator.operator, 'read_canvas', return_value=mock_canvas_data), \
             patch.object(orchestrator.operator, 'find_node_by_id') as mock_find:

            mock_find.return_value = mock_canvas_data["nodes"][0]

            # 执行处理
            result = await orchestrator.process_multiple_agents_for_node(
                "test_canvas.canvas",
                "test-node-123",
                max_concurrent=3
            )

            # 验证错误状态
            assert result["status"] == "error"
            assert "空" in result["error"]

    @pytest.mark.asyncio
    async def test_batch_process_nodes(self, orchestrator, mock_canvas_data):
        """测试批量处理多个节点"""
        # 准备多个节点
        mock_canvas_data["nodes"].append({
            "id": "test-node-456",
            "type": "text",
            "text": "我对德摩根定律的理解是：(A∧B)' = A'∨B'",
            "x": 500,
            "y": 200,
            "width": 300,
            "height": 150,
            "color": COLOR_YELLOW
        })

        node_ids = ["test-node-123", "test-node-456"]

        with patch.object(orchestrator.operator, 'read_canvas', return_value=mock_canvas_data), \
             patch.object(orchestrator.operator, 'find_node_by_id') as mock_find:

            # 模拟节点查找
            def find_node_by_id(canvas_data, node_id):
                for node in canvas_data["nodes"]:
                    if node["id"] == node_id:
                        return node
                return None

            mock_find.side_effect = find_node_by_id

            # 执行批量处理
            result = await orchestrator.batch_process_nodes(
                "test_canvas.canvas",
                node_ids,
                max_concurrent=6
            )

            # 验证结果结构
            assert result is not None
            assert "batch_id" in result
            assert "status" in result
            assert "node_results" in result
            assert "batch_summary" in result

            # 验证批量摘要
            summary = result["batch_summary"]
            assert summary["total_nodes"] == len(node_ids)
            assert "successful_nodes" in summary
            assert "failed_nodes" in summary
            assert "node_success_rate" in summary
            assert "total_execution_time" in summary


class TestPerformanceConstraints:
    """测试性能约束"""

    @pytest.mark.asyncio
    async def test_analysis_response_time(self):
        """测试分析响应时间 < 1秒"""
        selector = ReviewBoardAgentSelector()

        node_text = "测试文本内容用于性能测试"
        start_time = time.time()

        await selector.analyze_understanding_quality_advanced(node_text)

        response_time = time.time() - start_time
        assert response_time < 1.0, f"分析响应时间 {response_time}s 超过1秒限制"

    @pytest.mark.asyncio
    async def test_recommendation_generation_time(self):
        """测试推荐生成时间 < 0.5秒"""
        selector = ReviewBoardAgentSelector()

        quality_analysis = {
            "accuracy_score": 0.75,
            "completeness_score": 0.68,
            "clarity_score": 0.82,
            "originality_score": 0.60,
            "overall_quality": 0.71
        }

        start_time = time.time()

        await selector.recommend_multiple_agents(quality_analysis)

        response_time = time.time() - start_time
        assert response_time < 0.5, f"推荐生成时间 {response_time}s 超过0.5秒限制"

    @pytest.mark.asyncio
    async def test_parallel_execution_performance(self):
        """测试并行执行性能 < 5秒"""
        processor = ConcurrentAgentProcessor(max_concurrent=5)

        # 创建5个任务
        agent_tasks = []
        for i in range(5):
            agent_tasks.append({
                "agent_name": f"agent-{i}",
                "node_id": f"node-{i}",
                "node_text": f"测试内容{i}"
            })

        start_time = time.time()

        result = await processor.execute_parallel(
            agent_tasks,
            "test_canvas.canvas",
            timeout=10
        )

        execution_time = result["execution_summary"]["total_execution_time"]
        assert execution_time < 5.0, f"并行执行时间 {execution_time}s 超过5秒限制"


class TestErrorHandlingAndEdgeCases:
    """测试错误处理和边界条件"""

    @pytest.mark.asyncio
    async def test_invalid_node_text_handling(self):
        """测试无效节点文本处理"""
        selector = ReviewBoardAgentSelector()

        # 测试None输入
        with pytest.raises(Exception):
            await selector.analyze_understanding_quality_advanced(None)

        # 测试空字符串
        result = await selector.analyze_understanding_quality_advanced("")
        assert result["overall_quality"] == 0.0

    @pytest.mark.asyncio
    async def test_invalid_quality_analysis_handling(self):
        """测试无效质量分析处理"""
        selector = ReviewBoardAgentSelector()

        # 测试不完整的质量分析
        invalid_analysis = {
            "accuracy_score": 0.5
            # 缺少其他必需字段
        }

        with pytest.raises(Exception):
            await selector.recommend_multiple_agents(invalid_analysis)

    @pytest.mark.asyncio
    async def test_concurrent_processor_max_limit(self):
        """测试并发处理器最大限制"""
        # 创建限制为1的处理器
        processor = ConcurrentAgentProcessor(max_concurrent=1)

        # 创建多个任务
        agent_tasks = []
        for i in range(3):
            agent_tasks.append({
                "agent_name": f"agent-{i}",
                "node_id": f"node-{i}",
                "node_text": f"测试内容{i}"
            })

        # 验证并发限制
        assert processor.max_concurrent == 1

        # 执行并验证顺序执行（由于限制为1）
        start_time = time.time()
        result = await processor.execute_parallel(
            agent_tasks,
            "test_canvas.canvas",
            timeout=30
        )
        execution_time = time.time() - start_time

        assert result["status"] == "completed"
        # 由于并发限制为1，执行时间应该较长
        assert execution_time > 1.5  # 3个任务顺序执行

    def test_configuration_validation(self):
        """测试配置验证"""
        selector = ReviewBoardAgentSelector()

        # 验证默认配置
        config = selector.config
        assert "recommendations" in config
        assert "quality_weights" in config

        # 验证推荐配置
        rec_config = config["recommendations"]
        assert rec_config["max_recommendations"] > 0
        assert 0 <= rec_config["default_confidence_threshold"] <= 1
        assert 0 <= rec_config["min_confidence_threshold"] <= 1

        # 验证质量权重
        weights = config["quality_weights"]
        assert sum(weights.values()) == 1.0  # 权重总和应为1


# 集成测试类
class TestEndToEndIntegration:
    """端到端集成测试"""

    @pytest.mark.asyncio
    async def test_full_workflow_integration(self):
        """测试完整工作流集成"""
        # 1. 创建组件
        selector = ReviewBoardAgentSelector()
        processor = ConcurrentAgentProcessor(max_concurrent=3)

        # 2. 分析理解质量
        node_text = "我对逻辑门的理解是：AND门只有当所有输入都为1时输出才为1"
        quality_analysis = await selector.analyze_understanding_quality_advanced(node_text)

        # 3. 获取多Agent推荐
        recommendations = await selector.recommend_multiple_agents(
            quality_analysis,
            max_recommendations=3
        )

        # 4. 准备并行执行任务
        agent_tasks = []
        for agent_rec in recommendations["recommended_agents"]:
            agent_tasks.append({
                "agent_name": agent_rec["agent_name"],
                "node_id": "integration-test-node",
                "node_text": node_text,
                "confidence_score": agent_rec["confidence_score"]
            })

        # 5. 并行执行
        execution_result = await processor.execute_parallel(
            agent_tasks,
            "integration_test_canvas.canvas",
            timeout=10
        )

        # 6. 验证完整流程
        assert quality_analysis["overall_quality"] > 0
        assert len(recommendations["recommended_agents"]) > 0
        assert execution_result["status"] == "completed"
        assert len(execution_result["results"]) == len(agent_tasks)

        # 7. 验证性能指标更新
        metrics = processor.get_performance_metrics()
        assert metrics["total_executions"] >= len(agent_tasks)

    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self):
        """测试错误恢复工作流"""
        processor = ConcurrentAgentProcessor(max_concurrent=2)

        # 创建包含失败任务的混合任务列表
        agent_tasks = [
            {
                "agent_name": "valid-agent",
                "node_id": "node-1",
                "node_text": "有效内容"
            },
            {
                "agent_name": "",  # 无效Agent名称
                "node_id": "node-2",
                "node_text": "无效Agent测试"
            },
            {
                "agent_name": "another-valid-agent",
                "node_id": "node-3",
                "node_text": "另一个有效内容"
            }
        ]

        # 执行并处理错误
        result = await processor.execute_parallel(
            agent_tasks,
            "error_test_canvas.canvas",
            timeout=10
        )

        # 验证部分成功
        assert result["status"] == "completed"
        assert result["execution_summary"]["successful_tasks"] >= 1
        assert result["execution_summary"]["failed_tasks"] >= 1

        # 验证错误信息
        failed_results = [r for r in result["results"] if not r["success"]]
        assert len(failed_results) > 0
        assert "error" in failed_results[0]


if __name__ == "__main__":
    # 运行测试
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--durations=10"
    ])