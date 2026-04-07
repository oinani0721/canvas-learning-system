"""Integration tests for CRAG one-shot deep_research_fallback (Phase 4 task 4.5).

Part of fix-rag-faithfulness-and-add-crag-quality-loop. Validates that the
route_after_quality_check ↔ deep_research_fallback pair honors the
`deep_research_used` one-shot guard across a simulated multi-round flow:

- Round 1: router sees safe_degradation=True + deep_research_used=False
           -> routes to deep_research_fallback
           -> node flips deep_research_used=True and widens multi_queries
- Round 2: same quality_grade/safe_degradation, but deep_research_used=True
           -> router must NOT re-enter fallback; routes to faithfulness_check

Mock strategy: patch sys.modules['litellm'] so the node's lazy `import litellm`
picks up a stub. No real LLM call, no Neo4j fixture, no docker startup.
Unit tests in test_deep_research_fallback.py already cover router and node
in isolation; these tests exercise the router ↔ node ↔ router round-trip
that unit tests do not.
"""

import json
from types import SimpleNamespace
from unittest import mock as _mk

import pytest

from agentic_rag.deep_research import deep_research_fallback
from agentic_rag.state_graph import route_after_quality_check


def _make_runtime(context: dict | None) -> SimpleNamespace:
    return SimpleNamespace(context=context)


def _make_llm_reply(content: str) -> _mk.MagicMock:
    reply = _mk.MagicMock()
    reply.choices = [_mk.MagicMock(message=_mk.MagicMock(content=content))]
    return reply


# ── Scenario 1: router → node → verify one-shot guard flipped ────────────────


@pytest.mark.asyncio
async def test_route_enters_deep_research_after_safe_degradation():
    """Round 1: safe_degradation=True + not used -> deep_research_fallback.

    Then invoke the node and verify it returns a state update that (a) flips
    deep_research_used=True and (b) widens multi_queries via the mocked LLM.
    """
    state: dict = {
        "quality_grade": "low",
        "rewrite_count": 2,
        "safe_degradation": True,
        "deep_research_used": False,
    }

    # Router decision: must enter deep_research_fallback
    assert route_after_quality_check(state) == "deep_research_fallback"

    # Now simulate running the fallback node
    runtime = _make_runtime({"deep_research_enabled": True})
    state.update(
        {
            "original_query": "what is photosynthesis",
            "messages": [{"role": "user", "content": "what is photosynthesis"}],
        }
    )

    reply = _make_llm_reply(
        json.dumps(
            {
                "plan": "split compound concept into definition and mechanism",
                "queries": ["photosynthesis definition", "chlorophyll role"],
            }
        )
    )

    async def _mock_acompletion(**_kwargs):
        return reply

    stub_litellm = _mk.MagicMock(acompletion=_mock_acompletion)
    with _mk.patch.dict("sys.modules", {"litellm": stub_litellm}):
        update = await deep_research_fallback(state, runtime)

    # Guard must be flipped regardless of outcome
    assert update["deep_research_used"] is True
    # Node must widen recall scope
    assert update["cross_subject"] is True
    # Node must populate multi_queries from the mocked LLM
    assert update["multi_queries"] == [
        "photosynthesis definition",
        "chlorophyll role",
    ]


# ── Scenario 2: router does not re-enter deep_research after use ─────────────


def test_route_does_not_reenter_deep_research_second_time():
    """Round 2: safe_degradation still True but deep_research_used=True.

    The one-shot guard must prevent the router from routing back to
    deep_research_fallback. This is the critical invariant of Phase 4: no
    retrieval loop can exceed one CRAG fallback per query.
    """
    state_after = {
        "quality_grade": "low",
        "rewrite_count": 2,
        "safe_degradation": True,
        "deep_research_used": True,
    }
    assert route_after_quality_check(state_after) == "faithfulness_check"


# ── Scenario 3: simulate the second pass exits cleanly ───────────────────────


def test_deep_research_then_faithfulness_exits_cleanly():
    """Second pass after fallback: router must route to faithfulness_check.

    Even if quality_grade is still low and safe_degradation is still True,
    the router must not loop once deep_research_used=True. This ensures the
    graph terminates after one CRAG attempt regardless of retrieval outcome.
    """
    state_round2 = {
        "quality_grade": "low",
        "rewrite_count": 2,
        "safe_degradation": True,
        "deep_research_used": True,
    }
    next_route = route_after_quality_check(state_round2)
    assert next_route == "faithfulness_check", (
        "After one-shot deep_research, router must not re-enter fallback"
    )
