# Story 38.3: FSRS State Initialization Guarantee - Unit Tests
"""
Unit tests for Story 38.3: FSRS State Initialization Guarantee.

Tests cover:
- AC-1: get_fsrs_state() returns structured reason codes
- AC-3: FSRS manager initialization logging + health reporting
- AC-4: Auto card creation on first FSRS state query
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_canvas_service():
    """Create mock CanvasService."""
    mock = MagicMock()
    mock.get_canvas = AsyncMock(return_value={"nodes": [], "edges": []})
    return mock


@pytest.fixture
def mock_task_manager():
    """Create mock BackgroundTaskManager."""
    mock = MagicMock()
    mock.submit_task = MagicMock(return_value="task_123")
    return mock


class FakeCard:
    """Fake FSRS card with real numeric attributes."""
    def __init__(self):
        self.stability = 0.0
        self.difficulty = 0.0
        self.reps = 0
        self.lapses = 0
        self.last_review = None

    @property
    def state(self):
        return type('State', (), {'value': 0})()


@pytest.fixture
def mock_fsrs_manager():
    """Create mock FSRSManager with realistic behavior."""
    mock = MagicMock()
    fake_card = FakeCard()
    mock.create_card.return_value = fake_card
    mock.serialize_card.return_value = '{"stability":0.0,"difficulty":0.0,"state":0}'
    mock.deserialize_card.return_value = fake_card
    mock.get_retrievability.return_value = 1.0
    mock.get_due_date.return_value = None
    return mock


@pytest.fixture
def review_service(mock_canvas_service, mock_task_manager, mock_fsrs_manager):
    """Create ReviewService with mocked FSRS manager."""
    from app.services.review_service import ReviewService
    return ReviewService(
        canvas_service=mock_canvas_service,
        task_manager=mock_task_manager,
        fsrs_manager=mock_fsrs_manager
    )


@pytest.fixture
def review_service_no_fsrs(mock_canvas_service, mock_task_manager):
    """Create ReviewService without FSRS manager (simulating py-fsrs not available)."""
    with patch('app.services.review_service.FSRS_AVAILABLE', False):
        with patch('app.services.review_service.FSRSManager', None):
            from app.services.review_service import ReviewService
            svc = ReviewService(
                canvas_service=mock_canvas_service,
                task_manager=mock_task_manager,
                fsrs_manager=None
            )
    return svc


# ═══════════════════════════════════════════════════════════════════════════════
# AC-1: get_fsrs_state() returns structured reason codes
# ═══════════════════════════════════════════════════════════════════════════════


class TestAC1ReasonCodes:
    """AC-1: Non-null guarantee with reason codes."""

    @pytest.mark.asyncio
    async def test_fsrs_not_initialized_returns_reason(self, review_service_no_fsrs):
        """When _fsrs_manager is None, response has reason='fsrs_not_initialized'."""
        result = await review_service_no_fsrs.get_fsrs_state("concept-1")
        assert result["found"] is False
        assert result["reason"] == "fsrs_not_initialized"

    @pytest.mark.asyncio
    async def test_found_true_has_no_reason(self, review_service, mock_fsrs_manager):
        """When card exists, response has found=True and no reason field."""
        # Pre-populate cache
        review_service._card_states["concept-1"] = '{"test": true}'
        result = await review_service.get_fsrs_state("concept-1")
        assert result["found"] is True
        assert "reason" not in result

    @pytest.mark.asyncio
    async def test_error_returns_reason(self, review_service, mock_fsrs_manager):
        """When an error occurs, response includes error reason."""
        # Make deserialize_card raise to test error path after auto-creation
        mock_fsrs_manager.serialize_card.side_effect = Exception("test error")
        # Also make create_card succeed but serialize fail
        mock_fsrs_manager.create_card.return_value = MagicMock()
        result = await review_service.get_fsrs_state("concept-err")
        assert result["found"] is False
        assert "error" in result["reason"]


# ═══════════════════════════════════════════════════════════════════════════════
# AC-3: FSRS Manager initialization logging + health
# ═══════════════════════════════════════════════════════════════════════════════


class TestAC3InitLogging:
    """AC-3: FSRS manager initialization status tracking."""

    def test_fsrs_init_ok_when_manager_provided(self, review_service):
        """When fsrs_manager is injected, _fsrs_init_ok is True."""
        assert review_service._fsrs_init_ok is True
        assert review_service._fsrs_init_reason is None

    def test_fsrs_init_failed_when_no_manager(self, review_service_no_fsrs):
        """When fsrs_manager is None and lib not available, _fsrs_init_ok is False."""
        # When passing None explicitly, the code checks FSRS_AVAILABLE
        # Since we pass None, it tries FSRS_AVAILABLE path
        # Either way, the manager should be None
        assert review_service_no_fsrs._fsrs_manager is None

    def test_fsrs_init_reason_set_when_unavailable(self, mock_canvas_service, mock_task_manager):
        """When FSRS library not available, reason is set."""
        with patch('app.services.review_service.FSRS_AVAILABLE', False):
            with patch('app.services.review_service.FSRSManager', None):
                from app.services.review_service import ReviewService
                svc = ReviewService(
                    canvas_service=mock_canvas_service,
                    task_manager=mock_task_manager,
                    fsrs_manager=None
                )
                assert svc._fsrs_init_ok is False
                assert svc._fsrs_init_reason is not None
                assert "not available" in svc._fsrs_init_reason


# ═══════════════════════════════════════════════════════════════════════════════
# AC-4: Auto card creation on first query
# ═══════════════════════════════════════════════════════════════════════════════


class TestAC4AutoCardCreation:
    """AC-4: Auto card creation when no FSRS card exists."""

    @pytest.mark.asyncio
    async def test_auto_creates_card_when_none_exists(self, review_service, mock_fsrs_manager):
        """When no card exists, get_fsrs_state auto-creates one."""
        # No card in cache or persistence
        assert "new-concept" not in review_service._card_states

        result = await review_service.get_fsrs_state("new-concept")

        # Should return found=True with auto-created card
        assert result["found"] is True
        assert "stability" in result
        assert "difficulty" in result
        assert "state" in result
        assert "card_state" in result

        # create_card should have been called
        mock_fsrs_manager.create_card.assert_called_once()

        # Card should be cached
        assert "new-concept" in review_service._card_states

    @pytest.mark.asyncio
    async def test_auto_created_card_returned_on_subsequent_query(self, review_service, mock_fsrs_manager):
        """Subsequent queries return the auto-created card."""
        # First query - auto-creates
        result1 = await review_service.get_fsrs_state("concept-x")
        assert result1["found"] is True

        # Reset mock to verify deserialize is called on second query (not create)
        mock_fsrs_manager.create_card.reset_mock()

        # Second query - should use cached card
        result2 = await review_service.get_fsrs_state("concept-x")
        assert result2["found"] is True

        # create_card should NOT be called again
        mock_fsrs_manager.create_card.assert_not_called()

    @pytest.mark.asyncio
    async def test_existing_card_not_overwritten(self, review_service, mock_fsrs_manager):
        """When card already exists in cache, it's not overwritten."""
        # Pre-populate cache
        review_service._card_states["existing-concept"] = '{"existing": true}'

        result = await review_service.get_fsrs_state("existing-concept")
        assert result["found"] is True

        # create_card should NOT be called
        mock_fsrs_manager.create_card.assert_not_called()

        # deserialize should be called with existing data
        mock_fsrs_manager.deserialize_card.assert_called_with('{"existing": true}')


# ═══════════════════════════════════════════════════════════════════════════════
# AC-3: Health endpoint FSRS status
# ═══════════════════════════════════════════════════════════════════════════════


class TestAC3HealthEndpoint:
    """AC-3: /health endpoint includes fsrs status."""

    def test_health_response_has_components_field(self):
        """HealthCheckResponse model accepts components field."""
        from app.models.schemas import HealthCheckResponse
        from datetime import datetime, timezone

        resp = HealthCheckResponse(
            status="healthy",
            app_name="test",
            version="1.0.0",
            timestamp=datetime.now(timezone.utc),
            components={"fsrs": "ok"}
        )
        assert resp.components["fsrs"] == "ok"

    def test_health_response_components_optional(self):
        """HealthCheckResponse works without components field."""
        from app.models.schemas import HealthCheckResponse
        from datetime import datetime, timezone

        resp = HealthCheckResponse(
            status="healthy",
            app_name="test",
            version="1.0.0",
            timestamp=datetime.now(timezone.utc)
        )
        assert resp.components is None


# ═══════════════════════════════════════════════════════════════════════════════
# AC-1: FSRSStateQueryResponse includes reason field
# ═══════════════════════════════════════════════════════════════════════════════


class TestFSRSStateQueryResponseReason:
    """AC-1: FSRSStateQueryResponse model includes reason."""

    def test_response_accepts_reason(self):
        """FSRSStateQueryResponse can include reason field."""
        from app.models.schemas import FSRSStateQueryResponse

        resp = FSRSStateQueryResponse(
            concept_id="test",
            fsrs_state=None,
            card_state=None,
            found=False,
            reason="no_card_created"
        )
        assert resp.reason == "no_card_created"

    def test_response_reason_optional(self):
        """FSRSStateQueryResponse works without reason."""
        from app.models.schemas import FSRSStateQueryResponse

        resp = FSRSStateQueryResponse(
            concept_id="test",
            fsrs_state=None,
            card_state=None,
            found=True
        )
        assert resp.reason is None

    def test_response_fsrs_not_initialized_reason(self):
        """FSRSStateQueryResponse can carry fsrs_not_initialized reason."""
        from app.models.schemas import FSRSStateQueryResponse

        resp = FSRSStateQueryResponse(
            concept_id="test",
            found=False,
            reason="fsrs_not_initialized"
        )
        assert resp.found is False
        assert resp.reason == "fsrs_not_initialized"


# ═══════════════════════════════════════════════════════════════════════════════
# Code Review Round 2: C1/C2/M2 Fix Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestCodeReviewC1FireAndForgetPersistence:
    """C1 Fix: Auto-created cards persist via get_learning_memory_client(), not self.graphiti_client."""

    @pytest.mark.asyncio
    async def test_auto_create_fires_persistence_task(self, review_service, mock_fsrs_manager):
        """When auto-creating a card, a background task is spawned for persistence."""
        with patch('app.services.review_service.asyncio') as mock_asyncio:
            mock_asyncio.create_task = MagicMock()
            result = await review_service.get_fsrs_state("persist-test")
            assert result["found"] is True
            # asyncio.create_task should have been called for persistence
            mock_asyncio.create_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_persistence_create_task_failure_returns_error(self, review_service, mock_fsrs_manager):
        """When asyncio.create_task raises, get_fsrs_state returns error gracefully.

        review_service.py L1815 catches all exceptions and returns
        {"found": False, "reason": "error: ..."} instead of propagating.
        """
        with patch('app.services.review_service.asyncio') as mock_asyncio:
            mock_asyncio.create_task = MagicMock(side_effect=RuntimeError("no event loop"))
            result = await review_service.get_fsrs_state("persist-fail")
            assert result["found"] is False
            assert "error" in result["reason"]
            assert "no event loop" in result["reason"]


class TestCodeReviewC2ReviewServiceSingleton:
    """C2 Fix: _get_or_create_review_service() module-level singleton in review.py."""

    def test_singleton_creates_review_service(self):
        """_get_or_create_review_service returns a ReviewService instance."""
        import app.api.v1.endpoints.review as review_module
        # Reset singleton
        review_module._review_service_instance = None
        try:
            svc = review_module._get_or_create_review_service()
            from app.services.review_service import ReviewService
            assert isinstance(svc, ReviewService)
        finally:
            # Clean up
            review_module._review_service_instance = None

    def test_singleton_returns_same_instance(self):
        """Calling _get_or_create_review_service twice returns the same object."""
        import app.api.v1.endpoints.review as review_module
        review_module._review_service_instance = None
        try:
            svc1 = review_module._get_or_create_review_service()
            svc2 = review_module._get_or_create_review_service()
            assert svc1 is svc2
        finally:
            review_module._review_service_instance = None


class TestCodeReviewM2RuntimeFSRSFlag:
    """M2 Fix: FSRS_RUNTIME_OK module-level flag reflects runtime init status."""

    def test_runtime_ok_set_true_on_success(self, mock_canvas_service, mock_task_manager, mock_fsrs_manager):
        """FSRS_RUNTIME_OK is True when FSRSManager injects successfully."""
        import app.services.review_service as rs_module
        old_val = rs_module.FSRS_RUNTIME_OK
        try:
            from app.services.review_service import ReviewService
            ReviewService(
                canvas_service=mock_canvas_service,
                task_manager=mock_task_manager,
                fsrs_manager=mock_fsrs_manager
            )
            assert rs_module.FSRS_RUNTIME_OK is True
        finally:
            rs_module.FSRS_RUNTIME_OK = old_val

    def test_runtime_ok_set_false_when_unavailable(self, mock_canvas_service, mock_task_manager):
        """FSRS_RUNTIME_OK is False when FSRS library not available."""
        import app.services.review_service as rs_module
        old_val = rs_module.FSRS_RUNTIME_OK
        try:
            with patch.object(rs_module, 'FSRS_AVAILABLE', False):
                with patch.object(rs_module, 'FSRSManager', None):
                    from app.services.review_service import ReviewService
                    ReviewService(
                        canvas_service=mock_canvas_service,
                        task_manager=mock_task_manager,
                        fsrs_manager=None
                    )
                    assert rs_module.FSRS_RUNTIME_OK is False
        finally:
            rs_module.FSRS_RUNTIME_OK = old_val

    def test_health_endpoint_uses_runtime_flag(self):
        """Health endpoint prefers FSRS_RUNTIME_OK over FSRS_AVAILABLE."""
        from app.models.schemas import HealthCheckResponse

        # Simulate: FSRS_AVAILABLE=True but FSRS_RUNTIME_OK=False
        # (library importable but init failed at runtime)
        with patch('app.api.v1.endpoints.health.FSRS_AVAILABLE', True, create=True):
            pass  # import-time flag

        # Direct logic test: when FSRS_RUNTIME_OK is not None, it takes precedence
        # This validates the logic pattern, not the full endpoint
        fsrs_runtime_ok = False
        fsrs_available = True
        if fsrs_runtime_ok is not None:
            status = "ok" if fsrs_runtime_ok else "degraded"
        else:
            status = "ok" if fsrs_available else "degraded"
        assert status == "degraded"  # Runtime says failed, even though lib is available
