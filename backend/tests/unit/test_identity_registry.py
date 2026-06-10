"""Phase 0 (GRAPHITI-NATIVE-MEMORY-2026-06-10): 身份层 identity_registry 单测。

D3: node_id ↔ Graphiti entity_uuid 的单一确定性映射真相源。
所有 writer/reader 必须经此取 uuid — 否则三套命名空间(Canvas node_id /
belief 自造节点 / add_episode LLM 抽取名)再次分裂(审查 M2 + ChatGPT 命门)。
"""

import pytest
from graphiti_core.errors import NodeNotFoundError
from graphiti_core.nodes import EntityNode

from app.graphiti.identity_registry import IdentityRegistry, entity_uuid_for_node


# ═══════════════════════════════════════════════════════════════════════════════
# entity_uuid_for_node — 确定性 + 命名空间隔离
# ═══════════════════════════════════════════════════════════════════════════════


def test_entity_uuid_deterministic():
    u1 = entity_uuid_for_node("recursion-base-case", "vault__cs_61b__recursion")
    u2 = entity_uuid_for_node("recursion-base-case", "vault__cs_61b__recursion")
    assert u1 == u2
    assert len(u1) == 36  # uuid5 str 形态


def test_entity_uuid_namespaced_by_group():
    a = entity_uuid_for_node("x", "vault__a")
    b = entity_uuid_for_node("x", "vault__b")
    assert a != b  # 同 node_id 不同 group → 不同身份 (防跨 vault 串)


def test_entity_uuid_differs_by_node():
    a = entity_uuid_for_node("node-a", "vault__g")
    b = entity_uuid_for_node("node-b", "vault__g")
    assert a != b


# ═══════════════════════════════════════════════════════════════════════════════
# IdentityRegistry.ensure_entity_node — 复用已有 / 确定性新建 / D8 embedding
# ═══════════════════════════════════════════════════════════════════════════════


class FakeEmbedder:
    """最小 embedder double: 记录调用并返回向量。"""

    def __init__(self):
        self.calls: list[list[str]] = []

    async def create(self, input_data):
        self.calls.append(list(input_data))
        return [0.1, 0.2, 0.3]


@pytest.fixture
def capture(monkeypatch):
    """monkeypatch EntityNode 的 get_by_uuid/save 到内存 store。"""
    store: dict[str, EntityNode] = {}
    saved: list[EntityNode] = []

    async def fake_get_by_uuid(cls, driver, uuid):
        if uuid in store:
            return store[uuid]
        raise NodeNotFoundError(uuid)

    async def fake_save(self, driver):
        store[self.uuid] = self
        saved.append(self)

    monkeypatch.setattr(EntityNode, "get_by_uuid", classmethod(fake_get_by_uuid))
    monkeypatch.setattr(EntityNode, "save", fake_save)
    return store, saved


async def test_ensure_creates_node_when_absent(capture):
    store, saved = capture
    uuid = await IdentityRegistry.ensure_entity_node(
        driver=object(), node_id="recursion", sanitized_group_id="vault__g"
    )
    assert uuid == entity_uuid_for_node("recursion", "vault__g")
    assert len(saved) == 1
    node = saved[0]
    assert node.uuid == uuid
    assert node.name == "recursion"
    assert node.group_id == "vault__g"
    assert node.attributes.get("node_id") == "recursion"


async def test_ensure_reuses_existing_node(capture):
    store, saved = capture
    driver = object()
    u1 = await IdentityRegistry.ensure_entity_node(
        driver=driver, node_id="recursion", sanitized_group_id="vault__g"
    )
    u2 = await IdentityRegistry.ensure_entity_node(
        driver=driver, node_id="recursion", sanitized_group_id="vault__g"
    )
    assert u1 == u2
    assert len(saved) == 1  # 第二次复用, 不再 save


async def test_ensure_generates_embedding_when_embedder_given(capture):
    store, saved = capture
    embedder = FakeEmbedder()
    await IdentityRegistry.ensure_entity_node(
        driver=object(),
        node_id="recursion",
        sanitized_group_id="vault__g",
        embedder=embedder,
    )
    # D8: 新建节点时生成 name_embedding (save 不会自动生成, edges/nodes.py 核实)
    assert len(embedder.calls) == 1
    assert saved[0].name_embedding == [0.1, 0.2, 0.3]


async def test_ensure_skips_embedding_without_embedder(capture):
    store, saved = capture
    await IdentityRegistry.ensure_entity_node(
        driver=object(), node_id="recursion", sanitized_group_id="vault__g"
    )
    assert (
        saved[0].name_embedding is None
    )  # 无 embedder → 不生成 (一期 exact-read 可用)
