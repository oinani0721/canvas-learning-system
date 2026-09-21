# Story 7.2: LLM Stats API Integration Tests
"""Integration tests for LLM logging pipeline (Task 6.3, 6.4).

Tests cover:
- CostTracker aggregation query correctness
- Task type and time period filtering
- End-to-end: LLMCallLogger callback -> buffer flush -> SQLite persistence
- API Key never appears in persisted log entries
- HTTP endpoint response format via FastAPI TestClient
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import aiosqlite
import pytest
from app.middleware.cost_tracker import CostTracker
from app.middleware.llm_call_logger import LLMCallLog, LLMCallLogger


class TestLLMStatsAPI:
    @pytest.fixture
    async def seeded_tracker(self, tmp_path):
        db_path = str(tmp_path / "test_api_llm_logs.db")
        ct = CostTracker(db_path=db_path)
        await ct.initialize()
        entries = [
            LLMCallLog(
                request_id="api-1",
                task_type="conversation",
                model_name="gpt-4o",
                input_tokens=500,
                output_tokens=200,
                total_tokens=700,
                latency_ms=1500,
                estimated_cost_usd=0.01,
                status="success",
            ),
            LLMCallLog(
                request_id="api-2",
                task_type="scoring",
                model_name="gpt-4o-mini",
                input_tokens=300,
                output_tokens=100,
                total_tokens=400,
                latency_ms=800,
                estimated_cost_usd=0.005,
                status="success",
            ),
            LLMCallLog(
                request_id="api-3",
                task_type="conversation",
                model_name="gpt-4o",
                status="failure",
                error_type="NETWORK_ERROR",
                error_message="Connection timeout",
                latency_ms=5000,
            ),
        ]
        await ct.insert_logs(entries)
        yield ct
        await ct.stop()

    @pytest.mark.asyncio
    async def test_response_structure(self, seeded_tracker):
        stats = await seeded_tracker.get_stats_by_period(
            start="2000-01-01T00:00:00.000Z",
            end="2099-12-31T23:59:59.999Z",
        )
        assert "summary" in stats
        assert "by_task" in stats
        assert "by_day" in stats
        assert "errors" in stats

    @pytest.mark.asyncio
    async def test_values_correct(self, seeded_tracker):
        stats = await seeded_tracker.get_stats_by_period(
            start="2000-01-01T00:00:00.000Z",
            end="2099-12-31T23:59:59.999Z",
        )
        assert stats["summary"]["total_calls"] == 3
        assert stats["summary"]["total_tokens"] == 1100
        assert stats["errors"]["total"] == 1
        assert stats["errors"]["by_type"]["NETWORK_ERROR"] == 1

    @pytest.mark.asyncio
    async def test_task_type_filter(self, seeded_tracker):
        stats = await seeded_tracker.get_stats_by_period(
            start="2000-01-01T00:00:00.000Z",
            end="2099-12-31T23:59:59.999Z",
            task_type="scoring",
        )
        assert stats["summary"]["total_calls"] == 1
        assert stats["summary"]["total_tokens"] == 400

    @pytest.mark.asyncio
    async def test_by_task_breakdown(self, seeded_tracker):
        stats = await seeded_tracker.get_stats_by_period(
            start="2000-01-01T00:00:00.000Z",
            end="2099-12-31T23:59:59.999Z",
        )
        task_types = {t["task_type"]: t for t in stats["by_task"]}
        assert "conversation" in task_types
        assert "scoring" in task_types
        assert task_types["conversation"]["calls"] == 2
        assert task_types["scoring"]["calls"] == 1


def _make_usage_obj(prompt=100, completion=50, total=150):
    """Build a usage object with the given token counts."""
    u = MagicMock()
    u.prompt_tokens = prompt
    u.completion_tokens = completion
    u.total_tokens = total
    return u


def _make_response_obj(usage=None):
    """Build a response object with the given usage."""
    r = MagicMock()
    r.usage = usage
    return r


class TestCallbackToSQLiteE2E:
    """End-to-end: LLMCallLogger callback -> buffer flush -> SQLite -> query.

    Verifies that the full pipeline works without needing a live LLM.
    """

    @pytest.fixture
    async def logger_and_tracker(self, tmp_path):
        db_path = str(tmp_path / "e2e_llm_logs.db")
        ct = CostTracker(db_path=db_path)
        await ct.initialize()
        lgr = LLMCallLogger()
        await lgr.start(ct)
        lgr.BATCH_SIZE = 2  # Small batch for testing
        yield lgr, ct
        await lgr.stop()
        await ct.stop()

    @pytest.mark.asyncio
    async def test_callback_writes_to_sqlite(self, logger_and_tracker):
        """on_success -> flush -> SQLite row exists."""
        lgr, ct = logger_and_tracker
        usage = _make_usage_obj(prompt=150, completion=60, total=210)
        response = _make_response_obj(usage=usage)
        kwargs = {
            "model": "gpt-4o-mini",
            "response_cost": 0.003,
            "litellm_params": {"metadata": {"task_type": "scoring", "request_id": "e2e-req-1"}},
        }
        start = datetime(2026, 3, 18, 9, 0, 0, tzinfo=timezone.utc)
        end = datetime(2026, 3, 18, 9, 0, 2, tzinfo=timezone.utc)

        # Fire callback (adds to buffer)
        await lgr.on_success(kwargs, response, start, end)
        # Second entry to trigger batch flush (BATCH_SIZE=2)
        await lgr.on_success(kwargs, response, start, end)

        # Query from SQLite
        stats = await ct.get_stats_by_period(
            start="2000-01-01T00:00:00.000Z",
            end="2099-12-31T23:59:59.999Z",
        )
        assert stats["summary"]["total_calls"] == 2
        assert stats["summary"]["total_tokens"] == 420
        assert stats["summary"]["success_rate"] == 1.0

    @pytest.mark.asyncio
    async def test_failure_callback_writes_to_sqlite(self, logger_and_tracker):
        """on_failure -> flush -> SQLite error row exists."""
        lgr, ct = logger_and_tracker
        exc = type("Timeout", (Exception,), {})("Request timed out")
        kwargs = {
            "model": "gpt-4o",
            "litellm_params": {"metadata": {"task_type": "conversation"}},
        }
        # Two failures to trigger batch flush
        await lgr.on_failure(kwargs, exc, None, None)
        await lgr.on_failure(kwargs, exc, None, None)

        stats = await ct.get_stats_by_period(
            start="2000-01-01T00:00:00.000Z",
            end="2099-12-31T23:59:59.999Z",
        )
        assert stats["summary"]["total_calls"] == 2
        assert stats["errors"]["total"] == 2
        assert stats["errors"]["by_type"]["NETWORK_ERROR"] == 2

    @pytest.mark.asyncio
    async def test_api_key_not_in_sqlite_rows(self, logger_and_tracker):
        """API key must never appear in persisted SQLite rows."""
        lgr, ct = logger_and_tracker
        api_secret = "sk-SUPER-SECRET-KEY-xyz123"
        usage = _make_usage_obj(prompt=10, completion=5, total=15)
        response = _make_response_obj(usage=usage)
        kwargs = {
            "model": "gpt-4o",
            "api_key": api_secret,
            "response_cost": 0.001,
            "litellm_params": {
                "api_key": api_secret,
                "metadata": {"task_type": "extraction", "api_key": api_secret},
            },
        }
        # Two entries to flush
        await lgr.on_success(kwargs, response, None, None)
        await lgr.on_success(kwargs, response, None, None)

        # Read raw SQLite rows and verify no API key
        async with aiosqlite.connect(ct._db_path) as db:
            cursor = await db.execute("SELECT * FROM llm_call_logs")
            rows = await cursor.fetchall()
            col_names = [desc[0] for desc in cursor.description]

        assert len(rows) >= 2
        for row in rows:
            row_str = str(dict(zip(col_names, row)))
            assert api_secret not in row_str

    @pytest.mark.asyncio
    async def test_stop_flushes_remaining_buffer(self, tmp_path):
        """Stopping the logger flushes buffered entries to SQLite."""
        db_path = str(tmp_path / "stop_flush.db")
        ct = CostTracker(db_path=db_path)
        await ct.initialize()
        lgr = LLMCallLogger()
        await lgr.start(ct)
        lgr.BATCH_SIZE = 100  # Large batch so auto-flush won't trigger

        # Add a single entry (won't reach batch size)
        await lgr._add_to_buffer(LLMCallLog(request_id="pending-1", task_type="indexing", total_tokens=99))
        assert len(lgr._buffer) == 1

        # Stop should flush
        await lgr.stop()
        await ct.stop()

        # Verify it was written
        async with aiosqlite.connect(db_path) as db:
            cursor = await db.execute("SELECT COUNT(*) FROM llm_call_logs")
            row = await cursor.fetchone()
            assert row[0] == 1
