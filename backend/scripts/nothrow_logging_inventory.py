#!/usr/bin/env python3
# CARD-OBS-nothrow-logging (BATCH-2026-09-01-第八批) — 存量登记（只读）
"""扫描哪些模块的日志调用**还没有**被 no-throw 包装保护。

只读: 纯 ``ast`` 静态分析, 不 import 任何项目模块, 不写任何文件。
(``sys.dont_write_bytecode`` 显式置位 —— 动态加载会把 ``__pycache__`` 写进
被扫描的树。)

四张表:
- 表一 端点层模块级 logger 绑定与包装状态 (已包装 / 未包装 / NOT-WRAPPABLE /
  EXTERNAL / 死绑定 分列);
- 表二 匿名内联日志调用 (``logging.getLogger(...).<level>(...)``, 无变量可寻址,
  模块级 Assign 判定天然看不见它们);
- 表三 f-string 首参调用 (改惰性参数的存量面; **与包装正交** —— f-string 在
  实参求值阶段就抛, 包了 nothrow 也拦不住, 唯一修法是转 %-惰性参数);
- 表四 服务层移交站点 (CARD-G4-3 验收单 :1046 点名, 本卡只登记不改, 按**函数名**
  锚定而非行号)。

判定形态与自证 (A3 备料结论):
- 已包装 = 模块级绑定的外层是 ``nothrow(...)`` 调用 (Name 或 Attribute 尾名;
  解析本文件 import 别名)。内层形态**不做断言** —— 只认外层。
- structlog 绑定 (``structlog.get_logger``) 标 NOT-WRAPPABLE: 本适配器往 kwargs
  注入 ``stacklevel``, structlog 的 ``wrap_for_formatter`` 渲染链不认识它, 会把
  它渲染成 JSON 里的多余字段 (app/core/logging.py:106 的最终 renderer)。
- 函数体内 import 进来的 logger (health.py 的 memory_logger) 标 EXTERNAL ——
  包装状态在另一个文件, 本文件判 Wrapped/Unwrapped 都是错的。
- 开跑先过**篡改自检**: 合成 ``nothrow(...)`` 必须判已包装、合成裸
  ``getLogger`` 必须判未包装 —— 只跑真语料 (可能全 UNWRAPPED) 无法区分
  "判定正确"和"判定恒返回未包装"。**一道恒 0 的门与一道恒 0 的坏门同形。**
- 结构验伪锚: rollback.py 的匿名内联调用、health.py 的 EXTERNAL logger
  —— 检不出来 = 判定函数漏了这两类, 拒绝出报告。

本表不证明什么 (打印在报告尾部): 只看模块级绑定 + 经它发出的调用 + 匿名内联。
函数内局部绑定的 logger、经 ``.inner`` 绕过包装的调用、handler/装饰器级的
保护方案, 本表看不见。
"""

import argparse
import ast
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

sys.dont_write_bytecode = True

LOG_METHODS = {"debug", "info", "warning", "warn", "error", "exception", "critical", "log", "fatal"}

HANDOFF_ANCHORS: List[Tuple[str, str, str]] = [
    ("app/services/rag_service.py", "initialize", "G4-3 记 :194"),
    ("app/services/rag_service.py", "_get_fallback_result", "G4-3 记 :209"),
    ("app/services/rag_service.py", "query", "G4-3 记 :274-287/:289-290/:326-333"),
    ("app/core/vault_scope.py", "active_vault_aliases", "G4-3 记 :133"),
    ("app/core/vault_scope.py", "resolve_vault_scope", "G4-3 记 :184-198"),
    ("app/services/memory_service.py", "get_learning_history", "G4-3 记 :665-682/:748/:843-850"),
    ("app/services/memory_service.py", "get_concept_score_history", "G4-3 记 :1080-1089"),
    ("app/clients/neo4j_client.py", "_handle_merge_learning", "G4-3 记 :746"),
    ("lib/agentic_rag/nodes.py", "multi_query_rewrite_node", "G4-3 记 :1873"),
]


# ─────────────────────────────────────────────────────────────────────────────
# AST 判定原语
# ─────────────────────────────────────────────────────────────────────────────


def _alias_table(tree: ast.Module) -> Tuple[Set[str], Set[str]]:
    """本文件里指向 nothrow 的本地别名 + nothrow_logging 的模块别名。

    Codex round-1 LOW-8/round-2 MEDIUM-8: 只认**完整模块路径**
    ``app.core.nothrow_logging`` (round-1 的尾段匹配会把 ``evil.nothrow_logging``
    判成真来源); 同时收集 ``import app.core.nothrow_logging as obs`` 的模块
    别名, 让 ``obs.nothrow(...)`` 形态也能被识别 (round-2 指出的漏判)。
    """
    names: Set[str] = set()
    module_aliases: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if mod == "app.core.nothrow_logging":
                for alias in node.names:
                    if alias.name == "nothrow":
                        names.add(alias.asname or alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "app.core.nothrow_logging":
                    module_aliases.add(alias.asname or alias.name)
    return names, module_aliases


def _local_nothrow_shadows(tree: ast.Module) -> List[Tuple[str, int]]:
    """本文件里自定义的 nothrow 名字 (def nothrow / nothrow = ...) —— 假包装源。

    Codex round-1 LOW-8: 本地 ``def nothrow(x): return x`` 会让裸 Logger 在
    AST 形态上与真包装逐字相同。检出即整文件判 SUSPECT (不可信), 不判已包装。
    """
    out: List[Tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "nothrow":
            out.append(("def", node.lineno))
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "nothrow":
                    out.append(("assign", node.lineno))
    return out


def _is_call_named(node: ast.AST, names: Set[str], attr: Optional[str] = None) -> bool:
    """nothrow(...) / obs.nothrow(...) / getLogger(...) 形态判定。

    ``attr`` 给定时只认 ``.attr`` 尾名 (Attribute 形态) 或裸名 (Name 形态)。
    """
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    if isinstance(func, ast.Name):
        return func.id in names and (attr is None or func.id == attr)
    if isinstance(func, ast.Attribute):
        return func.attr in names and (attr is None or func.attr == attr)
    return False


def _is_nothrow_call(node: ast.AST, aliases: Set[str]) -> bool:
    """nothrow(...) / obs.nothrow(...) 形态判定。

    Name 形态要求在 alias 表内 (来源已验证是 app.core.nothrow_logging);
    Attribute 形态只认**尾名** nothrow —— 模块别名 (``obs.nothrow``) 的证据
    就是尾名本身, 模块别名表只用于让 ``obs`` 不被误判成别的名字。
    (round-2 自检现场修正: Attribute 分支曾错用名字表匹配 attr, 导致
    模块别名形态恒漏判 —— 被新增的模块别名自检案例当场抓出。)
    """
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    if isinstance(func, ast.Name):
        return func.id in aliases
    if isinstance(func, ast.Attribute):
        return func.attr == "nothrow"
    return False


def _is_getlogger_call(node: ast.AST) -> bool:
    return _is_call_named(node, {"getLogger", "get_logger"})


def _is_structlog_call(node: ast.AST) -> bool:
    """structlog.get_logger(...) / structlog.stdlib.get_logger(...)。"""
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    return isinstance(func, ast.Attribute) and func.attr == "get_logger"


def _module_stmts(tree: ast.Module) -> List[ast.stmt]:
    """模块级语句, 下探一层 Try/If 的 body (rollback.py 有 try-import 先例),
    但不进 FunctionDef/ClassDef。"""
    out: List[ast.stmt] = []
    stack = list(tree.body)
    while stack:
        node = stack.pop(0)
        out.append(node)
        if isinstance(node, ast.Try):
            stack.extend(node.body + node.orelse + [n for h in node.handlers for n in h.body])
        elif isinstance(node, ast.If):
            stack.extend(node.body + node.orelse)
    return out


class Binding:
    def __init__(self, name, lineno, source, kind, wrapped):
        self.name = name
        self.lineno = lineno
        self.source = source
        self.kind = kind  # stdlib | structlog
        self.wrapped = wrapped


def _bindings(tree: ast.Module, lines: List[str], aliases: Set[str]) -> List[Binding]:
    out = []
    for node in _module_stmts(tree):
        value = None
        targets = []
        if isinstance(node, ast.Assign):
            value, targets = node.value, node.targets
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            value, targets = node.value, [node.target]
        if value is None:
            continue
        nothrow_call = _is_nothrow_call(value, aliases)
        getlogger = _is_getlogger_call(value)
        structlog = _is_structlog_call(value)
        if not (nothrow_call or getlogger or structlog):
            continue
        kind = "structlog" if structlog else "stdlib"
        for target in targets:
            if isinstance(target, ast.Name):
                src = lines[node.lineno - 1].strip() if node.lineno <= len(lines) else ""
                out.append(Binding(target.id, node.lineno, src, kind, nothrow_call))
    return out


def _imported_logger_names(tree: ast.Module) -> List[Tuple[str, int]]:
    """函数体内 import 进来的 logger (包装状态在别的文件 → EXTERNAL)。"""
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if "logger" in alias.name.lower():
                    out.append((alias.asname or alias.name, node.lineno))
    return out


class Call:
    def __init__(self, lineno, method, fstring, func, snippet, receiver):
        self.lineno = lineno
        self.method = method
        self.fstring = fstring
        self.func = func
        self.snippet = snippet
        self.receiver = receiver


def _spans(tree: ast.Module) -> List[Tuple[int, int, str]]:
    return [
        (n.lineno, getattr(n, "end_lineno", n.lineno), n.name)
        for n in ast.walk(tree)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]


def _enclosing(spans, lineno):
    best = None
    for s, e, name in spans:
        if s <= lineno <= e and (best is None or s > best[0]):
            best = (s, e, name)
    return best[2] if best else "<module>"


def _calls(
    tree: ast.Module,
    bound_names: Set[str],
    lines: List[str],
    spans,
    external_names: Optional[Set[str]] = None,
) -> List[Call]:
    external_names = external_names or set()
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute) or func.attr not in LOG_METHODS:
            continue
        base = func.value
        receiver = None
        if isinstance(base, ast.Name) and base.id in bound_names:
            receiver = base.id
        elif isinstance(base, ast.Name) and base.id in external_names:
            receiver = f"<external:{base.id}>"
        elif isinstance(base, ast.Name) and base.id == "logging":
            # Codex round-1 LOW-8: 根模块便捷调用 logging.error("boom") ——
            # 无变量可寻址, 模块级包装罩不住, 单列计数。
            receiver = "<root-logging>"
        elif isinstance(base, ast.Call) and _is_getlogger_call(base):
            receiver = "<inline-getLogger>"
        if receiver is None:
            continue
        first = None
        if node.args:
            idx = 1 if (func.attr == "log" and len(node.args) > 1) else 0
            first = node.args[idx]
        is_f = isinstance(first, ast.JoinedStr)
        snippet = lines[node.lineno - 1].strip() if node.lineno <= len(lines) else ""
        out.append(Call(node.lineno, func.attr, is_f, _enclosing(spans, node.lineno), snippet, receiver))
    return out


def _parse(path: Path):
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None, []
    try:
        return ast.parse(text), text.splitlines()
    except SyntaxError:
        return None, text.splitlines()


# ─────────────────────────────────────────────────────────────────────────────
# 篡改自检 —— 防止"判定恒返回未包装"的坏门冒充工作
# ─────────────────────────────────────────────────────────────────────────────


def _self_check() -> None:
    cases = [
        (
            "from app.core.nothrow_logging import nothrow\nlogger = nothrow(logging.getLogger(__name__))",
            True,
        ),
        ("logger = logging.getLogger(__name__)", False),
        ("from app.core.nothrow_logging import nothrow as _nt\nlogger = _nt(logging.getLogger(__name__))", True),
        ("import structlog\nlogger = structlog.get_logger(__name__)", False),
    ]
    for src, expect_wrapped in cases:
        tree = ast.parse(src)
        nothrow_names, _module_aliases = _alias_table(tree)
        bs = _bindings(tree, src.splitlines(), nothrow_names | _module_aliases)
        got = bool(bs) and bs[0].wrapped
        if got is not expect_wrapped:
            print(
                f"⛔ 自检失败: 判定函数对合成语料的结论与预期相反\n  语料: {src!r}\n  期望 wrapped={expect_wrapped}, 实得 {got}",
                file=sys.stderr,
            )
            raise SystemExit(2)

    # Codex round-1 LOW-8: 假包装 (本地 def nothrow 恒等函数 / 来源不对的
    # import) 不得判已包装 —— 名字叫 nothrow 不等于包装。
    suspect_cases = [
        ("def nothrow(x):\n    return x\nlogger = nothrow(logging.getLogger(__name__))", False),
        ("from some.other.mod import nothrow\nlogger = nothrow(logging.getLogger(__name__))", False),
    ]
    for src, expect_wrapped in suspect_cases:
        tree = ast.parse(src)
        nothrow_names, _module_aliases = _alias_table(tree)
        bs = _bindings(tree, src.splitlines(), nothrow_names | _module_aliases)
        got = bool(bs) and bs[0].wrapped
        if got is not expect_wrapped:
            print(
                f"⛔ 假包装自检失败\n  语料: {src!r}\n  期望 wrapped={expect_wrapped}, 实得 {got}",
                file=sys.stderr,
            )
            raise SystemExit(2)

    # 模块别名形态 (import app.core.nothrow_logging as obs; obs.nothrow(...))
    tree = ast.parse("import app.core.nothrow_logging as obs\nlogger = obs.nothrow(logging.getLogger(__name__))")
    nt_names, mod_aliases = _alias_table(tree)
    bs = _bindings(tree, src.splitlines()[:0] or ["x"], nt_names | mod_aliases)
    if not (bs and bs[0].wrapped):
        print("⛔ 模块别名自检失败: obs.nothrow(...) 没被判已包装", file=sys.stderr)
        raise SystemExit(2)

    # root-module 便捷调用 (logging.error('boom')) 必须被看见
    tree = ast.parse("import logging\nlogging.error('boom')")
    calls = _calls(tree, set(), ["", ""], _spans(tree))
    if not any(c.receiver == "<root-logging>" for c in calls):
        print("⛔ 根模块调用自检失败: logging.error('boom') 没被识别", file=sys.stderr)
        raise SystemExit(2)

    print("[self-check] 篡改自检 4/4 + 假包装 2/2 + 根模块调用 1/1 通过 — 判定函数不是恒 False 的坏门")


def _structural_anchors(backend: Path, reports: Dict[str, dict]) -> None:
    """结构验伪锚: 检不出已知存在的形态 = 判定函数有漏, 拒绝出报告。"""
    bad = []
    rb = reports.get("rollback.py")
    if not rb or rb["inline_calls"] < 1:
        bad.append("rollback.py 的匿名内联 getLogger 调用没被识别 (已知存在 1 处 :41)")
    hp = reports.get("health.py")
    if not hp or hp["external"] < 1:
        bad.append("health.py 的 EXTERNAL logger (memory_logger) 没被识别")
    if bad:
        for b in bad:
            print(f"⛔ 结构锚失败: {b}", file=sys.stderr)
        raise SystemExit(2)
    print("[self-check] 结构验伪锚 2/2 通过 — 内联/EXTERNAL 两类都能看见")


# ─────────────────────────────────────────────────────────────────────────────
# 扫描
# ─────────────────────────────────────────────────────────────────────────────


def scan_endpoints(backend: Path) -> Dict[str, dict]:
    ep_dir = backend / "app" / "api" / "v1" / "endpoints"
    result: Dict[str, dict] = {}
    for path in sorted(ep_dir.glob("*.py")):
        tree, lines = _parse(path)
        if tree is None:
            result[path.name] = {"error": "parse failed"}
            continue
        nothrow_names, module_aliases = _alias_table(tree)
        shadows = _local_nothrow_shadows(tree)
        all_nothrow_names = nothrow_names | module_aliases
        bindings = _bindings(tree, lines, all_nothrow_names)
        if shadows:
            # Codex round-2 MEDIUM-8: 本地重定义了 nothrow 的文件, 其"已包装"
            # 判定不可信 —— 强制降级为未包装 (宁可误报不漏报)。
            for b in bindings:
                b.wrapped = False
        bound_names = {b.name for b in bindings}
        spans = _spans(tree)
        imported = _imported_logger_names(tree)
        external_names = {n for n, _ in imported}
        calls = _calls(tree, bound_names, lines, spans, external_names)
        inline = [c for c in calls if c.receiver == "<inline-getLogger>"]
        root_calls = [c for c in calls if c.receiver == "<root-logging>"]
        ext_calls = [c for c in calls if c.receiver and c.receiver.startswith("<external:")]
        stdlib_bs = [b for b in bindings if b.kind == "stdlib"]
        structlog_bs = [b for b in bindings if b.kind == "structlog"]
        module_calls = [c for c in calls if c.receiver in bound_names]
        result[path.name] = {
            "bindings": bindings,
            "stdlib_bindings": stdlib_bs,
            "structlog_bindings": structlog_bs,
            "calls": module_calls,
            "inline_calls": len(inline),
            "root_calls": root_calls,
            "shadows": shadows,
            "external": len(imported),
            "external_detail": imported,
            "external_calls": ext_calls,
            "fstring_calls": [c for c in module_calls if c.fstring],
        }
    return result


def scan_handoff(backend: Path) -> List[dict]:
    out = []
    by_file: Dict[str, List[Tuple[str, str]]] = {}
    for rel, fn, note in HANDOFF_ANCHORS:
        by_file.setdefault(rel, []).append((fn, note))
    for rel, anchors in by_file.items():
        path = backend / rel
        tree, lines = _parse(path)
        if tree is None:
            out.append({"file": rel, "func": "*", "error": "parse failed / missing"})
            continue
        nothrow_names, _module_aliases = _alias_table(tree)
        bindings = _bindings(tree, lines, nothrow_names | _module_aliases)
        names = {b.name for b in bindings}
        spans = _spans(tree)
        calls = _calls(tree, names, lines, spans)
        module_wrapped = bool(bindings) and all(b.wrapped for b in bindings)
        for fn, note in anchors:
            hits = [c for c in calls if c.func == fn]
            out.append(
                {
                    "file": rel,
                    "func": fn,
                    "note": note,
                    "found": bool(hits),
                    "module_wrapped": module_wrapped,
                    "calls": hits,
                }
            )
    return out


# ─────────────────────────────────────────────────────────────────────────────
# 报告
# ─────────────────────────────────────────────────────────────────────────────


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", default=str(Path(__file__).resolve().parent.parent))
    args = parser.parse_args()
    backend = Path(args.backend).resolve()

    _self_check()
    eps = scan_endpoints(backend)
    _structural_anchors(backend, eps)

    print("=" * 78)
    print("表一 · 端点层 logger 包装状态  (backend/app/api/v1/endpoints/*.py)")
    print("=" * 78)
    wrapped, unwrapped, notwrappable, dead, nolog, external_only, nobinding = [], [], [], [], [], [], []
    total_calls = 0
    total_fstring = 0
    total_inline = 0
    for name, info in eps.items():
        if info.get("error"):
            print(f"  !! {name}: {info['error']}")
            continue
        total_calls += len(info["calls"]) + info["inline_calls"] + len(info["external_calls"])
        total_fstring += len(info["fstring_calls"]) + sum(1 for c in info["external_calls"] if c.fstring)
        total_inline += info["inline_calls"]
        has_calls = bool(info["calls"]) or info["inline_calls"] > 0 or bool(info["root_calls"])
        if info["external"] and not info["bindings"]:
            external_only.append(name)
            continue
        if not info["bindings"]:
            if has_calls:
                nobinding.append(name)  # 无绑定但有调用 (如 rollback.py 的内联 getLogger)
            else:
                nolog.append(name)
            continue
        stdlib = info["stdlib_bindings"]
        slog = info["structlog_bindings"]
        if stdlib and all(b.wrapped for b in stdlib) and not slog:
            wrapped.append(name)
        elif slog and not stdlib:
            notwrappable.append(name)
        elif not has_calls:
            dead.append(name)
        else:
            unwrapped.append(name)

    print(f"\n【已包装】{len(wrapped)} 个 —— 本卡承诺覆盖面")
    for name in wrapped:
        info = eps[name]
        b = info["stdlib_bindings"][0]
        print(f"  ✓ {name:28} :{b.lineno:<5} {b.source}")
        print(f"      日志调用 {len(info['calls']):>3} 处 | f-string 首参 {len(info['fstring_calls'])} 处 (必须为 0)")
        if info["root_calls"]:
            print(f"      ⚠ 另有根模块便捷调用 {len(info['root_calls'])} 处 (logging.<level>, 包装罩不住)")
        if info["shadows"]:
            print(f"      ⚠ SUSPECT: 本文件自定义了 nothrow 名字 {info['shadows']} —— 已包装判定不可信")
        for c in info["fstring_calls"]:
            print(f"        ⚠ :{c.lineno} logger.{c.method}(f...)  in {c.func}()")

    print(f"\n【未包装】{len(unwrapped)} 个 —— 本卡**不覆盖**, 如实登记")
    for name in unwrapped:
        info = eps[name]
        b = info["bindings"][0]
        note = " (绑定后 0 调用但有内联调用)" if not info["calls"] and info["inline_calls"] else ""
        ext_note = ""
        if info["external_calls"]:
            rcv = info["external_calls"][0].receiver
            ext_note = (
                f" + EXTERNAL {rcv[1:-1].split(':')[1]} {len(info['external_calls'])} 处 (包装状态在别文件, 本表不判)"
            )
        print(
            f"  ✗ {name:28} :{b.lineno:<5} {b.kind:9} 日志调用 {len(info['calls']):>3} 处 (f-string {len(info['fstring_calls'])} 处, 内联 {info['inline_calls']}){note}{ext_note}"
        )

    print(f"\n【NOT-WRAPPABLE·structlog】{len(notwrappable)} 个 —— 本适配器技术不可包 (stacklevel 会泄进 JSON)")
    for name in notwrappable:
        info = eps[name]
        b = info["structlog_bindings"][0]
        print(
            f"  S {name:28} :{b.lineno:<5} 日志调用 {len(info['calls']):>3} 处 (f-string {len(info['fstring_calls'])} 处)"
        )

    print(f"\n【EXTERNAL·他文件 logger】{len(external_only)} 个")
    for name in external_only:
        info = eps[name]
        for lname, ln in info["external_detail"]:
            print(f"  E {name:28} :{ln:<5} imports {lname} → 包装状态看 app/core/memory_system_logger.py")

    print(f"\n【死绑定·绑了不用】{len(dead)} 个 —— 技术正确但零风险面, 不进待改队列")
    for name in dead:
        b = eps[name]["bindings"][0]
        print(f"  · {name:28} :{b.lineno:<5} {b.kind}")

    print(f"\n【无绑定但有调用】{len(nobinding)} 个 —— 模块级包装罩不住 (内联 getLogger)")
    for name in nobinding:
        info = eps[name]
        print(f"  ? {name:28} 内联 {info['inline_calls']} 处 / 经绑定调用 {len(info['calls'])} 处")

    print(f"\n【无模块级 logger】{len(nolog)} 个: {', '.join(nolog) if nolog else '(无)'}")

    print()
    print("=" * 78)
    print("表二 · 匿名内联日志调用 (无变量可寻址, 模块级包装永远罩不住)")
    print("=" * 78)
    for name, info in eps.items():
        if info.get("error") or not info["inline_calls"]:
            continue
        print(f"  ✗ {name}: {info['inline_calls']} 处")
    if total_inline == 0:
        print("  (0 处)")

    print()
    print("=" * 78)
    print("表四 · 服务层观测旁路移交登记  (CARD-G4-3 验收单 :1046 点名; 本卡只登记不改)")
    print("=" * 78)
    handoff = scan_handoff(backend)
    handoff_calls = 0
    for row in handoff:
        if row.get("error"):
            print(f"  !! {row['file']}::{row['func']} — {row['error']}")
            continue
        mark = "已包装" if row["module_wrapped"] else "未包装"
        print(f"\n  {row['file']}::{row['func']}()   [{mark}]  ({row['note']})")
        if not row["found"]:
            print("      (该函数内未找到模块 logger 的调用 —— 函数可能已改名/重构, 需人工重锚)")
            continue
        for c in row["calls"]:
            handoff_calls += 1
            flag = " ⚠f-string" if c.fstring else ""
            print(f"      :{c.lineno:<6} {c.receiver}.{c.method}{flag}")
            print(f"              {c.snippet[:88]}")

    print()
    print("-" * 78)
    print(
        f"登记合计: 已包装 {len(wrapped)} / 未包装 {len(unwrapped)} / structlog {len(notwrappable)}"
        f" / EXTERNAL {len(external_only)} / 死绑定 {len(dead)} / 无绑定有调用 {len(nobinding)}"
        f" / 无 logger {len(nolog)}"
    )
    print(f"          端点层调用点 {total_calls} 处 (其中 f-string {total_fstring} 处, 匿名内联 {total_inline} 处)")
    print(f"          服务层移交站点 {handoff_calls} 处日志调用 (跨 {len(HANDOFF_ANCHORS)} 个锚定函数)")
    print("-" * 78)
    print("本表不证明什么: 只看模块级绑定 + 经它发出的调用 + 匿名内联。函数内局部")
    print("绑定的 logger、经 .inner 绕过包装的调用、handler/装饰器级保护, 本表看不见。")
    print("f-string 列与包装正交: f-string 在实参求值阶段抛错, 包装拦不住, 唯一修法")
    print("是转 %-惰性参数。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
