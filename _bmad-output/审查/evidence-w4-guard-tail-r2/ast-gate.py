"""CARD-W4-GUARD-TAIL-R2 结构判据：数 AST 分支，不数文本。

⛔ 为什么不能 grep：``test_live_port_guard_contract.py`` 的 docstring 里改前就有 2 处
``ast.TypeAlias`` 字样（Codex round-5 的登记原文），``grep -c TypeAlias`` 改前即非 0 ⇒
文本判据恒假绿。本脚本只数 ``_refuse_to_guess_on_deferred_execution`` 体内
``isinstance(node, ...)`` 第二实参里出现的**类型表达式集合**，docstring / 注释 / 字符串
字面量一律不计。

验伪锚：同一函数喂 ``git show 9c4e7e82:<path>`` 的旧文本 —— 它恒不含 TypeAlias 分支。
锚若跟着 HEAD 一起变绿，说明脚本在读 HEAD 而不是在读 BASE。

从 backend/ 目录跑。
"""

import ast
import subprocess
import sys

BASE = "9c4e7e82"


def types_in(src: str) -> list[str]:
    """``_refuse_to_guess_on_deferred_execution`` 的 isinstance 类型分支集合。"""
    tree = ast.parse(src)
    fn = next(n for n in ast.walk(tree) if getattr(n, "name", "") == "_refuse_to_guess_on_deferred_execution")
    names: set[str] = set()
    for n in ast.walk(fn):
        if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "isinstance" and len(n.args) == 2:
            second = n.args[1]
            elts = second.elts if isinstance(second, ast.Tuple) else [second]
            names.update(ast.unparse(a) for a in elts)
    return sorted(names)


def handler_types(src: str, name: str) -> list[str]:
    """某函数体内全部 ``except X`` 的 X（``ast.unparse`` 后）。"""
    tree = ast.parse(src)
    fn = next(n for n in ast.walk(tree) if getattr(n, "name", "") == name)
    return sorted(ast.unparse(h.type) for h in ast.walk(fn) if isinstance(h, ast.ExceptHandler) and h.type)


def at_base(path: str) -> str:
    return subprocess.run(
        ["git", "show", f"{BASE}:{path}"], capture_output=True, text=True, check=True
    ).stdout


def main() -> int:
    contract = "backend/tests/unit/test_live_port_guard_contract.py"
    guard = "backend/tests/support/live_port_guard.py"
    head_contract = open(contract[len("backend/") :], encoding="utf-8").read()
    head_guard = open(guard[len("backend/") :], encoding="utf-8").read()

    print("HEAD deferred:", types_in(head_contract))
    print("BASE deferred:", types_in(at_base(contract)))
    print("HEAD late handlers:", handler_types(head_guard, "_rewrite_ledger_after_late_record"))
    print("BASE late handlers:", handler_types(at_base(guard), "_rewrite_ledger_after_late_record"))

    head_has = any("TypeAlias" in t for t in types_in(head_contract))
    base_has = any("TypeAlias" in t for t in types_in(at_base(contract)))
    print(f"GATE head_has_typealias={head_has} base_has_typealias={base_has}")
    print("FALSIFICATION-ANCHOR:", "OK（BASE 恒不含）" if not base_has else "BROKEN（锚跟着 HEAD 变了）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
