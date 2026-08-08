# RAG-S1-2026-08-02 阶段 1 索引重写 — 契约测试（四组，§九 反推重建）
#
# 组 A 写侧正确性: per-path pending 语义 / 参数同源 / 删除改名 / 黑名单
# 组 B API 诚实: 结构化状态不撒谎 / freshness 遥测
# 组 C SLO (真 LanceDB tmp 库): 新增/修改/删除/停机补齐 一轮 reconcile 内生效
# 组 D 防回潮: FTS 必产出 / pending 以 path 为 key / B0.7 不漂移
#
# 测试基建: LanceDB 用 tmp_path 真库 (vault_id="testvault" 显式隔离);
# embedding 用 _ollama_embed_batch 测试替身 (确定性 1024 维向量) —— 检验的是
# 索引编排正确性, 不是 bge-m3 的向量质量。
#
# [Source: _bmad-output/研究/2026-08-02-RAG阶段1-索引重写实施计划.md §六]

import asyncio
from pathlib import Path

import pytest

from app.config import settings
from app.services.vault_index_orchestrator import VaultIndexOrchestrator


# ═══════════════════════════════════════════════════════════════════════════════
# fixtures
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def tmp_vault(tmp_path):
    """Minimal vault with the canonical flat layout."""
    vault = tmp_path / "vault"
    (vault / "节点").mkdir(parents=True)
    (vault / "检验白板").mkdir()
    return vault


async def _fixed_vectors(self, texts):
    """Deterministic 1024-d embedding double (indexing-orchestration tests
    verify plumbing, not vector quality)."""
    return [[0.1] * 1024 for _ in texts]


@pytest.fixture
def orch(tmp_vault, tmp_path, monkeypatch):
    """Orchestrator wired to a REAL LanceDB in tmp_path with a test-double
    embedder and an isolated pending file."""
    from agentic_rag.clients.lancedb_client import LanceDBClient

    monkeypatch.setattr(LanceDBClient, "_ollama_embed_batch", _fixed_vectors)

    client = LanceDBClient(db_path=str(tmp_path / "db"), vault_id="testvault")
    assert client.connect_lightweight() is True

    o = VaultIndexOrchestrator(vault_path=str(tmp_vault))
    o._client = client
    o._pending_file = tmp_path / "pending.jsonl"
    return o


def _write_note(vault: Path, rel: str, content: str) -> Path:
    p = vault / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p


def _table_paths(orch_obj) -> list:
    """All canvas_file values currently in the notes table."""
    client = orch_obj._client
    table = client.resolve_table_name("vault_notes")
    if table not in client._db.table_names():
        return []
    return list(client._db.open_table(table).to_pandas()["canvas_file"])


# ═══════════════════════════════════════════════════════════════════════════════
# 组 A — 写侧正确性
# ═══════════════════════════════════════════════════════════════════════════════


async def test_a1_same_path_coalesces_to_one_entry(orch):
    assert orch.enqueue("upsert", "节点/a.md") == "accepted"
    assert orch.enqueue("upsert", "节点/a.md") == "coalesced"
    assert len(orch._pending) == 1


async def test_a2_different_paths_never_cancel_each_other(orch):
    assert orch.enqueue("upsert", "节点/a.md") == "accepted"
    assert orch.enqueue("upsert", "节点/b.md") == "accepted"
    assert orch.enqueue("upsert", "节点/c.md") == "accepted"
    # 旧实现: 整 vault 单 coalesce key, 后到者 cancel 前者 (ChatGPT 反证 #1)
    assert set(orch._pending.keys()) == {"节点/a.md", "节点/b.md", "节点/c.md"}


async def test_a3_event_during_inflight_marks_dirty_and_replays(orch, tmp_vault):
    _write_note(tmp_vault, "节点/a.md", "# A\n\nv1")
    orch.enqueue("upsert", "节点/a.md")
    entry = orch._pending["节点/a.md"]
    entry.state = "in_flight"  # simulate worker mid-index

    assert orch.enqueue("upsert", "节点/a.md") == "coalesced"
    assert entry.dirty is True, "索引中新事件必须标 dirty, 不许静默丢弃"

    entry.state = "pending"  # release for processing
    await orch.process_batch()
    # dirty 重放: 第一轮完成后 entry 回 pending 而非被移除
    assert "节点/a.md" in orch._pending
    assert orch._pending["节点/a.md"].state == "pending"
    assert orch._pending["节点/a.md"].dirty is False


async def test_a4_pending_survives_restart(orch, tmp_vault, tmp_path):
    orch.enqueue("upsert", "节点/a.md")
    orch._pending["节点/a.md"].state = "in_flight"
    orch._persist_sync()

    fresh = VaultIndexOrchestrator(vault_path=str(tmp_vault))
    fresh._pending_file = tmp_path / "pending.jsonl"
    recovered = fresh.recover()

    assert recovered == 1
    assert "节点/a.md" in fresh._pending
    # 崩溃时 in_flight 的意图必须重放 (delete-before-insert 使重放幂等)
    assert fresh._pending["节点/a.md"].state == "pending"


def test_a5_chunk_params_single_source(orch):
    assert orch._chunk_size == settings.VAULT_INDEX_CHUNK_SIZE
    assert orch._chunk_overlap == settings.VAULT_INDEX_OVERLAP


def test_a6_filename_blacklist_applies(orch):
    ok, reason = orch.should_index("节点/CLAUDE.md")
    assert (ok, reason) == (False, "blacklisted_file")


def test_a7_subject_matches_full_scan_derivation(orch):
    from app.config import get_current_vault_id, sanitize_vault_id
    from app.core.subject_config import build_vault_group_id

    expected = build_vault_group_id(sanitize_vault_id(get_current_vault_id()))
    assert orch._subject() == expected
    assert expected.startswith("vault:")


async def test_a8_delete_op_clears_chunks_and_fingerprint(orch, tmp_vault):
    _write_note(tmp_vault, "节点/a.md", "# A\n\n内容一二三")
    orch.enqueue("upsert", "节点/a.md")
    await orch.process_batch()
    assert "节点/a.md" in _table_paths(orch)
    assert "节点/a.md" in orch._client._get_all_fingerprints()

    orch.enqueue("delete", "节点/a.md")
    await orch.process_batch()
    assert "节点/a.md" not in _table_paths(orch)
    assert "节点/a.md" not in orch._client._get_all_fingerprints()


async def test_a9_rename_leaves_no_ghost_chunks(orch, tmp_vault):
    p = _write_note(tmp_vault, "节点/old.md", "# Old\n\n同一份内容")
    orch.enqueue("upsert", "节点/old.md")
    await orch.process_batch()
    assert "节点/old.md" in _table_paths(orch)

    p.rename(tmp_vault / "节点" / "new.md")
    # rename = 一次 reconcile 视角下的 deleted + new
    await orch.reconcile()
    await orch.process_batch()

    paths = _table_paths(orch)
    assert "节点/old.md" not in paths, "旧路径幽灵 chunk 必须清除"
    assert "节点/new.md" in paths


def test_a10_blacklist_copies_stay_identical():
    """settings (app 权威源) 与 lib 兜底常量必须内容一致 — lib 不能 import
    app, 物理上无法单源, 此测试就是防漂移的锁。"""
    from agentic_rag.clients.lancedb_client import DEFAULT_VAULT_SKIP_DIRS

    settings_dirs = {d.strip() for d in settings.VAULT_INDEX_SKIP_DIRS.split(",")}
    assert settings_dirs == set(DEFAULT_VAULT_SKIP_DIRS)


def test_a11_chunks_and_quarantine_excluded():
    dirs = {d.strip() for d in settings.VAULT_INDEX_SKIP_DIRS.split(",")}
    assert "chunks" in dirs, "chunks/merged.md 双份冗余必须排除"
    assert ".quarantine" in dirs


async def test_a13_empty_output_files_do_not_loop_forever(orch, tmp_vault):
    """空产出文件 (空内容 / 剥样板后无正文) 必须登记指纹 — 否则每轮
    reconcile 重判 new 形成永动循环 (live 实测 6 文件 × 60s 抓获)。"""
    _write_note(tmp_vault, "节点/empty.md", "")
    r1 = await orch.reconcile()
    assert r1["new"] == 1
    await orch.process_batch()
    # 指纹已登记 (chunk_count=0), 第二轮不得再判 new
    assert "节点/empty.md" in orch._client._get_all_fingerprints()
    r2 = await orch.reconcile()
    assert r2["new"] == 0 and r2["changed"] == 0

    # 内容从有到空: 旧行必须被清掉
    _write_note(tmp_vault, "节点/shrink.md", "# S\n\n有内容")
    await orch.reconcile()
    await orch.process_batch()
    assert "节点/shrink.md" in _table_paths(orch)
    _write_note(tmp_vault, "节点/shrink.md", "")
    await orch.reconcile()
    await orch.process_batch()
    assert "节点/shrink.md" not in _table_paths(orch)


def test_a12_fingerprint_table_is_vault_scoped(orch):
    client = orch._client
    assert client._fingerprint_table_name == "testvault_file_fingerprints"
    # _cache_tables 的维度检查必须跳过前缀化后的指纹表 (否则冷启动 drop 它)
    import inspect

    from agentic_rag.clients.lancedb_client import LanceDBClient

    src = inspect.getsource(LanceDBClient._cache_tables)
    assert "endswith" in src and "FINGERPRINT_TABLE" in src


# ═══════════════════════════════════════════════════════════════════════════════
# 组 B — API 诚实
# ═══════════════════════════════════════════════════════════════════════════════


async def test_b1_disabled_reports_disabled_not_scheduled(monkeypatch):
    import app.api.v1.endpoints.index as index_module
    import app.services.vault_index_orchestrator as orch_module
    from app.api.v1.endpoints.index import (
        RefreshChangedRequest,
        refresh_changed_paths,
    )

    monkeypatch.setattr(orch_module, "get_vault_index_orchestrator", lambda: None)

    resp = await refresh_changed_paths(RefreshChangedRequest(paths=["节点/a.md", "节点/b.md"]))
    assert resp.orchestrator_enabled is False
    assert resp.accepted == 0
    assert all(r.status == "disabled" for r in resp.results)
    # 旧假成功契约不得回潮
    assert not hasattr(resp, "scheduled")


async def test_b2_b3_structured_per_path_status(orch, monkeypatch):
    import app.services.vault_index_orchestrator as orch_module
    from app.api.v1.endpoints.index import (
        RefreshChangedRequest,
        refresh_changed_paths,
    )

    monkeypatch.setattr(orch_module, "get_vault_index_orchestrator", lambda: orch)

    resp = await refresh_changed_paths(RefreshChangedRequest(paths=["节点/a.md", "检验白板/exam.md", "节点/a.md"]))
    assert resp.orchestrator_enabled is True
    assert resp.accepted == 1  # 节点/a.md 首次
    assert resp.coalesced == 1  # 节点/a.md 重复
    assert resp.excluded == 1  # 检验白板 信息隔离
    by_path = {(r.path, r.status) for r in resp.results}
    assert ("检验白板/exam.md", "excluded") in by_path


def test_b5_freshness_fields_present(orch):
    f = orch.freshness()
    for key in (
        "last_index_at",
        "last_reconcile_at",
        "pending_depth",
        "lag_seconds",
        "stale",
    ):
        assert key in f
    assert f["stale"] is False


def test_b6_stale_when_lag_exceeds_threshold(orch):
    from datetime import datetime, timedelta, timezone

    orch.enqueue("upsert", "节点/a.md")
    old = datetime.now(timezone.utc) - timedelta(seconds=orch._stale_after + 60)
    orch._pending["节点/a.md"].enqueued_at = old.isoformat()

    f = orch.freshness()
    assert f["lag_seconds"] > orch._stale_after
    assert f["stale"] is True


# ═══════════════════════════════════════════════════════════════════════════════
# 组 C — SLO (真库端到端: 一轮 reconcile + 一轮 batch 内生效)
# ═══════════════════════════════════════════════════════════════════════════════


async def test_c1_new_file_searchable_after_one_reconcile(orch, tmp_vault):
    _write_note(tmp_vault, "节点/特征值.md", "# 特征值\n\nAv = λv 的缩放因子")
    result = await orch.reconcile()
    assert result["new"] == 1
    await orch.process_batch()
    assert "节点/特征值.md" in _table_paths(orch)


async def test_c2_modified_file_content_updates(orch, tmp_vault):
    _write_note(tmp_vault, "节点/a.md", "# A\n\n旧内容")
    await orch.reconcile()
    await orch.process_batch()

    _write_note(tmp_vault, "节点/a.md", "# A\n\n新内容已经替换")
    result = await orch.reconcile()
    assert result["changed"] == 1
    await orch.process_batch()

    client = orch._client
    table = client.resolve_table_name("vault_notes")
    df = client._db.open_table(table).to_pandas()
    contents = " ".join(df[df["canvas_file"] == "节点/a.md"]["content"])
    assert "新内容已经替换" in contents
    assert "旧内容" not in contents


async def test_c3_deleted_file_not_searchable(orch, tmp_vault):
    p = _write_note(tmp_vault, "节点/a.md", "# A\n\n内容")
    await orch.reconcile()
    await orch.process_batch()
    assert "节点/a.md" in _table_paths(orch)

    p.unlink()
    result = await orch.reconcile()
    assert result["deleted"] == 1
    await orch.process_batch()
    assert "节点/a.md" not in _table_paths(orch)


async def test_c4_startup_reconciliation_catches_offline_changes(orch, tmp_vault, tmp_path):
    """停机期间的变更 (orchestrator 不在场时写的文件) 由启动首轮补齐。"""
    _write_note(tmp_vault, "节点/downtime.md", "# 停机期间新增\n\n内容")

    fresh = VaultIndexOrchestrator(vault_path=str(tmp_vault))
    fresh._client = orch._client
    fresh._pending_file = tmp_path / "pending2.jsonl"
    fresh.recover()
    await fresh.reconcile()
    await fresh.process_batch()
    assert "节点/downtime.md" in _table_paths(fresh)


# ═══════════════════════════════════════════════════════════════════════════════
# 组 D — 防回潮
# ═══════════════════════════════════════════════════════════════════════════════


async def test_d1_batch_write_rebuilds_fts_once(orch, tmp_vault, monkeypatch):
    calls = {"n": 0}
    real_rebuild = orch._client._rebuild_fts_index

    def counting_rebuild(table_name):
        calls["n"] += 1
        return real_rebuild(table_name)

    monkeypatch.setattr(orch._client, "_rebuild_fts_index", counting_rebuild)

    _write_note(tmp_vault, "节点/a.md", "# A\n\n甲")
    _write_note(tmp_vault, "节点/b.md", "# B\n\n乙")
    await orch.reconcile()
    await orch.process_batch()

    assert calls["n"] == 1, "FTS 必须每批一次 (旧实现每文件全表重建一次)"


async def test_d2_refresh_changed_reaches_lancedb(orch, tmp_vault, monkeypatch):
    """端到端: 端点 enqueue → worker → 真库有行。锁死旧空转链
    (schedule_note_index 只刷 wikilink 图, 零 LanceDB 写入)。"""
    import app.services.vault_index_orchestrator as orch_module
    from app.api.v1.endpoints.index import (
        RefreshChangedRequest,
        refresh_changed_paths,
    )

    monkeypatch.setattr(orch_module, "get_vault_index_orchestrator", lambda: orch)
    _write_note(tmp_vault, "节点/via_endpoint.md", "# E\n\n经端点入库")

    resp = await refresh_changed_paths(RefreshChangedRequest(paths=["节点/via_endpoint.md"]))
    assert resp.accepted == 1
    await orch.process_batch()
    assert "节点/via_endpoint.md" in _table_paths(orch)


def test_d3_pending_keyed_by_rel_path(orch):
    orch.enqueue("upsert", "节点/x.md")
    orch.enqueue("delete", "节点/y.md")
    assert set(orch._pending.keys()) == {"节点/x.md", "节点/y.md"}
    # delete 永不被黑名单排除 (历史行可能存在, 清理必须永远可行)
    assert orch.enqueue("delete", "检验白板/old.md") == "accepted"


async def test_d4_resolve_prefers_prefixed_table(orch, tmp_vault):
    _write_note(tmp_vault, "节点/a.md", "# A\n\n内容")
    await orch.reconcile()
    await orch.process_batch()
    client = orch._client
    assert client.resolve_table_name("vault_notes") == "testvault_vault_notes"


async def test_d6_orphan_sweep_purges_rows_blacklisted_after_indexing(orch, tmp_vault, monkeypatch):
    """黑名单变更后的旧行必须被 reconcile 的 orphan sweep 清除 — 指纹 diff
    看不见「入库时合法、现在被排除」的行 (live 库 chunks/merged.md 时代旧行
    正是此形态), 收敛保证: 表内容 ⊆ 当前应索引集。"""
    _write_note(tmp_vault, "旧目录/legacy.md", "# L\n\n入库时还合法的内容")
    orch.enqueue("upsert", "旧目录/legacy.md")
    await orch.process_batch()
    assert "旧目录/legacy.md" in _table_paths(orch)

    # 模拟黑名单演化: 旧目录 事后被加入排除清单
    monkeypatch.setattr(orch, "_skip_dirs", orch._skip_dirs + ["旧目录"])
    await orch.reconcile()
    await orch.process_batch()
    assert "旧目录/legacy.md" not in _table_paths(orch), "被黑名单排除的历史行必须被 orphan sweep 清除"


async def test_d5_incremental_endpoint_enforces_blacklist(orch, tmp_vault):
    """增量端点与 orchestrator 共用同一套原语防线: index_single_file 内部
    强制目录+文件名黑名单, 黑名单路径 0 chunks 入库。"""
    _write_note(tmp_vault, "检验白板/exam.md", "# 考题\n\n答案不许回流")
    count = await orch._client.index_single_file(
        file_path=str(tmp_vault / "检验白板" / "exam.md"),
        table_name="vault_notes",
        vault_path=str(tmp_vault),
    )
    assert count == 0
    assert "检验白板/exam.md" not in _table_paths(orch)


# ═══════════════════════════════════════════════════════════════════════════════
# 组 E — Code-Review 修复锁 (RAG-S1 对抗审查 H1/H2/H3/M1/M3)
# ═══════════════════════════════════════════════════════════════════════════════


async def test_e1_embed_outage_is_loud_not_silent_success(orch, tmp_vault, monkeypatch):
    """H1: embed 双路全挂必须 raise 进重试通道 — 旧行为 return 0 被记成功,
    指纹不写 → 每轮重判 new → freshness 全绿而零行写入 (冻结模式重生)。"""
    from agentic_rag.clients.lancedb_client import LanceDBClient

    async def _ollama_down(self, texts):
        return None

    async def _no_cpu(self):
        self._vectorizer = None

    monkeypatch.setattr(LanceDBClient, "_ollama_embed_batch", _ollama_down)
    monkeypatch.setattr(LanceDBClient, "_init_vectorizer", _no_cpu)

    _write_note(tmp_vault, "节点/a.md", "# A\n\n内容")
    orch.enqueue("upsert", "节点/a.md")
    await orch.process_batch()

    entry = orch._pending.get("节点/a.md")
    assert entry is not None, "embed 故障的条目不得被当成功清除"
    assert entry.attempts == 1
    assert entry.next_retry_at != "", "必须进入退避重试通道"
    f = orch.freshness()
    assert f["pending_depth"] >= 1, "freshness 不得在零写入时报全绿"


async def test_e2_short_write_never_commits_fingerprint(orch, tmp_vault, monkeypatch):
    """H2: add_documents 短写/失败时禁止写指纹 — 否则旧行已删+指纹说已索引
    = 内容永久静默丢失直到下次编辑。"""
    from agentic_rag.clients.lancedb_client import LanceDBClient

    async def _swallowed_failure(self, table_name, documents):
        return 0  # add_documents 的真实失败形态: 吞异常返回 0

    monkeypatch.setattr(LanceDBClient, "add_documents", _swallowed_failure)

    _write_note(tmp_vault, "节点/a.md", "# A\n\n内容")
    orch.enqueue("upsert", "节点/a.md")
    await orch.process_batch()

    assert "节点/a.md" not in orch._client._get_all_fingerprints(), "写失败后指纹绝不能落库"
    entry = orch._pending.get("节点/a.md")
    assert entry is not None and entry.attempts == 1


def test_e3_default_vault_listing_excludes_prefixed_fingerprints(orch):
    """H3: default vault 的表清单不得含其他 vault 的前缀指纹表 —
    否则 DELETE /index/default 一次抹掉所有 vault 的变更检测。"""
    client = orch._client
    client._update_fingerprint("节点/x.md", "hash1", 1)  # 建 testvault_file_fingerprints
    default_tables = client.list_vault_tables(None)
    assert "testvault_file_fingerprints" not in default_tables


async def test_e4_backoff_survives_reconcile_but_user_event_resets(orch, tmp_vault, monkeypatch):
    """M1: reconcile 的重复 enqueue 不得清退避 (毒文件否则每轮重试 3 次);
    真实用户事件 (reset_backoff=True) 立即复活。"""
    from datetime import datetime, timedelta, timezone

    orch.enqueue("upsert", "节点/poison.md")
    entry = orch._pending["节点/poison.md"]
    entry.attempts = 3
    entry.state = "failed"
    future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    entry.next_retry_at = future

    # reconcile 形态的 enqueue (默认 reset_backoff=False): 退避保持
    assert orch.enqueue("upsert", "节点/poison.md") == "coalesced"
    assert entry.next_retry_at == future
    assert entry.state == "failed"
    # 退避未到期: 不进批
    result = await orch.process_batch()
    assert result["processed"] == 0

    # 用户事件: 立即复活
    orch.enqueue("upsert", "节点/poison.md", reset_backoff=True)
    assert entry.next_retry_at == ""
    assert entry.state == "pending"
    assert entry.attempts == 0


def test_e5_path_traversal_excluded(orch):
    """M3: 旧空转链下无害的穿越路径, 新链路真写库 — 必须拒绝。"""
    assert orch.enqueue("upsert", "../../其他库/x.md") == "excluded"
    assert orch.enqueue("upsert", "/etc/passwd.md") == "excluded"
    assert orch.enqueue("delete", "../escape.md") == "excluded"
    assert orch.enqueue("upsert", "节点/../检验白板/exam.md") == "excluded"
    # normpath 后合法的仍放行
    assert orch.enqueue("upsert", "节点/./a.md") == "accepted"
    assert "节点/a.md" in orch._pending


# ═══════════════════════════════════════════════════════════════════════════════
# 组 G — 观测层加固锁 (2026-08-09 假停摆误诊事后修正)
# 背景: UTC 时间戳被按本地时间解读, 制造了一次不存在的「7 小时停摆」误诊。
# 教训固化: 相对时间量 + 逐 task 状态 + scan 死亡独立维度 + 黑名单可观测。
# ═══════════════════════════════════════════════════════════════════════════════


def _utcnow_for_test():
    from datetime import datetime, timezone

    return datetime.now(timezone.utc)


def test_g1_freshness_reports_relative_ages_and_task_states(orch):
    """OBS-1/2: 逐 task 状态 + 时区免疫的相对秒数必须存在。"""
    f = orch.freshness()
    for key in (
        "tasks",
        "seconds_since_last_reconcile",
        "seconds_since_last_index",
        "scan_overdue",
        "excluded_count",
    ):
        assert key in f
    assert isinstance(f["tasks"], dict)


def test_g2_dead_scan_loop_flags_stale_despite_empty_pending(orch):
    """OBS-3: scan loop 死亡时 pending 恒空 → lag 恒 0 —— 旧 stale 判定
    永远不亮。scan_overdue 维度必须独立把 stale 拉红。"""
    from datetime import timedelta

    orch._last_reconcile_at = _utcnow_for_test() - timedelta(seconds=orch._scan_interval * 10)
    f = orch.freshness()
    assert f["pending_depth"] == 0
    assert f["lag_seconds"] == 0.0
    assert f["scan_overdue"] is True
    assert f["stale"] is True, "loop 死亡必须可被 stale 表达"


def test_g3_blacklist_exclusion_observability_hooks_exist(orch):
    """OBS-4: 黑名单排除不再绝对静默 — 遥测字段 + watcher 计数属性锁定。
    (Obsidian 默认文件名 未命名.md/Untitled.md 命中 DEFAULT_VAULT_SKIP_FILES,
    用户最自然的测试动作曾零痕迹消失。)"""
    assert orch.enqueue("upsert", "节点/未命名.md") == "excluded"
    assert hasattr(orch, "_excluded_count") and hasattr(orch, "_excluded_logged")
    assert "excluded_count" in orch.freshness()
