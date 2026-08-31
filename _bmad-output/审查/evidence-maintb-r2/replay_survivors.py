#!/usr/bin/env python3
"""CARD-维护B-R2 (a): 隔离拷贝上串行重放 6 个变异体，记「先红前基线」。

期望（= 复核裁定 F-4 的重放）：S1/S3/S4 变异后全套件 passed/failed 集合与原版
逐字相同（门没锁住 = survivor 仍存活）；3 个旧 survivor 按现结构等价重放，
已被第七批新门锁住者应出现新增红（记录实况，不预设）。
串行铁律：本脚本是唯一碰拷贝树 recap_scan.py 的进程；每条变异后立即还原并逐字节自检。
"""

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

SCRATCH = Path(__file__).resolve().parent
COPY = SCRATCH / "replay"
TARGET = COPY / "canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py"
PYTEST = Path(
    "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/"
    "card-v2-recapfix/backend/.venv/bin/pytest"
)
SUITE = "tests/regression/test_recap_scan_signals.py"

MUTANTS: list[tuple[str, str, str]] = [
    (
        "S1 _NODATA_REASONS 增「任意原因」",
        '    "数据源不可用",\n)',
        '    "数据源不可用",\n    "任意原因",\n)',
    ),
    (
        "S3 多层引用只剥一层",
        'bare = re.sub(r"^[>\\s]*", "", ln)',
        'bare = re.sub(r"^>?[^\\S\\n]*", "", ln)',
    ),
    (
        "S4 derive_ok 增「备注：…派生」允许式",
        '            re.compile(r"^[^。\\n]*集中在派生角色成员[^。\\n]*。?\\s*$"),\n        )',
        '            re.compile(r"^[^。\\n]*集中在派生角色成员[^。\\n]*。?\\s*$"),\n'
        '            re.compile(r"^\\s*备注[：:].*派生.*$"),\n        )',
    ),
    (
        "old-1 删闭栏同字符条件（仅留长度）",
        'and mc.group("fence")[0] == fence[0]\n                and len(mc.group("fence")) >= len(fence)',
        'and len(mc.group("fence")) >= len(fence)',
    ),
    (
        "old-2 tips_by_node 改取第一个节点值",
        "want = tips_by_node[node]",
        "want = next(iter(tips_by_node.values()))",
    ),
    (
        "old-3 _D2_EXEMPT_SECTIONS 增「你现在可以做的」（=旧 _D2_SECTIONS 砍半的现结构等价）",
        '    "数据来源与新鲜度",\n)',
        '    "数据来源与新鲜度",\n    "你现在可以做的",\n)',
    ),
]


def run_suite(tag: str) -> tuple[int, int, int, list[str]]:
    r = subprocess.run(
        [
            str(PYTEST),
            SUITE,
            "-q",
            "-rf",
            "-p",
            "no:cacheprovider",
            "-c",
            "/dev/null",
            f"--rootdir={COPY}/backend",
            f"--basetemp={SCRATCH}/bt-replay",
        ],
        cwd=COPY / "backend",
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        timeout=900,
    )
    out = r.stdout
    passed = sum(int(m) for m in re.findall(r"(\d+) passed", out))
    failed = sum(int(m) for m in re.findall(r"(\d+) failed", out))
    failed_ids = sorted(
        ln.split(" - ")[0].removeprefix("FAILED ").strip()
        for ln in out.splitlines()
        if ln.startswith("FAILED ")
    )
    (SCRATCH / "evidence" / f"replay-{tag}.out").write_text(out, encoding="utf-8")
    return r.returncode, passed, failed, failed_ids


def main() -> int:
    original = TARGET.read_bytes()
    sha = hashlib.sha256(original).hexdigest()
    print(f"拷贝树被测文件 sha256={sha[:12]}…")

    rc0, p0, f0, ids0 = run_suite("baseline")
    print(f"原版基线: rc={rc0} {p0} passed / {f0} failed")
    if ids0:
        print("原版失败集:", *ids0, sep="\n  ")

    results = {"baseline": {"rc": rc0, "passed": p0, "failed": f0, "failed_ids": ids0}}
    for i, (name, old, new) in enumerate(MUTANTS, 1):
        text = original.decode("utf-8")
        n = text.count(old)
        if n != 1:
            print(f"❌ {name}: old 串命中 {n} 次（须恰 1）——变异点定义有误")
            results[name] = {"error": f"old-hit={n}"}
            continue
        TARGET.write_text(text.replace(old, new, 1), encoding="utf-8")
        try:
            rc, p, f, ids = run_suite(f"mutant-{i}")
        finally:
            TARGET.write_bytes(original)
        got = hashlib.sha256(TARGET.read_bytes()).hexdigest()
        assert got == sha, f"还原后字节与备份不同！{got[:12]} != {sha[:12]}"
        same = p == p0 and ids == ids0
        verdict = "⛔ SURVIVOR（失败集与原版逐字相同）" if same else "🔴 有新增红（已被某门锁住）"
        print(f"{name}: rc={rc} {p} passed / {f} failed → {verdict}")
        new_reds = [x for x in ids if x not in ids0]
        if new_reds:
            print("  新增红:", *new_reds, sep="\n    ")
        results[name] = {
            "rc": rc,
            "passed": p,
            "failed": f,
            "failed_ids": ids,
            "survivor": same,
            "new_reds": new_reds,
        }

    out = SCRATCH / "evidence" / "replay-survivors-result.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n结果存档: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
