"""Phase 3 (GRAPHITI-NATIVE-MEMORY-2026-06-10): Graphiti 精确读 reader 单测。

D5: node_id → entity_uuid → EntityEdge.get_by_node_uuid → 属性过滤。
D9 (ChatGPT 计划审查):
  - active-only: invalid_at is None (排除 belief 链 supersede 的旧版)
  - 方向过滤: relation 边只取 source==本节点 (get_by_node_uuid 是 undirected,
    edges.py:535 — 不滤会把"别人为什么连到我"也混进来, 与旧出边行为不等价)
"""

from datetime import datetime, timezone

import pytest
from graphiti_core.edges import EntityEdge

import app.services.graphiti_memory_reader as r
from app.graphiti.group_id_compat import sanitize_group_id_for_graphiti
from app.graphiti.identity_registry import entity_uuid_for_node

GID = "vault:cs_61b:rec"
NODE = "recursion"
T = datetime(2026, 6, 1, tzinfo=timezone.utc)
T2 = datetime(2026, 6, 5, tzinfo=timezone.utc)

MY_UUID = entity_uuid_for_node(NODE, sanitize_group_id_for_graphiti(GID))


def _edge(
    *,
    fact,
    source,
    src=MY_UUID,
    tgt=MY_UUID,
    invalid_at=None,
    valid_at=T,
    **extra_attrs,
):
    return EntityEdge(
        group_id=sanitize_group_id_for_graphiti(GID),
        source_node_uuid=src,
        target_node_uuid=tgt,
        created_at=valid_at,
        valid_at=valid_at,
        invalid_at=invalid_at,
        name="X",
        fact=fact,
        attributes={"node_id": NODE, "source": source, **extra_attrs},
    )


@pytest.fixture
def edges_store(monkeypatch):
    store: list[EntityEdge] = []

    async def fake_get_by_node_uuid(cls, driver, node_uuid):
        # 复刻 undirected 语义: 返回 incident 于该 uuid 的全部边
        return [
            e for e in store if node_uuid in (e.source_node_uuid, e.target_node_uuid)
        ]

    monkeypatch.setattr(
        EntityEdge, "get_by_node_uuid", classmethod(fake_get_by_node_uuid)
    )
    return store


# ═══════════════════════════════════════════════════════════════════════════════
# read_node_tips — source=callout + active-only
# ═══════════════════════════════════════════════════════════════════════════════


async def test_read_tips_filters_source_and_active(edges_store):
    edges_store.extend(
        [
            _edge(fact="先想 base case", source="callout"),
            _edge(
                fact="旧版批注", source="callout", invalid_at=T2
            ),  # superseded → 排除
            _edge(fact="错误记录", source="error"),  # 非 callout → 排除
        ]
    )
    tips = await r.read_node_tips(object(), NODE, group_id=GID)
    assert tips == ["先想 base case"]


async def test_read_tips_empty_when_node_unknown(edges_store):
    tips = await r.read_node_tips(object(), "ghost-node", group_id=GID)
    assert tips == []


# ═══════════════════════════════════════════════════════════════════════════════
# read_node_errors — source=error, 形状对齐旧 _get_error_history
# ═══════════════════════════════════════════════════════════════════════════════


async def test_read_errors_shape(edges_store):
    edges_store.append(
        _edge(fact="忘了 base case", source="error", error_type="knowledge_gap")
    )
    errors = await r.read_node_errors(object(), NODE, group_id=GID)
    assert errors == [{"error_type": "knowledge_gap", "description": "忘了 base case"}]


# ═══════════════════════════════════════════════════════════════════════════════
# read_node_edge_reasons — D9 方向过滤 (只取出边)
# ═══════════════════════════════════════════════════════════════════════════════


async def test_read_edge_reasons_direction_filter(edges_store):
    other = entity_uuid_for_node("lecture 2", sanitize_group_id_for_graphiti(GID))
    edges_store.extend(
        [
            _edge(
                fact="我为此拉出节点", source="relation", src=MY_UUID, tgt=other
            ),  # 出边 ✓
            _edge(
                fact="别人连到我的原因", source="relation", src=other, tgt=MY_UUID
            ),  # 入边 ✗
        ]
    )
    reasons = await r.read_node_edge_reasons(object(), NODE, group_id=GID)
    assert reasons == ["我为此拉出节点"]  # 对齐旧 _get_edge_reasons 只查出边


# ═══════════════════════════════════════════════════════════════════════════════
# read_node_conversation_summary — 最新一条 (对齐旧 ORDER BY created_at DESC LIMIT 1)
# ═══════════════════════════════════════════════════════════════════════════════


async def test_read_conversation_summary_latest(edges_store):
    edges_store.extend(
        [
            _edge(fact="旧摘要", source="conversation", valid_at=T),
            _edge(fact="新摘要", source="conversation", valid_at=T2),
        ]
    )
    summary = await r.read_node_conversation_summary(object(), NODE, group_id=GID)
    assert summary == "新摘要"


async def test_read_conversation_summary_empty(edges_store):
    summary = await r.read_node_conversation_summary(object(), NODE, group_id=GID)
    assert summary == ""
