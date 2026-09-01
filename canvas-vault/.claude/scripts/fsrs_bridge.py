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

时刻契约 (CARD-G3-2, schema v1 §6.2 A5/A6; 修 §九登记的 bridge 三缺陷):
  - **统一 UTC**: 入参一律 astimezone(UTC) 后再交给调度器 —— fsrs 库对
    review_datetime 硬校验 "tz-aware 且 tzinfo 恰为 UTC"
    (scheduler.py:256-260), 原实现只补 tzinfo 不转换, 于是合法的
    '12:00:00+08:00' 会被库抛 ValueError;
  - **naive 拒绝**: 不带时区的时刻**拒收并在 stdout 明说**, 不再静默当 UTC ——
    无时区的时刻无法与水位线 W 做绝对瞬间比较, 猜一个时区等于伪造事实;
  - **整秒对齐**: 复习时刻在**入口**截到整秒 (原实现只在 _iso() 输出时截,
    于是写出的 W 与事件里的 review_time 差一个小数秒, A5 的"同一瞬间"不成立,
    重放时 10:00:00.5 > 10:00:00 恒真 ⇒ 同一事件被二次推进)。
  输出的 review_time 即本次实际采用的整秒 UTC 时刻, 与 fsrs_last_review 逐字相同;
  调用方必须把它写进事件 payload, 不要自己另算一份。

stdout 加性字段 (向后兼容, 老调用方只读 fm_block 不受影响):
  review_time / rating / fsrs_library_version / fsrs_params_hash。
stdin 加性字段: rating (可选, 显式指定 FSRS Rating; 缺省仍按 grade_norm+abandoned
  推导) —— 供 G3-2 的 A2 pending 重放按事件**已断言的** rating 复算。
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone

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
    """受理语法内时刻 → tz-aware datetime, 统一 astimezone(UTC)。

    naive (无时区) 一律 ValueError 拒绝 —— G3-2 契约 A6: 无时区的时刻无法
    与水位线 W 做绝对瞬间比较, 静默当 UTC 等于伪造事实。原实现
    `dt.replace(tzinfo=utc)` 只补 tzinfo 不转换, 合法的 '12:00:00+08:00'
    会原样传给 fsrs 库并被其 UTC 硬校验抛 ValueError (§九登记缺陷①②)。
    """
    dt = datetime.fromisoformat(str(s).strip().replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError(f"naive 时刻拒收 (无法与水位线比较, 请带时区重传): {s!r}")
    return dt.astimezone(timezone.utc)


def _whole_second(dt: datetime) -> datetime:
    """截掉小数秒 (向零取整, 即丢弃小数部分) —— A5 整秒口径。

    W 与事件 review_time 都只有秒级精度; 原实现只在 _iso() 输出时截,
    写出的 W 与调用方手里的 ts 差一个小数秒, A5 "同一瞬间" 不成立。
    """
    return dt.replace(microsecond=0)


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


_ONE_MINUTE = timedelta(minutes=1)


def _steps_to_minutes(steps) -> list[int]:
    """timedelta 序列 → 整分钟列表。非整分钟步长直接抛错, 不静默截断。

    用 timedelta 整除/取余 (内部纯整数微秒), 不走 total_seconds() 浮点 ——
    json.dumps 把 1.0 写成 "1.0"、1 写成 "1", hash 会分叉。
    """
    minutes: list[int] = []
    for td in steps:
        if td % _ONE_MINUTE != timedelta(0):
            raise ValueError(f"学习步长 {td!r} 非整分钟, 无法用 *_steps_minutes 表达")
        minutes.append(td // _ONE_MINUTE)
    return minutes


def scheduler_identity(sched) -> tuple[str, str]:
    """从活体 fsrs Scheduler 反推 (library_version, params_hash)。

    params_hash 口径与 backend/scripts/generate_fsrs_golden_vectors.py::
    params_hash() 逐字一致 (sha256 of canonical JSON, 六键形状), 零硬编码 ——
    golden manifest 真值相等是被**复算证明**的, 不是被声明的。库/参数升级时
    此处如实返回新身份, 与 manifest 的相等性检查由校验器负责。
    """
    from importlib.metadata import version as _pkg_version

    config = {
        "parameters": [float(p) for p in sched.parameters],
        "desired_retention": float(sched.desired_retention),
        "learning_steps_minutes": _steps_to_minutes(sched.learning_steps),
        "relearning_steps_minutes": _steps_to_minutes(sched.relearning_steps),
        "maximum_interval": int(sched.maximum_interval),
        "enable_fuzzing": bool(sched.enable_fuzzing),
    }
    canonical = json.dumps(config, sort_keys=True, separators=(",", ":"))
    return _pkg_version("fsrs"), hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def fields_from_frontmatter(fm: str) -> dict:
    """从 frontmatter 文本抽 fsrs_* 字段 (纯 stdlib, 读侧同款正则)。"""
    out = {}
    for key in FIELD_ORDER:
        m = re.search(rf'^{key}:\s*"?([^"\n]+?)"?\s*$', fm, re.M)
        if m:
            out[key] = m.group(1).strip()
    return out


def _legacy_param(v):
    """legacy state:0 伴生参数哨兵归一: 空/null/~/0/0.0/不可解析 → None。"""
    if v in (None, ""):
        return None
    s = str(v).strip().lower()
    if s in ("null", "none", "~"):
        return None
    try:
        return None if float(s) == 0.0 else v
    except ValueError:
        return None


#: A7 review 域上界 (schema v1 §6.2): review_time 与 W 同域同界且均须严格小于。
#: 调度会在其上叠加 interval, A3 还要 +1s —— 逼近上界时新事件不可写, fail-closed。
_REVIEW_MAX = datetime(9000, 1, 1, tzinfo=timezone.utc)


def review(fields: dict, grade_norm: float, abandoned: bool, ts: str, rating: int | None = None) -> dict:
    """一次评分 → 新 fsrs_* 字段 (需要 fsrs 可导入)。

    G3-2 时刻语义 (schema v1 §6.2 A3/A5/A6):
      - ts 归一 UTC 整秒后作为本次 review 时刻 (写出的 fsrs_last_review 与
        返回的 review_time 逐字相同);
      - 若当前 frontmatter 有 W (fsrs_last_review) 且本次时刻 ≤ W, 推进到
        W+1s 再写 (A3 等时唯一口径: 推进不拒绝);
      - rating 可显式指定 (A2 pending 重放按事件已断言的 rating 复算),
        缺省按 grade_norm+abandoned 推导; abandoned 恒为 1 (弃答一票否决)。
    """
    from fsrs import Card, Rating, Scheduler, State

    now = _whole_second(_aware(ts))
    if now >= _REVIEW_MAX:
        raise ValueError(f"review 时刻 {ts!r} 越出 A7 review 域上界 (须严格小于 {_iso(_REVIEW_MAX)})")
    if rating is not None:
        # 严格 int (Codex round-1 MEDIUM): int(1.5)==1 会把非法 pending 行
        # 静默应用; §6.1 冻结 rating 为真 int 1-4, bool 伪装同样拒绝。
        # abandoned 自洽 (round-2 HIGH): 显式 rating 无论 abandoned 与否都先
        # 验证类型 — abandoned 分支不再绕过类型门; 弃答恒 1 (§6.1), 显式给
        # 非 1 的 rating 与 abandoned=true 互斥。
        if isinstance(rating, bool) or not isinstance(rating, int) or rating not in (1, 2, 3, 4):
            raise ValueError(f"显式 rating 必须为 int 1-4, 实为 {rating!r}")
        if abandoned and rating != 1:
            raise ValueError(f"abandoned=true 时 rating 恒为 1 (弃答一票否决), 实为 {rating!r}")
    if abandoned:
        used_rating = 1
    elif rating is not None:
        used_rating = rating
    else:
        used_rating = rating_from_grade(grade_norm, abandoned)

    sched = Scheduler(enable_fuzzing=False)
    if fields.get("fsrs_due"):
        step = fields.get("fsrs_step")
        stability = fields.get("fsrs_stability")
        difficulty = fields.get("fsrs_difficulty")
        raw_state = int(fields.get("fsrs_state", 1))
        if raw_state == 0:
            # legacy New 形状字段级迁移 (CARD-C3, roundtrip 显式例外):
            # state 0→Learning(1) — py-fsrs 4+ 无 New 态, State(0) 抛
            # ValueError; 伴生哨兵 0/0.0/null → None (0.0 会进 v6 稳定度
            # 幂运算抛 ZeroDivisionError); step 兜底 0 (Learning 首步)。
            raw_state = 1
            stability = _legacy_param(stability)
            difficulty = _legacy_param(difficulty)
            step = _legacy_param(step) or 0
        card = Card(
            state=State(raw_state),
            step=int(step) if step not in (None, "") else None,
            stability=float(stability) if stability else None,
            difficulty=float(difficulty) if difficulty else None,
            due=_aware(fields["fsrs_due"]),
            last_review=_aware(fields["fsrs_last_review"]) if fields.get("fsrs_last_review") else None,
        )
        # A3 等时消解: 时刻 ≤ W → 推进 W+1s (写侧唯一口径, 禁止拒绝丢评分)。
        # W 与 review_time 同域同界, W+1s 越出 A7 上界 ⇒ 后继不可写, fail-closed。
        if fields.get("fsrs_last_review"):
            w = _whole_second(_aware(fields["fsrs_last_review"]))
            if now <= w:
                bumped = w + timedelta(seconds=1)
                if bumped >= _REVIEW_MAX:
                    raise ValueError(f"A3 推进 W+1s 越出 A7 上界 (W={_iso(w)}) — 后继事件不可写")
                now = bumped
    else:
        card = Card(due=now)  # 无字段 = New 卡即刻到期 (零迁移)

    card, _log = sched.review_card(
        card, Rating(used_rating), review_datetime=now
    )
    lib_ver, p_hash = scheduler_identity(sched)
    out = {
        "fsrs_due": _iso(card.due),
        "fsrs_state": int(card.state),
        "fsrs_step": card.step if card.step is not None else "",
        "fsrs_stability": round(card.stability, 4) if card.stability is not None else "",
        "fsrs_difficulty": round(card.difficulty, 4) if card.difficulty is not None else "",
        "fsrs_last_review": _iso(now),
        # G3-2 加性输出: 调用方必须把 review_time 原样写进事件 payload
        # (与 effective_at 同一瞬间), 不要自己另算一份。
        "review_time": _iso(now),
        "rating": used_rating,
        "fsrs_library_version": lib_ver,
        "fsrs_params_hash": p_hash,
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
    try:
        out = review(
            fields_from_frontmatter(p.get("fm", "")),
            float(p.get("grade_norm", 0.0)),
            bool(p.get("abandoned")),
            p["ts"],
            rating=p.get("rating"),
        )
    except ValueError as e:
        # G3-2: naive/越界/非法 rating 等输入缺陷 —— 拒绝并 stdout 明说,
        # 不静默降级。exit 2 = 输入错误 (区别于 3 = fsrs 不可用)。
        print(json.dumps({"error": f"invalid_input — {e}"}, ensure_ascii=False))
        return 2
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
