"""
Integration tests for Agent Memory Trigger Mechanism

Story 30.4: Agent Memory Write Trigger Mechanism
[Source: docs/stories/30.4.story.md]

Tests:
- Full agent execution flow triggers memory write
- Memory write persists to MemoryService (mock Neo4j)
- Concurrent agent executions with memory writes
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.agent_memory_mapping import (
    AGENT_MEMORY_MAPPING,
    ALL_AGENT_NAMES,
    AgentMemoryType,
    get_memory_type_for_agent,
)
from app.services.agent_service import AgentResult, AgentService, AgentType


class TestAgentMemoryIntegration:
    """Integration tests for agent memory trigger system."""

    @pytest.fixture
    def mock_memory_client(self):
        """Create a mock LearningMemoryClient."""
        client = AsyncMock()
        client.add_learning_episode = AsyncMock(return_value=True)
        client.search_memories = AsyncMock(return_value=[])
        client.format_for_context = MagicMock(return_value="")
        return client

    @pytest.fixture
    def mock_gemini_client(self):
        """Create a mock GeminiClient."""
        client = MagicMock()
        client.is_configured = MagicMock(return_value=True)
        client.call_agent = AsyncMock(return_value={"response": "Test response"})
        return client

    @pytest.fixture
    def agent_service(self, mock_gemini_client, mock_memory_client):
        """Create an AgentService with mocked dependencies."""
        service = AgentService(
            gemini_client=mock_gemini_client,
            memory_client=mock_memory_client,
            canvas_service=None,
            max_concurrent=10,
        )
        return service

    @pytest.mark.asyncio
    async def test_full_agent_execution_flow_triggers_memory_write(
        self, agent_service, mock_memory_client
    ):
        """Test that full agent execution triggers memory write (Task 6.1)."""
        # Trigger memory write directly (simulating post-agent execution)
        await agent_service._trigger_memory_write(
            agent_type="scoring-agent",
            canvas_name="test.canvas",
            node_id="node-001",
            concept="Integration test concept",
            score=85.0,
            agent_feedback="Test feedback",
        )

        # Wait for fire-and-forget task
        await asyncio.sleep(0.2)

        # Verify memory client was called
        mock_memory_client.add_learning_episode.assert_called_once()

    @pytest.mark.asyncio
    async def test_memory_write_persists_correct_data(
        self, agent_service, mock_memory_client
    ):
        """Test memory write persists to MemoryService with correct data (Task 6.2)."""
        # Trigger memory write
        await agent_service._trigger_memory_write(
            agent_type="four-level-explanation",
            canvas_name="math.canvas",
            node_id="node-math-001",
            concept="Quadratic equations",
            user_understanding="x = (-b ± √(b²-4ac)) / 2a",
            agent_feedback="Good understanding of the formula",
        )

        # Wait for fire-and-forget task
        await asyncio.sleep(0.2)

        # Verify the call was made with correct parameters
        call_args = mock_memory_client.add_learning_episode.call_args
        assert call_args is not None

        # The LearningMemory object should have correct fields
        memory_obj = call_args[0][0]
        assert memory_obj.canvas_name == "math.canvas"
        assert memory_obj.node_id == "node-math-001"
        assert memory_obj.concept == "Quadratic equations"

    @pytest.mark.asyncio
    async def test_concurrent_agent_executions_with_memory_writes(
        self, agent_service, mock_memory_client
    ):
        """Test concurrent agent executions with memory writes (Task 6.3)."""
        # Execute multiple agents concurrently
        agents_to_test = [
            ("scoring-agent", "concept1", 90.0),
            ("four-level-explanation", "concept2", None),
            ("deep-decomposition", "concept3", None),
            ("oral-explanation", "concept4", None),
            ("memory-anchor", "concept5", None),
        ]

        # Trigger all memory writes concurrently
        tasks = [
            agent_service._trigger_memory_write(
                agent_type=agent_type,
                canvas_name="test.canvas",
                node_id=f"node-{i}",
                concept=concept,
                score=score,
            )
            for i, (agent_type, concept, score) in enumerate(agents_to_test)
        ]

        # Wait for all triggers to start
        await asyncio.gather(*tasks)

        # Wait for fire-and-forget tasks to complete
        await asyncio.sleep(0.5)

        # All 5 agents should have triggered memory writes
        assert mock_memory_client.add_learning_episode.call_count == 5

    @pytest.mark.asyncio
    async def test_memory_client_unavailable_silent_degradation(self, mock_gemini_client):
        """Test silent degradation when memory client is unavailable."""
        # Create service without memory client
        service = AgentService(
            gemini_client=mock_gemini_client,
            memory_client=None,  # No memory client
            canvas_service=None,
            max_concurrent=10,
        )

        # Should not raise exception even without memory client
        await service._trigger_memory_write(
            agent_type="scoring-agent",
            canvas_name="test.canvas",
            node_id="node-001",
            concept="Test concept",
        )

        # Wait for any async operations
        await asyncio.sleep(0.1)

        # No exception means silent degradation worked

    @pytest.mark.asyncio
    async def test_memory_write_does_not_block_concurrent_operations(
        self, agent_service, mock_memory_client
    ):
        """Test that memory writes don't block other operations."""
        import time

        # Make memory write slow
        async def slow_add_episode(memory):
            await asyncio.sleep(0.3)
            return True

        mock_memory_client.add_learning_episode = slow_add_episode

        # Start memory write
        start = time.time()

        # Trigger multiple memory writes
        await asyncio.gather(
            agent_service._trigger_memory_write(
                agent_type="scoring-agent",
                canvas_name="test.canvas",
                node_id="node-001",
                concept="Concept 1",
            ),
            agent_service._trigger_memory_write(
                agent_type="four-level-explanation",
                canvas_name="test.canvas",
                node_id="node-002",
                concept="Concept 2",
            ),
            agent_service._trigger_memory_write(
                agent_type="deep-decomposition",
                canvas_name="test.canvas",
                node_id="node-003",
                concept="Concept 3",
            ),
        )

        duration = time.time() - start

        # All triggers should return immediately (fire-and-forget)
        # Not waiting for the slow memory writes
        assert duration < 0.1, f"Triggers took {duration}s, expected < 0.1s"


class TestAgentTypeMapping:
    """Tests to verify agent type mapping completeness."""

    def test_all_agent_types_have_memory_mapping(self):
        """Verify that the agent types defined in AgentType enum can map to memory types."""
        # Get agent names from AgentType enum (excluding aliases)
        agent_type_names = {
            AgentType.BASIC_DECOMPOSITION.value,
            AgentType.DEEP_DECOMPOSITION.value,
            AgentType.QUESTION_DECOMPOSITION.value,
            AgentType.ORAL_EXPLANATION.value,
            AgentType.FOUR_LEVEL_EXPLANATION.value,
            AgentType.CLARIFICATION_PATH.value,
            AgentType.COMPARISON_TABLE.value,
            AgentType.EXAMPLE_TEACHING.value,
            AgentType.MEMORY_ANCHOR.value,
            AgentType.SCORING_AGENT.value,
            AgentType.VERIFICATION_QUESTION.value,
            AgentType.CANVAS_ORCHESTRATOR.value,
        }

        # Check that all these agents have memory type mappings
        for agent_name in agent_type_names:
            memory_type = get_memory_type_for_agent(agent_name)
            assert (
                memory_type is not None
            ), f"AgentType {agent_name} has no memory mapping"

    def test_decomposition_agents_map_to_decomposition_type(self):
        """Test that decomposition agents map to decomposition_completed."""
        decomposition_agents = [
            "basic-decomposition",
            "deep-decomposition",
            "question-decomposition",
        ]
        for agent in decomposition_agents:
            memory_type = get_memory_type_for_agent(agent)
            assert memory_type == AgentMemoryType.DECOMPOSITION_COMPLETED

    def test_explanation_agents_map_to_explanation_type(self):
        """Test that explanation agents map to explanation_generated."""
        explanation_agents = [
            "four-level-explanation",
            "oral-explanation",
            "example-teaching",
            "clarification-path",
            "comparison-table",
            "verification-question-agent",
        ]
        for agent in explanation_agents:
            memory_type = get_memory_type_for_agent(agent)
            assert memory_type == AgentMemoryType.EXPLANATION_GENERATED

    def test_scoring_agent_maps_to_scoring_type(self):
        """Test that scoring-agent maps to scoring_completed."""
        memory_type = get_memory_type_for_agent("scoring-agent")
        assert memory_type == AgentMemoryType.SCORING_COMPLETED

    def test_memory_anchor_maps_to_node_created(self):
        """Test that memory-anchor maps to node_created."""
        memory_type = get_memory_type_for_agent("memory-anchor")
        assert memory_type == AgentMemoryType.NODE_CREATED

    def test_canvas_orchestrator_maps_to_canvas_opened(self):
        """Test that canvas-orchestrator maps to canvas_opened."""
        memory_type = get_memory_type_for_agent("canvas-orchestrator")
        assert memory_type == AgentMemoryType.CANVAS_OPENED

    def test_system_agents_map_to_concept_reviewed(self):
        """Test that system agents map to concept_reviewed."""
        system_agents = ["review-board-agent-selector", "graphiti-memory-agent"]
        for agent in system_agents:
            memory_type = get_memory_type_for_agent(agent)
            assert memory_type == AgentMemoryType.CONCEPT_REVIEWED
