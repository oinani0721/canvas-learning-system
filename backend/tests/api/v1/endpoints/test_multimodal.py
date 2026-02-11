# Canvas Learning System - Story 35.1 + 35.2 Model Validation Tests
# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: testing)
"""
Pydantic model validation tests for multimodal schemas.

Tests validate schema constraints, enum values, and field validation
WITHOUT using mock services (which produce false coverage).

- Story 35.1: Upload/Management models
- Story 35.2: Query/Search models
- Story 35.11: Health degradation transparency fields
"""

import pytest
from datetime import datetime

from app.models.multimodal_schemas import (
    MediaItemResponse,
    MultimodalByConceptResponse,
    MultimodalDeleteResponse,
    MultimodalHealthResponse,
    MultimodalMediaType,
    MultimodalMetadataSchema,
    MultimodalPaginatedListResponse,
    MultimodalResponse,
    MultimodalSearchRequest,
    MultimodalSearchResponse,
    MultimodalUpdateRequest,
    MultimodalUploadResponse,
    MultimodalUploadUrlRequest,
    PaginationMeta,
)


# =============================================================================
# Story 35.1: Upload/Management Model Tests
# =============================================================================

class TestMultimodalModels:
    """Test Pydantic model validation for Story 35.1."""

    def test_upload_url_request_valid(self):
        """Test valid upload URL request."""
        request = MultimodalUploadUrlRequest(
            url="https://example.com/image.jpg",
            related_concept_id="node-123",
            canvas_path="/path/to/canvas.canvas",
            description="Test description",
        )
        assert request.url == "https://example.com/image.jpg"
        assert request.related_concept_id == "node-123"

    def test_update_request_optional_fields(self):
        """Test update request with optional fields."""
        request = MultimodalUpdateRequest(
            description="Updated description",
        )
        assert request.description == "Updated description"
        assert request.related_concept_id is None
        assert request.source_location is None

    def test_multimodal_response_model(self):
        """Test multimodal response model."""
        response = MultimodalResponse(
            id="test-id",
            media_type=MultimodalMediaType.PDF,
            file_path="/path/to/file.pdf",
            related_concept_id="node-456",
            created_at=datetime.now(),
        )
        assert response.id == "test-id"
        assert response.media_type == MultimodalMediaType.PDF

    def test_media_type_enum(self):
        """Test media type enum values."""
        assert MultimodalMediaType.IMAGE.value == "image"
        assert MultimodalMediaType.PDF.value == "pdf"
        assert MultimodalMediaType.AUDIO.value == "audio"
        assert MultimodalMediaType.VIDEO.value == "video"


# =============================================================================
# Story 35.11: Health Model Tests
# =============================================================================

class TestMultimodalHealthModels:
    """Test health response model validation (Story 35.11 AC 35.11.3)."""

    def test_health_response_full_capability(self):
        """Test health response with full capability fields."""
        response = MultimodalHealthResponse(
            status="healthy",
            lancedb_connected=True,
            neo4j_connected=True,
            storage_path_writable=True,
            total_items=5,
            storage_backend="multimodal_store",
            vector_search_available=True,
            capability_level="full",
        )

        data = response.model_dump()
        assert "status" in data
        assert "lancedb_connected" in data
        assert "neo4j_connected" in data
        assert "storage_path_writable" in data
        assert "total_items" in data
        assert "storage_backend" in data
        assert "vector_search_available" in data
        assert "capability_level" in data
        assert response.storage_backend == "multimodal_store"
        assert response.vector_search_available is True
        assert response.capability_level == "full"

    def test_health_degraded_values(self):
        """Story 35.11 AC 35.11.3: Health endpoint reports degraded state correctly."""
        degraded_response = MultimodalHealthResponse(
            status="degraded",
            lancedb_connected=False,
            neo4j_connected=False,
            storage_path_writable=True,
            total_items=0,
            storage_backend="json_fallback",
            vector_search_available=False,
            capability_level="degraded",
        )
        assert degraded_response.storage_backend == "json_fallback"
        assert degraded_response.vector_search_available is False
        assert degraded_response.capability_level == "degraded"

    def test_health_field_validation(self):
        """Story 35.11 AC 35.11.3: storage_backend and capability_level are pattern-validated."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            MultimodalHealthResponse(
                status="healthy",
                lancedb_connected=True,
                neo4j_connected=True,
                storage_path_writable=True,
                total_items=0,
                storage_backend="invalid_backend",
            )

        with pytest.raises(ValidationError):
            MultimodalHealthResponse(
                status="healthy",
                lancedb_connected=True,
                neo4j_connected=True,
                storage_path_writable=True,
                total_items=0,
                capability_level="unknown",
            )


# =============================================================================
# Story 35.2: Query/Search Model Tests
# =============================================================================

class TestMultimodalQueryModels:
    """Test Story 35.2 Pydantic model validation."""

    def test_media_item_response_valid(self):
        """Test valid MediaItemResponse."""
        item = MediaItemResponse(
            id="item-123",
            type="image",
            path="/path/to/image.jpg",
            title="Test Image",
            relevanceScore=0.85,
            conceptId="concept-456",
        )
        assert item.id == "item-123"
        assert item.type == "image"
        assert item.relevanceScore == 0.85

    def test_media_item_response_type_validation(self):
        """Test MediaItemResponse type validation."""
        for valid_type in ["image", "pdf", "audio", "video"]:
            item = MediaItemResponse(
                id="item-123",
                type=valid_type,
                path="/path/to/file",
                relevanceScore=0.5,
            )
            assert item.type == valid_type

    def test_media_item_response_score_bounds(self):
        """Test relevanceScore must be between 0 and 1."""
        from pydantic import ValidationError

        MediaItemResponse(id="1", type="image", path="/p", relevanceScore=0.0)
        MediaItemResponse(id="2", type="image", path="/p", relevanceScore=1.0)

        with pytest.raises(ValidationError):
            MediaItemResponse(id="3", type="image", path="/p", relevanceScore=1.5)

        with pytest.raises(ValidationError):
            MediaItemResponse(id="4", type="image", path="/p", relevanceScore=-0.1)

    def test_pagination_meta_valid(self):
        """Test valid PaginationMeta."""
        meta = PaginationMeta(
            total=100,
            page=2,
            page_size=20,
            total_pages=5,
            has_next=True,
            has_prev=True,
        )
        assert meta.total == 100
        assert meta.page == 2
        assert meta.total_pages == 5

    def test_search_request_valid(self):
        """Test valid MultimodalSearchRequest."""
        request = MultimodalSearchRequest(
            query="find images of diagrams",
            media_types=[MultimodalMediaType.IMAGE, MultimodalMediaType.PDF],
            top_k=20,
            min_score=0.6,
        )
        assert request.query == "find images of diagrams"
        assert len(request.media_types) == 2
        assert request.top_k == 20

    def test_search_request_query_not_empty(self):
        """Test search request validates non-empty query."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            MultimodalSearchRequest(query="   ")
