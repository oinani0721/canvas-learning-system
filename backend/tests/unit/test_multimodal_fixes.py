# Canvas Learning System - EPIC-35 Blocking Fixes Unit Tests
"""
Tests for EPIC-35 三个阻塞级修复:
1. JSON 文件持久化 (问题1)
2. 缩略图生成 (问题2)
3. 向量搜索降级透明化 (问题3)
4. DI 迁移到 dependencies.py (附加)
"""

import io
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.models.multimodal_schemas import (
    MultimodalHealthResponse,
    MultimodalMediaType,
    MultimodalMetadataSchema,
    MultimodalSearchRequest,
    MultimodalSearchResponse,
)
from app.services.multimodal_service import (
    MultimodalService,
    reset_multimodal_service,
)


@pytest.fixture
def tmp_storage(tmp_path):
    """Create a temporary storage directory for tests."""
    return str(tmp_path)


@pytest.fixture
def service(tmp_storage):
    """Create a fresh MultimodalService with tmp storage."""
    reset_multimodal_service()
    svc = MultimodalService(storage_base_path=tmp_storage)
    try:
        yield svc
    finally:
        reset_multimodal_service()


# =============================================================================
# 问题1: JSON 文件持久化
# =============================================================================

class TestJSONPersistence:
    """Test JSON file persistence for content index."""

    @pytest.mark.asyncio
    async def test_upload_creates_index_file(self, service, tmp_storage):
        """After upload, content_index.json must exist."""
        await service.initialize()

        # Create a small test image file
        img_path = Path(tmp_storage) / "image"
        img_path.mkdir(parents=True, exist_ok=True)

        result = await service.upload_file(
            file_bytes=b"\xff\xd8\xff\xe0" + b"\x00" * 100,
            filename="test.jpg",
            content_type="image/jpeg",
            file_size=104,
            related_concept_id="node-1",
            canvas_path="test.canvas",
            description="test image",
        )

        index_path = Path(tmp_storage) / "content_index.json"
        assert index_path.exists(), "content_index.json must exist after upload"

        # Verify content
        data = json.loads(index_path.read_text(encoding="utf-8"))
        assert "items" in data
        assert result.content.id in data["items"]
        assert data["items"][result.content.id]["description"] == "test image"

    @pytest.mark.asyncio
    async def test_persistence_survives_restart(self, tmp_storage):
        """Data persisted by one service instance must be loadable by another."""
        # First instance: upload a file
        svc1 = MultimodalService(storage_base_path=tmp_storage)
        await svc1.initialize()

        result = await svc1.upload_file(
            file_bytes=b"\xff\xd8\xff\xe0" + b"\x00" * 50,
            filename="persist_test.jpg",
            content_type="image/jpeg",
            file_size=54,
            related_concept_id="node-persist",
            canvas_path="test.canvas",
        )
        content_id = result.content.id

        # Second instance: should load persisted data
        svc2 = MultimodalService(storage_base_path=tmp_storage)
        assert content_id in svc2._content_store, \
            "New service instance must load previously persisted content"
        assert svc2._content_store[content_id]["related_concept_id"] == "node-persist"

    @pytest.mark.asyncio
    async def test_delete_updates_index(self, service, tmp_storage):
        """Deleting content must update the index file."""
        await service.initialize()

        result = await service.upload_file(
            file_bytes=b"\xff\xd8\xff\xe0" + b"\x00" * 50,
            filename="delete_test.jpg",
            content_type="image/jpeg",
            file_size=54,
            related_concept_id="node-del",
            canvas_path="test.canvas",
        )
        content_id = result.content.id

        await service.delete_content(content_id)

        index_path = Path(tmp_storage) / "content_index.json"
        data = json.loads(index_path.read_text(encoding="utf-8"))
        assert content_id not in data["items"], \
            "Deleted content must be removed from index"

    @pytest.mark.asyncio
    async def test_update_persists(self, service, tmp_storage):
        """Updating content must persist changes."""
        await service.initialize()
        from app.models.multimodal_schemas import MultimodalUpdateRequest

        result = await service.upload_file(
            file_bytes=b"\xff\xd8\xff\xe0" + b"\x00" * 50,
            filename="update_test.jpg",
            content_type="image/jpeg",
            file_size=54,
            related_concept_id="node-upd",
            canvas_path="test.canvas",
            description="original",
        )
        content_id = result.content.id

        await service.update_content(
            content_id,
            MultimodalUpdateRequest(description="updated"),
        )

        index_path = Path(tmp_storage) / "content_index.json"
        data = json.loads(index_path.read_text(encoding="utf-8"))
        assert data["items"][content_id]["description"] == "updated"

    def test_no_multimodal_store_logs_warning(self, tmp_storage, caplog):
        """When multimodal_store is None, service must log a warning."""
        import logging
        with caplog.at_level(logging.WARNING):
            svc = MultimodalService(storage_base_path=tmp_storage)

        assert any(
            "MultimodalStore not available" in rec.message
            for rec in caplog.records
        ), "Must warn when MultimodalStore is not provided"


# =============================================================================
# 问题2: 缩略图生成
# =============================================================================

class TestThumbnailGeneration:
    """Test thumbnail generation for image uploads."""

    @pytest.mark.asyncio
    async def test_thumbnail_generated_for_image(self, service, tmp_storage):
        """Uploading an image must generate a thumbnail."""
        await service.initialize()

        # Create a minimal valid JPEG-like content
        # Use PIL to create a real test image
        try:
            from PIL import Image
        except ImportError:
            pytest.skip("Pillow not installed")

        # Create a test image in memory
        img = Image.new("RGB", (200, 200), color="red")
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        buf.seek(0)
        img_bytes = buf.read()
        buf.seek(0)

        result = await service.upload_file(
            file_bytes=img_bytes,
            filename="thumb_test.jpg",
            content_type="image/jpeg",
            file_size=len(img_bytes),
            related_concept_id="node-thumb",
            canvas_path="test.canvas",
        )

        assert result.thumbnail_generated is True, \
            "thumbnail_generated must be True for image uploads"
        assert result.content.thumbnail_path is not None, \
            "thumbnail_path must be set"
        assert Path(result.content.thumbnail_path).exists(), \
            "Thumbnail file must exist on disk"

    @pytest.mark.asyncio
    async def test_thumbnail_not_generated_for_pdf(self, service, tmp_storage):
        """PDF uploads should not generate thumbnails (no PIL support for PDF)."""
        await service.initialize()

        result = await service.upload_file(
            file_bytes=b"%PDF-1.4\n" + b"\x00" * 50,
            filename="test.pdf",
            content_type="application/pdf",
            file_size=59,
            related_concept_id="node-pdf",
            canvas_path="test.canvas",
        )

        assert result.thumbnail_generated is False

    @pytest.mark.asyncio
    async def test_thumbnail_failure_does_not_block_upload(self, service, tmp_storage):
        """If PIL fails, upload must still succeed."""
        await service.initialize()

        with patch(
            "app.services.multimodal_service.MultimodalService._generate_thumbnail",
            return_value=None,
        ):
            result = await service.upload_file(
                file_bytes=b"\xff\xd8\xff\xe0" + b"\x00" * 50,
                filename="fail_thumb.jpg",
                content_type="image/jpeg",
                file_size=54,
                related_concept_id="node-fail",
                canvas_path="test.canvas",
            )

        assert result.thumbnail_generated is False
        assert result.content.id is not None  # Upload still succeeded


# =============================================================================
# 问题3: 向量搜索降级透明化
# =============================================================================

class TestSearchModeTransparency:
    """Test that search mode is transparent in responses."""

    def test_search_response_has_search_mode_field(self):
        """MultimodalSearchResponse must have search_mode field."""
        resp = MultimodalSearchResponse(
            items=[],
            total=0,
            query_processed=True,
            search_mode="vector",
        )
        assert resp.search_mode == "vector"

        resp2 = MultimodalSearchResponse(
            items=[],
            total=0,
            query_processed=False,
            search_mode="text",
        )
        assert resp2.search_mode == "text"

    def test_search_mode_default_is_vector(self):
        """Default search_mode should be 'vector'."""
        resp = MultimodalSearchResponse(items=[], total=0)
        assert resp.search_mode == "vector"

    def test_search_mode_validation(self):
        """search_mode must be 'vector' or 'text'."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            MultimodalSearchResponse(
                items=[], total=0, search_mode="invalid"
            )

    @pytest.mark.asyncio
    async def test_text_fallback_sets_search_mode_text(self, service, tmp_storage):
        """When embedding is unavailable, search_mode must be 'text'."""
        await service.initialize()

        # Upload some content to search through
        await service.upload_file(
            file_bytes=b"\xff\xd8\xff\xe0" + b"\x00" * 50,
            filename="search_test.jpg",
            content_type="image/jpeg",
            file_size=54,
            related_concept_id="node-search",
            canvas_path="test.canvas",
            description="diagram of neural network",
        )

        request = MultimodalSearchRequest(query="neural network")
        result = await service.search(request)

        # Without embedding service, it must fallback to text
        assert result.search_mode == "text", \
            "search_mode must be 'text' when embedding is unavailable"

    @pytest.mark.asyncio
    async def test_text_fallback_logs_warning(self, service, tmp_storage, caplog):
        """Embedding unavailability must produce a WARNING log."""
        import logging

        await service.initialize()

        request = MultimodalSearchRequest(query="anything")

        with caplog.at_level(logging.WARNING):
            await service.search(request)

        assert any(
            "降级为文本搜索" in rec.message
            for rec in caplog.records
        ), "Must log WARNING about text search fallback"


# =============================================================================
# 附加: DI 迁移
# =============================================================================

class TestDIMigration:
    """Test that DI is properly moved to dependencies.py."""

    def test_multimodal_service_dep_exists_in_dependencies(self):
        """MultimodalServiceDep must be importable from dependencies."""
        from app.dependencies import MultimodalServiceDep
        assert MultimodalServiceDep is not None

    def test_get_multimodal_service_dep_exists(self):
        """get_multimodal_service_dep must be importable from dependencies."""
        from app.dependencies import get_multimodal_service_dep
        assert callable(get_multimodal_service_dep)

    def test_multimodal_router_does_not_define_get_service(self):
        """multimodal.py must NOT define its own get_service function."""
        import app.api.v1.endpoints.multimodal as mm_module
        assert not hasattr(mm_module, "get_service"), \
            "get_service must be removed from multimodal.py (moved to dependencies.py)"


# =============================================================================
# Story 35.11: 多模态搜索降级透明化
# =============================================================================

class TestHealthDegradationTransparency:
    """Story 35.11 AC 35.11.3: Health endpoint shows storage backend status."""

    def test_health_response_has_degradation_fields(self):
        """MultimodalHealthResponse must include storage_backend, vector_search_available, capability_level."""
        resp = MultimodalHealthResponse(
            status="healthy",
            lancedb_connected=True,
            neo4j_connected=True,
            storage_path_writable=True,
            total_items=5,
            storage_backend="multimodal_store",
            vector_search_available=True,
            capability_level="full",
        )
        assert resp.storage_backend == "multimodal_store"
        assert resp.vector_search_available is True
        assert resp.capability_level == "full"

    def test_health_response_degraded_defaults(self):
        """Default values should reflect degraded state (JSON fallback)."""
        resp = MultimodalHealthResponse(
            status="degraded",
            lancedb_connected=False,
            neo4j_connected=False,
            storage_path_writable=True,
            total_items=0,
        )
        assert resp.storage_backend == "json_fallback"
        assert resp.vector_search_available is False
        assert resp.capability_level == "degraded"

    def test_health_response_validation_storage_backend(self):
        """storage_backend must be 'multimodal_store' or 'json_fallback'."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            MultimodalHealthResponse(
                status="healthy",
                lancedb_connected=True,
                neo4j_connected=True,
                storage_path_writable=True,
                storage_backend="invalid_backend",
            )

    def test_health_response_validation_capability_level(self):
        """capability_level must be 'full' or 'degraded'."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            MultimodalHealthResponse(
                status="healthy",
                lancedb_connected=True,
                neo4j_connected=True,
                storage_path_writable=True,
                capability_level="partial",
            )

    @pytest.mark.asyncio
    async def test_service_health_without_store_returns_degraded(self, service):
        """Service without multimodal_store must return degraded capability."""
        await service.initialize()

        result = await service.get_health_status()

        assert result.storage_backend == "json_fallback"
        assert result.vector_search_available is False
        assert result.capability_level == "degraded"

    @pytest.mark.asyncio
    async def test_service_health_with_store_returns_full(self, tmp_storage):
        """Service with multimodal_store and lancedb must return full capability."""
        from unittest.mock import AsyncMock

        reset_multimodal_service()
        mock_store = MagicMock()
        mock_store.health_check = AsyncMock(
            return_value={"lancedb": True, "neo4j": True}
        )

        svc = MultimodalService(
            storage_base_path=tmp_storage,
            multimodal_store=mock_store,
        )
        await svc.initialize()

        result = await svc.get_health_status()

        assert result.storage_backend == "multimodal_store"
        assert result.vector_search_available is True
        assert result.capability_level == "full"
