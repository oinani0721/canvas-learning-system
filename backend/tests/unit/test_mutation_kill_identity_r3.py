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


def test_h1_no_reason_branch_flips_in_both_directions() -> None:
    """⛔ 如实钉住「无 ` - ` 切点」那一族判据换法后的**两个**翻转方向。

    初稿 docstring 写的是「候选集只增不减 ⇒ 只会 True→False」—— 2026-09-14 实测**推翻**：
    旧判据（整行方括号成对）与新判据（整行是 nodeid 形）**互不包含**。两条都钉住，
    免得后人以为这里是单调的、据此推出错误的安全性结论。
    """
    # 收紧方向：括号成对但正则切出的 nodeid 与唯一合法读法不符 ⇒ 本该拒
    assert mki._split_unique("FAILED a::b[c - d]", "a::b[c") is False
    # 放宽方向：括号不成对、却是**合法** nodeid（参数 ID = `[c`）⇒ 读法唯一
    assert mki._split_unique("FAILED a::b[[c]", "a::b[[c]") is True
    # ⛔ 但端到端不因此放宽：`_boundary_ok` 并联那道「方括号成对」仍会拒掉它
    assert mki._boundary_ok("a::b[[c]") is False


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
