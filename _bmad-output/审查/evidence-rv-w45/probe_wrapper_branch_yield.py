#!/usr/bin/env python3
"""CARD-RV-W4-5 (c)/R2-5a：实测「同作用域跨分支 yield」这条形态现在被不被拦下。

**为什么要这一跑**：R2 外审第 5 条（⑤）点了**两个**子形态——

  (i) 隔离块内的 yield 其实在嵌套函数里（存档反例，已配常设条目 `R2-5a`）；
  (ii) 存档原话：「普通的『一条分支隔离内 yield，另一条分支隔离外 yield』也存在
       同类问题」——**这一条在 `_AST_MUST_FLAG` 里没有对应条目**。

`07d59a52` 的整改是 `_walk_same_scope`（不下潜进另开作用域的节点），它按定义只
处理 (i)。(ii) 的 yield 与隔离块**同作用域、不同分支**，`_walk_same_scope` 不会
把它排除，也不会把它收进来——它压根不在那个 `with` 的 body 里。所以推演上 (ii)
仍然放行。但「代码机制能那样失败」不等于「它就是那样失败的」，所以在这里真跑一次。

**三态矩阵（缺正控就无法把「门漏放」与「探针没跑起来」分开）**：

  * POS-RED   —— 表里 `R2-5a` 那条原文，**必须**有违规。它证明探针确实在调用真
                 判据，而不是在空转。
  * POS-GREEN —— 表里 `验伪锚 10` 那条原文，**必须**零违规。它证明探针不是「什么
                 都判红」，否则待测项判红也没有信息量。
  * PROBE     —— 形态 (ii)。零违规 = 未被拦下。

只读：import 被测模块（其顶层无可执行语句、`if __name__` 守卫在文件末尾），
调用 `analyze_source` 纯函数，不写任何文件、不起子进程、不连任何端口。
"""

from __future__ import annotations

import hashlib
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "backend" / "scripts" / "lifespan_isolation_negative_control.py"

# ── 三条输入 ──────────────────────────────────────────────────────────────
# POS-RED：与 _AST_MUST_FLAG 的 "R2-5a ..." 条目逐字同形（嵌套函数里的 yield）。
POS_RED = (
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

# POS-GREEN：与 _AST_MUST_PASS 的 "验伪锚 10 ..." 条目逐字同形（合法包装器）。
POS_GREEN = (
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

# PROBE：形态 (ii)。flag 为假时走 else，让出控制权那一刻隔离已经不在了。
PROBE = (
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

CASES = (
    ("POS-RED", POS_RED, "must-flag"),
    ("POS-GREEN", POS_GREEN, "must-pass"),
    ("PROBE", PROBE, "unknown"),
)


def load_module():
    spec = importlib.util.spec_from_file_location("_rvw45_negctl", SRC)
    if spec is None or spec.loader is None:
        raise SystemExit(f"PROBE-HARNESS-BROKEN: 无法为 {SRC} 建 spec")
    mod = importlib.util.module_from_spec(spec)
    # 动态加载先注册 sys.modules，否则模块内任何按模块名自省的东西（dataclass 等）
    # 会在导入期崩，而那种崩会伪装成「被测物坏了」。
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    before = hashlib.sha256(SRC.read_bytes()).hexdigest()
    mod = load_module()

    results: dict[str, list[str]] = {}
    for name, source, _ in CASES:
        results[name] = mod.analyze_source(source, f"<rvw45:{name}>")

    for name, _, expect in CASES:
        v = results[name]
        head = v[0] if v else "(零违规)"
        print(f"  [{name:<9}] violations={len(v):<2} expect={expect}")
        print(f"              → {head}")

    after = hashlib.sha256(SRC.read_bytes()).hexdigest()
    print(f"  被测文件 sha256 跑前={before[:16]}… 跑后={after[:16]}… "
          f"identical={before == after}")

    # ── 判据 ────────────────────────────────────────────────────────────
    if before != after:
        print("PROBE: HARNESS-BROKEN（被测文件在本次运行中被改动）", file=sys.stderr)
        return 2
    if not results["POS-RED"]:
        print(
            "PROBE: HARNESS-BROKEN（正控 POS-RED 未被拦下 ⇒ 探针没在调用真判据，"
            "PROBE 的结果无信息量）",
            file=sys.stderr,
        )
        return 2
    if results["POS-GREEN"]:
        print(
            "PROBE: HARNESS-BROKEN（正控 POS-GREEN 被判红 ⇒ 探针在无差别判红，"
            "PROBE 的结果无信息量）",
            file=sys.stderr,
        )
        return 2

    if results["PROBE"]:
        print("PROBE: 形态 (ii) 已被拦下 —— R2-5a 的两个子形态都闭合")
        return 0
    print(
        "PROBE: 形态 (ii) **未被拦下** —— `_walk_same_scope` 只闭合了子形态 (i)"
        "（嵌套作用域），同作用域跨分支的 with 外 yield 仍可取得隔离包装器资格；"
        "两条正控均按预期（RED 红 / GREEN 绿），故本结论不是探针失效所致"
    )
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
