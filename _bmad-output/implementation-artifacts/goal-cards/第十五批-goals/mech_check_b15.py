#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第十五批卡文/短 goal 机械核（长度门之外的第二道；主 session 每次改卡文后重跑）。
逐卡：批次标记+卡号 / 两清单锚 / D-15 串 / APP 卡「pyright 保持 0」/ unit 基线路径 / 禁用词 / 旧字面量 / gpt-5.6（放行 grep -c 判据形态）/
       卡文全部 file:line 锚在主干树可解析且不越界 / 短 goal 字符数·行数·锚。
用法：python3 mech_check_b15.py [P1-A ...]（不带参数 = 全部 33 张）。输出每卡缺陷列表；干净卡不打印。
本核不比什么：不核 file:line 那一行是否含所写符号（regex 会把相邻符号错配，抽核实测 44 条「未命中」全为错配）；不核语义。
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # goal-cards/
TREE = ROOT.parent.parent.parent                        # feature-obsidian-hybrid-dev/
G = ROOT / "第十五批-goals"
sys.path.insert(0, str(G))
from gate_goal_length_b15 import ORDER, APP_CARDS, BATCH, D15, OLD_LITERALS, FORBIDDEN, UNIT_BASE  # noqa: E402

ANCHOR = re.compile(r"(?<![A-Za-z0-9_/.\-])((?:[A-Za-z0-9_\-]+/)*[A-Za-z0-9_\-]+\.(?:py|sh|yml|yaml|toml)):(\d{2,5})(?!\d)")


def card_id(ct):
    m = re.search(r"\[" + re.escape(BATCH) + r" / (CARD-[A-Za-z0-9\-]+)\]", ct)
    return m.group(1) if m else None


def resolve(f):
    for c in (TREE / f, TREE / "backend/app" / f, TREE / "backend" / f, TREE / "canvas-vault/.claude/skills" / f,
              TREE / "canvas-vault/.claude/scripts" / f, TREE / "scripts" / f):
        if c.exists():
            return c
    base = Path(f).name
    hits = [p for p in list((TREE / "backend").rglob(base)) + list((TREE / "canvas-vault/.claude").rglob(base)) + list((TREE / "scripts").rglob(base))
            if p.is_file() and "/.venv/" not in str(p) and "node_modules" not in str(p)]
    return hits[0] if len(hits) == 1 else None


def check(key):
    issues = []
    md = G / f"{key}.md"
    gl = G / "_goal" / f"{key}.txt"
    if not md.exists():
        return ["卡文缺"]
    ct = md.read_text(encoding="utf-8")
    cid = card_id(ct)
    if not cid:
        issues.append(f"卡文缺批次标记 [{BATCH} / CARD-…]")
    for a in ("本卡未证明什么", "台账待登记条目"):
        if a not in ct:
            issues.append(f"卡文缺「{a}」")
    if D15 not in ct:
        issues.append("卡文缺 D-15 串")
    if key in APP_CARDS and "pyright 保持 0" not in ct:
        issues.append("卡文缺「pyright 保持 0」")
    if UNIT_BASE not in ct:
        issues.append(f"卡文缺 unit 基线 {UNIT_BASE}")
    for w in FORBIDDEN:
        n = ct.count(w)
        if n:
            issues.append(f"卡文含禁用词「{w}」×{n}")
    for o in OLD_LITERALS:
        if o in ct:
            issues.append(f"卡文含旧字面量 {o!r}")
    if "gpt-5.6" in ct.replace("grep -c 'gpt-5.6'", ""):
        issues.append("卡文含 gpt-5.6（非 grep -c 判据形态）")
    if "\x00" in ct:
        issues.append("卡文含 NUL")
    anchors = {(f, int(l)) for f, l in ANCHOR.findall(ct) if "no_such" not in f}
    unresolved, oob = [], []
    for f, l in sorted(anchors):
        p = resolve(f)
        if p is None:
            unresolved.append(f)
            continue
        n = p.read_text(encoding="utf-8", errors="replace").count("\n") + 1
        if l > n:
            oob.append(f"{f}:{l}>{n}")
    if oob:
        issues.append(f"file:line 越界 {len(oob)}: {oob[:4]}")
    third = [u for u in unresolved if not any(u.startswith(x) for x in ("backend/", "scripts/", "canvas-vault/"))]
    real = [u for u in unresolved if u not in third]
    if real:
        issues.append(f"file:line 文件不存在 {len(real)}: {real[:4]}")
    if not gl.exists():
        issues.append("短 goal 缺")
    else:
        g = gl.read_text(encoding="utf-8").rstrip("\n")
        n, ln = len(g), g.count("\n") + 1
        if n > 3800:
            issues.append(f"短 goal {n} 字符 > 3800 ⛔")
        elif n > 3600:
            issues.append(f"短 goal {n} 字符 > 3600（建议裁）")
        if ln != 7:
            issues.append(f"短 goal {ln} 行 ≠ 7")
        if not g.startswith("/goal"):
            issues.append("短 goal 不以 /goal 开头")
        if str(md) not in g:
            issues.append("短 goal 缺卡文绝对路径")
        if cid and f"[{BATCH} / {cid}]" not in g:
            issues.append("短 goal 缺批次标记/卡号（须与卡文一致）")
        if "不 push" not in g:
            issues.append("短 goal 缺「不 push」")
        lane = key.rsplit("-", 1)[0]
        if f"复核第十五批 {lane}" not in g:
            issues.append(f"短 goal 缺「复核第十五批 {lane}」")
        if D15 not in g:
            issues.append("短 goal 缺 D-15 串")
        if key in APP_CARDS and "pyright 保持 0" not in g:
            issues.append("短 goal 缺「pyright 保持 0」")
        for w in FORBIDDEN:
            if w in g:
                issues.append(f"短 goal 含禁用词「{w}」")
        for o in OLD_LITERALS:
            if o in g:
                issues.append(f"短 goal 含旧字面量 {o!r}")
        if "gpt-5.6" in g.replace("grep -c 'gpt-5.6'", ""):
            issues.append("短 goal 含 gpt-5.6")
    return issues


def main():
    keys = sys.argv[1:] or ORDER
    report = {k: check(k) for k in keys}
    clean = [k for k, v in report.items() if not v]
    print(f"机械核：干净 {len(clean)}/{len(keys)}")
    for k in keys:
        if report[k]:
            print(f"\n{k}:")
            for i in report[k]:
                print("   -", i)
    out = G / ".mech_check_last.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    sys.exit(0 if len(clean) == len(keys) else 1)


if __name__ == "__main__":
    main()
