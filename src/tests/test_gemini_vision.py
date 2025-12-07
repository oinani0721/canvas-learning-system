"""
Tests for GeminiVisionProcessor (Story 6.4)

Validates:
- AC 6.4.1: 图片OCR文字自动提取（中/英/混合）
- AC 6.4.2: AI生成中文描述（50-200字）
- AC 6.4.3: LaTeX公式识别
- AC 6.4.4: 代码片段检测

Dependencies:
- google-generativeai (mocked for testing)
"""

import asyncio
import base64
import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from agentic_rag.processors.gemini_vision import (
    GeminiAPIError,
    GeminiConfigError,
    GeminiTimeoutError,
    GeminiVisionProcessor,
    VisionAnalysis,
    analyze_image,
)

# ============================================================
# Test Fixtures
# ============================================================

@pytest.fixture
def mock_genai():
    """Mock google.generativeai module."""
    with patch('agentic_rag.processors.gemini_vision.genai') as mock:
        mock.configure = MagicMock()
        mock.GenerativeModel = MagicMock()
        yield mock


@pytest.fixture
def sample_image_b64():
    """Create a minimal valid PNG image as base64."""
    # Minimal 1x1 red PNG
    png_bytes = (
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
        b'\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00'
        b'\x00\x0cIDATx\x9cc\xf8\xcf\xc0\x00\x00\x00\x03\x00\x01'
        b'\x00\x05\xfe\xd4\x00\x00\x00\x00IEND\xaeB`\x82'
    )
    return base64.b64encode(png_bytes).decode('utf-8')


@pytest.fixture
def sample_response_json():
    """Standard Gemini API response format."""
    return {
        "ocr_text": "这是一段中英文混合的测试文本 This is a test.",
        "latex_formulas": ["$E=mc^2$", "$\\frac{d}{dx}$"],
        "code_snippets": [
            {"language": "python", "code": "def hello(): print('Hello')"}
        ],
        "description": "这是一张包含代码和数学公式的截图，主要展示了Python编程和物理公式的混合内容。图片清晰度高，文字易于识别。",
        "key_concepts": ["Python编程", "物理公式", "代码示例"],
        "image_type": "screenshot"
    }


@pytest.fixture
def mock_model_response(sample_response_json):
    """Create mock model response."""
    response = MagicMock()
    response.text = json.dumps(sample_response_json)
    return response


@pytest.fixture
def temp_image_file(tmp_path, sample_image_b64):
    """Create temporary image file."""
    img_path = tmp_path / "test_image.png"
    img_path.write_bytes(base64.b64decode(sample_image_b64))
    return img_path


# ============================================================
# AC 6.4.1: OCR文字提取测试
# ============================================================

class TestOCRExtraction:
    """Test OCR text extraction capabilities."""

    @pytest.mark.asyncio
    async def test_chinese_text_extraction(self, mock_genai, sample_image_b64):
        """Test Chinese text extraction."""
        chinese_response = {
            "ocr_text": "这是纯中文文本测试，包括标点符号。",
            "latex_formulas": [],
            "code_snippets": [],
            "description": "包含中文文本的图片",
            "key_concepts": ["中文"],
            "image_type": "screenshot"
        }

        mock_response = MagicMock()
        mock_response.text = json.dumps(chinese_response)

        mock_model = MagicMock()
        mock_model.generate_content = MagicMock(return_value=mock_response)
        mock_genai.GenerativeModel.return_value = mock_model

        processor = GeminiVisionProcessor(api_key="test-key")

        with patch.object(processor, '_call_api', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_response
            result = await processor.analyze_image(sample_image_b64, "image/png")

        assert "中文" in result["ocr_text"]
        assert result["image_type"] == "screenshot"

    @pytest.mark.asyncio
    async def test_english_text_extraction(self, mock_genai, sample_image_b64):
        """Test English text extraction."""
        english_response = {
            "ocr_text": "This is a test of English text extraction.",
            "latex_formulas": [],
            "code_snippets": [],
            "description": "An image containing English text",
            "key_concepts": ["English"],
            "image_type": "screenshot"
        }

        mock_response = MagicMock()
        mock_response.text = json.dumps(english_response)

        mock_model = MagicMock()
        mock_model.generate_content = MagicMock(return_value=mock_response)
        mock_genai.GenerativeModel.return_value = mock_model

        processor = GeminiVisionProcessor(api_key="test-key")

        with patch.object(processor, '_call_api', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_response
            result = await processor.analyze_image(sample_image_b64, "image/png")

        assert "English" in result["ocr_text"]

    @pytest.mark.asyncio
    async def test_mixed_text_extraction(self, mock_genai, sample_image_b64, sample_response_json):
        """Test mixed Chinese/English text extraction."""
        mock_response = MagicMock()
        mock_response.text = json.dumps(sample_response_json)

        mock_model = MagicMock()
        mock_model.generate_content = MagicMock(return_value=mock_response)
        mock_genai.GenerativeModel.return_value = mock_model

        processor = GeminiVisionProcessor(api_key="test-key")

        with patch.object(processor, '_call_api', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_response
            result = await processor.analyze_image(sample_image_b64, "image/png")

        # Should contain both Chinese and English
        assert "中英文" in result["ocr_text"] or "test" in result["ocr_text"]


# ============================================================
# AC 6.4.2: AI描述生成测试
# ============================================================

class TestDescriptionGeneration:
    """Test AI-generated descriptions."""

    @pytest.mark.asyncio
    async def test_description_length_valid(self, mock_genai, sample_image_b64, sample_response_json):
        """Test description is within 50-200 character range."""
        mock_response = MagicMock()
        mock_response.text = json.dumps(sample_response_json)

        mock_model = MagicMock()
        mock_model.generate_content = MagicMock(return_value=mock_response)
        mock_genai.GenerativeModel.return_value = mock_model

        processor = GeminiVisionProcessor(api_key="test-key")

        with patch.object(processor, '_call_api', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_response
            result = await processor.analyze_image(sample_image_b64, "image/png")

        description = result["description"]
        assert 50 <= len(description) <= 200, f"Description length {len(description)} not in range 50-200"

    @pytest.mark.asyncio
    async def test_description_in_chinese(self, mock_genai, sample_image_b64, sample_response_json):
        """Test description is in Chinese."""
        mock_response = MagicMock()
        mock_response.text = json.dumps(sample_response_json)

        mock_model = MagicMock()
        mock_model.generate_content = MagicMock(return_value=mock_response)
        mock_genai.GenerativeModel.return_value = mock_model

        processor = GeminiVisionProcessor(api_key="test-key")

        with patch.object(processor, '_call_api', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_response
            result = await processor.analyze_image(sample_image_b64, "image/png")

        description = result["description"]
        # Check for Chinese characters
        chinese_chars = [c for c in description if '\u4e00' <= c <= '\u9fff']
        assert len(chinese_chars) > 0, "Description should contain Chinese characters"

    @pytest.mark.asyncio
    async def test_key_concepts_extracted(self, mock_genai, sample_image_b64, sample_response_json):
        """Test key concepts are extracted (3-5 concepts)."""
        mock_response = MagicMock()
        mock_response.text = json.dumps(sample_response_json)

        mock_model = MagicMock()
        mock_model.generate_content = MagicMock(return_value=mock_response)
        mock_genai.GenerativeModel.return_value = mock_model

        processor = GeminiVisionProcessor(api_key="test-key")

        with patch.object(processor, '_call_api', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_response
            result = await processor.analyze_image(sample_image_b64, "image/png")

        concepts = result["key_concepts"]
        assert isinstance(concepts, list)
        assert len(concepts) >= 1  # At least some concepts


# ============================================================
# AC 6.4.3: LaTeX公式识别测试
# ============================================================

class TestLaTeXRecognition:
    """Test LaTeX formula recognition."""

    @pytest.mark.asyncio
    async def test_latex_formula_detection(self, mock_genai, sample_image_b64, sample_response_json):
        """Test LaTeX formulas are detected."""
        mock_response = MagicMock()
        mock_response.text = json.dumps(sample_response_json)

        mock_model = MagicMock()
        mock_model.generate_content = MagicMock(return_value=mock_response)
        mock_genai.GenerativeModel.return_value = mock_model

        processor = GeminiVisionProcessor(api_key="test-key")

        with patch.object(processor, '_call_api', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_response
            result = await processor.analyze_image(sample_image_b64, "image/png")

        formulas = result["latex_formulas"]
        assert isinstance(formulas, list)
        assert len(formulas) > 0
        # Check formula format
        assert any("$" in f for f in formulas)

    @pytest.mark.asyncio
    async def test_empty_latex_when_no_formulas(self, mock_genai, sample_image_b64):
        """Test empty list when no LaTeX formulas present."""
        no_latex_response = {
            "ocr_text": "Just plain text",
            "latex_formulas": [],
            "code_snippets": [],
            "description": "这是一张纯文本图片，没有数学公式或代码内容，仅包含普通的文字说明。",
            "key_concepts": ["文本"],
            "image_type": "screenshot"
        }

        mock_response = MagicMock()
        mock_response.text = json.dumps(no_latex_response)

        mock_model = MagicMock()
        mock_model.generate_content = MagicMock(return_value=mock_response)
        mock_genai.GenerativeModel.return_value = mock_model

        processor = GeminiVisionProcessor(api_key="test-key")

        with patch.object(processor, '_call_api', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_response
            result = await processor.analyze_image(sample_image_b64, "image/png")

        assert result["latex_formulas"] == []


# ============================================================
# AC 6.4.4: 代码片段检测测试
# ============================================================

class TestCodeSnippetDetection:
    """Test code snippet detection."""

    @pytest.mark.asyncio
    async def test_code_snippet_detection(self, mock_genai, sample_image_b64, sample_response_json):
        """Test code snippets are detected with language."""
        mock_response = MagicMock()
        mock_response.text = json.dumps(sample_response_json)

        mock_model = MagicMock()
        mock_model.generate_content = MagicMock(return_value=mock_response)
        mock_genai.GenerativeModel.return_value = mock_model

        processor = GeminiVisionProcessor(api_key="test-key")

        with patch.object(processor, '_call_api', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_response
            result = await processor.analyze_image(sample_image_b64, "image/png")

        snippets = result["code_snippets"]
        assert isinstance(snippets, list)
        assert len(snippets) > 0

        # Check structure
        for snippet in snippets:
            assert "language" in snippet
            assert "code" in snippet

    @pytest.mark.asyncio
    async def test_empty_code_when_no_code(self, mock_genai, sample_image_b64):
        """Test empty list when no code present."""
        no_code_response = {
            "ocr_text": "Just a photo of nature",
            "latex_formulas": [],
            "code_snippets": [],
            "description": "这是一张自然风景照片，展示了美丽的山川湖泊，没有任何文字或代码内容。",
            "key_concepts": ["自然", "风景"],
            "image_type": "photo"
        }

        mock_response = MagicMock()
        mock_response.text = json.dumps(no_code_response)

        mock_model = MagicMock()
        mock_model.generate_content = MagicMock(return_value=mock_response)
        mock_genai.GenerativeModel.return_value = mock_model

        processor = GeminiVisionProcessor(api_key="test-key")

        with patch.object(processor, '_call_api', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_response
            result = await processor.analyze_image(sample_image_b64, "image/png")

        assert result["code_snippets"] == []


# ============================================================
# Error Handling Tests
# ============================================================

class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_missing_api_key_raises_error(self, mock_genai):
        """Test that missing API key raises GeminiConfigError."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(GeminiConfigError):
                GeminiVisionProcessor(api_key=None)

    @pytest.mark.asyncio
    async def test_timeout_handling(self, mock_genai, sample_image_b64):
        """Test timeout is handled properly."""
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model

        processor = GeminiVisionProcessor(api_key="test-key", timeout=1, max_retries=1)

        with patch.object(processor, '_call_api', new_callable=AsyncMock) as mock_call:
            mock_call.side_effect = asyncio.TimeoutError()

            with pytest.raises(GeminiTimeoutError):
                await processor.analyze_image(sample_image_b64, "image/png")

    @pytest.mark.asyncio
    async def test_api_error_handling(self, mock_genai, sample_image_b64):
        """Test API errors are handled properly."""
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model

        processor = GeminiVisionProcessor(api_key="test-key", max_retries=1)

        with patch.object(processor, '_call_api', new_callable=AsyncMock) as mock_call:
            mock_call.side_effect = Exception("API Error")

            with pytest.raises(GeminiAPIError):
                await processor.analyze_image(sample_image_b64, "image/png")

    @pytest.mark.asyncio
    async def test_invalid_json_fallback_parsing(self, mock_genai, sample_image_b64):
        """Test fallback parsing when JSON is invalid."""
        mock_response = MagicMock()
        mock_response.text = "This is not valid JSON but contains $E=mc^2$ formula"

        mock_model = MagicMock()
        mock_model.generate_content = MagicMock(return_value=mock_response)
        mock_genai.GenerativeModel.return_value = mock_model

        processor = GeminiVisionProcessor(api_key="test-key")

        with patch.object(processor, '_call_api', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_response
            result = await processor.analyze_image(sample_image_b64, "image/png")

        # Should use fallback parsing
        assert result["image_type"] == "unknown"
        # Should extract LaTeX from text
        assert len(result["latex_formulas"]) > 0


# ============================================================
# VisionAnalysis Dataclass Tests
# ============================================================

class TestVisionAnalysis:
    """Test VisionAnalysis dataclass."""

    def test_to_dict(self):
        """Test VisionAnalysis.to_dict() method."""
        analysis = VisionAnalysis(
            id="test123",
            image_path="/path/to/image.png",
            mime_type="image/png",
            ocr_text="Test text",
            latex_formulas=["$x^2$"],
            code_snippets=[{"language": "python", "code": "pass"}],
            description="Test description",
            key_concepts=["test"],
            image_type="screenshot",
            confidence=0.95,
            processing_time_ms=100
        )

        result = analysis.to_dict()

        assert result["id"] == "test123"
        assert result["ocr_text"] == "Test text"
        assert result["latex_formulas"] == ["$x^2$"]
        assert result["confidence"] == 0.95

    def test_from_dict(self):
        """Test VisionAnalysis.from_dict() method."""
        data = {
            "id": "test456",
            "image_path": "/path/to/image.png",
            "mime_type": "image/png",
            "ocr_text": "Loaded text",
            "latex_formulas": [],
            "code_snippets": [],
            "description": "Loaded description",
            "key_concepts": [],
            "image_type": "photo",
            "confidence": 0.8,
            "processing_time_ms": 50
        }

        analysis = VisionAnalysis.from_dict(data)

        assert analysis.id == "test456"
        assert analysis.ocr_text == "Loaded text"
        assert analysis.image_type == "photo"


# ============================================================
# File-based Analysis Tests
# ============================================================

class TestFileAnalysis:
    """Test file-based image analysis."""

    @pytest.mark.asyncio
    async def test_analyze_from_path(self, mock_genai, temp_image_file, sample_response_json):
        """Test analyzing image from file path."""
        mock_response = MagicMock()
        mock_response.text = json.dumps(sample_response_json)

        mock_model = MagicMock()
        mock_model.generate_content = MagicMock(return_value=mock_response)
        mock_genai.GenerativeModel.return_value = mock_model

        processor = GeminiVisionProcessor(api_key="test-key")

        with patch.object(processor, '_call_api', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_response
            result = await processor.analyze_image_from_path(temp_image_file)

        assert isinstance(result, VisionAnalysis)
        assert result.image_path == str(temp_image_file.absolute())
        assert result.mime_type == "image/png"
        assert len(result.id) == 16  # SHA256 hash prefix

    @pytest.mark.asyncio
    async def test_file_not_found_error(self, mock_genai):
        """Test FileNotFoundError for missing image."""
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model

        processor = GeminiVisionProcessor(api_key="test-key")

        with pytest.raises(FileNotFoundError):
            await processor.analyze_image_from_path("/nonexistent/image.png")


# ============================================================
# Batch Processing Tests
# ============================================================

class TestBatchProcessing:
    """Test batch image processing."""

    @pytest.mark.asyncio
    async def test_batch_analyze(self, mock_genai, sample_image_b64, sample_response_json):
        """Test batch processing of multiple images."""
        mock_response = MagicMock()
        mock_response.text = json.dumps(sample_response_json)

        mock_model = MagicMock()
        mock_model.generate_content = MagicMock(return_value=mock_response)
        mock_genai.GenerativeModel.return_value = mock_model

        processor = GeminiVisionProcessor(api_key="test-key")

        images = [
            (sample_image_b64, "image/png"),
            (sample_image_b64, "image/png"),
            (sample_image_b64, "image/png"),
        ]

        with patch.object(processor, 'analyze_image', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = sample_response_json
            results = await processor.batch_analyze(images)

        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_batch_with_progress_callback(self, mock_genai, sample_image_b64, sample_response_json):
        """Test batch processing with progress callback."""
        mock_response = MagicMock()
        mock_response.text = json.dumps(sample_response_json)

        mock_model = MagicMock()
        mock_model.generate_content = MagicMock(return_value=mock_response)
        mock_genai.GenerativeModel.return_value = mock_model

        processor = GeminiVisionProcessor(api_key="test-key")

        progress_calls = []
        def progress_callback(current, total):
            progress_calls.append((current, total))

        images = [
            (sample_image_b64, "image/png"),
            (sample_image_b64, "image/png"),
        ]

        with patch.object(processor, 'analyze_image', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = sample_response_json
            await processor.batch_analyze(images, progress_callback=progress_callback)

        # Progress should have been called
        assert len(progress_calls) == 2


# ============================================================
# Text Extraction Utility Tests
# ============================================================

class TestTextExtraction:
    """Test text extraction utility."""

    def test_extract_text_only(self, mock_genai, sample_response_json):
        """Test extract_text_only combines all text content."""
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model

        processor = GeminiVisionProcessor(api_key="test-key")

        result = processor.extract_text_only(sample_response_json)

        assert "中英文" in result or "test" in result
        # Code snippets should be included
        assert "python" in result.lower() or "hello" in result.lower()


# ============================================================
# Convenience Function Tests
# ============================================================

class TestConvenienceFunction:
    """Test analyze_image convenience function."""

    @pytest.mark.asyncio
    async def test_analyze_image_function(self, mock_genai, temp_image_file, sample_response_json):
        """Test the analyze_image convenience function."""
        mock_response = MagicMock()
        mock_response.text = json.dumps(sample_response_json)

        mock_model = MagicMock()
        mock_model.generate_content = MagicMock(return_value=mock_response)
        mock_genai.GenerativeModel.return_value = mock_model

        with patch('agentic_rag.processors.gemini_vision.GeminiVisionProcessor') as MockProcessor:
            mock_instance = MagicMock()
            mock_instance.analyze_image_from_path = AsyncMock(return_value=VisionAnalysis(
                id="test",
                image_path=str(temp_image_file),
                mime_type="image/png",
                ocr_text="Test",
                description="Test description with enough characters to meet the minimum requirement."
            ))
            MockProcessor.return_value = mock_instance

            result = await analyze_image(temp_image_file, api_key="test-key")

        assert isinstance(result, VisionAnalysis)


# ============================================================
# Image Type Classification Tests
# ============================================================

class TestImageTypeClassification:
    """Test image type classification."""

    @pytest.mark.asyncio
    async def test_screenshot_classification(self, mock_genai, sample_image_b64):
        """Test screenshot type classification."""
        response = {
            "ocr_text": "File Edit View",
            "latex_formulas": [],
            "code_snippets": [],
            "description": "这是一张软件界面截图，展示了菜单栏和工具栏的布局设计。",
            "key_concepts": ["界面", "截图"],
            "image_type": "screenshot"
        }

        mock_response = MagicMock()
        mock_response.text = json.dumps(response)

        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model

        processor = GeminiVisionProcessor(api_key="test-key")

        with patch.object(processor, '_call_api', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_response
            result = await processor.analyze_image(sample_image_b64, "image/png")

        assert result["image_type"] == "screenshot"

    @pytest.mark.asyncio
    async def test_diagram_classification(self, mock_genai, sample_image_b64):
        """Test diagram type classification."""
        response = {
            "ocr_text": "A -> B -> C",
            "latex_formulas": [],
            "code_snippets": [],
            "description": "这是一张流程图，展示了从A到B再到C的数据流转过程。",
            "key_concepts": ["流程图", "数据流"],
            "image_type": "diagram"
        }

        mock_response = MagicMock()
        mock_response.text = json.dumps(response)

        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model

        processor = GeminiVisionProcessor(api_key="test-key")

        with patch.object(processor, '_call_api', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_response
            result = await processor.analyze_image(sample_image_b64, "image/png")

        assert result["image_type"] == "diagram"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
