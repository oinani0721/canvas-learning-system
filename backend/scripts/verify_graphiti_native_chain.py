#!/usr/bin/env python
"""Phase 5 (GRAPHITI-NATIVE-MEMORY-2026-06-10): Graphiti-native 主链端到端验证。

替代旧 verify_targeted_exam_chain.py (那是 G-FAKE 时代的探针)。
4 断言 (真实 Neo4j, probe 自清理):
  (a) structured_writer 写出 :Entity-[RELATES_TO {node_id, source}]->:Entity (canonical)
  (b) 不再新建 :EpisodicNode{node_id} (Fix-D 模式已死)
  (c) reader 读回刚写的 (批注/原因/对话摘要, 方向+active 过滤正确)
  (d) belief 3 版本链在真实 Neo4j 正确 (valid_at/invalid_at 真消费 — 时序回溯)

用法: cd backend && .venv/bin/python scripts/verify_graphiti_native_chain.py
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PROBE = "__gn_probe__"
GREEN, RED, RESET = "\033[92m", "\033[91m", "\033[0m"
_failures: list[str] = []


def check(ok: bool, msg: str) -> None:
    if ok:
        print(f"  {GREEN}✅ PASS{RESET}  {msg}")
    else:
        print(f"  {RED}❌ FAIL{RESET}  {msg}")
        _failures.append(msg)


async def main() -> int:
    from app.config import DEFAULT_GROUP_ID, settings
    from graphiti_core.driver.neo4j_driver import Neo4jDriver
    from graphiti_core.embedder.gemini import GeminiEmbedder, GeminiEmbedderConfig

    from app.services import graphiti_belief_service as bs
    from app.services.graphiti_memory_reader import (
        read_node_conversation_summary,
        read_node_edge_reasons,
        read_node_tips,
    )
    from app.services.graphiti_structured_writer import (
        write_callout,
        write_conversation_summary,
        write_relation_reason,
    )

    google_key = os.getenv("GOOGLE_API_KEY") or getattr(settings, "GOOGLE_API_KEY", "")
    if not google_key:
        print("⛔ 需 GOOGLE_API_KEY (D8: Neo4j save 无向量必 NPE)")
        return 2
    driver = Neo4jDriver(
        uri=settings.NEO4J_URI,
        user=settings.NEO4J_USER,
        password=settings.NEO4J_PASSWORD,
    )
    embedder = GeminiEmbedder(
        config=GeminiEmbedderConfig(
            api_key=google_key, embedding_model="gemini-embedding-001"
        )
    )
    gid = DEFAULT_GROUP_ID
    now = datetime.now(timezone.utc)
    src, tgt = f"{PROBE}src", f"{PROBE}tgt"

    async def cleanup():
        await driver.execute_query(
            "MATCH (n:Entity) WHERE n.name STARTS WITH $p DETACH DELETE n", p=PROBE
        )
        await driver.execute_query(
            "MATCH (e:EpisodicNode) WHERE e.node_id STARTS WITH $p DETACH DELETE e",
            p=PROBE,
        )

    try:
        await cleanup()
        print("═" * 64)
        print("(a)+(c) 写→读: structured_writer → reader (真实 Neo4j)")
        print("═" * 64)
        await write_callout(
            driver,
            embedder,
            node_id=src,
            group_id=gid,
            callout_type="tip",
            text="probe 批注",
            occurred_at=now,
        )
        await write_relation_reason(
            driver,
            embedder,
            source_node_id=src,
            target_node_id=tgt,
            group_id=gid,
            relation_type="refines",
            reason="probe 拉出原因",
            occurred_at=now,
        )
        await write_conversation_summary(
            driver,
            embedder,
            node_id=src,
            group_id=gid,
            summary="probe 对话摘要",
            occurred_at=now,
        )
        # (a) canonical 图形状
        records, _, _ = await driver.execute_query(
            "MATCH (:Entity)-[e:RELATES_TO]->(:Entity) "
            "WHERE e.node_id STARTS WITH $p "
            "RETURN count(e) AS n",
            p=PROBE,
        )
        check(
            records[0]["n"] == 3,
            f"(a) :Entity-RELATES_TO canonical 边 = {records[0]['n']}/3",
        )
        # (c) reader 读回
        tips = await read_node_tips(driver, src)
        # F10 去重修复后 fact = canonical_callout_fact("[类型·理解度] 裸正文")
        check(tips == ["[tip] probe 批注"], f"(c) read_node_tips = {tips}")
        reasons_src = await read_node_edge_reasons(driver, src)
        reasons_tgt = await read_node_edge_reasons(driver, tgt)
        check(reasons_src == ["probe 拉出原因"], f"(c) 出边原因(src) = {reasons_src}")
        check(reasons_tgt == [], f"(c) 入边不泄漏(tgt) = {reasons_tgt}")
        conv = await read_node_conversation_summary(driver, src)
        check(conv == "probe 对话摘要", f"(c) 对话摘要 = {conv!r}")

        print("═" * 64)
        print("(b) 不再产出 :EpisodicNode{node_id} (Fix-D 模式已死)")
        print("═" * 64)
        records, _, _ = await driver.execute_query(
            "MATCH (e:EpisodicNode) WHERE e.node_id STARTS WITH $p "
            "RETURN count(e) AS n",
            p=PROBE,
        )
        check(
            records[0]["n"] == 0, f"(b) probe :EpisodicNode = {records[0]['n']} (应 0)"
        )

        print("═" * 64)
        print("(d) belief 3 版本链 (真实 Neo4j, bitemporal 真消费)")
        print("═" * 64)
        graphiti = SimpleNamespace(driver=driver, embedder=embedder)
        bk = f"callout:{src}:probe"
        for i, (ts, fact) in enumerate(
            [
                (now - timedelta(days=4), "v1: 初版理解"),
                (now - timedelta(days=2), "v2: 修正理解"),
                (now, "v3: 最终理解"),
            ],
            1,
        ):
            await bs.update_belief_version_chain(
                graphiti,
                belief_key=bk,
                group_id=gid,
                fact=fact,
                occurred_at=ts,
                node_id=src,
                source="callout",
            )
        history = await bs.get_belief_history(
            graphiti, bk, gid, as_of=now - timedelta(days=3)
        )
        check(len(history) == 3, f"(d) 版本链长度 = {len(history)}/3")
        superseded = [h for h in history if h["status"] == "superseded"]
        check(len(superseded) == 2, f"(d) superseded 旧版 = {len(superseded)}/2")
        current = [h for h in history if h["current"]]
        check(
            len(current) == 1 and current[0]["fact"] == "v3: 最终理解",
            f"(d) current = {current[0]['fact'] if current else None}",
        )
        as_of_active = [h for h in history if h["active_at_as_of"]]
        check(
            len(as_of_active) == 1 and as_of_active[0]["fact"] == "v1: 初版理解",
            f"(d) as_of(3天前) 当时认知 = {as_of_active[0]['fact'] if as_of_active else None}",
        )
    finally:
        await cleanup()
        await driver.close()
        print(f"\n{GREEN}probe 已清理。{RESET}")

    print("═" * 64)
    if _failures:
        print(f"{RED}❌ {len(_failures)} 项失败{RESET}")
        return 1
    print(
        f"{GREEN}✅ 全部断言通过 — Graphiti-native 主链 (写/读/belief 时序) 端到端可用{RESET}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
