# Canvas Learning System - E2E Multimodal Upload Tests
# Story 35.9: AC 35.9.1 + AC 35.9.2
"""
E2E tests for multimodal upload and relationship verification.

- AC 35.9.1: Upload image -> Verify storage
- AC 35.9.2: Associate Canvas node -> Verify relationship

Shared fixtures (client, test_image_file, test_pdf_file) provided by tests/e2e/conftest.py
"""

import io

from fastapi.testclient import TestClient


# =============================================================================
# AC 35.9.1: Upload Verification Tests
# =============================================================================

class TestMultimodalUploadE2E:
    """E2E tests for multimodal upload functionality."""

    def test_upload_image_returns_201(self, client: TestClient, test_image_file: bytes):
        """Test POST /api/v1/multimodal/upload returns 201 Created."""
        files = {"file": ("test_image.png", io.BytesIO(test_image_file), "image/png")}
        data = {
            "related_concept_id": "concept-001",
            "canvas_path": "/test/canvas/learning.canvas",
        }
        response = client.post("/api/v1/multimodal/upload", files=files, data=data)
        assert response.status_code == 201, f"Expected 201 Created, got {response.status_code}: {response.text}"

    def test_upload_image_returns_content_details(self, client: TestClient, test_image_file: bytes):
        """Test upload returns content details with valid structure."""
        files = {"file": ("test_image.png", io.BytesIO(test_image_file), "image/png")}
        data = {
            "related_concept_id": "concept-002",
            "canvas_path": "/test/canvas/learning.canvas",
            "description": "Test image for E2E testing",
        }
        response = client.post("/api/v1/multimodal/upload", files=files, data=data)

        assert response.status_code == 201, f"Expected 201 Created, got {response.status_code}: {response.text}"
        result = response.json()
        assert "content" in result
        content = result["content"]
        assert "id" in content
        assert content["media_type"] == "image"
        assert content["related_concept_id"] == "concept-002"

    def test_upload_pdf_stores_correctly(self, client: TestClient, test_pdf_file: bytes):
        """Test PDF upload creates correct media type."""
        files = {"file": ("test_document.pdf", io.BytesIO(test_pdf_file), "application/pdf")}
        data = {
            "related_concept_id": "concept-003",
            "canvas_path": "/test/canvas/documents.canvas",
        }
        response = client.post("/api/v1/multimodal/upload", files=files, data=data)

        assert response.status_code == 201, f"Expected 201 Created, got {response.status_code}: {response.text}"
        result = response.json()
        assert result["content"]["media_type"] == "pdf"

    def test_upload_validates_required_fields(self, client: TestClient, test_image_file: bytes):
        """Test upload fails when required fields are missing."""
        files = {"file": ("test.png", io.BytesIO(test_image_file), "image/png")}
        data = {"canvas_path": "/test/canvas.canvas"}
        response = client.post("/api/v1/multimodal/upload", files=files, data=data)
        assert response.status_code == 422

    def test_upload_rejects_unsupported_media_type(self, client: TestClient):
        """Test upload rejects unsupported file types."""
        files = {"file": ("malware.exe", io.BytesIO(b"MZ...fake exe content"), "application/x-msdownload")}
        data = {
            "related_concept_id": "concept-bad",
            "canvas_path": "/test/canvas.canvas",
        }
        response = client.post("/api/v1/multimodal/upload", files=files, data=data)
        assert response.status_code in [415, 422, 400]

    def test_upload_rejects_file_exceeding_size_limit(self, client: TestClient):
        """Test upload rejects files exceeding 50MB limit (AC 35.1.1).

        Uses MULTIMODAL_MAX_FILE_SIZE_MB env var override to test with small payload.
        """
        from app.services.multimodal_service import MAX_FILE_SIZE

        # Create a PNG header + payload slightly over the limit
        png_header = b'\x89PNG\r\n\x1a\n'
        over_limit_size = MAX_FILE_SIZE + 1024  # 1KB over limit

        # For speed, we mock the size check instead of creating a 50MB+ payload.
        # The actual size enforcement is at multimodal_service.py:378.
        # We use a minimal approach: create a file that passes format check
        # but will be rejected by size check via monkeypatching.
        import unittest.mock
        with unittest.mock.patch(
            'app.services.multimodal_service.MAX_FILE_SIZE', 1000
        ):
            # 2KB payload > 1000 byte limit
            big_content = png_header + b'\x00' * 2000
            files = {"file": ("big_image.png", io.BytesIO(big_content), "image/png")}
            data = {
                "related_concept_id": "concept-big",
                "canvas_path": "/test/canvas.canvas",
            }
            response = client.post("/api/v1/multimodal/upload", files=files, data=data)
            assert response.status_code in [413, 415, 400], (
                f"Expected 413/415/400 for oversized file, got {response.status_code}: {response.text[:200]}"
            )
            assert "too large" in response.text.lower(), (
                f"Expected 'too large' in error message, got: {response.text[:200]}"
            )

    def test_upload_rejects_mime_spoofed_exe_as_png(self, client: TestClient):
        """Test magic bytes validation rejects EXE disguised as PNG (NFR Security).

        Sends a file with .png extension and image/png MIME type but EXE content.
        The server should reject it because magic bytes don't match PNG.
        """
        # Windows PE executable header (MZ magic)
        exe_content = b'MZ' + b'\x00' * 500
        files = {"file": ("spoofed.png", io.BytesIO(exe_content), "image/png")}
        data = {
            "related_concept_id": "concept-spoof",
            "canvas_path": "/test/canvas.canvas",
        }
        response = client.post("/api/v1/multimodal/upload", files=files, data=data)
        assert response.status_code in [415, 400, 422], (
            f"MIME-spoofed EXE should be rejected, got {response.status_code}"
        )

    def test_upload_rejects_empty_file(self, client: TestClient):
        """Test upload rejects zero-byte files (NFR Reliability)."""
        files = {"file": ("empty.png", io.BytesIO(b""), "image/png")}
        data = {
            "related_concept_id": "concept-empty",
            "canvas_path": "/test/canvas.canvas",
        }
        response = client.post("/api/v1/multimodal/upload", files=files, data=data)
        assert response.status_code in [415, 400, 422], (
            f"Empty file should be rejected, got {response.status_code}"
        )

    def test_upload_handles_corrupted_png(self, client: TestClient):
        """Test upload handles truncated/corrupted PNG gracefully (NFR Reliability)."""
        # Valid PNG header but truncated body
        corrupted_png = b'\x89PNG\r\n\x1a\n' + b'\x00' * 50
        files = {"file": ("corrupted.png", io.BytesIO(corrupted_png), "image/png")}
        data = {
            "related_concept_id": "concept-corrupt",
            "canvas_path": "/test/canvas.canvas",
        }
        response = client.post("/api/v1/multimodal/upload", files=files, data=data)
        # Should either accept (magic bytes match) or reject gracefully - NOT 500
        assert response.status_code != 500, (
            f"Corrupted PNG should not cause 500 error: {response.text[:200]}"
        )


# =============================================================================
# AC 35.9.2: Relationship Verification Tests
# =============================================================================

class TestMultimodalRelationshipE2E:
    """E2E tests for concept-media relationship verification."""

    def test_upload_creates_concept_association(self, client: TestClient, test_image_file: bytes):
        """Test upload creates association with specified concept."""
        concept_id = "concept-relation-001"
        files = {"file": ("relation_test.png", io.BytesIO(test_image_file), "image/png")}
        data = {
            "related_concept_id": concept_id,
            "canvas_path": "/test/canvas/relations.canvas",
        }
        response = client.post("/api/v1/multimodal/upload", files=files, data=data)

        assert response.status_code == 201, f"Expected 201 Created, got {response.status_code}: {response.text}"
        result = response.json()
        assert result["content"]["related_concept_id"] == concept_id

    def test_get_by_concept_returns_associated_media(self, client: TestClient, test_image_file: bytes):
        """Test GET /api/v1/multimodal/by-concept/{concept_id} returns associated media."""
        concept_id = "concept-query-001"
        files = {"file": ("query_test.png", io.BytesIO(test_image_file), "image/png")}
        data = {
            "related_concept_id": concept_id,
            "canvas_path": "/test/canvas/query.canvas",
        }
        upload_response = client.post("/api/v1/multimodal/upload", files=files, data=data)
        assert upload_response.status_code == 201, (
            f"Setup upload failed: {upload_response.status_code}: {upload_response.text}"
        )

        response = client.get(f"/api/v1/multimodal/by-concept/{concept_id}")

        assert response.status_code == 200
        result = response.json()
        assert "items" in result
        assert "total" in result

    def test_multiple_media_per_concept(self, client: TestClient, test_image_file: bytes, test_pdf_file: bytes):
        """Test concept can have multiple associated media items."""
        concept_id = "concept-multi-001"
        canvas_path = "/test/canvas/multi.canvas"

        files1 = {"file": ("multi_image.png", io.BytesIO(test_image_file), "image/png")}
        data1 = {"related_concept_id": concept_id, "canvas_path": canvas_path}
        resp1 = client.post("/api/v1/multimodal/upload", files=files1, data=data1)

        files2 = {"file": ("multi_doc.pdf", io.BytesIO(test_pdf_file), "application/pdf")}
        data2 = {"related_concept_id": concept_id, "canvas_path": canvas_path}
        resp2 = client.post("/api/v1/multimodal/upload", files=files2, data=data2)

        assert resp1.status_code == 201, f"Setup upload 1 failed: {resp1.status_code}: {resp1.text}"
        assert resp2.status_code == 201, f"Setup upload 2 failed: {resp2.status_code}: {resp2.text}"

        response = client.get(f"/api/v1/multimodal/by-concept/{concept_id}")

        assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"
        result = response.json()
        assert result["total"] >= 2
