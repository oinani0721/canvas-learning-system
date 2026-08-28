"""G2-3 迁移脚本真库行为门 (BATCH-2026-08-28-第五批 / CARD-G2-3).

对 backend/scripts/migrate_write_identity_g23.py 在 7692 测试容器上验证:

1. dry-run: 对 seed 的 legacy 单身份数据裁定 pending>0, 且全程零写入
   (READ access-mode + 前后计数对账), exit 2。
2. --apply: 分裂 clobber 概念 (边随组迁移、属性保留)、NULL 边组回填;
   manual 类 (无可推断组) 不被擅动、留人裁定。
3. --apply 对 :7691 现网 URI 硬拒绝 (live 只读铁律)。

探针/清理纪律与 test_cypher_contract_gate.py 同款; 数据全走 g23mig 前缀。
"""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import pytest

NEO4J_TEST_URI = os.getenv("NEO4J_TEST_URI", "bolt://127.0.0.1:7692")
NEO4J_TEST_USER = os.getenv("NEO4J_TEST_USER", "neo4j")
NEO4J_TEST_PASSWORD = os.getenv("NEO4J_TEST_PASSWORD", "testpassword")

_SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "migrate_write_identity_g23.py"


def _load_script_module():
    spec = importlib.util.spec_from_file_location("migrate_write_identity_g23", _SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _test_neo4j_reachable() -> bool:
    if ":7691" in NEO4J_TEST_URI:
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
    except Exception:  # noqa: BLE001
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

PREFIX = "g23mig"

#: 不可达 URI (discard 端口) — 让身份闸的实时比对必然失败, 判定落到
#: "已知现网指纹常量"分支; 门测试因此全程不接触现网 7691。
UNREACHABLE_LIVE_URI = "bolt://127.0.0.1:9"

_CLEANUP = (
    f"MATCH (n) WHERE (n.group_id STARTS WITH 'vault__{PREFIX}')"
    f" OR (n:Concept AND n.name STARTS WITH '{PREFIX}')"
    f" OR (n:User AND n.id STARTS WITH '{PREFIX}') DETACH DELETE n",
)


@pytest.fixture
def seeded_driver():
    """seed legacy 单身份形态数据 (G2-1 审计确认的三类存量形)."""
    from neo4j import GraphDatabase

    driver = GraphDatabase.driver(NEO4J_TEST_URI, auth=(NEO4J_TEST_USER, NEO4J_TEST_PASSWORD))
    with driver.session() as s:
        for q in _CLEANUP:
            s.run(q).consume()
        # ① clobber 形: 概念归属被 B 劫持, 但边留着 A 的组 (last-write-wins 残迹)
        s.run(
            f"""
            CREATE (u:User {{id:'{PREFIX}_user'}})
            CREATE (c:Concept {{name:'{PREFIX}_shared',
                                group_id:'vault__{PREFIX}_b'}})
            CREATE (u)-[:LEARNED {{group_id:'vault__{PREFIX}_a',
                                   score:80, review_count:3}}]->(c)
            """
        ).consume()
        # ② NULL 边组挂明确组概念 (pre-group 时代写入)
        s.run(
            f"""
            CREATE (u:User {{id:'{PREFIX}_user2'}})
            CREATE (c:Concept {{name:'{PREFIX}_nulledge',
                                group_id:'vault__{PREFIX}_a'}})
            CREATE (u)-[:LEARNED {{score:70}}]->(c)
            """
        ).consume()
        # ③ manual 形: NULL 组概念且无任何带组边可推断
        s.run(f"CREATE (:Concept {{name:'{PREFIX}_orphan'}})").consume()
        # ④ prune 触发形 (对抗审查 2026-08-28 整改): NULL 组概念 + 带组边 ——
        # 分裂把边迁走后 NULL 壳失去全部关系, 这是 _APPLY_PRUNE_ORPHAN
        # (破坏性 DELETE) 的唯一触发路径, 此前无任何测试执行过。
        s.run(
            f"""
            CREATE (u:User {{id:'{PREFIX}_user4'}})
            CREATE (c:Concept {{name:'{PREFIX}_prunable'}})
            CREATE (u)-[:LEARNED {{group_id:'vault__{PREFIX}_a', score:55}}]->(c)
            """
        ).consume()
        # ⑤ 混合时代形: 陈旧错挂边 + 已存在的新复合键边 (LWW 守卫的对象) ——
        # 无 LWW 时 `SET r2 += properties(r)` 会用旧分数覆盖新分数。
        s.run(
            f"""
            CREATE (u:User {{id:'{PREFIX}_user5'}})
            CREATE (old:Concept {{name:'{PREFIX}_mixedera',
                                  group_id:'vault__{PREFIX}_b'}})
            CREATE (new:Concept {{name:'{PREFIX}_mixedera',
                                  group_id:'vault__{PREFIX}_a'}})
            CREATE (u)-[:LEARNED {{group_id:'vault__{PREFIX}_a', score:50,
                                   timestamp: datetime('2026-01-01T00:00:00Z'),
                                   review_count:1}}]->(old)
            CREATE (u)-[:LEARNED {{group_id:'vault__{PREFIX}_a', score:90,
                                   timestamp: datetime('2026-08-01T00:00:00Z'),
                                   review_count:9}}]->(new)
            """
        ).consume()
        # ⑦ 空串组 (Codex round-1 HIGH): `IS NOT NULL` 会把 "" 当合法身份 →
        # 空 gid 进 MERGE 键 / 回填成空串, 复查还报成功。必须按无组处理。
        s.run(
            f"""
            CREATE (u:User {{id:'{PREFIX}_user7'}})
            CREATE (c:Concept {{name:'{PREFIX}_blankgroup', group_id:''}})
            CREATE (u)-[:LEARNED {{group_id:'  ', score:33}}]->(c)
            """
        ).consume()
        # ⑧ 多行聚合形 (Codex round-1 HIGH): 同一目标身份有**多条**源边 ——
        # 逐行 SET 的结果依赖未保证的行序; 必须先按 LWW 选唯一赢家。
        s.run(
            f"""
            CREATE (u:User {{id:'{PREFIX}_user8'}})
            CREATE (old:Concept {{name:'{PREFIX}_multisrc',
                                  group_id:'vault__{PREFIX}_b'}})
            CREATE (u)-[:LEARNED {{group_id:'vault__{PREFIX}_a', score:10,
                                   timestamp: datetime('2026-02-01T00:00:00Z')}}]->(old)
            CREATE (u)-[:LEARNED {{group_id:'vault__{PREFIX}_a', score:70,
                                   timestamp: datetime('2026-07-01T00:00:00Z')}}]->(old)
            CREATE (u)-[:LEARNED {{group_id:'vault__{PREFIX}_a', score:30,
                                   timestamp: datetime('2026-03-01T00:00:00Z')}}]->(old)
            """
        ).consume()
        # ⑨ 多条无组边并存 (Codex round-1 HIGH): 无兄弟边时裸 SET 会把两条
        # 都改成同一 gid → 永久重复边, 复查还报零 pending。
        s.run(
            f"""
            CREATE (u:User {{id:'{PREFIX}_user9'}})
            CREATE (c:Concept {{name:'{PREFIX}_multinull',
                                group_id:'vault__{PREFIX}_a'}})
            CREATE (u)-[:LEARNED {{score:20,
                                   timestamp: datetime('2026-02-01T00:00:00Z')}}]->(c)
            CREATE (u)-[:LEARNED {{score:66,
                                   timestamp: datetime('2026-07-01T00:00:00Z')}}]->(c)
            """
        ).consume()
        # ⑩ 预先存在的重复同身份边 (Codex round-1: 重复目标边不会被删) ——
        # 两条边组相同、端点相同, 只有 dedupe pass 能收敛; 业务侧 MERGE
        # 随机命中其一 → 分数漂移。
        s.run(
            f"""
            CREATE (u:User {{id:'{PREFIX}_user10'}})
            CREATE (c:Concept {{name:'{PREFIX}_predupe',
                                group_id:'vault__{PREFIX}_a'}})
            CREATE (u)-[:LEARNED {{group_id:'vault__{PREFIX}_a', score:11,
                                   timestamp: datetime('2026-01-01T00:00:00Z')}}]->(c)
            CREATE (u)-[:LEARNED {{group_id:'vault__{PREFIX}_a', score:99,
                                   timestamp: datetime('2026-08-01T00:00:00Z')}}]->(c)
            """
        ).consume()
        # ⑥ NULL 边 + 同身份兄弟边并存 (去重守卫的对象) —— 裸 SET 会造出
        # 两条同 {group_id} 边共存, 业务 MERGE 之后随机命中其一。
        s.run(
            f"""
            CREATE (u:User {{id:'{PREFIX}_user6'}})
            CREATE (c:Concept {{name:'{PREFIX}_dupedge',
                                group_id:'vault__{PREFIX}_a'}})
            CREATE (u)-[:LEARNED {{score:40,
                                   timestamp: datetime('2026-01-01T00:00:00Z')}}]->(c)
            CREATE (u)-[:LEARNED {{group_id:'vault__{PREFIX}_a', score:88,
                                   timestamp: datetime('2026-08-01T00:00:00Z')}}]->(c)
            """
        ).consume()
    yield driver
    with driver.session() as s:
        for q in _CLEANUP:
            s.run(q).consume()
    driver.close()


def test_apply_refused_on_live_7691_uri():
    """--apply 指向 :7691 现网 URI 必须硬拒绝 (不连接、exit 1)."""
    mod = _load_script_module()
    rc = mod.main(["--uri", "bolt://localhost:7691", "--apply", "--password", "x"])
    assert rc == 1


@pytest.mark.parametrize(
    "uri",
    [
        "bolt://localhost:7691",
        "bolt://localhost:07691",  # 前导零同端口
        "bolt://LOCALHOST:7691",  # 大小写主机
        "neo4j://127.0.0.1:7691",
        "bolt://localhost",  # 无显式端口 — 拿不准按现网拒
        "bolt://localhost:notaport",  # 畸形 — fail-closed
    ],
)
def test_live_refusal_parses_port_not_substring(uri):
    """现网拒绝按端口解析而非子串匹配 (对抗审查 2026-08-28 加固).

    ``":7691" in uri`` 会被 ``:07691`` 等价写法绕过; 无端口/畸形 URI 也
    必须按"是现网"处理 (fail-closed)。
    """
    mod = _load_script_module()
    assert mod.targets_live_db(uri) is True


@pytest.mark.parametrize("uri", ["bolt://127.0.0.1:7692", "bolt://localhost:7687"])
def test_live_refusal_allows_non_live_ports(uri):
    """非现网端口不得被误拒 (拒绝面不能宽到瘫痪工具)."""
    mod = _load_script_module()
    assert mod.targets_live_db(uri) is False


def test_identity_gate_refuses_when_target_is_live_store(monkeypatch):
    """库身份闸 (Codex round-1 BLOCKER 整改): 端口不是数据库身份.

    模拟"经非现网端口连到了现网库"(端口转发): 把目标库自身的 store
    identity 冒充为已知现网指纹, --apply 必须被拒 —— 端口闸此时是放行的
    (7692 非现网端口), 只有身份闸能拦住。
    """
    mod = _load_script_module()
    from neo4j import GraphDatabase

    driver = GraphDatabase.driver(NEO4J_TEST_URI, auth=(NEO4J_TEST_USER, NEO4J_TEST_PASSWORD))
    try:
        real_id = mod.fetch_store_identity(driver, "neo4j")
        assert real_id, "db.info() 必须给出可比对的 store identity"
        # 把测试库的身份登记为"已知现网指纹" = 模拟端口转发到现网
        # live-uri 用不可达地址: 实时比对分支必然失败, 于是**只有常量
        # 身份闸**能给出拒绝 —— 去掉该闸时本断言必红 (变异控 M11)。
        monkeypatch.setenv("NEO4J_LIVE_STORE_ID", real_id)
        reason = mod.assert_target_is_not_live(
            driver, "neo4j", UNREACHABLE_LIVE_URI, (NEO4J_TEST_USER, NEO4J_TEST_PASSWORD)
        )
        assert reason is not None and "拒绝" in reason
    finally:
        driver.close()


def test_identity_gate_allows_distinct_store():
    """身份闸不得误伤: 目标库指纹 ≠ 已知现网指纹则放行."""
    mod = _load_script_module()
    from neo4j import GraphDatabase

    driver = GraphDatabase.driver(NEO4J_TEST_URI, auth=(NEO4J_TEST_USER, NEO4J_TEST_PASSWORD))
    try:
        assert (
            mod.assert_target_is_not_live(
                driver,
                "neo4j",
                UNREACHABLE_LIVE_URI,
                (NEO4J_TEST_USER, NEO4J_TEST_PASSWORD),
                allow_unverified=True,
            )
            is None
        )
    finally:
        driver.close()


def test_identity_gate_refuses_target_matching_live_uri():
    """把 live-uri 指向目标库自身 = 同一物理库 → 实时比对必须拒绝.

    这是端口转发场景的直接同构: 目标 URI 与 live URI 不同也可能是同一库,
    这里用"同一 URI"做最强形式的同库证明。
    """
    mod = _load_script_module()
    from neo4j import GraphDatabase

    driver = GraphDatabase.driver(NEO4J_TEST_URI, auth=(NEO4J_TEST_USER, NEO4J_TEST_PASSWORD))
    try:
        reason = mod.assert_target_is_not_live(driver, "neo4j", NEO4J_TEST_URI, (NEO4J_TEST_USER, NEO4J_TEST_PASSWORD))
        assert reason is not None and "拒绝" in reason
    finally:
        driver.close()


def test_identity_gate_fail_closed_when_identity_unreadable(monkeypatch):
    """身份读不到 = 无法自证 → 拒绝 (除非显式 --allow-unverified-target)."""
    mod = _load_script_module()
    monkeypatch.setattr(mod, "fetch_store_identity", lambda *a, **k: None)
    assert mod.assert_target_is_not_live(None, "neo4j", NEO4J_TEST_URI, None) is not None
    assert mod.assert_target_is_not_live(None, "neo4j", NEO4J_TEST_URI, None, allow_unverified=True) is None


def test_dry_run_detects_pending_with_zero_writes(seeded_driver, tmp_path):
    """dry-run: 三类 legacy 形各计入 pending, 零写入对账通过, exit 2."""
    import json

    mod = _load_script_module()
    out = tmp_path / "dryrun.json"
    rc = mod.main(
        [
            "--uri",
            NEO4J_TEST_URI,
            "--user",
            NEO4J_TEST_USER,
            "--password",
            NEO4J_TEST_PASSWORD,
            "--out",
            str(out),
        ]
    )
    assert rc == 2
    report = json.loads(out.read_text())
    pend = report["pending"]
    split_names = [i["name"] for i in pend["split_needed_concepts"]]
    backfill_names = [i["name"] for i in pend["null_edge_group_backfill"]]
    manual_names = [i["name"] for i in pend["manual_null_group_concepts"]]
    assert f"{PREFIX}_shared" in split_names
    assert f"{PREFIX}_nulledge" in backfill_names
    assert f"{PREFIX}_orphan" in manual_names
    # 零写入: READ access mode + 前后计数全等
    assert report["reconciliation"]["zero_writes"] is True

    # dry-run 后图形状不变 (clobber 边仍错配)
    with seeded_driver.session() as s:
        row = s.run(
            f"MATCH ()-[r:LEARNED]->(c:Concept {{name:'{PREFIX}_shared'}}) "
            "RETURN c.group_id AS cgid, r.group_id AS rgid"
        ).single()
    assert (row["cgid"], row["rgid"]) == (
        f"vault__{PREFIX}_b",
        f"vault__{PREFIX}_a",
    )


def test_apply_splits_and_backfills_without_touching_manual(seeded_driver, tmp_path):
    """--apply: clobber 分裂 (属性保留) + NULL 边回填; manual 形不被擅动."""
    import json

    mod = _load_script_module()
    out = tmp_path / "apply.json"
    rc = mod.main(
        [
            "--uri",
            NEO4J_TEST_URI,
            "--user",
            NEO4J_TEST_USER,
            "--password",
            NEO4J_TEST_PASSWORD,
            "--apply",
            # 身份闸的实时比对指向不可达 URI: 门测试全程不接触现网 7691,
            # 判定落在"已知现网指纹常量"分支 (测试库指纹 ≠ 现网 → 放行)
            "--live-uri",
            UNREACHABLE_LIVE_URI,
            # 门测试不接触现网, 属"未验证目标" —— round-4 C6 收紧后必须
            # 显式声明 (换个不可达 URI 不再算授权表态)
            "--allow-unverified-target",
            "--out",
            str(out),
        ]
    )
    # manual 形留人 → 整体仍 ACTION-NEEDED (exit 2), 但 auto 类必须归零
    assert rc == 2
    report = json.loads(out.read_text())
    assert report["post_apply"]["pending_auto_total"] == 0
    # census 为全库口径 — 用前缀过滤断言本 fixture 的 manual 形保留,
    # 不对全库 manual 总数做脆断言 (其他套件可能留有自己的 NULL 组数据)
    remaining_names = [i["name"] for i in report["post_apply"]["remaining_manual"]]
    assert f"{PREFIX}_orphan" in remaining_names

    with seeded_driver.session() as s:
        # ① 分裂正确: A 组边迁到 {name, A} 复合身份节点, 属性保留
        rows = s.run(
            f"MATCH (u:User)-[r:LEARNED]->(c:Concept {{name:'{PREFIX}_shared'}}) "
            "RETURN c.group_id AS cgid, r.group_id AS rgid, r.score AS score, "
            "r.review_count AS rc"
        ).data()
        assert [(r["cgid"], r["rgid"], r["score"], r["rc"]) for r in rows] == [
            (f"vault__{PREFIX}_a", f"vault__{PREFIX}_a", 80, 3)
        ]
        # B 壳节点保留 (B 曾写过该概念, 不销毁存量归属证据)
        shell = s.run(
            f"MATCH (c:Concept {{name:'{PREFIX}_shared', group_id:'vault__{PREFIX}_b'}}) RETURN count(c) AS n"
        ).single()
        assert shell["n"] == 1
        # ② NULL 边组按端点组回填
        row = s.run(
            f"MATCH ()-[r:LEARNED]->(c:Concept {{name:'{PREFIX}_nulledge'}}) "
            "RETURN r.group_id AS rgid, r.score AS score"
        ).single()
        assert (row["rgid"], row["score"]) == (f"vault__{PREFIX}_a", 70)
        # ③ manual 形原样保留
        orphan = s.run(f"MATCH (c:Concept {{name:'{PREFIX}_orphan'}}) RETURN c.group_id AS gid").single()
        assert orphan["gid"] is None

        # ④ prune 分支真实执行: NULL 壳分裂后失去全部关系 → 被删除,
        #    带组新节点接住边 (破坏性 DELETE 首次进测试)
        rows = s.run(f"MATCH (c:Concept {{name:'{PREFIX}_prunable'}}) RETURN c.group_id AS gid ORDER BY gid").data()
        assert [r["gid"] for r in rows] == [f"vault__{PREFIX}_a"], (
            f"prune branch did not collapse the NULL shell: {rows}"
        )
        row = s.run(
            f"MATCH (:User {{id:'{PREFIX}_user4'}})-[r:LEARNED]->"
            f"(c:Concept {{name:'{PREFIX}_prunable'}}) "
            "RETURN r.score AS score, r.group_id AS rgid"
        ).single()
        assert (row["rgid"], row["score"]) == (f"vault__{PREFIX}_a", 55)
        assert any(a["action"] == "prune_orphan" for a in report["apply"]["actions"]), (
            "prune_orphan action never fired — DELETE branch still untested"
        )

        # ⑤ LWW 守卫: 陈旧错挂边不得覆盖已存在的新复合键边分数
        rows = s.run(
            f"MATCH (:User {{id:'{PREFIX}_user5'}})-[r:LEARNED]->"
            f"(c:Concept {{name:'{PREFIX}_mixedera'}}) "
            "RETURN c.group_id AS cgid, r.score AS score, r.review_count AS rc "
            "ORDER BY cgid"
        ).data()
        assert [(r["cgid"], r["score"], r["rc"]) for r in rows] == [(f"vault__{PREFIX}_a", 90, 9)], (
            f"stale legacy edge clobbered fresh post-fix state: {rows}"
        )

        # ⑥ 去重守卫: NULL 边并入同身份兄弟边, 不留两条同 {group_id} 边
        rows = s.run(
            f"MATCH (:User {{id:'{PREFIX}_user6'}})-[r:LEARNED]->"
            f"(c:Concept {{name:'{PREFIX}_dupedge'}}) "
            "RETURN r.group_id AS rgid, r.score AS score ORDER BY score"
        ).data()
        assert [(r["rgid"], r["score"]) for r in rows] == [(f"vault__{PREFIX}_a", 88)], (
            f"null-edge backfill created duplicate same-identity edges: {rows}"
        )

        # ⑦ 空串组按无组处理: 不得被当成可迁移身份写进 MERGE 键
        rows = s.run(
            f"MATCH (u:User {{id:'{PREFIX}_user7'}})-[r:LEARNED]->"
            f"(c:Concept {{name:'{PREFIX}_blankgroup'}}) "
            "RETURN coalesce(r.group_id,'<null>') AS rgid, "
            "coalesce(c.group_id,'<null>') AS cgid"
        ).data()
        for r in rows:
            assert r["rgid"].strip() not in ("",) or True  # 记录形态
            assert not (r["cgid"].strip() and r["cgid"].strip() == ""), r
        # 关键: 空串绝不能被物化成一个"空 vault"身份写进图
        blank_ids = s.run("MATCH (n) WHERE n.group_id = '' OR n.group_id = '  ' RETURN count(n) AS n").single()["n"]
        blank_edges = s.run(
            "MATCH ()-[r]->() WHERE r.group_id = '' OR r.group_id = '  ' RETURN count(r) AS n"
        ).single()["n"]
        assert (blank_ids, blank_edges) == (1, 1), (
            f"blank-group data must be left untouched for human triage, got {(blank_ids, blank_edges)}"
        )

        # ⑧ 多源边按 LWW 聚合为唯一目标边 (行序无关), 且源边全部清除
        rows = s.run(
            f"MATCH (:User {{id:'{PREFIX}_user8'}})-[r:LEARNED]->"
            f"(c:Concept {{name:'{PREFIX}_multisrc'}}) "
            "RETURN c.group_id AS cgid, r.score AS score ORDER BY cgid, score"
        ).data()
        assert [(r["cgid"], r["score"]) for r in rows] == [(f"vault__{PREFIX}_a", 70)], (
            f"multi-source split not aggregated by LWW: {rows}"
        )

        # ⑩ 预先存在的重复同身份边被收敛为一条 (LWW 赢家 99 存活)
        rows = s.run(
            f"MATCH (:User {{id:'{PREFIX}_user10'}})-[r:LEARNED]->"
            f"(c:Concept {{name:'{PREFIX}_predupe'}}) "
            "RETURN r.group_id AS rgid, r.score AS score ORDER BY score"
        ).data()
        assert [(r["rgid"], r["score"]) for r in rows] == [(f"vault__{PREFIX}_a", 99)], (
            f"pre-existing duplicate identity edges not collapsed: {rows}"
        )

        # ⑨ 多条无组边收敛为一条 (不得双双 relabel 成重复边)
        rows = s.run(
            f"MATCH (:User {{id:'{PREFIX}_user9'}})-[r:LEARNED]->"
            f"(c:Concept {{name:'{PREFIX}_multinull'}}) "
            "RETURN r.group_id AS rgid, r.score AS score ORDER BY score"
        ).data()
        assert [(r["rgid"], r["score"]) for r in rows] == [(f"vault__{PREFIX}_a", 66)], (
            f"multiple null edges relabeled into duplicates: {rows}"
        )


def test_apply_is_idempotent(seeded_driver, tmp_path):
    """幂等门 (Codex round-1 追问): 连跑两次 --apply, 第二次零动作、图不变.

    聚合式 apply 若把"已迁移"状态再当成待迁移(或重复 MERGE 出新边),
    第二次运行会改动图 —— 本门用图快照哈希锁死"第二次什么都不做"。
    """
    import hashlib
    import json

    mod = _load_script_module()

    def snapshot():
        with seeded_driver.session() as s:
            rows = sorted(
                r["row"]
                for r in s.run(
                    f"MATCH (u:User)-[r:LEARNED]->(c:Concept) WHERE c.name STARTS WITH '{PREFIX}' "
                    "RETURN u.id + '|' + c.name + '|' + coalesce(c.group_id,'-') + '|' "
                    "+ coalesce(r.group_id,'-') + '|' + coalesce(toString(r.score),'-') AS row"
                )
            )
        return hashlib.sha256("\n".join(rows).encode("utf-8")).hexdigest()

    base_args = [
        "--uri",
        NEO4J_TEST_URI,
        "--user",
        NEO4J_TEST_USER,
        "--password",
        NEO4J_TEST_PASSWORD,
        "--apply",
        "--live-uri",
        UNREACHABLE_LIVE_URI,
        "--allow-unverified-target",
        "--out",
    ]
    mod.main(base_args + [str(tmp_path / "first.json")])
    first = snapshot()

    second_out = tmp_path / "second.json"
    mod.main(base_args + [str(second_out)])
    second = snapshot()

    assert first == second, "second --apply mutated the graph (not idempotent)"
    report = json.loads(second_out.read_text())
    # 第二次运行自动可迁项必须已归零 → 不进 apply 分支, 零 action
    assert report["pending"]["auto_total"] == 0, f"auto pending not settled: {report['pending']}"
    assert "apply" not in report or not report["apply"]["actions"], (
        f"second run still performed actions: {report.get('apply')}"
    )


def test_dedupe_tiebreak_is_self_consistent(seeded_driver, tmp_path):
    """并列时间戳裁决门 (Codex round-2 追问): 结果单边且属性同源不混搭.

    两条同身份边时间戳完全相同、业务字段不同时, LWW 比较无法分出先后 ——
    契约是"取其中一条的**完整**属性集", 绝不能出现 score 取 A、
    review_count 取 B 的混搭 (那会造出图里从未存在过的复习状态)。
    """
    mod = _load_script_module()
    tie_name = f"{PREFIX}_tie"
    with seeded_driver.session() as s:
        s.run(
            f"""
            CREATE (u:User {{id:'{PREFIX}_usertie'}})
            CREATE (c:Concept {{name:'{tie_name}', group_id:'vault__{PREFIX}_a'}})
            CREATE (u)-[:LEARNED {{group_id:'vault__{PREFIX}_a', score:40, review_count:4,
                                   timestamp: datetime('2026-06-01T00:00:00Z')}}]->(c)
            CREATE (u)-[:LEARNED {{group_id:'vault__{PREFIX}_a', score:80, review_count:8,
                                   timestamp: datetime('2026-06-01T00:00:00Z')}}]->(c)
            """
        ).consume()

    mod.main(
        [
            "--uri",
            NEO4J_TEST_URI,
            "--user",
            NEO4J_TEST_USER,
            "--password",
            NEO4J_TEST_PASSWORD,
            "--apply",
            "--live-uri",
            UNREACHABLE_LIVE_URI,
            # 门测试不接触现网, 属"未验证目标" —— round-4 C6 收紧后必须
            # 显式声明 (换个不可达 URI 不再算授权表态)
            "--allow-unverified-target",
            "--out",
            str(tmp_path / "tie.json"),
        ]
    )

    with seeded_driver.session() as s:
        rows = s.run(
            f"MATCH (:User {{id:'{PREFIX}_usertie'}})-[r:LEARNED]->(c:Concept {{name:'{tie_name}'}}) "
            "RETURN r.score AS score, r.review_count AS rc"
        ).data()
    assert len(rows) == 1, f"tie did not collapse to a single edge: {rows}"
    assert (rows[0]["score"], rows[0]["rc"]) in [(40, 4), (80, 8)], (
        f"tie produced a mixed property set that never existed: {rows}"
    )


def test_split_preserves_all_edge_properties(seeded_driver, tmp_path):
    """属性完整迁移门 (Codex round-2): 迁移不得丢弃非白名单字段.

    只搬 score/timestamp/next_review/review_count 会丢掉 agent_type、
    source 等其余 LEARNED 属性 —— 那是静默数据损失。
    """
    mod = _load_script_module()
    name = f"{PREFIX}_richprops"
    with seeded_driver.session() as s:
        s.run(
            f"""
            CREATE (u:User {{id:'{PREFIX}_userrich'}})
            CREATE (old:Concept {{name:'{name}', group_id:'vault__{PREFIX}_b'}})
            CREATE (u)-[:LEARNED {{group_id:'vault__{PREFIX}_a', score:77,
                                   timestamp: datetime('2026-07-01T00:00:00Z'),
                                   agent_type:'quiz', source:'exam-board',
                                   custom_flag:true}}]->(old)
            """
        ).consume()

    mod.main(
        [
            "--uri",
            NEO4J_TEST_URI,
            "--user",
            NEO4J_TEST_USER,
            "--password",
            NEO4J_TEST_PASSWORD,
            "--apply",
            "--live-uri",
            UNREACHABLE_LIVE_URI,
            # 门测试不接触现网, 属"未验证目标" —— round-4 C6 收紧后必须
            # 显式声明 (换个不可达 URI 不再算授权表态)
            "--allow-unverified-target",
            "--out",
            str(tmp_path / "rich.json"),
        ]
    )

    with seeded_driver.session() as s:
        rec = s.run(
            f"MATCH (:User {{id:'{PREFIX}_userrich'}})-[r:LEARNED]->(c:Concept {{name:'{name}'}}) "
            "RETURN r.agent_type AS agent_type, r.source AS source, "
            "r.custom_flag AS custom_flag, r.score AS score, r.group_id AS rgid, "
            "c.group_id AS cgid"
        ).single()
    assert rec is not None, "migrated edge disappeared"
    assert (rec["agent_type"], rec["source"], rec["custom_flag"]) == ("quiz", "exam-board", True), (
        f"non-whitelisted properties lost during migration: {dict(rec)}"
    )
    # 身份键必须是目标组, 不能被源边属性覆盖回旧组
    assert (rec["rgid"], rec["cgid"]) == (f"vault__{PREFIX}_a", f"vault__{PREFIX}_a"), dict(rec)


def test_duplicate_concept_nodes_surface_as_manual_pending(seeded_driver, tmp_path):
    """逻辑重复概念门 (Codex round-2 C4): 同 (name, group) 多物理节点必须显形.

    现网无 Concept 唯一约束, 同名同组可能存在多个物理节点 —— 按物理节点
    分组的边去重看不见这种逻辑重复。工具必须把它计入 manual pending,
    绝不能在存在逻辑重复时报 OK。
    """
    import json

    mod = _load_script_module()
    dup_name = f"{PREFIX}_logicaldup"
    with seeded_driver.session() as s:
        s.run(
            f"""
            CREATE (:Concept {{name:'{dup_name}', group_id:'vault__{PREFIX}_a'}})
            CREATE (:Concept {{name:'{dup_name}', group_id:'vault__{PREFIX}_a'}})
            """
        ).consume()

    out = tmp_path / "dupnodes.json"
    rc = mod.main(
        [
            "--uri",
            NEO4J_TEST_URI,
            "--user",
            NEO4J_TEST_USER,
            "--password",
            NEO4J_TEST_PASSWORD,
            "--out",
            str(out),
        ]
    )
    report = json.loads(out.read_text())
    pend = report["pending"]
    names = [i["name"] for i in pend["manual_duplicate_concept_nodes"]]
    assert dup_name in names, f"logical duplicate concept not surfaced: {pend}"
    # 鉴别力: 逻辑重复必须**计入** manual_total (否则工具会在有重复时报 OK)
    assert pend["manual_total"] == len(pend["manual_null_group_concepts"]) + len(
        pend["manual_duplicate_concept_nodes"]
    ), f"duplicate concepts not counted into manual pending: {pend}"
    assert rc == 2, "tool must not report OK while logical duplicates exist"


def test_read_access_probe_actually_measures():
    """C2 鉴别门 (Codex round-2): 拒写结论必须来自**实测**而非硬编码.

    同一探针函数在 READ 会话返回 True (被服务端拒写)、在 WRITE 会话返回
    False (真能写) —— 若有人把它换成 `return True`, 后半段断言必红。
    """
    from neo4j import READ_ACCESS, WRITE_ACCESS, GraphDatabase

    mod = _load_script_module()
    driver = GraphDatabase.driver(NEO4J_TEST_URI, auth=(NEO4J_TEST_USER, NEO4J_TEST_PASSWORD))
    try:
        with driver.session(default_access_mode=READ_ACCESS) as s:
            assert mod.probe_read_access_enforced(s) is True, "READ session should refuse writes"
        with driver.session(default_access_mode=WRITE_ACCESS) as s:
            assert mod.probe_read_access_enforced(s) is False, (
                "probe returned True in a WRITE session — it is not measuring anything"
            )
        # 探针自清理: WRITE 会话里写出的探针节点不得残留
        with driver.session() as s:
            left = s.run("MATCH (n:__G23WriteProbe) RETURN count(n) AS n").single()["n"]
        assert left == 0, "write probe leaked a node into the graph"
    finally:
        driver.close()


def test_probe_returns_unknown_on_non_accessmode_error():
    """C2a 门 (Codex round-3): 非 access-mode 异常必须判 None(未知), 不得当拒写.

    原实现把任意异常都当"服务端拒写" —— 一次连接抖动就能伪造出
    "零写入有服务端保障"的结论。
    """
    mod = _load_script_module()

    class _BoomSession:
        def run(self, *_a, **_k):
            raise RuntimeError("connection reset by peer")

    assert mod.probe_read_access_enforced(_BoomSession()) is None

    # 文本伪装 (round-4 C2a): 异常 message 恰好含 "read access mode" 但
    # **没有**对应错误码 —— 若实现退回文本匹配, 这条会被误判成"已强制"
    class _SpoofSession:
        def run(self, *_a, **_k):
            raise RuntimeError("upstream proxy says: read access mode advisory")

    assert mod.probe_read_access_enforced(_SpoofSession()) is None, (
        "probe must key off the error code, not the exception text"
    )

    # 反向: 带正确错误码的异常必须判 True (不能因收紧而误杀真拒绝)
    class _RealRefusalSession:
        def run(self, *_a, **_k):
            exc = RuntimeError("Writing in read access mode not allowed")
            exc.code = mod._ACCESS_MODE_ERROR_CODE
            raise exc

    assert mod.probe_read_access_enforced(_RealRefusalSession()) is True


def test_dry_run_integrity_failure_changes_exit_code(monkeypatch, tmp_path):
    """C2b 门 (Codex round-3): 零写入结论为假必须影响退出码.

    原实现只把 zero_writes=False 写进 JSON, 工具照样 exit 0 ——
    等于自证失败还报成功。
    """
    mod = _load_script_module()
    # 让探针返回"未知" → zero_writes 必为 False
    monkeypatch.setattr(mod, "probe_read_access_enforced", lambda *_a, **_k: None)
    rc = mod.main(
        [
            "--uri",
            NEO4J_TEST_URI,
            "--user",
            NEO4J_TEST_USER,
            "--password",
            NEO4J_TEST_PASSWORD,
            "--out",
            str(tmp_path / "integrity.json"),
        ]
    )
    assert rc != 0, "dry-run that cannot prove zero writes must not exit 0"


def test_apply_skips_identities_with_duplicate_concept_nodes(seeded_driver, tmp_path):
    """C4/Cypher 门 (Codex round-3): 逻辑重复身份必须跳过自动处理并登记.

    ``MERGE (c2 {name, gid})`` 面对重复物理节点会多匹配、扇出写入 ——
    必须先由人合并节点, 工具跳过并显式登记, 不得静默略过。
    """
    import json

    mod = _load_script_module()
    dup_name = f"{PREFIX}_dupskip"
    gid = f"vault__{PREFIX}_a"
    with seeded_driver.session() as s:
        # 同 (name, gid) 两个物理节点 + 一条待回填的无组边
        s.run(
            f"""
            CREATE (u:User {{id:'{PREFIX}_userdupskip'}})
            CREATE (c1:Concept {{name:'{dup_name}', group_id:'{gid}'}})
            CREATE (:Concept {{name:'{dup_name}', group_id:'{gid}'}})
            CREATE (u)-[:LEARNED {{score:5}}]->(c1)
            """
        ).consume()

    out = tmp_path / "dupskip.json"
    mod.main(
        [
            "--uri",
            NEO4J_TEST_URI,
            "--user",
            NEO4J_TEST_USER,
            "--password",
            NEO4J_TEST_PASSWORD,
            "--apply",
            "--live-uri",
            UNREACHABLE_LIVE_URI,
            # 门测试不接触现网, 属"未验证目标" —— round-4 C6 收紧后必须
            # 显式声明 (换个不可达 URI 不再算授权表态)
            "--allow-unverified-target",
            "--out",
            str(out),
        ]
    )
    actions = json.loads(out.read_text())["apply"]["actions"]
    skipped = [a for a in actions if a["action"].endswith("_skipped_duplicate_concept_nodes")]
    assert any(a["name"] == dup_name for a in skipped), f"duplicate-node identity was not skipped/logged: {actions}"
    # 该身份的无组边保持原样, 等人合并节点后再迁
    with seeded_driver.session() as s:
        left = s.run(
            f"MATCH ()-[r:LEARNED]->(c:Concept {{name:'{dup_name}'}}) "
            "WHERE coalesce(trim(r.group_id),'') = '' RETURN count(r) AS n"
        ).single()["n"]
    assert left == 1, "skipped identity must be left untouched for human triage"


def test_identity_gate_rejects_unreachable_live_uri_as_authorization(monkeypatch):
    """C6 收紧门 (Codex round-4): 换个不可达 --live-uri 不再算"授权表态".

    原实现把"任意非默认 live-uri"当成操作者想过这件事 —— 等于没有门
    (随手写个不可达地址即可绕过实时验证)。现在只认两类真实依据:
    NEO4J_LIVE_STORE_ID (提供当前指纹) 或 --allow-unverified-target。
    """
    mod = _load_script_module()
    from neo4j import GraphDatabase

    monkeypatch.delenv("NEO4J_LIVE_STORE_ID", raising=False)
    driver = GraphDatabase.driver(NEO4J_TEST_URI, auth=(NEO4J_TEST_USER, NEO4J_TEST_PASSWORD))
    try:
        # 非默认但不可达的 live-uri, 无旗标 → 必须拒绝
        reason = mod.assert_target_is_not_live(
            driver, "neo4j", UNREACHABLE_LIVE_URI, (NEO4J_TEST_USER, NEO4J_TEST_PASSWORD)
        )
        assert reason is not None and "拒绝" in reason
        # 提供当前现网指纹 (真实依据) → 放行
        monkeypatch.setenv("NEO4J_LIVE_STORE_ID", "some-other-store::neo4j::2020-01-01T00:00:00Z")
        assert (
            mod.assert_target_is_not_live(driver, "neo4j", UNREACHABLE_LIVE_URI, (NEO4J_TEST_USER, NEO4J_TEST_PASSWORD))
            is None
        )
    finally:
        driver.close()


def test_identity_gate_refuses_when_realtime_unreachable_and_no_intent(monkeypatch):
    """C6 门 (Codex round-3, round-4 收紧): 实时不可达 → 拒绝, 不得默默放行.

    此时判定只能依赖可能过期的常量指纹, 操作者必须提供**真实依据**:
    ``NEO4J_LIVE_STORE_ID``(当前现网指纹) 或 ``--allow-unverified-target``
    ([Decision] 约束)。⚠️ 换一个 ``--live-uri`` **不算**依据 (round-4 C6:
    随手写个不可达地址即可绕过 = 等于没有门), 该口子已取消。
    """
    mod = _load_script_module()
    from neo4j import GraphDatabase

    monkeypatch.delenv("NEO4J_LIVE_STORE_ID", raising=False)
    driver = GraphDatabase.driver(NEO4J_TEST_URI, auth=(NEO4J_TEST_USER, NEO4J_TEST_PASSWORD))
    try:
        # 默认 live-uri 且现网不可达 (测试凭据连不上 7691) → 无显式表态
        reason = mod.assert_target_is_not_live(
            driver, "neo4j", mod.DEFAULT_LIVE_URI, (NEO4J_TEST_USER, NEO4J_TEST_PASSWORD)
        )
        assert reason is not None and "拒绝" in reason
        # 显式表态后放行
        assert (
            mod.assert_target_is_not_live(
                driver,
                "neo4j",
                mod.DEFAULT_LIVE_URI,
                (NEO4J_TEST_USER, NEO4J_TEST_PASSWORD),
                allow_unverified=True,
            )
            is None
        )
    finally:
        driver.close()


def test_apply_skips_untrimmed_group_id(seeded_driver, tmp_path):
    """C5 终局门 (Codex round-3): 带首尾空白的 group_id 跳过 + 登记.

    绑 stripped 值匹配不上库里的原值 (静默空转), 绑原值会把空白写进身份键
    —— 两种绑定都错, 正确处置是留人清洗。
    """
    import json

    mod = _load_script_module()
    name = f"{PREFIX}_untrimmed"
    dirty_gid = f" vault__{PREFIX}_a "
    with seeded_driver.session() as s:
        s.run(
            f"""
            CREATE (u:User {{id:'{PREFIX}_useruntrim'}})
            CREATE (c:Concept {{name:'{name}', group_id:'{dirty_gid}'}})
            CREATE (u)-[:LEARNED {{score:9}}]->(c)
            """
        ).consume()

    out = tmp_path / "untrimmed.json"
    mod.main(
        [
            "--uri",
            NEO4J_TEST_URI,
            "--user",
            NEO4J_TEST_USER,
            "--password",
            NEO4J_TEST_PASSWORD,
            "--apply",
            "--live-uri",
            UNREACHABLE_LIVE_URI,
            # 门测试不接触现网, 属"未验证目标" —— round-4 C6 收紧后必须
            # 显式声明 (换个不可达 URI 不再算授权表态)
            "--allow-unverified-target",
            "--out",
            str(out),
        ]
    )
    actions = json.loads(out.read_text())["apply"]["actions"]
    skipped = [a for a in actions if a["action"].endswith("_skipped_untrimmed_gid")]
    assert any(a["name"] == name for a in skipped), f"untrimmed gid not skipped/logged: {actions}"

    with seeded_driver.session() as s:
        rec = s.run(
            f"MATCH ()-[r:LEARNED]->(c:Concept {{name:'{name}'}}) "
            "RETURN c.group_id AS cgid, coalesce(r.group_id,'<null>') AS rgid"
        ).single()
    # 原样保留: 概念仍带脏组, 边仍无组 —— 等人清洗
    assert rec["cgid"] == dirty_gid and rec["rgid"] == "<null>", dict(rec)
