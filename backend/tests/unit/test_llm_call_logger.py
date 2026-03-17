# Story 7.2: LLM Call Logger Unit Tests
"""Unit tests for LLM Call Logger middleware (Task 6.1)."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.middleware.llm_call_logger import (
    CallStatus, ErrorCategory, LLMCallLog, LLMCallLogger,
    TaskType, classify_error, _sanitize_kwargs,
)


class TestLLMCallLog:

    def test_default_values(self):
        log = LLMCallLog()
        assert log.request_id
        assert log.task_type == TaskType.CONVERSATION.value
        assert log.input_tokens == 0
        assert log.estimated_cost_usd is None
        assert log.status == CallStatus.SUCCESS.value

    def test_custom_values(self):
        log = LLMCallLog(
            request_id="test-123", task_type="scoring",
            model_name="gpt-4o-mini", input_tokens=1250,
            estimated_cost_usd=0.00285, status="success",
        )
        assert log.input_tokens == 1250
        assert log.estimated_cost_usd == 0.00285


class TestTaskType:

    def test_five_task_types_exist(self):
        assert TaskType.CONVERSATION.value == "conversation"
        assert TaskType.SCORING.value == "scoring"
        assert TaskType.EXTRACTION.value == "extraction"
        assert TaskType.INDEXING.value == "indexing"
        assert TaskType.QA_CHECK.value == "qa_check"


class TestErrorClassification:

    def test_auth_error_is_config(self):
        exc = type("AuthenticationError", (Exception,), {})()
        assert classify_error(exc) == ErrorCategory.CONFIG_ERROR

    def test_rate_limit_is_llm(self):
        exc = type("RateLimitError", (Exception,), {})()
        assert classify_error(exc) == ErrorCategory.LLM_ERROR

    def test_timeout_is_network(self):
        exc = type("Timeout", (Exception,), {})()
        assert classify_error(exc) == ErrorCategory.NETWORK_ERROR


class TestAPIKeyFiltering:

    def test_api_key_not_in_sanitized_kwargs(self):
        kwargs = {
            "model": "gpt-4o",
            "api_key": "sk-secret-key-12345",
            "response_cost": 0.005,
        }
        safe = _sanitize_kwargs(kwargs)
        assert "api_key" not in safe
        assert safe["model"] == "gpt-4o"


class TestLLMCallLogger:

    @pytest.fixture
    def logger_with_tracker(self):
        instance = LLMCallLogger()
        tracker = AsyncMock()
        tracker.insert_logs = AsyncMock()
        instance._cost_tracker = tracker
        instance._running = True
        return instance

    @pytest.mark.asyncio
    async def test_on_success_extracts_tokens(self, logger_with_tracker):
        usage = MagicMock()
        usage.prompt_tokens = 100
        usage.completion_tokens = 50
        usage.total_tokens = 150
        response = MagicMock()
        response.usage = usage
        kwargs = {
            "model": "gpt-4o-mini",
            "response_cost": 0.005,
            "litellm_params": {
                "metadata": {"task_type": "scoring", "request_id": "test-req-1"}
            },
        }
        start = datetime(2026, 3, 16, 10, 0, 0, tzinfo=timezone.utc)
        end = datetime(2026, 3, 16, 10, 0, 2, tzinfo=timezone.utc)
        await logger_with_tracker.on_success(kwargs, response, start, end)
        assert len(logger_with_tracker._buffer) == 1
        entry = logger_with_tracker._buffer[0]
        assert entry.input_tokens == 100
        assert entry.output_tokens == 50
        assert entry.estimated_cost_usd == 0.005

    @pytest.mark.asyncio
    async def test_on_failure_classifies_error(self, logger_with_tracker):
        RateLimitErr = type("RateLimitError", (Exception,), {})
        exception = RateLimitErr("Rate limit exceeded")
        kwargs = {
            "model": "gpt-4o",
            "litellm_params": {"metadata": {"task_type": "conversation"}},
        }
        start = datetime(2026, 3, 16, 10, 0, 0, tzinfo=timezone.utc)
        end = datetime(2026, 3, 16, 10, 0, 1, tzinfo=timezone.utc)
        await logger_with_tracker.on_failure(kwargs, exception, start, end)
        assert logger_with_tracker._buffer[0].status == "failure"
        assert logger_with_tracker._buffer[0].error_type == "LLM_ERROR"

    @pytest.mark.asyncio
    async def test_batch_flush_at_threshold(self, logger_with_tracker):
        logger_with_tracker.BATCH_SIZE = 3
        for i in range(3):
            await logger_with_tracker._add_to_buffer(LLMCallLog(request_id=f"req-{i}"))
        assert len(logger_with_tracker._buffer) == 0
        logger_with_tracker._cost_tracker.insert_logs.assert_called_once()

    @pytest.mark.asyncio
    async def test_on_success_never_raises(self, logger_with_tracker):
        await logger_with_tracker.on_success({}, None, None, None)
        assert len(logger_with_tracker._buffer) == 1
