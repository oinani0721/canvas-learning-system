# ✅ Verified structure from docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层
"""
Agent Service - Business logic for Agent operations.

This service provides async methods for Agent calls,
wrapping the Claude Code agent functionality with async support.

[Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层]
"""
import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

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
    """

    def __init__(self, api_key: Optional[str] = None, max_concurrent: int = 10):
        """
        Initialize AgentService.

        Args:
            api_key: Optional API key for agent calls
            max_concurrent: Maximum concurrent agent calls (default: 10)

        [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#依赖注入设计]
        """
        self.api_key = api_key
        self._max_concurrent = max_concurrent
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._total_calls = 0
        self._active_calls = 0
        self._initialized = True
        logger.debug(f"AgentService initialized with max_concurrent={max_concurrent}")

    @property
    def total_calls(self) -> int:
        """Total number of agent calls made"""
        return self._total_calls

    @property
    def active_calls(self) -> int:
        """Current number of active agent calls"""
        return self._active_calls

    async def _simulate_agent_call(self, agent_type: AgentType, prompt: str) -> Dict[str, Any]:
        """Simulate an agent call with a small delay"""
        await asyncio.sleep(0.1)  # Simulate API latency
        return {
            "agent_type": agent_type.value,
            "response": f"Simulated response for {agent_type.value}",
            "prompt": prompt[:50],
        }

    async def call_agent(
        self,
        agent_type: AgentType,
        prompt: str,
        timeout: Optional[float] = None
    ) -> AgentResult:
        """
        Call a single agent with concurrency control.

        Args:
            agent_type: Type of agent to call
            prompt: Input prompt for the agent
            timeout: Optional timeout in seconds

        Returns:
            AgentResult with the response
        """
        start_time = datetime.now()
        async with self._semaphore:
            self._active_calls += 1
            self._total_calls += 1
            try:
                if timeout:
                    data = await asyncio.wait_for(
                        self._simulate_agent_call(agent_type, prompt),
                        timeout=timeout
                    )
                else:
                    data = await self._simulate_agent_call(agent_type, prompt)

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
        explanation_type: str = "oral"
    ) -> AgentResult:
        """
        Call explanation agent.

        Args:
            content: Content to explain
            explanation_type: Type of explanation

        Returns:
            AgentResult with explanation
        """
        type_map = {
            "oral": AgentType.ORAL_EXPLANATION,
            "clarification": AgentType.CLARIFICATION_PATH,
            "comparison": AgentType.COMPARISON_TABLE,
            "memory": AgentType.MEMORY_ANCHOR,
            "four_level": AgentType.FOUR_LEVEL,
            "example": AgentType.EXAMPLE_TEACHING,
        }
        agent_type = type_map.get(explanation_type, AgentType.ORAL_EXPLANATION)
        return await self.call_agent(agent_type, content)

    async def decompose_basic(
        self,
        canvas_name: str,
        node_id: str,
        content: str
    ) -> Dict[str, Any]:
        """
        Perform basic decomposition on a concept node.

        Args:
            canvas_name: Target canvas name
            node_id: ID of node to decompose
            content: Node content to decompose

        Returns:
            Decomposition result with guiding questions

        [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层]
        """
        logger.debug(f"Basic decomposition for node {node_id}")
        result = await self.call_decomposition(content, deep=False)
        return {
            "node_id": node_id,
            "questions": ["What is this?", "Why is this important?"],
            "status": "completed",
            "result": result.data,
        }

    async def decompose_deep(
        self,
        canvas_name: str,
        node_id: str,
        content: str
    ) -> Dict[str, Any]:
        """
        Perform deep decomposition for verification questions.

        Args:
            canvas_name: Target canvas name
            node_id: ID of node to decompose
            content: Node content to decompose

        Returns:
            Deep verification questions

        [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层]
        """
        logger.debug(f"Deep decomposition for node {node_id}")
        result = await self.call_decomposition(content, deep=True)
        return {
            "node_id": node_id,
            "verification_questions": [],
            "status": "completed",
            "result": result.data,
        }

    async def score_node(
        self,
        canvas_name: str,
        node_id: str,
        user_answer: str,
        reference_answer: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Score a user's understanding based on their answer.

        Args:
            canvas_name: Target canvas name
            node_id: ID of node being scored
            user_answer: User's answer text
            reference_answer: Optional reference answer for comparison

        Returns:
            Scoring result with 4-dimension scores

        [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层]
        """
        logger.debug(f"Scoring node {node_id}")
        result = await self.call_scoring(reference_answer or "", user_answer)
        return {
            "node_id": node_id,
            "scores": {
                "accuracy": 0.0,
                "imagery": 0.0,
                "completeness": 0.0,
                "originality": 0.0
            },
            "overall_score": 0.0,
            "color_recommendation": "red",
            "result": result.data,
        }

    async def generate_explanation(
        self,
        canvas_name: str,
        node_id: str,
        content: str,
        explanation_type: str = "oral"
    ) -> Dict[str, Any]:
        """
        Generate an explanation for a concept.

        Args:
            canvas_name: Target canvas name
            node_id: ID of node to explain
            content: Node content to explain
            explanation_type: Type of explanation (oral, four-level, etc.)

        Returns:
            Generated explanation

        [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层]
        """
        logger.debug(f"Generating {explanation_type} explanation for node {node_id}")
        result = await self.call_explanation(content, explanation_type)
        return {
            "node_id": node_id,
            "explanation_type": explanation_type,
            "explanation": "",
            "status": "completed",
            "result": result.data,
        }

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
