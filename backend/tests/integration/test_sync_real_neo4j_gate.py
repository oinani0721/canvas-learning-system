"""R10 复审 P2-03 — 真实 Neo4j 验收门 (P0-SYNC-ISO-2026-08-17).

审查裁定: fake/stub 不能充当真实 parser、事务语义或双 vault E2E 的验收
证据 (上一轮 `SET...ON CREATE SET` 语法炸弹正是 stub 测不出、真库一枪
爆的实证)。本文件全部跑**真实 Neo4j** (settings.NEO4J_URI):

1. 约束在位 (SHOW CONSTRAINTS)
2. 双 vault 同 id 写删隔离 E2E (真 parser + 真事务 + 真数据回查)
3. poisoned-transaction 前提验证 (statement 失败后同事务续跑必炸 —
   per-edge 独立事务的存在理由)
4. edge 单条失败不连坐兄弟边 (P1-02 修复的真实验收)
5. stale 边清理 (端点变更不留同键旧关系, P2-01)
6. 身份注册表真实 claim/collision (P0-01)

Neo4j 不可达时整文件 skip (CI 离线不误红); 测试数据全部走
vault__r10gate_* 前缀, setup/teardown 双向清理, 不碰生产 group。
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

import pytest

from app.config import get_settings

# ---------------------------------------------------------------------------
# 可达性探针 (模块级, 决定整文件 skip)
# ---------------------------------------------------------------------------


def _neo4j_reachable() -> bool:
    try:
        from neo4j import GraphDatabase

        settings = get_settings()
        driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
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
    pytest.mark.skipif(not _neo4j_reachable(), reason="real Neo4j unreachable — gate skipped"),
]

GATE_PREFIX = "vault__r10gate"
GID_A = f"{GATE_PREFIX}_a"
GID_B = f"{GATE_PREFIX}_b"


def _make_op(
    *,
    entity_type: str,
    entity_id: str,
    operation: str = "create",
    payload: dict[str, Any] | None = None,
):
    from app.models.sync_models import SyncOperation

    default_payload: dict[str, Any] = {}
    if entity_type == "node":
        default_payload = {"title": f"t-{entity_id}", "content": "c"}
    elif entity_type == "board":
        default_payload = {"name": f"board-{entity_id}"}

    return SyncOperation(
        operation_id=f"gate-{entity_type}-{entity_id}-{operation}-{uuid.uuid4().hex[:8]}",
        entity_type=entity_type,  # type: ignore[arg-type]
        entity_id=entity_id,
        operation=operation,  # type: ignore[arg-type]
        payload=payload if payload is not None else default_payload,
        timestamp=datetime.now(timezone.utc),
    )


def _make_request(ops, vault_id: str = "r10gate"):
    from app.models.sync_models import SyncBatchRequest

    return SyncBatchRequest(canvas_id="r10gate-canvas", vault_id=vault_id, operations=ops)


async def _cypher(query: str, **params: Any) -> list[dict[str, Any]]:
    from neo4j import AsyncGraphDatabase

    settings = get_settings()
    driver = AsyncGraphDatabase.driver(settings.NEO4J_URI, auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD))
    try:
        async with driver.session(database=settings.NEO4J_DATABASE) as session:
            result = await session.run(query, **params)
            return await result.data()
    finally:
        await driver.close()


async def _cleanup_gate_data() -> None:
    await _cypher("MATCH (n) WHERE n.group_id STARTS WITH $p DETACH DELETE n", p=GATE_PREFIX)
    await _cypher(
        "MATCH (v:VaultIdentity) WHERE v.physical_gid STARTS WITH $p DELETE v",
        p=GATE_PREFIX,
    )


@pytest.fixture
async def clean_gate_data():
    await _cleanup_gate_data()
    yield
    await _cleanup_gate_data()


@pytest.fixture
async def sync_service():
    from app.services.sync_service import SyncService

    svc = SyncService()
    yield svc
    await svc.close()


# ---------------------------------------------------------------------------
# 1. 约束在位
# ---------------------------------------------------------------------------


class TestConstraintsPresent:
    @pytest.mark.asyncio
    async def test_composite_constraints_online(self) -> None:
        rows = await _cypher("SHOW CONSTRAINTS")
        names = {r.get("name") for r in rows}
        for required in (
            "canvasnode_group_id_unique",
            "canvasboard_group_id_unique",
            "canvasboard_group_subject_name_unique",
        ):
            assert required in names, f"constraint {required} missing on live DB"


# ---------------------------------------------------------------------------
# 2. 双 vault 同 id 写删隔离 (真 parser + 真数据回查)
# ---------------------------------------------------------------------------


class TestDualVaultIsolationReal:
    @pytest.mark.asyncio
    async def test_same_id_write_then_delete_isolated(self, clean_gate_data, sync_service) -> None:
        shared_id = "r10gate-shared-node"

        # vault A 与 vault B 各写同 id 节点 (真实 parser 8/8 的行为版)
        resp_a = await sync_service.process_sync_batch(
            _make_request([_make_op(entity_type="node", entity_id=shared_id)]),
            group_id=GID_A,
        )
        resp_b = await sync_service.process_sync_batch(
            _make_request([_make_op(entity_type="node", entity_id=shared_id)]),
            group_id=GID_B,
        )
        assert resp_a.synced_count == 1, resp_a.results
        assert resp_b.synced_count == 1, resp_b.results

        rows = await _cypher(
            "MATCH (n:CanvasNode {id: $id}) WHERE n.group_id STARTS WITH $p RETURN n.group_id AS g ORDER BY g",
            id=shared_id,
            p=GATE_PREFIX,
        )
        assert [r["g"] for r in rows] == [GID_A, GID_B]

        # vault A 删除 → 只删自己, B 存活
        resp_del = await sync_service.process_sync_batch(
            _make_request([_make_op(entity_type="node", entity_id=shared_id, operation="delete")]),
            group_id=GID_A,
        )
        assert resp_del.synced_count == 1

        rows = await _cypher(
            "MATCH (n:CanvasNode {id: $id}) WHERE n.group_id STARTS WITH $p RETURN n.group_id AS g",
            id=shared_id,
            p=GATE_PREFIX,
        )
        assert [r["g"] for r in rows] == [GID_B]


# ---------------------------------------------------------------------------
# 3. poisoned-transaction 前提 (P1-02 的存在理由, 真实事务语义)
# ---------------------------------------------------------------------------


class TestPoisonedTransactionPremise:
    @pytest.mark.asyncio
    async def test_failed_statement_poisons_transaction(self) -> None:
        """同一事务: statement 失败后, 后续 statement 必然抛错 — 证明
        「段内 catch 后继续跑」只对 stub 成立 (审查 P1-02 探针复现)。"""
        from neo4j import AsyncGraphDatabase

        settings = get_settings()
        driver = AsyncGraphDatabase.driver(settings.NEO4J_URI, auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD))
        try:
            async with driver.session(database=settings.NEO4J_DATABASE) as session:
                tx = await session.begin_transaction()
                with pytest.raises(Exception):
                    result = await tx.run("THIS IS NOT CYPHER")
                    await result.consume()
                # 事务已 poisoned: 合法 statement 也必须失败
                with pytest.raises(Exception):
                    result = await tx.run("RETURN 1 AS ok")
                    await result.consume()
                await tx.rollback()
        finally:
            await driver.close()


# ---------------------------------------------------------------------------
# 4. edge 单条失败不连坐兄弟边 (P1-02 修复真实验收)
# ---------------------------------------------------------------------------


class TestEdgeFailureIsolationReal:
    @pytest.mark.asyncio
    async def test_missing_endpoint_edge_does_not_poison_siblings(self, clean_gate_data, sync_service) -> None:
        # 底座: vault A 两个节点
        resp = await sync_service.process_sync_batch(
            _make_request(
                [
                    _make_op(entity_type="node", entity_id="r10gate-na"),
                    _make_op(entity_type="node", entity_id="r10gate-nb"),
                ]
            ),
            group_id=GID_A,
        )
        assert resp.synced_count == 2, resp.results

        def edge_op(eid: str, src: str, tgt: str):
            return _make_op(
                entity_type="edge",
                entity_id=eid,
                payload={"source_node_id": src, "target_node_id": tgt, "label": "L"},
            )

        # 中间那条边端点不存在 (真实 MATCH 落空) — 前后两条必须照常提交
        resp = await sync_service.process_sync_batch(
            _make_request(
                [
                    edge_op("r10gate-e-ok1", "r10gate-na", "r10gate-nb"),
                    edge_op("r10gate-e-bad", "r10gate-na", "r10gate-ghost"),
                    edge_op("r10gate-e-ok2", "r10gate-nb", "r10gate-na"),
                ]
            ),
            group_id=GID_A,
        )
        assert resp.synced_count == 2
        assert resp.failed_count == 1
        by_id = {r.entity_id: r for r in resp.results}
        assert by_id["r10gate-e-bad"].success is False
        assert by_id["r10gate-e-ok1"].success is True
        assert by_id["r10gate-e-ok2"].success is True

        # 真实回查: 两条 ok 边真的持久化了 (不是 stub ACK)
        rows = await _cypher(
            "MATCH ()-[e:CANVAS_EDGE {group_id: $g}]->() RETURN e.id AS id ORDER BY id",
            g=GID_A,
        )
        assert [r["id"] for r in rows] == ["r10gate-e-ok1", "r10gate-e-ok2"]


# ---------------------------------------------------------------------------
# 5. stale 边清理 (P2-01): 端点变更不留同键旧关系
# ---------------------------------------------------------------------------


class TestStaleEdgeCleanupReal:
    @pytest.mark.asyncio
    async def test_endpoint_change_replaces_edge(self, clean_gate_data, sync_service) -> None:
        resp = await sync_service.process_sync_batch(
            _make_request(
                [
                    _make_op(entity_type="node", entity_id="r10gate-sa"),
                    _make_op(entity_type="node", entity_id="r10gate-sb"),
                    _make_op(entity_type="node", entity_id="r10gate-sc"),
                ]
            ),
            group_id=GID_A,
        )
        assert resp.synced_count == 3

        def edge_op(tgt: str):
            return _make_op(
                entity_type="edge",
                entity_id="r10gate-moving-edge",
                payload={
                    "source_node_id": "r10gate-sa",
                    "target_node_id": tgt,
                    "label": "L",
                },
            )

        resp = await sync_service.process_sync_batch(_make_request([edge_op("r10gate-sb")]), group_id=GID_A)
        assert resp.synced_count == 1
        # 同 id 边改指向 sc — 旧的 sa→sb 关系必须被清掉
        resp = await sync_service.process_sync_batch(_make_request([edge_op("r10gate-sc")]), group_id=GID_A)
        assert resp.synced_count == 1

        rows = await _cypher(
            "MATCH (s)-[e:CANVAS_EDGE {id: 'r10gate-moving-edge', group_id: $g}]->(t) RETURN s.id AS s, t.id AS t",
            g=GID_A,
        )
        assert rows == [{"s": "r10gate-sa", "t": "r10gate-sc"}], "同 {group_id, id} 只允许一条关系, 且指向新端点"


# ---------------------------------------------------------------------------
# 6. 身份注册表真实 claim / collision (P0-01)
# ---------------------------------------------------------------------------


class TestVaultIdentityRegistryReal:
    @pytest.mark.asyncio
    async def test_claim_then_collision_fail_closed(self, clean_gate_data) -> None:
        from app.services.vault_identity_registry import (
            VaultIdentityCollisionError,
            VaultIdentityRegistry,
        )

        gid = f"{GATE_PREFIX}_reg"
        reg = VaultIdentityRegistry()
        try:
            await reg.assert_identity(raw_vault_id="R10 Gate Reg", physical_gid=gid)
            # 同 raw 重复认领通过
            await reg.assert_identity(raw_vault_id="R10 Gate Reg", physical_gid=gid)
            # 不同 raw 认领同 gid → fail closed (跨进程路径: 清缓存重查 DB)
            reg._owner_cache.clear()
            with pytest.raises(VaultIdentityCollisionError):
                await reg.assert_identity(raw_vault_id="R10-Gate-Reg", physical_gid=gid)
            # DB 里真的有持久化认领记录
            rows = await _cypher(
                "MATCH (v:VaultIdentity {physical_gid: $g}) RETURN v.raw_name AS raw",
                g=gid,
            )
            assert rows == [{"raw": "r10 gate reg"}]
        finally:
            await reg.close()
