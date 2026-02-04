"""
Audio processor for multimodal content.

This module handles audio processing for Canvas concept nodes, including:
- Format validation (mp3, wav, ogg, m4a, flac)
- Metadata extraction (duration, file_size, mime_type)
- Optional waveform thumbnail generation
- Optional Gemini transcription integration

Verified from Story 35.6:
- AC 35.6.1: Extract audio metadata (duration, file_size, mime_type - schema-compliant)
- AC 35.6.2: Support mp3, wav, ogg, m4a, flac formats (5 formats per Epic 35)
- AC 35.6.3: Generate waveform thumbnail (optional, feature flag)
- AC 35.6.4: Gemini transcription integration (optional, feature flag)
- AC 35.6.5: Return MultimodalContent instance
"""

import base64
import logging
import os
import uuid
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Optional, Tuple

# ✅ Verified from pydub documentation (https://github.com/jiaaro/pydub)
try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    AudioSegment = None

# ✅ Verified from ADR-011: pathlib standardization
from agentic_rag.models.multimodal_content import (
    MediaType,
    MultimodalContent,
    MultimodalMetadata,
)

logger = logging.getLogger(__name__)


# ===== Exception Classes (符合 ADR-009 错误处理策略) =====

class AudioProcessorError(Exception):
    """
    Base exception for audio processing errors.

    Verified from ADR-009: Error handling and retry strategy.

    Attributes:
        message: Error description
        error_code: Numeric error code for categorization
        category: Error category for logging/monitoring
    """

    def __init__(self, message: str, error_code: int = 5000):
        self.message = message
        self.error_code = error_code
        self.category = "audio_processing"
        super().__init__(message)


class AudioValidationError(AudioProcessorError):
    """Raised when audio format validation fails (unsupported format)."""

    def __init__(self, message: str):
        super().__init__(message, error_code=5001)


class AudioSizeError(AudioProcessorError):
    """Raised when audio file exceeds size limit."""

    def __init__(self, message: str):
        super().__init__(message, error_code=5002)


class AudioCorruptError(AudioProcessorError):
    """Raised when audio file is corrupted or unreadable."""

    def __init__(self, message: str):
        super().__init__(message, error_code=5003)


# ===== Main Processor Class =====

class AudioProcessor:
    """
    Audio processor for Canvas multimodal content.

    Handles audio format validation, metadata extraction, and optional features
    like waveform thumbnail generation and transcription.

    Verified from Story 35.6:
    - AC 35.6.1: Extract duration, file_size, mime_type (schema-compliant)
    - AC 35.6.2: Support mp3, wav, ogg, m4a, flac (5 formats per Epic 35)
    - AC 35.6.5: Return MultimodalContent

    Usage:
        processor = AudioProcessor()
        content = await processor.process(Path("audio.mp3"), "concept-123")
    """

    # ✅ Verified from Story 35.6 (Step 8d Conflict Resolution #1):
    # 5 formats per Epic 35 (removed aac)
    SUPPORTED_FORMATS: set[str] = {".mp3", ".wav", ".ogg", ".m4a", ".flac"}

    # ✅ Verified from Story 35.6: 100MB limit
    MAX_SIZE_BYTES: int = 100 * 1024 * 1024  # 100MB

    # ✅ Verified from Story 35.6: MIME type mapping (5 formats, no aac)
    MIME_TYPES: dict[str, str] = {
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
        ".ogg": "audio/ogg",
        ".m4a": "audio/mp4",
        ".flac": "audio/flac",
    }

    def __init__(
        self,
        max_size_bytes: Optional[int] = None,
        enable_waveform: bool = False,
        enable_transcription: bool = False,
    ):
        """
        Initialize AudioProcessor.

        Args:
            max_size_bytes: Maximum file size in bytes (default: 100MB)
            enable_waveform: Enable waveform thumbnail generation (AC 35.6.3)
            enable_transcription: Enable Gemini transcription (AC 35.6.4)
        """
        if not PYDUB_AVAILABLE:
            logger.warning(
                "pydub not available. Install with: pip install pydub. "
                "Note: ffmpeg may be required for some audio formats."
            )

        self.max_size_bytes = max_size_bytes or self.MAX_SIZE_BYTES
        self.enable_waveform = enable_waveform
        self.enable_transcription = enable_transcription

    def validate_format(self, audio_path: Path) -> bool:
        """
        Validate audio file format.

        Verified from Story 35.6 (AC 35.6.2): Support mp3, wav, ogg, m4a, flac

        Args:
            audio_path: Path to audio file (uses pathlib per ADR-011)

        Returns:
            True if format is supported, False otherwise
        """
        # ✅ Verified from ADR-011: Use .suffix.lower() for extension
        ext = audio_path.suffix.lower()
        return ext in self.SUPPORTED_FORMATS

    def validate_size(self, audio_path: Path) -> bool:
        """
        Validate audio file size.

        Args:
            audio_path: Path to audio file

        Returns:
            True if size is within limit, False otherwise
        """
        if not audio_path.exists():
            return False
        return audio_path.stat().st_size <= self.max_size_bytes

    def get_mime_type(self, audio_path: Path) -> str:
        """
        Get MIME type for audio file.

        Args:
            audio_path: Path to audio file

        Returns:
            MIME type string
        """
        ext = audio_path.suffix.lower()
        return self.MIME_TYPES.get(ext, "audio/unknown")

    def _extract_metadata(self, audio_path: Path) -> MultimodalMetadata:
        """
        Extract metadata using pydub and return MultimodalMetadata.

        Only stores schema-defined fields (duration, file_size, mime_type).

        Verified from Story 35.6 (Step 8d Conflict Resolution #2):
        Use schema-only fields, not sample_rate/channels/bitrate.

        Args:
            audio_path: Path to audio file

        Returns:
            MultimodalMetadata with audio-specific fields

        Raises:
            AudioCorruptError: If audio file cannot be read
        """
        if not PYDUB_AVAILABLE:
            raise AudioCorruptError(
                "pydub is required for metadata extraction. "
                "Install with: pip install pydub"
            )

        try:
            # ✅ Verified from pydub documentation: AudioSegment.from_file()
            audio = AudioSegment.from_file(str(audio_path))

            # Extract schema-compliant metadata only
            # Note: sample_rate, channels not stored (not in schema)
            # Can log for debugging: logger.debug(f"sample_rate={audio.frame_rate}")

            return MultimodalMetadata(
                file_size=audio_path.stat().st_size,
                duration=len(audio) / 1000.0,  # ms -> seconds
                mime_type=self.get_mime_type(audio_path),
            )

        except Exception as e:
            raise AudioCorruptError(
                f"Failed to read audio file: {audio_path}. Error: {e}"
            )

    async def process(
        self,
        audio_path: Path,
        related_concept_id: str,
    ) -> MultimodalContent:
        """
        Process audio and return MultimodalContent.

        Verified from Story 35.6 (AC 35.6.1, AC 35.6.5):
        - Extract duration, file_size, mime_type
        - Return MultimodalContent instance

        Args:
            audio_path: Path to audio file
            related_concept_id: ID of the related Canvas concept node

        Returns:
            MultimodalContent instance with media_type=MediaType.AUDIO

        Raises:
            FileNotFoundError: If audio file doesn't exist
            AudioValidationError: If format is not supported
            AudioSizeError: If file size exceeds limit
            AudioCorruptError: If file is corrupted or unreadable
        """
        # ✅ Verified from ADR-011: Use .resolve() for absolute path
        audio_path = Path(audio_path).resolve()

        # Validate file exists
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        # Validate format (AC 35.6.2)
        if not self.validate_format(audio_path):
            raise AudioValidationError(
                f"Unsupported audio format: {audio_path.suffix}. "
                f"Supported formats: {', '.join(sorted(self.SUPPORTED_FORMATS))}"
            )

        # Validate size
        if not self.validate_size(audio_path):
            max_mb = self.max_size_bytes / (1024 * 1024)
            actual_mb = audio_path.stat().st_size / (1024 * 1024)
            raise AudioSizeError(
                f"Audio file size ({actual_mb:.1f}MB) exceeds limit of {max_mb:.1f}MB"
            )

        # Extract metadata (AC 35.6.1)
        metadata = self._extract_metadata(audio_path)

        # Optional: Generate waveform thumbnail (AC 35.6.3)
        thumbnail_path: Optional[str] = None
        if self.enable_waveform:
            try:
                waveform_b64 = await self.generate_waveform_thumbnail(audio_path)
                if waveform_b64:
                    # Store as data URI for inline display
                    thumbnail_path = f"data:image/png;base64,{waveform_b64}"
            except Exception as e:
                logger.warning(f"Failed to generate waveform thumbnail: {e}")

        # Optional: Transcription (AC 35.6.4)
        extracted_text: Optional[str] = None
        if self.enable_transcription:
            try:
                extracted_text = await self.transcribe(audio_path)
            except Exception as e:
                logger.warning(f"Failed to transcribe audio: {e}")

        # Build MultimodalContent (AC 35.6.5)
        # ✅ Verified from multimodal-content.schema.json
        content = MultimodalContent(
            id=str(uuid.uuid4()),
            media_type=MediaType.AUDIO,
            file_path=str(audio_path),
            related_concept_id=related_concept_id,
            created_at=datetime.now(),
            thumbnail_path=thumbnail_path,
            extracted_text=extracted_text,
            metadata=metadata,
        )

        logger.info(
            f"Processed audio: {audio_path.name}, "
            f"duration={metadata.duration:.2f}s, "
            f"size={metadata.file_size} bytes"
        )

        return content

    async def generate_waveform_thumbnail(
        self,
        audio_path: Path,
        size: Tuple[int, int] = (200, 50),
    ) -> Optional[str]:
        """
        Generate waveform thumbnail as base64 PNG.

        Verified from Story 35.6 (AC 35.6.3): Optional feature flag.

        Args:
            audio_path: Path to audio file
            size: Thumbnail dimensions (width, height)

        Returns:
            Base64-encoded PNG image, or None if generation fails
        """
        if not PYDUB_AVAILABLE:
            logger.warning("pydub required for waveform generation")
            return None

        try:
            # Try to import matplotlib for visualization
            import matplotlib
            matplotlib.use('Agg')  # Non-interactive backend
            import matplotlib.pyplot as plt
            import numpy as np

            # Load audio
            audio = AudioSegment.from_file(str(audio_path))

            # Get samples as numpy array
            samples = np.array(audio.get_array_of_samples())

            # If stereo, convert to mono
            if audio.channels == 2:
                samples = samples.reshape((-1, 2)).mean(axis=1)

            # Downsample for visualization
            target_points = size[0]
            if len(samples) > target_points:
                # Take max absolute value in each chunk for waveform envelope
                chunk_size = len(samples) // target_points
                samples = np.array([
                    np.max(np.abs(samples[i:i + chunk_size]))
                    for i in range(0, len(samples) - chunk_size, chunk_size)
                ])

            # Normalize
            if np.max(np.abs(samples)) > 0:
                samples = samples / np.max(np.abs(samples))

            # Create figure
            fig, ax = plt.subplots(figsize=(size[0] / 50, size[1] / 50), dpi=50)
            ax.fill_between(
                range(len(samples)),
                samples,
                -samples,
                color='#4A90D9',
                alpha=0.7
            )
            ax.set_xlim(0, len(samples))
            ax.set_ylim(-1.1, 1.1)
            ax.axis('off')
            fig.patch.set_alpha(0)
            ax.patch.set_alpha(0)

            # Save to buffer
            buffer = BytesIO()
            plt.savefig(
                buffer,
                format='png',
                bbox_inches='tight',
                pad_inches=0,
                transparent=True
            )
            plt.close(fig)
            buffer.seek(0)

            return base64.b64encode(buffer.read()).decode('utf-8')

        except ImportError:
            logger.warning(
                "matplotlib and numpy required for waveform generation. "
                "Install with: pip install matplotlib numpy"
            )
            return None
        except Exception as e:
            logger.warning(f"Failed to generate waveform: {e}")
            return None

    async def transcribe(self, audio_path: Path) -> Optional[str]:
        """
        Transcribe audio using Gemini API.

        Verified from Story 35.6 (AC 35.6.4): Optional feature flag.

        Args:
            audio_path: Path to audio file

        Returns:
            Transcribed text, or None if transcription fails

        Note:
            Requires GOOGLE_API_KEY environment variable.
            Uses pattern from gemini_vision.py.
        """
        try:
            # Try to import Gemini client
            import google.generativeai as genai

            # Check for API key
            api_key = os.environ.get("GOOGLE_API_KEY")
            if not api_key:
                logger.warning("GOOGLE_API_KEY not set, skipping transcription")
                return None

            genai.configure(api_key=api_key)

            # Read audio file
            audio_bytes = audio_path.read_bytes()

            # Get MIME type
            mime_type = self.get_mime_type(audio_path)

            # Use Gemini for transcription
            model = genai.GenerativeModel('gemini-1.5-flash')

            # Upload audio for processing
            audio_file = genai.upload_file(
                audio_path,
                mime_type=mime_type
            )

            # Generate transcription
            response = model.generate_content([
                "Please transcribe this audio file accurately. "
                "If the audio contains speech in a language other than English, "
                "transcribe it in its original language.",
                audio_file
            ])

            # Clean up uploaded file
            try:
                genai.delete_file(audio_file.name)
            except Exception:
                pass

            if response.text:
                return response.text.strip()

            return None

        except ImportError:
            logger.warning(
                "google-generativeai required for transcription. "
                "Install with: pip install google-generativeai"
            )
            return None
        except Exception as e:
            logger.warning(f"Transcription failed: {e}")
            return None


# ===== Convenience Function =====

async def process_audio(
    audio_path: str | Path,
    related_concept_id: str,
    enable_waveform: bool = False,
    enable_transcription: bool = False,
    max_size_bytes: Optional[int] = None,
) -> MultimodalContent:
    """
    Convenience function to process audio file.

    Verified from Story 35.6 (AC 35.6.5).

    Args:
        audio_path: Path to audio file (string or Path)
        related_concept_id: ID of the related Canvas concept node
        enable_waveform: Enable waveform thumbnail generation
        enable_transcription: Enable Gemini transcription
        max_size_bytes: Optional custom size limit

    Returns:
        MultimodalContent instance

    Example:
        content = await process_audio(
            "lecture.mp3",
            "concept-123",
            enable_transcription=True
        )
    """
    processor = AudioProcessor(
        max_size_bytes=max_size_bytes,
        enable_waveform=enable_waveform,
        enable_transcription=enable_transcription,
    )
    return await processor.process(Path(audio_path), related_concept_id)
