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
    assert "逐条还原期间有异常被退出码盖住" in err, f"逐条入口也须显形，实得 {err!r}"
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
