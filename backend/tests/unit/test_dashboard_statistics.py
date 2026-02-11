# Story 32.4: Dashboard Statistics — Service-Level Tests
"""
Tests for the dashboard statistics calculations in ReviewService.get_history().

Covers:
- AC-32.4.1: review_count (total_count) per concept accuracy
- AC-32.4.2: streak_days consecutive review day calculation
- AC-32.4.3: History data sourced from _card_states (persistence proxy)
- AC-32.4.4: Statistics grouping by date (week/month trends)

These tests exercise the REAL ReviewService.get_history() business logic
(not mocked), with only infrastructure dependencies (CanvasService, TaskManager)
stubbed out.
"""

import pytest
from datetime import datetime, date, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.review_service import ReviewService


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_service(card_states: dict = None) -> ReviewService:
    """Create ReviewService with mock infrastructure, real business logic."""
    from app.services.background_task_manager import BackgroundTaskManager

    mock_canvas = MagicMock()
    mock_canvas.cleanup = AsyncMock()
    task_mgr = BackgroundTaskManager()

    svc = ReviewService(
        canvas_service=mock_canvas,
        task_manager=task_mgr,
        graphiti_client=None,
        fsrs_manager=None,
    )
    if card_states is not None:
        svc._card_states = card_states
    return svc


def _card(last_review: str, rating: int = 3) -> dict:
    """Shorthand for a card state entry."""
    return {"last_review": last_review, "rating": rating}


def _today() -> date:
    return datetime.now(timezone.utc).date()


# ── AC-32.4.2: streak_days calculation ───────────────────────────────────────

class TestStreakDaysCalculation:
    """Verify consecutive-day streak algorithm in get_history()."""

    @pytest.mark.asyncio
    async def test_streak_zero_when_no_reviews(self):
        """streak_days=0 when there are no review records."""
        svc = _make_service(card_states={})
        result = await svc.get_history(days=7, limit=None)
        assert result["streak_days"] == 0

    @pytest.mark.asyncio
    async def test_streak_one_day_today_only(self):
        """streak_days=1 when only today has reviews."""
        today = _today()
        states = {
            "math.canvas:concept_a": _card(
                datetime(today.year, today.month, today.day, 10, 0, 0).isoformat()
            ),
        }
        svc = _make_service(card_states=states)
        result = await svc.get_history(days=7, limit=None)
        assert result["streak_days"] == 1

    @pytest.mark.asyncio
    async def test_streak_consecutive_days(self):
        """streak_days counts backward from end_date through consecutive days."""
        today = _today()
        states = {}
        # Reviews on today, yesterday, and 2 days ago = streak of 3
        for i in range(3):
            d = today - timedelta(days=i)
            ts = datetime(d.year, d.month, d.day, 10, 0, 0).isoformat()
            states[f"math.canvas:concept_{i}"] = _card(ts)

        svc = _make_service(card_states=states)
        result = await svc.get_history(days=7, limit=None)
        assert result["streak_days"] == 3

    @pytest.mark.asyncio
    async def test_streak_breaks_on_gap(self):
        """streak_days stops counting at the first missing day."""
        today = _today()
        # Reviews on today and 2 days ago (gap on yesterday)
        d_today = datetime(today.year, today.month, today.day, 10, 0, 0)
        d_2ago = d_today - timedelta(days=2)
        states = {
            "math.canvas:a": _card(d_today.isoformat()),
            "math.canvas:b": _card(d_2ago.isoformat()),
        }
        svc = _make_service(card_states=states)
        result = await svc.get_history(days=7, limit=None)
        # Only today counts (yesterday is missing)
        assert result["streak_days"] == 1

    @pytest.mark.asyncio
    async def test_streak_zero_when_no_review_today(self):
        """streak_days=0 when reviews exist but not on end_date."""
        today = _today()
        # Review only 2 days ago
        d = today - timedelta(days=2)
        states = {
            "math.canvas:a": _card(
                datetime(d.year, d.month, d.day, 10, 0, 0).isoformat()
            ),
        }
        svc = _make_service(card_states=states)
        result = await svc.get_history(days=7, limit=None)
        assert result["streak_days"] == 0

    @pytest.mark.asyncio
    async def test_streak_multiple_reviews_same_day(self):
        """Multiple reviews on the same day count as 1 streak day."""
        today = _today()
        yesterday = today - timedelta(days=1)
        states = {
            "math.canvas:a": _card(
                datetime(today.year, today.month, today.day, 10, 0, 0).isoformat()
            ),
            "math.canvas:b": _card(
                datetime(today.year, today.month, today.day, 14, 0, 0).isoformat()
            ),
            "math.canvas:c": _card(
                datetime(yesterday.year, yesterday.month, yesterday.day, 9, 0, 0).isoformat()
            ),
        }
        svc = _make_service(card_states=states)
        result = await svc.get_history(days=7, limit=None)
        assert result["streak_days"] == 2


# ── AC-32.4.1: review_count (total_count) accuracy ──────────────────────────

class TestReviewCountAccuracy:
    """Verify total_count reflects actual number of review records."""

    @pytest.mark.asyncio
    async def test_total_count_matches_records(self):
        """total_count equals number of card state entries in date range."""
        today = _today()
        states = {}
        for i in range(5):
            d = today - timedelta(days=i % 3)
            ts = datetime(d.year, d.month, d.day, 10 + i, 0, 0).isoformat()
            states[f"math.canvas:concept_{i}"] = _card(ts)

        svc = _make_service(card_states=states)
        result = await svc.get_history(days=7, limit=None)
        assert result["total_count"] == 5

    @pytest.mark.asyncio
    async def test_total_count_excludes_out_of_range(self):
        """Records outside the date range are not counted."""
        today = _today()
        old = today - timedelta(days=30)
        states = {
            "math.canvas:recent": _card(
                datetime(today.year, today.month, today.day, 10, 0, 0).isoformat()
            ),
            "math.canvas:old": _card(
                datetime(old.year, old.month, old.day, 10, 0, 0).isoformat()
            ),
        }
        svc = _make_service(card_states=states)
        result = await svc.get_history(days=7, limit=None)
        assert result["total_count"] == 1

    @pytest.mark.asyncio
    async def test_total_count_zero_when_empty(self):
        """total_count=0 when no card states exist."""
        svc = _make_service(card_states={})
        result = await svc.get_history(days=7, limit=None)
        assert result["total_count"] == 0

    @pytest.mark.asyncio
    async def test_has_more_false_when_within_limit(self):
        """has_more=False when total records <= limit."""
        today = _today()
        states = {
            f"math.canvas:c{i}": _card(
                datetime(today.year, today.month, today.day, 10 + i, 0, 0).isoformat()
            )
            for i in range(3)
        }
        svc = _make_service(card_states=states)
        result = await svc.get_history(days=7, limit=5)
        assert result["has_more"] is False

    @pytest.mark.asyncio
    async def test_has_more_true_when_exceeds_limit(self):
        """has_more=True when total records > limit."""
        today = _today()
        states = {
            f"math.canvas:c{i}": _card(
                datetime(today.year, today.month, today.day, 10, i, 0).isoformat()
            )
            for i in range(10)
        }
        svc = _make_service(card_states=states)
        result = await svc.get_history(days=7, limit=5)
        assert result["has_more"] is True
        assert result["total_count"] == 10


# ── AC-32.4.3: Card states as data source (persistence proxy) ───────────────

class TestCardStatesDataSource:
    """Verify get_history reads from _card_states when Graphiti unavailable."""

    @pytest.mark.asyncio
    async def test_reads_from_card_states_without_graphiti(self):
        """Records are populated from _card_states when graphiti_client is None."""
        today = _today()
        states = {
            "algebra.canvas:linear_eq": _card(
                datetime(today.year, today.month, today.day, 10, 0, 0).isoformat(),
                rating=4,
            ),
        }
        svc = _make_service(card_states=states)
        result = await svc.get_history(days=7, limit=None)

        assert result["total_count"] == 1
        review = result["records"][0]["reviews"][0]
        assert review["concept_name"] == "linear_eq"
        assert review["canvas_path"] == "algebra.canvas"
        assert review["rating"] == 4

    @pytest.mark.asyncio
    async def test_concept_id_extracted_from_key(self):
        """concept_id comes from the full key, concept_name from part after ':'."""
        today = _today()
        states = {
            "calc.canvas:derivative_rules": _card(
                datetime(today.year, today.month, today.day, 10, 0, 0).isoformat()
            ),
        }
        svc = _make_service(card_states=states)
        result = await svc.get_history(days=7, limit=None)

        review = result["records"][0]["reviews"][0]
        assert review["concept_id"] == "calc.canvas:derivative_rules"
        assert review["concept_name"] == "derivative_rules"

    @pytest.mark.asyncio
    async def test_canvas_path_filter_works(self):
        """canvas_path filter only returns matching records."""
        today = _today()
        ts = datetime(today.year, today.month, today.day, 10, 0, 0).isoformat()
        states = {
            "algebra.canvas:eq": _card(ts),
            "calculus.canvas:integral": _card(ts),
        }
        svc = _make_service(card_states=states)
        result = await svc.get_history(days=7, canvas_path="algebra", limit=None)

        assert result["total_count"] == 1
        assert result["records"][0]["reviews"][0]["canvas_path"] == "algebra.canvas"

    @pytest.mark.asyncio
    async def test_concept_name_filter_works(self):
        """concept_name filter only returns matching records."""
        today = _today()
        ts = datetime(today.year, today.month, today.day, 10, 0, 0).isoformat()
        states = {
            "math.canvas:derivative": _card(ts),
            "math.canvas:integral": _card(ts),
        }
        svc = _make_service(card_states=states)
        result = await svc.get_history(
            days=7, concept_name="derivative", limit=None
        )

        assert result["total_count"] == 1
        assert result["records"][0]["reviews"][0]["concept_name"] == "derivative"


# ── AC-32.4.4: Date grouping for week/month trends ──────────────────────────

class TestDateGrouping:
    """Verify records are grouped by date for trend display."""

    @pytest.mark.asyncio
    async def test_records_grouped_by_date(self):
        """Records on the same day appear in the same date group."""
        today = _today()
        ts1 = datetime(today.year, today.month, today.day, 10, 0, 0).isoformat()
        ts2 = datetime(today.year, today.month, today.day, 14, 0, 0).isoformat()
        states = {
            "math.canvas:a": _card(ts1),
            "math.canvas:b": _card(ts2),
        }
        svc = _make_service(card_states=states)
        result = await svc.get_history(days=7, limit=None)

        assert len(result["records"]) == 1  # One date group
        assert len(result["records"][0]["reviews"]) == 2

    @pytest.mark.asyncio
    async def test_records_sorted_newest_first(self):
        """Date groups are sorted with newest date first."""
        today = _today()
        yesterday = today - timedelta(days=1)
        ts_today = datetime(today.year, today.month, today.day, 10, 0, 0).isoformat()
        ts_yesterday = datetime(
            yesterday.year, yesterday.month, yesterday.day, 10, 0, 0
        ).isoformat()
        states = {
            "math.canvas:a": _card(ts_yesterday),
            "math.canvas:b": _card(ts_today),
        }
        svc = _make_service(card_states=states)
        result = await svc.get_history(days=7, limit=None)

        assert len(result["records"]) == 2
        assert result["records"][0]["date"] == today.isoformat()
        assert result["records"][1]["date"] == yesterday.isoformat()

    @pytest.mark.asyncio
    async def test_multi_day_spread_for_trends(self):
        """Records spread across multiple days produce separate groups."""
        today = _today()
        states = {}
        # 5 consecutive days of reviews
        for i in range(5):
            d = today - timedelta(days=i)
            ts = datetime(d.year, d.month, d.day, 10, 0, 0).isoformat()
            states[f"math.canvas:c{i}"] = _card(ts)

        svc = _make_service(card_states=states)
        result = await svc.get_history(days=7, limit=None)

        assert len(result["records"]) == 5  # 5 date groups
        assert result["streak_days"] == 5

    @pytest.mark.asyncio
    async def test_streak_calculated_before_limit_truncation(self):
        """streak_days reflects ALL records, not just limited view."""
        today = _today()
        states = {}
        # 4 consecutive days
        for i in range(4):
            d = today - timedelta(days=i)
            ts = datetime(d.year, d.month, d.day, 10, 0, 0).isoformat()
            states[f"math.canvas:c{i}"] = _card(ts)

        svc = _make_service(card_states=states)
        # limit=2 truncates records but streak should still count all 4 days
        result = await svc.get_history(days=7, limit=2)

        assert result["streak_days"] == 4  # Calculated before truncation
        assert result["has_more"] is True
        assert result["total_count"] == 4
