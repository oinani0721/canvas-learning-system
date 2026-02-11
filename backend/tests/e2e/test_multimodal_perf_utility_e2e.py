# Canvas Learning System - E2E Multimodal Performance & Utility Tests
# Story 35.9: AC 35.9.5 + Utility
"""
E2E tests for multimodal performance and utility endpoints.

- AC 35.9.5: Performance: 10 images < 5 seconds
- Utility: Health, list, get, update endpoints

Shared fixtures (client, test_image_file, test_pdf_file) provided by tests/e2e/conftest.py
"""

import io
import time
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient


# =============================================================================
# AC 35.9.5: Performance Tests
# =============================================================================

@pytest.mark.slow
class TestMultimodalPerformanceE2E:
    """Performance E2E tests for multimodal operations."""

    def test_batch_upload_10_images_under_5_seconds(self, client: TestClient, test_image_file: bytes):
        """Test uploading 10 images completes in under 5 seconds."""
        num_images = 10
        canvas_path = "/test/canvas/performance.canvas"

        start = time.perf_counter()

        uploaded_ids = []
        for i in range(num_images):
            files = {"file": (f"perf_test_{i}.png", io.BytesIO(test_image_file), "image/png")}
            data = {
                "related_concept_id": f"perf-concept-{i}",
                "canvas_path": canvas_path,
            }
            response = client.post("/api/v1/multimodal/upload", files=files, data=data)
            assert response.status_code == 201, f"Upload {i} failed: {response.status_code}: {response.text}"
            uploaded_ids.append(response.json()["content"]["id"])

        elapsed_ms = (time.perf_counter() - start) * 1000

        assert elapsed_ms < 5000, f"Batch upload took {elapsed_ms:.0f}ms, expected < 5000ms"
        assert len(uploaded_ids) == num_images, f"Only {len(uploaded_ids)}/{num_images} uploads succeeded"

        for content_id in uploaded_ids:
            client.delete(f"/api/v1/multimodal/{content_id}")

    def test_concurrent_upload_performance(self, client: TestClient, test_image_file: bytes):
        """Test concurrent uploads complete efficiently."""
        num_images = 5
        canvas_path = "/test/canvas/concurrent.canvas"

        def upload_image(index: int) -> tuple[int, str | None]:
            files = {"file": (f"concurrent_{index}.png", io.BytesIO(test_image_file), "image/png")}
            data = {
                "related_concept_id": f"concurrent-concept-{index}",
                "canvas_path": canvas_path,
            }
            response = client.post("/api/v1/multimodal/upload", files=files, data=data)
            assert response.status_code == 201, (
                f"Upload {index} failed: {response.status_code} {response.text[:200]}"
            )
            return response.status_code, response.json()["content"]["id"]

        start = time.perf_counter()

        with ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(upload_image, range(num_images)))

        elapsed_ms = (time.perf_counter() - start) * 1000

        successful = [r for r in results if r[1] is not None]
        assert len(successful) == num_images, f"Only {len(successful)}/{num_images} concurrent uploads succeeded"
        assert elapsed_ms < 5000, f"Concurrent upload took {elapsed_ms:.0f}ms"

        for _, content_id in successful:
            if content_id:
                client.delete(f"/api/v1/multimodal/{content_id}")

    def test_search_response_time(self, client: TestClient):
        """Test search endpoint responds within acceptable time."""
        search_request = {
            "query": "test performance search query",
            "top_k": 20,
            "min_score": 0.0,
        }

        start = time.perf_counter()
        response = client.post("/api/v1/multimodal/search", json=search_request)
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert response.status_code == 200
        assert elapsed_ms < 2000, f"Search took {elapsed_ms:.0f}ms, expected < 2000ms"


# =============================================================================
# Utility Tests
# =============================================================================

class TestMultimodalUtilityE2E:
    """E2E tests for multimodal utility endpoints."""

    def test_health_endpoint_returns_status(self, client: TestClient):
        """Test multimodal health endpoint returns service status."""
        response = client.get("/api/v1/multimodal/health")

        assert response.status_code == 200
        result = response.json()
        assert "status" in result
        assert result["status"] in ["healthy", "degraded", "unhealthy"]

    def test_list_endpoint_returns_results(self, client: TestClient):
        """Test GET /api/v1/multimodal returns list of content."""
        response = client.get("/api/v1/multimodal", params={"limit": 10})

        assert response.status_code == 200
        result = response.json()
        assert "items" in result
        assert "total" in result

    def test_list_respects_media_type_filter(self, client: TestClient):
        """Test list endpoint filters by media type."""
        response = client.get("/api/v1/multimodal", params={"media_type": "image"})

        assert response.status_code == 200
        result = response.json()
        items = result.get("items", [])
        for item in items:
            assert item.get("media_type") == "image"

    def test_get_content_by_id(self, client: TestClient, test_image_file: bytes):
        """Test GET /api/v1/multimodal/{content_id} returns content details."""
        files = {"file": ("get_test.png", io.BytesIO(test_image_file), "image/png")}
        data = {
            "related_concept_id": "get-concept-001",
            "canvas_path": "/test/canvas/get.canvas",
        }
        upload_response = client.post("/api/v1/multimodal/upload", files=files, data=data)
        assert upload_response.status_code == 201, (
            f"Setup upload failed: {upload_response.status_code}: {upload_response.text}"
        )

        content_id = upload_response.json()["content"]["id"]

        response = client.get(f"/api/v1/multimodal/{content_id}")

        assert response.status_code == 200
        result = response.json()
        assert result["id"] == content_id

        client.delete(f"/api/v1/multimodal/{content_id}")

    def test_update_content_metadata(self, client: TestClient, test_image_file: bytes):
        """Test PUT /api/v1/multimodal/{content_id} updates metadata."""
        files = {"file": ("update_test.png", io.BytesIO(test_image_file), "image/png")}
        data = {
            "related_concept_id": "update-concept-001",
            "canvas_path": "/test/canvas/update.canvas",
        }
        upload_response = client.post("/api/v1/multimodal/upload", files=files, data=data)
        assert upload_response.status_code == 201, (
            f"Setup upload failed: {upload_response.status_code}: {upload_response.text}"
        )

        content_id = upload_response.json()["content"]["id"]

        update_data = {"description": "Updated test description"}
        response = client.put(f"/api/v1/multimodal/{content_id}", json=update_data)

        assert response.status_code == 200
        result = response.json()
        assert result.get("description") == "Updated test description"

        client.delete(f"/api/v1/multimodal/{content_id}")
