"""核「既有 60 条 headed 参数逐字未动」——AST 逐元素 dump 比对。

口径比 literal_eval 更严格且更宽用：含 `chr()` 拼接的元素（本表里有两条）literal_eval
会抛 ValueError，而 dump 能逐字比。
"""

import ast
import subprocess
import warnings

warnings.filterwarnings("ignore")

TG = "backend/tests/regression/test_g3_2_review_ledger.py"
PREV = "a05732c9"


def prev_elems():
    src = subprocess.run(
        ["git", "show", f"{PREV}:{TG}"], capture_output=True, text=True, check=True
    ).stdout
    for n in ast.parse(src).body:
        if isinstance(n, ast.FunctionDef) and n.name == "test_g33r2_harness_tree_no_pyyaml_never_returns_a_tree":
            for d in n.decorator_list:
                if isinstance(d, ast.Call) and len(d.args) == 2 and isinstance(d.args[1], ast.List):
                    return d.args[1].elts
    raise SystemExit("PREV 侧锚不到 parametrize 列表")


def head_elems():
    for n in ast.parse(open(TG, encoding="utf-8").read()).body:
        if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "_HEADED_LINES":
            return n.value.elts
    raise SystemExit("HEAD 侧锚不到 _HEADED_LINES")


a = [ast.dump(e) for e in prev_elems()]
b = [ast.dump(e) for e in head_elems()]
print(f"PREV parametrize 元素数   = {len(a)}")
print(f"HEAD _HEADED_LINES 元素数 = {len(b)}")
print(f"逐元素 AST dump 完全相同  = {a == b}")
if a != b:
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            print(f"  第 {i} 项不同")
    print(f"  长度: {len(a)} vs {len(b)}")

c = b[:-1] + ["<mutated>"]
print(f"验伪锚（人为替换末项后再比）= {a == c}   ⇒ 上面那个 True 不是恒真")
