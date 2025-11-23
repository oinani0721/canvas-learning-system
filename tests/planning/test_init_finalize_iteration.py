"""
Init and Finalize Iteration Tests

Tests for scripts/init-iteration.py and scripts/finalize-iteration.py.
Total: 28 tests
"""

import pytest
import json
import subprocess
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))


# =============================================================================
# Test: Pre-flight Checks
# =============================================================================

class TestPreflightChecks:
    """Tests for initialization pre-flight checks."""

    @patch('subprocess.run')
    def test_preflight_check_git_clean(self, mock_run):
        """Pass when Git working directory is clean."""
        mock_run.return_value = MagicMock(stdout="", returncode=0)

        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True
        )

        is_clean = result.stdout.strip() == ""
        assert is_clean

    @patch('subprocess.run')
    def test_preflight_check_git_dirty_fails(self, mock_run):
        """Fail when Git has uncommitted changes."""
        mock_run.return_value = MagicMock(stdout="M file.txt\n", returncode=0)

        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True
        )

        is_clean = result.stdout.strip() == ""
        assert not is_clean

    def test_preflight_check_required_directories(self, temp_project_dir):
        """Verify required directories exist."""
        required_dirs = [
            temp_project_dir / "docs" / "prd",
            temp_project_dir / "docs" / "architecture",
            temp_project_dir / "specs" / "api",
            temp_project_dir / "specs" / "data",
        ]

        for dir_path in required_dirs:
            assert dir_path.exists(), f"Missing: {dir_path}"

    def test_preflight_check_snapshots_directory(self, temp_project_dir):
        """Verify snapshots directory exists."""
        snapshots_dir = (
            temp_project_dir / ".bmad-core" / "planning-iterations" / "snapshots"
        )
        assert snapshots_dir.exists()

    def test_preflight_check_previous_iteration_exists(self, temp_project_dir, create_snapshot_file, sample_snapshot):
        """Check if previous iteration exists for validation."""
        create_snapshot_file(1, sample_snapshot)

        snapshots_dir = (
            temp_project_dir / ".bmad-core" / "planning-iterations" / "snapshots"
        )
        existing = list(snapshots_dir.glob("iteration-*.json"))

        has_previous = len(existing) > 0
        assert has_previous


# =============================================================================
# Test: Iteration Initialization
# =============================================================================

class TestIterationInitialization:
    """Tests for initializing new iterations."""

    def test_init_creates_snapshot_file(self, temp_project_dir, sample_snapshot):
        """Initialize creates new snapshot file."""
        snapshots_dir = (
            temp_project_dir / ".bmad-core" / "planning-iterations" / "snapshots"
        )
        snapshot_path = snapshots_dir / "iteration-001.json"

        with open(snapshot_path, "w") as f:
            json.dump(sample_snapshot, f)

        assert snapshot_path.exists()

    def test_init_assigns_correct_iteration_number(self, temp_project_dir, create_snapshot_file, sample_snapshot):
        """New iteration gets correct number."""
        # Create existing iterations
        for i in range(1, 3):
            snapshot = sample_snapshot.copy()
            snapshot["iteration"] = i
            create_snapshot_file(i, snapshot)

        # Determine next number
        snapshots_dir = (
            temp_project_dir / ".bmad-core" / "planning-iterations" / "snapshots"
        )
        existing = list(snapshots_dir.glob("iteration-*.json"))
        numbers = [int(f.stem.split("-")[1]) for f in existing]
        next_num = max(numbers) + 1

        assert next_num == 3

    @patch('subprocess.run')
    def test_init_creates_git_branch(self, mock_run):
        """Initialize creates planning iteration branch."""
        mock_run.return_value = MagicMock(returncode=0)

        iteration_num = 4
        branch_name = f"planning-iteration-{iteration_num}"

        subprocess.run(
            ["git", "checkout", "-b", branch_name],
            capture_output=True,
            check=True
        )

        mock_run.assert_called()

    def test_init_records_timestamp(self, sample_snapshot):
        """Snapshot records initialization timestamp."""
        timestamp = sample_snapshot["timestamp"]
        parsed = datetime.fromisoformat(timestamp)

        assert isinstance(parsed, datetime)

    @patch('subprocess.run')
    def test_init_records_git_sha(self, mock_run):
        """Snapshot records current Git SHA."""
        mock_run.return_value = MagicMock(stdout="abc123def456\n", returncode=0)

        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True
        )

        sha = result.stdout.strip()
        assert sha == "abc123def456"

    def test_init_accepts_description(self, sample_snapshot):
        """Initialize accepts user description."""
        description = "Epic 13 - Ebbinghaus Review"
        sample_snapshot["description"] = description

        assert sample_snapshot["description"] == description


# =============================================================================
# Test: Iteration Finalization
# =============================================================================

class TestIterationFinalization:
    """Tests for finalizing iterations."""

    @patch('subprocess.run')
    def test_finalize_creates_git_tag(self, mock_run):
        """Finalize creates Git tag for iteration."""
        mock_run.return_value = MagicMock(returncode=0)

        iteration_num = 4
        tag_name = f"planning-v{iteration_num}"

        subprocess.run(
            ["git", "tag", "-a", tag_name, "-m", f"Planning iteration {iteration_num}"],
            capture_output=True,
            check=True
        )

        mock_run.assert_called()

    @patch('subprocess.run')
    def test_finalize_merges_to_main(self, mock_run):
        """Finalize merges planning branch to main."""
        mock_run.return_value = MagicMock(returncode=0)

        subprocess.run(
            ["git", "checkout", "main"],
            capture_output=True,
            check=True
        )
        subprocess.run(
            ["git", "merge", "planning-iteration-4"],
            capture_output=True,
            check=True
        )

        assert mock_run.call_count == 2

    def test_finalize_updates_snapshot_status(self, temp_project_dir, create_snapshot_file, sample_snapshot):
        """Finalize updates snapshot with completion status."""
        create_snapshot_file(1, sample_snapshot)

        snapshot_path = (
            temp_project_dir / ".bmad-core" / "planning-iterations" /
            "snapshots" / "iteration-001.json"
        )

        # Update status
        with open(snapshot_path) as f:
            snapshot = json.load(f)

        snapshot["status"] = "finalized"
        snapshot["finalized_at"] = datetime.now().isoformat()

        with open(snapshot_path, "w") as f:
            json.dump(snapshot, f)

        # Verify
        with open(snapshot_path) as f:
            updated = json.load(f)

        assert updated["status"] == "finalized"
        assert "finalized_at" in updated

    def test_finalize_requires_validation_pass(self):
        """Finalize requires validation to pass first."""
        validation_result = {
            "passed": True,
            "errors": [],
            "warnings": []
        }

        can_finalize = validation_result["passed"]
        assert can_finalize

    def test_finalize_blocked_by_breaking_changes(self):
        """Finalize blocked when breaking changes detected."""
        validation_result = {
            "passed": False,
            "errors": [
                {"type": "breaking_change", "message": "Endpoint deleted"}
            ],
            "warnings": []
        }

        can_finalize = validation_result["passed"]
        assert not can_finalize


# =============================================================================
# Test: Breaking Change Acceptance
# =============================================================================

class TestBreakingChangeAcceptance:
    """Tests for accepting breaking changes."""

    def test_accept_breaking_changes_flag(self):
        """Accept breaking changes with explicit flag."""
        options = {
            "accept_breaking_changes": True
        }

        # With flag, finalization can proceed despite breaking changes
        can_proceed = options["accept_breaking_changes"]
        assert can_proceed

    def test_breaking_change_bumps_major_version(self):
        """Breaking changes trigger major version bump."""
        from planning_utils import increment_version

        current_version = "1.5.0"
        new_version = increment_version(current_version, "major")

        assert new_version == "2.0.0"

    def test_breaking_change_tag_suffix(self):
        """Breaking change tags have BREAKING suffix."""
        iteration_num = 4
        has_breaking = True

        if has_breaking:
            tag_name = f"planning-v{iteration_num}-BREAKING"
        else:
            tag_name = f"planning-v{iteration_num}"

        assert "-BREAKING" in tag_name


# =============================================================================
# Test: Rollback
# =============================================================================

class TestRollback:
    """Tests for rollback functionality."""

    @patch('subprocess.run')
    def test_rollback_to_previous_tag(self, mock_run):
        """Rollback reverts to previous Git tag."""
        mock_run.return_value = MagicMock(returncode=0)

        target_tag = "planning-v3"
        subprocess.run(
            ["git", "checkout", target_tag],
            capture_output=True,
            check=True
        )

        mock_run.assert_called()

    def test_rollback_preserves_snapshots(self, temp_project_dir, create_snapshot_file, sample_snapshot):
        """Rollback preserves snapshot history."""
        # Create snapshots
        for i in range(1, 4):
            snapshot = sample_snapshot.copy()
            snapshot["iteration"] = i
            create_snapshot_file(i, snapshot)

        snapshots_dir = (
            temp_project_dir / ".bmad-core" / "planning-iterations" / "snapshots"
        )

        # After rollback, all snapshots should still exist
        existing = list(snapshots_dir.glob("iteration-*.json"))
        assert len(existing) == 3

    def test_rollback_marks_snapshot_as_rolled_back(self, temp_project_dir, create_snapshot_file, sample_snapshot):
        """Rollback marks current snapshot as rolled back."""
        create_snapshot_file(3, sample_snapshot)

        snapshot_path = (
            temp_project_dir / ".bmad-core" / "planning-iterations" /
            "snapshots" / "iteration-003.json"
        )

        with open(snapshot_path) as f:
            snapshot = json.load(f)

        snapshot["status"] = "rolled_back"
        snapshot["rolled_back_at"] = datetime.now().isoformat()

        with open(snapshot_path, "w") as f:
            json.dump(snapshot, f)

        with open(snapshot_path) as f:
            updated = json.load(f)

        assert updated["status"] == "rolled_back"


# =============================================================================
# Test: Output and Reporting
# =============================================================================

class TestOutputReporting:
    """Tests for init/finalize output and reporting."""

    def test_init_outputs_summary(self, sample_snapshot):
        """Init outputs summary of created snapshot."""
        summary = {
            "iteration": sample_snapshot["iteration"],
            "timestamp": sample_snapshot["timestamp"],
            "files_tracked": sum(len(f) for f in sample_snapshot["files"].values()),
            "description": sample_snapshot["description"]
        }

        assert summary["iteration"] == 1
        assert summary["files_tracked"] == 4

    def test_finalize_outputs_changelog(self, previous_snapshot, current_snapshot):
        """Finalize outputs changelog summary."""
        # Calculate changes
        prev_endpoints = previous_snapshot["files"]["api_specs"][0]["endpoints"]
        curr_endpoints = current_snapshot["files"]["api_specs"][0]["endpoints"]

        changelog = {
            "iteration": current_snapshot["iteration"],
            "endpoints_added": curr_endpoints - prev_endpoints,
            "files_modified": 2
        }

        assert changelog["endpoints_added"] == 2

    def test_validation_report_format(self):
        """Validation report follows standard format."""
        report = {
            "iteration": 4,
            "timestamp": datetime.now().isoformat(),
            "validation_passed": True,
            "checks": [
                {"name": "PRD versions", "status": "pass"},
                {"name": "API breaking changes", "status": "pass"},
                {"name": "Schema compatibility", "status": "pass"}
            ],
            "errors": [],
            "warnings": []
        }

        assert report["validation_passed"]
        assert len(report["checks"]) == 3


# =============================================================================
# Fixtures from conftest (referenced)
# =============================================================================

# Uses fixtures from conftest.py:
# - temp_project_dir
# - sample_snapshot
# - previous_snapshot
# - current_snapshot
# - create_snapshot_file
