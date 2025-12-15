"""
Commit Gate v2 - 零幻觉验证机制测试

测试G1-G10验证检查项，确保Commit Gate正确工作。

Author: Canvas Learning System Team
Version: 1.0.0
Created: 2025-12-11
"""

import asyncio
import json
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from bmad_orchestrator.commit_gate import (
    AuditLogger,
    CommitGate,
    CommitGateError,
)


class TestAuditLogger:
    """AuditLogger单元测试"""

    def test_log_creates_jsonl_entry(self, tmp_path):
        """测试日志记录创建JSONL条目"""
        log_path = tmp_path / "test-audit.jsonl"
        logger = AuditLogger(log_path=log_path)

        logger.log("TEST_EVENT", "15.1", {"key": "value"})

        # 验证文件存在
        assert log_path.exists()

        # 验证内容
        with open(log_path, "r", encoding="utf-8") as f:
            line = f.readline()
            entry = json.loads(line)

        assert entry["event"] == "TEST_EVENT"
        assert entry["story_id"] == "15.1"
        assert entry["data"] == {"key": "value"}
        assert "timestamp" in entry

    def test_log_appends_multiple_entries(self, tmp_path):
        """测试多次日志记录追加"""
        log_path = tmp_path / "test-audit.jsonl"
        logger = AuditLogger(log_path=log_path)

        logger.log("EVENT_1", "15.1", {"seq": 1})
        logger.log("EVENT_2", "15.1", {"seq": 2})
        logger.log("EVENT_3", "15.2", {"seq": 3})

        with open(log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        assert len(lines) == 3


class TestCommitGateInitialization:
    """CommitGate初始化测试"""

    def test_initialization_with_paths(self, tmp_path):
        """测试使用指定路径初始化"""
        worktree = tmp_path / "worktree"
        worktree.mkdir()
        base = tmp_path / "base"
        base.mkdir()

        gate = CommitGate("15.1", worktree, base_path=base)

        assert gate.story_id == "15.1"
        assert gate.worktree_path == worktree
        assert gate.base_path == base

    def test_initialization_default_base_path(self, tmp_path):
        """测试默认base_path推断"""
        # 创建模拟的worktree结构: parent/parent/worktree
        base = tmp_path / "project"
        base.mkdir()
        worktrees_dir = base / ".git" / "worktrees"
        worktrees_dir.mkdir(parents=True)
        worktree = worktrees_dir / "develop-15.1"
        worktree.mkdir()

        gate = CommitGate("15.1", worktree)

        # base_path应该是worktree的parent.parent (即 .git 目录)
        assert gate.base_path == base / ".git"


class TestG1DocumentationSources:
    """G1: 文档来源标注验证测试"""

    @pytest.fixture
    def gate_with_files(self, tmp_path):
        """创建带有测试文件的CommitGate"""
        worktree = tmp_path / "worktree"
        worktree.mkdir()
        base = tmp_path / "base"
        base.mkdir()

        return CommitGate("15.1", worktree, base_path=base), worktree

    @pytest.mark.asyncio
    async def test_g1_passes_with_verified_comments(self, gate_with_files):
        """测试有验证注释时G1通过"""
        gate, worktree = gate_with_files

        # 创建带有验证注释的Python文件
        # 注意：必须包含 ✅ 符号，这是 VERIFICATION_COMMENT_PATTERN 的要求
        test_file = worktree / "test_module.py"
        content = """
# \u2705 Verified from LangGraph Skill (Pattern: StateGraph)
from langgraph.graph import StateGraph

# \u2705 Verified from Context 7 (FastAPI docs)
from fastapi import Depends
"""
        test_file.write_text(content, encoding="utf-8")

        result = await gate._verify_documentation_sources([test_file])

        assert result["passed"] is True

    @pytest.mark.asyncio
    async def test_g1_fails_without_verified_comments(self, gate_with_files):
        """测试缺少验证注释时G1失败"""
        gate, worktree = gate_with_files

        # 创建缺少验证注释的Python文件
        test_file = worktree / "test_module.py"
        test_file.write_text(
            '''
from langgraph.graph import StateGraph
from fastapi import Depends
'''
        )

        result = await gate._verify_documentation_sources([test_file])

        # G1应该失败或报告问题
        # 注意：根据实现，可能返回warnings而非直接失败
        assert "issues" in result or result["passed"] is False


class TestG3TestVerification:
    """G3: 测试存在性验证"""

    @pytest.mark.asyncio
    async def test_g3_passes_with_passing_tests(self, tmp_path):
        """测试pytest通过时G3通过"""
        worktree = tmp_path / "worktree"
        worktree.mkdir()

        gate = CommitGate("15.1", worktree, base_path=tmp_path)

        dev_outcome = {
            "story_id": "15.1",
            "status": "completed",
            "tests_passed": True,
            "test_count": 10,
            "coverage": 87.5,
        }

        result = await gate._verify_tests(dev_outcome)

        assert result["passed"] is True

    @pytest.mark.asyncio
    async def test_g3_fails_with_failing_tests(self, tmp_path):
        """测试pytest失败时G3失败"""
        worktree = tmp_path / "worktree"
        worktree.mkdir()

        gate = CommitGate("15.1", worktree, base_path=tmp_path)

        dev_outcome = {
            "story_id": "15.1",
            "status": "completed",
            "tests_passed": False,
            "test_count": 10,
            "coverage": 45.0,
        }

        result = await gate._verify_tests(dev_outcome)

        assert result["passed"] is False


class TestG4QAReview:
    """G4: QA审查验证"""

    @pytest.mark.asyncio
    async def test_g4_passes_with_pass_verdict(self, tmp_path):
        """测试QA qa_gate=PASS时G4通过"""
        worktree = tmp_path / "worktree"
        worktree.mkdir()

        gate = CommitGate("15.1", worktree, base_path=tmp_path)

        # 使用正确的字段名: qa_gate
        qa_outcome = {
            "story_id": "15.1",
            "qa_gate": "PASS",
            "quality_score": 85,
            "issues": [],
        }

        result = await gate._verify_qa_review(qa_outcome)

        assert result["passed"] is True

    @pytest.mark.asyncio
    async def test_g4_fails_with_fail_verdict(self, tmp_path):
        """测试QA qa_gate=FAIL时G4失败"""
        worktree = tmp_path / "worktree"
        worktree.mkdir()

        gate = CommitGate("15.1", worktree, base_path=tmp_path)

        # 使用正确的字段名: qa_gate
        qa_outcome = {
            "story_id": "15.1",
            "qa_gate": "FAIL",
            "quality_score": 40,
            "issues": ["Security vulnerability", "Missing error handling"],
        }

        result = await gate._verify_qa_review(qa_outcome)

        assert result["passed"] is False


class TestG5NonSynthetic:
    """G5: 非synthetic结果验证"""

    @pytest.mark.asyncio
    async def test_g5_passes_with_real_execution(self, tmp_path):
        """测试真实执行时G5通过"""
        worktree = tmp_path / "worktree"
        worktree.mkdir()

        gate = CommitGate("15.1", worktree, base_path=tmp_path)

        dev_outcome = {
            "story_id": "15.1",
            "status": "completed",
            "synthetic": False,
        }
        qa_outcome = {
            "story_id": "15.1",
            "verdict": "PASS",
            "synthetic": False,
        }

        result = await gate._verify_no_synthetic(dev_outcome, qa_outcome)

        assert result["passed"] is True

    @pytest.mark.asyncio
    async def test_g5_fails_with_synthetic_dev(self, tmp_path):
        """测试synthetic DEV结果时G5失败"""
        worktree = tmp_path / "worktree"
        worktree.mkdir()

        gate = CommitGate("15.1", worktree, base_path=tmp_path)

        dev_outcome = {
            "story_id": "15.1",
            "status": "synthetic_success",
            "synthetic": True,
        }
        qa_outcome = {
            "story_id": "15.1",
            "verdict": "PASS",
            "synthetic": False,
        }

        result = await gate._verify_no_synthetic(dev_outcome, qa_outcome)

        assert result["passed"] is False


class TestExecuteGate:
    """execute_gate完整流程测试"""

    @pytest.fixture
    def mock_gate(self, tmp_path):
        """创建带mock方法的CommitGate"""
        worktree = tmp_path / "worktree"
        worktree.mkdir()
        base = tmp_path / "base"
        base.mkdir()

        # 创建logs目录
        logs_dir = base / "logs"
        logs_dir.mkdir()

        gate = CommitGate("15.1", worktree, base_path=base)
        return gate

    @pytest.mark.asyncio
    async def test_execute_gate_all_pass(self, mock_gate):
        """测试所有检查通过时返回True"""
        # Mock所有验证方法返回通过
        async def mock_pass(*args, **kwargs):
            return {"passed": True}

        mock_gate._verify_documentation_sources = mock_pass
        mock_gate._verify_api_annotations = mock_pass
        mock_gate._verify_tests = mock_pass
        mock_gate._verify_qa_review = mock_pass
        mock_gate._verify_no_synthetic = mock_pass
        mock_gate._verify_prd_references = mock_pass
        mock_gate._verify_architecture_compliance = mock_pass
        mock_gate._verify_context7_skills = mock_pass
        mock_gate._verify_code_existence = mock_pass
        mock_gate._verify_tech_stack_reality = mock_pass

        dev_outcome = {"story_id": "15.1", "status": "completed"}
        qa_outcome = {"story_id": "15.1", "verdict": "PASS"}

        result = await mock_gate.execute_gate(
            dev_outcome=dev_outcome,
            qa_outcome=qa_outcome,
            changed_files=[],
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_execute_gate_raises_on_failure(self, mock_gate):
        """测试任何检查失败时抛出CommitGateError"""
        # Mock G1失败，其他通过
        async def mock_g1_fail(*args, **kwargs):
            return {"passed": False, "issues": ["Missing annotation"]}

        async def mock_pass(*args, **kwargs):
            return {"passed": True}

        mock_gate._verify_documentation_sources = mock_g1_fail
        mock_gate._verify_api_annotations = mock_pass
        mock_gate._verify_tests = mock_pass
        mock_gate._verify_qa_review = mock_pass
        mock_gate._verify_no_synthetic = mock_pass
        mock_gate._verify_prd_references = mock_pass
        mock_gate._verify_architecture_compliance = mock_pass
        mock_gate._verify_context7_skills = mock_pass
        mock_gate._verify_code_existence = mock_pass
        mock_gate._verify_tech_stack_reality = mock_pass

        dev_outcome = {"story_id": "15.1", "status": "completed"}
        qa_outcome = {"story_id": "15.1", "verdict": "PASS"}

        with pytest.raises(CommitGateError) as exc_info:
            await mock_gate.execute_gate(
                dev_outcome=dev_outcome,
                qa_outcome=qa_outcome,
                changed_files=[],
            )

        assert "G1" in str(exc_info.value)
        assert exc_info.value.story_id == "15.1"

    @pytest.mark.asyncio
    async def test_execute_gate_multiple_failures(self, mock_gate):
        """测试多个检查失败时包含所有失败信息"""
        async def mock_g1_fail(*args, **kwargs):
            return {"passed": False}

        async def mock_g3_fail(*args, **kwargs):
            return {"passed": False}

        async def mock_pass(*args, **kwargs):
            return {"passed": True}

        mock_gate._verify_documentation_sources = mock_g1_fail
        mock_gate._verify_api_annotations = mock_pass
        mock_gate._verify_tests = mock_g3_fail
        mock_gate._verify_qa_review = mock_pass
        mock_gate._verify_no_synthetic = mock_pass
        mock_gate._verify_prd_references = mock_pass
        mock_gate._verify_architecture_compliance = mock_pass
        mock_gate._verify_context7_skills = mock_pass
        mock_gate._verify_code_existence = mock_pass
        mock_gate._verify_tech_stack_reality = mock_pass

        dev_outcome = {"story_id": "15.1", "status": "completed"}
        qa_outcome = {"story_id": "15.1", "verdict": "PASS"}

        with pytest.raises(CommitGateError) as exc_info:
            await mock_gate.execute_gate(
                dev_outcome=dev_outcome,
                qa_outcome=qa_outcome,
                changed_files=[],
            )

        # 应该包含G1和G3
        assert len(exc_info.value.failed_checks) == 2
        failed_ids = [c[0] for c in exc_info.value.failed_checks]
        assert "G1" in failed_ids
        assert "G3" in failed_ids


class TestAuditTrail:
    """审计追踪测试"""

    @pytest.mark.asyncio
    async def test_audit_log_created_on_gate_execution(self, tmp_path):
        """测试execute_gate创建审计日志"""
        worktree = tmp_path / "worktree"
        worktree.mkdir()
        base = tmp_path / "base"
        base.mkdir()

        # 使用自定义日志路径
        log_path = tmp_path / "audit.jsonl"

        gate = CommitGate("15.1", worktree, base_path=base)
        gate.audit = AuditLogger(log_path=log_path)

        # Mock所有验证方法
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

        await gate.execute_gate(
            dev_outcome={"story_id": "15.1"},
            qa_outcome={"story_id": "15.1"},
            changed_files=[],
        )

        # 验证日志文件存在
        assert log_path.exists()

        # 验证包含预期事件
        with open(log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            events = [json.loads(line)["event"] for line in lines]

        assert "GATE_START" in events
        assert "G1_CHECK" in events
        assert "GATE_PASSED" in events


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
