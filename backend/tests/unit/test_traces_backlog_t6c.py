"""CARD-NEO4J-REPLAY-BOUND (T6-C, BATCH-2026-09-11-第十四批) — /traces 错目录 + 只读 backlog。

两件事，都是先红后绿：

1. **DD-13 名实不符**：``traces.py`` 的 ``DATA_DIR`` 用 4 层 ``.parent`` 只走到
   ``backend/app``，而所有死信文件实际落 ``backend/data``（写侧
   ``failure_counters.py`` / ``failed_writes_constants.py`` 用 3 层 ``.parent``
   从 ``backend/app/core/`` 恰好到 ``backend/data``）。``LOGS_DIR`` 同错
   （``backend/app/logs`` 不存在，``audit.jsonl`` 在 ``backend/logs``）。
   ⇒ ``/traces/{request_id}`` 的 summary 宣称聚合 bug_log / failed_edge_syncs /
   dead_letter_episodes / audit 四个源，实际读的是空目录，**恒查不到**。
2. **只读 backlog 路由**：新增 ``GET /traces/dead-letter-backlog``，必须声明在
   ``GET /traces/{request_id}`` **之前**，否则被动态段吃掉
   （``request_id="dead-letter-backlog"``）。

⛔ 硬边界：裸 ``FastAPI()`` 挂 router（**无 lifespan** ⇒ 不起 Neo4j、不连
7691/7687）；所有读取面 ``monkeypatch`` 到 ``tmp_path``，不碰现网
``backend/data`` / ``backend/logs``。
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import app.api.v1.endpoints.traces as traces

BACKLOG_PATH = "/api/v1/traces/dead-letter-backlog"


@pytest.fixture
def client():
    """裸 app：只挂 traces router，无 lifespan ⇒ 不触发任何启动期外连。"""
    bare = FastAPI()
    bare.include_router(traces.router, prefix="/api/v1")
    return TestClient(bare, raise_server_exceptions=False)


def _write_jsonl(path: Path, entries) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(e, ensure_ascii=False) + "\n" for e in entries),
        encoding="utf-8",
    )


# ═══════════════════════════════════════════════════════════════════════════
# (d)① DATA_DIR / LOGS_DIR 指错目录 —— 常量级断言
#      不 monkeypatch、不碰任何真实目录，只读 Path 对象的 .parts
# ═══════════════════════════════════════════════════════════════════════════


def test_data_dir_points_at_backend_data():
    """改前必红：DATA_DIR 末两段实测 == ("app", "data")，死信文件却在 backend/data。"""
    assert traces.DATA_DIR.parts[-2:] == ("backend", "data"), f"DATA_DIR 指错目录: {traces.DATA_DIR}"


def test_logs_dir_points_at_backend_logs():
    """改前必红：LOGS_DIR 同错 —— audit.jsonl 在 backend/logs，不在 backend/app/logs。"""
    assert traces.LOGS_DIR.parts[-2:] == ("backend", "logs"), f"LOGS_DIR 指错目录: {traces.LOGS_DIR}"


def test_data_dir_matches_dead_letter_writer_anchor():
    """读侧目录必须与写侧逐字同 —— 写侧是 failure_counters 的 dead-letter 路径。"""
    from app.core.failure_counters import EDGE_SYNC_DEAD_LETTER_PATH

    assert traces.DATA_DIR == EDGE_SYNC_DEAD_LETTER_PATH.parent, (
        f"读侧 {traces.DATA_DIR} != 写侧 {EDGE_SYNC_DEAD_LETTER_PATH.parent}"
    )


# ═══════════════════════════════════════════════════════════════════════════
# 验伪锚（承重）：改前改后都须绿
# ═══════════════════════════════════════════════════════════════════════════


def test_missing_source_file_does_not_crash_trace_query(client, monkeypatch, tmp_path):
    """验伪锚：源文件不存在时 /traces/{id} 返回 200 空 timeline，不是 500。

    这条在改前改后都绿 —— 它证明「文件缺席不崩」是既有性质，本卡既没有
    引入它也没有破坏它；(d) 的红不是「路由整体坏了」造成的。
    """
    monkeypatch.setattr(traces, "LOG_FILES", {"bug_log": tmp_path / "does-not-exist.jsonl"})
    r = client.get("/api/v1/traces/req-xyz")
    assert r.status_code == 200
    assert r.json()["total_events"] == 0


# ═══════════════════════════════════════════════════════════════════════════
# (d)② backlog 路由：声明顺序 + 形态
# ═══════════════════════════════════════════════════════════════════════════


def test_backlog_route_is_not_shadowed_by_dynamic_segment(client, monkeypatch, tmp_path):
    """改前必红：无该静态路由 ⇒ 被 /traces/{request_id} 吃掉，返回 trace 形态。

    ⚠️ 不断言 404 —— 改前是 **200**（动态段接住了），断言 404 会是
    「改前红、改后也红」的错方向。判据是**形态**：backlog 有 ``files``，
    trace 有 ``timeline``。
    """
    monkeypatch.setattr(traces, "BACKLOG_FILES", {"x": tmp_path / "x.jsonl"}, raising=False)
    r = client.get(BACKLOG_PATH)
    assert r.status_code == 200
    body = r.json()
    assert "files" in body, f"不是 backlog 形态（被动态段吃掉了？）: {sorted(body)}"
    assert "timeline" not in body, "返回的是 trace 形态，说明静态路由声明在动态段之后"


def test_backlog_counts_lines_and_reports_oldest_and_newest(client, monkeypatch, tmp_path):
    """backlog == 行数；oldest/newest == 首/末条的 timestamp（不放宽成「字段存在」）。"""
    active = tmp_path / "failed_writes.jsonl"
    _write_jsonl(
        active,
        [
            {"timestamp": "2026-09-01T00:00:00Z", "i": 0},
            {"timestamp": "2026-09-02T00:00:00Z", "i": 1},
            {"timestamp": "2026-09-03T00:00:00Z", "i": 2},
        ],
    )
    monkeypatch.setattr(traces, "BACKLOG_FILES", {"failed_writes.jsonl": active}, raising=False)

    entry = client.get(BACKLOG_PATH).json()["files"][0]
    # 端点对单链故障是降级（回 error 字段）而不是 500 —— 所以顺利路径必须
    # 显式断言「没有 error」，否则一个内部异常会被降级机制盖成 200 假绿。
    assert "error" not in entry, f"读取该链时降级了: {entry.get('error')}"
    assert entry["exists"] is True
    assert entry["backlog"] == 3
    assert entry["oldest"] == "2026-09-01T00:00:00Z"
    assert entry["newest"] == "2026-09-03T00:00:00Z"


def test_backlog_reports_overflow_siblings(client, monkeypatch, tmp_path):
    """轮转后活动文件很短，积压其实在 .overflow.* 里 —— 不报它就是谎报积压。"""
    active = tmp_path / "failed_writes.jsonl"
    _write_jsonl(active, [{"timestamp": "2026-09-09T00:00:00Z"}])
    for ts in ("2026-09-01-000000000001", "2026-09-02-000000000002"):
        _write_jsonl(tmp_path / f"failed_writes.overflow.{ts}", [{"a": 1}, {"a": 2}])
    monkeypatch.setattr(traces, "BACKLOG_FILES", {"failed_writes.jsonl": active}, raising=False)

    entry = client.get(BACKLOG_PATH).json()["files"][0]
    assert entry["overflow_files"] == 2, f"未报 .overflow.* 兄弟, backlog 谎报为 {entry['backlog']}"
    assert entry["overflow_bytes"] > 0


def test_backlog_missing_file_reports_zero_and_does_not_crash(client, monkeypatch, tmp_path):
    """文件不存在 ⇒ exists=False / backlog=0 / oldest=None，200 不崩。"""
    monkeypatch.setattr(
        traces,
        "BACKLOG_FILES",
        {"gone.jsonl": tmp_path / "nope" / "gone.jsonl"},
        raising=False,
    )
    r = client.get(BACKLOG_PATH)
    assert r.status_code == 200
    entry = r.json()["files"][0]
    assert entry["exists"] is False
    assert entry["backlog"] == 0
    assert entry["oldest"] is None
    assert entry["newest"] is None


def test_backlog_survives_corrupt_and_blank_lines(client, monkeypatch, tmp_path):
    """坏 JSON / 空行不得让端点 500；oldest 取第一条**可解析且带 timestamp** 的。"""
    active = tmp_path / "failed_writes.jsonl"
    active.write_text(
        'not json at all\n\n{"timestamp": "2026-09-05T00:00:00Z"}\n{"no_timestamp": 1}\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(traces, "BACKLOG_FILES", {"failed_writes.jsonl": active}, raising=False)
    r = client.get(BACKLOG_PATH)
    assert r.status_code == 200
    entry = r.json()["files"][0]
    assert entry["backlog"] == 4  # 行数照数，不因坏行漏计
    assert entry["oldest"] == "2026-09-05T00:00:00Z"


def test_backlog_non_jsonl_reports_size_not_fake_timestamps(client, monkeypatch, tmp_path):
    """非 JSONL（neo4j_memory.json 等）没有「首条 timestamp」⇒ oldest/newest 必须是 None。

    禁止把 mtime 塞进 newest 冒充条目时间戳 —— 那正是 DD-13 名实不符。
    """
    blob = tmp_path / "neo4j_memory.json"
    blob.write_text(json.dumps({"nodes": [1, 2, 3]}), encoding="utf-8")
    monkeypatch.setattr(traces, "BACKLOG_FILES", {"neo4j_memory.json": blob}, raising=False)

    entry = client.get(BACKLOG_PATH).json()["files"][0]
    assert entry["kind"] == "json"
    assert entry["backlog"] is None, "非 JSONL 不得谎报行数式的 backlog"
    assert entry["oldest"] is None and entry["newest"] is None
    assert entry["size_bytes"] == blob.stat().st_size
    assert entry["mtime"] is not None


# ═══════════════════════════════════════════════════════════════════════════
# 覆盖面 + 路径锚点（逐文件按各自写侧锚，不统一套 DATA_DIR）
# ═══════════════════════════════════════════════════════════════════════════


def test_backlog_covers_every_staging_chain():
    """七条降级暂存链一条都不能漏 —— 漏一条 = backlog 少报一处积压。"""
    assert set(traces.BACKLOG_FILES) == {
        "failed_writes.jsonl",
        "failed_edge_syncs.jsonl",
        "failed_dual_writes.jsonl",
        "dead_letter_episodes.jsonl",
        "neo4j_memory.json",
        "learning_memories.json",
        "canvas_events_fallback.json",
    }


def test_backlog_paths_are_anchored_at_each_writer():
    """canvas_events_fallback 写侧落 backend/app/data，与其余（backend/data）不同目录。

    统一套修好的 DATA_DIR 会让它恒 exists=False —— 报「不存在」而实际写在
    app/data，又是一处 DD-13。
    """
    files = traces.BACKLOG_FILES
    assert files["canvas_events_fallback.json"].parts[-3:] == (
        "app",
        "data",
        "canvas_events_fallback.json",
    )
    for name in (
        "failed_writes.jsonl",
        "failed_edge_syncs.jsonl",
        "failed_dual_writes.jsonl",
        "neo4j_memory.json",
        "learning_memories.json",
        "dead_letter_episodes.jsonl",
    ):
        assert files[name].parts[-3:] == ("backend", "data", name), f"{name} 锚错目录: {files[name]}"


def test_backlog_path_field_is_not_absolute(client, monkeypatch, tmp_path):
    """path 字段不回绝对路径 —— 本路由与兄弟 /traces/{id} 同样无鉴权。"""
    active = tmp_path / "failed_writes.jsonl"
    _write_jsonl(active, [{"timestamp": "2026-09-01T00:00:00Z"}])
    monkeypatch.setattr(traces, "BACKLOG_FILES", {"failed_writes.jsonl": active}, raising=False)
    entry = client.get(BACKLOG_PATH).json()["files"][0]
    assert not entry["path"].startswith("/"), f"回了绝对路径: {entry['path']}"
