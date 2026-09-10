#!/usr/bin/env python3
"""只读：按四套 harness 的常量表达式复算它们会写到哪些绝对路径。

⛔ 不 import 那四个模块（import 会跑模块顶层副作用）——按 `__file__` 语义手算。
"""
from __future__ import annotations

import pathlib
import sys

TREE = pathlib.Path(__file__).resolve().parents[3]
SCRIPTS = TREE / "backend" / "scripts"

# (harness, 常量名, 相对 <tree> 的路径)  —— 与各脚本源码逐行对齐，出处见右侧注释
TARGETS = [
    ("g32b", "SKILL", "canvas-vault/.claude/skills/quiz-answer/SKILL.md"),      # :41-42
    ("g32b", "BRIDGE", "canvas-vault/.claude/scripts/fsrs_bridge.py"),          # :41,:43
    ("g32cb", "SKILL", "canvas-vault/.claude/skills/quiz-answer/SKILL.md"),     # :78-79
    ("g32cb", "LEDGER_TEST", "backend/tests/regression/test_g3_2_review_ledger.py"),  # :81 (cwd=backend)
    ("g32ccr1", "SKILL", "canvas-vault/.claude/skills/quiz-answer/SKILL.md"),   # :55-56
    ("g32ccr1", "LEDGER_TEST", "backend/tests/regression/test_g3_2_review_ledger.py"),  # :60
    ("g33", "SKILL", "canvas-vault/.claude/skills/quiz-answer/SKILL.md"),       # :56-58
    ("g33", "BRIDGE", "canvas-vault/.claude/scripts/fsrs_bridge.py"),           # :56-59
]

LIVE_VAULT = pathlib.Path(
    "/Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault"
).resolve()

bad = 0
print(f"LANE TREE = {TREE}")
print(f"LIVE VAULT (禁写) = {LIVE_VAULT}")
seen: set[pathlib.Path] = set()
for hn, const, rel in TARGETS:
    p = (TREE / rel).resolve()
    inside = TREE in p.parents
    live = LIVE_VAULT == p or LIVE_VAULT in p.parents
    ok = inside and not live
    bad += 0 if ok else 1
    seen.add(p)
    print(f"{hn:9s} {const:12s} in_lane={inside!s:5s} in_live={live!s:5s} exists={p.exists()!s:5s} {p}")

print("--- 去重后的全部写入面 ---")
for p in sorted(seen):
    print(p)
print(f"VERDICT: {'PASS' if bad == 0 else f'FAIL({bad})'}")
sys.exit(0 if bad == 0 else 1)
