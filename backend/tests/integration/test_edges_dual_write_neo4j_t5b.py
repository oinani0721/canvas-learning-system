# CARD-T-EDGES (BATCH-2026-09-11-第十四批 / 车道 T5-B)
"""Edge 双写端点 Neo4j 侧的行为门.

被测缺陷: ``_write_neo4j_triplet`` 曾调 ``neo4j.execute_query(query, {...})``,
而 ``Neo4jClient`` 只有 ``run_query(query, **params)`` (``neo4j_client.py:536``).
``execute_query`` 不存在 ⇒ 每次调用抛 ``AttributeError``; 该函数的 except 元组
原为 ``(RuntimeError, ConnectionError, asyncio.TimeoutError, OSError)``, 不含
``AttributeError`` ⇒ 异常穿透 ``asyncio.gather`` (无 ``return_exceptions=True``)
再穿透无 try 的 handler ⇒ FastAPI 兜成 **500**, 把 LanceDB 侧那一半的结果一并丢弃,
而不是按 Story 4.4 AC-4 记成半成功 **207**.

⚠️ 措辞边界: 这里说的是「丢弃 LanceDB 那一半的**结果**」, 不是「丢弃已经落盘的数据」
—— 实测 ``_write_lancedb`` 目前**根本没有真写**(见文末「已知不实前提」), 所以
「已经写成功的那一半」是一句不实陈述, 本文件不再那么写.

门清单:

1. ``test_neo4j_attribute_error_degrades_to_207`` — 降级门, **零 DB**. 注入
   ``run_query`` / ``execute_query`` 都抛 ``AttributeError`` 的 stub, LanceDB 侧
   打成功, 断言 207 且 ``graphiti_status.error`` 带本门独有 sentinel.
   修复前 500 (RED), 修复后 207 (GREEN).
1c. ``test_每个被收进元组的对端故障类型都降级成_207`` — **零 DB, 参数化 5 格**.
   对 ``edges._NEO4J_WRITE_FAILURES`` 里新收的每一类(ServiceUnavailable /
   SessionExpired / TransientError / DatabaseError / RetryError)各跑一次, 逐格断言
   207 + sentinel + 错误串带类型名. ⛔ 类型清单**从生产模块读并逐类断言它确实在
   生产元组里**, 不在测试里手抄(手抄必漂移).
1d. ``test_本进程与部署缺陷不得被伪装成对端写失败`` — **反向门, 零 DB, 5 格**.
   ClientError / AuthError / ConnectionPoolError / TypeError / KeyError 必须仍然
   **500**. 这道门是「加宽」的护栏: 没有它, 后人把 ``Neo4jError`` 或 ``Exception``
   整族收进元组时不会有任何东西变红.
1e. ``test_run_query_返回空行必须记成写失败而不是_200`` + 其对照组
   ``test_run_query_返回一行是成功路径`` — **零 DB**. 钉住写确认判据.
1f. ``test_真客户端在_json_fallback_态下不得报写成功`` — **零 DB 零网络**, 用真的
   ``Neo4jClient(use_json_fallback=True)`` 证明 1e 模拟的「返回 []」形态确实是真实
   客户端在 fallback 态下的行为, 不是编出来的.
1b. ``test_test_uri_port_whitelist_rejects_everything_but_7692`` — 纯逻辑零网络,
   钉 scheme + 端口白名单.
2. ``test_run_query_writes_edge_rationale_to_7692`` — 真库写门, 走 **7692 测试
   容器** (D-39; ⛔ 禁 7691/7687 现网). 7692 不可达则该门 skip.

⛔ 为什么两道门都**不 mock 被测函数本身** (G-TEST-GAP):
既有 ``backend/tests/unit/test_edge_rationale_fallback.py`` 测 207/500 语义时
整体 ``patch("app.api.v1.endpoints.edges._write_neo4j_triplet", ...)`` (实测 9
处, 行号 :65/92/118/144/168/193/218/245/279), 把**被测函数本身**换成桩 ⇒ 真实的
``execute_query`` 调用永不执行, 本缺陷对既有套件完全不可见. 本文件只注入
``_write_neo4j_triplet`` 的**依赖** (``get_neo4j_client`` / ``_write_lancedb``),
跑的是真的 ``_write_neo4j_triplet``.

⛔ 打桩为什么打**源模块** ``app.clients.neo4j_client.get_neo4j_client``, 不打
``app.api.v1.endpoints.edges.get_neo4j_client``:
``_write_neo4j_triplet`` 在**函数体内**局部 import (``edges.py:63``), edges 模块
上根本没有这个属性 —— 打 edges 路径时 ``raising=True`` 会在 setup 阶段就抛
``AttributeError``, ``raising=False`` 则 stub 根本不生效、每次调用重新 import 真
函数. 而 ``get_neo4j_client()`` 恒返 ``Neo4jClient``、**永不返 None**
(``neo4j_client.py:2754-2808`` 唯一 ``return _client_instance``, 注解非
Optional ⇒ ``edges.py:66-70`` 的 ``neo4j is None`` 是死守卫), 且 ``backend/.env``
是 ``NEO4J_ENABLED=true`` + ``NEO4J_URI`` 端口 **7691**。
在上述配置且默认 W4 豁免生效时, 若注入失效并继续执行, 真实客户端**可能**连接并写入
7691; 连接、认证或写入本身也可能失败。``W4_GUARD_NO_EXEMPT=1`` 时上述默认豁免结论
不适用。故两道门在发请求 / 发写之前都先过注入锚。

⛔ 本文件**没有**证明什么 (如实记):

* **不证明「任何 Neo4j 写失败都会记成 207」**。被刻意排除在外的那一族(门 1d 的五格)
  仍然 500, 那是**有意的**: 它们不是对端的错。
* **已知未覆盖的逃逸面**: ``neo4j._exceptions.BoltError`` 族与 packstream 解码层的
  裸 ``ValueError`` / ``struct.error`` —— 握手完成后收到畸形 Bolt 帧时会逃出
  ``edges._NEO4J_WRITE_FAILURES`` 而 500。驱动自己的连接池写的是
  ``except (Neo4jError, DriverError, BoltError)``, 但 ``BoltError`` 在私有模块里,
  本卡不引私有 API。已登记移交。
* **写确认只证明「有没有落盘」, 不证明「落的内容对不对」**: 门 1e 用 stub 造出
  「返回 1 行」即判成功, 真库门(2)才校验字段值。
* **不证明整个 pytest 进程零网络**(见下方 W4 段)。

⛔ **已知不实前提(不是本卡能修的面, 但本文件的措辞必须绕开它)**:
``_write_lancedb`` 目前**不会真写 LanceDB**。``LanceDBClient.add_documents`` 是
``async def``(``backend/lib/agentic_rag/clients/lancedb_client.py:3787`` 实测),
而 ``_write_lancedb`` 用 ``await asyncio.to_thread(client.add_documents, ...)``
调它 —— ``to_thread`` 在工作线程里只是**调用**它拿到一个协程对象就返回, 函数体一行
都不执行、也不抛异常, 于是它恒返 ``WriteStatus(success=True)`` 而零写入
(进程日志里会有 ``RuntimeWarning: coroutine ... was never awaited``)。
⇒ 本文件与 ``edges.py`` 都**不得**写「LanceDB 侧已经写成功的那一半」这类话。
``_write_lancedb`` 不在本卡可改面内(卡文 §三 禁碰), 该缺陷已登记移交。

⛔ 为什么「改前 500」不能当注入证据 (恒真判据):
改前无论 stub 是否注入都得 500 —— 注入则 stub 抛 ``AttributeError``, 未注入则
真客户端同样没有 ``execute_query``, 照样 ``AttributeError``。所以「改前 500」对
注入与否不可分辨。唯一能分辨的锚是 ``stub.calls`` 的 0→≥1 变化,
与 **sentinel 串出现在响应体 ``graphiti_status.error`` 里**。

⛔ 打桩失效时**没有第二道网络防线** (Codex r3 L3 / r4 L3 整改, 这条曾被本文件写反):
``backend/tests/support/live_port_guard.py`` 的 ``EXEMPT_MARKERS`` 含 ``integration`` /
``real_neo4j``, ``EXEMPT_PATH_PREFIXES`` 含 ``integration`` —— 本文件两项都占, 于是
**默认豁免模式下, W4 只记录、不阻止连接尝试; 注入失效可能导致真实客户端连接并写入
7691**。(措辞边界, r4 L3: 是「可能」不是「必然」—— 连接、认证或写入本身也可能失败;
反过来也不像早先注释说的那样「被拦下抛 RuntimeError」, 那句是写反的。
另: ``W4_GUARD_NO_EXEMPT=1`` 时豁免被关掉, 上述默认结论不适用。)
⇒ 本文件的注入锚是唯一防线, 因此它们承重。其中**发写 / 发请求之前的前置身份检查**
才是真正的阻止手段; 请求之后的 ``stub.calls`` 与 sentinel 是**事后证明**, 不构成阻止。
存档末行的 ``NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0 (blocked=0, advisory=0, ...)`` 的正确
读法: **账本计入的、受其覆盖的连接尝试为零**(advisory 也是 0, 不是「拦了没记」)。
它只覆盖 7691/7687 两个端口, 且 W4 自证探针明确跳过记账, 因此不等于「整进程一次
网络动作都没有」。
"""

from __future__ import annotations

import asyncio
import os
import uuid
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlsplit

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from neo4j.exceptions import (
    AuthError,
    ClientError,
    ConnectionPoolError,
    DatabaseError,
    ServiceUnavailable,
    SessionExpired,
    TransientError,
)
from tenacity import RetryError

from app.graphiti.group_id_compat import to_physical_group_id
from app.models.edge_rationale import EdgeRationaleCreate, WriteStatus

pytestmark = [pytest.mark.integration]

# 本门独有 sentinel: 只有「stub 抛出的 AttributeError 被 _write_neo4j_triplet 的
# except 元组收下并写进 WriteStatus.error」这一条路径能把它送进响应体.
# 任何其它来源的 207 都不带它.
# (⛔ 这里刻意不写 edges.py 的行号: 本卡自己的改动会让同改动面内的行号引用失实,
#  同面引用一律用符号名.)
SENTINEL = "T5B-STUB-SENTINEL"

# _write_neo4j_triplet 传给 Neo4j 的参数键 (与其 params 字典逐字一致). 改后必须是
# run_query(query, **params) 展开, 键名一个不少 —— 若有人把位置 dict 留着不展开,
# run_query(self, query, **params) 会因多一个位置实参抛 TypeError, 而 TypeError
# 不在 except 元组里 ⇒ 仍是 500, 本门照样红.
EXPECTED_PARAM_KEYS = frozenset(
    {
        "record_id",
        "edge_id",
        "source_node_id",
        "target_node_id",
        "source_concept",
        "target_concept",
        "relation_type",
        "rationale_text",
        "confidence",
        "strategies_applied",
        "questioning_rounds",
        "explanation_depth_score",
        "episode_body",
        "group_id",
    }
)

# ---------------------------------------------------------------------------
# 7692 测试容器 (D-39): 禁 7691 / 7687 现网
# ---------------------------------------------------------------------------

NEO4J_TEST_URI = os.getenv("NEO4J_TEST_URI", "bolt://localhost:7692")
NEO4J_TEST_USER = os.getenv("NEO4J_TEST_USER", "neo4j")
NEO4J_TEST_PASSWORD = os.getenv("NEO4J_TEST_PASSWORD", "testpassword")
NEO4J_TEST_DATABASE = os.getenv("NEO4J_TEST_DATABASE", "neo4j")


#: 唯一放行的测试端口. ⛔ 白名单, 不是黑名单 —— 见 _test_uri_port_is_allowed.
ALLOWED_TEST_PORT = 7692

#: 唯一放行的 scheme. ⛔ **直连**族才行, 路由族 (``neo4j://`` / ``neo4j+s://`` /
#: ``neo4j+ssc://``) 一律拒绝 —— Codex r2 HIGH-2 整改: 路由 URI 的入口端口只决定去哪台
#: 机器取**路由表**, 真正的连接目标由服务端公布的地址决定, 服务端完全可以公布
#: 7687 / 7691。也就是说「入口端口 = 7692」对路由族根本不构成「只连 7692」的保证。
#: 直连族没有这一层间接, 目标就是 URI 里写的那个 host:port。
ALLOWED_TEST_SCHEMES = frozenset({"bolt", "bolt+s", "bolt+ssc"})


def _test_uri_port_is_allowed(uri: str) -> bool:
    """要求 scheme 属直连族**且**解析出的端口恰好等于 7692; 其余一律拒绝.

    ⛔ 为什么不写 ``":7691" in uri or ":7687" in uri`` 这种黑名单 (Codex r1 HIGH 整改):
    黑名单只看得见字面量。``bolt://localhost`` 省略端口时字面量里既没有 7691 也没有
    7687, 黑名单放行, 而 neo4j 驱动会把它归一成**默认 7687 = 现网**(驱动 6.1.0 实测,
    存档 ``evidence-t-edges/whitelist-vs-blacklist-*.txt``)。同族写法还有 ``:0``
    (同样归一成 7687)。要用黑名单挡住它们, 就得穷举一切会被驱动归一成现网端口的写法
    —— 那是挡不住的。白名单只放行「解析出来确实等于 7692」的目标。

    ⛔ 为什么还要卡 scheme (Codex r2 HIGH-2 整改): 端口白名单只约束**入口** URI。
    路由族 ``neo4j://host:7692`` 的入口端口是 7692, 但驱动随后按服务端公布的路由表
    去连别的地址, 那些地址可以是 7687 / 7691。端口白名单对这条路径无能为力, 只能在
    scheme 这一层把路由族整个排除掉。

    同口径的先例: ``backend/tests/support/live_port_guard.py`` 的 ALLOWED_TEST_PORTS
    是白名单, 而 BLOCKED_PORTS 黑名单只管 socket 层的每一次 connect —— 两者语义不同,
    URI 级判定必须走白名单。
    ⚠️ **那道 socket 层门对本文件不是「第二道防线」**(r4 L3 更正, 早先这里这么写过):
    本文件占 ``integration`` marker 与路径前缀, 落在它的豁免面内, 默认只记录不阻止
    (见模块 docstring)。本函数因此不依赖它成立 —— 「门在不在」不该变成本文件正确性的
    隐含前提, 而这里它本来也不拦。
    """
    try:
        parsed = urlsplit(uri)
    except ValueError:
        # urlsplit 本身失败: 坏的 IPv6 括号、非法 netloc 等 ⇒ 拒绝
        # (r3 L2 更正: 非整数端口不在这一段抛, 见下)
        return False
    if parsed.scheme.lower() not in ALLOWED_TEST_SCHEMES:
        return False
    try:
        return parsed.port == ALLOWED_TEST_PORT
    except ValueError:
        # 读 .port 时才抛: 端口段非整数 (bolt://host:abc) 或越界 ⇒ 拒绝
        return False


def _test_neo4j_reachable() -> bool:
    """真库门用的可达性探针.

    ⛔ **惰性调用, 不在模块收集期跑** (Codex r1 HIGH 整改): 放在模块级会让
    「只选降级门」的那一跑也发起一次网络连接, 而降级门本来完全不需要 DB。
    现在是否建连完全收进真库门自己。
    """
    if not _test_uri_port_is_allowed(NEO4J_TEST_URI):
        return False
    try:
        from neo4j import GraphDatabase

        driver = GraphDatabase.driver(
            NEO4J_TEST_URI,
            auth=(NEO4J_TEST_USER, NEO4J_TEST_PASSWORD),
            connection_timeout=3.0,
        )
        try:
            driver.verify_connectivity()
            return True
        finally:
            driver.close()
    except Exception:  # noqa: BLE001 — 任何失败都视为不可达
        return False


_REAL_DB_SKIP_REASON = (
    f"Neo4j 测试容器不可达, 或 NEO4J_TEST_URI ({NEO4J_TEST_URI}) 解析出的端口不是 "
    f"{ALLOWED_TEST_PORT} (白名单拒绝, 含省略端口被驱动归一成现网 7687 的写法). "
    "启动: docker compose --profile test up -d neo4j-test"
)


# ---------------------------------------------------------------------------
# 门 1c / 1d 的类型表
# ---------------------------------------------------------------------------

#: 被收进 ``edges._NEO4J_WRITE_FAILURES`` 的「对端故障」类型 —— 每一类一道门(1c)。
#: ⛔ 这里只写**名字→类**的映射; 「它在不在生产元组里」由门自己对生产模块断言,
#: 不靠本表自证(否则就是测试与测试对账)。
_WIDENED_TYPES: Dict[str, Any] = {
    "ServiceUnavailable": ServiceUnavailable,
    "SessionExpired": SessionExpired,
    "TransientError": TransientError,
    "DatabaseError": DatabaseError,
    "RetryError": RetryError,
}

#: 被**刻意排除**的类型 —— 每一类一道反向门(1d), 必须仍然 500。
_EXCLUDED_TYPES: Dict[str, Any] = {
    "ClientError": ClientError,  # 我们发的请求不对(ParameterMissing / CypherSyntax…)
    "AuthError": AuthError,  # 凭据没配对 = 部署坏了
    "ConnectionPoolError": ConnectionPoolError,  # 连接池耗尽 = 我方 session 泄漏
    "TypeError": TypeError,  # 签名漂移
    "KeyError": KeyError,  # params 契约破裂
}


# ---------------------------------------------------------------------------
# 降级门用的 stub 与夹具
# ---------------------------------------------------------------------------


class _AttributeErrorNeo4jStub:
    """假 Neo4j 客户端: 可注入「抛什么」或「返回什么」.

    默认两个方法都抛带 sentinel 的 ``AttributeError`` —— 同时覆盖 ``execute_query``
    (改名前的调用形态) 与 ``run_query`` (改名后), 使同一个 stub 在「改前跑」与
    「改后跑」两态下都能走到抛出点, 两跑的差别只来自 edges.py 的 except 元组。

    ``exc_factory`` 让同一个 stub 抛别的类型, 供「每个被收进 except 元组的类型都要有
    一道门」与「被刻意排除的类型必须仍然 500」两组用例共用(第十四批 T5-B 第二轮补)。
    ``rows`` 让它**正常返回**指定行 —— 用来钉住写确认判据: 返回 ``[]`` 必须被记成
    写失败, 而不是像本卡第一轮那样丢弃返回值直接报 success=True。
    """

    def __init__(
        self,
        exc_factory: Optional[Any] = None,
        rows: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        self.calls = 0
        self.called_methods: List[str] = []
        self.last_args: Optional[Tuple[Any, ...]] = None
        self.last_kwargs: Optional[Dict[str, Any]] = None
        #: None ⇒ 抛默认的 AttributeError(sentinel); 否则调它拿要抛的异常实例
        self._exc_factory = exc_factory
        #: 只有 exc_factory 与本项都为 None 之外的组合才有意义: rows 非 None ⇒ 正常返回
        self._rows = rows

    def _record(self, method: str, args: Tuple[Any, ...], kwargs: Dict[str, Any]) -> None:
        self.calls += 1
        self.called_methods.append(method)
        self.last_args = args
        self.last_kwargs = kwargs

    def _outcome(self, method: str) -> List[Dict[str, Any]]:
        if self._rows is not None:
            return self._rows
        if self._exc_factory is not None:
            raise self._exc_factory()
        raise AttributeError(f"{SENTINEL}: {method} refused by T5-B stub")

    async def run_query(self, query: str, **params: Any) -> List[Dict[str, Any]]:
        self._record("run_query", (query,), params)
        return self._outcome("run_query")

    async def execute_query(self, query: str, *args: Any, **kwargs: Any) -> List[Dict[str, Any]]:
        self._record("execute_query", (query, *args), kwargs)
        return self._outcome("execute_query")


def _post_with_stub(
    monkeypatch: pytest.MonkeyPatch,
    stub: _AttributeErrorNeo4jStub,
) -> Any:
    """把 stub 注入**源模块**、把 LanceDB 侧打成功, 然后发一次请求, 返回 response.

    ⛔ 注入锚在这里统一过: 打不中就 pytest.fail 立即停 —— 本文件落在 W4 门的
    advisory 豁免面内(见模块 docstring), 打桩失效时**没有** socket 层防线。
    """
    import app.api.v1.endpoints.edges as edges_module
    import app.clients.neo4j_client as neo4j_module

    def _fake_get_neo4j_client(*args: Any, **kwargs: Any) -> _AttributeErrorNeo4jStub:
        return stub

    monkeypatch.setattr("app.clients.neo4j_client.get_neo4j_client", _fake_get_neo4j_client)
    if neo4j_module.get_neo4j_client is not _fake_get_neo4j_client:
        pytest.fail("注入锚失败: 源模块 get_neo4j_client 未被替换, 已立即停跑")

    async def _fake_write_lancedb(rationale: EdgeRationaleCreate, record_id: str) -> WriteStatus:
        return WriteStatus(success=True)

    monkeypatch.setattr(edges_module, "_write_lancedb", _fake_write_lancedb)

    assert stub.calls == 0, "stub 在发请求前不应被调用过"
    client = TestClient(_minimal_edges_app(), raise_server_exceptions=False)
    resp = client.post("/edges/record-rationale", json=_valid_payload())
    assert stub.calls >= 1, (
        f"注入锚失败: stub 一次都没被调用 (calls={stub.calls}) —— 这一跑很可能用的是"
        f"真客户端并对现网 7691 发起过连接, 请登记后再排查"
    )
    return resp


def _minimal_edges_app() -> FastAPI:
    """只挂 edges_router 的裸 app: 无 lifespan / 无 startup hook / 无中间件."""
    from app.api.v1.endpoints.edges import edges_router

    app = FastAPI()
    app.include_router(edges_router, prefix="/edges")
    return app


def _valid_payload() -> Dict[str, Any]:
    """合法 EdgeRationaleCreate payload (vault_id / group_id 双缺失 ⇒ 推导 active vault 组, 不 409)."""
    return {
        "edge_id": "edge-t5b-001",
        "source_node_id": "node-t5b-a",
        "target_node_id": "node-t5b-b",
        "source_concept": "Concept A",
        "target_concept": "Concept B",
        "relation_type": "is prerequisite for",
        "rationale_text": "A must be understood before B because of X",
        "confidence": 0.85,
        "strategies_applied": ["EI", "SE"],
        "questioning_rounds": 3,
        "explanation_depth_score": 4,
    }


# ---------------------------------------------------------------------------
# 门 1 — 降级门 (不需要 DB, 承重)
# ---------------------------------------------------------------------------


def test_neo4j_attribute_error_degrades_to_207(monkeypatch: pytest.MonkeyPatch) -> None:
    """Neo4j 侧抛 AttributeError 时, 双写端点必须记成半成功 207, 不得崩成 500.

    改前 (edges.py 调 execute_query 且 except 元组不含 AttributeError): 实得 500 = RED.
    改后 (调 run_query(**params) 且 except 元组含 AttributeError): 207 = GREEN.
    """
    import app.api.v1.endpoints.edges as edges_module
    import app.clients.neo4j_client as neo4j_module

    # ── 行为锚: 证 stub 类自己确实会抛 ──────────────────────────────────────
    # ⛔ 必须用**独立实例**: 若拿下面注入用的那个 stub 做探针, 它的 calls 会先被
    # 探针自己加成 1, 注入锚 `stub.calls >= 1` 当场退化成恒真判据.
    probe = _AttributeErrorNeo4jStub()
    with pytest.raises(AttributeError, match=SENTINEL):
        asyncio.run(probe.run_query("RETURN 1"))
    with pytest.raises(AttributeError, match=SENTINEL):
        asyncio.run(probe.execute_query("RETURN 1", {}))

    # ── 口径锚: edges 模块上没有 get_neo4j_client 属性 (局部导入) ───────────
    # 这条锚同时解释了「为什么打源模块」: 打 edges 路径必然打空.
    assert not hasattr(edges_module, "get_neo4j_client"), (
        "edges 模块上出现了 get_neo4j_client 属性 —— 局部导入前提已变, "
        "本门的打桩目标需重新评估, 否则可能打不中而真连现网"
    )

    stub = _AttributeErrorNeo4jStub()

    def _fake_get_neo4j_client(*args: Any, **kwargs: Any) -> _AttributeErrorNeo4jStub:
        return stub

    # 打**源模块**, 默认 raising=True (属性必须已存在, 打不中即刻报错)
    monkeypatch.setattr("app.clients.neo4j_client.get_neo4j_client", _fake_get_neo4j_client)

    # ⛔ 前置注入锚 (承重): 源模块属性必须已被替换. 不成立就立即停 ——
    # 继续发请求会让真 get_neo4j_client() 造出连 .env 里 7691 现网的真客户端.
    if neo4j_module.get_neo4j_client is not _fake_get_neo4j_client:
        pytest.fail(
            "注入锚失败: app.clients.neo4j_client.get_neo4j_client 未被替换; "
            "继续发请求会真连 .env 的 7691 现网, 已立即停跑"
        )

    async def _fake_write_lancedb(rationale: EdgeRationaleCreate, record_id: str) -> WriteStatus:
        return WriteStatus(success=True)

    monkeypatch.setattr(edges_module, "_write_lancedb", _fake_write_lancedb)

    assert stub.calls == 0, "注入用 stub 在发请求前不应被调用过"

    client = TestClient(_minimal_edges_app(), raise_server_exceptions=False)
    resp = client.post("/edges/record-rationale", json=_valid_payload())

    # ── 注入锚 (承重): 证 stub 真被调到 ────────────────────────────────────
    assert stub.calls >= 1, (
        f"注入锚失败: stub 一次都没被调用 (calls={stub.calls}) —— "
        "这一跑很可能用的是真客户端并对现网 7691 发起过连接, 请登记后再排查"
    )

    # ── 核心断言: 半成功 207, 不是 500 ────────────────────────────────────
    assert resp.status_code == 207, (
        f"期望 207 Multi-Status (Neo4j 失败 + LanceDB 成功 = 半成功), "
        f"实得 {resp.status_code}; 500 说明 Neo4j 侧的 AttributeError 仍在穿透 "
        f"asyncio.gather 与 handler"
    )

    body = resp.json()
    graphiti_error = body["graphiti_status"]["error"] or ""
    # ── 注入锚 (承重, 第二条): 这条 207 确实是 stub 的 AttributeError 换来的 ──
    assert SENTINEL in graphiti_error, (
        f"207 响应体里没有本门 sentinel (graphiti_status.error={graphiti_error!r}) —— "
        "这条 207 不是 stub 的 AttributeError 被 _write_neo4j_triplet 的 except 元组收下换来的"
    )
    assert body["graphiti_status"]["success"] is False
    assert body["lancedb_status"]["success"] is True
    assert body["edge_id"] == "edge-t5b-001"

    # ── 形态锚: 改后走的是 run_query 且参数按 **params 展开 ─────────────────
    assert stub.called_methods == ["run_query"], f"期望只调 run_query 一次, 实得 {stub.called_methods}"
    assert stub.last_args is not None and "CREATE (er:EdgeRationale" in stub.last_args[0]
    assert stub.last_kwargs is not None and set(stub.last_kwargs) == EXPECTED_PARAM_KEYS, (
        f"run_query 收到的关键字参数键集不符: {sorted(stub.last_kwargs or {})}"
    )
    assert stub.last_kwargs["group_id"].startswith("vault__"), "group_id 未经 to_physical_group_id 物理化 (契约 W3)"


# ---------------------------------------------------------------------------
# 门 1c — 被收进 except 元组的每一类都必须真的降级成 207 (零 DB, 承重)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "type_name",
    ["ServiceUnavailable", "SessionExpired", "TransientError", "DatabaseError", "RetryError"],
)
def test_每个被收进元组的对端故障类型都降级成_207(monkeypatch: pytest.MonkeyPatch, type_name: str) -> None:
    """逐类钉住 ``edges._NEO4J_WRITE_FAILURES`` 里新收的那几类.

    ⛔ 为什么必须逐类: 本卡第一轮只有「stub 抛 AttributeError」这一种输入, 于是把
    元组里的任何类型删掉, 三道门依然全绿 —— 门不锁修复 = 修完等于没修(第十四批
    T5-B 第二轮对抗复核报的 HIGH)。现在删掉哪一类, 对应那一格就红。

    ⛔ 类型清单**从生产模块读**, 不在测试里手抄 —— 手抄的清单必然与生产漂移。
    """
    import app.api.v1.endpoints.edges as edges_module

    exc_cls = _WIDENED_TYPES[type_name]
    # 身份判据: 这一类确实在生产的元组里(而不是测试自说自话)
    assert issubclass(exc_cls, edges_module._NEO4J_WRITE_FAILURES), (
        f"{type_name} 不在 edges._NEO4J_WRITE_FAILURES 里 —— 本门与生产元组已漂移"
    )

    stub = _AttributeErrorNeo4jStub(exc_factory=lambda: exc_cls(f"{SENTINEL}: {type_name}"))
    resp = _post_with_stub(monkeypatch, stub)

    assert resp.status_code == 207, f"{type_name} 应被记成对端写失败 ⇒ 207(LanceDB 那一半保住), 实得 {resp.status_code}"
    body = resp.json()
    assert body["graphiti_status"]["success"] is False
    assert SENTINEL in (body["graphiti_status"]["error"] or "")
    assert type_name in (body["graphiti_status"]["error"] or ""), (
        "错误串必须带类型名, 否则 ServiceUnavailable(重试有用)与 DatabaseError(对端内部错)"
        "在响应体里不可分辨, 运维无法分流"
    )
    assert body["lancedb_status"]["success"] is True


# ---------------------------------------------------------------------------
# 门 1d — 被**刻意排除**的类型必须仍然 500 (零 DB, 承重的反向门)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "type_name",
    ["ClientError", "AuthError", "ConnectionPoolError", "TypeError", "KeyError"],
)
def test_本进程与部署缺陷不得被伪装成对端写失败(monkeypatch: pytest.MonkeyPatch, type_name: str) -> None:
    """反向门: 这几类**不该**降级, 必须原样上抛成 500.

    它们的共同点是「不是对端的错」:
    - ``ClientError`` / ``AuthError``  —— 我们发的请求或凭据不对(ParameterMissing /
      CypherSyntaxError / 密码没同步)。收进 207 的后果是每个请求都 207、5xx 率恒 0、
      前端 Outbox 把 207 当「部分成功已保留」继续投递 ⇒ 数据永久丢失且无人察觉。
    - ``ConnectionPoolError`` —— 连接池耗尽, 典型成因是我方 session 泄漏。
    - ``TypeError`` / ``KeyError`` —— 签名漂移与 params 契约破裂, 纯本地缺陷。

    ⛔ 这道门是「加宽」的护栏: 没有它, 后人把 ``Neo4jError`` 或 ``Exception`` 一整族
    收进元组时不会有任何东西变红。
    """
    import app.api.v1.endpoints.edges as edges_module

    exc_cls = _EXCLUDED_TYPES[type_name]
    # 身份判据: 这一类确实**不在**生产元组里
    assert not issubclass(exc_cls, edges_module._NEO4J_WRITE_FAILURES), (
        f"{type_name} 被收进了 edges._NEO4J_WRITE_FAILURES —— 本进程/部署缺陷正在被伪装成对端写失败, 见本门 docstring"
    )

    stub = _AttributeErrorNeo4jStub(exc_factory=lambda: exc_cls(f"{SENTINEL}: {type_name}"))
    resp = _post_with_stub(monkeypatch, stub)

    assert resp.status_code == 500, (
        f"{type_name} 是本进程/部署缺陷, 必须响亮地 500, 实得 {resp.status_code}(207 = 它被静默记成了对端写失败)"
    )


# ---------------------------------------------------------------------------
# 门 1e — 写确认: run_query 返回 0 行 = 没落盘, 不得报成功 (零 DB, 承重)
# ---------------------------------------------------------------------------


def test_run_query_返回空行必须记成写失败而不是_200(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """钉住本卡第二轮修的那个假绿.

    Cypher 以 ``RETURN er.record_id AS record_id`` 收尾 ⇒ 真写成功恒返 1 行。
    ``Neo4jClient`` 在 JSON fallback 态把查询交给 ``_run_query_json_fallback``,
    而那个分发器只认 MERGE+User+Concept / MATCH+LEARNED 两族, 本卡的
    ``CREATE (er:EdgeRationale …)`` 全不命中 ⇒ 落 else 分支 **返回 [] 且不抛异常**。
    第一轮的 ``_write_neo4j_triplet`` 丢弃返回值直接 ``WriteStatus(success=True)``
    ⇒ 「Neo4j 宕机」的实际产出是 **HTTP 200「双写全部成功」而图库里什么都没有** ——
    比 500 更坏, 且这条路是本卡接通 run_query 之后才可达的。

    ⛔ 本门是零 DB 的: 直接让 stub 正常返回 ``[]``。
    """
    stub = _AttributeErrorNeo4jStub(rows=[])
    resp = _post_with_stub(monkeypatch, stub)

    assert resp.status_code != 200, "run_query 返回 0 行 = 这次写没有落盘, 端点绝不能报 200「双写全部成功」"
    assert resp.status_code == 207, f"应记成半成功 207(LanceDB 那一半保住), 实得 {resp.status_code}"
    body = resp.json()
    assert body["graphiti_status"]["success"] is False
    assert "not confirmed" in (body["graphiti_status"]["error"] or "").lower()
    assert body["lancedb_status"]["success"] is True


def test_run_query_返回一行是成功路径(monkeypatch: pytest.MonkeyPatch) -> None:
    """写确认判据的对照组: 返回 1 行必须仍是 200.

    ⛔ 没有这条对照, 上一门可以靠「把 success 永远设成 False」作弊通过。
    """
    stub = _AttributeErrorNeo4jStub(rows=[{"record_id": "whatever"}])
    resp = _post_with_stub(monkeypatch, stub)

    assert resp.status_code == 200, f"两侧都成功应为 200, 实得 {resp.status_code}"
    body = resp.json()
    assert body["graphiti_status"]["success"] is True
    assert body["lancedb_status"]["success"] is True


# ---------------------------------------------------------------------------
# 门 1f — 端到端: 真 Neo4jClient 的 JSON fallback 态 (零 DB, 零网络)
# ---------------------------------------------------------------------------


async def test_真客户端在_json_fallback_态下不得报写成功(monkeypatch: pytest.MonkeyPatch, tmp_path: Any) -> None:
    """不用 stub, 用**真的** ``Neo4jClient(use_json_fallback=True)`` 走一遍.

    这道门比 1e 强的地方: 1e 靠 stub 模拟「返回 []」这个形态, 本门证明**真实客户端
    在真实的 fallback 态下确实返回 []**——即 1e 模拟的那个形态不是我编的。
    零网络: ``use_json_fallback=True`` 时 ``Neo4jClient`` 不建任何连接,
    storage_path 指向 pytest 的 tmp_path。
    """
    from app.api.v1.endpoints.edges import _write_neo4j_triplet
    from app.clients.neo4j_client import Neo4jClient

    fallback_client = Neo4jClient(
        uri="bolt://127.0.0.1:9",  # 不会被使用: fallback 态不建连
        use_json_fallback=True,
        storage_path=tmp_path / "t5b_fallback.json",
    )
    assert fallback_client._use_json_fallback is True

    monkeypatch.setattr(
        "app.clients.neo4j_client.get_neo4j_client",
        lambda *a, **k: fallback_client,
    )

    rationale = EdgeRationaleCreate(
        edge_id="edge-t5b-fallback",
        source_node_id="node-a",
        target_node_id="node-b",
        source_concept="A",
        target_concept="B",
        relation_type="is prerequisite for",
        rationale_text="fallback gate",
        confidence=0.5,
    )
    status_ = await _write_neo4j_triplet(rationale, "t5b-fallback-rec", "vault:t5bfallback")

    assert status_.success is False, (
        "真客户端在 JSON fallback 态下对 CREATE (er:EdgeRationale …) 只会 "
        "logger.warning + 返回 [], 零写入 —— 绝不能报 success=True"
    )
    assert "not confirmed" in (status_.error or "").lower()


# ---------------------------------------------------------------------------
# 门 1b — scheme + 端口白名单行为门 (纯逻辑, 零网络; Codex r1 HIGH / r2 HIGH-2 的验伪锚)
# ---------------------------------------------------------------------------


def test_test_uri_port_whitelist_rejects_everything_but_7692() -> None:
    """钉死: 只有「直连族 scheme + 解析出的端口 == 7692」才放行, 其余一律拒绝.

    这条门是 ``_test_uri_port_is_allowed`` 的验伪锚, 两组来历:

    * **Codex r1 HIGH**——字符串黑名单 ``":7691" in uri or ":7687" in uri`` 挡不住
      「省略端口」与 ``:0``: 驱动 6.1.0 实测把这两种都归一成 ``localhost:7687``(现网),
      而黑名单对两者都放行(存档 ``evidence-t-edges/whitelist-vs-blacklist-*.txt`` 逐行)。
      ⚠️ 只有这**两种**是黑名单放行的; ``bolt://host-7692.example:7687`` 字面量里含
      ``:7687``, 黑名单也会拒 —— 下面第三条断言防的是「子串式端口判定」这一类写法,
      不是「黑名单放行」(Codex r2 LOW-3 更正: 早先注释把三种都说成黑名单放行, 不实)。
    * **Codex r2 HIGH-2**——路由族 ``neo4j://`` / ``neo4j+s://`` / ``neo4j+ssc://`` 即便
      入口端口是 7692, 真实连接目标仍由服务端公布的路由表决定, 可以是 7687 / 7691。
      端口白名单管不到它, 只能在 scheme 层整族排除。
    """
    # ── 必须放行: 直连族 + 端口 7692 ────────────────────────────────────────
    assert _test_uri_port_is_allowed("bolt://localhost:7692")
    assert _test_uri_port_is_allowed("bolt://127.0.0.1:7692")
    assert _test_uri_port_is_allowed("bolt://user@host:7692")
    assert _test_uri_port_is_allowed("BOLT://localhost:7692"), "scheme 大小写不应改变判定"
    assert _test_uri_port_is_allowed("bolt+s://localhost:7692")
    assert _test_uri_port_is_allowed("bolt://[::1]:7692"), "IPv6 括号形态"

    # ── 必须拒绝: 路由族 (r2 HIGH-2) ────────────────────────────────────────
    assert not _test_uri_port_is_allowed("neo4j://host:7692"), "路由族: 入口 7692 不保证连接目标是 7692"
    assert not _test_uri_port_is_allowed("neo4j+s://host:7692"), "路由族同上"
    assert not _test_uri_port_is_allowed("neo4j+ssc://host:7692"), "路由族同上"
    assert not _test_uri_port_is_allowed("neo4j://user@host:7692"), "路由族 + user-info"

    # ── 必须拒绝: 黑名单放行的两种 (r1 HIGH) ────────────────────────────────
    assert not _test_uri_port_is_allowed("bolt://localhost"), "省略端口 ⇒ 驱动默认 7687 = 现网"
    assert not _test_uri_port_is_allowed("bolt://localhost:0"), ":0 ⇒ 驱动归一成 7687 = 现网"

    # ── 必须拒绝: 子串式判定会放行的写法 + 现网端口 + 非法端口 ──────────────
    assert not _test_uri_port_is_allowed("bolt://host-7692.example:7687"), "主机名含 7692 但端口是现网"
    assert not _test_uri_port_is_allowed("bolt://localhost:7691")
    assert not _test_uri_port_is_allowed("bolt://localhost:7687")
    assert not _test_uri_port_is_allowed("bolt://localhost:abc"), "端口段非整数 ⇒ 解析异常也要拒绝"
    assert not _test_uri_port_is_allowed("bolt://localhost:7692 "), "尾随空格 ⇒ 拒绝"


# ---------------------------------------------------------------------------
# 门 2 — 真库写门 (7692 测试容器, 可 skip)
# ---------------------------------------------------------------------------


@pytest.mark.real_neo4j
async def test_run_query_writes_edge_rationale_to_7692(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """真库门: run_query(**params) 真把 :EdgeRationale 节点写进 7692 并能查回.

    改前 (execute_query 不存在): 抛 AttributeError = RED.
    改后: WriteStatus(success=True) 且独立客户端在 7692 查得到该 record_id.

    ⛔ skip 判定放在函数体内、不用模块级 ``skipif`` (Codex r1 HIGH 整改): ``skipif``
    的条件在**收集期**求值, 会让「只选降级门」的那一跑也建一次连接; 挪进来之后,
    降级门那一跑零网络动作。
    """
    from app.api.v1.endpoints.edges import _write_neo4j_triplet
    from app.clients.neo4j_client import Neo4jClient
    import app.clients.neo4j_client as neo4j_module

    # ⛔ 端口白名单先于一切建连: 解析出的端口不等于 7692 就地 skip, 不做任何连接尝试
    if not _test_neo4j_reachable():
        pytest.skip(_REAL_DB_SKIP_REASON)

    suffix = uuid.uuid4().hex[:12]
    record_id = f"t5b-{suffix}"
    logical_group_id = f"vault:t5bgate_{suffix}"
    physical_group_id = to_physical_group_id(logical_group_id)

    def _make_test_client() -> Neo4jClient:
        return Neo4jClient(
            uri=NEO4J_TEST_URI,
            user=NEO4J_TEST_USER,
            password=NEO4J_TEST_PASSWORD,
            database=NEO4J_TEST_DATABASE,
        )

    injected_client = _make_test_client()

    def _fake_get_neo4j_client(*args: Any, **kwargs: Any) -> Neo4jClient:
        return injected_client

    monkeypatch.setattr("app.clients.neo4j_client.get_neo4j_client", _fake_get_neo4j_client)

    # ⛔ 前置注入锚 (发写之前). 不成立就立即 pytest.fail —— 绝不能带着未生效的打桩
    # 去调 _write_neo4j_triplet: 那一调会拿到 .env 指向 7691 现网的真单例,
    # 并真往现网写 :EdgeRationale 节点。
    #
    # ⚠️ 只有**这一条**是真承重的(第十四批 T5-B 第二轮对抗复核更正)。早先这里写着
    # 「三条前置锚」, 实测另外两条都不可证伪, 已按其真实检测力改写, 不再冒充承重:
    #   - 「client 的端口是不是 7692」与上面 :435 的 skip 判据是**同一个纯函数作用在
    #     同一个字符串上**(Neo4jClient.__init__ 原样存 uri, 不归一不重写), 因此在
    #     skip 放行之后必然也放行 ⇒ 恒真。它真正能钉住的是「client 没有改写 URI」,
    #     所以改成直接断言这一点。
    #   - 「client 是不是 JSON fallback 态」在此处恒假: 该标志只可能由 run_query →
    #     initialize() 内部的 _fallback_to_json() 置位, 而那发生在本行**之后**。
    #     真正覆盖 fallback 态的是零 DB 的门 1f + 生产侧的写确认判据。
    if neo4j_module.get_neo4j_client is not _fake_get_neo4j_client:
        pytest.fail(
            "前置注入锚失败: 源模块 get_neo4j_client 未被替换 —— 继续会真往 .env 的 7691 现网写节点, 已立即停跑"
        )
    # 结构断言(非承重): client 原样保存了我们给的 URI, 没有另接别处
    assert injected_client._uri == NEO4J_TEST_URI, (
        f"Neo4jClient 改写了 uri: 传入 {NEO4J_TEST_URI!r} 实得 {injected_client._uri!r} "
        f"—— 上游 skip 判据据此失效, 需重新评估发写前的防线"
    )
    assert _test_uri_port_is_allowed(injected_client._uri), "同上: 端口白名单对该 uri 必须成立"

    rationale = EdgeRationaleCreate(
        edge_id=f"edge-{suffix}",
        source_node_id=f"node-a-{suffix}",
        target_node_id=f"node-b-{suffix}",
        source_concept="T5B Source",
        target_concept="T5B Target",
        relation_type="is prerequisite for",
        rationale_text="T5-B real-DB gate rationale text",
        confidence=0.77,
        strategies_applied=["EI", "SE"],
        questioning_rounds=2,
        explanation_depth_score=3,
    )

    verifier = _make_test_client()
    # 查回用的独立客户端同样只许连 7692 (同一条解析白名单, 不用子串判定)
    assert _test_uri_port_is_allowed(verifier._uri), f"verifier client uri 非 7692: {verifier._uri!r}"
    try:
        status = await _write_neo4j_triplet(rationale, record_id, logical_group_id)
        assert status.success is True, (
            f"真库写失败: {status.error} —— 改前这里抛 AttributeError (Neo4jClient 无 execute_query)"
        )

        rows = await verifier.run_query(
            "MATCH (er:EdgeRationale {record_id: $record_id, group_id: $group_id}) "
            "RETURN er.record_id AS record_id, er.relation_type AS relation_type, "
            "er.confidence AS confidence, er.group_id AS group_id",
            record_id=record_id,
            group_id=physical_group_id,
        )
        assert len(rows) == 1, f"期望在 7692 查回恰 1 个 :EdgeRationale 节点, 实得 {len(rows)}"
        assert rows[0]["record_id"] == record_id
        assert rows[0]["relation_type"] == "is prerequisite for"
        assert rows[0]["group_id"] == physical_group_id
        assert rows[0]["confidence"] == pytest.approx(0.77)
    finally:
        # per-test uuid 隔离 + 无条件清理: 不清会永久滞留共享 7692
        try:
            await verifier.run_query(
                "MATCH (er:EdgeRationale) WHERE er.group_id = $group_id DETACH DELETE er",
                group_id=physical_group_id,
            )
        finally:
            # 两个客户端各自嵌套 finally (Codex r1 LOW 整改): 串行写法下
            # verifier.cleanup() 抛错会让 injected_client 永远拿不到释放机会。
            try:
                await verifier.cleanup()
            finally:
                await injected_client.cleanup()
