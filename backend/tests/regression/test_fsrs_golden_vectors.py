"""FSRS golden vectors 防依赖升级漂移门 (CARD-G3-4, BATCH-2026-08-28-第五批)。

锁七件事 (Codex round-1 整改后):
  1. 库版本钉死 — 安装版 != manifest.library_version 即红 (升级必先重冻结);
  2. requirements 精确钉版 — 逐行严格解析, 松绑/加 marker/.post 后缀均红;
  3. 默认参数/枚举面 — DEFAULT_PARAMETERS 或 Rating/State 值域漂移即红;
  4. manifest 完整性 — params_hash 与 scheduler_config 不自洽 (篡改任一) 即红;
  5. manifest 元数据字面锁 — algorithm/timezone/base_datetime/card_id/容差上限
     以测试内字面值二次锁定, manifest 单方篡改即红 (Codex round-1 反例整改);
  6. 矩阵结构 — 恰好 5 场景 × 4 评分、20 唯一 id、每场景前态字面锁、
     retrievability 恰 3 点 (Codex round-1 反例: 结构可篡改后全绿);
  7. 调度行为 — 20 条冻结向量重放 (含最终评分前 state 断言) + 3 条
     retrievability 曲线点, 偏离即红。

真实库验收铁律 (计划书 G3): 直接消费真实 fsrs 库 (Card/Rating/Scheduler/
State), 不 mock 不 FakeCard; 另断言生产模块 fsrs_manager.FSRS_AVAILABLE=True
(生产面真实库在位) — 注: fsrs_manager 无 __all__ re-export 契约, 本测试不再
宣称"只消费其公开接口", 库对象一律直接从 fsrs 导入 (Codex round-1 口径整改);
fsrs_manager.py 本体 (in-flight D4 锁定) 零接触。

golden 基线: fsrs_golden_manifest.json + fsrs_golden_vectors.json
(生成器 backend/scripts/generate_fsrs_golden_vectors.py — 仅评审后重冻结时重跑)。

⚠️ CI 接入移交 (Codex round-1 BLOCKER, 本卡不可修): .github/workflows/ 为
第五批 S8 车道独占且 test.yml 零改动纪律 — 本文件与
test_learning_events_schema_contract.py 加入 test.yml 显式清单的 micro-patch
移交主 session 合并后处理 (登记于验收单)。
"""

import hashlib
import json
import math
import sys
from datetime import datetime, timedelta
from importlib.metadata import version as pkg_version
from pathlib import Path

from fsrs import Card, Rating, Scheduler, State

# 生产模块真实库在位断言专用 (D4 锁定文件, 只读其模块级布尔)
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "lib"))
from memory.temporal.fsrs_manager import FSRS_AVAILABLE  # noqa: E402

HERE = Path(__file__).resolve().parent
WT = Path(__file__).resolve().parents[3]
MANIFEST = json.loads((HERE / "fsrs_golden_manifest.json").read_text(encoding="utf-8"))
GOLDEN = json.loads((HERE / "fsrs_golden_vectors.json").read_text(encoding="utf-8"))

FLOAT_REL = MANIFEST["comparison_tolerance"]["float_rel"]
FLOAT_ABS = MANIFEST["comparison_tolerance"]["float_abs"]
RATING_BY_NAME = {"again": Rating.Again, "hard": Rating.Hard, "good": Rating.Good, "easy": Rating.Easy}

#: 矩阵结构字面锁 (门 6): 场景 → (最终评分前期望 State, prefix rating 序列)
#: prefix skeleton 锁死每个场景的真实前缀 — Codex round-2 反例: 只锁前态时
#: new_card 可伪装成 learning_step2 (同为 state 1) 而全绿
EXPECTED_SCENARIO = {
    "new_card": (1, ()),
    "learning_step2": (1, ("good",)),
    "review_ontime": (2, ("good", "good")),
    "review_overdue_30d": (2, ("good", "good")),
    "relearning": (3, ("good", "good", "again")),
}
EXPECTED_SCENARIO_STATE = {k: v[0] for k, v in EXPECTED_SCENARIO.items()}
RATING_NAMES = ("again", "hard", "good", "easy")
#: 场景 → 最终评分时刻相对前缀末态 due 的偏移 (天); review_overdue_30d 是唯一逾期场景
EXPECTED_FINAL_OFFSET_DAYS = {
    "new_card": 0,
    "learning_step2": 0,
    "review_ontime": 0,
    "review_overdue_30d": 30,
    "relearning": 0,
}


def _build_scheduler() -> Scheduler:
    cfg = MANIFEST["scheduler_config"]
    return Scheduler(
        parameters=cfg["parameters"],
        desired_retention=cfg["desired_retention"],
        learning_steps=[timedelta(minutes=m) for m in cfg["learning_steps_minutes"]],
        relearning_steps=[timedelta(minutes=m) for m in cfg["relearning_steps_minutes"]],
        maximum_interval=cfg["maximum_interval"],
        enable_fuzzing=cfg["enable_fuzzing"],
    )


def _replay(steps: list[dict]) -> "Card":
    scheduler = _build_scheduler()
    card = Card(
        card_id=MANIFEST["card_id"],
        due=datetime.fromisoformat(MANIFEST["base_datetime"]),
    )
    for step in steps:
        card, _ = scheduler.review_card(card, RATING_BY_NAME[step["rating"]], datetime.fromisoformat(step["review_at"]))
    return card


def _close(actual: float | None, expected: float | None) -> bool:
    if actual is None or expected is None:
        return actual is expected
    return math.isclose(actual, expected, rel_tol=FLOAT_REL, abs_tol=FLOAT_ABS)


# ── 1. 库版本钉死 ──


def test_real_library_present_not_fallback():
    assert FSRS_AVAILABLE, "生产模块 fsrs_manager 未加载真实 fsrs 库 — fallback 不得参与验收"


def test_installed_version_matches_frozen_manifest():
    installed = pkg_version("fsrs")
    assert installed == MANIFEST["library_version"], (
        f"fsrs 安装版 {installed} != golden 冻结版 {MANIFEST['library_version']} — "
        "依赖升级检测: 须重跑 generate_fsrs_golden_vectors.py 评审重冻结基线"
    )


# ── 2. requirements 精确钉版 (严格逐行解析, 非正则前缀匹配) ──


def _fsrs_requirement_lines(req: Path) -> list[str]:
    """去注释后, 包名恰为 fsrs 的 requirement 行 (不吞 fsrs-xxx 等他包)。"""
    found = []
    for raw in req.read_text(encoding="utf-8").splitlines():
        spec = raw.split("#", 1)[0].strip()
        if not spec:
            continue
        name = spec
        for sep in "<>=!~[;":
            name = name.split(sep, 1)[0]
        if name.strip().lower() == "fsrs":
            found.append(spec)
    return found


def test_requirements_pin_exact_version():
    """Codex round-1 MEDIUM: 原正则 ^fsrs==6.3.1\\b 会放过 .post1/环境 marker。
    严格判据: 每份 requirements 恰好一行 fsrs 且整行 == fsrs==<冻结版>。"""
    expected = [f"fsrs=={MANIFEST['library_version']}"]
    for req in (WT / "requirements.txt", WT / "backend" / "requirements.txt"):
        assert _fsrs_requirement_lines(req) == expected, (
            f"{req} 的 fsrs 钉版行 {_fsrs_requirement_lines(req)} != {expected} — 禁止范围约束/.post 后缀/marker 回潮"
        )


# ── 3. 默认参数与枚举面 ──


def test_library_default_parameters_unchanged():
    from fsrs.scheduler import DEFAULT_PARAMETERS

    frozen = MANIFEST["scheduler_config"]["parameters"]
    assert len(DEFAULT_PARAMETERS) == MANIFEST["parameter_count"]
    assert [float(p) for p in DEFAULT_PARAMETERS] == frozen, (
        "fsrs DEFAULT_PARAMETERS 与冻结值漂移 — 算法权重变更, 须评审重冻结"
    )


def test_rating_and_state_value_surface_frozen():
    assert {name: int(RATING_BY_NAME[name]) for name in RATING_BY_NAME} == MANIFEST["rating_values"]
    assert {s.name: int(s.value) for s in State} == MANIFEST["state_values"]


# ── 4. manifest 完整性 (params_hash 自洽) ──


def test_params_hash_integrity():
    canonical = json.dumps(MANIFEST["scheduler_config"], sort_keys=True, separators=(",", ":"))
    recomputed = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    assert recomputed == MANIFEST["params_hash"], "params_hash 与 scheduler_config 不自洽 — manifest 被篡改或参数漂移"
    assert GOLDEN["params_hash"] == MANIFEST["params_hash"], "vectors 文件与 manifest 脱钩"
    assert GOLDEN["library_version"] == MANIFEST["library_version"]


# ── 5. manifest 元数据字面锁 (Codex round-1: algorithm='arbitrary' 曾全绿) ──


def test_manifest_metadata_frozen():
    assert MANIFEST["manifest_version"] == 1
    assert MANIFEST["library"] == "fsrs"
    assert MANIFEST["algorithm"] == "FSRS-6 (py-fsrs 21-parameter scheduler)"
    assert MANIFEST["timezone"] == "UTC"
    assert MANIFEST["base_datetime"] == "2026-01-01T00:00:00+00:00"
    assert MANIFEST["card_id"] == 20260101000000
    assert MANIFEST["parameter_count"] == 21


def test_tolerance_ceiling_locked():
    """容差只许更严不许放宽 — manifest 单方把 rel 调成 1e-3 即红。"""
    assert 0 < MANIFEST["comparison_tolerance"]["float_rel"] <= 1e-9
    assert 0 < MANIFEST["comparison_tolerance"]["float_abs"] <= 1e-12


# ── 6. 矩阵结构 (Codex round-1: 重复/缺格/空 retrievability 曾全绿) ──


def test_matrix_structure_frozen():
    vectors = GOLDEN["vectors"]
    assert len(vectors) == 20, "5 关键态 × 4 评分 = 20 条, 增删须评审重冻结"

    ids = [v["id"] for v in vectors]
    assert len(set(ids)) == 20, "向量 id 必须全唯一 (重复 = 有格子被顶掉)"

    # 组合全集按**真实 steps 的最终 rating**取, 不从 id 后缀推导
    # (Codex round-2 HIGH: 把 good 行的 steps 改成 hard 曾全绿)
    expected_combos = {(s, r) for s in EXPECTED_SCENARIO for r in RATING_NAMES}
    actual_combos = {(v["scenario"], v["steps"][-1]["rating"]) for v in vectors}
    assert actual_combos == expected_combos, f"场景×真实评分组合缺格/多格: 差集 {expected_combos ^ actual_combos}"

    for v in vectors:
        scenario = v["scenario"]
        expected_state, expected_prefix = EXPECTED_SCENARIO[scenario]
        final_rating = v["steps"][-1]["rating"]
        assert v["id"] == f"{scenario}__{final_rating}", (
            f"{v['id']}: id 必须 == scenario__真实最终rating (实为 {scenario}__{final_rating})"
        )
        assert v["state_before_final_review"] == expected_state, (
            f"{v['id']}: 声明前态 {v['state_before_final_review']} != 字面锁 {expected_state}"
        )
        actual_prefix = tuple(s["rating"] for s in v["steps"][:-1])
        assert actual_prefix == expected_prefix, (
            f"{v['id']}: 前缀 rating 序列 {actual_prefix} != 场景 skeleton {expected_prefix}"
        )
        # 时刻 skeleton: 前缀首步恒为 base_datetime; 逾期场景的最终时刻必须
        # 比前缀末态 due 晚整 30 天, 其余场景恰等于 due (= 准时)
        times = [datetime.fromisoformat(s["review_at"]) for s in v["steps"]]
        assert times == sorted(times), f"{v['id']}: 复习时刻必须非降序"
        assert times[0] == datetime.fromisoformat(MANIFEST["base_datetime"]), (
            f"{v['id']}: 首步时刻必须为 manifest.base_datetime"
        )
        prefix_card = _replay(v["steps"][:-1])
        expected_final_at = prefix_card.due + timedelta(days=EXPECTED_FINAL_OFFSET_DAYS[scenario])
        assert times[-1] == expected_final_at, (
            f"{v['id']}: 最终复习时刻 {times[-1].isoformat()} != 前缀末态 due"
            f"+{EXPECTED_FINAL_OFFSET_DAYS[scenario]}d ({expected_final_at.isoformat()})"
        )

    points = GOLDEN["retrievability"]["at"]
    assert len(points) == 3, "retrievability 曲线恰 3 点 (due/+7d/+30d)"
    times = [datetime.fromisoformat(p["current_datetime"]) for p in points]
    assert times == sorted(times) and len(set(times)) == 3


# ── 7. 调度行为向量重放 (含最终评分前 state 实测断言) ──


def test_all_golden_vectors_replay_exact():
    failures = []
    scheduler = _build_scheduler()
    for vector in GOLDEN["vectors"]:
        prefix, final = vector["steps"][:-1], vector["steps"][-1]
        card = _replay(prefix)
        if int(card.state) != vector["state_before_final_review"]:
            failures.append(f"{vector['id']}: 重放前态 {int(card.state)} != 声明 {vector['state_before_final_review']}")
            continue
        card, _ = scheduler.review_card(
            card, RATING_BY_NAME[final["rating"]], datetime.fromisoformat(final["review_at"])
        )
        expected = vector["expected"]
        checks = {
            "stability": _close(card.stability, expected["stability"]),
            "difficulty": _close(card.difficulty, expected["difficulty"]),
            "due": card.due.isoformat() == expected["due"],
            "last_review": (card.last_review.isoformat() if card.last_review else None) == expected["last_review"],
            "state": int(card.state) == expected["state"],
            "step": card.step == expected["step"],
        }
        bad = [k for k, ok in checks.items() if not ok]
        if bad:
            failures.append(f"{vector['id']}: 偏离字段 {bad}")
    assert not failures, "golden 向量重放偏离 (依赖漂移?):\n" + "\n".join(failures)


def test_retrievability_curve_matches_golden():
    golden = GOLDEN["retrievability"]
    card = _replay(golden["steps"])
    scheduler = _build_scheduler()
    for point in golden["at"]:
        actual = scheduler.get_card_retrievability(card, datetime.fromisoformat(point["current_datetime"]))
        assert _close(actual, point["expected"]), (
            f"retrievability@{point['current_datetime']}: {actual} != {point['expected']}"
        )
