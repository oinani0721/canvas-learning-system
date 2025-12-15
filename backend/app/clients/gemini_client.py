# Canvas Learning System - Gemini API Client
# ✅ Verified from Context7:/googleapis/python-genai (topic: async generate content)
# ✅ Multi-Provider Support: Also supports OpenAI-compatible APIs via custom base_url
"""
Gemini API client for real Agent calls.

This module provides the GeminiClient class for making actual API calls.
Supports:
- Google Gemini API (default)
- OpenAI-compatible APIs (custom provider with base_url)

[Source: docs/prd/sprint-change-proposal-20251208.md - Gemini Migration]
[Source: Multi-Provider AI Architecture]
"""

import asyncio
import logging
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

# ✅ Verified from Context7:/googleapis/python-genai
# Pattern: "from google import genai"
from google import genai

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class AgentPromptTemplate:
    """Parsed agent prompt template from .md file."""
    name: str
    description: str
    model: str
    system_prompt: str
    input_format: Optional[str] = None
    output_format: Optional[str] = None


class GeminiClient:
    """
    Async client for Gemini API calls.

    ✅ Verified from Context7:/googleapis/python-genai
    Pattern: genai.Client with aio.models.generate_content()

    Attributes:
        client: genai.Client instance
        model: Model to use for API calls (default: gemini-2.5-flash)
        prompt_templates: Cached agent prompt templates
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        prompt_path: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        """
        Initialize Gemini client.

        Args:
            api_key: API key (defaults to env GOOGLE_API_KEY or config)
            model: Model to use (defaults to config GEMINI_MODEL)
            prompt_path: Path to agent prompt templates (defaults to config AGENT_PROMPT_PATH)
            base_url: Custom API base URL for OpenAI-compatible providers

        [Multi-Provider] When base_url is provided, the client uses OpenAI-compatible
        API calls instead of Google genai library.
        """
        # Get API key from parameter, config, or environment
        self.api_key = api_key or getattr(settings, 'GOOGLE_API_KEY', None) or os.environ.get("GOOGLE_API_KEY", "")
        self.base_url = base_url  # For custom OpenAI-compatible providers

        if not self.api_key:
            logger.warning("No API key configured. API calls will fail.")

        # For custom providers with base_url, we use httpx instead of genai
        if self.base_url:
            self.client = None  # Don't use genai client
            self._http_client = httpx.AsyncClient(timeout=120.0)
            logger.info(f"Using OpenAI-compatible API at {self.base_url}")
        else:
            # ✅ Verified from Context7:/googleapis/python-genai
            # Pattern: genai.Client(api_key=...)
            self.client = genai.Client(api_key=self.api_key) if self.api_key else None
            self._http_client = None

        self.model = model or getattr(settings, 'GEMINI_MODEL', 'gemini-2.5-flash')
        self.prompt_path = Path(prompt_path or settings.AGENT_PROMPT_PATH)

        # Cache for loaded prompt templates
        self._prompt_templates: Dict[str, AgentPromptTemplate] = {}

        logger.info(f"GeminiClient initialized with model={self.model}" +
                   (f", base_url={self.base_url}" if self.base_url else ""))

    def _parse_prompt_template(self, content: str) -> AgentPromptTemplate:
        """
        Parse a prompt template from .md file content.

        Expected format:
        ---
        name: agent-name
        description: Agent description
        model: inherit
        ---

        # System Prompt Content
        ...

        Args:
            content: Raw markdown content

        Returns:
            Parsed AgentPromptTemplate
        """
        # Extract YAML frontmatter
        frontmatter_match = re.match(r'^---\n(.*?)\n---\n(.*)$', content, re.DOTALL)

        if not frontmatter_match:
            raise ValueError("Invalid prompt template: missing YAML frontmatter")

        frontmatter_text = frontmatter_match.group(1)
        system_prompt = frontmatter_match.group(2).strip()

        # Parse simple YAML (key: value format)
        frontmatter: Dict[str, str] = {}
        for line in frontmatter_text.strip().split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                frontmatter[key.strip()] = value.strip()

        # Extract input/output format sections if present
        input_format = None
        output_format = None

        input_match = re.search(r'## Input Format\n```(?:json)?\n(.*?)\n```', system_prompt, re.DOTALL)
        if input_match:
            input_format = input_match.group(1).strip()

        output_match = re.search(r'## Output Format\n```(?:json)?\n(.*?)\n```', system_prompt, re.DOTALL)
        if output_match:
            output_format = output_match.group(1).strip()

        return AgentPromptTemplate(
            name=frontmatter.get('name', 'unknown'),
            description=frontmatter.get('description', ''),
            model=frontmatter.get('model', 'inherit'),
            system_prompt=system_prompt,
            input_format=input_format,
            output_format=output_format,
        )

    def load_prompt_template(self, agent_type: str) -> AgentPromptTemplate:
        """
        Load and cache an agent prompt template.

        Args:
            agent_type: Agent type name (e.g., 'basic-decomposition')

        Returns:
            Parsed AgentPromptTemplate

        Raises:
            FileNotFoundError: If template file doesn't exist
            ValueError: If template format is invalid
        """
        if agent_type in self._prompt_templates:
            return self._prompt_templates[agent_type]

        template_file = self.prompt_path / f"{agent_type}.md"

        if not template_file.exists():
            raise FileNotFoundError(f"Agent prompt template not found: {template_file}")

        content = template_file.read_text(encoding='utf-8')
        template = self._parse_prompt_template(content)

        self._prompt_templates[agent_type] = template
        logger.info(f"Loaded prompt template for agent: {agent_type}")

        return template

    async def _call_openai_compatible(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_retries: int = 3,
        base_delay: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Call OpenAI-compatible API using httpx with retry logic.

        [Multi-Provider] Supports custom providers like OpenRouter, custom endpoints.
        [Retry] Automatically retries on transient errors (503, 502, 429) with exponential backoff.

        Args:
            system_prompt: System prompt text
            user_prompt: User prompt text
            temperature: Response temperature
            max_retries: Maximum retry attempts for transient errors (default: 3)
            base_delay: Base delay in seconds for exponential backoff (default: 1.0)

        Returns:
            Dict with response and usage info

        Raises:
            httpx.HTTPStatusError: After all retries exhausted
        """
        if not self._http_client:
            raise RuntimeError("HTTP client not initialized for custom provider.")

        url = f"{self.base_url}/chat/completions"

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # Retryable HTTP status codes
        RETRYABLE_STATUS_CODES = {502, 503, 504, 429}

        last_error: Optional[Exception] = None

        for attempt in range(max_retries + 1):
            try:
                logger.info(f"Calling OpenAI-compatible API at {url}, model={self.model}" +
                           (f" (attempt {attempt + 1}/{max_retries + 1})" if attempt > 0 else ""))

                response = await self._http_client.post(url, json=payload, headers=headers)
                response.raise_for_status()

                data = response.json()

                response_text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                usage = data.get("usage", {})

                logger.info("OpenAI-compatible API call successful" +
                           (f" after {attempt + 1} attempts" if attempt > 0 else ""))

                return {
                    "response": response_text,
                    "model": self.model,
                    "usage": {
                        "input_tokens": usage.get("prompt_tokens", 0),
                        "output_tokens": usage.get("completion_tokens", 0),
                    },
                }

            except httpx.HTTPStatusError as e:
                last_error = e
                status_code = e.response.status_code

                if status_code in RETRYABLE_STATUS_CODES and attempt < max_retries:
                    # Exponential backoff: 1s, 2s, 4s, ...
                    delay = base_delay * (2 ** attempt)
                    logger.warning(
                        f"OpenAI-compatible API returned {status_code}, "
                        f"retrying in {delay:.1f}s (attempt {attempt + 1}/{max_retries + 1})"
                    )
                    await asyncio.sleep(delay)
                else:
                    # Non-retryable error or max retries exhausted
                    logger.error(
                        f"OpenAI-compatible API error: {status_code} after {attempt + 1} attempts. "
                        f"URL: {url}"
                    )
                    raise

            except (httpx.ConnectError, httpx.TimeoutException) as e:
                last_error = e

                if attempt < max_retries:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(
                        f"Connection error to API: {type(e).__name__}, "
                        f"retrying in {delay:.1f}s (attempt {attempt + 1}/{max_retries + 1})"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"OpenAI-compatible API connection failed after {attempt + 1} attempts. "
                        f"URL: {url}, Error: {e}"
                    )
                    raise

        # Should not reach here, but just in case
        if last_error:
            raise last_error
        raise RuntimeError("Unexpected error in _call_openai_compatible")

    async def call_agent(
        self,
        agent_type: str,
        user_prompt: str,
        context: Optional[str] = None,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """
        Call API with an agent prompt template.

        ✅ Verified from Context7:/googleapis/python-genai
        Pattern: await client.aio.models.generate_content(...)

        [Multi-Provider] Routes to appropriate API based on base_url:
        - No base_url: Use Google genai library
        - With base_url: Use OpenAI-compatible API via httpx

        Args:
            agent_type: Agent type name (e.g., 'basic-decomposition')
            user_prompt: User's input prompt
            context: Optional additional context (e.g., adjacent nodes)
            temperature: Response temperature (0.0-1.0)

        Returns:
            Dict containing:
                - agent_type: The agent type used
                - response: API response text
                - model: Model used
                - usage: Token usage info (if available)

        Raises:
            RuntimeError: If API key not configured
        """
        # Check configuration
        if not self.api_key:
            raise RuntimeError("API key not configured.")

        if not self.client and not self._http_client:
            raise RuntimeError("Neither genai client nor HTTP client initialized.")

        # Load agent prompt template
        template = self.load_prompt_template(agent_type)

        # Build system prompt with optional context
        system_prompt = template.system_prompt
        if context:
            system_prompt = f"{system_prompt}\n\n## Additional Context\n{context}"

        logger.info(f"Calling API with agent={agent_type}, model={self.model}")

        # Route to appropriate API
        if self._http_client and self.base_url:
            # Use OpenAI-compatible API
            result = await self._call_openai_compatible(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=temperature,
            )
            result["agent_type"] = agent_type
            return result
        else:
            # Use Google genai library
            # ✅ Verified from Context7:/googleapis/python-genai
            # Gemini uses a different message format - combine system prompt with user prompt
            full_prompt = f"{system_prompt}\n\n## User Request\n{user_prompt}"

            # ✅ Verified from Context7:/googleapis/python-genai
            # Pattern: await client.aio.models.generate_content(model=..., contents=...)
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=full_prompt,
                config=genai.types.GenerateContentConfig(
                    temperature=temperature,
                ),
            )

            response_text = response.text or ""

            logger.info(f"Gemini API call successful for agent={agent_type}")

            return {
                "agent_type": agent_type,
                "response": response_text,
                "model": self.model,
                "usage": {
                    "input_tokens": getattr(response.usage_metadata, 'prompt_token_count', 0) if hasattr(response, 'usage_metadata') else 0,
                    "output_tokens": getattr(response.usage_metadata, 'candidates_token_count', 0) if hasattr(response, 'usage_metadata') else 0,
                },
            }

    async def call_agent_with_images(
        self,
        agent_type: str,
        user_prompt: str,
        images: Optional[List[Dict[str, Any]]] = None,
        context: Optional[str] = None,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """
        Call Gemini API with images (multimodal support).

        ✅ Verified from Context7:/googleapis/python-genai
        Gemini natively supports multimodal input

        Args:
            agent_type: Agent type name (e.g., 'basic-decomposition')
            user_prompt: User's input prompt
            images: List of image dicts with keys:
                - data: base64 encoded image data
                - media_type: MIME type (e.g., 'image/png', 'image/jpeg')
            context: Optional additional context (e.g., adjacent nodes)
            temperature: Response temperature (0.0-1.0)

        Returns:
            Dict containing:
                - agent_type: The agent type used
                - response: Gemini's response text
                - model: Model used
                - usage: Token usage info
                - images_processed: Number of images sent

        Raises:
            RuntimeError: If API key not configured
        """
        if not self.client:
            raise RuntimeError(
                "Gemini API client not initialized. "
                "Please configure GOOGLE_API_KEY in .env or environment."
            )

        # Load agent prompt template
        template = self.load_prompt_template(agent_type)

        # Build system prompt with optional context
        system_prompt = template.system_prompt
        if context:
            system_prompt = f"{system_prompt}\n\n## Additional Context\n{context}"

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
            logger.info(f"Added {len(images)} images to request")

        # Add text prompt
        full_prompt = f"{system_prompt}\n\n## User Request\n{user_prompt}"
        content_parts.append({"text": full_prompt})

        logger.info(f"Calling Gemini API with agent={agent_type}, model={self.model}, images={len(images) if images else 0}")

        # ✅ Verified from Context7:/googleapis/python-genai
        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=content_parts,
            config=genai.types.GenerateContentConfig(
                temperature=temperature,
            ),
        )

        response_text = response.text or ""

        logger.info(f"Gemini API call successful for agent={agent_type}")

        return {
            "agent_type": agent_type,
            "response": response_text,
            "model": self.model,
            "usage": {
                "input_tokens": getattr(response.usage_metadata, 'prompt_token_count', 0) if hasattr(response, 'usage_metadata') else 0,
                "output_tokens": getattr(response.usage_metadata, 'candidates_token_count', 0) if hasattr(response, 'usage_metadata') else 0,
            },
            "images_processed": len(images) if images else 0,
        }

    async def call_raw(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """
        Make a raw Gemini API call without using a template.

        Args:
            system_prompt: System prompt text
            user_prompt: User prompt text
            temperature: Response temperature

        Returns:
            Dict with response and usage info
        """
        if not self.client:
            raise RuntimeError("Gemini API client not initialized.")

        full_prompt = f"{system_prompt}\n\n{user_prompt}"

        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=full_prompt,
            config=genai.types.GenerateContentConfig(
                temperature=temperature,
            ),
        )

        response_text = response.text or ""

        return {
            "response": response_text,
            "model": self.model,
            "usage": {
                "input_tokens": getattr(response.usage_metadata, 'prompt_token_count', 0) if hasattr(response, 'usage_metadata') else 0,
                "output_tokens": getattr(response.usage_metadata, 'candidates_token_count', 0) if hasattr(response, 'usage_metadata') else 0,
            },
        }

    def is_configured(self) -> bool:
        """Check if the client is properly configured with an API key.

        [Multi-Provider] Returns True if either:
        - Google genai client is configured (api_key + client)
        - OpenAI-compatible HTTP client is configured (api_key + http_client + base_url)
        """
        if self.base_url and self._http_client:
            result = bool(self.api_key)
            # FIX: Debug logging to diagnose configuration issues
            logger.debug(
                f"is_configured (custom provider): {result}, "
                f"base_url={self.base_url!r}, "
                f"has_http_client={self._http_client is not None}, "
                f"has_api_key={bool(self.api_key)}"
            )
            return result
        result = bool(self.api_key and self.client)
        # FIX: Debug logging for google provider path
        logger.debug(
            f"is_configured (google provider): {result}, "
            f"has_api_key={bool(self.api_key)}, "
            f"has_genai_client={self.client is not None}"
        )
        return result


# Singleton instance for dependency injection
_gemini_client: Optional[GeminiClient] = None


def get_gemini_client() -> GeminiClient:
    """
    Get or create the Gemini client singleton.

    Returns:
        GeminiClient instance
    """
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiClient()
    return _gemini_client


def reset_gemini_client() -> None:
    """Reset the Gemini client singleton (for testing)."""
    global _gemini_client
    _gemini_client = None
