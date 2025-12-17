"""
Unit Tests for Story 12.E.5: Agent Endpoint Multimodal Integration

Story: 12.E.5 - Agent 端点多模态集成
Epic: 12.E - Agent 质量综合修复

Tests:
- _load_images_for_agent() function (AC 5.1)
- Image format support (PNG, JPG, WebP, GIF)
- File size limits (4MB)
- Missing/corrupt file handling (AC 5.4)
- Graceful degradation (AC 5.3)

Author: Dev Agent (James)
Created: 2025-12-16
"""

import base64
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Import the module under test
from app.api.v1.endpoints.agents import (
    IMAGE_MIME_TYPES,
    MAX_IMAGE_SIZE_MB,
    MAX_IMAGES_PER_REQUEST,
    _load_images_for_agent,
)


class TestImageMimeTypes:
    """Test IMAGE_MIME_TYPES constant."""

    def test_png_mime_type(self):
        """AC 5.1: PNG support."""
        assert IMAGE_MIME_TYPES['.png'] == 'image/png'

    def test_jpg_mime_type(self):
        """AC 5.1: JPG support."""
        assert IMAGE_MIME_TYPES['.jpg'] == 'image/jpeg'
        assert IMAGE_MIME_TYPES['.jpeg'] == 'image/jpeg'

    def test_webp_mime_type(self):
        """AC 5.1: WebP support."""
        assert IMAGE_MIME_TYPES['.webp'] == 'image/webp'

    def test_gif_mime_type(self):
        """AC 5.1: GIF support."""
        assert IMAGE_MIME_TYPES['.gif'] == 'image/gif'


class TestConstants:
    """Test module constants."""

    def test_max_images_per_request(self):
        """Story 12.E.5: Max 5 images per request."""
        assert MAX_IMAGES_PER_REQUEST == 5

    def test_max_image_size_mb(self):
        """Story 12.E.5: Max 4MB per image (Gemini API limit)."""
        assert MAX_IMAGE_SIZE_MB == 4.0


class TestLoadImagesForAgent:
    """Tests for _load_images_for_agent() function."""

    @pytest.mark.asyncio
    async def test_load_existing_png_image(self, tmp_path: Path):
        """AC 5.1: Load PNG image successfully."""
        # Create a minimal PNG file (1x1 pixel transparent PNG)
        png_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        )
        test_image = tmp_path / "test.png"
        test_image.write_bytes(png_data)

        resolved_refs = [
            {
                "reference": MagicMock(path="test.png"),
                "absolute_path": str(test_image),
                "exists": True
            }
        ]

        images = await _load_images_for_agent(resolved_refs)

        assert len(images) == 1
        assert images[0]["media_type"] == "image/png"
        assert images[0]["data"] is not None
        assert images[0]["path"] == str(test_image)

    @pytest.mark.asyncio
    async def test_load_existing_jpg_image(self, tmp_path: Path):
        """AC 5.1: Load JPG image successfully."""
        # Create a minimal JPEG file
        # This is a valid 1x1 white JPEG
        jpg_data = bytes([
            0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01,
            0x01, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0xFF, 0xDB, 0x00, 0x43,
            0x00, 0x08, 0x06, 0x06, 0x07, 0x06, 0x05, 0x08, 0x07, 0x07, 0x07, 0x09,
            0x09, 0x08, 0x0A, 0x0C, 0x14, 0x0D, 0x0C, 0x0B, 0x0B, 0x0C, 0x19, 0x12,
            0x13, 0x0F, 0x14, 0x1D, 0x1A, 0x1F, 0x1E, 0x1D, 0x1A, 0x1C, 0x1C, 0x20,
            0x24, 0x2E, 0x27, 0x20, 0x22, 0x2C, 0x23, 0x1C, 0x1C, 0x28, 0x37, 0x29,
            0x2C, 0x30, 0x31, 0x34, 0x34, 0x34, 0x1F, 0x27, 0x39, 0x3D, 0x38, 0x32,
            0x3C, 0x2E, 0x33, 0x34, 0x32, 0xFF, 0xC0, 0x00, 0x0B, 0x08, 0x00, 0x01,
            0x00, 0x01, 0x01, 0x01, 0x11, 0x00, 0xFF, 0xC4, 0x00, 0x1F, 0x00, 0x00,
            0x01, 0x05, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08,
            0x09, 0x0A, 0x0B, 0xFF, 0xC4, 0x00, 0xB5, 0x10, 0x00, 0x02, 0x01, 0x03,
            0x03, 0x02, 0x04, 0x03, 0x05, 0x05, 0x04, 0x04, 0x00, 0x00, 0x01, 0x7D,
            0x01, 0x02, 0x03, 0x00, 0x04, 0x11, 0x05, 0x12, 0x21, 0x31, 0x41, 0x06,
            0x13, 0x51, 0x61, 0x07, 0x22, 0x71, 0x14, 0x32, 0x81, 0x91, 0xA1, 0x08,
            0x23, 0x42, 0xB1, 0xC1, 0x15, 0x52, 0xD1, 0xF0, 0x24, 0x33, 0x62, 0x72,
            0x82, 0x09, 0x0A, 0x16, 0x17, 0x18, 0x19, 0x1A, 0x25, 0x26, 0x27, 0x28,
            0x29, 0x2A, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x3A, 0x43, 0x44, 0x45,
            0x46, 0x47, 0x48, 0x49, 0x4A, 0x53, 0x54, 0x55, 0x56, 0x57, 0x58, 0x59,
            0x5A, 0x63, 0x64, 0x65, 0x66, 0x67, 0x68, 0x69, 0x6A, 0x73, 0x74, 0x75,
            0x76, 0x77, 0x78, 0x79, 0x7A, 0x83, 0x84, 0x85, 0x86, 0x87, 0x88, 0x89,
            0x8A, 0x92, 0x93, 0x94, 0x95, 0x96, 0x97, 0x98, 0x99, 0x9A, 0xA2, 0xA3,
            0xA4, 0xA5, 0xA6, 0xA7, 0xA8, 0xA9, 0xAA, 0xB2, 0xB3, 0xB4, 0xB5, 0xB6,
            0xB7, 0xB8, 0xB9, 0xBA, 0xC2, 0xC3, 0xC4, 0xC5, 0xC6, 0xC7, 0xC8, 0xC9,
            0xCA, 0xD2, 0xD3, 0xD4, 0xD5, 0xD6, 0xD7, 0xD8, 0xD9, 0xDA, 0xE1, 0xE2,
            0xE3, 0xE4, 0xE5, 0xE6, 0xE7, 0xE8, 0xE9, 0xEA, 0xF1, 0xF2, 0xF3, 0xF4,
            0xF5, 0xF6, 0xF7, 0xF8, 0xF9, 0xFA, 0xFF, 0xDA, 0x00, 0x08, 0x01, 0x01,
            0x00, 0x00, 0x3F, 0x00, 0xFB, 0xD5, 0x00, 0x00, 0x00, 0x00, 0xFF, 0xD9
        ])
        test_image = tmp_path / "test.jpg"
        test_image.write_bytes(jpg_data)

        resolved_refs = [
            {
                "reference": MagicMock(path="test.jpg"),
                "absolute_path": str(test_image),
                "exists": True
            }
        ]

        images = await _load_images_for_agent(resolved_refs)

        assert len(images) == 1
        assert images[0]["media_type"] == "image/jpeg"

    @pytest.mark.asyncio
    async def test_skip_non_existing_image(self):
        """AC 5.1: Non-existing images are silently skipped."""
        resolved_refs = [
            {
                "reference": MagicMock(path="missing.png"),
                "absolute_path": "/path/to/missing.png",
                "exists": False
            }
        ]

        images = await _load_images_for_agent(resolved_refs)

        assert len(images) == 0

    @pytest.mark.asyncio
    async def test_skip_none_absolute_path(self):
        """AC 5.1: Refs with None absolute_path are skipped."""
        resolved_refs = [
            {
                "reference": MagicMock(path="missing.png"),
                "absolute_path": None,
                "exists": False
            }
        ]

        images = await _load_images_for_agent(resolved_refs)

        assert len(images) == 0

    @pytest.mark.asyncio
    async def test_skip_unsupported_format(self, tmp_path: Path):
        """AC 5.1: Unsupported formats are skipped."""
        # Create a file with unsupported extension
        test_file = tmp_path / "test.bmp"
        test_file.write_bytes(b"fake bmp data")

        resolved_refs = [
            {
                "reference": MagicMock(path="test.bmp"),
                "absolute_path": str(test_file),
                "exists": True
            }
        ]

        images = await _load_images_for_agent(resolved_refs)

        assert len(images) == 0

    @pytest.mark.asyncio
    async def test_skip_large_image(self, tmp_path: Path):
        """AC 5.4: Images larger than 4MB are skipped."""
        # Create a large file (5MB of zeros)
        large_file = tmp_path / "large.png"
        large_file.write_bytes(b'\x00' * (5 * 1024 * 1024))

        resolved_refs = [
            {
                "reference": MagicMock(path="large.png"),
                "absolute_path": str(large_file),
                "exists": True
            }
        ]

        images = await _load_images_for_agent(resolved_refs, max_size_mb=4.0)

        assert len(images) == 0

    @pytest.mark.asyncio
    async def test_limit_max_images(self, tmp_path: Path):
        """Story 12.E.5: Only first max_images are loaded."""
        # Create 7 small images
        png_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        )

        resolved_refs = []
        for i in range(7):
            test_image = tmp_path / f"test{i}.png"
            test_image.write_bytes(png_data)
            resolved_refs.append({
                "reference": MagicMock(path=f"test{i}.png"),
                "absolute_path": str(test_image),
                "exists": True
            })

        # Load with max_images=5 (default)
        images = await _load_images_for_agent(resolved_refs, max_images=5)

        assert len(images) == 5

    @pytest.mark.asyncio
    async def test_return_base64_data(self, tmp_path: Path):
        """AC 5.1: Returns base64 encoded data."""
        png_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        )
        test_image = tmp_path / "test.png"
        test_image.write_bytes(png_data)

        resolved_refs = [
            {
                "reference": MagicMock(path="test.png"),
                "absolute_path": str(test_image),
                "exists": True
            }
        ]

        images = await _load_images_for_agent(resolved_refs)

        assert len(images) == 1
        # Verify data is valid base64 by decoding it
        decoded = base64.b64decode(images[0]["data"])
        assert decoded == png_data

    @pytest.mark.asyncio
    async def test_mixed_valid_and_invalid_refs(self, tmp_path: Path):
        """AC 5.4: Valid images loaded, invalid ones skipped."""
        png_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        )
        valid_image = tmp_path / "valid.png"
        valid_image.write_bytes(png_data)

        resolved_refs = [
            {
                "reference": MagicMock(path="missing.png"),
                "absolute_path": "/path/to/missing.png",
                "exists": False
            },
            {
                "reference": MagicMock(path="valid.png"),
                "absolute_path": str(valid_image),
                "exists": True
            },
            {
                "reference": MagicMock(path="another_missing.png"),
                "absolute_path": None,
                "exists": False
            },
        ]

        images = await _load_images_for_agent(resolved_refs)

        assert len(images) == 1
        assert "valid.png" in images[0]["path"]

    @pytest.mark.asyncio
    async def test_empty_refs_list(self):
        """AC 5.3: Empty refs list returns empty images list."""
        images = await _load_images_for_agent([])
        assert images == []


class TestLoadImagesErrorHandling:
    """Tests for error handling in _load_images_for_agent()."""

    @pytest.mark.asyncio
    async def test_permission_error_skipped(self, tmp_path: Path):
        """AC 5.4: Permission errors are handled gracefully."""
        # Create a mock that raises PermissionError
        with patch('pathlib.Path.read_bytes') as mock_read:
            mock_read.side_effect = PermissionError("Access denied")

            test_file = tmp_path / "test.png"
            test_file.write_bytes(b"dummy")

            resolved_refs = [
                {
                    "reference": MagicMock(path="test.png"),
                    "absolute_path": str(test_file),
                    "exists": True
                }
            ]

            # Should not raise, should return empty list
            images = await _load_images_for_agent(resolved_refs)
            assert images == []

    @pytest.mark.asyncio
    async def test_os_error_skipped(self, tmp_path: Path):
        """AC 5.4: OS errors are handled gracefully."""
        with patch('pathlib.Path.read_bytes') as mock_read:
            mock_read.side_effect = OSError("Disk error")

            test_file = tmp_path / "test.png"
            test_file.write_bytes(b"dummy")

            resolved_refs = [
                {
                    "reference": MagicMock(path="test.png"),
                    "absolute_path": str(test_file),
                    "exists": True
                }
            ]

            images = await _load_images_for_agent(resolved_refs)
            assert images == []


class TestWebPAndGifSupport:
    """Tests for WebP and GIF format support."""

    @pytest.mark.asyncio
    async def test_webp_mime_type_detection(self, tmp_path: Path):
        """AC 5.1: WebP format support."""
        # Create a minimal WebP file header
        webp_data = b'RIFF\x00\x00\x00\x00WEBPVP8 '
        test_image = tmp_path / "test.webp"
        test_image.write_bytes(webp_data)

        resolved_refs = [
            {
                "reference": MagicMock(path="test.webp"),
                "absolute_path": str(test_image),
                "exists": True
            }
        ]

        images = await _load_images_for_agent(resolved_refs)

        assert len(images) == 1
        assert images[0]["media_type"] == "image/webp"

    @pytest.mark.asyncio
    async def test_gif_mime_type_detection(self, tmp_path: Path):
        """AC 5.1: GIF format support."""
        # Create a minimal GIF file header
        gif_data = b'GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
        test_image = tmp_path / "test.gif"
        test_image.write_bytes(gif_data)

        resolved_refs = [
            {
                "reference": MagicMock(path="test.gif"),
                "absolute_path": str(test_image),
                "exists": True
            }
        ]

        images = await _load_images_for_agent(resolved_refs)

        assert len(images) == 1
        assert images[0]["media_type"] == "image/gif"
