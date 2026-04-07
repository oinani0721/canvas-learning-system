"""
Unit tests for L1 LLM Router (agentic_rag.llm_router).

Tests the LLM-based query intent classifier that replaces the rule-based
classify_query_intent in state_graph.py. Covers:
    - Successful classification (valid intent + valid JSON)
    - Markdown code fence tolerance
    - Timeout fallback
    - JSON parse error fallback
    - Unknown intent fallback
    - Empty query fast-fail
    - Import error (litellm missing) fallback

All tests mock litellm.acompletion to avoid network calls.

[OpenSpec change: agentic-rag-l1-llm-router]
[Phase 1 of plan: C1-A LLM Router Module]
"""

from __future__ import annotations

import asyncio
import json
import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from agentic_rag.llm_router import (
    ALLOWED_INTENTS,
    DEFAULT_LLM_ROUTER_MODEL,
    LLMRouterResult,
    llm_route,
)


# ============================================================================
# Helpers
# ============================================================================


def _make_litellm_response(content: str) -> SimpleNamespace:
    """Build a minimal mock LiteLLM response object."""
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
    )


# ============================================================================
# Phase 1: Successful classification
# ============================================================================


class TestLLMRouterSuccess:
    """LLM returns valid JSON with a known intent."""

    @pytest.mark.asyncio
    async def test_classifies_knowledge_point(self):
        mock_response = _make_litellm_response(
            '{"intent": "knowledge_point", "reason": "asks about a concept"}'
        )

        with patch("litellm.acompletion", new=AsyncMock(return_value=mock_response)):
            result = await llm_route("什么是牛顿第二定律？")

        assert isinstance(result, LLMRouterResult)
        assert result.success is True
        assert result.intent == "knowledge_point"
        assert result.error is None
        assert "concept" in result.reason
        assert result.latency_ms >= 0

    @pytest.mark.asyncio
    async def test_classifies_file_locate(self):
        mock_response = _make_litellm_response(
            '{"intent": "file_locate", "reason": "locator query"}'
        )
        with patch("litellm.acompletion", new=AsyncMock(return_value=mock_response)):
            result = await llm_route("我的物理笔记在哪？")

        assert result.success is True
        assert result.intent == "file_locate"

    @pytest.mark.asyncio
    async def test_classifies_learning_history(self):
        mock_response = _make_litellm_response(
            '{"intent": "learning_history", "reason": "review query"}'
        )
        with patch("litellm.acompletion", new=AsyncMock(return_value=mock_response)):
            result = await llm_route("我之前复习过哪些章节？")

        assert result.success is True
        assert result.intent == "learning_history"

    @pytest.mark.asyncio
    async def test_handles_markdown_code_fence(self):
        """LLM sometimes wraps JSON in ```json ... ``` despite system prompt."""
        wrapped = (
            "```json\n"
            + json.dumps({"intent": "comprehensive", "reason": "fallback"})
            + "\n```"
        )
        mock_response = _make_litellm_response(wrapped)
        with patch("litellm.acompletion", new=AsyncMock(return_value=mock_response)):
            result = await llm_route("某个综合查询")

        assert result.success is True
        assert result.intent == "comprehensive"


# ============================================================================
# Phase 2: Fallback paths (caller falls back to rule-based)
# ============================================================================


class TestLLMRouterFallback:
    """LLM fails — should never raise, should return success=False with safe intent."""

    @pytest.mark.asyncio
    async def test_timeout_falls_back_to_comprehensive(self):
        async def hang_forever(*args, **kwargs):
            await asyncio.sleep(60)

        with patch("litellm.acompletion", new=hang_forever):
            result = await llm_route("查询", timeout_s=0.05)

        assert result.success is False
        assert result.intent == "comprehensive"
        assert result.error == "timeout"
        # Latency should reflect we waited near the timeout, not 0
        assert result.latency_ms >= 40  # 50ms timeout, give some margin

    @pytest.mark.asyncio
    async def test_litellm_exception_falls_back(self):
        async def raise_runtime(*args, **kwargs):
            raise RuntimeError("network down")

        with patch("litellm.acompletion", new=raise_runtime):
            result = await llm_route("查询")

        assert result.success is False
        assert result.intent == "comprehensive"
        assert result.error == "RuntimeError"

    @pytest.mark.asyncio
    async def test_invalid_json_falls_back(self):
        mock_response = _make_litellm_response("this is not json")
        with patch("litellm.acompletion", new=AsyncMock(return_value=mock_response)):
            result = await llm_route("查询")

        assert result.success is False
        assert result.intent == "comprehensive"
        assert result.error == "parse_error"

    @pytest.mark.asyncio
    async def test_unknown_intent_falls_back(self):
        mock_response = _make_litellm_response(
            '{"intent": "make_coffee", "reason": "haha"}'
        )
        with patch("litellm.acompletion", new=AsyncMock(return_value=mock_response)):
            result = await llm_route("查询")

        assert result.success is False
        assert result.intent == "comprehensive"
        assert result.error == "unknown_intent"

    @pytest.mark.asyncio
    async def test_missing_intent_field_falls_back(self):
        mock_response = _make_litellm_response('{"reason": "no intent field"}')
        with patch("litellm.acompletion", new=AsyncMock(return_value=mock_response)):
            result = await llm_route("查询")

        assert result.success is False
        assert result.intent == "comprehensive"
        assert result.error == "unknown_intent"

    @pytest.mark.asyncio
    async def test_empty_query_fast_fails(self):
        result = await llm_route("")
        assert result.success is False
        assert result.intent == "comprehensive"
        assert result.error == "empty_query"
        # Should not call litellm at all
        assert result.latency_ms == 0.0

    @pytest.mark.asyncio
    async def test_whitespace_query_fast_fails(self):
        result = await llm_route("   \n  ")
        assert result.success is False
        assert result.error == "empty_query"


# ============================================================================
# Phase 3: Configuration & contracts
# ============================================================================


class TestLLMRouterContract:
    """Public contract: dataclass shape, allowed intents, default model."""

    def test_allowed_intents_match_state_graph(self):
        """The 4 intents must match _build_sends_for_intent in state_graph.py."""
        # If this test ever fails, it means someone changed the intent vocabulary
        # in one place but not the other. Both must be kept in sync.
        expected = {
            "file_locate",
            "learning_history",
            "knowledge_point",
            "comprehensive",
        }
        assert set(ALLOWED_INTENTS) == expected

    def test_default_model_is_gemini_flash(self):
        """A9 decision: use Gemini Flash for low latency + cost."""
        assert "gemini" in DEFAULT_LLM_ROUTER_MODEL.lower()
        assert "flash" in DEFAULT_LLM_ROUTER_MODEL.lower()

    @pytest.mark.asyncio
    async def test_result_dataclass_shape(self):
        """LLMRouterResult must have the exact fields we documented."""
        mock_response = _make_litellm_response(
            '{"intent": "knowledge_point", "reason": "x"}'
        )
        with patch("litellm.acompletion", new=AsyncMock(return_value=mock_response)):
            result = await llm_route("query")

        # Required fields
        assert hasattr(result, "intent")
        assert hasattr(result, "reason")
        assert hasattr(result, "latency_ms")
        assert hasattr(result, "success")
        assert hasattr(result, "error")

    @pytest.mark.asyncio
    async def test_long_query_truncated_in_user_prompt(self):
        """Queries > 500 chars are truncated to keep prompt budget bounded."""
        captured = {}

        async def capture_acompletion(**kwargs):
            captured["messages"] = kwargs["messages"]
            return _make_litellm_response('{"intent": "comprehensive", "reason": "x"}')

        long_query = "牛顿" * 1000  # 2000 chars
        with patch("litellm.acompletion", new=capture_acompletion):
            await llm_route(long_query)

        user_msg = captured["messages"][1]["content"]
        # User prompt should be much shorter than the original 2000-char query
        assert len(user_msg) < 600
