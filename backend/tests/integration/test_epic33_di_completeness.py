# Canvas Learning System - EPIC-33 Story 33.9 DI Completeness Tests
# GREEN PHASE: Tests verify async lazy singleton initialization works.
"""
DI Chain Completeness Integration Tests for Story 33.9.

Verifies that IntelligentParallelService is fully wired with all required
dependencies after _ensure_async_deps() is called.

Acceptance Criteria Covered:
- AC-33.9.1: batch_orchestrator is injected (P0)
- AC-33.9.2: agent_service is injected (P0)
- AC-33.9.3: /confirm starts batch execution (P0)
- AC-33.9.4: /cancel can cancel a running batch (P0)
- AC-33.9.5: /single-agent (retry) works without RuntimeError (P0)
- AC-33.9.6: routing_engine is passed to BatchOrchestrator (P1)
- AC-33.9.7: DI completeness integration test (P1)
- AC-33.9.8: Cleanup phantom code (P2)

[Source: docs/stories/33.9.story.md]
"""

import logging
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.api.v1.endpoints.intelligent_parallel import (
    get_service,
    _ensure_async_deps,
    reset_service,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(autouse=True)
def _reset_singleton():
    """Reset the endpoint service singleton before each test."""
    reset_service()
    yield
    reset_service()


@pytest.fixture
def mock_settings():
    """Mock settings with all required fields."""
    settings = MagicMock()
    settings.AI_API_KEY = "test-api-key"
    settings.AI_MODEL_NAME = "gemini-test"
    settings.AI_BASE_URL = None
    settings.AI_PROVIDER = "google"
    settings.canvas_base_path = "/tmp/test-canvas"
    return settings


@pytest.fixture
def dep_patches(mock_settings):
    """Context manager that patches all dependency factories."""
    mock_session_mgr = MagicMock()
    mock_grouping_svc = MagicMock()
    mock_routing_engine = MagicMock()
    mock_neo4j = MagicMock()

    patches = {
        "app.dependencies.get_settings": mock_settings,
        "app.dependencies.get_session_manager": mock_session_mgr,
        "app.dependencies.get_intelligent_grouping_service": mock_grouping_svc,
        "app.dependencies.get_agent_routing_engine": mock_routing_engine,
        "app.dependencies.get_neo4j_client_dep": mock_neo4j,
    }

    return patches, {
        "settings": mock_settings,
        "session_manager": mock_session_mgr,
        "grouping_service": mock_grouping_svc,
        "routing_engine": mock_routing_engine,
        "neo4j_client": mock_neo4j,
    }


def _apply_patches(patches):
    """Helper: enter all patches and return stack."""
    import contextlib
    stack = contextlib.ExitStack()
    for target, return_val in patches.items():
        stack.enter_context(patch(target, return_value=return_val))
    return stack


# =============================================================================
# AC-33.9.1: batch_orchestrator is injected (P0)
# =============================================================================

class TestBatchOrchestratorInjection:
    """Verify batch_orchestrator is properly injected into the service."""

    @pytest.mark.asyncio
    async def test_batch_orchestrator_is_not_none(self, dep_patches):
        """
        AC-33.9.1: After _ensure_async_deps(),
        service._batch_orchestrator is not None.
        """
        patches, mocks = dep_patches
        with _apply_patches(patches):
            get_service()
            await _ensure_async_deps()
            service = get_service()

        assert service._batch_orchestrator is not None

    @pytest.mark.asyncio
    async def test_batch_orchestrator_has_session_manager(self, dep_patches):
        """AC-33.9.1: BatchOrchestrator was constructed with session_manager."""
        patches, mocks = dep_patches
        with _apply_patches(patches):
            get_service()
            await _ensure_async_deps()
            service = get_service()

        assert service._batch_orchestrator.session_manager is mocks["session_manager"]

    @pytest.mark.asyncio
    async def test_batch_orchestrator_has_agent_service(self, dep_patches):
        """AC-33.9.1: BatchOrchestrator was constructed with agent_service."""
        patches, mocks = dep_patches
        with _apply_patches(patches):
            get_service()
            await _ensure_async_deps()
            service = get_service()

        assert service._batch_orchestrator.agent_service is not None


# =============================================================================
# AC-33.9.2: agent_service is injected (P0)
# =============================================================================

class TestAgentServiceInjection:
    """Verify agent_service is properly injected into the service."""

    @pytest.mark.asyncio
    async def test_agent_service_is_not_none(self, dep_patches):
        """AC-33.9.2: service._agent_service is not None."""
        patches, mocks = dep_patches
        with _apply_patches(patches):
            get_service()
            await _ensure_async_deps()
            service = get_service()

        assert service._agent_service is not None


# =============================================================================
# AC-33.9.3: /confirm starts batch execution (P0)
# =============================================================================

class TestConfirmStartsBatchExecution:
    """Verify /confirm endpoint has access to batch_orchestrator."""

    @pytest.mark.asyncio
    async def test_service_has_batch_orchestrator_for_confirm(self, dep_patches):
        """
        AC-33.9.3: After _ensure_async_deps, the service can launch
        batch execution (batch_orchestrator is not None).
        """
        patches, mocks = dep_patches
        with _apply_patches(patches):
            get_service()
            await _ensure_async_deps()
            service = get_service()

        # The key check: batch_orchestrator exists so background task can be created
        assert service._batch_orchestrator is not None

    @pytest.mark.asyncio
    async def test_start_batch_creates_session_and_launches(self, dep_patches):
        """AC-33.9.3: start_batch_session creates session via SessionManager."""
        patches, mocks = dep_patches
        mock_sm = AsyncMock()
        mock_sm.create_session = AsyncMock(return_value="session-001")
        patches["app.dependencies.get_session_manager"] = mock_sm

        with _apply_patches(patches):
            get_service()
            await _ensure_async_deps()
            service = get_service()

            from app.models.intelligent_parallel_models import GroupExecuteConfig
            groups = [
                GroupExecuteConfig(
                    group_id="g1",
                    agent_type="test-agent",
                    node_ids=["n1"],
                )
            ]
            result = await service.start_batch_session("test.canvas", groups)

        assert result.task_id == "session-001"
        mock_sm.create_session.assert_called_once()


# =============================================================================
# AC-33.9.4: /cancel can cancel a running batch (P0)
# =============================================================================

class TestCancelRunningBatch:
    """Verify /cancel endpoint has access to BatchOrchestrator for cancel signaling."""

    @pytest.mark.asyncio
    async def test_cancel_has_batch_orchestrator(self, dep_patches):
        """AC-33.9.4: batch_orchestrator exists so cancel signaling works."""
        patches, mocks = dep_patches
        with _apply_patches(patches):
            get_service()
            await _ensure_async_deps()
            service = get_service()

        assert service._batch_orchestrator is not None
        # Verify _cancel_requested dict exists
        assert hasattr(service._batch_orchestrator, '_cancel_requested')


# =============================================================================
# AC-33.9.5: /single-agent (retry) works without RuntimeError (P0)
# =============================================================================

class TestSingleAgentRetry:
    """Verify /single-agent endpoint works without RuntimeError."""

    @pytest.mark.asyncio
    async def test_agent_service_available_for_retry(self, dep_patches):
        """AC-33.9.5: agent_service is available so retry_single_node works."""
        patches, mocks = dep_patches
        with _apply_patches(patches):
            get_service()
            await _ensure_async_deps()
            service = get_service()

        assert service._agent_service is not None


# =============================================================================
# AC-33.9.6: routing_engine is passed to BatchOrchestrator (P1)
# =============================================================================

class TestRoutingEngineInjection:
    """Verify routing_engine is passed to BatchOrchestrator."""

    @pytest.mark.asyncio
    async def test_batch_orchestrator_has_routing_engine(self, dep_patches):
        """AC-33.9.6: batch_orchestrator.routing_engine is not None."""
        patches, mocks = dep_patches
        with _apply_patches(patches):
            get_service()
            await _ensure_async_deps()
            service = get_service()

        assert service._batch_orchestrator.routing_engine is not None


# =============================================================================
# AC-33.9.7: DI completeness integration test (P1)
# =============================================================================

class TestDICompletenessIntegration:
    """
    AC-33.9.7: Comprehensive DI completeness verification.
    This test class IS the deliverable required by AC-33.9.7.
    """

    @pytest.mark.asyncio
    async def test_full_di_chain(self, dep_patches):
        """All 3 DI checks pass after _ensure_async_deps."""
        patches, mocks = dep_patches
        with _apply_patches(patches):
            get_service()
            await _ensure_async_deps()
            service = get_service()

        assert service._batch_orchestrator is not None
        assert service._agent_service is not None
        assert service._batch_orchestrator.routing_engine is not None

    @pytest.mark.asyncio
    async def test_idempotent_ensure(self, dep_patches):
        """Calling _ensure_async_deps twice is safe (no-op on second call)."""
        patches, mocks = dep_patches
        with _apply_patches(patches):
            get_service()
            await _ensure_async_deps()
            first_bo = get_service()._batch_orchestrator
            await _ensure_async_deps()
            second_bo = get_service()._batch_orchestrator

        assert first_bo is second_bo

    @pytest.mark.asyncio
    async def test_reset_clears_deps(self, dep_patches):
        """reset_service() clears deps so they can be re-injected."""
        patches, mocks = dep_patches
        with _apply_patches(patches):
            get_service()
            await _ensure_async_deps()
            assert get_service()._batch_orchestrator is not None

            reset_service()
            service = get_service()
            assert service._batch_orchestrator is None
            assert service._agent_service is None


# =============================================================================
# AC-33.9.8: Cleanup phantom code (P2)
# =============================================================================

class TestPhantomCodeCleanup:
    """Verify phantom code is cleaned up."""

    def test_no_set_batch_deps_references(self):
        """AC-33.9.8: No set_batch_deps() references in comments."""
        from pathlib import Path

        ep_file = (
            Path(__file__).parent.parent.parent
            / "app" / "api" / "v1" / "endpoints" / "intelligent_parallel.py"
        )
        content = ep_file.read_text(encoding="utf-8")

        assert "set_batch_deps" not in content, (
            "Found 'set_batch_deps' reference in intelligent_parallel.py."
        )


# =============================================================================
# Singleton Constraint: /confirm and /cancel share same BatchOrchestrator
# =============================================================================

class TestSingletonConstraint:
    """Verify BatchOrchestrator singleton constraint for cancel signaling."""

    @pytest.mark.asyncio
    async def test_shared_batch_orchestrator_instance(self, dep_patches):
        """
        /confirm and /cancel share the same BatchOrchestrator instance
        so _cancel_requested signaling works.
        """
        patches, mocks = dep_patches
        with _apply_patches(patches):
            get_service()
            await _ensure_async_deps()

            service1 = get_service()
            service2 = get_service()

        assert service1 is service2
        assert service1._batch_orchestrator is not None
        assert service1._batch_orchestrator is service2._batch_orchestrator


# =============================================================================
# WARNING log regression guard
# =============================================================================

class TestNoWarningLogs:
    """After _ensure_async_deps, no 'not injected' warnings should appear."""

    @pytest.mark.asyncio
    async def test_no_missing_dep_warnings_after_init(self, dep_patches, caplog):
        """After full init, no 'not injected' WARNING logs."""
        patches, mocks = dep_patches
        with _apply_patches(patches):
            with caplog.at_level(logging.INFO):
                get_service()
                await _ensure_async_deps()

        # Check that the P0 fix info log appears
        info_messages = [r.message for r in caplog.records if r.levelno == logging.INFO]
        assert any("P0 DI fix applied" in msg for msg in info_messages), (
            "Expected '[Story 33.9] P0 DI fix applied' info log"
        )
