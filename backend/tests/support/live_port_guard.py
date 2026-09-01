"""「测试进程运行时零连现网 Neo4j」硬门。

[BATCH-2026-09-01-第八批 / CARD-TEST-isolate-lifespan]

## 为什么是双层，而不只是「connect 前抛异常」

`backend/app/main.py` 的 lifespan 每一步都包在 ``try/except Exception`` +
``logger.warning`` 里（预热 MemoryService、fulltext index、LanceDB recover、
EventBus recover_outbox、graphiti 探活、wikilink build …）。所以在 connect 处抛出的
``RuntimeError`` 会被**吞掉**：``TestClient.__enter__`` 照常成功，用例照常全绿。

2026-09-01 于本车道 venv 实测（scratchpad/exp_mechanics.py）：不换 lifespan 栓时，
真实 ``app.main.app`` 起 ``TestClient`` 会发起 3 次到 ``('::1', 7691, 0, 0)`` 的连接，
3 次全部被本门拦下，**而没有任何一条用例变红**。

因此本门是三层：

1. **connect 前抛**（fail-closed）—— 保证进程永远不会真的连上现网库；
2. **每用例结账**（conftest 的 ``pytest_runtest_makereport`` 哨兵）—— 把被生产代码
   吞掉的拦截转成该用例 ``FAILED``；
3. **session 总账**（conftest 的 ``pytest_cmdline_main`` 收口）—— 任何「到死都没被
   哨兵结账」的拦截（迟到线程、collection 期、未知线程）都会把整个 pytest 进程的
   退出码改成 3。没有这一层，一条从不在任何用例名下出现的拦截就无人买单。

## 归属模型（线程安全 + 未知来源 fail-closed）

当前用例的归属信息放 **ContextVar**（不是共享字段）：主线程在
``pytest_runtest_protocol`` 边界 set/reset，TestClient 的 anyio portal 线程会携带
上下文副本（2026-09-01 实测 ``ContextVar`` 值在 portal 线程可见），所以 portal 里
发起的连接能记到发起用例名下。**不带上下文的裸线程**（``threading.Thread`` 直启）
看到的是默认值 → 归 ``<unknown>`` 且**永不豁免** → fail-closed。

## 这道门不比什么（诚实边界，验收单同步登记）

* 只拦本进程内的 ``socket.socket.connect`` / ``connect_ex``。**子进程**里的连接
  （``subprocess`` / ``os.system`` 起的 python）不在射程内。
* 只拦 TCP 连接建立那一刻。若某处**复用**了一条门装上之前就已建立的连接，
  本门看不到。
* 只按**目标端口**判定，不解析 bolt 协议。连到 7691/7687 之外端口的现网库
  （例如有人改了 compose 端口映射）本门不拦。
* uvloop 走 libuv 自己的 connect，**不经过** ``socket.socket.connect``。本门在
  :func:`install` 时把 ``sys.modules["uvloop"]`` 毒化为 ``None``（此后任何
  ``import uvloop`` 直接 ``ImportError``），并在 session fixture 里复核——不是
  只在装门那一刻检查一次（Codex round-1 HIGH：事后检查拦不住「先装门、后导入
  uvloop」的时序）。毒化是进程级承诺：本 venv 的 uvloop 全仓零引用，误伤面为零。
"""

from __future__ import annotations

import asyncio
import contextvars
import os
import socket as _socket_mod
import sys
import threading
import warnings

import pytest

# ═══════════════════════════════════════════════════════════════════════════
# 契约常量
# ═══════════════════════════════════════════════════════════════════════════

#: 现网 Neo4j 的 bolt 端口。7691 = docker-compose 的 canvas-learning-system-neo4j
#: （backend/.env 的 NEO4J_URI）；7687 = app/config.py 的 NEO4J_URI 默认值，
#: 也是 neo4j 官方默认端口——CI 没有 .env，任何遗漏隔离的测试会打到它。
#: 测试容器 7692（NEO4J_TEST_URI）**不在此列**，真库门测试照常可用。
BLOCKED_PORTS = frozenset({7691, 7687})

#: 打了这些 marker 的用例只记录不拦（advisory）。
EXEMPT_MARKERS = frozenset({"integration", "e2e", "real_neo4j"})

#: 这些路径前缀下的用例只记录不拦（advisory）。
#: 为什么按路径而不只按 marker：``backend/tests/integration/conftest.py`` 没有
#: ``pytest_collection_modifyitems`` 自动打标，``test_story_38_7_ac3/ac5`` 等文件
#: 也没有 ``pytestmark`` —— 只认 marker 会把它们错判成违规。
#: ⚠️ 这是**有意的旁路**：新写的测试只要放进 tests/integration/ 就自动免拦。
EXEMPT_PATH_PREFIXES = ("integration", "e2e")

#: 拦截原因文案。负控脚本按这个子串判"红得是不是因为这件事"，不要随手改。
BLOCK_REASON = "live Neo4j port connect attempted"

_SUMMARY_PREFIX = "NEO4J_LIVE_PORT_CONNECT_ATTEMPTS"

_UNKNOWN_OWNER = "<unknown>"


# ═══════════════════════════════════════════════════════════════════════════
# 归属上下文（ContextVar：portal 线程带副本可见，裸线程默认 fail-closed）
# ═══════════════════════════════════════════════════════════════════════════

_OWNER_CV: contextvars.ContextVar[str] = contextvars.ContextVar("w4_guard_owner", default=_UNKNOWN_OWNER)
_EXEMPT_CV: contextvars.ContextVar[bool] = contextvars.ContextVar("w4_guard_exempt", default=False)
#: 归属代次：begin_item 发新票，end_item 换代。ContextVar 会被 ``Context.copy()``
#: 复制走 —— 旧副本里存的代次一旦过期，其连接一律按 unknown fail-closed 处理
#: （Codex round-2 HIGH：否则豁免期复制的 context 能把豁免特权带出用例边界）。
_GEN_CV: contextvars.ContextVar[int] = contextvars.ContextVar("w4_guard_gen", default=-1)


# ═══════════════════════════════════════════════════════════════════════════
# 状态
# ═══════════════════════════════════════════════════════════════════════════


class _GuardState:
    """门的运行时账。计数跨线程累加；归属走 ContextVar。"""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.installed = False
        self.total = 0
        self.blocked = 0
        self.advisory = 0
        #: 已被哨兵结账（转成用例失败）的 blocked 数。
        self.billed = 0
        self.records: list[dict] = []
        # owner -> 该用例名下尚未结账的拦截记录
        self.pending: dict[str, list[dict]] = {}
        self._orig_connect = None
        self._orig_connect_ex = None
        #: 当前有效归属代次（end_item 即换代，旧 context 副本的票作废）。
        self.current_gen = 0
        self._next_gen = 1

    # ── 记账 ────────────────────────────────────────────────────────────
    def record(self, address) -> bool:
        """记一次到受拦端口的连接尝试。返回 True 表示应当拦（非豁免）。"""
        owner = _OWNER_CV.get()
        exempt = _EXEMPT_CV.get()
        gen = _GEN_CV.get()
        with self._lock:
            stale = gen != self.current_gen
            if stale:
                # 过期 context 副本（用例已结束/豁免已被撤销）—— fail-closed
                owner = _UNKNOWN_OWNER
                exempt = False
            rec = {
                "address": repr(address),
                "thread": threading.current_thread().name,
                "owner": owner,
                "exempt": exempt,
            }
            self.total += 1
            self.records.append(rec)
            if exempt:
                self.advisory += 1
                return False
            self.blocked += 1
            self.pending.setdefault(owner, []).append(rec)
            return True

    def take(self, owner: str) -> list[dict]:
        with self._lock:
            records = self.pending.pop(owner, [])
            self.billed += len(records)
            return records

    def unaccounted_blocked(self) -> list[dict]:
        """到死没被任何用例结账的 blocked 记录（迟到线程 / collection 期 / 未知线程）。

        每条 blocked 记录都会先落 ``pending[owner]``；哨兵 ``take()`` 时迁出并计入
        ``billed``。所以 session 结束时仍留在 ``pending`` 里的，就是无人买单的账。
        """
        with self._lock:
            return self._unaccounted_locked()

    def _unaccounted_locked(self) -> list[dict]:
        """``self._lock`` 已持有的前提下取无人买单的账（不可重入锁，禁止嵌套获取）。"""
        return [rec for records in self.pending.values() for rec in records]

    def summary_line(self) -> str:
        with self._lock:
            unaccounted = len(self._unaccounted_locked())
            return (
                f"{_SUMMARY_PREFIX}={self.total} "
                f"(blocked={self.blocked}, advisory={self.advisory}, "
                f"unaccounted={unaccounted})"
            )


STATE = _GuardState()


def begin_item(owner: str, exempt: bool) -> None:
    """标记「现在起到 end_item 之间的连接归属 owner」（ContextVar，portal 线程可见）。"""
    with STATE._lock:
        STATE.current_gen = STATE._next_gen
        STATE._next_gen += 1
        gen = STATE.current_gen
    _OWNER_CV.set(owner)
    _EXEMPT_CV.set(exempt)
    _GEN_CV.set(gen)


def end_item() -> None:
    """结束归属：主线程上下文复位 + 换代——旧 context 副本（含豁免票）立即作废。"""
    with STATE._lock:
        STATE.current_gen = STATE._next_gen
        STATE._next_gen += 1
    _OWNER_CV.set(_UNKNOWN_OWNER)
    _EXEMPT_CV.set(False)
    _GEN_CV.set(-1)


# ═══════════════════════════════════════════════════════════════════════════
# 端口提取 + 包装
# ═══════════════════════════════════════════════════════════════════════════


def extract_port(address) -> int | None:
    """从 socket 地址里取端口。

    IPv4 是 2 元组 ``('127.0.0.1', 7691)``；IPv6 是 4 元组
    ``('::1', 7691, 0, 0)`` —— 2026-09-01 实测 neo4j 驱动走的正是 IPv6 四元组，
    只按 ``len(address) == 2`` 判会**整条漏掉**。
    AF_UNIX（str/bytes 地址）与其它协议族返回 None（不在本门射程）。
    """
    if isinstance(address, tuple) and len(address) >= 2:
        port = address[1]
        if isinstance(port, int):
            return port
    return None


def _block_message(address) -> str:
    return (
        f"{BLOCK_REASON}: {address!r}. "
        f"受拦端口 {sorted(BLOCKED_PORTS)} 是现网 Neo4j；测试进程不得连接。"
        f"若这是端点测试，请用 backend/tests/support/lifespan.py::no_lifespan "
        f"关掉 app.main 的 lifespan；若确需真库，用测试容器 "
        f"NEO4J_TEST_URI(7692) 并打 integration/real_neo4j marker。"
    )


def _guarded_connect(sock_self, address):
    if extract_port(address) in BLOCKED_PORTS:
        if STATE.record(address):
            raise RuntimeError(_block_message(address))
    return STATE._orig_connect(sock_self, address)


def _guarded_connect_ex(sock_self, address):
    """``connect_ex`` 正常返回 errno 而不抛；这里**故意抛**。

    fail-closed 优先于 API 形状：一个用 connect_ex 探活现网库的调用方，
    拿到 errno 会静默走降级分支，那正是本卡要消灭的「静默连库」。
    """
    if extract_port(address) in BLOCKED_PORTS:
        if STATE.record(address):
            raise RuntimeError(_block_message(address))
    return STATE._orig_connect_ex(sock_self, address)


def poison_uvloop() -> None:
    """把 ``import uvloop`` 在本进程内变成 ``ImportError``。

    uvloop 的 connect 走 libuv，绕过 ``socket.socket.connect`` —— 与其事后
    检查「有没有人用了 uvloop」（Codex round-1 HIGH：时序上拦不住先装门后
    导入），不如直接关死这扇门。本 venv 的 uvloop 全仓零引用，误伤面为零；
    若未来确需 uvloop，必须连本门一起重新设计（下沉到 uvloop/OS 层）。
    """
    if "uvloop" not in sys.modules:
        sys.modules["uvloop"] = None  # type: ignore[assignment] — import 时即 ImportError
        for mod_name in [m for m in sys.modules if m.startswith("uvloop.")]:
            sys.modules[mod_name] = None  # type: ignore[assignment]


def install() -> None:
    """装门 + 毒化 uvloop。幂等——重复调用不会把包装函数当成原函数存起来。

    patch 目标是 ``_socket.socket``（= ``socket.SocketType`` 基类本体）而不是
    ``socket.socket`` 子类：Python 3.14 的 ``socket.SocketType`` 就是未包装的
    ``_socket.socket``，只 patch 子类会漏掉直接用基类/SocketType 的调用方
    （Codex round-2 HIGH 实测）。子类没有自己的 connect 定义，基类 patch 对
    全部子类生效。

    ⚠️ 装=不卸：本门**只装不卸**（uninstall 仅为 API 完整保留，生产代码路径
    不调用）。CLI 测试进程的迟到线程在 ``pytest_unconfigure`` 之后仍可能发起
    连接（Codex round-2 HIGH 实测），先恢复 socket 再结账会留下无账窗口——
    门随进程存活到退出，这是有意为之。
    """
    uvloop_mod = sys.modules.get("uvloop")
    if uvloop_mod is not None:
        # install 前就被人 import 了：collection/import 窗口已经不受保护，
        # 宁可立刻 fail 也不装一道已知失效的门（Codex round-2 HIGH）。
        raise RuntimeError(
            "uvloop 在 install() 之前已被导入 —— 本门会静默失效，拒绝装门。"
            "请在任何业务 import 之前先装门（根 conftest 已保证），并排查是谁提前导入了 uvloop。"
        )
    poison_uvloop()
    if STATE.installed:
        return
    base = _socket_mod.socket  # _socket.socket 基类（socket.SocketType 同一对象）
    STATE._orig_connect = base.connect
    STATE._orig_connect_ex = base.connect_ex
    base.connect = _guarded_connect  # type: ignore[method-assign]
    base.connect_ex = _guarded_connect_ex  # type: ignore[method-assign]
    STATE.installed = True


def uninstall() -> None:
    """仅保留 API 形状；CLI 测试进程**刻意不调用**（见 install 的 ⚠️ 说明）。"""
    if not STATE.installed:
        return
    base = _socket_mod.socket
    base.connect = STATE._orig_connect  # type: ignore[method-assign]
    base.connect_ex = STATE._orig_connect_ex  # type: ignore[method-assign]
    STATE.installed = False


# ═══════════════════════════════════════════════════════════════════════════
# 自证
# ═══════════════════════════════════════════════════════════════════════════


def assert_not_uvloop() -> None:
    """session 级复核：uvloop 已被 :func:`poison_uvloop` 关死。

    import 失败毒化 + policy 复核双保险；policy 拿不到时不算证据失败
    （3.14 起 get_event_loop_policy 已 deprecated），毒化才是承重防线。
    """
    if sys.modules.get("uvloop") is not None:
        raise RuntimeError(
            "uvloop 已在本进程被导入：本门包装的是 socket.socket.connect，uvloop 走 "
            "libuv 绕过它，门会静默失效。install() 应当已把 uvloop 毒化——出现本错误"
            "说明毒化被人绕过（例如 install 前已被 import）。"
        )
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            policy_module = type(asyncio.get_event_loop_policy()).__module__ or ""
    except Exception:  # noqa: BLE001 —— 拿不到 policy 不算证据，靠 sys.modules 那条
        return
    if "uvloop" in policy_module:
        raise RuntimeError(f"event loop policy 来自 uvloop（{policy_module}）：本门会静默失效。")


def assert_test_uri_not_blocked() -> None:
    """NEO4J_TEST_URI 指向受拦端口 = 配置事故，直接 fail 而不是悄悄放行。

    刻意**不**做「把 NEO4J_TEST_URI 的端口从受拦集合里摘掉」——那会给出一条
    「改个环境变量就能把门打开」的静默旁路。
    """
    uri = os.environ.get("NEO4J_TEST_URI") or ""
    for port in BLOCKED_PORTS:
        if f":{port}" in uri:
            raise RuntimeError(f"NEO4J_TEST_URI={uri!r} 指向受拦端口 {port}（现网库）。测试容器应当是 7692。")


# ═══════════════════════════════════════════════════════════════════════════
# pytest 接线（由根 conftest 调用）
# ═══════════════════════════════════════════════════════════════════════════


def is_exempt(item, tests_dir) -> tuple[bool, str]:
    """该用例是否豁免（只记不拦）。返回 (豁免, 依据)。

    ``tests_dir`` = backend/tests 的绝对路径（由 conftest 传入 ``Path(__file__).parent``）。
    路径判定用 **相对化后的首段目录**，不做整条路径的 substring——
    ``/tmp/tests/integration/...`` 之类的绝对路径不得误判（Codex round-1 MEDIUM）。
    """
    for marker in EXEMPT_MARKERS:
        if item.get_closest_marker(marker) is not None:
            return True, f"marker:{marker}"
    try:
        rel = item.path.resolve().relative_to(tests_dir.resolve())
    except Exception:  # noqa: BLE001 —— 相对化失败（如 rootdir 外）一律不豁免，fail-closed
        return False, ""
    first = rel.parts[0] if rel.parts else ""
    if first in EXEMPT_PATH_PREFIXES:
        return True, f"path:{first}/"
    return False, ""


def format_sentinel(owner: str, records: list[dict]) -> str:
    lines = [
        f"{BLOCK_REASON} —— 本用例期间有 {len(records)} 次到现网 Neo4j 的连接尝试被拦下。",
        "（连接处抛出的异常被 app/main.py 的 lifespan try/except 吞掉了，",
        "  所以由本哨兵把它转成用例失败——否则这道门什么都证明不了。）",
    ]
    for rec in records:
        lines.append(f"  - {rec['address']} on thread {rec['thread']} (owner={owner})")
    return "\n".join(lines)
