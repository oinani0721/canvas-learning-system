"""Phase 1 (GRAPHITI-NATIVE-MEMORY-2026-06-10): 结构化 Graphiti 写入适配器单测。

D2: 用户显式标注(批注/错误/关系原因/对话摘要)确定性写 :Entity/RELATES_TO,
零 LLM (不走 add_triplet — 实读 graphiti.py:1450-1568 证实其跑 LLM+2search)。
D8: writer 显式生成 embedding (save 纯持久化不自动 embed)。
D10: belief 版本链 = 统一入口、内部委托 graphiti_belief_service。
"""

from datetime import datetime, timezone

import pytest
from graphiti_core.edges import EntityEdge

import app.services.graphiti_structured_writer as w
from app.graphiti.identity_registry import IdentityRegistry

OCCURRED = datetime(2026, 6, 10, tzinfo=timezone.utc)


class FakeEmbedder:
    def __init__(self):
        self.calls = []

    async def create(self, input_data):
        self.calls.append(list(input_data))
        return [0.5, 0.5]


@pytest.fixture
def capture(monkeypatch):
    """捕获 EntityEdge.save + 替换身份层为确定性 fake。"""
    saved: list[EntityEdge] = []

    async def fake_save(self, driver):
        saved.append(self)

    async def fake_ensure(driver, node_id, sanitized_group_id, embedder=None, title=""):
        return f"uuid-{node_id}"

    monkeypatch.setattr(EntityEdge, "save", fake_save)
    monkeypatch.setattr(
        IdentityRegistry, "ensure_entity_node", staticmethod(fake_ensure)
    )
    return saved


# ═══════════════════════════════════════════════════════════════════════════════
# write_callout — 自环 SelfAnnotation
# ═══════════════════════════════════════════════════════════════════════════════


async def test_write_callout_self_loop_with_attributes(capture):
    edge = await w.write_callout(
        object(),
        None,
        node_id="recursion",
        group_id="vault:cs_61b:rec",
        callout_type="tip",
        text="先想 base case",
        occurred_at=OCCURRED,
    )
    assert capture == [edge]
    assert edge.source_node_uuid == edge.target_node_uuid == "uuid-recursion"  # 自环
    assert edge.name == "SelfAnnotation"
    assert edge.fact == "先想 base case"
    assert edge.group_id == "vault__cs_61b__rec"  # C-3 sanitize 真用
    assert edge.valid_at == OCCURRED and edge.invalid_at is None
    a = edge.attributes
    assert a["node_id"] == "recursion"
    assert a["source"] == "callout"
    assert a["event_type"] == "callout_added"
    assert a["callout_type"] == "tip"


async def test_write_callout_generates_embedding_d8(capture):
    embedder = FakeEmbedder()
    edge = await w.write_callout(
        object(),
        embedder,
        node_id="n",
        group_id="vault:g",
        callout_type="question",
        text="为什么?",
        occurred_at=OCCURRED,
    )
    assert edge.fact_embedding == [0.5, 0.5]  # D8: 显式生成
    assert len(embedder.calls) == 1


async def test_write_callout_no_embedder_no_embedding(capture):
    edge = await w.write_callout(
        object(),
        None,
        node_id="n",
        group_id="vault:g",
        callout_type="tip",
        text="t",
        occurred_at=OCCURRED,
    )
    assert edge.fact_embedding is None


# ═══════════════════════════════════════════════════════════════════════════════
# write_error — 自环 SelfMisconception
# ═══════════════════════════════════════════════════════════════════════════════


async def test_write_error_attributes(capture):
    edge = await w.write_error(
        object(),
        None,
        node_id="recursion",
        group_id="vault:g",
        error_type="knowledge_gap",
        description="忘了 base case",
        occurred_at=OCCURRED,
    )
    assert edge.name == "SelfMisconception"
    assert edge.attributes["source"] == "error"
    assert edge.attributes["event_type"] == "error_marked"
    assert edge.attributes["error_type"] == "knowledge_gap"
    assert edge.source_node_uuid == edge.target_node_uuid


# ═══════════════════════════════════════════════════════════════════════════════
# write_relation_reason — 真实 src→tgt
# ═══════════════════════════════════════════════════════════════════════════════


async def test_write_relation_reason_two_nodes(capture):
    edge = await w.write_relation_reason(
        object(),
        None,
        source_node_id="理性代理",
        target_node_id="lecture 2",
        group_id="vault:g",
        relation_type="related_to",
        reason="我对这个点没充分理解, 想单独讨论",
        occurred_at=OCCURRED,
    )
    assert edge.source_node_uuid == "uuid-理性代理"
    assert edge.target_node_uuid == "uuid-lecture 2"
    assert edge.fact == "我对这个点没充分理解, 想单独讨论"
    assert edge.attributes["source"] == "relation"
    assert edge.attributes["relation_type"] == "related_to"
    assert edge.attributes["node_id"] == "理性代理"  # 读侧按持有方 node 查


async def test_write_relation_reason_defaults_name(capture):
    edge = await w.write_relation_reason(
        object(),
        None,
        source_node_id="a",
        target_node_id="b",
        group_id="vault:g",
        relation_type=None,
        reason="r",
        occurred_at=OCCURRED,
    )
    assert edge.name == "RelatedTo"  # 兜底


# ═══════════════════════════════════════════════════════════════════════════════
# write_conversation_summary — 自环 (用户拍板: 归档时写摘要边)
# ═══════════════════════════════════════════════════════════════════════════════


async def test_write_conversation_summary(capture):
    edge = await w.write_conversation_summary(
        object(),
        None,
        node_id="recursion",
        group_id="vault:g",
        summary="用户起初混淆 base case, 3 轮后能自己推导",
        occurred_at=OCCURRED,
    )
    assert edge.name == "ConversationSummary"
    assert edge.attributes["source"] == "conversation"
    assert edge.attributes["event_type"] == "conversation_archived"
    assert edge.source_node_uuid == edge.target_node_uuid


# ═══════════════════════════════════════════════════════════════════════════════
# write_belief_version — D10 统一入口, 委托 belief 服务
# ═══════════════════════════════════════════════════════════════════════════════


async def test_write_belief_version_delegates(monkeypatch):
    received = {}

    async def fake_chain(graphiti, **kwargs):
        received.update(kwargs)
        return "EDGE"

    monkeypatch.setattr(
        "app.services.graphiti_belief_service.update_belief_version_chain", fake_chain
    )
    result = await w.write_belief_version(
        graphiti="G",
        belief_key="callout:n:abc",
        group_id="vault:g",
        fact="新版本",
        occurred_at=OCCURRED,
        node_id="n",
    )
    assert result == "EDGE"
    assert received["belief_key"] == "callout:n:abc"
    assert received["node_id"] == "n"


# ═══════════════════════════════════════════════════════════════════════════════
# 幂等性 (Phase 4.5 回填前置): 同内容→同 uuid (save MERGE 不重复), 改内容→新边
# ═══════════════════════════════════════════════════════════════════════════════


async def test_same_callout_same_uuid_idempotent(capture):
    kw = dict(
        node_id="n",
        group_id="vault:g",
        callout_type="tip",
        text="同一条批注",
        occurred_at=OCCURRED,
    )
    e1 = await w.write_callout(object(), None, **kw)
    e2 = await w.write_callout(object(), None, **kw)
    assert e1.uuid == e2.uuid  # MERGE on uuid → 重跑回填不重复


async def test_changed_text_new_uuid_accretion(capture):
    e1 = await w.write_callout(
        object(),
        None,
        node_id="n",
        group_id="vault:g",
        callout_type="tip",
        text="v1",
        occurred_at=OCCURRED,
    )
    e2 = await w.write_callout(
        object(),
        None,
        node_id="n",
        group_id="vault:g",
        callout_type="tip",
        text="v2",
        occurred_at=OCCURRED,
    )
    assert e1.uuid != e2.uuid  # 新内容=新边 (累积模型)
