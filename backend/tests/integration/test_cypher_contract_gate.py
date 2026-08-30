"""G2-1 Cypher 读写契约真库门测试 (BATCH-2026-08-27-第四批 / CARD-G2-1).

契约: .claude/rules/cypher-read-contract.md (R1-R5)
      .claude/rules/cypher-write-contract.md (W1-W5)
审计: _bmad-output/审查/G2-1-cypher-audit-2026-08-27.md

三道门, 全部跑真实 Neo4j **测试容器** (7692, 与现网 7691 物理隔离):

1. 语法门 — 契约规范形态 + cypher_with_group_filter() 注入输出在真实
   server 上 EXPLAIN 可编译 (unit 测试只断言字符串形状, 真库语法炸弹
   历史见 test_sync_real_neo4j_gate.py 的 `SET...ON CREATE SET` 实证);
   helper 的 MERGE-lead 注入产生非法 Cypher 的局限在此固化为行为证据。
2. 双 vault 读隔离行为门 — W1 复合键写入 + R1 过滤读回, 两 vault 互不
   可见 (手写 WHERE 与 helper 注入两条路径都验)。
3. Concept/LEARNED 写身份行为门 — G2-1 时期为 xfail(strict) 现状复现;
   G2-3 (BATCH-2026-08-28-第五批) 修复写路径为复合身份键后已去标翻绿:
   走真实业务写路径断言两 vault 同名概念/LEARNED 边互不覆盖。
4. G2-3 写身份扩展行为门 — 每类违规至少一条: Canvas/Node/Episode 写
   身份 (W1 #5/#6/#9/#10)、scoped delete (W2 #7/#15)、scoped update
   (W5 #16)、fallback replay 不合并 (fallback_sync_service:352/458)、
   group 缺失 fail-closed 防 500 (拒写返 False, 不抛异常不静默降级)。
5. G2-3 组解析链正向分支门 (对抗审查 2026-08-28 整改) — 门 4 全部传显式
   group_id (解析链分支 1), fail-closed 门只覆盖解析失败分支; 但生产主
   管道靠的是分支 2 (ContextVar) 与分支 3 (canvas_path 推导)。两条正向
   行为门锁死这两支, 打断任一分支即红。

⚠️ 假绿防线: 每道门的"能红"由 `backend/scripts/g23_mutation_negative_controls.py`
9 类变异机械验证 (写身份退回单键+SET / 删边降级 DEFAULT / 迁移器去 LWW 与
去去重 / 关联降级 DEFAULT / 解析链两分支各打断 / replay 退回单键 / 现网拒绝
退回子串)。改动本文件的门后请复跑它, 保证仍 9/9 能红。

启动测试容器: docker compose --profile test up -d neo4j-test
连接: NEO4J_TEST_URI (默认 bolt://127.0.0.1:7692), 探针不可达整文件 skip。
探针对 7691 (现网) 一律拒绝 — 本文件禁碰 live 库。
测试数据全部走 vault__g21gate_* / g21gate_* 前缀, setup/teardown 双向清理。
"""

from __future__ import annotations

import os

import pytest

from app.graphiti.group_id_compat import to_physical_group_id
from app.utils.cypher_helpers import cypher_with_group_filter

NEO4J_TEST_URI = os.getenv("NEO4J_TEST_URI", "bolt://127.0.0.1:7692")
NEO4J_TEST_USER = os.getenv("NEO4J_TEST_USER", "neo4j")
NEO4J_TEST_PASSWORD = os.getenv("NEO4J_TEST_PASSWORD", "testpassword")

# ---------------------------------------------------------------------------
# 模块级可达性探针 (决定整文件 skip; 7691 现网一律拒绝)
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

GATE_PREFIX = "g21gate"
GID_A_LOGICAL = f"vault:{GATE_PREFIX}_a"
GID_B_LOGICAL = f"vault:{GATE_PREFIX}_b"
GID_A = to_physical_group_id(GID_A_LOGICAL)  # vault__g21gate_a
GID_B = to_physical_group_id(GID_B_LOGICAL)  # vault__g21gate_b
SHARED_CONCEPT = f"{GATE_PREFIX}_shared_concept"

_CLEANUP_QUERIES = (
    "MATCH (n) WHERE n.group_id STARTS WITH 'vault__g21gate' DETACH DELETE n",
    f"MATCH (c:Concept) WHERE c.name STARTS WITH '{GATE_PREFIX}' DETACH DELETE c",
    f"MATCH (u:User) WHERE u.id STARTS WITH '{GATE_PREFIX}' DETACH DELETE u",
    # G2-3 门 4 清理补全 (对抗审查 2026-08-28 整改): 上面三条只匹配"带 gate
    # 前缀 group"或"前缀 name/id"。门 4 要抓的回归 (W1 退回无 group 写法)
    # 恰恰产出**无 group_id**、只有前缀 path/id 的 Canvas/Node/Episode ——
    # 不清理会永久滞留共享 7692 容器, 让回归修好后重跑仍假红。
    f"MATCH (c:Canvas) WHERE c.path STARTS WITH '{GATE_PREFIX}' DETACH DELETE c",
    f"MATCH (n:Node) WHERE n.id STARTS WITH '{GATE_PREFIX}' DETACH DELETE n",
    # Episode 无前缀字段 (id 为 randomUUID) — 按其挂靠的前缀 Node 反向删,
    # 顺带清无 group 的孤儿 scoring Episode。
    f"MATCH (e:Episode)-[:SCORED]->(n:Node) WHERE n.id STARTS WITH '{GATE_PREFIX}' DETACH DELETE e",
    "MATCH (e:Episode) WHERE e.type = 'scoring' AND e.group_id IS NULL AND NOT (e)--() DETACH DELETE e",
)


@pytest.fixture(scope="module")
def sync_driver():
    """同步 driver — 语法门 EXPLAIN 与隔离门 seed/回查用."""
    from neo4j import GraphDatabase

    driver = GraphDatabase.driver(NEO4J_TEST_URI, auth=(NEO4J_TEST_USER, NEO4J_TEST_PASSWORD))
    with driver.session() as session:
        for q in _CLEANUP_QUERIES:
            session.run(q).consume()
    yield driver
    with driver.session() as session:
        for q in _CLEANUP_QUERIES:
            session.run(q).consume()
    driver.close()


@pytest.fixture
async def gate_client(tmp_path):
    """真实 Neo4jClient 指向测试容器 — 写身份现状门走真实业务写路径.

    storage_path 指向 tmp_path: 万一触发 JSON fallback 也不污染
    backend/data/neo4j_memory.json (防御性, 探针通过时不应触发)。
    """
    from app.clients.neo4j_client import Neo4jClient

    client = Neo4jClient(
        uri=NEO4J_TEST_URI,
        user=NEO4J_TEST_USER,
        password=NEO4J_TEST_PASSWORD,
        use_json_fallback=False,
        storage_path=tmp_path / "gate_fallback.json",
    )
    await client.initialize()
    if client.is_fallback_mode:
        pytest.skip("Neo4j test container degraded to JSON fallback — gate void")
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


def _explain(driver, query: str) -> None:
    """EXPLAIN 编译一条 Cypher (不执行); 语法非法则抛 CypherSyntaxError."""
    with driver.session() as session:
        session.run(f"EXPLAIN {query}").consume()


# ---------------------------------------------------------------------------
# 门 0 — 环境自证: 本文件永不指向现网
# ---------------------------------------------------------------------------


def test_gate_never_targets_live_7691():
    """探针已拒 7691; 此断言把"禁碰 live"从注释升级为可执行契约."""
    assert ":7691" not in NEO4J_TEST_URI


# ---------------------------------------------------------------------------
# 门 1 — 语法门: 契约规范形态在真实 server 上可编译
# ---------------------------------------------------------------------------

# R/W 契约文档中的规范查询形态 (与 .claude/rules/cypher-*-contract.md 同步)
CONTRACT_PATTERNS = {
    "R1-where": "MATCH (n:Concept) WHERE n.group_id = $group_id RETURN n",
    "R1-map": "MATCH (n:Concept {group_id: $group_id, name: $name}) RETURN n",
    "R1-multi-alias": (
        "MATCH (b:CanvasBoard {name: $canvasName}) "
        "WHERE b.group_id = $g OR b.group_id STARTS WITH $p "
        "MATCH (n:CanvasNode {canvasId: b.id}) "
        "WHERE n.group_id = $g OR n.group_id STARTS WITH $p "
        "RETURN n"
    ),
    "W1-composite-merge": ("MERGE (c:Concept {name: $name, group_id: $group_id}) RETURN c"),
    "W2-scoped-delete": ("MATCH (n:Concept) WHERE n.group_id = $group_id AND n.name = $name DETACH DELETE n"),
    "W5-scoped-update": ("MATCH (c:Concept {name: $name, group_id: $group_id}) SET c.p_mastery = $val RETURN c"),
}


@pytest.mark.parametrize("pattern_name", sorted(CONTRACT_PATTERNS))
def test_syntax_gate_contract_patterns(sync_driver, pattern_name):
    """契约文档给出的规范形态必须是真实 server 认可的合法 Cypher."""
    _explain(sync_driver, CONTRACT_PATTERNS[pattern_name])


HELPER_SUPPORTED_BASES = {
    "match-return": "MATCH (n:Concept) RETURN n",
    "match-delete": "MATCH (n:Concept) DELETE n",
    "match-set": "MATCH (n:Concept) SET n.p_mastery = 1.0",
    "match-orderby": "MATCH (n:Concept) RETURN n.name ORDER BY n.name",
}


@pytest.mark.parametrize("base_name", sorted(HELPER_SUPPORTED_BASES))
def test_syntax_gate_helper_output_supported_shapes(sync_driver, base_name):
    """helper 支持面 (单 alias + MATCH 开头) 的注入输出真库可编译.

    unit 测试 (test_cypher_helpers.py) 只断言字符串形状; 这里是注入
    输出第一次过真实 server 语法编译。
    """
    injected, _params = cypher_with_group_filter(HELPER_SUPPORTED_BASES[base_name], GID_A)
    _explain(sync_driver, injected)


def test_syntax_gate_helper_output_existing_where_and(sync_driver):
    """已有 WHERE 子句 + where_keyword='AND' 的注入输出真库可编译."""
    injected, _params = cypher_with_group_filter(
        "MATCH (n:Concept) WHERE n.p_mastery > 0.5 RETURN n",
        GID_A,
        where_keyword="AND",
    )
    _explain(sync_driver, injected)


def test_helper_merge_lead_limitation_documented(sync_driver):
    """固化 helper 局限 #2 (审计 §2): MERGE 开头注入 = 非法 Cypher.

    cypher_with_group_filter 对 MERGE/CREATE 开头的写查询把 WHERE 插到
    查询最前面, 真实 server 直接 SyntaxError — 这就是"必须用 helper"的
    CLAUDE.md 条款在写侧完全失效的实证。本测试**不改 helper 行为**
    (G2-1 铁律), 只把该局限钉成可执行证据; 若未来 helper 修复此形态,
    本测试会失败提醒同步更新契约文档。
    """
    from neo4j.exceptions import CypherSyntaxError

    injected, _params = cypher_with_group_filter("MERGE (n:Concept {name: $name}) RETURN n", GID_A)
    assert injected.lstrip().upper().startswith("WHERE")  # 注入形态自证
    with pytest.raises(CypherSyntaxError):
        _explain(sync_driver, injected)


# ---------------------------------------------------------------------------
# 门 2 — 双 vault 读隔离行为门 (W1 复合键写入 + R1 过滤读回)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def dual_vault_seed(sync_driver):
    """两个 vault 各写一个同名 Concept (W1 复合键) + 一个独有 Concept."""
    with sync_driver.session() as session:
        for gid, own in ((GID_A, f"{GATE_PREFIX}_only_a"), (GID_B, f"{GATE_PREFIX}_only_b")):
            session.run(
                "MERGE (c:Concept {name: $name, group_id: $gid}) SET c.probe = $probe",
                name=SHARED_CONCEPT,
                gid=gid,
                probe=GATE_PREFIX,
            ).consume()
            session.run(
                "MERGE (c:Concept {name: $name, group_id: $gid}) SET c.probe = $probe",
                name=own,
                gid=gid,
                probe=GATE_PREFIX,
            ).consume()
    return {"a": GID_A, "b": GID_B}


def test_dual_vault_read_isolation_raw_filter(sync_driver, dual_vault_seed):
    """R1 手写 WHERE: vault A 视角只见 A 的数据, 同名概念不串."""
    with sync_driver.session() as session:
        rows = session.run(
            "MATCH (n:Concept) WHERE n.group_id = $group_id AND n.probe = $probe "
            "RETURN n.name AS name, n.group_id AS gid",
            group_id=GID_A,
            probe=GATE_PREFIX,
        ).data()
    names = sorted(r["name"] for r in rows)
    assert names == sorted([SHARED_CONCEPT, f"{GATE_PREFIX}_only_a"])
    assert all(r["gid"] == GID_A for r in rows)  # B 的同名概念不可见


def test_dual_vault_read_isolation_helper_injection(sync_driver, dual_vault_seed):
    """R1 helper 注入路径: cypher_with_group_filter 输出在真库上同等隔离."""
    injected, params = cypher_with_group_filter("MATCH (n:Concept) RETURN n.name AS name, n.group_id AS gid", GID_B)
    with sync_driver.session() as session:
        rows = [r for r in session.run(injected, params).data() if r["name"].startswith(GATE_PREFIX)]
    names = sorted(r["name"] for r in rows)
    assert names == sorted([SHARED_CONCEPT, f"{GATE_PREFIX}_only_b"])
    assert all(r["gid"] == GID_B for r in rows)


def test_dual_vault_w1_composite_key_no_collision(sync_driver, dual_vault_seed):
    """W1 复合键 MERGE 下, 同名概念在两 vault 是两个物理节点."""
    with sync_driver.session() as session:
        rows = session.run(
            "MATCH (c:Concept {name: $name}) RETURN c.group_id AS gid ORDER BY gid",
            name=SHARED_CONCEPT,
        ).data()
    assert [r["gid"] for r in rows] == [GID_A, GID_B]


# ---------------------------------------------------------------------------
# 门 3 — Concept/LEARNED 写身份行为门 (G2-3 修复后去 xfail 翻绿)
# ---------------------------------------------------------------------------
# G2-1 时期这两条为 xfail(strict) 现状复现 (审计 §5 #1: MERGE 仅按 name,
# 跨 vault 同名冲撞 + group_id last-write-wins)。G2-3 把写身份改为
# {name, group_id} 复合键后按交接设计移除 xfail 标记 — 现为正向行为门。


def _require_write_ok(**results: bool) -> None:
    """前置条件守卫: 写路径调用失败走 pytest.fail (Failed, 非 AssertionError).

    环境/写入故障与身份断言失败分离 — 保证失败原因可读。
    """
    failed = [name for name, ok in results.items() if not ok]
    if failed:
        pytest.fail(f"precondition: create_learning_relationship 返回 False: {failed}")


async def test_concept_write_identity_dual_vault_current_state(gate_client):
    """W1 行为门: 两 vault 各自持有同名 Concept 节点 (复合键语义).

    走真实业务写路径 create_learning_relationship (不 mock、不改业务
    代码) — G2-3 修复后 MERGE 按 {name, group_id} 复合身份, 第二个
    vault 的写入生成独立节点, 不再劫持第一个 vault 的归属。
    """
    ok_a = await gate_client.create_learning_relationship(
        user_id=f"{GATE_PREFIX}_user",
        concept=SHARED_CONCEPT,
        score=80,
        group_id=GID_A_LOGICAL,
    )
    ok_b = await gate_client.create_learning_relationship(
        user_id=f"{GATE_PREFIX}_user",
        concept=SHARED_CONCEPT,
        score=60,
        group_id=GID_B_LOGICAL,
    )
    _require_write_ok(ok_a=ok_a, ok_b=ok_b)

    rows = await gate_client.run_query(
        "MATCH (c:Concept {name: $name}) RETURN c.group_id AS gid ORDER BY gid",
        name=SHARED_CONCEPT,
    )
    gids = [r["gid"] for r in rows]
    # W1 语义: 两个物理节点, 各归其 vault。
    assert gids == [GID_A, GID_B], f"W1 write identity clobbered: {gids}"


async def test_learned_edge_write_identity_dual_vault_current_state(gate_client):
    """W1 行为门: 同一 user 在两 vault 各有一条 LEARNED 边, 分数互不覆盖.

    G2-3 修复后 Concept 节点按组分立, LEARNED 边身份含 {group_id} —
    每 vault 一条边, r.group_id/r.score 各归其组。
    """
    ok_a = await gate_client.create_learning_relationship(
        user_id=f"{GATE_PREFIX}_user",
        concept=SHARED_CONCEPT,
        score=80,
        group_id=GID_A_LOGICAL,
    )
    ok_b = await gate_client.create_learning_relationship(
        user_id=f"{GATE_PREFIX}_user",
        concept=SHARED_CONCEPT,
        score=60,
        group_id=GID_B_LOGICAL,
    )
    _require_write_ok(ok_a=ok_a, ok_b=ok_b)

    rows = await gate_client.run_query(
        "MATCH (:User {id: $uid})-[r:LEARNED]->(c:Concept {name: $name}) "
        "RETURN r.group_id AS gid, r.score AS score ORDER BY gid",
        uid=f"{GATE_PREFIX}_user",
        name=SHARED_CONCEPT,
    )
    # 正确的 W1 语义: 每 vault 一条边, 分数互不覆盖。
    assert [(r["gid"], r["score"]) for r in rows] == [(GID_A, 80), (GID_B, 60)], (
        f"LEARNED edge identity clobbered: {rows}"
    )


# ---------------------------------------------------------------------------
# 门 4 — G2-3 写身份扩展行为门 (BATCH-2026-08-28-第五批 / CARD-G2-3)
# 每类违规至少一条: W1 #5/#6/#9/#10、W2 #7/#15、W5 #16、fallback replay、
# group 缺失 fail-closed。全部走真实业务写路径, 不 mock。
# ---------------------------------------------------------------------------


async def test_canvas_node_write_identity_dual_vault(gate_client):
    """W1 #5 行为门: Canvas/Node 写身份 {path/id, group_id} 复合键 — 双组独立."""
    shared_canvas = f"{GATE_PREFIX}_shared.canvas"
    shared_node = f"{GATE_PREFIX}_shared_node"
    ok_a = await gate_client.create_canvas_node_relationship(
        canvas_path=shared_canvas,
        node_id=shared_node,
        node_text="from A",
        group_id=GID_A_LOGICAL,
    )
    ok_b = await gate_client.create_canvas_node_relationship(
        canvas_path=shared_canvas,
        node_id=shared_node,
        node_text="from B",
        group_id=GID_B_LOGICAL,
    )
    assert ok_a and ok_b

    rows = await gate_client.run_query(
        "MATCH (c:Canvas {path: $path}) RETURN c.group_id AS gid ORDER BY gid",
        path=shared_canvas,
    )
    assert [r["gid"] for r in rows] == [GID_A, GID_B], f"Canvas identity merged: {rows}"

    rows = await gate_client.run_query(
        "MATCH (n:Node {id: $id}) RETURN n.group_id AS gid, n.text AS text ORDER BY gid",
        id=shared_node,
    )
    # B 的写入不得覆盖 A 的 node_text (旧实现单身份节点 last-write-wins)
    assert [(r["gid"], r["text"]) for r in rows] == [
        (GID_A, "from A"),
        (GID_B, "from B"),
    ], f"Node identity clobbered: {rows}"


async def test_score_history_write_identity_dual_vault(gate_client):
    """W1 #9 行为门: record_score_history 双组独立 (Node/Canvas/Episode 全带组)."""
    node_id = f"{GATE_PREFIX}_score_node"
    canvas = f"{GATE_PREFIX}_score.canvas"
    ok_a = await gate_client.record_score_history(node_id, canvas, 80, group_id=GID_A_LOGICAL)
    ok_b = await gate_client.record_score_history(node_id, canvas, 60, group_id=GID_B_LOGICAL)
    assert ok_a and ok_b

    for gid, expected_score in ((GID_A, 80), (GID_B, 60)):
        rows = await gate_client.run_query(
            "MATCH (e:Episode {group_id: $gid})-[s:SCORED]->(n:Node {id: $id, group_id: $gid}) RETURN s.score AS score",
            gid=gid,
            id=node_id,
        )
        assert [r["score"] for r in rows] == [expected_score], f"score history crossed groups (gid={gid}): {rows}"


async def test_edge_delete_scoped_dual_vault(gate_client):
    """W2 #7 行为门: 删 A 组 CONNECTS_TO 边不影响 B 组同 edge_id 边."""
    canvas = f"{GATE_PREFIX}_edges.canvas"
    edge_id = f"{GATE_PREFIX}_edge_1"
    for gid in (GID_A_LOGICAL, GID_B_LOGICAL):
        ok = await gate_client.create_edge_relationship(
            canvas_path=canvas,
            edge_id=edge_id,
            from_node_id=f"{GATE_PREFIX}_from",
            to_node_id=f"{GATE_PREFIX}_to",
            edge_label="rel",
            group_id=gid,
        )
        assert ok

    deleted = await gate_client.delete_edge_relationship(edge_id, group_id=GID_A_LOGICAL)
    assert deleted is True

    rows = await gate_client.run_query(
        "MATCH ()-[r:CONNECTS_TO {edge_id: $eid}]->() RETURN r.group_id AS gid",
        eid=edge_id,
    )
    assert [r["gid"] for r in rows] == [GID_B], f"delete crossed groups: {rows}"


async def test_canvas_association_scoped_update_and_delete(gate_client):
    """W1 #10 + W5 #16 + W2 #15 行为门: update/delete A 组关联不动 B 组."""
    assoc_id = f"{GATE_PREFIX}_assoc_1"
    for gid in (GID_A_LOGICAL, GID_B_LOGICAL):
        ok = await gate_client.create_canvas_association(
            association_id=assoc_id,
            source_canvas=f"{GATE_PREFIX}_src.canvas",
            target_canvas=f"{GATE_PREFIX}_dst.canvas",
            association_type="related",
            confidence=1.0,
            group_id=gid,
        )
        assert ok

    # W5: update A 不动 B
    updated = await gate_client.update_canvas_association(assoc_id, confidence=0.25, group_id=GID_A_LOGICAL)
    assert updated is True
    rows = await gate_client.run_query(
        "MATCH ()-[r:ASSOCIATED_WITH {association_id: $aid}]->() "
        "RETURN r.group_id AS gid, r.confidence AS conf ORDER BY gid",
        aid=assoc_id,
    )
    assert [(r["gid"], r["conf"]) for r in rows] == [
        (GID_A, 0.25),
        (GID_B, 1.0),
    ], f"update crossed groups: {rows}"

    # W2: delete A 不影响 B
    deleted = await gate_client.delete_canvas_association(assoc_id, group_id=GID_A_LOGICAL)
    assert deleted is True
    rows = await gate_client.run_query(
        "MATCH ()-[r:ASSOCIATED_WITH {association_id: $aid}]->() RETURN r.group_id AS gid, r.confidence AS conf",
        aid=assoc_id,
    )
    assert [(r["gid"], r["conf"]) for r in rows] == [(GID_B, 1.0)], f"delete crossed groups: {rows}"


async def test_fallback_replay_write_identity_dual_vault(gate_client):
    """fallback_sync 行为门: 双 vault replay 不合并, 分数互不覆盖.

    对应 fallback_sync_service._replay_scoring_entry_to_neo4j (原 :352 违规)
    与 _replay_learning_memory_to_neo4j (原 :458 违规) 的复合键修复。
    ContextVar 切换 vault (业务真实机制), 不 mock 组解析。
    """
    from app.core.subject_config import _current_subject_id
    from app.services.fallback_sync_service import FallbackSyncService

    svc = FallbackSyncService(neo4j_client=gate_client)
    concept = f"{GATE_PREFIX}_replay_concept"
    base_entry = {
        "concept": concept,
        "canvas_name": f"{GATE_PREFIX}_replay.canvas",
        "timestamp": "2026-08-28T00:00:00",
    }

    # 写序纪律 (对抗审查 2026-08-28 整改): 单键 MERGE 的 clobber 只在"库里
    # 已有他组同名节点"时显形 —— 若某个 replay 函数只承担**第一笔**写入,
    # 把它退回单键+SET 也测不出来 (无可劫持对象)。故两个函数各承担一次
    # "第二笔": scoring A → learning B → scoring B(二笔) → learning A(二笔)。
    async def _replay(fn, gid_logical, entry):
        token = _current_subject_id.set(gid_logical)
        try:
            return await fn(entry)
        finally:
            _current_subject_id.reset(token)

    ok = [
        await _replay(svc._replay_scoring_entry_to_neo4j, GID_A_LOGICAL, {**base_entry, "score": 80}),
        await _replay(svc._replay_learning_memory_to_neo4j, GID_B_LOGICAL, {**base_entry, "score": 60}),
        # 第二笔: 此时库里已有他组同名节点, 单键回退必然 clobber
        await _replay(
            svc._replay_scoring_entry_to_neo4j,
            GID_B_LOGICAL,
            {**base_entry, "score": 61, "timestamp": "2026-08-28T01:00:00"},
        ),
        await _replay(
            svc._replay_learning_memory_to_neo4j,
            GID_A_LOGICAL,
            {**base_entry, "score": 81, "timestamp": "2026-08-28T01:00:00"},
        ),
    ]
    assert all(ok), f"replay returned False: {ok}"

    rows = await gate_client.run_query(
        "MATCH (:User {id: 'default_user'})-[r:LEARNED]->(c:Concept {name: $name}) "
        "RETURN c.group_id AS cgid, r.group_id AS rgid, r.score AS score "
        "ORDER BY cgid",
        name=concept,
    )
    # 每组恰一个节点一条边; 组内 LWW 生效 (后写的 81/61 覆盖同组先写),
    # 组间零串写。
    assert [(r["cgid"], r["rgid"], r["score"]) for r in rows] == [
        (GID_A, GID_A, 81),
        (GID_B, GID_B, 61),
    ], f"fallback replay merged across vaults: {rows}"


async def test_group_unresolvable_fail_closed_no_500(gate_client, caplog):
    """缺失路径门: group 解析失败 → 拒写返 False, 不抛异常 (防 500), 零写入.

    G2-3 (b): fail-closed 策略 — 不静默降级 DEFAULT_GROUP_ID (降级须
    [Decision] 记录), logger.error 首日观察。null 若进 MERGE 键会被
    Neo4j 服务端 500, 本门证明 null 永远到不了服务端。

    鉴别力设计 (对抗审查 2026-08-28 两轮整改):
    1. delete/update 断言落在**真实存在的目标**上 —— 只对凭空 ID 断言
       False 无法区分"fail-closed 拒绝"与"降级后没找到目标"。
    2. 目标同时在 **A 组** 与 **DEFAULT 组** 各布一条同 ID 的 canary ——
       静默降级 DEFAULT (契约明令禁止、破坏面最大的回归) 会精确命中
       DEFAULT canary 并删掉它; 只验 A 组存活抓不到这种降级。
    3. 断言 logger.error 真的发出 (fail-closed 的可观测契约, goal (b)
       首日观察要求) —— 降级路径不会记录拒绝日志。
    """
    import logging as _logging

    from app.core.subject_config import _current_subject_id

    default_gid_logical = "vault:default"
    default_gid = to_physical_group_id(default_gid_logical)

    concept = f"{GATE_PREFIX}_failclosed_concept"
    live_edge = f"{GATE_PREFIX}_fc_edge"
    live_assoc = f"{GATE_PREFIX}_fc_assoc"
    # 同 ID 双组布点: A 组 = 正常目标; DEFAULT 组 = 降级回归的 canary
    for gid in (GID_A_LOGICAL, default_gid_logical):
        assert await gate_client.create_edge_relationship(
            canvas_path=f"{GATE_PREFIX}_fc.canvas",
            edge_id=live_edge,
            from_node_id=f"{GATE_PREFIX}_fc_from",
            to_node_id=f"{GATE_PREFIX}_fc_to",
            group_id=gid,
        )
        assert await gate_client.create_canvas_association(
            association_id=live_assoc,
            source_canvas=f"{GATE_PREFIX}_fc_src.canvas",
            target_canvas=f"{GATE_PREFIX}_fc_dst.canvas",
            association_type="related",
            confidence=1.0,
            group_id=gid,
        )

    caplog.clear()
    token = _current_subject_id.set("general")  # 无 vault 上下文
    try:
        with caplog.at_level(_logging.ERROR):
            ok = await gate_client.create_learning_relationship(
                user_id=f"{GATE_PREFIX}_user_fc",
                concept=concept,
                score=50,
                group_id=None,
            )
            assert ok is False
            # W2 delete / W5 update 同口径 fail-closed
            assert await gate_client.delete_edge_relationship(live_edge) is False
            assert await gate_client.update_canvas_association(live_assoc, confidence=0.5) is False
            assert await gate_client.delete_canvas_association(live_assoc) is False
    finally:
        _current_subject_id.reset(token)

    rows = await gate_client.run_query("MATCH (c:Concept {name: $name}) RETURN count(c) AS n", name=concept)
    assert rows[0]["n"] == 0, "fail-closed path must write nothing"

    # 鉴别力核心 1: 两组目标都必须毫发无损 (DEFAULT canary 尤其 ——
    # 静默降级会精确删掉它)
    rows = await gate_client.run_query(
        "MATCH ()-[r:CONNECTS_TO {edge_id: $eid}]->() RETURN r.group_id AS gid ORDER BY gid",
        eid=live_edge,
    )
    assert sorted(r["gid"] for r in rows) == sorted([GID_A, default_gid]), (
        f"fail-closed delete removed an edge (silent DEFAULT downgrade?): {rows}"
    )
    rows = await gate_client.run_query(
        "MATCH ()-[r:ASSOCIATED_WITH {association_id: $aid}]->() "
        "RETURN r.group_id AS gid, r.confidence AS conf ORDER BY gid",
        aid=live_assoc,
    )
    assert sorted((r["gid"], r["conf"]) for r in rows) == sorted([(GID_A, 1.0), (default_gid, 1.0)]), (
        f"fail-closed update/delete touched an association: {rows}"
    )

    # 鉴别力核心 2: 四次拒绝都必须留下 fail-closed 错误日志 (goal (b))
    refusals = [r for r in caplog.records if "fail-closed" in r.message]
    assert len(refusals) >= 4, f"missing fail-closed observability: {[r.message for r in caplog.records]}"

    # DEFAULT 组 canary 不带 gate 前缀 group, 显式清理
    await gate_client.run_query(
        "MATCH ()-[r:CONNECTS_TO {edge_id: $eid, group_id: $gid}]->() DELETE r",
        eid=live_edge,
        gid=default_gid,
    )
    await gate_client.run_query(
        "MATCH ()-[r:ASSOCIATED_WITH {association_id: $aid, group_id: $gid}]->() DELETE r",
        aid=live_assoc,
        gid=default_gid,
    )
    await gate_client.run_query(
        "MATCH (c:Canvas) WHERE c.path STARTS WITH $p AND c.group_id = $gid DETACH DELETE c",
        p=GATE_PREFIX,
        gid=default_gid,
    )
    await gate_client.run_query(
        "MATCH (n:Node) WHERE n.id STARTS WITH $p AND n.group_id = $gid DETACH DELETE n",
        p=GATE_PREFIX,
        gid=default_gid,
    )


# ---------------------------------------------------------------------------
# 门 5 — 组解析链正向分支行为门 (对抗审查 2026-08-28 整改)
# 门 4 全部传显式 group_id (解析链分支 1), fail-closed 门只覆盖"解析失败"。
# 但生产主管道恰恰靠分支 2/3: memory_service 的 canvas 节点/边写入不传 group、
# canvas_service create/delete edge 只传 canvas_path。以下两条锁死这两个分支。
# ---------------------------------------------------------------------------


async def test_group_resolved_from_contextvar_branch(gate_client):
    """解析链分支 2: 不传 group_id, 由 ContextVar (请求边界 vault) 解析."""
    from app.core.subject_config import _current_subject_id

    concept = f"{GATE_PREFIX}_ctxvar_concept"
    token = _current_subject_id.set(GID_B_LOGICAL)
    try:
        ok = await gate_client.create_learning_relationship(
            user_id=f"{GATE_PREFIX}_user_ctx", concept=concept, score=70
        )
    finally:
        _current_subject_id.reset(token)
    assert ok is True

    rows = await gate_client.run_query(
        "MATCH (:User {id: $uid})-[r:LEARNED]->(c:Concept {name: $name}) RETURN c.group_id AS cgid, r.group_id AS rgid",
        uid=f"{GATE_PREFIX}_user_ctx",
        name=concept,
    )
    assert [(r["cgid"], r["rgid"]) for r in rows] == [(GID_B, GID_B)], (
        f"ContextVar branch did not attribute to the request vault: {rows}"
    )


async def test_group_resolved_from_canvas_path_branch(gate_client):
    """解析链分支 3: 无 group_id 无 ContextVar, 由 canvas_path 推导 vault:default.

    这是 memory_service.record_temporal_event 的 canvas 节点/边写入实际
    走的分支 (本卡铁律不碰 memory_service, 由 client 端兜底)。
    """
    from app.clients.neo4j_client import _resolve_physical_group_id
    from app.core.subject_config import _current_subject_id

    canvas_path = f"{GATE_PREFIX}_pathderive/{GATE_PREFIX}_board.canvas"
    node_id = f"{GATE_PREFIX}_pathderive_node"
    expected_gid = _resolve_physical_group_id(None, canvas_path)

    token = _current_subject_id.set("general")  # 无 vault 上下文 → 落 canvas 推导
    try:
        ok = await gate_client.create_canvas_node_relationship(
            canvas_path=canvas_path, node_id=node_id, node_text="derived"
        )
    finally:
        _current_subject_id.reset(token)
    assert ok is True
    assert expected_gid and expected_gid.startswith("vault__"), f"derived gid not physical: {expected_gid}"

    rows = await gate_client.run_query(
        "MATCH (c:Canvas {path: $path})-[r:CONTAINS_NODE]->(n:Node {id: $nid}) "
        "RETURN c.group_id AS cgid, n.group_id AS ngid, r.group_id AS rgid",
        path=canvas_path,
        nid=node_id,
    )
    assert [(r["cgid"], r["ngid"], r["rgid"]) for r in rows] == [(expected_gid, expected_gid, expected_gid)], (
        f"canvas_path derivation branch broken: {rows}"
    )

    # 清理: 该分支产出的 group 不带 gate 前缀, 模块级 cleanup 靠 path/id 兜底
    await gate_client.run_query("MATCH (c:Canvas {path: $path}) DETACH DELETE c", path=canvas_path)
    await gate_client.run_query("MATCH (n:Node {id: $nid}) DETACH DELETE n", nid=node_id)


# ---------------------------------------------------------------------------
# 门 6 — 读侧作用域行为门 (CARD-G4-1a, BATCH-2026-08-29-第六批)
#
# 门 2 只验了"同名概念在两 vault 不串"这一半 (泄漏面)。G4-1a 把 service 层的
# `group_id=None` 直通封死后, 出现了**方向相反**的新风险: 写侧按 D16 规约把
# 内容写进 vault 的二级子组 (canvas / semantic / punycode), 若读侧用等值过滤
# 锚 vault 根组, 泄漏堵住了但"复习建议整页空" —— 比泄漏更像产品坏了。
# 2026-08-30 现网 7691 只读实测: 全库唯一 Concept 与唯一 LEARNED 边都落在
# `vault__canvas_vault__xn--jhqx6ce6ettpca6420ada2925d`, vault 根组零命中。
#
# 因此本门**成对**断言, 两半缺一不可:
#   (保召回) A vault 根组读 → A 的 canvas/semantic/punycode 子组数据全部可见;
#   (零泄漏) 同一次读 → B vault 数据 0 条;
#   (保隔离) A 的 board_x 子组读 → 兄弟板 board_y 仍不可见 (证明保召回不是
#            靠"把隔离放宽成 vault 级"换来的);
#   (防误配) `vault__g21gate_a` 的前缀不得吃到 `vault__g21gate_ab`。
# 读路径走**真实生产方法** (Neo4jClient.get_review_suggestions /
# get_learning_history / get_concept_score_history、conversation_inheritance
# 的邻居查询), 不是重写一遍 Cypher 自测自。
# ---------------------------------------------------------------------------

G41A_USER = f"{GATE_PREFIX}_g41a_user"
G41A_ALIAS_USER = f"{GATE_PREFIX}_g41a_alias_user"
G41A_NODE = f"{GATE_PREFIX}_g41a_node"
G41A_CANVAS = f"{GATE_PREFIX}_g41a_board.canvas"

# A vault 的四类组: 根 / canvas 子组 / semantic 影子组 / punycode 中文白板子组
GID_A_BRDX = to_physical_group_id(f"{GID_A_LOGICAL}:board_x")
GID_A_BRDX_SEM = to_physical_group_id(f"{GID_A_LOGICAL}:board_x:semantic")
GID_A_BRDY = to_physical_group_id(f"{GID_A_LOGICAL}:board_y")
GID_A_SEM = to_physical_group_id(f"{GID_A_LOGICAL}:semantic")
GID_A_PUNY = to_physical_group_id(f"{GID_A_LOGICAL}:特征值与特征向量")
# 近似前缀的**另一个** vault — 防裸前缀误配 (vault__x 吃掉 vault__xy)
GID_AB_LOGICAL = f"vault:{GATE_PREFIX}_ab"
GID_AB = to_physical_group_id(GID_AB_LOGICAL)

#: concept 名 → 所属物理组。名字自带归属, 断言直接比集合。
_G41A_CONCEPTS = {
    f"{GATE_PREFIX}_g41a_a_root": GID_A,
    f"{GATE_PREFIX}_g41a_a_brdx": GID_A_BRDX,
    f"{GATE_PREFIX}_g41a_a_brdx_sem": GID_A_BRDX_SEM,
    f"{GATE_PREFIX}_g41a_a_brdy": GID_A_BRDY,
    f"{GATE_PREFIX}_g41a_a_sem": GID_A_SEM,
    f"{GATE_PREFIX}_g41a_a_puny": GID_A_PUNY,
    f"{GATE_PREFIX}_g41a_b_root": GID_B,
    f"{GATE_PREFIX}_g41a_ab_root": GID_AB,
}

#: score-history 五个 alias 的逐个异组样本 (H-4): key = "哪个 alias 在 B"。
#: "ok" 是全 A 正向对照 —— 没有它, "把过滤写死成永远返回空"也能让负门全绿。
_SCORE_ALIAS_CASES = {
    "ok": {"n": GID_A, "c": GID_A, "cn": GID_A, "e": GID_A, "r": GID_A},
    "n": {"n": GID_B, "c": GID_A, "cn": GID_A, "e": GID_A, "r": GID_A},
    "c": {"n": GID_A, "c": GID_B, "cn": GID_A, "e": GID_A, "r": GID_A},
    "cn": {"n": GID_A, "c": GID_A, "cn": GID_B, "e": GID_A, "r": GID_A},
    "e": {"n": GID_A, "c": GID_A, "cn": GID_A, "e": GID_B, "r": GID_A},
    "r": {"n": GID_A, "c": GID_A, "cn": GID_A, "e": GID_A, "r": GID_B},
}

#: A vault 根组读**应当**看到的全集 (保召回门的正向期望)。
#: 注意 `gid.startswith(GID_A)` 是错的 —— 它会把 `vault__g21gate_ab` 也算进来
#: (正是本门要抓的误配)。锚点必须带 `__` 定界符, 与 read_group_filter 同口径。
_A_SCOPE_EXPECTED = {
    name
    for name, gid in _G41A_CONCEPTS.items()
    if gid == GID_A or gid.startswith(GID_A + "__")
}


def test_g41a_punycode_subgroup_is_really_punycode():
    """自证: 中文白板子组确实转成了 punycode 形态 (与现网存量同形)。

    这条若红, 说明下面的"punycode 子组可见"门测的根本不是 punycode。
    """
    assert GID_A_PUNY.startswith(GID_A + "__xn--"), GID_A_PUNY
    assert GID_AB.startswith(GID_A), "近似前缀样本失效, 防误配门失去意义"
    assert GID_AB != GID_A


@pytest.fixture
async def g41a_seed(gate_client):
    """按写契约形态 (W1 复合键 + 关系带 group) 铺 8 个组的 LEARNED 数据。

    next_review 设为过去 → 全部满足 get_review_suggestions 的 due 条件。

    ⚠️ 必须**依赖 gate_client 且 function 作用域**: gate_client 在每次 setup /
    teardown 都跑 ``_CLEANUP_QUERIES``, 模块级 seed 会被第二个用例的 client
    清掉, 之后所有断言都对着空库假绿。声明依赖保证"先清后种"的顺序。
    """
    await gate_client.run_query("MERGE (u:User {id: $uid})", uid=G41A_USER)
    for name, gid in _G41A_CONCEPTS.items():
        await gate_client.run_query(
            """
            MERGE (c:Concept {name: $name, group_id: $gid})
            SET c.probe = $probe, c.id = $name
            WITH c
            MATCH (u:User {id: $uid})
            MERGE (u)-[r:LEARNED {group_id: $gid}]->(c)
            SET r.score = 42,
                r.review_count = 1,
                r.timestamp = $ts,
                r.next_review = datetime() - duration('P1D')
            """,
            name=name,
            gid=gid,
            uid=G41A_USER,
            probe=GATE_PREFIX,
            ts="2026-08-30T00:00:00",
        )
    # 自证 seed 真的落库了 —— 否则下面每一条"看不到 B"都可能是空库假绿
    planted = await gate_client.run_query(
        "MATCH (c:Concept) WHERE c.probe = $probe AND c.name STARTS WITH $p "
        "RETURN count(c) AS c",
        probe=GATE_PREFIX,
        p=f"{GATE_PREFIX}_g41a",
    )
    assert planted and planted[0]["c"] == len(_G41A_CONCEPTS), (
        f"g41a seed 未完整落库: {planted}"
    )
    return _G41A_CONCEPTS


def _names(rows, key="concept"):
    return {r[key] for r in rows if str(r.get(key, "")).startswith(GATE_PREFIX)}


# ── 6.1 契约片段在真实 server 上的行为 (等值 OR 前缀) ─────────────────────


async def test_g41a_contract_fragment_recall_and_isolation(gate_client, g41a_seed):
    """read_group_filter + read_scope_params 的输出在真库上同时满足保召回与零泄漏."""
    from app.core.vault_scope import read_group_filter, read_scope_params

    params = read_scope_params(GID_A_LOGICAL, context="gate")
    rows = await gate_client.run_query(
        f"MATCH (n:Concept) WHERE {read_group_filter('n')} AND n.probe = $probe "
        "RETURN n.name AS concept",
        probe=GATE_PREFIX,
        **params,
    )
    got = _names(rows)
    assert _A_SCOPE_EXPECTED <= got, (
        f"保召回门红: A vault 子组数据被误挡, 缺失 {_A_SCOPE_EXPECTED - got}"
    )
    assert f"{GATE_PREFIX}_g41a_b_root" not in got, "零泄漏门红: 读到了 B vault"
    assert f"{GATE_PREFIX}_g41a_ab_root" not in got, (
        "防误配门红: `vault__x` 前缀吃掉了另一个 vault `vault__xy`"
    )


async def test_g41a_canvas_scope_still_isolates_sibling_board(gate_client, g41a_seed):
    """保隔离: 前缀语义锚在 board_x 子组时, 兄弟板 board_y 仍不可见。

    这条是"保召回不得靠放宽隔离换取"的反向锁 —— 若有人把锚点改成 vault 根,
    本条立即红。
    """
    from app.core.vault_scope import read_group_filter, read_scope_params

    params = read_scope_params(f"{GID_A_LOGICAL}:board_x", context="gate")
    rows = await gate_client.run_query(
        f"MATCH (n:Concept) WHERE {read_group_filter('n')} AND n.probe = $probe "
        "RETURN n.name AS concept",
        probe=GATE_PREFIX,
        **params,
    )
    got = _names(rows)
    assert got == {
        f"{GATE_PREFIX}_g41a_a_brdx",
        f"{GATE_PREFIX}_g41a_a_brdx_sem",  # 自己的影子子组仍在可见面内
    }, f"canvas 级作用域的可见面不对: {got}"


# ── 6.2 真实生产读路径 (Neo4jClient 方法) ────────────────────────────────


async def test_g41a_review_suggestions_recall_and_isolation_in_one_read(
    gate_client, g41a_seed
):
    """用户可感门: vault 根组读"复习建议"必须**在同一个结果集里**同时满足
    保召回与零泄漏。

    卡文 (c) 的措辞是"**同时**断言子组可见 + 他库 0 条"。拆成两次独立读、
    各证一半是不够的 —— 那样只证明了"某次读能看到 A"和"某次读看不到 B",
    没证明"**这一次**读既完整又干净"。所以这里断言**精确集合相等**:
    它一次性蕴含 (i) A 的 root/canvas/semantic/punycode 子组全部在内,
    (ii) B vault 不在内, (iii) 近似前缀 vault `_ab` 不在内。

    现网风险背景: 存量 Concept/LEARNED 全在 punycode 子组, 等值过滤会让
    这个接口整页空。
    """
    rows = await gate_client.get_review_suggestions(
        user_id=G41A_USER, limit=50, group_id=GID_A_LOGICAL
    )
    got = _names(rows)

    # 一次断言同时覆盖三面 (缺失 / 多出 均会被 == 抓到)
    assert got == _A_SCOPE_EXPECTED, (
        f"缺失(保召回红): {sorted(_A_SCOPE_EXPECTED - got)}; "
        f"多出(零泄漏红): {sorted(got - _A_SCOPE_EXPECTED)}"
    )
    # 冗余但可读: 点名三类子组各自在内, 门红时能一眼看出是哪类丢了
    for kind, name in (
        ("punycode 中文白板子组", f"{GATE_PREFIX}_g41a_a_puny"),
        ("canvas 子组", f"{GATE_PREFIX}_g41a_a_brdx"),
        ("semantic 影子组", f"{GATE_PREFIX}_g41a_a_sem"),
        ("vault 根组", f"{GATE_PREFIX}_g41a_a_root"),
    ):
        assert name in got, f"保召回门红: {kind} 的待复习概念看不见"
    # 冗余但可读: 点名他库两类各自不在内
    for kind, name in (
        ("B vault", f"{GATE_PREFIX}_g41a_b_root"),
        ("近似前缀 vault (vault__x 不得吃掉 vault__xy)", f"{GATE_PREFIX}_g41a_ab_root"),
    ):
        assert name not in got, f"零泄漏门红: 读到了 {kind}"


async def test_g41a_review_suggestions_zero_cross_vault_leak(gate_client, g41a_seed):
    """同一次读: B vault 与近似前缀 vault 的待复习概念 0 条。"""
    rows = await gate_client.get_review_suggestions(
        user_id=G41A_USER, limit=50, group_id=GID_A_LOGICAL
    )
    got = _names(rows)
    assert f"{GATE_PREFIX}_g41a_b_root" not in got
    assert f"{GATE_PREFIX}_g41a_ab_root" not in got
    # 反向: B 作用域看得到自己、看不到 A
    rows_b = await gate_client.get_review_suggestions(
        user_id=G41A_USER, limit=50, group_id=GID_B_LOGICAL
    )
    got_b = _names(rows_b)
    assert got_b == {f"{GATE_PREFIX}_g41a_b_root"}, got_b


async def test_g41a_learning_history_recall_and_isolation(gate_client, g41a_seed):
    """get_learning_history 同一套语义 (r + c 双 alias 过滤)。

    与 review 门同口径: 对**同一个结果集**断言精确集合相等 —— 一次性蕴含
    "A 的四类组全在内"与"B / 近似前缀 vault 一条不在内"。
    """
    rows = await gate_client.get_learning_history(
        user_id=G41A_USER, group_id=GID_A_LOGICAL, limit=100
    )
    got = _names(rows)
    assert got == _A_SCOPE_EXPECTED, (
        f"缺失(保召回红): {sorted(_A_SCOPE_EXPECTED - got)}; "
        f"多出(零泄漏红): {sorted(got - _A_SCOPE_EXPECTED)}"
    )
    assert f"{GATE_PREFIX}_g41a_a_puny" in got, "punycode 子组的学习历史看不见"
    assert f"{GATE_PREFIX}_g41a_b_root" not in got
    assert f"{GATE_PREFIX}_g41a_ab_root" not in got


async def test_g41a_score_history_scoped_read(gate_client):
    """get_concept_score_history: 同 node id + 同 canvas path 在两 vault 各写一份,
    读侧必须只见本 vault 的分数 (审计 §5 #8 补齐)。"""
    for gid, score in ((GID_A_PUNY, 11), (GID_B, 99)):
        ok = await gate_client.record_score_history(
            concept_id=G41A_NODE,
            canvas_name=G41A_CANVAS,
            score=score,
            timestamp="2026-08-30T01:00:00",
            group_id=gid,
        )
        assert ok is True, f"seed 写入失败 (group={gid})"

    a_rows = await gate_client.get_concept_score_history(
        concept_id=G41A_NODE, canvas_name=G41A_CANVAS, limit=10, group_id=GID_A_LOGICAL
    )
    b_rows = await gate_client.get_concept_score_history(
        concept_id=G41A_NODE, canvas_name=G41A_CANVAS, limit=10, group_id=GID_B_LOGICAL
    )
    assert [r["score"] for r in a_rows] == [11], (
        f"A 作用域读到了非 A 的分数 (保召回/零泄漏双检): {a_rows}"
    )
    assert [r["score"] for r in b_rows] == [99], b_rows


async def test_g41a_score_history_fail_closed_on_unresolved_group(gate_client, monkeypatch):
    """无法解析作用域时抛错而不是返回空列表 —— 空列表会被展示成"没有历史分数"。

    Codex round-1 H-2 整改: 除了显式空白串, 还必须覆盖**生产默认**形态
    `group_id=None` + 无 per-request ContextVar + 进程无 active vault。
    旧实现复用写侧 resolver, 该形态会由 canvas_name 推导出
    `vault__default__<canvas>` —— 查询成功、零命中、被上层记成正常 empty
    并进 30s 缓存, 正是本卡要防的静默断读。
    """
    import app.config as config_mod
    from app.core.subject_config import _current_subject_id
    from app.core.vault_scope import VaultScopeUnresolved

    # 形态 1: 显式空白串 = 调用方 bug, 不得推导到别的 vault
    with pytest.raises(VaultScopeUnresolved):
        await gate_client.get_concept_score_history(
            concept_id=G41A_NODE, canvas_name=G41A_CANVAS, limit=5, group_id="   "
        )

    # 形态 2: 生产默认 None + ContextVar 未注入 + 无 active vault
    monkeypatch.setattr(config_mod, "get_current_vault_id", lambda: "default")
    token = _current_subject_id.set("general")
    try:
        with pytest.raises(VaultScopeUnresolved):
            await gate_client.get_concept_score_history(
                concept_id=G41A_NODE, canvas_name=G41A_CANVAS, limit=5
            )
    finally:
        _current_subject_id.reset(token)


# ── 6.3 逐 alias 异组负门 (Codex round-1 H-4 整改) ───────────────────────
# 6.1/6.2 的 fixture 把一条记录的所有 alias 放在同一个 group —— 任何**单个**
# alias 的过滤丢失都会被其他 alias 兜住, 门照绿 (实测: 把 read_group_filter
# 对 r 单独改成恒真, 门 6 仍 9/9 passed)。下面为每个 alias 单独构造"只有它在
# B、其余在 A"的记录: 该 alias 的过滤一旦失效, 记录就会在 A 视角下现形。


@pytest.fixture
async def g41a_alias_seed(gate_client):
    """逐 alias 异组样本。命名 `<prefix>_x<alias>` 标明哪个 alias 在 B。"""
    await gate_client.run_query("MERGE (u:User {id: $uid})", uid=G41A_ALIAS_USER)
    # review/history: (c, r) 两个 alias 各错一次
    for name, cgid, rgid in (
        (f"{GATE_PREFIX}_g41a_xr", GID_A, GID_B),  # 概念在 A, 关系在 B
        (f"{GATE_PREFIX}_g41a_xc", GID_B, GID_A),  # 概念在 B, 关系在 A
        (f"{GATE_PREFIX}_g41a_ok", GID_A, GID_A),  # 全 A — 正向对照, 必须可见
    ):
        await gate_client.run_query(
            """
            MERGE (c:Concept {name: $name, group_id: $cgid})
            SET c.probe = $probe, c.id = $name
            WITH c
            MATCH (u:User {id: $uid})
            MERGE (u)-[r:LEARNED {group_id: $rgid}]->(c)
            SET r.score = 7, r.review_count = 1, r.timestamp = $ts,
                r.next_review = datetime() - duration('P1D')
            """,
            name=name, cgid=cgid, rgid=rgid, uid=G41A_ALIAS_USER,
            probe=GATE_PREFIX, ts="2026-08-30T00:00:00",
        )

    # score history: n / c / cn / r / e 五个 alias 各错一次 + 一条全 A 对照
    for tag, gids in _SCORE_ALIAS_CASES.items():
        await gate_client.run_query(
            """
            MERGE (n:Node {id: $nid, group_id: $ngid})
            MERGE (c:Canvas {path: $path, group_id: $cgid})
            MERGE (c)-[cn:CONTAINS_NODE {group_id: $cngid}]->(n)
            CREATE (e:Episode {id: randomUUID(), type: 'scoring',
                               group_id: $egid, timestamp: datetime($ts)})
            CREATE (e)-[:SCORED {score: $score, group_id: $rgid,
                                 timestamp: datetime($ts)}]->(n)
            """,
            nid=f"{GATE_PREFIX}_g41a_sc_{tag}", path=f"{GATE_PREFIX}_g41a_sc_{tag}.canvas",
            ngid=gids["n"], cgid=gids["c"], cngid=gids["cn"],
            egid=gids["e"], rgid=gids["r"],
            score=1, ts="2026-08-30T02:00:00",
        )
    return True


@pytest.mark.parametrize(
    "crossed,visible",
    [
        (f"{GATE_PREFIX}_g41a_xr", False),  # r 在 B → r 过滤失效则现形
        (f"{GATE_PREFIX}_g41a_xc", False),  # c 在 B → c 过滤失效则现形
        (f"{GATE_PREFIX}_g41a_ok", True),   # 全 A 正向对照 (防"写死成空"假绿)
    ],
)
async def test_g41a_review_suggestions_per_alias(gate_client, g41a_alias_seed, crossed, visible):
    rows = await gate_client.get_review_suggestions(
        user_id=G41A_ALIAS_USER, limit=50, group_id=GID_A_LOGICAL
    )
    assert (crossed in _names(rows)) is visible, (
        f"{crossed} 可见性应为 {visible}; 实得 {sorted(_names(rows))}"
    )


@pytest.mark.parametrize(
    "crossed,visible",
    [
        (f"{GATE_PREFIX}_g41a_xr", False),
        (f"{GATE_PREFIX}_g41a_xc", False),
        (f"{GATE_PREFIX}_g41a_ok", True),
    ],
)
async def test_g41a_learning_history_per_alias(gate_client, g41a_alias_seed, crossed, visible):
    rows = await gate_client.get_learning_history(
        user_id=G41A_ALIAS_USER, group_id=GID_A_LOGICAL, limit=100
    )
    assert (crossed in _names(rows)) is visible, (
        f"{crossed} 可见性应为 {visible}; 实得 {sorted(_names(rows))}"
    )


@pytest.mark.parametrize("tag", sorted(_SCORE_ALIAS_CASES))
async def test_g41a_score_history_per_alias(gate_client, g41a_alias_seed, tag):
    """五个 alias 各错一次: 只有全 A 的对照能读到分数, 其余一律 0 条。"""
    rows = await gate_client.get_concept_score_history(
        concept_id=f"{GATE_PREFIX}_g41a_sc_{tag}",
        canvas_name=f"{GATE_PREFIX}_g41a_sc_{tag}.canvas",
        limit=10,
        group_id=GID_A_LOGICAL,
    )
    if tag == "ok":
        assert [r["score"] for r in rows] == [1], f"正向对照读不到分数: {rows}"
    else:
        assert rows == [], (
            f"alias {tag!r} 在 B 组却被 A 作用域读到 —— 该 alias 的过滤失效: {rows}"
        )


async def test_g41a_canvas_scope_via_production_methods(gate_client, g41a_seed):
    """M-1 整改: canvas 级作用域的隔离必须由**生产方法**证明, 不能只测 helper。

    生产方法若把 `vault:A:board_x` 错误提升成 `vault:A`, helper 门与根组生产门
    都仍绿, 但 board_x 会看到父组与兄弟板 —— 本条正是那个漏网场景的锁。
    """
    scope = f"{GID_A_LOGICAL}:board_x"
    expected = {f"{GATE_PREFIX}_g41a_a_brdx", f"{GATE_PREFIX}_g41a_a_brdx_sem"}
    for label, rows in (
        ("review", await gate_client.get_review_suggestions(
            user_id=G41A_USER, limit=50, group_id=scope)),
        ("history", await gate_client.get_learning_history(
            user_id=G41A_USER, group_id=scope, limit=100)),
    ):
        got = _names(rows)
        assert got == expected, f"{label}: canvas 作用域可见面不对 {sorted(got)}"


async def test_g41a_inheritance_neighbors_are_vault_scoped(gate_client, monkeypatch):
    """conversation_inheritance 邻居查询三 alias 过滤 (G2-2 Codex HIGH-7 移交)。

    两 vault 各建一对同名 EntityNode 邻居 —— 封堵前 A 会读到 B 的邻居名与边标签。
    """
    import app.clients.neo4j_client as neo4j_client_mod
    from app.services.conversation_inheritance import (
        _fetch_neighbor_records_for_inheritance,
    )

    monkeypatch.setattr(neo4j_client_mod, "get_neo4j_client", lambda: gate_client)

    anchor = f"{GATE_PREFIX}_g41a_anchor"
    for gid, neighbor in ((GID_A_PUNY, f"{GATE_PREFIX}_g41a_nbr_a"), (GID_B, f"{GATE_PREFIX}_g41a_nbr_b")):
        await gate_client.run_query(
            """
            MERGE (n:EntityNode {name: $anchor, group_id: $gid})
            MERGE (m:EntityNode {name: $neighbor, group_id: $gid})
            MERGE (n)-[r:RELATES_TO {group_id: $gid}]->(m)
            SET r.label = $neighbor
            """,
            anchor=anchor,
            neighbor=neighbor,
            gid=gid,
        )

    try:
        a_records = await _fetch_neighbor_records_for_inheritance(
            anchor, GID_A_LOGICAL
        )
        b_records = await _fetch_neighbor_records_for_inheritance(
            anchor, GID_B_LOGICAL
        )
        a_names = {r.get("name") for r in a_records}
        b_names = {r.get("name") for r in b_records}
        assert a_names == {f"{GATE_PREFIX}_g41a_nbr_a"}, (
            f"A 视角邻居集合不对 (保召回 punycode 子组 + 零泄漏 B): {a_names}"
        )
        assert b_names == {f"{GATE_PREFIX}_g41a_nbr_b"}, b_names
    finally:
        await gate_client.run_query(
            "MATCH (n:EntityNode) WHERE n.name STARTS WITH $p DETACH DELETE n",
            p=f"{GATE_PREFIX}_g41a",
        )


async def test_g41a_inheritance_per_alias_negative(gate_client, monkeypatch):
    """B-1 / H-4 回归锁: 三个 alias 逐个异组 + NULL 关系, 每种都必须不可见。

    ⚠️ `r` 为 NULL 的那条是 Codex round-1 **B-1** 的直接回归锁 —— 初版对关系
    alias 用了 `allow_null=True`, 理由是"两端节点已锚定, 边不可能跨库"。存量
    W1 clobber 图上这不成立: 节点可以现归 A, 而一条曾在 B 上下文生成的边仍是
    NULL group 且 label/reason 承载 B 的语义, 而本查询恰恰返回这两个字段。
    """
    import app.clients.neo4j_client as neo4j_client_mod
    from app.services.conversation_inheritance import (
        _fetch_neighbor_records_for_inheritance,
    )

    monkeypatch.setattr(neo4j_client_mod, "get_neo4j_client", lambda: gate_client)

    anchor = f"{GATE_PREFIX}_g41a_ali_anchor"
    # (邻居名, 锚点组, 邻居组, 边组 — None 表示边不带 group_id)
    cases = [
        (f"{GATE_PREFIX}_g41a_ali_ok", GID_A, GID_A, GID_A),        # 全 A: 可见
        (f"{GATE_PREFIX}_g41a_ali_xnbr", GID_A, GID_B, GID_A),      # 邻居在 B
        (f"{GATE_PREFIX}_g41a_ali_xrel", GID_A, GID_A, GID_B),      # 边在 B
        (f"{GATE_PREFIX}_g41a_ali_xnull", GID_A, GID_A, None),      # 边无 group
    ]
    try:
        for neighbor, ngid, mgid, rgid in cases:
            if rgid is None:
                await gate_client.run_query(
                    """
                    MERGE (n:EntityNode {name: $anchor, group_id: $ngid})
                    MERGE (m:EntityNode {name: $neighbor, group_id: $mgid})
                    MERGE (n)-[r:RELATES_TO {label: $neighbor}]->(m)
                    """,
                    anchor=anchor, neighbor=neighbor, ngid=ngid, mgid=mgid,
                )
            else:
                await gate_client.run_query(
                    """
                    MERGE (n:EntityNode {name: $anchor, group_id: $ngid})
                    MERGE (m:EntityNode {name: $neighbor, group_id: $mgid})
                    MERGE (n)-[r:RELATES_TO {group_id: $rgid}]->(m)
                    SET r.label = $neighbor
                    """,
                    anchor=anchor, neighbor=neighbor, ngid=ngid, mgid=mgid, rgid=rgid,
                )

        got = {
            r.get("name")
            for r in await _fetch_neighbor_records_for_inheritance(anchor, GID_A_LOGICAL)
        }
        assert got == {f"{GATE_PREFIX}_g41a_ali_ok"}, (
            "逐 alias 负门失败 — 期望只见全 A 的那条; 实得 "
            f"{sorted(x for x in got if x)}"
        )
    finally:
        await gate_client.run_query(
            "MATCH (n:EntityNode) WHERE n.name STARTS WITH $p DETACH DELETE n",
            p=f"{GATE_PREFIX}_g41a",
        )


# ---------------------------------------------------------------------------
# 门 7 — client 层读收口行为门 (CARD-G4-1b, BATCH-2026-08-31-第七批)
#
# 门 6 封的是 service 层的 BLOCKER 面 (review / history / score / inheritance)。
# 本门封 `neo4j_client` 自己剩下的 5 个读方法与 4 个 JSON 镜像, 四个主题:
#
#   7.1/7.2 concept-history —— 该方法此前**根本不查图** (无论是否连着 Neo4j
#           都只读 JSON 模拟器), 端点恒空。补真实 Cypher 后必须同时满足
#           "双 vault 各自召回自己" 与 "互不可见", 并逐 alias 可红。
#   7.3/7.4 recovery 只装本 vault 族 —— 产物进**进程级** episode 缓存,
#           泄漏面最大。方案甲 = active vault 根组 + 前缀语义。
#   7.5     LEARNED 族三条读的降级前后对拍 —— 只封一侧, "把 Neo4j 弄挂"即可
#           绕过。⚠️ 只覆盖 4 个镜像里的 `_get_all_recent_episodes_json`;
#           另三个镜像 (associations / canvas concepts / common concepts)
#           **没有任何门在证明它们与 Cypher 语义等价**, 本卡也不做这个宣称
#           (它们在真实数据上恒空, 见各自 docstring)。
#   7.6/7.7 误路由旁路 —— `_run_query_json_fallback` 按关键词派发,
#           `MATCH…LEARNED` 且无 `next_review` 的查询 (learning_history /
#           all_recent_episodes / concept_history 三条) **中途降级**时全都
#           落到 `_handle_query_history`。它若不 fail-closed, 三条刚封的读
#           只要把 Neo4j 弄挂就能整库倾倒。
#
# 断言形态一律沿用门 6: 对**同一个结果集**取精确集合相等 (否定断言在空结果
# 上恒真, 不能单用); 逐 alias 门另造"只有该 alias 在 B"的记录 + 全 A 正向
# 对照 (同组 fixture 杀不掉单 alias 变异 —— 门 6 的 H-4 教训)。
# ---------------------------------------------------------------------------


def _json_client(tmp_path, rows, name="g41b_mirror.json"):
    """构造一个 JSON 降级模式 client, 关系表按 (concept, group) 铺。

    rows: {concept_name: physical_group_id} —— 与 Cypher 侧 seed 同一份逻辑
    数据, 用于降级前后的**可见面**对拍 (见门 7.5: 比的是 concept 名集合,
    不是完整查询语义)。
    """
    import json as _json

    from app.clients.neo4j_client import Neo4jClient

    path = tmp_path / name
    data = {
        "users": [{"id": G41A_USER}],
        "concepts": [
            {"id": cname, "name": cname, "group_id": gid} for cname, gid in rows.items()
        ],
        "relationships": [
            {
                "id": f"rel-{i}",
                "user_id": G41A_USER,
                "concept_id": cname,
                "concept_name": cname,
                "timestamp": "2026-08-30T00:00:00",
                "last_score": 42,
                "next_review": "2020-01-01T00:00:00",
                "review_count": 1,
                "group_id": gid,
            }
            for i, (cname, gid) in enumerate(rows.items())
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_json.dumps(data), encoding="utf-8")
    # retry 收到最小值: 误路由门要反复触发"重试耗尽 → 降级", 默认的
    # 指数退避 (1s/2s/4s × 7 次探针) 会让这道门跑 27s。压到 1 次尝试 +
    # 10ms 退避后仍走**同一条** `_run_query_neo4j → _fallback_to_json` 路径,
    # 只是不再干等。
    return Neo4jClient(
        use_json_fallback=True,
        storage_path=path,
        retry_attempts=1,
        retry_delay_base=0.01,
        retry_max_delay=0.02,
    )


# ── 7.1/7.2 get_concept_history: 双 vault 召回 + 隔离 + 逐 alias ──────────


async def test_g41b_concept_history_recall_and_isolation(gate_client, g41a_seed):
    """A/B 两个作用域各读一次 —— 各自看全自己的族, 互相 0 条。

    seed 的每个概念 `c.id` 都等于它的名字, 而 `_CONCEPT_ID_MATCH_CYPHER` 按
    id **或** name 命中, 所以这里按名字点查 = 生产里调用方手上唯一能拿到的
    标识符形态 (生产写侧从不落 c.id)。
    """
    a_name = f"{GATE_PREFIX}_g41a_a_puny"  # A 的 punycode 子组 (现网存量同形)
    b_name = f"{GATE_PREFIX}_g41a_b_root"

    a_rows = await gate_client.get_concept_history(a_name, group_id=GID_A_LOGICAL)
    b_rows = await gate_client.get_concept_history(b_name, group_id=GID_B_LOGICAL)
    # 交叉: A 的作用域点查 B 的概念 / B 的作用域点查 A 的概念
    cross_ab = await gate_client.get_concept_history(b_name, group_id=GID_A_LOGICAL)
    cross_ba = await gate_client.get_concept_history(a_name, group_id=GID_B_LOGICAL)

    assert _names(a_rows) == {a_name}, (
        f"保召回红: A 根组作用域读不到自己 punycode 子组的概念历史 {a_rows}"
    )
    assert _names(b_rows) == {b_name}, b_rows
    assert cross_ab == [], f"零泄漏红: A 作用域读到了 B 的概念历史 {cross_ab}"
    assert cross_ba == [], f"零泄漏红: B 作用域读到了 A 的概念历史 {cross_ba}"


async def test_g41b_concept_history_is_not_reading_the_json_simulator(gate_client, g41a_seed):
    """名实一致锁: 连着 Neo4j 时必须走真 Cypher, 不得回落 JSON 模拟器。

    修复前本方法无条件调 `_handle_query_history` —— 真实部署下 `self._data`
    是空壳, 端点恒返回空 timeline。这条门直接钉住"有数据可读"这一事实:
    client 处于 Neo4j 模式且 `_data` 为空, 却仍能读到 seed 的历史。
    """
    assert gate_client.is_fallback_mode is False, "前置条件: 本门必须在 Neo4j 模式下跑"
    assert not gate_client._data.get("relationships"), (
        "前置条件: JSON 模拟器必须是空的 —— 否则读到数据也证明不了走的是 Cypher"
    )
    rows = await gate_client.get_concept_history(
        f"{GATE_PREFIX}_g41a_a_root", group_id=GID_A_LOGICAL
    )
    assert _names(rows) == {f"{GATE_PREFIX}_g41a_a_root"}, (
        f"名实一致红: Neo4j 模式下 get_concept_history 仍然没有查到图上的数据 {rows}"
    )


@pytest.mark.parametrize(
    "crossed,visible",
    [
        (f"{GATE_PREFIX}_g41a_xr", False),  # 关系在 B → r 过滤失效则现形
        (f"{GATE_PREFIX}_g41a_xc", False),  # 概念在 B → c 过滤失效则现形
        (f"{GATE_PREFIX}_g41a_ok", True),   # 全 A 正向对照 (防"写死成空"假绿)
    ],
)
async def test_g41b_concept_history_per_alias(gate_client, g41a_alias_seed, crossed, visible):
    rows = await gate_client.get_concept_history(crossed, group_id=GID_A_LOGICAL)
    assert (crossed in _names(rows)) is visible, (
        f"{crossed} 可见性应为 {visible}; 实得 {sorted(_names(rows))}"
    )


# ── 7.3/7.4 get_all_recent_episodes + 启动恢复 ───────────────────────────


async def test_g41b_all_recent_episodes_scoped(gate_client, g41a_seed):
    """全库扫 → 作用域族扫。同一个结果集精确相等 (保召回 + 零泄漏)。"""
    rows = await gate_client.get_all_recent_episodes(limit=500, group_id=GID_A_LOGICAL)
    assert _names(rows) == _A_SCOPE_EXPECTED, (
        f"缺失(保召回红): {sorted(_A_SCOPE_EXPECTED - _names(rows))}; "
        f"多出(零泄漏红): {sorted(_names(rows) - _A_SCOPE_EXPECTED)}"
    )
    rows_b = await gate_client.get_all_recent_episodes(limit=500, group_id=GID_B_LOGICAL)
    assert _names(rows_b) == {f"{GATE_PREFIX}_g41a_b_root"}, _names(rows_b)


async def test_g41b_recovery_loads_only_active_vault_family(
    gate_client, g41a_seed, monkeypatch
):
    """方案甲行为门: 启动恢复只装 **active vault 族**, 且不受请求级作用域影响。

    两半缺一不可:
      (保召回) A 的 root/canvas/semantic/punycode 子组全部进缓存 —— 现网存量
               LEARNED 就在 punycode 子组, 这半塌了等于"重启后历史全丢";
      (零泄漏) B vault 与近似前缀 vault 一条都不进。
    第三条断言钉住"进程级缓存不得被请求级 ContextVar 收窄": 把 ContextVar
    注入成板级子组后再恢复, 结果必须仍是整个 vault 族。
    """
    import app.core.subject_config as subject_config_mod
    from app.core.subject_config import _current_subject_id
    from app.services.memory_service import MemoryService

    monkeypatch.setattr(
        subject_config_mod, "default_vault_group_id", lambda: GID_A_LOGICAL
    )

    async def _recovered_names(ctx_scope=None):
        svc = MemoryService(neo4j_client=gate_client)
        token = _current_subject_id.set(ctx_scope) if ctx_scope else None
        try:
            await svc._recover_episodes_from_neo4j()
        finally:
            if token is not None:
                _current_subject_id.reset(token)
        assert svc._episodes_recovered is True
        return {
            e["concept"]
            for e in svc._episodes
            if str(e.get("concept", "")).startswith(GATE_PREFIX)
        }

    got = await _recovered_names()
    assert got == _A_SCOPE_EXPECTED, (
        f"缺失(保召回红): {sorted(_A_SCOPE_EXPECTED - got)}; "
        f"多出(零泄漏红): {sorted(got - _A_SCOPE_EXPECTED)}"
    )

    # 惰性恢复可能发生在某块白板的请求里 —— 缓存是进程级的, 作用域不得被
    # 那次请求收窄成板级, 否则其余白板的历史永远装不进来 (_episodes_recovered
    # 已置 True, 不会再恢复)。
    got_under_board_ctx = await _recovered_names(ctx_scope=f"{GID_A_LOGICAL}:board_x")
    assert got_under_board_ctx == _A_SCOPE_EXPECTED, (
        "恢复被请求级 ContextVar 收窄成板级作用域 —— 进程级缓存会永久缺其余白板: "
        f"{sorted(got_under_board_ctx)}"
    )


# ── 7.5 LEARNED 族三条读: 降级前后的**可见面**对拍 (不是完整语义等价) ──


async def test_g41b_json_mirror_visibility_equals_cypher(gate_client, g41a_seed, tmp_path):
    """LEARNED 族**三条读**降级前后的**可见面**对拍。

    同一份逻辑数据分别落 Neo4j 与 JSON, 这三条读**能看到哪些 concept** 必须相等。

    ⚠️ **本门比的是什么, 不比什么**(Codex round-4 Q5'' 整改, 防措辞过宽):
    比的是 ``_names()`` 取出的 **concept 名集合**。**不比**返回字段的完整性、
    排序、分页、日期过滤等其余语义 —— 那些各有自己的门 (门 7.6 管降级路径的
    limit / concept / startDate; 字段与排序无专门门)。所以本门证明的是
    "降级前后**看得见的东西**一样", 不是"两条路径完全等价"。

    只封 Cypher 一侧的话, "把 Neo4j 弄挂"就能把刚封的跨 vault 面整个拿回来;
    只封镜像一侧则会在降级时打断功能。两侧同批改的验收判据就是这条对拍。

    ⚠️ **覆盖面如实声明**(Codex round-1 HIGH / round-2 Q5 整改): 本门对拍的是
    ``get_all_recent_episodes`` / ``get_learning_history`` / ``get_concept_history``
    三条 —— 4 个 JSON 镜像里只覆盖到 ``_get_all_recent_episodes_json``。

    另三个镜像 (associations / canvas concepts / common concepts) **没有**真库
    对拍, 也**没有**任何门在证明它们与 Cypher 语义等价 —— 本卡不做这个宣称。
    原因有二: (i) 卡文 (d) 明令关联族"不造行为门种子"; (ii) 更根本的是
    JSON 存储里没有 Canvas/Node 实体, 镜像只能按扁平字段近似图遍历, 而全仓
    唯一的 relationships 写入点根本不写 ``canvas_path`` —— 那几个镜像在真实
    数据上恒空 (见 ``_get_canvas_concepts_json_fallback`` docstring)。
    对那一族, 本卡的保证**只有作用域收口**(单测合成 fixture 锁)。
    别把本门读成"四个镜像都验过了", 也别读成"另三个镜像语义已对齐"。
    """
    mirror = _json_client(tmp_path, _G41A_CONCEPTS)
    await mirror.initialize()
    assert mirror.is_fallback_mode is True

    for label, cypher_rows, json_rows in (
        (
            "all_recent_episodes",
            await gate_client.get_all_recent_episodes(limit=500, group_id=GID_A_LOGICAL),
            await mirror.get_all_recent_episodes(limit=500, group_id=GID_A_LOGICAL),
        ),
        (
            "learning_history",
            await gate_client.get_learning_history(
                user_id=G41A_USER, group_id=GID_A_LOGICAL, limit=500
            ),
            await mirror.get_learning_history(
                user_id=G41A_USER, group_id=GID_A_LOGICAL, limit=500
            ),
        ),
        (
            "concept_history",
            await gate_client.get_concept_history(
                f"{GATE_PREFIX}_g41a_a_puny", group_id=GID_A_LOGICAL
            ),
            await mirror.get_concept_history(
                f"{GATE_PREFIX}_g41a_a_puny", group_id=GID_A_LOGICAL
            ),
        ),
    ):
        assert _names(cypher_rows) == _names(json_rows), (
            f"{label}: 降级前后可见面不同 —— Cypher={sorted(_names(cypher_rows))} "
            f"JSON={sorted(_names(json_rows))}"
        )
    # 正向对照: 两侧都真的读到了东西 (否则"相等"可能只是双双为空的假绿)
    assert _names(await mirror.get_all_recent_episodes(limit=500, group_id=GID_A_LOGICAL)) == (
        _A_SCOPE_EXPECTED
    )
    await mirror.cleanup()


# ── 7.6/7.7 误路由旁路 ───────────────────────────────────────────────────


async def test_g41b_midflight_fallback_misroute_stays_scoped(tmp_path, monkeypatch):
    """中途降级 (Neo4j 打挂) 时, 关键词误路由不得变成整库倾倒。

    `_run_query_json_fallback` 按 `MATCH` + `LEARNED` + 无 `next_review` 把
    **三条**不同的读全部派给 `_handle_query_history`。这里让驱动在查询中途
    抛可重试异常, 走真实的 `_fallback_to_json` 路径, 断言降级后的结果仍然
    只含本作用域的数据。
    """
    from neo4j.exceptions import ServiceUnavailable

    client = _json_client(tmp_path, _G41A_CONCEPTS, name="g41b_midflight.json")
    await client.initialize()
    # 伪装成 Neo4j 模式, 让 run_query 走 _run_query_neo4j → 失败 → 降级
    client._use_json_fallback = False

    class _BoomDriver:
        def session(self, **_kw):
            raise ServiceUnavailable("gate-injected: neo4j went away mid-flight")

        async def close(self):
            return None

    def _rearm():
        """每次探针前重新武装"中途降级"。

        ⚠️ 变异负控实测抓到的坑 (2026-08-31): `_fallback_to_json()` 会把
        `_use_json_fallback` 置 True **并关掉 driver**。所以第一次探针之后,
        后续调用走的是各方法自己的 `if self._use_json_fallback:` 分支
        (`_get_learning_history_json` —— 它本来就实现了 date/concept 过滤),
        **不再经过关键词误路由**。不重新武装, 门名叫 misroute、测的却是另一
        条路径: 把 `_handle_query_history` 的 date/concept 过滤整个删掉,
        本门仍然全绿。
        """
        client._use_json_fallback = False
        client._driver = _BoomDriver()

    _rearm()

    # 三条形状**逐个**验 (Codex round-1 HIGH 整改: 初版只跑了 episodes 一条)
    rows = await client.get_all_recent_episodes(limit=500, group_id=GID_A_LOGICAL)
    assert client.is_fallback_mode is True, "前置条件: 本门必须真的走了中途降级"
    assert _names(rows) == _A_SCOPE_EXPECTED, (
        "误路由旁路: 中途降级后 get_all_recent_episodes 的结果越出了作用域 —— "
        f"多出 {sorted(_names(rows) - _A_SCOPE_EXPECTED)}"
    )

    _rearm()
    hist = await client.get_learning_history(
        user_id=G41A_USER, group_id=GID_A_LOGICAL, limit=500
    )
    assert _names(hist) == _A_SCOPE_EXPECTED, (
        "误路由旁路: get_learning_history 中途降级后越出作用域 —— "
        f"多出 {sorted(_names(hist) - _A_SCOPE_EXPECTED)}"
    )

    _rearm()
    one = await client.get_concept_history(
        f"{GATE_PREFIX}_g41a_a_puny", group_id=GID_A_LOGICAL
    )
    assert _names(one) == {f"{GATE_PREFIX}_g41a_a_puny"}, one
    _rearm()
    cross = await client.get_concept_history(
        f"{GATE_PREFIX}_g41a_b_root", group_id=GID_A_LOGICAL
    )
    assert cross == [], f"误路由旁路: A 作用域降级后读到了 B 的概念历史 {cross}"

    # limit 不得在降级路径上丢失。
    # ⚠️ Codex round-2 Q5 整改: 断言必须挂在**没有外层切片**的入口上。
    # `get_all_recent_episodes` 自己在 run_query 之后又切了一刀, 所以拿它测
    # 根本抓不到 `_handle_query_history` 丢 limit —— 那才是降级时真正在跑的
    # 代码。`get_learning_history` 没有外层切片, 它才是有效探针。
    _rearm()
    capped_hist = await client.get_learning_history(
        user_id=G41A_USER, group_id=GID_A_LOGICAL, limit=2
    )
    assert len(capped_hist) == 2, (
        f"降级路径丢了 limit: 要 2 条, 实得 {len(capped_hist)} 条 —— "
        "handler 忽略了 params['limit'] (外层无切片, 这里是唯一能抓到它的地方)"
    )
    _rearm()
    capped_ep = await client.get_all_recent_episodes(limit=2, group_id=GID_A_LOGICAL)
    assert len(capped_ep) == 2, f"episodes 外层切片也失效: {len(capped_ep)}"

    # date / concept 过滤同样不得在降级路径上被静默丢弃 (Codex round-2 Q3)
    _rearm()
    named = await client.get_learning_history(
        user_id=G41A_USER, group_id=GID_A_LOGICAL, limit=500, concept="a_puny"
    )
    assert _names(named) == {f"{GATE_PREFIX}_g41a_a_puny"}, (
        f"降级路径丢了 concept 过滤: {sorted(_names(named))}"
    )
    from datetime import datetime as _dt

    _rearm()
    future = await client.get_learning_history(
        user_id=G41A_USER,
        group_id=GID_A_LOGICAL,
        limit=500,
        start_date=_dt(2099, 1, 1),
    )
    assert future == [], f"降级路径丢了 startDate 过滤: {len(future)} 条"
    await client.cleanup()


G41B_IDNAME_USER = f"{GATE_PREFIX}_g41b_idname_user"
#: 生产形态: create_learning_relationship 的 MERGE 身份是 {name, group_id},
#: **从不落 c.id** —— 所以这个概念节点没有 id 属性。
G41B_NAME_ONLY = f"{GATE_PREFIX}_g41b_name_only"
#: 对照形态: id 与 name **不同**, 用来单独证明 id 分支自己也生效。
#: (若 seed 把 id 设成与 name 相同, `OR` 改成 `AND` 也照样命中 —— 门就死了)
G41B_ID_DIFFERS = f"{GATE_PREFIX}_g41b_id_differs"
G41B_DISTINCT_ID = f"{G41B_ID_DIFFERS}--distinct-id"


@pytest.fixture
async def g41b_idname_seed(gate_client):
    """概念点查的两种标识符形态。

    Codex round-1 HIGH 整改: `g41a_seed` 把 `c.id` 设成与 `c.name` 相同, 于是
    把 `_CONCEPT_ID_MATCH_CYPHER` 的 `OR` 改成 `AND` 时所有门仍然全绿 ——
    而生产数据里 `c.id` 是 **null**, `AND` 会让端点重新恒空。本 fixture 造出
    两者可分辨的数据, 让那条变异能被杀。
    """
    await gate_client.run_query("MERGE (u:User {id: $uid})", uid=G41B_IDNAME_USER)
    await gate_client.run_query(
        """
        MERGE (c:Concept {name: $name, group_id: $gid})
        SET c.probe = $probe
        WITH c
        MATCH (u:User {id: $uid})
        MERGE (u)-[r:LEARNED {group_id: $gid}]->(c)
        SET r.score = 5, r.timestamp = $ts
        """,
        name=G41B_NAME_ONLY, gid=GID_A_PUNY, uid=G41B_IDNAME_USER,
        probe=GATE_PREFIX, ts="2026-08-31T00:00:00",
    )
    await gate_client.run_query(
        """
        MERGE (c:Concept {name: $name, group_id: $gid})
        SET c.probe = $probe, c.id = $cid
        WITH c
        MATCH (u:User {id: $uid})
        MERGE (u)-[r:LEARNED {group_id: $gid}]->(c)
        SET r.score = 6, r.timestamp = $ts
        """,
        name=G41B_ID_DIFFERS, gid=GID_A_PUNY, cid=G41B_DISTINCT_ID,
        uid=G41B_IDNAME_USER, probe=GATE_PREFIX, ts="2026-08-31T00:00:01",
    )
    # 自证: 生产形态那条**确实**没有 id 属性 (否则下面测的不是生产形态)
    probe = await gate_client.run_query(
        "MATCH (c:Concept {name: $name}) RETURN c.id AS cid", name=G41B_NAME_ONLY
    )
    assert probe and probe[0]["cid"] is None, f"seed 形态不对, c.id 应为 null: {probe}"
    return True


async def test_g41b_concept_history_matches_production_shape_without_c_id(
    gate_client, g41b_idname_seed
):
    """生产形态 (Concept 无 `c.id`) 必须能按**名字**查到历史。

    这条是"名实一致修复"的真正判据: 只按 `c.id` 点查, 换了真 Cypher 之后端点
    **仍然**恒空 —— 因为生产写侧从不落 id。把匹配片段的 `OR` 改成 `AND`,
    本条立即红。
    """
    rows = await gate_client.get_concept_history(
        G41B_NAME_ONLY, group_id=GID_A_LOGICAL
    )
    assert _names(rows) == {G41B_NAME_ONLY}, (
        f"按名字点查生产形态的概念读不到历史 (c.id 为 null): {rows}"
    )


async def test_g41b_concept_history_matches_by_distinct_id(
    gate_client, g41b_idname_seed
):
    """id 与 name **不同**时, 按 id 也必须能查到 —— 证明 id 分支不是摆设。

    与上一条合起来才构成 `OR` 的完整判据: 一条只有 name 能命中, 一条只有 id
    能命中 (按名字查这条会命中它自己, 所以这里断言的是 id 那一半)。
    """
    rows = await gate_client.get_concept_history(
        G41B_DISTINCT_ID, group_id=GID_A_LOGICAL
    )
    assert _names(rows) == {G41B_ID_DIFFERS}, (
        f"按 c.id 点查 (id != name) 读不到历史: {rows}"
    )


async def test_g41b_handle_query_history_fail_closed_without_scope(tmp_path, caplog):
    """`_handle_query_history` 无 scope → 拒绝全库扫 (对齐 `_handle_query_reviews`)。

    正向对照同时断言: 带 scope 时它**读得到**数据 —— 否则"无 scope 返回空"
    可能只是这个 handler 本来就读不出东西的假绿。
    """
    import logging

    client = _json_client(tmp_path, _G41A_CONCEPTS, name="g41b_failclosed.json")
    await client.initialize()

    with caplog.at_level(logging.ERROR):
        refused = await client._handle_query_history({"userId": G41A_USER})
    assert refused == [], f"无 scope 时仍返回了 {len(refused)} 条跨 vault 记录"
    assert any("G4-1b" in r.message for r in caplog.records), (
        "fail-closed 必须留下 ERROR 级痕迹, 否则是静默断读"
    )

    allowed = await client._handle_query_history(
        {"userId": G41A_USER, "group_id": GID_A}
    )
    assert _names(allowed) == _A_SCOPE_EXPECTED, (
        f"正向对照红: 带 scope 也读不到数据, 上面的空结果不能证明是 fail-closed {allowed}"
    )
    await client.cleanup()
