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
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.endpoints.monitoring import set_alert_manager
from app.api.v1.router import router as api_v1_router
from app.config import settings
from app.core.logging import setup_logging
from app.middleware.metrics import MetricsMiddleware
from app.services.alert_manager import AlertManager, load_alert_rules_from_yaml
from app.services.notification_channels import create_default_dispatcher
from app.services.resource_monitor import get_default_monitor

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

    yield  # Application runs here

    # Shutdown
    logger.info(f"Shutting down {settings.PROJECT_NAME}...")

    # ✅ Stop alert manager gracefully
    await alert_manager.stop()
    logger.info("Alert manager stopped")

    # ✅ Stop resource monitoring gracefully
    await resource_monitor.stop_background_collection()
    logger.info("Resource monitoring stopped")

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
