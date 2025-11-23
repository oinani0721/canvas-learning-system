"""
Tests for AsyncExecutionEngine

Tests cover:
- AsyncTask creation
- AsyncExecutionEngine initialization
- Basic parallel execution (IV1)
- Semaphore concurrency limit (IV2)
- Error handling and isolation (IV3)
- Progress callback functionality
- Custom concurrency settings
- Dependency-aware execution

Author: Canvas Learning System
Date: 2025-11-04
"""

import asyncio
import pytest
from command_handlers.async_execution_engine import AsyncTask, AsyncExecutionEngine


class TestAsyncTaskCreation:
    """测试AsyncTask数据类创建"""

    def test_async_task_creation_with_minimal_params(self):
        """测试使用最小参数创建AsyncTask"""
        task = AsyncTask(
            task_id="task-1",
            agent_name="test-agent",
            node_data={"id": "node-1", "content": "test"}
        )

        assert task.task_id == "task-1"
        assert task.agent_name == "test-agent"
        assert task.node_data == {"id": "node-1", "content": "test"}
        assert task.priority == 0  # 默认值
        assert task.dependencies is None  # 默认值

    def test_async_task_creation_with_all_params(self):
        """测试使用所有参数创建AsyncTask"""
        task = AsyncTask(
            task_id="task-2",
            agent_name="oral-explanation",
            node_data={"id": "node-2", "content": "complex material"},
            priority=5,
            dependencies=["task-1"]
        )

        assert task.task_id == "task-2"
        assert task.agent_name == "oral-explanation"
        assert task.priority == 5
        assert task.dependencies == ["task-1"]

    def test_async_task_type_annotations(self):
        """测试AsyncTask类型注解正确"""
        task = AsyncTask(
            task_id="task-3",
            agent_name="test",
            node_data={}
        )

        # 验证字段存在
        assert hasattr(task, "task_id")
        assert hasattr(task, "agent_name")
        assert hasattr(task, "node_data")
        assert hasattr(task, "priority")
        assert hasattr(task, "dependencies")


class TestEngineInitialization:
    """测试AsyncExecutionEngine初始化"""

    def test_engine_initialization_default_concurrency(self):
        """测试默认并发数初始化"""
        engine = AsyncExecutionEngine()

        assert engine.max_concurrency == 12
        assert engine.semaphore._value == 12  # Semaphore初始值
        assert isinstance(engine.active_tasks, dict)
        assert isinstance(engine.completed_tasks, list)
        assert isinstance(engine.failed_tasks, list)

    def test_engine_initialization_custom_concurrency(self):
        """测试自定义并发数初始化"""
        # 测试最小值
        engine_min = AsyncExecutionEngine(max_concurrency=1)
        assert engine_min.max_concurrency == 1
        assert engine_min.semaphore._value == 1

        # 测试中间值
        engine_mid = AsyncExecutionEngine(max_concurrency=5)
        assert engine_mid.max_concurrency == 5
        assert engine_mid.semaphore._value == 5

        # 测试最大值
        engine_max = AsyncExecutionEngine(max_concurrency=20)
        assert engine_max.max_concurrency == 20
        assert engine_max.semaphore._value == 20

    def test_engine_initialization_invalid_concurrency(self):
        """测试无效并发数抛出异常"""
        # 小于1
        with pytest.raises(ValueError, match="must be between 1 and 20"):
            AsyncExecutionEngine(max_concurrency=0)

        # 大于20
        with pytest.raises(ValueError, match="must be between 1 and 20"):
            AsyncExecutionEngine(max_concurrency=21)


class TestBasicParallelExecution:
    """测试基础并行执行 (IV1)"""

    @pytest.mark.asyncio
    async def test_async_execution_engine_basic(self):
        """测试基础异步执行 - IV1验收标准"""
        engine = AsyncExecutionEngine(max_concurrency=3)

        # 创建mock executor
        async def mock_executor(task: AsyncTask):
            await asyncio.sleep(0.1)  # 模拟IO操作
            return {"task_id": task.task_id, "result": "success"}

        # 创建10个测试任务
        tasks = [
            AsyncTask(task_id=f"task-{i}", agent_name="test", node_data={})
            for i in range(10)
        ]

        # 执行
        result = await engine.execute_parallel(tasks, mock_executor)

        # 验证
        assert result["total"] == 10
        assert result["success"] == 10
        assert result["failed"] == 0
        assert len(result["results"]) == 10
        assert len(result["errors"]) == 0

    @pytest.mark.asyncio
    async def test_execution_time_is_parallel(self):
        """验证并发执行（总时间 < 0.5秒）"""
        import time

        engine = AsyncExecutionEngine(max_concurrency=5)

        async def mock_executor(task: AsyncTask):
            await asyncio.sleep(0.1)
            return {"task_id": task.task_id}

        tasks = [
            AsyncTask(task_id=f"task-{i}", agent_name="test", node_data={})
            for i in range(10)
        ]

        start_time = time.time()
        await engine.execute_parallel(tasks, mock_executor)
        elapsed_time = time.time() - start_time

        # 并发执行: 10任务 / 5并发 = 2批次 × 0.1秒 ≈ 0.2秒
        assert elapsed_time < 0.5

    @pytest.mark.asyncio
    async def test_empty_tasks_raises_error(self):
        """测试空任务列表抛出异常"""
        engine = AsyncExecutionEngine()

        async def mock_executor(task):
            return {}

        with pytest.raises(ValueError, match="cannot be empty"):
            await engine.execute_parallel([], mock_executor)

    @pytest.mark.asyncio
    async def test_invalid_executor_raises_error(self):
        """测试无效executor抛出异常"""
        engine = AsyncExecutionEngine()
        tasks = [AsyncTask(task_id="task-1", agent_name="test", node_data={})]

        with pytest.raises(TypeError, match="must be callable"):
            await engine.execute_parallel(tasks, "not_a_function")


class TestSemaphoreConcurrencyLimit:
    """测试Semaphore并发限制 (IV2)"""

    @pytest.mark.asyncio
    async def test_semaphore_concurrency_limit(self):
        """测试Semaphore并发限制 - IV2验收标准"""
        engine = AsyncExecutionEngine(max_concurrency=5)

        active_count = [0]  # 当前活跃任务数
        max_active = [0]    # 最大活跃任务数

        async def monitor_executor(task: AsyncTask):
            active_count[0] += 1
            max_active[0] = max(max_active[0], active_count[0])
            await asyncio.sleep(0.1)
            active_count[0] -= 1
            return {"task_id": task.task_id}

        tasks = [
            AsyncTask(task_id=f"task-{i}", agent_name="test", node_data={})
            for i in range(20)
        ]

        await engine.execute_parallel(tasks, monitor_executor)

        # 验证: 最大活跃数不超过5
        assert max_active[0] <= 5
        print(f"Max concurrent tasks: {max_active[0]}")

    @pytest.mark.asyncio
    async def test_semaphore_releases_on_completion(self):
        """验证Semaphore在任务完成后正确释放"""
        engine = AsyncExecutionEngine(max_concurrency=3)

        async def mock_executor(task: AsyncTask):
            await asyncio.sleep(0.05)
            return {"task_id": task.task_id}

        tasks = [
            AsyncTask(task_id=f"task-{i}", agent_name="test", node_data={})
            for i in range(6)
        ]

        result = await engine.execute_parallel(tasks, mock_executor)

        # 验证所有任务完成
        assert result["success"] == 6
        # 验证active_tasks已清空
        assert len(engine.active_tasks) == 0


class TestErrorHandling:
    """测试错误处理和任务隔离 (IV3)"""

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """测试错误处理和任务隔离 - IV3验收标准"""
        engine = AsyncExecutionEngine(max_concurrency=3)

        async def failing_executor(task: AsyncTask):
            await asyncio.sleep(0.1)
            # 第3, 7个任务失败
            if task.task_id in ["task-3", "task-7"]:
                raise ValueError(f"Simulated error for {task.task_id}")
            return {"task_id": task.task_id, "result": "success"}

        tasks = [
            AsyncTask(task_id=f"task-{i}", agent_name="test", node_data={})
            for i in range(10)
        ]

        result = await engine.execute_parallel(tasks, failing_executor)

        # 验证
        assert result["total"] == 10
        assert result["success"] == 8  # 10 - 2 = 8
        assert result["failed"] == 2
        assert len(result["errors"]) == 2

        # 验证错误信息
        error_task_ids = [err["task_id"] for err in result["errors"]]
        assert "task-3" in error_task_ids
        assert "task-7" in error_task_ids

        # 验证错误类型
        for err in result["errors"]:
            assert err["error_type"] == "ValueError"
            assert "Simulated error" in err["error"]

    @pytest.mark.asyncio
    async def test_all_tasks_fail(self):
        """测试所有任务都失败的情况"""
        engine = AsyncExecutionEngine(max_concurrency=3)

        async def always_fail_executor(task: AsyncTask):
            raise RuntimeError("All tasks fail")

        tasks = [
            AsyncTask(task_id=f"task-{i}", agent_name="test", node_data={})
            for i in range(5)
        ]

        result = await engine.execute_parallel(tasks, always_fail_executor)

        assert result["total"] == 5
        assert result["success"] == 0
        assert result["failed"] == 5
        assert len(result["errors"]) == 5


class TestProgressCallback:
    """测试进度回调功能"""

    @pytest.mark.asyncio
    async def test_progress_callback(self):
        """测试progress_callback正确工作"""
        engine = AsyncExecutionEngine(max_concurrency=3)

        callback_log = []

        async def test_callback(task_id, result, error):
            callback_log.append({
                "task_id": task_id,
                "result": result,
                "error": error
            })

        async def mock_executor(task: AsyncTask):
            await asyncio.sleep(0.05)
            return {"task_id": task.task_id, "status": "done"}

        tasks = [
            AsyncTask(task_id=f"task-{i}", agent_name="test", node_data={})
            for i in range(5)
        ]

        await engine.execute_parallel(tasks, mock_executor, test_callback)

        # 验证回调被调用5次
        assert len(callback_log) == 5

        # 验证所有回调都是成功的
        for log_entry in callback_log:
            assert log_entry["error"] is None
            assert log_entry["result"] is not None

    @pytest.mark.asyncio
    async def test_progress_callback_on_error(self):
        """测试progress_callback在错误时正确工作"""
        engine = AsyncExecutionEngine(max_concurrency=2)

        callback_log = []

        async def test_callback(task_id, result, error):
            callback_log.append({
                "task_id": task_id,
                "result": result,
                "error": error
            })

        async def failing_executor(task: AsyncTask):
            if task.task_id == "task-2":
                raise ValueError("Test error")
            return {"task_id": task.task_id}

        tasks = [
            AsyncTask(task_id=f"task-{i}", agent_name="test", node_data={})
            for i in range(4)
        ]

        await engine.execute_parallel(tasks, failing_executor, test_callback)

        # 验证回调被调用4次
        assert len(callback_log) == 4

        # 找到失败的回调
        failed_callbacks = [log for log in callback_log if log["error"] is not None]
        assert len(failed_callbacks) == 1
        assert failed_callbacks[0]["task_id"] == "task-2"
        assert "Test error" in failed_callbacks[0]["error"]


class TestDependencyAwareExecution:
    """测试依赖感知执行"""

    @pytest.mark.asyncio
    async def test_dependency_awareness(self):
        """测试依赖感知执行"""
        engine = AsyncExecutionEngine(max_concurrency=5)

        execution_order = []

        async def tracking_executor(task: AsyncTask):
            await asyncio.sleep(0.05)
            execution_order.append(task.task_id)
            return {"task_id": task.task_id}

        # 创建有依赖关系的任务
        tasks = [
            AsyncTask(task_id="task-1", agent_name="test", node_data={}, priority=10),
            AsyncTask(task_id="task-2", agent_name="test", node_data={}, priority=5, dependencies=["task-1"]),
            AsyncTask(task_id="task-3", agent_name="test", node_data={}, priority=3, dependencies=["task-2"]),
            AsyncTask(task_id="task-4", agent_name="test", node_data={}, priority=8),  # 无依赖
        ]

        result = await engine.execute_with_dependency_awareness(tasks, tracking_executor)

        # 验证所有任务成功
        assert result["success"] == 4
        assert result["failed"] == 0

        # 验证依赖关系：task-2必须在task-1之后，task-3必须在task-2之后
        task1_idx = execution_order.index("task-1")
        task2_idx = execution_order.index("task-2")
        task3_idx = execution_order.index("task-3")

        assert task2_idx > task1_idx
        assert task3_idx > task2_idx

    @pytest.mark.asyncio
    async def test_independent_tasks_run_parallel(self):
        """测试无依赖的任务可并发执行"""
        engine = AsyncExecutionEngine(max_concurrency=10)

        import time

        async def mock_executor(task: AsyncTask):
            await asyncio.sleep(0.1)
            return {"task_id": task.task_id}

        # 5个无依赖的任务
        tasks = [
            AsyncTask(task_id=f"task-{i}", agent_name="test", node_data={})
            for i in range(5)
        ]

        start_time = time.time()
        await engine.execute_with_dependency_awareness(tasks, mock_executor)
        elapsed_time = time.time() - start_time

        # 无依赖任务应并发执行，时间应接近0.1秒而非0.5秒
        assert elapsed_time < 0.3


class TestCustomConcurrency:
    """测试自定义并发数"""

    @pytest.mark.asyncio
    async def test_custom_concurrency(self):
        """测试自定义并发数 (测试1, 5, 20)"""
        async def mock_executor(task: AsyncTask):
            await asyncio.sleep(0.05)
            return {"task_id": task.task_id}

        tasks = [
            AsyncTask(task_id=f"task-{i}", agent_name="test", node_data={})
            for i in range(10)
        ]

        # 测试concurrency=1
        engine_1 = AsyncExecutionEngine(max_concurrency=1)
        result_1 = await engine_1.execute_parallel(tasks, mock_executor)
        assert result_1["success"] == 10

        # 测试concurrency=5
        engine_5 = AsyncExecutionEngine(max_concurrency=5)
        result_5 = await engine_5.execute_parallel(tasks, mock_executor)
        assert result_5["success"] == 10

        # 测试concurrency=20
        engine_20 = AsyncExecutionEngine(max_concurrency=20)
        result_20 = await engine_20.execute_parallel(tasks, mock_executor)
        assert result_20["success"] == 10
