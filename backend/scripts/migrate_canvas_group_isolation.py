#!/usr/bin/env python3
"""P0-SYNC-ISO-2026-08-17 · Canvas 图 vault 隔离迁移 (migrations/003 的自动化执行器).

职责 (与 migrations/003_canvas_group_isolation.cypher 一一对应):
  STEP 0 census   — 三 label NULL 计数 + 全量清单 (百级规模, 供人工核对)
                    + 复合键预重复检测 + board (group,subject,name) 冲突检测
  STEP 1-2 回填    — board 先 (node 继承源) → node (板继承, 兜底 default)
                    → edge (兜底 default); WHERE IS NULL 幂等不覆盖已有值
  STEP 3 verify   — NULL 三 label 归零 gate (复合唯一约束对 NULL 行不强制,
                    回填不完 = 约束静默失效, 不归零禁止建约束)
  STEP 4 约束替换  — 先建新 (group_id 复合) 后删旧 (全局), 无保护真空窗口

⚠️ 不复用 group_id_migration_service.migrate_legacy_group_ids —
其扫描器是 WHERE group_id IS NOT NULL (迁旧值), 对本次目标 (NULL 行)
完全不可见。本脚本的扫描全部 WHERE group_id IS NULL。

Usage:
    # 干跑 (默认, 只出 census 报告, 不改数据)
    python scripts/migrate_canvas_group_isolation.py --dry-run

    # 实际执行 (交互确认; --force 跳过; --json 必须配 --force)
    python scripts/migrate_canvas_group_isolation.py --apply

    # 自定义连接 / 覆盖 default group
    python scripts/migrate_canvas_group_isolation.py --apply \
        --uri bolt://localhost:7689 --default-gid vault__canvas_vault

[Source: backend/migrations/003_canvas_group_isolation.cypher]
[Source: backend/scripts/migrate_group_ids.py — CLI 骨架]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

# 确保能 import app.*
SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))


# ═══════════════════════════════════════════════════════════════════════════════
# Cypher 语句 (与 migrations/003 保持逐字一致)
# ═══════════════════════════════════════════════════════════════════════════════

Q_NULL_COUNT_NODE = "MATCH (n:CanvasNode) WHERE n.group_id IS NULL RETURN count(n) AS c"
Q_NULL_COUNT_BOARD = "MATCH (b:CanvasBoard) WHERE b.group_id IS NULL RETURN count(b) AS c"
Q_NULL_COUNT_EDGE = "MATCH ()-[e:CANVAS_EDGE]->() WHERE e.group_id IS NULL RETURN count(e) AS c"

Q_NULL_LIST_NODE = """
MATCH (n:CanvasNode) WHERE n.group_id IS NULL
RETURN n.id AS id, n.canvasId AS canvas_id, n.title AS title
ORDER BY id
"""
Q_NULL_LIST_BOARD = """
MATCH (b:CanvasBoard) WHERE b.group_id IS NULL
RETURN b.id AS id, b.name AS name, b.subjectId AS subject_id
ORDER BY id
"""
Q_NULL_LIST_EDGE = """
MATCH (s)-[e:CANVAS_EDGE]->(t) WHERE e.group_id IS NULL
RETURN e.id AS id, s.id AS source_id, t.id AS target_id
ORDER BY id
"""

Q_DUP_NODE_COMPOSITE = """
MATCH (n:CanvasNode)
OPTIONAL MATCH (b:CanvasBoard {id: n.canvasId})
WITH n, coalesce(n.group_id, head([g IN collect(b.group_id) WHERE g IS NOT NULL]),
                 $default_gid) AS gid
WITH gid, n.id AS id, count(*) AS cnt
WHERE cnt > 1
RETURN gid, id, cnt ORDER BY cnt DESC
"""
Q_DUP_BOARD_COMPOSITE = """
MATCH (b:CanvasBoard)
WITH coalesce(b.group_id, $default_gid) AS gid, b.id AS id, count(*) AS cnt
WHERE cnt > 1
RETURN gid, id, cnt ORDER BY cnt DESC
"""
Q_DUP_BOARD_SUBJECT_NAME = """
MATCH (b:CanvasBoard)
WITH coalesce(b.group_id, $default_gid) AS gid,
     b.subjectId AS subject_id, b.name AS name, count(*) AS cnt
WHERE cnt > 1
RETURN gid, subject_id, name, cnt
"""

Q_BACKFILL_BOARD = """
MATCH (b:CanvasBoard)
WHERE b.group_id IS NULL
SET b.group_id = $default_gid
RETURN count(b) AS updated
"""
Q_BACKFILL_NODE = """
MATCH (n:CanvasNode)
WHERE n.group_id IS NULL
OPTIONAL MATCH (b:CanvasBoard {id: n.canvasId})
WITH n, head([g IN collect(b.group_id) WHERE g IS NOT NULL]) AS board_gid
SET n.group_id = coalesce(board_gid, $default_gid)
RETURN count(n) AS updated
"""
Q_BACKFILL_EDGE = """
MATCH (s)-[e:CANVAS_EDGE]->()
WHERE e.group_id IS NULL
SET e.group_id = coalesce(s.group_id, $default_gid)
RETURN count(e) AS updated
"""

# 先建新、后删旧 — 全程无保护真空窗口 (顺序即语义, 测试锁死)
CONSTRAINT_STATEMENTS: tuple[str, ...] = (
    "CREATE CONSTRAINT canvasnode_group_id_unique IF NOT EXISTS "
    "FOR (n:CanvasNode) REQUIRE (n.group_id, n.id) IS UNIQUE",
    "CREATE CONSTRAINT canvasboard_group_id_unique IF NOT EXISTS "
    "FOR (b:CanvasBoard) REQUIRE (b.group_id, b.id) IS UNIQUE",
    "CREATE CONSTRAINT canvasboard_group_subject_name_unique IF NOT EXISTS "
    "FOR (b:CanvasBoard) REQUIRE (b.group_id, b.subjectId, b.name) IS UNIQUE",
    "DROP CONSTRAINT canvasnode_id_unique IF EXISTS",
    "DROP CONSTRAINT canvasboard_subject_name_unique IF EXISTS",
)


# ═══════════════════════════════════════════════════════════════════════════════
# 纯函数层 (session 注入, mock 友好 — group_id_migration_service._DriverLike 同款)
# ═══════════════════════════════════════════════════════════════════════════════


async def _fetch(session: Any, query: str, **params: Any) -> list[dict[str, Any]]:
    result = await session.run(query, **params)
    return await result.data()


async def run_census(session: Any, default_gid: str) -> dict[str, Any]:
    """STEP 0 — NULL 计数 + 全量清单 + 预重复/冲突检测 (只读)."""
    node_null = (await _fetch(session, Q_NULL_COUNT_NODE))[0]["c"]
    board_null = (await _fetch(session, Q_NULL_COUNT_BOARD))[0]["c"]
    edge_null = (await _fetch(session, Q_NULL_COUNT_EDGE))[0]["c"]
    return {
        "default_gid": default_gid,
        "null_counts": {
            "CanvasNode": node_null,
            "CanvasBoard": board_null,
            "CANVAS_EDGE": edge_null,
        },
        "null_rows": {
            "CanvasNode": await _fetch(session, Q_NULL_LIST_NODE),
            "CanvasBoard": await _fetch(session, Q_NULL_LIST_BOARD),
            "CANVAS_EDGE": await _fetch(session, Q_NULL_LIST_EDGE),
        },
        "duplicates": {
            "node_composite": await _fetch(session, Q_DUP_NODE_COMPOSITE, default_gid=default_gid),
            "board_composite": await _fetch(session, Q_DUP_BOARD_COMPOSITE, default_gid=default_gid),
            "board_subject_name": await _fetch(session, Q_DUP_BOARD_SUBJECT_NAME, default_gid=default_gid),
        },
    }


def census_blockers(census: dict[str, Any]) -> list[str]:
    """预重复/冲突命中 → 人工处置后才允许 --apply (约束会中断)."""
    blockers: list[str] = []
    for key, label in (
        ("node_composite", "CanvasNode (group_id, id)"),
        ("board_composite", "CanvasBoard (group_id, id)"),
        ("board_subject_name", "CanvasBoard (group_id, subjectId, name)"),
    ):
        hits = census["duplicates"][key]
        if hits:
            blockers.append(f"{label} 重复 {len(hits)} 组: {hits}")
    return blockers


async def run_backfill(session: Any, default_gid: str) -> dict[str, int]:
    """STEP 1-2 — 回填顺序: board → node (继承板) → edge."""
    board = (await _fetch(session, Q_BACKFILL_BOARD, default_gid=default_gid))[0]
    node = (await _fetch(session, Q_BACKFILL_NODE, default_gid=default_gid))[0]
    edge = (await _fetch(session, Q_BACKFILL_EDGE, default_gid=default_gid))[0]
    return {
        "CanvasBoard": board["updated"],
        "CanvasNode": node["updated"],
        "CANVAS_EDGE": edge["updated"],
    }


async def run_verify(session: Any) -> dict[str, int]:
    """STEP 3 — NULL 残留计数 (三项全 0 才允许建约束)."""
    return {
        "CanvasNode": (await _fetch(session, Q_NULL_COUNT_NODE))[0]["c"],
        "CanvasBoard": (await _fetch(session, Q_NULL_COUNT_BOARD))[0]["c"],
        "CANVAS_EDGE": (await _fetch(session, Q_NULL_COUNT_EDGE))[0]["c"],
    }


async def run_constraint_swap(session: Any) -> list[str]:
    """STEP 4 — 逐条执行 (顺序: 3×CREATE 新复合约束 → 2×DROP 旧全局约束)."""
    executed: list[str] = []
    for stmt in CONSTRAINT_STATEMENTS:
        await session.run(stmt)
        executed.append(stmt)
    return executed


def resolve_default_gid(override: str | None) -> str:
    """--default-gid 覆盖, 缺省与启动回填/projection 同源推导."""
    from app.core.subject_config import default_vault_group_id
    from app.graphiti.group_id_compat import to_physical_group_id

    if override:
        return to_physical_group_id(override)
    return to_physical_group_id(default_vault_group_id())


# ═══════════════════════════════════════════════════════════════════════════════
# CLI (骨架照抄 migrate_group_ids.py)
# ═══════════════════════════════════════════════════════════════════════════════


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=("P0-SYNC-ISO-2026-08-17 — Canvas 图 group_id 回填 + 复合唯一约束迁移"),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/migrate_canvas_group_isolation.py --dry-run
  python scripts/migrate_canvas_group_isolation.py --dry-run --json
  python scripts/migrate_canvas_group_isolation.py --apply
  python scripts/migrate_canvas_group_isolation.py --apply --uri bolt://localhost:7689
""".strip(),
    )

    mode_group = p.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        "--dry-run",
        action="store_true",
        help="STEP 0 census 报告 (全量 NULL 清单 + 预重复检测), 不改数据",
    )
    mode_group.add_argument(
        "--apply",
        action="store_true",
        help="执行回填 + verify gate + 约束替换 (写 Neo4j)",
    )

    p.add_argument("--uri", default=None, help="Neo4j Bolt URI (default: settings)")
    p.add_argument("--user", default=None, help="Neo4j username (default: settings)")
    p.add_argument("--password", default=None, help="Neo4j password (default: settings)")
    p.add_argument(
        "--default-gid",
        default=None,
        help=(
            "回填兜底 group_id (会过 to_physical_group_id 归一)。缺省 = to_physical_group_id(default_vault_group_id())"
        ),
    )
    p.add_argument("--json", action="store_true", help="机器可读 JSON 报表")
    p.add_argument("--force", action="store_true", help="跳过 --apply 的交互确认")
    return p.parse_args()


def _print_census(census: dict[str, Any]) -> None:
    print(f"Default physical gid (回填兜底): {census['default_gid']}")
    print()
    print("NULL 计数:")
    for label, cnt in census["null_counts"].items():
        print(f"  {label:<12} {cnt}")
    print()
    for label, rows in census["null_rows"].items():
        print(f"NULL 清单 — {label} ({len(rows)} 行):")
        for row in rows:
            print(f"  {row}")
        if not rows:
            print("  (无)")
        print()
    blockers = census_blockers(census)
    if blockers:
        print("⛔ 预重复/冲突检测命中 (须人工处置后才可 --apply):")
        for b in blockers:
            print(f"  {b}")
    else:
        print("预重复/冲突检测: 全部通过 (0 命中)")


async def run_migration(args: argparse.Namespace) -> int:
    from app.config import settings

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
    database = getattr(settings, "NEO4J_DATABASE", None)

    if not password:
        print("ERROR: NEO4J_PASSWORD not set. Use --password or env var.", file=sys.stderr)
        return 2

    default_gid = resolve_default_gid(args.default_gid)
    dry_run = args.dry_run
    mode_str = "DRY-RUN (census only)" if dry_run else "APPLY (writing to Neo4j)"

    if not args.json:
        print(f"=== P0-SYNC-ISO · canvas group isolation migration ({mode_str}) ===")
        print(f"  URI: {uri}")
        print(f"  User: {user}")
        print()

    if not dry_run and not args.force:
        if not args.json:
            confirm = input("Proceed with --apply (backfill + constraint swap on production Neo4j)? [yes/N]: ")
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
    report: dict[str, Any] = {"mode": "dry-run" if dry_run else "apply"}
    try:
        async with driver.session(database=database) as session:
            census = await run_census(session, default_gid)
            report["census"] = census
            blockers = census_blockers(census)

            if dry_run:
                if args.json:
                    print(json.dumps(report, ensure_ascii=False, indent=2))
                else:
                    _print_census(census)
                return 0

            # --apply 路径: 预重复命中即中止 (约束建不起来, 不留半成品)
            if blockers:
                report["aborted"] = "duplicate_precheck_failed"
                report["blockers"] = blockers
                if args.json:
                    print(json.dumps(report, ensure_ascii=False, indent=2))
                else:
                    print("⛔ 预重复检测命中, 中止 (未写任何数据):")
                    for b in blockers:
                        print(f"  {b}")
                return 3

            backfilled = await run_backfill(session, default_gid)
            report["backfilled"] = backfilled

            residual = await run_verify(session)
            report["verify_null_residual"] = residual
            if any(residual.values()):
                # verify gate: NULL 未归零 → 禁止建约束 (对 NULL 行不强制,
                # 建了也是静默失效的假约束)
                report["aborted"] = "verify_null_not_zero"
                if args.json:
                    print(json.dumps(report, ensure_ascii=False, indent=2))
                else:
                    print(f"⛔ verify 失败, NULL 残留: {residual} — 约束未执行")
                return 3

            executed = await run_constraint_swap(session)
            report["constraints_executed"] = executed
    finally:
        await driver.close()

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print("回填:")
        for label, cnt in backfilled.items():
            print(f"  {label:<12} {cnt} 行")
        print(f"verify NULL 残留: {residual} (全 0 ✓)")
        print("约束替换 (5 条, 先建后删):")
        for stmt in executed:
            print(f"  {stmt}")
        print()
        print("完成。请再跑 SHOW CONSTRAINTS 人工复核 (migrations/003 STEP 5)。")

    return 0


def main() -> int:
    args = parse_args()
    return asyncio.run(run_migration(args))


if __name__ == "__main__":
    sys.exit(main())
