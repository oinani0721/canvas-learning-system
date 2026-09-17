"""round-3 自审：把我自己问 Codex 的几条先验一遍（只读）。"""
import ast, importlib.util as u, sys
sys.argv = ["x"]
s = u.spec_from_file_location("n", "backend/scripts/lifespan_isolation_negative_control.py")
m = u.module_from_spec(s); s.loader.exec_module(m)

print("== Q0a _lambda_outer_defaults 的产出里会不会含 lambda ==")
SRCS = ["g = lambda a=(lambda b=(lambda c=(x := 1): c): b): a\n",
        "g = lambda *, k=(lambda *, j=(y := 2): j): k\n",
        "g = lambda a=(lambda b=1: b), *, k=(lambda: (z := 3)): a\n"]
bad = 0
for src in SRCS:
    lam = next(n for n in ast.walk(ast.parse(src)) if isinstance(n, ast.Lambda))
    out = list(m._lambda_outer_defaults(lam))
    has_lam = [type(o).__name__ for o in out if isinstance(o, ast.Lambda)]
    print(f"  产出 {len(out)} 个，含 lambda = {has_lam or '无'}   {src.strip()[:60]}")
    if has_lam: bad += 1

print("\n== Q0b 深嵌套/交替嵌套下的绑定（该记 vs 不该记）==")
CASES = [
 ("三层 lambda，海象在最内层**默认参数**里（一路定义时求值 ⇒ 该记）", "x",
  "g = lambda a=(lambda b=(lambda c=(x := 1): c): b): a\n"),
 ("三层 lambda，海象在最内层**体**里（调用时 ⇒ 不该记）", None,
  "g = lambda a=(lambda b=(lambda c=1: (x := 1)): b): a\n"),
 ("lambda 的默认参数里套 def？（语法不允许，改成 lambda 里套 comprehension）", "x",
  "g = lambda a=[(x := 1) for _ in range(1)]: a\n"),
 ("kwonly 默认参数里的海象（该记）", "y",
  "g = lambda *, k=(y := 2): k\n"),
]
for name, want, src in CASES:
    got = sorted(m._ModuleIndex(ast.parse(src)).module_scope.bindings)
    ok = (want in got) if want else ("x" not in got)
    print(f"  {'✓' if ok else '✗'} {'该记 ' + want if want else '不该记 x':12s} 实得 {got}   {name}")
    if not ok: bad += 1

print("\n== Q1 注解覆盖五类参数 ==")
T = ("import contextlib\nfrom app.main import app\nfrom fastapi.testclient import TestClient\n"
     "from tests.support.lifespan import no_lifespan\n@contextlib.contextmanager\n"
     "def isolated(a, quick):\n    if quick:\n{MID}    else:\n        with no_lifespan(a):\n"
     "            yield a\ndef t():\n    with isolated(app, True), TestClient(app):\n        pass\n")
MIDS = {
 "posonly 注解":  "        def u(x: (yield a), /):\n            pass\n",
 "普通参数注解":  "        def u(x: (yield a)):\n            pass\n",
 "kwonly 注解":   "        def u(*, x: (yield a)):\n            pass\n",
 "*args 注解":    "        def u(*x: (yield a)):\n            pass\n",
 "**kwargs 注解": "        def u(**x: (yield a)):\n            pass\n",
 "返回注解":      "        def u() -> (yield a):\n            pass\n",
}
for name, mid in MIDS.items():
    vs = m.analyze_source(T.replace("{MID}", mid), "<q1>")
    caught = bool(vs) and not any("SyntaxError" in v for v in vs)
    print(f"  {'✓ CAUGHT' if caught else '✗ 未抓/因 SyntaxError 而红'}  {name}")
    if not caught: bad += 1

print("\n== Q2 setattr 写路径：所有「看起来像遮蔽」的形态都必须仍被抓 ==")
print("   （round-3 撤回了模块级遮蔽开关 —— 一次绑定证明不了每个调用点都被遮蔽）")
SET = "import threading as mod\nfrom app.main import app\nfrom fastapi.testclient import TestClient\n"
TAIL = 'setattr(mod, "client", TestClient(app))\nwith mod.client:\n    pass\n'
Q2 = [("顶层 if 块里嵌套函数的局部赋值", SET + "if True:\n    def unrelated():\n        setattr = None\n" + TAIL),
      ("except as setattr（退出即删名）", SET + "try:\n    raise ValueError()\nexcept ValueError as setattr:\n    pass\n" + TAIL),
      ("if TYPE_CHECKING: setattr = None", "from typing import TYPE_CHECKING\n" + SET + "if TYPE_CHECKING:\n    setattr = None\n" + TAIL),
      ("遮蔽写在危险调用之后", SET + TAIL + "match 1:\n    case setattr:\n        pass\n"),
      ("无关函数的形参", SET + "def unrelated(setattr):\n    return setattr\n" + TAIL),
      ("无关函数里 global setattr", SET + "def unrelated():\n    global setattr\n" + TAIL),
      ("模块级 def setattr（⚠ 已登记的 fail-closed 误判，此处期望也是 CAUGHT）",
       "def setattr(o, n, v):\n    return None\n" + SET + TAIL)]
for name, src in Q2:
    vs = m.analyze_source(src, "<q2>")
    ok = bool(vs)
    print(f"  {'✓ CAUGHT' if ok else '✗ 漏放'}  {name}")
    if not ok: bad += 1

print(f"\n不符项 = {bad}")
sys.exit(1 if bad else 0)
