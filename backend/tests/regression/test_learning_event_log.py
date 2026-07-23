"""批次3' 2-4 统一学习事件日志契约锁定 (MEM-FLYWHEEL-2026-07-22)。

schema 四要素: event_id 幂等键 / event_version / recorded_at+effective_at
双时间戳 / 8 类白名单。写失败永不抛异常 (不炸主链)。
"""

import json

from app.services import learning_event_log as ev


def _patch_path(monkeypatch, tmp_path):
    monkeypatch.setattr(ev, "_log_path", lambda: tmp_path / "learning_events.jsonl")


def test_append_writes_full_schema(monkeypatch, tmp_path):
    _patch_path(monkeypatch, tmp_path)
    ok = ev.append_event(
        "candidate_disputed",
        event_id="dispute:c-1",
        node_id="Eigenvalues",
        payload={"dispute_reason": "这不是我的错误"},
    )
    assert ok
    rec = json.loads((tmp_path / "learning_events.jsonl").read_text().strip())
    for field in (
        "event_id",
        "event_version",
        "event_type",
        "node_id",
        "recorded_at",
        "effective_at",
        "payload",
    ):
        assert field in rec
    assert rec["event_version"] == 1
    assert rec["event_type"] == "candidate_disputed"


def test_idempotent_by_event_id(monkeypatch, tmp_path):
    _patch_path(monkeypatch, tmp_path)
    assert ev.append_event("answer_scored", event_id="quiz:e1")
    assert not ev.append_event("answer_scored", event_id="quiz:e1")  # 重放跳过
    lines = (tmp_path / "learning_events.jsonl").read_text().strip().splitlines()
    assert len(lines) == 1


def test_unknown_event_type_rejected(monkeypatch, tmp_path):
    _patch_path(monkeypatch, tmp_path)
    assert not ev.append_event("random_new_type", event_id="x-1")
    assert not (tmp_path / "learning_events.jsonl").exists()


def test_empty_event_id_rejected(monkeypatch, tmp_path):
    _patch_path(monkeypatch, tmp_path)
    assert not ev.append_event("answer_scored", event_id="")


def test_effective_at_can_backfill(monkeypatch, tmp_path):
    """补录历史事件: effective_at 与 recorded_at 分离。"""
    _patch_path(monkeypatch, tmp_path)
    ev.append_event(
        "session_archived",
        event_id="archive:s1",
        effective_at="2026-07-01T00:00:00+00:00",
    )
    rec = json.loads((tmp_path / "learning_events.jsonl").read_text().strip())
    assert rec["effective_at"] == "2026-07-01T00:00:00+00:00"
    assert rec["recorded_at"] != rec["effective_at"]


def test_io_failure_never_raises(monkeypatch):
    monkeypatch.setattr(
        ev, "_log_path", lambda: (_ for _ in ()).throw(RuntimeError("boom"))
    )
    assert not ev.append_event("answer_scored", event_id="quiz:e2")
