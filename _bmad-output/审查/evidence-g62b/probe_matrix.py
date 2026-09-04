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

    neg, pos, bad = [], [], []
    # 验伪锚: 未注入的真实源码在**两个**门下都必须放行 —— 否则整张矩阵可以
    # 被一个恒红的新门 / 恒绿的旧门平凡满足
    o, n = old_gate(real), cur._gate_verdict(real)
    if o is not None or n is not None:
        bad.append(f"验伪锚失败: 真实源码被拒 (旧={o!r} 新={n!r})")

    def _dump(kind: str, label: str, body: str, note: str):
        (HERE / f"{kind}-{label}.py.txt").write_text(
            f"# CARD-G6-2b AST 门探针 [{kind}]: {label}\n"
            "# 用法: 追加到 backend/app/api/v1/endpoints/review_app.py 源码**字符串**尾部\n"
            f"# (只在内存里拼, 不落进生产文件); 期望 = {note}\n" + body,
            encoding="utf-8",
        )

    for label in sorted(cur._AST_PROBES):
        snippet, expect = cur._AST_PROBES[label]
        _dump("probe", label, snippet, "补门前放行 / 补门后被拒")
        o, n = old_gate(real + "\n\n" + snippet), cur._gate_verdict(real + "\n\n" + snippet)
        neg.append((label, expect, o, n))
        # 分类依据取自**实测**的基线门行为, 不是脚本作者的期望表:
        #   旧放行 → 新拒 = 本卡新补的面;  旧拒 → 新拒 = 回归面 (证明本卡没把
        #   已有防线拆掉 —— ctx 判定那一改的风险恰在这里)。
        # 失败判据只有三条, 都与"旧门拦不拦"无关:
        if n is None:
            bad.append(f"{label}: 新门未拦下 — 该形态仍是漏网")
        elif expect not in n:
            bad.append(f"{label}: 新门红的身份不对 (期望含 {expect!r}, 实得 {n!r})")
        if o is not None and n is None:
            bad.append(f"{label}: 旧门拦得住、新门放行 —— 本卡把已有防线拆了")

    for label in sorted(cur._AST_ALLOWED_SHAPES):
        snippet = cur._AST_ALLOWED_SHAPES[label]
        _dump("allowed", label, snippet, "新门必须放行 (合法写法不许误伤)")
        o, n = old_gate(real + "\n\n" + snippet), cur._gate_verdict(real + "\n\n" + snippet)
        pos.append((label, o, n))
        if n is not None:
            bad.append(f"{label}: 新门误伤了合法写法 ({n!r})")

    lines = [
        "# CARD-G6-2b · AST 门探针红绿矩阵",
        "",
        f"- 「改前」门 = `{BASE_SHA[:8]}:{REL_TEST}` 里 "
        "`test_review_app_module_imports_are_closed` 的函数体本体 (git 取出后原样编译, "
        "只注入假 `_ENDPOINTS_DIR`; 本脚本不抄写任何一份门逻辑)",
        "- 「改后」门 = 当前 `_assert_module_closed()`",
        "- 验伪锚: **未注入**的真实源码在新旧两侧都放行 "
        f"(旧={'放行' if old_gate(real) is None else '拒绝'}, "
        f"新={'放行' if cur._gate_verdict(real) is None else '拒绝'})",
        "",
        "## 负向探针 — 改后必须被拒, 且拒因身份正确",
        "",
        "> 「改前」一栏是**分类**不是判据: 改前放行 = 本卡新补的面; 改前也拒 = 回归面",
        "> (证明本卡没把已有防线拆掉 —— `ctx=Store` 那一改的风险恰在这里)。",
        "> 真正的失败只有三种: 新门放行、新门红的身份不对、旧拒→新放。",
        "",
        "| 探针 | 拒因关键词 | 改前 (基线门) | 改后 (本卡门) | 类别 |",
        "|---|---|---|---|---|",
    ]
    fmt = lambda v: "✅ 放行" if v is None else "🔴 拒: `%s`" % v.replace("|", "\\|")[:90]  # noqa: E731
    for label, expect, o, n in neg:
        kind = "新补面" if o is None else "回归面"
        lines.append(f"| `{label}` | `{expect}` | {fmt(o)} | {fmt(n)} | {kind} |")
    lines += [
        "",
        "## 反向探针 — 合法写法不许被误伤",
        "",
        "> 加严的门在两个方向上都会错: 漏网(上表)与误伤(本表)。只测漏网 = 只证明了门够严,",
        "> 没证明它没坏。`下标读取保护名` 这一条在**基线门**下就是误伤 (它把 "
        "`cache[json] = value` 里读取位置的 `json` 当成了重绑定), 本卡按 Store 上下文修正。",
        "",
        "| 合法写法 | 基线门 | 本卡门 (必须放行) |",
        "|---|---|---|",
    ]
    for label, o, n in pos:
        lines.append(f"| `{label}` | {fmt(o)} | {fmt(n)} |")
    lines += ["", "## 自检", ""]
    n_new = sum(1 for _, _, o, _ in neg if o is None)
    lines += [f"- ❌ {b}" for b in bad] or [
        f"- ✅ 负向 {len(neg)} 条全部被拒且身份正确（其中 {n_new} 条新补面 = 基线门放行、"
        f"{len(neg) - n_new} 条回归面 = 基线门也拒）; 反向 {len(pos)} 条全部放行; "
        "无一条「旧拒 → 新放」; 验伪锚成立"
    ]
    (HERE / "probe-matrix.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
