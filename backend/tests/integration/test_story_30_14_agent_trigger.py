# Canvas Learning System - Story 30.14 Tests
# 14 Agent 触发集成测试
"""
Story 30.14 - Agent Memory Trigger Integration Tests

Task 1: Parametrized agent trigger tests (AC-30.14.1)
Task 2: Agent failure degradation tests (AC-30.14.2)
Task 3: Mapping completeness static analysis tests (AC-30.14.3)

[Source: docs/stories/30.14.test-agent-trigger-integration.story.md]
"""

import re
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.agent_memory_mapping import (
    AGENT_MEMORY_MAPPING,
    AgentMemoryType,
    ALL_AGENT_NAMES,
    get_memory_type_for_agent,
    is_memory_enabled_agent,
)
from app.services.agent_service import AgentType


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
# Task 1: Parametrized Agent Trigger Tests (AC-30.14.1)
# ============================================================================

# All 14 agents from the mapping
ALL_AGENTS = list(AGENT_MEMORY_MAPPING.keys())


class TestAgentMemoryMapping:
    """AC-30.14.1: Parametrized tests for AGENT_MEMORY_MAPPING."""

    def test_mapping_has_15_agents(self):
        """AGENT_MEMORY_MAPPING contains exactly 15 agents (C1 fix: +hint-generation)."""
        assert len(AGENT_MEMORY_MAPPING) == 15

    @pytest.mark.parametrize("agent_name", ALL_AGENTS)
    def test_get_memory_type_returns_valid_type(self, agent_name):
        """get_memory_type_for_agent returns a valid AgentMemoryType for each mapped agent."""
        result = get_memory_type_for_agent(agent_name)
        assert result is not None, f"Agent {agent_name} not found in mapping"
        assert isinstance(result, AgentMemoryType)

    @pytest.mark.parametrize("agent_name", ALL_AGENTS)
    def test_is_memory_enabled(self, agent_name):
        """is_memory_enabled_agent returns True for each mapped agent."""
        assert is_memory_enabled_agent(agent_name) is True

    def test_unmapped_agent_returns_none(self):
        """Unmapped agent name returns None."""
        assert get_memory_type_for_agent("nonexistent-agent") is None

    def test_unmapped_agent_not_enabled(self):
        """Unmapped agent returns False for is_memory_enabled."""
        assert is_memory_enabled_agent("nonexistent-agent") is False

    @pytest.mark.parametrize("agent_name,expected_type", [
        ("basic-decomposition", AgentMemoryType.DECOMPOSITION_COMPLETED),
        ("deep-decomposition", AgentMemoryType.DECOMPOSITION_COMPLETED),
        ("question-decomposition", AgentMemoryType.DECOMPOSITION_COMPLETED),
        ("scoring-agent", AgentMemoryType.SCORING_COMPLETED),
        ("four-level-explanation", AgentMemoryType.EXPLANATION_GENERATED),
        ("oral-explanation", AgentMemoryType.EXPLANATION_GENERATED),
        ("example-teaching", AgentMemoryType.EXPLANATION_GENERATED),
        ("clarification-path", AgentMemoryType.EXPLANATION_GENERATED),
        ("comparison-table", AgentMemoryType.EXPLANATION_GENERATED),
        ("verification-question-agent", AgentMemoryType.EXPLANATION_GENERATED),
        ("memory-anchor", AgentMemoryType.NODE_CREATED),
        ("canvas-orchestrator", AgentMemoryType.CANVAS_OPENED),
        ("review-board-agent-selector", AgentMemoryType.CONCEPT_REVIEWED),
        ("graphiti-memory-agent", AgentMemoryType.CONCEPT_REVIEWED),
    ])
    def test_agent_type_mapping_correct(self, agent_name, expected_type):
        """Each agent maps to the correct AgentMemoryType."""
        assert get_memory_type_for_agent(agent_name) == expected_type


class TestTriggerMemoryWriteParametrized:
    """AC-30.14.1: _trigger_memory_write called correctly for each agent type."""

    @pytest.mark.parametrize("agent_name", ALL_AGENTS)
    @pytest.mark.asyncio
    async def test_trigger_calls_record_for_mapped_agent(
        self, agent_service, mock_memory_client, agent_name, wait_for_call
    ):
        """_trigger_memory_write calls record_learning_episode for each mapped agent."""
        await agent_service._trigger_memory_write(
            agent_type=agent_name,
            canvas_name="test/concept.canvas",
            node_id="node_001",
            concept="Test Concept",
            user_understanding="User answer text",
        )

        # Wait for fire-and-forget background task to complete
        await wait_for_call(mock_memory_client.add_learning_episode)

        # Should have called add_learning_episode
        mock_memory_client.add_learning_episode.assert_called_once()

    @pytest.mark.asyncio
    async def test_trigger_skips_unmapped_agent(
        self, agent_service, mock_memory_client
    ):
        """_trigger_memory_write skips agents not in the mapping."""
        await agent_service._trigger_memory_write(
            agent_type="nonexistent-agent",
            canvas_name="test/concept.canvas",
            node_id="node_001",
            concept="Test Concept",
        )

        # Should NOT have called add_learning_episode
        mock_memory_client.add_learning_episode.assert_not_called()


# ============================================================================
# Task 2: Agent Failure Degradation Tests (AC-30.14.2)
# ============================================================================

class TestAgentFailureDegradation:
    """AC-30.14.2: Degradation tests for agent/memory failures."""

    @pytest.mark.asyncio
    async def test_memory_write_failure_non_blocking(
        self, agent_service, mock_memory_client, wait_for_call
    ):
        """Memory write failure does not raise exceptions (fire-and-forget)."""
        mock_memory_client.add_learning_episode = AsyncMock(
            side_effect=Exception("Memory write timeout")
        )

        # Should NOT raise
        await agent_service._trigger_memory_write(
            agent_type="scoring-agent",
            canvas_name="test/concept.canvas",
            node_id="node_001",
            concept="Test Concept",
        )

        # Wait for fire-and-forget background task to complete
        await wait_for_call(mock_memory_client.add_learning_episode)

        # Verify it was attempted
        mock_memory_client.add_learning_episode.assert_called_once()

    @pytest.mark.asyncio
    async def test_memory_client_none_graceful_skip(self):
        """When memory_client is None, _trigger_memory_write skips gracefully."""
        from app.services.agent_service import AgentService

        service = AgentService(
            gemini_client=MagicMock(),
            memory_client=None,
        )

        # Should not raise
        await service._trigger_memory_write(
            agent_type="scoring-agent",
            canvas_name="test/concept.canvas",
            node_id="node_001",
            concept="Test Concept",
        )

    @pytest.mark.asyncio
    async def test_memory_write_returns_false_non_blocking(
        self, agent_service, mock_memory_client
    ):
        """Memory write returning False does not raise or block."""
        mock_memory_client.add_learning_episode = AsyncMock(return_value=False)

        # Should NOT raise
        await agent_service._trigger_memory_write(
            agent_type="scoring-agent",
            canvas_name="test/concept.canvas",
            node_id="node_001",
            concept="Test Concept",
        )

    @pytest.mark.asyncio
    async def test_trigger_with_all_optional_params(
        self, agent_service, mock_memory_client, wait_for_call
    ):
        """_trigger_memory_write accepts all optional parameters."""
        await agent_service._trigger_memory_write(
            agent_type="scoring-agent",
            canvas_name="test/concept.canvas",
            node_id="node_001",
            concept="Test Concept",
            user_understanding="My understanding of the concept",
            score=0.85,
            agent_feedback="Good understanding, needs more depth",
        )

        # Wait for fire-and-forget background task to complete
        await wait_for_call(mock_memory_client.add_learning_episode)

        mock_memory_client.add_learning_episode.assert_called_once()


# ============================================================================
# Task 3: Mapping Completeness Static Analysis Tests (AC-30.14.3)
# ============================================================================

class TestMappingCompleteness:
    """AC-30.14.3: Static analysis of mapping completeness."""

    def test_all_agent_names_set_matches_mapping_keys(self):
        """ALL_AGENT_NAMES set matches AGENT_MEMORY_MAPPING keys."""
        assert ALL_AGENT_NAMES == set(AGENT_MEMORY_MAPPING.keys())

    def test_mapping_consistent_with_agent_type_enum(self):
        """Every agent in AGENT_MEMORY_MAPPING has a corresponding AgentType enum value.

        Note: AgentType enum may have aliases (e.g., SCORING = "scoring")
        that don't need to be in the mapping. We check that every mapped agent
        name appears as at least one AgentType enum value.
        """
        all_enum_values = {e.value for e in AgentType}

        # Agents in mapping that are NOT in AgentType enum
        # (reserved agents like review-board-agent-selector may not be in AgentType)
        not_in_enum = []
        for agent_name in AGENT_MEMORY_MAPPING:
            if agent_name not in all_enum_values:
                not_in_enum.append(agent_name)

        # Reserved agents are OK (Story 30.12 AC-30.12.3 notes these)
        reserved_agents = {"review-board-agent-selector", "graphiti-memory-agent"}
        unexpected_missing = set(not_in_enum) - reserved_agents

        assert unexpected_missing == set(), (
            f"Agents in AGENT_MEMORY_MAPPING but not in AgentType enum "
            f"(and not reserved): {unexpected_missing}"
        )

    def test_all_memory_types_used(self):
        """All AgentMemoryType enum values are used in at least one mapping."""
        used_types = set(AGENT_MEMORY_MAPPING.values())
        all_types = set(AgentMemoryType)

        unused = all_types - used_types
        # REVIEW_CANVAS_CREATED may not yet be used
        allowed_unused = {AgentMemoryType.REVIEW_CANVAS_CREATED, AgentMemoryType.NODE_UPDATED}
        unexpected_unused = unused - allowed_unused

        assert unexpected_unused == set(), (
            f"AgentMemoryType values not used in any mapping: {unexpected_unused}"
        )

    def test_trigger_call_sites_exist_in_codebase(self):
        """Verify that agents with call sites actually have _trigger_memory_write calls.

        This is a static analysis test that scans the agent_service.py source code
        for _trigger_memory_write calls and extracts the agent_type arguments.
        """
        agent_service_path = Path(__file__).parent.parent.parent / "app" / "services" / "agent_service.py"
        source = agent_service_path.read_text(encoding="utf-8")

        # Find all _trigger_memory_write calls with explicit agent_type="..."
        pattern = r'_trigger_memory_write\([^)]*agent_type\s*=\s*["\']([^"\']+)["\']'
        found_agents = set(re.findall(pattern, source))

        # Check that explicitly called agents are in the mapping
        for agent_name in found_agents:
            assert agent_name in AGENT_MEMORY_MAPPING or agent_name == "hint-generation", (
                f"Agent '{agent_name}' has _trigger_memory_write call but is not in AGENT_MEMORY_MAPPING"
            )

    def test_mapping_agents_with_known_call_sites(self):
        """Verify agents that should have call sites actually do.

        Agents with direct calls in agent_service.py:
        - basic-decomposition, deep-decomposition, question-decomposition
        - scoring-agent
        - verification-question-agent
        - explanation agents via explanation_type_to_agent mapping
        """
        agent_service_path = Path(__file__).parent.parent.parent / "app" / "services" / "agent_service.py"
        source = agent_service_path.read_text(encoding="utf-8")

        # Agents that MUST have direct _trigger_memory_write calls
        must_have_calls = {
            "basic-decomposition",
            "deep-decomposition",
            "question-decomposition",
            "scoring-agent",
            "verification-question-agent",
        }

        # Direct calls pattern
        pattern = r'_trigger_memory_write\([^)]*agent_type\s*=\s*["\']([^"\']+)["\']'
        found_direct = set(re.findall(pattern, source))

        for agent in must_have_calls:
            assert agent in found_direct, (
                f"Agent '{agent}' MUST have a direct _trigger_memory_write call in agent_service.py"
            )

    def test_explanation_type_mapping_covers_explanation_agents(self):
        """The explanation_type_to_agent mapping covers all explanation-type agents."""
        agent_service_path = Path(__file__).parent.parent.parent / "app" / "services" / "agent_service.py"
        source = agent_service_path.read_text(encoding="utf-8")

        # Extract explanation_type_to_agent dict from source
        pattern = r'explanation_type_to_agent\s*=\s*\{([^}]+)\}'
        match = re.search(pattern, source)
        assert match is not None, "explanation_type_to_agent dict not found in agent_service.py"

        dict_content = match.group(1)
        # Extract agent names from the dict values
        agent_pattern = r'"([^"]+(?:-explanation|-teaching|-table|-anchor|-path))"'
        mapped_explanation_agents = set(re.findall(agent_pattern, dict_content))

        # These explanation agents should be in the mapping
        expected_explanation_agents = {
            "oral-explanation",
            "four-level-explanation",
            "example-teaching",
            "comparison-table",
            "memory-anchor",
            "clarification-path",
        }

        assert expected_explanation_agents.issubset(mapped_explanation_agents), (
            f"Missing explanation agents in explanation_type_to_agent: "
            f"{expected_explanation_agents - mapped_explanation_agents}"
        )

    def test_hint_generation_in_mapping_and_has_call_site(self):
        """hint-generation is in AGENT_MEMORY_MAPPING (C1 fix) AND has a call site in verification_service.py."""
        # C1 fix: hint-generation is now properly in the mapping
        assert "hint-generation" in AGENT_MEMORY_MAPPING
        assert AGENT_MEMORY_MAPPING["hint-generation"] == AgentMemoryType.EXPLANATION_GENERATED

        # It also has a call site in verification_service.py
        verification_path = Path(__file__).parent.parent.parent / "app" / "services" / "verification_service.py"
        source = verification_path.read_text(encoding="utf-8")
        assert "hint-generation" in source, (
            "hint-generation should have a call site in verification_service.py"
        )
