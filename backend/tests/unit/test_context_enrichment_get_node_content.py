# Story 12.D.2: Unit tests for get_node_content() helper function
# Test Coverage Target: >= 90%
#
# [Source: ADR-008 - pytest testing framework]
# [Source: specs/data/canvas-node.schema.json#L24-L38 - node type definitions]
"""
Unit tests for the get_node_content() helper function in context_enrichment_service.py.

Tests cover all four Canvas node types:
- text: Returns node["text"] content
- file: Reads and returns file content from vault
- link: Returns node["url"]
- group: Returns empty string

Also tests error handling for missing/unreadable files.
"""

from pathlib import Path
from unittest.mock import patch

from app.services.context_enrichment_service import get_node_content


class TestGetNodeContentTextNode:
    """Tests for text type nodes."""

    def test_text_node_returns_text_content(self):
        """Text node returns text field content."""
        node = {
            "id": "test123",
            "type": "text",
            "text": "This is test content",
            "x": 100,
            "y": 200
        }
        result = get_node_content(node, "/fake/vault")
        assert result == "This is test content"

    def test_text_node_empty_text(self):
        """Text node with empty text returns empty string."""
        node = {
            "id": "test123",
            "type": "text",
            "text": "",
            "x": 100,
            "y": 200
        }
        result = get_node_content(node, "/fake/vault")
        assert result == ""

    def test_text_node_missing_text_field(self):
        """Text node missing text field returns empty string."""
        node = {
            "id": "test123",
            "type": "text",
            "x": 100,
            "y": 200
        }
        result = get_node_content(node, "/fake/vault")
        assert result == ""

    def test_default_type_is_text(self):
        """Node without type defaults to text type."""
        node = {
            "id": "test123",
            "text": "Default text content",
            "x": 100,
            "y": 200
        }
        result = get_node_content(node, "/fake/vault")
        assert result == "Default text content"


class TestGetNodeContentFileNode:
    """Tests for file type nodes."""

    def test_file_node_reads_file_content(self, tmp_path):
        """File node reads and returns file content."""
        # Create test file
        test_file = tmp_path / "notes" / "oral-explanation.md"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("# Oral Explanation\n\nThis is the explanation content.", encoding="utf-8")

        node = {
            "id": "file123",
            "type": "file",
            "file": "notes/oral-explanation.md",
            "x": 500,
            "y": 300
        }
        result = get_node_content(node, str(tmp_path))
        assert "# Oral Explanation" in result
        assert "This is the explanation content." in result

    def test_file_node_chinese_content(self, tmp_path):
        """File node correctly handles Chinese content."""
        test_file = tmp_path / "笔记" / "测试文件.md"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("# 中文测试\n\n这是中文内容。", encoding="utf-8")

        node = {
            "id": "file456",
            "type": "file",
            "file": "笔记/测试文件.md",
            "x": 500,
            "y": 300
        }
        result = get_node_content(node, str(tmp_path))
        assert "# 中文测试" in result
        assert "这是中文内容。" in result

    def test_file_node_not_found(self, tmp_path):
        """Missing file returns empty string, logs warning."""
        node = {
            "id": "file789",
            "type": "file",
            "file": "nonexistent/file.md",
            "x": 500,
            "y": 300
        }
        result = get_node_content(node, str(tmp_path))
        assert result == ""

    def test_file_node_missing_file_path(self):
        """File node without file field returns empty string."""
        node = {
            "id": "file000",
            "type": "file",
            "x": 500,
            "y": 300
        }
        result = get_node_content(node, "/fake/vault")
        assert result == ""

    def test_file_node_empty_file_path(self):
        """File node with empty file field returns empty string."""
        node = {
            "id": "file001",
            "type": "file",
            "file": "",
            "x": 500,
            "y": 300
        }
        result = get_node_content(node, "/fake/vault")
        assert result == ""

    def test_file_node_permission_error(self, tmp_path):
        """Permission denied returns empty string, logs warning."""
        node = {
            "id": "file_perm",
            "type": "file",
            "file": "protected/file.md",
            "x": 500,
            "y": 300
        }

        # Mock Path.read_text to raise PermissionError
        with patch.object(Path, 'read_text', side_effect=PermissionError("Access denied")):
            result = get_node_content(node, str(tmp_path))
            assert result == ""


class TestGetNodeContentLinkNode:
    """Tests for link type nodes."""

    def test_link_node_returns_url(self):
        """Link node returns url field."""
        node = {
            "id": "link123",
            "type": "link",
            "url": "https://example.com/resource",
            "x": 100,
            "y": 200
        }
        result = get_node_content(node, "/fake/vault")
        assert result == "https://example.com/resource"

    def test_link_node_missing_url(self):
        """Link node without url returns empty string."""
        node = {
            "id": "link456",
            "type": "link",
            "x": 100,
            "y": 200
        }
        result = get_node_content(node, "/fake/vault")
        assert result == ""

    def test_link_node_empty_url(self):
        """Link node with empty url returns empty string."""
        node = {
            "id": "link789",
            "type": "link",
            "url": "",
            "x": 100,
            "y": 200
        }
        result = get_node_content(node, "/fake/vault")
        assert result == ""


class TestGetNodeContentGroupNode:
    """Tests for group type nodes."""

    def test_group_node_returns_empty_string(self):
        """Group node returns empty string."""
        node = {
            "id": "group123",
            "type": "group",
            "x": 0,
            "y": 0,
            "width": 500,
            "height": 400
        }
        result = get_node_content(node, "/fake/vault")
        assert result == ""

    def test_group_node_with_label(self):
        """Group node with label still returns empty string (no text content)."""
        node = {
            "id": "group456",
            "type": "group",
            "label": "My Group",
            "x": 0,
            "y": 0,
            "width": 500,
            "height": 400
        }
        result = get_node_content(node, "/fake/vault")
        assert result == ""


class TestGetNodeContentUnknownType:
    """Tests for unknown/invalid node types."""

    def test_unknown_type_returns_empty_string(self):
        """Unknown type returns empty string, logs warning."""
        node = {
            "id": "unknown123",
            "type": "unknown_type",
            "x": 100,
            "y": 200
        }
        result = get_node_content(node, "/fake/vault")
        assert result == ""

    def test_invalid_type_returns_empty_string(self):
        """Invalid type value returns empty string."""
        node = {
            "id": "invalid123",
            "type": 12345,  # Invalid: type should be string
            "x": 100,
            "y": 200
        }
        result = get_node_content(node, "/fake/vault")
        assert result == ""


class TestGetNodeContentEdgeCases:
    """Edge case tests."""

    def test_empty_node_dict(self):
        """Empty node dict returns empty string (defaults to text type)."""
        node = {}
        result = get_node_content(node, "/fake/vault")
        assert result == ""

    def test_node_without_id(self):
        """Node without id still works (uses 'unknown' for logging)."""
        node = {
            "type": "text",
            "text": "No ID node"
        }
        result = get_node_content(node, "/fake/vault")
        assert result == "No ID node"

    def test_file_node_with_windows_path(self, tmp_path):
        """File node handles Windows-style paths correctly."""
        # pathlib.Path should handle both forward and backward slashes
        test_file = tmp_path / "folder" / "file.md"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("Windows path test", encoding="utf-8")

        node = {
            "id": "win123",
            "type": "file",
            "file": "folder/file.md",  # Canvas uses forward slashes
            "x": 500,
            "y": 300
        }
        result = get_node_content(node, str(tmp_path))
        assert result == "Windows path test"
