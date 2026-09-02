#!/usr/bin/env python
"""负门 —— 证明「lifespan 隔离 + socket 门 + 结账哨兵」这套防线真的在承重。

[BATCH-2026-09-01-第九批 / CARD-TEST-isolate-lifespan-R1]

方法：把 ``tests/api/v1/endpoints/test_metadata_subject_mapping.py`` 里的
``no_lifespan`` **原地摘掉**，跑其中三条钉死的 nodeid。此时 client fixture 会重新
触发 ``app.main`` 的真实 lifespan，向 ``NEO4J_URI`` 指向的库发起连接。防线的行为
应当是：

1. socket 门（audit hook 承重）在 connect 前拦下 —— 进程**永不真连**；
2. 连接处抛出的异常会被 ``app/main.py`` 的 try/except 吞掉 —— 所以根 conftest 的
   结账哨兵把每次被吞掉的拦截转成该用例 ``FAILED``；
3. 正证据闭环：子进程的门账必须 ``total == blocked > 0`` 且
   ``advisory == unaccounted == 0``。

## 运行时文件的判据方向（第九批更正）

第八批把「三个运行时文件前后 sha 不变」当成**变异运行**的 PASS 判据。方向反了：
socket 门只管连接，**挡不住文件写**；挡住文件写的是 ``no_lifespan``。所以摘掉隔离
之后运行时文件被写，恰恰是「隔离在承重」的正证据。本版改成：

* **硬判据**：*正控*（隔离态）运行时文件必须 unchanged —— 这才是本卡要证的那句话；
* **硬判据**：*变异态*必须**确实写了**至少一个运行时文件 —— 否则说明 lifespan 在
  到达写路径之前就 abort 了，这条负门此刻在测别的东西（2026-09-03 实测过一次：
  LanceDB canonical/legacy 环境变量冲突让 lifespan 在 Neo4j 之前就退出，
  ``blocked=0`` 看起来却像「哨兵没接住」）；
* **现场复原**：变异态新造出来的运行时文件（跑前 absent）由脚本删除。跑前就存在
  且内容变了的**不覆盖**（可能混有并发写入），直接判失败交人工。
  ``app/data/vault_index_pending.jsonl`` 的路径在
  ``app/services/vault_index_orchestrator.py:101`` 是**硬编码**的，重定向不了。

## 第八批 BLOCKER 的收口：子进程环境必须钉死，而不是继承

第八批本脚本把调用者环境整份继承给子进程。门**只按端口判定**（7691/7687），
所以只要 ``NEO4J_URI`` 指向别的库，「摘掉隔离」就会**真的连上去**——脚本只会
事后因 ``blocked=0`` 报失败，而实害已经发生，runtime SHA 也看不到数据库侧改动。

本版的收口是三重的，且每一重都在**任何测试跑起来之前**生效：

* :func:`_child_env` 清掉全部 ``NEO4J*`` 变量，重新钉死
  ``NEO4J_URI=bolt://127.0.0.1:7691``（受拦端口）+ 假凭据 + 测试容器 7692；
* ``W4_GUARD_REQUIRE_BLOCKED_TARGET=1`` 让 ``live_port_guard.install()`` 在装门时
  就核对目标端口在射程内，不在就**拒绝装门**（子进程直接起不来）；
* step 0c 用同一份环境起一个只读子进程，实际构造 ``Settings`` 并打印
  ``NEO4J_URI``——证明应用侧解析出来的也是那个受拦地址，而不只是环境变量好看。

同时 ``W4_GUARD_NO_EXEMPT=1`` 彻底关掉豁免：负控运行里不允许出现 advisory。

## 这道负门不比什么

* 只对**一个**代表文件做原地变异，且只跑其中 **3 条钉死的 nodeid**（覆盖
  GET 成功 / POST 写 / 404 三种请求形态）——变异态每用例要完整跑一遍真实
  lifespan（被拦的连接各自带驱动级重试/超时），全 19 条 ≈ 35 分钟。它证明的是
  「防线 + lifespan 摘除」的组合在该形态上红得符合预期；不证明其余用例与其它
  12 个改造文件的个体变异也会红（fixture 形态相同，未逐一变异）。
* 只跑 pytest 主进程。防线不拦子进程（见 live_port_guard 模块 docstring），
  本脚本也不构造子进程连接场景。
* AST 门是**静态**分析：它证明的是「源码里没有裸 TestClient(app.main 的 app)」，
  不证明「运行时真的没连」。运行时证明由变异运行承担。
* 底层 socket / atexit / shell 注入等旁路由
  ``backend/scripts/lifespan_isolation_guard_probes.py`` 单独证明，不在本脚本内。

## 原地变异的还原纪律（MEMORY reference_temp_file_swap_needs_exit_trap）

变异标志在写盘**之前**置位；``finally`` 写回原始字节；``atexit`` 与
SIGTERM/SIGINT 处理器兜底。**还原前先 CAS**：读回当前字节，若既不是本脚本写下的
变异体、也不是原文，说明期间有并发编辑——此时**不覆盖**，把双方各存一份到
``*.negctl-conflict.*`` 并判失败（第八批 Codex MEDIUM）。已知残余窗口：
``SIGKILL`` / 断电无法兜底。
"""

from __future__ import annotations

import ast
import atexit
import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
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

#: 钉死的**完整 nodeid**（第八批 Codex MEDIUM：此前用 ``-k`` 子串过滤 + 名字
#: substring 判定，三个名字加任意后缀仍能满足「身份钉死」）。这里直接把完整
#: nodeid 当 pytest 参数传，并对预采集集做**集合全等**比对。
FIXED_TARGET_NODEIDS = (
    f"{TARGET_REL}::TestGetSubjectMapping::test_get_returns_200",
    f"{TARGET_REL}::TestAddSubjectMapping::test_add_returns_200",
    f"{TARGET_REL}::TestRemoveSubjectMapping::test_remove_nonexistent_returns_404",
)

PYTEST_TIMEOUT_S = 1500

#: 门的汇总行必须**整行唯一**匹配，且 total==blocked>0、advisory==unaccounted==0
#: （第八批 Codex HIGH：旧版只取 total/blocked 且只要求 blocked>=1，
#: ``attempts=7 (blocked=3, advisory=4, unaccounted=0)`` 会通过——而 advisory
#: 那 4 次已经调用了原始 connect，也就是真连过）。
SUMMARY_RE = re.compile(
    r"^NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=(\d+) "
    r"\(blocked=(\d+), advisory=(\d+), unaccounted=(\d+)\)$"
)

# ═══════════════════════════════════════════════════════════════════════════
# AST 门 —— 静态扫描「裸 with TestClient(app.main 的 app)」
# ═══════════════════════════════════════════════════════════════════════════

#: 扫描范围：``backend/tests/`` 下**除 integration / e2e 之外的全部 .py**。
#:
#: 第八批只扫 ``tests/api`` + ``tests/unit`` + 三个具名根文件（259 个），
#: ``tests/regression``、``tests/contract``、``tests/bdd``、``tests/smoke`` 以及其余
#: 根级 ``tests/*.py`` 都在盲区里 —— 那些文件里今天没有 ``with TestClient(app.main
#: 的 app)``（它们用的是**不带 with** 的 ``TestClient(app)``，Starlette 只在
#: ``__enter__`` 里跑 lifespan，所以不触发启动副作用），但没有任何东西拦着谁明天
#: 加一个。2026-09-03 实测扩到全量后为 371 个文件、**0 违规**，扩射程是纯增益。
#:
#: ``tests/integration`` 与 ``tests/e2e`` 仍在射程外：它们按路径豁免（只记录不拦截），
#: 本来就允许跑真实 lifespan —— 这是卡文裁决的既定设计，不是遗漏。
AST_EXCLUDED_TOP_DIRS = ("integration", "e2e")
AST_ROOT = "tests"

#: 同一 with 语句里允许充当隔离基元的名字（必须真的 import 自 tests.support.lifespan）。
ISOLATION_HELPER_NAMES = {"no_lifespan", "lifespan_lite"}

#: TestClient 的合法来源模块。
TESTCLIENT_MODULES = {"fastapi.testclient", "starlette.testclient"}
#: FastAPI 类的合法来源模块。
FASTAPI_MODULES = {"fastapi", "fastapi.applications"}

# 来源标签
O_MAIN_APP = "app.main:app"  # app.main 的进程级单例 app
O_MAIN_MODULE = "app.main:module"  # app.main 模块对象（供 m.app）
O_FASTAPI_CLASS = "fastapi:FastAPI"  # 真正 import 来的 FastAPI 类
O_FASTAPI_MODULE = "fastapi:module"  # fastapi 模块对象（供 fastapi.FastAPI()）
O_LOCAL_APP = "local:FastAPI()"  # 由**可证的** FastAPI 类构造出来的局部 app
O_TESTCLIENT_CLASS = "testclient:TestClient"
O_TESTCLIENT_MODULE = "testclient:module"
O_HELPER = "tests.support.lifespan:helper"
#: 本模块 ``def`` 出来的函数名（``localfunc:<name>``）。有了它，「这个名字此刻
#: 还是不是本模块那个 def」可证 —— 被赋值重绑定后解析结果就变了。
O_LOCAL_FUNC_PREFIX = "localfunc:"
O_UNKNOWN = "unknown"

_POS_MAX = (10**9, 0)


def _pos(node: ast.AST) -> tuple[int, int]:
    return (getattr(node, "lineno", 0), getattr(node, "col_offset", 0))


class _Scope:
    """一个 Python 作用域的**有序**绑定表。

    绑定按 ``(lineno, col_offset)`` 排序保存，因此可以做「该使用点之前最后一次
    绑定是什么」的 reaching-definition 判断（第八批 Codex HIGH：旧版是扁平集合，
    ``with TestClient(app)`` 之后再写 ``app = FastAPI()`` 也会被当成局部应用）。
    """

    __slots__ = ("node", "parent", "kind", "bindings")

    def __init__(self, node, parent, kind: str) -> None:
        self.node = node
        self.parent = parent
        self.kind = kind  # module | function | class
        self.bindings: dict[str, list[tuple[tuple[int, int], str]]] = {}

    def bind(self, name: str, pos: tuple[int, int], origin: str) -> None:
        self.bindings.setdefault(name, []).append((pos, origin))

    def sorted_bindings(self, name: str) -> list[tuple[tuple[int, int], str]]:
        return sorted(self.bindings.get(name, ()), key=lambda b: b[0])


class _ModuleIndex:
    """一次 ``ast.parse`` 的作用域索引 —— 追踪真实 import、语句顺序与重绑定。

    与第八批版本的三处结构性差别（均为 Codex HIGH 的直接整改）：

    1. **来源要可证**：``FastAPI()`` 只有在被调用的那个名字**解析得到真正从
       ``fastapi`` import 来的类**时才算局部应用；本地 ``def FastAPI(): ...``
       之类一律 unknown（= 违规）。
    2. **顺序要对**：同作用域内按位置取「使用点之前的最后一次绑定」；只在使用点
       之后才绑定的名字 = unknown。
    3. **重绑定要失效**：``no_lifespan`` 被本地 def / 赋值重新绑定后，该使用点
       解析到的就不再是 ``O_HELPER``，隔离资格随之失效。

    另外类体是**独立作用域**（Python 语义如此），不再把 ``class C: app = FastAPI()``
    的绑定漏进模块/函数作用域。
    """

    def __init__(self, tree: ast.Module) -> None:
        #: 「返回局部 FastAPI() 的函数」名集（名字级过程间近似）：正例文件
        #: （test_rag_four_state_api 等）的模式是 helper 内 ``app = FastAPI()``
        #: 然后 return，测试里元组解包后传入 TestClient —— 不识别会把正例
        #: 误判成 unknown 违规。近似是**单向放宽**且要求「函数体内确有由可证
        #: FastAPI 类构造的赋值 + return 同一个名字」，冒用面极窄。
        self.fastapi_returning_funcs: set[str] = set()
        self.module_scope = _Scope(tree, None, "module")
        self.scope_of: dict[int, _Scope] = {}
        # 建表与「哪些函数返回局部 app」互为输入 —— 迭代到不动点，最后再建一次表，
        # 保证对外暴露的 scopes 反映的是**最终**知识（否则验伪锚 4 那种
        # `app, n = make()` 会被建表期的空知识判成 unknown）。
        for _ in range(4):
            self._rebuild(tree)
            before = set(self.fastapi_returning_funcs)
            self._mark_all_fastapi_returning(tree)
            if self.fastapi_returning_funcs == before:
                break
        self._rebuild(tree)

    def _rebuild(self, tree: ast.Module) -> None:
        self.module_scope = _Scope(tree, None, "module")
        self.scope_of = {}
        self._build_scope(tree.body, self.module_scope)

    # ── 作用域构建 ──────────────────────────────────────────────────────
    def _build_scope(self, body, scope: _Scope) -> None:
        for stmt in body:
            self._walk_stmt(stmt, scope)

    def _walk_stmt(self, stmt: ast.stmt, scope: _Scope) -> None:
        """把 stmt 记进 scope；遇到新作用域则建子作用域，不把绑定漏给父层。"""
        self.scope_of[id(stmt)] = scope

        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # 专门的来源标签：这样「这个名字此刻确实还是本模块那个 def」可以被
            # 证明；被后续赋值重绑定后解析结果就不再是它，工厂近似随之失效。
            scope.bind(stmt.name, _pos(stmt), f"{O_LOCAL_FUNC_PREFIX}{stmt.name}")
            child = _Scope(stmt, scope, "function")
            for arg in self._all_args(stmt.args):
                child.bind(arg.arg, (0, 0), O_UNKNOWN)  # 形参：来源不可证
            self._build_scope(stmt.body, child)
            return
        if isinstance(stmt, ast.ClassDef):
            scope.bind(stmt.name, _pos(stmt), O_UNKNOWN)
            child = _Scope(stmt, scope, "class")
            self._build_scope(stmt.body, child)
            return

        self._record_bindings(stmt, scope)

        # 非作用域语句：递归其子块，绑定仍归当前 scope
        for field in ("body", "orelse", "finalbody", "handlers", "cases"):
            block = getattr(stmt, field, None)
            if not block:
                continue
            for sub in block:
                if isinstance(sub, ast.stmt):
                    self._walk_stmt(sub, scope)
                else:  # ExceptHandler / match_case 容器
                    self.scope_of[id(sub)] = scope
                    name = getattr(sub, "name", None)
                    if isinstance(name, str):
                        scope.bind(name, _pos(sub), O_UNKNOWN)
                    for inner in getattr(sub, "body", []) or []:
                        self._walk_stmt(inner, scope)

    @staticmethod
    def _all_args(a: ast.arguments):
        return [
            *a.posonlyargs,
            *a.args,
            *a.kwonlyargs,
            *([a.vararg] if a.vararg else []),
            *([a.kwarg] if a.kwarg else []),
        ]

    def _record_bindings(self, stmt: ast.stmt, scope: _Scope) -> None:
        pos = _pos(stmt)
        if isinstance(stmt, ast.ImportFrom):
            mod = stmt.module or ""
            for alias in stmt.names:
                bound = alias.asname or alias.name
                origin = O_UNKNOWN
                if mod == "app.main" and alias.name == "app":
                    origin = O_MAIN_APP
                elif mod in TESTCLIENT_MODULES and alias.name == "TestClient":
                    origin = O_TESTCLIENT_CLASS
                elif mod in FASTAPI_MODULES and alias.name == "FastAPI":
                    origin = O_FASTAPI_CLASS
                elif mod == "fastapi" and alias.name == "testclient":
                    origin = O_TESTCLIENT_MODULE
                elif mod == "tests.support.lifespan" and alias.name in ISOLATION_HELPER_NAMES:
                    origin = O_HELPER
                elif mod == "app" and alias.name == "main":
                    origin = O_MAIN_MODULE
                scope.bind(bound, pos, origin)
            return
        if isinstance(stmt, ast.Import):
            for alias in stmt.names:
                # `import a.b` 绑定的是**顶层包** `a`；`import a.b as x` 绑定 `x` = a.b
                bound = alias.asname or alias.name.split(".")[0]
                origin = O_UNKNOWN
                if alias.asname:
                    if alias.name == "app.main":
                        origin = O_MAIN_MODULE
                    elif alias.name in TESTCLIENT_MODULES:
                        origin = O_TESTCLIENT_MODULE
                    elif alias.name == "fastapi":
                        origin = O_FASTAPI_MODULE
                elif alias.name == "fastapi":
                    origin = O_FASTAPI_MODULE
                # `import app.main`（无 asname）绑定的是包 `app` —— 保持 unknown；
                # `app.main.app` 这种链式属性由 _attribute_origin 的专门分支解析。
                scope.bind(bound, pos, origin)
            return
        if isinstance(stmt, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            value = getattr(stmt, "value", None)
            if isinstance(stmt, ast.Assign):
                targets = stmt.targets
            elif isinstance(stmt, ast.AnnAssign):
                targets = [stmt.target]
            else:
                targets = [stmt.target]
            if value is None:
                for t in targets:
                    self._bind_target(t, pos, O_UNKNOWN, scope)
                return
            origin = self._value_origin(value, stmt, scope)
            for t in targets:
                self._bind_target(t, pos, origin, scope)
            return
        if isinstance(stmt, (ast.With, ast.AsyncWith)):
            for item in stmt.items:
                var = item.optional_vars
                if var is not None:
                    self._bind_target(var, pos, O_UNKNOWN, scope)
            return
        if isinstance(stmt, (ast.For, ast.AsyncFor)):
            self._bind_target(stmt.target, pos, O_UNKNOWN, scope)
            return
        if isinstance(stmt, (ast.Global, ast.Nonlocal)):
            for name in stmt.names:
                scope.bind(name, pos, O_UNKNOWN)
            return

    def _bind_target(self, target: ast.expr, pos, origin: str, scope: _Scope) -> None:
        if isinstance(target, ast.Name):
            scope.bind(target.id, pos, origin)
        elif isinstance(target, (ast.Tuple, ast.List)):
            for elt in target.elts:
                # 解包：单个元素的来源不可逐一证明，只有整体来源可证时才传递
                self._bind_target(elt, pos, origin, scope)

    def _value_origin(self, value: ast.expr, stmt: ast.stmt, scope: _Scope) -> str:
        """赋值右侧的来源。只有**可证**的形态才给非 unknown。"""
        if isinstance(value, ast.Call):
            callee = self._callable_origin(value.func, stmt, scope)
            if callee == O_FASTAPI_CLASS:
                return O_LOCAL_APP
            if self._is_local_app_factory_call(value.func, stmt, scope):
                return O_LOCAL_APP
            return O_UNKNOWN
        if isinstance(value, ast.Name):
            return self.resolve_name(value.id, _pos(stmt), scope)
        if isinstance(value, ast.Attribute):
            return self._attribute_origin(value, stmt, scope)
        return O_UNKNOWN

    def _is_local_app_factory_call(self, func: ast.expr, node: ast.AST, scope: _Scope) -> bool:
        """本模块内「返回局部 FastAPI() 的工厂」调用形态。

        两种、且只有两种：
          * ``make()`` —— 裸名字，必须是本模块 def 出来的那个名字；
          * ``self.make()`` / ``cls.make()`` —— 同类方法（``test_rag_four_state_api``
            的 ``self._real_service_client()`` 就是这一形态）。

        **刻意不接受** ``other.make()``：``other`` 的类型无法静态证明，任何对象
        只要有个同名方法就能冒充局部工厂 —— 那是把 fail-closed 拆掉。
        """
        if isinstance(func, ast.Name):
            if func.id not in self.fastapi_returning_funcs:
                return False
            # 名字此刻必须仍绑定到本模块那个 def（重绑定后不再算数）
            return self.resolve_name(func.id, _pos(node), scope) == f"{O_LOCAL_FUNC_PREFIX}{func.id}"
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            return func.value.id in ("self", "cls") and func.attr in self.fastapi_returning_funcs
        return False

    def _callable_origin(self, func: ast.expr, node: ast.AST, scope: _Scope) -> str:
        if isinstance(func, ast.Name):
            return self.resolve_name(func.id, _pos(node), scope)
        if isinstance(func, ast.Attribute):
            return self._attribute_origin(func, node, scope)
        return O_UNKNOWN

    def _attribute_origin(self, attr: ast.Attribute, node: ast.AST, scope: _Scope) -> str:
        base = attr.value
        # app.main.app（`import app.main` 之后）
        if (
            isinstance(base, ast.Attribute)
            and isinstance(base.value, ast.Name)
            and base.value.id == "app"
            and base.attr == "main"
            and attr.attr == "app"
        ):
            return O_MAIN_APP
        if isinstance(base, ast.Name):
            base_origin = self.resolve_name(base.id, _pos(node), scope)
            if base_origin == O_MAIN_MODULE and attr.attr == "app":
                return O_MAIN_APP
            if base_origin == O_TESTCLIENT_MODULE and attr.attr == "TestClient":
                return O_TESTCLIENT_CLASS
            if base_origin == O_FASTAPI_MODULE and attr.attr == "FastAPI":
                return O_FASTAPI_CLASS
            if base_origin == O_FASTAPI_MODULE and attr.attr == "testclient":
                return O_TESTCLIENT_MODULE
        return O_UNKNOWN

    # ── FastAPI-returning helper 识别 ───────────────────────────────────
    def _mark_all_fastapi_returning(self, tree: ast.Module) -> None:
        """两轮：先按「可证 FastAPI 类」标一轮，再让 helper 调 helper 收敛一次。"""
        for _ in range(2):
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    self._mark_fastapi_returning(node)

    def _mark_fastapi_returning(self, fd) -> None:
        own = self.scope_of.get(id(fd.body[0])) if fd.body else None
        if own is None:
            return
        # 只看**本函数自己作用域**里的语句：嵌套函数的 return 归它自己，
        # 不能算到外层函数头上（否则 `def outer(): def inner(): return FastAPI()`
        # 会把 outer 误标成返回局部 app）。
        own_stmts = [s for s in ast.walk(fd) if self.scope_of.get(id(s)) is own]
        local_app_names: set[str] = set()
        for stmt in own_stmts:
            if isinstance(stmt, (ast.Assign, ast.AnnAssign)) and getattr(stmt, "value", None) is not None:
                if self._value_origin(stmt.value, stmt, own) == O_LOCAL_APP:
                    targets = stmt.targets if isinstance(stmt, ast.Assign) else [stmt.target]
                    for t in targets:
                        if isinstance(t, ast.Name):
                            local_app_names.add(t.id)
        for stmt in own_stmts:
            if isinstance(stmt, ast.Return) and stmt.value is not None:
                candidates = stmt.value.elts if isinstance(stmt.value, ast.Tuple) else [stmt.value]
                for c in candidates:
                    if isinstance(c, ast.Name) and c.id in local_app_names:
                        self.fastapi_returning_funcs.add(fd.name)
                        return
                    if isinstance(c, ast.Call) and self._callable_origin(c.func, stmt, own) == O_FASTAPI_CLASS:
                        self.fastapi_returning_funcs.add(fd.name)
                        return

    # ── 解析 ────────────────────────────────────────────────────────────
    def scope_for(self, node: ast.AST) -> _Scope:
        return self.scope_of.get(id(node), self.module_scope)

    def resolve_name(self, name: str, pos: tuple[int, int], scope: _Scope) -> str:
        """在 ``scope`` 处、位置 ``pos`` 上，名字 ``name`` 的来源。

        * **本作用域**：取 ``pos`` **之前**最后一次绑定；只在 ``pos`` 之后才绑定
          ⇒ unknown（Python 语义下那是 UnboundLocalError，静态上也不可证）。
        * **外层作用域**：函数调用时刻不确定，因此要求该名字在外层的**全部**绑定
          来源一致；有分歧 ⇒ unknown（fail-closed）。
        * 类作用域对内层函数不可见（Python 语义），查找链跳过它。
        """
        cur: _Scope | None = scope
        first = True
        while cur is not None:
            skip = (not first) and cur.kind == "class"
            if not skip and name in cur.bindings:
                bindings = cur.sorted_bindings(name)
                if first:
                    before = [o for p, o in bindings if p < pos]
                    if before:
                        return before[-1]
                    return O_UNKNOWN
                origins = {o for _, o in bindings}
                return origins.pop() if len(origins) == 1 else O_UNKNOWN
            cur = cur.parent
            first = False
        return O_UNKNOWN

    def resolve_arg(self, arg: ast.expr, node: ast.AST, scope: _Scope) -> str:
        if isinstance(arg, ast.Name):
            return self.resolve_name(arg.id, _pos(node), scope)
        if isinstance(arg, ast.Attribute):
            return self._attribute_origin(arg, node, scope)
        if isinstance(arg, ast.Call):
            return self._value_origin(arg, node if isinstance(node, ast.stmt) else arg, scope)
        return O_UNKNOWN


def _syntactic_call_name(node: ast.expr) -> str | None:
    """Call(...) 的**词法**函数名：``f()`` → f；``m.f()`` → f。"""
    if not isinstance(node, ast.Call):
        return None
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


def analyze_source(source: str, rel: str) -> list[str]:
    """对一份源码跑 AST 门，返回违规明细（空 = 合规）。"""
    violations: list[str] = []
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return [f"{rel}: SyntaxError {e}"]
    index = _ModuleIndex(tree)

    for node in ast.walk(tree):
        if not isinstance(node, (ast.With, ast.AsyncWith)):
            continue
        scope = index.scope_for(node)
        for pos_i, item in enumerate(node.items):
            ctx = item.context_expr
            if not isinstance(ctx, ast.Call):
                continue
            syn = _syntactic_call_name(ctx)
            callee_origin = index._callable_origin(ctx.func, node, scope)
            # 判为 TestClient 调用的两条路：词法叫 TestClient（哪怕被遮蔽），
            # 或者解析到真正 import 来的 TestClient 类（覆盖 `as TC` 别名）。
            if syn != "TestClient" and callee_origin != O_TESTCLIENT_CLASS:
                continue
            if syn == "TestClient" and callee_origin != O_TESTCLIENT_CLASS:
                violations.append(
                    f"{rel}:{node.lineno}: with TestClient(...) —— TestClient 这个名字"
                    f"解析不到 {sorted(TESTCLIENT_MODULES)} 的真实 import（当前来源"
                    f"={callee_origin}），无法证明它是被隔离约束覆盖的那个 TestClient"
                )
                continue
            if not ctx.args:
                violations.append(f"{rel}:{node.lineno}: TestClient() 无参 —— 人工复核")
                continue
            arg = ctx.args[0]
            origin = index.resolve_arg(arg, node, scope)
            if origin == O_LOCAL_APP:
                continue  # 局部 FastAPI() 正例（且 FastAPI 类来源可证）
            arg_desc = arg.id if isinstance(arg, ast.Name) else "<expr>"
            if origin != O_MAIN_APP:
                # unknown：来源无法静态证明 —— 按违规处理（fail-closed）。
                violations.append(
                    f"{rel}:{node.lineno}: with TestClient({arg_desc}) —— app 来源"
                    f"无法静态证明（解析结果={origin}，按违规处理，人工复核）"
                )
                continue
            # app 来自 app.main：必须有**排在前面的**隔离兄弟项、操作同一个 app、
            # 且该 helper 名在**该使用点**确实解析为 tests.support.lifespan 的 import
            # （重绑定 / 本地同名 no-op 一律失效）。
            ok = False
            for hpos, hitem in enumerate(node.items):
                if hpos >= pos_i:
                    break
                hctx = hitem.context_expr
                if not isinstance(hctx, ast.Call):
                    continue
                if index._callable_origin(hctx.func, node, scope) != O_HELPER:
                    continue
                hargs = hctx.args
                if hargs and isinstance(arg, ast.Name) and isinstance(hargs[0], ast.Name) and hargs[0].id == arg.id:
                    ok = True
                    break
            if not ok:
                violations.append(
                    f"{rel}:{node.lineno}: with TestClient({arg_desc}) —— app 来自"
                    " app.main 且缺少**在前**的 no_lifespan/lifespan_lite 兄弟项"
                    "（顺序不符、参数不同名，或 helper 名在该点已被重绑定/并非"
                    " import 自 tests.support.lifespan，同样算违规）"
                )
    return violations


def ast_scope_files() -> list[Path]:
    """射程内文件：``backend/tests`` 下除 integration / e2e 顶层目录外的全部 .py。"""
    root = BACKEND_DIR / AST_ROOT
    files: list[Path] = []
    for p in sorted(root.rglob("*.py")):
        rel = p.relative_to(root)
        if rel.parts and rel.parts[0] in AST_EXCLUDED_TOP_DIRS:
            continue
        files.append(p)
    return files


def run_ast_gate() -> tuple[int, list[str], int]:
    """返回 (违规数, 违规明细, 扫描的文件数)。"""
    files = ast_scope_files()
    # 射程不能悄悄缩水成空集/极小集 —— 空集扫描必然 0 违规，是最典型的假绿。
    if len(files) < 200:
        return (
            1,
            [f"AST 射程只剩 {len(files)} 个文件（期望 ≥200）—— 射程缩水会让本门恒绿，判门损坏"],
            len(files),
        )

    violations: list[str] = []
    for path in files:
        rel = str(path.relative_to(BACKEND_DIR))
        violations.extend(analyze_source(path.read_text(encoding="utf-8"), rel))
    return len(violations), violations, len(files)


# ═══════════════════════════════════════════════════════════════════════════
# AST 门的负控（四类绕过必须被抓 + 验伪锚：正例必须不被抓）
# ═══════════════════════════════════════════════════════════════════════════

_AST_MUST_FLAG: list[tuple[str, str]] = [
    (
        "属性式 TestClient（import fastapi.testclient as tc）",
        "import fastapi.testclient as tc\n"
        "from app.main import app\n"
        "def t():\n"
        "    with tc.TestClient(app) as c:\n"
        "        pass\n",
    ),
    (
        "局部重定义同名 no_lifespan（import provenance 必须失效）",
        "from app.main import app\n"
        "from fastapi.testclient import TestClient\n"
        "from tests.support.lifespan import no_lifespan\n"
        "import contextlib\n"
        "@contextlib.contextmanager\n"
        "def no_lifespan(a):\n"
        "    yield a\n"
        "def t():\n"
        "    with no_lifespan(app), TestClient(app) as c:\n"
        "        pass\n",
    ),
    (
        "with 之后才 app = FastAPI()（语句顺序）",
        "from fastapi import FastAPI\n"
        "from fastapi.testclient import TestClient\n"
        "def t():\n"
        "    with TestClient(app) as c:\n"
        "        pass\n"
        "    app = FastAPI()\n",
    ),
    (
        "class body 污染冒充局部 app",
        "from fastapi import FastAPI\n"
        "from fastapi.testclient import TestClient\n"
        "class C:\n"
        "    app = FastAPI()\n"
        "def t():\n"
        "    with TestClient(app) as c:\n"
        "        pass\n",
    ),
    (
        "伪造本地 FastAPI() 工厂",
        "from fastapi.testclient import TestClient\n"
        "def FastAPI():\n"
        "    return object()\n"
        "app = FastAPI()\n"
        "def t():\n"
        "    with TestClient(app) as c:\n"
        "        pass\n",
    ),
    (
        "helper 顺序在 TestClient 之后",
        "from app.main import app\n"
        "from fastapi.testclient import TestClient\n"
        "from tests.support.lifespan import no_lifespan\n"
        "def t():\n"
        "    with TestClient(app), no_lifespan(app) as c:\n"
        "        pass\n",
    ),
    (
        "TestClient 名字被本地遮蔽（无法证明是真 TestClient）",
        "from fastapi import FastAPI\n"
        "def TestClient(a):\n"
        "    return a\n"
        "def t():\n"
        "    app = FastAPI()\n"
        "    with TestClient(app) as c:\n"
        "        pass\n",
    ),
    (
        "import app.main as m; m.app 裸用",
        "import app.main as m\n"
        "from fastapi.testclient import TestClient\n"
        "def t():\n"
        "    with TestClient(m.app) as c:\n"
        "        pass\n",
    ),
    (
        "外部对象冒充局部 app 工厂（other.make() 不是 self.make()）",
        "from fastapi import FastAPI\n"
        "from fastapi.testclient import TestClient\n"
        "def make():\n"
        "    a = FastAPI()\n"
        "    return a\n"
        "def t(other):\n"
        "    app = other.make()\n"
        "    with TestClient(app) as c:\n"
        "        pass\n",
    ),
    (
        "工厂名被重绑定后仍冒充局部 app 工厂",
        "from fastapi import FastAPI\n"
        "from fastapi.testclient import TestClient\n"
        "from app.main import app as real_app\n"
        "def make():\n"
        "    a = FastAPI()\n"
        "    return a\n"
        "def t():\n"
        "    make = lambda: real_app\n"
        "    app = make()\n"
        "    with TestClient(app) as c:\n"
        "        pass\n",
    ),
]

_AST_MUST_PASS: list[tuple[str, str]] = [
    (
        "验伪锚 1：标准隔离形态",
        "from app.main import app\n"
        "from fastapi.testclient import TestClient\n"
        "from tests.support.lifespan import no_lifespan\n"
        "def t():\n"
        "    with no_lifespan(app), TestClient(app) as c:\n"
        "        pass\n",
    ),
    (
        "验伪锚 2：函数级 import + 别名 TestClient",
        "def t():\n"
        "    from app.main import app\n"
        "    from fastapi.testclient import TestClient as TC\n"
        "    from tests.support.lifespan import lifespan_lite\n"
        "    with lifespan_lite(app), TC(app) as c:\n"
        "        pass\n",
    ),
    (
        "验伪锚 3：局部 FastAPI()（来源可证）",
        "from fastapi import FastAPI\n"
        "from fastapi.testclient import TestClient\n"
        "def t():\n"
        "    app = FastAPI()\n"
        "    with TestClient(app) as c:\n"
        "        pass\n",
    ),
    (
        "验伪锚 4：helper 返回局部 FastAPI() 后解包",
        "from fastapi import FastAPI\n"
        "from fastapi.testclient import TestClient\n"
        "def make():\n"
        "    a = FastAPI()\n"
        "    return a, 1\n"
        "def t():\n"
        "    app, n = make()\n"
        "    with TestClient(app) as c:\n"
        "        pass\n",
    ),
    (
        "验伪锚 5：同类方法工厂 self._make()（test_rag_four_state_api 的真实形态）",
        "from fastapi import FastAPI\n"
        "from fastapi.testclient import TestClient\n"
        "class T:\n"
        "    def _make(self):\n"
        "        app = FastAPI()\n"
        "        return app, 1\n"
        "    def test_x(self):\n"
        "        app, _ = self._make()\n"
        "        with TestClient(app, raise_server_exceptions=False) as c:\n"
        "            pass\n",
    ),
]


def run_ast_negative_control() -> int:
    """四类绕过必须被抓；四条正例必须不被抓（验伪锚，防「恒判违规」的假门）。"""
    print("=== AST GATE NEGATIVE CONTROL ===")
    failures: list[str] = []
    for label, src in _AST_MUST_FLAG:
        vs = analyze_source(src, f"<negctl:{label}>")
        status = "CAUGHT" if vs else "*** MISSED ***"
        print(f"  [must-flag] {status}: {label}")
        if not vs:
            failures.append(f"绕过未被抓: {label}")
        else:
            print(f"              → {vs[0]}")
    for label, src in _AST_MUST_PASS:
        vs = analyze_source(src, f"<negctl:{label}>")
        status = "CLEAN" if not vs else "*** FALSE POSITIVE ***"
        print(f"  [must-pass] {status}: {label}")
        if vs:
            failures.append(f"正例误判: {label} → {vs}")
    if failures:
        print("AST-NEGATIVE-CONTROL: FAIL")
        for f in failures:
            print(f"  - {f}")
        return 1
    print(f"AST-NEGATIVE-CONTROL: PASS ({len(_AST_MUST_FLAG)} 绕过全抓 / {len(_AST_MUST_PASS)} 正例全净)")
    return 0


# ═══════════════════════════════════════════════════════════════════════════
# 子进程环境（第八批 BLOCKER 的收口）
# ═══════════════════════════════════════════════════════════════════════════

#: 负控钉死的连接目标：受拦端口 + loopback。门必然拦得住它。
PINNED_NEO4J_URI = "bolt://127.0.0.1:7691"
PINNED_TEST_URI = "bolt://127.0.0.1:7692"
#: 假凭据 —— 即使某条路径绕过了门，也拿不到任何真实库的会话。
PINNED_NEO4J_USER = "w4-negctl-invalid-user"
PINNED_NEO4J_PASSWORD = "w4-negctl-invalid-password"


def _child_env(vault_tmp: Path, lance_tmp: Path, ledger: Path | None) -> dict[str, str]:
    """构造子进程环境：清 Neo4j 面 → 钉死受拦目标 → 关豁免 → 隔离写路径。"""
    env = os.environ.copy()
    # 1) 清掉调用者带进来的**全部** Neo4j 相关变量（含 NEO4J_URI/USER/PASSWORD/
    #    TEST_URI/AUTH/DATABASE… 无论叫什么，只要以 NEO4J 开头）。
    for key in [k for k in env if k.upper().startswith("NEO4J")]:
        env.pop(key, None)
    # 2) 钉死：目标端口必在门的射程内；凭据是假的。
    env["NEO4J_URI"] = PINNED_NEO4J_URI
    env["NEO4J_TEST_URI"] = PINNED_TEST_URI
    env["NEO4J_USER"] = PINNED_NEO4J_USER
    env["NEO4J_PASSWORD"] = PINNED_NEO4J_PASSWORD
    # 3) 门自身的 fail-closed 开关：目标不在射程内就拒绝装门（子进程起不来）。
    env["W4_GUARD_REQUIRE_BLOCKED_TARGET"] = "1"
    # 4) 负控运行里不允许出现 advisory —— 豁免彻底关掉。
    env["W4_GUARD_NO_EXEMPT"] = "1"
    # 5) 写路径隔离到 tmp（live vault / 现网 LanceDB 只读）。
    #    ⚠️ canonical 与 legacy 两个 LanceDB 变量必须**同值**：
    #    `lib/agentic_rag/config.py::_resolve_lancedb_db_path` 在两者不同时抛
    #    RuntimeError，而 `app/main.py:103` 是**无守护直调**——于是 lifespan 会在
    #    LanceDB 这一步就 abort，**根本走不到 Neo4j 预热**，负门拿到 blocked=0
    #    却以为是「哨兵没接住」。只 pin canonical 而让 legacy 从 .env（本车道
    #    .env:94 就有 LANCEDB_PATH）漏进来，负门就变成了在测另一件事。
    #    2026-09-03 于本车道实测：只 pin canonical ⇒ 3 条全部 setup ERROR
    #    "Conflicting LanceDB paths"、attempts=0；两者同值 ⇒ 连接尝试正常发生。
    env["CANVAS_BASE_PATH"] = str(vault_tmp)
    env["LANCEDB_DATA_PATH"] = str(lance_tmp)
    env["LANCEDB_PATH"] = str(lance_tmp)
    # 6) 防注入：addopts 能塞 --rootdir/--confcutdir 绕开根 conftest；
    #    PYTEST_PLUGINS 能在门装上之前 import 任意插件。
    env.pop("PYTEST_ADDOPTS", None)
    env.pop("PYTEST_PLUGINS", None)
    # ⚠️ 不设 PYTEST_DISABLE_PLUGIN_AUTOLOAD：根 conftest 与目标文件依赖
    #    hypothesis / pytest-asyncio / pytest-bdd 的注册，关掉 autoload 会让
    #    collection 直接坏掉——那是「门没被验证」而不是「门更严」。门前窗口改由
    #    guard_plugin 的 **import 期装门** 收敛（见该模块 docstring）。
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    # -p 插件加载早于 pytest 把 rootdir 塞进 sys.path —— 必须显式给 PYTHONPATH。
    env["PYTHONPATH"] = str(BACKEND_DIR) + os.pathsep + env.get("PYTHONPATH", "")
    if ledger is not None:
        env["W4_GUARD_LEDGER"] = str(ledger)
    else:
        env.pop("W4_GUARD_LEDGER", None)
    return env


def _base_cmd() -> list[str]:
    """pytest 子进程命令前缀。

    用 ``sys.executable -m pytest`` 而不是 ``BACKEND_DIR/.venv/bin/pytest``
    （第八批 Codex MEDIUM/卡文裁判 2）：负控必须跑在**调用者指定的那个解释器**上，
    否则「我用 A 解释器验证的门」和「你用 B 解释器跑的测试」不是同一件事。
    """
    return [
        sys.executable,
        "-m",
        "pytest",
        "-p",
        "tests.support.guard_plugin",  # 显式点名装门（不受 rootdir/confcutdir 影响）
        "-p",
        "no:cacheprovider",
        "--override-ini=addopts=",
    ]


def _parse_summary(stdout: str) -> tuple[int, int, int, int] | str:
    """整行唯一解析门的汇总行。返回 (total, blocked, advisory, unaccounted) 或错误串。"""
    hits = [m for line in stdout.splitlines() if (m := SUMMARY_RE.match(line.strip()))]
    if len(hits) != 1:
        return f"门汇总行匹配 {len(hits)} 次（期望恰好 1 次）"
    return tuple(int(g) for g in hits[0].groups())  # type: ignore[return-value]


# ═══════════════════════════════════════════════════════════════════════════
# 变异 + 子进程 + 还原
# ═══════════════════════════════════════════════════════════════════════════


def sha_of(path: Path) -> str:
    if not path.exists():
        return "absent"
    return hashlib.sha256(path.read_bytes()).hexdigest()


def runtime_snapshot() -> str:
    return "\n".join(f"{sha_of(p)}  {p}" for p in RUNTIME_FILES)


def restore_absent_runtime_files(before: dict[Path, str]) -> tuple[list[str], list[str]]:
    """把变异运行创建出来的运行时文件删掉，恢复到跑之前的状态。

    只处理「跑之前 absent、跑之后存在」这一种情况 —— 那是**本脚本引起的**新增，
    删掉即回到原状。对「跑之前就有、内容变了」的文件**刻意不覆盖**：那可能混进了
    并发进程追加的真实数据，盲写回去会静默吞掉别人的记录（与变异体的 CAS 同口径）。
    这种情况返回到 ``unresolved``，由调用方判失败并交人工。

    Returns:
        (removed, unresolved) 两个路径描述列表。
    """
    removed: list[str] = []
    unresolved: list[str] = []
    for path in RUNTIME_FILES:
        was = before.get(path, "absent")
        now = sha_of(path)
        if was == now:
            continue
        if was == "absent" and path.exists():
            path.unlink()
            removed.append(str(path))
        else:
            unresolved.append(f"{path}: {was} → {now}")
    return removed, unresolved


def main() -> int:
    print("=== lifespan isolation NEGATIVE CONTROL ===")
    print(f"    interpreter: {sys.executable}")

    if "--ast-negative-control" in sys.argv:
        return run_ast_negative_control()

    # -- 0a. 门必须被根 conftest 接线（否则哨兵缺席，负门失去被测对象）--------
    conftest_text = (BACKEND_DIR / "tests/conftest.py").read_text(encoding="utf-8")
    if "live_port_guard" not in conftest_text:
        print(
            "NEGATIVE-CONTROL: FAIL — 根 tests/conftest.py 未引用 live_port_guard："
            "结账哨兵不会在子进程里工作，负门失去被测对象。"
        )
        return 1

    # -- 0b. AST 门（裁判 6）+ 其负控 ---------------------------------------
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
    pos_ledger = tmp_root / "ledger-positive.json"
    neg_ledger = tmp_root / "ledger-negative.json"

    # -- 0c. 前置：证明**应用侧**解析出来的 NEO4J_URI 也是那个受拦地址 --------
    #    环境变量好看不等于 Settings 解析结果好看（.env 覆盖、别名字段…）。
    preflight_env = _child_env(vault_tmp, lance_tmp, None)
    preflight = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys;"
            "sys.path.insert(0, 'lib');"
            "from app.config import get_settings;"
            "from agentic_rag.config import _resolve_lancedb_db_path;"
            "s=get_settings();"
            "print('RESOLVED_NEO4J_URI=%s' % s.NEO4J_URI);"
            "print('RESOLVED_LANCEDB=%s' % _resolve_lancedb_db_path())",
        ],
        cwd=BACKEND_DIR,
        env=preflight_env,
        capture_output=True,
        text=True,
        timeout=180,
    )
    resolved = ""
    resolved_lance = ""
    for line in preflight.stdout.splitlines():
        if line.startswith("RESOLVED_NEO4J_URI="):
            resolved = line.split("=", 1)[1].strip()
        elif line.startswith("RESOLVED_LANCEDB="):
            resolved_lance = line.split("=", 1)[1].strip()
    print(f"[0c] Settings 解析出的 NEO4J_URI = {resolved!r} LanceDB = {resolved_lance!r} (rc={preflight.returncode})")
    # LanceDB resolver 在 canonical/legacy 两个变量不同值时抛 RuntimeError，而
    # app/main.py 是无守护直调 —— 那会让 lifespan 在**到达 Neo4j 之前**就 abort，
    # 负门得到 blocked=0 却看起来像「哨兵没接住」。这里提前把它变成一条明话。
    if preflight.returncode == 0 and not resolved_lance:
        print(
            "NEGATIVE-CONTROL: FAIL — LanceDB 路径未能解析（canonical/legacy 冲突？），lifespan 会在到达 Neo4j 前 abort"
        )
        print(preflight.stdout[-800:])
        print(preflight.stderr[-800:])
        shutil.rmtree(tmp_root, ignore_errors=True)
        return 1
    if preflight.returncode != 0 or resolved != PINNED_NEO4J_URI:
        print(
            "NEGATIVE-CONTROL: FAIL — 应用侧解析出的 NEO4J_URI 不是钉死的受拦地址；"
            f"期望 {PINNED_NEO4J_URI!r}，实得 {resolved!r}。"
            "在此之前**不得**摘掉隔离运行（否则会真连一个门射程之外的库）。"
        )
        print("--- preflight stderr tail ---")
        print(preflight.stderr[-1200:])
        shutil.rmtree(tmp_root, ignore_errors=True)
        return 1

    original = TARGET.read_bytes()
    original_sha = hashlib.sha256(original).hexdigest()
    mutated_bytes = original.decode("utf-8").replace(ANCHOR, MUTATED).encode("utf-8")
    mutated = False
    conflict_note: str | None = None

    def _restore(*_a) -> None:
        """CAS 后写回原始字节（幂等）。变异标志先置位，保证任何路径都会走到这里。

        CAS：当前盘上的字节必须是「本脚本写下的变异体」或「原文」二者之一。
        既不是 ⇒ 期间有并发编辑 —— **不覆盖**，双方各存一份并留下 conflict 记录
        （第八批 Codex MEDIUM：无条件写回会静默吞掉别人的合法编辑）。
        """
        nonlocal mutated, conflict_note
        if not mutated:
            return
        current = TARGET.read_bytes()
        if current not in (mutated_bytes, original):
            stamp = time.strftime("%Y%m%d-%H%M%S")
            theirs = TARGET.with_suffix(TARGET.suffix + f".negctl-conflict-theirs.{stamp}")
            ours = TARGET.with_suffix(TARGET.suffix + f".negctl-conflict-original.{stamp}")
            theirs.write_bytes(current)
            ours.write_bytes(original)
            conflict_note = (
                f"并发编辑冲突：{TARGET_REL} 在变异期间被第三方修改。"
                f"未覆盖；对方版本保存在 {theirs.name}，本脚本持有的原文保存在 {ours.name}。"
            )
            print(f"*** {conflict_note} ***", file=sys.stderr)
            mutated = False
            return
        TARGET.write_bytes(original)
        mutated = False

    atexit.register(_restore)
    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP, signal.SIGQUIT):
        signal.signal(sig, lambda *_: (_restore(), sys.exit(130)))

    before_runtime = runtime_snapshot()
    before_runtime_map = {p: sha_of(p) for p in RUNTIME_FILES}
    positive_runtime_ok = False
    mutated_runtime_delta = ""
    runtime_removed: list[str] = []
    runtime_unresolved: list[str] = []
    pytest_rc: int | None = None
    total = 0
    green: list[str] = []
    red_nodeids: set[str] = set()
    red_for_wrong_reason: list[str] = []
    reason_verified: set[str] = set()
    expected_nodeids: set[str] = set()
    summary: tuple[int, int, int, int] | str = "未运行"
    ledger_problem: str | None = None
    pos_problem: str | None = None
    child_stdout = ""
    child_stderr = ""
    try:
        # -- 1. 预采集 nodeid（变异前）：必须与钉死的完整 nodeid 集全等 -------
        env = _child_env(vault_tmp, lance_tmp, None)
        collect = subprocess.run(
            _base_cmd() + [*FIXED_TARGET_NODEIDS, "--collect-only", "-q"],
            cwd=BACKEND_DIR,
            env=env,
            capture_output=True,
            text=True,
            timeout=PYTEST_TIMEOUT_S,
        )
        expected_nodeids = {ln.strip() for ln in collect.stdout.splitlines() if "::" in ln}
        if expected_nodeids != set(FIXED_TARGET_NODEIDS):
            print(
                "NEGATIVE-CONTROL: FAIL — 预采集集与钉死 nodeid **全等**判定不成立："
                f"缺 {sorted(set(FIXED_TARGET_NODEIDS) - expected_nodeids)}，"
                f"多 {sorted(expected_nodeids - set(FIXED_TARGET_NODEIDS))}"
            )
            print("--- collect stdout tail ---")
            print(collect.stdout[-1500:])
            return 1
        print(f"[1] 预采集 nodeid: {len(expected_nodeids)} 条（与钉死完整 nodeid 全等）")

        # -- 1b. 正控：同环境、未变异，三条必须全绿且门账为零 ----------------
        #     第八批 Codex MEDIUM：不先证明「原样是绿的」，就无法区分
        #     「变异让它红了」和「它本来就红」。
        pos = subprocess.run(
            _base_cmd() + [*FIXED_TARGET_NODEIDS, "-q", "--tb=short", "-rA"],
            cwd=BACKEND_DIR,
            env=_child_env(vault_tmp, lance_tmp, pos_ledger),
            capture_output=True,
            text=True,
            timeout=PYTEST_TIMEOUT_S,
        )
        pos_summary = _parse_summary(pos.stdout)
        print(f"[1b] 正控 rc={pos.returncode} 门汇总={pos_summary}")
        if pos.returncode != 0:
            pos_problem = f"正控 rc={pos.returncode} ≠ 0（未变异的三条用例本来就不绿）"
        elif not isinstance(pos_summary, tuple):
            pos_problem = f"正控门汇总行解析失败：{pos_summary}"
        elif pos_summary != (0, 0, 0, 0):
            pos_problem = f"正控门账非零：{pos_summary}（隔离态不应有任何连接尝试）"
        # 隔离态**必须**没动任何运行时文件 —— 这是本卡真正要证的那句话。
        positive_runtime_ok = runtime_snapshot() == before_runtime
        if not positive_runtime_ok and not pos_problem:
            pos_problem = "正控（隔离态）动了运行时文件 —— no_lifespan 没挡住启动副作用"
        if pos_problem:
            print(f"NEGATIVE-CONTROL: FAIL — {pos_problem}")
            print("--- 正控 stdout tail ---")
            print(pos.stdout[-2000:])
            return 1
        print("[1c] 正控运行时文件: unchanged（隔离态零副作用）")

        # -- 2. 原地摘掉 no_lifespan ----------------------------------------
        count = original.decode("utf-8").count(ANCHOR)
        if count != 1:
            print(
                f"NEGATIVE-CONTROL: FAIL — 隔离锚点出现 {count} 次（期望恰好 1 次），"
                f"文件形态与本脚本假设不符，拒绝盲改: {TARGET_REL}"
            )
            return 1
        mutated = True  # 先置位再写盘：任何崩溃路径都会走 _restore
        TARGET.write_bytes(mutated_bytes)
        print(f"[2] 已摘掉 no_lifespan: {TARGET_REL}")

        # -- 3. 变异运行 ----------------------------------------------------
        cmd = _base_cmd() + [*FIXED_TARGET_NODEIDS, "-q", "--tb=no", "-rA", f"--junitxml={junit_xml}"]
        print("[3] pytest 子进程（串行）:", " ".join(cmd))
        try:
            proc = subprocess.run(
                cmd,
                cwd=BACKEND_DIR,
                env=_child_env(vault_tmp, lance_tmp, neg_ledger),
                capture_output=True,
                text=True,
                timeout=PYTEST_TIMEOUT_S,
            )
        except subprocess.TimeoutExpired as e:
            print("NEGATIVE-CONTROL: FAIL — 变异运行超时；faulthandler dump（stderr）如下")
            print((e.stderr or "")[-5000:])
            print("--- stdout tail ---")
            print((e.stdout or "")[-1000:])
            return 1
        pytest_rc = proc.returncode
        child_stdout = proc.stdout
        child_stderr = proc.stderr
        print(f"    pytest exit={pytest_rc}")

        # -- 3b. 正证据：total == blocked > 0 且 advisory == unaccounted == 0 --
        summary = _parse_summary(proc.stdout)
        if not isinstance(summary, tuple):
            print(f"NEGATIVE-CONTROL: FAIL — {summary}（guard_plugin 未加载？）")
            print("--- child stdout tail ---")
            print(proc.stdout[-1500:])
            return 1
        s_total, s_blocked, s_advisory, s_unacct = summary
        print(f"[3b] 子进程门汇总: total={s_total} blocked={s_blocked} advisory={s_advisory} unaccounted={s_unacct}")

        # -- 3c. 父进程独立复核账本（不只信子进程 stdout）--------------------
        if not neg_ledger.exists():
            ledger_problem = "子进程未落账本（最终总账 atexit 未跑？）"
        else:
            led = json.loads(neg_ledger.read_text(encoding="utf-8"))
            print(
                f"[3c] 账本: {json.dumps({k: v for k, v in led.items() if k != 'unaccounted_records'}, ensure_ascii=False)}"
            )
            if (led["total"], led["blocked"], led["advisory"], led["unaccounted"]) != summary:
                ledger_problem = f"账本 {led} 与 stdout 汇总 {summary} 不一致"
            elif not led.get("exempt_disabled"):
                ledger_problem = "账本显示豁免未被禁用（W4_GUARD_NO_EXEMPT 未生效）"

        # -- 4. 解析 junitxml：红因判定必须吃完整 failure 正文 ---------------
        if not junit_xml.exists():
            print("NEGATIVE-CONTROL: FAIL — junitxml 未生成")
            return 1
        module_dotted = TARGET_REL[:-3].replace("/", ".")
        for case in ET.parse(junit_xml).getroot().iter("testcase"):
            classname = case.get("classname", "")
            name = case.get("name", "")
            if classname.startswith(module_dotted):
                class_chain = classname[len(module_dotted) :].lstrip(".")
                nid = f"{TARGET_REL}::" + (f"{class_chain.replace('.', '::')}::{name}" if class_chain else name)
            else:
                nid = f"{classname.replace('.', '/')}::{name}"
            total += 1
            # ``<error>`` 与 ``<failure>`` 都算红：setup/teardown 阶段炸掉时 pytest
            # 写的是 ``<error>``，只找 ``<failure>`` 会把它当成绿（fail-open）。
            failure = case.find("failure")
            if failure is None:
                failure = case.find("error")
            if failure is None:
                green.append(nid)
                continue
            red_nodeids.add(nid)
            text = " ".join(filter(None, [(failure.get("message") or ""), (failure.text or "")]))
            if EXPECTED_REASON in text:
                reason_verified.add(nid)
            else:
                red_for_wrong_reason.append(f"{nid} :: {text[:160] or '<failure 无正文 — 红因不明>'}")

        print(
            f"[4] junitxml: total={total} red={len(red_nodeids)} "
            f"green={len(green)} red-wrong-reason={len(red_for_wrong_reason)}"
        )
        for g in green:
            print(f"    GREEN (不应绿): {g}")
        for w in red_for_wrong_reason:
            print(f"    RED-WRONG-REASON: {w}")
    finally:
        # -- 5. CAS + 逐字节还原（无论上面死在哪一步；atexit/信号再兜底）-----
        _restore()
        restored_identical = sha_of(TARGET) == original_sha
        after_runtime = runtime_snapshot()
        mutated_runtime_delta = "" if after_runtime == before_runtime else after_runtime
        # 摘掉隔离之后运行时文件**被写了**，这不是失败，是本卡要证明的那件事：
        # socket 门只管连接，挡不住文件写；挡住文件写的是 no_lifespan。
        # `app/services/vault_index_orchestrator.py:101` 的 pending 文件路径是
        # **硬编码**的（`app/data/vault_index_pending.jsonl`，不读任何 env），
        # 所以变异态无法把它重定向到 tmp —— 只能事后把本脚本造出来的新增删掉。
        runtime_removed, runtime_unresolved = restore_absent_runtime_files(before_runtime_map)
        runtime_unchanged = runtime_snapshot() == before_runtime

    print(f"[5] 还原完成; byte-identical={restored_identical}; 运行时现场已复原={runtime_unchanged}")
    if mutated_runtime_delta:
        print("[5b] 变异态确实写了运行时文件（= 隔离在承重的正证据）:")
        for line in mutated_runtime_delta.splitlines():
            print(f"      {line}")
    if runtime_removed:
        print(f"[5c] 已删除本脚本造成的新增运行时文件（跑前 absent）: {runtime_removed}")
    if conflict_note:
        print(f"NEGATIVE-CONTROL: FAIL — {conflict_note}")
        return 1
    if not restored_identical:
        print("NEGATIVE-CONTROL: FAIL — 源文件未能逐字节还原（这是事故，请人工检查 git diff）")
        return 1

    # -- 6. 裁定 --------------------------------------------------------------
    problems: list[str] = []
    if pytest_rc is None:
        problems.append("pytest 未运行")
    if pytest_rc != 1:
        problems.append(f"pytest 退出码 {pytest_rc} ≠ 1（期望恰为 tests-failed）")
    if isinstance(summary, tuple):
        s_total, s_blocked, s_advisory, s_unacct = summary
        if not (s_total == s_blocked > 0):
            problems.append(f"门账 total({s_total}) == blocked({s_blocked}) > 0 不成立")
        if s_advisory != 0:
            problems.append(f"advisory={s_advisory} ≠ 0（有连接以豁免名义真的发出去了）")
        if s_unacct != 0:
            problems.append(f"unaccounted={s_unacct} ≠ 0（有拦截无人结账）")
    else:
        problems.append(f"门汇总解析失败：{summary}")
    if ledger_problem:
        problems.append(ledger_problem)
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
    if not positive_runtime_ok:
        problems.append("正控（隔离态）动了运行时文件")
    if runtime_unresolved:
        problems.append(
            f"运行时文件跑前就存在且内容变了，本脚本**不覆盖**（可能混有并发写入），需人工核对: {runtime_unresolved}"
        )
    if not runtime_unchanged:
        problems.append("运行时现场未能复原到跑前状态")
    if not mutated_runtime_delta:
        problems.append(
            "变异态**没有**写任何运行时文件 —— 说明 lifespan 没跑到写路径就 abort 了，"
            "这条负门此刻在测别的东西（历史教训：LanceDB canonical/legacy 冲突会让它"
            "在到达 Neo4j 之前就退出）"
        )
    if n_violations:
        problems.append(f"AST 门 {n_violations} 处违规（见上方 VIOLATION 清单）")

    shutil.rmtree(tmp_root, ignore_errors=True)

    if problems:
        print("NEGATIVE-CONTROL: FAIL")
        for p in problems:
            print(f"  - {p}")
        # 门自己失败时必须把证据摊开——否则「负门红了」和「负门为什么红」之间
        # 隔着一次重跑，而重跑要再做一遍原地变异（MEMORY：门要能说出自己的理由）。
        print("--- 变异运行 child stdout tail ---")
        print(child_stdout[-4000:])
        if child_stderr.strip():
            print("--- 变异运行 child stderr tail ---")
            print(child_stderr[-2000:])
        return 1

    print(
        f"NEGATIVE-CONTROL: PASS ({len(reason_verified)} nodeids red for expected reason; "
        f"summary={summary}; positive control green with zero attempts and zero runtime writes; "
        f"mutated run did touch runtime files (isolation is load-bearing) and the scene was restored; "
        f"target restored byte-identical; AST-GATE: PASS 0/{n_files} files)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
