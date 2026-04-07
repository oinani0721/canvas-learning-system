"""
Unit tests for RAGAS Faithfulness Check (Story 7.1)
Tests claim extraction, NLI verification, score calculation, degradation.
"""

from unittest import mock as _mock

import pytest

from agentic_rag.faithfulness_check import (
    ClaimVerdict,
    FaithfulnessResult,
    _parse_json_response,
    apply_degradation,
    calculate_faithfulness,
    faithfulness_check,
)


class TestCalculateFaithfulness:
    def test_all_supported(self):
        verdicts = [
            ClaimVerdict(claim="Earth is round", verdict="SUPPORTED"),
            ClaimVerdict(claim="Water is H2O", verdict="SUPPORTED"),
        ]
        assert calculate_faithfulness(verdicts) == 1.0

    def test_none_supported(self):
        verdicts = [
            ClaimVerdict(claim="Earth is flat", verdict="NOT_SUPPORTED"),
            ClaimVerdict(claim="Sky is green", verdict="NOT_SUPPORTED"),
        ]
        assert calculate_faithfulness(verdicts) == 0.0

    def test_partial_support(self):
        verdicts = [
            ClaimVerdict(claim="A", verdict="SUPPORTED"),
            ClaimVerdict(claim="B", verdict="NOT_SUPPORTED"),
            ClaimVerdict(claim="C", verdict="SUPPORTED"),
            ClaimVerdict(claim="D", verdict="NOT_SUPPORTED"),
        ]
        assert calculate_faithfulness(verdicts) == 0.5

    def test_empty_verdicts(self):
        assert calculate_faithfulness(list()) == 1.0

    def test_high_faithfulness(self):
        verdicts = [
            ClaimVerdict(claim=f"claim_{i}", verdict="SUPPORTED") for i in range(9)
        ] + [ClaimVerdict(claim="claim_9", verdict="NOT_SUPPORTED")]
        assert calculate_faithfulness(verdicts) == 0.9


class TestApplyDegradation:
    def test_high_score_no_degradation(self):
        result = FaithfulnessResult(score=0.9, total_claims=10, supported_claims=9)
        result = apply_degradation(0.9, result)
        assert not result.degraded

    def test_threshold_exact_no_degradation(self):
        result = FaithfulnessResult(score=0.85, total_claims=20, supported_claims=17)
        result = apply_degradation(0.85, result)
        assert not result.degraded

    def test_low_confidence_degradation(self):
        result = FaithfulnessResult(score=0.6, total_claims=10, supported_claims=6)
        result = apply_degradation(0.6, result)
        assert result.degraded
        assert "may not fully support" in result.degradation_reason

    def test_full_degradation(self):
        result = FaithfulnessResult(score=0.3, total_claims=10, supported_claims=3)
        result = apply_degradation(0.3, result)
        assert result.degraded
        assert "insufficient" in result.degradation_reason


class TestParseJsonResponse:
    def test_plain_json(self):
        result = _parse_json_response('{"claims": ["a", "b"]}')
        assert result == {"claims": ["a", "b"]}

    def test_json_with_markdown_fence(self):
        text = '```json\n{"claims": ["a"]}\n```'
        result = _parse_json_response(text)
        assert result == {"claims": ["a"]}


class TestFaithfulnessCheckNode:
    @pytest.mark.asyncio
    async def test_disabled_returns_none_score(self):
        with _mock.patch("agentic_rag.faithfulness_check.FAITHFULNESS_ENABLED", False):
            result = await faithfulness_check(
                {"messages": list(), "reranked_results": list()}
            )
            assert result["faithfulness_score"] is None
            assert result["faithfulness_degraded"] is False

    @pytest.mark.asyncio
    async def test_empty_answer_returns_not_applicable(self):
        """Vacuous-true fix: empty assistant answer returns None, not 1.0."""
        state = {
            "messages": [{"role": "assistant", "content": ""}],
            "reranked_results": list(),
        }
        with _mock.patch("agentic_rag.faithfulness_check.LITELLM_AVAILABLE", True):
            with _mock.patch(
                "agentic_rag.faithfulness_check.FAITHFULNESS_ENABLED", True
            ):
                result = await faithfulness_check(state)
                assert result["faithfulness_score"] is None
                assert (
                    result["faithfulness_details"]["status"]
                    == "not_applicable_no_answer"
                )
                assert result["faithfulness_degraded"] is False

    @pytest.mark.asyncio
    async def test_no_context_triggers_degradation(self):
        state = {
            "messages": [{"role": "assistant", "content": "The answer is 42."}],
            "reranked_results": list(),
        }
        with _mock.patch("agentic_rag.faithfulness_check.LITELLM_AVAILABLE", True):
            with _mock.patch(
                "agentic_rag.faithfulness_check.FAITHFULNESS_ENABLED", True
            ):
                result = await faithfulness_check(state)
                assert result["faithfulness_score"] == 0.0
                assert result["faithfulness_degraded"] is True
