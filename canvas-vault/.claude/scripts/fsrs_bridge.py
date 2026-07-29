#!/usr/bin/env python3
"""FSRS WHEN 桥 (FSRS-V2-2026-07-30, [Decision-FSRS-1/2])。

职责: 把 quiz-answer 的一次评分翻译成 py-fsrs 复习, 产出 6 个加性
frontmatter 字段 (fsrs_due/state/step/stability/difficulty/last_review)。
无字段 = New 卡即刻到期 (零迁移)。

调用形态: quiz-answer 静态段用系统 python3 (stdlib) 经 stdin JSON 调本
文件; 本文件发现 fsrs 不可导入时自动 re-exec backend/.venv python。
调度计算全部收拢在写侧 — 读侧 (daily_review_pick/Dashboard) 只做字符串
日期比较, 维持 launchd 纯 stdlib 契约 (审查报告 §四-④)。

参数契约: DEFAULT_PARAMETERS + desired_retention=0.9 + enable_fuzzing=False
(可复现可测试; 个人化拟合 F6 延后)。被 backend/tests/regression/
test_fsrs_bridge.py 锁定。
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone

def _venv_python() -> str | None:
    """候选顺序: 相对本 vault 的仓库根 backend/.venv (worktree 与主仓副本各自
    成立, Code-Review H1: 不能让 live vault 的 FSRS 写侧系于 dev worktree
    存亡) → 硬编码 worktree 路径兜底。"""
    from pathlib import Path

    candidates = [
        Path(__file__).resolve().parents[3] / "backend" / ".venv" / "bin" / "python",
        Path(
            "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/"
            "feature-obsidian-hybrid-dev/backend/.venv/bin/python"
        ),
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    return None

FIELD_ORDER = (
    "fsrs_due", "fsrs_state", "fsrs_step",
    "fsrs_stability", "fsrs_difficulty", "fsrs_last_review",
)


def _aware(s: str) -> datetime:
    dt = datetime.fromisoformat(str(s).strip().replace("Z", "+00:00"))
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def rating_from_grade(grade_norm: float, abandoned: bool) -> int:
    """[Decision-FSRS-1] 弃答→Again; 否则还原 grade=1+3·gn 就近落四档。"""
    if abandoned:
        return 1
    g = 1.0 + 3.0 * max(0.0, min(1.0, float(grade_norm)))
    if g < 1.5:
        return 1
    if g < 2.5:
        return 2
    if g < 3.5:
        return 3
    return 4


def fields_from_frontmatter(fm: str) -> dict:
    """从 frontmatter 文本抽 fsrs_* 字段 (纯 stdlib, 读侧同款正则)。"""
    out = {}
    for key in FIELD_ORDER:
        m = re.search(rf'^{key}:\s*"?([^"\n]+?)"?\s*$', fm, re.M)
        if m:
            out[key] = m.group(1).strip()
    return out


def review(fields: dict, grade_norm: float, abandoned: bool, ts: str) -> dict:
    """一次评分 → 新 fsrs_* 字段 (需要 fsrs 可导入)。"""
    from fsrs import Card, Rating, Scheduler, State

    now = _aware(ts)
    sched = Scheduler(enable_fuzzing=False)
    if fields.get("fsrs_due"):
        step = fields.get("fsrs_step")
        card = Card(
            state=State(int(fields.get("fsrs_state", 1))),
            step=int(step) if step not in (None, "") else None,
            stability=float(fields["fsrs_stability"]) if fields.get("fsrs_stability") else None,
            difficulty=float(fields["fsrs_difficulty"]) if fields.get("fsrs_difficulty") else None,
            due=_aware(fields["fsrs_due"]),
            last_review=_aware(fields["fsrs_last_review"]) if fields.get("fsrs_last_review") else None,
        )
    else:
        card = Card(due=now)  # 无字段 = New 卡即刻到期 (零迁移)

    card, _log = sched.review_card(
        card, Rating(rating_from_grade(grade_norm, abandoned)), review_datetime=now
    )
    out = {
        "fsrs_due": _iso(card.due),
        "fsrs_state": int(card.state),
        "fsrs_step": card.step if card.step is not None else "",
        "fsrs_stability": round(card.stability, 4) if card.stability is not None else "",
        "fsrs_difficulty": round(card.difficulty, 4) if card.difficulty is not None else "",
        "fsrs_last_review": _iso(now),
    }
    out["fm_block"] = "\n".join(
        f"{k}: {out[k]}" for k in FIELD_ORDER if out[k] != ""
    )
    return out


def _ensure_fsrs() -> bool:
    try:
        import fsrs  # noqa: F401
        return True
    except ImportError:
        venv_py = _venv_python()
        if os.environ.get("FSRS_BRIDGE_REEXEC") != "1" and venv_py:
            os.environ["FSRS_BRIDGE_REEXEC"] = "1"
            os.execv(venv_py, [venv_py, os.path.abspath(__file__)] + sys.argv[1:])
        return False


def main() -> int:
    if not _ensure_fsrs():
        print(json.dumps({"error": "fsrs_unavailable — backend/.venv 缺失或未装 fsrs"}))
        return 3
    p = json.load(sys.stdin)
    out = review(
        fields_from_frontmatter(p.get("fm", "")),
        float(p.get("grade_norm", 0.0)),
        bool(p.get("abandoned")),
        p["ts"],
    )
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
