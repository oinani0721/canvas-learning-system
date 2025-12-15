"""
Enhanced Agent Instance Pool Module - Canvas学习系统

本模块实现集成GLM Coding Plan用量管理的Agent实例池，
支持智能用量控制、实时监控和预警机制。

Author: Canvas Learning System Team
Version: 2.0
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

# 导入GLM用量管理模块
from glm_rate_limiter import GLMRateLimiter, get_global_rate_limiter, UsageAlert
from usage_monitor import UsageMonitor

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QuotaExhaustionStrategy(Enum):
    """用量耗尽策略"""
    REJECT = "reject"        # 拒绝新任务
    QUEUE = "queue"          # 排队等待
    WAIT = "wait"            # 等待周期重置


@dataclass
class QuotaControlConfig:
    """用量控制配置"""
    enable_quota_control: bool = True
    check_quota_before_creation: bool = True
    check_quota_before_execution: bool = True
    quota_exhaustion_strategy: QuotaExhaustionStrategy = QuotaExhaustionStrategy.QUEUE
    max_wait_time_seconds: int = 300
    prompts_per_task_estimate: Dict[str, int] = field(default_factory=lambda: {
        "clarification-path": 5,
        "memory-anchor": 3,
        "oral-explanation": 8,
        "comparison-table": 4,
        "four-level-explanation": 10,
        "example-teaching": 6,
        "basic-decomposition": 2,
        "deep-decomposition": 3,
        "scoring-agent": 2,
        "verification-question-agent": 3
    })


class EnhancedGLMInstancePool:
    """增强版GLM实例池，集成用量管理

    支持智能用量控制、实时监控、预警机制，
    确保并行处理不会超出GLM Coding Plan限制。
    """

    def __init__(self,
                 max_concurrent_instances: int = 6,
                 quota_control_config: Optional[QuotaControlConfig] = None,
                 rate_limiter: Optional[GLMRateLimiter] = None):
        """初始化增强版实例池

        Args:
            max_concurrent_instances: 最大并发实例数
            quota_control_config: 用量控制配置
            rate_limiter: GLM速率限制器实例
        """
        self.max_concurrent_instances = max_concurrent_instances
        self.quota_config = quota_control_config or QuotaControlConfig()

        # GLM速率限制器
        self.rate_limiter = rate_limiter or get_global_rate_limiter()

        # 用量监控器
        self.usage_monitor = UsageMonitor(self.rate_limiter)

        # 实例管理
        self.active_instances: Dict[str, Dict] = {}
        self.instance_queue: asyncio.Queue = asyncio.Queue()

        # 性能指标
        self.performance_metrics: Dict = {
            "total_tasks_processed": 0,
            "successful_tasks": 0,
            "failed_tasks": 0,
            "quota_exhausted_rejections": 0,
            "average_execution_time": 0.0,
            "pool_memory_usage": 0.0,
            "quota_usage_efficiency": 0.0
        }

        # 预警处理
        self.alert_handlers: List[Callable] = []

        # 运行状态
        self.is_running = False
        self._monitor_task = None
        self._queue_processor_task = None

        logger.info(f"EnhancedGLMInstancePool initialized with quota control")

    async def start(self):
        """启动增强版实例池"""
        if self.is_running:
            logger.warning("Enhanced instance pool is already running")
            return

        self.is_running = True

        # 启动速率限制器
        await self.rate_limiter.start()

        # 启动用量监控器
        await self.usage_monitor.start_monitoring()

        # 设置预警回调
        await self.rate_limiter.set_alert_callback(self._handle_usage_alert)

        # 启动后台任务
        self._monitor_task = asyncio.create_task(self._monitor_instances())
        self._queue_processor_task = asyncio.create_task(self._process_task_queue())

        logger.info("EnhancedGLMInstancePool started with quota management")

    async def stop(self):
        """停止增强版实例池"""
        self.is_running = False

        # 关闭所有实例
        for instance_id in list(self.active_instances.keys()):
            await self.shutdown_instance(instance_id)

        # 停止后台任务
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

        if self._queue_processor_task:
            self._queue_processor_task.cancel()
            try:
                await self._queue_processor_task
            except asyncio.CancelledError:
                pass

        # 停止用量监控器
        await self.usage_monitor.stop_monitoring()

        # 停止速率限制器
        await self.rate_limiter.stop()

        logger.info("EnhancedGLMInstancePool stopped")

    async def create_instance(self, agent_type: str, estimated_prompts: Optional[int] = None) -> str:
        """创建新Agent实例（带用量检查）

        Args:
            agent_type: Agent类型
            estimated_prompts: 预估的prompt数量

        Returns:
            str: 实例ID

        Raises:
            ValueError: 用量不足或达到限制
        """
        # 检查并发实例数限制
        if len(self.active_instances) >= self.max_concurrent_instances:
            raise ValueError(
                f"Maximum concurrent instances ({self.max_concurrent_instances}) reached"
            )

        # 用量控制检查
        if self.quota_config.enable_quota_control:
            # 估算所需prompt数量
            if estimated_prompts is None:
                estimated_prompts = self.quota_config.prompts_per_task_estimate.get(agent_type, 5)

            # 检查用量可用性
            if self.quota_config.check_quota_before_creation:
                if not await self._check_quota_availability(estimated_prompts):
                    # 根据策略处理
                    if self.quota_config.quota_exhaustion_strategy == QuotaExhaustionStrategy.REJECT:
                        self.performance_metrics["quota_exhausted_rejections"] += 1
                        raise ValueError(f"Insufficient quota for {estimated_prompts} prompts")
                    elif self.quota_config.quota_exhaustion_strategy == QuotaExhaustionStrategy.WAIT:
                        if not await self.rate_limiter.wait_for_quota(estimated_prompts):
                            raise ValueError("Timeout waiting for quota recovery")

        # 创建实例
        instance_id = f"enhanced-{uuid.uuid4().hex[:8]}"

        instance_data = {
            "instance_id": instance_id,
            "agent_type": agent_type,
            "status": "creating",
            "created_at": datetime.now(),
            "estimated_prompts": estimated_prompts or self.quota_config.prompts_per_task_estimate.get(agent_type, 5),
            "actual_prompts_used": 0,
            "task_count": 0,
            "memory_usage": 0.0,
            "process_id": None
        }

        self.active_instances[instance_id] = instance_data

        # 更新状态
        instance_data["status"] = "idle"

        logger.info(f"Created enhanced instance {instance_id} of type {agent_type}")
        return instance_id

    async def submit_task(self, instance_id: str, task_data: Dict) -> Dict:
        """提交任务到指定实例（带用量控制）

        Args:
            instance_id: 实例ID
            task_data: 任务数据

        Returns:
            Dict: 执行结果
        """
        if instance_id not in self.active_instances:
            logger.error(f"Instance {instance_id} not found")
            return {"status": "error", "message": "Instance not found"}

        instance = self.active_instances[instance_id]

        if instance["status"] != "idle":
            logger.warning(f"Instance {instance_id} is not idle (status: {instance['status']})")
            return {"status": "error", "message": "Instance is not idle"}

        # 用量检查
        estimated_prompts = instance["estimated_prompts"]
        if self.quota_config.enable_quota_control and self.quota_config.check_quota_before_execution:
            if not await self._check_quota_availability(estimated_prompts):
                # 加入队列等待
                if self.quota_config.quota_exhaustion_strategy == QuotaExhaustionStrategy.QUEUE:
                    await self.instance_queue.put({
                        "instance_id": instance_id,
                        "task_data": task_data,
                        "queue_time": datetime.now()
                    })
                    return {"status": "queued", "message": "Task queued due to quota limits"}
                else:
                    self.performance_metrics["quota_exhausted_rejections"] += 1
                    return {"status": "error", "message": "Insufficient quota"}

        # 执行任务
        return await self._execute_task_with_quota_control(instance_id, task_data)

    async def _execute_task_with_quota_control(self, instance_id: str, task_data: Dict) -> Dict:
        """执行任务并控制用量"""
        instance = self.active_instances[instance_id]
        estimated_prompts = instance["estimated_prompts"]

        # 预消耗用量
        if self.quota_config.enable_quota_control:
            if not await self.rate_limiter.consume_quota(estimated_prompts):
                return {"status": "error", "message": "Failed to consume quota"}

        try:
            # 更新实例状态
            instance["status"] = "running"
            instance["task_count"] += 1

            start_time = datetime.now()

            # 模拟任务执行（实际实现中会调用具体的Agent）
            await asyncio.sleep(0.1)

            # 模拟结果
            result = {
                "task_id": task_data.get("task_id", "unknown"),
                "instance_id": instance_id,
                "status": "completed",
                "result": f"Task completed by {instance['agent_type']}",
                "execution_time": (datetime.now() - start_time).total_seconds(),
                "prompts_used": estimated_prompts
            }

            # 更新用量统计
            instance["actual_prompts_used"] += estimated_prompts

            # 更新性能指标
            self.performance_metrics["successful_tasks"] += 1
            self.performance_metrics["total_tasks_processed"] += 1

            # 更新状态
            instance["status"] = "idle"

            return result

        except Exception as e:
            logger.error(f"Task execution failed in instance {instance_id}: {e}")

            # 回滚用量（如果可能）
            if self.quota_config.enable_quota_control:
                try:
                    # 减少已使用的额度（回滚）
                    self.rate_limiter.usage_metrics.used_prompts -= estimated_prompts
                    self.rate_limiter.usage_metrics.remaining_prompts += estimated_prompts
                    self.rate_limiter.usage_metrics.usage_percentage = (
                        self.rate_limiter.usage_metrics.used_prompts /
                        self.rate_limiter.usage_metrics.total_prompts
                    )
                    logger.info(f"Rolled back {estimated_prompts} prompts due to task failure")
                except Exception as rollback_error:
                    logger.error(f"Failed to rollback quota: {rollback_error}")

            self.performance_metrics["failed_tasks"] += 1
            instance["status"] = "error"

            return {
                "status": "error",
                "message": str(e),
                "instance_id": instance_id
            }

    async def _check_quota_availability(self, required_prompts: int) -> bool:
        """检查用量可用性"""
        return await self.rate_limiter.check_availability(required_prompts)

    async def _process_task_queue(self):
        """处理任务队列"""
        while self.is_running:
            try:
                # 从队列获取任务
                queue_item = await asyncio.wait_for(
                    self.instance_queue.get(),
                    timeout=1.0
                )

                instance_id = queue_item["instance_id"]
                task_data = queue_item["task_data"]
                queue_time = queue_item["queue_time"]

                # 检查等待时间
                wait_time = (datetime.now() - queue_time).total_seconds()
                if wait_time > self.quota_config.max_wait_time_seconds:
                    logger.warning(f"Task for instance {instance_id} expired after waiting {wait_time}s")
                    continue

                # 尝试执行任务
                if await self._check_quota_availability(self.active_instances[instance_id]["estimated_prompts"]):
                    await self._execute_task_with_quota_control(instance_id, task_data)
                else:
                    # 重新加入队列
                    await self.instance_queue.put(queue_item)
                    await asyncio.sleep(5)  # 等待5秒后重试

            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing task queue: {e}")

    async def _monitor_instances(self):
        """监控实例状态和用量"""
        while self.is_running:
            try:
                # 更新内存使用量
                for instance in self.active_instances.values():
                    if instance["process_id"]:
                        try:
                            process = psutil.Process(instance["process_id"])
                            instance["memory_usage"] = process.memory_info().rss
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass

                # 更新用量效率
                await self._update_usage_efficiency()

                await asyncio.sleep(5)  # 每5秒检查一次

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitor task: {e}")
                await asyncio.sleep(5)

    async def _update_usage_efficiency(self):
        """更新用量效率指标"""
        usage_status = await self.rate_limiter.get_usage_status()
        self.performance_metrics["quota_usage_efficiency"] = usage_status.usage_percentage

    async def _handle_usage_alert(self, alert: UsageAlert):
        """处理用量预警"""
        logger.warning(f"Usage alert: {alert.message}")

        # 调用所有预警处理器
        for handler in self.alert_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(alert)
                else:
                    handler(alert)
            except Exception as e:
                logger.error(f"Error in alert handler: {e}")

        # 根据预警级别调整策略
        if alert.alert_type == "critical":
            # 暂停创建新实例
            logger.info("Critical usage alert - pausing new instance creation")
            # 这里可以实现暂停逻辑

    async def shutdown_instance(self, instance_id: str) -> bool:
        """关闭指定实例"""
        if instance_id not in self.active_instances:
            logger.warning(f"Instance {instance_id} not found")
            return False

        instance = self.active_instances[instance_id]
        instance["status"] = "shutting"

        # 清理资源
        if instance["process_id"]:
            try:
                process = psutil.Process(instance["process_id"])
                process.terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        # 更新状态
        instance["status"] = "terminated"
        del self.active_instances[instance_id]

        logger.info(f"Shutdown enhanced instance {instance_id}")
        return True

    async def get_pool_status(self) -> Dict:
        """获取实例池状态（包含用量信息）"""
        # 获取用量状态
        usage_status = await self.rate_limiter.get_usage_status()
        plan_info = self.rate_limiter.get_plan_info()

        # 统计实例状态
        status_counts = {}
        for instance in self.active_instances.values():
            status = instance["status"]
            status_counts[status] = status_counts.get(status, 0) + 1

        # 计算总内存使用
        total_memory = sum(instance["memory_usage"] for instance in self.active_instances.values())
        self.performance_metrics["pool_memory_usage"] = total_memory

        return {
            "pool_type": "enhanced_with_quota_control",
            "pool_status": "running" if self.is_running else "stopped",
            "max_instances": self.max_concurrent_instances,
            "active_instances": len(self.active_instances),
            "instance_status_counts": status_counts,
            "performance_metrics": self.performance_metrics,
            "quota_status": {
                "current_usage": usage_status.to_dict(),
                "plan_info": plan_info,
                "quota_control_enabled": self.quota_config.enable_quota_control,
                "quota_exhaustion_strategy": self.quota_config.quota_exhaustion_strategy.value,
                "queue_length": self.instance_queue.qsize()
            },
            "instances": list(self.active_instances.values())
        }

    async def add_alert_handler(self, handler: Callable):
        """添加预警处理器"""
        self.alert_handlers.append(handler)

    async def remove_alert_handler(self, handler: Callable):
        """移除预警处理器"""
        if handler in self.alert_handlers:
            self.alert_handlers.remove(handler)

    async def get_usage_dashboard(self) -> Dict:
        """获取用量仪表板数据"""
        return await self.usage_monitor.create_usage_dashboard()

    async def generate_usage_report(self, days: int = 7) -> Dict:
        """生成用量报告"""
        return await self.usage_monitor.generate_usage_report(days)


# 工厂函数
async def create_enhanced_instance_pool(max_concurrent_instances: int = 6,
                                      plan_type: str = "pro") -> EnhancedGLMInstancePool:
    """创建增强版实例池

    Args:
        max_concurrent_instances: 最大并发实例数
        plan_type: GLM套餐类型

    Returns:
        EnhancedGLMInstancePool: 增强版实例池实例
    """
    # 创建速率限制器
    from glm_rate_limiter import create_rate_limiter
    rate_limiter = create_rate_limiter(plan_type)

    # 创建用量控制配置
    quota_config = QuotaControlConfig(
        enable_quota_control=True,
        quota_exhaustion_strategy=QuotaExhaustionStrategy.QUEUE
    )

    # 创建增强版实例池
    pool = EnhancedGLMInstancePool(
        max_concurrent_instances=max_concurrent_instances,
        quota_control_config=quota_config,
        rate_limiter=rate_limiter
    )

    await pool.start()
    return pool


# 全局增强版实例池
_enhanced_pool: Optional[EnhancedGLMInstancePool] = None


async def get_enhanced_pool() -> EnhancedGLMInstancePool:
    """获取全局增强版实例池"""
    global _enhanced_pool
    if _enhanced_pool is None:
        _enhanced_pool = await create_enhanced_instance_pool()
    return _enhanced_pool


async def start_enhanced_pool():
    """启动全局增强版实例池"""
    pool = await get_enhanced_pool()
    # pool is already started in create_enhanced_instance_pool


async def stop_enhanced_pool():
    """停止全局增强版实例池"""
    global _enhanced_pool
    if _enhanced_pool:
        await _enhanced_pool.stop()
        _enhanced_pool = None