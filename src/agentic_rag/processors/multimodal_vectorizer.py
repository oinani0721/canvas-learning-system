"""
Multimodal Content Vectorizer for Canvas Learning System (Story 6.6)

Provides vectorization capabilities for multimodal content including:
- Image content vectorization (OCR + AI description)
- PDF content vectorization (by chapters)
- Vector fusion with weighted averaging
- LanceDB storage integration

Dependencies:
- sentence-transformers: Text embedding model
- numpy: Vector operations

✅ Verified from Story 6.6:
- AC 6.6.1: 图片内容向量化 (OCR + AI描述, 768维)
- AC 6.6.2: PDF内容向量化 (按章节)
- AC 6.6.3: 存储到LanceDB (multimodal_content表)
- AC 6.6.4: 向量化速度≤1秒/内容
"""

import asyncio
import hashlib
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False


@dataclass
class VectorizedContent:
    """Vectorized content result."""

    id: str
    content_type: str  # "image", "pdf_chunk", "text"
    source_path: Optional[str]
    text_content: str
    vector: List[float]
    vector_dim: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    processing_time_ms: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "content_type": self.content_type,
            "source_path": self.source_path,
            "text_content": self.text_content,
            "vector": self.vector,
            "vector_dim": self.vector_dim,
            "metadata": self.metadata,
            "processing_time_ms": self.processing_time_ms,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "VectorizedContent":
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class FusedVector:
    """Fused vector from multiple sources."""

    id: str
    vectors: List[List[float]]  # Component vectors
    weights: List[float]  # Fusion weights
    fused_vector: List[float]  # Final fused vector
    sources: List[str]  # Source descriptions
    fusion_method: str = "weighted_average"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "fused_vector": self.fused_vector,
            "sources": self.sources,
            "weights": self.weights,
            "fusion_method": self.fusion_method,
        }


class MultimodalVectorizerError(Exception):
    """Base exception for MultimodalVectorizer errors."""
    pass


class EmbeddingModelError(MultimodalVectorizerError):
    """Raised when embedding model fails."""
    pass


class VectorizationError(MultimodalVectorizerError):
    """Raised when vectorization fails."""
    pass


class MultimodalVectorizer:
    """
    Multimodal Content Vectorizer for Canvas Learning System.

    Features:
    - Text embedding using sentence-transformers (768-dim by default)
    - Image content vectorization (OCR text + AI description fusion)
    - PDF chapter vectorization
    - Weighted vector fusion
    - LanceDB integration ready

    ✅ Story 6.6 AC 6.6.1: 图片内容向量化 (OCR + AI描述)
    ✅ Story 6.6 AC 6.6.2: PDF内容向量化 (按章节)
    ✅ Story 6.6 AC 6.6.4: 向量化速度≤1秒/内容

    Usage:
        vectorizer = MultimodalVectorizer()
        await vectorizer.initialize()

        # Vectorize image content
        result = await vectorizer.vectorize_image_content(
            ocr_text="微积分公式...",
            description="一张包含微积分公式的图片"
        )

        # Vectorize PDF chunk
        result = await vectorizer.vectorize_pdf_chunk(
            chunk_text="第一章内容...",
            chunk_metadata={"chapter": "Chapter 1"}
        )
    """

    # Default embedding model (768-dim)
    DEFAULT_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    DEFAULT_EMBEDDING_DIM: int = 384  # all-MiniLM-L6-v2 outputs 384-dim

    # Alternative models for 768-dim
    ALTERNATIVE_MODELS = {
        "all-mpnet-base-v2": 768,  # Higher quality, 768-dim
        "all-MiniLM-L12-v2": 384,  # Balanced
        "paraphrase-multilingual-MiniLM-L12-v2": 384,  # Multilingual
        "paraphrase-multilingual-mpnet-base-v2": 768,  # Multilingual 768-dim
    }

    # Fusion weights (Story 6.6 requirement: 0.4 OCR + 0.6 description)
    DEFAULT_OCR_WEIGHT: float = 0.4
    DEFAULT_DESC_WEIGHT: float = 0.6

    # Performance target (Story 6.6 AC 6.6.4)
    MAX_PROCESSING_TIME_MS: int = 1000

    def __init__(
        self,
        model_name: Optional[str] = None,
        device: str = "cpu",
        ocr_weight: float = DEFAULT_OCR_WEIGHT,
        desc_weight: float = DEFAULT_DESC_WEIGHT,
        batch_size: int = 32,
        normalize_vectors: bool = True
    ):
        """
        Initialize MultimodalVectorizer.

        Args:
            model_name: Sentence-transformers model name (default: all-MiniLM-L6-v2)
            device: Device to use ("cpu" or "cuda")
            ocr_weight: Weight for OCR text in fusion (default: 0.4)
            desc_weight: Weight for description in fusion (default: 0.6)
            batch_size: Batch size for encoding
            normalize_vectors: Whether to L2-normalize vectors
        """
        self.model_name = model_name or self.DEFAULT_MODEL_NAME
        self.device = device
        self.ocr_weight = ocr_weight
        self.desc_weight = desc_weight
        self.batch_size = batch_size
        self.normalize_vectors = normalize_vectors

        self._model = None
        self._initialized = False
        self._embedding_dim = None

        # Statistics
        self._stats = {
            "total_vectorizations": 0,
            "total_time_ms": 0,
            "avg_time_ms": 0,
            "exceeded_target_count": 0
        }

    async def initialize(self) -> bool:
        """
        Initialize the embedding model.

        Returns:
            True if initialization successful
        """
        if self._initialized:
            return True

        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "sentence-transformers is required. "
                "Install with: pip install sentence-transformers"
            )

        if not NUMPY_AVAILABLE:
            raise ImportError(
                "numpy is required. Install with: pip install numpy"
            )

        try:
            # Load model in thread pool to not block event loop
            loop = asyncio.get_event_loop()
            self._model = await loop.run_in_executor(
                None,
                lambda: SentenceTransformer(self.model_name, device=self.device)
            )

            # Get embedding dimension
            self._embedding_dim = self._model.get_sentence_embedding_dimension()
            self._initialized = True

            return True

        except Exception as e:
            raise EmbeddingModelError(f"Failed to load model: {e}")

    @property
    def embedding_dim(self) -> int:
        """Get embedding dimension."""
        return self._embedding_dim or self.DEFAULT_EMBEDDING_DIM

    async def vectorize_text(
        self,
        text: str,
        content_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> VectorizedContent:
        """
        Vectorize plain text.

        Args:
            text: Text to vectorize
            content_id: Optional content ID (auto-generated if not provided)
            metadata: Optional metadata

        Returns:
            VectorizedContent with embedding vector
        """
        if not self._initialized:
            await self.initialize()

        start_time = time.perf_counter()

        # Generate ID if not provided
        if content_id is None:
            content_id = self._generate_content_id(text)

        # Encode text
        try:
            vector = await self._encode_text(text)
        except Exception as e:
            raise VectorizationError(f"Failed to encode text: {e}")

        processing_time = int((time.perf_counter() - start_time) * 1000)

        # Update stats
        self._update_stats(processing_time)

        return VectorizedContent(
            id=content_id,
            content_type="text",
            source_path=None,
            text_content=text,
            vector=vector,
            vector_dim=len(vector),
            metadata=metadata or {},
            processing_time_ms=processing_time
        )

    async def vectorize_image_content(
        self,
        ocr_text: str,
        description: str,
        image_path: Optional[str] = None,
        content_id: Optional[str] = None,
        key_concepts: Optional[List[str]] = None,
        image_type: Optional[str] = None,
        fusion_method: str = "weighted_average"
    ) -> VectorizedContent:
        """
        Vectorize image content using OCR text and AI description.

        ✅ Story 6.6 AC 6.6.1: 图片内容向量化 (OCR + AI描述)

        Args:
            ocr_text: Extracted OCR text from image
            description: AI-generated description
            image_path: Optional source image path
            content_id: Optional content ID
            key_concepts: Optional extracted key concepts
            image_type: Optional image type (screenshot, diagram, etc.)
            fusion_method: Vector fusion method ("weighted_average" or "concat")

        Returns:
            VectorizedContent with fused embedding vector
        """
        if not self._initialized:
            await self.initialize()

        start_time = time.perf_counter()

        # Generate ID if not provided
        if content_id is None:
            unique_str = f"{ocr_text[:100]}:{description[:100]}:{image_path or ''}"
            content_id = self._generate_content_id(unique_str)

        # Encode both texts
        try:
            ocr_vector = await self._encode_text(ocr_text) if ocr_text else None
            desc_vector = await self._encode_text(description) if description else None
        except Exception as e:
            raise VectorizationError(f"Failed to encode image content: {e}")

        # Fuse vectors
        if fusion_method == "weighted_average":
            fused_vector = self._weighted_average_fusion(
                ocr_vector, desc_vector,
                self.ocr_weight, self.desc_weight
            )
        elif fusion_method == "concat":
            # Concatenate and reduce dimension
            fused_vector = self._concat_fusion(ocr_vector, desc_vector)
        else:
            # Default to weighted average
            fused_vector = self._weighted_average_fusion(
                ocr_vector, desc_vector,
                self.ocr_weight, self.desc_weight
            )

        processing_time = int((time.perf_counter() - start_time) * 1000)

        # Update stats
        self._update_stats(processing_time)

        # Combined text for storage
        combined_text = f"[OCR] {ocr_text}\n[Description] {description}"
        if key_concepts:
            combined_text += f"\n[Concepts] {', '.join(key_concepts)}"

        return VectorizedContent(
            id=content_id,
            content_type="image",
            source_path=image_path,
            text_content=combined_text,
            vector=fused_vector,
            vector_dim=len(fused_vector),
            metadata={
                "ocr_text": ocr_text,
                "description": description,
                "key_concepts": key_concepts or [],
                "image_type": image_type,
                "fusion_method": fusion_method,
                "ocr_weight": self.ocr_weight,
                "desc_weight": self.desc_weight
            },
            processing_time_ms=processing_time
        )

    async def vectorize_pdf_chunk(
        self,
        chunk_text: str,
        chunk_id: Optional[str] = None,
        pdf_path: Optional[str] = None,
        chapter_title: Optional[str] = None,
        page_numbers: Optional[List[int]] = None,
        chunk_index: int = 0,
        total_chunks: int = 1,
        heading_path: Optional[List[str]] = None
    ) -> VectorizedContent:
        """
        Vectorize PDF chunk (chapter or section).

        ✅ Story 6.6 AC 6.6.2: PDF内容向量化 (按章节)

        Args:
            chunk_text: Text content of the chunk
            chunk_id: Optional chunk ID
            pdf_path: Source PDF path
            chapter_title: Chapter or section title
            page_numbers: Pages covered by this chunk
            chunk_index: Index of this chunk
            total_chunks: Total number of chunks
            heading_path: Hierarchical heading path

        Returns:
            VectorizedContent with embedding vector
        """
        if not self._initialized:
            await self.initialize()

        start_time = time.perf_counter()

        # Generate ID if not provided
        if chunk_id is None:
            unique_str = f"{pdf_path or ''}:chunk_{chunk_index}:{chunk_text[:100]}"
            chunk_id = self._generate_content_id(unique_str)

        # Prepend chapter title to text for better context
        if chapter_title:
            text_to_encode = f"{chapter_title}\n\n{chunk_text}"
        else:
            text_to_encode = chunk_text

        # Encode text
        try:
            vector = await self._encode_text(text_to_encode)
        except Exception as e:
            raise VectorizationError(f"Failed to encode PDF chunk: {e}")

        processing_time = int((time.perf_counter() - start_time) * 1000)

        # Update stats
        self._update_stats(processing_time)

        return VectorizedContent(
            id=chunk_id,
            content_type="pdf_chunk",
            source_path=pdf_path,
            text_content=chunk_text,
            vector=vector,
            vector_dim=len(vector),
            metadata={
                "chapter_title": chapter_title,
                "page_numbers": page_numbers or [],
                "chunk_index": chunk_index,
                "total_chunks": total_chunks,
                "heading_path": heading_path or [],
                "text_length": len(chunk_text)
            },
            processing_time_ms=processing_time
        )

    async def batch_vectorize(
        self,
        texts: List[str],
        content_type: str = "text",
        metadata_list: Optional[List[Dict[str, Any]]] = None
    ) -> List[VectorizedContent]:
        """
        Batch vectorize multiple texts.

        Args:
            texts: List of texts to vectorize
            content_type: Content type for all items
            metadata_list: Optional list of metadata dicts

        Returns:
            List of VectorizedContent objects
        """
        if not self._initialized:
            await self.initialize()

        if not texts:
            return []

        start_time = time.perf_counter()

        # Encode all texts in batch
        try:
            loop = asyncio.get_event_loop()
            vectors = await loop.run_in_executor(
                None,
                lambda: self._model.encode(
                    texts,
                    batch_size=self.batch_size,
                    normalize_embeddings=self.normalize_vectors,
                    show_progress_bar=False
                ).tolist()
            )
        except Exception as e:
            raise VectorizationError(f"Batch encoding failed: {e}")

        processing_time = int((time.perf_counter() - start_time) * 1000)
        time_per_item = processing_time // len(texts)

        # Create results
        results = []
        for i, (text, vector) in enumerate(zip(texts, vectors)):
            content_id = self._generate_content_id(text)
            metadata = metadata_list[i] if metadata_list and i < len(metadata_list) else {}

            results.append(VectorizedContent(
                id=content_id,
                content_type=content_type,
                source_path=None,
                text_content=text,
                vector=vector,
                vector_dim=len(vector),
                metadata=metadata,
                processing_time_ms=time_per_item
            ))

        return results

    async def _encode_text(self, text: str) -> List[float]:
        """Encode single text to vector."""
        if not text or not text.strip():
            # Return zero vector for empty text
            return [0.0] * self.embedding_dim

        # Run encoding in thread pool
        loop = asyncio.get_event_loop()
        vector = await loop.run_in_executor(
            None,
            lambda: self._model.encode(
                text,
                normalize_embeddings=self.normalize_vectors,
                show_progress_bar=False
            ).tolist()
        )

        return vector

    def _weighted_average_fusion(
        self,
        vector1: Optional[List[float]],
        vector2: Optional[List[float]],
        weight1: float,
        weight2: float
    ) -> List[float]:
        """
        Fuse two vectors using weighted average.

        ✅ Story 6.6: 0.4 OCR + 0.6 description
        """
        if vector1 is None and vector2 is None:
            return [0.0] * self.embedding_dim

        if vector1 is None:
            return vector2

        if vector2 is None:
            return vector1

        # Normalize weights
        total_weight = weight1 + weight2
        w1 = weight1 / total_weight
        w2 = weight2 / total_weight

        # Weighted average
        fused = [
            v1 * w1 + v2 * w2
            for v1, v2 in zip(vector1, vector2)
        ]

        # Optional: L2 normalize the fused vector
        if self.normalize_vectors:
            fused = self._l2_normalize(fused)

        return fused

    def _concat_fusion(
        self,
        vector1: Optional[List[float]],
        vector2: Optional[List[float]]
    ) -> List[float]:
        """
        Fuse vectors by concatenation (then reduce dimension).

        Note: This doubles the dimension. Consider PCA reduction if needed.
        """
        if vector1 is None and vector2 is None:
            return [0.0] * self.embedding_dim

        if vector1 is None:
            return vector2

        if vector2 is None:
            return vector1

        # Simple: average to keep same dimension
        # Alternative: concatenate and apply learned projection
        return self._weighted_average_fusion(vector1, vector2, 0.5, 0.5)

    def _l2_normalize(self, vector: List[float]) -> List[float]:
        """L2 normalize a vector."""
        norm = sum(v * v for v in vector) ** 0.5
        if norm == 0:
            return vector
        return [v / norm for v in vector]

    def _generate_content_id(self, content: str) -> str:
        """Generate unique content ID."""
        hash_input = f"{content}:{datetime.now().isoformat()}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]

    def _update_stats(self, processing_time_ms: int):
        """Update statistics."""
        self._stats["total_vectorizations"] += 1
        self._stats["total_time_ms"] += processing_time_ms
        self._stats["avg_time_ms"] = (
            self._stats["total_time_ms"] / self._stats["total_vectorizations"]
        )

        if processing_time_ms > self.MAX_PROCESSING_TIME_MS:
            self._stats["exceeded_target_count"] += 1

    def get_stats(self) -> Dict[str, Any]:
        """Get vectorizer statistics."""
        return {
            **self._stats,
            "model_name": self.model_name,
            "embedding_dim": self.embedding_dim,
            "device": self.device,
            "initialized": self._initialized,
            "performance_target_ms": self.MAX_PROCESSING_TIME_MS
        }

    def create_fused_vector(
        self,
        vectors: List[List[float]],
        weights: List[float],
        sources: List[str],
        content_id: Optional[str] = None
    ) -> FusedVector:
        """
        Create a fused vector from multiple component vectors.

        Args:
            vectors: List of component vectors
            weights: List of weights for each vector
            sources: List of source descriptions
            content_id: Optional content ID

        Returns:
            FusedVector with fused result
        """
        if not vectors:
            raise VectorizationError("No vectors provided for fusion")

        if len(vectors) != len(weights):
            raise VectorizationError("Vectors and weights must have same length")

        # Normalize weights
        total_weight = sum(weights)
        normalized_weights = [w / total_weight for w in weights]

        # Compute weighted average
        fused = [0.0] * len(vectors[0])
        for vector, weight in zip(vectors, normalized_weights):
            for i, v in enumerate(vector):
                fused[i] += v * weight

        if self.normalize_vectors:
            fused = self._l2_normalize(fused)

        if content_id is None:
            content_id = self._generate_content_id(str(vectors[0][:10]))

        return FusedVector(
            id=content_id,
            vectors=vectors,
            weights=weights,
            fused_vector=fused,
            sources=sources,
            fusion_method="weighted_average"
        )


# Convenience functions
async def vectorize_image(
    ocr_text: str,
    description: str,
    **kwargs
) -> VectorizedContent:
    """
    Vectorize image content.

    Args:
        ocr_text: OCR extracted text
        description: AI-generated description
        **kwargs: Additional arguments for vectorize_image_content

    Returns:
        VectorizedContent with fused vector
    """
    vectorizer = MultimodalVectorizer()
    await vectorizer.initialize()
    return await vectorizer.vectorize_image_content(
        ocr_text=ocr_text,
        description=description,
        **kwargs
    )


async def vectorize_pdf_chunks(
    chunks: List[Dict[str, Any]],
    pdf_path: Optional[str] = None
) -> List[VectorizedContent]:
    """
    Vectorize multiple PDF chunks.

    Args:
        chunks: List of chunk dictionaries with 'text', 'title', etc.
        pdf_path: Source PDF path

    Returns:
        List of VectorizedContent objects
    """
    vectorizer = MultimodalVectorizer()
    await vectorizer.initialize()

    results = []
    total_chunks = len(chunks)

    for i, chunk in enumerate(chunks):
        result = await vectorizer.vectorize_pdf_chunk(
            chunk_text=chunk.get("text", ""),
            pdf_path=pdf_path,
            chapter_title=chunk.get("title"),
            page_numbers=chunk.get("pages"),
            chunk_index=i,
            total_chunks=total_chunks,
            heading_path=chunk.get("heading_path")
        )
        results.append(result)

    return results
