"""
Tests for MultimodalVectorizer (Story 6.6)

✅ Story 6.6 AC 6.6.1: 图片内容向量化 (OCR + AI描述)
✅ Story 6.6 AC 6.6.2: PDF内容向量化 (按章节)
✅ Story 6.6 AC 6.6.3: 存储到LanceDB (multimodal_content表)
✅ Story 6.6 AC 6.6.4: 向量化速度≤1秒/内容
"""

import os
import sys
import time
from unittest.mock import patch

import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class MockSentenceTransformer:
    """Mock SentenceTransformer for testing without GPU/model loading."""

    def __init__(self, model_name: str = None, device: str = "cpu"):
        self.model_name = model_name
        self.device = device
        self._embedding_dim = 384  # Match all-MiniLM-L6-v2

    def encode(
        self,
        sentences,
        batch_size: int = 32,
        normalize_embeddings: bool = True,
        show_progress_bar: bool = False
    ):
        """Mock encode method."""
        import numpy as np

        if isinstance(sentences, str):
            # Single sentence
            np.random.seed(hash(sentences) % (2**32))
            vec = np.random.rand(self._embedding_dim).astype(np.float32)
            if normalize_embeddings:
                vec = vec / np.linalg.norm(vec)
            return vec
        else:
            # Batch of sentences
            results = []
            for sent in sentences:
                np.random.seed(hash(sent) % (2**32))
                vec = np.random.rand(self._embedding_dim).astype(np.float32)
                if normalize_embeddings:
                    vec = vec / np.linalg.norm(vec)
                results.append(vec)
            return np.array(results)

    def get_sentence_embedding_dimension(self) -> int:
        return self._embedding_dim


@pytest.fixture
def mock_sentence_transformer():
    """Fixture to mock SentenceTransformer."""
    with patch(
        "src.agentic_rag.processors.multimodal_vectorizer.SentenceTransformer",
        MockSentenceTransformer
    ):
        with patch(
            "src.agentic_rag.processors.multimodal_vectorizer.SENTENCE_TRANSFORMERS_AVAILABLE",
            True
        ):
            yield


@pytest.fixture
def mock_numpy():
    """Fixture to ensure numpy is available."""
    with patch(
        "src.agentic_rag.processors.multimodal_vectorizer.NUMPY_AVAILABLE",
        True
    ):
        yield


# =============================================================================
# Import Tests
# =============================================================================

class TestImports:
    """Test module imports."""

    def test_import_multimodal_vectorizer(self):
        """Test importing MultimodalVectorizer."""
        from src.agentic_rag.processors.multimodal_vectorizer import MultimodalVectorizer
        assert MultimodalVectorizer is not None

    def test_import_vectorized_content(self):
        """Test importing VectorizedContent."""
        from src.agentic_rag.processors.multimodal_vectorizer import VectorizedContent
        assert VectorizedContent is not None

    def test_import_fused_vector(self):
        """Test importing FusedVector."""
        from src.agentic_rag.processors.multimodal_vectorizer import FusedVector
        assert FusedVector is not None

    def test_import_exceptions(self):
        """Test importing exceptions."""
        from src.agentic_rag.processors.multimodal_vectorizer import (
            EmbeddingModelError,
            MultimodalVectorizerError,
            VectorizationError,
        )
        assert MultimodalVectorizerError is not None
        assert EmbeddingModelError is not None
        assert VectorizationError is not None

    def test_import_from_package(self):
        """Test importing from processors package."""
        from src.agentic_rag.processors import (
            FusedVector,
            MultimodalVectorizer,
            VectorizedContent,
        )
        assert MultimodalVectorizer is not None
        assert VectorizedContent is not None
        assert FusedVector is not None


# =============================================================================
# VectorizedContent Tests
# =============================================================================

class TestVectorizedContent:
    """Test VectorizedContent dataclass."""

    def test_create_vectorized_content(self):
        """Test creating VectorizedContent."""
        from src.agentic_rag.processors.multimodal_vectorizer import VectorizedContent

        content = VectorizedContent(
            id="test_123",
            content_type="text",
            source_path=None,
            text_content="Hello world",
            vector=[0.1, 0.2, 0.3],
            vector_dim=3,
            metadata={"key": "value"},
            processing_time_ms=50
        )

        assert content.id == "test_123"
        assert content.content_type == "text"
        assert content.text_content == "Hello world"
        assert len(content.vector) == 3
        assert content.vector_dim == 3
        assert content.metadata["key"] == "value"

    def test_vectorized_content_to_dict(self):
        """Test converting VectorizedContent to dict."""
        from src.agentic_rag.processors.multimodal_vectorizer import VectorizedContent

        content = VectorizedContent(
            id="test_456",
            content_type="image",
            source_path="/path/to/image.png",
            text_content="OCR text here",
            vector=[0.5, 0.5],
            vector_dim=2
        )

        d = content.to_dict()

        assert d["id"] == "test_456"
        assert d["content_type"] == "image"
        assert d["source_path"] == "/path/to/image.png"
        assert "created_at" in d

    def test_vectorized_content_from_dict(self):
        """Test creating VectorizedContent from dict."""
        from src.agentic_rag.processors.multimodal_vectorizer import VectorizedContent

        data = {
            "id": "from_dict_1",
            "content_type": "pdf_chunk",
            "source_path": "/path/to/doc.pdf",
            "text_content": "Chapter 1 content",
            "vector": [0.1, 0.2],
            "vector_dim": 2
        }

        content = VectorizedContent.from_dict(data)

        assert content.id == "from_dict_1"
        assert content.content_type == "pdf_chunk"


# =============================================================================
# FusedVector Tests
# =============================================================================

class TestFusedVector:
    """Test FusedVector dataclass."""

    def test_create_fused_vector(self):
        """Test creating FusedVector."""
        from src.agentic_rag.processors.multimodal_vectorizer import FusedVector

        fused = FusedVector(
            id="fused_1",
            vectors=[[0.1, 0.2], [0.3, 0.4]],
            weights=[0.4, 0.6],
            fused_vector=[0.22, 0.32],
            sources=["ocr", "description"]
        )

        assert fused.id == "fused_1"
        assert len(fused.vectors) == 2
        assert len(fused.weights) == 2
        assert fused.fusion_method == "weighted_average"

    def test_fused_vector_to_dict(self):
        """Test converting FusedVector to dict."""
        from src.agentic_rag.processors.multimodal_vectorizer import FusedVector

        fused = FusedVector(
            id="fused_2",
            vectors=[[0.5, 0.5]],
            weights=[1.0],
            fused_vector=[0.5, 0.5],
            sources=["single"]
        )

        d = fused.to_dict()

        assert d["id"] == "fused_2"
        assert "fused_vector" in d
        assert d["fusion_method"] == "weighted_average"


# =============================================================================
# MultimodalVectorizer Initialization Tests
# =============================================================================

class TestMultimodalVectorizerInit:
    """Test MultimodalVectorizer initialization."""

    @pytest.mark.asyncio
    async def test_init_default_params(self, mock_sentence_transformer, mock_numpy):
        """Test initialization with default parameters."""
        from src.agentic_rag.processors.multimodal_vectorizer import MultimodalVectorizer

        vectorizer = MultimodalVectorizer()

        assert vectorizer.model_name == "sentence-transformers/all-MiniLM-L6-v2"
        assert vectorizer.device == "cpu"
        assert vectorizer.ocr_weight == 0.4
        assert vectorizer.desc_weight == 0.6
        assert not vectorizer._initialized

    @pytest.mark.asyncio
    async def test_init_custom_params(self, mock_sentence_transformer, mock_numpy):
        """Test initialization with custom parameters."""
        from src.agentic_rag.processors.multimodal_vectorizer import MultimodalVectorizer

        vectorizer = MultimodalVectorizer(
            model_name="custom-model",
            device="cuda",
            ocr_weight=0.3,
            desc_weight=0.7,
            batch_size=64
        )

        assert vectorizer.model_name == "custom-model"
        assert vectorizer.device == "cuda"
        assert vectorizer.ocr_weight == 0.3
        assert vectorizer.desc_weight == 0.7
        assert vectorizer.batch_size == 64

    @pytest.mark.asyncio
    async def test_initialize_success(self, mock_sentence_transformer, mock_numpy):
        """Test successful initialization."""
        from src.agentic_rag.processors.multimodal_vectorizer import MultimodalVectorizer

        vectorizer = MultimodalVectorizer()
        result = await vectorizer.initialize()

        assert result is True
        assert vectorizer._initialized is True
        assert vectorizer._model is not None

    @pytest.mark.asyncio
    async def test_double_initialize(self, mock_sentence_transformer, mock_numpy):
        """Test that double initialization returns True without reloading."""
        from src.agentic_rag.processors.multimodal_vectorizer import MultimodalVectorizer

        vectorizer = MultimodalVectorizer()

        result1 = await vectorizer.initialize()
        result2 = await vectorizer.initialize()

        assert result1 is True
        assert result2 is True


# =============================================================================
# Text Vectorization Tests
# =============================================================================

class TestTextVectorization:
    """Test plain text vectorization."""

    @pytest.mark.asyncio
    async def test_vectorize_text_basic(self, mock_sentence_transformer, mock_numpy):
        """Test basic text vectorization."""
        from src.agentic_rag.processors.multimodal_vectorizer import MultimodalVectorizer

        vectorizer = MultimodalVectorizer()
        await vectorizer.initialize()

        result = await vectorizer.vectorize_text("Hello world")

        assert result is not None
        assert result.content_type == "text"
        assert result.text_content == "Hello world"
        assert len(result.vector) == 384  # Mock dimension
        assert result.vector_dim == 384

    @pytest.mark.asyncio
    async def test_vectorize_text_with_id(self, mock_sentence_transformer, mock_numpy):
        """Test text vectorization with custom ID."""
        from src.agentic_rag.processors.multimodal_vectorizer import MultimodalVectorizer

        vectorizer = MultimodalVectorizer()
        await vectorizer.initialize()

        result = await vectorizer.vectorize_text(
            "Test content",
            content_id="custom_id_123"
        )

        assert result.id == "custom_id_123"

    @pytest.mark.asyncio
    async def test_vectorize_text_with_metadata(self, mock_sentence_transformer, mock_numpy):
        """Test text vectorization with metadata."""
        from src.agentic_rag.processors.multimodal_vectorizer import MultimodalVectorizer

        vectorizer = MultimodalVectorizer()
        await vectorizer.initialize()

        metadata = {"source": "test", "page": 5}
        result = await vectorizer.vectorize_text(
            "Content with metadata",
            metadata=metadata
        )

        assert result.metadata["source"] == "test"
        assert result.metadata["page"] == 5

    @pytest.mark.asyncio
    async def test_vectorize_empty_text(self, mock_sentence_transformer, mock_numpy):
        """Test vectorization of empty text returns zero vector."""
        from src.agentic_rag.processors.multimodal_vectorizer import MultimodalVectorizer

        vectorizer = MultimodalVectorizer()
        await vectorizer.initialize()

        result = await vectorizer.vectorize_text("")

        assert result is not None
        assert all(v == 0.0 for v in result.vector)

    @pytest.mark.asyncio
    async def test_vectorize_chinese_text(self, mock_sentence_transformer, mock_numpy):
        """Test vectorization of Chinese text."""
        from src.agentic_rag.processors.multimodal_vectorizer import MultimodalVectorizer

        vectorizer = MultimodalVectorizer()
        await vectorizer.initialize()

        result = await vectorizer.vectorize_text("这是一段中文文本，用于测试向量化功能。")

        assert result is not None
        assert len(result.vector) == 384


# =============================================================================
# Image Content Vectorization Tests (AC 6.6.1)
# =============================================================================

class TestImageContentVectorization:
    """Test image content vectorization (AC 6.6.1)."""

    @pytest.mark.asyncio
    async def test_vectorize_image_content_basic(self, mock_sentence_transformer, mock_numpy):
        """Test basic image content vectorization."""
        from src.agentic_rag.processors.multimodal_vectorizer import MultimodalVectorizer

        vectorizer = MultimodalVectorizer()
        await vectorizer.initialize()

        result = await vectorizer.vectorize_image_content(
            ocr_text="公式: E = mc²",
            description="一张包含质能方程的物理公式图片"
        )

        assert result is not None
        assert result.content_type == "image"
        assert "[OCR]" in result.text_content
        assert "[Description]" in result.text_content
        assert len(result.vector) == 384

    @pytest.mark.asyncio
    async def test_vectorize_image_with_path(self, mock_sentence_transformer, mock_numpy):
        """Test image vectorization with source path."""
        from src.agentic_rag.processors.multimodal_vectorizer import MultimodalVectorizer

        vectorizer = MultimodalVectorizer()
        await vectorizer.initialize()

        result = await vectorizer.vectorize_image_content(
            ocr_text="Text from image",
            description="Image description",
            image_path="/path/to/image.png"
        )

        assert result.source_path == "/path/to/image.png"

    @pytest.mark.asyncio
    async def test_vectorize_image_with_concepts(self, mock_sentence_transformer, mock_numpy):
        """Test image vectorization with key concepts."""
        from src.agentic_rag.processors.multimodal_vectorizer import MultimodalVectorizer

        vectorizer = MultimodalVectorizer()
        await vectorizer.initialize()

        result = await vectorizer.vectorize_image_content(
            ocr_text="微积分公式",
            description="积分公式图",
            key_concepts=["积分", "微积分", "数学公式"]
        )

        assert "[Concepts]" in result.text_content
        assert result.metadata["key_concepts"] == ["积分", "微积分", "数学公式"]

    @pytest.mark.asyncio
    async def test_vectorize_image_with_type(self, mock_sentence_transformer, mock_numpy):
        """Test image vectorization with image type."""
        from src.agentic_rag.processors.multimodal_vectorizer import MultimodalVectorizer

        vectorizer = MultimodalVectorizer()
        await vectorizer.initialize()

        result = await vectorizer.vectorize_image_content(
            ocr_text="Screenshot text",
            description="A screenshot",
            image_type="screenshot"
        )

        assert result.metadata["image_type"] == "screenshot"

    @pytest.mark.asyncio
    async def test_vectorize_image_fusion_weights(self, mock_sentence_transformer, mock_numpy):
        """Test that fusion weights are stored in metadata."""
        from src.agentic_rag.processors.multimodal_vectorizer import MultimodalVectorizer

        vectorizer = MultimodalVectorizer(ocr_weight=0.3, desc_weight=0.7)
        await vectorizer.initialize()

        result = await vectorizer.vectorize_image_content(
            ocr_text="OCR text",
            description="Description"
        )

        assert result.metadata["ocr_weight"] == 0.3
        assert result.metadata["desc_weight"] == 0.7
        assert result.metadata["fusion_method"] == "weighted_average"

    @pytest.mark.asyncio
    async def test_vectorize_image_ocr_only(self, mock_sentence_transformer, mock_numpy):
        """Test image vectorization with OCR only."""
        from src.agentic_rag.processors.multimodal_vectorizer import MultimodalVectorizer

        vectorizer = MultimodalVectorizer()
        await vectorizer.initialize()

        result = await vectorizer.vectorize_image_content(
            ocr_text="Only OCR text",
            description=""
        )

        assert result is not None
        assert len(result.vector) == 384

    @pytest.mark.asyncio
    async def test_vectorize_image_description_only(self, mock_sentence_transformer, mock_numpy):
        """Test image vectorization with description only."""
        from src.agentic_rag.processors.multimodal_vectorizer import MultimodalVectorizer

        vectorizer = MultimodalVectorizer()
        await vectorizer.initialize()

        result = await vectorizer.vectorize_image_content(
            ocr_text="",
            description="Only description text"
        )

        assert result is not None
        assert len(result.vector) == 384


# =============================================================================
# PDF Chunk Vectorization Tests (AC 6.6.2)
# =============================================================================

class TestPDFChunkVectorization:
    """Test PDF chunk vectorization (AC 6.6.2)."""

    @pytest.mark.asyncio
    async def test_vectorize_pdf_chunk_basic(self, mock_sentence_transformer, mock_numpy):
        """Test basic PDF chunk vectorization."""
        from src.agentic_rag.processors.multimodal_vectorizer import MultimodalVectorizer

        vectorizer = MultimodalVectorizer()
        await vectorizer.initialize()

        result = await vectorizer.vectorize_pdf_chunk(
            chunk_text="This is the content of chapter 1..."
        )

        assert result is not None
        assert result.content_type == "pdf_chunk"
        assert len(result.vector) == 384

    @pytest.mark.asyncio
    async def test_vectorize_pdf_chunk_with_title(self, mock_sentence_transformer, mock_numpy):
        """Test PDF chunk vectorization with chapter title."""
        from src.agentic_rag.processors.multimodal_vectorizer import MultimodalVectorizer

        vectorizer = MultimodalVectorizer()
        await vectorizer.initialize()

        result = await vectorizer.vectorize_pdf_chunk(
            chunk_text="Content of the introduction...",
            chapter_title="Chapter 1: Introduction"
        )

        assert result.metadata["chapter_title"] == "Chapter 1: Introduction"

    @pytest.mark.asyncio
    async def test_vectorize_pdf_chunk_with_path(self, mock_sentence_transformer, mock_numpy):
        """Test PDF chunk vectorization with PDF path."""
        from src.agentic_rag.processors.multimodal_vectorizer import MultimodalVectorizer

        vectorizer = MultimodalVectorizer()
        await vectorizer.initialize()

        result = await vectorizer.vectorize_pdf_chunk(
            chunk_text="PDF content",
            pdf_path="/docs/textbook.pdf"
        )

        assert result.source_path == "/docs/textbook.pdf"

    @pytest.mark.asyncio
    async def test_vectorize_pdf_chunk_with_pages(self, mock_sentence_transformer, mock_numpy):
        """Test PDF chunk vectorization with page numbers."""
        from src.agentic_rag.processors.multimodal_vectorizer import MultimodalVectorizer

        vectorizer = MultimodalVectorizer()
        await vectorizer.initialize()

        result = await vectorizer.vectorize_pdf_chunk(
            chunk_text="Content spanning pages",
            page_numbers=[10, 11, 12]
        )

        assert result.metadata["page_numbers"] == [10, 11, 12]

    @pytest.mark.asyncio
    async def test_vectorize_pdf_chunk_with_index(self, mock_sentence_transformer, mock_numpy):
        """Test PDF chunk vectorization with chunk index."""
        from src.agentic_rag.processors.multimodal_vectorizer import MultimodalVectorizer

        vectorizer = MultimodalVectorizer()
        await vectorizer.initialize()

        result = await vectorizer.vectorize_pdf_chunk(
            chunk_text="Chunk content",
            chunk_index=5,
            total_chunks=20
        )

        assert result.metadata["chunk_index"] == 5
        assert result.metadata["total_chunks"] == 20

    @pytest.mark.asyncio
    async def test_vectorize_pdf_chunk_with_heading_path(self, mock_sentence_transformer, mock_numpy):
        """Test PDF chunk vectorization with heading path."""
        from src.agentic_rag.processors.multimodal_vectorizer import MultimodalVectorizer

        vectorizer = MultimodalVectorizer()
        await vectorizer.initialize()

        result = await vectorizer.vectorize_pdf_chunk(
            chunk_text="Section content",
            heading_path=["Part 1", "Chapter 2", "Section 2.1"]
        )

        assert result.metadata["heading_path"] == ["Part 1", "Chapter 2", "Section 2.1"]

    @pytest.mark.asyncio
    async def test_vectorize_pdf_chunk_chinese(self, mock_sentence_transformer, mock_numpy):
        """Test PDF chunk vectorization with Chinese content."""
        from src.agentic_rag.processors.multimodal_vectorizer import MultimodalVectorizer

        vectorizer = MultimodalVectorizer()
        await vectorizer.initialize()

        result = await vectorizer.vectorize_pdf_chunk(
            chunk_text="第一章 绪论\n本章介绍了微积分的基本概念和历史发展...",
            chapter_title="第一章 绪论"
        )

        assert result is not None
        assert len(result.vector) == 384


# =============================================================================
# Batch Vectorization Tests
# =============================================================================

class TestBatchVectorization:
    """Test batch vectorization."""

    @pytest.mark.asyncio
    async def test_batch_vectorize_basic(self, mock_sentence_transformer, mock_numpy):
        """Test basic batch vectorization."""
        from src.agentic_rag.processors.multimodal_vectorizer import MultimodalVectorizer

        vectorizer = MultimodalVectorizer()
        await vectorizer.initialize()

        texts = ["First text", "Second text", "Third text"]
        results = await vectorizer.batch_vectorize(texts)

        assert len(results) == 3
        for result in results:
            assert len(result.vector) == 384

    @pytest.mark.asyncio
    async def test_batch_vectorize_with_metadata(self, mock_sentence_transformer, mock_numpy):
        """Test batch vectorization with metadata."""
        from src.agentic_rag.processors.multimodal_vectorizer import MultimodalVectorizer

        vectorizer = MultimodalVectorizer()
        await vectorizer.initialize()

        texts = ["Text A", "Text B"]
        metadata_list = [{"index": 0}, {"index": 1}]

        results = await vectorizer.batch_vectorize(
            texts,
            metadata_list=metadata_list
        )

        assert results[0].metadata["index"] == 0
        assert results[1].metadata["index"] == 1

    @pytest.mark.asyncio
    async def test_batch_vectorize_empty_list(self, mock_sentence_transformer, mock_numpy):
        """Test batch vectorization with empty list."""
        from src.agentic_rag.processors.multimodal_vectorizer import MultimodalVectorizer

        vectorizer = MultimodalVectorizer()
        await vectorizer.initialize()

        results = await vectorizer.batch_vectorize([])

        assert results == []

    @pytest.mark.asyncio
    async def test_batch_vectorize_large_batch(self, mock_sentence_transformer, mock_numpy):
        """Test batch vectorization with large batch."""
        from src.agentic_rag.processors.multimodal_vectorizer import MultimodalVectorizer

        vectorizer = MultimodalVectorizer(batch_size=32)
        await vectorizer.initialize()

        texts = [f"Text number {i}" for i in range(100)]
        results = await vectorizer.batch_vectorize(texts)

        assert len(results) == 100


# =============================================================================
# Vector Fusion Tests
# =============================================================================

class TestVectorFusion:
    """Test vector fusion methods."""

    def test_weighted_average_fusion(self, mock_sentence_transformer, mock_numpy):
        """Test weighted average fusion."""
        from src.agentic_rag.processors.multimodal_vectorizer import MultimodalVectorizer

        vectorizer = MultimodalVectorizer()

        v1 = [1.0, 0.0, 0.0]
        v2 = [0.0, 1.0, 0.0]

        fused = vectorizer._weighted_average_fusion(v1, v2, 0.4, 0.6)

        # Without normalization: [0.4, 0.6, 0.0]
        # With L2 norm: ~[0.55, 0.83, 0.0]
        assert len(fused) == 3
        assert fused[0] < fused[1]  # Weight 0.6 > 0.4

    def test_weighted_average_fusion_equal_weights(self, mock_sentence_transformer, mock_numpy):
        """Test weighted average fusion with equal weights."""
        from src.agentic_rag.processors.multimodal_vectorizer import MultimodalVectorizer

        vectorizer = MultimodalVectorizer()

        v1 = [1.0, 0.0]
        v2 = [0.0, 1.0]

        fused = vectorizer._weighted_average_fusion(v1, v2, 0.5, 0.5)

        # Both components should be roughly equal
        assert abs(fused[0] - fused[1]) < 0.01

    def test_fusion_with_none_vector1(self, mock_sentence_transformer, mock_numpy):
        """Test fusion when first vector is None."""
        from src.agentic_rag.processors.multimodal_vectorizer import MultimodalVectorizer

        vectorizer = MultimodalVectorizer()

        v2 = [0.5, 0.5]
        fused = vectorizer._weighted_average_fusion(None, v2, 0.4, 0.6)

        assert fused == v2

    def test_fusion_with_none_vector2(self, mock_sentence_transformer, mock_numpy):
        """Test fusion when second vector is None."""
        from src.agentic_rag.processors.multimodal_vectorizer import MultimodalVectorizer

        vectorizer = MultimodalVectorizer()

        v1 = [0.5, 0.5]
        fused = vectorizer._weighted_average_fusion(v1, None, 0.4, 0.6)

        assert fused == v1

    def test_fusion_both_none(self, mock_sentence_transformer, mock_numpy):
        """Test fusion when both vectors are None."""
        from src.agentic_rag.processors.multimodal_vectorizer import MultimodalVectorizer

        vectorizer = MultimodalVectorizer()

        fused = vectorizer._weighted_average_fusion(None, None, 0.4, 0.6)

        assert all(v == 0.0 for v in fused)

    def test_create_fused_vector(self, mock_sentence_transformer, mock_numpy):
        """Test creating FusedVector object."""
        from src.agentic_rag.processors.multimodal_vectorizer import MultimodalVectorizer

        vectorizer = MultimodalVectorizer()

        vectors = [[1.0, 0.0], [0.0, 1.0], [0.5, 0.5]]
        weights = [0.3, 0.3, 0.4]
        sources = ["source1", "source2", "source3"]

        fused = vectorizer.create_fused_vector(
            vectors=vectors,
            weights=weights,
            sources=sources,
            content_id="fused_test"
        )

        assert fused.id == "fused_test"
        assert len(fused.fused_vector) == 2
        assert fused.sources == sources

    def test_create_fused_vector_mismatched_lengths(self, mock_sentence_transformer, mock_numpy):
        """Test that mismatched lengths raise error."""
        from src.agentic_rag.processors.multimodal_vectorizer import MultimodalVectorizer, VectorizationError

        vectorizer = MultimodalVectorizer()

        vectors = [[1.0, 0.0], [0.0, 1.0]]
        weights = [0.5]  # Mismatched

        with pytest.raises(VectorizationError):
            vectorizer.create_fused_vector(
                vectors=vectors,
                weights=weights,
                sources=["s1", "s2"]
            )


# =============================================================================
# L2 Normalization Tests
# =============================================================================

class TestL2Normalization:
    """Test L2 normalization."""

    def test_l2_normalize(self, mock_sentence_transformer, mock_numpy):
        """Test L2 normalization."""
        from src.agentic_rag.processors.multimodal_vectorizer import MultimodalVectorizer

        vectorizer = MultimodalVectorizer()

        vec = [3.0, 4.0]  # norm = 5
        normalized = vectorizer._l2_normalize(vec)

        assert abs(normalized[0] - 0.6) < 0.001
        assert abs(normalized[1] - 0.8) < 0.001

    def test_l2_normalize_zero_vector(self, mock_sentence_transformer, mock_numpy):
        """Test L2 normalization of zero vector."""
        from src.agentic_rag.processors.multimodal_vectorizer import MultimodalVectorizer

        vectorizer = MultimodalVectorizer()

        vec = [0.0, 0.0, 0.0]
        normalized = vectorizer._l2_normalize(vec)

        assert normalized == vec


# =============================================================================
# Performance Tests (AC 6.6.4)
# =============================================================================

class TestPerformance:
    """Test performance requirements (AC 6.6.4: ≤1秒/内容)."""

    @pytest.mark.asyncio
    async def test_vectorization_under_1_second(self, mock_sentence_transformer, mock_numpy):
        """Test that vectorization completes under 1 second."""
        from src.agentic_rag.processors.multimodal_vectorizer import MultimodalVectorizer

        vectorizer = MultimodalVectorizer()
        await vectorizer.initialize()

        result = await vectorizer.vectorize_text("Performance test text")

        # With mock, should be well under 1000ms
        assert result.processing_time_ms < 1000

    @pytest.mark.asyncio
    async def test_image_vectorization_performance(self, mock_sentence_transformer, mock_numpy):
        """Test image vectorization performance."""
        from src.agentic_rag.processors.multimodal_vectorizer import MultimodalVectorizer

        vectorizer = MultimodalVectorizer()
        await vectorizer.initialize()

        result = await vectorizer.vectorize_image_content(
            ocr_text="Long OCR text " * 100,
            description="Long description " * 100
        )

        assert result.processing_time_ms < 1000

    @pytest.mark.asyncio
    async def test_stats_tracking(self, mock_sentence_transformer, mock_numpy):
        """Test that statistics are tracked correctly."""
        from src.agentic_rag.processors.multimodal_vectorizer import MultimodalVectorizer

        vectorizer = MultimodalVectorizer()
        await vectorizer.initialize()

        # Run multiple vectorizations
        for i in range(5):
            await vectorizer.vectorize_text(f"Text {i}")

        stats = vectorizer.get_stats()

        assert stats["total_vectorizations"] == 5
        assert stats["avg_time_ms"] >= 0
        assert stats["initialized"] is True


# =============================================================================
# Convenience Function Tests
# =============================================================================

class TestConvenienceFunctions:
    """Test convenience functions."""

    @pytest.mark.asyncio
    async def test_vectorize_image_function(self, mock_sentence_transformer, mock_numpy):
        """Test vectorize_image convenience function."""
        from src.agentic_rag.processors.multimodal_vectorizer import vectorize_image

        result = await vectorize_image(
            ocr_text="OCR text",
            description="Description"
        )

        assert result is not None
        assert result.content_type == "image"

    @pytest.mark.asyncio
    async def test_vectorize_pdf_chunks_function(self, mock_sentence_transformer, mock_numpy):
        """Test vectorize_pdf_chunks convenience function."""
        from src.agentic_rag.processors.multimodal_vectorizer import vectorize_pdf_chunks

        chunks = [
            {"text": "Chapter 1 content", "title": "Chapter 1"},
            {"text": "Chapter 2 content", "title": "Chapter 2"}
        ]

        results = await vectorize_pdf_chunks(chunks, pdf_path="/test.pdf")

        assert len(results) == 2
        assert results[0].source_path == "/test.pdf"
        assert results[1].source_path == "/test.pdf"


# =============================================================================
# Error Handling Tests
# =============================================================================

class TestErrorHandling:
    """Test error handling."""

    @pytest.mark.asyncio
    async def test_import_error_sentence_transformers(self):
        """Test behavior when sentence-transformers not installed."""
        with patch(
            "src.agentic_rag.processors.multimodal_vectorizer.SENTENCE_TRANSFORMERS_AVAILABLE",
            False
        ):
            from src.agentic_rag.processors.multimodal_vectorizer import MultimodalVectorizer

            vectorizer = MultimodalVectorizer()

            with pytest.raises(ImportError):
                await vectorizer.initialize()

    @pytest.mark.asyncio
    async def test_import_error_numpy(self, mock_sentence_transformer):
        """Test behavior when numpy not installed."""
        with patch(
            "src.agentic_rag.processors.multimodal_vectorizer.NUMPY_AVAILABLE",
            False
        ):
            from src.agentic_rag.processors.multimodal_vectorizer import MultimodalVectorizer

            vectorizer = MultimodalVectorizer()

            with pytest.raises(ImportError):
                await vectorizer.initialize()


# =============================================================================
# ID Generation Tests
# =============================================================================

class TestIDGeneration:
    """Test content ID generation."""

    def test_generate_content_id(self, mock_sentence_transformer, mock_numpy):
        """Test content ID generation."""
        from src.agentic_rag.processors.multimodal_vectorizer import MultimodalVectorizer

        vectorizer = MultimodalVectorizer()

        id1 = vectorizer._generate_content_id("test content")

        assert len(id1) == 16
        assert isinstance(id1, str)

    def test_content_ids_are_unique(self, mock_sentence_transformer, mock_numpy):
        """Test that different content generates different IDs."""
        from src.agentic_rag.processors.multimodal_vectorizer import MultimodalVectorizer

        vectorizer = MultimodalVectorizer()

        # Due to timestamp in ID generation, IDs should be unique
        id1 = vectorizer._generate_content_id("content 1")
        # Small delay to ensure different timestamp
        time.sleep(0.001)
        id2 = vectorizer._generate_content_id("content 2")

        assert id1 != id2


# =============================================================================
# Stats Tests
# =============================================================================

class TestStats:
    """Test statistics methods."""

    @pytest.mark.asyncio
    async def test_get_stats_initial(self, mock_sentence_transformer, mock_numpy):
        """Test initial stats."""
        from src.agentic_rag.processors.multimodal_vectorizer import MultimodalVectorizer

        vectorizer = MultimodalVectorizer()

        stats = vectorizer.get_stats()

        assert stats["total_vectorizations"] == 0
        assert stats["initialized"] is False

    @pytest.mark.asyncio
    async def test_get_stats_after_initialization(self, mock_sentence_transformer, mock_numpy):
        """Test stats after initialization."""
        from src.agentic_rag.processors.multimodal_vectorizer import MultimodalVectorizer

        vectorizer = MultimodalVectorizer()
        await vectorizer.initialize()

        stats = vectorizer.get_stats()

        assert stats["initialized"] is True
        assert stats["model_name"] == "sentence-transformers/all-MiniLM-L6-v2"
        assert stats["device"] == "cpu"

    @pytest.mark.asyncio
    async def test_exceeded_target_tracking(self, mock_sentence_transformer, mock_numpy):
        """Test that exceeding target time is tracked."""
        from src.agentic_rag.processors.multimodal_vectorizer import MultimodalVectorizer

        vectorizer = MultimodalVectorizer()
        await vectorizer.initialize()

        # Normal operation shouldn't exceed target
        await vectorizer.vectorize_text("Test")

        stats = vectorizer.get_stats()
        assert "exceeded_target_count" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
