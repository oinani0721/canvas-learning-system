"""AST 门探针红绿矩阵 (CARD-G6-2b R2/R3 的「改前 PASS / 改后 FAIL」证据)。

跑法 (从 backend/ 起, 用 card-v5-lance 的 venv):
    PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python ../_bmad-output/审查/evidence-g62b/probe_matrix.py

「改前」的门**不是**本脚本抄一份 —— 自抄等于自证。它是从基线 commit 里
取出 test_review_app_module_imports_are_closed 的**函数体本体**, 原样编译执行,
只把它读文件的那个 _ENDPOINTS_DIR 换成一个返回探针源码的假目录 (依赖注入,
不动一个字节的旧代码)。「改后」的门直接 import 当前测试模块的 _assert_module_closed。
"""

from __future__ import annotations

import ast
import importlib.util
import subprocess
import sys
from pathlib import Path

BASE_SHA = "1f249b33f0d3380fd0fe7e0b26bdf08576da54ee"
REL_TEST = "backend/tests/unit/test_review_app.py"
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
BACKEND = REPO / "backend"


class _FakeDir:
    """(_ENDPOINTS_DIR / "review_app.py").read_text() → 探针源码。"""

    def __init__(self, text: str) -> None:
        self._text = text

    def __truediv__(self, _other):
        return self

    def read_text(self, encoding: str = "utf-8") -> str:  # noqa: ARG002
        return self._text


def _load_old_gate():
    """从基线 commit 取旧门函数体, 编译成 _old_gate(fake_dir) 可调用对象。"""
    old_src = subprocess.run(
        ["git", "show", f"{BASE_SHA}:{REL_TEST}"],
        cwd=REPO, capture_output=True, text=True, check=True,
    ).stdout
    tree = ast.parse(old_src)
    fn = next(
        n for n in tree.body
        if isinstance(n, ast.FunctionDef) and n.name == "test_review_app_module_imports_are_closed"
    )
    wrapper = ast.Module(body=[fn], type_ignores=[])
    ast.fix_missing_locations(wrapper)
    import pytest  # 旧门体内用 pytest.fail

    ns: dict = {"ast": ast, "pytest": pytest}
    exec(compile(wrapper, "<old-gate@%s>" % BASE_SHA[:8], "exec"), ns)  # noqa: S102
    old_fn = ns["test_review_app_module_imports_are_closed"]

    def run(src: str):
        ns["_ENDPOINTS_DIR"] = _FakeDir(src)
        try:
            old_fn()
        except BaseException as exc:  # noqa: BLE001
            return f"{type(exc).__name__}: {exc}".splitlines()[0][:160]
        return None

    return run


def _load_new_module():
    spec = importlib.util.spec_from_file_location("_g62b_cur_test", BACKEND / REL_TEST.split("backend/")[1])
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["_g62b_cur_test"] = mod
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    sys.path.insert(0, str(BACKEND))
    sys.dont_write_bytecode = True
    old_gate = _load_old_gate()
    cur = _load_new_module()
    real = cur._review_app_src()

    rows, bad = [], []
    # 验伪锚: 未注入的真实源码在**两个**门下都必须放行 —— 否则整张矩阵可以
    # 被一个恒红的新门 / 恒绿的旧门平凡满足
    for tag, src in (("<真实源码·未注入>", real),):
        o, n = old_gate(src), cur._gate_verdict(src)
        rows.append((tag, o, n))
        if o is not None or n is not None:
            bad.append(f"验伪锚失败: 真实源码被拒 (旧={o!r} 新={n!r})")

    for label in sorted(cur._AST_PROBES):
        snippet = cur._AST_PROBES[label]
        (HERE / f"probe-{label}.py.txt").write_text(
            f"# CARD-G6-2b AST 门探针: {label}\n"
            "# 用法: 追加到 backend/app/api/v1/endpoints/review_app.py 源码**字符串**尾部\n"
            "# (只在内存里拼, 不落进生产文件); 期望 = 补门前放行 / 补门后被拒。\n"
            + snippet,
            encoding="utf-8",
        )
        src = real + "\n\n" + snippet
        o, n = old_gate(src), cur._gate_verdict(src)
        rows.append((label, o, n))
        if o is not None:
            bad.append(f"{label}: 旧门就已拦下 (探针不具鉴别力, 拒因={o!r})")
        if n is None:
            bad.append(f"{label}: 新门未拦下 — 该形态仍是漏网")
        elif "受保护名" not in n:
            bad.append(f"{label}: 新门红的身份不对 ({n!r})")

    lines = [
        "# CARD-G6-2b · AST 门探针红绿矩阵",
        "",
        f"- 「改前」门 = `{BASE_SHA[:8]}:{REL_TEST}` 里 "
        "`test_review_app_module_imports_are_closed` 的函数体本体 (git 取出后原样编译, "
        "只注入假 `_ENDPOINTS_DIR`; 本脚本不抄写任何一份门逻辑)",
        "- 「改后」门 = 当前 `_assert_module_closed()`",
        "- 期望: 改前 **放行**(门瞎) / 改后 **被拒且拒因是「受保护名…」**(门抓住且抓对了原因)",
        "",
        "| 探针 | 改前 (基线门) | 改后 (本卡门) |",
        "|---|---|---|",
    ]
    for label, o, n in rows:
        fmt = lambda v: "✅ 放行" if v is None else "🔴 拒: `%s`" % v.replace("|", "\\|")  # noqa: E731
        lines.append(f"| `{label}` | {fmt(o)} | {fmt(n)} |")
    lines += ["", "## 自检", ""]
    lines += [f"- ❌ {b}" for b in bad] or ["- ✅ 全部探针具鉴别力 (旧放行→新拒绝), 验伪锚成立"]
    (HERE / "probe-matrix.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
