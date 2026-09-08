#!/usr/bin/env python3
"""筛出 `expect_loc` 可能锚在**构造前提断言**上的条目（Z2-M15 假杀的同型）。

⛔ 为什么需要这道筛：位置判据挡住了「前提断言与目标断言在**不同**行」这一形态
（Y1-B HIGH-1），但挡不住「回填时就把位置绑到了前提断言上」——那样判据是自洽的，
结论却仍然是假杀。独立复核 2026-09-08 点名 `M89`/`M90`；本脚本把它做成**可复跑的
判据**，而不是一次性人工分析（手工查出来的不变量不写成判据 = 没查）。

判据（三条同时成立才算可疑，逐条都有理由，⛔ 不是「像前提就算」）：
  ① `expect_msg` 为空 —— 原作者当年也没能给这条绑出身份，说明该断言没有可辨识的消息；
  ② 该位置是它所在测试函数里的**第 1 条 `assert`** —— 构造段通常排在最前；
  ③ 该断言**期望子进程成功**（`returncode == 0`）—— 变异一旦让写点失败，它必然先红，
     而目标断言从不执行。反之期望 `!= 0` 的断言本身就是被测性质，不算前提。

⚠️ 单看任一条都会误伤：`M112` 的 `assert r1.returncode == 0, "来源为空但事实自洽
必须仍能恢复"` 满足 ③ 却**就是**被测性质；`M11` 满足 ② 却期望失败。三条同时成立的
才报出来。报出来的**不自动改判**，要人对着变异意图与门源码确认后写进豁免表。
"""
from __future__ import annotations

import ast
import importlib.util
import pathlib
import sys

TREE = pathlib.Path(__file__).resolve().parents[3]
SCRIPTS = TREE / "backend" / "scripts"
GATE = TREE / "backend" / "tests" / "regression" / "test_g3_2_review_ledger.py"
sys.path.insert(0, str(SCRIPTS))
from mutation_kill_identity import stmt_fingerprints  # noqa: E402

spec = importlib.util.spec_from_file_location("g32b_screen", SCRIPTS / "g32b_mutation_gates.py")
g32b = importlib.util.module_from_spec(spec)
sys.modules["g32b_screen"] = g32b
spec.loader.exec_module(g32b)

src = GATE.read_text(encoding="utf-8")
lines = src.splitlines()
tree = ast.parse(src)
fps = stmt_fingerprints(GATE)

func_asserts: dict[str, list[int]] = {}
for n in ast.walk(tree):
    if isinstance(n, ast.FunctionDef):
        a = sorted(x.lineno for x in ast.walk(n) if isinstance(x, ast.Assert))
        if a:
            func_asserts[n.name] = a

# ⛔ 位置来源取自 **probe 存档**（全部 138 条的实测 `file:lineno`），**不是** `EXPECT_LOC`。
# 只扫 `EXPECT_LOC` 的话，一条被判为「锚在前提上」而移进豁免表的条目就从筛选面里消失了
# ⇒ 修完之后这道判据恒返 0，变成死判据（它要防的东西正是「已登记的那两条」）。
import re as _re

_CAND = _re.compile(r"^EXPECT_LOC_CANDIDATE\t(?P<tag>\S+)\t(?P<loc>[^\t]*)\t(?P<rc>\d+)\t(?P<raw>[^\t]*)$", _re.M)
_probes = sorted((TREE / "_bmad-output" / "审查" / "evidence-mutkill-r2").glob("probe-g32b-*.txt"),
                 key=lambda x: x.stat().st_mtime)
_probes = [x for x in _probes if "作废" not in x.read_text(encoding="utf-8", errors="replace")[-400:]]
if not _probes:
    print("⛔ 找不到可用的 probe 存档 —— 抽取面为空不等于「没问题」")
    sys.exit(1)
_obs = {m["tag"]: (m["raw"], int(m["rc"])) for m in _CAND.finditer(_probes[-1].read_text(encoding="utf-8"))}
print(f"位置来源: {_probes[-1].name}（{len(_obs)} 条实测位置）")
if len(_obs) != len(g32b.MUTATIONS):
    print(f"⛔ probe 里只有 {len(_obs)} 条，与 MUTATIONS {len(g32b.MUTATIONS)} 条对不上 —— 抽取面不完整")
    sys.exit(1)

suspects, checked = [], 0
for mut in g32b.MUTATIONS:
    tag = mut[0]
    raw, rc = _obs.get(tag, ("", 0))
    if rc != 1 or ":" not in raw:
        continue
    _path, _, _lno = raw.rpartition(":")
    if pathlib.Path(_path).name != GATE.name:
        continue
    checked += 1
    ln = int(_lno)
    text = lines[ln - 1].strip()
    owner = next((f for f, a in func_asserts.items() if ln in a), None)
    if owner is None:
        continue
    c1 = g32b.EXPECT_MSG.get(tag) is None
    c2 = func_asserts[owner][0] == ln
    c3 = "returncode == 0" in text and "!= 0" not in text
    if c1 and c2 and c3:
        suspects.append((tag, mut[4], owner, ln, text))

print(f"已筛 {checked} 条已绑位置的变异")
print(f"三条判据同时成立（可疑锚在构造前提上）: {len(suspects)} 条")
for tag, gate, owner, ln, text in sorted(suspects):
    print(f"  ⚠️ {tag}\n     门 {gate}\n     位置 {owner}:{ln} 第 1/{len(func_asserts[owner])} 条 assert\n     {text[:110]}")
exempt = [t for t, *_ in suspects if t in g32b.EXPECT_LOC_EXEMPT and t not in g32b.EXPECT_LOC]
print(f"其中已登记进 EXPECT_LOC_EXEMPT 的: {len(exempt)}/{len(suspects)}  {exempt}")
print(f"VERDICT: {'PASS（全部已登记）' if len(exempt) == len(suspects) else f'⛔ 有 {len(suspects) - len(exempt)} 条仍绑在可疑锚上'}")
sys.exit(0 if len(exempt) == len(suspects) else 1)
