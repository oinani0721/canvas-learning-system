#!/usr/bin/env python
"""负门 —— 证明「lifespan 隔离 + socket 门 + 结账哨兵」这套防线真的在承重。

[BATCH-2026-09-01-第八批 / CARD-TEST-isolate-lifespan]

.. warning::
   **⛔ 移交材料（CARD-TEST-isolate-lifespan 降级收口，2026-09-01）**
   Codex round-3 BLOCKER：本脚本变异子进程继承调用者环境——若 ``NEO4J_URI``
   被设为**非受拦端口**（7691/7687 之外）的库，摘掉 no_lifespan 后会**真实连接**
   该库（门只拦 7691/7687）。当前 ``backend/.env`` 的 7691 受拦所以实害未发生，
   但**在接手卡钉死「受拦 loopback URI + 假凭据 + 禁豁免」之前，禁止运行本脚本**。
   本卡降级条款下本脚本不属于已主张完成面（见验收单「降级收口声明」）。

方法：把 ``tests/api/v1/endpoints/test_metadata_subject_mapping.py`` 里的
``no_lifespan`` **原地摘掉**，跑该文件。此时该文件的 client fixture 会重新触发
``app.main`` 的真实 lifespan，向 ``backend/.env`` 指向的现网 Neo4j（7691）发起
连接。防线的行为应当是：

1. socket 门在 connect 前拦下（进程**永不真连** 7691）。门经
   ``-p tests.support.guard_plugin`` **显式点名加载**——显式 ``-p`` 不受
   ``--rootdir``/``--confcutdir``/``PYTEST_ADDOPTS`` 影响（Codex round-1
   BLOCKER：只靠「根 conftest 会被发现」来保门是可被绕过的）；
2. 连接处抛出的 ``RuntimeError`` 会被 ``app/main.py`` 的 try/except 吞掉 ——
   所以根 conftest 的结账哨兵把每次被吞掉的拦截转成该用例 ``FAILED``；
3. 正证据闭环：子进程 stdout 的 ``blocked=`` 计数必须 ≥ 1 —— 这证明门确实
   在子进程里活过并拦下了东西，而不是「没装门、恰好没人连」的巧合绿。

期望：**选中的代表性 nodeid**（见 ``SELECTED_NODEID_FILTER``）全部 FAIL（红集
与预采集选中集严格相等），失败原因含 ``live Neo4j port connect attempted``，
pytest 退出码恰为 1（tests failed 而非收集/用法错误）；三个运行时文件 sha
前后不变；源文件逐字节还原。

任何一条不成立 → 本脚本 exit 1（= 防线有假门）。

## 原地变异的还原纪律（MEMORY reference_temp_file_swap_needs_exit_trap）

变异标志在写盘**之前**置位；``finally`` 无条件写回原始字节；``atexit`` 与
SIGTERM/SIGINT 处理器兜底。已知残余窗口：``SIGKILL`` / 断电无法兜底——
此时工作树会留下被变异的文件，但目标文件是 git tracked 的，``git status``
一眼可见（卡文裁决：原地变异 + 逐字节还原，不移临时副本）。

## 这道负门不比什么

* 只对**一个**代表文件做原地变异，且只跑其中 **3 条代表性 nodeid**（覆盖
  GET 成功 / POST 写 / 404 三种请求形态）——变异态每用例要完整跑一遍真实
  lifespan，全 19 条 ≈ 35 分钟（机器负载相关），子集把验证压回分钟级。它
  证明的是「防线 + lifespan 摘除」的组合在该形态上红得符合预期；不证明其余
  用例与其它 12 个改造文件的个体变异也会红（fixture 形态相同，未逐一变异）。
* 只跑 pytest 主进程。防线不拦子进程（见 live_port_guard 模块 docstring），
  本脚本也不构造子进程连接场景。
* 红因判定是 ``-rA`` 输出行上的子串匹配；若未来哨兵文案改了（
  ``BLOCK_REASON``），同步改 ``EXPECTED_REASON``。
* AST 门是**词法近似**：作用域链按「语句归属最近 enclosing 函数」构建、支持
  import 别名与函数级 import；解析不了的名字**按违规处理**（fail-closed，宁可
  人工复核不可漏报）。它不能证明「运行时真的没连」，运行时证明由变异运行承担。
"""

from __future__ import annotations

import ast
import atexit
import hashlib
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
TARGET_REL = "tests/api/v1/endpoints/test_metadata_subject_mapping.py"
TARGET = BACKEND_DIR / TARGET_REL

#: 原文件里的隔离形态（必须恰好出现一次，否则说明文件已被动过，先停下来）。
ANCHOR = "with no_lifespan(app), TestClient(app) as c:"
MUTATED = "with TestClient(app) as c:"

#: 与 tests/support/live_port_guard.py 的 BLOCK_REASON 保持一致。
EXPECTED_REASON = "live Neo4j port connect attempted"

#: 与 backend/scripts/lifespan_isolation_runtime_sha.sh 的监视清单保持一致。
RUNTIME_FILES = [
    BACKEND_DIR / "data/bug_log.jsonl",
    BACKEND_DIR / "app/data/vault_index_pending.jsonl",
    BACKEND_DIR / "data/outbox/events.jsonl",
]

#: 变异态每个用例都要完整跑一遍真实 lifespan（被拦的连接各自带驱动级重试/
#: 超时），实测单用例 ~30-110s（机器负载相关，多 session 并行时更慢）——
#: 19 个用例全跑 ≈ 35 分钟，把「验证负门」变成半小时级负担。卡文判据写的是
#: 「**指定 nodeid** 全部 FAIL」而非「全部用例」：取 3 条代表性 nodeid
#: （GET 成功路径 / POST 写路径 / 404 路径），红集判据相应改为与选中集严格
#: 相等。全 19 条逐个红这件事由「防线形态同构」+ 本子集实证共同背书，
#: 如实登记于验收单（「这道负门不比什么」）。
SELECTED_NODEID_FILTER = "test_get_returns_200 or test_add_returns_200 or test_remove_nonexistent_returns_404"

#: 钉死的身份（Codex round-2 MEDIUM：动态预采集集自洽不可靠——用例被删/改名
#: 后剩余条目仍能 PASS）。三个 nodeid 必须逐字存在于预采集集，且红集与
#: 这三个的**全等**是 PASS 的必要条件。
FIXED_TARGET_NAMES = (
    "test_get_returns_200",
    "test_add_returns_200",
    "test_remove_nonexistent_returns_404",
)
PYTEST_TIMEOUT_S = 1500

# ═══════════════════════════════════════════════════════════════════════════
# 裁判 6 的 AST 门 —— 静态扫描「裸 with TestClient(app.main 的 app)」
# ═══════════════════════════════════════════════════════════════════════════

#: 扫描范围（与卡文裁判 6 一致，并按 Codex round-1 MEDIUM 扩到子目录全部 .py，
#: 覆盖 tests/unit/conftest.py、tests/unit/grouping/conftest.py 等共享 fixture 面）。
#: tests/integration、tests/e2e、regression 及其它根级文件**不在射程**：
#: 前者按路径豁免（advisory），后者吃根 conftest 的 lifespan-free client fixture。
AST_SCOPE_DIRS = ["tests/api", "tests/unit"]
AST_SCOPE_FILES = [
    "tests/test_debug.py",
    "tests/test_deep_monitoring.py",
    "tests/conftest.py",
]

#: 同一 with 语句里允许充当隔离基元的名字。
ISOLATION_HELPER_NAMES = {"no_lifespan", "lifespan_lite"}

_ORIGIN_MAIN = "app.main"
_ORIGIN_FASTAPI = "FastAPI()"
_ORIGIN_UNKNOWN = "unknown"


def _call_name(node: ast.expr) -> str | None:
    """Call(...) 的函数名（仅 Name 形式），否则 None。"""
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        return node.func.id
    return None


class _ModuleIndex:
    """一次 ast.parse 的静态索引：import 别名 + 按作用域的名字来源表。

    来源（Codex round-1 HIGH 整改：支持函数级 import 与别名，解析不了 = 违规）：
      * ``from app.main import app``（任意层级）→ 绑定名 → _ORIGIN_MAIN；
      * ``import app.main`` / ``import app.main as m`` → 绑定名 → _ORIGIN_MAIN
        （供 ``m.app`` 这类 Attribute 解析）；
      * ``x = FastAPI(...)`` → x → _ORIGIN_FASTAPI（局部应用正例）；
      * 其它 Name 绑定 → _ORIGIN_UNKNOWN；
      * 解析失败 → _ORIGIN_UNKNOWN（= 违规，fail-closed）。

    作用域：每条名字记到「离它最近的 enclosing 函数」的作用域表；With 处解析时
    沿 parent 链从内向外查，最后查模块级。类体视作透明（近似，往保守方向偏）。
    """

    def __init__(self, tree: ast.Module) -> None:
        self.parent: dict[int, ast.AST] = {}
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                self.parent[id(child)] = node

        self.client_aliases: set[str] = {"TestClient"}
        #: 合法隔离基元名 = 真正从 tests.support.lifespan import 进来的名字
        #: （Codex round-2 HIGH：本地定义一个同名 no-op 不能冒充隔离基元）。
        self.helper_aliases: set[str] = set()
        #: 「返回局部 FastAPI() 的函数」名集（名字级过程间近似）：正例文件
        #: （test_rag_four_state_api 等）的模式是 helper 内 ``app = FastAPI()``
        #: 然后 return，测试里元组解包后传入 TestClient —— 不识别会把正例
        #: 误判成 unknown 违规。近似是**单向放宽**且要求函数体内确有
        #: ``x = FastAPI()`` + ``return x`` 同现，冒用面极窄。
        self.fastapi_returning_funcs: set[str] = set()
        self.module_scope: dict[str, str] = {}
        self.scope_by_func: dict[int, dict[str, str]] = {}
        self._index_statements(tree.body, self.module_scope)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                scope: dict[str, str] = {}
                self._index_statements(node.body, scope)
                self.scope_by_func[id(node)] = scope
                self._mark_fastapi_returning(node)

    def _mark_fastapi_returning(self, fd) -> None:
        """函数体内「x = FastAPI() … return x（或直接 return FastAPI()）」→ 记名。"""
        local_fastapi_names: set[str] = set()
        for stmt in ast.walk(fd):
            if isinstance(stmt, (ast.Assign, ast.AnnAssign)) and stmt.value is not None:
                if _call_name(stmt.value) == "FastAPI":
                    targets = stmt.targets if isinstance(stmt, ast.Assign) else [stmt.target]
                    for t in targets:
                        if isinstance(t, ast.Name):
                            local_fastapi_names.add(t.id)
        for stmt in ast.walk(fd):
            if isinstance(stmt, ast.Return) and stmt.value is not None:
                candidates = stmt.value.elts if isinstance(stmt.value, ast.Tuple) else [stmt.value]
                for c in candidates:
                    if _call_name(c) == "FastAPI" or (isinstance(c, ast.Name) and c.id in local_fastapi_names):
                        self.fastapi_returning_funcs.add(fd.name)
                        return

    def _index_statements(self, stmts, scope: dict[str, str]) -> None:
        """把一批语句的名字绑定记入 scope；不跨函数边界（内层函数另行建表）。"""
        for stmt in stmts:
            self._index_one(stmt, scope)
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for field in ("body", "orelse", "finalbody"):
                block = getattr(stmt, field, None)
                if block:
                    self._index_statements(block, scope)
            if isinstance(stmt, (ast.With, ast.AsyncWith)):
                for item in stmt.items:
                    var = item.optional_vars
                    if isinstance(var, ast.Name):
                        scope.setdefault(var.id, _ORIGIN_UNKNOWN)
            if isinstance(stmt, ast.ClassDef):
                self._index_statements(stmt.body, scope)

    def _index_one(self, stmt, scope: dict[str, str]) -> None:
        if isinstance(stmt, ast.ImportFrom):
            if stmt.module == "app.main":
                for alias in stmt.names:
                    if alias.name == "app":
                        scope[alias.asname or "app"] = _ORIGIN_MAIN
            if stmt.module == "fastapi.testclient":
                for alias in stmt.names:
                    if alias.name == "TestClient":
                        self.client_aliases.add(alias.asname or "TestClient")
            if stmt.module == "tests.support.lifespan":
                for alias in stmt.names:
                    if alias.name in ISOLATION_HELPER_NAMES:
                        self.helper_aliases.add(alias.asname or alias.name)
        elif isinstance(stmt, ast.Import):
            for alias in stmt.names:
                if alias.name == "app.main" or alias.name.startswith("app.main."):
                    bound = alias.asname or alias.name.split(".")[0]
                    scope[bound] = _ORIGIN_MAIN
        elif isinstance(stmt, (ast.Assign, ast.AnnAssign)):
            value = stmt.value
            targets = stmt.targets if isinstance(stmt, ast.Assign) else [stmt.target]
            if value is None:
                return
            call = value.func if isinstance(value, ast.Call) else None
            helper_name = None
            if isinstance(call, ast.Name):
                helper_name = call.id
            elif isinstance(call, ast.Attribute):
                helper_name = call.attr
            if _call_name(value) == "FastAPI" or (helper_name in self.fastapi_returning_funcs):
                for t in targets:
                    for elt in [t] if isinstance(t, ast.Name) else getattr(t, "elts", []):
                        if isinstance(elt, ast.Name):
                            scope[elt.id] = _ORIGIN_FASTAPI
            else:
                for t in targets:
                    for elt in [t] if isinstance(t, ast.Name) else getattr(t, "elts", []):
                        if isinstance(elt, ast.Name):
                            scope.setdefault(elt.id, _ORIGIN_UNKNOWN)

    def resolve_name(self, name: str, node: ast.AST) -> str:
        cur: ast.AST | None = node
        while cur is not None:
            parent = self.parent.get(id(cur))
            if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
                scope = self.scope_by_func.get(id(parent))
                if scope and name in scope:
                    return scope[name]
            cur = parent
        if name in self.module_scope:
            return self.module_scope[name]
        return _ORIGIN_UNKNOWN

    def resolve_arg(self, arg: ast.expr, node: ast.AST) -> str:
        if isinstance(arg, ast.Name):
            return self.resolve_name(arg.id, node)
        if isinstance(arg, ast.Attribute):
            base = arg.value
            if isinstance(base, ast.Name) and self.resolve_name(base.id, node) == _ORIGIN_MAIN:
                return _ORIGIN_MAIN
            return _ORIGIN_UNKNOWN
        if isinstance(arg, ast.Call):
            fname = None
            if isinstance(arg.func, ast.Name):
                fname = arg.func.id
            elif isinstance(arg.func, ast.Attribute):
                fname = arg.func.attr
            if fname == "FastAPI":
                return _ORIGIN_FASTAPI
            if fname in self.fastapi_returning_funcs:
                return _ORIGIN_FASTAPI
        return _ORIGIN_UNKNOWN


def run_ast_gate() -> tuple[int, list[str], int]:
    """返回 (违规数, 违规明细, 扫描的文件数)。"""
    files: list[Path] = []
    for d in AST_SCOPE_DIRS:
        files.extend(sorted((BACKEND_DIR / d).rglob("*.py")))
    for f in AST_SCOPE_FILES:
        p = BACKEND_DIR / f
        if p.exists():
            files.append(p)

    violations: list[str] = []
    for path in files:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError as e:
            violations.append(f"{path}: SyntaxError {e}")
            continue
        index = _ModuleIndex(tree)
        rel = path.relative_to(BACKEND_DIR)
        for node in ast.walk(tree):
            if not isinstance(node, (ast.With, ast.AsyncWith)):
                continue
            for pos, item in enumerate(node.items):
                cname = _call_name(item.context_expr)
                if cname not in index.client_aliases:
                    continue
                args = item.context_expr.args
                if not args:
                    violations.append(f"{rel}:{node.lineno}: TestClient() 无参 —— 人工复核")
                    continue
                arg = args[0]
                origin = index.resolve_arg(arg, node)
                if origin == _ORIGIN_FASTAPI:
                    continue  # 局部 FastAPI() 正例
                if origin != _ORIGIN_MAIN:
                    # unknown：来源无法静态证明 —— 按违规处理（fail-closed）。
                    # Codex round-2 HIGH：此前 unknown 被直接放行，与 docstring
                    # 声明相反（target = app / 晚绑定 / class 作用域污染全漏）。
                    arg_desc = arg.id if isinstance(arg, ast.Name) else "<expr>"
                    violations.append(
                        f"{rel}:{node.lineno}: with TestClient({arg_desc}) —— app 来源"
                        "无法静态证明（unknown 按违规处理，人工复核）"
                    )
                    continue
                # app 来自 app.main：必须有**排在前面的**隔离兄弟项、且操作同一个
                # app、且该名字确实 import 自 tests.support.lifespan（Codex
                # round-2 HIGH：本地同名 no-op 不能冒充隔离基元；
                # round-1 HIGH：顺序反了等于没隔离）。
                ok = False
                for hpos, hitem in enumerate(node.items):
                    if hpos >= pos:
                        break
                    if _call_name(hitem.context_expr) not in index.helper_aliases:
                        continue
                    hargs = hitem.context_expr.args
                    if hargs and isinstance(arg, ast.Name) and isinstance(hargs[0], ast.Name) and hargs[0].id == arg.id:
                        ok = True
                        break
                if not ok:
                    arg_desc = arg.id if isinstance(arg, ast.Name) else "<expr>"
                    violations.append(
                        f"{rel}:{node.lineno}: with TestClient({arg_desc}) —— app 来自"
                        " app.main 且缺少**在前**的 no_lifespan/lifespan_lite 兄弟项"
                        "（顺序不符、参数不同名或 helper 并非 import 自"
                        " tests.support.lifespan 同样算违规）"
                    )
    return len(violations), violations, len(files)


# ═══════════════════════════════════════════════════════════════════════════
# 变异 + 子进程 + 还原
# ═══════════════════════════════════════════════════════════════════════════


def sha_of(path: Path) -> str:
    if not path.exists():
        return "absent"
    return hashlib.sha256(path.read_bytes()).hexdigest()


def runtime_snapshot() -> str:
    return "\n".join(f"{sha_of(p)}  {p}" for p in RUNTIME_FILES)


def _parse_outcomes(stdout: str) -> dict[str, str]:
    """从 ``-rA`` 汇总块解析 nodeid → PASSED/FAILED/ERROR/...。"""
    outcomes: dict[str, str] = {}
    for line in stdout.splitlines():
        m = re.match(r"^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) (\S+)", line.strip())
        if m:
            outcomes[m.group(2)] = m.group(1)
    return outcomes


def main() -> int:
    print("=== lifespan isolation NEGATIVE CONTROL ===")

    # -- 0-保险. 门在位前置检查（belt）+ AST 门（裁判 6）-----------------------
    conftest_text = (BACKEND_DIR / "tests/conftest.py").read_text(encoding="utf-8")
    if "live_port_guard" not in conftest_text:
        print(
            "NEGATIVE-CONTROL: FAIL — 根 tests/conftest.py 未引用 live_port_guard："
            "结账哨兵不会在子进程里工作，负门失去被测对象。"
        )
        return 1
    n_violations, violation_lines, n_files = run_ast_gate()
    print(f"[0] AST gate: {n_violations} violations across {n_files} files")
    for v in violation_lines:
        print(f"    VIOLATION: {v}")
    if "--ast-only" in sys.argv:
        if n_violations:
            print("AST-GATE: FAIL")
            return 1
        print(f"AST-GATE: PASS (0 violations in {n_files} files)")
        return 0

    tmp_root = Path(tempfile.mkdtemp(prefix="lifespan-negctl-"))
    junit_xml = tmp_root / "negctl-junit.xml"
    vault_tmp = tmp_root / "vault"
    lance_tmp = tmp_root / "lancedb"
    vault_tmp.mkdir()
    lance_tmp.mkdir()

    original = TARGET.read_bytes()
    original_sha = hashlib.sha256(original).hexdigest()
    mutated = False

    def _restore(*_a) -> None:
        """无条件写回原始字节（幂等）。变异标志先置位，保证任何路径都会还原。"""
        nonlocal mutated
        if not mutated:
            return
        TARGET.write_bytes(original)
        mutated = False

    atexit.register(_restore)
    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP, signal.SIGQUIT):
        signal.signal(sig, lambda *_: (_restore(), sys.exit(130)))

    before_runtime = runtime_snapshot()
    pytest_rc: int | None = None
    outcomes: dict[str, str] = {}
    try:
        # -- 1. 预采集 nodeid 全集（变异前）----------------------------------
        env = os.environ.copy()
        env.pop("PYTEST_ADDOPTS", None)  # 防 addopts 注入 --rootdir/--confcutdir 绕门
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        # -p 插件加载早于 pytest 把 rootdir 塞进 sys.path —— 必须显式给
        # PYTHONPATH，否则 tests.support.guard_plugin 在插件装载期不可导入。
        env["PYTHONPATH"] = str(BACKEND_DIR) + os.pathsep + env.get("PYTHONPATH", "")
        base_cmd = [
            str(BACKEND_DIR / ".venv/bin/pytest"),
            TARGET_REL,
            "-p",
            "tests.support.guard_plugin",  # 显式点名装门（BLOCKER 整改：不受 rootdir/confcutdir 影响）
            "-p",
            "no:cacheprovider",
            "--override-ini=addopts=",
        ]
        collect = subprocess.run(
            base_cmd + ["--collect-only", "-q", "-k", SELECTED_NODEID_FILTER],
            cwd=BACKEND_DIR,
            env=env,
            capture_output=True,
            text=True,
            timeout=PYTEST_TIMEOUT_S,
        )
        expected_nodeids = {ln.strip() for ln in collect.stdout.splitlines() if "::" in ln}
        if not expected_nodeids:
            print("NEGATIVE-CONTROL: FAIL — 预采集拿到 0 个 nodeid")
            print("--- collect stdout tail ---")
            print(collect.stdout[-1500:])
            return 1
        # 钉死身份：三个指定 nodeid 必须逐字存在（防删/改名后剩余条目自洽 PASS）
        missing_fixed = [name for name in FIXED_TARGET_NAMES if not any(name in nid for nid in expected_nodeids)]
        if missing_fixed or len(expected_nodeids) != len(FIXED_TARGET_NAMES):
            print(
                "NEGATIVE-CONTROL: FAIL — 预采集集与钉死身份不符："
                f"missing_fixed={missing_fixed} collected={len(expected_nodeids)} "
                f"expected={len(FIXED_TARGET_NAMES)}"
            )
            print("--- collect stdout ---")
            print(collect.stdout[-1500:])
            return 1
        print(f"[1] 预采集 nodeid 全集: {len(expected_nodeids)} 条（与钉死身份全等）")

        # -- 2. 原地摘掉 no_lifespan ----------------------------------------
        original_text = original.decode("utf-8")
        count = original_text.count(ANCHOR)
        if count != 1:
            print(
                f"NEGATIVE-CONTROL: FAIL — 隔离锚点出现 {count} 次（期望恰好 1 次），"
                f"文件形态与本脚本假设不符，拒绝盲改: {TARGET_REL}"
            )
            return 1
        mutated = True  # 先置位再写盘：任何崩溃路径都会走 _restore
        TARGET.write_bytes(original_text.replace(ANCHOR, MUTATED).encode("utf-8"))
        print(f"[2] 已摘掉 no_lifespan: {TARGET_REL}")

        # -- 3. 跑该文件（-p 显式装门 + 根 conftest 哨兵）--------------------
        env = os.environ.copy()
        env.pop("PYTEST_ADDOPTS", None)
        env["CANVAS_BASE_PATH"] = str(vault_tmp)
        env["LANCEDB_DATA_PATH"] = str(lance_tmp)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["PYTHONPATH"] = str(BACKEND_DIR) + os.pathsep + env.get("PYTHONPATH", "")
        cmd = base_cmd + ["-q", "--tb=no", "-rA", "-k", SELECTED_NODEID_FILTER, f"--junitxml={junit_xml}"]
        print("[3] pytest 子进程（串行）:", " ".join(cmd))
        try:
            proc = subprocess.run(
                cmd,
                cwd=BACKEND_DIR,
                env=env,
                capture_output=True,
                text=True,
                timeout=PYTEST_TIMEOUT_S,
            )
        except subprocess.TimeoutExpired as e:
            print("NEGATIVE-CONTROL: FAIL — 变异运行超时；faulthandler dump（stderr）如下")
            err_tail = (e.stderr or "")[-5000:]
            print(err_tail)
            print("--- stdout tail ---")
            print((e.stdout or "")[-1000:])
            return 1
        pytest_rc = proc.returncode
        print(f"    pytest exit={pytest_rc}")

        # -- 3b. 正证据：门必须在子进程里真的拦下过东西 ----------------------
        m = re.search(r"NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=(\d+) \(blocked=(\d+)", proc.stdout)
        if not m:
            print("NEGATIVE-CONTROL: FAIL — 子进程输出里没有门的汇总行（guard_plugin 未加载？）")
            print("--- child stdout tail ---")
            print(proc.stdout[-1500:])
            return 1
        total_attempts, blocked_attempts = int(m.group(1)), int(m.group(2))
        print(f"[3b] 子进程门汇总: attempts={total_attempts} blocked={blocked_attempts}")
        if blocked_attempts < 1:
            print(
                "NEGATIVE-CONTROL: FAIL — 变异态下 blocked=0：门未在子进程生效"
                "（或 lifespan 未触发连接），防线证明不成立"
            )
            return 1

        # -- 4. 解析 junitxml：红因判定必须吃完整 failure 正文 ---------------
        # Codex round-2 HIGH：-rA 行对这些长 nodeid **没有 reason 段**
        # （实测 `FAILED <nodeid>` 到此为止），上一版按行匹配 reason 的解析
        # 把「无 reason」当「红得正确」= fail-open。junitxml 的 <failure>
        # 元素带完整 longrepr 文本，且 classname→nodeid 的映射对本目标文件
        # 是确定性的（模块前缀已知）。
        if not junit_xml.exists():
            print("NEGATIVE-CONTROL: FAIL — junitxml 未生成")
            return 1
        module_dotted = TARGET_REL[:-3].replace("/", ".")
        total = 0
        green: list[str] = []
        red_nodeids: set[str] = set()
        red_for_wrong_reason: list[str] = []
        reason_verified: set[str] = set()
        for case in ET.parse(junit_xml).getroot().iter("testcase"):
            classname = case.get("classname", "")
            name = case.get("name", "")
            if classname.startswith(module_dotted):
                class_chain = classname[len(module_dotted) :].lstrip(".")
                nid = f"{TARGET_REL}::" + (f"{class_chain.replace('.', '::')}::{name}" if class_chain else name)
            else:
                nid = f"{classname.replace('.', '/')}::{name}"
            total += 1
            failure = case.find("failure")
            if failure is None:
                green.append(nid)
                continue
            red_nodeids.add(nid)
            text = " ".join(filter(None, [(failure.get("message") or ""), (failure.text or "")]))
            if EXPECTED_REASON in text:
                reason_verified.add(nid)
            else:
                red_for_wrong_reason.append(f"{nid} :: {text[:160] or '<failure 无正文 — 红因不明>'}")
        red_for_right_reason = len(reason_verified)

        print(
            f"[4] junitxml: total={total} red={len(red_nodeids)} "
            f"green={len(green)} red-wrong-reason={len(red_for_wrong_reason)}"
        )
        for g in green:
            print(f"    GREEN (不应绿): {g}")
        for w in red_for_wrong_reason:
            print(f"    RED-WRONG-REASON: {w}")

        if pytest_rc != 1:
            print(f"    (判据锁定) pytest 退出码 {pytest_rc} ≠ 1 — 见最终裁定")
    finally:
        # -- 5. 逐字节还原（无论上面死在哪一步；atexit/信号再兜底）-----------
        _restore()
        restored_identical = sha_of(TARGET) == original_sha
        after_runtime = runtime_snapshot()
        runtime_unchanged = before_runtime == after_runtime

    print(f"[5] 还原完成; byte-identical={restored_identical}; runtime sha unchanged={runtime_unchanged}")
    if not restored_identical:
        print("NEGATIVE-CONTROL: FAIL — 源文件未能逐字节还原（这是事故，请人工检查 git diff）")
        return 1
    shutil.rmtree(tmp_root, ignore_errors=True)

    # -- 6. 裁定 --------------------------------------------------------------
    problems: list[str] = []
    if pytest_rc is None:
        problems.append("pytest 未运行")
    if pytest_rc != 1:
        problems.append(f"pytest 退出码 {pytest_rc} ≠ 1（期望恰为 tests-failed）")
    if total != len(expected_nodeids):
        problems.append(f"用例总数 {total} ≠ 预采集 {len(expected_nodeids)} — 解析或收集缩水")
    if green:
        problems.append(f"{len(green)} 个用例在 no_lifespan 摘除后仍然绿（哨兵没接住）")
    if red_nodeids != expected_nodeids:
        missing = expected_nodeids - red_nodeids
        extra = red_nodeids - expected_nodeids
        problems.append(f"红集与预采集全集不严格相等（缺红 {len(missing)} / 多红 {len(extra)}）")
    if red_for_wrong_reason:
        problems.append(f"{len(red_for_wrong_reason)} 个用例红了但原因不对（不是 live port connect）")
    if reason_verified != red_nodeids:
        problems.append(
            f"红因可验证集 {len(reason_verified)} ≠ 红集 {len(red_nodeids)}"
            " —— 存在红因不明的 FAILED 行（截断或缺 reason），fail-closed"
        )
    if not runtime_unchanged:
        problems.append("运行时文件 sha 变化 — 门没能在 connect 前拦住（或写路径被触发）")
    if n_violations:
        problems.append(f"AST 门 {n_violations} 处违规（见上方 VIOLATION 清单）")

    if problems:
        print("NEGATIVE-CONTROL: FAIL")
        for p in problems:
            print(f"  - {p}")
        return 1

    print(
        f"NEGATIVE-CONTROL: PASS ({red_for_right_reason} nodeids red for expected "
        f"reason; runtime files unchanged; restored byte-identical; AST-GATE: "
        f"PASS 0/{n_files} files)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
