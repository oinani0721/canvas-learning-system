"""P0-SYNC-ISO-2026-08-17 — /sync/batch 跨 vault 隔离行为测试.

背景 (Codex 对抗审查确认的 P0): sync_service 六条 Cypher 全部以裸 id 做
MERGE/MATCH/DELETE, 无任何 vault 隔离; sync.py 调 resolve_vault_group_id()
后丢弃返回值。两个 vault 同 id 实体互相覆盖; _delete_board 按 canvasId
级联 DETACH DELETE, 一次跨 vault 碰撞可抹掉另一 vault 整块画布。

教训锁: 上一轮 P0 逃逸的直接原因是 test_wave5_stageb_continued 只做静态
import/字段断言。本文件全部是**行为断言** — 检查 _StubTransaction.run_calls
里实际发出的 Cypher 文本和参数绑定, 禁止 hasattr 式断言。

覆盖矩阵:
1. 六条 Cypher 文本全部含 group_id 键 (MERGE/MATCH 花括号 pattern 内)
2. kwargs 携带物理格式 group (vault__ 前缀, 防漏 to_physical_group_id)
3. 双 vault 场景: 同 entity_id 不同 group 的 delete/upsert 参数互不相同
4. _delete_board 级联 Cypher 双侧 (board + node) 都带 group
5. endpoint 层: vault_id → 物理 group_id 注入 service (端到端行为)
"""

from __future__ import annotations

import re
from typing import Any

import pytest

from app.models.sync_models import SyncBatchRequest
from app.services.sync_service import SyncService

# 复用 Segment Commit 测试的 stub 基建 (行为记录: run_calls = query + kwargs)
from tests.unit.test_sync_segment_commit import (
    _make_op,
    _StubDriver,
    _StubSession,
    _StubTransaction,
)

PHYSICAL_GID_A = "vault__vault_a"
PHYSICAL_GID_B = "vault__vault_b"


def _norm(query: str) -> str:
    """折叠空白, 让 Cypher 文本断言不受缩进/换行影响."""
    return re.sub(r"\s+", " ", query).strip()


def _make_service() -> tuple[SyncService, _StubSession]:
    session = _StubSession()
    svc = SyncService()
    svc._driver = _StubDriver(session)  # type: ignore[assignment]
    return svc, session


def _all_run_calls(session: _StubSession) -> list[dict[str, Any]]:
    return [call for tx in session.transactions for call in tx.run_calls]


async def _run_single_op(
    *,
    entity_type: str,
    operation: str,
    group_id: str,
    entity_id: str = "shared-id",
) -> list[dict[str, Any]]:
    """跑单 op batch, 返回全部 run_calls."""
    svc, session = _make_service()
    request = SyncBatchRequest(
        canvas_id="c1",
        vault_id="vault_a",
        operations=[_make_op(entity_type=entity_type, entity_id=entity_id, operation=operation)],
    )
    await svc.process_sync_batch(request, group_id=group_id)
    return _all_run_calls(session)


# ---------------------------------------------------------------------------
# 1+2: 六条 Cypher 键含 group_id + kwargs 物理格式
# ---------------------------------------------------------------------------


class TestSyncServiceGroupKeys:
    """六条 Cypher 的 MERGE/MATCH 键 pattern 必须含 group_id, 参数必须绑定."""

    @pytest.mark.asyncio
    async def test_upsert_node_merge_key_carries_group(self) -> None:
        calls = await _run_single_op(entity_type="node", operation="create", group_id=PHYSICAL_GID_A)
        assert len(calls) == 1
        query = _norm(calls[0]["query"])
        assert "MERGE (n:CanvasNode {id: $entity_id, group_id: $group_id})" in query
        assert calls[0]["kwargs"]["group_id"] == PHYSICAL_GID_A
        assert calls[0]["kwargs"]["group_id"].startswith("vault__")

    @pytest.mark.asyncio
    async def test_delete_node_match_key_carries_group(self) -> None:
        calls = await _run_single_op(entity_type="node", operation="delete", group_id=PHYSICAL_GID_A)
        assert len(calls) == 1
        query = _norm(calls[0]["query"])
        assert "MATCH (n:CanvasNode {id: $entity_id, group_id: $group_id})" in query
        assert "DETACH DELETE n" in query
        assert calls[0]["kwargs"]["group_id"] == PHYSICAL_GID_A

    @pytest.mark.asyncio
    async def test_upsert_edge_endpoints_and_merge_key_carry_group(self) -> None:
        calls = await _run_single_op(entity_type="edge", operation="create", group_id=PHYSICAL_GID_A)
        assert len(calls) == 1
        query = _norm(calls[0]["query"])
        # 两个端点 OPTIONAL MATCH 都必须限定 group — 否则跨 vault 借端点
        assert "OPTIONAL MATCH (source:CanvasNode {id: $source_node_id, group_id: $group_id})" in query
        assert "OPTIONAL MATCH (target:CanvasNode {id: $target_node_id, group_id: $group_id})" in query
        # 边本身的 MERGE 键也必须含 group
        assert "MERGE (source)-[e:CANVAS_EDGE {id: $entity_id, group_id: $group_id}]->(target)" in query
        assert calls[0]["kwargs"]["group_id"] == PHYSICAL_GID_A

    @pytest.mark.asyncio
    async def test_delete_edge_match_key_carries_group(self) -> None:
        calls = await _run_single_op(entity_type="edge", operation="delete", group_id=PHYSICAL_GID_A)
        assert len(calls) == 1
        query = _norm(calls[0]["query"])
        assert "MATCH ()-[e:CANVAS_EDGE {id: $entity_id, group_id: $group_id}]->()" in query
        assert calls[0]["kwargs"]["group_id"] == PHYSICAL_GID_A

    @pytest.mark.asyncio
    async def test_upsert_board_merge_key_carries_group(self) -> None:
        calls = await _run_single_op(entity_type="board", operation="create", group_id=PHYSICAL_GID_A)
        assert len(calls) == 1
        query = _norm(calls[0]["query"])
        assert "MERGE (b:CanvasBoard {id: $entity_id, group_id: $group_id})" in query
        assert calls[0]["kwargs"]["group_id"] == PHYSICAL_GID_A

    @pytest.mark.asyncio
    async def test_delete_board_cascade_both_sides_carry_group(self) -> None:
        """最高危路径: board 级联删除的 board 侧和 node 侧都必须限定 group.

        缺任何一侧, 跨 vault 同 id board 的 delete 会把另一 vault 的
        整块画布 (board + 全部 node) DETACH DELETE 掉。
        """
        calls = await _run_single_op(entity_type="board", operation="delete", group_id=PHYSICAL_GID_A)
        assert len(calls) == 1
        query = _norm(calls[0]["query"])
        assert "MATCH (b:CanvasBoard {id: $entity_id, group_id: $group_id})" in query
        assert "OPTIONAL MATCH (n:CanvasNode {canvasId: $entity_id, group_id: $group_id})" in query
        assert "DETACH DELETE b, n" in query
        assert calls[0]["kwargs"]["group_id"] == PHYSICAL_GID_A


# ---------------------------------------------------------------------------
# 2.5: Cypher 子句顺序 (E2E 实测教训锁)
# ---------------------------------------------------------------------------


class TestUpsertCypherClauseOrder:
    """E2E 实测教训锁 (2026-08-17): ON CREATE SET 必须紧跟 MERGE — 放在
    独立 SET 之后是 CypherSyntaxError。Story 1.5 原始写法即错, 因路由无
    调用方 + 单测 stub tx.run, 从未被真实 Neo4j 校验; stub 测不了语法,
    用子句顺序锁住防回退。"""

    @pytest.mark.asyncio
    async def test_upsert_node_on_create_precedes_standalone_set(self) -> None:
        calls = await _run_single_op(entity_type="node", operation="create", group_id=PHYSICAL_GID_A)
        q = _norm(calls[0]["query"])
        assert q.index("ON CREATE SET") < q.index("SET n.title")

    @pytest.mark.asyncio
    async def test_upsert_edge_on_create_precedes_standalone_set(self) -> None:
        calls = await _run_single_op(entity_type="edge", operation="create", group_id=PHYSICAL_GID_A)
        q = _norm(calls[0]["query"])
        assert q.index("ON CREATE SET") < q.index("SET e.label")

    @pytest.mark.asyncio
    async def test_upsert_board_on_create_precedes_standalone_set(self) -> None:
        calls = await _run_single_op(entity_type="board", operation="create", group_id=PHYSICAL_GID_A)
        q = _norm(calls[0]["query"])
        assert q.index("ON CREATE SET") < q.index("SET b.name")


# ---------------------------------------------------------------------------
# 3: 双 vault 场景 — 同 entity_id 不同 group 参数互不相同
# ---------------------------------------------------------------------------


class TestDualVaultIsolation:
    """同 entity_id 在两个 vault 下的操作, 绑定参数必须互不相同."""

    @pytest.mark.asyncio
    async def test_same_entity_id_upsert_binds_distinct_groups(self) -> None:
        calls_a = await _run_single_op(
            entity_type="node",
            operation="create",
            group_id=PHYSICAL_GID_A,
            entity_id="n-shared",
        )
        calls_b = await _run_single_op(
            entity_type="node",
            operation="create",
            group_id=PHYSICAL_GID_B,
            entity_id="n-shared",
        )
        assert calls_a[0]["kwargs"]["entity_id"] == calls_b[0]["kwargs"]["entity_id"]
        assert calls_a[0]["kwargs"]["group_id"] != calls_b[0]["kwargs"]["group_id"], (
            "同 entity_id 不同 vault 的 upsert 必须绑定不同 group_id"
        )

    @pytest.mark.asyncio
    async def test_same_entity_id_delete_binds_distinct_groups(self) -> None:
        """vault A 删 n-shared 不得波及 vault B 的 n-shared."""
        calls_a = await _run_single_op(
            entity_type="node",
            operation="delete",
            group_id=PHYSICAL_GID_A,
            entity_id="n-shared",
        )
        calls_b = await _run_single_op(
            entity_type="node",
            operation="delete",
            group_id=PHYSICAL_GID_B,
            entity_id="n-shared",
        )
        assert calls_a[0]["kwargs"]["group_id"] == PHYSICAL_GID_A
        assert calls_b[0]["kwargs"]["group_id"] == PHYSICAL_GID_B

    @pytest.mark.asyncio
    async def test_same_board_id_delete_binds_distinct_groups(self) -> None:
        """跨 vault 同 id board 的级联删除参数互不相同 (Codex 场景)."""
        calls_a = await _run_single_op(
            entity_type="board",
            operation="delete",
            group_id=PHYSICAL_GID_A,
            entity_id="b-shared",
        )
        calls_b = await _run_single_op(
            entity_type="board",
            operation="delete",
            group_id=PHYSICAL_GID_B,
            entity_id="b-shared",
        )
        assert calls_a[0]["kwargs"]["group_id"] != calls_b[0]["kwargs"]["group_id"]


# ---------------------------------------------------------------------------
# 5: endpoint 层 — vault_id → 物理 group_id 注入 service
# ---------------------------------------------------------------------------


class TestEndpointPhysicalGroupInjection:
    """POST /sync/batch: vault_id 必须被解析成物理格式 group_id 并绑进 Cypher.

    防两类回归: (a) handler 调 resolve 后丢弃返回值 (缺陷原状);
    (b) 传了逻辑格式 vault:x 忘过 to_physical_group_id (假隔离)。
    """

    def test_vault_id_reaches_cypher_as_physical_group(self, monkeypatch) -> None:
        from fastapi.testclient import TestClient

        from app.config import Settings, get_settings
        from app.main import app
        from app.services import sync_service as sync_service_module

        session = _StubSession()
        svc = sync_service_module.get_sync_service()
        monkeypatch.setattr(svc, "_driver", _StubDriver(session))

        def _settings() -> Settings:
            return Settings(
                PROJECT_NAME="Test",
                VERSION="1.0.0-test",
                DEBUG=True,
                LOG_LEVEL="DEBUG",
                CORS_ORIGINS="http://localhost:3000",
                CANVAS_BASE_PATH="./test_canvas",
                INTERNAL_API_KEY="tk",
            )

        app.dependency_overrides[get_settings] = _settings
        try:
            with TestClient(app) as client:
                response = client.post(
                    "/api/v1/sync/batch",
                    json={
                        "canvas_id": "c1",
                        "vault_id": "canvas_vault",
                        "operations": [
                            {
                                "operation_id": "op-e2e-1",
                                "entity_type": "node",
                                "entity_id": "n1",
                                "operation": "create",
                                "payload": {"title": "t", "content": "c"},
                                "timestamp": "2026-08-17T00:00:00Z",
                            }
                        ],
                    },
                    headers={"X-CLS-Internal-Key": "tk"},
                )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200
        calls = _all_run_calls(session)
        assert len(calls) == 1, "预期恰好一条 node upsert Cypher"
        # vault_id=canvas_vault → vault:canvas_vault → 物理 vault__canvas_vault
        assert calls[0]["kwargs"]["group_id"] == "vault__canvas_vault"
        assert "group_id: $group_id" in _norm(calls[0]["query"])
