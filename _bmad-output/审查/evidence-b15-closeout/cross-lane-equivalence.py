#!/usr/bin/env python3
"""B15 收口：跨车道文件等价核验（可重跑）。
口径：对每条车道，取 lane 相对 B15 基线 9c4e7e82 改过的**代码文件**（排除 _bmad-output），
逐个与候选树 HEAD 的同路径文件比对字节；对不等的文件，逐条核验「该车道在该文件上加过的行
（strip 归一化、len>=12）全部仍在候选树文件中」＝交集已并集化（多写者声明面）。
用法：python3 cross-lane-equivalence.py [candidate_repo]  （默认 = 本仓）
"""
import subprocess, sys, os, difflib
BASE = "9c4e7e82"
W = "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees"
C = sys.argv[1] if len(sys.argv) > 1 else f"{W}/batch15-integ"
LANES = {f"p{i}": d for i, d in enumerate(
    ["p1-storage","p2-outbox","p3-deploy","p4-fsrs","p5-review",
     "p6-skills-w","p7-skills-x","p8-backend","p9-testinfra","p10-docs"], 1)}

def run(args, cwd):
    return subprocess.run(["git"]+args, cwd=cwd, capture_output=True, text=True).stdout

print(f"# candidate={C}")
print(f"# candidate_head={run(['rev-parse','HEAD'],C).strip()}")
bad = 0
for lane, d in LANES.items():
    L = f"{W}/card-{d}"
    tip = run(["rev-parse","HEAD"], L).strip()
    files = [f for f in run(["diff","--name-only",f"{BASE}..HEAD","--",".",":(exclude)_bmad-output"], L).splitlines() if f]
    differs = []
    for f in files:
        a = subprocess.run(["git","show",f"HEAD:{f}"], cwd=C, capture_output=True).stdout
        b = subprocess.run(["git","show",f"HEAD:{f}"], cwd=L, capture_output=True).stdout
        if a != b:
            differs.append(f)
    print(f"\n## {lane} (tip {tip[:8]}): files={len(files)} identical={len(files)-len(differs)} differs={len(differs)}")
    for f in differs:
        base = subprocess.run(["git","show",f"{BASE}:{f}"], cwd=L, capture_output=True, text=True).stdout
        tipf = subprocess.run(["git","show",f"HEAD:{f}"], cwd=L, capture_output=True, text=True).stdout
        cand = subprocess.run(["git","show",f"HEAD:{f}"], cwd=C, capture_output=True, text=True).stdout
        cand_lines = set(l.strip() for l in cand.splitlines() if l.strip())
        added = [l[1:].strip() for l in difflib.unified_diff(base.splitlines(), tipf.splitlines(), lineterm="", n=0)
                 if l.startswith("+") and not l.startswith("+++")]
        added = [a for a in added if len(a) >= 12]
        miss = [a for a in added if a not in cand_lines]
        verdict = "UNION-OK" if not miss else f"MISSING={len(miss)}"
        if miss: bad += 1
        print(f"   - {f}: lane-added={len(added)} present_in_candidate={len(added)-len(miss)} {verdict}")
        for m in miss[:3]:
            print(f"       MISSING: {m[:120]}")
print(f"\n# verdict={'PASS' if bad==0 else 'FAIL('+str(bad)+')'}")
