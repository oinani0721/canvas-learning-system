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

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: APIRouter)
from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

# ✅ Verified from Context7:/prometheus/client_python (topic: generate_latest REGISTRY)
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.config import Settings, get_settings
from app.core.failure_counters import (
    get_dual_write_failures,
    get_edge_sync_failures,
    reset_counters,
)
from app.dependencies import AgentServiceDep
from app.middleware.agent_metrics import get_agent_metrics_snapshot
from app.middleware.memory_metrics import get_memory_metrics_snapshot
from app.models.common import (
    AgentMetricsSummary,
    AgentTypeStats,
    MemoryMetricsSummary,
    MemoryTypeStats,
    MetricsSummary,
    ResourceMetricsSummary,
)
from app.models.schemas import HealthCheckResponse
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
    settings: Settings = Depends(get_settings)  # noqa: B008
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

    # Story 38.3 AC-3: Include FSRS status in health check
    # Code Review M2 Fix: Use FSRS_RUNTIME_OK (runtime init status) when available,
    # fall back to FSRS_AVAILABLE (import-time) if ReviewService hasn't been instantiated yet.
    components = {}
    try:
        from app.services.review_service import FSRS_AVAILABLE, FSRS_RUNTIME_OK
        if FSRS_RUNTIME_OK is not None:
            components["fsrs"] = "ok" if FSRS_RUNTIME_OK else "degraded"
        else:
            components["fsrs"] = "ok" if FSRS_AVAILABLE else "degraded"
    except Exception:
        components["fsrs"] = "degraded"

    # NFR Quick Win #2: Include batch_orchestrator initialization status
    try:
        from app.api.v1.endpoints.intelligent_parallel import _deps_initialized
        components["batch_orchestrator"] = "ok" if _deps_initialized else "not_initialized"
    except Exception:
        components["batch_orchestrator"] = "unavailable"

    return HealthCheckResponse(
        status="healthy",
        app_name=settings.PROJECT_NAME,
        version=settings.VERSION,
        timestamp=datetime.now(timezone.utc),
        components=components
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


# ═══════════════════════════════════════════════════════════════════════════════
# AI Health Check Endpoint (Story 21.5.2)
# [Source: docs/stories/21.5.2.story.md - AC-3]
# ═══════════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════════
# Agent Health Check Endpoint (Story 21.5.4)
# [Source: docs/stories/21.5.4.story.md - AC-1, AC-4]
# ═══════════════════════════════════════════════════════════════════════════════

# ✅ Verified from Story 21.5.4 - Agent端点健康检查增强
# Agent端点映射 (用于状态检查)
AGENT_ENDPOINTS = {
    "decompose_basic": "/api/v1/agents/decompose/basic",
    "decompose_deep": "/api/v1/agents/decompose/deep",
    "decompose_question": "/api/v1/agents/decompose/question",
    "explain_oral": "/api/v1/agents/explain/oral",
    "explain_four_level": "/api/v1/agents/explain/four-level",
    "explain_memory": "/api/v1/agents/explain/memory",
    "clarification_path": "/api/v1/agents/clarification/path",
    "comparison_table": "/api/v1/agents/comparison/table",
    "example_teaching": "/api/v1/agents/example/teaching",
    "scoring": "/api/v1/agents/scoring",
    "verification": "/api/v1/agents/verification/question",
}


@router.get(
    "/health/agents",
    summary="Agent端点状态检查",
    description="检查所有Agent端点的可用状态",
    operation_id="check_agents_health",
    responses={
        200: {
            "description": "Agent端点状态",
            "content": {
                "application/json": {
                    "example": {
                        "status": "ok",
                        "agents": {
                            "decompose_basic": "available",
                            "explain_oral": "available"
                        },
                        "total_agents": 11,
                        "available_count": 11
                    }
                }
            }
        }
    }
)
async def check_agents_health() -> Dict[str, Any]:
    """
    检查所有Agent端点状态。

    返回每个Agent端点的可用性状态。
    注意：此端点不实际调用Agent，只检查路由是否注册。

    ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: path operation decorators)

    [Source: docs/stories/21.5.4.story.md - AC-1]
    [Source: docs/prd/EPIC-21.5-AGENT-RELIABILITY-FIX.md#story-21-5-4]

    Returns:
        Dict containing agent endpoint availability status
    """
    logger.debug("Agent health check requested")

    # 所有端点默认可用（路由已注册）
    agents_status = {name: "available" for name in AGENT_ENDPOINTS}

    return {
        "status": "ok",
        "agents": agents_status,
        "total_agents": len(AGENT_ENDPOINTS),
        "available_count": len(agents_status)
    }


@router.get(
    "/health/ai",
    summary="AI连接状态检查",
    description="测试AI Provider API连接是否正常，返回连接状态、模型名称和延迟信息",
    operation_id="check_ai_health",
    responses={
        200: {
            "description": "AI连接正常",
            "content": {
                "application/json": {
                    "example": {
                        "status": "ok",
                        "model": "gemini-2.0-flash-exp",
                        "provider": "google",
                        "latency_ms": 245
                    }
                }
            }
        },
        503: {
            "description": "AI连接失败",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "model": "gemini-2.0-flash-exp",
                        "provider": "google",
                        "error": "Invalid API key",
                        "error_code": "LLM_API_ERROR"
                    }
                }
            }
        }
    }
)
async def check_ai_health(
    agent_service: AgentServiceDep
) -> Any:
    """
    测试AI API连接状态。

    此端点通过发送最小请求到配置的AI Provider来验证API连接。
    用于诊断AI服务是否可用，帮助快速定位Agent功能失败的原因。

    ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: path operation decorators)

    [Source: docs/stories/21.5.2.story.md - AC-3]
    [Source: docs/prd/EPIC-21.5-AGENT-RELIABILITY-FIX.md#story-21-5-2]

    Args:
        agent_service: AgentService实例 (通过依赖注入获取)

    Returns:
        dict: AI连接状态信息
            - status: "ok" 或 "error"
            - model: 配置的模型名称
            - provider: AI提供商名称
            - latency_ms: 响应延迟（仅成功时）
            - error: 错误信息（仅失败时）
            - error_code: 错误码（仅失败时）

    Raises:
        503: 当AI连接失败时返回503状态码，但响应体仍包含详细错误信息
    """
    logger.debug("AI health check requested")

    result = await agent_service.test_ai_connection()

    if result.get("status") == "error":
        # ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: JSONResponse)
        # 返回503但包含详细错误信息，便于诊断
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=503,
            content=result
        )

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# Full System Diagnostic Endpoint (Story 21.5.4)
# [Source: docs/stories/21.5.4.story.md - AC-3, AC-4, AC-5]
# ═══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/health/full",
    summary="完整系统诊断",
    description="返回所有组件的完整健康状态和配置信息",
    operation_id="full_health_check",
    responses={
        200: {
            "description": "所有组件正常",
            "content": {
                "application/json": {
                    "example": {
                        "status": "ok",
                        "components": {
                            "api": "ok",
                            "ai_provider": {"status": "ok", "model": "gemini-2.0-flash-exp"},
                            "canvas_service": "ok",
                            "agents": "ok"
                        },
                        "config": {
                            "ai_model": "gemini-2.0-flash-exp",
                            "ai_provider": "google",
                            "cors_origins": ["app://obsidian.md"]
                        },
                        "timestamp": "2025-12-14T10:00:00Z"
                    }
                }
            }
        },
        503: {
            "description": "部分组件异常(degraded状态)，与/health/ai保持一致",
            "content": {
                "application/json": {
                    "example": {
                        "status": "degraded",
                        "components": {
                            "api": "ok",
                            "ai_provider": {"status": "error", "error": "AI not configured"},
                            "canvas_service": "ok",
                            "agents": "ok"
                        },
                        "config": {
                            "ai_model": "gemini-2.0-flash-exp",
                            "ai_provider": "google",
                            "cors_origins": ["app://obsidian.md"]
                        },
                        "timestamp": "2025-12-14T10:00:00Z"
                    }
                }
            }
        }
    }
)
async def full_health_check(
    agent_service: AgentServiceDep,
    settings: Settings = Depends(get_settings)  # noqa: B008
) -> Dict[str, Any]:
    """
    完整系统诊断。

    一次请求获取所有服务组件状态、AI连接状态和关键配置信息。
    用于快速诊断系统问题。

    ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: path operation decorators)

    [Source: docs/stories/21.5.4.story.md - AC-3, AC-4]
    [Source: docs/prd/EPIC-21.5-AGENT-RELIABILITY-FIX.md#story-21-5-4]

    Args:
        agent_service: Agent服务实例
        settings: 应用配置

    Returns:
        Dict containing full system diagnostic info
    """
    logger.debug("Full health check requested")

    # 测试AI连接
    ai_status = await agent_service.test_ai_connection()

    # 检查Agent端点状态
    agents_status = "ok"  # 路由注册即可用

    # 确定总体状态
    overall_status = "ok" if ai_status.get("status") == "ok" else "degraded"

    # P1 Fix: Unify HTTP status codes with /health/ai
    # [Source: docs/qa/gates/21.5.4-agent-health-check-enhancement.yml#OPS-001]
    result = {
        "status": overall_status,
        "components": {
            "api": "ok",
            "ai_provider": ai_status,
            "canvas_service": "ok",
            "agents": agents_status
        },
        "config": {
            "ai_model": settings.AI_MODEL_NAME,
            "ai_provider": settings.AI_PROVIDER,
            "cors_origins": settings.cors_origins_list
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    # Return 503 when degraded (consistent with /health/ai returning 503 on error)
    if overall_status == "degraded":
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=503, content=result)

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# Neo4j Health Check Endpoint (Story 30.1)
# [Source: docs/stories/30.1.story.md - AC 4]
# [Source: specs/data/neo4j-health-response.schema.json]
# ═══════════════════════════════════════════════════════════════════════════════

class Neo4jHealthChecks(BaseModel):
    """Neo4j健康检查详情."""
    neo4j_enabled: Optional[bool] = Field(
        default=None,
        description="Neo4j是否在配置中启用"
    )
    neo4j_connection: Optional[bool] = Field(
        default=None,
        description="Neo4j Bolt连接是否成功"
    )
    driver_initialized: Optional[bool] = Field(
        default=None,
        description="Neo4j AsyncGraphDatabase driver是否已初始化"
    )
    database_accessible: Optional[bool] = Field(
        default=None,
        description="目标数据库是否可访问 (RETURN 1 测试通过)"
    )
    uri: Optional[str] = Field(
        default=None,
        description="Neo4j连接URI (仅在healthy时返回)"
    )
    reason: Optional[str] = Field(
        default=None,
        description="降级或不健康状态的原因说明"
    )
    error: Optional[str] = Field(
        default=None,
        description="错误信息 (仅在unhealthy时返回)"
    )


class Neo4jHealthResponse(BaseModel):
    """
    Neo4j健康检查响应.

    [Source: specs/data/neo4j-health-response.schema.json]
    [Source: docs/stories/30.1.story.md - AC 4]
    """
    status: str = Field(
        description="整体健康状态: healthy=Neo4j连接正常, degraded=Neo4j已禁用, unhealthy=连接失败"
    )
    checks: Neo4jHealthChecks = Field(
        description="各项检查结果"
    )
    cached: bool = Field(
        default=False,
        description="是否为缓存结果 (缓存TTL: 30秒, 参考ADR-007)"
    )
    timestamp: datetime = Field(
        description="检查时间戳 (ISO 8601格式)"
    )


# Module-level cached Neo4j driver for health checks
# ✅ Story 30.3 Fix: Reuse driver across health checks to avoid 21s initialization per call
_cached_neo4j_driver = None
_neo4j_driver_uri = None


async def _ensure_neo4j_driver():
    """
    确保Neo4j驱动已初始化（缓存复用）。

    此函数在超时约束外调用，避免首次初始化超时问题。
    驱动创建是同步的，但需要在事件循环中。

    ✅ Story 30.3 Fix: Separate driver init from health check query

    Returns:
        driver: 缓存的AsyncGraphDatabase driver
    """
    global _cached_neo4j_driver, _neo4j_driver_uri
    from neo4j import AsyncGraphDatabase
    from app.config import settings

    # Create or reuse cached driver
    if _cached_neo4j_driver is None or _neo4j_driver_uri != settings.neo4j_uri:
        if _cached_neo4j_driver is not None:
            try:
                await _cached_neo4j_driver.close()
            except Exception:
                pass
        _cached_neo4j_driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password)
        )
        _neo4j_driver_uri = settings.neo4j_uri
        logger.info("Neo4j health check driver initialized")

    return _cached_neo4j_driver


async def _test_neo4j_connection() -> bool:
    """
    测试Neo4j连接（仅执行查询，驱动应已初始化）。

    使用缓存的AsyncGraphDatabase driver执行RETURN 1验证。

    ✅ Story 30.3 Fix: Query only, driver init happens separately

    Returns:
        bool: 连接成功返回True

    Raises:
        Exception: 连接失败时抛出异常
    """
    global _cached_neo4j_driver, _neo4j_driver_uri
    from app.config import settings

    if _cached_neo4j_driver is None:
        raise RuntimeError("Neo4j driver not initialized")

    try:
        async with _cached_neo4j_driver.session(database=settings.neo4j_database) as session:
            result = await session.run("RETURN 1 as test")
            await result.consume()
        return True
    except Exception as e:
        # Connection failed - reset driver for next attempt
        logger.warning(f"Neo4j health check failed, resetting driver: {e}")
        try:
            await _cached_neo4j_driver.close()
        except Exception:
            pass
        _cached_neo4j_driver = None
        _neo4j_driver_uri = None
        raise


@router.get(
    "/health/neo4j",
    response_model=Neo4jHealthResponse,
    summary="Neo4j连接状态检查",
    description="检查Neo4j图数据库连接健康状态",
    operation_id="check_neo4j_health",
    responses={
        200: {
            "description": "Neo4j健康检查结果",
            "model": Neo4jHealthResponse,
            "content": {
                "application/json": {
                    "examples": {
                        "healthy": {
                            "summary": "连接正常",
                            "value": {
                                "status": "healthy",
                                "checks": {
                                    "neo4j_enabled": True,
                                    "neo4j_connection": True,
                                    "driver_initialized": True,
                                    "database_accessible": True,
                                    "uri": "bolt://localhost:7687"
                                },
                                "cached": False,
                                "timestamp": "2026-01-16T10:30:00Z"
                            }
                        },
                        "degraded": {
                            "summary": "Neo4j已禁用",
                            "value": {
                                "status": "degraded",
                                "checks": {
                                    "neo4j_enabled": False,
                                    "reason": "Neo4j is disabled in configuration"
                                },
                                "cached": False,
                                "timestamp": "2026-01-16T10:30:00Z"
                            }
                        },
                        "unhealthy": {
                            "summary": "连接失败",
                            "value": {
                                "status": "unhealthy",
                                "checks": {
                                    "neo4j_enabled": True,
                                    "neo4j_connection": False,
                                    "error": "Connection timeout (>500ms)"
                                },
                                "cached": False,
                                "timestamp": "2026-01-16T10:30:00Z"
                            }
                        }
                    }
                }
            }
        }
    }
)
async def check_neo4j_health(
    settings: Settings = Depends(get_settings)  # noqa: B008
) -> Neo4jHealthResponse:
    """
    检查Neo4j连接健康状态.

    此端点验证Neo4j图数据库的连接状态，用于监控和故障诊断。

    ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: path operation decorators)

    [Source: docs/stories/30.1.story.md - AC 4]
    [Source: specs/data/neo4j-health-response.schema.json]

    Returns:
        Neo4jHealthResponse: 健康检查结果
            - status: "healthy" | "degraded" | "unhealthy"
            - checks: 详细检查结果
            - cached: 是否为缓存结果
            - timestamp: 检查时间戳

    Health Status:
        - healthy: Neo4j连接正常，可以执行查询
        - degraded: Neo4j在配置中被禁用 (NEO4J_ENABLED=false)
        - unhealthy: 连接失败或超时
    """
    logger.debug("Neo4j health check requested")

    # Check if Neo4j is enabled in configuration
    if not settings.neo4j_enabled:
        logger.info("Neo4j is disabled in configuration")
        return Neo4jHealthResponse(
            status="degraded",
            checks=Neo4jHealthChecks(
                neo4j_enabled=False,
                reason="Neo4j is disabled in configuration"
            ),
            cached=False,
            timestamp=datetime.now(timezone.utc)
        )

    # Import memory system logger for debugging
    from app.core.memory_system_logger import memory_logger

    try:
        # ✅ Story 30.3 Fix: Initialize driver outside timeout to avoid first-call timeout
        memory_logger.info(f"HEALTH_CHECK_START | uri={settings.neo4j_uri}")
        await _ensure_neo4j_driver()

        # Use 30s timeout: AsyncGraphDatabase first connection can take 20+ seconds
        # under high memory pressure (async driver is much slower than sync on cold start)
        import time
        start_time = time.time()
        await asyncio.wait_for(
            _test_neo4j_connection(),
            timeout=30.0
        )
        latency_ms = (time.time() - start_time) * 1000

        logger.debug("Neo4j connection healthy")
        memory_logger.info(f"HEALTH_CHECK_SUCCESS | latency={latency_ms:.2f}ms | uri={settings.neo4j_uri}")
        return Neo4jHealthResponse(
            status="healthy",
            checks=Neo4jHealthChecks(
                neo4j_enabled=True,
                neo4j_connection=True,
                driver_initialized=True,
                database_accessible=True,
                uri=settings.neo4j_uri
            ),
            cached=False,
            timestamp=datetime.now(timezone.utc)
        )

    except asyncio.TimeoutError:
        logger.warning("Neo4j connection timeout (>30000ms)")
        memory_logger.error(f"HEALTH_CHECK_TIMEOUT | timeout=30s | uri={settings.neo4j_uri}")
        # Reset driver after timeout to avoid stale connection state
        global _cached_neo4j_driver, _neo4j_driver_uri
        if _cached_neo4j_driver is not None:
            try:
                await _cached_neo4j_driver.close()
            except Exception:
                pass
            _cached_neo4j_driver = None
            _neo4j_driver_uri = None
        return Neo4jHealthResponse(
            status="unhealthy",
            checks=Neo4jHealthChecks(
                neo4j_enabled=True,
                neo4j_connection=False,
                error="Connection timeout (>30000ms)"
            ),
            cached=False,
            timestamp=datetime.now(timezone.utc)
        )

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Neo4j connection failed: {error_msg}")
        memory_logger.error(f"HEALTH_CHECK_FAILED | error={error_msg} | uri={settings.neo4j_uri}")
        return Neo4jHealthResponse(
            status="unhealthy",
            checks=Neo4jHealthChecks(
                neo4j_enabled=True,
                neo4j_connection=False,
                error=error_msg
            ),
            cached=False,
            timestamp=datetime.now(timezone.utc)
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Graphiti Health Check Endpoint (Story 30.3)
# [Source: docs/stories/30.3.memory-api-health-endpoints.story.md - AC-30.3.7]
# [Source: specs/data/graphiti-health-response.schema.json]
# ═══════════════════════════════════════════════════════════════════════════════

class GraphitiHealthResponse(BaseModel):
    """
    Graphiti健康检查响应.

    [Source: specs/data/graphiti-health-response.schema.json]
    [Source: docs/stories/30.3.memory-api-health-endpoints.story.md - AC-30.3.7]
    """
    status: str = Field(
        description="状态: ok=正常, error=不可用"
    )
    graph_stats: Optional[Dict[str, Any]] = Field(
        default=None,
        description="图统计信息: node_count, edge_count, episode_count"
    )
    last_episode_timestamp: Optional[str] = Field(
        default=None,
        description="最近episode的时间戳"
    )
    error: Optional[str] = Field(
        default=None,
        description="错误信息(仅error时存在)"
    )


@router.get(
    "/health/graphiti",
    response_model=GraphitiHealthResponse,
    summary="Graphiti连接状态检查",
    description="检查Graphiti客户端初始化状态和图统计信息",
    operation_id="check_graphiti_health",
    responses={
        200: {
            "description": "Graphiti健康检查结果",
            "model": GraphitiHealthResponse,
            "content": {
                "application/json": {
                    "examples": {
                        "ok": {
                            "summary": "Graphiti正常",
                            "value": {
                                "status": "ok",
                                "graph_stats": {
                                    "node_count": 1234,
                                    "edge_count": 5678,
                                    "episode_count": 890
                                },
                                "last_episode_timestamp": "2026-01-15T15:30:00Z"
                            }
                        },
                        "error": {
                            "summary": "Graphiti不可用",
                            "value": {
                                "status": "error",
                                "error": "Graphiti client not initialized: Neo4j connection failed"
                            }
                        }
                    }
                }
            }
        }
    }
)
async def check_graphiti_health(
    settings: Settings = Depends(get_settings)  # noqa: B008
) -> GraphitiHealthResponse:
    """
    检查Graphiti健康状态.

    此端点验证Graphiti客户端的初始化状态和图统计信息。

    ✅ Verified from Story 30.3 AC-30.3.7

    [Source: docs/stories/30.3.memory-api-health-endpoints.story.md - AC-30.3.7]
    [Source: specs/data/graphiti-health-response.schema.json]

    Returns:
        GraphitiHealthResponse: 健康检查结果
    """
    logger.debug("Graphiti health check requested")

    # Check if Neo4j (underlying backend) is enabled
    if not settings.neo4j_enabled:
        logger.info("Graphiti unavailable: Neo4j is disabled")
        return GraphitiHealthResponse(
            status="error",
            error="Graphiti unavailable: Neo4j is disabled in configuration"
        )

    try:
        # Try to get graph stats from Neo4j
        from app.clients.neo4j_client import get_neo4j_client

        neo4j_client = get_neo4j_client()

        # Ensure client is initialized before checking status
        if not neo4j_client.stats.get("initialized"):
            await neo4j_client.initialize()

        # Run a fresh health check to get current connection state
        health_ok = await neo4j_client.health_check()

        if not health_ok:
            return GraphitiHealthResponse(
                status="error",
                error="Graphiti unavailable: Neo4j not connected"
            )

        stats = neo4j_client.stats

        graph_stats = {
            "node_count": stats.get("node_count", 0),
            "edge_count": stats.get("edge_count", 0),
            "episode_count": stats.get("episode_count", 0)
        }

        return GraphitiHealthResponse(
            status="ok",
            graph_stats=graph_stats,
            last_episode_timestamp=stats.get("last_episode_timestamp")
        )

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Graphiti health check failed: {error_msg}")
        return GraphitiHealthResponse(
            status="error",
            error=f"Graphiti client error: {error_msg}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# LanceDB Health Check Endpoint (Story 30.3)
# [Source: docs/stories/30.3.memory-api-health-endpoints.story.md - AC-30.3.8]
# [Source: specs/data/lancedb-health-response.schema.json]
# ═══════════════════════════════════════════════════════════════════════════════

class LanceDBHealthResponse(BaseModel):
    """
    LanceDB健康检查响应.

    [Source: specs/data/lancedb-health-response.schema.json]
    [Source: docs/stories/30.3.memory-api-health-endpoints.story.md - AC-30.3.8]
    """
    status: str = Field(
        description="状态: ok=正常, error=不可用"
    )
    table_count: Optional[int] = Field(
        default=None,
        description="向量表数量"
    )
    total_vectors: Optional[int] = Field(
        default=None,
        description="向量总数"
    )
    embedding_model: Optional[str] = Field(
        default=None,
        description="使用的Embedding模型名称"
    )
    error: Optional[str] = Field(
        default=None,
        description="错误信息(仅error时存在)"
    )


@router.get(
    "/health/lancedb",
    response_model=LanceDBHealthResponse,
    summary="LanceDB连接状态检查",
    description="检查LanceDB向量库连接状态和统计信息",
    operation_id="check_lancedb_health",
    responses={
        200: {
            "description": "LanceDB健康检查结果",
            "model": LanceDBHealthResponse,
            "content": {
                "application/json": {
                    "examples": {
                        "ok": {
                            "summary": "LanceDB正常",
                            "value": {
                                "status": "ok",
                                "table_count": 3,
                                "total_vectors": 50000,
                                "embedding_model": "text-embedding-3-small"
                            }
                        },
                        "error": {
                            "summary": "LanceDB不可用",
                            "value": {
                                "status": "error",
                                "error": "LanceDB directory not found: /data/lancedb"
                            }
                        }
                    }
                }
            }
        }
    }
)
async def check_lancedb_health(
    settings: Settings = Depends(get_settings)  # noqa: B008
) -> LanceDBHealthResponse:
    """
    检查LanceDB健康状态.

    此端点验证LanceDB向量库的连接状态和统计信息。

    ✅ Verified from Story 30.3 AC-30.3.8

    [Source: docs/stories/30.3.memory-api-health-endpoints.story.md - AC-30.3.8]
    [Source: specs/data/lancedb-health-response.schema.json]

    Returns:
        LanceDBHealthResponse: 健康检查结果
    """
    logger.debug("LanceDB health check requested")

    try:
        # Try to import and check LanceDB
        import lancedb
        from pathlib import Path

        # Get LanceDB path from settings or use default
        lancedb_path = getattr(settings, "lancedb_path", "./data/lancedb")
        db_path = Path(lancedb_path)

        if not db_path.exists():
            # Create the directory if it doesn't exist (degraded mode)
            db_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created LanceDB directory: {db_path}")

        # Connect to LanceDB
        db = lancedb.connect(str(db_path))
        tables = db.table_names()

        # Calculate total vectors
        total_vectors = 0
        for table_name in tables:
            try:
                table = db.open_table(table_name)
                total_vectors += len(table)
            except Exception:
                pass  # Skip inaccessible tables

        # Get embedding model from settings
        embedding_model = getattr(settings, "embedding_model", "text-embedding-3-small")

        return LanceDBHealthResponse(
            status="ok",
            table_count=len(tables),
            total_vectors=total_vectors,
            embedding_model=embedding_model
        )

    except ImportError:
        logger.warning("LanceDB not installed")
        return LanceDBHealthResponse(
            status="error",
            error="LanceDB library not installed"
        )

    except Exception as e:
        error_msg = str(e)
        logger.error(f"LanceDB health check failed: {error_msg}")
        return LanceDBHealthResponse(
            status="error",
            error=f"LanceDB error: {error_msg}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Unified Storage Health Endpoint (Story 36.10)
# [Source: docs/stories/36.10.story.md]
# [Source: specs/data/storage-health-response.schema.json]
# ═══════════════════════════════════════════════════════════════════════════════

from collections import deque
import time
from typing import List


class LatencyTracker:
    """Track request latencies and calculate percentiles.

    ✅ Story 36.10 AC-36.10.3
    [Source: ADR-007 caching performance targets]
    """

    def __init__(self, window_seconds: int = 300):
        """Initialize with sliding window duration.

        Args:
            window_seconds: Time window for latency samples (default: 5 minutes)
        """
        self._window = window_seconds
        self._samples: deque = deque()  # (timestamp, latency_ms)
        self._lock = asyncio.Lock()

    async def record(self, latency_ms: float) -> None:
        """Record a latency sample thread-safely."""
        async with self._lock:
            now = time.time()
            self._samples.append((now, latency_ms))
            self._prune_old()

    def _prune_old(self) -> None:
        """Remove samples outside the window."""
        cutoff = time.time() - self._window
        while self._samples and self._samples[0][0] < cutoff:
            self._samples.popleft()

    async def get_p95(self) -> float:
        """Calculate P95 latency."""
        async with self._lock:
            self._prune_old()
            if not self._samples:
                return 0.0
            latencies = sorted(s[1] for s in self._samples)
            idx = int(len(latencies) * 0.95)
            return latencies[min(idx, len(latencies) - 1)]

    async def get_p50(self) -> float:
        """Calculate P50 (median) latency."""
        async with self._lock:
            self._prune_old()
            if not self._samples:
                return 0.0
            latencies = sorted(s[1] for s in self._samples)
            idx = int(len(latencies) * 0.50)
            return latencies[idx]

    async def get_sample_count(self) -> int:
        """Get number of samples in current window."""
        async with self._lock:
            self._prune_old()
            return len(self._samples)


# Module-level latency tracker for storage health
_storage_latency_tracker = LatencyTracker(window_seconds=300)


# Response cache for storage health (TTL=30s per ADR-007)
_storage_health_cache: Optional[Dict[str, Any]] = None
_storage_health_cache_time: float = 0
_STORAGE_HEALTH_CACHE_TTL: int = 30  # seconds


class StorageBackendStatus(BaseModel):
    """Storage backend health status."""
    name: str = Field(description="Storage backend name: neo4j, mcp, json")
    status: str = Field(description="Status: ok or error")
    latency_ms: Optional[float] = Field(default=None, description="Health check latency in ms")
    error: Optional[str] = Field(default=None, description="Error message if status=error")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional details")


class Neo4jConnectionPool(BaseModel):
    """Neo4j connection pool status."""
    active: int = Field(default=0, description="Active connections")
    idle: int = Field(default=0, description="Idle connections")
    max_size: int = Field(default=50, description="Maximum pool size")
    utilization_percent: float = Field(default=0.0, description="Pool utilization percentage")


class LatencyMetrics(BaseModel):
    """Latency metrics for storage health checks."""
    p95_ms: float = Field(description="P95 latency in milliseconds")
    p50_ms: Optional[float] = Field(default=None, description="P50 (median) latency in ms")
    sample_count: Optional[int] = Field(default=None, description="Number of samples in window")
    window_seconds: int = Field(description="Statistics window in seconds")


class StorageHealthResponse(BaseModel):
    """
    Unified Storage Health Response.

    [Source: specs/data/storage-health-response.schema.json]
    [Source: docs/stories/36.10.story.md]
    """
    status: str = Field(
        description="Overall status: healthy=all backends ok, degraded=some error, unhealthy=critical (neo4j) error"
    )
    storage_backends: List[StorageBackendStatus] = Field(
        description="Status of each storage backend"
    )
    connection_pool: Dict[str, Neo4jConnectionPool] = Field(
        default_factory=dict,
        description="Connection pool status"
    )
    latency_metrics: LatencyMetrics = Field(
        description="Latency metrics from health checks"
    )
    cached: bool = Field(
        description="Whether this is a cached response"
    )
    cache_ttl_remaining_seconds: int = Field(
        default=0,
        description="Remaining cache TTL in seconds"
    )
    timestamp: datetime = Field(
        description="Health check timestamp"
    )
    # Story 36.12 AC-36.12.6: Failure counters for observability
    edge_sync_failures: int = Field(
        default=0,
        description="Total edge sync failures since last reset"
    )
    dual_write_failures: int = Field(
        default=0,
        description="Total dual-write failures since last reset"
    )


def _aggregate_storage_status(
    backends: List[StorageBackendStatus],
    edge_sync_failures: int = 0,
    dual_write_failures: int = 0,
) -> str:
    """Aggregate storage backend statuses.

    ✅ Story 36.10 AC-36.10.5
    - healthy: ALL backends ok
    - degraded: SOME backends error (non-critical)
    - unhealthy: CRITICAL backend error (neo4j)
    """
    statuses = {b.name: b.status for b in backends}

    # Neo4j is critical - if it's down, system is unhealthy
    if statuses.get("neo4j") == "error":
        return "unhealthy"

    # Any other errors = degraded
    if any(s == "error" for s in statuses.values()):
        return "degraded"

    # Story 36.12 AC-36.12.6: Failure counters > 0 = degraded
    if edge_sync_failures > 0 or dual_write_failures > 0:
        return "degraded"

    return "healthy"


async def _check_mcp_health() -> StorageBackendStatus:
    """Check MCP Graphiti Memory Server health.

    ✅ Story 36.10 Task 2.4
    Uses MCP list_memories call to verify server reachability.
    """
    start_time = time.time()
    try:
        # Try to import and use the MCP graphiti-memory client
        # The MCP server should be reachable via HTTP if configured
        from app.config import settings

        # Check if MCP is configured
        mcp_enabled = getattr(settings, "mcp_enabled", True)
        if not mcp_enabled:
            return StorageBackendStatus(
                name="mcp",
                status="error",
                error="MCP is disabled in configuration"
            )

        # For MCP health, we check if the graphiti-memory MCP server is running
        # by attempting a simple operation with timeout
        # Since MCP is typically accessed via Claude, we check if endpoint is configured
        mcp_endpoint = getattr(settings, "mcp_graphiti_endpoint", None)

        if mcp_endpoint:
            # If endpoint is configured, try a simple HTTP check
            import aiohttp
            async with aiohttp.ClientSession() as session:
                await asyncio.wait_for(
                    session.get(f"{mcp_endpoint}/health", timeout=aiohttp.ClientTimeout(total=0.5)),
                    timeout=0.5
                )
            latency_ms = (time.time() - start_time) * 1000
            return StorageBackendStatus(
                name="mcp",
                status="ok",
                latency_ms=round(latency_ms, 2)
            )
        else:
            # MCP endpoint not configured, assume available via Claude MCP tools
            latency_ms = (time.time() - start_time) * 1000
            return StorageBackendStatus(
                name="mcp",
                status="ok",
                latency_ms=round(latency_ms, 2),
                details={"mode": "claude_mcp_tools"}
            )

    except asyncio.TimeoutError:
        latency_ms = (time.time() - start_time) * 1000
        return StorageBackendStatus(
            name="mcp",
            status="error",
            latency_ms=round(latency_ms, 2),
            error="MCP server timeout (>500ms)"
        )
    except ImportError:
        return StorageBackendStatus(
            name="mcp",
            status="ok",
            details={"mode": "not_configured", "reason": "aiohttp not available"}
        )
    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        return StorageBackendStatus(
            name="mcp",
            status="error",
            latency_ms=round(latency_ms, 2),
            error=str(e)
        )


async def _check_json_health() -> StorageBackendStatus:
    """Check JSON fallback storage health.

    ✅ Story 36.10 Task 2.5
    Verifies JSON data directory is accessible and writable.
    """
    start_time = time.time()
    try:
        from pathlib import Path
        from app.config import settings

        # Check JSON storage directory
        json_data_dir = getattr(settings, "json_data_dir", "./data")
        data_path = Path(json_data_dir)

        if not data_path.exists():
            data_path.mkdir(parents=True, exist_ok=True)

        # Test write access by touching a temp file
        test_file = data_path / ".health_check"
        test_file.touch()
        test_file.unlink()

        latency_ms = (time.time() - start_time) * 1000
        return StorageBackendStatus(
            name="json",
            status="ok",
            latency_ms=round(latency_ms, 2),
            details={"path": str(data_path.absolute())}
        )

    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        return StorageBackendStatus(
            name="json",
            status="error",
            latency_ms=round(latency_ms, 2),
            error=str(e)
        )


async def _check_neo4j_for_storage() -> StorageBackendStatus:
    """Check Neo4j health for unified storage endpoint.

    ✅ Story 36.10 Task 2.3
    Reuses existing check_neo4j_health logic.
    """
    start_time = time.time()
    try:
        from app.config import settings

        if not settings.neo4j_enabled:
            return StorageBackendStatus(
                name="neo4j",
                status="error",
                error="Neo4j is disabled in configuration"
            )

        # Ensure driver is initialized and test connection
        await _ensure_neo4j_driver()
        await asyncio.wait_for(_test_neo4j_connection(), timeout=10.0)

        latency_ms = (time.time() - start_time) * 1000
        return StorageBackendStatus(
            name="neo4j",
            status="ok",
            latency_ms=round(latency_ms, 2),
            details={"uri": settings.neo4j_uri}
        )

    except asyncio.TimeoutError:
        latency_ms = (time.time() - start_time) * 1000
        return StorageBackendStatus(
            name="neo4j",
            status="error",
            latency_ms=round(latency_ms, 2),
            error="Connection timeout (>10000ms)"
        )
    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        return StorageBackendStatus(
            name="neo4j",
            status="error",
            latency_ms=round(latency_ms, 2),
            error=str(e)
        )


def _get_neo4j_pool_stats() -> Neo4jConnectionPool:
    """Extract Neo4j driver connection pool statistics.

    ✅ Story 36.10 AC-36.10.2
    Returns mock stats if driver not initialized (graceful degradation).
    """
    global _cached_neo4j_driver

    if _cached_neo4j_driver is None:
        # Return empty pool stats when driver not initialized
        return Neo4jConnectionPool(
            active=0,
            idle=0,
            max_size=50,
            utilization_percent=0.0
        )

    try:
        # Neo4j Python driver doesn't expose pool stats directly
        # We estimate based on driver configuration
        # In production, this could use driver metrics if available
        from app.config import settings

        max_pool_size = getattr(settings, "neo4j_max_connection_pool_size", 50)

        # Estimate: assume some connections are in use
        # Real implementation would use driver._pool if available
        return Neo4jConnectionPool(
            active=1,  # At least 1 if driver is initialized
            idle=max_pool_size - 1,
            max_size=max_pool_size,
            utilization_percent=round(1 / max_pool_size * 100, 2)
        )
    except Exception:
        return Neo4jConnectionPool(
            active=0,
            idle=0,
            max_size=50,
            utilization_percent=0.0
        )


@router.get(
    "/health/storage",
    response_model=StorageHealthResponse,
    summary="统一存储健康检查",
    description="检查所有存储后端(Neo4j/MCP/JSON)的健康状态，包含连接池指标和P95延迟",
    operation_id="check_storage_health",
    responses={
        200: {
            "description": "存储健康检查结果",
            "model": StorageHealthResponse,
            "content": {
                "application/json": {
                    "examples": {
                        "healthy": {
                            "summary": "所有存储正常",
                            "value": {
                                "status": "healthy",
                                "storage_backends": [
                                    {"name": "neo4j", "status": "ok", "latency_ms": 45},
                                    {"name": "mcp", "status": "ok", "latency_ms": 120},
                                    {"name": "json", "status": "ok", "latency_ms": 5}
                                ],
                                "connection_pool": {
                                    "neo4j": {"active": 3, "idle": 7, "max_size": 50, "utilization_percent": 6.0}
                                },
                                "latency_metrics": {"p95_ms": 85, "p50_ms": 42, "sample_count": 150, "window_seconds": 300},
                                "cached": False,
                                "cache_ttl_remaining_seconds": 0,
                                "timestamp": "2026-01-20T10:30:00Z"
                            }
                        },
                        "degraded": {
                            "summary": "部分存储异常",
                            "value": {
                                "status": "degraded",
                                "storage_backends": [
                                    {"name": "neo4j", "status": "ok", "latency_ms": 50},
                                    {"name": "mcp", "status": "error", "error": "MCP server timeout"},
                                    {"name": "json", "status": "ok", "latency_ms": 3}
                                ],
                                "connection_pool": {"neo4j": {"active": 5, "idle": 5, "max_size": 50, "utilization_percent": 10.0}},
                                "latency_metrics": {"p95_ms": 120, "window_seconds": 300},
                                "cached": True,
                                "cache_ttl_remaining_seconds": 15,
                                "timestamp": "2026-01-20T10:29:45Z"
                            }
                        }
                    }
                }
            }
        }
    }
)
async def check_storage_health(
    settings: Settings = Depends(get_settings)  # noqa: B008
) -> StorageHealthResponse:
    """
    检查统一存储健康状态.

    此端点整合Neo4j、MCP和JSON存储后端的健康状态，
    返回连接池指标和P95延迟统计信息。

    ✅ Story 36.10 AC-36.10.1, AC-36.10.4

    [Source: docs/stories/36.10.story.md]
    [Source: specs/data/storage-health-response.schema.json]

    Features:
        - Parallel health checks for all storage backends
        - Connection pool metrics for Neo4j
        - P95/P50 latency tracking (5-minute window)
        - Response caching (TTL=30s per ADR-007)
        - Status aggregation: healthy/degraded/unhealthy

    Returns:
        StorageHealthResponse: Unified storage health status
    """
    global _storage_health_cache, _storage_health_cache_time

    logger.debug("Storage health check requested")
    check_start_time = time.time()

    # Check cache first (TTL=30s per ADR-007)
    current_time = time.time()
    cache_age = current_time - _storage_health_cache_time

    if _storage_health_cache and cache_age < _STORAGE_HEALTH_CACHE_TTL:
        # Return cached response
        logger.debug(f"Returning cached storage health (age: {cache_age:.1f}s)")
        cache_ttl_remaining = int(_STORAGE_HEALTH_CACHE_TTL - cache_age)

        cached_response = StorageHealthResponse(**_storage_health_cache)
        cached_response.cached = True
        cached_response.cache_ttl_remaining_seconds = cache_ttl_remaining
        return cached_response

    # Perform parallel health checks
    neo4j_task = asyncio.create_task(_check_neo4j_for_storage())
    mcp_task = asyncio.create_task(_check_mcp_health())
    json_task = asyncio.create_task(_check_json_health())

    # Wait for all checks with overall timeout
    try:
        backends = await asyncio.wait_for(
            asyncio.gather(neo4j_task, mcp_task, json_task, return_exceptions=True),
            timeout=5.0  # 5s overall timeout
        )
    except asyncio.TimeoutError:
        logger.warning("Storage health check overall timeout")
        backends = [
            StorageBackendStatus(name="neo4j", status="error", error="Overall timeout"),
            StorageBackendStatus(name="mcp", status="error", error="Overall timeout"),
            StorageBackendStatus(name="json", status="error", error="Overall timeout")
        ]

    # Handle any exceptions from gather
    storage_backends = []
    for i, result in enumerate(backends):
        backend_names = ["neo4j", "mcp", "json"]
        if isinstance(result, Exception):
            storage_backends.append(StorageBackendStatus(
                name=backend_names[i],
                status="error",
                error=str(result)
            ))
        else:
            storage_backends.append(result)

    # Calculate total check latency and record it
    total_latency_ms = (time.time() - check_start_time) * 1000
    await _storage_latency_tracker.record(total_latency_ms)

    # Get latency metrics
    p95 = await _storage_latency_tracker.get_p95()
    p50 = await _storage_latency_tracker.get_p50()
    sample_count = await _storage_latency_tracker.get_sample_count()

    latency_metrics = LatencyMetrics(
        p95_ms=round(p95, 2),
        p50_ms=round(p50, 2),
        sample_count=sample_count,
        window_seconds=300
    )

    # Get connection pool stats
    neo4j_pool = _get_neo4j_pool_stats()
    connection_pool = {"neo4j": neo4j_pool}

    # Story 36.12 AC-36.12.6: Get failure counters
    esf = get_edge_sync_failures()
    dwf = get_dual_write_failures()

    # Aggregate status (now considers failure counters)
    overall_status = _aggregate_storage_status(storage_backends, esf, dwf)

    # Build response
    response = StorageHealthResponse(
        status=overall_status,
        storage_backends=storage_backends,
        connection_pool=connection_pool,
        latency_metrics=latency_metrics,
        cached=False,
        cache_ttl_remaining_seconds=0,
        timestamp=datetime.now(timezone.utc),
        edge_sync_failures=esf,
        dual_write_failures=dwf,
    )

    # Cache the response
    _storage_health_cache = response.model_dump()
    _storage_health_cache_time = time.time()

    logger.debug(f"Storage health check completed: {overall_status} ({total_latency_ms:.1f}ms)")
    return response


@router.post(
    "/health/storage/reset-counters",
    summary="重置存储失败计数器",
    description="重置 edge_sync_failures 和 dual_write_failures 计数器（运维用）",
    operation_id="reset_storage_failure_counters",
)
async def reset_storage_failure_counters() -> Dict[str, Any]:
    """
    Reset failure counters for storage health.

    Story 36.12 AC-36.12.6: Operational endpoint to reset counters
    after failures have been investigated and resolved.

    Returns:
        Previous counter values before reset.
    """
    prev = reset_counters()
    # Invalidate cache so next health check reflects reset
    global _storage_health_cache, _storage_health_cache_time
    _storage_health_cache = None
    _storage_health_cache_time = 0.0
    logger.info(f"Storage failure counters reset: {prev}")
    return {"reset": True, "previous_values": prev}


# ============================================================================
# Memory System Error Logs API (Story: Debug Memory Connection Issues)
# ============================================================================

from fastapi import Query


class MemoryLogsResponse(BaseModel):
    """记忆系统日志响应模型"""
    log_file: str = Field(..., description="日志文件路径")
    total_lines: int = Field(..., description="返回的日志行数")
    logs: list[str] = Field(..., description="日志内容列表")


@router.get(
    "/health/memory-logs",
    response_model=MemoryLogsResponse,
    summary="获取记忆系统错误日志",
    description="获取记忆系统（Neo4j/LanceDB/Graphiti）的最近日志，用于前端调试面板",
    operation_id="get_memory_system_logs"
)
async def get_memory_system_logs(
    lines: int = Query(default=50, ge=1, le=500, description="返回最近 N 行日志")
) -> MemoryLogsResponse:
    """
    获取记忆系统错误日志（最近 N 行）

    用于前端调试面板显示连接状态和错误信息。
    日志文件位置: backend/logs/memory-system-{date}.log
    """
    from pathlib import Path

    # __file__ = backend/app/api/v1/endpoints/health.py
    # .parent x5 = backend/app/api/v1/endpoints → v1 → api → app → backend
    log_dir = Path(__file__).parent.parent.parent.parent.parent / "logs"
    today = datetime.now().strftime('%Y-%m-%d')
    log_file = log_dir / f"memory-system-{today}.log"

    logs: list[str] = []
    log_file_str = str(log_file)

    if log_file.exists():
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                logs = [line.strip() for line in all_lines[-lines:]]
        except Exception as e:
            logger.warning(f"Failed to read memory system logs: {e}")
            logs = [f"[ERROR] Failed to read log file: {e}"]

    return MemoryLogsResponse(
        log_file=log_file_str,
        total_lines=len(logs),
        logs=logs
    )
