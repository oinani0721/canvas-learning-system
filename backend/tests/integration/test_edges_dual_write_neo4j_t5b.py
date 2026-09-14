# CARD-T-EDGES (BATCH-2026-09-11-第十四批 / 车道 T5-B)
"""Edge 双写端点 Neo4j 侧的两道行为门.

被测缺陷: ``_write_neo4j_triplet`` 曾调 ``neo4j.execute_query(query, {...})``,
而 ``Neo4jClient`` 只有 ``run_query(query, **params)`` (``neo4j_client.py:536``).
``execute_query`` 不存在 ⇒ 每次调用抛 ``AttributeError``; 该函数的 except 元组
原为 ``(RuntimeError, ConnectionError, asyncio.TimeoutError, OSError)``, 不含
``AttributeError`` ⇒ 异常穿透 ``asyncio.gather`` (无 ``return_exceptions=True``)
再穿透无 try 的 handler ⇒ FastAPI 兜成 **500**, 连 LanceDB 侧已经写成功的那一半
也一起丢掉, 而不是按 Story 4.4 AC-4 记成半成功 **207**.

两道门:

1. ``test_neo4j_attribute_error_degrades_to_207`` — 降级门, **不需要任何 DB**.
   注入一个 ``run_query`` / ``execute_query`` 都抛 ``AttributeError`` 的 stub,
   LanceDB 侧打成功, 断言端点返回 207 且 ``graphiti_status.error`` 带本门独有的
   sentinel. 修复前实得 500 (RED), 修复后 207 (GREEN).
2. ``test_run_query_writes_edge_rationale_to_7692`` — 真库写门, 走 **7692 测试
   容器** (D-39; ⛔ 禁 7691/7687 现网). 7692 不可达则整门 skip, 核心缺陷仍由
   降级门覆盖.

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
是 ``NEO4J_ENABLED=true`` + ``NEO4J_URI`` 端口 **7691** ⇒ **打桩一旦失效那一跑就
会真连现网**. 故两道门在发请求 / 发写之前都先过注入锚.

⛔ 为什么「改前 500」不能当注入证据 (恒真判据):
改前无论 stub 是否注入都得 500 —— 注入则 stub 抛 ``AttributeError``, 未注入则
真客户端同样没有 ``execute_query``, 照样 ``AttributeError``. 改后同样不可分辨:
未注入时真客户端连 7691 会被 W4 门拦下抛 ``RuntimeError``, 而 ``RuntimeError``
本就在 except 元组里 ⇒ 照样得 207. 唯一能分辨的锚是
``stub.calls`` 与 **sentinel 串出现在响应体 ``graphiti_status.error`` 里**.
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


def _test_uri_port_is_allowed(uri: str) -> bool:
    """解析 URI 并要求端口**恰好**等于 7692; 解析不出端口一律拒绝.

    ⛔ 为什么不写 ``":7691" in uri or ":7687" in uri`` 这种黑名单 (Codex r1 HIGH 整改):
    黑名单只看得见字面量。``bolt://localhost`` 省略端口时字面量里既没有 7691 也没有
    7687, 黑名单放行, 而 neo4j 驱动会把它归一成**默认 7687 = 现网**。同族写法还有
    ``:0``(同样归一成 7687)、``:07692``、带 user-info 或 IPv6 括号的变体。要用黑名单
    挡住它们, 就得穷举一切会被驱动归一成现网端口的写法 —— 那是挡不住的。白名单只放行
    「解析出来确实等于 7692」的目标, 其余(含解析失败、端口缺省)全部拒绝。

    同口径的先例: ``backend/tests/support/live_port_guard.py`` 的 ALLOWED_TEST_PORTS
    是白名单, 而 BLOCKED_PORTS 黑名单只管 socket 层的每一次 connect —— 两者语义不同,
    URI 级判定必须走白名单。
    """
    try:
        return urlsplit(uri).port == ALLOWED_TEST_PORT
    except ValueError:
        # 端口段不是合法整数 (如 bolt://host:abc) ⇒ 拒绝
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
# 降级门用的 stub 与夹具
# ---------------------------------------------------------------------------


class _AttributeErrorNeo4jStub:
    """两个方法都抛带 sentinel 的 AttributeError 的假 Neo4j 客户端.

    同时覆盖 ``execute_query`` (改名前的调用形态) 与 ``run_query`` (改名后),
    使同一个 stub 在「改前跑」与「改后跑」两态下都能走到抛出点 —— 这样两跑的
    差别只来自 edges.py 的 except 元组, 不来自 stub 形态.
    """

    def __init__(self) -> None:
        self.calls = 0
        self.called_methods: List[str] = []
        self.last_args: Optional[Tuple[Any, ...]] = None
        self.last_kwargs: Optional[Dict[str, Any]] = None

    def _record(self, method: str, args: Tuple[Any, ...], kwargs: Dict[str, Any]) -> None:
        self.calls += 1
        self.called_methods.append(method)
        self.last_args = args
        self.last_kwargs = kwargs

    async def run_query(self, query: str, **params: Any) -> List[Dict[str, Any]]:
        self._record("run_query", (query,), params)
        raise AttributeError(f"{SENTINEL}: run_query refused by T5-B stub")

    async def execute_query(self, query: str, *args: Any, **kwargs: Any) -> List[Dict[str, Any]]:
        self._record("execute_query", (query, *args), kwargs)
        raise AttributeError(f"{SENTINEL}: execute_query refused by T5-B stub")


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
# 门 1b — 端口白名单行为门 (纯逻辑, 零网络; Codex r1 HIGH 整改的验伪锚)
# ---------------------------------------------------------------------------


def test_test_uri_port_whitelist_rejects_everything_but_7692() -> None:
    """钉死: 只有解析出的端口 == 7692 才放行, 其余一律拒绝.

    这条门是 ``_test_uri_port_is_allowed`` 的验伪锚 —— 它在下面几种写法上必须拒绝,
    而**字符串黑名单 ``":7691" in uri or ":7687" in uri`` 对前三种全都会放行**:
    省略端口(驱动归一成现网 7687)、``:0``(同样归一成 7687)、含 7692 子串但端口不是
    7692 的主机名。
    """
    # ── 必须放行 ────────────────────────────────────────────────────────────
    assert _test_uri_port_is_allowed("bolt://localhost:7692")
    assert _test_uri_port_is_allowed("bolt://127.0.0.1:7692")
    assert _test_uri_port_is_allowed("neo4j://user@host:7692")

    # ── 必须拒绝: 黑名单看不见的三种 ────────────────────────────────────────
    assert not _test_uri_port_is_allowed("bolt://localhost"), "省略端口 ⇒ 驱动默认 7687 = 现网"
    assert not _test_uri_port_is_allowed("bolt://localhost:0"), ":0 ⇒ 驱动归一成 7687 = 现网"
    assert not _test_uri_port_is_allowed("bolt://host-7692.example:7687"), "主机名含 7692 但端口是现网"

    # ── 必须拒绝: 现网端口与非法端口 ────────────────────────────────────────
    assert not _test_uri_port_is_allowed("bolt://localhost:7691")
    assert not _test_uri_port_is_allowed("bolt://localhost:7687")
    assert not _test_uri_port_is_allowed("bolt://localhost:abc"), "端口段非整数 ⇒ 解析异常也要拒绝"


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

    # ⛔ 前置注入锚 (承重, 发写之前). 三条任一不成立就立即 pytest.fail ——
    # 绝不能带着未生效的打桩去调 _write_neo4j_triplet: 那一调会拿到 .env 指向
    # 7691 现网的真单例, 并真往现网写 :EdgeRationale 节点.
    if neo4j_module.get_neo4j_client is not _fake_get_neo4j_client:
        pytest.fail(
            "前置注入锚失败: 源模块 get_neo4j_client 未被替换 —— 继续会真往 .env 的 7691 现网写节点, 已立即停跑"
        )
    if not _test_uri_port_is_allowed(injected_client._uri):
        # 走解析白名单而不是 ":7692" in uri 子串判定 (Codex r1 HIGH 同族整改)
        pytest.fail(
            f"前置注入锚失败: 注入的 client 解析出的端口不是 {ALLOWED_TEST_PORT} "
            f"(实测 uri={injected_client._uri!r}), 已立即停跑"
        )
    if injected_client._use_json_fallback:
        pytest.fail(
            "前置注入锚失败: 注入的 client 处于 JSON fallback 模式, 不会真写 Neo4j —— 这一跑的绿是假绿, 已立即停跑"
        )

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
