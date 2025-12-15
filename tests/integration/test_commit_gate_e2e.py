"""
Commit Gate v2 - 端到端集成测试

测试完整的Gate执行流程，验证：
1. 所有检查通过时返回True
2. 任何检查失败时抛出CommitGateError
3. 审计日志正确记录

Author: Canvas Learning System Team
Version: 1.0.0
Created: 2025-12-11
"""

import asyncio
import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from bmad_orchestrator.commit_gate import (
    AuditLogger,
    CommitGate,
    CommitGateError,
)


class TestE2EGateExecution:
    """端到端Gate执行测试"""

    @pytest.fixture
    def setup_gate(self, tmp_path):
        """创建测试环境"""
        worktree = tmp_path / "worktree"
        worktree.mkdir()
        base = tmp_path / "base"
        base.mkdir()

        # 创建logs目录
        logs_dir = base / "logs"
        logs_dir.mkdir()

        # 创建审计日志路径
        audit_log_path = tmp_path / "e2e-audit.jsonl"

        gate = CommitGate("15.1", worktree, base_path=base)
        gate.audit = AuditLogger(log_path=audit_log_path)

        return gate, audit_log_path

    @pytest.mark.asyncio
    async def test_e2e_all_checks_pass(self, setup_gate):
        """E2E测试：所有检查通过"""
        gate, audit_log_path = setup_gate

        # Mock所有验证方法返回通过
        async def mock_pass(*args, **kwargs):
            return {"passed": True}

        gate._verify_documentation_sources = mock_pass
        gate._verify_api_annotations = mock_pass
        gate._verify_tests = mock_pass
        gate._verify_qa_review = mock_pass
        gate._verify_no_synthetic = mock_pass
        gate._verify_prd_references = mock_pass
        gate._verify_architecture_compliance = mock_pass
        gate._verify_context7_skills = mock_pass
        gate._verify_code_existence = mock_pass
        gate._verify_tech_stack_reality = mock_pass

        # 准备输入
        dev_outcome = {
            "story_id": "15.1",
            "status": "completed",
            "tests_passed": True,
            "synthetic": False,
        }
        qa_outcome = {
            "story_id": "15.1",
            "qa_gate": "PASS",
            "synthetic": False,
        }

        # 执行Gate
        result = await gate.execute_gate(
            dev_outcome=dev_outcome,
            qa_outcome=qa_outcome,
            changed_files=[],
        )

        # 验证结果
        assert result is True, "Gate should pass when all checks pass"

        # 验证审计日志
        assert audit_log_path.exists(), "Audit log should be created"

        with open(audit_log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            events = [json.loads(line)["event"] for line in lines]

        assert "GATE_START" in events, "GATE_START event should be logged"
        assert "GATE_PASSED" in events, "GATE_PASSED event should be logged"

    @pytest.mark.asyncio
    async def test_e2e_g1_fails(self, setup_gate):
        """E2E测试：G1失败，Gate应该抛出异常"""
        gate, audit_log_path = setup_gate

        # Mock G1失败
        async def mock_g1_fail(*args, **kwargs):
            return {"passed": False, "issues": ["Missing verification comment"]}

        async def mock_pass(*args, **kwargs):
            return {"passed": True}

        gate._verify_documentation_sources = mock_g1_fail
        gate._verify_api_annotations = mock_pass
        gate._verify_tests = mock_pass
        gate._verify_qa_review = mock_pass
        gate._verify_no_synthetic = mock_pass
        gate._verify_prd_references = mock_pass
        gate._verify_architecture_compliance = mock_pass
        gate._verify_context7_skills = mock_pass
        gate._verify_code_existence = mock_pass
        gate._verify_tech_stack_reality = mock_pass

        dev_outcome = {"story_id": "15.1", "status": "completed"}
        qa_outcome = {"story_id": "15.1", "qa_gate": "PASS"}

        # 执行Gate，应该抛出异常
        with pytest.raises(CommitGateError) as exc_info:
            await gate.execute_gate(
                dev_outcome=dev_outcome,
                qa_outcome=qa_outcome,
                changed_files=[],
            )

        # 验证异常内容
        assert exc_info.value.story_id == "15.1"
        assert "G1" in [c[0] for c in exc_info.value.failed_checks]

        # 验证审计日志记录了失败
        with open(audit_log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            events = [json.loads(line)["event"] for line in lines]

        assert "GATE_START" in events
        assert "GATE_FAILED" in events or "G1_CHECK" in events

    @pytest.mark.asyncio
    async def test_e2e_multiple_failures(self, setup_gate):
        """E2E测试：多个检查失败"""
        gate, audit_log_path = setup_gate

        # Mock G1和G3失败
        async def mock_g1_fail(*args, **kwargs):
            return {"passed": False}

        async def mock_g3_fail(*args, **kwargs):
            return {"passed": False}

        async def mock_pass(*args, **kwargs):
            return {"passed": True}

        gate._verify_documentation_sources = mock_g1_fail
        gate._verify_api_annotations = mock_pass
        gate._verify_tests = mock_g3_fail
        gate._verify_qa_review = mock_pass
        gate._verify_no_synthetic = mock_pass
        gate._verify_prd_references = mock_pass
        gate._verify_architecture_compliance = mock_pass
        gate._verify_context7_skills = mock_pass
        gate._verify_code_existence = mock_pass
        gate._verify_tech_stack_reality = mock_pass

        dev_outcome = {"story_id": "15.1", "status": "completed"}
        qa_outcome = {"story_id": "15.1", "qa_gate": "PASS"}

        with pytest.raises(CommitGateError) as exc_info:
            await gate.execute_gate(
                dev_outcome=dev_outcome,
                qa_outcome=qa_outcome,
                changed_files=[],
            )

        # 验证包含两个失败
        failed_ids = [c[0] for c in exc_info.value.failed_checks]
        assert len(failed_ids) == 2
        assert "G1" in failed_ids
        assert "G3" in failed_ids

    @pytest.mark.asyncio
    async def test_e2e_audit_trail_complete(self, setup_gate):
        """E2E测试：验证审计日志完整性"""
        gate, audit_log_path = setup_gate

        async def mock_pass(*args, **kwargs):
            return {"passed": True}

        # 设置所有mock
        gate._verify_documentation_sources = mock_pass
        gate._verify_api_annotations = mock_pass
        gate._verify_tests = mock_pass
        gate._verify_qa_review = mock_pass
        gate._verify_no_synthetic = mock_pass
        gate._verify_prd_references = mock_pass
        gate._verify_architecture_compliance = mock_pass
        gate._verify_context7_skills = mock_pass
        gate._verify_code_existence = mock_pass
        gate._verify_tech_stack_reality = mock_pass

        dev_outcome = {"story_id": "15.1", "status": "completed"}
        qa_outcome = {"story_id": "15.1", "qa_gate": "PASS"}

        await gate.execute_gate(
            dev_outcome=dev_outcome,
            qa_outcome=qa_outcome,
            changed_files=[],
        )

        # 验证审计日志结构
        with open(audit_log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # 至少应该有GATE_START和GATE_PASSED
        assert len(lines) >= 2

        # 验证每行都是有效JSON
        for line in lines:
            entry = json.loads(line)
            assert "timestamp" in entry
            assert "event" in entry
            assert "story_id" in entry


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
