# Canvas Learning System - LiteLLM Configuration
# Story 7.2: LLM 调用日志与 Token 追踪
# [Source: _bmad-output/implementation-artifacts/7-2-llm-logging-token-tracking.md]
"""
LiteLLM callback registration for 100% LLM call logging coverage.

Registers the LLMCallLogger's success/failure callbacks with LiteLLM SDK
so that every call through litellm.acompletion() / litellm.aembedding()
is automatically intercepted and logged.

[Source: Story 7.2 Task 1.3 — Register LiteLLM callback handler]
[Source: Story 7.2 Dev Notes — LiteLLM Custom Callback registration]
[Source: architecture.md#Technical Stack — LiteLLM SDK (100+ models)]
"""

import logging

logger = logging.getLogger(__name__)


def register_litellm_callbacks() -> bool:
    """Register LLM call logging callbacks with LiteLLM SDK.

    This function registers the llm_call_logger's on_success and on_failure
    methods as LiteLLM callbacks. Once registered, ALL LLM calls made through
    litellm.acompletion() / litellm.aembedding() will be automatically logged.

    [Source: Story 7.2 AC #2 — 100% LLM call coverage (NFR-OBS-01)]

    Returns:
        True if callbacks were registered successfully, False if LiteLLM
        is not available.
    """
    try:
        import litellm

        from app.middleware.llm_call_logger import llm_call_logger

        # Register success callback
        if not hasattr(litellm, "success_callback"):
            litellm.success_callback = []
        if llm_call_logger.on_success not in litellm.success_callback:
            litellm.success_callback.append(llm_call_logger.on_success)

        # Register failure callback
        if not hasattr(litellm, "failure_callback"):
            litellm.failure_callback = []
        if llm_call_logger.on_failure not in litellm.failure_callback:
            litellm.failure_callback.append(llm_call_logger.on_failure)

        # Disable LiteLLM's own telemetry to avoid noise
        litellm.telemetry = False

        logger.info(
            "[Story 7.2] LiteLLM callbacks registered: "
            "success_callback + failure_callback"
        )
        return True

    except ImportError:
        logger.info(
            "[Story 7.2] LiteLLM not installed, callbacks not registered. "
            "LLM calls can still be logged via llm_call_logger.log_call()"
        )
        return False
    except Exception as e:
        logger.warning(f"[Story 7.2] Failed to register LiteLLM callbacks: {e}")
        return False
