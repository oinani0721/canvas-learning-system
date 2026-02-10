# Canvas Learning System - Agent Memory Mapping
# Story 30.4: Agent Memory Mapping Configuration
# [Source: docs/stories/30.4.story.md]
"""
Agent to memory type mapping configuration.

This module defines which agents write to which memory layers.
Maps 15 agents to their corresponding temporal event types as defined
in temporal-event.schema.json.

Memory Event Types (from temporal-event.schema.json):
- decomposition_completed: Decomposition agents finish analysis
- scoring_completed: Scoring agent evaluates understanding
- explanation_generated: Explanation agents produce content
- review_canvas_created: Review canvas generation
- concept_reviewed: Concept review completed
- canvas_opened: Canvas opened for learning
- node_created: New node created (memory anchors)
- node_updated: Existing node updated
"""

from enum import Enum
from typing import Dict, Optional, Set


class AgentMemoryType(str, Enum):
    """Memory event types aligned with temporal-event.schema.json."""
    DECOMPOSITION_COMPLETED = "decomposition_completed"
    SCORING_COMPLETED = "scoring_completed"
    EXPLANATION_GENERATED = "explanation_generated"
    REVIEW_CANVAS_CREATED = "review_canvas_created"
    CONCEPT_REVIEWED = "concept_reviewed"
    CANVAS_OPENED = "canvas_opened"
    NODE_CREATED = "node_created"
    NODE_UPDATED = "node_updated"


# Complete agent to memory type mapping (15 agents)
# Agent names use hyphen format to match AgentType enum values
AGENT_MEMORY_MAPPING: Dict[str, AgentMemoryType] = {
    # Decomposition agents -> decomposition_completed
    "basic-decomposition": AgentMemoryType.DECOMPOSITION_COMPLETED,
    "deep-decomposition": AgentMemoryType.DECOMPOSITION_COMPLETED,
    "question-decomposition": AgentMemoryType.DECOMPOSITION_COMPLETED,

    # Explanation agents -> explanation_generated
    "four-level-explanation": AgentMemoryType.EXPLANATION_GENERATED,
    "oral-explanation": AgentMemoryType.EXPLANATION_GENERATED,
    "example-teaching": AgentMemoryType.EXPLANATION_GENERATED,
    "clarification-path": AgentMemoryType.EXPLANATION_GENERATED,
    "comparison-table": AgentMemoryType.EXPLANATION_GENERATED,
    "verification-question-agent": AgentMemoryType.EXPLANATION_GENERATED,
    "hint-generation": AgentMemoryType.EXPLANATION_GENERATED,  # Story 30.12 fix: was missing, trigger in verification_service.py

    # Scoring agent -> scoring_completed
    "scoring-agent": AgentMemoryType.SCORING_COMPLETED,

    # Memory anchor -> node_created
    "memory-anchor": AgentMemoryType.NODE_CREATED,

    # Canvas orchestrator -> canvas_opened
    "canvas-orchestrator": AgentMemoryType.CANVAS_OPENED,

    # System agents -> concept_reviewed
    # Reserved: no active call site yet (Story 30.12 AC-30.12.3)
    "review-board-agent-selector": AgentMemoryType.CONCEPT_REVIEWED,
    "graphiti-memory-agent": AgentMemoryType.CONCEPT_REVIEWED,
}

# All agent names (15 agents total)
ALL_AGENT_NAMES: Set[str] = set(AGENT_MEMORY_MAPPING.keys())


def get_memory_type_for_agent(agent_name: str) -> Optional[AgentMemoryType]:
    """
    Get memory type for an agent.

    Args:
        agent_name: Name of the agent (hyphen format, e.g., 'scoring-agent')

    Returns:
        AgentMemoryType if agent is mapped, None if not found
    """
    return AGENT_MEMORY_MAPPING.get(agent_name, None)


def is_memory_enabled_agent(agent_name: str) -> bool:
    """
    Check if an agent has memory writing enabled.

    Args:
        agent_name: Name of the agent

    Returns:
        bool: True if agent writes to memory
    """
    return agent_name in AGENT_MEMORY_MAPPING
