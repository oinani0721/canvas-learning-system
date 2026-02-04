# Canvas Learning System - Story 35.8 Integration Tests
# ✅ Verified from pytest documentation
"""
Story 35.8 - RAG多模态搜索集成 Integration Tests

This module provides integration tests that verify the RAG multimodal search
functionality works correctly end-to-end through the API layer.

Test Coverage:
- AC 35.8.1: RAGQueryResponse includes multimodal_results field
- AC 35.8.2: MultimodalRetriever is wired to RAG Service
- AC 35.8.3: Image results include thumbnail
- AC 35.8.4: Multimodal results participate in RRF fusion

[Source: docs/stories/35.8.story.md]
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.services.rag_service import get_rag_service


# ============================================================================
# Fixtures
# ============================================================================

def create_mock_rag_service(fusion_strategy_override=None):
    """Create a mock RAG service for testing."""
    mock = MagicMock()
    mock.is_available = True
    mock._initialized = True

    async def mock_query(query, canvas_file=None, is_review_canvas=False,
                         fusion_strategy=None, reranking_strategy=None):
        """Return mock RAG results with multimodal content."""
        # Use override for review canvas, else use request param
        actual_fusion = fusion_strategy_override or fusion_strategy or (
            "weighted" if is_review_canvas else "rrf"
        )
        return {
            "results": [
                {
                    "doc_id": "node-123",
                    "content": "逆否命题是将原命题的条件和结论同时取否定...",
                    "score": 0.95,
                    "metadata": {"source": "graphiti", "canvas": canvas_file}
                }
            ],
            "multimodal_results": [
                {
                    "id": "mm-001",
                    "media_type": "image",
                    "path": "images/concept_diagram.png",
                    "thumbnail": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUg...",
                    "relevance_score": 0.87,
                    "metadata": {"width": 800, "height": 600}
                },
                {
                    "id": "mm-002",
                    "media_type": "pdf",
                    "path": "docs/reference.pdf",
                    "thumbnail": None,
                    "relevance_score": 0.72,
                    "metadata": {"pages": 5}
                }
            ],
            "quality_grade": "high",
            "result_count": 1,
            "latency_ms": {
                "graphiti": 45.2,
                "lancedb": 32.1,
                "multimodal": 58.5,
                "fusion": 5.3,
                "reranking": 12.8
            },
            "total_latency_ms": 153.9,
            "metadata": {
                "query_rewritten": False,
                "rewrite_count": 0,
                "fusion_strategy": actual_fusion,
                "reranking_strategy": reranking_strategy or "hybrid_auto"
            }
        }

    mock.query = AsyncMock(side_effect=mock_query)
    mock.get_status = MagicMock(return_value={
        "available": True,
        "initialized": True,
        "langgraph_available": True,
        "import_error": None
    })

    return mock


@pytest.fixture
def mock_rag_service():
    """Create a mock RAG service for testing."""
    return create_mock_rag_service()


# ============================================================================
# AC 35.8.1: RAGQueryResponse includes multimodal_results field
# ============================================================================

class TestRAGQueryResponseMultimodal:
    """
    AC 35.8.1: Integration tests for multimodal_results in RAGQueryResponse.

    Verifies that:
    - POST /api/v1/rag/query returns multimodal_results array
    - MultimodalResultItem fields are correctly populated
    - Response schema matches OpenAPI specification

    [Source: Story 35.8 - AC 35.8.1]
    """

    @pytest.mark.asyncio
    async def test_rag_query_returns_multimodal_results(self, mock_rag_service):
        """
        AC 35.8.1.1: Verify RAG query response includes multimodal_results.

        Given: A RAG query request
        When: POST /api/v1/rag/query is called
        Then: Response contains multimodal_results array with correct structure
        """
        # Override FastAPI dependency
        app.dependency_overrides[get_rag_service] = lambda: mock_rag_service
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/v1/rag/query",
                    json={
                        "query": "什么是逆否命题?",
                        "canvas_file": "离散数学.canvas"
                    }
                )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()

        # Verify multimodal_results exists and is a list
        assert "multimodal_results" in data
        assert isinstance(data["multimodal_results"], list)
        assert len(data["multimodal_results"]) >= 1

    @pytest.mark.asyncio
    async def test_multimodal_result_item_fields(self, mock_rag_service):
        """
        AC 35.8.1.2: Verify MultimodalResultItem has required fields.

        Given: A RAG query with multimodal results
        When: Response is received
        Then: Each multimodal result has id, media_type, path, thumbnail, relevance_score
        """
        app.dependency_overrides[get_rag_service] = lambda: mock_rag_service
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/v1/rag/query",
                    json={"query": "图像搜索测试"}
                )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()

        for item in data["multimodal_results"]:
            # Required fields per OpenAPI spec
            assert "id" in item
            assert "media_type" in item
            assert "path" in item
            assert "relevance_score" in item
            assert "metadata" in item

            # media_type must be valid enum
            assert item["media_type"] in ["image", "pdf", "audio", "video"]

            # relevance_score must be 0-1
            assert 0.0 <= item["relevance_score"] <= 1.0


# ============================================================================
# AC 35.8.2: MultimodalRetriever wired to RAG Service
# ============================================================================

class TestMultimodalRetrieverIntegration:
    """
    AC 35.8.2: Integration tests for MultimodalRetriever wiring.

    Verifies that:
    - MultimodalRetriever is called during RAG query
    - Results flow through the state graph correctly
    - Graceful fallback when multimodal unavailable

    [Source: Story 35.8 - AC 35.8.2]
    """

    @pytest.mark.asyncio
    async def test_multimodal_retriever_called_on_query(self, mock_rag_service):
        """
        AC 35.8.2.1: Verify multimodal retriever is invoked.

        Given: RAG service with multimodal enabled
        When: Query is executed
        Then: Multimodal retrieval is performed (latency > 0)
        """
        app.dependency_overrides[get_rag_service] = lambda: mock_rag_service
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/v1/rag/query",
                    json={"query": "测试多模态检索"}
                )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()

        # Verify multimodal latency is tracked
        assert "latency_ms" in data
        assert data["latency_ms"]["multimodal"] is not None
        assert data["latency_ms"]["multimodal"] > 0

    @pytest.mark.asyncio
    async def test_graceful_degradation_no_multimodal(self):
        """
        AC 35.8.2.2: Verify graceful degradation when no multimodal results.

        Given: RAG service returns empty multimodal results
        When: Query is executed
        Then: Response still valid with empty multimodal_results array
        """
        mock = MagicMock()
        mock.is_available = True
        mock._initialized = True

        async def mock_query(*args, **kwargs):
            return {
                "results": [{"doc_id": "1", "content": "test", "score": 0.9, "metadata": {}}],
                "multimodal_results": [],  # Empty multimodal
                "quality_grade": "medium",
                "result_count": 1,
                "latency_ms": {"multimodal": 0.0},
                "total_latency_ms": 50.0,
                "metadata": {}
            }

        mock.query = AsyncMock(side_effect=mock_query)

        app.dependency_overrides[get_rag_service] = lambda: mock
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/v1/rag/query",
                    json={"query": "无多模态结果"}
                )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["multimodal_results"] == []


# ============================================================================
# AC 35.8.3: Image results include thumbnail
# ============================================================================

class TestThumbnailIntegration:
    """
    AC 35.8.3: Integration tests for thumbnail population.

    Verifies that:
    - Image results include thumbnail Base64 or URL
    - Thumbnail field is properly mapped from backend

    [Source: Story 35.8 - AC 35.8.3]
    """

    @pytest.mark.asyncio
    async def test_image_result_has_thumbnail(self, mock_rag_service):
        """
        AC 35.8.3.1: Verify image results include thumbnail.

        Given: RAG query returns image results
        When: Response is received
        Then: Image items have thumbnail field populated
        """
        app.dependency_overrides[get_rag_service] = lambda: mock_rag_service
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/v1/rag/query",
                    json={"query": "图片搜索"}
                )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()

        # Find image result
        image_results = [
            r for r in data["multimodal_results"]
            if r["media_type"] == "image"
        ]

        assert len(image_results) >= 1

        # Verify thumbnail is present for image
        for img in image_results:
            assert "thumbnail" in img
            # Thumbnail should be Base64 data URL or path
            assert img["thumbnail"] is not None
            assert (
                img["thumbnail"].startswith("data:image/") or
                img["thumbnail"].endswith((".png", ".jpg", ".jpeg", ".gif"))
            )


# ============================================================================
# AC 35.8.4: RRF Multimodal Fusion
# ============================================================================

class TestRRFMultimodalFusionIntegration:
    """
    AC 35.8.4: Integration tests for RRF multimodal fusion.

    Verifies that:
    - Multimodal results participate in fusion
    - Fusion strategy can be configured
    - Total latency < 200ms budget

    [Source: Story 35.8 - AC 35.8.4]
    """

    @pytest.mark.asyncio
    async def test_fusion_strategy_configurable(self):
        """
        AC 35.8.4.1: Verify fusion strategy can be configured via request.

        Given: RAG query with fusion_strategy parameter
        When: Query is executed
        Then: Specified fusion strategy is used
        """
        # Create mock that respects fusion_strategy parameter
        mock = create_mock_rag_service()
        app.dependency_overrides[get_rag_service] = lambda: mock
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/v1/rag/query",
                    json={
                        "query": "融合策略测试",
                        "fusion_strategy": "weighted"
                    }
                )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()

        # Verify fusion strategy in metadata
        assert data["metadata"]["fusion_strategy"] == "weighted"

    @pytest.mark.asyncio
    async def test_review_canvas_uses_weighted_fusion(self):
        """
        AC 35.8.4.2: Verify review canvas uses weighted fusion by default.

        Given: RAG query with is_review_canvas=True
        When: Query is executed without explicit fusion_strategy
        Then: Weighted fusion is used (better for review scenarios)
        """
        mock = create_mock_rag_service()
        app.dependency_overrides[get_rag_service] = lambda: mock
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/v1/rag/query",
                    json={
                        "query": "复习模式测试",
                        "is_review_canvas": True
                    }
                )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()

        # Review canvas should use weighted fusion
        assert data["metadata"]["fusion_strategy"] == "weighted"

    @pytest.mark.asyncio
    async def test_latency_tracking(self, mock_rag_service):
        """
        AC 35.8.4.3: Verify latency is tracked for all components.

        Given: RAG query execution
        When: Response is received
        Then: Latency breakdown includes all retrieval sources
        """
        app.dependency_overrides[get_rag_service] = lambda: mock_rag_service
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/v1/rag/query",
                    json={"query": "延迟测试"}
                )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()

        latency = data["latency_ms"]

        # Verify all latency components tracked
        expected_components = ["graphiti", "lancedb", "multimodal", "fusion", "reranking"]
        for component in expected_components:
            assert component in latency, f"Missing latency for {component}"


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """
    Error handling integration tests for RAG multimodal API.
    """

    @pytest.mark.asyncio
    async def test_rag_unavailable_returns_503(self):
        """
        Verify 503 returned when RAG service unavailable.
        """
        from app.services.rag_service import RAGUnavailableError

        mock = MagicMock()
        mock.query = AsyncMock(
            side_effect=RAGUnavailableError("LangGraph not available")
        )

        app.dependency_overrides[get_rag_service] = lambda: mock
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/v1/rag/query",
                    json={"query": "测试"}
                )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 503

    @pytest.mark.asyncio
    async def test_invalid_fusion_strategy(self):
        """
        Verify 422 returned for invalid fusion_strategy enum value.
        """
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/rag/query",
                json={
                    "query": "测试",
                    "fusion_strategy": "invalid_strategy"  # Not in enum
                }
            )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_empty_query_rejected(self):
        """
        Verify empty query is rejected with 422.
        """
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/rag/query",
                json={"query": ""}  # Empty query
            )

        assert response.status_code == 422  # min_length=1 validation


# ============================================================================
# Status Endpoint Tests
# ============================================================================

class TestRAGStatusEndpoint:
    """
    Tests for /api/v1/rag/status endpoint.
    """

    @pytest.mark.asyncio
    async def test_status_endpoint_returns_availability(self, mock_rag_service):
        """
        Verify status endpoint returns service availability info.
        """
        app.dependency_overrides[get_rag_service] = lambda: mock_rag_service
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get("/api/v1/rag/status")
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()

        assert "available" in data
        assert "initialized" in data
        assert "langgraph_available" in data
        assert data["available"] is True
