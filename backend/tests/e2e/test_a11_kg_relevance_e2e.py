# Canvas Learning System - A11 KG-Relevance End-to-End Regression
# openspec change: fix-fr-kg-04-schema-drift-and-sync-hardening (A11)
#
# Phase 5 deferred Task 5.1 closure: migrate A11 off MagicMock toward a real
# Neo4j test container so regressions to constant-0.5 kg_relevance (the A11
# root cause) are caught in CI, not only by manual runs of the driver script.
"""End-to-end regression for the A11 kg_relevance fix against real Neo4j.

The driver script at ``scripts/test-a11-end-to-end.py`` renders a
user-facing Rich report; this pytest file is the **CI regression guard**
for the same scenario. Assertions are deliberately redundant with the
script's runtime checks so this file fails loudly even if a future change
replaces the script with something else.

Fixture strategy
----------------
- Creates a **function-scoped** Neo4jClient per test — bypasses the
  project's module-scoped ``real_neo4j_client`` to avoid the pytest-asyncio
  "Future attached to a different loop" bug that surfaces when an
  asyncio-connection-holding fixture outlives the event loop it was
  created on (``_bmad-output/test-artifacts/test-review-epic32-20260210.md``
  documents the exact same gotcha for epic 32 integration tests).
  Cost: ~100ms extra per test for driver init; benefit: no loop bleed.
- Stubs orthogonal dependencies (``_get_canvas_nodes`` and
  ``_get_mastery_data``) on the QuestionGenerator instance so
  ``kg_relevance`` is the single variable driving priority.
- Pins ``app.clients.neo4j_client.get_neo4j_client`` to the fresh test
  client so the function-local import inside ``_get_kg_relevance``
  resolves to the port-7692 container, not a stale singleton.

Assertions (aligned with plan §验证 Plan)
-----------------------------------------
1. Schema: canonical CanvasNode with ``{id, canvasId}`` exists, 0 legacy
   ``{uuid}`` nodes.
2. ``_get_kg_relevance`` returns the exact weighted-degree scores for
   each fixture node (no constant-0.5 regression).
3. ``_get_kg_relevance`` attaches ``"empty_graph"`` only for the two
   zero-edge nodes — NOT for nodeC (which has 4 edges → 0.5 raw score,
   same number as the degraded fallback, different meaning).
4. ``select_target_node`` picks nodes in connectivity order:
   nodeE → nodeD → nodeC → nodeA → nodeB.
5. At least 3 distinct ``kg_relevance`` values observed — trips if the
   bug where every node collapses to 0.5 ever reappears.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import pytest

from app.clients import neo4j_client as neo4j_module
from app.clients.neo4j_client import Neo4jClient
from app.models.exam_models import ExamMode, NodePriority
from app.services.question_generator import QuestionGenerator

# Mark every test in this module as ``e2e`` + ``slow`` so developers can skip
# with ``-m 'not e2e'`` when iterating on unrelated code. The ``a11_canvas``
# fixture below graceful-skips when the neo4j-test container is unreachable,
# so no separate ``real_neo4j`` mark is needed (and would just be a noisy
# unknown mark — it is not registered in backend/pytest.ini).
#
# NOTE: intentionally NOT including ``pytest.mark.asyncio`` — backend/pytest.ini
# enables ``asyncio_mode = auto`` which auto-marks every async def test, and
# adding an explicit mark on top of auto-mode is the documented cause of the
# "Future attached to a different loop" regression from epic 32.
pytestmark = [
    pytest.mark.e2e,
    pytest.mark.slow,
]

TEST_NEO4J_URI = os.environ.get("NEO4J_TEST_URI", "bolt://localhost:7692")
TEST_NEO4J_USER = os.environ.get("NEO4J_TEST_USER", "neo4j")
TEST_NEO4J_PASSWORD = os.environ.get("NEO4J_TEST_PASSWORD", "testpassword")


# ---------------------------------------------------------------------------
# Fixture data (kept in sync with scripts/test-a11-end-to-end.py)
# ---------------------------------------------------------------------------
CANVAS_ID = "a11-pytest-canvas"
PRIMARY_NODES = ["nodeE", "nodeD", "nodeC", "nodeA", "nodeB"]
FILLER_NODES = [f"pyfill-{i}" for i in range(1, 9)]

EDGE_COUNTS: Dict[str, int] = {
    "nodeA": 0,
    "nodeB": 0,
    "nodeC": 4,
    "nodeD": 6,
    "nodeE": 8,
}

EXPECTED_KG: Dict[str, tuple[float, Optional[str]]] = {
    "nodeA": (0.5, "empty_graph"),
    "nodeB": (0.5, "empty_graph"),
    "nodeC": (0.5, None),  # computed, NOT degraded
    "nodeD": (0.75, None),
    "nodeE": (1.0, None),
}

# A10 Phase 0 NOTE: the constant 0.0 here is INTENTIONAL test simplification,
# not a regression of the silent bug fixed in commit ${PHASE0_COMMIT}.
# This stub replaces _get_mastery_data wholesale (see stubbed_qg fixture below),
# bypassing the real MasteryEngine routing entirely. The test pins
# effective_proficiency to a constant so that kg_relevance is the only variable
# affecting priority ordering. Any constant value works — we kept 0.0 for
# git-history clarity.
STUB_MASTERY: Dict[str, Any] = {
    "p_mastery": 0.5,
    "retrievability": 1.0,
    "effective_proficiency": 0.0,
    "mastery_level": 0,
    "mastery_label": "Not Assessed",
}


# ---------------------------------------------------------------------------
# Real-Neo4j seeding helpers — raw Cypher matching SyncService schema
# ---------------------------------------------------------------------------
async def _clear_canvas(client: Neo4jClient) -> None:
    await client.run_query(
        "MATCH (n:CanvasNode) WHERE n.canvasId = $canvas_id DETACH DELETE n",
        canvas_id=CANVAS_ID,
    )


async def _seed_canvas(client: Neo4jClient) -> None:
    """Seed the A11 test canvas. Same shape as the driver script but with
    a distinct canvas_id so pytest and the CLI script can run concurrently
    without stepping on each other's data."""
    await _clear_canvas(client)

    # Nodes
    for node_id in PRIMARY_NODES + FILLER_NODES:
        await client.run_query(
            """
            MERGE (n:CanvasNode {id: $node_id})
            SET n.title = $title,
                n.content = '',
                n.canvasId = $canvas_id,
                n.type = 'text',
                n.x = 0,
                n.y = 0,
                n.width = 200,
                n.height = 120
            """,
            node_id=node_id,
            title=f"pytest-{node_id}",
            canvas_id=CANVAS_ID,
        )

    # Edges — nodeC×4 + nodeD×6 + nodeE×8 = 18
    for primary, count in EDGE_COUNTS.items():
        for i in range(count):
            filler = FILLER_NODES[i]
            edge_id = f"pye-{primary}-{filler}"
            await client.run_query(
                """
                MATCH (src:CanvasNode {id: $src_id})
                MATCH (tgt:CanvasNode {id: $tgt_id})
                MERGE (src)-[e:CANVAS_EDGE {id: $edge_id}]->(tgt)
                SET e.canvasId = $canvas_id,
                    e.label = ''
                """,
                src_id=primary,
                tgt_id=filler,
                edge_id=edge_id,
                canvas_id=CANVAS_ID,
            )


# ---------------------------------------------------------------------------
# Pytest fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
async def a11_canvas():
    """Create a function-scoped Neo4jClient pointed at the test container,
    seed the A11 fixture, pin ``get_neo4j_client``, yield the client, cleanup.

    This fixture deliberately does NOT depend on ``real_neo4j_client`` from
    conftest.py — that module-scoped fixture holds connections bound to the
    first event loop it sees, which breaks when pytest-asyncio auto-mode
    creates a fresh loop per test.

    Pinning ``get_neo4j_client`` is necessary because the function-local
    ``from app.clients.neo4j_client import get_neo4j_client`` inside
    ``_get_kg_relevance`` would otherwise resolve via the global singleton,
    which may point at a non-test client depending on test order.
    """
    client = Neo4jClient(
        uri=TEST_NEO4J_URI,
        user=TEST_NEO4J_USER,
        password=TEST_NEO4J_PASSWORD,
        database="neo4j",
    )
    try:
        await client.initialize()
    except Exception as exc:
        pytest.skip(f"neo4j-test container unreachable at {TEST_NEO4J_URI}: {exc}")
    if getattr(client, "is_fallback_mode", False):
        await client.cleanup()
        pytest.skip("neo4j-test container responded with fallback mode")

    await _seed_canvas(client)

    original_get = getattr(neo4j_module, "get_neo4j_client", None)
    original_instance = getattr(neo4j_module, "_client_instance", None)
    neo4j_module.get_neo4j_client = lambda *a, **kw: client  # type: ignore[assignment]
    neo4j_module._client_instance = client  # type: ignore[attr-defined]

    try:
        yield client
    finally:
        if original_get is not None:
            neo4j_module.get_neo4j_client = original_get  # type: ignore[assignment]
        neo4j_module._client_instance = original_instance  # type: ignore[attr-defined]
        try:
            await _clear_canvas(client)
        except Exception:
            pass
        try:
            await client.cleanup()
        except Exception:
            pass


@pytest.fixture
def stubbed_qg() -> QuestionGenerator:
    """Return a QuestionGenerator with orthogonal helpers stubbed.

    Only ``_get_canvas_nodes`` and ``_get_mastery_data`` are replaced —
    ``_get_kg_relevance`` hits the real test Neo4j. This is the whole point:
    stubbing the thing under test would invalidate the regression.
    """
    qg = QuestionGenerator()

    async def _stub_mastery(node_id: str) -> Dict[str, Any]:
        return dict(STUB_MASTERY)

    async def _stub_canvas_nodes(canvas_id: str) -> List[Dict[str, str]]:
        return [{"id": nid} for nid in PRIMARY_NODES]

    qg._get_mastery_data = _stub_mastery  # type: ignore[method-assign]
    qg._get_canvas_nodes = _stub_canvas_nodes  # type: ignore[method-assign]
    return qg


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------
class TestA11SchemaIsCanonical:
    """Phase 1 negative assertion: no legacy ``{uuid}`` nodes in the seeded canvas."""

    async def test_no_legacy_uuid_nodes(self, a11_canvas: Neo4jClient) -> None:
        rows = await a11_canvas.run_query(
            """
            MATCH (n:CanvasNode)
            WHERE n.canvasId = $canvas_id AND n.uuid IS NOT NULL
            RETURN count(n) AS c
            """,
            canvas_id=CANVAS_ID,
        )
        assert int(rows[0]["c"]) == 0, (
            "schema drift regression — CanvasNode must not write {uuid}"
        )

    async def test_all_nodes_have_canonical_id_and_canvas_id(
        self, a11_canvas: Neo4jClient
    ) -> None:
        rows = await a11_canvas.run_query(
            """
            MATCH (n:CanvasNode)
            WHERE n.canvasId = $canvas_id AND n.id IS NOT NULL
            RETURN count(n) AS c
            """,
            canvas_id=CANVAS_ID,
        )
        expected = len(PRIMARY_NODES) + len(FILLER_NODES)
        assert int(rows[0]["c"]) == expected, (
            f"expected {expected} canonical nodes, got {rows[0]['c']}"
        )


class TestA11KgRelevanceDirect:
    """Phase 1 + Phase 6: ``_get_kg_relevance`` returns weighted scores + degraded markers."""

    @pytest.mark.parametrize("node_id", list(EDGE_COUNTS))
    async def test_weighted_score_matches_expected(
        self,
        a11_canvas: Neo4jClient,
        stubbed_qg: QuestionGenerator,
        node_id: str,
    ) -> None:
        expected_score, expected_degraded = EXPECTED_KG[node_id]
        score, degraded = await stubbed_qg._get_kg_relevance(node_id, CANVAS_ID)
        assert score == pytest.approx(expected_score, abs=1e-3), (
            f"{node_id}: expected {expected_score}, got {score}"
        )
        assert degraded == expected_degraded, (
            f"{node_id}: expected degraded={expected_degraded!r}, got {degraded!r}"
        )

    async def test_nodeC_four_edges_NOT_marked_as_degraded(
        self, a11_canvas: Neo4jClient, stubbed_qg: QuestionGenerator
    ) -> None:
        """Critical A11 assertion — nodeC has raw kg=0.5 but is NOT degraded.

        The raw score 0.5 collides with the degraded-fallback value 0.5;
        only the ``kg_relevance_degraded`` field distinguishes "4 real
        edges" from "no edges, fell back". This test prevents a future
        regression where someone "simplifies" the fallback marker away.
        """
        score, degraded = await stubbed_qg._get_kg_relevance("nodeC", CANVAS_ID)
        assert score == pytest.approx(0.5, abs=1e-3)
        assert degraded is None, (
            "nodeC has 4 edges — its 0.5 score is computed, NOT degraded"
        )


class TestA11SelectionSequence:
    """Phase 1 + Phase 6: ``select_target_node`` orders by connectivity."""

    async def test_first_pick_is_highest_connectivity(
        self, a11_canvas: Neo4jClient, stubbed_qg: QuestionGenerator
    ) -> None:
        picked: Optional[NodePriority] = await stubbed_qg.select_target_node(
            exam_id="a11-pytest",
            source_canvas_id=CANVAS_ID,
            exam_mode=ExamMode.MIXED,
            examined_nodes=None,
        )
        assert picked is not None
        assert picked.node_id == "nodeE", (
            "nodeE has 8 edges → must be picked first; "
            "if this fails, kg_relevance is probably constant again"
        )
        assert picked.kg_relevance == pytest.approx(1.0, abs=1e-3)
        assert picked.kg_relevance_degraded is None

    async def test_full_sequence_reflects_connectivity_ranking(
        self, a11_canvas: Neo4jClient, stubbed_qg: QuestionGenerator
    ) -> None:
        examined: List[str] = []
        sequence: List[NodePriority] = []
        for _ in range(len(PRIMARY_NODES)):
            picked = await stubbed_qg.select_target_node(
                exam_id="a11-pytest",
                source_canvas_id=CANVAS_ID,
                exam_mode=ExamMode.MIXED,
                examined_nodes=list(examined),
            )
            assert picked is not None
            sequence.append(picked)
            examined.append(picked.node_id)

        actual_order = [p.node_id for p in sequence]
        assert actual_order == ["nodeE", "nodeD", "nodeC", "nodeA", "nodeB"], (
            f"connectivity-ranked selection broken — got {actual_order}"
        )

        # Degraded markers persist across the sequence
        by_id = {p.node_id: p for p in sequence}
        assert by_id["nodeA"].kg_relevance_degraded == "empty_graph"
        assert by_id["nodeB"].kg_relevance_degraded == "empty_graph"
        assert by_id["nodeC"].kg_relevance_degraded is None
        assert by_id["nodeD"].kg_relevance_degraded is None
        assert by_id["nodeE"].kg_relevance_degraded is None

    async def test_at_least_three_distinct_kg_values_observed(
        self, a11_canvas: Neo4jClient, stubbed_qg: QuestionGenerator
    ) -> None:
        """Regression guard for the A11 root-cause signature.

        The original bug collapsed all 5 nodes to kg_relevance=0.5 (single
        value). The fix must produce at least 3 distinct values across the
        primary fixture: {0.5, 0.75, 1.0}. Any future change that trips
        this assertion is strong evidence of a kg_relevance regression.
        """
        examined: List[str] = []
        seen_values: set[float] = set()
        for _ in range(len(PRIMARY_NODES)):
            picked = await stubbed_qg.select_target_node(
                exam_id="a11-pytest",
                source_canvas_id=CANVAS_ID,
                exam_mode=ExamMode.MIXED,
                examined_nodes=list(examined),
            )
            assert picked is not None
            seen_values.add(round(picked.kg_relevance, 3))
            examined.append(picked.node_id)

        assert len(seen_values) >= 3, (
            f"A11 regression: expected ≥3 distinct kg_relevance values, "
            f"observed {sorted(seen_values)} — likely back to constant 0.5"
        )
