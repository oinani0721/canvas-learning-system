#!/usr/bin/env python3
"""CARD-G3-9 负控的负控 —— 逐条抽掉对账脚本里的判据, 证明"声称的那条测试"确实变红。

不是"跑一遍有失败就算数": 每个变异体点名**它必须打红的那个 nodeid**, 并要求
① 该 nodeid FAILED  ② 其余 nodeid 不受牵连 (否则说明变异面过宽, 证明力不成立)。

纪律 (本仓既有教训):
  - 还原基准 = **变异前的 sha**, 不是 HEAD (脚本是新文件, HEAD 里根本没有)。
  - 跑前 / 跑后各落一次全文件 shasum, 逐字节比对。
  - 变异串必须在文件中**唯一**命中, 否则该变异作废 (改到了别处 = 结论不可归因)。
"""
import hashlib
import subprocess
import sys
from pathlib import Path

WT = Path("/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3")
SCRIPT = WT / "backend" / "scripts" / "g39_three_view_reconcile.py"
TESTFILE = "tests/regression/test_g39_three_view_reconcile.py"

# (变异名, 原串, 替换串, 必须变红的 nodeid)
MUTANTS = [
    (
        "M1_去掉_overview板级due对账",
        '            diffs.append(_diff("overview ↔ picker.due_nodes", f"boards[{b}].due", a, c, "cross-source"))',
        '            pass  # MUTANT M1',
        "test_negctl_overview_board_due_plus_one",
    ),
    (
        "M2_去掉_板序对账",
        '        diffs.append(\n'
        '            _diff("picker.top_boards ↔ overview.boards", "board_order", top_names, ov_ranked_prefix, "cross-source")\n'
        '        )',
        '        pass  # MUTANT M2',
        "test_negctl_picker_top_boards_order_swapped",
    ),
    (
        "M3_去掉_stats与明细长度对账",
        '        diffs.append(_diff("picker.stats ↔ picker.due_nodes", "due_count", p_stats_due, p_len_due, "cross-source"))',
        '        pass  # MUTANT M3',
        "test_negctl_stats_due_nodes_mismatch",
    ),
    (
        "M4_把corrupt降级成not-fetched豁免",
        '    if status not in OVERVIEW_COMPARABLE_STATUS:',
        '    if False:  # MUTANT M4 — 假绿: corrupt 被放行',
        "test_falsify_anchor_overview_corrupt_counts_as_semantic_diff",
    ),
    (
        "M5_把行序对账退化成集合比较",
        '        if ov_seq != expected:',
        '        if sorted(ov_seq) != sorted(expected):  # MUTANT M5',
        "test_node_order_mirrors_urgency_not_scan_order",
    ),
    (
        "M6_用isinstance判number（bool陷阱）",
        '    return type(v) is int or type(v) is float',
        '    return isinstance(v, (int, float))  # MUTANT M6',
        "test_dashboard_bool_is_not_a_js_number",
    ),
]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run_pytest(nodeid: str) -> tuple[int, str]:
    r = subprocess.run(
        [str(WT / "backend" / ".venv" / "bin" / "pytest"), "-q", "-p", "no:cacheprovider",
         f"{TESTFILE}::{nodeid}"],
        cwd=str(WT / "backend"), capture_output=True, text=True,
        env={"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1", "HOME": str(Path.home())},
    )
    return r.returncode, r.stdout + r.stderr


def main() -> int:
    baseline_sha = sha(SCRIPT)
    baseline_text = SCRIPT.read_text(encoding="utf-8")
    print(f"跑前 shasum: {baseline_sha}")
    print(f"还原基准 = 变异前 sha (脚本是新文件, HEAD 无此文件)\n")

    ok = True
    for name, old, new, nodeid in MUTANTS:
        hits = baseline_text.count(old)
        if hits != 1:
            print(f"[{name}] ⛔ 变异串命中 {hits} 次 (须恰好 1) — 该变异作废")
            ok = False
            continue
        SCRIPT.write_text(baseline_text.replace(old, new), encoding="utf-8")
        rc, out = run_pytest(nodeid)
        SCRIPT.write_text(baseline_text, encoding="utf-8")
        after = sha(SCRIPT)
        restored = "OK" if after == baseline_sha else f"⛔ 未还原 {after}"
        killed = rc != 0 and f"{nodeid}" in out and "failed" in out
        print(f"[{name}]")
        print(f"  点名 nodeid : {nodeid}")
        print(f"  变异后 rc   : {rc}  ⇒ {'KILLED (判据有牙齿)' if killed else '⛔ SURVIVED (判据空转!)'}")
        print(f"  还原        : {restored}")
        tail = [ln for ln in out.splitlines() if "passed" in ln or "failed" in ln]
        print(f"  pytest 摘要 : {tail[-1] if tail else '(无)'}")
        if not killed or after != baseline_sha:
            ok = False
        print()

    print(f"跑后 shasum: {sha(SCRIPT)}  (与跑前{'相同' if sha(SCRIPT) == baseline_sha else '不同 ⛔'})")
    print(f"\n结论: {'全部变异体被点名的那条断言打红 ⇒ 负控有牙齿' if ok else '⛔ 存在空转判据或未还原'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
