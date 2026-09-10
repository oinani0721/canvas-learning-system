#!/usr/bin/env python3
"""CARD-RV-W4-5 (c)：把「五条 HIGH 整改后还剩什么」的三个推演当场跑一遍。

三条待测形态各自都是**已整改那条 HIGH 的另一个语法位置**，不是新缺陷类别：

  P1 (R2-5a 之 ii) —— 存档 §5 原话「普通的『一条分支隔离内 yield，另一条分支
      隔离外 yield』也存在同类问题」。整改件 ``_walk_same_scope`` 按定义只处理
      「下潜进另开作用域的节点」，而这条的 yield 与隔离块**同作用域、不同分支**。
  P2 (R2-5b 之 lambda) —— 整改在 :691 特判了 FunctionDef 的
      ``decorator_list/defaults/kw_defaults``；``_own_exprs`` 却把整个 ``Lambda``
      排除（其 docstring 的理由「lambda 体里的 := 绑定 lambda 自己的作用域」对
      lambda **body** 成立，对 lambda **defaults** 不成立——defaults 与 FunctionDef
      的 defaults 一样在定义处求值，那正是 :691 存在的理由）。
      与表内 ``R2-5b`` 条目**只差 ``def`` → ``lambda`` 一处**，归因干净。
  P3 (R2-7 之 setattr) —— ``_module_attr_write_paths`` 扫的是
      Assign/AnnAssign/AugAssign/For/With-as/Delete 的**目标**；``setattr(mod, ...)``
      是一次 Call，不在这些语法位置上。与表内 ``R2-7`` 条目只差写法。

**五条正控（缺了它们，「零违规」既可解释成门漏放、也可解释成探针空转）**：
三条必红分别锚住包装器判定链、R2-5b 的失格路径、R2-7 的 module_attr_writes 路径；
两条必绿证明探针不是无差别判红，其中 C4b 专门锚住「C4 豁免这条路本身是通的」——
否则 P3 判绿也可能只是因为它根本没走到 C4。

只读：import 被测模块（顶层无可执行语句、``if __name__`` 守卫在 :3471），
只调 ``analyze_source`` 纯函数；不写文件、不起子进程、不连任何端口。
"""

from __future__ import annotations

import hashlib
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "backend" / "scripts" / "lifespan_isolation_negative_control.py"

# ── 正控：必红 ────────────────────────────────────────────────────────────
# 与 _AST_MUST_FLAG 的 "R2-5a ..." 条目逐字同形。
RED_5A = (
    "import contextlib\n"
    "from app.main import app\n"
    "from fastapi.testclient import TestClient\n"
    "from tests.support.lifespan import no_lifespan\n"
    "@contextlib.contextmanager\n"
    "def isolated(a):\n"
    "    with no_lifespan(a):\n"
    "        def unused():\n"
    "            yield a\n"
    "    yield a\n"
    "def t():\n"
    "    with isolated(app), TestClient(app):\n"
    "        pass\n"
)
# 与 _AST_MUST_FLAG 的 "R2-5b ..." 条目逐字同形（P2 的对照输入）。
RED_5B = (
    "import contextlib\n"
    "from fastapi import FastAPI\n"
    "from app.main import app\n"
    "from fastapi.testclient import TestClient\n"
    "from tests.support.lifespan import no_lifespan\n"
    "@contextlib.contextmanager\n"
    "def isolated(a):\n"
    "    def unused(x=(a := FastAPI())):\n"
    "        pass\n"
    "    with no_lifespan(a):\n"
    "        yield a\n"
    "def t():\n"
    "    with isolated(app), TestClient(app):\n"
    "        pass\n"
)
# 与 _AST_MUST_FLAG 的 "R2-7 C4 ..." 条目逐字同形（P3 的对照输入）。
RED_7 = (
    "import contextlib as mod\n"
    "from app.main import app\n"
    "from fastapi.testclient import TestClient\n"
    "mod.client = TestClient(app)\n"
    "with mod.client:\n"
    "    pass\n"
)

# ── 正控：必绿 ────────────────────────────────────────────────────────────
# 与 _AST_MUST_PASS 的 "验伪锚 10 ..." 条目逐字同形。
GREEN_WRAP = (
    "import contextlib\n"
    "from app.main import app\n"
    "from fastapi.testclient import TestClient\n"
    "from tests.support.lifespan import no_lifespan\n"
    "@contextlib.contextmanager\n"
    "def isolated(a):\n"
    "    with no_lifespan(a):\n"
    "        yield a\n"
    "def t():\n"
    "    with isolated(app), TestClient(app) as c:\n"
    "        pass\n"
)
# 与 _AST_MUST_PASS 的 "验伪锚 C4b ..." 条目逐字同形。
GREEN_C4B = (
    "import somemod as mod\n"
    "from app.main import app\n"
    "from fastapi.testclient import TestClient\n"
    "def t():\n"
    "    with mod._refresh_guard:\n"
    "        pass\n"
)

# ── 待测 ─────────────────────────────────────────────────────────────────
P1_BRANCH_YIELD = (
    "import contextlib\n"
    "from app.main import app\n"
    "from fastapi.testclient import TestClient\n"
    "from tests.support.lifespan import no_lifespan\n"
    "@contextlib.contextmanager\n"
    "def isolated(a, flag):\n"
    "    if flag:\n"
    "        with no_lifespan(a):\n"
    "            yield a\n"
    "    else:\n"
    "        yield a\n"
    "def t():\n"
    "    with isolated(app, False), TestClient(app):\n"
    "        pass\n"
)
P2_LAMBDA_DEFAULT_WALRUS = (
    "import contextlib\n"
    "from fastapi import FastAPI\n"
    "from app.main import app\n"
    "from fastapi.testclient import TestClient\n"
    "from tests.support.lifespan import no_lifespan\n"
    "@contextlib.contextmanager\n"
    "def isolated(a):\n"
    "    unused = lambda x=(a := FastAPI()): x\n"
    "    with no_lifespan(a):\n"
    "        yield a\n"
    "def t():\n"
    "    with isolated(app), TestClient(app):\n"
    "        pass\n"
)
P3_SETATTR_MODULE_WRITE = (
    "import contextlib as mod\n"
    "from app.main import app\n"
    "from fastapi.testclient import TestClient\n"
    "setattr(mod, 'client', TestClient(app))\n"
    "with mod.client:\n"
    "    pass\n"
)

CONTROLS_RED = (
    ("RED-R2-5a", RED_5A, "包装器判定链在跑（嵌套函数 yield 失格）"),
    ("RED-R2-5b", RED_5B, "def-defaults 海象失格路径在跑（P2 的对照）"),
    ("RED-R2-7", RED_7, "module_attr_writes 路径在跑（P3 的对照）"),
)
CONTROLS_GREEN = (
    ("GREEN-anchor10", GREEN_WRAP, "不是无差别判红（合法包装器仍绿）"),
    ("GREEN-C4b", GREEN_C4B, "C4 豁免这条路本身是通的（P3 判绿才有归因）"),
)
PROBES = (
    ("P1-branch-yield", P1_BRANCH_YIELD, "R2-5a 之 ii：同作用域跨分支 with 外 yield"),
    ("P2-lambda-default", P2_LAMBDA_DEFAULT_WALRUS, "R2-5b 之 lambda：只差 def→lambda"),
    ("P3-setattr-write", P3_SETATTR_MODULE_WRITE, "R2-7 之 setattr：只差写法"),
)


def load_module():
    spec = importlib.util.spec_from_file_location("_rvw45_residual", SRC)
    if spec is None or spec.loader is None:
        raise SystemExit(f"PROBE-HARNESS-BROKEN: 无法为 {SRC} 建 spec")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod  # 动态加载先注册，否则模块内自省会在导入期崩
    spec.loader.exec_module(mod)
    return mod


def show(tag: str, why: str, vs: list[str]) -> None:
    head = vs[0] if vs else "(零违规)"
    print(f"  [{tag:<16}] violations={len(vs):<2} — {why}")
    print(f"                     → {head}")


def main() -> int:
    before = hashlib.sha256(SRC.read_bytes()).hexdigest()
    mod = load_module()

    def run(src: str, tag: str) -> list[str]:
        return mod.analyze_source(src, f"<rvw45:{tag}>")

    print("── 正控（必红）─────────────────────────────────────────────")
    red = {}
    for tag, src, why in CONTROLS_RED:
        red[tag] = run(src, tag)
        show(tag, why, red[tag])

    print("── 正控（必绿）─────────────────────────────────────────────")
    green = {}
    for tag, src, why in CONTROLS_GREEN:
        green[tag] = run(src, tag)
        show(tag, why, green[tag])

    print("── 待测 ───────────────────────────────────────────────────")
    probe = {}
    for tag, src, why in PROBES:
        probe[tag] = run(src, tag)
        show(tag, why, probe[tag])

    after = hashlib.sha256(SRC.read_bytes()).hexdigest()
    print(f"\n  被测文件 sha256 跑前={before[:16]}… 跑后={after[:16]}… identical={before == after}")

    # ── harness 自检：正控不达标则三条待测结果无信息量 ──────────────────
    if before != after:
        print("RESIDUAL-PROBE: HARNESS-BROKEN（被测文件在本次运行中被改动）", file=sys.stderr)
        return 2
    bad_red = [t for t in red if not red[t]]
    bad_green = [t for t in green if green[t]]
    if bad_red or bad_green:
        print(
            f"RESIDUAL-PROBE: HARNESS-BROKEN（必红未红={bad_red} 必绿未绿={bad_green}）"
            "⇒ 待测项的结果无信息量",
            file=sys.stderr,
        )
        return 2

    unflagged = [t for t, _, _ in PROBES if not probe[t]]
    print(f"\n  正控自检: 3/3 必红全红, 2/2 必绿全绿 ⇒ 待测结果可归因")
    if not unflagged:
        print("RESIDUAL-PROBE: 三条待测形态均已被拦下")
        return 0
    print(f"RESIDUAL-PROBE: 未被拦下的形态 = {unflagged}（各自与对照输入只差一处写法）")
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
