"""
Unit tests for Neo4j data migration script.

Story 30.1 - AC 3: migrate_neo4j_data.py with ftfy Unicode fixing

[Source: docs/stories/30.1.story.md - AC 3]
[Source: backend/scripts/migrate_neo4j_data.py]
"""

import json
import sys
import pytest
from pathlib import Path
from unittest.mock import patch

# Add scripts to path for import
_SCRIPTS_DIR = Path(__file__).parent.parent.parent / "scripts"
sys.path.insert(0, str(_SCRIPTS_DIR))

from migrate_neo4j_data import (
    fix_unicode_garbage,
    _fix_recursive,
    analyze_unicode_issues,
    migrate_json_data,
)


class TestFixUnicodeGarbage:
    """Test fix_unicode_garbage function."""

    def test_preserves_valid_chinese(self):
        """Normal Chinese text is not modified."""
        text = "这是正常的中文文本"
        assert fix_unicode_garbage(text) == text

    def test_preserves_valid_english(self):
        """Normal English text is not modified."""
        text = "Hello World 123"
        assert fix_unicode_garbage(text) == text

    def test_preserves_mixed_text(self):
        """Mixed Chinese/English text is not modified."""
        text = "Canvas 学习系统 v1.0"
        assert fix_unicode_garbage(text) == text

    def test_handles_empty_string(self):
        """Empty string returns empty string."""
        assert fix_unicode_garbage("") == ""

    def test_handles_non_string_input(self):
        """Non-string input is returned as-is."""
        assert fix_unicode_garbage(123) == 123
        assert fix_unicode_garbage(None) is None
        assert fix_unicode_garbage(True) is True

    def test_output_is_valid_utf8(self):
        """Output is always valid UTF-8."""
        # Input with potential encoding issues
        text = "test\x80text"  # Invalid byte
        result = fix_unicode_garbage(text)
        # Should not raise on encode
        result.encode("utf-8")


class TestFixRecursive:
    """Test _fix_recursive function."""

    def test_fixes_string(self):
        """Fixes a plain string."""
        result = _fix_recursive("Hello")
        assert result == "Hello"

    def test_fixes_dict_values(self):
        """Fixes all string values in a dict."""
        data = {"name": "正常", "count": 42, "active": True}
        result = _fix_recursive(data)
        assert result["name"] == "正常"
        assert result["count"] == 42
        assert result["active"] is True

    def test_fixes_nested_dict(self):
        """Recursively fixes nested dicts."""
        data = {
            "outer": {
                "inner": {
                    "text": "正常中文"
                }
            }
        }
        result = _fix_recursive(data)
        assert result["outer"]["inner"]["text"] == "正常中文"

    def test_fixes_list_items(self):
        """Fixes all string items in a list."""
        data = ["正常", 42, "Hello"]
        result = _fix_recursive(data)
        assert result == ["正常", 42, "Hello"]

    def test_fixes_nested_list(self):
        """Recursively fixes nested lists."""
        data = [["正常"], [{"text": "Hello"}]]
        result = _fix_recursive(data)
        assert result[0][0] == "正常"
        assert result[1][0]["text"] == "Hello"

    def test_passthrough_int(self):
        """Integers pass through unchanged."""
        assert _fix_recursive(42) == 42

    def test_passthrough_float(self):
        """Floats pass through unchanged."""
        assert _fix_recursive(3.14) == 3.14

    def test_passthrough_bool(self):
        """Booleans pass through unchanged."""
        assert _fix_recursive(True) is True
        assert _fix_recursive(False) is False

    def test_passthrough_none(self):
        """None passes through unchanged."""
        assert _fix_recursive(None) is None

    def test_complex_nested_structure(self):
        """Fixes a complex nested structure mimicking real data."""
        data = {
            "memories": [
                {
                    "content": "学习笔记",
                    "metadata": {
                        "tags": ["数学", "物理"],
                        "score": 0.95,
                    },
                },
            ],
            "metadata": {"version": 1},
        }
        result = _fix_recursive(data)
        assert result["memories"][0]["content"] == "学习笔记"
        assert result["memories"][0]["metadata"]["tags"] == ["数学", "物理"]
        assert result["memories"][0]["metadata"]["score"] == 0.95


class TestAnalyzeUnicodeIssues:
    """Test analyze_unicode_issues function."""

    def test_clean_data_returns_empty(self):
        """Clean data produces no issues."""
        data = {"name": "正常中文", "count": 42}
        issues = analyze_unicode_issues(data)
        assert issues == []

    def test_clean_nested_data_returns_empty(self):
        """Clean nested data produces no issues."""
        data = {
            "memories": [
                {"content": "Hello World"},
                {"content": "正常中文"},
            ]
        }
        issues = analyze_unicode_issues(data)
        assert issues == []

    def test_returns_path_for_issues(self):
        """Issues include the JSON path to problematic values."""
        # Create data that ftfy would fix
        # Using a common mojibake pattern: UTF-8 decoded as Latin-1
        try:
            import ftfy
            # "—" (em dash) mojibaked
            garbled = "â\x80\x93"
            fixed = ftfy.fix_text(garbled)
            if garbled != fixed:
                data = {"text": garbled}
                issues = analyze_unicode_issues(data)
                assert len(issues) >= 1
                assert issues[0][0] == "text"  # JSON path
            else:
                pytest.skip("ftfy did not fix test input")
        except ImportError:
            pytest.skip("ftfy not installed")

    def test_analyzes_nested_list(self):
        """Analyzes items in nested lists with correct path."""
        try:
            import ftfy
            garbled = "â\x80\x93"
            fixed = ftfy.fix_text(garbled)
            if garbled != fixed:
                data = {"items": [garbled]}
                issues = analyze_unicode_issues(data)
                assert len(issues) >= 1
                assert "items[0]" in issues[0][0]
            else:
                pytest.skip("ftfy did not fix test input")
        except ImportError:
            pytest.skip("ftfy not installed")


class TestMigrateJsonData:
    """Test migrate_json_data function."""

    def test_dry_run_does_not_modify_file(self, tmp_path):
        """--dry-run mode does not write changes to disk."""
        data = {"memories": [{"content": "正常"}]}
        source = tmp_path / "test.json"
        source.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

        original_content = source.read_text(encoding="utf-8")

        migrate_json_data(source=source, dry_run=True, force=True)

        assert source.read_text(encoding="utf-8") == original_content

    def test_dry_run_no_backup_created(self, tmp_path):
        """--dry-run mode does not create backup files."""
        data = {"memories": []}
        source = tmp_path / "test.json"
        source.write_text(json.dumps(data), encoding="utf-8")

        migrate_json_data(source=source, dry_run=True, force=True)

        backup_files = list(tmp_path.glob("*.bak*"))
        assert len(backup_files) == 0

    def test_migration_creates_backup(self, tmp_path):
        """Migration creates .bak backup file before writing."""
        data = {"memories": [{"content": "test"}]}
        source = tmp_path / "test.json"
        source.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

        migrate_json_data(source=source, dry_run=False, force=True)

        backup_files = list(tmp_path.glob("*.bak*"))
        assert len(backup_files) >= 1, "No backup file created"

    def test_migration_preserves_valid_data(self, tmp_path):
        """Migration preserves data that has no Unicode issues."""
        data = {"memories": [{"content": "正常中文"}, {"content": "Hello"}]}
        source = tmp_path / "test.json"
        source.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

        result = migrate_json_data(source=source, dry_run=False, force=True)

        assert result["memories"][0]["content"] == "正常中文"
        assert result["memories"][1]["content"] == "Hello"

    def test_migration_writes_utf8(self, tmp_path):
        """Migration writes output in UTF-8 with ensure_ascii=False."""
        data = {"content": "中文"}
        source = tmp_path / "test.json"
        source.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

        migrate_json_data(source=source, dry_run=False, force=True)

        # Read the file and verify it's valid UTF-8 JSON
        written = source.read_text(encoding="utf-8")
        parsed = json.loads(written)
        assert parsed["content"] == "中文"
        # Verify not escaped as \uXXXX
        assert "\\u" not in written

    def test_source_not_found_exits(self, tmp_path):
        """Non-existent source file causes sys.exit(1)."""
        fake_path = tmp_path / "nonexistent.json"

        with pytest.raises(SystemExit) as exc_info:
            migrate_json_data(source=fake_path)

        assert exc_info.value.code == 1

    def test_invalid_json_exits(self, tmp_path):
        """Invalid JSON source file causes sys.exit(1)."""
        source = tmp_path / "bad.json"
        source.write_text("not valid json {{{", encoding="utf-8")

        with pytest.raises(SystemExit) as exc_info:
            migrate_json_data(source=source)

        assert exc_info.value.code == 1

    def test_migration_returns_fixed_data(self, tmp_path):
        """Migration returns the fixed data dict."""
        data = {"key": "value", "num": 42}
        source = tmp_path / "test.json"
        source.write_text(json.dumps(data), encoding="utf-8")

        result = migrate_json_data(source=source, dry_run=True, force=True)

        assert isinstance(result, dict)
        assert result["key"] == "value"
        assert result["num"] == 42


class TestFixUnicodeGarbageFallback:
    """Test fix_unicode_garbage fallback when ftfy is unavailable."""

    def test_fallback_handles_valid_text(self):
        """Fallback mode preserves valid text."""
        with patch("migrate_neo4j_data.HAS_FTFY", False):
            result = fix_unicode_garbage("正常中文 Hello")
            assert result == "正常中文 Hello"

    def test_fallback_handles_empty_string(self):
        """Fallback mode handles empty string."""
        with patch("migrate_neo4j_data.HAS_FTFY", False):
            result = fix_unicode_garbage("")
            assert result == ""

    def test_fallback_returns_valid_utf8(self):
        """Fallback mode output is valid UTF-8."""
        with patch("migrate_neo4j_data.HAS_FTFY", False):
            result = fix_unicode_garbage("test text")
            result.encode("utf-8")  # Should not raise
