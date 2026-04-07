"""FR-KG-04 isolation Phase 3 — cross_canvas_retriever fail-soft semantics.

Before Phase 3, ``CrossCanvasService.search_related_nodes`` fell back to a
whole-vault LanceDB search when ``find_related_canvases`` returned an empty
list. Since ``find_related_canvases`` is still a placeholder that always
returns ``[]``, every RAG call was effectively doing an unfiltered search —
leaking nodes across canvases that were never meant to be linked.

Phase 3 changes the semantics: empty ``related_canvases`` → return ``[]``
(feature off). A module-level ``_warned_unimplemented`` sentinel ensures
the operator sees ONE warning at boot time, not one per retrieval call.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from agentic_rag.retrievers import cross_canvas_retriever as ccr_mod
from agentic_rag.retrievers.cross_canvas_retriever import (
    CrossCanvasRetrieverConfig,
    CrossCanvasService,
)


pytestmark = pytest.mark.asyncio


@pytest.fixture(autouse=True)
def _reset_warned_sentinel():
    """Each test starts with a fresh warning sentinel."""
    ccr_mod._warned_unimplemented = False
    yield
    ccr_mod._warned_unimplemented = False


@pytest.fixture
def mock_lancedb():
    """LanceDB client that ALWAYS returns a known canvas result.

    If the old whole-vault fallback path were accidentally re-introduced,
    the test would see this phantom result and fail — which is exactly
    the regression we want to catch.
    """
    client = AsyncMock()
    client.search = AsyncMock(
        return_value=[
            {
                "id": "phantom",
                "score": 0.99,
                "metadata": {"canvas_file": "phantom.canvas"},
            }
        ]
    )
    return client


# ---------------------------------------------------------------------------
# Scenario A — placeholder find_related_canvases → search returns []
# ---------------------------------------------------------------------------


async def test_search_returns_empty_when_placeholder_active(mock_lancedb):
    """Under the current placeholder, search() must return [] (not the
    phantom whole-vault result)."""
    service = CrossCanvasService(mock_lancedb, CrossCanvasRetrieverConfig())
    await service.initialize()

    results = await service.search(
        query="anything", canvas_file="physics.canvas", num_results=5
    )

    assert results == []
    # The fallback whole-vault call must never happen.
    assert mock_lancedb.search.await_count == 0


# ---------------------------------------------------------------------------
# Scenario B — dedup warning fires exactly once across N calls
# ---------------------------------------------------------------------------


async def test_warning_deduplicated_across_many_calls(mock_lancedb, caplog):
    """100 calls → at most 1 'cross_canvas disabled' warning entry.

    Uses caplog to capture stdlib logging events. cross_canvas_retriever.py
    has dual-mode logging (loguru if available, stdlib otherwise); in the
    unit-test env without loguru, stdlib logger is used and caplog works.
    Under loguru, we validate the sentinel flip instead.
    """
    import logging

    caplog.set_level(
        logging.WARNING, logger="agentic_rag.retrievers.cross_canvas_retriever"
    )

    service = CrossCanvasService(mock_lancedb, CrossCanvasRetrieverConfig())
    await service.initialize()

    for _ in range(100):
        await service.search(query="q", canvas_file="x.canvas", num_results=3)

    # The canonical invariant regardless of logging backend: the sentinel
    # must have flipped to True after the first call.
    assert ccr_mod._warned_unimplemented is True

    # If stdlib logging was captured, also verify dedup at log level.
    warning_hits = [
        rec for rec in caplog.records if "cross_canvas disabled" in rec.getMessage()
    ]
    # Either loguru swallowed them (len==0) or stdlib captured exactly 1.
    assert len(warning_hits) <= 1


# ---------------------------------------------------------------------------
# Scenario C — when find_related_canvases is patched to return real data,
#              no warning fires (future-path regression guard)
# ---------------------------------------------------------------------------


async def test_no_warning_when_relations_present(mock_lancedb):
    """If a future implementation wires in real canvas relations, the
    warning must NOT fire — the sentinel stays False."""
    service = CrossCanvasService(mock_lancedb, CrossCanvasRetrieverConfig())
    await service.initialize()

    # Patch the instance's find_related_canvases to return a real list.
    async def fake_related(canvas_file: str):
        return ["other.canvas", "another.canvas", canvas_file]

    service.find_related_canvases = fake_related  # type: ignore[assignment]

    await service.search(query="q", canvas_file="physics.canvas", num_results=5)

    assert ccr_mod._warned_unimplemented is False
    # LanceDB should be consulted exactly for the (now non-empty)
    # related_canvases — at least one real search call.
    assert mock_lancedb.search.await_count >= 1
