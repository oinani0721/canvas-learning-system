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
3. Concept/LEARNED 写身份现状门 — **xfail(strict=True)**: 复现
   neo4j_client.create_learning_relationship 的 W1 违规 (MERGE Concept
   仅按 name, 跨 vault 同名冲撞 + group_id last-write-wins)。
   ⛔ 交接 G2-3: 写路径修复为复合键后, 这两条会 XPASS(strict) 报错,
   届时移除 xfail 标记翻绿 — 这是有意设计的交接信号, 不是测试损坏。

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
# 门 3 — Concept/LEARNED 写身份现状 (xfail strict, 交接 G2-3 翻绿)
# ---------------------------------------------------------------------------

_W1_XFAIL_REASON = (
    "现状违规 W1 (审计 §5 #1): create_learning_relationship 的 MERGE "
    "(c:Concept {name}) 缺 group_id 复合键, 跨 vault 同名概念冲撞 + "
    "group_id last-write-wins。G2-3 修复写路径后本测试 XPASS(strict) "
    "报错, 届时移除 xfail 标记翻绿。raises=AssertionError 收窄 (Codex "
    "round-1 MEDIUM 整改): 连接异常/写入失败等错误原因不计 XFAIL, "
    "只有身份断言本身失败才算预期失败。"
)


def _require_write_ok(**results: bool) -> None:
    """前置条件守卫: 写路径调用失败走 pytest.fail (Failed, 非 AssertionError).

    配合 xfail(raises=AssertionError): 环境/写入故障会让测试真失败,
    而不是被误收进 XFAIL — 保证 xfail 只因 W1 身份断言而挂。
    """
    failed = [name for name, ok in results.items() if not ok]
    if failed:
        pytest.fail(f"precondition: create_learning_relationship 返回 False: {failed}")


@pytest.mark.xfail(strict=True, raises=AssertionError, reason=_W1_XFAIL_REASON)
async def test_concept_write_identity_dual_vault_current_state(gate_client):
    """期望行为: 两 vault 各自持有同名 Concept 节点 (W1 复合键语义).

    走真实业务写路径 create_learning_relationship (不 mock、不改业务
    代码), 断言**正确**行为 — 当前实现 MERGE 仅按 name, 第二个 vault
    的写入会劫持第一个 vault 的节点, 断言失败 → xfailed。
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
    # 正确的 W1 语义: 两个物理节点, 各归其 vault。
    # 现状: 单节点, group_id 被 B 的写入 clobber → 此断言失败 (xfail)。
    assert gids == [GID_A, GID_B], f"W1 write identity clobbered: {gids}"


@pytest.mark.xfail(strict=True, raises=AssertionError, reason=_W1_XFAIL_REASON)
async def test_learned_edge_write_identity_dual_vault_current_state(gate_client):
    """期望行为: 同一 user 在两 vault 各有一条 LEARNED 边, r.group_id 各归其组.

    现状: 因 Concept 节点被合并成一个, MERGE (u)-[r:LEARNED]->(c) 也
    合并成单条边, r.group_id/r.score 被后写 vault 覆盖 → xfailed。
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
