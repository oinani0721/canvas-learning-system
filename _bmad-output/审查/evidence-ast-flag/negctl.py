"""定向负控：逐个撤掉本卡的一处修复，断言**指定的那一条**负控输入变红。

判据是「那一条」而不是「某处失败」—— 后者会被任何无关的红蒙混过去。
每个变异跑在**副本**上，生产文件一字不动；控制组（未变异定稿）红项必须为空，否则结论不可比。
⛔ 变异锚会随生产代码改动失效（本卡实测栽过一次：patch6 之后第 6 个锚命中 0 次）。
   脚本对每个锚断言 count == 1，锚不命中直接抛，不会静默少跑一个变异。
"""
import ast, importlib.util as u, pathlib, sys, tempfile

SRC = pathlib.Path("backend/scripts/lifespan_isolation_negative_control.py")
BASE = SRC.read_text(encoding="utf-8")

MUTANTS = [
 ("卡文(b) _own_exprs 不再下潜 lambda 默认参数",
  "R2-5b-B-lambda-defaults", "MISSED",
  [("""                if isinstance(child, ast.Lambda):
                    if child_in_body:""",
    """                if isinstance(child, ast.Lambda):
                    if True:  # MUTANT""")]),
 ("卡文(c) collect_setattr 整条失效",
  "R2-7-B-setattr-write", "MISSED",
  [("""        if not (isinstance(call.func, ast.Name) and call.func.id == "setattr"):
            return""",
    """        return  # MUTANT
        if not (isinstance(call.func, ast.Name) and call.func.id == "setattr"):
            return""")]),
 ("r3 回装被撤回的「模块级遮蔽开关」的**一种**实现（any(ast.walk) 形态）",
  "R3-HIGH2-except-as-name-deleted", "MISSED",
  [("""    paths: set[str] = set()

    def collect_setattr(call: ast.Call) -> None:""",
    """    paths: set[str] = set()
    _shadowed = any(  # MUTANT：重新引入 round-3 撤回掉的那个开关
        (isinstance(_n, ast.ExceptHandler) and _n.name == "setattr")
        or (isinstance(_n, (ast.MatchAs, ast.MatchStar)) and _n.name == "setattr")
        or (isinstance(_n, ast.Name) and isinstance(_n.ctx, ast.Store) and _n.id == "setattr")
        or (isinstance(_n, (ast.FunctionDef, ast.AsyncFunctionDef)) and _n.name == "setattr")
        for _n in ast.walk(tree)
    )

    def collect_setattr(call: ast.Call) -> None:
        if _shadowed:  # MUTANT
            return""")]),
 ("卡文(d) 不再要求每一条 yield 都被覆盖",
  "R2-5a-ii-branch-split-isolation", "MISSED",
  [("""            if any(id(y) not in covered for y in all_yields):
                continue""",
    """            if False:  # MUTANT
                continue""")]),
 ("r1-HIGH2 _outer_evaluated_parts 不产出任何东西",
  "R1-HIGH2-nested-def-default-yield", "MISSED",
  [("""    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        yield from node.decorator_list""",
    """    if True:  # MUTANT
        return
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        yield from node.decorator_list""")]),
 ("r1-HIGH1 回装被撤回的改动：根位置 lambda 也只走默认参数",
  "R1-HIGH1-regress-lambda-body-walrus", "MISSED",
  [("""        stack: list[tuple[ast.AST, bool]] = [(node, False)]""",
    """        stack: list[tuple[ast.AST, bool]] = (  # MUTANT
            [(d, False) for d in _lambda_outer_defaults(node)]
            if isinstance(node, ast.Lambda)
            else [(node, False)]
        )""")]),
 ("r2-HIGH1 _own_exprs 不再区分「已进入 lambda 体」",
  "R2-HIGH1-nested-lambda-in-lambda-body", "MISSED",
  [("""                child_in_body = in_lambda_body or (isinstance(cur, ast.Lambda) and child is cur.body)""",
    """                child_in_body = False  # MUTANT""")]),
 ("r2-HIGH2 push 的部件不再递归过 push",
  "R2-HIGH2-default-lambda-body-yield", "MISSED",
  [("""            for part in _outer_evaluated_parts(n):
                push(part)""",
    """            stack.extend(_outer_evaluated_parts(n))  # MUTANT""")]),
 ("r2-HIGH3 _outer_evaluated_parts 不再收注解",
  "R2-HIGH3-param-annotation-yield", "MISSED",
  [("""        a = node.args
        for arg in (*a.posonlyargs, *a.args, *a.kwonlyargs, a.vararg, a.kwarg):
            if arg is not None and arg.annotation is not None:
                yield arg.annotation
        if node.returns is not None:
            yield node.returns""",
    """        pass  # MUTANT""")]),
]

def _id_of(label: str) -> str:
    """条目 label 的 ID 段 = 第一个全角冒号之前那截。

    ⛔ Codex round-3 LOW：上一版用 `want_label in label` 子串匹配，`验伪锚 R2-M5` 会同时
    命中 M5 与 M5b —— 只要其中**任何一条**红就算「指定判据红」，指定目标因此不唯一。
    现在按 ID 段**精确相等**匹配，并在开跑前断言每个目标 ID 在两张表里恰好出现一次。
    """
    return label.split("：", 1)[0]


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

import importlib.util as _u, tempfile as _t
with _t.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as _fh:
    _fh.write(BASE); _bp = _fh.name
sys.argv = ["x"]
_s = _u.spec_from_file_location("base", _bp); _bm = _u.module_from_spec(_s); _s.loader.exec_module(_bm)
_ids = [_id_of(l) for l, _ in (*_bm._AST_MUST_FLAG, *_bm._AST_MUST_PASS)]
for _, _want, _, _ in MUTANTS:
    _n = _ids.count(_want)
    assert _n == 1, f"目标 ID {_want!r} 在两表里出现 {_n} 次（须恰好 1，否则「指定的那一条」不唯一）"
print(f"目标 ID 唯一性自检：{len(MUTANTS)} 个目标各命中 1 条 ✓")

# ⛔ 上面那条断言只覆盖**本脚本用到的那几个目标**，不是「表里 ID 都唯一」。两者差别在于
#    下一张卡若把目标指向一个重复 ID，断言同样不会报警。这里把全表重复 ID 打出来，
#    注明它们**不可用作变异目标**（车道自审 2026-09-17 发现，非本卡新增条目）。
import collections as _c
_dups = sorted(k for k, v in _c.Counter(_ids).items() if v > 1)
print(f"全表 ID：{len(_ids)} 个，去重 {len(set(_ids))} 个。"
      f"重复 = {_dups or '（无）'}"
      + ("   ⛔ 这些 ID 不可用作变异目标" if _dups else ""))

print(f"=== 控制组：未变异的定稿（{len(MUTANTS)} 个变异待跑）===")
base_red = run(BASE)
print(f"  红项 = {base_red}   （须为空，否则后面全部结论不可比）")
assert not base_red
bad = 0
for name, want_label, want_kind, edits in MUTANTS:
    text = BASE
    for old, new in edits:
        assert text.count(old) == 1, f"{name}: 变异锚命中 {text.count(old)} 次（锚已漂移）"
        text = text.replace(old, new)
    try:
        red = run(text)
    except SyntaxError as e:
        print(f"  ✗ {name}: 变异体语法错 {e}"); bad += 1; continue
    hit = [(k, l) for k, l in red if _id_of(l) == want_label and k == want_kind]
    others = [(k, l) for k, l in red if not (_id_of(l) == want_label and k == want_kind)]
    if not hit: bad += 1
    print(f"  {'✓' if hit else '✗ 未红 = 该锚没绑住这处修复'}  {name}")
    print(f"        指定判据 [{want_kind}] {want_label[:52]} → {'红' if hit else '仍绿'}"
          f"   （连带红 {len(others)} 条）")
print(f"\n未按预期变红的变异数 = {bad}")
sys.exit(1 if bad else 0)
