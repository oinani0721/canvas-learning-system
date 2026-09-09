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

import ast
from pathlib import Path

import pytest

# ===========================================================================
# Constants
# ===========================================================================

# Expected agent template files.
# CARD-RED-E (2026-09-09): the earlier note here claimed recovery via
# `git checkout eb86275` — that tree holds only 17 templates and no
# hint-generation.md, so it cannot produce this 18-item list. Actual origin:
# 11 never deleted + 6 restored byte-for-byte from `f425d7b7^` + hint-generation.md
# newly authored (absent from every tree in repo history).
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

# AgentType members that are aliases of another member's template file
# (agent_service.AgentType.FOUR_LEVEL / .SCORING). They have no .md of their own.
AGENT_TYPE_ALIASES = {"four-level", "scoring"}

# Templates that live in .claude/agents/ but are NOT AgentType members, so
# call_agent() never loads them and the /agents/health probe must not watch them.
# They stay on disk purely as a delete tripwire: commit f425d7b7 removed all five
# at once, which is why EXPECTED_AGENT_TEMPLATES is wider than the health table.
TEMPLATES_NOT_IN_AGENT_TYPE = {
    "graphiti-memory-agent",
    "iteration-validator",
    "parallel-dev-orchestrator",
    "planning-orchestrator",
    "review-board-agent-selector",
}


def _health_expected_templates() -> list[str]:
    """Read the /agents/health probe's expected_templates literal from source.

    Binds to the production module actually imported (``agent_service.__file__``)
    rather than a path guess, and parses it with ``ast`` instead of a regex so a
    rename or deletion of the list raises here instead of silently passing.
    """
    from app.services import agent_service

    tree = ast.parse(Path(agent_service.__file__).read_text(encoding="utf-8"))
    found = [
        [e.value for e in node.value.elts if isinstance(e, ast.Constant)]
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.List)
        for t in node.targets
        if isinstance(t, ast.Name) and t.id == "expected_templates"
    ]
    assert len(found) == 1, (
        f"expected exactly one `expected_templates = [...]` literal in "
        f"{agent_service.__file__}, found {len(found)} — the health probe was "
        f"renamed or removed, so this gate no longer watches anything"
    )
    return found[0]


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
        """Each agent template must exist AND have content (non-zero size).

        CARD-RED-E: the existence check used to be `if filepath.exists():`, which
        made a missing file pass with zero assertions — all 7 absent templates
        reported PASSED here while test_agent_template_exists reported FAILED on
        the same files. Asserting existence first is what makes this test load-bearing.
        """
        filepath = _AGENTS_DIR / filename
        assert filepath.exists(), f"Missing agent template: {filepath}"
        content = filepath.read_text(encoding="utf-8")
        assert len(content.strip()) > 0, f"Empty template: {filename}"

    def test_no_expected_template_is_missing(self):
        """Delete tripwire: report every missing template in one message.

        The parametrized existence test names one file per failure; this one
        names the whole missing set at once, which is what a bulk deletion
        (like commit f425d7b7, which removed 6 templates) looks like.
        """
        missing = sorted(n for n in EXPECTED_AGENT_TEMPLATES if not (_AGENTS_DIR / n).exists())
        assert not missing, (
            f"{len(missing)} of {len(EXPECTED_AGENT_TEMPLATES)} agent templates "
            f"are missing from {_AGENTS_DIR}: {missing}"
        )

    def test_minimum_template_count(self):
        """At least 18 agent templates must exist.

        18 = 11 never deleted + 6 restored from `f425d7b7^` + hint-generation.md.
        The threshold was 17 before CARD-RED-E, which let the directory lose
        hint-generation.md and still pass.
        """
        actual_files = list(_AGENTS_DIR.glob("*.md"))
        assert len(actual_files) >= 18, (
            f"Expected >= 18 agent templates, found {len(actual_files)}: {[f.name for f in actual_files]}"
        )

    def test_health_expected_templates_equals_loadable_agent_types(self):
        """The /agents/health probe must watch exactly the loadable AgentType values.

        Binds agent_service's `expected_templates` literal to AgentType itself, so
        adding an AgentType member without adding it to the health table (which is
        how hint-generation stayed invisible to the probe for 7 months) fails here.
        """
        from app.services.agent_service import AgentType

        health = set(_health_expected_templates())
        loadable = {t.value for t in AgentType} - AGENT_TYPE_ALIASES
        assert health == loadable, (
            f"health probe table != loadable AgentType values; "
            f"in health only: {sorted(health - loadable)}; "
            f"in AgentType only: {sorted(loadable - health)}"
        )

    def test_smoke_table_minus_health_table_is_the_tripwire_only_set(self):
        """Make the gap between the two tables an executable fact, not a comment.

        This file guards 18 templates; the health probe watches 13. The 5-item
        difference is exactly the templates that are not AgentType members, so
        production never loads them — they are kept on disk as a delete tripwire.
        The reverse difference must be empty: anything the health probe watches
        must also be guarded here.
        """
        smoke = {n.removesuffix(".md") for n in EXPECTED_AGENT_TEMPLATES}
        health = set(_health_expected_templates())
        assert smoke - health == TEMPLATES_NOT_IN_AGENT_TYPE, (
            f"unexpected smoke-only templates: {sorted((smoke - health) ^ TEMPLATES_NOT_IN_AGENT_TYPE)}"
        )
        assert health - smoke == set(), (
            f"health probe watches templates this file does not guard: {sorted(health - smoke)}"
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
