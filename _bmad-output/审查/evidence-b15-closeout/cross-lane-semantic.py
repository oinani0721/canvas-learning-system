#!/usr/bin/env python3
"""跨车道语义等价核验（D-15 r1 H-3 修复）。

口径（对每条车道相对 B15 基线 9c4e7e82 改过的**代码文件**，排除 _bmad-output）：
  1. .py 双可解析 ⇒ `ast.dump(ast.parse(x))` 相等判 EQUIV（对 ruff-format 重排免疫）；
  2. 双不可解析或非 .py ⇒ 去全部空白后文本相等判 EQUIV；
  3. 否则：若文件属**声明例外**（多写者并集面 / 未合车道加固）⇒ EXCEPTION（须与登记一致）；再否则 ⇒ FAIL。
输出末行：`verdict=PASS/FAIL(...)` + 计数。用法：python3 cross-lane-semantic.py <candidate_repo>
"""
import ast, subprocess, sys

W = "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees"
BASE = "9c4e7e82"
C = sys.argv[1] if len(sys.argv) > 1 else f"{W}/batch15-integ"
LANES = {f"p{i}": d for i, d in enumerate(
    ["p1-storage","p2-outbox","p3-deploy","p4-fsrs","p5-review",
     "p6-skills-w","p7-skills-x","p8-backend","p9-testinfra","p10-docs"], 1)}
# 声明例外：路径 → 理由（须在台账 §一.b 登记）
EXCEPTIONS = {
    "backend/scripts/gold_set_manifest_tool.py": "P9 车道 r3-r20 加固未合（转第十六批）",
    "backend/scripts/run_memory_retrieval_regression.py": "P9 同上",
    "backend/scripts/run_vault_retrieval_regression.py": "P9 同上",
    "backend/tests/regression/test_gold_set_manifest_g413.py": "P9 同上",
    "backend/app/clients/neo4j_client.py": "多写者并集面（P1×P2）",
    "backend/app/services/memory_service.py": "多写者并集面（P1×P2）",
    "backend/app/services/episode_worker.py": "多写者并集面（P1×P2）",
    "backend/app/graphiti/canvas_episode.py": "多写者并集面",
    "backend/tests/unit/test_neo4j_client.py": "多写者并集面",
    "docs/release-evidence/README.md": "多写者并集面（P5/P10）",
}

def run(args, cwd):
    return subprocess.run(["git"] + args, cwd=cwd, capture_output=True).stdout

def blob(cwd, ref, path):
    return subprocess.run(["git", "show", f"{ref}:{path}"], cwd=cwd, capture_output=True).stdout

def norm_py(b: bytes):
    try:
        return ast.dump(ast.parse(b.decode("utf-8")))
    except Exception:
        return None

def norm_ws(b: bytes) -> str:
    return b.decode("utf-8", "replace").replace(" ", "").replace("\t", "").replace("\n", "").replace("\r", "")

equiv_n = diff_n = exc_n = fail_n = 0
print(f"# candidate={C} head={run(['rev-parse','--short=8','HEAD'],C).decode().strip()}")
for lane, d in LANES.items():
    L = f"{W}/card-{d}"
    tip = run(["rev-parse", "HEAD"], L).decode().strip()
    files = [f for f in run(["diff", "--name-only", "-z", f"{BASE}..HEAD", "--", ".", ":(exclude)_bmad-output"], L).decode("utf-8","surrogateescape").split("\0") if f]
    for f in files:
        a = blob(C, "HEAD", f); b = blob(L, "HEAD", f)
        if f.endswith(".py"):
            na, nb = norm_py(a), norm_py(b)
            same = (na is not None and na == nb)
        else:
            same = norm_ws(a) == norm_ws(b)
        if same:
            equiv_n += 1
        else:
            if f in EXCEPTIONS:
                exc_n += 1
                print(f"  [EXCEPTION] {lane} {f} —— {EXCEPTIONS[f]}")
            else:
                diff_n += 1
                print(f"  [DIFF] {lane} {f}（无声明例外，需归因）")
total = equiv_n + diff_n + exc_n
verdict = "PASS" if diff_n == 0 else f"FAIL({diff_n})"
print(f"\nchecked={total} equiv={equiv_n} exceptions={exc_n} undecided_diff={diff_n}")
print(f"verdict={verdict}")
