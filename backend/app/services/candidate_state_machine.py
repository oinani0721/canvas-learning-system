"""Story 2.5.X Task 2 — Candidate 6 状态机校验 + 状态变更 helper.

AC #2 (Story 2.5.X):
- 6 状态: pending | accepted | edited | dismissed | disputed | expired
- 仅允许 pending → {accepted, edited, dismissed, disputed, expired} 转换
- 反向转换 (如 accepted → pending) 被拒 (HTTP 422)
- 状态变更必须自动记录 status_changed_at + status_changed_by

Story trace: _bmad-output/implementation-artifacts/epic-2/2-5-x-error-candidate-progressive-confirmation.md
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from fastapi import HTTPException

# ═══════════════════════════════════════════════════════════════════════════════
# 6 状态机定义 (AC #2)
# ═══════════════════════════════════════════════════════════════════════════════

CandidateStatus = Literal[
    "pending",
    "accepted",
    "edited",
    "dismissed",
    "disputed",
    "expired",
]

# 合法转换图：
#   pending 是唯一初始/活跃状态
#   其他 5 个是终态 (terminal, 不可再转出)
#   反向转换 (如 accepted → pending) 全部被拒
ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "pending": {"accepted", "edited", "dismissed", "disputed", "expired"},
    "accepted": set(),  # 终态: 已确认入 errors[], 不可逆
    "edited": set(),  # 终态: 用户编辑后入 errors[], 不可逆
    "dismissed": set(),  # 终态: 用户标 AI 误判, 保留 candidate 但不入 errors[]
    "disputed": set(),  # 终态: 用户有异议 + dispute_reason, 保留 candidate 不入 errors[]
    "expired": set(),  # 终态: 30 天未处理自动归档
}

# 状态变更归属: user (用户主动) / system (cron 自动 expire)
StatusChangeAuthor = Literal["user", "system"]


# ═══════════════════════════════════════════════════════════════════════════════
# Task 2.2 + 2.3 — 状态转换校验
# ═══════════════════════════════════════════════════════════════════════════════


def validate_status_transition(current: str, target: str) -> None:
    """Story 2.5.X AC #2 — 校验状态机合法转换 (非法 → HTTP 422).

    Args:
        current: 当前 candidate.status (从 frontmatter 读)
        target: 期望的新 status

    Raises:
        HTTPException(422): current 不是合法 status, OR target 不在允许集合
    """
    if current not in ALLOWED_TRANSITIONS:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Unknown candidate status: '{current}'. "
                f"Valid statuses: {sorted(ALLOWED_TRANSITIONS.keys())}"
            ),
        )

    allowed = ALLOWED_TRANSITIONS[current]
    if target not in allowed:
        if not allowed:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Illegal status transition: '{current}' is a terminal state "
                    f"(no further transitions allowed). Cannot transition to '{target}'."
                ),
            )
        raise HTTPException(
            status_code=422,
            detail=(
                f"Illegal status transition: '{current}' → '{target}'. "
                f"Allowed transitions from '{current}': {sorted(allowed)}"
            ),
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Task 2.4 — 状态变更 helper (自动写 status_changed_at + status_changed_by)
# ═══════════════════════════════════════════════════════════════════════════════


def apply_status_change(
    candidate: dict[str, Any],
    target: CandidateStatus,
    *,
    changed_by: StatusChangeAuthor = "user",
) -> dict[str, Any]:
    """Story 2.5.X AC #2 Task 2.4 — 应用状态变更, 自动写时间戳 + 归属.

    校验 + in-place mutation + 返回. 调用方应在 frontmatter 写入前调本函数.

    Args:
        candidate: existing candidate dict (from error_candidates[])
        target: new CandidateStatus value
        changed_by: "user" (默认, 用户主动) / "system" (cron expire)

    Returns:
        Mutated candidate dict (含 status_changed_at + status_changed_by 字段)

    Raises:
        HTTPException(422): 非法转换 (来自 validate_status_transition)
    """
    current = candidate.get("status", "pending")
    validate_status_transition(current, target)

    candidate["status"] = target
    candidate["status_changed_at"] = datetime.now(timezone.utc).isoformat()
    candidate["status_changed_by"] = changed_by
    return candidate


def is_terminal_status(status: str) -> bool:
    """Helper — 判断 status 是否为终态 (不可再转出).

    Useful for Dashboard 过滤 (只显示 status=pending 的候选).
    """
    if status not in ALLOWED_TRANSITIONS:
        return False  # unknown status, 保守判定为非终态
    return len(ALLOWED_TRANSITIONS[status]) == 0


def is_active_status(status: str) -> bool:
    """Helper — 判断 status 是否为活跃 (用户可操作)."""
    return status == "pending"
