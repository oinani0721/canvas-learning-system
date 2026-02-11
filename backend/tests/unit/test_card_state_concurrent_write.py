# Canvas Learning System - Concurrent Card State Write Safety Tests
# Story 32.11: AC-32.11.3 并发 card state 写入安全
"""
Tests that concurrent asyncio.create_task calls to record_review_result()
do not corrupt the card states JSON file.

Verifies:
- 10 concurrent calls all succeed without exception
- Card states JSON file remains parseable after concurrent writes
- Final card state reflects eventual consistency

[Source: docs/stories/32.11.story.md - AC-32.11.3]
"""

import asyncio
import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from app.services.review_service import ReviewService


# =============================================================================
# Mock FSRSManager
# =============================================================================

def _make_mock_fsrs_manager():
    """Create a mock FSRSManager that returns realistic FSRS responses.

    The mock supports create_card, deserialize_card, review_card,
    get_due_date, and serialize_card — enough for record_review_result.
    """
    mgr = MagicMock()

    # Mock card object
    mock_card = MagicMock()
    mock_card.stability = 1.0
    mock_card.difficulty = 5.0
    mock_card.state = MagicMock(value=2)
    mock_card.reps = 1
    mock_card.lapses = 0

    mgr.create_card.return_value = mock_card
    mgr.deserialize_card.return_value = mock_card
    mgr.review_card.return_value = (mock_card, MagicMock())
    mgr.get_due_date.return_value = datetime(2026, 2, 13, tzinfo=timezone.utc)
    mgr.serialize_card.return_value = '{"mock": "card_data"}'

    return mgr


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def review_service_with_fsrs(isolate_card_states_file):
    """ReviewService with mock FSRSManager for concurrent write testing."""
    mock_canvas = MagicMock()
    mock_task_mgr = MagicMock()
    mock_fsrs = _make_mock_fsrs_manager()

    service = ReviewService(
        canvas_service=mock_canvas,
        task_manager=mock_task_mgr,
        fsrs_manager=mock_fsrs,
    )
    return service


# =============================================================================
# AC-32.11.3: 并发 card state 写入安全
# =============================================================================

class TestConcurrentCardStateWrite:
    """Verify asyncio.Lock protects _save_card_states from corruption."""

    @pytest.mark.asyncio
    async def test_concurrent_record_review_no_exception(
        self, review_service_with_fsrs
    ):
        """T2.2: 10 concurrent record_review_result calls — all succeed.

        AC-32.11.3: All 10 calls return successfully without exception.
        """
        service = review_service_with_fsrs

        tasks = [
            asyncio.create_task(
                service.record_review_result(
                    canvas_name="concurrent-test",
                    concept_id="concurrent-concept",
                    rating=3,
                )
            )
            for _ in range(10)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        exceptions = [r for r in results if isinstance(r, Exception)]
        assert len(exceptions) == 0, (
            f"Concurrent writes raised {len(exceptions)} exception(s): {exceptions}"
        )
        # All results should be dicts with algorithm key
        for r in results:
            assert isinstance(r, dict), f"Expected dict result, got {type(r)}"
            assert "algorithm" in r

    @pytest.mark.asyncio
    async def test_concurrent_write_json_integrity(
        self, review_service_with_fsrs, isolate_card_states_file
    ):
        """T2.3: After concurrent writes, card states JSON is parseable.

        AC-32.11.3: card states JSON file does not become corrupted.
        """
        service = review_service_with_fsrs
        card_states_file = isolate_card_states_file

        # Write 10 different concepts concurrently
        tasks = [
            asyncio.create_task(
                service.record_review_result(
                    canvas_name="integrity-test",
                    concept_id=f"concept-{i}",
                    rating=(i % 4) + 1,
                )
            )
            for i in range(10)
        ]
        await asyncio.gather(*tasks)

        # Verify JSON file is parseable
        assert card_states_file.exists(), "Card states file should exist after writes"
        raw = card_states_file.read_text(encoding="utf-8")
        parsed = json.loads(raw)
        assert isinstance(parsed, dict), f"Expected dict, got {type(parsed)}"

    @pytest.mark.asyncio
    async def test_concurrent_write_eventual_consistency(
        self, review_service_with_fsrs, isolate_card_states_file
    ):
        """T2.4: Final card state reflects last write (eventual consistency).

        AC-32.11.3: After all concurrent writes complete, the in-memory
        card state for the concept exists and is a valid string.
        """
        service = review_service_with_fsrs

        # 10 concurrent writes to same concept — last writer wins
        tasks = [
            asyncio.create_task(
                service.record_review_result(
                    canvas_name="consistency-test",
                    concept_id="same-concept",
                    rating=(i % 4) + 1,
                )
            )
            for i in range(10)
        ]
        await asyncio.gather(*tasks)

        # Verify the concept has a card state (content determined by last write)
        assert "same-concept" in service._card_states, (
            "Concept should have a card state after concurrent writes"
        )
        state = service._card_states["same-concept"]
        assert isinstance(state, str), f"Card state should be string, got {type(state)}"
        assert len(state) > 0, "Card state should not be empty"
        # M3 Fix: Verify state is a complete, valid JSON (not corrupted by partial writes)
        parsed = json.loads(state)
        assert isinstance(parsed, dict), f"Card state should deserialize to dict, got {type(parsed)}"
