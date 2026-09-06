#!/usr/bin/env python3
"""归因变异：证明每条新增反例是被**它对应的那条规则**拦下的，不是被别的既有规则。

做法：对每条规则做一个「只关掉这条规则」的变异体（写进临时文件，**不碰生产文件**），
然后看它点名的那些反例是否变成 MISSED。若变异后仍被抓，说明那条反例的绿其实来自
别处，它并没有守住这条规则。

三态判定（防假杀 / 假归因）：
  * MISSED  —— 变异后该反例不再被抓 ⇒ 归因成立
  * STILL   —— 变异后仍被抓 ⇒ 归因**不成立**，那条反例守的不是这条规则
  * SYNTAX  —— 变异体语法不合法（编译期就死）⇒ 变异无效，结论作废
每个变异都断言锚点 count == 1（锚点漂移会让变异静默不生效）。
"""

import ast
import importlib.util
import pathlib
import sys

W = pathlib.Path("/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y8-w4-ast")
SRC = W / "backend/scripts/lifespan_isolation_negative_control.py"
TMP = W / "backend/scripts/_attr_mut_tmp.py"

BASE = SRC.read_text(encoding="utf-8")
BASE_SHA = __import__("hashlib").sha256(BASE.encode()).hexdigest()

# (变异名, 锚点, 替换, 它应该让哪些反例 label 前缀变 MISSED)
MUTANTS = [
    (
        "(a) 整条退回旧行为：`if not node.args: continue`（两半一起关）",
        """            target = _enter_context_arg(node)
            if target is None:""",
        """            if not node.args:
                continue
            target = node.args[0]
            if False:""",
        ["(a)-1", "(a)-2"],
    ),
    (
        "(a) 只关「取 cm=」这一半，保留 fail-closed（看 (a)-1 是否有两层守护）",
        "    for kw in call.keywords:\n        if kw.arg == _ENTER_CONTEXT_CM_PARAM:\n            return kw.value\n    for kw in call.keywords:\n        if kw.arg is not None:\n            return kw.value\n    return None",
        "    return None",
        [],  # 期望空：这条只用来观察连带效果
    ),
    (
        "(b) 去掉 IfExp 展开",
        "        if isinstance(ctx, ast.IfExp):",
        "        if False and isinstance(ctx, ast.IfExp):",
        [],  # 期望空：实测被 (c) 三分兜住，见输出的连带列
    ),
    (
        "(c) 去掉 NamedExpr 递归",
        "    if isinstance(expr, ast.NamedExpr):\n        # `enter_context(client := TestClient(app))`",
        "    if False and isinstance(expr, ast.NamedExpr):\n        # `enter_context(client := TestClient(app))`",
        [],  # 期望空：同上，承重体现在正例 c1
    ),
    (
        "(c) 三分退回「不可证即放行」",
        "    exempt = _unprovable_context_exempt(index, node, scope, expr, how)\n    if exempt is not None:\n        return",
        "    exempt = _unprovable_context_exempt(index, node, scope, expr, how)\n    if True:\n        return",
        # 期望里**不含** (b)-1/(b)-2/(c)-1：第二轮实测它们在三分被关掉后**仍被抓**——
        # 各自由 IfExp 展开与 NamedExpr 递归独立抓到（(b) 与 (c) 互为冗余，不是单点）。
        ["(c)-2", "(c)-4"],
    ),
    (
        "(c)-C2 调用面无条件放行（不收回部分-main 工厂）",
        '        if index.factory_returns_any_main(expr.func, node, scope):\n            return None\n        return "C2:call-surface-cross-function"',
        '        return "C2:call-surface-cross-function"',
        ["(c)-3"],
    ),
    (
        "(d) 解包退回「整体来源原样传给每个元素」（旧行为）",
        "                self._bind_target(elt, pos, elts[i] if elts is not None else O_UNKNOWN, scope)",
        "                self._bind_target(elt, pos, origin, scope)",
        ["(d)-1"],
    ),
    (
        "(d) 去掉 Delete 绑定",
        "        if isinstance(stmt, ast.Delete):",
        "        if False and isinstance(stmt, ast.Delete):",
        ["(d)-2"],
    ),
    (
        "(d) 去掉 match capture 绑定",
        '                    self._record_match_captures(getattr(sub, "pattern", None), scope)',
        "                    pass  # MUTANT: 不绑 match capture",
        ["(d)-3"],
    ),
    (
        "(f)-④ 去掉「形参被重绑定则失格」",
        "                if any(pos != (0, 0) for pos, _ in own.sorted_bindings(isolated_param)):\n                    continue",
        "                if False:\n                    continue",
        ["(f)-1"],
    ),
    (
        "(f)-⑤ yield 检查退回「体内有 yield 即可」",
        "                if not all(isinstance(y, ast.Yield) and _ref_path(y.value) == isolated_param for y in yields):\n                    continue",
        "                if False:\n                    continue",
        ["(f)-2"],
    ),
    (
        "(f)-⑥ 去掉同名重定义聚合（退回 add-only 覆盖）",
        "            if key in verdicts and verdicts[key] != idx:\n                verdicts[key] = None  # 同名多定义裁定不一致 ⇒ 整 key 失格\n            else:\n                verdicts[key] = idx",
        "            if idx is not None:\n                verdicts[key] = idx\n            elif key not in verdicts:\n                verdicts[key] = None",
        ["(f)-3"],
    ),
]


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    ref = load(SRC, "_attr_ref")
    labels = [lab for lab, _ in ref._AST_MUST_FLAG]
    print(f"生产文件 sha256[:16] = {BASE_SHA[:16]}   must_flag = {len(labels)} 条\n")

    bad = []
    for i, (name, old, new, expect) in enumerate(MUTANTS, 1):
        n = BASE.count(old)
        if n != 1:
            print(f"[{i:2d}] ❌ 锚点 count={n}（应为 1）— 变异未生效，结论作废：{name}")
            bad.append(name)
            continue
        mutated = BASE.replace(old, new)
        try:
            ast.parse(mutated)
        except SyntaxError as e:
            print(f"[{i:2d}] ❌ SYNTAX-INVALID（变异体编译期就死，结论作废）：{name} — {e}")
            bad.append(name)
            continue
        modname = f"_attr_mut_{i}"
        try:
            TMP.write_text(mutated, encoding="utf-8")
            mod = load(TMP, modname)
            missed = {lab for lab, s in mod._AST_MUST_FLAG if not mod.analyze_source(s, "<x>")}
            fps = {lab for lab, s in mod._AST_MUST_PASS if mod.analyze_source(s, "<x>")}
        finally:
            if TMP.exists():
                TMP.unlink()
            sys.modules.pop(modname, None)

        hit, stay = [], []
        for pref in expect:
            got = [lab for lab in labels if lab.startswith(pref)]
            assert got, f"找不到反例前缀 {pref}"
            for lab in got:
                (hit if lab in missed else stay).append(lab)
        extra = sorted(missed - {lab for lab in labels for pref in expect if lab.startswith(pref)})
        status = ("ℹ️ 观察项（无点名反例）" if not expect else ("✅ 归因成立" if not stay else "❌ 归因不成立"))
        if stay:
            bad.append(name)
        print(f"[{i:2d}] {status}  {name}")
        print(f"        点名反例变 MISSED: {[l.split('：')[0] for l in hit] or '（无）'}")
        if stay:
            print(f"        ⚠️ 仍被抓（说明它守的不是这条规则）: {[l.split('：')[0] for l in stay]}")
        if extra:
            print(f"        ℹ️ 连带 MISSED（这条规则也在守它们）: {[l.split('：')[0] for l in extra]}")
        if fps:
            print(f"        ℹ️ 连带正例翻红: {[l.split('：')[0] for l in fps]}")

    now = __import__("hashlib").sha256(SRC.read_text(encoding="utf-8").encode()).hexdigest()
    print(f"\n生产文件跑后 sha256[:16] = {now[:16]}  ⇒ {'逐字节未变 ✅' if now == BASE_SHA else '被改动 ❌'}")
    print(f"结论：{len(MUTANTS) - len(bad)}/{len(MUTANTS)} 条归因成立")
    return 1 if (bad or now != BASE_SHA) else 0


if __name__ == "__main__":
    sys.exit(main())
