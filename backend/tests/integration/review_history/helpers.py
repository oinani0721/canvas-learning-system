"""Constants, context managers, and factory functions for review history tests."""

from contextlib import contextmanager
from datetime import datetime, date, timedelta
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch

# Fixed timestamp for deterministic tests (avoid datetime.now() flakiness)
FIXED_REVIEW_TIME = datetime(2025, 1, 15, 10, 30, 0)

# Patch target: review.py imports get_review_service as _get_review_service_singleton
REVIEW_SERVICE_PATCH = "app.api.v1.endpoints.review._get_review_service_singleton"


@contextmanager
def mock_review_history(*, records=None, has_more=False, streak_days=0,
                        retention_rate=None, side_effect=None):
    """Patch review service singleton with configured get_history mock.

    Replaces 26 occurrences of the boilerplate pattern:
        with patch(REVIEW_SERVICE_PATCH, new_callable=AsyncMock) as mock_get:
            mock_service = AsyncMock()
            mock_service.get_history = AsyncMock(return_value={...})
            mock_get.return_value = mock_service

    Yields the mock_service for call assertions.
    """
    return_value = {
        "records": records if records is not None else [],
        "has_more": has_more,
        "streak_days": streak_days,
    }
    if retention_rate is not None:
        return_value["retention_rate"] = retention_rate

    with patch(REVIEW_SERVICE_PATCH, new_callable=AsyncMock) as mock_get:
        mock_service = AsyncMock()
        if side_effect is not None:
            mock_service.get_history = AsyncMock(side_effect=side_effect)
        else:
            mock_service.get_history = AsyncMock(return_value=return_value)
        mock_get.return_value = mock_service
        yield mock_service


def make_real_review_service(card_states: Dict[str, Any] = None):
    """Create a real ReviewService with mock CanvasService but real business logic.

    Story 34.8 AC1: ReviewService.get_history() runs its real implementation
    (sorting, filtering, pagination) — only CanvasService and TaskManager are
    mocked since they are infrastructure dependencies, not the SUT.
    """
    from app.services.background_task_manager import BackgroundTaskManager
    from app.services.review_service import ReviewService

    mock_canvas_service = MagicMock()
    mock_canvas_service.cleanup = AsyncMock()
    mock_canvas_service.canvas_exists = AsyncMock(return_value=True)
    mock_canvas_service.get_canvas = AsyncMock(return_value={"nodes": [], "edges": []})

    task_manager = BackgroundTaskManager()

    service = ReviewService(
        canvas_service=mock_canvas_service,
        task_manager=task_manager,
        graphiti_client=None,
        fsrs_manager=None,
    )

    if card_states:
        service._card_states = card_states

    return service


def build_card_states(count: int, canvas_prefix: str = "math") -> Dict[str, Any]:
    """Build fake _card_states entries for get_history() to read.

    ReviewService.get_history() uses _card_states as fallback when Graphiti
    is unavailable. Each entry needs 'last_review' as an ISO string,
    and the key format is 'canvas:concept'.

    Uses fixed date (2025-06-15) for deterministic tests (test-review H3 fix).
    """
    base_date = date(2025, 6, 15)
    states = {}
    for i in range(count):
        review_date = base_date - timedelta(days=i % 5)
        key = f"{canvas_prefix}.canvas:concept_{i}"
        states[key] = {
            "last_review": datetime(
                review_date.year, review_date.month, review_date.day, 10, 0, 0
            ).isoformat(),
            "rating": (i % 4) + 1,
        }
    return states
