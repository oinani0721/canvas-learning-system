"""
S33 Tier 2: Real Neo4j integration tests for MasteryStore.

Tests CRUD operations on EntityNode mastery properties against a live
Neo4j test container (port 7692). Each test creates its own client
and uses UUID-prefixed group_ids for isolation.

[Source: S33 Phase1 Tier2 — MasteryStore migration]
"""

import os
import uuid

import pytest

from app.clients.neo4j_client import Neo4jClient
from app.models.mastery_state import ConceptState
from app.services.mastery_store import MasteryStore

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


async def _cleanup_group(client: Neo4jClient, group_id: str) -> None:
    """Remove all EntityNodes in the given group."""
    try:
        await client.run_query(
            "MATCH (n:EntityNode {group_id: $gid}) DETACH DELETE n",
            gid=group_id,
        )
    except Exception:
        pass


# ============================================================================
# Read Operations
# ============================================================================


class TestRealGetConcept:
    """get_concept against real Neo4j — proves Cypher MATCH and property mapping."""

    async def test_found(self):
        client = _make_client()
        gid = f"test_{uuid.uuid4().hex[:8]}"
        try:
            await client.initialize()
            store = MasteryStore(client)

            # Seed a concept via save_concept
            concept = ConceptState(concept_id="c1", topic="Graphs", name="BFS", p_mastery=0.65)
            await store.save_concept(concept, group_id=gid)

            # Read it back
            result = await store.get_concept("c1", group_id=gid)

            assert result is not None, "Saved concept should be retrievable"
            assert result.concept_id == "c1"
            assert result.name == "BFS"
            assert result.topic == "Graphs"
            assert abs(result.p_mastery - 0.65) < 0.01
        finally:
            await _cleanup_group(client, gid)
            await client.cleanup()

    async def test_not_found(self):
        client = _make_client()
        gid = f"test_{uuid.uuid4().hex[:8]}"
        try:
            await client.initialize()
            store = MasteryStore(client)

            result = await store.get_concept("nonexistent", group_id=gid)
            assert result is None
        finally:
            await _cleanup_group(client, gid)
            await client.cleanup()


class TestRealSaveConcept:
    """save_concept MERGE upsert — proves data persists and updates."""

    async def test_save_and_read_round_trip(self):
        client = _make_client()
        gid = f"test_{uuid.uuid4().hex[:8]}"
        try:
            await client.initialize()
            store = MasteryStore(client)

            concept = ConceptState(
                concept_id="save_test", topic="Search", name="DFS",
                p_mastery=0.42, bkt_difficulty="hard",
            )
            await store.save_concept(concept, group_id=gid)

            result = await store.get_concept("save_test", group_id=gid)

            assert result is not None
            assert result.name == "DFS"
            assert result.bkt_difficulty == "hard"
            assert abs(result.p_mastery - 0.42) < 0.01
        finally:
            await _cleanup_group(client, gid)
            await client.cleanup()

    async def test_save_upsert_updates_existing(self):
        """MERGE should update existing concept, not create duplicate."""
        client = _make_client()
        gid = f"test_{uuid.uuid4().hex[:8]}"
        try:
            await client.initialize()
            store = MasteryStore(client)

            # Save initial version
            v1 = ConceptState(concept_id="upsert_c", topic="T", name="A", p_mastery=0.3)
            await store.save_concept(v1, group_id=gid)

            # Save updated version
            v2 = ConceptState(concept_id="upsert_c", topic="T", name="A", p_mastery=0.8)
            await store.save_concept(v2, group_id=gid)

            # Only one concept should exist, with updated p_mastery
            result = await store.get_concept("upsert_c", group_id=gid)
            assert result is not None
            assert abs(result.p_mastery - 0.8) < 0.01

            # Verify no duplicates
            all_concepts = await store.get_all_concepts(group_id=gid)
            matching = [c for c in all_concepts if c.concept_id == "upsert_c"]
            assert len(matching) == 1, f"Expected 1, got {len(matching)} duplicates"
        finally:
            await _cleanup_group(client, gid)
            await client.cleanup()


class TestRealGetAllConcepts:
    """get_all_concepts — proves list query and ordering."""

    async def test_returns_multiple(self):
        client = _make_client()
        gid = f"test_{uuid.uuid4().hex[:8]}"
        try:
            await client.initialize()
            store = MasteryStore(client)

            for name, p in [("BFS", 0.3), ("DFS", 0.7), ("A*", 0.5)]:
                c = ConceptState(concept_id=name.lower(), topic="Search", name=name, p_mastery=p)
                await store.save_concept(c, group_id=gid)

            results = await store.get_all_concepts(group_id=gid)
            assert len(results) == 3
            names = {r.name for r in results}
            assert names == {"BFS", "DFS", "A*"}
        finally:
            await _cleanup_group(client, gid)
            await client.cleanup()

    async def test_empty_group(self):
        client = _make_client()
        gid = f"test_{uuid.uuid4().hex[:8]}"
        try:
            await client.initialize()
            store = MasteryStore(client)

            results = await store.get_all_concepts(group_id=gid)
            assert len(results) == 0
        finally:
            await client.cleanup()


# ============================================================================
# get_or_create
# ============================================================================


class TestRealGetOrCreateConcept:
    """get_or_create_concept — BKT initialization logic."""

    async def test_creates_new_with_bkt_defaults(self):
        """New concept gets p_mastery from BKT P_L0 for its difficulty."""
        from app.models.mastery_state import DEFAULT_BKT_PARAMS

        client = _make_client()
        gid = f"test_{uuid.uuid4().hex[:8]}"
        try:
            await client.initialize()
            store = MasteryStore(client)

            # Medium difficulty (default) → P_L0 = 0.1
            result = await store.get_or_create_concept(
                "new_medium", topic="Algebra", name="Quadratic", group_id=gid,
            )
            assert result.concept_id == "new_medium"
            assert abs(result.p_mastery - DEFAULT_BKT_PARAMS["medium"]["P_L0"]) < 0.01

            # Hard difficulty → P_L0 = 0.05
            result_hard = await store.get_or_create_concept(
                "new_hard", topic="Analysis", name="Limits", group_id=gid,
                bkt_difficulty="hard",
            )
            assert abs(result_hard.p_mastery - DEFAULT_BKT_PARAMS["hard"]["P_L0"]) < 0.01

            # Verify both persisted in DB
            all_c = await store.get_all_concepts(group_id=gid)
            assert len(all_c) == 2
        finally:
            await _cleanup_group(client, gid)
            await client.cleanup()

    async def test_returns_existing_unchanged(self):
        """Existing concept is returned as-is — p_mastery not overwritten."""
        client = _make_client()
        gid = f"test_{uuid.uuid4().hex[:8]}"
        try:
            await client.initialize()
            store = MasteryStore(client)

            # Pre-save a concept with high p_mastery
            pre = ConceptState(
                concept_id="existing_c", topic="Graph", name="BFS", p_mastery=0.9,
            )
            await store.save_concept(pre, group_id=gid)

            # get_or_create should return the existing, not overwrite to P_L0
            result = await store.get_or_create_concept(
                "existing_c", topic="Graph", name="BFS", group_id=gid,
            )
            assert abs(result.p_mastery - 0.9) < 0.01, (
                f"Existing p_mastery should be preserved, got {result.p_mastery}"
            )
        finally:
            await _cleanup_group(client, gid)
            await client.cleanup()


# ============================================================================
# Event Recording
# ============================================================================


class TestRealRecordEvents:
    """record_*_event — proves event properties persisted to EntityNode."""

    async def test_record_interaction_sets_grade(self):
        client = _make_client()
        gid = f"test_{uuid.uuid4().hex[:8]}"
        try:
            await client.initialize()
            store = MasteryStore(client)

            # Must create the concept first (MATCH requires existing node)
            c = ConceptState(concept_id="interact_c", topic="T", name="N", p_mastery=0.5)
            await store.save_concept(c, group_id=gid)

            await store.record_interaction_event("interact_c", grade=3, group_id=gid)

            # Verify grade was set on the EntityNode
            records = await client.run_query(
                "MATCH (n:EntityNode {group_id: $gid, mastery_concept_id: $cid}) "
                "RETURN n.last_grade AS grade, n.grade_source AS source",
                gid=gid, cid="interact_c",
            )
            assert len(records) >= 1
            assert records[0]["grade"] == 3
            assert records[0]["source"] == "interaction"
        finally:
            await _cleanup_group(client, gid)
            await client.cleanup()

    async def test_record_override_sets_level(self):
        client = _make_client()
        gid = f"test_{uuid.uuid4().hex[:8]}"
        try:
            await client.initialize()
            store = MasteryStore(client)

            c = ConceptState(concept_id="override_c", topic="T", name="N", p_mastery=0.5)
            await store.save_concept(c, group_id=gid)

            await store.record_override_event(
                "override_c", level="proficient", reason="manual review", group_id=gid,
            )

            records = await client.run_query(
                "MATCH (n:EntityNode {group_id: $gid, mastery_concept_id: $cid}) "
                "RETURN n.last_override_level AS level, n.last_override_reason AS reason",
                gid=gid, cid="override_c",
            )
            assert len(records) >= 1
            assert records[0]["level"] == "proficient"
            assert records[0]["reason"] == "manual review"
        finally:
            await _cleanup_group(client, gid)
            await client.cleanup()

    async def test_record_self_assess_sets_color(self):
        client = _make_client()
        gid = f"test_{uuid.uuid4().hex[:8]}"
        try:
            await client.initialize()
            store = MasteryStore(client)

            c = ConceptState(concept_id="assess_c", topic="T", name="N", p_mastery=0.5)
            await store.save_concept(c, group_id=gid)

            await store.record_self_assess_event("assess_c", color="3", group_id=gid)

            records = await client.run_query(
                "MATCH (n:EntityNode {group_id: $gid, mastery_concept_id: $cid}) "
                "RETURN n.last_self_assess_color AS color",
                gid=gid, cid="assess_c",
            )
            assert len(records) >= 1
            assert records[0]["color"] == "3"
        finally:
            await _cleanup_group(client, gid)
            await client.cleanup()


# ============================================================================
# Search and Isolation
# ============================================================================


class TestRealFindByName:
    """find_concept_by_name — fuzzy search with toLower CONTAINS."""

    async def test_finds_by_partial_name(self):
        client = _make_client()
        gid = f"test_{uuid.uuid4().hex[:8]}"
        try:
            await client.initialize()
            store = MasteryStore(client)

            c = ConceptState(
                concept_id="bfs_concept", topic="Search", name="Breadth-First Search",
                p_mastery=0.6,
            )
            await store.save_concept(c, group_id=gid)

            result = await store.find_concept_by_name("breadth", group_id=gid)

            assert result is not None
            assert "Breadth" in result.name
        finally:
            await _cleanup_group(client, gid)
            await client.cleanup()

    async def test_not_found_returns_none(self):
        client = _make_client()
        gid = f"test_{uuid.uuid4().hex[:8]}"
        try:
            await client.initialize()
            store = MasteryStore(client)

            result = await store.find_concept_by_name("nonexistent_xyz", group_id=gid)
            assert result is None
        finally:
            await client.cleanup()


class TestRealGroupIdIsolation:
    """group_id isolation — data in one group invisible to another."""

    async def test_different_groups_isolated(self):
        client = _make_client()
        gid_a = f"test_{uuid.uuid4().hex[:8]}_A"
        gid_b = f"test_{uuid.uuid4().hex[:8]}_B"
        try:
            await client.initialize()
            store = MasteryStore(client)

            # Save concept in group A only
            c = ConceptState(concept_id="isolated_c", topic="T", name="N", p_mastery=0.5)
            await store.save_concept(c, group_id=gid_a)

            # Should be found in A
            in_a = await store.get_concept("isolated_c", group_id=gid_a)
            assert in_a is not None

            # Should NOT be found in B
            in_b = await store.get_concept("isolated_c", group_id=gid_b)
            assert in_b is None, "Concept saved in group A should not appear in group B"
        finally:
            await _cleanup_group(client, gid_a)
            await _cleanup_group(client, gid_b)
            await client.cleanup()
