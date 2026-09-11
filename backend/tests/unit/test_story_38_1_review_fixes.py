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
                # 契约演进 14f0412d (2026-02-07)：_do_index 在取到 client 后新增
                # `if hasattr(client, "initialize"): await client.initialize()`
                # (lancedb_index_service.py:451-453)；a9304c69 (2026-03-29 except 精确化)
                # 又把兜底收窄成 (RuntimeError, OSError, ConnectionError)，于是
                # `await MagicMock()` 抛的 TypeError 不再被吞、直接穿透 ⇒ 本用例必红。
                # 裸 MagicMock 是替身形态过期，不是生产回归 ⇒ 把 initialize 换成可等待替身。
                # [CARD-RED-C2]
                mock_client.initialize = AsyncMock()
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
                # 判据强度提升：14f0412d 引入的「索引前先 initialize」新契约本身要有锚，
                # 否则本次修改只是让替身跟上、把新契约的覆盖留成空白。
                mock_client.initialize.assert_awaited_once()
                # Codex round-1 LOW：只断次数不证明**顺序**（把 initialize 挪到索引之后
                # 次数仍是 1）。两者都是同一个 mock_client 的子调用，mock_calls 按真实
                # 发生顺序记录 ⇒ 直接比对下标即可锁住「先 initialize 再 index」。
                _names = [c[0] for c in mock_client.mock_calls]
                assert "initialize" in _names and "index_canvas" in _names, _names
                assert _names.index("initialize") < _names.index("index_canvas"), (
                    f"initialize 必须在 index_canvas 之前发生，实际顺序={_names}"
                )
                call_kwargs = mock_client.index_canvas.call_args
                assert (
                    call_kwargs.kwargs.get("canvas_path") == "my_canvas.canvas"
                    or call_kwargs[1].get("canvas_path") == "my_canvas.canvas"
                    or (
                        len(call_kwargs[0]) > 0
                        and call_kwargs[0][0] == "my_canvas.canvas"
                    )
                )

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
                # 契约演进 14f0412d (2026-02-07)：_do_index 在取到 client 后新增
                # `if hasattr(client, "initialize"): await client.initialize()`
                # (lancedb_index_service.py:451-453)；a9304c69 (2026-03-29 except 精确化)
                # 又把兜底收窄成 (RuntimeError, OSError, ConnectionError)，于是
                # `await MagicMock()` 抛的 TypeError 不再被吞、直接穿透 ⇒ 本用例必红。
                # 裸 MagicMock 是替身形态过期，不是生产回归 ⇒ 把 initialize 换成可等待替身。
                # [CARD-RED-C2]
                mock_client.initialize = AsyncMock()
                svc._get_or_init_client = MagicMock(return_value=mock_client)

                mock_resolver = MagicMock()
                mock_resolver.resolve.return_value = MagicMock(subject="test")
                with patch(
                    "app.services.subject_resolver.get_subject_resolver",
                    return_value=mock_resolver,
                ):
                    with pytest.raises(FileNotFoundError):
                        await svc._do_index("nonexistent_canvas", tmpdir)

                # Codex round-1 LOW：本条原先没有 initialize 的锚，于是「取消初始化」
                # 这个改动不会让它翻红。initialize 发生在文件存在性检查之前
                # （lancedb_index_service.py:451-453 → :462 才解析 canvas_path），
                # 故即便本条以 FileNotFoundError 收场，initialize 也必须已被等待。
                mock_client.initialize.assert_awaited_once()


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
                "nodes": [
                    {
                        "id": node_id,
                        "type": "text",
                        "text": "bye",
                        "x": 0,
                        "y": 0,
                        "width": 200,
                        "height": 100,
                    }
                ],
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
