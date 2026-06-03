"""
5-ge-2 单元测试: belief 时序版本链 (用有状态 FakeEdgeStore)。

覆盖 AC#7:
  - 同一 belief_key 写入 3 次 → 3 个 EntityEdge, 前 2 个 invalid_at != None,
    最新 status=active; 且 edges[0].invalid_at == edges[1].valid_at
  - get_belief_history(as_of=2 天前) → 返回当时 active(v1), current 仍是 v3
  - use_bulk=True → 抛 ValueError (add_episode_bulk 不做 invalidation)

不连真实 Neo4j: monkeypatch driver 接缝 (_find_*_edges_by_belief_key /
_ensure_entity_node / _ensure_belief_key_index) + EntityEdge.save 到 FakeEdgeStore。
"""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from graphiti_core.edges import EntityEdge

import app.services.graphiti_belief_service as bs

T1 = datetime(2026, 6, 1, tzinfo=timezone.utc)
T2 = datetime(2026, 6, 3, tzinfo=timezone.utc)
T3 = datetime(2026, 6, 5, tzinfo=timezone.utc)

BK = "callout:recursion-base-case:abc123"


class FakeEdgeStore:
    """有状态内存边库, 复刻 Neo4j RELATES_TO + belief_key 属性语义。"""

    def __init__(self):
        self.edges: list[EntityEdge] = []

    def active(self, belief_key: str) -> list[EntityEdge]:
        return [
            e
            for e in self.edges
            if (e.attributes or {}).get("belief_key") == belief_key
            and (e.attributes or {}).get("status") == "active"
            and e.invalid_at is None
        ]

    def all(self, belief_key: str) -> list[EntityEdge]:
        return [
            e
            for e in self.edges
            if (e.attributes or {}).get("belief_key") == belief_key
        ]

    def save(self, edge: EntityEdge) -> None:
        for i, e in enumerate(self.edges):
            if e.uuid == edge.uuid:
                self.edges[i] = edge
                return
        self.edges.append(edge)


@pytest.fixture
def store_and_graphiti(monkeypatch):
    store = FakeEdgeStore()

    async def fake_active(driver, group_id, belief_key):
        return store.active(belief_key)

    async def fake_all(driver, group_id, belief_key):
        return store.all(belief_key)

    async def fake_ensure_node(graphiti, node_name, group_id):
        return f"node-uuid-{node_name}"

    async def fake_index(driver):
        return None

    async def fake_save(self, driver):
        store.save(self)
        return {"uuid": self.uuid}

    monkeypatch.setattr(bs, "_find_active_edges_by_belief_key", fake_active)
    monkeypatch.setattr(bs, "_find_all_edges_by_belief_key", fake_all)
    monkeypatch.setattr(bs, "_ensure_entity_node", fake_ensure_node)
    monkeypatch.setattr(bs, "_ensure_belief_key_index", fake_index)
    monkeypatch.setattr(EntityEdge, "save", fake_save)

    graphiti = SimpleNamespace(driver=SimpleNamespace(provider="neo4j"))
    return store, graphiti


async def _write(graphiti, *, fact, occurred_at):
    return await bs.update_belief_version_chain(
        graphiti,
        belief_key=BK,
        group_id="vault:cs_61b:recursion",
        fact=fact,
        occurred_at=occurred_at,
        node_id="recursion-base-case",
        source="callout",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# AC#7 case 1 — 3 次写入 → 版本链
# ═══════════════════════════════════════════════════════════════════════════════


async def test_three_writes_build_version_chain(store_and_graphiti):
    store, graphiti = store_and_graphiti

    await _write(graphiti, fact="v1: 先想 base case", occurred_at=T1)
    await _write(graphiti, fact="v2: base case 要返回", occurred_at=T2)
    await _write(graphiti, fact="v3: base case 必须可达", occurred_at=T3)

    edges = sorted(store.edges, key=lambda e: e.valid_at)
    assert len(edges) == 3, "同一 belief_key 写 3 次应有 3 条边"

    # 前 2 条被 supersede (invalid_at 已设)
    assert edges[0].invalid_at is not None
    assert edges[1].invalid_at is not None
    assert edges[0].attributes["status"] == "superseded"
    assert edges[1].attributes["status"] == "superseded"

    # 旧边 invalid_at == 下一版 valid_at (时序无缝衔接)
    assert edges[0].invalid_at == edges[1].valid_at
    assert edges[1].invalid_at == edges[2].valid_at

    # 最新一条仍 active 且未失效
    assert edges[2].invalid_at is None
    assert edges[2].attributes["status"] == "active"
    assert edges[2].fact == "v3: base case 必须可达"

    # 只有 1 条 active
    assert len(store.active(BK)) == 1


# ═══════════════════════════════════════════════════════════════════════════════
# AC#7 case 2 — get_belief_history as_of 时序回溯
# ═══════════════════════════════════════════════════════════════════════════════


async def test_get_belief_history_as_of_returns_then_active(store_and_graphiti):
    store, graphiti = store_and_graphiti

    await _write(graphiti, fact="v1", occurred_at=T1)
    await _write(graphiti, fact="v2", occurred_at=T2)
    await _write(graphiti, fact="v3", occurred_at=T3)

    # as_of = v1 与 v2 之间 (v1 当时有效)
    as_of = T2 - timedelta(days=1)
    history = await bs.get_belief_history(
        graphiti, BK, "vault:cs_61b:recursion", as_of=as_of
    )

    assert len(history) == 3
    # 按 valid_at 升序
    assert [h["fact"] for h in history] == ["v1", "v2", "v3"]

    # as_of 时刻有效的是 v1
    as_of_active = [h for h in history if h["active_at_as_of"]]
    assert len(as_of_active) == 1
    assert as_of_active[0]["fact"] == "v1"

    # 但 current 仍是 v3 (最新 active)
    current = [h for h in history if h["current"]]
    assert len(current) == 1
    assert current[0]["fact"] == "v3"


async def test_get_belief_history_marks_single_current(store_and_graphiti):
    store, graphiti = store_and_graphiti
    await _write(graphiti, fact="only", occurred_at=T1)
    history = await bs.get_belief_history(graphiti, BK, "vault:cs_61b:recursion")
    assert len(history) == 1
    assert history[0]["current"] is True
    assert history[0]["status"] == "active"


# ═══════════════════════════════════════════════════════════════════════════════
# AC#7 case 3 — use_bulk 违规抛错
# ═══════════════════════════════════════════════════════════════════════════════


async def test_use_bulk_raises_value_error(store_and_graphiti):
    store, graphiti = store_and_graphiti
    with pytest.raises(ValueError, match="bulk"):
        await bs.update_belief_version_chain(
            graphiti,
            belief_key=BK,
            group_id="vault:cs_61b:recursion",
            fact="x",
            occurred_at=T1,
            node_id="recursion-base-case",
            use_bulk=True,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# 关系边 (非自环) + BeliefKeyResolver
# ═══════════════════════════════════════════════════════════════════════════════


async def test_relation_edge_uses_two_distinct_nodes(store_and_graphiti):
    store, graphiti = store_and_graphiti
    edge = await bs.update_belief_version_chain(
        graphiti,
        belief_key="edge:recursion:prerequisite:base-case",
        group_id="vault:cs_61b:recursion",
        fact="recursion 需要先懂 base-case",
        occurred_at=T1,
        source_node_id="recursion",
        target_node_id="base-case",
        relation_type="prerequisite",
        source="frontmatter",
    )
    assert edge.source_node_uuid == "node-uuid-recursion"
    assert edge.target_node_uuid == "node-uuid-base-case"
    assert edge.name == "Prerequisite"  # edge_name_for_relation("prerequisite")
    assert edge.source_node_uuid != edge.target_node_uuid


def test_belief_key_resolver_patterns():
    r = bs.BeliefKeyResolver
    assert r.make_edge_belief_key("a", "prerequisite", "b") == "edge:a:prerequisite:b"
    assert r.make_calibration_belief_key("q1", "v2") == "calib:q1:v2"
    assert r.make_error_belief_key("n1", "knowledge_gap") == "error:n1:knowledge_gap"
    ck = r.make_callout_belief_key("n1", "节点/n1.md", 42)
    assert ck.startswith("callout:n1:") and len(ck.split(":")[-1]) == 16


async def test_self_loop_edge_name_from_belief_key(store_and_graphiti):
    store, graphiti = store_and_graphiti
    edge = await bs.update_belief_version_chain(
        graphiti,
        belief_key="error:recursion-base-case:knowledge_gap",
        group_id="vault:cs_61b:recursion",
        fact="忘了 base case",
        occurred_at=T1,
        node_id="recursion-base-case",
    )
    assert edge.name == "SelfMisconception"
    assert edge.source_node_uuid == edge.target_node_uuid  # 自环


# ═══════════════════════════════════════════════════════════════════════════════
# 审查 M1 回归 — naive/aware datetime 混用不崩溃
# ═══════════════════════════════════════════════════════════════════════════════


async def test_naive_occurred_at_normalized_does_not_crash(store_and_graphiti):
    """M1: 调用方传 naive datetime 也不能让 get_belief_history 排序/比较崩溃。"""
    store, graphiti = store_and_graphiti
    naive_t1 = datetime(2026, 6, 1)  # 无 tzinfo
    aware_t2 = datetime(2026, 6, 3, tzinfo=timezone.utc)

    await _write(graphiti, fact="v1 (naive 写入)", occurred_at=naive_t1)
    await _write(graphiti, fact="v2 (aware 写入)", occurred_at=aware_t2)

    # 写入端已归一化 → 所有 valid_at 都 aware
    for e in store.edges:
        assert e.valid_at.tzinfo is not None, "occurred_at 应被归一化为 aware"

    # 混用场景下 get_belief_history 不抛 TypeError
    history = await bs.get_belief_history(
        graphiti,
        BK,
        "vault:cs_61b:recursion",
        as_of=datetime(2026, 6, 2, tzinfo=timezone.utc),
    )
    assert len(history) == 2
    as_of_active = [h for h in history if h["active_at_as_of"]]
    assert len(as_of_active) == 1 and as_of_active[0]["fact"] == "v1 (naive 写入)"


async def test_get_belief_history_defensive_against_naive_stored(store_and_graphiti):
    """M1 防御: 即便库里混进 naive valid_at (历史数据), 查询也不崩。"""
    store, graphiti = store_and_graphiti
    await _write(graphiti, fact="aware 版本", occurred_at=T1)
    # 模拟历史脏数据: 直接塞一条 naive valid_at 的边
    store.edges[0].valid_at = datetime(2026, 5, 30)  # naive
    history = await bs.get_belief_history(
        graphiti,
        BK,
        "vault:cs_61b:recursion",
        as_of=datetime(2026, 6, 1, tzinfo=timezone.utc),
    )
    assert len(history) == 1  # 不抛异常即通过
