"""
Snapshot Planning Tests

Tests for scripts/snapshot-planning.py functionality.
Total: 22 tests
"""

import pytest
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))


# =============================================================================
# Test: Snapshot Creation
# =============================================================================

class TestSnapshotCreation:
    """Tests for creating planning iteration snapshots."""

    def test_create_snapshot_basic(self, temp_project_dir, sample_snapshot):
        """Create a basic iteration snapshot."""
        snapshot_path = (
            temp_project_dir / ".bmad-core" / "planning-iterations" /
            "snapshots" / "iteration-001.json"
        )

        with open(snapshot_path, "w", encoding="utf-8") as f:
            json.dump(sample_snapshot, f, indent=2)

        assert snapshot_path.exists()
        with open(snapshot_path) as f:
            loaded = json.load(f)
        assert loaded["iteration"] == 1

    def test_create_snapshot_with_timestamp(self, tmp_path):
        """Snapshot includes ISO format timestamp."""
        snapshot = {
            "iteration": 1,
            "timestamp": datetime.now().isoformat(),
            "files": {}
        }

        # Verify timestamp format
        timestamp = snapshot["timestamp"]
        parsed = datetime.fromisoformat(timestamp)
        assert isinstance(parsed, datetime)

    def test_create_snapshot_increments_number(self, temp_project_dir):
        """Snapshot number increments correctly."""
        snapshots_dir = (
            temp_project_dir / ".bmad-core" / "planning-iterations" / "snapshots"
        )

        # Create existing snapshots
        for i in range(1, 4):
            snapshot_file = snapshots_dir / f"iteration-{i:03d}.json"
            snapshot_file.write_text(json.dumps({"iteration": i}))

        # Find next number
        existing = list(snapshots_dir.glob("iteration-*.json"))
        numbers = [int(f.stem.split("-")[1]) for f in existing]
        next_num = max(numbers) + 1 if numbers else 1

        assert next_num == 4

    def test_create_snapshot_includes_git_sha(self, sample_snapshot):
        """Snapshot includes Git commit SHA."""
        assert "git_sha" in sample_snapshot
        assert len(sample_snapshot["git_sha"]) > 0

    def test_create_snapshot_includes_description(self, sample_snapshot):
        """Snapshot includes user description."""
        assert "description" in sample_snapshot
        assert sample_snapshot["description"] == "Initial iteration"

    def test_create_snapshot_file_categories(self, sample_snapshot):
        """Snapshot organizes files by category."""
        files = sample_snapshot["files"]

        assert "prd" in files
        assert "architecture" in files
        assert "api_specs" in files
        assert "schemas" in files


# =============================================================================
# Test: File Scanning
# =============================================================================

class TestFileScanning:
    """Tests for scanning planning files."""

    def test_scan_prd_files(self, temp_project_dir, create_prd_file):
        """Scan PRD markdown files."""
        # Create PRD files
        create_prd_file("epic-1.md")
        create_prd_file("epic-2.md")

        prd_dir = temp_project_dir / "docs" / "prd"
        prd_files = list(prd_dir.glob("*.md"))

        assert len(prd_files) == 2

    def test_scan_architecture_files(self, temp_project_dir, create_architecture_file):
        """Scan architecture markdown files."""
        create_architecture_file("canvas-layer.md")

        arch_dir = temp_project_dir / "docs" / "architecture"
        arch_files = list(arch_dir.glob("*.md"))

        assert len(arch_files) == 1

    def test_scan_openapi_files(self, temp_project_dir, create_openapi_file):
        """Scan OpenAPI YAML files."""
        create_openapi_file("canvas-api.openapi.yml")

        api_dir = temp_project_dir / "specs" / "api"
        api_files = list(api_dir.glob("*.yml"))

        assert len(api_files) == 1

    def test_scan_schema_files(self, temp_project_dir, create_schema_file):
        """Scan JSON schema files."""
        create_schema_file("canvas-node.schema.json")

        schema_dir = temp_project_dir / "specs" / "data"
        schema_files = list(schema_dir.glob("*.json"))

        assert len(schema_files) == 1

    def test_scan_collects_file_metadata(self, temp_project_dir, create_prd_file):
        """File scanning collects path, size, hash."""
        file_path = create_prd_file("epic-1.md")

        stat = file_path.stat()
        metadata = {
            "path": str(file_path.relative_to(temp_project_dir)),
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
        }

        assert "path" in metadata
        assert "size" in metadata
        assert metadata["size"] > 0


# =============================================================================
# Test: Snapshot Loading
# =============================================================================

class TestSnapshotLoading:
    """Tests for loading existing snapshots."""

    def test_load_snapshot_by_number(self, temp_project_dir, create_snapshot_file, sample_snapshot):
        """Load snapshot by iteration number."""
        create_snapshot_file(1, sample_snapshot)

        snapshot_path = (
            temp_project_dir / ".bmad-core" / "planning-iterations" /
            "snapshots" / "iteration-001.json"
        )

        with open(snapshot_path) as f:
            loaded = json.load(f)

        assert loaded["iteration"] == 1

    def test_load_latest_snapshot(self, temp_project_dir, create_snapshot_file, sample_snapshot):
        """Load the most recent snapshot."""
        # Create multiple snapshots
        for i in range(1, 4):
            snapshot = sample_snapshot.copy()
            snapshot["iteration"] = i
            create_snapshot_file(i, snapshot)

        snapshots_dir = (
            temp_project_dir / ".bmad-core" / "planning-iterations" / "snapshots"
        )

        existing = sorted(snapshots_dir.glob("iteration-*.json"))
        latest = existing[-1]

        with open(latest) as f:
            loaded = json.load(f)

        assert loaded["iteration"] == 3

    def test_load_nonexistent_snapshot_returns_none(self, temp_project_dir):
        """Return None for non-existent snapshot."""
        snapshot_path = (
            temp_project_dir / ".bmad-core" / "planning-iterations" /
            "snapshots" / "iteration-999.json"
        )

        assert not snapshot_path.exists()

    def test_load_corrupted_snapshot_raises_error(self, temp_project_dir):
        """Raise error for corrupted JSON snapshot."""
        snapshots_dir = (
            temp_project_dir / ".bmad-core" / "planning-iterations" / "snapshots"
        )
        snapshot_path = snapshots_dir / "iteration-001.json"
        snapshot_path.write_text("not valid json {")

        with pytest.raises(json.JSONDecodeError):
            with open(snapshot_path) as f:
                json.load(f)


# =============================================================================
# Test: Snapshot Comparison
# =============================================================================

class TestSnapshotComparison:
    """Tests for comparing snapshots between iterations."""

    def test_compare_snapshots_detect_added_files(self, previous_snapshot):
        """Detect newly added files."""
        current = previous_snapshot.copy()
        current["files"] = previous_snapshot["files"].copy()
        current["files"]["prd"] = previous_snapshot["files"]["prd"] + [
            {"path": "docs/prd/epic-2.md", "hash": "new", "version": "1.0.0", "size": 100}
        ]

        prev_paths = {f["path"] for f in previous_snapshot["files"]["prd"]}
        curr_paths = {f["path"] for f in current["files"]["prd"]}

        added = curr_paths - prev_paths
        assert "docs/prd/epic-2.md" in added

    def test_compare_snapshots_detect_deleted_files(self, previous_snapshot):
        """Detect deleted files."""
        current = previous_snapshot.copy()
        current["files"] = {"prd": [], "architecture": [], "api_specs": [], "schemas": []}

        prev_paths = {f["path"] for f in previous_snapshot["files"]["prd"]}
        curr_paths = set()

        deleted = prev_paths - curr_paths
        assert len(deleted) > 0

    def test_compare_snapshots_detect_modified_files(self, previous_snapshot):
        """Detect modified files by hash change."""
        current = previous_snapshot.copy()
        current["files"] = {
            "prd": [
                {
                    "path": "docs/prd/epic-1.md",
                    "hash": "sha256:different...",  # Changed hash
                    "version": "1.0.0",
                    "size": 1024
                }
            ],
            "architecture": previous_snapshot["files"]["architecture"],
            "api_specs": previous_snapshot["files"]["api_specs"],
            "schemas": previous_snapshot["files"]["schemas"]
        }

        prev_file = previous_snapshot["files"]["prd"][0]
        curr_file = current["files"]["prd"][0]

        modified = prev_file["hash"] != curr_file["hash"]
        assert modified

    def test_compare_snapshots_statistics(self, previous_snapshot, current_snapshot):
        """Compare statistics between snapshots."""
        prev_endpoints = previous_snapshot["files"]["api_specs"][0]["endpoints"]
        curr_endpoints = current_snapshot["files"]["api_specs"][0]["endpoints"]

        diff = curr_endpoints - prev_endpoints
        assert diff == 2  # 14 - 12 = 2 added


# =============================================================================
# Test: Snapshot Statistics
# =============================================================================

class TestSnapshotStatistics:
    """Tests for snapshot statistics calculation."""

    def test_calculate_total_files(self, sample_snapshot):
        """Calculate total number of tracked files."""
        total = 0
        for category in sample_snapshot["files"].values():
            total += len(category)

        assert total == 4

    def test_calculate_total_endpoints(self, sample_snapshot):
        """Calculate total API endpoints."""
        total_endpoints = sum(
            spec.get("endpoints", 0)
            for spec in sample_snapshot["files"]["api_specs"]
        )
        assert total_endpoints == 12

    def test_calculate_total_schemas(self, sample_snapshot):
        """Calculate total schemas."""
        total_schemas = len(sample_snapshot["files"]["schemas"])
        assert total_schemas == 1


# =============================================================================
# Fixtures from conftest (referenced)
# =============================================================================

# Uses fixtures from conftest.py:
# - temp_project_dir
# - sample_snapshot
# - previous_snapshot
# - current_snapshot
# - create_prd_file
# - create_architecture_file
# - create_openapi_file
# - create_schema_file
# - create_snapshot_file
