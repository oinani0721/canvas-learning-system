# Canvas Learning System - System Health Check Endpoint
# Story 1.1: Project Scaffold & Docker Setup (AC-2)
"""
System-level health check endpoint that verifies connectivity to
Neo4j, Ollama, and LanceDB infrastructure components.

Returns a structured response with per-component status, following
the API response envelope: {"data": {...}, "meta": {...}}.
"""

import logging
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.config import Settings, get_settings
from app.security import require_internal_api_key

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
        return ComponentStatus(name="neo4j", status="unhealthy", message=str(exc)[:200])


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
# Startup Health Check (Story 1.1 Task 4)
# [Source: _bmad-output/implementation-artifacts/epic-1/1-1-vault-init-templates.md]
# ═══════════════════════════════════════════════════════════════════════════════


class StartupCheckResult(BaseModel):
    service: str
    status: str
    latency_ms: float
    error_detail: str | None = None
    fix_hint: str | None = None


async def _timed_check(name: str, coro, fix_hint: str = "") -> StartupCheckResult:
    import time

    start = time.monotonic()
    try:
        result = await coro
        elapsed = (time.monotonic() - start) * 1000
        return StartupCheckResult(
            service=name,
            status=result.status,
            latency_ms=round(elapsed, 1),
            error_detail=result.message if result.status != "healthy" else None,
            fix_hint=fix_hint if result.status != "healthy" else None,
        )
    except Exception as exc:
        elapsed = (time.monotonic() - start) * 1000
        return StartupCheckResult(
            service=name,
            status="unhealthy",
            latency_ms=round(elapsed, 1),
            error_detail=str(exc)[:200],
            fix_hint=fix_hint,
        )


async def _check_fastapi() -> ComponentStatus:
    return ComponentStatus(name="fastapi", status="healthy", message="Self-check OK")


async def _check_mcp() -> ComponentStatus:
    try:
        from app.mcp.server import mcp

        tools = await mcp.list_tools()
        count = len(tools)
        return ComponentStatus(
            name="mcp",
            status="healthy" if count > 0 else "unhealthy",
            message=f"{count} tools registered",
        )
    except Exception as exc:
        return ComponentStatus(name="mcp", status="unhealthy", message=str(exc)[:200])


@router.get("/startup-check")
async def startup_health_check(
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> dict:
    """
    AR1-ordered startup verification (Story 1.1 AC #3).

    Checks: Neo4j → Ollama(bge-m3) → FastAPI → MCP tools.
    """
    checks = [
        await _timed_check(
            "neo4j",
            _check_neo4j(settings),
            "确认 Neo4j 容器运行中: docker-compose up -d neo4j",
        ),
        await _timed_check(
            "ollama",
            _check_ollama(settings),
            "确认 Ollama 运行中: brew services start ollama && ollama pull bge-m3",
        ),
        await _timed_check("fastapi", _check_fastapi(), "FastAPI 进程异常"),
        await _timed_check(
            "mcp",
            _check_mcp(),
            "MCP server 初始化失败，检查 backend/app/mcp/server.py",
        ),
    ]

    all_ok = all(c.status == "healthy" for c in checks)
    now = datetime.now(timezone.utc).isoformat()

    return {
        "data": {
            "overall_status": "ready" if all_ok else "not_ready",
            "checks": [c.model_dump() for c in checks],
        },
        "meta": {"timestamp": now},
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Setup Wizard (Story 1.1 Task 5)
# ═══════════════════════════════════════════════════════════════════════════════


class SetupWizardRequest(BaseModel):
    vault_path: str = Field(..., description="Path to the Obsidian vault directory")


@router.post("/setup-wizard")
async def setup_wizard(
    request: SetupWizardRequest,
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> dict:
    """
    Installation wizard: vault init → plugin check → startup verify (Story 1.1 AC #1-3).
    """
    from app.services.vault_init_service import VaultInitService

    svc = VaultInitService()
    vault_result = svc.initialize_vault(request.vault_path)
    plugins = svc.check_required_plugins(request.vault_path)

    startup_resp = await startup_health_check(settings)
    backend_checks = startup_resp["data"]["checks"]

    plugins_ok = all(p.installed for p in plugins)
    backend_ok = startup_resp["data"]["overall_status"] == "ready"
    vault_ok = True

    now = datetime.now(timezone.utc).isoformat()

    return {
        "data": {
            "vault_ready": vault_ok,
            "vault_dirs": vault_result,
            "plugins": [
                {
                    "id": p.plugin_id,
                    "name": p.display_name,
                    "type": p.plugin_type,
                    "installed": p.installed,
                }
                for p in plugins
            ],
            "backend": backend_checks,
            "overall_status": "ready"
            if (vault_ok and plugins_ok and backend_ok)
            else "not_ready",
        },
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
        # Story 3-7 FIX M1: Generalize error message — do not leak internal details
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve LLM statistics. Please try again later.",
        ) from e

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


# ═══════════════════════════════════════════════════════════════════════════════
# Model Configuration Endpoints (Story 1.3)
# [Source: _bmad-output/implementation-artifacts/1-3-model-config-settings-panel.md]
# ═══════════════════════════════════════════════════════════════════════════════


class _ModelTaskConfigRequest(BaseModel):
    """Single-task model config received from the frontend.

    [Source: Story 1.3 Task 9.2]
    """

    provider: str = Field(..., description="gemini | anthropic | openai | ollama")
    model_name: str = Field(..., description="Model identifier")
    api_key: str = Field(default="", description="Provider API key")


class _SystemModelConfigRequest(BaseModel):
    """Aggregated config pushed from the Settings Tab.

    [Source: Story 1.3 Task 9.2]
    """

    chat: _ModelTaskConfigRequest | None = None
    scoring: _ModelTaskConfigRequest | None = None


@router.post(
    "/config",
    summary="Sync model configuration from frontend",
    description=(
        "Receives model provider, name and API key from the Obsidian Settings Tab "
        "and stores them in the backend's in-memory runtime config. "
        "API keys are never persisted to disk. (Story 1.3 AC-8)"
    ),
    tags=["System"],
    dependencies=[Depends(require_internal_api_key)],
    responses={
        403: {"description": "Invalid internal API key"},
        503: {
            "description": "Internal API key not configured (production fail-closed)"
        },
    },
)
async def update_model_config(body: _SystemModelConfigRequest) -> dict:
    """Receive model configuration from the frontend Settings Tab.

    [Source: Story 1.3 AC-8 — model config sync to backend]
    [Source: Story 1.3 Task 9.2 — POST /api/v1/system/config]
    [Source: Story 1.3 Task 9.5 — API Key in-memory only]
    [Source: Story 1.3 Task 9.6 — API Key not written to logs]
    """
    from app.core.litellm_config import (
        ModelTaskConfig,
        SystemModelConfig,
        get_runtime_model_config,
    )

    chat_cfg = (
        ModelTaskConfig(
            provider=body.chat.provider,
            model_name=body.chat.model_name,
            api_key=body.chat.api_key,
        )
        if body.chat
        else None
    )
    scoring_cfg = (
        ModelTaskConfig(
            provider=body.scoring.provider,
            model_name=body.scoring.model_name,
            api_key=body.scoring.api_key,
        )
        if body.scoring
        else None
    )

    sys_config = SystemModelConfig(chat=chat_cfg, scoring=scoring_cfg)
    mgr = get_runtime_model_config()
    mgr.update(sys_config)

    now = datetime.now(timezone.utc).isoformat()
    # Log confirmation without exposing API keys (Story 1.3 Task 9.6)
    logger.info(
        "[Story 1.3] Model config received — chat_provider=%s, scoring_provider=%s",
        body.chat.provider if body.chat else "none",
        body.scoring.provider if body.scoring else "none",
    )

    return {
        "data": {"status": "ok", "message": "Model configuration updated"},
        "meta": {"timestamp": now},
    }


@router.post(
    "/test-llm",
    summary="Test LLM connection",
    description=(
        "Sends a minimal completion request via LiteLLM to verify that "
        "the provided model and API key are valid. (Story 1.3 AC-3/AC-4)"
    ),
    tags=["System"],
    dependencies=[Depends(require_internal_api_key)],
    responses={
        403: {"description": "Invalid internal API key"},
        503: {
            "description": "Internal API key not configured (production fail-closed)"
        },
    },
)
async def test_llm_connection(config: _ModelTaskConfigRequest) -> dict:
    """Test LLM connection with the given provider, model, and API key.

    [Source: Story 1.3 AC-3 — test connection button]
    [Source: Story 1.3 Task 9.3 — POST /api/v1/system/test-llm]
    [Source: Story 1.3 Dev Notes — LiteLLM test connection implementation]
    """
    from app.core.litellm_config import format_litellm_model

    model_str = format_litellm_model(config.provider, config.model_name)
    now = datetime.now(timezone.utc).isoformat()

    try:
        import litellm

        await litellm.acompletion(
            model=model_str,
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=5,
            api_key=config.api_key if config.api_key else None,
        )

        # Successful response — connection is valid
        logger.info(
            "[Story 1.3] LLM connection test passed — model=%s",
            model_str,
        )
        return {
            "data": {"status": "success", "model": model_str},
            "meta": {"timestamp": now},
        }

    except ImportError:
        logger.warning("[Story 1.3] litellm not installed, test-llm unavailable")
        return {
            "data": {
                "status": "failed",
                "error": "litellm is not installed on the backend",
            },
            "meta": {"timestamp": now},
        }
    except Exception as e:
        # Sanitize error message: strip any API key fragments (NFR-SEC-02)
        raw_msg = str(e)
        # Remove potential key patterns (sk-..., AIza..., key=..., etc.)
        sanitized = re.sub(
            r"(sk-[a-zA-Z0-9]{3})[a-zA-Z0-9-]+",
            r"\1***",
            raw_msg,
        )
        sanitized = re.sub(
            r"(AIza[a-zA-Z0-9]{3})[a-zA-Z0-9-]+",
            r"\1***",
            sanitized,
        )
        sanitized = re.sub(
            r'(api[_-]?key["\s:=]+)["\']?[a-zA-Z0-9_-]{8,}["\']?',
            r"\1***",
            sanitized,
            flags=re.IGNORECASE,
        )
        logger.warning("[Story 1.3] LLM connection test failed — model=%s", model_str)
        return {
            "data": {"status": "failed", "error": sanitized},
            "meta": {"timestamp": now},
        }


# ═══════════════════════════════════════════════════════════════════════════════
# QA Metrics & Pipeline Health Endpoints (Story 7.4)
# [Source: _bmad-output/implementation-artifacts/7-4-difficulty-matching-extraction-validation.md]
# ═══════════════════════════════════════════════════════════════════════════════


class AnnotationRequestBody(BaseModel):
    """Request body for annotation submission (Story 7.4 AC-3)."""

    annotation: str = Field(
        ..., description="Annotation value: 'correct' | 'incorrect' | 'partial'"
    )


class UpdateExtractionRequestBody(BaseModel):
    """Request body for updating extraction content (Story 5.8 AC-4)."""

    extracted_content: str = Field(
        ..., min_length=1, description="Updated extracted content"
    )


@router.get(
    "/qa-metrics",
    summary="Get QA quality metrics",
    description=(
        "Returns difficulty matching rate (sliding window of 50 questions) "
        "and extraction quality statistics. (Story 7.4 AC-2, AC-4)"
    ),
    tags=["System"],
)
async def get_qa_metrics() -> dict:
    """Return combined QA metrics: difficulty match rate + extraction quality.

    [Source: Story 7.4 Task 5.1 — GET /api/v1/system/qa-metrics]
    [Source: Story 7.4 AC-2, AC-4]
    """
    from app.models.qa_models import QAMetricsResponse
    from app.services.difficulty_matcher import get_difficulty_matcher
    from app.services.extraction_validator import get_extraction_validator

    now = datetime.now(timezone.utc).isoformat()

    try:
        matcher = get_difficulty_matcher()
        match_stats = await matcher.get_stats_with_recent()
    except Exception as e:
        logger.error(f"[Story 7.4] Failed to get difficulty stats: {e}")
        from app.models.qa_models import DifficultyMatchStats

        match_stats = DifficultyMatchStats()

    try:
        validator = get_extraction_validator()
        extraction_stats = await validator.get_stats()
    except Exception as e:
        logger.error(f"[Story 7.4] Failed to get extraction stats: {e}")
        from app.models.qa_models import ExtractionStats

        extraction_stats = ExtractionStats()

    response = QAMetricsResponse(
        difficulty_match=match_stats,
        extraction_quality=extraction_stats,
    )

    return {
        "data": response.model_dump(),
        "meta": {"timestamp": now},
    }


@router.get(
    "/pipeline-health",
    summary="Get pipeline health indicators",
    description=(
        "Returns 7 pipeline health metrics with traffic-light statuses "
        "and error classification summary. (Story 7.4 AC-5)"
    ),
    tags=["System"],
)
async def get_pipeline_health() -> dict:
    """Return full pipeline health status with all 7 indicators.

    [Source: Story 7.4 Task 5.2 — GET /api/v1/system/pipeline-health]
    [Source: Story 7.4 AC-5]
    """
    from app.services.health_monitor import get_pipeline_health_monitor

    now = datetime.now(timezone.utc).isoformat()

    try:
        monitor = get_pipeline_health_monitor()
        health = await monitor.get_health()
    except Exception as e:
        logger.error(f"[Story 7.4] Failed to get pipeline health: {e}")
        from app.models.qa_models import PipelineHealthStatus

        health = PipelineHealthStatus(overall="critical")

    return {
        "data": health.model_dump(),
        "meta": {"timestamp": now},
    }


@router.get(
    "/extraction-records",
    summary="Query extraction records for human review",
    description=(
        "Paginated query of structured extraction records, with optional "
        "type filtering (error/tip/key_qa). (Story 7.4 AC-3)"
    ),
    tags=["System"],
)
async def get_extraction_records(
    extraction_type: Optional[str] = Query(
        default=None,
        description="Filter by type: error, tip, key_qa",
    ),
    annotation_filter: Optional[str] = Query(
        default=None,
        description="Filter by annotation status: 'annotated' | 'unannotated' | None for all",
    ),
    page: int = Query(default=1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Records per page"),
) -> dict:
    """Return paginated extraction records for human spot-check review.

    [Source: Story 7.4 Task 5.3 — GET /api/v1/system/extraction-records]
    [Source: Story 7.4 AC-3, Story 5.8 AC-5]
    """
    from app.services.extraction_validator import get_extraction_validator

    now = datetime.now(timezone.utc).isoformat()

    try:
        validator = get_extraction_validator()
        result = await validator.get_records(
            extraction_type=extraction_type,
            annotation_filter=annotation_filter,
            page=page,
            page_size=page_size,
        )
    except Exception as e:
        logger.error(f"[Story 7.4] Failed to get extraction records: {e}")
        from app.models.qa_models import ExtractionRecordPage

        result = ExtractionRecordPage()

    return {
        "data": result.model_dump(),
        "meta": {"timestamp": now},
    }


@router.post(
    "/extraction-records/{record_id}/annotate",
    summary="Submit human annotation for extraction record",
    description=(
        "Mark an extraction record as correct, incorrect, or partial. (Story 7.4 AC-3)"
    ),
    tags=["System"],
)
async def annotate_extraction_record(
    record_id: str,
    body: "AnnotationRequestBody",
) -> dict:
    """Submit a human annotation for a specific extraction record.

    [Source: Story 7.4 Task 5.4 — POST /api/v1/system/extraction-records/{id}/annotate]
    [Source: Story 7.4 AC-3]
    """
    from app.services.extraction_validator import get_extraction_validator

    now = datetime.now(timezone.utc).isoformat()

    try:
        validator = get_extraction_validator()
        updated = await validator.annotate(record_id, body.annotation)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error(f"[Story 7.4] Failed to annotate record {record_id}: {e}")
        raise HTTPException(status_code=500, detail="Annotation failed") from e

    if not updated:
        raise HTTPException(status_code=404, detail=f"Record {record_id} not found")

    return {
        "data": {"status": "ok", "record_id": record_id, "annotation": body.annotation},
        "meta": {"timestamp": now},
    }


@router.patch(
    "/extraction-records/{record_id}",
    summary="Update extraction record content",
    description=(
        "Edit the extracted_content of a record. Used for correcting LLM extraction errors. (Story 5.8 AC-4)"
    ),
    tags=["System"],
)
async def update_extraction_record(
    record_id: str,
    body: "UpdateExtractionRequestBody",
) -> dict:
    """Update extracted_content for a specific record.

    [Source: Story 5.8 Task 2.1 — PATCH /api/v1/system/extraction-records/{record_id}]
    """
    from app.services.extraction_validator import get_extraction_validator

    now = datetime.now(timezone.utc).isoformat()

    try:
        validator = get_extraction_validator()
        updated = await validator.update_content(record_id, body.extracted_content)
    except Exception as e:
        logger.error(f"[Story 5.8] Failed to update record {record_id}: {e}")
        raise HTTPException(status_code=500, detail="Update failed") from e

    if not updated:
        raise HTTPException(status_code=404, detail=f"Record {record_id} not found")

    return {
        "data": updated.model_dump(),
        "meta": {"timestamp": now},
    }


@router.delete(
    "/extraction-records/{record_id}",
    summary="Soft-delete an extraction record",
    description=(
        "Marks an extraction record as deleted (soft delete). "
        "The record is excluded from queries but not physically removed. (Story 5.8 AC-4)"
    ),
    tags=["System"],
)
async def delete_extraction_record(
    record_id: str,
) -> dict:
    """Soft-delete a specific extraction record.

    [Source: Story 5.8 Task 2.2 — DELETE /api/v1/system/extraction-records/{record_id}]
    """
    from app.services.extraction_validator import get_extraction_validator

    try:
        validator = get_extraction_validator()
        deleted = await validator.delete_record(record_id)
    except Exception as e:
        logger.error(f"[Story 5.8] Failed to delete record {record_id}: {e}")
        raise HTTPException(status_code=500, detail="Delete failed") from e

    if not deleted:
        raise HTTPException(status_code=404, detail=f"Record {record_id} not found")

    now = datetime.now(timezone.utc).isoformat()
    return {
        "data": {"status": "deleted", "record_id": record_id},
        "meta": {"timestamp": now},
    }


@router.delete(
    "/extraction-records/{record_id}/annotation",
    summary="Reset annotation for an extraction record",
    description=(
        "Clears the annotation and annotated_at fields, allowing re-annotation. (Story 5.8 AC-2)"
    ),
    tags=["System"],
)
async def reset_extraction_annotation(
    record_id: str,
) -> dict:
    """Reset (revoke) annotation for a specific extraction record.

    [Source: Story 5.8 Task 2.3 — DELETE /api/v1/system/extraction-records/{record_id}/annotation]
    """
    from app.services.extraction_validator import get_extraction_validator

    now = datetime.now(timezone.utc).isoformat()

    try:
        validator = get_extraction_validator()
        reset = await validator.reset_annotation(record_id)
    except Exception as e:
        logger.error(f"[Story 5.8] Failed to reset annotation {record_id}: {e}")
        raise HTTPException(status_code=500, detail="Reset failed") from e

    if not reset:
        raise HTTPException(status_code=404, detail=f"Record {record_id} not found")

    return {
        "data": {"status": "ok", "record_id": record_id, "annotation": None},
        "meta": {"timestamp": now},
    }


@router.get(
    "/error-aggregation",
    summary="Get error classification aggregation",
    description=(
        "Returns error counts grouped by 4 categories (LLM/Network/Algorithm/Data) "
        "across 24h, 7d, and 30d time windows. (Story 7.4 AC-6)"
    ),
    tags=["System"],
)
async def get_error_aggregation() -> dict:
    """Return error classification aggregation across time windows.

    [Source: Story 7.4 Task 5.5 — GET /api/v1/system/error-aggregation]
    [Source: Story 7.4 AC-6]
    """
    from app.services.error_aggregator import get_error_aggregator

    now = datetime.now(timezone.utc).isoformat()

    try:
        aggregator = get_error_aggregator()
        aggregation = await aggregator.get_aggregation()
    except Exception as e:
        logger.error(f"[Story 7.4] Failed to get error aggregation: {e}")
        from app.models.qa_models import ErrorAggregation

        aggregation = ErrorAggregation()

    return {
        "data": aggregation.model_dump(),
        "meta": {"timestamp": now},
    }
