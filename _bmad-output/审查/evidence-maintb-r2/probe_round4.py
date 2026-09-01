#!/usr/bin/env python3
"""round-4 抢救发现的三缝隙复现（先红）+ 整改后复验。"""

import subprocess
import sys
import tempfile
from pathlib import Path

W = Path("/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix")
sys.path.insert(0, str(W / "backend/tests/regression"))
import test_recap_scan_signals as t  # noqa: E402


def probe(name, build, want_block):
    tmp = Path(tempfile.mkdtemp(prefix=f"r4-{name}-", dir=Path(__file__).parent))
    vault = t.standard_vault(tmp)
    r = build(vault, tmp)
    first = next((ln for ln in r.stdout.splitlines() if "✗" in ln), "VERIFY PASS")
    ok = "✅" if (r.returncode != 0) == want_block else "❌"
    print(f"{ok} {name}: exit {r.returncode} (期望{'拦' if want_block else '放'}) · {first[:110]}")


def a_leading_space_fence(vault, tmp):
    """A: 前导空格的引用内列表围栏藏信号（Codex round-4 探针 A）。"""
    scan = t.collect_json(vault)
    report = t.write_report(vault, scan)
    lines = report.read_text(encoding="utf-8").splitlines()
    labels = t.SIGNAL_LABELS
    idx = [i for i, ln in enumerate(lines) if any(lb in ln for lb in labels)]
    core = [lines[i].lstrip("> ").lstrip("- ").strip() for i in range(idx[0], idx[-1] + 1)]
    body = [" > - ```"] + [" >   " + x for x in core] + [" >   ```"]
    out = lines[: idx[0]] + body + lines[idx[-1] + 1 :]
    report.write_text("\n".join(out) + "\n", encoding="utf-8")
    return t.run_verify(report)


def b_manifest_appendix(vault, tmp):
    """B: manifest 模式附录伪信号（Codex round-4 探针 B）。"""
    scan = t.collect_json(vault, "--manifest", str(t.make_manifest(vault)))
    report = t.write_report(vault, scan)
    with report.open("a", encoding="utf-8") as f:
        f.write("\n## 附录\n\n- 无来源结论：987654/2 派生角色成员缺来源锚点【实测】\n")
    return t.run_verify(report)


def c_cjk_heading_number(vault, tmp):
    """C: HIGH-6 标题行中文数字绕过（Codex round-4 探针 C）。"""
    scan = t.collect_json(vault)
    report = t.write_report(vault, scan)
    text = report.read_text(encoding="utf-8")
    report.write_text(
        text.replace("方向叙述：", "\n#### 派生子女 九十八万个 的说明\n\n方向叙述：", 1),
        encoding="utf-8",
    )
    return t.run_verify(report)


probe("A 前导空格引用内列表围栏藏信号", a_leading_space_fence, True)
probe("B manifest 附录伪无来源结论", b_manifest_appendix, True)
probe("C 标题行中文数字", c_cjk_heading_number, True)
