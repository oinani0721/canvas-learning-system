#!/usr/bin/env python3
"""复核 Codex round-1 **LOW-1** 指出的那条「未被本卡对照拦下的输入」（⛔ 不直接采信，自己跑）。

Codex 的对照思路：保持 §一 那份合成 `out` 的前提失败、单条摘要行与 `rc=1` **不变**，
只在 `=== FAILURES ===` 区**额外加一条**落在**目标行**的位置行 ——
    `<门文件>:<目标断言行>: AssertionError: <expect_msg>`
`_loc_identity()` 的位置判据是 `expect_loc in tokens`（**任一** token 命中即算），于是
`expect_loc` 仍然「命中」，三套重新判成 `KILLED`。

⚠️ 这条属于**共用裁判** `mutation_kill_identity._loc_identity()` 的判据边界（T8-B 地盘），
不是本卡三套 harness 的接线缺陷；本卡未改共用裁判。它的意义是把本卡的说法收窄成
「本卡这三份对照输入已被拦下」，而不是「Y1-B HIGH-1 已全面闭合」。

⚠️ 本脚本**不主张**真实 pytest 会不会打出这种两条位置行的输出 —— 那没有实测，如实留空。

用法：`python3 negctl_extra_loc_uncovered.py <g32cb|g32ccr1|g33>`
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[2] / "backend" / "scripts"))

from mutation_kill_identity import kill_identity  # noqa: E402
from negctl_expect_loc_driver import CASES, _harness_facts, _pick_stmts, _scope_of, _synth_out  # noqa: E402


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[1] not in CASES:
        print(__doc__)
        return 4
    harness = argv[1]
    modname, mid = CASES[harness]
    mod, gate_file, nodeid, expect_msg = _harness_facts(modname, mid)
    prem, tgt = _pick_stmts(Path(gate_file), _scope_of(nodeid), expect_msg)
    base = _synth_out(Path(gate_file), nodeid, prem[1], expect_msg)
    expect_loc = mod.EXPECT_LOC[mid]

    # 在 FAILURES 区的前提位置行**之后**再插一条落在目标行的位置行（摘要区一字不改）
    extra = f"{gate_file}:{tgt[1]}: AssertionError: {expect_msg}"
    lines = base.splitlines()
    i = next(k for k, ln in enumerate(lines) if ln.startswith(f"{gate_file}:{prem[1]}:"))
    out = "\n".join(lines[: i + 1] + [extra] + lines[i + 1 :]) + "\n"

    print(f"── {harness} / {mid} · Codex round-1 LOW-1 的对照输入 ──")
    print(f"  expect_loc  : {expect_loc}（读自 {modname}.EXPECT_LOC）")
    print(f"  前提位置行  : 行 {prem[1]}  stmt:{prem[0]}")
    print(f"  额外位置行  : 行 {tgt[1]}  stmt:{tgt[0]}  ← Codex 加的这一条")
    print("  合成 out（逐行）:")
    for ln in out.splitlines():
        print(f"    | {ln}")

    v0, w0 = kill_identity(
        1, base, nodeid, expect_msg, gate_file=gate_file, require_gate_file=True, expect_loc=expect_loc
    )
    v1, w1 = kill_identity(
        1, out, nodeid, expect_msg, gate_file=gate_file, require_gate_file=True, expect_loc=expect_loc
    )
    print(f"\n  本卡 §一 的 after 输入（只有前提位置行）⇒ {v0}  |  {w0}")
    print(f"  Codex 的输入（多一条目标位置行）      ⇒ {v1}  |  {w1}")
    reproduced = not v0.startswith("KILLED") and v1.startswith("KILLED")
    print(f"\n  复现 Codex LOW-1: {'✅ 是' if reproduced else '⛔ 否（与 Codex 的描述不符，需人判）'}")
    print("  归属: `mutation_kill_identity._loc_identity()` 的 `expect_loc in tokens`（任一命中）—— 共用裁判面，T8-B 地盘，本卡未改它")
    return 0 if reproduced else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
