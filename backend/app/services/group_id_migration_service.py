"""Story 2.5.Y Task 6 — group_id 命名统一迁移 service.

把旧格式 group_id (cs188 / canvas-dev / cs_61b / cs_61b:main) 迁移到新格式 vault:<id>.

支持 dry_run 模式 (默认 True 防误改 production data).

Story trace: _bmad-output/implementation-artifacts/epic-2/2-5-y-isolation-hardening-subject-config-reuse.md
"""

from __future__ import annotations

import time as _time
from typing import Any, Optional, Protocol

import structlog
from pydantic import BaseModel, Field

from app.core.subject_config import is_vault_group_id, sanitize_subject_name

logger = structlog.get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Schemas
# ═══════════════════════════════════════════════════════════════════════════════


class GroupIdMigration(BaseModel):
    """单个 group_id 迁移记录."""

    old: str
    new: str
    node_count: int = 0


class MigrationStats(BaseModel):
    """Story 2.5.Y Task 6 — migrate_group_ids 返回值."""

    dry_run: bool = True
    total_old_group_ids: int = 0
    total_nodes_affected: int = 0
    migrations: list[GroupIdMigration] = Field(default_factory=list)
    skipped_already_vault_format: int = Field(
        default=0, description="已是 vault: 格式的 group_id 被跳过"
    )
    elapsed_ms: float = 0.0


# ═══════════════════════════════════════════════════════════════════════════════
# Mapping rules
# ═══════════════════════════════════════════════════════════════════════════════


# Story 2.5.Y 已知 legacy group_id 映射规则
LEGACY_TO_VAULT_MAPPING = {
    "cs188": "vault:default",  # config.py 默认 fallback
    "canvas-dev": "vault:default",  # 旧 CLAUDE.md 全局默认
    "general": "vault:default",  # Story 1.9 DEFAULT_SUBJECT_ID
    "main": "vault:default",  # 极少数兜底场景
}


def map_legacy_group_id(old: str) -> str:
    """把 legacy group_id 映射到新 vault: 格式.

    映射规则:
    1. 已是 vault: 前缀 → 不变 (幂等性)
    2. 命中 LEGACY_TO_VAULT_MAPPING 显式映射 → 用映射值
    3. 含冒号 (subject:canvas) → vault:default:<原值> 保留二级
    4. 其他 → vault:<sanitize(原值)>

    Args:
        old: legacy group_id

    Returns:
        New vault: format group_id
    """
    if not old or not old.strip():
        return "vault:default"

    if is_vault_group_id(old):
        return old  # 已是新格式, 幂等

    if old in LEGACY_TO_VAULT_MAPPING:
        return LEGACY_TO_VAULT_MAPPING[old]

    # 含冒号 (Story 1.9 格式 subject:canvas)
    if ":" in old:
        # subject:canvas → vault:<sanitize(subject)>:<sanitize(canvas)>
        parts = old.split(":", 1)
        subject = sanitize_subject_name(parts[0])
        rest = sanitize_subject_name(parts[1]) if len(parts) > 1 else ""
        if rest:
            return f"vault:{subject}:{rest}"
        return f"vault:{subject}"

    # 默认: vault:<sanitize(old)>
    return f"vault:{sanitize_subject_name(old)}"


# ═══════════════════════════════════════════════════════════════════════════════
# Neo4j driver Protocol (mock-friendly)
# ═══════════════════════════════════════════════════════════════════════════════


class _SessionLike(Protocol):
    """协议定义 mock 友好的 driver session."""

    async def run(self, query: str, **params: Any) -> Any: ...
    async def __aenter__(self) -> Any: ...
    async def __aexit__(self, *args: Any) -> None: ...


class _DriverLike(Protocol):
    def session(self) -> _SessionLike: ...


# ═══════════════════════════════════════════════════════════════════════════════
# Task 6 — migrate_legacy_group_ids
# ═══════════════════════════════════════════════════════════════════════════════


async def migrate_legacy_group_ids(
    driver: Optional[_DriverLike] = None,
    *,
    dry_run: bool = True,
    distinct_query: str = "MATCH (n) WHERE n.group_id IS NOT NULL RETURN DISTINCT n.group_id AS gid, count(n) AS node_count",
    update_query: str = "MATCH (n) WHERE n.group_id = $old SET n.group_id = $new RETURN count(n) AS updated",
) -> MigrationStats:
    """Story 2.5.Y Task 6 — 扫描 Neo4j 旧 group_id 并迁移到新 vault: 格式.

    设计:
    - dry_run=True (默认): 仅扫描 + 报告将要迁移的内容, **不**实际改 production data
    - dry_run=False: 真实执行 SET n.group_id = new

    幂等性:
    - 已是 vault: 格式的 group_id 自动跳过 (skipped_already_vault_format 计数)

    Args:
        driver: Neo4j async driver (mock 时传入测试 stub)
        dry_run: True 默认, 不改 production
        distinct_query: scan query (允许 override 测试)
        update_query: migrate query (allow override)

    Returns:
        MigrationStats — 含 migrations[] 详情 + 统计

    用法 (从 CLI):
        python -c "
        import asyncio
        from neo4j import AsyncGraphDatabase
        from app.services.group_id_migration_service import migrate_legacy_group_ids

        async def run():
            driver = AsyncGraphDatabase.driver('bolt://localhost:7691', auth=('neo4j', 'password'))
            stats = await migrate_legacy_group_ids(driver, dry_run=True)
            print(stats.model_dump_json(indent=2))
            await driver.close()

        asyncio.run(run())
        "
    """
    start = _time.monotonic()

    if driver is None:
        # 无 driver — 仅返回 mapping rules 报告 (用于 doc/sample)
        return MigrationStats(
            dry_run=dry_run,
            elapsed_ms=round((_time.monotonic() - start) * 1000.0, 2),
        )

    migrations: list[GroupIdMigration] = []
    total_nodes = 0
    skipped = 0

    # Step 1: scan distinct group_ids
    try:
        async with driver.session() as session:
            result = await session.run(distinct_query)
            records = await result.data() if hasattr(result, "data") else []
    except Exception as e:
        logger.warning("group_id_migration.scan_failed", error=str(e))
        return MigrationStats(
            dry_run=dry_run,
            elapsed_ms=round((_time.monotonic() - start) * 1000.0, 2),
        )

    # Step 2: compute mappings + (optional) execute migration
    for rec in records:
        if not isinstance(rec, dict):
            continue
        old = rec.get("gid") or rec.get("group_id") or ""
        node_count = int(rec.get("node_count") or 0)

        if not old:
            continue

        if is_vault_group_id(old):
            skipped += 1
            continue

        new = map_legacy_group_id(old)
        if new == old:
            skipped += 1
            continue

        migration = GroupIdMigration(old=old, new=new, node_count=node_count)
        migrations.append(migration)
        total_nodes += node_count

        if not dry_run:
            try:
                async with driver.session() as session:
                    await session.run(update_query, old=old, new=new)
                    logger.info(
                        "group_id_migration.migrated",
                        old=old,
                        new=new,
                        node_count=node_count,
                    )
            except Exception as e:
                logger.warning(
                    "group_id_migration.update_failed",
                    old=old,
                    new=new,
                    error=str(e),
                )

    elapsed_ms = (_time.monotonic() - start) * 1000.0
    logger.info(
        "group_id_migration.completed",
        dry_run=dry_run,
        total_old_group_ids=len(migrations),
        total_nodes_affected=total_nodes,
        skipped=skipped,
        elapsed_ms=round(elapsed_ms, 2),
    )

    return MigrationStats(
        dry_run=dry_run,
        total_old_group_ids=len(migrations),
        total_nodes_affected=total_nodes,
        migrations=migrations,
        skipped_already_vault_format=skipped,
        elapsed_ms=round(elapsed_ms, 2),
    )
