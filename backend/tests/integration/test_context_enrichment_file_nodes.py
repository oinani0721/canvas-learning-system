# Story 12.D.2: Integration tests for FILE node content in context enrichment
#
# [Source: ADR-008 - pytest testing framework]
# [Source: specs/data/canvas-node.schema.json - Canvas node types]
"""
Integration tests verifying FILE node content flows through the context enrichment pipeline.

Tests verify that:
1. _build_enriched_context() includes FILE node content
2. Agent prompts contain file content from FILE type nodes
3. Adjacent FILE nodes are properly resolved
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from app.services.context_enrichment_service import AdjacentNode, ContextEnrichmentService


@pytest.fixture
def mock_canvas_service(tmp_path):
    """Create mock canvas service with test vault path."""
    service = MagicMock()
    service.canvas_base_path = str(tmp_path)
    return service


@pytest.fixture
def test_vault(tmp_path):
    """Create test vault with sample files."""
    # Create oral explanation file
    oral_file = tmp_path / "explanations" / "oral-explanation.md"
    oral_file.parent.mkdir(parents=True, exist_ok=True)
    oral_file.write_text(
        "# Oral Explanation\n\n"
        "This is the oral explanation of the concept.\n"
        "It helps students understand through verbal description.",
        encoding="utf-8"
    )

    # Create another explanation file
    deep_file = tmp_path / "deep-dive.md"
    deep_file.write_text(
        "# Deep Dive Analysis\n\n"
        "Detailed analysis of the topic with examples.",
        encoding="utf-8"
    )

    return tmp_path


class TestBuildEnrichedContextWithFileNodes:
    """Tests for _build_enriched_context() with FILE type nodes."""

    def test_file_node_content_in_target(self, mock_canvas_service, test_vault):
        """Target FILE node content is included in context."""
        mock_canvas_service.canvas_base_path = str(test_vault)

        service = ContextEnrichmentService(
            canvas_service=mock_canvas_service
        )

        # FILE type target node
        target_node = {
            "id": "file_target",
            "type": "file",
            "file": "explanations/oral-explanation.md",
            "x": 100,
            "y": 200,
            "color": "2"
        }

        result = service._build_enriched_context(target_node, [])

        assert "# Oral Explanation" in result
        assert "oral explanation of the concept" in result
        assert "[目标节点" in result

    def test_file_node_content_in_adjacent_parent(self, mock_canvas_service, test_vault):
        """Adjacent FILE node content is included as parent."""
        mock_canvas_service.canvas_base_path = str(test_vault)

        service = ContextEnrichmentService(
            canvas_service=mock_canvas_service
        )

        target_node = {
            "id": "text_target",
            "type": "text",
            "text": "Main concept node",
            "x": 100,
            "y": 200
        }

        # FILE type parent node
        parent_file_node = {
            "id": "file_parent",
            "type": "file",
            "file": "deep-dive.md",
            "x": 100,
            "y": 100
        }

        adjacent_nodes = [
            AdjacentNode(
                node=parent_file_node,
                relation="parent",
                edge_label="explains"
            )
        ]

        result = service._build_enriched_context(target_node, adjacent_nodes)

        assert "Main concept node" in result
        assert "# Deep Dive Analysis" in result
        assert "[parent|explains]" in result

    def test_file_node_content_in_adjacent_child(self, mock_canvas_service, test_vault):
        """Adjacent FILE node content is included as child."""
        mock_canvas_service.canvas_base_path = str(test_vault)

        service = ContextEnrichmentService(
            canvas_service=mock_canvas_service
        )

        target_node = {
            "id": "text_target",
            "type": "text",
            "text": "Parent concept",
            "x": 100,
            "y": 100
        }

        # FILE type child node
        child_file_node = {
            "id": "file_child",
            "type": "file",
            "file": "explanations/oral-explanation.md",
            "x": 100,
            "y": 200
        }

        adjacent_nodes = [
            AdjacentNode(
                node=child_file_node,
                relation="child",
                edge_label="detailed_by"
            )
        ]

        result = service._build_enriched_context(target_node, adjacent_nodes)

        assert "Parent concept" in result
        assert "# Oral Explanation" in result
        assert "[child|detailed_by]" in result

    def test_mixed_node_types_in_context(self, mock_canvas_service, test_vault):
        """Mix of text and file nodes all contribute content."""
        mock_canvas_service.canvas_base_path = str(test_vault)

        service = ContextEnrichmentService(
            canvas_service=mock_canvas_service
        )

        # TEXT type target
        target_node = {
            "id": "text_target",
            "type": "text",
            "text": "Central concept being studied",
            "x": 200,
            "y": 200
        }

        # TEXT type parent
        text_parent = {
            "id": "text_parent",
            "type": "text",
            "text": "Prerequisite knowledge",
            "x": 100,
            "y": 100
        }

        # FILE type parent
        file_parent = {
            "id": "file_parent",
            "type": "file",
            "file": "deep-dive.md",
            "x": 300,
            "y": 100
        }

        # FILE type child
        file_child = {
            "id": "file_child",
            "type": "file",
            "file": "explanations/oral-explanation.md",
            "x": 200,
            "y": 300
        }

        adjacent_nodes = [
            AdjacentNode(node=text_parent, relation="parent", edge_label="requires"),
            AdjacentNode(node=file_parent, relation="parent", edge_label="see_also"),
            AdjacentNode(node=file_child, relation="child", edge_label="explained_in"),
        ]

        result = service._build_enriched_context(target_node, adjacent_nodes)

        # Target text content
        assert "Central concept being studied" in result

        # Text parent content
        assert "Prerequisite knowledge" in result

        # File parent content
        assert "Deep Dive Analysis" in result

        # File child content
        assert "Oral Explanation" in result

    def test_missing_file_graceful_degradation(self, mock_canvas_service, test_vault):
        """Missing file returns empty content without breaking context."""
        mock_canvas_service.canvas_base_path = str(test_vault)

        service = ContextEnrichmentService(
            canvas_service=mock_canvas_service
        )

        target_node = {
            "id": "text_target",
            "type": "text",
            "text": "Main content",
            "x": 100,
            "y": 200
        }

        # FILE node pointing to non-existent file
        missing_file_node = {
            "id": "missing_file",
            "type": "file",
            "file": "nonexistent/file.md",
            "x": 100,
            "y": 100
        }

        adjacent_nodes = [
            AdjacentNode(node=missing_file_node, relation="parent", edge_label="ref")
        ]

        # Should not raise exception
        result = service._build_enriched_context(target_node, adjacent_nodes)

        # Target content still present
        assert "Main content" in result
        # Parent label still present (with empty content)
        assert "[parent|ref]" in result


class TestEnrichWithAdjacentNodesFileSupport:
    """Integration tests for full enrichment flow with FILE nodes."""

    @pytest.mark.asyncio
    async def test_file_node_in_enriched_context(self, mock_canvas_service, test_vault):
        """FILE node content flows through enrich_with_adjacent_nodes()."""
        mock_canvas_service.canvas_base_path = str(test_vault)

        # Setup mock read_canvas response with FILE type node
        canvas_data = {
            "nodes": [
                {
                    "id": "file_node_1",
                    "type": "file",
                    "file": "explanations/oral-explanation.md",
                    "x": 100,
                    "y": 200,
                    "width": 300,
                    "height": 200
                },
                {
                    "id": "text_node_1",
                    "type": "text",
                    "text": "Related concept",
                    "x": 100,
                    "y": 100
                }
            ],
            "edges": [
                {
                    "id": "edge_1",
                    "fromNode": "text_node_1",
                    "toNode": "file_node_1",
                    "label": "explains"
                }
            ]
        }

        mock_canvas_service.read_canvas = AsyncMock(return_value=canvas_data)

        service = ContextEnrichmentService(
            canvas_service=mock_canvas_service
        )

        result = await service.enrich_with_adjacent_nodes(
            canvas_name="test_canvas",
            node_id="file_node_1"
        )

        # The enriched context should contain file content
        assert "Oral Explanation" in result.enriched_context
        assert result.target_node["type"] == "file"
