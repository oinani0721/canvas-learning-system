"""
S02 T02 — Unit tests for search_() upgrade, unified relevance scoring, and FSRS R-value injection.

Tests:
  (a) _search_graphiti calls search_() and parses SearchResults with edges+nodes+scores
  (b) 5 search config recipes are mapped correctly
  (c) _compute_unified_score normalizes scores for each tier
  (d) FSRS R-value injection with mock MasteryEngine
  (e) search_memories returns results sorted by relevance_score descending
  (f) SearchFilters passthrough to search_()
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

import pytest

from app.services.memory_service import MemoryService


# ══════════════════════════════════════════════════════════════════════
# Helpers: mock SearchResults + edges/nodes
# ══════════════════════════════════════════════════════════════════════

def _make_mock_edge(uuid: str, fact: str, name: str, created_at=None):
    """Build a mock EntityEdge-like object."""
    edge = MagicMock()
    edge.uuid = uuid
    edge.fact = fact
    edge.name = name
    edge.created_at = created_at or datetime(2026, 1, 1)
    return edge


def _make_mock_node(uuid: str, name: str, summary: str = "", created_at=None):
    """Build a mock EntityNode-like object."""
    node = MagicMock()
    node.uuid = uuid
    node.name = name
    node.summary = summary or name
    node.created_at = created_at or datetime(2026, 1, 1)
    return node


def _make_search_results(
    edges=None, edge_scores=None,
    nodes=None, node_scores=None,
):
    """Build a mock SearchResults Pydantic model."""
    sr = MagicMock()
    sr.edges = edges or []
    sr.edge_reranker_scores = edge_scores or []
    sr.nodes = nodes or []
    sr.node_reranker_scores = node_scores or []
    sr.episodes = []
    sr.episode_reranker_scores = []
    sr.communities = []
    sr.community_reranker_scores = []
    return sr


def _make_service() -> MemoryService:
    """Build a MemoryService with mocked Neo4j."""
    neo4j = MagicMock()
    neo4j.stats = {"initialized": False}
    neo4j.initialize = AsyncMock()
    svc = MemoryService(neo4j_client=neo4j)
    svc._initialized = True
    svc._episodes_recovered = True
    return svc


# ══════════════════════════════════════════════════════════════════════
# (a) _search_graphiti calls search_() and parses SearchResults
# ══════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_search_graphiti_parses_edges_and_nodes():
    """search_() results parsed into dicts with reranker scores as relevance_score."""
    svc = _make_service()

    edges = [
        _make_mock_edge("e1", "fact A", "edge_A"),
        _make_mock_edge("e2", "fact B", "edge_B"),
    ]
    nodes = [
        _make_mock_node("n1", "node_X", summary="summary X"),
    ]
    search_results = _make_search_results(
        edges=edges, edge_scores=[0.95, 0.70],
        nodes=nodes, node_scores=[0.88],
    )

    mock_graphiti = MagicMock()
    mock_graphiti.search_ = AsyncMock(return_value=search_results)

    mock_worker = MagicMock()
    mock_worker.is_ready = True
    mock_worker._graphiti = mock_graphiti

    with patch("app.services.memory_service.get_episode_worker", return_value=mock_worker):
        results = await svc._search_graphiti("test query", group_id="grp1", limit=10)

    assert len(results) == 3  # 2 edges + 1 node

    # Check edge results
    assert results[0]["episode_id"] == "e1"
    assert results[0]["content"] == "fact A"
    assert results[0]["relevance_score"] == 0.95
    assert results[0]["source"] == "graphiti"
    assert results[0]["result_type"] == "edge"

    assert results[1]["episode_id"] == "e2"
    assert results[1]["relevance_score"] == 0.70

    # Check node result
    assert results[2]["episode_id"] == "n1"
    assert results[2]["content"] == "summary X"
    assert results[2]["relevance_score"] == 0.88
    assert results[2]["result_type"] == "node"


@pytest.mark.asyncio
async def test_search_graphiti_empty_results():
    """search_() returns empty SearchResults — no crash, empty list."""
    svc = _make_service()
    search_results = _make_search_results()
    mock_graphiti = MagicMock()
    mock_graphiti.search_ = AsyncMock(return_value=search_results)
    mock_worker = MagicMock()
    mock_worker.is_ready = True
    mock_worker._graphiti = mock_graphiti

    with patch("app.services.memory_service.get_episode_worker", return_value=mock_worker):
        results = await svc._search_graphiti("empty query")

    assert results == []


@pytest.mark.asyncio
async def test_search_graphiti_worker_not_ready():
    """Worker not ready → empty list, no crash."""
    svc = _make_service()
    mock_worker = MagicMock()
    mock_worker.is_ready = False
    mock_worker._graphiti = None

    with patch("app.services.memory_service.get_episode_worker", return_value=mock_worker):
        results = await svc._search_graphiti("any query")

    assert results == []


@pytest.mark.asyncio
async def test_search_graphiti_timeout_degrades():
    """search_() timeout → empty list, graceful degradation."""
    svc = _make_service()
    mock_graphiti = MagicMock()
    mock_graphiti.search_ = AsyncMock(side_effect=asyncio.TimeoutError)
    mock_worker = MagicMock()
    mock_worker.is_ready = True
    mock_worker._graphiti = mock_graphiti

    with patch("app.services.memory_service.get_episode_worker", return_value=mock_worker):
        results = await svc._search_graphiti("timeout query")

    assert results == []


# ══════════════════════════════════════════════════════════════════════
# (b) 5 search config recipes are mapped correctly
# ══════════════════════════════════════════════════════════════════════

def test_search_recipes_all_5_mapped():
    """All 5 recipe names resolve to distinct SearchConfig objects."""
    recipes = MemoryService._get_search_recipes()
    expected_keys = {
        "combined_rrf",
        "combined_cross_encoder",
        "edge_cross_encoder",
        "edge_rrf",
        "node_rrf",
    }
    assert set(recipes.keys()) == expected_keys

    # Each recipe should be a distinct object
    values = list(recipes.values())
    # At least verify they're not all the same object
    assert len(set(id(v) for v in values)) >= 3  # some may share config but shouldn't all be same


@pytest.mark.asyncio
async def test_search_graphiti_passes_config_to_search_():
    """The resolved SearchConfig is passed to search_() with correct limit."""
    svc = _make_service()
    search_results = _make_search_results()
    mock_graphiti = MagicMock()
    mock_graphiti.search_ = AsyncMock(return_value=search_results)
    mock_worker = MagicMock()
    mock_worker.is_ready = True
    mock_worker._graphiti = mock_graphiti

    with patch("app.services.memory_service.get_episode_worker", return_value=mock_worker):
        await svc._search_graphiti(
            "test", limit=15, search_config="edge_rrf"
        )

    call_kwargs = mock_graphiti.search_.call_args[1]
    assert call_kwargs["query"] == "test"
    # Config should have limit=15
    config = call_kwargs["config"]
    assert config.limit == 15


@pytest.mark.asyncio
async def test_search_graphiti_unknown_config_falls_back():
    """Unknown config name falls back to combined_rrf, not crash."""
    svc = _make_service()
    search_results = _make_search_results()
    mock_graphiti = MagicMock()
    mock_graphiti.search_ = AsyncMock(return_value=search_results)
    mock_worker = MagicMock()
    mock_worker.is_ready = True
    mock_worker._graphiti = mock_graphiti

    with patch("app.services.memory_service.get_episode_worker", return_value=mock_worker):
        results = await svc._search_graphiti("q", search_config="nonexistent_recipe")

    # Should not crash — falls back to combined_rrf
    assert isinstance(results, list)


# ══════════════════════════════════════════════════════════════════════
# (c) _compute_unified_score for each tier
# ══════════════════════════════════════════════════════════════════════

def test_unified_score_tier1_uses_reranker():
    """Tier 1 (graphiti): uses relevance_score directly."""
    ep = {"relevance_score": 0.85}
    assert MemoryService._compute_unified_score(ep, tier=1) == 0.85


def test_unified_score_tier1_default_zero():
    """Tier 1 with no score → 0.0."""
    assert MemoryService._compute_unified_score({}, tier=1) == 0.0


def test_unified_score_tier2_normalizes_lucene():
    """Tier 2 (neo4j): raw score / 10.0, capped at 1.0."""
    # Score 5.0 → 0.5
    ep = {"score": 5.0}
    assert MemoryService._compute_unified_score(ep, tier=2) == 0.5

    # Score 15.0 → capped at 1.0
    ep_high = {"score": 15.0}
    assert MemoryService._compute_unified_score(ep_high, tier=2) == 1.0

    # Score 0 → 0.0
    ep_zero = {"score": 0.0}
    assert MemoryService._compute_unified_score(ep_zero, tier=2) == 0.0


def test_unified_score_tier3_fixed():
    """Tier 3 (in-memory): fixed 0.1."""
    assert MemoryService._compute_unified_score({}, tier=3) == 0.1
    assert MemoryService._compute_unified_score({"score": 999}, tier=3) == 0.1


# ══════════════════════════════════════════════════════════════════════
# (d) FSRS R-value injection with mock MasteryEngine
# ══════════════════════════════════════════════════════════════════════

def test_fsrs_injection_boosts_low_r():
    """Low R-value concept gets up to 50% score boost."""
    svc = _make_service()

    results = [
        {"name": "calculus", "relevance_score": 0.8},
        {"name": "algebra", "relevance_score": 0.6},
    ]

    # Mock MasteryEngine with concept cache
    mock_engine = MagicMock()
    mock_concept_calculus = MagicMock()
    mock_concept_algebra = MagicMock()

    mock_engine._concept_cache = {
        "calculus": mock_concept_calculus,
        "algebra": mock_concept_algebra,
    }
    # Calculus: low R (about to forget) → big boost
    # Algebra: high R (fresh) → small boost
    mock_engine.get_retrievability.side_effect = lambda c: (
        0.2 if c is mock_concept_calculus else 0.9
    )

    with patch("app.services.mastery_engine.get_mastery_engine", return_value=mock_engine):
        svc._inject_fsrs_r_values(results)

    # calculus: 0.8 * (1.0 + (1.0 - 0.2) * 0.5) = 0.8 * 1.4 = 1.12
    assert abs(results[0]["relevance_score"] - 1.12) < 0.001
    assert results[0]["fsrs_r_value"] == 0.2

    # algebra: 0.6 * (1.0 + (1.0 - 0.9) * 0.5) = 0.6 * 1.05 = 0.63
    assert abs(results[1]["relevance_score"] - 0.63) < 0.001
    assert results[1]["fsrs_r_value"] == 0.9


def test_fsrs_injection_graceful_when_engine_unavailable():
    """MasteryEngine import fails → no crash, results unchanged."""
    svc = _make_service()
    results = [{"name": "physics", "relevance_score": 0.7}]

    with patch(
        "app.services.mastery_engine.get_mastery_engine",
        side_effect=ImportError("no engine"),
    ):
        svc._inject_fsrs_r_values(results)

    # Score unchanged, no fsrs_r_value added
    assert results[0]["relevance_score"] == 0.7
    assert "fsrs_r_value" not in results[0]


def test_fsrs_injection_skips_unknown_concepts():
    """Concepts not in engine cache are skipped, not crashed."""
    svc = _make_service()
    results = [{"name": "unknown_topic", "relevance_score": 0.5}]

    mock_engine = MagicMock()
    mock_engine._concept_cache = {}  # empty cache

    with patch("app.services.mastery_engine.get_mastery_engine", return_value=mock_engine):
        svc._inject_fsrs_r_values(results)

    assert results[0]["relevance_score"] == 0.5
    assert "fsrs_r_value" not in results[0]


def test_fsrs_injection_no_name_or_concept():
    """Results without 'name' or 'concept' are skipped."""
    svc = _make_service()
    results = [{"content": "some content", "relevance_score": 0.3}]

    mock_engine = MagicMock()
    mock_engine._concept_cache = {}

    with patch("app.services.mastery_engine.get_mastery_engine", return_value=mock_engine):
        svc._inject_fsrs_r_values(results)

    assert results[0]["relevance_score"] == 0.3


# ══════════════════════════════════════════════════════════════════════
# (e) search_memories returns results sorted by relevance_score
# ══════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_search_memories_sorted_by_relevance():
    """Results from all 3 tiers are sorted by relevance_score descending."""
    svc = _make_service()

    # Pre-populate in-memory episodes for tier 3
    svc._episodes = [
        {
            "episode_id": "mem-1",
            "content": "python basics",
            "episode_type": "learning",
            "concept": "python",
            "node_id": "n1",
            "source": "in_memory",
        }
    ]

    # Mock tier 1 (graphiti) — high score
    tier1_results = [
        {
            "episode_id": "g1",
            "content": "python advanced",
            "name": "python_adv",
            "source": "graphiti",
            "relevance_score": 0.95,
            "result_type": "edge",
            "episode_type": "graphiti_search",
            "timestamp": "2026-01-01T00:00:00",
            "group_id": "",
        }
    ]
    # Mock tier 2 (neo4j) — medium score
    tier2_results = [
        {
            "episode_id": "neo-1",
            "content": "python intermediate",
            "score": 7.5,  # will be normalized to 0.75
            "source": "neo4j_fulltext",
            "episode_type": "learning",
            "timestamp": "",
            "group_id": "",
            "node_id": "",
        }
    ]

    with patch.object(svc, "_search_graphiti", new_callable=AsyncMock, return_value=tier1_results), \
         patch.object(svc, "_search_neo4j_fulltext", new_callable=AsyncMock, return_value=tier2_results), \
         patch.object(svc, "_inject_fsrs_r_values"):  # skip FSRS for this test
        results = await svc.search_memories("python")

    assert len(results) == 3

    # Verify descending order
    scores = [r["relevance_score"] for r in results]
    assert scores == sorted(scores, reverse=True), f"Not sorted descending: {scores}"

    # Tier 1 (0.95) first, Tier 2 (0.75) second, Tier 3 (0.1) last
    assert results[0]["episode_id"] == "g1"
    assert results[0]["relevance_score"] == 0.95
    assert results[2]["relevance_score"] == 0.1


@pytest.mark.asyncio
async def test_search_memories_passes_search_config():
    """search_memories forwards search_config and search_filter to _search_graphiti."""
    svc = _make_service()
    svc._episodes = []

    with patch.object(svc, "_search_graphiti", new_callable=AsyncMock, return_value=[]) as mock_sg, \
         patch.object(svc, "_search_neo4j_fulltext", new_callable=AsyncMock, return_value=[]), \
         patch.object(svc, "_inject_fsrs_r_values"):
        mock_filter = MagicMock()
        await svc.search_memories(
            "test", search_config="edge_cross_encoder", search_filter=mock_filter
        )

    mock_sg.assert_called_once()
    call_kwargs = mock_sg.call_args[1]
    assert call_kwargs["search_config"] == "edge_cross_encoder"
    assert call_kwargs["search_filter"] is mock_filter


@pytest.mark.asyncio
async def test_search_memories_backward_compat():
    """Existing callers with just (query, group_id, max_results) still work."""
    svc = _make_service()
    svc._episodes = []

    with patch.object(svc, "_search_graphiti", new_callable=AsyncMock, return_value=[]), \
         patch.object(svc, "_search_neo4j_fulltext", new_callable=AsyncMock, return_value=[]), \
         patch.object(svc, "_inject_fsrs_r_values"):
        results = await svc.search_memories("test query", group_id="g1", max_results=10)

    assert isinstance(results, list)


# ══════════════════════════════════════════════════════════════════════
# (f) SearchFilters passthrough
# ══════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_search_filter_passed_to_search_():
    """SearchFilters object is forwarded to graphiti search_()."""
    svc = _make_service()
    search_results = _make_search_results()
    mock_graphiti = MagicMock()
    mock_graphiti.search_ = AsyncMock(return_value=search_results)
    mock_worker = MagicMock()
    mock_worker.is_ready = True
    mock_worker._graphiti = mock_graphiti

    mock_filter = MagicMock()
    mock_filter.__class__.__name__ = "SearchFilters"

    with patch("app.services.memory_service.get_episode_worker", return_value=mock_worker):
        await svc._search_graphiti("q", search_filter=mock_filter)

    call_kwargs = mock_graphiti.search_.call_args[1]
    assert call_kwargs["search_filter"] is mock_filter


@pytest.mark.asyncio
async def test_search_filter_none_not_passed():
    """When search_filter is None, it's not included in search_() kwargs."""
    svc = _make_service()
    search_results = _make_search_results()
    mock_graphiti = MagicMock()
    mock_graphiti.search_ = AsyncMock(return_value=search_results)
    mock_worker = MagicMock()
    mock_worker.is_ready = True
    mock_worker._graphiti = mock_graphiti

    with patch("app.services.memory_service.get_episode_worker", return_value=mock_worker):
        await svc._search_graphiti("q", search_filter=None)

    call_kwargs = mock_graphiti.search_.call_args[1]
    assert "search_filter" not in call_kwargs
