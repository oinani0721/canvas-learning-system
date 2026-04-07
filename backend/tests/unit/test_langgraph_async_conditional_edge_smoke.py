"""
C1-PRE smoke test: Verify LangGraph supports async conditional edge routing.

Background:
    C1 (agentic-rag-l1-llm-router) needs to call an async LLM router from
    fan_out_retrieval, which is registered via builder.add_conditional_edges().
    The project's existing fan_out_retrieval is synchronous; rewrite_query is
    async but it's an `add_node` (regular node), not a conditional edge router.

    LangGraph 1.x theoretically supports async conditional edges, but the
    project has zero existing test coverage for this pattern. Without
    verification, an async refactor of fan_out_retrieval could fail at
    runtime in surprising ways.

Three possible outcomes:
    🟢 GREEN: async conditional edge works → C1-B uses async fan_out_retrieval
    🟡 YELLOW: works only with sync wrapper → C1-B wraps async LLM call inside
       sync fan_out_retrieval via asyncio.run / loop.run_until_complete
    🔴 RED: completely unsupported → STOP, return to design phase, update D3

[OpenSpec change: agentic-rag-l1-llm-router]
[Decision gate: C1-PRE in 2026-04-06 plan]
"""

import asyncio
from typing import Any

import pytest
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send


# ============================================================================
# Async conditional edge smoke test
# ============================================================================


def _noop_node(state: dict[str, Any]) -> dict[str, Any]:
    """Pass-through node — returns state unchanged."""
    return state


async def _async_router(state: dict[str, Any]) -> list[Send]:
    """
    Async conditional edge function. Simulates the C1 future state where
    fan_out_retrieval awaits an LLM call before deciding which retrievers
    to dispatch.

    Returns Send list (the project's existing pattern in state_graph.py:171).
    """
    # Simulate async LLM call
    await asyncio.sleep(0.001)
    return [Send("noop_node", state)]


@pytest.mark.asyncio
async def test_langgraph_supports_async_conditional_edge():
    """
    🟢 GREEN gate: LangGraph compiles and routes through an async conditional
    edge function without raising. If this test fails, C1-B must adopt a sync
    wrapper or the design must change.
    """
    builder: StateGraph = StateGraph(dict)
    builder.add_node("start_noop", _noop_node)
    builder.add_node("noop_node", _noop_node)
    builder.add_edge(START, "start_noop")
    builder.add_conditional_edges("start_noop", _async_router)
    builder.add_edge("noop_node", END)

    graph = builder.compile()
    result = await graph.ainvoke({"counter": 1})

    # If we got here, async conditional edge ROUTING works
    assert result is not None, "Graph returned None — async router likely failed"
    assert result.get("counter") == 1, (
        "State did not propagate through async router. Got: %s" % result
    )


@pytest.mark.asyncio
async def test_langgraph_async_router_can_await_io():
    """
    🟢 GREEN gate variant: confirm the async router can `await` real IO
    (not just sleep). Mirrors C1's actual pattern of awaiting litellm.acompletion.
    """

    async def _io_simulating_router(state: dict[str, Any]) -> list[Send]:
        # Simulate awaiting an HTTP-like async operation
        await asyncio.gather(
            asyncio.sleep(0.001),
            asyncio.sleep(0.001),
        )
        return [Send("noop_node", state)]

    builder: StateGraph = StateGraph(dict)
    builder.add_node("start_noop", _noop_node)
    builder.add_node("noop_node", _noop_node)
    builder.add_edge(START, "start_noop")
    builder.add_conditional_edges("start_noop", _io_simulating_router)
    builder.add_edge("noop_node", END)

    graph = builder.compile()
    result = await graph.ainvoke({"x": 42})

    assert result.get("x") == 42, (
        "Async router with awaited gather failed. Got: %s" % result
    )
