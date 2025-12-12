# Canvas Learning System - OpenAI Provider
# ✅ Verified from Context7:/openai/openai-python (topic: async chat completions)
"""
OpenAI AI provider implementation.

This module implements the BaseProvider interface for OpenAI's models,
supporting both text and multimodal (image) inputs via GPT-4 Vision.

Also supports OpenAI-compatible APIs (OpenRouter, custom endpoints).

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


class OpenAIProvider(BaseProvider):
    """
    OpenAI AI provider.

    Supports:
    - OpenAI API (default)
    - OpenAI-compatible APIs via custom base_url (OpenRouter, etc.)

    Supported models:
    - gpt-4o (recommended for vision)
    - gpt-4-turbo
    - gpt-4
    - gpt-3.5-turbo
    """

    # Default OpenAI API base URL
    DEFAULT_BASE_URL = "https://api.openai.com/v1"

    # Supported models for validation
    SUPPORTED_MODELS = [
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4-turbo",
        "gpt-4",
        "gpt-3.5-turbo",
        "o1-preview",
        "o1-mini",
    ]

    def __init__(self, config: ProviderConfig):
        """
        Initialize OpenAI provider.

        Args:
            config: Provider configuration with api_key, model, and optional base_url
        """
        super().__init__(config)
        self._http_client: Optional[httpx.AsyncClient] = None
        self._base_url = config.base_url or self.DEFAULT_BASE_URL

    async def initialize(self) -> bool:
        """
        Initialize HTTP client for OpenAI API.

        Returns:
            True if initialization successful
        """
        try:
            if not self.config.api_key:
                logger.error(f"OpenAI provider {self.name}: No API key configured")
                return False

            self._http_client = httpx.AsyncClient(
                timeout=self.config.timeout,
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json",
                },
            )
            self._initialized = True

            logger.info(
                f"OpenAI provider {self.name} initialized: "
                f"model={self.config.model}, base_url={self._base_url}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to initialize OpenAI provider: {e}")
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
        Generate completion using OpenAI Chat Completions API.

        ✅ Verified from Context7:/openai/openai-python
        Uses /chat/completions endpoint with messages format.

        Args:
            system_prompt: System prompt text
            user_prompt: User prompt text
            temperature: Response randomness (0.0-1.0)
            max_tokens: Maximum tokens in response

        Returns:
            ProviderResponse with generated text

        Raises:
            ProviderError: If API call fails
        """
        if not self._http_client:
            raise ProviderError(
                "OpenAI client not initialized. Call initialize() first.",
                provider=self.name,
            )

        start_time = time.time()

        try:
            url = f"{self._base_url}/chat/completions"

            payload: Dict[str, Any] = {
                "model": self.config.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": temperature,
            }

            if max_tokens:
                payload["max_tokens"] = max_tokens

            response = await self._http_client.post(url, json=payload)
            response.raise_for_status()

            data = response.json()
            latency_ms = (time.time() - start_time) * 1000

            response_text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            usage = data.get("usage", {})

            await self.update_health(success=True, latency_ms=latency_ms)

            logger.info(
                f"OpenAI completion successful: model={self.config.model}, "
                f"latency={latency_ms:.0f}ms"
            )

            return ProviderResponse(
                text=response_text,
                model=self.config.model,
                provider=self.name,
                input_tokens=usage.get("prompt_tokens", 0),
                output_tokens=usage.get("completion_tokens", 0),
                latency_ms=latency_ms,
                raw_response=data,
            )

        except httpx.HTTPStatusError as e:
            latency_ms = (time.time() - start_time) * 1000
            error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
            await self.update_health(success=False, latency_ms=latency_ms, error=error_msg)

            logger.error(f"OpenAI API error: {error_msg}")
            raise ProviderError(
                f"OpenAI API call failed: {error_msg}",
                provider=self.name,
                cause=e,
            ) from e

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            await self.update_health(success=False, latency_ms=latency_ms, error=str(e))

            logger.error(f"OpenAI completion failed: {e}")
            raise ProviderError(
                f"OpenAI API call failed: {e}",
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
        Generate completion with image inputs using GPT-4 Vision.

        ✅ Verified from Context7:/openai/openai-python
        Uses image_url content type with base64 data URL.

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
                "OpenAI client not initialized. Call initialize() first.",
                provider=self.name,
            )

        start_time = time.time()

        try:
            url = f"{self._base_url}/chat/completions"

            # Build content array with images and text
            user_content: List[Dict[str, Any]] = []

            # Add images
            for img in images:
                media_type = img.get("media_type", "image/png")
                data = img.get("data", "")
                user_content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{media_type};base64,{data}",
                    },
                })

            # Add text prompt
            user_content.append({
                "type": "text",
                "text": user_prompt,
            })

            payload: Dict[str, Any] = {
                "model": self.config.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                "temperature": temperature,
            }

            if max_tokens:
                payload["max_tokens"] = max_tokens

            response = await self._http_client.post(url, json=payload)
            response.raise_for_status()

            data = response.json()
            latency_ms = (time.time() - start_time) * 1000

            response_text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            usage = data.get("usage", {})

            await self.update_health(success=True, latency_ms=latency_ms)

            logger.info(
                f"OpenAI vision completion successful: "
                f"images={len(images)}, latency={latency_ms:.0f}ms"
            )

            return ProviderResponse(
                text=response_text,
                model=self.config.model,
                provider=self.name,
                input_tokens=usage.get("prompt_tokens", 0),
                output_tokens=usage.get("completion_tokens", 0),
                latency_ms=latency_ms,
            )

        except httpx.HTTPStatusError as e:
            latency_ms = (time.time() - start_time) * 1000
            error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
            await self.update_health(success=False, latency_ms=latency_ms, error=error_msg)

            logger.error(f"OpenAI vision API error: {error_msg}")
            raise ProviderError(
                f"OpenAI vision API call failed: {error_msg}",
                provider=self.name,
                cause=e,
            ) from e

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            await self.update_health(success=False, latency_ms=latency_ms, error=str(e))

            logger.error(f"OpenAI vision completion failed: {e}")
            raise ProviderError(
                f"OpenAI vision API call failed: {e}",
                provider=self.name,
                cause=e,
            ) from e

    async def health_check(self) -> ProviderHealth:
        """
        Check OpenAI API health.

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
            url = f"{self._base_url}/chat/completions"

            payload = {
                "model": self.config.model,
                "messages": [
                    {"role": "user", "content": "Say 'OK'"},
                ],
                "max_tokens": 5,
                "temperature": 0.0,
            }

            response = await self._http_client.post(url, json=payload)
            response.raise_for_status()

            latency_ms = (time.time() - start_time) * 1000
            await self.update_health(success=True, latency_ms=latency_ms)

            logger.debug(f"OpenAI health check passed: latency={latency_ms:.0f}ms")

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            await self.update_health(success=False, latency_ms=latency_ms, error=str(e))

            logger.warning(f"OpenAI health check failed: {e}")

        return self.health

    async def close(self) -> None:
        """Clean up HTTP client resources."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
        await super().close()
