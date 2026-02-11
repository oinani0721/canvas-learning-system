# Canvas Learning System - Agent Templates Smoke Tests
# Story 31.A.2: Agent模板恢复与hint-generation
"""
Smoke tests verifying agent template files exist and AgentType enum is complete.

Tests verify:
- 31.A.2: All 18 agent template .md files exist in .claude/agents/
- 31.A.2: hint-generation AgentType enum value exists
- 31.A.2: All agent templates are non-empty

[Source: docs/stories/31.A.2.story.md]
"""

from pathlib import Path

import pytest


# ===========================================================================
# Constants
# ===========================================================================

# Expected agent template files after recovery (git checkout eb86275)
EXPECTED_AGENT_TEMPLATES = [
    "basic-decomposition.md",
    "canvas-orchestrator.md",
    "clarification-path.md",
    "comparison-table.md",
    "deep-decomposition.md",
    "example-teaching.md",
    "four-level-explanation.md",
    "graphiti-memory-agent.md",
    "hint-generation.md",
    "iteration-validator.md",
    "memory-anchor.md",
    "oral-explanation.md",
    "parallel-dev-orchestrator.md",
    "planning-orchestrator.md",
    "question-decomposition.md",
    "review-board-agent-selector.md",
    "scoring-agent.md",
    "verification-question-agent.md",
]

# Project root — navigate from backend/tests/unit/ up to project root
_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
_AGENTS_DIR = _PROJECT_ROOT / ".claude" / "agents"


# ===========================================================================
# Tests: Agent Template File Existence
# ===========================================================================


class TestAgentTemplateFiles:
    """Smoke tests for agent template file existence.

    Story 31.A.2: Agent templates were accidentally deleted in commit abf1d58
    and restored via `git checkout eb86275 -- .claude/agents/`.
    These tests ensure they remain present.

    [Source: docs/stories/31.A.2.story.md]
    """

    def test_agents_directory_exists(self):
        """Verify .claude/agents/ directory exists."""
        assert _AGENTS_DIR.exists(), f"Missing: {_AGENTS_DIR}"
        assert _AGENTS_DIR.is_dir()

    @pytest.mark.parametrize("filename", EXPECTED_AGENT_TEMPLATES)
    def test_agent_template_exists(self, filename):
        """Each expected agent template file must exist."""
        filepath = _AGENTS_DIR / filename
        assert filepath.exists(), f"Missing agent template: {filepath}"

    @pytest.mark.parametrize("filename", EXPECTED_AGENT_TEMPLATES)
    def test_agent_template_not_empty(self, filename):
        """Each agent template must have content (non-zero size)."""
        filepath = _AGENTS_DIR / filename
        if filepath.exists():
            content = filepath.read_text(encoding="utf-8")
            assert len(content.strip()) > 0, f"Empty template: {filename}"

    def test_minimum_template_count(self):
        """At least 17 agent templates must exist (original count before deletion)."""
        actual_files = list(_AGENTS_DIR.glob("*.md"))
        assert len(actual_files) >= 17, (
            f"Expected >= 17 agent templates, found {len(actual_files)}: "
            f"{[f.name for f in actual_files]}"
        )

    def test_hint_generation_template_exists(self):
        """Story 31.A.2: hint-generation.md must exist (new template added)."""
        filepath = _AGENTS_DIR / "hint-generation.md"
        assert filepath.exists(), "hint-generation.md template missing"

    def test_scoring_agent_template_exists(self):
        """scoring-agent.md must exist (critical for EPIC-31 scoring)."""
        filepath = _AGENTS_DIR / "scoring-agent.md"
        assert filepath.exists(), "scoring-agent.md template missing"

    def test_verification_question_template_exists(self):
        """verification-question-agent.md must exist (critical for EPIC-31 questions)."""
        filepath = _AGENTS_DIR / "verification-question-agent.md"
        assert filepath.exists(), "verification-question-agent.md template missing"


# ===========================================================================
# Tests: AgentType Enum
# ===========================================================================


class TestAgentTypeEnum:
    """Verify AgentType enum includes all required values.

    Story 31.A.2: hint-generation was added as new AgentType enum value.

    [Source: docs/stories/31.A.2.story.md]
    """

    def test_hint_generation_enum_exists(self):
        """AgentType.HINT_GENERATION enum value must exist."""
        from app.services.agent_service import AgentType
        assert hasattr(AgentType, "HINT_GENERATION")
        assert AgentType.HINT_GENERATION.value == "hint-generation"

    def test_verification_question_enum_exists(self):
        """AgentType.VERIFICATION_QUESTION enum value must exist."""
        from app.services.agent_service import AgentType
        assert hasattr(AgentType, "VERIFICATION_QUESTION")

    def test_scoring_enum_exists(self):
        """AgentType.SCORING enum value must exist."""
        from app.services.agent_service import AgentType
        assert hasattr(AgentType, "SCORING")

    def test_basic_decomposition_enum_exists(self):
        """AgentType.BASIC_DECOMPOSITION enum value must exist."""
        from app.services.agent_service import AgentType
        assert hasattr(AgentType, "BASIC_DECOMPOSITION")
