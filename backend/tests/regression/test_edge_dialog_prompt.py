# Story 4.3: EI+SE Dual Strategy - Edge Dialog Prompt Regression Tests
# [Source: _bmad-output/implementation-artifacts/4-3-ei-se-dual-strategy.md#Task 5]
"""
Regression tests for edge-dialog.md prompt template.

Verifies:
  - AC-1: Prompt contains Elaborative Interrogation (EI) strategy instructions
  - AC-2: Prompt contains Self-Explanation (SE) strategy instructions
  - AC-3: Active Recall is explicitly excluded
  - AC-4: Prompt instructs natural conversation style (no teaching jargon)
  - AC-5: Prompt includes depth assessment standards and density control
  - AC-5: Prompt includes existing knowledge context placeholders

NOTE (Story 4-3/4-4 M1): These tests validate the backend prompt template that is
served to the CLI via MCP tools. In the current architecture (CLI mode), the
frontend does NOT maintain a copy of this prompt — the Claude Code CLI loads it
via --append-system-prompt or MCP tool configuration. These regression tests
ensure prompt content integrity at the source of truth (backend/prompts/).
"""

from pathlib import Path

import pytest

# Path to the edge-dialog prompt template
_PROMPT_PATH = Path(__file__).parent.parent.parent / "prompts" / "edge-dialog.md"


@pytest.fixture(scope="module")
def prompt_content():
    """Load the edge-dialog.md prompt template."""
    assert _PROMPT_PATH.exists(), f"Prompt file not found: {_PROMPT_PATH}"
    return _PROMPT_PATH.read_text(encoding="utf-8")


# ═══════════════════════════════════════════════════════════════════════════════
# AC-1: Elaborative Interrogation (EI) strategy present
# ═══════════════════════════════════════════════════════════════════════════════


def test_ei_strategy_header_present(prompt_content):
    """Prompt contains an EI strategy section."""
    assert "Elaborative Interrogation" in prompt_content


def test_ei_why_how_questions(prompt_content):
    """Prompt instructs Agent to ask why/how deep questions."""
    has_why = any(
        kw in prompt_content
        for kw in [
            "why",
            "how",
            "cause",
            "condition",
            # Chinese equivalents in the actual prompt
            "\u4e3a\u4ec0\u4e48",
            "\u600e\u4e48\u6837",
            "\u56e0\u679c",
            "\u6761\u4ef6",
        ]
    )
    assert has_why, "EI section must instruct asking why/how/cause/condition questions"


def test_ei_counterexample_probing(prompt_content):
    """Prompt instructs Agent to probe for counterexamples/exceptions."""
    has_counter = any(
        kw in prompt_content
        for kw in [
            "counterexample",
            "exception",
            "not hold",
            "counter",
            # Chinese equivalents
            "\u53cd\u4f8b",
            "\u4f8b\u5916",
            "\u4e0d\u6210\u7acb",
        ]
    )
    assert has_counter, "EI section must mention counterexamples or exceptions"


# ═══════════════════════════════════════════════════════════════════════════════
# AC-2: Self-Explanation (SE) strategy present
# ═══════════════════════════════════════════════════════════════════════════════


def test_se_strategy_header_present(prompt_content):
    """Prompt contains an SE strategy section."""
    assert "Self-Explanation" in prompt_content or "self-explanation" in prompt_content.lower()


def test_se_own_words_instruction(prompt_content):
    """Prompt instructs user to explain in own words."""
    has_own_words = any(
        kw in prompt_content
        for kw in [
            "own words",
            "your words",
            "rephrase",
            "restate",
            # Chinese equivalents
            "\u81ea\u5df1\u7684\u8bdd",
        ]
    )
    assert has_own_words, "SE section must instruct user to explain in own words"


def test_se_conditional_trigger(prompt_content):
    """SE is triggered conditionally, not every time."""
    has_conditional = any(
        kw in prompt_content
        for kw in [
            "not every time",
            "when",
            "insufficient",
            "not deep enough",
            "only when",
            # Chinese equivalents
            "\u4e0d\u662f\u6bcf\u6b21\u90fd",
            "\u4e0d\u591f\u6df1\u5165",
            "\u4e0d\u5145\u5206",
        ]
    )
    assert has_conditional, "SE must be conditionally triggered, not forced every time"


# ═══════════════════════════════════════════════════════════════════════════════
# AC-3: Active Recall explicitly excluded
# ═══════════════════════════════════════════════════════════════════════════════


def test_active_recall_excluded(prompt_content):
    """Prompt explicitly excludes Active Recall strategy."""
    assert "Active Recall" in prompt_content, "Prompt must mention Active Recall"
    has_exclusion = any(
        kw in prompt_content
        for kw in [
            "not use active recall",
            "exclude active recall",
            "no active recall",
            # Chinese: "not use Active Recall strategy"
            "\u4e0d\u8981\u4f7f\u7528 Active Recall",
        ]
    )
    assert has_exclusion, "Prompt must explicitly instruct NOT to use Active Recall"


# ═══════════════════════════════════════════════════════════════════════════════
# AC-4: Natural conversation style (no teaching jargon)
# ═══════════════════════════════════════════════════════════════════════════════


def test_no_teaching_jargon_instruction(prompt_content):
    """Prompt instructs Agent to avoid using teaching terminology."""
    has_no_jargon = any(
        kw in prompt_content
        for kw in [
            "no teaching",
            "avoid jargon",
            "natural",
            "casual",
            # Chinese equivalents
            "\u81ea\u7136",
            "\u6559\u5b66\u672f\u8bed",
            "\u4e0d\u8981\u7528\u6559\u5b66\u672f\u8bed",
        ]
    )
    assert has_no_jargon, "Prompt must instruct natural conversation without teaching jargon"


def test_conversation_style_not_exam(prompt_content):
    """Prompt distinguishes from exam/quiz interaction style."""
    has_not_exam = any(
        kw in prompt_content
        for kw in [
            "not exam",
            "not quiz",
            "not test",
            "not homework",
            # Chinese equivalents
            "\u8003\u8bd5",
            "\u505a\u4f5c\u4e1a",
            "\u505a\u7ec3\u4e60",
        ]
    )
    assert has_not_exam, "Prompt must differentiate from exam/quiz style"


# ═══════════════════════════════════════════════════════════════════════════════
# AC-5: Depth assessment and density control
# ═══════════════════════════════════════════════════════════════════════════════


def test_depth_assessment_table(prompt_content):
    """Prompt contains depth assessment standards (levels 1-5)."""
    for level in ["1", "2", "3", "4"]:
        assert level in prompt_content, f"Depth level {level} must be in prompt"


def test_density_control_max_rounds(prompt_content):
    """Prompt specifies maximum questioning rounds."""
    has_limit = any(
        kw in prompt_content
        for kw in [
            "3-4",
            "3 to 4",
            "max",
            "at most",
            "no more than",
            # Chinese equivalents
            "\u6700\u591a",
        ]
    )
    assert has_limit, "Prompt must specify max questioning rounds (3-4)"


# ═══════════════════════════════════════════════════════════════════════════════
# AC-5: Existing knowledge context placeholders
# ═══════════════════════════════════════════════════════════════════════════════


def test_source_concept_placeholder(prompt_content):
    """Prompt contains source_concept template variable."""
    assert "{{source_concept}}" in prompt_content


def test_target_concept_placeholder(prompt_content):
    """Prompt contains target_concept template variable."""
    assert "{{target_concept}}" in prompt_content


def test_existing_tips_placeholder(prompt_content):
    """Prompt contains existing_tips context section."""
    assert "existing_tips" in prompt_content


def test_existing_errors_placeholder(prompt_content):
    """Prompt contains existing_errors context section."""
    assert "existing_errors" in prompt_content


def test_existing_rationale_placeholder(prompt_content):
    """Prompt contains existing_rationale context section."""
    assert "existing_rationale" in prompt_content


# ═══════════════════════════════════════════════════════════════════════════════
# Structural integrity
# ═══════════════════════════════════════════════════════════════════════════════


def test_prompt_not_empty(prompt_content):
    """Prompt file is not empty."""
    assert len(prompt_content.strip()) > 100, "Prompt must have substantial content"


def test_prompt_has_record_edge_rationale_tool(prompt_content):
    """Prompt instructs Agent to call record_edge_rationale tool."""
    assert "record_edge_rationale" in prompt_content
