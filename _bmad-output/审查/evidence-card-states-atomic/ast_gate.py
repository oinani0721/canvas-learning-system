#!/usr/bin/env python3
"""CARD-CARD-STATES-ATOMIC-WRITE 结构门 (卡文 §一(f) / §二.2)。

数 **AST 节点**，不数文本：注释里写 fsync / 字符串里写 unlink 一律不计。

⚠️ write_text 必须数 Attribute **引用**而不是 Call：改前形态
``asyncio.to_thread(tmp_file.write_text, data, "utf-8")`` 里
``tmp_file.write_text`` 是被当作值传的 Attribute，不是 Call —— 数 Call
则改前/改后同为 0，门恒绿（假绿）。

用法: python3 ast_gate.py <file.py>
"""
from __future__ import annotations

import ast
import sys


def _attr_name(node: ast.AST) -> str | None:
    """Call 的被调名：``a.b(...)`` → ``b``；``b(...)`` → ``b``。"""
    if not isinstance(node, ast.Call):
        return None
    f = node.func
    if isinstance(f, ast.Attribute):
        return f.attr
    if isinstance(f, ast.Name):
        return f.id
    return None


def _calls(tree: ast.AST, name: str) -> list[ast.Call]:
    return [n for n in ast.walk(tree) if isinstance(n, ast.Call) and _attr_name(n) == name]


def _attr_refs(tree: ast.AST, name: str) -> list[ast.Attribute]:
    """Attribute 引用（含被当作值传递的、未被调用的）。"""
    return [n for n in ast.walk(tree) if isinstance(n, ast.Attribute) and n.attr == name]


def _find_func(module: ast.Module, name: str):
    for n in ast.walk(module):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name:
            return n
    return None


def main() -> int:
    path = sys.argv[1] if len(sys.argv) > 1 else "backend/app/services/review_service.py"
    src = open(path, "r", encoding="utf-8").read()
    module = ast.parse(src)

    print(f"file={path}")

    # ── 模块顶层 import os ────────────────────────────────────────────────
    import_os = any(
        isinstance(n, ast.Import) and any(a.name == "os" for a in n.names) for n in module.body
    )
    print(f"import_os={import_os}")

    # ── _save_card_states ────────────────────────────────────────────────
    saver = _find_func(module, "_save_card_states")
    if saver is None:
        print("saver=absent")
        return 1
    print(f"saver_span={saver.lineno}-{getattr(saver, 'end_lineno', '?')}")

    to_thread = _calls(saver, "to_thread")
    print(f"to_thread={len(to_thread)}")
    for c in to_thread:
        first = ast.unparse(c.args[0]) if c.args else "<no-args>"
        print(f"  to_thread_arg0@{c.lineno}={first}")

    wt = _attr_refs(saver, "write_text")
    print(f"write_text_attr_refs={len(wt)}")
    for a in wt:
        print(f"  write_text_ref@{a.lineno}={ast.unparse(a)}")

    enc = _calls(saver, "encode")
    enc_ln = min((c.lineno for c in enc), default=None)
    tt_ln = min((c.lineno for c in to_thread), default=None)
    print(f"encode_calls={len(enc)} encode_min_lineno={enc_ln} to_thread_min_lineno={tt_ln}")
    encode_before = enc_ln is not None and tt_ln is not None and enc_ln < tt_ln
    print(f"encode_before_to_thread={encode_before}")

    # ── helper _persist_card_states_bytes ────────────────────────────────
    helper = _find_func(module, "_persist_card_states_bytes")
    if helper is None:
        print("helper=absent")
        return 0
    print(f"helper=present helper_span={helper.lineno}-{getattr(helper, 'end_lineno', '?')}")
    for name in ("fsync", "replace", "unlink", "open"):
        print(f"  helper_{name}_calls={len(_calls(helper, name))}")

    # unlink 必须落在某个 Try 的 finalbody 子树内
    final_calls: list[int] = []
    for t in ast.walk(helper):
        if isinstance(t, ast.Try):
            for stmt in t.finalbody:
                for n in ast.walk(stmt):
                    if isinstance(n, ast.Call) and _attr_name(n) == "unlink":
                        final_calls.append(n.lineno)
    print(f"  helper_unlink_in_finally={bool(final_calls)} at={final_calls}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
