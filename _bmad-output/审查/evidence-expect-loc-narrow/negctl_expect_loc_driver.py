#!/usr/bin/env python3
"""CARD-EXPECT-LOC-NARROW 的**只读**对照输入驱动（(b) 先红 / (e) 反例翻转）。

⛔ 它**不跑 pytest、不改任何文件、不连库**：只合成一份 `out`（形状与真 pytest
`-rfE --tb=line --show-capture=no` 的输出逐段同构），喂给 `mutation_kill_identity.
kill_identity()`，看**同一份输入**在 `expect_loc=None` 与 `expect_loc=stmt:<目标>`
两种口径下判成什么。

复现的形态 = **Y1-B HIGH-1**（UAT-CARD-DEBT-mutkill-R2 §9 #4）：
  门文件里有两条断言 —— **前提断言**（先执行，消息里内嵌了被测子进程的输出）与
  **目标断言**（这条变异本该打红的那一条）。子进程运行期拼出的文本里**含**目标断言
  的 `expect_msg` 片段 ⇒ 摘要区 reason 与 `--tb=line` 位置行两个信源都「命中」，
  而位置落在**前提断言**上。`require_gate_file=True` 只问「有没有某条失败落在**门
  文件**里」—— 两条断言同在一个文件里，它分不开 ⇒ 误判 KILLED。

⚠️ 两条断言的 `stmt:` 指纹都由 `stmt_fingerprints(<门文件>)` **实测**取得（本文件
只按「作用域 + 是不是 Assert + 源码里含不含 expect_msg 字面量」选，⛔ 不推算行号、
不手抄指纹）。选中的指纹与它在门文件里的行号一并打印，便于复核。

用法：
  python3 negctl_expect_loc_driver.py before <g32cb|g32ccr1|g33>
  python3 negctl_expect_loc_driver.py after  <g32cb|g32ccr1|g33>

`after` 模式的 `expect_loc` **不自己算**，而是 `import` 该套 harness 后读它的
`EXPECT_LOC[<mid>]` —— 证的是「本卡真正写进表里的那个值」能翻转，而不是
「某个临时算出来的值」能翻转。
"""

from __future__ import annotations

import ast
import importlib
import sys
from pathlib import Path

WT = Path(__file__).resolve().parents[3]
SCRIPTS = WT / "backend" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from mutation_kill_identity import (  # noqa: E402
    _fp,
    _stmts_with_scope,
    kill_identity,
    stmt_fingerprints,
)

#: 每套挑一条变异做对照。`mid` 必须是该套 `MUTATIONS` 的第 1 字段。
#: ⚠️ 选的是「门函数里至少有两条断言」的条目 —— 对照形态本身要求前提与目标可分。
CASES = {
    "g32cb": ("g32cb_mutation_gates", "M1"),
    "g32ccr1": ("g32ccr1_negative_controls", "E1"),
    "g33": ("g33_mutation_gates", "M2-cas-guard"),
}


def _harness_facts(modname: str, mid: str):
    """从 harness 模块**实测**取 (门文件绝对路径, nodeid, expect_msg)。⛔ 不手抄。"""
    mod = importlib.import_module(modname)
    muts = {m[0]: m for m in mod.MUTATIONS}
    if mid not in muts:
        raise SystemExit(f"✗✗ {modname} 里没有变异 {mid!r}")
    m = muts[mid]
    if modname == "g33_mutation_gates":
        # (id, 文件, 原文, 变异文, nodeid, 说明, expect_msg)
        gate_file = mod.BACKEND / mod.TESTS
        nodeid, expect_msg = m[4], m[6]
    else:
        # (id, 说明, 目标文件, 原文, 变异文, 门函数名)
        gate_file = mod.GATE_FILE
        nodeid, expect_msg = mod._nodeid(m[5]), mod.EXPECT_MSG.get(mid)
    return mod, gate_file, nodeid, expect_msg


def _scope_of(nodeid: str) -> str:
    """nodeid → 门函数名（`stmt_fingerprints` 的作用域键就是它）。"""
    return nodeid.rsplit("::", 1)[-1].split("[", 1)[0]


def _pick_stmts(gate_file: Path, scope: str, expect_msg: str):
    """在门函数作用域里挑 (前提断言, 目标断言)。返回两个 `(指纹, 行号, 源码首行)`。

    * **目标断言** = 该作用域里源码含 `expect_msg` 字面量的那条 `assert`（唯一）；
    * **前提断言** = 该作用域里**行号最小**、不含 `expect_msg`、且指纹在整份门文件里
      恰好命中 1 条的那条 `assert`。
    ⛔ 两者都取实测指纹；任何一条取不到就当场退出（不猜、不降级）。
    """
    src = gate_file.read_text(encoding="utf-8").splitlines()
    fps = stmt_fingerprints(gate_file)
    cands = [
        (node, sc)
        for node, sc in _stmts_with_scope(gate_file)
        if sc == scope and isinstance(node, ast.Assert)
    ]
    if not cands:
        raise SystemExit(f"✗✗ 门文件 {gate_file.name} 的作用域 {scope!r} 里没有 assert 语句")

    def rec(node, sc):
        fp = _fp(node, sc)
        return fp, node.lineno, src[node.lineno - 1].strip()[:110], len(fps.get(fp, []))

    seg = {}
    for node, sc in cands:
        seg[id(node)] = ast.get_source_segment(gate_file.read_text(encoding="utf-8"), node) or ""
    targets = [(n, s) for n, s in cands if expect_msg in seg[id(n)]]
    if len(targets) != 1:
        raise SystemExit(
            f"✗✗ 作用域 {scope!r} 里含 expect_msg 的 assert 有 {len(targets)} 条（应为 1）—— 对照形态选不出目标断言"
        )
    tgt = rec(*targets[0])
    if tgt[3] != 1:
        raise SystemExit(f"✗✗ 目标断言指纹在门文件里命中 {tgt[3]} 条（应为 1）")
    prem = None
    for node, sc in sorted(cands, key=lambda x: x[0].lineno):
        if expect_msg in seg[id(node)]:
            continue
        r = rec(node, sc)
        if r[3] == 1:
            prem = r
            break
    if prem is None:
        raise SystemExit(f"✗✗ 作用域 {scope!r} 里挑不出「不含 expect_msg 且指纹唯一」的前提断言")
    return prem, tgt


def _synth_out(gate_file: Path, nodeid: str, premise_line: int, expect_msg: str) -> str:
    """合成 `out`：位置行落在**前提断言**上，而它的消息里内嵌了含 `expect_msg` 的子进程输出。

    ⛔ reason 里**不得**出现第二个 ` - `：`gate_identity_unprovable()` 会把更靠后的
    切点读成「另一个不属于本门的 nodeid」⇒ 判 HARNESS-ERROR，那样对照就不是
    「误判 KILLED」这件事了（判据面坏掉，而不是判据被喂饱）。
    """
    reason = (
        f"AssertionError: 前提不成立(子进程 stderr 原样内嵌): "
        f"[child-stderr] ... {expect_msg} ... [/child-stderr]"
    )
    return (
        "=========================== FAILURES ===========================\n"
        f"{gate_file}:{premise_line}: {reason}\n"
        "===================== short test summary info =====================\n"
        f"FAILED {nodeid} - {reason}\n"
        "========================= 1 failed in 0.42s =========================\n"
    )


def main(argv: list[str]) -> int:
    if len(argv) != 3 or argv[1] not in ("before", "after") or argv[2] not in CASES:
        print(__doc__)
        return 4
    mode, harness = argv[1], argv[2]
    modname, mid = CASES[harness]
    mod, gate_file, nodeid, expect_msg = _harness_facts(modname, mid)
    scope = _scope_of(nodeid)
    prem, tgt = _pick_stmts(Path(gate_file), scope, expect_msg)
    out = _synth_out(Path(gate_file), nodeid, prem[1], expect_msg)

    print(f"── 对照输入（{harness} / 变异 {mid} / 口径 {mode}）──")
    print(f"  门文件      : {gate_file}")
    print(f"  nodeid      : {nodeid}")
    print(f"  expect_msg  : {expect_msg!r}")
    print(f"  前提断言    : 行 {prem[1]}  指纹 stmt:{prem[0]}  命中 {prem[3]} 条")
    print(f"                源码 {prem[2]!r}")
    print(f"  目标断言    : 行 {tgt[1]}  指纹 stmt:{tgt[0]}  命中 {tgt[3]} 条")
    print(f"                源码 {tgt[2]!r}")
    print("  合成 out（逐行）:")
    for ln in out.splitlines():
        print(f"    | {ln}")

    if mode == "before":
        expect_loc = None
        print("\n  口径: expect_loc=None（本卡改前三套的实际调用形态）")
    else:
        table = getattr(mod, "EXPECT_LOC", None)
        if not isinstance(table, dict):
            raise SystemExit(f"✗✗ {modname} 里没有 EXPECT_LOC 表 —— 改后口径取不到")
        expect_loc = table.get(mid)
        if expect_loc is None:
            raise SystemExit(f"✗✗ {modname}.EXPECT_LOC 里没有 {mid!r} —— 对照条目不能挑一个被豁免的")
        print(f"\n  口径: expect_loc={expect_loc!r}（**读自 {modname}.EXPECT_LOC[{mid!r}]**，不是现算的）")
        if expect_loc != f"stmt:{tgt[0]}":
            print(f"  ⚠️ 注意: 表里的值与本驱动实测的目标断言指纹 stmt:{tgt[0]} 不同 —— 如实打印，不代改")
        if expect_loc == f"stmt:{prem[0]}":
            raise SystemExit("✗✗ 表里的 expect_loc 恰是**前提断言** —— 对照不成立，停下")

    verdict, why = kill_identity(
        1, out, nodeid, expect_msg, gate_file=gate_file, require_gate_file=True, expect_loc=expect_loc
    )
    print(f"\n  ⇒ verdict = {verdict}")
    print(f"     why     = {why}")
    killed = verdict.startswith("KILLED")
    if mode == "before":
        ok = killed
        print(f"\n  判据: verdict 以 KILLED 开头 ⇒ {'✅ 成立（当前口径误判）' if ok else '⛔ 不成立'}")
    else:
        ok = not killed
        print(f"\n  判据: verdict **不**以 KILLED 开头 ⇒ {'✅ 成立（位置身份挡住了）' if ok else '⛔ 不成立'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
