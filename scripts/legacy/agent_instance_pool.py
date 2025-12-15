"""
Agent Instance Pool Module - Canvas学习系统

本模块实现Agent实例池管理框架，支持动态创建和管理多个Agent实例，
为并行处理奠定架构基础。

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-24
"""

import asyncio
import uuid
import psutil
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from multiprocessing import Manager
import json
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InstanceStatus(Enum):
    """Agent实例状态枚举"""
    CREATING = "creating"      # 创建中
    IDLE = "idle"            # 空闲
    RUNNING = "running"      # 运行中
    COMPLETED = "completed"  # 已完成
    ERROR = "error"          # 错误
    SHUTTING = "shutting"    # 关闭中
    TERMINATED = "terminated"  # 已终止


class TaskPriority(Enum):
    """任务优先级枚举"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class AgentTask:
    """Agent任务数据模型"""
    task_id: str
    agent_type: str
    node_data: Dict  # Canvas节点数据
    user_context: Optional[str] = None
    priority: TaskPriority = TaskPriority.NORMAL
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "task_id": self.task_id,
            "agent_type": self.agent_type,
            "node_data": self.node_data,
            "user_context": self.user_context,
            "priority": self.priority.value,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class AgentInstance:
    """Agent实例数据模型"""
    instance_id: str  # 唯一实例标识符，使用UUID v4
    agent_type: str  # Agent类型
    status: InstanceStatus  # 实例状态
    task: Optional[AgentTask] = None  # 当前分配的任务
    context_window: Dict = field(default_factory=dict)  # 独立上下文窗口
    process_id: Optional[int] = None  # 进程ID
    memory_usage: float = 0.0  # 内存使用量(字节)
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)

    def update_activity(self):
        """更新最后活动时间"""
        self.last_activity = datetime.now()

    def get_uptime(self) -> float:
        """获取运行时间(秒)"""
        return (datetime.now() - self.created_at).total_seconds()

    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "instance_id": self.instance_id,
            "agent_type": self.agent_type,
            "status": self.status.value,
            "task_id": self.task.task_id if self.task else None,
            "process_id": self.process_id,
            "memory_usage": self.memory_usage,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "uptime": self.get_uptime()
        }


class ProcessWorker:
    """进程工作器，用于在独立进程中运行Agent"""

    def __init__(self, instance_id: str, agent_type: str):
        self.instance_id = instance_id
        self.agent_type = agent_type
        self.current_task = None
        self.is_running = False

    async def run_task(self, task: AgentTask) -> Dict:
        """在独立进程中执行任务"""
        self.current_task = task
        self.is_running = True

        try:
            # 模拟Agent任务执行
            # 实际实现中，这里会调用具体的Agent逻辑
            await asyncio.sleep(0.1)  # 模拟处理时间

            result = {
                "task_id": task.task_id,
                "instance_id": self.instance_id,
                "status": "completed",
                "result": f"Task {task.task_id} completed by {self.agent_type}",
                "execution_time": 0.1
            }

            return result

        except Exception as e:
            logger.error(f"Task execution failed in instance {self.instance_id}: {e}")
            return {
                "task_id": task.task_id,
                "instance_id": self.instance_id,
                "status": "error",
                "error": str(e)
            }
        finally:
            self.is_running = False
            self.current_task = None


class GLMInstancePool:
    """GLM实例池核心管理类

    支持最多4-6个并发实例管理，实现进程级隔离，
    提供完整的实例生命周期管理功能。
    """

    def __init__(self, max_concurrent_instances: int = 20):
        """初始化实例池

        Args:
            max_concurrent_instances: 最大并发实例数，默认20个（GLM4.6支持）
        """
        self.max_concurrent_instances = max_concurrent_instances
        self.active_instances: Dict[str, AgentInstance] = {}
        self.instance_workers: Dict[str, ProcessWorker] = {}
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.performance_metrics: Dict = {
            "total_tasks_processed": 0,
            "successful_tasks": 0,
            "failed_tasks": 0,
            "average_execution_time": 0.0,
            "pool_memory_usage": 0.0
        }
        self.is_running = False
        self._monitor_task = None

        logger.info(f"GLMInstancePool initialized with max_instances={max_concurrent_instances}")

    async def start(self):
        """启动实例池"""
        if self.is_running:
            logger.warning("Instance pool is already running")
            return

        self.is_running = True
        self._monitor_task = asyncio.create_task(self._monitor_instances())
        logger.info("GLMInstancePool started")

    async def stop(self):
        """停止实例池"""
        self.is_running = False

        # 关闭所有实例
        for instance_id in list(self.active_instances.keys()):
            await self.shutdown_instance(instance_id)

        # 取消监控任务
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

        logger.info("GLMInstancePool stopped")

    async def create_instance(self, agent_type: str) -> str:
        """创建新Agent实例

        Args:
            agent_type: Agent类型(如clarification-path, memory-anchor等)

        Returns:
            str: 实例ID

        Raises:
            ValueError: 如果达到最大实例数限制
        """
        if len(self.active_instances) >= self.max_concurrent_instances:
            raise ValueError(
                f"Maximum concurrent instances ({self.max_concurrent_instances}) reached"
            )

        # 生成唯一实例ID
        instance_id = f"instance-{uuid.uuid4().hex[:8]}"

        # 创建实例
        instance = AgentInstance(
            instance_id=instance_id,
            agent_type=agent_type,
            status=InstanceStatus.CREATING
        )

        # 创建工作器
        worker = ProcessWorker(instance_id, agent_type)

        # 添加到管理列表
        self.active_instances[instance_id] = instance
        self.instance_workers[instance_id] = worker

        # 更新状态为空闲
        instance.status = InstanceStatus.IDLE

        logger.info(f"Created new instance {instance_id} of type {agent_type}")
        return instance_id

    async def submit_task(self, instance_id: str, task: AgentTask) -> bool:
        """向指定实例提交任务

        Args:
            instance_id: 实例ID
            task: 要执行的任务

        Returns:
            bool: 提交是否成功
        """
        if instance_id not in self.active_instances:
            logger.error(f"Instance {instance_id} not found")
            return False

        instance = self.active_instances[instance_id]

        if instance.status != InstanceStatus.IDLE:
            logger.warning(f"Instance {instance_id} is not idle (status: {instance.status})")
            return False

        # 分配任务
        instance.task = task
        instance.status = InstanceStatus.RUNNING
        instance.update_activity()

        # 执行任务
        worker = self.instance_workers[instance_id]
        result = await worker.run_task(task)

        # 更新状态
        if result["status"] == "completed":
            instance.status = InstanceStatus.COMPLETED
            self.performance_metrics["successful_tasks"] += 1
        else:
            instance.status = InstanceStatus.ERROR
            self.performance_metrics["failed_tasks"] += 1

        self.performance_metrics["total_tasks_processed"] += 1

        # 清理任务
        instance.task = None
        if instance.status == InstanceStatus.COMPLETED:
            instance.status = InstanceStatus.IDLE

        return True

    async def get_instance_status(self, instance_id: str) -> Optional[Dict]:
        """获取实例状态信息

        Args:
            instance_id: 实例ID

        Returns:
            Dict: 实例状态信息，如果实例不存在返回None
        """
        if instance_id not in self.active_instances:
            return None

        instance = self.active_instances[instance_id]

        # 更新内存使用量
        if instance.process_id:
            try:
                process = psutil.Process(instance.process_id)
                instance.memory_usage = process.memory_info().rss
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        return instance.to_dict()

    async def shutdown_instance(self, instance_id: str) -> bool:
        """关闭指定实例并释放资源

        Args:
            instance_id: 实例ID

        Returns:
            bool: 关闭是否成功
        """
        if instance_id not in self.active_instances:
            logger.warning(f"Instance {instance_id} not found")
            return False

        instance = self.active_instances[instance_id]
        instance.status = InstanceStatus.SHUTTING

        # 清理资源
        if instance_id in self.instance_workers:
            worker = self.instance_workers[instance_id]
            if worker.is_running:
                # 在实际实现中，这里会终止进程
                pass
            del self.instance_workers[instance_id]

        # 更新状态
        instance.status = InstanceStatus.TERMINATED
        del self.active_instances[instance_id]

        logger.info(f"Shutdown instance {instance_id}")
        return True

    async def get_pool_status(self) -> Dict:
        """获取实例池整体状态

        Returns:
            Dict: 实例池状态信息
        """
        # 计算内存使用
        total_memory = sum(
            instance.memory_usage for instance in self.active_instances.values()
        )
        self.performance_metrics["pool_memory_usage"] = total_memory

        # 统计各状态实例数
        status_counts = {}
        for status in InstanceStatus:
            status_counts[status.value] = sum(
                1 for instance in self.active_instances.values()
                if instance.status == status
            )

        return {
            "pool_status": "running" if self.is_running else "stopped",
            "max_instances": self.max_concurrent_instances,
            "active_instances": len(self.active_instances),
            "instance_status_counts": status_counts,
            "performance_metrics": self.performance_metrics,
            "instances": [
                instance.to_dict() for instance in self.active_instances.values()
            ]
        }

    async def _monitor_instances(self):
        """监控实例状态的后台任务"""
        while self.is_running:
            try:
                # 检查长时间运行的实例
                for instance in list(self.active_instances.values()):
                    if instance.status == InstanceStatus.RUNNING:
                        # 如果实例运行超过60秒，标记为错误
                        if instance.get_uptime() > 60:
                            logger.warning(
                                f"Instance {instance.instance_id} running for too long"
                            )
                            instance.status = InstanceStatus.ERROR

                # 更新内存使用量
                for instance in self.active_instances.values():
                    if instance.process_id:
                        try:
                            process = psutil.Process(instance.process_id)
                            instance.memory_usage = process.memory_info().rss
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass

                await asyncio.sleep(5)  # 每5秒检查一次

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitor task: {e}")
                await asyncio.sleep(5)


# 单例模式管理实例池
_instance_pool: Optional[GLMInstancePool] = None


def get_instance_pool() -> GLMInstancePool:
    """获取全局实例池实例(单例模式)"""
    global _instance_pool
    if _instance_pool is None:
        _instance_pool = GLMInstancePool()
    return _instance_pool


async def start_instance_pool():
    """启动全局实例池"""
    pool = get_instance_pool()
    await pool.start()


async def stop_instance_pool():
    """停止全局实例池"""
    global _instance_pool
    if _instance_pool:
        await _instance_pool.stop()
        _instance_pool = None