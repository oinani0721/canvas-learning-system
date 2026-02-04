# Canvas Learning System - Multimodal API Schemas
# Story 35.1: Multimodal Upload/Management API Endpoints
# [Source: docs/stories/35.1.story.md]
# [Source: specs/data/multimodal-content.schema.json]
"""
Pydantic models for Multimodal Content API.

These models define the request/response schemas for multimodal content
upload, management, and retrieval endpoints.
"""

from datetime import datetime
from enum import Enum
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ═══════════════════════════════════════════════════════════════════════════════
# Enums
# ═══════════════════════════════════════════════════════════════════════════════

class MultimodalMediaType(str, Enum):
    """
    Supported media types for multimodal content.

    [Source: specs/data/multimodal-content.schema.json#media_type]
    [Source: src/agentic_rag/models/multimodal_content.py#MediaType]
    """
    IMAGE = "image"
    PDF = "pdf"
    AUDIO = "audio"
    VIDEO = "video"


# ═══════════════════════════════════════════════════════════════════════════════
# Metadata Schema
# ═══════════════════════════════════════════════════════════════════════════════

class MultimodalMetadataSchema(BaseModel):
    """
    Metadata for multimodal content.

    [Source: src/agentic_rag/models/multimodal_content.py#MultimodalMetadata]
    """
    file_size: Optional[int] = Field(None, ge=0, description="File size in bytes")
    width: Optional[int] = Field(None, ge=0, description="Width in pixels (image/video)")
    height: Optional[int] = Field(None, ge=0, description="Height in pixels (image/video)")
    duration: Optional[float] = Field(None, ge=0, description="Duration in seconds (audio/video)")
    page_count: Optional[int] = Field(None, ge=0, description="Page count (PDF)")
    mime_type: Optional[str] = Field(None, description="MIME type")
    author: Optional[str] = Field(None, description="Content author")
    title: Optional[str] = Field(None, description="Content title")
    language: Optional[str] = Field(None, description="Content language")


# ═══════════════════════════════════════════════════════════════════════════════
# Request Schemas
# ═══════════════════════════════════════════════════════════════════════════════

class MultimodalUploadUrlRequest(BaseModel):
    """
    Request model for uploading content from URL.

    [Source: docs/stories/35.1.story.md#AC-35.1.2]
    [Source: specs/api/multimodal-api.openapi.yml#MultimodalUploadUrlRequest]
    """
    url: str = Field(
        ...,
        min_length=1,
        description="URL to fetch content from (must be accessible)"
    )
    related_concept_id: str = Field(
        ...,
        min_length=1,
        description="Canvas node ID to associate this content with"
    )
    canvas_path: str = Field(
        ...,
        min_length=1,
        description="Canvas file path for context"
    )
    description: Optional[str] = Field(
        None,
        max_length=1000,
        description="Optional description for the content"
    )


class MultimodalUpdateRequest(BaseModel):
    """
    Request model for updating multimodal content metadata.

    [Source: docs/stories/35.1.story.md#AC-35.1.4]
    [Source: specs/api/multimodal-api.openapi.yml#MultimodalUpdateRequest]
    """
    description: Optional[str] = Field(
        None,
        max_length=1000,
        description="Updated description"
    )
    related_concept_id: Optional[str] = Field(
        None,
        min_length=1,
        description="New related concept ID"
    )
    source_location: Optional[str] = Field(
        None,
        max_length=255,
        description="Page number (PDF) or timestamp (audio/video)"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Response Schemas
# ═══════════════════════════════════════════════════════════════════════════════

class MultimodalResponse(BaseModel):
    """
    Response model for multimodal content.

    Matches frontend MediaItem interface for seamless integration.

    [Source: docs/stories/35.1.story.md#AC-35.1.1]
    [Source: specs/data/multimodal-content.schema.json]
    [Source: canvas-progress-tracker/obsidian-plugin/src/types/media.ts#MediaItem]
    """
    id: str = Field(..., description="Unique content identifier (UUID)")
    media_type: MultimodalMediaType = Field(..., description="Type of media content")
    file_path: str = Field(..., description="Path to the media file")
    related_concept_id: str = Field(..., description="Associated Canvas concept node ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    thumbnail_path: Optional[str] = Field(None, description="Path to thumbnail image")
    extracted_text: Optional[str] = Field(None, description="OCR-extracted text (images/PDFs)")
    description: Optional[str] = Field(None, description="AI-generated or user description")
    source_location: Optional[str] = Field(None, description="Page number or timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    metadata: Optional[MultimodalMetadataSchema] = Field(
        None,
        description="Additional metadata (dimensions, duration, etc.)"
    )

    model_config = ConfigDict(from_attributes=True)


class MultimodalUploadResponse(BaseModel):
    """
    Response model for successful upload.

    [Source: docs/stories/35.1.story.md#AC-35.1.1]
    """
    content: MultimodalResponse = Field(..., description="Uploaded content details")
    message: str = Field(
        default="Content uploaded successfully",
        description="Status message"
    )
    thumbnail_generated: bool = Field(
        default=False,
        description="Whether thumbnail was generated"
    )


class MultimodalDeleteResponse(BaseModel):
    """
    Response model for successful deletion.

    [Source: docs/stories/35.1.story.md#AC-35.1.3]
    """
    deleted_id: str = Field(..., description="ID of deleted content")
    message: str = Field(
        default="Content deleted successfully",
        description="Status message"
    )
    file_deleted: bool = Field(
        default=True,
        description="Whether physical file was deleted"
    )
    thumbnail_deleted: bool = Field(
        default=False,
        description="Whether thumbnail was also deleted"
    )


class MultimodalListResponse(BaseModel):
    """
    Response model for listing multimodal content.

    [Source: Story 35.1 - Additional utility endpoint]
    """
    items: list[MultimodalResponse] = Field(
        default_factory=list,
        description="List of multimodal content items"
    )
    total: int = Field(..., ge=0, description="Total item count")
    concept_id: Optional[str] = Field(None, description="Filter concept ID if applied")
    media_type: Optional[MultimodalMediaType] = Field(None, description="Filter media type if applied")


class MultimodalHealthResponse(BaseModel):
    """
    Response model for multimodal service health check.

    [Source: Story 35.1 - Service health endpoint]
    """
    status: str = Field(..., description="Service status: healthy/degraded/unhealthy")
    lancedb_connected: bool = Field(..., description="LanceDB connection status")
    neo4j_connected: bool = Field(..., description="Neo4j connection status")
    storage_path_writable: bool = Field(..., description="Storage path write access")
    total_items: int = Field(0, ge=0, description="Total stored items count")


# ═══════════════════════════════════════════════════════════════════════════════
# Story 35.2: Query/Search API Schemas
# [Source: docs/stories/35.2.story.md]
# [Source: canvas-progress-tracker/obsidian-plugin/src/components/MediaPanel.ts#MediaItem]
# ═══════════════════════════════════════════════════════════════════════════════

class MediaItemResponse(BaseModel):
    """
    Response model matching frontend MediaItem interface.

    This is the core response model for all query endpoints,
    matching the TypeScript MediaItem interface exactly.

    [Source: docs/stories/35.2.story.md#AC-35.2.4]
    [Source: canvas-progress-tracker/obsidian-plugin/src/components/MediaPanel.ts:30-45]
    """
    id: str = Field(..., description="Unique content identifier (UUID)")
    type: str = Field(
        ...,
        pattern="^(image|pdf|audio|video)$",
        description="Media type: 'image' | 'pdf' | 'audio' | 'video'"
    )
    path: str = Field(..., description="File path")
    title: Optional[str] = Field(None, max_length=50, description="Title (truncated to 50 chars)")
    relevanceScore: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Relevance score (0-1)"
    )
    conceptId: Optional[str] = Field(None, description="Related concept node ID")
    metadata: Optional[dict[str, Any]] = Field(
        None,
        description="Additional metadata (dimensions, duration, etc.)"
    )
    thumbnail: Optional[str] = Field(None, description="Base64 encoded thumbnail image")

    model_config = ConfigDict(from_attributes=True)


class PaginationMeta(BaseModel):
    """
    Pagination metadata matching frontend pagination standards.

    [Source: docs/stories/35.2.story.md#AC-35.2.3]
    [Source: specs/data/pagination-meta.schema.json]
    """
    total: int = Field(..., ge=0, description="Total number of items")
    page: int = Field(..., ge=1, description="Current page number (1-indexed)")
    page_size: int = Field(..., ge=1, le=100, description="Items per page")
    total_pages: int = Field(..., ge=0, description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")


class MultimodalByConceptResponse(BaseModel):
    """
    Response model for GET /api/v1/multimodal/by-concept/{concept_id}.

    [Source: docs/stories/35.2.story.md#AC-35.2.1]
    """
    items: List[MediaItemResponse] = Field(
        default_factory=list,
        description="List of media items associated with the concept"
    )
    total: int = Field(..., ge=0, description="Total number of items")


class MultimodalSearchRequest(BaseModel):
    """
    Request model for POST /api/v1/multimodal/search.

    [Source: docs/stories/35.2.story.md#AC-35.2.2]
    """
    query: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Search query text for semantic search"
    )
    media_types: Optional[List[MultimodalMediaType]] = Field(
        None,
        description="Optional filter by media types"
    )
    top_k: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum number of results"
    )
    min_score: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score threshold"
    )

    @field_validator("query")
    @classmethod
    def query_not_empty(cls, v: str) -> str:
        """Validate query is not just whitespace."""
        if not v.strip():
            raise ValueError("Query cannot be empty or whitespace only")
        return v.strip()


class MultimodalSearchResponse(BaseModel):
    """
    Response model for POST /api/v1/multimodal/search.

    [Source: docs/stories/35.2.story.md#AC-35.2.2]
    """
    items: List[MediaItemResponse] = Field(
        default_factory=list,
        description="List of search results sorted by relevance"
    )
    total: int = Field(..., ge=0, description="Number of results returned")
    query_processed: bool = Field(
        default=True,
        description="Whether the query was successfully processed"
    )


class MultimodalPaginatedListResponse(BaseModel):
    """
    Response model for GET /api/v1/multimodal/list with pagination.

    [Source: docs/stories/35.2.story.md#AC-35.2.3]
    """
    items: List[MediaItemResponse] = Field(
        default_factory=list,
        description="List of media items for current page"
    )
    pagination: PaginationMeta = Field(..., description="Pagination metadata")
