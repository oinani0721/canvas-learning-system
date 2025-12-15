"""
动态实例管理器 - Canvas学习系统

本模块实现智能的并行实例数调整算法，包括：
- 系统负载评估
- 动态扩缩容决策
- 性能优化建议
- 自动调整策略

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-27
Story: 10.6 - Task 2
"""

import asyncio
import time
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

# 导入性能监控器
from performance_monitor import PerformanceMonitor, ResourceMetrics

# 导入实例池
try:
    from enhanced_agent_instance_pool import EnhancedGLMInstancePool
    ENHANCED_POOL_AVAILABLE = True
except ImportError:
    try:
        from agent_instance_pool import GLMInstancePool
        ENHANCED_POOL_AVAILABLE = False
    except ImportError:
        ENHANCED_POOL_AVAILABLE = False


class ScalingDirection(Enum):
    """扩缩容方向"""
    SCALE_UP = "scale_up"      # 扩容
    SCALE_DOWN = "scale_down"  # 缩容
    MAINTAIN = "maintain"      # 保持不变


class AdjustmentStrategy(Enum):
    """调整策略"""
    AGGRESSIVE = "aggressive"    # 激进调整
    CONSERVATIVE = "conservative"  # 保守调整
    BALANCED = "balanced"       # 平衡调整


@dataclass
class SystemLoadInfo:
    """系统负载信息"""
    cpu_usage: float  # 0-100%
    memory_usage: float  # 0-100%
    active_instances: int
    queued_tasks: int
    avg_response_time: float  # ms
    error_rate: float  # 0-1
    throughput: float  # tasks/sec
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def load_score(self) -> float:
        """综合负载分数 0-1"""
        cpu_score = self.cpu_usage / 100
        memory_score = self.memory_usage / 100
        response_score = min(self.avg_response_time / 5000, 1)  # 5s作为满分
        error_score = self.error_rate

        return (cpu_score * 0.3 + memory_score * 0.25 +
                response_score * 0.25 + error_score * 0.2)

    @property
    def efficiency_score(self) -> float:
        """效率分数 0-1"""
        if self.active_instances == 0:
            return 0.0

        # 吞吐量 per instance
        throughput_per_instance = self.throughput / self.active_instances

        # 响应时间分数（越低越好）
        response_score = max(0, 1 - self.avg_response_time / 3000)  # 3s作为基准

        # 错误率分数（越低越好）
        error_score = max(0, 1 - self.error_rate)

        return (throughput_per_instance * 0.4 + response_score * 0.3 + error_score * 0.3)


@dataclass
class OptimizationRecommendation:
    """优化建议"""
    recommendation_id: str
    recommendation_type: str  # "scale_up", "scale_down", "adjust_cache", "tune_params"
    priority: str  # "high", "medium", "low"
    description: str
    expected_improvement: float  # 预期改善百分比
    implementation_cost: str  # "low", "medium", "high"
    auto_applicable: bool = False
    parameters: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class DynamicAdjustmentResult:
    """动态调整结果"""
    adjustment_id: str
    adjustment_type: str
    old_value: Any
    new_value: Any
    adjustment_time: datetime = field(default_factory=datetime.now)
    success: bool = True
    performance_impact: Optional[Dict[str, float]] = None
    rollback_available: bool = True
    rollback_reason: Optional[str] = None


class DynamicInstanceManager:
    """动态实例管理器

    基于系统负载和性能指标，智能调整并行实例数量，
    以达到最佳的性能和资源利用效率。
    """

    def __init__(self,
                 instance_pool,
                 performance_monitor: PerformanceMonitor,
                 config: Dict[str, Any]):
        """初始化动态实例管理器

        Args:
            instance_pool: 实例池对象
            performance_monitor: 性能监控器
            config: 配置参数
        """
        self.instance_pool = instance_pool
        self.performance_monitor = performance_monitor
        self.config = config

        # 调整参数
        self.min_instances = config.get("min_instances", 1)
        self.max_instances = config.get("max_instances", 8)
        self.scale_up_threshold = config.get("scale_up_threshold", 0.7)  # 负载分数
        self.scale_down_threshold = config.get("scale_down_threshold", 0.3)
        self.adjustment_cooldown = config.get("adjustment_cooldown_seconds", 60)
        self.adjustment_strategy = AdjustmentStrategy(
            config.get("adjustment_strategy", "balanced")
        )

        # 性能目标
        self.target_response_time = config.get("target_response_time_ms", 2000)
        self.target_throughput_per_instance = config.get("target_throughput_per_instance", 0.5)
        self.max_error_rate = config.get("max_error_rate", 0.05)  # 5%

        # 状态跟踪
        self.last_adjustment_time = 0
        self.adjustment_history: List[DynamicAdjustmentResult] = []
        self.load_history: List[SystemLoadInfo] = []
        self.recommendations: List[OptimizationRecommendation] = []

        # 自动调整开关
        self.auto_adjustment_enabled = config.get("auto_adjustment_enabled", True)
        self.adjustment_task: Optional[asyncio.Task] = None
        self.monitoring_active = False

        # 调整统计
        self.stats = {
            "total_adjustments": 0,
            "scale_up_count": 0,
            "scale_down_count": 0,
            "successful_adjustments": 0,
            "failed_adjustments": 0
        }

    async def start_monitoring(self) -> None:
        """启动动态监控"""
        if self.monitoring_active:
            return

        self.monitoring_active = True
        self.adjustment_task = asyncio.create_task(self._monitoring_loop())

        print(f"DynamicInstanceManager started with strategy: {self.adjustment_strategy.value}")

    async def stop_monitoring(self) -> None:
        """停止动态监控"""
        self.monitoring_active = False
        if self.adjustment_task:
            self.adjustment_task.cancel()
            try:
                await self.adjustment_task
            except asyncio.CancelledError:
                pass

    async def _monitoring_loop(self) -> None:
        """监控主循环"""
        while self.monitoring_active:
            try:
                # 评估系统负载
                load_info = await self.assess_system_load()

                # 记录负载历史
                self.load_history.append(load_info)
                if len(self.load_history) > 100:  # 保留最近100条记录
                    self.load_history = self.load_history[-100:]

                # 自动调整（如果启用）
                if self.auto_adjustment_enabled:
                    await self._auto_adjust(load_info)

                # 生成优化建议
                await self._update_recommendations(load_info)

                await asyncio.sleep(30)  # 每30秒检查一次

            except Exception as e:
                print(f"DynamicInstanceManager monitoring error: {e}")
                await asyncio.sleep(10)

    async def assess_system_load(self) -> SystemLoadInfo:
        """评估系统负载

        Returns:
            SystemLoadInfo: 系统负载信息
        """
        # 获取当前资源指标
        if self.performance_monitor.resource_metrics_history:
            recent_metrics = self.performance_monitor.resource_metrics_history[-1]
            cpu_usage = recent_metrics.cpu_percent
            memory_usage = recent_metrics.memory_percent
        else:
            # 如果没有监控数据，使用psutil直接获取
            import psutil
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            memory_usage = memory.percent

        # 获取当前活跃实例数
        if hasattr(self.instance_pool, 'active_instances'):
            active_instances = len(self.instance_pool.active_instances)
        else:
            active_instances = getattr(self.instance_pool, 'current_instance_count', 1)

        # 获取队列任务数
        if hasattr(self.instance_pool, 'instance_queue'):
            queued_tasks = self.instance_pool.instance_queue.qsize()
        else:
            queued_tasks = 0

        # 获取执行指标
        if self.performance_monitor.execution_metrics_history:
            recent_executions = self.performance_monitor.execution_metrics_history[-5:]
            avg_response_time = statistics.mean(
                m.average_task_time_ms for m in recent_executions
            )
            throughput = statistics.mean(
                m.throughput_tasks_per_second for m in recent_executions
            )

            # 计算错误率
            total_tasks = sum(m.task_count for m in recent_executions)
            failed_tasks = sum(m.failed_tasks for m in recent_executions)
            error_rate = failed_tasks / total_tasks if total_tasks > 0 else 0
        else:
            avg_response_time = 1000  # 默认1秒
            throughput = 0.1
            error_rate = 0

        return SystemLoadInfo(
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            active_instances=active_instances,
            queued_tasks=queued_tasks,
            avg_response_time=avg_response_time,
            error_rate=error_rate,
            throughput=throughput
        )

    async def should_scale_up(self, load_info: SystemLoadInfo) -> bool:
        """判断是否应该扩容

        Args:
            load_info: 系统负载信息

        Returns:
            bool: 是否应该扩容
        """
        # 检查是否已达到最大实例数
        if load_info.active_instances >= self.max_instances:
            return False

        # 检查冷却时间
        if time.time() - self.last_adjustment_time < self.adjustment_cooldown:
            return False

        # 根据策略判断
        if self.adjustment_strategy == AdjustmentStrategy.AGGRESSIVE:
            # 激进策略：负载超过阈值或队列积压
            return (load_info.load_score > self.scale_up_threshold or
                    load_info.queued_tasks > 3 or
                    load_info.avg_response_time > self.target_response_time * 1.5)

        elif self.adjustment_strategy == AdjustmentStrategy.CONSERVATIVE:
            # 保守策略：综合判断
            return (load_info.load_score > self.scale_up_threshold * 1.2 and
                    load_info.queued_tasks > 5 and
                    load_info.avg_response_time > self.target_response_time * 2)

        else:  # BALANCED
            # 平衡策略：多因素判断
            reasons = []
            if load_info.load_score > self.scale_up_threshold:
                reasons.append("high_load")
            if load_info.queued_tasks > 3:
                reasons.append("queue_backup")
            if load_info.avg_response_time > self.target_response_time:
                reasons.append("slow_response")
            if load_info.efficiency_score < 0.5:
                reasons.append("low_efficiency")

            return len(reasons) >= 2

    async def should_scale_down(self, load_info: SystemLoadInfo) -> bool:
        """判断是否应该缩容

        Args:
            load_info: 系统负载信息

        Returns:
            bool: 是否应该缩容
        """
        # 检查是否已达到最小实例数
        if load_info.active_instances <= self.min_instances:
            return False

        # 检查冷却时间
        if time.time() - self.last_adjustment_time < self.adjustment_cooldown:
            return False

        # 根据策略判断
        if self.adjustment_strategy == AdjustmentStrategy.AGGRESSIVE:
            # 激进策略：负载很低就缩容
            return (load_info.load_score < self.scale_down_threshold and
                    load_info.queued_tasks == 0 and
                    load_info.efficiency_score > 0.8)

        elif self.adjustment_strategy == AdjustmentStrategy.CONSERVATIVE:
            # 保守策略：连续低负载才缩容
            if len(self.load_history) < 5:
                return False

            recent_loads = self.load_history[-5:]
            avg_load = statistics.mean(l.load_score for l in recent_loads)
            return (avg_load < self.scale_down_threshold * 0.8 and
                    all(l.queued_tasks == 0 for l in recent_loads))

        else:  # BALANCED
            # 平衡策略：综合判断
            return (load_info.load_score < self.scale_down_threshold and
                    load_info.queued_tasks == 0 and
                    load_info.efficiency_score > 0.7 and
                    load_info.avg_response_time < self.target_response_time * 0.5)

    async def adjust_instance_count(self, target_count: int) -> DynamicAdjustmentResult:
        """调整实例数量

        Args:
            target_count: 目标实例数

        Returns:
            DynamicAdjustmentResult: 调整结果
        """
        adjustment_id = f"adj-{int(time.time())}"
        old_count = await self._get_current_instance_count()

        try:
            # 执行调整
            if target_count > old_count:
                # 扩容
                success = await self._scale_up(target_count - old_count)
                adjustment_type = "scale_up"
            elif target_count < old_count:
                # 缩容
                success = await self._scale_down(old_count - target_count)
                adjustment_type = "scale_down"
            else:
                # 无需调整
                return DynamicAdjustmentResult(
                    adjustment_id=adjustment_id,
                    adjustment_type="no_change",
                    old_value=old_count,
                    new_value=old_count,
                    success=True
                )

            if success:
                # 记录调整
                result = DynamicAdjustmentResult(
                    adjustment_id=adjustment_id,
                    adjustment_type=adjustment_type,
                    old_value=old_count,
                    new_value=target_count,
                    success=True
                )

                self.adjustment_history.append(result)
                self.last_adjustment_time = time.time()

                # 更新统计
                self.stats["total_adjustments"] += 1
                if adjustment_type == "scale_up":
                    self.stats["scale_up_count"] += 1
                else:
                    self.stats["scale_down_count"] += 1
                self.stats["successful_adjustments"] += 1

                print(f"Instance count adjusted: {old_count} -> {target_count} ({adjustment_type})")
                return result
            else:
                raise Exception("Adjustment failed")

        except Exception as e:
            self.stats["failed_adjustments"] += 1
            print(f"Failed to adjust instance count: {e}")

            return DynamicAdjustmentResult(
                adjustment_id=adjustment_id,
                adjustment_type="failed",
                old_value=old_count,
                new_value=old_count,
                success=False,
                rollback_reason=str(e)
            )

    async def _get_current_instance_count(self) -> int:
        """获取当前实例数"""
        if hasattr(self.instance_pool, 'active_instances'):
            return len(self.instance_pool.active_instances)
        else:
            return getattr(self.instance_pool, 'current_instance_count', 1)

    async def _scale_up(self, increment: int) -> bool:
        """扩容实例"""
        try:
            if hasattr(self.instance_pool, 'set_max_concurrent_instances'):
                # 如果支持动态调整最大并发数
                current_max = self.instance_pool.max_concurrent_instances
                new_max = min(current_max + increment, self.max_instances)
                await self.instance_pool.set_max_concurrent_instances(new_max)
                return True
            else:
                print(f"Instance pool doesn't support dynamic scaling")
                return False
        except Exception as e:
            print(f"Scale up failed: {e}")
            return False

    async def _scale_down(self, decrement: int) -> bool:
        """缩容实例"""
        try:
            if hasattr(self.instance_pool, 'set_max_concurrent_instances'):
                # 如果支持动态调整最大并发数
                current_max = self.instance_pool.max_concurrent_instances
                new_max = max(current_max - decrement, self.min_instances)
                await self.instance_pool.set_max_concurrent_instances(new_max)
                return True
            else:
                print(f"Instance pool doesn't support dynamic scaling")
                return False
        except Exception as e:
            print(f"Scale down failed: {e}")
            return False

    async def _auto_adjust(self, load_info: SystemLoadInfo) -> None:
        """自动调整实例数"""
        # 判断调整方向
        if await self.should_scale_up(load_info):
            scaling_direction = ScalingDirection.SCALE_UP
            adjustment_size = self._calculate_adjustment_size(scaling_direction)
            target_count = min(load_info.active_instances + adjustment_size,
                            self.max_instances)
        elif await self.should_scale_down(load_info):
            scaling_direction = ScalingDirection.SCALE_DOWN
            adjustment_size = self._calculate_adjustment_size(scaling_direction)
            target_count = max(load_info.active_instances - adjustment_size,
                            self.min_instances)
        else:
            return  # 无需调整

        # 执行调整
        await self.adjust_instance_count(target_count)

    def _calculate_adjustment_size(self, direction: ScalingDirection) -> int:
        """计算调整大小"""
        if direction == ScalingDirection.SCALE_UP:
            if self.adjustment_strategy == AdjustmentStrategy.AGGRESSIVE:
                return min(3, self.max_instances // 2)
            elif self.adjustment_strategy == AdjustmentStrategy.CONSERVATIVE:
                return 1
            else:  # BALANCED
                return 2
        else:  # SCALE_DOWN
            if self.adjustment_strategy == AdjustmentStrategy.AGGRESSIVE:
                return max(2, self.max_instances // 3)
            elif self.adjustment_strategy == AdjustmentStrategy.CONSERVATIVE:
                return 1
            else:  # BALANCED
                return 1

    async def _update_recommendations(self, load_info: SystemLoadInfo) -> None:
        """更新优化建议"""
        self.recommendations.clear()

        # 响应时间优化建议
        if load_info.avg_response_time > self.target_response_time * 1.5:
            self.recommendations.append(OptimizationRecommendation(
                recommendation_id=f"resp-time-{int(time.time())}",
                recommendation_type="scale_up",
                priority="high",
                description=f"响应时间过长 ({load_info.avg_response_time:.0f}ms)，建议增加实例数",
                expected_improvement=30.0,
                implementation_cost="low",
                auto_applicable=True,
                parameters={"increment": 2}
            ))

        # 内存使用优化建议
        if load_info.memory_usage > 85:
            self.recommendations.append(OptimizationRecommendation(
                recommendation_id=f"mem-usage-{int(time.time())}",
                recommendation_type="tune_params",
                priority="high",
                description=f"内存使用率过高 ({load_info.memory_usage:.1f}%)，建议优化Agent内存使用",
                expected_improvement=20.0,
                implementation_cost="medium",
                parameters={"reduce_context_size": True}
            ))

        # CPU使用优化建议
        if load_info.cpu_usage > 80:
            self.recommendations.append(OptimizationRecommendation(
                recommendation_id=f"cpu-usage-{int(time.time())}",
                recommendation_type="scale_down",
                priority="medium",
                description=f"CPU使用率过高 ({load_info.cpu_usage:.1f}%)，可能需要优化算法",
                expected_improvement=15.0,
                implementation_cost="high",
                auto_applicable=False
            ))

        # 错误率优化建议
        if load_info.error_rate > self.max_error_rate:
            self.recommendations.append(OptimizationRecommendation(
                recommendation_id=f"error-rate-{int(time.time())}",
                recommendation_type="tune_params",
                priority="high",
                description=f"错误率过高 ({load_info.error_rate:.1%})，建议检查Agent实现",
                expected_improvement=50.0,
                implementation_cost="medium",
                auto_applicable=False
            ))

    async def get_optimization_recommendations(self) -> List[OptimizationRecommendation]:
        """获取优化建议

        Returns:
            List[OptimizationRecommendation]: 优化建议列表
        """
        return sorted(self.recommendations,
                     key=lambda r: (r.priority == "high", r.expected_improvement),
                     reverse=True)

    async def auto_optimize(self) -> List[DynamicAdjustmentResult]:
        """自动优化

        Returns:
            List[DynamicAdjustmentResult]: 调整结果列表
        """
        results = []

        # 应用自动可执行的建议
        for recommendation in self.recommendations:
            if recommendation.auto_applicable:
                if recommendation.recommendation_type == "scale_up":
                    increment = recommendation.parameters.get("increment", 1)
                    current_count = await self._get_current_instance_count()
                    target_count = min(current_count + increment, self.max_instances)
                    result = await self.adjust_instance_count(target_count)
                    results.append(result)

        return results

    def get_adjustment_statistics(self) -> Dict[str, Any]:
        """获取调整统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        recent_adjustments = self.adjustment_history[-10:]  # 最近10次调整

        return {
            "total_adjustments": self.stats["total_adjustments"],
            "scale_up_count": self.stats["scale_up_count"],
            "scale_down_count": self.stats["scale_down_count"],
            "successful_adjustments": self.stats["successful_adjustments"],
            "failed_adjustments": self.stats["failed_adjustments"],
            "success_rate": (self.stats["successful_adjustments"] /
                           max(self.stats["total_adjustments"], 1)),
            "recent_adjustments": [
                {
                    "id": adj.adjustment_id,
                    "type": adj.adjustment_type,
                    "time": adj.adjustment_time.isoformat(),
                    "success": adj.success
                }
                for adj in recent_adjustments
            ],
            "current_instance_count": asyncio.run(self._get_current_instance_count()),
            "auto_adjustment_enabled": self.auto_adjustment_enabled
        }