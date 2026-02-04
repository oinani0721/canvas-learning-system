"""
Video processor for multimodal content.

This module handles video processing for Canvas concept nodes, including:
- Format validation (MP4, WebM, MKV, AVI, MOV)
- Thumbnail generation (first frame)
- Metadata extraction

Verified from Story 35.7:
- AC 35.7.1: Extract duration, resolution, fps
- AC 35.7.2: Support mp4, webm, mkv, avi, mov
- AC 35.7.3: Generate first frame thumbnail
"""

import base64
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Optional, Tuple

# Verified from Context7 MoviePy documentation
try:
    from moviepy import VideoFileClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False
    VideoFileClip = None

# Verified from image_processor.py
try:
    from PIL import Image
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False
    Image = None

from src.agentic_rag.models.multimodal_content import (
    MediaType,
    MultimodalContent,
    MultimodalMetadata,
)

logger = logging.getLogger(__name__)


@dataclass
class VideoMetadata:
    """
    Metadata extracted from a video file.

    Verified from Story 35.7 (AC 35.7.1).

    Attributes:
        id: Unique identifier for this metadata record
        file_path: Absolute path to the video file
        file_name: Name of the video file
        file_size: Size in bytes
        format: Video format (mp4, webm, etc.)
        duration: Duration in seconds
        width: Video width in pixels
        height: Video height in pixels
        fps: Frames per second
        codec: Video codec (optional)
        mime_type: MIME type of the video
        thumbnail_base64: Base64-encoded thumbnail (optional)
        created_at: Timestamp when metadata was created
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    file_path: str = ""
    file_name: str = ""
    file_size: int = 0       # bytes
    format: str = ""         # mp4, webm, mkv, etc.
    duration: float = 0.0    # seconds
    width: int = 0           # pixels
    height: int = 0          # pixels
    fps: float = 0.0         # frames per second
    codec: Optional[str] = None
    mime_type: str = ""
    thumbnail_base64: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """Convert metadata to dictionary for storage."""
        return {
            "id": self.id,
            "file_path": self.file_path,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "format": self.format,
            "duration": self.duration,
            "width": self.width,
            "height": self.height,
            "fps": self.fps,
            "codec": self.codec,
            "mime_type": self.mime_type,
            "thumbnail_base64": self.thumbnail_base64,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "VideoMetadata":
        """Create metadata from dictionary."""
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        return cls(
            id=data.get("id", str(uuid.uuid4())),
            file_path=data.get("file_path", ""),
            file_name=data.get("file_name", ""),
            file_size=data.get("file_size", 0),
            format=data.get("format", ""),
            duration=data.get("duration", 0.0),
            width=data.get("width", 0),
            height=data.get("height", 0),
            fps=data.get("fps", 0.0),
            codec=data.get("codec"),
            mime_type=data.get("mime_type", ""),
            thumbnail_base64=data.get("thumbnail_base64"),
            created_at=created_at or datetime.now(),
        )

    def validate(self) -> bool:
        """
        Validate metadata fields.

        Returns:
            True if all numeric fields are valid, False otherwise
        """
        if self.file_size < 0:
            return False
        if self.duration < 0:
            return False
        if self.width < 0 or self.height < 0:
            return False
        if self.fps < 0:
            return False
        return True


class VideoProcessorError(Exception):
    """
    Base exception for video processing errors.

    [Source: ADR-009]
    """
    pass


class VideoValidationError(VideoProcessorError):
    """Raised when video format validation fails."""
    pass


class VideoSizeError(VideoProcessorError):
    """Raised when video file exceeds size limit."""
    pass


class VideoCorruptError(VideoProcessorError):
    """Raised when video file is corrupted or unreadable."""
    pass


class VideoProcessor:
    """
    Video processor for Canvas multimodal content.

    Handles video format validation, thumbnail generation, and metadata extraction.

    Verified from Story 35.7:
    - AC 35.7.1: Extract duration, resolution, fps
    - AC 35.7.2: Support mp4, webm, mkv, avi, mov
    - AC 35.7.3: Generate first frame thumbnail
    - AC 35.7.5: Return MultimodalContent

    Usage:
        processor = VideoProcessor()
        content = await processor.process(Path("video.mp4"), "concept-123")
        thumbnail = await processor.generate_thumbnail(Path("video.mp4"))

    Attributes:
        SUPPORTED_FORMATS: Set of supported video file extensions
        MAX_SIZE_BYTES: Maximum allowed video file size (500MB default)
        THUMBNAIL_SIZE: Default thumbnail dimensions (100x100)
        MIME_TYPES: Mapping of extensions to MIME types
    """

    # Verified from multimodal_content.py:47
    SUPPORTED_FORMATS: set[str] = {".mp4", ".webm", ".mkv", ".avi", ".mov"}

    # Video files can be larger than images
    MAX_SIZE_BYTES: int = 500 * 1024 * 1024  # 500MB

    # Default thumbnail size (matches ImageProcessor)
    THUMBNAIL_SIZE: Tuple[int, int] = (100, 100)

    MIME_TYPES: dict[str, str] = {
        ".mp4": "video/mp4",
        ".webm": "video/webm",
        ".mkv": "video/x-matroska",
        ".avi": "video/x-msvideo",
        ".mov": "video/quicktime",
    }

    def __init__(
        self,
        thumbnail_size: Optional[Tuple[int, int]] = None,
        max_size_bytes: Optional[int] = None,
        enable_video_understanding: bool = False,
    ):
        """
        Initialize VideoProcessor.

        Args:
            thumbnail_size: Custom thumbnail dimensions (default: 100x100)
            max_size_bytes: Maximum file size in bytes (default: 500MB)
            enable_video_understanding: Enable Gemini video AI (default: False)
        """
        if not MOVIEPY_AVAILABLE:
            logger.warning("moviepy not available. Install with: pip install moviepy")

        if not PILLOW_AVAILABLE:
            logger.warning("Pillow not available. Install with: pip install Pillow")

        self.thumbnail_size = thumbnail_size or self.THUMBNAIL_SIZE
        self.max_size_bytes = max_size_bytes or self.MAX_SIZE_BYTES
        self.enable_video_understanding = enable_video_understanding

    def validate_format(self, video_path: Path) -> bool:
        """
        Validate video file format.

        Verified from Story 35.7 (AC 35.7.2): Support mp4, webm, mkv, avi, mov

        Args:
            video_path: Path to video file

        Returns:
            True if format is supported, False otherwise
        """
        ext = video_path.suffix.lower()
        return ext in self.SUPPORTED_FORMATS

    def validate_size(self, video_path: Path) -> bool:
        """
        Validate video file size.

        Args:
            video_path: Path to video file

        Returns:
            True if size is within limit, False otherwise
        """
        if not video_path.exists():
            return False
        return video_path.stat().st_size <= self.max_size_bytes

    def get_mime_type(self, video_path: Path) -> str:
        """
        Get MIME type for video file.

        Args:
            video_path: Path to video file

        Returns:
            MIME type string (e.g., "video/mp4")
        """
        ext = video_path.suffix.lower()
        return self.MIME_TYPES.get(ext, "application/octet-stream")

    async def process(
        self,
        video_path: Path,
        related_concept_id: str,
    ) -> MultimodalContent:
        """
        Process video and return MultimodalContent.

        Verified from Story 35.7:
        - AC 35.7.1: Extract metadata
        - AC 35.7.3: Generate thumbnail
        - AC 35.7.5: Return MultimodalContent

        Args:
            video_path: Path to video file
            related_concept_id: ID of the related Canvas concept node

        Returns:
            MultimodalContent with extracted information

        Raises:
            VideoValidationError: If format is not supported
            VideoSizeError: If file exceeds size limit
            FileNotFoundError: If video file doesn't exist
        """
        if not video_path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")

        if not self.validate_format(video_path):
            raise VideoValidationError(
                f"Unsupported format: {video_path.suffix}. "
                f"Supported: {', '.join(self.SUPPORTED_FORMATS)}"
            )

        if not self.validate_size(video_path):
            max_mb = self.max_size_bytes / (1024 * 1024)
            raise VideoSizeError(f"File size exceeds limit of {max_mb:.1f}MB")

        if not MOVIEPY_AVAILABLE:
            raise RuntimeError("moviepy is required for video processing")

        # Extract metadata
        metadata = await self._extract_metadata(video_path)

        # Generate thumbnail
        thumbnail_b64 = await self.generate_thumbnail(video_path)

        # Build and return MultimodalContent
        # Note: fps and codec stored in VideoMetadata but not in MultimodalContent
        # per Story 35.7 Dev Notes - these values don't persist to the schema
        return MultimodalContent(
            media_type=MediaType.VIDEO,
            file_path=str(video_path.resolve()),
            related_concept_id=related_concept_id,
            thumbnail_path=None,  # Using base64 instead
            description=None,  # Filled by Gemini if enabled
            metadata=MultimodalMetadata(
                file_size=metadata.file_size,
                width=metadata.width,
                height=metadata.height,
                duration=metadata.duration,
                mime_type=metadata.mime_type,
            ),
        )

    async def _extract_metadata(self, video_path: Path) -> VideoMetadata:
        """
        Extract metadata from video file using moviepy.

        Verified from Context7 MoviePy documentation.

        Args:
            video_path: Path to video file

        Returns:
            VideoMetadata with extracted information

        Raises:
            VideoCorruptError: If video cannot be read
        """
        clip = None
        try:
            # Verified from Context7: VideoFileClip usage
            clip = VideoFileClip(str(video_path))

            width, height = clip.size
            duration = clip.duration
            fps = clip.fps

            return VideoMetadata(
                file_path=str(video_path.resolve()),
                file_name=video_path.name,
                file_size=video_path.stat().st_size,
                format=video_path.suffix.lower().lstrip("."),
                duration=duration,
                width=width,
                height=height,
                fps=fps,
                mime_type=self.get_mime_type(video_path),
            )

        except Exception as e:
            logger.error(f"Error extracting video metadata: {e}")
            raise VideoCorruptError(f"Cannot read video: {video_path}") from e

        finally:
            # Clean up - always close the clip to release resources
            if clip is not None:
                clip.close()

    async def generate_thumbnail(
        self,
        video_path: Path,
        size: Optional[Tuple[int, int]] = None,
        t: float = 0,
    ) -> str:
        """
        Generate thumbnail from video first frame.

        Verified from Story 35.7 (AC 35.7.3): Generate first frame thumbnail

        Args:
            video_path: Path to video file
            size: Custom thumbnail size (default: 100x100)
            t: Time in seconds to capture frame (default: 0 = first frame)

        Returns:
            Base64-encoded JPEG thumbnail

        Raises:
            RuntimeError: If required dependencies are missing
            VideoCorruptError: If thumbnail generation fails
        """
        if not MOVIEPY_AVAILABLE:
            raise RuntimeError("moviepy is required for thumbnail generation")
        if not PILLOW_AVAILABLE:
            raise RuntimeError("Pillow is required for thumbnail generation")

        thumb_size = size or self.thumbnail_size
        clip = None

        try:
            # Verified from Context7: save_frame usage
            clip = VideoFileClip(str(video_path))

            # Get frame as numpy array
            frame = clip.get_frame(t)

            # Convert to PIL Image
            img = Image.fromarray(frame)

            # Resize to thumbnail
            img.thumbnail(thumb_size, Image.Resampling.LANCZOS)

            # Encode to base64
            buffer = BytesIO()
            img.save(buffer, format="JPEG", quality=85)
            buffer.seek(0)

            return base64.b64encode(buffer.read()).decode("utf-8")

        except Exception as e:
            logger.error(f"Error generating thumbnail: {e}")
            raise VideoCorruptError(f"Cannot generate thumbnail: {video_path}") from e

        finally:
            # Clean up - always close the clip to release resources
            if clip is not None:
                clip.close()

    async def analyze_video(self, video_path: Path) -> Optional[str]:
        """
        Analyze video content using Gemini AI (if enabled).

        Verified from Story 35.7 (AC 35.7.4): Gemini video understanding

        Args:
            video_path: Path to video file

        Returns:
            AI-generated description of video content, or None if disabled/unavailable
        """
        if not self.enable_video_understanding:
            logger.debug("Video understanding disabled")
            return None

        # Feature flag check for ENABLE_VIDEO_UNDERSTANDING
        import os
        if not os.getenv("ENABLE_VIDEO_UNDERSTANDING", "").lower() in ("true", "1", "yes"):
            logger.debug("ENABLE_VIDEO_UNDERSTANDING feature flag not set")
            return None

        try:
            # Integration with Gemini Vision follows the pattern from gemini_vision.py
            # This is a placeholder for future Gemini video understanding integration
            logger.info(f"Video understanding requested for: {video_path}")
            return None  # Placeholder - actual implementation pending Gemini video API

        except Exception as e:
            logger.warning(f"Video understanding failed: {e}")
            return None


async def process_video(
    video_path: str | Path,
    related_concept_id: str,
    **kwargs,
) -> MultimodalContent:
    """
    Convenience function to process a video file.

    Args:
        video_path: Path to video file (string or Path)
        related_concept_id: ID of the related Canvas concept node
        **kwargs: Additional arguments passed to VideoProcessor

    Returns:
        MultimodalContent instance
    """
    processor = VideoProcessor(**kwargs)
    path = Path(video_path) if isinstance(video_path, str) else video_path
    return await processor.process(path, related_concept_id)
