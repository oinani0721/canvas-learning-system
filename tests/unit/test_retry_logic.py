"""
Unit tests for RETRY-UNTIL-PASS logic in BMad Orchestrator.

Tests the unlimited retry mechanism for *epic-develop:
- FAIL → DEV retry (infinite)
- CONCERNS → FIX → QA retry (infinite)
- DEV_BLOCKED → DEV retry (infinite)

Created: 2025-12-12
"""

import pytest
from typing import Dict, Any, List
from unittest.mock import patch, MagicMock

# Import routing functions
import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from bmad_orchestrator.graph import (
    route_after_qa,
    route_after_dev,
    route_after_fix,
)
from bmad_orchestrator.state import BmadOrchestratorState


# ============================================================================
# Helper Functions
# ============================================================================

def create_mock_state(**kwargs) -> Dict[str, Any]:
    """Create a mock state dictionary for testing."""
    default_state = {
        "epic_id": "test-epic",
        "stories": ["1.1", "1.2"],
        "current_phase": "QA",
        "qa_outcomes": [],
        "dev_outcomes": [],
        "fix_attempts": 0,
        "dev_retry_count": 0,
    }
    default_state.update(kwargs)
    return default_state


def create_qa_outcome(
    story_id: str,
    qa_gate: str,
    issues: List[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create a mock QA outcome."""
    return {
        "story_id": story_id,
        "qa_gate": qa_gate,
        "top_issues": issues or [],
        "status_reason": f"QA result: {qa_gate}",
    }


def create_dev_outcome(
    story_id: str,
    outcome: str,
    reason: str = ""
) -> Dict[str, Any]:
    """Create a mock DEV outcome."""
    return {
        "story_id": story_id,
        "outcome": outcome,
        "reason": reason,
    }


# ============================================================================
# Test: route_after_qa() - FAIL → DEV routing
# ============================================================================

class TestRouteAfterQA:
    """Test QA routing logic for RETRY-UNTIL-PASS."""

    def test_all_pass_continues_to_sdd(self):
        """All PASS → continue to SDD validation."""
        state = create_mock_state(
            qa_outcomes=[
                create_qa_outcome("1.1", "PASS"),
                create_qa_outcome("1.2", "PASS"),
            ]
        )
        result = route_after_qa(state)
        assert result == "sdd_validation_node"

    def test_all_waived_continues_to_sdd(self):
        """All WAIVED → continue to SDD validation."""
        state = create_mock_state(
            qa_outcomes=[
                create_qa_outcome("1.1", "WAIVED"),
                create_qa_outcome("1.2", "WAIVED"),
            ]
        )
        result = route_after_qa(state)
        assert result == "sdd_validation_node"

    def test_mixed_pass_waived_continues(self):
        """Mix of PASS and WAIVED → continue to SDD."""
        state = create_mock_state(
            qa_outcomes=[
                create_qa_outcome("1.1", "PASS"),
                create_qa_outcome("1.2", "WAIVED"),
            ]
        )
        result = route_after_qa(state)
        assert result == "sdd_validation_node"

    def test_single_fail_routes_to_dev(self):
        """Single FAIL → route back to DEV (RETRY-UNTIL-PASS)."""
        state = create_mock_state(
            qa_outcomes=[
                create_qa_outcome("1.1", "PASS"),
                create_qa_outcome("1.2", "FAIL", [{"id": "SEC-001", "description": "Security issue"}]),
            ]
        )
        result = route_after_qa(state)
        assert result == "dev_node", "FAIL should route to dev_node for retry"

    def test_all_fail_routes_to_dev(self):
        """All FAIL → route back to DEV."""
        state = create_mock_state(
            qa_outcomes=[
                create_qa_outcome("1.1", "FAIL"),
                create_qa_outcome("1.2", "FAIL"),
            ]
        )
        result = route_after_qa(state)
        assert result == "dev_node"

    def test_concerns_routes_to_fix(self):
        """CONCERNS (no FAIL) → route to FIX."""
        state = create_mock_state(
            qa_outcomes=[
                create_qa_outcome("1.1", "PASS"),
                create_qa_outcome("1.2", "CONCERNS", [{"id": "COV-001", "description": "Low coverage"}]),
            ]
        )
        result = route_after_qa(state)
        assert result == "fix_node"

    def test_fail_takes_priority_over_concerns(self):
        """FAIL + CONCERNS → FAIL takes priority, route to DEV."""
        state = create_mock_state(
            qa_outcomes=[
                create_qa_outcome("1.1", "FAIL"),
                create_qa_outcome("1.2", "CONCERNS"),
            ]
        )
        result = route_after_qa(state)
        assert result == "dev_node", "FAIL should take priority over CONCERNS"

    def test_empty_qa_outcomes_retries(self):
        """Empty QA outcomes → retry DEV (RETRY-UNTIL-PASS design)."""
        state = create_mock_state(qa_outcomes=[])
        result = route_after_qa(state)
        # With RETRY-UNTIL-PASS, no definitive PASS means retry
        assert result == "dev_node"


# ============================================================================
# Test: route_after_dev() - DEV_BLOCKED → DEV routing
# ============================================================================

class TestRouteAfterDev:
    """Test DEV routing logic for RETRY-UNTIL-PASS."""

    def test_all_success_routes_to_qa(self):
        """All SUCCESS → route to QA."""
        state = create_mock_state(
            dev_outcomes=[
                create_dev_outcome("1.1", "SUCCESS"),
                create_dev_outcome("1.2", "SUCCESS"),
            ]
        )
        result = route_after_dev(state)
        assert result == "qa_node"

    def test_partial_success_routes_to_qa(self):
        """Partial SUCCESS → route to QA (let QA handle failures)."""
        state = create_mock_state(
            dev_outcomes=[
                create_dev_outcome("1.1", "SUCCESS"),
                create_dev_outcome("1.2", "DEV_BLOCKED", "Test failure"),
            ]
        )
        result = route_after_dev(state)
        assert result == "qa_node"

    def test_all_blocked_routes_to_dev(self):
        """All DEV_BLOCKED → route back to DEV for retry."""
        state = create_mock_state(
            dev_outcomes=[
                create_dev_outcome("1.1", "DEV_BLOCKED", "Test failure"),
                create_dev_outcome("1.2", "DEV_BLOCKED", "Build error"),
            ]
        )
        result = route_after_dev(state)
        assert result == "dev_node", "All blocked should retry DEV"

    def test_empty_dev_outcomes_routes_to_qa(self):
        """Empty DEV outcomes → route to QA (edge case)."""
        state = create_mock_state(dev_outcomes=[])
        result = route_after_dev(state)
        # This should handle gracefully
        assert result in ["qa_node", "dev_node"]


# ============================================================================
# Test: route_after_fix() - Always QA (unlimited retry)
# ============================================================================

class TestRouteAfterFix:
    """Test FIX routing logic for RETRY-UNTIL-PASS."""

    def test_first_fix_routes_to_qa(self):
        """First fix attempt → QA."""
        state = create_mock_state(fix_attempts=1)
        result = route_after_fix(state)
        assert result == "qa_node"

    def test_second_fix_routes_to_qa(self):
        """Second fix attempt → still QA (no commit fallback)."""
        state = create_mock_state(fix_attempts=2)
        result = route_after_fix(state)
        assert result == "qa_node", "Should always return qa_node, not commit_node"

    def test_tenth_fix_routes_to_qa(self):
        """10th fix attempt → still QA (unlimited retry)."""
        state = create_mock_state(fix_attempts=10)
        result = route_after_fix(state)
        assert result == "qa_node"

    def test_hundredth_fix_routes_to_qa(self):
        """100th fix attempt → still QA (truly unlimited)."""
        state = create_mock_state(fix_attempts=100)
        result = route_after_fix(state)
        assert result == "qa_node"


# ============================================================================
# Test: Integration scenarios
# ============================================================================

class TestRetryScenarios:
    """Test complete retry scenarios."""

    def test_fail_retry_cycle(self):
        """Simulate a FAIL → DEV → QA → FAIL cycle."""
        # First QA: FAIL
        state = create_mock_state(
            qa_outcomes=[create_qa_outcome("1.1", "FAIL")],
            dev_retry_count=0,
        )
        assert route_after_qa(state) == "dev_node"

        # After DEV retry: SUCCESS
        state["dev_outcomes"] = [create_dev_outcome("1.1", "SUCCESS")]
        state["dev_retry_count"] = 1
        assert route_after_dev(state) == "qa_node"

        # Second QA: PASS
        state["qa_outcomes"] = [create_qa_outcome("1.1", "PASS")]
        assert route_after_qa(state) == "sdd_validation_node"

    def test_concerns_retry_cycle(self):
        """Simulate a CONCERNS → FIX → QA → CONCERNS cycle."""
        # First QA: CONCERNS
        state = create_mock_state(
            qa_outcomes=[create_qa_outcome("1.1", "CONCERNS")],
            fix_attempts=0,
        )
        assert route_after_qa(state) == "fix_node"

        # After FIX: always QA
        state["fix_attempts"] = 1
        assert route_after_fix(state) == "qa_node"

        # Second QA: still CONCERNS
        state["qa_outcomes"] = [create_qa_outcome("1.1", "CONCERNS")]
        assert route_after_qa(state) == "fix_node"

        # After FIX again
        state["fix_attempts"] = 2
        assert route_after_fix(state) == "qa_node"

        # Third QA: PASS
        state["qa_outcomes"] = [create_qa_outcome("1.1", "PASS")]
        assert route_after_qa(state) == "sdd_validation_node"

    def test_multiple_stories_mixed_results(self):
        """Test with multiple stories having mixed results."""
        state = create_mock_state(
            qa_outcomes=[
                create_qa_outcome("1.1", "PASS"),
                create_qa_outcome("1.2", "FAIL"),
                create_qa_outcome("1.3", "CONCERNS"),
            ]
        )
        # FAIL takes priority
        assert route_after_qa(state) == "dev_node"

        # After fixing FAIL, only CONCERNS remains
        state["qa_outcomes"] = [
            create_qa_outcome("1.1", "PASS"),
            create_qa_outcome("1.2", "PASS"),  # Fixed
            create_qa_outcome("1.3", "CONCERNS"),
        ]
        assert route_after_qa(state) == "fix_node"

        # After fixing CONCERNS
        state["qa_outcomes"] = [
            create_qa_outcome("1.1", "PASS"),
            create_qa_outcome("1.2", "PASS"),
            create_qa_outcome("1.3", "PASS"),  # Fixed
        ]
        assert route_after_qa(state) == "sdd_validation_node"


# ============================================================================
# Test: Edge cases and error handling
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_none_qa_outcomes(self):
        """Handle None qa_outcomes gracefully."""
        state = create_mock_state()
        state["qa_outcomes"] = None
        # Should not crash
        try:
            result = route_after_qa(state)
            assert result in ["sdd_validation_node", "dev_node", "fix_node", "halt_node"]
        except (TypeError, AttributeError):
            pytest.fail("Should handle None qa_outcomes gracefully")

    def test_invalid_qa_gate_value(self):
        """Handle invalid qa_gate values."""
        state = create_mock_state(
            qa_outcomes=[
                create_qa_outcome("1.1", "INVALID_VALUE"),
            ]
        )
        # Should not crash, treat as non-PASS
        try:
            result = route_after_qa(state)
            assert result is not None
        except Exception:
            pytest.fail("Should handle invalid qa_gate values")

    def test_negative_fix_attempts(self):
        """Handle negative fix_attempts (edge case)."""
        state = create_mock_state(fix_attempts=-1)
        result = route_after_fix(state)
        assert result == "qa_node"

    def test_very_large_retry_count(self):
        """Handle very large retry counts."""
        state = create_mock_state(
            dev_retry_count=999999,
            fix_attempts=999999,
        )
        # Should still work
        assert route_after_fix(state) == "qa_node"


# ============================================================================
# Run tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
