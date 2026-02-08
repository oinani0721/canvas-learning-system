# Canvas Learning System - FastAPI Application Entry Point
# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: FastAPI application initialization)
"""
FastAPI application entry point for the Canvas Learning System backend.

This module creates and configures the FastAPI application instance,
including middleware, routes, and lifecycle events.

[Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#FastAPI应用初始化]
[Source: specs/api/fastapi-backend-api.openapi.yml]

Usage:
    uvicorn app.main:app --reload
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: FastAPI CORSMiddleware)
from fastapi import FastAPI, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.v1.endpoints.monitoring import set_alert_manager
from app.api.v1.router import router as api_v1_router
from app.config import settings
from app.core.bug_tracker import bug_tracker
from app.core.logging import setup_logging
from app.middleware.metrics import MetricsMiddleware
from app.services.alert_manager import AlertManager, load_alert_rules_from_yaml
from app.services.notification_channels import create_default_dispatcher
from app.services.resource_monitor import get_default_monitor

# ✅ Story 30.3 Fix: Import MemoryService for startup pre-warm
from app.api.v1.endpoints.memory import get_memory_service, cleanup_memory_service

# ✅ Story 33.2: WebSocket endpoint import
from app.api.v1.endpoints.websocket import (
    websocket_intelligent_parallel,
    set_session_validator,
)

# ═══════════════════════════════════════════════════════════════════════════════
# Logging Setup
# ═══════════════════════════════════════════════════════════════════════════════

# Configure logging before application starts
# [Source: ADR-010 - Logging聚合策略]
setup_logging(log_level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Lifespan Event Handler
# ═══════════════════════════════════════════════════════════════════════════════

# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: lifespan event handlers)
# Pattern: asynccontextmanager for startup/shutdown lifecycle management
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan context manager.

    Handles startup and shutdown events for the FastAPI application.
    This is the modern replacement for @app.on_event decorators.

    ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: lifespan asynccontextmanager)

    Args:
        app: FastAPI application instance.

    Yields:
        None: Control returns to the application during runtime.
    """
    # Startup
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"Log level: {settings.LOG_LEVEL}")
    logger.info(f"CORS origins: {settings.cors_origins_list}")
    logger.info(f"API prefix: {settings.API_V1_PREFIX}")

    # ✅ Verified from Story 17.2 AC-4: Start resource monitoring (≤5s interval)
    # [Source: docs/architecture/performance-monitoring-architecture.md:281-320]
    resource_monitor = get_default_monitor()
    await resource_monitor.start_background_collection(interval_seconds=5.0)
    logger.info("Resource monitoring started with 5s interval")

    # ✅ Verified from Story 17.3: Start alert evaluation system
    # [Source: docs/architecture/performance-monitoring-architecture.md:281-323]
    # [Source: docs/stories/17.3.story.md - AC 1-5]
    alert_rules = load_alert_rules_from_yaml("config/alerts.yaml")
    notification_dispatcher = create_default_dispatcher()
    alert_manager = AlertManager(
        rules=alert_rules,
        notification_dispatcher=notification_dispatcher,
        evaluation_interval=30,  # 30-second evaluation cycle
    )
    await alert_manager.start()
    logger.info(f"Alert manager started with {len(alert_rules)} rules (30s interval)")

    # Store alert_manager in app state for dependency injection
    app.state.alert_manager = alert_manager

    # Set global alert manager for monitoring endpoint dependency injection
    set_alert_manager(alert_manager)

    # ✅ Story 30.3 Fix: Pre-warm MemoryService singleton to avoid first-call latency
    # This ensures the first /api/v1/memory/health call is fast (<100ms vs 21s)
    try:
        logger.info("Pre-warming MemoryService singleton...")
        await get_memory_service()
        logger.info("MemoryService pre-warmed successfully")
    except Exception as e:
        logger.warning(f"MemoryService pre-warm failed (non-fatal): {e}")

    # ✅ Story 38.4: Log dual-write configuration status (AC-1, AC-2)
    if settings.ENABLE_GRAPHITI_JSON_DUAL_WRITE:
        logger.info("Dual-write: enabled (default)")
    else:
        logger.info("Dual-write: disabled (explicit configuration)")
        logger.warning("JSON fallback is disabled. Neo4j outage will cause data loss.")

    # ✅ Story 38.6 AC-3: Recover failed writes from fallback file on startup
    try:
        from app.services.memory_service import get_memory_service as _get_ms
        ms = _get_ms()
        recovery_result = await ms.recover_failed_writes()
        recovered = recovery_result.get("recovered", 0)
        pending = recovery_result.get("pending", 0)
        if recovered > 0 or pending > 0:
            logger.info(f"[Story 38.6] Recovered {recovered} failed writes, {pending} still pending")
    except Exception as e:
        logger.warning(f"[Story 38.6] Failed write recovery skipped: {e}")

    # ✅ Story 38.1 AC-3: Recover pending LanceDB index operations on startup
    try:
        from app.services.lancedb_index_service import get_lancedb_index_service
        lancedb_idx_svc = get_lancedb_index_service()
        if lancedb_idx_svc:
            idx_result = await lancedb_idx_svc.recover_pending(settings.canvas_base_path)
            recovered = idx_result.get("recovered", 0)
            pending = idx_result.get("pending", 0)
            if recovered > 0 or pending > 0:
                logger.info(
                    f"[Story 38.1] LanceDB index recovery: "
                    f"{recovered} recovered, {pending} still pending"
                )
            else:
                logger.info("[Story 38.1] No pending LanceDB index operations")
    except Exception as e:
        logger.warning(f"[Story 38.1] LanceDB index recovery skipped: {e}")

    yield  # Application runs here

    # Shutdown
    logger.info(f"Shutting down {settings.PROJECT_NAME}...")

    # ✅ Stop alert manager gracefully
    await alert_manager.stop()
    logger.info("Alert manager stopped")

    # ✅ Stop resource monitoring gracefully
    await resource_monitor.stop_background_collection()
    logger.info("Resource monitoring stopped")

    # ✅ Story 38.1: Cleanup LanceDB index service (cancel pending debounce tasks)
    try:
        from app.services.lancedb_index_service import get_lancedb_index_service
        lancedb_idx_svc = get_lancedb_index_service()
        if lancedb_idx_svc:
            await lancedb_idx_svc.cleanup()
            logger.info("LanceDB index service cleaned up")
    except Exception as e:
        logger.warning(f"LanceDB index service cleanup failed: {e}")

    # ✅ Story 30.3: Cleanup MemoryService singleton (Neo4j driver, etc.)
    await cleanup_memory_service()
    logger.info("MemoryService cleaned up")

# ═══════════════════════════════════════════════════════════════════════════════
# FastAPI Application
# ═══════════════════════════════════════════════════════════════════════════════

# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: FastAPI initialization)
# Pattern: FastAPI(title, description, version, docs_url, redoc_url, openapi_url, lifespan)
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.VERSION,
    # Conditional documentation URLs based on DEBUG mode
    # ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: conditional-openapi)
    # [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#安全考虑]
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    # ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: lifespan event handlers)
    lifespan=lifespan
)

# ═══════════════════════════════════════════════════════════════════════════════
# Middleware Configuration
# ═══════════════════════════════════════════════════════════════════════════════


# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: BaseHTTPMiddleware)
# [Source: docs/prd/EPIC-21.5-AGENT-RELIABILITY-FIX.md - Story 21.5.1]
# [Source: specs/data/error-response.schema.json]
# ✅ Story 12.J.3: 编码验证中间件
# [Source: specs/data/error-response.schema.json] - 响应格式
# [Source: ADR-009] - 错误处理策略
# [Source: ADR-010] - 日志不使用 emoji
class EncodingValidationMiddleware(BaseHTTPMiddleware):
    """
    Story 12.J.3: 验证请求体 UTF-8 编码.

    在 Pydantic 解析之前验证请求体是有效的 UTF-8，
    对无效编码返回 400 Bad Request 而不是 500。

    Acceptance Criteria:
    - AC1: 无效 UTF-8 请求返回 HTTP 400，不是 500
    - AC2: 有效 UTF-8 请求正常处理 (无性能影响)
    - AC3: 错误响应包含 ENCODING_ERROR 类型
    """

    async def dispatch(self, request: Request, call_next):
        """验证请求体的 UTF-8 编码."""
        # AC2: 仅验证有请求体的方法 (POST, PUT, PATCH)
        if request.method in ("POST", "PUT", "PATCH"):
            content_type = request.headers.get("content-type", "")
            if "application/json" in content_type:
                try:
                    body = await request.body()
                    # 验证 UTF-8 编码
                    body.decode('utf-8')
                except UnicodeDecodeError as e:
                    # [Source: ADR-010] - 日志不使用 emoji，避免 Windows GBK 编码错误
                    logger.warning(
                        f"[Story 12.J.3] Invalid UTF-8 encoding: "
                        f"path={request.url.path}, position={e.start}"
                    )
                    # AC1: 返回 400 而非 500
                    # AC3: 包含 ENCODING_ERROR 类型
                    # [Source: specs/data/error-response.schema.json]
                    # 使用 details (复数) 而非 detail (单数)
                    return JSONResponse(
                        status_code=400,
                        content={
                            "code": 400,
                            "message": "Invalid UTF-8 encoding in request body",
                            "error_type": "ENCODING_ERROR",
                            "details": {
                                "position": e.start,
                                "path": str(request.url.path)
                            }
                        }
                    )
        return await call_next(request)


class CORSExceptionMiddleware(BaseHTTPMiddleware):
    """
    确保500错误也返回CORS头的中间件。

    当未处理的异常发生时，CORSMiddleware 不会被执行，导致 500 响应没有 CORS 头。
    此中间件在 CORSMiddleware 之前捕获异常，确保异常响应也包含 CORS 头。

    [Source: docs/stories/21.5.1.story.md - AC-1, AC-2]
    [Source: docs/stories/story-12.J.5-cors-encoding-safety.md - 编码安全增强]
    """

    def _safe_extract_request_params(self, request: Request) -> dict:
        """
        Story 12.J.5: 安全提取请求参数.

        确保所有字符串都可以安全序列化为 JSON。

        [Source: docs/stories/story-12.J.5-cors-encoding-safety.md - AC2]

        Args:
            request: HTTP 请求对象

        Returns:
            dict: 安全编码的请求参数
        """
        try:
            query_params = dict(request.query_params)
            # 安全化每个值
            safe_params = {}
            for key, value in query_params.items():
                if isinstance(value, str):
                    safe_params[key] = value.encode('utf-8', errors='replace').decode('utf-8')
                else:
                    safe_params[key] = value
            return {
                "path": str(request.url.path),
                "method": request.method,
                "query_params": safe_params,
            }
        except Exception:
            return {
                "path": "[extraction failed]",
                "method": request.method,
                "query_params": {},
            }

    async def dispatch(self, request: Request, call_next):
        """
        处理请求，捕获异常并返回带 CORS 头的响应。

        Args:
            request: HTTP 请求对象
            call_next: 下一个中间件或路由处理函数

        Returns:
            Response: HTTP 响应，包含 CORS 头
        """
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            # ✅ SDD Aligned: specs/data/error-response.schema.json
            # 获取请求的 Origin 头，用于动态设置 CORS
            origin = request.headers.get("origin", "")

            # 检查 origin 是否在允许列表中
            allowed_origin = origin if origin in settings.cors_origins_list else ""

            # 如果没有匹配的 origin，使用默认值 (app://obsidian.md)
            if not allowed_origin and "app://obsidian.md" in settings.cors_origins_list:
                allowed_origin = "app://obsidian.md"

            # ✅ Story 12.J.5: 安全化错误消息
            # [Source: docs/stories/story-12.J.5-cors-encoding-safety.md - AC1, AC2]
            try:
                error_message = str(e)
            except (UnicodeEncodeError, UnicodeDecodeError):
                # 使用 repr() 作为 ASCII 安全的后备
                error_message = repr(e)

            # 确保消息可以安全编码为 JSON
            safe_message = error_message.encode('utf-8', errors='replace').decode('utf-8')

            # ✅ Story 21.5.3 AC-1, AC-2: 生成 bug_id 并记录到 bug_log.jsonl
            # [Source: docs/stories/21.5.3.story.md]
            # ✅ Story 12.J.5: 使用安全参数提取方法
            request_params = self._safe_extract_request_params(request)
            bug_id = bug_tracker.log_error(
                endpoint=str(request.url.path),
                error=e,
                request_params=request_params,
            )

            # ✅ Story 12.J.5: 使用安全消息记录日志，限制长度为 200 字符
            # [Source: ADR-010 - Logging聚合策略]
            logger.error(
                f"Unhandled exception caught by CORSExceptionMiddleware: {type(e).__name__}: {safe_message[:200]} [bug_id={bug_id}]",
                exc_info=True
            )

            return JSONResponse(
                status_code=500,
                content={
                    "code": 500,                      # Required by JSON Schema
                    "message": safe_message[:500],    # ✅ Story 12.J.5: 限制长度为 500 字符
                    "error_type": type(e).__name__,   # Extension field
                    "bug_id": bug_id,                 # ✅ Story 21.5.5 AC-1: 返回 bug_id
                },
                headers={
                    "Access-Control-Allow-Origin": allowed_origin,
                    "Access-Control-Allow-Credentials": "true",
                }
            )


# ⚠️ 中间件注册顺序 (先添加的后执行):
# 1. CORSExceptionMiddleware ← 最外层，捕获所有异常
# 2. EncodingValidationMiddleware ← Story 12.J.3，验证 UTF-8 编码
# 3. CORSMiddleware ← CORS 头处理
# 4. MetricsMiddleware ← 最内层，收集指标
# [Source: docs/stories/21.5.1.story.md - AC-3]
# [Source: docs/stories/story-12.J.3-encoding-validation-middleware.md]
app.add_middleware(CORSExceptionMiddleware)

# ✅ Story 12.J.3: 编码验证中间件
# 在 CORSExceptionMiddleware 之后、CORSMiddleware 之前执行
# 确保无效 UTF-8 请求返回 400 而非触发 500 异常
app.add_middleware(EncodingValidationMiddleware)

# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: CORSMiddleware CORS)
# Pattern: app.add_middleware(CORSMiddleware, allow_origins=[], ...)
# [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#CORS配置]
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Verified from Context7:/prometheus/client_python (topic: Counter Histogram Gauge)
# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: middleware http)
# [Source: docs/stories/17.1.story.md - AC-1]
# Pattern: MetricsMiddleware auto-records method/endpoint/status/response_time
app.add_middleware(MetricsMiddleware)

# ═══════════════════════════════════════════════════════════════════════════════
# Route Registration
# ═══════════════════════════════════════════════════════════════════════════════

# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: include_router prefix)
# Pattern: app.include_router(router, prefix="/api/v1")
app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)

# ═══════════════════════════════════════════════════════════════════════════════
# WebSocket Routes (Story 33.2)
# [Source: docs/stories/33.2.story.md - Task 1]
# [Source: specs/api/parallel-api.openapi.yml#L523-L559]
# ═══════════════════════════════════════════════════════════════════════════════


@app.websocket("/ws/intelligent-parallel/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for intelligent parallel batch processing progress.

    [Source: docs/stories/33.2.story.md - AC1]
    [Source: docs/architecture/decisions/ADR-007-WEBSOCKET-BATCH-PROCESSING.md]

    Args:
        websocket: WebSocket connection
        session_id: Session ID to subscribe to
    """
    await websocket_intelligent_parallel(websocket, session_id)

# ═══════════════════════════════════════════════════════════════════════════════
# Root Endpoint
# ═══════════════════════════════════════════════════════════════════════════════


@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint providing API information.

    Returns basic API metadata including name, version, and documentation URL.

    Returns:
        dict: API information.
    """
    return {
        "message": "Canvas Learning System API",
        "version": settings.VERSION,
        "docs": "/docs" if settings.DEBUG else "disabled",
        "health": f"{settings.API_V1_PREFIX}/health"
    }
