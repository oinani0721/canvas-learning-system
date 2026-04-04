"""
Infra Domain Gateway — 基础设施统一入口

Strangler Fig Pattern: 所有外部调用应通过此 gateway 访问 infra 领域。

包含: event_bus, event_handlers, alert_manager, health_monitor,
       resource_monitor, background_task_manager, batch_orchestrator,
       intelligent_parallel_service, intelligent_grouping_service,
       session_manager, websocket_manager, metrics_collector,
       error_aggregator, notification_channels, prompt_registry,
       rollback_service
"""

from __future__ import annotations

# ── 事件系统 ──
from app.services.event_bus import EventBus, get_event_bus
from app.services.event_handlers import register_all_handlers

# ── 告警 ──
from app.services.alert_manager import AlertManager, AlertSeverity

# ── 监控 ──
from app.services.health_monitor import PipelineHealthMonitor
from app.services.resource_monitor import (
    get_default_monitor,
    get_resource_metrics_snapshot,
)
from app.services.metrics_collector import MetricsSummary

# ── 后台任务 ──
from app.services.background_task_manager import BackgroundTaskManager

# ── 批处理 ──
from app.services.intelligent_parallel_service import IntelligentParallelService
from app.services.intelligent_grouping_service import (
    IntelligentGroupingService,
    CanvasNotFoundError,
)
from app.services.session_manager import SessionManager
from app.services.websocket_manager import ConnectionManager, get_connection_manager

# ── 错误聚合 ──
from app.services.error_aggregator import ErrorAggregator

# ── 通知 ──
from app.services.notification_channels import create_default_dispatcher

# ── Prompt 管理 ──
from app.services.prompt_registry import get_prompt_registry

# ── 回滚 ──
from app.services.rollback_service import RollbackService

__all__ = [
    # 事件
    "EventBus",
    "get_event_bus",
    "register_all_handlers",
    # 告警
    "AlertManager",
    "AlertSeverity",
    # 监控
    "PipelineHealthMonitor",
    "get_default_monitor",
    "get_resource_metrics_snapshot",
    "MetricsSummary",
    # 后台任务
    "BackgroundTaskManager",
    # 批处理
    "IntelligentParallelService",
    "IntelligentGroupingService",
    "CanvasNotFoundError",
    "SessionManager",
    "ConnectionManager",
    "get_connection_manager",
    # 错误
    "ErrorAggregator",
    # 通知
    "create_default_dispatcher",
    # Prompt
    "get_prompt_registry",
    # 回滚
    "RollbackService",
]
