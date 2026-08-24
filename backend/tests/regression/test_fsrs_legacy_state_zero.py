# CARD-C3 回归锁定 (BATCH-2026-08-25-跨vault与收束)
# [Source: _bmad-output/implementation-artifacts/goal-cards/2026-08-25-第二批小goal卡-跨vault与收束.md#CARD-C3]
"""legacy state:0 反序列化回归测试。

当前 py-fsrs 6.x 的 State 枚举只有 Learning(1)/Review(2)/Relearning(3)，
`State(0)` 抛 ValueError: "0 is not a valid State"。legacy 实现（官方
py-fsrs v3 及本仓库的 FSRS_AVAILABLE=False fallback）会存出 New(0) +
stability/difficulty 0.0 哨兵的旧形状记录。

修复语义（对 CARD-A1 严格 roundtrip 原则的显式例外, Codex C3 审查 BLOCKER
后升级为字段级迁移）:
  - 读取层 (deserialize_card): legacy state:0 → State.Learning(1)（官方
    语义: Learning == "new card being studied for the first time"）；
    canonical New 形状的参数哨兵 stability/difficulty 0.0 → None——
    v6 调度器只认 None 为未初始化, 0.0 会进稳定度幂运算抛
    ZeroDivisionError（Codex BLOCKER 实测）。正参数(矛盾形状)保留并
    logger.warning, 不猜成 Review；
  - 写侧 (serialize_card / card_to_state / CardState / fallback
    create_card): 任何路径不得再产出 state=0；
  - fsrs_bridge.review: frontmatter fsrs_state:0 分支同款字段级迁移
    （伴生 0/0.0/null 哨兵归 None, step 兜底 0）, 不抛且产出 >= 1。

注意本文件独立于 test_fsrs_new_card_none_serialization.py（A1 锁的是
新卡 None 语义, 与本卡的 legacy 0 迁移无关, 禁混）。
"""

import json
import subprocess
import sys
from pathlib import Path

# Add backend/lib to path for imports (同 tests/regression 既有约定)
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))

from memory.temporal.fsrs_manager import (  # noqa: E402
    FSRS_AVAILABLE,
    CardState,
    FSRSManager,
)

# fsrs_bridge 与 test_fsrs_bridge.py 同款路径注入
_WT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_WT / "canvas-vault" / ".claude" / "scripts"))

import fsrs_bridge as fb  # noqa: E402

NOW = "2026-08-25T01:00:00Z"

# 官方 py-fsrs v3 / 本仓库 fallback 都会产出的 canonical legacy New 形状
CANONICAL_LEGACY_NEW = {
    "due": "2026-01-01T00:00:00+00:00",
    "stability": 0.0,
    "difficulty": 0.0,
    "state": 0,
    "reps": 0,
    "lapses": 0,
    "last_review": None,
}


def test_real_fsrs_library_is_installed():
    """门禁 fail-closed（同 A1 约定）: 缺真实库必须红，禁 skipif 假绿。"""
    assert FSRS_AVAILABLE, "真实 py-fsrs 未安装 — 本回归套件不允许跳过"


class _HeadlessCard:
    """无 state/reps/lapses/last_review 属性的残缺对象，逼出写侧 else 兜底。"""

    due = None
    stability = None
    difficulty = None


# ── 读取层: canonical legacy New 全链（deserialize → 真实复习 → serialize） ──


def test_canonical_legacy_new_deserialize_review_serialize_full_chain():
    """Codex BLOCKER 锁定: 仅迁 state 不迁参数哨兵 → 真实复习
    ZeroDivisionError('zero to a negative power')。全链必须走通。"""
    from fsrs import State

    manager = FSRSManager()
    card = manager.deserialize_card(json.dumps(CANONICAL_LEGACY_NEW))
    assert card.state == State.Learning
    assert card.stability is None, "legacy 哨兵 0.0 必须归 None（v6 未初始化语义）"
    assert card.difficulty is None

    reviewed, _log = manager.review_card(card, 3)  # 真实 Scheduler, Good
    assert reviewed.stability is not None and reviewed.stability > 0

    rewritten = json.loads(manager.serialize_card(reviewed))
    assert rewritten["state"] != 0
    assert rewritten["stability"] > 0


def test_legacy_zero_contradictory_shape_preserves_params_and_warns(caplog):
    """state:0 但带正参数的矛盾形状: 保留正参数（合法可复习）+ 显式告警，
    不猜成 Review（Codex 审查建议）。"""
    import logging

    from fsrs import State

    manager = FSRSManager()
    with caplog.at_level(logging.WARNING):
        card = manager.deserialize_card(
            json.dumps(
                {
                    "due": "2026-01-01T00:00:00+00:00",
                    "stability": 3.5,
                    "difficulty": 5.0,
                    "state": 0,
                    "reps": 2,
                    "lapses": 1,
                    "last_review": "2025-12-25T00:00:00+00:00",
                }
            )
        )
    assert card.state == State.Learning, "矛盾形状不猜 Review, 仍映射 Learning"
    assert card.stability == 3.5, "正参数不得被哨兵归一误伤"
    assert card.difficulty == 5.0
    assert card.reps == 2 and card.lapses == 1
    assert card.due.isoformat() == "2026-01-01T00:00:00+00:00"
    assert card.last_review.isoformat() == "2025-12-25T00:00:00+00:00"
    assert any("state:0" in r.message for r in caplog.records), "矛盾形状必须告警"

    reviewed, _log = manager.review_card(card, 3)  # 带正参数也必须能真实复习
    assert reviewed.stability is not None


def test_deserialize_valid_states_unchanged():
    """非 0 状态严格 roundtrip 不受例外影响（A1 原则仍然成立）。"""
    from fsrs import State

    manager = FSRSManager()
    for raw, expected in [(1, State.Learning), (2, State.Review), (3, State.Relearning)]:
        card = manager.deserialize_card(json.dumps({"state": raw, "stability": 0.0}))
        assert card.state == expected
        # 哨兵归一是 legacy state:0 专属例外, 不得外溢到合法状态
        assert card.stability == 0.0


def test_legacy_zero_roundtrip_rewrites_as_learning():
    """legacy 0 读入后再序列化，落盘值必须是 1——雷只拆一次。"""
    manager = FSRSManager()
    card = manager.deserialize_card(json.dumps({"state": 0, "reps": 2}))
    rewritten = json.loads(manager.serialize_card(card))
    assert rewritten["state"] == 1
    assert rewritten["reps"] == 2


# ── 写侧: serialize_card / card_to_state / CardState 永不写 state=0 ──


def test_serialize_card_fallback_never_writes_state_zero():
    manager = FSRSManager()
    card_dict = json.loads(manager.serialize_card(_HeadlessCard()))
    assert card_dict["state"] != 0, "写侧兜底不得产出 v6 非法的 state=0"
    assert card_dict["state"] == 1


def test_card_to_state_fallback_never_writes_state_zero():
    manager = FSRSManager()
    state = manager.card_to_state(_HeadlessCard(), "概念X", "board.canvas")
    assert state.state != 0, "写侧兜底不得产出 v6 非法的 state=0"
    assert state.state == 1


def test_real_new_card_serializes_state_one():
    """真实 fsrs 6.x 新卡本身就是 Learning(1)——主路径无 0 可写。"""
    manager = FSRSManager()
    card_dict = json.loads(manager.serialize_card(manager.create_card()))
    assert card_dict["state"] == 1


def test_cardstate_dataclass_never_defaults_or_reads_zero():
    """Codex MEDIUM: CardState 公共序列器默认值与 from_dict 读侧同规则。"""
    assert CardState(concept="c", canvas_file="f.canvas").state == 1
    restored = CardState.from_dict(
        {"concept": "c", "canvas_file": "f.canvas", "state": 0}
    )
    assert restored.state == 1
    assert CardState.from_dict({"concept": "c", "canvas_file": "f.canvas"}).state == 1


# ── FSRS_AVAILABLE=False fallback 分支: 不再持续制造 state:0 (Codex HIGH-2) ──


def test_fallback_branch_never_produces_state_zero_in_isolated_process():
    """屏蔽 fsrs import 的隔离子进程实测 fallback 分支:
    create_card / serialize / deserialize(0) / card_to_state 全部无 0。"""
    probe = r"""
import json, sys
sys.modules["fsrs"] = None  # 强制 ImportError → FSRS_AVAILABLE=False
sys.path.insert(0, %r)
from memory.temporal.fsrs_manager import FSRS_AVAILABLE, FSRSManager
assert not FSRS_AVAILABLE
m = FSRSManager()
created = m.create_card()
assert created["state"] != 0, f"fallback create_card 产出 state={created['state']}"
# 既有缺陷(超 C3 范围): fallback serialize 不支持 datetime due — 置 None 绕过
created["due"] = None
serialized = json.loads(m.serialize_card(created))
assert serialized["state"] != 0
legacy = m.deserialize_card('{"state": 0, "stability": 0.0, "reps": 2}')
assert legacy["state"] == 1, f"fallback 读侧未迁移: {legacy['state']}"
assert legacy["reps"] == 2
cs = m.card_to_state({"stability": 1.0}, "c", "f.canvas")
assert cs.state == 1, f"fallback card_to_state 兜底产出 {cs.state}"
assert json.loads(cs.card_data).get("state", 1) != 0
print("FALLBACK-OK")
""" % str(Path(__file__).parent.parent.parent / "lib")
    r = subprocess.run(
        [sys.executable, "-c", probe], capture_output=True, text=True, timeout=60
    )
    assert r.returncode == 0, r.stderr[-800:]
    assert "FALLBACK-OK" in r.stdout


# ── fsrs_bridge: frontmatter fsrs_state:0 字段级防御映射 ──


def test_bridge_legacy_state_zero_does_not_raise_and_outputs_valid_state():
    out = fb.review(
        {"fsrs_due": "2026-08-24T00:00:00Z", "fsrs_state": "0"},
        2.0 / 3,
        False,
        NOW,
    )
    assert int(out["fsrs_state"]) >= 1, "复习产出必须落在 v6 合法状态"
    assert out["fsrs_last_review"] == NOW


def test_bridge_legacy_state_zero_behaves_like_learning():
    """防御映射语义 = Learning：与显式 fsrs_state:1 的复习产出一致。"""
    fields = {"fsrs_due": "2026-08-24T00:00:00Z"}
    out_zero = fb.review({**fields, "fsrs_state": "0"}, 2.0 / 3, False, NOW)
    out_one = fb.review({**fields, "fsrs_state": "1"}, 2.0 / 3, False, NOW)
    assert out_zero == out_one


def test_bridge_legacy_full_frontmatter_zero_and_null_params():
    """Codex HIGH-1 锁定: 完整 legacy frontmatter 的伴生哨兵字段——
    0/0.0 → 真实调度 ZeroDivisionError；null → float()/int() ValueError。
    state:0 分支必须字段级归一后走通真实复习。"""
    fm = (
        "fsrs_due: 2026-08-24T00:00:00Z\n"
        "fsrs_state: 0\n"
        "fsrs_step: null\n"
        "fsrs_stability: 0.0\n"
        "fsrs_difficulty: null\n"
        "fsrs_last_review: 2026-08-20T00:00:00Z"
    )
    out = fb.review(fb.fields_from_frontmatter(fm), 2.0 / 3, False, NOW)
    assert int(out["fsrs_state"]) >= 1
    assert float(out["fsrs_stability"]) > 0
    assert out["fsrs_due"].endswith("Z")


def test_bridge_legacy_zero_state_with_positive_params_kept():
    """矛盾形状（state:0 + 正 stability）: 正参数保留参与真实调度。"""
    fm = (
        "fsrs_due: 2026-08-24T00:00:00Z\n"
        "fsrs_state: 0\n"
        "fsrs_stability: 3.5\n"
        "fsrs_difficulty: 5.0"
    )
    out = fb.review(fb.fields_from_frontmatter(fm), 2.0 / 3, False, NOW)
    assert int(out["fsrs_state"]) >= 1
    assert float(out["fsrs_stability"]) > 0
