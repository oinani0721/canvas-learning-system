# Canvas Learning System - Textbook Link Format Tests
# Story 28.1: 教材路径元数据传递
# Story 28.3: PDF页码链接支持
"""
Unit tests for textbook link formatting.

Tests the _format_textbook_link() and _format_textbook_context() methods
for Obsidian bidirectional link generation with complete file paths.

Story 28.1 Tests:
- AC1: 教材路径保留 - Complete textbook_canvas path in output
- AC2: Obsidian链接格式正确 - [[file#section]] format
- AC3: 向后兼容性 - Empty context handling, existing structure preserved

Story 28.3 Tests:
- PDF page number link support: [[file.pdf#page=N|section]]

[Source: Story 28.1 - 教材路径元数据传递]
[Source: Story 28.3 - PDF页码链接支持]
[Source: ADR-001 - Obsidian链接格式规范]
[Verified from ADR-011 - pathlib路径处理规范]
"""

import pytest
from unittest.mock import MagicMock

from backend.app.services.textbook_context_service import (
    TextbookContext,
    FullTextbookContext,
)
from backend.app.services.context_enrichment_service import ContextEnrichmentService
from backend.app.services.canvas_service import CanvasService


class TestTextbookContextDataclass:
    """Test TextbookContext dataclass with new fields."""

    def test_textbook_context_default_values(self):
        """Test default values for new fields (AC1)."""
        ctx = TextbookContext(
            textbook_canvas="教材/离散数学.canvas",
            section_name="逆否命题",
            node_id="node-001",
            relevance_score=0.95,
            content_preview="逆否命题是将原命题的条件和结论都取反...",
        )
        # Verify defaults
        assert ctx.page_number is None
        assert ctx.file_type == "canvas"

    def test_textbook_context_with_pdf_fields(self):
        """Test TextbookContext with PDF fields (AC1)."""
        ctx = TextbookContext(
            textbook_canvas="教材/高等数学.pdf",
            section_name="第3章 微分",
            node_id="node-123",
            relevance_score=0.95,
            content_preview="微分的定义...",
            page_number=47,
            file_type="pdf",
        )
        assert ctx.page_number == 47
        assert ctx.file_type == "pdf"
        assert ctx.textbook_canvas == "教材/高等数学.pdf"


class TestFormatTextbookLink:
    """Test _format_textbook_link() method."""

    @pytest.fixture
    def mock_canvas_service(self):
        """Create mock CanvasService with required attributes."""
        mock = MagicMock(spec=CanvasService)
        mock.canvas_base_path = "/mock/vault/path"
        return mock

    @pytest.fixture
    def service(self, mock_canvas_service):
        """Create ContextEnrichmentService instance with mock canvas_service."""
        return ContextEnrichmentService(canvas_service=mock_canvas_service)

    def test_pdf_link_with_page_number(self, service):
        """Test PDF file generates #page=N format (AC2)."""
        ctx = TextbookContext(
            textbook_canvas="教材/高等数学.pdf",
            section_name="第3章 微分",
            node_id="node-123",
            relevance_score=0.95,
            content_preview="微分的定义...",
            page_number=47,
            file_type="pdf",
        )
        link = service._format_textbook_link(ctx)
        assert link == "[[教材/高等数学.pdf#page=47|第3章 微分]]"

    def test_canvas_link_without_page(self, service):
        """Test Canvas file generates #section format (AC3)."""
        ctx = TextbookContext(
            textbook_canvas="教材/离散数学.canvas",
            section_name="逆否命题",
            node_id="node-456",
            relevance_score=0.88,
            content_preview="逆否命题是指...",
            page_number=None,
            file_type="canvas",
        )
        link = service._format_textbook_link(ctx)
        assert link == "[[教材/离散数学.canvas#逆否命题]]"

    def test_markdown_link_format(self, service):
        """Test Markdown file generates #heading format (AC3)."""
        ctx = TextbookContext(
            textbook_canvas="教材/集合论.md",
            section_name="并集定义",
            node_id="node-789",
            relevance_score=0.75,
            content_preview="并集是指...",
            page_number=None,
            file_type="markdown",
        )
        link = service._format_textbook_link(ctx)
        assert link == "[[教材/集合论.md#并集定义]]"

    def test_pdf_without_page_fallback(self, service):
        """Test PDF without page number falls back to section format (AC3)."""
        ctx = TextbookContext(
            textbook_canvas="教材/物理.pdf",
            section_name="牛顿第二定律",
            node_id="node-789",
            relevance_score=0.75,
            content_preview="F=ma...",
            page_number=None,  # No page number
            file_type="pdf",
        )
        link = service._format_textbook_link(ctx)
        # Should fall back to section format when no page number
        assert link == "[[教材/物理.pdf#牛顿第二定律]]"

    def test_special_characters_in_filename(self, service):
        """Test special characters in filename (AC2, AC3)."""
        ctx = TextbookContext(
            textbook_canvas="教材文件夹/高等 数学（上册）.pdf",
            section_name="第一章 极限",
            node_id="node-spec",
            relevance_score=0.90,
            content_preview="极限的定义...",
            page_number=15,
            file_type="pdf",
        )
        link = service._format_textbook_link(ctx)
        assert link == "[[教材文件夹/高等 数学（上册）.pdf#page=15|第一章 极限]]"

    def test_default_file_type_when_missing(self, service):
        """Test backward compatibility when file_type is not set."""
        # Simulate old TextbookContext without file_type (uses getattr default)
        ctx = TextbookContext(
            textbook_canvas="教材/线性代数.canvas",
            section_name="矩阵乘法",
            node_id="node-old",
            relevance_score=0.85,
            content_preview="矩阵乘法定义...",
        )
        link = service._format_textbook_link(ctx)
        # Should use default "canvas" type -> section format
        assert link == "[[教材/线性代数.canvas#矩阵乘法]]"


class TestFormatTextbookContext:
    """Test _format_textbook_context() method with new link format."""

    @pytest.fixture
    def mock_canvas_service(self):
        """Create mock CanvasService with required attributes."""
        mock = MagicMock(spec=CanvasService)
        mock.canvas_base_path = "/mock/vault/path"
        return mock

    @pytest.fixture
    def service(self, mock_canvas_service):
        """Create ContextEnrichmentService instance with mock canvas_service."""
        return ContextEnrichmentService(canvas_service=mock_canvas_service)

    def test_format_with_pdf_context(self, service):
        """Test formatting includes PDF link (AC2)."""
        ctx = TextbookContext(
            textbook_canvas="教材/高等数学.pdf",
            section_name="微分学基础",
            node_id="node-pdf",
            relevance_score=0.92,
            content_preview="微分是函数变化率的度量...",
            page_number=47,
            file_type="pdf",
        )
        full_ctx = FullTextbookContext(contexts=[ctx])
        result = service._format_textbook_context(full_ctx)

        # Verify output contains Obsidian link
        assert "[[教材/高等数学.pdf#page=47|微分学基础]]" in result
        assert "### 教材参考: 微分学基础" in result
        assert "**来源文件**:" in result
        assert "**相关度**: 92%" in result

    def test_format_with_canvas_context(self, service):
        """Test formatting includes Canvas link (AC3)."""
        ctx = TextbookContext(
            textbook_canvas="教材/离散数学.canvas",
            section_name="逆否命题",
            node_id="node-canvas",
            relevance_score=0.88,
            content_preview="逆否命题是原命题的逆命题的否命题...",
        )
        full_ctx = FullTextbookContext(contexts=[ctx])
        result = service._format_textbook_context(full_ctx)

        # Verify output contains Obsidian link
        assert "[[教材/离散数学.canvas#逆否命题]]" in result
        assert "### 教材参考: 逆否命题" in result
        assert "**相关度**: 88%" in result

    def test_format_with_empty_contexts(self, service):
        """Test formatting with no contexts (Story 28.1 AC3 backward compatibility)."""
        full_ctx = FullTextbookContext(contexts=[])
        result = service._format_textbook_context(full_ctx)

        # Story 28.1 AC3: Empty contexts should return empty string
        assert result == ""

    def test_format_with_none_textbook_ctx(self, service):
        """Test formatting with None textbook context (Story 28.1 AC3)."""
        result = service._format_textbook_context(None)

        # Should return empty string for None input
        assert result == ""

    def test_format_with_multiple_contexts(self, service):
        """Test formatting with multiple contexts."""
        contexts = [
            TextbookContext(
                textbook_canvas="教材/高等数学.pdf",
                section_name="极限",
                node_id="node-1",
                relevance_score=0.95,
                content_preview="极限的定义...",
                page_number=10,
                file_type="pdf",
            ),
            TextbookContext(
                textbook_canvas="教材/离散数学.canvas",
                section_name="命题逻辑",
                node_id="node-2",
                relevance_score=0.85,
                content_preview="命题是可以判断真假的陈述句...",
            ),
        ]
        full_ctx = FullTextbookContext(contexts=contexts)
        result = service._format_textbook_context(full_ctx)

        # Verify both links present
        assert "[[教材/高等数学.pdf#page=10|极限]]" in result
        assert "[[教材/离散数学.canvas#命题逻辑]]" in result
        assert result.count("### 教材参考:") == 2

    def test_format_preserves_prerequisites(self, service):
        """Test prerequisites section with Obsidian links (Story 28.1 AC1, AC2)."""
        from backend.app.services.textbook_context_service import Prerequisite

        ctx = TextbookContext(
            textbook_canvas="教材/微积分.canvas",
            section_name="积分",
            node_id="node-int",
            relevance_score=0.90,
            content_preview="积分是微分的逆运算...",
        )
        prereq = Prerequisite(
            concept_name="导数",
            source_canvas="教材/微积分.canvas",
            node_id="node-deriv",
            importance="required",
        )
        full_ctx = FullTextbookContext(contexts=[ctx], prerequisites=[prereq])
        result = service._format_textbook_context(full_ctx)

        # Verify textbook context with Obsidian link
        assert "[[教材/微积分.canvas#积分]]" in result

        # Story 28.1: Prerequisites now use Obsidian links format
        assert "### 建议先复习 (Prerequisites)" in result
        assert "**[必修]** 导数" in result
        # Prerequisites should have Obsidian link to source canvas
        assert "[[教材/微积分.canvas#导数]]" in result

    def test_format_prerequisites_without_source_canvas(self, service):
        """Test prerequisites without source canvas (Story 28.1 AC3)."""
        from backend.app.services.textbook_context_service import Prerequisite

        prereq = Prerequisite(
            concept_name="基础概念",
            source_canvas=None,  # No source canvas
            node_id="node-prereq",
            importance="recommended",
        )
        full_ctx = FullTextbookContext(contexts=[], prerequisites=[prereq])
        result = service._format_textbook_context(full_ctx)

        # Should show prerequisite without link
        assert "**[推荐]** 基础概念" in result
        # Should NOT have an empty Obsidian link
        assert "[[#" not in result
        assert "[[None" not in result
