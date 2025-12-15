"""
性能监控仪表板 - Canvas学习系统

本模块实现集成的性能监控仪表板，整合：
- 性能监控
- 动态实例管理
- 智能缓存
- 配置管理
- 基准测试

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-27
Story: 10.6 - Integration
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import threading

# 导入性能组件
from performance_monitor import PerformanceMonitor
from dynamic_instance_manager import DynamicInstanceManager
from intelligent_cache_manager import IntelligentCacheManager, CacheEntryType
from configuration_manager import ConfigurationManager, PerformanceConfig
from performance_benchmark_system import PerformanceBenchmarkSystem


@dataclass
class DashboardMetrics:
    """仪表板指标"""
    timestamp: datetime = field(default_factory=datetime.now)
    system_health: str = "good"  # good, warning, critical
    active_instances: int = 0
    queue_length: int = 0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    cache_hit_rate: float = 0.0
    cache_size_mb: float = 0.0
    requests_per_second: float = 0.0
    average_response_time: float = 0.0
    error_rate: float = 0.0
    efficiency_ratio: float = 1.0
    alerts_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "system_health": self.system_health,
            "active_instances": self.active_instances,
            "queue_length": self.queue_length,
            "cpu_usage": self.cpu_usage,
            "memory_usage": self.memory_usage,
            "cache_hit_rate": self.cache_hit_rate,
            "cache_size_mb": self.cache_size_mb,
            "requests_per_second": self.requests_per_second,
            "average_response_time": self.average_response_time,
            "error_rate": self.error_rate,
            "efficiency_ratio": self.efficiency_ratio,
            "alerts_count": self.alerts_count
        }


@dataclass
class DashboardAlert:
    """仪表板告警"""
    alert_id: str
    severity: str  # info, warning, critical
    category: str  # performance, resource, cache, system
    title: str
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    acknowledged: bool = False
    auto_resolved: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "alert_id": self.alert_id,
            "severity": self.severity,
            "category": self.category,
            "title": self.title,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "acknowledged": self.acknowledged,
            "auto_resolved": self.auto_resolved
        }


class PerformanceDashboard:
    """性能监控仪表板

    集成所有性能监控组件，提供统一的性能视图和控制接口。
    """

    def __init__(self, config_file: str = "config/performance_config.yaml"):
        """初始化性能仪表板

        Args:
            config_file: 配置文件路径
        """
        self.config_file = Path(config_file)
        self.config_dir = self.config_file.parent

        # 初始化配置管理器
        self.config_manager = ConfigurationManager(str(self.config_dir))
        self.current_config: PerformanceConfig

        # 性能组件
        self.performance_monitor: Optional[PerformanceMonitor] = None
        self.instance_manager: Optional[DynamicInstanceManager] = None
        self.cache_manager: Optional[IntelligentCacheManager] = None
        self.benchmark_system: Optional[PerformanceBenchmarkSystem] = None

        # 模拟实例池（用于测试）
        self.mock_instance_pool = None

        # 仪表板状态
        self.is_running = False
        self.metrics_history: List[DashboardMetrics] = []
        self.active_alerts: List[DashboardAlert] = []
        self.alert_history: List[DashboardAlert] = []

        # 监控任务
        self.dashboard_task: Optional[asyncio.Task] = None
        self.metrics_update_interval = 5  # 秒

        # 告警阈值
        self.alert_thresholds = {
            "cpu_warning": 70,
            "cpu_critical": 90,
            "memory_warning": 75,
            "memory_critical": 90,
            "response_time_warning": 3000,  # ms
            "response_time_critical": 5000,  # ms
            "error_rate_warning": 0.05,  # 5%
            "error_rate_critical": 0.10,  # 10%
            "cache_hit_rate_warning": 0.40,  # 40%
            "efficiency_warning": 2.0,
            "efficiency_critical": 1.5
        }

    async def start(self) -> bool:
        """启动性能仪表板

        Returns:
            bool: 是否成功启动
        """
        try:
            print("Starting Performance Dashboard...")

            # 1. 加载配置
            await self._load_configuration()

            # 2. 初始化性能组件
            await self._initialize_components()

            # 3. 启动所有组件
            await self._start_components()

            # 4. 启动仪表板监控
            self.is_running = True
            self.dashboard_task = asyncio.create_task(self._dashboard_loop())

            print("✓ Performance Dashboard started successfully")
            return True

        except Exception as e:
            print(f"✗ Failed to start Performance Dashboard: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def stop(self) -> None:
        """停止性能仪表板"""
        print("Stopping Performance Dashboard...")

        self.is_running = False

        # 停止仪表板任务
        if self.dashboard_task:
            self.dashboard_task.cancel()
            try:
                await self.dashboard_task
            except asyncio.CancelledError:
                pass

        # 停止所有组件
        await self._stop_components()

        print("✓ Performance Dashboard stopped")

    async def _load_configuration(self) -> None:
        """加载配置"""
        # 获取当前有效配置
        self.current_config = await self.config_manager.get_current_config()

        # 创建配置目录（如果不存在）
        self.config_dir.mkdir(parents=True, exist_ok=True)

    async def _initialize_components(self) -> None:
        """初始化性能组件"""
        config_dict = self.current_config.to_dict()

        # 1. 初始化性能监控器
        self.performance_monitor = PerformanceMonitor({
            "enabled": self.current_config.monitoring_enabled,
            "collect_metrics": True,
            "log_performance_data": self.current_config.log_performance_metrics,
            "slow_execution_threshold_seconds": self.current_config.slow_execution_threshold_seconds,
            "memory_usage_alert_threshold_mb": self.current_config.memory_usage_alert_threshold_mb,
            "cpu_usage_alert_threshold_percent": self.current_config.cpu_usage_alert_threshold_percent,
            "metrics_collection_interval_seconds": self.current_config.metrics_collection_interval_seconds
        })

        # 2. 初始化缓存管理器
        self.cache_manager = IntelligentCacheManager({
            "max_cache_size_mb": self.current_config.cache_max_size_mb,
            "max_entries": self.current_config.cache_max_entries,
            "default_ttl_seconds": self.current_config.cache_ttl_seconds,
            "enable_compression": self.current_config.cache_compression_enabled,
            "similarity_threshold": self.current_config.cache_similarity_threshold,
            "eviction_policy": self.current_config.cache_eviction_policy,
            "cleanup_interval_seconds": 60
        })

        # 3. 创建模拟实例池（用于演示）
        self.mock_instance_pool = MockInstancePool(self.current_config.max_concurrent_instances)

        # 4. 初始化动态实例管理器
        self.instance_manager = DynamicInstanceManager(
            instance_pool=self.mock_instance_pool,
            performance_monitor=self.performance_monitor,
            config={
                "min_instances": self.current_config.min_instances,
                "max_instances": self.current_config.max_concurrent_instances,
                "scale_up_threshold": self.current_config.scaling_threshold_cpu / 100,
                "scale_down_threshold": 0.3,
                "adjustment_cooldown_seconds": self.current_config.adjustment_cooldown_seconds,
                "adjustment_strategy": self.current_config.adjustment_strategy,
                "auto_adjustment_enabled": self.current_config.auto_scaling_enabled
            }
        )

        # 5. 初始化基准测试系统
        self.benchmark_system = PerformanceBenchmarkSystem(
            performance_monitor=self.performance_monitor,
            cache_manager=self.cache_manager,
            config_manager=self.config_manager
        )

    async def _start_components(self) -> None:
        """启动所有组件"""
        # 启动性能监控器
        if self.current_config.monitoring_enabled:
            await self.performance_monitor.start_monitoring()

        # 启动缓存管理器
        if self.current_config.cache_enabled:
            await self.cache_manager.start_monitoring()

        # 启动动态实例管理器
        if self.current_config.auto_scaling_enabled:
            await self.instance_manager.start_monitoring()

    async def _stop_components(self) -> None:
        """停止所有组件"""
        # 停止性能监控器
        if self.performance_monitor:
            await self.performance_monitor.stop_monitoring()

        # 停止缓存管理器
        if self.cache_manager:
            await self.cache_manager.stop_monitoring()

        # 停止动态实例管理器
        if self.instance_manager:
            await self.instance_manager.stop_monitoring()

    async def _dashboard_loop(self) -> None:
        """仪表板主循环"""
        print("Dashboard monitoring loop started")

        while self.is_running:
            try:
                # 收集指标
                metrics = await self._collect_metrics()

                # 更新历史记录
                self.metrics_history.append(metrics)
                if len(self.metrics_history) > 1000:  # 保留最近1000条记录
                    self.metrics_history = self.metrics_history[-1000:]

                # 检查告警
                await self._check_alerts(metrics)

                # 输出仪表板状态
                if len(self.metrics_history) % 12 == 0:  # 每分钟输出一次
                    self._print_dashboard_status(metrics)

                await asyncio.sleep(self.metrics_update_interval)

            except Exception as e:
                print(f"Dashboard loop error: {e}")
                await asyncio.sleep(5)

    async def _collect_metrics(self) -> DashboardMetrics:
        """收集性能指标"""
        metrics = DashboardMetrics()

        # 系统资源指标
        if self.performance_monitor and self.performance_monitor.resource_metrics_history:
            latest_resource = self.performance_monitor.resource_metrics_history[-1]
            metrics.cpu_usage = latest_resource.cpu_percent
            metrics.memory_usage = latest_resource.memory_percent

        # 实例指标
        if self.mock_instance_pool:
            metrics.active_instances = self.mock_instance_pool.get_active_instance_count()
            metrics.queue_length = self.mock_instance_pool.get_queue_length()

        # 缓存指标
        if self.cache_manager:
            cache_stats = await self.cache_manager.get_cache_statistics()
            metrics.cache_hit_rate = cache_stats.hit_rate
            metrics.cache_size_mb = cache_stats.total_size_mb

        # 性能指标
        if self.performance_monitor and self.performance_monitor.execution_metrics_history:
            recent_executions = self.performance_monitor.execution_metrics_history[-5:]
            if recent_executions:
                metrics.average_response_time = statistics.mean(
                    m.average_task_time_ms for m in recent_executions
                )
                metrics.requests_per_second = statistics.mean(
                    m.throughput_tasks_per_second for m in recent_executions
                )

                # 计算错误率
                total_tasks = sum(m.task_count for m in recent_executions)
                failed_tasks = sum(m.failed_tasks for m in recent_executions)
                metrics.error_rate = failed_tasks / total_tasks if total_tasks > 0 else 0

                # 计算效率比
                metrics.efficiency_ratio = statistics.mean(
                    m.parallel_efficiency for m in recent_executions
                )

        # 告警计数
        metrics.alerts_count = len([a for a in self.active_alerts if not a.acknowledged])

        # 评估系统健康状态
        metrics.system_health = self._evaluate_system_health(metrics)

        return metrics

    def _evaluate_system_health(self, metrics: DashboardMetrics) -> str:
        """评估系统健康状态"""
        # 检查关键指标
        critical_issues = 0
        warning_issues = 0

        if metrics.cpu_usage > self.alert_thresholds["cpu_critical"]:
            critical_issues += 1
        elif metrics.cpu_usage > self.alert_thresholds["cpu_warning"]:
            warning_issues += 1

        if metrics.memory_usage > self.alert_thresholds["memory_critical"]:
            critical_issues += 1
        elif metrics.memory_usage > self.alert_thresholds["memory_warning"]:
            warning_issues += 1

        if metrics.error_rate > self.alert_thresholds["error_rate_critical"]:
            critical_issues += 1
        elif metrics.error_rate > self.alert_thresholds["error_rate_warning"]:
            warning_issues += 1

        if metrics.average_response_time > self.alert_thresholds["response_time_critical"]:
            critical_issues += 1
        elif metrics.average_response_time > self.alert_thresholds["response_time_warning"]:
            warning_issues += 1

        if metrics.efficiency_ratio < self.alert_thresholds["efficiency_critical"]:
            critical_issues += 1
        elif metrics.efficiency_ratio < self.alert_thresholds["efficiency_warning"]:
            warning_issues += 1

        # 确定健康状态
        if critical_issues > 0:
            return "critical"
        elif warning_issues > 2:
            return "warning"
        else:
            return "good"

    async def _check_alerts(self, metrics: DashboardMetrics) -> None:
        """检查并生成告警"""
        new_alerts = []

        # CPU告警
        if metrics.cpu_usage > self.alert_thresholds["cpu_critical"]:
            new_alerts.append(DashboardAlert(
                alert_id=f"cpu-critical-{int(time.time())}",
                severity="critical",
                category="resource",
                title="CPU使用率过高",
                message=f"CPU使用率达到{metrics.cpu_usage:.1f}%，超过{self.alert_thresholds['cpu_critical']}%阈值"
            ))
        elif metrics.cpu_usage > self.alert_thresholds["cpu_warning"]:
            new_alerts.append(DashboardAlert(
                alert_id=f"cpu-warning-{int(time.time())}",
                severity="warning",
                category="resource",
                title="CPU使用率偏高",
                message=f"CPU使用率达到{metrics.cpu_usage:.1f}%，超过{self.alert_thresholds['cpu_warning']}%阈值"
            ))

        # 内存告警
        if metrics.memory_usage > self.alert_thresholds["memory_critical"]:
            new_alerts.append(DashboardAlert(
                alert_id=f"memory-critical-{int(time.time())}",
                severity="critical",
                category="resource",
                title="内存使用率过高",
                message=f"内存使用率达到{metrics.memory_usage:.1f}%，超过{self.alert_thresholds['memory_critical']}%阈值"
            ))

        # 响应时间告警
        if metrics.average_response_time > self.alert_thresholds["response_time_critical"]:
            new_alerts.append(DashboardAlert(
                alert_id=f"response-critical-{int(time.time())}",
                severity="critical",
                category="performance",
                title="响应时间过长",
                message=f"平均响应时间达到{metrics.average_response_time:.0f}ms，超过{self.alert_thresholds['response_time_critical']}ms阈值"
            ))

        # 效率比告警
        if metrics.efficiency_ratio < self.alert_thresholds["efficiency_critical"]:
            new_alerts.append(DashboardAlert(
                alert_id=f"efficiency-critical-{int(time.time())}",
                severity="critical",
                category="performance",
                title="并行效率过低",
                message=f"并行效率仅为{metrics.efficiency_ratio:.1f}x，低于{self.alert_thresholds['efficiency_critical']}x阈值"
            ))

        # 更新告警列表
        for alert in new_alerts:
            # 检查是否已存在相似告警
            existing = self._find_similar_alert(alert)
            if not existing:
                self.active_alerts.append(alert)
                self.alert_history.append(alert)
                print(f"🚨 ALERT: {alert.title} - {alert.message}")

    def _find_similar_alert(self, new_alert: DashboardAlert) -> Optional[DashboardAlert]:
        """查找相似的活跃告警"""
        for alert in self.active_alerts:
            if (alert.category == new_alert.category and
                alert.title == new_alert.title and
                not alert.acknowledged):
                return alert
        return None

    def _print_dashboard_status(self, metrics: DashboardMetrics) -> None:
        """打印仪表板状态"""
        # 清屏
        os.system('cls' if os.name == 'nt' else 'clear')

        # 打印状态
        print("=" * 80)
        print("🎯 Canvas Learning System - Performance Dashboard")
        print("=" * 80)
        print(f"📅 Time: {metrics.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🏥 System Health: {metrics.system_health.upper()}")
        print("-" * 80)

        # 资源使用
        print(f"\n📊 Resource Usage:")
        print(f"  CPU: {metrics.cpu_usage:.1f}% {'▓' * int(metrics.cpu_usage/5)}{'░' * (20-int(metrics.cpu_usage/5))}")
        print(f"  Memory: {metrics.memory_usage:.1f}% {'▓' * int(metrics.memory_usage/5)}{'░' * (20-int(metrics.memory_usage/5))}")

        # 实例状态
        print(f"\n🔄 Instance Status:")
        print(f"  Active Instances: {metrics.active_instances}/{self.current_config.max_concurrent_instances}")
        print(f"  Queue Length: {metrics.queue_length}")
        print(f"  Efficiency Ratio: {metrics.efficiency_ratio:.1f}x {'✓' if metrics.efficiency_ratio >= 3 else '✗'}")

        # 缓存状态
        print(f"\n💾 Cache Status:")
        print(f"  Hit Rate: {metrics.cache_hit_rate:.1%} {'✓' if metrics.cache_hit_rate > 0.6 else '✗'}")
        print(f"  Size: {metrics.cache_size_mb:.1f} MB")

        # 性能指标
        print(f"\n⚡ Performance:")
        print(f"  Requests/sec: {metrics.requests_per_second:.1f}")
        print(f"  Avg Response: {metrics.average_response_time:.0f}ms {'✓' if metrics.average_response_time < 2000 else '✗'}")
        print(f"  Error Rate: {metrics.error_rate:.1%}")

        # 活跃告警
        if metrics.alerts_count > 0:
            print(f"\n🚨 Active Alerts ({metrics.alerts_count}):")
            for alert in self.active_alerts[-5:]:  # 显示最近5个
                if not alert.acknowledged:
                    print(f"  • {alert.title}: {alert.message}")

        print("\n" + "=" * 80)
        print("Commands: 'run_benchmark', 'config', 'alerts', 'help', 'quit'")
        print("=" * 80)

    async def run_benchmark(self) -> Dict[str, Any]:
        """运行性能基准测试"""
        if not self.benchmark_system:
            return {"error": "Benchmark system not initialized"}

        print("\n🏁 Running performance benchmark...")
        try:
            report = await self.benchmark_system.run_comprehensive_benchmark()
            return {
                "success": True,
                "report_id": report.report_id,
                "summary": report.summary,
                "recommendations": report.recommendations
            }
        except Exception as e:
            return {"error": str(e)}

    async def update_configuration(self, changes: Dict[str, Any]) -> bool:
        """更新配置"""
        try:
            success = await self.config_manager.apply_config_changes(changes)
            if success:
                # 重新加载配置
                await self._load_configuration()
                # 重启组件以应用新配置
                await self._restart_components()
                print("✓ Configuration updated successfully")
            return success
        except Exception as e:
            print(f"✗ Failed to update configuration: {e}")
            return False

    async def _restart_components(self) -> None:
        """重启组件以应用新配置"""
        await self._stop_components()
        await self._initialize_components()
        await self._start_components()

    async def acknowledge_alert(self, alert_id: str) -> bool:
        """确认告警"""
        for alert in self.active_alerts:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                return True
        return False

    def get_metrics_summary(self, hours: int = 1) -> Dict[str, Any]:
        """获取指标摘要"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_metrics = [
            m for m in self.metrics_history
            if m.timestamp >= cutoff_time
        ]

        if not recent_metrics:
            return {"error": "No metrics available"}

        # 计算统计信息
        import statistics
        avg_cpu = statistics.mean(m.cpu_usage for m in recent_metrics)
        avg_memory = statistics.mean(m.memory_usage for m in recent_metrics)
        avg_response = statistics.mean(m.average_response_time for m in recent_metrics)
        avg_efficiency = statistics.mean(m.efficiency_ratio for m in recent_metrics)

        return {
            "time_range_hours": hours,
            "sample_count": len(recent_metrics),
            "averages": {
                "cpu_usage": avg_cpu,
                "memory_usage": avg_memory,
                "response_time_ms": avg_response,
                "efficiency_ratio": avg_efficiency
            },
            "peaks": {
                "cpu_usage": max(m.cpu_usage for m in recent_metrics),
                "memory_usage": max(m.memory_usage for m in recent_metrics),
                "response_time_ms": max(m.average_response_time for m in recent_metrics)
            },
            "system_health": recent_metrics[-1].system_health if recent_metrics else "unknown"
        }

    def get_active_alerts(self) -> List[DashboardAlert]:
        """获取活跃告警"""
        return [a for a in self.active_alerts if not a.acknowledged]

    async def export_dashboard_data(self, file_path: str) -> bool:
        """导出仪表板数据"""
        try:
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "current_config": self.current_config.to_dict(),
                "metrics_history": [m.to_dict() for m in self.metrics_history[-100:]],
                "active_alerts": [a.to_dict() for a in self.get_active_alerts()],
                "alert_history": [a.to_dict() for a in self.alert_history[-50:]]
            }

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

            return True
        except Exception as e:
            print(f"Failed to export dashboard data: {e}")
            return False


class MockInstancePool:
    """模拟实例池（用于演示）"""

    def __init__(self, max_instances: int = 6):
        self.max_instances = max_instances
        self.active_instances = max_instances // 2
        self.queue_length = 0
        self.last_update = time.time()

    def get_active_instance_count(self) -> int:
        """获取活跃实例数"""
        # 模拟动态变化
        if time.time() - self.last_update > 10:
            import random
            self.active_instances = max(1, min(self.max_instances,
                self.active_instances + random.randint(-2, 2)))
            self.last_update = time.time()
        return self.active_instances

    def get_queue_length(self) -> int:
        """获取队列长度"""
        import random
        if random.random() < 0.1:  # 10%概率变化
            self.queue_length = max(0, self.queue_length + random.randint(-3, 3))
        return self.queue_length

    async def set_max_concurrent_instances(self, max_instances: int) -> None:
        """设置最大并发实例数"""
        self.max_instances = max_instances
        print(f"[Mock] Max concurrent instances set to: {max_instances}")


# 主程序入口
async def main():
    """主程序"""
    import os

    dashboard = PerformanceDashboard()

    # 启动仪表板
    if await dashboard.start():
        print("\nDashboard is running. Press Ctrl+C to stop.")

        try:
            # 简单的交互界面
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down...")
            await dashboard.stop()
    else:
        print("Failed to start dashboard")


if __name__ == "__main__":
    asyncio.run(main())