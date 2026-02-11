# Canvas Learning System - Intelligent Parallel Processing Endpoints
# Story 33.1: Backend REST Endpoints
# ✅ Verified from specs/api/parallel-api.openapi.yml
# ✅ Verified from specs/data/parallel-task.schema.json
"""
REST API endpoints for intelligent parallel batch processing.

Provides 5 endpoints:
1. POST /canvas/intelligent-parallel - Analyze and group nodes
2. POST /canvas/intelligent-parallel/confirm - Start batch processing
3. GET /canvas/intelligent-parallel/{session_id} - Get progress status
4. POST /canvas/intelligent-parallel/cancel/{session_id} - Cancel session
5. POST /canvas/single-agent - Retry single failed node

[Source: specs/api/parallel-api.openapi.yml]
[Source: docs/stories/33.1.story.md]
"""

import asyncio
import logging
from typing import Optional

# ✅ Verified from Context7:/fastapi/fastapi (topic: APIRouter, HTTPException)
from fastapi import APIRouter, HTTPException, Path, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

from app.services.intelligent_grouping_service import CanvasNotFoundError
from app.models.intelligent_parallel_models import (
    CancelResponse,
    ConfirmRequest,
    IntelligentParallelRequest,
    IntelligentParallelResponse,
    ParallelErrorResponse,
    ProgressResponse,
    SessionResponse,
    SingleAgentRequest,
    SingleAgentResponse,
)

# ═══════════════════════════════════════════════════════════════════════════════
# Routers
# [Source: specs/api/parallel-api.openapi.yml#/paths]
# ═══════════════════════════════════════════════════════════════════════════════

# Main router for /canvas/intelligent-parallel/* endpoints
intelligent_parallel_router = APIRouter(
    responses={
        400: {"model": ParallelErrorResponse, "description": "Bad request"},
        404: {"model": ParallelErrorResponse, "description": "Resource not found"},
        409: {"model": ParallelErrorResponse, "description": "Conflict"},
        500: {"model": ParallelErrorResponse, "description": "Internal server error"},
    }
)

# Separate router for /canvas/single-agent endpoint
single_agent_router = APIRouter(
    responses={
        400: {"model": ParallelErrorResponse, "description": "Bad request"},
        404: {"model": ParallelErrorResponse, "description": "Resource not found"},
        500: {"model": ParallelErrorResponse, "description": "Internal server error"},
    }
)


# ═══════════════════════════════════════════════════════════════════════════════
# Service Import (EPIC-33 P0 Fix: uses DI from dependencies.py)
# ═══════════════════════════════════════════════════════════════════════════════

# Lazy-init singleton with async dep injection (Story 33.9 P0 Fix)
_service: Optional["IntelligentParallelService"] = None  # type: ignore
_validator_set: bool = False
_deps_initialized: bool = False
_deps_lock: asyncio.Lock = asyncio.Lock()  # EPIC-33 P0 Fix #3: prevent race condition


def get_service():
    """
    Get IntelligentParallelService singleton (sync skeleton).

    Creates the service with sync-available dependencies only.
    Async dependencies (batch_orchestrator, agent_service) are injected
    lazily by _ensure_async_deps() on first request.
    """
    global _service, _validator_set
    if _service is None:
        from app.services.intelligent_parallel_service import (
            IntelligentParallelService,
        )
        from app.dependencies import (
            get_settings,
            get_session_manager,
            get_intelligent_grouping_service,
            get_agent_routing_engine,
        )

        settings = get_settings()

        # Assemble sync-available dependencies
        session_manager = get_session_manager()
        grouping_service = get_intelligent_grouping_service(settings)
        routing_engine = get_agent_routing_engine()

        _service = IntelligentParallelService(
            grouping_service=grouping_service,
            session_manager=session_manager,
            batch_orchestrator=None,  # Injected by _ensure_async_deps()
            agent_service=None,  # Injected by _ensure_async_deps()
            routing_engine=routing_engine,
        )

        # Story 33.2: Set up WebSocket session validator
        if not _validator_set:
            try:
                from app.api.v1.endpoints.websocket import set_session_validator
                set_session_validator(_service.session_exists)
                _validator_set = True
            except ImportError:
                pass  # WebSocket module not available

    return _service


async def _ensure_async_deps() -> None:
    """
    Lazily inject batch_orchestrator and agent_service into the singleton.

    Story 33.11: Delegates to dependencies.py build_batch_processing_deps()
    so that DI construction logic lives in ONE place (single source of truth).

    Uses asyncio.Lock for double-check locking to prevent race condition
    when concurrent first requests arrive simultaneously.

    Called by every endpoint before using the service.
    """
    global _deps_initialized
    # Fast path: already initialized (no lock needed)
    if _deps_initialized:
        return

    # Slow path: acquire lock and double-check
    async with _deps_lock:
        if _deps_initialized:
            return  # Another coroutine already initialized while we waited

        service = get_service()

        # Story 33.11 AC-33.11.2: Delegate to dependencies.py (single source of truth)
        from app.dependencies import build_batch_processing_deps
        batch_orchestrator, agent_service, canvas_service = await build_batch_processing_deps()

        # Inject into the singleton service
        service._batch_orchestrator = batch_orchestrator
        service._agent_service = agent_service
        service._canvas_service = canvas_service

        _deps_initialized = True
        logger.info(
            "[Story 33.11] DI consolidated: batch deps built via dependencies.py"
        )


def reset_service():
    """Reset the service singleton (for testing)."""
    global _service, _validator_set, _deps_initialized, _deps_lock
    _service = None
    _validator_set = False
    _deps_initialized = False
    _deps_lock = asyncio.Lock()  # Fresh lock to avoid stale state


# ═══════════════════════════════════════════════════════════════════════════════
# POST /canvas/intelligent-parallel - Analyze and group nodes (AC1)
# [Source: specs/api/parallel-api.openapi.yml#L54-L95]
# ═══════════════════════════════════════════════════════════════════════════════

@intelligent_parallel_router.post(
    "/",
    response_model=IntelligentParallelResponse,
    summary="Analyze canvas and group nodes for parallel processing",
    description="""
Analyzes the specified canvas file and groups nodes of the target color
using TF-IDF + K-Means clustering algorithm.

Returns grouped nodes with recommended agents and confidence scores.
Response time target: < 3 seconds.
""",
    responses={
        200: {
            "description": "Grouping analysis completed successfully",
            "model": IntelligentParallelResponse,
        },
        404: {
            "description": "Canvas file not found",
            "model": ParallelErrorResponse,
        },
    },
)
async def analyze_canvas(
    request: IntelligentParallelRequest,
) -> IntelligentParallelResponse:
    """
    Analyze canvas and return node groupings with agent recommendations.

    [Source: specs/api/parallel-api.openapi.yml#/paths/~1canvas~1intelligent-parallel/post]
    [Source: docs/stories/33.1.story.md - AC1]

    Args:
        request: Canvas path and grouping parameters

    Returns:
        IntelligentParallelResponse with grouped nodes and recommendations

    Raises:
        HTTPException 404: Canvas file not found
    """
    await _ensure_async_deps()
    service = get_service()

    try:
        result = await service.analyze_canvas(
            canvas_path=request.canvas_path,
            target_color=request.target_color,
            max_groups=request.max_groups,
            min_nodes_per_group=request.min_nodes_per_group,
        )
        return result
    except (FileNotFoundError, CanvasNotFoundError) as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "CanvasNotFoundError",
                "message": f"Canvas file '{request.canvas_path}' not found",
                "details": {"path": request.canvas_path},
            },
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "AnalysisError",
                "message": str(e),
            },
        ) from e


# ═══════════════════════════════════════════════════════════════════════════════
# POST /canvas/intelligent-parallel/confirm - Start batch processing (AC2)
# [Source: specs/api/parallel-api.openapi.yml#L96-L132]
# ═══════════════════════════════════════════════════════════════════════════════

@intelligent_parallel_router.post(
    "/confirm",
    response_model=SessionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Confirm and start batch processing",
    description="""
Starts batch processing for the confirmed node groups.
Returns immediately with session ID for tracking progress.

Client can override recommended agents in the request.
""",
    responses={
        202: {
            "description": "Batch processing started",
            "model": SessionResponse,
        },
        400: {
            "description": "Invalid group configuration",
            "model": ParallelErrorResponse,
        },
        404: {
            "description": "Canvas file not found",
            "model": ParallelErrorResponse,
        },
    },
)
async def confirm_batch(
    request: ConfirmRequest,
) -> SessionResponse:
    """
    Confirm groupings and start batch processing.

    [Source: specs/api/parallel-api.openapi.yml#/paths/~1canvas~1intelligent-parallel~1confirm/post]
    [Source: docs/stories/33.1.story.md - AC2]

    Args:
        request: Confirmed groups with agent assignments

    Returns:
        SessionResponse with session ID and estimated completion time

    Raises:
        HTTPException 400: Invalid group configuration
        HTTPException 404: Canvas file not found
    """
    await _ensure_async_deps()
    service = get_service()

    try:
        result = await service.start_batch_session(
            canvas_path=request.canvas_path,
            groups=request.groups,
            max_concurrent=request.max_concurrent,
            timeout=request.timeout,
        )
        return result
    except (FileNotFoundError, CanvasNotFoundError) as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "CanvasNotFoundError",
                "message": f"Canvas file '{request.canvas_path}' not found",
                "details": {"path": request.canvas_path},
            },
        ) from e
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "InvalidGroupConfigError",
                "message": str(e),
            },
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "BatchStartError",
                "message": str(e),
            },
        ) from e


# ═══════════════════════════════════════════════════════════════════════════════
# GET /canvas/intelligent-parallel/{session_id} - Get progress status (AC3)
# [Source: specs/api/parallel-api.openapi.yml#L133-L169]
# ═══════════════════════════════════════════════════════════════════════════════

@intelligent_parallel_router.get(
    "/{session_id}",
    response_model=ProgressResponse,
    summary="Get batch processing progress",
    description="""
Returns current progress status for a batch processing session.
Includes completed/failed node counts, per-group details, and performance metrics.
""",
    responses={
        200: {
            "description": "Progress status retrieved",
            "model": ProgressResponse,
        },
        404: {
            "description": "Session not found",
            "model": ParallelErrorResponse,
        },
    },
)
async def get_progress(
    session_id: str = Path(
        ...,
        description="Session ID returned from confirm endpoint",
        examples=["parallel-20250118-001"],
    ),
) -> ProgressResponse:
    """
    Get current progress status for a batch session.

    [Source: specs/api/parallel-api.openapi.yml#/paths/~1canvas~1intelligent-parallel~1{sessionId}/get]
    [Source: docs/stories/33.1.story.md - AC3]

    Args:
        session_id: Session ID from confirm response

    Returns:
        ProgressResponse with current status and progress details

    Raises:
        HTTPException 404: Session not found
    """
    await _ensure_async_deps()
    service = get_service()

    try:
        result = await service.get_session_status(session_id)
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "SessionNotFoundError",
                    "message": f"Session '{session_id}' not found",
                    "details": {"session_id": session_id},
                },
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "ProgressRetrievalError",
                "message": str(e),
            },
        ) from e


# ═══════════════════════════════════════════════════════════════════════════════
# POST /canvas/intelligent-parallel/cancel/{session_id} - Cancel session (AC4)
# [Source: specs/api/parallel-api.openapi.yml#L170-L217]
# ═══════════════════════════════════════════════════════════════════════════════

@intelligent_parallel_router.post(
    "/cancel/{session_id}",
    response_model=CancelResponse,
    summary="Cancel batch processing session",
    description="""
Cancels an in-progress batch processing session.
Returns the count of nodes completed before cancellation.

Returns 409 Conflict if session is already completed or cancelled.
""",
    responses={
        200: {
            "description": "Session cancelled successfully",
            "model": CancelResponse,
        },
        404: {
            "description": "Session not found",
            "model": ParallelErrorResponse,
        },
        409: {
            "description": "Session already completed or cancelled",
            "model": ParallelErrorResponse,
        },
    },
)
async def cancel_session(
    session_id: str = Path(
        ...,
        description="Session ID to cancel",
        examples=["parallel-20250118-001"],
    ),
) -> CancelResponse:
    """
    Cancel an in-progress batch processing session.

    [Source: specs/api/parallel-api.openapi.yml#/paths/~1canvas~1intelligent-parallel~1cancel~1{sessionId}/post]
    [Source: docs/stories/33.1.story.md - AC4]

    Args:
        session_id: Session ID to cancel

    Returns:
        CancelResponse with success status and completed count

    Raises:
        HTTPException 404: Session not found
        HTTPException 409: Session already completed or cancelled
    """
    await _ensure_async_deps()
    service = get_service()

    try:
        result = await service.cancel_session(session_id)
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "SessionNotFoundError",
                    "message": f"Session '{session_id}' not found",
                    "details": {"session_id": session_id},
                },
            )
        return result
    except HTTPException:
        raise
    except ValueError as e:
        # Session already completed or cancelled
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "SessionAlreadyCompletedError",
                "message": str(e),
                "details": {"session_id": session_id},
            },
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "CancellationError",
                "message": str(e),
            },
        ) from e


# ═══════════════════════════════════════════════════════════════════════════════
# POST /canvas/single-agent - Retry single failed node (AC5)
# [Source: specs/api/parallel-api.openapi.yml - NEW endpoint]
# ═══════════════════════════════════════════════════════════════════════════════

@single_agent_router.post(
    "/single-agent",
    response_model=SingleAgentResponse,
    summary="Retry single node with specified agent",
    description="""
Executes a single agent on a specific node.
Useful for retrying failed nodes from batch processing.

This endpoint is independent of any batch session.
""",
    responses={
        200: {
            "description": "Agent execution completed",
            "model": SingleAgentResponse,
        },
        404: {
            "description": "Node or canvas not found",
            "model": ParallelErrorResponse,
        },
    },
)
async def retry_single_node(
    request: SingleAgentRequest,
) -> SingleAgentResponse:
    """
    Execute single agent on a specific node.

    [Source: docs/stories/33.1.story.md - AC5]

    Args:
        request: Node ID, agent type, and canvas path

    Returns:
        SingleAgentResponse with generated file path and status

    Raises:
        HTTPException 404: Node or canvas not found
    """
    await _ensure_async_deps()
    service = get_service()

    try:
        result = await service.retry_single_node(
            node_id=request.node_id,
            agent_type=request.agent_type,
            canvas_path=request.canvas_path,
        )
        return result
    except (FileNotFoundError, CanvasNotFoundError) as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "ResourceNotFoundError",
                "message": str(e),
                "details": {
                    "node_id": request.node_id,
                    "canvas_path": request.canvas_path,
                },
            },
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "SingleAgentError",
                "message": str(e),
            },
        ) from e
