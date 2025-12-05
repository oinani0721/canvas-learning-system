"""
Tests for ImageProcessor.

Verified from Story 6.1:
- AC 6.1.1: Canvas节点可附加PNG/JPG/GIF/SVG图片
- AC 6.1.2: 图片显示为缩略图
"""

import base64
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Check if Pillow is available
try:
    from PIL import Image
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

# Import the module under test
from agentic_rag.processors.image_processor import (
    ImageProcessor,
    ImageMetadata,
)


class TestImageMetadata:
    """Tests for ImageMetadata dataclass."""

    def test_metadata_default_values(self):
        """Test default values are set correctly."""
        metadata = ImageMetadata()

        assert metadata.id is not None
        assert metadata.file_path == ""
        assert metadata.format == ""
        assert metadata.width == 0
        assert metadata.height == 0
        assert metadata.file_size == 0
        assert metadata.mime_type == ""
        assert metadata.thumbnail_base64 is None
        assert metadata.created_at is not None

    def test_metadata_to_dict(self):
        """Test conversion to dictionary."""
        metadata = ImageMetadata(
            id="test-id",
            file_path="/path/to/image.png",
            format="png",
            width=100,
            height=100,
            file_size=1024,
            mime_type="image/png",
        )

        result = metadata.to_dict()

        assert result["id"] == "test-id"
        assert result["file_path"] == "/path/to/image.png"
        assert result["format"] == "png"
        assert result["width"] == 100
        assert result["height"] == 100
        assert result["file_size"] == 1024
        assert result["mime_type"] == "image/png"
        assert "created_at" in result

    def test_metadata_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "id": "test-id",
            "file_path": "/path/to/image.png",
            "format": "png",
            "width": 200,
            "height": 150,
            "file_size": 2048,
            "mime_type": "image/png",
            "created_at": "2025-01-01T12:00:00",
        }

        metadata = ImageMetadata.from_dict(data)

        assert metadata.id == "test-id"
        assert metadata.file_path == "/path/to/image.png"
        assert metadata.format == "png"
        assert metadata.width == 200
        assert metadata.height == 150
        assert metadata.file_size == 2048
        assert metadata.mime_type == "image/png"


class TestImageProcessor:
    """Tests for ImageProcessor class."""

    @pytest.fixture
    def processor(self):
        """Create processor instance."""
        return ImageProcessor()

    def test_supported_formats(self, processor):
        """Test supported formats constant (AC 6.1.1)."""
        # ✅ Verified from Story 6.1 (AC 6.1.1)
        assert ".png" in processor.SUPPORTED_FORMATS
        assert ".jpg" in processor.SUPPORTED_FORMATS
        assert ".jpeg" in processor.SUPPORTED_FORMATS
        assert ".gif" in processor.SUPPORTED_FORMATS
        assert ".svg" in processor.SUPPORTED_FORMATS

    def test_max_size_limit(self, processor):
        """Test max size limit is 10MB (AC 6.1.1)."""
        # ✅ Verified from Story 6.1 (AC 6.1.1): 10MB limit
        assert processor.MAX_SIZE_BYTES == 10 * 1024 * 1024

    def test_thumbnail_size(self, processor):
        """Test default thumbnail size is 100x100 (AC 6.1.2)."""
        # ✅ Verified from Story 6.1 (AC 6.1.2)
        assert processor.THUMBNAIL_SIZE == (100, 100)

    def test_validate_format_png(self, processor):
        """Test PNG format validation."""
        assert processor.validate_format(Path("image.png")) is True
        assert processor.validate_format(Path("image.PNG")) is True

    def test_validate_format_jpg(self, processor):
        """Test JPG format validation."""
        assert processor.validate_format(Path("image.jpg")) is True
        assert processor.validate_format(Path("image.jpeg")) is True
        assert processor.validate_format(Path("image.JPEG")) is True

    def test_validate_format_gif(self, processor):
        """Test GIF format validation."""
        assert processor.validate_format(Path("image.gif")) is True

    def test_validate_format_svg(self, processor):
        """Test SVG format validation."""
        assert processor.validate_format(Path("image.svg")) is True

    def test_validate_format_unsupported(self, processor):
        """Test unsupported format rejection."""
        assert processor.validate_format(Path("image.bmp")) is False
        assert processor.validate_format(Path("image.webp")) is False
        assert processor.validate_format(Path("image.tiff")) is False
        assert processor.validate_format(Path("document.pdf")) is False

    def test_get_mime_type(self, processor):
        """Test MIME type lookup."""
        assert processor.get_mime_type(Path("image.png")) == "image/png"
        assert processor.get_mime_type(Path("image.jpg")) == "image/jpeg"
        assert processor.get_mime_type(Path("image.jpeg")) == "image/jpeg"
        assert processor.get_mime_type(Path("image.gif")) == "image/gif"
        assert processor.get_mime_type(Path("image.svg")) == "image/svg+xml"

    def test_get_mime_type_unknown(self, processor):
        """Test MIME type for unknown format."""
        assert processor.get_mime_type(Path("file.xyz")) == "application/octet-stream"

    def test_custom_thumbnail_size(self):
        """Test custom thumbnail size initialization."""
        processor = ImageProcessor(thumbnail_size=(200, 200))
        assert processor.thumbnail_size == (200, 200)

    def test_custom_max_dimension(self):
        """Test custom max dimension initialization."""
        processor = ImageProcessor(max_dimension=2048)
        assert processor.max_dimension == 2048

    def test_custom_max_size(self):
        """Test custom max size initialization."""
        processor = ImageProcessor(max_size_bytes=5 * 1024 * 1024)
        assert processor.max_size_bytes == 5 * 1024 * 1024


@pytest.mark.skipif(not PILLOW_AVAILABLE, reason="Pillow not installed")
class TestImageProcessorWithPillow:
    """Tests requiring Pillow."""

    @pytest.fixture
    def processor(self):
        """Create processor instance."""
        return ImageProcessor()

    @pytest.fixture
    def sample_png(self, tmp_path):
        """Create a sample PNG image."""
        img = Image.new("RGB", (200, 150), color="red")
        path = tmp_path / "sample.png"
        img.save(path)
        return path

    @pytest.fixture
    def sample_jpg(self, tmp_path):
        """Create a sample JPG image."""
        img = Image.new("RGB", (300, 200), color="blue")
        path = tmp_path / "sample.jpg"
        img.save(path, format="JPEG")
        return path

    @pytest.fixture
    def sample_gif(self, tmp_path):
        """Create a sample GIF image."""
        img = Image.new("RGB", (100, 100), color="green")
        path = tmp_path / "sample.gif"
        img.save(path, format="GIF")
        return path

    @pytest.fixture
    def sample_svg(self, tmp_path):
        """Create a sample SVG file."""
        svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
            <circle cx="50" cy="50" r="40" fill="red"/>
        </svg>'''
        path = tmp_path / "sample.svg"
        path.write_text(svg_content)
        return path

    @pytest.fixture
    def large_image(self, tmp_path):
        """Create a large image for testing."""
        img = Image.new("RGB", (2000, 1500), color="purple")
        path = tmp_path / "large.png"
        img.save(path)
        return path

    def test_validate_size_valid(self, processor, sample_png):
        """Test size validation with valid file."""
        assert processor.validate_size(sample_png) is True

    def test_validate_size_nonexistent(self, processor):
        """Test size validation with nonexistent file."""
        assert processor.validate_size(Path("/nonexistent/file.png")) is False

    @pytest.mark.asyncio
    async def test_process_png(self, processor, sample_png):
        """Test processing PNG image (AC 6.1.1)."""
        metadata = await processor.process(sample_png)

        assert metadata.format == "png"
        assert metadata.width == 200
        assert metadata.height == 150
        assert metadata.file_size > 0
        assert metadata.mime_type == "image/png"
        assert metadata.thumbnail_base64 is not None

    @pytest.mark.asyncio
    async def test_process_jpg(self, processor, sample_jpg):
        """Test processing JPG image (AC 6.1.1)."""
        metadata = await processor.process(sample_jpg)

        assert metadata.format == "jpg"
        assert metadata.width == 300
        assert metadata.height == 200
        assert metadata.mime_type == "image/jpeg"
        assert metadata.thumbnail_base64 is not None

    @pytest.mark.asyncio
    async def test_process_gif(self, processor, sample_gif):
        """Test processing GIF image (AC 6.1.1)."""
        metadata = await processor.process(sample_gif)

        assert metadata.format == "gif"
        assert metadata.width == 100
        assert metadata.height == 100
        assert metadata.mime_type == "image/gif"
        assert metadata.thumbnail_base64 is not None

    @pytest.mark.asyncio
    async def test_process_svg(self, processor, sample_svg):
        """Test processing SVG image (AC 6.1.1)."""
        metadata = await processor.process(sample_svg)

        assert metadata.format == "svg"
        assert metadata.mime_type == "image/svg+xml"
        assert metadata.thumbnail_base64 is not None  # SVG content as base64

    @pytest.mark.asyncio
    async def test_process_nonexistent_file(self, processor):
        """Test processing nonexistent file raises error."""
        with pytest.raises(FileNotFoundError):
            await processor.process(Path("/nonexistent/file.png"))

    @pytest.mark.asyncio
    async def test_process_unsupported_format(self, processor, tmp_path):
        """Test processing unsupported format raises error."""
        # Create a file with unsupported extension
        unsupported = tmp_path / "file.bmp"
        unsupported.write_bytes(b"fake image data")

        with pytest.raises(ValueError, match="Unsupported format"):
            await processor.process(unsupported)

    @pytest.mark.asyncio
    async def test_generate_thumbnail_png(self, processor, sample_png):
        """Test thumbnail generation for PNG (AC 6.1.2)."""
        thumbnail_b64 = await processor.generate_thumbnail(sample_png)

        assert thumbnail_b64 is not None
        # Verify it's valid base64
        decoded = base64.b64decode(thumbnail_b64)
        assert len(decoded) > 0

    @pytest.mark.asyncio
    async def test_generate_thumbnail_custom_size(self, processor, sample_png):
        """Test thumbnail with custom size."""
        thumbnail_b64 = await processor.generate_thumbnail(
            sample_png, size=(50, 50)
        )

        assert thumbnail_b64 is not None
        # Decode and verify dimensions
        decoded = base64.b64decode(thumbnail_b64)
        img = Image.open(BytesIO(decoded))
        # Thumbnail maintains aspect ratio, so may not be exactly 50x50
        assert img.width <= 50
        assert img.height <= 50

    @pytest.mark.asyncio
    async def test_generate_thumbnail_svg(self, processor, sample_svg):
        """Test thumbnail generation for SVG."""
        thumbnail_b64 = await processor.generate_thumbnail(sample_svg)

        assert thumbnail_b64 is not None
        # For SVG, raw content is returned
        decoded = base64.b64decode(thumbnail_b64)
        assert b"<svg" in decoded

    @pytest.mark.asyncio
    async def test_resize_image(self, processor, large_image, tmp_path):
        """Test image resizing."""
        output_path = tmp_path / "resized.png"

        result = await processor.resize_image(
            large_image,
            output_path=output_path,
            max_dimension=1024
        )

        assert result == output_path
        assert output_path.exists()

        # Verify dimensions
        with Image.open(output_path) as img:
            assert max(img.size) <= 1024

    @pytest.mark.asyncio
    async def test_resize_image_small_no_resize(self, processor, sample_png, tmp_path):
        """Test that small images aren't resized."""
        output_path = tmp_path / "output.png"

        result = await processor.resize_image(
            sample_png,
            output_path=output_path,
            max_dimension=1024
        )

        # Small image should be copied, not resized
        assert output_path.exists()

    def test_get_data_uri(self, processor, sample_png):
        """Test data URI generation."""
        data_uri = processor.get_data_uri(sample_png)

        assert data_uri.startswith("data:image/png;base64,")
        # Verify base64 portion is valid
        b64_part = data_uri.split(",")[1]
        decoded = base64.b64decode(b64_part)
        assert len(decoded) > 0

    def test_get_data_uri_nonexistent(self, processor):
        """Test data URI for nonexistent file."""
        with pytest.raises(FileNotFoundError):
            processor.get_data_uri(Path("/nonexistent/file.png"))


# Need to import BytesIO for test
from io import BytesIO


class TestImageProcessorEdgeCases:
    """Edge case tests."""

    @pytest.fixture
    def processor(self):
        """Create processor instance."""
        return ImageProcessor()

    def test_validate_format_case_insensitive(self, processor):
        """Test format validation is case insensitive."""
        assert processor.validate_format(Path("IMAGE.PNG")) is True
        assert processor.validate_format(Path("Photo.JPEG")) is True
        assert processor.validate_format(Path("icon.Gif")) is True
        assert processor.validate_format(Path("logo.SVG")) is True

    def test_validate_format_with_multiple_dots(self, processor):
        """Test format validation with multiple dots in filename."""
        assert processor.validate_format(Path("my.photo.png")) is True
        assert processor.validate_format(Path("photo.2024.01.jpg")) is True

    @pytest.mark.skipif(not PILLOW_AVAILABLE, reason="Pillow not installed")
    def test_rgba_to_rgb_conversion(self, processor, tmp_path):
        """Test RGBA images are converted to RGB for thumbnails."""
        # Create RGBA image
        img = Image.new("RGBA", (100, 100), color=(255, 0, 0, 128))
        path = tmp_path / "rgba.png"
        img.save(path)

        # This should not raise an error
        import asyncio
        thumbnail = asyncio.run(processor.generate_thumbnail(path))
        assert thumbnail is not None
