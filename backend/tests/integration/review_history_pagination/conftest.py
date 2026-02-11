# Story 34.11: Shared fixtures for review history pagination tests
"""
Shared fixtures extracted from test_review_history_pagination.py (1234 lines).
Eliminates ~15 duplicate mock definitions across test modules.
"""

from datetime import datetime, date, timedelta
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.review_service import ReviewService

# ── Constants ────────────────────────────────────────────────────────────────

REVIEW_SERVICE_PATCH = "app.api.v1.endpoints.review._get_review_service_singleton"
_FIXED_REVIEW_TIME = datetime(2025, 1, 15, 10, 30, 0)


# ── Singleton reset (autouse) ───────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _reset_review_service_singleton():
    """Reset ReviewService singleton between tests to prevent contamination."""
    from app.services.review_service import reset_review_service_singleton
    reset_review_service_singleton()
    try:
        yield
    finally:
        reset_review_service_singleton()


# ── Shared fixtures ─────────────────────────────────────────────────────────

@pytest.fixture
def client():
    """Create FastAPI test client (shared across all test modules)."""
    return TestClient(app)


# ── Helper functions ─────────────────────────────────────────────────────────

def make_mock_review_service(history_return_value: dict = None) -> AsyncMock:
    """Create a mock ReviewService with get_history pre-configured.

    Eliminates repeated inline mock setup across 15+ tests.
    """
    service = AsyncMock()
    service.get_history = AsyncMock(
        return_value=history_return_value or {
            "records": [],
            "has_more": False,
            "streak_days": 0,
        }
    )
    return service


class TestableReviewService(ReviewService):
    """Test-only subclass exposing card state injection (Story 34.11 AC3 Option B).

    Eliminates direct private attribute access in tests by providing a public API.
    Production ReviewService remains unchanged — no test pollution.
    """

    def set_card_states(self, states: Dict[str, Any]) -> None:
        """Public test API for injecting card states."""
        self._card_states = states


def make_real_review_service(card_states: Dict[str, Any] = None) -> TestableReviewService:
    """Create a TestableReviewService with mock infrastructure but real business logic.

    Story 34.8 AC1: Only CanvasService and TaskManager are mocked (infrastructure).
    ReviewService.get_history() runs its real implementation.
    """
    from app.services.background_task_manager import BackgroundTaskManager

    mock_canvas_service = MagicMock()
    mock_canvas_service.cleanup = AsyncMock()
    mock_canvas_service.canvas_exists = AsyncMock(return_value=True)
    mock_canvas_service.get_canvas = AsyncMock(return_value={"nodes": [], "edges": []})

    task_manager = BackgroundTaskManager()

    service = TestableReviewService(
        canvas_service=mock_canvas_service,
        task_manager=task_manager,
        graphiti_client=None,
        fsrs_manager=None,
    )

    if card_states:
        service.set_card_states(card_states)

    return service


def build_card_states_for_history(
    count: int, canvas_prefix: str = "math"
) -> Dict[str, Any]:
    """Build fake card state entries for get_history() to read.

    Uses fixed date (2025-06-15) for deterministic tests.
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
