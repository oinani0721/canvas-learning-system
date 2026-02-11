# Shared fixtures for EPIC-32 FSRS unit tests
# Extracted from test_review_service_fsrs.py, test_fsrs_state_query.py
# to eliminate fixture duplication across 4 files.
"""
Shared pytest fixtures for FSRS unit tests.

Provides mock dependencies (CanvasService, BackgroundTaskManager) and
ReviewService factory/instance fixtures used by:
- test_review_service_fsrs.py
- test_fsrs_state_query.py
- test_card_state_concurrent_write.py (indirectly)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_canvas_service():
    """Shared mock CanvasService for FSRS unit tests."""
    mock = MagicMock()
    mock.get_canvas = AsyncMock(return_value={"nodes": [], "edges": []})
    return mock


@pytest.fixture
def mock_task_manager():
    """Shared mock BackgroundTaskManager for FSRS unit tests."""
    mock = MagicMock()
    mock.submit_task = MagicMock(return_value="task_123")
    return mock


@pytest.fixture
def review_service_factory(mock_canvas_service, mock_task_manager):
    """Factory to create ReviewService with mocked dependencies."""
    def _create():
        from app.services.review_service import ReviewService
        return ReviewService(
            canvas_service=mock_canvas_service,
            task_manager=mock_task_manager,
        )
    return _create


@pytest.fixture
def review_service(review_service_factory):
    """Create ReviewService instance for testing."""
    return review_service_factory()


@pytest.fixture
def fallback_service(mock_canvas_service, mock_task_manager):
    """ReviewService with FSRS disabled (Ebbinghaus fallback mode)."""
    from app.services.review_service import ReviewService
    with patch("app.services.review_service.create_fsrs_manager", return_value=None):
        return ReviewService(
            canvas_service=mock_canvas_service,
            task_manager=mock_task_manager,
            fsrs_manager=None,
        )
