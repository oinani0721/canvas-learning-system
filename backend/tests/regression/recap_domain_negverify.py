#!/usr/bin/env python3
"""维护卡 B · 负验证（变异）脚本 —— 证明双向门是**承重**的，不是摆设。

⛔ 三条铁律，全部来自踩过的坑：
  1. **必须串行**（MEMORY `reference_mutation_script_serial_only`）：本脚本原地改
     被测文件再还原，并发跑会让 B 的还原把 A 的 mutation 写回，而测试照样全绿。
     脚本自带互斥锁，重入直接拒绝。
  2. **变体必须禁掉该性质的全部防线**（MEMORY `reference_mutation_must_disable_all_layers`）：
     只退化一层时纵深防御会让测试仍绿，从而误判「门非承重」去改本来正确的测试。
  3. **还原后必须与备份逐字节相同**——这道自检本身抓出过"还原不干净"。

用法: python recap_domain_negverify.py   （无参数；退出码 0 = 全部如期变红）
"""

from __future__ import annotations

import hashlib
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TARGET = ROOT / "canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py"
PYTEST = ROOT / "backend/.venv/bin/pytest"
SUITE = "tests/regression/test_recap_scan_signals.py"
LOCK = Path(tempfile.gettempdir()) / "recap-domain-negverify.lock.d"

# 每条变体 = (名称, [(原文, 替换), ...], 期望至少变红的用例关键字)
# ⛔ 列表里给出的是**该性质的全部防线**，一次全禁——只禁一层会得到假绿。
MUTANTS: list[tuple[str, list[tuple[str, str]], str]] = [
    (
        "survivor-1 围栏闭合退回宽松判定（E1 全线：长度 + 尾随空白 两条一起禁）",
        [
            (
                'close_re = re.compile(r"^ {0,3}(?P<fence>`{3,}|~{3,})[^\\S\\n]*$")',
                'close_re = re.compile(r"^ {0,3}(?P<fence>`{3,}|~{3,})")',
            ),
            (
                'if (\n                mc\n                and mc.group("fence")[0] == fence[0]\n'
                '                and len(mc.group("fence")) >= len(fence)\n            ):',
                "if mc:",
            ),
        ],
        "four_fence_short_close or fence_close_needs_trailing_blank_only",
    ),
    (
        "survivor-2 规模行允许式去掉行尾锚（H-2 前半全线）",
        [
            (
                'r"^[>\\s]*\\d+\\s*成员（\\d+\\s*种子\\s*\\+\\s*\\d+\\s*派生，\\d+\\s*占位）"\n                r"\\s*/\\s*\\d+\\s*批注\\s*/?\\s*$"',
                'r"^[>\\s]*\\d+\\s*成员（\\d+\\s*种子\\s*\\+\\s*\\d+\\s*派生，\\d+\\s*占位）"',
            )
        ],
        "scale_line_tail_append",
    ),
    (
        "survivor-3 种子行只查形状不绑值（H-2 后半全线）",
        [("    _verify_seed_ledger_counts(text, scan, problems)\n", "")],
        "seed_ledger_fake_count",
    ),
    (
        "survivor-4 信号行尾部退回开放式 + 恢复字符黑名单（H-3 全线）",
        [
            (
                "rf\"{sig['denominator']}\\s*{re.escape(tail)}\"",
                "rf\"{sig['denominator']}\\s*(?P<tail>[^【】]*)\"",
            )
        ],
        "signal_tail_append",
    ),
    (
        "survivor-5 D2 叙述域计数绑定整体关闭（本卡原始命题）",
        [("    _verify_prose_counts(text, scan, problems)\n", "")],
        "bare_count_in_prose",
    ),
]


def run_suite(keyword: str) -> tuple[int, str, int, int]:
    """跑目标用例，返回 (rc, 输出尾部, 收集到的用例数, 失败数)。

    ⛔ Codex round-1 HIGH: 原实现只看 `rc != 0` 就判「如期变红」——
    pytest 的 rc=5 是**一个用例都没匹配到**（`-k` 写错就会这样），
    rc=2/3/4 是用法错误/内部错误。把它们当成"门变红了"正是
    MEMORY `reference_gate_design_pitfalls` 的头号形态：
    **把「没有发生」当成「验证通过」**。现在解析出真实的 passed/failed 计数，
    要求"确实收集到用例"且"确实有失败"才算变红。
    """
    r = subprocess.run(
        [str(PYTEST), SUITE, "-q", "-p", "no:cacheprovider", "-k", keyword],
        cwd=ROOT / "backend",
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        timeout=600,
    )
    out = r.stdout
    failed = sum(int(m) for m in re.findall(r"(\d+) failed", out))
    passed = sum(int(m) for m in re.findall(r"(\d+) passed", out))
    return r.returncode, out[-400:], passed + failed, failed


def main() -> int:
    try:
        LOCK.mkdir()  # 原子互斥: 已存在即抛
    except FileExistsError:
        print(f"⛔ 另一个负验证进程正在跑（锁: {LOCK}）。变异脚本必须串行——见脚本 docstring。")
        return 2
    try:
        original = TARGET.read_bytes()
        backup_sha = hashlib.sha256(original).hexdigest()

        rc0, out0, n0, f0 = run_suite("domain_")
        if rc0 != 0 or f0 or n0 == 0:
            print(f"⛔ 基线不可信（rc={rc0} 收集={n0} 失败={f0}）:\n{out0}")
            return 2
        print(f"基线: 双向门全绿 · 被测文件 sha256={backup_sha[:12]}…\n")

        failures = 0
        for name, subs, keyword in MUTANTS:
            text = original.decode("utf-8")
            for old, new in subs:
                if old not in text:
                    print(f"❌ {name}: 变异点未命中（实现已变？）——按失败计")
                    failures += 1
                    text = None
                    break
                text = text.replace(old, new, 1)
            if text is None:
                continue
            TARGET.write_text(text, encoding="utf-8")
            try:
                rc, out, n, f = run_suite(keyword)
            finally:
                TARGET.write_bytes(original)  # 立刻还原，异常也还原
            got = hashlib.sha256(TARGET.read_bytes()).hexdigest()
            assert got == backup_sha, f"还原后字节与备份不同！{got[:12]} != {backup_sha[:12]}"
            # ⛔ 必须是"收集到用例 且 确实有失败"，不能只看 rc != 0
            if n == 0:
                print(f"❌ {name}: `-k {keyword}` 一个用例都没匹配到（rc={rc}）——这不是变红")
                failures += 1
            elif f == 0:
                print(f"❌ {name}: 变异后 {n} 个用例仍全绿 = 该门不承重\n{out}")
                failures += 1
            else:
                print(f"✅ {name}: 如期变红（{f}/{n} 失败）")

        print(f"\n{'全部承重' if not failures else f'{failures} 条未承重'}（共 {len(MUTANTS)} 条变体）")
        return 1 if failures else 0
    finally:
        LOCK.rmdir()


if __name__ == "__main__":
    sys.exit(main())
