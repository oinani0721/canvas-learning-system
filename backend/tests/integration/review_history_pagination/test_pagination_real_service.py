# Story 34.11: Real ReviewService integration tests (no mocking ReviewService)
"""
Tests using a real ReviewService instance to validate sorting, filtering,
pagination, and limiting logic.

Split from test_review_history_pagination.py (1234 lines → ≤300 lines).

Covers:
- Story 34.8 AC1: Real service pagination and sorting
- Story 34.8 AC3: show_all hard cap (MAX_HISTORY_RECORDS=1000)
"""

from datetime import datetime, date, timedelta
from unittest.mock import patch

import pytest

from app.services.review_service import MAX_HISTORY_RECORDS

from .conftest import (
    make_real_review_service,
    build_card_states_for_history,
)


# ── Shared fixture for all real-service tests in this module ─────────────────

@pytest.fixture(autouse=True)
def _patch_service_datetime():
    """Patch datetime.now() in review_service to match fixed test dates."""
    _fixed_now = datetime(2025, 6, 15, 23, 59, 0)
    with patch("app.services.review_service.datetime") as mock_dt:
        mock_dt.now.return_value = _fixed_now
        mock_dt.fromisoformat = datetime.fromisoformat
        yield


# ── Real service pagination tests ────────────────────────────────────────────

@pytest.mark.asyncio
class TestRealReviewServiceHistory:
    """Story 34.8 AC1: Real integration tests using actual ReviewService instance.

    Uses fixed dates (2025-06-15) for determinism.
    """

    async def test_default_limit_returns_max_5_records(self):
        """AC1: Default limit=5 returns at most 5 individual review records."""
        card_states = build_card_states_for_history(10, "math")
        service = make_real_review_service(card_states)

        result = await service.get_history(days=7, limit=5)

        total_reviews = sum(len(day["reviews"]) for day in result["records"])
        assert total_reviews <= 5
        assert result["has_more"] is True
        assert result["total_count"] == 10

    async def test_show_all_returns_all_records_within_cap(self):
        """AC1+AC3: Large limit returns all records when count < limit."""
        card_states = build_card_states_for_history(8, "physics")
        service = make_real_review_service(card_states)

        result = await service.get_history(days=7, limit=MAX_HISTORY_RECORDS)

        total_reviews = sum(len(day["reviews"]) for day in result["records"])
        assert total_reviews == 8
        assert result["has_more"] is False

    async def test_limit_parameter_slices_correctly(self):
        """AC1: Custom limit slices records correctly."""
        card_states = build_card_states_for_history(12, "chem")
        service = make_real_review_service(card_states)

        result = await service.get_history(days=7, limit=3)

        total_reviews = sum(len(day["reviews"]) for day in result["records"])
        assert total_reviews <= 3
        assert result["has_more"] is True
        assert result["total_count"] == 12

    async def test_records_sorted_by_time_descending(self):
        """AC1: Records are sorted by review_time descending (newest first)."""
        card_states = build_card_states_for_history(6, "bio")
        service = make_real_review_service(card_states)

        result = await service.get_history(days=7, limit=MAX_HISTORY_RECORDS)

        all_times = []
        for day_record in result["records"]:
            for review in day_record["reviews"]:
                all_times.append(review["review_time"])

        for i in range(len(all_times) - 1):
            assert all_times[i] >= all_times[i + 1], (
                f"Records not sorted descending: {all_times[i]} < {all_times[i + 1]}"
            )

    async def test_filter_by_canvas_path(self):
        """AC1: canvas_path filter works with real service."""
        states = {}
        fixed = date(2025, 6, 15)
        for i in range(3):
            states[f"math.canvas:concept_{i}"] = {
                "last_review": datetime(
                    fixed.year, fixed.month, fixed.day, 10, 0, 0
                ).isoformat(),
                "rating": 3,
            }
        for i in range(2):
            states[f"physics.canvas:concept_{i}"] = {
                "last_review": datetime(
                    fixed.year, fixed.month, fixed.day, 11, 0, 0
                ).isoformat(),
                "rating": 4,
            }

        service = make_real_review_service(states)
        result = await service.get_history(
            days=7, canvas_path="math", limit=MAX_HISTORY_RECORDS
        )

        total_reviews = sum(len(d["reviews"]) for d in result["records"])
        assert total_reviews == 3

    async def test_filter_by_concept_name(self):
        """AC1: concept_name filter works with real service."""
        states = {}
        fixed = date(2025, 6, 15)
        states["math.canvas:逆否命题"] = {
            "last_review": datetime(
                fixed.year, fixed.month, fixed.day, 10, 0, 0
            ).isoformat(),
            "rating": 4,
        }
        states["math.canvas:充分条件"] = {
            "last_review": datetime(
                fixed.year, fixed.month, fixed.day, 11, 0, 0
            ).isoformat(),
            "rating": 3,
        }

        service = make_real_review_service(states)
        result = await service.get_history(
            days=7, concept_name="逆否命题", limit=MAX_HISTORY_RECORDS
        )

        total_reviews = sum(len(d["reviews"]) for d in result["records"])
        assert total_reviews == 1

    async def test_streak_days_calculation(self):
        """AC1: Streak days are calculated from consecutive review days."""
        states = {}
        fixed = date(2025, 6, 15)
        for day_offset in [0, 1]:
            review_date = fixed - timedelta(days=day_offset)
            states[f"math.canvas:concept_{day_offset}"] = {
                "last_review": datetime(
                    review_date.year, review_date.month, review_date.day, 10, 0, 0
                ).isoformat(),
                "rating": 3,
            }

        service = make_real_review_service(states)
        result = await service.get_history(days=7, limit=MAX_HISTORY_RECORDS)

        assert result["streak_days"] == 2


# ── Hard cap tests ───────────────────────────────────────────────────────────

class TestShowAllHardCap:
    """Story 34.8 AC3: Verify show_all=True uses MAX_HISTORY_RECORDS cap."""

    def test_max_history_records_constant_exists(self):
        """AC3: MAX_HISTORY_RECORDS constant must be defined."""
        assert MAX_HISTORY_RECORDS == 1000

    def test_show_all_uses_max_cap_in_endpoint(self):
        """AC3: show_all=True in endpoint must use MAX_HISTORY_RECORDS, not None."""
        from pathlib import Path
        review_path = (
            Path(__file__).resolve().parents[3]
            / "app" / "api" / "v1" / "endpoints" / "review.py"
        )
        source = review_path.read_text(encoding="utf-8")

        assert "effective_limit = None if show_all" not in source, (
            "show_all=True still uses effective_limit=None — must use MAX_HISTORY_RECORDS"
        )
        assert "MAX_HISTORY_RECORDS" in source, (
            "review.py endpoint does not reference MAX_HISTORY_RECORDS"
        )

    @pytest.mark.asyncio
    async def test_show_all_truncates_above_cap(self):
        """AC3: When records > limit, truncate and set has_more=True."""
        card_states = build_card_states_for_history(15, "large")
        service = make_real_review_service(card_states)

        result = await service.get_history(days=7, limit=8)

        total_reviews = sum(len(d["reviews"]) for d in result["records"])
        assert total_reviews <= 8
        assert result["has_more"] is True
        assert result["total_count"] == 15

    @pytest.mark.asyncio
    async def test_show_all_no_truncation_below_cap(self):
        """AC3: When records < MAX_HISTORY_RECORDS, return all with has_more=False."""
        card_states = build_card_states_for_history(5, "small")
        service = make_real_review_service(card_states)

        result = await service.get_history(days=7, limit=MAX_HISTORY_RECORDS)

        total_reviews = sum(len(d["reviews"]) for d in result["records"])
        assert total_reviews == 5
        assert result["has_more"] is False
