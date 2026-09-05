"""CARD-CX-G6-2b-R1 · Codex round-1 发现的**独立复现 + 修复对照**（完成条件 g）。

规矩：报告里的每一条都先在本车道实测，再决定采信或驳回——不直接抄结论。

复现要在**报告所审的那一版**上做。本卡在读完报告后又改了门，所以只跑当前门的话，
被修好的那几条会「复现不出来」，看上去像报告说错了。因此本脚本同时加载两个门：

- **修复前** = `d9f7b544`（本卡第一个 commit，也正是 Codex 审的那一版）的测试文件，
  从 git 取出后原样编译 —— 本脚本不抄写任何一份门逻辑（自抄等于自证）。
- **修复后** = 工作树当前的 `_assert_module_closed()`。

于是每条用例有两列：修复前那列回答「报告说的漏网/误拒**是否属实**」，
修复后那列回答「本卡改完之后**还在不在**」。两列合起来才既复现了发现、又证明了修复。

每组都配一条**归因对照**：少了它，「放行」可能来自「整条规则不存在」而不是报告指出的
那个具体分支。

覆盖 AST 检查器那几条（HIGH-2 / HIGH-3 / HIGH-4 / MEDIUM-1）；
JS 状态机那条（HIGH-1）在 `verify_codex_r1_js.py`；
脚本自身缺陷那三条（MEDIUM-2 / MEDIUM-3 / LOW）读代码即可判定，结论写在验收单。

跑法（从 backend/ 起）:
    PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. \\
      .venv/bin/python ../_bmad-output/审查/evidence-g62b/verify_codex_r1.py

只在内存里拼字符串，跑完对源文件做 sha256 自证。
"""

from __future__ import annotations

import ast
import hashlib
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
BACKEND = REPO / "backend"
TEST_PY = BACKEND / "tests" / "unit" / "test_review_app.py"
PROD_PY = BACKEND / "app" / "api" / "v1" / "endpoints" / "review_app.py"

#: Codex round-1 所审的那一版 = 本卡第一个 commit
AUDITED_SHA = "d9f7b544"
REL_TEST = "backend/tests/unit/test_review_app.py"

#: label → (注入片段, 修复前预期, 修复后预期, 对应发现 + 设计说明)
#: 预期 "ALLOW" / "REJECT:<拒因关键词>"。
CASES: dict[str, tuple[str, str, str, str]] = {
    # ── HIGH-2 间接取别名（**未修**，登记交后续卡） ──
    "H2-布尔短路取别名后写": (
        '_alias_a = (json or list)\n_alias_a.dumps = lambda value, **kwargs: "wrong"\n',
        "ALLOW", "ALLOW",
        "HIGH-2：别名禁令只在赋值右侧**恰为** ast.Name 时触发；换成 BoolOp 就拿到同一个对象的"
        "引用，再经别名写属性 —— 根名 `_alias_a` 不在黑名单。**本卡未修**：堵它要做引用传播/"
        "别名追踪，是新的设计而非收紧一个判据，超出只读复核卡范围",
    ),
    "H2-元组解包取别名后写": (
        '(_alias_b, _unused) = (json, 1)\n_alias_b.dumps = lambda value, **kwargs: "wrong"\n',
        "ALLOW", "ALLOW",
        "HIGH-2：右侧是 Tuple → 同上。换一种形态确认不是 BoolOp 专属",
    ),
    "H2-海象取别名后写": (
        'if (_alias_c := json):\n    _alias_c.dumps = lambda value, **kwargs: "wrong"\n',
        "ALLOW", "ALLOW",
        "HIGH-2：NamedExpr 走 _flag_targets(node.target)，目标名不在黑名单即放行；"
        "别名禁令只挂在 Assign 上，管不到海象",
    ),
    "H2-对照-直接取别名": (
        '_alias_d = json\n_alias_d.dumps = lambda value, **kwargs: "wrong"\n',
        "REJECT:被取别名", "REJECT:被取别名",
        "HIGH-2 归因对照：右侧是裸 Name → 别名禁令命中。证明上面三条的放行来自「右侧形态」，"
        "而不是「别名禁令整个不存在」",
    ),
    # ── HIGH-3 装饰器（中间层穿透**已修**；白名单笛卡尔积**未修**） ──
    "H3-链式中间层": (
        "@request.app.router.get\ndef _probe_h3a():\n    pass\n",
        "ALLOW", "REJECT:非白名单装饰器接收者",
        "HIGH-3 主体：接收者原先只取**根名**，中间的 `.app.router` 整段穿透；而同一串表达式"
        "作为调用会被 Call 分支的 unparse 全路径比对拒 —— 一放一拒的口径分叉，宽的那条就是"
        "绕过面。**本卡已修**：装饰器分支改用同一套 unparse 全路径比对",
    ),
    "H3-白名单组合语义错配": (
        "@_STATUS_META.get\ndef _probe_h3b():\n    pass\n",
        "ALLOW", "ALLOW",
        "HIGH-3 残留：`_STATUS_META` ∈ 接收者白名单、`get` ∈ 方法名白名单，组合合法 —— 但它是"
        "`dict.get`，导入期真会调用、被装饰的名字变成 None。两张白名单是**笛卡尔积**，没有配对"
        "约束。**本卡未修**：要修得给出「哪个接收者允许哪些方法」的配对表，是新设计",
    ),
    "H3-白名单组合语义错配2": (
        "@_PAGE_TEMPLATE.replace\ndef _probe_h3c():\n    pass\n",
        "ALLOW", "ALLOW",
        "HIGH-3 残留：同上，`str.replace` 作装饰器。确认不是 dict.get 特例",
    ),
    "H3-对照-非白名单接收者": (
        "@Foo.get\ndef _probe_h3d():\n    pass\n",
        "REJECT:非白名单装饰器接收者", "REJECT:非白名单装饰器接收者",
        "HIGH-3 归因对照：接收者压根不在白名单时两版都拒 —— 证明放行来自「根名恰好在白名单」",
    ),
    # ── HIGH-4 Request（绑定**已修**；注解形态**未修**，(d) 禁改判据） ──
    "H4-Request被重绑定后仍豁免": (
        "Request = str\n\n\ndef _probe_h4a(request: Request):\n    return request\n",
        "ALLOW", "REJECT:受保护名",
        "HIGH-4 主体：`Request` 既不是调用名也不是接收者，原先不在 _BANNED_REBINDS，于是"
        "`Request = str` 之后注解拼写仍是 'Request'、豁免照给，而 FastAPI 会把它当查询参数"
        "（拿到字符串，`.url_for` 不存在）。检查器把**名字拼写**当成了类型身份。"
        "**本卡已修**：`Request` 进 _BANNED_REBINDS（黑名单加名 = 收紧，不违反「禁放宽白名单」）",
    ),
    "H4-Attribute注解也被豁免": (
        "def _probe_h4b(request: Request.__class__):\n    return request\n",
        "ALLOW", "ALLOW",
        "HIGH-4 残留：_root_name 沿 .value **下钻**到 Name('Request') → 判等成立。"
        "⇒ 本卡初版写的「豁免只认裸 Name」**不准确**，已更正注释。"
        "**本卡未修判据**：卡文 (d) 明令只改声明不动判据",
    ),
    "H4-Subscript注解也被豁免": (
        "def _probe_h4c(request: Request[0]):\n    return request\n",
        "ALLOW", "ALLOW",
        "HIGH-4 残留：Subscript 同样下钻到根 Name('Request')",
    ),
    "H4-对照-Annotated仍拒": (
        "def _probe_h4d(request: Annotated[Request, None]):\n    return request\n",
        "REJECT:受保护名", "REJECT:受保护名",
        "HIGH-4 归因对照：根名是 'Annotated' → 不豁免。同一条判据既漏网（上面两条）"
        "又误拒（洞②）—— 因为它比的是「根名等于 Request」这个拼写",
    ),
    # ── MEDIUM-1 本卡收紧带来的误拒（**保留**，登记为保守限制） ──
    "M1-普通对象条件选择后下标写": (
        "def _probe_m1(cache_a, cache_b, k, v, flag):\n    (cache_a if flag else cache_b)[k] = v\n",
        "REJECT:根不可解析", "REJECT:根不可解析",
        "MEDIUM-1：不碰任何保护名、不新增调用的正常写法，被本卡的新判据拒。反向探针集 6 条都"
        "没覆盖「非 Name 根上的普通对象写入」。**保留**：本模块是「只允许模板注入一种依赖形态」"
        "的封闭模块，宁可保守；收宽要能证明安全，归后续卡",
    ),
    "M1-对照-单一普通对象下标写": (
        "def _probe_m1b(cache, k, v):\n    cache[k] = v\n",
        "ALLOW", "ALLOW",
        "MEDIUM-1 归因对照：根是 Name 就放行 —— 误拒确实来自「根不可解析」这一条，"
        "不是「下标写整个被禁」",
    ),
}


def _build_gate(test_src: str, tag: str):
    ns: dict = {"__file__": str(TEST_PY), "__name__": f"_g62b_v_{tag}"}
    exec(compile(test_src, f"<gate:{tag}>", "exec"), ns)  # noqa: S102

    def verdict(src: str):
        try:
            ns["_assert_module_closed"](src)
        except BaseException as exc:  # noqa: BLE001
            return f"{type(exc).__name__}: {exc}".splitlines()[0][:150]
        return None

    return verdict, ns


def main() -> int:
    sys.path.insert(0, str(BACKEND))
    sys.dont_write_bytecode = True
    sha_before = (hashlib.sha256(TEST_PY.read_bytes()).hexdigest(),
                  hashlib.sha256(PROD_PY.read_bytes()).hexdigest())

    audited_src = subprocess.run(
        ["git", "show", f"{AUDITED_SHA}:{REL_TEST}"],
        cwd=REPO, capture_output=True, text=True, check=True,
    ).stdout
    before_verdict, _ = _build_gate(audited_src, "audited")
    after_verdict, ns = _build_gate(TEST_PY.read_text(encoding="utf-8"), "current")
    real = ns["_review_app_src"]()

    rows, bad = [], []
    # 验伪锚: 两个门都必须放行未注入的真实源码。少了它，整张表可以被一个恒红的门平凡满足。
    for tag, fn in (("修复前", before_verdict), ("修复后", after_verdict)):
        if (a := fn(real)) is not None:
            bad.append(f"验伪锚失败（{tag}）: 未注入的真实源码被拒 ({a!r})")

    def _check(label, tag, expect, got):
        if expect == "ALLOW":
            if got is not None:
                bad.append(f"{label}[{tag}]: 预期放行, 实得拒绝 ({got!r})")
        else:
            kw = expect.split(":", 1)[1]
            if got is None:
                bad.append(f"{label}[{tag}]: 预期被拒(含 {kw!r}), 实得放行")
            elif kw not in got:
                bad.append(f"{label}[{tag}]: 拒因身份不对 (期望含 {kw!r}, 实得 {got!r})")

    for label, (snippet, exp_b, exp_a, note) in CASES.items():
        probe = real + "\n\n" + snippet
        try:
            ast.parse(probe)
        except SyntaxError as exc:
            bad.append(f"{label}: 片段不是合法 Python ({exc})")
            rows.append((label, exp_b, exp_a, f"SyntaxError: {exc}", "-", note))
            continue
        gb, ga = before_verdict(probe), after_verdict(probe)
        _check(label, "修复前", exp_b, gb)
        _check(label, "修复后", exp_a, ga)
        rows.append((label, exp_b, exp_a, gb, ga, note))

    sha_after = (hashlib.sha256(TEST_PY.read_bytes()).hexdigest(),
                 hashlib.sha256(PROD_PY.read_bytes()).hexdigest())
    if sha_before != sha_after:
        bad.append("落盘自证失败: 源文件 sha 变了")

    fmt = lambda v: "✅ 放行" if v is None else ("🔴 拒: `%s`" % str(v).replace("|", "\\|")[:60]) if v != "-" else "-"  # noqa: E731
    # 计数只算**洞**，不算归因对照 —— 对照两列都放行是它的正确行为，
    # 把它算进「未修的洞」会让数字和说明对不上。
    n_fixed = sum(1 for lb, b, a, _, _, _ in rows if b == "ALLOW" and a != "ALLOW" and "对照" not in lb)
    n_open = sum(1 for lb, b, a, _, _, _ in rows if b == "ALLOW" and a == "ALLOW" and "对照" not in lb)
    n_ctrl = sum(1 for lb, *_ in rows if "对照" in lb)
    L = [
        "# CARD-CX-G6-2b-R1 · Codex 发现的独立复现 + 修复对照（完成条件 g）",
        "",
        "> 生成: `verify_codex_r1.py`。**先实测再采信**，且复现要在**报告所审的那一版**上做。",
        f"> 「修复前」= `{AUDITED_SHA}`（本卡第一个 commit，正是 Codex 审的那版）的测试文件，",
        "> 从 git 取出原样编译，本脚本不抄写任何门逻辑；「修复后」= 工作树当前的门。",
        "> 只跑当前门的话，被修好的那几条会「复现不出来」，看上去像报告说错了。",
        "",
        "> 每组配一条**归因对照**：少了它，「放行」可能来自「整条规则不存在」，",
        "> 而不是报告指出的那个具体分支。",
        "",
        f"验伪锚（未注入的真实源码在两个门下）：{'✅ 都放行' if not [b for b in bad if '验伪锚' in b] else '❌ 见自检'}",
        f"源文件 sha256 跑前跑后：{'逐字节相同 ✅' if sha_before == sha_after else '不同 ❌'}",
        "",
        "| 用例 | 修复前 | 修复后 | 对应发现与处置 |",
        "|---|---|---|---|",
    ]
    for label, _eb, _ea, gb, ga, note in rows:
        L.append(f"| `{label}` | {fmt(gb)} | {fmt(ga)} | {note} |")
    L += [
        "",
        "## 采信结论",
        "",
        f"- Codex 的 AST 类发现 **全部复现成立**（修复前那一列与报告描述逐条吻合）→ 予以采信。",
        f"- 本卡据此**已封** {n_fixed} 条（修复前放行 → 修复后拒）。",
        f"- 仍**登记未修** {n_open} 条洞（两列都放行；另有 {n_ctrl} 条归因对照不计入——",
        "  对照两列同色是它该有的行为）：HIGH-2 别名传播 ×3、HIGH-3 白名单笛卡尔积 ×2、",
        "  HIGH-4 注解节点形态 ×2。三类都要新设计（引用追踪 / 接收者-方法配对表 / 注解形态白名单），",
        "  不是收紧一个判据能解决的，且 HIGH-4 那条被卡文 (d)「只改声明不动判据」明令挡住。",
        "- MEDIUM-1 的误拒**保留**并登记为保守限制：本模块是「只允许模板注入一种依赖形态」的",
        "  封闭模块，宁可保守；收宽要能证明安全。",
        "",
        "## 自检",
        "",
    ]
    L += [f"- ❌ {b}" for b in bad] or ["- ✅ 全部用例的两列都与预期一致"]
    (HERE / "codex-verify-r1-ast.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
