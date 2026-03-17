# Canvas Learning System - System Health Check Endpoint
# Story 1.1: Project Scaffold & Docker Setup (AC-2)
"""
System-level health check endpoint that verifies connectivity to
Neo4j, Ollama, and LanceDB infrastructure components.

Returns a structured response with per-component status, following
the API response envelope: {"data": {...}, "meta": {...}}.
"""

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/system", tags=["System"])


class ComponentStatus(BaseModel):
    """Health status of a single infrastructure component."""

    name: str
    status: str  # "healthy" | "unhealthy" | "unknown"
    message: str | None = None


class HealthResponse(BaseModel):
    """Aggregated health status of all infrastructure components."""

    status: str  # "healthy" | "degraded" | "unhealthy"
    components: list[ComponentStatus]
    timestamp: str


async def _check_neo4j(settings: Settings) -> ComponentStatus:
    """Check Neo4j connectivity via Bolt driver."""
    try:
        from neo4j import AsyncGraphDatabase

        driver = AsyncGraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
        )
        try:
            async with driver.session(database=settings.NEO4J_DATABASE) as session:
                result = await session.run("RETURN 1 AS n")
                record = await result.single()
                if record and record["n"] == 1:
                    return ComponentStatus(
                        name="neo4j", status="healthy", message="Bolt connection OK"
                    )
                return ComponentStatus(
                    name="neo4j",
                    status="unhealthy",
                    message="Unexpected query result",
                )
        finally:
            await driver.close()
    except Exception as exc:
        logger.warning("Neo4j health check failed: %s", exc)
        return ComponentStatus(
            name="neo4j", status="unhealthy", message=str(exc)[:200]
        )


async def _check_ollama(settings: Settings) -> ComponentStatus:
    """Check Ollama connectivity via HTTP GET /api/tags."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.OLLAMA_HOST}/api/tags")
            if resp.status_code == 200:
                return ComponentStatus(
                    name="ollama", status="healthy", message="API reachable"
                )
            return ComponentStatus(
                name="ollama",
                status="unhealthy",
                message=f"HTTP {resp.status_code}",
            )
    except Exception as exc:
        logger.warning("Ollama health check failed: %s", exc)
        return ComponentStatus(
            name="ollama", status="unhealthy", message=str(exc)[:200]
        )


async def _check_lancedb(settings: Settings) -> ComponentStatus:
    """Check LanceDB data directory exists."""
    try:
        lancedb_dir = Path(settings.CANVAS_BASE_PATH) / ".lancedb"
        if lancedb_dir.exists() and lancedb_dir.is_dir():
            return ComponentStatus(
                name="lancedb",
                status="healthy",
                message=f"Data directory exists: {lancedb_dir}",
            )
        # Directory not existing is not necessarily unhealthy on first run;
        # report as unknown so the frontend shows a meaningful state.
        return ComponentStatus(
            name="lancedb",
            status="unknown",
            message=f"Data directory not found: {lancedb_dir}",
        )
    except Exception as exc:
        logger.warning("LanceDB health check failed: %s", exc)
        return ComponentStatus(
            name="lancedb", status="unhealthy", message=str(exc)[:200]
        )


@router.get("/health")
async def system_health_check(
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> dict:
    """
    System-level health check (AC-2).

    Returns per-component connectivity status for Neo4j, Ollama, and LanceDB
    wrapped in the standard API envelope.
    """
    components = [
        await _check_neo4j(settings),
        await _check_ollama(settings),
        await _check_lancedb(settings),
    ]

    all_healthy = all(c.status == "healthy" for c in components)
    any_unhealthy = any(c.status == "unhealthy" for c in components)

    if all_healthy:
        overall = "healthy"
    elif any_unhealthy:
        overall = "degraded"
    else:
        overall = "degraded"

    now = datetime.now(timezone.utc).isoformat()

    health = HealthResponse(
        status=overall,
        components=components,
        timestamp=now,
    )

    return {
        "data": health.model_dump(),
        "meta": {"timestamp": now},
    }


# ═══════════════════════════════════════════════════════════════════════════════
# LLM Usage Statistics (Story 7.2)
# [Source: _bmad-output/implementation-artifacts/7-2-llm-logging-token-tracking.md]
# ═══════════════════════════════════════════════════════════════════════════════


class LLMStatsSummary(BaseModel):
    """Summary statistics for LLM usage.

    [Source: Story 7.2 Task 3.3]
    """

    total_calls: int = Field(0, description="Total number of LLM calls")
    total_tokens: int = Field(0, description="Total tokens consumed")
    total_input_tokens: int = Field(0, description="Total input/prompt tokens")
    total_output_tokens: int = Field(0, description="Total output/completion tokens")
    total_cost_usd: float = Field(0.0, description="Total estimated cost in USD")
    avg_latency_ms: float = Field(0.0, description="Average response latency in ms")
    success_rate: float = Field(1.0, description="Success rate (0.0 to 1.0)")


class TaskTypeStats(BaseModel):
    """Per-task-type statistics.

    [Source: Story 7.2 Task 3.4]
    """

    task_type: str = Field(..., description="Task type identifier")
    calls: int = Field(0, description="Number of calls")
    tokens: int = Field(0, description="Total tokens consumed")
    cost_usd: float = Field(0.0, description="Estimated cost in USD")


class DayStats(BaseModel):
    """Per-day statistics."""

    date: str = Field(..., description="Date (YYYY-MM-DD)")
    calls: int = Field(0, description="Number of calls")
    tokens: int = Field(0, description="Total tokens consumed")
    cost_usd: float = Field(0.0, description="Estimated cost in USD")


class ErrorStats(BaseModel):
    """Error statistics.

    [Source: Story 7.2 Task 3.5]
    """

    total: int = Field(0, description="Total error count")
    by_type: Dict[str, int] = Field(
        default_factory=dict, description="Error count by category"
    )


class LLMStatsData(BaseModel):
    """LLM statistics data payload."""

    summary: LLMStatsSummary = Field(
        default_factory=LLMStatsSummary, description="Aggregated summary"
    )
    by_task: list[TaskTypeStats] = Field(
        default_factory=list, description="Per-task-type breakdown"
    )
    by_day: list[DayStats] = Field(
        default_factory=list, description="Per-day breakdown"
    )
    errors: ErrorStats = Field(
        default_factory=ErrorStats, description="Error statistics"
    )


class LLMStatsMeta(BaseModel):
    """LLM statistics metadata."""

    period: str = Field(..., description="Requested period")
    start_date: str = Field(..., description="Period start date")
    end_date: str = Field(..., description="Period end date")
    timestamp: str = Field(..., description="Query timestamp")


class LLMStatsResponse(BaseModel):
    """Full LLM statistics response.

    [Source: Story 7.2 Task 3.2 — Response format]
    """

    data: LLMStatsData = Field(..., description="Statistics data")
    meta: LLMStatsMeta = Field(..., description="Query metadata")


def _compute_period_range(
    period: str,
    start_date: Optional[str],
    end_date: Optional[str],
) -> tuple[str, str, str]:
    """Compute start/end timestamps for a given period.

    Args:
        period: One of 'today', 'week', 'month', 'custom'
        start_date: Required for 'custom' period (YYYY-MM-DD)
        end_date: Required for 'custom' period (YYYY-MM-DD)

    Returns:
        Tuple of (start_iso, end_iso, period_label)

    Raises:
        HTTPException: If custom period is missing dates
    """
    now = datetime.now(timezone.utc)

    if period == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
        label = "today"
    elif period == "week":
        start = now - timedelta(days=7)
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
        label = "week"
    elif period == "month":
        start = now - timedelta(days=30)
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
        label = "month"
    elif period == "custom":
        if not start_date or not end_date:
            raise HTTPException(
                status_code=400,
                detail="start_date and end_date are required for custom period",
            )
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d").replace(
                tzinfo=timezone.utc
            )
            end = datetime.strptime(end_date, "%Y-%m-%d").replace(
                tzinfo=timezone.utc, hour=23, minute=59, second=59
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail="Invalid date format. Use YYYY-MM-DD",
            ) from exc
        label = "custom"
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid period: {period}. Use today/week/month/custom",
        )

    start_iso = start.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    end_iso = end.strftime("%Y-%m-%dT%H:%M:%S.999Z")

    return start_iso, end_iso, label


@router.get(
    "/llm-stats",
    summary="Get LLM usage statistics",
    description=(
        "Returns aggregated LLM usage statistics including call counts, "
        "token consumption, estimated costs, and error breakdowns. "
        "Supports filtering by time period and task type."
    ),
    tags=["System"],
)
async def get_llm_stats(
    period: str = Query(
        default="today",
        description="Time period: today, week, month, or custom",
    ),
    start_date: Optional[str] = Query(
        default=None,
        description="Start date for custom period (YYYY-MM-DD)",
    ),
    end_date: Optional[str] = Query(
        default=None,
        description="End date for custom period (YYYY-MM-DD)",
    ),
    task_type: Optional[str] = Query(
        default=None,
        description="Filter by task type: conversation, scoring, extraction, indexing, qa_check",
    ),
) -> dict:
    """Get aggregated LLM usage statistics.

    [Source: Story 7.2 AC #7 — GET /api/v1/system/llm-stats]
    [Source: Story 7.2 Task 3.1 — Query parameters]

    Args:
        period: Time period filter (today/week/month/custom)
        start_date: Start date for custom period
        end_date: End date for custom period
        task_type: Optional task type filter

    Returns:
        LLMStatsResponse with data and meta
    """
    from app.middleware.cost_tracker import get_cost_tracker

    start_iso, end_iso, label = _compute_period_range(period, start_date, end_date)

    try:
        cost_tracker = await get_cost_tracker()
        stats = await cost_tracker.get_stats_by_period(
            start=start_iso,
            end=end_iso,
            task_type=task_type,
        )
    except Exception as e:
        logger.error(f"[Story 7.2] Failed to get LLM stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get LLM stats: {e}") from e

    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

    response = LLMStatsResponse(
        data=LLMStatsData(
            summary=LLMStatsSummary(**stats["summary"]),
            by_task=[TaskTypeStats(**t) for t in stats["by_task"]],
            by_day=[DayStats(**d) for d in stats["by_day"]],
            errors=ErrorStats(**stats["errors"]),
        ),
        meta=LLMStatsMeta(
            period=label,
            start_date=start_iso[:10],
            end_date=end_iso[:10],
            timestamp=now_iso,
        ),
    )

    return response.model_dump()
