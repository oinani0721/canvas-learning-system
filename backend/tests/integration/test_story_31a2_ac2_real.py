# Canvas Learning System - Story 31.A.2 AC-31.A.2.2 Real Neo4j Integration Tests
# Migrated from: tests/unit/test_story_31a2_ac2_client_method.py
# [Source: docs/stories/31.A.2.story.md]
"""
Real-DB integration tests for AC-31.A.2.2: Neo4jClient.get_learning_history() method.

Each test creates its OWN Neo4jClient to avoid event-loop-scope conflicts
with shared conftest fixtures.

Requires: docker compose --profile test up -d neo4j-test  (port 7692)

Run with:
    cd backend && pytest tests/integration/test_story_31a2_ac2_real.py -m integration -v
"""

import inspect
import os
import uuid
from datetime import datetime

import pytest

from app.clients.neo4j_client import Neo4jClient


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

async def _insert_user_concept_relationship(
    neo4j_client, prefix, user_id, concept_name, score, timestamp,
    group_id="test", concept_id=None, agent_type="scoring", review_count=1,
):
    """Insert a User -> LEARNED -> Concept relationship into Neo4j.

    Matches the Cypher schema that Neo4jClient.get_learning_history() queries:
    (u:User {id})-[r:LEARNED {score, timestamp, group_id, agent_type, review_count}]->(c:Concept {name, id})
    """
    cid = concept_id or f"{prefix}cid_{concept_name}"
    await neo4j_client.run_query(
        """
        MERGE (u:User {id: $uid})
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
        concept=concept_name,
        cid=cid,
        score=score,
        ts=timestamp,
        gid=group_id,
        agent_type=agent_type,
        review_count=review_count,
    )


# =============================================================================
# AC-31.A.2.2: Neo4jClient.get_learning_history() Method — Real DB
# [Source: docs/stories/31.A.2.story.md#AC-31.A.2.2]
# =============================================================================

class TestAC31A22_Neo4jClientMethod_Real:
    """AC-31.A.2.2: Neo4jClient must have get_learning_history() (real DB)."""

    async def test_method_exists(self):
        """get_learning_history must exist on Neo4jClient."""
        assert hasattr(Neo4jClient, "get_learning_history")
        assert callable(getattr(Neo4jClient, "get_learning_history"))

    async def test_method_signature_params(self):
        """Method must support required parameters."""
        sig = inspect.signature(Neo4jClient.get_learning_history)
        param_names = list(sig.parameters.keys())

        assert "self" in param_names
        assert "user_id" in param_names
        assert "start_date" in param_names
        assert "end_date" in param_names
        assert "concept" in param_names
        assert "group_id" in param_names
        assert "limit" in param_names

    async def test_filters_by_user_id(self):
        """Real Neo4j filters results by user_id."""
        client = _make_client()
        prefix = f"test_{uuid.uuid4().hex[:8]}_"
        try:
            await client.initialize()
            user1 = f"{prefix}u1"
            user2 = f"{prefix}u2"

            await _insert_user_concept_relationship(
                client, prefix, user1, f"{prefix}ConceptA", 90, "2026-02-05T10:00:00",
            )
            await _insert_user_concept_relationship(
                client, prefix, user2, f"{prefix}ConceptB", 80, "2026-02-05T10:00:00",
            )

            results = await client.get_learning_history(user_id=user1)

            assert len(results) >= 1
            user_ids = [r.get("user_id") for r in results]
            assert all(uid == user1 for uid in user_ids), (
                f"Expected only user {user1}, got user_ids: {user_ids}"
            )
        finally:
            await _cleanup_prefix(client, prefix)
            await client.cleanup()

    async def test_filters_by_concept(self):
        """Real Neo4j filters by concept (partial match via CONTAINS)."""
        client = _make_client()
        prefix = f"test_{uuid.uuid4().hex[:8]}_"
        try:
            await client.initialize()
            user_id = f"{prefix}u1"

            await _insert_user_concept_relationship(
                client, prefix, user_id, f"{prefix}线性代数-矩阵乘法",
                90, "2026-02-05T10:00:00",
            )
            await _insert_user_concept_relationship(
                client, prefix, user_id, f"{prefix}概率论-贝叶斯",
                80, "2026-02-05T10:00:00",
            )

            results = await client.get_learning_history(
                user_id=user_id, concept="矩阵"
            )

            assert len(results) >= 1
            for r in results:
                assert "矩阵" in r["concept"], f"Unexpected concept: {r['concept']}"
        finally:
            await _cleanup_prefix(client, prefix)
            await client.cleanup()

    async def test_filters_by_group_id(self):
        """Real Neo4j filters by group_id."""
        client = _make_client()
        prefix = f"test_{uuid.uuid4().hex[:8]}_"
        try:
            await client.initialize()
            user_id = f"{prefix}u1"

            await _insert_user_concept_relationship(
                client, prefix, user_id, f"{prefix}MathConcept",
                90, "2026-02-05T10:00:00", group_id=f"{prefix}math-001",
            )
            await _insert_user_concept_relationship(
                client, prefix, user_id, f"{prefix}PhysConcept",
                80, "2026-02-05T10:00:00", group_id=f"{prefix}physics-001",
            )

            results = await client.get_learning_history(
                user_id=user_id, group_id=f"{prefix}math-001"
            )

            assert len(results) >= 1
            for r in results:
                assert r["group_id"] == f"{prefix}math-001", (
                    f"Expected group_id {prefix}math-001, got {r['group_id']}"
                )
        finally:
            await _cleanup_prefix(client, prefix)
            await client.cleanup()

    async def test_filters_by_date_range(self):
        """Real Neo4j filters by start_date and end_date."""
        client = _make_client()
        prefix = f"test_{uuid.uuid4().hex[:8]}_"
        try:
            await client.initialize()
            user_id = f"{prefix}u1"

            await _insert_user_concept_relationship(
                client, prefix, user_id, f"{prefix}Old",
                70, "2026-01-01T10:00:00",
            )
            await _insert_user_concept_relationship(
                client, prefix, user_id, f"{prefix}Current",
                85, "2026-02-05T10:00:00",
            )
            await _insert_user_concept_relationship(
                client, prefix, user_id, f"{prefix}Future",
                95, "2026-03-01T10:00:00",
            )

            results = await client.get_learning_history(
                user_id=user_id,
                start_date=datetime(2026, 2, 1),
                end_date=datetime(2026, 2, 28),
            )

            assert len(results) >= 1
            concepts = [r["concept"] for r in results]
            assert any("Current" in c for c in concepts), (
                f"Expected 'Current' in results, got: {concepts}"
            )
            # Old and Future should NOT appear
            assert not any("Old" in c for c in concepts), (
                f"Old record should be filtered out, got: {concepts}"
            )
            assert not any("Future" in c for c in concepts), (
                f"Future record should be filtered out, got: {concepts}"
            )
        finally:
            await _cleanup_prefix(client, prefix)
            await client.cleanup()

    async def test_limits_results(self):
        """Real Neo4j respects limit parameter."""
        client = _make_client()
        prefix = f"test_{uuid.uuid4().hex[:8]}_"
        try:
            await client.initialize()
            user_id = f"{prefix}u1"

            # Insert 10 concepts
            for i in range(10):
                await _insert_user_concept_relationship(
                    client, prefix, user_id, f"{prefix}LimitC{i}",
                    80, f"2026-02-05T{10+i}:00:00",
                )

            results = await client.get_learning_history(user_id=user_id, limit=3)

            assert len(results) == 3, f"Expected 3 results with limit=3, got {len(results)}"
        finally:
            await _cleanup_prefix(client, prefix)
            await client.cleanup()

    async def test_sorts_newest_first(self):
        """Real Neo4j returns results sorted by timestamp DESC."""
        client = _make_client()
        prefix = f"test_{uuid.uuid4().hex[:8]}_"
        try:
            await client.initialize()
            user_id = f"{prefix}u1"

            await _insert_user_concept_relationship(
                client, prefix, user_id, f"{prefix}Oldest",
                70, "2026-02-01T10:00:00",
            )
            await _insert_user_concept_relationship(
                client, prefix, user_id, f"{prefix}Newest",
                90, "2026-02-05T10:00:00",
            )
            await _insert_user_concept_relationship(
                client, prefix, user_id, f"{prefix}Middle",
                80, "2026-02-03T10:00:00",
            )

            results = await client.get_learning_history(user_id=user_id)

            assert len(results) >= 3
            assert results[0]["concept"] == f"{prefix}Newest", (
                f"First result should be Newest, got: {results[0]['concept']}"
            )
            assert results[-1]["concept"] == f"{prefix}Oldest", (
                f"Last result should be Oldest, got: {results[-1]['concept']}"
            )
        finally:
            await _cleanup_prefix(client, prefix)
            await client.cleanup()

    async def test_returns_correct_fields(self):
        """Real Neo4j returns all expected fields."""
        client = _make_client()
        prefix = f"test_{uuid.uuid4().hex[:8]}_"
        try:
            await client.initialize()
            user_id = f"{prefix}u1"

            await _insert_user_concept_relationship(
                client, prefix, user_id, f"{prefix}FieldTest",
                90, "2026-02-05T10:00:00",
                group_id=f"{prefix}math-001",
                concept_id=f"{prefix}c-field-1",
                agent_type="scoring",
                review_count=3,
            )

            results = await client.get_learning_history(user_id=user_id)

            assert len(results) >= 1
            item = results[0]
            assert item["user_id"] == user_id
            assert item["concept"] == f"{prefix}FieldTest"
            assert item["concept_id"] == f"{prefix}c-field-1"
            assert item["score"] == 90
            assert "2026-02-05" in str(item["timestamp"])
            assert item["group_id"] == f"{prefix}math-001"
            assert item["review_count"] == 3
        finally:
            await _cleanup_prefix(client, prefix)
            await client.cleanup()

    async def test_neo4j_mode_runs_cypher_query(self):
        """In Neo4j mode, get_learning_history executes a real Cypher query
        and returns results from the database."""
        client = _make_client()
        prefix = f"test_{uuid.uuid4().hex[:8]}_"
        try:
            await client.initialize()
            user_id = f"{prefix}u1"

            # Insert data and verify it comes back through get_learning_history
            await _insert_user_concept_relationship(
                client, prefix, user_id, f"{prefix}CypherTest",
                85, "2026-02-05T10:00:00",
            )

            results = await client.get_learning_history(user_id=user_id)

            assert len(results) >= 1
            concepts = [r["concept"] for r in results]
            assert f"{prefix}CypherTest" in concepts, (
                f"Cypher query should return inserted data, got: {concepts}"
            )
        finally:
            await _cleanup_prefix(client, prefix)
            await client.cleanup()

    async def test_empty_result_for_nonexistent_user(self):
        """Query for a non-existent user returns empty list."""
        client = _make_client()
        prefix = f"test_{uuid.uuid4().hex[:8]}_"
        try:
            await client.initialize()

            results = await client.get_learning_history(
                user_id=f"{prefix}nonexistent_user_xyz"
            )

            assert results == [], f"Expected empty list for nonexistent user, got: {results}"
        finally:
            await _cleanup_prefix(client, prefix)
            await client.cleanup()
