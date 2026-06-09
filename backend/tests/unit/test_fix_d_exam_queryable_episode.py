"""Fix-D 回归测试: record_knowledge_entity 同步直写 node_id-keyed EpisodicNode。

背景 (GAP-D): Graphiti add_episode 不传 node_id, 直接 record_episode 写 User-LEARNED-
Concept — 都产不出 question_generator._get_tips 能查的 EpisodicNode{source_description,
node_id}。Fix-D 在 record_knowledge_entity 里加同步直写补齐。

verify_targeted_exam_chain.py 已做真实 Neo4j 端到端验证 (Layer 2 红→绿);
本文件用 capture 双做 CI 友好的纯逻辑回归 (无需 Neo4j)。
"""

import pytest

from app.services.memory_service import MemoryService


class CaptureNeo4j:
    """捕获 run_query 调用的 test double (复刻足够的 Neo4jClient 接口)。"""

    def __init__(self):
        self.calls: list[tuple[str, dict]] = []
        self.stats = {"initialized": False}  # 让 record_episode User-LEARNED 写跳过

    async def run_query(self, query: str, **params):
        self.calls.append((query, params))
        return []


@pytest.fixture
def svc_with_capture():
    svc = MemoryService()
    svc._initialized = True  # 跳过 initialize()
    cap = CaptureNeo4j()
    svc.neo4j = cap
    return svc, cap


# ═══════════════════════════════════════════════════════════════════════════════
# helper 直接测: 写出的 EpisodicNode 形状对齐 _get_tips / _get_error_history
# ═══════════════════════════════════════════════════════════════════════════════


async def test_helper_writes_node_id_and_canonical_source(svc_with_capture):
    svc, cap = svc_with_capture
    await svc._write_exam_queryable_episode(
        entity_id="tip-abc",
        node_id="recursion-base-case",
        source_description="callout-annotation-record",
        content="递归一定要先想 base case",
        created_at="2026-06-10T00:00:00",
        group_id="vault:cs_61b:recursion",
    )
    assert len(cap.calls) == 1
    query, params = cap.calls[0]
    assert "MERGE (e:EpisodicNode" in query
    assert "e.node_id = $node_id" in query
    # _get_tips 按 source_description + node_id 精确查 → 两者必须落顶层属性
    assert params["node_id"] == "recursion-base-case"
    assert params["source_description"] == "callout-annotation-record"
    assert params["content"] == "递归一定要先想 base case"
    # tip 无 error_type → description 为 None (不污染 _get_error_history)
    assert params["error_type"] is None
    assert params["description"] is None


async def test_helper_sets_error_type_and_description_for_errors(svc_with_capture):
    svc, cap = svc_with_capture
    await svc._write_exam_queryable_episode(
        entity_id="err-1",
        node_id="recursion-base-case",
        source_description="misconception-record",
        content="忘了写 base case",
        created_at="2026-06-10T00:00:00",
        group_id="vault:cs_61b:recursion",
        error_type="knowledge_gap",
    )
    _query, params = cap.calls[0]
    # _get_error_history 读 e.error_type / e.description
    assert params["error_type"] == "knowledge_gap"
    assert params["description"] == "忘了写 base case"


async def test_helper_deterministic_uuid_idempotent(svc_with_capture):
    """同一 (node_id, source_description, content) → 同 uuid → MERGE 幂等不重复。"""
    svc, cap = svc_with_capture
    args = dict(
        entity_id="x",
        node_id="n1",
        source_description="callout-annotation-record",
        content="same",
        created_at="2026-06-10T00:00:00",
        group_id="g",
    )
    await svc._write_exam_queryable_episode(**args)
    await svc._write_exam_queryable_episode(**args)
    uuid1 = cap.calls[0][1]["uuid"]
    uuid2 = cap.calls[1][1]["uuid"]
    assert uuid1 == uuid2
    assert uuid1.startswith("exam-ep-")


# ═══════════════════════════════════════════════════════════════════════════════
# 集成 gate 逻辑: record_knowledge_entity 何时调 helper
# ═══════════════════════════════════════════════════════════════════════════════


async def test_record_knowledge_entity_writes_exam_node_when_node_id_present(
    svc_with_capture, monkeypatch
):
    svc, _cap = svc_with_capture
    captured = {}

    async def spy(**kwargs):
        captured.update(kwargs)
        return True

    monkeypatch.setattr(svc, "_write_exam_queryable_episode", spy)
    # _enqueue_episode 走 worker, 隔离掉 (worker 未跑会自然 return False, 但保险 stub)
    monkeypatch.setattr(svc, "_enqueue_episode", lambda **kw: False)

    await svc.record_knowledge_entity(
        event_type="callout_annotation",
        content="先想 base case",
        metadata={"node_id": "recursion-base-case"},
        group_id="vault:cs_61b:recursion",
    )
    assert captured.get("node_id") == "recursion-base-case"
    assert captured.get("source_description") == "callout-annotation-record"


async def test_record_knowledge_entity_skips_exam_node_without_node_id(
    svc_with_capture, monkeypatch
):
    svc, _cap = svc_with_capture
    called = {"n": 0}

    async def spy(**kwargs):
        called["n"] += 1
        return True

    monkeypatch.setattr(svc, "_write_exam_queryable_episode", spy)
    monkeypatch.setattr(svc, "_enqueue_episode", lambda **kw: False)

    await svc.record_knowledge_entity(
        event_type="callout_annotation",
        content="无节点的事件",
        metadata={},  # 无 node_id
        group_id="vault:cs_61b:recursion",
    )
    assert called["n"] == 0, "无 node_id 不应写 exam-queryable 节点"


async def test_record_knowledge_entity_skips_exam_node_for_unknown_event(
    svc_with_capture, monkeypatch
):
    """非 canonical event_type (如 conversation_archive) 不写 exam 节点, 避免污染。"""
    svc, _cap = svc_with_capture
    called = {"n": 0}

    async def spy(**kwargs):
        called["n"] += 1
        return True

    monkeypatch.setattr(svc, "_write_exam_queryable_episode", spy)
    monkeypatch.setattr(svc, "_enqueue_episode", lambda **kw: False)

    await svc.record_knowledge_entity(
        event_type="conversation_archive",  # 不在 EVENT_TO_ENTITY_TYPE
        content="归档对话",
        metadata={"node_id": "n1"},
        group_id="g",
    )
    assert called["n"] == 0, "未知 event_type 不应写 exam-queryable 节点"
