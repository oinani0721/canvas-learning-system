"""逐条复现 Codex round-3 的 2 HIGH + 1 MEDIUM（四版对照）。"""
import ast, importlib.util as u, sys, pathlib
HERE = pathlib.Path("/private/tmp/claude-501/-Users-Heishing-Desktop-canvas-canvas-learning-system--claude-worktrees-card-t8-tools/b42fcc2d-3fce-4f80-8e22-bd7ab51c0fbc/scratchpad")
sys.argv = ["x"]
def load(p, n):
    s = u.spec_from_file_location(n, p); m = u.module_from_spec(s); s.loader.exec_module(m); return m
V = [("base", load(HERE / "orig.py", "v0")), ("r1", load(HERE / "r1.py", "v1")),
     ("r2", load(HERE / "r2.py", "v2")),
     ("现", load("backend/scripts/lifespan_isolation_negative_control.py", "v3"))]
SET = "import threading as mod\nfrom app.main import app\nfrom fastapi.testclient import TestClient\n"
TAIL = 'setattr(mod, "client", TestClient(app))\nwith mod.client:\n    pass\n'
CASES = [
 ("r3-HIGH1 顶层 if 块里嵌套函数的局部赋值（不遮蔽模块级调用）", "CAUGHT",
  SET + "if True:\n    def unrelated():\n        setattr = None\n" + TAIL),
 ("r3-HIGH2 except as setattr（退出即删名）", "CAUGHT",
  SET + "try:\n    raise ValueError()\nexcept ValueError as setattr:\n    pass\n" + TAIL),
 ("r3-HIGH2b if TYPE_CHECKING: setattr = None（运行时不执行）", "CAUGHT",
  "from typing import TYPE_CHECKING\n" + SET + "if TYPE_CHECKING:\n    setattr = None\n" + TAIL),
 ("r3-HIGH2c 遮蔽写在危险调用**之后**", "CAUGHT",
  SET + TAIL + "match 1:\n    case setattr:\n        pass\n"),
 ("r3-MEDIUM3 顶层 if 块里真 def setattr（只读锁）", "CLEAN（已知 fail-closed 误判，登记）",
  "import threading as mod\nfrom fastapi.testclient import TestClient\n"
  "if True:\n    def setattr(obj, name, value):\n        return getattr(obj, name)\n"
  'setattr(mod, "_active_limbo_lock", None)\nwith mod._active_limbo_lock:\n    pass\n'),
 ("对照 原 R2-7-B（本卡三条之一）", "CAUGHT", SET + TAIL),
 ("对照 r2-HIGH4 global setattr", "CAUGHT",
  SET + "def unrelated():\n    global setattr\n" + TAIL),
]
for name, want, src in CASES:
    row = "  ".join(f"{t}={'CAUGHT' if m.analyze_source(src,'<v>') else 'CLEAN'}" for t, m in V)
    print(f"  期望 {want}\n      {row}\n      {name}")
