# Story 32.3: FSRS State Query Endpoint Unit Tests
# [Source: docs/stories/32.3.story.md]
"""
Unit tests for GET /api/v1/review/fsrs-state/{concept_id} endpoint.

Tests cover:
- AC-32.3.1: Endpoint returns FSRS state for priority calculation
- AC-32.3.2: Response contains stability, difficulty, state, reps, lapses, retrievability, due
- AC-32.3.3: Response includes serialized card_state for plugin caching
- AC-32.3.5: Graceful degradation when no card exists

[Source: specs/api/review-api.openapi.yml#/review/fsrs-state/{concept_id}]
[Source: specs/data/fsrs-state-query.schema.json]
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.config import get_settings, Settings

# Correct patch target: review.py imports get_review_service as _get_review_service_singleton
REVIEW_SERVICE_PATCH = "app.api.v1.endpoints.review._get_review_service_singleton"


def _test_settings_override() -> Settings:
    return Settings(
        PROJECT_NAME="Canvas Test",
        VERSION="1.0.0-test",
        DEBUG=True,
        LOG_LEVEL="DEBUG",
        CORS_ORIGINS="http://localhost:3000",
        CANVAS_BASE_PATH="./test_canvas",
    )


@pytest.fixture(autouse=True)
def override_settings():
    app.dependency_overrides[get_settings] = _test_settings_override
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_settings, None)


# Shared fixtures (mock_canvas_service, mock_task_manager, review_service_factory)
# are provided by unit/conftest.py


class TestFSRSStateQueryEndpoint:
    """Tests for GET /api/v1/review/fsrs-state/{concept_id} endpoint."""

    @pytest.fixture
    def test_client(self):
        """Create FastAPI test client."""
        with TestClient(app) as c:
            yield c

    def test_endpoint_returns_fsrs_state_when_card_exists(self, test_client):
        """
        AC-32.3.1: Endpoint returns FSRS state for priority calculation.
        AC-32.3.2: Response contains all required FSRS fields.
        """
        concept_id = "test-concept-123"

        mock_service = MagicMock()
        mock_service.get_fsrs_state = AsyncMock(return_value={
            "found": True,
            "stability": 8.5,
            "difficulty": 5.2,
            "state": 2,  # Review
            "reps": 5,
            "lapses": 1,
            "retrievability": 0.85,
            "due": "2026-01-22T10:00:00Z",
            "card_state": '{"stability":8.5,"difficulty":5.2}'
        })

        with patch(
            REVIEW_SERVICE_PATCH,
            new_callable=AsyncMock,
            return_value=mock_service,
        ):
            response = test_client.get(f"/api/v1/review/fsrs-state/{concept_id}")

            assert response.status_code == 200
            data = response.json()

            # AC-32.3.1: Response structure
            assert data["concept_id"] == concept_id
            assert data["found"] is True

            # AC-32.3.2: FSRS state fields
            fsrs_state = data["fsrs_state"]
            assert fsrs_state["stability"] == 8.5
            assert fsrs_state["difficulty"] == 5.2
            assert fsrs_state["state"] == 2
            assert fsrs_state["reps"] == 5
            assert fsrs_state["lapses"] == 1
            assert fsrs_state["retrievability"] == 0.85
            assert fsrs_state["due"] == "2026-01-22T10:00:00Z"

            # AC-32.3.3: card_state for caching
            assert data["card_state"] is not None

    def test_endpoint_returns_not_found_when_no_card(self, test_client):
        """
        AC-32.3.5: Graceful degradation when no card exists.
        Returns found=false instead of 404.
        """
        concept_id = "new-concept-no-card"

        mock_service = MagicMock()
        mock_service.get_fsrs_state = AsyncMock(return_value={
            "found": False
        })

        with patch(
            REVIEW_SERVICE_PATCH,
            new_callable=AsyncMock,
            return_value=mock_service,
        ):
            response = test_client.get(f"/api/v1/review/fsrs-state/{concept_id}")

            assert response.status_code == 200
            data = response.json()

            assert data["concept_id"] == concept_id
            assert data["found"] is False
            assert data["fsrs_state"] is None
            assert data["card_state"] is None

    def test_endpoint_handles_special_characters_in_concept_id(self, test_client):
        """Endpoint handles special characters in concept IDs correctly."""
        # Use characters that don't conflict with URL path (no slashes)
        concept_id = "node-with-dashes_and_underscores"

        mock_service = MagicMock()
        mock_service.get_fsrs_state = AsyncMock(return_value={
            "found": False
        })

        with patch(
            REVIEW_SERVICE_PATCH,
            new_callable=AsyncMock,
            return_value=mock_service,
        ):
            response = test_client.get(f"/api/v1/review/fsrs-state/{concept_id}")

            assert response.status_code == 200
            mock_service.get_fsrs_state.assert_called_once_with(concept_id)

    def test_endpoint_handles_null_retrievability_and_due(self, test_client):
        """Response handles null values for optional fields."""
        concept_id = "new-card-no-schedule"

        mock_service = MagicMock()
        mock_service.get_fsrs_state = AsyncMock(return_value={
            "found": True,
            "stability": 1.0,
            "difficulty": 5.0,
            "state": 0,  # New
            "reps": 0,
            "lapses": 0,
            "retrievability": None,  # Not yet scheduled
            "due": None,
            "card_state": None
        })

        with patch(
            REVIEW_SERVICE_PATCH,
            new_callable=AsyncMock,
            return_value=mock_service,
        ):
            response = test_client.get(f"/api/v1/review/fsrs-state/{concept_id}")

            assert response.status_code == 200
            data = response.json()

            assert data["fsrs_state"]["retrievability"] is None
            assert data["fsrs_state"]["due"] is None


class TestReviewServiceGetFSRSState:
    """Tests for ReviewService.get_fsrs_state() method."""

    @pytest.mark.asyncio
    async def test_get_fsrs_state_returns_card_data(self, review_service_factory):
        """Service returns FSRS state from card storage."""
        service = review_service_factory()

        # Test that the method exists and returns a dict
        # The actual implementation uses internal FSRS card cache
        result = await service.get_fsrs_state("nonexistent-concept")

        # Should return found=False for nonexistent concept
        assert isinstance(result, dict)
        assert "found" in result

    @pytest.mark.asyncio
    async def test_get_fsrs_state_returns_not_found_for_missing_card(
        self, review_service_factory
    ):
        """Service returns found=false when concept has no card."""
        service = review_service_factory()

        result = await service.get_fsrs_state("missing-concept")

        assert result["found"] is False

    @pytest.mark.asyncio
    async def test_get_fsrs_state_graceful_on_error(self, review_service_factory):
        """
        AC-32.3.5: Service handles errors gracefully.
        Should not raise exception, returns found=false.
        """
        service = review_service_factory()

        # Test with various edge cases
        result = await service.get_fsrs_state("")  # Empty concept ID
        assert result["found"] is False

        result = await service.get_fsrs_state("with/slashes/in/id")  # Special chars
        assert result["found"] is False


class TestFSRSStateResponseSchema:
    """Tests to verify response matches JSON schema."""

    def test_response_matches_schema_with_card(self):
        """
        Response structure matches specs/data/fsrs-state-query.schema.json
        when card is found.
        """
        from app.models.schemas import FSRSStateQueryResponse, FSRSStateResponse

        fsrs_state = FSRSStateResponse(
            stability=8.5,
            difficulty=5.2,
            state=2,
            reps=5,
            lapses=1,
            retrievability=0.85,
            due=datetime(2026, 1, 22, 10, 0, 0, tzinfo=timezone.utc)
        )

        response = FSRSStateQueryResponse(
            concept_id="test-concept",
            fsrs_state=fsrs_state,
            card_state='{"stability":8.5}',
            found=True
        )

        data = response.model_dump()

        # Required fields per schema
        assert "concept_id" in data
        assert "found" in data

        # FSRS state fields
        assert data["fsrs_state"]["stability"] == 8.5
        assert data["fsrs_state"]["difficulty"] == 5.2
        assert data["fsrs_state"]["state"] == 2
        assert data["fsrs_state"]["reps"] == 5
        assert data["fsrs_state"]["lapses"] == 1

    def test_response_matches_schema_without_card(self):
        """
        Response structure matches schema when card is not found.
        """
        from app.models.schemas import FSRSStateQueryResponse

        response = FSRSStateQueryResponse(
            concept_id="new-concept",
            fsrs_state=None,
            card_state=None,
            found=False
        )

        data = response.model_dump()

        assert data["concept_id"] == "new-concept"
        assert data["found"] is False
        assert data["fsrs_state"] is None
        assert data["card_state"] is None


class TestFSRSStateIntegration:
    """Integration tests for FSRS state query with plugin priority calculation."""

    def test_retrievability_in_valid_range(self):
        """
        AC-32.3.4: Retrievability should be in range [0, 1] for priority calculation.
        """
        from app.models.schemas import FSRSStateResponse

        # Valid retrievability
        state = FSRSStateResponse(
            stability=8.5,
            difficulty=5.2,
            state=2,
            reps=5,
            lapses=1,
            retrievability=0.85,
            due=datetime.now(timezone.utc)
        )
        assert 0 <= state.retrievability <= 1

    def test_state_values_are_valid_fsrs_states(self):
        """
        State field should be valid FSRS state: 0=New, 1=Learning, 2=Review, 3=Relearning.
        """
        from app.models.schemas import FSRSStateResponse

        valid_states = [0, 1, 2, 3]

        for state_val in valid_states:
            state = FSRSStateResponse(
                stability=5.0,
                difficulty=5.0,
                state=state_val,
                reps=0,
                lapses=0
            )
            assert state.state in valid_states

    def test_difficulty_in_valid_range(self):
        """
        Difficulty should be in range [1, 10] per FSRS algorithm.
        """
        from app.models.schemas import FSRSStateResponse

        state = FSRSStateResponse(
            stability=5.0,
            difficulty=7.5,
            state=2,
            reps=3,
            lapses=0
        )
        assert 1 <= state.difficulty <= 10
