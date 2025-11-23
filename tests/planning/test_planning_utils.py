"""
Planning Utils Unit Tests

Unit tests for scripts/lib/planning_utils.py functions.
Total: 45 tests
"""

import pytest
import json
import tempfile
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts" / "lib"))

from planning_utils import (
    read_file, write_file, compute_file_hash,
    extract_frontmatter, update_frontmatter, get_version_from_frontmatter,
    read_openapi_spec, get_openapi_version, get_openapi_endpoints,
    get_git_sha, get_git_status, is_git_clean, create_git_tag,
    get_next_iteration_number, get_iteration_snapshot_path, load_snapshot, save_snapshot,
    parse_semver, compare_versions, increment_version,
    load_validation_rules, generate_markdown_report
)


# =============================================================================
# Test: File Operations
# =============================================================================

class TestFileOperations:
    """Tests for file read/write operations."""

    def test_read_file_utf8(self, tmp_path):
        """Read UTF-8 encoded file."""
        file_path = tmp_path / "test.md"
        content = "# Test\n\nContent with Chinese: 测试内容"
        file_path.write_text(content, encoding="utf-8")

        result = read_file(file_path)
        assert result == content

    def test_read_file_gbk_fallback(self, tmp_path):
        """Fall back to GBK encoding if UTF-8 fails."""
        file_path = tmp_path / "test_gbk.txt"
        content = "GBK编码内容"
        file_path.write_text(content, encoding="gbk")

        result = read_file(file_path)
        assert "编码内容" in result

    def test_write_file_creates_directories(self, tmp_path):
        """Automatically create parent directories when writing."""
        file_path = tmp_path / "nested" / "dir" / "test.txt"
        content = "Test content"

        write_file(file_path, content)

        assert file_path.exists()
        assert file_path.read_text(encoding="utf-8") == content

    def test_compute_file_hash_consistency(self, tmp_path):
        """Same content produces same hash."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        content = "Same content"

        file1.write_text(content, encoding="utf-8")
        file2.write_text(content, encoding="utf-8")

        hash1 = compute_file_hash(file1)
        hash2 = compute_file_hash(file2)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 produces 64 hex chars

    def test_compute_file_hash_empty_file(self, tmp_path):
        """Handle empty file hash computation."""
        empty_file = tmp_path / "empty.txt"
        empty_file.write_text("", encoding="utf-8")

        hash_result = compute_file_hash(empty_file)
        assert hash_result  # Should return valid hash

    def test_compute_file_hash_nonexistent_file(self, tmp_path):
        """Return empty string for non-existent file."""
        nonexistent = tmp_path / "does_not_exist.txt"

        hash_result = compute_file_hash(nonexistent)
        assert hash_result == ""


# =============================================================================
# Test: Frontmatter Handling
# =============================================================================

class TestFrontmatterHandling:
    """Tests for YAML frontmatter extraction and update."""

    def test_extract_frontmatter_valid(self):
        """Extract valid YAML frontmatter."""
        content = '''---
title: "Test Doc"
version: "1.0.0"
---

# Heading

Content here.'''

        frontmatter, body = extract_frontmatter(content)

        assert frontmatter is not None
        assert frontmatter["title"] == "Test Doc"
        assert frontmatter["version"] == "1.0.0"
        assert "# Heading" in body

    def test_extract_frontmatter_missing(self):
        """Handle content without frontmatter."""
        content = "# Just a heading\n\nNo frontmatter here."

        frontmatter, body = extract_frontmatter(content)

        assert frontmatter is None
        assert body == content

    def test_extract_frontmatter_invalid_yaml(self):
        """Handle invalid YAML in frontmatter."""
        content = '''---
title: [invalid yaml
---

Content'''

        frontmatter, body = extract_frontmatter(content)

        assert frontmatter is None

    def test_update_frontmatter_existing(self):
        """Update existing frontmatter fields."""
        content = '''---
title: "Old Title"
version: "1.0.0"
---

Content'''

        updated = update_frontmatter(content, {"version": "1.1.0"})

        frontmatter, _ = extract_frontmatter(updated)
        assert frontmatter["version"] == "1.1.0"
        assert frontmatter["title"] == "Old Title"

    def test_update_frontmatter_create_new(self):
        """Create frontmatter when none exists."""
        content = "# Just content"

        updated = update_frontmatter(content, {"version": "1.0.0"})

        frontmatter, _ = extract_frontmatter(updated)
        assert frontmatter["version"] == "1.0.0"

    def test_get_version_from_frontmatter(self, tmp_path):
        """Get version field from file's frontmatter."""
        file_path = tmp_path / "versioned.md"
        content = '''---
version: "2.5.0"
---

Content'''
        file_path.write_text(content, encoding="utf-8")

        version = get_version_from_frontmatter(file_path)
        assert version == "2.5.0"

    def test_get_version_from_frontmatter_missing(self, tmp_path):
        """Return None when version field is missing."""
        file_path = tmp_path / "no_version.md"
        content = '''---
title: "No version"
---

Content'''
        file_path.write_text(content, encoding="utf-8")

        version = get_version_from_frontmatter(file_path)
        assert version is None


# =============================================================================
# Test: OpenAPI Handling
# =============================================================================

class TestOpenAPIHandling:
    """Tests for OpenAPI spec operations."""

    def test_read_openapi_spec(self, tmp_path, sample_openapi_spec):
        """Read and parse OpenAPI YAML file."""
        import yaml
        file_path = tmp_path / "api.yml"
        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(sample_openapi_spec, f)

        spec = read_openapi_spec(file_path)
        assert spec["openapi"] == "3.0.3"
        assert spec["info"]["title"] == "Canvas API"

    def test_get_openapi_version(self, tmp_path, sample_openapi_spec):
        """Extract version from OpenAPI spec."""
        import yaml
        file_path = tmp_path / "api.yml"
        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(sample_openapi_spec, f)

        version = get_openapi_version(file_path)
        assert version == "1.0.0"

    def test_get_openapi_endpoints(self, sample_openapi_spec):
        """Get list of endpoint paths from spec."""
        endpoints = get_openapi_endpoints(sample_openapi_spec)

        assert "/canvas/{canvas_path}" in endpoints
        assert "/canvas/{canvas_path}/nodes" in endpoints

    def test_get_openapi_version_nonexistent(self, tmp_path):
        """Handle non-existent OpenAPI file."""
        nonexistent = tmp_path / "does_not_exist.yml"

        version = get_openapi_version(nonexistent)
        assert version is None


# =============================================================================
# Test: Git Operations
# =============================================================================

class TestGitOperations:
    """Tests for Git-related operations."""

    @patch('planning_utils.subprocess.run')
    def test_get_git_sha(self, mock_run):
        """Get current Git commit SHA."""
        mock_run.return_value = MagicMock(stdout="abc123def456\n", returncode=0)

        sha = get_git_sha()
        assert sha == "abc123def456"

    @patch('planning_utils.subprocess.run')
    def test_get_git_sha_error(self, mock_run):
        """Return empty string on Git error."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")

        sha = get_git_sha()
        assert sha == ""

    @patch('planning_utils.subprocess.run')
    def test_get_git_status(self, mock_run):
        """Get Git status output."""
        mock_run.return_value = MagicMock(stdout="M file.txt\n?? new.txt\n", returncode=0)

        status = get_git_status()
        assert "M file.txt" in status
        assert "?? new.txt" in status

    @patch('planning_utils.subprocess.run')
    def test_is_git_clean_true(self, mock_run):
        """Return True when Git working directory is clean."""
        mock_run.return_value = MagicMock(stdout="", returncode=0)

        assert is_git_clean() is True

    @patch('planning_utils.subprocess.run')
    def test_is_git_clean_false(self, mock_run):
        """Return False when Git has uncommitted changes."""
        mock_run.return_value = MagicMock(stdout="M file.txt\n", returncode=0)

        assert is_git_clean() is False


# =============================================================================
# Test: Iteration Management
# =============================================================================

class TestIterationManagement:
    """Tests for iteration number and snapshot management."""

    @patch('planning_utils.get_snapshots_dir')
    def test_get_next_iteration_number_first(self, mock_dir, tmp_path):
        """Return 1 for first iteration."""
        mock_dir.return_value = tmp_path / "snapshots"

        num = get_next_iteration_number()
        assert num == 1

    @patch('planning_utils.get_snapshots_dir')
    def test_get_next_iteration_number_increment(self, mock_dir, tmp_path):
        """Increment from existing iterations."""
        snapshots_dir = tmp_path / "snapshots"
        snapshots_dir.mkdir()
        (snapshots_dir / "iteration-001.json").write_text("{}")
        (snapshots_dir / "iteration-002.json").write_text("{}")
        mock_dir.return_value = snapshots_dir

        num = get_next_iteration_number()
        assert num == 3

    @patch('planning_utils.get_snapshots_dir')
    def test_get_iteration_snapshot_path(self, mock_dir, tmp_path):
        """Generate correct snapshot file path."""
        mock_dir.return_value = tmp_path / "snapshots"

        path = get_iteration_snapshot_path(5)
        assert path.name == "iteration-005.json"

    @patch('planning_utils.get_iteration_snapshot_path')
    def test_load_snapshot(self, mock_path, tmp_path, sample_snapshot):
        """Load snapshot from JSON file."""
        snapshot_file = tmp_path / "iteration-001.json"
        with open(snapshot_file, "w") as f:
            json.dump(sample_snapshot, f)
        mock_path.return_value = snapshot_file

        loaded = load_snapshot(1)
        assert loaded["iteration"] == 1
        assert "files" in loaded

    @patch('planning_utils.get_iteration_snapshot_path')
    def test_load_snapshot_nonexistent(self, mock_path, tmp_path):
        """Return None for non-existent snapshot."""
        mock_path.return_value = tmp_path / "does_not_exist.json"

        loaded = load_snapshot(999)
        assert loaded is None

    @patch('planning_utils.get_iteration_snapshot_path')
    def test_save_snapshot(self, mock_path, tmp_path, sample_snapshot, capsys):
        """Save snapshot to JSON file."""
        snapshot_file = tmp_path / "snapshots" / "iteration-001.json"
        mock_path.return_value = snapshot_file

        save_snapshot(sample_snapshot, 1)

        assert snapshot_file.exists()
        with open(snapshot_file, "r") as f:
            saved = json.load(f)
        assert saved["iteration"] == 1

    @patch('planning_utils.get_iteration_snapshot_path')
    def test_save_snapshot_creates_directory(self, mock_path, tmp_path, sample_snapshot):
        """Create parent directory when saving snapshot."""
        snapshot_file = tmp_path / "nested" / "dir" / "iteration-001.json"
        mock_path.return_value = snapshot_file

        save_snapshot(sample_snapshot, 1)

        assert snapshot_file.exists()


# =============================================================================
# Test: Version Comparison
# =============================================================================

class TestVersionComparison:
    """Tests for semantic versioning operations."""

    def test_parse_semver_standard(self):
        """Parse standard semantic version."""
        major, minor, patch = parse_semver("1.2.3")

        assert major == 1
        assert minor == 2
        assert patch == 3

    def test_parse_semver_with_v_prefix(self):
        """Parse version with 'v' prefix."""
        major, minor, patch = parse_semver("v2.0.0")

        assert major == 2
        assert minor == 0
        assert patch == 0

    def test_parse_semver_invalid(self):
        """Raise error for invalid version."""
        with pytest.raises(ValueError, match="Invalid semver"):
            parse_semver("not-a-version")

    def test_compare_versions_greater(self):
        """Compare: v1 > v2."""
        assert compare_versions("2.0.0", "1.9.9") == 1

    def test_compare_versions_equal(self):
        """Compare: v1 == v2."""
        assert compare_versions("1.0.0", "1.0.0") == 0

    def test_compare_versions_lesser(self):
        """Compare: v1 < v2."""
        assert compare_versions("1.0.0", "2.0.0") == -1

    def test_compare_versions_minor_difference(self):
        """Compare with minor version difference."""
        assert compare_versions("1.2.0", "1.1.9") == 1

    def test_increment_version_patch(self):
        """Increment patch version."""
        assert increment_version("1.2.3", "patch") == "1.2.4"

    def test_increment_version_minor(self):
        """Increment minor version."""
        assert increment_version("1.2.3", "minor") == "1.3.0"

    def test_increment_version_major(self):
        """Increment major version."""
        assert increment_version("1.2.3", "major") == "2.0.0"


# =============================================================================
# Test: Validation Rules Loading
# =============================================================================

class TestValidationRulesLoading:
    """Tests for loading validation rules."""

    @patch('planning_utils.get_validators_dir')
    def test_load_validation_rules(self, mock_dir, tmp_path, sample_validation_rules):
        """Load validation rules from YAML file."""
        import yaml
        validators_dir = tmp_path / "validators"
        validators_dir.mkdir()
        rules_file = validators_dir / "iteration-rules.yaml"
        with open(rules_file, "w") as f:
            yaml.dump(sample_validation_rules, f)
        mock_dir.return_value = validators_dir

        rules = load_validation_rules()
        assert rules["version"] == "1.0"
        assert "prd" in rules["rules"]

    @patch('planning_utils.get_validators_dir')
    def test_load_validation_rules_not_found(self, mock_dir, tmp_path):
        """Raise error when rules file not found."""
        mock_dir.return_value = tmp_path / "validators"

        with pytest.raises(FileNotFoundError):
            load_validation_rules()


# =============================================================================
# Test: Report Generation
# =============================================================================

class TestReportGeneration:
    """Tests for markdown report generation."""

    def test_generate_markdown_report(self):
        """Generate markdown report with sections."""
        sections = [
            {"title": "Summary", "content": "This is a summary."},
            {"title": "Details", "content": "- Item 1\n- Item 2"}
        ]

        report = generate_markdown_report("Test Report", sections)

        assert "# Test Report" in report
        assert "## Summary" in report
        assert "This is a summary." in report
        assert "## Details" in report
        assert "- Item 1" in report

    def test_generate_markdown_report_empty_sections(self):
        """Generate report with no sections."""
        report = generate_markdown_report("Empty Report", [])

        assert "# Empty Report" in report
        assert "**生成时间**" in report

    def test_generate_markdown_report_timestamp(self):
        """Report includes generation timestamp."""
        report = generate_markdown_report("Test", [])

        assert "**生成时间**:" in report


# =============================================================================
# Test: Edge Cases
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_frontmatter_with_unicode(self):
        """Handle Unicode in frontmatter."""
        content = '''---
title: "中文标题"
description: "包含特殊字符: ✅ ❌"
---

内容'''

        frontmatter, body = extract_frontmatter(content)
        assert frontmatter["title"] == "中文标题"

    def test_version_comparison_with_v_prefix(self):
        """Compare versions with and without 'v' prefix."""
        assert compare_versions("v1.0.0", "1.0.0") == 0

    def test_increment_version_zero_versions(self):
        """Increment from zero versions."""
        assert increment_version("0.0.0", "patch") == "0.0.1"
        assert increment_version("0.0.0", "minor") == "0.1.0"
        assert increment_version("0.0.0", "major") == "1.0.0"

    def test_compute_hash_binary_file(self, tmp_path):
        """Compute hash for binary file."""
        binary_file = tmp_path / "binary.bin"
        binary_file.write_bytes(b"\x00\x01\x02\x03\xff")

        hash_result = compute_file_hash(binary_file)
        assert len(hash_result) == 64
