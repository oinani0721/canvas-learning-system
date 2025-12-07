"""
测试 Agent Instance Pool 模块

测试GLM实例池管理框架的各项功能，包括：
- 实例创建和管理
- 实例生命周期
- 并发安全性
- 与Canvas架构集成

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-24
"""

import asyncio
import os

# 导入被测试的模块
import sys
from datetime import datetime

import pytest
import pytest_asyncio

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_instance_pool import (
    AgentInstance,
    AgentTask,
    GLMInstancePool,
    InstanceStatus,
    ProcessWorker,
    TaskPriority,
    get_instance_pool,
    start_instance_pool,
    stop_instance_pool,
)


class TestAgentInstance:
    """测试AgentInstance数据模型"""

    def test_instance_creation(self):
        """测试实例创建"""
        instance = AgentInstance(
            instance_id="test-001",
            agent_type="clarification-path",
            status=InstanceStatus.IDLE
        )

        assert instance.instance_id == "test-001"
        assert instance.agent_type == "clarification-path"
        assert instance.status == InstanceStatus.IDLE
        assert instance.task is None
        assert instance.process_id is None
        assert instance.memory_usage == 0.0
        assert isinstance(instance.created_at, datetime)
        assert isinstance(instance.last_activity, datetime)

    def test_instance_to_dict(self):
        """测试实例转换为字典"""
        task = AgentTask(
            task_id="task-001",
            agent_type="oral-explanation",
            node_data={"concept": "测试概念"}
        )

        instance = AgentInstance(
            instance_id="test-002",
            agent_type="oral-explanation",
            status=InstanceStatus.RUNNING,
            task=task,
            process_id=12345,
            memory_usage=1024000
        )

        data = instance.to_dict()

        assert data["instance_id"] == "test-002"
        assert data["agent_type"] == "oral-explanation"
        assert data["status"] == "running"
        assert data["task_id"] == "task-001"
        assert data["process_id"] == 12345
        assert data["memory_usage"] == 1024000
        assert "created_at" in data
        assert "last_activity" in data
        assert "uptime" in data

    def test_instance_update_activity(self):
        """测试更新活动时间"""
        instance = AgentInstance(
            instance_id="test-003",
            agent_type="memory-anchor",
            status=InstanceStatus.IDLE
        )

        old_activity = instance.last_activity
        import time
        time.sleep(0.01)  # 等待一小段时间
        instance.update_activity()

        assert instance.last_activity > old_activity

    def test_instance_uptime(self):
        """测试运行时间计算"""
        instance = AgentInstance(
            instance_id="test-004",
            agent_type="comparison-table",
            status=InstanceStatus.IDLE
        )

        uptime = instance.get_uptime()
        assert uptime >= 0
        assert uptime < 1  # 应该小于1秒


class TestAgentTask:
    """测试AgentTask数据模型"""

    def test_task_creation(self):
        """测试任务创建"""
        task = AgentTask(
            task_id="task-002",
            agent_type="scoring-agent",
            node_data={"text": "用户输入文本"}
        )

        assert task.task_id == "task-002"
        assert task.agent_type == "scoring-agent"
        assert task.node_data["text"] == "用户输入文本"
        assert task.user_context is None
        assert task.priority == TaskPriority.NORMAL
        assert isinstance(task.created_at, datetime)

    def test_task_to_dict(self):
        """测试任务转换为字典"""
        task = AgentTask(
            task_id="task-003",
            agent_type="verification-question-agent",
            node_data={"concept": "逆否命题"},
            user_context="请详细解释",
            priority=TaskPriority.HIGH
        )

        data = task.to_dict()

        assert data["task_id"] == "task-003"
        assert data["agent_type"] == "verification-question-agent"
        assert data["node_data"]["concept"] == "逆否命题"
        assert data["user_context"] == "请详细解释"
        assert data["priority"] == TaskPriority.HIGH.value
        assert "created_at" in data


class TestProcessWorker:
    """测试ProcessWorker类"""

    @pytest.mark.asyncio
    async def test_worker_task_execution(self):
        """测试工作器执行任务"""
        worker = ProcessWorker(
            instance_id="worker-001",
            agent_type="test-agent"
        )

        task = AgentTask(
            task_id="task-004",
            agent_type="test-agent",
            node_data={"test": "data"}
        )

        result = await worker.run_task(task)

        assert result["task_id"] == "task-004"
        assert result["instance_id"] == "worker-001"
        assert result["status"] == "completed"
        assert "result" in result
        assert "execution_time" in result
        assert not worker.is_running
        assert worker.current_task is None

    @pytest.mark.asyncio
    async def test_worker_error_handling(self):
        """测试工作器错误处理"""
        worker = ProcessWorker(
            instance_id="worker-002",
            agent_type="test-agent"
        )

        # 创建一个会导致错误的任务
        task = AgentTask(
            task_id="task-error",
            agent_type="test-agent",
            node_data=None  # 故意传入None
        )

        # 由于我们的简化实现不会抛出错误，这里只测试基本流程
        result = await worker.run_task(task)
        assert result["task_id"] == "task-error"
        assert result["instance_id"] == "worker-002"


class TestGLMInstancePool:
    """测试GLMInstancePool核心类"""

    @pytest_asyncio.fixture
    async def pool(self):
        """创建测试用的实例池"""
        pool = GLMInstancePool(max_concurrent_instances=3)
        await pool.start()
        yield pool
        await pool.stop()

    @pytest.mark.asyncio
    async def test_pool_start_stop(self):
        """测试实例池启动和停止"""
        pool = GLMInstancePool()
        assert not pool.is_running

        await pool.start()
        assert pool.is_running

        await pool.stop()
        assert not pool.is_running

    @pytest.mark.asyncio
    async def test_create_instance(self, pool):
        """测试创建实例"""
        instance_id = await pool.create_instance("clarification-path")

        assert instance_id in pool.active_instances
        assert instance_id in pool.instance_workers

        instance = pool.active_instances[instance_id]
        assert instance.agent_type == "clarification-path"
        assert instance.status == InstanceStatus.IDLE

    @pytest.mark.asyncio
    async def test_max_instances_limit(self, pool):
        """测试最大实例数限制"""
        # 创建最大数量的实例
        instance_ids = []
        for i in range(pool.max_concurrent_instances):
            instance_id = await pool.create_instance(f"agent-type-{i}")
            instance_ids.append(instance_id)

        # 尝试创建超出限制的实例
        with pytest.raises(ValueError, match="Maximum concurrent instances"):
            await pool.create_instance("extra-agent")

    @pytest.mark.asyncio
    async def test_submit_task(self, pool):
        """测试提交任务"""
        # 创建实例
        instance_id = await pool.create_instance("test-agent")

        # 创建任务
        task = AgentTask(
            task_id="task-submit",
            agent_type="test-agent",
            node_data={"test": "data"}
        )

        # 提交任务
        success = await pool.submit_task(instance_id, task)
        assert success

        # 检查实例状态
        instance = pool.active_instances[instance_id]
        assert instance.status == InstanceStatus.IDLE  # 任务已完成，回到空闲状态

    @pytest.mark.asyncio
    async def test_submit_task_to_nonexistent_instance(self, pool):
        """测试向不存在的实例提交任务"""
        task = AgentTask(
            task_id="task-invalid",
            agent_type="test-agent",
            node_data={"test": "data"}
        )

        success = await pool.submit_task("nonexistent-id", task)
        assert not success

    @pytest.mark.asyncio
    async def test_get_instance_status(self, pool):
        """测试获取实例状态"""
        instance_id = await pool.create_instance("test-agent")
        status = await pool.get_instance_status(instance_id)

        assert status is not None
        assert status["instance_id"] == instance_id
        assert status["agent_type"] == "test-agent"
        assert status["status"] == "idle"

        # 测试不存在的实例
        status = await pool.get_instance_status("nonexistent")
        assert status is None

    @pytest.mark.asyncio
    async def test_shutdown_instance(self, pool):
        """测试关闭实例"""
        instance_id = await pool.create_instance("test-agent")
        assert instance_id in pool.active_instances

        success = await pool.shutdown_instance(instance_id)
        assert success
        assert instance_id not in pool.active_instances
        assert instance_id not in pool.instance_workers

    @pytest.mark.asyncio
    async def test_get_pool_status(self, pool):
        """测试获取实例池状态"""
        # 创建几个实例
        await pool.create_instance("agent-1")
        await pool.create_instance("agent-2")

        status = await pool.get_pool_status()

        assert status["pool_status"] == "running"
        assert status["max_instances"] == 3
        assert status["active_instances"] == 2
        assert "instance_status_counts" in status
        assert "performance_metrics" in status
        assert "instances" in status
        assert len(status["instances"]) == 2

    @pytest.mark.asyncio
    async def test_concurrent_instance_creation(self, pool):
        """测试并发创建实例"""
        # 并发创建多个实例
        tasks = [
            pool.create_instance(f"agent-{i}")
            for i in range(3)
        ]

        instance_ids = await asyncio.gather(*tasks)

        # 验证所有实例都创建成功
        for instance_id in instance_ids:
            assert instance_id in pool.active_instances
            assert pool.active_instances[instance_id].status == InstanceStatus.IDLE

    @pytest.mark.asyncio
    async def test_instance_lifecycle(self, pool):
        """测试实例完整生命周期"""
        # 1. 创建实例
        instance_id = await pool.create_instance("lifecycle-agent")
        instance = pool.active_instances[instance_id]
        assert instance.status == InstanceStatus.IDLE

        # 2. 提交任务
        task = AgentTask(
            task_id="lifecycle-task",
            agent_type="lifecycle-agent",
            node_data={"test": "lifecycle"}
        )
        success = await pool.submit_task(instance_id, task)
        assert success

        # 3. 检查状态
        status = await pool.get_instance_status(instance_id)
        assert status["status"] == "idle"  # 任务已完成

        # 4. 关闭实例
        success = await pool.shutdown_instance(instance_id)
        assert success
        assert instance_id not in pool.active_instances


class TestPoolIntegration:
    """测试实例池与Canvas架构集成"""

    @pytest.mark.asyncio
    async def test_singleton_pool(self):
        """测试单例模式"""
        pool1 = get_instance_pool()
        pool2 = get_instance_pool()
        assert pool1 is pool2

    @pytest.mark.asyncio
    async def test_start_stop_global_pool(self):
        """测试启动和停止全局实例池"""
        await start_instance_pool()
        pool = get_instance_pool()
        assert pool.is_running

        await stop_instance_pool()
        # 注意：停止后全局变量会被设为None
        # 所以需要重新获取来验证
        pool2 = get_instance_pool()
        assert not pool2.is_running

    @pytest.mark.asyncio
    async def test_integration_with_canvas_orchestrator(self):
        """测试与CanvasOrchestrator的集成"""
        # 由于CanvasOrchestrator需要canvas文件，这里只测试导入
        try:
            # 先添加当前目录到Python路径
            import os
            import sys
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if current_dir not in sys.path:
                sys.path.insert(0, current_dir)

            from canvas_utils import AGENT_POOL_ENABLED
            assert AGENT_POOL_ENABLED  # 确保实例池模块已启用
        except ImportError as e:
            pytest.skip(f"Canvas utils not available: {e}")


class TestPerformanceConstraints:
    """测试性能约束"""

    @pytest.mark.asyncio
    async def test_memory_usage_tracking(self):
        """测试内存使用跟踪"""
        pool = GLMInstancePool()
        await pool.start()

        # 创建实例
        instance_id = await pool.create_instance("memory-test")
        instance = pool.active_instances[instance_id]

        # 虽然没有实际进程，但可以测试内存字段
        assert instance.memory_usage >= 0

        await pool.stop()

    @pytest.mark.asyncio
    async def test_instance_timeout(self):
        """测试实例超时处理"""
        pool = GLMInstancePool()
        await pool.start()

        # 创建实例
        instance_id = await pool.create_instance("timeout-test")

        # 等待超过超时时间（简化实现中不会触发）
        await asyncio.sleep(0.1)

        status = await pool.get_instance_status(instance_id)
        assert status["status"] == "idle"  # 简化实现中不会超时

        await pool.stop()


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])
