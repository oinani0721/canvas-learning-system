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


def _health_check_body() -> ast.AST:
    """Locate AgentService.health_check in the production source.

    Scoped to that one method on purpose: a module-wide scan for the name
    ``expected_templates`` turns any unrelated local of the same name — in a
    helper nobody calls — into a failure of this gate.
    """
    from app.services import agent_service

    source_path = agent_service.__file__
    tree = ast.parse(Path(source_path).read_text(encoding="utf-8"))
    functions = [
        node
        for cls in ast.walk(tree)
        if isinstance(cls, ast.ClassDef) and cls.name == "AgentService"
        for node in cls.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "health_check"
    ]
    assert len(functions) == 1, (
        f"expected exactly one AgentService.health_check in {source_path}, "
        f"found {len(functions)} — the /agents/health probe moved or was renamed, "
        f"so this gate no longer watches it"
    )
    return functions[0]


def _health_expected_templates() -> list[str]:
    """Read the /agents/health probe's expected_templates list from source.

    Binds to the production module actually imported (``agent_service.__file__``)
    rather than a path guess, and parses it with ``ast`` instead of a regex.

    ⚠️ This is a *source* read and cannot see edits that change the list's
    contents without rebinding the name — ``expected_templates.remove(x)`` and
    ``expected_templates[:] = ...`` both do exactly that. Reading this list is
    therefore only half the gate; the other half is
    ``test_health_probe_output_matches_the_table_this_gate_reads``, which
    compares this list against what the probe actually produced at runtime.
    """
    fn = _health_check_body()

    bindings = [
        n
        for n in ast.walk(fn)
        if isinstance(n, ast.Name) and n.id == "expected_templates" and isinstance(n.ctx, ast.Store)
    ]
    assert len(bindings) == 1, (
        f"`expected_templates` is bound {len(bindings)} time(s) inside "
        f"AgentService.health_check at line(s) {sorted(n.lineno for n in bindings)}; "
        f"this gate reads a single list literal, so 0 bindings means the table was "
        f"renamed or removed and 2+ means the list this gate reads may not be the "
        f"one the probe iterates"
    )

    literals = [
        [e.value for e in node.value.elts if isinstance(e, ast.Constant)]
        for node in ast.walk(fn)
        if isinstance(node, (ast.Assign, ast.AnnAssign)) and isinstance(node.value, ast.List)
        for t in (node.targets if isinstance(node, ast.Assign) else [node.target])
        if isinstance(t, ast.Name) and t.id == "expected_templates"
    ]
    assert len(literals) == 1, (
        f"`expected_templates` is bound exactly once inside AgentService.health_check "
        f"but not to a list literal, so this gate can no longer read the probe's table"
    )
    return literals[0]


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

    async def test_health_probe_output_matches_the_table_this_gate_reads(self):
        """Bind the source read to what the probe actually produced at runtime.

        `_health_expected_templates` reads a list literal out of the source, and
        a source read is blind to edits that change the list's *contents* without
        rebinding the name — `expected_templates.remove("hint-generation")` and
        `expected_templates[:] = expected_templates[:-1]` both do that, leaving a
        purely static gate green over a table it no longer describes.

        Running the real probe closes that: any such edit changes the length the
        probe reports, so `total` stops matching the static list. `missing == []`
        additionally catches a name the table watches but the directory lacks —
        which is the whole failure this card exists to fix.

        No network: `include_api_test=False` never reaches the AI provider, and a
        bare AgentService() has no client configured.
        """
        from app.services.agent_service import AgentService

        names = _health_expected_templates()
        report = await AgentService().health_check(include_api_test=False)
        check = report["checks"]["prompt_templates"]

        assert check["total"] == len(names), (
            f"the probe iterates {check['total']} templates but the list this gate "
            f"reads from source has {len(names)} ({sorted(names)}) — the table is "
            f"being modified after it is defined, so the source read is stale"
        )
        assert check["missing"] == [], (
            f"the probe reports missing templates: {check['missing']}; "
            f"/agents/health is degraded until those .md files are restored"
        )
        assert check["available"] == len(names), (
            f"probe available={check['available']} but the table has {len(names)} entries"
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
        smoke_only = smoke - health
        # Report each direction separately (a symmetric difference cannot say
        # which side moved) and state each side neutrally: an entry can leave
        # the smoke-only set either because health started watching it OR
        # because it was dropped from EXPECTED_AGENT_TEMPLATES.
        assert smoke_only == TEMPLATES_NOT_IN_AGENT_TYPE, (
            f"smoke-only set drifted; "
            f"in EXPECTED_AGENT_TEMPLATES but not watched by health, and not listed "
            f"as tripwire-only: {sorted(smoke_only - TEMPLATES_NOT_IN_AGENT_TYPE)}; "
            f"listed as tripwire-only but no longer smoke-only (health now watches it, "
            f"or it left EXPECTED_AGENT_TEMPLATES): "
            f"{sorted(TEMPLATES_NOT_IN_AGENT_TYPE - smoke_only)}"
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
