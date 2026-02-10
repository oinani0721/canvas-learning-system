# Canvas Learning System - Multimodal API Router
# Story 35.1: Multimodal Upload/Management API Endpoints
# Story 35.2: Multimodal Query/Search API Endpoints
# [Source: docs/stories/35.1.story.md]
# [Source: docs/stories/35.2.story.md]
"""
API endpoints for multimodal content upload, management, and search.

Story 35.1 Implementation:
- AC-35.1.1: POST /api/v1/multimodal/upload - File upload with validation
- AC-35.1.2: POST /api/v1/multimodal/upload-url - URL content fetch
- AC-35.1.3: DELETE /api/v1/multimodal/{content_id} - Delete content
- AC-35.1.4: PUT /api/v1/multimodal/{content_id} - Update metadata
- AC-35.1.5: GET /api/v1/multimodal/{content_id} - Retrieve content

Story 35.2 Implementation:
- AC-35.2.1: GET /api/v1/multimodal/by-concept/{concept_id} - Query by concept
- AC-35.2.2: POST /api/v1/multimodal/search - Vector similarity search
- AC-35.2.3: GET /api/v1/multimodal/list - Paginated list with filters
- AC-35.2.4: Response format matches frontend MediaItem interface

[Source: docs/stories/35.1.story.md#Task-1]
[Source: docs/stories/35.2.story.md#Task-1]
[Source: specs/api/multimodal-api.openapi.yml]
"""

import logging
from typing import Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    File,
    Form,
    HTTPException,
    Path,
    Query,
    UploadFile,
    status,
)

from app.models.multimodal_schemas import (
    # Story 35.1: Upload/Management
    MultimodalHealthResponse,
    MultimodalListResponse,
    MultimodalMediaType,
    MultimodalResponse,
    MultimodalUpdateRequest,
    MultimodalUploadResponse,
    MultimodalUploadUrlRequest,
    # Story 35.2: Query/Search
    MediaItemResponse,
    MultimodalByConceptResponse,
    MultimodalPaginatedListResponse,
    MultimodalSearchRequest,
    MultimodalSearchResponse,
    PaginationMeta,
)
from app.dependencies import MultimodalServiceDep
from app.services.multimodal_service import (
    ContentNotFoundError,
    FileValidationError,
    MultimodalServiceError,
)

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# Router Configuration
# ═══════════════════════════════════════════════════════════════════════════════

multimodal_router = APIRouter(
    responses={
        400: {"description": "Invalid request - validation error"},
        404: {"description": "Content not found"},
        413: {"description": "File too large (max 50MB)"},
        415: {"description": "Unsupported media type"},
        500: {"description": "Internal server error"},
    }
)


# ═══════════════════════════════════════════════════════════════════════════════
# Upload Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@multimodal_router.post(
    "/upload",
    response_model=MultimodalUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a file",
    description="Upload a multimodal file (image, PDF, audio, video) and associate it with a Canvas concept.",
)
async def upload_file(
    service: MultimodalServiceDep,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="File to upload"),
    related_concept_id: str = Form(..., description="Canvas node ID to associate"),
    canvas_path: Optional[str] = Form(None, description="Canvas file path"),
    description: Optional[str] = Form(None, description="Optional description"),
) -> MultimodalUploadResponse:
    """
    Upload a multimodal file.

    Accepts image, PDF, audio, and video files up to 50MB.
    The file is stored locally and metadata is saved for retrieval.

    - **file**: The file to upload (required)
    - **related_concept_id**: Canvas node ID to associate with (required)
    - **canvas_path**: Path to the Canvas file (required)
    - **description**: Optional description for the content

    Returns the uploaded content details including its unique ID.

    [Source: docs/stories/35.1.story.md#AC-35.1.1]
    """
    try:
        # Read file content once (avoid double-read)
        file_bytes = await file.read()
        file_size = len(file_bytes)

        result = await service.upload_file(
            file_bytes=file_bytes,
            filename=file.filename or "uploaded_file",
            content_type=file.content_type,
            file_size=file_size,
            related_concept_id=related_concept_id,
            canvas_path=canvas_path,
            description=description,
        )

        logger.info(
            f"File uploaded: {result.content.id} by concept {related_concept_id}"
        )

        return result

    except FileValidationError as e:
        logger.warning(f"File validation failed: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=e.message,
        )
    except MultimodalServiceError as e:
        logger.error(f"Upload failed: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message,
        )


@multimodal_router.post(
    "/upload-url",
    response_model=MultimodalUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload from URL",
    description="Fetch content from a URL and upload it as multimodal content.",
)
async def upload_from_url(
    service: MultimodalServiceDep,
    request: MultimodalUploadUrlRequest,
) -> MultimodalUploadResponse:
    """
    Upload content from a URL.

    Fetches the content from the specified URL, validates it,
    and stores it as multimodal content.

    - **url**: URL to fetch content from (required)
    - **related_concept_id**: Canvas node ID to associate with (required)
    - **canvas_path**: Path to the Canvas file (required)
    - **description**: Optional description

    Returns the uploaded content details including its unique ID.

    [Source: docs/stories/35.1.story.md#AC-35.1.2]
    """
    try:
        result = await service.upload_from_url(request)

        logger.info(
            f"URL content uploaded: {result.content.id} from {request.url}"
        )

        return result

    except FileValidationError as e:
        logger.warning(f"URL content validation failed: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=e.message,
        )
    except MultimodalServiceError as e:
        logger.error(f"URL upload failed: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Static Path Endpoints (MUST be defined BEFORE /{content_id} path parameter)
# IMPORTANT: FastAPI matches routes in definition order. Path parameters like
# /{content_id} will match ANY string including "health", "list", etc.
# Static paths must be defined first to ensure correct routing.
# [Source: QA Review 35.9 - Route ordering fix]
# ═══════════════════════════════════════════════════════════════════════════════

@multimodal_router.get(
    "",
    response_model=MultimodalListResponse,
    summary="List content",
    description="List multimodal content with optional filters.",
)
async def list_content(
    service: MultimodalServiceDep,
    concept_id: Optional[str] = Query(None, description="Filter by concept ID"),
    media_type: Optional[MultimodalMediaType] = Query(None, description="Filter by media type"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum items to return"),
) -> MultimodalListResponse:
    """
    List multimodal content.

    Returns a list of content items with optional filtering by concept or media type.

    [Source: Story 35.1 - Additional utility endpoint]
    """
    return await service.list_content(
        concept_id=concept_id,
        media_type=media_type,
        limit=limit,
    )


@multimodal_router.get(
    "/health",
    response_model=MultimodalHealthResponse,
    summary="Health check",
    description="Check the health status of the multimodal service.",
)
async def health_check(
    service: MultimodalServiceDep,
) -> MultimodalHealthResponse:
    """
    Get multimodal service health status.

    Returns the status of storage, LanceDB, and Neo4j connections.

    [Source: Story 35.1 - Service health endpoint]
    """
    return await service.get_health_status()


@multimodal_router.get(
    "/list",
    response_model=MultimodalPaginatedListResponse,
    summary="List all content with pagination",
    description="List all multimodal content with pagination and filtering.",
)
async def list_multimodal(
    service: MultimodalServiceDep,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    media_type: Optional[MultimodalMediaType] = Query(None, description="Filter by media type"),
    sort_by: str = Query("created_at", pattern="^(created_at|updated_at)$", description="Sort field"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort direction"),
    include_thumbnail: bool = Query(False, description="Include base64 encoded thumbnails"),
) -> MultimodalPaginatedListResponse:
    """
    List all multimodal content with pagination.

    Returns a paginated list of content with optional filtering by media type.
    Supports sorting by creation or update time.

    - **page**: Page number, 1-indexed (default 1)
    - **page_size**: Items per page (default 20, max 100)
    - **media_type**: Optional filter by media type
    - **sort_by**: Field to sort by (created_at/updated_at)
    - **sort_order**: Sort direction (asc/desc)
    - **include_thumbnail**: Include base64 encoded thumbnails in response

    [Source: docs/stories/35.2.story.md#AC-35.2.3]
    """
    try:
        return await service.list_all(
            page=page,
            page_size=page_size,
            media_type=media_type,
            sort_by=sort_by,
            sort_order=sort_order,
            include_thumbnail=include_thumbnail,
        )
    except MultimodalServiceError as e:
        logger.error(f"List failed: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message,
        )


@multimodal_router.post(
    "/search",
    response_model=MultimodalSearchResponse,
    summary="Search content",
    description="Search multimodal content using semantic similarity.",
)
async def search_multimodal(
    service: MultimodalServiceDep,
    request: MultimodalSearchRequest,
    include_thumbnail: bool = Query(False, description="Include base64 encoded thumbnails"),
) -> MultimodalSearchResponse:
    """
    Search multimodal content using vector similarity.

    Performs semantic search using embeddings to find relevant content.
    Falls back to text search if embedding service is unavailable.

    - **query**: Search query text (required)
    - **media_types**: Optional filter by media types
    - **top_k**: Maximum results to return (default 10, max 100)
    - **min_score**: Minimum similarity score threshold (default 0.5)
    - **include_thumbnail**: Include base64 encoded thumbnails in response

    Returns results sorted by relevance score (highest first).
    The `query_processed` field indicates if vector search was used (true)
    or fallback text search (false).

    [Source: docs/stories/35.2.story.md#AC-35.2.2]
    """
    try:
        return await service.search(
            request=request,
            include_thumbnail=include_thumbnail,
        )
    except MultimodalServiceError as e:
        logger.error(f"Search failed: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message,
        )


@multimodal_router.get(
    "/by-concept/{concept_id}",
    response_model=MultimodalByConceptResponse,
    summary="Get content by concept",
    description="Retrieve all multimodal content associated with a Canvas concept node.",
)
async def get_by_concept(
    service: MultimodalServiceDep,
    concept_id: str = Path(..., description="Canvas concept node ID"),
    media_type: Optional[MultimodalMediaType] = Query(None, description="Filter by media type"),
    limit: int = Query(100, ge=1, le=200, description="Maximum items to return"),
    include_thumbnail: bool = Query(False, description="Include base64 encoded thumbnails"),
) -> MultimodalByConceptResponse:
    """
    Get all multimodal content associated with a concept.

    Returns a list of media items that are linked to the specified concept node.
    Useful for displaying related media when viewing a concept in Canvas.

    - **concept_id**: Canvas node ID to query (required)
    - **media_type**: Optional filter by media type (image/pdf/audio/video)
    - **limit**: Maximum items to return (default 100, max 200)
    - **include_thumbnail**: Include base64 encoded thumbnails in response

    [Source: docs/stories/35.2.story.md#AC-35.2.1]
    """
    try:
        return await service.get_by_concept(
            concept_id=concept_id,
            media_type=media_type,
            limit=limit,
            include_thumbnail=include_thumbnail,
        )
    except MultimodalServiceError as e:
        logger.error(f"Get by concept failed: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Dynamic Path Parameter Endpoints (/{content_id})
# MUST be defined AFTER all static paths to prevent incorrect matching
# ═══════════════════════════════════════════════════════════════════════════════

@multimodal_router.get(
    "/{content_id}",
    response_model=MultimodalResponse,
    summary="Get content by ID",
    description="Retrieve multimodal content details by its unique ID.",
)
async def get_content(
    service: MultimodalServiceDep,
    content_id: str = Path(..., pattern=r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$", description="Content UUID"),
) -> MultimodalResponse:
    """
    Get multimodal content by ID.

    Returns the content details including file path, metadata, and associations.

    [Source: docs/stories/35.1.story.md#AC-35.1.5]
    """
    try:
        return await service.get_content(content_id)

    except ContentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Content not found: {content_id}",
        )


@multimodal_router.put(
    "/{content_id}",
    response_model=MultimodalResponse,
    summary="Update content metadata",
    description="Update metadata for existing multimodal content.",
)
async def update_content(
    service: MultimodalServiceDep,
    content_id: str = Path(..., pattern=r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$", description="Content UUID"),
    request: MultimodalUpdateRequest = ...,
) -> MultimodalResponse:
    """
    Update multimodal content metadata.

    Allows updating description, related concept, and source location.
    The file itself cannot be updated - delete and re-upload instead.

    [Source: docs/stories/35.1.story.md#AC-35.1.4]
    """
    try:
        return await service.update_content(content_id, request)

    except ContentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Content not found: {content_id}",
        )


@multimodal_router.delete(
    "/{content_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete content",
    description="Delete multimodal content and its associated files.",
)
async def delete_content(
    service: MultimodalServiceDep,
    content_id: str = Path(..., pattern=r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$", description="Content UUID"),
) -> None:
    """
    Delete multimodal content.

    Removes the content metadata and associated files (including thumbnails).
    This action cannot be undone. Returns 204 No Content on success.

    [Source: docs/stories/35.10.story.md#AC-35.10.3]
    """
    try:
        await service.delete_content(content_id)

    except ContentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Content not found: {content_id}",
        )
