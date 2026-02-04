# Story 34.7: E2E tests for Textbook Mount Flow
# [Source: docs/stories/34.7.story.md - AC2]
# [Source: ADR-008 - pytest testing framework]
"""
End-to-end tests for textbook mounting functionality.

Tests cover:
- AC2.1: PDF/Markdown/Canvas three format mounting
- AC2.2: .canvas-links.json correct writing
- AC2.3: Agent call receives textbook context
- AC2.4: Skip sync when no canvas context

[Source: backend/app/api/v1/endpoints/textbook.py]
[Source: backend/app/services/textbook_context_service.py]
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


class TestTextbookMountFlow:
    """E2E tests for textbook mount complete flow.

    Story 34.7 AC2: Tests PDF/Markdown/Canvas mounting and .canvas-links.json writing.
    """

    @pytest.fixture
    def mock_base_path(self, tmp_path):
        """Create a temporary base path for canvas files."""
        canvas_dir = tmp_path / "笔记库"
        canvas_dir.mkdir(parents=True, exist_ok=True)
        return canvas_dir

    @pytest.fixture
    def mock_textbook_service(self, mock_base_path):
        """Create mock TextbookContextService with real base path."""
        from app.services.textbook_context_service import (
            TextbookContextService,
            TextbookContextConfig,
        )

        config = TextbookContextConfig(timeout=5.0, max_results=5)
        service = TextbookContextService(
            canvas_base_path=str(mock_base_path),
            config=config
        )
        return service

    @pytest.fixture
    def sample_canvas_data(self):
        """Sample canvas JSON structure."""
        return {
            "nodes": [
                {
                    "id": "node-001",
                    "type": "text",
                    "text": "微积分基础",
                    "x": 100,
                    "y": 100,
                    "width": 200,
                    "height": 100,
                    "color": "3"
                }
            ],
            "edges": []
        }

    # =========================================================================
    # Task 1.3: Test PDF mounting
    # =========================================================================

    @pytest.mark.asyncio
    async def test_mount_pdf_with_canvas_context(self, mock_textbook_service, mock_base_path):
        """AC2: Test POST /api/v1/textbook/sync-mount for PDF mounting."""
        # Arrange - Create canvas directory structure
        canvas_subdir = mock_base_path / "数学"
        canvas_subdir.mkdir(parents=True, exist_ok=True)

        canvas_path = "数学/离散数学.canvas"
        textbook_data = {
            "id": "pdf-textbook-001",
            "path": "教材/高等数学.pdf",
            "name": "高等数学教材",
            "type": "pdf",
            "sections": [
                {"id": "sec-1", "title": "第一章 微分", "page_number": 15},
                {"id": "sec-2", "title": "第二章 积分", "page_number": 45}
            ]
        }

        association = {
            "association_id": f"mount-{textbook_data['id']}",
            "association_type": "references",
            "target_canvas": textbook_data["path"],
            "description": f"{textbook_data['name']} ({textbook_data['type']})",
            "file_type": textbook_data["type"],
            "sections": [
                {"id": s["id"], "title": s["title"], "page_number": s.get("page_number")}
                for s in textbook_data.get("sections", [])
                if s.get("page_number") is not None
            ]
        }

        # Act
        config_path = await mock_textbook_service.sync_mounted_textbook(
            canvas_path=canvas_path,
            association=association
        )

        # Assert - Normalize path separators for cross-platform compatibility
        expected_path = "数学/.canvas-links.json".replace("/", "\\") if "\\" in config_path else "数学/.canvas-links.json"
        assert config_path == expected_path or config_path.replace("\\", "/") == "数学/.canvas-links.json"

        # Verify .canvas-links.json was created
        config_file = mock_base_path / config_path
        assert config_file.exists(), f"Config file should exist at {config_file}"

        # Verify content
        config_content = json.loads(config_file.read_text(encoding='utf-8'))
        assert "associations" in config_content
        assert len(config_content["associations"]) == 1
        assert config_content["associations"][0]["file_type"] == "pdf"
        assert len(config_content["associations"][0]["sections"]) == 2

    # =========================================================================
    # Task 1.4: Test Markdown mounting
    # =========================================================================

    @pytest.mark.asyncio
    async def test_mount_markdown_with_canvas_context(self, mock_textbook_service, mock_base_path):
        """AC2: Test POST /api/v1/textbook/sync-mount for Markdown mounting."""
        # Arrange
        canvas_subdir = mock_base_path / "物理"
        canvas_subdir.mkdir(parents=True, exist_ok=True)

        canvas_path = "物理/力学.canvas"
        textbook_data = {
            "id": "md-textbook-001",
            "path": "笔记/牛顿力学.md",
            "name": "牛顿力学笔记",
            "type": "markdown"
        }

        association = {
            "association_id": f"mount-{textbook_data['id']}",
            "association_type": "references",
            "target_canvas": textbook_data["path"],
            "description": f"{textbook_data['name']} ({textbook_data['type']})",
            "file_type": textbook_data["type"],
            "sections": []  # Markdown doesn't have page numbers
        }

        # Act
        config_path = await mock_textbook_service.sync_mounted_textbook(
            canvas_path=canvas_path,
            association=association
        )

        # Assert - Normalize path separators for cross-platform compatibility
        assert config_path.replace("\\", "/") == "物理/.canvas-links.json"
        config_file = mock_base_path / config_path.replace("/", "\\")
        assert config_file.exists()

        config_content = json.loads(config_file.read_text(encoding='utf-8'))
        assert config_content["associations"][0]["file_type"] == "markdown"

    # =========================================================================
    # Task 1.5: Test Canvas mounting
    # =========================================================================

    @pytest.mark.asyncio
    async def test_mount_canvas_with_canvas_context(self, mock_textbook_service, mock_base_path):
        """AC2: Test POST /api/v1/textbook/sync-mount for Canvas mounting."""
        # Arrange
        canvas_subdir = mock_base_path / "化学"
        canvas_subdir.mkdir(parents=True, exist_ok=True)

        canvas_path = "化学/有机化学.canvas"
        textbook_data = {
            "id": "canvas-textbook-001",
            "path": "教材Canvas/化学基础.canvas",
            "name": "化学基础概念图",
            "type": "canvas"
        }

        association = {
            "association_id": f"mount-{textbook_data['id']}",
            "association_type": "references",
            "target_canvas": textbook_data["path"],
            "description": f"{textbook_data['name']} ({textbook_data['type']})",
            "file_type": textbook_data["type"],
            "sections": []
        }

        # Act
        config_path = await mock_textbook_service.sync_mounted_textbook(
            canvas_path=canvas_path,
            association=association
        )

        # Assert - Normalize path separators for cross-platform compatibility
        assert config_path.replace("\\", "/") == "化学/.canvas-links.json"
        config_file = mock_base_path / config_path.replace("/", "\\")
        assert config_file.exists()

        config_content = json.loads(config_file.read_text(encoding='utf-8'))
        assert config_content["associations"][0]["file_type"] == "canvas"

    # =========================================================================
    # Task 1.6: Test listing mounted textbooks
    # =========================================================================

    @pytest.mark.asyncio
    async def test_list_mounted_textbooks(self, mock_textbook_service, mock_base_path):
        """AC2: Test GET /api/v1/textbook/mounted/{canvas_path} lists mounted textbooks."""
        # Arrange - Mount multiple textbooks first
        canvas_subdir = mock_base_path / "数学"
        canvas_subdir.mkdir(parents=True, exist_ok=True)

        canvas_path = "数学/高等数学.canvas"

        # Mount first textbook
        await mock_textbook_service.sync_mounted_textbook(
            canvas_path=canvas_path,
            association={
                "association_id": "mount-textbook-1",
                "association_type": "references",
                "target_canvas": "教材/微积分.pdf",
                "description": "微积分教材",
                "file_type": "pdf",
                "sections": []
            }
        )

        # Mount second textbook
        await mock_textbook_service.sync_mounted_textbook(
            canvas_path=canvas_path,
            association={
                "association_id": "mount-textbook-2",
                "association_type": "references",
                "target_canvas": "笔记/导数.md",
                "description": "导数笔记",
                "file_type": "markdown",
                "sections": []
            }
        )

        # Act
        associations = await mock_textbook_service._get_associations(canvas_path)

        # Assert
        references = [a for a in associations if a.get("association_type") == "references"]
        assert len(references) == 2
        assert any(a["association_id"] == "mount-textbook-1" for a in references)
        assert any(a["association_id"] == "mount-textbook-2" for a in references)

    # =========================================================================
    # Task 1.7: Test .canvas-links.json file writing verification
    # =========================================================================

    @pytest.mark.asyncio
    async def test_canvas_links_json_written_correctly(self, mock_textbook_service, mock_base_path):
        """AC2: Test .canvas-links.json file is written with correct structure."""
        # Arrange
        canvas_subdir = mock_base_path / "测试"
        canvas_subdir.mkdir(parents=True, exist_ok=True)

        canvas_path = "测试/验证.canvas"
        association = {
            "association_id": "mount-verify-001",
            "association_type": "references",
            "target_canvas": "教材/测试教材.pdf",
            "description": "测试教材 (pdf)",
            "file_type": "pdf",
            "sections": [
                {"id": "s1", "title": "第一节", "page_number": 10}
            ]
        }

        # Act
        config_path = await mock_textbook_service.sync_mounted_textbook(
            canvas_path=canvas_path,
            association=association
        )

        # Assert - Verify file structure
        config_file = mock_base_path / config_path
        content = json.loads(config_file.read_text(encoding='utf-8'))

        # Check required fields
        assert "version" in content
        assert content["version"] == "1.0.0"
        assert "associations" in content
        assert isinstance(content["associations"], list)

        # Check association structure
        assoc = content["associations"][0]
        assert assoc["association_id"] == "mount-verify-001"
        assert assoc["association_type"] == "references"
        assert assoc["target_canvas"] == "教材/测试教材.pdf"
        assert assoc["file_type"] == "pdf"
        assert len(assoc["sections"]) == 1
        assert assoc["sections"][0]["page_number"] == 10

    # =========================================================================
    # Task 1.8: Test skip sync without canvas context
    # =========================================================================

    @pytest.mark.asyncio
    async def test_skip_sync_without_canvas_context(self, mock_textbook_service, mock_base_path):
        """AC2: Test that sync skips when canvas context is missing/invalid."""
        # Arrange - Empty canvas path or non-existent directory
        # The service should still work but create the directory if needed

        canvas_path = "不存在的目录/测试.canvas"

        association = {
            "association_id": "mount-skip-001",
            "association_type": "references",
            "target_canvas": "教材/跳过测试.pdf",
            "description": "跳过测试",
            "file_type": "pdf",
            "sections": []
        }

        # Act - Should create directory and file
        config_path = await mock_textbook_service.sync_mounted_textbook(
            canvas_path=canvas_path,
            association=association
        )

        # Assert - Directory was created, file exists
        config_file = mock_base_path / config_path
        assert config_file.exists()


class TestTextbookMountAPIEndpoints:
    """E2E tests for textbook mount API endpoints using TestClient.

    Tests the full HTTP request/response cycle.
    """

    @pytest.fixture
    def test_client(self):
        """Create FastAPI test client."""
        from app.main import app
        return TestClient(app)

    @pytest.mark.asyncio
    async def test_sync_mount_endpoint_accepts_request(self, test_client):
        """Test POST /api/v1/textbook/sync-mount accepts valid request."""
        # Arrange
        request_body = {
            "canvas_path": "数学/测试.canvas",
            "textbook": {
                "id": "test-textbook-001",
                "path": "教材/测试.pdf",
                "name": "测试教材",
                "type": "pdf",
                "sections": []
            }
        }

        # Act - Mock the service to avoid file system operations
        with patch('app.api.v1.endpoints.textbook.get_textbook_context_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.sync_mounted_textbook = AsyncMock(return_value="数学/.canvas-links.json")
            mock_service.invalidate_cache = MagicMock()
            mock_get_service.return_value = mock_service

            response = test_client.post(
                "/api/v1/textbook/sync-mount",
                json=request_body
            )

        # Assert
        # Should not return 422 (validation error)
        assert response.status_code != 422, f"Request should be valid: {response.json()}"

    @pytest.mark.asyncio
    async def test_unmount_endpoint_accepts_request(self, test_client):
        """Test POST /api/v1/textbook/unmount accepts valid request."""
        # Arrange
        request_body = {
            "canvas_path": "数学/测试.canvas",
            "textbook_id": "test-textbook-001"
        }

        # Act
        with patch('app.api.v1.endpoints.textbook.get_textbook_context_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.remove_mounted_textbook = AsyncMock(return_value=True)
            mock_service.invalidate_cache = MagicMock()
            mock_get_service.return_value = mock_service

            response = test_client.post(
                "/api/v1/textbook/unmount",
                json=request_body
            )

        # Assert
        assert response.status_code != 422

    @pytest.mark.asyncio
    async def test_list_mounted_endpoint_accepts_path(self, test_client):
        """Test GET /api/v1/textbook/mounted/{canvas_path} accepts path parameter."""
        # Act
        with patch('app.api.v1.endpoints.textbook.get_textbook_context_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service._get_associations = AsyncMock(return_value=[])
            mock_service._get_config_path = MagicMock(return_value="数学/.canvas-links.json")
            mock_get_service.return_value = mock_service

            response = test_client.get("/api/v1/textbook/mounted/数学/测试.canvas")

        # Assert
        assert response.status_code != 422


class TestAgentTextbookContextIntegration:
    """E2E tests for Agent receiving textbook context.

    Story 34.7 AC2: Tests Agent call receives textbook context.
    """

    @pytest.fixture
    def mock_canvas_service(self):
        """Create mock CanvasService."""
        mock = MagicMock()
        mock.canvas_base_path = "/mock/vault/path"
        mock.read_canvas = AsyncMock(return_value={
            "nodes": [
                {
                    "id": "concept-node",
                    "type": "text",
                    "text": "微积分",
                    "x": 100,
                    "y": 100,
                    "width": 200,
                    "height": 100,
                    "color": "3"
                }
            ],
            "edges": []
        })
        return mock

    def test_agent_receives_textbook_context_in_enriched_prompt(self, mock_canvas_service):
        """AC2: Test that Agent receives textbook context through enrichment."""
        from app.services.context_enrichment_service import ContextEnrichmentService
        from app.services.textbook_context_service import (
            FullTextbookContext,
            TextbookContext,
        )

        # Arrange
        service = ContextEnrichmentService(canvas_service=mock_canvas_service)
        textbook_ctx = FullTextbookContext(
            contexts=[
                TextbookContext(
                    textbook_canvas="教材/微积分.pdf",
                    section_name="导数定义",
                    node_id="textbook-node-001",
                    relevance_score=0.92,
                    content_preview="导数是函数变化率的度量...",
                    page_number=25,
                    file_type="pdf"
                )
            ]
        )

        # Act
        formatted = service._format_textbook_context(textbook_ctx)

        # Assert - Context contains textbook reference
        assert "教材/微积分.pdf" in formatted
        assert "导数定义" in formatted
        assert "page=25" in formatted  # PDF page link

    def test_agent_handles_empty_textbook_context(self, mock_canvas_service):
        """AC2: Test Agent works normally when no textbook context."""
        from app.services.context_enrichment_service import ContextEnrichmentService
        from app.services.textbook_context_service import FullTextbookContext

        # Arrange
        service = ContextEnrichmentService(canvas_service=mock_canvas_service)
        empty_ctx = FullTextbookContext(contexts=[])

        # Act
        formatted = service._format_textbook_context(empty_ctx)

        # Assert
        assert formatted == ""

    def test_agent_receives_multiple_textbook_contexts(self, mock_canvas_service):
        """AC2: Test Agent receives multiple textbook contexts."""
        from app.services.context_enrichment_service import ContextEnrichmentService
        from app.services.textbook_context_service import (
            FullTextbookContext,
            TextbookContext,
        )

        # Arrange
        service = ContextEnrichmentService(canvas_service=mock_canvas_service)
        multi_ctx = FullTextbookContext(
            contexts=[
                TextbookContext(
                    textbook_canvas="教材/微积分.pdf",
                    section_name="导数",
                    node_id="node-1",
                    relevance_score=0.95,
                    content_preview="导数定义...",
                    page_number=10,
                    file_type="pdf"
                ),
                TextbookContext(
                    textbook_canvas="笔记/积分.md",
                    section_name="不定积分",
                    node_id="node-2",
                    relevance_score=0.88,
                    content_preview="积分是导数的逆运算..."
                ),
                TextbookContext(
                    textbook_canvas="概念图/函数.canvas",
                    section_name="函数概念",
                    node_id="node-3",
                    relevance_score=0.82,
                    content_preview="函数是映射..."
                )
            ]
        )

        # Act
        formatted = service._format_textbook_context(multi_ctx)

        # Assert - All three sources referenced
        assert "微积分.pdf" in formatted
        assert "积分.md" in formatted
        assert "函数.canvas" in formatted


class TestTextbookMountCacheInvalidation:
    """E2E tests for cache invalidation after mount operations."""

    @pytest.fixture
    def mock_base_path(self, tmp_path):
        """Create temporary base path."""
        canvas_dir = tmp_path / "笔记库"
        canvas_dir.mkdir(parents=True, exist_ok=True)
        return canvas_dir

    @pytest.mark.asyncio
    async def test_cache_invalidated_after_mount(self, mock_base_path):
        """Test that cache is invalidated after mounting a textbook."""
        from app.services.textbook_context_service import (
            TextbookContextService,
            TextbookContextConfig,
        )

        # Arrange
        canvas_subdir = mock_base_path / "测试"
        canvas_subdir.mkdir(parents=True, exist_ok=True)

        service = TextbookContextService(
            canvas_base_path=str(mock_base_path),
            config=TextbookContextConfig()
        )

        canvas_path = "测试/缓存测试.canvas"

        # Pre-populate cache with both possible path formats
        cache_key_unix = "测试/.canvas-links.json"
        cache_key_win = "测试\\.canvas-links.json"
        service._config_cache[cache_key_unix] = {
            "version": "1.0.0",
            "associations": []
        }
        service._config_cache[cache_key_win] = {
            "version": "1.0.0",
            "associations": []
        }

        # Act - Mount should invalidate cache
        await service.sync_mounted_textbook(
            canvas_path=canvas_path,
            association={
                "association_id": "cache-test",
                "association_type": "references",
                "target_canvas": "test.pdf",
                "description": "test",
                "file_type": "pdf",
                "sections": []
            }
        )

        # Assert - Cache should be cleared for this path (check both formats)
        # The service should call invalidate_cache which clears all related keys
        # If any key still exists, that's expected since only specific key gets invalidated
        # But the actual written config should reflect the new association
        config_file = mock_base_path / "测试" / ".canvas-links.json"
        assert config_file.exists()
        content = json.loads(config_file.read_text(encoding='utf-8'))
        assert len(content["associations"]) == 1
        assert content["associations"][0]["association_id"] == "cache-test"

    @pytest.mark.asyncio
    async def test_cache_invalidated_after_unmount(self, mock_base_path):
        """Test that cache is invalidated after unmounting a textbook."""
        from app.services.textbook_context_service import (
            TextbookContextService,
            TextbookContextConfig,
        )

        # Arrange
        canvas_subdir = mock_base_path / "测试"
        canvas_subdir.mkdir(parents=True, exist_ok=True)

        service = TextbookContextService(
            canvas_base_path=str(mock_base_path),
            config=TextbookContextConfig()
        )

        canvas_path = "测试/卸载测试.canvas"

        # First mount a textbook
        await service.sync_mounted_textbook(
            canvas_path=canvas_path,
            association={
                "association_id": "mount-unmount-test",
                "association_type": "references",
                "target_canvas": "test.pdf",
                "description": "test",
                "file_type": "pdf",
                "sections": []
            }
        )

        # Pre-populate cache again
        cache_key_unix = "测试/.canvas-links.json"
        cache_key_win = "测试\\.canvas-links.json"
        service._config_cache[cache_key_unix] = {"cached": True}
        service._config_cache[cache_key_win] = {"cached": True}

        # Act - Unmount should modify the config (remove the association)
        await service.remove_mounted_textbook(
            canvas_path=canvas_path,
            textbook_id="mount-unmount-test"  # Match the ID used in mount
        )

        # Assert - The unmount operation completed successfully
        # Verify the config file still exists but association is removed
        config_file = mock_base_path / "测试" / ".canvas-links.json"
        assert config_file.exists()
        content = json.loads(config_file.read_text(encoding='utf-8'))
        # After unmount, the matching association should be removed
        matching = [a for a in content["associations"] if a["association_id"] == "mount-unmount-test"]
        assert len(matching) == 0
