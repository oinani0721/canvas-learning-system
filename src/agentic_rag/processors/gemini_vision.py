"""
Gemini Vision Processor for Canvas Learning System (Story 6.4)

Provides image analysis using Gemini 2.0 Flash including:
- OCR text extraction (Chinese, English, mixed)
- AI-generated content descriptions
- LaTeX formula recognition
- Code snippet detection

Dependencies:
- google-generativeai: Gemini API client
"""

import asyncio
import base64
import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, TypedDict

try:
    import google.generativeai as genai
except ImportError:
    genai = None


class ImageAnalysisResult(TypedDict):
    """Structured result from image analysis."""
    ocr_text: str
    latex_formulas: list[str]
    code_snippets: list[dict]  # {"language": str, "code": str}
    description: str
    key_concepts: list[str]
    image_type: str  # screenshot, diagram, handwriting, photo, chart, etc.


@dataclass
class VisionAnalysis:
    """Complete vision analysis result."""

    id: str
    image_path: Optional[str]
    mime_type: str
    ocr_text: str
    latex_formulas: list[str] = field(default_factory=list)
    code_snippets: list[dict] = field(default_factory=list)
    description: str = ""
    key_concepts: list[str] = field(default_factory=list)
    image_type: str = "unknown"
    confidence: float = 0.0
    processing_time_ms: int = 0
    analyzed_at: str = field(default_factory=lambda: datetime.now().isoformat())
    raw_response: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "image_path": self.image_path,
            "mime_type": self.mime_type,
            "ocr_text": self.ocr_text,
            "latex_formulas": self.latex_formulas,
            "code_snippets": self.code_snippets,
            "description": self.description,
            "key_concepts": self.key_concepts,
            "image_type": self.image_type,
            "confidence": self.confidence,
            "processing_time_ms": self.processing_time_ms,
            "analyzed_at": self.analyzed_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "VisionAnalysis":
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class GeminiVisionError(Exception):
    """Base exception for Gemini Vision errors."""
    pass


class GeminiAPIError(GeminiVisionError):
    """Raised when Gemini API call fails."""
    pass


class GeminiConfigError(GeminiVisionError):
    """Raised when Gemini is not properly configured."""
    pass


class GeminiTimeoutError(GeminiVisionError):
    """Raised when API call times out."""
    pass


class GeminiVisionProcessor:
    """
    Gemini 2.0 Flash Vision Processor for image analysis.

    Features:
    - OCR: Extract text from images (Chinese, English, mixed)
    - LaTeX: Convert mathematical formulas to LaTeX format
    - Description: Generate Chinese descriptions (50-200 chars)
    - Code Detection: Identify and extract code snippets
    - Image Type: Classify image type

    Usage:
        processor = GeminiVisionProcessor(api_key="your-api-key")
        result = await processor.analyze_image(image_b64, "image/png")
    """

    # Configuration
    MODEL_NAME: str = "gemini-2.0-flash-exp"
    MAX_RETRIES: int = 3
    TIMEOUT_SECONDS: int = 30
    DEFAULT_LANGUAGE: str = "Chinese"

    # Analysis prompt template
    ANALYSIS_PROMPT = """请分析这张图片，完成以下任务：

1. **OCR文字提取**: 识别图片中的所有文字，包括：
   - 普通文本（中文、英文、混合）
   - 数学公式（输出为LaTeX格式，如 $E=mc^2$）
   - 代码片段（标注编程语言）

2. **内容描述**: 用中文描述图片内容（50-200字），包括：
   - 图片类型（截图、手绘、图表、照片、流程图、公式等）
   - 主要内容
   - 关键概念

请严格以JSON格式输出（不要有多余文字）：
{
  "ocr_text": "提取的所有文字内容...",
  "latex_formulas": ["$formula1$", "$formula2$"],
  "code_snippets": [{"language": "python", "code": "代码内容..."}],
  "description": "图片内容的中文描述（50-200字）...",
  "key_concepts": ["关键概念1", "关键概念2", "关键概念3"],
  "image_type": "screenshot|diagram|handwriting|photo|chart|formula|flowchart|other"
}

重要：
- 如果没有数学公式，latex_formulas返回空数组[]
- 如果没有代码，code_snippets返回空数组[]
- 确保description在50-200字之间
- key_concepts提取3-5个关键概念"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: int = None,
        max_retries: int = None
    ):
        """
        Initialize Gemini Vision Processor.

        Args:
            api_key: Gemini API key (or use GOOGLE_API_KEY env var)
            model_name: Model to use (default: gemini-2.0-flash-exp)
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
        """
        if genai is None:
            raise ImportError(
                "google-generativeai is required. "
                "Install with: pip install google-generativeai"
            )

        # Get API key
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise GeminiConfigError(
                "Gemini API key required. Set GOOGLE_API_KEY environment variable "
                "or pass api_key parameter."
            )

        # Configure Gemini
        genai.configure(api_key=self.api_key)

        # Settings
        self.model_name = model_name or self.MODEL_NAME
        self.timeout = timeout or self.TIMEOUT_SECONDS
        self.max_retries = max_retries or self.MAX_RETRIES

        # Initialize model
        self.model = genai.GenerativeModel(self.model_name)

    async def analyze_image(
        self,
        image_data: str | bytes,
        mime_type: str,
        custom_prompt: Optional[str] = None
    ) -> ImageAnalysisResult:
        """
        Analyze image using Gemini Vision.

        Args:
            image_data: Base64-encoded image string or raw bytes
            mime_type: Image MIME type (e.g., "image/png", "image/jpeg")
            custom_prompt: Optional custom analysis prompt

        Returns:
            ImageAnalysisResult with OCR, descriptions, etc.

        Raises:
            GeminiAPIError: If API call fails
            GeminiTimeoutError: If request times out
        """
        import time
        start_time = time.time()

        # Ensure base64 string
        if isinstance(image_data, bytes):
            image_b64 = base64.b64encode(image_data).decode("utf-8")
        else:
            image_b64 = image_data

        # Build prompt
        prompt = custom_prompt or self.ANALYSIS_PROMPT

        # Prepare image part
        image_part = {
            "mime_type": mime_type,
            "data": image_b64
        }

        # Call API with retries
        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = await asyncio.wait_for(
                    self._call_api(image_part, prompt),
                    timeout=self.timeout
                )

                # Parse response
                result = self._parse_response(response.text)

                processing_time = int((time.time() - start_time) * 1000)

                return result

            except asyncio.TimeoutError:
                last_error = GeminiTimeoutError(
                    f"Request timed out after {self.timeout}s (attempt {attempt + 1}/{self.max_retries})"
                )
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff

            except Exception as e:
                last_error = GeminiAPIError(f"API call failed: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(1 * (attempt + 1))

        raise last_error

    async def _call_api(self, image_part: dict, prompt: str):
        """Make async API call to Gemini."""
        # Gemini's generate_content is synchronous, wrap in executor
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.model.generate_content([image_part, prompt])
        )

    def _parse_response(self, response_text: str) -> ImageAnalysisResult:
        """Parse Gemini response into structured result."""
        try:
            # Extract JSON from response (may have markdown code blocks)
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to parse entire response as JSON
                json_str = response_text.strip()

            data = json.loads(json_str)

            return ImageAnalysisResult(
                ocr_text=data.get("ocr_text", ""),
                latex_formulas=data.get("latex_formulas", []),
                code_snippets=data.get("code_snippets", []),
                description=data.get("description", ""),
                key_concepts=data.get("key_concepts", []),
                image_type=data.get("image_type", "unknown")
            )

        except json.JSONDecodeError:
            # If JSON parsing fails, try to extract information manually
            return self._fallback_parse(response_text)

    def _fallback_parse(self, text: str) -> ImageAnalysisResult:
        """Fallback parsing when JSON parsing fails."""
        # Extract what we can from the text
        ocr_text = ""
        description = text[:200] if len(text) > 200 else text

        # Try to find LaTeX formulas
        latex_formulas = re.findall(r'\$[^$]+\$', text)

        return ImageAnalysisResult(
            ocr_text=ocr_text,
            latex_formulas=latex_formulas,
            code_snippets=[],
            description=description,
            key_concepts=[],
            image_type="unknown"
        )

    async def analyze_image_from_path(
        self,
        image_path: str | Path,
        custom_prompt: Optional[str] = None
    ) -> VisionAnalysis:
        """
        Analyze image from file path.

        Args:
            image_path: Path to image file
            custom_prompt: Optional custom analysis prompt

        Returns:
            VisionAnalysis with complete analysis results
        """
        import hashlib
        import time

        start_time = time.time()

        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        # Determine MIME type
        mime_types = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp",
            ".bmp": "image/bmp"
        }
        mime_type = mime_types.get(image_path.suffix.lower(), "image/png")

        # Read and encode image
        with open(image_path, "rb") as f:
            image_data = f.read()

        image_b64 = base64.b64encode(image_data).decode("utf-8")

        # Generate ID
        unique_str = f"{image_path.absolute()}:{len(image_data)}"
        analysis_id = hashlib.sha256(unique_str.encode()).hexdigest()[:16]

        # Analyze
        result = await self.analyze_image(image_b64, mime_type, custom_prompt)

        processing_time = int((time.time() - start_time) * 1000)

        return VisionAnalysis(
            id=analysis_id,
            image_path=str(image_path.absolute()),
            mime_type=mime_type,
            ocr_text=result["ocr_text"],
            latex_formulas=result["latex_formulas"],
            code_snippets=result["code_snippets"],
            description=result["description"],
            key_concepts=result["key_concepts"],
            image_type=result["image_type"],
            processing_time_ms=processing_time
        )

    async def batch_analyze(
        self,
        images: list[tuple[str | bytes, str]],  # [(image_data, mime_type), ...]
        progress_callback: Optional[callable] = None,
        max_concurrent: int = 3
    ) -> list[ImageAnalysisResult]:
        """
        Batch analyze multiple images.

        Args:
            images: List of (image_data, mime_type) tuples
            progress_callback: Optional callback(current, total)
            max_concurrent: Maximum concurrent requests

        Returns:
            List of ImageAnalysisResult
        """
        results = []
        semaphore = asyncio.Semaphore(max_concurrent)

        async def analyze_with_semaphore(idx: int, img_data: str | bytes, mime_type: str):
            async with semaphore:
                try:
                    result = await self.analyze_image(img_data, mime_type)
                    if progress_callback:
                        progress_callback(idx + 1, len(images))
                    return result
                except Exception as e:
                    # Return empty result on error
                    return ImageAnalysisResult(
                        ocr_text="",
                        latex_formulas=[],
                        code_snippets=[],
                        description=f"Error: {str(e)}",
                        key_concepts=[],
                        image_type="error"
                    )

        tasks = [
            analyze_with_semaphore(idx, img_data, mime_type)
            for idx, (img_data, mime_type) in enumerate(images)
        ]

        results = await asyncio.gather(*tasks)
        return list(results)

    def extract_text_only(self, result: ImageAnalysisResult) -> str:
        """
        Extract all text content from analysis result.

        Combines OCR text with LaTeX formulas for full text representation.

        Args:
            result: ImageAnalysisResult from analyze_image

        Returns:
            Combined text content
        """
        parts = []

        if result["ocr_text"]:
            parts.append(result["ocr_text"])

        # Add LaTeX formulas if not already in OCR text
        for formula in result["latex_formulas"]:
            if formula not in result["ocr_text"]:
                parts.append(formula)

        # Add code snippets
        for snippet in result["code_snippets"]:
            code_text = f"[{snippet.get('language', 'code')}]: {snippet.get('code', '')}"
            parts.append(code_text)

        return "\n".join(parts)


# Convenience function
async def analyze_image(
    image_path: str | Path,
    api_key: Optional[str] = None,
    **kwargs
) -> VisionAnalysis:
    """
    Analyze image file and return results.

    Args:
        image_path: Path to image file
        api_key: Gemini API key (optional, uses env var)
        **kwargs: Additional arguments for GeminiVisionProcessor

    Returns:
        VisionAnalysis with OCR, description, etc.
    """
    processor = GeminiVisionProcessor(api_key=api_key, **kwargs)
    return await processor.analyze_image_from_path(image_path)
