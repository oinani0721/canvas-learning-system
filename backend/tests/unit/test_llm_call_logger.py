# Story 7.2: LLM Call Logger Unit Tests
"""Unit tests for LLM Call Logger middleware (Task 6.1).

Tests cover:
- LLMCallLog Pydantic model defaults and custom values
- 5 TaskType enum values
- Error classification (7+ LiteLLM exception types + fallback heuristics)
- API Key whitelist sanitization (NFR-SEC-02)
- LLMCallLogger on_success / on_failure core logic
- CustomLogger async_log_success_event / async_log_failure_event delegation
- Batch flush threshold
- Robustness (never raises)
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.middleware.llm_call_logger import (
    CallStatus,
    ErrorCategory,
    LLMCallLog,
    LLMCallLogger,
    TaskType,
    _sanitize_kwargs,
    classify_error,
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
            request_id="test-123",
            task_type="scoring",
            model_name="gpt-4o-mini",
            input_tokens=1250,
            estimated_cost_usd=0.00285,
            status="success",
        )
        assert log.input_tokens == 1250
        assert log.estimated_cost_usd == 0.00285

    def test_created_at_is_iso8601(self):
        log = LLMCallLog()
        assert log.created_at.endswith("Z")
        assert "T" in log.created_at


class TestTaskType:
    def test_five_task_types_exist(self):
        assert TaskType.CONVERSATION.value == "conversation"
        assert TaskType.SCORING.value == "scoring"
        assert TaskType.EXTRACTION.value == "extraction"
        assert TaskType.INDEXING.value == "indexing"
        assert TaskType.QA_CHECK.value == "qa_check"

    def test_exactly_five_types(self):
        assert len(TaskType) == 5


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

    def test_api_connection_error_is_network(self):
        exc = type("APIConnectionError", (Exception,), {})()
        assert classify_error(exc) == ErrorCategory.NETWORK_ERROR

    def test_not_found_is_config(self):
        exc = type("NotFoundError", (Exception,), {})()
        assert classify_error(exc) == ErrorCategory.CONFIG_ERROR

    def test_bad_request_is_llm(self):
        exc = type("BadRequestError", (Exception,), {})()
        assert classify_error(exc) == ErrorCategory.LLM_ERROR

    def test_service_unavailable_is_llm(self):
        exc = type("ServiceUnavailableError", (Exception,), {})()
        assert classify_error(exc) == ErrorCategory.LLM_ERROR

    def test_fallback_timeout_heuristic(self):
        exc = Exception("Request timed out after 30s")
        assert classify_error(exc) == ErrorCategory.NETWORK_ERROR

    def test_fallback_connection_heuristic(self):
        exc = Exception("Failed to connect to host")
        assert classify_error(exc) == ErrorCategory.NETWORK_ERROR

    def test_fallback_auth_heuristic(self):
        exc = Exception("Invalid auth credentials provided")
        assert classify_error(exc) == ErrorCategory.CONFIG_ERROR

    def test_unknown_error_defaults_to_llm(self):
        exc = Exception("Something weird happened")
        assert classify_error(exc) == ErrorCategory.LLM_ERROR


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

    def test_authorization_header_not_in_sanitized_kwargs(self):
        kwargs = {
            "model": "gpt-4o",
            "authorization": "Bearer sk-secret",
            "api_base": "https://api.openai.com",
            "response_cost": 0.01,
        }
        safe = _sanitize_kwargs(kwargs)
        assert "authorization" not in safe
        assert "api_base" not in safe
        assert safe["model"] == "gpt-4o"
        assert safe["response_cost"] == 0.01

    def test_metadata_api_key_stripped(self):
        kwargs = {
            "model": "gpt-4o",
            "litellm_params": {
                "metadata": {
                    "task_type": "scoring",
                    "request_id": "req-1",
                    "api_key": "sk-should-not-appear",
                },
                "api_key": "sk-another-secret",
            },
        }
        safe = _sanitize_kwargs(kwargs)
        assert "api_key" not in safe.get("metadata", {})
        assert safe["metadata"]["task_type"] == "scoring"
        assert safe["metadata"]["request_id"] == "req-1"

    def test_no_api_key_anywhere_in_serialized_output(self):
        """Verify API key does not appear anywhere in the sanitized output string."""
        secret = "sk-test-SECRET-KEY-1234567890abcdef"
        kwargs = {
            "model": "gpt-4o",
            "api_key": secret,
            "response_cost": 0.005,
            "litellm_params": {
                "api_key": secret,
                "metadata": {"task_type": "scoring", "api_key": secret},
            },
        }
        safe = _sanitize_kwargs(kwargs)
        serialized = str(safe)
        assert secret not in serialized


class TestLLMCallLogger:
    @pytest.fixture
    def logger_with_tracker(self):
        instance = LLMCallLogger()
        tracker = AsyncMock()
        tracker.insert_logs = AsyncMock()
        instance._cost_tracker = tracker
        instance._running = True
        return instance

    def _build_usage(self, prompt=100, completion=50, total=150):
        """Build a usage object with the given token counts."""
        usage = MagicMock()
        usage.prompt_tokens = prompt
        usage.completion_tokens = completion
        usage.total_tokens = total
        return usage

    def _build_response(self, usage=None):
        """Build a response object with the given usage."""
        resp = MagicMock()
        resp.usage = usage
        return resp

    @pytest.mark.asyncio
    async def test_on_success_extracts_tokens(self, logger_with_tracker):
        usage = self._build_usage(prompt=100, completion=50, total=150)
        response = self._build_response(usage=usage)
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
    async def test_on_success_extracts_latency(self, logger_with_tracker):
        response = self._build_response(usage=None)
        start = datetime(2026, 3, 16, 10, 0, 0, tzinfo=timezone.utc)
        end = datetime(2026, 3, 16, 10, 0, 3, tzinfo=timezone.utc)
        await logger_with_tracker.on_success({"model": "test"}, response, start, end)
        entry = logger_with_tracker._buffer[0]
        assert entry.latency_ms == 3000

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
    async def test_on_failure_truncates_error_message(self, logger_with_tracker):
        long_msg = "x" * 1000
        exc = Exception(long_msg)
        await logger_with_tracker.on_failure({"model": "test"}, exc, None, None)
        entry = logger_with_tracker._buffer[0]
        assert len(entry.error_message) == 500

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

    @pytest.mark.asyncio
    async def test_async_log_success_event_delegates(self, logger_with_tracker):
        """Verify CustomLogger async_log_success_event calls on_success."""
        usage = self._build_usage(prompt=200, completion=80, total=280)
        response = self._build_response(usage=usage)
        kwargs = {
            "model": "gemini-2.0-flash",
            "litellm_params": {"metadata": {"task_type": "extraction"}},
        }
        start = datetime(2026, 3, 17, 12, 0, 0, tzinfo=timezone.utc)
        end = datetime(2026, 3, 17, 12, 0, 1, tzinfo=timezone.utc)
        await logger_with_tracker.async_log_success_event(kwargs, response, start, end)
        assert len(logger_with_tracker._buffer) == 1
        entry = logger_with_tracker._buffer[0]
        assert entry.task_type == "extraction"
        assert entry.model_name == "gemini-2.0-flash"
        assert entry.input_tokens == 200
        assert entry.status == "success"

    @pytest.mark.asyncio
    async def test_async_log_failure_event_delegates(self, logger_with_tracker):
        """Verify CustomLogger async_log_failure_event calls on_failure."""
        exc = type("APIConnectionError", (Exception,), {})("Connection refused")
        kwargs = {
            "model": "gpt-4o",
            "litellm_params": {"metadata": {"task_type": "indexing"}},
        }
        await logger_with_tracker.async_log_failure_event(kwargs, exc, None, None)
        assert len(logger_with_tracker._buffer) == 1
        entry = logger_with_tracker._buffer[0]
        assert entry.task_type == "indexing"
        assert entry.status == "failure"
        assert entry.error_type == "NETWORK_ERROR"
        assert "Connection refused" in entry.error_message

    @pytest.mark.asyncio
    async def test_task_type_from_direct_metadata(self, logger_with_tracker):
        """Test task_type extraction from direct metadata path."""
        kwargs = {"model": "test", "metadata": {"task_type": "qa_check"}}
        response = self._build_response(usage=None)
        await logger_with_tracker.on_success(kwargs, response, None, None)
        assert logger_with_tracker._buffer[0].task_type == "qa_check"

    @pytest.mark.asyncio
    async def test_unknown_task_type_defaults_to_conversation(
        self, logger_with_tracker
    ):
        kwargs = {
            "model": "test",
            "litellm_params": {"metadata": {"task_type": "invalid_type"}},
        }
        response = self._build_response(usage=None)
        await logger_with_tracker.on_success(kwargs, response, None, None)
        assert logger_with_tracker._buffer[0].task_type == "conversation"
