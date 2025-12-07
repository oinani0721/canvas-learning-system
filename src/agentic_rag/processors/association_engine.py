"""
Association Engine for Canvas Learning System (Story 6.7)

Provides automatic multi-modal association capabilities:
- Concept-media similarity calculation
- Top-K recommendation for each concept
- Neo4j relationship creation
- Configurable similarity threshold

Dependencies:
- LanceDB: Vector storage and similarity search
- GraphitiClient: Knowledge graph relationships
- NumPy: Vector operations

Verified from:
- Story 6.7 (AC 6.7.1): 概念-资料相似度计算
- Story 6.7 (AC 6.7.2): 自动关联推荐
- Story 6.7 (AC 6.7.3): 建立Neo4j关系
- Story 6.7 (AC 6.7.4): 推荐延迟≤500ms
"""

import asyncio
import hashlib
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Protocol, Tuple, Union

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


# ============================================================
# Error Definitions
# ============================================================

class AssociationEngineError(Exception):
    """Base exception for association engine errors."""
    pass


class SimilarityCalculationError(AssociationEngineError):
    """Raised when similarity calculation fails."""
    pass


class RecommendationError(AssociationEngineError):
    """Raised when recommendation fails."""
    pass


class RelationCreationError(AssociationEngineError):
    """Raised when Neo4j relation creation fails."""
    pass


# ============================================================
# Enums and Constants
# ============================================================

class SimilarityMetric(str, Enum):
    """Similarity metric options."""
    COSINE = "cosine"
    EUCLIDEAN = "euclidean"
    DOT_PRODUCT = "dot_product"


class MediaType(str, Enum):
    """Media type options."""
    IMAGE = "image"
    PDF = "pdf"
    PDF_CHUNK = "pdf_chunk"
    UNKNOWN = "unknown"


# Default configuration
DEFAULT_SIMILARITY_THRESHOLD = 0.7
DEFAULT_TOP_K = 5
DEFAULT_RECOMMENDATION_TIMEOUT_MS = 500
DEFAULT_CACHE_SIZE = 100
DEFAULT_BATCH_SIZE = 10


# ============================================================
# Data Classes
# ============================================================

@dataclass
class MediaRecommendation:
    """
    Media recommendation result.

    Verified from Story 6.7 (AC 6.7.2): 自动关联推荐
    """
    media_id: str
    media_type: str
    file_path: str
    similarity_score: float
    description: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "media_id": self.media_id,
            "media_type": self.media_type,
            "file_path": self.file_path,
            "similarity_score": self.similarity_score,
            "description": self.description,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MediaRecommendation":
        """Create from dictionary."""
        return cls(
            media_id=data.get("media_id", ""),
            media_type=data.get("media_type", MediaType.UNKNOWN.value),
            file_path=data.get("file_path", ""),
            similarity_score=data.get("similarity_score", 0.0),
            description=data.get("description"),
            metadata=data.get("metadata", {})
        )


@dataclass
class AssociationResult:
    """
    Result of concept-media association.

    Verified from Story 6.7 (AC 6.7.3): 建立Neo4j关系
    """
    concept_id: str
    concept_name: str
    recommendations: List[MediaRecommendation] = field(default_factory=list)
    created_relations: int = 0
    processing_time_ms: int = 0
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "concept_id": self.concept_id,
            "concept_name": self.concept_name,
            "recommendations": [r.to_dict() for r in self.recommendations],
            "created_relations": self.created_relations,
            "processing_time_ms": self.processing_time_ms,
            "error": self.error
        }


@dataclass
class AssociationStats:
    """Statistics for association operations."""
    total_concepts_processed: int = 0
    total_recommendations: int = 0
    total_relations_created: int = 0
    average_similarity_score: float = 0.0
    average_processing_time_ms: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_concepts_processed": self.total_concepts_processed,
            "total_recommendations": self.total_recommendations,
            "total_relations_created": self.total_relations_created,
            "average_similarity_score": self.average_similarity_score,
            "average_processing_time_ms": self.average_processing_time_ms,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses
        }


# ============================================================
# Protocol Definitions (for type hints)
# ============================================================

class LanceDBClientProtocol(Protocol):
    """Protocol for LanceDB client."""

    async def search(
        self,
        query: Union[str, List[float]],
        table_name: str,
        num_results: int,
        metric: str
    ) -> List[Dict[str, Any]]:
        ...

    async def initialize(self) -> bool:
        ...


class GraphitiClientProtocol(Protocol):
    """Protocol for Graphiti client."""

    async def add_relationship(
        self,
        entity1: str,
        entity2: str,
        relationship_type: str
    ) -> bool:
        ...

    async def initialize(self) -> bool:
        ...


# ============================================================
# Association Engine Implementation
# ============================================================

class AssociationEngine:
    """
    Multi-modal Auto Association Engine.

    Provides automatic association between concepts and media content
    using vector similarity search and knowledge graph relationships.

    Verified from Story 6.7:
    - AC 6.7.1: 概念-资料相似度计算 (cosine similarity)
    - AC 6.7.2: 自动关联推荐 (Top-K)
    - AC 6.7.3: 建立Neo4j关系 (HAS_MEDIA)
    - AC 6.7.4: 推荐延迟≤500ms

    Usage:
        engine = AssociationEngine(lancedb_client, graphiti_client)
        recommendations = await engine.recommend_media_for_concept(
            concept_id="concept_123",
            concept_vector=[0.1, 0.2, ...]
        )
    """

    # Configuration
    MULTIMODAL_TABLE = "multimodal_content"
    HAS_MEDIA_RELATION = "HAS_MEDIA"

    def __init__(
        self,
        lancedb_client: Optional[LanceDBClientProtocol] = None,
        graphiti_client: Optional[GraphitiClientProtocol] = None,
        similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
        top_k: int = DEFAULT_TOP_K,
        timeout_ms: int = DEFAULT_RECOMMENDATION_TIMEOUT_MS,
        metric: SimilarityMetric = SimilarityMetric.COSINE,
        enable_cache: bool = True,
        cache_size: int = DEFAULT_CACHE_SIZE
    ):
        """
        Initialize Association Engine.

        Args:
            lancedb_client: LanceDB client for vector search
            graphiti_client: Graphiti client for relationship creation
            similarity_threshold: Minimum similarity for recommendations (0-1)
            top_k: Maximum number of recommendations
            timeout_ms: Recommendation timeout in milliseconds
            metric: Similarity metric to use
            enable_cache: Enable result caching
            cache_size: Maximum cache entries
        """
        self.lancedb = lancedb_client
        self.graphiti = graphiti_client
        self.threshold = similarity_threshold
        self.top_k = top_k
        self.timeout_ms = timeout_ms
        self.metric = metric
        self.enable_cache = enable_cache
        self.cache_size = cache_size

        # Internal state
        self._cache: Dict[str, Tuple[List[MediaRecommendation], float]] = {}
        self._stats = AssociationStats()
        self._initialized = False

    async def initialize(self) -> bool:
        """
        Initialize the engine and its dependencies.

        Returns:
            True if initialization successful
        """
        if self._initialized:
            return True

        try:
            # Initialize LanceDB client
            if self.lancedb is not None:
                await self.lancedb.initialize()

            # Initialize Graphiti client
            if self.graphiti is not None:
                await self.graphiti.initialize()

            self._initialized = True
            return True

        except Exception as e:
            raise AssociationEngineError(f"Initialization failed: {e}")

    # ============================================================
    # Similarity Calculation (AC 6.7.1)
    # ============================================================

    def calculate_similarity(
        self,
        vector1: List[float],
        vector2: List[float],
        metric: Optional[SimilarityMetric] = None
    ) -> float:
        """
        Calculate similarity between two vectors.

        Verified from Story 6.7 (AC 6.7.1): 概念-资料相似度计算

        Args:
            vector1: First vector
            vector2: Second vector
            metric: Similarity metric (default: engine's metric)

        Returns:
            Similarity score (0-1 for cosine, varies for others)

        Raises:
            SimilarityCalculationError: If calculation fails
        """
        if not NUMPY_AVAILABLE:
            return self._calculate_similarity_pure_python(
                vector1, vector2, metric or self.metric
            )

        try:
            v1 = np.array(vector1)
            v2 = np.array(vector2)

            if v1.shape != v2.shape:
                raise SimilarityCalculationError(
                    f"Vector dimension mismatch: {v1.shape} vs {v2.shape}"
                )

            metric = metric or self.metric

            if metric == SimilarityMetric.COSINE:
                # Cosine similarity = dot(a, b) / (norm(a) * norm(b))
                norm1 = np.linalg.norm(v1)
                norm2 = np.linalg.norm(v2)

                if norm1 == 0 or norm2 == 0:
                    return 0.0

                similarity = np.dot(v1, v2) / (norm1 * norm2)
                return float(similarity)

            elif metric == SimilarityMetric.EUCLIDEAN:
                # Convert Euclidean distance to similarity
                # similarity = 1 / (1 + distance)
                distance = np.linalg.norm(v1 - v2)
                return float(1.0 / (1.0 + distance))

            elif metric == SimilarityMetric.DOT_PRODUCT:
                return float(np.dot(v1, v2))

            else:
                raise SimilarityCalculationError(f"Unknown metric: {metric}")

        except Exception as e:
            if isinstance(e, SimilarityCalculationError):
                raise
            raise SimilarityCalculationError(f"Similarity calculation failed: {e}")

    def _calculate_similarity_pure_python(
        self,
        vector1: List[float],
        vector2: List[float],
        metric: SimilarityMetric
    ) -> float:
        """Pure Python fallback for similarity calculation."""
        if len(vector1) != len(vector2):
            raise SimilarityCalculationError(
                f"Vector dimension mismatch: {len(vector1)} vs {len(vector2)}"
            )

        if metric == SimilarityMetric.COSINE:
            dot_product = sum(a * b for a, b in zip(vector1, vector2))
            norm1 = sum(a * a for a in vector1) ** 0.5
            norm2 = sum(b * b for b in vector2) ** 0.5

            if norm1 == 0 or norm2 == 0:
                return 0.0

            return dot_product / (norm1 * norm2)

        elif metric == SimilarityMetric.EUCLIDEAN:
            distance = sum((a - b) ** 2 for a, b in zip(vector1, vector2)) ** 0.5
            return 1.0 / (1.0 + distance)

        elif metric == SimilarityMetric.DOT_PRODUCT:
            return sum(a * b for a, b in zip(vector1, vector2))

        else:
            raise SimilarityCalculationError(f"Unknown metric: {metric}")

    # ============================================================
    # Media Recommendation (AC 6.7.2)
    # ============================================================

    async def recommend_media_for_concept(
        self,
        concept_id: str,
        concept_vector: List[float],
        concept_name: Optional[str] = None,
        filter_existing: bool = True,
        existing_media_ids: Optional[List[str]] = None
    ) -> List[MediaRecommendation]:
        """
        Recommend media for a concept based on vector similarity.

        Verified from Story 6.7 (AC 6.7.2): 自动关联推荐
        Verified from Story 6.7 (AC 6.7.4): 推荐延迟≤500ms

        Args:
            concept_id: Concept identifier
            concept_vector: Concept embedding vector
            concept_name: Optional concept name for caching
            filter_existing: Whether to filter already associated media
            existing_media_ids: List of already associated media IDs

        Returns:
            List of MediaRecommendation sorted by similarity

        Raises:
            RecommendationError: If recommendation fails
        """
        start_time = time.perf_counter()

        if not self._initialized:
            await self.initialize()

        # Check cache
        cache_key = self._get_cache_key(concept_id, concept_vector)
        if self.enable_cache and cache_key in self._cache:
            cached_result, cached_time = self._cache[cache_key]
            # Cache valid for 5 minutes
            if time.time() - cached_time < 300:
                self._stats.cache_hits += 1
                return cached_result

        self._stats.cache_misses += 1

        try:
            # Set timeout for the operation
            timeout_seconds = self.timeout_ms / 1000.0

            recommendations = await asyncio.wait_for(
                self._recommend_internal(
                    concept_id=concept_id,
                    concept_vector=concept_vector,
                    filter_existing=filter_existing,
                    existing_media_ids=existing_media_ids
                ),
                timeout=timeout_seconds
            )

            # Update cache
            if self.enable_cache:
                self._update_cache(cache_key, recommendations)

            # Update stats
            processing_time = (time.perf_counter() - start_time) * 1000
            self._update_stats(recommendations, processing_time)

            return recommendations

        except asyncio.TimeoutError:
            raise RecommendationError(
                f"Recommendation timeout ({self.timeout_ms}ms) for concept {concept_id}"
            )
        except Exception as e:
            if isinstance(e, RecommendationError):
                raise
            raise RecommendationError(f"Recommendation failed: {e}")

    async def _recommend_internal(
        self,
        concept_id: str,
        concept_vector: List[float],
        filter_existing: bool,
        existing_media_ids: Optional[List[str]]
    ) -> List[MediaRecommendation]:
        """Internal recommendation implementation."""
        recommendations = []

        # If no LanceDB client, return empty
        if self.lancedb is None:
            return recommendations

        # Perform vector similarity search
        # Get more results than needed for filtering
        search_results = await self.lancedb.search(
            query=concept_vector,
            table_name=self.MULTIMODAL_TABLE,
            num_results=self.top_k * 2,  # Get extra for filtering
            metric=self.metric.value
        )

        # Convert results to recommendations
        existing_set = set(existing_media_ids or [])

        for result in search_results:
            # Get similarity score
            # LanceDB returns distance, convert to similarity
            distance = result.get("_distance") or result.get("distance") or 0.0

            # For cosine metric, LanceDB returns cosine distance (1 - similarity)
            # We need to convert back to similarity
            if self.metric == SimilarityMetric.COSINE:
                similarity = 1.0 - distance
            else:
                # For other metrics, use the score directly or convert
                similarity = result.get("score", 1.0 / (1.0 + distance))

            # Filter by threshold
            if similarity < self.threshold:
                continue

            # Get media ID
            media_id = (
                result.get("id") or
                result.get("doc_id") or
                result.get("content_id") or
                ""
            )

            # Filter existing associations
            if filter_existing and media_id in existing_set:
                continue

            # Create recommendation
            rec = MediaRecommendation(
                media_id=media_id,
                media_type=result.get("media_type", MediaType.UNKNOWN.value),
                file_path=result.get("file_path", ""),
                similarity_score=similarity,
                description=result.get("description"),
                metadata={
                    "content": result.get("content", ""),
                    "key_concepts": result.get("key_concepts", []),
                    "vector_id": result.get("vector_id", ""),
                }
            )

            recommendations.append(rec)

            # Stop if we have enough
            if len(recommendations) >= self.top_k:
                break

        # Sort by similarity (highest first)
        recommendations.sort(key=lambda x: x.similarity_score, reverse=True)

        return recommendations

    async def batch_recommend(
        self,
        concepts: List[Tuple[str, List[float], Optional[str]]],  # (id, vector, name)
        max_concurrent: int = DEFAULT_BATCH_SIZE,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[AssociationResult]:
        """
        Batch recommend media for multiple concepts.

        Args:
            concepts: List of (concept_id, concept_vector, concept_name) tuples
            max_concurrent: Maximum concurrent recommendations
            progress_callback: Optional callback(current, total)

        Returns:
            List of AssociationResult for each concept
        """
        results = []
        semaphore = asyncio.Semaphore(max_concurrent)

        async def recommend_with_semaphore(
            idx: int,
            concept_id: str,
            concept_vector: List[float],
            concept_name: Optional[str]
        ) -> AssociationResult:
            async with semaphore:
                start_time = time.perf_counter()

                try:
                    recommendations = await self.recommend_media_for_concept(
                        concept_id=concept_id,
                        concept_vector=concept_vector,
                        concept_name=concept_name
                    )

                    processing_time = int((time.perf_counter() - start_time) * 1000)

                    result = AssociationResult(
                        concept_id=concept_id,
                        concept_name=concept_name or concept_id,
                        recommendations=recommendations,
                        processing_time_ms=processing_time
                    )

                except Exception as e:
                    result = AssociationResult(
                        concept_id=concept_id,
                        concept_name=concept_name or concept_id,
                        error=str(e)
                    )

                if progress_callback:
                    progress_callback(idx + 1, len(concepts))

                return result

        tasks = [
            recommend_with_semaphore(idx, cid, cvec, cname)
            for idx, (cid, cvec, cname) in enumerate(concepts)
        ]

        results = await asyncio.gather(*tasks)
        return list(results)

    # ============================================================
    # Relationship Creation (AC 6.7.3)
    # ============================================================

    async def create_associations(
        self,
        concept_id: str,
        recommendations: List[MediaRecommendation]
    ) -> int:
        """
        Create Neo4j relationships for recommendations.

        Verified from Story 6.7 (AC 6.7.3): 建立Neo4j关系

        Args:
            concept_id: Concept identifier
            recommendations: List of media recommendations

        Returns:
            Number of relationships created

        Raises:
            RelationCreationError: If relation creation fails
        """
        if self.graphiti is None:
            return 0

        if not self._initialized:
            await self.initialize()

        created_count = 0

        for rec in recommendations:
            try:
                success = await self.graphiti.add_relationship(
                    entity1=concept_id,
                    entity2=rec.media_id,
                    relationship_type=self.HAS_MEDIA_RELATION
                )

                if success:
                    created_count += 1

            except Exception:
                # Log but don't fail the whole batch
                pass

        self._stats.total_relations_created += created_count

        return created_count

    async def batch_create_associations(
        self,
        association_results: List[AssociationResult]
    ) -> int:
        """
        Batch create Neo4j relationships for multiple concepts.

        Args:
            association_results: List of AssociationResult from recommendations

        Returns:
            Total number of relationships created
        """
        total_created = 0

        for result in association_results:
            if result.recommendations:
                created = await self.create_associations(
                    concept_id=result.concept_id,
                    recommendations=result.recommendations
                )
                result.created_relations = created
                total_created += created

        return total_created

    # ============================================================
    # Full Pipeline
    # ============================================================

    async def process_concept(
        self,
        concept_id: str,
        concept_vector: List[float],
        concept_name: Optional[str] = None,
        create_relations: bool = True
    ) -> AssociationResult:
        """
        Full pipeline: recommend media and create relationships.

        Args:
            concept_id: Concept identifier
            concept_vector: Concept embedding vector
            concept_name: Optional concept name
            create_relations: Whether to create Neo4j relationships

        Returns:
            AssociationResult with recommendations and created relations
        """
        start_time = time.perf_counter()

        try:
            # Get recommendations
            recommendations = await self.recommend_media_for_concept(
                concept_id=concept_id,
                concept_vector=concept_vector,
                concept_name=concept_name
            )

            # Create relationships if requested
            created_count = 0
            if create_relations and recommendations:
                created_count = await self.create_associations(
                    concept_id=concept_id,
                    recommendations=recommendations
                )

            processing_time = int((time.perf_counter() - start_time) * 1000)

            return AssociationResult(
                concept_id=concept_id,
                concept_name=concept_name or concept_id,
                recommendations=recommendations,
                created_relations=created_count,
                processing_time_ms=processing_time
            )

        except Exception as e:
            return AssociationResult(
                concept_id=concept_id,
                concept_name=concept_name or concept_id,
                error=str(e)
            )

    # ============================================================
    # Cache Management
    # ============================================================

    def _get_cache_key(
        self,
        concept_id: str,
        concept_vector: List[float]
    ) -> str:
        """Generate cache key from concept ID and vector."""
        # Use first 8 elements of vector for key (for efficiency)
        vector_hash = hashlib.md5(
            str(concept_vector[:8]).encode()
        ).hexdigest()[:8]
        return f"{concept_id}_{vector_hash}"

    def _update_cache(
        self,
        key: str,
        recommendations: List[MediaRecommendation]
    ) -> None:
        """Update cache with new recommendations."""
        # Evict old entries if cache is full
        if len(self._cache) >= self.cache_size:
            # Remove oldest entry (simple FIFO)
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]

        self._cache[key] = (recommendations, time.time())

    def clear_cache(self) -> int:
        """
        Clear the recommendation cache.

        Returns:
            Number of entries cleared
        """
        count = len(self._cache)
        self._cache.clear()
        return count

    # ============================================================
    # Statistics
    # ============================================================

    def _update_stats(
        self,
        recommendations: List[MediaRecommendation],
        processing_time_ms: float
    ) -> None:
        """Update statistics after a recommendation."""
        self._stats.total_concepts_processed += 1
        self._stats.total_recommendations += len(recommendations)

        # Update average similarity
        if recommendations:
            avg_sim = sum(r.similarity_score for r in recommendations) / len(recommendations)
            n = self._stats.total_concepts_processed
            old_avg = self._stats.average_similarity_score
            self._stats.average_similarity_score = (old_avg * (n - 1) + avg_sim) / n

        # Update average processing time
        n = self._stats.total_concepts_processed
        old_avg = self._stats.average_processing_time_ms
        self._stats.average_processing_time_ms = (
            old_avg * (n - 1) + processing_time_ms
        ) / n

    def get_stats(self) -> Dict[str, Any]:
        """
        Get engine statistics.

        Returns:
            Statistics dictionary
        """
        return {
            "initialized": self._initialized,
            "similarity_threshold": self.threshold,
            "top_k": self.top_k,
            "timeout_ms": self.timeout_ms,
            "metric": self.metric.value,
            "cache_enabled": self.enable_cache,
            "cache_size": len(self._cache),
            "max_cache_size": self.cache_size,
            **self._stats.to_dict()
        }

    def reset_stats(self) -> None:
        """Reset statistics."""
        self._stats = AssociationStats()


# ============================================================
# Convenience Functions
# ============================================================

async def recommend_media(
    concept_vector: List[float],
    lancedb_client: LanceDBClientProtocol,
    similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
    top_k: int = DEFAULT_TOP_K,
    **kwargs
) -> List[MediaRecommendation]:
    """
    Convenience function to recommend media for a concept.

    Args:
        concept_vector: Concept embedding vector
        lancedb_client: LanceDB client instance
        similarity_threshold: Minimum similarity threshold
        top_k: Maximum number of recommendations
        **kwargs: Additional arguments for AssociationEngine

    Returns:
        List of MediaRecommendation
    """
    engine = AssociationEngine(
        lancedb_client=lancedb_client,
        similarity_threshold=similarity_threshold,
        top_k=top_k,
        **kwargs
    )

    # Generate a temporary concept ID
    concept_id = f"temp_{hashlib.md5(str(concept_vector[:8]).encode()).hexdigest()[:8]}"

    return await engine.recommend_media_for_concept(
        concept_id=concept_id,
        concept_vector=concept_vector
    )


def cosine_similarity(vector1: List[float], vector2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors.

    Args:
        vector1: First vector
        vector2: Second vector

    Returns:
        Cosine similarity (-1 to 1, higher is more similar)
    """
    engine = AssociationEngine()
    return engine.calculate_similarity(
        vector1, vector2,
        metric=SimilarityMetric.COSINE
    )


def euclidean_similarity(vector1: List[float], vector2: List[float]) -> float:
    """
    Calculate Euclidean similarity between two vectors.

    Args:
        vector1: First vector
        vector2: Second vector

    Returns:
        Euclidean similarity (0 to 1, higher is more similar)
    """
    engine = AssociationEngine()
    return engine.calculate_similarity(
        vector1, vector2,
        metric=SimilarityMetric.EUCLIDEAN
    )
