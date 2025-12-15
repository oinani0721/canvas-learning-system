"""
智能任务分发器 - 增强版

提供多种任务分发策略，包括基于复杂度、性能和动态负载均衡的
智能分发算法。

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-24
Story: 10.4 - Canvas并行处理集成引擎
"""

import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

try:
    import statistics
    HAS_STATISTICS = True
except ImportError:
    HAS_STATISTICS = False

from parallel_canvas_processor import (
    ProcessingTask, NodeComplexity, LoadBalanceStrategy,
    TaskDistributionConfig
)

try:
    from loguru import logger
    LOGURU_ENABLED = True
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    LOGURU_ENABLED = False


@dataclass
class InstanceMetrics:
    """实例性能指标"""
    instance_id: str
    total_tasks_processed: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    total_processing_time: float = 0.0  # 总处理时间（秒）
    average_task_time: float = 0.0  # 平均任务处理时间
    last_activity: Optional[datetime] = None
    current_load: int = 0  # 当前任务数
    max_concurrent: int = 10  # 最大并发数
    complexity_scores: List[float] = field(default_factory=list)  # 历史复杂度分数
    reliability_score: float = 1.0  # 可靠性分数 (0-1)
    performance_score: float = 1.0  # 性能分数 (0-1)

    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_tasks_processed == 0:
            return 1.0
        return self.successful_tasks / self.total_tasks_processed

    @property
    def load_percentage(self) -> float:
        """负载百分比"""
        return (self.current_load / self.max_concurrent) * 100

    def update_metrics(self, task: ProcessingTask, success: bool, processing_time: float):
        """更新指标"""
        self.total_tasks_processed += 1
        self.total_processing_time += processing_time
        self.average_task_time = self.total_processing_time / self.total_tasks_processed
        self.last_activity = datetime.now()
        self.current_load = max(0, self.current_load - 1)

        if success:
            self.successful_tasks += 1
        else:
            self.failed_tasks += 1

        # 更新复杂度分数历史
        self.complexity_scores.append(task.complexity.value)
        if len(self.complexity_scores) > 100:
            self.complexity_scores.pop(0)

        # 更新可靠性分数
        self.reliability_score = 0.7 * self.reliability_score + 0.3 * (1.0 if success else 0.0)

        # 更新性能分数（基于处理时间）
        expected_time = _estimate_expected_time(task.complexity, task.agent_type)
        performance_ratio = expected_time / max(processing_time, 0.1)
        self.performance_score = 0.8 * self.performance_score + 0.2 * min(1.0, performance_ratio)


class AdvancedTaskDistributor:
    """高级任务分发器

    实现多种智能分发策略，包括：
    - 轮询分发
    - 基于复杂度的分发
    - 基于性能的分发
    - 动态负载均衡
    - 预测性分发
    """

    def __init__(self, config: TaskDistributionConfig):
        self.config = config
        self.instance_metrics: Dict[str, InstanceMetrics] = {}
        self.distribution_history: List[Dict] = []
        self._lock = asyncio.Lock()

    async def register_instance(self, instance_id: str, max_concurrent: int = 10):
        """注册实例"""
        async with self._lock:
            self.instance_metrics[instance_id] = InstanceMetrics(
                instance_id=instance_id,
                max_concurrent=max_concurrent
            )
            logger.info(f"Registered instance: {instance_id} (max_concurrent: {max_concurrent})")

    async def unregister_instance(self, instance_id: str):
        """注销实例"""
        async with self._lock:
            if instance_id in self.instance_metrics:
                del self.instance_metrics[instance_id]
                logger.info(f"Unregistered instance: {instance_id}")

    async def distribute_tasks(self,
                              tasks: List[ProcessingTask],
                              available_instances: List[str],
                              strategy: LoadBalanceStrategy = LoadBalanceStrategy.ROUND_ROBIN) -> Dict[str, List[ProcessingTask]]:
        """智能分发任务到实例"""
        logger.info(f"Distributing {len(tasks)} tasks using {strategy.value} strategy")

        # 确保所有实例都已注册
        for instance_id in available_instances:
            if instance_id not in self.instance_metrics:
                await self.register_instance(instance_id)

        # 根据策略分发
        if strategy == LoadBalanceStrategy.ROUND_ROBIN:
            distribution = await self._distribute_round_robin(tasks, available_instances)
        elif strategy == LoadBalanceStrategy.COMPLEXITY_BASED:
            distribution = await self._distribute_complexity_based(tasks, available_instances)
        elif strategy == LoadBalanceStrategy.PERFORMANCE_BASED:
            distribution = await self._distribute_performance_based(tasks, available_instances)
        else:
            # 默认使用智能负载均衡
            distribution = await self._distribute_adaptive(tasks, available_instances)

        # 更新实例负载
        async with self._lock:
            for instance_id, task_list in distribution.items():
                if instance_id in self.instance_metrics:
                    self.instance_metrics[instance_id].current_load += len(task_list)

        # 记录分发历史
        self._record_distribution(distribution, strategy)

        return distribution

    async def _distribute_round_robin(self,
                                     tasks: List[ProcessingTask],
                                     instances: List[str]) -> Dict[str, List[ProcessingTask]]:
        """轮询分发策略"""
        distribution = {instance_id: [] for instance_id in instances}

        # 过滤可用实例（有容量接受任务）
        available = []
        for instance_id in instances:
            metrics = self.instance_metrics.get(instance_id)
            if metrics and metrics.current_load < metrics.max_concurrent:
                available.append(instance_id)

        if not available:
            logger.warning("No available instances for round-robin distribution")
            return distribution

        # 轮询分配
        for i, task in enumerate(tasks):
            instance_id = available[i % len(available)]
            distribution[instance_id].append(task)

        return distribution

    async def _distribute_complexity_based(self,
                                          tasks: List[ProcessingTask],
                                          instances: List[str]) -> Dict[str, List[ProcessingTask]]:
        """基于复杂度的分发策略"""
        distribution = {instance_id: [] for instance_id in instances}

        # 按复杂度排序（从高到低）
        sorted_tasks = sorted(tasks, key=lambda t: t.complexity.value, reverse=True)

        # 为每个实例维护复杂度负载
        instance_complexity = {instance_id: 0 for instance_id in instances}

        # 考虑实例当前负载
        for instance_id in instances:
            metrics = self.instance_metrics.get(instance_id)
            if metrics:
                # 根据当前负载调整可接受复杂度
                load_factor = 1.0 - (metrics.current_load / metrics.max_concurrent)
                instance_complexity[instance_id] = metrics.current_load * 10  # 当前复杂度负载

        # 分配任务
        for task in sorted_tasks:
            # 选择复杂度负载最低且有容量的实例
            candidates = []
            for instance_id in instances:
                metrics = self.instance_metrics.get(instance_id)
                if metrics and metrics.current_load < metrics.max_concurrent:
                    candidates.append((instance_id, instance_complexity[instance_id]))

            if not candidates:
                # 没有可用实例，跳过
                continue

            # 选择负载最低的实例
            selected_instance = min(candidates, key=lambda x: x[1])[0]
            distribution[selected_instance].append(task)
            # 将枚举转换为数值进行复杂度累加
            complexity_value = {
                NodeComplexity.LOW: 1,
                NodeComplexity.MEDIUM: 2,
                NodeComplexity.HIGH: 3
            }.get(task.complexity, 2)
            instance_complexity[selected_instance] += complexity_value

        return distribution

    async def _distribute_performance_based(self,
                                           tasks: List[ProcessingTask],
                                           instances: List[str]) -> Dict[str, List[ProcessingTask]]:
        """基于性能的分发策略"""
        distribution = {instance_id: [] for instance_id in instances}

        # 计算每个实例的综合评分
        instance_scores = {}
        for instance_id in instances:
            metrics = self.instance_metrics.get(instance_id)
            if metrics:
                # 综合评分 = 可靠性 * 性能 * (1 - 负载率)
                load_factor = 1.0 - (metrics.current_load / metrics.max_concurrent)
                score = metrics.reliability_score * metrics.performance_score * load_factor
                instance_scores[instance_id] = score
            else:
                instance_scores[instance_id] = 0.5  # 新实例默认分数

        # 按任务复杂度排序，优先分配重要任务到高性能实例
        sorted_tasks = sorted(tasks, key=lambda t: t.complexity.value, reverse=True)

        for task in sorted_tasks:
            # 选择评分最高且有容量的实例
            candidates = []
            for instance_id, score in instance_scores.items():
                metrics = self.instance_metrics.get(instance_id)
                if metrics and metrics.current_load < metrics.max_concurrent:
                    candidates.append((instance_id, score))

            if not candidates:
                continue

            # 选择最高评分的实例
            selected_instance = max(candidates, key=lambda x: x[1])[0]
            distribution[selected_instance].append(task)

            # 更新评分（考虑新负载）
            metrics = self.instance_metrics[selected_instance]
            load_factor = 1.0 - (metrics.current_load + 1) / metrics.max_concurrent
            instance_scores[selected_instance] = metrics.reliability_score * metrics.performance_score * load_factor

        return distribution

    async def _distribute_adaptive(self,
                                  tasks: List[ProcessingTask],
                                  instances: List[str]) -> Dict[str, List[ProcessingTask]]:
        """自适应分发策略（结合多种因素）"""
        # 分析任务特征
        if HAS_STATISTICS:
            avg_complexity = statistics.mean([t.complexity.value for t in tasks])
        else:
            complexity_values = [t.complexity.value for t in tasks]
            avg_complexity = sum(complexity_values) / len(complexity_values) if complexity_values else 0
        high_complexity_ratio = sum(1 for t in tasks if t.complexity == NodeComplexity.HIGH) / len(tasks)

        # 根据任务特征选择策略
        if high_complexity_ratio > 0.5:
            # 高复杂度任务多，使用复杂度策略
            return await self._distribute_complexity_based(tasks, instances)
        elif avg_complexity < 2:
            # 简单任务多，使用性能策略
            return await self._distribute_performance_based(tasks, instances)
        else:
            # 混合任务，使用轮询
            return await self._distribute_round_robin(tasks, instances)

    async def rebalance_tasks(self,
                             current_assignments: Dict[str, List[ProcessingTask]],
                             new_tasks: List[ProcessingTask]) -> Dict[str, List[ProcessingTask]]:
        """动态负载均衡"""
        logger.info("Rebalancing tasks across instances")

        # 计算每个实例的预期负载
        total_instances = len(current_assignments)
        if total_instances == 0:
            return {}

        # 找出过载和空闲的实例
        overloaded = {}
        underloaded = {}

        for instance_id, task_list in current_assignments.items():
            metrics = self.instance_metrics.get(instance_id)
            if metrics:
                if metrics.load_percentage > 80:  # 超过80%负载
                    overloaded[instance_id] = task_list
                elif metrics.load_percentage < 50:  # 低于50%负载
                    underloaded[instance_id] = task_list

        # 从过载实例移动任务到空闲实例
        moved_tasks = 0
        for overloaded_id, tasks in overloaded.items():
            for underloaded_id in underloaded:
                if tasks and moved_tasks < len(new_tasks) // 4:  # 最多移动25%的任务
                    # 移动一个任务
                    task = tasks.pop()
                    current_assignments[underloaded_id].append(task)
                    moved_tasks += 1
                    logger.info(f"Moved task {task.task_id} from {overloaded_id} to {underloaded_id}")

        # 添加新任务
        for task in new_tasks:
            # 找到负载最低的实例
            min_load_instance = min(
                current_assignments.keys(),
                key=lambda i: len(current_assignments[i]) if i in self.instance_metrics else float('inf')
            )
            current_assignments[min_load_instance].append(task)

        return current_assignments

    async def get_instance_performance_report(self) -> Dict:
        """获取实例性能报告"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_instances": len(self.instance_metrics),
            "instances": {}
        }

        for instance_id, metrics in self.instance_metrics.items():
            report["instances"][instance_id] = {
                "total_tasks": metrics.total_tasks_processed,
                "success_rate": metrics.success_rate,
                "average_task_time": metrics.average_task_time,
                "current_load": metrics.current_load,
                "load_percentage": metrics.load_percentage,
                "reliability_score": metrics.reliability_score,
                "performance_score": metrics.performance_score,
                "last_activity": metrics.last_activity.isoformat() if metrics.last_activity else None
            }

        return report

    def _record_distribution(self, distribution: Dict, strategy: LoadBalanceStrategy):
        """记录分发历史"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "strategy": strategy.value,
            "total_tasks": sum(len(tasks) for tasks in distribution.values()),
            "distribution": {iid: len(tasks) for iid, tasks in distribution.items()}
        }
        self.distribution_history.append(record)

        # 保持历史记录不超过1000条
        if len(self.distribution_history) > 1000:
            self.distribution_history.pop(0)


def _estimate_expected_time(complexity: NodeComplexity, agent_type: str) -> float:
    """估算预期处理时间"""
    base_times = {
        'basic-decomposition': 10.0,
        'deep-decomposition': 20.0,
        'oral-explanation': 30.0,
        'clarification-path': 40.0,
        'comparison-table': 25.0,
        'memory-anchor': 20.0,
        'four-level-explanation': 35.0,
        'example-teaching': 30.0,
        'scoring-agent': 10.0,
        'verification-question-agent': 15.0
    }

    base_time = base_times.get(agent_type, 30.0)
    multipliers = {
        NodeComplexity.LOW: 0.5,
        NodeComplexity.MEDIUM: 1.0,
        NodeComplexity.HIGH: 2.0
    }

    return base_time * multipliers[complexity]