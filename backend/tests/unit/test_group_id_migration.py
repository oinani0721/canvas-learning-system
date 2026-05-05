"""Story 2.5.Y Task 6 — group_id 命名迁移单元测试.

覆盖:
- map_legacy_group_id 各种 legacy 格式映射
- 已是 vault: 格式 → 幂等不变
- 含冒号 (Story 1.9 格式) → vault:<sanitize>:<rest>
- migrate_legacy_group_ids dry_run vs apply 模式 (mock driver)

Story trace: _bmad-output/implementation-artifacts/epic-2/2-5-y-isolation-hardening-subject-config-reuse.md
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.group_id_migration_service import (
    LEGACY_TO_VAULT_MAPPING,
    map_legacy_group_id,
    migrate_legacy_group_ids,
)


# ════════════════════════════════════════════════════════════════════
# map_legacy_group_id — pure function 映射规则
# ════════════════════════════════════════════════════════════════════


def test_map_legacy_cs188_to_vault_default():
    assert map_legacy_group_id("cs188") == "vault:default"


def test_map_legacy_canvas_dev_to_vault_default():
    assert map_legacy_group_id("canvas-dev") == "vault:default"


def test_map_legacy_general_to_vault_default():
    """Story 1.9 DEFAULT_SUBJECT_ID 'general' → vault:default."""
    assert map_legacy_group_id("general") == "vault:default"


def test_map_already_vault_format_unchanged():
    """已是 vault: 前缀 → 幂等不变."""
    assert map_legacy_group_id("vault:cs_61b") == "vault:cs_61b"
    assert (
        map_legacy_group_id("vault:cs_61b:algorithms") == "vault:cs_61b:algorithms"
    )
    assert map_legacy_group_id("vault:数学") == "vault:数学"


def test_map_story_1_9_subject_canvas_format():
    """Story 1.9 subject:canvas → vault:<sanitized>:<sanitized>."""
    assert map_legacy_group_id("cs_61b:main") == "vault:cs_61b:main"
    assert map_legacy_group_id("数学:离散") == "vault:数学:离散"


def test_map_unknown_subject_to_vault_prefix():
    """未在 LEGACY_TO_VAULT_MAPPING 中的 subject → vault:<sanitize>."""
    assert map_legacy_group_id("physics") == "vault:physics"
    assert map_legacy_group_id("ML") == "vault:ml"


def test_map_chinese_subject():
    assert map_legacy_group_id("数学") == "vault:数学"


def test_map_special_chars_sanitized():
    """特殊字符 underscore 替换."""
    assert map_legacy_group_id("CS 61B!") == "vault:cs_61b"


def test_map_empty_to_vault_default():
    assert map_legacy_group_id("") == "vault:default"
    assert map_legacy_group_id("   ") == "vault:default"


def test_legacy_mapping_dict_contains_known_legacy_values():
    """LEGACY_TO_VAULT_MAPPING 应至少含 cs188 / canvas-dev (CLAUDE.md 历史值)."""
    assert "cs188" in LEGACY_TO_VAULT_MAPPING
    assert "canvas-dev" in LEGACY_TO_VAULT_MAPPING


# ════════════════════════════════════════════════════════════════════
# migrate_legacy_group_ids — driver=None 边界
# ════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_migrate_no_driver_returns_empty_stats():
    """driver=None → 返回空 stats (用于 sample/doc 不连 Neo4j)."""
    stats = await migrate_legacy_group_ids(None, dry_run=True)
    assert stats.dry_run is True
    assert stats.total_old_group_ids == 0
    assert stats.total_nodes_affected == 0
    assert stats.migrations == []


# ════════════════════════════════════════════════════════════════════
# migrate_legacy_group_ids — mock driver 测试
# ════════════════════════════════════════════════════════════════════


def _make_mock_driver(distinct_records: list):
    """构造 mock driver 模拟 distinct group_id query."""

    class _MockResult:
        def __init__(self, recs):
            self._recs = recs

        async def data(self):
            return self._recs

    class _MockSession:
        def __init__(self, recs):
            self._recs = recs
            self.run_calls = []

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def run(self, query, **params):
            self.run_calls.append((query, params))
            # distinct query 返回 records, update query 返回 counter
            if "DISTINCT" in query:
                return _MockResult(self._recs)
            return _MockResult([{"updated": 1}])

    class _MockDriver:
        def __init__(self, recs):
            self.session_obj = _MockSession(recs)

        def session(self):
            return self.session_obj

    return _MockDriver(distinct_records)


@pytest.mark.asyncio
async def test_migrate_dry_run_lists_migrations_no_apply():
    """dry_run=True 仅扫描+报告, 不调 update query."""
    driver = _make_mock_driver(
        [
            {"gid": "cs188", "node_count": 100},
            {"gid": "canvas-dev", "node_count": 50},
            {"gid": "vault:cs_61b", "node_count": 30},  # 已是新格式, 跳过
        ]
    )

    stats = await migrate_legacy_group_ids(driver, dry_run=True)

    assert stats.dry_run is True
    assert stats.total_old_group_ids == 2  # cs188 + canvas-dev
    assert stats.total_nodes_affected == 150
    assert stats.skipped_already_vault_format == 1  # vault:cs_61b
    assert len(stats.migrations) == 2

    # dry_run → 仅 distinct query, 不调 update
    update_calls = [
        c for c in driver.session_obj.run_calls if "SET" in c[0] or "UPDATE" in c[0]
    ]
    assert len(update_calls) == 0


@pytest.mark.asyncio
async def test_migrate_apply_mode_calls_update():
    """dry_run=False 实际调 update query."""
    driver = _make_mock_driver(
        [
            {"gid": "cs188", "node_count": 100},
        ]
    )

    stats = await migrate_legacy_group_ids(driver, dry_run=False)

    assert stats.dry_run is False
    update_calls = [c for c in driver.session_obj.run_calls if "SET" in c[0]]
    assert len(update_calls) == 1
    # 验证参数
    assert update_calls[0][1]["old"] == "cs188"
    assert update_calls[0][1]["new"] == "vault:default"


@pytest.mark.asyncio
async def test_migrate_idempotent_second_run_no_changes():
    """二次跑 (假设第一次已迁移) → 全部跳过."""
    driver = _make_mock_driver(
        [
            {"gid": "vault:cs_61b", "node_count": 100},
            {"gid": "vault:数学", "node_count": 50},
        ]
    )

    stats = await migrate_legacy_group_ids(driver, dry_run=True)
    assert stats.total_old_group_ids == 0
    assert stats.skipped_already_vault_format == 2


@pytest.mark.asyncio
async def test_migrate_handles_empty_database():
    """空 db → 0 stats."""
    driver = _make_mock_driver([])
    stats = await migrate_legacy_group_ids(driver, dry_run=True)
    assert stats.total_old_group_ids == 0
    assert stats.total_nodes_affected == 0


@pytest.mark.asyncio
async def test_migrate_records_node_count_per_migration():
    """每条 migration 应记录原始 node_count."""
    driver = _make_mock_driver(
        [
            {"gid": "cs188", "node_count": 100},
            {"gid": "physics", "node_count": 25},
        ]
    )
    stats = await migrate_legacy_group_ids(driver, dry_run=True)

    by_old = {m.old: m for m in stats.migrations}
    assert by_old["cs188"].node_count == 100
    assert by_old["cs188"].new == "vault:default"
    assert by_old["physics"].node_count == 25
    assert by_old["physics"].new == "vault:physics"
