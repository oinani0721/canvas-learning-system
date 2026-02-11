# Canvas Learning System - Story 30.22 Tests
# Agent 触发深度测试 (映射表 → 行为验证)
"""
Story 30.22 - Agent Trigger Deep Behavior Tests

Task 1: Agent trigger behavior verification with parameter validation (AC-30.22.1)
Task 2: Degradation tests with logger.warning verification (AC-30.22.2)
Task 3: Episode structure completeness and determinism (AC-30.22.3)

Difference from Story 30.14:
- 30.14 verifies mapping table existence + assert_called_once()
- 30.22 verifies actual call PARAMETERS (LearningMemory fields) + logger content + episode structure

[Source: docs/stories/30.22.agent-trigger-deep-test.story.md]
"""

import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.clients.graphiti_client import LearningMemory
from app.core.agent_memory_mapping import (
    AGENT_MEMORY_MAPPING,
    AgentMemoryType,
    get_memory_type_for_agent,
)

# All 15 agents from the mapping
ALL_AGENTS = list(AGENT_MEMORY_MAPPING.keys())


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_gemini_client():
    client = MagicMock()
    client.call_agent = AsyncMock(return_value="mock agent response")
    return client


@pytest.fixture
def mock_memory_client():
    client = MagicMock()
    client.add_learning_episode = AsyncMock(return_value=True)
    return client


@pytest.fixture
def agent_service(mock_gemini_client, mock_memory_client):
    from app.services.agent_service import AgentService
    service = AgentService(
        gemini_client=mock_gemini_client,
        memory_client=mock_memory_client,
    )
    return service


# ============================================================================
# Task 1: Behavior Verification Tests (AC-30.22.1)
# ============================================================================

class TestAgentTriggerBehavior:
    """AC-30.22.1: Verify _trigger_memory_write calls add_learning_episode
    with correct LearningMemory parameters for each AgentType."""

    @pytest.mark.parametrize("agent_name", ALL_AGENTS)
    @pytest.mark.asyncio
    async def test_trigger_passes_correct_canvas_name(
        self, agent_service, mock_memory_client, agent_name, wait_for_call
    ):
        """_trigger_memory_write passes correct canvas_name to LearningMemory."""
        await agent_service._trigger_memory_write(
            agent_type=agent_name,
            canvas_name="math/calculus.canvas",
            node_id="node_001",
            concept="Derivative",
        )

        await wait_for_call(mock_memory_client.add_learning_episode)

        mock_memory_client.add_learning_episode.assert_called_once()
        memory_arg = mock_memory_client.add_learning_episode.call_args[0][0]
        assert isinstance(memory_arg, LearningMemory)
        assert memory_arg.canvas_name == "math/calculus.canvas"

    @pytest.mark.parametrize("agent_name", ALL_AGENTS)
    @pytest.mark.asyncio
    async def test_trigger_passes_correct_concept(
        self, agent_service, mock_memory_client, agent_name, wait_for_call
    ):
        """_trigger_memory_write passes correct concept to LearningMemory."""
        await agent_service._trigger_memory_write(
            agent_type=agent_name,
            canvas_name="test.canvas",
            node_id="node_002",
            concept="Integration by Parts",
        )

        await wait_for_call(mock_memory_client.add_learning_episode)

        memory_arg = mock_memory_client.add_learning_episode.call_args[0][0]
        assert memory_arg.concept == "Integration by Parts"

    @pytest.mark.parametrize("agent_name", ALL_AGENTS)
    @pytest.mark.asyncio
    async def test_trigger_passes_correct_node_id(
        self, agent_service, mock_memory_client, agent_name, wait_for_call
    ):
        """_trigger_memory_write passes correct node_id to LearningMemory."""
        await agent_service._trigger_memory_write(
            agent_type=agent_name,
            canvas_name="test.canvas",
            node_id="node_xyz_123",
            concept="Test",
        )

        await wait_for_call(mock_memory_client.add_learning_episode)

        memory_arg = mock_memory_client.add_learning_episode.call_args[0][0]
        assert memory_arg.node_id == "node_xyz_123"

    @pytest.mark.parametrize("agent_name", ALL_AGENTS)
    @pytest.mark.asyncio
    async def test_trigger_passes_all_fields_non_empty(
        self, agent_service, mock_memory_client, agent_name, wait_for_call
    ):
        """LearningMemory has non-empty canvas_name, node_id, concept for every agent."""
        await agent_service._trigger_memory_write(
            agent_type=agent_name,
            canvas_name="physics/mechanics.canvas",
            node_id="n_001",
            concept="Newton's Laws",
            user_understanding="F=ma is the second law",
        )

        await wait_for_call(mock_memory_client.add_learning_episode)

        memory_arg = mock_memory_client.add_learning_episode.call_args[0][0]
        assert memory_arg.canvas_name, "canvas_name must be non-empty"
        assert memory_arg.node_id, "node_id must be non-empty"
        assert memory_arg.concept, "concept must be non-empty"


# ============================================================================
# Task 2: Degradation Tests (AC-30.22.2)
# ============================================================================

class TestTriggerDegradation:
    """AC-30.22.2: Verify fire-and-forget degradation and logger.warning."""

    @pytest.mark.asyncio
    async def test_trigger_with_none_memory_client_no_crash(self):
        """memory_client=None: _trigger_memory_write does not raise, logs degradation."""
        from app.services.agent_service import AgentService

        service = AgentService(
            gemini_client=MagicMock(),
            memory_client=None,
        )

        # Should not raise for any mapped agent; verify degradation is logged
        with patch("app.services.agent_service.logger") as mock_logger:
            await service._trigger_memory_write(
                agent_type="scoring-agent",
                canvas_name="test.canvas",
                node_id="node_001",
                concept="Test Concept",
            )

            from tests.conftest import yield_to_event_loop
            await yield_to_event_loop(10)

            # record_learning_episode logs debug when memory_client is None
            debug_calls = [str(c) for c in mock_logger.debug.call_args_list]
            assert any(
                "Memory client not available" in c for c in debug_calls
            ), f"Expected 'Memory client not available' debug log, got: {debug_calls}"

    @pytest.mark.asyncio
    async def test_trigger_with_exception_in_add_episode_no_crash(
        self, agent_service, mock_memory_client, wait_for_call
    ):
        """add_learning_episode raises exception: _trigger_memory_write does not crash."""
        mock_memory_client.add_learning_episode = AsyncMock(
            side_effect=Exception("Database connection lost")
        )

        # Should not raise
        await agent_service._trigger_memory_write(
            agent_type="basic-decomposition",
            canvas_name="test.canvas",
            node_id="node_001",
            concept="Test Concept",
        )

        # Wait for fire-and-forget to complete
        await wait_for_call(mock_memory_client.add_learning_episode)

    @pytest.mark.asyncio
    async def test_trigger_warning_contains_agent_type_on_outer_failure(
        self, mock_gemini_client, mock_memory_client
    ):
        """When record_learning_episode raises, logger.warning includes agent_type."""
        from app.services.agent_service import AgentService

        service = AgentService(
            gemini_client=mock_gemini_client,
            memory_client=mock_memory_client,
        )

        # Patch record_learning_episode to raise — triggers _write_with_timeout's except
        service.record_learning_episode = AsyncMock(
            side_effect=RuntimeError("Unexpected failure")
        )

        with patch("app.services.agent_service.logger") as mock_logger:
            await service._trigger_memory_write(
                agent_type="deep-decomposition",
                canvas_name="test.canvas",
                node_id="node_001",
                concept="Test Concept",
            )

            # Wait for fire-and-forget task to complete (robust condition-based wait)
            from tests.conftest import wait_for_condition
            await wait_for_condition(
                lambda: mock_logger.warning.called,
                description="logger.warning called after fire-and-forget failure",
                timeout=5.0,
            )

            # _write_with_timeout logs: "Memory write failed for {agent_type}: {e}"
            warning_calls = [
                str(call) for call in mock_logger.warning.call_args_list
            ]
            assert any(
                "deep-decomposition" in call for call in warning_calls
            ), f"logger.warning should contain agent_type 'deep-decomposition', got: {warning_calls}"


# ============================================================================
# Task 3: Episode Structure Completeness (AC-30.22.3)
# ============================================================================

class TestEpisodeStructure:
    """AC-30.22.3: Verify LearningMemory (episode) structure completeness."""

    @pytest.mark.asyncio
    async def test_episode_structure_has_required_fields(
        self, agent_service, mock_memory_client, wait_for_call
    ):
        """LearningMemory passed to add_learning_episode has all required fields."""
        await agent_service._trigger_memory_write(
            agent_type="scoring-agent",
            canvas_name="biology/genetics.canvas",
            node_id="node_gene_001",
            concept="DNA Replication",
            user_understanding="Leading and lagging strand",
            score=0.85,
            agent_feedback="Good grasp of basic mechanism",
        )

        await wait_for_call(mock_memory_client.add_learning_episode)

        memory_arg = mock_memory_client.add_learning_episode.call_args[0][0]
        assert isinstance(memory_arg, LearningMemory)

        # Required fields (non-empty)
        assert memory_arg.canvas_name == "biology/genetics.canvas"
        assert memory_arg.node_id == "node_gene_001"
        assert memory_arg.concept == "DNA Replication"

        # Optional fields (passed through correctly)
        assert memory_arg.user_understanding == "Leading and lagging strand"
        assert memory_arg.score == 0.85
        assert memory_arg.agent_feedback == "Good grasp of basic mechanism"

    def test_episode_memory_key_determinism(self):
        """Same inputs produce same memory_key (episode_id equivalent)."""
        m1 = LearningMemory(
            canvas_name="test.canvas",
            node_id="node_001",
            concept="Test",
            timestamp="2026-02-10T10:00:00",
        )
        m2 = LearningMemory(
            canvas_name="test.canvas",
            node_id="node_001",
            concept="Test",
            timestamp="2026-02-10T10:00:00",
        )

        assert m1.memory_key == m2.memory_key
        assert m1.memory_key != ""

    def test_episode_memory_key_differs_for_different_inputs(self):
        """Different inputs produce different memory_keys."""
        m1 = LearningMemory(
            canvas_name="test.canvas",
            node_id="node_001",
            concept="Test",
            timestamp="2026-02-10T10:00:00",
        )
        m2 = LearningMemory(
            canvas_name="test.canvas",
            node_id="node_002",
            concept="Test",
            timestamp="2026-02-10T10:00:00",
        )

        assert m1.memory_key != m2.memory_key

    @pytest.mark.asyncio
    async def test_unmapped_agent_skips_write(
        self, agent_service, mock_memory_client
    ):
        """Unmapped agent_name causes _trigger_memory_write to early-return (no write)."""
        await agent_service._trigger_memory_write(
            agent_type="nonexistent-agent-xyz",
            canvas_name="test.canvas",
            node_id="node_001",
            concept="Test",
        )

        from tests.conftest import yield_to_event_loop
        await yield_to_event_loop(10)

        mock_memory_client.add_learning_episode.assert_not_called()

    def test_memory_key_with_auto_timestamp(self):
        """When timestamp is None, memory_key uses datetime.now() and is valid ISO 8601."""
        m = LearningMemory(
            canvas_name="test.canvas",
            node_id="node_001",
            concept="Test",
            timestamp=None,
        )

        assert m.memory_key, "memory_key must be non-empty even with timestamp=None"
        parts = m.memory_key.split(":")
        assert len(parts) >= 3
        # Rejoin from index 2: timestamp in ISO 8601 contains colons
        timestamp_str = ":".join(parts[2:])
        from datetime import datetime as dt
        try:
            dt.fromisoformat(timestamp_str)
        except ValueError:
            pytest.fail(f"Auto-generated timestamp '{timestamp_str}' is not valid ISO 8601")

    @pytest.mark.asyncio
    async def test_episode_timestamp_field_present(
        self, agent_service, mock_memory_client, wait_for_call
    ):
        """LearningMemory.timestamp is set (or None for auto-generation)."""
        await agent_service._trigger_memory_write(
            agent_type="oral-explanation",
            canvas_name="test.canvas",
            node_id="node_001",
            concept="Test",
        )

        await wait_for_call(mock_memory_client.add_learning_episode)

        memory_arg = mock_memory_client.add_learning_episode.call_args[0][0]
        # memory_key always produces a non-empty string (uses datetime.now if timestamp is None)
        assert memory_arg.memory_key, "memory_key (episode_id) must be non-empty"
        # canvas_name:node_id:timestamp format — ISO 8601 timestamps contain colons
        parts = memory_arg.memory_key.split(":")
        assert len(parts) >= 3, f"memory_key should have at least 3 parts, got: {memory_arg.memory_key}"
        # AC-30.22.3: Validate timestamp portion is ISO 8601 format
        timestamp_str = ":".join(parts[2:])
        from datetime import datetime as dt
        try:
            dt.fromisoformat(timestamp_str)
        except ValueError:
            pytest.fail(f"timestamp portion '{timestamp_str}' is not valid ISO 8601 format")
