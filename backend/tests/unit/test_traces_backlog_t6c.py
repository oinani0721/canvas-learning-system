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
    """每条降级暂存链都不能漏 —— 漏一条 = backlog 少报一处积压。

    ``outbox/events.jsonl`` 是独立复核 2026-09-15 抓到的遗漏：event_bus 的
    Tier-2 图写入重试耗尽后落它，同样是 Neo4j 降级链，而端点 description
    写的是「every Neo4j-degradation staging file」。
    """
    assert set(traces.BACKLOG_FILES) == {
        "outbox/events.jsonl",
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


# ═══════════════════════════════════════════════════════════════════════════
# Codex round-1 M2：部分读取失败必须留痕，不得被包装成正常零值
# ═══════════════════════════════════════════════════════════════════════════


def test_overflow_scan_failure_is_flagged_not_zeroed(client, monkeypatch, tmp_path):
    """归档目录列不出来 ⇒ 必须 partial + degraded，而不是静悄悄的 overflow_files=0。

    「没测到」和「没积压」在响应里长得一样，就是本卡要修的那类 DD-13。
    """
    active = tmp_path / "failed_writes.jsonl"
    _write_jsonl(active, [{"timestamp": "2026-09-01T00:00:00Z"}])

    def _boom(_p):
        raise PermissionError("cannot list dir")

    monkeypatch.setattr(traces, "overflow_siblings", _boom)
    monkeypatch.setattr(traces, "BACKLOG_FILES", {"failed_writes.jsonl": active}, raising=False)

    body = client.get(BACKLOG_PATH).json()
    entry = body["files"][0]
    assert entry["partial"] is True, "归档枚举失败却报成了完整结果"
    assert any(d.startswith("overflow_scan:") for d in entry["degraded"]), entry["degraded"]
    assert body["incomplete"] is True
    assert body["degraded_chains"] == ["failed_writes.jsonl"]
    # 活动文件仍然读到了 —— 降级是局部的，不是整条链报废
    assert entry["backlog"] == 1


def test_timestamp_scan_failure_is_flagged(client, monkeypatch, tmp_path):
    """数行成功、时间戳扫描失败 ⇒ oldest/newest 为 null **且**带 degraded 原因。"""
    active = tmp_path / "failed_writes.jsonl"
    _write_jsonl(active, [{"timestamp": "2026-09-01T00:00:00Z"}])

    def _boom(_p, *, max_bytes):
        raise AssertionError("不该被调用")

    monkeypatch.setattr(traces, "_first_last_timestamp", lambda p, *, max_bytes: (None, None, "read:OSError"))
    monkeypatch.setattr(traces, "BACKLOG_FILES", {"failed_writes.jsonl": active}, raising=False)

    entry = client.get(BACKLOG_PATH).json()["files"][0]
    assert entry["oldest"] is None and entry["newest"] is None
    assert "timestamp_scan:read:OSError" in entry["degraded"]
    assert entry["partial"] is True


def test_oversized_file_skips_timestamp_scan_and_says_so(client, monkeypatch, tmp_path):
    """超过尺寸闸 ⇒ 跳过时间戳扫描，但必须报 size_capped 而不是假装扫过了。

    「跳过」与「失败」是两个原因标签，不能合成一个 truncated 布尔。
    """
    active = tmp_path / "failed_writes.jsonl"
    _write_jsonl(active, [{"timestamp": "2026-09-01T00:00:00Z"}, {"timestamp": "2026-09-02T00:00:00Z"}])
    monkeypatch.setattr(traces, "BACKLOG_SCAN_MAX_BYTES", 1)  # 任何真实文件都超闸
    monkeypatch.setattr(traces, "BACKLOG_FILES", {"failed_writes.jsonl": active}, raising=False)

    body = client.get(BACKLOG_PATH).json()
    entry = body["files"][0]
    assert entry["backlog"] == 2, "尺寸超闸只该跳过时间戳扫描，不该连行数也不数"
    assert entry["oldest"] is None and entry["newest"] is None
    assert "timestamp_scan:size_capped" in entry["degraded"]
    assert body["incomplete"] is True


def test_healthy_chain_is_not_flagged(client, monkeypatch, tmp_path):
    """验伪锚（承重）：一切正常时 partial/incomplete 必须是 False。

    否则「恒 partial=True」也能让上面三条门变绿 —— 那样标记就没有鉴别力。
    """
    active = tmp_path / "failed_writes.jsonl"
    _write_jsonl(active, [{"timestamp": "2026-09-01T00:00:00Z"}])
    monkeypatch.setattr(traces, "BACKLOG_FILES", {"failed_writes.jsonl": active}, raising=False)

    body = client.get(BACKLOG_PATH).json()
    assert body["incomplete"] is False
    assert body["degraded_chains"] == []
    assert body["files"][0]["partial"] is False
    assert body["files"][0]["degraded"] == []


def test_missing_file_is_not_treated_as_degraded(client, monkeypatch, tmp_path):
    """文件不存在 ≠ 读失败：那是「确实没有积压」，不该标 partial。"""
    monkeypatch.setattr(traces, "BACKLOG_FILES", {"gone.jsonl": tmp_path / "nope" / "gone.jsonl"}, raising=False)
    body = client.get(BACKLOG_PATH).json()
    assert body["files"][0]["partial"] is False
    assert body["incomplete"] is False


# ═══════════════════════════════════════════════════════════════════════════
# Codex round-1 L2：降级路径上的 _display_path 自己不得抛
# ═══════════════════════════════════════════════════════════════════════════


def test_display_path_never_raises(monkeypatch, tmp_path):
    """resolve() 抛 RuntimeError（符号链接成环，Py<3.13）时必须退回文件名。

    ``_safe_backlog_entry`` 的降级分支**又会调用**它，所以这一处漏网会让
    异常逃出整条路由变成 500。捕获面必须宽于 (ValueError, OSError)。
    """

    class _Loop(type(tmp_path)):
        def resolve(self, strict=False):
            raise RuntimeError("Symlink loop")

    p = _Loop(tmp_path / "failed_writes.jsonl")
    assert traces._display_path(p) == "failed_writes.jsonl"


def test_entry_level_failure_degrades_that_chain_only(client, monkeypatch, tmp_path):
    """一条链整体抛错 ⇒ 该条 error + partial，另一条仍要能读出来。"""
    good = tmp_path / "failed_writes.jsonl"
    _write_jsonl(good, [{"timestamp": "2026-09-01T00:00:00Z"}])
    bad = tmp_path / "failed_edge_syncs.jsonl"
    _write_jsonl(bad, [{"timestamp": "2026-09-02T00:00:00Z"}])

    real = traces._backlog_entry

    def _selective(name, path):
        if name == "failed_edge_syncs.jsonl":
            raise RuntimeError("boom")
        return real(name, path)

    monkeypatch.setattr(traces, "_backlog_entry", _selective)
    monkeypatch.setattr(
        traces,
        "BACKLOG_FILES",
        {"failed_writes.jsonl": good, "failed_edge_syncs.jsonl": bad},
        raising=False,
    )

    body = client.get(BACKLOG_PATH).json()
    assert body["files"][0]["backlog"] == 1, "好的那条链被连累了"
    assert body["files"][1]["error"] == "RuntimeError"
    assert body["files"][1]["partial"] is True
    assert body["incomplete"] is True
    assert body["degraded_chains"] == ["failed_edge_syncs.jsonl"]


# ═══════════════════════════════════════════════════════════════════════════
# 独立复核 2026-09-15：被点名「零覆盖 / 判据恒真」的分支
# ═══════════════════════════════════════════════════════════════════════════


def test_display_path_success_branch_is_repo_relative(tmp_path, monkeypatch):
    """顺利分支必须有断言 —— 只测 fallback 的话，实现恒返回 path.name 也全绿。"""
    monkeypatch.setattr(traces, "_BACKEND_DIR", tmp_path)
    got = traces._display_path(tmp_path / "data" / "failed_writes.jsonl")
    assert got == "backend/data/failed_writes.jsonl"
    assert not got.startswith("/")


def test_display_path_does_not_leak_absolute_when_anchor_is_root(monkeypatch, tmp_path):
    """锚点退化成 `/` 时不得把整条绝对路径当「相对路径」回出去。

    这正是初版用 parents[5] 当仓根的问题：容器里 relative_to('/') **不会**
    抛异常，只是把前导斜杠去掉，脱敏静默失效。现在锚在 backend 上，
    tmp_path 下的文件根本不在锚内 ⇒ 走 fallback 只回文件名。
    """
    # ⚠️ 真的传 "/"（Codex round-2 L3：原先传的是一个不存在的目录，只测到
    # 「锚外走 fallback」，没测到「锚点就是根」这个真正会让脱敏失效的情形 ——
    # relative_to("/") **不抛异常**，只把前导斜杠去掉）。
    # ⚠️ 路径必须**浅到绕开深度闸**（Codex round-3 LOW-4）：tmp_path 有好几段，
    # 即便删掉根锚检查，「结果不超 3 段」那道闸也会兜住 ⇒ 门测不到根锚保护本身。
    # 用 /secret.jsonl：锚为 "/" 时 relative_to 只得 1 段，深度闸放行，
    # 于是只有根锚检查能阻止它把绝对路径回出去。
    monkeypatch.setattr(traces, "_BACKEND_DIR", Path("/"))
    assert traces._display_path(Path("/secret.jsonl")) == "secret.jsonl"


def test_newest_skips_entries_without_timestamp(client, monkeypatch, tmp_path):
    """末条没有 timestamp 时，newest 必须回退到**最后一条有 timestamp 的**。

    只断言 oldest 的话，把 `if ts is None: continue` 删掉照样全绿。
    """
    active = tmp_path / "failed_writes.jsonl"
    active.write_text(
        '{"timestamp": "2026-09-01T00:00:00Z"}\n{"timestamp": "2026-09-02T00:00:00Z"}\n{"no_timestamp": 1}\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(traces, "BACKLOG_FILES", {"failed_writes.jsonl": active}, raising=False)
    entry = client.get(BACKLOG_PATH).json()["files"][0]
    assert entry["oldest"] == "2026-09-01T00:00:00Z"
    assert entry["newest"] == "2026-09-02T00:00:00Z", "末条无 timestamp 时 newest 取错了"


def test_totals_are_asserted_and_unknown_is_not_counted_as_zero(client, monkeypatch, tmp_path):
    """顶层汇总字段必须有断言，且「未知」不得被压成「空」。"""
    jsonl = tmp_path / "failed_writes.jsonl"
    _write_jsonl(jsonl, [{"timestamp": "2026-09-01T00:00:00Z"}, {"timestamp": "2026-09-02T00:00:00Z"}])
    blob = tmp_path / "neo4j_memory.json"
    blob.write_text("{}", encoding="utf-8")
    for ts in ("2026-09-01-000000000001",):
        _write_jsonl(tmp_path / f"failed_writes.overflow.{ts}.jsonl", [{"a": 1}])
    monkeypatch.setattr(
        traces,
        "BACKLOG_FILES",
        {"failed_writes.jsonl": jsonl, "neo4j_memory.json": blob},
        raising=False,
    )
    body = client.get(BACKLOG_PATH).json()
    # 非 JSONL 链的 backlog 是 None（未知），不得被当 0 加进去，也不得让求和崩
    assert body["total_backlog"] == 2
    assert body["total_overflow_files"] == 1
    assert body["incomplete"] is False


# ═══════════════════════════════════════════════════════════════════════════
# Codex round-2 M1 / M2 / M3
# ═══════════════════════════════════════════════════════════════════════════


def test_permission_error_on_active_file_is_flagged_not_reported_as_absent(client, monkeypatch, tmp_path):
    """活动文件读不到（权限）⇒ 必须标降级，不得报成 exists=False / backlog=0。

    Python 3.14 的 `Path.exists()` 把 PermissionError 吞成 False，于是一个权限
    问题长得和「真的没有积压」一模一样 —— 正是本卡要修的那类 DD-13。
    """
    active = tmp_path / "failed_writes.jsonl"
    _write_jsonl(active, [{"timestamp": "2026-09-01T00:00:00Z"}])

    def _boom(p):
        raise PermissionError("no access")

    monkeypatch.setattr(traces, "_stat_or_error", lambda p: (None, f"stat:{type(PermissionError()).__name__}"))
    monkeypatch.setattr(traces, "BACKLOG_FILES", {"failed_writes.jsonl": active}, raising=False)

    body = client.get(BACKLOG_PATH).json()
    entry = body["files"][0]
    assert entry["partial"] is True, "权限问题被报成了完整结果"
    assert any(d.startswith("stat:") for d in entry["degraded"]), entry["degraded"]
    assert body["incomplete"] is True


def test_stat_or_error_distinguishes_absent_from_unreadable(tmp_path, monkeypatch):
    """`_stat_or_error` 的两条分支必须分开：不存在 ⇒ 无原因；读不到 ⇒ 带原因。"""
    missing = tmp_path / "nope.jsonl"
    assert traces._stat_or_error(missing) == (None, None)

    present = tmp_path / "failed_writes.jsonl"
    present.write_text("{}\n", encoding="utf-8")
    real_stat = type(present).stat

    def _boom(self, *a, **kw):
        if self == present:
            raise PermissionError("no access")
        return real_stat(self, *a, **kw)

    monkeypatch.setattr(type(present), "stat", _boom)
    st, err = traces._stat_or_error(present)
    assert st is None and err == "stat:PermissionError"


def test_lone_surrogate_timestamp_does_not_500_the_route(client, monkeypatch, tmp_path):
    """一条含孤立代理字符的记录不得让整条只读路由 500。

    `{"timestamp":"\\ud800"}` 是**合法** JSON；产出的字符一路活到响应序列化才抛
    UnicodeEncodeError，而那时已经出了 `_safe_backlog_entry` 的 try —— 降级机制
    接不住。死信文件正是系统出问题时写的，畸形内容是常态。
    """
    active = tmp_path / "failed_writes.jsonl"
    active.write_text('{"timestamp":"\\ud800"}\n', encoding="utf-8")
    monkeypatch.setattr(traces, "BACKLOG_FILES", {"failed_writes.jsonl": active}, raising=False)

    r = client.get(BACKLOG_PATH)
    assert r.status_code == 200, f"坏记录把整条路由打挂了: {r.status_code}"
    entry = r.json()["files"][0]
    assert entry["backlog"] == 1
    assert entry["oldest"] is not None


def test_utf8_safe_replaces_unencodable_and_keeps_normal_text():
    """验伪锚：清洗只动不可编码的码点，正常文本必须原样。"""
    assert traces._utf8_safe("2026-09-01T00:00:00Z") == "2026-09-01T00:00:00Z"
    assert traces._utf8_safe("中文 ok") == "中文 ok"
    cleaned = traces._utf8_safe("\ud800")
    cleaned.encode("utf-8")  # 不抛即为通过
    assert cleaned != "\ud800"


def test_scan_budget_stops_midway_when_file_grows_after_stat(tmp_path, monkeypatch):
    """尺寸闸必须在**读取过程中**也生效，不只是开扫前 stat 一次。

    交错：stat 时没超限 → 写者追加超长记录 → 扫描器才开始读。

    ⚠️ 这条门的第一版是**空壳**：它打桩的是 `traces._stat_or_error`，而
    `_first_last_timestamp` 自己还会 `path.stat()`；那次 stat 拿到真实大小、
    在**开扫前**就 size_capped 返回了，根本没进读循环 —— 负控摘掉字节预算后
    它照样绿。必须让**开扫前那次 stat** 也看到小尺寸，才逼得到读取期的预算。
    """
    active = tmp_path / "failed_writes.jsonl"
    long_ts = "2026-09-01T00:00:00Z" + "x" * 5000
    active.write_text(
        '{"timestamp":"2026-09-01T00:00:00Z"}\n' + json.dumps({"timestamp": long_ts}) + "\n",
        encoding="utf-8",
    )

    real_stat = type(active).stat

    class _SmallStat:
        st_size = 10  # 开扫前看到的尺寸：远小于闸
        st_mtime = 0.0

    def _fake_stat(self, *a, **kw):
        if self == active:
            return _SmallStat()
        return real_stat(self, *a, **kw)

    monkeypatch.setattr(type(active), "stat", _fake_stat)

    oldest, newest, reason = traces._first_last_timestamp(active, max_bytes=100)
    assert reason == "size_capped", f"读取期预算没生效, reason={reason!r}"
    assert newest != long_ts, "超长记录被整条读进来了"
    assert oldest == "2026-09-01T00:00:00Z", "预算耗尽前已读到的那条应当保留"


def test_scan_reads_at_most_max_bytes_from_disk(tmp_path, monkeypatch):
    """闸必须限制**实际从磁盘读取的字节数**，不是「读完整行再拒绝解析」。

    前两版都错在同一点：`for line in f` 在扣预算之前就把整行读进内存了。
    这条门直接盯**一次 read 拿了多少字节**。

    ⚠️ 必须同时把开扫前那次 stat 打成小尺寸 —— 否则它会在开扫前就
    size_capped 返回，二进制读根本不执行，`read_sizes` 为空，门测的是
    另一条路径（这个坑本卡已经踩过一次）。
    """
    active = tmp_path / "failed_writes.jsonl"
    huge = json.dumps({"timestamp": "2026-09-01T00:00:00Z" + "x" * 200_000})
    active.write_text(huge + "\n", encoding="utf-8")

    real_stat = type(active).stat

    class _Small:
        st_size = 10
        st_mtime = 0.0

    monkeypatch.setattr(
        type(active), "stat", lambda self, *a, **kw: _Small() if self == active else real_stat(self, *a, **kw)
    )

    read_sizes = []
    import builtins

    real_open = builtins.open

    class _CountingFile:
        def __init__(self, f):
            self._f = f

        def read(self, n=-1):
            data = self._f.read(n)
            read_sizes.append(len(data))
            return data

        def __enter__(self):
            return self

        def __exit__(self, *a):
            self._f.close()
            return False

    def _spy_open(file, mode="r", *a, **kw):
        f = real_open(file, mode, *a, **kw)
        if str(file) == str(active) and "b" in str(mode):
            return _CountingFile(f)
        return f

    monkeypatch.setattr(builtins, "open", _spy_open)
    _, _, reason = traces._first_last_timestamp(active, max_bytes=100)
    monkeypatch.setattr(builtins, "open", real_open)

    assert read_sizes, "没有走到二进制读取路径 —— 门测的是别的分支"
    assert max(read_sizes) <= 101, f"一次从磁盘读了 {max(read_sizes)} 字节, 上限是 100"
    assert reason == "size_capped"


def test_scan_budget_counts_bytes_not_characters(tmp_path, monkeypatch):
    """预算按**字节**算：多字节字符不得靠「字符数少」骗过闸。

    30 个 emoji 的 timestamp = 48 字符 / 138 字节；按字符算就会放行。
    """
    active = tmp_path / "failed_writes.jsonl"
    emoji_ts = "2026-09-01T00:00:00Z" + "😀" * 30
    active.write_text(json.dumps({"timestamp": emoji_ts}, ensure_ascii=False) + "\n", encoding="utf-8")
    size = active.stat().st_size
    assert size > 100, f"前置不成立: 文件才 {size} 字节"

    real_stat = type(active).stat

    class _Small:
        st_size = 10
        st_mtime = 0.0

    monkeypatch.setattr(
        type(active), "stat", lambda self, *a, **kw: _Small() if self == active else real_stat(self, *a, **kw)
    )
    _, _, reason = traces._first_last_timestamp(active, max_bytes=100)
    assert reason == "size_capped", f"按字符数算把 {size} 字节的内容放行了, reason={reason!r}"
