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

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

# Load .env BEFORE any other app imports so os.getenv() works everywhere
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

# ═══════════════════════════════════════════════════════════════════════════════
# Logging Setup — MUST run before any app.* import that may construct a logger
# at module level. Otherwise those loggers fall through to structlog's default
# (ConsoleRenderer) and the first few startup lines escape the JSON pipeline.
# [Source: ADR-010 - Logging聚合策略]
# [Source: openspec/changes/fix-structlog-caplog-compat — Task 2]
# ═══════════════════════════════════════════════════════════════════════════════
from app.core.logging import configure_logging  # noqa: E402

_log_level_name = os.getenv("LOG_LEVEL", "INFO").upper()
configure_logging(level=getattr(logging, _log_level_name, logging.INFO))
logger = logging.getLogger(__name__)

# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: FastAPI CORSMiddleware)
from fastapi import FastAPI, Request, WebSocket  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402
from starlette.middleware.base import BaseHTTPMiddleware  # noqa: E402

# ✅ Story 5.2: Mastery WebSocket endpoint
from app.api.v1.endpoints.mastery_ws import websocket_mastery_endpoint  # noqa: E402
from app.api.v1.endpoints.monitoring import set_alert_manager  # noqa: E402

# ✅ Story 33.2: WebSocket endpoint import
from app.api.v1.endpoints.websocket import (  # noqa: E402
    websocket_intelligent_parallel,
)
from app.api.v1.router import router as api_v1_router  # noqa: E402
from app.config import settings  # noqa: E402
from app.core.bug_tracker import bug_tracker  # noqa: E402
from app.core.litellm_config import register_litellm_callbacks  # noqa: E402

# ✅ Story 7.2: LLM Call Logging & Token Tracking
from app.middleware.cost_tracker import cleanup_cost_tracker, get_cost_tracker  # noqa: E402
from app.middleware.llm_call_logger import llm_call_logger  # noqa: E402
from app.middleware.metrics import MetricsMiddleware  # noqa: E402
from app.services.alert_manager import AlertManager, load_alert_rules_from_yaml  # noqa: E402

# ✅ Story 30.3 Fix: Import MemoryService from canonical singleton location
from app.services.memory_service import cleanup_memory_service, get_memory_service  # noqa: E402
from app.services.notification_channels import create_default_dispatcher  # noqa: E402

# ✅ Story 7.3: Prompt Version Management & Regression Testing
from app.services.prompt_registry import get_prompt_registry  # noqa: E402
from app.services.resource_monitor import get_default_monitor  # noqa: E402


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

    # ✅ Story 7.3: Initialize PromptRegistry (load all prompt templates)
    # [Source: _bmad-output/implementation-artifacts/7-3-prompt-version-regression-test.md]
    try:
        prompt_registry = get_prompt_registry()
        loaded_count = prompt_registry.load_all()
        logger.info(f"[Story 7.3] PromptRegistry loaded {loaded_count} templates")
    except Exception as e:
        logger.warning(f"[Story 7.3] PromptRegistry init failed (non-fatal): {e}")

    # ✅ Story 7.2: Initialize CostTracker and LLM Call Logger
    # [Source: _bmad-output/implementation-artifacts/7-2-llm-logging-token-tracking.md]
    try:
        cost_tracker = await get_cost_tracker()
        await llm_call_logger.start(cost_tracker)
        await cost_tracker.start_rotation()
        register_litellm_callbacks()
        logger.info("[Story 7.2] LLM logging infrastructure initialized")
    except Exception as e:
        logger.warning(f"[Story 7.2] LLM logging init failed (non-fatal): {e}")

    # ✅ Story 30.3 Fix: Pre-warm MemoryService singleton to avoid first-call latency
    # This ensures the first /api/v1/memory/health call is fast (<100ms vs 21s)
    try:
        logger.info("Pre-warming MemoryService singleton...")
        memory_svc = await get_memory_service()
        logger.info("MemoryService pre-warmed successfully")
    except Exception as e:
        memory_svc = None
        logger.warning(f"MemoryService pre-warm failed (non-fatal): {e}")

    # ✅ Epic 4 Feature 4.1: Auto-create Neo4j fulltext index on startup
    # Creates episode_content index for Tier 2 keyword search in search_memories
    try:
        if memory_svc is not None:
            await memory_svc.ensure_fulltext_index()
    except Exception as e:
        logger.warning(f"[Epic 4] Fulltext index setup failed (non-fatal): {e}")

    # ✅ Story 38.1 AC-3: Recover pending LanceDB index operations on startup
    try:
        from app.services.lancedb_index_service import get_lancedb_index_service

        lancedb_idx_svc = get_lancedb_index_service()
        if lancedb_idx_svc:
            idx_result = await lancedb_idx_svc.recover_pending(
                settings.canvas_base_path
            )
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

    # ✅ Story 3.8: Start archive scheduler (24h interval)
    # [Source: _bmad-output/implementation-artifacts/3-8-dialog-archive-async-generation.md#Task 3]
    archive_scheduler = None
    try:
        from app.services.archive_scheduler import get_archive_scheduler

        archive_scheduler = get_archive_scheduler()
        await archive_scheduler.start()
        logger.info("[Story 3.8] Archive scheduler started (24h interval)")
    except Exception as e:
        logger.warning(f"[Story 3.8] Archive scheduler init failed (non-fatal): {e}")

    # ✅ Story 5.7: Register EventBus production handlers
    # [Source: _bmad-output/implementation-artifacts/5-7-eventbus-triconnect.md]
    # Connects FSRS, Graphiti, and RAG subsystems via event-driven architecture.
    try:
        from app.services.event_bus import get_event_bus
        from app.services.event_handlers import register_all_handlers

        event_bus = get_event_bus()
        register_all_handlers(event_bus)

        # Recover any failed Tier 2 events from previous run
        recovered = await event_bus.recover_outbox()
        if recovered > 0:
            logger.info(f"[Story 5.7] EventBus recovered {recovered} outbox events")
        logger.info("[Story 5.7] EventBus handlers registered")
    except Exception as e:
        logger.warning(
            f"[Story 5.7] EventBus handler registration failed (non-fatal): {e}"
        )

    # ✅ Story 5.6: Register signal adapters for mastery fusion engine
    try:
        from app.services.mastery_engine import MasteryEngine, set_mastery_engine
        from app.services.mastery_fusion import MasteryFusionEngine
        from app.services.signal_registry import (
            BKTMasterySignal,
            CalibrationBiasSignal,
            ExamScoreSignal,
            FSRSRetrievabilitySignal,
            SelfConfidenceSignal,
            SignalRegistry,
        )

        mastery_engine = MasteryEngine()
        signal_registry = SignalRegistry()

        # Register 5 MVP signal adapters
        signal_registry.register(BKTMasterySignal(mastery_engine, None))
        signal_registry.register(FSRSRetrievabilitySignal(mastery_engine))
        signal_registry.register(ExamScoreSignal())
        signal_registry.register(CalibrationBiasSignal())
        signal_registry.register(SelfConfidenceSignal())

        # Attach fusion engine to mastery engine
        fusion_engine = MasteryFusionEngine(signal_registry)
        mastery_engine.set_fusion_engine(fusion_engine)

        # Store in app state AND set as global singleton for DI
        set_mastery_engine(
            mastery_engine
        )  # All get_mastery_engine() calls now return this instance
        app.state.mastery_engine = mastery_engine
        app.state.signal_registry = signal_registry
        app.state.fusion_engine = fusion_engine
        logger.info(
            f"[Story 5.6] Signal registry initialized with "
            f"{signal_registry.signal_count} adapters, fusion engine attached"
        )
    except Exception as e:
        logger.warning(
            f"[Story 5.6] Signal adapter registration failed (non-fatal): {e}"
        )

    # Phase 2: GraphitiEpisodeWorker — real Graphiti integration
    from app.services.episode_worker import get_episode_worker

    episode_worker = get_episode_worker()
    try:
        graphiti_ready = await episode_worker.initialize_graphiti(
            neo4j_uri=settings.NEO4J_URI,
            neo4j_user=settings.NEO4J_USER,
            neo4j_password=settings.NEO4J_PASSWORD,
            google_api_key=settings.GOOGLE_API_KEY,
        )
        if graphiti_ready:
            await episode_worker.start()
            app.state.episode_worker = episode_worker
            logger.info("[Phase 2] GraphitiEpisodeWorker started")
        else:
            app.state.episode_worker = episode_worker
            logger.warning(
                "[Phase 2] GraphitiEpisodeWorker in degraded mode (no graphiti client)"
            )
    except Exception as e:
        app.state.episode_worker = None
        logger.warning(f"[Phase 2] GraphitiEpisodeWorker init failed (non-fatal): {e}")

    # ✅ Story 2.1 Phase 1.6: Eager-build wikilink graph on startup
    # Eliminates "Graph version: unbuilt / wikilink_graph_not_built" degraded state
    # observed by users when first invoking chat-with-context after backend restart.
    # Pattern verified by 4 parallel Explore agents (FastAPI lifespan / Obsidian PKM
    # ecosystem / RAG indexing / Dumb-client philosophy) — all converge on
    # server-side eager init over plugin-side self-healing retry.
    try:
        from app.services.wikilink_graph_service import get_wikilink_graph_service

        wikilink_svc = get_wikilink_graph_service()
        wl_result = await wikilink_svc.build(settings.canvas_base_path)
        logger.info(
            f"[Story 2.1] Wikilink graph eager-built: "
            f"{wl_result['total_nodes']} nodes, "
            f"{wl_result['total_edges']} edges, "
            f"{wl_result['build_time_ms']}ms"
        )
    except Exception as e:
        logger.warning(
            f"[Story 2.1] Wikilink graph eager-build failed (non-fatal, "
            f"endpoints will degrade until manual /wikilink/build): {e}"
        )

    # ✅ Story 2.2 Phase A: Background eager-init LanceDB singleton + BGEM3 model
    # Avoids per-request BGEM3 cold-start (4 min in docker) blocking enrich-context.
    # Background task: 不 block startup，4 min 内后台完成；首批 request 仍触发降级，
    # init 完成后 subsequent request 命中缓存 0.x s。
    async def _eager_init_lancedb_singleton() -> None:
        try:
            from app.api.v1.endpoints.chat import _get_supp_lancedb_client

            client = await _get_supp_lancedb_client(init_timeout=600.0)
            if client is not None:
                logger.info(
                    "[Story 2.2 Phase A] LanceDB singleton eager-init complete — supplementary search warm"
                )
            else:
                logger.warning(
                    "[Story 2.2 Phase A] LanceDB singleton eager-init returned None — supplementary will degrade per-request"
                )
        except Exception as e:  # noqa: BLE001  background task 失败不影响主 service
            logger.warning(
                f"[Story 2.2 Phase A] LanceDB singleton eager-init exception (non-fatal): {e}"
            )

    asyncio.create_task(_eager_init_lancedb_singleton())
    logger.info("[Story 2.2 Phase A] LanceDB singleton background init dispatched")

    # ✅ Fix-E1 (2026-06-10): 搭车扫 vault markdown, 把节点 frontmatter relationships[]
    # 同步成 Neo4j CANVAS_EDGE{label=原因}, 让检验白板 _get_edge_reasons 能拿到"用户为什么
    # 拉出这个节点"的原因 (GAP-E: 降级后 .canvas 边同步失效, 原因边写入路径缺失)。
    # ⚠️ Graphiti-native 重构 Phase 4 将把此服务降级为 canvas_projection_sync (仅 UI 投影)。
    try:
        from app.services.node_relationship_sync_service import (
            get_node_relationship_sync_service,
        )

        rel_svc = get_node_relationship_sync_service()
        rel_result = await rel_svc.sync(settings.canvas_base_path)
        logger.info(
            f"[Fix-E1] 节点原因边同步: "
            f"{rel_result['nodes_with_relationships']} nodes, "
            f"{rel_result['edges_synced']} edges, "
            f"{rel_result['failed']} failed"
        )
    except Exception as e:
        logger.warning(f"[Fix-E1] 节点原因边同步 failed (non-fatal): {e}")

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

    # ✅ Story 7.2: Cleanup LLM logging infrastructure
    try:
        await llm_call_logger.stop()
        await cleanup_cost_tracker()
        logger.info("[Story 7.2] LLM logging infrastructure cleaned up")
    except Exception as e:
        logger.warning(f"[Story 7.2] LLM logging cleanup failed: {e}")

    # ✅ Story 3.8: Stop archive scheduler
    if archive_scheduler is not None:
        try:
            await archive_scheduler.stop()
            logger.info("[Story 3.8] Archive scheduler stopped")
        except Exception as e:
            logger.warning(f"[Story 3.8] Archive scheduler stop failed: {e}")

    # Phase 2: Stop episode worker gracefully
    try:
        from app.services.episode_worker import cleanup_episode_worker

        await cleanup_episode_worker()
        logger.info("[Phase 2] GraphitiEpisodeWorker stopped")
    except Exception as e:
        logger.warning(f"[Phase 2] Episode worker cleanup failed: {e}")

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
    lifespan=lifespan,
)


# Round-5 A1 (ChatGPT V4 + cross-check D 部分成立):
# 旧: openapi.json 缺 securitySchemes — 实现完整但 spec 没声明 → 第三方工具无法推导鉴权
# 新: custom OpenAPI schema 加 InternalApiKey APIKey scheme + 全局 security requirement
# 影响: openapi.json + /docs Swagger UI 自动显示 X-CLS-Internal-Key header 鉴权契约
def _custom_openapi():
    """Custom OpenAPI schema with securitySchemes declaration (Round-5 A1)."""
    from fastapi.openapi.utils import get_openapi

    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=settings.PROJECT_DESCRIPTION,
        routes=app.routes,
    )
    components = openapi_schema.setdefault("components", {})
    components["securitySchemes"] = {
        "InternalApiKey": {
            "type": "apiKey",
            "in": "header",
            "name": "X-CLS-Internal-Key",
            "description": (
                "Internal API key for backend authentication. "
                "Required for /chat/*, /sync/*, /system/* endpoints in production mode (DEBUG=False). "
                "DEBUG=True mode allows requests without key (dev_bypass with warning log). "
                "See backend/app/security.py:require_internal_api_key for fail-closed matrix."
            ),
        }
    }
    # Global security requirement (per-endpoint can override)
    openapi_schema["security"] = [{"InternalApiKey": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = _custom_openapi  # type: ignore[method-assign]

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
                    body.decode("utf-8")
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
                                "path": str(request.url.path),
                            },
                        },
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
                    safe_params[key] = value.encode("utf-8", errors="replace").decode(
                        "utf-8"
                    )
                else:
                    safe_params[key] = value
            return {
                "path": str(request.url.path),
                "method": request.method,
                "query_params": safe_params,
            }
        except (ValueError, TypeError, AttributeError, UnicodeDecodeError):
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
            safe_message = error_message.encode("utf-8", errors="replace").decode(
                "utf-8"
            )

            # ✅ Story 21.5.3 AC-1, AC-2: 生成 bug_id 并记录到 bug_log.jsonl
            # [Source: docs/stories/21.5.3.story.md]
            # ✅ Story 12.J.5: 使用安全参数提取方法
            request_params = self._safe_extract_request_params(request)
            bug_id = bug_tracker.log_error(
                endpoint=str(request.url.path),
                error=e,
                request_params=request_params,
                request_id=getattr(request.state, "request_id", None),
            )

            # ✅ Story 12.J.5: 使用安全消息记录日志，限制长度为 200 字符
            # [Source: ADR-010 - Logging聚合策略]
            logger.error(
                f"Unhandled exception caught by CORSExceptionMiddleware: {type(e).__name__}: {safe_message[:200]} [bug_id={bug_id}]",
                exc_info=True,
            )

            return JSONResponse(
                status_code=500,
                content={
                    "code": 500,  # Required by JSON Schema
                    "message": safe_message[
                        :500
                    ],  # ✅ Story 12.J.5: 限制长度为 500 字符
                    "error_type": type(e).__name__,  # Extension field
                    "bug_id": bug_id,  # ✅ Story 21.5.5 AC-1: 返回 bug_id
                },
                headers={
                    "Access-Control-Allow-Origin": allowed_origin,
                    "Access-Control-Allow-Credentials": "true",
                },
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
# MCP Server Registration (Story 3.2)
# [Source: _bmad-output/implementation-artifacts/3-2-mcp-tool-exposure-backend-api.md#Task 1]
# [Source: _decisions/ADR-001-dialogue-engine.md — MCP injection]
# ═══════════════════════════════════════════════════════════════════════════════

try:
    from app.mcp import setup_mcp_server

    setup_mcp_server(app)
except (ImportError, AttributeError) as e:
    logger.warning(f"[Story 3.2] MCP server setup skipped: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# WebSocket Routes (Story 33.2)
# [Source: docs/stories/33.2.story.md - Task 1]
# [Source: specs/api/parallel-api.openapi.yml#L523-L559]
# ═══════════════════════════════════════════════════════════════════════════════


@app.websocket("/ws/intelligent-parallel/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for intelligent parallel batch processing progress.

    Round-23 Story 7.5: 加入 INTERNAL_API_KEY 查询参数鉴权 (?token=xxx).
    fail-closed 矩阵与 REST require_internal_api_key 一致.

    [Source: docs/stories/33.2.story.md - AC1]
    [Source: docs/architecture/decisions/ADR-007-WEBSOCKET-BATCH-PROCESSING.md]

    Args:
        websocket: WebSocket connection
        session_id: Session ID to subscribe to
    """
    from app.security import verify_websocket_internal_key

    if not await verify_websocket_internal_key(websocket):
        return  # close already invoked by verify helper

    await websocket_intelligent_parallel(websocket, session_id)


# ═══════════════════════════════════════════════════════════════════════════════
# WebSocket Routes (Story 5.2 - Mastery Updates)
# [Source: obsidian-canvas-learning/src/services/api-client.ts - connectWebSocket]
# [Source: _bmad-output/implementation-artifacts/5-2-node-color-mastery-visualization.md]
# ═══════════════════════════════════════════════════════════════════════════════


@app.websocket("/ws")
async def websocket_mastery(websocket: WebSocket):
    """
    WebSocket endpoint for real-time mastery update broadcasts.

    Round-23 Story 7.5: 加入 INTERNAL_API_KEY 查询参数鉴权 (?token=xxx).
    Obsidian 前端需在 connect URL 末尾追加 token, 否则连接被 close 1008.

    The Obsidian frontend connects to ws://host:8001/ws?token=xxx and receives
    mastery_update messages whenever a node's mastery state changes.
    This enables live node color updates without polling.

    [Source: api-client.ts connectWebSocket() / handleWebSocketMessage()]

    Args:
        websocket: WebSocket connection from the Obsidian plugin
    """
    from app.security import verify_websocket_internal_key

    if not await verify_websocket_internal_key(websocket):
        return  # close already invoked by verify helper

    await websocket_mastery_endpoint(websocket)


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
        "health": f"{settings.API_V1_PREFIX}/health",
    }
