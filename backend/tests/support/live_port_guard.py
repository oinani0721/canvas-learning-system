"""「测试进程运行时零连现网 Neo4j」硬门。

[BATCH-2026-09-01-第九批 / CARD-TEST-isolate-lifespan-R1]

## 承重层为什么是 audit hook，而不是 monkeypatch ``socket.socket.connect``

第八批用的是「把 ``socket.socket.connect`` 换成包装函数」。2026-09-03 于本车道
venv（CPython 3.14.4）实测，这条防线有一个结构性缺口：

* ``socket.socket`` 是 **Python 子类**，``socket.SocketType is _socket.socket`` 为
  ``True`` 而 ``socket.SocketType is socket.socket`` 为 ``False``；
* 因此 ``base.connect = ...`` 只在**子类** ``__dict__`` 里放了一个覆盖；
* 直接用 ``_socket.socket(...)`` 或 ``socket.SocketType(...)`` 建的 socket **完全
  不经过**那个覆盖 —— 实测 loopback 直连成功、门的账面 ``blocked=0``；
* 而 ``_socket.socket`` 是 C 不可变类型，``TypeError: cannot set 'connect'
  attribute of immutable type`` —— 「把 patch 挪到基类」这条路走不通。

所以承重换成 :func:`sys.addaudithook` 监听 CPython 的 ``socket.connect`` 审计事件：
该事件由 ``sock_connect`` 在**真正发起连接之前**触发，对
``socket.socket`` / ``_socket.socket`` / ``socket.SocketType`` / ``connect_ex``
四条路径**一律**触发（2026-09-03 实测四条全部被拦），且 CPython **没有**
``sys.removeaudithook`` —— 装上即不可摘。

``socket.socket.connect`` 上仍保留一层 **belt**，但它 **不承重、不记账**：它只是
高层路径上一个「身份可校验的锚点」，让 :func:`assert_guard_live` 能发现「有人把
``socket.socket.connect`` 换掉了」这类漂移（第八批 Codex HIGH：``install()`` 只信
``STATE.installed``，门被拆掉后重装仍报 ``installed=True``）。belt 的实现只是
委托给原函数——真正的拦截与记账全部发生在 audit hook 里，因此不存在双计。

## 为什么还要「结账哨兵」和「最终总账」

``backend/app/main.py`` 的 lifespan 每一步都包在 ``try/except Exception`` +
``logger.warning`` 里。所以在 connect 处抛出的异常会被**吞掉**：
``TestClient.__enter__`` 照常成功、用例照常全绿。因此本门是四层：

1. **connect 前抛**（audit hook，fail-closed）—— 进程永远不会真的连上现网库；
2. **每用例结账**（conftest 的 ``pytest_runtest_makereport`` 哨兵）—— 把被生产
   代码吞掉的拦截转成该用例 ``FAILED``；
3. **session 总账**（conftest 的 ``pytest_cmdline_main`` 收口）—— 任何「到死都没
   被哨兵结账」的拦截把退出码改成 3；
4. **最终总账**（:func:`register_final_accounting` 注册的 ``atexit``）——
   ``pytest_cmdline_main`` 返回之后仍有 cleanup / ``atexit`` / 迟到线程的窗口
   （第八批 Codex HIGH 实测：那段窗口里的拦截被记账、进程却仍 exit 0）。本层在
   **所有** ``atexit`` 之后执行（``atexit`` 是 LIFO，本层在 :func:`install` 里
   最早注册 ⇒ 最后执行），发现未结账的拦截就 ``os._exit(3)``，把「迟到尝试」
   变成非零 rc。同时把账本落到 ``W4_GUARD_LEDGER`` 指定的文件，供父进程独立复核。

## 归属模型（线程安全 + 未知来源 fail-closed）

当前用例的归属信息放 **ContextVar**（不是共享字段）：主线程在
``pytest_runtest_protocol`` 边界 set/reset，TestClient 的 anyio portal 线程会携带
上下文副本，所以 portal 里发起的连接能记到发起用例名下。**不带上下文的裸线程**
（``threading.Thread`` 直启）看到的是默认值 → 归 ``<unknown>`` 且**永不豁免** →
fail-closed。

## 环境开关只有一个方向

本模块读三个环境变量，**没有任何一个能把门打开**：

* ``W4_GUARD_NO_EXEMPT=1`` —— 关掉 integration/e2e 的豁免（更严）；
* ``W4_GUARD_REQUIRE_BLOCKED_TARGET=1`` —— 目标端口不在射程内就**拒绝装门**（更严）；
* ``W4_GUARD_LEDGER=<path>`` —— 把账本落盘供父进程复核（只增加可观测性）。

「改个环境变量就能让测试连上现网库」这条路刻意不存在。同理，
:func:`assert_test_uri_not_blocked` 也**不**做「把 NEO4J_TEST_URI 的端口从受拦集合
里摘掉」——那会给出一条静默旁路。

## 这道门不比什么（诚实边界，验收单同步登记）

* 只拦本进程内的连接。**子进程**里的连接（``subprocess`` / ``os.system`` 起的
  python）不在射程内 —— 子解释器没有本进程的 audit hook。
* 只拦 TCP 连接建立那一刻。若某处**复用**了一条门装上之前就已建立的连接，
  本门看不到。
* 只按**目标端口**判定，不解析 bolt 协议。连到 7691/7687 之外端口的现网库
  （例如有人改了 compose 端口映射）本门不拦 —— 这正是负控必须**钉死**
  ``NEO4J_URI`` 指向受拦端口的原因（见 :func:`assert_neo4j_target_blocked`）。
* uvloop 走 libuv 自己的 connect。libuv 的连接**不经过** CPython 的
  ``socket.connect`` 审计事件，本门在 :func:`install` 时把
  ``sys.modules["uvloop"]`` 毒化为 ``None``（此后任何 ``import uvloop`` 直接
  ``ImportError``），并在 session fixture 与每个用例边界复核。
* 「最终总账」之后（解释器 finalization 期间）发起的连接仍会被 audit hook 拦下，
  但已无人能把它变成非零 rc —— 这段窗口无法在进程内闭合，如实登记。
"""

from __future__ import annotations

import asyncio
import atexit
import contextvars
import json
import operator
import os
import socket as _socket_mod
import sys
import threading
import warnings

# ═══════════════════════════════════════════════════════════════════════════
# 契约常量
# ═══════════════════════════════════════════════════════════════════════════

#: 现网 Neo4j 的 bolt 端口。7691 = docker-compose 的 canvas-learning-system-neo4j
#: （backend/.env 的 NEO4J_URI）；7687 = app/config.py 的 NEO4J_URI 默认值，
#: 也是 neo4j 官方默认端口——CI 没有 .env，任何遗漏隔离的测试会打到它。
#: 测试容器 7692（NEO4J_TEST_URI）**不在此列**，真库门测试照常可用。
#:
#: :data:`REQUIRED_BLOCKED_PORTS` 是**不可协商的下界**：:func:`assert_guard_live`
#: 在每个用例边界复核它仍被 :data:`BLOCKED_PORTS` 覆盖。允许往上加（探针会临时
#: 加一个本地端口），**不允许往下减** —— 「把 7691 从集合里摘掉」是最省事的
#: 拆门方式，必须让它当场翻红而不是静默放行。
REQUIRED_BLOCKED_PORTS = frozenset({7691, 7687})
BLOCKED_PORTS = REQUIRED_BLOCKED_PORTS

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

#: 私有审计事件：:func:`assert_guard_live` 用它把一枚一次性 token 送进 audit
#: 子系统再取回，从而**行为上**证明「本模块的 hook 仍挂在链上且正在执行」。
#: 这不是「读一个布尔值」——token 没回来就说明 hook 已经不在了。
_SELFTEST_EVENT = "w4.live_port_guard.selftest"

#: 负控用：置为 "1" 时**彻底禁用豁免**（integration/e2e 也照拦）。
#: 只会让门更严，不会更松 —— 不存在「设个环境变量把门打开」的方向。
ENV_NO_EXEMPT = "W4_GUARD_NO_EXEMPT"

#: 负控用：置为 "1" 时要求 ``NEO4J_URI`` 必须指向受拦端口，否则**拒绝装门**。
#: 第八批 Codex BLOCKER：负控子进程继承调用者环境，``NEO4J_URI`` 若指向
#: 7691/7687 之外的库，摘掉 no_lifespan 后会**真实连接**那个库，而门只拦
#: 7691/7687 —— 脚本只会事后因 blocked=0 失败，实害已经发生。
ENV_REQUIRE_BLOCKED_TARGET = "W4_GUARD_REQUIRE_BLOCKED_TARGET"

#: 最终总账落盘路径（父进程独立复核用）。
ENV_LEDGER = "W4_GUARD_LEDGER"

#: 最终总账判定「有未结账拦截」时强制的退出码（与 session 总账同码）。
FINAL_EXIT_CODE = 3


# ═══════════════════════════════════════════════════════════════════════════
# 归属上下文（ContextVar：portal 线程带副本可见，裸线程默认 fail-closed）
# ═══════════════════════════════════════════════════════════════════════════

_OWNER_CV: contextvars.ContextVar[str] = contextvars.ContextVar("w4_guard_owner", default=_UNKNOWN_OWNER)
_EXEMPT_CV: contextvars.ContextVar[bool] = contextvars.ContextVar("w4_guard_exempt", default=False)
#: 归属代次：begin_item 发新票，end_item 换代。ContextVar 会被 ``Context.copy()``
#: 复制走 —— 旧副本里存的代次一旦过期，其连接一律按 unknown fail-closed 处理
#: （Codex round-2 HIGH：否则豁免期复制的 context 能把豁免特权带出用例边界）。
_GEN_CV: contextvars.ContextVar[int] = contextvars.ContextVar("w4_guard_gen", default=-1)


class GuardDrift(RuntimeError):
    """门的身份/在位性发生漂移 —— 一律 fail-closed，不允许静默继续。"""


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
        #: ``pytest_cmdline_main`` 收口时报回来的退出码；None = pytest 没跑过。
        self.reported_status: int | None = None

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

    def ledger(self) -> dict:
        """账本快照（父进程复核 / 最终总账都读这一份，口径唯一）。"""
        with self._lock:
            unaccounted = self._unaccounted_locked()
            return {
                "total": self.total,
                "blocked": self.blocked,
                "advisory": self.advisory,
                "billed": self.billed,
                "unaccounted": len(unaccounted),
                "unaccounted_records": unaccounted,
                "reported_status": self.reported_status,
                "installed": self.installed,
                "blocked_ports": sorted(BLOCKED_PORTS),
                "exempt_disabled": exempt_disabled(),
            }

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


def exempt_disabled() -> bool:
    """负控模式：豁免被彻底关掉（只会更严）。"""
    return os.environ.get(ENV_NO_EXEMPT) == "1"


# ═══════════════════════════════════════════════════════════════════════════
# 端口提取 + 承重 audit hook
# ═══════════════════════════════════════════════════════════════════════════


def extract_port(address) -> int | None:
    """从 socket 地址里取端口。

    IPv4 是 2 元组 ``('127.0.0.1', 7691)``；IPv6 是 4 元组
    ``('::1', 7691, 0, 0)`` —— 2026-09-01 实测 neo4j 驱动走的正是 IPv6 四元组，
    只按 ``len(address) == 2`` 判会**整条漏掉**。
    AF_UNIX（str/bytes 地址）与其它协议族返回 None（不在本门射程）。

    端口用 :func:`operator.index` 规范化而不是 ``isinstance(port, int)``：
    CPython 的 socket 接受任何实现 ``__index__`` 的对象当端口（2026-09-03 实测
    ``sock.connect(("127.0.0.1", IndexPort(p)))`` 连接成功），只认 ``int`` 会把
    这类地址整条漏掉（第八批 Codex MEDIUM）。
    """
    if isinstance(address, tuple) and len(address) >= 2:
        try:
            return operator.index(address[1])
        except TypeError:
            return None
    return None


def _block_message(address) -> str:
    return (
        f"{BLOCK_REASON}: {address!r}. "
        f"受拦端口 {sorted(BLOCKED_PORTS)} 是现网 Neo4j；测试进程不得连接。"
        f"若这是端点测试，请用 backend/tests/support/lifespan.py::no_lifespan "
        f"关掉 app.main 的 lifespan；若确需真库，用测试容器 "
        f"NEO4J_TEST_URI(7692) 并打 integration/real_neo4j marker。"
    )


#: :func:`assert_guard_live` 与 audit hook 之间的一次性 token 信箱。
_SELFTEST_INBOX: list[object] = []
_selftest_counter = 0
_selftest_lock = threading.Lock()


def _audit_hook(event: str, args) -> None:
    """承重层：CPython ``socket.connect`` 审计事件（连接**发起前**触发）。

    对 ``socket.socket`` / ``_socket.socket`` / ``socket.SocketType`` /
    ``connect_ex`` 四条路径一律触发；hook 抛出的异常会原样传给调用方，
    因此「抛 = 连接没发生」。
    """
    if event == "socket.connect":
        address = args[1] if len(args) > 1 else None
        if extract_port(address) in BLOCKED_PORTS:
            if STATE.record(address):
                raise RuntimeError(_block_message(address))
    elif event == _SELFTEST_EVENT:
        _SELFTEST_INBOX.append(args[0])


#: audit hook 只能装一次（CPython 无 removeaudithook）；重复装会导致双计。
_AUDIT_INSTALLED = False

#: 进程级单例锚点。本模块若被以**两个不同的模块名**导入（``tests.support.
#: live_port_guard`` 与 ``support.live_port_guard``，取决于 sys.path 怎么摆），
#: 会出现两份 ``STATE`` 与两个 audit hook —— 连接尝试被记进其中一份账，另一份
#: 汇报「零尝试」，而汇总行只打印其中一份。这是**账本分裂型假绿**，必须让它当场
#: 炸掉而不是安静地少算。
_SINGLETON_ATTR = "_w4_live_port_guard_module"


def _install_audit_hook() -> None:
    global _AUDIT_INSTALLED
    if _AUDIT_INSTALLED:
        return
    me = sys.modules[__name__]
    existing = getattr(sys, _SINGLETON_ATTR, None)
    if existing is not None and existing is not me:
        raise RuntimeError(
            f"live_port_guard 已以另一个模块名装过门（{getattr(existing, '__name__', '?')} "
            f"vs {__name__}）：会出现两份账本与两个 audit hook，汇总数字必然少算。"
            "请统一导入路径（根 conftest 与 guard_plugin 都用 tests.support.live_port_guard）。"
        )
    setattr(sys, _SINGLETON_ATTR, me)
    sys.addaudithook(_audit_hook)
    _AUDIT_INSTALLED = True


# ── 高层路径的身份锚点（belt，不承重、不记账）──────────────────────────────


def _guarded_connect(sock_self, address):
    """``socket.socket.connect`` 的身份锚点。**不拦截、不记账**，只委托。

    拦截与记账全部由 :func:`_audit_hook` 完成（原函数内部触发审计事件）。
    本包装存在的唯一理由：给 :func:`assert_guard_live` 一个**可比对身份**的对象，
    从而发现「有人把 ``socket.socket.connect`` 换掉了」这类漂移。
    """
    return STATE._orig_connect(sock_self, address)


def _guarded_connect_ex(sock_self, address):
    """``socket.socket.connect_ex`` 的身份锚点。语义同 :func:`_guarded_connect`。"""
    return STATE._orig_connect_ex(sock_self, address)


def poison_uvloop() -> None:
    """把 ``import uvloop`` 在本进程内变成 ``ImportError``。

    uvloop 的 connect 走 libuv，不触发 CPython 的 ``socket.connect`` 审计事件 ——
    与其事后检查「有没有人用了 uvloop」（时序上拦不住先装门后导入），不如直接
    关死这扇门。本 venv 的 uvloop 全仓零引用，误伤面为零；若未来确需 uvloop，
    必须连本门一起重新设计（下沉到 uvloop/OS 层）。
    """
    if "uvloop" not in sys.modules:
        sys.modules["uvloop"] = None  # type: ignore[assignment] — import 时即 ImportError
        for mod_name in [m for m in sys.modules if m.startswith("uvloop.")]:
            sys.modules[mod_name] = None  # type: ignore[assignment]


def install() -> None:
    """装门（audit hook 承重 + belt 身份锚点 + uvloop 毒化 + 最终总账）。

    幂等，且**每次调用都复核身份**：第八批 Codex HIGH 实测「装门 → 把
    ``connect`` 恢复成原函数 → 再 ``install()``」得到 ``installed=True`` 而
    ``connect_guarded=False``——只信布尔值的 install 会把已被拆掉的门当成在位。
    这里改成：已装过就走 :func:`assert_guard_live`，漂移即抛 :class:`GuardDrift`。

    ⚠️ 装=不卸：本门**只装不卸**。audit hook 本身就不可摘（CPython 无
    ``sys.removeaudithook``）；belt 的 :func:`uninstall` 仅为 API 完整保留，
    生产代码路径不调用。CLI 测试进程的迟到线程在 ``pytest_unconfigure`` 之后
    仍可能发起连接，先恢复 socket 会留下无账窗口——门随进程存活到退出。
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
    if os.environ.get(ENV_REQUIRE_BLOCKED_TARGET) == "1":
        assert_neo4j_target_blocked()
    _install_audit_hook()
    register_final_accounting()
    if STATE.installed:
        assert_guard_live("install(已装过，复核身份)")
        return
    base = _socket_mod.socket
    STATE._orig_connect = base.connect
    STATE._orig_connect_ex = base.connect_ex
    base.connect = _guarded_connect  # type: ignore[method-assign]
    base.connect_ex = _guarded_connect_ex  # type: ignore[method-assign]
    STATE.installed = True
    assert_guard_live("install(首次)")


def uninstall() -> None:
    """仅恢复 belt 的形状；**承重的 audit hook 摘不掉**（CPython 无 removeaudithook）。

    CLI 测试进程刻意不调用（见 :func:`install` 的 ⚠️ 说明）。
    """
    if not STATE.installed:
        return
    base = _socket_mod.socket
    base.connect = STATE._orig_connect  # type: ignore[method-assign]
    base.connect_ex = STATE._orig_connect_ex  # type: ignore[method-assign]
    STATE.installed = False


# ═══════════════════════════════════════════════════════════════════════════
# 自证（安装时 + 每个用例边界）
# ═══════════════════════════════════════════════════════════════════════════


def audit_hook_alive() -> bool:
    """行为级验证：把一枚一次性 token 送进 audit 子系统，看它是否回到本模块。

    这不是读布尔值——token 没回来就说明 :func:`_audit_hook` 已不在 hook 链上
    （或被替换成了别的对象）。CPython 不提供枚举 audit hook 的 API，
    round-trip 是唯一能**证明**而不是**声明**在位的方式。
    """
    global _selftest_counter
    with _selftest_lock:
        _selftest_counter += 1
        token = f"w4-selftest-{os.getpid()}-{_selftest_counter}"
    _SELFTEST_INBOX.clear()
    sys.audit(_SELFTEST_EVENT, token)
    seen = token in _SELFTEST_INBOX
    _SELFTEST_INBOX.clear()
    return seen


def assert_guard_live(context: str = "") -> None:
    """门在位自证：audit 承重层 + belt 身份 + uvloop 毒化。漂移即 fail-closed。

    调用点：:func:`install`（每次）、根 conftest 的 session fixture、以及**每个
    用例边界**（``pytest_runtest_protocol`` 的进入与退出）。
    """
    where = f"（{context}）" if context else ""
    if not _AUDIT_INSTALLED:
        raise GuardDrift(f"承重 audit hook 从未安装{where}")
    if not audit_hook_alive():
        raise GuardDrift(
            f"承重 audit hook 已不在链上{where}：selftest token 未回到本模块。"
            "CPython 无 removeaudithook，出现本错误说明 sys.audit 被替换或本模块被重载。"
        )
    if not REQUIRED_BLOCKED_PORTS <= set(BLOCKED_PORTS):
        raise GuardDrift(
            f"受拦端口集被缩小{where}：当前 {sorted(BLOCKED_PORTS)}，"
            f"必须覆盖 {sorted(REQUIRED_BLOCKED_PORTS)}。把现网端口从集合里摘掉 = 拆门。"
        )
    if not STATE.installed:
        raise GuardDrift(f"belt 未安装{where}（install() 未跑？）")
    base = _socket_mod.socket
    if base.connect is not _guarded_connect:
        raise GuardDrift(
            f"socket.socket.connect 身份漂移{where}：当前是 {base.connect!r}，"
            f"期望 {_guarded_connect!r}。有人把高层 connect 换掉了。"
        )
    if base.connect_ex is not _guarded_connect_ex:
        raise GuardDrift(
            f"socket.socket.connect_ex 身份漂移{where}：当前是 {base.connect_ex!r}，期望 {_guarded_connect_ex!r}。"
        )
    # 只查毒化这条**承重**证据：本函数会在每个用例边界跑，不适合每次都去动
    # warnings 的全局过滤器（``assert_not_uvloop`` 里的 policy 复核会）。完整的
    # policy 复核由 session fixture 单独调 :func:`assert_not_uvloop` 承担。
    if sys.modules.get("uvloop") is not None:
        raise GuardDrift(f"uvloop 毒化被绕过{where}：uvloop 走 libuv，不触发 socket.connect 审计事件。")


def assert_not_uvloop() -> None:
    """session 级复核：uvloop 已被 :func:`poison_uvloop` 关死。

    import 失败毒化 + policy 复核双保险；policy 拿不到时不算证据失败
    （3.14 起 get_event_loop_policy 已 deprecated），毒化才是承重防线。
    """
    if sys.modules.get("uvloop") is not None:
        raise RuntimeError(
            "uvloop 已在本进程被导入：uvloop 走 libuv，不触发 CPython 的 "
            "socket.connect 审计事件，门会静默失效。install() 应当已把 uvloop "
            "毒化——出现本错误说明毒化被人绕过（例如 install 前已被 import）。"
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


def assert_neo4j_target_blocked() -> None:
    """要求 ``NEO4J_URI`` 指向**受拦端口**，否则拒绝装门（负控专用，默认关闭）。

    第八批 Codex BLOCKER 的结构性收口：本门只按端口判定，射程之外的库它拦不住。
    负控要做的事是「摘掉隔离，看门拦不拦」——如果此时 ``NEO4J_URI`` 指向的是
    7691/7687 之外的某个真库，那么「摘掉隔离」会**真的连上去**，脚本只会事后
    因 ``blocked=0`` 报失败，而实害已经发生。

    所以负控用 ``W4_GUARD_REQUIRE_BLOCKED_TARGET=1`` 打开本检查：目标不在射程内
    就在**任何测试跑起来之前**拒绝装门。检查读的是 **环境变量**（负控显式钉死的
    那一份），不是 ``Settings``——本模块刻意不 import ``app.*``，装门必须早于任何
    业务 import。负控另有一道 ``Settings`` 侧的前置自检（见负控脚本 step 0c），
    两边口径一致才放行。
    """
    uri = os.environ.get("NEO4J_URI")
    if not uri:
        raise RuntimeError(
            f"{ENV_REQUIRE_BLOCKED_TARGET}=1 但 NEO4J_URI 未设置：无法证明连接目标在门的射程内，拒绝装门。"
        )
    port = _port_of_uri(uri)
    if port is None:
        raise RuntimeError(f"{ENV_REQUIRE_BLOCKED_TARGET}=1 但 NEO4J_URI={uri!r} 解析不出端口，拒绝装门。")
    if port not in BLOCKED_PORTS:
        raise RuntimeError(
            f"{ENV_REQUIRE_BLOCKED_TARGET}=1 但 NEO4J_URI={uri!r} 指向端口 {port}，"
            f"不在受拦集合 {sorted(BLOCKED_PORTS)} 内 —— 摘掉隔离后会真实连接该库，拒绝装门。"
        )


def _port_of_uri(uri: str) -> int | None:
    """从 ``bolt://[user:pass@]host:port[/path]`` 取端口。

    解析不出来返回 None —— 调用方 :func:`assert_neo4j_target_blocked` 对 None
    一律 fail-closed（拒绝装门），所以「解析器看不懂的 URI」不会变成放行。
    """
    tail = uri.split("://", 1)[1] if "://" in uri else uri
    tail = tail.split("/", 1)[0]  # 去掉 path/query
    tail = tail.rpartition("@")[2] or tail  # 去掉 userinfo（其中可能含 ':'）
    if tail.startswith("["):  # IPv6 字面量 [::1]:7691
        tail = tail.partition("]")[2]
    if ":" not in tail:
        return None
    port_str = tail.rsplit(":", 1)[1]
    try:
        return int(port_str)
    except ValueError:
        return None


# ═══════════════════════════════════════════════════════════════════════════
# 最终总账（所有 cleanup / atexit 之后）
# ═══════════════════════════════════════════════════════════════════════════

_FINAL_REGISTERED = False


def register_final_accounting() -> None:
    """注册最终总账。``atexit`` 是 LIFO —— 本函数在 :func:`install` 里最早调用，
    所以本处理器**最后**执行，位于 pytest 的全部清理与其它 ``atexit`` 之后。
    """
    global _FINAL_REGISTERED
    if _FINAL_REGISTERED:
        return
    atexit.register(_final_accounting)
    _FINAL_REGISTERED = True


def write_ledger(path: str) -> None:
    """把账本写到 ``path``（父进程独立复核用）。写失败不静默——直接抛。"""
    ledger = STATE.ledger()
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(ledger, fh, ensure_ascii=False, indent=2)


def _final_accounting() -> None:
    """最后一道结账：任何未结账的拦截都必须让进程以非零 rc 结束。

    第八批 Codex HIGH：``pytest_cmdline_main`` 返回之后还有 pytest 自身的清理、
    其它 ``atexit`` 处理器和迟到线程 —— 那段窗口里被拦下的连接会被记账，进程
    却仍然 ``exit 0``，于是「任何未结账尝试都令测试失败」这句承诺不成立。
    """
    ledger = STATE.ledger()
    path = os.environ.get(ENV_LEDGER)
    if path:
        try:
            write_ledger(path)
        except Exception as exc:  # noqa: BLE001 —— 落盘失败要说话，但不能盖掉结账
            print(f"*** W4 guard: 账本落盘失败 {path}: {exc!r} ***", file=sys.stderr)
    unaccounted = ledger["unaccounted"]
    blocked = ledger["blocked"]
    status = ledger["reported_status"]
    # status is None ⇒ 不是 pytest 跑的（脚本/探针直接 import 本模块）：按 0 处理，
    # 也就是「有非豁免拦截却打算正常退出」同样算失败。
    effective_status = 0 if status is None else status
    if unaccounted > 0 or (blocked > 0 and effective_status == 0):
        print(
            f"\n*** {BLOCK_REASON} —— 最终总账：blocked={blocked} "
            f"unaccounted={unaccounted} reported_status={status}；"
            f"进程被强制以退出码 {FINAL_EXIT_CODE} 结束（迟到连接不得以 0 收场）***",
            file=sys.stderr,
        )
        for rec in ledger["unaccounted_records"]:
            print(f"    - {rec['address']} on thread {rec['thread']} (owner={rec['owner']})", file=sys.stderr)
        try:
            sys.stdout.flush()
            sys.stderr.flush()
        except Exception:  # noqa: BLE001
            pass
        os._exit(FINAL_EXIT_CODE)


# ═══════════════════════════════════════════════════════════════════════════
# pytest 接线（由根 conftest 调用）
# ═══════════════════════════════════════════════════════════════════════════


def is_exempt(item, tests_dir) -> tuple[bool, str]:
    """该用例是否豁免（只记不拦）。返回 (豁免, 依据)。

    ``tests_dir`` = backend/tests 的绝对路径（由 conftest 传入 ``Path(__file__).parent``）。
    路径判定用 **相对化后的首段目录**，不做整条路径的 substring——
    ``/tmp/tests/integration/...`` 之类的绝对路径不得误判（Codex round-1 MEDIUM）。

    ``W4_GUARD_NO_EXEMPT=1``（负控）时**一律不豁免**。
    """
    if exempt_disabled():
        return False, "no-exempt-mode"
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
