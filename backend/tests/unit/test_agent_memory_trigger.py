"""
Unit tests for Agent Memory Trigger Mechanism

Story 30.4: Agent Memory Write Trigger Mechanism
[Source: docs/stories/30.4.story.md]

Tests:
- Agent memory mapping returns correct types
- _trigger_memory_write() is called after agent completion
- Async write doesn't block agent response
- Silent degradation on memory write failure
- All 14 agents trigger appropriate memory types
"""

from unittest.mock import AsyncMock

import pytest

# Story 30.4: Test agent memory mapping module
from app.core.agent_memory_mapping import (
    AGENT_MEMORY_MAPPING,
    ALL_AGENT_NAMES,
    AgentMemoryType,
    get_memory_type_for_agent,
    is_memory_enabled_agent,
)

from tests.conftest import simulate_async_delay, wait_for_condition, yield_to_event_loop


class TestAgentMemoryMapping:
    """Tests for agent_memory_mapping.py (Task 1, AC-30.4.4)"""

    def test_agent_memory_type_enum_has_all_required_types(self):
        """Test that AgentMemoryType enum has all required event types."""
        expected_types = {
            "decomposition_completed",
            "scoring_completed",
            "explanation_generated",
            "review_canvas_created",
            "concept_reviewed",
            "canvas_opened",
            "node_created",
            "node_updated",
        }
        actual_types = {e.value for e in AgentMemoryType}
        assert expected_types == actual_types

    def test_all_14_agents_are_mapped(self):
        """Test that every mapped agent has a memory type (now 15, was 14).

        契约演进 1a4f42ae (2026-02-09 "TTLCache for agent memory, inject memory_client
        into VS AgentService")：该 commit 往 AGENT_MEMORY_MAPPING 补了第 15 个条目
        `"hint-generation": AgentMemoryType.EXPLANATION_GENERATED`（生产行内注释自述
        "Story 30.12 fix: was missing, trigger in verification_service.py"）——
        提示生成本来就在触发记忆写入，只是漏登记，补齐是修漏不是扩面。
        ⛔ 函数名保留 `_14_` 不改：改名 = nodeid 变化 = 这条红「消失」而非「转绿」，
           名实不符已登记进台账，留给专门的重命名卡处理。[CARD-RED-C2]
        """
        # 判据强度提升：原断言只数个数，等长替换（删一个补一个）照样能过。
        # 改为锁**身份**——键集必须逐字等于下面这份抄写的字面量（不 import 生产常量，
        # import 当期望值就是自证）。任何增/删/改名都会红。
        expected_agents = {
            "basic-decomposition",
            "deep-decomposition",
            "question-decomposition",
            "four-level-explanation",
            "oral-explanation",
            "example-teaching",
            "clarification-path",
            "comparison-table",
            "verification-question-agent",
            "hint-generation",
            "scoring-agent",
            "memory-anchor",
            "canvas-orchestrator",
            "review-board-agent-selector",
            "graphiti-memory-agent",
        }
        assert len(expected_agents) == 15, "字面量完整性守卫：重复串会让集合悄悄缩小"
        assert set(AGENT_MEMORY_MAPPING.keys()) == expected_agents
        assert ALL_AGENT_NAMES == expected_agents

    def test_expected_agents_are_in_mapping(self):
        """Test that expected agent names are in the mapping."""
        expected_agents = [
            "scoring-agent",
            "four-level-explanation",
            "verification-question-agent",
            "oral-explanation",
            "example-teaching",
            "deep-decomposition",
            "comparison-table",
            "memory-anchor",
            "clarification-path",
            "basic-decomposition",
            "question-decomposition",
            "canvas-orchestrator",
            "review-board-agent-selector",
            "graphiti-memory-agent",
        ]
        for agent in expected_agents:
            assert agent in AGENT_MEMORY_MAPPING, f"Missing agent: {agent}"

    @pytest.mark.parametrize(
        "agent_name,expected_type",
        [
            ("scoring-agent", AgentMemoryType.SCORING_COMPLETED),
            ("four-level-explanation", AgentMemoryType.EXPLANATION_GENERATED),
            ("verification-question-agent", AgentMemoryType.EXPLANATION_GENERATED),
            ("oral-explanation", AgentMemoryType.EXPLANATION_GENERATED),
            ("example-teaching", AgentMemoryType.EXPLANATION_GENERATED),
            ("deep-decomposition", AgentMemoryType.DECOMPOSITION_COMPLETED),
            ("comparison-table", AgentMemoryType.EXPLANATION_GENERATED),
            ("memory-anchor", AgentMemoryType.NODE_CREATED),
            ("clarification-path", AgentMemoryType.EXPLANATION_GENERATED),
            ("basic-decomposition", AgentMemoryType.DECOMPOSITION_COMPLETED),
            ("question-decomposition", AgentMemoryType.DECOMPOSITION_COMPLETED),
            ("canvas-orchestrator", AgentMemoryType.CANVAS_OPENED),
            ("review-board-agent-selector", AgentMemoryType.CONCEPT_REVIEWED),
            ("graphiti-memory-agent", AgentMemoryType.CONCEPT_REVIEWED),
        ],
    )
    def test_get_memory_type_for_agent_returns_correct_type(
        self, agent_name: str, expected_type: AgentMemoryType
    ):
        """Test that get_memory_type_for_agent returns correct type for each agent."""
        result = get_memory_type_for_agent(agent_name)
        assert result == expected_type

    def test_get_memory_type_for_unknown_agent_returns_none(self):
        """Test that unknown agents return None."""
        result = get_memory_type_for_agent("unknown-agent")
        assert result is None

    def test_is_memory_enabled_agent_true_for_mapped_agents(self):
        """Test is_memory_enabled_agent returns True for mapped agents."""
        assert is_memory_enabled_agent("scoring-agent") is True
        assert is_memory_enabled_agent("four-level-explanation") is True

    def test_is_memory_enabled_agent_false_for_unknown_agents(self):
        """Test is_memory_enabled_agent returns False for unknown agents."""
        assert is_memory_enabled_agent("unknown-agent") is False
        assert is_memory_enabled_agent("") is False


class TestTriggerMemoryWrite:
    """Tests for _trigger_memory_write() method (Tasks 2, 3, 4)"""

    @pytest.fixture
    def mock_agent_service(self):
        """Create a mock AgentService for testing."""
        from app.services.agent_service import AgentService

        # Create service with mocked dependencies
        service = AgentService(
            gemini_client=None,
            memory_client=AsyncMock(),
            canvas_service=None,
            max_concurrent=10,
        )
        # Mock record_learning_episode
        service.record_learning_episode = AsyncMock(return_value=True)
        return service

    @pytest.mark.asyncio
    async def test_trigger_memory_write_calls_record_learning_episode(
        self, mock_agent_service, wait_for_call
    ):
        """Test that _trigger_memory_write calls record_learning_episode."""
        await mock_agent_service._trigger_memory_write(
            agent_type="scoring-agent",
            canvas_name="test.canvas",
            node_id="node-001",
            concept="Test concept",
        )

        # Poll until the fire-and-forget task completes
        await wait_for_call(mock_agent_service.record_learning_episode)

        mock_agent_service.record_learning_episode.assert_called_once()

    @pytest.mark.asyncio
    async def test_trigger_memory_write_skips_unmapped_agent(self, mock_agent_service):
        """Test that _trigger_memory_write skips agents not in mapping."""
        await mock_agent_service._trigger_memory_write(
            agent_type="unknown-agent",
            canvas_name="test.canvas",
            node_id="node-001",
            concept="Test concept",
        )

        await yield_to_event_loop()

        # Should not call record_learning_episode for unmapped agents
        mock_agent_service.record_learning_episode.assert_not_called()

    @pytest.mark.asyncio
    async def test_trigger_memory_write_is_non_blocking(self, mock_agent_service):
        """Test that _trigger_memory_write returns immediately (AC-30.4.2)."""
        import time

        # Make record_learning_episode take 50ms
        async def slow_record(*args, **kwargs):
            await simulate_async_delay(0.05)
            return True

        mock_agent_service.record_learning_episode = slow_record

        start = time.time()
        await mock_agent_service._trigger_memory_write(
            agent_type="scoring-agent",
            canvas_name="test.canvas",
            node_id="node-001",
            concept="Test concept",
        )
        duration = time.time() - start

        # Should return immediately, not wait for the 200ms
        assert duration < 0.1, f"Method took {duration}s, expected < 0.1s"

    @pytest.mark.asyncio
    async def test_trigger_memory_write_silent_degradation_on_timeout(
        self, mock_agent_service
    ):
        """Test silent degradation when memory write times out (AC-30.4.3)."""

        # Make record_learning_episode take longer than 100ms timeout
        async def very_slow_record(*args, **kwargs):
            await simulate_async_delay(0.15)
            return True

        mock_agent_service.record_learning_episode = very_slow_record

        # Should not raise exception
        await mock_agent_service._trigger_memory_write(
            agent_type="scoring-agent",
            canvas_name="test.canvas",
            node_id="node-001",
            concept="Test concept",
        )

        # Wait for fire-and-forget timeout to complete (poll instead of hard sleep)
        await wait_for_condition(
            lambda: True,  # just yield to event loop until timeout
            timeout=0.6,
            description="memory write timeout",
        )

        # No exception should be raised - silent degradation

    @pytest.mark.asyncio
    async def test_trigger_memory_write_silent_degradation_on_exception(
        self, mock_agent_service
    ):
        """Test silent degradation when memory write raises exception (AC-30.4.3)."""

        # Make record_learning_episode raise an exception
        mock_agent_service.record_learning_episode = AsyncMock(
            side_effect=Exception("Database connection failed")
        )

        # Should not raise exception
        await mock_agent_service._trigger_memory_write(
            agent_type="scoring-agent",
            canvas_name="test.canvas",
            node_id="node-001",
            concept="Test concept",
        )

        # Yield control to let the fire-and-forget task run
        await yield_to_event_loop()

        # No exception should be raised - silent degradation

    @pytest.mark.asyncio
    async def test_trigger_memory_write_passes_all_parameters(
        self, mock_agent_service, wait_for_call
    ):
        """Test that all parameters are passed to record_learning_episode."""
        await mock_agent_service._trigger_memory_write(
            agent_type="scoring-agent",
            canvas_name="test.canvas",
            node_id="node-001",
            concept="Test concept",
            user_understanding="User's understanding",
            score=85.5,
            agent_feedback="Good understanding",
        )

        await wait_for_call(mock_agent_service.record_learning_episode)

        mock_agent_service.record_learning_episode.assert_called_once_with(
            canvas_name="test.canvas",
            node_id="node-001",
            concept="Test concept",
            user_understanding="User's understanding",
            score=85.5,
            agent_feedback="Good understanding",
        )


class TestAllAgentsTriggerMemoryWrite:
    """Test that all 14 agents trigger appropriate memory types (Task 5.5)"""

    @pytest.mark.parametrize("agent_name", ALL_AGENT_NAMES)
    def test_each_agent_has_valid_memory_type(self, agent_name: str):
        """Test that each agent has a valid AgentMemoryType assigned."""
        memory_type = get_memory_type_for_agent(agent_name)
        assert memory_type is not None, f"Agent {agent_name} has no memory type"
        assert isinstance(memory_type, AgentMemoryType), (
            f"Agent {agent_name} memory type is not AgentMemoryType"
        )

    def test_memory_types_align_with_schema(self):
        """Test that all memory types align with temporal-event.schema.json."""
        # Valid event types from temporal-event.schema.json
        valid_schema_types = {
            "decomposition_completed",
            "scoring_completed",
            "explanation_generated",
            "review_canvas_created",
            "concept_reviewed",
            "canvas_opened",
            "node_created",
            "node_updated",
        }

        for agent_name in ALL_AGENT_NAMES:
            memory_type = get_memory_type_for_agent(agent_name)
            assert memory_type.value in valid_schema_types, (
                f"Agent {agent_name} has invalid memory type: {memory_type.value}"
            )
