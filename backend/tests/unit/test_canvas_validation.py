"""
Unit tests for Canvas name validation.

Tests the security checks in CanvasService._validate_canvas_name() to ensure:
1. Valid subdirectory paths are allowed (e.g., "笔记库/子目录/test")
2. Dangerous path traversal patterns are blocked (e.g., "..", "//", etc.)
3. Absolute paths are rejected

Story: 21.5.1.2 - 优化后端Path Traversal安全检查
"""

import pytest
from app.core.exceptions import ValidationError
from app.services.canvas_service import CanvasService


class TestCanvasValidation:
    """Test suite for canvas name validation security checks."""

    @pytest.fixture
    def canvas_service(self):
        """Create a CanvasService instance for testing."""
        return CanvasService(canvas_base_path="./test_data")

    # ========================================
    # Valid Paths (should NOT raise)
    # ========================================

    def test_valid_simple_filename(self, canvas_service):
        """AC1: Simple filename without path should be valid."""
        # Should not raise ValidationError
        canvas_service._validate_canvas_name("test")

    def test_valid_filename_with_extension(self, canvas_service):
        """AC1: Filename with extension should be valid."""
        canvas_service._validate_canvas_name("test.canvas")

    def test_valid_subdirectory_path_chinese(self, canvas_service):
        """AC1: Subdirectory path with Chinese characters should be valid."""
        canvas_service._validate_canvas_name("笔记库/子目录/test")

    def test_valid_deep_chinese_path(self, canvas_service):
        """AC1: Deep path with Chinese characters should be valid."""
        canvas_service._validate_canvas_name("学习/数学/离散数学")

    def test_valid_deep_ascii_path(self, canvas_service):
        """AC1: Deep ASCII path should be valid."""
        canvas_service._validate_canvas_name("a/b/c/d/e/file")

    # ========================================
    # Invalid Paths (should raise ValidationError)
    # ========================================

    def test_invalid_directory_traversal(self, canvas_service):
        """AC2: Directory traversal with .. should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            canvas_service._validate_canvas_name("../../../etc/passwd")
        assert "Invalid canvas path" in str(exc_info.value)

    def test_invalid_embedded_traversal(self, canvas_service):
        """AC2: Embedded .. in path should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            canvas_service._validate_canvas_name("test/../secret")
        assert "Invalid canvas path" in str(exc_info.value)

    def test_invalid_null_byte_injection(self, canvas_service):
        """AC2: Null byte injection should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            canvas_service._validate_canvas_name("test\0.canvas")
        assert "Invalid canvas path" in str(exc_info.value)

    def test_invalid_backslash(self, canvas_service):
        """AC2: Backslash (Windows path separator) should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            canvas_service._validate_canvas_name("test\\file")
        assert "Invalid canvas path" in str(exc_info.value)

    def test_invalid_double_slash(self, canvas_service):
        """AC2: Double slash should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            canvas_service._validate_canvas_name("test//file")
        assert "Invalid canvas path" in str(exc_info.value)

    def test_invalid_current_directory_reference(self, canvas_service):
        """AC2: Current directory reference /./ should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            canvas_service._validate_canvas_name("test/./file")
        assert "Invalid canvas path" in str(exc_info.value)

    def test_invalid_absolute_path(self, canvas_service):
        """AC3: Absolute path starting with / should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            canvas_service._validate_canvas_name("/etc/passwd")
        assert "Absolute path not allowed" in str(exc_info.value)

    # ========================================
    # Edge Cases
    # ========================================

    def test_valid_single_slash_in_middle(self, canvas_service):
        """AC1: Single slash in the middle (subdirectory) should be valid."""
        canvas_service._validate_canvas_name("folder/file")

    def test_invalid_trailing_slash(self, canvas_service):
        """Edge case: Trailing slash could be blocked (implementation choice)."""
        # This is technically a valid subdirectory path, but may indicate a directory
        # Current implementation allows it (no explicit check for trailing /)
        # If you want to block trailing slash, add this check:
        # if canvas_name.endswith('/'):
        #     raise ValidationError(f"Canvas name cannot end with /: {canvas_name}")
        canvas_service._validate_canvas_name("folder/")

    def test_valid_unicode_filename(self, canvas_service):
        """AC1: Unicode characters should be valid."""
        canvas_service._validate_canvas_name("数学/微积分")

    def test_invalid_multiple_dots_in_traversal(self, canvas_service):
        """AC2: Multiple .. sequences should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            canvas_service._validate_canvas_name("../../secret")
        assert "Invalid canvas path" in str(exc_info.value)
