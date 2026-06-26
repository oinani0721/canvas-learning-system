"""P2 (A+-prime 2026-06-26): A7 诚实失败契约单测。

record_knowledge_entity 返回 {entity_id, status}:
- written:  结构化写入图 (graphiti 就绪 + 写成功)
- enqueued: 进语义队列 (无 graphiti 但 worker 就绪)
- degraded: worker 未就绪 → 落 outbox 待重放 (不再静默假成功)

recover_failed_writes 重放结构化 outbox 条目 (kind=knowledge_entity)。
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

import app.services.memory_service as ms


@pytest.fixture
def service():
    svc = ms.MemoryService.__new__(ms.MemoryService)
    svc._initialized = True
    svc._episodes = []
    svc.MAX_EPISODE_CACHE = 100
    svc._pending_failed_writes = []
    return svc


def _worker(monkeypatch, *, graphiti, is_ready, enqueue_ok=True):
    w = MagicMock()
    w._graphiti = graphiti
    w.is_ready = is_ready
    w.enqueue = MagicMock(return_value=enqueue_ok)
    monkeypatch.setattr(ms, "get_episode_worker", lambda: w)
    return w


async def test_status_written_when_structured_succeeds(service, monkeypatch):
    g = MagicMock()
    g.driver = MagicMock()
    g.embedder = MagicMock()
    _worker(monkeypatch, graphiti=g, is_ready=True)
    monkeypatch.setattr(
        "app.services.graphiti_structured_writer.write_callout", AsyncMock()
    )
    r = await service.record_knowledge_entity(
        "callout_annotation", "x", {"node_id": "n", "content": "x"}, "vault:g"
    )
    assert r["status"] == "written"
    assert r["entity_id"].startswith("callout_annotation-")


async def test_status_enqueued_when_no_graphiti_but_worker_ready(service, monkeypatch):
    _worker(monkeypatch, graphiti=None, is_ready=True, enqueue_ok=True)
    r = await service.record_knowledge_entity("learning_tip", "x", {}, "vault:g")
    assert r["status"] == "enqueued"


async def test_status_degraded_and_outbox_when_worker_not_ready(service, monkeypatch):
    """A7 核心: worker 未就绪 → degraded + 落 outbox, 不静默假成功。"""
    _worker(monkeypatch, graphiti=None, is_ready=False)
    captured = []
    monkeypatch.setattr(
        service, "_record_structured_outbox", lambda e: captured.append(e) or True
    )
    r = await service.record_knowledge_entity(
        "callout_annotation", "x", {"node_id": "n", "content": "x"}, "vault:g"
    )
    assert r["status"] == "degraded"
    assert len(captured) == 1
    assert captured[0]["kind"] == "knowledge_entity"
    assert captured[0]["event_type"] == "callout_annotation"
    assert captured[0]["metadata"]["node_id"] == "n"


async def test_from_recovery_does_not_repersist_outbox(service, monkeypatch):
    """重放路径 degraded 时不再落 outbox, 避免重复堆积。"""
    _worker(monkeypatch, graphiti=None, is_ready=False)
    captured = []
    monkeypatch.setattr(
        service, "_record_structured_outbox", lambda e: captured.append(e)
    )
    r = await service.record_knowledge_entity(
        "callout_annotation", "x", {"node_id": "n"}, "vault:g", _from_recovery=True
    )
    assert r["status"] == "degraded"
    assert captured == []


async def test_recover_replays_structured_entry(service, monkeypatch, tmp_path):
    """recover_failed_writes 重放 kind=knowledge_entity → 调 record_knowledge_entity。"""
    f = tmp_path / "failed.jsonl"
    f.write_text(
        json.dumps(
            {
                "kind": "knowledge_entity",
                "event_type": "callout_annotation",
                "content": "x",
                "metadata": {"node_id": "n"},
                "group_id": "vault:g",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(ms, "FAILED_WRITES_FILE", f)
    calls = []

    async def fake_rke(
        event_type, content, metadata=None, group_id=None, _from_recovery=False
    ):
        calls.append((event_type, _from_recovery))
        return {"entity_id": "e", "status": "written"}

    monkeypatch.setattr(service, "record_knowledge_entity", fake_rke)
    result = await service.recover_failed_writes()
    assert result["recovered"] == 1
    assert calls == [("callout_annotation", True)]  # 用 _from_recovery=True 重放
    assert not f.exists()  # 全部重放成功 → 文件清空


async def test_recover_keeps_pending_when_replay_degrades(
    service, monkeypatch, tmp_path
):
    """重放仍 degraded → 保留条目待下次 (不丢)。"""
    f = tmp_path / "failed.jsonl"
    f.write_text(
        json.dumps(
            {
                "kind": "knowledge_entity",
                "event_type": "callout_annotation",
                "content": "x",
                "metadata": {"node_id": "n"},
                "group_id": "vault:g",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(ms, "FAILED_WRITES_FILE", f)

    async def fake_rke(*a, **kw):
        return {"entity_id": "e", "status": "degraded"}

    monkeypatch.setattr(service, "record_knowledge_entity", fake_rke)
    result = await service.recover_failed_writes()
    assert result["recovered"] == 0
    assert f.exists()  # 仍 degraded → 保留
