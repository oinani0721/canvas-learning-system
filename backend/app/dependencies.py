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
# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: dependency injection Depends)
# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: dependencies with yield cleanup)
# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: settings BaseSettings lru_cache)
from __future__ import annotations

import logging
from functools import lru_cache
from typing import TYPE_CHECKING, Annotated, AsyncGenerator

if TYPE_CHECKING:
    from .services.rollback_service import RollbackService

from fastapi import Depends

from .config import Settings
from .services.agent_service import AgentService
from .services.background_task_manager import BackgroundTaskManager
from .services.canvas_service import CanvasService
from .services.context_enrichment_service import ContextEnrichmentService
from .services.review_service import ReviewService
from .services.textbook_context_service import TextbookContextConfig, TextbookContextService
from .services.cross_canvas_service import CrossCanvasService, get_cross_canvas_service

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
# BackgroundTaskManager Dependency (Singleton)
# =============================================================================

def get_task_manager() -> BackgroundTaskManager:
    """
    Get BackgroundTaskManager singleton instance.

    The BackgroundTaskManager uses a singleton pattern internally,
    so this always returns the same instance.

    Returns:
        BackgroundTaskManager: Singleton task manager instance
    """
    logger.debug("Getting BackgroundTaskManager instance")
    return BackgroundTaskManager.get_instance()


# Type alias for BackgroundTaskManager dependency
TaskManagerDep = Annotated[BackgroundTaskManager, Depends(get_task_manager)]


# =============================================================================
# ReviewService Dependency (Chained: depends on Settings AND CanvasService)
# =============================================================================

# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: chained dependencies)
async def get_review_service(
    canvas_service: CanvasServiceDep,
    task_manager: TaskManagerDep
) -> AsyncGenerator[ReviewService, None]:
    """
    Get ReviewService instance with automatic resource cleanup.

    This is a chained dependency - it depends on CanvasService and TaskManager.
    FastAPI will resolve the dependency chain automatically.

    ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: chained dependencies)

    Dependency Chain:
        get_settings() → settings
        get_canvas_service(settings) → canvas_service
        get_task_manager() → task_manager
        get_review_service(canvas_service, task_manager) → review_service

    Args:
        canvas_service: CanvasService instance (injected via Depends)
        task_manager: BackgroundTaskManager instance (injected via Depends)

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
        canvas_service=canvas_service,
        task_manager=task_manager
    )
    try:
        yield service
    finally:
        await service.cleanup()
        logger.debug("ReviewService cleanup completed")


# Type alias for ReviewService dependency
ReviewServiceDep = Annotated[ReviewService, Depends(get_review_service)]


# =============================================================================
# ContextEnrichmentService Dependency (Story 25.2 + Story 25.3)
# [Source: docs/stories/25.2.story.md#TextbookContextService-Integration]
# [Source: docs/stories/25.3.story.md#Exercise-Lecture-Canvas-Association]
# =============================================================================

# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: chained dependencies)
async def get_context_enrichment_service(
    canvas_service: CanvasServiceDep,
    settings: SettingsDep
) -> AsyncGenerator[ContextEnrichmentService, None]:
    """
    Get ContextEnrichmentService instance with TextbookContextService and CrossCanvasService integration.

    This is a chained dependency that combines Canvas service with textbook context
    and cross-canvas lecture references.
    Uses 3-second timeout for textbook queries per Story 25.2 AC4.

    ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: chained dependencies)

    Dependency Chain:
        get_settings() → settings
        get_canvas_service(settings) → canvas_service
        get_cross_canvas_service() → cross_canvas_service
        get_context_enrichment_service(canvas_service, settings) → context_enrichment_service

    Args:
        canvas_service: CanvasService instance (injected via Depends)
        settings: Application settings (injected via Depends)

    Yields:
        ContextEnrichmentService: Context enrichment service with textbook and cross-canvas support

    Example:
        ```python
        @router.post("/decompose/basic")
        async def decompose_basic(
            request: DecomposeRequest,
            context_service: ContextEnrichmentService = Depends(get_context_enrichment_service)
        ):
            enriched = await context_service.enrich_with_adjacent_nodes(...)
            return result
        ```

    [Source: docs/stories/25.2.story.md#Dev-Notes]
    [Source: docs/stories/25.3.story.md#Task-4]
    [AC4: Timeout fallback 3 seconds]
    """
    logger.debug("Creating ContextEnrichmentService instance with TextbookContextService and CrossCanvasService")

    # AC4: 3-second timeout for textbook queries (Story 25.2)
    textbook_config = TextbookContextConfig(timeout=3.0)
    textbook_service = TextbookContextService(
        canvas_base_path=settings.canvas_base_path,
        config=textbook_config
    )

    # Story 25.3: Get CrossCanvasService singleton for cross-canvas context
    cross_canvas_service = get_cross_canvas_service()

    service = ContextEnrichmentService(
        canvas_service=canvas_service,
        textbook_service=textbook_service,
        cross_canvas_service=cross_canvas_service
    )

    try:
        yield service
    finally:
        logger.debug("ContextEnrichmentService cleanup completed")


# Type alias for ContextEnrichmentService dependency
ContextEnrichmentServiceDep = Annotated[ContextEnrichmentService, Depends(get_context_enrichment_service)]


# =============================================================================
# CrossCanvasService Dependency (Story 25.3)
# [Source: docs/stories/25.3.story.md#Exercise-Lecture-Canvas-Association]
# =============================================================================

def get_cross_canvas_service_dep() -> CrossCanvasService:
    """
    Get CrossCanvasService singleton instance.

    The CrossCanvasService uses a singleton pattern for in-memory storage,
    ensuring consistent state across all requests.

    [Source: Story 25.3 - Exercise-Lecture Canvas Association]

    Returns:
        CrossCanvasService: Singleton cross-canvas service instance
    """
    logger.debug("Getting CrossCanvasService instance")
    return get_cross_canvas_service()


# Type alias for CrossCanvasService dependency
CrossCanvasServiceDep = Annotated[CrossCanvasService, Depends(get_cross_canvas_service_dep)]


# =============================================================================
# RollbackService Dependency (Story 18.5)
# [Source: docs/architecture/rollback-recovery-architecture.md]
# =============================================================================

# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: dependencies with yield cleanup)
async def get_rollback_service(
    settings: SettingsDep
) -> AsyncGenerator["RollbackService", None]:
    """
    Get RollbackService instance with automatic resource cleanup.

    Uses yield syntax to support resource cleanup after request completion.
    Configures the service using application settings.

    ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: dependencies-with-yield)

    Args:
        settings: Application settings (injected via Depends)

    Yields:
        RollbackService: Rollback operations service instance

    Example:
        ```python
        @router.post("/rollback")
        async def execute_rollback(
            request: RollbackRequest,
            service: RollbackService = Depends(get_rollback_service)
        ):
            return await service.rollback(request)
        ```

    [Source: docs/stories/18.5.story.md#Dev-Notes]
    [Source: docs/architecture/rollback-recovery-architecture.md]
    """
    # Lazy import to avoid circular dependencies
    from .services.rollback_service import RollbackService

    logger.debug("Creating RollbackService instance")
    service = RollbackService(
        storage_path=settings.rollback_storage_path,
        history_limit=settings.rollback_history_limit,
        snapshot_interval=settings.rollback_snapshot_interval,
        max_snapshots=settings.rollback_max_snapshots,
        graphiti_timeout_ms=settings.rollback_graphiti_timeout_ms,
        enable_graphiti_sync=settings.rollback_enable_graphiti_sync,
        enable_auto_backup=settings.rollback_enable_auto_backup,
    )
    try:
        yield service
    finally:
        await service.cleanup()
        logger.debug("RollbackService cleanup completed")


# Lazy type alias for RollbackService dependency (forward reference)
# Note: RollbackService is imported lazily in get_rollback_service
def _get_rollback_service_dep():
    """Helper to create RollbackServiceDep with lazy import."""
    from .services.rollback_service import RollbackService
    return Annotated[RollbackService, Depends(get_rollback_service)]


# =============================================================================
# Exported Dependencies for easy import
# =============================================================================

__all__ = [
    # Functions
    "get_settings",
    "get_canvas_service",
    "get_agent_service",
    "get_task_manager",
    "get_review_service",
    "get_context_enrichment_service",
    "get_cross_canvas_service_dep",
    "get_rollback_service",
    # Type Aliases (Annotated types for cleaner endpoint signatures)
    "SettingsDep",
    "CanvasServiceDep",
    "AgentServiceDep",
    "TaskManagerDep",
    "ReviewServiceDep",
    "ContextEnrichmentServiceDep",
    "CrossCanvasServiceDep",
]
