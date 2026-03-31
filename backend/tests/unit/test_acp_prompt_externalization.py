# Epic 3: Layer 3 ACP Prompt Externalization
# Features 3.1 + 3.2: Create layer3.md template + Refactor _format_acp_layer
#
# TDD: These tests are written FIRST, before implementation.
"""
Tests for Layer 3 ACP prompt externalization.

Feature 3.1: Verify layer3.md template file exists with required placeholders.
Feature 3.2: Verify _format_acp_layer loads from file and produces identical output.
"""

from pathlib import Path

import pytest

from app.models.exam_models import ACPData
from app.services.question_generator import QuestionGenerator, _PROMPTS_DIR


# ---------------------------------------------------------------------------
# Feature 3.1: Template file existence and structure
# ---------------------------------------------------------------------------


class TestLayer3TemplateFile:
    """Feature 3.1: layer3.md template must exist with correct placeholders."""

    def test_layer3_template_file_exists(self) -> None:
        """AC: File backend/app/prompts/exam/layer3.md exists."""
        path = _PROMPTS_DIR / "layer3.md"
        assert path.exists(), f"layer3.md not found at {path}"
        content = path.read_text(encoding="utf-8")
        assert len(content) > 0, "layer3.md is empty"

    def test_layer3_template_is_valid_markdown(self) -> None:
        """AC: Template is valid Markdown (contains markdown formatting)."""
        path = _PROMPTS_DIR / "layer3.md"
        content = path.read_text(encoding="utf-8")
        # Must contain bold markers (** **) used in the ACP format
        assert "**" in content, "Template should contain markdown bold markers"

    def test_layer3_template_has_required_placeholders(self) -> None:
        """AC: Template contains placeholders for all required context variables."""
        path = _PROMPTS_DIR / "layer3.md"
        content = path.read_text(encoding="utf-8")

        required_placeholders = [
            "{node_content}",
            "{node_type}",
            "{effective_proficiency}",
            "{p_mastery}",
            "{retrievability}",
            "{mastery_label}",
            "{optional_sections}",
        ]
        for placeholder in required_placeholders:
            assert placeholder in content, (
                f"Missing placeholder {placeholder} in layer3.md"
            )


# ---------------------------------------------------------------------------
# Feature 3.2: Refactored _format_acp_layer
# ---------------------------------------------------------------------------


def _make_full_acp() -> ACPData:
    """Create an ACPData with ALL fields populated for testing."""
    return ACPData(
        node_id="node-test-001",
        node_content="Euler's formula: e^(ix) = cos(x) + i*sin(x)",
        node_type="knowledge_point",
        student_tips=["Remember the unit circle", "Link to Taylor series"],
        error_history=[
            {"error_type": "conceptual", "description": "Confused e^ix with e^x"},
            {"error_type": "procedural", "description": "Wrong sign on imaginary part"},
        ],
        edge_reasons=["prerequisite of Fourier transform", "builds on complex numbers"],
        mastery_level=0.35,
        mastery_label="Developing",
        effective_proficiency=0.42,
        conversation_summary="Student struggles with the geometric interpretation.",
        retrievability=0.78,
        p_mastery=0.30,
        kg_relevance=0.6,
    )


def _make_minimal_acp() -> ACPData:
    """Create an ACPData with only required fields (no optional sections)."""
    return ACPData(
        node_id="node-minimal-001",
        node_content="Basic algebra",
        node_type="knowledge_point",
        mastery_label="Not Assessed",
        effective_proficiency=0.0,
        p_mastery=0.1,
        retrievability=1.0,
    )


class TestFormatAcpLayerRefactored:
    """Feature 3.2: _format_acp_layer must load from file, no inline strings."""

    def test_format_acp_layer_with_all_fields(self) -> None:
        """AC: Formatted output contains all context data when all fields present."""
        gen = QuestionGenerator()
        acp = _make_full_acp()
        result = gen._format_acp_layer(acp)

        # Required fields always present
        assert "Euler's formula" in result
        assert "knowledge_point" in result
        assert "effective_proficiency=0.42" in result
        assert "p_mastery=0.30" in result
        assert "retrievability=0.78" in result
        assert "Developing" in result

        # Optional sections present when data exists
        assert "Remember the unit circle" in result
        assert "Link to Taylor series" in result
        assert "conceptual" in result
        assert "Confused e^ix with e^x" in result
        assert "procedural" in result
        assert "prerequisite of Fourier transform" in result
        assert "Student struggles with the geometric interpretation" in result

    def test_format_acp_layer_with_minimal_fields(self) -> None:
        """AC: No crash when only required fields are present."""
        gen = QuestionGenerator()
        acp = _make_minimal_acp()
        result = gen._format_acp_layer(acp)

        assert "Basic algebra" in result
        assert "knowledge_point" in result
        assert "Not Assessed" in result
        # Should not crash, should return non-empty string
        assert len(result) > 0

    def test_format_acp_layer_optional_sections_omitted(self) -> None:
        """AC: Empty tips/errors/edges/conversation do NOT appear in output."""
        gen = QuestionGenerator()
        acp = _make_minimal_acp()
        result = gen._format_acp_layer(acp)

        # These labels should NOT appear when their data is empty
        assert "Tips" not in result
        assert "历史错误" not in result
        assert "Edge" not in result
        assert "对话历史" not in result

    def test_format_acp_layer_uses_template_file(self) -> None:
        """AC: _format_acp_layer reads from layer3.md (not hardcoded inline).

        Verify by checking that the generator has loaded the layer3 template
        and that the template content is non-empty.
        """
        gen = QuestionGenerator()
        # The refactored __init__ should load _layer3_template
        assert hasattr(gen, "_layer3_template"), (
            "_layer3_template attribute missing — _format_acp_layer is not loading from file"
        )
        assert len(gen._layer3_template) > 0, (
            "_layer3_template is empty — layer3.md not loaded"
        )

    def test_format_acp_layer_output_matches_original_format(self) -> None:
        """AC: Output format is identical to the original inline implementation.

        The refactored method must produce the SAME output structure:
        lines joined by newline, same field labels, same truncation.
        """
        gen = QuestionGenerator()
        acp = _make_full_acp()
        result = gen._format_acp_layer(acp)

        # Verify the exact structure matches the original format
        lines = result.strip().split("\n")

        # Line 0: target node
        assert lines[0].startswith("**目标节点**:")
        # Line 1: node type
        assert lines[1].startswith("**节点类型**:")
        # Line 2: proficiency
        assert lines[2].startswith("**精通度**:")

    def test_format_acp_layer_truncates_node_content(self) -> None:
        """AC: node_content is truncated to 200 chars as in original."""
        gen = QuestionGenerator()
        long_content = "A" * 300
        acp = ACPData(
            node_id="node-long",
            node_content=long_content,
            effective_proficiency=0.5,
            p_mastery=0.5,
            retrievability=0.5,
            mastery_label="Developing",
        )
        result = gen._format_acp_layer(acp)
        # The first line should have truncated content (200 chars max)
        first_line = result.split("\n")[0]
        # Original code: acp.node_content[:200]
        assert "A" * 200 in first_line
        assert "A" * 201 not in first_line

    def test_format_acp_layer_error_history_format(self) -> None:
        """AC: Error history uses the exact same format as original."""
        gen = QuestionGenerator()
        acp = ACPData(
            node_id="node-err",
            node_content="Test concept",
            error_history=[
                {"error_type": "conceptual", "description": "Mixed up A and B"},
            ],
            effective_proficiency=0.3,
            p_mastery=0.2,
            retrievability=0.9,
            mastery_label="Beginner",
        )
        result = gen._format_acp_layer(acp)
        # Original format: "  - [error_type] description"
        assert "  - [conceptual] Mixed up A and B" in result

    def test_format_acp_layer_conversation_truncated(self) -> None:
        """AC: Conversation summary is truncated to 500 chars as in original."""
        gen = QuestionGenerator()
        long_summary = "B" * 600
        acp = ACPData(
            node_id="node-conv",
            node_content="Test",
            conversation_summary=long_summary,
            effective_proficiency=0.5,
            p_mastery=0.5,
            retrievability=0.5,
            mastery_label="Developing",
        )
        result = gen._format_acp_layer(acp)
        # Should contain exactly 500 B's, not 501
        assert "B" * 500 in result
        assert "B" * 501 not in result
