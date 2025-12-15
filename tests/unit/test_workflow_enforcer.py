"""
Unit tests for WorkflowEnforcer

Tests for BMad workflow enforcement mechanism:
- Legacy Epic detection (Epic 1-20 skip)
- Story status parsing
- YAML status retrieval
- State transition validation
- Commit readiness validation

Author: Canvas Learning System Team
Created: 2025-12-11
"""

import tempfile
from pathlib import Path

import pytest
import yaml

from src.bmad_orchestrator.workflow_enforcer import (
    ALLOWED_TRANSITIONS,
    COMMIT_READY_STATUSES,
    StoryStatus,
    ValidationResult,
    WorkflowEnforcer,
    is_legacy_story,
    validate_story_for_commit,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory with test files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)

        # Create directory structure
        (base / "docs" / "stories").mkdir(parents=True)
        (base / ".bmad-core" / "data").mkdir(parents=True)
        (base / "logs").mkdir(parents=True)

        yield base


@pytest.fixture
def sample_story_draft(temp_project_dir):
    """Create a sample story file in Draft status"""
    story_content = """# Story 21.1: Test Story

---
document_type: "Story"
version: "1.0.0"
status: "draft"
epic_id: "21"
story_id: "21.1"

reviewers:
  - name: "PO Agent"
    role: "Product Owner"
    approved: false
---

## Status

- [x] Draft
- [ ] Ready for Dev
- [ ] In Progress
- [ ] QA Review
- [ ] Done

## Story Overview

Test story content.
"""
    story_file = temp_project_dir / "docs" / "stories" / "21.1.story.md"
    story_file.write_text(story_content, encoding="utf-8")
    return story_file


@pytest.fixture
def sample_story_review(temp_project_dir):
    """Create a sample story file in Review status"""
    story_content = """# Story 21.2: Test Story Review

---
document_type: "Story"
version: "1.0.0"
status: "review"
epic_id: "21"
story_id: "21.2"

reviewers:
  - name: "PO Agent"
    role: "Product Owner"
    approved: true
---

## Status

- [x] Draft
- [x] Ready for Dev
- [x] In Progress
- [x] QA Review
- [ ] Done

## Story Overview

Test story in review status.
"""
    story_file = temp_project_dir / "docs" / "stories" / "21.2.story.md"
    story_file.write_text(story_content, encoding="utf-8")
    return story_file


@pytest.fixture
def sample_yaml_status(temp_project_dir):
    """Create a sample YAML status file"""
    yaml_content = {
        "project": {
            "name": "Canvas Learning System",
            "phase": "implementation",
        },
        "epics": {
            "epic-20": {
                "name": "Backend Stability",
                "status": "completed",
                "stories": ["20.1", "20.2", "20.3", "20.4"],
            },
            "epic-21": {
                "name": "Workflow Enforcement",
                "status": "in_progress",
                "stories": [
                    {"id": "21.1", "status": "draft"},
                    {"id": "21.2", "status": "review"},
                ],
            },
        },
    }

    yaml_file = temp_project_dir / ".bmad-core" / "data" / "canvas-project-status.yaml"
    with open(yaml_file, "w", encoding="utf-8") as f:
        yaml.dump(yaml_content, f, allow_unicode=True)
    return yaml_file


# ============================================================================
# StoryStatus Enum Tests
# ============================================================================


class TestStoryStatus:
    """Tests for StoryStatus enum"""

    def test_from_string_exact_match(self):
        """Test exact status string matching"""
        assert StoryStatus.from_string("Draft") == StoryStatus.DRAFT
        assert StoryStatus.from_string("Approved") == StoryStatus.APPROVED
        assert StoryStatus.from_string("InProgress") == StoryStatus.IN_PROGRESS
        assert StoryStatus.from_string("Review") == StoryStatus.REVIEW
        assert StoryStatus.from_string("Done") == StoryStatus.DONE

    def test_from_string_case_insensitive(self):
        """Test case-insensitive matching"""
        assert StoryStatus.from_string("draft") == StoryStatus.DRAFT
        assert StoryStatus.from_string("DRAFT") == StoryStatus.DRAFT
        assert StoryStatus.from_string("DrAfT") == StoryStatus.DRAFT

    def test_from_string_aliases(self):
        """Test status aliases"""
        assert StoryStatus.from_string("ready for dev") == StoryStatus.APPROVED
        assert StoryStatus.from_string("ready") == StoryStatus.APPROVED
        assert StoryStatus.from_string("in progress") == StoryStatus.IN_PROGRESS
        assert StoryStatus.from_string("development") == StoryStatus.IN_PROGRESS
        assert StoryStatus.from_string("qa review") == StoryStatus.REVIEW
        assert StoryStatus.from_string("qa") == StoryStatus.REVIEW
        assert StoryStatus.from_string("completed") == StoryStatus.DONE
        assert StoryStatus.from_string("complete") == StoryStatus.DONE

    def test_from_string_unknown(self):
        """Test unknown status strings"""
        assert StoryStatus.from_string("invalid") == StoryStatus.UNKNOWN
        assert StoryStatus.from_string("") == StoryStatus.UNKNOWN
        assert StoryStatus.from_string("random text") == StoryStatus.UNKNOWN


# ============================================================================
# State Transition Tests
# ============================================================================


class TestStateTransitions:
    """Tests for state transition validation"""

    def test_allowed_transitions_from_draft(self):
        """Draft can only go to Approved"""
        assert StoryStatus.APPROVED in ALLOWED_TRANSITIONS[StoryStatus.DRAFT]
        assert StoryStatus.IN_PROGRESS not in ALLOWED_TRANSITIONS[StoryStatus.DRAFT]
        assert StoryStatus.DONE not in ALLOWED_TRANSITIONS[StoryStatus.DRAFT]

    def test_allowed_transitions_from_approved(self):
        """Approved can only go to InProgress"""
        assert StoryStatus.IN_PROGRESS in ALLOWED_TRANSITIONS[StoryStatus.APPROVED]
        assert StoryStatus.REVIEW not in ALLOWED_TRANSITIONS[StoryStatus.APPROVED]

    def test_allowed_transitions_from_review(self):
        """Review can go to Done or back to InProgress"""
        assert StoryStatus.DONE in ALLOWED_TRANSITIONS[StoryStatus.REVIEW]
        assert StoryStatus.IN_PROGRESS in ALLOWED_TRANSITIONS[StoryStatus.REVIEW]

    def test_done_is_terminal(self):
        """Done is a terminal state"""
        assert len(ALLOWED_TRANSITIONS[StoryStatus.DONE]) == 0

    def test_commit_ready_statuses(self):
        """Only Review and Done are commit-ready"""
        assert StoryStatus.REVIEW in COMMIT_READY_STATUSES
        assert StoryStatus.DONE in COMMIT_READY_STATUSES
        assert StoryStatus.DRAFT not in COMMIT_READY_STATUSES
        assert StoryStatus.APPROVED not in COMMIT_READY_STATUSES
        assert StoryStatus.IN_PROGRESS not in COMMIT_READY_STATUSES


# ============================================================================
# Legacy Epic Tests
# ============================================================================


class TestLegacyEpic:
    """Tests for legacy Epic detection"""

    def test_legacy_epic_detection(self, temp_project_dir):
        """Test that Epic 1-20 are detected as legacy"""
        enforcer = WorkflowEnforcer(temp_project_dir)

        # Legacy Epics (1-20)
        assert enforcer.is_legacy_epic("1.1") is True
        assert enforcer.is_legacy_epic("5.3") is True
        assert enforcer.is_legacy_epic("10.1") is True
        assert enforcer.is_legacy_epic("20.1") is True
        assert enforcer.is_legacy_epic("20.99") is True

    def test_non_legacy_epic_detection(self, temp_project_dir):
        """Test that Epic 21+ are not legacy"""
        enforcer = WorkflowEnforcer(temp_project_dir)

        # Non-legacy Epics (21+)
        assert enforcer.is_legacy_epic("21.1") is False
        assert enforcer.is_legacy_epic("25.3") is False
        assert enforcer.is_legacy_epic("100.1") is False

    def test_invalid_story_id_is_legacy(self, temp_project_dir):
        """Invalid story IDs default to legacy (safe fallback)"""
        enforcer = WorkflowEnforcer(temp_project_dir)

        assert enforcer.is_legacy_epic("invalid") is True
        assert enforcer.is_legacy_epic("") is True
        assert enforcer.is_legacy_epic("abc.def") is True

    def test_is_legacy_story_helper(self):
        """Test the helper function"""
        assert is_legacy_story("1.1") is True
        assert is_legacy_story("20.1") is True
        assert is_legacy_story("21.1") is False


# ============================================================================
# Story Parsing Tests
# ============================================================================


class TestStoryParsing:
    """Tests for Story file parsing"""

    def test_parse_draft_story(self, temp_project_dir, sample_story_draft):
        """Test parsing a story in Draft status"""
        enforcer = WorkflowEnforcer(temp_project_dir)
        status, meta = enforcer.parse_story_status("21.1")

        assert status == StoryStatus.DRAFT
        assert "frontmatter" in meta or "source" in meta

    def test_parse_review_story(self, temp_project_dir, sample_story_review):
        """Test parsing a story in Review status"""
        enforcer = WorkflowEnforcer(temp_project_dir)
        status, meta = enforcer.parse_story_status("21.2")

        assert status == StoryStatus.REVIEW

    def test_parse_nonexistent_story(self, temp_project_dir):
        """Test parsing a non-existent story returns Unknown"""
        enforcer = WorkflowEnforcer(temp_project_dir)
        status, meta = enforcer.parse_story_status("99.99")

        assert status == StoryStatus.UNKNOWN
        assert "error" in meta


# ============================================================================
# YAML Status Tests
# ============================================================================


class TestYamlStatus:
    """Tests for YAML status retrieval"""

    def test_get_yaml_status_draft(self, temp_project_dir, sample_yaml_status):
        """Test getting draft status from YAML"""
        enforcer = WorkflowEnforcer(temp_project_dir)
        status_str, meta = enforcer.get_yaml_status("21.1")

        assert status_str == "draft"

    def test_get_yaml_status_review(self, temp_project_dir, sample_yaml_status):
        """Test getting review status from YAML"""
        enforcer = WorkflowEnforcer(temp_project_dir)
        status_str, meta = enforcer.get_yaml_status("21.2")

        assert status_str == "review"

    def test_get_yaml_status_completed_epic(self, temp_project_dir, sample_yaml_status):
        """Test getting status from completed Epic"""
        enforcer = WorkflowEnforcer(temp_project_dir)
        status_str, meta = enforcer.get_yaml_status("20.1")

        assert status_str == "completed"

    def test_get_yaml_status_nonexistent(self, temp_project_dir, sample_yaml_status):
        """Test getting status for non-existent story"""
        enforcer = WorkflowEnforcer(temp_project_dir)
        status_str, meta = enforcer.get_yaml_status("99.99")

        assert "error" in meta


# ============================================================================
# Transition Validation Tests
# ============================================================================


class TestTransitionValidation:
    """Tests for state transition validation"""

    def test_valid_transition_draft_to_approved(self, temp_project_dir):
        """Test valid transition: Draft → Approved"""
        enforcer = WorkflowEnforcer(temp_project_dir)
        is_valid, error = enforcer.validate_transition(
            StoryStatus.DRAFT, StoryStatus.APPROVED
        )
        assert is_valid is True
        assert error == ""

    def test_invalid_transition_draft_to_done(self, temp_project_dir):
        """Test invalid transition: Draft → Done (skips phases)"""
        enforcer = WorkflowEnforcer(temp_project_dir)
        is_valid, error = enforcer.validate_transition(
            StoryStatus.DRAFT, StoryStatus.DONE
        )
        assert is_valid is False
        assert "Invalid transition" in error

    def test_valid_transition_review_to_inprogress(self, temp_project_dir):
        """Test valid transition: Review → InProgress (return for fixes)"""
        enforcer = WorkflowEnforcer(temp_project_dir)
        is_valid, error = enforcer.validate_transition(
            StoryStatus.REVIEW, StoryStatus.IN_PROGRESS
        )
        assert is_valid is True


# ============================================================================
# Commit Readiness Tests
# ============================================================================


class TestCommitReadiness:
    """Tests for commit readiness validation"""

    def test_legacy_story_always_passes(self, temp_project_dir):
        """Legacy stories (Epic 1-20) always pass"""
        enforcer = WorkflowEnforcer(temp_project_dir)
        result = enforcer.validate_commit_ready("15.1")

        assert result.passed is True
        assert result.details.get("skipped") is True
        assert "Legacy" in result.details.get("reason", "")

    def test_draft_story_fails(self, temp_project_dir, sample_story_draft, sample_yaml_status):
        """Draft story fails commit validation"""
        enforcer = WorkflowEnforcer(temp_project_dir)
        result = enforcer.validate_commit_ready("21.1")

        assert result.passed is False
        assert result.current_status == StoryStatus.DRAFT
        assert "BLOCKED" in result.error_message

    def test_review_story_passes(self, temp_project_dir, sample_story_review, sample_yaml_status):
        """Review story passes commit validation"""
        enforcer = WorkflowEnforcer(temp_project_dir)
        result = enforcer.validate_commit_ready("21.2")

        assert result.passed is True
        assert result.current_status == StoryStatus.REVIEW

    def test_validation_result_contains_workflow_phases(
        self, temp_project_dir, sample_story_draft, sample_yaml_status
    ):
        """Validation result includes workflow phases for error context"""
        enforcer = WorkflowEnforcer(temp_project_dir)
        result = enforcer.validate_commit_ready("21.1")

        # Should contain suggestions for completing workflow
        assert "/sm" in result.error_message or "SM" in result.error_message
        assert "/qa" in result.error_message or "QA" in result.error_message


# ============================================================================
# Helper Function Tests
# ============================================================================


class TestHelperFunctions:
    """Tests for convenience helper functions"""

    def test_validate_story_for_commit_legacy(self, temp_project_dir):
        """Test helper function with legacy story"""
        result = validate_story_for_commit("15.1", temp_project_dir)
        assert result.passed is True

    def test_validate_story_for_commit_draft(
        self, temp_project_dir, sample_story_draft, sample_yaml_status
    ):
        """Test helper function with draft story"""
        result = validate_story_for_commit("21.1", temp_project_dir)
        assert result.passed is False


# ============================================================================
# Workflow Phase Tests
# ============================================================================


class TestWorkflowPhases:
    """Tests for workflow phase detection"""

    def test_get_workflow_phases_draft(self, temp_project_dir, sample_story_draft):
        """Test workflow phases for draft story"""
        enforcer = WorkflowEnforcer(temp_project_dir)
        phases = enforcer.get_workflow_phases("21.1")

        assert len(phases) == 5
        assert phases[0].name == "SM Draft"
        assert phases[0].completed is True  # Story file exists

        assert phases[1].name == "PO Approve"
        assert phases[1].completed is False

    def test_get_workflow_phases_review(self, temp_project_dir, sample_story_review):
        """Test workflow phases for review story"""
        enforcer = WorkflowEnforcer(temp_project_dir)
        phases = enforcer.get_workflow_phases("21.2")

        # Review status means SM, PO, DEV, QA are complete
        assert phases[0].completed is True  # SM Draft
        assert phases[1].completed is True  # PO Approve
        assert phases[2].completed is True  # DEV
        assert phases[3].completed is True  # QA Review
        assert phases[4].completed is False  # Merge (not Done yet)


# ============================================================================
# Edge Cases
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases and error handling"""

    def test_missing_yaml_file(self, temp_project_dir, sample_story_draft):
        """Test behavior when YAML file doesn't exist"""
        # Don't create YAML file
        enforcer = WorkflowEnforcer(temp_project_dir)
        status_str, meta = enforcer.get_yaml_status("21.1")

        assert "error" in meta

    def test_malformed_story_file(self, temp_project_dir):
        """Test parsing malformed story file"""
        # Create a malformed story file
        story_file = temp_project_dir / "docs" / "stories" / "21.3.story.md"
        story_file.write_text("Not a valid story file", encoding="utf-8")

        enforcer = WorkflowEnforcer(temp_project_dir)
        status, meta = enforcer.parse_story_status("21.3")

        # Should default to Draft or Unknown
        assert status in {StoryStatus.DRAFT, StoryStatus.UNKNOWN}

    def test_empty_project_directory(self, temp_project_dir):
        """Test with minimal project structure"""
        # Remove all files
        import shutil

        for item in temp_project_dir.iterdir():
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()

        enforcer = WorkflowEnforcer(temp_project_dir)
        result = enforcer.validate_commit_ready("21.1")

        # Non-legacy story without files should fail
        # But if story file doesn't exist, status is Unknown
        assert result.story_id == "21.1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
