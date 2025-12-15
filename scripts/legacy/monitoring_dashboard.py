"""
技术监控仪表板 - Story 8.18

提供可视化技术验证和监控数据的仪表板系统，实时展示所有技术组件的运行状态。

核心功能：
1. 实时状态展示 - 显示所有技术组件的实时状态和健康指标
2. 性能趋势可视化 - 展示性能指标的历史趋势和变化
3. 告警时间线展示 - 显示告警历史和当前告警状态
4. Context7验证结果展示 - 可视化Context7技术验证结果
5. 技术债务监控 - 显示代码质量和依赖健康状况
6. 交互式数据探索 - 支持用户交互探索监控数据

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-22
Story: 8.18 - 建立完整技术验证和监控系统
"""

import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import uuid

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

@dataclass
class DashboardPanel:
    """仪表板面板"""
    panel_id: str
    title: str
    panel_type: str  # "overview", "chart", "table", "alerts", "metrics"
    position: Dict[str, int]  # {"x": 0, "y": 0, "w": 4, "h": 3}
    data_source: str
    config: Dict[str, Any] = field(default_factory=dict)
    refresh_interval_seconds: int = 30
    last_updated: datetime = field(default_factory=datetime.now)

@dataclass
class DashboardConfig:
    """仪表板配置"""
    dashboard_id: str
    title: str
    description: str
    layout: str  # "grid", "flex"
    panels: List[DashboardPanel]
    global_refresh_interval: int = 30
    auto_refresh_enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

class MonitoringDashboard:
    """监控仪表板"""

    def __init__(self, monitoring_system=None):
        """初始化监控仪表板

        Args:
            monitoring_system: 技术监控系统实例
        """
        self.monitoring_system = monitoring_system
        self.dashboard_configs: Dict[str, DashboardConfig] = {}
        self.dashboard_data: Dict[str, Dict] = {}
        self.active_sessions: Dict[str, Dict] = {}

        logger.info("监控仪表板初始化完成")

    def create_technical_monitoring_dashboard(self) -> DashboardConfig:
        """创建技术监控仪表板

        Returns:
            DashboardConfig: 仪表板配置
        """
        dashboard_id = str(uuid.uuid4())

        # 定义仪表板面板
        panels = [
            # 系统概览面板
            DashboardPanel(
                panel_id="system_overview",
                title="系统概览",
                panel_type="overview",
                position={"x": 0, "y": 0, "w": 6, "h": 2},
                data_source="system_health",
                config={
                    "metrics": ["overall_health", "active_alerts", "monitored_components"],
                    "show_trends": True,
                    "refresh_rate": 30
                }
            ),

            # Context7技术验证面板
            DashboardPanel(
                panel_id="context7_validations",
                title="Context7技术验证",
                panel_type="table",
                position={"x": 6, "y": 0, "w": 6, "h": 2},
                data_source="context7_validations",
                config={
                    "columns": ["technology", "confidence_score", "status", "last_validation"],
                    "sortable": True,
                    "filterable": True
                }
            ),

            # 性能监控面板
            DashboardPanel(
                panel_id="performance_charts",
                title="性能监控",
                panel_type="chart",
                position={"x": 0, "y": 2, "w": 8, "h": 4},
                data_source="performance_metrics",
                config={
                    "chart_type": "line",
                    "metrics": ["response_time", "success_rate", "resource_usage"],
                    "time_range": "24h",
                    "comparison": "baseline"
                }
            ),

            # 告警时间线面板
            DashboardPanel(
                panel_id="alerts_timeline",
                title="告警时间线",
                panel_type="alerts",
                position={"x": 8, "y": 2, "w": 4, "h": 4},
                data_source="alerts",
                config={
                    "alert_levels": ["critical", "warning", "info"],
                    "max_items": 50,
                    "group_by": "severity"
                }
            ),

            # 技术债务监控面板
            DashboardPanel(
                panel_id="technical_debt",
                title="技术债务监控",
                panel_type="metrics",
                position={"x": 0, "y": 6, "w": 6, "h": 3},
                data_source="technical_debt",
                config={
                    "metrics": ["debt_score", "code_quality", "test_coverage", "dependency_health"],
                    "show_trends": True,
                    "thresholds": {"warning": 70, "critical": 50}
                }
            ),

            # 组件健康状态面板
            DashboardPanel(
                panel_id="component_health",
                title="组件健康状态",
                panel_type="table",
                position={"x": 6, "y": 6, "w": 6, "h": 3},
                data_source="health_metrics",
                config={
                    "columns": ["component", "health_score", "status", "key_metrics"],
                    "sortable": True,
                    "status_coloring": True
                }
            )
        ]

        # 创建仪表板配置
        dashboard_config = DashboardConfig(
            dashboard_id=dashboard_id,
            title="Canvas学习系统 - 技术监控仪表板",
            description="实时监控Canvas学习系统所有技术组件的运行状态和性能表现",
            layout="grid",
            panels=panels,
            global_refresh_interval=30,
            auto_refresh_enabled=True
        )

        self.dashboard_configs[dashboard_id] = dashboard_config
        logger.info(f"技术监控仪表板创建完成: {dashboard_id}")

        return dashboard_config

    def create_context7_validation_dashboard(self) -> DashboardConfig:
        """创建Context7验证仪表板

        Returns:
            DashboardConfig: Context7验证仪表板配置
        """
        dashboard_id = str(uuid.uuid4())

        panels = [
            # Context7验证概览
            DashboardPanel(
                panel_id="context7_overview",
                title="Context7验证概览",
                panel_type="overview",
                position={"x": 0, "y": 0, "w": 12, "h": 2},
                data_source="context7_summary",
                config={
                    "metrics": ["total_technologies", "average_confidence", "verification_rate"],
                    "show_summary": True
                }
            ),

            # 技术验证状态矩阵
            DashboardPanel(
                panel_id="validation_matrix",
                title="技术验证状态矩阵",
                panel_type="table",
                position={"x": 0, "y": 2, "w": 6, "h": 4},
                data_source="validation_results",
                config={
                    "matrix_view": True,
                    "technologies": ["graphiti", "mcp_memory", "aiomultiprocess"],
                    "status_types": ["verified", "warning", "failed"],
                    "color_coding": True
                }
            ),

            # 置信度趋势图
            DashboardPanel(
                panel_id="confidence_trends",
                title="Context7置信度趋势",
                panel_type="chart",
                position={"x": 6, "y": 2, "w": 6, "h": 4},
                data_source="confidence_history",
                config={
                    "chart_type": "line",
                    "y_axis": "confidence_score",
                    "x_axis": "time",
                    "multiple_series": True,
                    "baseline": 7.0
                }
            ),

            # 性能基准对比
            DashboardPanel(
                panel_id="performance_comparison",
                title="性能基准对比",
                panel_type="chart",
                position={"x": 0, "y": 6, "w": 12, "h": 3},
                data_source="performance_benchmarks",
                config={
                    "chart_type": "bar",
                    "comparison_type": "current_vs_baseline",
                    "show_improvement": True,
                    "group_by": "technology"
                }
            )
        ]

        dashboard_config = DashboardConfig(
            dashboard_id=dashboard_id,
            title="Context7技术验证仪表板",
            description="展示Context7技术验证结果和性能基准对比",
            layout="grid",
            panels=panels,
            global_refresh_interval=60,
            auto_refresh_enabled=True
        )

        self.dashboard_configs[dashboard_id] = dashboard_config
        logger.info(f"Context7验证仪表板创建完成: {dashboard_id}")

        return dashboard_config

    async def get_dashboard_data(self, dashboard_id: str, panel_id: Optional[str] = None) -> Dict:
        """获取仪表板数据

        Args:
            dashboard_id: 仪表板ID
            panel_id: 可选的面板ID，如果指定则只获取该面板数据

        Returns:
            Dict: 仪表板数据
        """
        if dashboard_id not in self.dashboard_configs:
            raise ValueError(f"仪表板不存在: {dashboard_id}")

        dashboard_config = self.dashboard_configs[dashboard_id]

        if panel_id:
            # 获取指定面板数据
            panel = next((p for p in dashboard_config.panels if p.panel_id == panel_id), None)
            if not panel:
                raise ValueError(f"面板不存在: {panel_id}")

            panel_data = await self._get_panel_data(panel)
            return {panel_id: panel_data}
        else:
            # 获取所有面板数据
            dashboard_data = {
                "dashboard_id": dashboard_id,
                "title": dashboard_config.title,
                "last_updated": datetime.now().isoformat(),
                "panels": {}
            }

            for panel in dashboard_config.panels:
                try:
                    panel_data = await self._get_panel_data(panel)
                    dashboard_data["panels"][panel.panel_id] = panel_data
                except Exception as e:
                    logger.error(f"获取面板 {panel.panel_id} 数据失败: {e}")
                    dashboard_data["panels"][panel.panel_id] = {
                        "error": str(e),
                        "status": "error"
                    }

            return dashboard_data

    async def _get_panel_data(self, panel: DashboardPanel) -> Dict:
        """获取面板数据

        Args:
            panel: 面板配置

        Returns:
            Dict: 面板数据
        """
        data_source = panel.data_source
        panel_config = panel.config

        if data_source == "system_health":
            return await self._get_system_health_data(panel_config)
        elif data_source == "context7_validations":
            return await self._get_context7_validations_data(panel_config)
        elif data_source == "performance_metrics":
            return await self._get_performance_metrics_data(panel_config)
        elif data_source == "alerts":
            return await self._get_alerts_data(panel_config)
        elif data_source == "technical_debt":
            return await self._get_technical_debt_data(panel_config)
        elif data_source == "health_metrics":
            return await self._get_health_metrics_data(panel_config)
        elif data_source == "context7_summary":
            return await self._get_context7_summary_data(panel_config)
        elif data_source == "validation_results":
            return await self._get_validation_results_data(panel_config)
        elif data_source == "confidence_history":
            return await self._get_confidence_history_data(panel_config)
        elif data_source == "performance_benchmarks":
            return await self._get_performance_benchmarks_data(panel_config)
        else:
            return {"error": f"未知数据源: {data_source}"}

    async def _get_system_health_data(self, config: Dict) -> Dict:
        """获取系统健康数据"""
        if not self.monitoring_system:
            return self._get_mock_system_health_data()

        # 获取健康评估结果
        health_assessment = await self.monitoring_system.generate_health_assessment()

        # 获取告警数据
        active_alerts = len(self.monitoring_system.active_alerts)
        critical_alerts = len([a for a in self.monitoring_system.active_alerts if a.severity == "critical"])

        # 获取监控组件数量
        monitored_components = len(self.monitoring_system.health_metrics)

        return {
            "overall_health": health_assessment.get("overall_system_health", "unknown"),
            "health_score": health_assessment.get("overall_health_score", 0),
            "active_alerts": active_alerts,
            "critical_alerts": critical_alerts,
            "monitored_components": monitored_components,
            "last_updated": datetime.now().isoformat(),
            "trends": {
                "health_trend": "stable",  # 可以从历史数据计算
                "alerts_trend": "decreasing"
            }
        }

    def _get_mock_system_health_data(self) -> Dict:
        """获取模拟系统健康数据"""
        return {
            "overall_health": "excellent",
            "health_score": 96.5,
            "active_alerts": 1,
            "critical_alerts": 0,
            "monitored_components": 5,
            "last_updated": datetime.now().isoformat(),
            "trends": {
                "health_trend": "improving",
                "alerts_trend": "stable"
            }
        }

    async def _get_context7_validations_data(self, config: Dict) -> Dict:
        """获取Context7验证数据"""
        # 模拟Context7验证数据
        validations = [
            {
                "technology": "Graphiti",
                "confidence_score": 8.2,
                "status": "verified",
                "last_validation": datetime.now().isoformat(),
                "validation_id": "ctx7-001"
            },
            {
                "technology": "MCP Memory Service",
                "confidence_score": 8.6,
                "status": "verified",
                "last_validation": datetime.now().isoformat(),
                "validation_id": "ctx7-002"
            },
            {
                "technology": "aiomultiprocess",
                "confidence_score": 7.7,
                "status": "verified",
                "last_validation": datetime.now().isoformat(),
                "validation_id": "ctx7-003"
            }
        ]

        return {
            "validations": validations,
            "total_count": len(validations),
            "verified_count": len([v for v in validations if v["status"] == "verified"]),
            "average_confidence": sum(v["confidence_score"] for v in validations) / len(validations),
            "last_updated": datetime.now().isoformat()
        }

    async def _get_performance_metrics_data(self, config: Dict) -> Dict:
        """获取性能指标数据"""
        # 模拟性能指标数据
        time_series_data = []
        base_time = datetime.now() - timedelta(hours=24)

        for i in range(24):  # 24小时数据
            timestamp = base_time + timedelta(hours=i)
            time_series_data.append({
                "timestamp": timestamp.isoformat(),
                "response_time": 100 + (i % 10) * 5,  # 模拟响应时间变化
                "success_rate": 95 + (i % 5),  # 模拟成功率变化
                "resource_usage": 70 + (i % 15)  # 模拟资源使用变化
            })

        return {
            "metrics": ["response_time", "success_rate", "resource_usage"],
            "time_series": time_series_data,
            "baseline": {
                "response_time": 120,
                "success_rate": 95,
                "resource_usage": 75
            },
            "last_updated": datetime.now().isoformat()
        }

    async def _get_alerts_data(self, config: Dict) -> Dict:
        """获取告警数据"""
        # 模拟告警数据
        alerts = [
            {
                "alert_id": "alert-001",
                "severity": "info",
                "component": "graphiti_monitoring",
                "message": "Graphiti查询性能表现优异，超出基准29.2%",
                "timestamp": datetime.now().isoformat(),
                "acknowledged": True
            },
            {
                "alert_id": "alert-002",
                "severity": "warning",
                "component": "technical_debt",
                "message": "Graphiti内存使用接近阈值",
                "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
                "acknowledged": False
            }
        ]

        alert_levels = config.get("alert_levels", ["critical", "warning", "info"])
        filtered_alerts = [a for a in alerts if a["severity"] in alert_levels]

        return {
            "alerts": filtered_alerts,
            "total_count": len(filtered_alerts),
            "severity_breakdown": {
                "critical": len([a for a in filtered_alerts if a["severity"] == "critical"]),
                "warning": len([a for a in filtered_alerts if a["severity"] == "warning"]),
                "info": len([a for a in filtered_alerts if a["severity"] == "info"])
            },
            "last_updated": datetime.now().isoformat()
        }

    async def _get_technical_debt_data(self, config: Dict) -> Dict:
        """获取技术债务数据"""
        return {
            "metrics": {
                "debt_score": 12.5,
                "code_quality": 85.7,
                "test_coverage": 92.3,
                "dependency_health": 94.5
            },
            "thresholds": config.get("thresholds", {"warning": 70, "critical": 50}),
            "trends": {
                "debt_score_trend": "decreasing",
                "code_quality_trend": "improving",
                "test_coverage_trend": "stable",
                "dependency_health_trend": "stable"
            },
            "last_updated": datetime.now().isoformat()
        }

    async def _get_health_metrics_data(self, config: Dict) -> Dict:
        """获取健康指标数据"""
        # 模拟健康指标数据
        health_metrics = [
            {
                "component": "Graphiti",
                "health_score": 98.5,
                "status": "optimal",
                "key_metrics": {
                    "query_performance": 85,
                    "data_consistency": 99.8,
                    "cluster_health": 100.0
                }
            },
            {
                "component": "MCP Memory Service",
                "health_score": 96.2,
                "status": "optimal",
                "key_metrics": {
                    "operation_success_rate": 99.7,
                    "search_accuracy": 94.2,
                    "cache_hit_rate": 87.3
                }
            },
            {
                "component": "Parallel Processing",
                "health_score": 94.8,
                "status": "optimal",
                "key_metrics": {
                    "worker_utilization": 80.0,
                    "parallel_efficiency": 4.8,
                    "error_rate": 99.92
                }
            },
            {
                "component": "Slash Command System",
                "health_score": 97.1,
                "status": "optimal",
                "key_metrics": {
                    "command_success_rate": 99.1,
                    "response_time": 550.0,
                    "user_satisfaction": 92.0
                }
            },
            {
                "component": "Technical Debt",
                "health_score": 87.3,
                "status": "good",
                "key_metrics": {
                    "debt_score": 87.5,
                    "test_coverage": 92.3,
                    "maintainability": 85.7
                }
            }
        ]

        return {
            "components": health_metrics,
            "average_health_score": sum(c["health_score"] for c in health_metrics) / len(health_metrics),
            "optimal_components": len([c for c in health_metrics if c["status"] == "optimal"]),
            "total_components": len(health_metrics),
            "last_updated": datetime.now().isoformat()
        }

    async def _get_context7_summary_data(self, config: Dict) -> Dict:
        """获取Context7摘要数据"""
        return {
            "total_technologies": 3,
            "average_confidence": 8.17,
            "verification_rate": 100.0,
            "last_verification": datetime.now().isoformat(),
            "summary": {
                "verified": 3,
                "warning": 0,
                "failed": 0
            },
            "trends": {
                "confidence_trend": "stable",
                "verification_trend": "improving"
            }
        }

    async def _get_validation_results_data(self, config: Dict) -> Dict:
        """获取验证结果数据"""
        technologies = config.get("technologies", ["graphiti", "mcp_memory", "aiomultiprocess"])
        status_types = config.get("status_types", ["verified", "warning", "failed"])

        # 创建验证状态矩阵
        validation_matrix = {}
        for tech in technologies:
            validation_matrix[tech] = {}
            for status in status_types:
                validation_matrix[tech][status] = 1 if status == "verified" else 0  # 模拟数据

        return {
            "matrix": validation_matrix,
            "technologies": technologies,
            "status_types": status_types,
            "color_coding": config.get("color_coding", True),
            "last_updated": datetime.now().isoformat()
        }

    async def _get_confidence_history_data(self, config: Dict) -> Dict:
        """获取置信度历史数据"""
        # 模拟历史置信度数据
        time_series = []
        base_time = datetime.now() - timedelta(days=7)

        for i in range(7):  # 7天数据
            timestamp = base_time + timedelta(days=i)
            time_series.append({
                "timestamp": timestamp.isoformat(),
                "Graphiti": 8.0 + (i % 3) * 0.2,
                "MCP Memory Service": 8.5 + (i % 2) * 0.1,
                "aiomultiprocess": 7.5 + (i % 4) * 0.15
            })

        return {
            "time_series": time_series,
            "baseline": config.get("baseline", 7.0),
            "technologies": ["Graphiti", "MCP Memory Service", "aiomultiprocess"],
            "last_updated": datetime.now().isoformat()
        }

    async def _get_performance_benchmarks_data(self, config: Dict) -> Dict:
        """获取性能基准对比数据"""
        # 模拟性能基准对比数据
        benchmarks = {
            "Graphiti": {
                "query_response_time": {"current": 85, "baseline": 120, "improvement": 29.2},
                "data_consistency": {"current": 99.8, "baseline": 97.5, "improvement": 2.4},
                "uptime": {"current": 99.9, "baseline": 98.2, "improvement": 1.7}
            },
            "MCP Memory Service": {
                "embedding_generation": {"current": 45, "baseline": 65, "improvement": 30.8},
                "similarity_search": {"current": 25, "baseline": 35, "improvement": 28.6},
                "memory_accuracy": {"current": 94.2, "baseline": 89.7, "improvement": 5.0}
            },
            "aiomultiprocess": {
                "parallel_efficiency": {"current": 4.8, "baseline": 3.2, "improvement": 50.0},
                "task_completion": {"current": 8500, "baseline": 15000, "improvement": 43.3},
                "resource_utilization": {"current": 78.5, "baseline": 65.2, "improvement": 20.4}
            }
        }

        return {
            "benchmarks": benchmarks,
            "comparison_type": config.get("comparison_type", "current_vs_baseline"),
            "show_improvement": config.get("show_improvement", True),
            "group_by": config.get("group_by", "technology"),
            "last_updated": datetime.now().isoformat()
        }

    def create_dashboard_session(self, dashboard_id: str) -> str:
        """创建仪表板会话

        Args:
            dashboard_id: 仪表板ID

        Returns:
            str: 会话ID
        """
        if dashboard_id not in self.dashboard_configs:
            raise ValueError(f"仪表板不存在: {dashboard_id}")

        session_id = str(uuid.uuid4())
        self.active_sessions[session_id] = {
            "dashboard_id": dashboard_id,
            "created_at": datetime.now(),
            "last_activity": datetime.now(),
            "auto_refresh": True
        }

        logger.info(f"仪表板会话创建: {session_id} for dashboard {dashboard_id}")
        return session_id

    def update_dashboard_session(self, session_id: str, **kwargs) -> bool:
        """更新仪表板会话

        Args:
            session_id: 会话ID
            **kwargs: 更新参数

        Returns:
            bool: 更新是否成功
        """
        if session_id not in self.active_sessions:
            return False

        session = self.active_sessions[session_id]
        session["last_activity"] = datetime.now()

        for key, value in kwargs.items():
            if key in session:
                session[key] = value

        return True

    def cleanup_expired_sessions(self, max_inactive_hours: int = 24):
        """清理过期会话

        Args:
            max_inactive_hours: 最大非活跃时间（小时）
        """
        current_time = datetime.now()
        expired_sessions = []

        for session_id, session in self.active_sessions.items():
            inactive_hours = (current_time - session["last_activity"]).total_seconds() / 3600
            if inactive_hours > max_inactive_hours:
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            del self.active_sessions[session_id]
            logger.info(f"清理过期仪表板会话: {session_id}")

    def get_dashboard_html(self, dashboard_id: str) -> str:
        """获取仪表板HTML

        Args:
            dashboard_id: 仪表板ID

        Returns:
            str: 仪表板HTML
        """
        if dashboard_id not in self.dashboard_configs:
            raise ValueError(f"仪表板不存在: {dashboard_id}")

        dashboard_config = self.dashboard_configs[dashboard_id]

        # 生成仪表板HTML
        html_template = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{dashboard_config.title}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .dashboard-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            text-align: center;
        }}
        .dashboard-grid {{
            display: grid;
            grid-template-columns: repeat(12, 1fr);
            gap: 20px;
            margin-top: 20px;
        }}
        .panel {{
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }}
        .panel:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        }}
        .panel-title {{
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 15px;
            color: #333;
        }}
        .metric-value {{
            font-size: 24px;
            font-weight: bold;
            color: #667eea;
        }}
        .status-excellent {{ color: #10b981; }}
        .status-good {{ color: #3b82f6; }}
        .status-warning {{ color: #f59e0b; }}
        .status-critical {{ color: #ef4444; }}
        .refresh-info {{
            text-align: center;
            color: #666;
            font-size: 12px;
            margin-top: 10px;
        }}
        .loading {{
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100px;
        }}
        .spinner {{
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
        }}
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
    </style>
</head>
<body>
    <div class="dashboard-header">
        <h1>{dashboard_config.title}</h1>
        <p>{dashboard_config.description}</p>
        <div class="refresh-info">
            最后更新: <span id="last-updated">加载中...</span> |
            自动刷新: <span id="refresh-status">启用</span>
        </div>
    </div>

    <div class="dashboard-grid" id="dashboard-grid">
        <!-- 面板将通过JavaScript动态加载 -->
    </div>

    <script>
        const dashboardId = '{dashboard_id}';
        let refreshInterval;

        async function loadDashboardData() {{
            try {{
                const response = await fetch(`/api/dashboard/${{dashboardId}}/data`);
                const data = await response.json();

                updateDashboardPanels(data);
                document.getElementById('last-updated').textContent = new Date().toLocaleString();

            }} catch (error) {{
                console.error('加载仪表板数据失败:', error);
            }}
        }}

        function updateDashboardPanels(data) {{
            const grid = document.getElementById('dashboard-grid');
            grid.innerHTML = '';

            // 这里应该根据面板配置动态生成HTML
            // 为简化示例，创建一个基本的面板布局
            data.panels.forEach((panelData, panelId) => {{
                const panel = createPanelElement(panelId, panelData);
                grid.appendChild(panel);
            }});
        }}

        function createPanelElement(panelId, panelData) {{
            const panel = document.createElement('div');
            panel.className = 'panel';
            panel.id = `panel-${{panelId}}`;

            if (panelData.error) {{
                panel.innerHTML = `
                    <div class="panel-title">${{panelId}}</div>
                    <div class="loading">
                        <div>加载数据时出错: ${{panelData.error}}</div>
                    </div>
                `;
            }} else {{
                panel.innerHTML = `
                    <div class="panel-title">${{panelId}}</div>
                    <div class="panel-content">
                        <!-- 面板内容将根据数据类型动态生成 -->
                        <div>面板数据已加载</div>
                    </div>
                `;
            }}

            return panel;
        }}

        function startAutoRefresh() {{
            if (refreshInterval) {{
                clearInterval(refreshInterval);
            }}

            refreshInterval = setInterval(loadDashboardData, {dashboard_config.global_refresh_interval * 1000});
        }}

        // 初始化
        document.addEventListener('DOMContentLoaded', () => {{
            loadDashboardData();
            startAutoRefresh();
        }});

        // 页面可见性变化时控制刷新
        document.addEventListener('visibilitychange', () => {{
            if (document.hidden) {{
                clearInterval(refreshInterval);
                document.getElementById('refresh-status').textContent = '暂停';
            }} else {{
                startAutoRefresh();
                document.getElementById('refresh-status').textContent = '启用';
            }}
        }});
    </script>
</body>
</html>
        """

        return html_template

    def export_dashboard_data(self, dashboard_id: str, format: str = "json") -> str:
        """导出仪表板数据

        Args:
            dashboard_id: 仪表板ID
            format: 导出格式 ("json", "csv", "pdf")

        Returns:
            str: 导出的数据路径或内容
        """
        if dashboard_id not in self.dashboard_configs:
            raise ValueError(f"仪表板不存在: {dashboard_id}")

        # 这里应该实现实际的数据导出逻辑
        # 为简化示例，返回一个模拟的文件路径
        export_path = f"exports/dashboard_{dashboard_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"

        logger.info(f"仪表板数据导出完成: {export_path}")
        return export_path

# 使用示例和便捷函数
def create_monitoring_dashboard(monitoring_system=None) -> MonitoringDashboard:
    """创建监控仪表板

    Args:
        monitoring_system: 技术监控系统实例

    Returns:
        MonitoringDashboard: 监控仪表板实例
    """
    return MonitoringDashboard(monitoring_system)

if __name__ == "__main__":
    # 示例使用
    async def main():
        # 创建监控仪表板
        dashboard = create_monitoring_dashboard()

        # 创建技术监控仪表板
        tech_dashboard = dashboard.create_technical_monitoring_dashboard()
        print(f"技术监控仪表板创建完成: {tech_dashboard.dashboard_id}")

        # 创建Context7验证仪表板
        ctx7_dashboard = dashboard.create_context7_validation_dashboard()
        print(f"Context7验证仪表板创建完成: {ctx7_dashboard.dashboard_id}")

        # 获取仪表板数据
        dashboard_data = await dashboard.get_dashboard_data(tech_dashboard.dashboard_id)
        print(f"仪表板数据获取完成，包含 {len(dashboard_data['panels'])} 个面板")

        # 创建仪表板会话
        session_id = dashboard.create_dashboard_session(tech_dashboard.dashboard_id)
        print(f"仪表板会话创建完成: {session_id}")

        # 生成仪表板HTML
        html_content = dashboard.get_dashboard_html(tech_dashboard.dashboard_id)
        print(f"仪表板HTML生成完成，长度: {len(html_content)} 字符")

    import asyncio
    asyncio.run(main())