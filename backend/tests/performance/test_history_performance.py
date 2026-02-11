# EPIC-34 NFR: Performance benchmark for ReviewService.get_history()
# [Source: _bmad-output/test-artifacts/nfr-assessment.md — Evidence Gap #1]
"""
Performance benchmarks for review history pagination.

Measures get_history() execution time at different data volumes to verify
that MAX_HISTORY_RECORDS=1000 cap keeps P95 under reasonable bounds.

Thresholds:
- 100 records: P95 < 50ms
- 500 records: P95 < 100ms
- 1000 records: P95 < 200ms
"""

import statistics
import time
from datetime import date, datetime, timedelta
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.review_service import MAX_HISTORY_RECORDS, ReviewService

# Fixed date to avoid date.today() non-determinism
_FIXED_DATE = date(2025, 6, 15)


def _build_card_states(count: int, canvas_prefix: str = "perf") -> Dict[str, Any]:
    """Build card_states entries for performance testing."""
    states = {}
    for i in range(count):
        review_date = _FIXED_DATE - timedelta(days=i % 30)
        key = f"{canvas_prefix}.canvas:concept_{i}"
        states[key] = {
            "last_review": datetime(
                review_date.year, review_date.month, review_date.day, 10, 0, 0
            ).isoformat(),
            "rating": (i % 4) + 1
        }
    return states


def _make_service(card_states: Dict[str, Any]) -> ReviewService:
    """Create ReviewService with injected card_states for benchmarking."""
    mock_canvas = MagicMock()
    mock_canvas.canvas_exists = AsyncMock(return_value=True)
    mock_canvas.get_canvas = AsyncMock(return_value={"nodes": [], "edges": []})

    from app.services.background_task_manager import BackgroundTaskManager
    task_manager = BackgroundTaskManager()

    service = ReviewService(
        canvas_service=mock_canvas,
        task_manager=task_manager,
        graphiti_client=None,
        fsrs_manager=None
    )
    service._card_states = card_states
    return service


async def _benchmark_get_history(count: int, iterations: int = 20) -> Dict[str, float]:
    """Run get_history benchmark and return timing statistics."""
    card_states = _build_card_states(count)
    service = _make_service(card_states)

    # Patch datetime.now() in service to match _FIXED_DATE so records fall in range
    _fixed_now = datetime(_FIXED_DATE.year, _FIXED_DATE.month, _FIXED_DATE.day, 23, 59, 0)

    timings = []
    with patch("app.services.review_service.datetime") as mock_dt:
        mock_dt.now.return_value = _fixed_now
        mock_dt.fromisoformat = datetime.fromisoformat
        for _ in range(iterations):
            start = time.perf_counter()
            await service.get_history(days=30, limit=min(count, MAX_HISTORY_RECORDS))
            elapsed_ms = (time.perf_counter() - start) * 1000
            timings.append(elapsed_ms)

    timings.sort()
    n = len(timings)
    return {
        "count": count,
        "iterations": iterations,
        "mean_ms": statistics.mean(timings),
        "p50_ms": timings[n // 2],
        "p95_ms": timings[int(n * 0.95)],
        "min_ms": min(timings),
        "max_ms": max(timings),
    }


@pytest.fixture(autouse=True)
def _reset_review_singleton():
    """Reset services-layer singleton to prevent test contamination (Story 38.9)."""
    from app.services.review_service import reset_review_service_singleton
    reset_review_service_singleton()
    try:
        yield
    finally:
        reset_review_service_singleton()


@pytest.mark.asyncio
class TestHistoryPerformanceBenchmarks:
    """Performance benchmarks for ReviewService.get_history().

    NFR Threshold: 1000 records sort+slice P95 < 200ms
    """

    @pytest.fixture(autouse=True)
    def _patch_service_datetime(self):
        """Patch datetime.now() in review_service to match _FIXED_DATE."""
        _fixed_now = datetime(_FIXED_DATE.year, _FIXED_DATE.month, _FIXED_DATE.day, 23, 59, 0)
        with patch("app.services.review_service.datetime") as mock_dt:
            mock_dt.now.return_value = _fixed_now
            mock_dt.fromisoformat = datetime.fromisoformat
            yield

    async def test_100_records_performance(self):
        """Benchmark: 100 records P95 < 50ms."""
        result = await _benchmark_get_history(100, iterations=20)

        print(f"\n--- 100 records ---")
        print(f"  Mean: {result['mean_ms']:.2f}ms  P50: {result['p50_ms']:.2f}ms  P95: {result['p95_ms']:.2f}ms")

        assert result["p95_ms"] < 50, (
            f"100 records P95={result['p95_ms']:.2f}ms exceeds 50ms"
        )

    async def test_500_records_performance(self):
        """Benchmark: 500 records P95 < 100ms."""
        result = await _benchmark_get_history(500, iterations=20)

        print(f"\n--- 500 records ---")
        print(f"  Mean: {result['mean_ms']:.2f}ms  P50: {result['p50_ms']:.2f}ms  P95: {result['p95_ms']:.2f}ms")

        assert result["p95_ms"] < 100, (
            f"500 records P95={result['p95_ms']:.2f}ms exceeds 100ms"
        )

    async def test_1000_records_performance(self):
        """Benchmark: 1000 records (MAX_HISTORY_RECORDS) P95 < 200ms."""
        result = await _benchmark_get_history(1000, iterations=20)

        print(f"\n--- 1000 records ---")
        print(f"  Mean: {result['mean_ms']:.2f}ms  P50: {result['p50_ms']:.2f}ms  P95: {result['p95_ms']:.2f}ms")

        assert result["p95_ms"] < 200, (
            f"1000 records P95={result['p95_ms']:.2f}ms exceeds 200ms"
        )

    async def test_scaling_is_subquadratic(self):
        """Verify doubling records doesn't quadruple time (O(n log n) expected)."""
        result_500 = await _benchmark_get_history(500, iterations=10)
        result_1000 = await _benchmark_get_history(1000, iterations=10)

        ratio = result_1000["mean_ms"] / max(result_500["mean_ms"], 0.001)

        print(f"\n--- Scaling ---")
        print(f"  500: {result_500['mean_ms']:.2f}ms  1000: {result_1000['mean_ms']:.2f}ms  ratio: {ratio:.2f}")

        assert ratio < 4.0, f"Scaling ratio {ratio:.2f} worse than O(n log n)"

    async def test_filter_by_canvas_performance(self):
        """Filtering by canvas_path should not degrade performance."""
        states = {}
        for i in range(1000):
            canvas = f"canvas_{i % 10}"
            review_date = _FIXED_DATE - timedelta(days=i % 30)
            states[f"{canvas}.canvas:concept_{i}"] = {
                "last_review": datetime(
                    review_date.year, review_date.month, review_date.day, 10, 0, 0
                ).isoformat(),
                "rating": (i % 4) + 1
            }

        service = _make_service(states)

        start = time.perf_counter()
        await service.get_history(days=30, limit=MAX_HISTORY_RECORDS)
        unfiltered_ms = (time.perf_counter() - start) * 1000

        start = time.perf_counter()
        await service.get_history(days=30, canvas_path="canvas_0", limit=MAX_HISTORY_RECORDS)
        filtered_ms = (time.perf_counter() - start) * 1000

        print(f"\n--- Filter ---")
        print(f"  Unfiltered: {unfiltered_ms:.2f}ms  Filtered: {filtered_ms:.2f}ms")

        assert filtered_ms < unfiltered_ms * 2, "Filtered should not be slower"
