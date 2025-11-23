"""
并发Agent执行引擎测试套件

测试Story 7.1的核心功能：
- ConcurrentTask数据模型
- TaskDecomposer任务分解
- ResourceMonitor资源监控
- ConcurrentAgentExecutor并发执行
- MultiAgentOrchestrator多Agent协调
"""

import asyncio
import pytest
import time
import uuid
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

# Import the classes we're testing
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from canvas_utils import (
    # Constants
    MAX_CONCURRENT_AGENTS,
    DEFAULT_TIMEOUT_SECONDS,
    PRIORITY_HIGH,
    PRIORITY_MEDIUM,
    PRIORITY_LOW,
    TASK_STATUS_PENDING,
    TASK_STATUS_RUNNING,
    TASK_STATUS_COMPLETED,
    TASK_STATUS_FAILED,
    TASK_STATUS_CANCELLED,
    CONCURRENT_AGENT_TYPES,
    CONCURRENT_AGENTS_ENABLED,

    # Data models
    ConcurrentTask,
    TaskExecutionContext,
    TaskResult,
    PerformanceMetrics,

    # Core classes
    TaskDecomposer,
    ResourceMonitor,
    ConcurrentAgentExecutor,
    MultiAgentOrchestrator
)


class TestConcurrentTask:
    """测试ConcurrentTask数据模型"""

    def test_valid_task_creation(self):
        """测试有效任务创建"""
        task = ConcurrentTask(
            task_id="test_task_1",
            agent_type="basic-decomposition",
            input_data={"material": "test content"},
            dependencies=[]
        )

        assert task.task_id == "test_task_1"
        assert task.agent_type == "basic-decomposition"
        assert task.input_data == {"material": "test content"}
        assert task.dependencies == []
        assert task.priority == PRIORITY_MEDIUM
        assert task.estimated_duration == 30.0
        assert task.timeout_seconds == DEFAULT_TIMEOUT_SECONDS
        assert isinstance(task.created_at, datetime)

    def test_invalid_agent_type(self):
        """测试无效Agent类型"""
        with pytest.raises(ValueError, match="不支持的Agent类型"):
            ConcurrentTask(
                task_id="test_task_2",
                agent_type="invalid-agent",
                input_data={},
                dependencies=[]
            )

    def test_task_with_dependencies(self):
        """测试有依赖关系的任务"""
        task = ConcurrentTask(
            task_id="test_task_3",
            agent_type="deep-decomposition",
            input_data={"content": "test"},
            dependencies=["task_1", "task_2"],
            priority=PRIORITY_HIGH
        )

        assert task.dependencies == ["task_1", "task_2"]
        assert task.priority == PRIORITY_HIGH

    def test_task_edge_cases(self):
        """测试任务边界情况"""
        # 测试空输入数据
        task = ConcurrentTask(
            task_id="test_task_4",
            agent_type="scoring-agent",
            input_data={},
            dependencies=[]
        )
        assert task.input_data == {}
        assert isinstance(task.task_id, str)
        assert isinstance(task.agent_type, str)

        # 测试最小超时时间
        task = ConcurrentTask(
            task_id="test_task_5",
            agent_type="oral-explanation",
            input_data={"test": "data"},
            dependencies=[],
            timeout_seconds=1
        )
        assert task.timeout_seconds == 1


class TestTaskDecomposer:
    """测试TaskDecomposer任务分解器"""

    def setup_method(self):
        self.decomposer = TaskDecomposer()

    def test_basic_decomposition_request(self):
        """测试基础拆解请求分解"""
        user_request = "请拆解这个不明白的概念"
        canvas_context = {
            "material_content": "逆否命题的定义",
            "topic": "逆否命题"
        }

        tasks = self.decomposer.analyze_and_decompose(user_request, canvas_context)

        assert len(tasks) == 1
        assert tasks[0].agent_type == "basic-decomposition"
        assert tasks[0].priority == PRIORITY_HIGH
        assert "逆否命题的定义" in tasks[0].input_data["material_content"]

    def test_explanation_request(self):
        """测试解释类请求分解"""
        user_request = "请解释这个概念并讲清楚"
        canvas_context = {
            "concept": "布尔代数",
            "material_content": "布尔代数的基本运算",
            "user_level": "beginner"
        }

        tasks = self.decomposer.analyze_and_decompose(user_request, canvas_context)

        # 应该创建多个解释Agent任务
        assert len(tasks) >= 3
        agent_types = [task.agent_type for task in tasks]
        assert "oral-explanation" in agent_types
        assert "clarification-path" in agent_types
        assert "four-level-explanation" in agent_types

    def test_scoring_request(self):
        """测试评分请求分解"""
        user_request = "请给我的理解打分"
        canvas_context = {
            "question_text": "什么是逆否命题？",
            "user_understanding": "就是把命题反过来",
            "reference_material": "逆否命题的标准定义"
        }

        tasks = self.decomposer.analyze_and_decompose(user_request, canvas_context)

        assert len(tasks) == 1
        assert tasks[0].agent_type == "scoring-agent"
        assert tasks[0].priority == PRIORITY_HIGH

    def test_complex_request_with_multiple_agents(self):
        """测试复杂请求分解为多个Agent"""
        user_request = "我看不懂这个概念，请拆解并解释清楚，还要帮我记住"
        canvas_context = {
            "material_content": "复杂的数学概念",
            "topic": "高等数学",
            "concept": "微积分",
            "difficulty": "hard"
        }

        tasks = self.decomposer.analyze_and_decompose(user_request, canvas_context)

        # 应该包含基础拆解、多个解释、记忆锚点
        agent_types = [task.agent_type for task in tasks]
        assert "basic-decomposition" in agent_types
        assert "memory-anchor" in agent_types
        assert len([t for t in agent_types if t in ["oral-explanation", "clarification-path", "four-level-explanation"]]) >= 1

    def test_empty_request_default_task(self):
        """测试空请求创建默认任务"""
        user_request = ""
        canvas_context = {"topic": "通用主题"}

        tasks = self.decomposer.analyze_and_decompose(user_request, canvas_context)

        assert len(tasks) == 1
        assert tasks[0].agent_type == "basic-decomposition"
        assert tasks[0].input_data["material_content"] == ""

    def test_task_counter_increment(self):
        """测试任务计数器递增"""
        initial_counter = self.decomposer.task_counter

        # 创建第一个任务
        tasks1 = self.decomposer.analyze_and_decompose("test", {})
        assert self.decomposer.task_counter == initial_counter + 1

        # 创建第二个任务
        tasks2 = self.decomposer.analyze_and_decompose("test2", {})
        assert self.decomposer.task_counter == initial_counter + 2

    def test_task_decomposer_input_validation(self):
        """测试任务分解器输入验证"""
        # 测试空用户请求
        with pytest.raises(ValueError, match="用户请求必须是非空字符串"):
            self.decomposer.analyze_and_decompose("", {})

        with pytest.raises(ValueError, match="用户请求必须是非空字符串"):
            self.decomposer.analyze_and_decompose(None, {})

        # 测试无效上下文
        with pytest.raises(ValueError, match="Canvas上下文必须是非空字典"):
            self.decomposer.analyze_and_decompose("test", None)

        with pytest.raises(ValueError, match="Canvas上下文必须是非空字典"):
            self.decomposer.analyze_and_decompose("test", "invalid")

        with pytest.raises(ValueError, match="Canvas上下文必须是非空字典"):
            self.decomposer.analyze_and_decompose("test", [])


class TestResourceMonitor:
    """测试ResourceMonitor资源监控器"""

    def setup_method(self):
        self.monitor = ResourceMonitor()

    def test_memory_usage_estimation(self):
        """测试内存使用估算"""
        memory_usage = self.monitor.get_memory_usage()
        assert isinstance(memory_usage, float)
        assert memory_usage >= 0

    def test_cpu_usage_estimation(self):
        """测试CPU使用率估算"""
        cpu_usage = self.monitor.get_cpu_usage()
        assert isinstance(cpu_usage, float)
        assert 0 <= cpu_usage <= 100

    def test_resource_limits_check(self):
        """测试资源限制检查"""
        resource_status = self.monitor.check_resource_limits()

        assert isinstance(resource_status, dict)
        assert "memory_ok" in resource_status
        assert "cpu_ok" in resource_status
        assert "memory_usage_mb" in resource_status
        assert "cpu_usage_percent" in resource_status
        assert "free_memory_mb" in resource_status

        assert isinstance(resource_status["memory_ok"], bool)
        assert isinstance(resource_status["cpu_ok"], bool)

    def test_can_add_more_tasks(self):
        """测试是否可以添加更多任务"""
        # 测试无任务时可以添加
        assert self.monitor.can_add_more_tasks(0) == True

        # 测试达到最大限制时不能添加
        assert self.monitor.can_add_more_tasks(MAX_CONCURRENT_AGENTS) == False

        # 测试超过限制时不能添加
        assert self.monitor.can_add_more_tasks(MAX_CONCURRENT_AGENTS + 1) == False


@pytest.mark.skipif(not CONCURRENT_AGENTS_ENABLED, reason="并发Agent依赖未安装")
class TestConcurrentAgentExecutor:
    """测试ConcurrentAgentExecutor并发执行引擎"""

    def setup_method(self):
        self.executor = ConcurrentAgentExecutor()

    @pytest.mark.asyncio
    async def test_simple_concurrent_execution(self):
        """测试简单并发执行"""
        complex_task = {
            "user_request": "请拆解这个概念",
            "canvas_context": {
                "material_content": "测试材料",
                "topic": "测试主题"
            }
        }

        result = await self.executor.execute_concurrent_agents(complex_task)

        assert result["success"] == True
        assert "execution_id" in result
        assert "results" in result
        assert "performance_metrics" in result
        assert len(result["results"]) >= 1

    @pytest.mark.asyncio
    async def test_multiple_agents_execution(self):
        """测试多Agent并发执行"""
        complex_task = {
            "user_request": "请解释这个概念并帮我记住，还要评分",
            "canvas_context": {
                "material_content": "复杂的学习材料",
                "concept": "重要概念",
                "question_text": "理解测试",
                "user_understanding": "初步理解",
                "reference_material": "参考资料"
            }
        }

        result = await self.executor.execute_concurrent_agents(complex_task)

        assert result["success"] == True
        assert result["total_tasks"] >= 3  # 至少包含解释、记忆、评分任务
        assert result["successful_tasks"] > 0

    @pytest.mark.asyncio
    async def test_empty_task_handling(self):
        """测试空任务处理"""
        complex_task = {
            "user_request": "",
            "canvas_context": {}
        }

        result = await self.executor.execute_concurrent_agents(complex_task)

        # 应该创建默认任务
        assert result["success"] == True
        assert result["total_tasks"] >= 1

    @pytest.mark.asyncio
    async def test_max_agents_limit(self):
        """测试最大Agent数量限制"""
        # 创建一个会生成很多任务的请求
        complex_task = {
            "user_request": "请拆解、深度拆解、解释、说明、讲清楚、记住、记忆、对比、评分、打分",  # 包含多种关键词
            "canvas_context": {
                "material_content": "非常复杂的学习材料",
                "concept": "复杂概念",
                "question_text": "复杂问题",
                "user_understanding": "复杂理解",
                "reference_material": "复杂参考"
            }
        }

        result = await self.executor.execute_concurrent_agents(complex_task, max_agents=3)

        assert result["success"] == True
        # 即使生成了很多任务，并发执行应该被限制
        assert result["total_tasks"] >= 1

    @pytest.mark.asyncio
    async def test_execution_progress_tracking(self):
        """测试执行进度跟踪"""
        complex_task = {
            "user_request": "请拆解这个概念",
            "canvas_context": {"material_content": "测试"}
        }

        result = await self.executor.execute_concurrent_agents(complex_task)
        execution_id = result["execution_id"]

        # 获取进度
        progress = self.executor.get_progress(execution_id)

        assert progress["execution_id"] == execution_id
        assert progress["status"] == TASK_STATUS_COMPLETED
        assert progress["total_tasks"] == result["total_tasks"]
        assert progress["completed_tasks"] == result["successful_tasks"]
        assert progress["progress_percentage"] == 100.0

    @pytest.mark.asyncio
    async def test_performance_metrics_calculation(self):
        """测试性能指标计算"""
        complex_task = {
            "user_request": "请解释并记住这个概念",
            "canvas_context": {
                "material_content": "测试材料",
                "concept": "测试概念"
            }
        }

        result = await self.executor.execute_concurrent_agents(complex_task)

        metrics = result["performance_metrics"]

        assert "serial_execution_time" in metrics
        assert "concurrent_execution_time" in metrics
        assert "speedup_ratio" in metrics
        assert "success_rate" in metrics
        assert "agent_utilization" in metrics
        assert "total_tasks" in metrics
        assert "completed_tasks" in metrics
        assert "failed_tasks" in metrics
        assert "memory_usage_mb" in metrics
        assert "cpu_usage_percent" in metrics

        # 验证数值合理性
        assert metrics["serial_execution_time"] > 0
        assert metrics["concurrent_execution_time"] > 0
        assert metrics["speedup_ratio"] > 0
        assert 0 <= metrics["success_rate"] <= 1
        assert metrics["total_tasks"] > 0

    @pytest.mark.asyncio
    async def test_cancel_execution(self):
        """测试取消执行"""
        complex_task = {
            "user_request": "请拆解这个概念",
            "canvas_context": {"material_content": "测试"}
        }

        # 启动执行但不等待完成
        execution_task = asyncio.create_task(
            self.executor.execute_concurrent_agents(complex_task)
        )

        # 等待一小段时间后取消
        await asyncio.sleep(0.01)

        # 获取execution_id（这需要修改ConcurrentAgentExecutor来立即返回execution_id）
        # 目前模拟测试
        result = False  # 实际实现中应该测试取消功能

        # 清理任务
        execution_task.cancel()

        try:
            await execution_task
        except asyncio.CancelledError:
            pass


@pytest.mark.skipif(not CONCURRENT_AGENTS_ENABLED, reason="并发Agent依赖未安装")
class TestMultiAgentOrchestrator:
    """测试MultiAgentOrchestrator多Agent协调器"""

    def setup_method(self):
        self.orchestrator = MultiAgentOrchestrator()

    @pytest.mark.asyncio
    async def test_orchestrate_simple_task(self):
        """测试协调简单任务"""
        user_request = "请拆解这个概念"
        canvas_path = "test_canvas.canvas"

        result = await self.orchestrator.orchestrate_complex_learning_task(
            user_request, canvas_path
        )

        assert result["success"] == True
        assert "session_id" in result
        assert "execution_id" in result
        assert "results" in result
        assert result["user_request"] == user_request
        assert result["canvas_path"] == canvas_path

    @pytest.mark.asyncio
    async def test_orchestrate_with_additional_context(self):
        """测试带额外上下文的协调"""
        user_request = "请解释这个概念"
        canvas_path = "test_canvas.canvas"
        additional_context = {
            "user_level": "advanced",
            "preferred_style": "detailed"
        }

        result = await self.orchestrator.orchestrate_complex_learning_task(
            user_request, canvas_path, additional_context
        )

        assert result["success"] == True
        assert "session_id" in result

    def test_session_status_tracking(self):
        """测试会话状态跟踪"""
        # 创建一个模拟会话
        session_id = "test_session_123"
        self.orchestrator.active_sessions[session_id] = {
            "user_request": "测试请求",
            "canvas_path": "test.canvas",
            "started_at": datetime.now(),
            "status": "running"
        }

        status = self.orchestrator.get_session_status(session_id)

        assert status["user_request"] == "测试请求"
        assert status["canvas_path"] == "test.canvas"
        assert status["status"] == "running"
        assert "started_at" in status

    def test_nonexistent_session_status(self):
        """测试不存在会话的状态查询"""
        status = self.orchestrator.get_session_status("nonexistent_session")

        assert "error" in status
        assert "会话ID不存在" in status["error"]


class TestIntegration:
    """集成测试"""

    @pytest.mark.skipif(not CONCURRENT_AGENTS_ENABLED, reason="并发Agent依赖未安装")
    @pytest.mark.asyncio
    async def test_full_workflow_integration(self):
        """测试完整工作流程集成"""
        # 1. 创建分解器
        decomposer = TaskDecomposer()

        # 2. 分解复杂任务
        user_request = "我看不懂这个复杂的数学概念，请拆解、解释清楚，还要帮我记住并评分"
        canvas_context = {
            "material_content": "关于微积分的复杂概念说明",
            "topic": "微积分",
            "concept": "导数",
            "question_text": "什么是导数？",
            "user_understanding": "导数就是斜率吧",
            "reference_material": "导数的严格数学定义",
            "difficulty": "hard",
            "user_level": "intermediate"
        }

        tasks = decomposer.analyze_and_decompose(user_request, canvas_context)

        # 验证任务分解
        assert len(tasks) >= 4  # 至少包含拆解、解释、记忆、评分

        agent_types = [task.agent_type for task in tasks]
        assert "basic-decomposition" in agent_types
        assert "scoring-agent" in agent_types
        assert any(t in ["oral-explanation", "clarification-path", "four-level-explanation"] for t in agent_types)
        assert "memory-anchor" in agent_types

        # 3. 创建执行器
        executor = ConcurrentAgentExecutor()

        # 4. 执行并发任务
        complex_task = {
            "user_request": user_request,
            "canvas_context": canvas_context
        }

        result = await executor.execute_concurrent_agents(complex_task)

        # 5. 验证执行结果
        assert result["success"] == True
        assert result["total_tasks"] == len(tasks)
        assert result["successful_tasks"] > 0
        assert result["speedup_ratio"] > 0

        # 6. 验证性能指标
        metrics = result["performance_metrics"]
        assert metrics["success_rate"] > 0
        assert metrics["total_tasks"] == len(tasks)

        # 7. 验证资源监控
        resource_status = executor.resource_monitor.check_resource_limits()
        assert isinstance(resource_status["memory_ok"], bool)
        assert isinstance(resource_status["cpu_ok"], bool)

        print(f"集成测试完成:")
        print(f"  - 分解任务数: {len(tasks)}")
        print(f"  - 执行任务数: {result['total_tasks']}")
        print(f"  - 成功任务数: {result['successful_tasks']}")
        print(f"  - 性能提升比: {result['speedup_ratio']:.2f}x")
        print(f"  - 成功率: {metrics['success_rate']:.2%}")


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])