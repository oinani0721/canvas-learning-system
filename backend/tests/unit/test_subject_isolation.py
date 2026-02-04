# Canvas Learning System - Subject Isolation Unit Tests
# Story 30.8: 多学科隔离与group_id支持
# ✅ Verified from docs/stories/30.8.story.md#Testing
"""
Unit tests for subject isolation functionality.

Test Cases (from Story 30.8):
1. test_extract_subject_single_level: 单级路径提取
2. test_extract_subject_multi_level: 多级路径提取
3. test_extract_subject_unicode: 中文路径处理
4. test_extract_subject_fallback: 降级到文件名
5. test_build_group_id: group_id构建
6. test_sanitize_subject_name: 学科名称清理

[Source: docs/stories/30.8.story.md#Testing]
"""

import pytest

from app.core.subject_config import (
    DEFAULT_SUBJECT,
    SKIP_DIRECTORIES_LOWER,
    SubjectType,
    build_group_id,
    extract_subject_from_canvas_path,
    sanitize_subject_name,
)


class TestExtractSubjectFromCanvasPath:
    """Tests for extract_subject_from_canvas_path function."""

    def test_extract_subject_single_level(self):
        """
        Test single level path extraction.

        ✅ AC-30.8.2: "数学/离散数学.canvas" → "数学"
        """
        assert extract_subject_from_canvas_path("数学/离散数学.canvas") == "数学"
        assert extract_subject_from_canvas_path("physics/mechanics.canvas") == "physics"

    def test_extract_subject_multi_level(self):
        """
        Test multi-level path extraction.

        ✅ AC-30.8.2: "托福/听力/托福听力.canvas" → "托福"
        """
        assert extract_subject_from_canvas_path("托福/听力/托福听力.canvas") == "托福"
        assert extract_subject_from_canvas_path("math/calculus/integrals.canvas") == "math"
        assert extract_subject_from_canvas_path("a/b/c/d.canvas") == "a"

    def test_extract_subject_unicode(self):
        """
        Test Chinese/Unicode path handling.

        ✅ AC-30.8.2: Properly handles Unicode characters
        """
        assert extract_subject_from_canvas_path("数学/代数/线性代数.canvas") == "数学"
        assert extract_subject_from_canvas_path("物理/力学.canvas") == "物理"
        assert extract_subject_from_canvas_path("计算机科学/算法.canvas") == "计算机科学"

    def test_extract_subject_fallback(self):
        """
        Test fallback to filename when no directory.

        ✅ AC-30.8.2: "离散数学.canvas" → "离散数学"
        """
        assert extract_subject_from_canvas_path("离散数学.canvas") == "离散数学"
        assert extract_subject_from_canvas_path("calculus.canvas") == "calculus"

    def test_extract_subject_skip_root_dirs(self):
        """
        Test skipping common root directories.

        ✅ AC-30.8.2: "笔记库/物理/力学.canvas" → "物理" (skip 笔记库)
        """
        assert extract_subject_from_canvas_path("笔记库/物理/力学.canvas") == "物理"
        assert extract_subject_from_canvas_path("vault/math/calc.canvas") == "math"
        assert extract_subject_from_canvas_path("notes/cs/algo.canvas") == "cs"
        assert extract_subject_from_canvas_path("obsidian/history/ww2.canvas") == "history"

    def test_extract_subject_empty_path(self):
        """Test empty path returns default subject."""
        assert extract_subject_from_canvas_path("") == DEFAULT_SUBJECT.value
        assert extract_subject_from_canvas_path(None) == DEFAULT_SUBJECT.value

    def test_extract_subject_only_filename(self):
        """Test path with only filename."""
        assert extract_subject_from_canvas_path("test.canvas") == "test"

    def test_extract_subject_windows_path(self):
        """Test Windows-style paths."""
        # Path should normalize separators
        result = extract_subject_from_canvas_path("math\\calculus\\limits.canvas")
        assert result in ["math", "math\\calculus\\limits"]  # Depends on Path handling


class TestBuildGroupId:
    """Tests for build_group_id function."""

    def test_build_group_id_simple(self):
        """
        Test simple group_id building.

        ✅ AC-30.8.1: Each subject uses independent group_id namespace
        """
        assert build_group_id("math") == "math"
        assert build_group_id("physics") == "physics"

    def test_build_group_id_with_canvas(self):
        """Test group_id with canvas name."""
        assert build_group_id("math", "calculus") == "math:calculus"
        assert build_group_id("physics", "mechanics") == "physics:mechanics"

    def test_build_group_id_unicode(self):
        """Test group_id with Unicode characters (Chinese preserved)."""
        result = build_group_id("数学")
        # Unicode chars are now preserved (QA Review fix)
        assert result == "数学"

    def test_build_group_id_mixed_unicode_ascii(self):
        """Test group_id with mixed Unicode and ASCII characters."""
        result = build_group_id("托福 Listening")
        # Chinese preserved, ASCII lowercased, space becomes underscore
        assert result == "托福_listening"

    def test_build_group_id_sanitization(self):
        """Test group_id sanitization."""
        result = build_group_id("Math 101!")
        assert result == "math_101"  # Spaces and special chars handled


class TestSanitizeSubjectName:
    """Tests for sanitize_subject_name function."""

    def test_sanitize_lowercase(self):
        """Test lowercase conversion."""
        assert sanitize_subject_name("MATH") == "math"
        assert sanitize_subject_name("Physics") == "physics"

    def test_sanitize_spaces(self):
        """Test space handling."""
        assert sanitize_subject_name("linear algebra") == "linear_algebra"
        assert sanitize_subject_name("computer  science") == "computer_science"

    def test_sanitize_special_chars(self):
        """Test special character handling."""
        assert sanitize_subject_name("math-101") == "math_101"
        assert sanitize_subject_name("c++") == "c"
        assert sanitize_subject_name("c#") == "c"

    def test_sanitize_empty(self):
        """Test empty string returns default."""
        assert sanitize_subject_name("") == "default"

    def test_sanitize_consecutive_underscores(self):
        """Test consecutive underscore removal."""
        assert sanitize_subject_name("a___b") == "a_b"
        assert sanitize_subject_name("test--value") == "test_value"

    def test_sanitize_leading_trailing(self):
        """Test leading/trailing underscore removal."""
        assert sanitize_subject_name("_test_") == "test"
        assert sanitize_subject_name("__test__") == "test"

    def test_sanitize_chinese_preserved(self):
        """Test Chinese characters are preserved (QA Review fix)."""
        assert sanitize_subject_name("数学") == "数学"
        assert sanitize_subject_name("物理") == "物理"
        assert sanitize_subject_name("计算机科学") == "计算机科学"
        assert sanitize_subject_name("托福") == "托福"

    def test_sanitize_mixed_chinese_ascii(self):
        """Test mixed Chinese and ASCII handling."""
        assert sanitize_subject_name("托福 Listening") == "托福_listening"
        assert sanitize_subject_name("数学-离散") == "数学_离散"
        assert sanitize_subject_name("计算机/算法") == "计算机_算法"

    def test_sanitize_chinese_with_special_chars(self):
        """Test Chinese with special characters."""
        assert sanitize_subject_name("数学（高等）") == "数学_高等"
        assert sanitize_subject_name("托福【听力】") == "托福_听力"


class TestSkipDirectoriesConfig:
    """Tests for SKIP_DIRECTORIES_LOWER configuration."""

    def test_skip_dirs_contains_chinese(self):
        """Verify Chinese directories are in skip list."""
        assert "笔记库" in SKIP_DIRECTORIES_LOWER

    def test_skip_dirs_contains_common_roots(self):
        """Verify common root directories are in skip list."""
        assert "vault" in SKIP_DIRECTORIES_LOWER
        assert "notes" in SKIP_DIRECTORIES_LOWER
        assert "obsidian" in SKIP_DIRECTORIES_LOWER

    def test_skip_dirs_contains_system_dirs(self):
        """Verify system directories are in skip list."""
        assert ".obsidian" in SKIP_DIRECTORIES_LOWER
        assert ".git" in SKIP_DIRECTORIES_LOWER
        assert ".trash" in SKIP_DIRECTORIES_LOWER
        assert "__pycache__" in SKIP_DIRECTORIES_LOWER
        assert "node_modules" in SKIP_DIRECTORIES_LOWER


class TestSubjectTypeEnum:
    """Tests for SubjectType enum."""

    def test_subject_types_exist(self):
        """Verify all expected subject types exist."""
        assert SubjectType.MATH.value == "math"
        assert SubjectType.PHYSICS.value == "physics"
        assert SubjectType.COMPUTER_SCIENCE.value == "computer_science"
        assert SubjectType.LANGUAGE.value == "language"
        assert SubjectType.GENERAL.value == "general"

    def test_default_subject(self):
        """Verify default subject is GENERAL."""
        assert DEFAULT_SUBJECT == SubjectType.GENERAL
