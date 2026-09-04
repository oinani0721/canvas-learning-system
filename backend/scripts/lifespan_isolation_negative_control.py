#!/usr/bin/env python
"""负门 —— 证明「lifespan 隔离 + socket 门 + 结账哨兵」这套防线真的在承重。

[BATCH-2026-09-01-第九批 / CARD-TEST-isolate-lifespan-R1]

方法：在 tmp 里建一份**只含 git tracked 文件**的 backend 副本，在**副本**的
``tests/api/v1/endpoints/test_metadata_subject_mapping.py`` 里把 ``no_lifespan``
摘掉，跑其中三条钉死的 nodeid。此时 client fixture 会重新触发 ``app.main`` 的
真实 lifespan，向 ``NEO4J_URI`` 指向的库发起连接。防线的行为应当是：

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
  orchestrator 的 durable journal 落在 ``app/data/`` 下（``state_dir`` 不给就取
  模块相对路径），重定向不了；文件名自 CARD-G2-5 起是 vault 命名空间下的
  ``vault_index_pending__<vault_key>.jsonl``，见 ``RUNTIME_FILE_GLOBS``。

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

* 只对**一个**代表文件做变异（在副本上），且只跑其中 **3 条钉死的 nodeid**（覆盖
  GET 成功 / POST 写 / 404 三种请求形态）——变异态每用例要完整跑一遍真实
  lifespan（被拦的连接各自带驱动级重试/超时），全 19 条 ≈ 35 分钟。它证明的是
  「防线 + lifespan 摘除」的组合在该形态上红得符合预期；不证明其余用例与其它
  12 个改造文件的个体变异也会红（fixture 形态相同，未逐一变异）。
* 只跑 pytest 主进程。防线不拦子进程（见 live_port_guard 模块 docstring），
  本脚本也不构造子进程连接场景。
* AST 门是**静态**分析：它证明的是「源码里没有裸 TestClient(app.main 的 app)」，
  不证明「运行时真的没连」。运行时证明由变异运行承担。
* AST 门**追不动容器与跨函数的实例传递**（2026-09-03 自查实测的已知盲区）：
  ``clients = [TestClient(app)]`` 之后 ``with clients[0]:``、以及把实例作为普通
  返回值/参数在函数间传递后再进 ``with``，都不会被抓。能追的三条是：绑到局部名字
  （``client = TestClient(app)`` → ``with client:``）、存到 ``self.<attr>``、
  以及**每条 return 都是 main 实例**的本模块工厂（``with make():``）。
  要覆盖容器需要元素级别名分析，本卡不做。
* 底层 socket / atexit / shell 注入等旁路由
  ``backend/scripts/lifespan_isolation_guard_probes.py`` 单独证明，不在本脚本内。

## 为什么不再原地变异（R1 Codex HIGH-6/HIGH-7 的结构性收口）

第八批到第九批 round-1 都是**原地**改真实文件再还原，于是要靠「写盘前置标志 +
finally 写回 + atexit/信号兜底 + 还原前 CAS」一整套纪律去追一个本来就不该发生的写。
Codex 指出两个洞：并发编辑会在 collect/正控期间落到目标文件上而 CAS 看不出来；
变异运行造出的运行时文件用「跑前 absent、跑后存在」判归属并 ``unlink``，可能删掉
别的进程刚写的真实数据。

现在改成在 tmp 副本上变异 —— **真实工作树的 tracked 文件与运行时文件全程一个字节
都不写**，上面那两条链条从源头消失，也就不需要 CAS 与还原纪律了。脚本仍会断言
「真实树 untouched」，把这句话变成每次运行都要过的门，而不是一句声明。
残余：副本是**复制那一刻**的快照，复制期间的并发编辑不在射程（脚本会比对副本与
工作树里目标文件的 sha，不一致即停）。
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
RUNTIME_FILE_RELPATHS = [
    "data/bug_log.jsonl",
    "data/outbox/events.jsonl",
]

#: ⛔ 不能写成固定文件名（2026-09-04 主干合并后当场抓到的假门）：CARD-G2-5
#: （第七批）把 orchestrator 的 durable journal 从 ``app/data/vault_index_pending.jsonl``
#: 改成了 vault 命名空间下的 ``vault_index_pending__<vault_key>.jsonl``
#: （``app/core/vault_state_paths.py::namespaced_state_path``），而且 vault_key 还会
#: 因 ``NAME_MAX`` 的**字节**预算被 hash 截断 —— 文件名根本不可预先硬编码。
#: 后果分两个方向，都很难看：
#:   * 本脚本这一侧：「变异态必须写至少一个运行时文件」的正证据锚点落空 → 负控
#:     报 FAIL（fail-closed，还算诚实）；
#:   * ``runtime_sha.sh`` 那一侧：断言的是 ``unchanged``，锚点落空直接变**假绿**。
#: 所以按 stem 前缀 glob，新旧两种文件名一并收（旧的固定名也匹配）。
#:
#: 覆盖面刻意与合并前**等价**：只跟随这一个 journal 的改名，不新增监视项。
#: 同族的 ``lancedb_pending_index__<key>.jsonl``（``lancedb_index_service.py:76``）
#: 合并前就不在清单里，本卡只登记移交，不在此扩面（扩面会让 runtime_sha 变严，
#: 属于另一张卡的范围决策）。
RUNTIME_FILE_GLOBS = [
    "app/data/vault_index_pending*.jsonl",
]


def runtime_files(backend_dir: Path) -> list[Path]:
    """固定项 + glob 项。

    ⚠️ glob **每次调用都重新展开** —— before 快照时文件还不存在、after 才被写出来
    正是本门要抓的情形；把展开结果缓存下来就等于抓不到新建文件。
    展开结果排序，避免文件系统顺序波动造成假 delta。
    """
    fixed = [backend_dir / rel for rel in RUNTIME_FILE_RELPATHS]
    globbed: list[Path] = []
    for pattern in RUNTIME_FILE_GLOBS:
        globbed.extend(backend_dir.glob(pattern))
    return fixed + sorted(globbed)


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

#: 会触发 ``__enter__`` 的方法名（``ExitStack`` / ``AsyncExitStack``）。
#: 走这条路进入的 TestClient 同样会跑真实 lifespan（R1 Codex HIGH-8）。
_ENTER_CONTEXT_ATTRS = {"enter_context", "enter_async_context"}

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
#: 由 app.main 的 app 构造出来的 TestClient **实例**（还没进 with，所以还没跑
#: lifespan；一旦进了 with / enter_context 就会跑）。R1 Codex HIGH-8。
#: 后面拼上**它包的那个 app 名**（`testclient:instance(app.main):app`）——
#: 检查「外层 with no_lifespan(X)」时要比对的是 X 而不是客户端变量名。
O_TESTCLIENT_INSTANCE_MAIN = "testclient:instance(app.main)"


def _instance_main(app_name: str | None) -> str:
    return f"{O_TESTCLIENT_INSTANCE_MAIN}:{app_name or '?'}"


def _instance_app_name(origin: str) -> str | None:
    """从实例来源里取回它包的 app 名；不是 main 实例则 None。"""
    if not origin.startswith(O_TESTCLIENT_INSTANCE_MAIN + ":"):
        return None
    name = origin[len(O_TESTCLIENT_INSTANCE_MAIN) + 1 :]
    return None if name == "?" else name


def _is_instance_main(origin: str) -> bool:
    return origin.startswith(O_TESTCLIENT_INSTANCE_MAIN)


#: 由局部 FastAPI() 构造出来的 TestClient 实例 —— 进 with 也无害。
O_TESTCLIENT_INSTANCE_LOCAL = "testclient:instance(local)"
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
        #: 「每一条 return 都返回 app.main 的 TestClient 实例」的函数（`类名.方法名`
        #: 或 `<module>.函数名`）—— `with make():` 会跑真实 lifespan（L2-d）。
        self.main_client_funcs: set[str] = set()
        #: `self.<attr> = TestClient(app.main 的 app)` —— 记 `类名.attr`，
        #: 让 `with self.<attr>:` 也能被抓（L2-b）。
        self.main_client_attrs: set[str] = set()
        #: 本模块里**自建的隔离包装器**：`<owner>.<name>` → 被隔离的那个形参下标。
        #: 形态必须窄到可证（见 :meth:`_mark_isolation_wrappers`）。
        self.isolation_wrappers: dict[str, int] = {}
        self.module_scope = _Scope(tree, None, "module")
        self.scope_of: dict[int, _Scope] = {}
        # 建表与「哪些函数返回局部 app」互为输入 —— 迭代到不动点，最后再建一次表，
        # 保证对外暴露的 scopes 反映的是**最终**知识（否则验伪锚 4 那种
        # `app, n = make()` 会被建表期的空知识判成 unknown）。
        for _ in range(4):
            self._rebuild(tree)
            before = (
                set(self.fastapi_returning_funcs),
                set(self.main_client_funcs),
                set(self.main_client_attrs),
                dict(self.isolation_wrappers),
            )
            self._mark_all_fastapi_returning(tree)
            self._mark_main_client_sources(tree)
            self._mark_isolation_wrappers(tree)
            if (
                self.fastapi_returning_funcs,
                self.main_client_funcs,
                self.main_client_attrs,
                self.isolation_wrappers,
            ) == before:
                break
        self._rebuild(tree)

    def _rebuild(self, tree: ast.Module) -> None:
        self.module_scope = _Scope(tree, None, "module")
        self.scope_of = {}
        # 父链：用来找「支配本 with 的外层 with」（R1 Codex MEDIUM-13）
        self.parents: dict[int, ast.AST] = {}
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                self.parents[id(child)] = node
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
                elif bound == "fastapi":
                    # `import fastapi` 与 `import fastapi.testclient` 绑定的都是
                    # **顶层 fastapi 模块**这同一个对象，来源相同。若这里只认前者，
                    # 两条 import 并存时「全部绑定必须一致」会把 fastapi 判成 unknown，
                    # 于是 `fastapi.testclient.TestClient(...)` 整条链解析失败（误报）。
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
            # TestClient(...) 的**实例**：记下它包的是哪种 app，供
            # `with client:` / `enter_context(client)` 追踪（R1 Codex HIGH-8）
            if self.is_testclient_call(value, stmt, scope):
                app_arg = self.testclient_app_arg(value)
                if app_arg is None:
                    return _instance_main(None)  # 无参/取不到 ⇒ fail-closed
                origin = self.resolve_arg(app_arg, stmt, scope)
                if origin == O_LOCAL_APP:
                    return O_TESTCLIENT_INSTANCE_LOCAL
                return _instance_main(app_arg.id if isinstance(app_arg, ast.Name) else None)
            # 本模块里「每一条 return 都返回 app.main 实例」的工厂：`with make():`
            # 同样会跑 lifespan（L2-d）。
            if self._is_main_client_factory_call(value.func, stmt, scope):
                return _instance_main(None)
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
            if f"<module>.{func.id}" not in self.fastapi_returning_funcs:
                return False
            # 名字此刻必须仍绑定到本模块那个 def（重绑定后不再算数）
            return self.resolve_name(func.id, _pos(node), scope) == f"{O_LOCAL_FUNC_PREFIX}{func.id}"
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            if func.value.id not in ("self", "cls"):
                return False
            # 按**调用点所在的那个类**限定（R1 Codex HIGH-11：同名方法跨类污染）
            owner = self._enclosing_class_name(node)
            return f"{owner}.{func.attr}" in self.fastapi_returning_funcs
        return False

    def _callable_origin(self, func: ast.expr, node: ast.AST, scope: _Scope) -> str:
        if isinstance(func, ast.Name):
            return self.resolve_name(func.id, _pos(node), scope)
        if isinstance(func, ast.Attribute):
            return self._attribute_origin(func, node, scope)
        return O_UNKNOWN

    def _attribute_origin(self, attr: ast.Attribute, node: ast.AST, scope: _Scope) -> str:
        """属性访问的来源。**递归**解析 base，从而支持完整属性链。

        R1 Codex MEDIUM-13：``fastapi.testclient.TestClient(...)`` 是
        ``Attribute(Attribute(Name('fastapi'), 'testclient'), 'TestClient')``，
        旧实现只认 base 是 ``Name`` 的一层，整条链解析不出来 → 误判。
        """
        base = attr.value
        # app.main.app（`import app.main` 之后绑定的是顶层包 `app`）
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
        elif isinstance(base, ast.Attribute):
            base_origin = self._attribute_origin(base, node, scope)
        else:
            return O_UNKNOWN
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
        """判定「本函数的**每一条**可达 return 都返回可证的局部 app」。

        R1 Codex HIGH-10 打回的旧判据是「**存在**一条 return 返回局部 app」，于是

            a = FastAPI()
            a = production_app
            return a

        被标成安全，调用方裸启生产 lifespan。现在改成：

        * 每一条 return 都在**它自己的位置**上按 :meth:`resolve_name` 解析
          （「全部先前绑定必须一致」的口径，见该方法），必须解析为 ``O_LOCAL_APP``；
        * 函数里**必须至少有一条** return（没有 return 的函数不算工厂）；
        * 任何一条不合格 ⇒ 整个函数不算工厂。
        """
        own = self.scope_of.get(id(fd.body[0])) if fd.body else None
        if own is None:
            return
        # 只看**本函数自己作用域**里的语句：嵌套函数的 return 归它自己，
        # 不能算到外层函数头上（否则 `def outer(): def inner(): return FastAPI()`
        # 会把 outer 误标成返回局部 app）。
        own_stmts = [s for s in ast.walk(fd) if self.scope_of.get(id(s)) is own]
        returns = [s for s in own_stmts if isinstance(s, ast.Return) and s.value is not None]
        if not returns:
            return
        for stmt in returns:
            candidates = stmt.value.elts if isinstance(stmt.value, ast.Tuple) else [stmt.value]
            if not any(self._value_origin(c, stmt, own) == O_LOCAL_APP for c in candidates):
                return  # 这条 return 拿不出可证的局部 app ⇒ 整个函数不算工厂
        key = self._factory_key(fd)
        self.fastapi_returning_funcs.add(key)

    def _mark_main_client_sources(self, tree: ast.Module) -> None:
        """收敛两类「会把 app.main 的 TestClient 实例递出来」的源。

        * ``main_client_funcs``：函数的**每一条** return 都解析为 main 实例
          （与 FastAPI 工厂同口径：存在一条安全的不算数，必须条条都是）；
        * ``main_client_attrs``：``self.<attr> = TestClient(<app.main 的 app>)``。

        ⚠️ **不覆盖容器**：``clients = [TestClient(app)]`` 之后 ``with clients[0]:``
        静态上追不动（要做容器元素级别的别名分析），如实登记为已知盲区，
        见模块 docstring「这道负门不比什么」。
        """
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                own = self.scope_of.get(id(node.body[0])) if node.body else None
                if own is None:
                    continue
                own_stmts = [s for s in ast.walk(node) if self.scope_of.get(id(s)) is own]
                returns = [s for s in own_stmts if isinstance(s, ast.Return) and s.value is not None]
                if returns and all(_is_instance_main(self._value_origin(r.value, r, own)) for r in returns):
                    self.main_client_funcs.add(self._factory_key(node))
            elif isinstance(node, (ast.Assign, ast.AnnAssign)) and getattr(node, "value", None) is not None:
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                attrs = [
                    tgt
                    for tgt in targets
                    if isinstance(tgt, ast.Attribute) and isinstance(tgt.value, ast.Name) and tgt.value.id == "self"
                ]
                if not attrs:
                    continue
                scope = self.scope_for(node)
                if _is_instance_main(self._value_origin(node.value, node, scope)):
                    owner = self._enclosing_class_name(node)
                    for tgt in attrs:
                        self.main_client_attrs.add(f"{owner}.{tgt.attr}")

    def _mark_isolation_wrappers(self, tree: ast.Module) -> None:
        """识别**自建的隔离包装器**，避免把合法写法误判成违规。

        ``@contextlib.contextmanager`` 包一层 ``no_lifespan`` 是很自然的写法::

            @contextlib.contextmanager
            def isolated(a):
                with no_lifespan(a):
                    yield a

            with isolated(app), TestClient(app) as c: ...

        这段是**安全**的，但按「helper 必须直接 import 自 tests.support.lifespan」
        的口径会被判违规（实测确认，属 R1 Codex 归类的「误判为违规 = MEDIUM」）。

        识别条件收得很窄，三条**全部**满足才算：

        1. 函数体里有一个 ``with``，其某个 item 解析为 :data:`O_HELPER`
           （真的是 import 来的 ``no_lifespan``/``lifespan_lite``）；
        2. 该 helper 调用的实参是本函数**自己的某个位置形参**；
        3. 那个 ``with`` 的**体内**有 ``yield`` —— 即隔离确实覆盖了让出控制权的
           那一刻。只在 with 外面 yield 的包装器不算数（隔离没盖住调用方的代码）。

        记下被隔离的**形参下标**，调用点按同一下标的实参名比对；换个参数传就不算。
        """
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            own = self.scope_of.get(id(node.body[0])) if node.body else None
            if own is None:
                continue
            params = [a.arg for a in (node.args.posonlyargs + node.args.args)]
            if not params:
                continue
            for stmt in ast.walk(node):
                if not isinstance(stmt, (ast.With, ast.AsyncWith)):
                    continue
                if self.scope_of.get(id(stmt)) is not own:
                    continue
                has_yield = any(isinstance(x, (ast.Yield, ast.YieldFrom)) for b in stmt.body for x in ast.walk(b))
                if not has_yield:
                    continue
                for item in stmt.items:
                    ctx = item.context_expr
                    if not isinstance(ctx, ast.Call):
                        continue
                    if self._callable_origin(ctx.func, stmt, own) != O_HELPER:
                        continue
                    if ctx.args and isinstance(ctx.args[0], ast.Name) and ctx.args[0].id in params:
                        self.isolation_wrappers[self._factory_key(node)] = params.index(ctx.args[0].id)

    def isolation_wrapper_param(self, func: ast.expr, node: ast.AST, scope: _Scope) -> int | None:
        """这次调用是不是自建隔离包装器；是则返回被隔离的形参下标。"""
        if isinstance(func, ast.Name):
            key = f"<module>.{func.id}"
            if key not in self.isolation_wrappers:
                return None
            if self.resolve_name(func.id, _pos(node), scope) != f"{O_LOCAL_FUNC_PREFIX}{func.id}":
                return None
            return self.isolation_wrappers[key]
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name) and func.value.id in ("self", "cls"):
            return self.isolation_wrappers.get(f"{self._enclosing_class_name(node)}.{func.attr}")
        return None

    def _is_main_client_factory_call(self, func: ast.expr, node: ast.AST, scope: _Scope) -> bool:
        """调用形态与 :meth:`_is_local_app_factory_call` 同口径，只是查另一张表。"""
        if isinstance(func, ast.Name):
            if f"<module>.{func.id}" not in self.main_client_funcs:
                return False
            return self.resolve_name(func.id, _pos(node), scope) == f"{O_LOCAL_FUNC_PREFIX}{func.id}"
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            if func.value.id not in ("self", "cls"):
                return False
            return f"{self._enclosing_class_name(node)}.{func.attr}" in self.main_client_funcs
        return False

    def is_main_client_attr(self, expr: ast.expr, node: ast.AST) -> bool:
        """``self.<attr>`` 是否是本类里存下来的 app.main TestClient 实例。"""
        if not (isinstance(expr, ast.Attribute) and isinstance(expr.value, ast.Name)):
            return False
        if expr.value.id not in ("self", "cls"):
            return False
        return f"{self._enclosing_class_name(node)}.{expr.attr}" in self.main_client_attrs

    def _factory_key(self, fd) -> str:
        """工厂身份 = 「(类名或 <module>) . 方法名」。

        R1 Codex HIGH-11：旧实现只按**方法名**记，于是 A 类的 ``make`` 返回局部 app
        会让 B 类同名、返回生产 app 的 ``make`` 也被判安全。按类限定之后，
        ``self.make()`` 只能命中**它自己那个类**里的定义。
        """
        enclosing = self.scope_of.get(id(fd))
        while enclosing is not None and enclosing.kind != "class":
            enclosing = enclosing.parent
        owner = getattr(enclosing.node, "name", "<anon>") if enclosing is not None else "<module>"
        return f"{owner}.{fd.name}"

    def _enclosing_class_name(self, node: ast.AST) -> str:
        scope = self.scope_of.get(id(node))
        while scope is not None and scope.kind != "class":
            scope = scope.parent
        return getattr(scope.node, "name", "<anon>") if scope is not None else "<module>"

    # ── TestClient 识别 ─────────────────────────────────────────────────
    def is_testclient_call(self, call: ast.expr, node: ast.AST, scope: _Scope) -> bool:
        """这次调用是不是在构造 TestClient。

        两条路，取并集（检测面要宽，判定面才敢严）：
          * **词法**叫 ``TestClient``（哪怕被本地遮蔽——那种情况另有一条违规）；
          * **解析**到真正 import 自 fastapi/starlette 的 TestClient 类
            （覆盖 ``as TC`` 别名与 ``fastapi.testclient.TestClient`` 全链）。
        """
        if not isinstance(call, ast.Call):
            return False
        return _syntactic_call_name(call) == "TestClient" or self._callable_origin(call.func, node, scope) == (
            O_TESTCLIENT_CLASS
        )

    @staticmethod
    def testclient_app_arg(call: ast.Call) -> ast.expr | None:
        """取 TestClient(...) 的 app 实参：第一个位置参数，或 ``app=`` 关键字。

        R1 Codex MEDIUM-13：只看位置参数会漏掉 ``TestClient(app=app)``。
        """
        if call.args:
            return call.args[0]
        for kw in call.keywords:
            if kw.arg == "app":
                return kw.value
        return None

    # ── 解析 ────────────────────────────────────────────────────────────
    def scope_for(self, node: ast.AST) -> _Scope:
        """节点所属作用域。

        ``scope_of`` 只对**语句**建了索引，所以表达式节点（比如
        ``stack.enter_context(client)`` 这个 Call）要沿父链往上找到它所在的语句。
        直接 fallback 到 module_scope 会让函数内的局部名字整片解析不出来。
        """
        cur: ast.AST | None = node
        while cur is not None:
            scope = self.scope_of.get(id(cur))
            if scope is not None:
                return scope
            cur = self.parents.get(id(cur))
        return self.module_scope

    def parent_of(self, node: ast.AST) -> ast.AST | None:
        return self.parents.get(id(node))

    def resolve_name(self, name: str, pos: tuple[int, int], scope: _Scope) -> str:
        """在 ``scope`` 处、位置 ``pos`` 上，名字 ``name`` 的来源。

        判据（R1 Codex HIGH-9 整改后）：**所有**位于 ``pos`` 之前的绑定必须来源
        一致，才给出那个来源；有任何分歧一律 unknown（= 违规，fail-closed）。

        为什么不能只取「最后一次绑定」：那是**词法**上的最后一次，不是**控制流**
        上的。Codex 的反例——

            app = production_app
            if use_local:
                app = FastAPI()
            with TestClient(app): ...

        ——「最后一次绑定」是 ``FastAPI()``，于是判安全；而 ``use_local`` 为假时
        跑的是生产 app 的真实 lifespan。做完整的 reaching-definition 需要 CFG；
        这里用「全部先前绑定必须一致」这个**更保守**的近似：它对上面这种分支写法
        必然判 unknown，代价是「先赋 A 后无条件覆盖成 B」的写法也会被判 unknown
        （本仓库 371 个文件实测 0 例，见 AST 门输出）。

        * **本作用域**：只看 ``pos`` 之前的绑定；一个都没有 ⇒ unknown。
        * **外层作用域**：函数调用时刻不确定，要求该名字在外层的**全部**绑定一致。
        * 类作用域对内层函数不可见（Python 语义），查找链跳过它。
        """
        cur: _Scope | None = scope
        first = True
        while cur is not None:
            skip = (not first) and cur.kind == "class"
            if not skip and name in cur.bindings:
                bindings = cur.sorted_bindings(name)
                if first:
                    origins = {o for p, o in bindings if p < pos}
                    if not origins:
                        return O_UNKNOWN
                else:
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


def _item_isolates(index: "_ModuleIndex", ctx, host_node, scope, app_name: str) -> bool:
    """一个 ``with`` item 是否对名为 ``app_name`` 的 app 施加了隔离。

    两条路：直接调 import 来的 ``no_lifespan``/``lifespan_lite``；
    或调本模块**自建的隔离包装器**（窄定义见 `_mark_isolation_wrappers`），
    此时比对的是**被隔离的那个形参下标**上的实参。
    """
    if not isinstance(ctx, ast.Call):
        return False
    if index._callable_origin(ctx.func, host_node, scope) == O_HELPER:
        return bool(ctx.args) and isinstance(ctx.args[0], ast.Name) and ctx.args[0].id == app_name
    idx = index.isolation_wrapper_param(ctx.func, host_node, scope)
    if idx is None or idx >= len(ctx.args):
        return False
    arg = ctx.args[idx]
    return isinstance(arg, ast.Name) and arg.id == app_name


def _isolation_sibling_covers(index: "_ModuleIndex", with_node, upto_pos: int, app_arg, scope) -> bool:
    """同一个 ``with`` 语句里，位置**在前**的兄弟项是否对同一个 app 做了隔离。"""
    if not isinstance(app_arg, ast.Name):
        return False
    for hpos, hitem in enumerate(with_node.items):
        if hpos >= upto_pos:
            break
        if _item_isolates(index, hitem.context_expr, with_node, scope, app_arg.id):
            return True
    return False


def _isolation_enclosing_covers_name(index: "_ModuleIndex", node, app_name: str) -> bool:
    """按**名字**找支配本节点的外层 ``with no_lifespan(<app_name>):``。"""
    cur = index.parent_of(node)
    while cur is not None:
        if isinstance(cur, (ast.With, ast.AsyncWith)):
            scope = index.scope_for(cur)
            for hitem in cur.items:
                if _item_isolates(index, hitem.context_expr, cur, scope, app_name):
                    return True
        cur = index.parent_of(cur)
    return False


def _isolation_enclosing_covers(index: "_ModuleIndex", node, app_arg) -> bool:
    """**外层**的 ``with no_lifespan(app):`` 是否支配本节点（R1 Codex MEDIUM-13）。

    外层隔离块内的一切都在 no-op lifespan 生效期间执行，真实 startup 不会跑，
    所以那是安全写法，旧实现却报违规。这里沿父链往上找 With，逐个看它是不是对
    **同一个名字**做了隔离。
    """
    if not isinstance(app_arg, ast.Name):
        return False
    return _isolation_enclosing_covers_name(index, node, app_arg.id)


def _describe(expr) -> str:
    if isinstance(expr, ast.Name):
        return expr.id
    if isinstance(expr, ast.Attribute):
        return f"<...>.{expr.attr}"
    return "<expr>"


def _flag_instance_context(violations, index, rel, node, scope, expr, how: str) -> None:
    """判定「把一个已构造好的 TestClient 实例送进 ``__enter__``」是否合规。

    覆盖 ``with client:``、``with self.client:``、``enter_context(client)``。
    关键修正（我自己在 round-2 自查时抓到的）：外层隔离要比对的是**这个实例包着的
    那个 app 名**，不是客户端变量名 —— 之前拿 ``client`` 去找 ``no_lifespan(client)``，
    于是合法的 `with no_lifespan(app): with client:` 被误报。
    """
    origin = None
    desc = _describe(expr)
    if isinstance(expr, ast.Name):
        origin = index.resolve_name(expr.id, _pos(node), scope)
    elif index.is_main_client_attr(expr, node):
        origin = _instance_main(None)
    elif isinstance(expr, ast.Call) and index._is_main_client_factory_call(expr.func, node, scope):
        # `with make():` —— 工厂的每一条 return 都是 app.main 实例（L2-d）
        origin = _instance_main(None)
        desc = f"{_describe(expr.func)}()"
    if origin is None or not _is_instance_main(origin):
        return
    app_name = _instance_app_name(origin)
    if app_name is not None and _isolation_enclosing_covers_name(index, node, app_name):
        return
    hint = f"（它包的是 {app_name}）" if app_name else "（包的 app 名静态不可知，fail-closed）"
    violations.append(
        f"{rel}:{node.lineno}: {how} {desc} —— 它是用 app.main 的 app 构造的 TestClient 实例，"
        f"进入上下文会跑真实 lifespan{hint}；构造点没有隔离，本处也没有支配的外层隔离块"
    )


def analyze_source(source: str, rel: str) -> list[str]:
    """对一份源码跑 AST 门，返回违规明细（空 = 合规）。

    三类被检面（R1 Codex HIGH-8 之后）：

    1. ``with TestClient(<app>) ...`` —— 直接进 with 的构造；
    2. ``client = TestClient(<app>)`` 之后 ``with client:`` —— 实例被追踪进 with；
    3. ``stack.enter_context(TestClient(<app>))`` / ``enter_context(client)``
       —— ExitStack 同样会触发 ``__enter__``。

    ⚠️ **不带 with 的裸 ``TestClient(app)`` 不算违规**：Starlette 只在
    ``__enter__`` 里跑 lifespan，构造本身没有启动副作用（本仓库 7 个文件用这种
    写法，全部无害）。
    """
    violations: list[str] = []
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return [f"{rel}: SyntaxError {e}"]
    index = _ModuleIndex(tree)

    def flag_client_construction(call, node, scope, pos_in_with=None, with_node=None, how=""):
        """判定一次「会触发 lifespan 的 TestClient 构造」是否合规。"""
        app_arg = index.testclient_app_arg(call)
        if app_arg is None:
            violations.append(f"{rel}:{node.lineno}: TestClient() 取不到 app 实参 —— 人工复核{how}")
            return
        origin = index.resolve_arg(app_arg, node, scope)
        if origin == O_LOCAL_APP:
            return
        desc = _describe(app_arg)
        if origin != O_MAIN_APP:
            violations.append(
                f"{rel}:{node.lineno}: TestClient({desc}) —— app 来源无法静态证明"
                f"（解析结果={origin}，按违规处理，人工复核）{how}"
            )
            return
        covered = with_node is not None and _isolation_sibling_covers(index, with_node, pos_in_with, app_arg, scope)
        if not covered:
            covered = _isolation_enclosing_covers(index, node, app_arg)
        if not covered:
            violations.append(
                f"{rel}:{node.lineno}: TestClient({desc}) —— app 来自 app.main 且没有"
                "生效中的 no_lifespan/lifespan_lite（同 with 语句里排在前面的兄弟项，"
                f"或支配本处的外层 with 块）{how}"
            )

    for node in ast.walk(tree):
        scope = index.scope_for(node)

        # ── 面 1/2：with 语句 ────────────────────────────────────────────
        if isinstance(node, (ast.With, ast.AsyncWith)):
            for pos_i, item in enumerate(node.items):
                ctx = item.context_expr
                # 1) with TestClient(...)
                if isinstance(ctx, ast.Call):
                    syn = _syntactic_call_name(ctx)
                    callee_origin = index._callable_origin(ctx.func, node, scope)
                    if syn == "TestClient" and callee_origin != O_TESTCLIENT_CLASS:
                        violations.append(
                            f"{rel}:{node.lineno}: with TestClient(...) —— TestClient 这个名字"
                            f"解析不到 {sorted(TESTCLIENT_MODULES)} 的真实 import"
                            f"（当前来源={callee_origin}），无法证明它是被隔离约束覆盖的那个 TestClient"
                        )
                        continue
                    if index.is_testclient_call(ctx, node, scope):
                        flag_client_construction(ctx, node, scope, pos_in_with=pos_i, with_node=node)
                    else:
                        # `with make():` —— 返回 app.main 实例的工厂调用（L2-d）
                        _flag_instance_context(violations, index, rel, node, scope, ctx, "with")
                    continue
                # 2) with client: / with self.client:（先前构造的 TestClient 实例）
                _flag_instance_context(violations, index, rel, node, scope, ctx, "with")
            continue

        # ── 面 3：ExitStack.enter_context(...) ──────────────────────────
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in _ENTER_CONTEXT_ATTRS
        ):
            if not node.args:
                continue
            target = node.args[0]
            stmt = node
            if isinstance(target, ast.Call) and index.is_testclient_call(target, stmt, scope):
                flag_client_construction(target, node, scope, how="（经 enter_context）")
            else:
                _flag_instance_context(violations, index, rel, node, scope, target, node.func.attr)
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
        "R1-8a：client = TestClient(app) 之后 with client:",
        "from app.main import app\n"
        "from fastapi.testclient import TestClient\n"
        "def t():\n"
        "    client = TestClient(app)\n"
        "    with client:\n"
        "        pass\n",
    ),
    (
        "R1-8b：ExitStack.enter_context(TestClient(app))",
        "import contextlib\n"
        "from app.main import app\n"
        "from fastapi.testclient import TestClient\n"
        "def t():\n"
        "    with contextlib.ExitStack() as stack:\n"
        "        c = stack.enter_context(TestClient(app))\n",
    ),
    (
        "R1-8c：enter_context(先前构造的实例)",
        "import contextlib\n"
        "from app.main import app\n"
        "from fastapi.testclient import TestClient\n"
        "def t():\n"
        "    client = TestClient(app)\n"
        "    stack = contextlib.ExitStack()\n"
        "    stack.enter_context(client)\n",
    ),
    (
        "R1-9：分支里才赋局部 app（控制流不是词法顺序）",
        "from app.main import app as production_app\n"
        "from fastapi import FastAPI\n"
        "from fastapi.testclient import TestClient\n"
        "def t(use_local):\n"
        "    app = production_app\n"
        "    if use_local:\n"
        "        app = FastAPI()\n"
        "    with TestClient(app) as c:\n"
        "        pass\n",
    ),
    (
        "R1-10：工厂里 a=FastAPI() 之后被覆盖成生产 app",
        "from app.main import app as production_app\n"
        "from fastapi import FastAPI\n"
        "from fastapi.testclient import TestClient\n"
        "def make():\n"
        "    a = FastAPI()\n"
        "    a = production_app\n"
        "    return a\n"
        "def t():\n"
        "    app = make()\n"
        "    with TestClient(app) as c:\n"
        "        pass\n",
    ),
    (
        "R1-11：同名方法跨类污染（A.make 安全不代表 B.make 安全）",
        "from app.main import app as production_app\n"
        "from fastapi import FastAPI\n"
        "from fastapi.testclient import TestClient\n"
        "class A:\n"
        "    def make(self):\n"
        "        a = FastAPI()\n"
        "        return a\n"
        "class B:\n"
        "    def make(self):\n"
        "        return production_app\n"
        "    def test_x(self):\n"
        "        app = self.make()\n"
        "        with TestClient(app) as c:\n"
        "            pass\n",
    ),
    (
        "R1-13c：TestClient(app=...) 关键字形态",
        "from app.main import app\n"
        "from fastapi.testclient import TestClient\n"
        "def t():\n"
        "    with TestClient(app=app) as c:\n"
        "        pass\n",
    ),
    (
        "L2-b：TestClient 实例存进 self 再在别处 with",
        "from app.main import app\n"
        "from fastapi.testclient import TestClient\n"
        "class T:\n"
        "    def setup(self):\n"
        "        self.c = TestClient(app)\n"
        "    def test_x(self):\n"
        "        with self.c:\n"
        "            pass\n",
    ),
    (
        "L2-d：工厂函数返回 TestClient(app) 后直接 with make()",
        "from app.main import app\n"
        "from fastapi.testclient import TestClient\n"
        "def make():\n"
        "    return TestClient(app)\n"
        "def t():\n"
        "    with make():\n"
        "        pass\n",
    ),
    (
        "L1-c：包装器没有真的调 no_lifespan",
        "import contextlib\n"
        "from app.main import app\n"
        "from fastapi.testclient import TestClient\n"
        "@contextlib.contextmanager\n"
        "def isolated(a):\n"
        "    yield a\n"
        "def t():\n"
        "    with isolated(app), TestClient(app) as c:\n"
        "        pass\n",
    ),
    (
        "L1-d：包装器在 with 之外 yield（隔离没盖住让出控制权那一刻）",
        "import contextlib\n"
        "from app.main import app\n"
        "from fastapi.testclient import TestClient\n"
        "from tests.support.lifespan import no_lifespan\n"
        "@contextlib.contextmanager\n"
        "def isolated(a):\n"
        "    with no_lifespan(a):\n"
        "        pass\n"
        "    yield a\n"
        "def t():\n"
        "    with isolated(app), TestClient(app) as c:\n"
        "        pass\n",
    ),
    (
        "L1-e：包装器隔离的是**另一个**形参",
        "import contextlib\n"
        "from app.main import app\n"
        "from fastapi import FastAPI\n"
        "from fastapi.testclient import TestClient\n"
        "from tests.support.lifespan import no_lifespan\n"
        "@contextlib.contextmanager\n"
        "def isolated(other, a):\n"
        "    with no_lifespan(other):\n"
        "        yield a\n"
        "def t():\n"
        "    spare = FastAPI()\n"
        "    with isolated(spare, app), TestClient(app) as c:\n"
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
        "验伪锚 6：外层 with no_lifespan(app) 支配内层 with TestClient(app)",
        "from app.main import app\n"
        "from fastapi.testclient import TestClient\n"
        "from tests.support.lifespan import no_lifespan\n"
        "def t():\n"
        "    with no_lifespan(app):\n"
        "        with TestClient(app) as c:\n"
        "            pass\n",
    ),
    (
        "验伪锚 7：完整属性链 fastapi.testclient.TestClient + 局部 app",
        "import fastapi\n"
        "import fastapi.testclient\n"
        "from fastapi import FastAPI\n"
        "def t():\n"
        "    app = FastAPI()\n"
        "    with fastapi.testclient.TestClient(app) as c:\n"
        "        pass\n",
    ),
    (
        "验伪锚 8：裸 TestClient(app) 不进 with —— 不跑 lifespan，不算违规",
        "from app.main import app\n"
        "from fastapi.testclient import TestClient\n"
        "def t():\n"
        "    client = TestClient(app)\n"
        "    return client.get('/x')\n",
    ),
    (
        "验伪锚 9：局部 app 构造的实例进 with —— 无害",
        "from fastapi import FastAPI\n"
        "from fastapi.testclient import TestClient\n"
        "def t():\n"
        "    app = FastAPI()\n"
        "    client = TestClient(app)\n"
        "    with client:\n"
        "        pass\n",
    ),
    (
        "验伪锚 10：自建 contextmanager 包 no_lifespan（合法，不该报）",
        "import contextlib\n"
        "from app.main import app\n"
        "from fastapi.testclient import TestClient\n"
        "from tests.support.lifespan import no_lifespan\n"
        "@contextlib.contextmanager\n"
        "def isolated(a):\n"
        "    with no_lifespan(a):\n"
        "        yield a\n"
        "def t():\n"
        "    with isolated(app), TestClient(app) as c:\n"
        "        pass\n",
    ),
    (
        "验伪锚 11：外层 no_lifespan(app) 支配 with client:（合法，不该报）",
        "from app.main import app\n"
        "from fastapi.testclient import TestClient\n"
        "from tests.support.lifespan import no_lifespan\n"
        "def t():\n"
        "    client = TestClient(app)\n"
        "    with no_lifespan(app):\n"
        "        with client:\n"
        "            pass\n",
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


def _child_env(vault_tmp: Path, lance_tmp: Path, ledger: Path | None, backend_dir: Path) -> dict[str, str]:
    """构造子进程环境：清 Neo4j 面 → 钉死受拦目标 → 关豁免 → 隔离写路径。

    ``backend_dir`` 是子进程的 backend 根（负控里恒为**隔离副本**），
    ``PYTHONPATH`` 必须指向它，否则 ``-p tests.support.guard_plugin`` 会加载到
    真实树里的那一份，验的就不是副本的代码了。
    """
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
    # ⚠️ 只放隔离副本，**不**追加调用者原有的 PYTHONPATH：否则真实树可能排在前面，
    # 子进程会去 import 真实树的 tests.support.*，验的就不是副本了。
    env["PYTHONPATH"] = str(backend_dir)
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


def make_isolated_backend(tmp_root: Path) -> Path:
    """把当前工作树的 ``backend/`` 复制一份到 tmp，变异只在副本上做。

    R1 Codex HIGH-6/HIGH-7 的结构性收口：

    * **HIGH-7（变异前无 CAS）**：真实的 tracked 测试文件从头到尾**一个字节都不
      被写**，所以「读原文 → 期间别人编辑 → 用旧变异体覆盖」这条链根本不存在，
      不需要靠 CAS 去追一个本来就不该发生的写。
    * **HIGH-6（`absent → exists` 就 unlink 可能删掉别人的数据）**：变异运行产生的
      运行时文件（orchestrator 的 journal 只落在 ``app/data/`` 下，重定向不了）
      落在**副本**里，随 tmp 目录一起消失；真实树下的同名文件本脚本**永远不删**。

    **只复制 git tracked 的文件**（内容取自工作树，所以未提交的改动照样进副本 ——
    负控要验的就是此刻这份代码）。这一条不是为了省空间，是为了不把数据带出去：
    ``backend/data/`` 下有 ``llm_call_logs.db`` / ``neo4j_memory.json`` /
    ``learning_memories.json`` 这类**运行时数据**，它们全是 git-ignored 的，
    整目录 ``copytree`` 会把它们原样搬进 ``/tmp``（2026-09-03 实测搬了 12 个文件，
    含一个 36KB 的 sqlite）。tracked-only 的复制把这一面直接消掉。

    ``.env`` 是 git-ignored 但副本必须能读到它（``Settings`` 依赖），所以用**软链**
    而不是拷贝 —— 凭据一个字节都不落到 tmp。
    """
    iso = tmp_root / "iso-backend"
    iso.mkdir(parents=True)
    listing = subprocess.run(
        ["git", "ls-files", "-z", "--", "."],
        cwd=BACKEND_DIR,
        capture_output=True,
        check=True,
        timeout=120,
    )
    names = [n for n in listing.stdout.decode("utf-8").split("\0") if n]
    if len(names) < 500:
        raise RuntimeError(f"git ls-files 只列出 {len(names)} 个文件，副本会不完整，拒绝继续")
    for name in names:
        src = BACKEND_DIR / name
        if not src.exists():  # 已删除但还在 index 里
            continue
        dst = iso / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst, follow_symlinks=False)
    real_env = BACKEND_DIR / ".env"
    if real_env.exists():
        (iso / ".env").symlink_to(real_env)
    # 副本里不应有任何运行时残留（tracked-only 复制本来就不会带，这里做个断言式清理）
    for p in runtime_files(iso):
        if p.exists():
            p.unlink()
    return iso


def sha_of(path: Path) -> str:
    if not path.exists():
        return "absent"
    return hashlib.sha256(path.read_bytes()).hexdigest()


def runtime_snapshot(root: Path) -> str:
    """``root`` 下受监视运行时文件的 "<sha|absent>  <path>" 快照。

    ⛔ 必须传 root 并**在每次快照时重新展开 glob**：模块级缓存一份 Path 列表会让
    「跑完之后新出现的 journal」永远进不了 after 快照 —— 那正是本门要抓的东西。
    """
    return "\n".join(f"{sha_of(p)}  {p}" for p in runtime_files(root))


def _parse_junit(path: Path, target_rel: str) -> list[tuple[str, dict]]:
    """junitxml → ``[(nodeid, {"outcome": ..., "text": ...}), ...]``，**保留重复项**。

    刻意返回列表而不是 dict：同一个 nodeid 可能出现多次（参数化、重复传参、
    插件重跑），dict 会把它们悄悄合并成一条，于是「三条各跑一次」这句判据就变成了
    「三个不同的名字出现过」——数量对不上也看不出来。
    """
    module_dotted = target_rel[:-3].replace("/", ".")
    out: list[tuple[str, dict]] = []
    for case in ET.parse(path).getroot().iter("testcase"):
        classname = case.get("classname", "")
        name = case.get("name", "")
        if classname.startswith(module_dotted):
            chain = classname[len(module_dotted) :].lstrip(".")
            nid = f"{target_rel}::" + (f"{chain.replace('.', '::')}::{name}" if chain else name)
        else:
            nid = f"{classname.replace('.', '/')}::{name}"
        failure = case.find("failure")
        error = case.find("error")
        skipped = case.find("skipped")
        node = failure if failure is not None else (error if error is not None else None)
        if node is not None:
            outcome = "failed" if failure is not None else "error"
            text = " ".join(filter(None, [(node.get("message") or ""), (node.text or "")]))
        elif skipped is not None:
            outcome, text = "skipped", (skipped.get("message") or "")
        else:
            outcome, text = "passed", ""
        out.append((nid, {"outcome": outcome, "text": text}))
    return out


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

    # -- 0b. AST 门（裁判 6）------------------------------------------------
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
    cleaned = False

    def _cleanup(*_a) -> None:
        nonlocal cleaned
        if cleaned:
            return
        cleaned = True
        shutil.rmtree(tmp_root, ignore_errors=True)

    atexit.register(_cleanup)
    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP, signal.SIGQUIT):
        signal.signal(sig, lambda *_: (_cleanup(), sys.exit(130)))

    vault_tmp = tmp_root / "vault"
    lance_tmp = tmp_root / "lancedb"
    vault_tmp.mkdir()
    lance_tmp.mkdir()
    pos_junit = tmp_root / "positive-junit.xml"
    neg_junit = tmp_root / "negctl-junit.xml"
    pos_ledger = tmp_root / "ledger-positive.json"
    neg_ledger = tmp_root / "ledger-negative.json"

    # -- 0c. 隔离副本：变异只在这里做，真实 tracked 文件一个字节都不写 --------
    iso = make_isolated_backend(tmp_root)
    iso_target = iso / TARGET_REL
    print(f"[0b] 隔离副本: {iso}")

    # 真实树的运行时文件在整个脚本期间必须纹丝不动（本脚本从不写、也从不删它们）
    real_before = runtime_snapshot(BACKEND_DIR)

    # -- 0d. 前置：逐项精确核对**应用侧解析出来的**隔离环境 -------------------
    preflight_env = _child_env(vault_tmp, lance_tmp, None, iso)
    preflight = subprocess.run(
        [
            sys.executable,
            "-c",
            "import json, os, sys;"
            "sys.path.insert(0, 'lib');"
            "from app.config import get_settings;"
            "from agentic_rag.config import _resolve_lancedb_db_path;"
            "s = get_settings();"
            "print('W4_PREFLIGHT=' + json.dumps({"
            "'neo4j_uri': s.NEO4J_URI,"
            "'neo4j_user': getattr(s, 'NEO4J_USER', None),"
            "'neo4j_password': getattr(s, 'NEO4J_PASSWORD', None),"
            "'canvas_base_path': str(s.canvas_base_path),"
            "'lancedb_resolved': _resolve_lancedb_db_path(),"
            "'lancedb_data_path_env': os.environ.get('LANCEDB_DATA_PATH'),"
            "'lancedb_path_env': os.environ.get('LANCEDB_PATH'),"
            "}))",
        ],
        cwd=iso,
        env=preflight_env,
        capture_output=True,
        text=True,
        timeout=180,
    )
    resolved: dict = {}
    for line in preflight.stdout.splitlines():
        if line.startswith("W4_PREFLIGHT="):
            resolved = json.loads(line.split("=", 1)[1])
    print(f"[0c] Settings 解析（rc={preflight.returncode}）: {json.dumps(resolved, ensure_ascii=False)}")
    # R1 Codex MEDIUM-15：旧版只精确核对 NEO4J_URI，LanceDB 只要求非空、
    # canvas 路径完全不查 —— 解析漂移到现网 LanceDB 或真实 vault 时前置检查照样通过。
    expected_preflight = {
        "neo4j_uri": PINNED_NEO4J_URI,
        "neo4j_user": PINNED_NEO4J_USER,
        "neo4j_password": PINNED_NEO4J_PASSWORD,
        "canvas_base_path": str(vault_tmp),
        "lancedb_resolved": str(lance_tmp),
        "lancedb_data_path_env": str(lance_tmp),
        "lancedb_path_env": str(lance_tmp),
    }
    mismatch = {k: (v, resolved.get(k)) for k, v in expected_preflight.items() if resolved.get(k) != v}
    if preflight.returncode != 0 or mismatch:
        print("NEGATIVE-CONTROL: FAIL — 应用侧解析出的隔离环境与钉死值不符（期望, 实得）:")
        for k, (want, got) in mismatch.items():
            print(f"    {k}: {want!r} != {got!r}")
        print("--- preflight stdout tail ---")
        print(preflight.stdout[-1200:])
        print("--- preflight stderr tail ---")
        print(preflight.stderr[-1200:])
        return 1

    original = iso_target.read_bytes()
    original_sha = hashlib.sha256(original).hexdigest()
    mutated_bytes = original.decode("utf-8").replace(ANCHOR, MUTATED).encode("utf-8")

    # 副本内容必须与真实工作树逐字节一致，否则本门验的不是这份代码
    if hashlib.sha256(TARGET.read_bytes()).hexdigest() != original_sha:
        print("NEGATIVE-CONTROL: FAIL — 隔离副本里的目标文件与工作树不一致（复制期间被改？）")
        return 1

    pytest_rc: int | None = None
    total = 0
    green: list[str] = []
    red_nodeids: set[str] = set()
    red_for_wrong_reason: list[str] = []
    reason_verified: set[str] = set()
    expected_nodeids: set[str] = set()
    summary: tuple[int, int, int, int] | str = "未运行"
    ledger_problem: str | None = None
    child_stdout = ""
    child_stderr = ""
    iso_runtime_before = runtime_snapshot(iso)
    positive_runtime_ok = False
    mutated_runtime_delta = ""

    # -- 1. 预采集 nodeid（变异前）：必须与钉死的完整 nodeid 集全等 -------
    collect = subprocess.run(
        _base_cmd() + [*FIXED_TARGET_NODEIDS, "--collect-only", "-q"],
        cwd=iso,
        env=_child_env(vault_tmp, lance_tmp, None, iso),
        capture_output=True,
        text=True,
        timeout=PYTEST_TIMEOUT_S,
    )
    expected_nodeids = {ln.strip() for ln in collect.stdout.splitlines() if "::" in ln}
    if collect.returncode != 0 or expected_nodeids != set(FIXED_TARGET_NODEIDS):
        print(
            f"NEGATIVE-CONTROL: FAIL — 预采集失败或与钉死 nodeid 不全等（collect rc={collect.returncode}）："
            f"缺 {sorted(set(FIXED_TARGET_NODEIDS) - expected_nodeids)}，"
            f"多 {sorted(expected_nodeids - set(FIXED_TARGET_NODEIDS))}"
        )
        print(collect.stdout[-1500:])
        return 1
    print(f"[1] 预采集 nodeid: {len(expected_nodeids)} 条（与钉死完整 nodeid 全等，collect rc=0）")

    # -- 1b. 正控：三条必须**各跑一次且全 passed**，门账全零，运行时零写 -----
    #     R1 Codex HIGH-12：只查 rc=0 证明不了「三条全绿」—— 在 client fixture
    #     yield 之后 `pytest.skip()` 同样是 rc=0/零门账，而变异态照旧按预期红，
    #     于是整条负门变成假 PASS。所以正控也出 junit，逐条核对 outcome。
    pos = subprocess.run(
        _base_cmd() + [*FIXED_TARGET_NODEIDS, "-q", "--tb=short", "-rA", f"--junitxml={pos_junit}"],
        cwd=iso,
        env=_child_env(vault_tmp, lance_tmp, pos_ledger, iso),
        capture_output=True,
        text=True,
        timeout=PYTEST_TIMEOUT_S,
    )
    pos_summary = _parse_summary(pos.stdout)
    pos_cases = _parse_junit(pos_junit, TARGET_REL) if pos_junit.exists() else []
    pos_outcomes = [(nid, c["outcome"]) for nid, c in pos_cases]
    positive_runtime_ok = runtime_snapshot(iso) == iso_runtime_before
    print(f"[1b] 正控 rc={pos.returncode} 门汇总={pos_summary} outcomes={pos_outcomes}")
    pos_problem = None
    if pos.returncode != 0:
        pos_problem = f"正控 rc={pos.returncode} ≠ 0"
    elif sorted(nid for nid, _ in pos_outcomes) != sorted(FIXED_TARGET_NODEIDS):
        # **多重集**比较：三条各恰好一次。用集合比会把重复项吞掉。
        pos_problem = f"正控 junit 的 nodeid 多重集与钉死集不等（要求各恰好一次）：{pos_outcomes}"
    elif any(outcome != "passed" for _, outcome in pos_outcomes):
        pos_problem = f"正控三条不是全 passed：{pos_outcomes}（skip/error 也不算绿）"
    elif not isinstance(pos_summary, tuple):
        pos_problem = f"正控门汇总行解析失败：{pos_summary}"
    elif pos_summary != (0, 0, 0, 0):
        pos_problem = f"正控门账非零：{pos_summary}（隔离态不应有任何连接尝试）"
    elif not positive_runtime_ok:
        pos_problem = "正控（隔离态）动了运行时文件 —— no_lifespan 没挡住启动副作用"
    if pos_problem:
        print(f"NEGATIVE-CONTROL: FAIL — {pos_problem}")
        print("--- 正控 stdout tail ---")
        print(pos.stdout[-2000:])
        return 1
    print("[1c] 正控：三条全 passed、门账全零、运行时文件 unchanged")

    # -- 2. 在**副本**里摘掉 no_lifespan（真实文件不动）--------------------
    count = original.decode("utf-8").count(ANCHOR)
    if count != 1:
        print(
            f"NEGATIVE-CONTROL: FAIL — 隔离锚点出现 {count} 次（期望恰好 1 次），"
            f"文件形态与本脚本假设不符，拒绝盲改: {TARGET_REL}"
        )
        return 1
    iso_target.write_bytes(mutated_bytes)
    print(f"[2] 已在副本里摘掉 no_lifespan: {iso_target}")

    # -- 3. 变异运行 ----------------------------------------------------
    cmd = _base_cmd() + [*FIXED_TARGET_NODEIDS, "-q", "--tb=no", "-rA", f"--junitxml={neg_junit}"]
    print("[3] pytest 子进程（串行，cwd=隔离副本）:", " ".join(cmd))
    try:
        proc = subprocess.run(
            cmd,
            cwd=iso,
            env=_child_env(vault_tmp, lance_tmp, neg_ledger, iso),
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
        print(proc.stdout[-1500:])
        return 1
    s_total, s_blocked, s_advisory, s_unacct = summary
    print(f"[3b] 子进程门汇总: total={s_total} blocked={s_blocked} advisory={s_advisory} unaccounted={s_unacct}")

    # -- 3c. 父进程独立复核账本 -----------------------------------------
    if not neg_ledger.exists():
        ledger_problem = "子进程未落账本（最终结算 atexit 未跑？）"
    else:
        led = json.loads(neg_ledger.read_text(encoding="utf-8"))
        print(
            f"[3c] 账本: {json.dumps({k: v for k, v in led.items() if k != 'unaccounted_records'}, ensure_ascii=False)}"
        )
        if (led["total"], led["blocked"], led["advisory"], led["unaccounted"]) != summary:
            ledger_problem = f"账本 {led} 与 stdout 汇总 {summary} 不一致"
        elif not led.get("exempt_disabled"):
            ledger_problem = "账本显示豁免未被禁用（W4_GUARD_NO_EXEMPT 未生效）"

    # -- 4. 解析 junitxml：红因判定必须吃完整 failure/error 正文 ---------
    if not neg_junit.exists():
        print("NEGATIVE-CONTROL: FAIL — junitxml 未生成")
        return 1
    red_list: list[str] = []
    for nid, case in _parse_junit(neg_junit, TARGET_REL):
        total += 1
        if case["outcome"] in ("passed", "skipped"):
            green.append(nid)  # skip 不是红
            continue
        red_list.append(nid)
        red_nodeids.add(nid)
        if EXPECTED_REASON in case["text"]:
            reason_verified.add(nid)
        else:
            red_for_wrong_reason.append(f"{nid} :: {case['text'][:160] or '<无正文 — 红因不明>'}")

    print(
        f"[4] junitxml: total={total} red={len(red_nodeids)} "
        f"green={len(green)} red-wrong-reason={len(red_for_wrong_reason)}"
    )
    for g in green:
        print(f"    GREEN (不应绿): {g}")
    for w in red_for_wrong_reason:
        print(f"    RED-WRONG-REASON: {w}")

    # -- 5. 运行时文件：副本必须被写（隔离承重的正证据）；真实树必须纹丝不动 --
    iso_runtime_after = runtime_snapshot(iso)
    mutated_runtime_delta = "" if iso_runtime_after == iso_runtime_before else iso_runtime_after
    real_after = runtime_snapshot(BACKEND_DIR)
    real_untouched = real_after == real_before
    target_untouched = hashlib.sha256(TARGET.read_bytes()).hexdigest() == original_sha
    print(f"[5] 真实树运行时文件 untouched={real_untouched}; 真实目标文件 untouched={target_untouched}")
    if mutated_runtime_delta:
        print("[5b] 副本里变异态确实写了运行时文件（= 隔离在承重的正证据）:")
        for line in mutated_runtime_delta.splitlines():
            print(f"      {line}")

    # -- 6. 裁定 --------------------------------------------------------------
    problems: list[str] = []
    if pytest_rc != 1:
        problems.append(f"pytest 退出码 {pytest_rc} ≠ 1（期望恰为 tests-failed）")
    if not (s_total == s_blocked > 0):
        problems.append(f"门账 total({s_total}) == blocked({s_blocked}) > 0 不成立")
    if s_advisory != 0:
        problems.append(f"advisory={s_advisory} ≠ 0（有连接以豁免名义真的发出去了）")
    if s_unacct != 0:
        problems.append(f"unaccounted={s_unacct} ≠ 0（有拦截无人结账）")
    if ledger_problem:
        problems.append(ledger_problem)
    if total != len(expected_nodeids):
        problems.append(f"用例总数 {total} ≠ 预采集 {len(expected_nodeids)} — 解析或收集缩水")
    if green:
        problems.append(f"{len(green)} 个用例在 no_lifespan 摘除后没红（哨兵没接住）")
    if sorted(red_list) != sorted(FIXED_TARGET_NODEIDS):
        # 多重集比较：三条各恰好红一次（集合比会把重复项吞掉）
        problems.append(f"红集多重集与钉死 nodeid 不等（要求各恰好一次）：{sorted(red_list)}")
    if red_for_wrong_reason:
        problems.append(f"{len(red_for_wrong_reason)} 个用例红了但原因不对（不是 live port connect）")
    if reason_verified != red_nodeids:
        problems.append(f"红因可验证集 {len(reason_verified)} ≠ 红集 {len(red_nodeids)} —— 红因不明，fail-closed")
    if not mutated_runtime_delta:
        problems.append(
            "变异态**没有**写任何运行时文件 —— 说明 lifespan 没跑到写路径就 abort 了，"
            "这条负门此刻在测别的东西（历史教训：LanceDB canonical/legacy 冲突会让它"
            "在到达 Neo4j 之前就退出）"
        )
    if not real_untouched:
        problems.append(f"真实树的运行时文件被动过（本脚本从不写它们）：\n{real_before}\n---\n{real_after}")
    if not target_untouched:
        problems.append("真实树的目标测试文件被动过（本脚本只改副本）")
    if n_violations:
        problems.append(f"AST 门 {n_violations} 处违规（见上方 VIOLATION 清单）")

    if problems:
        print("NEGATIVE-CONTROL: FAIL")
        for p in problems:
            print(f"  - {p}")
        print("--- 变异运行 child stdout tail ---")
        print(child_stdout[-4000:])
        if child_stderr.strip():
            print("--- 变异运行 child stderr tail ---")
            print(child_stderr[-2000:])
        return 1

    print(
        f"NEGATIVE-CONTROL: PASS ({len(reason_verified)} nodeids red for expected reason; "
        f"summary={summary}; positive control: 3/3 passed, zero attempts, zero runtime writes; "
        f"mutated run in an isolated copy did touch runtime files (isolation is load-bearing); "
        f"real tree untouched; AST-GATE: PASS 0/{n_files} files)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
