# Story 36.1: Graphiti Client Unification - AC Coverage Tests
"""
Tests for AC-36.1.2: Import redirection validation.

Verifies that the unified GraphitiEdgeClient can be imported from
the expected module path.

[Source: docs/stories/36.1.story.md#AC-36.1.2]
"""

import pytest


class TestImportRedirection:
    """AC-36.1.2: Verify import paths resolve correctly."""

    def test_graphiti_edge_client_importable(self):
        """AC-36.1.2: GraphitiEdgeClient importable from app.clients.graphiti_client."""
        from app.clients.graphiti_client import GraphitiEdgeClient
        assert GraphitiEdgeClient is not None

    def test_edge_relationship_importable(self):
        """AC-36.1.2: EdgeRelationship importable from graphiti_client_base."""
        from app.clients.graphiti_client_base import EdgeRelationship
        assert EdgeRelationship is not None

    def test_learning_memory_client_importable(self):
        """AC-36.1.2: LearningMemoryClient importable from app.clients.graphiti_client."""
        from app.clients.graphiti_client import LearningMemoryClient
        assert LearningMemoryClient is not None

    def test_get_graphiti_edge_client_importable(self):
        """AC-36.1.2: Factory function importable."""
        from app.clients.graphiti_client import get_graphiti_edge_client
        assert callable(get_graphiti_edge_client)
