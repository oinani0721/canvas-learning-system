# Story 34.8: Real service integration + DI completeness + show_all hard cap
"""
Tests using real ReviewService instance (not mocking get_history),
DI completeness verification, and MAX_HISTORY_RECORDS cap.

- Story 34.8 AC1: Real integration tests
- Story 34.8 AC2: DI completeness (graphiti_client injection)
- Story 34.8 AC3: show_all hard cap (MAX_HISTORY_RECORDS=1000)
"""

from datetime import datetime, date, timedelta
from unittest.mock import patch

import pytest

from .helpers import make_real_review_service, build_card_states


# ═══════════════════════════════════════════════════════════════════════════════
# Story 34.8 AC1: Real Integration Tests (NOT mocking ReviewService)
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
@pytest.mark.usefixtures("patch_service_datetime")
class TestRealReviewServiceHistory:
    """Story 34.8 AC1: Real integration tests using actual ReviewService instance.

    These tests validate the REAL sorting, filtering, and pagination logic
    inside ReviewService.get_history() — NOT a mock.

    Uses fixed dates for determinism (test-review H3 fix): test data uses
    date(2025, 6, 15) as base, so we patch datetime.now() in the service
    module to match, ensuring records fall within the query date range.
    """

    async def test_default_limit_returns_max_5_records(self):
        """AC1: Default limit=5 returns at most 5 individual review records."""
        card_states = build_card_states(10, "math")
        service = make_real_review_service(card_states)

        result = await service.get_history(days=7, limit=5)

        total_reviews = sum(len(day["reviews"]) for day in result["records"])
        assert total_reviews <= 5
        assert result["has_more"] is True  # 10 records > limit 5
        assert result["total_count"] == 10

    async def test_show_all_returns_all_records_within_cap(self):
        """AC1+AC3: Large limit returns all records when count < limit."""
        card_states = build_card_states(8, "physics")
        service = make_real_review_service(card_states)

        from app.services.review_service import MAX_HISTORY_RECORDS
        result = await service.get_history(days=7, limit=MAX_HISTORY_RECORDS)

        total_reviews = sum(len(day["reviews"]) for day in result["records"])
        assert total_reviews == 8
        assert result["has_more"] is False

    async def test_limit_parameter_slices_correctly(self):
        """AC1: Custom limit slices records correctly."""
        card_states = build_card_states(12, "chem")
        service = make_real_review_service(card_states)

        result = await service.get_history(days=7, limit=3)

        total_reviews = sum(len(day["reviews"]) for day in result["records"])
        assert total_reviews <= 3
        assert result["has_more"] is True
        assert result["total_count"] == 12

    async def test_records_sorted_by_time_descending(self):
        """AC1: Records are sorted by review_time descending (newest first)."""
        card_states = build_card_states(6, "bio")
        service = make_real_review_service(card_states)

        from app.services.review_service import MAX_HISTORY_RECORDS
        result = await service.get_history(days=7, limit=MAX_HISTORY_RECORDS)

        all_times = []
        for day_record in result["records"]:
            for review in day_record["reviews"]:
                all_times.append(review["review_time"])

        for i in range(len(all_times) - 1):
            assert all_times[i] >= all_times[i + 1], (
                f"Records not sorted descending: {all_times[i]} < {all_times[i+1]}"
            )

    async def test_filter_by_canvas_path(self):
        """AC1: canvas_path filter works with real service."""
        states = {}
        fixed = date(2025, 6, 15)
        for i in range(3):
            states[f"math.canvas:concept_{i}"] = {
                "last_review": datetime(fixed.year, fixed.month, fixed.day, 10, 0, 0).isoformat(),
                "rating": 3,
            }
        for i in range(2):
            states[f"physics.canvas:concept_{i}"] = {
                "last_review": datetime(fixed.year, fixed.month, fixed.day, 11, 0, 0).isoformat(),
                "rating": 4,
            }

        service = make_real_review_service(states)
        from app.services.review_service import MAX_HISTORY_RECORDS
        result = await service.get_history(days=7, canvas_path="math", limit=MAX_HISTORY_RECORDS)

        total_reviews = sum(len(d["reviews"]) for d in result["records"])
        assert total_reviews == 3  # Only math records

    async def test_filter_by_concept_name(self):
        """AC1: concept_name filter works with real service."""
        states = {}
        fixed = date(2025, 6, 15)
        states["math.canvas:逆否命题"] = {
            "last_review": datetime(fixed.year, fixed.month, fixed.day, 10, 0, 0).isoformat(),
            "rating": 4,
        }
        states["math.canvas:充分条件"] = {
            "last_review": datetime(fixed.year, fixed.month, fixed.day, 11, 0, 0).isoformat(),
            "rating": 3,
        }

        service = make_real_review_service(states)
        from app.services.review_service import MAX_HISTORY_RECORDS
        result = await service.get_history(days=7, concept_name="逆否命题", limit=MAX_HISTORY_RECORDS)

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
        from app.services.review_service import MAX_HISTORY_RECORDS
        result = await service.get_history(days=7, limit=MAX_HISTORY_RECORDS)

        assert result["streak_days"] == 2


# ═══════════════════════════════════════════════════════════════════════════════
# Story 34.8 AC2: DI Completeness Test — graphiti_client injection
# ═══════════════════════════════════════════════════════════════════════════════


class TestReviewServiceDICompleteness:
    """Story 34.8 AC2: Verify get_review_service explicitly handles graphiti_client."""

    def test_dependencies_get_review_service_delegates_to_services_layer(self):
        """Story 38.9 AC2: dependencies.py delegates to services.review_service singleton."""
        from pathlib import Path
        deps_path = Path(__file__).resolve().parents[3] / "app" / "dependencies.py"
        source = deps_path.read_text(encoding="utf-8")

        func_start = source.find("async def get_review_service(")
        assert func_start != -1, "get_review_service() not found in dependencies.py"

        next_func = source.find("\nasync def ", func_start + 10)
        if next_func == -1:
            next_func = source.find("\ndef ", func_start + 10)
        func_body = source[func_start:next_func] if next_func != -1 else source[func_start:]

        assert "from .services.review_service import" in func_body or \
               "services.review_service" in func_body, (
            "get_review_service() does not delegate to services.review_service"
        )

    def test_services_layer_singleton_passes_graphiti_client(self):
        """Story 38.9 AC5: services/review_service.py singleton factory handles graphiti_client."""
        import inspect
        from app.services.review_service import get_review_service

        source = inspect.getsource(get_review_service)
        assert "graphiti_client" in source, (
            "services.review_service.get_review_service() does not mention graphiti_client"
        )
        assert "graphiti_client=graphiti_client" in source, (
            "services.review_service.get_review_service() does not pass graphiti_client= to ReviewService()"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Story 34.8 AC3: show_all hard cap tests (MAX_HISTORY_RECORDS=1000)
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.usefixtures("patch_service_datetime")
class TestShowAllHardCap:
    """Story 34.8 AC3: Verify show_all=True uses MAX_HISTORY_RECORDS cap."""

    def test_max_history_records_constant_exists(self):
        """AC3: MAX_HISTORY_RECORDS constant must be defined."""
        from app.services.review_service import MAX_HISTORY_RECORDS
        assert MAX_HISTORY_RECORDS == 1000

    def test_show_all_uses_max_cap_in_endpoint(self):
        """AC3: show_all=True in endpoint must use MAX_HISTORY_RECORDS, not None."""
        from pathlib import Path
        review_path = Path(__file__).resolve().parents[3] / "app" / "api" / "v1" / "endpoints" / "review.py"
        source = review_path.read_text(encoding="utf-8")

        assert "effective_limit = None if show_all" not in source, (
            "show_all=True still uses effective_limit=None — must use MAX_HISTORY_RECORDS"
        )
        assert "MAX_HISTORY_RECORDS" in source, (
            "review.py endpoint does not reference MAX_HISTORY_RECORDS"
        )

    @pytest.mark.asyncio
    async def test_show_all_truncates_above_cap(self):
        """AC3: When records > MAX_HISTORY_RECORDS, truncate and set has_more=True."""
        card_states = build_card_states(15, "large")
        service = make_real_review_service(card_states)

        result = await service.get_history(days=7, limit=8)

        total_reviews = sum(len(d["reviews"]) for d in result["records"])
        assert total_reviews <= 8
        assert result["has_more"] is True
        assert result["total_count"] == 15

    @pytest.mark.asyncio
    async def test_show_all_no_truncation_below_cap(self):
        """AC3: When records < MAX_HISTORY_RECORDS, return all with has_more=False."""
        card_states = build_card_states(5, "small")
        service = make_real_review_service(card_states)

        from app.services.review_service import MAX_HISTORY_RECORDS
        result = await service.get_history(days=7, limit=MAX_HISTORY_RECORDS)

        total_reviews = sum(len(d["reviews"]) for d in result["records"])
        assert total_reviews == 5
        assert result["has_more"] is False
