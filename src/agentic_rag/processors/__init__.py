"""
Multimodal content processors for Canvas Learning System (SCP-006).

This module provides processors for handling different types of media content:
- ImageProcessor: PNG, JPG, GIF, SVG processing with thumbnails (Story 6.1)
- PDFProcessor: PDF parsing, thumbnails, metadata extraction (Story 6.2)
- GeminiVisionProcessor: OCR, description, LaTeX recognition (Story 6.4)
- PDFExtractor: PDF structured extraction with TOC and images (Story 6.5)
- MultimodalVectorizer: Text/image/PDF vectorization (Story 6.6)

Verified from:
- Story 6.1 (AC 6.1.1): Canvas节点可附加PNG/JPG/GIF/SVG图片
- Story 6.2 (AC 6.2.1): Canvas节点可附加PDF文件
- Story 6.4 (AC 6.4.1): 图片中的文字自动提取（OCR）
- Story 6.5 (AC 6.5.1-6.5.4): PDF目录提取、章节分块、图片提取
- Story 6.6 (AC 6.6.1-6.6.4): 多模态内容向量化
"""

from .association_engine import (
    AssociationEngine,
    AssociationEngineError,
    AssociationResult,
    AssociationStats,
    MediaRecommendation,
    MediaType,
    RecommendationError,
    RelationCreationError,
    SimilarityCalculationError,
    SimilarityMetric,
    cosine_similarity,
    euclidean_similarity,
    recommend_media,
)
from .gemini_vision import (
    GeminiAPIError,
    GeminiConfigError,
    GeminiTimeoutError,
    GeminiVisionError,
    GeminiVisionProcessor,
    ImageAnalysisResult,
    VisionAnalysis,
    analyze_image,
)
from .image_processor import ImageMetadata, ImageProcessor
from .multimodal_vectorizer import (
    EmbeddingModelError,
    FusedVector,
    MultimodalVectorizer,
    MultimodalVectorizerError,
    VectorizationError,
    VectorizedContent,
    vectorize_image,
    vectorize_pdf_chunks,
)
from .pdf_extractor import (
    PDFChunk,
    PDFExtractionError,
    PDFExtractor,
    PDFExtractorError,
    PDFImage,
    PDFNotFoundError,
    PDFStructure,
    TOCEntry,
    extract_pdf_structure,
)
from .pdf_processor import (
    PageRangeError,
    PDFCorruptError,
    PDFMetadata,
    PDFProcessor,
    PDFProcessorError,
    PDFSizeError,
    PDFValidationError,
    process_pdf,
)
from .video_processor import (
    VideoCorruptError,
    VideoMetadata,
    VideoProcessor,
    VideoProcessorError,
    VideoSizeError,
    VideoValidationError,
    process_video,
)
from .audio_processor import (
    AudioCorruptError,
    AudioProcessor,
    AudioProcessorError,
    AudioSizeError,
    AudioValidationError,
    process_audio,
)

__all__ = [
    # Story 6.1 - Image Processing
    "ImageProcessor",
    "ImageMetadata",
    # Story 6.2 - PDF Processing
    "PDFProcessor",
    "PDFMetadata",
    "PDFProcessorError",
    "PDFValidationError",
    "PDFSizeError",
    "PDFCorruptError",
    "PageRangeError",
    "process_pdf",
    # Story 6.4 - Gemini Vision
    "GeminiVisionProcessor",
    "VisionAnalysis",
    "ImageAnalysisResult",
    "GeminiVisionError",
    "GeminiAPIError",
    "GeminiConfigError",
    "GeminiTimeoutError",
    "analyze_image",
    # Story 6.5 - PDF Extraction
    "PDFExtractor",
    "PDFStructure",
    "PDFChunk",
    "PDFImage",
    "TOCEntry",
    "PDFExtractorError",
    "PDFNotFoundError",
    "PDFExtractionError",
    "extract_pdf_structure",
    # Story 6.6 - Multimodal Vectorization
    "MultimodalVectorizer",
    "VectorizedContent",
    "FusedVector",
    "MultimodalVectorizerError",
    "EmbeddingModelError",
    "VectorizationError",
    "vectorize_image",
    "vectorize_pdf_chunks",
    # Story 6.7 - Auto Association
    "AssociationEngine",
    "MediaRecommendation",
    "AssociationResult",
    "AssociationStats",
    "SimilarityMetric",
    "MediaType",
    "AssociationEngineError",
    "SimilarityCalculationError",
    "RecommendationError",
    "RelationCreationError",
    "recommend_media",
    "cosine_similarity",
    "euclidean_similarity",
    # Story 35.7 - Video Processing
    "VideoProcessor",
    "VideoMetadata",
    "VideoProcessorError",
    "VideoValidationError",
    "VideoSizeError",
    "VideoCorruptError",
    "process_video",
    # Story 35.6 - Audio Processing
    "AudioProcessor",
    "AudioProcessorError",
    "AudioValidationError",
    "AudioSizeError",
    "AudioCorruptError",
    "process_audio",
]
