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
from typing import TYPE_CHECKING, Annotated, AsyncGenerator, Optional

if TYPE_CHECKING:
    from .services.rollback_service import RollbackService

from fastapi import Depends

from .clients.gemini_client import GeminiClient
from .config import Settings
from .services.agent_service import AgentService
from .services.background_task_manager import BackgroundTaskManager
from .services.canvas_service import CanvasService
from .services.context_enrichment_service import ContextEnrichmentService
from .services.cross_canvas_service import CrossCanvasService, get_cross_canvas_service
from .services.rag_service import get_rag_service
from .services.review_service import ReviewService
from .services.textbook_context_service import TextbookContextConfig, TextbookContextService
from .services.verification_service import VerificationService

# Story 36.1: Unified GraphitiClient Architecture
from .clients.neo4j_client import Neo4jClient, get_neo4j_client
from .clients.graphiti_client import GraphitiEdgeClient

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

    # P0 Fix: Inject MemoryService for Story 36.3/36.4 edge sync to Neo4j
    # Import from canonical singleton in memory_service.py (not endpoint)
    memory_client = None
    try:
        from app.services.memory_service import get_memory_service as _get_memory_svc
        memory_client = await _get_memory_svc()
    except Exception as e:
        logger.warning(f"MemoryService not available for CanvasService edge sync: {e}")

    service = CanvasService(
        canvas_base_path=settings.canvas_base_path,
        memory_client=memory_client
    )
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
    settings: SettingsDep,
    canvas_service: CanvasServiceDep,  # ✅ FIX-Canvas-Write: 注入 CanvasService
    neo4j_client: Neo4jClientDep  # Story 36.7: 注入 Neo4jClient
) -> AsyncGenerator[AgentService, None]:
    """
    Get AgentService instance with automatic resource cleanup.

    Uses yield syntax to support resource cleanup after request completion.
    The service is created per-request and cleaned up in the finally block.

    ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: dependencies-with-yield)

    Args:
        settings: Application settings (injected via Depends)
        canvas_service: CanvasService instance for writing nodes to Canvas
        neo4j_client: Neo4jClient instance for learning memory queries (Story 36.7)

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
    [Source: FIX-Canvas-Write: Backend直接写入Canvas文件]
    [Source: docs/stories/36.7.story.md - AC1 Neo4jClient注入]
    """
    logger.debug("Creating AgentService instance")

    # Create GeminiClient with settings from configuration
    # [FIX] Epic 21.5 Bug #1: GeminiClient was not being created and injected
    gemini_client = None
    if settings.AI_API_KEY:
        try:
            gemini_client = GeminiClient(
                api_key=settings.AI_API_KEY,
                model=settings.AI_MODEL_NAME,
                base_url=settings.AI_BASE_URL if settings.AI_BASE_URL else None
            )
            logger.info(f"GeminiClient created: model={settings.AI_MODEL_NAME}, "
                       f"provider={settings.AI_PROVIDER}")
        except Exception as e:
            logger.error(f"Failed to create GeminiClient: {e}")
    else:
        logger.warning("AI_API_KEY not configured, AgentService will not have AI capabilities")

    # Story 36.11: Inject LearningMemoryClient for memory fallback when Neo4j unavailable
    memory_client = None
    try:
        from .clients.graphiti_client import get_learning_memory_client
        memory_client = get_learning_memory_client()
        logger.debug("LearningMemoryClient injected into AgentService")
    except Exception as e:
        logger.warning(f"LearningMemoryClient not available for AgentService: {e}")

    # ✅ FIX-Canvas-Write: Pass canvas_service to AgentService for direct Canvas writes
    # Story 36.7: Pass neo4j_client to AgentService for learning memory queries
    # Story 36.11: Pass memory_client for fallback when Neo4j unavailable
    service = AgentService(
        gemini_client=gemini_client,
        memory_client=memory_client,  # Story 36.11: 注入 LearningMemoryClient
        canvas_service=canvas_service,  # ✅ FIX: 注入 canvas_service
        neo4j_client=neo4j_client  # Story 36.7: 注入 Neo4jClient
    )
    logger.debug("AgentService created with CanvasService, Neo4jClient, and LearningMemoryClient")

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
    task_manager: TaskManagerDep,
    settings: SettingsDep
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
    # Story 32.8 AC-32.8.3 + AC-32.8.4: Unified FSRSManager factory
    # Checks USE_FSRS setting and creates FSRSManager via single path
    fsrs_manager = None
    try:
        from .services.review_service import create_fsrs_manager
        fsrs_manager = create_fsrs_manager(settings)
    except Exception as e:
        logger.warning(f"FSRSManager DI creation failed, ReviewService will auto-create: {e}")

    # Story 34.8 AC2: Explicitly inject graphiti_client (was previously missing)
    # Uses get_graphiti_temporal_client() singleton — returns None if unavailable
    graphiti_client = None
    try:
        graphiti_client = get_graphiti_temporal_client()
        if graphiti_client:
            logger.debug("GraphitiTemporalClient injected into ReviewService for history queries")
        else:
            logger.warning(
                "Graphiti client not available for ReviewService, "
                "history will use FSRS fallback"
            )
    except Exception as e:
        logger.warning(f"Failed to get graphiti_client for ReviewService: {e}")

    logger.debug("Creating ReviewService instance (chained dependency)")
    service = ReviewService(
        canvas_service=canvas_service,
        task_manager=task_manager,
        graphiti_client=graphiti_client,
        fsrs_manager=fsrs_manager
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

    # P1 Fix: Inject LearningMemoryClient for Graphiti learning memory enrichment
    # Without this, ContextEnrichmentService._search_graphiti_relations() always returns []
    graphiti_service = None
    try:
        from .clients.graphiti_client import get_learning_memory_client
        graphiti_service = get_learning_memory_client()
        logger.debug("LearningMemoryClient injected into ContextEnrichmentService")
    except Exception as e:
        logger.warning(f"LearningMemoryClient not available for context enrichment: {e}")

    service = ContextEnrichmentService(
        canvas_service=canvas_service,
        textbook_service=textbook_service,
        cross_canvas_service=cross_canvas_service,
        graphiti_service=graphiti_service  # P1 Fix: Enable Graphiti learning memory context
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
# VerificationService Dependency (Story 24.5)
# [Source: docs/stories/24.5.story.md#Dev-Notes]
# =============================================================================

# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: chained dependencies)
async def get_verification_service(
    settings: SettingsDep,
    canvas_service: CanvasServiceDep  # P0 Fix: Inject CanvasService for concept extraction
) -> AsyncGenerator[VerificationService, None]:
    """
    Get VerificationService instance with RAG context injection.

    This is a chained dependency that integrates RAGService, CrossCanvasService,
    and TextbookContextService for intelligent verification canvas generation.

    Story 24.5 Integration:
    - RAGService for learning history and context
    - CrossCanvasService for cross-canvas relationships
    - TextbookContextService for textbook references

    ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: chained dependencies)

    Dependency Chain:
        get_settings() → settings
        get_rag_service() → rag_service
        get_cross_canvas_service() → cross_canvas_service
        TextbookContextService(settings) → textbook_service
        get_verification_service(...) → verification_service

    Args:
        settings: Application settings (injected via Depends)

    Yields:
        VerificationService: Verification canvas service with RAG integration

    Example:
        ```python
        @router.post("/verification/start")
        async def start_verification(
            request: StartVerificationRequest,
            service: VerificationService = Depends(get_verification_service)
        ):
            return await service.start_session(...)
        ```

    [Source: docs/stories/24.5.story.md#Dev-Notes]
    [AC5: Graceful degradation - services are optional]
    """
    logger.debug("Creating VerificationService instance with RAG integration")

    # Get RAG service (singleton)
    rag_service = get_rag_service()

    # Get CrossCanvas service (singleton)
    cross_canvas_service = get_cross_canvas_service()

    # Story 31.A.1 AC-31.A.1.1: Get GraphitiTemporalClient singleton
    # [Source: docs/stories/31.A.1.story.md#AC-31.A.1.1]
    graphiti_client = get_graphiti_temporal_client()
    if graphiti_client:
        logger.debug("GraphitiTemporalClient injected into VerificationService")
    else:
        logger.warning(
            "GraphitiTemporalClient not available - "
            "verification question deduplication will be disabled"
        )

    # Create TextbookContext service
    # Story 24.5 AC4: Textbook context with timeout
    textbook_config = TextbookContextConfig(timeout=3.0)
    textbook_service = TextbookContextService(
        canvas_base_path=settings.canvas_base_path,
        config=textbook_config
    )

    # Story 31.5: Get MemoryService for difficulty adaptation
    # Import from canonical singleton in memory_service.py (not endpoint)
    from app.services.memory_service import get_memory_service as _get_memory_svc
    try:
        memory_service = await _get_memory_svc()
    except Exception as e:
        logger.warning(f"MemoryService not available for difficulty adaptation: {e}")
        memory_service = None

    # P0-2: Create AgentService for AI question generation and scoring
    agent_service = None
    try:
        gemini_client = None
        if settings.AI_API_KEY:
            gemini_client = GeminiClient(
                api_key=settings.AI_API_KEY,
                model=settings.AI_MODEL_NAME,
                base_url=settings.AI_BASE_URL if settings.AI_BASE_URL else None
            )
        neo4j_client = get_neo4j_client_dep()
        agent_service = AgentService(
            gemini_client=gemini_client,
            neo4j_client=neo4j_client
        )
        logger.info("AgentService created for VerificationService AI integration")
    except Exception as e:
        logger.warning(f"AgentService not available for verification: {e}")

    # Create VerificationService with all dependencies
    # AC5: Services are optional - graceful degradation built into VerificationService
    # Story 31.A.1 AC-31.A.1.1: Added graphiti_client injection
    # Story 31.5: Added memory_service injection for difficulty adaptation
    service = VerificationService(
        rag_service=rag_service,
        cross_canvas_service=cross_canvas_service,
        textbook_context_service=textbook_service,
        graphiti_client=graphiti_client,  # Story 31.A.1: Enable question deduplication
        memory_service=memory_service,  # Story 31.5: Enable difficulty adaptation
        agent_service=agent_service,  # P0-2: Enable AI question generation and scoring
        canvas_service=canvas_service,  # P0 Fix: Enable Canvas concept extraction
        canvas_base_path=str(settings.canvas_base_path) if settings.canvas_base_path else None  # P0 Fix
    )

    try:
        yield service
    finally:
        if agent_service:
            await agent_service.cleanup()
        await service.cleanup()
        logger.debug("VerificationService cleanup completed")


# Type alias for VerificationService dependency
VerificationServiceDep = Annotated[VerificationService, Depends(get_verification_service)]


# =============================================================================
# RAGService Dependency (Story 12.A.2 - Agent-RAG Bridge Layer)
# [Source: docs/stories/story-12.A.2-agent-rag-bridge.md#Task-0]
# =============================================================================

from .services.rag_service import RAGService

# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: dependencies with yield cleanup)
async def get_rag_service_dep() -> AsyncGenerator[RAGService, None]:
    """
    Get RAGService instance for Agent-RAG integration.

    Provides RAGService with 5-source parallel retrieval capability:
    - Graphiti (temporal knowledge graph)
    - LanceDB (vector embeddings)
    - Multimodal (images/diagrams)
    - Textbook (lecture references)
    - CrossCanvas (related canvases)

    Uses singleton pattern internally via get_rag_service().
    Supports graceful degradation when LangGraph not available.

    ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: dependencies-with-yield)

    Yields:
        RAGService: RAG orchestration service instance

    Example:
        ```python
        @router.post("/agents/decompose/basic")
        async def decompose_basic(
            request: DecomposeRequest,
            rag_service: RAGService = Depends(get_rag_service_dep)
        ):
            rag_context = await rag_service.query_with_fallback(...)
            return await agent_service.decompose_basic(..., rag_context=rag_context)
        ```

    [Source: docs/stories/story-12.A.2-agent-rag-bridge.md#Task-0]
    [Source: src/agentic_rag/state_graph.py - 5-source parallel retrieval]
    """
    logger.debug("Getting RAGService instance for Agent-RAG bridge")
    service = get_rag_service()

    # Initialize if not already done
    if not service._initialized:
        await service.initialize()

    try:
        yield service
    finally:
        # RAGService is singleton, no cleanup needed per-request
        logger.debug("RAGService dependency released")


# Type alias for RAGService dependency
RAGServiceDep = Annotated[RAGService, Depends(get_rag_service_dep)]


# =============================================================================
# Neo4jClient Dependency (Story 30.2 + Story 36.1)
# [Source: docs/stories/30.2.story.md#Neo4jClient-Real-Driver]
# [Source: docs/stories/36.1.story.md#Unified-GraphitiClient-Architecture]
# =============================================================================

def get_neo4j_client_dep() -> Neo4jClient:
    """
    Get Neo4jClient singleton instance.

    Story 30.2: Neo4jClient with real Bolt driver implementation.
    - Connection pool: max_pool_size=50, connection_acquisition_timeout=30s
    - Retry mechanism: tenacity 3x exponential backoff (1s, 2s, 4s)
    - JSON fallback: NEO4J_MOCK=true or NEO4J_ENABLED=false

    Story 36.1: Used for dependency injection into GraphitiClients.

    Returns:
        Neo4jClient: Singleton Neo4j client instance

    Example:
        ```python
        @router.get("/health/neo4j")
        async def neo4j_health(
            neo4j: Neo4jClient = Depends(get_neo4j_client_dep)
        ):
            return await neo4j.health_check()
        ```

    [Source: docs/stories/30.2.story.md#AC-30.2.1]
    [Source: docs/stories/36.1.story.md#AC-36.1.3]
    """
    logger.debug("Getting Neo4jClient singleton instance")
    return get_neo4j_client()


# Type alias for Neo4jClient dependency
Neo4jClientDep = Annotated[Neo4jClient, Depends(get_neo4j_client_dep)]


# =============================================================================
# GraphitiClient Dependency (Story 36.1)
# [Source: docs/stories/36.1.story.md#Unified-GraphitiClient-Architecture]
# =============================================================================

# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: dependencies with yield cleanup)
async def get_graphiti_client(
    neo4j_client: Neo4jClientDep
) -> AsyncGenerator[GraphitiEdgeClient, None]:
    """
    Get GraphitiEdgeClient instance with Neo4jClient dependency injection.

    Story 36.1 AC-36.1.3: Neo4jClient injection
    - Reuses Story 30.2 connection pool (50 connections, 30s timeout)
    - Reuses existing retry mechanism (tenacity 3x exponential backoff)
    - Reuses existing JSON fallback (NEO4J_MOCK=true)

    This is the unified entry point for Graphiti operations. The GraphitiEdgeClient
    inherits from GraphitiClientBase and delegates Neo4j operations to the injected
    Neo4jClient, ensuring the entire application uses the same connection pool.

    ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: dependencies-with-yield)

    Dependency Chain:
        get_neo4j_client_dep() → neo4j_client (singleton)
        get_graphiti_client(neo4j_client) → graphiti_client

    Args:
        neo4j_client: Neo4jClient singleton (injected via Depends)

    Yields:
        GraphitiEdgeClient: Graphiti client with Neo4j dependency injection

    Example:
        ```python
        @router.post("/canvas/{canvas_name}/edges")
        async def add_edge(
            canvas_name: str,
            edge: EdgeData,
            graphiti: GraphitiEdgeClient = Depends(get_graphiti_client)
        ):
            relationship = EdgeRelationship(
                canvas_path=canvas_name,
                from_node_id=edge.from_id,
                to_node_id=edge.to_id,
                edge_label=edge.label
            )
            return await graphiti.add_edge_relationship(relationship)
        ```

    [Source: docs/stories/36.1.story.md#AC-36.1.3]
    [Source: docs/architecture/decisions/ADR-003-AGENTIC-RAG-ARCHITECTURE.md]
    """
    logger.debug("Creating GraphitiEdgeClient with Neo4jClient injection")

    # Create GraphitiEdgeClient with injected Neo4jClient
    # This ensures the same connection pool is used across the application
    client = GraphitiEdgeClient(neo4j_client=neo4j_client)

    # Initialize if needed
    if not client._initialized:
        await client.initialize()

    try:
        yield client
    finally:
        await client.cleanup()
        logger.debug("GraphitiEdgeClient cleanup completed")


# Type alias for GraphitiClient dependency
GraphitiClientDep = Annotated[GraphitiEdgeClient, Depends(get_graphiti_client)]


# =============================================================================
# GraphitiTemporalClient Dependency (Story 31.4)
# [Source: docs/stories/31.4.story.md#Task-4]
# =============================================================================

# Import GraphitiTemporalClient from src/agentic_rag
import sys
from pathlib import Path as _PathLib

# Add src to path if needed
_src_path = _PathLib(__file__).parent.parent.parent / "src"
if str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))

# Lazy import to avoid circular dependency issues
_graphiti_temporal_client_instance = None


def get_graphiti_temporal_client():
    """
    Get GraphitiTemporalClient singleton instance.

    Story 31.4 AC-31.4.1: Used for querying verification question history.
    Story 31.4 AC-31.4.3: Required for the verification history endpoint.
    Story 36.1 AC-36.1.3: Neo4jClient dependency injection.

    This function returns a singleton instance of GraphitiTemporalClient
    for efficient reuse across requests. Returns None if the client
    cannot be initialized (graceful degradation).

    Returns:
        GraphitiTemporalClient or None: Client instance or None if unavailable

    Example:
        ```python
        @router.get("/verification/history/{concept}")
        async def get_history(concept: str):
            client = get_graphiti_temporal_client()
            if client:
                return await client.search_verification_questions(concept)
            return {"items": []}
        ```

    [Source: docs/stories/31.4.story.md#Task-4]
    [Source: docs/stories/36.1.story.md#AC-36.1.3]
    [Source: src/agentic_rag/clients/graphiti_temporal_client.py]
    """
    global _graphiti_temporal_client_instance

    if _graphiti_temporal_client_instance is not None:
        return _graphiti_temporal_client_instance

    try:
        # Story 36.1 AC-36.1.3: Get Neo4jClient for dependency injection
        neo4j_client = get_neo4j_client()

        from agentic_rag.clients.graphiti_temporal_client import GraphitiTemporalClient

        # Fix: Inject neo4j_client (required parameter)
        _graphiti_temporal_client_instance = GraphitiTemporalClient(
            neo4j_client=neo4j_client,
            timeout_ms=500,
            enable_fallback=True
        )
        logger.info(
            "GraphitiTemporalClient singleton initialized with Neo4jClient "
            f"(mode={neo4j_client.stats.get('mode', 'unknown') if neo4j_client else 'none'})"
        )
        return _graphiti_temporal_client_instance

    except ImportError as e:
        logger.warning(
            f"GraphitiTemporalClient not available: {e}. "
            "Question deduplication and learning history will be DISABLED. "
            "To fix: pip install graphiti-core"
        )
        return None
    except ValueError as e:
        logger.error(
            f"GraphitiTemporalClient initialization failed (Neo4jClient issue): {e}. "
            "Check NEO4J_HOST, NEO4J_PORT environment variables."
        )
        return None
    except Exception as e:
        logger.error(f"Failed to initialize GraphitiTemporalClient: {type(e).__name__}: {e}")
        return None


# =============================================================================
# MultimodalService Dependency (Story 35.1)
# [Source: docs/stories/35.1.story.md]
# =============================================================================

from .services.multimodal_service import MultimodalService


async def get_multimodal_service_dep(settings: SettingsDep) -> MultimodalService:
    """
    Get MultimodalService singleton instance and ensure it's initialized.

    Uses the module-level singleton pattern from multimodal_service.py.
    Injects storage_base_path from settings and attempts to create
    MultimodalStore for vector search / Neo4j integration.

    Returns:
        MultimodalService: Singleton multimodal service instance

    [Source: docs/stories/35.1.story.md#Task-3.1]
    """
    from .services.multimodal_service import get_multimodal_service

    logger.debug("Getting MultimodalService singleton instance")

    # D1 Persistence: Compute storage path from settings
    storage_base_path = None
    if settings.canvas_base_path:
        storage_base_path = str(_PathLib(settings.canvas_base_path) / "multimodal")

    # D5 Degradation: Try to inject MultimodalStore, fall back gracefully
    multimodal_store = None
    try:
        from src.agentic_rag.storage.multimodal_store import MultimodalStore as _MMStore
        multimodal_store = _MMStore()
        logger.info("MultimodalStore injected — vector search and Neo4j enabled")
    except ImportError:
        logger.warning(
            "MultimodalStore not available (agentic_rag not installed) — "
            "using JSON fallback. Vector search disabled."
        )
    except Exception as e:
        logger.warning(f"MultimodalStore creation failed: {e} — using JSON fallback")

    service = get_multimodal_service(
        storage_base_path=storage_base_path,
        multimodal_store=multimodal_store,
    )
    await service.initialize()
    return service


# Type alias for MultimodalService dependency
MultimodalServiceDep = Annotated[MultimodalService, Depends(get_multimodal_service_dep)]


# =============================================================================
# EPIC-33: Intelligent Parallel Processing Dependencies
# =============================================================================

from .services.session_manager import SessionManager
from .services.intelligent_grouping_service import IntelligentGroupingService
from .services.agent_routing_engine import AgentRoutingEngine


def get_session_manager() -> SessionManager:
    """
    Get SessionManager singleton instance.

    EPIC-33 Story 33.3: Session lifecycle management.

    Returns:
        SessionManager: Singleton session manager instance
    """
    logger.debug("Getting SessionManager singleton instance")
    return SessionManager.get_instance()


# Type alias for SessionManager dependency
SessionManagerDep = Annotated[SessionManager, Depends(get_session_manager)]


def get_intelligent_grouping_service(
    settings: SettingsDep
) -> IntelligentGroupingService:
    """
    Get IntelligentGroupingService instance.

    EPIC-33 Story 33.4: TF-IDF + K-Means canvas node clustering.

    Args:
        settings: Application settings for canvas_base_path

    Returns:
        IntelligentGroupingService: Grouping service instance
    """
    logger.debug("Creating IntelligentGroupingService instance")
    canvas_base_path = str(settings.canvas_base_path) if settings.canvas_base_path else None
    return IntelligentGroupingService(canvas_base_path=canvas_base_path)


# Type alias for IntelligentGroupingService dependency
IntelligentGroupingServiceDep = Annotated[IntelligentGroupingService, Depends(get_intelligent_grouping_service)]


# AgentRoutingEngine singleton
_agent_routing_engine_instance: Optional[AgentRoutingEngine] = None


def get_agent_routing_engine() -> AgentRoutingEngine:
    """
    Get AgentRoutingEngine singleton instance.

    EPIC-33 Story 33.5: Content-based agent routing.

    Returns:
        AgentRoutingEngine: Singleton routing engine instance
    """
    global _agent_routing_engine_instance
    if _agent_routing_engine_instance is None:
        _agent_routing_engine_instance = AgentRoutingEngine()
        logger.info("AgentRoutingEngine singleton initialized")
    return _agent_routing_engine_instance


# Type alias for AgentRoutingEngine dependency
AgentRoutingEngineDep = Annotated[AgentRoutingEngine, Depends(get_agent_routing_engine)]


async def get_batch_orchestrator(
    settings: SettingsDep,
    agent_service: AgentServiceDep,
    canvas_service: CanvasServiceDep,
):
    """
    Get BatchOrchestrator instance with all dependencies.

    EPIC-33 Story 33.6: Parallel execution orchestration.

    Args:
        settings: Application settings
        agent_service: AgentService for agent calls
        canvas_service: CanvasService for node content

    Yields:
        BatchOrchestrator: Orchestrator instance
    """
    from .services.batch_orchestrator import BatchOrchestrator

    session_manager = get_session_manager()
    vault_path = str(settings.canvas_base_path) if settings.canvas_base_path else None

    orchestrator = BatchOrchestrator(
        session_manager=session_manager,
        agent_service=agent_service,
        canvas_service=canvas_service,
        vault_path=vault_path,
    )

    logger.debug("BatchOrchestrator created with SessionManager, AgentService, CanvasService")
    yield orchestrator


# Type alias for BatchOrchestrator dependency
from .services.batch_orchestrator import BatchOrchestrator as _BatchOrchestrator
BatchOrchestratorDep = Annotated[_BatchOrchestrator, Depends(get_batch_orchestrator)]


# NOTE: get_intelligent_parallel_service() and IntelligentParallelServiceDep
# were dead code (never used by endpoints). Removed per AC-33.9.8.
# The endpoint uses a singleton pattern with _ensure_async_deps() instead,
# because BatchOrchestrator._cancel_requested requires a shared instance.


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
    "get_verification_service",
    "get_rag_service_dep",  # Story 12.A.2
    "get_neo4j_client_dep",  # Story 36.1
    "get_graphiti_client",  # Story 36.1
    "get_graphiti_temporal_client",  # Story 31.4
    "get_multimodal_service_dep",  # Story 35.1
    "get_session_manager",  # EPIC-33
    "get_intelligent_grouping_service",  # EPIC-33
    "get_agent_routing_engine",  # EPIC-33
    "get_batch_orchestrator",  # EPIC-33
    # get_intelligent_parallel_service removed per AC-33.9.8 (dead code)
    # Type Aliases (Annotated types for cleaner endpoint signatures)
    "SettingsDep",
    "CanvasServiceDep",
    "AgentServiceDep",
    "TaskManagerDep",
    "ReviewServiceDep",
    "ContextEnrichmentServiceDep",
    "CrossCanvasServiceDep",
    "VerificationServiceDep",
    "RAGServiceDep",  # Story 12.A.2
    "Neo4jClientDep",  # Story 36.1
    "GraphitiClientDep",  # Story 36.1
    "MultimodalServiceDep",  # Story 35.1
    "SessionManagerDep",  # EPIC-33
    "IntelligentGroupingServiceDep",  # EPIC-33
    "AgentRoutingEngineDep",  # EPIC-33
    "BatchOrchestratorDep",  # EPIC-33
    # IntelligentParallelServiceDep removed per AC-33.9.8 (dead code)
]
