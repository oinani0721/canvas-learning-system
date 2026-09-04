"""CARD-CX-G6-2b-R1 · AST 门补审探针台（完成条件 c / d / e 的证据脚本）。

跑法（从 backend/ 起，用本树 venv）:
    PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. \\
      .venv/bin/python ../_bmad-output/审查/evidence-g62b/probe_r1.py

与同目录 `probe_matrix.py` 的分工
--------------------------------
`probe_matrix.py` 拿**基线 commit** `1f249b33` 的门函数体做「改前」对照，回答的是
「这条面是不是本卡新补的」。它回答不了「当前门里**哪几行**在承重」——一条探针
可以同时被两条规则拦下，拆掉其中任何一条它都还是红的（假承重）。

本脚本换一种问法：**定向变异**。逐条把当前门里被点名的那几行拆掉（`assert` 换
`pass`、`isinstance` 判据换成恒假），再跑指定探针；只有那条探针从「红」变成
「放行」，才算这几行**独家承重**。同一次变异里另跑一条**对照探针**，它必须仍然
红——否则说明我拆的不是那条规则，而是把门整个弄坏了（那样任何探针都会变绿，
「承重」就成了平凡真命题）。

变异只在**内存字符串**上做：读当前测试文件源码 → 字符串替换 → `compile`/`exec`
成一个临时命名空间。磁盘上的生产文件与测试文件一个字节都不碰，所以不存在
「变异体残留」「还原漏跑」这一类事故面（历史教训：变异脚本 SIGTERM 绕过
finally、`+=` 追加在执行块之后）。脚本末尾仍对两个源文件做 sha256 前后比对，
作为这条声明的**外部锚点**——自称不落盘不算数，要有独立证据。

输出: probe-r1.md（矩阵）+ probe-r1-*.py.txt（每条新探针的注入片段）。
退出码 0 = 全部结论与预期一致；1 = 有一条对不上（详见 md 的自检段）。
"""

from __future__ import annotations

import ast
import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
BACKEND = REPO / "backend"
TEST_PY = BACKEND / "tests" / "unit" / "test_review_app.py"
PROD_PY = BACKEND / "app" / "api" / "v1" / "endpoints" / "review_app.py"


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _build_gate(test_src: str, tag: str):
    """把一份测试模块源码文本编译成命名空间，返回 (verdict_fn, ns)。

    `__file__` 必须设成真实测试文件路径 —— 模块里的
    `_ENDPOINTS_DIR = Path(__file__).resolve().parents[2] / "app" / …` 靠它定位生产源码。
    """
    ns: dict = {"__file__": str(TEST_PY), "__name__": f"_g62b_r1_{tag}"}
    exec(compile(test_src, f"<gate:{tag}>", "exec"), ns)  # noqa: S102

    def verdict(src: str):
        """跑门: 返回拒因首行 (None = 放行)。"""
        try:
            ns["_assert_module_closed"](src)
        except BaseException as exc:  # noqa: BLE001
            return f"{type(exc).__name__}: {exc}".splitlines()[0][:150]
        return None

    return verdict, ns


# ══════════════════════════════════════════════════════════════════════
# 一 · 新探针（完成条件 c 的 ①③④ 与 d）—— 跑的是**未变异的当前门**
# ══════════════════════════════════════════════════════════════════════
#: label → (注入片段, 预期结论, 说明)
#: 预期结论: "REJECT:<关键词>" = 必须被拒且拒因含该词; "ALLOW" = 当前门实测放行(洞)。
_NEW_PROBES: dict[str, tuple[str, str, str]] = {
    # ── (c)① 洞 ①: _root_name 根不是 Name 时返回空串 → 写路径检查 fail-OPEN ──
    # 片段里的调用取自白名单 (_js_json)，否则红的会是「白名单外调用」而不是被测规则。
    "洞①-调用结果属性写": (
        '_js_json(1).dumps = lambda value, **kwargs: "wrong"\n',
        "REJECT:根不可解析",
        "根是 ast.Call → _root_name 返回空串。**本卡已收紧**：黑名单消费点上「取不到根」"
        "直接拒（收紧前实测放行，见 git diff 与 probe-matrix.md 的「改前」栏）",
    ),
    # 这一条不含任何调用，最干净：运行时改掉的就是受保护的 json.dumps 本体。
    "洞①-布尔短路属性写": (
        '(json or list).dumps = lambda value, **kwargs: "wrong"\n',
        "REJECT:根不可解析",
        "根是 ast.BoolOp → 空串。json 为真值，运行时改的就是 json.dumps 本体 —— "
        "这是洞①里最直接的绕过形态（不留别名、不碰任何保护名的 Store 位置）。**本卡已收紧**",
    ),
    # 三元同理，换一种表达式形态确认不是 BoolOp 专属。
    "洞①-三元属性写": (
        '(json if _PAGE_TEMPLATE else list).dumps = lambda value, **kwargs: "wrong"\n',
        "REJECT:根不可解析",
        "根是 ast.IfExp → 空串。**本卡已收紧**（换一种表达式形态确认收紧不是 BoolOp 专属）",
    ),
    # 对照: 根**是** Name 时同一条路径必须拒 —— 证明放行来自「取不到根」而不是
    # 「Attribute 写整个不检查」。少了这条，上面三条的 ALLOW 无法归因。
    "洞①-对照-根是Name": (
        '_STATUS_META.dumps = lambda value, **kwargs: "wrong"\n',
        "REJECT:受保护对象",
        "同一条 Attribute-Store 路径，根名可解析 → 命中黑名单 → 拒（洞①的归因对照）",
    ),
    # ── (c)③ global / nonlocal ──
    "global-声明加赋值": (
        'def _probe_g1():\n    global _PAGE_TEMPLATE\n    _PAGE_TEMPLATE = "wrong"\n',
        "REJECT:受保护名",
        "ast.Global 本身没有专门检查，但赋值语句的 Name-Store 目标被 _flag_targets 抓住",
    ),
    "global-声明加for绑定": (
        "def _probe_g2():\n    global json\n    for json in ():\n        pass\n",
        "REJECT:受保护名",
        "global + for 目标绑定 —— 走 ast.For 分支",
    ),
    "global-声明加del": (
        "def _probe_g3():\n    global json\n    del json\n",
        "REJECT:受保护名",
        "global + del —— 走 ast.Delete 分支",
    ),
    "nonlocal-声明加赋值": (
        'def _probe_n1():\n    json = 1\n\n    def _inner():\n        nonlocal json\n        json = "wrong"\n\n    return _inner\n',
        "REJECT:受保护名",
        "nonlocal 同理；且外层 `json = 1` 本身已是函数内重绑定，两处都该红",
    ),
    # 纯声明不赋值 = 不改变任何绑定 → 放行是**正确**行为，不是洞。
    "global-纯声明不赋值": (
        "def _probe_g4():\n    global json\n    return _js_json(1)\n",
        "ALLOW",
        "只有 global 声明、没有赋值 → 绑定未被改变 → 放行是正确语义，不是漏网",
    ),
    # ── (c)④ 装饰器 Attribute 分支: 只查尾部 attr + 根名，中间层不查 ──
    "装饰器-链式中间层": (
        "@request.app.router.get\ndef _probe_dc1():\n    pass\n",
        "REJECT:非白名单装饰器接收者",
        "本卡初版实测**放行**（尾 attr 'get' ∈ _ALLOWED_CALL_ATTRS、根名 'request' ∈ "
        "_ALLOWED_RECEIVERS，中间 .app.router 无人校验）。Codex round-1 HIGH-3 指出它已构成"
        "实际的隐式调用面 → 本卡把装饰器接收者改成与 Call 分支同口径的 unparse 全路径比对，"
        "现在拒。修复前后的对照见 codex-verify-r1-ast.md",
    ),
    # 同一条表达式**作为调用**必须被拒 —— 证明这是装饰器分支与 Call 分支的口径分叉，
    # 而不是「这个形态本来就允许」。
    "装饰器-链式对照-同表达式作调用": (
        "_probe_dc2 = request.app.router.get()\n",
        "REJECT:非白名单接收者",
        "Call 分支用 ast.unparse 全路径比对 → 'request.app.router' 不在白名单 → 拒。"
        "同一表达式作无括号装饰器却放行 = 两条分支口径不一致",
    ),
    # ── (d) 洞 ②: request 形参注解豁免面窄于合法集 ──
    "洞②-限定名注解": (
        "def _probe_r1(request: fastapi.Request):\n    return request\n",
        "REJECT:受保护名",
        "FastAPI 合法写法；_root_name 下钻到 'fastapi' ≠ 'Request' → 误拒（fail-closed 方向）",
    ),
    "洞②-Annotated注解": (
        "def _probe_r2(request: Annotated[Request, None]):\n    return request\n",
        "REJECT:受保护名",
        "FastAPI 合法写法；Subscript 下钻到 'Annotated' ≠ 'Request' → 误拒。"
        "（真实写法里第二个参数是 Depends()，那会先撞「白名单外调用」，"
        "换成 None 才能隔离出注解判定这一条）",
    ),
    "洞②-字符串注解": (
        'def _probe_r3(request: "Request"):\n    return request\n',
        "REJECT:受保护名",
        "PEP 563 / 手写字符串注解；ast.Constant 不是 Name/Attribute/Subscript → 空串 → 误拒",
    ),
    "洞②-Annotated带Depends原样": (
        "def _probe_r4(request: Annotated[Request, Depends()]):\n    return request\n",
        "REJECT:受保护名",
        "卡文点名的原样写法。实测拒因**就是**洞②那条（参数遮蔽）而不是「白名单外调用」——"
        "`ast.walk` 是 BFS（内部用 deque），FunctionDef 先于它的子节点 Call 出队，"
        "参数遮蔽检查先触发。写这条前我预期它会先撞 Call 白名单，实测推翻了该预期",
    ),
    # 对照: 直接注解必须放行 —— 证明上面三条的 REJECT 来自注解形态而非「request 恒拒」。
    "洞②-对照-直接注解": (
        "def _probe_r5(request: Request):\n    return request\n",
        "ALLOW",
        "唯一被豁免的写法（_root_name 直接得到 'Request'）——洞②的归因对照",
    ),
}


# ══════════════════════════════════════════════════════════════════════
# 二 · 定向变异承重矩阵（完成条件 c② 与 e）
# ══════════════════════════════════════════════════════════════════════
#: 变异名 → (原文片段, 替换片段, 被测探针 → 该探针在变异后的期望, 说明)
#: 「被测探针」取自当前测试模块的 _AST_PROBES，形态与拒因关键词都由生产测试文件
#: 自己定义，本脚本不抄写。变异后期望 "ALLOW" = 这几行独家承重；期望
#: "REJECT" = 对照探针，必须仍然红（证明变异没把门整个弄坏）。
_MUTATIONS: dict[str, tuple[str, str, dict[str, str], str]] = {
    # ── (e) :503 重复定义收口 ──
    "E-dupes收口": (
        '    dupes = sorted(n for n, c in definitions.items() if c > 1)\n'
        '    assert not dupes, f"受保护名有多个模块级定义点: {dupes} — 后一个静默顶掉前一个, 而两个都各自享受了定义豁免"\n',
        "    pass  # MUTANT-E: dupes 收口整条拆除\n",
        {
            "重复定义-def": "ALLOW",
            "重复定义-模板": "ALLOW",
            # 对照: 走 def/class 名遮蔽那条路径，与 dupes 无关，必须仍红
            "重复定义-class": "REJECT",
            "模块级覆盖-import名": "REJECT",
        },
        "拆掉 :503-:504 两行后，两条「第二个定义点」探针必须放行 = 这两行独家承重",
    ),
    # ── (c)② match 三类绑定 ──
    "C2-match三类绑定": (
        "        if isinstance(node, ast.MatchAs) and node.name:\n"
        '            _flag_rebind(node.name, "match 捕获绑定")\n'
        "        if isinstance(node, ast.MatchStar) and node.name:\n"
        '            _flag_rebind(node.name, "match 星号捕获绑定")\n'
        "        if isinstance(node, ast.MatchMapping) and node.rest:\n"
        '            _flag_rebind(node.rest, "match **rest 绑定")\n',
        "        pass  # MUTANT-C2: match 三类绑定检查整体拆除\n",
        {
            "match-捕获": "ALLOW",
            "match-星号": "ALLOW",
            "match-rest": "ALLOW",
            # 对照: 同样是「赋值语句之外的绑定形态」，但走 ast.For 分支
            "for-目标": "REJECT",
            "海象": "REJECT",
        },
        "match 绑定名不产生 Store 位置的 Name —— 拆掉这三条后三条探针必须全部放行",
    ),
    # ── (c)④ 装饰器 Attribute 分支的接收者断言 ──
    "C4-装饰器接收者": (
        '                    dec_recv = ast.unparse(dec.value).split("(", 1)[0]\n'
        "                    assert dec_recv in _ALLOWED_RECEIVERS, (\n"
        '                        f"非白名单装饰器接收者 @{dec_recv}.{dec.attr} — 只查方法名挡不住任意对象"\n'
        "                    )\n",
        "                    pass  # MUTANT-C4: 装饰器接收者断言拆除\n",
        {
            "装饰器-非白名单接收者": "ALLOW",
            # 对照: 装饰器的另外两种形态走 else 分支，与接收者断言无关
            "装饰器-下标取内建": "REJECT",
            "装饰器-lambda包裹": "REJECT",
            "无括号装饰器": "REJECT",
        },
        "拆掉接收者断言后 @Foo.get 必须放行 = 这三行独家承重（只查方法名挡不住任意对象）",
    ),
    # ── (c)① 洞 ① 的收紧本身: 「根取不到就拒」这几行独家承重 ──
    "C1b-根不可解析收紧": (
        "                if not root:\n",
        "                if False:  # MUTANT-C1b: 根不可解析的拒绝拆除 (回到收紧前的 fail-open)\n",
        {
            "根不可解析-调用结果属性写": "ALLOW",
            "根不可解析-布尔短路属性写": "ALLOW",
            "根不可解析-三元属性写": "ALLOW",
            # 对照: 根**可**解析的写路径走下一个 if，与本次收紧无关，必须仍红
            "受保护对象-下标写": "REJECT",
            "元组内属性目标": "REJECT",
        },
        "拆掉「根取不到就拒」后三条洞①探针必须放行 —— 这既证明这几行独家承重, "
        "也复现了收紧**之前**的 fail-open 行为（负控体是代码本身的上一形态, 不是手工编的坏法）",
    ),
    # ── (c)① 洞 ① 的归因: Attribute/Subscript 写路径检查本体 ──
    "C1-写路径根名检查": (
        "            elif isinstance(sub, (ast.Attribute, ast.Subscript)) and isinstance(sub.ctx, (ast.Store, ast.Del)):\n",
        "            elif False:  # MUTANT-C1: 写路径根名检查拆除\n",
        {
            "受保护对象-下标写": "ALLOW",
            "元组内属性目标": "ALLOW",
            # 对照: Name-Store 那半条不受影响
            "模块级覆盖-import名": "REJECT",
            "for-目标": "REJECT",
        },
        "证明「受保护对象内部被写」这条防线由这一支 elif 独家承重（洞①的收紧也挂在这一支里, "
        "所以拆掉整支时洞①探针一并放行 —— 那是 C1b 单独测的）",
    ),
}


def main() -> int:  # noqa: C901
    sys.path.insert(0, str(BACKEND))
    sys.dont_write_bytecode = True

    sha_before = {"test": _sha(TEST_PY), "prod": _sha(PROD_PY)}
    test_src = TEST_PY.read_text(encoding="utf-8")

    cur_verdict, cur_ns = _build_gate(test_src, "current")
    real = cur_ns["_review_app_src"]()
    bad: list[str] = []

    # 验伪锚: 未注入的真实源码必须放行。少了它，「探针全被拒」可由恒红的门平凡满足。
    anchor = cur_verdict(real)
    if anchor is not None:
        bad.append(f"验伪锚失败: 未注入的真实源码被当前门拒绝 ({anchor!r})")

    # ── 一 · 新探针 ──
    new_rows = []
    for label, (snippet, expect, note) in _NEW_PROBES.items():
        (HERE / f"probe-r1-{label}.py.txt").write_text(
            f"# CARD-CX-G6-2b-R1 探针: {label}\n"
            "# 用法: 追加到 review_app.py 源码**字符串**尾部（只在内存里拼, 不落进生产文件）\n"
            f"# 预期: {expect}  —  {note}\n" + snippet,
            encoding="utf-8",
        )
        try:
            ast.parse(real + "\n\n" + snippet)
        except SyntaxError as exc:
            bad.append(f"{label}: 探针片段不是合法 Python ({exc}) — 测的会是语法错不是门")
            new_rows.append((label, expect, f"SyntaxError: {exc}", note))
            continue
        got = cur_verdict(real + "\n\n" + snippet)
        if expect == "ALLOW":
            if got is not None:
                bad.append(f"{label}: 预期放行, 实得拒绝 ({got!r})")
        else:
            kw = expect.split(":", 1)[1]
            if got is None:
                bad.append(f"{label}: 预期被拒(含 {kw!r}), 实得放行")
            elif kw not in got:
                bad.append(f"{label}: 拒因身份不对 (期望含 {kw!r}, 实得 {got!r})")
        new_rows.append((label, expect, got, note))

    # ── 二 · 定向变异 ──
    mut_rows = []
    for mname, (old, new, probes, note) in _MUTATIONS.items():
        n_hit = test_src.count(old)
        if n_hit != 1:
            bad.append(f"变异 {mname}: 原文片段在测试文件里命中 {n_hit} 次 (须恰好 1) — 变异点定位失败")
            mut_rows.append((mname, "定位失败", {}, note))
            continue
        mutated_verdict, _ = _build_gate(test_src.replace(old, new, 1), f"mut_{mname}")
        # 变异体自身的验伪锚: 拆一条规则不该让真实源码变红
        m_anchor = mutated_verdict(real)
        if m_anchor is not None:
            bad.append(f"变异 {mname}: 变异体把未注入的真实源码也拒了 ({m_anchor!r}) — 变异改坏了门本体")
        results = {}
        for plabel, want in probes.items():
            snippet, kw = cur_ns["_AST_PROBES"][plabel]
            before = cur_verdict(real + "\n\n" + snippet)
            after = mutated_verdict(real + "\n\n" + snippet)
            results[plabel] = (want, before, after)
            # 变异前所有被点名探针都必须是红的 —— 否则「变异后变绿」无从谈起
            if before is None:
                bad.append(f"变异 {mname} / 探针 {plabel}: 变异**前**就放行, 承重命题不成立")
            elif kw not in before:
                bad.append(f"变异 {mname} / 探针 {plabel}: 变异前拒因身份不对 (期望含 {kw!r}, 实得 {before!r})")
            if want == "ALLOW" and after is not None:
                bad.append(
                    f"变异 {mname} / 探针 {plabel}: 拆了被点名的行, 探针仍红 ({after!r}) — "
                    "该探针另有防线兜底, 这几行不是独家承重"
                )
            if want == "REJECT":
                # 对照探针不能只查「非空」(Codex round-1 MEDIUM-2): 变异若把某个分支
                # 弄成 NameError/TypeError, 那也是「非空」, 于是局部损坏会被记成「仍红」。
                # 必须连**拒因身份**一起比 —— 与变异前逐字同一条规则才算对照成立。
                if after is None:
                    bad.append(
                        f"变异 {mname} / 对照 {plabel}: 对照探针也变绿了 — 变异把门整个弄坏了, "
                        "「承重」成了平凡真命题"
                    )
                elif kw not in after:
                    bad.append(
                        f"变异 {mname} / 对照 {plabel}: 变异后仍红, 但**拒因身份变了** "
                        f"(期望含 {kw!r}, 实得 {after!r}) — 多半是变异让该分支抛了别的异常, "
                        "不能算「这条防线没被动到」"
                    )
        mut_rows.append((mname, "ok", results, note))

    sha_after = {"test": _sha(TEST_PY), "prod": _sha(PROD_PY)}
    if sha_before != sha_after:
        bad.append(f"落盘自证失败: 源文件 sha 变了 before={sha_before} after={sha_after}")

    # ── 输出 ──
    fmt = lambda v: "✅ 放行" if v is None else "🔴 拒: `%s`" % str(v).replace("|", "\\|")[:88]  # noqa: E731
    L = [
        "# CARD-CX-G6-2b-R1 · AST 门补审探针矩阵",
        "",
        "> 生成: `probe_r1.py`（本目录）。与 `probe-matrix.md` 的分工：那份用**基线 commit**",
        "> `1f249b33` 的门做「改前」对照，回答「这条面是不是本卡新补的」；本份用**定向变异**",
        "> 回答「当前门里**哪几行**在承重」。一条探针可以同时被两条规则拦下，只看「改前放行/",
        "> 改后拒绝」分辨不出假承重。",
        "",
        "## 〇 落盘自证",
        "",
        "变异只在内存字符串上做（读源码 → `str.replace` → `compile`/`exec`），磁盘文件不碰。",
        "自称不算数，下面是外部锚点：",
        "",
        "| 文件 | 跑前 sha256 | 跑后 sha256 | 相同 |",
        "|---|---|---|---|",
        f"| `backend/tests/unit/test_review_app.py` | `{sha_before['test'][:16]}…` | "
        f"`{sha_after['test'][:16]}…` | {'✅' if sha_before['test'] == sha_after['test'] else '❌'} |",
        f"| `backend/app/api/v1/endpoints/review_app.py` | `{sha_before['prod'][:16]}…` | "
        f"`{sha_after['prod'][:16]}…` | {'✅' if sha_before['prod'] == sha_after['prod'] else '❌'} |",
        "",
        f"验伪锚（未注入的真实源码在当前门下）：{'✅ 放行' if anchor is None else '❌ 被拒 ' + repr(anchor)}",
        "",
        "## 一 新探针 — 当前门的实测结论（完成条件 c①③④ / d）",
        "",
        "> `ALLOW` = 实测放行。对**洞**而言这是如实记录，不是「测试通过」；",
        "> 对**对照探针**而言这是正确语义。每组洞都配了一条对照探针做归因：",
        "> 少了对照，「放行」可能来自「整条规则不存在」而不是「这一个判定分支漏了」。",
        "",
        "| 探针 | 预期 | 实测 | 说明 |",
        "|---|---|---|---|",
    ]
    for label, expect, got, note in new_rows:
        L.append(f"| `{label}` | `{expect}` | {fmt(got)} | {note} |")

    L += [
        "",
        "## 二 定向变异承重矩阵（完成条件 c② / e）",
        "",
        "> 每个变异拆掉门里被点名的那几行，再跑指定探针。**被测探针**必须由红变绿",
        "> （= 这几行独家承重）；**对照探针**必须仍然红（= 变异没把门整个弄坏，否则",
        "> 「承重」是平凡真命题）。另有一条变异体自身的验伪锚：拆一条规则不该让",
        "> 未注入的真实源码变红。",
        "",
    ]
    for mname, status, results, note in mut_rows:
        L += [f"### `{mname}`", "", f"{note}", ""]
        if status != "ok":
            L += [f"❌ {status}", ""]
            continue
        L += ["| 探针 | 角色 | 变异前 | 变异后 | 结论 |", "|---|---|---|---|---|"]
        for plabel, (want, before, after) in results.items():
            role = "被测（应变绿）" if want == "ALLOW" else "对照（应仍红）"
            ok = (after is None) if want == "ALLOW" else (after is not None)
            L.append(f"| `{plabel}` | {role} | {fmt(before)} | {fmt(after)} | {'✅' if ok else '❌'} |")
        L.append("")

    L += ["## 三 自检", ""]
    if bad:
        L += [f"- ❌ {b}" for b in bad]
    else:
        n_allow = sum(1 for _, e, _, _ in new_rows if e == "ALLOW")
        L += [
            f"- ✅ 新探针 {len(new_rows)} 条全部与预期一致"
            f"（其中 {n_allow} 条实测放行 = 洞或正确语义，见上表说明列）",
            f"- ✅ 定向变异 {len(mut_rows)} 组：被测探针全部由红变绿、对照探针全部仍红、"
            "变异体验伪锚全部成立",
            "- ✅ 落盘自证：两个源文件 sha256 跑前跑后逐字节相同",
        ]
    (HERE / "probe-r1.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
