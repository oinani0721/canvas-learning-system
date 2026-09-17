#!/usr/bin/env python3
"""证明「跑完裁判之后的那次编辑是**纯注释**」—— D-32 等价证明（不靠人读 diff）。

用法：`python3 ast_equal_after_comment_edit.py <文件> <编辑前快照>`
判据：两侧 `ast.dump(ast.parse(src), include_attributes=False)` **逐字符相同**
      ⇒ 注释与行号之外没有任何差异（注释在 `ast.parse` 阶段就被丢掉）。
⚠️ 覆盖面如实说：**docstring 是字符串字面量、会进 AST**，所以改 docstring 会让本脚本报
   `AST 相同 = False`。换句话说本脚本给 True 的范围只有「改 `#` 注释 / 改空白与换行」，
   ⛔ 它不是「所有文案编辑都放行」的证明。本卡的跑后编辑只动 `#` 注释。
⚠️ 验伪锚（每次用之前跑一遍，证明它不是恒 True）：
   `x = 1` vs `x = 2` 必须报 False；`x = 1` vs `# c\\nx = 1` 必须报 True。
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path


def dump(src: str) -> str:
    return ast.dump(ast.parse(src), include_attributes=False)


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__)
        return 4
    now = Path(argv[1]).read_text(encoding="utf-8")
    before = Path(argv[2]).read_text(encoding="utf-8")
    same = dump(now) == dump(before)
    print(f"文件        : {argv[1]}")
    print(f"编辑前快照  : {argv[2]}")
    print(f"字节相同    : {now == before}")
    print(f"AST 相同    : {same}  ← True = 那次编辑只动了注释/行号，代码零改动")
    if not same:
        print("⛔ AST 不同 —— 那次编辑不是纯注释，裁判存档必须重跑")
    return 0 if same else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
