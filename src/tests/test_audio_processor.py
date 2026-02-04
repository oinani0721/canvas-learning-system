"""
Tests for AudioProcessor.

Verified from Story 35.6:
- AC 35.6.1: Extract audio metadata (duration, file_size, mime_type)
- AC 35.6.2: Support mp3, wav, ogg, m4a, flac formats (5 formats per Epic 35)
- AC 35.6.3: Generate waveform thumbnail (optional, feature flag)
- AC 35.6.4: Gemini transcription integration (optional, feature flag)
- AC 35.6.5: Return MultimodalContent instance
"""

import base64
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Check if pydub is available
try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False

# Import the module under test
from agentic_rag.processors.audio_processor import (
    AudioCorruptError,
    AudioProcessor,
    AudioProcessorError,
    AudioSizeError,
    AudioValidationError,
    process_audio,
)
from agentic_rag.models.multimodal_content import (
    MediaType,
    MultimodalContent,
    MultimodalMetadata,
)


class TestAudioProcessorExceptions:
    """Tests for AudioProcessor exception classes (ADR-009 compliance)."""

    def test_base_exception(self):
        """Test AudioProcessorError base exception."""
        error = AudioProcessorError("Test error")
        assert error.message == "Test error"
        assert error.error_code == 5000
        assert error.category == "audio_processing"
        assert str(error) == "Test error"

    def test_base_exception_custom_code(self):
        """Test AudioProcessorError with custom error code."""
        error = AudioProcessorError("Custom error", error_code=5999)
        assert error.error_code == 5999

    def test_validation_error(self):
        """Test AudioValidationError exception."""
        error = AudioValidationError("Invalid format")
        assert error.message == "Invalid format"
        assert error.error_code == 5001
        assert error.category == "audio_processing"

    def test_size_error(self):
        """Test AudioSizeError exception."""
        error = AudioSizeError("File too large")
        assert error.message == "File too large"
        assert error.error_code == 5002

    def test_corrupt_error(self):
        """Test AudioCorruptError exception."""
        error = AudioCorruptError("Cannot read file")
        assert error.message == "Cannot read file"
        assert error.error_code == 5003


class TestAudioProcessor:
    """Tests for AudioProcessor class."""

    @pytest.fixture
    def processor(self):
        """Create processor instance."""
        return AudioProcessor()

    def test_supported_formats(self, processor):
        """Test supported formats constant (AC 35.6.2)."""
        # Verified from Story 35.6 (AC 35.6.2): 5 formats, no aac
        assert ".mp3" in processor.SUPPORTED_FORMATS
        assert ".wav" in processor.SUPPORTED_FORMATS
        assert ".ogg" in processor.SUPPORTED_FORMATS
        assert ".m4a" in processor.SUPPORTED_FORMATS
        assert ".flac" in processor.SUPPORTED_FORMATS
        # Verify aac is NOT included (conflict resolution #1)
        assert ".aac" not in processor.SUPPORTED_FORMATS
        assert len(processor.SUPPORTED_FORMATS) == 5

    def test_max_size_limit(self, processor):
        """Test max size limit is 100MB (Story 35.6)."""
        assert processor.MAX_SIZE_BYTES == 100 * 1024 * 1024

    def test_mime_types(self, processor):
        """Test MIME type mapping (5 formats)."""
        assert processor.MIME_TYPES[".mp3"] == "audio/mpeg"
        assert processor.MIME_TYPES[".wav"] == "audio/wav"
        assert processor.MIME_TYPES[".ogg"] == "audio/ogg"
        assert processor.MIME_TYPES[".m4a"] == "audio/mp4"
        assert processor.MIME_TYPES[".flac"] == "audio/flac"
        assert len(processor.MIME_TYPES) == 5

    def test_validate_format_mp3(self, processor):
        """Test MP3 format validation."""
        assert processor.validate_format(Path("audio.mp3")) is True
        assert processor.validate_format(Path("audio.MP3")) is True

    def test_validate_format_wav(self, processor):
        """Test WAV format validation."""
        assert processor.validate_format(Path("audio.wav")) is True
        assert processor.validate_format(Path("audio.WAV")) is True

    def test_validate_format_ogg(self, processor):
        """Test OGG format validation."""
        assert processor.validate_format(Path("audio.ogg")) is True

    def test_validate_format_m4a(self, processor):
        """Test M4A format validation."""
        assert processor.validate_format(Path("audio.m4a")) is True

    def test_validate_format_flac(self, processor):
        """Test FLAC format validation."""
        assert processor.validate_format(Path("audio.flac")) is True

    def test_validate_format_unsupported(self, processor):
        """Test unsupported format rejection."""
        assert processor.validate_format(Path("audio.aac")) is False
        assert processor.validate_format(Path("audio.wma")) is False
        assert processor.validate_format(Path("audio.aiff")) is False
        assert processor.validate_format(Path("document.pdf")) is False

    def test_get_mime_type(self, processor):
        """Test MIME type lookup."""
        assert processor.get_mime_type(Path("audio.mp3")) == "audio/mpeg"
        assert processor.get_mime_type(Path("audio.wav")) == "audio/wav"
        assert processor.get_mime_type(Path("audio.ogg")) == "audio/ogg"
        assert processor.get_mime_type(Path("audio.m4a")) == "audio/mp4"
        assert processor.get_mime_type(Path("audio.flac")) == "audio/flac"

    def test_get_mime_type_unknown(self, processor):
        """Test MIME type for unknown format."""
        assert processor.get_mime_type(Path("file.xyz")) == "audio/unknown"

    def test_custom_max_size(self):
        """Test custom max size initialization."""
        processor = AudioProcessor(max_size_bytes=50 * 1024 * 1024)
        assert processor.max_size_bytes == 50 * 1024 * 1024

    def test_enable_waveform_flag(self):
        """Test waveform feature flag (AC 35.6.3)."""
        processor = AudioProcessor(enable_waveform=True)
        assert processor.enable_waveform is True

        processor_disabled = AudioProcessor(enable_waveform=False)
        assert processor_disabled.enable_waveform is False

    def test_enable_transcription_flag(self):
        """Test transcription feature flag (AC 35.6.4)."""
        processor = AudioProcessor(enable_transcription=True)
        assert processor.enable_transcription is True

        processor_disabled = AudioProcessor(enable_transcription=False)
        assert processor_disabled.enable_transcription is False


class TestAudioProcessorValidation:
    """Tests for AudioProcessor validation methods."""

    @pytest.fixture
    def processor(self):
        """Create processor instance."""
        return AudioProcessor()

    @pytest.fixture
    def sample_audio(self, tmp_path):
        """Create a sample audio file (fake content for testing)."""
        path = tmp_path / "sample.mp3"
        # Create a small fake file
        path.write_bytes(b"fake mp3 data" * 100)
        return path

    @pytest.fixture
    def large_audio(self, tmp_path):
        """Create a large audio file exceeding limit."""
        path = tmp_path / "large.mp3"
        # Create file larger than 100MB (use smaller for test speed)
        processor = AudioProcessor(max_size_bytes=1000)  # 1KB limit for test
        path.write_bytes(b"x" * 2000)  # 2KB file
        return path

    def test_validate_size_valid(self, processor, sample_audio):
        """Test size validation with valid file."""
        assert processor.validate_size(sample_audio) is True

    def test_validate_size_nonexistent(self, processor):
        """Test size validation with nonexistent file."""
        assert processor.validate_size(Path("/nonexistent/file.mp3")) is False

    def test_validate_size_exceeds_limit(self, tmp_path):
        """Test size validation with file exceeding limit."""
        processor = AudioProcessor(max_size_bytes=100)  # 100 bytes limit
        path = tmp_path / "large.mp3"
        path.write_bytes(b"x" * 200)  # 200 bytes file
        assert processor.validate_size(path) is False


class TestAudioProcessorProcess:
    """Tests for AudioProcessor process() method."""

    @pytest.fixture
    def processor(self):
        """Create processor instance."""
        return AudioProcessor()

    @pytest.fixture
    def sample_audio(self, tmp_path):
        """Create a sample audio file."""
        path = tmp_path / "sample.mp3"
        path.write_bytes(b"fake mp3 data" * 100)
        return path

    @pytest.mark.asyncio
    async def test_process_nonexistent_file(self, processor):
        """Test processing nonexistent file raises error."""
        with pytest.raises(FileNotFoundError):
            await processor.process(Path("/nonexistent/file.mp3"), "concept-123")

    @pytest.mark.asyncio
    async def test_process_unsupported_format(self, processor, tmp_path):
        """Test processing unsupported format raises error."""
        unsupported = tmp_path / "file.aac"
        unsupported.write_bytes(b"fake data")

        with pytest.raises(AudioValidationError, match="Unsupported audio format"):
            await processor.process(unsupported, "concept-123")

    @pytest.mark.asyncio
    async def test_process_file_too_large(self, tmp_path):
        """Test processing file exceeding size limit raises error."""
        processor = AudioProcessor(max_size_bytes=100)  # 100 bytes limit
        large_file = tmp_path / "large.mp3"
        large_file.write_bytes(b"x" * 200)  # 200 bytes

        with pytest.raises(AudioSizeError, match="exceeds limit"):
            await processor.process(large_file, "concept-123")

    @pytest.mark.asyncio
    @pytest.mark.skipif(not PYDUB_AVAILABLE, reason="pydub not installed")
    async def test_process_returns_multimodal_content(self, tmp_path):
        """Test process returns MultimodalContent (AC 35.6.5)."""
        # Create actual audio file using pydub
        from pydub.generators import Sine

        # Generate 1 second of sine wave
        audio = Sine(440).to_audio_segment(duration=1000)
        path = tmp_path / "test.mp3"
        audio.export(str(path), format="mp3")

        processor = AudioProcessor()
        result = await processor.process(path, "concept-123")

        assert isinstance(result, MultimodalContent)
        assert result.media_type == MediaType.AUDIO
        assert result.related_concept_id == "concept-123"
        assert result.file_path == str(path.resolve())
        assert result.id is not None
        assert result.created_at is not None

    @pytest.mark.asyncio
    @pytest.mark.skipif(not PYDUB_AVAILABLE, reason="pydub not installed")
    async def test_process_extracts_metadata(self, tmp_path):
        """Test process extracts metadata correctly (AC 35.6.1)."""
        from pydub.generators import Sine

        # Generate 2 seconds of sine wave
        audio = Sine(440).to_audio_segment(duration=2000)
        path = tmp_path / "test.wav"
        audio.export(str(path), format="wav")

        processor = AudioProcessor()
        result = await processor.process(path, "concept-123")

        # Verify metadata extraction (AC 35.6.1)
        assert result.metadata is not None
        assert result.metadata.duration is not None
        assert result.metadata.duration >= 1.9  # ~2 seconds
        assert result.metadata.file_size > 0
        assert result.metadata.mime_type == "audio/wav"


class TestAudioProcessorWithMocks:
    """Tests using mocks for pydub dependency."""

    @pytest.fixture
    def processor(self):
        """Create processor instance."""
        return AudioProcessor()

    @pytest.fixture
    def sample_audio(self, tmp_path):
        """Create a sample audio file."""
        path = tmp_path / "sample.mp3"
        path.write_bytes(b"fake mp3 data" * 100)
        return path

    @pytest.mark.asyncio
    async def test_process_with_mocked_pydub(self, processor, sample_audio):
        """Test process with mocked pydub."""
        mock_audio = MagicMock()
        mock_audio.__len__ = MagicMock(return_value=5000)  # 5 seconds in ms

        with patch('agentic_rag.processors.audio_processor.PYDUB_AVAILABLE', True):
            with patch('agentic_rag.processors.audio_processor.AudioSegment') as mock_segment:
                mock_segment.from_file.return_value = mock_audio

                result = await processor.process(sample_audio, "concept-123")

                assert result.media_type == MediaType.AUDIO
                assert result.metadata.duration == 5.0  # 5000ms / 1000
                assert result.metadata.mime_type == "audio/mpeg"

    @pytest.mark.asyncio
    async def test_process_pydub_not_available(self, tmp_path):
        """Test process raises error when pydub not available."""
        path = tmp_path / "sample.mp3"
        path.write_bytes(b"fake data")

        with patch('agentic_rag.processors.audio_processor.PYDUB_AVAILABLE', False):
            processor = AudioProcessor()

            with pytest.raises(AudioCorruptError, match="pydub is required"):
                await processor.process(path, "concept-123")


class TestAudioProcessorWaveform:
    """Tests for waveform thumbnail generation (AC 35.6.3)."""

    @pytest.fixture
    def processor(self):
        """Create processor with waveform enabled."""
        return AudioProcessor(enable_waveform=True)

    @pytest.mark.asyncio
    async def test_generate_waveform_pydub_not_available(self, processor, tmp_path):
        """Test waveform generation when pydub not available."""
        path = tmp_path / "sample.mp3"
        path.write_bytes(b"fake data")

        with patch('agentic_rag.processors.audio_processor.PYDUB_AVAILABLE', False):
            result = await processor.generate_waveform_thumbnail(path)
            assert result is None

    @pytest.mark.asyncio
    @pytest.mark.skipif(not PYDUB_AVAILABLE, reason="pydub not installed")
    async def test_generate_waveform_no_matplotlib(self, tmp_path):
        """Test waveform generation when matplotlib not available."""
        from pydub.generators import Sine

        audio = Sine(440).to_audio_segment(duration=1000)
        path = tmp_path / "test.mp3"
        audio.export(str(path), format="mp3")

        processor = AudioProcessor(enable_waveform=True)

        with patch.dict('sys.modules', {'matplotlib': None}):
            result = await processor.generate_waveform_thumbnail(path)
            # Should return None when matplotlib not available
            # (import error caught)


class TestAudioProcessorTranscription:
    """Tests for Gemini transcription (AC 35.6.4)."""

    @pytest.fixture
    def processor(self):
        """Create processor with transcription enabled."""
        return AudioProcessor(enable_transcription=True)

    @pytest.fixture
    def sample_audio(self, tmp_path):
        """Create a sample audio file."""
        path = tmp_path / "sample.mp3"
        path.write_bytes(b"fake mp3 data" * 100)
        return path

    @pytest.mark.asyncio
    async def test_transcribe_no_api_key(self, processor, sample_audio):
        """Test transcription returns None when API key not set."""
        with patch.dict('os.environ', {}, clear=True):
            result = await processor.transcribe(sample_audio)
            # Should return None when GOOGLE_API_KEY not set
            assert result is None

    @pytest.mark.asyncio
    async def test_transcribe_no_genai_module(self, processor, sample_audio):
        """Test transcription returns None when google.generativeai not available."""
        with patch.dict('sys.modules', {'google.generativeai': None}):
            result = await processor.transcribe(sample_audio)
            assert result is None


class TestProcessAudioConvenienceFunction:
    """Tests for process_audio convenience function."""

    @pytest.fixture
    def sample_audio(self, tmp_path):
        """Create a sample audio file."""
        path = tmp_path / "sample.mp3"
        path.write_bytes(b"fake mp3 data" * 100)
        return path

    @pytest.mark.asyncio
    async def test_process_audio_function(self, sample_audio):
        """Test convenience function creates processor and processes."""
        mock_audio = MagicMock()
        mock_audio.__len__ = MagicMock(return_value=3000)

        with patch('agentic_rag.processors.audio_processor.PYDUB_AVAILABLE', True):
            with patch('agentic_rag.processors.audio_processor.AudioSegment') as mock_segment:
                mock_segment.from_file.return_value = mock_audio

                result = await process_audio(
                    sample_audio,
                    "concept-456",
                    enable_waveform=False,
                    enable_transcription=False,
                )

                assert isinstance(result, MultimodalContent)
                assert result.related_concept_id == "concept-456"

    @pytest.mark.asyncio
    async def test_process_audio_with_string_path(self, sample_audio):
        """Test convenience function accepts string path."""
        mock_audio = MagicMock()
        mock_audio.__len__ = MagicMock(return_value=2000)

        with patch('agentic_rag.processors.audio_processor.PYDUB_AVAILABLE', True):
            with patch('agentic_rag.processors.audio_processor.AudioSegment') as mock_segment:
                mock_segment.from_file.return_value = mock_audio

                # Pass string instead of Path
                result = await process_audio(
                    str(sample_audio),
                    "concept-789",
                )

                assert isinstance(result, MultimodalContent)


class TestAudioProcessorEdgeCases:
    """Edge case tests."""

    @pytest.fixture
    def processor(self):
        """Create processor instance."""
        return AudioProcessor()

    def test_validate_format_case_insensitive(self, processor):
        """Test format validation is case insensitive."""
        assert processor.validate_format(Path("AUDIO.MP3")) is True
        assert processor.validate_format(Path("audio.WAV")) is True
        assert processor.validate_format(Path("Audio.Ogg")) is True
        assert processor.validate_format(Path("track.M4A")) is True
        assert processor.validate_format(Path("song.FLAC")) is True

    def test_validate_format_with_multiple_dots(self, processor):
        """Test format validation with multiple dots in filename."""
        assert processor.validate_format(Path("my.song.mp3")) is True
        assert processor.validate_format(Path("podcast.2024.01.wav")) is True

    def test_validate_format_path_with_spaces(self, processor):
        """Test format validation with spaces in path."""
        assert processor.validate_format(Path("my music/song name.mp3")) is True
        assert processor.validate_format(Path("audio files/podcast episode.wav")) is True

    @pytest.mark.asyncio
    async def test_process_path_resolved(self, tmp_path):
        """Test that process resolves the path to absolute."""
        path = tmp_path / "sample.mp3"
        path.write_bytes(b"fake data" * 100)

        mock_audio = MagicMock()
        mock_audio.__len__ = MagicMock(return_value=1000)

        with patch('agentic_rag.processors.audio_processor.PYDUB_AVAILABLE', True):
            with patch('agentic_rag.processors.audio_processor.AudioSegment') as mock_segment:
                mock_segment.from_file.return_value = mock_audio

                processor = AudioProcessor()
                result = await processor.process(path, "concept-123")

                # Verify path is resolved to absolute
                assert Path(result.file_path).is_absolute()
