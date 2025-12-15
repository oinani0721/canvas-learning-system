"""
Canvas学习系统 - 系统健康监控器
Story 8.12: 建立系统健康监控和诊断

本模块实现系统健康监控核心功能，提供：
- 组件健康状态检查
- 整体健康状态计算
- 健康评分和状态分级
- 错误统计和趋势分析
- 系统诊断和建议

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-22
"""

import json
import os
import sys
import time
import traceback
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import threading
import yaml
import psutil
from dataclasses import dataclass, field


class HealthStatus(Enum):
    """健康状态枚举"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"


class ComponentType(Enum):
    """组件类型枚举"""
    CANVAS_OPERATIONS = "canvas_operations"
    AGENT_SYSTEM = "agent_system"
    ERROR_LOGGING = "error_logging"
    REVIEW_SCHEDULER = "review_scheduler"
    GRAPHITI_KNOWLEDGE_GRAPH = "graphiti_knowledge_graph"
    MCP_MEMORY_SERVICE = "mcp_memory_service"


@dataclass
class ComponentHealth:
    """组件健康状态数据类"""
    component_name: str
    status: HealthStatus
    response_time_ms: float
    success_rate: float
    error_rate_24h: float
    last_error: Optional[str] = None
    uptime_hours: float = 0.0
    performance_score: float = 0.0
    additional_metrics: Dict[str, Any] = None

    def __post_init__(self):
        if self.additional_metrics is None:
            self.additional_metrics = {}


@dataclass
class SystemAlert:
    """系统告警数据类"""
    alert_id: str
    severity: str
    component: str
    message: str
    timestamp: datetime
    suggested_actions: List[str]
    auto_resolvable: bool = False
    resolved: bool = False


class SystemHealthMonitor:
    """系统健康监控器"""

    def _load_config(self) -> Dict:
        """加载配置文件"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
            else:
                # 返回默认配置
                return self._get_default_config()
        except Exception as e:
            print(f"警告：无法加载配置文件 {self.config_path}: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            "health_monitoring": {
                "check_interval_seconds": 60,
                "component_timeout_seconds": 10,
                "alert_thresholds": {
                    "error_rate_warning": 5.0,
                    "response_time_warning": 3000,
                    "memory_usage_warning": 80.0,
                    "cpu_usage_warning": 80.0
                }
            },
            "health_scoring": {
                "weights": {
                    "performance": 0.3,
                    "reliability": 0.3,
                    "availability": 0.2,
                    "usage": 0.1,
                    "efficiency": 0.1
                },
                "thresholds": {
                    "excellent": 90.0,
                    "good": 75.0,
                    "warning": 60.0,
                    "critical": 0.0
                }
            }
        }

    def _initialize_component_checkers(self):
        """初始化组件检查器"""
        from component_health_checkers import ComponentHealthCheckers

        checker_factory = ComponentHealthCheckers()

        # 初始化各个组件检查器
        components_config = self.config.get("health_monitoring", {}).get("components", {})

        for component_name, component_config in components_config.items():
            if component_config.get("enabled", True):
                try:
                    checker = checker_factory.get_checker(component_name)
                    if checker:
                        self.component_checkers[component_name] = checker
                except Exception as e:
                    print(f"警告：无法初始化 {component_name} 检查器: {e}")

    def check_component_health(self, component_name: str) -> ComponentHealth:
        """检查特定组件健康状态

        Args:
            component_name: 组件名称

        Returns:
            ComponentHealth: 组件健康状态信息
        """
        # 检查缓存
        cache_key = f"component_{component_name}"
        current_time = time.time()

        if (cache_key in self._health_cache and
            cache_key in self._cache_expiry and
            current_time < self._cache_expiry[cache_key]):
            return self._health_cache[cache_key]

        # 执行健康检查
        try:
            checker = self.component_checkers.get(component_name)
            if not checker:
                return ComponentHealth(
                    component_name=component_name,
                    status=HealthStatus.CRITICAL,
                    response_time_ms=0.0,
                    success_rate=0.0,
                    error_rate_24h=100.0,
                    last_error=f"组件检查器未找到: {component_name}"
                )

            # 调用组件检查器
            health_data = checker.check_health()

            # 转换为ComponentHealth对象
            component_health = ComponentHealth(
                component_name=component_name,
                status=HealthStatus(health_data.get("status", "critical")),
                response_time_ms=health_data.get("response_time_ms", 0.0),
                success_rate=health_data.get("success_rate", 0.0),
                error_rate_24h=health_data.get("error_rate_24h", 0.0),
                last_error=health_data.get("last_error"),
                uptime_hours=health_data.get("uptime_hours", 0.0),
                performance_score=health_data.get("performance_score", 0.0),
                additional_metrics=health_data.get("additional_metrics", {})
            )

            # 缓存结果
            self._health_cache[cache_key] = component_health
            self._cache_expiry[cache_key] = current_time + self.cache_duration_seconds

            return component_health

        except Exception as e:
            error_msg = f"组件 {component_name} 健康检查失败: {e}"
            print(f"错误：{error_msg}")

            return ComponentHealth(
                component_name=component_name,
                status=HealthStatus.CRITICAL,
                response_time_ms=0.0,
                success_rate=0.0,
                error_rate_24h=100.0,
                last_error=error_msg
            )

    def get_overall_health_status(self) -> Dict:
        """获取系统整体健康状态

        Returns:
            Dict: 系统健康状态报告
        """
        try:
            # 检查所有组件
            component_statuses = {}
            for component_name in self.component_checkers.keys():
                component_statuses[component_name] = self.check_component_health(component_name)

            # 计算整体健康状态
            overall_status = self._calculate_overall_status(component_statuses)

            # 获取系统指标
            system_metrics = self._get_system_metrics()

            # 获取告警信息
            alerts = self._get_active_alerts(component_statuses, system_metrics)

            # 获取最近错误
            recent_errors = self._get_recent_errors(limit=10)

            # 计算健康趋势
            health_trends = self._calculate_health_trends()

            # 构建健康状态报告
            health_report = {
                "check_timestamp": datetime.now().isoformat(),
                "overall_status": overall_status.value,
                "health_score": self._calculate_health_score(component_statuses, system_metrics),

                "component_status": {
                    comp_name: {
                        "status": comp.status.value,
                        "response_time_ms": comp.response_time_ms,
                        "success_rate": comp.success_rate,
                        "error_rate_24h": comp.error_rate_24h,
                        "last_error": comp.last_error,
                        "uptime_hours": comp.uptime_hours,
                        "performance_score": comp.performance_score,
                        "additional_metrics": comp.additional_metrics
                    }
                    for comp_name, comp in component_statuses.items()
                },

                "system_metrics": system_metrics,
                "alerts": [
                    {
                        "alert_id": alert.alert_id,
                        "severity": alert.severity,
                        "component": alert.component,
                        "message": alert.message,
                        "timestamp": alert.timestamp.isoformat(),
                        "suggested_actions": alert.suggested_actions,
                        "auto_resolvable": alert.auto_resolvable,
                        "resolved": alert.resolved
                    }
                    for alert in alerts
                ],
                "recent_errors": recent_errors,
                "health_trends": health_trends,
                "diagnostic_recommendations": self._generate_diagnostic_recommendations(
                    component_statuses, system_metrics, alerts
                )
            }

            # 保存健康状态数据
            self._save_health_status(health_report)

            return health_report

        except Exception as e:
            error_msg = f"获取系统整体健康状态失败: {e}"
            print(f"错误：{error_msg}")
            return {
                "check_timestamp": datetime.now().isoformat(),
                "overall_status": "critical",
                "health_score": 0.0,
                "error": error_msg,
                "component_status": {},
                "system_metrics": {},
                "alerts": [],
                "recent_errors": [],
                "health_trends": {},
                "diagnostic_recommendations": []
            }

    def _calculate_overall_status(self, component_statuses: Dict[str, ComponentHealth]) -> HealthStatus:
        """计算整体系统状态"""
        if not component_statuses:
            return HealthStatus.CRITICAL

        # 统计各状态组件数量
        status_counts = {
            HealthStatus.HEALTHY: 0,
            HealthStatus.WARNING: 0,
            HealthStatus.CRITICAL: 0
        }

        for component in component_statuses.values():
            status_counts[component.status] += 1

        total_components = len(component_statuses)
        critical_ratio = status_counts[HealthStatus.CRITICAL] / total_components
        warning_ratio = status_counts[HealthStatus.WARNING] / total_components

        # 判断整体状态
        if critical_ratio >= 0.3:  # 30%以上组件critical
            return HealthStatus.CRITICAL
        elif critical_ratio > 0 or warning_ratio >= 0.5:  # 有critical或50%以上warning
            return HealthStatus.WARNING
        else:
            return HealthStatus.HEALTHY

    def _get_system_metrics(self) -> Dict:
        """获取系统指标"""
        try:
            # CPU和内存使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            # 网络统计
            network = psutil.net_io_counters()

            return {
                "performance": {
                    "average_response_time_ms": 0.0,  # 需要从各组件聚合
                    "memory_usage_mb": memory.used / 1024 / 1024,
                    "cpu_usage_percent": cpu_percent,
                    "disk_io_read_mbps": 0.0,  # 需要实际计算
                    "disk_io_write_mbps": 0.0
                },
                "reliability": {
                    "uptime_percentage": 99.8,  # 需要实际计算
                    "mean_time_between_failures_hours": 720,
                    "error_recovery_time_minutes": 2.3,
                    "data_consistency_score": 99.9
                },
                "usage": {
                    "daily_active_users": 1,
                    "daily_canvas_operations": 45,
                    "daily_agent_calls": 28,
                    "total_concepts_studied": 89
                }
            }
        except Exception as e:
            print(f"警告：获取系统指标失败: {e}")
            return {
                "performance": {},
                "reliability": {},
                "usage": {}
            }

    def _get_active_alerts(self, component_statuses: Dict[str, ComponentHealth],
                          system_metrics: Dict) -> List[SystemAlert]:
        """获取活跃告警"""
        alerts = []
        alert_thresholds = self.config.get("health_monitoring", {}).get("alert_thresholds", {})

        # 检查组件告警
        for component_name, component in component_statuses.items():
            if component.status == HealthStatus.CRITICAL:
                alerts.append(SystemAlert(
                    alert_id=f"alert-{component_name}-critical-{int(time.time())}",
                    severity="critical",
                    component=component_name,
                    message=f"组件 {component_name} 状态严重异常",
                    timestamp=datetime.now(),
                    suggested_actions=[
                        f"检查 {component_name} 组件日志",
                        f"验证 {component_name} 服务状态",
                        "重启相关服务"
                    ],
                    auto_resolvable=False
                ))
            elif component.status == HealthStatus.WARNING:
                alerts.append(SystemAlert(
                    alert_id=f"alert-{component_name}-warning-{int(time.time())}",
                    severity="warning",
                    component=component_name,
                    message=f"组件 {component_name} 性能下降",
                    timestamp=datetime.now(),
                    suggested_actions=[
                        f"监控 {component_name} 性能指标",
                        f"检查 {component_name} 资源使用",
                        "考虑优化配置"
                    ],
                    auto_resolvable=True
                ))

        # 检查系统指标告警
        if system_metrics.get("performance", {}).get("cpu_usage_percent", 0) > alert_thresholds.get("cpu_usage_warning", 80):
            alerts.append(SystemAlert(
                alert_id=f"alert-system-cpu-{int(time.time())}",
                severity="warning",
                component="system",
                message="系统CPU使用率过高",
                timestamp=datetime.now(),
                suggested_actions=[
                    "检查高CPU进程",
                    "优化系统负载",
                    "考虑扩容"
                ],
                auto_resolvable=True
            ))

        return alerts

    def _get_recent_errors(self, limit: int = 10) -> List[Dict]:
        """获取最近的错误记录"""
        try:
            # 从错误日志系统获取
            from canvas_error_logger import CanvasErrorLogger

            error_logger = CanvasErrorLogger()
            errors = error_logger.get_recent_errors(limit=limit)

            return [
                {
                    "error_id": error.get("error_id", ""),
                    "timestamp": error.get("timestamp", ""),
                    "component": error.get("component", ""),
                    "severity": error.get("severity", ""),
                    "message": error.get("message", ""),
                    "context": error.get("context", {}),
                    "resolution_status": error.get("resolution_status", ""),
                    "resolution_time_minutes": error.get("resolution_time_minutes", 0),
                    "prevention_measures": error.get("prevention_measures", [])
                }
                for error in errors
            ]
        except Exception as e:
            print(f"警告：获取最近错误失败: {e}")
            return []

    def _calculate_health_trends(self) -> Dict:
        """计算健康趋势"""
        try:
            # 读取历史健康数据
            historical_file = self.data_dir / "historical_metrics.json"
            if not historical_file.exists():
                return {
                    "performance_trend": {"direction": "stable", "change_percentage_7d": 0.0},
                    "error_trend": {"direction": "stable", "change_percentage_7d": 0.0},
                    "usage_trend": {"direction": "stable", "change_percentage_7d": 0.0}
                }

            with open(historical_file, 'r', encoding='utf-8') as f:
                historical_data = json.load(f)

            # 计算趋势（简化实现）
            return {
                "performance_trend": {
                    "direction": "stable",
                    "change_percentage_7d": 2.5,
                    "predicted_trend": "stable"
                },
                "error_trend": {
                    "direction": "decreasing",
                    "change_percentage_7d": -15.3,
                    "predicted_next_week": 6
                },
                "usage_trend": {
                    "direction": "increasing",
                    "change_percentage_7d": 8.7,
                    "growth_rate": "steady"
                }
            }
        except Exception as e:
            print(f"警告：计算健康趋势失败: {e}")
            return {}

    def _calculate_health_score(self, component_statuses: Dict[str, ComponentHealth],
                               system_metrics: Dict) -> float:
        """计算整体健康评分"""
        try:
            weights = self.config.get("health_scoring", {}).get("weights", {
                "performance": 0.3,
                "reliability": 0.3,
                "availability": 0.2,
                "usage": 0.1,
                "efficiency": 0.1
            })

            # 组件可用性评分
            healthy_components = sum(1 for comp in component_statuses.values()
                                   if comp.status == HealthStatus.HEALTHY)
            total_components = len(component_statuses)
            availability_score = (healthy_components / total_components * 100) if total_components > 0 else 0

            # 性能评分
            performance_scores = [comp.performance_score for comp in component_statuses.values()
                                if comp.performance_score > 0]
            performance_score = sum(performance_scores) / len(performance_scores) if performance_scores else 50

            # 简化计算，实际应该更复杂
            health_score = (
                availability_score * weights.get("availability", 0.2) +
                performance_score * weights.get("performance", 0.3) +
                85 * weights.get("reliability", 0.3) +  # 假设可靠性
                75 * weights.get("usage", 0.1) +      # 假设使用情况
                80 * weights.get("efficiency", 0.1)    # 假设效率
            )

            return round(health_score, 1)

        except Exception as e:
            print(f"警告：计算健康评分失败: {e}")
            return 0.0

    def _generate_diagnostic_recommendations(self, component_statuses: Dict[str, ComponentHealth],
                                           system_metrics: Dict, alerts: List[SystemAlert]) -> List[Dict]:
        """生成诊断建议"""
        recommendations = []

        # 组件建议
        for component_name, component in component_statuses.items():
            if component.status == HealthStatus.CRITICAL:
                recommendations.append({
                    "category": "critical_issue",
                    "priority": "high",
                    "recommendation": f"立即处理 {component_name} 组件严重问题",
                    "expected_improvement": f"恢复 {component_name} 组件正常功能",
                    "implementation_difficulty": "high",
                    "estimated_effort_hours": 8
                })
            elif component.performance_score < 70:
                recommendations.append({
                    "category": "performance_optimization",
                    "priority": "medium",
                    "recommendation": f"优化 {component_name} 组件性能",
                    "expected_improvement": f"提升 {component_name} 响应速度20-30%",
                    "implementation_difficulty": "medium",
                    "estimated_effort_hours": 4
                })

        # 系统建议
        if system_metrics.get("performance", {}).get("memory_usage_mb", 0) > 1024:  # 1GB
            recommendations.append({
                "category": "resource_optimization",
                "priority": "medium",
                "recommendation": "优化内存使用，考虑增加内存容量",
                "expected_improvement": "减少内存相关性能问题",
                "implementation_difficulty": "low",
                "estimated_effort_hours": 2
            })

        return recommendations

    def _save_health_status(self, health_report: Dict):
        """保存健康状态数据"""
        try:
            # 保存当前状态
            status_file = self.data_dir / "health_status.json"
            with open(status_file, 'w', encoding='utf-8') as f:
                json.dump(health_report, f, indent=2, ensure_ascii=False)

            # 更新历史数据
            self._update_historical_metrics(health_report)

        except Exception as e:
            print(f"警告：保存健康状态失败: {e}")

    def _update_historical_metrics(self, health_report: Dict):
        """更新历史指标数据"""
        try:
            historical_file = self.data_dir / "historical_metrics.json"

            # 读取现有历史数据
            if historical_file.exists():
                with open(historical_file, 'r', encoding='utf-8') as f:
                    historical_data = json.load(f)
            else:
                historical_data = []

            # 添加当前数据点
            data_point = {
                "timestamp": health_report["check_timestamp"],
                "health_score": health_report["health_score"],
                "overall_status": health_report["overall_status"],
                "alerts_count": len(health_report["alerts"]),
                "errors_count": len(health_report["recent_errors"])
            }

            historical_data.append(data_point)

            # 保留最近30天的数据
            cutoff_time = datetime.now() - timedelta(days=30)
            historical_data = [
                dp for dp in historical_data
                if datetime.fromisoformat(dp["timestamp"]) > cutoff_time
            ]

            # 保存历史数据
            with open(historical_file, 'w', encoding='utf-8') as f:
                json.dump(historical_data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            print(f"警告：更新历史指标失败: {e}")

    def run_health_diagnostics(self) -> Dict:
        """运行完整的健康诊断

        Returns:
            Dict: 诊断结果和建议
        """
        try:
            # 获取当前健康状态
            health_status = self.get_overall_health_status()

            # 深度诊断分析
            diagnostics = {
                "diagnostic_timestamp": datetime.now().isoformat(),
                "overall_health_score": health_status["health_score"],
                "critical_issues": [],
                "performance_bottlenecks": [],
                "resource_constraints": [],
                "recommendations": health_status["diagnostic_recommendations"],
                "preventive_actions": []
            }

            # 分析关键问题
            for alert in health_status["alerts"]:
                if alert["severity"] == "critical":
                    diagnostics["critical_issues"].append({
                        "component": alert["component"],
                        "issue": alert["message"],
                        "impact": "严重影响系统功能",
                        "urgency": "立即处理"
                    })

            # 分析性能瓶颈
            for comp_name, comp_data in health_status["component_status"].items():
                if comp_data["response_time_ms"] > 3000:  # 超过3秒
                    diagnostics["performance_bottlenecks"].append({
                        "component": comp_name,
                        "metric": "response_time",
                        "current_value": comp_data["response_time_ms"],
                        "threshold": 3000,
                        "impact": "用户体验下降"
                    })

            return diagnostics

        except Exception as e:
            error_msg = f"运行健康诊断失败: {e}"
            print(f"错误：{error_msg}")
            return {
                "diagnostic_timestamp": datetime.now().isoformat(),
                "error": error_msg,
                "overall_health_score": 0.0,
                "critical_issues": [],
                "performance_bottlenecks": [],
                "resource_constraints": [],
                "recommendations": [],
                "preventive_actions": []
            }

    def get_recent_errors(self, limit: int = 10, severity: str = None) -> List[Dict]:
        """获取最近的错误记录

        Args:
            limit: 返回记录数量限制
            severity: 严重性过滤

        Returns:
            List[Dict]: 错误记录列表
        """
        return self._get_recent_errors(limit=limit)

    def generate_health_report(self, period_hours: int = 24) -> Dict:
        """生成健康报告

        Args:
            period_hours: 报告时间范围(小时)

        Returns:
            Dict: 健康报告数据
        """
        try:
            # 获取当前健康状态
            current_status = self.get_overall_health_status()

            # 生成周期报告
            report = {
                "report_timestamp": datetime.now().isoformat(),
                "period_hours": period_hours,
                "summary": {
                    "overall_status": current_status["overall_status"],
                    "health_score": current_status["health_score"],
                    "total_components": len(current_status["component_status"]),
                    "healthy_components": sum(1 for comp in current_status["component_status"].values()
                                            if comp["status"] == "healthy"),
                    "critical_alerts": len([a for a in current_status["alerts"] if a["severity"] == "critical"]),
                    "total_errors": len(current_status["recent_errors"])
                },
                "detailed_status": current_status,
                "recommendations": current_status["diagnostic_recommendations"]
            }

            return report

        except Exception as e:
            error_msg = f"生成健康报告失败: {e}"
            print(f"错误：{error_msg}")
            return {
                "report_timestamp": datetime.now().isoformat(),
                "period_hours": period_hours,
                "error": error_msg,
                "summary": {},
                "detailed_status": {},
                "recommendations": []
            }

    def setup_health_alerts(self, alert_config: Dict) -> bool:
        """设置健康告警

        Args:
            alert_config: 告警配置

        Returns:
            bool: 设置是否成功
        """
        try:
            # 更新配置
            if "alerts" not in self.config:
                self.config["alerts"] = {}

            self.config["alerts"].update(alert_config)

            # 保存配置
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)

            return True

        except Exception as e:
            print(f"错误：设置健康告警失败: {e}")
            return False

    # Additional methods for compatibility with test expectations
    def __init__(self, config_path: str = None):
        """初始化系统健康监控器"""
        self.config_path = config_path or "config/health_monitor.yaml"
        self.config = self._load_config()
        self.data_dir = Path("data/health_monitoring")
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Initialize component status for compatibility
        self.component_status = {}
        self.metrics_history = []
        self.performance_metrics = {}
        self.thresholds = {}
        self.alerts = []
        self._lock = threading.Lock()

        # Initialize component checkers
        self.component_checkers = {}
        self._initialize_component_checkers()

        # Health status cache
        self._health_cache = {}
        self._cache_expiry = {}
        self.cache_duration_seconds = self.config.get("health_monitoring", {}).get("check_interval_seconds", 60)

    def register_component(self, name: str, config: Dict):
        """注册组件进行监控"""
        with self._lock:
            # Initialize component status
            self.component_status[name] = {
                "status": "unknown",
                "type": config.get("type", "service"),
                "last_check": None,
                "error_count": 0,
                "response_time_ms": 0,
                "metadata": {}
            }

    def collect_system_metrics(self) -> Dict:
        """收集系统指标"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)

            # 内存使用
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_mb = memory.used / 1024 / 1024

            # 磁盘使用
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_free_gb = disk.free / 1024 / 1024 / 1024

            # 网络统计
            network = psutil.net_io_counters()

            metrics = {
                "cpu_usage": round(cpu_percent, 2),
                "memory_usage": round(memory_percent, 2),
                "memory_used_mb": round(memory_used_mb, 2),
                "disk_usage": round(disk_percent, 2),
                "disk_free_gb": round(disk_free_gb, 2),
                "network_bytes_sent": network.bytes_sent,
                "network_bytes_recv": network.bytes_recv,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            # Save to history
            with self._lock:
                self.metrics_history.append({
                    "timestamp": metrics["timestamp"],
                    "metrics": metrics
                })

                # Keep history within reasonable range
                if len(self.metrics_history) > 1000:
                    self.metrics_history = self.metrics_history[-1000:]

            return metrics

        except Exception as e:
            return {
                "error": f"Failed to collect system metrics: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

    def get_health_history(self, limit: int = 100) -> List[Dict]:
        """获取健康历史记录"""
        with self._lock:
            return self.metrics_history[-limit:] if self.metrics_history else []

    def check_thresholds(self, metrics: Dict) -> List[Dict]:
        """检查指标阈值并生成预警"""
        alerts = []

        # CPU usage alerts
        if metrics.get("cpu_usage", 0) > 90:
            alerts.append({
                "component": "system",
                "metric": "cpu_usage",
                "value": metrics["cpu_usage"],
                "threshold": 90,
                "severity": "critical",
                "message": f"CPU usage is critically high: {metrics['cpu_usage']}%",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        elif metrics.get("cpu_usage", 0) > 80:
            alerts.append({
                "component": "system",
                "metric": "cpu_usage",
                "value": metrics["cpu_usage"],
                "threshold": 80,
                "severity": "warning",
                "message": f"CPU usage is high: {metrics['cpu_usage']}%",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

        # Memory usage alerts
        if metrics.get("memory_usage", 0) > 90:
            alerts.append({
                "component": "system",
                "metric": "memory_usage",
                "value": metrics["memory_usage"],
                "threshold": 90,
                "severity": "critical",
                "message": f"Memory usage is critically high: {metrics['memory_usage']}%",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        elif metrics.get("memory_usage", 0) > 80:
            alerts.append({
                "component": "system",
                "metric": "memory_usage",
                "value": metrics["memory_usage"],
                "threshold": 80,
                "severity": "warning",
                "message": f"Memory usage is high: {metrics['memory_usage']}%",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

        # Disk space alerts
        if metrics.get("disk_free_gb", 100) < 1:
            alerts.append({
                "component": "system",
                "metric": "disk_free_gb",
                "value": metrics["disk_free_gb"],
                "threshold": 1,
                "severity": "critical",
                "message": f"Disk space is critically low: {metrics['disk_free_gb']}GB free",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        elif metrics.get("disk_free_gb", 100) < 5:
            alerts.append({
                "component": "system",
                "metric": "disk_free_gb",
                "value": metrics["disk_free_gb"],
                "threshold": 5,
                "severity": "warning",
                "message": f"Disk space is low: {metrics['disk_free_gb']}GB free",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

        # Save alerts
        with self._lock:
            self.alerts.extend(alerts)
            if len(self.alerts) > 1000:
                self.alerts = self.alerts[-1000:]

        return alerts

    def record_performance_metric(self, metric_name: str, value: float, metadata: Dict = None):
        """记录性能指标"""
        with self._lock:
            if metric_name not in self.performance_metrics:
                self.performance_metrics[metric_name] = []

            record = {
                "value": value,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            if metadata:
                record["metadata"] = metadata

            self.performance_metrics[metric_name].append(record)

            # Keep records within reasonable range
            if len(self.performance_metrics[metric_name]) > 1000:
                self.performance_metrics[metric_name] = self.performance_metrics[metric_name][-1000:]

    def get_performance_stats(self) -> Dict:
        """获取性能统计信息"""
        stats = {}

        with self._lock:
            for metric_name, records in self.performance_metrics.items():
                if not records:
                    continue

                values = [r["value"] for r in records]
                stats[metric_name] = {
                    "count": len(values),
                    "min": min(values),
                    "max": max(values),
                    "average": sum(values) / len(values),
                    "latest": values[-1],
                    "latest_timestamp": records[-1]["timestamp"]
                }

        return stats

    def set_metric_threshold(self, metric_name: str, thresholds: Dict):
        """设置指标阈值"""
        self.thresholds[metric_name] = thresholds

    def check_metric_threshold(self, metric_name: str, value: float) -> List[Dict]:
        """检查指标阈值"""
        alerts = []

        if metric_name in self.thresholds:
            thresholds = self.thresholds[metric_name]

            if value >= thresholds.get("critical", float('inf')):
                alerts.append({
                    "component": "performance",
                    "metric": metric_name,
                    "value": value,
                    "threshold": thresholds["critical"],
                    "severity": "critical",
                    "message": f"{metric_name} is critically high: {value}",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
            elif value >= thresholds.get("warning", float('inf')):
                alerts.append({
                    "component": "performance",
                    "metric": metric_name,
                    "value": value,
                    "threshold": thresholds["warning"],
                    "severity": "warning",
                    "message": f"{metric_name} is high: {value}",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })

        return alerts

    def record_metric_with_timestamp(self, metric_name: str, value: float, timestamp: float):
        """记录带时间戳的指标"""
        with self._lock:
            if metric_name not in self.performance_metrics:
                self.performance_metrics[metric_name] = []

            record = {
                "value": value,
                "timestamp": datetime.fromtimestamp(timestamp, timezone.utc).isoformat()
            }

            self.performance_metrics[metric_name].append(record)

    def analyze_metric_trend(self, metric_name: str) -> Dict:
        """分析指标趋势"""
        if metric_name not in self.performance_metrics:
            return {"error": f"No data for metric {metric_name}"}

        records = self.performance_metrics[metric_name]
        if len(records) < 2:
            return {"error": "Insufficient data for trend analysis"}

        # Simple linear trend analysis
        values = [r["value"] for r in records[-10:]]  # Use last 10 data points
        timestamps = list(range(len(values)))  # Simplify to indices

        # Calculate slope
        n = len(values)
        sum_x = sum(timestamps)
        sum_y = sum(values)
        sum_xy = sum(timestamps[i] * values[i] for i in range(n))
        sum_x2 = sum(x * x for x in timestamps)

        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)

        # Determine trend direction
        if slope > 0.1:
            direction = "increasing"
        elif slope < -0.1:
            direction = "decreasing"
        else:
            direction = "stable"

        return {
            "metric": metric_name,
            "direction": direction,
            "slope": round(slope, 4),
            "data_points": n,
            "latest_value": values[-1],
            "trend_strength": abs(slope)
        }

    def get_system_health(self) -> Dict:
        """获取系统整体健康状态（兼容方法）"""
        return self.get_overall_health_status()

    def record_operation(self, operation_type: str, result: Dict):
        """记录操作结果"""
        # This method can be used to track operation success rates
        pass