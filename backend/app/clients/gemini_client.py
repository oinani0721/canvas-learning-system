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

from app.config import get_settings, settings

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
        prompt_path: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        """
        Initialize Gemini client.

        Args:
            api_key: API key (defaults to env GOOGLE_API_KEY or config)
            prompt_path: Path to agent prompt templates (defaults to config AGENT_PROMPT_PATH)
            base_url: Custom API base URL for OpenAI-compatible providers

        [Multi-Provider] When base_url is provided, the client uses OpenAI-compatible
        API calls instead of Google genai library.

        Note: model is always read dynamically from Settings via the `model` property.
        This ensures POST /config/ai changes take effect immediately without restart.
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

        self.prompt_path = Path(prompt_path or settings.AGENT_PROMPT_PATH)

        # Cache for loaded prompt templates
        self._prompt_templates: Dict[str, AgentPromptTemplate] = {}

        logger.info(f"GeminiClient initialized with model={self.model}" +
                   (f", base_url={self.base_url}" if self.base_url else ""))

    @property
    def model(self) -> str:
        """Always read model from Settings dynamically. Never cached at creation time."""
        s = get_settings()
        return getattr(s, 'AI_MODEL_NAME', None) or getattr(s, 'GEMINI_MODEL', 'gemini-3.1-flash-lite-preview')

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
            context_instruction = (
                "\n\n## Context Usage Rules\n"
                "下方的「Additional Context」包含了与当前内容相关的检索结果。\n\n"
                "**你必须遵守以下规则：**\n"
                "1. **主动引用**：解释中涉及上下文材料时，用方括号标注来源，"
                "格式如 [lecture 3.md:29-65 (## A* 搜索)]。\n"
                "2. **相关资料列表**：如果上下文包含 `[Notes]` 来源，"
                "在回答末尾添加 `## 相关资料` 小节，列出最多5条相关笔记来源。\n"
                "3. **用户请求优先**：如果上下文中「用户之前的个人理解」包含具体请求"
                "（如「列出笔记」「举例子」），必须直接回应该请求。\n"
                "4. **不编造来源**：只引用上下文中实际存在的来源。\n"
            )
            system_prompt = f"{system_prompt}{context_instruction}\n## Additional Context\n{context}"

        # ✅ Story 12.C.2: 添加调试日志追踪最终发送给AI的内容
        # [Source: docs/plans/epic-12.C-agent-context-pollution-fix.md#Story-12.C.2]
        logger.info(
            f"[Story 12.C.2] GeminiClient.call_agent FINAL PROMPT:\n"
            f"  - agent_type: {agent_type}\n"
            f"  - model: {self.model}\n"
            f"  - system_prompt length: {len(system_prompt)} chars\n"
            f"  - user_prompt length: {len(user_prompt)} chars\n"
            f"  - user_prompt preview: {user_prompt[:400]}..."
        )
        if context:
            # [Story 12.I.4] Removed emoji to fix Windows GBK encoding
            logger.warning(
                f"[Story 12.C.2] WARNING: CONTEXT APPENDED TO SYSTEM PROMPT ({len(context)} chars)\n"
                f"  - context preview: {context[:300]}..."
            )

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
            assert self.client is not None
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=full_prompt,
                config=genai.types.GenerateContentConfig(
                    temperature=temperature,
                ),
            )

            # Diagnose empty responses (safety filters, blocked content, etc.)
            try:
                response_text = response.text or ""
            except ValueError as e:
                # response.text raises ValueError when blocked by safety filters
                logger.error(
                    f"Gemini response blocked for agent={agent_type}: {e}. "
                    f"candidates={getattr(response, 'candidates', 'N/A')}, "
                    f"prompt_feedback={getattr(response, 'prompt_feedback', 'N/A')}"
                )
                response_text = ""

            if not response_text:
                logger.warning(
                    f"Gemini returned EMPTY response for agent={agent_type}. "
                    f"candidates={getattr(response, 'candidates', 'N/A')}, "
                    f"prompt_feedback={getattr(response, 'prompt_feedback', 'N/A')}, "
                    f"model={self.model}"
                )

            logger.info(f"Gemini API call successful for agent={agent_type}, response_len={len(response_text)}")

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
            context_instruction = (
                "\n\n## Context Usage Rules\n"
                "下方的「Additional Context」包含了与当前内容相关的检索结果。\n\n"
                "**你必须遵守以下规则：**\n"
                "1. **主动引用**：解释中涉及上下文材料时，用方括号标注来源，"
                "格式如 [lecture 3.md:29-65 (## A* 搜索)]。\n"
                "2. **相关资料列表**：如果上下文包含 `[Notes]` 来源，"
                "在回答末尾添加 `## 相关资料` 小节，列出最多5条相关笔记来源。\n"
                "3. **用户请求优先**：如果上下文中「用户之前的个人理解」包含具体请求"
                "（如「列出笔记」「举例子」），必须直接回应该请求。\n"
                "4. **不编造来源**：只引用上下文中实际存在的来源。\n"
            )
            system_prompt = f"{system_prompt}{context_instruction}\n## Additional Context\n{context}"

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

    async def call_agent_with_tools(
        self,
        agent_type: str,
        user_prompt: str,
        tool_declarations: "genai.types.Tool",
        tool_executor: Any,
        context: Optional[str] = None,
        max_iterations: int = 3,
        temperature: float = 0.7,
        thinking_budget: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Call API with function calling support (Phase 2: LLM-controlled retrieval).

        The LLM can actively search for information by requesting tool calls.
        This method handles the multi-turn tool calling loop:
        1. Send prompt to LLM with tool declarations
        2. If LLM requests tool calls, execute them and send results back
        3. Repeat until LLM produces a text response or max_iterations reached

        Args:
            agent_type: Agent type name (e.g., 'oral-explanation')
            user_prompt: User's input prompt
            tool_declarations: genai.types.Tool with function declarations
            tool_executor: ToolExecutor instance to execute function calls
            context: Optional pre-fetched context (RAG pipeline results)
            max_iterations: Max tool call rounds (default: 3, prevents infinite loops)
            temperature: Response temperature (0.0-1.0)

        Returns:
            Dict containing agent_type, response, model, usage, tool_calls_made

        Raises:
            RuntimeError: If API key not configured or not using Google genai
        """
        if not self.client:
            raise RuntimeError(
                "Gemini API client required for function calling. "
                "OpenAI-compatible providers do not support this feature yet."
            )

        # Load agent prompt template
        template = self.load_prompt_template(agent_type)

        # Build system prompt with optional context
        system_prompt = template.system_prompt
        if context:
            context_instruction = (
                "\n\n## Context Usage Rules\n"
                "下方的「Additional Context」包含了与当前内容相关的检索结果。\n\n"
                "**你必须遵守以下规则：**\n"
                "1. **主动引用**：解释中涉及上下文材料时，用方括号标注来源，"
                "格式如 [lecture 3.md:29-65 (## A* 搜索)]。\n"
                "2. **相关资料列表**：如果上下文包含 `[Notes]` 来源，"
                "在回答末尾添加 `## 相关资料` 小节，列出最多5条相关笔记来源。\n"
                "3. **用户请求优先**：如果上下文中「用户之前的个人理解」包含具体请求"
                "（如「列出笔记」「举例子」），必须直接回应该请求。\n"
                "4. **不编造来源**：只引用上下文中实际存在的来源。\n"
            )
            system_prompt = f"{system_prompt}{context_instruction}\n## Additional Context\n{context}"

        # Tool-use instruction appended to system prompt
        system_prompt += (
            "\n\n## Available Tools\n"
            "你可以使用以下工具主动搜索信息：\n"
            "- `search_vault_notes`: 搜索笔记库中的相关内容\n"
            "- `search_knowledge_graph`: 搜索知识图谱中的概念和历史记录\n"
            "- `get_note_content`: 读取指定笔记的具体内容\n\n"
            "**如果用户要求列出笔记或需要引用具体资料，请主动调用搜索工具获取信息。**\n"
            "**当你已有足够信息时，直接生成回答即可，无需调用工具。**\n"
        )

        # Build initial contents for multi-turn conversation
        full_prompt = f"{system_prompt}\n\n## User Request\n{user_prompt}"
        contents = [
            genai.types.Content(
                role="user",
                parts=[genai.types.Part.from_text(text=full_prompt)],
            )
        ]

        tool_calls_log: List[Dict[str, Any]] = []
        total_input_tokens = 0
        total_output_tokens = 0
        response = None  # Initialize to satisfy type checker

        for iteration in range(max_iterations):
            logger.info(
                f"[Phase2] Tool calling iteration {iteration + 1}/{max_iterations} "
                f"for agent={agent_type}"
            )

            # Call Gemini with tools (optional thinking tokens for deep reasoning)
            gen_config = genai.types.GenerateContentConfig(
                temperature=temperature,
                tools=[tool_declarations],
            )
            if thinking_budget is not None:
                try:
                    gen_config.thinking_config = genai.types.ThinkingConfig(
                        thinking_budget=thinking_budget
                    )
                except (AttributeError, TypeError):
                    logger.debug("ThinkingConfig not available in this genai version")

            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=contents,  # type: ignore[arg-type]
                config=gen_config,
            )

            # Track usage
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                total_input_tokens += getattr(response.usage_metadata, 'prompt_token_count', 0)
                total_output_tokens += getattr(response.usage_metadata, 'candidates_token_count', 0)

            # Check for function calls in response
            function_calls = response.function_calls
            if not function_calls:
                # No tool calls - LLM is done, extract text response
                try:
                    response_text = response.text or ""
                except ValueError:
                    response_text = ""

                logger.info(
                    f"[Phase2] Agent={agent_type} completed after {iteration + 1} iterations, "
                    f"{len(tool_calls_log)} tool calls made, response_len={len(response_text)}"
                )
                return {
                    "agent_type": agent_type,
                    "response": response_text,
                    "model": self.model,
                    "usage": {
                        "input_tokens": total_input_tokens,
                        "output_tokens": total_output_tokens,
                    },
                    "tool_calls_made": tool_calls_log,
                }

            # Execute tool calls and build response
            # Append model's function call content to history
            if response.candidates is None:
                break
            model_content = response.candidates[0].content
            contents.append(model_content)  # type: ignore[arg-type]

            # Execute each function call and collect responses
            function_response_parts = []
            for fc in function_calls:
                fc_name = fc.name
                fc_args = dict(fc.args) if fc.args else {}
                logger.info(f"[Phase2] Tool call: {fc_name}({fc_args})")

                result = await tool_executor.execute(fc_name, fc_args)

                tool_calls_log.append({
                    "iteration": iteration + 1,
                    "name": fc_name,
                    "args": fc_args,
                    "result_length": len(result),
                })

                function_response_parts.append(
                    genai.types.Part.from_function_response(
                        name=fc_name or "",
                        response={"result": result},
                    )
                )

            # Append tool responses to conversation
            contents.append(
                genai.types.Content(
                    role="tool",
                    parts=function_response_parts,
                )
            )

        # Max iterations reached - extract whatever text we have
        logger.warning(
            f"[Phase2] Max iterations ({max_iterations}) reached for agent={agent_type}. "
            f"Forcing text extraction."
        )
        if response is not None:
            try:
                response_text = response.text or ""
            except (ValueError, AttributeError):
                response_text = ""
        else:
            response_text = ""

        return {
            "agent_type": agent_type,
            "response": response_text,
            "model": self.model,
            "usage": {
                "input_tokens": total_input_tokens,
                "output_tokens": total_output_tokens,
            },
            "tool_calls_made": tool_calls_log,
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
