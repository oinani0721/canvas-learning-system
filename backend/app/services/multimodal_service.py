# Canvas Learning System - Multimodal Service
# Story 35.1: Multimodal Upload/Management API Endpoints
# [Source: docs/stories/35.1.story.md]
"""
Multimodal Service - File upload and management business logic.

Story 35.1 Implementation:
- AC-35.1.1: POST /api/v1/multimodal/upload - File upload with validation
- AC-35.1.2: POST /api/v1/multimodal/upload-url - URL content fetch
- AC-35.1.3: DELETE /api/v1/multimodal/{content_id} - Delete content
- AC-35.1.4: PUT /api/v1/multimodal/{content_id} - Update metadata
- AC-35.1.5: GET /api/v1/multimodal/{content_id} - Retrieve content

[Source: docs/stories/35.1.story.md#Task-2]
[Source: src/agentic_rag/storage/multimodal_store.py]
"""

import asyncio
import base64
import hashlib
import logging
import math
import mimetypes
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, BinaryIO, List, Optional, Tuple

import httpx

from app.models.multimodal_schemas import (
    # Story 35.1: Upload/Management
    MultimodalDeleteResponse,
    MultimodalHealthResponse,
    MultimodalListResponse,
    MultimodalMediaType,
    MultimodalMetadataSchema,
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

logger = logging.getLogger(__name__)

# Supported MIME types per media type
SUPPORTED_MIME_TYPES = {
    MultimodalMediaType.IMAGE: {
        "image/jpeg", "image/png", "image/gif", "image/webp", "image/bmp", "image/svg+xml"
    },
    MultimodalMediaType.PDF: {"application/pdf"},
    MultimodalMediaType.AUDIO: {
        "audio/mpeg", "audio/wav", "audio/ogg", "audio/mp4", "audio/flac", "audio/aac"
    },
    MultimodalMediaType.VIDEO: {
        "video/mp4", "video/webm", "video/x-matroska", "video/avi", "video/quicktime", "video/x-ms-wmv"
    },
}

# Extension to media type mapping
EXTENSION_MEDIA_TYPE = {
    ".jpg": MultimodalMediaType.IMAGE,
    ".jpeg": MultimodalMediaType.IMAGE,
    ".png": MultimodalMediaType.IMAGE,
    ".gif": MultimodalMediaType.IMAGE,
    ".webp": MultimodalMediaType.IMAGE,
    ".bmp": MultimodalMediaType.IMAGE,
    ".svg": MultimodalMediaType.IMAGE,
    ".pdf": MultimodalMediaType.PDF,
    ".mp3": MultimodalMediaType.AUDIO,
    ".wav": MultimodalMediaType.AUDIO,
    ".ogg": MultimodalMediaType.AUDIO,
    ".m4a": MultimodalMediaType.AUDIO,
    ".flac": MultimodalMediaType.AUDIO,
    ".aac": MultimodalMediaType.AUDIO,
    ".mp4": MultimodalMediaType.VIDEO,
    ".webm": MultimodalMediaType.VIDEO,
    ".mkv": MultimodalMediaType.VIDEO,
    ".avi": MultimodalMediaType.VIDEO,
    ".mov": MultimodalMediaType.VIDEO,
    ".wmv": MultimodalMediaType.VIDEO,
}

# Maximum file size (50MB)
MAX_FILE_SIZE = 50 * 1024 * 1024

# URL fetch timeout
URL_FETCH_TIMEOUT = 30.0


class MultimodalServiceError(Exception):
    """Base exception for multimodal service errors."""

    def __init__(self, message: str, error_code: str = "MULTIMODAL_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class FileValidationError(MultimodalServiceError):
    """File validation failed."""

    def __init__(self, message: str):
        super().__init__(message, "FILE_VALIDATION_ERROR")


class ContentNotFoundError(MultimodalServiceError):
    """Content not found."""

    def __init__(self, content_id: str):
        super().__init__(f"Content not found: {content_id}", "CONTENT_NOT_FOUND")


class MultimodalService:
    """
    Multimodal content management service.

    Provides business logic for uploading, managing, and retrieving
    multimodal content (images, PDFs, audio, video).

    [Source: docs/stories/35.1.story.md#Task-2]
    """

    # Storage base path (relative to project root)
    DEFAULT_STORAGE_PATH = ".canvas-learning/multimodal"

    def __init__(
        self,
        storage_base_path: Optional[str] = None,
        multimodal_store=None,
    ):
        """
        Initialize MultimodalService.

        Args:
            storage_base_path: Base path for file storage
            multimodal_store: Optional MultimodalStore instance

        [Source: docs/stories/35.1.story.md#Task-2.1]
        """
        self.storage_base_path = Path(storage_base_path or self.DEFAULT_STORAGE_PATH)
        self.multimodal_store = multimodal_store
        self._initialized = False

        # In-memory content store (when MultimodalStore is not available)
        self._content_store: dict[str, dict] = {}

        # Ensure storage directories exist
        self._ensure_storage_dirs()

    def _ensure_storage_dirs(self) -> None:
        """Create storage directories if they don't exist."""
        for media_type in MultimodalMediaType:
            dir_path = self.storage_base_path / media_type.value
            dir_path.mkdir(parents=True, exist_ok=True)
        # Also create thumbnails directory
        (self.storage_base_path / "thumbnails").mkdir(parents=True, exist_ok=True)

    async def initialize(self) -> bool:
        """Initialize the service."""
        if self._initialized:
            return True

        self._ensure_storage_dirs()
        self._initialized = True
        logger.info("MultimodalService initialized successfully")
        return True

    def _detect_media_type(
        self,
        filename: str,
        content_type: Optional[str] = None
    ) -> MultimodalMediaType:
        """
        Detect media type from filename and/or content type.

        Args:
            filename: Original filename
            content_type: MIME content type

        Returns:
            Detected media type

        Raises:
            FileValidationError: If file type is not supported
        """
        # Try extension first
        ext = Path(filename).suffix.lower()
        if ext in EXTENSION_MEDIA_TYPE:
            return EXTENSION_MEDIA_TYPE[ext]

        # Try content type
        if content_type:
            for media_type, mime_types in SUPPORTED_MIME_TYPES.items():
                if content_type in mime_types:
                    return media_type

        raise FileValidationError(
            f"Unsupported file type: {ext or content_type}"
        )

    def _validate_file(
        self,
        filename: str,
        content_type: Optional[str],
        file_size: int
    ) -> MultimodalMediaType:
        """
        Validate uploaded file.

        Args:
            filename: Original filename
            content_type: MIME content type
            file_size: File size in bytes

        Returns:
            Detected media type

        Raises:
            FileValidationError: If validation fails
        """
        # Validate file size
        if file_size > MAX_FILE_SIZE:
            raise FileValidationError(
                f"File too large: {file_size / 1024 / 1024:.1f}MB (max: 50MB)"
            )

        # Validate and detect media type
        media_type = self._detect_media_type(filename, content_type)

        # Validate content type matches detected media type
        if content_type:
            expected_mimes = SUPPORTED_MIME_TYPES.get(media_type, set())
            if content_type not in expected_mimes:
                logger.warning(
                    f"Content-Type mismatch: {content_type} vs expected {expected_mimes}"
                )

        return media_type

    def _generate_unique_filename(
        self,
        original_filename: str,
        media_type: MultimodalMediaType
    ) -> str:
        """
        Generate a unique filename for storage.

        Args:
            original_filename: Original filename
            media_type: Media type

        Returns:
            Unique filename
        """
        ext = Path(original_filename).suffix.lower()
        unique_id = uuid.uuid4().hex[:16]
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"{timestamp}_{unique_id}{ext}"

    async def upload_file(
        self,
        file: BinaryIO,
        filename: str,
        content_type: Optional[str],
        file_size: int,
        related_concept_id: str,
        canvas_path: str,
        description: Optional[str] = None,
    ) -> MultimodalUploadResponse:
        """
        Upload a file from binary content.

        Args:
            file: File-like object with binary content
            filename: Original filename
            content_type: MIME content type
            file_size: File size in bytes
            related_concept_id: Canvas node ID to associate with
            canvas_path: Canvas file path
            description: Optional description

        Returns:
            MultimodalUploadResponse with content details

        Raises:
            FileValidationError: If file validation fails

        [Source: docs/stories/35.1.story.md#AC-35.1.1]
        """
        if not self._initialized:
            await self.initialize()

        # Validate file
        media_type = self._validate_file(filename, content_type, file_size)

        # Generate unique filename and path
        unique_filename = self._generate_unique_filename(filename, media_type)
        file_path = self.storage_base_path / media_type.value / unique_filename

        # Save file to disk
        try:
            with open(file_path, "wb") as f:
                shutil.copyfileobj(file, f)
        except Exception as e:
            logger.error(f"Failed to save file: {e}")
            raise MultimodalServiceError(f"Failed to save file: {e}")

        # Generate content ID
        content_id = str(uuid.uuid4())

        # Build metadata
        metadata = MultimodalMetadataSchema(
            file_size=file_size,
            mime_type=content_type or mimetypes.guess_type(filename)[0],
        )

        # Create content record
        content_data = {
            "id": content_id,
            "media_type": media_type,
            "file_path": str(file_path),
            "related_concept_id": related_concept_id,
            "created_at": datetime.now(),
            "description": description,
            "metadata": metadata,
        }

        # Store in memory (and multimodal_store if available)
        self._content_store[content_id] = content_data

        if self.multimodal_store:
            try:
                from src.agentic_rag.models.multimodal_content import (
                    MediaType,
                    MultimodalContent,
                    MultimodalMetadata,
                )

                mm_content = MultimodalContent(
                    id=content_id,
                    media_type=MediaType(media_type.value),
                    file_path=str(file_path),
                    related_concept_id=related_concept_id,
                    description=description,
                    metadata=MultimodalMetadata(
                        file_size=file_size,
                        mime_type=content_type,
                    ),
                )
                await self.multimodal_store.add(mm_content)
            except Exception as e:
                logger.warning(f"Failed to add to MultimodalStore: {e}")

        # Build response
        response_content = MultimodalResponse(
            id=content_id,
            media_type=media_type,
            file_path=str(file_path),
            related_concept_id=related_concept_id,
            created_at=content_data["created_at"],
            description=description,
            metadata=metadata,
        )

        logger.info(
            f"Uploaded file: {content_id} ({media_type.value}) - {file_size} bytes"
        )

        return MultimodalUploadResponse(
            content=response_content,
            message="Content uploaded successfully",
            thumbnail_generated=False,  # Thumbnail generation is async
        )

    async def upload_from_url(
        self,
        request: MultimodalUploadUrlRequest,
    ) -> MultimodalUploadResponse:
        """
        Upload content from URL.

        Args:
            request: URL upload request

        Returns:
            MultimodalUploadResponse with content details

        Raises:
            FileValidationError: If file validation fails
            MultimodalServiceError: If URL fetch fails

        [Source: docs/stories/35.1.story.md#AC-35.1.2]
        """
        if not self._initialized:
            await self.initialize()

        # Fetch content from URL
        try:
            async with httpx.AsyncClient(timeout=URL_FETCH_TIMEOUT) as client:
                response = await client.get(request.url, follow_redirects=True)
                response.raise_for_status()
        except httpx.TimeoutException:
            raise MultimodalServiceError(
                f"URL fetch timeout after {URL_FETCH_TIMEOUT}s"
            )
        except httpx.HTTPStatusError as e:
            raise MultimodalServiceError(
                f"URL fetch failed: HTTP {e.response.status_code}"
            )
        except Exception as e:
            raise MultimodalServiceError(f"URL fetch failed: {e}")

        # Extract filename from URL
        url_path = Path(request.url.split("?")[0])
        filename = url_path.name or "downloaded_content"

        # Get content type and size
        content_type = response.headers.get("content-type", "").split(";")[0]
        content_bytes = response.content
        file_size = len(content_bytes)

        # Validate
        media_type = self._validate_file(filename, content_type, file_size)

        # Generate unique filename and path
        unique_filename = self._generate_unique_filename(filename, media_type)
        file_path = self.storage_base_path / media_type.value / unique_filename

        # Save to disk
        try:
            with open(file_path, "wb") as f:
                f.write(content_bytes)
        except Exception as e:
            logger.error(f"Failed to save URL content: {e}")
            raise MultimodalServiceError(f"Failed to save content: {e}")

        # Generate content ID
        content_id = str(uuid.uuid4())

        # Build metadata
        metadata = MultimodalMetadataSchema(
            file_size=file_size,
            mime_type=content_type or mimetypes.guess_type(filename)[0],
        )

        # Create content record
        content_data = {
            "id": content_id,
            "media_type": media_type,
            "file_path": str(file_path),
            "related_concept_id": request.related_concept_id,
            "created_at": datetime.now(),
            "description": request.description,
            "metadata": metadata,
        }

        # Store
        self._content_store[content_id] = content_data

        # Build response
        response_content = MultimodalResponse(
            id=content_id,
            media_type=media_type,
            file_path=str(file_path),
            related_concept_id=request.related_concept_id,
            created_at=content_data["created_at"],
            description=request.description,
            metadata=metadata,
        )

        logger.info(
            f"Uploaded from URL: {content_id} ({media_type.value}) - {file_size} bytes"
        )

        return MultimodalUploadResponse(
            content=response_content,
            message="Content uploaded from URL successfully",
            thumbnail_generated=False,
        )

    async def get_content(self, content_id: str) -> MultimodalResponse:
        """
        Get content by ID.

        Args:
            content_id: Content UUID

        Returns:
            MultimodalResponse with content details

        Raises:
            ContentNotFoundError: If content not found

        [Source: docs/stories/35.1.story.md#AC-35.1.5]
        """
        if not self._initialized:
            await self.initialize()

        # Check in-memory store
        if content_id in self._content_store:
            data = self._content_store[content_id]
            return MultimodalResponse(
                id=data["id"],
                media_type=data["media_type"],
                file_path=data["file_path"],
                related_concept_id=data["related_concept_id"],
                created_at=data["created_at"],
                thumbnail_path=data.get("thumbnail_path"),
                extracted_text=data.get("extracted_text"),
                description=data.get("description"),
                source_location=data.get("source_location"),
                updated_at=data.get("updated_at"),
                metadata=data.get("metadata"),
            )

        # Try multimodal_store
        if self.multimodal_store:
            try:
                content = await self.multimodal_store.get(content_id)
                if content:
                    return MultimodalResponse(
                        id=content.id,
                        media_type=MultimodalMediaType(content.media_type.value),
                        file_path=content.file_path,
                        related_concept_id=content.related_concept_id,
                        created_at=content.created_at,
                        thumbnail_path=content.thumbnail_path,
                        extracted_text=content.extracted_text,
                        description=content.description,
                        source_location=content.source_location,
                        updated_at=content.updated_at,
                        metadata=MultimodalMetadataSchema(
                            file_size=content.metadata.file_size,
                            width=content.metadata.width,
                            height=content.metadata.height,
                            duration=content.metadata.duration,
                            page_count=content.metadata.page_count,
                            mime_type=content.metadata.mime_type,
                        ) if content.metadata else None,
                    )
            except Exception as e:
                logger.warning(f"MultimodalStore get failed: {e}")

        raise ContentNotFoundError(content_id)

    async def update_content(
        self,
        content_id: str,
        request: MultimodalUpdateRequest,
    ) -> MultimodalResponse:
        """
        Update content metadata.

        Args:
            content_id: Content UUID
            request: Update request

        Returns:
            Updated MultimodalResponse

        Raises:
            ContentNotFoundError: If content not found

        [Source: docs/stories/35.1.story.md#AC-35.1.4]
        """
        if not self._initialized:
            await self.initialize()

        # Get existing content
        if content_id not in self._content_store:
            raise ContentNotFoundError(content_id)

        data = self._content_store[content_id]

        # Apply updates
        if request.description is not None:
            data["description"] = request.description
        if request.related_concept_id is not None:
            data["related_concept_id"] = request.related_concept_id
        if request.source_location is not None:
            data["source_location"] = request.source_location

        data["updated_at"] = datetime.now()

        # Update in multimodal_store if available
        if self.multimodal_store:
            try:
                await self.multimodal_store.update(
                    content_id,
                    {
                        "description": request.description,
                        "related_concept_id": request.related_concept_id,
                        "source_location": request.source_location,
                    }
                )
            except Exception as e:
                logger.warning(f"MultimodalStore update failed: {e}")

        logger.info(f"Updated content: {content_id}")

        return MultimodalResponse(
            id=data["id"],
            media_type=data["media_type"],
            file_path=data["file_path"],
            related_concept_id=data["related_concept_id"],
            created_at=data["created_at"],
            thumbnail_path=data.get("thumbnail_path"),
            extracted_text=data.get("extracted_text"),
            description=data.get("description"),
            source_location=data.get("source_location"),
            updated_at=data.get("updated_at"),
            metadata=data.get("metadata"),
        )

    async def delete_content(self, content_id: str) -> MultimodalDeleteResponse:
        """
        Delete content.

        Args:
            content_id: Content UUID

        Returns:
            MultimodalDeleteResponse

        Raises:
            ContentNotFoundError: If content not found

        [Source: docs/stories/35.1.story.md#AC-35.1.3]
        """
        if not self._initialized:
            await self.initialize()

        # Get content data
        if content_id not in self._content_store:
            raise ContentNotFoundError(content_id)

        data = self._content_store[content_id]
        file_path = Path(data["file_path"])
        thumbnail_path = data.get("thumbnail_path")

        # Delete physical file
        file_deleted = False
        if file_path.exists():
            try:
                file_path.unlink()
                file_deleted = True
            except Exception as e:
                logger.warning(f"Failed to delete file: {e}")

        # Delete thumbnail if exists
        thumbnail_deleted = False
        if thumbnail_path:
            thumb_path = Path(thumbnail_path)
            if thumb_path.exists():
                try:
                    thumb_path.unlink()
                    thumbnail_deleted = True
                except Exception as e:
                    logger.warning(f"Failed to delete thumbnail: {e}")

        # Remove from store
        del self._content_store[content_id]

        # Delete from multimodal_store if available
        if self.multimodal_store:
            try:
                await self.multimodal_store.delete(content_id)
            except Exception as e:
                logger.warning(f"MultimodalStore delete failed: {e}")

        logger.info(f"Deleted content: {content_id}")

        return MultimodalDeleteResponse(
            deleted_id=content_id,
            message="Content deleted successfully",
            file_deleted=file_deleted,
            thumbnail_deleted=thumbnail_deleted,
        )

    async def list_content(
        self,
        concept_id: Optional[str] = None,
        media_type: Optional[MultimodalMediaType] = None,
        limit: int = 100,
    ) -> MultimodalListResponse:
        """
        List multimodal content.

        Args:
            concept_id: Filter by concept ID
            media_type: Filter by media type
            limit: Maximum items to return

        Returns:
            MultimodalListResponse

        [Source: Story 35.1 - Additional utility endpoint]
        """
        if not self._initialized:
            await self.initialize()

        items = []

        for content_id, data in self._content_store.items():
            # Apply filters
            if concept_id and data["related_concept_id"] != concept_id:
                continue
            if media_type and data["media_type"] != media_type:
                continue

            items.append(
                MultimodalResponse(
                    id=data["id"],
                    media_type=data["media_type"],
                    file_path=data["file_path"],
                    related_concept_id=data["related_concept_id"],
                    created_at=data["created_at"],
                    thumbnail_path=data.get("thumbnail_path"),
                    extracted_text=data.get("extracted_text"),
                    description=data.get("description"),
                    source_location=data.get("source_location"),
                    updated_at=data.get("updated_at"),
                    metadata=data.get("metadata"),
                )
            )

            if len(items) >= limit:
                break

        return MultimodalListResponse(
            items=items,
            total=len(items),
            concept_id=concept_id,
            media_type=media_type,
        )

    async def get_health_status(self) -> MultimodalHealthResponse:
        """
        Get service health status.

        Returns:
            MultimodalHealthResponse

        [Source: Story 35.1 - Service health endpoint]
        """
        if not self._initialized:
            await self.initialize()

        # Check storage path
        storage_writable = False
        try:
            test_file = self.storage_base_path / ".health_check"
            test_file.write_text("test")
            test_file.unlink()
            storage_writable = True
        except Exception:
            pass

        # Check LanceDB and Neo4j if multimodal_store is available
        lancedb_connected = False
        neo4j_connected = False

        if self.multimodal_store:
            try:
                health = await self.multimodal_store.health_check()
                lancedb_connected = health.get("lancedb", False)
                neo4j_connected = health.get("neo4j", False)
            except Exception:
                pass

        # Determine overall status
        if storage_writable and (lancedb_connected or not self.multimodal_store):
            status = "healthy"
        elif storage_writable:
            status = "degraded"
        else:
            status = "unhealthy"

        return MultimodalHealthResponse(
            status=status,
            lancedb_connected=lancedb_connected,
            neo4j_connected=neo4j_connected,
            storage_path_writable=storage_writable,
            total_items=len(self._content_store),
        )

    # ═══════════════════════════════════════════════════════════════════════════════
    # Story 35.2: Query/Search API Methods
    # [Source: docs/stories/35.2.story.md]
    # ═══════════════════════════════════════════════════════════════════════════════

    def _to_media_item(
        self,
        data: dict,
        score: float = 1.0,
        include_thumbnail: bool = False,
    ) -> MediaItemResponse:
        """
        Convert internal content data to MediaItemResponse.

        Maps MultimodalContent fields to frontend MediaItem interface.

        [Source: docs/stories/35.2.story.md#AC-35.2.4]
        [Source: docs/stories/35.2.story.md#Task-1.2]

        Args:
            data: Content data dictionary
            score: Relevance score (0-1), default 1.0 for exact queries
            include_thumbnail: Whether to load and encode thumbnail

        Returns:
            MediaItemResponse matching frontend interface
        """
        # Extract title from description (truncate to 50 chars)
        title = None
        if data.get("description"):
            title = data["description"][:50]

        # Load thumbnail if requested
        thumbnail_base64 = None
        if include_thumbnail and data.get("thumbnail_path"):
            thumbnail_base64 = self._load_thumbnail_base64(data["thumbnail_path"])

        # Convert metadata to dict if it's a schema object
        metadata_dict = None
        if data.get("metadata"):
            meta = data["metadata"]
            if isinstance(meta, MultimodalMetadataSchema):
                metadata_dict = {
                    "file_size": meta.file_size,
                    "width": meta.width,
                    "height": meta.height,
                    "duration": meta.duration,
                    "page_count": meta.page_count,
                    "mime_type": meta.mime_type,
                }
            elif isinstance(meta, dict):
                metadata_dict = meta
            else:
                # Handle MultimodalMetadata from agentic_rag
                metadata_dict = meta.to_dict() if hasattr(meta, "to_dict") else {}

        return MediaItemResponse(
            id=data["id"],
            type=data["media_type"].value if hasattr(data["media_type"], "value") else data["media_type"],
            path=data["file_path"],
            title=title,
            relevanceScore=score,
            conceptId=data.get("related_concept_id"),
            metadata=metadata_dict,
            thumbnail=thumbnail_base64,
        )

    def _load_thumbnail_base64(self, thumbnail_path: str) -> Optional[str]:
        """
        Load thumbnail file and encode as base64.

        [Source: docs/stories/35.2.story.md#Task-4.2]

        Args:
            thumbnail_path: Path to thumbnail file

        Returns:
            Base64 encoded thumbnail string, or None if failed
        """
        try:
            thumb_path = Path(thumbnail_path)
            if thumb_path.exists():
                with open(thumb_path, "rb") as f:
                    return base64.b64encode(f.read()).decode("utf-8")
        except Exception as e:
            logger.warning(f"Failed to load thumbnail {thumbnail_path}: {e}")
        return None

    async def get_by_concept(
        self,
        concept_id: str,
        media_type: Optional[MultimodalMediaType] = None,
        limit: int = 100,
        include_thumbnail: bool = False,
    ) -> MultimodalByConceptResponse:
        """
        Get all content associated with a concept.

        [Source: docs/stories/35.2.story.md#AC-35.2.1]
        [Source: docs/stories/35.2.story.md#Task-1.1]

        Args:
            concept_id: Concept node ID to query
            media_type: Optional media type filter
            limit: Maximum items to return (default 100, max 200)
            include_thumbnail: Whether to include base64 thumbnails

        Returns:
            MultimodalByConceptResponse with matching items
        """
        if not self._initialized:
            await self.initialize()

        items: List[MediaItemResponse] = []

        # Query from multimodal_store if available
        if self.multimodal_store:
            try:
                # Convert to agentic_rag MediaType if needed
                store_media_type = None
                if media_type:
                    from src.agentic_rag.models.multimodal_content import MediaType
                    store_media_type = MediaType(media_type.value)

                contents = await self.multimodal_store.get_by_concept(
                    concept_id=concept_id,
                    media_type=store_media_type,
                )

                for content in contents[:limit]:
                    items.append(self._content_to_media_item(content, 1.0, include_thumbnail))

            except Exception as e:
                logger.warning(f"MultimodalStore get_by_concept failed: {e}")

        # Fallback to in-memory store
        if not items:
            for content_id, data in self._content_store.items():
                if data["related_concept_id"] != concept_id:
                    continue
                if media_type and data["media_type"] != media_type:
                    continue

                items.append(self._to_media_item(data, 1.0, include_thumbnail))

                if len(items) >= limit:
                    break

        return MultimodalByConceptResponse(
            items=items,
            total=len(items),
        )

    def _content_to_media_item(
        self,
        content,
        score: float = 1.0,
        include_thumbnail: bool = False,
    ) -> MediaItemResponse:
        """
        Convert MultimodalContent object to MediaItemResponse.

        [Source: docs/stories/35.2.story.md#AC-35.2.4]

        Args:
            content: MultimodalContent from agentic_rag
            score: Relevance score (0-1)
            include_thumbnail: Whether to load thumbnail

        Returns:
            MediaItemResponse
        """
        # Extract title from description
        title = None
        if content.description:
            title = content.description[:50]

        # Load thumbnail if requested
        thumbnail_base64 = None
        if include_thumbnail and content.thumbnail_path:
            thumbnail_base64 = self._load_thumbnail_base64(content.thumbnail_path)

        # Convert metadata
        metadata_dict = None
        if content.metadata:
            metadata_dict = content.metadata.to_dict()

        return MediaItemResponse(
            id=content.id,
            type=content.media_type.value,
            path=content.file_path,
            title=title,
            relevanceScore=score,
            conceptId=content.related_concept_id,
            metadata=metadata_dict,
            thumbnail=thumbnail_base64,
        )

    async def search(
        self,
        request: MultimodalSearchRequest,
        include_thumbnail: bool = False,
    ) -> MultimodalSearchResponse:
        """
        Search content using vector similarity.

        [Source: docs/stories/35.2.story.md#AC-35.2.2]
        [Source: docs/stories/35.2.story.md#Task-2]

        Args:
            request: Search request with query, filters
            include_thumbnail: Whether to include base64 thumbnails

        Returns:
            MultimodalSearchResponse with search results
        """
        if not self._initialized:
            await self.initialize()

        items: List[MediaItemResponse] = []

        # Try multimodal_store with embedding
        if self.multimodal_store:
            try:
                # Generate embedding for query
                query_vector = await self._generate_embedding(request.query)

                if query_vector:
                    # Convert media types
                    store_media_types = None
                    if request.media_types:
                        from src.agentic_rag.models.multimodal_content import MediaType
                        store_media_types = [MediaType(mt.value) for mt in request.media_types]

                    # Perform vector search
                    results = await self.multimodal_store.search(
                        query_vector=query_vector,
                        media_types=store_media_types,
                        top_k=request.top_k,
                        min_score=request.min_score,
                    )

                    # Convert to MediaItemResponse
                    for content, score in results:
                        items.append(self._content_to_media_item(content, score, include_thumbnail))

                    return MultimodalSearchResponse(
                        items=items,
                        total=len(items),
                        query_processed=True,
                    )

            except Exception as e:
                logger.warning(f"MultimodalStore search failed: {e}")

        # Fallback: simple text search in descriptions
        logger.info("Using fallback text search (no embedding available)")

        query_lower = request.query.lower()
        scored_items: List[Tuple[dict, float]] = []

        for content_id, data in self._content_store.items():
            # Apply media type filter
            if request.media_types:
                if data["media_type"] not in request.media_types:
                    continue

            # Simple text match scoring
            score = 0.0
            if data.get("description"):
                if query_lower in data["description"].lower():
                    score = 0.8
            if data.get("extracted_text"):
                if query_lower in data["extracted_text"].lower():
                    score = max(score, 0.7)

            if score >= request.min_score:
                scored_items.append((data, score))

        # Sort by score descending
        scored_items.sort(key=lambda x: x[1], reverse=True)

        # Take top_k
        for data, score in scored_items[:request.top_k]:
            items.append(self._to_media_item(data, score, include_thumbnail))

        return MultimodalSearchResponse(
            items=items,
            total=len(items),
            query_processed=False,  # Indicates fallback was used
        )

    async def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding vector for text.

        [Source: docs/stories/35.2.story.md#Task-2.2]
        [ADR-009: Embedding retry strategy - 2 retries, 2s interval]

        Args:
            text: Text to embed

        Returns:
            768-dimensional embedding vector, or None if failed
        """
        try:
            # Try to use the RAG embedding service
            from src.agentic_rag.embedding.embedding_service import get_embedding_service

            service = get_embedding_service()
            if service:
                vector = await service.embed_text(text)
                if vector and len(vector) == 768:
                    return vector

        except ImportError:
            logger.debug("Embedding service not available")
        except Exception as e:
            logger.warning(f"Embedding generation failed: {e}")

        return None

    async def list_all(
        self,
        page: int = 1,
        page_size: int = 20,
        media_type: Optional[MultimodalMediaType] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        include_thumbnail: bool = False,
    ) -> MultimodalPaginatedListResponse:
        """
        List all content with pagination.

        [Source: docs/stories/35.2.story.md#AC-35.2.3]
        [Source: docs/stories/35.2.story.md#Task-4.1]

        Note: MultimodalStore.list_by_type() only supports single type filter
        and no sorting. This method implements in-memory sorting and aggregation.

        Args:
            page: Page number (1-indexed)
            page_size: Items per page (max 100)
            media_type: Optional filter by media type
            sort_by: Sort field (created_at/updated_at)
            sort_order: Sort direction (asc/desc)
            include_thumbnail: Whether to include base64 thumbnails

        Returns:
            MultimodalPaginatedListResponse with paginated results
        """
        if not self._initialized:
            await self.initialize()

        all_items: List[dict] = []

        # Collect items from multimodal_store
        if self.multimodal_store:
            try:
                if media_type:
                    from src.agentic_rag.models.multimodal_content import MediaType
                    contents = await self.multimodal_store.list_by_type(
                        media_type=MediaType(media_type.value),
                        limit=1000,  # Get more for accurate pagination
                    )
                    for content in contents:
                        all_items.append({
                            "id": content.id,
                            "media_type": MultimodalMediaType(content.media_type.value),
                            "file_path": content.file_path,
                            "related_concept_id": content.related_concept_id,
                            "created_at": content.created_at,
                            "updated_at": content.updated_at,
                            "description": content.description,
                            "thumbnail_path": content.thumbnail_path,
                            "metadata": content.metadata,
                        })
                else:
                    # Aggregate all types
                    from src.agentic_rag.models.multimodal_content import MediaType
                    for mt in MediaType:
                        try:
                            contents = await self.multimodal_store.list_by_type(
                                media_type=mt,
                                limit=500,
                            )
                            for content in contents:
                                all_items.append({
                                    "id": content.id,
                                    "media_type": MultimodalMediaType(content.media_type.value),
                                    "file_path": content.file_path,
                                    "related_concept_id": content.related_concept_id,
                                    "created_at": content.created_at,
                                    "updated_at": content.updated_at,
                                    "description": content.description,
                                    "thumbnail_path": content.thumbnail_path,
                                    "metadata": content.metadata,
                                })
                        except Exception:
                            pass

            except Exception as e:
                logger.warning(f"MultimodalStore list failed: {e}")

        # Fallback to in-memory store
        if not all_items:
            for content_id, data in self._content_store.items():
                if media_type and data["media_type"] != media_type:
                    continue
                all_items.append(data)

        # Sort items
        reverse = sort_order.lower() == "desc"
        sort_key = sort_by if sort_by in ("created_at", "updated_at") else "created_at"

        def get_sort_value(item: dict):
            value = item.get(sort_key)
            if value is None:
                return datetime.min if not reverse else datetime.max
            return value

        all_items.sort(key=get_sort_value, reverse=reverse)

        # Calculate pagination
        total = len(all_items)
        total_pages = math.ceil(total / page_size) if total > 0 else 0
        offset = (page - 1) * page_size
        paginated_items = all_items[offset:offset + page_size]

        # Convert to MediaItemResponse
        items = [
            self._to_media_item(item, 1.0, include_thumbnail)
            for item in paginated_items
        ]

        # Build pagination meta
        pagination = PaginationMeta(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )

        return MultimodalPaginatedListResponse(
            items=items,
            pagination=pagination,
        )

    async def cleanup(self) -> None:
        """Cleanup resources."""
        self._initialized = False
        logger.debug("MultimodalService cleanup completed")


# Singleton instance
_service_instance: Optional[MultimodalService] = None


def get_multimodal_service() -> MultimodalService:
    """
    Get or create MultimodalService singleton.

    Returns:
        MultimodalService instance
    """
    global _service_instance

    if _service_instance is None:
        _service_instance = MultimodalService()

    return _service_instance


def reset_multimodal_service() -> None:
    """Reset singleton instance (for testing)."""
    global _service_instance
    _service_instance = None
