# Canvas Learning System - Claude API Client
# ✅ Verified from Context7:/anthropics/anthropic-sdk-python (topic: async client messages create)
"""
Claude API client for real Agent calls.

This module provides the ClaudeClient class for making actual Claude API calls,
replacing the mock implementation in agent_service.py.

[Source: docs/prd/sprint-change-proposal-20251208.md - Epic 20 Story 20.1]
"""

import logging
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

# ✅ Verified from Context7:/anthropics/anthropic-sdk-python
# Pattern: "from anthropic import AsyncAnthropic"
from anthropic import AsyncAnthropic
from anthropic.types import Message

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


class ClaudeClient:
    """
    Async client for Claude API calls.

    ✅ Verified from Context7:/anthropics/anthropic-sdk-python
    Pattern: AsyncAnthropic client with messages.create()

    Attributes:
        client: AsyncAnthropic client instance
        model: Model to use for API calls
        max_tokens: Maximum tokens per response
        prompt_templates: Cached agent prompt templates
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        prompt_path: Optional[str] = None,
    ):
        """
        Initialize Claude client.

        Args:
            api_key: Anthropic API key (defaults to env ANTHROPIC_API_KEY or config)
            model: Model to use (defaults to config AGENT_MODEL)
            max_tokens: Max tokens per response (defaults to config AGENT_MAX_TOKENS)
            prompt_path: Path to agent prompt templates (defaults to config AGENT_PROMPT_PATH)
        """
        # Get API key from parameter, config, or environment
        self.api_key = api_key or settings.ANTHROPIC_API_KEY or os.environ.get("ANTHROPIC_API_KEY", "")

        if not self.api_key:
            logger.warning("No Anthropic API key configured. Claude API calls will fail.")

        # ✅ Verified from Context7:/anthropics/anthropic-sdk-python
        # Pattern: AsyncAnthropic(api_key=...)
        self.client = AsyncAnthropic(api_key=self.api_key) if self.api_key else None

        self.model = model or settings.AGENT_MODEL
        self.max_tokens = max_tokens or settings.AGENT_MAX_TOKENS
        self.prompt_path = Path(prompt_path or settings.AGENT_PROMPT_PATH)

        # Cache for loaded prompt templates
        self._prompt_templates: Dict[str, AgentPromptTemplate] = {}

        logger.info(f"ClaudeClient initialized with model={self.model}, max_tokens={self.max_tokens}")

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

    async def call_agent(
        self,
        agent_type: str,
        user_prompt: str,
        context: Optional[str] = None,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """
        Call Claude API with an agent prompt template.

        ✅ Verified from Context7:/anthropics/anthropic-sdk-python
        Pattern: await client.messages.create(...)

        Args:
            agent_type: Agent type name (e.g., 'basic-decomposition')
            user_prompt: User's input prompt
            context: Optional additional context (e.g., adjacent nodes)
            temperature: Response temperature (0.0-1.0)

        Returns:
            Dict containing:
                - agent_type: The agent type used
                - response: Claude's response text
                - model: Model used
                - usage: Token usage info

        Raises:
            RuntimeError: If API key not configured
            anthropic.APIError: On API call failure
        """
        if not self.client:
            raise RuntimeError(
                "Claude API client not initialized. "
                "Please configure ANTHROPIC_API_KEY in .env or environment."
            )

        # Load agent prompt template
        template = self.load_prompt_template(agent_type)

        # Build system prompt with optional context
        system_prompt = template.system_prompt
        if context:
            system_prompt = f"{system_prompt}\n\n## Additional Context\n{context}"

        # Build messages
        messages = [
            {
                "role": "user",
                "content": user_prompt,
            }
        ]

        logger.info(f"Calling Claude API with agent={agent_type}, model={self.model}")

        # ✅ Verified from Context7:/anthropics/anthropic-sdk-python
        # Pattern: await client.messages.create(max_tokens=..., messages=[...], model=...)
        response: Message = await self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system_prompt,
            messages=messages,
            temperature=temperature,
        )

        # Extract text content from response
        response_text = ""
        for block in response.content:
            if hasattr(block, 'text'):
                response_text += block.text

        logger.info(f"Claude API call successful: {response.usage.input_tokens} in, {response.usage.output_tokens} out")

        return {
            "agent_type": agent_type,
            "response": response_text,
            "model": response.model,
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
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
        Call Claude API with images (multimodal support).

        ✅ Verified from Context7:/anthropics/anthropic-cookbook
        Pattern: content = [{"type": "image", "source": {...}}, {"type": "text", "text": ...}]

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
                - response: Claude's response text
                - model: Model used
                - usage: Token usage info
                - images_processed: Number of images sent

        Raises:
            RuntimeError: If API key not configured

        [Source: FIX-2.1 实现Claude Vision多模态支持]
        """
        if not self.client:
            raise RuntimeError(
                "Claude API client not initialized. "
                "Please configure ANTHROPIC_API_KEY in .env or environment."
            )

        # Load agent prompt template
        template = self.load_prompt_template(agent_type)

        # Build system prompt with optional context
        system_prompt = template.system_prompt
        if context:
            system_prompt = f"{system_prompt}\n\n## Additional Context\n{context}"

        # ✅ Verified from Context7:/anthropics/anthropic-cookbook (multimodal/best_practices_for_vision.ipynb)
        # Build content blocks with images first, then text
        content_blocks: List[Dict[str, Any]] = []

        # Add image blocks
        if images:
            for img in images:
                content_blocks.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": img.get("media_type", "image/png"),
                        "data": img["data"],
                    },
                })
            logger.info(f"Added {len(images)} images to request")

        # Add text block
        content_blocks.append({
            "type": "text",
            "text": user_prompt,
        })

        # Build messages with content blocks
        messages = [
            {
                "role": "user",
                "content": content_blocks,
            }
        ]

        logger.info(f"Calling Claude API with agent={agent_type}, model={self.model}, images={len(images) if images else 0}")

        # ✅ Verified from Context7:/anthropics/anthropic-sdk-python
        response: Message = await self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system_prompt,
            messages=messages,
            temperature=temperature,
        )

        # Extract text content from response
        response_text = ""
        for block in response.content:
            if hasattr(block, 'text'):
                response_text += block.text

        logger.info(f"Claude API call successful: {response.usage.input_tokens} in, {response.usage.output_tokens} out")

        return {
            "agent_type": agent_type,
            "response": response_text,
            "model": response.model,
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
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
        Make a raw Claude API call without using a template.

        Args:
            system_prompt: System prompt text
            user_prompt: User prompt text
            temperature: Response temperature

        Returns:
            Dict with response and usage info
        """
        if not self.client:
            raise RuntimeError("Claude API client not initialized.")

        response: Message = await self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            temperature=temperature,
        )

        response_text = ""
        for block in response.content:
            if hasattr(block, 'text'):
                response_text += block.text

        return {
            "response": response_text,
            "model": response.model,
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
        }

    def is_configured(self) -> bool:
        """Check if the client is properly configured with an API key."""
        return bool(self.api_key and self.client)


# Singleton instance for dependency injection
_claude_client: Optional[ClaudeClient] = None


def get_claude_client() -> ClaudeClient:
    """
    Get or create the Claude client singleton.

    Returns:
        ClaudeClient instance
    """
    global _claude_client
    if _claude_client is None:
        _claude_client = ClaudeClient()
    return _claude_client


def reset_claude_client() -> None:
    """Reset the Claude client singleton (for testing)."""
    global _claude_client
    _claude_client = None
