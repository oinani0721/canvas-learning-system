#!/usr/bin/env python3
"""CARD-RV-W4-5 (f)：用 ``ast.parse`` 独立数两张 AST 表的条目数。

**为什么不 import 被测模块**：门自己报的 ``48 绕过全抓 / 27 正例全净`` 与表里
真实条目数如果来自同一次求值，它们就不是两个来源——表退化时那个数字会跟着一起
退化，判据看不见（同源期望值的假绿面）。本脚本只做静态解析，与门的运行期自报
构成**互相独立**的两个来源；两者不等即阻断。

只读：不 import 被测模块、不跑门、不写任何文件。
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

# evidence-rv-w45 -> 审查 -> _bmad-output -> <worktree root>
ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "backend" / "scripts" / "lifespan_isolation_negative_control.py"

WANTED = ("_AST_MUST_FLAG", "_AST_MUST_PASS")
EXPECTED = {"_AST_MUST_FLAG": 48, "_AST_MUST_PASS": 27}


def main() -> int:
    if not SRC.is_file():
        print(f"AST-TABLE-COUNT: ERROR 被测文件不存在 {SRC}", file=sys.stderr)
        return 2

    tree = ast.parse(SRC.read_text(encoding="utf-8"), filename=str(SRC))

    # ⛔ 验伪锚一：只认**模块顶层**的 AnnAssign，且把全部 `_AST_MUST_` 前缀的表都
    #    收进来——若将来新增第三张表而本脚本仍只数两张，下面的名单比对会报出来，
    #    而不是静默漏掉它。
    found: dict[str, ast.AnnAssign] = {}
    for node in tree.body:
        if not isinstance(node, ast.AnnAssign):
            continue
        tgt = node.target
        if isinstance(tgt, ast.Name) and tgt.id.startswith("_AST_MUST_"):
            found[tgt.id] = node

    if set(found) != set(WANTED):
        # ⛔ 定位不到就必须报错退出，不能给个数字——「找不到 ⇒ 返回 0 ⇒ 判据恒真」
        #    是提取器类判据最典型的假绿面。
        print(
            f"AST-TABLE-COUNT: ERROR 顶层 _AST_MUST_* 表名单 ={sorted(found)} "
            f"与期望 {sorted(WANTED)} 不符（表被改名/新增/移出顶层？）",
            file=sys.stderr,
        )
        return 2

    counts: dict[str, int] = {}
    for name in WANTED:
        node = found[name]
        value = node.value
        if not isinstance(value, ast.List):
            print(f"AST-TABLE-COUNT: ERROR {name} 的值不是字面 list", file=sys.stderr)
            return 2
        # ⛔ 验伪锚二：声明是 list[tuple[str, str]]。逐条核形状——若某条被写成别的
        #    形态（如少一个字段、或用变量拼接），条目数照样能数出来但语义已经变了。
        for i, elt in enumerate(value.elts):
            if not isinstance(elt, ast.Tuple) or len(elt.elts) != 2:
                print(
                    f"AST-TABLE-COUNT: ERROR {name}[{i}] 不是 2 元 tuple 字面量"
                    f"（line {getattr(elt, 'lineno', '?')}）",
                    file=sys.stderr,
                )
                return 2
        counts[name] = len(value.elts)

    line = " ".join(f"{name}={counts[name]}" for name in WANTED)
    print(f"AST-TABLE-COUNT: {line}")
    print(f"  source: {SRC}")
    print(f"  anchors: " + " ".join(f"{n}@:{found[n].lineno}" for n in WANTED))

    bad = {n: (counts[n], EXPECTED[n]) for n in WANTED if counts[n] != EXPECTED[n]}
    if bad:
        print(f"AST-TABLE-COUNT: MISMATCH 实测 vs 卡文期望 {bad}", file=sys.stderr)
        return 1
    print("AST-TABLE-COUNT: PASS (静态解析数与卡文期望 48/27 一致)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
