#!/usr/bin/env python
"""P1-05b 步骤 2: Graphiti 结构化图污染只读盘点 (census)。

用法 (需 Neo4j 在跑):
  cd backend && .venv/bin/python scripts/census_graphiti_pollution.py            # 只读
  cd backend && .venv/bin/python scripts/census_graphiti_pollution.py --vault X  # 指定 vault

⛔ 本脚本**没有 --apply** — 隔离执行属独立轮次, 必须用户过目本报告并批准后
   另行进行。全部 Cypher 为 MATCH/RETURN 计数, routing_="r" (只读路由)。
   不输出 fact 正文、不输出图侧 node_id 明细 — 只有计数与聚合。

盘点问题 (施工计划裁定的顺序):
  Q0 组分布     污染可能分散在 启动回填组 (vault:<active>) 与 CLI 脚本的
                DEFAULT_GROUP_ID 两处 — 先摸清再假定
  Q4 碰撞体检   (纯磁盘侧) 禁区 stem ∩ 合法 stem 必须为空; 否则按 stem 失效
                会误杀合法节点的边 → 执行步降级到按预计算 uuid5 精确匹配
  Q1 爆炸半径   禁区 stem 命中的边, 按 source 分组: total / active /
                active_reconcilable。active − reconcilable = 现有
                invalidate_missing_callouts (只认 annotation_id 的 callout)
                永远够不到的那批
  Q2 补集残渣   node_id 无法用磁盘上任何 md stem 解释的 active 边
                (禁区文件已删除/改名, stem 无法从磁盘枚举)
  Q3 实体节点   被禁区 stem 命名的 :Entity 节点数

磁盘侧禁区判定 = vault_backfill.is_blacklisted_for_backfill (与回填**同一**
判定函数, 不是拷贝) — 保证"census 说的禁区"就是"回填现在拦的禁区"。
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

#: structured_writer 的全部写入通道 (attributes.source 的取值域)
SOURCES = ["callout", "error", "relation", "conversation"]


def _fmt_table(rows: list[tuple], headers: tuple) -> str:
    widths = [max(len(str(r[i])) for r in [headers, *rows]) for i in range(len(headers))]
    lines = ["  ".join(str(c).ljust(w) for c, w in zip(r, widths)) for r in [headers, *rows]]
    lines.insert(1, "  ".join("-" * w for w in widths))
    return "\n".join(lines)


async def run(args: argparse.Namespace) -> int:
    from app.config import DEFAULT_GROUP_ID, get_current_vault_id, settings
    from app.core.subject_config import build_vault_group_id
    from app.graphiti.group_id_compat import sanitize_group_id_for_graphiti
    from app.services.vault_backfill import is_blacklisted_for_backfill

    vault = Path(args.vault or settings.canvas_base_path)
    if not vault.is_dir():
        print(f"⛔ vault 不存在: {vault}")
        return 2

    startup_gid = sanitize_group_id_for_graphiti(build_vault_group_id(get_current_vault_id()))
    cli_gid = sanitize_group_id_for_graphiti(DEFAULT_GROUP_ID)

    print("=" * 72)
    print("Graphiti 结构化图污染只读盘点 (P1-05b 步骤 2)")
    print("=" * 72)
    print(f"vault           : {vault}")
    print(f"启动回填组(物理): {startup_gid}")
    print(f"CLI 脚本组(物理): {cli_gid}")
    print(f"Neo4j           : {settings.NEO4J_URI}")

    # ── 磁盘侧全量枚举: 禁区 / 合法 两桶 (与 backfill 同一判定函数) ──────────
    skip_dirs = set(settings.effective_vault_skip_dirs())
    skip_dirs.add("templates")
    forbidden_stems: set[str] = set()
    legal_stems: set[str] = set()
    for md in vault.rglob("*.md"):
        try:
            blacklisted = is_blacklisted_for_backfill(md, vault, skip_dirs)
        except ValueError:
            continue  # 非 vault 内路径 (不应出现, 防御)
        (forbidden_stems if blacklisted else legal_stems).add(md.stem)

    print(f"\n磁盘侧: 禁区 stem {len(forbidden_stems)} 个 · 合法 stem {len(legal_stems)} 个")

    # ── Q4 碰撞体检 (先做 — 决定 Q1 的可信度与执行步的定位手段) ─────────────
    collisions = sorted(forbidden_stems & legal_stems)
    print("\n" + "─" * 72)
    print(f"Q4 碰撞体检: 禁区 stem ∩ 合法 stem = {len(collisions)} 个")
    if collisions:
        print("  ⛔ 存在碰撞 — 按 stem 隔离会误杀合法节点的边, 执行步必须降级到")
        print("     按预计算 uuid5 精确匹配。碰撞文件名 (仅文件名, 无内容):")
        for stem in collisions:
            print(f"     - {stem}")
    else:
        print("  ✅ 无碰撞 — 按 stem 定位即精确定位")

    from neo4j import AsyncGraphDatabase

    driver = AsyncGraphDatabase.driver(settings.NEO4J_URI, auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD))
    forbidden = sorted(forbidden_stems)
    all_stems = sorted(forbidden_stems | legal_stems)
    try:
        # ── Q0 组分布 ────────────────────────────────────────────────────────
        q0, _, _ = await driver.execute_query(
            """
            MATCH ()-[r:RELATES_TO]->()
            WHERE r.source IN $sources
            RETURN r.group_id AS gid, r.source AS source, count(r) AS c
            ORDER BY gid, source
            """,
            sources=SOURCES,
            routing_="r",
        )
        print("\n" + "─" * 72)
        print("Q0 组分布 (structured_writer 四通道边, 按 group_id × source):")
        rows = [(rec["gid"] or "(null)", rec["source"], rec["c"]) for rec in q0]
        print(_fmt_table(rows, ("group_id", "source", "edges")) if rows else "  (图中无四通道边)")
        groups = sorted({rec["gid"] for rec in q0 if rec["gid"]})

        grand_active = 0
        for gid in groups:
            print("\n" + "─" * 72)
            print(f"组 {gid}")

            # ── Q1 爆炸半径 (禁区 stem 命中) ────────────────────────────────
            q1, _, _ = await driver.execute_query(
                """
                MATCH ()-[r:RELATES_TO]->()
                WHERE r.group_id = $gid AND r.source IN $sources
                  AND r.node_id IN $forbidden
                RETURN r.source AS source,
                       count(r) AS total,
                       sum(CASE WHEN r.invalid_at IS NULL THEN 1 ELSE 0 END) AS active,
                       sum(CASE WHEN r.invalid_at IS NULL AND r.source = 'callout'
                                 AND r.annotation_id IS NOT NULL
                            THEN 1 ELSE 0 END) AS active_reconcilable
                ORDER BY source
                """,
                gid=gid,
                sources=SOURCES,
                forbidden=forbidden,
                routing_="r",
            )
            rows = [(rec["source"], rec["total"], rec["active"], rec["active_reconcilable"]) for rec in q1]
            active_sum = sum(r[2] for r in rows)
            reconcilable_sum = sum(r[3] for r in rows)
            grand_active += active_sum
            print(f"  Q1 爆炸半径 (node_id ∈ 禁区 stem, {len(forbidden)} 个 stem 参与匹配):")
            if rows:
                print(
                    "    "
                    + _fmt_table(rows, ("source", "total", "active", "active_reconcilable")).replace("\n", "\n    ")
                )
                unreachable = active_sum - reconcilable_sum
                print(
                    f"    → active 合计 {active_sum}, 其中 {unreachable} 条是现有"
                    f" invalidate_missing_callouts 永远够不到的 (无 annotation_id"
                    f" 或非 callout 通道)"
                )
            else:
                print("    (无命中)")

            # ── Q2 补集残渣 (node_id 无法从磁盘解释) ────────────────────────
            q2, _, _ = await driver.execute_query(
                """
                MATCH ()-[r:RELATES_TO]->()
                WHERE r.group_id = $gid AND r.source IN $sources
                  AND r.invalid_at IS NULL
                  AND NOT r.node_id IN $all_stems
                RETURN count(r) AS edges, count(DISTINCT r.node_id) AS orphan_ids
                """,
                gid=gid,
                sources=SOURCES,
                all_stems=all_stems,
                routing_="r",
            )
            rec = q2[0] if q2 else None
            edges = rec["edges"] if rec else 0
            orphan_ids = rec["orphan_ids"] if rec else 0
            print(
                f"  Q2 补集残渣: active 边 {edges} 条, 涉及 {orphan_ids} 个磁盘上"
                f"不存在的 node_id (文件已删/改名 — 只能人工裁定或整组处置)"
            )

            # ── Q3 被污染的 Entity 节点 ─────────────────────────────────────
            q3, _, _ = await driver.execute_query(
                """
                MATCH (n:Entity)
                WHERE n.group_id = $gid AND n.node_id IN $forbidden
                RETURN count(n) AS c
                """,
                gid=gid,
                forbidden=forbidden,
                routing_="r",
            )
            print(f"  Q3 禁区 stem 命名的 :Entity 节点: {q3[0]['c'] if q3 else 0} 个")

        print("\n" + "=" * 72)
        print(f"总结: 全部组的 Q1 active 污染边合计 {grand_active} 条")
        print("本脚本只读 — 隔离执行需用户过目本报告后另行批准。")
        print("=" * 72)
    finally:
        await driver.close()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vault", default=None, help="vault 路径 (默认 settings.canvas_base_path)")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="恒为只读 (本脚本无写模式, 参数仅为语义显式)",
    )
    return asyncio.run(run(parser.parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
