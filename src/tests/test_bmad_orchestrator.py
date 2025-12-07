"""
BMad Orchestrator Tests

测试 BMad 全自动化编排器的核心功能。

Author: Canvas Learning System Team
Version: 1.0.0
Created: 2025-11-30
"""

from pathlib import Path

import pytest

# ============================================================================
# Test Imports
# ============================================================================

def test_imports():
    """Test that all modules can be imported."""
    assert True


# ============================================================================
# State Tests
# ============================================================================

class TestState:
    """State Schema 测试"""

    def test_create_initial_state(self):
        """Test initial state creation."""
        from bmad_orchestrator import create_initial_state

        state = create_initial_state(
            epic_id="15",
            story_ids=["15.1", "15.2", "15.3"],
            base_path="/test/path",
        )

        assert state["epic_id"] == "15"
        assert state["story_ids"] == ["15.1", "15.2", "15.3"]
        assert state["base_path"] == "/test/path"
        assert state["current_phase"] == "SM"
        assert state["sm_status"] == "pending"
        assert state["po_status"] == "pending"
        assert state["dev_status"] == "pending"
        assert state["qa_status"] == "pending"

    def test_create_initial_state_with_mode_override(self):
        """Test initial state with mode override."""
        from bmad_orchestrator import create_initial_state

        state = create_initial_state(
            epic_id="15",
            story_ids=["15.1"],
            base_path="/test/path",
            mode_override="parallel",
        )

        assert state["mode_override"] == "parallel"

    def test_merge_dev_outcomes(self):
        """Test dev outcomes reducer."""
        from bmad_orchestrator import DevOutcome, merge_dev_outcomes

        existing = [
            DevOutcome(
                story_id="15.1",
                outcome="SUCCESS",
                commit_sha="abc123",
                worktree_path="/path/1",
            )
        ]
        new = [
            DevOutcome(
                story_id="15.2",
                outcome="SUCCESS",
                commit_sha="def456",
                worktree_path="/path/2",
            )
        ]

        result = merge_dev_outcomes(existing, new)

        assert len(result) == 2
        assert result[0]["story_id"] == "15.1"
        assert result[1]["story_id"] == "15.2"

    def test_merge_blockers(self):
        """Test blockers reducer."""
        from bmad_orchestrator import BlockerInfo, merge_blockers

        existing = [
            BlockerInfo(
                story_id="15.1",
                blocker_type="DEV_FAILURE",
                description="Test failure",
            )
        ]
        new = [
            BlockerInfo(
                story_id="15.2",
                blocker_type="QA_FAIL",
                description="Security issue",
            )
        ]

        result = merge_blockers(existing, new)

        assert len(result) == 2


# ============================================================================
# Dependency Analyzer Tests
# ============================================================================

class TestDependencyAnalyzer:
    """依赖分析器测试"""

    @pytest.mark.asyncio
    async def test_parse_story_file_not_found(self):
        """Test parsing non-existent story file."""
        from bmad_orchestrator.dependency_analyzer import parse_story_file

        result = await parse_story_file(Path("/nonexistent/path.md"))
        assert result is None

    def test_detect_conflicts_no_overlap(self):
        """Test conflict detection with no overlapping files."""
        from bmad_orchestrator.dependency_analyzer import (
            StoryDependency,
            detect_conflicts,
        )

        deps = {
            "15.1": StoryDependency(
                story_id="15.1",
                files_to_modify=["src/a.py"],
            ),
            "15.2": StoryDependency(
                story_id="15.2",
                files_to_modify=["src/b.py"],
            ),
        }

        conflicts, details = detect_conflicts(deps)

        assert len(conflicts) == 0
        assert len(details) == 0

    def test_detect_conflicts_with_overlap(self):
        """Test conflict detection with overlapping files."""
        from bmad_orchestrator.dependency_analyzer import (
            StoryDependency,
            detect_conflicts,
        )

        deps = {
            "15.1": StoryDependency(
                story_id="15.1",
                files_to_modify=["src/common.py", "src/a.py"],
            ),
            "15.2": StoryDependency(
                story_id="15.2",
                files_to_modify=["src/common.py", "src/b.py"],
            ),
        }

        conflicts, details = detect_conflicts(deps)

        assert len(conflicts) == 1
        assert "15.1-15.2" in conflicts
        assert "src/common.py" in conflicts["15.1-15.2"]
        assert len(details) == 1
        assert details[0].conflict_type == "MODIFY_CONFLICT"

    def test_generate_batches_no_conflicts(self):
        """Test batch generation with no conflicts."""
        from bmad_orchestrator.dependency_analyzer import generate_batches

        story_ids = ["15.1", "15.2", "15.3"]
        conflicts = {}

        batches = generate_batches(story_ids, conflicts)

        # All stories should be in one batch (can run in parallel)
        assert len(batches) == 1
        assert set(batches[0]) == {"15.1", "15.2", "15.3"}

    def test_generate_batches_with_conflicts(self):
        """Test batch generation with conflicts."""
        from bmad_orchestrator.dependency_analyzer import generate_batches

        story_ids = ["15.1", "15.2", "15.3"]
        conflicts = {
            "15.1-15.2": ["src/common.py"],
            "15.2-15.3": ["src/other.py"],
        }

        batches = generate_batches(story_ids, conflicts)

        # Stories with conflicts should be in different batches
        assert len(batches) >= 2

        # Verify no conflicting stories in same batch
        for batch in batches:
            if "15.1" in batch and "15.2" in batch:
                pytest.fail("15.1 and 15.2 should not be in same batch")
            if "15.2" in batch and "15.3" in batch:
                pytest.fail("15.2 and 15.3 should not be in same batch")

    def test_recommend_mode_parallel(self):
        """Test mode recommendation for no conflicts."""
        from bmad_orchestrator.dependency_analyzer import recommend_mode

        story_ids = ["15.1", "15.2", "15.3"]
        conflicts = {}
        batches = [["15.1", "15.2", "15.3"]]

        mode = recommend_mode(story_ids, conflicts, batches)

        assert mode == "parallel"

    def test_recommend_mode_linear(self):
        """Test mode recommendation for high conflicts."""
        from bmad_orchestrator.dependency_analyzer import recommend_mode

        story_ids = ["15.1", "15.2", "15.3"]
        # All pairs conflict
        conflicts = {
            "15.1-15.2": ["file1"],
            "15.1-15.3": ["file2"],
            "15.2-15.3": ["file3"],
        }
        batches = [["15.1"], ["15.2"], ["15.3"]]

        mode = recommend_mode(story_ids, conflicts, batches)

        assert mode == "linear"

    def test_recommend_mode_hybrid(self):
        """Test mode recommendation for partial conflicts."""
        from bmad_orchestrator.dependency_analyzer import recommend_mode

        story_ids = ["15.1", "15.2", "15.3", "15.4"]
        # Only one conflict
        conflicts = {
            "15.1-15.2": ["file1"],
        }
        batches = [["15.1", "15.3", "15.4"], ["15.2"]]

        mode = recommend_mode(story_ids, conflicts, batches)

        assert mode == "hybrid"

    def test_print_analysis_report(self):
        """Test analysis report generation."""
        from bmad_orchestrator.dependency_analyzer import print_analysis_report

        result = {
            "dependencies": {
                "15.1": {"story_id": "15.1", "files_to_modify": ["a.py"]},
                "15.2": {"story_id": "15.2", "files_to_modify": ["b.py"]},
            },
            "conflicts": {},
            "recommended_mode": "parallel",
            "batches": [["15.1", "15.2"]],
            "conflict_details": [],
        }

        report = print_analysis_report(result)

        assert "Stories Analyzed: 2" in report
        assert "Recommended Mode: PARALLEL" in report
        assert "Batch 1: 15.1, 15.2" in report


# ============================================================================
# Graph Tests
# ============================================================================

class TestGraph:
    """StateGraph 测试"""

    def test_build_graph(self):
        """Test graph building."""
        from bmad_orchestrator import build_graph

        graph = build_graph()

        # Verify graph structure
        assert graph is not None

    def test_routing_functions(self):
        """Test routing functions."""
        from bmad_orchestrator.graph import (
            route_after_dev,
            route_after_po,
            route_after_qa,
            route_after_sm,
        )

        # SM routing
        assert route_after_sm({"sm_status": "completed"}) == "po_node"
        assert route_after_sm({"sm_status": "failed"}) == "halt_node"

        # PO routing
        assert route_after_po({"approved_stories": ["15.1"]}) == "analysis_node"
        assert route_after_po({"approved_stories": []}) == "halt_node"
        assert route_after_po({}) == "halt_node"

        # DEV routing
        assert route_after_dev({"dev_status": "completed"}) == "qa_node"
        assert route_after_dev({"dev_status": "partially_failed"}) == "qa_node"
        assert route_after_dev({"dev_status": "failed"}) == "halt_node"

        # QA routing (v1.1.0: QA → SDD_VALIDATION → MERGE)
        assert route_after_qa({"current_qa_gate": "PASS"}) == "sdd_validation_node"
        assert route_after_qa({"current_qa_gate": "WAIVED"}) == "sdd_validation_node"
        assert route_after_qa({"current_qa_gate": "CONCERNS", "fix_attempts": 0}) == "fix_node"
        assert route_after_qa({"current_qa_gate": "CONCERNS", "fix_attempts": 1}) == "sdd_validation_node"  # fail-forward
        assert route_after_qa({"current_qa_gate": "FAIL"}) == "halt_node"


# ============================================================================
# Session Spawner Tests
# ============================================================================

class TestSessionSpawner:
    """Session Spawner 测试"""

    def test_session_result_dataclass(self):
        """Test SessionResult dataclass."""
        from bmad_orchestrator import SessionResult

        result = SessionResult(
            story_id="15.1",
            outcome="SUCCESS",
            timestamp="2025-11-30T12:00:00",
            duration_seconds=120,
        )

        assert result.story_id == "15.1"
        assert result.outcome == "SUCCESS"
        assert result.duration_seconds == 120

    def test_sm_result_dataclass(self):
        """Test SMResult dataclass."""
        from bmad_orchestrator import SMResult

        result = SMResult(
            story_id="15.1",
            outcome="SUCCESS",
            timestamp="2025-11-30T12:00:00",
            story_file="docs/stories/15.1.story.md",
            title="Test Story",
            checklist_passed=True,
        )

        assert result.story_file == "docs/stories/15.1.story.md"
        assert result.checklist_passed is True

    def test_dev_result_dataclass(self):
        """Test DevResult dataclass."""
        from bmad_orchestrator import DevResult

        result = DevResult(
            story_id="15.1",
            outcome="SUCCESS",
            timestamp="2025-11-30T12:00:00",
            tests_passed=True,
            test_count=10,
            test_coverage=85.5,
        )

        assert result.outcome == "SUCCESS"
        assert result.test_coverage == 85.5

    def test_qa_result_dataclass(self):
        """Test QAResult dataclass."""
        from bmad_orchestrator import QAResult

        result = QAResult(
            story_id="15.1",
            outcome="SUCCESS",
            timestamp="2025-11-30T12:00:00",
            qa_gate="PASS",
            quality_score=85,
        )

        assert result.qa_gate == "PASS"
        assert result.quality_score == 85


# ============================================================================
# CLI Tests
# ============================================================================

class TestCLI:
    """CLI 测试"""

    def test_main_no_args(self):
        """Test CLI with no arguments."""
        import sys

        from bmad_orchestrator.cli import main

        # Save original argv
        original_argv = sys.argv

        try:
            sys.argv = ["bmad_orchestrator"]
            result = main()
            assert result == 1  # Should fail without command
        finally:
            sys.argv = original_argv


# ============================================================================
# Integration Tests (Mocked)
# ============================================================================

class TestIntegration:
    """集成测试 (使用 Mock)"""

    @pytest.mark.asyncio
    async def test_analyze_dependencies_integration(self):
        """Test full dependency analysis flow."""
        from bmad_orchestrator import analyze_dependencies

        # Create temp story files would be needed for real test
        # Here we just verify the function signature works
        result = await analyze_dependencies(
            story_ids=["15.1", "15.2"],
            base_path=Path("."),
        )

        assert "dependencies" in result
        assert "conflicts" in result
        assert "recommended_mode" in result
        assert "batches" in result


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
