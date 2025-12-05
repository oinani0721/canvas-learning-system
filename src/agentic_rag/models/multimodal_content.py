"""
Multimodal content data models.

This module defines the core data structures for multimodal content storage,
including images, PDFs, audio, and video files associated with Canvas concepts.

Verified from Story 6.3 (AC 6.3.3): Unified MultimodalContent interface
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class MediaType(Enum):
    """
    Supported media types for multimodal content.

    Verified from multimodal-content.schema.json
    """
    IMAGE = "image"
    PDF = "pdf"
    AUDIO = "audio"
    VIDEO = "video"

    @classmethod
    def from_extension(cls, extension: str) -> "MediaType":
        """
        Determine media type from file extension.

        Args:
            extension: File extension (with or without dot)

        Returns:
            MediaType enum value

        Raises:
            ValueError: If extension is not supported
        """
        ext = extension.lower().lstrip(".")

        image_exts = {"jpg", "jpeg", "png", "gif", "webp", "bmp", "svg"}
        pdf_exts = {"pdf"}
        audio_exts = {"mp3", "wav", "ogg", "m4a", "flac", "aac"}
        video_exts = {"mp4", "webm", "mkv", "avi", "mov", "wmv"}

        if ext in image_exts:
            return cls.IMAGE
        elif ext in pdf_exts:
            return cls.PDF
        elif ext in audio_exts:
            return cls.AUDIO
        elif ext in video_exts:
            return cls.VIDEO
        else:
            raise ValueError(f"Unsupported file extension: {extension}")

    @classmethod
    def get_supported_extensions(cls, media_type: "MediaType") -> set[str]:
        """Get supported file extensions for a media type."""
        extensions_map = {
            cls.IMAGE: {"jpg", "jpeg", "png", "gif", "webp", "bmp", "svg"},
            cls.PDF: {"pdf"},
            cls.AUDIO: {"mp3", "wav", "ogg", "m4a", "flac", "aac"},
            cls.VIDEO: {"mp4", "webm", "mkv", "avi", "mov", "wmv"},
        }
        return extensions_map.get(media_type, set())


@dataclass
class MultimodalMetadata:
    """
    Metadata for multimodal content.

    Contains optional fields for dimensions, duration, page count, etc.
    """
    file_size: Optional[int] = None  # bytes
    width: Optional[int] = None  # pixels (image/video)
    height: Optional[int] = None  # pixels (image/video)
    duration: Optional[float] = None  # seconds (audio/video)
    page_count: Optional[int] = None  # PDF
    mime_type: Optional[str] = None

    # Additional metadata
    author: Optional[str] = None
    title: Optional[str] = None
    language: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert metadata to dictionary, excluding None values."""
        return {k: v for k, v in {
            "file_size": self.file_size,
            "width": self.width,
            "height": self.height,
            "duration": self.duration,
            "page_count": self.page_count,
            "mime_type": self.mime_type,
            "author": self.author,
            "title": self.title,
            "language": self.language,
        }.items() if v is not None}

    @classmethod
    def from_dict(cls, data: dict) -> "MultimodalMetadata":
        """Create metadata from dictionary."""
        return cls(
            file_size=data.get("file_size"),
            width=data.get("width"),
            height=data.get("height"),
            duration=data.get("duration"),
            page_count=data.get("page_count"),
            mime_type=data.get("mime_type"),
            author=data.get("author"),
            title=data.get("title"),
            language=data.get("language"),
        )


@dataclass
class MultimodalContent:
    """
    Core data model for multimodal content.

    Represents a piece of multimodal content (image, PDF, audio, video)
    associated with a Canvas concept node.

    Verified from Story 6.3 (AC 6.3.3) and multimodal-content.schema.json

    Attributes:
        id: Unique identifier (UUID)
        media_type: Type of media content
        file_path: Absolute path to the media file
        related_concept_id: ID of the associated Canvas concept node
        created_at: Creation timestamp
        thumbnail_path: Optional path to thumbnail image
        extracted_text: Optional OCR-extracted text (for images/PDFs)
        description: Optional AI-generated description
        vector: Optional 768-dimensional embedding vector
        source_location: Optional page number (PDF) or timestamp (audio/video)
        updated_at: Optional last update timestamp
        metadata: Additional metadata (dimensions, duration, etc.)
    """
    media_type: MediaType
    file_path: str
    related_concept_id: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)

    # Optional fields
    thumbnail_path: Optional[str] = None
    extracted_text: Optional[str] = None
    description: Optional[str] = None
    vector: Optional[list[float]] = None  # 768-dimensional
    source_location: Optional[str] = None
    updated_at: Optional[datetime] = None
    metadata: MultimodalMetadata = field(default_factory=MultimodalMetadata)

    def __post_init__(self):
        """Validate content after initialization."""
        # Ensure media_type is MediaType enum
        if isinstance(self.media_type, str):
            self.media_type = MediaType(self.media_type)

        # Validate vector dimensions if present
        if self.vector is not None and len(self.vector) != 768:
            raise ValueError(
                f"Vector must have 768 dimensions, got {len(self.vector)}"
            )

    def to_dict(self) -> dict:
        """
        Convert content to dictionary for serialization.

        Returns:
            Dictionary representation of the content
        """
        return {
            "id": self.id,
            "media_type": self.media_type.value,
            "file_path": self.file_path,
            "related_concept_id": self.related_concept_id,
            "created_at": self.created_at.isoformat(),
            "thumbnail_path": self.thumbnail_path,
            "extracted_text": self.extracted_text,
            "description": self.description,
            "vector": self.vector,
            "source_location": self.source_location,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "metadata": self.metadata.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MultimodalContent":
        """
        Create content from dictionary.

        Args:
            data: Dictionary containing content data

        Returns:
            MultimodalContent instance
        """
        metadata = data.get("metadata", {})
        if isinstance(metadata, dict):
            metadata = MultimodalMetadata.from_dict(metadata)

        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        updated_at = data.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)

        return cls(
            id=data.get("id", str(uuid.uuid4())),
            media_type=MediaType(data["media_type"]),
            file_path=data["file_path"],
            related_concept_id=data["related_concept_id"],
            created_at=created_at or datetime.now(),
            thumbnail_path=data.get("thumbnail_path"),
            extracted_text=data.get("extracted_text"),
            description=data.get("description"),
            vector=data.get("vector"),
            source_location=data.get("source_location"),
            updated_at=updated_at,
            metadata=metadata,
        )

    def to_lancedb_record(self) -> dict:
        """
        Convert to LanceDB record format.

        Returns:
            Dictionary suitable for LanceDB insertion
        """
        return {
            "id": self.id,
            "media_type": self.media_type.value,
            "file_path": self.file_path,
            "related_concept_id": self.related_concept_id,
            "thumbnail_path": self.thumbnail_path or "",
            "extracted_text": self.extracted_text or "",
            "description": self.description or "",
            "vector": self.vector or [0.0] * 768,
            "source_location": self.source_location or "",
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata.to_dict(),
        }

    def to_neo4j_properties(self) -> dict:
        """
        Convert to Neo4j node properties.

        Returns:
            Dictionary of properties for Neo4j node creation
        """
        return {
            "id": self.id,
            "media_type": self.media_type.value,
            "file_path": self.file_path,
            "thumbnail_path": self.thumbnail_path,
            "description": self.description,
            "source_location": self.source_location,
            "created_at": self.created_at.isoformat(),
            "file_size": self.metadata.file_size,
            "mime_type": self.metadata.mime_type,
        }

    @property
    def has_vector(self) -> bool:
        """Check if content has embedding vector."""
        return self.vector is not None and len(self.vector) == 768

    @property
    def has_extracted_text(self) -> bool:
        """Check if content has extracted text."""
        return bool(self.extracted_text)

    @property
    def has_description(self) -> bool:
        """Check if content has AI-generated description."""
        return bool(self.description)
