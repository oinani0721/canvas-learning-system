#!/usr/bin/env python
"""P1-05b 步骤 3: Graphiti 结构化图污染隔离执行 (用户 2026-08-19 批准, 组名 B)。

用法:
  cd backend && .venv/bin/python scripts/quarantine_graphiti_pollution.py           # dry-run
  cd backend && .venv/bin/python scripts/quarantine_graphiti_pollution.py --apply   # 真写

手法 (计划裁定):
  - **改 group_id 到隔离组** `quarantine__p105b` — 不 DELETE (可回滚)、不只设
    invalid_at (_search_graphiti 不传 SearchFilters, invalid_at 挡不住语义检索)。
  - 组名沿 quarantine__mem_cleanup 既有先例: 不带 vault 前缀, 结构上永远不会被
    _expand_vault_subgroups (按 `vault__canvas_vault__*` 前缀扫**节点**) 并回检索面。
  - **裸 Cypher SET** — 绕开 EntityEdge.save() 的 embedding 回载 NPE 陷阱
    (graphiti_structured_writer.py:317 实测; canvas_projection_sync /
    graphiti_belief_service 均有裸 Cypher 先例)。
  - 同时打 quarantined_reason / quarantined_at — 一条 Cypher 可整批回滚:
      MATCH ()-[r:RELATES_TO]->() WHERE r.group_id=$q AND r.quarantined_reason=$why
      SET r.group_id=$orig REMOVE r.quarantined_reason, r.quarantined_at

定位 (census 2026-08-19 实测背书):
  - 按禁区 stem 精确匹配 (Q4 碰撞体检: 碰撞 stem 命中 active 边 0 条 → 无误杀面);
    碰撞 stem 仍防御性排除并单独报告。
  - 不限 invalid_at IS NULL: 已失效边留在主组同样可被语义检索召回, 一并迁走。

不输出 fact 正文; 只输出计数与聚合。
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SOURCES = ["callout", "error", "relation", "conversation"]
QUARANTINE_GROUP = "quarantine__p105b"
QUARANTINE_REASON = "p105b_admission_backfill_gap"


async def run(args: argparse.Namespace) -> int:
    from app.config import get_current_vault_id, settings
    from app.core.subject_config import build_vault_group_id
    from app.graphiti.group_id_compat import sanitize_group_id_for_graphiti
    from app.services.vault_backfill import is_blacklisted_for_backfill

    vault = Path(args.vault or settings.canvas_base_path)
    if not vault.is_dir():
        print(f"⛔ vault 不存在: {vault}")
        return 2
    target_gid = sanitize_group_id_for_graphiti(build_vault_group_id(get_current_vault_id()))

    # 磁盘划分 (与 census / backfill 同一判定函数; P1-05c 已委托 check_vault_path)
    forbidden: set[str] = set()
    legal: set[str] = set()
    for md in vault.rglob("*.md"):
        try:
            (forbidden if is_blacklisted_for_backfill(md, vault) else legal).add(md.stem)
        except ValueError:
            continue
    collisions = sorted(forbidden & legal)
    safe_forbidden = sorted(forbidden - legal)  # 碰撞 stem 防御性排除 (census: 命中 0)

    mode = "APPLY 真写" if args.apply else "DRY-RUN 只读"
    print("=" * 72)
    print(f"P1-05b 污染隔离 · {mode}")
    print(f"源组: {target_gid} → 隔离组: {QUARANTINE_GROUP}")
    print(f"禁区 stem {len(forbidden)} 个 (碰撞排除 {len(collisions)} 个: {collisions or '无'})")
    print("=" * 72)

    from neo4j import AsyncGraphDatabase

    driver = AsyncGraphDatabase.driver(settings.NEO4J_URI, auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD))
    try:
        # 先点名 (只读): 将被隔离的边按 source 计数
        preview, _, _ = await driver.execute_query(
            """
            MATCH ()-[r:RELATES_TO]->()
            WHERE r.group_id = $gid AND r.source IN $sources AND r.node_id IN $stems
            RETURN r.source AS source, count(r) AS c,
                   sum(CASE WHEN r.invalid_at IS NULL THEN 1 ELSE 0 END) AS active
            ORDER BY source
            """,
            gid=target_gid,
            sources=SOURCES,
            stems=safe_forbidden,
            routing_="r",
        )
        total = sum(rec["c"] for rec in preview)
        for rec in preview:
            print(f"  待隔离: source={rec['source']}  total={rec['c']}  active={rec['active']}")
        print(f"  合计 {total} 条")
        if not args.apply:
            if total == 0:
                print("  (无待隔离边)")
            print("\nDRY-RUN 结束 — 加 --apply 执行。")
            return 0
        if total == 0:
            # P1-05c: 幂等重跑不提前退出 — 边已隔离时仍要跑节点隔离与四门验收
            print("  (无待隔离边 — 幂等重跑, 继续节点隔离与验收门)")

        moved, _, _ = await driver.execute_query(
            """
            MATCH ()-[r:RELATES_TO]->()
            WHERE r.group_id = $gid AND r.source IN $sources AND r.node_id IN $stems
            SET r.group_id = $q_gid,
                r.quarantined_reason = $why,
                r.quarantined_at = datetime()
            RETURN count(r) AS c
            """,
            gid=target_gid,
            sources=SOURCES,
            stems=safe_forbidden,
            q_gid=QUARANTINE_GROUP,
            why=QUARANTINE_REASON,
        )
        print(f"\n✅ 已隔离 {moved[0]['c']} 条边 → {QUARANTINE_GROUP}")

        # ── 节点隔离 (P1-05c, Codex 三轮 F-03 证据二): 禁区 stem 命名的主组
        # Entity 节点仍进 combined node lane (name/summary/name_embedding 非空)。
        # 只迁**无主组活边**的节点 — 有活边的迁走会造边端点跨组悬挂, 点名报告
        # 留人工裁定。
        n_moved, _, _ = await driver.execute_query(
            """
            MATCH (n:Entity)
            WHERE n.group_id = $gid AND n.node_id IN $stems
              AND NOT EXISTS {
                  MATCH (n)-[r:RELATES_TO]-()
                  WHERE r.group_id = $gid AND r.invalid_at IS NULL
              }
            SET n.group_id = $q_gid,
                n.quarantined_reason = $why,
                n.quarantined_at = datetime()
            RETURN count(n) AS c
            """,
            gid=target_gid,
            stems=safe_forbidden,
            q_gid=QUARANTINE_GROUP,
            why=QUARANTINE_REASON,
        )
        n_stuck, _, _ = await driver.execute_query(
            """
            MATCH (n:Entity)
            WHERE n.group_id = $gid AND n.node_id IN $stems
            RETURN count(n) AS c
            """,
            gid=target_gid,
            stems=safe_forbidden,
            routing_="r",
        )
        print(
            f"✅ 已隔离 {n_moved[0]['c']} 个禁区 Entity 节点; 仍滞留主组 {n_stuck[0]['c']} 个 (有主组活边, 需人工裁定)"
        )

        # ── 验收三门 ─────────────────────────────────────────────────────
        # 门 1: 源组内禁区 stem 命中归零
        g1, _, _ = await driver.execute_query(
            """
            MATCH ()-[r:RELATES_TO]->()
            WHERE r.group_id = $gid AND r.source IN $sources AND r.node_id IN $stems
            RETURN count(r) AS c
            """,
            gid=target_gid,
            sources=SOURCES,
            stems=safe_forbidden,
            routing_="r",
        )
        print(f"门1 源组残留: {g1[0]['c']} (必须 0)")

        # 门 2: 检索面子组枚举 (与 memory_service._expand_vault_subgroups
        # 同一条 Cypher, 按**节点** group_id 扫 vault 前缀) 不含隔离组
        g2, _, _ = await driver.execute_query(
            "MATCH (n) WHERE n.group_id STARTS WITH $prefix RETURN DISTINCT n.group_id AS gid LIMIT 50",
            prefix=target_gid + "__",
            routing_="r",
        )
        subgroups = sorted(str(rec["gid"]) for rec in g2 if rec["gid"])
        leak = [g for g in subgroups if QUARANTINE_GROUP in g or "quarantin" in g.lower()]
        print(f"门2 子组枚举: {subgroups or '(空)'} — 隔离组混入: {leak or '无'} (必须无)")

        # 门 3 (机制面): 隔离组不在检索组集合 {主组, __semantic, 子组枚举} 中,
        # graphiti search_ 按 group_ids 过滤边 → 隔离边结构上不可召回
        search_groups = {target_gid, target_gid + "__semantic", *subgroups}
        print(f"门3 检索组集合含隔离组: {QUARANTINE_GROUP in search_groups} (必须 False)")

        # 门 4 (P1-05c, 真实读路径冒烟 — 替代此前被 Codex 三轮判"伪门"的纯
        # set 检查): 用**生产精确 reader** 以主组身份实测隔离内容不可读回。
        # 修复前实锤: get_by_node_uuid 不查边 group, read_node_tips 读回隔离边。
        q_nodes, _, _ = await driver.execute_query(
            "MATCH ()-[r:RELATES_TO]->() WHERE r.group_id = $q RETURN DISTINCT r.node_id AS nid",
            q=QUARANTINE_GROUP,
            routing_="r",
        )
        recalled = -1
        try:
            from graphiti_core.driver.neo4j_driver import Neo4jDriver

            from app.config import get_current_vault_id as _gvid
            from app.core.subject_config import build_vault_group_id as _bgid
            from app.services.graphiti_memory_reader import (
                read_node_edge_reasons,
                read_node_errors,
                read_node_tips,
            )

            logical_gid = _bgid(_gvid())
            gdriver = Neo4jDriver(uri=settings.NEO4J_URI, user=settings.NEO4J_USER, password=settings.NEO4J_PASSWORD)
            try:
                recalled = 0
                for rec in q_nodes:
                    nid = str(rec["nid"] or "")
                    if not nid:
                        continue
                    recalled += len(await read_node_tips(gdriver, nid, group_id=logical_gid))
                    recalled += len(await read_node_errors(gdriver, nid, group_id=logical_gid))
                    recalled += len(await read_node_edge_reasons(gdriver, nid, group_id=logical_gid))
            finally:
                await gdriver.close()
            print(
                f"门4 精确读冒烟: 隔离 node_id ×{len(q_nodes)} 经 "
                f"read_node_tips/errors/edge_reasons(主组身份) 召回 {recalled} 条 (必须 0)"
            )
        except Exception as e:  # noqa: BLE001 — 冒烟失败按未过处理, 不静默
            print(f"门4 冒烟执行失败 (按未过处理): {e}")

        ok = g1[0]["c"] == 0 and not leak and QUARANTINE_GROUP not in search_groups and recalled == 0
        print("\n" + ("✅ 四门全过" if ok else "⛔ 验收未过 — 检查上方输出"))
        return 0 if ok else 1
    finally:
        await driver.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="真写 (默认 dry-run)")
    parser.add_argument("--vault", default=None, help="vault 路径 (默认 settings.canvas_base_path)")
    return asyncio.run(run(parser.parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
