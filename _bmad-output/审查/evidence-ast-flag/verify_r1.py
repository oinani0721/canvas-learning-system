"""独立复现 Codex round-1 的 HIGH-1 / HIGH-2 / MEDIUM-3。"""
import ast, importlib.util as u, sys, pathlib
HERE = pathlib.Path(__file__).parent
sys.argv = ["x"]
def load(p, n):
    s = u.spec_from_file_location(n, p); m = u.module_from_spec(s); s.loader.exec_module(m); return m
old = load(HERE / "orig.py", "old")
new = load("backend/scripts/lifespan_isolation_negative_control.py", "new")

H1 = (
"import contextlib\n"
"from fastapi import FastAPI\n"
"from app.main import app as production\n"
"from fastapi.testclient import TestClient\n"
"app = FastAPI()\n"
"def t(cb=lambda s: ((app := production), s.enter_context(TestClient(app)))):\n"
"    with contextlib.ExitStack() as stack:\n"
"        cb(stack)\n")
H1b = (
"import contextlib\n"
"from fastapi import FastAPI\n"
"from fastapi.testclient import TestClient\n"
"def t(cb=lambda s: ((a := FastAPI()), s.enter_context(TestClient(a)))):\n"
"    with contextlib.ExitStack() as stack:\n"
"        cb(stack)\n")
H2 = (
"import contextlib\n"
"from app.main import app\n"
"from fastapi.testclient import TestClient\n"
"from tests.support.lifespan import no_lifespan\n"
"@contextlib.contextmanager\n"
"def isolated(a, quick):\n"
"    if quick:\n"
"        def unused(x=(yield a)):\n"
"            pass\n"
"    else:\n"
"        with no_lifespan(a):\n"
"            yield a\n"
"def t():\n"
"    with isolated(app, True), TestClient(app):\n"
"        pass\n")
M3 = (
"import threading as mod\n"
"from fastapi.testclient import TestClient\n"
"def setattr(obj, name, value):\n"
"    return getattr(obj, name)\n"
"setattr(mod, '_active_limbo_lock', None)\n"
"def t():\n"
"    with mod._active_limbo_lock:\n"
"        pass\n")

CASES = [
 ("HIGH-1 主：lambda **体**内海象重绑成生产 app，同体内 enter_context(TestClient(app))",
  "CAUGHT（真危险：lambda 局部 app 就是生产 app）", H1),
 ("HIGH-1 副：同形态但海象是局部 FastAPI()（应 CLEAN）",
  "CLEAN（合法）", H1b),
 ("HIGH-2：嵌套 def 的**默认参数**里 yield（在外层求值 = 真让出）",
  "CAUGHT（quick 支在隔离外让出）", H2),
 ("MEDIUM-3：模块自己 def 了一个不写属性的 setattr",
  "CLEAN（没有真的属性写，C4 豁免应成立）", M3),
]
for name, want, src in CASES:
    r = []
    for tag, m in (("旧", old), ("新", new)):
        vs = m.analyze_source(src, "<v>")
        r.append(f"{tag}={'CAUGHT' if vs else 'CLEAN'}")
    print(f"  {name}\n      正确答案 = {want}\n      {'   '.join(r)}\n")
