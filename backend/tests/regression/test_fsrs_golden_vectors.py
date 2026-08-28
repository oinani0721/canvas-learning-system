"""FSRS golden vectors 防依赖升级漂移门 (CARD-G3-4, BATCH-2026-08-28-第五批)。

十门 (逐轮 Codex 对抗后收敛):
  1. 库版本钉死 — 安装版 != manifest.library_version 即红 (升级必先重冻结);
  2. requirements 精确钉版 — 逐行严格解析, 松绑/加 marker/.post 后缀均红;
  3. 默认参数/枚举面 — DEFAULT_PARAMETERS 或 Rating/State 值域漂移即红;
  4. manifest 完整性 — params_hash 与 scheduler_config 不自洽即红;
  5. manifest 元数据字面锁 — algorithm/timezone/base_datetime/card_id (r1);
  6. manifest 键集 + 出处锁 — card/frozen_on/generator 与键集 (r4);
  7. scheduler_config 全字段字面锁 — 只锁 21 个 parameters 时 retention
     0.9→0.8 可自洽重算而全绿 (r3);
  8. 容差上限 + 子键集锁 — manifest 单方放宽即红 (r1/r5);
  9. 矩阵结构 — 5 场景 x 4 评分全组合 (按真实 steps rating 取)、20 唯一 id、
     id==scenario__rating、前缀 rating skeleton、**逐步时刻 skeleton**、
     向量/步/expected 键集与 description 字面锁、类型门 (r1-r5 反例累积);
 10. 行为重放 — 20 条向量逐步重放 (含前态实测) + retrievability 历史
     skeleton/逐步时刻/card 快照逐字段/采样点 due+(0,7,30) 真实复算 (r4/r5)。

⚠️ 覆盖范围诚实声明: 上述锁住的是**基线的语义与结构**; 未逐字节锁 JSON
文本本身 (格式化空白、键顺序等不影响语义的改动不会翻红)。

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

import pytest
from fsrs import Card, Rating, Scheduler, State

# 生产模块真实库在位断言专用 (D4 锁定文件, 只读其模块级布尔)
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "lib"))
from memory.temporal.fsrs_manager import FSRS_AVAILABLE  # noqa: E402

HERE = Path(__file__).resolve().parent
WT = Path(__file__).resolve().parents[3]


class _NonStandardGoldenJSON(ValueError):
    """金标文件出现重复键或 NaN/Infinity — 不同解析器会得到不同结果。"""


def _reject_dup(pairs):
    seen = set()
    for key, _ in pairs:
        if key in seen:
            raise _NonStandardGoldenJSON(
                f"金标 JSON 内重复键 {key!r}: last-wins 解析器读到后者、first-wins 读到前者 — "
                f"同一字节序列在不同解析器下产生相反结论, 防漂移门形同虚设"
            )
        seen.add(key)
    return dict(pairs)


def _load_golden(path: Path):
    """严格解析金标文件 (round-15, Codex 十四轮 HIGH)。

    默认 `json.loads` 对重复键 last-wins: 在 manifest 开头插入
    `"library_version": "999.0.0",` 并保留后面的真值, 原 13 门**全部照过**,
    而 first-wins 解析器读到 999.0.0。金标文件的全部意义是"同一字节序列人人
    读到同一事实", 故重复键与 NaN/Infinity 一律 fail-closed。
    """
    return json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=_reject_dup,
        parse_constant=lambda name: (_ for _ in ()).throw(_NonStandardGoldenJSON(f"金标 JSON 出现非标准常量 {name}")),
    )


MANIFEST = _load_golden(HERE / "fsrs_golden_manifest.json")
GOLDEN = _load_golden(HERE / "fsrs_golden_vectors.json")

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
#: 场景描述字面锁 (round-5 LOW: 改 description 曾全绿 — 描述是人读基线的一部分)
EXPECTED_SCENARIO_DESCRIPTION = {
    "new_card": "新卡首评 (state=Learning step=0, stability/difficulty=None)",
    "learning_step2": "Learning 第二步 (Good@T0 后 10 分钟到期复评)",
    "review_ontime": "Review 态准时复评 (两次 Good 毕业后恰于到期日复评)",
    "review_overdue_30d": "Review 态逾期 30 天复评",
    "relearning": "Relearning 态 (Review 后 Again 进重学, 10 分钟到期复评)",
}
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
    # round-15 (Codex 十四轮 MEDIUM): Python 里 True == 1, 故把 again 改成 true
    # 后上面的字典比较仍成立、13 门全绿 —— 值域锁必须连 JSON 类型一起锁
    for label, mapping in (("rating_values", MANIFEST["rating_values"]), ("state_values", MANIFEST["state_values"])):
        for name, value in mapping.items():
            assert type(value) is int, f"{label}.{name} 必须是 JSON 整数, 得到 {value!r} ({type(value).__name__})"


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


def test_manifest_key_set_and_provenance_frozen():
    """round-4 LOW: manifest 的 card/frozen_on/generator 与完整键集未锁 —
    出处字段被改写会让基线来源不可追溯。"""
    assert MANIFEST["card"] == "CARD-G3-4 (BATCH-2026-08-28-第五批)"
    assert MANIFEST["frozen_on"] == "2026-08-28"
    assert MANIFEST["generator"] == "backend/scripts/generate_fsrs_golden_vectors.py"
    assert set(MANIFEST.keys()) == {
        "algorithm",
        "base_datetime",
        "card",
        "card_id",
        "comparison_tolerance",
        "frozen_on",
        "generator",
        "library",
        "library_version",
        "manifest_version",
        "parameter_count",
        "params_hash",
        "rating_values",
        "scheduler_config",
        "state_values",
        "timezone",
    }, "manifest 键集变化 — 须评审重冻结"
    assert set(GOLDEN.keys()) == {"library_version", "params_hash", "retrievability", "vectors"}


def test_scheduler_config_non_parameter_fields_frozen():
    """Codex round-3 HIGH: 只锁 21 个 parameters 时, 把 desired_retention
    0.9→0.8 并重算 manifest/vectors/hash 可自洽伪装 (11 passed 全绿) —
    调度配置每个字段都必须字面锁死。"""
    cfg = MANIFEST["scheduler_config"]
    assert cfg["desired_retention"] == 0.9
    assert cfg["learning_steps_minutes"] == [1, 10]
    assert cfg["relearning_steps_minutes"] == [10]
    assert cfg["maximum_interval"] == 36500
    assert cfg["enable_fuzzing"] is False
    assert set(cfg.keys()) == {
        "parameters",
        "desired_retention",
        "learning_steps_minutes",
        "relearning_steps_minutes",
        "maximum_interval",
        "enable_fuzzing",
    }, "scheduler_config 键集变化 = 配置面漂移, 须评审重冻结"


def test_tolerance_ceiling_locked():
    """容差只许更严不许放宽 — manifest 单方把 rel 调成 1e-3 即红。
    子键集同锁 (round-5 LOW: 增删容差键会改变比较语义却曾静默通过)。"""
    tolerance = MANIFEST["comparison_tolerance"]
    assert set(tolerance.keys()) == {"float_rel", "float_abs"}
    assert 0 < tolerance["float_rel"] <= 1e-9
    assert 0 < tolerance["float_abs"] <= 1e-12


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
        # 键集锁 (round-5 LOW: 改 description / 塞嵌套未知键曾全绿)
        assert set(v.keys()) == {
            "id",
            "scenario",
            "description",
            "state_before_final_review",
            "steps",
            "expected",
        }, f"{v.get('id')}: 向量键集变化 — 须评审重冻结"
        assert set(v["expected"].keys()) == {
            "stability",
            "difficulty",
            "due",
            "last_review",
            "state",
            "step",
        }
        for step in v["steps"]:
            assert set(step.keys()) == {"rating", "review_at"}
        assert v["description"] == EXPECTED_SCENARIO_DESCRIPTION[v["scenario"]]

        scenario = v["scenario"]
        expected_state, expected_prefix = EXPECTED_SCENARIO[scenario]
        final_rating = v["steps"][-1]["rating"]
        assert v["id"] == f"{scenario}__{final_rating}", (
            f"{v['id']}: id 必须 == scenario__真实最终rating (实为 {scenario}__{final_rating})"
        )
        state_before = v["state_before_final_review"]
        assert isinstance(state_before, int) and not isinstance(state_before, bool), (
            f"{v['id']}: state_before_final_review 须为 int (bool 与 1 相等会静默通过)"
        )
        assert state_before == expected_state, f"{v['id']}: 声明前态 {state_before} != 字面锁 {expected_state}"
        actual_prefix = tuple(s["rating"] for s in v["steps"][:-1])
        assert actual_prefix == expected_prefix, (
            f"{v['id']}: 前缀 rating 序列 {actual_prefix} != 场景 skeleton {expected_prefix}"
        )
        # 时刻 skeleton **逐步**验证 (Codex round-3 HIGH: 只锁首步时,
        # 把中间步 00:10→00:05 并同步最终时刻与真实 expected 仍全绿 —
        # 因为后续 due 由已被篡改的 prefix 动态推导)。
        # 规则: 首步 == base_datetime; 其后每步时刻 == 上一步结果卡 due
        # + 该步偏移 (仅逾期场景的最终步偏移 30 天, 其余恒 0)。
        times = [datetime.fromisoformat(s["review_at"]) for s in v["steps"]]
        assert times == sorted(times), f"{v['id']}: 复习时刻必须非降序"
        scheduler = _build_scheduler()
        card = Card(card_id=MANIFEST["card_id"], due=datetime.fromisoformat(MANIFEST["base_datetime"]))
        last_index = len(v["steps"]) - 1
        for i, step in enumerate(v["steps"]):
            offset_days = EXPECTED_FINAL_OFFSET_DAYS[scenario] if i == last_index else 0
            expected_at = (
                datetime.fromisoformat(MANIFEST["base_datetime"]) if i == 0 else card.due + timedelta(days=offset_days)
            )
            assert times[i] == expected_at, (
                f"{v['id']}: 第 {i} 步时刻 {times[i].isoformat()} != skeleton 期望 "
                f"{expected_at.isoformat()}（首步=base_datetime，其后=上一步 due+{offset_days}d）"
            )
            card, _ = scheduler.review_card(card, RATING_BY_NAME[step["rating"]], times[i])

    # expected 字段类型门 (Codex round-3 MEDIUM: Python bool 与 0/1 数值相等,
    # state=true / step=false 曾静默全绿)
    for v in vectors:
        e = v["expected"]
        assert isinstance(e["state"], int) and not isinstance(e["state"], bool), f"{v['id']}: state 须为 int"
        assert e["step"] is None or (isinstance(e["step"], int) and not isinstance(e["step"], bool)), (
            f"{v['id']}: step 须为 int 或 null"
        )
        for key in ("stability", "difficulty"):
            value = e[key]
            assert value is None or (isinstance(value, float) and not isinstance(value, bool)), (
                f"{v['id']}: {key} 须为 float 或 null"
            )
        assert isinstance(e["due"], str) and isinstance(e["last_review"], (str, type(None)))

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


#: retrievability 曲线 skeleton 字面锁 (round-4 HIGH#5): 历史 rating 序列 +
#: 采样点相对末态 due 的天偏移。原实现只查三点升序唯一并信任 JSON 自带
#: steps/at, 把历史改成 Easy@T0、采样改 due+1/+2/+3 并同步 expected 仍全绿。
RETRIEVABILITY_PREFIX = ("good", "good")
RETRIEVABILITY_OFFSET_DAYS = (0, 7, 30)


def test_retrievability_curve_matches_golden():
    golden = GOLDEN["retrievability"]

    # skeleton: 历史 rating 序列与时刻链 (首步 base_datetime, 次步前一步 due)
    actual_prefix = tuple(s["rating"] for s in golden["steps"])
    assert actual_prefix == RETRIEVABILITY_PREFIX, (
        f"retrievability 历史 rating 序列 {actual_prefix} != 字面锁 {RETRIEVABILITY_PREFIX}"
    )
    scheduler = _build_scheduler()
    card = Card(card_id=MANIFEST["card_id"], due=datetime.fromisoformat(MANIFEST["base_datetime"]))
    for i, step in enumerate(golden["steps"]):
        expected_at = datetime.fromisoformat(MANIFEST["base_datetime"]) if i == 0 else card.due
        assert datetime.fromisoformat(step["review_at"]) == expected_at, (
            f"retrievability 第 {i} 步时刻 {step['review_at']} != skeleton 期望 {expected_at.isoformat()}"
        )
        card, _ = scheduler.review_card(card, RATING_BY_NAME[step["rating"]], expected_at)

    # card 快照必须与真实重放一致 (原实现完全不读该字段, 可换成任意对象)
    snapshot = golden["card"]
    assert _close(card.stability, snapshot["stability"])
    assert _close(card.difficulty, snapshot["difficulty"])
    assert card.due.isoformat() == snapshot["due"]
    assert (card.last_review.isoformat() if card.last_review else None) == snapshot["last_review"]
    # 类型门 (round-5: state 从 2 改成 2.0 曾仍全绿 — int 与 float 数值相等)
    assert isinstance(snapshot["state"], int) and not isinstance(snapshot["state"], bool), (
        "retrievability.card.state 须为 int (2.0 等浮点写法不接受)"
    )
    assert int(card.state) == snapshot["state"]
    assert snapshot["step"] is None or (isinstance(snapshot["step"], int) and not isinstance(snapshot["step"], bool))
    assert card.step == snapshot["step"]
    assert set(snapshot.keys()) == {"stability", "difficulty", "due", "last_review", "state", "step"}
    assert set(golden.keys()) == {"steps", "card", "at"}, "retrievability 键集变化 — 须评审重冻结"

    # 采样点必须恰为末态 due + 字面锁偏移, 且期望值由真实库复算
    assert len(golden["at"]) == len(RETRIEVABILITY_OFFSET_DAYS)
    for point, offset in zip(golden["at"], RETRIEVABILITY_OFFSET_DAYS):
        # 子键集锁 (round-6 LOW: point 加未知键曾全绿)
        assert set(point.keys()) == {"current_datetime", "expected"}
        assert isinstance(point["expected"], float) and not isinstance(point["expected"], bool)
        expected_at = card.due + timedelta(days=offset)
        assert datetime.fromisoformat(point["current_datetime"]) == expected_at, (
            f"retrievability 采样点 {point['current_datetime']} != 末态 due+{offset}d ({expected_at.isoformat()})"
        )
        actual = scheduler.get_card_retrievability(card, expected_at)
        assert _close(actual, point["expected"]), f"retrievability@+{offset}d: {actual} != {point['expected']}"


# ── 11. 解析歧义门 (round-15, Codex 十四轮 HIGH/MEDIUM) ──


def test_duplicate_keys_in_golden_json_are_rejected(tmp_path):
    """Codex 十四轮反例: manifest 开头插入重复 library_version 并保留后面的真值。

    默认 json.loads last-wins ⇒ 解析对象与原对象**完全相同**, 原 13 门全部照过;
    而 first-wins 解析器读到 999.0.0 —— 同一字节序列在两个合理解析器下结论相反。
    """
    raw = (HERE / "fsrs_golden_manifest.json").read_text(encoding="utf-8")
    tampered = raw.replace("{", '{"library_version": "999.0.0",', 1)
    path = tmp_path / "m.json"
    path.write_text(tampered, encoding="utf-8")

    # 前提复现: 宽松解析确实看不出任何差异
    assert json.loads(tampered) == json.loads(raw)
    assert json.loads(tampered)["library_version"] == MANIFEST["library_version"]
    # 严格加载必须拒
    with pytest.raises(_NonStandardGoldenJSON, match="library_version"):
        _load_golden(path)


def test_enum_bool_drift_is_rejected():
    """Rating/State 枚举值必须是 JSON 整数 — True == 1 会让 bool 漂移全绿。"""
    drifted = {**MANIFEST["rating_values"], "again": True}
    assert drifted == MANIFEST["rating_values"]  # 前提: 字典比较看不出来
    assert type(drifted["again"]) is not int  # 类型锁才看得出来
