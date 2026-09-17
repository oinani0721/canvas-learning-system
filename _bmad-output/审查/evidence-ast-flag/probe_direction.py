"""核「根位置 lambda」那一支的行为变更方向：是去掉误判，还是放过真危险？"""
import ast, importlib.util as u, sys, pathlib
HERE = pathlib.Path(__file__).parent
sys.argv = ["x"]
def load(p, n):
    s = u.spec_from_file_location(n, p); m = u.module_from_spec(s); s.loader.exec_module(m); return m
old = load(HERE / "orig.py", "old")
new = load("backend/scripts/lifespan_isolation_negative_control.py", "new")
H = ("import contextlib\nfrom fastapi import FastAPI\nfrom app.main import app\n"
     "from fastapi.testclient import TestClient\nfrom tests.support.lifespan import no_lifespan\n"
     "@contextlib.contextmanager\n")
T = "def t():\n    with isolated(app), TestClient(app):\n        pass\n"
CASES = {
 "A 嵌套 def 的默认参数是**裸 lambda**，海象在 lambda **体**内\n"
 "    → 该海象绑 lambda 自己的作用域（PEP 572），外层 a 没被动 ⇒ 包装器真安全 ⇒ 正确答案 = CLEAN":
   H + "def isolated(a):\n    def inner(cb=lambda: (a := FastAPI())):\n        pass\n"
       "    with no_lifespan(a):\n        yield a\n" + T,
 "B 同上，但海象在 lambda 的**默认参数**里\n"
 "    → 该海象在定义处求值、绑外层 ⇒ a 真被重绑 ⇒ 正确答案 = CAUGHT（本卡 (b) 要修的就是它）":
   H + "def isolated(a):\n    def inner(cb=lambda x=(a := FastAPI()): x):\n        pass\n"
       "    with no_lifespan(a):\n        yield a\n" + T,
 "C 对照：嵌套 def 自己的默认参数里有海象（早已被抓，不该被本卡弄丢）":
   H + "def isolated(a):\n    def inner(x=(a := FastAPI())):\n        pass\n"
       "    with no_lifespan(a):\n        yield a\n" + T,
}
for name, src in CASES.items():
    r = []
    for tag, m in (("旧", old), ("新", new)):
        r.append(f"{tag}={'CAUGHT' if m.analyze_source(src, '<p>') else 'CLEAN'}")
    print(f"  {name}\n      {'   '.join(r)}\n")
