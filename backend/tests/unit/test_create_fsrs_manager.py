# Story 32.8 Code Review Fix: Unit tests for create_fsrs_manager() factory
"""
Tests for the unified FSRSManager factory function and USE_FSRS config toggle.

Covers:
- USE_FSRS=False disables FSRS
- USE_FSRS=True with FSRS available creates manager
- FSRS unavailable returns None
- settings=None auto-loads from get_settings()
- FSRSManager creation exception returns None
- ReviewService.__init__ respects USE_FSRS=False via factory
"""

import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture(autouse=True)
def _isolate_card_states_file(tmp_path):
    """Prevent test data pollution of production fsrs_card_states.json."""
    tmp_file = tmp_path / "fsrs_card_states.json"
    with patch("app.services.review_service._CARD_STATES_FILE", tmp_file):
        yield tmp_file


def _make_settings(use_fsrs=True, desired_retention=0.9):
    """Create a mock Settings object with FSRS-related attributes."""
    settings = MagicMock()
    settings.USE_FSRS = use_fsrs
    settings.FSRS_DESIRED_RETENTION = desired_retention
    return settings


# ═══════════════════════════════════════════════════════════════════════════════
# create_fsrs_manager() factory tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestCreateFsrsManagerFactory:
    """Tests for the create_fsrs_manager() unified factory function."""

    def test_returns_none_when_use_fsrs_false(self):
        """USE_FSRS=False → factory returns None, FSRS disabled."""
        from app.services.review_service import create_fsrs_manager

        settings = _make_settings(use_fsrs=False)
        result = create_fsrs_manager(settings)
        assert result is None

    def test_returns_manager_when_use_fsrs_true_and_available(self):
        """USE_FSRS=True + FSRS available → returns FSRSManager instance."""
        from app.services.review_service import create_fsrs_manager

        mock_mgr = MagicMock()
        settings = _make_settings(use_fsrs=True, desired_retention=0.85)

        with patch("app.services.review_service.FSRS_AVAILABLE", True), \
             patch("app.services.review_service.FSRSManager", return_value=mock_mgr) as mock_cls:
            result = create_fsrs_manager(settings)

        assert result is mock_mgr
        mock_cls.assert_called_once_with(desired_retention=0.85)

    def test_returns_none_when_fsrs_unavailable(self):
        """USE_FSRS=True but FSRS library not installed → returns None."""
        from app.services.review_service import create_fsrs_manager

        settings = _make_settings(use_fsrs=True)

        with patch("app.services.review_service.FSRS_AVAILABLE", False):
            result = create_fsrs_manager(settings)

        assert result is None

    def test_returns_none_when_fsrs_manager_is_none(self):
        """USE_FSRS=True but FSRSManager class is None (import failed) → returns None."""
        from app.services.review_service import create_fsrs_manager

        settings = _make_settings(use_fsrs=True)

        with patch("app.services.review_service.FSRS_AVAILABLE", True), \
             patch("app.services.review_service.FSRSManager", None):
            result = create_fsrs_manager(settings)

        assert result is None

    def test_auto_loads_settings_when_none(self):
        """settings=None → factory calls get_settings() internally."""
        from app.services.review_service import create_fsrs_manager

        mock_settings = _make_settings(use_fsrs=False)

        with patch("app.config.get_settings", return_value=mock_settings):
            result = create_fsrs_manager(settings=None)

        assert result is None  # USE_FSRS=False

    def test_returns_none_on_creation_exception(self):
        """FSRSManager constructor throws → factory catches and returns None."""
        from app.services.review_service import create_fsrs_manager

        settings = _make_settings(use_fsrs=True)

        with patch("app.services.review_service.FSRS_AVAILABLE", True), \
             patch("app.services.review_service.FSRSManager", side_effect=RuntimeError("init fail")):
            result = create_fsrs_manager(settings)

        assert result is None

    def test_desired_retention_passed_to_constructor(self):
        """Factory passes FSRS_DESIRED_RETENTION from settings to FSRSManager."""
        from app.services.review_service import create_fsrs_manager

        mock_mgr = MagicMock()
        settings = _make_settings(use_fsrs=True, desired_retention=0.75)

        with patch("app.services.review_service.FSRS_AVAILABLE", True), \
             patch("app.services.review_service.FSRSManager", return_value=mock_mgr) as mock_cls:
            create_fsrs_manager(settings)

        mock_cls.assert_called_once_with(desired_retention=0.75)


# ═══════════════════════════════════════════════════════════════════════════════
# ReviewService.__init__ integration with factory
# ═══════════════════════════════════════════════════════════════════════════════


class TestReviewServiceInitFactory:
    """Tests that ReviewService.__init__ correctly delegates to the factory."""

    def test_init_uses_passed_fsrs_manager(self):
        """When fsrs_manager is passed, __init__ uses it directly (no factory call)."""
        from app.services.review_service import ReviewService

        mock_mgr = MagicMock()
        svc = ReviewService(
            canvas_service=MagicMock(),
            task_manager=MagicMock(),
            fsrs_manager=mock_mgr,
        )
        assert svc._fsrs_manager is mock_mgr
        assert svc._fsrs_init_ok is True

    def test_init_auto_creates_when_none_and_use_fsrs_true(self):
        """When fsrs_manager=None and USE_FSRS=True, __init__ calls factory."""
        from app.services.review_service import ReviewService

        auto_mgr = MagicMock()
        with patch("app.services.review_service.create_fsrs_manager", return_value=auto_mgr):
            svc = ReviewService(
                canvas_service=MagicMock(),
                task_manager=MagicMock(),
                fsrs_manager=None,
            )
        assert svc._fsrs_manager is auto_mgr
        assert svc._fsrs_init_ok is True

    def test_init_no_fsrs_when_factory_returns_none(self):
        """When fsrs_manager=None and factory returns None (USE_FSRS=False), no FSRS."""
        from app.services.review_service import ReviewService

        with patch("app.services.review_service.create_fsrs_manager", return_value=None):
            svc = ReviewService(
                canvas_service=MagicMock(),
                task_manager=MagicMock(),
                fsrs_manager=None,
            )
        assert svc._fsrs_manager is None
        assert svc._fsrs_init_ok is False
        assert "unavailable" in svc._fsrs_init_reason or "disabled" in svc._fsrs_init_reason
