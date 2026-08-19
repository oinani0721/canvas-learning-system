"""P1-05c B2 (Codex 三轮 F-02/F-03) — 墓碑与隔离的读侧闭合契约。

F-02: canvas_projection_sync 写的软失效墓碑 (invalidated_at + active=false)
此前在 3 文件 5 条当前态 Cypher 中不被过滤 — 幽灵边持续参与 kg_relevance
打分、把孤立节点误判为已连接、给标签建议池供料。本文件锁: 四个读侧模块中
每条含 CANVAS_EDGE 的 MATCH 查询都必须带 `invalidated_at IS NULL`。

F-03: graphiti_core 的 EntityEdge.get_by_node_uuid 按端点 UUID 取边**不查
边的 group_id** — 隔离组 (quarantine__*) 的边会被原主组的精确读取回。
锁: _node_uuid_and_active_edges 必须丢弃与请求组不一致的边。
"""

from __future__ import annotations

import inspect
import re
from datetime import datetime, timezone

import pytest

# ── F-02: CANVAS_EDGE 读侧查询源码级契约 ────────────────────────────────────


def _canvas_edge_match_queries(module) -> list[str]:
    """模块源码里所有含 CANVAS_EDGE 的 MATCH 查询字符串 (排除 docstring 噪音)。"""
    src = inspect.getsource(module)
    return [s for s in re.findall(r'"""(.*?)"""', src, re.S) if "CANVAS_EDGE" in s and "MATCH" in s]


def _read_side_modules():
    from app.services import (
        question_generator,
        recommendation_service,
        targeting_material_service,
        verification_service,
    )

    return [
        pytest.param(question_generator, id="question_generator"),
        pytest.param(verification_service, id="verification_service"),
        pytest.param(recommendation_service, id="recommendation_service"),
        pytest.param(targeting_material_service, id="targeting_material_service"),
    ]


@pytest.mark.parametrize("mod", _read_side_modules())
def test_canvas_edge_read_queries_filter_tombstones(mod):
    """四个读侧模块的每条 CANVAS_EDGE MATCH 查询必须过滤墓碑。

    写路径 (MERGE / SET invalidated_at 对账) 豁免 — 它们在
    canvas_projection_sync / sync_service / exam_service_ext, 不在本参数化内。
    """
    queries = _canvas_edge_match_queries(mod)
    assert queries, f"{mod.__name__} 未找到 CANVAS_EDGE 查询 — 契约面漂移, 请更新本测试"
    for q in queries:
        assert "invalidated_at IS NULL" in q, (
            f"{mod.__name__} 存在未过滤墓碑的 CANVAS_EDGE 读查询 (F-02 回归):\n{q[:300]}"
        )


# ── F-03: 精确 reader 跨组拒绝 ──────────────────────────────────────────────


def _mk_edge(gid: str, fact: str, node_id: str = "n1", invalid=None):
    from graphiti_core.edges import EntityEdge

    now = datetime.now(timezone.utc)
    return EntityEdge(
        uuid=f"test-{gid}-{fact[:8]}",
        group_id=gid,
        source_node_uuid="node-uuid",
        target_node_uuid="node-uuid",
        created_at=now,
        valid_at=now,
        invalid_at=invalid,
        name="callout",
        fact=fact,
        attributes={"source": "callout", "node_id": node_id},
    )


@pytest.mark.asyncio
async def test_reader_drops_edges_from_other_groups(monkeypatch):
    """read_node_tips 以主组身份读取时, 隔离组 (quarantine__*) 的边必须被丢弃。

    真实事故形状 (Codex 三轮 F-03 实测): 隔离脚本只改边 group_id, 但
    get_by_node_uuid 按端点 UUID 匹配 → 主组身份读回隔离边 fact。
    注入层是 graphiti_core 的类方法 (返回真实 EntityEdge 实例, 非 mock 数据
    形状) — 过滤逻辑本体真实执行。
    """
    import app.services.graphiti_memory_reader as reader

    main_gid = "vault__canvas_vault"
    edges = [
        _mk_edge(main_gid, "主组批注-应保留"),
        _mk_edge("quarantine__p105b", "隔离批注-不得读回"),
        _mk_edge("vault__other_vault", "跨vault批注-不得读回"),
    ]

    async def fake_get_by_node_uuid(driver, uuid):
        return list(edges)

    monkeypatch.setattr(reader.EntityEdge, "get_by_node_uuid", staticmethod(fake_get_by_node_uuid))

    tips = await reader.read_node_tips(None, "n1", group_id="vault:canvas_vault")

    assert tips == ["主组批注-应保留"], f"跨组边泄入精确读: {tips}"


@pytest.mark.asyncio
async def test_reader_still_filters_invalid_at(monkeypatch):
    """组校验不得弄丢原有的 invalid_at 过滤 (D9 active-only 语义)。"""
    import app.services.graphiti_memory_reader as reader

    main_gid = "vault__canvas_vault"
    now = datetime.now(timezone.utc)
    edges = [
        _mk_edge(main_gid, "活边"),
        _mk_edge(main_gid, "失效边", invalid=now),
    ]

    async def fake_get_by_node_uuid(driver, uuid):
        return list(edges)

    monkeypatch.setattr(reader.EntityEdge, "get_by_node_uuid", staticmethod(fake_get_by_node_uuid))

    tips = await reader.read_node_tips(None, "n1", group_id="vault:canvas_vault")

    assert tips == ["活边"]


# ── P1-05d C3 (Codex 四轮 V6/V7): 组闭环 ────────────────────────────────────


@pytest.mark.asyncio
async def test_conversation_summary_caller_passes_vault_group(monkeypatch):
    """V6: 全仓唯一生产 caller 曾不传组 → 回落 vault:default 与写侧
    (active-vault 组) uuid5 错位, 真实链路恒空。锁: caller 必须显式传当前 vault 组。"""
    from app.services.question_generator import QuestionGenerator

    captured: dict = {}

    async def fake_reader(driver, node_id, group_id=None):
        captured["group_id"] = group_id
        return "摘要"

    import app.services.graphiti_memory_reader as reader_mod

    monkeypatch.setattr(reader_mod, "read_node_conversation_summary", fake_reader)
    monkeypatch.setattr("app.config.get_current_vault_id", lambda: "canvas_vault")

    qg = QuestionGenerator.__new__(QuestionGenerator)
    monkeypatch.setattr(qg, "_graphiti_driver", lambda: object(), raising=False)

    result = await qg._get_conversation_summary("n1")

    assert result == "摘要"
    assert captured["group_id"] is not None, "caller 仍不传组 (V6 回归) — 会回落 vault:default"
    assert "canvas_vault" in str(captured["group_id"])


@pytest.mark.asyncio
async def test_ensure_entity_node_rejects_quarantined_identity(monkeypatch):
    """V7: 隔离只改节点 group_id 不重键 uuid, ensure_entity_node 命中后曾不核对
    当前组 → 原组写入复用已隔离节点重建跨组拓扑。锁: quarantine__* 组拒绝复用。"""
    from types import SimpleNamespace

    from app.graphiti.identity_registry import IdentityRegistry

    async def fake_get_by_uuid(driver, uuid):
        return SimpleNamespace(uuid=uuid, group_id="quarantine__p105b")

    from graphiti_core.nodes import EntityNode

    monkeypatch.setattr(EntityNode, "get_by_uuid", staticmethod(fake_get_by_uuid))

    with pytest.raises(ValueError, match="隔离"):
        await IdentityRegistry.ensure_entity_node(None, "污染节点", "vault__canvas_vault")


@pytest.mark.asyncio
async def test_ensure_entity_node_same_group_still_reuses(monkeypatch):
    """正向对照: 同组命中照常复用 uuid (防御不能焊死正门)。"""
    from types import SimpleNamespace

    from app.graphiti.identity_registry import IdentityRegistry, entity_uuid_for_node

    async def fake_get_by_uuid(driver, uuid):
        return SimpleNamespace(uuid=uuid, group_id="vault__canvas_vault")

    from graphiti_core.nodes import EntityNode

    monkeypatch.setattr(EntityNode, "get_by_uuid", staticmethod(fake_get_by_uuid))

    uuid = await IdentityRegistry.ensure_entity_node(None, "正常节点", "vault__canvas_vault")

    assert uuid == entity_uuid_for_node("正常节点", "vault__canvas_vault")
