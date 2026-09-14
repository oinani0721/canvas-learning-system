"""CARD-G6-10 — 双 vault Neo4j 维隔离真库门（A 组的复习写对 B 组的复习读零影响）。

> 批次: BATCH-2026-09-11-第十四批 / CARD-G6-10
> 姊妹件: ``backend/scripts/g610_dual_vault_interaction_canary.py``（state 文件维）
> 结构模板: ``backend/tests/integration/test_cypher_contract_gate.py``（逐条照抄）
> 契约: ``.claude/rules/cypher-read-contract.md`` R1/R4 · ``cypher-write-contract.md`` W1

本卡的主张是「跨 vault 复习进度各算各的、切换不串台」。它有两条腿：

  · state 文件维（snooze / done 的看板账）—— 姊妹 canary 跑，无需容器；
  · **Neo4j 维（复习本身的账：LEARNED 边 + scoring Episode）—— 本文件跑 7692 容器**。

⛔ 只跑容器（7692），**永不碰现网 7691**：``_test_neo4j_reachable()`` 在 URI 含
``:7691`` 时直接返回 False（整文件 skip），另有 :func:`test_g610_never_targets_live_7691`
把这条从注释升级成可执行断言。

同名攻击用例集（总账 :983）
---------------------------
两个 group 用**完全相同**的资产标识（同 concept 名 / 同 node ID / 同 canvas path /
同 user ID）—— 名字不同的话，「A 的写没出现在 B 的读里」会因为"名字本来就不一样"
而恒真，门变成一场自证。

⚠ 形状复用 G2-9，字面量**不**从 ``g29_dual_vault_canary`` import，理由如实写在这里：
7692 是共享容器，G2-9 的清理语句按 ``g29`` 前缀 ``DETACH DELETE``。若本门直接用它那组
字面量，两边并发跑时会互删对方的种子，红/绿都不可信。所以本门用自己的 ``g610gate``
命名空间承载**同一个形状**。这一条与总账 :983「强制复用 G2-9 同名攻击用例集」的读法
差异已登记进验收单 §四，请主 session 裁。

先红后绿：一条正例 + 两条负控，共用同一个断言
--------------------------------------------
三条测试调用的是**同一个** :func:`_assert_group_b_intact`。这是刻意的：负控红在哪条
断言上必须可证，而不是"某处失败了"。所以负控用
``pytest.raises(AssertionError, match=_BREACH_MARKER)`` 捕获，既证明它红了，也证明
红的是隔离断言本身，不是 import / fixture / 连接错误。

  · 正例 :func:`test_group_b_unaffected_by_group_a_review_write`
        A 组做一次复习等价写（``create_learning_relationship`` + ``record_score_history``）
        ⇒ B 组的 group-scoped 读**按 concept 名 / node 名逐个**不变。
        ⛔ 不用「数量不减」这类计数判据 —— 幂等 MERGE 会让计数恒等而内容已被覆盖。
  · 负控 ① :func:`test_negctl_write_side_mislabeled_group_breaches_isolation`
        把本该属于 A 的那次写**误标成 B 的 group 身份键**（W1 把 group_id 放进 MERGE
        身份键，写侧没有可"去掉"的过滤，所以串台只能从身份键这一侧制造）⇒ B 的读
        必然看见它 ⇒ 同一条断言必红。
  · 负控 ② :func:`test_negctl_read_side_without_group_filter_breaches_isolation`
        B 的读**去掉 group 过滤**（R1 违规形态）⇒ 看见 A 的写 ⇒ 同一条断言必红。

两条负控各用自己的 group 命名空间（``g610gate_neg_*``），与正例的 ``g610gate_[ab]``
物理异组，于是 pytest 跑序怎么变都不互相污染。

容器不可达 / 降级 JSON 时整文件 skip —— **skip 不是 pass**：那种情形下本维记为
「本卡未证明」，state 文件维的先红后绿仍独立成立。

跑法（⛔ 文件级单跑，禁 ``tests/integration`` 目录级 —— 协议 §3：该目录走 advisory
会真连现网）::

    cd backend && NEO4J_TEST_URI=bolt://127.0.0.1:7692 \\
        .venv/bin/pytest -q -p no:cacheprovider \\
        tests/integration/test_g610_dual_vault_isolation.py
"""

from __future__ import annotations

import os
from typing import Any

import pytest

from app.graphiti.group_id_compat import to_physical_group_id

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

GATE_PREFIX = "g610gate"

#: 正例用的两个 vault 组
GID_A_LOGICAL = f"vault:{GATE_PREFIX}_a"
GID_B_LOGICAL = f"vault:{GATE_PREFIX}_b"
GID_A = to_physical_group_id(GID_A_LOGICAL)  # vault__g610gate_a
GID_B = to_physical_group_id(GID_B_LOGICAL)  # vault__g610gate_b

#: 负控专用的两个 vault 组（与正例物理异组 ⇒ 跑序无关）
GID_NEG_A_LOGICAL = f"vault:{GATE_PREFIX}_neg_a"
GID_NEG_B_LOGICAL = f"vault:{GATE_PREFIX}_neg_b"
GID_NEG_A = to_physical_group_id(GID_NEG_A_LOGICAL)
GID_NEG_B = to_physical_group_id(GID_NEG_B_LOGICAL)

#: 两组共用的同名资产（G2-9 攻击形状，见模块 docstring 的命名空间说明）
SHARED_CONCEPT = f"{GATE_PREFIX}_同名概念"
SHARED_NODE_ID = f"{GATE_PREFIX}-node-0001"
SHARED_CANVAS_PATH = f"{GATE_PREFIX}/同名白板.canvas"
SHARED_USER_ID = f"{GATE_PREFIX}-user"

#: seed 分数与「复习」分数刻意不同 —— 相同的话，串台写覆盖了 B 的值也看不出来。
SEED_SCORE = 40
REVIEW_SCORE = 95

#: 隔离断言失败正文里的稳定锚。负控用它 match，证明红的是**这条**断言。
_BREACH_MARKER = "G610-ISOLATION-BREACH"

_CLEANUP_QUERIES = (
    f"MATCH (n) WHERE n.group_id STARTS WITH 'vault__{GATE_PREFIX}' DETACH DELETE n",
    f"MATCH (c:Concept) WHERE c.name STARTS WITH '{GATE_PREFIX}' DETACH DELETE c",
    f"MATCH (u:User) WHERE u.id STARTS WITH '{GATE_PREFIX}' DETACH DELETE u",
    # 与模板同因: 写身份回归会产出**无 group_id**、只有前缀 path/id 的 Canvas/Node,
    # 不清理会永久滞留共享 7692 容器, 让回归修好后重跑仍假红。
    f"MATCH (c:Canvas) WHERE c.path STARTS WITH '{GATE_PREFIX}' DETACH DELETE c",
    f"MATCH (n:Node) WHERE n.id STARTS WITH '{GATE_PREFIX}' DETACH DELETE n",
    f"MATCH (e:Episode)-[:SCORED]->(n:Node) WHERE n.id STARTS WITH '{GATE_PREFIX}' DETACH DELETE e",
)


@pytest.fixture
async def gate_client(tmp_path):
    """真实 Neo4jClient 指向测试容器 — 走真实业务写路径，不 mock、不改业务代码。

    storage_path 指向 tmp_path: 万一触发 JSON fallback 也不污染
    backend/data/neo4j_memory.json（防御性，探针通过时不应触发）。
    """
    from app.clients.neo4j_client import Neo4jClient

    client = Neo4jClient(
        uri=NEO4J_TEST_URI,
        user=NEO4J_TEST_USER,
        password=NEO4J_TEST_PASSWORD,
        use_json_fallback=False,
        storage_path=tmp_path / "g610_gate_fallback.json",
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


# ---------------------------------------------------------------------------
# 取样与断言 — 正例与两条负控**共用**，负控红在这里才算数
# ---------------------------------------------------------------------------


async def _seed_pair(client, gid_a_logical: str, gid_b_logical: str) -> None:
    """两个组各写一份**同名**资产（同 concept / 同 node / 同 canvas / 同 user）。"""
    for gid in (gid_a_logical, gid_b_logical):
        ok = await client.create_learning_relationship(
            user_id=SHARED_USER_ID,
            concept=SHARED_CONCEPT,
            score=SEED_SCORE,
            group_id=gid,
        )
        if not ok:
            pytest.fail(f"precondition: create_learning_relationship 返回 False (group={gid})")
        ok = await client.record_score_history(
            concept_id=SHARED_NODE_ID,
            canvas_name=SHARED_CANVAS_PATH,
            score=SEED_SCORE,
            group_id=gid,
        )
        if not ok:
            pytest.fail(f"precondition: record_score_history 返回 False (group={gid})")


async def _review_write(client, gid_logical: str) -> None:
    """一次「复习」等价写：LEARNED 分数 + 一条 scoring Episode。

    负控 ① 把 ``gid_logical`` 传成 B 的 group 身份键，其余逐字不变 —— 单变量。
    """
    ok = await client.create_learning_relationship(
        user_id=SHARED_USER_ID,
        concept=SHARED_CONCEPT,
        score=REVIEW_SCORE,
        group_id=gid_logical,
    )
    if not ok:
        pytest.fail(f"precondition: 复习写 create_learning_relationship 返回 False (group={gid_logical})")
    ok = await client.record_score_history(
        concept_id=SHARED_NODE_ID,
        canvas_name=SHARED_CANVAS_PATH,
        score=REVIEW_SCORE,
        group_id=gid_logical,
    )
    if not ok:
        pytest.fail(f"precondition: 复习写 record_score_history 返回 False (group={gid_logical})")


async def _snapshot_group(
    client, gid_logical: str, gid_physical: str, *, group_filtered: bool = True
) -> dict[str, Any]:
    """按 **concept 名 / node 名**取样一个组的复习读面。

    三条读各自是生产读路径:
      · ``get_learning_history``       —— LEARNED 边（复习分数账）
      · ``get_concept_score_history``  —— scoring Episode（历史分数）
      · Concept 节点直读              —— 负控 ② 在这里把 group 过滤去掉

    返回的是**按名字索引的字典**而不是计数: 计数判据挡不住等长替换（幂等 MERGE 把
    B 的 40 分覆盖成 95 分时，行数一个都不会少）。
    """
    history = await client.get_learning_history(user_id=SHARED_USER_ID, group_id=gid_logical)
    scores = await client.get_concept_score_history(
        concept_id=SHARED_NODE_ID,
        canvas_name=SHARED_CANVAS_PATH,
        group_id=gid_logical,
    )
    if group_filtered:
        concept_rows = await client.run_query(
            "MATCH (c:Concept) WHERE c.group_id = $gid AND c.name STARTS WITH $prefix "
            "RETURN c.name AS name, c.group_id AS gid ORDER BY name, gid",
            gid=gid_physical,
            prefix=GATE_PREFIX,
        )
    else:
        # 负控 ②: R1 违规形态 —— 去掉 group 过滤的裸读
        concept_rows = await client.run_query(
            "MATCH (c:Concept) WHERE c.name STARTS WITH $prefix RETURN c.name AS name, c.group_id AS gid ORDER BY name, gid",
            prefix=GATE_PREFIX,
        )
    return {
        "learned": {r["concept"]: (r.get("score"), r.get("timestamp")) for r in history},
        "episodes": [(r.get("score"), str(r.get("timestamp"))) for r in scores],
        "concepts": sorted((r["name"], r["gid"]) for r in concept_rows),
    }


def _assert_group_b_intact(before: dict[str, Any], after: dict[str, Any], *, where: str) -> None:
    """B 组的复习读面逐条不变 —— 正例与两条负控**共用**的那一条断言。

    逐个名字比对（不是计数）: 先比键集合，再比每个键的值。键集合相同而值变了，正是
    「同名概念被对方的写覆盖」的形态，计数判据对它完全失明。
    """
    b_names = set(before["learned"])
    a_names = set(after["learned"])
    assert a_names == b_names, f"{_BREACH_MARKER} [{where}] B 组 LEARNED 概念名集合变了: {b_names} → {a_names}"
    for name in sorted(b_names):
        assert after["learned"][name] == before["learned"][name], (
            f"{_BREACH_MARKER} [{where}] B 组概念 {name!r} 的复习账被改动: "
            f"{before['learned'][name]} → {after['learned'][name]}"
        )
    assert after["episodes"] == before["episodes"], (
        f"{_BREACH_MARKER} [{where}] B 组 node {SHARED_NODE_ID!r} 的历史分数被改动: "
        f"{before['episodes']} → {after['episodes']}"
    )
    assert after["concepts"] == before["concepts"], (
        f"{_BREACH_MARKER} [{where}] B 组可见的 Concept 名单变了: {before['concepts']} → {after['concepts']}"
    )


# ---------------------------------------------------------------------------
# 门 0 — 环境自证: 本文件永不指向现网
# ---------------------------------------------------------------------------


def test_g610_never_targets_live_7691():
    """探针已拒 7691; 此断言把"禁碰 live"从注释升级为可执行契约."""
    assert ":7691" not in NEO4J_TEST_URI


# ---------------------------------------------------------------------------
# 门 1 — 正例: A 组的复习写，B 组逐个名字不变
# ---------------------------------------------------------------------------


async def test_group_b_unaffected_by_group_a_review_write(gate_client):
    """A 组复习一次，B 组的 LEARNED / Episode / Concept 名单逐条不变。

    正向对照同在本测试内: A 组自己的读**必须**看到新分数。少了它，「B 没变」可以是
    因为那次复习写根本没落库 —— 那是假绿，不是隔离。
    """
    await _seed_pair(gate_client, GID_A_LOGICAL, GID_B_LOGICAL)
    before = await _snapshot_group(gate_client, GID_B_LOGICAL, GID_B)

    await _review_write(gate_client, GID_A_LOGICAL)

    # 正向对照: A 确有本次复习写
    a_after = await _snapshot_group(gate_client, GID_A_LOGICAL, GID_A)
    assert a_after["learned"][SHARED_CONCEPT][0] == REVIEW_SCORE, (
        f"precondition: A 组自己没看到复习分数 {REVIEW_SCORE}（拿到 {a_after['learned'].get(SHARED_CONCEPT)}）"
        " —— 写没落库，本测试的『B 没变』不构成隔离证据"
    )
    assert REVIEW_SCORE in [s for s, _ in a_after["episodes"]], (
        f"precondition: A 组的历史分数里没有本次复习的 {REVIEW_SCORE}（拿到 {a_after['episodes']}）"
    )

    after = await _snapshot_group(gate_client, GID_B_LOGICAL, GID_B)
    _assert_group_b_intact(before, after, where="positive")


# ---------------------------------------------------------------------------
# 门 2 — 负控 ①: 写侧误标 group 身份键 ⇒ 同一条断言必红
# ---------------------------------------------------------------------------


async def test_negctl_write_side_mislabeled_group_breaches_isolation(gate_client):
    """本该写进 A 的那次复习，group 身份键误标成 B ⇒ B 的读看见它 ⇒ 隔离断言必红。

    为什么负控从写侧身份键制造: 按 W1，业务写把 group_id 放进 MERGE 身份键
    （``MERGE (c:Concept {name, group_id})``），写侧**没有**可"去掉"的 group 过滤。
    误标身份键就是这条路径上唯一真实的串台形态。

    与正例的单变量差: 只有 ``_review_write`` 的 group 实参从 A 换成 B，seed、资产、
    取样函数、断言函数全部逐字相同。
    """
    await _seed_pair(gate_client, GID_NEG_A_LOGICAL, GID_NEG_B_LOGICAL)
    before = await _snapshot_group(gate_client, GID_NEG_B_LOGICAL, GID_NEG_B)

    # ⬇ 唯一的变量：本该是 GID_NEG_A_LOGICAL
    await _review_write(gate_client, GID_NEG_B_LOGICAL)

    after = await _snapshot_group(gate_client, GID_NEG_B_LOGICAL, GID_NEG_B)
    with pytest.raises(AssertionError, match=_BREACH_MARKER):
        _assert_group_b_intact(before, after, where="negctl-write-side")


# ---------------------------------------------------------------------------
# 门 3 — 负控 ②: 读侧去掉 group 过滤 ⇒ 同一条断言必红
# ---------------------------------------------------------------------------


async def test_negctl_read_side_without_group_filter_breaches_isolation(gate_client):
    """B 的读去掉 group 过滤（R1 违规形态）⇒ 看见 A 组的写 ⇒ 隔离断言必红。

    与正例的单变量差: 只有 ``_snapshot_group`` 的 ``group_filtered`` 从 True 换成
    False。A 的那次复习写本身完全正确（落的是 A 的身份键）—— 串台纯粹由"读的时候
    没带 scope"造成，这正是读契约 R1 要拦的那件事。

    A 组的复习写会新建一个 A 独有的概念（``…_only_a``），于是"名单变了"在去过滤的
    读里必然发生；带过滤的读则看不到它（门 1 已证）。
    """
    await _seed_pair(gate_client, GID_NEG_A_LOGICAL, GID_NEG_B_LOGICAL)
    before = await _snapshot_group(gate_client, GID_NEG_B_LOGICAL, GID_NEG_B, group_filtered=False)

    ok = await gate_client.create_learning_relationship(
        user_id=SHARED_USER_ID,
        concept=f"{GATE_PREFIX}_only_a",
        score=REVIEW_SCORE,
        group_id=GID_NEG_A_LOGICAL,
    )
    if not ok:
        pytest.fail("precondition: A 组独有概念写入返回 False")

    after = await _snapshot_group(gate_client, GID_NEG_B_LOGICAL, GID_NEG_B, group_filtered=False)
    with pytest.raises(AssertionError, match=_BREACH_MARKER):
        _assert_group_b_intact(before, after, where="negctl-read-side")

    # 对照: 同一次写，带 group 过滤的读**看不见** —— 证明红是"去过滤"造成的，
    # 不是那次写本身越界。
    filtered = await _snapshot_group(gate_client, GID_NEG_B_LOGICAL, GID_NEG_B)
    assert all(name != f"{GATE_PREFIX}_only_a" for name, _ in filtered["concepts"]), (
        f"A 组独有概念出现在 B 的 group-scoped 读里: {filtered['concepts']}"
    )
