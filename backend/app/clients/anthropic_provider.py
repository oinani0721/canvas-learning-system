# Canvas Learning System - Anthropic Provider
# ✅ Verified from Context7:/anthropics/anthropic-sdk-python (topic: async messages)
"""
Anthropic Claude AI provider implementation.

This module implements the BaseProvider interface for Anthropic's Claude models,
supporting both text and multimodal (image) inputs.

[Source: docs/prd/EPIC-20-BACKEND-STABILITY-MULTI-PROVIDER.md]
[Source: Story 20.1 - Multi-Provider Architecture Design]
"""

import logging
import time
from typing import Any, Dict, List, Optional

import httpx

from app.clients.base_provider import (
    BaseProvider,
    ProviderConfig,
    ProviderError,
    ProviderHealth,
    ProviderResponse,
    ProviderStatus,
)

logger = logging.getLogger(__name__)


class AnthropicProvider(BaseProvider):
    """
    Anthropic Claude AI provider.

    Supported models:
    - claude-3-5-sonnet-20241022 (recommended)
    - claude-3-opus-20240229
    - claude-3-sonnet-20240229
    - claude-3-haiku-20240307
    """

    # Default Anthropic API base URL
    DEFAULT_BASE_URL = "https://api.anthropic.com"

    # API version header
    API_VERSION = "2023-06-01"

    # Supported models for validation
    SUPPORTED_MODELS = [
        "claude-3-5-sonnet-20241022",
        "claude-3-5-sonnet-latest",
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307",
        "claude-opus-4-5-20251101",
        "claude-sonnet-4-5-20250929",
    ]

    def __init__(self, config: ProviderConfig):
        """
        Initialize Anthropic provider.

        Args:
            config: Provider configuration with api_key and model
        """
        super().__init__(config)
        self._http_client: Optional[httpx.AsyncClient] = None
        self._base_url = config.base_url or self.DEFAULT_BASE_URL

    async def initialize(self) -> bool:
        """
        Initialize HTTP client for Anthropic API.

        Returns:
            True if initialization successful
        """
        try:
            if not self.config.api_key:
                logger.error(f"Anthropic provider {self.name}: No API key configured")
                return False

            # ✅ Verified from Context7:/anthropics/anthropic-sdk-python
            # Anthropic uses x-api-key header and anthropic-version
            self._http_client = httpx.AsyncClient(
                timeout=self.config.timeout,
                headers={
                    "x-api-key": self.config.api_key,
                    "anthropic-version": self.API_VERSION,
                    "Content-Type": "application/json",
                },
            )
            self._initialized = True

            logger.info(
                f"Anthropic provider {self.name} initialized: "
                f"model={self.config.model}, base_url={self._base_url}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Anthropic provider: {e}")
            return False

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> ProviderResponse:
        """
        Generate completion using Anthropic Messages API.

        ✅ Verified from Context7:/anthropics/anthropic-sdk-python
        Uses /v1/messages endpoint.

        Args:
            system_prompt: System prompt text
            user_prompt: User prompt text
            temperature: Response randomness (0.0-1.0)
            max_tokens: Maximum tokens in response (default: 4096)

        Returns:
            ProviderResponse with generated text

        Raises:
            ProviderError: If API call fails
        """
        if not self._http_client:
            raise ProviderError(
                "Anthropic client not initialized. Call initialize() first.",
                provider=self.name,
            )

        start_time = time.time()

        try:
            url = f"{self._base_url}/v1/messages"

            # ✅ Verified from Context7:/anthropics/anthropic-sdk-python
            # Anthropic uses separate system parameter
            payload: Dict[str, Any] = {
                "model": self.config.model,
                "system": system_prompt,
                "messages": [
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": max_tokens or 4096,
                "temperature": temperature,
            }

            response = await self._http_client.post(url, json=payload)
            response.raise_for_status()

            data = response.json()
            latency_ms = (time.time() - start_time) * 1000

            # Extract text from content blocks
            content_blocks = data.get("content", [])
            response_text = ""
            for block in content_blocks:
                if block.get("type") == "text":
                    response_text += block.get("text", "")

            usage = data.get("usage", {})

            await self.update_health(success=True, latency_ms=latency_ms)

            logger.info(
                f"Anthropic completion successful: model={self.config.model}, "
                f"latency={latency_ms:.0f}ms"
            )

            return ProviderResponse(
                text=response_text,
                model=self.config.model,
                provider=self.name,
                input_tokens=usage.get("input_tokens", 0),
                output_tokens=usage.get("output_tokens", 0),
                latency_ms=latency_ms,
                raw_response=data,
            )

        except httpx.HTTPStatusError as e:
            latency_ms = (time.time() - start_time) * 1000
            error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
            await self.update_health(success=False, latency_ms=latency_ms, error=error_msg)

            logger.error(f"Anthropic API error: {error_msg}")
            raise ProviderError(
                f"Anthropic API call failed: {error_msg}",
                provider=self.name,
                cause=e,
            ) from e

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            await self.update_health(success=False, latency_ms=latency_ms, error=str(e))

            logger.error(f"Anthropic completion failed: {e}")
            raise ProviderError(
                f"Anthropic API call failed: {e}",
                provider=self.name,
                cause=e,
            ) from e

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
        Generate completion with image inputs using Claude Vision.

        ✅ Verified from Context7:/anthropics/anthropic-sdk-python
        Claude supports images via base64 source in content blocks.

        Args:
            system_prompt: System prompt text
            user_prompt: User prompt text
            images: List of image dicts with 'data' (base64) and 'media_type'
            temperature: Response randomness (0.0-1.0)
            max_tokens: Maximum tokens in response

        Returns:
            ProviderResponse with generated text

        Raises:
            ProviderError: If API call fails
        """
        if not self._http_client:
            raise ProviderError(
                "Anthropic client not initialized. Call initialize() first.",
                provider=self.name,
            )

        start_time = time.time()

        try:
            url = f"{self._base_url}/v1/messages"

            # Build content array with images and text
            user_content: List[Dict[str, Any]] = []

            # Add images
            for img in images:
                user_content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": img.get("media_type", "image/png"),
                        "data": img.get("data", ""),
                    },
                })

            # Add text prompt
            user_content.append({
                "type": "text",
                "text": user_prompt,
            })

            payload: Dict[str, Any] = {
                "model": self.config.model,
                "system": system_prompt,
                "messages": [
                    {"role": "user", "content": user_content},
                ],
                "max_tokens": max_tokens or 4096,
                "temperature": temperature,
            }

            response = await self._http_client.post(url, json=payload)
            response.raise_for_status()

            data = response.json()
            latency_ms = (time.time() - start_time) * 1000

            content_blocks = data.get("content", [])
            response_text = ""
            for block in content_blocks:
                if block.get("type") == "text":
                    response_text += block.get("text", "")

            usage = data.get("usage", {})

            await self.update_health(success=True, latency_ms=latency_ms)

            logger.info(
                f"Anthropic vision completion successful: "
                f"images={len(images)}, latency={latency_ms:.0f}ms"
            )

            return ProviderResponse(
                text=response_text,
                model=self.config.model,
                provider=self.name,
                input_tokens=usage.get("input_tokens", 0),
                output_tokens=usage.get("output_tokens", 0),
                latency_ms=latency_ms,
            )

        except httpx.HTTPStatusError as e:
            latency_ms = (time.time() - start_time) * 1000
            error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
            await self.update_health(success=False, latency_ms=latency_ms, error=error_msg)

            logger.error(f"Anthropic vision API error: {error_msg}")
            raise ProviderError(
                f"Anthropic vision API call failed: {error_msg}",
                provider=self.name,
                cause=e,
            ) from e

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            await self.update_health(success=False, latency_ms=latency_ms, error=str(e))

            logger.error(f"Anthropic vision completion failed: {e}")
            raise ProviderError(
                f"Anthropic vision API call failed: {e}",
                provider=self.name,
                cause=e,
            ) from e

    async def health_check(self) -> ProviderHealth:
        """
        Check Anthropic API health.

        Makes a lightweight API call to verify connectivity.

        Returns:
            ProviderHealth with current status
        """
        if not self._http_client:
            self.health.status = ProviderStatus.UNHEALTHY
            self.health.error_message = "Client not initialized"
            return self.health

        start_time = time.time()

        try:
            url = f"{self._base_url}/v1/messages"

            payload = {
                "model": self.config.model,
                "messages": [
                    {"role": "user", "content": "Say 'OK'"},
                ],
                "max_tokens": 10,
                "temperature": 0.0,
            }

            response = await self._http_client.post(url, json=payload)
            response.raise_for_status()

            latency_ms = (time.time() - start_time) * 1000
            await self.update_health(success=True, latency_ms=latency_ms)

            logger.debug(f"Anthropic health check passed: latency={latency_ms:.0f}ms")

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            await self.update_health(success=False, latency_ms=latency_ms, error=str(e))

            logger.warning(f"Anthropic health check failed: {e}")

        return self.health

    async def close(self) -> None:
        """Clean up HTTP client resources."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
        await super().close()
