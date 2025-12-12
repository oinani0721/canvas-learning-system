# ✅ Verified structure from docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层
# ✅ Epic 20 Story 20.4: AgentService重写 - 使用真实Gemini API调用
# ✅ Verified from Context7:/googleapis/python-genai (topic: async generate content)
"""
Agent Service - Business logic for Agent operations.

This service provides async methods for Agent calls,
wrapping the Gemini API functionality with async support.

[Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层]
[Source: docs/prd/sprint-change-proposal-20251208.md - Story 20.4]
[Source: Gemini Migration - Using google.genai instead of anthropic]
"""
import asyncio
import json
import logging
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.clients.gemini_client import GeminiClient
    from app.clients.graphiti_client import LearningMemoryClient

logger = logging.getLogger(__name__)


class AgentType(str, Enum):
    """
    Agent类型枚举
    [Source: helpers.md#Section-1-14-agents详细说明]
    """
    BASIC_DECOMPOSITION = "basic-decomposition"
    DEEP_DECOMPOSITION = "deep-decomposition"
    QUESTION_DECOMPOSITION = "question-decomposition"
    ORAL_EXPLANATION = "oral-explanation"
    FOUR_LEVEL_EXPLANATION = "four-level-explanation"
    FOUR_LEVEL = "four-level"  # Alias for FOUR_LEVEL_EXPLANATION
    CLARIFICATION_PATH = "clarification-path"
    COMPARISON_TABLE = "comparison-table"
    EXAMPLE_TEACHING = "example-teaching"
    MEMORY_ANCHOR = "memory-anchor"
    SCORING_AGENT = "scoring-agent"
    SCORING = "scoring"  # Alias for SCORING_AGENT
    VERIFICATION_QUESTION = "verification-question-agent"
    CANVAS_ORCHESTRATOR = "canvas-orchestrator"


@dataclass
class AgentResult:
    """
    Agent调用结果数据类
    [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层]
    """
    agent_type: AgentType
    node_id: str = ""
    success: bool = True
    result: Optional[Dict[str, Any]] = None
    data: Optional[Dict[str, Any]] = None  # Alias for result
    error: Optional[str] = None
    duration_ms: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Ensure data and result are synchronized"""
        if self.data is None and self.result is not None:
            self.data = self.result
        elif self.result is None and self.data is not None:
            self.result = self.data

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "agent_type": self.agent_type.value,
            "node_id": self.node_id,
            "success": self.success,
            "result": self.result,
            "data": self.data,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "created_at": self.created_at.isoformat(),
        }


class AgentService:
    """
    Agent call business logic service.

    Provides async methods for invoking various learning agents
    (basic-decomposition, scoring, oral-explanation, etc.).

    [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层]
    [Source: docs/prd/sprint-change-proposal-20251208.md - Story 20.4]
    """

    def __init__(
        self,
        gemini_client: Optional["GeminiClient"] = None,
        memory_client: Optional["LearningMemoryClient"] = None,
        max_concurrent: int = 10,
        ai_config: Optional[Any] = None  # AIConfig from dependencies.py
    ):
        """
        Initialize AgentService with optional GeminiClient and LearningMemoryClient.

        ✅ Verified from Context7:/googleapis/python-genai (topic: async generate content)

        Args:
            gemini_client: GeminiClient instance for real Gemini API calls.
                          If None or not configured, raises error (no mock fallback).
            memory_client: LearningMemoryClient for querying historical learning memories.
                          If None, historical context is not included.
            max_concurrent: Maximum concurrent agent calls (default: 10)
            ai_config: AIConfig dataclass with provider, model, base_url, api_key.
                      Used for future multi-provider support.

        [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#依赖注入设计]
        [Source: docs/prd/sprint-change-proposal-20251208.md - Story 20.4]
        [Source: FIX-4.2 Agent调用时查询历史]
        [Source: Multi-Provider AI Architecture]
        """
        self._gemini_client = gemini_client
        self._memory_client = memory_client
        self._max_concurrent = max_concurrent
        self._ai_config = ai_config  # Store for future multi-provider support
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._total_calls = 0
        self._active_calls = 0
        self._initialized = True
        self._use_real_api = gemini_client is not None and gemini_client.is_configured()

        # Log AI configuration
        if ai_config:
            provider = getattr(ai_config, 'provider', 'unknown')
            model = getattr(ai_config, 'model_name', 'unknown')
            logger.info(f"AgentService AI config: provider={provider}, model={model}")

        if self._use_real_api:
            logger.info("AgentService initialized with REAL AI API calls")
        else:
            logger.warning("AgentService initialized without configured AI client - API calls will fail")

        if self._memory_client:
            logger.info("AgentService will use LearningMemoryClient for historical context")

        logger.debug(f"AgentService max_concurrent={max_concurrent}")

    @property
    def total_calls(self) -> int:
        """Total number of agent calls made"""
        return self._total_calls

    @property
    def active_calls(self) -> int:
        """Current number of active agent calls"""
        return self._active_calls

    async def _call_gemini_api(
        self,
        agent_type: AgentType,
        prompt: str,
        context: Optional[str] = None,
        canvas_name: Optional[str] = None,
        node_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Call Gemini API through GeminiClient.

        ✅ Verified from Context7:/googleapis/python-genai (topic: async generate content)

        Makes a real Gemini API call. No mock fallback - raises error if not configured.

        FIX-4.2: Now queries historical learning memories and enriches context.

        Args:
            agent_type: Type of agent to invoke
            prompt: User prompt to send
            context: Optional additional context (e.g., adjacent nodes, textbook refs)
            canvas_name: Optional Canvas name for memory lookup
            node_id: Optional node ID for memory lookup

        Returns:
            Dict with agent response

        [Source: docs/prd/sprint-change-proposal-20251208.md - Story 20.4]
        [Source: FIX-4.2 Agent调用时查询历史]
        [Source: Gemini Migration - Using google.genai instead of anthropic]
        """
        # FIX-4.2: Query historical memories before calling Claude
        enriched_context = context or ""

        if self._memory_client and (canvas_name or prompt):
            try:
                # Search for relevant memories
                query = prompt[:100] if prompt else ""
                memories = await self._memory_client.search_memories(
                    query=query,
                    canvas_name=canvas_name,
                    node_id=node_id,
                    limit=5
                )

                if memories:
                    memory_context = self._memory_client.format_for_context(memories)
                    if memory_context:
                        enriched_context = f"{enriched_context}\n\n{memory_context}" if enriched_context else memory_context
                        logger.debug(f"Added {len(memories)} historical memories to context")

            except Exception as e:
                logger.warning(f"Failed to query historical memories: {e}")
                # Continue without memories - graceful degradation

        # Phase 1 FIX: 强制真实API调用，不再回退到Mock
        # [Source: C:\Users\ROG\.claude\plans\wild-purring-umbrella.md - Phase 1]
        # [Gemini Migration] Now uses GOOGLE_API_KEY instead of ANTHROPIC_API_KEY
        if not self._use_real_api:
            # FIX: Provide diagnostic information in error message
            ai_config_info = ""
            if self._ai_config:
                ai_config_info = (
                    f" (Received config: provider={getattr(self._ai_config, 'provider', 'unknown')}, "
                    f"model={getattr(self._ai_config, 'model_name', 'unknown')}, "
                    f"has_api_key={bool(getattr(self._ai_config, 'api_key', ''))}, "
                    f"base_url={getattr(self._ai_config, 'base_url', 'none')!r})"
                )
            raise RuntimeError(
                f"AI API not configured!{ai_config_info} "
                "For custom providers, ensure base_url is set. "
                "Check: 1) API key in plugin settings, 2) base_url for custom providers, "
                "3) Headers being sent (browser dev tools)."
            )

        if not self._gemini_client:
            raise RuntimeError(
                "GeminiClient not initialized. "
                "This is a configuration error - check backend startup logs."
            )

        # Real Gemini API call - 不再有Mock回退
        # ✅ Verified from Context7:/googleapis/python-genai (topic: async generate content)
        logger.info(f"Making REAL Gemini API call for agent: {agent_type.value}")
        try:
            result = await self._gemini_client.call_agent(
                agent_type=agent_type.value,
                user_prompt=prompt,
                context=enriched_context if enriched_context else None,
                temperature=0.7
            )

            # ✅ FIX: Parse AI response JSON from string
            # [Source: Plan - unified-knitting-crane.md - Root Cause Analysis]
            # GeminiClient returns {"response": "JSON_STRING", ...}
            # We need to parse the JSON string and merge it into result
            if "response" in result and isinstance(result["response"], str):
                response_text = result["response"]
                try:
                    json_text = response_text.strip()

                    # Handle markdown code block wrappers
                    if "```json" in json_text:
                        json_text = json_text.split("```json")[1].split("```")[0].strip()
                    elif "```" in json_text:
                        # Handle code blocks without language marker
                        parts = json_text.split("```")
                        if len(parts) >= 3:
                            json_text = parts[1].strip()

                    # Parse JSON (json module imported at file top, line 15)
                    parsed = json.loads(json_text)

                    # Merge parsed data into result
                    if isinstance(parsed, dict):
                        result.update(parsed)
                        logger.debug(f"Parsed AI response JSON keys: {list(parsed.keys())}")
                except (json.JSONDecodeError, IndexError, ValueError) as e:
                    # Catch more exception types for robustness
                    logger.warning(f"Failed to parse AI response as JSON: {e}")
                    logger.debug(f"Raw response (first 500 chars): {response_text[:500] if response_text else 'empty'}...")

            # 添加来源标记，便于验证是真实API调用
            result["_source"] = "gemini_api"
            result["_mock"] = False
            logger.info(f"Gemini API success: {result.get('usage', {})}")
            return result
        except FileNotFoundError as e:
            # Prompt template not found - 不再回退到Mock，直接报错
            logger.error(f"Prompt template not found for {agent_type.value}: {e}")
            raise FileNotFoundError(
                f"Agent prompt template missing: {agent_type.value}. "
                f"Please ensure .claude/agents/{agent_type.value}.md exists."
            ) from e
        except Exception as e:
            logger.error(f"Gemini API error for {agent_type.value}: {e}")
            raise

    # Phase 1 FIX: _mock_response removed - all calls must use real Gemini API
    # [Source: C:\Users\ROG\.claude\plans\wild-purring-umbrella.md - Phase 1]
    # [Source: Gemini Migration - Using google.genai instead of anthropic]

    def _enrich_prompt_with_neighbors(
        self,
        original_content: str,
        adjacent_data: Dict[str, Any],
        max_context_length: int = 200
    ) -> str:
        """
        Enrich agent prompt with adjacent node content.

        Phase 4.1: Option A - Adjacent Node Enrichment
        Injects parent and child node context into the Agent prompt.

        Args:
            original_content: Original node content
            adjacent_data: Result from CanvasService.get_adjacent_nodes()
            max_context_length: Maximum characters per adjacent node

        Returns:
            Enriched prompt with neighbor context

        [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Phase-4-Edge-Enhancement]
        """
        if not adjacent_data:
            return original_content

        parents = adjacent_data.get("parents", [])
        children = adjacent_data.get("children", [])

        # If no neighbors, return original
        if not parents and not children:
            return original_content

        context_parts = [original_content, "\n\n### Adjacent Concept Context (相邻概念上下文):"]

        # Add parent context
        for parent_info in parents:
            parent_node = parent_info.get("node", {})
            label = parent_info.get("label", "related")
            text = parent_node.get("text", "")[:max_context_length]
            node_type = parent_node.get("type", "text")

            if text:
                context_parts.append(f"\n- Parent [{label or 'prerequisite'}] ({node_type}): {text}")

        # Add child context
        for child_info in children:
            child_node = child_info.get("node", {})
            label = child_info.get("label", "related")
            text = child_node.get("text", "")[:max_context_length]
            node_type = child_node.get("type", "text")

            if text:
                context_parts.append(f"\n- Child [{label or 'extends'}] ({node_type}): {text}")

        return "\n".join(context_parts)

    async def call_agent(
        self,
        agent_type: AgentType,
        prompt: str,
        timeout: Optional[float] = None,
        context: Optional[str] = None
    ) -> AgentResult:
        """
        Call a single agent with concurrency control.

        Uses real Claude API if ClaudeClient is configured, otherwise mock.

        Args:
            agent_type: Type of agent to call
            prompt: Input prompt for the agent
            timeout: Optional timeout in seconds
            context: Optional additional context for the agent

        Returns:
            AgentResult with the response

        [Source: docs/prd/sprint-change-proposal-20251208.md - Story 20.4]
        """
        start_time = datetime.now()
        async with self._semaphore:
            self._active_calls += 1
            self._total_calls += 1
            try:
                if timeout:
                    data = await asyncio.wait_for(
                        self._call_gemini_api(agent_type, prompt, context),
                        timeout=timeout
                    )
                else:
                    data = await self._call_gemini_api(agent_type, prompt, context)

                duration_ms = (datetime.now() - start_time).total_seconds() * 1000
                return AgentResult(
                    agent_type=agent_type,
                    success=True,
                    result=data,
                    data=data,
                    duration_ms=duration_ms,
                )
            except asyncio.TimeoutError:
                return AgentResult(
                    agent_type=agent_type,
                    success=False,
                    error="Agent call timed out",
                )
            except Exception as e:
                logger.error(f"Agent call failed: {agent_type.value} - {e}")
                return AgentResult(
                    agent_type=agent_type,
                    success=False,
                    error=str(e),
                )
            finally:
                self._active_calls -= 1

    async def call_agent_with_images(
        self,
        agent_type: AgentType,
        prompt: str,
        images: Optional[List[Dict[str, Any]]] = None,
        timeout: Optional[float] = None,
        context: Optional[str] = None
    ) -> AgentResult:
        """
        Call a single agent with images (multimodal support).

        Uses real Claude API with vision capabilities.

        Args:
            agent_type: Type of agent to call
            prompt: Input prompt for the agent
            images: List of image dicts with 'data' (base64) and 'media_type'
            timeout: Optional timeout in seconds
            context: Optional additional context for the agent

        Returns:
            AgentResult with the response

        [Source: FIX-2.1 实现Claude Vision多模态支持]
        """
        start_time = datetime.now()
        async with self._semaphore:
            self._active_calls += 1
            self._total_calls += 1
            try:
                if self._gemini_client:
                    # ✅ Verified from Context7:/googleapis/python-genai
                    # Gemini natively supports multimodal input
                    agent_type_str = agent_type.value if isinstance(agent_type, AgentType) else agent_type

                    if timeout:
                        data = await asyncio.wait_for(
                            self._gemini_client.call_agent_with_images(
                                agent_type_str, prompt, images=images, context=context
                            ),
                            timeout=timeout
                        )
                    else:
                        data = await self._gemini_client.call_agent_with_images(
                            agent_type_str, prompt, images=images, context=context
                        )
                else:
                    # Phase 1 FIX: No fallback to mock - raise error if not configured
                    # [Source: C:\Users\ROG\.claude\plans\wild-purring-umbrella.md - Phase 1]
                    # [Gemini Migration] Now uses GOOGLE_API_KEY
                    raise RuntimeError(
                        "GeminiClient not configured for multimodal! "
                        "Please set GOOGLE_API_KEY in backend/.env or plugin settings."
                    )

                duration_ms = (datetime.now() - start_time).total_seconds() * 1000
                return AgentResult(
                    agent_type=agent_type,
                    success=True,
                    result=data,
                    data=data,
                    duration_ms=duration_ms,
                )
            except asyncio.TimeoutError:
                return AgentResult(
                    agent_type=agent_type,
                    success=False,
                    error="Agent call with images timed out",
                )
            except Exception as e:
                logger.error(f"Agent call with images failed: {agent_type.value} - {e}")
                return AgentResult(
                    agent_type=agent_type,
                    success=False,
                    error=str(e),
                )
            finally:
                self._active_calls -= 1

    async def call_agents_batch(
        self,
        requests: List[Dict[str, Any]],
        return_exceptions: bool = False
    ) -> List[AgentResult]:
        """
        Call multiple agents concurrently.

        Args:
            requests: List of dicts with 'agent_type' and 'prompt' keys
            return_exceptions: If True, return exceptions as results

        Returns:
            List of AgentResult objects
        """
        tasks = [
            self.call_agent(req["agent_type"], req["prompt"])
            for req in requests
        ]

        if return_exceptions:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            # Convert exceptions to AgentResult with error
            processed = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    processed.append(AgentResult(
                        agent_type=requests[i]["agent_type"],
                        success=False,
                        error=str(result),
                    ))
                else:
                    processed.append(result)
            return processed
        else:
            return await asyncio.gather(*tasks)

    async def call_decomposition(
        self,
        content: str,
        deep: bool = False
    ) -> AgentResult:
        """
        Call decomposition agent.

        Args:
            content: Content to decompose
            deep: If True, use deep decomposition

        Returns:
            AgentResult with decomposition
        """
        agent_type = AgentType.DEEP_DECOMPOSITION if deep else AgentType.BASIC_DECOMPOSITION
        return await self.call_agent(agent_type, content)

    async def call_scoring(
        self,
        node_content: str,
        user_understanding: str
    ) -> AgentResult:
        """
        Call scoring agent.

        Args:
            node_content: Original node content
            user_understanding: User's explanation

        Returns:
            AgentResult with scores
        """
        prompt = f"Content: {node_content}\nUser: {user_understanding}"
        return await self.call_agent(AgentType.SCORING, prompt)

    async def call_explanation(
        self,
        content: str,
        explanation_type: str = "oral",
        context: Optional[str] = None,
        images: Optional[List[Dict[str, Any]]] = None
    ) -> AgentResult:
        """
        Call explanation agent with optional multimodal support.

        Args:
            content: Content to explain
            explanation_type: Type of explanation
            context: Optional additional context (adjacent nodes, textbook refs, etc.)
            images: Optional list of images for multimodal analysis

        Returns:
            AgentResult with explanation

        [Source: FIX-1.1 修复上下文传递链]
        [Source: FIX-2.1 实现Claude Vision多模态支持]
        """
        type_map = {
            "oral": AgentType.ORAL_EXPLANATION,
            "clarification": AgentType.CLARIFICATION_PATH,
            "comparison": AgentType.COMPARISON_TABLE,
            "memory": AgentType.MEMORY_ANCHOR,
            "four_level": AgentType.FOUR_LEVEL,
            "four-level": AgentType.FOUR_LEVEL,  # ✅ Support both formats
            "example": AgentType.EXAMPLE_TEACHING,
        }
        agent_type = type_map.get(explanation_type, AgentType.ORAL_EXPLANATION)

        # ✅ FIX-2.1: Use multimodal call if images are provided
        if images and len(images) > 0:
            logger.info(f"Calling {agent_type.value} with {len(images)} images")
            return await self.call_agent_with_images(
                agent_type, content, images=images, context=context
            )

        # ✅ FIX-1.1: Pass context to call_agent for adjacent node enrichment
        return await self.call_agent(agent_type, content, context=context)

    async def decompose_basic(
        self,
        canvas_name: str,
        node_id: str,
        content: str,
        source_x: float = 0,
        source_y: float = 0
    ) -> Dict[str, Any]:
        """
        Perform basic decomposition on a concept node.

        Args:
            canvas_name: Target canvas name
            node_id: ID of node to decompose
            content: Node content to decompose
            source_x: X coordinate of source node (for positioning new nodes)
            source_y: Y coordinate of source node (for positioning new nodes)

        Returns:
            Decomposition result with guiding questions and created_nodes for Canvas

        [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层]
        [FIX: Return created_nodes array for frontend to write to Canvas]
        """
        import uuid

        logger.debug(f"Basic decomposition for node {node_id}")
        result = await self.call_decomposition(content, deep=False)

        # Extract questions from AI result
        questions = []
        created_nodes = []

        if result.success and result.data:
            sub_questions = result.data.get("sub_questions", [])

            # Generate Canvas nodes for each question
            # Position nodes below and to the right of source node
            node_width = 280
            node_height = 100
            gap_x = 20
            gap_y = 30
            nodes_per_row = 2

            for idx, q in enumerate(sub_questions):
                question_text = q.get("text", "")
                question_type = q.get("type", "")
                guidance = q.get("guidance", "")

                # Format node text with type and guidance
                node_text = question_text
                if question_type:
                    node_text = f"[{question_type}] {node_text}"
                if guidance:
                    node_text = f"{node_text}\n\n{guidance}"

                questions.append(question_text)

                # Calculate position (grid layout below source node)
                row = idx // nodes_per_row
                col = idx % nodes_per_row
                x = source_x + col * (node_width + gap_x)
                y = source_y + 150 + row * (node_height + gap_y)  # 150px below source

                # Create node object matching frontend NodeRead type
                created_nodes.append({
                    "id": f"q-{node_id}-{idx}-{uuid.uuid4().hex[:8]}",
                    "type": "text",
                    "text": node_text,
                    "x": x,
                    "y": y,
                    "width": node_width,
                    "height": node_height,
                    "color": "3",  # Yellow - indicates question/understanding area
                })

        logger.info(f"Basic decomposition created {len(created_nodes)} nodes")
        return {
            "node_id": node_id,
            "questions": questions,
            "created_nodes": created_nodes,
            "status": "completed",
            "result": result.data,
        }

    async def decompose_deep(
        self,
        canvas_name: str,
        node_id: str,
        content: str,
        source_x: float = 0,
        source_y: float = 0
    ) -> Dict[str, Any]:
        """
        Perform deep decomposition for verification questions.

        Args:
            canvas_name: Target canvas name
            node_id: ID of node to decompose
            content: Node content to decompose
            source_x: X coordinate of source node for positioning
            source_y: Y coordinate of source node for positioning

        Returns:
            Deep verification questions and created nodes

        [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层]
        """
        import uuid
        logger.debug(f"Deep decomposition for node {node_id}")
        result = await self.call_decomposition(content, deep=True)

        verification_questions = []
        created_nodes = []

        if result.success and result.data:
            # Extract sub_questions from AI result
            sub_questions = result.data.get("sub_questions", [])

            # Node positioning parameters
            node_width = 300
            node_height = 120
            gap_x = 20
            gap_y = 40
            nodes_per_row = 2

            for idx, q in enumerate(sub_questions):
                question_text = q.get("text", "")
                question_type = q.get("type", "")
                guidance = q.get("guidance", "")

                # Build node text with type and guidance
                node_text = question_text
                if question_type:
                    node_text = f"[{question_type}] {node_text}"
                if guidance:
                    node_text = f"{node_text}\n\n{guidance}"

                verification_questions.append(question_text)

                # Calculate position (grid layout below source node)
                row = idx // nodes_per_row
                col = idx % nodes_per_row
                x = source_x + col * (node_width + gap_x)
                y = source_y + 180 + row * (node_height + gap_y)  # 180px below source

                # Create node object matching frontend NodeRead type
                # Deep decomposition uses purple color (indicating "partially understood")
                created_nodes.append({
                    "id": f"vq-{node_id}-{idx}-{uuid.uuid4().hex[:8]}",
                    "type": "text",
                    "text": node_text,
                    "x": x,
                    "y": y,
                    "width": node_width,
                    "height": node_height,
                    "color": "6",  # Purple - indicates verification/deep question
                })

        logger.info(f"Deep decomposition created {len(created_nodes)} nodes")
        return {
            "node_id": node_id,
            "verification_questions": verification_questions,
            "created_nodes": created_nodes,
            "status": "completed",
            "result": result.data,
        }

    async def score_node(
        self,
        canvas_name: str,
        node_ids: List[str],
        node_contents: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Score multiple nodes' understanding.

        Args:
            canvas_name: Target canvas name
            node_ids: List of node IDs to score
            node_contents: Dict mapping node_id to content text

        Returns:
            {"scores": [{"node_id": ..., "accuracy": ..., ...}]}

        [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层]
        [Source: FIX-4.2 记录学习历程]
        [Source: FIX-5.1 修复score_node签名不匹配]
        """
        logger.debug(f"Scoring {len(node_ids)} nodes")

        scores = []
        for node_id in node_ids:
            content = node_contents.get(node_id, "")

            # Call scoring for each node
            result = await self.call_scoring("", content)

            # Determine color based on score
            total_score = 0.0
            if result.success and result.data:
                total_score = result.data.get("total", 0.0)

            # Color mapping: 0-40% red, 40-70% yellow, 70%+ green
            if total_score >= 0.7:
                new_color = "4"  # green
            elif total_score >= 0.4:
                new_color = "3"  # yellow
            else:
                new_color = "1"  # red

            scores.append({
                "node_id": node_id,
                "accuracy": result.data.get("accuracy", 0.0) if result.data else 0.0,
                "imagery": result.data.get("imagery", 0.0) if result.data else 0.0,
                "completeness": result.data.get("completeness", 0.0) if result.data else 0.0,
                "originality": result.data.get("originality", 0.0) if result.data else 0.0,
                "total": total_score,
                "new_color": new_color,
            })

            # Record learning episode
            await self.record_learning_episode(
                canvas_name=canvas_name,
                node_id=node_id,
                concept=content[:50] if content else "Unknown",
                user_understanding=content,
                score=total_score,
                agent_feedback=str(result.data) if result.data else None
            )

        return {"scores": scores}

    async def find_related_understanding_content(
        self,
        canvas_name: str,
        source_node_id: str,
        canvas_data: Dict[str, Any]
    ) -> List[str]:
        """
        FIX-4.4: 查找与源节点关联的所有黄色理解节点内容。

        通过 Canvas 的 edges 追踪：
        源节点 → 解释节点 → 黄色理解节点

        用于在生成新解释时，结合用户之前填写的个人理解，
        实现个性化、渐进式的学习解释。

        Args:
            canvas_name: Canvas 文件名
            source_node_id: 源节点 ID
            canvas_data: Canvas 数据字典

        Returns:
            用户填写的理解内容列表（排除空内容和占位符）
        """
        understanding_contents = []

        # 遍历所有 edges，找到从源节点出发的解释链
        edges = canvas_data.get("edges", [])
        nodes = {n["id"]: n for n in canvas_data.get("nodes", [])}

        # 查找所有与源节点相关的节点（通过 edge 关系，BFS遍历）
        related_node_ids = set()
        queue = [source_node_id]
        visited = {source_node_id}

        while queue:
            current_id = queue.pop(0)
            for edge in edges:
                if edge.get("fromNode") == current_id:
                    to_node_id = edge.get("toNode")
                    if to_node_id and to_node_id not in visited:
                        related_node_ids.add(to_node_id)
                        visited.add(to_node_id)
                        queue.append(to_node_id)

        logger.info(f"[FIX-4.4] Found {len(related_node_ids)} related nodes for {source_node_id}")

        # 从关联节点中找出黄色节点（color: "3"）并读取内容
        for node_id in related_node_ids:
            node = nodes.get(node_id)
            if node and node.get("color") == "3":  # Yellow node
                logger.debug(f"[FIX-4.4] Found yellow node: {node_id}, type={node.get('type')}")

                if node.get("type") == "file" and node.get("file"):
                    # FIX-4.4: Read file content from vault
                    content = await self.canvas_service.read_file_content(node["file"])
                    if content:
                        understanding_contents.append(content)
                        logger.info(f"[FIX-4.4] Read understanding from file: {node['file']}")
                elif node.get("type") == "text" and node.get("text"):
                    text = node["text"].strip()
                    if text and "[请在此填写" not in text:
                        understanding_contents.append(text)
                        logger.info(f"[FIX-4.4] Read understanding from text node: {node_id}")

        logger.info(f"[FIX-4.4] Total user understandings found: {len(understanding_contents)}")
        return understanding_contents

    async def generate_explanation(
        self,
        canvas_name: str,
        node_id: str,
        content: str,
        explanation_type: str = "oral",
        adjacent_context: Optional[str] = None,
        images: Optional[List[Dict[str, Any]]] = None,
        source_x: float = 0,
        source_y: float = 0,
        source_width: float = 400,
        source_height: float = 200
    ) -> Dict[str, Any]:
        """
        Generate an explanation for a concept with adjacent node context and optional images.

        Args:
            canvas_name: Target canvas name
            node_id: ID of node to explain
            content: Node content to explain
            explanation_type: Type of explanation (oral, four-level, etc.)
            adjacent_context: Context from adjacent nodes (1-hop neighbors)
            images: Optional list of images for multimodal analysis
            source_x: X coordinate of source node (for positioning new nodes)
            source_y: Y coordinate of source node (for positioning new nodes)
            source_width: Width of source node
            source_height: Height of source node

        Returns:
            Generated explanation with created_nodes for Canvas

        [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层]
        [Source: FIX-1.1 修复上下文传递链 - adjacent_context now flows through]
        [Source: FIX-2.1 实现Claude Vision多模态支持]
        [Source: FIX-3.0 返回created_nodes数组用于Canvas写入]
        """
        import uuid
        import json as json_module  # Avoid conflict with local variables

        context_len = len(adjacent_context) if adjacent_context else 0
        images_count = len(images) if images else 0
        logger.debug(f"Generating {explanation_type} explanation for node {node_id}, context_len={context_len}, images={images_count}")

        # ✅ FIX-4.4: 读取用户之前填写的个人理解
        user_understandings = []
        try:
            from app.config import settings
            canvas_path = os.path.join(settings.CANVAS_BASE_PATH, canvas_name)
            if not canvas_path.endswith('.canvas'):
                canvas_path += '.canvas'

            if os.path.exists(canvas_path):
                with open(canvas_path, 'r', encoding='utf-8') as f:
                    canvas_data = json_module.load(f)

                # 查找关联的黄色理解节点内容
                user_understandings = await self.find_related_understanding_content(
                    canvas_name, node_id, canvas_data
                )
                logger.info(f"[FIX-4.4] Found {len(user_understandings)} user understandings for node {node_id}")
        except Exception as e:
            logger.warning(f"[FIX-4.4] Failed to read user understandings: {e}")

        # ✅ FIX-4.4: 构建包含用户理解的增强上下文
        enhanced_context = adjacent_context or ""
        if user_understandings:
            user_context = "\n\n## 用户之前的个人理解\n\n"
            for i, understanding in enumerate(user_understandings, 1):
                user_context += f"### 理解 {i}\n{understanding}\n\n"
            user_context += "请结合用户的这些理解，生成更贴合用户认知水平的解释。如果用户理解有误，请在解释中委婉纠正。\n"
            enhanced_context = (enhanced_context + user_context) if enhanced_context else user_context
            logger.info(f"[FIX-4.4] Enhanced context with {len(user_understandings)} user understandings")

        # ✅ FIX-1.1: Pass adjacent_context to call_explanation
        # ✅ FIX-2.1: Pass images for multimodal support
        # ✅ FIX-4.4: Pass enhanced_context with user understandings
        result = await self.call_explanation(
            content, explanation_type, context=enhanced_context, images=images
        )

        # ✅ FIX: Extract explanation text from AI response
        # [Source: unified-knitting-crane.md - Root Cause: ExplainResponse validation failed]
        # The AI returns Markdown text directly in result.data["response"]
        explanation_text = ""
        if result.data:
            if isinstance(result.data, dict):
                # AI response is in "response" field as Markdown text
                explanation_text = result.data.get("response", "")
                if not explanation_text:
                    # Fallback: try "explanation" key or stringify the dict
                    explanation_text = result.data.get("explanation", str(result.data))
            elif isinstance(result.data, str):
                explanation_text = result.data
            else:
                explanation_text = str(result.data)

        # ✅ FIX: Generate created_node_id (required by ExplainResponse)
        created_node_id = f"explain-{explanation_type}-{node_id}-{uuid.uuid4().hex[:8]}"

        # ✅ FIX-4.3: Create file nodes instead of text nodes
        # All explanation nodes will be .md files stored in {canvas}-explanations/ folder
        created_nodes = []
        created_edges = []

        # ✅ FIX-4.3: Calculate explanations directory path
        from app.config import settings
        from datetime import datetime
        import re

        vault_path = settings.CANVAS_BASE_PATH  # e.g., "C:/Users/ROG/托福/Canvas/笔记库"
        # canvas_name is relative path like "Canvas/Math53/Lecture5.canvas"
        canvas_dir = os.path.dirname(canvas_name)  # "Canvas/Math53"
        canvas_basename = os.path.splitext(os.path.basename(canvas_name))[0]  # "Lecture5"
        explanations_dir = f"{canvas_dir}/{canvas_basename}-explanations"  # "Canvas/Math53/Lecture5-explanations"

        # Create explanations directory if it doesn't exist
        full_explanations_dir = os.path.join(vault_path, explanations_dir)
        os.makedirs(full_explanations_dir, exist_ok=True)
        logger.info(f"[FIX-4.3] Explanations directory: {full_explanations_dir}")

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

        if explanation_text:
            # Check if this is a four-level explanation (contains level headers)
            is_four_level = explanation_type in ["four-level", "four_level", "four-level-explanation"]
            level_pattern = r'##\s*(新手层|进阶层|专家层|创新层).*?\n'

            if is_four_level and re.search(level_pattern, explanation_text):
                # ✅ FIX-4.8: Create ONE .md file containing ALL 4 levels
                # (User feedback: should be 1 file, not 4 separate files)

                # Layout configuration
                node_width = 500
                node_height = 600  # Taller to accommodate all 4 levels
                yellow_height = 150
                gap_y = 40

                # Position below source node
                node_x = source_x
                node_y = source_y + source_height + gap_y

                # ✅ FIX-4.8: Create single .md file with all 4 levels
                explain_node_id = f"explain-four-level-{node_id[:8]}-{uuid.uuid4().hex[:4]}"
                explain_filename = f"四层次解释-{node_id[:8]}-{timestamp}.md"
                explain_file_path = f"{explanations_dir}/{explain_filename}"
                explain_full_path = os.path.join(vault_path, explain_file_path)

                # Write ALL levels to single .md file
                with open(explain_full_path, 'w', encoding='utf-8') as f:
                    f.write(f"# 四层次解释\n\n{explanation_text}")
                logger.info(f"[FIX-4.8] Created SINGLE four-level explanation file: {explain_file_path}")

                # Create file type node (green for explanation)
                created_nodes.append({
                    "id": explain_node_id,
                    "type": "file",
                    "file": explain_file_path,
                    "x": node_x,
                    "y": node_y,
                    "width": node_width,
                    "height": node_height,
                    "color": "4",  # Green - explanation
                })
                logger.info(f"[FIX-4.8] Created four-level file node {explain_node_id}")

                # ✅ FIX-4.9: Create ONE yellow understanding node
                yellow_node_id = f"understand-four-level-{node_id[:8]}-{uuid.uuid4().hex[:4]}"
                yellow_y = node_y + node_height + gap_y
                created_nodes.append({
                    "id": yellow_node_id,
                    "type": "text",
                    "text": "# 💡 我的理解\n\n[请在此填写你对四层次解释的整体理解...]\n\n## 新手层理解\n\n\n## 进阶层理解\n\n\n## 专家层理解\n\n\n## 创新层理解\n\n",
                    "x": node_x,
                    "y": yellow_y,
                    "width": node_width,
                    "height": yellow_height,
                    "color": "6",  # ✅ FIX-4.11: Purple (matches user's reference node)
                })
                logger.info(f"[FIX-4.11] Created PURPLE understanding node {yellow_node_id}")

                # Create edges: Source → Explanation → Yellow
                edge1_id = f"edge-src-explain-{uuid.uuid4().hex[:8]}"
                created_edges.append({
                    "id": edge1_id,
                    "fromNode": node_id,
                    "toNode": explain_node_id,
                    "fromSide": "bottom",
                    "toSide": "top",
                    "label": "四层次解释",
                })

                edge2_id = f"edge-explain-yellow-{uuid.uuid4().hex[:8]}"
                created_edges.append({
                    "id": edge2_id,
                    "fromNode": explain_node_id,
                    "toNode": yellow_node_id,
                    "fromSide": "bottom",
                    "toSide": "top",
                    "label": "个人理解",  # ✅ FIX-4.10: Add edge label
                    "color": "6",  # ✅ Purple edge (matches user's reference)
                })

                created_node_id = explain_node_id
                logger.info(f"[FIX-4.8/4.9] Four-level explanation complete: 1 file, 1 yellow node, 2 edges")

            else:
                # ✅ FIX-4.3: Standard single-node explanation (oral, basic, etc.) - create .md files
                node_width = 500
                node_height = max(300, min(800, len(explanation_text) // 3))

                # Position below source node
                gap_y = 50
                node_x = source_x
                node_y = source_y + source_height + gap_y

                # ✅ FIX-4.3: Create .md file for explanation node
                explain_filename = f"{explanation_type}-解释-{node_id[:8]}-{timestamp}.md"
                explain_file_path = f"{explanations_dir}/{explain_filename}"
                explain_full_path = os.path.join(vault_path, explain_file_path)

                # Write explanation content to .md file
                with open(explain_full_path, 'w', encoding='utf-8') as f:
                    f.write(f"# {explanation_type.title()} 解释\n\n{explanation_text}")
                logger.info(f"[FIX-4.3] Created explanation file: {explain_file_path}")

                # Create file type node
                created_nodes.append({
                    "id": created_node_id,
                    "type": "file",
                    "file": explain_file_path,  # Relative to vault
                    "x": node_x,
                    "y": node_y,
                    "width": node_width,
                    "height": node_height,
                    "color": "4",  # Green - indicates explanation
                })
                logger.info(f"[FIX-4.3] Created explanation file node {created_node_id} at ({node_x}, {node_y})")

                # ✅ FIX-4.5: Create text type yellow understanding node (directly editable in Canvas)
                yellow_node_id = f"understand-{node_id[:8]}-{uuid.uuid4().hex[:4]}"
                yellow_y = node_y + node_height + 30
                created_nodes.append({
                    "id": yellow_node_id,
                    "type": "text",
                    "text": "# 💡 我的理解\n\n[请在此填写你的个人理解...]",
                    "x": node_x,
                    "y": yellow_y,
                    "width": node_width,
                    "height": 120,
                    "color": "3",  # Yellow
                })
                logger.info(f"[FIX-4.5] Created yellow text node {yellow_node_id}")

                # Create edges: Source → Explanation → Yellow
                edge1_id = f"edge-{node_id[:8]}-{created_node_id[:8]}-{uuid.uuid4().hex[:4]}"
                created_edges.append({
                    "id": edge1_id,
                    "fromNode": node_id,
                    "toNode": created_node_id,
                    "fromSide": "bottom",
                    "toSide": "top",
                    "label": explanation_type,
                })

                edge2_id = f"edge-{created_node_id[:8]}-{yellow_node_id[:8]}-{uuid.uuid4().hex[:4]}"
                created_edges.append({
                    "id": edge2_id,
                    "fromNode": created_node_id,
                    "toNode": yellow_node_id,
                    "fromSide": "bottom",
                    "toSide": "top",
                })

                logger.info(f"[FIX-4.3] Created edges for standard explanation")

        return {
            "node_id": node_id,
            "explanation_type": explanation_type,
            "explanation": explanation_text,  # ✅ Now contains actual AI response
            "created_node_id": created_node_id,  # ✅ Required by ExplainResponse
            "created_nodes": created_nodes,  # ✅ FIX-3.0: Nodes for Canvas
            "created_edges": created_edges,  # ✅ FIX-4.1: Edges for Canvas
            "status": "completed",
            "result": result.data,
            "context_used": context_len > 0,  # Track if context was provided
            "images_processed": images_count,  # Track images processed
        }

    async def record_learning_episode(
        self,
        canvas_name: str,
        node_id: str,
        concept: str,
        user_understanding: Optional[str] = None,
        score: Optional[float] = None,
        agent_feedback: Optional[str] = None
    ) -> bool:
        """
        Record a learning episode to the memory system.

        This method should be called after any Agent analysis to track
        the user's learning progress over time.

        Args:
            canvas_name: Canvas file name
            node_id: Node ID that was analyzed
            concept: Concept name or summary
            user_understanding: User's answer or understanding text
            score: Score from scoring agent (0-40)
            agent_feedback: Feedback from the agent

        Returns:
            True if successfully recorded, False otherwise

        [Source: FIX-4.2 Agent调用时查询历史]
        """
        if not self._memory_client:
            logger.debug("Memory client not available, skipping episode recording")
            return False

        try:
            from app.clients.graphiti_client import LearningMemory

            memory = LearningMemory(
                canvas_name=canvas_name,
                node_id=node_id,
                concept=concept,
                user_understanding=user_understanding,
                score=score,
                agent_feedback=agent_feedback
            )

            success = await self._memory_client.add_learning_episode(memory)
            if success:
                logger.debug(f"Recorded learning episode: {canvas_name}/{node_id}")
            return success

        except Exception as e:
            logger.warning(f"Failed to record learning episode: {e}")
            return False

    async def cleanup(self) -> None:
        """
        Cleanup resources when service is no longer needed.

        Waits for all active calls to complete before cleanup.

        [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#依赖注入设计]
        """
        # Wait for active calls to complete
        while self._active_calls > 0:
            await asyncio.sleep(0.01)

        self._initialized = False
        logger.debug("AgentService cleanup completed")
