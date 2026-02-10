# Story 38.3: FSRS State Initialization Guarantee - Edge Case Tests
"""
Edge case and boundary tests for Story 38.3.

Covers scenarios not in the primary test file:
- Concurrent access patterns
- Persistence layer failures during auto-creation
- Empty/special concept_id values
- Card state corruption recovery

[Source: docs/implementation-artifacts/story-38.3.md]
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Use shared isolate_card_states_file fixture from conftest.py
pytestmark = pytest.mark.usefixtures("isolate_card_states_file")


class FakeCard:
    """Fake FSRS card for testing."""
    stability = 1.0
    difficulty = 5.0
    reps = 0
    lapses = 0
    last_review = None

    @property
    def state(self):
        return type('State', (), {'value': 0})()


@pytest.fixture
def mock_canvas_service():
    mock = MagicMock()
    mock.get_canvas = AsyncMock(return_value={"nodes": [], "edges": []})
    return mock


@pytest.fixture
def mock_task_manager():
    return MagicMock()


@pytest.fixture
def mock_fsrs_manager():
    mock = MagicMock()
    mock.create_card.return_value = FakeCard()
    mock.serialize_card.return_value = '{"stability":1.0,"difficulty":5.0,"state":0}'
    mock.deserialize_card.return_value = FakeCard()
    mock.get_retrievability.return_value = 1.0
    mock.get_due_date.return_value = None
    return mock


@pytest.fixture
def service(mock_canvas_service, mock_task_manager, mock_fsrs_manager):
    from app.services.review_service import ReviewService
    return ReviewService(
        canvas_service=mock_canvas_service,
        task_manager=mock_task_manager,
        fsrs_manager=mock_fsrs_manager,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# AC-4: Auto-creation edge cases
# ═══════════════════════════════════════════════════════════════════════════════


class TestAutoCreationEdgeCases:
    """Edge cases for AC-4 auto card creation."""

    @pytest.mark.asyncio
    async def test_persistence_load_returns_none(self, service, mock_fsrs_manager):
        """When load_card_state returns None, auto-create kicks in."""
        service.load_card_state = AsyncMock(return_value=None)

        result = await service.get_fsrs_state("no-persist")
        assert result["found"] is True
        mock_fsrs_manager.create_card.assert_called_once()

    @pytest.mark.asyncio
    async def test_persistence_load_returns_empty_string(self, service, mock_fsrs_manager):
        """When load_card_state returns empty string, auto-create kicks in."""
        service.load_card_state = AsyncMock(return_value="")

        result = await service.get_fsrs_state("empty-persist")
        assert result["found"] is True
        mock_fsrs_manager.create_card.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_card_failure_returns_error(self, service, mock_fsrs_manager):
        """When create_card raises, error reason is returned."""
        mock_fsrs_manager.create_card.side_effect = RuntimeError("FSRS internal error")

        result = await service.get_fsrs_state("create-fail")
        assert result["found"] is False
        assert "error" in result["reason"]

    @pytest.mark.asyncio
    async def test_auto_create_caches_in_card_states(self, service, mock_fsrs_manager):
        """After auto-creation, card is stored in _card_states cache."""
        result = await service.get_fsrs_state("cache-test")
        assert result["found"] is True
        assert "cache-test" in service._card_states
        assert service._card_states["cache-test"] == '{"stability":1.0,"difficulty":5.0,"state":0}'


# ═══════════════════════════════════════════════════════════════════════════════
# AC-1: Reason code correctness
# ═══════════════════════════════════════════════════════════════════════════════


class TestReasonCodeEdgeCases:
    """Edge cases for AC-1 reason codes."""

    @pytest.mark.asyncio
    async def test_deserialize_failure_after_persistence_load(self, service, mock_fsrs_manager):
        """When deserialize_card fails on persisted data, error reason returned."""
        service._card_states["corrupt-concept"] = '{"bad json'
        mock_fsrs_manager.deserialize_card.side_effect = ValueError("invalid JSON")

        result = await service.get_fsrs_state("corrupt-concept")
        assert result["found"] is False
        assert "error" in result["reason"]

    @pytest.mark.asyncio
    async def test_get_retrievability_failure_returns_error(self, service, mock_fsrs_manager):
        """When get_retrievability raises, error reason returned."""
        service._card_states["retr-fail"] = '{"valid": true}'
        mock_fsrs_manager.get_retrievability.side_effect = TypeError("cannot compute")

        result = await service.get_fsrs_state("retr-fail")
        assert result["found"] is False
        assert "error" in result["reason"]

    @pytest.mark.asyncio
    async def test_unicode_concept_id(self, service, mock_fsrs_manager):
        """Auto-creation works with unicode concept IDs."""
        result = await service.get_fsrs_state("概念-递归")
        assert result["found"] is True
        assert "概念-递归" in service._card_states

    @pytest.mark.asyncio
    async def test_empty_concept_id(self, service, mock_fsrs_manager):
        """Auto-creation works with empty concept ID (edge case)."""
        result = await service.get_fsrs_state("")
        assert result["found"] is True
        assert "" in service._card_states


# ═══════════════════════════════════════════════════════════════════════════════
# AC-3: Initialization flag consistency
# ═══════════════════════════════════════════════════════════════════════════════


class TestInitFlagConsistency:
    """Tests for _fsrs_init_ok flag consistency."""

    def test_init_ok_true_when_manager_present(self, service):
        """_fsrs_init_ok is True when fsrs_manager is provided."""
        assert service._fsrs_init_ok is True

    def test_init_ok_false_without_manager(self, mock_canvas_service, mock_task_manager):
        """_fsrs_init_ok is False when no FSRS manager."""
        with patch('app.services.review_service.FSRS_AVAILABLE', False):
            with patch('app.services.review_service.FSRSManager', None):
                from app.services.review_service import ReviewService
                svc = ReviewService(
                    canvas_service=mock_canvas_service,
                    task_manager=mock_task_manager,
                    fsrs_manager=None,
                )
        assert svc._fsrs_init_ok is False
        assert svc._fsrs_init_reason is not None

    def test_init_reason_none_when_ok(self, service):
        """_fsrs_init_reason is None when FSRS is available."""
        assert service._fsrs_init_reason is None
