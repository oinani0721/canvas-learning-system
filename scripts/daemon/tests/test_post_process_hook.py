"""
Unit tests for PostProcessHook.

Tests the post-processing orchestrator for Dev-QA auto-record pipeline.
"""

import pytest
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from post_process_hook import PostProcessHook, PostProcessResult


class TestPostProcessHook:
    """Test cases for PostProcessHook."""

    @pytest.fixture
    def sample_result_data(self):
        """Sample .worktree-result.json data."""
        return {
            "story_id": "15.1",
            "story_title": "FastAPI Application Initialization",
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
    def setup_test_environment(self, sample_result_data, story_content_with_placeholders):
        """Set up a complete test environment with worktree and main repo."""
        with TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create worktree structure
            worktree_path = tmpdir / "Canvas-develop-15.1"
            worktree_stories = worktree_path / "docs" / "stories"
            worktree_stories.mkdir(parents=True)

            # Create main repo structure
            main_repo_path = tmpdir / "Canvas"
            main_stories = main_repo_path / "docs" / "stories"
            main_stories.mkdir(parents=True)
            main_qa_gates = main_repo_path / "docs" / "qa" / "gates"
            main_qa_gates.mkdir(parents=True)

            # Create story file
            story_file = worktree_stories / "15.1.story.md"
            story_file.write_text(story_content_with_placeholders, encoding="utf-8")

            # Create .worktree-result.json
            result_file = worktree_path / ".worktree-result.json"
            with open(result_file, "w", encoding="utf-8") as f:
                json.dump(sample_result_data, f, indent=2)

            yield {
                "tmpdir": tmpdir,
                "worktree_path": worktree_path,
                "main_repo_path": main_repo_path,
                "story_file": story_file,
                "result_file": result_file,
            }

    def test_process_success(self, setup_test_environment):
        """Test full process workflow with success outcome."""
        env = setup_test_environment
        hook = PostProcessHook(env["main_repo_path"])

        result = hook.process(
            story_id="15.1",
            worktree_path=env["worktree_path"],
            session_id="test-session"
        )

        assert result.story_id == "15.1"
        assert result.session_id == "test-session"
        assert result.gate_generated is True
        assert result.errors is None or len(result.errors) == 0

    def test_process_missing_result_file(self):
        """Test process handles missing result file."""
        with TemporaryDirectory() as tmpdir:
            main_repo = Path(tmpdir) / "Canvas"
            main_repo.mkdir()
            worktree = Path(tmpdir) / "worktree"
            worktree.mkdir()

            hook = PostProcessHook(main_repo)
            result = hook.process(
                story_id="15.1",
                worktree_path=worktree,
                session_id="test"
            )

            assert result.story_updated is False
            assert result.gate_generated is False
            assert result.errors is not None
            assert len(result.errors) > 0
            assert "result" in result.errors[0].lower()

    def test_read_result_file(self, setup_test_environment):
        """Test _read_result_file reads JSON correctly."""
        env = setup_test_environment
        hook = PostProcessHook(env["main_repo_path"])

        data = hook._read_result_file(env["worktree_path"])

        assert data is not None
        assert data["story_id"] == "15.1"
        assert data["outcome"] == "SUCCESS"
        assert data["qa_gate"] == "PASS"

    def test_read_result_file_not_found(self):
        """Test _read_result_file handles missing file."""
        with TemporaryDirectory() as tmpdir:
            hook = PostProcessHook(Path(tmpdir))
            data = hook._read_result_file(Path(tmpdir))

            assert data is None

    def test_read_result_file_invalid_json(self):
        """Test _read_result_file handles invalid JSON."""
        with TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            result_file = tmpdir / ".worktree-result.json"
            result_file.write_text("{ invalid json }", encoding="utf-8")

            hook = PostProcessHook(tmpdir)
            data = hook._read_result_file(tmpdir)

            assert data is None

    def test_generate_qa_gate(self, setup_test_environment, sample_result_data):
        """Test QA Gate generation through hook."""
        env = setup_test_environment
        hook = PostProcessHook(env["main_repo_path"])

        result = hook._generate_qa_gate(
            story_id="15.1",
            story_title="FastAPI Application Initialization",
            result_data=sample_result_data
        )

        assert result.success is True
        assert result.gate_status == "PASS"
        assert result.gate_file.exists()
        assert "15.1" in result.gate_file.name

    def test_update_result_file(self, setup_test_environment, sample_result_data):
        """Test _update_result_file adds post_process info."""
        env = setup_test_environment
        hook = PostProcessHook(env["main_repo_path"])

        # Create mock UpdateResult and GateResult
        from story_file_updater import UpdateResult
        from qa_gate_generator import GateResult

        update_result = UpdateResult(
            story_file=env["story_file"],
            story_id="15.1",
            dev_record_updated=True,
            qa_results_updated=True,
            file_synced=True
        )

        gate_result = GateResult(
            gate_file=env["main_repo_path"] / "docs" / "qa" / "gates" / "15.1-test.yml",
            story_id="15.1",
            gate_status="PASS",
            quality_score=88,
            success=True
        )

        hook._update_result_file(
            env["worktree_path"],
            sample_result_data,
            update_result,
            gate_result
        )

        # Read updated file
        with open(env["result_file"], "r", encoding="utf-8") as f:
            updated_data = json.load(f)

        assert "post_process" in updated_data
        assert updated_data["post_process"]["completed"] is True
        assert updated_data["post_process"]["story_file_updated"] is True
        assert updated_data["post_process"]["dev_record_complete"] is True
        assert updated_data["post_process"]["qa_record_complete"] is True

    def test_process_updates_story_file(self, setup_test_environment):
        """Test process updates Story file with Dev and QA sections."""
        env = setup_test_environment
        hook = PostProcessHook(env["main_repo_path"])

        result = hook.process(
            story_id="15.1",
            worktree_path=env["worktree_path"],
            session_id="test"
        )

        # Read updated story file
        updated_content = env["story_file"].read_text(encoding="utf-8")

        # Check placeholders are replaced
        assert "*待填写*" not in updated_content
        assert "*待QA Agent审查*" not in updated_content

        # Check new content is present
        assert "Claude Code" in updated_content
        assert "PASS" in updated_content


class TestPostProcessResult:
    """Test cases for PostProcessResult dataclass."""

    def test_is_success_all_true(self):
        result = PostProcessResult(
            story_id="15.1",
            session_id="test",
            story_updated=True,
            gate_generated=True,
            dev_record_complete=True,
            qa_record_complete=True,
            errors=None
        )
        assert result.is_success() is True

    def test_is_success_story_not_updated(self):
        result = PostProcessResult(
            story_id="15.1",
            session_id="test",
            story_updated=False,
            gate_generated=True,
            errors=None
        )
        assert result.is_success() is False

    def test_is_success_gate_not_generated(self):
        result = PostProcessResult(
            story_id="15.1",
            session_id="test",
            story_updated=True,
            gate_generated=False,
            errors=None
        )
        assert result.is_success() is False

    def test_is_success_with_errors(self):
        result = PostProcessResult(
            story_id="15.1",
            session_id="test",
            story_updated=True,
            gate_generated=True,
            errors=["Some error occurred"]
        )
        assert result.is_success() is False

    def test_default_timestamp(self):
        result = PostProcessResult(
            story_id="15.1",
            session_id="test",
            story_updated=True,
            gate_generated=True
        )
        assert result.timestamp is not None
        assert len(result.timestamp) > 10  # ISO format should be longer

    def test_default_errors_list(self):
        result = PostProcessResult(
            story_id="15.1",
            session_id="test",
            story_updated=True,
            gate_generated=True
        )
        assert result.errors == []

    def test_to_dict(self):
        result = PostProcessResult(
            story_id="15.1",
            session_id="test",
            story_updated=True,
            gate_generated=True,
            story_file="/path/to/story.md",
            gate_file="/path/to/gate.yml",
            dev_record_complete=True,
            qa_record_complete=True,
            errors=None
        )
        d = result.to_dict()

        assert d["story_id"] == "15.1"
        assert d["session_id"] == "test"
        assert d["story_updated"] is True
        assert d["gate_generated"] is True
        assert d["story_file"] == "/path/to/story.md"
        assert d["gate_file"] == "/path/to/gate.yml"


class TestPostProcessHookIntegration:
    """Integration tests for the complete post-process pipeline."""

    @pytest.fixture
    def full_environment(self):
        """Create a complete test environment simulating real workflow."""
        with TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create main repo
            main_repo = tmpdir / "Canvas"
            (main_repo / "docs" / "stories").mkdir(parents=True)
            (main_repo / "docs" / "qa" / "gates").mkdir(parents=True)

            # Create worktree
            worktree = tmpdir / "Canvas-develop-15.1"
            worktree_stories = worktree / "docs" / "stories"
            worktree_stories.mkdir(parents=True)

            # Create story file with placeholders
            story_content = """# Story 15.1: FastAPI Application Initialization

## Status
- **State**: In Progress

## Description
Initialize the FastAPI application with proper configuration.

## Acceptance Criteria
- AC1: Application starts successfully
- AC2: CORS is configured correctly
- AC3: Health check endpoint works

## Dev Agent Record

*待填写*

## QA Results

*待QA Agent审查*

## Change Log
- 2025-11-29: Initial creation
"""
            (worktree_stories / "15.1.story.md").write_text(story_content, encoding="utf-8")

            # Create result file
            result_data = {
                "story_id": "15.1",
                "story_title": "FastAPI Application Initialization",
                "outcome": "SUCCESS",
                "tests_passed": True,
                "test_count": 52,
                "test_coverage": 96.5,
                "qa_gate": "PASS",
                "commit_sha": "def4567890abc",
                "timestamp": "2025-11-29T20:30:00Z",
                "duration_seconds": 1800,
                "dev_record": {
                    "agent_model": "Claude Code (claude-sonnet-4-5)",
                    "duration_seconds": 1800,
                    "files_created": [
                        {"path": "src/api/main.py", "description": "FastAPI application entry point"},
                        {"path": "src/api/routers/health.py", "description": "Health check router"}
                    ],
                    "files_modified": [
                        {"path": "requirements.txt", "description": "Added FastAPI dependencies"}
                    ],
                    "completion_notes": "Implemented FastAPI application with CORS and health check"
                },
                "qa_record": {
                    "quality_score": 92,
                    "ac_coverage": {
                        "AC1": {"status": "PASS", "evidence": "test_app_startup"},
                        "AC2": {"status": "PASS", "evidence": "test_cors_headers"},
                        "AC3": {"status": "PASS", "evidence": "test_health_endpoint"}
                    },
                    "issues_found": [],
                    "recommendations": ["Consider adding request logging middleware"]
                }
            }
            result_file = worktree / ".worktree-result.json"
            with open(result_file, "w", encoding="utf-8") as f:
                json.dump(result_data, f, indent=2)

            yield {
                "main_repo": main_repo,
                "worktree": worktree,
                "story_file": worktree_stories / "15.1.story.md",
                "result_file": result_file
            }

    def test_complete_pipeline(self, full_environment):
        """Test the complete post-processing pipeline."""
        env = full_environment
        hook = PostProcessHook(env["main_repo"])

        result = hook.process(
            story_id="15.1",
            worktree_path=env["worktree"],
            session_id="integration-test"
        )

        # Check result
        assert result.is_success() is True
        assert result.story_id == "15.1"
        assert result.dev_record_complete is True
        assert result.qa_record_complete is True

        # Check story file was updated
        story_content = env["story_file"].read_text(encoding="utf-8")
        assert "*待填写*" not in story_content
        assert "Claude Code" in story_content
        assert "52 tests" in story_content
        assert "96.5%" in story_content
        assert "PASS" in story_content

        # Check QA gate was generated
        gate_dir = env["main_repo"] / "docs" / "qa" / "gates"
        gate_files = list(gate_dir.glob("15.1-*.yml"))
        assert len(gate_files) == 1

        # Check result file was updated
        with open(env["result_file"], "r", encoding="utf-8") as f:
            updated_result = json.load(f)
        assert "post_process" in updated_result
        assert updated_result["post_process"]["completed"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
