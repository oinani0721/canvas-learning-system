#!/usr/bin/env python3
"""CARD-PYRIGHT-DEBT-rest: 位置默认 Field(x, ...) -> Field(default=x, ...) 机械改写。

只做一件事: 在**第一个位置实参**的起始处插入 b"default="。
- 表达式本身逐字不动(多行形态天然兼容, 因为只插入不重排)
- 其余关键字实参原样不动
- Field(..., ) 必填形态不动(第一个位置实参是 Ellipsis 常量时跳过)
- Field(*args) 形态(ast.Starred)拒绝改写并报错退出 —— `default=*x` 非法语法

col_offset 是 UTF-8 **字节**偏移, 故按行的 bytes 操作。
"""
import ast, pathlib, sys, collections

def targets(tree):
    out = []
    for n in ast.walk(tree):
        if not isinstance(n, ast.Call):
            continue
        fn = n.func
        name = fn.id if isinstance(fn, ast.Name) else (fn.attr if isinstance(fn, ast.Attribute) else None)
        if name != "Field" or not n.args:
            continue
        a0 = n.args[0]
        if isinstance(a0, ast.Constant) and a0.value is Ellipsis:
            continue
        if isinstance(a0, ast.Starred):
            raise SystemExit(f"REFUSE: Field(*args) 形态 at line {a0.lineno}")
        out.append((a0.lineno, a0.col_offset))
    return out

def rewrite(path, apply):
    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src)
    tg = targets(tree)
    if not tg:
        return 0
    lines = src.splitlines(keepends=True)
    # 同一行可能多处 -> 按 (行, 列) 降序插入, 避免偏移失效
    for lineno, col in sorted(tg, reverse=True):
        b = lines[lineno - 1].encode("utf-8")
        lines[lineno - 1] = (b[:col] + b"default=" + b[col:]).decode("utf-8")
    new = "".join(lines)
    # 自检: 改写后必须仍可解析, 且目标数归 0
    t2 = ast.parse(new)
    assert not targets(t2), f"{path}: 改写后仍有位置默认残留"
    if apply:
        path.write_text(new, encoding="utf-8")
    return len(tg)

def main():
    apply = "--apply" in sys.argv
    roots = [a for a in sys.argv[1:] if not a.startswith("--")]
    per = collections.Counter()
    for root in roots:
        rp = pathlib.Path(root)
        files = sorted(rp.rglob("*.py")) if rp.is_dir() else [rp]
        for p in files:
            c = rewrite(p, apply)
            if c:
                per[str(p)] = c
    print(("APPLIED" if apply else "DRYRUN"), "total", sum(per.values()), "files", len(per))
    for f, c in sorted(per.items(), key=lambda x: -x[1]):
        print(f"{c:4d} {f}")

main()
