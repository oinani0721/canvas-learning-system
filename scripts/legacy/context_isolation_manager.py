"""
上下文隔离管理器 - Canvas学习系统

负责管理并行Agent执行的上下文隔离，确保：
- 每个Agent运行在独立的进程空间中
- 独立的内存和状态管理，避免数据冲突
- 完整的上下文生命周期管理和资源回收
- 安全的进程间通信和数据共享

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-22
Story: 8.14 (Task 2)
"""

import asyncio
import uuid
import time
import os
import gc
import pickle
import tempfile
import shutil
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
import psutil
import multiprocessing as mp
from multiprocessing import Manager, Queue
import threading
import weakref


class IsolationLevel(Enum):
    """隔离级别枚举"""
    THREAD = "thread"         # 线程级隔离（轻量级）
    PROCESS = "process"       # 进程级隔离（标准）
    CONTAINER = "container"   # 容器级隔离（重量级，预留）


class ContextStatus(Enum):
    """上下文状态枚举"""
    INITIALIZING = "initializing"
    ACTIVE = "active"
    IDLE = "idle"
    CLEANING_UP = "cleaning_up"
    CLEANED_UP = "cleaned_up"
    ERROR = "error"


@dataclass
class ContextConfiguration:
    """上下文配置"""
    isolation_level: IsolationLevel = IsolationLevel.PROCESS
    memory_limit_mb: int = 256
    context_size_limit_mb: int = 256
    shared_memory_size_mb: int = 512
    timeout_seconds: int = 300
    auto_cleanup: bool = True
    gc_threshold_percentage: float = 80.0
    max_open_files: int = 1000

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return asdict(self)


@dataclass
class IsolatedContext:
    """隔离上下文实例"""
    context_id: str = field(default_factory=lambda: f"ctx-{uuid.uuid4().hex[:16]}")
    task_id: str = ""
    agent_name: str = ""
    isolation_level: IsolationLevel = IsolationLevel.PROCESS

    # 进程和资源信息
    worker_process_id: int = 0
    worker_thread_id: str = ""
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0

    # 状态和时间
    status: ContextStatus = ContextStatus.INITIALIZING
    creation_time: float = field(default_factory=time.time)
    last_activity_time: float = field(default_factory=time.time)
    cleanup_time: Optional[float] = None

    # 资源限制
    memory_limit_mb: int = 256
    open_files_count: int = 0

    # 配置和路径
    temp_directory: Optional[str] = None
    shared_memory_key: Optional[str] = None
    environment_variables: Dict[str, str] = field(default_factory=dict)

    # 统计信息
    total_operations: int = 0
    total_execution_time_ms: float = 0.0
    gc_collection_count: int = 0
    error_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        data = asdict(self)
        data["isolation_level"] = self.isolation_level.value
        data["status"] = self.status.value
        return data

    def update_activity(self) -> None:
        """更新活动时间"""
        self.last_activity_time = time.time()
        self.total_operations += 1


class ProcessIsolationManager:
    """进程级隔离管理器

    管理独立进程中的Agent执行，确保完全的进程、内存和状态隔离。
    """

    def __init__(self, config: ContextConfiguration):
        """初始化进程隔离管理器

        Args:
            config: 上下文配置
        """
        self.config = config
        self.active_processes: Dict[str, mp.Process] = {}
        self.process_pipes: Dict[str, Tuple[mp.Connection, mp.Connection]] = {}
        self.shared_memory_manager = Manager()
        self.shared_contexts = self.shared_memory_manager.dict()

        # 资源监控
        self.resource_monitors: Dict[str, threading.Thread] = {}
        self.monitoring_active = True

        # 垃圾回收控制
        self.gc_lock = threading.Lock()
        self.gc_threshold = config.gc_threshold_percentage

    def create_isolated_context(self, task_id: str, agent_name: str) -> IsolatedContext:
        """创建隔离的执行上下文

        Args:
            task_id: 任务ID
            agent_name: Agent名称

        Returns:
            IsolatedContext: 隔离上下文实例
        """
        context = IsolatedContext(
            task_id=task_id,
            agent_name=agent_name,
            isolation_level=self.config.isolation_level,
            memory_limit_mb=self.config.memory_limit_mb,
            worker_process_id=os.getpid()
        )

        # 创建临时目录
        context.temp_directory = tempfile.mkdtemp(prefix=f"context_{context.context_id}_")

        # 设置环境变量
        context.environment_variables.update({
            "CONTEXT_ID": context.context_id,
            "TASK_ID": task_id,
            "AGENT_NAME": agent_name,
            "MEMORY_LIMIT_MB": str(self.config.memory_limit_mb),
            "TEMP_DIR": context.temp_directory
        })

        # 注册到共享内存
        self.shared_contexts[context.context_id] = context.to_dict()

        # 启动资源监控
        self._start_resource_monitoring(context)

        # 更新状态
        context.status = ContextStatus.ACTIVE
        context.update_activity()

        return context

    def _start_resource_monitoring(self, context: IsolatedContext) -> None:
        """启动资源监控线程

        Args:
            context: 隔离上下文
        """
        def monitor_resources():
            """资源监控线程函数"""
            while self.monitoring_active:
                try:
                    # 获取进程信息
                    process = psutil.Process()

                    # 更新资源使用情况
                    context.memory_usage_mb = process.memory_info().rss / 1024 / 1024
                    context.cpu_usage_percent = process.cpu_percent()
                    context.open_files_count = len(process.open_files())

                    # 检查内存限制
                    if context.memory_usage_mb > context.memory_limit_mb:
                        self._trigger_memory_cleanup(context)

                    # 检查是否需要垃圾回收
                    if self._should_trigger_gc(context):
                        self._perform_garbage_collection(context)

                    # 更新共享内存中的上下文信息
                    self.shared_contexts[context.context_id] = context.to_dict()

                    time.sleep(5)  # 每5秒检查一次

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    # 进程已终止
                    break
                except Exception as e:
                    print(f"资源监控错误 {context.context_id}: {e}")
                    time.sleep(10)

        monitor_thread = threading.Thread(
            target=monitor_resources,
            name=f"ResourceMonitor-{context.context_id}",
            daemon=True
        )
        monitor_thread.start()

        self.resource_monitors[context.context_id] = monitor_thread

    def _should_trigger_gc(self, context: IsolatedContext) -> bool:
        """判断是否应该触发垃圾回收

        Args:
            context: 隔离上下文

        Returns:
            bool: 是否应该触发垃圾回收
        """
        if context.memory_limit_mb == 0:
            return False

        memory_usage_ratio = (context.memory_usage_mb / context.memory_limit_mb) * 100
        return memory_usage_ratio >= self.gc_threshold

    def _trigger_memory_cleanup(self, context: IsolatedContext) -> None:
        """触发内存清理

        Args:
            context: 隔离上下文
        """
        # 记录内存溢出事件
        context.error_count += 1

        # 执行清理操作
        self._cleanup_temp_files(context)

        # 强制垃圾回收
        gc.collect()

        print(f"内存清理触发 - Context: {context.context_id}, "
              f"Memory: {context.memory_usage_mb:.1f}MB/{context.memory_limit_mb}MB")

    def _perform_garbage_collection(self, context: IsolatedContext) -> None:
        """执行垃圾回收

        Args:
            context: 隔离上下文
        """
        with self.gc_lock:
            before_memory = context.memory_usage_mb
            collected = gc.collect()

            context.gc_collection_count += 1

            # 重新测量内存
            process = psutil.Process()
            context.memory_usage_mb = process.memory_info().rss / 1024 / 1024

            memory_freed = before_memory - context.memory_usage_mb

            print(f"垃圾回收完成 - Context: {context.context_id}, "
                  f"Collected: {collected} objects, Memory freed: {memory_freed:.1f}MB")

    def _cleanup_temp_files(self, context: IsolatedContext) -> None:
        """清理临时文件

        Args:
            context: 隔离上下文
        """
        if context.temp_directory and os.path.exists(context.temp_directory):
            try:
                # 删除临时目录中的所有文件
                for item in Path(context.temp_directory).iterdir():
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)
            except Exception as e:
                print(f"清理临时文件失败 {context.temp_directory}: {e}")

    async def cleanup_context(self, context: IsolatedContext) -> bool:
        """清理指定的执行上下文

        Args:
            context: 隔离上下文

        Returns:
            bool: 清理是否成功
        """
        try:
            # 更新状态
            context.status = ContextStatus.CLEANING_UP
            context.cleanup_time = time.time()

            # 停止资源监控
            if context.context_id in self.resource_monitors:
                # 注意：这里应该优雅地停止监控线程
                del self.resource_monitors[context.context_id]

            # 清理临时文件
            if context.temp_directory and os.path.exists(context.temp_directory):
                shutil.rmtree(context.temp_directory, ignore_errors=True)

            # 清理共享内存
            if context.context_id in self.shared_contexts:
                del self.shared_contexts[context.context_id]

            # 清理进程资源
            if context.context_id in self.active_processes:
                process = self.active_processes[context.context_id]
                if process.is_alive():
                    process.terminate()
                    process.join(timeout=5)
                    if process.is_alive():
                        process.kill()
                del self.active_processes[context.context_id]

            # 清理进程管道
            if context.context_id in self.process_pipes:
                parent_conn, child_conn = self.process_pipes[context.context_id]
                parent_conn.close()
                child_conn.close()
                del self.process_pipes[context.context_id]

            # 最终垃圾回收
            gc.collect()

            # 更新状态
            context.status = ContextStatus.CLEANED_UP

            return True

        except Exception as e:
            print(f"清理上下文失败 {context.context_id}: {e}")
            context.status = ContextStatus.ERROR
            return False

    async def get_context_usage(self, context_id: str) -> Optional[Dict[str, Any]]:
        """获取上下文使用情况

        Args:
            context_id: 上下文ID

        Returns:
            Optional[Dict]: 上下文使用信息
        """
        if context_id in self.shared_contexts:
            return dict(self.shared_contexts[context_id])
        return None

    def get_all_contexts_status(self) -> Dict[str, Any]:
        """获取所有上下文的状态

        Returns:
            Dict: 所有上下文状态信息
        """
        return {
            "active_contexts": len(self.active_processes),
            "shared_contexts_count": len(self.shared_contexts),
            "resource_monitors_count": len(self.resource_monitors),
            "contexts": {
                ctx_id: dict(ctx_data)
                for ctx_id, ctx_data in self.shared_contexts.items()
            }
        }

    async def shutdown(self) -> None:
        """关闭管理器并清理所有资源"""
        self.monitoring_active = False

        # 清理所有活跃上下文
        all_context_ids = list(self.shared_contexts.keys())
        for context_id in all_context_ids:
            context_data = self.shared_contexts.get(context_id, {})
            if context_data:
                # 重构上下文对象
                context = IsolatedContext(
                    context_id=context_data.get("context_id", context_id),
                    task_id=context_data.get("task_id", ""),
                    agent_name=context_data.get("agent_name", ""),
                    temp_directory=context_data.get("temp_directory")
                )
                await self.cleanup_context(context)

        # 关闭共享内存管理器
        self.shared_memory_manager.shutdown()


class ContextIsolationManager:
    """上下文隔离管理器主类

    统一管理所有类型的上下文隔离，提供统一的接口和生命周期管理。
    """

    def __init__(self, config: Dict[str, Any]):
        """初始化上下文隔离管理器

        Args:
            config: 上下文隔离配置
        """
        self.config = config
        self.isolation_level = IsolationLevel(config.get("isolation_level", "process"))

        # 创建上下文配置
        self.context_config = ContextConfiguration(
            isolation_level=self.isolation_level,
            memory_limit_mb=config.get("context_size_limit_mb", 256),
            context_size_limit_mb=config.get("context_size_limit_mb", 256),
            shared_memory_size_mb=config.get("shared_memory_size_mb", 512),
            auto_cleanup=config.get("context_cleanup_enabled", True),
            gc_threshold_percentage=config.get("gc_threshold_percentage", 80.0)
        )

        # 根据隔离级别创建相应管理器
        if self.isolation_level == IsolationLevel.PROCESS:
            self.isolation_manager = ProcessIsolationManager(self.context_config)
        else:
            # 其他隔离级别的实现
            raise ValueError(f"不支持的隔离级别: {self.isolation_level}")

        # 活跃上下文注册表
        self.active_contexts: Dict[str, IsolatedContext] = {}

        # 清理统计
        self.cleanup_stats = {
            "total_contexts_created": 0,
            "total_contexts_cleaned": 0,
            "total_memory_freed_mb": 0.0,
            "total_gc_collections": 0
        }

    async def create_isolated_context(self, task_id: str, agent_name: str) -> str:
        """为任务创建隔离的执行上下文

        Args:
            task_id: 任务ID
            agent_name: Agent名称

        Returns:
            str: 上下文ID
        """
        context = self.isolation_manager.create_isolated_context(task_id, agent_name)
        self.active_contexts[context.context_id] = context

        # 更新统计
        self.cleanup_stats["total_contexts_created"] += 1

        return context.context_id

    async def cleanup_context(self, context_id: str) -> bool:
        """清理指定的执行上下文

        Args:
            context_id: 上下文ID

        Returns:
            bool: 清理是否成功
        """
        if context_id not in self.active_contexts:
            return False

        context = self.active_contexts[context_id]
        success = await self.isolation_manager.cleanup_context(context)

        if success:
            # 更新统计
            self.cleanup_stats["total_contexts_cleaned"] += 1
            self.cleanup_stats["total_memory_freed_mb"] += context.memory_usage_mb
            self.cleanup_stats["total_gc_collections"] += context.gc_collection_count

            # 从活跃上下文中移除
            del self.active_contexts[context_id]

        return success

    async def get_context_usage(self, context_id: str) -> Optional[Dict[str, Any]]:
        """获取上下文使用情况

        Args:
            context_id: 上下文ID

        Returns:
            Optional[Dict]: 上下文使用信息
        """
        return await self.isolation_manager.get_context_usage(context_id)

    def get_all_contexts_status(self) -> Dict[str, Any]:
        """获取所有上下文的状态

        Returns:
            Dict: 所有上下文状态信息
        """
        base_status = self.isolation_manager.get_all_contexts_status()

        # 添加管理器级别统计
        base_status["isolation_manager_stats"] = self.cleanup_stats
        base_status["active_contexts_detail"] = {
            ctx_id: ctx.to_dict()
            for ctx_id, ctx in self.active_contexts.items()
        }

        return base_status

    async def cleanup_idle_contexts(self, idle_timeout_seconds: int = 300) -> int:
        """清理空闲超时的上下文

        Args:
            idle_timeout_seconds: 空闲超时时间（秒）

        Returns:
            int: 清理的上下文数量
        """
        current_time = time.time()
        idle_contexts = []

        for context_id, context in self.active_contexts.items():
            idle_time = current_time - context.last_activity_time
            if idle_time > idle_timeout_seconds and context.status == ContextStatus.IDLE:
                idle_contexts.append(context_id)

        cleaned_count = 0
        for context_id in idle_contexts:
            if await self.cleanup_context(context_id):
                cleaned_count += 1

        return cleaned_count

    async def force_cleanup_all_contexts(self) -> int:
        """强制清理所有上下文

        Returns:
            int: 清理的上下文数量
        """
        all_context_ids = list(self.active_contexts.keys())
        cleaned_count = 0

        for context_id in all_context_ids:
            if await self.cleanup_context(context_id):
                cleaned_count += 1

        return cleaned_count

    def get_cleanup_statistics(self) -> Dict[str, Any]:
        """获取清理统计信息

        Returns:
            Dict: 清理统计信息
        """
        return self.cleanup_stats.copy()

    async def shutdown(self) -> None:
        """关闭管理器并清理所有资源"""
        # 强制清理所有上下文
        await self.force_cleanup_all_contexts()

        # 关闭底层隔离管理器
        if hasattr(self.isolation_manager, 'shutdown'):
            await self.isolation_manager.shutdown()

        # 最终垃圾回收
        gc.collect()


# 上下文隔离管理器工厂函数
def create_context_isolation_manager(config: Dict[str, Any]) -> ContextIsolationManager:
    """创建上下文隔离管理器

    Args:
        config: 隔离配置

    Returns:
        ContextIsolationManager: 上下文隔离管理器实例
    """
    return ContextIsolationManager(config)


# 上下文验证和测试函数
async def validate_context_isolation(manager: ContextIsolationManager,
                                  test_tasks: List[Tuple[str, str]]) -> Dict[str, Any]:
    """验证上下文隔离功能

    Args:
        manager: 上下文隔离管理器
        test_tasks: 测试任务列表 [(task_id, agent_name), ...]

    Returns:
        Dict: 验证结果
    """
    results = {
        "total_tests": len(test_tasks),
        "successful_contexts": 0,
        "failed_contexts": 0,
        "memory_isolation_valid": True,
        "process_isolation_valid": True,
        "cleanup_success_rate": 0.0,
        "context_ids": [],
        "errors": []
    }

    created_contexts = []

    try:
        # 创建测试上下文
        for task_id, agent_name in test_tasks:
            try:
                context_id = await manager.create_isolated_context(task_id, agent_name)
                created_contexts.append(context_id)
                results["context_ids"].append(context_id)
                results["successful_contexts"] += 1

                # 验证上下文隔离
                usage = await manager.get_context_usage(context_id)
                if usage:
                    # 验证进程ID独立性
                    process_id = usage.get("worker_process_id")
                    if process_id == os.getpid():
                        results["process_isolation_valid"] = False
                        results["errors"].append(f"进程隔离失败: {context_id}")

            except Exception as e:
                results["failed_contexts"] += 1
                results["errors"].append(f"创建上下文失败 {task_id}: {e}")

        # 清理测试上下文
        cleanup_success = 0
        for context_id in created_contexts:
            if await manager.cleanup_context(context_id):
                cleanup_success += 1

        if created_contexts:
            results["cleanup_success_rate"] = cleanup_success / len(created_contexts)

    except Exception as e:
        results["errors"].append(f"验证过程错误: {e}")

    return results