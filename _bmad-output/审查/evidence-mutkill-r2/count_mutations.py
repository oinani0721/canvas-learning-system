#!/usr/bin/env python3
"""只读独立计数 + 变异写入面枚举（⛔ 不 import 被测模块）。

用 `ast.parse` 数 `MUTATIONS` / `EXPECT_MSG` / `EXPECT_MSG_EXEMPT`，并把每条变异
元组里引用到的**路径常量**解析成绝对路径 —— 写入面名单**从表里取**，不靠人眼枚举
常量定义（第一版就是这么漏掉 `VALIDATOR` / `EVLOG` 的）。
"""
from __future__ import annotations

import ast
import pathlib
import sys

TREE = pathlib.Path(__file__).resolve().parents[3]
SCRIPTS = TREE / "backend" / "scripts"
LIVE_VAULT = (TREE.parents[2] / "canvas-vault").resolve()

FILES = {
    "g32b": SCRIPTS / "g32b_mutation_gates.py",
    "g32cb": SCRIPTS / "g32cb_mutation_gates.py",
    "g32ccr1": SCRIPTS / "g32ccr1_negative_controls.py",
    "g33": SCRIPTS / "g33_mutation_gates.py",
}

#: 各脚本的树根常量名 -> 它等于哪个绝对路径（按源码里的 parents[N] 语义手算）
ROOTS = {
    "g32b": {"ROOT": TREE},
    "g32cb": {"WT": TREE},
    "g32ccr1": {"WT": TREE},
    "g33": {"BACKEND": TREE / "backend", "REPO": TREE},
}


def _eval_path(node: ast.AST, env: dict[str, object]) -> object | None:
    """把 `ROOT / "a/b"` / `WT / "a" / "b"` 这类表达式算成 Path；算不动返回 None。"""
    if isinstance(node, ast.Name):
        return env.get(node.id)
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        left = _eval_path(node.left, env)
        right = _eval_path(node.right, env)
        if isinstance(left, pathlib.Path) and isinstance(right, str):
            return left / right
        return None
    return None


def analyse(name: str, path: pathlib.Path) -> dict[str, object]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    env: dict[str, object] = dict(ROOTS[name])
    n_mut = 0
    n_expect: int | None = None
    n_exempt: int | None = None
    mut_nodes: list[ast.AST] = []

    for stmt in tree.body:
        # 模块级简单赋值：先把路径常量填进 env
        if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
            tgt = stmt.targets[0].id
            val = _eval_path(stmt.value, env)
            if val is not None and tgt not in env:
                env[tgt] = val
            if tgt == "MUTATIONS" and isinstance(stmt.value, (ast.List, ast.Tuple)):
                n_mut = len(stmt.value.elts)
                mut_nodes = list(stmt.value.elts)
            elif tgt == "EXPECT_MSG" and isinstance(stmt.value, ast.Dict):
                n_expect = len(stmt.value.keys)
            elif tgt == "EXPECT_MSG_EXEMPT" and isinstance(stmt.value, ast.Dict):
                n_exempt = len(stmt.value.keys)
        elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name) and stmt.value is not None:
            tgt = stmt.target.id
            if tgt == "EXPECT_MSG" and isinstance(stmt.value, ast.Dict):
                n_expect = len(stmt.value.keys)
            elif tgt == "EXPECT_MSG_EXEMPT" and isinstance(stmt.value, ast.Dict):
                n_exempt = len(stmt.value.keys)
            elif tgt == "MUTATIONS" and isinstance(stmt.value, (ast.List, ast.Tuple)):
                n_mut = len(stmt.value.elts)
                mut_nodes = list(stmt.value.elts)
        elif (
            isinstance(stmt, ast.AugAssign)
            and isinstance(stmt.target, ast.Name)
            and stmt.target.id == "MUTATIONS"
            and isinstance(stmt.value, (ast.List, ast.Tuple))
        ):
            n_mut += len(stmt.value.elts)
            mut_nodes += list(stmt.value.elts)

    # 写入面：**逐个元组元素整体求值**（不是 walk 里捡裸 Name —— 那样
    # `REPO / "canvas-vault" / … / "start-exam-board" / "SKILL.md"` 会被读成
    # `REPO` 本身，既漏掉真目标又报出一个假的「越界写树根」）。
    targets: set[pathlib.Path] = set()
    unresolved: set[str] = set()
    for elt in mut_nodes:
        elts = elt.elts if isinstance(elt, (ast.Tuple, ast.List)) else [elt]
        hit = False
        for sub in elts:
            v = _eval_path(sub, env)
            if isinstance(v, pathlib.Path):
                targets.add(v)
                hit = True
        if not hit:
            # 整条元组里没有任何可解析的路径 ⇒ 人核（可能是新写法）
            for sub in ast.walk(elt):
                if isinstance(sub, ast.Name) and sub.id.isupper() and sub.id != "MARK":
                    unresolved.add(sub.id)
    return {
        "mutations": n_mut,
        "expect_msg": n_expect,
        "exempt": n_exempt,
        "targets": sorted(targets),
        "unresolved_upper_names": sorted(unresolved),
    }


EXPECT = {  # 卡文 §〇 声称值 —— 与实测互证，不等即非零退出
    "g32b": (138, 99, 39),
    "g32cb": (9, 9, 0),
    "g32ccr1": (11, 11, 0),
    "g33": (18, None, None),
}

bad = 0
all_targets: set[pathlib.Path] = set()
for name, path in FILES.items():
    r = analyse(name, path)
    exp = EXPECT[name]
    got = (r["mutations"], r["expect_msg"], r["exempt"])
    mark = "OK " if got == exp else "MISMATCH"
    if got != exp:
        bad += 1
    print(f"{mark} {name:9s} MUTATIONS={r['mutations']} EXPECT_MSG={r['expect_msg']} EXEMPT={r['exempt']}  (卡文声称 {exp})")
    for t in r["targets"]:
        rel = t.relative_to(TREE) if TREE in t.parents else t
        inside = TREE in t.parents
        live = LIVE_VAULT == t or LIVE_VAULT in t.parents
        if not inside or live:
            bad += 1
            print(f"     ⛔ 写入面越界 {t}")
        print(f"     target in_lane={inside!s:5s} in_live={live!s:5s} exists={t.exists()!s:5s} {rel}")
    all_targets |= set(r["targets"])
    if r["unresolved_upper_names"]:
        print(f"     未解析的大写名(需人核): {r['unresolved_upper_names']}")

print("=== 去重后的全部变异写入面 ===")
for t in sorted(all_targets):
    print(t.relative_to(TREE) if TREE in t.parents else t)
print(f"VERDICT: {'PASS' if bad == 0 else f'FAIL({bad})'}")
sys.exit(0 if bad == 0 else 1)
