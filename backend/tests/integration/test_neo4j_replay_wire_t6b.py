"""T6-B 回灌接线真库端到端门 (BATCH-2026-09-11-第十四批 / CARD-NEO4J-REPLAY-WIRE).

卡文: _bmad-output/implementation-artifacts/goal-cards/第十四批-goals/T6-B.md §一(g)
普查: _bmad-output/审查/2026-09-14-NEO4J-REPLAY-CENSUS.md (T6-A)

本门锁的性质 —— 「Neo4j 离线时落盘的条目, 在恢复后真的回到图里」:

1. **离线写 → 恢复 → 回灌 → 图内可查**（承重）: 往 ``failed_writes.jsonl``
   (测试隔离路径) 写一条评分条目, 经**鉴权管理端点**触发
   ``FallbackSyncService.sync_all_fallbacks()``, 然后直接查 7692 断言
   ``(:User)-[:LEARNED]->(:Concept)`` 三元组按内容逐字段落库。
   ⚠️ 断言的是**图内内容**, 不是 stats 自述 —— stats 由被测代码自己产出,
   拿它当判据等于让被测对象给自己打分。
2. **幂等**: 同一条目触发两次回灌, 第二次 ``recovered == 0`` 且门前缀节点数
   与第一次后**逐一相同**。⚠️ 这条不是靠 Cypher MERGE 兜住的 ——
   ``neo4j_client.record_score_history`` 是 ``CREATE (e:Episode {id: randomUUID()})``,
   同一条目真被重放两次会多出一个 Episode。挡住重复的是
   ``_sync_failed_writes`` 成功后的 ``_rotate_file``（文件搬走 ⇒ 第二轮无输入）。
   所以节点数断言是在验**那条**防线, 不是验 MERGE。
3. **鉴权与 /system/* 逐字同口径**: 缺 header → 403、key 不匹配 → 403、
   生产态未配置 key → 503（``security.py`` Branch 3 / 4 / 1）。

⛔ 隔离与边界:
- 只连 **7692** 测试容器 (``NEO4J_TEST_URI``); 探针指向现网 7691 一律拒绝,
  不可达则整文件 skip (不假绿)。
- 三条暂存文件 + checkpoint 全部 monkeypatch 到 ``tmp_path``, 绝不碰
  ``backend/data/`` 与 ``backend/app/data/`` 下的真实暂存文件。
- 走 ``ASGITransport`` 而非 ``TestClient``: 前者**不跑 lifespan**
  (``tests/support/lifespan.py`` 记的那条现网副作用链一条都不会发生),
  且请求与夹具共用同一个事件循环 —— neo4j async driver 绑定创建时的 loop,
  TestClient 的 portal 线程另起一个 loop 会让夹具建的 driver 跨 loop 使用。
- DD-03 禁 mock: 回灌走真 ``Neo4jClient`` → 真 7692, 不打桩 sync 路径。

启动测试容器: docker compose --profile test up -d neo4j-test
"""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List

import pytest
from httpx import ASGITransport, AsyncClient

from app.config import DEFAULT_GROUP_ID, Settings, get_settings
from app.graphiti.group_id_compat import to_physical_group_id

NEO4J_TEST_URI = os.getenv("NEO4J_TEST_URI", "bolt://127.0.0.1:7692")
NEO4J_TEST_USER = os.getenv("NEO4J_TEST_USER", "neo4j")
NEO4J_TEST_PASSWORD = os.getenv("NEO4J_TEST_PASSWORD", "testpassword")

# ---------------------------------------------------------------------------
# 模块级可达性探针 (决定整文件 skip; 7691 现网一律拒绝)
# 形态同 tests/integration/test_cypher_contract_gate.py:56-74
# ---------------------------------------------------------------------------


def _test_neo4j_reachable() -> bool:
    if ":7691" in NEO4J_TEST_URI:
        # 禁碰 live: 即使有人把 NEO4J_TEST_URI 指到现网也拒绝运行
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


pytestmark = [
    pytest.mark.integration,
    pytest.mark.real_neo4j,
    pytest.mark.skipif(
        not _test_neo4j_reachable(),
        reason=(
            "Neo4j test container unreachable (or NEO4J_TEST_URI points at live "
            "7691 — refused). Start: docker compose --profile test up -d neo4j-test"
        ),
    ),
]

GATE_PREFIX = "t6bgate"
GATE_CANVAS = f"{GATE_PREFIX}_canvas"
GATE_USER_ID = "default_user"  # fallback_sync_service.py:354 写死的 userId
ADMIN_PATH = "/api/v1/traces/replay-fallbacks"
GATE_KEY = "t6bgate-internal-key"
GATE_HEADERS = {"X-CLS-Internal-Key": GATE_KEY}

_CLEANUP_QUERIES = (
    # ⚠️ Episode 必须删在 Node **之前**: Episode 的 id 是 randomUUID(), 没有门
    # 前缀可认, 唯一的抓手是它挂在哪个前缀 Node 上。若先 DETACH DELETE 了 Node,
    # 这条 MATCH 就恒不命中 = 一条永远清不到东西的死查询, 残留 Episode 会滞留在
    # 共享的 7692 容器里, 把下一轮的「节点数不变」幂等断言污染成假红。
    f"MATCH (e:Episode)-[:SCORED]->(n:Node) WHERE n.id STARTS WITH '{GATE_PREFIX}' DETACH DELETE e",
    f"MATCH (c:Concept) WHERE c.name STARTS WITH '{GATE_PREFIX}' DETACH DELETE c",
    f"MATCH (n:Node) WHERE n.id STARTS WITH '{GATE_PREFIX}' DETACH DELETE n",
    f"MATCH (c:Canvas) WHERE c.path STARTS WITH '{GATE_PREFIX}' DETACH DELETE c",
    # 兜底: 上一条若因顺序/中断没抓到, 无邻居的 scoring Episode 一律清掉。
    # (本容器共用, 无邻居的 scoring Episode 对任何门都是垃圾。)
    "MATCH (e:Episode) WHERE e.type = 'scoring' AND NOT (e)--() DETACH DELETE e",
)


def _seed_entry() -> Dict[str, Any]:
    """造一条「Neo4j 离线时落盘」的评分条目 (字段同 memory_service 写侧形态).

    concept / concept_id 带一次性 uuid 后缀 —— 同一个 7692 容器被多条门共用,
    固定名字会让上一轮的残留节点把「回灌后图内可查」变成恒真。
    """
    tag = uuid.uuid4().hex[:12]
    return {
        "concept": f"{GATE_PREFIX}_concept_{tag}",
        "concept_id": f"{GATE_PREFIX}_cid_{tag}",
        "canvas_name": GATE_CANVAS,
        "score": 73,
        "timestamp": "2026-09-14T10:00:00",
    }


def _settings_override(*, debug: bool, key: str) -> Callable[[], Settings]:
    """``get_settings`` 覆盖工厂 —— 形态与理由同 tests/unit/test_sync_batch_auth.py.

    ``debug=False, key=""`` 这一档必须走 ``model_construct``:
    ``app/config.py::validate_security_defaults`` 是 after-validator,
    ``DEBUG=False`` + 空 key 会在**请求处理期**抛 ValueError 被
    ``CORSExceptionMiddleware`` 兜成 500, 请求根本走不到 ``security.py`` 的
    Branch 1 —— 那样测到的是配置层而非它声称要测的鉴权层。
    生产代码一字未改; 改的只是「测试如何造出『运维忘了配 key』这个非法配置」。
    """
    fields = dict(
        PROJECT_NAME="Canvas Learning System API (Test)",
        VERSION="1.0.0-test",
        DEBUG=debug,
        LOG_LEVEL="DEBUG",
        CORS_ORIGINS="http://localhost:3000",
        CANVAS_BASE_PATH="./test_canvas",
        INTERNAL_API_KEY=key,
    )

    def override() -> Settings:
        if not debug and not key:
            built = Settings.model_construct(**fields)
            assert built.DEBUG is False
            assert built.INTERNAL_API_KEY == ""
            return built
        return Settings(**fields)

    return override


# ---------------------------------------------------------------------------
# 夹具
# ---------------------------------------------------------------------------


@pytest.fixture
async def gate_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """真 Neo4jClient → 7692 + 三条暂存链全部改指 tmp_path.

    ``_fallback_sync_instance`` 被换成绑定本 client 的服务实例, 于是
    ``get_fallback_sync_service()`` (生产端点与启动钩子共用的那个工厂)
    在本门内返回的是指向测试容器的服务 —— 端点代码一字未改地被真实执行。
    """
    from app.clients.neo4j_client import Neo4jClient
    from app.services import fallback_sync_service as fss

    client = Neo4jClient(
        uri=NEO4J_TEST_URI,
        user=NEO4J_TEST_USER,
        password=NEO4J_TEST_PASSWORD,
        use_json_fallback=False,
        storage_path=tmp_path / "gate_neo4j_fallback.json",
    )
    await client.initialize()
    if client.is_fallback_mode:
        pytest.skip("Neo4j test container degraded to JSON fallback — gate void")

    # 暂存链隔离: 三个文件 + checkpoint 全部落 tmp_path。
    # ⚠️ 必须 patch ``fss`` 模块属性而不是源模块 —— fss 是
    # ``from ... import FAILED_WRITES_FILE``, 绑的是自己命名空间里的名字。
    monkeypatch.setattr(fss, "FAILED_WRITES_FILE", tmp_path / "failed_writes.jsonl")
    monkeypatch.setattr(fss, "CANVAS_EVENTS_FALLBACK_FILE", tmp_path / "canvas_events_fallback.json")
    monkeypatch.setattr(fss, "LEARNING_MEMORIES_FILE", tmp_path / "learning_memories.json")
    monkeypatch.setattr(fss, "SYNC_CHECKPOINT_FILE", tmp_path / "sync_checkpoint.json")
    monkeypatch.setattr(fss, "_fallback_sync_instance", fss.FallbackSyncService(neo4j_client=client))

    try:
        for q in _CLEANUP_QUERIES:
            await client.run_query(q)
        yield client
    finally:
        try:
            for q in _CLEANUP_QUERIES:
                await client.run_query(q)
        finally:
            await client.cleanup()


@pytest.fixture
def authed_app():
    """app + get_settings 覆盖 (配好 key 的生产态); 退出时清覆盖."""
    from app.main import app

    app.dependency_overrides[get_settings] = _settings_override(debug=False, key=GATE_KEY)
    try:
        yield app
    finally:
        app.dependency_overrides.pop(get_settings, None)


def _client(app) -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://t6bgate")


async def _write_seed(monkeypatch_path: Path, entry: Dict[str, Any]) -> None:
    """把条目写进被 patch 后的 failed_writes.jsonl (模拟离线落盘)."""
    monkeypatch_path.write_text(json.dumps(entry, ensure_ascii=False) + "\n", encoding="utf-8")


async def _gate_node_count(client) -> Dict[str, int]:
    """门前缀节点计数 —— 逐标签分开数, 便于定位是哪一类被重复创建."""
    rows: List[Dict[str, Any]] = await client.run_query(
        """
        MATCH (n)
        WHERE n.name STARTS WITH $p OR n.id STARTS WITH $p OR n.path STARTS WITH $p
        RETURN labels(n)[0] AS label, count(n) AS c
        """,
        p=GATE_PREFIX,
    )
    counts = {str(r["label"]): int(r["c"]) for r in rows}
    episodes = await client.run_query(
        """
        MATCH (e:Episode)-[:SCORED]->(n:Node)
        WHERE n.id STARTS WITH $p
        RETURN count(e) AS c
        """,
        p=GATE_PREFIX,
    )
    counts["Episode"] = int(episodes[0]["c"]) if episodes else 0
    return counts


async def _read_learned(client, concept: str) -> List[Dict[str, Any]]:
    """按 Concept 名字点查回灌产物 —— 不预设 group_id, 由断言反过来核它."""
    return await client.run_query(
        """
        MATCH (u:User {id: $uid})-[r:LEARNED]->(c:Concept {name: $name})
        RETURN c.group_id AS concept_group,
               r.group_id AS edge_group,
               r.score    AS score,
               toString(r.timestamp) AS ts
        """,
        uid=GATE_USER_ID,
        name=concept,
    )


# ---------------------------------------------------------------------------
# 门 0 — 环境自证: 本文件永不指向现网
# ---------------------------------------------------------------------------


def test_gate_never_targets_live_7691() -> None:
    """探针已拒 7691; 此断言把「禁碰 live」从注释升级为可执行契约."""
    assert ":7691" not in NEO4J_TEST_URI


# ---------------------------------------------------------------------------
# 门 1 — 承重: 离线写 → 管理端点触发 → 回灌 → 图内逐字段可查
# ---------------------------------------------------------------------------


async def test_offline_entry_replays_into_graph_via_admin_endpoint(gate_client, authed_app, tmp_path: Path) -> None:
    """离线落盘的评分条目, 经鉴权管理端点回灌后在 7692 图内按内容可查."""
    from app.services import fallback_sync_service as fss

    entry = _seed_entry()
    await _write_seed(fss.FAILED_WRITES_FILE, entry)

    # 前置自证: 回灌前图内**没有**这个 Concept —— 否则「回灌后可查」恒真。
    assert await _read_learned(gate_client, entry["concept"]) == [], (
        "夹具清理失效: 回灌前图内已存在门 Concept, 本门的正向断言将恒真"
    )

    async with _client(authed_app) as http:
        resp = await http.post(ADMIN_PATH, headers=GATE_HEADERS)

    # 承重断言放最前: 本门的主张是「图里真有这条」, 不是「端点返回了 200」。
    rows = await _read_learned(gate_client, entry["concept"])
    assert rows, (
        f"回灌后 7692 图内查不到 (:User {{id:{GATE_USER_ID!r}}})-[:LEARNED]->"
        f"(:Concept {{name:{entry['concept']!r}}}) —— 暂存条目没有被回灌。"
        f"管理端点响应: {resp.status_code} {resp.text[:300]}"
    )
    assert len(rows) == 1, f"同名 Concept 出现 {len(rows)} 条, 期望恰 1 条"

    row = rows[0]
    assert row["score"] == entry["score"], f"回灌的分数不符: {row['score']} != {entry['score']}"
    assert row["ts"].startswith("2026-09-14T10:00:00"), f"回灌的时间戳不符: {row['ts']}"

    # W1 写身份: group 必须进 MERGE 键且是物理格式, 且**不是** DEFAULT 污染桶。
    # (G2-3 之前 fallback replay 会把恢复的分数落进 DEFAULT, 主 vault 读不到。)
    assert row["concept_group"], "Concept 落库时 group_id 为空 — W1 复合写身份失效"
    assert row["concept_group"].startswith("vault__"), f"group_id 不是物理格式 vault__*: {row['concept_group']!r}"
    assert row["concept_group"] != to_physical_group_id(DEFAULT_GROUP_ID), (
        "回灌落进了 DEFAULT 污染桶 — 恢复的数据主 vault 读不到 (G2-3 回归)"
    )
    assert row["edge_group"] == row["concept_group"], (
        f"LEARNED 边与 Concept 的 group 不同组: {row['edge_group']!r} != {row['concept_group']!r}"
    )

    # 端点契约 (承重断言之后再核, 避免 404 抢在图断言之前顶掉红的身份)
    assert resp.status_code == 200, f"管理端点未返回 200: {resp.status_code} {resp.text[:300]}"
    stats = resp.json()
    assert isinstance(stats, dict) and "failed_writes" in stats, (
        f"管理端点未原样返回 sync_all_fallbacks 的 stats: {stats!r}"
    )
    assert stats["failed_writes"]["recovered"] == 1, f"stats 自述回灌数不符: {stats!r}"

    # 暂存文件已被 _rotate_file 搬走 (成功回灌的条目不再滞留)
    assert not fss.FAILED_WRITES_FILE.exists(), "回灌成功后 failed_writes.jsonl 仍在原地"


# ---------------------------------------------------------------------------
# 门 2 — 幂等: 重复触发不产生重复图数据
# ---------------------------------------------------------------------------


async def test_second_replay_is_idempotent(gate_client, authed_app, tmp_path: Path) -> None:
    """同一条目触发两次回灌: 第二次 recovered == 0 且门前缀节点数逐标签不变."""
    from app.services import fallback_sync_service as fss

    entry = _seed_entry()
    await _write_seed(fss.FAILED_WRITES_FILE, entry)

    async with _client(authed_app) as http:
        first = await http.post(ADMIN_PATH, headers=GATE_HEADERS)
        assert first.status_code == 200, f"首次回灌未返回 200: {first.status_code} {first.text[:300]}"
        assert first.json()["failed_writes"]["recovered"] == 1, (
            f"首次回灌未回灌到 1 条, 幂等断言无从谈起: {first.json()!r}"
        )
        counts_after_first = await _gate_node_count(gate_client)
        assert counts_after_first.get("Concept", 0) == 1, f"首次回灌后门 Concept 数不为 1: {counts_after_first!r}"

        second = await http.post(ADMIN_PATH, headers=GATE_HEADERS)

    assert second.status_code == 200, f"二次回灌未返回 200: {second.status_code} {second.text[:300]}"
    assert second.json()["failed_writes"]["recovered"] == 0, (
        f"二次回灌仍回灌了条目 (应为 0, 首次成功后文件已轮转): {second.json()!r}"
    )

    counts_after_second = await _gate_node_count(gate_client)
    assert counts_after_second == counts_after_first, (
        "二次回灌改变了图内节点数 — 重复回灌产生了重复数据。"
        f"首次后 {counts_after_first!r} vs 二次后 {counts_after_second!r}。"
        "注意 record_score_history 建的是 CREATE(:Episode{id:randomUUID()}), "
        "挡住重复的是 _sync_failed_writes 的 _rotate_file 而非 MERGE。"
    )


# ---------------------------------------------------------------------------
# 门 3 — 鉴权: 与 /system/* 逐字同口径 (security.py Branch 3 / 4 / 1)
# ---------------------------------------------------------------------------


# ⚠️ 这三条**必须**挂 ``gate_client``, 尽管它们一条 Cypher 都不跑。
# 正常态下鉴权依赖在 handler 之前拒掉请求, 端点体根本不执行, 不挂也零连接
# (实测 NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0)。但**负控段①**要拆掉的正是那层
# 鉴权 —— 拆掉后请求会落进端点体, ``get_fallback_sync_service()`` 返回的是
# 进程默认单例, 它按 ``backend/.env`` 的 ``NEO4J_URI=bolt://localhost:7691``
# 去连**现网**。挂上 gate_client 就把单例换成指向 7692 的实例, 于是「本门在
# 任何状态下都不指向现网」是结构性的, 不依赖「鉴权恰好先拦住」这个前提。


async def test_admin_endpoint_rejects_missing_key_403(gate_client, authed_app) -> None:
    """缺 X-CLS-Internal-Key header → 403 (security.py Branch 3)."""
    async with _client(authed_app) as http:
        resp = await http.post(ADMIN_PATH)
    assert resp.status_code == 403, f"缺 key 未被拒: {resp.status_code} {resp.text[:300]}"
    assert "invalid" in resp.json()["detail"].lower()


async def test_admin_endpoint_rejects_wrong_key_403(gate_client, authed_app) -> None:
    """key 不匹配 → 403 (security.py Branch 4)."""
    async with _client(authed_app) as http:
        resp = await http.post(ADMIN_PATH, headers={"X-CLS-Internal-Key": "wrong-key"})
    assert resp.status_code == 403, f"错 key 未被拒: {resp.status_code} {resp.text[:300]}"
    assert "invalid" in resp.json()["detail"].lower()


async def test_admin_endpoint_unconfigured_key_503(gate_client) -> None:
    """生产态未配置 INTERNAL_API_KEY → 503 fail-closed (security.py Branch 1)."""
    from app.main import app

    app.dependency_overrides[get_settings] = _settings_override(debug=False, key="")
    try:
        async with _client(app) as http:
            resp = await http.post(ADMIN_PATH)
    finally:
        app.dependency_overrides.pop(get_settings, None)

    assert resp.status_code == 503, f"未配置 key 未 fail-closed: {resp.status_code} {resp.text[:300]}"
    assert resp.json()["detail"] == "Internal API key not configured"
