"""CARD-DEBT-mutkill-R3 的先红后绿单测 —— 变异裁决共用判据的收口。

⛔ **覆盖面如实声明（DD-13 名实一致）**：文件名只提 `mutation_kill_identity`，实际
覆盖**两个**模块，其中 g33 那一块很容易被后人漏掉：

  · H1  `mutation_kill_identity._split_unique` —— 让**无 reason 读法**也进候选集；
        整行二义（两种合法读法并存）⇒ 切分不唯一 ⇒ 调用方判 `HARNESS-ERROR`。
  · H2  `mutation_kill_identity.kill_identity` —— 弱位置分支（`require_gate_file`
        且**无** `expect_loc`）禁止借用**另一道门**的失败位置合成 `KILLED`。
  · M①  `mutation_kill_identity.kill_identity` / `_loc_identity` —— 锚漂移优先判
        `HARNESS-ERROR`（不被 `rc==0` / 「红在门文件外」两条 SURVIVED 早退掩盖），
        且 `stmt:` 指纹**复核命中数恰为 1**（与 `check_expect_loc_unique` 同口径）。
  · M②  **`g33_mutation_gates.restore_or_keep_exit_code`** —— 末次还原失败不再被
        `_was_exiting` 静默吞掉，且**还原逐字节自检仍执行**。

⚠️ M② 的驱动形态（(h)④ 固定走「甲」，R-B14-9 补裁已接受）：该函数原本是 `main()`
内的**嵌套 def**，无模块级符号、不能直接 import 驱动；本卡把它提为模块级并接受注入
的 `restore_all` / `exiting` 回调，负控因此**在进程内**喂「末次还原抛异常」，
⛔ **不启动任何 g33 子进程** —— g33 除 `--selfcheck-syntax`（早返回）外的任何入口都会
进主 `try` 并在外层 `finally` 对 `_TARGET_FILES` **全量** `write_bytes`，其中含零写者
铁律覆盖的 `canvas-vault/.claude/scripts/fsrs_bridge.py`。

全部 I/O 落 pytest 的 `tmp_path`；不连 Neo4j / LanceDB，不读写 live vault。
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import g33_mutation_gates as g33  # noqa: E402
import mutation_kill_identity as mki  # noqa: E402

# ── 合成 pytest 输出 ────────────────────────────────────────────────────────
#
# ⚠️ 这里合成的是**判据的输入样本**，不是 mock 掉某一层：被测物仍是真实的
# `kill_identity()` / `_split_unique()`。格式逐字照 pytest 9.0.2 的
# `-rf --tb=line` 形态（分隔线、摘要头、收尾统计行三者缺一，判据面就不成立）。

_FAILURES_HEAD = "=================================== FAILURES ==================================="
_SUMMARY_HEAD = "=========================== short test summary info ============================"
_TAIL = "========================= 1 failed in 0.10s ========================="


def _out(summary_lines: list[str], loc_lines: list[str] | None = None) -> str:
    parts: list[str] = []
    if loc_lines:
        parts.append(_FAILURES_HEAD)
        parts.extend(loc_lines)
    parts.append(_SUMMARY_HEAD)
    parts.extend(summary_lines)
    parts.append(_TAIL)
    return "\n".join(parts) + "\n"


def _write_gate(tmp_path: Path, body: str, name: str = "test_gate_sample.py") -> Path:
    p = tmp_path / name
    p.write_text(body, encoding="utf-8")
    return p


# 门文件样本：两条**逐字相同**的断言写在同一个函数里 ⇒ 指纹相同、命中 2 条。
# `_fp()` 把作用域全名也拼进哈希，所以「同函数内重复」才撞得上（跨函数不撞）。
_GATE_DUP = """\
def test_dup() -> None:
    assert 1 == 2, "boom"
    assert 1 == 2, "boom"


def test_single() -> None:
    assert 3 == 4, "only-once"
"""


# ══ H1 —— 无 reason 读法必须进候选集 ════════════════════════════════════════


def test_h1_ambiguous_no_reason_reading_makes_split_non_unique() -> None:
    """整行二义 ⇒ `_split_unique` 必须判**不唯一**。

    `FAILED tests/x.py::test_x[case] - EXPECT[] ` 有两种合法读法：
      (读法 A) nodeid=`tests/x.py::test_x[case]` + reason=`EXPECT[]`；
      (读法 B) 整行就是一个**无 reason** 的 nodeid，参数 ID = `case] - EXPECT[`。
    旧实现只在「有 ` - ` 切点」时枚举候选，读法 B 从未进候选集 ⇒ `len(cands)==1`
    在一个**残缺的候选集**上成立（恒真式）。
    """
    nodeid = "tests/x.py::test_x[case]"
    line = f"FAILED {nodeid} - EXPECT[]"
    assert mki._split_unique(line, nodeid) is False, (
        "H1: 整行还可读成一个无 reason 的 nodeid（参数 ID = `case] - EXPECT[`），两种读法并存 ⇒ 切分不唯一，必须拒"
    )


def test_h1_ambiguous_line_escalates_to_harness_error(tmp_path: Path) -> None:
    """H1 的最终观测面：二义行应让 `kill_identity` 升 `HARNESS-ERROR`，⛔ 不是 KILLED。"""
    gate = _write_gate(tmp_path, _GATE_DUP)
    nodeid = "tests/x.py::test_x[case]"
    out = _out(
        [f"FAILED {nodeid} - EXPECT[]"],
        [f"{gate}:2: AssertionError: EXPECT[]"],
    )
    verdict, why = mki.kill_identity(1, out, nodeid, "EXPECT", gate_file=gate, require_gate_file=True)
    assert verdict == "HARNESS-ERROR", (
        f"H1: 摘要行切分不唯一 ⇒ 失败集合不可证 ⇒ 应判 HARNESS-ERROR，实得 {verdict}（{why}）"
    )


def test_h1_reading_space_is_documented() -> None:
    """读法空间的穷举必须**写进 docstring** —— 修的是「边界不可判定」这个性质。

    ⛔ round-3/4 连续被同一个错推翻的由来：每轮只补「这一条输入」，下一轮换个
    参数 ID 又漏一类。把读法空间列齐是让后人能检查「还漏了哪一类」的唯一办法。
    """
    doc = mki._split_unique.__doc__ or ""
    for token in ("完整 reason", "参数化", "无 reason", "读法空间"):
        assert token in doc, f"H1: `_split_unique` docstring 缺「{token}」这一类读法的登记"


@pytest.mark.parametrize(
    ("line", "nodeid"),
    [
        # 正控 ①：普通 reason —— 整行含**括号外**空白 ⇒ 读不成无 reason 的 nodeid。
        ("FAILED tests/x.py::test_x - AssertionError: boom", "tests/x.py::test_x"),
        # 正控 ②：参数化 + reason —— 整行不以 `]` 收尾 ⇒ 读不成无 reason 的 nodeid。
        ("FAILED tests/x.py::test_x[case] - AssertionError: boom", "tests/x.py::test_x[case]"),
        # 正控 ③：无 reason 的普通行。
        ("FAILED tests/x.py::test_x", "tests/x.py::test_x"),
        # 正控 ④：无 reason 的参数化行。
        ("FAILED tests/x.py::test_x[case]", "tests/x.py::test_x[case]"),
    ],
)
def test_pc_split_unique_accepts_unambiguous_readings(line: str, nodeid: str) -> None:
    """⛔ 验伪锚（改前必绿）：四类**本来就唯一**的读法不得被 H1 修法误伤。"""
    assert mki._split_unique(line, nodeid) is True, f"正控被误伤: {line!r}"


def test_h1_split_unique_flips_in_both_directions_in_both_families() -> None:
    """⛔ 如实钉住：本函数**不是单调的**，两族、两个方向都会翻。

    这条断言被推翻过**两次**：初稿「候选集只增不减 ⇒ 只会 True→False」被实测推翻；
    改成「只有无 ` - ` 那族会双向翻」又被 Codex round-1 LOW 推翻（有 ` - ` 那族也会
    False→True：旧版一条候选都没有、落到旧回退返回 False，新版捞到了唯一候选返回 True）。
    两族两向各钉一条，免得后人再据「它是单调的」推出错误的安全性结论。
    """
    # 无 ` - ` 族 · 收紧：括号成对，但正则切出的 nodeid 与唯一合法读法不符 ⇒ 本该拒
    assert mki._split_unique("FAILED a::b[c - d]", "a::b[c") is False
    # 无 ` - ` 族 · 放宽：括号不成对、却是**合法** nodeid（参数 ID = `[c`）⇒ 读法唯一
    assert mki._split_unique("FAILED a::b[[c]", "a::b[[c]") is True
    # 有 ` - ` 族 · 放宽（Codex round-1 LOW 的反例）：左侧 `a::b[[c]` 括号不成对、旧版
    # 不收它 ⇒ 无候选 ⇒ 旧回退按整行括号数判 False；新版认出它是 nodeid 形 ⇒ 唯一候选
    assert mki._split_unique("FAILED a::b[[c] - boom", "a::b[[c]") is True
    # ⛔ 两条放宽都不影响端到端：`_boundary_ok` 并联那道「方括号成对」仍会拒掉它
    assert mki._boundary_ok("a::b[[c]") is False


def test_h1_bracket_in_path_is_not_a_param_segment() -> None:
    """⛔ 路径段里的方括号**不是**参数段（Codex round-1 MEDIUM）。

    `tests/test_[x].py::test_x` 是合法 nodeid。拿「整串第一个 `[`」定位参数段起点会把
    路径里的方括号误当参数段 ⇒「不以 `]` 收尾」⇒ 判它不是 nodeid 形 ⇒ 一条**合法的
    无 reason 摘要行**被判不可判定 ⇒ 假 HARNESS-ERROR（旧裁决是 KILLED-UNBOUND）。
    """
    nid = "tests/test_[x].py::test_x"
    assert mki._nodeid_shaped(nid) is True, "路径含方括号的普通 nodeid 应是 nodeid 形"
    assert mki._split_unique(f"FAILED {nid}", nid) is True, "合法无 reason 行不得被判不唯一"
    # 参数化 + 路径含方括号：仍认得出参数段（起点是「前缀含 `::` 且无空白」的那个 `[`）
    assert mki._nodeid_shaped("tests/test_[x].py::test_x[case]") is True
    # 不以 `]` 收尾时整串就是路径/测试名（收集错误行 `ERROR tests/x.py`），无参数段可言
    assert mki._nodeid_shaped("tests/test_[x].py") is True
    # ⛔ 验伪锚：路径含空白仍不是 nodeid 形（不是把判据整个放掉）
    assert mki._nodeid_shaped("tests/te st.py::test_x") is False


def test_h1_parametrized_reason_ending_with_bracket_is_ambiguous() -> None:
    """保守性的代价：参数化 + reason 以 `]` 收尾 ⇒ 判不唯一（HARNESS-ERROR）。

    这**确实**是两种合法读法（读法 B 的参数 ID = `c] - AssertionError: [1, 2`），
    只看摘要行分不开。⛔ 不得在这里挑一个「看起来更像」的读法 —— 那正是 round-3/4
    两轮栽过的形态；要分开只能靠 `expect_loc`（D-28 延期，T8-C 的面）。
    """
    assert mki._split_unique("FAILED a::b[c] - AssertionError: [1, 2]", "a::b[c]") is False
    # 对照：reason 不以 `]` 收尾时仍然唯一（不是把整族参数化门都打成 HARNESS-ERROR）
    assert mki._split_unique("FAILED a::b[c] - AssertionError: [1, 2] boom", "a::b[c]") is True


# ══ H2 —— 弱位置判据禁跨门借位 ══════════════════════════════════════════════


def test_h2_weak_position_must_not_borrow_other_gate_failure(tmp_path: Path) -> None:
    """弱位置 + 跨门借位 ⇒ `HARNESS-ERROR`，⛔ 不是 KILLED。

    构造：目标门的失败红在**门文件之外**（消息命中）；另一道门的失败红在**门文件
    之内**（消息不命中）。旧实现在弱位置分支只查 `any(_same_file(...))`（有**某条**
    失败落在门文件里即可），而「所有失败 nodeid 都属于目标门」那道检查只在
    `_loc_identity()` 里、**只有传 `expect_loc` 才跑** ⇒ 两维由**不同**失败实例
    分别满足，凑成 KILLED。目标门只有一条 reason 时配对保护（`len(gate_reasons) > 1`）
    也不触发。
    """
    gate = _write_gate(tmp_path, _GATE_DUP)
    other = _write_gate(tmp_path, "def test_other() -> None:\n    assert 5 == 6, 'noise'\n", "test_other_gate.py")
    nodeid = "tests/gate.py::test_target"
    out = _out(
        [
            f"FAILED {nodeid} - EXPECT boom",
            "FAILED tests/other.py::test_other - noise",
        ],
        [
            # 目标门的失败落在**门文件之外**
            f"{other}:2: AssertionError: EXPECT boom",
            # 另一道门的失败落在**门文件之内** —— 被旧实现借去当「位置命中」
            f"{gate}:2: AssertionError: noise",
        ],
    )
    verdict, why = mki.kill_identity(1, out, nodeid, "EXPECT", gate_file=gate, require_gate_file=True)
    assert verdict == "HARNESS-ERROR", (
        f"H2: 摘要区里有不属于目标门的失败 ⇒ `--tb=line` 的位置行归属不可证，"
        f"弱位置判据不得据此合成 KILLED；实得 {verdict}（{why}）"
    )


def test_pc_h2_single_target_failure_still_killed(tmp_path: Path) -> None:
    """⛔ 验伪锚（改前必绿）：只有目标门失败、且红在门文件内 ⇒ 仍是 KILLED。"""
    gate = _write_gate(tmp_path, _GATE_DUP)
    nodeid = "tests/gate.py::test_target"
    out = _out(
        [f"FAILED {nodeid} - EXPECT boom"],
        [f"{gate}:2: AssertionError: EXPECT boom"],
    )
    verdict, why = mki.kill_identity(1, out, nodeid, "EXPECT", gate_file=gate, require_gate_file=True)
    assert verdict == "KILLED", f"正控被误伤: 实得 {verdict}（{why}）"


def test_h2_boundary_with_d28_is_documented() -> None:
    """H2 封堵的是**弱位置判据自己的承诺**，不触碰 D-28 延期的「具体断言绑定」。"""
    doc = mki.kill_identity.__doc__ or ""
    assert "弱位置" in doc and "D-28" in doc, "H2: `kill_identity` docstring 须写清与 D-28 的分界"


# ══ M① —— 锚漂移优先 HARNESS-ERROR + 命中数复核到 1 ═══════════════════════


def _fp_of(gate: Path, lineno: int) -> str:
    """取门文件 `lineno` 那条最小语句的指纹（`stmt:` 去前缀后的 12 位十六进制）。"""
    token = mki.loc_token_for(gate, str(gate), lineno)
    assert token is not None and token.startswith("stmt:"), f"取不到 {gate}:{lineno} 的指纹"
    return token[5:]


def test_m1_anchor_drift_not_masked_by_rc0_survived(tmp_path: Path) -> None:
    """锚漂移 + `rc==0` ⇒ `HARNESS-ERROR`，⛔ 不得当成 SURVIVED。

    `rc==0 → SURVIVED` 这条早退在**锚检查之前**，于是「门文件被别的卡改写、
    `expect_loc` 已找不到对应语句」会被读成「变异没被这道门抓住」——
    下一个人会去修一个根本没坏的门。
    """
    gate = _write_gate(tmp_path, _GATE_DUP)
    out_green = "=========================== 3 passed in 0.10s ===========================\n"
    verdict, why = mki.kill_identity(
        0,
        out_green,
        "tests/gate.py::test_single",
        gate_file=gate,
        expect_loc="stmt:deadbeef0000",  # 门文件里不存在的指纹 = 锚已漂
    )
    assert verdict == "HARNESS-ERROR", f"M①: 判据面（锚）已坏时不得先给出关于被测物的结论；实得 {verdict}（{why}）"


def test_m1_anchor_drift_not_masked_by_out_of_gate_survived(tmp_path: Path) -> None:
    """锚漂移 + 「红在门文件之外」⇒ `HARNESS-ERROR`，⛔ 不得当成 SURVIVED。"""
    gate = _write_gate(tmp_path, _GATE_DUP)
    other = _write_gate(tmp_path, "def test_other() -> None:\n    assert 5 == 6, 'noise'\n", "test_other_gate.py")
    nodeid = "tests/gate.py::test_single"
    out = _out([f"FAILED {nodeid} - boom"], [f"{other}:2: AssertionError: boom"])
    verdict, why = mki.kill_identity(1, out, nodeid, gate_file=gate, expect_loc="stmt:deadbeef0000")
    assert verdict == "HARNESS-ERROR", f"M①: 锚失效应盖过「红在门文件之外 ⇒ SURVIVED」这条早退；实得 {verdict}（{why}）"


def test_m1_stmt_fingerprint_hit_count_must_be_one(tmp_path: Path) -> None:
    """`stmt:` 指纹命中 **2** 条 ⇒ 身份不可唯一归属 ⇒ `HARNESS-ERROR`。

    旧实现只查指纹「在不在」（存在性），命中数是否为 1 交给跑门**之前**的
    `check_expect_loc_unique()` 把关 —— 门文件在跑门**期间**被改写成同形两条时，
    运行期这一侧看不见。与 `check_expect_loc_unique` 同口径：`len(hits) != 1` 即拒。
    """
    gate = _write_gate(tmp_path, _GATE_DUP)
    fp = _fp_of(gate, 2)
    assert len(mki.stmt_fingerprints(gate)[fp]) == 2, "夹具前提：该指纹应在门文件里命中 2 条语句"
    nodeid = "tests/gate.py::test_dup"
    out = _out([f"FAILED {nodeid} - boom"], [f"{gate}:2: AssertionError: boom"])
    verdict, why = mki.kill_identity(1, out, nodeid, gate_file=gate, expect_loc=f"stmt:{fp}")
    assert verdict == "HARNESS-ERROR", f"M①: 指纹命中 2 条 ⇒ 位置身份不可证，不得判 KILLED；实得 {verdict}（{why}）"


def test_m1_loc_identity_itself_rejects_multi_hit_fingerprint(tmp_path: Path) -> None:
    """⛔ 这条**直接**打在 `_loc_identity` 上，不经 `kill_identity`。

    为什么必须单列：`kill_identity` 里的 `anchor_surface_broken()` 与 `_loc_identity`
    里的命中数复核是**两层**，对上面那条端到端用例而言是冗余的 —— 2026-09-14 负控实测
    （`r3-negctl-m1a` / `r3-negctl-m1b`）：**单独拆掉任一层，端到端那条都仍然绿**。
    只有给每一层各留一个**自己的显形点**，「这一层承重」才是可证的（否则两层里随便
    哪一层悄悄失效都没人知道 —— 「门绿 ≠ 锁住修复」）。
    """
    gate = _write_gate(tmp_path, _GATE_DUP)
    fp = _fp_of(gate, 2)
    nodeid = "tests/gate.py::test_dup"
    out = _out([f"FAILED {nodeid} - boom"], [f"{gate}:2: AssertionError: boom"])
    ok, why = mki._loc_identity(out, nodeid, gate, f"stmt:{fp}")
    assert ok is False and why.startswith("HARNESS:"), (
        f"M①: `_loc_identity` 自己就该拒命中 2 条的指纹（HARNESS 面），实得 ({ok}, {why})"
    )
    assert "命中 2 条" in why, f"M①: 说明里须写清命中数，实得 {why}"


def test_m1_anchor_surface_broken_itself_reports_both_shapes(tmp_path: Path) -> None:
    """⛔ 这条**直接**打在 `anchor_surface_broken` 上，给该层留自己的显形点。"""
    gate = _write_gate(tmp_path, _GATE_DUP)
    assert mki.anchor_surface_broken(gate, f"stmt:{_fp_of(gate, 7)}") is None, "锚完好时不得报坏"
    drifted = mki.anchor_surface_broken(gate, "stmt:deadbeef0000")
    assert drifted is not None and "命中 0 条" in drifted, f"锚漂（0 条）应报出，实得 {drifted!r}"
    dup = mki.anchor_surface_broken(gate, f"stmt:{_fp_of(gate, 2)}")
    assert dup is not None and "命中 2 条" in dup, f"同形两处（2 条）应报出，实得 {dup!r}"
    assert mki.anchor_surface_broken(gate, None) is None, "不使用位置锚时不得报坏"


def test_pc_m1_rc0_with_valid_anchor_still_survived(tmp_path: Path) -> None:
    """⛔ 验伪锚（改前必绿）：锚**没坏**时 `rc==0` 仍是 SURVIVED —— rc 契约不变。"""
    gate = _write_gate(tmp_path, _GATE_DUP)
    fp = _fp_of(gate, 7)  # `test_single` 里那条唯一断言
    out_green = "=========================== 3 passed in 0.10s ===========================\n"
    verdict, why = mki.kill_identity(
        0, out_green, "tests/gate.py::test_single", gate_file=gate, expect_loc=f"stmt:{fp}"
    )
    assert verdict == "SURVIVED", f"正控被误伤: rc=0 + 锚完好应仍是 SURVIVED，实得 {verdict}（{why}）"


def test_pc_m1_valid_anchor_hit_once_still_killed(tmp_path: Path) -> None:
    """⛔ 验伪锚（改前必绿）：指纹恰命中 1 条且位置命中 ⇒ 仍是 KILLED。"""
    gate = _write_gate(tmp_path, _GATE_DUP)
    fp = _fp_of(gate, 7)
    nodeid = "tests/gate.py::test_single"
    out = _out([f"FAILED {nodeid} - only-once"], [f"{gate}:7: AssertionError: only-once"])
    verdict, why = mki.kill_identity(1, out, nodeid, gate_file=gate, expect_loc=f"stmt:{fp}")
    assert verdict == "KILLED", f"正控被误伤: 实得 {verdict}（{why}）"


# ══ M② —— g33 末次还原失败不吞、SHA 自检仍跑 ═══════════════════════════════


def _restore_fn():
    """取模块级 `restore_or_keep_exit_code`；缺席即 M② 未落地（指定断言）。"""
    fn = getattr(g33, "restore_or_keep_exit_code", None)
    assert callable(fn), (
        "M②: `restore_or_keep_exit_code` 应是**模块级**可注入函数（原为 main() 内嵌套 def，"
        "无模块级符号 ⇒ 末次还原路径无法在进程内驱动，负控也就无从落地）"
    )
    return fn


def test_m2_final_restore_failure_is_not_swallowed_and_sha_still_runs() -> None:
    """末次还原**新失败**必须浮出，且还原逐字节自检仍执行。

    旧形态：`_was_exiting` 为真时把还原的新异常 `traceback.print_exc()` 后 `pass`
    吞掉 ⇒ 原先那个 `SystemExit(130)` 继续展开 ⇒ `main()` 走不到 `drift` / `ok_restore`
    的计算与那道 rc=3 检查 ⇒ 「变异体可能留在生产文件里」这件事**一声不响**。
    """
    fn = _restore_fn()
    verified: list[str] = []

    def _boom() -> None:
        raise OSError("restore failed (synthetic)")

    def _verify() -> list[str]:
        verified.append("ran")
        return ["canvas-vault/.claude/scripts/example_target.py"]

    with pytest.raises(SystemExit) as ei:
        fn(_boom, lambda: True, final=True, verify=_verify)
    assert ei.value.code == 3, (
        f"M②: 末次还原失败 = 「变异体可能留在生产文件里」，退出码应升到 3，实得 {ei.value.code!r}"
    )
    assert verified == ["ran"], "M②: 末次还原失败时**还原逐字节自检仍须执行**（不得因早退跳过）"


def test_m2_first_signal_130_is_still_kept() -> None:
    """⛔ 验伪锚：还原**成功**时不改变任何控制流 —— 首次信号的 130 照旧保号。"""
    fn = _restore_fn()
    calls: list[str] = []
    assert fn(lambda: calls.append("restored"), lambda: True) is True
    assert calls == ["restored"]


def test_m2_not_exiting_means_new_exception_still_raises() -> None:
    """⛔ 验伪锚：**进来前没在退出展开**时，还原的异常照旧原样抛出（round-4 HIGH 约定不变）。"""
    fn = _restore_fn()

    def _boom() -> None:
        raise RuntimeError("not exiting (synthetic)")

    with pytest.raises(RuntimeError, match="not exiting"):
        fn(_boom, lambda: False)


def test_m2_non_final_failure_is_reported_not_silent() -> None:
    """非末次还原失败仍吞异常保号，但必须**返回 False** 让调用方记账。"""
    fn = _restore_fn()

    def _boom() -> None:
        raise OSError("mid-loop restore failed (synthetic)")

    assert fn(_boom, lambda: True) is False, "M②: 吞掉异常保号可以，但「还原失败过」这件事不得丢失"


def test_m2_signal_exit_during_final_restore_is_not_a_restore_failure(capsys) -> None:
    """⛔ 信号退出**不是**还原失败（Codex round-1 LOW）。

    `RestoreGuard` 收到信号时先把 `restore()` 跑完、再抛 `SystemExit(exit_code)`。若该
    信号落在**本次**还原期间（进来时 `exiting()` 为假、出来时为真），这个 SystemExit
    说的是「还原做完了，然后按约定退出」。不分辨的话，一次**正常**的 Ctrl-C 会让报告印出
    「末次还原失败／不得当成干净」—— 那正是本卡要消灭的那类谎报。
    """
    fn = _restore_fn()
    state = {"exiting": False, "verified": 0}

    def _restore_then_signal() -> None:
        state["exiting"] = True  # 守卫在还原**之后**置位并抛出约定退出码
        raise SystemExit(130)

    def _verify() -> list[str]:
        state["verified"] += 1
        return []

    with pytest.raises(SystemExit) as ei:
        fn(
            _restore_then_signal,
            lambda: state["exiting"],
            final=True,
            verify=_verify,
            clean_exit_code=130,  # ⛔ 必须显式告知；不告知即 fail-closed（见下一条用例）
        )
    assert ei.value.code == 130, f"⛔ 信号退出必须**保号** 130，不得升成 3，实得 {ei.value.code!r}"
    assert "末次还原失败" not in capsys.readouterr().err, "⛔ 还原其实成功了，不得谎报「末次还原失败」"


def test_m2_real_failure_during_signal_unwind_still_surfaces(capsys) -> None:
    """⛔ 验伪锚：**真的**还原失败（非 SystemExit）仍照旧浮出 —— 上面那条分辨没把门放掉。"""
    fn = _restore_fn()
    state = {"exiting": False}

    def _boom() -> None:
        state["exiting"] = True  # 即便同期进入了退出展开，OSError 也不是「按约定退出」
        raise OSError("real restore failure (synthetic)")

    with pytest.raises(OSError, match="real restore failure"):
        fn(_boom, lambda: state["exiting"], final=True, verify=lambda: [])
    assert "末次还原失败" in capsys.readouterr().err, "真失败必须浮出"


def test_h1_double_colon_inside_param_id_still_ambiguous() -> None:
    """⛔ 参数 ID 里可以有 `::` —— 参数段起点不能固定取「最后一个 `::` 之后」。

    Codex round-2 HIGH（本函数上一版引入的回归）：
    `FAILED tests/gate.py::test_target[case] - EXPECT[x :: y]] - AssertionError: other`
    的读法 B 是「整段左侧就是 nodeid，参数 ID = `case] - EXPECT[x :: y]`」。上一版用
    `rpartition("::")` 定位参数段，切点落进**参数 ID 内部**、前缀含空白 ⇒ 这条真实读法
    被漏掉 ⇒ 二义行重新判唯一 ⇒ 假 KILLED。
    """
    left = "tests/gate.py::test_target[case] - EXPECT[x :: y]]"
    assert mki._nodeid_shaped(left) is True, "参数 ID 含 `::` 的 nodeid 仍是 nodeid 形"
    line = "FAILED tests/gate.py::test_target[case] - EXPECT[x :: y]] - AssertionError: other"
    assert mki._split_unique(line, "tests/gate.py::test_target[case]") is False, (
        "H1: 参数 ID 含 `::` 时两种读法并存 ⇒ 必须判不唯一"
    )


def test_m2_restore_failure_exit_code_is_not_a_clean_signal_exit(capsys) -> None:
    """⛔ `SystemExit(131)` 是「还原失败」的约定信号，**不是**干净的信号退出。

    Codex round-2 MEDIUM：`RestoreGuard._finish` 在还原本身失败时抛 `exit_code + 1`。
    上一版只看「是不是 SystemExit」，于是 131 被当成干净退出放行，末次逐字节自检
    **零次调用** —— 本卡承诺的那道检查又丢了一次。
    """
    fn = _restore_fn()
    state = {"exiting": False, "verified": 0}

    def _restore_fails_then_guard_exits() -> None:
        state["exiting"] = True
        raise SystemExit(131)  # 守卫：还原失败 ⇒ exit_code + 1

    def _verify() -> list[str]:
        state["verified"] += 1
        return []

    with pytest.raises(SystemExit):
        fn(
            _restore_fails_then_guard_exits,
            lambda: state["exiting"],
            final=True,
            verify=_verify,
            clean_exit_code=130,
        )
    assert state["verified"] == 1, "M②: 131 = 还原失败 ⇒ 末次逐字节自检必须仍然跑"
    assert "末次还原失败" in capsys.readouterr().err, "M②: 131 必须浮出，不得当干净退出放行"


def test_m2_clean_exit_code_unknown_is_fail_closed(capsys) -> None:
    """⛔ 没告知干净退出码时 **fail-closed**：一律按还原失败处置（不猜）。"""
    fn = _restore_fn()
    state = {"exiting": False, "verified": 0}

    def _sig() -> None:
        state["exiting"] = True
        raise SystemExit(130)

    with pytest.raises(SystemExit):
        fn(_sig, lambda: state["exiting"], final=True, verify=lambda: state.__setitem__("verified", 1) or [])
    assert state["verified"] == 1, "M②: 未告知干净码 ⇒ 不得放行，自检照跑"
    assert "末次还原失败" in capsys.readouterr().err


def test_h1_param_bracket_must_follow_a_double_colon() -> None:
    """⛔ 参数段挂在**测试名**上，而测试名必然在 `::` 之后（Codex round-3 MEDIUM）。

    少了这条，`tests/test_[x].py::test_x - AssertionError: [1, 2]` 会拿**路径**里那个 `[`
    当参数段起点（前缀 `tests/test_` 无空白）⇒ 整行被误收进「无 reason」候选 ⇒ 一条合法行
    被判二义 ⇒ 假 HARNESS-ERROR。而 `tests/test_` 里没有 `::`，它当不了 `path::test`。
    """
    line = "FAILED tests/test_[x].py::test_x - AssertionError: [1, 2]"
    assert mki._nodeid_shaped("tests/test_[x].py::test_x - AssertionError: [1, 2]") is False
    assert mki._split_unique(line, "tests/test_[x].py::test_x") is True, "合法行不得被判二义"
    # ⛔ 验伪锚：`::` 之后的参数段仍然认（不是把整条判据放掉）
    assert mki._nodeid_shaped("tests/test_[x].py::test_x[case]") is True
    assert mki._nodeid_shaped("tests/x.py::TestC::test_m[a]") is True


def test_m2_mid_loop_failure_surfaces_even_when_final_restore_succeeds(capsys) -> None:
    """⛔ 中途还原失败过 + 末次还原**成功** ⇒ 这件事仍须显形（Codex round-4 LOW）。

    round-3 的收窄声明说这条路「由守卫退出码与末次还原的报告兜」—— 实测两个都没兜上：
    「守卫首次还原成功 → 中途某条还原失败 → 末次还原成功」跑下来退出码是 **130**（不是
    131）、末次也**不报失败**，那次中途失败只剩一段 traceback。现在把账传进来，末次即使
    成功也照样打印并跑一次逐字节自检。
    """
    fn = _restore_fn()
    verified: list[str] = []

    assert fn(lambda: None, lambda: True, final=True, verify=lambda: verified.append("x") or []) is True
    assert verified == [], "⛔ 验伪锚：账为空时不得平白报警、也不必跑自检"

    assert (
        fn(
            lambda: None,
            lambda: True,
            final=True,
            verify=lambda: verified.append("ran") or [],
            pending_failures=["M3", "M7"],
        )
        is True
    )
    err = capsys.readouterr().err
    assert verified == ["ran"], "M②: 账非空时末次即使成功也须跑逐字节自检"
    # ⚠️ 措辞在 round-6 改成如实的「末次还原成功, 但本轮早些时候有还原失败被吞」（round-5 LOW）
    assert "有还原失败被吞" in err and "2 次" in err and "M3, M7" in err, f"M②: 中途失败必须显形，实得 {err!r}"
    assert "末次还原失败" not in err, "⛔ 末次其实成功了，不得这么说"


def test_m2_guard_retry_must_not_hide_the_first_real_failure(capsys) -> None:
    """⛔ 守卫**重试成功**不得把首次真实失败盖掉（Codex round-5 MEDIUM）。

    `RestoreGuard.critical()` 的 `finally` 在**本体已经抛了 OSError** 的情况下仍会跑
    `_finish(pending)` —— 它重试 `restore()` 这次成功了，于是抛 `SystemExit(130)`。
    Python 把正在处理的 `OSError` 挂到 `__context__` 上，调用方只看见一个**形态干净**的
    130 ⇒ 首次那次真实还原失败一点痕迹都不留、自检也不跑。
    ⚠️ 本例用**真实** `RestoreGuard`（不是模拟守卫），逐字复现该时序。
    """
    calls = {"n": 0}

    def _restore() -> None:
        calls["n"] += 1
        if calls["n"] == 1:
            raise OSError("first restore failed (synthetic)")  # 重试那次会成功

    guard = mki.RestoreGuard(_restore, log=lambda _m: None)

    def _restore_all_under_critical() -> None:
        with guard.critical():
            guard._handler(2, None)  # 还原期收到 SIGINT ⇒ 只记待办
            _restore()  # 首次失败 ⇒ critical 的 finally 里守卫重试并抛 SystemExit(130)

    verified: list[str] = []
    with pytest.raises(SystemExit) as ei:
        g33.restore_or_keep_exit_code(
            _restore_all_under_critical,
            guard.exiting,
            final=True,
            verify=lambda: verified.append("ran") or [],
            clean_exit_code=130,
        )
    err = capsys.readouterr().err
    assert ei.value.code == 130, f"⛔ 约定退出码仍须保号 130，实得 {ei.value.code!r}"
    assert verified == ["ran"], "M②: 底下压着真实失败时，逐字节自检必须仍然跑"
    assert "first restore failed" in err, f"M②: 被盖住的原始失败必须显形，实得 {err!r}"


def test_m2_clean_signal_exit_has_no_swallowed_cause(capsys) -> None:
    """⛔ 验伪锚：**真正干净**的信号退出（底下没压异常）仍不得报警、不得多跑自检。"""
    verified: list[str] = []
    guard = mki.RestoreGuard(lambda: None, log=lambda _m: None)

    def _restore_then_signal() -> None:
        guard._handler(2, None)  # 不在 critical 里 ⇒ 立刻 _finish：还原成功后抛 130

    with pytest.raises(SystemExit) as ei:
        g33.restore_or_keep_exit_code(
            _restore_then_signal,
            guard.exiting,
            final=True,
            verify=lambda: verified.append("ran") or [],
            clean_exit_code=130,
        )
    assert ei.value.code == 130
    assert verified == [], "⛔ 干净信号退出不得平白多跑自检"
    assert "末次还原" not in capsys.readouterr().err, "⛔ 干净信号退出不得报「末次还原失败」"


def test_m2_wording_matches_what_actually_happened(capsys) -> None:
    """⛔ 措辞必须说实话：末次**成功**时不得印「末次还原失败」（Codex round-5 LOW）。"""
    fn = _restore_fn()
    assert fn(lambda: None, lambda: True, final=True, verify=lambda: [], pending_failures=["M3"]) is True
    err = capsys.readouterr().err
    assert "末次还原成功" in err, f"末次确实成功，措辞必须如实，实得 {err!r}"
    assert "末次还原失败" not in err, f"⛔ 末次没失败，不得这么说，实得 {err!r}"

    def _boom() -> None:
        raise OSError("real final failure (synthetic)")

    with pytest.raises(SystemExit):
        fn(_boom, lambda: True, final=True, verify=lambda: [], clean_exit_code=130)
    assert "末次还原失败" in capsys.readouterr().err, "⛔ 验伪锚：真失败时仍须说「末次还原失败」"


def test_m3_ast_denominator_fails_closed_on_uncountable_shapes(tmp_path: Path) -> None:
    """⛔ 数不出来时必须**抛**，不得返回一个偏小的数（Codex round-5 MEDIUM）。

    上一版只扫 `tree.body`，嵌套块里的写入既不计数**也不报错** —— 又一次「少算而不出声」，
    正是这条判据连着两轮失效的同一个形态。
    """
    import mutation_verdict_reconcile as rec

    base = "MUTATIONS = [1, 2, 3]\nMUTATIONS += [4, 5]\n"
    probe = tmp_path / "probe.py"
    orig = rec.SCRIPTS
    rec.SCRIPTS = tmp_path
    try:
        probe.write_text(base, encoding="utf-8")
        assert rec.ast_mutation_count("probe.py") == 5, "⛔ 验伪锚：可数形态必须数得对（含 `+=` 扩展）"
        for tail in (
            "\nif True:\n    MUTATIONS += [9]\n",  # 嵌套块
            "\nfor _ in range(3):\n    MUTATIONS += [9]\n",  # 循环
            "\n_X = [1]\nMUTATIONS += [*_X, 2]\n",  # `*` 展开
            "\nMUTATIONS.extend([9])\n",  # 就地改动
            "\ndef _f():\n    global MUTATIONS\n    MUTATIONS = []\n",  # 函数内 global
            "\n_O = None\nMUTATIONS = _O = [1]\n",  # 链式赋值
            "\n_Y = [1]\nMUTATIONS += _Y\n",  # `+= 变量`
            "\ntry:\n    MUTATIONS += [9]\nexcept Exception:\n    pass\n",  # try 块
        ):
            probe.write_text(base + tail, encoding="utf-8")
            with pytest.raises(rec.ReconcileError):
                rec.ast_mutation_count("probe.py")
    finally:
        rec.SCRIPTS = orig


def test_h1_double_colon_inside_path_is_not_a_test_name(tmp_path: Path) -> None:
    """⛔ **路径自身可以含 `::`** —— 参数段起点的前缀必须留得下**非空测试名**。

    Codex round-6 MEDIUM：`tests/foo::[x]/test_gate.py::test_x - AssertionError: [1, 2]`
    里 `[x]` 前面那截 `tests/foo::` 既无空白又含 `::`，「前缀含 `::`」那条单独放它过 ⇒
    整行又被误收进「无 reason」候选 ⇒ 同一种假 HARNESS-ERROR 换了个入口。
    加上「最后一个 `::` 之后非空」之后，`tests/foo::` 的测试名是空的，当不了 `path::test`。
    """
    nid = "tests/foo::[x]/test_gate.py::test_x"
    assert mki._nodeid_shaped(f"{nid} - AssertionError: [1, 2]") is False
    assert mki._split_unique(f"FAILED {nid} - AssertionError: [1, 2]", nid) is True, "合法行不得判二义"
    # ⛔ 验伪锚：同一条路径带真参数段时仍认得出（不是把判据整个放掉）
    assert mki._nodeid_shaped(f"{nid}[case]") is True
    # ⛔ 验伪锚：③ 没有退化成「取最后一个 `::` 之后的那个 `[`」—— 参数 ID 里的 `::` 仍算数
    assert mki._nodeid_shaped("tests/gate.py::test_target[case] - EXPECT[x :: y]]") is True
    # 测试名为空的纯形态也拒
    assert mki._nodeid_shaped("a::[b]") is False


def test_m2_swallowed_cause_walks_both_chain_branches() -> None:
    """⛔ 异常链的 `__cause__` 与 `__context__` **两支都要走**（Codex round-6 MEDIUM）。

    `raise SystemExit(130) from SystemExit(130)` 在处理 `OSError` 时抛出 ⇒ `__cause__` 是那个
    `SystemExit`、`__context__` 才是 `OSError`。只沿「优先链」(`__cause__ or __context__`) 走
    会一路走到 `None`，把真实失败整条漏掉。
    """

    def _cause_is_systemexit_context_is_oserror() -> None:
        try:
            raise OSError("hidden real failure")
        except OSError:
            raise SystemExit(130) from SystemExit(130)

    with pytest.raises(SystemExit) as ei:
        _cause_is_systemexit_context_is_oserror()
    found = g33._swallowed_cause(ei.value)
    assert isinstance(found, OSError) and "hidden real failure" in str(found), f"两支都要走，实得 {found!r}"

    def _suppressed_context() -> None:
        try:
            raise OSError("suppressed but real")
        except OSError:
            raise SystemExit(130) from None

    with pytest.raises(SystemExit) as ei2:
        _suppressed_context()
    # ⛔ 不理会 `__suppress_context__`：它是给 traceback 打印用的显示提示，不是
    #   「那次失败没发生」。拿它当豁免，正好等于给判据开一个后门。
    assert isinstance(g33._swallowed_cause(ei2.value), OSError), "`from None` 不得成为豁免口"

    # ⛔ 验伪锚：真干净的退出仍返回 None（不是把所有 SystemExit 都报成脏）
    assert g33._swallowed_cause(SystemExit(130)) is None
    try:
        try:
            raise SystemExit(131)
        except SystemExit:
            raise SystemExit(130)
    except SystemExit as e:
        assert g33._swallowed_cause(e) is None, "SystemExit 套 SystemExit 底下没有真失败"
    assert g33._swallowed_cause(OSError("not a SystemExit")) is None


def test_m2_non_final_entry_also_surfaces_a_swallowed_failure(capsys) -> None:
    """⛔ **逐条**还原入口（`final=False`）上被盖住的失败也必须显形（Codex round-6 MEDIUM）。

    那条路在 `was_exiting` 为假时直接 `raise`，记账那行根本走不到 —— 打印是唯一的痕迹。
    """
    calls = {"n": 0}

    def _restore() -> None:
        calls["n"] += 1
        if calls["n"] == 1:
            raise OSError("mid-loop first restore failed (synthetic)")

    guard = mki.RestoreGuard(_restore, log=lambda _m: None)

    def _restore_all_under_critical() -> None:
        with guard.critical():
            guard._handler(2, None)
            _restore()

    with pytest.raises(SystemExit):
        g33.restore_or_keep_exit_code(_restore_all_under_critical, guard.exiting, clean_exit_code=130)
    err = capsys.readouterr().err
    # ⚠️ 措辞在 round-7 改成不归因的「盖住了一个异常(未必来自还原本身)」（round-7 LOW）
    assert "逐条还原的退出码盖住了一个异常" in err, f"逐条入口也须显形，实得 {err!r}"
    assert "mid-loop first restore failed" in err


def test_m3_ast_denominator_rejects_subscript_and_del(tmp_path: Path) -> None:
    """⛔ 切片增删也要 fail-closed（Codex round-6 MEDIUM）。

    `MUTATIONS[:0] = [9]` / `del MUTATIONS[0]` 里的 `MUTATIONS` 是 **Load** 上下文
    （写入位是外层 `Subscript`），只看 `Name` 的 `Store`/`Del` 会整条漏掉 ⇒ 又一次少算而不出声。
    """
    import mutation_verdict_reconcile as rec

    probe = tmp_path / "probe.py"
    orig = rec.SCRIPTS
    rec.SCRIPTS = tmp_path
    try:
        probe.write_text("MUTATIONS = [1, 2, 3]\n", encoding="utf-8")
        assert rec.ast_mutation_count("probe.py") == 3, "⛔ 验伪锚：可数形态仍要数得对"
        for tail in ("\nMUTATIONS[:0] = [9]\n", "\ndel MUTATIONS[0]\n", "\nMUTATIONS[0] = 9\n"):
            probe.write_text("MUTATIONS = [1, 2, 3]" + tail, encoding="utf-8")
            with pytest.raises(rec.ReconcileError):
                rec.ast_mutation_count("probe.py")
    finally:
        rec.SCRIPTS = orig


def test_m3_real_suite_denominators_are_unchanged() -> None:
    """⛔ 验伪锚：fail-closed 收紧之后，四套**真实**源码的分母必须原样（138/9/11/18）。

    收紧判据最容易的失败模式是「把合法写法也拒掉」—— 那会让整条对账链恒红。
    """
    import mutation_verdict_reconcile as rec

    assert {k: rec.ast_mutation_count(v.source) for k, v in rec.SUITES.items()} == {
        "g32b": 138,
        "g32cb": 9,
        "g32ccr1": 11,
        "g33": 18,
    }


def test_h1_dash_inside_reason_is_genuinely_ambiguous() -> None:
    """⛔ reason 里带 ` - ` 的行**确实**二义 —— 判 HARNESS-ERROR 是对的，不是误判。

    这条断言的方向被**改过两次、回滚过一次**，过程本身是教训：

    round-8 曾把候选判据里的「方括号成对」删掉，让这类行判「唯一」。两次独立复核
    （Codex round-7 MEDIUM + 一次 172-agent 多视角扫描的 HIGH）都主张这么改，理由是
    「`…::test_x - AssertionError: expected` 在括号外含空白，pytest 永远不会把它当 nodeid」。

    ⛔ **那个共同前提是错的**，2026-09-15 于 pytest 9.0.2 实测推翻（存档
    `evidence-mutkill-r3/probe-nodeid-whitespace-*.txt`）：`globals()["test_x[case] - EXPECT"] = f`
    注入的测试**能被正常收集**，短摘要打出
    `FAILED …::test_x[case] - EXPECT - AssertionError: OTHER` —— 与「nodeid + reason」
    形态**逐字不可区分**。round-8 的收紧因此开了一条**假 KILLED**（Codex round-8 HIGH
    当场复现），已回滚。

    ⚠️ 代价如实说：这类行判 HARNESS-ERROR，是**保守但正确**的；要分开只能靠 `expect_loc`。
    """
    # 真二义：左侧可能是一个名字含 ` - ` 的测试
    assert (
        mki._split_unique("FAILED tests/gate.py::test_x - AssertionError: expected - actual", "tests/gate.py::test_x")
        is False
    )
    assert mki._split_unique("FAILED tests/gate.py::test_x - assert 3 - 1 == 1", "tests/gate.py::test_x") is False
    # ⛔ round-8 HIGH 的那条反例：左侧 `…[case] - EXPECT` 括号成对 ⇒ 必须进候选 ⇒ 判二义
    assert (
        mki._split_unique(
            "FAILED tests/gate.py::test_x[case] - EXPECT - AssertionError: OTHER",
            "tests/gate.py::test_x[case]",
        )
        is False
    ), "⛔ 不判二义就会把一条名字含 ` - ` 的测试的失败误当成 expect_msg 命中 ⇒ 假 KILLED"
    # ⛔ 验伪锚：reason 里**没有** ` - ` 时仍判唯一（收紧没有把整族都打成二义）
    assert mki._split_unique("FAILED tests/gate.py::test_x - AssertionError: boom", "tests/gate.py::test_x") is True


def test_h1_false_killed_path_is_closed_end_to_end(tmp_path: Path) -> None:
    """⛔ round-8 HIGH 的端到端面：那条行不得判 KILLED。

    构造与实测摘要行同形：目标门声明 `…::test_x`、`expect_msg="EXPECT"`；真实失败的是
    名字为 `test_x[case] - EXPECT` 的测试，其真实 reason 是 `AssertionError: OTHER`
    （**不含** EXPECT）。若判据把左侧截断成 `…::test_x[case]`，`EXPECT` 就从**测试名**里
    被读成了 reason ⇒ 假 KILLED。
    """
    gate = _write_gate(tmp_path, _GATE_DUP)
    out = _out(
        ["FAILED tests/gate.py::test_x[case] - EXPECT - AssertionError: OTHER"],
        [f"{gate}:2: AssertionError: OTHER"],
    )
    verdict, why = mki.kill_identity(1, out, "tests/gate.py::test_x", "EXPECT", gate_file=gate, require_gate_file=True)
    assert verdict == "HARNESS-ERROR", f"⛔ 假 KILLED 路径必须封死，实得 {verdict}（{why}）"


def test_m2_missing_verify_must_not_claim_no_drift(capsys) -> None:
    """⛔ **没跑自检就不能说「未检出漂移」**（Codex round-7 MEDIUM）。

    上一版把 `verify=None` 和「跑了、结果是空」折成同一个分支，于是一条根本没做的检查被
    报成了「没问题」—— 这正是本卡从头到尾在消灭的那类话。
    """
    fn = _restore_fn()
    assert fn(lambda: None, lambda: True, final=True, verify=None, pending_failures=["M3"]) is True
    err = capsys.readouterr().err
    assert "未跑" in err and "未知" in err, f"没给自检回调时必须说「未跑/未知」，实得 {err!r}"
    assert "未检出漂移" not in err, "⛔ 根本没跑，不得说「未检出漂移」"
    # ⛔ 验伪锚：真跑了且没漂移时，仍照旧说「未检出漂移」
    assert fn(lambda: None, lambda: True, final=True, verify=lambda: [], pending_failures=["M3"]) is True
    assert "未检出漂移" in capsys.readouterr().err


def test_m2_swallowed_exception_is_not_attributed_to_restore(capsys) -> None:
    """⛔ 被退出码盖住的异常**未必来自还原**，措辞不得替它归因（Codex round-7 LOW）。

    跑门时的 `TimeoutExpired` 正在展开、还原期间收到信号、三次还原**全部成功** —— 此时
    链上压着的是门执行的异常，不是还原失败。
    """
    fn = _restore_fn()

    def _signal_during_outer_unwind() -> None:
        raise SystemExit(130)

    try:
        raise TimeoutError("gate run timed out (synthetic)")
    except TimeoutError:
        with pytest.raises(SystemExit):
            fn(_signal_during_outer_unwind, lambda: True, final=True, verify=lambda: [], clean_exit_code=130)
    err = capsys.readouterr().err
    assert "未必来自还原本身" in err, f"不得把它归因给还原，实得 {err!r}"
    assert "TimeoutError" in err, "必须把原异常 repr 给出来让人自己判断"


def _rec():
    import mutation_verdict_reconcile as rec

    return rec


_G32B_OK = """
── 汇总 ──
KILLED (绑定断言身份: 位置 [+ 消息]): 138/138
KILLED-UNBOUND (仅证明指定门红了, 位置与消息都没绑): 0
KILLED 合计 (两者之和, **不等于**「全部被指定断言杀死」): 138/138
SURVIVED: 0
HARNESS-ERROR: 0 (负控自己坏了, 不是关于被测物的结论)
ANCHOR-ERROR: 0 (变异未施加, 不是结论)
SYNTAX-INVALID: 0 (>0 说明负控自己坏了)
六档之和: 138 (应 = 138) ✓
"""


def test_rec_parse_stdout_g32b_happy_path() -> None:
    """⛔ 验伪锚：合法 g32b 汇总段必须解析得出，且不把「KILLED 合计」吃成一档。"""
    parsed = _rec().parse_stdout("g32b", _G32B_OK)
    assert parsed.counts["KILLED"] == 138 and parsed.counts["KILLED-UNBOUND"] == 0
    assert parsed.printed_total == 138 and parsed.declared_m == 138
    assert sum(parsed.counts.values()) == 138, "「KILLED 合计」那行不得被多算成一档"


@pytest.mark.parametrize(
    ("mutate", "must_mention"),
    [
        (lambda t: t.replace("SURVIVED: 0", "SURVIVED: 0.5"), "解析不到"),  # 整 token：`0.5`
        (lambda t: t.replace("SURVIVED: 0", "SURVIVED: 0x10"), "解析不到"),  # 整 token：`0x10`
        (lambda t: t.replace("SURVIVED: 0", "SURVIVED: 7\nSURVIVED: 0"), "不止一次"),  # 同档重复
        (lambda t: t.replace("SURVIVED: 0\n", ""), "解析不到"),  # 缺档
        (lambda t: t.replace("六档之和: 138", "六档之和: 137"), None),  # 和 ≠ 逐档相加
    ],
)
def test_rec_parse_stdout_rejects_each_bad_shape(mutate, must_mention) -> None:
    """⛔ 五种坏法逐条钉住 —— 这些正是 round-1~3 接受的修复，此前 pytest 侧零覆盖。"""
    rec = _rec()
    bad = mutate(_G32B_OK)
    if must_mention is None:
        parsed = rec.parse_stdout("g32b", bad)
        assert sum(parsed.counts.values()) != parsed.printed_total, "逐档相加应与印出来的和对不上"
    else:
        with pytest.raises(rec.ReconcileError, match=must_mention):
            rec.parse_stdout("g32b", bad)


def test_rec_parse_json_rejects_non_integer_and_duplicate_keys() -> None:
    """⛔ JSON 侧：小数截断 / 负数抵消 / 重复键，三条都必须抛。"""
    rec = _rec()
    base = (
        '{"verdict_counts": {"KILLED": %s, "KILLED-UNBOUND": 0, "SURVIVED": %s, '
        '"HARNESS-ERROR": 0, "ANCHOR-ERROR": 0, "SYNTAX-INVALID": 0}, "total": 18}'
    )
    assert rec.parse_json("g33", base % (18, 0)).counts["KILLED"] == 18, "⛔ 验伪锚：合法 JSON 必须解析得出"
    with pytest.raises(rec.ReconcileError, match="不是整数"):
        rec.parse_json("g33", base % (18.9, 0))
    with pytest.raises(rec.ReconcileError, match="为负数"):
        rec.parse_json("g33", base % (19, -1))
    with pytest.raises(rec.ReconcileError, match="不止一次"):
        rec.parse_json("g33", '{"verdict_counts": {}, "total": 5, "total": 18}')


def test_rec_aggregate_vs_per_item_catches_compensating_tamper() -> None:
    """⛔ **补偿式篡改**只有「聚合 vs 逐条」这一维看得见。

    KILLED 9→8 同时 SURVIVED 0→1：逐档相加、印出来的和、自称分母、AST 现算条数
    **四个数全对得上**，只有把逐条裁决记录数一遍才露馅。
    """
    rec = _rec()
    tee = (
        "  x → rc=1 ⇒ KILLED (a)\n" * 9 + "\n  8/9 KILLED (绑定: 消息 + 失败位置在门文件内; x)\n"
        "  KILLED-UNBOUND: 0 (x)\n  SURVIVED: 1\n  HARNESS-ERROR: 0 (x)\n"
        "  ANCHOR-ERROR: 0 (x)\n  SYNTAX-INVALID: 0 (x)\n  六档之和: 9 (应 = 变异条数 9) ✓\n"
    )
    parsed = rec.parse_stdout("g32cb", tee)
    assert sum(parsed.counts.values()) == parsed.printed_total == parsed.declared_m == 9, "四数确实全对得上"
    assert parsed.per_item == {
        "KILLED": 9,
        "KILLED-UNBOUND": 0,
        "SURVIVED": 0,
        "HARNESS-ERROR": 0,
        "ANCHOR-ERROR": 0,
        "SYNTAX-INVALID": 0,
    }, "逐条记录里 KILLED 仍是 9 —— 与聚合的 8 对不上"
    assert parsed.counts != parsed.per_item, "这一维必须能看出差异"


def test_rec_per_item_none_means_unchecked_not_consistent() -> None:
    """⛔ 没有逐条记录时是「**未核**」，不得当成「核过且一致」。"""
    parsed = _rec().parse_stdout("g32b", _G32B_OK)
    assert parsed.per_item is None, "纯汇总段存档没有逐条行 ⇒ 这一维未核"


def test_rec_per_item_regex_does_not_eat_killed_unbound() -> None:
    """⛔ `KILLED` 的逐条正则不得把 `KILLED-UNBOUND` 吃掉一半（边界锚）。"""
    rec = _rec()
    tee = (
        "  a → rc=1 ⇒ KILLED (x)\n  b → rc=1 ⇒ KILLED-UNBOUND (x)\n"
        "\n  1/2 KILLED (绑定: 消息 + 失败位置在门文件内; x)\n"
        "  KILLED-UNBOUND: 1 (x)\n  SURVIVED: 0\n  HARNESS-ERROR: 0 (x)\n"
        "  ANCHOR-ERROR: 0 (x)\n  SYNTAX-INVALID: 0 (x)\n  六档之和: 2 (应 = 变异条数 2) ✓\n"
    )
    parsed = rec.parse_stdout("g32cb", tee)
    assert parsed.per_item["KILLED"] == 1 and parsed.per_item["KILLED-UNBOUND"] == 1


def test_judge_flags_keeps_error_lines_in_the_summary() -> None:
    """⛔ `-r` 的字符串**替换**默认 `fE` ⇒ 只写 `-rf` 会让 ERROR 行整条不进短摘要。

    2026-09-15 实测（pytest 9.0.2）：同一份用例集，`-rf` 的摘要区只有 FAILED 一行，
    `-rfE` 才多出 `ERROR …`。后果三层（最坏的是**假 SURVIVED**）见 `judge_flags` docstring。
    """
    assert "-rfE" in mki.judge_flags(), "⛔ 缺 `E`：目标门 ERROR 时会被判成 SURVIVED"
    assert "-rf" not in mki.judge_flags(), "⛔ 不得同时留下裸 `-rf`"


def test_h2_error_summary_line_is_not_borrowable(tmp_path: Path) -> None:
    """⛔ 目标门 **ERROR**（而非 FAILED）时不得判 SURVIVED（`-rfE` 修复的端到端面）。

    `-rf` 下目标门的 ERROR 不进摘要 ⇒ `gate_hit` 为假 ⇒ 判 SURVIVED（**假 SURVIVED**），
    而 `failures_region()` 却把 `=== ERRORS ===` 段的位置行一起收下 ⇒ H2 刚堵的借位
    从 ERROR 那一半原样复活。带上 `E` 之后该 nodeid 进失败集，归属不可证 ⇒ HARNESS-ERROR。
    """
    gate = _write_gate(tmp_path, _GATE_DUP)
    other = _write_gate(tmp_path, "def test_other() -> None:\n    assert 5 == 6, 'x'\n", "test_other_gate.py")
    nodeid = "tests/gate.py::test_target"
    head_err = "=================================== ERRORS ===================================="
    out = (
        f"{head_err}\n{gate}:2: RuntimeError: fixture exploded\n"
        f"{_FAILURES_HEAD}\n{other}:2: AssertionError: unrelated\n"
        f"{_SUMMARY_HEAD}\n"
        "FAILED tests/other.py::test_other - AssertionError: unrelated\n"
        f"ERROR {nodeid} - RuntimeError: fixture exploded\n{_TAIL}\n"
    )
    verdict, why = mki.kill_identity(1, out, nodeid, gate_file=gate, require_gate_file=True)
    assert verdict == "HARNESS-ERROR", f"目标门 ERROR 时不得判 SURVIVED，实得 {verdict}（{why}）"


def test_rec_reconcile_one_rejects_compensating_tamper(tmp_path: Path, capsys) -> None:
    """⛔ 这条打在 **`reconcile_one()`** 本体上，不是只断言解析结果不同（Codex round-8 MEDIUM）。

    上一条补偿式篡改用例只比较了 `parse_stdout()` 的返回值 —— 把 `reconcile_one()` 里那段
    「聚合 vs 逐条」比较整段删掉，它照样绿。判据本身没被门护住，与本卡要修的病同族。
    """
    rec = _rec()
    src = tmp_path / "probe_suite.py"
    src.write_text("MUTATIONS = [1, 2, 3, 4, 5, 6, 7, 8, 9]\n", encoding="utf-8")
    tee = tmp_path / "tee.txt"
    per_item_lines = "  x → rc=1 ⇒ KILLED (a)\n" * 9
    good = (
        "\n  9/9 KILLED (绑定: 消息 + 失败位置在门文件内; x)\n  KILLED-UNBOUND: 0 (x)\n  SURVIVED: 0\n"
        "  HARNESS-ERROR: 0 (x)\n  ANCHOR-ERROR: 0 (x)\n  SYNTAX-INVALID: 0 (x)\n"
        "  六档之和: 9 (应 = 变异条数 9) ✓\n"
    )
    orig_scripts, orig_suites = rec.SCRIPTS, dict(rec.SUITES)
    rec.SCRIPTS = tmp_path
    rec.SUITES["g32cb"] = rec.Suite("probe_suite.py", "stdout")
    try:
        tee.write_text(per_item_lines + good, encoding="utf-8")
        assert rec.reconcile_one("g32cb", tee) == [], "⛔ 验伪锚：全对的存档必须判空问题列表"
        # 补偿式篡改：KILLED 9→8 且 SURVIVED 0→1，四个数仍全对得上
        tee.write_text(
            per_item_lines + good.replace("9/9 KILLED", "8/9 KILLED").replace("SURVIVED: 0", "SURVIVED: 1"),
            encoding="utf-8",
        )
        problems = rec.reconcile_one("g32cb", tee)
        assert problems, "⛔ `reconcile_one()` 必须把补偿式篡改报成问题"
        assert any("逐条" in p for p in problems), f"必须点名是「聚合 vs 逐条」这一维，实得 {problems}"
    finally:
        rec.SCRIPTS = orig_scripts
        rec.SUITES.clear()
        rec.SUITES.update(orig_suites)
        capsys.readouterr()


def test_rec_per_item_regex_ignores_diagnostic_text(tmp_path: Path) -> None:
    """⛔ why 里的诊断文字不得被数进逐条（Codex round-8 MEDIUM）。

    why 是**被测进程可控**的断言消息拼出来的 —— 让它能影响计数本身就是个口子；
    且会让**合法**存档反而对账失败（假红）。
    """
    rec = _rec()
    tee = (
        "  a → rc=1 ⇒ SURVIVED (红在别的断言上: 实见 ['diagnostic ⇒ KILLED'])\n"
        "\n  0/1 KILLED (绑定: 消息 + 失败位置在门文件内; x)\n  KILLED-UNBOUND: 0 (x)\n  SURVIVED: 1\n"
        "  HARNESS-ERROR: 0 (x)\n  ANCHOR-ERROR: 0 (x)\n  SYNTAX-INVALID: 0 (x)\n"
        "  六档之和: 1 (应 = 变异条数 1) ✓\n"
    )
    per = rec.parse_stdout("g32cb", tee).per_item
    assert per["KILLED"] == 0 and per["SURVIVED"] == 1, f"诊断文字里的 `⇒ KILLED` 不得计数，实得 {per}"


def test_rec_json_results_wrong_shape_is_an_error_not_unchecked() -> None:
    """⛔ 字段**在但形态错** ≠ 字段**缺席**（Codex round-8 MEDIUM）。

    两者一起降级成「未核」，就等于把 `results` 改成 `"broken"` 当作豁免口。
    """
    rec = _rec()
    base = (
        '{"verdict_counts": {"KILLED": 18, "KILLED-UNBOUND": 0, "SURVIVED": 0, '
        '"HARNESS-ERROR": 0, "ANCHOR-ERROR": 0, "SYNTAX-INVALID": 0}, "total": 18%s}'
    )
    assert rec.parse_json("g33", base % "").per_item is None, "缺席 ⇒ 未核（如实说）"
    assert rec.parse_json("g33", base % ', "results": []').per_item is None, "空数组 ⇒ 未核"
    for bad in ('"broken"', "{}", "5"):
        with pytest.raises(rec.ReconcileError, match="不是数组"):
            rec.parse_json("g33", base % f', "results": {bad}')


def test_rec_expect_rejects_duplicate_suite() -> None:
    """⛔ `--expect g33,g33` 把同一份来源核两遍却报「2 套」—— 覆盖面说宽了（round-8 LOW）。"""
    rec = _rec()
    with pytest.raises(SystemExit, match="重复声明"):
        rec.main(["--expect", "g33,g33", "--json", "g33=/nonexistent.json"])
    # ⛔ 验伪锚：不重复时不得被这条误拦（它应当走到「文件不存在」那一条）
    with pytest.raises(SystemExit):
        rec.main(["--expect", "g33", "--json", "g33=/nonexistent.json"])


def test_rec_per_item_regex_is_per_suite_not_one_size_fits_all() -> None:
    """⛔ 逐条正则**按套写** —— g32b 的形态与另两套完全不同（Codex round-9 提问②）。

    `g32cb` / `g32ccr1`：`… → rc=1 ⇒ KILLED (…)`；
    `g32b`：`[<tag>] <gate> → KILLED (…)` —— **`→` 不是 `⇒`、没有 `rc=`**，而且
    `SURVIVED` 的标签里**自带一个 `⇒`**（源码实测 `"SURVIVED ⇒ 假门 (…)"`）。
    只用一条 `⇒` 正则对 g32b **零命中** ⇒ 整个「聚合 vs 逐条」这一维**静默**降级成「未核」。
    """
    rec = _rec()
    agg_b = (
        "\n── 汇总 ──\nKILLED (绑定断言身份: 位置 [+ 消息]): 1/2\n"
        "KILLED-UNBOUND (仅证明指定门红了, 位置与消息都没绑): 0\n"
        "KILLED 合计 (两者之和, **不等于**「全部被指定断言杀死」): 1/2\n"
        "SURVIVED: 1\nHARNESS-ERROR: 0 (x)\nANCHOR-ERROR: 0 (x)\nSYNTAX-INVALID: 0 (x)\n"
        "六档之和: 2 (应 = 2) ✓\n"
    )
    per_b = (
        "[M1] tests/x.py::t1 → KILLED (红在声称的那一条断言上)  [还原字节相同 abc123def456]\n"
        "[M2] tests/x.py::t2 → SURVIVED ⇒ 假门 (门全绿)  [还原字节相同 abc123def456]\n"
    )
    parsed = rec.parse_stdout("g32b", per_b + agg_b)
    assert parsed.per_item is not None, "⛔ g32b 的逐条行必须数得到，不得静默降级成「未核」"
    assert parsed.per_item["KILLED"] == 1 and parsed.per_item["SURVIVED"] == 1, parsed.per_item
    # ⛔ `SURVIVED ⇒ 假门` 里那个 `⇒` 不得让它被数成别的档
    assert sum(parsed.per_item.values()) == 2, f"恰好两条逐条记录，实得 {parsed.per_item}"


def test_rec_truncated_archive_is_rejected_not_silently_accepted(tmp_path: Path) -> None:
    """⛔ 半截存档（跑到一半的 tee）必须被拒 —— 这正是「禁 glob 取存档」那条规则的由来。

    2026-09-15 实跑时 `ls -1t` 取到了**正在跑**的那份 31 行 tee，判据当场报「KILLED 行命中
    0 次」。⇒ 拿 glob 取「最新」存档，会在并发跑动时悄悄换成一份没写完的。
    """
    rec = _rec()
    partial = tmp_path / "partial.txt"
    partial.write_text("  [M1] 变异说明\n        t1 → rc=1 ⇒ KILLED (x)\n", encoding="utf-8")
    with pytest.raises(rec.ReconcileError, match="KILLED 行"):
        rec.parse_stdout("g32cb", partial.read_text(encoding="utf-8"))


def test_h1_expect_msg_must_not_be_read_from_the_test_name(tmp_path: Path) -> None:
    """⛔ `expect_msg` 不得从**测试名**里读出来（Codex round-9 HIGH）。

    ⚠️ 这是第六次动这条线，但**换了问法**：前五次都在问「哪一种切分是真的」，每次给一条
    新的 nodeid 形态启发式，然后被下一条反例打掉。实测证明测试名可以是**任意字符串**
    ⇒ 每个 ` - ` 切点原则上都是合法读法 ⇒ 行级的「唯一性」判据要么漏、要么把几乎所有行
    都判成不可判定。现在只问：**我正要下的那个结论，对所有还说得通的读法是否都成立**。

    攻击：`FAILED …::test_x[case] - EXPECT]tail - AssertionError: OTHER`
    —— 解析器切成 nodeid=`…test_x[case]` + reason=`EXPECT]tail - …`，`EXPECT`「命中」；
    但真相可能是有个**名字叫** `test_x[case] - EXPECT]tail` 的测试，它的 reason 是
    `AssertionError: OTHER`，**根本不含** EXPECT。
    """
    gate = _write_gate(tmp_path, _GATE_DUP)
    out = _out(
        ["FAILED tests/gate.py::test_x[case] - EXPECT]tail - AssertionError: OTHER"],
        [f"{gate}:2: AssertionError: OTHER"],
    )
    verdict, why = mki.kill_identity(1, out, "tests/gate.py::test_x", "EXPECT", gate_file=gate, require_gate_file=True)
    assert verdict == "HARNESS-ERROR", f"⛔ 假 KILLED：EXPECT 可能来自测试名，实得 {verdict}（{why}）"
    assert "测试名" in why, f"诊断必须点明是「可能来自测试名」，实得 {why}"


@pytest.mark.parametrize(
    ("summary", "loc_rest", "declared", "expect"),
    [
        (
            "FAILED tests/gate.py::test_x - AssertionError: boom",
            "AssertionError: boom",
            "tests/gate.py::test_x",
            "boom",
        ),
        (
            "FAILED tests/gate.py::test_x[case] - AssertionError: boom",
            "AssertionError: boom",
            "tests/gate.py::test_x",
            "boom",
        ),
        (
            "FAILED tests/gate.py::test_x[c] - AssertionError: EXPECT here",
            "AssertionError: EXPECT here",
            "tests/gate.py::test_x",
            "EXPECT",
        ),
    ],
)
def test_pc_expect_msg_from_reason_still_killed(
    tmp_path: Path, summary: str, loc_rest: str, declared: str, expect: str
) -> None:
    """⛔ 验伪锚：`expect_msg` 确实在 reason 里时仍判 KILLED（这条收紧没有误伤正常面）。

    ⚠️ 夹具里位置行必须带**真实**的那条消息 —— 2026-09-15 实测（pytest 9.0.2）：摘要区的
    reason 与 `--tb=line` 的位置行**逐字相同**（带消息的断言与裸 `assert 1 == 2` 都是）。
    初稿这里图省事写成 `AssertionError: X`，于是 round-13 新加的「两个信源须一致」当场把
    它判成 HARNESS-ERROR —— **夹具不真，正控就测不出真东西**。
    """
    gate = _write_gate(tmp_path, _GATE_DUP)
    out = _out([summary], [f"{gate}:2: {loc_rest}"])
    verdict, why = mki.kill_identity(1, out, declared, expect, gate_file=gate, require_gate_file=True)
    assert verdict == "KILLED", f"正控被误伤: {summary!r} 实得 {verdict}（{why}）"


def test_rec_per_item_line_anchored_against_diagnostic_injection() -> None:
    """⛔ 逐条正则必须**整行锚定** —— why 里塞 `rc=1 ⇒ KILLED` 就能污染计数（round-9 MEDIUM）。

    why 由被测进程的断言消息拼出、**内容它可控**，所以判据不能只靠「附近有没有某个片段」，
    必须靠**这一行整体长什么样**。污染的后果是**合法**存档反而对账假红。
    """
    rec = _rec()
    tee = (
        "  a → rc=1 ⇒ SURVIVED (红在别的断言上: 实见 ['diagnostic rc=1 ⇒ KILLED'])\n"
        "\n  0/1 KILLED (绑定: 消息 + 失败位置在门文件内; x)\n  KILLED-UNBOUND: 0 (x)\n  SURVIVED: 1\n"
        "  HARNESS-ERROR: 0 (x)\n  ANCHOR-ERROR: 0 (x)\n  SYNTAX-INVALID: 0 (x)\n"
        "  六档之和: 1 (应 = 变异条数 1) ✓\n"
    )
    per = rec.parse_stdout("g32cb", tee).per_item
    assert per["KILLED"] == 0 and per["SURVIVED"] == 1, f"注入的 `rc=1 ⇒ KILLED` 不得计数，实得 {per}"


def test_h1_shortest_split_makes_later_only_scan_complete() -> None:
    """⛔ 钉住「只看更靠后」那条完备性论证**所依赖的前提**。

    `expect_msg_may_come_from_nodeid()` 只扫比解析结果更靠后的 ` - ` 切点，完备性来自
    `_FAILED_RE` 的 nodeid 是 `\\S+?`（**非贪婪**）⇒ 正则给出的就是**最短**合法切分 ⇒
    不存在「更靠前且仍命中目标门」的读法可漏。
    ⚠️ 谁把它改成贪婪或 `rsplit`，那条完备性当场失效 —— 所以把前提本身钉在这里。
    """
    m = mki._FAILED_RE.match("FAILED tests/gate.py::test_x - EXPECT - AssertionError: OTHER")
    assert m is not None and m.group("nodeid") == "tests/gate.py::test_x", (
        "⛔ 解析结果必须是**最短**切分；非贪婪一旦被改成贪婪，"
        "`expect_msg_may_come_from_nodeid` 的「只看更靠后」就漏读法了"
    )
    assert "\\S+?" in mki._FAILED_RE.pattern, "⛔ nodeid 必须保持非贪婪 `\\S+?`"


def test_h1_expect_msg_must_be_corroborated_by_the_location_line(tmp_path: Path) -> None:
    """⛔ `expect_msg` 必须被**位置行**这条独立信源佐证（Codex round-10 HIGH）。

    攻击：`FAILED …::test_x[<超长参数>] - EXPECT]tail` —— 超长参数把 reason 挤没了，
    `EXPECT` 其实是**测试名**的一部分。上一版的「更靠后切点」检查够不着它（整行无 reason
    的读法被有意排除，否则任何参数化行都会误判）。

    ⇒ 换信源：`--tb=line` 的位置行打 `<file>:<lineno>: <Exc>: <msg>`，与摘要区的 reason
    **不是同一条来源**。攻击下两者当场不一致（位置行是 `AssertionError: OTHER`）⇒ 不可证。
    """
    gate = _write_gate(tmp_path, _GATE_DUP)
    out = _out(
        [f"FAILED tests/gate.py::test_x[{'a' * 1100}] - EXPECT]tail"],
        [f"{gate}:2: AssertionError: OTHER"],
    )
    verdict, why = mki.kill_identity(1, out, "tests/gate.py::test_x", "EXPECT", gate_file=gate, require_gate_file=True)
    assert verdict == "HARNESS-ERROR", f"⛔ 两个信源不一致时不得判 KILLED，实得 {verdict}（{why}）"
    assert "两个独立信源" in why, f"诊断须点明是信源不一致，实得 {why}"


def test_pc_expect_msg_corroborated_by_both_sources_still_killed(tmp_path: Path) -> None:
    """⛔ 验伪锚：两个信源**都**含 `expect_msg` 时仍判 KILLED（这条收紧没有误伤正常面）。"""
    gate = _write_gate(tmp_path, _GATE_DUP)
    for summary, loc in (
        ("FAILED tests/gate.py::test_x - AssertionError: boom", "AssertionError: boom"),
        ("FAILED tests/gate.py::test_x[c] - AssertionError: boom", "AssertionError: boom"),
    ):
        out = _out([summary], [f"{gate}:2: {loc}"])
        verdict, why = mki.kill_identity(
            1, out, "tests/gate.py::test_x", "boom", gate_file=gate, require_gate_file=True
        )
        assert verdict == "KILLED", f"正控被误伤: {summary!r} 实得 {verdict}（{why}）"


def test_h1_location_crosscheck_truncation_asymmetry_is_safe(tmp_path: Path) -> None:
    """⛔ 钉住「位置行交叉核」那条安全性论证 —— 截断的不对称落在**安全**那一侧。

    交叉核的危险方向是「`expect_msg` 在**摘要**里有、在**位置行**里没有」（会造假
    HARNESS-ERROR）。2026-09-15 实测（pytest 9.0.2，`COLUMNS=1000`）：约 900 字符的断言
    消息下，**摘要 reason 被截得更短**（879，带 `...` 省略号），**位置行更长**（924，完整）
    —— 不对称恰好在反方向，所以截断造不出那个危险方向。

    ⚠️ 这条是**真跑**出来的性质，不是推理；所以用真 pytest 复跑一次钉住，
    而不是拿合成串假装验过。若哪天 pytest 改了截断策略，这条会先红。
    """
    import os
    import subprocess

    probe = tmp_path / "test_trunc_probe.py"
    probe.write_text('def test_long():\n    assert False, "X" * 900 + "TAILMARK"\n', encoding="utf-8")
    pytest_bin = Path(__file__).resolve().parents[2] / ".venv" / "bin" / "pytest"
    if not pytest_bin.exists():  # pragma: no cover - 环境缺 venv 时不把门判红
        pytest.skip("本树 backend/.venv/bin/pytest 不在")
    run = subprocess.run(
        [str(pytest_bin), str(probe), *mki.judge_flags()],
        capture_output=True,
        text=True,
        env={**os.environ, **mki.judge_env()},
    )
    out = run.stdout + run.stderr
    reasons = [r for _n, r in mki.failed_reasons(out)]
    locs = [rest for _p, _l, rest in mki.failed_locations(out)]
    assert reasons and locs, "夹具前提：这一跑必须同时产出摘要行与位置行"
    assert len(locs[0]) >= len(reasons[0]), (
        f"⛔ 位置行被截得比摘要还短 ⇒ 「摘要有、位置行没有」这个**危险方向**会因截断出现 ⇒ "
        f"位置行交叉核会造假 HARNESS-ERROR（摘要 {len(reasons[0])} / 位置行 {len(locs[0])}）"
    )
    assert "TAILMARK" in locs[0] and "TAILMARK" not in reasons[0], (
        "夹具前提：这一跑确实触发了两侧的截断差（否则这条论证没被真的测到）"
    )


def test_h2_gate_identity_must_be_provable(tmp_path: Path) -> None:
    """⛔ 「红的是**这道门**」本身要证明（Codex round-11 HIGH-2）。

    真实失败的是一个**名字叫** `test_x - suffix]tail` 的测试 —— 它跟声明的 `test_x`
    **是两个测试**。但 `_FAILED_RE` 的 `\\S+?` 非贪婪把它截成 `test_x`，`gate_hit()` 于是
    「命中」，消息与位置也都对得上 ⇒ 判 KILLED，而**指定的那道门根本没红**。
    """
    gate = _write_gate(tmp_path, _GATE_DUP)
    out = _out(
        ["FAILED tests/gate.py::test_x - suffix]tail - AssertionError: EXPECT"],
        [f"{gate}:2: AssertionError: EXPECT"],
    )
    verdict, why = mki.kill_identity(1, out, "tests/gate.py::test_x", "EXPECT", gate_file=gate, require_gate_file=True)
    assert verdict == "HARNESS-ERROR", f"⛔ 门身份不可证时不得判 KILLED，实得 {verdict}（{why}）"
    assert "不属于目标门" in why


def test_h2_multi_failure_locations_must_all_be_in_gate(tmp_path: Path) -> None:
    """⛔ 目标门有**多条**失败时，位置必须全部落在门文件里（Codex round-11 HIGH-1）。

    否则弱位置判据可被**跨实例拼装**：位置从落在门内的那一条借、消息从另一条借，
    两维各由不同失败实例满足 —— `--tb=line` 的位置行不带 nodeid，多条时配对本就不可证。
    """
    gate = _write_gate(tmp_path, _GATE_DUP)
    outside = _write_gate(tmp_path, "x = 1\n", "helper.py")
    out = _out(
        [
            f"FAILED tests/gate.py::test_x[{'a' * 1100}] - EXPECT]tail",
            "FAILED tests/gate.py::test_x[other] - AssertionError: EXPECT",
        ],
        [f"{gate}:2: AssertionError: OTHER", f"{outside}:1: AssertionError: EXPECT"],
    )
    verdict, why = mki.kill_identity(1, out, "tests/gate.py::test_x", "EXPECT", gate_file=gate, require_gate_file=True)
    assert verdict == "HARNESS-ERROR", f"⛔ 跨实例拼装必须拦下，实得 {verdict}（{why}）"
    # ⛔ 验伪锚：多条失败但位置**全部**在门内时仍判 KILLED（不是把多条一律打死）
    out_ok = _out(
        [
            "FAILED tests/gate.py::test_x[a] - AssertionError: boom",
            "FAILED tests/gate.py::test_x[b] - AssertionError: boom",
        ],
        [f"{gate}:2: AssertionError: boom", f"{gate}:3: AssertionError: boom"],
    )
    assert (
        mki.kill_identity(1, out_ok, "tests/gate.py::test_x", "boom", gate_file=gate, require_gate_file=True)[0]
        == "KILLED"
    )


def test_m1_crosscheck_only_applies_when_summary_actually_hit(tmp_path: Path) -> None:
    """⛔ 两侧**都不含** `expect_msg` 是正常的 SURVIVED，不是 HARNESS-ERROR（round-11 MEDIUM）。

    交叉核问的是「摘要命中了、另一条信源认不认」；摘要没命中就没有可对的东西。
    上一版把它排在「摘要有没有命中」之前，于是把一条正常的 SURVIVED 改判成 HARNESS-ERROR，
    诊断还谎称「只在摘要区命中」。
    """
    gate = _write_gate(tmp_path, _GATE_DUP)
    out = _out(
        ["FAILED tests/gate.py::test_x - AssertionError: OTHER"],
        [f"{gate}:2: AssertionError: OTHER"],
    )
    verdict, why = mki.kill_identity(1, out, "tests/gate.py::test_x", "EXPECT", gate_file=gate, require_gate_file=True)
    assert verdict == "SURVIVED", f"两侧都不命中 = 变异没被这道门抓住，实得 {verdict}（{why}）"


def test_rec_all_attribute_access_on_mutations_is_banned(tmp_path: Path) -> None:
    """⛔ 对 `MUTATIONS` 的属性访问**整族禁掉**（Codex round-11 MEDIUM）。

    「白名单」被连着绕开三次，每次换个入口：`__imul__` → `__class__.__imul__` →
    `copy.__self__` → `__iter__().__reduce__()[1][0]`。最后那个的属性链**以调用表达式为根**，
    「顺链找根 Name」够不着 —— 只要允许**任何**属性访问，就总能再找到一条通往原列表的路。
    ⇒ 停止逐个堵入口，改封整个面。实测四套源码对 `MUTATIONS` 的属性访问**各 0 处**。

    ⚠️ 本条**取代**了三条按「白名单」写的旧用例（`…uses_a_readonly_allowlist` /
    `…whitelist_rejects_attribute_chains` / `…must_be_called_not_taken_as_value`）——
    白名单那套判据已整体作废，留着它们就是在**断言一份已经不存在的契约**。
    """
    rec = _rec()
    probe = tmp_path / "probe.py"
    orig = rec.SCRIPTS
    rec.SCRIPTS = tmp_path
    try:
        for tail in (
            "\nMUTATIONS.__iter__().__reduce__()[1][0].append(4)\n",
            "\nmethod = MUTATIONS.copy\n",
            "\nMUTATIONS.__class__.__imul__(MUTATIONS, 2)\n",
            "\n_c = MUTATIONS.copy()\n",
        ):
            probe.write_text("MUTATIONS = [1, 2, 3]" + tail, encoding="utf-8")
            with pytest.raises(rec.ReconcileError, match="属性访问"):
                rec.ast_mutation_count("probe.py")
        # ⛔ 验伪锚：不走属性的合法读法仍放行（禁令不挡任何现有写法）
        for tail in ("\n_n = len(MUTATIONS)\n", "\n_s = [m for m in MUTATIONS]\n", "\n_f = MUTATIONS[0]\n"):
            probe.write_text("MUTATIONS = [1, 2, 3]" + tail, encoding="utf-8")
            assert rec.ast_mutation_count("probe.py") == 3
    finally:
        rec.SCRIPTS = orig
    # ⛔ 四套真实源码必须原样（收紧最容易的失败模式是把合法写法也拒掉）
    assert {k: rec.ast_mutation_count(v.source) for k, v in rec.SUITES.items()} == {
        "g32b": 138,
        "g32cb": 9,
        "g32ccr1": 11,
        "g33": 18,
    }


def test_rec_extra_verdict_key_is_rejected() -> None:
    """⛔ `verdict_counts` 里**多出来**的档也要抛（Codex round-11 MEDIUM）。

    只按六个已知键取值时，加一个 `"UNEXPECTED-VERDICT": 1` 会被**静默忽略** —— 存档自己的
    计数和是 19，本工具却按 18 去跟 AST 分母比，照样打 ✓。
    缺档不许当 0，多档同样不许当不存在：两边都是「没看见的东西当成没有」。
    """
    rec = _rec()
    base = (
        '{"verdict_counts": {"KILLED": 18, "KILLED-UNBOUND": 0, "SURVIVED": 0, '
        '"HARNESS-ERROR": 0, "ANCHOR-ERROR": 0, "SYNTAX-INVALID": 0%s}, "total": 18}'
    )
    assert rec.parse_json("g33", base % "").counts["KILLED"] == 18, "⛔ 验伪锚：合法 JSON 仍要解析得出"
    with pytest.raises(rec.ReconcileError, match="不认识"):
        rec.parse_json("g33", base % ', "UNEXPECTED-VERDICT": 1')


def test_h2_multi_failure_guard_counts_records_not_deduped_nodeids(tmp_path: Path) -> None:
    """⛔ 数**失败记录**，不数去重后的 nodeid（Codex round-12 HIGH）。

    `failed` 是个 `set`：两条摘要行只要解析出的 nodeid 相同（长前缀 + 不同尾巴）就被去重成
    1 条 ⇒ 「多条失败」判假 ⇒ round-14 那道位置守卫**整条失效**，跨实例拼装原样复活。
    `failure_records()` 保留全部记录、不去重 —— 它就是为这件事存在的。
    """
    gate = _write_gate(tmp_path, _GATE_DUP)
    outside = _write_gate(tmp_path, "x = 1\n", "helper.py")
    long_id = "a" * 1100
    out = _out(
        [
            f"FAILED tests/gate.py::test_x[{long_id}] - EXPECT]first",
            f"FAILED tests/gate.py::test_x[{long_id}] - EXPECT]second",
        ],
        [f"{gate}:2: AssertionError: OTHER", f"{outside}:1: AssertionError: EXPECT"],
    )
    verdict, why = mki.kill_identity(1, out, "tests/gate.py::test_x", "EXPECT", gate_file=gate, require_gate_file=True)
    assert verdict == "HARNESS-ERROR", f"⛔ 去重不得让守卫失效，实得 {verdict}（{why}）"


def test_pc_multi_failure_guard_does_not_touch_the_expect_loc_path(tmp_path: Path) -> None:
    """⛔ 验伪锚：给了 `expect_loc` 时那道守卫**不参与**（Codex round-12 MEDIUM）。

    位置已绑到门文件里的**那一条语句**上，另一条失败落在 helper 并不妨碍身份成立；
    在那条路上套用弱位置守卫会把**正当**的 KILLED 打成 HARNESS-ERROR。
    """
    gate = _write_gate(tmp_path, 'def test_a() -> None:\n    assert 1 == 2, "EXPECT"\n', "test_loc_gate.py")
    outside = _write_gate(tmp_path, "x = 1\n", "helper.py")
    token = mki.loc_token_for(gate, str(gate), 2)
    assert token and token.startswith("stmt:"), "夹具前提：门里那条语句要取得到指纹"
    out = _out(
        [
            "FAILED tests/gate.py::test_x[a] - AssertionError: EXPECT",
            "FAILED tests/gate.py::test_x[b] - AssertionError: EXPECT",
        ],
        [f"{gate}:2: AssertionError: EXPECT", f"{outside}:1: AssertionError: EXPECT"],
    )
    verdict, why = mki.kill_identity(1, out, "tests/gate.py::test_x", "EXPECT", gate_file=gate, expect_loc=token)
    assert verdict == "KILLED", f"expect_loc 路不得被弱位置守卫误伤，实得 {verdict}（{why}）"


def test_rec_mutations_read_contexts_are_whitelisted(tmp_path: Path) -> None:
    """⛔ **读**也按白名单收（Codex round-12 MEDIUM）。

    上一轮只禁了 `MUTATIONS.<属性>`，于是换成**不经属性**的路子照样改表：
    `list.append(MUTATIONS, 4)`（当**实参**传给未绑定方法）、
    `alias = MUTATIONS; alias.append(4)`（换个名字，根 Name 就不叫 MUTATIONS 了）。
    ⇒ 逐个堵入口这条路已走到头（第五次换入口）。改成**只认三种语境**。
    ⚠️ 实测四套源码对 `MUTATIONS` 的 Load **只有**这三种（各 23 / 12 / 11 处）。
    """
    rec = _rec()
    probe = tmp_path / "probe.py"
    orig = rec.SCRIPTS
    rec.SCRIPTS = tmp_path
    try:
        for tail in ("\nlist.append(MUTATIONS, 4)\n", "\nalias = MUTATIONS\nalias.append(4)\n", "\n_x = MUTATIONS\n"):
            probe.write_text("MUTATIONS = [1, 2, 3]" + tail, encoding="utf-8")
            with pytest.raises(rec.ReconcileError, match="未白名单"):
                rec.ast_mutation_count("probe.py")
        # ⛔ 验伪锚：四套实际用到的三种读法必须仍放行
        for tail in (
            "\n_n = len(MUTATIONS)\n",
            "\n_s = [m for m in MUTATIONS]\n",
            "\n_f = MUTATIONS[0]\n",
            "\nfor _m in MUTATIONS:\n    pass\n",
        ):
            probe.write_text("MUTATIONS = [1, 2, 3]" + tail, encoding="utf-8")
            assert rec.ast_mutation_count("probe.py") == 3, f"合法读法被误挡: {tail!r}"
    finally:
        rec.SCRIPTS = orig
    assert {k: rec.ast_mutation_count(v.source) for k, v in rec.SUITES.items()} == {
        "g32b": 138,
        "g32cb": 9,
        "g32ccr1": 11,
        "g33": 18,
    }
