# Sprint 1.1 — Phase 1 residual: kg_relevance weighted formula + degraded reason
# Story FR-KG-04 / openspec change: fix-fr-kg-04-schema-drift-and-sync-hardening
#
# TDD: tests written FIRST, before implementation.
"""
Tests for the upgraded kg_relevance computation.

Covers:
- ``QuestionGenerator._get_kg_relevance`` returns ``tuple[float, Optional[str]]``
- Weighted formula: ``CANVAS_EDGE = 1.0``, ``RELATES_TO = 0.7``, normalized by 8.0
- Degraded reason markers: ``"empty_graph"``, ``"neo4j_unavailable"``
- ``NodePriority.kg_relevance_degraded`` field accepts the degraded reason
- ``select_target_node`` destructures the tuple and propagates the degraded reason
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.exam_models import ExamMode, NodePriority
from app.services.question_generator import QuestionGenerator


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_records(weighted_degree: float, neighbor_count: int) -> List[Dict[str, Any]]:
    """Build a fake Neo4j result set with weighted_degree + neighbor_count."""
    return [{"weighted_degree": weighted_degree, "neighbor_count": neighbor_count}]


def _patch_neo4j_client(records_or_exception: Any) -> Any:
    """Return a context manager that patches ``get_neo4j_client`` to a fake client.

    ``records_or_exception``: either a list of dict records (success path) or an
    exception instance/class (failure path).
    """
    fake_client = MagicMock()
    if isinstance(records_or_exception, BaseException) or (
        isinstance(records_or_exception, type)
        and issubclass(records_or_exception, BaseException)
    ):
        fake_client.run_query = AsyncMock(side_effect=records_or_exception)
    else:
        fake_client.run_query = AsyncMock(return_value=records_or_exception)
    return patch(
        "app.clients.neo4j_client.get_neo4j_client",
        return_value=fake_client,
    )


# ---------------------------------------------------------------------------
# NodePriority degraded reason field
# ---------------------------------------------------------------------------


class TestNodePriorityDegradedField:
    """``NodePriority`` must carry the optional ``kg_relevance_degraded`` marker."""

    def test_default_degraded_is_none(self) -> None:
        np = NodePriority(
            node_id="n1",
            priority_score=0.5,
            p_mastery=0.4,
            retrievability=0.6,
            kg_relevance=0.5,
        )
        assert np.kg_relevance_degraded is None

    def test_accepts_degraded_string(self) -> None:
        np = NodePriority(
            node_id="n1",
            priority_score=0.5,
            p_mastery=0.4,
            retrievability=0.6,
            kg_relevance=0.5,
            kg_relevance_degraded="empty_graph",
        )
        assert np.kg_relevance_degraded == "empty_graph"


# ---------------------------------------------------------------------------
# _get_kg_relevance: weighted formula + degraded reasons
# ---------------------------------------------------------------------------


class TestGetKgRelevanceFormula:
    """The Cypher query MUST sum CANVAS_EDGE×1.0 + RELATES_TO×0.7 / 8.0."""

    @pytest.mark.asyncio
    async def test_canvas_edge_only_three_neighbors(self) -> None:
        # 3 CANVAS_EDGE neighbors → weighted_degree=3.0 → 3.0/8.0 = 0.375
        with _patch_neo4j_client(_make_records(weighted_degree=3.0, neighbor_count=3)):
            qg = QuestionGenerator()
            score, degraded = await qg._get_kg_relevance("n1", "c1")
        assert score == pytest.approx(0.375, rel=1e-3)
        assert degraded is None

    @pytest.mark.asyncio
    async def test_relates_to_only_four_neighbors(self) -> None:
        # 4 RELATES_TO neighbors → weighted=4*0.7=2.8 → 2.8/8.0 = 0.35
        with _patch_neo4j_client(_make_records(weighted_degree=2.8, neighbor_count=4)):
            qg = QuestionGenerator()
            score, degraded = await qg._get_kg_relevance("n1", "c1")
        assert score == pytest.approx(0.35, rel=1e-3)
        assert degraded is None

    @pytest.mark.asyncio
    async def test_mixed_edges(self) -> None:
        # 2 CANVAS_EDGE + 3 RELATES_TO = 2.0 + 2.1 = 4.1 → 4.1/8.0 ≈ 0.5125
        with _patch_neo4j_client(_make_records(weighted_degree=4.1, neighbor_count=5)):
            qg = QuestionGenerator()
            score, degraded = await qg._get_kg_relevance("n1", "c1")
        assert score == pytest.approx(0.5125, rel=1e-3)
        assert degraded is None

    @pytest.mark.asyncio
    async def test_high_degree_capped_at_one(self) -> None:
        # 10 CANVAS_EDGE → 10.0 → min(1.0, 10.0/8.0) = 1.0
        with _patch_neo4j_client(
            _make_records(weighted_degree=10.0, neighbor_count=10)
        ):
            qg = QuestionGenerator()
            score, degraded = await qg._get_kg_relevance("n1", "c1")
        assert score == 1.0
        assert degraded is None

    @pytest.mark.asyncio
    async def test_zero_weighted_returns_empty_graph_marker(self) -> None:
        with _patch_neo4j_client(_make_records(weighted_degree=0.0, neighbor_count=0)):
            qg = QuestionGenerator()
            score, degraded = await qg._get_kg_relevance("n1", "c1")
        assert score == 0.5
        assert degraded == "empty_graph"

    @pytest.mark.asyncio
    async def test_no_records_returns_empty_graph_marker(self) -> None:
        with _patch_neo4j_client([]):
            qg = QuestionGenerator()
            score, degraded = await qg._get_kg_relevance("n1", "c1")
        assert score == 0.5
        assert degraded == "empty_graph"

    @pytest.mark.asyncio
    async def test_connection_error_returns_neo4j_unavailable(self) -> None:
        with _patch_neo4j_client(ConnectionError("Neo4j down")):
            qg = QuestionGenerator()
            score, degraded = await qg._get_kg_relevance("n1", "c1")
        assert score == 0.5
        assert degraded == "neo4j_unavailable"

    @pytest.mark.asyncio
    async def test_runtime_error_returns_neo4j_unavailable(self) -> None:
        with _patch_neo4j_client(RuntimeError("driver gone")):
            qg = QuestionGenerator()
            score, degraded = await qg._get_kg_relevance("n1", "c1")
        assert score == 0.5
        assert degraded == "neo4j_unavailable"


# ---------------------------------------------------------------------------
# Cypher string assertions: the query must reference both edge types and the
# canonical SyncService schema fields
# ---------------------------------------------------------------------------


class TestKgRelevanceCypherShape:
    """Guard against future schema regressions by inspecting the Cypher text."""

    @pytest.mark.asyncio
    async def test_query_uses_id_and_camelcase_canvasid(self) -> None:
        captured: Dict[str, Any] = {}

        fake_client = MagicMock()

        async def fake_run_query(query: str, **kwargs: Any) -> List[Dict[str, Any]]:
            captured["query"] = query
            captured["kwargs"] = kwargs
            return _make_records(weighted_degree=1.0, neighbor_count=1)

        fake_client.run_query = AsyncMock(side_effect=fake_run_query)
        with patch(
            "app.clients.neo4j_client.get_neo4j_client",
            return_value=fake_client,
        ):
            qg = QuestionGenerator()
            await qg._get_kg_relevance("n1", "c1")

        cypher = captured["query"]
        # Schema correctness (FR-KG-04)
        assert "CanvasNode {id: $node_id}" in cypher, (
            "kg_relevance must query by {id: $node_id} to match SyncService writes"
        )
        assert "neighbor.canvasId" in cypher, (
            "kg_relevance must filter on canvasId (camelCase) not canvas_id"
        )
        # Weighted formula must reference both edge types
        assert "CANVAS_EDGE" in cypher and "RELATES_TO" in cypher, (
            "Weighted formula must consider CANVAS_EDGE and RELATES_TO together"
        )
        # SUM(CASE ...) shape — case-insensitive to allow stylistic variants
        normalized = cypher.lower()
        assert "sum" in normalized and "case" in normalized, (
            "Weighted formula must aggregate via SUM(CASE type(r) ...)"
        )


# ---------------------------------------------------------------------------
# select_target_node: tuple destructuring + degraded propagation
# ---------------------------------------------------------------------------


class TestSelectTargetNodeDegradedPropagation:
    """``select_target_node`` must persist ``kg_relevance_degraded`` on each NodePriority."""

    @pytest.mark.asyncio
    async def test_degraded_reason_persisted_on_node_priority(self) -> None:
        qg = QuestionGenerator()

        # Mock private helpers used by select_target_node
        with (
            patch.object(
                qg,
                "_get_canvas_nodes",
                AsyncMock(return_value=[{"id": "n1"}, {"id": "n2"}]),
            ),
            patch.object(
                qg,
                "_get_mastery_data",
                AsyncMock(return_value={"p_mastery": 0.4, "retrievability": 0.6}),
            ),
            patch.object(
                qg,
                "_get_kg_relevance",
                AsyncMock(side_effect=[(0.8, None), (0.5, "empty_graph")]),
            ),
        ):
            selected: Optional[NodePriority] = await qg.select_target_node(
                exam_id="exam-1",
                source_canvas_id="c1",
                exam_mode=ExamMode.POINT_TO_POINT,
                examined_nodes=None,
            )

        assert selected is not None
        # Top-priority node is n1 because kg_relevance=0.8 > 0.5
        # (with identical p_mastery + retrievability)
        assert selected.node_id == "n1"
        assert selected.kg_relevance == pytest.approx(0.8)
        assert selected.kg_relevance_degraded is None

    @pytest.mark.asyncio
    async def test_target_node_id_path_sets_no_degraded(self) -> None:
        """When target_node_id is provided, no kg query runs → degraded must be None."""
        qg = QuestionGenerator()
        with patch.object(
            qg,
            "_get_mastery_data",
            AsyncMock(return_value={"p_mastery": 0.4, "retrievability": 0.6}),
        ):
            np = await qg.select_target_node(
                exam_id="exam-1",
                source_canvas_id="c1",
                exam_mode=ExamMode.POINT_TO_POINT,
                target_node_id="explicit-node",
            )
        assert np is not None
        assert np.node_id == "explicit-node"
        assert np.kg_relevance_degraded is None
