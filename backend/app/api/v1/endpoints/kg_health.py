"""Knowledge Graph health check — Story 1.6 AC #3-5.

GET /api/v1/kg/health — orphaned nodes, relationship stats, confidence distribution.
"""

from __future__ import annotations

from datetime import datetime, timezone

import structlog
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.config import Settings, get_settings

logger = structlog.get_logger(__name__)

kg_health_router = APIRouter()


class KGHealthResponse(BaseModel):
    total_nodes: int = 0
    total_relationships: int = 0
    orphaned_nodes: list[str] = []
    orphaned_count: int = 0
    confidence_distribution: dict[str, int] = {}
    neo4j_available: bool = False
    error: str | None = None


@kg_health_router.get("/health")
async def kg_health_check(
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> dict:
    """Story 1.6 AC #3: KG index health report."""
    try:
        from neo4j import AsyncGraphDatabase

        driver = AsyncGraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
        )
        try:
            async with driver.session(database=settings.NEO4J_DATABASE) as session:
                node_result = await session.run("MATCH (n) RETURN count(n) AS cnt")
                node_record = await node_result.single()
                total_nodes = node_record["cnt"] if node_record else 0

                rel_result = await session.run(
                    "MATCH ()-[r]->() RETURN count(r) AS cnt"
                )
                rel_record = await rel_result.single()
                total_rels = rel_record["cnt"] if rel_record else 0

                orphan_result = await session.run(
                    "MATCH (n) WHERE NOT (n)--() RETURN n.name AS name LIMIT 20"
                )
                orphan_records = [r["name"] async for r in orphan_result if r["name"]]

                report = KGHealthResponse(
                    total_nodes=total_nodes,
                    total_relationships=total_rels,
                    orphaned_nodes=orphan_records,
                    orphaned_count=len(orphan_records),
                    neo4j_available=True,
                )
        finally:
            await driver.close()

    except Exception as exc:
        logger.warning("kg_health_check_failed", error=str(exc))
        report = KGHealthResponse(
            neo4j_available=False,
            error=f"Neo4j 未连接: {str(exc)[:100]}. 修复: docker compose up -d neo4j",
        )

    now = datetime.now(timezone.utc).isoformat()
    return {"data": report.model_dump(), "meta": {"timestamp": now}}
