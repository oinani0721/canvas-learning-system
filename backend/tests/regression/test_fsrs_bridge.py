"""fsrs_bridge 契约锁定 (FSRS-V2-2026-07-30, [Decision-FSRS-1/2])。

锁四件事: 映射边界 / New卡零迁移语义 / F2 间隔扩张与 F3 当日重学 /
stdlib 入口 re-exec 降级路径。
"""

import json
import subprocess
import sys
from pathlib import Path

WT = Path(__file__).resolve().parents[3]
BRIDGE = WT / "canvas-vault" / ".claude" / "scripts" / "fsrs_bridge.py"
sys.path.insert(0, str(BRIDGE.parent))

import fsrs_bridge as fb  # noqa: E402

NOW = "2026-07-30T01:00:00Z"


# ── [Decision-FSRS-1] 映射边界 ──


def test_rating_mapping_boundaries():
    assert fb.rating_from_grade(1.0, abandoned=True) == 1, "弃答一票否决 Again"
    assert fb.rating_from_grade(0.0, False) == 1  # grade 1.0
    assert fb.rating_from_grade(0.1, False) == 1  # 1.3 → Again
    assert fb.rating_from_grade(0.2, False) == 2  # 1.6 → Hard
    assert fb.rating_from_grade(1.0 / 3, False) == 2  # 2.0 → Hard
    assert fb.rating_from_grade(0.5, False) == 3  # 2.5 边界 → Good
    assert fb.rating_from_grade(2.0 / 3, False) == 3  # 3.0 → Good
    assert fb.rating_from_grade(0.84, False) == 4  # 3.52 → Easy
    assert fb.rating_from_grade(1.0, False) == 4
    assert fb.rating_from_grade(9.9, False) == 4, "越界钳制"


# ── [Decision-FSRS-2] New 卡零迁移 + 调度行为 ──


def test_new_card_first_good_enters_learning_minutes():
    out = fb.review({}, 2.0 / 3, False, NOW)
    assert out["fsrs_state"] == 1 and out["fsrs_step"] == 1
    assert out["fsrs_due"] == "2026-07-30T01:10:00Z", "Learning 第二步 = +10 分钟"
    assert float(out["fsrs_stability"]) > 0 and float(out["fsrs_difficulty"]) > 0
    assert out["fsrs_last_review"] == NOW


def test_graduation_then_interval_expands_f2():
    """F2: Good 毕业进 Review 后, 连续 Good 的间隔单调拉长。"""
    out = fb.review({}, 2.0 / 3, False, NOW)
    out = fb.review(out, 2.0 / 3, False, out["fsrs_due"])
    assert out["fsrs_state"] == 2, "毕业进 Review"
    d1 = fb._aware(out["fsrs_due"]) - fb._aware(out["fsrs_last_review"])
    out2 = fb.review(out, 2.0 / 3, False, out["fsrs_due"])
    d2 = fb._aware(out2["fsrs_due"]) - fb._aware(out2["fsrs_last_review"])
    assert d1.days >= 1 and d2 > d1, f"间隔应扩张: {d1} → {d2}"


def test_again_relearning_same_day_f3():
    """F3: Review 态答 Again → Relearning, due = +10 分钟 (当日重学环)。"""
    out = fb.review({}, 2.0 / 3, False, NOW)
    out = fb.review(out, 2.0 / 3, False, out["fsrs_due"])  # 进 Review
    ts = out["fsrs_due"]
    out = fb.review(out, 0.0, True, ts)  # 弃答 → Again
    assert out["fsrs_state"] == 3
    assert (fb._aware(out["fsrs_due"]) - fb._aware(ts)).total_seconds() == 600


def test_easy_due_later_than_good_f5():
    """F5: 同一张 Review 卡, Easy 的下次到期晚于 Good。"""
    base = fb.review({}, 2.0 / 3, False, NOW)
    base = fb.review(base, 2.0 / 3, False, base["fsrs_due"])
    ts = base["fsrs_due"]
    good = fb.review(dict(base), 2.0 / 3, False, ts)
    easy = fb.review(dict(base), 1.0, False, ts)
    assert fb._aware(easy["fsrs_due"]) > fb._aware(good["fsrs_due"])


def test_fields_from_frontmatter_roundtrip():
    """frontmatter 序列化往返: 写出的字段能被解析并继续复习。"""
    out = fb.review({}, 0.5, False, NOW)
    fm = out["fm_block"]
    assert "fsrs_due:" in fm and "fsrs_last_review:" in fm
    parsed = fb.fields_from_frontmatter(fm)
    assert parsed["fsrs_due"] == out["fsrs_due"]
    out2 = fb.review(parsed, 0.5, False, out["fsrs_due"])
    assert fb._aware(out2["fsrs_due"]) > fb._aware(out["fsrs_due"])


def test_legacy_state_zero_frontmatter_defensive_mapping():
    """CARD-C3: legacy pre-v6 frontmatter fsrs_state: 0 → 防御映射 Learning(1)。

    py-fsrs 4+ 删除 New(0) 态, State(0) 抛 ValueError — 老记录必须在读侧
    映射, 复习产出落回合法状态 (>=1)。深度用例（伴生哨兵字段/矛盾形状）
    见 test_fsrs_legacy_state_zero.py。
    """
    fm = "fsrs_due: 2026-08-24T00:00:00Z\nfsrs_state: 0"
    out = fb.review(fb.fields_from_frontmatter(fm), 2.0 / 3, False, NOW)
    assert int(out["fsrs_state"]) >= 1
    assert out["fsrs_due"].endswith("Z")


def test_cli_legacy_state_zero_full_frontmatter_via_stdin():
    """CARD-C3: stdin CLI 形态下 legacy state:0 + 哨兵伴生字段全链走通
    (quiz-answer 实际调用路径, 含 re-exec)。"""
    fm = (
        "fsrs_due: 2026-08-24T00:00:00Z\n"
        "fsrs_state: 0\n"
        "fsrs_step: null\n"
        "fsrs_stability: 0.0\n"
        "fsrs_difficulty: null"
    )
    payload = json.dumps({"fm": fm, "grade_norm": 2.0 / 3, "abandoned": False, "ts": NOW})
    r = subprocess.run(["python3", str(BRIDGE)], input=payload, capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr[-500:]
    out = json.loads(r.stdout)
    assert int(out["fsrs_state"]) >= 1
    assert float(out["fsrs_stability"]) > 0


def test_cli_via_system_python_reexec_success():
    """stdlib 入口: 系统 python3 (可能无 fsrs) 经 stdin JSON 调用 → 自动
    re-exec venv python 返回结果 — quiz-answer 的实际调用形态。"""
    payload = json.dumps({"fm": "type: concept", "grade_norm": 0.5, "abandoned": False, "ts": NOW})
    r = subprocess.run(["python3", str(BRIDGE)], input=payload, capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr[-500:]
    out = json.loads(r.stdout)
    assert out["fsrs_due"].endswith("Z") and out["fsrs_state"] == 1


def test_cli_degradation_exit3_when_reexec_blocked():
    """Code-Review L2: 真降级路径锁定 — REEXEC 守卫置 1 (禁止再跳 venv) 且
    解释器无 fsrs 时, 必须诚实输出 error JSON + exit 3, 不得死循环/裸崩。"""
    import os as _os

    env = dict(_os.environ, FSRS_BRIDGE_REEXEC="1")
    payload = json.dumps({"fm": "", "grade_norm": 0.5, "abandoned": False, "ts": NOW})
    r = subprocess.run(
        ["python3", str(BRIDGE)],
        input=payload,
        capture_output=True,
        text=True,
        timeout=30,
        env=env,
    )
    if r.returncode == 0:
        import pytest

        pytest.skip("系统 python3 自带 fsrs, 降级路径在本机不可达")
    assert r.returncode == 3, r.stderr[-300:]
    assert "error" in json.loads(r.stdout)
