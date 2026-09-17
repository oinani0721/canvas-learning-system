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


#: 现网端口。7691 = 现网 Neo4j 的宿主映射端口；7687 = Neo4j 默认端口（容器内/直连现网）。
_LIVE_PORTS = frozenset({7691, 7687})

#: **正面白名单**：本文件只允许打 7692 测试容器。与
#: ``tests/support/live_port_guard.ALLOWED_TEST_PORTS`` 同值同语义。
#: ⚠ Codex r4 M2: 只列黑名单（拒 7691/7687）与文件开头「只跑容器（7692）」的声明
#: 不一致 —— `bolt://127.0.0.1:7693` 会被放行。判据必须恰好等于它的主张，所以改成
#: 白名单：不是 7692 就不跑。黑名单保留，让「指到现网」这一类有专属的拒绝理由。
_ALLOWED_TEST_PORTS = frozenset({7692})


def _parse_port(uri: str) -> int | None:
    """解析 URI 端口；畸形或缺省一律返回 None（= 不可判定 = 不安全）。

    ⚠ Codex r3 M2: 不能用 `":7691" in uri` 这种子串判据 ——
    `bolt://127.0.0.1:07691` 连的就是 7691，子串检查却放行。
    """
    from urllib.parse import urlsplit

    try:
        return urlsplit(uri).port
    except ValueError:  # 端口非法/越界
        return None


def _targets_live_port(uri: str) -> bool:
    """URI 是否指向现网端口（按解析出的端口判，子串作为额外一层）。"""
    if any(f":{p}" in uri for p in _LIVE_PORTS):
        return True
    port = _parse_port(uri)
    if port is None:  # 缺省端口 = 驱动取 7687 = 现网默认；或畸形 URI
        return True
    return port in _LIVE_PORTS


def _targets_allowed_test_port(uri: str) -> bool:
    """URI 是否指向本文件允许的测试端口（白名单，当前只有 7692）。"""
    if _targets_live_port(uri):
        return False
    return _parse_port(uri) in _ALLOWED_TEST_PORTS


def _test_neo4j_reachable() -> bool:
    if not _targets_allowed_test_port(NEO4J_TEST_URI):
        # 禁碰 live，且非白名单端口一律不跑（不是 7692 就不是本文件该打的库）
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

#: ⚠ Codex r1 MEDIUM-6: **Episode 必须删在 Node 之前**。原版把
#: `MATCH (e:Episode)-[:SCORED]->(n:Node) …` 放在 `DETACH DELETE n` 之后，而
#: `DETACH DELETE` 连边一起删 —— 等轮到 Episode 那条时，用来定位它的 SCORED 边已经
#: 没了，声称要清的「无 group 的 scoring Episode」一条也定位不到，清理语句形同虚设。
#: 收尾再补一条模板 `:109` 的孤儿扫（没有任何边、type=scoring、无 group 的残渣）。
_CLEANUP_QUERIES = (
    # ① 先按 SCORED 边定位 Episode（此时 Node 还在，边还在）
    f"MATCH (e:Episode)-[:SCORED]->(n:Node) WHERE n.id STARTS WITH '{GATE_PREFIX}' DETACH DELETE e",
    # ② 再删节点族
    f"MATCH (n) WHERE n.group_id STARTS WITH 'vault__{GATE_PREFIX}' DETACH DELETE n",
    f"MATCH (c:Concept) WHERE c.name STARTS WITH '{GATE_PREFIX}' DETACH DELETE c",
    f"MATCH (u:User) WHERE u.id STARTS WITH '{GATE_PREFIX}' DETACH DELETE u",
    # 与模板同因: 写身份回归会产出**无 group_id**、只有前缀 path/id 的 Canvas/Node,
    # 不清理会永久滞留共享 7692 容器, 让回归修好后重跑仍假红。
    f"MATCH (c:Canvas) WHERE c.path STARTS WITH '{GATE_PREFIX}' DETACH DELETE c",
    f"MATCH (n:Node) WHERE n.id STARTS WITH '{GATE_PREFIX}' DETACH DELETE n",
    # ⛔ 这里**刻意没有**模板 `:109` 那条孤儿扫
    #    `MATCH (e:Episode) WHERE e.type='scoring' AND e.group_id IS NULL AND NOT (e)--() …`
    #    （Codex r2 MEDIUM-3）: 它没有任何 g610gate 范围条件，在**共享的** 7692 容器里会
    #    连别的卡/别的任务留下的无 group、无边 scoring Episode 一起删掉 —— 判据的作用面
    #    大于它的主张，那是越界清理，不是清理不彻底。
    #    本门不需要它: ① 已在 Node 还在、SCORED 边还在时按边删过 Episode；② 带 group 的
    #    由 `group_id STARTS WITH 'vault__g610gate'` 覆盖。
    #    未覆盖的只剩「无 group **且** 边已先消失」这一种，本门自己的写路径产不出来
    #    （record_score_history 恒 CREATE 边、恒带 group）—— 如实登记，不拿越界语句去盖。
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


async def _snapshot_raw(client, gid_physical: str, *, group_filtered: bool) -> dict[str, Any]:
    """按 concept 名 / node 名取样复习读面 —— **三条 facet 都是手写 Cypher**。

    ⚠ Codex r1 HIGH-2 的收口。原版这个函数在 ``group_filtered=False`` 时只把**手写的
    Concept 查询**去掉过滤，另外两条仍走生产方法（生产方法按 R4 恒带 scope，去不掉），
    于是负控 ② 实际改了两个变量：过滤 + 换了写入内容。现在三条 facet 全部手写、
    ``group_filtered`` 是它们**唯一**的差别 —— 负控 ② 才真是单变量。

    生产读路径的隔离另由 :func:`_snapshot_production` 在正例里单独证（那才是用户真正
    走的那条路；手写查询只用来表达「读侧带不带 scope」这一个对照维度）。

    ⚠ Codex r1 MEDIUM-4: LEARNED 的键是 **(concept 名, concept 的 group, 边的 group)**
    三元组，不是概念名。按名字做键会把「A 的同名行泄漏进 B 的结果」和「B 自己那行」
    压成同一个键，泄漏行被静默吃掉 —— 判据要测身份，不是测名字。
    """
    scope_learned = "AND r.group_id = $gid AND c.group_id = $gid" if group_filtered else ""
    learned_rows = await client.run_query(
        f"""
        MATCH (u:User {{id: $uid}})-[r:LEARNED]->(c:Concept)
        WHERE c.name STARTS WITH $prefix {scope_learned}
        RETURN c.name AS name, c.group_id AS cgid, r.group_id AS rgid, r.score AS score
        ORDER BY name, cgid, rgid, score
        """,
        uid=SHARED_USER_ID,
        prefix=GATE_PREFIX,
        gid=gid_physical,
    )
    scope_ep = "AND n.group_id = $gid AND r.group_id = $gid AND e.group_id = $gid" if group_filtered else ""
    episode_rows = await client.run_query(
        f"""
        MATCH (n:Node)<-[r:SCORED]-(e:Episode)
        WHERE n.id STARTS WITH $prefix {scope_ep}
        RETURN n.id AS nid, n.group_id AS ngid, r.group_id AS rgid, r.score AS score
        ORDER BY nid, ngid, rgid, score
        """,
        prefix=GATE_PREFIX,
        gid=gid_physical,
    )
    scope_concept = "AND c.group_id = $gid" if group_filtered else ""
    concept_rows = await client.run_query(
        f"""
        MATCH (c:Concept) WHERE c.name STARTS WITH $prefix {scope_concept}
        RETURN c.name AS name, c.group_id AS gid ORDER BY name, gid
        """,
        prefix=GATE_PREFIX,
        gid=gid_physical,
    )
    return {
        "learned": sorted((r["name"], r["cgid"], r["rgid"], r["score"]) for r in learned_rows),
        "episodes": sorted((r["nid"], r["ngid"], r["rgid"], r["score"]) for r in episode_rows),
        "concepts": sorted((r["name"], r["gid"]) for r in concept_rows),
    }


async def _snapshot_production(client, gid_logical: str) -> dict[str, Any]:
    """用**生产读方法**取样 —— 用户真正走的那条路，正例里单独断言它也隔离。

    键同样含 group_id（MEDIUM-4 同因）：生产方法读回的 group_id 已被
    ``desanitize_group_id_from_graphiti`` 还原成 D16 冒号格式，原样入键即可。
    """
    history = await client.get_learning_history(user_id=SHARED_USER_ID, group_id=gid_logical)
    scores = await client.get_concept_score_history(
        concept_id=SHARED_NODE_ID,
        canvas_name=SHARED_CANVAS_PATH,
        group_id=gid_logical,
    )
    return {
        "learned": sorted((r.get("concept"), r.get("group_id"), r.get("score")) for r in history),
        "episodes": sorted((r.get("score"), str(r.get("timestamp"))) for r in scores),
        "concepts": [],
    }


def _assert_seed_landed(raw: dict[str, Any], prod: dict[str, Any], *, where: str) -> None:
    """seed **回读**确认 B 组确实有初始复习账（Codex r1 MEDIUM-5）。

    只检查写函数返回 True 是不够的：写返回成功却没落库时，B 是「空 → 空」，
    隔离断言照样绿。那是最难看的一种假绿 —— 门测的是一个空集合。
    所以取样之后立刻断言三个 facet 都**非空**，并且分数确实是 seed 分数。
    """
    for facet in ("learned", "episodes", "concepts"):
        assert raw[facet], f"precondition [{where}]: 手写带 scope 的读里 {facet} 为空 —— seed 没落库，门会测一个空集合"
    for facet in ("learned", "episodes"):
        assert prod[facet], f"precondition [{where}]: 生产读的 {facet} 为空 —— seed 没落库，门会测一个空集合"
    seed_scores = {score for _n, _c, _r, score in raw["learned"]}
    assert seed_scores == {SEED_SCORE}, f"precondition [{where}]: B 组初始 LEARNED 分数不是 seed 分数: {seed_scores}"
    # ⚠ Codex r3 M3: Episode 也要锁到 seed 分数，不能只要求"非空"。否则 seed 的
    # Episode 若已是 REVIEW_SCORE，后面那句「A 看到 95」就证明不了这次复习真的新增了
    # 记录 —— 旧的 95 就足以让正控通过。锁死之后，任何一条 95 都必然是本次写的。
    ep_scores = {score for _nid, _ngid, _rgid, score in raw["episodes"]}
    assert ep_scores == {SEED_SCORE}, f"precondition [{where}]: 初始 Episode 分数不是 seed 分数: {ep_scores}"


def _assert_group_b_intact(before: dict[str, Any], after: dict[str, Any], *, where: str) -> None:
    """B 组的复习读面逐条不变 —— 正例与两条负控**共用**的那一条断言。

    逐条比对身份（不是计数）: 每个 facet 都是「(名字, group, 值)」的有序列表，
    多出一行、少一行、同名行的值被覆盖，三种都会让它红。计数判据对第三种完全失明。
    """
    for facet, human in (
        ("learned", "LEARNED 复习账"),
        ("episodes", "scoring Episode 历史分数"),
        ("concepts", "可见 Concept 名单"),
    ):
        assert after[facet] == before[facet], (
            f"{_BREACH_MARKER} [{where}] B 组的 {human} 变了:\n  before = {before[facet]}\n  after  = {after[facet]}"
        )


# ---------------------------------------------------------------------------
# 门 0 — 环境自证: 本文件永不指向现网
# ---------------------------------------------------------------------------


def test_g610_never_targets_live_7691():
    """探针已拒现网端口; 此断言把"禁碰 live"从注释升级为可执行契约.

    ⚠ 如实声明（Codex r1 LOW-1 / r2 LOW-1 / r3 L1，三轮同一条，未改代码）：本测试与
    数据库测试**共用模块级 skipif**，所以 URI 指现网时它自己也被 skip，不构成独立的
    第三层执行证据。该层的独立证据落在 `evidence-g610/gate-7691-selflayer-*.txt`
    （直接调 `_targets_live_port()` / `_test_neo4j_reachable()` 证明其对 7691 返 True/False）。
    要让它真正独立执行需要把它拆到另一个不带 skipif 的文件 —— 属地盘外，登记待裁。

    顺带把 r3 M2 的形态钉死: 带前导零的 `:07691` 也必须被判为现网。
    """
    assert not _targets_live_port(NEO4J_TEST_URI)
    assert _targets_allowed_test_port(NEO4J_TEST_URI)
    # 形态门: 判据按解析端口而不是子串（前导零 / 缺省端口 两种都得拦下）
    assert _targets_live_port("bolt://127.0.0.1:07691")
    assert _targets_live_port("bolt://127.0.0.1:7691")
    assert _targets_live_port("bolt://127.0.0.1:7687")
    assert _targets_live_port("bolt://127.0.0.1")  # 缺省端口 = 7687 = 现网默认
    assert not _targets_live_port("bolt://127.0.0.1:7692")
    # 白名单（Codex r4 M2）: 不是 7692 就不跑 —— 「只跑容器」是声明，也得是判据
    assert _targets_allowed_test_port("bolt://127.0.0.1:7692")
    assert not _targets_allowed_test_port("bolt://127.0.0.1:7693")
    assert not _targets_allowed_test_port("bolt://127.0.0.1:07691")
    assert not _targets_allowed_test_port("bolt://127.0.0.1")


# ---------------------------------------------------------------------------
# 门 1 — 正例: A 组的复习写，B 组逐条不变（手写读 + 生产读两条路都验）
# ---------------------------------------------------------------------------


async def test_group_b_unaffected_by_group_a_review_write(gate_client):
    """A 组复习一次，B 组的 LEARNED / Episode / Concept 名单逐条不变。

    两层正向对照同在本测试内，缺一「B 没变」就不构成隔离证据:
      · seed 回读 —— B 组**确实有**初始复习账（Codex r1 MEDIUM-5: 只看写函数返回
        True 挡不住「写返回成功但没落库」，那种情形下 B 是空→空，照样"没变"）;
      · A 组自己的读**必须**看到新分数 —— 证明那次复习写真的发生了。
    """
    await _seed_pair(gate_client, GID_A_LOGICAL, GID_B_LOGICAL)

    before = await _snapshot_raw(gate_client, GID_B, group_filtered=True)
    before_prod = await _snapshot_production(gate_client, GID_B_LOGICAL)
    _assert_seed_landed(before, before_prod, where="positive/B")
    # A 侧也锁 seed 形态：这样「复习后 A 出现 95」必然是本次写的，不是本来就有的
    a_before = await _snapshot_raw(gate_client, GID_A, group_filtered=True)
    _assert_seed_landed(a_before, await _snapshot_production(gate_client, GID_A_LOGICAL), where="positive/A")

    await _review_write(gate_client, GID_A_LOGICAL)

    # 正向对照: A 确有本次复习写（读的是 A 自己的 scope）
    a_after = await _snapshot_raw(gate_client, GID_A, group_filtered=True)
    a_scores = {score for _n, _c, _r, score in a_after["learned"]}
    assert REVIEW_SCORE in a_scores, (
        f"precondition: A 组自己没看到复习分数 {REVIEW_SCORE}（拿到 {a_after['learned']}）"
        " —— 写没落库，本测试的『B 没变』不构成隔离证据"
    )
    a_ep_scores = {score for _nid, _ngid, _rgid, score in a_after["episodes"]}
    assert REVIEW_SCORE in a_ep_scores, (
        f"precondition: A 组的 Episode 里没有本次复习的 {REVIEW_SCORE}（拿到 {a_after['episodes']}）"
    )
    # Codex r3 M3 + r4 L1: 「有 95 且集合变了」只证明**变化**，不证明**新增** ——
    # 把原来那条 40 原地改成 95 也满足它。要证新增只能数条数: `_snapshot_raw` 的
    # episodes 是 list 不是 set（重复行保留），所以 +1 就是实打实多了一条 Episode。
    assert len(a_after["episodes"]) == len(a_before["episodes"]) + 1, (
        f"precondition: A 组 Episode 条数未 +1（{len(a_before['episodes'])} → {len(a_after['episodes'])}）"
        " —— 本次复习没有**新增**记录，只是改了旧的"
    )
    # 且旧的那条 seed 记录原样还在（新增 ≠ 覆盖）
    assert all(row in a_after["episodes"] for row in a_before["episodes"]), (
        f"precondition: A 组原有 Episode 被改写而非新增: {a_before['episodes']} → {a_after['episodes']}"
    )

    # Codex r4 M1: 生产读也要有「切回 A 看得见本次复习」的正控。少了它，一个恒返回
    # B 的旧数据的生产 getter 也能让本门全绿（B 前后相等 + A 由手写查询单独验）。
    a_after_prod = await _snapshot_production(gate_client, GID_A_LOGICAL)
    assert REVIEW_SCORE in {score for _n, _g, score in a_after_prod["learned"]}, (
        f"precondition: **生产读**在 A 的 scope 下看不到本次复习分数 {REVIEW_SCORE}"
        f"（拿到 {a_after_prod['learned']}）—— 生产读可能根本没按 group 取数"
    )
    assert REVIEW_SCORE in {s for s, _ts in a_after_prod["episodes"]}, (
        f"precondition: **生产读**在 A 的 scope 下看不到本次复习的 Episode（拿到 {a_after_prod['episodes']}）"
    )

    # 隔离判据: 手写带 scope 的读 与 生产读，两条路都不变
    after = await _snapshot_raw(gate_client, GID_B, group_filtered=True)
    _assert_group_b_intact(before, after, where="positive/raw-scoped")
    after_prod = await _snapshot_production(gate_client, GID_B_LOGICAL)
    _assert_group_b_intact(before_prod, after_prod, where="positive/production-read")


# ---------------------------------------------------------------------------
# 门 2 — 负控 ①: 写侧误标 group 身份键 ⇒ 同一条断言必红
# ---------------------------------------------------------------------------


async def test_negctl_write_side_mislabeled_group_breaches_isolation(gate_client):
    """本该写进 A 的那次复习，group 身份键误标成 B ⇒ B 的读看见它 ⇒ 隔离断言必红。

    为什么负控从写侧身份键制造: 按 W1，业务写把 group_id 放进 MERGE 身份键
    （``MERGE (c:Concept {name, group_id})``），写侧**没有**可"去掉"的 group 过滤。
    误标身份键就是这条路径上唯一真实的串台形态。

    与正例的单变量差: 只有 ``_review_write`` 的 group 实参从 A 换成 B —— seed、资产、
    取样函数、断言函数全部逐字相同。
    """
    await _seed_pair(gate_client, GID_NEG_A_LOGICAL, GID_NEG_B_LOGICAL)
    before = await _snapshot_raw(gate_client, GID_NEG_B, group_filtered=True)
    before_prod = await _snapshot_production(gate_client, GID_NEG_B_LOGICAL)
    _assert_seed_landed(before, before_prod, where="negctl-write-side/B")

    # ⬇ 唯一的变量：本该是 GID_NEG_A_LOGICAL
    await _review_write(gate_client, GID_NEG_B_LOGICAL)

    after = await _snapshot_raw(gate_client, GID_NEG_B, group_filtered=True)
    with pytest.raises(AssertionError, match=_BREACH_MARKER):
        _assert_group_b_intact(before, after, where="negctl-write-side")


# ---------------------------------------------------------------------------
# 门 3 — 负控 ②: 读侧去掉 group 过滤 ⇒ 同一条断言必红
# ---------------------------------------------------------------------------


async def test_negctl_read_side_without_group_filter_breaches_isolation(gate_client):
    """B 的读去掉 group 过滤（R1 违规形态）⇒ 看见 A 组的写 ⇒ 隔离断言必红。

    **单变量**（Codex r1 HIGH-2 的收口）: 与正例相比，这里写的还是同一次
    ``_review_write(A)``、落的还是 A 自己的身份键、seed 与断言函数逐字相同 ——
    唯一的差别是 :func:`_snapshot_raw` 的 ``group_filtered`` 从 True 换成 False。

    为什么它一定会红: seed 让两组各有一条同名概念的 40 分 LEARNED；A 复习后 A 那条
    变 95。带 scope 的读只看见 B 的 40（不变）；去掉 scope 的读同时看见 A 的 95 与
    B 的 40，A 那条从 40 变 95 ⇒ 身份三元组里的值变了 ⇒ 红。
    这正是读契约 R1 要拦的那件事：写是对的，读没带 scope。
    """
    await _seed_pair(gate_client, GID_NEG_A_LOGICAL, GID_NEG_B_LOGICAL)
    before_unscoped = await _snapshot_raw(gate_client, GID_NEG_B, group_filtered=False)
    before_scoped = await _snapshot_raw(gate_client, GID_NEG_B, group_filtered=True)
    _assert_seed_landed(
        before_scoped, await _snapshot_production(gate_client, GID_NEG_B_LOGICAL), where="negctl-read-side/B"
    )

    await _review_write(gate_client, GID_NEG_A_LOGICAL)  # 写是**对的**：落 A 的身份键

    after_unscoped = await _snapshot_raw(gate_client, GID_NEG_B, group_filtered=False)
    with pytest.raises(AssertionError, match=_BREACH_MARKER):
        _assert_group_b_intact(before_unscoped, after_unscoped, where="negctl-read-side")

    # 对照: 同一次写、同一个 B、只把 scope 加回来 ⇒ 不红。
    # 证明红是"读少了 scope"造成的，不是那次写本身越界。
    after_scoped = await _snapshot_raw(gate_client, GID_NEG_B, group_filtered=True)
    _assert_group_b_intact(before_scoped, after_scoped, where="negctl-read-side/scoped-control")
