# Story 38.1: LanceDB Auto-Index Trigger — AC-3 + Lifecycle Tests
"""
AC-3: Pending index operations recovered from JSONL on startup.
Also includes singleton management and cleanup tests.

Split from test_story_38_1_lancedb_auto_index.py for maintainability.
"""

import json
import logging
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ═══════════════════════════════════════════════════════════════════════════════
# AC-3: Startup Recovery (D1: Persistence)
# ═══════════════════════════════════════════════════════════════════════════════


class TestAC3StartupRecovery:
    """AC-3: Pending index updates recovered from JSONL on startup."""

    @pytest.mark.asyncio
    async def test_recover_pending_no_file_returns_zero(self):
        """
        [P0] recover_pending() returns {recovered: 0, pending: 0} when no JSONL file.

        Verifies: lancedb_index_service.py L102-103
        """
        from app.services.lancedb_index_service import LanceDBIndexService

        with (
            tempfile.TemporaryDirectory() as tmpdir,
            patch("app.services.lancedb_index_service.settings") as mock_settings,
        ):
            mock_settings.ENABLE_LANCEDB_AUTO_INDEX = True
            mock_settings.LANCEDB_INDEX_DEBOUNCE_MS = 100
            mock_settings.LANCEDB_INDEX_TIMEOUT = 5.0

            svc = LanceDBIndexService()
            svc._pending_file = Path(tmpdir) / "nonexistent.jsonl"

            result = await svc.recover_pending("/tmp/canvas")
            assert result == {"recovered": 0, "pending": 0}

    @pytest.mark.asyncio
    async def test_recover_pending_retries_entries(self):
        """
        [P0] recover_pending() retries each entry in the JSONL file.

        Verifies: lancedb_index_service.py L130-139 retry loop.
        """
        from app.services.lancedb_index_service import LanceDBIndexService

        with (
            tempfile.TemporaryDirectory() as tmpdir,
            patch("app.services.lancedb_index_service.settings") as mock_settings,
        ):
            mock_settings.ENABLE_LANCEDB_AUTO_INDEX = True
            mock_settings.LANCEDB_INDEX_DEBOUNCE_MS = 100
            mock_settings.LANCEDB_INDEX_TIMEOUT = 5.0

            svc = LanceDBIndexService()
            svc._pending_file = Path(tmpdir) / "pending.jsonl"

            # Write 2 pending entries
            entries = [
                {"canvas_name": "canvas_a", "timestamp": "2026-01-01T00:00:00", "error": "timeout"},
                {"canvas_name": "canvas_b", "timestamp": "2026-01-01T00:01:00", "error": "timeout"},
            ]
            svc._pending_file.write_text(
                "\n".join(json.dumps(e) for e in entries) + "\n",
                encoding="utf-8",
            )

            # Mock _do_index to succeed
            svc._do_index = AsyncMock(return_value=5)

            result = await svc.recover_pending("/tmp/canvas")
            assert result["recovered"] == 2
            assert result["pending"] == 0

            # JSONL file should be removed after all recovered
            assert not svc._pending_file.exists(), (
                "JSONL file should be deleted when all entries are recovered"
            )

    @pytest.mark.asyncio
    async def test_recover_pending_partial_failure(self):
        """
        [P1] recover_pending() keeps failed entries in JSONL.

        Verifies: lancedb_index_service.py L142-153 rewrite logic.
        """
        from app.services.lancedb_index_service import LanceDBIndexService

        with (
            tempfile.TemporaryDirectory() as tmpdir,
            patch("app.services.lancedb_index_service.settings") as mock_settings,
        ):
            mock_settings.ENABLE_LANCEDB_AUTO_INDEX = True
            mock_settings.LANCEDB_INDEX_DEBOUNCE_MS = 100
            mock_settings.LANCEDB_INDEX_TIMEOUT = 5.0

            svc = LanceDBIndexService()
            svc._pending_file = Path(tmpdir) / "pending.jsonl"

            entries = [
                {"canvas_name": "canvas_ok", "timestamp": "2026-01-01T00:00:00", "error": "timeout"},
                {"canvas_name": "canvas_fail", "timestamp": "2026-01-01T00:01:00", "error": "timeout"},
            ]
            svc._pending_file.write_text(
                "\n".join(json.dumps(e) for e in entries) + "\n",
                encoding="utf-8",
            )

            # First succeeds, second fails
            call_count = 0

            async def selective_index(canvas_name, canvas_base_path):
                nonlocal call_count
                call_count += 1
                if canvas_name == "canvas_fail":
                    raise ConnectionError("still down")
                return 5

            svc._do_index = selective_index

            result = await svc.recover_pending("/tmp/canvas")
            assert result["recovered"] == 1
            assert result["pending"] == 1

            # JSONL should still exist with only the failed entry
            assert svc._pending_file.exists()
            remaining = svc._pending_file.read_text(encoding="utf-8").strip()
            remaining_entry = json.loads(remaining)
            assert remaining_entry["canvas_name"] == "canvas_fail"

    @pytest.mark.asyncio
    async def test_recover_pending_deduplicates_entries(self):
        """
        [P1] recover_pending() deduplicates by canvas_name (keeps latest).

        Verifies: lancedb_index_service.py L114-119 dedup logic.
        """
        from app.services.lancedb_index_service import LanceDBIndexService

        with (
            tempfile.TemporaryDirectory() as tmpdir,
            patch("app.services.lancedb_index_service.settings") as mock_settings,
        ):
            mock_settings.ENABLE_LANCEDB_AUTO_INDEX = True
            mock_settings.LANCEDB_INDEX_DEBOUNCE_MS = 100
            mock_settings.LANCEDB_INDEX_TIMEOUT = 5.0

            svc = LanceDBIndexService()
            svc._pending_file = Path(tmpdir) / "pending.jsonl"

            # Same canvas_name twice — should deduplicate
            entries = [
                {"canvas_name": "canvas_a", "timestamp": "2026-01-01T00:00:00", "error": "first"},
                {"canvas_name": "canvas_a", "timestamp": "2026-01-01T00:05:00", "error": "second"},
            ]
            svc._pending_file.write_text(
                "\n".join(json.dumps(e) for e in entries) + "\n",
                encoding="utf-8",
            )

            svc._do_index = AsyncMock(return_value=5)

            result = await svc.recover_pending("/tmp/canvas")
            # Should only have 1 entry (deduplicated)
            assert result["recovered"] == 1
            assert svc._do_index.call_count == 1

    @pytest.mark.asyncio
    async def test_recover_pending_startup_log(self, caplog):
        """
        [P1] Startup recovery emits log: "LanceDB: {N} pending index updates recovered".

        Verifies: lancedb_index_service.py L123-125
        """
        from app.services.lancedb_index_service import LanceDBIndexService

        with (
            tempfile.TemporaryDirectory() as tmpdir,
            patch("app.services.lancedb_index_service.settings") as mock_settings,
        ):
            mock_settings.ENABLE_LANCEDB_AUTO_INDEX = True
            mock_settings.LANCEDB_INDEX_DEBOUNCE_MS = 100
            mock_settings.LANCEDB_INDEX_TIMEOUT = 5.0

            svc = LanceDBIndexService()
            svc._pending_file = Path(tmpdir) / "pending.jsonl"

            entries = [
                {"canvas_name": "canvas_x", "timestamp": "2026-01-01T00:00:00", "error": "err"},
            ]
            svc._pending_file.write_text(
                json.dumps(entries[0]) + "\n",
                encoding="utf-8",
            )

            svc._do_index = AsyncMock(return_value=3)

            with caplog.at_level(logging.INFO):
                await svc.recover_pending("/tmp/canvas")

            info_messages = [r.message for r in caplog.records]
            assert any(
                "pending index updates recovered" in msg
                for msg in info_messages
            ), (
                f"Expected startup log about pending recovery. Got: {info_messages}"
            )


# ═══════════════════════════════════════════════════════════════════════════════
# Singleton & Cleanup
# ═══════════════════════════════════════════════════════════════════════════════


class TestSingletonAndCleanup:
    """Module-level singleton and shutdown cleanup."""

    def test_get_lancedb_index_service_returns_singleton(self):
        """
        [P1] get_lancedb_index_service() returns the same instance.

        Verifies: lancedb_index_service.py L286-293 singleton.
        """
        import app.services.lancedb_index_service as mod

        original = mod._lancedb_index_service_instance
        try:
            mod._lancedb_index_service_instance = None

            with patch.object(mod, "settings") as mock_settings:
                mock_settings.ENABLE_LANCEDB_AUTO_INDEX = True
                mock_settings.LANCEDB_INDEX_DEBOUNCE_MS = 500
                mock_settings.LANCEDB_INDEX_TIMEOUT = 5.0

                svc1 = mod.get_lancedb_index_service()
                svc2 = mod.get_lancedb_index_service()
                assert svc1 is svc2, "Should return the same singleton instance"
        finally:
            mod._lancedb_index_service_instance = original

    def test_get_lancedb_index_service_returns_none_when_disabled(self):
        """
        [P0] get_lancedb_index_service() returns None when auto-index is disabled.

        Verifies: lancedb_index_service.py L289-290 early return.
        """
        import app.services.lancedb_index_service as mod

        original = mod._lancedb_index_service_instance
        try:
            mod._lancedb_index_service_instance = None

            with patch.object(mod, "settings") as mock_settings:
                mock_settings.ENABLE_LANCEDB_AUTO_INDEX = False

                result = mod.get_lancedb_index_service()
                assert result is None
        finally:
            mod._lancedb_index_service_instance = original

    @pytest.mark.asyncio
    async def test_cleanup_cancels_pending_tasks(self):
        """
        [P1] cleanup() cancels all pending debounce tasks.

        Verifies: lancedb_index_service.py L157-162 cleanup.
        """
        from app.services.lancedb_index_service import LanceDBIndexService

        with patch("app.services.lancedb_index_service.settings") as mock_settings:
            mock_settings.ENABLE_LANCEDB_AUTO_INDEX = True
            mock_settings.LANCEDB_INDEX_DEBOUNCE_MS = 60000  # Very long debounce
            mock_settings.LANCEDB_INDEX_TIMEOUT = 5.0

            svc = LanceDBIndexService()
            svc.schedule_index("canvas_a", "/tmp")
            svc.schedule_index("canvas_b", "/tmp")

            assert len(svc._pending_tasks) == 2

            await svc.cleanup()

            assert len(svc._pending_tasks) == 0
