"""Phase 2 (GRAPHITI-NATIVE-MEMORY-2026-06-10): record_knowledge_entity 路由重构单测。

① 删 neo4j.record_episode 双写 (假写: MERGE User-LEARNED-Concept 丢弃 tip 内容)。
② 结构化 event → graphiti_structured_writer 确定性写 (主路径);
   非结构化 / graphiti 未就绪 / 缺 node_id → 原 add_episode 队列 (语义通道/fallback)。
"""

from types import SimpleNamespace

import pytest

from app.services.memory_service import MemoryService


class SpyNeo4j:
    """record_episode 间谍: 断言双写已删。"""

    def __init__(self):
        self.record_episode_calls = []
        self.stats = {"initialized": True}  # 即使"已连接"也不该再调 record_episode

    async def record_episode(self, data):
        self.record_episode_calls.append(data)
        return True

    async def run_query(self, query, **params):
        return []


@pytest.fixture
def svc(monkeypatch):
    s = MemoryService()
    s._initialized = True
    s.neo4j = SpyNeo4j()

    enqueued = []
    monkeypatch.setattr(s, "_enqueue_episode", lambda **kw: enqueued.append(kw) or True)

    # graphiti 就绪的 worker
    fake_graphiti = SimpleNamespace(driver="DRIVER", embedder="EMBEDDER")
    monkeypatch.setattr(
        "app.services.memory_service.get_episode_worker",
        lambda: SimpleNamespace(_graphiti=fake_graphiti),
    )

    written = {}

    async def spy_callout(driver, embedder, **kw):
        written["callout"] = {"driver": driver, "embedder": embedder, **kw}

    async def spy_error(driver, embedder, **kw):
        written["error"] = {"driver": driver, "embedder": embedder, **kw}

    async def spy_conv(driver, embedder, **kw):
        written["conversation"] = {"driver": driver, "embedder": embedder, **kw}

    monkeypatch.setattr(
        "app.services.graphiti_structured_writer.write_callout", spy_callout
    )
    monkeypatch.setattr(
        "app.services.graphiti_structured_writer.write_error", spy_error
    )
    monkeypatch.setattr(
        "app.services.graphiti_structured_writer.write_conversation_summary", spy_conv
    )
    return s, enqueued, written


# ═══════════════════════════════════════════════════════════════════════════════
# ① 双写已删: 任何 event_type 都不再调 neo4j.record_episode
# ═══════════════════════════════════════════════════════════════════════════════


async def test_record_episode_dual_write_removed(svc):
    s, enqueued, written = svc
    await s.record_knowledge_entity(
        event_type="learning_tip",
        content="先想 base case",
        metadata={"node_id": "recursion"},
        group_id="vault:g",
    )
    assert s.neo4j.record_episode_calls == []  # 假写路径已删


# ═══════════════════════════════════════════════════════════════════════════════
# ② 结构化路由 → structured_writer (不再 enqueue)
# ═══════════════════════════════════════════════════════════════════════════════


async def test_callout_routes_to_structured_writer(svc):
    s, enqueued, written = svc
    await s.record_knowledge_entity(
        event_type="callout_annotation",
        content="批注正文",
        metadata={"node_id": "recursion", "tag": "question"},
        group_id="vault:cs_61b:rec",
    )
    assert "callout" in written
    call = written["callout"]
    assert call["driver"] == "DRIVER" and call["embedder"] == "EMBEDDER"
    assert call["node_id"] == "recursion"
    assert call["group_id"] == "vault:cs_61b:rec"
    assert call["callout_type"] == "question"
    assert call["text"] == "批注正文"
    assert enqueued == []  # 结构化主路径不再进 add_episode 队列 (D6)


async def test_learning_tip_routes_as_callout_tip(svc):
    s, enqueued, written = svc
    await s.record_knowledge_entity(
        event_type="learning_tip",
        content="t",
        metadata={"node_id": "n"},
        group_id="vault:g",
    )
    assert written["callout"]["callout_type"] == "tip"


async def test_misconception_routes_to_write_error(svc):
    s, enqueued, written = svc
    await s.record_knowledge_entity(
        event_type="misconception",
        content="忘了 base case",
        metadata={"node_id": "recursion", "error_type": "knowledge_gap"},
        group_id="vault:g",
    )
    assert written["error"]["error_type"] == "knowledge_gap"
    assert written["error"]["description"] == "忘了 base case"
    assert enqueued == []


async def test_conversation_archive_routes_to_summary(svc):
    s, enqueued, written = svc
    await s.record_knowledge_entity(
        event_type="conversation_archive",
        content="full content",
        metadata={"node_id": "recursion", "summary": "讨论了 base case"},
        group_id="vault:g",
    )
    assert written["conversation"]["summary"] == "讨论了 base case"
    assert enqueued == []


# ═══════════════════════════════════════════════════════════════════════════════
# fallback: 非结构化 / 缺 node_id / graphiti 未就绪 → 原 enqueue 队列
# ═══════════════════════════════════════════════════════════════════════════════


async def test_non_structured_event_falls_back_to_enqueue(svc):
    s, enqueued, written = svc
    await s.record_knowledge_entity(
        event_type="mastery_update",  # 非结构化路由表内
        content="c",
        metadata={"node_id": "n"},
        group_id="vault:g",
    )
    assert written == {}
    assert len(enqueued) == 1


async def test_missing_node_id_falls_back_to_enqueue(svc):
    s, enqueued, written = svc
    await s.record_knowledge_entity(
        event_type="learning_tip",
        content="c",
        metadata={},  # 无 node_id → 无法精确键写
        group_id="vault:g",
    )
    assert written == {}
    assert len(enqueued) == 1


async def test_graphiti_unready_falls_back_to_enqueue(svc, monkeypatch):
    s, enqueued, written = svc
    monkeypatch.setattr(
        "app.services.memory_service.get_episode_worker",
        lambda: SimpleNamespace(_graphiti=None),
    )
    await s.record_knowledge_entity(
        event_type="learning_tip",
        content="c",
        metadata={"node_id": "n"},
        group_id="vault:g",
    )
    assert written == {}
    assert len(enqueued) == 1


async def test_structured_write_failure_falls_back_to_enqueue(svc, monkeypatch):
    s, enqueued, written = svc

    async def boom(driver, embedder, **kw):
        raise RuntimeError("neo4j down")

    monkeypatch.setattr("app.services.graphiti_structured_writer.write_callout", boom)
    await s.record_knowledge_entity(
        event_type="learning_tip",
        content="c",
        metadata={"node_id": "n"},
        group_id="vault:g",
    )
    assert len(enqueued) == 1  # 结构化失败非致命, 退语义队列保数据
