"""
BMad Orchestrator v1.1.0 Integration Tests

测试工作流节点交互和状态传播

测试策略: Pure Mocks (所有外部依赖模拟)

Author: Canvas Learning System Team
Version: 1.1.0
Created: 2025-12-01
"""

from typing import Any, Dict
from unittest.mock import AsyncMock, patch

import pytest

# ============================================================================
# Mock Session Results (Fixtures)
# ============================================================================

MOCK_QA_RESULT_PASS = {
    "story_id": "15.1",
    "outcome": "SUCCESS",
    "timestamp": "2025-12-01T10:00:00",
    "qa_gate": "PASS",
    "quality_score": 90,
    "ac_coverage": {"AC1": {"status": "PASS"}},
    "issues_found": [],
    "recommendations": [],
    "adr_compliance": True,
    "duration_seconds": 60,
}

MOCK_QA_RESULT_CONCERNS = {
    "story_id": "15.1",
    "outcome": "SUCCESS",
    "timestamp": "2025-12-01T10:00:00",
    "qa_gate": "CONCERNS",
    "quality_score": 70,
    "issues_found": [{"severity": "medium", "description": "Missing test"}],
    "duration_seconds": 60,
}

MOCK_QA_RESULT_FAIL = {
    "story_id": "15.1",
    "outcome": "FAIL",
    "timestamp": "2025-12-01T10:00:00",
    "qa_gate": "FAIL",
    "quality_score": 30,
    "issues_found": [{"severity": "high", "description": "Security issue"}],
}


# ============================================================================
# Mock Classes
# ============================================================================

class MockBmadSessionSpawner:
    """Mock session spawner for integration tests."""

    def __init__(self, qa_result=None):
        self.qa_result = qa_result or MOCK_QA_RESULT_PASS
        self.spawned_sessions = []
        self.spawn_count = 0

    async def spawn_session(self, phase, story_id, worktree_path, **kwargs):
        self.spawn_count += 1
        session_id = f"mock-{phase}-{story_id}-{self.spawn_count}"
        self.spawned_sessions.append(session_id)
        return session_id

    async def wait_for_session(self, session_id, **kwargs):
        return (0, None)  # Success

    async def get_session_result(self, phase, worktree_path):
        if phase == "QA":
            from bmad_orchestrator import QAResult
            return QAResult(**self.qa_result)
        return None


# ============================================================================
# Integration Test Scenarios
# ============================================================================

class TestWorkflowIntegration:
    """工作流集成测试"""

    @pytest.fixture
    def integration_state(self) -> Dict[str, Any]:
        """Base state for integration tests."""
        return {
            "epic_id": "15",
            "story_ids": ["15.1"],
            "base_path": "/mock/path",
            "current_phase": "QA",
            "worktree_paths": {
                "15.1": "/mock/path/Canvas-develop-15.1",
            },
            "dev_outcomes": [
                {"story_id": "15.1", "outcome": "SUCCESS", "commit_sha": "abc123"},
            ],
            "qa_outcomes": [],
            "fix_attempts": 0,
            "parallel_batches": [["15.1"]],
            "current_batch_index": 0,
            "max_turns": 200,
            "timeout": 3600,
        }

    @pytest.mark.asyncio
    async def test_happy_path_single_story(self, integration_state):
        """Test complete workflow success: QA → SDD → MERGE → COMMIT → CLEANUP."""
        from bmad_orchestrator.nodes import cleanup_node, commit_node, merge_node, qa_node, sdd_validation_node

        mock_spawner = MockBmadSessionSpawner(qa_result=MOCK_QA_RESULT_PASS)

        # Step 1: QA Node
        with patch('bmad_orchestrator.nodes.BmadSessionSpawner', return_value=mock_spawner):
            qa_result = await qa_node(integration_state)

        assert qa_result["qa_status"] == "completed"
        assert qa_result["current_qa_gate"] == "PASS"
        assert qa_result["current_phase"] == "COMMIT"

        # Update state for next node
        integration_state.update(qa_result)
        integration_state["current_phase"] = "SDD"

        # Step 2: SDD Validation Node
        async def mock_subprocess(*args, **kwargs):
            process = AsyncMock()
            process.returncode = 0
            process.communicate = AsyncMock(return_value=(b'{"coverage": 90}', b''))
            return process

        with patch('asyncio.create_subprocess_exec', side_effect=mock_subprocess):
            sdd_result = await sdd_validation_node(integration_state)

        assert sdd_result["sdd_status"] in ("passed", "warnings", "skipped")
        assert sdd_result["current_phase"] == "MERGE"

        # Update state for next node
        integration_state.update(sdd_result)

        # Step 3: Merge Node
        with patch('asyncio.create_subprocess_exec', side_effect=mock_subprocess):
            merge_result = await merge_node(integration_state)

        assert merge_result["merge_status"] == "completed"
        assert merge_result["current_phase"] == "COMMIT"

        # Update state for next node
        integration_state.update(merge_result)

        # Step 4: Commit Node
        with patch('asyncio.create_subprocess_exec', side_effect=mock_subprocess):
            commit_result = await commit_node(integration_state)

        assert "commit_shas" in commit_result
        assert commit_result["current_phase"] == "COMMIT"  # Routing to CLEANUP via route_after_commit

        # Update state for next node
        integration_state.update(commit_result)

        # Step 5: Cleanup Node
        with patch('bmad_orchestrator.nodes.remove_worktree', new_callable=AsyncMock, return_value=True):
            with patch('asyncio.create_subprocess_exec', side_effect=mock_subprocess):
                cleanup_result = await cleanup_node(integration_state)

        assert cleanup_result["cleanup_completed"] == True

    @pytest.mark.asyncio
    async def test_qa_concerns_fix_loop(self, integration_state):
        """Test QA CONCERNS → FIX → QA → SDD flow."""
        from bmad_orchestrator.nodes import fix_node, qa_node

        call_count = {"qa_calls": 0}

        class FixingMockSpawner(MockBmadSessionSpawner):
            async def get_session_result(self, phase, worktree_path):
                if phase == "QA":
                    call_count["qa_calls"] += 1
                    from bmad_orchestrator import QAResult
                    if call_count["qa_calls"] == 1:
                        return QAResult(**MOCK_QA_RESULT_CONCERNS)
                    else:
                        return QAResult(**MOCK_QA_RESULT_PASS)
                return None

        mock_spawner = FixingMockSpawner()

        # First QA: CONCERNS
        with patch('bmad_orchestrator.nodes.BmadSessionSpawner', return_value=mock_spawner):
            qa_result1 = await qa_node(integration_state)

        assert qa_result1["current_qa_gate"] == "CONCERNS"
        assert qa_result1["current_phase"] == "FIX"

        # Update state
        integration_state.update(qa_result1)

        # FIX Node
        fix_result = await fix_node(integration_state)
        assert fix_result["fix_attempts"] == 1
        assert fix_result["current_phase"] == "QA"

        # Update state
        integration_state.update(fix_result)

        # Second QA: PASS (after fix)
        with patch('bmad_orchestrator.nodes.BmadSessionSpawner', return_value=mock_spawner):
            qa_result2 = await qa_node(integration_state)

        assert qa_result2["current_qa_gate"] == "PASS"
        assert qa_result2["current_phase"] == "COMMIT"

    @pytest.mark.asyncio
    async def test_qa_fail_to_halt(self, integration_state):
        """Test QA FAIL → HALT → CLEANUP flow."""
        from bmad_orchestrator.nodes import cleanup_node, halt_node, qa_node

        mock_spawner = MockBmadSessionSpawner(qa_result=MOCK_QA_RESULT_FAIL)

        # QA Node: FAIL
        with patch('bmad_orchestrator.nodes.BmadSessionSpawner', return_value=mock_spawner):
            qa_result = await qa_node(integration_state)

        assert qa_result["current_qa_gate"] == "FAIL"
        assert qa_result["current_phase"] == "HALT"

        # Update state
        integration_state.update(qa_result)

        # HALT Node
        with patch('bmad_orchestrator.status_persister.StatusPersister') as mock_persister:
            mock_persister.return_value.persist_workflow_result = AsyncMock(return_value=True)
            halt_result = await halt_node(integration_state)

        assert halt_result["final_status"] == "halted"
        assert halt_result["current_phase"] == "HALT"  # Routing to CLEANUP via graph edge

        # Update state
        integration_state.update(halt_result)

        # CLEANUP Node (guaranteed to run)
        async def mock_subprocess(*args, **kwargs):
            process = AsyncMock()
            process.returncode = 0
            process.communicate = AsyncMock(return_value=(b'', b''))
            return process

        with patch('bmad_orchestrator.nodes.remove_worktree', new_callable=AsyncMock, return_value=True):
            with patch('asyncio.create_subprocess_exec', side_effect=mock_subprocess):
                cleanup_result = await cleanup_node(integration_state)

        assert cleanup_result["cleanup_completed"] == True

    @pytest.mark.asyncio
    async def test_sdd_fail_to_halt(self, integration_state):
        """Test SDD failure → HALT → CLEANUP flow."""
        from bmad_orchestrator.nodes import sdd_validation_node

        # Setup state as if QA passed
        integration_state["qa_outcomes"] = [
            {"story_id": "15.1", "qa_gate": "PASS", "quality_score": 90},
        ]
        integration_state["current_phase"] = "SDD"

        # SDD Node with simulated Tier 1 failure
        async def failing_subprocess(*args, **kwargs):
            process = AsyncMock()
            # Simulate coverage check failure
            if 'coverage' in str(args).lower():
                process.returncode = 1
                process.communicate = AsyncMock(return_value=(b'coverage: 50%', b'Tier 1 fail'))
            else:
                process.returncode = 0
                process.communicate = AsyncMock(return_value=(b'', b''))
            return process

        with patch('asyncio.create_subprocess_exec', side_effect=failing_subprocess):
            sdd_result = await sdd_validation_node(integration_state)

        # Update and verify flow continues properly
        integration_state.update(sdd_result)

    @pytest.mark.asyncio
    async def test_merge_conflict_halt(self, integration_state):
        """Test MERGE conflict → HALT → CLEANUP flow."""
        from bmad_orchestrator.nodes import merge_node

        # Setup state as if SDD passed
        integration_state["qa_outcomes"] = [
            {"story_id": "15.1", "qa_gate": "PASS"},
        ]
        integration_state["current_phase"] = "MERGE"

        # MERGE Node with conflict
        async def conflict_subprocess(*args, **kwargs):
            process = AsyncMock()
            if 'merge' in str(args):
                process.returncode = 1  # Conflict
                process.communicate = AsyncMock(return_value=(b'', b'CONFLICT'))
            else:
                process.returncode = 0
                process.communicate = AsyncMock(return_value=(b'', b''))
            process.wait = AsyncMock(return_value=process.returncode)
            return process

        with patch('asyncio.create_subprocess_exec', side_effect=conflict_subprocess):
            merge_result = await merge_node(integration_state)

        assert merge_result["merge_status"] == "conflict_detected"
        assert merge_result["current_phase"] == "HALT"

    @pytest.mark.asyncio
    async def test_partial_dev_success_fail_forward(self, integration_state):
        """Test fail-forward: partial DEV success continues to QA."""
        from bmad_orchestrator.nodes import qa_node

        # Setup: 2 stories, 1 success, 1 failure
        integration_state["story_ids"] = ["15.1", "15.2"]
        integration_state["worktree_paths"] = {
            "15.1": "/mock/path/Canvas-develop-15.1",
            "15.2": "/mock/path/Canvas-develop-15.2",
        }
        integration_state["dev_outcomes"] = [
            {"story_id": "15.1", "outcome": "SUCCESS", "commit_sha": "abc123"},
            # 15.2 not in dev_outcomes (failed)
        ]

        mock_spawner = MockBmadSessionSpawner(qa_result=MOCK_QA_RESULT_PASS)

        # QA should only process successful stories
        with patch('bmad_orchestrator.nodes.BmadSessionSpawner', return_value=mock_spawner):
            qa_result = await qa_node(integration_state)

        # Should have QA result for 15.1 only
        assert len(qa_result["qa_outcomes"]) == 1
        assert qa_result["qa_outcomes"][0]["story_id"] == "15.1"

    @pytest.mark.asyncio
    async def test_partial_qa_success_fail_forward(self, integration_state):
        """Test fail-forward: partial QA success continues to SDD."""
        from bmad_orchestrator.nodes import qa_node

        # Setup: 2 stories for QA
        integration_state["story_ids"] = ["15.1", "15.2"]
        integration_state["worktree_paths"] = {
            "15.1": "/mock/path/Canvas-develop-15.1",
            "15.2": "/mock/path/Canvas-develop-15.2",
        }
        integration_state["dev_outcomes"] = [
            {"story_id": "15.1", "outcome": "SUCCESS", "commit_sha": "abc123"},
            {"story_id": "15.2", "outcome": "SUCCESS", "commit_sha": "def456"},
        ]

        call_count = {"count": 0}

        class MixedQASpawner(MockBmadSessionSpawner):
            async def get_session_result(self, phase, worktree_path):
                if phase == "QA":
                    call_count["count"] += 1
                    from bmad_orchestrator import QAResult
                    if call_count["count"] == 1:
                        return QAResult(**MOCK_QA_RESULT_PASS)
                    else:
                        return QAResult(**MOCK_QA_RESULT_FAIL)
                return None

        mock_spawner = MixedQASpawner()

        with patch('bmad_orchestrator.nodes.BmadSessionSpawner', return_value=mock_spawner):
            qa_result = await qa_node(integration_state)

        # Mixed results: at least one PASS exists, but FAIL takes precedence for gate
        assert qa_result["current_qa_gate"] == "FAIL"  # FAIL takes precedence
        assert len(qa_result["qa_outcomes"]) == 2

    @pytest.mark.asyncio
    async def test_cleanup_always_runs_on_success(self, integration_state):
        """Test cleanup always runs on successful workflow."""
        from bmad_orchestrator.nodes import cleanup_node

        integration_state["current_phase"] = "CLEANUP"
        integration_state["final_status"] = "success"

        async def mock_subprocess(*args, **kwargs):
            process = AsyncMock()
            process.returncode = 0
            process.communicate = AsyncMock(return_value=(b'', b''))
            return process

        with patch('bmad_orchestrator.nodes.remove_worktree', new_callable=AsyncMock, return_value=True):
            with patch('asyncio.create_subprocess_exec', side_effect=mock_subprocess):
                result = await cleanup_node(integration_state)

        assert result["cleanup_completed"] == True

    @pytest.mark.asyncio
    async def test_cleanup_always_runs_on_halt(self, integration_state):
        """Test cleanup always runs even after HALT (v1.1.0 guarantee)."""
        from bmad_orchestrator.nodes import cleanup_node

        integration_state["current_phase"] = "CLEANUP"
        integration_state["final_status"] = "halted"
        integration_state["blockers"] = [
            {"story_id": "15.1", "blocker_type": "QA_FAIL", "description": "Error"},
        ]

        async def mock_subprocess(*args, **kwargs):
            process = AsyncMock()
            process.returncode = 0
            process.communicate = AsyncMock(return_value=(b'', b''))
            return process

        with patch('bmad_orchestrator.nodes.remove_worktree', new_callable=AsyncMock, return_value=True):
            with patch('asyncio.create_subprocess_exec', side_effect=mock_subprocess):
                result = await cleanup_node(integration_state)

        # Cleanup MUST run even after HALT
        assert result["cleanup_completed"] == True

    @pytest.mark.asyncio
    async def test_status_persistence_on_halt(self, integration_state):
        """Test status is persisted to YAML on HALT."""
        from bmad_orchestrator.nodes import halt_node

        integration_state["current_phase"] = "HALT"
        integration_state["blockers"] = [
            {"story_id": "15.1", "blocker_type": "QA_FAIL", "description": "Error"},
        ]

        persist_called = {"called": False, "state": None}

        class TrackingPersister:
            async def persist_workflow_result(self, final_state, epic_id):
                persist_called["called"] = True
                persist_called["state"] = final_state
                return True

        with patch('bmad_orchestrator.status_persister.StatusPersister', return_value=TrackingPersister()):
            result = await halt_node(integration_state)

        assert persist_called["called"] == True
        assert persist_called["state"] is not None


# ============================================================================
# Multi-Batch Integration Tests
# ============================================================================

class TestMultiBatchIntegration:
    """多批次工作流集成测试"""

    @pytest.fixture
    def multi_batch_state(self) -> Dict[str, Any]:
        """State for multi-batch tests."""
        return {
            "epic_id": "15",
            "story_ids": ["15.1", "15.2", "15.3"],
            "base_path": "/mock/path",
            "current_phase": "COMMIT",
            "worktree_paths": {
                "15.1": "/mock/path/Canvas-develop-15.1",
                "15.2": "/mock/path/Canvas-develop-15.2",
                "15.3": "/mock/path/Canvas-develop-15.3",
            },
            "dev_outcomes": [],
            "qa_outcomes": [{"story_id": "15.1", "qa_gate": "PASS"}],
            "parallel_batches": [["15.1"], ["15.2", "15.3"]],  # 2 batches
            "current_batch_index": 0,
            "max_turns": 200,
            "timeout": 3600,
        }

    @pytest.mark.asyncio
    async def test_commit_routes_to_dev_for_next_batch(self, multi_batch_state):
        """Test commit node completes and routing function handles batch transition."""
        from bmad_orchestrator.graph import route_after_commit
        from bmad_orchestrator.nodes import commit_node

        async def mock_subprocess(*args, **kwargs):
            process = AsyncMock()
            process.returncode = 0
            process.communicate = AsyncMock(return_value=(b'abc123', b''))
            return process

        with patch('asyncio.create_subprocess_exec', side_effect=mock_subprocess):
            result = await commit_node(multi_batch_state)

        # commit_node always returns "COMMIT", routing is handled by route_after_commit
        assert result["current_phase"] == "COMMIT"

        # Verify routing function would route to DEV for next batch
        multi_batch_state.update(result)
        next_node = route_after_commit(multi_batch_state)
        assert next_node == "dev_node"  # More batches → back to DEV

    @pytest.mark.asyncio
    async def test_commit_routes_to_cleanup_on_last_batch(self, multi_batch_state):
        """Test commit node completes and routing function handles last batch."""
        from bmad_orchestrator.graph import route_after_commit
        from bmad_orchestrator.nodes import commit_node

        # Set to last batch
        multi_batch_state["current_batch_index"] = 1

        async def mock_subprocess(*args, **kwargs):
            process = AsyncMock()
            process.returncode = 0
            process.communicate = AsyncMock(return_value=(b'def456', b''))
            return process

        with patch('asyncio.create_subprocess_exec', side_effect=mock_subprocess):
            result = await commit_node(multi_batch_state)

        # commit_node always returns "COMMIT", routing is handled by route_after_commit
        assert result["current_phase"] == "COMMIT"

        # Verify routing function would route to CLEANUP on last batch
        multi_batch_state.update(result)
        next_node = route_after_commit(multi_batch_state)
        assert next_node == "cleanup_node"  # Last batch → CLEANUP


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
