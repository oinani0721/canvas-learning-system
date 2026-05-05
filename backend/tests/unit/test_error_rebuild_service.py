"""Story 2.5.X Task 5 — rebuild_graphiti_from_frontmatter 单元测试.

覆盖 AC #6:
- dry_run=True 仅扫描计数, 不调 Graphiti
- 实际写入 (dry_run=False) 调 write_error_to_graphiti N 次
- 单条失败 (file 损坏 / classifier 构造失败 / Graphiti 写入失败) 记录到 failures[] 不中断
- 节点/*.md fallback 路径
- vault 不存在 → 返回空 stats

Story trace: _bmad-output/implementation-artifacts/epic-2/2-5-x-error-candidate-progressive-confirmation.md
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
import yaml

from app.services.error_rebuild_service import (
    _err_record_to_classified,
    _scan_vault_md_files,
    rebuild_graphiti_from_frontmatter,
)


# ════════════════════════════════════════════════════════════════════
# Fixtures
# ════════════════════════════════════════════════════════════════════


def _md_with_errors(
    file_path,
    errors: list[dict] | None = None,
    extra_fm: dict | None = None,
):
    """创建 .md 含 frontmatter errors[]."""
    fm = {"type": "concept"}
    if extra_fm:
        fm.update(extra_fm)
    fm["errors"] = errors or []
    fm_str = yaml.safe_dump(fm, allow_unicode=True, sort_keys=False)
    file_path.write_text(f"---\n{fm_str}---\n# Body\n", encoding="utf-8")


def _make_error_record(
    error_id: str = "err-1",
    description: str = "学生混淆 X 与 Y",
    pedagogy_type: str = "conceptual_confusion",
    legacy_type: str = "knowledge_gap",
    confidence: float = 0.85,
):
    return {
        "id": error_id,
        "dedupe_hash": "abc123",
        "type": pedagogy_type,
        "legacy_type": legacy_type,
        "legacy_remedy": "backtrack_definition",
        "description": description,
        "corrected_at": None,
        "last_seen_at": "2026-05-04T00:00:00+00:00",
        "seen_count": 1,
        "tags": [],
        "remedy_strategies": ["discrimination_comparison"],
        "confidence": confidence,
        "created_at": "2026-05-04T00:00:00+00:00",
    }


# ════════════════════════════════════════════════════════════════════
# Helper functions
# ════════════════════════════════════════════════════════════════════


def test_err_record_to_classified_basic():
    """frontmatter errors[] 单条 dict → ClassifiedError 重建."""
    record = _make_error_record()
    classified = _err_record_to_classified(record)
    assert classified.description == "学生混淆 X 与 Y"
    assert classified.pedagogy_type.value == "conceptual_confusion"
    assert classified.legacy_type.value == "knowledge_gap"
    assert classified.confidence == 0.85


def test_err_record_to_classified_unknown_enum_fallback():
    """未知 enum 值 → fallback 到 default (CONCEPTUAL_CONFUSION / KNOWLEDGE_GAP / BACKTRACK_DEFINITION)."""
    record = _make_error_record(
        pedagogy_type="bogus_type",
        legacy_type="garbage",
    )
    record["legacy_remedy"] = "fake_remedy"
    classified = _err_record_to_classified(record)
    assert classified.pedagogy_type.value == "conceptual_confusion"
    assert classified.legacy_type.value == "knowledge_gap"
    assert classified.legacy_remedy.value == "backtrack_definition"


def test_scan_vault_md_files_uses_节点_dir(tmp_path):
    """优先扫描 vault_root/节点/*.md."""
    nodes_dir = tmp_path / "节点"
    nodes_dir.mkdir()
    (nodes_dir / "a.md").write_text("a", encoding="utf-8")
    (nodes_dir / "b.md").write_text("b", encoding="utf-8")
    (tmp_path / "Dashboard.md").write_text("ignored", encoding="utf-8")

    files = _scan_vault_md_files(tmp_path)
    assert len(files) == 2
    names = {p.name for p in files}
    assert names == {"a.md", "b.md"}


def test_scan_vault_md_files_fallback_to_root(tmp_path):
    """节点/ 不存在 → fallback 到 vault_root/*.md."""
    (tmp_path / "x.md").write_text("x", encoding="utf-8")
    (tmp_path / "y.md").write_text("y", encoding="utf-8")

    files = _scan_vault_md_files(tmp_path)
    assert len(files) == 2


# ════════════════════════════════════════════════════════════════════
# rebuild_graphiti_from_frontmatter — dry_run
# ════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_rebuild_dry_run_counts_only_no_graphiti_call(tmp_path):
    """dry_run=True 仅扫描计数, 不调 Graphiti."""
    nodes = tmp_path / "节点"
    nodes.mkdir()
    _md_with_errors(
        nodes / "a.md",
        errors=[_make_error_record(error_id="e1"), _make_error_record(error_id="e2")],
    )
    _md_with_errors(
        nodes / "b.md", errors=[_make_error_record(error_id="e3")]
    )

    with patch(
        "app.services.error_rebuild_service.write_error_to_graphiti",
        new=AsyncMock(return_value=True),
    ) as mock_g:
        stats = await rebuild_graphiti_from_frontmatter(
            tmp_path, group_id="vault:cs_61b", dry_run=True
        )

    assert stats.dry_run is True
    assert stats.total_files_scanned == 2
    assert stats.total_errors_scanned == 3
    assert stats.newly_written == 0  # dry_run 不写
    assert stats.failed == 0
    mock_g.assert_not_called()  # dry_run 不调 Graphiti


@pytest.mark.asyncio
async def test_rebuild_actual_writes_each_error_to_graphiti(tmp_path):
    """dry_run=False 实际写入 N 次 Graphiti."""
    nodes = tmp_path / "节点"
    nodes.mkdir()
    _md_with_errors(
        nodes / "a.md",
        errors=[_make_error_record(error_id="e1"), _make_error_record(error_id="e2")],
    )

    with patch(
        "app.services.error_rebuild_service.write_error_to_graphiti",
        new=AsyncMock(return_value=True),
    ) as mock_g:
        stats = await rebuild_graphiti_from_frontmatter(
            tmp_path, group_id="vault:cs_61b", dry_run=False
        )

    assert stats.dry_run is False
    assert stats.total_errors_scanned == 2
    assert stats.newly_written == 2
    assert stats.failed == 0
    assert mock_g.call_count == 2


# ════════════════════════════════════════════════════════════════════
# rebuild — failure handling
# ════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_rebuild_graphiti_failure_records_in_failures_list(tmp_path):
    """write_error_to_graphiti 返回 False → 记入 failures[] 不中断."""
    nodes = tmp_path / "节点"
    nodes.mkdir()
    _md_with_errors(
        nodes / "a.md",
        errors=[_make_error_record(error_id="e1"), _make_error_record(error_id="e2")],
    )

    # 第 1 次成功, 第 2 次失败
    with patch(
        "app.services.error_rebuild_service.write_error_to_graphiti",
        new=AsyncMock(side_effect=[True, False]),
    ):
        stats = await rebuild_graphiti_from_frontmatter(
            tmp_path, group_id="vault:cs_61b", dry_run=False
        )

    assert stats.newly_written == 1
    assert stats.failed == 1
    assert len(stats.failures) == 1
    assert stats.failures[0].error_id == "e2"
    assert "graphiti_write_failed" in stats.failures[0].reason


@pytest.mark.asyncio
async def test_rebuild_graphiti_exception_recorded_not_raised(tmp_path):
    """write_error_to_graphiti 抛 Exception → 记入 failures[] 不中断."""
    nodes = tmp_path / "节点"
    nodes.mkdir()
    _md_with_errors(nodes / "a.md", errors=[_make_error_record(error_id="e1")])

    with patch(
        "app.services.error_rebuild_service.write_error_to_graphiti",
        new=AsyncMock(side_effect=ValueError("boom")),
    ):
        stats = await rebuild_graphiti_from_frontmatter(
            tmp_path, group_id="vault:cs_61b", dry_run=False
        )

    assert stats.newly_written == 0
    assert stats.failed == 1
    assert "unexpected: boom" in stats.failures[0].reason


@pytest.mark.asyncio
async def test_rebuild_corrupted_frontmatter_skipped(tmp_path):
    """损坏 .md (无 frontmatter / yaml 错误) → 跳过, failed=0 (parse 失败属于 skip)."""
    nodes = tmp_path / "节点"
    nodes.mkdir()
    # 损坏文件: 非合法 frontmatter
    (nodes / "broken.md").write_text("---\nbad yaml: [\n---\n", encoding="utf-8")
    # 正常文件
    _md_with_errors(nodes / "ok.md", errors=[_make_error_record(error_id="e1")])

    with patch(
        "app.services.error_rebuild_service.write_error_to_graphiti",
        new=AsyncMock(return_value=True),
    ):
        stats = await rebuild_graphiti_from_frontmatter(
            tmp_path, group_id="vault:cs_61b", dry_run=False
        )

    # broken.md 被记入 failures (parse_failed)
    assert stats.failed == 1
    assert any("parse_failed" in f.reason for f in stats.failures)
    # ok.md 仍然处理
    assert stats.newly_written == 1


@pytest.mark.asyncio
async def test_rebuild_no_errors_in_frontmatter_just_scanned(tmp_path):
    """frontmatter 无 errors[] → total_errors_scanned=0, 不调 Graphiti."""
    nodes = tmp_path / "节点"
    nodes.mkdir()
    _md_with_errors(nodes / "a.md", errors=[])

    with patch(
        "app.services.error_rebuild_service.write_error_to_graphiti",
        new=AsyncMock(return_value=True),
    ) as mock_g:
        stats = await rebuild_graphiti_from_frontmatter(
            tmp_path, group_id="vault:cs_61b", dry_run=False
        )

    assert stats.total_files_scanned == 1
    assert stats.total_errors_scanned == 0
    assert stats.newly_written == 0
    mock_g.assert_not_called()


@pytest.mark.asyncio
async def test_rebuild_vault_root_not_exist_returns_empty(tmp_path):
    """vault_root 不存在 → 返回空 stats."""
    fake_vault = tmp_path / "missing"
    stats = await rebuild_graphiti_from_frontmatter(
        fake_vault, group_id="vault:cs_61b"
    )
    assert stats.total_files_scanned == 0
    assert stats.total_errors_scanned == 0


@pytest.mark.asyncio
async def test_rebuild_node_id_uses_vault_relative_path(tmp_path):
    """node_id 应是 vault-relative path (节点/X.md), 不是绝对路径."""
    nodes = tmp_path / "节点"
    nodes.mkdir()
    _md_with_errors(nodes / "admissibility.md", errors=[_make_error_record()])

    with patch(
        "app.services.error_rebuild_service.write_error_to_graphiti",
        new=AsyncMock(return_value=True),
    ) as mock_g:
        await rebuild_graphiti_from_frontmatter(
            tmp_path, group_id="vault:cs_61b", dry_run=False
        )

    # 验证 node_id 是 vault-relative
    call_kwargs = mock_g.call_args.kwargs
    assert "节点/admissibility.md" in call_kwargs["node_id"]


@pytest.mark.asyncio
async def test_rebuild_returns_elapsed_ms(tmp_path):
    """RebuildStats.elapsed_ms 有正值."""
    nodes = tmp_path / "节点"
    nodes.mkdir()
    _md_with_errors(nodes / "a.md", errors=[_make_error_record()])

    with patch(
        "app.services.error_rebuild_service.write_error_to_graphiti",
        new=AsyncMock(return_value=True),
    ):
        stats = await rebuild_graphiti_from_frontmatter(
            tmp_path, group_id="vault:cs_61b", dry_run=False
        )

    assert stats.elapsed_ms >= 0.0
