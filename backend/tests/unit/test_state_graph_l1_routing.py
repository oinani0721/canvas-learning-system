"""
Integration tests for fan_out_retrieval with L1 LLM routing.

Verifies the state_graph.fan_out_retrieval conditional edge correctly picks
retrieval channels based on the configured l1_router_strategy:
    - "hybrid": LLM first, fall back to rule on failure
    - "llm":    LLM only, fall back to "comprehensive" on failure
    - "rule":   legacy keyword matcher only

Also covers:
    - multi_queries variants share a single L1 routing decision
    - Each retrieval channel intent maps to the correct Send list

These are the first conditional-edge unit tests in the project. The project
previously had zero coverage of fan_out_retrieval routing because the old
rule-based version was trivial keyword matching. Now that it can call an
LLM, we need to pin behavior against future regressions.

[OpenSpec change: agentic-rag-l1-llm-router]
[Phase 4 of plan: C1-D Integration Tests]
"""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from agentic_rag.llm_router import LLMRouterResult
from agentic_rag.state_graph import fan_out_retrieval


# ============================================================================
# Helpers
# ============================================================================


def _state_with_query(
    query: str, multi_queries: list[str] | None = None
) -> dict[str, Any]:
    """Build a minimal CanvasRAGState-compatible dict for testing."""
    return {
        "messages": [{"role": "user", "content": query}],
        "multi_queries": multi_queries,
    }


def _extract_destinations(sends: list[Any]) -> list[str]:
    """Pull node names out of LangGraph Send objects."""
    return [s.node for s in sends]


# ============================================================================
# Phase 1: hybrid strategy — LLM succeeds
# ============================================================================


class TestFanOutHybridLLMSuccess:
    """l1_router_strategy=hybrid, LLM classifies successfully."""

    @pytest.mark.asyncio
    async def test_knowledge_point_activates_all_5_routes(self):
        """LLM returns knowledge_point → all 5 retrievers activated."""
        fake_result = LLMRouterResult(
            intent="knowledge_point",
            reason="concept question",
            latency_ms=50.0,
            success=True,
            error=None,
        )

        # state_graph imports llm_route lazily inside _classify_intent_with_strategy,
        # so we patch the source module (agentic_rag.llm_router).
        with patch(
            "agentic_rag.llm_router.llm_route",
            new=AsyncMock(return_value=fake_result),
        ):
            state = _state_with_query("牛顿第二定律的公式是什么？")
            sends = await fan_out_retrieval(state)

        dests = _extract_destinations(sends)
        assert "retrieve_graphiti" in dests
        assert "retrieve_lancedb" in dests
        assert "retrieve_multimodal" in dests
        assert "retrieve_cross_canvas" in dests
        assert "retrieve_vault_notes" in dests
        assert len(dests) == 5

    @pytest.mark.asyncio
    async def test_file_locate_skips_graphiti_and_multimodal(self):
        """LLM returns file_locate → only vault/lancedb/cross_canvas."""
        fake_result = LLMRouterResult(
            intent="file_locate",
            reason="locator query",
            latency_ms=40.0,
            success=True,
            error=None,
        )
        with patch(
            "agentic_rag.llm_router.llm_route",
            new=AsyncMock(return_value=fake_result),
        ):
            state = _state_with_query("我的物理笔记在哪？")
            sends = await fan_out_retrieval(state)

        dests = _extract_destinations(sends)
        assert "retrieve_lancedb" in dests
        assert "retrieve_vault_notes" in dests
        assert "retrieve_cross_canvas" in dests
        # These should NOT be activated for file_locate
        assert "retrieve_graphiti" not in dests
        assert "retrieve_multimodal" not in dests

    @pytest.mark.asyncio
    async def test_learning_history_routes_to_graphiti_priority(self):
        """LLM returns learning_history → graphiti + lancedb + vault_notes."""
        fake_result = LLMRouterResult(
            intent="learning_history",
            reason="review query",
            latency_ms=45.0,
            success=True,
            error=None,
        )
        with patch(
            "agentic_rag.llm_router.llm_route",
            new=AsyncMock(return_value=fake_result),
        ):
            state = _state_with_query("我上周学了什么？")
            sends = await fan_out_retrieval(state)

        dests = _extract_destinations(sends)
        assert "retrieve_graphiti" in dests
        assert "retrieve_lancedb" in dests
        assert "retrieve_vault_notes" in dests


# ============================================================================
# Phase 2: hybrid strategy — LLM fails, rule fallback
# ============================================================================


class TestFanOutHybridLLMFallback:
    """LLM fails for various reasons; rule-based classifier takes over."""

    @pytest.mark.asyncio
    async def test_llm_timeout_falls_back_to_rule(self):
        """LLM times out → rule-based classify_query_intent handles it."""
        fake_result = LLMRouterResult(
            intent="comprehensive",  # llm_route's safe default on fallback
            reason="",
            latency_ms=3000.0,
            success=False,
            error="timeout",
        )
        with patch(
            "agentic_rag.llm_router.llm_route",
            new=AsyncMock(return_value=fake_result),
        ):
            # This query contains "笔记" which the rule classifier maps to file_locate
            state = _state_with_query("我的物理笔记在哪？")
            sends = await fan_out_retrieval(state)

        dests = _extract_destinations(sends)
        # Rule classifier should have run and returned file_locate → no graphiti
        assert "retrieve_graphiti" not in dests
        assert "retrieve_vault_notes" in dests

    @pytest.mark.asyncio
    async def test_llm_exception_falls_back_to_rule(self):
        """llm_route raises unexpectedly → rule-based classifier takes over."""

        async def raise_runtime(*args, **kwargs):
            raise RuntimeError("unexpected network error")

        with patch(
            "agentic_rag.llm_router.llm_route",
            new=raise_runtime,
        ):
            state = _state_with_query("我之前学过什么？")  # rule → learning_history
            sends = await fan_out_retrieval(state)

        dests = _extract_destinations(sends)
        # learning_history rule → graphiti + lancedb + vault_notes
        assert "retrieve_graphiti" in dests
        assert "retrieve_lancedb" in dests
        assert "retrieve_multimodal" not in dests


# ============================================================================
# Phase 3: rule strategy — explicit rollback
# ============================================================================


class TestFanOutRuleStrategy:
    """l1_router_strategy=rule → LLM is never called, rule classifier only."""

    @pytest.mark.asyncio
    async def test_rule_strategy_skips_llm_call(self):
        """With strategy=rule, llm_route should NOT be invoked at all."""
        mock_llm = AsyncMock()

        with patch.dict(
            "agentic_rag.config.DEFAULT_CONFIG",
            {"l1_router_strategy": "rule"},
        ):
            with patch(
                "agentic_rag.llm_router.llm_route",
                new=mock_llm,
            ):
                state = _state_with_query("什么是相对论？")
                await fan_out_retrieval(state)

        # LLM must never have been called
        assert mock_llm.call_count == 0


# ============================================================================
# Phase 4: multi_queries sharing single routing decision
# ============================================================================


class TestFanOutMultiQuerySharedRouting:
    """
    Verify the pre-existing behavior: multi_queries variants all share ONE
    L1 routing decision (made on the original query). The LLM refactor must
    not change this.
    """

    @pytest.mark.asyncio
    async def test_multi_queries_share_single_llm_call(self):
        """LLM called once for the original query, not once per variant."""
        call_count = {"n": 0}

        async def counting_llm(query: str, **kwargs):
            call_count["n"] += 1
            return LLMRouterResult(
                intent="knowledge_point",
                reason="",
                latency_ms=10.0,
                success=True,
                error=None,
            )

        with patch(
            "agentic_rag.llm_router.llm_route",
            new=counting_llm,
        ):
            state = _state_with_query(
                "原始查询",
                multi_queries=["变体1", "变体2", "变体3"],
            )
            sends = await fan_out_retrieval(state)

        # LLM called exactly once (on the original query)
        assert call_count["n"] == 1, (
            "LLM called %d times, expected 1 — multi_query should NOT trigger "
            "one LLM call per variant (would be O(k) cost)" % call_count["n"]
        )

        # 3 variants × 5 channels (knowledge_point intent) = 15 sends
        dests = _extract_destinations(sends)
        assert len(dests) == 15, (
            "Got %d sends, expected 15 (3 variants × 5 channels)" % len(dests)
        )


# ============================================================================
# Phase 5: graph compiles and async conditional edge works end-to-end
# ============================================================================


class TestFanOutGraphCompile:
    """End-to-end sanity: the full RAG graph compiles with the async fan_out."""

    def test_graph_compiles_with_async_fan_out(self):
        """
        The full Canvas Agentic RAG graph must compile even though
        fan_out_retrieval is now async. If LangGraph 1.x somehow breaks
        on async conditional edges, this catches it.
        """
        from agentic_rag.state_graph import build_canvas_agentic_rag_graph

        graph = build_canvas_agentic_rag_graph()
        assert graph is not None
        # The graph has a .compile() method — if it got this far, Send setup worked
        compiled = graph.compile()
        assert compiled is not None
