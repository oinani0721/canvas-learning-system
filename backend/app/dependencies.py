# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: dependency injection Depends)
# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: dependencies with yield cleanup)
# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: settings BaseSettings lru_cache)
"""
Dependency Injection System for Canvas Learning System.

This module provides all dependency provider functions for the FastAPI application.
Dependencies are used to inject services into API endpoints with proper lifecycle management.

Dependency Graph:
    Settings (singleton, @lru_cache)
        ↓
    ┌───┴───┐
    ↓       ↓
    CanvasService  AgentService
        ↓
    ReviewService

[Source: docs/stories/15.3.story.md#Dev-Notes]
[Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#依赖注入架构]
"""
from functools import lru_cache
from typing import Annotated, AsyncGenerator
import logging

from fastapi import Depends

from .config import Settings
from .services.canvas_service import CanvasService
from .services.agent_service import AgentService
from .services.review_service import ReviewService

logger = logging.getLogger(__name__)


# =============================================================================
# Settings Dependency (Singleton)
# =============================================================================

# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: settings BaseSettings lru_cache)
# Using @lru_cache ensures Settings is instantiated only once
@lru_cache
def get_settings() -> Settings:
    """
    Get cached Settings instance (singleton pattern).

    Uses @lru_cache to ensure the Settings object is created only once,
    preventing repeated reads from environment variables or .env file.
    This is the recommended pattern from FastAPI documentation.

    ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: settings lru_cache)

    Returns:
        Settings: Cached application settings instance

    Example:
        ```python
        @router.get("/info")
        async def info(settings: Settings = Depends(get_settings)):
            return {"app_name": settings.app_name}
        ```

    [Source: docs/stories/15.3.story.md#Dev-Notes - 示例1: 基础依赖函数]
    """
    logger.debug("Creating Settings instance (singleton)")
    return Settings()


# Type alias for Settings dependency
# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: Annotated Depends)
SettingsDep = Annotated[Settings, Depends(get_settings)]


# =============================================================================
# CanvasService Dependency (with yield for resource cleanup)
# =============================================================================

# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: dependencies with yield cleanup)
async def get_canvas_service(
    settings: SettingsDep
) -> AsyncGenerator[CanvasService, None]:
    """
    Get CanvasService instance with automatic resource cleanup.

    Uses yield syntax to support resource cleanup after request completion.
    The service is created per-request and cleaned up in the finally block.

    ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: dependencies-with-yield)

    Args:
        settings: Application settings (injected via Depends)

    Yields:
        CanvasService: Canvas operations service instance

    Example:
        ```python
        @router.get("/{canvas_name}")
        async def read_canvas(
            canvas_name: str,
            service: CanvasService = Depends(get_canvas_service)
        ):
            return await service.read_canvas(canvas_name)
        ```

    [Source: docs/stories/15.3.story.md#Dev-Notes - 示例2: 带yield的依赖]
    [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#依赖注入设计]
    """
    logger.debug("Creating CanvasService instance")
    service = CanvasService(canvas_base_path=settings.canvas_base_path)
    try:
        yield service
    finally:
        # ✅ Verified cleanup pattern from Context7:/websites/fastapi_tiangolo
        await service.cleanup()
        logger.debug("CanvasService cleanup completed")


# Type alias for CanvasService dependency
CanvasServiceDep = Annotated[CanvasService, Depends(get_canvas_service)]


# =============================================================================
# AgentService Dependency (with yield for resource cleanup)
# =============================================================================

# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: dependencies with yield cleanup)
async def get_agent_service(
    settings: SettingsDep
) -> AsyncGenerator[AgentService, None]:
    """
    Get AgentService instance with automatic resource cleanup.

    Uses yield syntax to support resource cleanup after request completion.
    The service is created per-request and cleaned up in the finally block.

    ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: dependencies-with-yield)

    Args:
        settings: Application settings (injected via Depends)

    Yields:
        AgentService: Agent call service instance

    Example:
        ```python
        @router.post("/decompose/basic")
        async def decompose_basic(
            request: DecomposeRequest,
            service: AgentService = Depends(get_agent_service)
        ):
            return await service.decompose_basic(...)
        ```

    [Source: docs/stories/15.3.story.md#Dev-Notes - 示例3: 链式依赖]
    [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#依赖注入设计]
    """
    logger.debug("Creating AgentService instance")
    # AgentService may use API keys from settings in future
    service = AgentService()
    try:
        yield service
    finally:
        await service.cleanup()
        logger.debug("AgentService cleanup completed")


# Type alias for AgentService dependency
AgentServiceDep = Annotated[AgentService, Depends(get_agent_service)]


# =============================================================================
# ReviewService Dependency (Chained: depends on Settings AND CanvasService)
# =============================================================================

# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: chained dependencies)
async def get_review_service(
    settings: SettingsDep,
    canvas_service: CanvasServiceDep
) -> AsyncGenerator[ReviewService, None]:
    """
    Get ReviewService instance with automatic resource cleanup.

    This is a chained dependency - it depends on both Settings and CanvasService.
    FastAPI will resolve the dependency chain automatically.

    ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: chained dependencies)

    Dependency Chain:
        get_settings() → settings
        get_canvas_service(settings) → canvas_service
        get_review_service(settings, canvas_service) → review_service

    Args:
        settings: Application settings (injected via Depends)
        canvas_service: CanvasService instance (injected via Depends)

    Yields:
        ReviewService: Review and verification canvas service instance

    Example:
        ```python
        @router.post("/generate")
        async def generate_review(
            request: GenerateReviewRequest,
            service: ReviewService = Depends(get_review_service)
        ):
            return await service.generate_verification_canvas(...)
        ```

    [Source: docs/stories/15.3.story.md#Dev-Notes - 示例3: 链式依赖]
    [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#依赖注入设计]
    """
    logger.debug("Creating ReviewService instance (chained dependency)")
    service = ReviewService(
        canvas_base_path=settings.canvas_base_path,
        canvas_service=canvas_service
    )
    try:
        yield service
    finally:
        await service.cleanup()
        logger.debug("ReviewService cleanup completed")


# Type alias for ReviewService dependency
ReviewServiceDep = Annotated[ReviewService, Depends(get_review_service)]


# =============================================================================
# Exported Dependencies for easy import
# =============================================================================

__all__ = [
    # Functions
    "get_settings",
    "get_canvas_service",
    "get_agent_service",
    "get_review_service",
    # Type Aliases (Annotated types for cleaner endpoint signatures)
    "SettingsDep",
    "CanvasServiceDep",
    "AgentServiceDep",
    "ReviewServiceDep",
]
