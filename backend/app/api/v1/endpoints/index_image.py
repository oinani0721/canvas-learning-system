# Canvas Learning System - Image Index API
# Story 1.6: Image OCR extraction via Vision API (AC-4, AC-5)
"""
POST /api/v1/index/image

Receives a base64 image, calls a Vision-capable LLM via LiteLLM
to extract OCR text, summary, and concepts. Returns structured results.

[Source: _bmad-output/implementation-artifacts/1-6-image-node-async-index.md#Task 7]
"""

import json
import logging
import time
from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.config import settings

logger = logging.getLogger(__name__)

index_image_router = APIRouter()


# ═══════════════════════════════════════════════════════════════════════════════
# Request / Response Models
# ═══════════════════════════════════════════════════════════════════════════════


class ImageIndexRequest(BaseModel):
    """Request body for image OCR indexing."""

    node_id: str = Field(..., description="Canvas node ID")
    image_data: str = Field(..., description="Base64 DataURL of the image")


class ImageIndexResponse(BaseModel):
    """Response from image OCR indexing."""

    node_id: str
    ocr_text: str
    summary: str
    concepts: List[str]
    processing_time_ms: int


# ═══════════════════════════════════════════════════════════════════════════════
# Vision Extraction Prompt
# ═══════════════════════════════════════════════════════════════════════════════

EXTRACTION_PROMPT = """请分析这张图片，提取以下信息并以 JSON 格式返回：
{
  "ocr_text": "图片中所有可见文字的完整转录（保留原始格式，公式使用 LaTeX 表示）",
  "summary": "图片内容的一句话摘要",
  "concepts": ["提取的核心概念/术语列表"]
}
注意：
- 数学公式使用 LaTeX 格式（如 $E=mc^2$）
- 代码块保持原始格式
- 概念列表提取 3-10 个核心术语
- 如果图片中没有文字，ocr_text 填写图片的详细描述
- 必须返回有效的 JSON"""


# ═══════════════════════════════════════════════════════════════════════════════
# API Endpoint
# ═══════════════════════════════════════════════════════════════════════════════


@index_image_router.post(
    "/index/image",
    response_model=ImageIndexResponse,
    summary="Extract text/concepts from image via Vision API",
    operation_id="index_image",
)
async def index_image(request: ImageIndexRequest) -> ImageIndexResponse:
    """
    Process an image through Vision API for OCR extraction.

    - Validates the image data format
    - Calls Vision-capable LLM via LiteLLM
    - Returns structured OCR text, summary, and concepts
    - Timeout: 30s per call (NFR-PERF-05 target < 10s)

    [Source: Story 1.6 AC-4, AC-5]
    """
    start_time = time.time()

    # Validate base64 DataURL format
    if not request.image_data.startswith("data:image/"):
        raise HTTPException(
            status_code=400,
            detail="Invalid image data: must be a base64 DataURL starting with 'data:image/'",
        )

    # Determine supported image types
    supported_types = (
        "data:image/png",
        "data:image/jpeg",
        "data:image/jpg",
        "data:image/webp",
    )
    if not any(request.image_data.startswith(t) for t in supported_types):
        raise HTTPException(
            status_code=400,
            detail="Unsupported image format. Supported: PNG, JPEG, WebP",
        )

    try:
        import litellm

        # Use the configured vision model, fallback to chat model
        vision_model = getattr(settings, "VISION_MODEL", None) or getattr(
            settings, "CHAT_MODEL", "gemini/gemini-2.0-flash"
        )

        response = await litellm.acompletion(
            model=vision_model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": EXTRACTION_PROMPT},
                        {"type": "image_url", "image_url": {"url": request.image_data}},
                    ],
                }
            ],
            timeout=30,
            response_format={"type": "json_object"},
        )

        raw_content = response.choices[0].message.content
        if not raw_content:
            raise HTTPException(
                status_code=502,
                detail="Vision API returned empty response",
            )

        # Parse JSON response
        result = json.loads(raw_content)

        processing_time_ms = int((time.time() - start_time) * 1000)

        return ImageIndexResponse(
            node_id=request.node_id,
            ocr_text=result.get("ocr_text", ""),
            summary=result.get("summary", ""),
            concepts=result.get("concepts", []),
            processing_time_ms=processing_time_ms,
        )

    except json.JSONDecodeError as e:
        logger.error(f"Vision API returned invalid JSON: {e}")
        raise HTTPException(
            status_code=502,
            detail=f"Vision API returned invalid JSON: {e}",
        )
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="LiteLLM not available — Vision API cannot be called",
        )
    except Exception as e:
        error_msg = str(e)
        if "timeout" in error_msg.lower():
            raise HTTPException(
                status_code=504,
                detail=f"Vision API timeout: {error_msg}",
            )
        logger.error(f"Vision API error: {error_msg}")
        raise HTTPException(
            status_code=503,
            detail=f"Vision API error: {error_msg}",
        )
