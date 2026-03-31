# Canvas Learning System - LiteLLM Configuration
# Story 1.3: Model Configuration & Runtime Config Management
# Story 7.2: LLM 调用日志与 Token 追踪
# [Source: _bmad-output/implementation-artifacts/1-3-model-config-settings-panel.md#Task 9]
# [Source: _bmad-output/implementation-artifacts/7-2-llm-logging-token-tracking.md]
"""
LiteLLM runtime model configuration and callback registration.

Story 1.3: Provides Pydantic models for per-task LLM configuration
(chat / scoring / embedding) and a singleton RuntimeModelConfigManager
that holds API keys in memory only (never persisted to backend disk).

Story 7.2: Registers the LLMCallLogger's success/failure callbacks
with LiteLLM SDK so that every call is automatically logged.

[Source: Story 1.3 Task 9.1 — ModelTaskConfig / SystemModelConfig]
[Source: Story 1.3 Task 9.4 — LiteLLM model name format mapping]
[Source: Story 1.3 Task 9.5 — API Key in-memory only, no disk persistence]
[Source: Story 7.2 Task 1.3 — Register LiteLLM callback handler]
[Source: architecture.md#Technical Stack — LiteLLM SDK (100+ models)]
"""

import logging
from typing import Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Story 1.3 — Runtime Model Configuration
# [Source: _bmad-output/implementation-artifacts/1-3-model-config-settings-panel.md]
# ═══════════════════════════════════════════════════════════════════════════════


class ModelTaskConfig(BaseModel):
    """Configuration for a single LLM task (chat, scoring, or embedding).

    [Source: Story 1.3 Task 9.1]
    """

    provider: str = Field(
        ..., description="LLM provider: gemini, anthropic, openai, ollama"
    )
    model_name: str = Field(..., description="Model identifier (e.g. gemini-2.0-flash)")
    api_key: str = Field(default="", description="API key for this provider")


class SystemModelConfig(BaseModel):
    """Aggregated model configuration for all three task types.

    [Source: Story 1.3 Task 9.1]
    [Source: architecture.md — dual-layer key separation]
    """

    chat: Optional[ModelTaskConfig] = Field(
        default=None, description="Chat / conversation model (outer layer)"
    )
    scoring: Optional[ModelTaskConfig] = Field(
        default=None, description="Scoring / extraction model (inner layer)"
    )
    embedding: Optional[ModelTaskConfig] = Field(
        default=None, description="Embedding model (read-only, Ollama bge-m3)"
    )


# ── Provider → LiteLLM model-name prefix mapping ─────────────────────────────
# [Source: Story 1.3 Dev Notes — LiteLLM 模型名称格式]

_PROVIDER_PREFIX: dict[str, str] = {
    "gemini": "gemini",
    "anthropic": "anthropic",
    "openai": "",  # OpenAI models don't need a prefix in LiteLLM
    "ollama": "ollama",
    "lm_studio": "lm_studio",
    "deepseek": "deepseek",
    "qwen": "openai",  # Qwen models route through OpenAI-compatible API
}


def format_litellm_model(provider: str, model_name: str) -> str:
    """Build the LiteLLM-compatible ``provider/model`` string.

    [Source: Story 1.3 Task 9.4]

    Args:
        provider: Provider key (gemini, anthropic, openai, ollama, …).
        model_name: Raw model identifier.

    Returns:
        Formatted model string ready for ``litellm.acompletion(model=…)``.
    """
    prefix = _PROVIDER_PREFIX.get(provider, provider)
    if not prefix:
        return model_name
    # Avoid double-prefixing (e.g. user already typed "gemini/gemini-2.0-flash")
    if model_name.startswith(f"{prefix}/"):
        return model_name
    return f"{prefix}/{model_name}"


class RuntimeModelConfigManager:
    """Singleton that holds model configuration in memory.

    API keys are **never** persisted to the backend filesystem.
    The frontend pushes configuration via ``POST /api/v1/system/config``
    and the backend keeps it only in this in-memory object.

    [Source: Story 1.3 Task 9.5 — API Key in-memory only]
    """

    _instance: Optional["RuntimeModelConfigManager"] = None

    def __new__(cls) -> "RuntimeModelConfigManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._config = SystemModelConfig()
        return cls._instance

    # ── Public API ────────────────────────────────────────────────────────────

    def update(self, config: SystemModelConfig) -> None:
        """Replace the current runtime configuration.

        [Source: Story 1.3 Task 9.2]
        """
        self._config = config
        logger.info(
            "[Story 1.3] Runtime model config updated — chat=%s, scoring=%s",
            self._config.chat.provider if self._config.chat else "none",
            self._config.scoring.provider if self._config.scoring else "none",
        )

    @property
    def config(self) -> SystemModelConfig:
        return self._config

    def get_chat_model(self) -> Optional[str]:
        """Return the LiteLLM-formatted chat model string, or None."""
        if self._config.chat and self._config.chat.model_name:
            return format_litellm_model(
                self._config.chat.provider, self._config.chat.model_name
            )
        return None

    def get_chat_api_key(self) -> Optional[str]:
        """Return the chat API key, or None."""
        if self._config.chat and self._config.chat.api_key:
            return self._config.chat.api_key
        return None

    def get_scoring_model(self) -> Optional[str]:
        """Return the LiteLLM-formatted scoring model string.

        Falls back to the chat model when no scoring model is configured,
        matching the frontend UI hint "leave empty to reuse Chat API Key".
        """
        if self._config.scoring and self._config.scoring.model_name:
            return format_litellm_model(
                self._config.scoring.provider, self._config.scoring.model_name
            )
        return self.get_chat_model()

    def get_scoring_api_key(self) -> Optional[str]:
        """Return the scoring API key.

        Falls back to the chat API key when no scoring key is configured,
        matching the frontend UI hint "leave empty to reuse Chat API Key".
        """
        if self._config.scoring and self._config.scoring.api_key:
            return self._config.scoring.api_key
        return self.get_chat_api_key()


def get_runtime_model_config() -> RuntimeModelConfigManager:
    """Return the singleton RuntimeModelConfigManager.

    Usage::

        from app.core.litellm_config import get_runtime_model_config
        cfg = get_runtime_model_config()
        model = cfg.get_scoring_model()   # e.g. "gemini/gemini-2.0-flash"
        key   = cfg.get_scoring_api_key() # e.g. "AIza..."
    """
    return RuntimeModelConfigManager()


# ═══════════════════════════════════════════════════════════════════════════════
# Story 7.2 — LiteLLM Callback Registration
# [Source: _bmad-output/implementation-artifacts/7-2-llm-logging-token-tracking.md]
# ═══════════════════════════════════════════════════════════════════════════════


def register_litellm_callbacks() -> bool:
    """Register LLM call logging callbacks with LiteLLM SDK.

    Registers the ``llm_call_logger`` (a ``CustomLogger`` subclass) via
    ``litellm.callbacks``.  This ensures that **all** async LLM calls made
    through ``litellm.acompletion()`` / ``litellm.aembedding()`` automatically
    invoke ``async_log_success_event`` and ``async_log_failure_event``.

    Reference: https://docs.litellm.ai/docs/observability/custom_callback

    [Source: Story 7.2 AC #2 — 100% LLM call coverage (NFR-OBS-01)]

    Returns:
        True if callbacks were registered successfully, False if LiteLLM
        is not available.
    """
    try:
        import litellm

        from app.middleware.llm_call_logger import llm_call_logger

        # Register the CustomLogger instance via litellm.callbacks.
        # This is the recommended approach for async callbacks.
        # Reference: https://docs.litellm.ai/docs/observability/custom_callback
        if not hasattr(litellm, "callbacks") or litellm.callbacks is None:
            litellm.callbacks = []
        if llm_call_logger not in litellm.callbacks:
            litellm.callbacks.append(llm_call_logger)

        # Disable LiteLLM's own telemetry to avoid noise
        litellm.telemetry = False

        logger.info(
            "[Story 7.2] LiteLLM CustomLogger callback registered via litellm.callbacks"
        )
        return True

    except ImportError:
        logger.info(
            "[Story 7.2] LiteLLM not installed, callbacks not registered. "
            "LLM calls can still be logged via llm_call_logger.log_call()"
        )
        return False
    except (AttributeError, TypeError, ValueError) as e:
        logger.warning(f"[Story 7.2] Failed to register LiteLLM callbacks: {e}")
        return False
