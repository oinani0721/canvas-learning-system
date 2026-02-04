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

    # ✅ FIX-Canvas-Write: Pass canvas_service to AgentService for direct Canvas writes
    # Story 36.7: Pass neo4j_client to AgentService for learning memory queries
    service = AgentService(
        gemini_client=gemini_client,
        canvas_service=canvas_service,  # ✅ FIX: 注入 canvas_service
        neo4j_client=neo4j_client  # Story 36.7: 注入 Neo4jClient
    )
    logger.debug("AgentService created with CanvasService and Neo4jClient for direct Canvas writes and memory queries")

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
# VerificationService Dependency (Story 24.5)
# [Source: docs/stories/24.5.story.md#Dev-Notes]
# =============================================================================

# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: chained dependencies)
async def get_verification_service(
    settings: SettingsDep
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

    # Create TextbookContext service
    # Story 24.5 AC4: Textbook context with timeout
    textbook_config = TextbookContextConfig(timeout=3.0)
    textbook_service = TextbookContextService(
        canvas_base_path=settings.canvas_base_path,
        config=textbook_config
    )

    # Create VerificationService with all dependencies
    # AC5: Services are optional - graceful degradation built into VerificationService
    service = VerificationService(
        rag_service=rag_service,
        cross_canvas_service=cross_canvas_service,
        textbook_context_service=textbook_service
    )

    try:
        yield service
    finally:
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
    [Source: src/agentic_rag/clients/graphiti_temporal_client.py]
    """
    global _graphiti_temporal_client_instance

    if _graphiti_temporal_client_instance is not None:
        return _graphiti_temporal_client_instance

    try:
        from agentic_rag.clients.graphiti_temporal_client import GraphitiTemporalClient

        _graphiti_temporal_client_instance = GraphitiTemporalClient()
        logger.info("GraphitiTemporalClient singleton initialized")
        return _graphiti_temporal_client_instance

    except ImportError as e:
        logger.warning(f"GraphitiTemporalClient not available: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to initialize GraphitiTemporalClient: {e}")
        return None


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
]
