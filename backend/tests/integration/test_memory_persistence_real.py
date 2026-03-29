"""
S33 Migration: Real Neo4j integration tests for MemoryService persistence.

Each test creates its own Neo4jClient to avoid event-loop-scope conflicts.
Proves that dict-simulated persistence tests hide real bugs.

[Source: S33 Phase1 — Real-Neo4j migration]
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


# ============================================================================
# Cross-Session Persistence
# ============================================================================


class TestRealCrossSessionPersistence:
    """Data recorded by one MemoryService is visible to a fresh instance."""

    @pytest.mark.xfail(
        reason="BUG: Neo4j returns DateTime objects but MemoryService._recover_episodes_from_neo4j "
        "compares them with ISO strings. S33 exposed: '<' not supported between DateTime and str.",
        strict=True,
    )
    async def test_history_persists_across_service_instances(self):
        """A fresh MemoryService reads history written by a prior instance."""
        client = _make_client()
        prefix = f"test_{uuid.uuid4().hex[:8]}_"
        try:
            await client.initialize()

            # Service 1: record an event
            service1 = MemoryService(neo4j_client=client)
            await service1.initialize()

            user_id = f"{prefix}user"
            await service1.record_learning_event(
                user_id=user_id,
                canvas_path=f"{prefix}test.canvas",
                node_id=f"{prefix}node1",
                concept=f"{prefix}linear_algebra",
                agent_type="default",
                score=85,
            )

            await _poll_neo4j(client, user_id)

            # Service 2: fresh instance, empty _episodes
            service2 = MemoryService(neo4j_client=client)
            await service2.initialize()

            result = await service2.get_learning_history(user_id=user_id)

            assert result["items"], "Fresh service should see persisted history"
            concepts = [item.get("concept", "") for item in result["items"]]
            assert any("linear_algebra" in c for c in concepts), (
                f"Expected 'linear_algebra' in concepts, got: {concepts}"
            )
        finally:
            await _cleanup_prefix(client, prefix)
            await client.cleanup()

    @pytest.mark.xfail(
        reason="BUG: Neo4j DateTime vs str comparison in MemoryService (same as above).",
        strict=True,
    )
    async def test_all_fields_complete_after_restart(self):
        """All recorded fields survive a service restart via Neo4j."""
        client = _make_client()
        prefix = f"test_{uuid.uuid4().hex[:8]}_"
        try:
            await client.initialize()

            service1 = MemoryService(neo4j_client=client)
            await service1.initialize()

            user_id = f"{prefix}user_fields"
            concept_name = f"{prefix}calculus_basics"
            await service1.record_learning_event(
                user_id=user_id,
                canvas_path=f"{prefix}math/calculus.canvas",
                node_id=f"{prefix}node_calc",
                concept=concept_name,
                agent_type="explain",
                score=92,
            )

            await _poll_neo4j(client, user_id)

            service2 = MemoryService(neo4j_client=client)
            await service2.initialize()

            result = await service2.get_learning_history(user_id=user_id)

            assert result["items"], "Should have items after restart"
            item = result["items"][0]
            assert item.get("concept"), "concept should be non-empty"
            assert "calculus_basics" in item["concept"]
            if "score" in item and item["score"] is not None:
                assert item["score"] == 92
        finally:
            await _cleanup_prefix(client, prefix)
            await client.cleanup()


# ============================================================================
# Query Behavior — Data Comes From Neo4j
# ============================================================================


class TestRealQueryBehavior:
    """Prove query results originate from Neo4j, not in-memory cache."""

    @pytest.mark.xfail(
        reason="BUG: Neo4j DateTime vs str comparison in MemoryService.",
        strict=True,
    )
    async def test_returned_from_neo4j(self):
        """A fresh service with empty _episodes still returns data from Neo4j."""
        client = _make_client()
        prefix = f"test_{uuid.uuid4().hex[:8]}_"
        try:
            await client.initialize()

            service1 = MemoryService(neo4j_client=client)
            await service1.initialize()

            user_id = f"{prefix}user_query"
            await service1.record_learning_event(
                user_id=user_id,
                canvas_path=f"{prefix}math/prob.canvas",
                node_id=f"{prefix}node_prob",
                concept=f"{prefix}probability_theory",
                agent_type="default",
                score=78,
            )

            await _poll_neo4j(client, user_id)

            # Fresh service — _episodes is empty, data must come from Neo4j
            service2 = MemoryService(neo4j_client=client)
            await service2.initialize()

            result = await service2.get_learning_history(user_id=user_id)

            assert result["items"], "Fresh service should retrieve from Neo4j"
            concepts = [item.get("concept", "") for item in result["items"]]
            assert any("probability_theory" in c for c in concepts)
        finally:
            await _cleanup_prefix(client, prefix)
            await client.cleanup()


# ============================================================================
# Filtering and Pagination
# ============================================================================


class TestRealFilteringAndPagination:
    """Test Cypher-level filtering and pagination against real Neo4j."""

    @pytest.mark.xfail(
        reason="BUG: Neo4j DateTime vs str comparison in MemoryService.",
        strict=True,
    )
    async def test_concept_filter_cypher(self):
        """Concept partial-match filter works at the Cypher level."""
        client = _make_client()
        prefix = f"test_{uuid.uuid4().hex[:8]}_"
        try:
            await client.initialize()

            service1 = MemoryService(neo4j_client=client)
            await service1.initialize()

            user_id = f"{prefix}user_filter"

            await service1.record_learning_event(
                user_id=user_id,
                canvas_path=f"{prefix}test.canvas",
                node_id=f"{prefix}node_mat",
                concept=f"{prefix}matrix_multiplication",
                agent_type="default",
                score=80,
            )
            await service1.record_learning_event(
                user_id=user_id,
                canvas_path=f"{prefix}test.canvas",
                node_id=f"{prefix}node_qm",
                concept=f"{prefix}quantum_mechanics",
                agent_type="default",
                score=90,
            )

            await _poll_neo4j(client, user_id, min_count=2)

            service2 = MemoryService(neo4j_client=client)
            await service2.initialize()

            result = await service2.get_learning_history(
                user_id=user_id,
                concept=f"{prefix}matrix",
            )

            items = result["items"]
            concepts = [item.get("concept", "") for item in items]

            assert any("matrix_multiplication" in c for c in concepts), (
                f"Expected 'matrix_multiplication' in filtered results, got: {concepts}"
            )
            assert not any("quantum_mechanics" in c for c in concepts), (
                f"'quantum_mechanics' should NOT appear, got: {concepts}"
            )
        finally:
            await _cleanup_prefix(client, prefix)
            await client.cleanup()

    async def test_subject_filter_group_id(self):
        """group_id filter isolates records by discipline."""
        client = _make_client()
        prefix = f"test_{uuid.uuid4().hex[:8]}_"
        try:
            await client.initialize()

            service1 = MemoryService(neo4j_client=client)
            await service1.initialize()

            user_id = f"{prefix}user_subject"

            await service1.record_learning_event(
                user_id=user_id,
                canvas_path=f"{prefix}math/test.canvas",
                node_id=f"{prefix}node_calc",
                concept=f"{prefix}calculus",
                agent_type="default",
                score=85,
                subject=f"{prefix}math",
            )
            await service1.record_learning_event(
                user_id=user_id,
                canvas_path=f"{prefix}physics/test.canvas",
                node_id=f"{prefix}node_newton",
                concept=f"{prefix}newtonian_mechanics",
                agent_type="default",
                score=70,
                subject=f"{prefix}physics",
            )

            await _poll_neo4j(client, user_id, min_count=2)

            service2 = MemoryService(neo4j_client=client)
            await service2.initialize()

            result = await service2.get_learning_history(
                user_id=user_id,
                subject=f"{prefix}math",
            )

            items = result["items"]
            concepts = [item.get("concept", "") for item in items]

            assert any("calculus" in c for c in concepts), (
                f"Expected 'calculus' in math-filtered results, got: {concepts}"
            )
            assert not any("newtonian_mechanics" in c for c in concepts), (
                f"'newtonian_mechanics' should NOT appear, got: {concepts}"
            )
        finally:
            await _cleanup_prefix(client, prefix)
            await client.cleanup()

    @pytest.mark.xfail(
        reason="BUG: Neo4j DateTime vs str comparison in MemoryService.",
        strict=True,
    )
    async def test_pagination_limit_skip(self):
        """Pagination correctly limits and offsets results."""
        client = _make_client()
        prefix = f"test_{uuid.uuid4().hex[:8]}_"
        try:
            await client.initialize()

            service1 = MemoryService(neo4j_client=client)
            await service1.initialize()

            user_id = f"{prefix}user_page"

            for i in range(1, 6):
                await service1.record_learning_event(
                    user_id=user_id,
                    canvas_path=f"{prefix}test.canvas",
                    node_id=f"{prefix}node_pg_{i}",
                    concept=f"{prefix}concept_{i}",
                    agent_type="default",
                    score=50 + i * 10,
                )

            await _poll_neo4j(client, user_id, min_count=5, timeout=15.0)

            service2 = MemoryService(neo4j_client=client)
            await service2.initialize()

            page1 = await service2.get_learning_history(
                user_id=user_id, page=1, page_size=2,
            )
            assert len(page1["items"]) <= 2
            assert page1["page"] == 1

            page2 = await service2.get_learning_history(
                user_id=user_id, page=2, page_size=2,
            )
            assert len(page2["items"]) <= 2
            assert page2["page"] == 2

            page1_concepts = {item.get("concept", "") for item in page1["items"]}
            page2_concepts = {item.get("concept", "") for item in page2["items"]}
            assert page1_concepts.isdisjoint(page2_concepts), (
                f"Pages overlap: p1={page1_concepts}, p2={page2_concepts}"
            )
        finally:
            await _cleanup_prefix(client, prefix)
            await client.cleanup()
