"""Boundary tests for faithfulness_check vacuous-true fix.

Validates Phase 1 of fix-rag-faithfulness-and-add-crag-quality-loop:
the not_applicable contract for `faithfulness_check`.

Three scenarios where the legacy code returned `score=1.0` (vacuous true)
must now return `score=None` (not_applicable):

1. last message role is not assistant -> short-circuit BEFORE LiteLLM call
2. assistant message has empty content
3. claim extraction returns zero claims

Plus an integration check: llm_call_logger.record_faithfulness_score(None)
must early-return so health_monitor stats stay clean.
"""

from unittest import mock as _mock

import pytest

from agentic_rag.faithfulness_check import faithfulness_check


# ───────────────────────────────────────────────────────────────────────────────
# Scenario 1: last_role != "assistant"  ->  no LLM call, return None
# ───────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_returns_none_when_last_role_is_user():
    """User-only conversation history must return not_applicable, not 1.0."""
    state = {
        "messages": [
            {"role": "user", "content": "What is photosynthesis?"},
        ],
        "reranked_results": list(),
    }
    with _mock.patch("agentic_rag.faithfulness_check.LITELLM_AVAILABLE", True):
        with _mock.patch("agentic_rag.faithfulness_check.FAITHFULNESS_ENABLED", True):
            result = await faithfulness_check(state)

    assert result["faithfulness_score"] is None
    assert (
        result["faithfulness_details"]["status"] == "not_applicable_no_assistant_answer"
    )
    assert result["faithfulness_details"]["last_role"] == "user"
    assert result["faithfulness_degraded"] is False


@pytest.mark.asyncio
async def test_does_not_call_litellm_when_last_role_is_user():
    """The short-circuit must skip claim extraction entirely (no token burn)."""
    state = {
        "messages": [
            {"role": "user", "content": "Solve x^2 = 4"},
        ],
        "reranked_results": [{"content": "Math context", "doc_id": "d1", "score": 1.0}],
    }
    with _mock.patch("agentic_rag.faithfulness_check.LITELLM_AVAILABLE", True):
        with _mock.patch("agentic_rag.faithfulness_check.FAITHFULNESS_ENABLED", True):
            with _mock.patch(
                "agentic_rag.faithfulness_check.extract_claims",
                new_callable=_mock.AsyncMock,
            ) as mock_extract:
                with _mock.patch(
                    "agentic_rag.faithfulness_check.verify_claims_nli",
                    new_callable=_mock.AsyncMock,
                ) as mock_verify:
                    result = await faithfulness_check(state)

    assert result["faithfulness_score"] is None
    assert mock_extract.call_count == 0, "extract_claims must not be called"
    assert mock_verify.call_count == 0, "verify_claims_nli must not be called"


@pytest.mark.asyncio
async def test_returns_none_for_langchain_human_message_type():
    """LangChain BaseMessage uses .type='human'/'ai', not .role."""

    class _FakeHumanMessage:
        type = "human"
        content = "Tell me about black holes"

    state = {
        "messages": [_FakeHumanMessage()],
        "reranked_results": list(),
    }
    with _mock.patch("agentic_rag.faithfulness_check.LITELLM_AVAILABLE", True):
        with _mock.patch("agentic_rag.faithfulness_check.FAITHFULNESS_ENABLED", True):
            result = await faithfulness_check(state)

    assert result["faithfulness_score"] is None
    assert result["faithfulness_details"]["last_role"] == "human"


@pytest.mark.asyncio
async def test_accepts_langchain_ai_message_type():
    """LangChain BaseMessage with type='ai' must NOT be short-circuited."""

    class _FakeAIMessage:
        type = "ai"
        content = "Photosynthesis is the process by which plants convert light."

    state = {
        "messages": [_FakeAIMessage()],
        "reranked_results": [
            {
                "content": "Plants use chlorophyll to capture light energy.",
                "doc_id": "d1",
                "score": 1.0,
            }
        ],
    }
    # We expect the function to proceed past the role check;
    # mock extract_claims to return empty so we hit the no_claims path
    # but still verify the ai role was accepted.
    with _mock.patch("agentic_rag.faithfulness_check.LITELLM_AVAILABLE", True):
        with _mock.patch("agentic_rag.faithfulness_check.FAITHFULNESS_ENABLED", True):
            with _mock.patch(
                "agentic_rag.faithfulness_check.extract_claims",
                new_callable=_mock.AsyncMock,
                return_value=[],
            ):
                result = await faithfulness_check(state)

    # Should reach no_claims path, not no_assistant_answer
    assert result["faithfulness_score"] is None
    assert result["faithfulness_details"]["status"] == "not_applicable_no_claims"


# ───────────────────────────────────────────────────────────────────────────────
# Scenario 2: empty/whitespace answer  ->  return None
# ───────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_returns_none_when_answer_empty():
    state = {
        "messages": [{"role": "assistant", "content": ""}],
        "reranked_results": list(),
    }
    with _mock.patch("agentic_rag.faithfulness_check.LITELLM_AVAILABLE", True):
        with _mock.patch("agentic_rag.faithfulness_check.FAITHFULNESS_ENABLED", True):
            result = await faithfulness_check(state)

    assert result["faithfulness_score"] is None
    assert result["faithfulness_details"]["status"] == "not_applicable_no_answer"
    assert result["faithfulness_degraded"] is False


@pytest.mark.asyncio
async def test_returns_none_when_answer_whitespace():
    state = {
        "messages": [{"role": "assistant", "content": "   \n\t  "}],
        "reranked_results": list(),
    }
    with _mock.patch("agentic_rag.faithfulness_check.LITELLM_AVAILABLE", True):
        with _mock.patch("agentic_rag.faithfulness_check.FAITHFULNESS_ENABLED", True):
            result = await faithfulness_check(state)

    assert result["faithfulness_score"] is None
    assert result["faithfulness_details"]["status"] == "not_applicable_no_answer"


# ───────────────────────────────────────────────────────────────────────────────
# Scenario 3: zero claims extracted  ->  return None
# ───────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_returns_none_when_claims_empty():
    """Short numeric answer that yields no extractable claims."""
    state = {
        "messages": [{"role": "assistant", "content": "42"}],
        "reranked_results": [
            {"content": "The meaning of life", "doc_id": "d1", "score": 1.0}
        ],
    }
    with _mock.patch("agentic_rag.faithfulness_check.LITELLM_AVAILABLE", True):
        with _mock.patch("agentic_rag.faithfulness_check.FAITHFULNESS_ENABLED", True):
            with _mock.patch(
                "agentic_rag.faithfulness_check.extract_claims",
                new_callable=_mock.AsyncMock,
                return_value=[],  # Force empty claims
            ):
                result = await faithfulness_check(state)

    assert result["faithfulness_score"] is None
    assert result["faithfulness_details"]["status"] == "not_applicable_no_claims"
    assert result["faithfulness_details"]["total_claims"] == 0
    assert result["faithfulness_degraded"] is False


# ───────────────────────────────────────────────────────────────────────────────
# Scenario 4: logger integration — None must early-return without polluting stats
# ───────────────────────────────────────────────────────────────────────────────


def test_logger_record_faithfulness_score_ignores_none():
    """record_faithfulness_score(None) must not increment _faithfulness_stats."""
    from app.middleware.llm_call_logger import LLMCallLogger

    logger = LLMCallLogger()
    initial_count = logger._faithfulness_stats["count"]
    initial_total = logger._faithfulness_stats["total_score"]

    logger.record_faithfulness_score(None)

    assert logger._faithfulness_stats["count"] == initial_count, (
        "None score must not increment count"
    )
    assert logger._faithfulness_stats["total_score"] == initial_total, (
        "None score must not increment total"
    )


def test_logger_record_faithfulness_score_accepts_valid_score():
    """Sanity: valid scores should still be recorded."""
    from app.middleware.llm_call_logger import LLMCallLogger

    logger = LLMCallLogger()
    initial_count = logger._faithfulness_stats["count"]

    logger.record_faithfulness_score(0.92)

    assert logger._faithfulness_stats["count"] == initial_count + 1
    assert logger._faithfulness_stats["total_score"] >= 0.92
