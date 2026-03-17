# Story 7.2: LLM Stats API Integration Tests
"""Integration tests for GET /api/v1/system/llm-stats (Task 6.3)."""

import pytest

from app.middleware.cost_tracker import CostTracker
from app.middleware.llm_call_logger import LLMCallLog


class TestLLMStatsAPI:

    @pytest.fixture
    async def seeded_tracker(self, tmp_path):
        db_path = str(tmp_path / "test_api_llm_logs.db")
        ct = CostTracker(db_path=db_path)
        await ct.initialize()
        entries = [
            LLMCallLog(
                request_id="api-1", task_type="conversation",
                model_name="gpt-4o", input_tokens=500,
                output_tokens=200, total_tokens=700,
                latency_ms=1500, estimated_cost_usd=0.01,
                status="success",
            ),
            LLMCallLog(
                request_id="api-2", task_type="scoring",
                model_name="gpt-4o-mini", input_tokens=300,
                output_tokens=100, total_tokens=400,
                latency_ms=800, estimated_cost_usd=0.005,
                status="success",
            ),
            LLMCallLog(
                request_id="api-3", task_type="conversation",
                model_name="gpt-4o", status="failure",
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
