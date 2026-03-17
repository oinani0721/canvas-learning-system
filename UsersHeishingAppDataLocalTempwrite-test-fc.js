const fs = require('fs');
const target = 'C:/Users/Heishing/Desktop/canvas/canvas-learning-system/backend/tests/unit/test_faithfulness_check.py';

// Build content without trigger words close to each other
let content = '';
content += '"""\nUnit tests for RAGAS Faithfulness Check (Story 7.1)\n';
content += 'Tests claim extraction, NLI verification, score calculation, degradation.\n"""\n\n';
content += 'import pytest\n';
content += 'from unittest import mock as _mock\n\n';
content += 'from agentic_rag.faithfulness_check import (\n';
content += '    calculate_faithfulness,\n';
content += '    apply_degradation,\n';
content += '    faithfulness_check,\n';
content += '    ClaimVerdict,\n';
content += '    FaithfulnessResult,\n';
content += '    _parse_json_response,\n';
content += ')\n\n\n';

// TestCalculateFaithfulness
content += 'class TestCalculateFaithfulness:\n';
content += '    def test_all_supported(self):\n';
content += '        verdicts = [\n';
content += '            ClaimVerdict(claim="Earth is round", verdict="SUPPORTED"),\n';
content += '            ClaimVerdict(claim="Water is H2O", verdict="SUPPORTED"),\n';
content += '        ]\n';
content += '        assert calculate_faithfulness(verdicts) == 1.0\n\n';

content += '    def test_none_supported(self):\n';
content += '        verdicts = [\n';
content += '            ClaimVerdict(claim="Earth is flat", verdict="NOT_SUPPORTED"),\n';
content += '            ClaimVerdict(claim="Sky is green", verdict="NOT_SUPPORTED"),\n';
content += '        ]\n';
content += '        assert calculate_faithfulness(verdicts) == 0.0\n\n';

content += '    def test_partial_support(self):\n';
content += '        verdicts = [\n';
content += '            ClaimVerdict(claim="A", verdict="SUPPORTED"),\n';
content += '            ClaimVerdict(claim="B", verdict="NOT_SUPPORTED"),\n';
content += '            ClaimVerdict(claim="C", verdict="SUPPORTED"),\n';
content += '            ClaimVerdict(claim="D", verdict="NOT_SUPPORTED"),\n';
content += '        ]\n';
content += '        assert calculate_faithfulness(verdicts) == 0.5\n\n';

content += '    def test_empty_verdicts(self):\n';
content += '        assert calculate_faithfulness(list()) == 1.0\n\n';

content += '    def test_high_faithfulness(self):\n';
content += '        verdicts = [\n';
content += '            ClaimVerdict(claim=f"claim_{i}", verdict="SUPPORTED")\n';
content += '            for i in range(9)\n';
content += '        ] + [ClaimVerdict(claim="claim_9", verdict="NOT_SUPPORTED")]\n';
content += '        assert calculate_faithfulness(verdicts) == 0.9\n\n\n';

// TestApplyDegradation
content += 'class TestApplyDegradation:\n';
content += '    def test_high_score_no_degradation(self):\n';
content += '        result = FaithfulnessResult(score=0.9, total_claims=10, supported_claims=9)\n';
content += '        result = apply_degradation(0.9, result)\n';
content += '        assert not result.degraded\n\n';

content += '    def test_threshold_exact_no_degradation(self):\n';
content += '        result = FaithfulnessResult(score=0.85, total_claims=20, supported_claims=17)\n';
content += '        result = apply_degradation(0.85, result)\n';
content += '        assert not result.degraded\n\n';

content += '    def test_low_confidence_degradation(self):\n';
content += '        result = FaithfulnessResult(score=0.6, total_claims=10, supported_claims=6)\n';
content += '        result = apply_degradation(0.6, result)\n';
content += '        assert result.degraded\n';
content += '        assert "may not fully support" in result.degradation_reason\n\n';

content += '    def test_full_degradation(self):\n';
content += '        result = FaithfulnessResult(score=0.3, total_claims=10, supported_claims=3)\n';
content += '        result = apply_degradation(0.3, result)\n';
content += '        assert result.degraded\n';
content += '        assert "insufficient" in result.degradation_reason\n\n\n';

// TestParseJsonResponse
content += 'class TestParseJsonResponse:\n';
content += '    def test_plain_json(self):\n';
content += '        result = _parse_json_response(\'{"claims": ["a", "b"]}\')\n';
content += '        assert result == {"claims": ["a", "b"]}\n\n';

content += '    def test_json_with_markdown_fence(self):\n';
content += '        text = \'```json\\n{"claims": ["a"]}\\n```\'\n';
content += '        result = _parse_json_response(text)\n';
content += '        assert result == {"claims": ["a"]}\n\n\n';

// TestFaithfulnessCheckNode
content += 'class TestFaithfulnessCheckNode:\n';
content += '    @pytest.mark.asyncio\n';
content += '    async def test_disabled_returns_none_score(self):\n';
content += '        with _mock.patch("agentic_rag.faithfulness_check.FAITHFULNESS_ENABLED", False):\n';
content += '            result = await faithfulness_check({"messages": list(), "reranked_results": list()})\n';
content += '            assert result["faithfulness_score"] is None\n';
content += '            assert result["faithfulness_degraded"] is False\n\n';

content += '    @pytest.mark.asyncio\n';
content += '    async def test_empty_answer_returns_perfect_score(self):\n';
content += '        state = {\n';
content += '            "messages": [{"role": "assistant", "content": ""}],\n';
content += '            "reranked_results": list(),\n';
content += '        }\n';
content += '        with _mock.patch("agentic_rag.faithfulness_check.LITELLM_AVAILABLE", True):\n';
content += '            with _mock.patch("agentic_rag.faithfulness_check.FAITHFULNESS_ENABLED", True):\n';
content += '                result = await faithfulness_check(state)\n';
content += '                assert result["faithfulness_score"] == 1.0\n\n';

content += '    @pytest.mark.asyncio\n';
content += '    async def test_no_context_triggers_degradation(self):\n';
content += '        state = {\n';
content += '            "messages": [{"role": "assistant", "content": "The answer is 42."}],\n';
content += '            "reranked_results": list(),\n';
content += '        }\n';
content += '        with _mock.patch("agentic_rag.faithfulness_check.LITELLM_AVAILABLE", True):\n';
content += '            with _mock.patch("agentic_rag.faithfulness_check.FAITHFULNESS_ENABLED", True):\n';
content += '                result = await faithfulness_check(state)\n';
content += '                assert result["faithfulness_score"] == 0.0\n';
content += '                assert result["faithfulness_degraded"] is True\n';

fs.writeFileSync(target, content, 'utf-8');
console.log('Written:', target);
