"""
Story 12.K.5: Node ID Pattern Contract Tests

Tests node ID validation against the relaxed pattern defined in:
- backend/app/models/schemas.py:221
- specs/data/canvas-node.schema.json:20
- docs/architecture/decisions/ADR-012-NODE-ID-PATTERNS.md

Pattern: ^[a-zA-Z0-9][-a-zA-Z0-9]*$
"""

import pytest
from pydantic import ValidationError

from app.models.schemas import NodeRead


class TestNodeIdPatternValidation:
    """Contract tests for node ID patterns."""

    # =========================================================================
    # Valid IDs: Obsidian Native (Pure Hexadecimal)
    # =========================================================================

    @pytest.mark.parametrize("node_id", [
        "b33c50660173e5d3",  # Standard Obsidian 16-char hex
        "a1b2c3d4e5f67890",  # All hex digits
        "1234567890abcdef",  # Numbers first
        "abcdef1234567890",  # Letters first
        "0",                  # Single digit
        "a",                  # Single letter
        "A1B2C3",             # Mixed case (allowed by relaxed pattern)
    ])
    def test_obsidian_native_ids_valid(self, node_id: str):
        """Obsidian native hexadecimal IDs should be accepted."""
        node = NodeRead(
            id=node_id,
            type="text",
            x=0,
            y=0,
            width=100,
            height=100
        )
        assert node.id == node_id

    # =========================================================================
    # Valid IDs: Agent-Generated (Semantic Prefix)
    # =========================================================================

    @pytest.mark.parametrize("node_id,description", [
        # Verification Question (vq-)
        ("vq-b33c5066-0-ee742d", "VQ with index 0"),
        ("vq-a1b2c3d4-5-abc123", "VQ with higher index"),

        # Question Decomposition (qd-)
        ("qd-b33c5066-1-ab12cd", "QD sub-question"),
        ("qd-original-0-xyz789", "QD from text node"),

        # Explanation Types
        ("explain-oral-b33c50-a1b2c3d4", "Oral explanation"),
        ("explain-clarification-abc12-uuid4", "Clarification path"),
        ("explain-comparison-def34-uuid4", "Comparison table"),
        ("explain-memory-ghi56-uuid4", "Memory anchor"),
        ("explain-example-jkl78-uuid4", "Example teaching"),

        # Four-Level Explanation
        ("explain-four-level-b33c-a1b2", "Four-level explanation"),

        # Understanding Check
        ("understand-b33c5066-a1b2c3d4", "Understanding node"),

        # Error Nodes
        ("error-oral-12345678", "Error from oral agent"),
        ("error-scoring-abcd1234", "Error from scoring agent"),

        # Edge IDs
        ("edge-vq-abc12-qd-def34", "Edge between VQ and QD"),
        ("edge-a1b2c3d4-e5f67890", "Edge with hex IDs"),
    ])
    def test_agent_generated_ids_valid(self, node_id: str, description: str):
        """Agent-generated semantic prefix IDs should be accepted."""
        node = NodeRead(
            id=node_id,
            type="text",
            x=0,
            y=0,
            width=100,
            height=100
        )
        assert node.id == node_id, f"Failed for: {description}"

    # =========================================================================
    # Invalid IDs: Should Be Rejected
    # =========================================================================

    @pytest.mark.parametrize("node_id,reason", [
        # Empty or whitespace
        ("", "Empty string"),
        ("   ", "Only whitespace"),

        # Special characters
        ("node@special", "Contains @"),
        ("node#hash", "Contains #"),
        ("node$dollar", "Contains $"),
        ("node%percent", "Contains %"),
        ("node&ampersand", "Contains &"),
        ("node*asterisk", "Contains *"),
        ("node!exclaim", "Contains !"),

        # Spaces
        ("node with spaces", "Contains spaces"),
        ("node id", "Contains space"),
        (" leadingspace", "Leading space"),
        ("trailingspace ", "Trailing space"),

        # Leading hyphen
        ("-starts-with-hyphen", "Starts with hyphen"),
        ("-", "Only hyphen"),
        ("--double-hyphen", "Starts with double hyphen"),

        # Unicode/Non-ASCII
        ("节点id", "Contains Chinese characters"),
        ("nöde", "Contains umlaut"),

        # Brackets and quotes
        ("[bracket]", "Contains brackets"),
        ("(paren)", "Contains parentheses"),
        ("'quote'", "Contains single quotes"),
        ('"doublequote"', "Contains double quotes"),
    ])
    def test_invalid_ids_rejected(self, node_id: str, reason: str):
        """Invalid IDs should raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            NodeRead(
                id=node_id,
                type="text",
                x=0,
                y=0,
                width=100,
                height=100
            )
        assert "id" in str(exc_info.value), f"Expected ID validation error for: {reason}"

    # =========================================================================
    # Edge Cases
    # =========================================================================

    @pytest.mark.parametrize("node_id", [
        "a-b",                # Minimum with hyphen
        "A-B-C-D-E-F",        # Multiple hyphens
        "x" * 100,            # Long ID (no max length defined)
        "0-1-2-3-4-5",        # All numeric with hyphens
        "Z",                  # Single uppercase
    ])
    def test_edge_cases_valid(self, node_id: str):
        """Edge case IDs that should be valid."""
        node = NodeRead(
            id=node_id,
            type="text",
            x=0,
            y=0,
            width=100,
            height=100
        )
        assert node.id == node_id


class TestNodeIdPatternConsistency:
    """Tests ensuring schema consistency between Pydantic and JSON Schema."""

    def test_pattern_matches_json_schema(self):
        """Pydantic pattern should match JSON Schema pattern."""
        import json
        from pathlib import Path

        # Read JSON Schema
        schema_path = Path(__file__).parent.parent.parent.parent / "specs" / "data" / "canvas-node.schema.json"
        with open(schema_path, "r", encoding="utf-8") as f:
            json_schema = json.load(f)

        json_pattern = json_schema["properties"]["id"]["pattern"]

        # Get Pydantic pattern
        pydantic_pattern = NodeRead.model_fields["id"].metadata[0].pattern

        # They should be equivalent (Pydantic adds ^ and $ anchors internally)
        assert json_pattern == pydantic_pattern or \
               json_pattern == f"^{pydantic_pattern}$" or \
               pydantic_pattern == f"^{json_pattern}$", \
               f"Pattern mismatch: JSON={json_pattern}, Pydantic={pydantic_pattern}"
