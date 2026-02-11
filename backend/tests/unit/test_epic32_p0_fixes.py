# EPIC-32 P0 阻塞修复单元测试
"""
Tests for 3 P0 fixes:
- P0-1: FSRSManager injected via DI in dependencies.py
- P0-2: Card state persistence to JSON file (survives restart)
- P0-3: rating input validation (non-integer handling)
"""

import json
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock


@pytest.fixture
def mock_canvas_service():
    mock = MagicMock()
    mock.get_canvas = AsyncMock(return_value={"nodes": [], "edges": []})
    return mock


@pytest.fixture
def mock_task_manager():
    mock = MagicMock()
    mock.submit_task = MagicMock(return_value="task_123")
    return mock


# ============================================================
# P0-1: FSRSManager DI injection
# ============================================================

class TestP01FSRSManagerDI:
    """P0-1: FSRSManager should be created and injected in dependencies.py."""

    def test_dependencies_injects_fsrs_manager(self):
        """get_review_service singleton factory should pass fsrs_manager to ReviewService.

        Story 38.9: dependencies.py delegates to services.review_service.get_review_service()
        singleton factory, which is where the actual FSRSManager injection happens.
        """
        import inspect
        from app.services.review_service import get_review_service
        source = inspect.getsource(get_review_service)
        assert "fsrs_manager=" in source, (
            "services/review_service.py get_review_service singleton must pass "
            "fsrs_manager to ReviewService"
        )

    def test_review_service_accepts_fsrs_manager(self, mock_canvas_service, mock_task_manager):
        """ReviewService should accept and store fsrs_manager parameter."""
        mock_fsrs = MagicMock()
        with patch("app.services.review_service.ReviewService._load_card_states", return_value={}):
            from app.services.review_service import ReviewService
            service = ReviewService(
                canvas_service=mock_canvas_service,
                task_manager=mock_task_manager,
                fsrs_manager=mock_fsrs
            )
        assert service._fsrs_manager is mock_fsrs
        assert service._fsrs_init_ok is True

    def test_review_service_fsrs_manager_none_fallback(self, mock_canvas_service, mock_task_manager):
        """When fsrs_manager=None, ReviewService should attempt auto-create."""
        with patch("app.services.review_service.ReviewService._load_card_states", return_value={}):
            from app.services.review_service import ReviewService
            service = ReviewService(
                canvas_service=mock_canvas_service,
                task_manager=mock_task_manager,
                fsrs_manager=None
            )
        # Should still initialize (auto-create or None depending on FSRS_AVAILABLE)
        assert service is not None


# ============================================================
# P0-2: Card state persistence
# ============================================================

class TestP02CardStatePersistence:
    """P0-2: Card states should persist to/from JSON file."""

    def test_load_card_states_empty_when_no_file(self, tmp_path):
        """Should return empty dict when file doesn't exist."""
        with patch("app.services.review_service._CARD_STATES_FILE", tmp_path / "nonexistent.json"):
            from app.services.review_service import ReviewService
            result = ReviewService._load_card_states()
        assert result == {}

    def test_load_card_states_from_file(self, tmp_path):
        """Should load card states from existing JSON file."""
        states = {"concept_a": '{"stability": 1.0}', "concept_b": '{"stability": 2.0}'}
        json_file = tmp_path / "fsrs_card_states.json"
        json_file.write_text(json.dumps(states), encoding="utf-8")

        with patch("app.services.review_service._CARD_STATES_FILE", json_file):
            from app.services.review_service import ReviewService
            result = ReviewService._load_card_states()
        assert result == states
        assert len(result) == 2

    def test_load_card_states_handles_corrupt_file(self, tmp_path):
        """Should return empty dict when file is corrupt."""
        json_file = tmp_path / "fsrs_card_states.json"
        json_file.write_text("NOT VALID JSON{{{", encoding="utf-8")

        with patch("app.services.review_service._CARD_STATES_FILE", json_file):
            from app.services.review_service import ReviewService
            result = ReviewService._load_card_states()
        assert result == {}

    @pytest.mark.asyncio
    async def test_save_card_states_writes_file(self, tmp_path, mock_canvas_service, mock_task_manager):
        """_save_card_states should write to JSON file (now async with atomic write)."""
        json_file = tmp_path / "fsrs_card_states.json"

        with patch("app.services.review_service._CARD_STATES_FILE", json_file):
            with patch("app.services.review_service.ReviewService._load_card_states", return_value={}):
                from app.services.review_service import ReviewService
                service = ReviewService(
                    canvas_service=mock_canvas_service,
                    task_manager=mock_task_manager
                )
            service._card_states = {"concept_x": '{"stability": 3.0}'}
            await service._save_card_states()

        assert json_file.exists()
        loaded = json.loads(json_file.read_text(encoding="utf-8"))
        assert loaded == {"concept_x": '{"stability": 3.0}'}

    @pytest.mark.asyncio
    async def test_save_card_states_survives_restart(self, tmp_path, mock_canvas_service, mock_task_manager):
        """Card states should survive service restart (save then load)."""
        json_file = tmp_path / "fsrs_card_states.json"
        states = {"concept_1": '{"s":1}', "concept_2": '{"s":2}'}

        with patch("app.services.review_service._CARD_STATES_FILE", json_file):
            # First service writes states
            with patch("app.services.review_service.ReviewService._load_card_states", return_value={}):
                from app.services.review_service import ReviewService
                svc1 = ReviewService(
                    canvas_service=mock_canvas_service,
                    task_manager=mock_task_manager
                )
            svc1._card_states = states
            await svc1._save_card_states()

            # Second service (simulating restart) should load them
            result = ReviewService._load_card_states()
        assert result == states


# ============================================================
# P0-3: rating input validation
# ============================================================

class TestP03RatingValidation:
    """P0-3: rating should handle non-integer inputs without crashing."""

    @pytest.fixture
    def review_service(self, mock_canvas_service, mock_task_manager):
        with patch("app.services.review_service.ReviewService._load_card_states", return_value={}):
            from app.services.review_service import ReviewService
            return ReviewService(
                canvas_service=mock_canvas_service,
                task_manager=mock_task_manager
            )

    @pytest.mark.asyncio
    async def test_rating_string_abc_defaults_to_3(self, review_service):
        """rating='abc' should not crash, should default to 3."""
        # Mock FSRS manager to avoid actual FSRS operations
        review_service._fsrs_manager = None
        result = await review_service.record_review_result(
            canvas_name="test_canvas",
            concept_id="test_concept",
            rating="abc"
        )
        # Should not crash; returns a dict with rating = 3
        assert result is not None
        assert result.get("rating") == 3

    @pytest.mark.asyncio
    async def test_rating_float_5_7_clamped_to_4(self, review_service):
        """rating=5.7 should be converted to int(5)=5, then clamped to 4."""
        review_service._fsrs_manager = None
        result = await review_service.record_review_result(
            canvas_name="test_canvas",
            concept_id="test_concept",
            rating=5.7
        )
        assert result is not None
        assert result.get("rating") == 4  # max(1, min(4, 5)) = 4

    @pytest.mark.asyncio
    async def test_rating_none_defaults_to_3(self, review_service):
        """rating=None should default to 3."""
        review_service._fsrs_manager = None
        result = await review_service.record_review_result(
            canvas_name="test_canvas",
            concept_id="test_concept",
            rating=None
        )
        assert result is not None
        assert result.get("rating") == 3

    @pytest.mark.asyncio
    async def test_rating_valid_int_passes_through(self, review_service):
        """rating=2 (valid int) should pass through unchanged."""
        review_service._fsrs_manager = None
        result = await review_service.record_review_result(
            canvas_name="test_canvas",
            concept_id="test_concept",
            rating=2
        )
        assert result is not None
        assert result.get("rating") == 2

    @pytest.mark.asyncio
    async def test_rating_negative_clamped_to_1(self, review_service):
        """rating=-1 should be clamped to 1."""
        review_service._fsrs_manager = None
        result = await review_service.record_review_result(
            canvas_name="test_canvas",
            concept_id="test_concept",
            rating=-1
        )
        assert result is not None
        assert result.get("rating") == 1
