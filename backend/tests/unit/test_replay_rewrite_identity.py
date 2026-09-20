# CARD-REPLAY-REWRITE (BATCH-2026-09-18-第十五批) — 回灌算法重写单测（tmp 文件、不连库）
#
# 被测面（改写后契约）:
#   1. 写侧身份: failed_writes_constants.stamp_failed_write_identity / serialize_failed_write
#      + 三写者（agent_service._record_failed_write / memory_service._record_structured_outbox
#      / memory_service._flush_pending_failed_writes）落盘条目带 record_id/vault_id/schema_version
#   2. 回灌侧: 身份代替位置（legacy-hash 去重）、确认身份日志（崩溃恢复）、
#      来源 vault 只用条目自带值、缺 vault 隔离不猜、回执比对、overflow 代际扫回、
#      旧 _PROGRESS_VERSION 位置游标被忽略且别链键保留
#
# ⛔ DD-03 口径: 文件 IO 全真（tmp_path）; 只有 Neo4j 客户端边界是替身（同
#    test_story_38_8_fallback_sync.py 既有形态）——被测对象是算法与文件行为。

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import AsyncMock

import pytest

from app.services import fallback_sync_service as fss
from app.services.fallback_sync_service import FallbackSyncService

# ─────────────────────────────────────────────────────────────────────────
# 替身与工具
# ─────────────────────────────────────────────────────────────────────────


def _receipt_row(**kwargs: Any) -> Dict[str, Any]:
    """回执形状与生产查询 RETURN 对齐（should_update 支）。"""
    return {
        "should_update": True,
        "score_after": kwargs.get("score"),
        "group_after": kwargs.get("groupId"),
        "ts_equal": True,
        "ts_after_ts": False,
    }


def _make_client(*, fail_concepts: tuple = ()) -> tuple[AsyncMock, List[Dict[str, Any]]]:
    """Neo4j 客户端替身: run_query 回**回执**（按 kwargs 回显）, 二次写恒成功。"""
    calls: List[Dict[str, Any]] = []

    async def run_query(query: str, **kwargs: Any) -> List[Dict[str, Any]]:
        calls.append({"query": query, **kwargs})
        if kwargs.get("concept") in fail_concepts:
            row = _receipt_row(**kwargs)
            row["score_after"] = -999  # 回执与送入值不符 ⇒ 判失败
            return [row]
        return [_receipt_row(**kwargs)]

    client = AsyncMock()
    client.run_query = AsyncMock(side_effect=run_query)
    client.record_score_history_by_record_id = AsyncMock(return_value=True)
    return client, calls


def _entry(
    tag: str,
    *,
    vault: Any = "test_vault",
    ts: Any = "2026-09-19T10:00:00",
    score: Any = 80,
    with_id: bool = True,
    **extra: Any,
) -> Dict[str, Any]:
    entry: Dict[str, Any] = {
        "event_type": "scoring",
        "concept": f"concept_{tag}",
        "concept_id": f"cid_{tag}",
        "canvas_name": "test.canvas",
        "score": score,
        "timestamp": ts,
        "error_reason": "timeout",
    }
    if with_id:
        entry["record_id"] = f"rid_{tag}_{uuid.uuid4().hex[:8]}"
    if vault is not None:
        entry["vault_id"] = vault
    entry.update(extra)
    return entry


def _write_jsonl(path: Path, entries: List[Dict[str, Any]]) -> None:
    path.write_text("\n".join(json.dumps(e, ensure_ascii=False) for e in entries) + "\n", encoding="utf-8")


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").split("\n") if l.strip()]


@pytest.fixture
def env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """四条路径 + 确认身份日志全部落 tmp_path；清掉 legacy env。"""
    writes = tmp_path / "failed_writes.jsonl"
    monkeypatch.setattr(fss, "FAILED_WRITES_FILE", writes)
    monkeypatch.setattr(fss, "SYNC_CHECKPOINT_FILE", tmp_path / "sync_checkpoint.json")
    monkeypatch.setattr(fss, "SYNC_CONFIRMED_IDS_FILE", tmp_path / "sync_confirmed_ids.json", raising=False)
    monkeypatch.delenv("CLS_REPLAY_LEGACY_NOSCOPE_VAULT", raising=False)
    return {
        "writes": writes,
        "checkpoint": tmp_path / "sync_checkpoint.json",
        "confirmed": tmp_path / "sync_confirmed_ids.json",
        "tmp": tmp_path,
    }


def _confirmed_ids(env) -> Dict[str, Any]:
    path: Path = env["confirmed"]
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


# ─────────────────────────────────────────────────────────────────────────
# 1. 写侧身份戳（helpers + 三写者）
# ─────────────────────────────────────────────────────────────────────────


def test_stamp_adds_identity_fields_and_serialize_roundtrip():
    """stamp_failed_write_identity: 补 record_id/vault_id/group_id/recorded_at/schema_version。"""
    from app.core import failed_writes_constants as fwc

    stamp = getattr(fwc, "stamp_failed_write_identity", None)
    assert stamp is not None, "failed_writes_constants.stamp_failed_write_identity 未实现"

    entry = _entry("stamp", vault="cs_61b")
    out = stamp(dict(entry))
    assert out["record_id"], "record_id 未补"
    assert out["vault_id"] == "cs_61b"
    assert out["schema_version"] == 2
    assert out["recorded_at"], "recorded_at 未补"
    assert out["group_id"].startswith("vault:cs_61b"), f"group_id 形态不符: {out['group_id']!r}"
    # 幂等: 已有值不覆盖
    out2 = stamp(dict(out))
    assert out2["record_id"] == out["record_id"]

    serialize = getattr(fwc, "serialize_failed_write", None)
    assert serialize is not None, "failed_writes_constants.serialize_failed_write 未实现"
    roundtrip = json.loads(serialize(dict(entry)))
    assert roundtrip["record_id"] and roundtrip["schema_version"] == 2


def test_three_writers_stamp_identity(env, monkeypatch: pytest.MonkeyPatch):
    """三写者落盘条目都带 record_id / vault_id 键 / schema_version=2。"""
    from app.services import agent_service
    from app.services import memory_service as ms

    # ⚠️ 三个写者各读**自己模块**的 FAILED_WRITES_FILE 绑定副本（既有打桩口径），
    # 必须逐个打桩 —— 漏打一个就会把条目写进本树 backend/data/ 真文件。
    monkeypatch.setattr(agent_service, "FAILED_WRITES_FILE", env["writes"])
    monkeypatch.setattr(ms, "FAILED_WRITES_FILE", env["writes"])

    # 写者① agent_service._record_failed_write
    agent_service._record_failed_write(
        event_type="score_write",
        concept_id="cid_w1",
        canvas_name="test.canvas",
        score=88.0,
        error_reason="timeout",
        concept="C1",
    )
    # 写者② memory_service._record_structured_outbox（实例方法, 只走落盘分支）
    svc = ms.MemoryService.__new__(ms.MemoryService)
    assert svc._record_structured_outbox({"kind": "knowledge_entity", "concept": "C2"}) is True
    # 写者③ _flush_pending_failed_writes（tmp 组装 → 刷盘时打戳）
    svc2 = ms.MemoryService.__new__(ms.MemoryService)
    svc2._pending_failed_writes = [{"episode_id": "ep_w3", "timestamp": "2026-09-19T10:00:00Z", "reason": "Neo4j down"}]
    svc2._flush_pending_failed_writes()

    lines = _read_jsonl(env["writes"])
    assert len(lines) == 3, f"三写者应各落 1 条, 实得 {len(lines)}"
    for entry in lines:
        assert entry.get("record_id"), f"缺 record_id: {entry!r}"
        assert "vault_id" in entry, f"缺 vault_id 键: {entry!r}"
        assert entry.get("schema_version") == 2, f"schema_version != 2: {entry!r}"


# ─────────────────────────────────────────────────────────────────────────
# 2. 回灌侧: 身份代替位置 / legacy-hash 去重
# ─────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_legacy_hash_dedup_within_generation(env, monkeypatch: pytest.MonkeyPatch):
    """内容逐字相同的两条历史条目 = 同一条（legacy-hash 身份）⇒ 只重放一次。"""
    client, calls = _make_client()
    svc = FallbackSyncService(neo4j_client=client)

    # 历史条目无身份无 vault ⇒ 默认隔离; env 点名后按该 vault 归属（本用例只测身份去重）
    monkeypatch.setenv("CLS_REPLAY_LEGACY_NOSCOPE_VAULT", "cs_61b")
    dup = _entry("dup", vault=None, with_id=False)  # 无身份的历史条目
    other = _entry("other", vault=None, ts="2026-09-19T10:01:00", with_id=False)
    _write_jsonl(env["writes"], [dup, dup, other])

    stats = await svc._sync_failed_writes()

    assert stats.get("deduped") == 1, f"重复条目未被去重计数: {stats!r}"
    assert stats.get("recovered") == 2, f"应只重放两条不同身份: {stats!r}"
    concepts = [c["concept"] for c in calls]
    assert concepts.count("concept_dup") == 1, f"重复条目被重放多次: {concepts!r}"


# ─────────────────────────────────────────────────────────────────────────
# 3. 确认身份日志: 崩溃恢复（写日志与写回之间崩）不丢不重
# ─────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_confirmed_log_crash_between_log_and_rewrite(env, monkeypatch: pytest.MonkeyPatch):
    """崩溃点 = 确认日志已写、文件写回未发生: 重启不重放已确认者、不丢未确认者。"""
    writes: Path = env["writes"]
    e1, e2 = _entry("a"), _entry("b", ts="2026-09-19T10:01:00")
    e3, e4 = _entry("c", ts="2026-09-19T10:02:00"), _entry("d", ts="2026-09-19T10:03:00")
    _write_jsonl(writes, [e1, e2, e3, e4])

    # 第一轮: c/d 的回执不符 ⇒ 判失败留待; 随后在**文件写回**处注入崩溃
    client1, calls1 = _make_client(fail_concepts=("concept_c", "concept_d"))
    svc1 = FallbackSyncService(neo4j_client=client1)
    # ⚠️ 还原必须用 staticmethod 描述符本身：把裸函数装回类属性会让它退化成
    # 普通方法（self 被当作 path 传入），production 语义被破坏。
    original_descriptor = fss.FallbackSyncService.__dict__["_atomic_write_file"]
    original_atomic = original_descriptor.__func__

    def crashing_atomic(self, path: Path, content: str) -> None:
        if Path(path) == writes:
            raise OSError("simulated crash before rewrite")
        return original_atomic(path, content)

    monkeypatch.setattr(fss.FallbackSyncService, "_atomic_write_file", crashing_atomic)
    with pytest.raises(OSError):
        await svc1._sync_failed_writes()

    # 日志已写 a/b（先记日志再进下一条）; 文件未被改写
    log = _confirmed_ids(env)
    gen = writes.name
    assert set(log.get(gen, [])) == {e1["record_id"], e2["record_id"]}, f"确认日志不符: {log!r}"
    assert len(_read_jsonl(writes)) == 4, "崩溃前文件不应被改写"

    # 第二轮: 撤掉崩溃注入, c/d 回执恢复
    monkeypatch.setattr(fss.FallbackSyncService, "_atomic_write_file", original_descriptor)
    client2, calls2 = _make_client()
    svc2 = FallbackSyncService(neo4j_client=client2)
    stats2 = await svc2._sync_failed_writes()

    replayed2 = [c["concept"] for c in calls2]
    assert replayed2 == ["concept_c", "concept_d"], f"第二轮重放了已确认者或漏了未确认者: {replayed2!r}"
    assert stats2.get("recovered") == 2
    assert stats2.get("confirmed") == 4, f"confirmed 应含日志里的 2 条 + 本轮 2 条: {stats2!r}"
    assert stats2.get("pending") == 0, f"全部确认后 pending 应为 0: {stats2!r}"
    assert not writes.exists(), "全部确认后活动文件应被轮转走"
    assert not _confirmed_ids(env), "finalize 后该代日志应被清掉"


# ─────────────────────────────────────────────────────────────────────────
# 4. 旧位置游标被忽略; 别链键保留
# ─────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_old_progress_checkpoint_ignored_other_keys_kept(env):
    """旧 _PROGRESS_VERSION 的 failed_writes 位置游标被忽略（不跳条）; 别链键保留。"""
    from app.services.fallback_sync_service import _PROGRESS_VERSION

    entries = [_entry(f"n{i}", ts=f"2026-09-19T10:{i:02d}:00") for i in range(4)]
    _write_jsonl(env["writes"], entries)

    # 种一个**当前位置语义版本**的旧游标（index=3）+ 别链（learning_memories）键
    env["checkpoint"].write_text(
        json.dumps(
            {
                "failed_writes": {"index": 3, "progress_version": _PROGRESS_VERSION, "updated_at": "x"},
                "learning_memories": {"index": 7, "progress_version": _PROGRESS_VERSION, "updated_at": "x"},
            }
        ),
        encoding="utf-8",
    )

    client, calls = _make_client()
    svc = FallbackSyncService(neo4j_client=client)
    stats = await svc._sync_failed_writes()

    assert len(calls) == 4, f"位置游标不应再被读取（4 条全重放）: {[c['concept'] for c in calls]!r}"
    assert stats.get("recovered") == 4

    ckpt = json.loads(env["checkpoint"].read_text(encoding="utf-8")) if env["checkpoint"].exists() else {}
    assert "learning_memories" in ckpt, f"别链的键被误删: {ckpt!r}"


# ─────────────────────────────────────────────────────────────────────────
# 5. 来源 vault: 条目自带值优先; 缺 vault 默认隔离
# ─────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_entry_vault_wins_over_active_vault(env):
    """条目带 vault_id ⇒ 组按**条目**的 vault 构造, 不看进程 active vault。"""
    from app.core.subject_config import build_vault_group_id
    from app.graphiti.group_id_compat import to_physical_group_id

    entry = _entry("vaulted", vault="cs_61b")
    _write_jsonl(env["writes"], [entry])

    client, calls = _make_client()
    svc = FallbackSyncService(neo4j_client=client)
    stats = await svc._sync_failed_writes()

    assert stats.get("recovered") == 1
    expected = to_physical_group_id(build_vault_group_id("cs_61b", canvas_path="test.canvas"))
    assert calls and calls[0]["groupId"] == expected, f"组未按条目 vault 构造: {calls[0]['groupId']!r} != {expected!r}"


@pytest.mark.asyncio
async def test_quarantine_legacy_without_vault(env, monkeypatch: pytest.MonkeyPatch):
    """缺 vault 的历史条目默认隔离: 不写图、留文件、quarantined 计数; env 点名才归属。"""
    entry = _entry("legacy", vault=None, with_id=False)  # 纯历史条目: 无身份无来源
    _write_jsonl(env["writes"], [entry])

    client, calls = _make_client()
    svc = FallbackSyncService(neo4j_client=client)
    stats = await svc._sync_failed_writes()

    assert calls == [], f"被隔离的条目不应发生任何图写入: {calls!r}"
    assert stats.get("quarantined") == 1, f"quarantined 计数不符: {stats!r}"
    assert stats.get("pending") == 1, "被隔离的条目应留在文件（计 pending）"
    assert len(_read_jsonl(env["writes"])) == 1, "被隔离的条目必须留在文件里"

    # env 显式点名 ⇒ 按该 vault 归属（重跑同一文件）
    monkeypatch.setenv("CLS_REPLAY_LEGACY_NOSCOPE_VAULT", "cs_61b")
    client2, calls2 = _make_client()
    svc2 = FallbackSyncService(neo4j_client=client2)
    stats2 = await svc2._sync_failed_writes()
    assert stats2.get("recovered") == 1, f"env 点名后应重放: {stats2!r}"
    assert calls2 and calls2[0]["groupId"].startswith("vault__cs_61b"), f"env 归属组不符: {calls2!r}"


# ─────────────────────────────────────────────────────────────────────────
# 6. 回执比对: 不符判失败留待
# ─────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_receipt_mismatch_keeps_pending(env):
    """回执与送入值不符（写后属性对不上）⇒ 整条判失败, 留在文件。"""
    entry = _entry("mismatch")
    _write_jsonl(env["writes"], [entry])

    client, calls = _make_client(fail_concepts=("concept_mismatch",))
    svc = FallbackSyncService(neo4j_client=client)
    stats = await svc._sync_failed_writes()

    assert stats.get("recovered") == 0, f"回执不符不应算成功: {stats!r}"
    assert stats.get("pending") == 1
    assert len(_read_jsonl(env["writes"])) == 1, "回执不符的条目必须留待重试"


@pytest.mark.asyncio
async def test_receipt_conflict_requires_graph_newer(env):
    """should_update=false 支: 图上时间戳确实更新 ⇒ 成功; 否则失败留待。"""
    entry = _entry("conflict", ts="2026-09-01T10:00:00")
    _write_jsonl(env["writes"], [entry])

    # 分支 A: 图上更新（ts_after_ts=True）⇒ 让位成功
    async def run_query_ok(query: str, **kwargs: Any):
        return [
            {
                "should_update": False,
                "score_after": 99,
                "group_after": kwargs.get("groupId"),
                "ts_equal": False,
                "ts_after_ts": True,
            }
        ]

    client_a = AsyncMock()
    client_a.run_query = AsyncMock(side_effect=run_query_ok)
    client_a.record_score_history_by_record_id = AsyncMock(return_value=True)
    svc_a = FallbackSyncService(neo4j_client=client_a)
    stats_a = await svc_a._sync_failed_writes()
    assert stats_a.get("recovered") == 1, f"图上更新时应判成功: {stats_a!r}"

    # 分支 B: 图上并不更新（ts_after_ts=False）⇒ 不能确认, 留待
    _write_jsonl(env["writes"], [entry])

    async def run_query_bad(query: str, **kwargs: Any):
        return [
            {
                "should_update": False,
                "score_after": 99,
                "group_after": kwargs.get("groupId"),
                "ts_equal": False,
                "ts_after_ts": False,
            }
        ]

    client_b = AsyncMock()
    client_b.run_query = AsyncMock(side_effect=run_query_bad)
    client_b.record_score_history_by_record_id = AsyncMock(return_value=True)
    svc_b = FallbackSyncService(neo4j_client=client_b)
    stats_b = await svc_b._sync_failed_writes()
    assert stats_b.get("recovered") == 0, f"图上未更新却判成功: {stats_b!r}"
    assert stats_b.get("pending") == 1


# ─────────────────────────────────────────────────────────────────────────
# 7. overflow 代际扫回
# ─────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_overflow_generation_swept_and_rotated(env):
    """overflow 代际条目回灌后被扫回: 全部确认 ⇒ 该代改名 .synced.*。"""
    writes: Path = env["writes"]
    gen = writes.parent / "failed_writes.overflow.2026-09-19-120000000000-00.jsonl"
    _write_jsonl(gen, [_entry("o1"), _entry("o2", ts="2026-09-19T10:01:00")])

    client, calls = _make_client()
    svc = FallbackSyncService(neo4j_client=client)
    stats = await svc._sync_failed_writes()

    assert stats.get("generations") == 1, f"generations 计数不符: {stats!r}"
    assert stats.get("recovered") == 2, f"overflow 代际未被扫回: {stats!r}"
    assert not gen.exists(), "全部确认的 overflow 代际应被轮转走"
    synced = list(writes.parent.glob("failed_writes.overflow.*.synced.*"))
    assert synced, "未见 .synced.* 产物"


# ─────────────────────────────────────────────────────────────────────────
# 8. 复核整改（Codex r1）：缺 ts+score 不确认 / 坏 score 不阻代 / 未知不外泄
# ─────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_no_ts_with_score_stays_pending(env):
    """缺 timestamp 且带 score ⇒ 不写评分历史也不确认（整条留待, fail-closed）。"""
    entry = _entry("nots", ts=None)
    _write_jsonl(env["writes"], [entry])

    client, calls = _make_client()
    svc = FallbackSyncService(neo4j_client=client)
    stats = await svc._sync_failed_writes()

    assert stats.get("recovered") == 0, f"缺时间戳且带 score 不应被确认: {stats!r}"
    assert stats.get("pending") == 1
    assert client.record_score_history_by_record_id.call_count == 0, "不应写出无事件时间的评分历史"
    assert len(_read_jsonl(env["writes"])) == 1, "条目必须留在文件"


@pytest.mark.asyncio
async def test_unconvertible_score_stays_pending_without_blocking_others(env):
    """score 不可转 int ⇒ 该条留待、其余照常（不中断整代）。"""
    bad = _entry("bado", score="not-a-number")
    good = _entry("goodo", ts="2026-09-19T10:01:00")
    _write_jsonl(env["writes"], [bad, good])

    client, calls = _make_client()
    svc = FallbackSyncService(neo4j_client=client)
    stats = await svc._sync_failed_writes()

    assert stats.get("recovered") == 1, f"坏 score 不应阻断后续条目: {stats!r}"
    assert stats.get("pending") == 1
    assert [c["concept"] for c in calls] == ["concept_goodo"], f"坏条目不应发生图写入: {calls!r}"


@pytest.mark.asyncio
async def test_overflow_unreadable_propagates_unknown(env):
    """overflow 代际读不出来 ⇒ 顶层 pending=-1 + error（未知不与已知相加）。"""
    import os as _os

    gen = env["tmp"] / "failed_writes.overflow.2026-09-19-120000000000-00.jsonl"
    _write_jsonl(gen, [_entry("u1")])
    good = _entry("u2", ts="2026-09-19T10:01:00")
    _write_jsonl(env["writes"], [good])
    _os.chmod(gen, 0o000)

    try:
        client, calls = _make_client()
        svc = FallbackSyncService(neo4j_client=client)
        stats = await svc._sync_failed_writes()
    finally:
        _os.chmod(gen, 0o644)

    assert stats.get("pending") == -1, f"overflow 未知应传播为 pending=-1: {stats!r}"
    assert "error" in stats, f"未知应带 error: {stats!r}"
    assert stats.get("recovered") == 1, f"活动文件仍应照常回灌: {stats!r}"
