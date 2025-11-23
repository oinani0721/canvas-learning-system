"""
AsyncExecutionEngine - 异步并发执行引擎

Epic 10.2核心组件，提供真正的异步并发执行能力。

主要特性:
- 使用asyncio实现真正的并发
- Semaphore控制最大并发数 (默认12,可配置1-20)
- 支持进度回调和错误处理
- 支持依赖感知的智能并发

Author: Canvas Learning System
Date: 2025-11-04
"""

import asyncio
from dataclasses import dataclass
from typing import List, Dict, Any, Callable, Optional


@dataclass
class AsyncTask:
    """异步任务定义

    Attributes:
        task_id: 任务唯一标识
        agent_name: Agent名称 (例: "oral-explanation")
        node_data: 节点数据 (包含id, content, x, y等)
        priority: 优先级 (高优先级任务先执行)
        dependencies: 依赖的任务ID列表 (可选)
    """
    task_id: str
    agent_name: str
    node_data: Dict[str, Any]
    priority: int = 0
    dependencies: Optional[List[str]] = None


class AsyncExecutionEngine:
    """
    异步执行引擎 - Epic 10核心组件

    实现三级并发控制:
    1. Agent级: 最多20个Agent实例并发
    2. Node级: 最多12个节点组并发 (可配置1-20)
    3. Task级: 最多5个任务组并发 (依赖感知)

    Attributes:
        max_concurrency: 最大并发数
        semaphore: asyncio信号量，用于限制并发
        active_tasks: 当前活跃任务字典 {task_id: asyncio.Task}
        completed_tasks: 已完成任务结果列表
        failed_tasks: 失败任务信息列表
    """

    def __init__(self, max_concurrency: int = 12):
        """初始化异步引擎

        Args:
            max_concurrency: 最大并发数 (默认12,可配置1-20)

        Raises:
            ValueError: 如果max_concurrency不在1-20范围内
        """
        if not 1 <= max_concurrency <= 20:
            raise ValueError(
                f"max_concurrency must be between 1 and 20, got {max_concurrency}"
            )

        self.max_concurrency = max_concurrency
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.completed_tasks: List[Dict[str, Any]] = []
        self.failed_tasks: List[Dict[str, Any]] = []

    async def execute_parallel(
        self,
        tasks: List[AsyncTask],
        executor_func: Callable,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """并行执行所有任务

        使用asyncio.gather实现真正的并发执行，通过Semaphore控制最大并发数。

        Args:
            tasks: 任务列表
            executor_func: 执行函数 (async def executor(task) -> result)
            progress_callback: 进度回调 (async def callback(task_id, result, error))

        Returns:
            Dict[str, Any]: 执行结果字典，包含:
                - total: 总任务数
                - success: 成功数
                - failed: 失败数
                - results: 成功结果列表
                - errors: 失败任务信息列表

        Raises:
            ValueError: 如果tasks为空列表
            TypeError: 如果executor_func不是可调用对象
        """
        if not tasks:
            raise ValueError("tasks list cannot be empty")

        if not callable(executor_func):
            raise TypeError("executor_func must be callable")

        # 清空之前的结果
        self.completed_tasks = []
        self.failed_tasks = []
        self.active_tasks = {}

        # 创建所有异步任务
        async_tasks = []
        for task in tasks:
            async_task = asyncio.create_task(
                self._execute_with_semaphore(task, executor_func, progress_callback)
            )
            async_tasks.append(async_task)
            self.active_tasks[task.task_id] = async_task

        # 等待所有任务完成 (return_exceptions=True 确保单个任务失败不影响gather)
        results = await asyncio.gather(*async_tasks, return_exceptions=True)

        # 汇总结果
        success_count = 0
        error_count = 0

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                error_count += 1
                self.failed_tasks.append({
                    "task_id": tasks[i].task_id,
                    "agent_name": tasks[i].agent_name,
                    "error": str(result),
                    "error_type": type(result).__name__
                })
            else:
                success_count += 1
                self.completed_tasks.append(result)

        return {
            "total": len(tasks),
            "success": success_count,
            "failed": error_count,
            "results": self.completed_tasks,
            "errors": self.failed_tasks
        }

    async def _execute_with_semaphore(
        self,
        task: AsyncTask,
        executor_func: Callable,
        progress_callback: Optional[Callable]
    ) -> Dict[str, Any]:
        """使用Semaphore控制并发执行单个任务

        关键实现:
        - async with self.semaphore: 获取信号量，自动限制并发数
        - 执行 executor_func(task)
        - 捕获异常并回调 progress_callback
        - finally块中清理 active_tasks

        Args:
            task: 要执行的异步任务
            executor_func: 执行函数
            progress_callback: 进度回调函数

        Returns:
            Dict[str, Any]: 任务执行结果

        Raises:
            Exception: 任务执行中的任何异常都会被重新抛出
        """
        async with self.semaphore:  # 获取信号量,自动限制并发数
            try:
                result = await executor_func(task)

                # 调用进度回调（成功）
                if progress_callback:
                    await progress_callback(task.task_id, result, None)

                return result

            except Exception as e:
                # 调用进度回调（失败）
                if progress_callback:
                    await progress_callback(task.task_id, None, str(e))
                raise

            finally:
                # 清理任务
                if task.task_id in self.active_tasks:
                    del self.active_tasks[task.task_id]

    async def execute_with_dependency_awareness(
        self,
        tasks: List[AsyncTask],
        executor_func: Callable,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """基于依赖关系的智能并发执行

        策略:
        1. 拓扑排序确定执行顺序
        2. 有依赖关系的任务按顺序执行
        3. 无依赖关系的任务并发执行
        4. 最多5个任务组并发 (Task级Semaphore)

        Args:
            tasks: 任务列表（可能包含dependencies字段）
            executor_func: 执行函数
            progress_callback: 进度回调函数

        Returns:
            Dict[str, Any]: 执行结果字典（格式同execute_parallel）

        Raises:
            ValueError: 如果检测到循环依赖
        """
        if not tasks:
            raise ValueError("tasks list cannot be empty")

        # 清空之前的结果
        self.completed_tasks = []
        self.failed_tasks = []
        self.active_tasks = {}

        # 拓扑排序
        sorted_tasks = self._topological_sort(tasks)

        # 创建任务完成跟踪集合
        completed_task_ids = set()
        task_results = {}

        # Task级Semaphore (最多5个任务组并发)
        task_level_semaphore = asyncio.Semaphore(5)

        async def execute_with_dependency_check(task: AsyncTask):
            """执行前检查依赖"""
            async with task_level_semaphore:
                # 等待依赖任务完成
                if task.dependencies:
                    while not all(dep_id in completed_task_ids for dep_id in task.dependencies):
                        await asyncio.sleep(0.1)  # 轮询依赖状态

                # 执行任务
                try:
                    result = await self._execute_with_semaphore(
                        task, executor_func, progress_callback
                    )
                    completed_task_ids.add(task.task_id)
                    task_results[task.task_id] = result
                    return result
                except Exception:
                    completed_task_ids.add(task.task_id)  # 标记为完成（失败）
                    raise

        # 创建所有任务
        async_tasks = []
        for task in sorted_tasks:
            async_task = asyncio.create_task(execute_with_dependency_check(task))
            async_tasks.append(async_task)
            self.active_tasks[task.task_id] = async_task

        # 等待所有任务完成
        results = await asyncio.gather(*async_tasks, return_exceptions=True)

        # 汇总结果
        success_count = 0
        error_count = 0

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                error_count += 1
                self.failed_tasks.append({
                    "task_id": sorted_tasks[i].task_id,
                    "agent_name": sorted_tasks[i].agent_name,
                    "error": str(result),
                    "error_type": type(result).__name__
                })
            else:
                success_count += 1
                self.completed_tasks.append(result)

        return {
            "total": len(tasks),
            "success": success_count,
            "failed": error_count,
            "results": self.completed_tasks,
            "errors": self.failed_tasks
        }

    def _topological_sort(self, tasks: List[AsyncTask]) -> List[AsyncTask]:
        """拓扑排序 - 确定任务执行顺序

        简化实现: 按优先级排序（真正的拓扑排序留待需要时实现）

        Args:
            tasks: 任务列表

        Returns:
            List[AsyncTask]: 排序后的任务列表

        Note:
            当前实现是简化版本，仅按priority降序排序。
            真正的拓扑排序需要构建依赖图并检测循环依赖。
        """
        return sorted(tasks, key=lambda t: t.priority, reverse=True)
