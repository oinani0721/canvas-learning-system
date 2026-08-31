#!/usr/bin/env python3
"""复现 Codex round-2 截断前的线索：引用内「列表项 + 围栏」形态。

构造 A: 信号行整体包进 `> - ``` … `> - ``` `（列表项围栏，Codex 的构造）
构造 B: `>   ``` `（缩进引用围栏）开栏形态
构造 C: 单元层面直接看 _strip_code_blocks 对各形态的输出
"""

import subprocess
import sys
import tempfile
from pathlib import Path

W = Path("/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix")
sys.path.insert(0, str(W / "backend/tests/regression"))
import test_recap_scan_signals as t  # noqa: E402

tmp = Path(tempfile.mkdtemp(prefix="codexhint-", dir=Path(__file__).parent))
vault = t.standard_vault(tmp)
scan = t.collect_json(vault)
report = t.write_report(vault, scan)
base = t.run_verify(report)
assert base.returncode == 0, base.stdout
text = report.read_text(encoding="utf-8")
lines = text.splitlines()
labels = ("未答问题年龄", "来源覆盖率", "无来源结论", "重复堆积")
idx = [i for i, ln in enumerate(lines) if any(lb in ln for lb in labels)]
start, end = idx[0], idx[-1]

import re as _re


def run_case(name, new_lines):
    out = lines[:start] + new_lines + lines[end + 1 :]
    report.write_text("\n".join(out) + "\n", encoding="utf-8")
    r = t.run_verify(report)
    probs = [ln for ln in r.stdout.splitlines() if "✗" in ln][:3]
    print(f"{name}: exit {r.returncode} · {probs if probs else 'VERIFY PASS'}")


# A: Codex 构造 — 列表项围栏，信号行剥掉原前缀后加 ">   "
body_a = ["> - ```"] + [
    ">   " + _re.sub(r"^[>\s]*-\s*", "", lines[i]) for i in range(start, end + 1)
] + [">   ```"]
run_case("A 列表项围栏 - ```/缩进内容", body_a)

# A2: 全部用 "- " 列表形态（更贴近标准信号行前缀）
body_a2 = ["> - ```"] + ["> - " + _re.sub(r"^[>\s]*-\s*", "", lines[i]) for i in range(start, end + 1)] + ["> - ```"]
run_case("A2 列表项围栏 - ```/- 内容", body_a2)

# C: 单元层面
sys.path.insert(0, str(W / "canvas-vault/.claude/skills/board-recap/scripts"))
import importlib.util

spec = importlib.util.spec_from_file_location("rs_probe", W / "canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py")
rs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rs)
cases = {
    "U1 '>- ```' 开栏+内容+'>- ```'": "> - ```\n> - 未答问题年龄：无据（无带时间戳批注）\n> - ```",
    "U2 '- ```' 裸列表围栏": "- ```\n- 未答问题年龄：无据（无带时间戳批注）\n- ```",
    "U3 '> > - ```' 两层": "> > - ```\n> > - x\n> > - ```",
}
for name, src in cases.items():
    got = rs._strip_code_blocks(src)
    print(f"{name}: 剥后={got!r}")
