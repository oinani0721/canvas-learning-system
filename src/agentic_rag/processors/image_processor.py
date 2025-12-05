"""
Image processor for multimodal content.

This module handles image processing for Canvas concept nodes, including:
- Format validation (PNG, JPG, GIF, SVG)
- Thumbnail generation
- Metadata extraction
- Base64 encoding

Verified from Story 6.1:
- AC 6.1.1: Canvas节点可附加PNG/JPG/GIF/SVG图片
- AC 6.1.2: 图片显示为缩略图
"""

import base64
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Optional, Tuple

# ✅ Verified from Pillow documentation (PIL.Image module)
try:
    from PIL import Image, UnidentifiedImageError
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False
    Image = None
    UnidentifiedImageError = Exception

logger = logging.getLogger(__name__)


@dataclass
class ImageMetadata:
    """
    Metadata extracted from an image file.

    Verified from Story 6.1 (AC 6.1.3): 图片元数据存储到Neo4j
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    file_path: str = ""
    format: str = ""  # png, jpg, gif, svg
    width: int = 0
    height: int = 0
    file_size: int = 0  # bytes
    mime_type: str = ""
    thumbnail_base64: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """Convert metadata to dictionary for storage."""
        return {
            "id": self.id,
            "file_path": self.file_path,
            "format": self.format,
            "width": self.width,
            "height": self.height,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "thumbnail_base64": self.thumbnail_base64,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ImageMetadata":
        """Create metadata from dictionary."""
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        return cls(
            id=data.get("id", str(uuid.uuid4())),
            file_path=data.get("file_path", ""),
            format=data.get("format", ""),
            width=data.get("width", 0),
            height=data.get("height", 0),
            file_size=data.get("file_size", 0),
            mime_type=data.get("mime_type", ""),
            thumbnail_base64=data.get("thumbnail_base64"),
            created_at=created_at or datetime.now(),
        )


class ImageProcessor:
    """
    Image processor for Canvas multimodal content.

    Handles image format validation, thumbnail generation, and metadata extraction.

    Verified from Story 6.1:
    - AC 6.1.1: Support PNG/JPG/GIF/SVG formats
    - AC 6.1.2: Generate 100x100 thumbnails
    - AC 6.1.3: Extract metadata for Neo4j storage

    Usage:
        processor = ImageProcessor()
        metadata = await processor.process(Path("image.png"))
        thumbnail_b64 = await processor.generate_thumbnail(Path("image.png"))
    """

    # ✅ Verified from Story 6.1 (AC 6.1.1): Supported formats
    SUPPORTED_FORMATS: set[str] = {".png", ".jpg", ".jpeg", ".gif", ".svg"}

    # ✅ Verified from Story 6.1 (AC 6.1.1): 10MB limit
    MAX_SIZE_BYTES: int = 10 * 1024 * 1024  # 10MB

    # ✅ Verified from Story 6.1 (AC 6.1.2): Default thumbnail size
    THUMBNAIL_SIZE: Tuple[int, int] = (100, 100)

    # Maximum dimension for processed images (longest edge)
    MAX_DIMENSION: int = 1024

    # MIME type mapping
    MIME_TYPES: dict[str, str] = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".svg": "image/svg+xml",
    }

    def __init__(
        self,
        thumbnail_size: Optional[Tuple[int, int]] = None,
        max_dimension: Optional[int] = None,
        max_size_bytes: Optional[int] = None,
    ):
        """
        Initialize ImageProcessor.

        Args:
            thumbnail_size: Custom thumbnail dimensions (default: 100x100)
            max_dimension: Maximum dimension for processed images (default: 1024)
            max_size_bytes: Maximum file size in bytes (default: 10MB)
        """
        if not PILLOW_AVAILABLE:
            logger.warning("Pillow not available. Install with: pip install Pillow")

        self.thumbnail_size = thumbnail_size or self.THUMBNAIL_SIZE
        self.max_dimension = max_dimension or self.MAX_DIMENSION
        self.max_size_bytes = max_size_bytes or self.MAX_SIZE_BYTES

    def validate_format(self, image_path: Path) -> bool:
        """
        Validate image file format.

        Verified from Story 6.1 (AC 6.1.1): Support PNG/JPG/GIF/SVG

        Args:
            image_path: Path to image file

        Returns:
            True if format is supported, False otherwise
        """
        ext = image_path.suffix.lower()
        return ext in self.SUPPORTED_FORMATS

    def validate_size(self, image_path: Path) -> bool:
        """
        Validate image file size.

        Verified from Story 6.1 (AC 6.1.1): 10MB limit

        Args:
            image_path: Path to image file

        Returns:
            True if size is within limit, False otherwise
        """
        if not image_path.exists():
            return False

        file_size = image_path.stat().st_size
        return file_size <= self.max_size_bytes

    def get_mime_type(self, image_path: Path) -> str:
        """Get MIME type for image file."""
        ext = image_path.suffix.lower()
        return self.MIME_TYPES.get(ext, "application/octet-stream")

    async def process(self, image_path: Path) -> ImageMetadata:
        """
        Process image and extract metadata.

        Verified from Story 6.1:
        - AC 6.1.1: Validate format and size
        - AC 6.1.2: Generate thumbnail
        - AC 6.1.3: Extract metadata

        Args:
            image_path: Path to image file

        Returns:
            ImageMetadata with extracted information

        Raises:
            ValueError: If format is not supported or size exceeds limit
            FileNotFoundError: If image file doesn't exist
        """
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        if not self.validate_format(image_path):
            raise ValueError(
                f"Unsupported format: {image_path.suffix}. "
                f"Supported: {', '.join(self.SUPPORTED_FORMATS)}"
            )

        if not self.validate_size(image_path):
            max_mb = self.max_size_bytes / (1024 * 1024)
            raise ValueError(
                f"File size exceeds limit of {max_mb:.1f}MB"
            )

        # Get file info
        file_size = image_path.stat().st_size
        ext = image_path.suffix.lower()
        mime_type = self.get_mime_type(image_path)

        # Handle SVG separately (can't use Pillow directly)
        if ext == ".svg":
            return await self._process_svg(image_path, file_size, mime_type)

        # Process with Pillow
        return await self._process_raster(image_path, file_size, ext, mime_type)

    async def _process_svg(
        self,
        image_path: Path,
        file_size: int,
        mime_type: str,
    ) -> ImageMetadata:
        """Process SVG file (dimensions not directly available)."""
        # For SVG, we can't easily get dimensions without parsing
        # Return basic metadata
        thumbnail_b64 = None

        # Try to read SVG and encode as base64 for preview
        try:
            svg_content = image_path.read_bytes()
            thumbnail_b64 = base64.b64encode(svg_content).decode("utf-8")
        except Exception as e:
            logger.warning(f"Failed to read SVG: {e}")

        return ImageMetadata(
            file_path=str(image_path.resolve()),
            format="svg",
            width=0,  # Unknown for SVG
            height=0,
            file_size=file_size,
            mime_type=mime_type,
            thumbnail_base64=thumbnail_b64,
        )

    async def _process_raster(
        self,
        image_path: Path,
        file_size: int,
        ext: str,
        mime_type: str,
    ) -> ImageMetadata:
        """Process raster image (PNG, JPG, GIF)."""
        if not PILLOW_AVAILABLE:
            raise RuntimeError("Pillow is required for image processing")

        try:
            # ✅ Verified from Pillow documentation: Image.open()
            with Image.open(image_path) as img:
                width, height = img.size
                format_name = ext.lstrip(".")

                # Generate thumbnail
                thumbnail_b64 = await self._generate_thumbnail_from_image(img)

                return ImageMetadata(
                    file_path=str(image_path.resolve()),
                    format=format_name,
                    width=width,
                    height=height,
                    file_size=file_size,
                    mime_type=mime_type,
                    thumbnail_base64=thumbnail_b64,
                )

        except UnidentifiedImageError:
            raise ValueError(f"Cannot open image: {image_path}")
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            raise

    async def generate_thumbnail(
        self,
        image_path: Path,
        size: Optional[Tuple[int, int]] = None,
    ) -> str:
        """
        Generate thumbnail for image.

        Verified from Story 6.1 (AC 6.1.2): 默认显示100x100px缩略图

        Args:
            image_path: Path to image file
            size: Custom thumbnail size (default: 100x100)

        Returns:
            Base64-encoded thumbnail image

        Raises:
            ValueError: If format is not supported
            FileNotFoundError: If image file doesn't exist
        """
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        ext = image_path.suffix.lower()

        # SVG: return raw content as base64
        if ext == ".svg":
            svg_content = image_path.read_bytes()
            return base64.b64encode(svg_content).decode("utf-8")

        if not PILLOW_AVAILABLE:
            raise RuntimeError("Pillow is required for thumbnail generation")

        # ✅ Verified from Pillow documentation: Image.thumbnail()
        with Image.open(image_path) as img:
            return await self._generate_thumbnail_from_image(img, size)

    async def _generate_thumbnail_from_image(
        self,
        img: "Image.Image",
        size: Optional[Tuple[int, int]] = None,
    ) -> str:
        """
        Generate thumbnail from PIL Image object.

        Args:
            img: PIL Image object
            size: Thumbnail size (default: self.thumbnail_size)

        Returns:
            Base64-encoded thumbnail
        """
        thumb_size = size or self.thumbnail_size

        # Create a copy to avoid modifying original
        thumb = img.copy()

        # Convert RGBA to RGB if needed (for JPEG output)
        if thumb.mode == "RGBA":
            # Create white background
            background = Image.new("RGB", thumb.size, (255, 255, 255))
            background.paste(thumb, mask=thumb.split()[3])
            thumb = background
        elif thumb.mode != "RGB":
            thumb = thumb.convert("RGB")

        # ✅ Verified from Pillow documentation: Image.thumbnail()
        # thumbnail() modifies in-place and maintains aspect ratio
        thumb.thumbnail(thumb_size, Image.Resampling.LANCZOS)

        # Encode to base64
        buffer = BytesIO()
        thumb.save(buffer, format="JPEG", quality=85)
        buffer.seek(0)

        return base64.b64encode(buffer.read()).decode("utf-8")

    async def resize_image(
        self,
        image_path: Path,
        output_path: Optional[Path] = None,
        max_dimension: Optional[int] = None,
    ) -> Path:
        """
        Resize image to maximum dimension while maintaining aspect ratio.

        Args:
            image_path: Path to source image
            output_path: Path for resized image (default: overwrite source)
            max_dimension: Maximum edge length (default: 1024)

        Returns:
            Path to resized image
        """
        if not PILLOW_AVAILABLE:
            raise RuntimeError("Pillow is required for image resizing")

        max_dim = max_dimension or self.max_dimension
        out_path = output_path or image_path

        ext = image_path.suffix.lower()
        if ext == ".svg":
            # SVG is vector, no resizing needed
            return image_path

        with Image.open(image_path) as img:
            width, height = img.size

            # Check if resizing is needed
            if max(width, height) <= max_dim:
                if output_path and output_path != image_path:
                    img.save(output_path)
                    return output_path
                return image_path

            # Calculate new dimensions
            if width > height:
                new_width = max_dim
                new_height = int(height * (max_dim / width))
            else:
                new_height = max_dim
                new_width = int(width * (max_dim / height))

            # ✅ Verified from Pillow documentation: Image.resize()
            resized = img.resize(
                (new_width, new_height),
                Image.Resampling.LANCZOS
            )

            # Save
            resized.save(out_path)
            logger.info(
                f"Resized image from {width}x{height} to {new_width}x{new_height}"
            )

            return out_path

    def get_data_uri(self, image_path: Path) -> str:
        """
        Get data URI for image (for inline HTML embedding).

        Args:
            image_path: Path to image file

        Returns:
            Data URI string (data:mime_type;base64,...)
        """
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        mime_type = self.get_mime_type(image_path)
        content = image_path.read_bytes()
        b64_content = base64.b64encode(content).decode("utf-8")

        return f"data:{mime_type};base64,{b64_content}"
