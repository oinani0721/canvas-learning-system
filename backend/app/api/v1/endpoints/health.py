# Canvas Learning System - Health Check and Metrics Endpoints
# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: path operation decorators)
# ✅ Verified from Context7:/prometheus/client_python (topic: generate_latest CONTENT_TYPE_LATEST)
"""
Health check and metrics endpoints for the Canvas Learning System API.

This module provides:
- Health check endpoint for monitoring and load balancer health checks
- Prometheus metrics endpoint in text/plain format
- Metrics summary endpoint in JSON format

[Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1health]
[Source: specs/api/canvas-api.openapi.yml:605-642]
[Source: Story 17.2: Deep Monitoring - Agent and Memory System Performance Tracking]
"""

import logging
from datetime import datetime, timezone

# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: APIRouter)
from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse

# ✅ Verified from Context7:/prometheus/client_python (topic: generate_latest REGISTRY)
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.config import Settings, get_settings
from app.middleware.agent_metrics import get_agent_metrics_snapshot
from app.middleware.memory_metrics import get_memory_metrics_snapshot
from app.models.common import (
    AgentMetricsSummary,
    AgentTypeStats,
    HealthCheckResponse,
    MemoryMetricsSummary,
    MemoryTypeStats,
    MetricsSummary,
    ResourceMetricsSummary,
)
from app.services.resource_monitor import get_resource_metrics_snapshot

# Get logger for this module
logger = logging.getLogger(__name__)

# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: APIRouter)
# Pattern: Create router instance with tags for OpenAPI grouping
router = APIRouter()


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="健康检查",
    description="返回应用状态、名称、版本和时间戳",
    operation_id="health_check",
    responses={
        200: {
            "description": "应用健康",
            "model": HealthCheckResponse
        },
        500: {
            "description": "应用异常"
        }
    }
)
async def health_check(
    settings: Settings = Depends(get_settings)
) -> HealthCheckResponse:
    """
    Check application health status.

    Returns application name, version, and current timestamp to indicate
    the service is running and responsive.

    ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: Depends lru_cache settings)
    Pattern: Inject settings using Depends(get_settings)

    [Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1health]

    Args:
        settings: Application settings injected via dependency.

    Returns:
        HealthCheckResponse: Health status with app info and timestamp.

    Example Response:
        {
            "status": "healthy",
            "app_name": "Canvas Learning System API",
            "version": "1.0.0",
            "timestamp": "2025-11-24T10:30:00Z"
        }
    """
    logger.debug("Health check requested")

    return HealthCheckResponse(
        status="healthy",
        app_name=settings.PROJECT_NAME,
        version=settings.VERSION,
        timestamp=datetime.now(timezone.utc)
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Metrics Endpoints (Story 17.2)
# [Source: specs/api/canvas-api.openapi.yml:605-642]
# ═══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/health/metrics",
    summary="Prometheus指标",
    description="返回Prometheus格式的监控指标",
    operation_id="get_prometheus_metrics",
    response_class=PlainTextResponse,
    responses={
        200: {
            "description": "Prometheus格式指标",
            "content": {
                "text/plain": {
                    "example": "# HELP canvas_agent_execution_seconds Agent execution time\n# TYPE canvas_agent_execution_seconds histogram\n"
                }
            }
        }
    }
)
async def get_metrics() -> PlainTextResponse:
    """
    Get Prometheus-format metrics.

    Returns all registered Prometheus metrics in the standard text exposition format.
    This endpoint is designed to be scraped by Prometheus.

    ✅ Verified from Context7:/prometheus/client_python (topic: generate_latest REGISTRY)

    [Source: specs/api/canvas-api.openapi.yml:605-628]
    [Source: Story 17.2 AC-5]

    Returns:
        PlainTextResponse: Prometheus metrics in text/plain format

    Metrics included:
        - canvas_agent_execution_seconds (Histogram): Agent execution time
        - canvas_agent_errors_total (Counter): Agent execution errors
        - canvas_agent_invocations_total (Counter): Agent invocation count
        - canvas_memory_query_seconds (Histogram): Memory system query latency
        - canvas_memory_errors_total (Counter): Memory system errors
        - canvas_memory_queries_total (Counter): Memory query count
        - canvas_resource_cpu_percent (Gauge): CPU usage percentage
        - canvas_resource_memory_percent (Gauge): Memory usage percentage
        - canvas_resource_disk_percent (Gauge): Disk usage percentage
    """
    logger.debug("Prometheus metrics requested")

    # ✅ Verified from Context7:/prometheus/client_python (generate_latest returns bytes)
    metrics_output = generate_latest()

    return PlainTextResponse(
        content=metrics_output.decode("utf-8"),
        media_type=CONTENT_TYPE_LATEST
    )


@router.get(
    "/health/metrics/summary",
    response_model=MetricsSummary,
    summary="指标摘要",
    description="返回JSON格式的监控指标摘要，包含Agent、记忆系统和资源使用统计",
    operation_id="get_metrics_summary",
    responses={
        200: {
            "description": "指标摘要",
            "model": MetricsSummary
        }
    }
)
async def get_metrics_summary() -> MetricsSummary:
    """
    Get metrics summary in JSON format.

    Returns aggregated metrics for agents, memory systems, and system resources
    in a structured JSON format suitable for dashboards and monitoring UIs.

    [Source: specs/api/canvas-api.openapi.yml:630-642]
    [Source: Story 17.2 AC-6]

    Returns:
        MetricsSummary: Aggregated metrics summary

    Summary includes:
        - agents: Agent execution statistics (by type, avg time, error rates)
        - memory_system: Memory query statistics (graphiti, lancedb, temporal)
        - resources: System resource usage (CPU, memory, disk)
    """
    logger.debug("Metrics summary requested")

    # Get agent metrics snapshot
    agent_snapshot = get_agent_metrics_snapshot()

    # Convert by_type to proper AgentTypeStats models
    agent_by_type = {}
    for agent_type, stats in agent_snapshot.get("by_type", {}).items():
        agent_by_type[agent_type] = AgentTypeStats(
            count=stats.get("count", 0),
            success_count=stats.get("success_count", 0),
            error_count=stats.get("error_count", 0),
            avg_time_s=stats.get("avg_time_s", 0.0)
        )

    agents_summary = AgentMetricsSummary(
        invocations_total=agent_snapshot.get("invocations_total", 0),
        avg_execution_time_s=agent_snapshot.get("avg_execution_time_s", 0.0),
        by_type=agent_by_type
    )

    # Get memory metrics snapshot
    memory_snapshot = get_memory_metrics_snapshot()

    # Convert by_type to proper MemoryTypeStats models
    memory_by_type = {}
    for memory_type, stats in memory_snapshot.get("by_type", {}).items():
        memory_by_type[memory_type] = MemoryTypeStats(
            query_count=stats.get("query_count", 0),
            success_count=stats.get("success_count", 0),
            error_count=stats.get("error_count", 0),
            avg_latency_s=stats.get("avg_latency_s", 0.0),
            by_operation=stats.get("by_operation", {})
        )

    memory_summary = MemoryMetricsSummary(
        queries_total=memory_snapshot.get("queries_total", 0),
        avg_latency_s=memory_snapshot.get("avg_latency_s", 0.0),
        by_type=memory_by_type
    )

    # Get resource metrics snapshot
    resource_snapshot = get_resource_metrics_snapshot()

    # Extract resource metrics from the nested structure
    cpu_metrics = resource_snapshot.get("cpu", {})
    memory_metrics = resource_snapshot.get("memory", {})
    disk_metrics = resource_snapshot.get("disk", {})

    # Get first disk mount point metrics (usually "/" or "C:\\")
    first_disk_key = next(iter(disk_metrics.keys()), None)
    disk_data = disk_metrics.get(first_disk_key, {}) if first_disk_key else {}

    resources_summary = ResourceMetricsSummary(
        cpu_usage_percent=cpu_metrics.get("percent", 0.0),
        memory_usage_percent=memory_metrics.get("percent", 0.0),
        memory_available_bytes=memory_metrics.get("available_bytes", 0),
        memory_total_bytes=memory_metrics.get("total_bytes", 0),
        disk_usage_percent=disk_data.get("percent", 0.0),
        disk_free_bytes=disk_data.get("free_bytes", 0)
    )

    return MetricsSummary(
        agents=agents_summary,
        memory_system=memory_summary,
        resources=resources_summary,
        timestamp=datetime.now(timezone.utc)
    )
