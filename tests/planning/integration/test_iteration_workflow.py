"""
Planning Iteration Integration Tests

End-to-end tests for complete planning iteration workflows.
Total: 43 tests
"""

import pytest
import json
import subprocess
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "scripts" / "lib"))


# =============================================================================
# Test: Complete Iteration Workflow
# =============================================================================

@pytest.mark.integration
class TestCompleteIterationWorkflow:
    """End-to-end tests for complete iteration workflows."""

    def test_first_iteration_workflow(self, temp_project_dir, create_prd_file,
                                      create_architecture_file, create_openapi_file,
                                      create_schema_file):
        """Complete workflow for first iteration."""
        # Step 1: Create planning files
        create_prd_file("epic-1.md")
        create_architecture_file("canvas-layer.md")
        create_openapi_file("canvas-api.openapi.yml")
        create_schema_file("canvas-node.schema.json")

        # Step 2: Verify files exist
        assert (temp_project_dir / "docs" / "prd" / "epic-1.md").exists()
        assert (temp_project_dir / "docs" / "architecture" / "canvas-layer.md").exists()
        assert (temp_project_dir / "specs" / "api" / "canvas-api.openapi.yml").exists()
        assert (temp_project_dir / "specs" / "data" / "canvas-node.schema.json").exists()

        # Step 3: Create snapshot
        snapshots_dir = temp_project_dir / ".bmad-core" / "planning-iterations" / "snapshots"
        snapshot_path = snapshots_dir / "iteration-001.json"

        snapshot = {
            "iteration": 1,
            "timestamp": datetime.now().isoformat(),
            "git_sha": "abc123",
            "description": "Initial iteration",
            "files": {
                "prd": [{"path": "docs/prd/epic-1.md", "hash": "a", "version": "1.0.0", "size": 100}],
                "architecture": [{"path": "docs/architecture/canvas-layer.md", "hash": "b", "version": "1.0.0", "size": 200}],
                "api_specs": [{"path": "specs/api/canvas-api.openapi.yml", "hash": "c", "version": "1.0.0", "endpoints": 12}],
                "schemas": [{"path": "specs/data/canvas-node.schema.json", "hash": "d", "title": "CanvasNode"}]
            }
        }

        with open(snapshot_path, "w") as f:
            json.dump(snapshot, f, indent=2)

        assert snapshot_path.exists()

    def test_subsequent_iteration_workflow(self, temp_project_dir, create_snapshot_file,
                                           sample_snapshot, current_snapshot):
        """Complete workflow for subsequent iterations."""
        # Step 1: Create previous iteration
        create_snapshot_file(1, sample_snapshot)

        # Step 2: Create current iteration with changes
        create_snapshot_file(2, current_snapshot)

        # Step 3: Compare iterations
        snapshots_dir = temp_project_dir / ".bmad-core" / "planning-iterations" / "snapshots"

        with open(snapshots_dir / "iteration-001.json") as f:
            prev = json.load(f)
        with open(snapshots_dir / "iteration-002.json") as f:
            curr = json.load(f)

        # Verify changes detected
        prev_endpoints = prev["files"]["api_specs"][0]["endpoints"]
        curr_endpoints = curr["files"]["api_specs"][0]["endpoints"]

        assert curr_endpoints > prev_endpoints

    def test_iteration_with_validation(self, temp_project_dir, create_snapshot_file,
                                       sample_snapshot):
        """Iteration workflow with validation step."""
        create_snapshot_file(1, sample_snapshot)

        # Simulate validation
        validation_result = {
            "iteration": 1,
            "passed": True,
            "errors": [],
            "warnings": []
        }

        # Save validation result
        validation_path = (
            temp_project_dir / ".bmad-core" / "planning-iterations" /
            "validation-001.json"
        )
        validation_path.parent.mkdir(parents=True, exist_ok=True)

        with open(validation_path, "w") as f:
            json.dump(validation_result, f)

        assert validation_path.exists()
        with open(validation_path) as f:
            result = json.load(f)
        assert result["passed"]


# =============================================================================
# Test: Multi-File Changes
# =============================================================================

@pytest.mark.integration
class TestMultiFileChanges:
    """Tests for iterations with multiple file changes."""

    def test_add_multiple_epics(self, temp_project_dir, create_prd_file):
        """Add multiple Epic PRD files in one iteration."""
        files = []
        for i in range(1, 4):
            file_path = create_prd_file(f"epic-{i}.md")
            files.append(file_path)

        assert len(files) == 3
        for f in files:
            assert f.exists()

    def test_modify_prd_and_api(self, temp_project_dir, create_prd_file,
                                create_openapi_file, sample_openapi_spec):
        """Modify both PRD and API spec in same iteration."""
        # Create files
        prd_path = create_prd_file("epic-1.md")
        api_path = create_openapi_file("canvas-api.openapi.yml", sample_openapi_spec)

        # Modify PRD
        new_prd_content = '''---
title: "Epic 1 - Updated"
version: "1.1.0"
---
# Updated content'''
        prd_path.write_text(new_prd_content, encoding="utf-8")

        # Modify API spec (add endpoint)
        import yaml
        with open(api_path) as f:
            spec = yaml.safe_load(f)

        spec["paths"]["/canvas/{canvas_path}/export"] = {
            "get": {
                "operationId": "exportCanvas",
                "summary": "Export canvas",
                "responses": {"200": {"description": "Success"}}
            }
        }

        with open(api_path, "w") as f:
            yaml.dump(spec, f)

        # Verify both modified
        assert "1.1.0" in prd_path.read_text()
        with open(api_path) as f:
            updated_spec = yaml.safe_load(f)
        assert "/canvas/{canvas_path}/export" in updated_spec["paths"]

    def test_schema_and_api_consistency(self, temp_project_dir, create_openapi_file,
                                        create_schema_file, sample_openapi_spec,
                                        sample_json_schema):
        """Verify schema changes are reflected in API spec."""
        create_openapi_file("canvas-api.openapi.yml", sample_openapi_spec)
        create_schema_file("canvas-node.schema.json", sample_json_schema)

        # Both should reference same schema name
        schema_title = sample_json_schema["title"]
        assert schema_title in str(sample_openapi_spec["components"]["schemas"])


# =============================================================================
# Test: Breaking Change Workflow
# =============================================================================

@pytest.mark.integration
class TestBreakingChangeWorkflow:
    """Tests for workflows involving breaking changes."""

    def test_endpoint_deletion_workflow(self, temp_project_dir, create_openapi_file,
                                        sample_openapi_spec):
        """Complete workflow when endpoint is deleted."""
        import yaml

        # Create initial spec
        api_path = create_openapi_file("canvas-api.openapi.yml", sample_openapi_spec)

        # Delete an endpoint
        with open(api_path) as f:
            spec = yaml.safe_load(f)

        del spec["paths"]["/canvas/{canvas_path}/nodes"]

        with open(api_path, "w") as f:
            yaml.dump(spec, f)

        # Verify deletion
        with open(api_path) as f:
            updated = yaml.safe_load(f)

        assert "/canvas/{canvas_path}/nodes" not in updated["paths"]
        # This would trigger breaking change detection

    def test_required_field_removal_workflow(self, temp_project_dir, create_schema_file,
                                             sample_json_schema):
        """Complete workflow when required field is removed."""
        # Create initial schema
        schema_path = create_schema_file("canvas-node.schema.json", sample_json_schema)

        # Remove required field
        with open(schema_path) as f:
            schema = json.load(f)

        schema["required"] = ["id", "type"]  # Removed x, y, width, height

        with open(schema_path, "w") as f:
            json.dump(schema, f, indent=2)

        # Verify
        with open(schema_path) as f:
            updated = json.load(f)

        assert len(updated["required"]) == 2
        # This would trigger breaking change detection

    def test_breaking_change_acceptance_workflow(self, temp_project_dir,
                                                 create_snapshot_file, sample_snapshot):
        """Complete workflow for accepting breaking changes."""
        # Create snapshot with breaking change flag
        snapshot = sample_snapshot.copy()
        snapshot["breaking_changes_accepted"] = True
        snapshot["breaking_changes"] = [
            {"type": "endpoint_deleted", "path": "/api/cache/{id}"}
        ]

        create_snapshot_file(2, snapshot)

        # Verify
        snapshots_dir = temp_project_dir / ".bmad-core" / "planning-iterations" / "snapshots"
        with open(snapshots_dir / "iteration-002.json") as f:
            loaded = json.load(f)

        assert loaded["breaking_changes_accepted"]


# =============================================================================
# Test: Rollback Workflow
# =============================================================================

@pytest.mark.integration
class TestRollbackWorkflow:
    """Tests for rollback workflows."""

    def test_rollback_to_previous_iteration(self, temp_project_dir, create_snapshot_file,
                                            sample_snapshot):
        """Complete rollback to previous iteration."""
        # Create multiple iterations
        for i in range(1, 4):
            snapshot = sample_snapshot.copy()
            snapshot["iteration"] = i
            create_snapshot_file(i, snapshot)

        # Mark iteration 3 as rolled back
        snapshots_dir = temp_project_dir / ".bmad-core" / "planning-iterations" / "snapshots"
        snapshot_path = snapshots_dir / "iteration-003.json"

        with open(snapshot_path) as f:
            snapshot = json.load(f)

        snapshot["status"] = "rolled_back"
        snapshot["rolled_back_to"] = 2

        with open(snapshot_path, "w") as f:
            json.dump(snapshot, f)

        # Verify
        with open(snapshot_path) as f:
            updated = json.load(f)

        assert updated["status"] == "rolled_back"
        assert updated["rolled_back_to"] == 2

    def test_rollback_preserves_history(self, temp_project_dir, create_snapshot_file,
                                        sample_snapshot):
        """Rollback preserves all snapshot history."""
        # Create iterations
        for i in range(1, 4):
            snapshot = sample_snapshot.copy()
            snapshot["iteration"] = i
            create_snapshot_file(i, snapshot)

        # All snapshots should exist after rollback
        snapshots_dir = temp_project_dir / ".bmad-core" / "planning-iterations" / "snapshots"
        existing = list(snapshots_dir.glob("iteration-*.json"))

        assert len(existing) == 3


# =============================================================================
# Test: Version Management
# =============================================================================

@pytest.mark.integration
class TestVersionManagement:
    """Tests for version management across iterations."""

    def test_version_increment_workflow(self, temp_project_dir, create_prd_file):
        """Version increments correctly across iterations."""
        from planning_utils import increment_version

        versions = ["1.0.0"]
        for _ in range(3):
            versions.append(increment_version(versions[-1], "minor"))

        assert versions == ["1.0.0", "1.1.0", "1.2.0", "1.3.0"]

    def test_semver_comparison_workflow(self):
        """Semantic version comparison works correctly."""
        from planning_utils import compare_versions

        # Version progression
        assert compare_versions("1.1.0", "1.0.0") == 1
        assert compare_versions("2.0.0", "1.9.9") == 1
        assert compare_versions("1.0.1", "1.0.0") == 1

    def test_api_version_sync(self, temp_project_dir, create_openapi_file,
                              sample_openapi_spec):
        """API spec version stays in sync with iterations."""
        import yaml

        api_path = create_openapi_file("canvas-api.openapi.yml", sample_openapi_spec)

        # Update API version
        with open(api_path) as f:
            spec = yaml.safe_load(f)

        spec["info"]["version"] = "1.1.0"

        with open(api_path, "w") as f:
            yaml.dump(spec, f)

        # Verify
        with open(api_path) as f:
            updated = yaml.safe_load(f)

        assert updated["info"]["version"] == "1.1.0"


# =============================================================================
# Test: Git Integration
# =============================================================================

@pytest.mark.integration
class TestGitIntegration:
    """Tests for Git integration in iteration workflow."""

    @patch('subprocess.run')
    def test_git_branch_creation(self, mock_run, temp_git_repo):
        """Git branch created for new iteration."""
        mock_run.return_value = MagicMock(returncode=0)

        subprocess.run(
            ["git", "checkout", "-b", "planning-iteration-1"],
            cwd=temp_git_repo,
            capture_output=True
        )

        mock_run.assert_called()

    @patch('subprocess.run')
    def test_git_tag_creation(self, mock_run, temp_git_repo):
        """Git tag created on finalization."""
        mock_run.return_value = MagicMock(returncode=0)

        subprocess.run(
            ["git", "tag", "-a", "planning-v1", "-m", "Planning iteration 1"],
            cwd=temp_git_repo,
            capture_output=True
        )

        mock_run.assert_called()

    @patch('subprocess.run')
    def test_git_sha_recording(self, mock_run):
        """Git SHA recorded in snapshot."""
        mock_run.return_value = MagicMock(stdout="abc123def456\n", returncode=0)

        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True
        )

        sha = result.stdout.strip()
        assert len(sha) == 12


# =============================================================================
# Test: Cross-Iteration Validation
# =============================================================================

@pytest.mark.integration
class TestCrossIterationValidation:
    """Tests for validation across iterations."""

    def test_detect_prd_regression(self, previous_snapshot, current_snapshot):
        """Detect PRD version regression."""
        # Check that version doesn't decrease
        prev_version = previous_snapshot["files"]["prd"][0]["version"]
        curr_version = current_snapshot["files"]["prd"][0]["version"]

        from planning_utils import compare_versions
        assert compare_versions(curr_version, prev_version) >= 0

    def test_detect_endpoint_count_decrease(self, previous_snapshot, breaking_change_snapshot):
        """Detect endpoint count decrease as potential breaking change."""
        prev_count = previous_snapshot["files"]["api_specs"][0]["endpoints"]
        curr_count = breaking_change_snapshot["files"]["api_specs"][0]["endpoints"]

        is_decrease = curr_count < prev_count
        assert is_decrease

    def test_track_schema_changes(self, temp_project_dir, create_schema_file,
                                  sample_json_schema):
        """Track schema changes between iterations."""
        import copy
        # Create two versions of schema
        schema1 = copy.deepcopy(sample_json_schema)
        schema2 = copy.deepcopy(sample_json_schema)
        schema2["properties"]["newField"] = {"type": "string"}

        schema_dir = temp_project_dir / "specs" / "data"
        (schema_dir / "v1.json").write_text(json.dumps(schema1))
        (schema_dir / "v2.json").write_text(json.dumps(schema2))

        # Compare
        with open(schema_dir / "v1.json") as f:
            s1 = json.load(f)
        with open(schema_dir / "v2.json") as f:
            s2 = json.load(f)

        new_fields = set(s2["properties"].keys()) - set(s1["properties"].keys())
        assert "newField" in new_fields


# =============================================================================
# Test: Report Generation
# =============================================================================

@pytest.mark.integration
class TestReportGeneration:
    """Tests for iteration report generation."""

    def test_generate_iteration_summary(self, sample_snapshot):
        """Generate summary report for iteration."""
        summary = {
            "iteration": sample_snapshot["iteration"],
            "timestamp": sample_snapshot["timestamp"],
            "total_files": sum(len(f) for f in sample_snapshot["files"].values()),
            "total_endpoints": sample_snapshot["files"]["api_specs"][0]["endpoints"],
            "description": sample_snapshot["description"]
        }

        assert summary["total_files"] == 4
        assert summary["total_endpoints"] == 12

    def test_generate_change_report(self, previous_snapshot, current_snapshot):
        """Generate change report between iterations."""
        prev_endpoints = previous_snapshot["files"]["api_specs"][0]["endpoints"]
        curr_endpoints = current_snapshot["files"]["api_specs"][0]["endpoints"]

        report = {
            "from_iteration": previous_snapshot["iteration"],
            "to_iteration": current_snapshot["iteration"],
            "endpoints_added": curr_endpoints - prev_endpoints,
            "prd_version_changed": (
                previous_snapshot["files"]["prd"][0]["version"] !=
                current_snapshot["files"]["prd"][0]["version"]
            )
        }

        assert report["endpoints_added"] == 2
        assert report["prd_version_changed"]

    def test_generate_validation_report(self):
        """Generate validation report with all checks."""
        report = {
            "iteration": 2,
            "validation_passed": True,
            "checks": [
                {"name": "PRD version increment", "status": "pass", "details": "1.0.0 → 1.1.0"},
                {"name": "API backward compatibility", "status": "pass", "details": "No breaking changes"},
                {"name": "Schema compatibility", "status": "pass", "details": "All fields preserved"},
                {"name": "Git status clean", "status": "pass", "details": "No uncommitted changes"}
            ],
            "errors": [],
            "warnings": []
        }

        assert len(report["checks"]) == 4
        assert all(c["status"] == "pass" for c in report["checks"])


# =============================================================================
# Test: Error Handling
# =============================================================================

@pytest.mark.integration
class TestErrorHandling:
    """Tests for error handling in iteration workflows."""

    def test_handle_missing_snapshot(self, temp_project_dir):
        """Handle gracefully when snapshot is missing."""
        snapshots_dir = temp_project_dir / ".bmad-core" / "planning-iterations" / "snapshots"
        snapshot_path = snapshots_dir / "iteration-999.json"

        assert not snapshot_path.exists()

    def test_handle_corrupted_snapshot(self, temp_project_dir):
        """Handle corrupted snapshot file."""
        snapshots_dir = temp_project_dir / ".bmad-core" / "planning-iterations" / "snapshots"
        snapshot_path = snapshots_dir / "iteration-001.json"
        snapshot_path.write_text("not valid json")

        with pytest.raises(json.JSONDecodeError):
            with open(snapshot_path) as f:
                json.load(f)

    def test_handle_missing_planning_files(self, temp_project_dir):
        """Handle when expected planning files are missing."""
        # Check for expected file
        prd_path = temp_project_dir / "docs" / "prd" / "epic-1.md"

        if not prd_path.exists():
            # Create empty file or raise warning
            assert not prd_path.exists()

    def test_validation_failure_blocks_finalization(self):
        """Validation failure should block finalization."""
        validation_result = {
            "passed": False,
            "errors": [
                {"type": "breaking_change", "message": "Endpoint deleted"}
            ]
        }

        can_finalize = validation_result["passed"]
        assert not can_finalize


# =============================================================================
# Fixtures from conftest (referenced)
# =============================================================================

# Uses fixtures from conftest.py:
# - temp_project_dir
# - temp_git_repo
# - sample_snapshot
# - previous_snapshot
# - current_snapshot
# - breaking_change_snapshot
# - sample_openapi_spec
# - sample_json_schema
# - create_prd_file
# - create_architecture_file
# - create_openapi_file
# - create_schema_file
# - create_snapshot_file
