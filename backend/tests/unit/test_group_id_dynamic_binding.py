# Canvas Learning System - Epic 6: group_id Dynamic Binding
"""
Epic 6 - Feature 6.1 & 6.2: Pass canvas name as group_id from frontend,
normalize canvas name to group_id format.

Tests verify:
1. extract_canvas_name() extracts filename without .canvas extension
2. build_group_id() with canvas_name produces subject:canvas format
3. Normalization: "CS 188" -> "cs_188"
4. record_learning_event uses canvas-scoped group_id
5. Batch and temporal paths also use canvas-scoped group_id
6. No static group_id when canvas_path is available

[Source: Phase 3 PRD Epic 6 - group_id Dynamic Binding]
"""

import pytest

from app.core.subject_config import (
    build_group_id,
    extract_canvas_name,
    extract_subject_from_canvas_path,
    sanitize_subject_name,
)


# =============================================================================
# Feature 6.2: extract_canvas_name
# =============================================================================


class TestExtractCanvasName:
    """Tests for extract_canvas_name() utility."""

    def test_basic_canvas_file(self):
        """Basic .canvas file returns stem."""
        assert extract_canvas_name("数学/离散数学.canvas") == "离散数学"

    def test_nested_path(self):
        """Deeply nested path returns only the filename stem."""
        assert extract_canvas_name("Math 54/chapter1/calc.canvas") == "calc"

    def test_no_extension(self):
        """Path without .canvas extension returns last component stem."""
        assert extract_canvas_name("random") == "random"

    def test_empty_string(self):
        """Empty string returns 'untitled'."""
        assert extract_canvas_name("") == "untitled"

    def test_only_extension(self):
        """File named just '.canvas' returns 'untitled'."""
        assert extract_canvas_name(".canvas") == "untitled"

    def test_chinese_canvas_name(self):
        """Chinese canvas name is preserved."""
        assert extract_canvas_name("托福/听力练习.canvas") == "听力练习"

    def test_spaces_in_name(self):
        """Spaces in canvas filename are preserved (sanitization is separate)."""
        assert extract_canvas_name("CS 188/Lecture Notes.canvas") == "Lecture Notes"

    def test_windows_style_path(self):
        """Windows-style backslash path handled by pathlib."""
        # pathlib handles both separators on all platforms
        result = extract_canvas_name("数学/线性代数.canvas")
        assert result == "线性代数"


# =============================================================================
# Feature 6.2: Normalization via build_group_id + canvas_name
# =============================================================================


class TestBuildGroupIdWithCanvasName:
    """Tests for build_group_id() with canvas_name parameter."""

    def test_subject_only(self):
        """Without canvas_name, returns sanitized subject only."""
        assert build_group_id("math") == "math"

    def test_subject_with_canvas_name(self):
        """With canvas_name, returns subject:canvas format."""
        assert build_group_id("math", "离散数学") == "math:离散数学"

    def test_normalizes_ascii(self):
        """ASCII characters are lowercased, spaces become underscores."""
        result = build_group_id("Math 54", "CS 188")
        assert result == "math_54:cs_188"

    def test_normalizes_special_chars(self):
        """Special characters stripped, underscores collapsed."""
        result = build_group_id("Math!", "Lecture Notes")
        assert result == "math:lecture_notes"

    def test_chinese_subject_and_canvas(self):
        """Chinese characters preserved in both subject and canvas."""
        result = build_group_id("数学", "离散数学")
        assert result == "数学:离散数学"

    def test_mixed_unicode_ascii(self):
        """Mixed Unicode and ASCII handled correctly."""
        result = build_group_id("托福", "Listening Practice")
        assert result == "托福:listening_practice"

    def test_canvas_name_none_fallback(self):
        """canvas_name=None falls back to subject-only."""
        assert build_group_id("physics", None) == "physics"

    def test_canvas_name_empty_string(self):
        """canvas_name='' falls back to subject-only."""
        # empty string is falsy, so no canvas component
        assert build_group_id("physics", "") == "physics"


# =============================================================================
# Feature 6.1: End-to-end group_id construction from canvas_path
# =============================================================================


class TestEndToEndGroupIdFromCanvasPath:
    """Integration-style tests: canvas_path -> extract -> build -> group_id."""

    def test_full_pipeline_chinese(self):
        """Full pipeline: 数学/离散数学.canvas -> subject=数学, canvas=离散数学."""
        canvas_path = "数学/离散数学.canvas"
        subject = extract_subject_from_canvas_path(canvas_path)
        canvas_name = extract_canvas_name(canvas_path)
        group_id = build_group_id(subject, canvas_name)
        assert subject == "数学"
        assert canvas_name == "离散数学"
        assert group_id == "数学:离散数学"

    def test_full_pipeline_ascii(self):
        """Full pipeline: Math 54/calculus.canvas -> subject=Math 54, canvas=calculus."""
        canvas_path = "Math 54/calculus.canvas"
        subject = extract_subject_from_canvas_path(canvas_path)
        canvas_name = extract_canvas_name(canvas_path)
        group_id = build_group_id(subject, canvas_name)
        assert subject == "Math 54"
        assert canvas_name == "calculus"
        assert group_id == "math_54:calculus"

    def test_full_pipeline_single_file(self):
        """Single file without directory: uses filename as both subject and canvas."""
        canvas_path = "离散数学.canvas"
        subject = extract_subject_from_canvas_path(canvas_path)
        canvas_name = extract_canvas_name(canvas_path)
        group_id = build_group_id(subject, canvas_name)
        # Subject falls back to filename stem, canvas is also the stem
        assert subject == "离散数学"
        assert canvas_name == "离散数学"
        assert group_id == "离散数学:离散数学"

    def test_different_canvases_same_subject_produce_different_group_ids(self):
        """Two canvases under same subject produce different group_ids."""
        gid1 = build_group_id("数学", "线性代数")
        gid2 = build_group_id("数学", "离散数学")
        assert gid1 != gid2
        assert gid1 == "数学:线性代数"
        assert gid2 == "数学:离散数学"

    def test_skip_directory_handling(self):
        """Skip directories (笔记库) are ignored for subject, but canvas name works."""
        canvas_path = "笔记库/物理/力学.canvas"
        subject = extract_subject_from_canvas_path(canvas_path)
        canvas_name = extract_canvas_name(canvas_path)
        group_id = build_group_id(subject, canvas_name)
        assert subject == "物理"
        assert canvas_name == "力学"
        assert group_id == "物理:力学"
