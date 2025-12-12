# Canvas Learning System - Google AI Provider
# ✅ Verified from Context7:/googleapis/python-genai (topic: async generate content)
"""
Google Gemini AI provider implementation.

This module implements the BaseProvider interface for Google's Gemini models,
supporting both text and multimodal (image) inputs.

[Source: docs/prd/EPIC-20-BACKEND-STABILITY-MULTI-PROVIDER.md]
[Source: Story 20.1 - Multi-Provider Architecture Design]
"""

import logging
import time
from typing import Any, Dict, List, Optional

# ✅ Verified from Context7:/googleapis/python-genai
# Pattern: "from google import genai"
from google import genai

from app.clients.base_provider import (
    BaseProvider,
    ProviderConfig,
    ProviderError,
    ProviderHealth,
    ProviderResponse,
    ProviderStatus,
)

logger = logging.getLogger(__name__)


class GoogleProvider(BaseProvider):
    """
    Google Gemini AI provider.

    ✅ Verified from Context7:/googleapis/python-genai
    Uses google-genai library for API calls.

    Supported models:
    - gemini-2.0-flash-exp (recommended for speed)
    - gemini-1.5-pro (for complex tasks)
    - gemini-1.5-flash (balanced)
    """

    # Supported models for validation
    SUPPORTED_MODELS = [
        "gemini-2.0-flash-exp",
        "gemini-1.5-pro",
        "gemini-1.5-flash",
        "gemini-pro",
        "gemini-pro-vision",
    ]

    def __init__(self, config: ProviderConfig):
        """
        Initialize Google provider.

        Args:
            config: Provider configuration with api_key and model
        """
        super().__init__(config)
        self._client: Optional[genai.Client] = None

    async def initialize(self) -> bool:
        """
        Initialize Google genai client.

        ✅ Verified from Context7:/googleapis/python-genai
        Pattern: genai.Client(api_key=...)

        Returns:
            True if initialization successful
        """
        try:
            if not self.config.api_key:
                logger.error(f"Google provider {self.name}: No API key configured")
                return False

            # ✅ Verified from Context7:/googleapis/python-genai
            self._client = genai.Client(api_key=self.config.api_key)
            self._initialized = True

            logger.info(
                f"Google provider {self.name} initialized: model={self.config.model}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Google provider: {e}")
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
        Generate completion using Gemini API.

        ✅ Verified from Context7:/googleapis/python-genai
        Pattern: await client.aio.models.generate_content(model=..., contents=...)

        Args:
            system_prompt: System prompt text
            user_prompt: User prompt text
            temperature: Response randomness (0.0-1.0)
            max_tokens: Maximum tokens in response
            **kwargs: Additional options

        Returns:
            ProviderResponse with generated text

        Raises:
            ProviderError: If API call fails
        """
        if not self._client:
            raise ProviderError(
                "Google client not initialized. Call initialize() first.",
                provider=self.name,
            )

        start_time = time.time()

        try:
            # Gemini combines system and user prompt
            full_prompt = f"{system_prompt}\n\n## User Request\n{user_prompt}"

            # ✅ Verified from Context7:/googleapis/python-genai
            # Pattern: GenerateContentConfig for temperature and max_tokens
            config = genai.types.GenerateContentConfig(
                temperature=temperature,
            )

            if max_tokens:
                config = genai.types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                )

            # ✅ Verified from Context7:/googleapis/python-genai
            # Pattern: await client.aio.models.generate_content(...)
            response = await self._client.aio.models.generate_content(
                model=self.config.model,
                contents=full_prompt,
                config=config,
            )

            latency_ms = (time.time() - start_time) * 1000
            response_text = response.text or ""

            # Extract usage metadata
            input_tokens = 0
            output_tokens = 0
            if hasattr(response, 'usage_metadata'):
                input_tokens = getattr(response.usage_metadata, 'prompt_token_count', 0)
                output_tokens = getattr(response.usage_metadata, 'candidates_token_count', 0)

            await self.update_health(success=True, latency_ms=latency_ms)

            logger.info(
                f"Google completion successful: model={self.config.model}, "
                f"latency={latency_ms:.0f}ms, tokens={input_tokens}+{output_tokens}"
            )

            return ProviderResponse(
                text=response_text,
                model=self.config.model,
                provider=self.name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
                raw_response={"text": response_text},
            )

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            await self.update_health(success=False, latency_ms=latency_ms, error=str(e))

            logger.error(f"Google completion failed: {e}")
            raise ProviderError(
                f"Google API call failed: {e}",
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
        Generate completion with image inputs (multimodal).

        ✅ Verified from Context7:/googleapis/python-genai
        Gemini natively supports multimodal input with inline_data.

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
        if not self._client:
            raise ProviderError(
                "Google client not initialized. Call initialize() first.",
                provider=self.name,
            )

        start_time = time.time()

        try:
            # Build content parts for multimodal
            content_parts = []

            # Add images first
            if images:
                for img in images:
                    content_parts.append({
                        "inline_data": {
                            "mime_type": img.get("media_type", "image/png"),
                            "data": img["data"],
                        }
                    })

            # Add text prompt
            full_prompt = f"{system_prompt}\n\n## User Request\n{user_prompt}"
            content_parts.append({"text": full_prompt})

            config = genai.types.GenerateContentConfig(
                temperature=temperature,
            )

            if max_tokens:
                config = genai.types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                )

            # ✅ Verified from Context7:/googleapis/python-genai
            response = await self._client.aio.models.generate_content(
                model=self.config.model,
                contents=content_parts,
                config=config,
            )

            latency_ms = (time.time() - start_time) * 1000
            response_text = response.text or ""

            input_tokens = 0
            output_tokens = 0
            if hasattr(response, 'usage_metadata'):
                input_tokens = getattr(response.usage_metadata, 'prompt_token_count', 0)
                output_tokens = getattr(response.usage_metadata, 'candidates_token_count', 0)

            await self.update_health(success=True, latency_ms=latency_ms)

            logger.info(
                f"Google multimodal completion successful: "
                f"images={len(images)}, latency={latency_ms:.0f}ms"
            )

            return ProviderResponse(
                text=response_text,
                model=self.config.model,
                provider=self.name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
            )

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            await self.update_health(success=False, latency_ms=latency_ms, error=str(e))

            logger.error(f"Google multimodal completion failed: {e}")
            raise ProviderError(
                f"Google multimodal API call failed: {e}",
                provider=self.name,
                cause=e,
            ) from e

    async def health_check(self) -> ProviderHealth:
        """
        Check Google API health.

        Makes a lightweight API call to verify connectivity.

        Returns:
            ProviderHealth with current status
        """
        if not self._client:
            self.health.status = ProviderStatus.UNHEALTHY
            self.health.error_message = "Client not initialized"
            return self.health

        start_time = time.time()

        try:
            # Simple health check - just verify we can make a request
            # ✅ Verified from Context7:/googleapis/python-genai
            _response = await self._client.aio.models.generate_content(
                model=self.config.model,
                contents="Say 'OK' if you receive this message.",
                config=genai.types.GenerateContentConfig(
                    temperature=0.0,
                    max_output_tokens=10,
                ),
            )

            latency_ms = (time.time() - start_time) * 1000
            await self.update_health(success=True, latency_ms=latency_ms)

            logger.debug(f"Google health check passed: latency={latency_ms:.0f}ms")

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            await self.update_health(success=False, latency_ms=latency_ms, error=str(e))

            logger.warning(f"Google health check failed: {e}")

        return self.health

    async def close(self) -> None:
        """Clean up Google client resources."""
        self._client = None
        await super().close()
