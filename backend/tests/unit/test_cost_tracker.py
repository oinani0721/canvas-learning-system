# Story 7.2: Cost Tracker Unit Tests
"""Unit tests for Cost Tracker SQLite persistence (Task 6.2)."""

import pytest

from app.middleware.cost_tracker import CostTracker
from app.middleware.llm_call_logger import LLMCallLog


class TestCostTracker:

    @pytest.fixture
    async def tracker(self, tmp_path):
        db_path = str(tmp_path / "test_llm_logs.db")
        ct = CostTracker(db_path=db_path)
        await ct.initialize()
        yield ct
        await ct.stop()

    @pytest.mark.asyncio
    async def test_initialize_creates_tables(self, tracker):
        import aiosqlite
        async with aiosqlite.connect(tracker._db_path) as db:
            cursor = await db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            tables = [row[0] for row in await cursor.fetchall()]
        assert "llm_call_logs" in tables
        assert "llm_call_logs_daily" in tables

    @pytest.mark.asyncio
    async def test_insert_and_query_logs(self, tracker):
        entries = [
            LLMCallLog(
                request_id=f"req-{i}",
                task_type="scoring",
                model_name="gpt-4o-mini",
                input_tokens=100 * (i + 1),
                output_tokens=50 * (i + 1),
                total_tokens=150 * (i + 1),
                estimated_cost_usd=0.001 * (i + 1),
                status="success",
            )
            for i in range(5)
        ]
        await tracker.insert_logs(entries)
        stats = await tracker.get_stats_by_period(
            start="2000-01-01T00:00:00.000Z",
            end="2099-12-31T23:59:59.999Z",
        )
        assert stats["summary"]["total_calls"] == 5
        assert stats["summary"]["total_tokens"] == 150 + 300 + 450 + 600 + 750
        assert stats["summary"]["success_rate"] == 1.0

    @pytest.mark.asyncio
    async def test_rotate_logs_compresses_old_entries(self, tracker):
        old_entries = [
            LLMCallLog(
                request_id=f"old-{i}",
                task_type="scoring",
                total_tokens=100,
                created_at="2020-01-01T00:00:00.000Z",
            )
            for i in range(5)
        ]
        new_entries = [
            LLMCallLog(
                request_id=f"new-{i}",
                task_type="conversation",
                total_tokens=200,
            )
            for i in range(3)
        ]
        await tracker.insert_logs(old_entries + new_entries)
        result = await tracker.rotate_logs()
        assert result["deleted"] == 5
        stats = await tracker.get_stats_by_period(
            start="2000-01-01T00:00:00.000Z",
            end="2099-12-31T23:59:59.999Z",
        )
        assert stats["summary"]["total_calls"] == 3

    @pytest.mark.asyncio
    async def test_empty_stats_when_no_entries(self, tracker):
        stats = await tracker.get_stats_by_period(
            start="2000-01-01T00:00:00.000Z",
            end="2099-12-31T23:59:59.999Z",
        )
        assert stats["summary"]["total_calls"] == 0
        assert stats["summary"]["total_tokens"] == 0
        assert stats["summary"]["success_rate"] == 1.0
        assert stats["errors"]["total"] == 0

    @pytest.mark.asyncio
    async def test_health_probe(self, tracker):
        entries = [
            LLMCallLog(request_id=f"h-{i}", status="success", latency_ms=100)
            for i in range(10)
        ]
        entries.append(LLMCallLog(request_id="h-fail", status="failure", latency_ms=500))
        await tracker.insert_logs(entries)
        probe = await tracker.get_health_probe()
        assert probe["total_recent"] == 11
        assert probe["success_rate"] < 1.0
        assert probe["avg_latency_ms"] > 0
