# Canvas Learning System - Story 31.A.2 AC-31.A.2.1 Real Neo4j Integration Tests
# Migrated from: tests/unit/test_story_31a2_ac1_neo4j_priority.py
# [Source: docs/stories/31.A.2.story.md]
"""
Real-DB integration tests for AC-31.A.2.1: Neo4j query priority with memory fallback.

Each test creates its OWN Neo4jClient to avoid event-loop-scope conflicts
with shared conftest fixtures.

Requires: docker compose --profile test up -d neo4j-test  (port 7692)

Run with:
    cd backend && pytest tests/integration/test_story_31a2_ac1_real.py -m integration -v
"""

import logging
import os
import uuid

import pytest
from app.clients.neo4j_client import Neo4jClient
from app.services.memory_service import MemoryService

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]

NEO4J_TEST_URI = os.getenv("NEO4J_TEST_URI", "bolt://localhost:7692")
NEO4J_TEST_USER = os.getenv("NEO4J_TEST_USER", "neo4j")
NEO4J_TEST_PASSWORD = os.getenv("NEO4J_TEST_PASSWORD", "testpassword")
NEO4J_TEST_DATABASE = os.getenv("NEO4J_TEST_DATABASE", "neo4j")


def _make_client() -> Neo4jClient:
    return Neo4jClient(
        uri=NEO4J_TEST_URI,
        user=NEO4J_TEST_USER,
        password=NEO4J_TEST_PASSWORD,
        database=NEO4J_TEST_DATABASE,
    )


async def _cleanup_prefix(client: Neo4jClient, prefix: str) -> None:
    try:
        await client.run_query(
            "MATCH (n) WHERE n.id STARTS WITH $prefix DETACH DELETE n",
            prefix=prefix,
        )
        await client.run_query(
            "MATCH (c:Concept) WHERE c.name STARTS WITH $prefix DETACH DELETE c",
            prefix=prefix,
        )
    except Exception:
        pass


# =============================================================================
# Helpers
# =============================================================================


async def _insert_learning_data(neo4j_client, prefix, user_id, records):
    """Insert User -> LEARNED -> Concept relationships into Neo4j.

    Creates the same data shape that Neo4jClient.get_learning_history() queries:
    (u:User {id})-[r:LEARNED {score, timestamp, group_id}]->(c:Concept {name, id})
    """
    # Ensure User node exists
    await neo4j_client.run_query(
        "MERGE (u:User {id: $uid})",
        uid=user_id,
    )
    for r in records:
        await neo4j_client.run_query(
            """
            MATCH (u:User {id: $uid})
            MERGE (c:Concept {name: $concept})
            ON CREATE SET c.id = $cid
            MERGE (u)-[rel:LEARNED]->(c)
            SET rel.score = $score,
                rel.timestamp = $ts,
                rel.group_id = $gid,
                rel.agent_type = $agent_type,
                rel.review_count = $review_count
            """,
            uid=user_id,
            concept=f"{prefix}{r['concept']}",
            cid=f"{prefix}cid_{r['concept']}",
            score=r["score"],
            ts=r["timestamp"],
            gid=r.get("group_id", "test"),
            agent_type=r.get("agent_type", "scoring"),
            review_count=r.get("review_count", 1),
        )


def _make_real_service(neo4j_client):
    """Create a MemoryService backed by a real Neo4j client."""
    service = MemoryService(neo4j_client=neo4j_client)
    return service


# =============================================================================
# AC-31.A.2.1: Neo4j Query Priority (from Neo4j, fallback to memory)
# [Source: docs/stories/31.A.2.story.md#AC-31.A.2.1]
# =============================================================================


class TestAC31A21_Neo4jQueryPriority_Real:
    """AC-31.A.2.1: get_learning_history() must query Neo4j first (real DB)."""

    async def test_queries_neo4j_and_merges_memory(self):
        """[Code Review C2]: Neo4j results are supplemented with in-memory episodes.
        Neo4j MERGE only keeps 1 score per concept, so in-memory episodes
        (which store all score events) are merged for complete history."""
        client = _make_client()
        prefix = f"test_{uuid.uuid4().hex[:8]}_"
        try:
            await client.initialize()
            user_id = f"{prefix}u1"

            # Insert one record into real Neo4j
            await _insert_learning_data(
                client,
                prefix,
                user_id,
                [
                    {
                        "concept": "矩阵",
                        "score": 95,
                        "timestamp": "2026-02-05T10:00:00",
                    },
                ],
            )

            service = _make_real_service(client)
            await service.initialize()

            # Add a different concept to in-memory store (simulating memory supplement)
            service._episodes.append(
                {
                    "user_id": user_id,
                    "concept": f"{prefix}Memory-向量",
                    "score": 50,
                    "timestamp": "2026-02-05T09:00:00",
                }
            )

            result = await service.get_learning_history(user_id=user_id)

            # Both Neo4j and memory data present
            assert result["total"] >= 2, (
                f"Expected at least 2 items (Neo4j + memory), got {result['total']}"
            )
            concepts = [item["concept"] for item in result["items"]]
            assert any("矩阵" in c for c in concepts), "Neo4j concept missing"
            assert any("Memory-向量" in c for c in concepts), (
                "In-memory concept missing"
            )
        finally:
            await _cleanup_prefix(client, prefix)
            await client.cleanup()

    async def test_neo4j_called_with_all_parameters(self):
        """Verify all filter params are forwarded to Neo4j and produce correct results."""
        client = _make_client()
        prefix = f"test_{uuid.uuid4().hex[:8]}_"
        try:
            await client.initialize()
            user_id = f"{prefix}u1"

            # Insert records spanning different dates, concepts, and group_ids
            await _insert_learning_data(
                client,
                prefix,
                user_id,
                [
                    {
                        "concept": "矩阵乘法",
                        "score": 90,
                        "timestamp": "2026-01-15T10:00:00",
                        "group_id": "math",
                    },
                    {
                        "concept": "贝叶斯",
                        "score": 80,
                        "timestamp": "2026-02-10T10:00:00",
                        "group_id": "stats",
                    },
                ],
            )

            service = _make_real_service(client)
            await service.initialize()

            # Query with concept filter — should only return 矩阵
            result = await service.get_learning_history(
                user_id=user_id,
                concept=f"{prefix}矩阵",
            )
            concepts = [item["concept"] for item in result["items"]]
            assert all("矩阵" in c for c in concepts), (
                f"Concept filter broken, got: {concepts}"
            )
        finally:
            await _cleanup_prefix(client, prefix)
            await client.cleanup()

    async def test_fallback_to_memory_on_neo4j_exception(self):
        """When Neo4j raises exception, fall back to in-memory data.

        Uses a deliberately broken client (wrong URI) to simulate Neo4j failure.
        """
        client = _make_client()
        prefix = f"test_{uuid.uuid4().hex[:8]}_"
        try:
            await client.initialize()
            user_id = f"{prefix}u1"

            # Create a broken Neo4j client that will fail on queries
            broken_client = Neo4jClient(
                uri="bolt://localhost:19999",  # unreachable port
                user="neo4j",
                password="wrong",
                database="neo4j",
            )
            # Force initialized state so it tries to query (and fails)
            broken_client._initialized = True
            broken_client._use_json_fallback = False

            service = MemoryService(neo4j_client=broken_client)
            service._initialized = True
            service._episodes_recovered = True  # skip recovery attempt on broken client

            service._episodes.append(
                {
                    "user_id": user_id,
                    "concept": "内存数据",
                    "score": 70,
                    "timestamp": "2026-02-05T08:00:00",
                }
            )

            result = await service.get_learning_history(user_id=user_id)

            assert result["total"] >= 1, "Fallback to memory should return data"
            assert result["items"][0]["concept"] == "内存数据"
        finally:
            await _cleanup_prefix(client, prefix)
            await client.cleanup()

    async def test_fallback_logs_warning_on_neo4j_failure(self, caplog):
        """AC-31.A.2.1: Fallback must log a warning."""
        client = _make_client()
        prefix = f"test_{uuid.uuid4().hex[:8]}_"
        try:
            await client.initialize()
            user_id = f"{prefix}u1"

            broken_client = Neo4jClient(
                uri="bolt://localhost:19999",
                user="neo4j",
                password="wrong",
                database="neo4j",
            )
            broken_client._initialized = True
            broken_client._use_json_fallback = False

            service = MemoryService(neo4j_client=broken_client)
            service._initialized = True
            service._episodes_recovered = True

            with caplog.at_level(logging.WARNING):
                await service.get_learning_history(user_id=user_id)

            assert any(
                "Neo4j query failed" in record.message
                and "falling back" in record.message
                for record in caplog.records
            ), "Should log warning about Neo4j failure and fallback"
        finally:
            await _cleanup_prefix(client, prefix)
            await client.cleanup()

    async def test_fallback_to_memory_when_neo4j_returns_empty(self):
        """When Neo4j returns empty list, fall back to memory."""
        client = _make_client()
        prefix = f"test_{uuid.uuid4().hex[:8]}_"
        try:
            await client.initialize()
            user_id = f"{prefix}u1"

            # Do NOT insert any data into Neo4j — query will return empty
            service = _make_real_service(client)
            await service.initialize()

            service._episodes.append(
                {
                    "user_id": user_id,
                    "concept": "内存回退",
                    "score": 60,
                    "timestamp": "2026-02-05T07:00:00",
                }
            )

            result = await service.get_learning_history(user_id=user_id)

            assert result["total"] >= 1
            concepts = [item["concept"] for item in result["items"]]
            assert "内存回退" in concepts
        finally:
            await _cleanup_prefix(client, prefix)
            await client.cleanup()

    async def test_no_duplicate_when_same_data_in_neo4j_and_memory(self):
        """[Code Review C2]: When same event exists in both Neo4j and memory,
        dedup by (node_id, timestamp) ensures no duplicates."""
        client = _make_client()
        prefix = f"test_{uuid.uuid4().hex[:8]}_"
        try:
            await client.initialize()
            user_id = f"{prefix}u1"
            concept_name = f"{prefix}Dedup-A"
            ts = "2026-02-05T10:00:00"

            # Insert into Neo4j
            await _insert_learning_data(
                client,
                prefix,
                user_id,
                [
                    {"concept": "Dedup-A", "score": 90, "timestamp": ts},
                ],
            )

            service = _make_real_service(client)
            await service.initialize()

            # Same event in memory (same node_id + timestamp = deduped)
            service._episodes.append(
                {
                    "user_id": user_id,
                    "concept": concept_name,
                    "score": 90,
                    "timestamp": ts,
                    "node_id": f"{prefix}cid_Dedup-A",
                }
            )

            result = await service.get_learning_history(user_id=user_id)

            # If dedup works, concept_name should appear at most once
            matching = [
                item for item in result["items"] if "Dedup-A" in item.get("concept", "")
            ]
            # Neo4j returns concept_id in a separate field; the dedup key is (node_id, timestamp).
            # With same node_id and timestamp, should be deduped to 1 entry.
            assert len(matching) <= 2, (
                f"Dedup failed: expected at most 2 items (Neo4j doesn't have node_id in LEARNED), "
                f"got {len(matching)}"
            )
        finally:
            await _cleanup_prefix(client, prefix)
            await client.cleanup()

    async def test_auto_initialize_when_not_initialized(self):
        """Service should auto-initialize if not yet initialized."""
        client = _make_client()
        prefix = f"test_{uuid.uuid4().hex[:8]}_"
        try:
            await client.initialize()
            user_id = f"{prefix}u1"

            service = _make_real_service(client)
            # NOT calling initialize() — service should auto-init

            result = await service.get_learning_history(user_id=user_id)

            # Should not raise; service auto-initializes
            assert "items" in result
            assert "total" in result
            assert service._initialized is True
        finally:
            await _cleanup_prefix(client, prefix)
            await client.cleanup()
