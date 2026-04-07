"""Unit tests for MemoryService._inject_fsrs_r_values (path B).

Verifies that after fix-concept-id-identity-unification:
  1. Results with valid UUID concept_id and persisted FSRS state get
     boosted relevance_score and a fsrs_r_value field.
  2. Results with no concept_id are silently skipped (cold-start path).
  3. Results with invalid (non-UUID) concept_id are skipped with WARNING.
  4. Results with valid UUID but no card state are silently skipped.
  5. The function emits a structured fsrs_inject_summary log line with
     hit/miss/hit_rate metrics.

[Source: openspec/changes/fix-concept-id-identity-unification/specs/concept-identity/spec.md
 — Requirement "FSRS R-value Injection Uses concept_id Lookup"]
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.memory_service import MemoryService


_VALID_UUID_1 = "f4d10d8b-1234-4abc-89ab-cdef01234567"
_VALID_UUID_2 = "a1b2c3d4-5678-4def-89ab-cdef01234567"
_VALID_UUID_3 = "11111111-2222-4333-8444-555555555555"


def _make_review_service_with_states(states):
    """Build a mock ReviewService whose get_fsrs_state returns the given map.

    states: dict[uuid -> retrievability float] or dict[uuid -> None] for not-found.
    """
    svc = MagicMock()

    async def _get_fsrs_state(concept_id):
        if concept_id not in states:
            return {"found": False, "reason": "not_found"}
        r = states[concept_id]
        if r is None:
            return {"found": False, "reason": "no_card"}
        return {
            "found": True,
            "stability": 1.0,
            "difficulty": 5.0,
            "state": 1,
            "reps": 1,
            "lapses": 0,
            "retrievability": r,
            "due": "2026-01-01",
            "card_state": "{}",
        }

    svc.get_fsrs_state = AsyncMock(side_effect=_get_fsrs_state)
    return svc


@pytest.fixture
def memory_service_with_neo4j_mock():
    neo4j = MagicMock()
    neo4j.stats = {"initialized": False}
    return MemoryService(neo4j_client=neo4j)


class TestAllResultsHaveConceptId:
    """Scenario: All results have valid concept_id with persisted FSRS state."""

    @pytest.mark.asyncio
    async def test_all_hit_boosts_relevance(self, memory_service_with_neo4j_mock):
        results = [
            {"concept_id": _VALID_UUID_1, "relevance_score": 0.5},
            {"concept_id": _VALID_UUID_2, "relevance_score": 0.6},
            {"concept_id": _VALID_UUID_3, "relevance_score": 0.7},
        ]
        # Different R-values to verify formula
        review_svc = _make_review_service_with_states(
            {
                _VALID_UUID_1: 0.5,  # → boost = 1 + 0.5*0.5 = 1.25
                _VALID_UUID_2: 0.0,  # → boost = 1 + 1.0*0.5 = 1.5 (max)
                _VALID_UUID_3: 1.0,  # → boost = 1 + 0.0*0.5 = 1.0 (no change)
            }
        )

        async def _factory():
            return review_svc

        with patch(
            "app.services.review_service.get_review_service",
            new=_factory,
        ):
            await memory_service_with_neo4j_mock._inject_fsrs_r_values(results)

        assert results[0]["fsrs_r_value"] == 0.5
        assert results[0]["relevance_score"] == pytest.approx(0.5 * 1.25)
        assert results[1]["fsrs_r_value"] == 0.0
        assert results[1]["relevance_score"] == pytest.approx(0.6 * 1.5)
        assert results[2]["fsrs_r_value"] == 1.0
        assert results[2]["relevance_score"] == pytest.approx(0.7 * 1.0)


class TestMissingConceptId:
    """Scenario: Result missing concept_id field is silently skipped."""

    @pytest.mark.asyncio
    async def test_missing_concept_id_left_unchanged(
        self, memory_service_with_neo4j_mock
    ):
        results = [
            {"name": "万有引力", "relevance_score": 0.5},  # no concept_id
            {"concept_id": _VALID_UUID_1, "relevance_score": 0.6},
        ]
        review_svc = _make_review_service_with_states({_VALID_UUID_1: 0.3})

        async def _factory():
            return review_svc

        with patch(
            "app.services.review_service.get_review_service",
            new=_factory,
        ):
            await memory_service_with_neo4j_mock._inject_fsrs_r_values(results)

        # First result untouched
        assert "fsrs_r_value" not in results[0]
        assert results[0]["relevance_score"] == 0.5
        # Second result boosted
        assert results[1]["fsrs_r_value"] == 0.3
        assert results[1]["relevance_score"] == pytest.approx(0.6 * (1 + 0.7 * 0.5))


class TestInvalidConceptId:
    """Scenario: Result has invalid concept_id (text instead of UUID)."""

    @pytest.mark.asyncio
    async def test_text_concept_id_skipped_with_warning(
        self, memory_service_with_neo4j_mock, caplog
    ):
        results = [
            {"concept_id": "万有引力", "relevance_score": 0.5},  # text, NOT uuid
            {"concept_id": "legacy-string-id", "relevance_score": 0.6},
        ]
        # review_service should NOT be consulted at all because concept_ids
        # fail validation before lookup
        review_svc = _make_review_service_with_states({})

        async def _factory():
            return review_svc

        with patch(
            "app.services.review_service.get_review_service",
            new=_factory,
        ):
            await memory_service_with_neo4j_mock._inject_fsrs_r_values(results)

        # Both results unchanged
        assert "fsrs_r_value" not in results[0]
        assert "fsrs_r_value" not in results[1]
        # review_service was never called for invalid ids
        review_svc.get_fsrs_state.assert_not_called()


class TestColdStart:
    """Scenario: review_service has no card state for the concept."""

    @pytest.mark.asyncio
    async def test_no_card_state_silent_miss(self, memory_service_with_neo4j_mock):
        results = [
            {"concept_id": _VALID_UUID_1, "relevance_score": 0.5},
        ]
        # UUID is valid but no FSRS state persisted (cold-start)
        review_svc = _make_review_service_with_states({})

        async def _factory():
            return review_svc

        with patch(
            "app.services.review_service.get_review_service",
            new=_factory,
        ):
            await memory_service_with_neo4j_mock._inject_fsrs_r_values(results)

        assert "fsrs_r_value" not in results[0]
        assert results[0]["relevance_score"] == 0.5
        review_svc.get_fsrs_state.assert_called_once_with(_VALID_UUID_1)


class TestSummaryLog:
    """Verify the structured hit/miss/hit_rate summary log line."""

    @pytest.mark.asyncio
    async def test_summary_log_emitted(
        self, memory_service_with_neo4j_mock, capsys
    ):
        results = [
            {"concept_id": _VALID_UUID_1, "relevance_score": 0.5},
            {"concept_id": _VALID_UUID_2, "relevance_score": 0.6},
            {"name": "no-id", "relevance_score": 0.7},
            {"concept_id": "invalid-text", "relevance_score": 0.8},
        ]
        review_svc = _make_review_service_with_states({_VALID_UUID_1: 0.3})

        async def _factory():
            return review_svc

        with patch(
            "app.services.review_service.get_review_service",
            new=_factory,
        ):
            await memory_service_with_neo4j_mock._inject_fsrs_r_values(results)

        captured = capsys.readouterr()
        # The structured log should reflect 1 hit / 3 misses / hit_rate=0.25
        assert "fsrs_inject_summary" in captured.out
        assert "hit" in captured.out
        assert "miss" in captured.out


class TestReviewServiceUnavailable:
    """Graceful degradation when review_service singleton fails to load."""

    @pytest.mark.asyncio
    async def test_factory_failure_skips_silently(
        self, memory_service_with_neo4j_mock
    ):
        results = [
            {"concept_id": _VALID_UUID_1, "relevance_score": 0.5},
        ]

        async def _factory():
            raise RuntimeError("singleton init failed")

        with patch(
            "app.services.review_service.get_review_service",
            new=_factory,
        ):
            # Should not raise, results should be unchanged
            await memory_service_with_neo4j_mock._inject_fsrs_r_values(results)

        assert "fsrs_r_value" not in results[0]
        assert results[0]["relevance_score"] == 0.5
