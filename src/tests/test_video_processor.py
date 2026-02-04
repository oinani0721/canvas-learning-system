"""
Unit tests for VideoProcessor (Story 35.7).

Verified from Story 35.7:
- AC 35.7.1: Extract duration, resolution, fps
- AC 35.7.2: Support mp4, webm, mkv, avi, mov
- AC 35.7.3: Generate first frame thumbnail
- AC 35.7.5: Return MultimodalContent

Test framework: pytest + pytest-asyncio [Source: ADR-008]
"""

import base64
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from src.agentic_rag.processors.video_processor import (
    VideoCorruptError,
    VideoMetadata,
    VideoProcessor,
    VideoProcessorError,
    VideoSizeError,
    VideoValidationError,
    process_video,
)


class TestVideoMetadata:
    """Tests for VideoMetadata dataclass."""

    def test_create_video_metadata_with_defaults(self):
        """Test VideoMetadata creates with default values."""
        metadata = VideoMetadata()

        assert metadata.id is not None
        assert metadata.file_path == ""
        assert metadata.file_name == ""
        assert metadata.file_size == 0
        assert metadata.format == ""
        assert metadata.duration == 0.0
        assert metadata.width == 0
        assert metadata.height == 0
        assert metadata.fps == 0.0
        assert metadata.codec is None
        assert metadata.mime_type == ""
        assert metadata.thumbnail_base64 is None
        assert isinstance(metadata.created_at, datetime)

    def test_create_video_metadata_with_values(self):
        """Test VideoMetadata creates with provided values."""
        metadata = VideoMetadata(
            id="test-id",
            file_path="/path/to/video.mp4",
            file_name="video.mp4",
            file_size=1000000,
            format="mp4",
            duration=120.5,
            width=1920,
            height=1080,
            fps=30.0,
            codec="h264",
            mime_type="video/mp4",
        )

        assert metadata.id == "test-id"
        assert metadata.file_path == "/path/to/video.mp4"
        assert metadata.file_name == "video.mp4"
        assert metadata.file_size == 1000000
        assert metadata.format == "mp4"
        assert metadata.duration == 120.5
        assert metadata.width == 1920
        assert metadata.height == 1080
        assert metadata.fps == 30.0
        assert metadata.codec == "h264"
        assert metadata.mime_type == "video/mp4"

    def test_to_dict(self):
        """Test VideoMetadata.to_dict() serialization."""
        metadata = VideoMetadata(
            id="test-id",
            file_path="/path/to/video.mp4",
            file_name="video.mp4",
            file_size=1000000,
            format="mp4",
            duration=120.5,
            width=1920,
            height=1080,
            fps=30.0,
        )

        result = metadata.to_dict()

        assert result["id"] == "test-id"
        assert result["file_path"] == "/path/to/video.mp4"
        assert result["file_name"] == "video.mp4"
        assert result["file_size"] == 1000000
        assert result["duration"] == 120.5
        assert result["width"] == 1920
        assert result["height"] == 1080
        assert result["fps"] == 30.0
        assert "created_at" in result

    def test_from_dict(self):
        """Test VideoMetadata.from_dict() deserialization."""
        data = {
            "id": "test-id",
            "file_path": "/path/to/video.mp4",
            "file_name": "video.mp4",
            "file_size": 1000000,
            "format": "mp4",
            "duration": 120.5,
            "width": 1920,
            "height": 1080,
            "fps": 30.0,
            "codec": "h264",
            "mime_type": "video/mp4",
            "created_at": "2026-01-20T10:30:00",
        }

        metadata = VideoMetadata.from_dict(data)

        assert metadata.id == "test-id"
        assert metadata.file_path == "/path/to/video.mp4"
        assert metadata.duration == 120.5
        assert metadata.width == 1920
        assert metadata.height == 1080
        assert metadata.fps == 30.0

    def test_validate_valid_metadata(self):
        """Test validate() returns True for valid metadata."""
        metadata = VideoMetadata(
            file_size=1000,
            duration=120.5,
            width=1920,
            height=1080,
            fps=30.0,
        )

        assert metadata.validate() is True

    def test_validate_invalid_file_size(self):
        """Test validate() returns False for negative file_size."""
        metadata = VideoMetadata(file_size=-1)
        assert metadata.validate() is False

    def test_validate_invalid_duration(self):
        """Test validate() returns False for negative duration."""
        metadata = VideoMetadata(duration=-1.0)
        assert metadata.validate() is False

    def test_validate_invalid_dimensions(self):
        """Test validate() returns False for negative dimensions."""
        metadata = VideoMetadata(width=-1)
        assert metadata.validate() is False

        metadata = VideoMetadata(height=-1)
        assert metadata.validate() is False

    def test_validate_invalid_fps(self):
        """Test validate() returns False for negative fps."""
        metadata = VideoMetadata(fps=-1.0)
        assert metadata.validate() is False


class TestVideoProcessorExceptions:
    """Tests for VideoProcessor exception classes."""

    def test_video_processor_error_is_exception(self):
        """Test VideoProcessorError is an Exception."""
        error = VideoProcessorError("test error")
        assert isinstance(error, Exception)
        assert str(error) == "test error"

    def test_video_validation_error_inherits_from_base(self):
        """Test VideoValidationError inherits from VideoProcessorError."""
        error = VideoValidationError("invalid format")
        assert isinstance(error, VideoProcessorError)
        assert isinstance(error, Exception)

    def test_video_size_error_inherits_from_base(self):
        """Test VideoSizeError inherits from VideoProcessorError."""
        error = VideoSizeError("file too large")
        assert isinstance(error, VideoProcessorError)

    def test_video_corrupt_error_inherits_from_base(self):
        """Test VideoCorruptError inherits from VideoProcessorError."""
        error = VideoCorruptError("file corrupted")
        assert isinstance(error, VideoProcessorError)


class TestVideoProcessorClassConstants:
    """Tests for VideoProcessor class constants."""

    def test_supported_formats(self):
        """Test SUPPORTED_FORMATS contains all expected formats (AC 35.7.2)."""
        expected = {".mp4", ".webm", ".mkv", ".avi", ".mov"}
        assert VideoProcessor.SUPPORTED_FORMATS == expected

    def test_max_size_bytes(self):
        """Test MAX_SIZE_BYTES is 500MB."""
        assert VideoProcessor.MAX_SIZE_BYTES == 500 * 1024 * 1024

    def test_thumbnail_size(self):
        """Test THUMBNAIL_SIZE is (100, 100)."""
        assert VideoProcessor.THUMBNAIL_SIZE == (100, 100)

    def test_mime_types_mapping(self):
        """Test MIME_TYPES contains correct mappings."""
        assert VideoProcessor.MIME_TYPES[".mp4"] == "video/mp4"
        assert VideoProcessor.MIME_TYPES[".webm"] == "video/webm"
        assert VideoProcessor.MIME_TYPES[".mkv"] == "video/x-matroska"
        assert VideoProcessor.MIME_TYPES[".avi"] == "video/x-msvideo"
        assert VideoProcessor.MIME_TYPES[".mov"] == "video/quicktime"


class TestVideoProcessorInit:
    """Tests for VideoProcessor.__init__()."""

    def test_init_with_defaults(self):
        """Test VideoProcessor initializes with default values."""
        processor = VideoProcessor()

        assert processor.thumbnail_size == (100, 100)
        assert processor.max_size_bytes == 500 * 1024 * 1024
        assert processor.enable_video_understanding is False

    def test_init_with_custom_thumbnail_size(self):
        """Test VideoProcessor with custom thumbnail size."""
        processor = VideoProcessor(thumbnail_size=(200, 200))
        assert processor.thumbnail_size == (200, 200)

    def test_init_with_custom_max_size(self):
        """Test VideoProcessor with custom max size."""
        processor = VideoProcessor(max_size_bytes=100 * 1024 * 1024)
        assert processor.max_size_bytes == 100 * 1024 * 1024

    def test_init_with_video_understanding_enabled(self):
        """Test VideoProcessor with video understanding enabled."""
        processor = VideoProcessor(enable_video_understanding=True)
        assert processor.enable_video_understanding is True


class TestVideoProcessorValidateFormat:
    """Tests for VideoProcessor.validate_format() (AC 35.7.2)."""

    @pytest.fixture
    def processor(self):
        return VideoProcessor()

    @pytest.mark.parametrize("extension", [".mp4", ".webm", ".mkv", ".avi", ".mov"])
    def test_validate_format_supported_formats(self, processor, tmp_path, extension):
        """Test validate_format returns True for supported formats."""
        video_file = tmp_path / f"test{extension}"
        video_file.touch()

        assert processor.validate_format(video_file) is True

    @pytest.mark.parametrize("extension", [".txt", ".jpg", ".pdf", ".mp3", ".gif"])
    def test_validate_format_unsupported_formats(self, processor, tmp_path, extension):
        """Test validate_format returns False for unsupported formats."""
        video_file = tmp_path / f"test{extension}"
        video_file.touch()

        assert processor.validate_format(video_file) is False

    def test_validate_format_case_insensitive(self, processor, tmp_path):
        """Test validate_format is case-insensitive."""
        video_file = tmp_path / "test.MP4"
        video_file.touch()

        assert processor.validate_format(video_file) is True


class TestVideoProcessorValidateSize:
    """Tests for VideoProcessor.validate_size()."""

    @pytest.fixture
    def processor(self):
        return VideoProcessor(max_size_bytes=1000)

    def test_validate_size_within_limit(self, processor, tmp_path):
        """Test validate_size returns True for files within limit."""
        video_file = tmp_path / "test.mp4"
        video_file.write_bytes(b'\x00' * 500)

        assert processor.validate_size(video_file) is True

    def test_validate_size_at_limit(self, processor, tmp_path):
        """Test validate_size returns True for files at exact limit."""
        video_file = tmp_path / "test.mp4"
        video_file.write_bytes(b'\x00' * 1000)

        assert processor.validate_size(video_file) is True

    def test_validate_size_exceeds_limit(self, processor, tmp_path):
        """Test validate_size returns False for files exceeding limit."""
        video_file = tmp_path / "test.mp4"
        video_file.write_bytes(b'\x00' * 1500)

        assert processor.validate_size(video_file) is False

    def test_validate_size_file_not_exists(self, processor, tmp_path):
        """Test validate_size returns False for non-existent file."""
        video_file = tmp_path / "nonexistent.mp4"

        assert processor.validate_size(video_file) is False


class TestVideoProcessorGetMimeType:
    """Tests for VideoProcessor.get_mime_type()."""

    @pytest.fixture
    def processor(self):
        return VideoProcessor()

    @pytest.mark.parametrize("extension,expected_mime", [
        (".mp4", "video/mp4"),
        (".webm", "video/webm"),
        (".mkv", "video/x-matroska"),
        (".avi", "video/x-msvideo"),
        (".mov", "video/quicktime"),
    ])
    def test_get_mime_type_known_formats(self, processor, tmp_path, extension, expected_mime):
        """Test get_mime_type returns correct MIME type for known formats."""
        video_file = tmp_path / f"test{extension}"

        assert processor.get_mime_type(video_file) == expected_mime

    def test_get_mime_type_unknown_format(self, processor, tmp_path):
        """Test get_mime_type returns fallback for unknown formats."""
        video_file = tmp_path / "test.unknown"

        assert processor.get_mime_type(video_file) == "application/octet-stream"


@pytest.fixture
def mock_video_clip():
    """Create mock VideoFileClip for testing."""
    mock_clip = MagicMock()
    mock_clip.duration = 10.5
    mock_clip.fps = 30.0
    mock_clip.size = (1920, 1080)
    # Return a valid numpy array for frame
    mock_clip.get_frame.return_value = np.zeros((100, 100, 3), dtype=np.uint8)
    return mock_clip


class TestVideoProcessorProcess:
    """Tests for VideoProcessor.process() (AC 35.7.1, 35.7.5)."""

    @pytest.fixture
    def processor(self):
        return VideoProcessor()

    @pytest.mark.asyncio
    async def test_process_file_not_found(self, processor, tmp_path):
        """Test process raises FileNotFoundError for missing file."""
        video_file = tmp_path / "nonexistent.mp4"

        with pytest.raises(FileNotFoundError, match="Video not found"):
            await processor.process(video_file, "concept-123")

    @pytest.mark.asyncio
    async def test_process_unsupported_format(self, processor, tmp_path):
        """Test process raises VideoValidationError for unsupported format."""
        video_file = tmp_path / "test.txt"
        video_file.write_bytes(b'\x00' * 100)

        with pytest.raises(VideoValidationError, match="Unsupported format"):
            await processor.process(video_file, "concept-123")

    @pytest.mark.asyncio
    async def test_process_file_too_large(self, tmp_path):
        """Test process raises VideoSizeError for oversized file."""
        processor = VideoProcessor(max_size_bytes=100)
        video_file = tmp_path / "test.mp4"
        video_file.write_bytes(b'\x00' * 200)

        with pytest.raises(VideoSizeError, match="exceeds limit"):
            await processor.process(video_file, "concept-123")

    @pytest.mark.asyncio
    async def test_process_returns_multimodal_content(self, processor, tmp_path, mock_video_clip):
        """Test process returns MultimodalContent instance (AC 35.7.5)."""
        video_file = tmp_path / "test.mp4"
        video_file.write_bytes(b'\x00' * 1000)

        with patch('src.agentic_rag.processors.video_processor.MOVIEPY_AVAILABLE', True), \
             patch('src.agentic_rag.processors.video_processor.PILLOW_AVAILABLE', True), \
             patch('src.agentic_rag.processors.video_processor.VideoFileClip', return_value=mock_video_clip):
            from src.agentic_rag.models.multimodal_content import MediaType, MultimodalContent

            result = await processor.process(video_file, "concept-123")

            assert isinstance(result, MultimodalContent)
            assert result.media_type == MediaType.VIDEO
            assert result.related_concept_id == "concept-123"

    @pytest.mark.asyncio
    async def test_process_extracts_metadata(self, processor, tmp_path, mock_video_clip):
        """Test process extracts correct metadata (AC 35.7.1)."""
        video_file = tmp_path / "test.mp4"
        video_file.write_bytes(b'\x00' * 1000)

        with patch('src.agentic_rag.processors.video_processor.MOVIEPY_AVAILABLE', True), \
             patch('src.agentic_rag.processors.video_processor.PILLOW_AVAILABLE', True), \
             patch('src.agentic_rag.processors.video_processor.VideoFileClip', return_value=mock_video_clip):
            result = await processor.process(video_file, "concept-123")

            assert result.metadata.width == 1920
            assert result.metadata.height == 1080
            assert result.metadata.duration == 10.5
            assert result.metadata.mime_type == "video/mp4"


class TestVideoProcessorGenerateThumbnail:
    """Tests for VideoProcessor.generate_thumbnail() (AC 35.7.3)."""

    @pytest.fixture
    def processor(self):
        return VideoProcessor()

    @pytest.mark.asyncio
    async def test_generate_thumbnail_returns_base64(self, processor, tmp_path, mock_video_clip):
        """Test generate_thumbnail returns valid base64 string."""
        video_file = tmp_path / "test.mp4"
        video_file.write_bytes(b'\x00' * 1000)

        with patch('src.agentic_rag.processors.video_processor.MOVIEPY_AVAILABLE', True), \
             patch('src.agentic_rag.processors.video_processor.PILLOW_AVAILABLE', True), \
             patch('src.agentic_rag.processors.video_processor.VideoFileClip', return_value=mock_video_clip):
            thumbnail = await processor.generate_thumbnail(video_file)

            assert isinstance(thumbnail, str)
            # Verify it's valid base64
            decoded = base64.b64decode(thumbnail)
            assert len(decoded) > 0

    @pytest.mark.asyncio
    async def test_generate_thumbnail_custom_size(self, processor, tmp_path, mock_video_clip):
        """Test generate_thumbnail with custom size."""
        video_file = tmp_path / "test.mp4"
        video_file.write_bytes(b'\x00' * 1000)

        with patch('src.agentic_rag.processors.video_processor.MOVIEPY_AVAILABLE', True), \
             patch('src.agentic_rag.processors.video_processor.PILLOW_AVAILABLE', True), \
             patch('src.agentic_rag.processors.video_processor.VideoFileClip', return_value=mock_video_clip):
            thumbnail = await processor.generate_thumbnail(video_file, size=(50, 50))

            assert isinstance(thumbnail, str)
            base64.b64decode(thumbnail)  # Should not raise

    @pytest.mark.asyncio
    async def test_generate_thumbnail_corrupt_video(self, processor, tmp_path):
        """Test generate_thumbnail raises VideoCorruptError for corrupt video."""
        video_file = tmp_path / "test.mp4"
        video_file.write_bytes(b'\x00' * 1000)

        mock_clip = MagicMock()
        mock_clip.get_frame.side_effect = Exception("Cannot read frame")

        with patch('src.agentic_rag.processors.video_processor.MOVIEPY_AVAILABLE', True), \
             patch('src.agentic_rag.processors.video_processor.PILLOW_AVAILABLE', True), \
             patch('src.agentic_rag.processors.video_processor.VideoFileClip', return_value=mock_clip):
            with pytest.raises(VideoCorruptError, match="Cannot generate thumbnail"):
                await processor.generate_thumbnail(video_file)


class TestVideoProcessorExtractMetadata:
    """Tests for VideoProcessor._extract_metadata()."""

    @pytest.fixture
    def processor(self):
        return VideoProcessor()

    @pytest.mark.asyncio
    async def test_extract_metadata_success(self, processor, tmp_path, mock_video_clip):
        """Test _extract_metadata returns VideoMetadata with correct values."""
        video_file = tmp_path / "test.mp4"
        video_file.write_bytes(b'\x00' * 1000)

        with patch('src.agentic_rag.processors.video_processor.MOVIEPY_AVAILABLE', True), \
             patch('src.agentic_rag.processors.video_processor.VideoFileClip', return_value=mock_video_clip):
            metadata = await processor._extract_metadata(video_file)

            assert isinstance(metadata, VideoMetadata)
            assert metadata.duration == 10.5
            assert metadata.fps == 30.0
            assert metadata.width == 1920
            assert metadata.height == 1080
            assert metadata.file_size == 1000

    @pytest.mark.asyncio
    async def test_extract_metadata_corrupt_video(self, processor, tmp_path):
        """Test _extract_metadata raises VideoCorruptError for corrupt video."""
        video_file = tmp_path / "test.mp4"
        video_file.write_bytes(b'\x00' * 1000)

        with patch('src.agentic_rag.processors.video_processor.MOVIEPY_AVAILABLE', True), \
             patch('src.agentic_rag.processors.video_processor.VideoFileClip', side_effect=Exception("Cannot read")):
            with pytest.raises(VideoCorruptError, match="Cannot read video"):
                await processor._extract_metadata(video_file)


class TestVideoProcessorAnalyzeVideo:
    """Tests for VideoProcessor.analyze_video() (AC 35.7.4)."""

    @pytest.fixture
    def processor(self):
        return VideoProcessor(enable_video_understanding=False)

    @pytest.fixture
    def processor_with_understanding(self):
        return VideoProcessor(enable_video_understanding=True)

    @pytest.mark.asyncio
    async def test_analyze_video_disabled_returns_none(self, processor, tmp_path):
        """Test analyze_video returns None when disabled."""
        video_file = tmp_path / "test.mp4"
        video_file.touch()

        result = await processor.analyze_video(video_file)

        assert result is None

    @pytest.mark.asyncio
    async def test_analyze_video_no_feature_flag_returns_none(self, processor_with_understanding, tmp_path):
        """Test analyze_video returns None without feature flag."""
        video_file = tmp_path / "test.mp4"
        video_file.touch()

        with patch.dict('os.environ', {}, clear=True):
            result = await processor_with_understanding.analyze_video(video_file)

        assert result is None

    @pytest.mark.asyncio
    async def test_analyze_video_with_feature_flag(self, processor_with_understanding, tmp_path):
        """Test analyze_video with feature flag enabled (placeholder)."""
        video_file = tmp_path / "test.mp4"
        video_file.touch()

        with patch.dict('os.environ', {'ENABLE_VIDEO_UNDERSTANDING': 'true'}):
            result = await processor_with_understanding.analyze_video(video_file)

        # Currently returns None as placeholder
        assert result is None


class TestProcessVideoConvenienceFunction:
    """Tests for process_video() convenience function."""

    @pytest.mark.asyncio
    async def test_process_video_with_string_path(self, tmp_path, mock_video_clip):
        """Test process_video accepts string path."""
        video_file = tmp_path / "test.mp4"
        video_file.write_bytes(b'\x00' * 1000)

        with patch('src.agentic_rag.processors.video_processor.MOVIEPY_AVAILABLE', True), \
             patch('src.agentic_rag.processors.video_processor.PILLOW_AVAILABLE', True), \
             patch('src.agentic_rag.processors.video_processor.VideoFileClip', return_value=mock_video_clip):
            from src.agentic_rag.models.multimodal_content import MultimodalContent

            result = await process_video(str(video_file), "concept-123")

            assert isinstance(result, MultimodalContent)

    @pytest.mark.asyncio
    async def test_process_video_with_path_object(self, tmp_path, mock_video_clip):
        """Test process_video accepts Path object."""
        video_file = tmp_path / "test.mp4"
        video_file.write_bytes(b'\x00' * 1000)

        with patch('src.agentic_rag.processors.video_processor.MOVIEPY_AVAILABLE', True), \
             patch('src.agentic_rag.processors.video_processor.PILLOW_AVAILABLE', True), \
             patch('src.agentic_rag.processors.video_processor.VideoFileClip', return_value=mock_video_clip):
            from src.agentic_rag.models.multimodal_content import MultimodalContent

            result = await process_video(video_file, "concept-123")

            assert isinstance(result, MultimodalContent)

    @pytest.mark.asyncio
    async def test_process_video_passes_kwargs(self, tmp_path, mock_video_clip):
        """Test process_video passes kwargs to VideoProcessor."""
        video_file = tmp_path / "test.mp4"
        video_file.write_bytes(b'\x00' * 1000)

        with patch('src.agentic_rag.processors.video_processor.MOVIEPY_AVAILABLE', True), \
             patch('src.agentic_rag.processors.video_processor.PILLOW_AVAILABLE', True), \
             patch('src.agentic_rag.processors.video_processor.VideoFileClip', return_value=mock_video_clip):
            result = await process_video(
                video_file,
                "concept-123",
                thumbnail_size=(50, 50),
            )

            assert result is not None


class TestVideoProcessorIntegration:
    """Integration tests for VideoProcessor."""

    @pytest.fixture
    def processor(self):
        return VideoProcessor()

    @pytest.mark.asyncio
    async def test_full_processing_workflow(self, processor, tmp_path, mock_video_clip):
        """Test complete processing workflow end-to-end."""
        video_file = tmp_path / "test.mp4"
        video_file.write_bytes(b'\x00' * 1000)

        with patch('src.agentic_rag.processors.video_processor.MOVIEPY_AVAILABLE', True), \
             patch('src.agentic_rag.processors.video_processor.PILLOW_AVAILABLE', True), \
             patch('src.agentic_rag.processors.video_processor.VideoFileClip', return_value=mock_video_clip):
            from src.agentic_rag.models.multimodal_content import MediaType

            # Process video
            content = await processor.process(video_file, "concept-123")

            # Verify content
            assert content.media_type == MediaType.VIDEO
            assert content.related_concept_id == "concept-123"
            assert content.metadata.width == 1920
            assert content.metadata.height == 1080
            assert content.metadata.duration == 10.5
            assert content.metadata.file_size == 1000
            assert content.metadata.mime_type == "video/mp4"

    def test_processor_exports_from_init(self):
        """Test VideoProcessor is properly exported from __init__.py."""
        from src.agentic_rag.processors import (
            VideoCorruptError,
            VideoMetadata,
            VideoProcessor,
            VideoProcessorError,
            VideoSizeError,
            VideoValidationError,
            process_video,
        )

        assert VideoProcessor is not None
        assert VideoMetadata is not None
        assert VideoProcessorError is not None
        assert VideoValidationError is not None
        assert VideoSizeError is not None
        assert VideoCorruptError is not None
        assert process_video is not None
