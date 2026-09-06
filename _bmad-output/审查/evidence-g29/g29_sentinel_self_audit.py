#!/usr/bin/env python3
"""CARD-G2-9 自查 — `read_scope_sentinels_clean` 是不是一条恒 0 的死判据？

结论先写在前面：**是**（在当前 graphiti_core 0.28.2 的实现下）。本脚本给出实证，
供验收单的「本卡未证明什么」引用，不是交付物的一部分。

推理链：
  graphiti_core 的 `EpisodicNode/EntityNode.get_by_group_ids` 用的是
  `WHERE e.group_id IN $group_ids`（精确等值，本脚本 step 1 打印源码片段佐证）。
  传入单个 group_id 时，返回节点的 group_id **恒等于**该值，于是
  `group_in_read_scope(node.group_id, scope)` 的等值分支恒 True ⇒ sentinel 恒 0。

所以它**不是隔离判据**，而是「graphiti 的读侧口径 vs 生产 vault_scope 口径是否分叉」
的检测器：graphiti 哪天改成前缀匹配、或 `group_in_read_scope` 改了口径，它才会翻红。
canary 的 M1-M5 变异**没有一条覆盖它** ⇒ 本卡未证明这条判据能翻红。

step 3 反向坐实它不是恒真的**代码**：把 scope 换成一个与节点归属无关的值，
sentinel 立刻非 0 —— 判据本身有效，只是在 canary 的调用方式下走不到那个分支。
"""

from __future__ import annotations

import asyncio
import inspect
import os
import pathlib
import sys

_BACKEND = pathlib.Path(__file__).resolve().parents[3] / "backend"
sys.path.insert(0, str(_BACKEND / "tests" / "support"))
import live_port_guard  # noqa: E402  # pyright: ignore[reportMissingImports]

live_port_guard.install()
live_port_guard.register_final_accounting()
live_port_guard.assert_test_uri_not_blocked()
sys.path.insert(0, str(_BACKEND))

from datetime import datetime, timezone  # noqa: E402

from graphiti_core.driver.neo4j_driver import Neo4jDriver  # noqa: E402
from graphiti_core.nodes import EpisodeType, EpisodicNode  # noqa: E402

from app.core.vault_scope import group_in_read_scope  # noqa: E402

URI = os.environ["NEO4J_TEST_URI"]
GA, GB = "vault__g29audit_a", "vault__g29audit_b"
TS = datetime(2026, 1, 1, tzinfo=timezone.utc)


async def main() -> int:
    print("=== step 1: graphiti 的过滤条件（源码实读，不是推测）===")
    src = inspect.getsource(EpisodicNode.get_by_group_ids)
    for line in src.splitlines():
        if "group_id" in line and "WHERE" in line.upper() or "group_id IN" in line:
            print(f"  {line.strip()}")

    d = Neo4jDriver(uri=URI, user="neo4j", password="testpassword")
    try:
        for g in (GA, GB):
            await EpisodicNode(
                name="审计情节", group_id=g, source=EpisodeType.text,
                source_description="sentinel self-audit", content="x",
                valid_at=TS, created_at=TS, entity_edges=[],
            ).save(d)

        print("\n=== step 2: 用 A 的 scope 查，返回节点的 group_id 集合 ===")
        got = await EpisodicNode.get_by_group_ids(d, [GA])
        groups = sorted({n.group_id for n in got})
        outside = sum(1 for n in got if not group_in_read_scope(n.group_id, GA))
        print(f"  查询 scope = {GA}")
        print(f"  库里同时存在 {GA} 与 {GB} 两组数据")
        print(f"  返回节点的 group_id 集合 = {groups}")
        print(f"  outside_read_scope = {outside}   ← 恒 0：等值过滤下不可能非 0")

        print("\n=== step 3: 反向坐实判据本身有效（不是恒真的代码）===")
        bogus = "vault__unrelated_scope"
        outside_bogus = sum(1 for n in got if not group_in_read_scope(n.group_id, bogus))
        print(f"  把 scope 换成无关值 {bogus}")
        print(f"  outside_read_scope = {outside_bogus}   ← 非 0，说明判据会算，只是走不到")

        return 0 if (outside == 0 and outside_bogus > 0) else 1
    finally:
        for g in (GA, GB):
            for n in await EpisodicNode.get_by_group_ids(d, [g]):
                await n.delete(d)
        await d.close()


rc = asyncio.run(main())
print(f"\n{live_port_guard.STATE.summary_line()}")
sys.exit(rc)
