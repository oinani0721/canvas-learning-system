"""
Story 35.12 AC 35.12.3 & 35.12.4: 真实持久化集成测试 (Service 层)

测试多模态内容的完整生命周期：Upload → Search → Delete，
使用真实文件系统 I/O（非 mock）。

⚠️ 测试范围：直接调用 MultimodalService 方法（非 HTTP 客户端）。
   验证核心持久化逻辑和文件系统 I/O，不覆盖路由、请求验证、序列化。
   HTTP 层验证参见 tests/e2e/test_multimodal_workflow.py。

AC 35.12.3: Upload → 验证存储 → Search → Delete → 验证清理
AC 35.12.4: 数据在服务重启后仍然存在
"""

import asyncio
import json
from pathlib import Path

import pytest

from app.models.multimodal_schemas import (
    MultimodalMediaType,
    MultimodalMetadataSchema,
)
from app.services.multimodal_service import (
    ContentNotFoundError,
    MultimodalService,
)
from tests.fixtures.multimodal import make_minimal_pdf, make_minimal_png

pytestmark = [
    pytest.mark.integration,
    pytest.mark.asyncio,
]


# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def real_storage_dir(tmp_path):
    """使用 tmp_path 创建真实临时目录，不使用 mock.

    AC 35.12.3: 每一步使用真实文件系统读写.
    """
    storage = tmp_path / ".canvas-learning" / "multimodal"
    storage.mkdir(parents=True)
    return storage


@pytest.fixture
def service(real_storage_dir) -> MultimodalService:
    """创建指向真实临时目录的 MultimodalService 实例."""
    svc = MultimodalService(storage_base_path=str(real_storage_dir))
    return svc


@pytest.fixture
def png_bytes() -> bytes:
    """最小有效 PNG（69 bytes）."""
    return make_minimal_png()


@pytest.fixture
def pdf_bytes() -> bytes:
    """最小有效 PDF（329 bytes）."""
    return make_minimal_pdf()


# ═══════════════════════════════════════════════════════════════════════════════
# AC 35.12.3: 完整生命周期 Upload → Search → Delete
# ═══════════════════════════════════════════════════════════════════════════════


class TestFullLifecycleRealPersistence:
    """AC 35.12.3: 真实持久化端到端测试."""

    async def test_upload_creates_file_on_disk(self, service, png_bytes, real_storage_dir):
        """Step 1: Upload — 验证文件真的写入磁盘."""
        await service.initialize()

        result = await service.upload_file(
            file_bytes=png_bytes,
            filename="test_upload.png",
            content_type="image/png",
            file_size=len(png_bytes),
            related_concept_id="concept-001",
            description="Test image for persistence",
        )

        content_id = result.content.id
        assert content_id is not None

        # 验证: 文件在磁盘上存在
        uploaded_files = list(real_storage_dir.rglob("*.png"))
        assert len(uploaded_files) >= 1, (
            f"Expected at least 1 PNG on disk, found {len(uploaded_files)}"
        )

        # 验证: 文件内容匹配
        actual_bytes = uploaded_files[0].read_bytes()
        assert actual_bytes == png_bytes

    async def test_upload_persists_to_json_index(self, service, png_bytes, real_storage_dir):
        """Upload 后 content_index.json 包含新条目."""
        await service.initialize()

        result = await service.upload_file(
            file_bytes=png_bytes,
            filename="indexed.png",
            content_type="image/png",
            file_size=len(png_bytes),
            related_concept_id="concept-idx",
        )

        index_path = real_storage_dir / "content_index.json"
        assert index_path.exists(), "content_index.json not created"

        index_data = json.loads(index_path.read_text(encoding="utf-8"))
        assert result.content.id in index_data["items"]

    async def test_search_finds_uploaded_content(self, service, png_bytes):
        """Step 2: Search — 验证能找到刚上传的内容 (text fallback)."""
        await service.initialize()

        result = await service.upload_file(
            file_bytes=png_bytes,
            filename="searchable.png",
            content_type="image/png",
            file_size=len(png_bytes),
            related_concept_id="concept-search",
            description="数学公式推导",
        )
        content_id = result.content.id

        # Text fallback search
        from app.models.multimodal_schemas import MultimodalSearchRequest

        search_req = MultimodalSearchRequest(
            query="数学",
            top_k=10,
            min_score=0.0,  # low threshold for text match
        )
        search_result = await service.search(request=search_req)

        found_ids = [item.id for item in search_result.items]
        assert content_id in found_ids, (
            f"Uploaded content {content_id} not found in search results: {found_ids}"
        )
        assert search_result.search_mode == "text"

    async def test_delete_removes_file_from_disk(self, service, png_bytes, real_storage_dir):
        """Step 3: Delete — 验证文件从磁盘删除."""
        await service.initialize()

        result = await service.upload_file(
            file_bytes=png_bytes,
            filename="to_delete.png",
            content_type="image/png",
            file_size=len(png_bytes),
            related_concept_id="concept-del",
        )
        content_id = result.content.id

        # Verify file exists before delete
        uploaded_files_before = list(real_storage_dir.rglob("*.png"))
        assert len(uploaded_files_before) >= 1

        # Delete — returns None (matches HTTP 204 No Content)
        await service.delete_content(content_id)

        # 验证: 文件已从磁盘删除
        # (只有 to_delete 的 PNG 应被删除)
        remaining = [
            f for f in real_storage_dir.rglob("*.png")
            if f.name != ".health_check"
        ]
        assert len(remaining) == 0, (
            f"Expected 0 PNG files after delete, found {len(remaining)}: {remaining}"
        )

    async def test_delete_removes_from_json_index(self, service, png_bytes, real_storage_dir):
        """Delete 后 content_index.json 不再包含该条目."""
        await service.initialize()

        result = await service.upload_file(
            file_bytes=png_bytes,
            filename="idx_del.png",
            content_type="image/png",
            file_size=len(png_bytes),
            related_concept_id="concept-idx-del",
        )
        content_id = result.content.id

        await service.delete_content(content_id)

        index_path = real_storage_dir / "content_index.json"
        index_data = json.loads(index_path.read_text(encoding="utf-8"))
        assert content_id not in index_data["items"]

    async def test_get_after_delete_raises_not_found(self, service, png_bytes):
        """Delete 后 get_content 抛出 ContentNotFoundError."""
        await service.initialize()

        result = await service.upload_file(
            file_bytes=png_bytes,
            filename="get_after_del.png",
            content_type="image/png",
            file_size=len(png_bytes),
            related_concept_id="concept-gad",
        )
        content_id = result.content.id

        await service.delete_content(content_id)

        with pytest.raises(ContentNotFoundError):
            await service.get_content(content_id)

    async def test_full_lifecycle_upload_search_delete(
        self, service, png_bytes, real_storage_dir
    ):
        """完整 Upload → Verify → Search → Delete → Verify 流程."""
        await service.initialize()

        # ── Upload ──
        upload_result = await service.upload_file(
            file_bytes=png_bytes,
            filename="lifecycle.png",
            content_type="image/png",
            file_size=len(png_bytes),
            related_concept_id="concept-lifecycle",
            description="lifecycle test image",
        )
        content_id = upload_result.content.id

        # ── Verify on disk ──
        pngs = list(real_storage_dir.rglob("*.png"))
        assert len(pngs) >= 1

        # ── Get ──
        content = await service.get_content(content_id)
        assert content.id == content_id
        assert content.related_concept_id == "concept-lifecycle"

        # ── Search ──
        from app.models.multimodal_schemas import MultimodalSearchRequest

        search_result = await service.search(
            request=MultimodalSearchRequest(query="lifecycle", min_score=0.0)
        )
        assert any(i.id == content_id for i in search_result.items)

        # ── Delete (returns None — HTTP 204) ──
        await service.delete_content(content_id)

        # ── Verify cleanup ──
        remaining = [
            f for f in real_storage_dir.rglob("*.png")
            if f.name != ".health_check"
        ]
        assert len(remaining) == 0

        with pytest.raises(ContentNotFoundError):
            await service.get_content(content_id)


# ═══════════════════════════════════════════════════════════════════════════════
# AC 35.12.4: 持久化跨重启验证 (D1 维度)
# ═══════════════════════════════════════════════════════════════════════════════


class TestDataSurvivesServiceRestart:
    """AC 35.12.4: 数据在服务重启后仍然存在."""

    async def test_data_survives_service_restart(self, real_storage_dir, png_bytes):
        """验证数据在服务重启后仍然存在."""
        # 第一个 service 实例: 上传
        service1 = MultimodalService(storage_base_path=str(real_storage_dir))
        await service1.initialize()

        upload_result = await service1.upload_file(
            file_bytes=png_bytes,
            filename="survive.png",
            content_type="image/png",
            file_size=len(png_bytes),
            related_concept_id="concept-survive",
            description="Should survive restart",
        )
        content_id = upload_result.content.id

        # 确认 JSON index 已持久化
        index_path = real_storage_dir / "content_index.json"
        assert index_path.exists()

        # 模拟重启: 创建新实例（从 JSON 加载）
        service2 = MultimodalService(storage_base_path=str(real_storage_dir))
        await service2.initialize()

        # 验证: 数据仍然存在
        content = await service2.get_content(content_id)
        assert content is not None
        assert content.id == content_id
        assert content.related_concept_id == "concept-survive"
        assert content.description == "Should survive restart"

    async def test_multiple_items_survive_restart(self, real_storage_dir, png_bytes, pdf_bytes):
        """多个不同类型的内容在重启后全部保留."""
        service1 = MultimodalService(storage_base_path=str(real_storage_dir))
        await service1.initialize()

        # Upload PNG
        png_result = await service1.upload_file(
            file_bytes=png_bytes,
            filename="multi_restart.png",
            content_type="image/png",
            file_size=len(png_bytes),
            related_concept_id="concept-multi",
            description="PNG for restart test",
        )

        # Upload PDF
        pdf_result = await service1.upload_file(
            file_bytes=pdf_bytes,
            filename="multi_restart.pdf",
            content_type="application/pdf",
            file_size=len(pdf_bytes),
            related_concept_id="concept-multi",
            description="PDF for restart test",
        )

        # 模拟重启
        service2 = MultimodalService(storage_base_path=str(real_storage_dir))
        await service2.initialize()

        # 验证两个都存在
        png_content = await service2.get_content(png_result.content.id)
        assert png_content.media_type == MultimodalMediaType.IMAGE

        pdf_content = await service2.get_content(pdf_result.content.id)
        assert pdf_content.media_type == MultimodalMediaType.PDF

        # List 验证总数
        list_result = await service2.list_content()
        assert list_result.total == 2

    async def test_deleted_items_stay_deleted_after_restart(
        self, real_storage_dir, png_bytes
    ):
        """删除的内容在重启后不会复活."""
        service1 = MultimodalService(storage_base_path=str(real_storage_dir))
        await service1.initialize()

        result = await service1.upload_file(
            file_bytes=png_bytes,
            filename="del_restart.png",
            content_type="image/png",
            file_size=len(png_bytes),
            related_concept_id="concept-dr",
        )
        content_id = result.content.id

        # 删除
        await service1.delete_content(content_id)

        # 模拟重启
        service2 = MultimodalService(storage_base_path=str(real_storage_dir))
        await service2.initialize()

        # 确认仍然不存在
        with pytest.raises(ContentNotFoundError):
            await service2.get_content(content_id)


# ═══════════════════════════════════════════════════════════════════════════════
# 并发上传测试 (Story 35.12 Task 3.5)
# ═══════════════════════════════════════════════════════════════════════════════


class TestConcurrentUploads:
    """并发上传不会导致数据损坏."""

    async def test_concurrent_uploads_no_data_loss(self, service, real_storage_dir):
        """多文件同时上传后，所有文件都存在."""
        await service.initialize()

        async def upload_one(index: int):
            png = make_minimal_png()
            return await service.upload_file(
                file_bytes=png,
                filename=f"concurrent_{index}.png",
                content_type="image/png",
                file_size=len(png),
                related_concept_id=f"concept-{index}",
                description=f"Concurrent upload {index}",
            )

        # 并发上传 5 个文件
        results = await asyncio.gather(*[upload_one(i) for i in range(5)])

        # 所有 5 个都成功
        assert len(results) == 5
        ids = {r.content.id for r in results}
        assert len(ids) == 5, "Duplicate content IDs generated"

        # 磁盘上有 5 个 PNG
        pngs = list(real_storage_dir.rglob("*.png"))
        assert len(pngs) == 5

        # JSON index 包含 5 个条目
        index_data = json.loads(
            (real_storage_dir / "content_index.json").read_text(encoding="utf-8")
        )
        assert len(index_data["items"]) == 5


# ═══════════════════════════════════════════════════════════════════════════════
# PDF 文件持久化测试
# ═══════════════════════════════════════════════════════════════════════════════


class TestPdfPersistence:
    """PDF 文件的持久化测试."""

    async def test_pdf_upload_and_retrieve(self, service, pdf_bytes, real_storage_dir):
        """PDF 上传、磁盘写入、获取完整流程."""
        await service.initialize()

        result = await service.upload_file(
            file_bytes=pdf_bytes,
            filename="lecture.pdf",
            content_type="application/pdf",
            file_size=len(pdf_bytes),
            related_concept_id="concept-pdf",
            description="Lecture notes",
        )

        # 磁盘验证
        pdfs = list(real_storage_dir.rglob("*.pdf"))
        assert len(pdfs) == 1
        assert pdfs[0].read_bytes() == pdf_bytes

        # API 验证
        content = await service.get_content(result.content.id)
        assert content.media_type == MultimodalMediaType.PDF
        assert content.description == "Lecture notes"


# ═══════════════════════════════════════════════════════════════════════════════
# Update 持久化测试
# ═══════════════════════════════════════════════════════════════════════════════


class TestUpdatePersistence:
    """Update 操作的持久化验证."""

    async def test_update_persists_to_json_and_survives_restart(
        self, real_storage_dir, png_bytes
    ):
        """Update 后的 metadata 在重启后保留."""
        service1 = MultimodalService(storage_base_path=str(real_storage_dir))
        await service1.initialize()

        result = await service1.upload_file(
            file_bytes=png_bytes,
            filename="update_test.png",
            content_type="image/png",
            file_size=len(png_bytes),
            related_concept_id="concept-up",
            description="Original description",
        )
        content_id = result.content.id

        # Update
        from app.models.multimodal_schemas import MultimodalUpdateRequest

        await service1.update_content(
            content_id,
            MultimodalUpdateRequest(description="Updated description"),
        )

        # 模拟重启
        service2 = MultimodalService(storage_base_path=str(real_storage_dir))
        await service2.initialize()

        content = await service2.get_content(content_id)
        assert content.description == "Updated description"
