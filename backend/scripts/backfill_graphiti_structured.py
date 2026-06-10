#!/usr/bin/env python
"""Phase 4.5: vault 历史批注/原因 回填进 Graphiti 结构化图 (CLI)。

用法 (需 Neo4j 在跑):
  cd backend && .venv/bin/python scripts/backfill_graphiti_structured.py            # dry-run
  cd backend && .venv/bin/python scripts/backfill_graphiti_structured.py --execute  # 真写

幂等: 边 uuid 确定性 (内容 hash), 重跑 MERGE 不重复。
embedding: 有 GOOGLE_API_KEY 时用 GeminiEmbedder (D8, 语义召回可用);
否则 None (仅 exact-read, 后续可补)。
"""

import argparse
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true", help="真写 (默认 dry-run)")
    parser.add_argument("--vault", default=None, help="vault 路径 (默认 settings)")
    args = parser.parse_args()

    from app.config import DEFAULT_GROUP_ID, settings
    from app.services.vault_backfill import backfill_vault

    vault = args.vault or settings.canvas_base_path
    group_id = DEFAULT_GROUP_ID

    # driver: graphiti_core 官方 Neo4jDriver (EntityNode/Edge.save 需要)
    from graphiti_core.driver.neo4j_driver import Neo4jDriver

    driver = Neo4jDriver(
        uri=settings.NEO4J_URI,
        user=settings.NEO4J_USER,
        password=settings.NEO4J_PASSWORD,
    )

    # embedder (D8 硬前提): Neo4j 的 save 查询无条件调 db.create.setNodeVectorProperty,
    # embedding=None 必 NPE → execute 模式必须有可用 embedder。
    # 配置镜像 episode_worker:378-383 (embedding_model=gemini-embedding-001,
    # 默认 text-embedding-001 已 404)。
    embedder = None
    google_key = os.getenv("GOOGLE_API_KEY") or getattr(settings, "GOOGLE_API_KEY", "")
    if google_key:
        try:
            from graphiti_core.embedder.gemini import (
                GeminiEmbedder,
                GeminiEmbedderConfig,
            )

            embedder = GeminiEmbedder(
                config=GeminiEmbedderConfig(
                    api_key=google_key,
                    embedding_model="gemini-embedding-001",
                )
            )
            print("embedder: GeminiEmbedder/gemini-embedding-001")
        except Exception as e:  # noqa: BLE001
            print(f"embedder 初始化失败: {e}")
    if args.execute and embedder is None:
        print("⛔ execute 需要可用 embedder (Neo4j save 无向量会 NPE)。中止。")
        return 2

    mode = "EXECUTE 真写" if args.execute else "DRY-RUN 仅统计"
    print(f"vault: {vault}\ngroup_id: {group_id}\n模式: {mode}\n{'=' * 60}")

    stats = await backfill_vault(
        vault, driver, embedder, group_id, execute=args.execute
    )
    print(f"文件(含批注/关系): {stats['files']}")
    print(f"批注 callouts:    {stats['callouts']}")
    print(f"错误 errors:      {stats['errors']}")
    print(f"原因 relations:   {stats['relations']}")
    print(f"失败:             {stats['failed']}")
    if not args.execute:
        print("\n(dry-run 完成 — 确认数字后加 --execute 真写)")
    await driver.close()
    return 0 if stats["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
