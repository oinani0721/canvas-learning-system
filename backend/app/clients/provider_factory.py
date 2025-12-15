# Canvas Learning System - AI Provider Factory
# ✅ Story 20.2: Provider Switching Mechanism
"""
AI Provider Factory with automatic failover and selection strategies.

This module implements the ProviderFactory pattern for managing multiple AI providers,
supporting automatic failover, health-based selection, and multiple selection strategies.

[Source: docs/prd/EPIC-20-BACKEND-STABILITY-MULTI-PROVIDER.md]
[Source: Story 20.2 - Provider Switching Mechanism]
"""

import asyncio
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Type

from app.clients.base_provider import (
    BaseProvider,
    NoHealthyProviderError,
    ProviderConfig,
    ProviderError,
    ProviderHealth,
    ProviderNotFoundError,
    ProviderResponse,
    ProviderStatus,
)
from app.config import settings

logger = logging.getLogger(__name__)


class SelectionStrategy(str, Enum):
    """Provider selection strategy enum."""
    PRIORITY = "priority"          # Select by priority (default)
    ROUND_ROBIN = "round_robin"    # Rotate between healthy providers
    LATENCY_OPTIMAL = "latency"    # Select lowest latency provider


class ProviderFactory:
    """
    AI Provider Factory with automatic failover.

    Manages multiple AI providers with support for:
    - Provider registration and initialization
    - Multiple selection strategies (priority, round-robin, latency-optimal)
    - Automatic failover on provider failure
    - Health status tracking

    Usage:
        factory = ProviderFactory.get_instance()
        await factory.initialize_providers()

        # Get best available provider
        provider = factory.get_provider()

        # Or get specific provider
        provider = factory.get_provider(name="google")
    """

    _instance: Optional["ProviderFactory"] = None
    _lock = asyncio.Lock()

    def __init__(self):
        """Initialize ProviderFactory (use get_instance() instead)."""
        self._providers: Dict[str, BaseProvider] = {}
        self._priority_order: List[str] = []
        self._round_robin_index: int = 0
        self._selection_strategy: SelectionStrategy = SelectionStrategy.PRIORITY
        self._initialized: bool = False
        self._switch_count: int = 0
        self._last_switch_time: Optional[datetime] = None

    @classmethod
    async def get_instance(cls) -> "ProviderFactory":
        """
        Get singleton ProviderFactory instance.

        Returns:
            ProviderFactory singleton instance
        """
        if cls._instance is None:
            async with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton instance (for testing)."""
        cls._instance = None

    def set_selection_strategy(self, strategy: SelectionStrategy) -> None:
        """
        Set the provider selection strategy.

        Args:
            strategy: Selection strategy to use
        """
        self._selection_strategy = strategy
        logger.info(f"Provider selection strategy set to: {strategy.value}")

    async def register_provider(
        self,
        provider_class: Type[BaseProvider],
        config: ProviderConfig,
    ) -> bool:
        """
        Register a new provider.

        Args:
            provider_class: Provider class to instantiate
            config: Provider configuration

        Returns:
            True if registration successful

        Raises:
            ValueError: If provider with same name already registered
        """
        if config.name in self._providers:
            logger.warning(f"Provider {config.name} already registered, skipping")
            return False

        try:
            provider = provider_class(config)
            success = await provider.initialize()

            if success:
                self._providers[config.name] = provider
                self._update_priority_order()
                logger.info(
                    f"Provider {config.name} registered: "
                    f"priority={config.priority}, model={config.model}"
                )
                return True
            else:
                logger.error(f"Failed to initialize provider {config.name}")
                return False

        except Exception as e:
            logger.error(f"Error registering provider {config.name}: {e}")
            return False

    async def initialize_providers(self) -> int:
        """
        Initialize all configured providers from settings.

        Reads provider configurations from app settings and initializes them.

        Returns:
            Number of successfully initialized providers
        """
        if self._initialized:
            logger.warning("ProviderFactory already initialized")
            return len(self._providers)

        # Import provider implementations here to avoid circular imports
        from app.clients.anthropic_provider import AnthropicProvider
        from app.clients.google_provider import GoogleProvider
        from app.clients.openai_provider import OpenAIProvider

        provider_classes: Dict[str, Type[BaseProvider]] = {
            "google": GoogleProvider,
            "openai": OpenAIProvider,
            "anthropic": AnthropicProvider,
        }

        initialized_count = 0

        # Parse provider configurations from settings
        configs = self._parse_provider_configs()

        for config in configs:
            if not config.enabled:
                logger.info(f"Provider {config.name} is disabled, skipping")
                continue

            provider_class = provider_classes.get(config.name.lower())
            if not provider_class:
                logger.warning(f"Unknown provider type: {config.name}")
                continue

            success = await self.register_provider(provider_class, config)
            if success:
                initialized_count += 1

        self._initialized = True
        logger.info(f"ProviderFactory initialized with {initialized_count} providers")

        return initialized_count

    def _parse_provider_configs(self) -> List[ProviderConfig]:
        """
        Parse provider configurations from settings.

        Returns:
            List of ProviderConfig objects
        """
        configs: List[ProviderConfig] = []

        # Primary provider from legacy settings
        if hasattr(settings, 'AI_PROVIDER') and settings.AI_PROVIDER:
            primary_config = ProviderConfig(
                name=settings.AI_PROVIDER,
                api_key=getattr(settings, 'AI_API_KEY', '') or
                        getattr(settings, 'GOOGLE_API_KEY', '') or
                        getattr(settings, 'OPENAI_API_KEY', '') or
                        getattr(settings, 'ANTHROPIC_API_KEY', ''),
                model=getattr(settings, 'AI_MODEL_NAME', '') or
                      getattr(settings, 'GEMINI_MODEL', 'gemini-2.0-flash-exp'),
                base_url=getattr(settings, 'AI_BASE_URL', None),
                priority=1,
                enabled=True,
            )
            if primary_config.api_key:
                configs.append(primary_config)

        # Multi-provider configs (numbered)
        for i in range(1, 6):  # Support up to 5 providers
            name_key = f'AI_PROVIDER_{i}_NAME'
            key_key = f'AI_PROVIDER_{i}_API_KEY'
            model_key = f'AI_PROVIDER_{i}_MODEL'
            priority_key = f'AI_PROVIDER_{i}_PRIORITY'
            base_url_key = f'AI_PROVIDER_{i}_BASE_URL'
            enabled_key = f'AI_PROVIDER_{i}_ENABLED'

            name = getattr(settings, name_key, None)
            api_key = getattr(settings, key_key, None)

            if name and api_key:
                config = ProviderConfig(
                    name=name,
                    api_key=api_key,
                    model=getattr(settings, model_key, 'gemini-2.0-flash-exp'),
                    base_url=getattr(settings, base_url_key, None),
                    priority=int(getattr(settings, priority_key, i * 10)),
                    enabled=getattr(settings, enabled_key, 'true').lower() == 'true',
                )
                configs.append(config)

        # Also check direct provider API keys
        if hasattr(settings, 'GOOGLE_API_KEY') and settings.GOOGLE_API_KEY:
            if not any(c.name.lower() == 'google' for c in configs):
                configs.append(ProviderConfig(
                    name='google',
                    api_key=settings.GOOGLE_API_KEY,
                    model=getattr(settings, 'GEMINI_MODEL', 'gemini-2.0-flash-exp'),
                    priority=10,
                ))

        if hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY:
            if not any(c.name.lower() == 'openai' for c in configs):
                configs.append(ProviderConfig(
                    name='openai',
                    api_key=settings.OPENAI_API_KEY,
                    model='gpt-4o',
                    priority=20,
                ))

        if hasattr(settings, 'ANTHROPIC_API_KEY') and settings.ANTHROPIC_API_KEY:
            if not any(c.name.lower() == 'anthropic' for c in configs):
                configs.append(ProviderConfig(
                    name='anthropic',
                    api_key=settings.ANTHROPIC_API_KEY,
                    model='claude-3-5-sonnet-20241022',
                    priority=30,
                ))

        logger.info(f"Parsed {len(configs)} provider configurations")
        return configs

    def _update_priority_order(self) -> None:
        """Update provider priority order."""
        self._priority_order = sorted(
            self._providers.keys(),
            key=lambda name: self._providers[name].priority
        )

    def get_provider(self, name: Optional[str] = None) -> BaseProvider:
        """
        Get an available provider.

        Args:
            name: Optional specific provider name

        Returns:
            Available provider instance

        Raises:
            ProviderNotFoundError: If named provider not found
            NoHealthyProviderError: If no healthy provider available
        """
        if name:
            if name not in self._providers:
                raise ProviderNotFoundError(name)
            return self._providers[name]

        # Use selection strategy
        provider = self._select_provider()
        if not provider:
            raise NoHealthyProviderError()

        return provider

    def _select_provider(self) -> Optional[BaseProvider]:
        """
        Select provider based on current strategy.

        Returns:
            Selected provider or None if no healthy provider
        """
        healthy_providers = [
            p for p in self._providers.values()
            if p.is_available
        ]

        if not healthy_providers:
            return None

        if self._selection_strategy == SelectionStrategy.PRIORITY:
            return self._select_by_priority(healthy_providers)
        elif self._selection_strategy == SelectionStrategy.ROUND_ROBIN:
            return self._select_round_robin(healthy_providers)
        elif self._selection_strategy == SelectionStrategy.LATENCY_OPTIMAL:
            return self._select_by_latency(healthy_providers)
        else:
            return self._select_by_priority(healthy_providers)

    def _select_by_priority(self, providers: List[BaseProvider]) -> BaseProvider:
        """Select highest priority (lowest number) provider."""
        return min(providers, key=lambda p: p.priority)

    def _select_round_robin(self, providers: List[BaseProvider]) -> BaseProvider:
        """Select next provider in round-robin order."""
        # Sort by priority first, then round-robin within same priority
        sorted_providers = sorted(providers, key=lambda p: p.priority)
        self._round_robin_index = (self._round_robin_index + 1) % len(sorted_providers)
        return sorted_providers[self._round_robin_index]

    def _select_by_latency(self, providers: List[BaseProvider]) -> BaseProvider:
        """Select provider with lowest latency."""
        # Filter providers with known latency
        with_latency = [p for p in providers if p.health.latency_ms is not None]
        if with_latency:
            return min(with_latency, key=lambda p: p.health.latency_ms or float('inf'))
        # Fall back to priority if no latency data
        return self._select_by_priority(providers)

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        provider_name: Optional[str] = None,
        **kwargs: Any,
    ) -> ProviderResponse:
        """
        Generate completion with automatic failover.

        Tries the selected provider, then falls back to others on failure.

        Args:
            system_prompt: System prompt text
            user_prompt: User prompt text
            temperature: Response randomness (0.0-1.0)
            max_tokens: Maximum tokens in response
            provider_name: Optional specific provider to use
            **kwargs: Additional options

        Returns:
            ProviderResponse with generated text

        Raises:
            NoHealthyProviderError: If all providers fail
        """
        tried_providers: List[str] = []
        last_error: Optional[Exception] = None

        # Get ordered list of providers to try
        providers_to_try = self._get_failover_order(provider_name)

        for provider in providers_to_try:
            if provider.name in tried_providers:
                continue

            tried_providers.append(provider.name)

            try:
                logger.info(f"Attempting completion with provider: {provider.name}")
                response = await provider.complete(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs,
                )

                # Log switch if not first choice
                if len(tried_providers) > 1:
                    self._record_switch(tried_providers[0], provider.name)

                return response

            except ProviderError as e:
                last_error = e
                logger.warning(
                    f"Provider {provider.name} failed: {e}. "
                    f"Trying next provider..."
                )
                continue
            except Exception as e:
                last_error = e
                logger.error(f"Unexpected error from {provider.name}: {e}")
                continue

        # All providers failed
        raise NoHealthyProviderError(
            f"All providers failed. Tried: {tried_providers}. "
            f"Last error: {last_error}"
        )

    async def complete_with_images(
        self,
        system_prompt: str,
        user_prompt: str,
        images: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        provider_name: Optional[str] = None,
        **kwargs: Any,
    ) -> ProviderResponse:
        """
        Generate completion with images and automatic failover.

        Args:
            system_prompt: System prompt text
            user_prompt: User prompt text
            images: List of image dicts with 'data' (base64) and 'media_type'
            temperature: Response randomness (0.0-1.0)
            max_tokens: Maximum tokens in response
            provider_name: Optional specific provider to use
            **kwargs: Additional options

        Returns:
            ProviderResponse with generated text

        Raises:
            NoHealthyProviderError: If all providers fail
        """
        tried_providers: List[str] = []
        last_error: Optional[Exception] = None

        providers_to_try = self._get_failover_order(provider_name)

        for provider in providers_to_try:
            if provider.name in tried_providers:
                continue

            tried_providers.append(provider.name)

            try:
                logger.info(
                    f"Attempting multimodal completion with provider: {provider.name}"
                )
                response = await provider.complete_with_images(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    images=images,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs,
                )

                if len(tried_providers) > 1:
                    self._record_switch(tried_providers[0], provider.name)

                return response

            except ProviderError as e:
                last_error = e
                logger.warning(
                    f"Provider {provider.name} failed: {e}. "
                    f"Trying next provider..."
                )
                continue
            except Exception as e:
                last_error = e
                logger.error(f"Unexpected error from {provider.name}: {e}")
                continue

        raise NoHealthyProviderError(
            f"All providers failed for multimodal. Tried: {tried_providers}. "
            f"Last error: {last_error}"
        )

    def _get_failover_order(self, preferred_name: Optional[str] = None) -> List[BaseProvider]:
        """
        Get providers in failover order.

        Args:
            preferred_name: Preferred provider to try first

        Returns:
            List of providers in order to try
        """
        providers = []

        # Add preferred provider first if specified and available
        if preferred_name and preferred_name in self._providers:
            preferred = self._providers[preferred_name]
            if preferred.is_enabled:
                providers.append(preferred)

        # Add remaining by priority
        for name in self._priority_order:
            provider = self._providers[name]
            if provider not in providers and provider.is_enabled:
                providers.append(provider)

        return providers

    def _record_switch(self, from_provider: str, to_provider: str) -> None:
        """Record a provider switch event."""
        self._switch_count += 1
        self._last_switch_time = datetime.now()
        logger.warning(
            f"Provider switched from {from_provider} to {to_provider}. "
            f"Total switches: {self._switch_count}"
        )

    async def check_all_health(self) -> Dict[str, ProviderHealth]:
        """
        Check health of all providers.

        Returns:
            Dict mapping provider names to health status
        """
        health_results: Dict[str, ProviderHealth] = {}

        for name, provider in self._providers.items():
            try:
                health = await provider.health_check()
                health_results[name] = health
            except Exception as e:
                logger.error(f"Health check failed for {name}: {e}")
                health_results[name] = ProviderHealth(
                    status=ProviderStatus.UNHEALTHY,
                    error_message=str(e),
                )

        return health_results

    def get_all_providers(self) -> Dict[str, BaseProvider]:
        """Get all registered providers."""
        return self._providers.copy()

    def get_provider_status(self) -> Dict[str, Any]:
        """
        Get status of all providers.

        Returns:
            Dict with provider status information
        """
        return {
            "providers": {
                name: {
                    "name": name,
                    "priority": provider.priority,
                    "enabled": provider.is_enabled,
                    "available": provider.is_available,
                    "health": provider.health.to_dict(),
                    "model": provider.config.model,
                }
                for name, provider in self._providers.items()
            },
            "selection_strategy": self._selection_strategy.value,
            "active_provider": self._get_active_provider_name(),
            "switch_count": self._switch_count,
            "last_switch_time": self._last_switch_time.isoformat() if self._last_switch_time else None,
            "initialized": self._initialized,
        }

    def _get_active_provider_name(self) -> Optional[str]:
        """Get name of currently active (best) provider."""
        try:
            provider = self._select_provider()
            return provider.name if provider else None
        except Exception:
            return None

    async def close_all(self) -> None:
        """Close all providers."""
        for provider in self._providers.values():
            try:
                await provider.close()
            except Exception as e:
                logger.error(f"Error closing provider {provider.name}: {e}")

        self._providers.clear()
        self._priority_order.clear()
        self._initialized = False
        logger.info("All providers closed")


# Convenience function for getting factory instance
async def get_provider_factory() -> ProviderFactory:
    """
    Get ProviderFactory instance (FastAPI dependency).

    Returns:
        ProviderFactory singleton instance
    """
    return await ProviderFactory.get_instance()
