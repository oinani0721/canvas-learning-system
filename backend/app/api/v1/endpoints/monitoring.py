# Canvas Learning System - Monitoring API Endpoints
# ✅ Verified from OpenAPI Spec (canvas-api.openapi.yml:644-662)
# ✅ Verified from Context7:/fastapi/fastapi (topic: APIRouter Query Depends)
# ✅ Verified from Context7:/pydantic/pydantic (topic: BaseModel)
"""
Monitoring and alert API endpoints.

Provides:
- GET /metrics/alerts - Get active alerts
- GET /metrics/summary - Get dashboard data

[Source: specs/api/canvas-api.openapi.yml:630-662]
[Source: docs/stories/17.3.story.md - Tasks 4, 6]
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

# ✅ Verified from ADR-010:77-100 (structlog logging)
import structlog

# ✅ Verified from Context7:/fastapi/fastapi (topic: APIRouter Query Depends)
from fastapi import APIRouter, Depends, HTTPException, Query

# ✅ Verified from Context7:/pydantic/pydantic (topic: BaseModel)
from pydantic import BaseModel, ConfigDict, Field

logger = structlog.get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Response Models
# [Source: specs/api/canvas-api.openapi.yml:1062-1091]
# ═══════════════════════════════════════════════════════════════════════════════

class AlertResponse(BaseModel):
    """Alert response model.

    [Source: specs/api/canvas-api.openapi.yml:1062-1091]

    Matches the OpenAPI Alert schema definition.
    """
    id: str = Field(..., description="Unique alert identifier")
    name: str = Field(..., description="Alert name (e.g., 'HighAPILatency')")
    severity: str = Field(..., description="Alert severity: critical, warning, info")
    message: str = Field(..., description="Human-readable alert message")
    triggered_at: datetime = Field(..., description="When alert was triggered")
    value: Optional[float] = Field(None, description="Current metric value")
    threshold: Optional[float] = Field(None, description="Alert threshold")
    labels: Dict[str, str] = Field(default_factory=dict, description="Additional labels")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "abc123def456",
                "name": "HighAPILatency",
                "severity": "warning",
                "message": "95分位API响应时间超过1秒，当前值: 1.5s",
                "triggered_at": "2025-12-03T20:15:00",
                "value": 1.5,
                "threshold": 1.0,
                "labels": {"endpoint": "/api/v1/canvas"},
            }
        }
    )


class AlertListResponse(BaseModel):
    """Alert list response.

    [Source: specs/api/canvas-api.openapi.yml:644-662]
    """
    alerts: List[AlertResponse] = Field(..., description="List of active alerts")
    total: int = Field(..., description="Total count of active alerts")


# ═══════════════════════════════════════════════════════════════════════════════
# Dashboard Summary Models
# [Source: specs/api/canvas-api.openapi.yml:987-1060]
# ═══════════════════════════════════════════════════════════════════════════════

class APIMetricsSummary(BaseModel):
    """API metrics summary.

    [Source: specs/api/canvas-api.openapi.yml:987-1000]
    """
    requests_total: int = Field(..., description="Total requests count")
    requests_per_second: float = Field(..., description="Current RPS")
    avg_latency_ms: float = Field(..., description="Average latency in ms")
    p95_latency_ms: float = Field(..., description="P95 latency in ms")
    error_rate: float = Field(..., description="Error rate (0.0 - 1.0)")


class AgentTypeSummary(BaseModel):
    """Agent type summary."""
    agent_type: str
    invocations: int
    avg_execution_time_s: float


class AgentMetricsSummary(BaseModel):
    """Agent metrics summary.

    [Source: specs/api/canvas-api.openapi.yml:1001-1020]
    """
    invocations_total: int = Field(..., description="Total agent invocations")
    avg_execution_time_s: float = Field(..., description="Average execution time")
    by_type: List[AgentTypeSummary] = Field(
        default_factory=list,
        description="Breakdown by agent type"
    )


class MemoryLayerSummary(BaseModel):
    """Memory layer summary."""
    queries_total: int
    avg_latency_ms: float


class MemorySystemSummary(BaseModel):
    """Memory system metrics summary.

    [Source: specs/api/canvas-api.openapi.yml:1021-1040]
    """
    graphiti: MemoryLayerSummary
    temporal: MemoryLayerSummary
    semantic: MemoryLayerSummary


class ResourcesSummary(BaseModel):
    """System resources summary.

    [Source: specs/api/canvas-api.openapi.yml:1041-1055]
    """
    cpu_usage_percent: float = Field(..., description="CPU usage percentage")
    memory_usage_percent: float = Field(..., description="Memory usage percentage")
    disk_usage_percent: float = Field(..., description="Disk usage percentage")


class AlertsSummary(BaseModel):
    """Alerts summary for dashboard."""
    active_count: int = Field(..., description="Total active alerts")
    critical_count: int = Field(..., description="Critical alerts count")
    warning_count: int = Field(..., description="Warning alerts count")
    info_count: int = Field(0, description="Info alerts count")


class MetricsSummaryResponse(BaseModel):
    """Complete metrics summary for dashboard.

    [Source: specs/api/canvas-api.openapi.yml:987-1060]
    [Source: docs/stories/17.3.story.md - AC 6]
    """
    timestamp: datetime = Field(..., description="Summary timestamp")
    api: APIMetricsSummary
    agents: AgentMetricsSummary
    memory_system: MemorySystemSummary
    resources: ResourcesSummary
    alerts: AlertsSummary

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "timestamp": "2025-12-03T20:15:00",
                "api": {
                    "requests_total": 10000,
                    "requests_per_second": 25.5,
                    "avg_latency_ms": 150.0,
                    "p95_latency_ms": 350.0,
                    "error_rate": 0.01,
                },
                "agents": {
                    "invocations_total": 500,
                    "avg_execution_time_s": 2.5,
                    "by_type": [
                        {"agent_type": "scoring-agent", "invocations": 200, "avg_execution_time_s": 1.8},
                    ],
                },
                "memory_system": {
                    "graphiti": {"queries_total": 1000, "avg_latency_ms": 50.0},
                    "temporal": {"queries_total": 800, "avg_latency_ms": 30.0},
                    "semantic": {"queries_total": 500, "avg_latency_ms": 100.0},
                },
                "resources": {
                    "cpu_usage_percent": 45.0,
                    "memory_usage_percent": 60.0,
                    "disk_usage_percent": 35.0,
                },
                "alerts": {
                    "active_count": 2,
                    "critical_count": 0,
                    "warning_count": 2,
                    "info_count": 0,
                },
            }
        }
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Router Definition
# [Source: docs/stories/17.3.story.md - Task 4]
# ═══════════════════════════════════════════════════════════════════════════════

router = APIRouter()

# Alias for router.py import consistency
monitoring_router = router


# Global alert manager reference (set by application startup)
_alert_manager = None


def get_alert_manager():
    """Get the global AlertManager instance.

    Returns:
        AlertManager: The global alert manager

    Raises:
        HTTPException: If alert manager is not initialized
    """
    if _alert_manager is None:
        raise HTTPException(
            status_code=503,
            detail="Alert manager not initialized"
        )
    return _alert_manager


def set_alert_manager(manager):
    """Set the global AlertManager instance.

    Called during application startup.

    Args:
        manager: AlertManager instance
    """
    global _alert_manager
    _alert_manager = manager


# ═══════════════════════════════════════════════════════════════════════════════
# Alert Endpoints
# [Source: specs/api/canvas-api.openapi.yml:644-662]
# ═══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/alerts",
    response_model=AlertListResponse,
    summary="Get active alerts",
    description="Returns list of currently active (firing) alerts",
)
async def get_active_alerts(
    severity: Optional[str] = Query(
        None,
        description="Filter by severity: critical, warning, info",
        enum=["critical", "warning", "info"],
    ),
    limit: int = Query(
        100,
        ge=1,
        le=1000,
        description="Maximum number of alerts to return",
    ),
    offset: int = Query(
        0,
        ge=0,
        description="Offset for pagination",
    ),
    alert_manager = Depends(get_alert_manager),
) -> AlertListResponse:
    """Get currently active alerts.

    [Source: specs/api/canvas-api.openapi.yml:644-662]
    [Source: docs/stories/17.3.story.md - AC 4]

    Args:
        severity: Optional severity filter
        limit: Maximum results (default: 100, max: 1000)
        offset: Pagination offset (default: 0)
        alert_manager: Injected AlertManager

    Returns:
        AlertListResponse: List of alerts and total count
    """
    from app.services.alert_manager import AlertSeverity

    severity_enum = None
    if severity:
        try:
            severity_enum = AlertSeverity(severity)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid severity: {severity}"
            )

    alerts = alert_manager.get_active_alerts(severity=severity_enum)

    # Apply pagination
    paginated = alerts[offset:offset + limit]

    logger.debug(
        "monitoring.get_alerts",
        total=len(alerts),
        returned=len(paginated),
        severity=severity,
    )

    return AlertListResponse(
        alerts=[AlertResponse(**a.to_dict()) for a in paginated],
        total=len(alerts),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Dashboard Summary Endpoint
# [Source: specs/api/canvas-api.openapi.yml:630-642]
# ═══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/summary",
    response_model=MetricsSummaryResponse,
    summary="Get metrics summary",
    description="Returns comprehensive metrics summary for dashboard display",
)
async def get_metrics_summary(
    alert_manager = Depends(get_alert_manager),
) -> MetricsSummaryResponse:
    """Get comprehensive metrics summary for dashboard.

    [Source: specs/api/canvas-api.openapi.yml:630-642]
    [Source: docs/stories/17.3.story.md - AC 6]

    Returns:
        MetricsSummaryResponse: Complete metrics summary
    """
    from datetime import datetime as dt

    # Get alert summary
    alerts_summary = alert_manager.get_alerts_summary()

    # Get API metrics
    api_metrics = _get_api_metrics()

    # Get agent metrics
    agent_metrics = _get_agent_metrics()

    # Get memory system metrics
    memory_metrics = _get_memory_metrics()

    # Get resource metrics
    resource_metrics = _get_resource_metrics()

    logger.debug("monitoring.get_summary")

    return MetricsSummaryResponse(
        timestamp=dt.now(),
        api=APIMetricsSummary(**api_metrics),
        agents=AgentMetricsSummary(**agent_metrics),
        memory_system=MemorySystemSummary(**memory_metrics),
        resources=ResourcesSummary(**resource_metrics),
        alerts=AlertsSummary(**alerts_summary),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Metrics Collection Helpers
# [Source: docs/stories/17.3.story.md - Task 6]
# ═══════════════════════════════════════════════════════════════════════════════

def _get_api_metrics() -> Dict[str, Any]:
    """Get API metrics from Prometheus registry.

    [Source: backend/app/middleware/metrics.py]

    Returns:
        Dict with API metrics
    """
    from prometheus_client import REGISTRY

    # Get request count
    requests_total = 0
    error_count = 0
    latency_sum = 0.0
    latency_count = 0

    for metric in REGISTRY.collect():
        if metric.name == 'canvas_api_requests_total':
            for sample in metric.samples:
                if sample.name.endswith('_total') or sample.name == 'canvas_api_requests_total':
                    count = int(sample.value)
                    requests_total += count
                    status = sample.labels.get('status', '200')
                    if status.startswith('5'):
                        error_count += count

        elif metric.name == 'canvas_api_request_latency_seconds':
            for sample in metric.samples:
                if sample.name.endswith('_sum'):
                    latency_sum += sample.value
                elif sample.name.endswith('_count'):
                    latency_count += int(sample.value)

    # Calculate statistics
    avg_latency_ms = (latency_sum / latency_count * 1000) if latency_count > 0 else 0
    error_rate = error_count / requests_total if requests_total > 0 else 0

    return {
        "requests_total": requests_total,
        "requests_per_second": 0.0,  # Would need time-series for accurate calculation
        "avg_latency_ms": round(avg_latency_ms, 2),
        "p95_latency_ms": 0.0,  # Would need histogram percentile calculation
        "error_rate": round(error_rate, 4),
    }


def _get_agent_metrics() -> Dict[str, Any]:
    """Get agent metrics from Prometheus registry.

    [Source: backend/app/middleware/agent_metrics.py]

    Returns:
        Dict with agent metrics
    """
    from prometheus_client import REGISTRY

    invocations_total = 0
    execution_sum = 0.0
    execution_count = 0
    by_type = {}

    for metric in REGISTRY.collect():
        if metric.name == 'canvas_agent_invocations_total':
            for sample in metric.samples:
                if sample.name == 'canvas_agent_invocations_total':
                    agent_type = sample.labels.get('agent_type', 'unknown')
                    count = int(sample.value)
                    invocations_total += count
                    if agent_type not in by_type:
                        by_type[agent_type] = {"invocations": 0, "sum": 0.0, "count": 0}
                    by_type[agent_type]["invocations"] += count

        elif metric.name == 'canvas_agent_execution_seconds':
            for sample in metric.samples:
                if sample.name.endswith('_sum'):
                    agent_type = sample.labels.get('agent_type', 'unknown')
                    execution_sum += sample.value
                    if agent_type not in by_type:
                        by_type[agent_type] = {"invocations": 0, "sum": 0.0, "count": 0}
                    by_type[agent_type]["sum"] += sample.value
                elif sample.name.endswith('_count'):
                    agent_type = sample.labels.get('agent_type', 'unknown')
                    execution_count += int(sample.value)
                    if agent_type not in by_type:
                        by_type[agent_type] = {"invocations": 0, "sum": 0.0, "count": 0}
                    by_type[agent_type]["count"] += int(sample.value)

    avg_execution = (execution_sum / execution_count) if execution_count > 0 else 0

    by_type_list = [
        AgentTypeSummary(
            agent_type=agent_type,
            invocations=data["invocations"],
            avg_execution_time_s=round(data["sum"] / data["count"], 2) if data["count"] > 0 else 0,
        )
        for agent_type, data in by_type.items()
    ]

    return {
        "invocations_total": invocations_total,
        "avg_execution_time_s": round(avg_execution, 2),
        "by_type": by_type_list,
    }


def _get_memory_metrics() -> Dict[str, Any]:
    """Get memory system metrics from Prometheus registry.

    [Source: backend/app/middleware/memory_metrics.py]

    Returns:
        Dict with memory system metrics
    """
    from prometheus_client import REGISTRY

    memory_stats = {
        "graphiti": {"queries_total": 0, "latency_sum": 0.0, "latency_count": 0},
        "temporal": {"queries_total": 0, "latency_sum": 0.0, "latency_count": 0},
        "semantic": {"queries_total": 0, "latency_sum": 0.0, "latency_count": 0},
    }

    for metric in REGISTRY.collect():
        if 'memory' in metric.name.lower() or 'graphiti' in metric.name.lower():
            for sample in metric.samples:
                layer = sample.labels.get('layer', 'unknown')
                if layer in memory_stats:
                    if '_total' in sample.name:
                        memory_stats[layer]["queries_total"] += int(sample.value)
                    elif '_sum' in sample.name:
                        memory_stats[layer]["latency_sum"] += sample.value
                    elif '_count' in sample.name:
                        memory_stats[layer]["latency_count"] += int(sample.value)

    return {
        "graphiti": MemoryLayerSummary(
            queries_total=memory_stats["graphiti"]["queries_total"],
            avg_latency_ms=round(
                memory_stats["graphiti"]["latency_sum"] / memory_stats["graphiti"]["latency_count"] * 1000, 2
            ) if memory_stats["graphiti"]["latency_count"] > 0 else 0,
        ),
        "temporal": MemoryLayerSummary(
            queries_total=memory_stats["temporal"]["queries_total"],
            avg_latency_ms=round(
                memory_stats["temporal"]["latency_sum"] / memory_stats["temporal"]["latency_count"] * 1000, 2
            ) if memory_stats["temporal"]["latency_count"] > 0 else 0,
        ),
        "semantic": MemoryLayerSummary(
            queries_total=memory_stats["semantic"]["queries_total"],
            avg_latency_ms=round(
                memory_stats["semantic"]["latency_sum"] / memory_stats["semantic"]["latency_count"] * 1000, 2
            ) if memory_stats["semantic"]["latency_count"] > 0 else 0,
        ),
    }


def _get_resource_metrics() -> Dict[str, Any]:
    """Get system resource metrics.

    [Source: backend/app/services/resource_monitor.py]

    Returns:
        Dict with resource metrics
    """
    try:
        import psutil

        return {
            "cpu_usage_percent": round(psutil.cpu_percent(interval=None), 1),
            "memory_usage_percent": round(psutil.virtual_memory().percent, 1),
            "disk_usage_percent": round(psutil.disk_usage('/').percent, 1),
        }
    except ImportError:
        logger.warning("monitoring.psutil_not_installed")
        return {
            "cpu_usage_percent": 0.0,
            "memory_usage_percent": 0.0,
            "disk_usage_percent": 0.0,
        }
    except Exception as e:
        logger.error("monitoring.resource_metrics_failed", error=str(e))
        return {
            "cpu_usage_percent": 0.0,
            "memory_usage_percent": 0.0,
            "disk_usage_percent": 0.0,
        }
