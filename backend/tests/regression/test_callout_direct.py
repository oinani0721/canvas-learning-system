"""批次5' 批注过滤直连端点契约 (MEM-FLYWHEEL-2026-07-22, 燃料对账 §三)。

锁定: 类型过滤 / callout_id 幂等 / question 入 worker 队列 (json episode +
原始时间戳) / error 走 candidate_only 提名 / 低价值拒绝。
"""

from unittest.mock import MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.v1.endpoints.tips import tips_router
from fastapi import FastAPI

app = FastAPI()
app.include_router(tips_router, prefix="/api/v1/tips")


def _req(callout_type="question", callout_id="cb-test-1"):
    return {
        "callout_id": callout_id,
        "callout_type": callout_type,
        "node_id": "Eigenvalues",
        "text": "为什么特征值可以是复数？",
        "added_at": "2026-07-24T01:00:00+00:00",
        "vault_id": "canvas-vault",
    }


@pytest.fixture
def client():
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _post(client, payload, worker=None, append_ok=True):
    worker = worker or MagicMock(enqueue=MagicMock(return_value=True))
    with (
        patch("app.services.learning_event_log.append_event", return_value=append_ok) as ev,
        patch("app.services.episode_worker.get_episode_worker", return_value=worker),
    ):
        resp = await client.post("/api/v1/tips/callout-direct", json=payload)
    return resp, ev, worker


async def test_low_value_type_rejected(client):
    resp, ev, _ = await _post(client, _req(callout_type="tip"))
    assert resp.status_code == 200
    body = resp.json()
    assert body["accepted"] is False
    assert body["lane"] == "rejected_type"
    ev.assert_not_called()  # 低价值不落 callout_ingested 事件


async def test_duplicate_callout_id_idempotent(client):
    resp, _, worker = await _post(client, _req(), append_ok=False)
    body = resp.json()
    assert body["accepted"] is False
    assert "幂等" in body["message"]
    worker.enqueue.assert_not_called()


async def test_question_enqueues_narrative_episode_with_original_time(client):
    """e2e 修正 (2026-07-24): 疑问批注用陈述句 episode — 纯 json 对疑问句
    抽不出关系边 (疑问没有 fact), 「用户提出疑问」本身才是可抽取的事实。"""
    resp, ev, worker = await _post(client, _req())
    body = resp.json()
    assert body["accepted"] is True
    assert body["lane"] == "question_episode"
    task = worker.enqueue.call_args.args[0]
    assert task.source is None  # 陈述句 text episode, 非 json
    assert "提出了疑问" in task.episode_body
    assert "为什么特征值可以是复数" in task.episode_body
    assert "Eigenvalues" in task.episode_body
    # 时间戳守卫: reference_time = 批注原始时间, 不是入库时间
    assert task.reference_time.isoformat().startswith("2026-07-24T01:00:00")
    # 事件 effective_at 同样回填原始时间
    assert ev.call_args.kwargs["effective_at"].startswith("2026-07-24T01:00:00")


async def test_error_schedules_candidate_nomination(client):
    with patch("app.services.error_classifier.get_error_classifier") as get_cls:
        get_cls.return_value = MagicMock()
        resp, _, _ = await _post(client, _req(callout_type="error", callout_id="cb-err-1"))
    body = resp.json()
    assert body["accepted"] is True
    assert body["lane"] == "error_candidate"


async def test_missing_added_at_rejected_422(client):
    payload = _req()
    del payload["added_at"]
    resp = await client.post("/api/v1/tips/callout-direct", json=payload)
    assert resp.status_code == 422  # 时间戳守卫: 缺原始时间直接拒收
