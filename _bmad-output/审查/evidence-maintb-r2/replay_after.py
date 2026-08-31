#!/usr/bin/env python3
"""CARD-维护B-R2 承重验证：在隔离拷贝上重放 8 条变异体，验证每条新门变红。

与 replay_survivors.py（先红基线）互补——本脚本跑在**整改后**代码上：
每条变体 = (名称, old, new, 期望变红的关键字)。全串行，还原逐字节自检。
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

MUTANTS: list[tuple[str, str, str, list[str]]] = [
    (
        "survivor-6 S1 `_NODATA_REASONS` 增「任意原因」",
        '    "数据源不可用",\n)',
        '    "数据源不可用",\n    "任意原因",\n)',
        ["test_domain_skill_sync_nodata_reasons_table", "test_domain_block_nodata_reason_outside_table"],
    ),
    (
        "survivor-7 S3 :1011 改单层剥离（含列表符剥离退化）",
        'bare = re.sub(r"^[>\\s]*(?:[-*+][^\\S\\n]+)?", "", ln)',
        'bare = re.sub(r"^>?[^\\S\\n]*", "", ln)',
        [
            "test_domain_block_multilevel_blockquote_fence",
            "test_domain_strip_code_blocks_unit_contract",
            "test_domain_block_list_item_fence_hides_signals",
        ],
    ),
    (
        "survivor-8 S4 允许式表增备注自由式",
        '        "skill:③段固定句式",\n    ),\n)',
        '        "skill:③段固定句式",\n    ),\n    (re.compile(r"^\\s*备注[：:].*派生.*$"), "skill:③段固定句式"),\n)',
        ["test_domain_block_freeform_derivation_note", "test_domain_derive_allow_entries_are_grounded"],
    ),
    (
        "old-1 删闭栏同字符条件（仅留长度）",
        'and mc.group("fence")[0] == fence[0]\n                and len(mc.group("fence")) >= len(fence)',
        'and len(mc.group("fence")) >= len(fence)',
        ["test_domain_block_fence_close_must_be_same_char"],
    ),
    (
        "⑦ 退化为原自由段式",
        'r"^[>\\s]*(?:\\d+\\s*个)?派生角色成员缺来源锚点[^。\\n0-9]*。?\\s*$"',
        'r"^[>\\s]*(?:\\d+\\s*个)?派生角色成员[^。\\n]*。?\\s*$"',
        ["test_domain_block_derive_clause_free_tail"],
    ),
    (
        "survivor-9 注记槽退化 `[^【】]*` 自由文本",
        '            note_slot = (\n'
        '                rf"(?:\\s*[·，,、]?\\s*"\n'
        "                rf\"(?:{'|'.join(re.escape(x) for x in _SIGNAL_TAIL_NOTES)}))?\"\n"
        "            )",
        '            note_slot = r"(?:[^【】]*)"',
        ["test_domain_block_signal_tail_note_outside_table"],
    ),
    (
        "survivor-10 `_SIGNAL_TAIL_NOTES` 增「另有仨条」",
        '_SIGNAL_TAIL_NOTES = ("口径一致",)',
        '_SIGNAL_TAIL_NOTES = ("口径一致", "另有仨条")',
        ["test_domain_skill_sync_signal_tail_notes_table"],
    ),
    (
        "⑧ 退化为原自由段式",
        're.compile(r"^[^。\\n0-9]*集中在派生角色成员[^。\\n0-9]*。?\\s*$")',
        're.compile(r"^[^。\\n]*集中在派生角色成员[^。\\n]*。?\\s*$")',
        ["test_domain_block_derive_clause_free_tail"],
    ),
]


def run_suite(tag: str) -> tuple[int, int, int, list[str]]:
    r = subprocess.run(
        [str(PYTEST), SUITE, "-q", "-rf", "-p", "no:cacheprovider",
         "-c", "/dev/null", f"--rootdir={COPY}/backend", f"--basetemp={SCRATCH}/bt-after"],
        cwd=COPY / "backend",
        capture_output=True, text=True,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        timeout=900,
    )
    out = r.stdout
    passed = sum(int(m) for m in re.findall(r"(\d+) passed", out))
    failed = sum(int(m) for m in re.findall(r"(\d+) failed", out))
    failed_ids = sorted(
        ln.split(" - ")[0].removeprefix("FAILED ").strip()
        for ln in out.splitlines() if ln.startswith("FAILED ")
    )
    (SCRATCH / "evidence" / f"replay-after-{tag}.out").write_text(out, encoding="utf-8")
    return r.returncode, passed, failed, failed_ids


def main() -> int:
    original = TARGET.read_bytes()
    sha = hashlib.sha256(original).hexdigest()
    print(f"拷贝树被测文件（整改后）sha256={sha[:12]}…")
    bad = 0
    for i, (name, old, new, expect) in enumerate(MUTANTS, 1):
        text = original.decode("utf-8")
        n = text.count(old)
        if n != 1:
            print(f"❌ {name}: old 串命中 {n} 次（须恰 1）")
            bad += 1
            continue
        TARGET.write_text(text.replace(old, new, 1), encoding="utf-8")
        try:
            rc, p, f, ids = run_suite(f"mutant-{i}")
        finally:
            TARGET.write_bytes(original)
        got = hashlib.sha256(TARGET.read_bytes()).hexdigest()
        assert got == sha, f"还原后字节与备份不同！"
        short = [x.split("::")[-1] for x in ids]
        missing = [e for e in expect if not any(e in s for s in short)]
        ok = f > 0 and not missing
        print(f"{'✅' if ok else '❌'} {name}: {f} failed → 门红: {[s for s in short if any(e in s for e in expect)] or '（无）'}")
        if missing:
            print(f"   ⛔ 期望变红但没红: {missing}（全部红: {short}）")
        if not ok:
            bad += 1
    print(f"\n{'全部承重' if not bad else f'{bad} 条问题'}（共 {len(MUTANTS)} 条变体）")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
