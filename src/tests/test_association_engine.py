"""
Tests for Association Engine (Story 6.7)

Covers:
- AC 6.7.1: Concept-media similarity calculation (cosine, euclidean, dot product)
- AC 6.7.2: Auto association recommendation (Top-K, filter existing)
- AC 6.7.3: Neo4j relationship creation (HAS_MEDIA)
- AC 6.7.4: Recommendation latency ≤500ms

Test Categories:
1. Unit Tests - Similarity calculation
2. Unit Tests - MediaRecommendation dataclass
3. Unit Tests - AssociationResult dataclass
4. Integration Tests - LanceDB search
5. Integration Tests - Neo4j relationship creation
6. Performance Tests - Latency requirements
7. Edge Cases - Error handling
"""

import asyncio
import math
import time
from unittest.mock import AsyncMock

import pytest
from src.agentic_rag.processors.association_engine import (
    DEFAULT_SIMILARITY_THRESHOLD,
    DEFAULT_TOP_K,
    AssociationEngine,
    AssociationEngineError,
    AssociationResult,
    AssociationStats,
    MediaRecommendation,
    MediaType,
    RecommendationError,
    SimilarityCalculationError,
    SimilarityMetric,
    cosine_similarity,
    euclidean_similarity,
    recommend_media,
)

# ============================================================
# Test Fixtures
# ============================================================


@pytest.fixture
def sample_vectors():
    """Sample vectors for testing."""
    return {
        "v1": [1.0, 0.0, 0.0],  # Unit vector in x direction
        "v2": [0.0, 1.0, 0.0],  # Unit vector in y direction
        "v3": [1.0, 1.0, 0.0],  # 45 degrees between x and y
        "v4": [1.0, 0.0, 0.0],  # Same as v1
        "v5": [-1.0, 0.0, 0.0],  # Opposite of v1
        "zero": [0.0, 0.0, 0.0],  # Zero vector
        "high_dim": [0.1] * 768,  # High dimensional vector
    }


@pytest.fixture
def sample_recommendations():
    """Sample media recommendations."""
    return [
        MediaRecommendation(
            media_id="media_1",
            media_type=MediaType.IMAGE.value,
            file_path="/path/to/image1.png",
            similarity_score=0.95,
            description="Test image 1",
            metadata={"key_concepts": ["concept1"]}
        ),
        MediaRecommendation(
            media_id="media_2",
            media_type=MediaType.PDF.value,
            file_path="/path/to/doc.pdf",
            similarity_score=0.85,
            description="Test PDF document",
            metadata={"page_count": 10}
        ),
        MediaRecommendation(
            media_id="media_3",
            media_type=MediaType.PDF_CHUNK.value,
            file_path="/path/to/doc.pdf",
            similarity_score=0.75,
            description="PDF chunk from chapter 2",
            metadata={"chunk_id": "chunk_5"}
        ),
    ]


@pytest.fixture
def mock_lancedb_client():
    """Mock LanceDB client."""
    client = AsyncMock()
    client.initialize = AsyncMock(return_value=True)

    async def mock_search(query, table_name, num_results, metric):
        """Return mock search results."""
        return [
            {
                "id": "media_1",
                "media_type": "image",
                "file_path": "/path/to/image1.png",
                "_distance": 0.05,  # cosine distance (1 - similarity)
                "description": "Test image",
                "content": "Image content",
                "key_concepts": ["concept1", "concept2"],
            },
            {
                "id": "media_2",
                "media_type": "pdf",
                "file_path": "/path/to/doc.pdf",
                "_distance": 0.15,
                "description": "Test PDF",
                "content": "PDF content",
                "key_concepts": ["concept3"],
            },
            {
                "id": "media_3",
                "media_type": "pdf_chunk",
                "file_path": "/path/to/doc2.pdf",
                "_distance": 0.35,  # Below threshold (similarity = 0.65)
                "description": "Low similarity item",
                "content": "Low similarity content",
            },
        ]

    client.search = AsyncMock(side_effect=mock_search)
    return client


@pytest.fixture
def mock_graphiti_client():
    """Mock Graphiti client."""
    client = AsyncMock()
    client.initialize = AsyncMock(return_value=True)
    client.add_relationship = AsyncMock(return_value=True)
    return client


@pytest.fixture
def engine(mock_lancedb_client, mock_graphiti_client):
    """Create AssociationEngine with mocked clients."""
    return AssociationEngine(
        lancedb_client=mock_lancedb_client,
        graphiti_client=mock_graphiti_client,
        similarity_threshold=0.7,
        top_k=5,
        timeout_ms=500,
        enable_cache=True
    )


# ============================================================
# Unit Tests - Similarity Calculation (AC 6.7.1)
# ============================================================


class TestSimilarityCalculation:
    """Tests for similarity calculation methods."""

    def test_cosine_similarity_identical_vectors(self, sample_vectors):
        """Test cosine similarity for identical vectors."""
        engine = AssociationEngine()
        similarity = engine.calculate_similarity(
            sample_vectors["v1"],
            sample_vectors["v4"],
            SimilarityMetric.COSINE
        )
        assert math.isclose(similarity, 1.0, abs_tol=1e-6)

    def test_cosine_similarity_orthogonal_vectors(self, sample_vectors):
        """Test cosine similarity for orthogonal vectors."""
        engine = AssociationEngine()
        similarity = engine.calculate_similarity(
            sample_vectors["v1"],
            sample_vectors["v2"],
            SimilarityMetric.COSINE
        )
        assert math.isclose(similarity, 0.0, abs_tol=1e-6)

    def test_cosine_similarity_opposite_vectors(self, sample_vectors):
        """Test cosine similarity for opposite vectors."""
        engine = AssociationEngine()
        similarity = engine.calculate_similarity(
            sample_vectors["v1"],
            sample_vectors["v5"],
            SimilarityMetric.COSINE
        )
        assert math.isclose(similarity, -1.0, abs_tol=1e-6)

    def test_cosine_similarity_45_degree_angle(self, sample_vectors):
        """Test cosine similarity for 45 degree angle."""
        engine = AssociationEngine()
        similarity = engine.calculate_similarity(
            sample_vectors["v1"],
            sample_vectors["v3"],
            SimilarityMetric.COSINE
        )
        # cos(45°) = 1/√2 ≈ 0.707
        expected = 1.0 / math.sqrt(2)
        assert math.isclose(similarity, expected, abs_tol=1e-6)

    def test_cosine_similarity_zero_vector(self, sample_vectors):
        """Test cosine similarity with zero vector."""
        engine = AssociationEngine()
        similarity = engine.calculate_similarity(
            sample_vectors["v1"],
            sample_vectors["zero"],
            SimilarityMetric.COSINE
        )
        assert similarity == 0.0

    def test_euclidean_similarity_identical_vectors(self, sample_vectors):
        """Test Euclidean similarity for identical vectors."""
        engine = AssociationEngine()
        similarity = engine.calculate_similarity(
            sample_vectors["v1"],
            sample_vectors["v4"],
            SimilarityMetric.EUCLIDEAN
        )
        # Distance = 0, similarity = 1/(1+0) = 1.0
        assert math.isclose(similarity, 1.0, abs_tol=1e-6)

    def test_euclidean_similarity_different_vectors(self, sample_vectors):
        """Test Euclidean similarity for different vectors."""
        engine = AssociationEngine()
        similarity = engine.calculate_similarity(
            sample_vectors["v1"],
            sample_vectors["v2"],
            SimilarityMetric.EUCLIDEAN
        )
        # Distance = √2, similarity = 1/(1+√2) ≈ 0.414
        expected = 1.0 / (1.0 + math.sqrt(2))
        assert math.isclose(similarity, expected, abs_tol=1e-6)

    def test_dot_product_similarity(self, sample_vectors):
        """Test dot product calculation."""
        engine = AssociationEngine()
        similarity = engine.calculate_similarity(
            sample_vectors["v1"],
            sample_vectors["v3"],
            SimilarityMetric.DOT_PRODUCT
        )
        # [1,0,0] · [1,1,0] = 1
        assert math.isclose(similarity, 1.0, abs_tol=1e-6)

    def test_similarity_dimension_mismatch(self, sample_vectors):
        """Test similarity calculation with mismatched dimensions."""
        engine = AssociationEngine()
        with pytest.raises(SimilarityCalculationError, match="dimension mismatch"):
            engine.calculate_similarity(
                sample_vectors["v1"],
                sample_vectors["high_dim"],
                SimilarityMetric.COSINE
            )

    def test_similarity_high_dimensional_vectors(self, sample_vectors):
        """Test similarity calculation with high dimensional vectors."""
        engine = AssociationEngine()
        v1 = sample_vectors["high_dim"]
        v2 = [0.2] * 768

        similarity = engine.calculate_similarity(v1, v2, SimilarityMetric.COSINE)

        # Both vectors are normalized to have the same direction
        # [0.1, 0.1, ...] · [0.2, 0.2, ...] should give high similarity
        assert 0.9 < similarity <= 1.0

    def test_cosine_similarity_convenience_function(self, sample_vectors):
        """Test cosine_similarity convenience function."""
        similarity = cosine_similarity(
            sample_vectors["v1"],
            sample_vectors["v4"]
        )
        assert math.isclose(similarity, 1.0, abs_tol=1e-6)

    def test_euclidean_similarity_convenience_function(self, sample_vectors):
        """Test euclidean_similarity convenience function."""
        similarity = euclidean_similarity(
            sample_vectors["v1"],
            sample_vectors["v4"]
        )
        assert math.isclose(similarity, 1.0, abs_tol=1e-6)


# ============================================================
# Unit Tests - MediaRecommendation Dataclass
# ============================================================


class TestMediaRecommendation:
    """Tests for MediaRecommendation dataclass."""

    def test_create_media_recommendation(self):
        """Test creating a MediaRecommendation instance."""
        rec = MediaRecommendation(
            media_id="test_123",
            media_type=MediaType.IMAGE.value,
            file_path="/path/to/image.png",
            similarity_score=0.95
        )

        assert rec.media_id == "test_123"
        assert rec.media_type == "image"
        assert rec.file_path == "/path/to/image.png"
        assert rec.similarity_score == 0.95
        assert rec.description is None
        assert rec.metadata == {}

    def test_media_recommendation_to_dict(self, sample_recommendations):
        """Test converting MediaRecommendation to dictionary."""
        rec = sample_recommendations[0]
        result = rec.to_dict()

        assert result["media_id"] == "media_1"
        assert result["media_type"] == "image"
        assert result["similarity_score"] == 0.95
        assert "key_concepts" in result["metadata"]

    def test_media_recommendation_from_dict(self):
        """Test creating MediaRecommendation from dictionary."""
        data = {
            "media_id": "test_456",
            "media_type": "pdf",
            "file_path": "/path/to/doc.pdf",
            "similarity_score": 0.85,
            "description": "Test document",
            "metadata": {"pages": 10}
        }

        rec = MediaRecommendation.from_dict(data)

        assert rec.media_id == "test_456"
        assert rec.media_type == "pdf"
        assert rec.similarity_score == 0.85
        assert rec.metadata["pages"] == 10


class TestAssociationResult:
    """Tests for AssociationResult dataclass."""

    def test_create_association_result(self, sample_recommendations):
        """Test creating an AssociationResult instance."""
        result = AssociationResult(
            concept_id="concept_123",
            concept_name="Test Concept",
            recommendations=sample_recommendations,
            created_relations=3,
            processing_time_ms=150
        )

        assert result.concept_id == "concept_123"
        assert result.concept_name == "Test Concept"
        assert len(result.recommendations) == 3
        assert result.created_relations == 3
        assert result.processing_time_ms == 150
        assert result.error is None

    def test_association_result_to_dict(self, sample_recommendations):
        """Test converting AssociationResult to dictionary."""
        result = AssociationResult(
            concept_id="concept_123",
            concept_name="Test Concept",
            recommendations=sample_recommendations[:2],
            created_relations=2
        )

        data = result.to_dict()

        assert data["concept_id"] == "concept_123"
        assert len(data["recommendations"]) == 2
        assert data["created_relations"] == 2


class TestAssociationStats:
    """Tests for AssociationStats dataclass."""

    def test_create_association_stats(self):
        """Test creating AssociationStats instance."""
        stats = AssociationStats()

        assert stats.total_concepts_processed == 0
        assert stats.total_recommendations == 0
        assert stats.cache_hits == 0
        assert stats.cache_misses == 0

    def test_association_stats_to_dict(self):
        """Test converting AssociationStats to dictionary."""
        stats = AssociationStats(
            total_concepts_processed=10,
            total_recommendations=25,
            average_similarity_score=0.85
        )

        data = stats.to_dict()

        assert data["total_concepts_processed"] == 10
        assert data["total_recommendations"] == 25
        assert data["average_similarity_score"] == 0.85


# ============================================================
# Unit Tests - AssociationEngine Configuration
# ============================================================


class TestAssociationEngineConfiguration:
    """Tests for AssociationEngine configuration."""

    def test_default_configuration(self):
        """Test default engine configuration."""
        engine = AssociationEngine()

        assert engine.threshold == DEFAULT_SIMILARITY_THRESHOLD
        assert engine.top_k == DEFAULT_TOP_K
        assert engine.timeout_ms == 500
        assert engine.metric == SimilarityMetric.COSINE
        assert engine.enable_cache is True

    def test_custom_configuration(self):
        """Test custom engine configuration."""
        engine = AssociationEngine(
            similarity_threshold=0.8,
            top_k=10,
            timeout_ms=1000,
            metric=SimilarityMetric.EUCLIDEAN,
            enable_cache=False
        )

        assert engine.threshold == 0.8
        assert engine.top_k == 10
        assert engine.timeout_ms == 1000
        assert engine.metric == SimilarityMetric.EUCLIDEAN
        assert engine.enable_cache is False

    def test_get_stats(self):
        """Test getting engine statistics."""
        engine = AssociationEngine(similarity_threshold=0.8)
        stats = engine.get_stats()

        assert stats["initialized"] is False
        assert stats["similarity_threshold"] == 0.8
        assert stats["top_k"] == DEFAULT_TOP_K
        assert stats["cache_enabled"] is True
        assert stats["total_concepts_processed"] == 0

    def test_reset_stats(self):
        """Test resetting engine statistics."""
        engine = AssociationEngine()
        engine._stats.total_concepts_processed = 100
        engine._stats.cache_hits = 50

        engine.reset_stats()

        assert engine._stats.total_concepts_processed == 0
        assert engine._stats.cache_hits == 0


# ============================================================
# Integration Tests - Media Recommendation (AC 6.7.2)
# ============================================================


class TestMediaRecommendation:
    """Tests for media recommendation functionality."""

    @pytest.mark.asyncio
    async def test_recommend_media_for_concept(self, engine, sample_vectors):
        """Test recommending media for a concept."""
        recommendations = await engine.recommend_media_for_concept(
            concept_id="concept_123",
            concept_vector=sample_vectors["high_dim"],
            concept_name="Test Concept"
        )

        # Should return 2 recommendations (media_3 is below threshold)
        assert len(recommendations) == 2

        # Should be sorted by similarity (highest first)
        assert recommendations[0].similarity_score >= recommendations[1].similarity_score

        # First recommendation should have highest similarity
        assert recommendations[0].media_id == "media_1"
        assert recommendations[0].similarity_score == 0.95  # 1 - 0.05

    @pytest.mark.asyncio
    async def test_recommend_media_filter_existing(self, engine, sample_vectors):
        """Test filtering existing associations."""
        recommendations = await engine.recommend_media_for_concept(
            concept_id="concept_123",
            concept_vector=sample_vectors["high_dim"],
            filter_existing=True,
            existing_media_ids=["media_1"]  # Filter out the first result
        )

        # Should not include media_1
        media_ids = [r.media_id for r in recommendations]
        assert "media_1" not in media_ids

    @pytest.mark.asyncio
    async def test_recommend_media_respects_threshold(self, engine, sample_vectors):
        """Test that recommendation respects similarity threshold."""
        recommendations = await engine.recommend_media_for_concept(
            concept_id="concept_123",
            concept_vector=sample_vectors["high_dim"]
        )

        # All recommendations should be above threshold
        for rec in recommendations:
            assert rec.similarity_score >= engine.threshold

    @pytest.mark.asyncio
    async def test_recommend_media_respects_top_k(self, mock_lancedb_client, mock_graphiti_client, sample_vectors):
        """Test that recommendation respects top_k limit."""
        engine = AssociationEngine(
            lancedb_client=mock_lancedb_client,
            graphiti_client=mock_graphiti_client,
            top_k=1
        )

        recommendations = await engine.recommend_media_for_concept(
            concept_id="concept_123",
            concept_vector=sample_vectors["high_dim"]
        )

        assert len(recommendations) <= 1

    @pytest.mark.asyncio
    async def test_recommend_media_without_lancedb(self, sample_vectors):
        """Test recommendation without LanceDB client."""
        engine = AssociationEngine(lancedb_client=None)

        recommendations = await engine.recommend_media_for_concept(
            concept_id="concept_123",
            concept_vector=sample_vectors["high_dim"]
        )

        assert recommendations == []

    @pytest.mark.asyncio
    async def test_recommend_media_updates_stats(self, engine, sample_vectors):
        """Test that recommendation updates statistics."""
        await engine.recommend_media_for_concept(
            concept_id="concept_123",
            concept_vector=sample_vectors["high_dim"]
        )

        stats = engine.get_stats()
        assert stats["total_concepts_processed"] == 1
        assert stats["total_recommendations"] == 2

    @pytest.mark.asyncio
    async def test_recommend_media_uses_cache(self, engine, sample_vectors):
        """Test that caching works correctly."""
        # First call - cache miss
        await engine.recommend_media_for_concept(
            concept_id="concept_123",
            concept_vector=sample_vectors["high_dim"]
        )

        stats1 = engine.get_stats()
        assert stats1["cache_misses"] == 1

        # Second call with same parameters - cache hit
        await engine.recommend_media_for_concept(
            concept_id="concept_123",
            concept_vector=sample_vectors["high_dim"]
        )

        stats2 = engine.get_stats()
        assert stats2["cache_hits"] == 1

    @pytest.mark.asyncio
    async def test_recommend_media_cache_disabled(self, mock_lancedb_client, mock_graphiti_client, sample_vectors):
        """Test recommendation with cache disabled."""
        engine = AssociationEngine(
            lancedb_client=mock_lancedb_client,
            graphiti_client=mock_graphiti_client,
            enable_cache=False
        )

        # First call
        await engine.recommend_media_for_concept(
            concept_id="concept_123",
            concept_vector=sample_vectors["high_dim"]
        )

        # Second call
        await engine.recommend_media_for_concept(
            concept_id="concept_123",
            concept_vector=sample_vectors["high_dim"]
        )

        stats = engine.get_stats()
        assert stats["cache_hits"] == 0
        assert stats["cache_misses"] == 2

    @pytest.mark.asyncio
    async def test_clear_cache(self, engine, sample_vectors):
        """Test clearing the cache."""
        await engine.recommend_media_for_concept(
            concept_id="concept_123",
            concept_vector=sample_vectors["high_dim"]
        )

        assert engine.get_stats()["cache_size"] == 1

        cleared = engine.clear_cache()

        assert cleared == 1
        assert engine.get_stats()["cache_size"] == 0


# ============================================================
# Integration Tests - Batch Recommendation
# ============================================================


class TestBatchRecommendation:
    """Tests for batch recommendation functionality."""

    @pytest.mark.asyncio
    async def test_batch_recommend(self, engine, sample_vectors):
        """Test batch recommendation for multiple concepts."""
        concepts = [
            ("concept_1", sample_vectors["high_dim"], "Concept 1"),
            ("concept_2", sample_vectors["high_dim"], "Concept 2"),
            ("concept_3", sample_vectors["high_dim"], "Concept 3"),
        ]

        results = await engine.batch_recommend(concepts)

        assert len(results) == 3
        assert all(isinstance(r, AssociationResult) for r in results)
        assert all(r.error is None for r in results)

    @pytest.mark.asyncio
    async def test_batch_recommend_with_callback(self, engine, sample_vectors):
        """Test batch recommendation with progress callback."""
        concepts = [
            ("concept_1", sample_vectors["high_dim"], "Concept 1"),
            ("concept_2", sample_vectors["high_dim"], "Concept 2"),
        ]

        progress_updates = []

        def callback(current, total):
            progress_updates.append((current, total))

        await engine.batch_recommend(concepts, progress_callback=callback)

        assert len(progress_updates) == 2
        assert progress_updates[-1] == (2, 2)

    @pytest.mark.asyncio
    async def test_batch_recommend_with_error(self, mock_lancedb_client, mock_graphiti_client, sample_vectors):
        """Test batch recommendation handles errors gracefully."""
        # Make second search fail
        call_count = 0

        async def failing_search(query, table_name, num_results, metric):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise Exception("Search failed")
            return [{"id": "media_1", "_distance": 0.05, "media_type": "image", "file_path": "/test"}]

        mock_lancedb_client.search = AsyncMock(side_effect=failing_search)

        engine = AssociationEngine(
            lancedb_client=mock_lancedb_client,
            graphiti_client=mock_graphiti_client
        )

        concepts = [
            ("concept_1", sample_vectors["high_dim"], "Concept 1"),
            ("concept_2", sample_vectors["high_dim"], "Concept 2"),
        ]

        results = await engine.batch_recommend(concepts)

        assert len(results) == 2
        assert results[0].error is None
        assert results[1].error is not None


# ============================================================
# Integration Tests - Relationship Creation (AC 6.7.3)
# ============================================================


class TestRelationshipCreation:
    """Tests for Neo4j relationship creation."""

    @pytest.mark.asyncio
    async def test_create_associations(self, engine, sample_recommendations):
        """Test creating associations for recommendations."""
        created = await engine.create_associations(
            concept_id="concept_123",
            recommendations=sample_recommendations[:2]
        )

        assert created == 2
        assert engine._stats.total_relations_created == 2

    @pytest.mark.asyncio
    async def test_create_associations_without_graphiti(self, mock_lancedb_client, sample_recommendations):
        """Test creating associations without Graphiti client."""
        engine = AssociationEngine(
            lancedb_client=mock_lancedb_client,
            graphiti_client=None
        )

        created = await engine.create_associations(
            concept_id="concept_123",
            recommendations=sample_recommendations
        )

        assert created == 0

    @pytest.mark.asyncio
    async def test_create_associations_partial_failure(self, mock_lancedb_client, mock_graphiti_client, sample_recommendations):
        """Test that partial failures don't fail the whole batch."""
        # Make some relationships fail
        call_count = 0

        async def failing_add_relationship(entity1, entity2, relationship_type):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise Exception("Failed to create relationship")
            return True

        mock_graphiti_client.add_relationship = AsyncMock(side_effect=failing_add_relationship)

        engine = AssociationEngine(
            lancedb_client=mock_lancedb_client,
            graphiti_client=mock_graphiti_client
        )
        await engine.initialize()

        created = await engine.create_associations(
            concept_id="concept_123",
            recommendations=sample_recommendations
        )

        # Should create 2 out of 3 (one failed)
        assert created == 2

    @pytest.mark.asyncio
    async def test_batch_create_associations(self, engine, sample_recommendations, sample_vectors):
        """Test batch creation of associations."""
        results = [
            AssociationResult(
                concept_id="concept_1",
                concept_name="Concept 1",
                recommendations=sample_recommendations[:2]
            ),
            AssociationResult(
                concept_id="concept_2",
                concept_name="Concept 2",
                recommendations=sample_recommendations[1:]
            ),
        ]

        total_created = await engine.batch_create_associations(results)

        assert total_created == 4
        assert results[0].created_relations == 2
        assert results[1].created_relations == 2


# ============================================================
# Integration Tests - Full Pipeline
# ============================================================


class TestFullPipeline:
    """Tests for the complete recommendation and association pipeline."""

    @pytest.mark.asyncio
    async def test_process_concept(self, engine, sample_vectors):
        """Test full pipeline: recommend and create associations."""
        result = await engine.process_concept(
            concept_id="concept_123",
            concept_vector=sample_vectors["high_dim"],
            concept_name="Test Concept",
            create_relations=True
        )

        assert result.concept_id == "concept_123"
        assert result.concept_name == "Test Concept"
        assert len(result.recommendations) == 2
        assert result.created_relations == 2
        assert result.processing_time_ms >= 0
        assert result.error is None

    @pytest.mark.asyncio
    async def test_process_concept_without_relations(self, engine, sample_vectors):
        """Test pipeline without creating relationships."""
        result = await engine.process_concept(
            concept_id="concept_123",
            concept_vector=sample_vectors["high_dim"],
            create_relations=False
        )

        assert len(result.recommendations) == 2
        assert result.created_relations == 0

    @pytest.mark.asyncio
    async def test_process_concept_handles_errors(self, mock_lancedb_client, sample_vectors):
        """Test that process_concept handles errors gracefully."""
        mock_lancedb_client.search = AsyncMock(side_effect=Exception("Search failed"))

        engine = AssociationEngine(lancedb_client=mock_lancedb_client)

        result = await engine.process_concept(
            concept_id="concept_123",
            concept_vector=sample_vectors["high_dim"]
        )

        assert result.error is not None
        assert "Search failed" in result.error


# ============================================================
# Performance Tests (AC 6.7.4)
# ============================================================


class TestPerformance:
    """Tests for performance requirements."""

    @pytest.mark.asyncio
    async def test_recommendation_latency(self, engine, sample_vectors):
        """Test that recommendation latency is under 500ms."""
        start_time = time.perf_counter()

        await engine.recommend_media_for_concept(
            concept_id="concept_123",
            concept_vector=sample_vectors["high_dim"]
        )

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # Should be well under 500ms with mocked clients
        assert elapsed_ms < 500

    @pytest.mark.asyncio
    async def test_timeout_enforcement(self, mock_lancedb_client, mock_graphiti_client, sample_vectors):
        """Test that timeout is enforced."""
        # Make search take too long
        async def slow_search(query, table_name, num_results, metric):
            await asyncio.sleep(2)  # 2 seconds - way over timeout
            return []

        mock_lancedb_client.search = AsyncMock(side_effect=slow_search)

        engine = AssociationEngine(
            lancedb_client=mock_lancedb_client,
            graphiti_client=mock_graphiti_client,
            timeout_ms=100  # 100ms timeout
        )

        with pytest.raises(RecommendationError, match="timeout"):
            await engine.recommend_media_for_concept(
                concept_id="concept_123",
                concept_vector=sample_vectors["high_dim"]
            )

    @pytest.mark.asyncio
    async def test_batch_performance(self, engine, sample_vectors):
        """Test batch processing performance."""
        concepts = [
            (f"concept_{i}", sample_vectors["high_dim"], f"Concept {i}")
            for i in range(10)
        ]

        start_time = time.perf_counter()

        results = await engine.batch_recommend(concepts, max_concurrent=5)

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        assert len(results) == 10
        # With mocked clients and concurrency, should complete quickly
        assert elapsed_ms < 1000

    def test_similarity_calculation_performance(self, sample_vectors):
        """Test similarity calculation performance."""
        engine = AssociationEngine()
        v1 = sample_vectors["high_dim"]
        v2 = [0.2] * 768

        start_time = time.perf_counter()

        for _ in range(1000):
            engine.calculate_similarity(v1, v2, SimilarityMetric.COSINE)

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # 1000 calculations should be fast (< 100ms)
        assert elapsed_ms < 100


# ============================================================
# Edge Cases and Error Handling
# ============================================================


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_empty_concept_vector(self, engine):
        """Test handling of empty concept vector."""
        recommendations = await engine.recommend_media_for_concept(
            concept_id="concept_123",
            concept_vector=[]
        )

        # Should handle gracefully (LanceDB will be called with empty vector)
        assert isinstance(recommendations, list)

    @pytest.mark.asyncio
    async def test_recommendation_with_no_results(self, mock_lancedb_client, mock_graphiti_client, sample_vectors):
        """Test recommendation when LanceDB returns no results."""
        mock_lancedb_client.search = AsyncMock(return_value=[])

        engine = AssociationEngine(
            lancedb_client=mock_lancedb_client,
            graphiti_client=mock_graphiti_client
        )

        recommendations = await engine.recommend_media_for_concept(
            concept_id="concept_123",
            concept_vector=sample_vectors["high_dim"]
        )

        assert recommendations == []

    @pytest.mark.asyncio
    async def test_initialization_idempotent(self, engine):
        """Test that initialization is idempotent."""
        result1 = await engine.initialize()
        result2 = await engine.initialize()

        assert result1 is True
        assert result2 is True

    @pytest.mark.asyncio
    async def test_initialization_failure(self, mock_lancedb_client, mock_graphiti_client):
        """Test handling of initialization failure."""
        mock_lancedb_client.initialize = AsyncMock(side_effect=Exception("Init failed"))

        engine = AssociationEngine(
            lancedb_client=mock_lancedb_client,
            graphiti_client=mock_graphiti_client
        )

        with pytest.raises(AssociationEngineError, match="Initialization failed"):
            await engine.initialize()

    def test_unknown_similarity_metric(self, sample_vectors):
        """Test handling of unknown similarity metric."""
        engine = AssociationEngine()

        with pytest.raises(SimilarityCalculationError, match="Unknown metric"):
            engine.calculate_similarity(
                sample_vectors["v1"],
                sample_vectors["v2"],
                "unknown_metric"
            )

    @pytest.mark.asyncio
    async def test_recommend_media_convenience_function(self, mock_lancedb_client, sample_vectors):
        """Test recommend_media convenience function."""
        recommendations = await recommend_media(
            concept_vector=sample_vectors["high_dim"],
            lancedb_client=mock_lancedb_client,
            similarity_threshold=0.7,
            top_k=5
        )

        assert isinstance(recommendations, list)
        assert len(recommendations) <= 5

    def test_cache_eviction(self):
        """Test cache eviction when full."""
        engine = AssociationEngine(cache_size=2)

        # Fill cache
        engine._update_cache("key1", [])
        engine._update_cache("key2", [])

        assert len(engine._cache) == 2

        # Add one more - should evict oldest
        engine._update_cache("key3", [])

        assert len(engine._cache) == 2
        assert "key1" not in engine._cache
        assert "key3" in engine._cache


# ============================================================
# MediaType Enum Tests
# ============================================================


class TestMediaType:
    """Tests for MediaType enum."""

    def test_media_type_values(self):
        """Test MediaType enum values."""
        assert MediaType.IMAGE.value == "image"
        assert MediaType.PDF.value == "pdf"
        assert MediaType.PDF_CHUNK.value == "pdf_chunk"
        assert MediaType.UNKNOWN.value == "unknown"

    def test_media_type_string_comparison(self):
        """Test MediaType can be compared to strings."""
        assert MediaType.IMAGE == "image"
        assert MediaType.PDF == "pdf"


# ============================================================
# SimilarityMetric Enum Tests
# ============================================================


class TestSimilarityMetric:
    """Tests for SimilarityMetric enum."""

    def test_similarity_metric_values(self):
        """Test SimilarityMetric enum values."""
        assert SimilarityMetric.COSINE.value == "cosine"
        assert SimilarityMetric.EUCLIDEAN.value == "euclidean"
        assert SimilarityMetric.DOT_PRODUCT.value == "dot_product"

    def test_similarity_metric_string_comparison(self):
        """Test SimilarityMetric can be compared to strings."""
        assert SimilarityMetric.COSINE == "cosine"
        assert SimilarityMetric.EUCLIDEAN == "euclidean"


# ============================================================
# Pure Python Fallback Tests
# ============================================================


class TestPurePythonFallback:
    """Tests for pure Python fallback when NumPy is not available."""

    def test_pure_python_cosine_similarity(self, sample_vectors):
        """Test pure Python cosine similarity calculation."""
        engine = AssociationEngine()

        similarity = engine._calculate_similarity_pure_python(
            sample_vectors["v1"],
            sample_vectors["v4"],
            SimilarityMetric.COSINE
        )

        assert math.isclose(similarity, 1.0, abs_tol=1e-6)

    def test_pure_python_euclidean_similarity(self, sample_vectors):
        """Test pure Python Euclidean similarity calculation."""
        engine = AssociationEngine()

        similarity = engine._calculate_similarity_pure_python(
            sample_vectors["v1"],
            sample_vectors["v4"],
            SimilarityMetric.EUCLIDEAN
        )

        assert math.isclose(similarity, 1.0, abs_tol=1e-6)

    def test_pure_python_dot_product(self, sample_vectors):
        """Test pure Python dot product calculation."""
        engine = AssociationEngine()

        result = engine._calculate_similarity_pure_python(
            sample_vectors["v1"],
            sample_vectors["v3"],
            SimilarityMetric.DOT_PRODUCT
        )

        assert math.isclose(result, 1.0, abs_tol=1e-6)

    def test_pure_python_dimension_mismatch(self, sample_vectors):
        """Test pure Python handling of dimension mismatch."""
        engine = AssociationEngine()

        with pytest.raises(SimilarityCalculationError, match="dimension mismatch"):
            engine._calculate_similarity_pure_python(
                sample_vectors["v1"],
                sample_vectors["high_dim"],
                SimilarityMetric.COSINE
            )

    def test_pure_python_zero_vector(self, sample_vectors):
        """Test pure Python handling of zero vector."""
        engine = AssociationEngine()

        similarity = engine._calculate_similarity_pure_python(
            sample_vectors["v1"],
            sample_vectors["zero"],
            SimilarityMetric.COSINE
        )

        assert similarity == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
