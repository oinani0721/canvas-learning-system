"""逐条复现 Codex round-2 的 4 HIGH + 1 MEDIUM（三版对照）。"""
import importlib.util as u, sys, pathlib
HERE = pathlib.Path("/private/tmp/claude-501/-Users-Heishing-Desktop-canvas-canvas-learning-system--claude-worktrees-card-t8-tools/b42fcc2d-3fce-4f80-8e22-bd7ab51c0fbc/scratchpad")
sys.argv = ["x"]
def load(p, n):
    s = u.spec_from_file_location(n, p); m = u.module_from_spec(s); s.loader.exec_module(m); return m
V = [("B14_BASE", load(HERE / "orig.py", "v0")),
     ("r1定稿", load(HERE / "r1.py", "v1")),
     ("现在", load("backend/scripts/lifespan_isolation_negative_control.py", "v2"))]

IMP = ("import contextlib\nfrom fastapi import FastAPI\nfrom app.main import app\n"
       "from fastapi.testclient import TestClient\nfrom tests.support.lifespan import no_lifespan\n")
SET = ("import threading as mod\nfrom app.main import app\n"
       "from fastapi.testclient import TestClient\n")

CASES = [
 ("HIGH-1 根 lambda 体内又套 lambda（两者都没被调用，app 仍是生产实例）", "CAUGHT",
  IMP + "def test():\n    def unused(cb=lambda: (lambda x=(app := FastAPI()): x)):\n        pass\n"
        "    with TestClient(app):\n        pass\n"),
 ("HIGH-1 child 路径同型", "CAUGHT",
  IMP + "def test():\n    unused = lambda cb=lambda: (app := FastAPI()): cb\n"
        "    with TestClient(app):\n        pass\n"),
 ("HIGH-2 默认值 lambda 的**体**里 yield（unused 根本不是生成器）", "CAUGHT",
  IMP + "def isolated(a):\n    with no_lifespan(a):\n        def unused(cb=lambda: (yield a)):\n"
        "            pass\n    return contextlib.nullcontext(a)\n"
        "def test():\n    with isolated(app), TestClient(app):\n        pass\n"),
 ("HIGH-3 参数**注解**里 yield（3.11/3.12 合法且真让出）", "CAUGHT",
  IMP + "@contextlib.contextmanager\ndef isolated(a, quick):\n    if quick:\n"
        "        def unused(x: (yield a)):\n            pass\n"
        "    else:\n        with no_lifespan(a):\n            yield a\n"
        "def test():\n    with isolated(app, True), TestClient(app):\n        pass\n"),
 ("HIGH-3 **返回注解**里 yield", "CAUGHT",
  IMP + "@contextlib.contextmanager\ndef isolated(a, quick):\n    if quick:\n"
        "        def unused() -> (yield a):\n            pass\n"
        "    else:\n        with no_lifespan(a):\n            yield a\n"
        "def test():\n    with isolated(app, True), TestClient(app):\n        pass\n"),
 ("HIGH-4 无关函数里一句 global setattr（没绑任何对象）", "CAUGHT",
  SET + "def unrelated():\n    global setattr\n"
        'setattr(mod, "client", TestClient(app))\nwith mod.client:\n    pass\n'),
 ("HIGH-4 无关函数的同名**形参**", "CAUGHT",
  SET + "def unrelated(setattr):\n    return setattr\n"
        'setattr(mod, "client", TestClient(app))\nwith mod.client:\n    pass\n'),
 ("MEDIUM-5 match case setattr（真遮蔽，只读锁）", "CLEAN",
  "import threading as mod\nfrom fastapi.testclient import TestClient\n"
  "match (lambda obj, name, value: getattr(obj, name)):\n    case setattr:\n"
  '        setattr(mod, "_active_limbo_lock", None)\n'
  "        with mod._active_limbo_lock:\n            pass\n"),
 ("MEDIUM-5 except ... as setattr（真遮蔽）", "CLEAN",
  "import threading as mod\nfrom fastapi.testclient import TestClient\n"
  "try:\n    pass\nexcept Exception as setattr:\n"
  '    setattr(mod, "_active_limbo_lock", None)\n'
  "    with mod._active_limbo_lock:\n        pass\n"),
 ("对照 原 R2-7-B（本卡三条之一，不许丢）", "CAUGHT",
  SET + 'setattr(mod, "client", TestClient(app))\nwith mod.client:\n    pass\n'),
 ("对照 模块级 def setattr 真遮蔽", "CLEAN",
  "def setattr(o, n, v):\n    return None\n" + SET
  + 'setattr(mod, "client", TestClient(app))\nwith mod.client:\n    pass\n'),
]
bad = 0
for name, want, src in CASES:
    row = []
    for tag, m in V:
        got = "CAUGHT" if m.analyze_source(src, "<v>") else "CLEAN"
        row.append(f"{tag}={got}")
        if tag == "现在" and got != want:
            bad += 1
    mark = "✓" if row[-1].endswith(want) else "✗"
    print(f"  {mark} 期望 {want:6s} | {'  '.join(row)}\n      {name}")
print(f"\n现版不符项 = {bad}")
sys.exit(1 if bad else 0)
