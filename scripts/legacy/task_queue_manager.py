"""
任务队列管理器 - Canvas学习系统

负责并行Agent处理的任务队列管理，包括：
- 多优先级队列调度
- 智能任务分发和负载均衡
- 死锁预防和背压控制
- 任务进度监控和状态跟踪

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-22
Story: 8.14 (Task 3)
"""

import asyncio
import time
import uuid
import threading
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple, Callable, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, deque
import heapq
import random
import json
from pathlib import Path


class QueueType(Enum):
    """队列类型枚举"""
    FIFO = "fifo"           # 先进先出
    PRIORITY = "priority"   # 优先级队列
    LIFO = "lifo"          # 后进先出


class TaskPriority(Enum):
    """任务优先级枚举"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4

    @classmethod
    def from_string(cls, priority_str: str) -> 'TaskPriority':
        """从字符串创建优先级对象"""
        priority_map = {
            "low": cls.LOW,
            "normal": cls.NORMAL,
            "high": cls.HIGH,
            "urgent": cls.URGENT
        }
        return priority_map.get(priority_str.lower(), cls.NORMAL)


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    RETRY = "retry"


class LoadBalancingStrategy(Enum):
    """负载均衡策略"""
    ROUND_ROBIN = "round_robin"           # 轮询
    LEAST_BUSY = "least_busy"            # 最少忙碌
    WEIGHTED = "weighted"                  # 加权
    RANDOM = "random"                     # 随机


class BackPressureStrategy(Enum):
    """背压策略"""
    REJECT = "reject"                     # 拒绝新任务
    THROTTLE = "throttle"                # 节流
    QUEUE = "queue"                       # 缓冲队列


@dataclass
class TaskDefinition:
    """任务定义"""
    task_id: str = field(default_factory=lambda: f"task-{uuid.uuid4().hex[:16]}")
    execution_id: str = field(default_factory=lambda: f"exec-{uuid.uuid4().hex[:16]}")
    agent_name: str = ""
    canvas_path: str = ""
    input_data: Dict[str, Any] = field(default_factory=dict)

    # 优先级和调度
    priority: TaskPriority = TaskPriority.NORMAL
    weight: float = 1.0
    timeout_seconds: int = 120
    retry_attempts: int = 3
    retry_delay_seconds: int = 5

    # 依赖关系
    dependencies: List[str] = field(default_factory=list)
    affinity_groups: List[str] = field(default_factory=list)

    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    creation_time: float = field(default_factory=time.time)

    def __post_init__(self):
        """后处理验证"""
        if not self.agent_name:
            raise ValueError("agent_name is required")
        if not self.canvas_path:
            raise ValueError("canvas_path is required")

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        data = asdict(self)
        data["priority"] = self.priority.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskDefinition':
        """从字典创建任务定义"""
        # 处理优先级枚举
        if "priority" in data:
            data["priority"] = TaskPriority(data["priority"])

        return cls(**data)


@dataclass
class TaskExecution:
    """任务执行记录"""
    task_id: str
    execution_id: str
    agent_name: str
    status: TaskStatus = TaskStatus.PENDING

    # 时间信息
    submission_time: float = field(default_factory=time.time)
    queue_time: Optional[float] = None
    start_time: Optional[float] = None
    completion_time: Optional[float] = None

    # 执行信息
    worker_id: Optional[str] = None
    retry_count: int = 0
    timeout_count: int = 0

    # 结果和错误
    result: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    error_traceback: Optional[str] = None

    # 性能指标
    execution_duration_ms: Optional[float] = None
    queue_wait_duration_ms: Optional[float] = None

    def calculate_durations(self) -> None:
        """计算执行持续时间"""
        if self.start_time and self.completion_time:
            self.execution_duration_ms = (self.completion_time - self.start_time) * 1000

        if self.queue_time and self.start_time:
            self.queue_wait_duration_ms = (self.start_time - self.queue_time) * 1000

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        data = asdict(self)
        data["status"] = self.status.value
        return data


@dataclass
class QueueStatistics:
    """队列统计信息"""
    queue_type: str
    max_queue_size: int

    # 任务统计
    total_tasks: int = 0
    pending_tasks: int = 0
    queued_tasks: int = 0
    running_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    cancelled_tasks: int = 0
    timeout_tasks: int = 0

    # 性能统计
    average_wait_time_ms: float = 0.0
    average_execution_time_ms: float = 0.0
    throughput_tasks_per_second: float = 0.0
    queue_utilization: float = 0.0

    # 优先级分布
    priority_distribution: Dict[str, int] = field(default_factory=lambda: defaultdict(int))

    # 错误统计
    error_types: Dict[str, int] = field(default_factory=lambda: defaultdict(int))

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return asdict(self)


class WorkerInfo:
    """工作节点信息"""

    def __init__(self, worker_id: str, max_concurrent_tasks: int = 1):
        self.worker_id = worker_id
        self.max_concurrent_tasks = max_concurrent_tasks
        self.current_tasks: Set[str] = set()
        self.total_tasks_processed = 0
        self.last_activity_time = time.time()
        self.weight = 1.0
        self.affinity_groups: Set[str] = set()

    @property
    def is_available(self) -> bool:
        """是否可用"""
        return len(self.current_tasks) < self.max_concurrent_tasks

    @property
    def load_ratio(self) -> float:
        """负载比例"""
        return len(self.current_tasks) / self.max_concurrent_tasks

    def add_task(self, task_id: str) -> None:
        """添加任务"""
        self.current_tasks.add(task_id)
        self.last_activity_time = time.time()
        self.total_tasks_processed += 1

    def remove_task(self, task_id: str) -> None:
        """移除任务"""
        self.current_tasks.discard(task_id)
        self.last_activity_time = time.time()


class PriorityTaskQueue:
    """优先级任务队列"""

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._queue = []
        self._queue_lock = asyncio.Lock()
        self._not_empty = asyncio.Condition(self._queue_lock)
        self._not_full = asyncio.Condition(self._queue_lock)

    async def put(self, task: TaskDefinition) -> bool:
        """添加任务到队列"""
        async with self._not_full:
            if len(self._queue) >= self.max_size:
                return False

            # 使用优先级堆（负值实现最大堆）
            heapq.heappush(self._queue, (-task.priority.value, time.time(), task))
            self._not_empty.notify()
            return True

    async def get(self) -> Optional[TaskDefinition]:
        """从队列获取任务"""
        async with self._not_empty:
            while not self._queue:
                await self._not_empty.wait()

            _, _, task = heapq.heappop(self._queue)
            self._not_full.notify()
            return task

    async def get_nowait(self) -> Optional[TaskDefinition]:
        """非阻塞获取任务"""
        async with self._queue_lock:
            if not self._queue:
                return None

            _, _, task = heapq.heappop(self._queue)
            return task

    def size(self) -> int:
        """获取队列大小"""
        return len(self._queue)

    def empty(self) -> bool:
        """检查队列是否为空"""
        return not self._queue

    def full(self) -> bool:
        """检查队列是否已满"""
        return len(self._queue) >= self.max_size


class FIFOTaskQueue:
    """先进先出任务队列"""

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._queue = deque()
        self._queue_lock = asyncio.Lock()
        self._not_empty = asyncio.Condition(self._queue_lock)
        self._not_full = asyncio.Condition(self._queue_lock)

    async def put(self, task: TaskDefinition) -> bool:
        """添加任务到队列"""
        async with self._not_full:
            if len(self._queue) >= self.max_size:
                return False

            self._queue.append(task)
            self._not_empty.notify()
            return True

    async def get(self) -> Optional[TaskDefinition]:
        """从队列获取任务"""
        async with self._not_empty:
            while not self._queue:
                await self._not_empty.wait()

            task = self._queue.popleft()
            self._not_full.notify()
            return task

    async def get_nowait(self) -> Optional[TaskDefinition]:
        """非阻塞获取任务"""
        async with self._queue_lock:
            if not self._queue:
                return None

            return self._queue.popleft()

    def size(self) -> int:
        """获取队列大小"""
        return len(self._queue)


class TaskQueueManager:
    """任务队列管理器主类

    提供完整的任务队列管理功能，支持多种队列类型、
    负载均衡策略和背压控制机制。
    """

    def __init__(self, config: Dict[str, Any]):
        """初始化任务队列管理器

        Args:
            config: 队列配置
        """
        self.config = config
        self.queue_type = QueueType(config.get("queue_type", "priority"))
        self.max_queue_size = config.get("max_queue_size", 1000)

        # 初始化队列
        if self.queue_type == QueueType.PRIORITY:
            self.main_queue = PriorityTaskQueue(self.max_queue_size)
        elif self.queue_type == QueueType.FIFO:
            self.main_queue = FIFOTaskQueue(self.max_queue_size)
        else:
            raise ValueError(f"不支持的队列类型: {self.queue_type}")

        # 任务执行记录
        self.task_executions: Dict[str, TaskExecution] = {}

        # 工作节点管理
        self.workers: Dict[str, WorkerInfo] = {}
        self.load_balancing_strategy = LoadBalancingStrategy(
            config.get("load_balancing_strategy", "round_robin")
        )
        self._round_robin_index = 0

        # 背压控制
        self.back_pressure_enabled = config.get("back_pressure_enabled", True)
        self.back_pressure_threshold = config.get("back_pressure_threshold", 0.8)
        self.back_pressure_strategy = BackPressureStrategy(
            config.get("back_pressure_strategy", "reject")
        )

        # 死锁检测
        self.deadlock_detection_enabled = config.get("deadlock_detection_enabled", True)
        self.deadlock_timeout_seconds = config.get("deadlock_timeout_seconds", 300)
        self.dependency_graph: Dict[str, Set[str]] = defaultdict(set)

        # 统计信息
        self.statistics = QueueStatistics(
            queue_type=self.queue_type.value,
            max_queue_size=self.max_queue_size
        )

        # 时间统计
        self._completion_times: List[float] = []
        self._wait_times: List[float] = []

        # 锁
        self._stats_lock = asyncio.Lock()
        self._workers_lock = asyncio.Lock()

    async def submit_task(self, task: TaskDefinition) -> bool:
        """提交任务到队列

        Args:
            task: 任务定义

        Returns:
            bool: 提交是否成功
        """
        # 检查背压
        if self.back_pressure_enabled:
            queue_utilization = self.main_queue.size() / self.max_queue_size
            if queue_utilization >= self.back_pressure_threshold:
                return self._handle_back_pressure(task)

        # 检查依赖关系
        if not await self._check_dependencies(task):
            return False

        # 创建任务执行记录
        execution = TaskExecution(
            task_id=task.task_id,
            execution_id=task.execution_id,
            agent_name=task.agent_name
        )
        self.task_executions[task.task_id] = execution

        # 添加到队列
        success = await self.main_queue.put(task)
        if success:
            execution.queue_time = time.time()
            execution.status = TaskStatus.QUEUED

            # 更新依赖图
            self._update_dependency_graph(task)

            # 更新统计
            await self._update_statistics("submit", task)

        return success

    def _handle_back_pressure(self, task: TaskDefinition) -> bool:
        """处理背压控制

        Args:
            task: 任务定义

        Returns:
            bool: 是否接受任务
        """
        if self.back_pressure_strategy == BackPressureStrategy.REJECT:
            return False
        elif self.back_pressure_strategy == BackPressureStrategy.THROTTLE:
            # 降低任务优先级
            if task.priority == TaskPriority.URGENT:
                task.priority = TaskPriority.HIGH
            elif task.priority == TaskPriority.HIGH:
                task.priority = TaskPriority.NORMAL
            elif task.priority == TaskPriority.NORMAL:
                task.priority = TaskPriority.LOW
            return True
        elif self.back_pressure_strategy == BackPressureStrategy.QUEUE:
            # 继续排队（但可能会有性能问题）
            return True

        return False

    async def _check_dependencies(self, task: TaskDefinition) -> bool:
        """检查任务依赖关系

        Args:
            task: 任务定义

        Returns:
            bool: 依赖是否满足
        """
        if not task.dependencies:
            return True

        for dep_task_id in task.dependencies:
            if dep_task_id not in self.task_executions:
                return False

            dep_execution = self.task_executions[dep_task_id]
            if dep_execution.status != TaskStatus.COMPLETED:
                return False

        return True

    def _update_dependency_graph(self, task: TaskDefinition) -> None:
        """更新依赖图

        Args:
            task: 任务定义
        """
        for dep_task_id in task.dependencies:
            self.dependency_graph[task.task_id].add(dep_task_id)

    async def get_next_task(self, worker_id: Optional[str] = None) -> Optional[TaskDefinition]:
        """获取下一个要执行的任务

        Args:
            worker_id: 工作节点ID

        Returns:
            Optional[TaskDefinition]: 下一个任务
        """
        # 检查死锁
        if self.deadlock_detection_enabled:
            await self._detect_deadlock()

        # 从队列获取任务
        task = await self.main_queue.get_nowait()
        if not task:
            return None

        # 分配给工作节点
        if worker_id:
            selected_worker_id = worker_id
        else:
            selected_worker_id = await self._select_worker(task)

        if selected_worker_id and selected_worker_id in self.workers:
            worker = self.workers[selected_worker_id]
            worker.add_task(task.task_id)

        # 更新执行记录
        execution = self.task_executions[task.task_id]
        execution.status = TaskStatus.RUNNING
        execution.start_time = time.time()
        execution.worker_id = selected_worker_id
        execution.calculate_durations()

        # 更新统计
        await self._update_statistics("start", task)

        return task

    async def _select_worker(self, task: TaskDefinition) -> Optional[str]:
        """选择工作节点

        Args:
            task: 任务定义

        Returns:
            Optional[str]: 选中的工作节点ID
        """
        available_workers = [
            worker_id for worker_id, worker in self.workers.items()
            if worker.is_available
        ]

        if not available_workers:
            return None

        # 根据策略选择工作节点
        if self.load_balancing_strategy == LoadBalancingStrategy.ROUND_ROBIN:
            selected = available_workers[self._round_robin_index % len(available_workers)]
            self._round_robin_index += 1
            return selected

        elif self.load_balancing_strategy == LoadBalancingStrategy.LEAST_BUSY:
            return min(available_workers, key=lambda w: self.workers[w].load_ratio)

        elif self.load_balancing_strategy == LoadBalancingStrategy.WEIGHTED:
            # 基于权重的随机选择
            weights = [self.workers[w].weight for w in available_workers]
            return random.choices(available_workers, weights=weights)[0]

        elif self.load_balancing_strategy == LoadBalancingStrategy.RANDOM:
            return random.choice(available_workers)

        return None

    async def complete_task(self, task_id: str, success: bool = True,
                           result: Optional[Dict[str, Any]] = None,
                           error_message: Optional[str] = None) -> bool:
        """标记任务完成

        Args:
            task_id: 任务ID
            success: 是否成功
            result: 执行结果
            error_message: 错误信息

        Returns:
            bool: 标记是否成功
        """
        if task_id not in self.task_executions:
            return False

        execution = self.task_executions[task_id]
        execution.completion_time = time.time()
        execution.calculate_durations()

        if success:
            execution.status = TaskStatus.COMPLETED
            if result:
                execution.result = result
        else:
            execution.status = TaskStatus.FAILED
            if error_message:
                execution.error_message = error_message

        # 从工作节点移除
        if execution.worker_id and execution.worker_id in self.workers:
            self.workers[execution.worker_id].remove_task(task_id)

        # 清理依赖图
        self._cleanup_dependency_graph(task_id)

        # 更新统计
        task = None  # 需要从原始任务定义获取
        await self._update_statistics("complete", task, success)

        return True

    async def cancel_task(self, task_id: str) -> bool:
        """取消任务

        Args:
            task_id: 任务ID

        Returns:
            bool: 取消是否成功
        """
        if task_id not in self.task_executions:
            return False

        execution = self.task_executions[task_id]

        # 只能取消未开始的任务
        if execution.status in [TaskStatus.PENDING, TaskStatus.QUEUED]:
            execution.status = TaskStatus.CANCELLED
            execution.completion_time = time.time()

            # 从工作节点移除（如果已分配）
            if execution.worker_id and execution.worker_id in self.workers:
                self.workers[execution.worker_id].remove_task(task_id)

            # 更新统计
            await self._update_statistics("cancel", None, False)

            return True

        return False

    def register_worker(self, worker_id: str, max_concurrent_tasks: int = 1,
                       weight: float = 1.0, affinity_groups: List[str] = None) -> None:
        """注册工作节点

        Args:
            worker_id: 工作节点ID
            max_concurrent_tasks: 最大并发任务数
            weight: 权重
            affinity_groups: 亲和组
        """
        worker = WorkerInfo(worker_id, max_concurrent_tasks)
        worker.weight = weight
        if affinity_groups:
            worker.affinity_groups = set(affinity_groups)

        self.workers[worker_id] = worker

    def unregister_worker(self, worker_id: str) -> None:
        """注销工作节点

        Args:
            worker_id: 工作节点ID
        """
        if worker_id in self.workers:
            # 重新分配任务
            worker = self.workers[worker_id]
            for task_id in list(worker.current_tasks):
                # 标记任务为失败
                if task_id in self.task_executions:
                    execution = self.task_executions[task_id]
                    execution.status = TaskStatus.FAILED
                    execution.error_message = f"工作节点 {worker_id} 离线"

            del self.workers[worker_id]

    async def _detect_deadlock(self) -> None:
        """检测死锁"""
        current_time = time.time()

        for task_id, execution in self.task_executions.items():
            if execution.status == TaskStatus.RUNNING:
                # 检查是否超时
                if execution.start_time and \
                   (current_time - execution.start_time) > self.deadlock_timeout_seconds:

                    # 标记为超时
                    execution.status = TaskStatus.TIMEOUT
                    execution.timeout_count += 1

                    print(f"检测到任务超时（可能的死锁）: {task_id}")

    def _cleanup_dependency_graph(self, completed_task_id: str) -> None:
        """清理依赖图

        Args:
            completed_task_id: 已完成的任务ID
        """
        # 移除已完成的任务
        if completed_task_id in self.dependency_graph:
            del self.dependency_graph[completed_task_id]

        # 移除其他任务对该任务的依赖
        for task_id in list(self.dependency_graph.keys()):
            self.dependency_graph[task_id].discard(completed_task_id)
            if not self.dependency_graph[task_id]:
                del self.dependency_graph[task_id]

    async def _update_statistics(self, action: str, task: Optional[TaskDefinition],
                               success: bool = True) -> None:
        """更新统计信息

        Args:
            action: 操作类型
            task: 任务定义
            success: 是否成功
        """
        async with self._stats_lock:
            if action == "submit" and task:
                self.statistics.total_tasks += 1
                self.statistics.pending_tasks += 1
                self.statistics.priority_distribution[task.priority.name.lower()] += 1

            elif action == "start" and task:
                self.statistics.pending_tasks -= 1
                self.statistics.queued_tasks -= 1
                self.statistics.running_tasks += 1

            elif action == "complete":
                self.statistics.running_tasks -= 1
                if success:
                    self.statistics.completed_tasks += 1
                else:
                    self.statistics.failed_tasks += 1

            elif action == "cancel":
                self.statistics.pending_tasks -= 1
                self.statistics.cancelled_tasks += 1

            # 更新队列利用率
            self.statistics.queue_utilization = self.main_queue.size() / self.max_queue_size

            # 计算性能指标
            await self._calculate_performance_metrics()

    async def _calculate_performance_metrics(self) -> None:
        """计算性能指标"""
        if self._completion_times:
            self.statistics.average_execution_time_ms = sum(self._completion_times) / len(self._completion_times)

        if self._wait_times:
            self.statistics.average_wait_time_ms = sum(self._wait_times) / len(self._wait_times)

        # 计算吞吐量（最近60秒）
        current_time = time.time()
        recent_completions = [
            exec_time for exec_time in self._completion_times
            if (current_time - exec_time) <= 60
        ]
        self.statistics.throughput_tasks_per_second = len(recent_completions) / 60

    async def get_queue_status(self) -> Dict[str, Any]:
        """获取队列状态

        Returns:
            Dict: 队列状态信息
        """
        async with self._stats_lock:
            status = self.statistics.to_dict()

        # 添加实时状态
        status.update({
            "queue_size": self.main_queue.size(),
            "worker_count": len(self.workers),
            "available_workers": len([w for w in self.workers.values() if w.is_available]),
            "active_dependencies": len(self.dependency_graph),
            "back_pressure_active": self._is_back_pressure_active()
        })

        return status

    def _is_back_pressure_active(self) -> bool:
        """检查背压是否激活"""
        if not self.back_pressure_enabled:
            return False

        queue_utilization = self.main_queue.size() / self.max_queue_size
        return queue_utilization >= self.back_pressure_threshold

    async def get_task_execution_info(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务执行信息

        Args:
            task_id: 任务ID

        Returns:
            Optional[Dict]: 任务执行信息
        """
        if task_id not in self.task_executions:
            return None

        execution = self.task_executions[task_id]
        return execution.to_dict()

    async def get_worker_status(self) -> Dict[str, Any]:
        """获取工作节点状态

        Returns:
            Dict: 工作节点状态信息
        """
        workers_status = {}

        for worker_id, worker in self.workers.items():
            workers_status[worker_id] = {
                "current_tasks": list(worker.current_tasks),
                "current_load": worker.load_ratio,
                "is_available": worker.is_available,
                "total_tasks_processed": worker.total_tasks_processed,
                "last_activity_time": worker.last_activity_time,
                "weight": worker.weight,
                "affinity_groups": list(worker.affinity_groups)
            }

        return {
            "total_workers": len(self.workers),
            "available_workers": len([w for w in self.workers.values() if w.is_available]),
            "average_load": sum(w.load_ratio for w in self.workers.values()) / len(self.workers) if self.workers else 0,
            "workers": workers_status
        }

    async def export_queue_data(self, file_path: str) -> bool:
        """导出队列数据

        Args:
            file_path: 导出文件路径

        Returns:
            bool: 导出是否成功
        """
        try:
            data = {
                "export_timestamp": datetime.now(timezone.utc).isoformat(),
                "queue_type": self.queue_type.value,
                "max_queue_size": self.max_queue_size,
                "statistics": self.statistics.to_dict(),
                "task_executions": {
                    task_id: execution.to_dict()
                    for task_id, execution in self.task_executions.items()
                },
                "workers": await self.get_worker_status(),
                "dependency_graph": {
                    task_id: list(deps)
                    for task_id, deps in self.dependency_graph.items()
                }
            }

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            return True
        except Exception as e:
            print(f"导出队列数据失败: {e}")
            return False

    async def clear_completed_tasks(self, older_than_hours: int = 24) -> int:
        """清理已完成的任务记录

        Args:
            older_than_hours: 清理多少小时前的记录

        Returns:
            int: 清理的记录数量
        """
        cutoff_time = time.time() - (older_than_hours * 3600)

        to_remove = []
        for task_id, execution in self.task_executions.items():
            if (execution.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED] and
                execution.completion_time and
                execution.completion_time < cutoff_time):
                to_remove.append(task_id)

        for task_id in to_remove:
            del self.task_executions[task_id]

        return len(to_remove)