# Story 34.13: Real E2E tests for textbook mount sync path
# [Source: docs/epics/EPIC-34-COMPLETE-ACTIVATION.md - Story 34.13]
"""
True end-to-end tests for textbook mounting using httpx.AsyncClient.

Unlike test_textbook_mount_flow.py (which calls services directly or mocks them),
these tests exercise the FULL HTTP path:
  HTTP POST → endpoint handler → TextbookContextService → .canvas-links.json write → read-back

AC1: httpx.AsyncClient + ASGITransport (not TestClient + mock)
AC2: Full sync path: request → processing → .canvas-links.json write → read-back
AC3: PDF/Markdown/Canvas each one E2E case
AC4: Existing tests in integration/ and e2e/test_textbook_mount_flow.py untouched
"""

import json
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.textbook_context_service import (
    TextbookContextService,
    get_textbook_context_service,
    reset_textbook_context_service,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def e2e_canvas_base(tmp_path):
    """Create a temporary canvas base directory for E2E tests."""
    base = tmp_path / "vault"
    base.mkdir()
    return base


@pytest.fixture(autouse=True)
def _reset_textbook_singleton():
    """Reset the TextbookContextService singleton before and after each test.

    Ensures each test gets a fresh service instance pointing to its own tmp_path.
    """
    reset_textbook_context_service()
    yield
    reset_textbook_context_service()


@pytest.fixture
async def e2e_client(e2e_canvas_base):
    """Async HTTP client wired to a real TextbookContextService using tmp_path.

    Patches get_textbook_context_service so the endpoint creates a service
    pointing at the temp directory, enabling real filesystem writes without
    touching the user's vault.
    """
    # Pre-create the singleton with our temp base path so the endpoint uses it
    import app.services.textbook_context_service as tcs_mod

    service = TextbookContextService(canvas_base_path=str(e2e_canvas_base))
    tcs_mod._textbook_context_service = service

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://e2e-test") as client:
        yield client


# ============================================================================
# Helpers
# ============================================================================


def _read_canvas_links(base: Path, canvas_path: str) -> dict:
    """Read and parse the .canvas-links.json for a given canvas_path."""
    # canvas_path like "数学/离散数学.canvas" → directory is "数学"
    canvas_dir = Path(canvas_path).parent
    config_file = base / canvas_dir / ".canvas-links.json"
    assert config_file.exists(), f".canvas-links.json not found at {config_file}"
    return json.loads(config_file.read_text(encoding="utf-8"))


# ============================================================================
# AC3: PDF E2E — sync-mount → .canvas-links.json write → read-back
# ============================================================================


class TestPdfMountE2E:
    """E2E: PDF textbook mount through full HTTP path."""

    @pytest.mark.asyncio
    async def test_pdf_sync_mount_creates_canvas_links_json(
        self, e2e_client: AsyncClient, e2e_canvas_base: Path
    ):
        """POST /api/v1/textbook/sync-mount (PDF) writes .canvas-links.json."""
        # Arrange
        canvas_path = "数学/线性代数.canvas"
        (e2e_canvas_base / "数学").mkdir(parents=True, exist_ok=True)

        request_body = {
            "canvas_path": canvas_path,
            "textbook": {
                "id": "pdf-la-001",
                "path": "教材/线性代数教程.pdf",
                "name": "线性代数教程",
                "type": "pdf",
                "sections": [
                    {"id": "s1", "title": "向量空间", "level": 1, "preview": "", "start_offset": 0, "end_offset": 0, "page_number": 12},
                    {"id": "s2", "title": "线性变换", "level": 1, "preview": "", "start_offset": 0, "end_offset": 0, "page_number": 45},
                ],
            },
        }

        # Act — real HTTP request through the full stack
        response = await e2e_client.post("/api/v1/textbook/sync-mount", json=request_body)

        # Assert — HTTP response
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["success"] is True
        assert data["association_id"] == "mount-pdf-la-001"

        # Assert — filesystem read-back
        config = _read_canvas_links(e2e_canvas_base, canvas_path)
        assert config["version"] == "1.0.0"
        assert len(config["associations"]) == 1

        assoc = config["associations"][0]
        assert assoc["association_id"] == "mount-pdf-la-001"
        assert assoc["file_type"] == "pdf"
        assert assoc["target_canvas"] == "教材/线性代数教程.pdf"
        assert len(assoc["sections"]) == 2
        assert assoc["sections"][0]["page_number"] == 12
        assert assoc["sections"][1]["page_number"] == 45


# ============================================================================
# AC3: Markdown E2E — sync-mount → .canvas-links.json write → read-back
# ============================================================================


class TestMarkdownMountE2E:
    """E2E: Markdown textbook mount through full HTTP path."""

    @pytest.mark.asyncio
    async def test_markdown_sync_mount_creates_canvas_links_json(
        self, e2e_client: AsyncClient, e2e_canvas_base: Path
    ):
        """POST /api/v1/textbook/sync-mount (Markdown) writes .canvas-links.json."""
        # Arrange
        canvas_path = "物理/力学.canvas"
        (e2e_canvas_base / "物理").mkdir(parents=True, exist_ok=True)

        request_body = {
            "canvas_path": canvas_path,
            "textbook": {
                "id": "md-physics-001",
                "path": "笔记/牛顿力学.md",
                "name": "牛顿力学笔记",
                "type": "markdown",
                "sections": [],
            },
        }

        # Act
        response = await e2e_client.post("/api/v1/textbook/sync-mount", json=request_body)

        # Assert — HTTP response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["association_id"] == "mount-md-physics-001"

        # Assert — filesystem read-back
        config = _read_canvas_links(e2e_canvas_base, canvas_path)
        assert len(config["associations"]) == 1

        assoc = config["associations"][0]
        assert assoc["association_id"] == "mount-md-physics-001"
        assert assoc["file_type"] == "markdown"
        assert assoc["target_canvas"] == "笔记/牛顿力学.md"
        # Markdown has no PDF sections
        assert assoc["sections"] == []


# ============================================================================
# AC3: Canvas E2E — sync-mount → .canvas-links.json write → read-back
# ============================================================================


class TestCanvasMountE2E:
    """E2E: Canvas-type textbook mount through full HTTP path."""

    @pytest.mark.asyncio
    async def test_canvas_sync_mount_creates_canvas_links_json(
        self, e2e_client: AsyncClient, e2e_canvas_base: Path
    ):
        """POST /api/v1/textbook/sync-mount (Canvas) writes .canvas-links.json."""
        # Arrange
        canvas_path = "化学/有机化学.canvas"
        (e2e_canvas_base / "化学").mkdir(parents=True, exist_ok=True)

        request_body = {
            "canvas_path": canvas_path,
            "textbook": {
                "id": "canvas-chem-001",
                "path": "概念图/化学基础.canvas",
                "name": "化学基础概念图",
                "type": "canvas",
                "sections": [],
            },
        }

        # Act
        response = await e2e_client.post("/api/v1/textbook/sync-mount", json=request_body)

        # Assert — HTTP response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["association_id"] == "mount-canvas-chem-001"

        # Assert — filesystem read-back
        config = _read_canvas_links(e2e_canvas_base, canvas_path)
        assert len(config["associations"]) == 1

        assoc = config["associations"][0]
        assert assoc["association_id"] == "mount-canvas-chem-001"
        assert assoc["file_type"] == "canvas"
        assert assoc["target_canvas"] == "概念图/化学基础.canvas"


# ============================================================================
# AC2: Unmount E2E — mount → unmount → read-back verify removal
# ============================================================================


class TestUnmountE2E:
    """E2E: Unmount textbook through full HTTP path."""

    @pytest.mark.asyncio
    async def test_unmount_removes_association_from_canvas_links(
        self, e2e_client: AsyncClient, e2e_canvas_base: Path
    ):
        """POST /unmount removes association and .canvas-links.json reflects it."""
        # Arrange — first mount a textbook
        canvas_path = "测试/unmount.canvas"
        (e2e_canvas_base / "测试").mkdir(parents=True, exist_ok=True)

        mount_body = {
            "canvas_path": canvas_path,
            "textbook": {
                "id": "unmount-test-001",
                "path": "教材/待卸载.pdf",
                "name": "待卸载教材",
                "type": "pdf",
                "sections": [],
            },
        }
        mount_resp = await e2e_client.post("/api/v1/textbook/sync-mount", json=mount_body)
        assert mount_resp.status_code == 200

        # Verify mount succeeded on disk
        config_before = _read_canvas_links(e2e_canvas_base, canvas_path)
        assert len(config_before["associations"]) == 1

        # Act — unmount
        unmount_body = {
            "canvas_path": canvas_path,
            "textbook_id": "mount-unmount-test-001",
        }
        unmount_resp = await e2e_client.post("/api/v1/textbook/unmount", json=unmount_body)

        # Assert — HTTP response
        assert unmount_resp.status_code == 200
        assert unmount_resp.json()["success"] is True

        # Assert — filesystem read-back: association removed
        config_after = _read_canvas_links(e2e_canvas_base, canvas_path)
        matching = [
            a for a in config_after["associations"]
            if a["association_id"] == "mount-unmount-test-001"
        ]
        assert len(matching) == 0


# ============================================================================
# AC2: List mounted E2E — mount multiple → list → verify
# ============================================================================


class TestListMountedE2E:
    """E2E: List mounted textbooks through full HTTP path."""

    @pytest.mark.asyncio
    async def test_list_returns_all_mounted_textbooks(
        self, e2e_client: AsyncClient, e2e_canvas_base: Path
    ):
        """GET /mounted/{canvas_path} returns all associations after mounts."""
        # Arrange — mount two textbooks to the same canvas
        canvas_path = "数学/综合.canvas"
        (e2e_canvas_base / "数学").mkdir(parents=True, exist_ok=True)

        for textbook_id, name, fmt in [
            ("list-pdf-001", "微积分教材", "pdf"),
            ("list-md-001", "导数笔记", "markdown"),
        ]:
            body = {
                "canvas_path": canvas_path,
                "textbook": {
                    "id": textbook_id,
                    "path": f"教材/{name}.{fmt}",
                    "name": name,
                    "type": fmt,
                    "sections": [],
                },
            }
            resp = await e2e_client.post("/api/v1/textbook/sync-mount", json=body)
            assert resp.status_code == 200

        # Act — list mounted textbooks
        encoded_path = canvas_path  # FastAPI handles path encoding
        list_resp = await e2e_client.get(f"/api/v1/textbook/mounted/{encoded_path}")

        # Assert — HTTP response
        assert list_resp.status_code == 200
        data = list_resp.json()
        assert len(data["associations"]) == 2

        ids = {a["association_id"] for a in data["associations"]}
        assert "mount-list-pdf-001" in ids
        assert "mount-list-md-001" in ids
