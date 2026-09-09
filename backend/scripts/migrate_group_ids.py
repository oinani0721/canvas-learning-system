#!/usr/bin/env python3
"""Round-23 Story 7.6 · cs188 历史数据迁移脚本.

CLI 包装器 for app.services.group_id_migration_service.migrate_legacy_group_ids.
扫 Neo4j 内所有 distinct group_id, 把 legacy 格式 (cs188 / canvas-dev / general / cs_61b:main)
迁移到 Story 2.5.Y vault: 前缀格式 (vault:default / vault:cs_61b:main / ...).

幂等: 已是 vault: 前缀的 group_id 自动跳过.

Usage:
    # 干跑 (默认, 不改 production)
    python scripts/migrate_group_ids.py --dry-run

    # 实际执行
    python scripts/migrate_group_ids.py --apply

    # 自定义连接
    python scripts/migrate_group_ids.py --apply --uri bolt://localhost:7691 --user neo4j --password XXX

[Source: _bmad-output/research/round-23-chatgpt-dr-result-and-synthesis-2026-05-08.md Stage 1 Task 6]
[Source: app/services/group_id_migration_service.py:migrate_legacy_group_ids]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

# 确保能 import app.*
SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Round-23 Story 7.6 — Migrate legacy Neo4j group_id to vault: prefix format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/migrate_group_ids.py --dry-run
  python scripts/migrate_group_ids.py --apply
  python scripts/migrate_group_ids.py --apply --uri bolt://localhost:7691

Migration rules (LEGACY_TO_VAULT_MAPPING):
  cs188       -> vault:default
  canvas-dev  -> vault:default
  general     -> vault:default
  main        -> vault:default
  <other>:<x> -> vault:<sanitized>:<x>
  <other>     -> vault:<sanitized>
""".strip(),
    )

    mode_group = p.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        "--dry-run",
        action="store_true",
        help="Scan + report only, do NOT modify Neo4j data",
    )
    mode_group.add_argument(
        "--apply",
        action="store_true",
        help="Actually execute the migration (writes to Neo4j)",
    )

    p.add_argument(
        "--uri",
        default=None,
        help="Neo4j Bolt URI (default: from settings.NEO4J_URI)",
    )
    p.add_argument(
        "--user",
        default=None,
        help="Neo4j username (default: from settings.NEO4J_USER)",
    )
    p.add_argument(
        "--password",
        default=None,
        help="Neo4j password (default: from settings.NEO4J_PASSWORD)",
    )
    p.add_argument(
        "--json",
        action="store_true",
        help="Output stats as JSON (machine-readable)",
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="Skip interactive confirmation prompt before --apply",
    )

    return p.parse_args()


async def run_migration(args: argparse.Namespace) -> int:
    from app.config import settings
    from app.services.group_id_migration_service import migrate_legacy_group_ids

    try:
        from neo4j import AsyncGraphDatabase
    except ImportError:
        print(
            "ERROR: neo4j Python driver not installed. Run: pip install neo4j",
            file=sys.stderr,
        )
        return 2

    uri = args.uri or settings.NEO4J_URI
    user = args.user or settings.NEO4J_USER
    password = args.password or settings.NEO4J_PASSWORD

    if not password:
        print(
            "ERROR: NEO4J_PASSWORD not set. Use --password or env var.", file=sys.stderr
        )
        return 2

    dry_run = args.dry_run
    mode_str = "DRY-RUN (no writes)" if dry_run else "APPLY (writing to Neo4j)"

    if not args.json:
        print(f"=== Round-23 Story 7.6 · group_id migration ({mode_str}) ===")
        print(f"  URI: {uri}")
        print(f"  User: {user}")
        print()

    if not dry_run and not args.force:
        if not args.json:
            confirm = input(
                "Proceed with --apply (writes to production Neo4j)? [yes/N]: "
            )
            if confirm.strip().lower() not in ("yes", "y"):
                print("Aborted by user.")
                return 1
        else:
            print(
                "ERROR: --apply requires --force when --json (no interactive prompt).",
                file=sys.stderr,
            )
            return 2

    driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
    try:
        stats = await migrate_legacy_group_ids(driver=driver, dry_run=dry_run)
    finally:
        await driver.close()

    if args.json:
        print(stats.model_dump_json(indent=2))
    else:
        print(f"Total old group_ids found: {stats.total_old_group_ids}")
        print(f"Total nodes affected:      {stats.total_nodes_affected}")
        print(f"Skipped (already vault):   {stats.skipped_already_vault_format}")
        print(f"Elapsed:                   {stats.elapsed_ms:.2f} ms")
        print()
        if stats.migrations:
            print("Migrations:")
            for m in stats.migrations:
                print(f"  {m.old!r:>30}  ->  {m.new!r:<30}  ({m.node_count} nodes)")
        else:
            print("No legacy group_ids found — vault is already canonical.")

    return 0


def main() -> int:
    args = parse_args()
    return asyncio.run(run_migration(args))


if __name__ == "__main__":
    sys.exit(main())
