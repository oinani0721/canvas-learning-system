# Canvas Learning System - LLM Call Logger
# Story 7.2: LLM 调用日志与 Token 追踪
# [Source: _bmad-output/implementation-artifacts/7-2-llm-logging-token-tracking.md]
"""
LiteLLM Custom Callback handler for structured LLM call logging.

Implements 100% LLM call coverage via LiteLLM success/failure callbacks.
Every call through litellm.acompletion() / litellm.aembedding() is
automatically intercepted, parsed, and logged to SQLite.

Features:
- Structured log extraction from LiteLLM callback kwargs
- API Key filtering (whitelist approach, NFR-SEC-02)
- task_type inference from metadata
- Batch write buffer (10 entries or 5 seconds)
- Error classification (LLM_ERROR / NETWORK_ERROR / CONFIG_ERROR)

[Source: architecture.md#Cross-Cutting Concerns #3 — LLM调用管理]
[Source: architecture.md#Cross-Cutting Concerns #7 — 错误处理与可观测性]
"""

import asyncio
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Enums (Task 1.2, Task 2.2, Task 2.5)
# [Source: Story 7.2 AC #3 — 5 task types]
# [Source: Story 7.2 AC #4 — 3 error categories]
# ═══════════════════════════════════════════════════════════════════════════════


class TaskType(str, Enum):
    """LLM call task type classification.

    [Source: Story 7.2 AC #3 — Token consumption by task type]
    Mapping:
    - context_assembler.py / chat.py -> CONVERSATION
    - autoscore.py -> SCORING
    - conversation_archive.py / error_classifier.py -> EXTRACTION
    - indexing/pipeline.py -> INDEXING
    - faithfulness_check.py -> QA_CHECK
    """

    CONVERSATION = "conversation"
    SCORING = "scoring"
    EXTRACTION = "extraction"
    INDEXING = "indexing"
    QA_CHECK = "qa_check"


class ErrorCategory(str, Enum):
    """LLM error classification categories.

    [Source: Story 7.2 Dev Notes — Error classification rules]
    """

    LLM_ERROR = "LLM_ERROR"
    NETWORK_ERROR = "NETWORK_ERROR"
    CONFIG_ERROR = "CONFIG_ERROR"


class CallStatus(str, Enum):
    """LLM call outcome status."""

    SUCCESS = "success"
    FAILURE = "failure"


# ═══════════════════════════════════════════════════════════════════════════════
# Pydantic Models (Task 1.2)
# [Source: Story 7.2 Dev Notes — Structured log schema]
# ═══════════════════════════════════════════════════════════════════════════════


class LLMCallLog(BaseModel):
    """Structured log entry for a single LLM call.

    [Source: Story 7.2 AC #1 — Required fields]
    [Source: Story 7.2 Dev Notes — Single LLM call log schema]
    """

    request_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique request identifier (UUID)",
    )
    task_type: str = Field(
        default=TaskType.CONVERSATION.value,
        description="Task type classification",
    )
    model_name: str = Field(
        default="unknown",
        description="LLM model name used",
    )
    input_tokens: int = Field(
        default=0,
        description="Number of input/prompt tokens",
    )
    output_tokens: int = Field(
        default=0,
        description="Number of output/completion tokens",
    )
    total_tokens: int = Field(
        default=0,
        description="Total tokens (input + output)",
    )
    latency_ms: int = Field(
        default=0,
        description="Response latency in milliseconds",
    )
    estimated_cost_usd: Optional[float] = Field(
        default=None,
        description="Estimated cost in USD (from LiteLLM pricing DB)",
    )
    status: str = Field(
        default=CallStatus.SUCCESS.value,
        description="Call outcome: success or failure",
    )
    error_type: Optional[str] = Field(
        default=None,
        description="Error category if failed (LLM_ERROR/NETWORK_ERROR/CONFIG_ERROR)",
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if failed (truncated to 500 chars)",
    )
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%S.%f"
        )[:-3]
        + "Z",
        description="Timestamp in ISO 8601 format",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# API Key Filtering (Task 1.4)
# [Source: Story 7.2 AC #6 — API Key must not appear in logs (NFR-SEC-02)]
# ═══════════════════════════════════════════════════════════════════════════════

# Whitelist approach: only these fields are extracted from LiteLLM kwargs
_SAFE_KWARGS_FIELDS = frozenset(
    {
        "model",
        "response_cost",
        "response_time",
        "stream",
        "call_type",
        "optional_params",
    }
)

_SAFE_METADATA_FIELDS = frozenset(
    {
        "task_type",
        "request_id",
    }
)


def _sanitize_kwargs(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """Extract only safe fields from LiteLLM callback kwargs.

    Uses whitelist approach (NFR-SEC-02): only explicitly allowed
    fields are kept. API keys, authorization headers, and other
    sensitive data are never included.

    Args:
        kwargs: Raw LiteLLM callback kwargs

    Returns:
        Sanitized dict with only safe fields
    """
    safe = {}
    for key in _SAFE_KWARGS_FIELDS:
        if key in kwargs:
            safe[key] = kwargs[key]

    # Sanitize nested metadata
    litellm_params = kwargs.get("litellm_params", {})
    if isinstance(litellm_params, dict):
        metadata = litellm_params.get("metadata", {})
        if isinstance(metadata, dict):
            safe["metadata"] = {
                k: v for k, v in metadata.items() if k in _SAFE_METADATA_FIELDS
            }

    return safe


# ═══════════════════════════════════════════════════════════════════════════════
# Error Classification (Task 2.5)
# [Source: Story 7.2 Dev Notes — Error classification rules table]
# ═══════════════════════════════════════════════════════════════════════════════

# Maps LiteLLM exception class names to error categories
_ERROR_CLASSIFICATION: Dict[str, ErrorCategory] = {
    "AuthenticationError": ErrorCategory.CONFIG_ERROR,
    "RateLimitError": ErrorCategory.LLM_ERROR,
    "APIError": ErrorCategory.LLM_ERROR,
    "ServiceUnavailableError": ErrorCategory.LLM_ERROR,
    "Timeout": ErrorCategory.NETWORK_ERROR,
    "APIConnectionError": ErrorCategory.NETWORK_ERROR,
    "NotFoundError": ErrorCategory.CONFIG_ERROR,
    "BadRequestError": ErrorCategory.LLM_ERROR,
}


def classify_error(exception: Exception) -> ErrorCategory:
    """Classify an LLM exception into an error category.

    [Source: Story 7.2 Dev Notes — Error classification rules]

    Args:
        exception: The exception from the LLM call

    Returns:
        ErrorCategory enum value
    """
    exc_name = type(exception).__name__

    if exc_name in _ERROR_CLASSIFICATION:
        return _ERROR_CLASSIFICATION[exc_name]

    # Fallback heuristics
    exc_str = str(exception).lower()
    if any(kw in exc_str for kw in ("timeout", "timed out", "deadline")):
        return ErrorCategory.NETWORK_ERROR
    if any(kw in exc_str for kw in ("connection", "connect", "dns", "resolve")):
        return ErrorCategory.NETWORK_ERROR
    if any(kw in exc_str for kw in ("auth", "key", "credential", "permission")):
        return ErrorCategory.CONFIG_ERROR

    return ErrorCategory.LLM_ERROR


# ═══════════════════════════════════════════════════════════════════════════════
# LLM Call Logger (Task 1.1, 1.3, 1.5)
# [Source: Story 7.2 Dev Notes — LiteLLM Custom Callback]
# ═══════════════════════════════════════════════════════════════════════════════


class LLMCallLogger:
    """LiteLLM callback handler for 100% LLM call logging coverage.

    Implements success_callback and failure_callback for LiteLLM SDK.
    Buffers log entries and flushes to SQLite via CostTracker in batches.

    [Source: Story 7.2 AC #1, #2 — 100% coverage via LiteLLM callbacks]
    [Source: Story 7.2 Dev Notes — Batch write optimization (10 entries or 5s)]
    """

    BATCH_SIZE = 10
    FLUSH_INTERVAL_SECONDS = 5.0

    def __init__(self) -> None:
        self._buffer: List[LLMCallLog] = []
        self._lock = asyncio.Lock()
        self._flush_task: Optional[asyncio.Task] = None
        self._cost_tracker: Optional[Any] = None
        self._running = False

    async def start(self, cost_tracker: Any) -> None:
        """Start the logger with a CostTracker for persistence.

        Args:
            cost_tracker: CostTracker instance for SQLite writes
        """
        self._cost_tracker = cost_tracker
        self._running = True
        self._flush_task = asyncio.create_task(self._periodic_flush())
        logger.info("[Story 7.2] LLM Call Logger started")

    async def stop(self) -> None:
        """Stop the logger and flush remaining buffer."""
        self._running = False
        if self._flush_task and not self._flush_task.done():
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
        # Final flush
        await self._flush_buffer()
        logger.info("[Story 7.2] LLM Call Logger stopped")

    def _extract_task_type(self, kwargs: Dict[str, Any]) -> str:
        """Infer task_type from LiteLLM metadata.

        [Source: Story 7.2 Task 1.5 — task_type auto-inference]

        Args:
            kwargs: LiteLLM callback kwargs

        Returns:
            task_type string, defaults to 'conversation'
        """
        litellm_params = kwargs.get("litellm_params", {})
        if isinstance(litellm_params, dict):
            metadata = litellm_params.get("metadata", {})
            if isinstance(metadata, dict):
                task_type = metadata.get("task_type", "")
                # Validate against known types
                try:
                    return TaskType(task_type).value
                except ValueError:
                    pass

        # Direct metadata access (alternative path)
        metadata = kwargs.get("metadata", {})
        if isinstance(metadata, dict):
            task_type = metadata.get("task_type", "")
            try:
                return TaskType(task_type).value
            except ValueError:
                pass

        return TaskType.CONVERSATION.value

    def _extract_request_id(self, kwargs: Dict[str, Any]) -> str:
        """Extract request_id from metadata or generate a new one.

        Args:
            kwargs: LiteLLM callback kwargs

        Returns:
            request_id string
        """
        for params_key in ("litellm_params", "metadata"):
            params = kwargs.get(params_key, {})
            if isinstance(params, dict):
                metadata = params.get("metadata", params)
                if isinstance(metadata, dict):
                    rid = metadata.get("request_id")
                    if rid:
                        return str(rid)

        return str(uuid4())

    async def on_success(
        self,
        kwargs: Dict[str, Any],
        completion_response: Any,
        start_time: Any,
        end_time: Any,
    ) -> None:
        """LiteLLM success callback.

        Called automatically by LiteLLM after every successful LLM call.

        [Source: Story 7.2 AC #1 — Auto-record structured log]

        Args:
            kwargs: LiteLLM call kwargs (model, messages, etc.)
            completion_response: LiteLLM ModelResponse
            start_time: Call start timestamp
            end_time: Call end timestamp
        """
        try:
            # Extract token usage
            input_tokens = 0
            output_tokens = 0
            total_tokens = 0

            if hasattr(completion_response, "usage") and completion_response.usage:
                usage = completion_response.usage
                input_tokens = getattr(usage, "prompt_tokens", 0) or 0
                output_tokens = getattr(usage, "completion_tokens", 0) or 0
                total_tokens = getattr(usage, "total_tokens", 0) or (
                    input_tokens + output_tokens
                )

            # Calculate latency
            latency_ms = 0
            if start_time and end_time:
                if isinstance(start_time, (int, float)) and isinstance(
                    end_time, (int, float)
                ):
                    latency_ms = int((end_time - start_time) * 1000)
                elif hasattr(start_time, "timestamp") and hasattr(
                    end_time, "timestamp"
                ):
                    latency_ms = int(
                        (end_time.timestamp() - start_time.timestamp()) * 1000
                    )

            # Extract cost (LiteLLM built-in pricing)
            estimated_cost = kwargs.get("response_cost")
            if estimated_cost is not None:
                try:
                    estimated_cost = float(estimated_cost)
                except (ValueError, TypeError):
                    estimated_cost = None

            log_entry = LLMCallLog(
                request_id=self._extract_request_id(kwargs),
                task_type=self._extract_task_type(kwargs),
                model_name=kwargs.get("model", "unknown"),
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
                latency_ms=latency_ms,
                estimated_cost_usd=estimated_cost,
                status=CallStatus.SUCCESS.value,
            )

            await self._add_to_buffer(log_entry)

        except Exception as e:
            # Never let logging errors affect the main LLM call flow
            logger.warning(f"[Story 7.2] Failed to log LLM success: {e}")

    async def on_failure(
        self,
        kwargs: Dict[str, Any],
        completion_response: Any,
        start_time: Any,
        end_time: Any,
    ) -> None:
        """LiteLLM failure callback.

        Called automatically by LiteLLM after every failed LLM call.

        [Source: Story 7.2 AC #4 — Error auto-classification]

        Args:
            kwargs: LiteLLM call kwargs
            completion_response: Exception or error response
            start_time: Call start timestamp
            end_time: Call end timestamp
        """
        try:
            # Calculate latency
            latency_ms = 0
            if start_time and end_time:
                if isinstance(start_time, (int, float)) and isinstance(
                    end_time, (int, float)
                ):
                    latency_ms = int((end_time - start_time) * 1000)
                elif hasattr(start_time, "timestamp") and hasattr(
                    end_time, "timestamp"
                ):
                    latency_ms = int(
                        (end_time.timestamp() - start_time.timestamp()) * 1000
                    )

            # Classify the error
            exception = completion_response if isinstance(
                completion_response, Exception
            ) else kwargs.get("exception", Exception("Unknown error"))

            if not isinstance(exception, Exception):
                exception = Exception(str(completion_response))

            error_cat = classify_error(exception)
            error_msg = str(exception)[:500]  # Truncate to 500 chars

            log_entry = LLMCallLog(
                request_id=self._extract_request_id(kwargs),
                task_type=self._extract_task_type(kwargs),
                model_name=kwargs.get("model", "unknown"),
                input_tokens=0,
                output_tokens=0,
                total_tokens=0,
                latency_ms=latency_ms,
                estimated_cost_usd=None,
                status=CallStatus.FAILURE.value,
                error_type=error_cat.value,
                error_message=error_msg,
            )

            await self._add_to_buffer(log_entry)

        except Exception as e:
            logger.warning(f"[Story 7.2] Failed to log LLM failure: {e}")

    async def log_call(self, log_entry: LLMCallLog) -> None:
        """Manually log an LLM call (for non-LiteLLM providers).

        This provides a direct logging API for code that doesn't use
        LiteLLM but still needs call tracking.

        Args:
            log_entry: Pre-built LLMCallLog entry
        """
        await self._add_to_buffer(log_entry)

    async def _add_to_buffer(self, entry: LLMCallLog) -> None:
        """Add entry to buffer and flush if batch size reached."""
        async with self._lock:
            self._buffer.append(entry)
            if len(self._buffer) >= self.BATCH_SIZE:
                await self._flush_buffer_locked()

    async def _flush_buffer(self) -> None:
        """Flush buffer to SQLite via CostTracker."""
        async with self._lock:
            await self._flush_buffer_locked()

    async def _flush_buffer_locked(self) -> None:
        """Flush buffer (must hold self._lock)."""
        if not self._buffer or not self._cost_tracker:
            return

        entries = self._buffer[:]
        self._buffer.clear()

        try:
            await self._cost_tracker.insert_logs(entries)
        except Exception as e:
            logger.error(f"[Story 7.2] Failed to flush {len(entries)} log entries: {e}")
            # Re-add failed entries to buffer (up to 2x batch size to prevent unbounded growth)
            if len(self._buffer) < self.BATCH_SIZE * 2:
                self._buffer.extend(entries)

    async def _periodic_flush(self) -> None:
        """Background task: flush buffer every FLUSH_INTERVAL_SECONDS."""
        while self._running:
            try:
                await asyncio.sleep(self.FLUSH_INTERVAL_SECONDS)
                await self._flush_buffer()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"[Story 7.2] Periodic flush error: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# Module-level singleton
# ═══════════════════════════════════════════════════════════════════════════════

llm_call_logger = LLMCallLogger()
