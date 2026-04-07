"""FR-KG-04 isolation Phase 1 — group_id isolation integration tests.

Verifies that ``learning_context_service.get_node_context()`` respects the
``group_id`` namespace when querying 1-hop neighbors from Neo4j. Prior to
the Phase 1 fix, ``_fetch_neighbor_records`` emitted a Cypher query with
no group filter, so a concept named ``贝叶斯定理`` in group ``physics``
would pull in neighbors from group ``math`` when they shared the same
node name.

Requires the dedicated test Neo4j container on port 7692 (see
``backend/scripts/run-integration.sh``).

Uses function-scoped client creation to side-step the
Python 3.14 / pytest-asyncio 1.3 event-loop-scope mismatch that
affects the shared ``real_neo4j_client`` module-scoped fixture.
"""

from __future__ import annotations

import os
import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.clients.neo4j_client import Neo4jClient
from app.services.learning_context_service import get_node_context


pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


NEO4J_TEST_URI = os.getenv("NEO4J_TEST_URI", "bolt://localhost:7692")
NEO4J_TEST_USER = os.getenv("NEO4J_TEST_USER", "neo4j")
NEO4J_TEST_PASSWORD = os.getenv("NEO4J_TEST_PASSWORD", "testpassword")
NEO4J_TEST_DATABASE = os.getenv("NEO4J_TEST_DATABASE", "neo4j")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


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
    except Exception:
        pass


@pytest.fixture
async def two_subject_graph():
    """Seed two EntityNode subgraphs that share a concept name but differ in group_id.

    Layout (node_label [group_id]):

        贝叶斯定理 [physics] --RELATES_TO--> 先验概率 [physics]
        贝叶斯定理 [physics] --RELATES_TO--> 条件概率 [physics]
        贝叶斯定理 [math]    --RELATES_TO--> 概率测度 [math]
        贝叶斯定理 [math]    --RELATES_TO--> σ代数    [math]

    Additionally seeds one legacy NULL-group_id subgraph so the backward-
    compatibility ``OR group_id IS NULL`` branch is exercised.

    Yields a tuple ``(client, prefix)`` and patches
    ``learning_context_service.get_neo4j_client`` to return the test client,
    so that ``get_node_context()`` hits the test container instead of the
    singleton product client.
    """
    client = _make_client()
    await client.initialize()
    if getattr(client, "is_fallback_mode", False):
        await client.cleanup()
        pytest.skip("Neo4j test container not available (fallback mode)")

    prefix = f"test_{uuid.uuid4().hex[:8]}_"

    try:
        # Clean any residual test data from a prior failed run.
        await _cleanup_prefix(client, prefix)

        await client.run_query(
            """
            CREATE
              (bayes_physics:EntityNode {
                  id: $prefix + 'bayes_phys',
                  name: $prefix + '贝叶斯定理',
                  mastery_concept_id: $prefix + 'bayes_phys',
                  group_id: 'physics'
              }),
              (prior:EntityNode {
                  id: $prefix + 'prior',
                  name: $prefix + '先验概率',
                  group_id: 'physics'
              }),
              (cond:EntityNode {
                  id: $prefix + 'cond',
                  name: $prefix + '条件概率',
                  group_id: 'physics'
              }),
              (bayes_math:EntityNode {
                  id: $prefix + 'bayes_math',
                  name: $prefix + '贝叶斯定理',
                  mastery_concept_id: $prefix + 'bayes_math',
                  group_id: 'math'
              }),
              (measure:EntityNode {
                  id: $prefix + 'measure',
                  name: $prefix + '概率测度',
                  group_id: 'math'
              }),
              (sigma:EntityNode {
                  id: $prefix + 'sigma',
                  name: $prefix + 'sigma代数',
                  group_id: 'math'
              }),
              (bayes_physics)-[:RELATES_TO {reason: 'prior belief'}]->(prior),
              (bayes_physics)-[:RELATES_TO {reason: 'conditional rule'}]->(cond),
              (bayes_math)-[:RELATES_TO {reason: 'measure theory'}]->(measure),
              (bayes_math)-[:RELATES_TO {reason: 'sigma algebra basis'}]->(sigma)
            """,
            prefix=prefix,
        )

        await client.run_query(
            """
            CREATE
              (legacy_anchor:EntityNode {
                  id: $prefix + 'legacy_anchor',
                  name: $prefix + '老知识点',
                  mastery_concept_id: $prefix + 'legacy_anchor'
              }),
              (legacy_neighbor:EntityNode {
                  id: $prefix + 'legacy_neighbor',
                  name: $prefix + '老邻居'
              }),
              (legacy_anchor)-[:RELATES_TO {reason: 'historical link'}]->(legacy_neighbor)
            """,
            prefix=prefix,
        )

        # Patch the service-layer neo4j client factory so
        # get_node_context() reads from the test container instead of
        # the product singleton (which points at port 7689).
        # The actual import lives inside the function, so we patch
        # the source module: app.clients.neo4j_client.get_neo4j_client.
        #
        # Also bypass _fetch_tips_and_errors and _fetch_inherited_context
        # so the test focuses on the group_id neighbor filter. Both
        # helpers depend on external services (Graphiti, LearningMemoryClient)
        # that are either unavailable or carry pre-existing signature
        # mismatches unrelated to this change.
        with (
            patch(
                "app.clients.neo4j_client.get_neo4j_client",
                return_value=client,
            ),
            patch(
                "app.services.learning_context_service._fetch_tips_and_errors",
                new=AsyncMock(return_value=([], [])),
            ),
            patch(
                "app.services.learning_context_service._fetch_inherited_context",
                new=AsyncMock(return_value=[]),
            ),
            patch(
                "app.services.learning_context_service._fetch_mastery",
                new=AsyncMock(
                    return_value={
                        "node_name": f"{prefix}bayes",
                        "p_mastery": None,
                        "stability": None,
                        "next_review": None,
                    }
                ),
            ),
        ):
            yield client, prefix

    finally:
        await _cleanup_prefix(client, prefix)
        await client.cleanup()


# ---------------------------------------------------------------------------
# Scenario 1: cross-subject isolation
# ---------------------------------------------------------------------------


async def test_physics_group_does_not_leak_math_neighbors(two_subject_graph):
    """get_node_context(group_id='physics') must not return 'math' neighbors."""
    _client, prefix = two_subject_graph
    ctx = await get_node_context(
        node_id=f"{prefix}bayes_phys",
        group_id="physics",
    )

    neighbor_names = {
        rec.get("name") for rec in ctx["tier2"]["neighbors"] if rec.get("name")
    }

    # Physics neighbors should be present.
    assert f"{prefix}先验概率" in neighbor_names
    assert f"{prefix}条件概率" in neighbor_names

    # Math neighbors MUST be absent.
    assert f"{prefix}概率测度" not in neighbor_names
    assert f"{prefix}sigma代数" not in neighbor_names


async def test_math_group_does_not_leak_physics_neighbors(two_subject_graph):
    """Mirror image: math group must not pull in physics neighbors."""
    _client, prefix = two_subject_graph
    ctx = await get_node_context(
        node_id=f"{prefix}bayes_math",
        group_id="math",
    )

    neighbor_names = {
        rec.get("name") for rec in ctx["tier2"]["neighbors"] if rec.get("name")
    }

    assert f"{prefix}概率测度" in neighbor_names
    assert f"{prefix}sigma代数" in neighbor_names
    assert f"{prefix}先验概率" not in neighbor_names
    assert f"{prefix}条件概率" not in neighbor_names


# ---------------------------------------------------------------------------
# Scenario 2: NULL group_id legacy nodes remain readable
# ---------------------------------------------------------------------------


async def test_legacy_null_group_id_node_visible_from_any_group(two_subject_graph):
    """Nodes without group_id (pre-Phase-1 legacy seed) MUST still be read.

    The Cypher uses ``n.group_id = $gid OR n.group_id IS NULL`` so that
    the rollout does not break historical data. This test pins that
    backward-compat branch.
    """
    _client, prefix = two_subject_graph

    # Read the legacy node under a physics group context — the anchor
    # itself has no group_id, so the ``OR IS NULL`` branch is what
    # allows the query to succeed at all.
    ctx_physics = await get_node_context(
        node_id=f"{prefix}legacy_anchor",
        group_id="physics",
    )
    neighbor_names_physics = {
        rec.get("name") for rec in ctx_physics["tier2"]["neighbors"] if rec.get("name")
    }
    assert f"{prefix}老邻居" in neighbor_names_physics

    # Same read under a math group context should also succeed —
    # NULL-group nodes are visible to every group by design.
    ctx_math = await get_node_context(
        node_id=f"{prefix}legacy_anchor",
        group_id="math",
    )
    neighbor_names_math = {
        rec.get("name") for rec in ctx_math["tier2"]["neighbors"] if rec.get("name")
    }
    assert f"{prefix}老邻居" in neighbor_names_math
