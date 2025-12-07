# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: BackgroundTasks)
"""
BackgroundTaskManager - Manages background task lifecycle.
[Source: Story 15.5 - 异步操作和后台任务]

Features:
- Task status tracking: pending/running/completed/failed
- Task result storage and query
- Task cancellation support
- Automatic cleanup of old tasks
"""
import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Optional

from ..config import settings
from ..core.exceptions import TaskNotFoundError

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """
    任务状态枚举
    [Source: Story 15.5 AC:6 - 任务状态追踪: pending/running/completed/failed]
    """
    PENDING = "pending"      # 等待执行
    RUNNING = "running"      # 正在执行
    COMPLETED = "completed"  # 执行完成
    FAILED = "failed"        # 执行失败
    CANCELLED = "cancelled"  # 已取消


@dataclass
class TaskInfo:
    """
    任务信息数据类
    """
    task_id: str
    task_type: str
    status: TaskStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    progress: float = 0.0  # 0.0 - 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result,
            "error": self.error,
            "progress": self.progress,
            "metadata": self.metadata,
        }


class BackgroundTaskManager:
    """
    后台任务管理器
    [Source: Story 15.5 AC:4 - 实现BackgroundTaskManager管理后台任务生命周期]

    Features:
    - 任务创建和追踪
    - 任务状态查询
    - 任务取消
    - 自动清理过期任务
    """

    _instance: Optional["BackgroundTaskManager"] = None

    def __new__(cls, *args, **kwargs):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化任务管理器"""
        # 避免重复初始化
        if hasattr(self, '_initialized') and self._initialized:
            return

        self._tasks: Dict[str, TaskInfo] = {}
        self._running_futures: Dict[str, asyncio.Task] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
        self._initialized = True

        logger.info("BackgroundTaskManager initialized")

    @classmethod
    def get_instance(cls) -> "BackgroundTaskManager":
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """重置单例（仅用于测试）"""
        if cls._instance is not None:
            cls._instance._tasks.clear()
            cls._instance._running_futures.clear()
        cls._instance = None

    def _generate_task_id(self) -> str:
        """生成唯一任务ID"""
        return str(uuid.uuid4())

    async def create_task(
        self,
        task_type: str,
        func: Callable[..., Awaitable[Any]],
        *args,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        """
        创建并启动后台任务
        [Source: Story 15.5 AC:4 - create_task方法]

        Args:
            task_type: 任务类型标识
            func: 要执行的异步函数
            *args: 函数参数
            metadata: 任务元数据
            **kwargs: 函数关键字参数

        Returns:
            任务ID
        """
        task_id = self._generate_task_id()

        # 创建任务信息
        task_info = TaskInfo(
            task_id=task_id,
            task_type=task_type,
            status=TaskStatus.PENDING,
            created_at=datetime.now(),
            metadata=metadata or {}
        )
        self._tasks[task_id] = task_info

        logger.info(f"Created task {task_id} of type {task_type}")

        # 启动任务执行
        async def wrapped_task():
            try:
                # 更新状态为运行中
                task_info.status = TaskStatus.RUNNING
                task_info.started_at = datetime.now()
                logger.debug(f"Task {task_id} started")

                # 执行任务
                result = await func(*args, **kwargs)

                # 更新状态为完成
                task_info.status = TaskStatus.COMPLETED
                task_info.completed_at = datetime.now()
                task_info.result = result
                task_info.progress = 1.0
                logger.info(f"Task {task_id} completed successfully")

            except asyncio.CancelledError:
                # 任务被取消
                task_info.status = TaskStatus.CANCELLED
                task_info.completed_at = datetime.now()
                logger.warning(f"Task {task_id} was cancelled")
                raise

            except Exception as e:
                # 任务失败
                task_info.status = TaskStatus.FAILED
                task_info.completed_at = datetime.now()
                task_info.error = str(e)
                logger.error(f"Task {task_id} failed: {e}")

            finally:
                # 清理running futures
                self._running_futures.pop(task_id, None)

        # 创建asyncio.Task
        future = asyncio.create_task(wrapped_task())
        self._running_futures[task_id] = future

        return task_id

    def get_task_status(self, task_id: str) -> TaskInfo:
        """
        获取任务状态
        [Source: Story 15.5 AC:4 - get_task_status方法]

        Args:
            task_id: 任务ID

        Returns:
            任务信息

        Raises:
            TaskNotFoundError: 任务不存在
        """
        if task_id not in self._tasks:
            raise TaskNotFoundError(task_id)

        return self._tasks[task_id]

    def get_task_status_dict(self, task_id: str) -> Dict[str, Any]:
        """获取任务状态字典"""
        return self.get_task_status(task_id).to_dict()

    async def cancel_task(self, task_id: str) -> bool:
        """
        取消任务
        [Source: Story 15.5 AC:4 - cancel_task方法]

        Args:
            task_id: 任务ID

        Returns:
            是否成功取消

        Raises:
            TaskNotFoundError: 任务不存在
        """
        if task_id not in self._tasks:
            raise TaskNotFoundError(task_id)

        task_info = self._tasks[task_id]

        # 只有pending或running状态的任务可以取消
        if task_info.status not in (TaskStatus.PENDING, TaskStatus.RUNNING):
            logger.warning(f"Cannot cancel task {task_id} in status {task_info.status}")
            return False

        # 取消正在运行的future
        if task_id in self._running_futures:
            future = self._running_futures[task_id]
            future.cancel()
            logger.info(f"Cancelled running task {task_id}")
            return True

        # pending状态直接标记为取消
        task_info.status = TaskStatus.CANCELLED
        task_info.completed_at = datetime.now()
        logger.info(f"Cancelled pending task {task_id}")
        return True

    def update_progress(self, task_id: str, progress: float) -> None:
        """
        更新任务进度

        Args:
            task_id: 任务ID
            progress: 进度值 (0.0 - 1.0)
        """
        if task_id in self._tasks:
            self._tasks[task_id].progress = min(max(progress, 0.0), 1.0)

    def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        task_type: Optional[str] = None
    ) -> List[TaskInfo]:
        """
        列出任务

        Args:
            status: 按状态筛选
            task_type: 按类型筛选

        Returns:
            任务列表
        """
        tasks = list(self._tasks.values())

        if status is not None:
            tasks = [t for t in tasks if t.status == status]

        if task_type is not None:
            tasks = [t for t in tasks if t.task_type == task_type]

        return tasks

    async def cleanup_old_tasks(self, max_age_hours: int = 24) -> int:
        """
        清理过期任务

        Args:
            max_age_hours: 任务最大保留时间（小时）

        Returns:
            清理的任务数量
        """
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        cleaned = 0

        task_ids_to_remove = []
        for task_id, task_info in self._tasks.items():
            # 只清理已完成或已失败的任务
            if task_info.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
                if task_info.completed_at and task_info.completed_at < cutoff_time:
                    task_ids_to_remove.append(task_id)

        for task_id in task_ids_to_remove:
            del self._tasks[task_id]
            cleaned += 1

        if cleaned > 0:
            logger.info(f"Cleaned up {cleaned} old tasks")

        return cleaned

    async def start_cleanup_scheduler(self) -> None:
        """启动定期清理任务"""
        async def cleanup_loop():
            while True:
                try:
                    await asyncio.sleep(settings.TASK_CLEANUP_INTERVAL_SECONDS)
                    await self.cleanup_old_tasks()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Cleanup error: {e}")

        self._cleanup_task = asyncio.create_task(cleanup_loop())
        logger.info("Started background task cleanup scheduler")

    async def stop_cleanup_scheduler(self) -> None:
        """停止定期清理任务"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
            logger.info("Stopped background task cleanup scheduler")

    async def cleanup(self) -> None:
        """
        清理资源
        [Source: Story 15.5 AC:8 - 所有服务支持资源清理]
        """
        # 停止清理调度器
        await self.stop_cleanup_scheduler()

        # 取消所有运行中的任务
        for task_id, future in list(self._running_futures.items()):
            future.cancel()
            logger.debug(f"Cancelled task {task_id}")

        # 等待任务取消完成
        if self._running_futures:
            await asyncio.gather(
                *self._running_futures.values(),
                return_exceptions=True
            )

        self._tasks.clear()
        self._running_futures.clear()
        self._initialized = False

        logger.info("BackgroundTaskManager cleanup completed")
