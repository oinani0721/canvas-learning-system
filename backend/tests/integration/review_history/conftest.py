"""Shared fixtures for review history integration tests."""

from datetime import datetime
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(autouse=True)
def _reset_review_service_singleton():
    """Reset ReviewService singleton between tests to prevent contamination."""
    from app.services.review_service import reset_review_service_singleton
    reset_review_service_singleton()
    try:
        yield
    finally:
        reset_review_service_singleton()


@pytest.fixture
def client():
    """Create FastAPI test client (function-scoped, shadows module-scoped conftest)."""
    return TestClient(app)


@pytest.fixture
def patch_service_datetime():
    """Patch datetime.now() in review_service to match fixed test dates.

    Opt-in: use @pytest.mark.usefixtures("patch_service_datetime") on classes that need it.
    """
    _fixed_now = datetime(2025, 6, 15, 23, 59, 0)
    with patch("app.services.review_service.datetime") as mock_dt:
        mock_dt.now.return_value = _fixed_now
        mock_dt.fromisoformat = datetime.fromisoformat
        yield
