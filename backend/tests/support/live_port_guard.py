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
4. **最终结算**（:func:`register_final_accounting` 注册的 ``atexit``）——
   ``pytest_cmdline_main`` 返回之后仍有 cleanup / ``atexit`` / 迟到线程的窗口
   （第八批 Codex HIGH 实测：那段窗口里的拦截被记账、进程却仍 exit 0）。本层发现
   未结账的拦截就 ``os._exit(3)``，并把账本落到 ``W4_GUARD_LEDGER`` 指定的文件
   供父进程独立复核。
   ⚠️ 本层**不是**「在所有 atexit 之后」跑（R1 Codex HIGH 打回的过宽表述）：
   ``atexit`` 是 LIFO，本模块 import **之前**就注册的回调排在本层**后面**。
   所以本层进入时立刻置不可逆的结算标志（:meth:`_GuardState.finalize_and_snapshot`），
   此后 audit hook 命中受拦端口就**就地** ``os._exit(3)`` —— 不再依赖任何后续结账机会。

## 结算必须是原子的（CARD-W4-4，2026-09-05）

上面第 4 层曾经**自己就是一处假绿**。旧实现把「置结算标志」与「取账本快照」写成
两条独立语句（``_FINALIZING = True`` 之后才去取账本快照），而 audit hook 对
那个标志是**锁外读**、``STATE.record()`` 又在另一把锁里。于是存在一个夹缝：

    迟到线程读到「尚未结算」──► 主线程置位并取完快照 ──► 迟到线程才落账

这条 blocked 记录**既不在快照里**（裁定看不见 ⇒ 不 ``os._exit(3)``），**又没走迟到
路径**（标志读的是置位之前的值）⇒ 进程 ``exit 0``；hook 在非主线程抛的
``RuntimeError`` 被吞，无人看见。2026-09-05 于本车道实测复现（证据
``_bmad-output/审查/evidence-w4-4/before-repro.py`` 的 ``before-1``）。

同一条竞态还有第二个观察面：裁定读 ``_final_accounting`` 自己取的快照，落盘却读
``write_ledger`` **另外再取一次**的快照。记录落在两次之间时，账本文件写着
``unaccounted=1`` 而进程 ``rc=0`` —— 父进程复核与子进程裁定互相打脸（``before-2``）。

现在两条都收在同一把锁里：

* :meth:`_GuardState.finalize_and_snapshot` 在**同一次持锁**内置标志 + 取快照；
* :meth:`_GuardState.record` 在**同一把锁**内先看结算标志，已结算就返回
  :data:`RECORD_LATE`（并照常进账 ⇒ 该记录必然是 ``unaccounted``）。

所以一条记录只有两种归宿，没有第三种：``record`` 先拿到锁 ⇒ 它在快照里；
``finalize_and_snapshot`` 先拿到锁 ⇒ 它被判迟到、hook 就地 ``os._exit(3)``。
裁定与落盘从此用**同一个** dict（:func:`write_ledger` 接收快照），迟到路径在退出前
把含迟到记录的账本**重写**一次，保证 **账本 ``unaccounted>0`` ⇒ ``rc=3``**。

⚠️ 这是**单向**的，反向不成立（原文写「双向成立」是过宽表述，2026-09-08 撤回）：
:func:`_final_accounting` 的退出判据还有第二个分支 —— ``blocked > 0`` 且原本的
``reported_status`` 为 0 时同样退 3，而那种形态下 ``unaccounted`` 可以是 0。
父进程复核 rc=3 时该读的是 ``blocked`` 与 ``unaccounted`` 两个字段，不能只看后者。

⛔ 这里刻意**没有** sleep / 重试 / 「多取一次快照」—— 那些只会把窗口变窄，
不会让它消失，而变窄的窗口比明显的窗口更难被门抓住。

## 归属模型（线程安全 + 未知来源 fail-closed）

当前用例的归属信息放 **ContextVar**（不是共享字段）：主线程在
``pytest_runtest_protocol`` 边界 set/reset，TestClient 的 anyio portal 线程会携带
上下文副本，所以 portal 里发起的连接能记到发起用例名下。**不带上下文的裸线程**
（``threading.Thread`` 直启）看到的是默认值 → 归 ``<unknown>`` 且**永不豁免** →
fail-closed。

## 环境开关只有一个方向

本模块读三个环境变量，**没有任何一个能把门打开**：

* ``W4_GUARD_NO_EXEMPT=1`` —— 关掉 integration/e2e 的豁免（更严）；
* ``W4_GUARD_REQUIRE_BLOCKED_TARGET=1`` —— 目标端口不在射程内就**拒绝装门**（更严；
  拒的是 belt / ``STATE.installed`` —— 此刻 audit hook 与 atexit 结算器**已生效且摘
  不掉**：零账时不改退出码，有未结账的拦截则强制退 3，见 :func:`install`）；
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
  ``socket.connect`` 审计事件。承重的关门方式是 audit 的 ``import`` 事件——
  ``import uvloop`` 直接抛（摘不掉）；``sys.modules`` 毒化只是让错误更早更清楚
  （R1 Codex HIGH：毒化条目可以被 ``del`` 掉再 import，所以它不能当承重）。
* **本门只覆盖 CPython 的 socket API**。绕过 CPython 直接调 libc 的路径
  （``ctypes.CDLL(None).connect(...)`` 或原生扩展自己发 syscall）不触发审计事件，
  本门看不见。当前 neo4j 驱动走的是 CPython socket，故按「防手滑」的威胁模型
  这条属于已声明边界；要覆盖它必须下沉到 OS 层出站约束。
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

#: ``NEO4J_TEST_URI`` 允许指向的端口 —— **正面白名单**，默认拒绝一切其它值。
#:
#: ⛔ 为什么这里是白名单而 :data:`BLOCKED_PORTS` 仍是黑名单（两者**语义不同、
#: 各管各的**，别把它们统一）：
#:
#: * 本白名单只管一件事：``NEO4J_TEST_URI`` 这个**配置值**指向哪里。配置只有
#:   一个正确答案（测试容器 7692），所以「默认拒绝 + 列出唯一允许项」是对的。
#:   X4 两轮独立终审的 BLOCKER 正是黑名单式判据挡不住的：``bolt://127.0.0.1:0``
#:   端口既非 None 又不在黑名单里 ⇒ 放行，而驱动会把 ``:0`` 归一成 **7687**
#:   （现网默认端口），再经 :func:`is_exempt` 的 integration/e2e advisory 真连开发库。
#:   黑名单要挡住它，就得枚举 0、00、空、以及一切会被驱动归一成 7687 的写法 ——
#:   那是「枚举白名单」式的必输游戏，方向反了。
#: * :data:`BLOCKED_PORTS` 管的是 :func:`_audit_hook` 里**每一次 socket.connect**。
#:   那里**绝不能**改成白名单：测试进程要连的本地端口远不止 7692 ——
#:   Ollama ``localhost:11434``（``app/config.py:531``）、``tests/contract/
#:   test_pact_provider.py``、``tests/unit/test_embedder_factory.py`` 都会连
#:   非 7692 的本地端口，探针自己还会临时往受拦集合里加端口（见上）。
#:   在 hook 上做白名单 = 把整个测试套件的出站流量一并拦死。
#: * 黑名单常量还是 :func:`audit_hook_alive` / :func:`assert_guard_live` 的自证
#:   锚点，取值动不得（详见那两处）。
#:
#: 允许往里加端口的唯一场景是「又起了一个测试容器」，且必须同步更新
#: :func:`assert_test_uri_not_blocked` 的探针与契约测试 —— 探针
#: ``guard-allowed-test-ports-cannot-admit-live`` 钉死了「把 7687 加进白名单仍必须拒」。
ALLOWED_TEST_PORTS = frozenset({7692})

#: neo4j 驱动对「没写端口 / 端口为 0」时使用的默认端口。
#: 来源不是文档而是实现：``neo4j/_sync/driver.py::_Direct._default_port``，
#: 由 ``_parse_target`` 传给 ``Address.parse(default_port=…)``；
#: ``neo4j/_addressing.py`` 里 ``port = port or default_port or 0`` ——
#: ``int("0")`` 是 falsy，所以 ``:0`` 和 ``:00`` 都会落到这个默认值上。
#: 它恰好等于 :data:`BLOCKED_PORTS` 里的现网默认端口，这正是 BLOCKER 的要害。
_DRIVER_DEFAULT_PORT = 7687
_DRIVER_DEFAULT_HOST = "localhost"

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

#: :meth:`_GuardState.record` 的三种归宿。**在同一把锁内**判定，调用方按此分流 ——
#: 这是 CARD-W4-4 的要害：旧实现让 audit hook 在锁外先读一次结算标志、再进锁记账，
#: 两次之间的夹缝能让一条 blocked 记录既不进快照、又不触发迟到路径。
RECORD_ADVISORY = "advisory"  #: 豁免用例，只记不拦
RECORD_BLOCK = "block"  #: 非豁免，调用方抛 RuntimeError（连接不发生）
RECORD_LATE = "late"  #: 最终结算的快照已取走，调用方就地 ``os._exit(FINAL_EXIT_CODE)``


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


#: 取账本快照的**全进程单调序**。每取一次快照 +1，于是任意两份快照都能比出「谁取得
#: 更晚」—— 账本落盘的发布顺序就靠它（见 :func:`_publish_ledger`）。
#:
#: 用模块级而不是实例级：契约测试里每个用例新建一份 :class:`_GuardState`，实例级计数
#: 会让不同 state 的序号撞车，比不出先后。
_SNAPSHOT_SEQ = 0
#: 只保护 :data:`_SNAPSHOT_SEQ` 的**叶子锁**：它自己不再取任何别的锁，所以在
#: ``_GuardState._lock`` 里面取它不可能成环（锁序固定：``_lock`` → ``_SEQ_LOCK``）。
_SEQ_LOCK = threading.Lock()


def _next_snapshot_seq() -> int:
    """取下一个快照序号（全进程单调递增，从 1 起）。"""
    global _SNAPSHOT_SEQ
    with _SEQ_LOCK:
        _SNAPSHOT_SEQ += 1
        return _SNAPSHOT_SEQ


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
        #: 「已进入最终结算」的不可逆标志。**受 ``self._lock`` 保护** —— 置位与取
        #: 账本快照必须在同一次持锁内完成（见 :meth:`finalize_and_snapshot`），
        #: 且 :meth:`record` 在同一把锁内读它。任何锁外读写都会把 CARD-W4-4 修掉的
        #: 那个夹缝重新打开。
        self.finalizing = False
        #: 结算快照取走**之后**才落地的拦截数（这些记录必然无人结账）。
        self.late = 0
        #: ``NEO4J_TEST_URI`` 白名单预检是否已完成。未完成前 :func:`begin_item`
        #: **不发豁免票**（fail-closed，见那里的说明）。
        self.precheck_done = False

    # ── 记账 ────────────────────────────────────────────────────────────
    def record(self, address) -> str:
        """记一次到受拦端口的连接尝试。返回 :data:`RECORD_ADVISORY` /
        :data:`RECORD_BLOCK` / :data:`RECORD_LATE` 之一。

        ⛔ **结算判定必须在这把锁里**（CARD-W4-4）。旧实现由 audit hook 在锁外先读
        一次模块级 ``_FINALIZING``、再调本方法进锁记账；两次之间主线程可以完成
        「置位 + 取快照」，于是这条记录既不在快照里、又没被判成迟到 ⇒ 进程 exit 0。
        现在结算标志与账本在同一把锁下，一条记录只有两种归宿：在快照里，或者被判
        :data:`RECORD_LATE`。没有第三种。

        迟到记录**照常进账**（``total`` / ``blocked`` / ``pending`` 都加），所以它必然
        体现为 ``unaccounted`` —— 迟到路径重写账本后，**账本 ``unaccounted>0`` ⇒
        ``rc=3``**，父进程按账本复核不会与子进程 rc 打架。反向不成立：``rc=3`` 也可能
        来自 :func:`_final_accounting` 的第二个分支（``blocked>0`` 且原 rc=0），那时
        ``unaccounted`` 可以是 0（2026-09-08 撤回原「两个方向都成立」的过宽表述）。
        迟到路径**不看豁免**：结算之后已经没有任何一层能把 advisory 变成非零 rc，
        「只记不拦」在这一刻等于「什么都没做」（旧实现的 ``if _FINALIZING`` 同样
        不看豁免，语义未变）。
        """
        owner = _OWNER_CV.get()
        exempt = _EXEMPT_CV.get()
        gen = _GEN_CV.get()
        # ⛔ 地址的 ``repr`` 必须在**锁外**算（Codex round-1 MEDIUM-8）。``address``
        #    完全由调用方提供，``__repr__`` 是任意用户代码：
        #      * 它若回调 :meth:`ledger` / :meth:`unaccounted_blocked`，就会再取同一把
        #        **不可重入**的 ``self._lock`` ⇒ 自死锁，表现为「进程挂住」；
        #      * 它若抛异常，异常会从**计数之前**逃出去 ⇒ 这次尝试整条不进账。
        #    锁内只放一个已经算好的字符串，上面两条都被挡在临界区外面。
        #    （格式化细节与 ``BaseException`` 的理由见 :func:`_safe_repr`。）
        addr_text = _safe_repr(address)
        with self._lock:
            stale = gen != self.current_gen
            if stale or self.finalizing:
                # 过期 context 副本（用例已结束/豁免已被撤销）—— fail-closed；
                # 结算之后同理：归属早已复位，豁免也不再有意义。
                owner = _UNKNOWN_OWNER
                exempt = False
            rec = {
                "address": addr_text,
                "thread": threading.current_thread().name,
                "owner": owner,
                "exempt": exempt,
            }
            self.total += 1
            self.records.append(rec)
            if self.finalizing:
                self.late += 1
                self.blocked += 1
                self.pending.setdefault(owner, []).append(rec)
                return RECORD_LATE
            if exempt:
                self.advisory += 1
                return RECORD_ADVISORY
            self.blocked += 1
            self.pending.setdefault(owner, []).append(rec)
            return RECORD_BLOCK

    def finalize_and_snapshot(self) -> dict:
        """**同一次持锁内**：置不可逆结算标志 + 取账本快照。返回该快照。

        这两步之间不允许有任何间隙 —— 有间隙就等于 CARD-W4-4 修掉的那个缺陷。
        返回的 dict 是**结算路径唯一的一份**：裁定读它、落盘也写它
        （:func:`write_ledger` 接收它），两者不可能分叉。

        ``self._lock`` 不可重入（见 :meth:`_unaccounted_locked`）⇒ 这里只能调
        ``_ledger_locked()``，绝不能调会自己取锁的 :meth:`ledger`。
        """
        with self._lock:
            self.finalizing = True
            return self._ledger_locked(stamp=True)

    def late_snapshot(self) -> dict:
        """迟到路径用的账本快照：结算快照之后落地的记录**也在里面**。

        用于在 ``os._exit(FINAL_EXIT_CODE)`` 之前把账本文件重写一次 —— 否则文件里
        会是结算那一刻的空账，而进程 rc=3，父进程复核与子进程裁定又打起来。

        带发布序（``stamp=True``）：这一份**一定**比结算那份取得晚，序号也就一定更大，
        于是结算线程手上的旧快照再也盖不回来（见 :func:`_publish_ledger`）。
        """
        with self._lock:
            return self._ledger_locked(stamp=True)

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
        """账本快照（公共读接口）。

        ⚠️ **结算路径不走这里**：那条路上快照只能取一次，由
        :meth:`finalize_and_snapshot` 产出（见 CARD-W4-4）。本方法留给「随手看一眼
        当前账面」的调用方（契约测试、独立调用 :func:`write_ledger` 的场景）。
        """
        with self._lock:
            return self._ledger_locked()

    def _ledger_locked(self, *, stamp: bool = False) -> dict:
        """``self._lock`` 已持有的前提下取账本快照（不可重入锁，禁止嵌套获取）。

        字段名是**对外契约**：父进程复核脚本、``test_ledger_shape``、探针
        ``ledger-written`` 都按名读，别改。

        ``stamp=True`` 时额外带一个 ``seq`` —— CARD-W4-4b 新增的**发布序**（全进程单调，
        取快照即定）。它让 :func:`_publish_ledger` 判得出「我手上这份是不是已经过时了」：
        结算线程取了零账快照、迟到线程随后记账并把含迟到记录的账本写进文件，结算线程
        再拿旧快照 ``open(path,"w")`` 就会把它盖回零账（Codex round-1 MEDIUM-4）。

        ⛔ 只有**要发布的**快照才盖序号（:meth:`finalize_and_snapshot` /
        :meth:`late_snapshot`）。:meth:`ledger` 这种「随手看一眼账面」的读**不盖** ——
        否则一次纯读取也会推进发布序，探针 ``guard-finalize-seam-inert-when-unset``
        的「前后账本逐字节相同」当场变成恒假（2026-09-08 实测：加进无条件路径后它转红，
        那是本设计的错，不是那道判据该让路）。
        """
        unaccounted = self._unaccounted_locked()
        ledger: dict = {
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
        if stamp:
            ledger["seq"] = _next_snapshot_seq()
        return ledger

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
    """标记「现在起到 end_item 之间的连接归属 owner」（ContextVar，portal 线程可见）。

    ⛔ **预检未完成 ⇒ 不发豁免票**（T-10，CARD-W4-4）。``assert_test_uri_not_blocked``
    原来跑在 session autouse fixture 里，而 session fixture 的 setup 跑在**首个用例的**
    ``pytest_runtest_protocol`` 之内 —— 也就是 ``begin_item(exempt=True)`` **之后**。
    首个被收集的用例若在 ``tests/integration`` / ``tests/e2e``（自动豁免），那么预检
    整段（含它的延迟 ``import neo4j``）都落在 advisory 窗口里：那段时间到现网端口的
    连接只被记录、不被拦，而它恰恰是「测试容器 URI 有没有指向现网库」还没被证明的
    时候。2026-09-05 实测（``evidence-w4-4/before-repro.py`` 的 ``before-4``）：
    session fixture 执行时 ``_EXEMPT_CV`` 确实是 ``True``。

    结构性修法是把预检上移到 ``pytest_configure``（``tests/conftest.py`` /
    ``tests/support/guard_plugin.py``），那时根本还没有任何用例作用域。本处是配套的
    **闩**：即使有人把预检挪回去、或者某条路径绕过了 ``pytest_configure``，
    「预检没完成就享受豁免」这件事也不会发生。

    ⚠️ 如实声明的收紧：预检完成之前的用例**一律不豁免**。上移之后正常 pytest 会话
    里这个状态不会出现（``pytest_configure`` 早于一切用例），所以它是一道纵深，
    不是日常路径。
    """
    with STATE._lock:
        if not STATE.precheck_done:
            exempt = False
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

    ⛔ **tuple 子类要读底层槽位，不能拒绝，也不能走它的重载方法**
    （X4 §7.10 A 类 HIGH #2 + round-1 Codex HIGH，本卡两次修才对）：

    ``len(address)`` / ``address[1]`` 走的是可被子类重载的 ``__len__`` /
    ``__getitem__``，而 CPython 的 socket 读的是**底层槽位** —— 覆写
    ``__getitem__`` 让它对我们返回安全端口、对 C 层仍是 7691，就能让 guard 判安全
    而连接照常发出。

    ⚠️ 本卡第一版的修法是「tuple 子类一律不可信」，**错了，而且误拦真流量**：
    neo4j 驱动自己的地址类 ``neo4j._addressing.Address``（``IPv4Address`` /
    ``ResolvedIPv4Address`` …）**就是 tuple 子类**，且
    ``_async_compat/network/_bolt_socket.py`` 直接 ``s.connect(resolved_address)``
    —— 一律拒绝会把**合法的 7692 测试容器连接**当场拦掉（2026-09-05 实测：
    ``Address.parse('127.0.0.1:7692')`` 经本 hook 抛 RuntimeError）。
    当时的注释还写着「Python 层读不到 C 层看见的那个值」—— 这句同样是错的，
    ``tuple.__getitem__(addr, 1)`` 就读得到（契约测试自己就在用它）。

    正解是**绕开重载、直接读底层槽位**：``tuple.__len__`` / ``tuple.__getitem__``
    拿到的就是 C 层 sockaddr 构造时会看到的那个对象，伪装子类骗不过它，
    真驱动的地址类也照常工作。
    """
    if not isinstance(address, tuple):
        return None
    try:
        if tuple.__len__(address) < 2:
            return None
        raw = tuple.__getitem__(address, 1)
    except Exception:  # noqa: BLE001 —— 连底层槽位都读不到 ⇒ 取不到端口
        return None
    try:
        return operator.index(raw)
    except Exception:  # noqa: BLE001 —— 见下：这里只能 fail-closed，不能让异常逸出
        # ⛔ 必须与上面读槽位那半**同口径**（RV-C H-1a）。原来只捕 ``TypeError``：
        #    ``__index__`` 是调用方给的任意用户代码，它抛 ``ValueError`` /
        #    ``RuntimeError`` 时异常会从这里逸出 —— 而本函数的唯一调用点
        #    :func:`_audit_hook` 是在 ``STATE.record()` **之前**调它的，于是那次尝试
        #    连接确实被阻断了（异常传给调用方），账本却是零。与 round-1 HIGH-1
        #    「seam 抛异常跳过记账」同型：**任何在记账之前执行用户代码的地方都得
        #    fail-closed**。取不到端口 ⇒ 返回 None ⇒ ``port_is_trustworthy`` 随后判
        #    不可信 ⇒ 照样走受拦分支、照样进账，没有放宽任何东西。
        return None


def port_is_trustworthy(address) -> bool:
    """端口值能否被**二次求值**信任。

    R1 Codex LOW-17 实测的 TOCTOU：一个有状态的 ``__index__``（第一次返回受拦
    端口给 CPython 构造 sockaddr，第二次返回 1 给本 hook）能让连接建立而账本为零。
    审计事件拿到的是**同一个对象**，我们的 ``operator.index()`` 是**第二次**求值。

    因此凡端口不是**真正的 int**（``type(port) is int``；``bool`` 也不算，它虽是
    int 子类但当端口毫无意义）一律视为不可信 —— 调用方按受拦处理（fail-closed）。
    这会连带拦掉「用奇怪端口对象连非受拦端口」的写法；那种写法在本仓库不存在，
    宁可误拦也不给 TOCTOU 留口子。

    ⛔ **端口一律从底层槽位读**（X4 §7.10 A 类 HIGH #2 + round-1 Codex HIGH）：
    地址是 tuple **子类**时，``len(address)`` / ``address[1]`` 走的是可重载的
    ``__len__`` / ``__getitem__``，而 CPython 的 socket 读的是**底层槽位** ——
    覆写 ``__getitem__``（对本 hook 返回 1、对 C 层仍是 7691）就能让 guard 判安全
    而连接照常建立，与那个有状态 ``__index__`` 的 TOCTOU 同型但更好写。

    ⚠️ 本卡第一版写成「tuple 子类一律不可信」，**误拦真流量**：neo4j 驱动的
    ``Address`` 家族就是 tuple 子类，且直接被 ``s.connect()`` 使用。
    详见 :func:`extract_port` 的说明。现在两个函数都用
    ``tuple.__len__`` / ``tuple.__getitem__`` 绕开重载读底层槽位 —— 伪装骗不过，
    真驱动也不误伤。
    """
    if not isinstance(address, tuple):
        return True  # 非元组地址（AF_UNIX 等）不在射程，不谈可信不可信
    try:
        if tuple.__len__(address) < 2:
            return True  # 长度不足 —— 不在射程
        raw = tuple.__getitem__(address, 1)
    except Exception:  # noqa: BLE001 —— 底层槽位都读不到 ⇒ 不可信，fail-closed
        return False
    return type(raw) is int  # noqa: E721 —— 必须是精确 int，子类（含 bool）不算


def _safe_repr(address) -> str:
    """对**不可信的**地址对象做 ``repr``，任何异常都不得逃出去（MEDIUM-8）。

    ``address`` 完全由调用方给，``__repr__`` 是任意用户代码：

    * 在 :meth:`_GuardState.record` 里，它在 ``self._lock`` **之外**跑 —— ``__repr__``
      若回调 :meth:`ledger` 会再取同一把**不可重入**的锁 ⇒ 自死锁；若抛异常，会从
      ``total += 1`` **之前**穿出去 ⇒ 这次尝试整条不进账（与 HIGH-1 修掉的
      「跳过记账的旁路」同形）。
    * 在 :func:`_block_message` 里，它决定拒因文本 —— 裸 ``{address!r}`` 会被
      恶意 ``__repr__`` 劫持：逃出 hook 的成了 ``__repr__`` 自己的异常而不是含
      ``BLOCK_REASON`` 的 ``RuntimeError``，「红得是因为这件事」的绑定断裂
      （父进程 / 探针全按 ``BLOCK_REASON in str(e)`` 判拒因身份）。

    捕 ``BaseException``：从 ``__repr__`` 逃出的**任何**东西（含 ``KeyboardInterrupt``）
    都会破坏上面两条；退化串本身再包一层，免得兜底路径自己抛。
    """
    try:
        return repr(address)
    except BaseException:  # noqa: BLE001 —— 可观测性不得挡住记账/拒因绑定
        try:
            return f"<unrepr {type(address).__name__}>"
        except BaseException:  # noqa: BLE001 —— 同上
            return "<unrepr>"


def _block_message(address) -> str:
    return (
        f"{BLOCK_REASON}: {_safe_repr(address)}. "
        f"受拦端口 {sorted(BLOCKED_PORTS)} 是现网 Neo4j；测试进程不得连接。"
        f"若这是端点测试，请用 backend/tests/support/lifespan.py::no_lifespan "
        f"关掉 app.main 的 lifespan；若确需真库，用测试容器 "
        f"NEO4J_TEST_URI(7692) 并打 integration/real_neo4j marker。"
    )


class _SelfTestBlocked(RuntimeError):
    """自证探针被承重路径拦下时抛出的私有异常（不进账本）。"""


#: 自证专用的哨兵主机名。含 NUL 字节，**不可能**是任何真实 connect 的目标
#: （CPython 的 socket 会对含 NUL 的主机名报错），所以它不会与真实流量混淆。
_SELFTEST_HOST = "\x00w4-live-port-guard-selftest"


def _finalize_race_seam() -> None:
    """**默认 no-op**。存在的唯一理由是让「结算竞态」可以被**确定性**地复现。

    ⛔ 关于这个注入点的完整声明（Codex 请单独审这一处）：

    * :func:`_audit_hook` 在**进入非自证的受拦分支之后无条件**调用它 —— 那一层里
      没有 ``if``、不读任何环境变量、不 sleep（措辞按 Codex round-1 收窄：不是
      「hook 一进来就调」，自证地址与非受拦端口都到不了这里）。未被替换时它就是一次
      no-op 函数调用，**不出现在任何判据里**；
    * 它的返回值被丢弃，**且整个调用被 ``try/except BaseException`` 包住**
      （Codex round-1 HIGH-1 的处置）⇒ 它对控制流的影响面是 **0**：不能把「该拦的」
      变成「放行」，也不能靠抛异常跳过记账。被替换后它唯一能做的是**延迟**，
      以及「自己结束进程」这种任何同进程代码都能做的事；
    * 位置在 ``STATE.record()`` **之前**。修好之后 hook 里已经没有「先读结算标志、
      再记账」这个间隙了（判定进了 ``record`` 的锁内），所以要证明「间隙关上了」，
      必须能让 hook 在**即将记账**那一点停住、让主线程完成结算、再放行 ——
      这件事在进程外没法做，只能留这个 seam。探针
      ``guard-finalize-race-loses-record`` 就是这么用的；
    * :func:`assert_guard_live` 会复核 ``_finalize_race_seam_hook`` 仍是本函数
      （与 belt 身份漂移、受拦集合被缩小同型的纵深）。⚠️ 如实声明：这道复核
      **只在被显式调用时发生**（``install()``、每个用例边界、session 自证），
      所以「独立脚本里替换了它」「在下一个用例边界之前又换回去」这两种情形它抓不到
      （Codex round-1 HIGH-1）。承重的不是这道复核，而是上一条的 ``try/except``。
    """


#: 可替换的注入点引用（测试/探针替换它；生产恒为 :func:`_finalize_race_seam`）。
_finalize_race_seam_hook = _finalize_race_seam


def _is_uvloop_module(name) -> bool:
    """``import`` 审计事件里的模块名是不是 uvloop 或它的子模块（RV-C M-4）。

    ⛔ 判据必须覆盖**子模块**，原因是实测出来的（2026-09-08，本树 CPython 3.14.4，
    证据 ``_bmad-output/审查/evidence-w47/m4-importlib-*.txt``）：

    * ``import uvloop``（语句）⇒ ``__import__`` 抛 ``import`` 事件，``args[0]`` 恰是
      ``"uvloop"`` —— 旧判据拦得住；
    * ``importlib.import_module("uvloop")`` ⇒ 走 ``_bootstrap._gcd_import``，**不为顶层名
      抛事件**。于是 ``del sys.modules["uvloop"]`` 绕过非承重的毒化层之后，这条路
      **两层防御全都越过、uvloop 真的被导入了**。

    但 hook 并不是没被调用：uvloop 的 ``__init__.py`` 自己 import 子模块，实测触发了
    ``uvloop.includes`` / ``uvloop.loop`` / ``uvloop._noop`` / ``uvloop._version``。
    所以把判据从「等于 uvloop」放宽到「uvloop 或 uvloop. 开头」，就能在**同一层**
    （audit ``import`` 事件）把这条路关上 —— 承重方式没有改变，模块 docstring 对
    「audit 事件承重、毒化不承重」的定性照旧成立。

    前缀带**点**（``uvloop.``）而不是裸 ``startswith("uvloop")``：否则 ``uvloopx`` /
    ``uvloop_shim`` 这类无关模块会被误拦（契约 ``test_lookalike_module_names_are_not_blocked``
    是这条的验伪锚）。``type(name) is str`` 而不是 ``isinstance``：审计事件的参数由
    调用方给，``str`` 子类可以重载 ``__eq__`` / ``startswith``。
    """
    if type(name) is not str:  # noqa: E721 —— str 子类可重载比较，不认
        return False
    return name == "uvloop" or name.startswith("uvloop.")


def _is_selftest_address(address) -> bool:
    """这条地址是不是**本模块自己合成的**自证探针地址。

    ⛔ 这个分类决定「拦截要不要记账」，所以它必须**比端口判据更严**，且一步都
    不能走被测对象能重载的方法（round-1 Codex round-2 HIGH-1）。

    旧实现 ``isinstance(address, tuple) and len(address) >= 1 and address[0] == _SELFTEST_HOST``
    的三处都可被重载，于是有两种伪装能让**真实的受拦连接**被分类成自证 ——
    抛出的 ``_SelfTestBlocked`` 继承 ``RuntimeError``、普通 ``except`` 就能吞掉，
    而 ``STATE.record()`` 在这之后才跑 ⇒ **账本为零**，后续结账无从据此拒绝 rc=0：

    * tuple 子类：底层槽位是 ``("127.0.0.1", 7691)``，``[0]`` 返回哨兵主机名；
    * 普通 tuple + ``str`` 子类主机名，其 ``__eq__`` 对哨兵恒真。

    现在三道都钉死：``type(address) is tuple``（不认子类）、
    ``tuple.__getitem__`` 读底层槽位（不走重载）、``type(host) is str``
    （不认 ``str`` 子类的 ``__eq__``）。本模块自己合成的探针地址恰好满足全部三条，
    别人构造的地址想满足就得**真的**是精确 tuple + 精确 str —— 那时它已经不是
    伪装，而就是自证地址本身，而含 NUL 的主机名连不上任何东西。
    """
    if type(address) is not tuple:  # noqa: E721 —— 子类不算
        return False
    try:
        if tuple.__len__(address) < 1:
            return False
        host = tuple.__getitem__(address, 0)
    except Exception:  # noqa: BLE001
        return False
    return type(host) is str and host == _SELFTEST_HOST  # noqa: E721 —— str 子类不算


def _audit_hook(event: str, args) -> None:
    """承重层：CPython ``socket.connect`` 审计事件（连接**发起前**触发）。

    对 ``socket.socket`` / ``_socket.socket`` / ``socket.SocketType`` /
    ``connect_ex`` 四条路径一律触发；hook 抛出的异常会原样传给调用方，
    因此「抛 = 连接没发生」。

    ``import`` 事件用来关死 uvloop：毒化 ``sys.modules`` 会被「del 掉再 import」
    绕过（R1 Codex HIGH-4 实测），而 audit hook 摘不掉。
    """
    if event == "socket.connect":
        address = args[1] if len(args) > 1 else None
        port = extract_port(address)
        # 端口对象不可信（有状态 __index__）⇒ 按受拦处理，见 port_is_trustworthy
        if port in BLOCKED_PORTS or not port_is_trustworthy(address):
            # 自证探针：走完整的「取端口 → 判受拦 → 抛」路径，只跳过记账。
            # 判定在**端口判断之后**，所以把 extract_port 改坏、把受拦集合清空、
            # 或把 hook 摘掉，自证都会失败（这正是 R1 Codex HIGH-3 要求的）。
            if _is_selftest_address(address):
                raise _SelfTestBlocked("selftest reached the blocking path")
            # 注入点：默认 no-op，返回值不参与任何判据（见 _finalize_race_seam）。
            # ⛔ 必须包在 try 里（Codex round-1 HIGH-1 实测）：seam 若抛异常，连接确实被
            #    阻断了，但 `STATE.record()` 根本没跑到 ⇒ 账本零、进程 exit 0。也就是说
            #    这个「只为测试存在」的缝会变成一条**跳过记账**的旁路。吞掉它之后，seam
            #    对控制流的影响面收敛到 0：它只能延迟，不能改变任何判定。
            try:
                _finalize_race_seam_hook()
            except BaseException:  # noqa: BLE001 —— 见上：注入点不得影响控制流
                pass
            # ⛔ 「是不是迟到」由 record() **在账本那把锁里**判定，不在这里锁外读标志
            #    （CARD-W4-4：锁外读 + 另一把锁记账之间的夹缝会整条丢掉记录）。
            outcome = STATE.record(address)
            if outcome == RECORD_LATE:
                # 最终结算之后的迟到连接：已无人能改 rc，只能就地把进程打成非零。
                # ⛔ 落盘与打印全部包住（Codex round-1 HIGH-3 实测）：原来 print 在 try
                #    之外，stderr 若已关闭，`ValueError` 会**越过** os._exit —— 于是
                #    「判迟到就必然就地退出 3」这句在那种状态下不成立。强制退出是承重
                #    的那一层，任何可观测性动作都不得挡在它前面。
                try:
                    # 退出前把**含这条记录**的账本重写一次 —— 否则文件里是结算那一刻的
                    # 空账而进程 rc=3，父进程复核与子进程裁定互相打脸。
                    _rewrite_ledger_after_late_record()
                    print(
                        f"\n*** {BLOCK_REASON}（最终结算之后）: {address!r} —— "
                        f"进程被强制以退出码 {FINAL_EXIT_CODE} 结束 ***",
                        file=sys.stderr,
                    )
                    sys.stdout.flush()
                    sys.stderr.flush()
                except BaseException:  # noqa: BLE001 —— 见上：绝不阻断 os._exit
                    pass
                os._exit(FINAL_EXIT_CODE)
            if outcome == RECORD_BLOCK:
                raise RuntimeError(_block_message(address))
    elif event == "import" and args and _is_uvloop_module(args[0]):
        raise RuntimeError(
            "uvloop 的 import 被本门拦下：uvloop 走 libuv，不触发 socket.connect "
            "审计事件，门会静默失效。若确需 uvloop，必须连本门一起重新设计。"
        )


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

    ⛔ **hook 一旦生效就必须有人结账**（Codex round-1 HIGH-2）。正因为
    ``_install_audit_hook()`` 摘不掉，它与 :func:`register_final_accounting` 之间
    不允许夹任何可抛出的步骤：中途抛出 ⇒ 门在位、照常记账，却没有人在退出时把账
    交出来。所以顺序是 **hook → 结算器 → 预检 → 身份复核**，预检抛出时结算器
    **照样已经注册**。

    此时 ``STATE.installed`` 仍是 ``False``，账本 ``installed`` 字段如实写 False ——
    :func:`_final_accounting` 在这种「装门失败但账本仍要交」的形态下语义不变：它读
    的是 ``unaccounted`` / ``blocked`` / ``reported_status``，与 ``installed`` 无关
    （退出码判据见那里，本卡不改）。一次连接都没有 ⇒ 零账 ⇒ 不改退出码，装门失败
    该以什么 rc 收场就还是什么。
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
    # ⛔ 承重 hook 必须装在**任何预检之前**（T-14，CARD-W4-4）。
    #    ``assert_neo4j_target_blocked()`` 会走 ``canonical_target_ports``，后者在
    #    函数体内 ``from neo4j import Address`` —— 那段 import 期（以及预检本身可能
    #    触发的任何连接）原来跑在门装上**之前**，完全不受保护也不进账。
    #    2026-09-05 实测（``evidence-w4-4/before-3``）：在预检内发起一次到受拦端口的
    #    连接，旧顺序下结果是 ``connected`` 且 ``STATE.blocked=0``。
    # ⛔ ``register_final_accounting()`` 必须紧跟在 hook 之后、排在**预检之前**
    #    （Codex round-1 HIGH-2）。hook 摘不掉：预检抛出时它已经在位、照常记账，而旧
    #    顺序下结算器还没注册 —— 那些记录无人交账，进程 ``exit 0``。旧注释写的
    #    「预检抛出时本来就拒绝装门，此时不该留下一个会 os._exit 的 atexit」把因果
    #    弄反了：atexit 处理器不是负担而是**责任**，装了 hook 就必须有人结账。零账时
    #    它本来也不改退出码（见 :func:`_final_accounting`），留下它没有代价。
    _install_audit_hook()
    register_final_accounting()
    if os.environ.get(ENV_REQUIRE_BLOCKED_TARGET) == "1":
        assert_neo4j_target_blocked()
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
    """行为级验证：让一个合成地址**走完整条阻断路径**，看它是不是真的被拦。

    做法是自己发一次 ``socket.connect`` 审计事件，地址为
    ``(_SELFTEST_HOST, <受拦端口>)``。这条探针会依次经过：
    audit 分发 → :func:`extract_port` → :data:`BLOCKED_PORTS` 判定 → 抛异常。
    只有在**最后一步之后**才按哨兵主机名分流成 :class:`_SelfTestBlocked`，
    所以链条上任何一环被改坏（hook 摘掉 / ``extract_port`` 恒返 None /
    受拦集合被清空 / 判定条件被改写）都会让本函数返回 ``False``。

    R1 Codex HIGH-3 打回的旧实现用的是一个**独立的私有事件**，只证明「hook 对象
    还在链上」，把 ``extract_port`` 改成恒返 ``None`` 之后自证照样通过、真实
    loopback 连接照样成功、账本照样全零。「自证」必须穿过被自证的那条路径。

    ⚠️ 本函数会向进程内**所有** audit hook 发一次 ``socket.connect`` 事件；
    地址主机名含 NUL 字节，不可能是真实目标，但第三方 hook 会看见它。
    """
    probe_port = next(iter(sorted(REQUIRED_BLOCKED_PORTS)))
    try:
        sys.audit("socket.connect", None, (_SELFTEST_HOST, probe_port))
    except _SelfTestBlocked:
        return True
    except Exception:  # noqa: BLE001 —— 被别的东西拦下 ≠ 被本门拦下
        return False
    return False


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
            f"承重阻断路径自证失败{where}：合成的受拦地址没有被拦下。"
            "链条上有一环被改坏了（hook 摘掉 / extract_port 恒返 None / "
            "受拦集合被清空 / 判定条件被改写），门此刻不承重。"
        )
    if _finalize_race_seam_hook is not _finalize_race_seam:
        raise GuardDrift(
            f"结算竞态注入点被替换{where}：当前是 {_finalize_race_seam_hook!r}，"
            f"期望 {_finalize_race_seam!r}。该注入点只允许探针在独立子进程里用，"
            "生产路径上它必须是那个 no-op（见 _finalize_race_seam 的说明）。"
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
    _assert_uvloop_closed(GuardDrift, where)


def _assert_uvloop_closed(exc_type, where: str = "") -> None:
    """uvloop 必须**既**被 import 拦死、**又**没有实际生效的 policy。

    R1 Codex HIGH-4 打回的旧检查是 ``sys.modules.get("uvloop") is not None``：
    ``del sys.modules["uvloop"]`` 之后这个表达式为 ``None is not None`` = False，
    检查通过 —— 而此时 uvloop 已经可以被重新 import。所以这里要求 key **存在
    且为 None**。真正的承重是 audit ``import`` 事件（摘不掉），毒化只是让错误
    信息更早、更清楚。
    """
    if "uvloop" not in sys.modules:
        raise exc_type(
            f"uvloop 毒化条目被删除{where}：sys.modules 里已经没有 'uvloop' 键，"
            "此刻可以重新 import。（承重的 import 审计拦截仍在，但毒化被动过说明有人在拆门。）"
        )
    if sys.modules["uvloop"] is not None:
        raise exc_type(f"uvloop 已在本进程被真实导入{where}：它走 libuv，不触发 socket.connect 审计事件。")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            policy_module = type(asyncio.get_event_loop_policy()).__module__ or ""
    except Exception:  # noqa: BLE001 —— 拿不到 policy 不算证据，靠上面两条
        return
    if "uvloop" in policy_module:
        raise exc_type(f"event loop policy 来自 uvloop（{policy_module}）{where}：本门会静默失效。")


def assert_not_uvloop() -> None:
    """session 级复核（与用例边界同一套判据，异常类型不同）。"""
    _assert_uvloop_closed(RuntimeError, "（session 复核）")


def canonical_target_ports(uri: str) -> tuple[tuple[int, ...] | None, str]:
    """按 **neo4j 驱动自己的解析链**复算这个 URI 的**全部初始目标端口**。

    返回 ``(端口元组, 依据)``；解析不出来返回 ``(None, 原因)``，调用方一律 fail-closed。

    ⚠️ 返回的是**元组**而不是单值：routing scheme（``neo4j://``）的 netloc 会被
    ``Address.parse_list`` 按空白拆成**多个**初始地址（驱动取 ``[0]``，但整张表
    都会进连接池的初始候选）。调用方必须要求**每一个**端口都合规 ——
    只看第一个就会漏掉 ``neo4j://ok:7692 evil:7691`` 这类写法。

    ⛔ 为什么不能用本模块的 :func:`_port_of_uri` 推断：它是**另一个解析器**，
    与驱动的口径必然会分叉。X4 的 BLOCKER 就是这么来的 ——
    ``_port_of_uri("bolt://127.0.0.1:0")`` 老实返回 ``0``，而驱动返回 **7687**。
    判据要挡的是「驱动实际会连哪里」，就必须问驱动本人。

    驱动的链路是三段（2026-09-05 于 venv 内实读 + 实跑）：

    1. ``neo4j/_api.py::parse_neo4j_uri`` → ``urlparse(uri)``；
       ``parsed.username`` / ``parsed.password`` 非空**直接** ``ConfigurationError``
       —— 驱动根本不接受带 userinfo 的 URI；
    2. 同处校验 scheme 白名单（bolt / bolt+s / bolt+ssc / neo4j / neo4j+s / neo4j+ssc），
       其它 scheme ``ConfigurationError``；
    3. ``_sync/driver.py:276`` 把 **``parsed.netloc``** 交给
       ``_Direct._parse_target`` → ``Address.parse(netloc, default_host='localhost',
       default_port=7687)``。

    所以这里也走 ``urlparse → scheme 校验 → netloc → Address.parse{,_list}``，
    参数与 ``:446-452`` / ``:470-479`` 一字不差。
    **刻意不自己切字符串**：直接把 ``bolt://user:pass@h:7692`` 的 tail 喂给
    ``Address.parse`` 得到的东西与驱动的真实行为（在第 1 步就 ConfigurationError）
    是两回事 —— 那种"看起来也拒了"的巧合不能当判据，它在别的输入上就会分叉。
    （原注释说那会抛 ``ValueError: Unknown port value``，round-1 Codex 指出**并非
    总是如此**，本机实测某些形态会返回字符串端口；措辞已改成不依赖具体异常。）

    ⚠️ **延迟 import 的合法性**：本模块刻意不在模块层 import 任何重物（装门必须
    早于一切业务 import，见 ``tests/conftest.py:28``）。本函数的两个调用方里，
    :func:`assert_test_uri_not_blocked` 现在在 ``pytest_configure`` 期跑；
    :func:`assert_neo4j_target_blocked` 由 :func:`install` 在 ``W4_GUARD_REQUIRE_BLOCKED_TARGET=1``
    时调用，而 ``guard_plugin`` 是在**模块 import 期**调 ``install()`` 的 ——
    也就是说开了那个负控开关时，本函数**会在插件 import 期**跑，比 configure 更早
    （Codex round-1 LOW-10 更正了这里原先「两个调用方都在 configure 期或更晚」的说法）。
    负控脚本实测这条路径可用（`lifespan_isolation_negative_control.py` 常绿）。
    2026-09-05 实测：在一个**不加载 root conftest** 的最小会话里，
    ``pytest_configure`` 期 ``from neo4j import Address`` 与本函数都正常工作，
    所以「延迟 import 那时才可用」这个前提比上移前更弱、依然成立。
    所以 import 写在**函数体内**是合法的；模块层新增 import 则禁止（裁判 6 会数）。

    ⛔ 而且这段 import 现在跑在**门内**：:func:`install` 已把 ``_install_audit_hook()``
    提到预检之前（T-14）——旧顺序下这整段是不受保护、也不进账的。
    """
    try:
        from urllib.parse import urlparse
    except Exception as exc:  # noqa: BLE001 —— 标准库都 import 不了，只能 fail-closed
        return None, f"urllib.parse 不可用（{exc!r}）"
    try:
        from neo4j import Address
        from neo4j import api as neo4j_api
    except Exception as exc:  # noqa: BLE001
        return None, f"neo4j.Address / neo4j.api 不可用（{exc!r}）—— 无法按驱动口径复算，拒绝推断"
    try:
        parsed = urlparse(uri)
    except Exception as exc:  # noqa: BLE001
        return None, f"urlparse({uri!r}) 失败：{exc!r}"
    try:
        if parsed.username or parsed.password:
            return None, "URI 含 userinfo —— 驱动的 parse_neo4j_uri 会直接 ConfigurationError"
    except Exception as exc:  # noqa: BLE001 —— 畸形 netloc 会让 username 属性本身抛
        return None, f"URI 的 userinfo 无法判定：{exc!r}"
    # 第 2 段：scheme 白名单。常量取自 **驱动自己的公开 api 模块**，不自己抄字面值 ——
    # 抄下来的字符串会随驱动升级悄悄过期，而 import 它则会当场报错。
    # ⚠️ ``bolt+routing`` 刻意**不在**集合里：驱动对它抛「已改名，请用 neo4j://」。
    # ⚠️ 这一段是 2026-09-05 本 session 自查补的：先前只做了 userinfo + Address.parse，
    #    于是 ``ftp://127.0.0.1:7692`` / ``http://…`` / ``bolt+routing://…`` 都会被算出
    #    7692 而**放行** —— 驱动那边其实是 ConfigurationError（连都建不起来）。
    #    后果不是安全洞（建不起 driver 就不会连任何东西），但它让 docstring 里
    #    「按驱动自己的解析链复算」这句**比实现宽**，而且拒因会给错（说"会连 7687"）。
    supported_schemes = frozenset(
        {
            neo4j_api.URI_SCHEME_BOLT,
            neo4j_api.URI_SCHEME_BOLT_SELF_SIGNED_CERTIFICATE,
            neo4j_api.URI_SCHEME_BOLT_SECURE,
            neo4j_api.URI_SCHEME_NEO4J,
            neo4j_api.URI_SCHEME_NEO4J_SELF_SIGNED_CERTIFICATE,
            neo4j_api.URI_SCHEME_NEO4J_SECURE,
        }
    )
    # urlparse 已把 scheme 小写化，与驱动侧的比较口径一致。
    if parsed.scheme not in supported_schemes:
        return None, (
            f"scheme {parsed.scheme!r} 不在驱动支持的集合 {sorted(supported_schemes)} 内 "
            f"—— 驱动的 parse_neo4j_uri 会 ConfigurationError"
        )
    # 第 3 段：direct 与 routing 走的是**两个不同的解析入口**，必须跟着分流。
    #
    # ⛔ round-1 Codex BLOCKER：本卡第一版对所有 scheme 统一调 ``Address.parse``，
    #    而驱动对 ``neo4j[+s|+ssc]`` 走的是 ``_Routing._parse_targets`` →
    #    ``Address.parse_list``，后者**按空白把 netloc 拆成多个地址**
    #    （``_addressing.py`` 的 ``parse_list``）。两条实测反例（本机 neo4j 6.1.0）：
    #      * ``neo4j://127.0.0.1 :7692``      单值解析给 7692（放行），
    #        parse_list 给 [('127.0.0.1', **7687**), ('localhost', 7692)]，驱动取 [0] ⇒ 连现网；
    #      * ``neo4j://[::1]:7691 [::1]:7692`` 同理，驱动实际连 **7691**。
    #    反方向也误拒：``neo4j://127.0.0.1:7692 localhost:7692`` 单值解析失败被拒，
    #    而驱动接受它。
    routing_schemes = frozenset(
        {
            neo4j_api.URI_SCHEME_NEO4J,
            neo4j_api.URI_SCHEME_NEO4J_SELF_SIGNED_CERTIFICATE,
            neo4j_api.URI_SCHEME_NEO4J_SECURE,
        }
    )
    try:
        if parsed.scheme in routing_schemes:
            addrs = list(
                Address.parse_list(
                    parsed.netloc,
                    default_host=_DRIVER_DEFAULT_HOST,
                    default_port=_DRIVER_DEFAULT_PORT,
                )
            )
            how = "Address.parse_list（routing scheme，按空白拆分多地址）"
        else:
            addrs = [
                Address.parse(
                    parsed.netloc,
                    default_host=_DRIVER_DEFAULT_HOST,
                    default_port=_DRIVER_DEFAULT_PORT,
                )
            ]
            how = "Address.parse（direct scheme）"
    except Exception as exc:  # noqa: BLE001
        return None, f"驱动口径解析 netloc={parsed.netloc!r} 失败：{exc!r}"
    if not addrs:
        return None, f"驱动口径解析 netloc={parsed.netloc!r} 得到空地址表"
    ports: list[int] = []
    for addr in addrs:
        try:
            port = addr[1]
        except Exception as exc:  # noqa: BLE001
            return None, f"驱动解析结果取不到端口：{addr!r}（{exc!r}）"
        if type(port) is not int or isinstance(port, bool):  # noqa: E721 —— 必须是精确 int
            return None, f"驱动解析出的端口不是 int：{port!r}"
        ports.append(port)
    return tuple(ports), f"驱动 canonical：netloc={parsed.netloc!r} → {how} → {addrs!r}"


def assert_test_uri_not_blocked() -> None:
    """``NEO4J_TEST_URI`` 的**驱动 canonical 端口**必须在 :data:`ALLOWED_TEST_PORTS` 里。

    判据历史（两次都是被独立终审打回后改的，留着免得有人往回改）：

    1. 最早是 ``f":{port}" in uri`` 的子串判断 —— ``bolt://127.0.0.1``（不写端口）
       通过检查，而驱动会用 7687。R1 Codex BLOCKER。
    2. 改成「解析出端口 + 端口不在 :data:`BLOCKED_PORTS`」—— 仍是**黑名单**，
       ``bolt://127.0.0.1:0`` 的端口 ``0`` 既非 None 又不在黑名单里 ⇒ 放行，
       而驱动把 ``:0`` 归一成 7687，再经 :func:`is_exempt` 的 advisory 路径**真连开发库**。
       X4 两轮独立终审给出的**同一条 BLOCKER**。

    现在是**正面白名单 + 驱动口径**，判据显式三分，没有"其余情况"这种灰地带：

    * 没配 ``NEO4J_TEST_URI`` → **射程外**，直接返回（不是本函数要管的事）；
    * 驱动口径解析不出 int 端口 → **拒绝**（fail-closed，不再靠"没看见受拦端口"推断）；
    * 解析出端口且 ∈ :data:`ALLOWED_TEST_PORTS` → **放行**；其余一律**拒绝**。

    白名单为空时连 7692 也拒 —— 契约测试 monkeypatch 空集验证这一点，证明它承重
    而不是恒真。
    """
    # ⛔ 先检查白名单**自己**合不合法，且**无条件**检查（不受"有没有配 URI"影响）：
    #    「往 ALLOWED_TEST_PORTS 里加一个现网端口」是拆掉本判据最省事的方式 ——
    #    加完之后 `:0`→7687 就成了"白名单内"，这道判据当场变成恒真。白名单与
    #    受拦集合必须不相交，相交即 fail-closed。探针
    #    `guard-allowed-test-ports-cannot-admit-live` 钉死这一条。
    admitted_live = ALLOWED_TEST_PORTS & BLOCKED_PORTS
    if admitted_live:
        raise RuntimeError(
            f"ALLOWED_TEST_PORTS={sorted(ALLOWED_TEST_PORTS)} 与受拦集合 "
            f"{sorted(BLOCKED_PORTS)} 相交于 {sorted(admitted_live)} —— "
            f"把现网端口放进测试白名单等于把这道判据拆成恒真，拒绝装门。"
        )
    uri = os.environ.get("NEO4J_TEST_URI")
    if not uri:
        _mark_precheck_done()
        return  # 射程外：没配测试容器 URI
    ports, why = canonical_target_ports(uri)
    if ports is None:
        raise RuntimeError(
            f"NEO4J_TEST_URI={uri!r} 无法按驱动口径解析出端口（{why}）。"
            f"解析不了就不能证明它不指向现网库（默认端口 {_DRIVER_DEFAULT_PORT}），"
            f"拒绝装门。测试容器请写全，例如 bolt://127.0.0.1:7692。"
        )
    # ⛔ **每一个**初始候选地址都要合规，不是只看驱动会先用的那个：routing scheme
    #    的 netloc 会被拆成多地址，`neo4j://ok:7692 evil:7691` 只看第一个就漏了。
    offending = sorted({p for p in ports if p not in ALLOWED_TEST_PORTS})
    if offending:
        raise RuntimeError(
            f"NEO4J_TEST_URI={uri!r} 按驱动口径的初始目标端口是 {list(ports)}，"
            f"其中 {offending} 不在允许的测试端口白名单 {sorted(ALLOWED_TEST_PORTS)} 内。"
            f"（{why}；驱动对缺省/0 端口的默认值是 {_DRIVER_DEFAULT_PORT}，"
            f"而 {_DRIVER_DEFAULT_PORT} 正是现网默认端口。）"
            f"测试容器请写全，例如 bolt://127.0.0.1:7692。"
        )
    _mark_precheck_done()


def _mark_precheck_done() -> None:
    """标记「``NEO4J_TEST_URI`` 白名单预检已通过」——只在**成功返回的路径**上调。

    ``begin_item`` 读它决定要不要发豁免票（T-10 的闩，见那里的说明）。

    ⚠️ **语义严格说是「曾经成功过一次」，不是「当前配置合规」**（Codex round-1
    MEDIUM-5 更正了这里原先过宽的措辞）：单向置位，一旦为真就不再回落。因此
    「先成功 → 配置被改 → 再次预检失败但调用方吞掉异常 → 继续跑」这条序列里，
    豁免票仍然会发。它成立的前提是**预检的输入在会话期内不变**——正常路径确实如此
    （``pytest_configure`` 期跑一次，失败就终止会话），但这是前提，不是本函数保证的。
    刻意不做「入口先清零、成功再置位」：契约测试里有十余处**期望抛出**的调用，
    清零后异常路径会把真 ``STATE`` 的闩永久留在 False，反而让后续 integration 用例
    集体失去 advisory 豁免——那是拿一个假想风险换一个真实回归。
    """
    with STATE._lock:
        STATE.precheck_done = True


def assert_neo4j_target_blocked() -> None:
    """要求 ``NEO4J_URI`` 指向**受拦端口**，否则拒绝装门（负控专用，默认关闭）。

    第八批 Codex BLOCKER 的结构性收口：本门只按端口判定，射程之外的库它拦不住。
    负控要做的事是「摘掉隔离，看门拦不拦」——如果此时 ``NEO4J_URI`` 指向的是
    7691/7687 之外的某个真库，那么「摘掉隔离」会**真的连上去**，脚本只会事后
    因 ``blocked=0`` 报失败，而实害已经发生。

    所以负控用 ``W4_GUARD_REQUIRE_BLOCKED_TARGET=1`` 打开本检查：目标不在射程内
    就在**任何测试跑起来之前**拒绝装门（拒的是 belt / ``STATE.installed`` —— audit
    hook 与 atexit 结算器已生效且摘不掉，零账不改 rc、有账强制 3，见
    :func:`install`；探针 ``guard-partial-install-settles-late-connection`` 钉的正是
    这种半装形态下「有人结账」）。检查读的是 **环境变量**（负控显式钉死的
    那一份），不是 ``Settings``——本模块刻意不 import ``app.*``，装门必须早于任何
    业务 import。负控另有一道 ``Settings`` 侧的前置自检（见负控脚本 step 0c），
    两边口径一致才放行。
    """
    uri = os.environ.get("NEO4J_URI")
    if not uri:
        raise RuntimeError(
            f"{ENV_REQUIRE_BLOCKED_TARGET}=1 但 NEO4J_URI 未设置：无法证明连接目标在门的射程内，拒绝装门。"
        )
    # ⛔ 这里也必须用驱动口径（round-2 Codex MEDIUM）：旧实现用本模块自写的
    #    :func:`_port_of_uri`，它把 query / fragment 里的数字当端口 —— 实测
    #    ``bolt://127.0.0.1:11434#tag:7687`` 被它读成 7687、
    #    ``bolt://127.0.0.1:7692?x=:7691`` 被它读成 7691，于是这道"目标必须在射程内"
    #    的预检会**假通过**，负控以为自己钉死了受拦目标，其实没有。
    #    与 :func:`assert_test_uri_not_blocked` 同源同口径，两处不再各用一个解析器。
    ports, why = canonical_target_ports(uri)
    if ports is None:
        raise RuntimeError(
            f"{ENV_REQUIRE_BLOCKED_TARGET}=1 但 NEO4J_URI={uri!r} 按驱动口径解析不出端口（{why}），拒绝装门。"
        )
    # 反向判据：这里要的是「目标**在**受拦集合内」，所以**每一个**初始候选地址
    # 都必须受拦 —— 有一个在射程外，摘掉隔离后它就会被真连。
    escaping = sorted({p for p in ports if p not in BLOCKED_PORTS})
    if escaping:
        raise RuntimeError(
            f"{ENV_REQUIRE_BLOCKED_TARGET}=1 但 NEO4J_URI={uri!r} 的初始目标端口是 {list(ports)}，"
            f"其中 {escaping} 不在受拦集合 {sorted(BLOCKED_PORTS)} 内 —— "
            f"摘掉隔离后会真实连接该库，拒绝装门。（{why}）"
        )


# ⛔ 这里原本有一个 `_port_of_uri()` —— 本模块自写的 URI 端口解析器，
#    已于 CARD-W4-3a **删除**（不是留着不用，是删掉）。理由：
#
#    它是「**另一个**解析器」，而门要判的是「驱动实际会连哪里」。两个解析器必然
#    分叉，而每一次分叉都是一个洞。这个函数身上已经攒了两条实证缺陷：
#      * `_port_of_uri("bolt://127.0.0.1:0")` 老实返回 0，驱动返回 7687
#        （X4 两轮独立终审的那条 BLOCKER 就是这么来的）；
#      * 它把 query / fragment 里的数字当端口 —— `bolt://127.0.0.1:11434#tag:7687`
#        被读成 7687、`bolt://127.0.0.1:7692?x=:7691` 被读成 7691，于是
#        `assert_neo4j_target_blocked` 的「目标必须在射程内」预检**假通过**
#        （round-2 Codex MEDIUM）。
#
#    两个调用点（`assert_test_uri_not_blocked` / `assert_neo4j_target_blocked`）
#    现在都走 :func:`canonical_target_ports`，同源同口径。留着一个零调用、已知有
#    缺陷、名字又像"正经解析器"的函数，只会让下一个人再捡起来用。


# ═══════════════════════════════════════════════════════════════════════════
# 最终总账（atexit；**不是**「所有 cleanup / atexit 之后」——见 register_final_accounting）
# ═══════════════════════════════════════════════════════════════════════════

_FINAL_REGISTERED = False


def register_final_accounting() -> None:
    """注册最终总账。

    ⚠️ **不能**声称「在所有 atexit 之后执行」（R1 Codex HIGH-2 打回的过宽表述）。
    ``atexit`` 是 LIFO：本处理器排在**本模块 import 之后**注册的回调后面，却排在
    **本模块 import 之前**就已注册的回调**前面**。Codex 实测复现：先注册一个会发起
    连接的 atexit 回调、再 import 本门 —— 最终总账先跑、看见零账、返回，随后那个旧
    回调发起的连接被 audit 拦下，而进程仍然 ``exit 0``。

    所以本处理器**进入时立刻置不可逆的结算标志**（:meth:`_GuardState.finalize_and_snapshot`
    在同一次持锁内置位并取走快照）：此后 audit hook 一旦命中受拦端口，
    :meth:`_GuardState.record` 会在同一把锁里判成 :data:`RECORD_LATE`，hook 就地
    ``os._exit(3)``，不再依赖任何后续的结账机会。
    """
    global _FINAL_REGISTERED
    if _FINAL_REGISTERED:
        return
    atexit.register(_final_accounting)
    _FINAL_REGISTERED = True


def write_ledger(path: str, ledger: dict | None = None) -> None:
    """把账本写到 ``path``（父进程独立复核用）。写失败不静默——直接抛。

    ⛔ **结算路径必须把快照传进来**（CARD-W4-4）。旧实现在这里自己**再取一次快照**，
    于是裁定读的是 ``_final_accounting`` 那一份、落盘写的是这一
    份——一条记录落在两次取快照之间，账本文件就会写着 ``unaccounted=1`` 而进程
    ``rc=0``。2026-09-05 实测复现见 ``evidence-w4-4/before-repro.py`` 的 ``before-2``。

    ``ledger=None`` 只留给**结算之外**的独立调用（「现在把账面存一份看看」），
    那种场景没有第二份快照可比，取一次是对的。
    """
    if ledger is None:
        ledger = STATE.ledger()
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(ledger, fh, ensure_ascii=False, indent=2)


#: 已发布到账本文件的最高快照序（只增）。见 :func:`_publish_ledger`。
_PUBLISHED_SEQ = -1
#: 只保护「比序号 + 写文件」这一小段的锁。
_PUBLISH_LOCK = threading.Lock()
#: 取 :data:`_PUBLISH_LOCK` 的上限。迟到路径在 ``os._exit`` **之前**走这里，绝不能被
#: 另一个线程无限期挡住 —— 超时就放弃写盘（账本只是可观测性，强制非零 rc 才承重）。
_PUBLISH_LOCK_TIMEOUT = 5.0


def _publish_ledger(path: str, ledger: dict) -> bool:
    """发布账本到 ``path`` —— **只在这份快照比已发布的那份更新时**才真写。

    ⛔ CARD-W4-4b / Codex round-1 MEDIUM-4：两条写盘路径（:func:`_final_accounting`
    与 :func:`_rewrite_ledger_after_late_record`）各自「先取快照、后 ``open(path,"w")``
    整写」，中间没有任何发布顺序控制。于是这个交错会让文件与 rc 打架：

    1. 结算线程取到**零账**快照，尚未写盘；
    2. 迟到线程记账（``unaccounted=1``）、取快照、把含迟到记录的账本写进文件；
    3. 结算线程拿着第 1 步那份**旧**快照 ``open(path,"w")``，把文件盖回零账；
    4. 迟到线程 ``os._exit(3)``。
    ⇒ 进程 rc=3，而父进程按文件复核得到「什么都没发生」。

    修法是给每份快照一个取快照时就定下的单调序（``ledger["seq"]``，见
    :meth:`_GuardState._ledger_locked`），发布时比一次：序号不比已发布的大就**不回写**。
    第 3 步于是变成一次 no-op，文件停在 ``unaccounted=1``。

    ⚠️ **发布序必须在写盘之前推进**（自查修正，2026-09-08）：初版把
    ``_PUBLISHED_SEQ = seq`` 放在 ``write_ledger`` 成功之后 —— 于是「较新的那份写
    失败（磁盘满 / 权限 / 路径消失）」会把门**重开**：序号没动，紧接着的陈旧发布
    ``seq <= _PUBLISHED_SEQ`` 判假 ⇒ 照写 ⇒ 账本文件是合法的零账 JSON 而进程 rc=3，
    MEDIUM-4 关掉的交错从 I/O 失败这条缝里原样回来。先行推进后，失败方向变成
    「**更旧的也别写**」：文件停留在截断/无效态，父进程 ``json.loads`` 直接报错 ——
    是可辨识的坏，不是可信的谎（裁判门
    ``test_publish_ledger_refuses_stale_even_after_a_failed_write``）。

    返回是否真的写了。**失败方向一律是「不写」**：拿不到锁（超时）或序号落后都返回
    ``False``，而 :func:`write_ledger` 自己抛出的 I/O 异常照常向上传（两个调用点各自
    有 try 包着，见那里；HIGH-3 的「异常不得越过 ``os._exit``」语义不变；此时序号
    已先行推进，后续任何陈旧发布都会被拒）。

    ``ledger`` 没有 ``seq`` 字段时（手工构造的账本）按「此刻最新」处理 —— 那种调用方
    本来就没有可比的先后关系。
    """
    global _PUBLISHED_SEQ
    seq = ledger.get("seq")
    if seq is None:
        seq = _next_snapshot_seq()
    if not _PUBLISH_LOCK.acquire(timeout=_PUBLISH_LOCK_TIMEOUT):
        return False
    try:
        if seq <= _PUBLISHED_SEQ:
            # 已经有更新的一份发布过了 —— 回写就是把新账盖成旧账。
            return False
        _PUBLISHED_SEQ = seq  # 先行推进：写盘失败也不许更旧的再写（见上）
        write_ledger(path, ledger)
        return True
    finally:
        _PUBLISH_LOCK.release()


def _rewrite_ledger_after_late_record() -> None:
    """迟到记录落地之后，把账本文件重写成**含这条记录**的版本。

    由 :func:`_audit_hook` 的迟到分支在 ``os._exit(FINAL_EXIT_CODE)`` **之前**调用。
    没有这一步，账本文件停留在结算那一刻（空账），而进程 rc=3 —— 父进程按文件复核
    会得出「什么都没发生」，与 rc 直接矛盾。有了它，**账本 ``unaccounted>0`` ⇒
    ``rc=3``** 成立。

    ⚠️ 反向不成立（2026-09-08 撤回原「两个方向都成立」）：``rc=3`` 还可能来自
    :func:`_final_accounting` 的第二个分支（``blocked>0`` 且原 ``reported_status``
    为 0），那时 ``unaccounted`` 可以是 0。探针 ``guard-ledger-matches-verdict``
    钉的也不是等价，而是**两个特例**（有迟到 ⇒ rc=3 且 unaccounted>0；零连接 ⇒
    rc=0 且零账），判据本身不变。

    ⚠️ 全程 fail-open：这是解释器收尾期、在任意线程里跑的，落盘失败绝不能挡住
    ``os._exit`` —— 强制非零 rc 才是承重的那一层，账本只是可观测性。
    """
    try:
        path = os.environ.get(ENV_LEDGER)
        if not path:
            return
        # 经 _publish_ledger 而不是直接 write_ledger：这一份是**较新**的快照，
        # 发布后结算线程手上的旧快照就再也盖不回来（MEDIUM-4）。
        _publish_ledger(path, STATE.late_snapshot())
    except Exception:  # noqa: BLE001 —— 见上：绝不阻断 os._exit
        pass


def _final_accounting() -> None:
    """最后一道结账：任何未结账的拦截都必须让进程以非零 rc 结束。

    第八批 Codex HIGH：``pytest_cmdline_main`` 返回之后还有 pytest 自身的清理、
    其它 ``atexit`` 处理器和迟到线程 —— 那段窗口里被拦下的连接会被记账，进程
    却仍然 ``exit 0``，于是「任何未结账尝试都令测试失败」这句承诺不成立。

    R1 Codex HIGH-2：本处理器**之后**仍可能有更早注册的 atexit 回调在跑
    （见 :func:`register_final_accounting`）。所以第一件事是置不可逆的结算标志：
    从这一刻起，audit hook 命中受拦端口就直接 ``os._exit(3)``，不再指望任何后续结账。

    ⛔ CARD-W4-4：置标志与取快照必须是**一次**操作
    （:meth:`_GuardState.finalize_and_snapshot`，同一次持锁），且裁定与落盘用
    **同一个** dict。旧实现这两处各写各的，留下的夹缝让一条 blocked 记录既进不了
    快照、又不触发迟到路径 ⇒ 进程 exit 0（``evidence-w4-4`` 的 ``before-1``）；
    而 ``write_ledger`` 自己再取一次快照，又让账本文件与裁定能互相打脸（``before-2``）。
    """
    ledger = STATE.finalize_and_snapshot()
    path = os.environ.get(ENV_LEDGER)
    if path:
        try:
            # 同一份快照，不再取第二次；经 _publish_ledger ⇒ 若迟到线程已经发布了
            # 更新的一份，这里不回写（MEDIUM-4 的陈旧覆盖）。
            _publish_ledger(path, ledger)
        except Exception as exc:  # noqa: BLE001 —— 落盘失败要说话，但不能盖掉结账
            print(f"*** W4 guard: 账本落盘失败 {path}: {exc!r} ***", file=sys.stderr)
    unaccounted = ledger["unaccounted"]
    blocked = ledger["blocked"]
    status = ledger["reported_status"]
    # status is None ⇒ 不是 pytest 跑的（脚本/探针直接 import 本模块）：按 0 处理，
    # 也就是「有非豁免拦截却打算正常退出」同样算失败。
    effective_status = 0 if status is None else status
    if unaccounted > 0 or (blocked > 0 and effective_status == 0):
        # ⛔ 报告整块包住（Codex round-1 HIGH-3 同型）：stderr 已关闭时 print 会抛，
        #    原来那个只裹 flush 的 try 挡不住它，异常会越过下面的强制退出。
        try:
            print(
                f"\n*** {BLOCK_REASON} —— 最终总账：blocked={blocked} "
                f"unaccounted={unaccounted} reported_status={status}；"
                f"进程被强制以退出码 {FINAL_EXIT_CODE} 结束（迟到连接不得以 0 收场）***",
                file=sys.stderr,
            )
            for rec in ledger["unaccounted_records"]:
                print(f"    - {rec['address']} on thread {rec['thread']} (owner={rec['owner']})", file=sys.stderr)
            sys.stdout.flush()
            sys.stderr.flush()
        except BaseException:  # noqa: BLE001 —— 可观测性不得挡在强制退出前面
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
