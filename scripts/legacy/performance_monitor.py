"""
性能监控器 - Canvas学习系统

负责监控并行Agent处理的性能指标，包括：
- 并行效率指标计算
- 资源使用监控
- 性能调优建议
- 实时性能数据收集

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-22
Story: 8.14 (Task 6)
"""

import asyncio
import time
import psutil
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field, asdict
from pathlib import Path
import threading
import statistics


@dataclass
class ResourceMetrics:
    """资源使用指标"""
    timestamp: float
    cpu_percent: float
    memory_usage_mb: float
    memory_percent: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_io_sent_mb: float
    network_io_recv_mb: float
    active_processes: int
    active_threads: int

    def to_dict(self) -> Dict[str, float]:
        """转换为字典格式"""
        return asdict(self)


@dataclass
class ExecutionMetrics:
    """执行性能指标"""
    execution_id: str
    task_count: int
    successful_tasks: int
    failed_tasks: int
    total_execution_time_ms: float
    average_task_time_ms: float
    parallel_efficiency: float
    concurrency_utilization: float
    throughput_tasks_per_second: float
    resource_efficiency: float

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return asdict(self)


@dataclass
class PerformanceAlert:
    """性能告警"""
    alert_id: str = field(default_factory=lambda: f"alert-{int(time.time())}")
    timestamp: float = field(default_factory=time.time)
    alert_type: str = ""  # memory, cpu, throughput, error_rate
    severity: str = "medium"  # low, medium, high, critical
    title: str = ""
    description: str = ""
    current_value: float = 0.0
    threshold_value: float = 0.0
    recommendation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return asdict(self)


class PerformanceMonitor:
    """性能监控器主类

    提供全面的并行Agent处理性能监控功能，
    包括资源监控、执行指标计算、性能分析和调优建议。
    """

    def __init__(self, config: Dict[str, Any]):
        """初始化性能监控器

        Args:
            config: 性能监控配置
        """
        self.config = config
        self.enabled = config.get("enabled", True)
        self.collect_metrics = config.get("collect_metrics", True)
        self.log_performance_data = config.get("log_performance_data", True)

        # 性能阈值配置
        self.slow_execution_threshold = config.get("slow_execution_threshold_seconds", 60) * 1000
        self.memory_alert_threshold = config.get("memory_usage_alert_threshold_mb", 1024)
        self.cpu_alert_threshold = config.get("cpu_usage_alert_threshold_percent", 85)

        # 监控间隔
        self.metrics_collection_interval = config.get("metrics_collection_interval_seconds", 30)

        # 数据存储
        self.resource_metrics_history: List[ResourceMetrics] = []
        self.execution_metrics_history: List[ExecutionMetrics] = []
        self.active_alerts: List[PerformanceAlert] = []

        # 实时监控状态
        self.monitoring_active = False
        self.monitoring_task: Optional[asyncio.Task] = None

        # 回调函数
        self.alert_callbacks: List[Callable[[PerformanceAlert], None]] = []

        # 日志配置
        self.log_file = None
        if self.log_performance_data:
            self._setup_logging()

    def _setup_logging(self) -> None:
        """设置性能日志"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        self.log_file = log_dir / "performance_monitor.log"

    def add_alert_callback(self, callback: Callable[[PerformanceAlert], None]) -> None:
        """添加告警回调函数

        Args:
            callback: 告警回调函数
        """
        self.alert_callbacks.append(callback)

    async def start_monitoring(self) -> None:
        """启动性能监控"""
        if not self.enabled:
            return

        self.monitoring_active = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())

    async def stop_monitoring(self) -> None:
        """停止性能监控"""
        self.monitoring_active = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass

    async def _monitoring_loop(self) -> None:
        """监控主循环"""
        while self.monitoring_active:
            try:
                # 收集资源指标
                if self.collect_metrics:
                    resource_metrics = self._collect_resource_metrics()
                    self.resource_metrics_history.append(resource_metrics)

                    # 检查性能告警
                    await self._check_performance_alerts(resource_metrics)

                    # 记录日志
                    if self.log_file:
                        self._log_resource_metrics(resource_metrics)

                # 清理历史数据（保留最近1000条记录）
                if len(self.resource_metrics_history) > 1000:
                    self.resource_metrics_history = self.resource_metrics_history[-1000:]

                await asyncio.sleep(self.metrics_collection_interval)

            except Exception as e:
                print(f"性能监控错误: {e}")
                await asyncio.sleep(5)  # 错误时短暂等待

    def _collect_resource_metrics(self) -> ResourceMetrics:
        """收集资源使用指标

        Returns:
            ResourceMetrics: 资源指标
        """
        # 获取CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)

        # 获取内存使用情况
        memory = psutil.virtual_memory()
        memory_usage_mb = memory.used / 1024 / 1024
        memory_percent = memory.percent

        # 获取磁盘IO
        disk_io = psutil.disk_io_counters()
        disk_io_read_mb = disk_io.read_bytes / 1024 / 1024 if disk_io else 0
        disk_io_write_mb = disk_io.write_bytes / 1024 / 1024 if disk_io else 0

        # 获取网络IO
        network_io = psutil.net_io_counters()
        network_io_sent_mb = network_io.bytes_sent / 1024 / 1024 if network_io else 0
        network_io_recv_mb = network_io.bytes_recv / 1024 / 1024 if network_io else 0

        # 获取进程和线程数
        active_processes = len(psutil.pids())
        active_threads = threading.active_count()

        return ResourceMetrics(
            timestamp=time.time(),
            cpu_percent=cpu_percent,
            memory_usage_mb=memory_usage_mb,
            memory_percent=memory_percent,
            disk_io_read_mb=disk_io_read_mb,
            disk_io_write_mb=disk_io_write_mb,
            network_io_sent_mb=network_io_sent_mb,
            network_io_recv_mb=network_io_recv_mb,
            active_processes=active_processes,
            active_threads=active_threads
        )

    async def _check_performance_alerts(self, metrics: ResourceMetrics) -> None:
        """检查性能告警条件

        Args:
            metrics: 资源指标
        """
        # 内存使用告警
        if metrics.memory_usage_mb > self.memory_alert_threshold:
            await self._trigger_alert(
                alert_type="memory",
                severity="high" if metrics.memory_usage_mb > self.memory_alert_threshold * 1.5 else "medium",
                title="内存使用率过高",
                description=f"当前内存使用: {metrics.memory_usage_mb:.1f}MB",
                current_value=metrics.memory_usage_mb,
                threshold_value=self.memory_alert_threshold,
                recommendation="考虑增加内存限制或优化Agent内存使用"
            )

        # CPU使用告警
        if metrics.cpu_percent > self.cpu_alert_threshold:
            await self._trigger_alert(
                alert_type="cpu",
                severity="high" if metrics.cpu_percent > self.cpu_alert_threshold * 1.2 else "medium",
                title="CPU使用率过高",
                description=f"当前CPU使用: {metrics.cpu_percent:.1f}%",
                current_value=metrics.cpu_percent,
                threshold_value=self.cpu_alert_threshold,
                recommendation="检查并行任务数量或优化Agent算法"
            )

    async def _trigger_alert(self, **kwargs) -> None:
        """触发性能告警

        Args:
            **kwargs: 告警参数
        """
        alert = PerformanceAlert(**kwargs)
        self.active_alerts.append(alert)

        # 调用回调函数
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                print(f"告警回调错误: {e}")

        # 记录告警日志
        if self.log_file:
            self._log_alert(alert)

    def _log_resource_metrics(self, metrics: ResourceMetrics) -> None:
        """记录资源指标日志

        Args:
            metrics: 资源指标
        """
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                log_entry = {
                    "timestamp": datetime.fromtimestamp(metrics.timestamp).isoformat(),
                    "type": "resource_metrics",
                    "data": metrics.to_dict()
                }
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        except Exception as e:
            print(f"写入性能日志失败: {e}")

    def _log_alert(self, alert: PerformanceAlert) -> None:
        """记录告警日志

        Args:
            alert: 性能告警
        """
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                log_entry = {
                    "timestamp": datetime.fromtimestamp(alert.timestamp).isoformat(),
                    "type": "performance_alert",
                    "data": alert.to_dict()
                }
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        except Exception as e:
            print(f"写入告警日志失败: {e}")

    def record_execution_metrics(self,
                              execution_id: str,
                              task_count: int,
                              successful_tasks: int,
                              failed_tasks: int,
                              total_execution_time_ms: float,
                              parallel_efficiency: float,
                              concurrency_utilization: float) -> ExecutionMetrics:
        """记录执行性能指标

        Args:
            execution_id: 执行ID
            task_count: 任务总数
            successful_tasks: 成功任务数
            failed_tasks: 失败任务数
            total_execution_time_ms: 总执行时间（毫秒）
            parallel_efficiency: 并行效率
            concurrency_utilization: 并发利用率

        Returns:
            ExecutionMetrics: 执行指标
        """
        # 计算平均任务时间
        average_task_time_ms = total_execution_time_ms / task_count if task_count > 0 else 0

        # 计算吞吐量
        throughput_tasks_per_second = task_count / (total_execution_time_ms / 1000) if total_execution_time_ms > 0 else 0

        # 计算资源效率（基于最近资源指标）
        resource_efficiency = self._calculate_resource_efficiency()

        metrics = ExecutionMetrics(
            execution_id=execution_id,
            task_count=task_count,
            successful_tasks=successful_tasks,
            failed_tasks=failed_tasks,
            total_execution_time_ms=total_execution_time_ms,
            average_task_time_ms=average_task_time_ms,
            parallel_efficiency=parallel_efficiency,
            concurrency_utilization=concurrency_utilization,
            throughput_tasks_per_second=throughput_tasks_per_second,
            resource_efficiency=resource_efficiency
        )

        self.execution_metrics_history.append(metrics)

        # 清理历史数据
        if len(self.execution_metrics_history) > 100:
            self.execution_metrics_history = self.execution_metrics_history[-100:]

        return metrics

    def _calculate_resource_efficiency(self) -> float:
        """计算资源效率

        Returns:
            float: 资源效率分数 (0-1)
        """
        if not self.resource_metrics_history:
            return 1.0

        # 使用最近的资源指标
        recent_metrics = self.resource_metrics_history[-10:]  # 最近10次记录

        if not recent_metrics:
            return 1.0

        # 计算平均CPU和内存使用率
        avg_cpu = statistics.mean(m.cpu_percent for m in recent_metrics)
        avg_memory = statistics.mean(m.memory_percent for m in recent_metrics)

        # 资源效率 = 1 - (资源使用率 / 目标使用率)
        # 目标使用率: CPU 70%, Memory 80%
        cpu_efficiency = max(0, 1 - (avg_cpu / 70))
        memory_efficiency = max(0, 1 - (avg_memory / 80))

        # 综合资源效率
        resource_efficiency = (cpu_efficiency + memory_efficiency) / 2
        return min(1.0, max(0.0, resource_efficiency))

    def generate_performance_report(self, execution_id: Optional[str] = None) -> Dict[str, Any]:
        """生成性能报告

        Args:
            execution_id: 可选的执行ID，如果指定则生成特定执行的报告

        Returns:
            Dict: 性能报告
        """
        report = {
            "report_id": f"perf-report-{int(time.time())}",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "monitoring_status": "active" if self.monitoring_active else "inactive",
            "summary": {},
            "resource_metrics": {},
            "execution_metrics": {},
            "recommendations": [],
            "alerts": [alert.to_dict() for alert in self.active_alerts[-20:]]  # 最近20个告警
        }

        # 资源指标汇总
        if self.resource_metrics_history:
            recent_metrics = self.resource_metrics_history[-100:]  # 最近100次记录

            report["resource_metrics"] = {
                "current": recent_metrics[-1].to_dict() if recent_metrics else {},
                "average": {
                    "cpu_percent": statistics.mean(m.cpu_percent for m in recent_metrics),
                    "memory_usage_mb": statistics.mean(m.memory_usage_mb for m in recent_metrics),
                    "memory_percent": statistics.mean(m.memory_percent for m in recent_metrics),
                    "active_threads": statistics.mean(m.active_threads for m in recent_metrics)
                },
                "peak": {
                    "cpu_percent": max(m.cpu_percent for m in recent_metrics),
                    "memory_usage_mb": max(m.memory_usage_mb for m in recent_metrics),
                    "memory_percent": max(m.memory_percent for m in recent_metrics),
                    "active_threads": max(m.active_threads for m in recent_metrics)
                }
            }

        # 执行指标汇总
        if execution_id:
            # 特定执行的指标
            execution_metrics = [m for m in self.execution_metrics_history if m.execution_id == execution_id]
            if execution_metrics:
                latest_metrics = execution_metrics[-1]
                report["execution_metrics"] = latest_metrics.to_dict()
        else:
            # 所有执行的指标汇总
            if self.execution_metrics_history:
                report["execution_metrics"] = {
                    "total_executions": len(self.execution_metrics_history),
                    "average_parallel_efficiency": statistics.mean(m.parallel_efficiency for m in self.execution_metrics_history),
                    "average_throughput": statistics.mean(m.throughput_tasks_per_second for m in self.execution_metrics_history),
                    "total_tasks_processed": sum(m.task_count for m in self.execution_metrics_history),
                    "total_successful_tasks": sum(m.successful_tasks for m in self.execution_metrics_history),
                    "success_rate": sum(m.successful_tasks for m in self.execution_metrics_history) / sum(m.task_count for m in self.execution_metrics_history) if self.execution_metrics_history else 0
                }

        # 生成性能优化建议
        report["recommendations"] = self._generate_performance_recommendations()

        return report

    def _generate_performance_recommendations(self) -> List[str]:
        """生成性能优化建议

        Returns:
            List[str]: 优化建议列表
        """
        recommendations = []

        if not self.resource_metrics_history or not self.execution_metrics_history:
            return ["暂无足够数据生成建议"]

        recent_metrics = self.resource_metrics_history[-20:]
        recent_executions = self.execution_metrics_history[-10:]

        # CPU使用率建议
        avg_cpu = statistics.mean(m.cpu_percent for m in recent_metrics)
        if avg_cpu > 80:
            recommendations.append("CPU使用率较高，建议减少并发Agent数量或优化Agent算法")

        # 内存使用建议
        avg_memory = statistics.mean(m.memory_usage_mb for m in recent_metrics)
        if avg_memory > 1024:  # 1GB
            recommendations.append("内存使用量较大，建议启用更频繁的垃圾回收或减少Agent上下文大小")

        # 并行效率建议
        avg_efficiency = statistics.mean(m.parallel_efficiency for m in recent_executions)
        if avg_efficiency < 2.0:
            recommendations.append("并行效率较低，建议检查任务分配是否均衡或考虑增加并发数")

        # 吞吐量建议
        avg_throughput = statistics.mean(m.throughput_tasks_per_second for m in recent_executions)
        if avg_throughput < 0.5:
            recommendations.append("任务吞吐量较低，建议优化Agent响应时间或减少任务复杂度")

        # 告警相关建议
        if len(self.active_alerts) > 10:
            recommendations.append("活跃告警数量较多，建议优先处理高优先级告警")

        return recommendations if recommendations else ["系统性能表现良好，暂无特殊建议"]

    def get_current_performance_snapshot(self) -> Dict[str, Any]:
        """获取当前性能快照

        Returns:
            Dict: 性能快照数据
        """
        snapshot = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "monitoring_active": self.monitoring_active,
            "current_resource_metrics": {},
            "recent_performance_summary": {},
            "active_alerts_count": len(self.active_alerts),
            "metrics_history_counts": {
                "resource_metrics": len(self.resource_metrics_history),
                "execution_metrics": len(self.execution_metrics_history)
            }
        }

        # 当前资源指标
        if self.resource_metrics_history:
            snapshot["current_resource_metrics"] = self.resource_metrics_history[-1].to_dict()

        # 最近性能摘要
        if self.execution_metrics_history:
            recent = self.execution_metrics_history[-5:]
            snapshot["recent_performance_summary"] = {
                "average_efficiency": statistics.mean(m.parallel_efficiency for m in recent),
                "average_throughput": statistics.mean(m.throughput_tasks_per_second for m in recent),
                "total_recent_tasks": sum(m.task_count for m in recent),
                "recent_success_rate": sum(m.successful_tasks for m in recent) / sum(m.task_count for m in recent) if recent else 0
            }

        return snapshot

    def export_metrics_data(self, file_path: str) -> bool:
        """导出性能监控数据

        Args:
            file_path: 导出文件路径

        Returns:
            bool: 导出是否成功
        """
        try:
            data = {
                "export_timestamp": datetime.now(timezone.utc).isoformat(),
                "resource_metrics_history": [m.to_dict() for m in self.resource_metrics_history],
                "execution_metrics_history": [m.to_dict() for m in self.execution_metrics_history],
                "active_alerts": [alert.to_dict() for alert in self.active_alerts],
                "monitoring_config": self.config
            }

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            return True
        except Exception as e:
            print(f"导出性能数据失败: {e}")
            return False

    def clear_metrics_history(self, older_than_hours: int = 24) -> int:
        """清理历史指标数据

        Args:
            older_than_hours: 清理多少小时前的数据

        Returns:
            int: 清理的记录数量
        """
        cutoff_time = time.time() - (older_than_hours * 3600)

        # 清理资源指标历史
        original_resource_count = len(self.resource_metrics_history)
        self.resource_metrics_history = [
            m for m in self.resource_metrics_history
            if m.timestamp > cutoff_time
        ]
        cleaned_resource_count = original_resource_count - len(self.resource_metrics_history)

        # 清理执行指标历史
        original_execution_count = len(self.execution_metrics_history)
        self.execution_metrics_history = [
            m for m in self.execution_metrics_history
            if m.timestamp > cutoff_time
        ]
        cleaned_execution_count = original_execution_count - len(self.execution_metrics_history)

        # 清理过期告警
        original_alert_count = len(self.active_alerts)
        self.active_alerts = [
            alert for alert in self.active_alerts
            if alert.timestamp > cutoff_time
        ]
        cleaned_alert_count = original_alert_count - len(self.active_alerts)

        return cleaned_resource_count + cleaned_execution_count + cleaned_alert_count