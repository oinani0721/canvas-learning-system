# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: testing)
"""
Unit tests for Story 12.E.3: 2-hop Context Traversal Implementation
[Source: docs/stories/story-12.E.3-2hop-context-traversal.md]

Tests:
- AC 3.1: AdjacentNode has hop_distance field
- AC 3.2: 2-hop traversal discovers grandparent nodes
- AC 3.3: Cycle prevention with visited set
- AC 3.4: Performance requirements (< 100ms for 100 nodes)
- AC 3.5: Backward compatibility with 1-hop default
"""
import time
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.services.canvas_service import CanvasService
from app.services.context_enrichment_service import (
    AdjacentNode,
    ContextEnrichmentService,
)

# Performance test constants
PERF_TIMEOUT_MS = 100  # Maximum allowed traversal time in milliseconds
PERF_LARGE_GRAPH_NODES = 100  # Node count for large graph test
PERF_DENSE_GRAPH_NODES = 20  # Node count for dense graph test
PERF_DENSE_MAX_CONNECTIONS = 5  # Max connections per node in dense graph

# ============================================================================
# AC 3.1: AdjacentNode hop_distance Field Tests
# ============================================================================

class TestAdjacentNodeHopDistance:
    """Tests for AdjacentNode dataclass hop_distance field (AC 3.1)"""

    def test_adjacent_node_has_hop_distance_default(self):
        """Test that AdjacentNode has hop_distance field with default value 1."""
        # Act
        adj = AdjacentNode(
            node={"id": "n1", "text": "Test node"},
            relation="parent",
            edge_label="defines"
        )

        # Assert - default should be 1 (backward compatible)
        assert hasattr(adj, "hop_distance")
        assert adj.hop_distance == 1

    def test_adjacent_node_hop_distance_custom_value(self):
        """Test that hop_distance can be set to custom values."""
        # Act
        adj2 = AdjacentNode(
            node={"id": "n2", "text": "Grandparent node"},
            relation="parent",
            edge_label="explains",
            hop_distance=2
        )

        # Assert
        assert adj2.hop_distance == 2

    def test_adjacent_node_hop_distance_child_relation(self):
        """Test hop_distance works with child relation."""
        # Act
        adj = AdjacentNode(
            node={"id": "c1", "text": "Child node"},
            relation="child",
            edge_label="follows",
            hop_distance=1
        )

        # Assert
        assert adj.relation == "child"
        assert adj.hop_distance == 1


# ============================================================================
# AC 3.2: 2-hop Traversal Tests
# ============================================================================

class TestTwoHopTraversal:
    """Tests for 2-hop context traversal (AC 3.2)"""

    @pytest.fixture
    def mock_canvas_service(self) -> MagicMock:
        """Create mock CanvasService with canvas_base_path."""
        mock = MagicMock(spec=CanvasService)
        mock.canvas_base_path = "/mock/vault/path"
        return mock

    @pytest.fixture
    def service(self, mock_canvas_service: MagicMock) -> ContextEnrichmentService:
        """Create ContextEnrichmentService instance."""
        return ContextEnrichmentService(canvas_service=mock_canvas_service)

    def test_2hop_discovers_grandparent_nodes(self, service: ContextEnrichmentService):
        """
        Test 2-hop discovers grandparent nodes.

        Graph Structure:
        A --[defines]--> B --[explains]--> C (target)

        When calling _find_adjacent_nodes(node_id="C", hop_depth=2):
        - B should be found with hop_distance=1, relation="parent"
        - A should be found with hop_distance=2, relation="parent"
        """
        # Arrange
        nodes = {
            "A": {"id": "A", "type": "text", "text": "Root concept (grandparent)"},
            "B": {"id": "B", "type": "text", "text": "Intermediate node (parent)"},
            "C": {"id": "C", "type": "text", "text": "Target node"}
        }
        edges = [
            {"fromNode": "A", "toNode": "B", "label": "defines"},
            {"fromNode": "B", "toNode": "C", "label": "explains"}
        ]

        # Act
        result = service._find_adjacent_nodes("C", nodes, edges, hop_depth=2)

        # Assert
        assert len(result) == 2

        hop1_nodes = [n for n in result if n.hop_distance == 1]
        hop2_nodes = [n for n in result if n.hop_distance == 2]

        assert len(hop1_nodes) == 1  # B
        assert len(hop2_nodes) == 1  # A

        assert hop1_nodes[0].node["id"] == "B"
        assert hop1_nodes[0].relation == "parent"
        assert hop1_nodes[0].edge_label == "explains"

        assert hop2_nodes[0].node["id"] == "A"
        assert hop2_nodes[0].relation == "parent"
        assert hop2_nodes[0].edge_label == "defines"

    def test_2hop_discovers_grandchild_nodes(self, service: ContextEnrichmentService):
        """
        Test 2-hop discovers grandchild nodes.

        Graph Structure:
        A (target) --[leads_to]--> B --[extends]--> C

        When calling _find_adjacent_nodes(node_id="A", hop_depth=2):
        - B should be found with hop_distance=1, relation="child"
        - C should be found with hop_distance=2, relation="child"
        """
        # Arrange
        nodes = {
            "A": {"id": "A", "type": "text", "text": "Target node"},
            "B": {"id": "B", "type": "text", "text": "Child node"},
            "C": {"id": "C", "type": "text", "text": "Grandchild node"}
        }
        edges = [
            {"fromNode": "A", "toNode": "B", "label": "leads_to"},
            {"fromNode": "B", "toNode": "C", "label": "extends"}
        ]

        # Act
        result = service._find_adjacent_nodes("A", nodes, edges, hop_depth=2)

        # Assert
        assert len(result) == 2

        hop1_nodes = [n for n in result if n.hop_distance == 1]
        hop2_nodes = [n for n in result if n.hop_distance == 2]

        assert len(hop1_nodes) == 1  # B
        assert len(hop2_nodes) == 1  # C

        assert hop1_nodes[0].node["id"] == "B"
        assert hop1_nodes[0].relation == "child"

        assert hop2_nodes[0].node["id"] == "C"
        assert hop2_nodes[0].relation == "child"

    def test_2hop_mixed_relations(self, service: ContextEnrichmentService):
        """
        Test 2-hop with mixed parent and child relations.

        Graph Structure:
        P2 --[prereq]--> P1 --[defines]--> T --[explains]--> C1 --[leads]--> C2
        (grandparent)   (parent)        (target)  (child)         (grandchild)
        """
        # Arrange
        nodes = {
            "P2": {"id": "P2", "type": "text", "text": "Grandparent"},
            "P1": {"id": "P1", "type": "text", "text": "Parent"},
            "T": {"id": "T", "type": "text", "text": "Target"},
            "C1": {"id": "C1", "type": "text", "text": "Child"},
            "C2": {"id": "C2", "type": "text", "text": "Grandchild"}
        }
        edges = [
            {"fromNode": "P2", "toNode": "P1", "label": "prereq"},
            {"fromNode": "P1", "toNode": "T", "label": "defines"},
            {"fromNode": "T", "toNode": "C1", "label": "explains"},
            {"fromNode": "C1", "toNode": "C2", "label": "leads"}
        ]

        # Act
        result = service._find_adjacent_nodes("T", nodes, edges, hop_depth=2)

        # Assert
        assert len(result) == 4  # P1, P2, C1, C2

        parents = [n for n in result if n.relation == "parent"]
        children = [n for n in result if n.relation == "child"]

        assert len(parents) == 2
        assert len(children) == 2

        # Check hop distances
        parent_ids = {n.node["id"]: n.hop_distance for n in parents}
        child_ids = {n.node["id"]: n.hop_distance for n in children}

        assert parent_ids["P1"] == 1
        assert parent_ids["P2"] == 2
        assert child_ids["C1"] == 1
        assert child_ids["C2"] == 2

    def test_2hop_sorted_by_hop_distance(self, service: ContextEnrichmentService):
        """Test that results are sorted by hop_distance (closer nodes first)."""
        # Arrange
        nodes = {
            "A": {"id": "A", "type": "text", "text": "Grandparent"},
            "B": {"id": "B", "type": "text", "text": "Parent"},
            "C": {"id": "C", "type": "text", "text": "Target"}
        }
        edges = [
            {"fromNode": "A", "toNode": "B"},
            {"fromNode": "B", "toNode": "C"}
        ]

        # Act
        result = service._find_adjacent_nodes("C", nodes, edges, hop_depth=2)

        # Assert - sorted by hop_distance
        hop_distances = [n.hop_distance for n in result]
        assert hop_distances == sorted(hop_distances)  # Should be [1, 2]


# ============================================================================
# AC 3.3: Cycle Prevention Tests
# ============================================================================

class TestCyclePrevention:
    """Tests for cycle prevention with visited set (AC 3.3)"""

    @pytest.fixture
    def mock_canvas_service(self) -> MagicMock:
        """Create mock CanvasService."""
        mock = MagicMock(spec=CanvasService)
        mock.canvas_base_path = "/mock/vault/path"
        return mock

    @pytest.fixture
    def service(self, mock_canvas_service: MagicMock) -> ContextEnrichmentService:
        """Create ContextEnrichmentService instance."""
        return ContextEnrichmentService(canvas_service=mock_canvas_service)

    def test_2hop_no_cycle_in_circular_graph(self, service: ContextEnrichmentService):
        """
        Test that circular graph does not cause infinite loop.

        Circular Graph:
        A ---> B ---> C ---> A (cycle!)

        Should not infinite loop, each node visited only once.
        """
        # Arrange
        nodes = {
            "A": {"id": "A", "type": "text", "text": "Node A"},
            "B": {"id": "B", "type": "text", "text": "Node B"},
            "C": {"id": "C", "type": "text", "text": "Node C"}
        }
        edges = [
            {"fromNode": "A", "toNode": "B"},
            {"fromNode": "B", "toNode": "C"},
            {"fromNode": "C", "toNode": "A"}  # Creates cycle
        ]

        # Act - should complete without hanging
        result = service._find_adjacent_nodes("A", nodes, edges, hop_depth=2)

        # Assert
        # No duplicate nodes
        node_ids = [n.node["id"] for n in result]
        assert len(node_ids) == len(set(node_ids)), "No duplicates should exist"

        # Should find B (1-hop) and C (2-hop), but not A again
        assert "A" not in node_ids
        assert "B" in node_ids
        assert "C" in node_ids

    def test_2hop_no_duplicate_nodes(self, service: ContextEnrichmentService):
        """Test that duplicate nodes are not returned."""
        # Arrange - diamond pattern
        #     A
        #    / \
        #   B   C
        #    \ /
        #     D (target)
        nodes = {
            "A": {"id": "A", "type": "text", "text": "Root"},
            "B": {"id": "B", "type": "text", "text": "Left"},
            "C": {"id": "C", "type": "text", "text": "Right"},
            "D": {"id": "D", "type": "text", "text": "Target"}
        }
        edges = [
            {"fromNode": "A", "toNode": "B"},
            {"fromNode": "A", "toNode": "C"},
            {"fromNode": "B", "toNode": "D"},
            {"fromNode": "C", "toNode": "D"}
        ]

        # Act
        result = service._find_adjacent_nodes("D", nodes, edges, hop_depth=2)

        # Assert - no duplicates
        node_ids = [n.node["id"] for n in result]
        assert len(node_ids) == len(set(node_ids))

        # A should appear only once even though reachable via B and C
        assert node_ids.count("A") <= 1

    def test_2hop_self_loop_ignored(self, service: ContextEnrichmentService):
        """Test that self-loops are handled correctly."""
        # Arrange
        nodes = {
            "A": {"id": "A", "type": "text", "text": "Node A"},
            "B": {"id": "B", "type": "text", "text": "Node B"}
        }
        edges = [
            {"fromNode": "A", "toNode": "B"},
            {"fromNode": "A", "toNode": "A"}  # Self-loop
        ]

        # Act
        result = service._find_adjacent_nodes("A", nodes, edges, hop_depth=2)

        # Assert - target node should not be in results
        node_ids = [n.node["id"] for n in result]
        assert "A" not in node_ids
        assert "B" in node_ids


# ============================================================================
# AC 3.4: Performance Tests
# ============================================================================

class TestPerformance:
    """Tests for performance requirements (AC 3.4)"""

    @pytest.fixture
    def mock_canvas_service(self) -> MagicMock:
        """Create mock CanvasService."""
        mock = MagicMock(spec=CanvasService)
        mock.canvas_base_path = "/mock/vault/path"
        return mock

    @pytest.fixture
    def service(self, mock_canvas_service: MagicMock) -> ContextEnrichmentService:
        """Create ContextEnrichmentService instance."""
        return ContextEnrichmentService(canvas_service=mock_canvas_service)

    @pytest.mark.performance
    def test_2hop_performance_100_nodes(self, service: ContextEnrichmentService):
        """
        Test that 2-hop traversal on 100-node Canvas completes within 100ms.

        Large Canvas performance test.
        """
        # Arrange - Generate large canvas with complex edges
        nodes = {f"n{i}": {"id": f"n{i}", "type": "text", "text": f"Node {i}"} for i in range(PERF_LARGE_GRAPH_NODES)}
        edges = []
        for i in range(PERF_LARGE_GRAPH_NODES - 1):
            edges.append({"fromNode": f"n{i}", "toNode": f"n{i+1}"})
            # Add some cross-links for complexity
            if i % 3 == 0 and i + 2 < PERF_LARGE_GRAPH_NODES:
                edges.append({"fromNode": f"n{i}", "toNode": f"n{i+2}"})

        # Act
        start = time.time()
        result = service._find_adjacent_nodes("n50", nodes, edges, hop_depth=2)
        elapsed_ms = (time.time() - start) * 1000

        # Assert
        assert elapsed_ms < PERF_TIMEOUT_MS, f"Too slow: {elapsed_ms:.2f}ms (should be < {PERF_TIMEOUT_MS}ms)"
        assert len(result) > 0  # Should find some adjacent nodes

    @pytest.mark.performance
    def test_2hop_performance_dense_graph(self, service: ContextEnrichmentService):
        """Test performance on a dense graph (many edges per node)."""
        # Arrange - Dense graph with many interconnections
        nodes = {f"n{i}": {"id": f"n{i}", "type": "text", "text": f"Node {i}"} for i in range(PERF_DENSE_GRAPH_NODES)}
        edges = []
        # Create dense connections
        for i in range(PERF_DENSE_GRAPH_NODES):
            for j in range(i + 1, min(i + PERF_DENSE_MAX_CONNECTIONS, PERF_DENSE_GRAPH_NODES)):
                edges.append({"fromNode": f"n{i}", "toNode": f"n{j}"})

        # Act
        start = time.time()
        _result = service._find_adjacent_nodes("n10", nodes, edges, hop_depth=2)
        elapsed_ms = (time.time() - start) * 1000

        # Assert
        assert elapsed_ms < PERF_TIMEOUT_MS, f"Too slow: {elapsed_ms:.2f}ms"


# ============================================================================
# AC 3.5: Backward Compatibility Tests
# ============================================================================

class TestBackwardCompatibility:
    """Tests for backward compatibility with 1-hop default (AC 3.5)"""

    @pytest.fixture
    def mock_canvas_service(self) -> MagicMock:
        """Create mock CanvasService."""
        mock = MagicMock(spec=CanvasService)
        mock.canvas_base_path = "/mock/vault/path"
        return mock

    @pytest.fixture
    def service(self, mock_canvas_service: MagicMock) -> ContextEnrichmentService:
        """Create ContextEnrichmentService instance."""
        return ContextEnrichmentService(canvas_service=mock_canvas_service)

    def test_1hop_backward_compatible(self, service: ContextEnrichmentService):
        """
        Test that hop_depth=1 (default) behaves exactly as before.
        """
        # Arrange
        nodes = {
            "A": {"id": "A", "type": "text", "text": "Grandparent"},
            "B": {"id": "B", "type": "text", "text": "Parent"},
            "C": {"id": "C", "type": "text", "text": "Target"}
        }
        edges = [
            {"fromNode": "A", "toNode": "B"},
            {"fromNode": "B", "toNode": "C"}
        ]

        # Act - default hop_depth=1
        result = service._find_adjacent_nodes("B", nodes, edges)

        # Assert
        assert len(result) == 2  # A (parent) and C (child)
        assert all(n.hop_distance == 1 for n in result)

        node_ids = {n.node["id"] for n in result}
        assert "A" in node_ids
        assert "C" in node_ids

    def test_1hop_explicit_parameter(self, service: ContextEnrichmentService):
        """Test that explicit hop_depth=1 works the same as default."""
        # Arrange
        nodes = {
            "A": {"id": "A", "type": "text", "text": "Parent"},
            "B": {"id": "B", "type": "text", "text": "Target"},
            "C": {"id": "C", "type": "text", "text": "Child"}
        }
        edges = [
            {"fromNode": "A", "toNode": "B"},
            {"fromNode": "B", "toNode": "C"}
        ]

        # Act
        result_default = service._find_adjacent_nodes("B", nodes, edges)
        result_explicit = service._find_adjacent_nodes("B", nodes, edges, hop_depth=1)

        # Assert - should be identical
        assert len(result_default) == len(result_explicit)
        default_ids = {n.node["id"] for n in result_default}
        explicit_ids = {n.node["id"] for n in result_explicit}
        assert default_ids == explicit_ids

    def test_1hop_only_returns_direct_neighbors(self, service: ContextEnrichmentService):
        """Test that 1-hop only returns direct neighbors, not 2-hop."""
        # Arrange
        nodes = {
            "GP": {"id": "GP", "type": "text", "text": "Grandparent"},
            "P": {"id": "P", "type": "text", "text": "Parent"},
            "T": {"id": "T", "type": "text", "text": "Target"},
            "C": {"id": "C", "type": "text", "text": "Child"},
            "GC": {"id": "GC", "type": "text", "text": "Grandchild"}
        }
        edges = [
            {"fromNode": "GP", "toNode": "P"},
            {"fromNode": "P", "toNode": "T"},
            {"fromNode": "T", "toNode": "C"},
            {"fromNode": "C", "toNode": "GC"}
        ]

        # Act - 1-hop
        result = service._find_adjacent_nodes("T", nodes, edges, hop_depth=1)

        # Assert - only P and C, not GP or GC
        node_ids = {n.node["id"] for n in result}
        assert node_ids == {"P", "C"}
        assert "GP" not in node_ids
        assert "GC" not in node_ids


# ============================================================================
# Integration Tests (using enrich_with_adjacent_nodes)
# ============================================================================

class TestEnrichWithAdjacentNodes2Hop:
    """Integration tests for 2-hop through enrich_with_adjacent_nodes method."""

    @pytest.fixture
    def mock_canvas_service(self) -> MagicMock:
        """Create mock CanvasService."""
        mock = MagicMock(spec=CanvasService)
        mock.canvas_base_path = "/mock/vault/path"
        mock.read_canvas = AsyncMock(return_value={
            "nodes": [
                {"id": "A", "type": "text", "text": "Grandparent concept", "x": 0, "y": 0},
                {"id": "B", "type": "text", "text": "Parent concept", "x": 100, "y": 0},
                {"id": "C", "type": "text", "text": "Target concept", "x": 200, "y": 0},
            ],
            "edges": [
                {"fromNode": "A", "toNode": "B", "label": "defines"},
                {"fromNode": "B", "toNode": "C", "label": "explains"},
            ]
        })
        return mock

    @pytest.fixture
    def service(self, mock_canvas_service: MagicMock) -> ContextEnrichmentService:
        """Create ContextEnrichmentService instance."""
        return ContextEnrichmentService(canvas_service=mock_canvas_service)

    @pytest.mark.asyncio
    async def test_enrich_with_2hop_adjacent_nodes(
        self,
        service: ContextEnrichmentService,
    ):
        """Test enrich_with_adjacent_nodes with hop_depth=2."""
        # Act
        result = await service.enrich_with_adjacent_nodes(
            canvas_name="test-canvas",
            node_id="C",
            hop_depth=2,
            include_graphiti=False,
        )

        # Assert
        assert result is not None
        assert len(result.adjacent_nodes) == 2  # B (1-hop) and A (2-hop)

        hop1 = [n for n in result.adjacent_nodes if n.hop_distance == 1]
        hop2 = [n for n in result.adjacent_nodes if n.hop_distance == 2]

        assert len(hop1) == 1
        assert len(hop2) == 1
        assert hop1[0].node["id"] == "B"
        assert hop2[0].node["id"] == "A"

    @pytest.mark.asyncio
    async def test_enriched_context_contains_2hop_labels(
        self,
        service: ContextEnrichmentService,
    ):
        """Test that enriched_context string contains 2-hop node labels."""
        # Act
        result = await service.enrich_with_adjacent_nodes(
            canvas_name="test-canvas",
            node_id="C",
            hop_depth=2,
            include_graphiti=False,
        )

        # Assert - check that 2-hop is indicated in the context
        assert "parent-2hop" in result.enriched_context or "Grandparent" in result.enriched_context
