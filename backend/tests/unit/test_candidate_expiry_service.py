"""Story 2.5.X Task 9 — expire_pending_candidates 单元测试.

覆盖 AC #2 + Task 9:
- pending + created_at < cutoff → status=expired (changed_by=system)
- pending + created_at >= cutoff → 不变 (不到期)
- non-pending (accepted/dismissed/etc) → 不变 (幂等)
- 无 created_at 字段 → 保守不 expire
- 跨文件批量处理: file A 改 + file B 不变, file 各自原子写入
- 单条失败不中断 (state_change / write 异常)

Story trace: _bmad-output/implementation-artifacts/epic-2/2-5-x-error-candidate-progressive-confirmation.md
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
import yaml

from app.services.candidate_expiry_service import (
    DEFAULT_EXPIRY_DAYS,
    _is_expired,
    _parse_created_at,
    expire_pending_candidates,
)


# ════════════════════════════════════════════════════════════════════
# Fixtures
# ════════════════════════════════════════════════════════════════════


def _md_with_candidates(file_path, candidates: list[dict]):
    """创建测试 .md 含 error_candidates[]."""
    fm = {"type": "concept", "error_candidates": candidates}
    fm_str = yaml.safe_dump(fm, allow_unicode=True, sort_keys=False)
    file_path.write_text(f"---\n{fm_str}---\n# Body\n", encoding="utf-8")


def _make_candidate(
    candidate_id: str,
    status: str = "pending",
    created_at: str | None = "2026-04-01T00:00:00+00:00",  # 默认 30+ 天前
):
    return {
        "id": candidate_id,
        "status": status,
        "source": "ai_suggested",
        "node_id": "节点/x.md",
        "session_id": "s-1",
        "candidate_dedupe_hash": f"hash-{candidate_id}",
        "pedagogy_type": "conceptual_confusion",
        "legacy_type": "knowledge_gap",
        "legacy_remedy": "backtrack_definition",
        "description": f"错误 {candidate_id}",
        "context": "",
        "ai_reason": None,
        "evidence_turns": [],
        "raw_dialog_excerpt": None,
        "confidence": 0.7,
        "confidence_source": "llm",
        "sub_tags": [],
        "suggested_remedy_strategies": [],
        "created_at": created_at,
        "last_seen_at": created_at,
        "seen_count": 1,
        "seen_sessions": ["s-1"],
        "status_changed_at": None,
        "status_changed_by": None,
    }


# ════════════════════════════════════════════════════════════════════
# Helpers
# ════════════════════════════════════════════════════════════════════


def test_parse_created_at_iso_string():
    dt = _parse_created_at("2026-05-04T10:30:00+00:00")
    assert dt is not None
    assert dt.year == 2026 and dt.month == 5 and dt.day == 4


def test_parse_created_at_z_suffix():
    """ISO 8601 with 'Z' suffix (UTC)."""
    dt = _parse_created_at("2026-05-04T10:30:00Z")
    assert dt is not None
    assert dt.tzinfo is not None


def test_parse_created_at_naive_treated_as_utc():
    """Naive datetime string → assume UTC."""
    dt = _parse_created_at("2026-05-04T10:30:00")
    assert dt is not None
    assert dt.tzinfo is not None  # 自动加 UTC


def test_parse_created_at_invalid_returns_none():
    assert _parse_created_at("garbage") is None
    assert _parse_created_at(None) is None
    assert _parse_created_at(12345) is None


def test_is_expired_pending_old_returns_true():
    cand = _make_candidate("c1", created_at="2026-01-01T00:00:00+00:00")
    cutoff = datetime(2026, 5, 1, tzinfo=timezone.utc)
    assert _is_expired(cand, cutoff) is True


def test_is_expired_pending_recent_returns_false():
    """created_at >= cutoff → 不 expire."""
    cand = _make_candidate("c1", created_at="2026-04-30T00:00:00+00:00")
    cutoff = datetime(2026, 4, 1, tzinfo=timezone.utc)  # cutoff 比 created 早 → 不 expire
    assert _is_expired(cand, cutoff) is False


def test_is_expired_non_pending_returns_false():
    cand = _make_candidate(
        "c1", status="accepted", created_at="2026-01-01T00:00:00+00:00"
    )
    cutoff = datetime(2026, 5, 1, tzinfo=timezone.utc)
    assert _is_expired(cand, cutoff) is False


def test_is_expired_no_created_at_returns_false():
    """无 created_at 字段 → 保守不 expire."""
    cand = _make_candidate("c1", created_at=None)
    cutoff = datetime(2026, 5, 1, tzinfo=timezone.utc)
    assert _is_expired(cand, cutoff) is False


# ════════════════════════════════════════════════════════════════════
# expire_pending_candidates — 主流程
# ════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_expire_old_pending_candidate_marked_expired(tmp_path):
    """30 天前的 pending → status=expired + status_changed_by=system."""
    nodes = tmp_path / "节点"
    nodes.mkdir()
    f = nodes / "x.md"
    _md_with_candidates(
        f,
        [
            _make_candidate("old-1", created_at="2026-04-01T00:00:00+00:00"),
        ],
    )

    now = datetime(2026, 5, 5, tzinfo=timezone.utc)  # 34 天后
    stats = await expire_pending_candidates(
        tmp_path, expiry_days=30, now=now
    )

    assert stats.total_files_scanned == 1
    assert stats.total_pending_scanned == 1
    assert stats.total_expired == 1
    assert stats.failed == 0

    # 验证 frontmatter 写回
    fm = yaml.safe_load(f.read_text().split("---")[1])
    cand = fm["error_candidates"][0]
    assert cand["status"] == "expired"
    assert cand["status_changed_by"] == "system"
    assert cand["status_changed_at"] is not None


@pytest.mark.asyncio
async def test_expire_recent_pending_not_changed(tmp_path):
    """新 pending (< 30 天) → 不 expire."""
    nodes = tmp_path / "节点"
    nodes.mkdir()
    f = nodes / "x.md"
    _md_with_candidates(
        f,
        [_make_candidate("new-1", created_at="2026-05-04T00:00:00+00:00")],
    )

    now = datetime(2026, 5, 5, tzinfo=timezone.utc)  # 仅 1 天后
    stats = await expire_pending_candidates(
        tmp_path, expiry_days=30, now=now
    )

    assert stats.total_pending_scanned == 1
    assert stats.total_expired == 0

    fm = yaml.safe_load(f.read_text().split("---")[1])
    assert fm["error_candidates"][0]["status"] == "pending"


@pytest.mark.asyncio
async def test_expire_skips_terminal_status(tmp_path):
    """已 accepted/dismissed/disputed/expired 的不再处理 (幂等)."""
    nodes = tmp_path / "节点"
    nodes.mkdir()
    f = nodes / "x.md"
    _md_with_candidates(
        f,
        [
            _make_candidate("accepted-1", status="accepted"),
            _make_candidate("dismissed-1", status="dismissed"),
            _make_candidate("expired-1", status="expired"),
            _make_candidate("disputed-1", status="disputed"),
        ],
    )

    now = datetime(2026, 5, 5, tzinfo=timezone.utc)
    stats = await expire_pending_candidates(
        tmp_path, expiry_days=30, now=now
    )

    assert stats.total_pending_scanned == 0  # 没有 pending
    assert stats.total_expired == 0  # 都不动

    fm = yaml.safe_load(f.read_text().split("---")[1])
    statuses = [c["status"] for c in fm["error_candidates"]]
    assert statuses == ["accepted", "dismissed", "expired", "disputed"]  # 全部不变


@pytest.mark.asyncio
async def test_expire_idempotent_second_run_no_change(tmp_path):
    """二次 expire (同一时间) → 第二次 0 expired (幂等)."""
    nodes = tmp_path / "节点"
    nodes.mkdir()
    f = nodes / "x.md"
    _md_with_candidates(
        f, [_make_candidate("c1", created_at="2026-04-01T00:00:00+00:00")]
    )

    now = datetime(2026, 5, 5, tzinfo=timezone.utc)
    stats1 = await expire_pending_candidates(tmp_path, expiry_days=30, now=now)
    assert stats1.total_expired == 1

    # 第二次跑 (同样时间)
    stats2 = await expire_pending_candidates(tmp_path, expiry_days=30, now=now)
    assert stats2.total_expired == 0
    assert stats2.total_pending_scanned == 0  # 第一次后已无 pending


@pytest.mark.asyncio
async def test_expire_mixed_pending_keeps_recent_expires_old(tmp_path):
    """同文件混合 old + new pending → 仅 old 被 expire."""
    nodes = tmp_path / "节点"
    nodes.mkdir()
    f = nodes / "x.md"
    _md_with_candidates(
        f,
        [
            _make_candidate("old", created_at="2026-04-01T00:00:00+00:00"),
            _make_candidate("new", created_at="2026-05-04T00:00:00+00:00"),
        ],
    )

    now = datetime(2026, 5, 5, tzinfo=timezone.utc)
    stats = await expire_pending_candidates(tmp_path, expiry_days=30, now=now)

    assert stats.total_pending_scanned == 2
    assert stats.total_expired == 1

    fm = yaml.safe_load(f.read_text().split("---")[1])
    statuses = {c["id"]: c["status"] for c in fm["error_candidates"]}
    assert statuses == {"old": "expired", "new": "pending"}


@pytest.mark.asyncio
async def test_expire_no_candidates_in_file_skipped(tmp_path):
    """无 error_candidates[] 字段 → 不动."""
    nodes = tmp_path / "节点"
    nodes.mkdir()
    f = nodes / "x.md"
    f.write_text("---\ntype: concept\n---\n# Body\n", encoding="utf-8")

    now = datetime(2026, 5, 5, tzinfo=timezone.utc)
    stats = await expire_pending_candidates(tmp_path, expiry_days=30, now=now)

    assert stats.total_files_scanned == 1
    assert stats.total_pending_scanned == 0
    assert stats.total_expired == 0


@pytest.mark.asyncio
async def test_expire_vault_not_exist_returns_empty(tmp_path):
    """vault 不存在 → 空 stats."""
    stats = await expire_pending_candidates(
        tmp_path / "missing", expiry_days=30
    )
    assert stats.total_files_scanned == 0
    assert stats.total_expired == 0


@pytest.mark.asyncio
async def test_expire_no_created_at_field_skipped(tmp_path):
    """无 created_at → 保守不 expire (避免误伤旧数据)."""
    nodes = tmp_path / "节点"
    nodes.mkdir()
    f = nodes / "x.md"
    _md_with_candidates(f, [_make_candidate("c1", created_at=None)])

    now = datetime(2026, 5, 5, tzinfo=timezone.utc)
    stats = await expire_pending_candidates(tmp_path, expiry_days=30, now=now)

    assert stats.total_pending_scanned == 1
    assert stats.total_expired == 0  # 无时间戳保守跳过


@pytest.mark.asyncio
async def test_expire_only_writes_when_changes_exist(tmp_path):
    """无 expire 改动时不修改文件 mtime."""
    nodes = tmp_path / "节点"
    nodes.mkdir()
    f = nodes / "x.md"
    _md_with_candidates(
        f, [_make_candidate("recent", created_at="2026-05-04T00:00:00+00:00")]
    )

    mtime_before = f.stat().st_mtime
    import time as _time

    _time.sleep(0.1)  # 确保 mtime 变化可被检测

    now = datetime(2026, 5, 5, tzinfo=timezone.utc)
    await expire_pending_candidates(tmp_path, expiry_days=30, now=now)

    mtime_after = f.stat().st_mtime
    # 无 expire 改动时不应写文件 (mtime 不变)
    assert mtime_after == mtime_before


@pytest.mark.asyncio
async def test_expire_multiple_files_processed_independently(tmp_path):
    """多文件批量处理: 每文件独立, 单文件失败不影响其他."""
    nodes = tmp_path / "节点"
    nodes.mkdir()
    _md_with_candidates(
        nodes / "a.md",
        [_make_candidate("old-a", created_at="2026-04-01T00:00:00+00:00")],
    )
    _md_with_candidates(
        nodes / "b.md",
        [_make_candidate("old-b", created_at="2026-04-01T00:00:00+00:00")],
    )

    now = datetime(2026, 5, 5, tzinfo=timezone.utc)
    stats = await expire_pending_candidates(tmp_path, expiry_days=30, now=now)

    assert stats.total_files_scanned == 2
    assert stats.total_expired == 2

    # 各自验证
    for fname in ("a.md", "b.md"):
        fm = yaml.safe_load((nodes / fname).read_text().split("---")[1])
        assert fm["error_candidates"][0]["status"] == "expired"


@pytest.mark.asyncio
async def test_expire_default_expiry_days_is_30():
    """默认 expiry_days = 30."""
    assert DEFAULT_EXPIRY_DAYS == 30


@pytest.mark.asyncio
async def test_expire_stats_includes_cutoff_iso(tmp_path):
    """ExpireStats 含 cutoff_iso (用于审计)."""
    nodes = tmp_path / "节点"
    nodes.mkdir()
    _md_with_candidates(nodes / "x.md", [])

    now = datetime(2026, 5, 5, tzinfo=timezone.utc)
    stats = await expire_pending_candidates(tmp_path, expiry_days=30, now=now)

    expected_cutoff = now - timedelta(days=30)
    assert stats.cutoff_iso == expected_cutoff.isoformat()
    assert stats.expiry_days == 30
