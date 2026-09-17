"""定向负控：逐个撤掉本卡的一处修复，断言**指定的那一条**负控输入变红。

判据是「那一条」而不是「某处失败」—— 后者会被任何无关的红蒙混过去。
每个变异跑在**副本**上，生产文件一字不动。
"""
import ast, importlib.util as u, pathlib, sys, tempfile

SRC = pathlib.Path("backend/scripts/lifespan_isolation_negative_control.py")
BASE = SRC.read_text(encoding="utf-8")

MUTANTS = [
 ("撤 (b)：_own_exprs 不再下潜 lambda 默认参数",
  "R2-5b-B-lambda-defaults", "MISSED",
  [("""                if isinstance(child, ast.Lambda):""",
    """                if isinstance(child, ast.Lambda) or False:  # MUTANT
                    continue
                if False:""")]),
 ("撤 (c)：collect_setattr 整条失效",
  "R2-7-B-setattr-write", "MISSED",
  [('''        if not builtin_setattr:
            return''',
    '''        return  # MUTANT
        if not builtin_setattr:
            return''')]),
 ("撤 (d)：不再要求每一条 yield 都被覆盖",
  "R2-5a-ii-branch-split-isolation", "MISSED",
  [("""            if any(id(y) not in covered for y in all_yields):
                continue""",
    """            if False:  # MUTANT
                continue""")]),
 ("撤 HIGH-2：_outer_evaluated_parts 不产出任何东西",
  "R1-HIGH2-nested-def-default-yield", "MISSED",
  [('''    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        yield from node.decorator_list''',
    '''    if True:  # MUTANT
        return
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        yield from node.decorator_list''')]),
 ("撤 MEDIUM-3：setattr 遮蔽判据恒真（内建）",
  "验伪锚 R1-M3", "FALSE POSITIVE",
  [("""    builtin_setattr = not _module_binds_name(tree, "setattr")""",
    """    builtin_setattr = True  # MUTANT""")]),
 ("回装 HIGH-1 那次被撤回的改动（根位置 lambda 也只走默认参数）",
  "R1-HIGH1-regress-lambda-body-walrus", "MISSED",
  [("""        stack: list[ast.AST] = [node]
        while stack:
            cur = stack.pop()
            for child in ast.iter_child_nodes(cur):
                if isinstance(child, ast.Lambda):""",
    """        stack: list[ast.AST] = [node]
        while stack:
            cur = stack.pop()
            if isinstance(cur, ast.Lambda):  # MUTANT
                for d in (*cur.args.defaults, *cur.args.kw_defaults):
                    if d is not None:
                        yield d
                        stack.append(d)
                continue
            for child in ast.iter_child_nodes(cur):
                if isinstance(child, ast.Lambda):""")]),
]

def run(text):
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as fh:
        fh.write(text); p = fh.name
    sys.argv = ["x"]
    s = u.spec_from_file_location("mut", p); m = u.module_from_spec(s); s.loader.exec_module(m)
    out = []
    for label, src in m._AST_MUST_FLAG:
        if not m.analyze_source(src, f"<n:{label}>"):
            out.append(("MISSED", label))
    for label, src in m._AST_MUST_PASS:
        if m.analyze_source(src, f"<n:{label}>"):
            out.append(("FALSE POSITIVE", label))
    return out

print("=== 控制组：未变异的定稿 ===")
base_red = run(BASE)
print(f"  红项 = {base_red}   （须为空，否则后面全部结论不可比）")
assert not base_red
bad = 0
for name, want_label, want_kind, edits in MUTANTS:
    text = BASE
    for old, new in edits:
        assert text.count(old) == 1, f"{name}: 变异锚命中 {text.count(old)} 次"
        text = text.replace(old, new)
    try:
        red = run(text)
    except SyntaxError as e:
        print(f"  ✗ {name}: 变异体语法错 {e}"); bad += 1; continue
    hit = [(k, l) for k, l in red if want_label in l and k == want_kind]
    others = [(k, l) for k, l in red if not (want_label in l and k == want_kind)]
    ok = "✓" if hit else "✗ 未红 = 该锚没绑住这处修复"
    if not hit: bad += 1
    print(f"  {ok}  {name}")
    print(f"        指定判据 [{want_kind}] {want_label[:52]} → {'红' if hit else '仍绿'}"
          f"   （连带红 {len(others)} 条: {[l[:34] for _, l in others][:3]}）")
print(f"\n未按预期变红的变异数 = {bad}")
sys.exit(1 if bad else 0)
