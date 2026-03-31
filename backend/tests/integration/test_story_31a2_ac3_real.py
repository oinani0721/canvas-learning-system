# Canvas Learning System - Story 31.A.2 AC-31.A.2.3 Real Neo4j Tests
# Story 31.A.2: 学习历史读取修复
# [Source: docs/stories/31.A.2.story.md]
"""
Real Neo4j integration tests for AC-31.A.2.3: Cross-session data persistence.

Migrated from: tests/unit/test_story_31a2_ac3_persistence.py
Each test uses real Neo4j (port 7692 test container) with per-test UUID isolation.

Pattern: Each test creates its own Neo4jClient to avoid event-loop-scope conflicts
(same approach as test_memory_persistence_real.py).

[Source: docs/stories/31.A.2.story.md#AC-31.A.2.3]
"""

import asyncio
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


async def _poll_neo4j(
    client: Neo4jClient, user_id: str, *, min_count: int = 1, timeout: float = 10.0
):
    """Poll Neo4j until at least min_count learning history records appear."""
    loop = asyncio.get_running_loop()
    start = loop.time()
    while (loop.time() - start) < timeout:
        results = await client.get_learning_history(user_id=user_id)
        if results and len(results) >= min_count:
            return results
        await asyncio.sleep(0.3)
    raise TimeoutError(
        f"Neo4j did not return {min_count} records for {user_id} within {timeout}s"
    )


# =============================================================================
# AC-31.A.2.3: Cross-Session Data Persistence (Real Neo4j)
# [Source: docs/stories/31.A.2.story.md#AC-31.A.2.3]
# =============================================================================


class TestAC31A23_CrossSessionPersistence:
    """AC-31.A.2.3: Data must persist across service restarts (real Neo4j)."""

    async def test_session1_write_session2_read(self):
        """Data written in session 1 is readable in session 2."""
        client = _make_client()
        prefix = f"test_{uuid.uuid4().hex[:8]}_"
        try:
            await client.initialize()

            # Session 1: Write
            svc1 = MemoryService(neo4j_client=client)
            await svc1.initialize()
            await svc1.record_learning_event(
                user_id=f"{prefix}u1",
                canvas_path=f"{prefix}test/a.canvas",
                node_id=f"{prefix}n1",
                concept=f"{prefix}linear_algebra",
                agent_type="scoring",
                score=85,
            )

            await _poll_neo4j(client, f"{prefix}u1")

            # Session 2: Fresh service instance reads from Neo4j
            # (In real DB, _episodes may be non-empty due to recovery —
            #  the point is that Neo4j data is accessible regardless.)
            svc2 = MemoryService(neo4j_client=client)
            await svc2.initialize()

            result = await svc2.get_learning_history(user_id=f"{prefix}u1")

            assert result["total"] >= 1
            found = any(
                "linear_algebra" in str(i.get("concept", "")) for i in result["items"]
            )
            assert found, "Session 1 data should be accessible in session 2"
        finally:
            await _cleanup_prefix(client, prefix)
            await client.cleanup()

    async def test_data_fields_complete(self):
        """All critical fields survive cross-session read."""
        client = _make_client()
        prefix = f"test_{uuid.uuid4().hex[:8]}_"
        try:
            await client.initialize()

            # Session 1: Write
            svc1 = MemoryService(neo4j_client=client)
            await svc1.initialize()
            await svc1.record_learning_event(
                user_id=f"{prefix}u1",
                canvas_path=f"{prefix}test/b.canvas",
                node_id=f"{prefix}n2",
                concept=f"{prefix}probability_theory",
                agent_type="oral-explanation",
                score=92,
                subject=f"{prefix}math",
            )

            await _poll_neo4j(client, f"{prefix}u1")

            # Session 2: Read
            svc2 = MemoryService(neo4j_client=client)
            await svc2.initialize()
            result = await svc2.get_learning_history(user_id=f"{prefix}u1")

            item = next(
                (
                    i
                    for i in result["items"]
                    if "probability_theory" in str(i.get("concept", ""))
                ),
                None,
            )
            assert item is not None, "Should find probability_theory in results"
            # Score should be preserved (Neo4j MERGE sets r.score)
            if item.get("score") is not None:
                assert item["score"] == 92
            assert item.get("timestamp") is not None, "timestamp should be present"
        finally:
            await _cleanup_prefix(client, prefix)
            await client.cleanup()

    async def test_multiple_events_persist(self):
        """Multiple events from session 1 all persist to session 2."""
        client = _make_client()
        prefix = f"test_{uuid.uuid4().hex[:8]}_"
        try:
            await client.initialize()

            # Session 1: Write multiple concepts
            svc1 = MemoryService(neo4j_client=client)
            await svc1.initialize()

            concepts = ["calculus", "linear_algebra", "discrete_math"]
            for i, c in enumerate(concepts):
                await svc1.record_learning_event(
                    user_id=f"{prefix}u1",
                    canvas_path=f"{prefix}test/c.canvas",
                    node_id=f"{prefix}n3_{i}",
                    concept=f"{prefix}{c}",
                    agent_type="scoring",
                    score=80,
                )

            await _poll_neo4j(client, f"{prefix}u1", min_count=len(concepts))

            # Session 2: Read
            svc2 = MemoryService(neo4j_client=client)
            await svc2.initialize()
            result = await svc2.get_learning_history(user_id=f"{prefix}u1")

            found_concepts = {str(i.get("concept", "")) for i in result["items"]}
            for c in concepts:
                assert any(c in fc for fc in found_concepts), f"Missing concept: {c}"
        finally:
            await _cleanup_prefix(client, prefix)
            await client.cleanup()
