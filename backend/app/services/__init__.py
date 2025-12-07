# Services Package
# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: dependency injection)
"""Business logic services for Canvas Learning System."""

from app.services.agent_service import AgentResult, AgentService, AgentType
from app.services.background_task_manager import BackgroundTaskManager, TaskInfo, TaskStatus
from app.services.canvas_service import CanvasService
from app.services.metrics_collector import (
    HealthStatus,
    MetricsSummary,
    get_metrics_summary,
    get_prometheus_metrics,
)
from app.services.resource_monitor import (
    RESOURCE_CPU_USAGE,
    RESOURCE_DISK_USAGE,
    RESOURCE_MEMORY_USAGE,
    ResourceMonitor,
    get_default_monitor,
    get_resource_metrics_snapshot,
)
from app.services.review_service import ReviewProgress, ReviewService, ReviewStatus

__all__ = [
    # Core services
    "AgentService",
    "AgentType",
    "AgentResult",
    "CanvasService",
    "ReviewService",
    "ReviewProgress",
    "ReviewStatus",
    "BackgroundTaskManager",
    "TaskStatus",
    "TaskInfo",
    # Resource monitoring
    "ResourceMonitor",
    "get_resource_metrics_snapshot",
    "get_default_monitor",
    "RESOURCE_CPU_USAGE",
    "RESOURCE_MEMORY_USAGE",
    "RESOURCE_DISK_USAGE",
    # Metrics collection
    "MetricsSummary",
    "HealthStatus",
    "get_prometheus_metrics",
    "get_metrics_summary",
]
