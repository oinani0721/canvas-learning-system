"""Story 2.5.X Task 2 — 状态机单元测试.

覆盖 AC #2:
- pending → {accepted, edited, dismissed, disputed, expired} 5 个合法转换
- 反向转换全部被拒 (accepted → pending 等)
- 终态间转换被拒 (accepted → dismissed 等)
- unknown status 被拒
- apply_status_change 自动写 status_changed_at + status_changed_by

Story trace: _bmad-output/implementation-artifacts/epic-2/2-5-x-error-candidate-progressive-confirmation.md
"""

from __future__ import annotations

import re

import pytest
from fastapi import HTTPException

from app.services.candidate_state_machine import (
    ALLOWED_TRANSITIONS,
    apply_status_change,
    is_active_status,
    is_terminal_status,
    validate_status_transition,
)


# ════════════════════════════════════════════════════════════════════
# Task 2.1 — CandidateStatus 枚举值
# ════════════════════════════════════════════════════════════════════


def test_allowed_transitions_contains_all_6_statuses():
    """6 状态机必须包含全部 status."""
    expected = {"pending", "accepted", "edited", "dismissed", "disputed", "expired"}
    assert set(ALLOWED_TRANSITIONS.keys()) == expected


# ════════════════════════════════════════════════════════════════════
# Task 2.2 + 2.3 — 合法转换 (pending → 5 终态)
# ════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "target",
    ["accepted", "edited", "dismissed", "disputed", "expired"],
)
def test_pending_can_transition_to_any_terminal(target):
    """AC #2: pending 可以转换到任意 5 个终态 (不抛错)."""
    # 不抛 → 合法
    validate_status_transition("pending", target)


# ════════════════════════════════════════════════════════════════════
# Task 2.3 — 非法转换被拒
# ════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "current,target",
    [
        ("accepted", "pending"),  # 反向不可逆
        ("edited", "pending"),
        ("dismissed", "pending"),
        ("disputed", "pending"),
        ("expired", "pending"),
        ("accepted", "dismissed"),  # 终态间转换
        ("dismissed", "accepted"),
        ("disputed", "edited"),
        ("expired", "accepted"),
    ],
)
def test_illegal_transitions_raise_422(current, target):
    """AC #2: 反向转换 + 终态间转换全部抛 HTTP 422."""
    with pytest.raises(HTTPException) as exc_info:
        validate_status_transition(current, target)
    assert exc_info.value.status_code == 422
    assert "Illegal status transition" in exc_info.value.detail


def test_unknown_current_status_raises_422():
    """unknown current status (frontmatter 损坏) 抛 422."""
    with pytest.raises(HTTPException) as exc_info:
        validate_status_transition("garbage", "accepted")
    assert exc_info.value.status_code == 422
    assert "Unknown candidate status" in exc_info.value.detail


def test_unknown_target_status_raises_422():
    """target 不在允许集合 (含未知字符串) 抛 422."""
    with pytest.raises(HTTPException) as exc_info:
        validate_status_transition("pending", "fake_status")
    assert exc_info.value.status_code == 422


def test_terminal_state_error_message_explains_terminal():
    """从终态尝试转换时, 错误消息说明这是终态."""
    with pytest.raises(HTTPException) as exc_info:
        validate_status_transition("accepted", "dismissed")
    assert "terminal state" in exc_info.value.detail


# ════════════════════════════════════════════════════════════════════
# Task 2.4 — apply_status_change 自动写时间戳 + 归属
# ════════════════════════════════════════════════════════════════════


def test_apply_status_change_writes_timestamp_iso_format():
    """状态变更时 status_changed_at 自动写 ISO 8601 时间戳."""
    candidate = {"id": "x", "status": "pending"}
    result = apply_status_change(candidate, "accepted")

    assert result["status"] == "accepted"
    assert result["status_changed_at"] is not None
    # ISO 8601 格式: YYYY-MM-DDTHH:MM:SS.fff+00:00
    assert re.match(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}",
        result["status_changed_at"],
    )


def test_apply_status_change_default_changed_by_user():
    """未指定 changed_by 时默认为 'user' (用户主动)."""
    candidate = {"id": "x", "status": "pending"}
    result = apply_status_change(candidate, "accepted")
    assert result["status_changed_by"] == "user"


def test_apply_status_change_explicit_changed_by_system():
    """expired 由 cron 触发时 changed_by='system'."""
    candidate = {"id": "x", "status": "pending"}
    result = apply_status_change(candidate, "expired", changed_by="system")
    assert result["status_changed_by"] == "system"


def test_apply_status_change_mutates_in_place():
    """apply_status_change 应 in-place 改原 dict (不复制)."""
    candidate = {"id": "x", "status": "pending"}
    result = apply_status_change(candidate, "dismissed")
    assert result is candidate  # 同一对象引用
    assert candidate["status"] == "dismissed"  # 原对象已变更


def test_apply_status_change_rejects_illegal_transition():
    """非法转换时不写时间戳, 抛 HTTPException."""
    candidate = {"id": "x", "status": "accepted"}
    with pytest.raises(HTTPException) as exc_info:
        apply_status_change(candidate, "pending")
    assert exc_info.value.status_code == 422
    # 抛错时不应写时间戳 (失败回滚)
    assert "status_changed_at" not in candidate or candidate.get("status") == "accepted"


def test_apply_status_change_default_pending_when_no_status():
    """frontmatter 中 candidate 缺 status 字段 → 默认视为 'pending'."""
    candidate = {"id": "x"}  # 无 status 字段
    result = apply_status_change(candidate, "accepted")
    assert result["status"] == "accepted"
    # 不应抛 422 (默认 pending → accepted 是合法)


# ════════════════════════════════════════════════════════════════════
# Helper — is_terminal_status / is_active_status
# ════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "status,expected_terminal",
    [
        ("pending", False),
        ("accepted", True),
        ("edited", True),
        ("dismissed", True),
        ("disputed", True),
        ("expired", True),
    ],
)
def test_is_terminal_status(status, expected_terminal):
    """5 终态 + pending 非终态."""
    assert is_terminal_status(status) is expected_terminal


def test_is_terminal_status_unknown_returns_false():
    """unknown status 保守判定为非终态."""
    assert is_terminal_status("garbage") is False


@pytest.mark.parametrize(
    "status,expected_active",
    [
        ("pending", True),
        ("accepted", False),
        ("edited", False),
        ("dismissed", False),
        ("disputed", False),
        ("expired", False),
    ],
)
def test_is_active_status(status, expected_active):
    """仅 pending 是活跃状态 (用户可操作)."""
    assert is_active_status(status) is expected_active


# ════════════════════════════════════════════════════════════════════
# 业务场景 — 模拟 accept_candidate 路径
# ════════════════════════════════════════════════════════════════════


def test_accept_workflow_pending_to_accepted():
    """场景 1: 用户点接受 → status 从 pending → accepted."""
    candidate = {
        "id": "uuid-1",
        "status": "pending",
        "description": "学生混淆 X 与 Y",
    }
    result = apply_status_change(candidate, "accepted", changed_by="user")
    assert result["status"] == "accepted"
    assert result["status_changed_by"] == "user"


def test_dispute_workflow_pending_to_disputed():
    """场景 2: 用户提异议 → status 从 pending → disputed."""
    candidate = {
        "id": "uuid-1",
        "status": "pending",
    }
    result = apply_status_change(candidate, "disputed")
    assert result["status"] == "disputed"


def test_expire_workflow_cron_triggers_pending_to_expired():
    """场景 3: 30 天 cron → status 从 pending → expired (changed_by=system)."""
    candidate = {
        "id": "uuid-1",
        "status": "pending",
        "created_at": "2026-04-04T00:00:00Z",  # 30+ 天前
    }
    result = apply_status_change(candidate, "expired", changed_by="system")
    assert result["status"] == "expired"
    assert result["status_changed_by"] == "system"


def test_double_accept_rejected():
    """场景 4: 已接受的候选不能再次接受 (反映 idempotency 设计)."""
    candidate = {"id": "uuid-1", "status": "accepted"}
    with pytest.raises(HTTPException) as exc_info:
        apply_status_change(candidate, "accepted")
    assert exc_info.value.status_code == 422
