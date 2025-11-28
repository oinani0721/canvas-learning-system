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

from app.config import settings
from app.core.logging import setup_logging
from app.api.v1.router import router as api_v1_router

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

    yield  # Application runs here

    # Shutdown
    logger.info(f"Shutting down {settings.PROJECT_NAME}...")

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

