#!/usr/bin/env python
"""批次1'③ 测试数据清污 — B 迁出方案 (MEM-FLYWHEEL-2026-07-22, 用户拍板 2026-07-23)。

把生产组内的测试污染 (对抗审查 C1 清单, 每日审计实测 6 节点) 迁出到隔离组
`quarantine__mem_cleanup` — 不带 vault__ 前缀, 生产检索的组前缀扩展与污染
审计永远不再命中; 原组名存 `quarantined_from` + 时间戳存 `quarantined_at`,
--restore 一键可逆。

对象 (2026-07-23 盘点):
  节点: session:m3-e2e-sessionen ×2 (主组+semantic), UAT-2.5.X-test,
        m3-e2e 蒸馏 Episodic ×2, uat_2_5_x_test 白板组全量
  边:   上述节点全部关联边 (MENTIONS/RELATES_TO) + 垃圾 fact「测试」边 (q9 rank1)

用法 (离线迁移工具, 唯一允许 dry-run 默认的场景):
  cd backend && .venv/bin/python scripts/quarantine_test_pollution.py            # dry-run 列清单
  .venv/bin/python scripts/quarantine_test_pollution.py --execute               # 执行迁出
  .venv/bin/python scripts/quarantine_test_pollution.py --restore               # 反向恢复
"""

import argparse
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

QUARANTINE_GROUP = "quarantine__mem_cleanup"

# 污染节点谓词 (与 memory-health.sh 审计 + 2026-07-23 盘点口径一致)
NODE_PREDICATE = """(
    coalesce(n.name,'') CONTAINS 'TestConcept' OR coalesce(n.content,'') CONTAINS 'TestConcept'
    OR coalesce(n.name,'') CONTAINS 'UAT-2.5' OR coalesce(n.content,'') CONTAINS 'UAT-2.5'
    OR coalesce(n.name,'') CONTAINS 'm3-e2e' OR coalesce(n.content,'') CONTAINS 'm3-e2e'
    OR n.group_id = 'vault__canvas_vault__uat_2_5_x_test'
)"""

# 垃圾 fact 边谓词 (裸词「测试」— 对抗审查 q9 rank1 满分垃圾)
EDGE_PREDICATE = """(
    r.fact = '测试' OR coalesce(r.fact,'') CONTAINS 'm3-e2e'
    OR coalesce(r.fact,'') CONTAINS 'UAT-2.5' OR coalesce(r.fact,'') CONTAINS 'TestConcept'
)"""


async def main() -> int:
    parser = argparse.ArgumentParser(description="测试污染 B 迁出 (默认 dry-run)")
    parser.add_argument("--execute", action="store_true", help="执行迁出")
    parser.add_argument("--restore", action="store_true", help="从隔离组恢复原组")
    args = parser.parse_args()

    from app.clients.neo4j_client import get_neo4j_client

    client = get_neo4j_client()
    await client.initialize()

    if args.restore:
        n = await client.run_query(
            "MATCH (n) WHERE n.group_id = $q AND n.quarantined_from IS NOT NULL "
            "SET n.group_id = n.quarantined_from "
            "REMOVE n.quarantined_from, n.quarantined_at "
            "RETURN count(n) AS c",
            q=QUARANTINE_GROUP,
        )
        e = await client.run_query(
            "MATCH ()-[r]-() WHERE r.group_id = $q AND r.quarantined_from IS NOT NULL "
            "SET r.group_id = r.quarantined_from "
            "REMOVE r.quarantined_from, r.quarantined_at "
            "RETURN count(DISTINCT r) AS c",
            q=QUARANTINE_GROUP,
        )
        print(f"♻️ 已恢复: 节点 {n[0]['c']}, 边 {e[0]['c']}")
        return 0

    # 盘点 (dry-run 与 execute 共用同一谓词 — 所见即所迁)
    nodes = await client.run_query(
        f"MATCH (n) WHERE {NODE_PREDICATE} AND n.group_id <> $q "
        "RETURN labels(n) AS labels, n.group_id AS gid, "
        "left(coalesce(n.name, n.content, ''), 60) AS preview",
        q=QUARANTINE_GROUP,
    )
    rel_edges = await client.run_query(
        f"MATCH (n)-[r]-() WHERE {NODE_PREDICATE} AND r.group_id <> $q "
        "RETURN type(r) AS t, count(DISTINCT r) AS c",
        q=QUARANTINE_GROUP,
    )
    junk_edges = await client.run_query(
        f"MATCH ()-[r]->() WHERE {EDGE_PREDICATE} AND r.group_id <> $q "
        "RETURN type(r) AS t, left(r.fact, 40) AS fact",
        q=QUARANTINE_GROUP,
    )

    print(f"污染节点 {len(nodes or [])}:")
    for rec in nodes or []:
        d = rec if isinstance(rec, dict) else rec.data()
        print(f"  {d['labels']} @{d['gid']}: {d['preview']}")
    print("关联边:")
    for rec in rel_edges or []:
        d = rec if isinstance(rec, dict) else rec.data()
        print(f"  {d['t']} × {d['c']}")
    print(f"垃圾 fact 边 {len(junk_edges or [])}:")
    for rec in junk_edges or []:
        d = rec if isinstance(rec, dict) else rec.data()
        print(f"  {d['t']}: {d['fact']}")

    if not args.execute:
        print("\n(dry-run — 加 --execute 执行迁出)")
        return 0

    # 执行: 先边后节点 (边谓词依赖节点还在原判定内, 顺序无硬依赖但保持确定性)
    e1 = await client.run_query(
        f"MATCH (n)-[r]-() WHERE {NODE_PREDICATE} AND r.group_id <> $q "
        "SET r.quarantined_from = r.group_id, r.quarantined_at = datetime(), "
        "    r.group_id = $q "
        "RETURN count(DISTINCT r) AS c",
        q=QUARANTINE_GROUP,
    )
    e2 = await client.run_query(
        f"MATCH ()-[r]->() WHERE {EDGE_PREDICATE} AND r.group_id <> $q "
        "SET r.quarantined_from = coalesce(r.group_id, ''), r.quarantined_at = datetime(), "
        "    r.group_id = $q "
        "RETURN count(DISTINCT r) AS c",
        q=QUARANTINE_GROUP,
    )
    n1 = await client.run_query(
        f"MATCH (n) WHERE {NODE_PREDICATE} AND n.group_id <> $q "
        "SET n.quarantined_from = coalesce(n.group_id, ''), n.quarantined_at = datetime(), "
        "    n.group_id = $q "
        "RETURN count(n) AS c",
        q=QUARANTINE_GROUP,
    )
    print(
        f"\n✅ 迁出完成: 节点 {n1[0]['c']}, 关联边 {e1[0]['c']}, 垃圾边 {e2[0]['c']} "
        f"→ {QUARANTINE_GROUP}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
