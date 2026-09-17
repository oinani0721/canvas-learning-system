"""新旧 _walk_same_scope 的差分：新版比旧版多产出的节点，是否恰好都是「外层求值」那几处。"""
import ast, importlib.util as u, sys, pathlib
sys.argv = ["x"]
s = u.spec_from_file_location("n", "backend/scripts/lifespan_isolation_negative_control.py")
m = u.module_from_spec(s); s.loader.exec_module(m)

SCOPE = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)

def old_walk(node):
    """B14_BASE 版逐字复刻。"""
    if isinstance(node, SCOPE):
        return
    stack = [node]
    while stack:
        cur = stack.pop()
        yield cur
        for child in ast.iter_child_nodes(cur):
            if isinstance(child, SCOPE):
                continue
            stack.append(child)

files = m.ast_scope_files()
tot_old = tot_new = 0
only_old = 0
delta_kinds = {}
delta_yield = 0
for p in files:
    try:
        tree = ast.parse(p.read_text(encoding="utf-8"))
    except SyntaxError:
        continue
    for fn in [n for n in ast.walk(tree) if isinstance(fn_t := n, (ast.FunctionDef, ast.AsyncFunctionDef))]:
        for b in fn.body:
            o = {id(x) for x in old_walk(b)}
            n_ = {id(x): x for x in m._walk_same_scope(b)}
            tot_old += len(o); tot_new += len(n_)
            only_old += len(o - set(n_))
            for i in set(n_) - o:
                x = n_[i]
                delta_kinds[type(x).__name__] = delta_kinds.get(type(x).__name__, 0) + 1
                if isinstance(x, (ast.Yield, ast.YieldFrom)):
                    delta_yield += 1
print(f"扫描面 {len(files)} 文件 · 所有函数体逐条语句走一遍")
print(f"  旧版产出节点总数 = {tot_old}")
print(f"  新版产出节点总数 = {tot_new}")
print(f"  **旧有而新没有**的节点数 = {only_old}   ← 必须是 0（新版只增不减）")
print(f"  新增节点里 Yield/YieldFrom 的条数 = {delta_yield}   ← 真实面上「外层求值的让出」有几处")
top = sorted(delta_kinds.items(), key=lambda kv: -kv[1])[:12]
print(f"  新增节点按类型（前 12）= {top}")
