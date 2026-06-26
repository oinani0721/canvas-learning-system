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
    from graphiti_core.errors import EdgeNotFoundError

    saved: list[EntityEdge] = []

    async def fake_save(self, driver):
        saved.append(self)

    async def fake_ensure(driver, node_id, sanitized_group_id, embedder=None, title=""):
        return f"uuid-{node_id}"

    async def fake_get_by_uuid(driver, uuid):
        # 默认: 边不存在 → _preserved_times 用 occurred_at (新边语义)
        raise EdgeNotFoundError(uuid)

    monkeypatch.setattr(EntityEdge, "save", fake_save)
    monkeypatch.setattr(
        IdentityRegistry, "ensure_entity_node", staticmethod(fake_ensure)
    )
    monkeypatch.setattr(EntityEdge, "get_by_uuid", staticmethod(fake_get_by_uuid))
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
    assert edge.fact == "[tip] 先想 base case"  # 规范格式 (无 understanding)
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


# ═══════════════════════════════════════════════════════════════════════════════
# 去重修复 (2026-06-13): 规范 fact + 逻辑身份 (节点+批注首行) — 三通道合一
# ═══════════════════════════════════════════════════════════════════════════════


async def test_canonical_fact_format(capture):
    """writer 持有唯一格式: [类型·理解度] 裸文本 — 调用方不再各自包装。"""
    edge = await w.write_callout(
        object(),
        None,
        node_id="n",
        group_id="vault:g",
        callout_type="tips",
        understanding="fuzzy",
        text="一个代理是实体\n✍️ 我的理解：还不太懂",
        occurred_at=OCCURRED,
    )
    assert edge.fact == "[tips·fuzzy] 一个代理是实体\n✍️ 我的理解：还不太懂"


async def test_identity_by_first_line_versions_collapse(capture):
    """同一批注的不同版本(选中→续写全文) → 同 uuid → MERGE 原地升级, 不并排。"""
    e1 = await w.write_callout(
        object(),
        None,
        node_id="n",
        group_id="vault:g",
        callout_type="tips",
        understanding="fuzzy",
        text="一个代理是实体",  # 即时上报: 仅选中
        occurred_at=OCCURRED,
    )
    e2 = await w.write_callout(
        object(),
        None,
        node_id="n",
        group_id="vault:g",
        callout_type="tips",
        understanding="fuzzy",
        text="一个代理是实体\n✍️ 我的理解：还不太懂",  # 停笔同步: 全文
        occurred_at=OCCURRED,
    )
    assert e1.uuid == e2.uuid  # 首行相同 = 同一条批注 → 覆盖升级


async def test_different_annotations_different_identity(capture):
    """新批注(不同选中文本) → 新身份 → 累积模型不受影响。"""
    e1 = await w.write_callout(
        object(),
        None,
        node_id="n",
        group_id="vault:g",
        callout_type="tips",
        understanding=None,
        text="批注A",
        occurred_at=OCCURRED,
    )
    e2 = await w.write_callout(
        object(),
        None,
        node_id="n",
        group_id="vault:g",
        callout_type="tips",
        understanding=None,
        text="批注B",
        occurred_at=OCCURRED,
    )
    assert e1.uuid != e2.uuid


# ═══════════════════════════════════════════════════════════════════════════════
# P0 (A+-prime 2026-06-26): 稳定 annotation_id 作身份 — 改正文不换身份, 同首行不碰撞
# ═══════════════════════════════════════════════════════════════════════════════


async def test_annotation_id_is_identity_over_content(capture):
    """同 annotation_id + 改正文 → 同 uuid (改批注不产生孤儿边)。"""
    kw = dict(
        node_id="n",
        group_id="vault:g",
        callout_type="tips",
        annotation_id="cb-abc123",
        occurred_at=OCCURRED,
    )
    e1 = await w.write_callout(object(), None, text="初版理解", **kw)
    e2 = await w.write_callout(object(), None, text="修订后的全新正文", **kw)
    assert e1.uuid == e2.uuid  # 身份由 id 定, 不由内容定 → MERGE 原地升级
    assert e2.attributes["annotation_id"] == "cb-abc123"


async def test_same_first_line_different_id_no_collision(capture):
    """同节点同一句原文的两条不同批注 (不同 id) → 不同 uuid (A1 碰撞已修)。"""
    e1 = await w.write_callout(
        object(),
        None,
        node_id="n",
        group_id="vault:g",
        callout_type="tips",
        annotation_id="cb-first0",
        text="一个代理是实体\n✍️ 我从定义角度不懂",
        occurred_at=OCCURRED,
    )
    e2 = await w.write_callout(
        object(),
        None,
        node_id="n",
        group_id="vault:g",
        callout_type="tips",
        annotation_id="cb-second",
        text="一个代理是实体\n✍️ 我从行动角度不懂",
        occurred_at=OCCURRED,
    )
    assert e1.uuid != e2.uuid  # 首行相同但 id 不同 → 两条独立批注, 不再合并


async def test_no_annotation_id_falls_back_to_first_line(capture):
    """无 id 的历史批注 → 回退首行身份 (向后兼容)。"""
    e1 = await w.write_callout(
        object(),
        None,
        node_id="n",
        group_id="vault:g",
        callout_type="tips",
        text="同一句\n版本1",
        occurred_at=OCCURRED,
    )
    e2 = await w.write_callout(
        object(),
        None,
        node_id="n",
        group_id="vault:g",
        callout_type="tips",
        text="同一句\n版本2",
        occurred_at=OCCURRED,
    )
    assert e1.uuid == e2.uuid  # 无 id 时首行相同仍合并 (旧行为不变)


# ═══════════════════════════════════════════════════════════════════════════════
# P3 (A4 2026-06-26): create-or-preserve — 边已存在保留原始时间, 防回填覆写
# ═══════════════════════════════════════════════════════════════════════════════


async def test_new_edge_uses_occurred_at(capture):
    """边不存在(EdgeNotFoundError) → valid_at/created_at = occurred_at (源事件时间)。"""
    edge = await w.write_callout(
        object(),
        None,
        node_id="n",
        group_id="vault:g",
        callout_type="tips",
        annotation_id="cb-new",
        text="新批注",
        occurred_at=OCCURRED,
    )
    assert edge.valid_at == OCCURRED and edge.created_at == OCCURRED


async def test_existing_edge_preserves_original_time(capture, monkeypatch):
    """边已存在 → 保留其原始时间, 即使回填传入更晚的 occurred_at (A4 根治)。"""
    old = datetime(2026, 1, 1, tzinfo=timezone.utc)

    class _Existing:
        created_at = old
        valid_at = old

    async def fake_get(driver, uuid):
        return _Existing()

    monkeypatch.setattr(EntityEdge, "get_by_uuid", staticmethod(fake_get))
    backfill_time = datetime(2026, 6, 26, tzinfo=timezone.utc)
    edge = await w.write_callout(
        object(),
        None,
        node_id="n",
        group_id="vault:g",
        callout_type="tips",
        annotation_id="cb-existing",
        text="回填重写",
        occurred_at=backfill_time,
    )
    # 回填时刻 6-26 被丢弃, 保留原始 1-1 → 时序不被污染
    assert edge.valid_at == old and edge.created_at == old


async def test_relation_reason_preserves_existing_time(capture, monkeypatch):
    """write_relation_reason 同样 create-or-preserve。"""
    old = datetime(2026, 2, 2, tzinfo=timezone.utc)

    class _Existing:
        created_at = old
        valid_at = old

    async def fake_get(driver, uuid):
        return _Existing()

    monkeypatch.setattr(EntityEdge, "get_by_uuid", staticmethod(fake_get))
    edge = await w.write_relation_reason(
        object(),
        None,
        source_node_id="a",
        target_node_id="b",
        group_id="vault:g",
        relation_type="refines",
        reason="原因",
        occurred_at=datetime(2026, 6, 26, tzinfo=timezone.utc),
    )
    assert edge.valid_at == old and edge.created_at == old
