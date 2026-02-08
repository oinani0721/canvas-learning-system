# Story 38.1: LanceDB Auto-Index Trigger — Code Review Fix Tests
"""
Tests for code review findings: H2 (_do_index coverage),
M1 (concurrency guard), M2 (fast-fail), M4 (delete_node trigger).

Split from test_story_38_1_lancedb_auto_index.py for maintainability.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ═══════════════════════════════════════════════════════════════════════════════
# Review H2: _do_index coverage
# ═══════════════════════════════════════════════════════════════════════════════


class TestDoIndexCoverage:
    """[Review H2] Tests for _do_index — previously zero coverage."""

    @pytest.mark.asyncio
    async def test_do_index_raises_when_client_unavailable(self):
        """
        [P0][Review H2] _do_index raises RuntimeError when client is None.
        """
        from app.services.lancedb_index_service import LanceDBIndexService

        with patch("app.services.lancedb_index_service.settings") as mock_settings:
            mock_settings.ENABLE_LANCEDB_AUTO_INDEX = True
            mock_settings.LANCEDB_INDEX_DEBOUNCE_MS = 100
            mock_settings.LANCEDB_INDEX_TIMEOUT = 5.0

            svc = LanceDBIndexService()
            svc._get_or_init_client = MagicMock(return_value=None)

            with pytest.raises(RuntimeError, match="LanceDB client not available"):
                await svc._do_index("test", "/tmp")

    @pytest.mark.asyncio
    async def test_do_index_reads_canvas_and_calls_index(self):
        """
        [P0][Review H2] _do_index reads canvas file and calls client.index_canvas().
        """
        from app.services.lancedb_index_service import LanceDBIndexService

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create fake canvas file
            canvas_data = {
                "nodes": [
                    {"id": "n1", "type": "text", "text": "hello"},
                    {"id": "n2", "type": "text", "text": "world"},
                ],
                "edges": [],
            }
            canvas_file = Path(tmpdir) / "my_canvas.canvas"
            canvas_file.write_text(json.dumps(canvas_data), encoding="utf-8")

            with patch("app.services.lancedb_index_service.settings") as mock_settings:
                mock_settings.ENABLE_LANCEDB_AUTO_INDEX = True
                mock_settings.LANCEDB_INDEX_DEBOUNCE_MS = 100
                mock_settings.LANCEDB_INDEX_TIMEOUT = 5.0

                svc = LanceDBIndexService()

                # Mock client
                mock_client = MagicMock()
                mock_client.index_canvas = AsyncMock(return_value=2)
                svc._get_or_init_client = MagicMock(return_value=mock_client)

                # Mock subject resolver (lazy import inside _do_index)
                mock_info = MagicMock()
                mock_info.subject = "math"
                mock_resolver = MagicMock()
                mock_resolver.resolve.return_value = mock_info

                with patch(
                    "app.services.subject_resolver.get_subject_resolver",
                    return_value=mock_resolver,
                ):
                    result = await svc._do_index("my_canvas", tmpdir)

                assert result == 2
                mock_client.index_canvas.assert_called_once()
                call_kwargs = mock_client.index_canvas.call_args
                assert call_kwargs.kwargs.get("canvas_path") == "my_canvas.canvas" or \
                       call_kwargs[1].get("canvas_path") == "my_canvas.canvas" or \
                       (len(call_kwargs[0]) > 0 and call_kwargs[0][0] == "my_canvas.canvas")

    @pytest.mark.asyncio
    async def test_do_index_raises_file_not_found(self):
        """
        [P0][Review H2] _do_index raises FileNotFoundError for missing canvas.
        """
        from app.services.lancedb_index_service import LanceDBIndexService

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("app.services.lancedb_index_service.settings") as mock_settings:
                mock_settings.ENABLE_LANCEDB_AUTO_INDEX = True
                mock_settings.LANCEDB_INDEX_DEBOUNCE_MS = 100
                mock_settings.LANCEDB_INDEX_TIMEOUT = 5.0

                svc = LanceDBIndexService()

                mock_client = MagicMock()
                svc._get_or_init_client = MagicMock(return_value=mock_client)

                mock_resolver = MagicMock()
                mock_resolver.resolve.return_value = MagicMock(subject="test")
                with patch(
                    "app.services.subject_resolver.get_subject_resolver",
                    return_value=mock_resolver,
                ):
                    with pytest.raises(FileNotFoundError):
                        await svc._do_index("nonexistent_canvas", tmpdir)


# ═══════════════════════════════════════════════════════════════════════════════
# Review M1: Concurrency Guard
# ═══════════════════════════════════════════════════════════════════════════════


class TestReviewM1ConcurrencyGuard:
    """[Review M1] Concurrent duplicate index prevention."""

    @pytest.mark.asyncio
    async def test_indexing_canvases_set_prevents_duplicates(self):
        """
        [P1][Review M1] _indexing_canvases set blocks concurrent index for same canvas.
        """
        from app.services.lancedb_index_service import LanceDBIndexService

        with patch("app.services.lancedb_index_service.settings") as mock_settings:
            mock_settings.ENABLE_LANCEDB_AUTO_INDEX = True
            mock_settings.LANCEDB_INDEX_DEBOUNCE_MS = 0
            mock_settings.LANCEDB_INDEX_TIMEOUT = 5.0

            svc = LanceDBIndexService()

            # Simulate: canvas_a is currently being indexed
            svc._indexing_canvases.add("canvas_a")
            svc._do_index_with_retry = AsyncMock(return_value=5)
            svc._persist_pending = MagicMock()

            # Debounced index should skip because canvas_a is in _indexing_canvases
            await svc._debounced_index("canvas_a", "/tmp")

            svc._do_index_with_retry.assert_not_called()


# ═══════════════════════════════════════════════════════════════════════════════
# Review M2: Fast-Fail
# ═══════════════════════════════════════════════════════════════════════════════


class TestReviewM2FastFail:
    """[Review M2] Fast-fail when agentic_rag is not installed."""

    @pytest.mark.asyncio
    async def test_client_unavailable_flag_skips_retries(self):
        """
        [P0][Review M2] When _client_unavailable is True, _do_index raises immediately.
        """
        from app.services.lancedb_index_service import LanceDBIndexService

        with patch("app.services.lancedb_index_service.settings") as mock_settings:
            mock_settings.ENABLE_LANCEDB_AUTO_INDEX = True
            mock_settings.LANCEDB_INDEX_DEBOUNCE_MS = 100
            mock_settings.LANCEDB_INDEX_TIMEOUT = 5.0

            svc = LanceDBIndexService()
            svc._client_unavailable = True

            with pytest.raises(RuntimeError, match="permanently unavailable"):
                await svc._do_index("test", "/tmp")


# ═══════════════════════════════════════════════════════════════════════════════
# Review M4: delete_node Trigger
# ═══════════════════════════════════════════════════════════════════════════════


class TestReviewM4DeleteNodeTrigger:
    """[Review M4] delete_node triggers LanceDB re-index."""

    @pytest.mark.asyncio
    async def test_delete_node_triggers_lancedb_index(self):
        """
        [P1][Review M4] CanvasService.delete_node() triggers LanceDB re-index.
        """
        from app.services.canvas_service import CanvasService

        with tempfile.TemporaryDirectory() as tmpdir:
            node_id = "node-to-delete"
            canvas_data = {
                "nodes": [{"id": node_id, "type": "text", "text": "bye", "x": 0, "y": 0, "width": 200, "height": 100}],
                "edges": [],
            }
            canvas_path = Path(tmpdir) / "test.canvas"
            canvas_path.write_text(json.dumps(canvas_data), encoding="utf-8")

            svc = CanvasService(canvas_base_path=tmpdir)

            mock_index_svc = MagicMock()
            with patch(
                "app.services.lancedb_index_service.get_lancedb_index_service",
                return_value=mock_index_svc,
            ):
                result = await svc.delete_node("test", node_id)
                assert result is True
                mock_index_svc.schedule_index.assert_called_once_with(
                    "test", tmpdir, trigger_node_id=node_id
                )
