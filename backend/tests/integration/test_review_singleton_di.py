# Story 38.9: ReviewService Singleton DI Completeness Test
"""
Integration test verifying that services/review_service.py's singleton factory
(get_review_service) creates ReviewService with the correct parameters.

Story 38.9 supersedes the old review.py module-level singleton
(_get_or_create_review_service). The canonical singleton now lives in
services/review_service.py, and both dependencies.py and review.py
delegate to it.

Tests:
1. Singleton passes all 4 constructor args (canvas_service, task_manager,
   graphiti_client, fsrs_manager)
2. CanvasService receives memory_client (P0 EPIC-36 fix)
3. fire-and-forget _auto_persist_failures counter is initialized
4. ReviewServiceDep in dependencies.py is not used by review.py endpoints
5. Singleton returns same instance on repeated calls
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def _isolate_review_singleton():
    """Reset the services-layer ReviewService singleton before/after each test."""
    from app.services.review_service import reset_review_service_singleton
    reset_review_service_singleton()
    yield
    reset_review_service_singleton()


class TestReviewSingletonDICompleteness:
    """Verify get_review_service() injects all dependencies (Story 38.9 AC5)."""

    @pytest.mark.asyncio
    async def test_singleton_passes_all_four_constructor_args(self):
        """AC-5: Singleton must pass canvas_service, task_manager,
        graphiti_client, fsrs_manager — matching the ReviewService constructor."""
        import app.services.review_service as rs_mod

        captured_kwargs = {}

        class FakeReviewService:
            def __init__(self, **kwargs):
                captured_kwargs.update(kwargs)

        # Patch at source for lazy imports inside get_review_service()
        with (
            patch.object(rs_mod, "ReviewService", FakeReviewService),
            patch.object(rs_mod, "create_fsrs_manager", return_value=MagicMock(name="fsrs_manager")),
            patch("app.services.canvas_service.CanvasService", return_value=MagicMock(name="canvas_service")),
            patch("app.services.background_task_manager.BackgroundTaskManager", return_value=MagicMock(name="task_manager")),
            patch(
                "app.dependencies.get_graphiti_temporal_client",
                return_value=MagicMock(name="graphiti_client"),
            ),
            patch(
                "app.services.memory_service.get_memory_service",
                new_callable=AsyncMock,
                return_value=MagicMock(name="memory_service"),
            ),
        ):
            from app.services.review_service import get_review_service
            await get_review_service()

        expected_keys = {"canvas_service", "task_manager", "graphiti_client", "fsrs_manager"}
        actual_keys = set(captured_kwargs.keys())
        assert expected_keys == actual_keys, (
            f"ReviewService constructor args mismatch.\n"
            f"  Expected: {expected_keys}\n"
            f"  Actual:   {actual_keys}\n"
            f"  Missing:  {expected_keys - actual_keys}\n"
            f"  Extra:    {actual_keys - expected_keys}"
        )

    @pytest.mark.asyncio
    async def test_canvas_service_receives_memory_client(self):
        """AC-5: CanvasService in singleton must receive memory_client
        (P0 fix from EPIC-36)."""
        import app.services.review_service as rs_mod

        canvas_init_kwargs = {}

        class SpyCanvasService:
            def __init__(self, **kwargs):
                canvas_init_kwargs.update(kwargs)

        # Patch at source for lazy imports inside get_review_service()
        with (
            patch("app.services.canvas_service.CanvasService", SpyCanvasService),
            patch.object(rs_mod, "create_fsrs_manager", return_value=None),
            patch("app.services.background_task_manager.BackgroundTaskManager", return_value=MagicMock()),
            patch.object(rs_mod, "ReviewService", MagicMock()),
            patch(
                "app.dependencies.get_graphiti_temporal_client",
                return_value=None,
            ),
            patch(
                "app.services.memory_service.get_memory_service",
                new_callable=AsyncMock,
                return_value=MagicMock(name="memory_service"),
            ),
        ):
            from app.services.review_service import get_review_service
            await get_review_service()

        assert "memory_client" in canvas_init_kwargs, (
            "CanvasService must receive memory_client parameter. "
            "Without it, EPIC-36 edge sync to Neo4j will silently skip."
        )

    def test_auto_persist_failures_counter_initialized(self):
        """AC-5 + AC-3: ReviewService must have _auto_persist_failures counter."""
        from app.services.review_service import ReviewService

        mock_canvas = MagicMock()
        mock_task_mgr = MagicMock()

        with patch("app.services.review_service.create_fsrs_manager", return_value=None):
            svc = ReviewService(
                canvas_service=mock_canvas,
                task_manager=mock_task_mgr,
            )

        assert hasattr(svc, "_auto_persist_failures"), (
            "ReviewService must have _auto_persist_failures counter "
            "for fire-and-forget observability (Story 32.10 AC-3)"
        )
        assert svc._auto_persist_failures == 0

    def test_review_service_dep_not_used_in_review_endpoints(self):
        """AC-4: ReviewServiceDep should not appear in review.py endpoint signatures."""
        import inspect
        import app.api.v1.endpoints.review as review_mod

        source = inspect.getsource(review_mod)
        assert "ReviewServiceDep" not in source, (
            "review.py should not import or use ReviewServiceDep. "
            "All endpoints use the services-layer singleton via _get_review_service_singleton()."
        )

    @pytest.mark.asyncio
    async def test_singleton_returns_same_instance_on_repeated_calls(self):
        """Singleton must return the same ReviewService instance."""
        with (
            patch(
                "app.services.review_service.create_fsrs_manager",
                return_value=None,
            ),
            patch(
                "app.dependencies.get_graphiti_temporal_client",
                return_value=None,
            ),
        ):
            from app.services.review_service import get_review_service
            svc1 = await get_review_service()
            svc2 = await get_review_service()

        assert svc1 is svc2, "Must return the same singleton instance"
