"""
Command Executor - Canvas学习系统

本模块实现并行命令的执行引擎，负责与GLMInstancePool集成，
执行并行任务并提供实时反馈和进度监控。

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-26
"""

import asyncio
import time
import uuid
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import logging
from concurrent.futures import ThreadPoolExecutor

# 导入并行命令解析器模块
from parallel_command_parser import (
    ParallelCommand, CommandResult, CommandType, TaskPriority
)

# 导入Agent实例池模块
try:
    from agent_instance_pool import (
        get_instance_pool, AgentTask, TaskPriority as PoolTaskPriority
    )
    AGENT_POOL_AVAILABLE = True
except ImportError as e:
    AGENT_POOL_AVAILABLE = False
    logging.warning(f"Agent instance pool not available: {e}")

# 导入Canvas操作模块
try:
    from canvas_utils import CanvasOrchestrator
    CANVAS_UTILS_AVAILABLE = True
except ImportError as e:
    CANVAS_UTILS_AVAILABLE = False
    logging.warning(f"Canvas utils not available: {e}")

# 配置日志
logger = logging.getLogger(__name__)


class ExecutionStatus:
    """执行状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProgressTracker:
    """进度跟踪器"""

    def __init__(self, total_tasks: int):
        self.total_tasks = total_tasks
        self.completed_tasks = 0
        self.failed_tasks = 0
        self.start_time = time.time()
        self.current_task = None
        self.status_updates = []

    def update_progress(self, completed: int = 0, failed: int = 0, current_task: Optional[str] = None):
        """更新进度"""
        self.completed_tasks += completed
        self.failed_tasks += failed
        if current_task:
            self.current_task = current_task

        # 记录状态更新
        progress = (self.completed_tasks + self.failed_tasks) / self.total_tasks * 100
        self.status_updates.append({
            "timestamp": datetime.now().isoformat(),
            "progress": progress,
            "completed": self.completed_tasks,
            "failed": self.failed_tasks,
            "current_task": self.current_task
        })

    def get_progress_percentage(self) -> float:
        """获取进度百分比"""
        return (self.completed_tasks + self.failed_tasks) / self.total_tasks * 100 if self.total_tasks > 0 else 0

    def get_elapsed_time(self) -> float:
        """获取已用时间（秒）"""
        return time.time() - self.start_time

    def get_eta(self) -> Optional[float]:
        """估算剩余时间（秒）"""
        if self.completed_tasks + self.failed_tasks == 0:
            return None

        elapsed = self.get_elapsed_time()
        if elapsed < 0.01:  # 如果时间太短，使用默认估算
            # 假设每个任务平均需要1秒
            avg_task_time = 1.0
        else:
            avg_task_time = elapsed / (self.completed_tasks + self.failed_tasks)

        remaining_tasks = self.total_tasks - (self.completed_tasks + self.failed_tasks)
        eta = avg_task_time * remaining_tasks
        return max(eta, 0.1) if eta > 0 else None


class CommandExecutor:
    """命令执行器

    负责执行并行命令，管理任务生命周期，提供实时反馈。
    """

    def __init__(self,
                 instance_pool: Optional[Any] = None,
                 progress_callback: Optional[Callable[[Dict], None]] = None):
        """初始化命令执行器

        Args:
            instance_pool: Agent实例池，如果为None则尝试获取全局实例池
            progress_callback: 进度回调函数，接收进度更新字典
        """
        self.instance_pool = instance_pool
        self.progress_callback = progress_callback
        self.active_commands: Dict[str, Dict] = {}  # 活跃命令状态
        self.execution_history: List[CommandResult] = []  # 执行历史

        # 获取实例池
        if not self.instance_pool and AGENT_POOL_AVAILABLE:
            self.instance_pool = get_instance_pool()

        # 验证依赖
        if not AGENT_POOL_AVAILABLE:
            logger.warning("Agent instance pool not available - some features may be limited")
        if not CANVAS_UTILS_AVAILABLE:
            logger.warning("Canvas utils not available - cannot process canvas files")

        logger.info("CommandExecutor initialized")

    async def execute_command(self, command: ParallelCommand) -> CommandResult:
        """执行并行命令

        Args:
            command: 并行命令对象

        Returns:
            CommandResult: 命令执行结果
        """
        command_id = str(uuid.uuid4())
        start_time = time.time()

        logger.info(f"Executing command {command_id}: {command.command_type.value}")

        # 创建命令结果对象
        result = CommandResult(
            command_id=command_id,
            status="running",
            message=f"正在执行 {command.command_type.value} 命令"
        )

        # 记录命令状态
        self.active_commands[command_id] = {
            "command": command,
            "result": result,
            "start_time": start_time,
            "status": ExecutionStatus.RUNNING
        }

        try:
            # 根据命令类型执行不同的处理逻辑
            if command.command_type == CommandType.PARALLEL_AGENTS:
                result = await self._execute_parallel_agents(command, command_id)
            elif command.command_type == CommandType.PARALLEL_NODES:
                result = await self._execute_parallel_nodes(command, command_id)
            elif command.command_type == CommandType.PARALLEL_COLOR:
                result = await self._execute_parallel_color(command, command_id)
            elif command.command_type == CommandType.PARALLEL_MIXED:
                result = await self._execute_parallel_mixed(command, command_id)
            else:
                raise ValueError(f"Unknown command type: {command.command_type}")

        except Exception as e:
            logger.error(f"Error executing command {command_id}: {e}")
            result.status = "failed"
            result.message = f"命令执行失败: {str(e)}"
            result.errors.append(str(e))

        # 计算执行时间
        result.execution_time = time.time() - start_time

        # 更新命令状态
        if command_id in self.active_commands:
            self.active_commands[command_id]["status"] = (
                ExecutionStatus.COMPLETED if result.status == "success"
                else ExecutionStatus.FAILED
            )

        # 添加到执行历史
        self.execution_history.append(result)

        logger.info(f"Command {command_id} completed with status: {result.status}")
        return result

    async def _execute_parallel_agents(self, command: ParallelCommand, command_id: str) -> CommandResult:
        """执行*parallel-agents命令

        根据Agent类型创建指定数量的实例，并行处理节点
        """
        if not AGENT_POOL_AVAILABLE:
            return CommandResult(
                command_id=command_id,
                status="failed",
                message="Agent实例池不可用",
                errors=["Agent instance pool module not loaded"]
            )

        # 获取Canvas文件路径
        canvas_path = command.canvas_path or self._get_default_canvas_path()
        if not canvas_path:
            return CommandResult(
                command_id=command_id,
                status="failed",
                message="未指定Canvas文件路径",
                errors=["Canvas path is required"]
            )

        # 获取节点列表
        try:
            orchestrator = CanvasOrchestrator(canvas_path) if CANVAS_UTILS_AVAILABLE else None
            if not orchestrator:
                return CommandResult(
                    command_id=command_id,
                    status="failed",
                    message="无法初始化Canvas操作器",
                    errors=["Canvas utils not available"]
                )

            # 获取所有节点
            all_nodes = orchestrator.get_all_nodes()

            # 筛选目标节点
            if command.target_nodes:
                # 如果指定了节点列表，使用指定节点
                target_nodes = [node for node in all_nodes if node["id"] in command.target_nodes]
            else:
                # 否则使用所有问题节点（红色或紫色）
                target_nodes = [
                    node for node in all_nodes
                    if node.get("color") in ["1", "3"]  # 红色或紫色
                ]

            # 如果指定了节点数量，限制处理的节点数
            if command.node_count:
                target_nodes = target_nodes[:command.node_count]

            if not target_nodes:
                return CommandResult(
                    command_id=command_id,
                    status="completed",
                    message="没有找到需要处理的节点",
                    processed_nodes=0
                )

        except Exception as e:
            return CommandResult(
                command_id=command_id,
                status="failed",
                message=f"获取Canvas节点失败: {str(e)}",
                errors=[str(e)]
            )

        # 创建进度跟踪器
        progress = ProgressTracker(len(target_nodes))

        # 如果是试运行，只返回计划
        if command.dry_run:
            return CommandResult(
                command_id=command_id,
                status="success",
                message=f"试运行：将使用 {command.agent_type} 处理 {len(target_nodes)} 个节点",
                processed_nodes=len(target_nodes),
                total_instances=min(len(target_nodes), command.max_instances or 6),
                metrics={
                    "dry_run": True,
                    "target_nodes": [node["id"] for node in target_nodes],
                    "agent_type": command.agent_type
                }
            )

        # 创建并提交任务
        tasks = []
        for i, node in enumerate(target_nodes):
            # 创建Agent任务
            task = AgentTask(
                task_id=f"{command_id}-task-{i}",
                agent_type=command.agent_type,
                node_data=node,
                priority=self._convert_priority(command.priority)
            )

            tasks.append(task)

        # 执行并行任务
        processed_count = 0
        errors = []

        # 限制并发实例数
        max_instances = min(
            command.max_instances or 6,
            len(tasks),
            self.instance_pool.max_concurrent_instances if self.instance_pool else 6
        )

        # 使用信号量控制并发
        semaphore = asyncio.Semaphore(max_instances)

        async def process_task(task):
            async with semaphore:
                try:
                    # 提交任务到实例池
                    if self.instance_pool:
                        success = await self.instance_pool.submit_task_to_any_instance(task)
                        if success:
                            progress.update_progress(completed=1)
                            return True
                        else:
                            progress.update_progress(failed=1)
                            return False
                    else:
                        # 模拟执行（用于测试）
                        await asyncio.sleep(1)  # 模拟处理时间
                        progress.update_progress(completed=1)
                        return True
                except Exception as e:
                    progress.update_progress(failed=1)
                    errors.append(f"Task {task.task_id} failed: {str(e)}")
                    return False

        # 报告进度
        self._report_progress(command_id, progress)

        # 执行所有任务
        results = await asyncio.gather(*[process_task(task) for task in tasks], return_exceptions=True)

        # 统计结果
        processed_count = sum(1 for r in results if r is True)
        error_count = sum(1 for r in results if r is False)

        return CommandResult(
            command_id=command_id,
            status="success" if error_count == 0 else "completed_with_errors",
            message=f"处理完成: {processed_count} 成功, {error_count} 失败",
            processed_nodes=processed_count,
            total_instances=max_instances,
            errors=errors,
            metrics={
                "total_nodes": len(target_nodes),
                "success_count": processed_count,
                "error_count": error_count,
                "agent_type": command.agent_type,
                "execution_time": progress.get_elapsed_time()
            }
        )

    async def _execute_parallel_nodes(self, command: ParallelCommand, command_id: str) -> CommandResult:
        """执行*parallel-nodes命令

        处理指定的节点ID列表
        """
        # 实现逻辑与_execute_parallel_agents类似，但只处理指定节点
        logger.info(f"Executing parallel-nodes command {command_id}")

        # 创建一个新的命令对象，重用parallel-agents的逻辑
        agents_command = ParallelCommand(
            command_type=CommandType.PARALLEL_AGENTS,
            agent_type=command.agent_type,
            target_nodes=command.target_nodes,
            max_instances=command.max_instances,
            canvas_path=command.canvas_path,
            dry_run=command.dry_run,
            priority=command.priority
        )

        return await self._execute_parallel_agents(agents_command, command_id)

    async def _execute_parallel_color(self, command: ParallelCommand, command_id: str) -> CommandResult:
        """执行*parallel-color命令

        处理指定颜色的所有节点
        """
        logger.info(f"Executing parallel-color command {command_id}")

        # 获取Canvas文件路径
        canvas_path = command.canvas_path or self._get_default_canvas_path()
        if not canvas_path:
            return CommandResult(
                command_id=command_id,
                status="failed",
                message="未指定Canvas文件路径",
                errors=["Canvas path is required"]
            )

        # 获取指定颜色的节点
        try:
            orchestrator = CanvasOrchestrator(canvas_path) if CANVAS_UTILS_AVAILABLE else None
            if not orchestrator:
                return CommandResult(
                    command_id=command_id,
                    status="failed",
                    message="无法初始化Canvas操作器",
                    errors=["Canvas utils not available"]
                )

            # 获取所有节点并筛选颜色
            all_nodes = orchestrator.get_all_nodes()
            target_nodes = [
                node for node in all_nodes
                if node.get("color") == command.color_filter
            ]

            # 如果指定了限制数量
            if command.node_count:
                target_nodes = target_nodes[:command.node_count]

            if not target_nodes:
                return CommandResult(
                    command_id=command_id,
                    status="completed",
                    message=f"没有找到颜色为 {command.color_filter} 的节点",
                    processed_nodes=0
                )

            # 创建节点ID列表
            node_ids = [node["id"] for node in target_nodes]

            # 创建新的命令对象，重用parallel-nodes的逻辑
            nodes_command = ParallelCommand(
                command_type=CommandType.PARALLEL_NODES,
                agent_type=command.agent_type,
                target_nodes=node_ids,
                max_instances=command.max_instances,
                canvas_path=command.canvas_path,
                dry_run=command.dry_run,
                priority=command.priority
            )

            return await self._execute_parallel_nodes(nodes_command, command_id)

        except Exception as e:
            return CommandResult(
                command_id=command_id,
                status="failed",
                message=f"获取颜色节点失败: {str(e)}",
                errors=[str(e)]
            )

    async def _execute_parallel_mixed(self, command: ParallelCommand, command_id: str) -> CommandResult:
        """执行*parallel-mixed命令

        使用多种Agent类型混合处理
        """
        logger.info(f"Executing parallel-mixed command {command_id}")

        if not command.mixed_config:
            return CommandResult(
                command_id=command_id,
                status="failed",
                message="混合命令必须指定配置",
                errors=["Mixed config is required"]
            )

        # 获取Canvas文件路径
        canvas_path = command.canvas_path or self._get_default_canvas_path()
        if not canvas_path:
            return CommandResult(
                command_id=command_id,
                status="failed",
                message="未指定Canvas文件路径",
                errors=["Canvas path is required"]
            )

        # 如果是试运行，返回计划
        if command.dry_run:
            total_instances = sum(command.mixed_config.values())
            return CommandResult(
                command_id=command_id,
                status="success",
                message=f"试运行：将使用混合配置处理，总计 {total_instances} 个实例",
                total_instances=total_instances,
                metrics={
                    "dry_run": True,
                    "mixed_config": command.mixed_config,
                    "total_instances": total_instances
                }
            )

        # 执行混合任务
        results = []
        total_processed = 0
        all_errors = []

        for agent_type, count in command.mixed_config.items():
            # 为每种Agent类型创建子命令
            sub_command = ParallelCommand(
                command_type=CommandType.PARALLEL_AGENTS,
                agent_type=agent_type,
                node_count=count,
                max_instances=min(count, command.max_instances or 6),
                canvas_path=command.canvas_path,
                dry_run=False,
                priority=command.priority
            )

            # 执行子命令
            sub_result = await self._execute_parallel_agents(sub_command, f"{command_id}-{agent_type}")
            results.append(sub_result)

            total_processed += sub_result.processed_nodes
            all_errors.extend(sub_result.errors)

        # 合并结果
        total_instances = sum(command.mixed_config.values())
        success_count = sum(1 for r in results if r.status == "success")

        return CommandResult(
            command_id=command_id,
            status="success" if success_count == len(results) else "completed_with_errors",
            message=f"混合处理完成: {success_count}/{len(results)} 种Agent类型成功",
            processed_nodes=total_processed,
            total_instances=total_instances,
            errors=all_errors,
            metrics={
                "mixed_config": command.mixed_config,
                "sub_results": [r.to_dict() for r in results],
                "success_rate": success_count / len(results) if results else 0
            }
        )

    async def preview_command(self, command: ParallelCommand) -> Dict:
        """预览命令执行计划（不实际执行）

        Args:
            command: 并行命令对象

        Returns:
            Dict: 预览信息
        """
        preview = {
            "command_type": command.command_type.value,
            "agent_type": command.agent_type,
            "dry_run": True,
            "estimated_duration": None,
            "resource_requirements": {},
            "target_summary": {}
        }

        # 获取目标节点信息
        if command.canvas_path and CANVAS_UTILS_AVAILABLE:
            try:
                orchestrator = CanvasOrchestrator(command.canvas_path)
                all_nodes = orchestrator.get_all_nodes()

                if command.target_nodes:
                    target_nodes = [n for n in all_nodes if n["id"] in command.target_nodes]
                elif command.color_filter:
                    target_nodes = [n for n in all_nodes if n.get("color") == command.color_filter]
                    if command.node_count:
                        target_nodes = target_nodes[:command.node_count]
                else:
                    # 默认处理问题节点
                    target_nodes = [n for n in all_nodes if n.get("color") in ["1", "3"]]
                    if command.node_count:
                        target_nodes = target_nodes[:command.node_count]

                preview["target_summary"] = {
                    "total_nodes": len(all_nodes),
                    "target_nodes": len(target_nodes),
                    "by_color": {}
                }

                # 统计颜色分布
                for node in target_nodes:
                    color = node.get("color", "unknown")
                    preview["target_summary"]["by_color"][color] = \
                        preview["target_summary"]["by_color"].get(color, 0) + 1

            except Exception as e:
                preview["target_summary"]["error"] = str(e)

        # 估算资源需求
        if command.command_type == CommandType.PARALLEL_MIXED and command.mixed_config:
            preview["resource_requirements"] = {
                "total_instances": sum(command.mixed_config.values()),
                "agent_distribution": command.mixed_config
            }
        else:
            instance_count = command.node_count or command.max_instances or 1
            preview["resource_requirements"] = {
                "total_instances": instance_count,
                "agent_type": command.agent_type
            }

        # 估算执行时间（假设每个节点平均2秒）
        target_count = preview["target_summary"].get("target_nodes", 0)
        preview["estimated_duration"] = {
            "seconds": target_count * 2 / min(command.max_instances or 6, 6),
            "formatted": f"{(target_count * 2 / min(command.max_instances or 6, 6)):.1f} seconds"
        }

        return preview

    def get_execution_status(self, command_id: str) -> Optional[Dict]:
        """获取命令执行状态

        Args:
            command_id: 命令ID

        Returns:
            Optional[Dict]: 状态信息，如果命令不存在则返回None
        """
        if command_id not in self.active_commands:
            return None

        cmd_info = self.active_commands[command_id]
        return {
            "command_id": command_id,
            "status": cmd_info["status"],
            "start_time": cmd_info["start_time"],
            "elapsed_time": time.time() - cmd_info["start_time"],
            "result": cmd_info["result"].to_dict() if cmd_info["result"] else None
        }

    async def cancel_command(self, command_id: str) -> bool:
        """取消正在执行的命令

        Args:
            command_id: 命令ID

        Returns:
            bool: 是否成功取消
        """
        if command_id not in self.active_commands:
            return False

        cmd_info = self.active_commands[command_id]
        if cmd_info["status"] not in [ExecutionStatus.RUNNING, ExecutionStatus.PENDING]:
            return False

        # 更新状态
        cmd_info["status"] = ExecutionStatus.CANCELLED
        if cmd_info["result"]:
            cmd_info["result"].status = "cancelled"
            cmd_info["result"].message = "命令已取消"

        logger.info(f"Command {command_id} cancelled")
        return True

    def get_active_commands(self) -> List[Dict]:
        """获取所有活跃命令的列表

        Returns:
            List[Dict]: 活跃命令信息列表
        """
        active = []
        for command_id, cmd_info in self.active_commands.items():
            if cmd_info["status"] in [ExecutionStatus.RUNNING, ExecutionStatus.PENDING]:
                status = self.get_execution_status(command_id)
                if status:
                    active.append(status)

        return active

    def get_execution_history(self, limit: int = 10) -> List[Dict]:
        """获取执行历史

        Args:
            limit: 返回的历史记录数量限制

        Returns:
            List[Dict]: 执行历史列表
        """
        history = self.execution_history[-limit:] if limit > 0 else self.execution_history
        return [result.to_dict() for result in reversed(history)]

    def _get_default_canvas_path(self) -> Optional[str]:
        """获取默认Canvas文件路径

        Returns:
            Optional[str]: Canvas文件路径，如果没有找到则返回None
        """
        # 这里可以实现查找默认Canvas的逻辑
        # 例如查找当前目录下的.canvas文件
        import glob
        import os

        canvas_files = glob.glob("*.canvas")
        if canvas_files:
            return canvas_files[0]

        return None

    def _convert_priority(self, priority: TaskPriority) -> PoolTaskPriority:
        """转换优先级类型

        Args:
            priority: 命令优先级

        Returns:
            PoolTaskPriority: 实例池优先级
        """
        if AGENT_POOL_AVAILABLE:
            priority_map = {
                TaskPriority.LOW: PoolTaskPriority.LOW,
                TaskPriority.NORMAL: PoolTaskPriority.NORMAL,
                TaskPriority.HIGH: PoolTaskPriority.HIGH,
                TaskPriority.URGENT: PoolTaskPriority.URGENT
            }
            return priority_map.get(priority, PoolTaskPriority.NORMAL)

        return TaskPriority.NORMAL

    def _report_progress(self, command_id: str, progress: ProgressTracker):
        """报告进度

        Args:
            command_id: 命令ID
            progress: 进度跟踪器
        """
        if self.progress_callback:
            progress_info = {
                "command_id": command_id,
                "progress_percentage": progress.get_progress_percentage(),
                "completed": progress.completed_tasks,
                "failed": progress.failed_tasks,
                "total": progress.total_tasks,
                "elapsed_time": progress.get_elapsed_time(),
                "eta": progress.get_eta(),
                "current_task": progress.current_task
            }

            # 异步调用回调
            if asyncio.iscoroutinefunction(self.progress_callback):
                asyncio.create_task(self.progress_callback(progress_info))
            else:
                self.progress_callback(progress_info)

    # 清理完成的命令
    def cleanup_completed_commands(self, max_age: float = 3600):
        """清理已完成的命令记录

        Args:
            max_age: 最大保留时间（秒），默认1小时
        """
        current_time = time.time()
        to_remove = []

        for command_id, cmd_info in self.active_commands.items():
            if cmd_info["status"] in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED]:
                age = current_time - cmd_info["start_time"]
                if age > max_age:
                    to_remove.append(command_id)

        for command_id in to_remove:
            del self.active_commands[command_id]
            logger.info(f"Cleaned up command {command_id}")

        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} completed commands")