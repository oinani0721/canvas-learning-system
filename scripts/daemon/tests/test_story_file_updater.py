"""
Unit tests for StoryFileUpdater.

Tests the hybrid mode Story file update functionality.
"""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from story_file_updater import StoryFileUpdater, UpdateResult


class TestStoryFileUpdater:
    """Test cases for StoryFileUpdater."""

    @pytest.fixture
    def updater(self):
        return StoryFileUpdater()

    @pytest.fixture
    def sample_result(self):
        """Sample .worktree-result.json data."""
        return {
            "story_id": "15.1",
            "outcome": "SUCCESS",
            "tests_passed": True,
            "test_count": 48,
            "test_coverage": 94.0,
            "qa_gate": "PASS",
            "commit_sha": "abc1234567890",
            "timestamp": "2025-11-29T18:00:00Z",
            "duration_seconds": 1200,
            "dev_record": {
                "agent_model": "Claude Code (claude-sonnet-4-5)",
                "duration_seconds": 1200,
                "files_created": [
                    {"path": "src/api/main.py", "description": "FastAPI application"}
                ],
                "files_modified": [
                    {"path": "src/__init__.py", "description": "Updated exports"}
                ],
                "completion_notes": "Implemented FastAPI initialization with CORS"
            },
            "qa_record": {
                "quality_score": 88,
                "ac_coverage": {
                    "AC1": {"status": "PASS", "evidence": "test_app_creation"},
                    "AC2": {"status": "PASS", "evidence": "test_cors_middleware"}
                },
                "issues_found": [
                    {"severity": "low", "description": "Consider adding rate limiting"}
                ],
                "recommendations": ["Add OpenTelemetry integration"]
            }
        }

    @pytest.fixture
    def story_content_with_placeholders(self):
        """Story file content with placeholder sections."""
        return """# Story 15.1: FastAPI Application Initialization

## Status
- **State**: Draft

## Description
Initialize the FastAPI application with proper configuration.

## Acceptance Criteria
- AC1: Application starts successfully
- AC2: CORS is configured correctly

## Dev Agent Record

*待填写*

## QA Results

*待QA Agent审查*

## Change Log
- Initial creation
"""

    @pytest.fixture
    def story_content_already_updated(self):
        """Story file content that's already been updated."""
        return """# Story 15.1: FastAPI Application Initialization

## Status
- **State**: Complete

## Description
Initialize the FastAPI application with proper configuration.

## Dev Agent Record

### Agent Model Used
Claude Code (claude-sonnet-4-5)

### Debug Log References
- Session ID: auto-generated
- Process: Automated via `*linear`

### Completion Notes List
- Implemented FastAPI initialization
- Tests: PASS (48 tests, 94.0% coverage)
- QA Gate: PASS

## QA Results

**验证方式**: `*linear` 自动化验证流程
**验证时间**: 2025-11-29
**验证状态**: ✅ PASSED

## Change Log
- Completed development
"""

    def test_section_needs_update_with_placeholder(self, updater, story_content_with_placeholders):
        """Test detection of placeholder content."""
        assert updater._section_needs_update(
            story_content_with_placeholders,
            "## Dev Agent Record"
        ) is True
        assert updater._section_needs_update(
            story_content_with_placeholders,
            "## QA Results"
        ) is True

    def test_section_needs_update_already_filled(self, updater, story_content_already_updated):
        """Test detection of already-updated content."""
        assert updater._section_needs_update(
            story_content_already_updated,
            "## Dev Agent Record"
        ) is False
        assert updater._section_needs_update(
            story_content_already_updated,
            "## QA Results"
        ) is False

    def test_generate_dev_record(self, updater, sample_result):
        """Test Dev Agent Record generation."""
        content = updater._generate_dev_record(sample_result)

        assert "Claude Code" in content
        assert "abc1234567890" in content or "abc1234" in content
        assert "48 tests" in content
        assert "94.0%" in content or "94" in content
        assert "PASS" in content
        assert "src/api/main.py" in content

    def test_generate_qa_results(self, updater, sample_result):
        """Test QA Results generation."""
        content = updater._generate_qa_results(sample_result)

        assert "PASS" in content
        assert "88/100" in content or "88" in content
        assert "AC1" in content
        assert "AC2" in content
        assert "rate limiting" in content

    def test_update_section(self, updater, story_content_with_placeholders):
        """Test section content replacement."""
        new_dev_record = "### Agent Model Used\nTest Model"
        updated = updater._update_section(
            story_content_with_placeholders,
            "## Dev Agent Record",
            new_dev_record
        )

        assert "Test Model" in updated
        assert "*待填写*" not in updated

    def test_find_story_file_multiple_patterns(self, updater):
        """Test finding story files with different naming patterns."""
        with TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)

            # Create test file
            story_file = base_path / "15.1.story.md"
            story_file.write_text("# Test Story", encoding="utf-8")

            found = updater._find_story_file("15.1", base_path)
            assert found is not None
            assert found.name == "15.1.story.md"

    def test_find_story_file_alternative_pattern(self, updater):
        """Test finding story files with alternative naming pattern."""
        with TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)

            # Create test file with alternative pattern
            story_file = base_path / "story-15.1.md"
            story_file.write_text("# Test Story", encoding="utf-8")

            found = updater._find_story_file("15.1", base_path)
            assert found is not None
            assert found.name == "story-15.1.md"

    def test_update_story_file_integration(self, updater, sample_result, story_content_with_placeholders):
        """Integration test for full update workflow."""
        with TemporaryDirectory() as tmpdir:
            worktree_path = Path(tmpdir) / "worktree"
            main_repo_path = Path(tmpdir) / "main"

            # Create directories
            worktree_stories = worktree_path / "docs" / "stories"
            worktree_stories.mkdir(parents=True)
            main_stories = main_repo_path / "docs" / "stories"
            main_stories.mkdir(parents=True)

            # Create story file
            story_file = worktree_stories / "15.1.story.md"
            story_file.write_text(story_content_with_placeholders, encoding="utf-8")

            # Run update
            result = updater.update_story_file(
                story_id="15.1",
                result=sample_result,
                worktree_path=worktree_path,
                main_repo_path=main_repo_path
            )

            assert result.dev_record_updated is True
            assert result.qa_results_updated is True
            assert result.is_complete() is True

            # Verify content was updated
            updated_content = story_file.read_text(encoding="utf-8")
            assert "*待填写*" not in updated_content
            assert "Claude Code" in updated_content


class TestUpdateResult:
    """Test cases for UpdateResult dataclass."""

    def test_is_complete_all_true(self):
        result = UpdateResult(
            story_file=Path("test.md"),
            story_id="15.1",
            dev_record_updated=True,
            qa_results_updated=True,
            file_synced=True
        )
        assert result.is_complete() is True

    def test_is_complete_missing_dev(self):
        result = UpdateResult(
            story_file=Path("test.md"),
            story_id="15.1",
            dev_record_updated=False,
            qa_results_updated=True,
            file_synced=True
        )
        assert result.is_complete() is False

    def test_to_dict(self):
        result = UpdateResult(
            story_file=Path("test.md"),
            story_id="15.1",
            dev_record_updated=True,
            qa_results_updated=True,
            file_synced=True,
            error=None
        )
        d = result.to_dict()
        assert d["story_id"] == "15.1"
        assert d["dev_record_updated"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
