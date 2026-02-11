# Story 38.1: LanceDB Auto-Index Trigger — AC-1 Tests
"""
AC-1: Canvas node create/update auto-triggers LanceDB index
(async, non-blocking, debounce).

Split from test_story_38_1_lancedb_auto_index.py for maintainability.
"""

import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.conftest import yield_to_event_loop


class TestAC1AutoTrigger:
    """AC-1: Canvas node create/update auto-triggers LanceDB index."""

    def test_config_enable_lancedb_auto_index_default_true(self):
        """
        [P0] ENABLE_LANCEDB_AUTO_INDEX defaults to True.

        Verifies: config.py Field(default=True) for auto-index setting.
        """
        from app.config import Settings

        field_info = Settings.model_fields["ENABLE_LANCEDB_AUTO_INDEX"]
        assert field_info.default is True, (
            f"Expected default=True, got {field_info.default}. "
            f"Story 38.1 AC-1: Auto-index must be enabled by default."
        )

    def test_config_debounce_default_500ms(self):
        """
        [P0] LANCEDB_INDEX_DEBOUNCE_MS defaults to 500.

        Verifies: config.py debounce window setting.
        """
        from app.config import Settings

        field_info = Settings.model_fields["LANCEDB_INDEX_DEBOUNCE_MS"]
        assert field_info.default == 500, (
            f"Expected debounce default=500ms, got {field_info.default}. "
            f"Story 38.1: Debounce should prevent rapid re-indexing."
        )

    def test_config_index_timeout_default_5s(self):
        """
        [P0] LANCEDB_INDEX_TIMEOUT defaults to 5.0 seconds.

        Verifies: config.py timeout setting (AC-1: within 5 seconds).
        """
        from app.config import Settings

        field_info = Settings.model_fields["LANCEDB_INDEX_TIMEOUT"]
        assert field_info.default == 5.0, (
            f"Expected timeout default=5.0s, got {field_info.default}. "
            f"Story 38.1 AC-1: Index must complete within 5 seconds."
        )

    @pytest.mark.asyncio
    async def test_schedule_index_creates_async_task(self):
        """
        [P0] schedule_index() creates an async task for debounced indexing.

        Verifies: lancedb_index_service.py schedule_index() creates task.
        """
        from app.services.lancedb_index_service import LanceDBIndexService

        with patch("app.services.lancedb_index_service.settings") as mock_settings:
            mock_settings.ENABLE_LANCEDB_AUTO_INDEX = True
            mock_settings.LANCEDB_INDEX_DEBOUNCE_MS = 500
            mock_settings.LANCEDB_INDEX_TIMEOUT = 5.0

            svc = LanceDBIndexService()
            svc.schedule_index("test_canvas", "/tmp/canvas")
            assert "test_canvas" in svc._pending_tasks
            task = svc._pending_tasks["test_canvas"]
            assert isinstance(task, asyncio.Task)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    def test_schedule_index_disabled_does_nothing(self):
        """
        [P0] schedule_index() is a no-op when ENABLE_LANCEDB_AUTO_INDEX is False.

        Verifies: lancedb_index_service.py L75-76 early return.
        """
        from app.services.lancedb_index_service import LanceDBIndexService

        with patch("app.services.lancedb_index_service.settings") as mock_settings:
            mock_settings.ENABLE_LANCEDB_AUTO_INDEX = False
            mock_settings.LANCEDB_INDEX_DEBOUNCE_MS = 500
            mock_settings.LANCEDB_INDEX_TIMEOUT = 5.0

            svc = LanceDBIndexService()
            # Should not create a task when disabled
            svc.schedule_index("test_canvas", "/tmp/canvas")
            assert len(svc._pending_tasks) == 0

    @pytest.mark.asyncio
    async def test_debounce_cancels_previous_task(self):
        """
        [P1] Rapid schedule_index() calls cancel previous debounce task.

        Verifies: lancedb_index_service.py L78-82 cancel logic.
        """
        from app.services.lancedb_index_service import LanceDBIndexService

        with patch("app.services.lancedb_index_service.settings") as mock_settings:
            mock_settings.ENABLE_LANCEDB_AUTO_INDEX = True
            mock_settings.LANCEDB_INDEX_DEBOUNCE_MS = 5000  # Long debounce for test
            mock_settings.LANCEDB_INDEX_TIMEOUT = 5.0

            svc = LanceDBIndexService()

            svc.schedule_index("test_canvas", "/tmp/canvas")
            first_task = svc._pending_tasks["test_canvas"]

            svc.schedule_index("test_canvas", "/tmp/canvas")
            second_task = svc._pending_tasks["test_canvas"]

            # Allow event loop to process the cancellation
            await yield_to_event_loop(1)

            assert first_task.cancelled() or first_task.done(), (
                "First debounce task should be cancelled when a second update arrives"
            )
            assert second_task is not first_task, (
                "Second call should create a new task"
            )

            # Cleanup
            second_task.cancel()
            try:
                await second_task
            except asyncio.CancelledError:
                pass

    @pytest.mark.asyncio
    async def test_canvas_service_add_node_triggers_lancedb(self):
        """
        [P0][Review M3] CanvasService.add_node() behaviorally calls schedule_index.

        Verifies via mock: add_node -> _trigger_lancedb_index -> schedule_index.
        """
        from app.services.canvas_service import CanvasService

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create minimal canvas file
            canvas_file = Path(tmpdir) / "test.canvas"
            canvas_data = {"nodes": [], "edges": []}
            canvas_file.write_text(json.dumps(canvas_data), encoding="utf-8")

            svc = CanvasService(canvas_base_path=tmpdir)

            mock_index_svc = MagicMock()
            with patch(
                "app.services.lancedb_index_service.get_lancedb_index_service",
                return_value=mock_index_svc,
            ):
                node_data = {
                    "type": "text",
                    "text": "hello",
                    "x": 0, "y": 0, "width": 200, "height": 100,
                }
                result = await svc.add_node(canvas_name="test", node_data=node_data)
                mock_index_svc.schedule_index.assert_called_once_with(
                    "test", tmpdir, trigger_node_id=result["id"]
                )

    @pytest.mark.asyncio
    async def test_canvas_service_update_node_triggers_lancedb(self):
        """
        [P0][Review M3] CanvasService.update_node() behaviorally calls schedule_index.

        Verifies via mock: update_node -> _trigger_lancedb_index -> schedule_index.
        """
        from app.services.canvas_service import CanvasService

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create canvas with one node
            node_id = "node-1"
            canvas_data = {
                "nodes": [{"id": node_id, "type": "text", "text": "old", "x": 0, "y": 0, "width": 200, "height": 100}],
                "edges": [],
            }
            canvas_file = Path(tmpdir) / "test.canvas"
            canvas_file.write_text(json.dumps(canvas_data), encoding="utf-8")

            svc = CanvasService(canvas_base_path=tmpdir)

            mock_index_svc = MagicMock()
            with patch(
                "app.services.lancedb_index_service.get_lancedb_index_service",
                return_value=mock_index_svc,
            ):
                await svc.update_node(
                    canvas_name="test",
                    node_id=node_id,
                    node_data={"text": "new"},
                )
                mock_index_svc.schedule_index.assert_called_once_with(
                    "test", tmpdir, trigger_node_id=node_id
                )

    def test_trigger_lancedb_index_catches_exceptions(self):
        """
        [P0] _trigger_lancedb_index() catches all exceptions (AC-2: no CRUD blocking).

        Verifies: canvas_service.py L345-354 try/except.
        """
        from app.services.canvas_service import CanvasService

        svc = CanvasService(canvas_base_path="/tmp/test")
        # Patch the lazy-imported function at the module level where it's imported
        with patch(
            "app.services.lancedb_index_service.get_lancedb_index_service",
            side_effect=RuntimeError("boom"),
        ):
            # Should not raise — _trigger_lancedb_index catches all exceptions
            svc._trigger_lancedb_index("test_canvas")
