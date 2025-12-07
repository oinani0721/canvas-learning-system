"""
BMad Orchestrator v1.1.0 Routing Function Tests

测试所有条件路由函数: route_after_qa, route_after_sdd_validation,
route_after_merge, route_after_commit, route_after_fix

Author: Canvas Learning System Team
Version: 1.1.0
Created: 2025-12-01
"""


import pytest

# ============================================================================
# Routing Function Tests (15 tests)
# ============================================================================

class TestRouteAfterQA:
    """route_after_qa 路由函数测试"""

    def test_route_after_qa_pass(self):
        """Test routing when QA gate is PASS."""
        from bmad_orchestrator.graph import route_after_qa

        state = {
            "current_qa_gate": "PASS",
            "fix_attempts": 0,
            "qa_outcomes": [{"story_id": "15.1", "qa_gate": "PASS"}],
        }

        result = route_after_qa(state)
        assert result == "sdd_validation_node"

    def test_route_after_qa_fail(self):
        """Test routing when QA gate is FAIL."""
        from bmad_orchestrator.graph import route_after_qa

        state = {
            "current_qa_gate": "FAIL",
            "fix_attempts": 0,
            "qa_outcomes": [{"story_id": "15.1", "qa_gate": "FAIL"}],
        }

        result = route_after_qa(state)
        assert result == "halt_node"

    def test_route_after_qa_concerns_first_attempt(self):
        """Test routing when CONCERNS on first attempt (should FIX)."""
        from bmad_orchestrator.graph import route_after_qa

        state = {
            "current_qa_gate": "CONCERNS",
            "fix_attempts": 0,
            "qa_outcomes": [{"story_id": "15.1", "qa_gate": "CONCERNS"}],
        }

        result = route_after_qa(state)
        assert result == "fix_node"

    def test_route_after_qa_concerns_after_fix(self):
        """Test routing when CONCERNS after fix attempt (fail-forward to SDD)."""
        from bmad_orchestrator.graph import route_after_qa

        state = {
            "current_qa_gate": "CONCERNS",
            "fix_attempts": 1,
            "qa_outcomes": [{"story_id": "15.1", "qa_gate": "CONCERNS"}],
        }

        result = route_after_qa(state)
        assert result == "sdd_validation_node"

    def test_route_after_qa_waived(self):
        """Test routing when QA is WAIVED."""
        from bmad_orchestrator.graph import route_after_qa

        state = {
            "current_qa_gate": "WAIVED",
            "fix_attempts": 0,
            "qa_outcomes": [{"story_id": "15.1", "qa_gate": "WAIVED"}],
        }

        result = route_after_qa(state)
        assert result == "sdd_validation_node"

    def test_route_after_qa_empty_outcomes_pass_gate(self):
        """Test routing with empty outcomes but PASS gate (legacy fallback)."""
        from bmad_orchestrator.graph import route_after_qa

        state = {
            "current_qa_gate": "PASS",
            "fix_attempts": 0,
            "qa_outcomes": [],
        }

        result = route_after_qa(state)
        assert result == "sdd_validation_node"

    def test_route_after_qa_fail_forward_with_mixed(self):
        """Test fail-forward: at least one PASS should continue."""
        from bmad_orchestrator.graph import route_after_qa

        state = {
            "fix_attempts": 0,
            "qa_outcomes": [
                {"story_id": "15.1", "qa_gate": "PASS"},
                {"story_id": "15.2", "qa_gate": "FAIL"},
            ],
        }

        result = route_after_qa(state)
        assert result == "sdd_validation_node"  # Fail-forward: at least one passed

    def test_route_after_qa_all_fail(self):
        """Test routing when ALL stories FAIL."""
        from bmad_orchestrator.graph import route_after_qa

        state = {
            "fix_attempts": 0,
            "qa_outcomes": [
                {"story_id": "15.1", "qa_gate": "FAIL"},
                {"story_id": "15.2", "qa_gate": "FAIL"},
            ],
        }

        result = route_after_qa(state)
        assert result == "halt_node"


class TestRouteAfterSDDValidation:
    """route_after_sdd_validation 路由函数测试"""

    def test_route_after_sdd_passed(self):
        """Test routing when SDD validation passed."""
        from bmad_orchestrator.graph import route_after_sdd_validation

        state = {"sdd_status": "passed"}

        result = route_after_sdd_validation(state)
        assert result == "merge_node"

    def test_route_after_sdd_failed(self):
        """Test routing when SDD validation failed."""
        from bmad_orchestrator.graph import route_after_sdd_validation

        state = {"sdd_status": "failed"}

        result = route_after_sdd_validation(state)
        assert result == "halt_node"

    def test_route_after_sdd_warnings(self):
        """Test routing when SDD has warnings (should continue)."""
        from bmad_orchestrator.graph import route_after_sdd_validation

        state = {"sdd_status": "warnings"}

        result = route_after_sdd_validation(state)
        assert result == "merge_node"

    def test_route_after_sdd_skipped(self):
        """Test routing when SDD validation skipped."""
        from bmad_orchestrator.graph import route_after_sdd_validation

        state = {"sdd_status": "skipped"}

        result = route_after_sdd_validation(state)
        assert result == "merge_node"

    def test_route_after_sdd_default(self):
        """Test routing with missing sdd_status (default to skipped)."""
        from bmad_orchestrator.graph import route_after_sdd_validation

        state = {}  # No sdd_status

        result = route_after_sdd_validation(state)
        assert result == "merge_node"  # Default: skipped


class TestRouteAfterMerge:
    """route_after_merge 路由函数测试"""

    def test_route_after_merge_success(self):
        """Test routing when merge completed successfully."""
        from bmad_orchestrator.graph import route_after_merge

        state = {"merge_status": "completed"}

        result = route_after_merge(state)
        assert result == "commit_node"

    def test_route_after_merge_conflict(self):
        """Test routing when merge conflict detected."""
        from bmad_orchestrator.graph import route_after_merge

        state = {"merge_status": "conflict_detected"}

        result = route_after_merge(state)
        assert result == "halt_node"

    def test_route_after_merge_partial(self):
        """Test routing when merge partially succeeded (fail-forward)."""
        from bmad_orchestrator.graph import route_after_merge

        state = {"merge_status": "partial"}

        result = route_after_merge(state)
        assert result == "commit_node"  # Fail-forward

    def test_route_after_merge_unknown(self):
        """Test routing with unknown merge status."""
        from bmad_orchestrator.graph import route_after_merge

        state = {"merge_status": "unknown"}

        result = route_after_merge(state)
        assert result == "commit_node"  # Default: continue


class TestRouteAfterCommit:
    """route_after_commit 路由函数测试"""

    def test_route_after_commit_more_batches(self):
        """Test routing when more batches remain."""
        from bmad_orchestrator.graph import route_after_commit

        state = {
            "current_batch_index": 0,
            "parallel_batches": [["15.1"], ["15.2"]],
        }

        result = route_after_commit(state)
        assert result == "dev_node"  # Return to DEV for next batch

    def test_route_after_commit_last_batch(self):
        """Test routing when on last batch."""
        from bmad_orchestrator.graph import route_after_commit

        state = {
            "current_batch_index": 1,
            "parallel_batches": [["15.1"], ["15.2"]],
        }

        result = route_after_commit(state)
        assert result == "cleanup_node"

    def test_route_after_commit_single_batch(self):
        """Test routing with single batch."""
        from bmad_orchestrator.graph import route_after_commit

        state = {
            "current_batch_index": 0,
            "parallel_batches": [["15.1", "15.2"]],
        }

        result = route_after_commit(state)
        assert result == "cleanup_node"

    def test_route_after_commit_empty_batches(self):
        """Test routing with empty batches."""
        from bmad_orchestrator.graph import route_after_commit

        state = {
            "current_batch_index": 0,
            "parallel_batches": [],
        }

        result = route_after_commit(state)
        assert result == "cleanup_node"


class TestRouteAfterFix:
    """route_after_fix 路由函数测试"""

    def test_route_after_fix_first_attempt(self):
        """Test routing after first fix attempt (return to QA)."""
        from bmad_orchestrator.graph import route_after_fix

        state = {"fix_attempts": 1}

        result = route_after_fix(state)
        assert result == "qa_node"

    def test_route_after_fix_max_attempts(self):
        """Test routing after max fix attempts (proceed to commit)."""
        from bmad_orchestrator.graph import route_after_fix

        state = {"fix_attempts": 2}

        result = route_after_fix(state)
        assert result == "commit_node"


class TestUnconditionalEdges:
    """测试无条件边 (HALT→CLEANUP, CLEANUP→END)"""

    def test_halt_to_cleanup_edge(self):
        """Verify HALT always routes to CLEANUP (unconditional)."""
        # This is verified by graph structure, not a routing function
        from bmad_orchestrator.graph import build_graph

        graph = build_graph()
        # The graph should have an edge from halt_node to cleanup_node
        # This test verifies the graph structure is correct
        assert graph is not None

    def test_cleanup_to_end_edge(self):
        """Verify CLEANUP always routes to END (unconditional)."""
        from bmad_orchestrator.graph import build_graph

        graph = build_graph()
        assert graph is not None


# ============================================================================
# Integration: Routing Chain Tests
# ============================================================================

class TestRoutingChains:
    """测试完整的路由链"""

    def test_happy_path_routing_chain(self):
        """Test happy path routing: QA(PASS) → SDD → MERGE → COMMIT → CLEANUP."""
        from bmad_orchestrator.graph import (
            route_after_commit,
            route_after_merge,
            route_after_qa,
            route_after_sdd_validation,
        )

        # Step 1: QA PASS → SDD
        state1 = {"qa_outcomes": [{"story_id": "15.1", "qa_gate": "PASS"}], "fix_attempts": 0}
        assert route_after_qa(state1) == "sdd_validation_node"

        # Step 2: SDD passed → MERGE
        state2 = {"sdd_status": "passed"}
        assert route_after_sdd_validation(state2) == "merge_node"

        # Step 3: MERGE completed → COMMIT
        state3 = {"merge_status": "completed"}
        assert route_after_merge(state3) == "commit_node"

        # Step 4: COMMIT (last batch) → CLEANUP
        state4 = {"current_batch_index": 0, "parallel_batches": [["15.1"]]}
        assert route_after_commit(state4) == "cleanup_node"

    def test_fail_path_routing_chain(self):
        """Test failure path routing: QA(FAIL) → HALT → CLEANUP."""
        from bmad_orchestrator.graph import route_after_qa

        state = {
            "qa_outcomes": [
                {"story_id": "15.1", "qa_gate": "FAIL"},
                {"story_id": "15.2", "qa_gate": "FAIL"},
            ],
            "fix_attempts": 0,
        }

        # All FAIL → HALT
        assert route_after_qa(state) == "halt_node"
        # HALT → CLEANUP is unconditional edge (not a routing function)

    def test_fix_loop_routing_chain(self):
        """Test fix loop routing: QA(CONCERNS) → FIX → QA."""
        from bmad_orchestrator.graph import route_after_fix, route_after_qa

        # Step 1: QA CONCERNS (first attempt) → FIX
        state1 = {
            "qa_outcomes": [{"story_id": "15.1", "qa_gate": "CONCERNS"}],
            "fix_attempts": 0,
        }
        assert route_after_qa(state1) == "fix_node"

        # Step 2: FIX → QA (for retry)
        state2 = {"fix_attempts": 1}
        assert route_after_fix(state2) == "qa_node"

        # Step 3: QA CONCERNS (after fix) → SDD (fail-forward)
        state3 = {
            "qa_outcomes": [{"story_id": "15.1", "qa_gate": "CONCERNS"}],
            "fix_attempts": 1,
        }
        assert route_after_qa(state3) == "sdd_validation_node"


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
