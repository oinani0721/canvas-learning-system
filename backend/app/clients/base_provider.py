# Canvas Learning System - Base AI Provider Interface
# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: dependency injection)
"""
Abstract base class for AI providers.

This module defines the interface that all AI providers must implement,
enabling a unified API for multi-provider support with automatic failover.

[Source: docs/prd/EPIC-20-BACKEND-STABILITY-MULTI-PROVIDER.md]
[Source: Story 20.1 - Multi-Provider Architecture Design]
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ProviderStatus(str, Enum):
    """Provider health status enum."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ProviderHealth:
    """
    Provider health status information.

    Attributes:
        status: Current health status
        latency_ms: Last measured response latency in milliseconds
        last_check: Timestamp of last health check
        consecutive_failures: Number of consecutive failures
        error_message: Last error message if unhealthy
    """
    status: ProviderStatus = ProviderStatus.UNKNOWN
    latency_ms: Optional[float] = None
    last_check: Optional[datetime] = None
    consecutive_failures: int = 0
    error_message: Optional[str] = None

    @property
    def is_healthy(self) -> bool:
        """Check if provider is available for requests."""
        return self.status in (ProviderStatus.HEALTHY, ProviderStatus.DEGRADED)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "status": self.status.value,
            "latency_ms": self.latency_ms,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "consecutive_failures": self.consecutive_failures,
            "error_message": self.error_message,
        }


@dataclass
class ProviderConfig:
    """
    Provider configuration.

    Attributes:
        name: Provider identifier (e.g., 'google', 'openai', 'anthropic')
        api_key: API key for authentication
        model: Default model name
        base_url: Optional custom API base URL
        priority: Provider priority (lower = higher priority)
        enabled: Whether provider is enabled
        timeout: Request timeout in seconds
        max_retries: Maximum retry attempts
    """
    name: str
    api_key: str
    model: str
    base_url: Optional[str] = None
    priority: int = 10
    enabled: bool = True
    timeout: float = 120.0
    max_retries: int = 3
    extra_config: Dict[str, Any] = field(default_factory=dict)

    def is_valid(self) -> bool:
        """Check if configuration is valid."""
        return bool(self.name and self.api_key and self.model)

    @property
    def masked_api_key(self) -> str:
        """Return masked API key for logging (show first 4 and last 4 chars)."""
        if not self.api_key:
            return "<not set>"
        if len(self.api_key) <= 12:
            return "*" * len(self.api_key)
        return f"{self.api_key[:4]}...{self.api_key[-4:]}"


@dataclass
class ProviderResponse:
    """
    Standardized response from AI provider.

    Attributes:
        text: Response text content
        model: Model used for generation
        provider: Provider name
        input_tokens: Number of input tokens (if available)
        output_tokens: Number of output tokens (if available)
        latency_ms: Request latency in milliseconds
        raw_response: Original provider response (for debugging)
    """
    text: str
    model: str
    provider: str
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0
    raw_response: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "text": self.text,
            "model": self.model,
            "provider": self.provider,
            "usage": {
                "input_tokens": self.input_tokens,
                "output_tokens": self.output_tokens,
            },
            "latency_ms": self.latency_ms,
        }


class BaseProvider(ABC):
    """
    Abstract base class for AI providers.

    All AI providers must implement this interface to work with the
    ProviderFactory and automatic failover system.

    Attributes:
        config: Provider configuration
        health: Current health status
    """

    def __init__(self, config: ProviderConfig):
        """
        Initialize provider with configuration.

        Args:
            config: Provider configuration
        """
        self.config = config
        self.health = ProviderHealth()
        self._initialized = False

        logger.info(
            f"Initializing {self.__class__.__name__} provider: "
            f"name={config.name}, model={config.model}, "
            f"api_key={config.masked_api_key}"
        )

    @property
    def name(self) -> str:
        """Get provider name."""
        return self.config.name

    @property
    def priority(self) -> int:
        """Get provider priority."""
        return self.config.priority

    @property
    def is_enabled(self) -> bool:
        """Check if provider is enabled."""
        return self.config.enabled

    @property
    def is_available(self) -> bool:
        """Check if provider is available (enabled and healthy)."""
        return self.is_enabled and self.health.is_healthy

    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize provider connection.

        Returns:
            True if initialization successful, False otherwise
        """
        pass

    @abstractmethod
    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> ProviderResponse:
        """
        Generate completion from the AI model.

        Args:
            system_prompt: System prompt text
            user_prompt: User prompt text
            temperature: Response randomness (0.0-1.0)
            max_tokens: Maximum tokens in response
            **kwargs: Additional provider-specific options

        Returns:
            ProviderResponse with generated text and metadata

        Raises:
            ProviderError: If API call fails
        """
        pass

    @abstractmethod
    async def complete_with_images(
        self,
        system_prompt: str,
        user_prompt: str,
        images: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> ProviderResponse:
        """
        Generate completion with image inputs (multimodal).

        Args:
            system_prompt: System prompt text
            user_prompt: User prompt text
            images: List of image dicts with 'data' (base64) and 'media_type'
            temperature: Response randomness (0.0-1.0)
            max_tokens: Maximum tokens in response
            **kwargs: Additional provider-specific options

        Returns:
            ProviderResponse with generated text and metadata

        Raises:
            ProviderError: If API call fails
            NotImplementedError: If provider doesn't support images
        """
        pass

    @abstractmethod
    async def health_check(self) -> ProviderHealth:
        """
        Check provider health status.

        Should make a lightweight API call to verify connectivity.

        Returns:
            ProviderHealth with current status
        """
        pass

    async def update_health(self, success: bool, latency_ms: float = 0.0, error: Optional[str] = None) -> None:
        """
        Update health status after a request.

        Args:
            success: Whether the request succeeded
            latency_ms: Request latency in milliseconds
            error: Error message if failed
        """
        self.health.last_check = datetime.now()
        self.health.latency_ms = latency_ms

        if success:
            self.health.consecutive_failures = 0
            self.health.error_message = None
            self.health.status = ProviderStatus.HEALTHY
        else:
            self.health.consecutive_failures += 1
            self.health.error_message = error

            # Mark as unhealthy after 3 consecutive failures
            if self.health.consecutive_failures >= 3:
                self.health.status = ProviderStatus.UNHEALTHY
            elif self.health.consecutive_failures >= 1:
                self.health.status = ProviderStatus.DEGRADED

        logger.debug(
            f"Provider {self.name} health updated: "
            f"status={self.health.status.value}, "
            f"latency={latency_ms:.0f}ms, "
            f"failures={self.health.consecutive_failures}"
        )

    async def close(self) -> None:
        """
        Clean up provider resources.

        Should be called when provider is being removed.
        """
        self._initialized = False
        logger.info(f"Provider {self.name} closed")


class ProviderError(Exception):
    """Base exception for provider errors."""

    def __init__(self, message: str, provider: str, cause: Optional[Exception] = None):
        super().__init__(message)
        self.provider = provider
        self.cause = cause


class NoHealthyProviderError(ProviderError):
    """Raised when no healthy provider is available."""

    def __init__(self, message: str = "No healthy provider available"):
        super().__init__(message, provider="none")


class ProviderNotFoundError(ProviderError):
    """Raised when requested provider is not found."""

    def __init__(self, provider: str):
        super().__init__(f"Provider not found: {provider}", provider=provider)
