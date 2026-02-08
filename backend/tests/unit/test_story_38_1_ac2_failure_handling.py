# Story 38.1: LanceDB Auto-Index Trigger — AC-2 Tests
"""
AC-2: Index failure does not block CRUD; 3 retries with exponential backoff;
WARNING log on failure; pending persisted to JSONL.

Split from test_story_38_1_lancedb_auto_index.py for maintainability.
"""

import json
import logging
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestAC2FailureHandling:
    """AC-2: Index failure does not block CRUD; retry and WARNING log."""

    @pytest.mark.asyncio
    async def test_do_index_with_retry_has_3_attempts(self):
        """
        [P0] _do_index_with_retry uses tenacity with 3 attempts.

        Verifies: lancedb_index_service.py L193-198 @retry decorator.
        The decorator uses reraise=True, so the original exception is raised.
        """
        from app.services.lancedb_index_service import LanceDBIndexService

        with patch("app.services.lancedb_index_service.settings") as mock_settings:
            mock_settings.ENABLE_LANCEDB_AUTO_INDEX = True
            mock_settings.LANCEDB_INDEX_DEBOUNCE_MS = 100
            mock_settings.LANCEDB_INDEX_TIMEOUT = 5.0

            svc = LanceDBIndexService()

            call_count = 0

            async def failing_index(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                raise ConnectionError("LanceDB unavailable")

            svc._do_index = failing_index

            # tenacity reraise=True re-raises the original exception
            with pytest.raises(ConnectionError):
                await svc._do_index_with_retry("test_canvas", "/tmp/canvas")

            assert call_count == 3, (
                f"Expected 3 retry attempts, got {call_count}. "
                f"Story 38.1 AC-2: max 3 attempts with exponential backoff."
            )

    @pytest.mark.asyncio
    async def test_failed_index_emits_warning_log(self, caplog):
        """
        [P1] Failed index update emits WARNING log with node ID.

        Expected: "LanceDB index update failed for node {id}, queued for retry"
        Verifies: lancedb_index_service.py L187-191
        """
        from app.services.lancedb_index_service import LanceDBIndexService

        with patch("app.services.lancedb_index_service.settings") as mock_settings:
            mock_settings.ENABLE_LANCEDB_AUTO_INDEX = True
            mock_settings.LANCEDB_INDEX_DEBOUNCE_MS = 0  # No debounce for fast test
            mock_settings.LANCEDB_INDEX_TIMEOUT = 5.0

            svc = LanceDBIndexService()
            svc._do_index_with_retry = AsyncMock(
                side_effect=Exception("connection refused")
            )
            # Mock _persist_pending to avoid file I/O
            svc._persist_pending = MagicMock()

            with caplog.at_level(logging.WARNING):
                await svc._debounced_index("my_canvas", "/tmp/canvas")

            warning_messages = [
                r.message for r in caplog.records if r.levelno >= logging.WARNING
            ]
            assert any(
                "LanceDB index update failed" in msg and "my_canvas" in msg
                for msg in warning_messages
            ), (
                f"Expected WARNING with 'LanceDB index update failed for node my_canvas'. "
                f"Got: {warning_messages}"
            )

    @pytest.mark.asyncio
    async def test_failed_index_persists_to_jsonl(self):
        """
        [P0] Failed index update is persisted to JSONL for later recovery.

        Verifies: lancedb_index_service.py _persist_pending() writes to JSONL.
        """
        from app.services.lancedb_index_service import LanceDBIndexService

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("app.services.lancedb_index_service.settings") as mock_settings:
                mock_settings.ENABLE_LANCEDB_AUTO_INDEX = True
                mock_settings.LANCEDB_INDEX_DEBOUNCE_MS = 100
                mock_settings.LANCEDB_INDEX_TIMEOUT = 5.0

                svc = LanceDBIndexService()
                svc._pending_file = Path(tmpdir) / "pending.jsonl"

                svc._persist_pending("test_canvas", "connection error")

                assert svc._pending_file.exists(), (
                    "Pending JSONL file should be created"
                )

                content = svc._pending_file.read_text(encoding="utf-8").strip()
                entry = json.loads(content)
                assert entry["canvas_name"] == "test_canvas"
                assert entry["error"] == "connection error"
                assert "timestamp" in entry

    @pytest.mark.asyncio
    async def test_crud_succeeds_even_when_index_fails(self):
        """
        [P0] Canvas CRUD operation succeeds even when LanceDB index fails.

        Verifies: canvas_service.py _trigger_lancedb_index catches exceptions.
        """
        from app.services.canvas_service import CanvasService

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a minimal canvas file
            canvas_path = Path(tmpdir) / "test.canvas"
            canvas_data = {
                "nodes": [],
                "edges": [],
            }
            canvas_path.write_text(json.dumps(canvas_data), encoding="utf-8")

            svc = CanvasService(canvas_base_path=tmpdir)

            # Mock the lazy-imported function to raise
            with patch(
                "app.services.lancedb_index_service.get_lancedb_index_service",
                side_effect=RuntimeError("LanceDB crashed"),
            ):
                # _trigger_lancedb_index should not raise
                svc._trigger_lancedb_index("test")
                # If we reach here without exception, CRUD is not blocked
