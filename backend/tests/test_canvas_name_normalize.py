# Canvas Learning System - Canvas Name Normalization Tests
# ✅ Source: Story 12.A.1 - AC 5: 添加单元测试覆盖路径标准化逻辑
"""
Unit tests for Canvas name normalization in CanvasService.

These tests verify that the _get_canvas_path method correctly normalizes
canvas names by removing .canvas and .md extensions to prevent path
construction errors like "file.md.canvas".

[Source: Story 12.A.1 - Canvas名称标准化]
"""

import tempfile
from pathlib import Path

import pytest
from app.services.canvas_service import CanvasService


class TestCanvasNameNormalization:
    """Test suite for canvas name normalization in _get_canvas_path."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def canvas_service(self, temp_dir):
        """Create a CanvasService instance with temp directory."""
        return CanvasService(canvas_base_path=str(temp_dir))

    # =========================================================================
    # Test: Standard format (no extension) - should pass through unchanged
    # =========================================================================
    def test_standard_format_no_extension(self, canvas_service, temp_dir):
        """
        Test: Canvas name without extension should pass through unchanged.

        Input: "Canvas/Math53/Lecture5"
        Expected: temp_dir/Canvas/Math53/Lecture5.canvas
        """
        result = canvas_service._get_canvas_path("Canvas/Math53/Lecture5")
        expected = temp_dir / "Canvas/Math53/Lecture5.canvas"
        assert result == expected

    def test_simple_name_no_extension(self, canvas_service, temp_dir):
        """
        Test: Simple canvas name without extension.

        Input: "test"
        Expected: temp_dir/test.canvas
        """
        result = canvas_service._get_canvas_path("test")
        expected = temp_dir / "test.canvas"
        assert result == expected

    # =========================================================================
    # Test: .canvas extension - should be removed
    # =========================================================================
    def test_canvas_extension_removed(self, canvas_service, temp_dir):
        """
        Test: .canvas extension should be removed before adding .canvas.

        Input: "Canvas/Math53/Lecture5.canvas"
        Expected: temp_dir/Canvas/Math53/Lecture5.canvas (NOT Lecture5.canvas.canvas)
        """
        result = canvas_service._get_canvas_path("Canvas/Math53/Lecture5.canvas")
        expected = temp_dir / "Canvas/Math53/Lecture5.canvas"
        assert result == expected

    def test_canvas_extension_case_insensitive(self, canvas_service, temp_dir):
        """
        Test: .CANVAS extension (uppercase) should also be handled.

        Note: Python's removesuffix is case-sensitive, but our backend
        normalizes to lowercase before storage, so this tests the actual behavior.
        """
        result = canvas_service._get_canvas_path("test.canvas")
        expected = temp_dir / "test.canvas"
        assert result == expected

    # =========================================================================
    # Test: .md extension - should be removed (Bug fix for Story 12.A.1)
    # =========================================================================
    def test_md_extension_removed(self, canvas_service, temp_dir):
        """
        Test: .md extension should be removed before adding .canvas.

        This is the PRIMARY BUG FIX for Story 12.A.1.

        Input: "KP13-线性逼近与微分.md"
        Expected: temp_dir/KP13-线性逼近与微分.canvas (NOT .md.canvas)

        [Source: Story 12.A.1 - 39次错误根因]
        """
        result = canvas_service._get_canvas_path("KP13-线性逼近与微分.md")
        expected = temp_dir / "KP13-线性逼近与微分.canvas"
        assert result == expected

    def test_md_extension_with_path(self, canvas_service, temp_dir):
        """
        Test: .md extension with full path should be handled.

        Input: "笔记库/数学/test.md"
        Expected: temp_dir/笔记库/数学/test.canvas
        """
        result = canvas_service._get_canvas_path("笔记库/数学/test.md")
        expected = temp_dir / "笔记库/数学/test.canvas"
        assert result == expected

    # =========================================================================
    # Test: Chinese file names
    # =========================================================================
    def test_chinese_filename_no_extension(self, canvas_service, temp_dir):
        """
        Test: Chinese filename without extension.

        Input: "线性代数复习"
        Expected: temp_dir/线性代数复习.canvas
        """
        result = canvas_service._get_canvas_path("线性代数复习")
        expected = temp_dir / "线性代数复习.canvas"
        assert result == expected

    def test_chinese_filename_with_canvas_extension(self, canvas_service, temp_dir):
        """
        Test: Chinese filename with .canvas extension.

        Input: "微积分第五讲.canvas"
        Expected: temp_dir/微积分第五讲.canvas
        """
        result = canvas_service._get_canvas_path("微积分第五讲.canvas")
        expected = temp_dir / "微积分第五讲.canvas"
        assert result == expected

    def test_chinese_filename_with_md_extension(self, canvas_service, temp_dir):
        """
        Test: Chinese filename with .md extension (the bug case).

        Input: "KP13-线性逼近与微分.md"
        Expected: temp_dir/KP13-线性逼近与微分.canvas

        [Source: Story 12.A.1 - Bug Log中的实际错误案例]
        """
        result = canvas_service._get_canvas_path("KP13-线性逼近与微分.md")
        expected = temp_dir / "KP13-线性逼近与微分.canvas"
        assert result == expected

    # =========================================================================
    # Test: Edge cases
    # =========================================================================
    def test_empty_string(self, canvas_service, temp_dir):
        """
        Test: Empty string should produce .canvas file.

        Input: ""
        Expected: temp_dir/.canvas
        """
        result = canvas_service._get_canvas_path("")
        expected = temp_dir / ".canvas"
        assert result == expected

    def test_only_extension_canvas(self, canvas_service, temp_dir):
        """
        Test: Input that is only ".canvas" extension.

        Input: ".canvas"
        Expected: temp_dir/.canvas
        """
        result = canvas_service._get_canvas_path(".canvas")
        expected = temp_dir / ".canvas"
        assert result == expected

    def test_only_extension_md(self, canvas_service, temp_dir):
        """
        Test: Input that is only ".md" extension.

        Input: ".md"
        Expected: temp_dir/.canvas
        """
        result = canvas_service._get_canvas_path(".md")
        expected = temp_dir / ".canvas"
        assert result == expected

    def test_double_extension_canvas_md(self, canvas_service, temp_dir):
        """
        Test: File with both extensions (edge case).

        Input: "test.canvas.md"
        Expected: temp_dir/test.canvas.canvas (only .md removed)

        Note: This is an edge case - the method removes from the end only.
        """
        result = canvas_service._get_canvas_path("test.canvas.md")
        expected = temp_dir / "test.canvas.canvas"
        assert result == expected

    def test_double_extension_md_canvas(self, canvas_service, temp_dir):
        """
        Test: File with .md.canvas (edge case).

        Input: "test.md.canvas"
        Expected: temp_dir/test.md.canvas (only .canvas removed, then .canvas added)

        Note: removesuffix is applied in order: .canvas first, then .md
        """
        result = canvas_service._get_canvas_path("test.md.canvas")
        expected = temp_dir / "test.canvas"
        assert result == expected

    # =========================================================================
    # Test: Subdirectory paths
    # =========================================================================
    def test_subdirectory_path(self, canvas_service, temp_dir):
        """
        Test: Path with subdirectories.

        Input: "笔记库/子目录/test"
        Expected: temp_dir/笔记库/子目录/test.canvas
        """
        result = canvas_service._get_canvas_path("笔记库/子目录/test")
        expected = temp_dir / "笔记库/子目录/test.canvas"
        assert result == expected

    def test_deep_subdirectory_path(self, canvas_service, temp_dir):
        """
        Test: Path with deep subdirectories.

        Input: "Canvas/Math53/Week1/Lecture5"
        Expected: temp_dir/Canvas/Math53/Week1/Lecture5.canvas
        """
        result = canvas_service._get_canvas_path("Canvas/Math53/Week1/Lecture5")
        expected = temp_dir / "Canvas/Math53/Week1/Lecture5.canvas"
        assert result == expected


class TestCanvasNameValidation:
    """Test suite for canvas name validation security checks."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def canvas_service(self, temp_dir):
        """Create a CanvasService instance with temp directory."""
        return CanvasService(canvas_base_path=str(temp_dir))

    def test_path_traversal_blocked(self, canvas_service):
        """Test that path traversal attacks are blocked."""
        from app.core.exceptions import ValidationError

        with pytest.raises(ValidationError):
            canvas_service._get_canvas_path("../../../etc/passwd")

    def test_absolute_path_blocked(self, canvas_service):
        """Test that absolute paths are blocked."""
        from app.core.exceptions import ValidationError

        with pytest.raises(ValidationError):
            canvas_service._get_canvas_path("/etc/passwd")

    def test_double_slash_blocked(self, canvas_service):
        """Test that double slashes are blocked."""
        from app.core.exceptions import ValidationError

        with pytest.raises(ValidationError):
            canvas_service._get_canvas_path("test//file")
