"""纯搬迁证明：HEAD 版 test 文件 vs (新模块 + 新 test) 的顶层节点 AST 逐条比对。

判据三条，任一不成立即停：
  1. 新模块 + 新 test 的顶层符号集合的**并集** == HEAD 版 test 的顶层符号集合（零丢失、零新增）
  2. 每个同名顶层节点的 ast.dump() 逐字符相同（含 docstring；= 代码零改动）
  3. test 函数名集合前后完全相同（防「切片静默删掉整条测试」）
"""

import ast, subprocess, sys
from pathlib import Path

W = "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills"
PRE_SHA = "17c14d2705e519d44cb7c4988c81a920b175d03f"  # ⛔ 钉语义值(T7B_TIP)，不钉位置锚 HEAD
REL = "backend/tests/skills/test_skill_portability_lint.py"

# ⛔ 位置锚 HEAD 在本卡 commit 后会指向改后版本 ⇒ 判据失效(实测 check_*: 前卡tip=0, FAIL)
old_src = subprocess.run(
    ["git", "-C", W, "show", f"{PRE_SHA}:{REL}"], capture_output=True, text=True, check=True
).stdout
new_test = Path(W, REL).read_text(encoding="utf-8")
new_mod = Path(W, "backend/tests/skills/skill_portability_lint.py").read_text(encoding="utf-8")


def toplevel(src):
    out = {}
    for n in ast.parse(src).body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out[n.name] = n
        elif isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name):
                    out[t.id] = n
        elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name):
            out[n.target.id] = n
    return out


O, T, M = toplevel(old_src), toplevel(new_test), toplevel(new_mod)

# ── 验伪锚：先证这套比对能抓到差异（人为改一个节点必须判不等）──
probe_a = ast.dump(ast.parse("X = 1").body[0])
probe_b = ast.dump(ast.parse("X = 2").body[0])
assert probe_a != probe_b, "验伪锚失效：ast.dump 分不出 X=1 与 X=2"
print("验伪锚 OK: ast.dump 能分辨 `X = 1` / `X = 2`")

overlap = set(T) & set(M)
print(f"前卡tip顶层符号={len(O)}  新test={len(T)}  新模块={len(M)}  两侧重名={len(overlap)}")
if overlap:
    print("⛔ 两侧重名（可能是旧副本没删）:", sorted(overlap))
    sys.exit(1)

union = set(T) | set(M)
lost, added = set(O) - union, union - set(O)
print(f"丢失={len(lost)}  新增={len(added)}")
if lost:
    print("⛔ 丢失:", sorted(lost))
if added:
    print("ℹ️  新增(应为空):", sorted(added))

diffs = [k for k in set(O) & union if ast.dump(O[k]) != ast.dump((T if k in T else M)[k])]
print(f"ast.dump 不等的同名节点 = {len(diffs)}")
if diffs:
    print("⛔ 内容变了:", sorted(diffs)[:20])

old_tests = {k for k in O if k.startswith("test_")}
new_tests = {k for k in T if k.startswith("test_")}
print(
    f"test 函数: 前卡tip={len(old_tests)} 新={len(new_tests)}  丢失={sorted(old_tests - new_tests)}  新增={sorted(new_tests - old_tests)}"
)

check_old = {k for k in O if k.startswith("check_")}
check_mod = {k for k in M if k.startswith("check_")}
check_tst = {k for k in T if k.startswith("check_")}
print(f"check_*: 前卡tip={len(check_old)} 模块={len(check_mod)} 留在test={len(check_tst)}（须 0）")

ok = (
    (not lost)
    and (not added)
    and (not diffs)
    and (not overlap)
    and old_tests == new_tests
    and check_mod == check_old
    and not check_tst
)
print("RESULT:", "PASS 纯搬迁、零漂移" if ok else "FAIL")
sys.exit(0 if ok else 1)
