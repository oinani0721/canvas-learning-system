"""CARD-REPLAY-REWRITE 7692 真库端到端门 (BATCH-2026-09-18-第十五批).

卡文: _bmad-output/implementation-artifacts/goal-cards/第十五批-goals/P2-C.md §一(g)
重写面: fallback_sync_service._sync_failed_writes 从「位置游标 + 长度比较 +
试过即成功」改为「稳定记录身份 + 来源 vault 落盘 + 写完读回执才算成功 +
身份日志崩溃恢复幂等 + .overflow.* 代际扫回」。

本门锁的性质（全部断言**图内事实**，不用 stats 自述替代）:

1. **身份戳条目回灌** → 图内按字段可查, 且 ``Episode {record_id}`` 恰 1。
2. **崩溃恢复幂等**: 第 2 条二次写注入 ConnectionError → pending>0; 撤掉注入
   重跑 → 全部确认, 每个 record_id 的 Episode 仍恰 1、LEARNED 边数不变。
3. **overflow 代际扫回**: tmp 下的 ``failed_writes.overflow.<定宽戳>-00.jsonl``
   被回灌且改名 ``.synced.*``。
4. **来源 vault**: 条目自带 ``vault_id`` ⇒ 组前缀是**条目**的 vault, 不是 active。
5. **历史无身份条目**: 无 vault 且未设 ``CLS_REPLAY_LEGACY_NOSCOPE_VAULT`` ⇒
   不写图、留文件、``quarantined == 1``。
6. **缺 timestamp**: 对已有更新分数的边不改分（不取 now() 覆盖）。
7. **本文件永不指向现网 7691**（驱动口径断言）。

⛔ 隔离与边界（照 test_neo4j_replay_wire_t6b.py 骨架）:
- 只连 7692 测试容器 (``NEO4J_TEST_URI``); 探针指向 7691 一律拒绝, 不可达整文件 skip。
- 五条路径常量（含新 ``SYNC_CONFIRMED_IDS_FILE``）+ 单例全部改指 tmp_path / 7692。
- 走 ``ASGITransport``（不跑 lifespan）; 触发经真实管理端点
  ``POST /api/v1/traces/replay-fallbacks``（合法 internal key）。
- DD-03 禁 mock: 回灌走真 ``Neo4jClient`` → 真 7692; 故障注入只发生在
  **真客户端实例的单点**（二次写包装), 查询路径不打桩。

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
# 模块级可达性探针 (决定整文件 skip; 7691 现网一律拒绝) —— 形态照 t6b :61-102
# ---------------------------------------------------------------------------


def _targets_only_allowed_test_ports(uri: str) -> bool:
    """URI 的驱动 canonical 初始目标端口是否全部落在测试白名单内（正向白名单）。"""
    from tests.support.live_port_guard import ALLOWED_TEST_PORTS, canonical_target_ports

    ports, _why = canonical_target_ports(uri)
    if not ports:
        return False
    return all(p in ALLOWED_TEST_PORTS for p in ports)


def _test_neo4j_reachable() -> bool:
    if not _targets_only_allowed_test_ports(NEO4J_TEST_URI):
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

GATE_PREFIX = "p2cgate"
GATE_USER_ID = "default_user"  # fallback_sync_service 写死的 userId
ADMIN_PATH = "/api/v1/traces/replay-fallbacks"
GATE_KEY = "p2cgate-internal-key"
GATE_HEADERS = {"X-CLS-Internal-Key": GATE_KEY}

#: 本次运行的独立身份（并行运行互不可见, 照 t6b :133-136 的教训）。
_GATE_RUN_ID = uuid.uuid4().hex[:12]
GATE_CANVAS = f"{GATE_PREFIX}_canvas_{_GATE_RUN_ID}"
_GATE_CONCEPT_PREFIX = f"{GATE_PREFIX}_concept_{_GATE_RUN_ID}_"
_GATE_NODE_PREFIX = f"{GATE_PREFIX}_cid_{_GATE_RUN_ID}_"
_GATE_RID_PREFIX = f"{GATE_PREFIX}_rid_{_GATE_RUN_ID}_"


def _gate_vault_id() -> str:
    """本门条目自带的来源 vault（不是 active vault —— 门 4 恰恰要区分两者）。"""
    return f"{GATE_PREFIX}_old_{_GATE_RUN_ID}"


def _cleanup_queries() -> tuple[tuple[str, dict], ...]:
    """清理查询 —— 一律精确身份（运行级前缀/等值），照 t6b :153-193 的教训。"""
    return (
        (
            "MATCH (e:Episode)-[:SCORED]->(n:Node) WHERE n.id STARTS WITH $node_prefix DETACH DELETE e",
            {"node_prefix": _GATE_NODE_PREFIX},
        ),
        (
            "MATCH (e:Episode) WHERE e.record_id STARTS WITH $rid_prefix DETACH DELETE e",
            {"rid_prefix": _GATE_RID_PREFIX},
        ),
        (
            "MATCH (c:Concept) WHERE c.name STARTS WITH $concept_prefix DETACH DELETE c",
            {"concept_prefix": _GATE_CONCEPT_PREFIX},
        ),
        (
            "MATCH (n:Node) WHERE n.id STARTS WITH $node_prefix DETACH DELETE n",
            {"node_prefix": _GATE_NODE_PREFIX},
        ),
        ("MATCH (c:Canvas) WHERE c.path = $canvas DETACH DELETE c", {"canvas": GATE_CANVAS}),
    )


def _seed_entry(
    tag: str,
    *,
    vault: str | None = None,
    record_id: str | None = None,
    ts: str | None = "2026-09-19T10:00:00",
    score: int = 73,
    concept: str | None = None,
) -> Dict[str, Any]:
    """一条「离线落盘」的评分条目（形态 = 新写侧戳过的身份条目）。"""
    entry: Dict[str, Any] = {
        "concept": concept or f"{_GATE_CONCEPT_PREFIX}{tag}",
        "concept_id": f"{_GATE_NODE_PREFIX}{tag}",
        "canvas_name": GATE_CANVAS,
        "score": score,
        "event_type": "scoring",
        "error_reason": "timeout",
    }
    if ts is not None:
        entry["timestamp"] = ts
    if vault is not None:
        entry["vault_id"] = vault
    if record_id is not None:
        entry["record_id"] = record_id
    return entry


def _settings_override(*, debug: bool, key: str) -> Callable[[], Settings]:
    """``get_settings`` 覆盖工厂 —— 形态与理由同 t6b :212-240。"""
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
    """真 Neo4jClient → 7692 + 五条暂存路径全部改指 tmp_path（含新确认日志）。"""
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

    monkeypatch.setattr(fss, "FAILED_WRITES_FILE", tmp_path / "failed_writes.jsonl")
    monkeypatch.setattr(fss, "CANVAS_EVENTS_FALLBACK_FILE", tmp_path / "canvas_events_fallback.json")
    monkeypatch.setattr(fss, "LEARNING_MEMORIES_FILE", tmp_path / "learning_memories.json")
    monkeypatch.setattr(fss, "SYNC_CHECKPOINT_FILE", tmp_path / "sync_checkpoint.json")
    monkeypatch.setattr(fss, "SYNC_CONFIRMED_IDS_FILE", tmp_path / "sync_confirmed_ids.json", raising=False)
    monkeypatch.setattr(fss, "_fallback_sync_instance", fss.FallbackSyncService(neo4j_client=client))
    monkeypatch.delenv("CLS_REPLAY_LEGACY_NOSCOPE_VAULT", raising=False)

    try:
        for q, params in _cleanup_queries():
            await client.run_query(q, **params)
        yield client
    finally:
        try:
            for q, params in _cleanup_queries():
                await client.run_query(q, **params)
        finally:
            await client.cleanup()


@pytest.fixture
def authed_app():
    from app.main import app

    app.dependency_overrides[get_settings] = _settings_override(debug=False, key=GATE_KEY)
    try:
        yield app
    finally:
        app.dependency_overrides.pop(get_settings, None)


def _client(app) -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://p2cgate")


def _write_seed(path: Path, entries: List[Dict[str, Any]]) -> None:
    path.write_text("\n".join(json.dumps(e, ensure_ascii=False) for e in entries) + "\n", encoding="utf-8")


async def _read_learned(client, concept: str) -> List[Dict[str, Any]]:
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


async def _episode_count(client, record_id: str) -> int:
    rows = await client.run_query(
        "MATCH (e:Episode) WHERE e.record_id = $rid RETURN count(e) AS c",
        rid=record_id,
    )
    return int(rows[0]["c"]) if rows else 0


async def _learned_edge_count(client, concept: str) -> int:
    rows = await client.run_query(
        """
        MATCH (:User {id: $uid})-[r:LEARNED]->(:Concept {name: $name})
        RETURN count(r) AS c
        """,
        uid=GATE_USER_ID,
        name=concept,
    )
    return int(rows[0]["c"]) if rows else 0


# ---------------------------------------------------------------------------
# 门 0 — 环境自证: 本文件永不指向现网 (照 t6b :369-391)
# ---------------------------------------------------------------------------


def test_gate_never_targets_live_7691() -> None:
    from tests.support.live_port_guard import ALLOWED_TEST_PORTS, canonical_target_ports

    ports, why = canonical_target_ports(NEO4J_TEST_URI)
    assert ports, f"URI 的驱动 canonical 端口解析失败, fail-closed: {why}"
    assert all(p in ALLOWED_TEST_PORTS for p in ports), (
        f"本门只允许测试端口 {sorted(ALLOWED_TEST_PORTS)}, 实际解析到 {ports}（{why}）"
    )
    bypass_ports, _ = canonical_target_ports("bolt://127.0.0.1:07691")
    assert bypass_ports == (7691,), f"前导零 URI 的驱动解析结果意外: {bypass_ports}"
    assert not all(p in ALLOWED_TEST_PORTS for p in bypass_ports), (
        "判据放行了 bolt://127.0.0.1:07691 —— 字符串面判据看不见这条输入"
    )


# ---------------------------------------------------------------------------
# 门 1 — 身份戳条目回灌: 图内可查 + Episode {record_id} 恰 1
# ---------------------------------------------------------------------------


async def test_identity_entry_replays_with_stable_episode(gate_client, authed_app) -> None:
    from app.services import fallback_sync_service as fss

    rid = f"{_GATE_RID_PREFIX}one"
    entry = _seed_entry("one", vault=_gate_vault_id(), record_id=rid)
    _write_seed(fss.FAILED_WRITES_FILE, [entry])

    assert await _read_learned(gate_client, entry["concept"]) == [], (
        "夹具清理失效: 回灌前图内已存在门 Concept, 正向断言将恒真"
    )

    async with _client(authed_app) as http:
        resp = await http.post(ADMIN_PATH, headers=GATE_HEADERS)

    rows = await _read_learned(gate_client, entry["concept"])
    assert rows, f"回灌后 7692 图内查不到条目（端点 {resp.status_code}: {resp.text[:200]}）"
    assert len(rows) == 1, f"同名 Concept 出现 {len(rows)} 条"
    assert rows[0]["score"] == entry["score"], f"分数不符: {rows[0]['score']!r}"
    assert rows[0]["ts"].startswith("2026-09-19T10:00:00"), f"时间戳不符: {rows[0]['ts']!r}"
    assert rows[0]["concept_group"].startswith(f"vault__{_gate_vault_id()}"), (
        f"组不是条目自带 vault: {rows[0]['concept_group']!r}"
    )
    assert await _episode_count(gate_client, rid) == 1, "Episode {record_id} 不是恰 1 个"

    assert resp.status_code == 200, f"管理端点未返回 200: {resp.status_code}"
    stats = resp.json()
    assert stats["failed_writes"].get("recovered") == 1, f"stats 不符: {stats!r}"


# ---------------------------------------------------------------------------
# 门 2 — 崩溃恢复幂等: 注入单点故障 → 重跑不重不丢
# ---------------------------------------------------------------------------


async def test_crash_recovery_is_idempotent(gate_client, authed_app, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.services import fallback_sync_service as fss

    rid1, rid2 = f"{_GATE_RID_PREFIX}c1", f"{_GATE_RID_PREFIX}c2"
    e1 = _seed_entry("c1", vault=_gate_vault_id(), record_id=rid1)
    e2 = _seed_entry("c2", vault=_gate_vault_id(), record_id=rid2, ts="2026-09-19T10:01:00")
    _write_seed(fss.FAILED_WRITES_FILE, [e1, e2])

    # 单点故障注入: 真客户端实例的**二次写**第 2 次调用抛 ConnectionError。
    # 用 getattr 容错取原方法：新函数缺失时注入成为 no-op（红会落在行为断言上，
    # 而不是 AttributeError —— 改前先红的判据要求「红在断言不是夹具」）。
    original_secondary = getattr(gate_client, "record_score_history_by_record_id", None)
    state = {"calls": 0, "fail": True}

    async def flaky_secondary(*args: Any, **kwargs: Any) -> bool:
        state["calls"] += 1
        if state["fail"] and state["calls"] == 2:
            raise ConnectionError("p2cgate injected single-point failure")
        if original_secondary is None:
            raise AssertionError("record_score_history_by_record_id 未实现（新函数缺失）")
        return await original_secondary(*args, **kwargs)

    monkeypatch.setattr(gate_client, "record_score_history_by_record_id", flaky_secondary)

    async with _client(authed_app) as http:
        first = await http.post(ADMIN_PATH, headers=GATE_HEADERS)

    assert first.status_code == 200, f"首次回灌未返回 200: {first.status_code} {first.text[:200]}"
    fw_first = first.json()["failed_writes"]
    assert fw_first.get("pending", 0) > 0, f"注入后应留下未确认条目: {fw_first!r}"
    assert fw_first.get("recovered") == 1, f"第 1 条应已确认: {fw_first!r}"

    # 图内: e1 完成（Episode 1）, e2 只到 LEARNED（Episode 0）
    assert await _episode_count(gate_client, rid1) == 1, "第 1 条 Episode 不为 1"
    assert await _episode_count(gate_client, rid2) == 0, "注入生效前第 2 条不该有 Episode"
    assert await _learned_edge_count(gate_client, e2["concept"]) == 1, "第 2 条 LEARNED 边应已在（首次写入成功）"

    # 撤掉注入, 重跑
    state["fail"] = False
    async with _client(authed_app) as http:
        second = await http.post(ADMIN_PATH, headers=GATE_HEADERS)

    assert second.status_code == 200, f"二次回灌未返回 200: {second.status_code}"
    fw_second = second.json()["failed_writes"]
    assert fw_second.get("pending") == 0, f"重跑后应全部确认: {fw_second!r}"

    # 不重: 每个 record_id 的 Episode 仍恰 1; 不丢: e2 的 Episode 补上
    assert await _episode_count(gate_client, rid1) == 1, "重跑产生了第二个 Episode（不幂等）"
    assert await _episode_count(gate_client, rid2) == 1, "第 2 条 Episode 未被补上"
    assert await _learned_edge_count(gate_client, e1["concept"]) == 1
    assert await _learned_edge_count(gate_client, e2["concept"]) == 1, "LEARNED 边数变了"


# ---------------------------------------------------------------------------
# 门 3 — overflow 代际扫回
# ---------------------------------------------------------------------------


async def test_overflow_generation_swept(gate_client, authed_app, tmp_path: Path) -> None:
    from app.services import fallback_sync_service as fss

    gen = fss.FAILED_WRITES_FILE.parent / "failed_writes.overflow.2026-09-19-130000000000-00.jsonl"
    e1 = _seed_entry("o1", vault=_gate_vault_id(), record_id=f"{_GATE_RID_PREFIX}o1")
    e2 = _seed_entry("o2", vault=_gate_vault_id(), record_id=f"{_GATE_RID_PREFIX}o2", ts="2026-09-19T10:01:00")
    _write_seed(gen, [e1, e2])

    async with _client(authed_app) as http:
        resp = await http.post(ADMIN_PATH, headers=GATE_HEADERS)

    assert await _read_learned(gate_client, e1["concept"]), "overflow 代际第 1 条未回灌"
    assert await _read_learned(gate_client, e2["concept"]), "overflow 代际第 2 条未回灌"
    assert not gen.exists(), "全部确认的 overflow 代际应被轮转走"
    synced = list(gen.parent.glob("failed_writes.overflow.*.synced.*"))
    assert synced, "未见 overflow 代际的 .synced.* 产物"
    stats = resp.json()["failed_writes"]
    assert stats.get("generations") == 1, f"generations 计数不符: {stats!r}"


# ---------------------------------------------------------------------------
# 门 4 — 来源 vault: 条目自带值优先
# ---------------------------------------------------------------------------


async def test_source_vault_wins_over_active_vault(gate_client, authed_app) -> None:
    from app.core.subject_config import build_vault_group_id
    from app.services import fallback_sync_service as fss

    vault = _gate_vault_id()
    entry = _seed_entry("vault", vault=vault, record_id=f"{_GATE_RID_PREFIX}v")
    _write_seed(fss.FAILED_WRITES_FILE, [entry])

    async with _client(authed_app) as http:
        resp = await http.post(ADMIN_PATH, headers=GATE_HEADERS)

    rows = await _read_learned(gate_client, entry["concept"])
    assert rows, f"回灌后图内查不到: {resp.status_code} {resp.text[:200]}"
    expected = to_physical_group_id(build_vault_group_id(vault, canvas_path=GATE_CANVAS))
    assert rows[0]["concept_group"] == expected, (
        f"组未按条目自带 vault 构造: {rows[0]['concept_group']!r} != {expected!r}"
    )
    assert rows[0]["concept_group"].startswith(f"vault__{GATE_PREFIX}_old_"), "组前缀不是条目的 vault"
    assert rows[0]["concept_group"] != to_physical_group_id(DEFAULT_GROUP_ID), "落进了 DEFAULT 桶"


# ---------------------------------------------------------------------------
# 门 5 — 历史无身份条目: 默认隔离
# ---------------------------------------------------------------------------


async def test_legacy_entry_without_vault_is_quarantined(gate_client, authed_app) -> None:
    from app.services import fallback_sync_service as fss

    entry = _seed_entry("legacy", vault=None, record_id=None)  # 纯历史条目: 无身份无来源
    _write_seed(fss.FAILED_WRITES_FILE, [entry])

    async with _client(authed_app) as http:
        resp = await http.post(ADMIN_PATH, headers=GATE_HEADERS)

    assert await _read_learned(gate_client, entry["concept"]) == [], (
        "缺 vault 的历史条目被写进了图（应默认隔离, 不猜 active vault）"
    )
    remaining = fss.FAILED_WRITES_FILE.read_text(encoding="utf-8")
    assert entry["concept"] in remaining, "被隔离的条目必须留在文件里（不能静默丢弃）"
    stats = resp.json()["failed_writes"]
    assert stats.get("quarantined") == 1, f"quarantined 计数不符: {stats!r}"
    assert stats.get("pending") == 1, f"pending 应含被隔离条目: {stats!r}"


# ---------------------------------------------------------------------------
# 门 6 — 缺 timestamp: 不覆盖图上更新的分数
# ---------------------------------------------------------------------------


async def test_missing_timestamp_does_not_overwrite_newer_score(gate_client, authed_app) -> None:
    from app.services import fallback_sync_service as fss

    concept = f"{_GATE_CONCEPT_PREFIX}ts"
    e1 = _seed_entry("ts1", vault=_gate_vault_id(), record_id=f"{_GATE_RID_PREFIX}t1", concept=concept, score=90)
    _write_seed(fss.FAILED_WRITES_FILE, [e1])
    async with _client(authed_app) as http:
        first = await http.post(ADMIN_PATH, headers=GATE_HEADERS)
    rows = await _read_learned(gate_client, concept)
    assert rows and rows[0]["score"] == 90, f"前置: 第一条未落 90 分: {rows!r} {first.text[:200]}"

    # 第二条: 缺 timestamp（且无 recorded_at）—— 不得取 now() 覆盖图上更新的 90 分
    e2 = _seed_entry(
        "ts2", vault=_gate_vault_id(), record_id=f"{_GATE_RID_PREFIX}t2", concept=concept, score=10, ts=None
    )
    _write_seed(fss.FAILED_WRITES_FILE, [e2])
    async with _client(authed_app) as http:
        second = await http.post(ADMIN_PATH, headers=GATE_HEADERS)

    rows_after = await _read_learned(gate_client, concept)
    assert rows_after and rows_after[0]["score"] == 90, (
        f"缺 timestamp 的条目覆盖了图上更新的分数（取 now() 的旧缺陷回归）: {rows_after!r} {second.text[:200]}"
    )
    # Codex r1 HIGH-1 修复口径（fail-closed）：缺时间戳且带 score ⇒ 不写评分历史、
    # **整条留待**（不确认）—— 条目仍在文件、pending 计入。
    assert await _episode_count(gate_client, f"{_GATE_RID_PREFIX}t2") == 0, (
        "缺时间戳条目不应写出评分历史（无可靠事件时间）"
    )
    fw = second.json()["failed_writes"]
    assert fw.get("pending") == 1, f"缺时间戳条目应留待（fail-closed）: {fw!r}"
    assert f"{_GATE_RID_PREFIX}t2" in fss.FAILED_WRITES_FILE.read_text(encoding="utf-8"), (
        "缺时间戳条目必须留在文件里"
    )
