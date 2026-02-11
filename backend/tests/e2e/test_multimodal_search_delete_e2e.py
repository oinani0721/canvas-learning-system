# Canvas Learning System - E2E Multimodal Search & Deletion Tests
# Story 35.9: AC 35.9.3 + AC 35.9.4
"""
E2E tests for multimodal search and deletion verification.

- AC 35.9.3: Vector search -> Verify relevance ordering
- AC 35.9.4: Delete content -> Verify dual-database cleanup

Shared fixtures (client, test_image_file, test_pdf_file) provided by tests/e2e/conftest.py
"""

import io

import pytest
from fastapi.testclient import TestClient


# =============================================================================
# AC 35.9.3: Vector Search Tests
# =============================================================================

class TestMultimodalSearchE2E:
    """E2E tests for vector similarity search."""

    def test_search_endpoint_returns_200(self, client: TestClient):
        """Test POST /api/v1/multimodal/search returns 200."""
        search_request = {
            "query": "test concept learning",
            "top_k": 10,
            "min_score": 0.1,
        }
        response = client.post("/api/v1/multimodal/search", json=search_request)
        assert response.status_code == 200

    def test_search_returns_relevance_ordered_results(self, client: TestClient, test_image_file: bytes):
        """Test search results are ordered by relevance score descending."""
        for i in range(3):
            files = {"file": (f"search_test_{i}.png", io.BytesIO(test_image_file), "image/png")}
            data = {
                "related_concept_id": f"search-concept-{i}",
                "canvas_path": "/test/canvas/search.canvas",
                "description": f"Test image {i} for search testing",
            }
            client.post("/api/v1/multimodal/upload", files=files, data=data)

        search_request = {
            "query": "test image search",
            "top_k": 10,
            "min_score": 0.0,
        }
        response = client.post("/api/v1/multimodal/search", json=search_request)

        assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"
        result = response.json()
        items = result.get("items", [])
        assert len(items) >= 2, f"Expected at least 2 search results after uploading 3 items, got {len(items)}"
        scores = [item.get("relevanceScore", 0) for item in items]
        assert scores == sorted(scores, reverse=True), "Results not ordered by relevance"

    def test_search_respects_top_k_parameter(self, client: TestClient):
        """Test search returns at most top_k results."""
        search_request = {"query": "test", "top_k": 5, "min_score": 0.0}
        response = client.post("/api/v1/multimodal/search", json=search_request)

        assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"
        result = response.json()
        assert len(result.get("items", [])) <= 5

    def test_search_filters_by_media_type(self, client: TestClient):
        """Test search can filter by media type."""
        search_request = {
            "query": "test search filter",
            "top_k": 10,
            "media_types": ["image"],
            "min_score": 0.0,
        }
        response = client.post("/api/v1/multimodal/search", json=search_request)

        assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"
        result = response.json()
        items = result.get("items", [])
        for item in items:
            assert item.get("type") == "image"

    def test_search_degrades_gracefully_without_vector_store(self, client: TestClient):
        """Test search degrades to text search when vector store unavailable (NFR Reliability).

        Story 35.11: 降级透明化 — search_mode should indicate fallback.
        """
        search_request = {
            "query": "degradation test query",
            "top_k": 5,
            "min_score": 0.0,
        }
        response = client.post("/api/v1/multimodal/search", json=search_request)

        # Should always succeed (200) even without vector store
        assert response.status_code == 200, (
            f"Search should degrade gracefully, not fail. Got {response.status_code}: {response.text[:200]}"
        )
        result = response.json()
        # search_mode indicates whether vector or text search was used
        assert "search_mode" in result, "Response should include search_mode for degradation transparency"

    def test_search_returns_empty_for_nonexistent_concept(self, client: TestClient):
        """Test search returns empty results for nonexistent concepts."""
        search_request = {
            "query": "completely nonexistent concept xyz123",
            "top_k": 5,
            "concept_id": "nonexistent-concept-xyz",
            "min_score": 0.5,
        }
        response = client.post("/api/v1/multimodal/search", json=search_request)

        assert response.status_code == 200
        result = response.json()
        assert result.get("total", 0) == 0 or len(result.get("items", [])) == 0



# =============================================================================
# AC 35.9.4: Deletion Verification Tests
# =============================================================================

class TestMultimodalDeletionE2E:
    """E2E tests for multimodal content deletion."""

    def test_delete_returns_success(self, client: TestClient, test_image_file: bytes):
        """Test DELETE /api/v1/multimodal/{content_id} returns success."""
        files = {"file": ("delete_test.png", io.BytesIO(test_image_file), "image/png")}
        data = {
            "related_concept_id": "delete-concept-001",
            "canvas_path": "/test/canvas/delete.canvas",
        }
        upload_response = client.post("/api/v1/multimodal/upload", files=files, data=data)
        assert upload_response.status_code == 201, (
            f"Setup upload failed: {upload_response.status_code}: {upload_response.text}"
        )

        content_id = upload_response.json()["content"]["id"]
        response = client.delete(f"/api/v1/multimodal/{content_id}")
        assert response.status_code == 204

    def test_delete_removes_from_get(self, client: TestClient, test_image_file: bytes):
        """Test deleted content is no longer retrievable via GET."""
        files = {"file": ("delete_verify.png", io.BytesIO(test_image_file), "image/png")}
        data = {
            "related_concept_id": "delete-concept-002",
            "canvas_path": "/test/canvas/delete.canvas",
        }
        upload_response = client.post("/api/v1/multimodal/upload", files=files, data=data)
        assert upload_response.status_code == 201, (
            f"Setup upload failed: {upload_response.status_code}: {upload_response.text}"
        )

        content_id = upload_response.json()["content"]["id"]
        client.delete(f"/api/v1/multimodal/{content_id}")

        response = client.get(f"/api/v1/multimodal/{content_id}")
        assert response.status_code == 404

    def test_delete_removes_from_concept_query(self, client: TestClient, test_image_file: bytes):
        """Test deleted content no longer appears in by-concept query."""
        concept_id = "delete-concept-003"
        files = {"file": ("delete_relation.png", io.BytesIO(test_image_file), "image/png")}
        data = {
            "related_concept_id": concept_id,
            "canvas_path": "/test/canvas/delete.canvas",
        }
        upload_response = client.post("/api/v1/multimodal/upload", files=files, data=data)
        assert upload_response.status_code == 201, (
            f"Setup upload failed: {upload_response.status_code}: {upload_response.text}"
        )

        content_id = upload_response.json()["content"]["id"]

        initial_response = client.get(f"/api/v1/multimodal/by-concept/{concept_id}")
        initial_count = initial_response.json().get("total", 0)

        client.delete(f"/api/v1/multimodal/{content_id}")

        response = client.get(f"/api/v1/multimodal/by-concept/{concept_id}")

        assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"
        result = response.json()
        assert result.get("total", 0) < initial_count or initial_count == 0

    def test_delete_nonexistent_returns_404(self, client: TestClient):
        """Test deleting nonexistent content returns 404."""
        response = client.delete("/api/v1/multimodal/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404
