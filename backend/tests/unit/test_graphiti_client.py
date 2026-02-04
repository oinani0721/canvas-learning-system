"""
Unit tests for GraphitiClient with Neo4jClient dependency injection.

Story 36.1: 统一GraphitiClient架构
- AC-36.1.1: 统一基类创建 (GraphitiClientBase)
- AC-36.1.2: 代码合并 (GraphitiEdgeClient继承基类)
- AC-36.1.3: Neo4jClient注入 (构造函数DI)
- AC-36.1.4: 向后兼容 (GraphitiEdgeClientAdapter)
- AC-36.1.5: 代码消重 (统一导入路径)

[Source: docs/stories/36.1.story.md]
[Source: docs/architecture/decisions/ADR-003-AGENTIC-RAG-ARCHITECTURE.md]
"""

import asyncio
import pytest
import warnings
from unittest.mock import AsyncMock, MagicMock, patch

import pytest_asyncio

from app.clients.graphiti_client_base import (
    GraphitiClientBase,
    EdgeRelationship,
)
from app.clients.graphiti_client import (
    GraphitiEdgeClient,
    GraphitiEdgeClientAdapter,
)
from app.clients.neo4j_client import Neo4jClient


# =============================================================================
# Test EdgeRelationship DataClass
# =============================================================================

class TestEdgeRelationship:
    """Test EdgeRelationship dataclass - AC-36.1.1."""

    def test_basic_creation(self):
        """Test basic EdgeRelationship creation."""
        rel = EdgeRelationship(
            canvas_path="数学/离散数学.canvas",
            from_node_id="node1",
            to_node_id="node2",
        )

        assert rel.canvas_path == "数学/离散数学.canvas"
        assert rel.from_node_id == "node1"
        assert rel.to_node_id == "node2"
        assert rel.edge_label == "CONNECTED_TO"  # default
        assert rel.edge_id is None
        assert rel.group_id is None

    def test_with_optional_fields(self):
        """Test EdgeRelationship with all optional fields."""
        rel = EdgeRelationship(
            canvas_path="physics/mechanics.canvas",
            from_node_id="nodeA",
            to_node_id="nodeB",
            edge_label="DEPENDS_ON",
            edge_id="edge-123",
            group_id="physics",
        )

        assert rel.edge_label == "DEPENDS_ON"
        assert rel.edge_id == "edge-123"
        assert rel.group_id == "physics"

    def test_entity1_property(self):
        """Test entity1 property generates correct format."""
        rel = EdgeRelationship(
            canvas_path="笔记库/数学/代数.canvas",
            from_node_id="concept-1",
            to_node_id="concept-2",
        )

        # Path should be sanitized (/ and \ replaced with _)
        assert rel.entity1 == "node:笔记库_数学_代数.canvas:concept-1"

    def test_entity2_property(self):
        """Test entity2 property generates correct format."""
        rel = EdgeRelationship(
            canvas_path="test/sub\\path.canvas",
            from_node_id="node1",
            to_node_id="node2",
        )

        # Both / and \ should be sanitized
        assert rel.entity2 == "node:test_sub_path.canvas:node2"

    def test_relationship_type_property(self):
        """Test relationship_type normalization."""
        # Default label
        rel1 = EdgeRelationship(
            canvas_path="test.canvas",
            from_node_id="a",
            to_node_id="b",
        )
        assert rel1.relationship_type == "CONNECTED_TO"

        # Custom label with spaces
        rel2 = EdgeRelationship(
            canvas_path="test.canvas",
            from_node_id="a",
            to_node_id="b",
            edge_label="depends on",
        )
        assert rel2.relationship_type == "DEPENDS_ON"

        # Custom label with hyphens
        rel3 = EdgeRelationship(
            canvas_path="test.canvas",
            from_node_id="a",
            to_node_id="b",
            edge_label="is-related-to",
        )
        assert rel3.relationship_type == "IS_RELATED_TO"

        # Empty label should return default
        rel4 = EdgeRelationship(
            canvas_path="test.canvas",
            from_node_id="a",
            to_node_id="b",
            edge_label="",
        )
        assert rel4.relationship_type == "CONNECTED_TO"


# =============================================================================
# Test GraphitiClientBase Abstract Class
# =============================================================================

class TestGraphitiClientBase:
    """Test GraphitiClientBase abstract class - AC-36.1.1."""

    def test_cannot_instantiate_directly(self):
        """Test that GraphitiClientBase cannot be instantiated directly."""
        mock_neo4j = MagicMock(spec=Neo4jClient)
        mock_neo4j.stats = {"mode": "BOLT"}

        with pytest.raises(TypeError):
            # Should fail because abstract methods not implemented
            GraphitiClientBase(mock_neo4j)

    def test_requires_neo4j_client(self):
        """Test that None neo4j_client raises ValueError."""
        # Create a concrete subclass for testing
        class ConcreteClient(GraphitiClientBase):
            async def add_edge_relationship(self, relationship):
                pass

            async def search_nodes(self, query, canvas_path=None, group_id=None, limit=10):
                return []

            async def get_related_memories(self, node_id, canvas_path=None, limit=10):
                return []

        with pytest.raises(ValueError) as exc_info:
            ConcreteClient(None)

        assert "neo4j_client cannot be None" in str(exc_info.value)


# =============================================================================
# Test GraphitiEdgeClient with Dependency Injection
# =============================================================================

class TestGraphitiEdgeClientDependencyInjection:
    """Test GraphitiEdgeClient dependency injection - AC-36.1.3."""

    def test_injection_with_neo4j_client(self):
        """Test GraphitiEdgeClient accepts Neo4jClient via constructor."""
        mock_neo4j = MagicMock(spec=Neo4jClient)
        mock_neo4j.stats = {"mode": "BOLT", "uri": "bolt://localhost:7687"}
        mock_neo4j.enabled = True
        mock_neo4j.is_fallback_mode = False

        client = GraphitiEdgeClient(neo4j_client=mock_neo4j)

        assert client._neo4j is mock_neo4j
        assert client.neo4j_client is mock_neo4j
        assert client.is_neo4j_enabled is True
        assert client.is_fallback_mode is False

    def test_injection_with_fallback_mode(self):
        """Test GraphitiEdgeClient with fallback mode Neo4jClient."""
        mock_neo4j = MagicMock(spec=Neo4jClient)
        mock_neo4j.stats = {"mode": "JSON_FALLBACK"}
        mock_neo4j.enabled = False
        mock_neo4j.is_fallback_mode = True

        client = GraphitiEdgeClient(neo4j_client=mock_neo4j)

        assert client.is_neo4j_enabled is False
        assert client.is_fallback_mode is True

    def test_custom_timeout_and_batch_size(self):
        """Test GraphitiEdgeClient with custom timeout and batch_size."""
        mock_neo4j = MagicMock(spec=Neo4jClient)
        mock_neo4j.stats = {"mode": "BOLT"}

        client = GraphitiEdgeClient(
            neo4j_client=mock_neo4j,
            timeout_ms=5000,
            batch_size=20,
        )

        assert client._timeout_ms == 5000
        assert client._batch_size == 20


class TestGraphitiEdgeClientMethods:
    """Test GraphitiEdgeClient method implementations."""

    @pytest.fixture
    def mock_neo4j_client(self):
        """Create a mock Neo4jClient for testing."""
        mock = MagicMock(spec=Neo4jClient)
        mock.stats = {"mode": "BOLT", "uri": "bolt://localhost:7687"}
        mock.enabled = True
        mock.is_fallback_mode = False
        mock.initialize = AsyncMock(return_value=True)
        mock.create_edge_relationship = AsyncMock(return_value=True)
        mock.run_query = AsyncMock(return_value=[])
        mock.health_check = AsyncMock(return_value=True)
        return mock

    @pytest.fixture
    def graphiti_client(self, mock_neo4j_client):
        """Create GraphitiEdgeClient with mock Neo4jClient."""
        return GraphitiEdgeClient(neo4j_client=mock_neo4j_client)

    @pytest.mark.asyncio
    async def test_initialize_delegates_to_neo4j(self, graphiti_client, mock_neo4j_client):
        """Test initialize() calls Neo4jClient.initialize()."""
        result = await graphiti_client.initialize()

        assert result is True
        mock_neo4j_client.initialize.assert_awaited_once()
        assert graphiti_client._initialized is True

    @pytest.mark.asyncio
    async def test_add_edge_relationship(self, graphiti_client, mock_neo4j_client):
        """Test add_edge_relationship delegates to Neo4jClient."""
        relationship = EdgeRelationship(
            canvas_path="test.canvas",
            from_node_id="node1",
            to_node_id="node2",
            edge_label="CONNECTED_TO",
            edge_id="edge-001",
        )

        result = await graphiti_client.add_edge_relationship(relationship)

        assert result is True
        mock_neo4j_client.create_edge_relationship.assert_awaited_once()
        call_kwargs = mock_neo4j_client.create_edge_relationship.call_args.kwargs
        assert call_kwargs["canvas_path"] == "test.canvas"
        assert call_kwargs["from_node_id"] == "node1"
        assert call_kwargs["to_node_id"] == "node2"
        assert call_kwargs["edge_label"] == "CONNECTED_TO"

    @pytest.mark.asyncio
    async def test_search_nodes(self, graphiti_client, mock_neo4j_client):
        """Test search_nodes returns expected format."""
        mock_neo4j_client.run_query = AsyncMock(return_value=[
            {"id": "node1", "content": "Test content", "score": 0.9}
        ])

        results = await graphiti_client.search_nodes(
            query="test query",
            canvas_path="test.canvas",
            limit=5
        )

        assert isinstance(results, list)
        # The actual implementation details may vary

    @pytest.mark.asyncio
    async def test_health_check_delegates_to_neo4j(self, graphiti_client, mock_neo4j_client):
        """Test health_check() calls Neo4jClient.health_check()."""
        result = await graphiti_client.health_check()

        assert result is True
        mock_neo4j_client.health_check.assert_awaited_once()

    def test_get_stats(self, graphiti_client, mock_neo4j_client):
        """Test get_stats returns expected structure."""
        stats = graphiti_client.get_stats()

        assert "class_name" in stats
        assert stats["class_name"] == "GraphitiEdgeClient"
        assert "initialized" in stats
        assert "is_neo4j_enabled" in stats
        assert "is_fallback_mode" in stats
        assert "neo4j_stats" in stats


# =============================================================================
# Test GraphitiEdgeClientAdapter (Backward Compatibility) - AC-36.1.4
# =============================================================================

class TestGraphitiEdgeClientAdapter:
    """Test backward-compatible GraphitiEdgeClientAdapter - AC-36.1.4."""

    def test_deprecation_warning(self):
        """Test that adapter emits deprecation warning."""
        # Patch at the source module where it's imported from
        with patch("app.clients.neo4j_client.get_neo4j_client") as mock_get:
            mock_neo4j = MagicMock(spec=Neo4jClient)
            mock_neo4j.stats = {"mode": "BOLT"}
            mock_neo4j.enabled = True
            mock_neo4j.is_fallback_mode = False
            mock_get.return_value = mock_neo4j

            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                adapter = GraphitiEdgeClientAdapter()

                assert len(w) >= 1
                deprecation_warnings = [x for x in w if issubclass(x.category, DeprecationWarning)]
                assert len(deprecation_warnings) >= 1
                assert any("deprecated" in str(x.message).lower() for x in deprecation_warnings)

    def test_adapter_creates_internal_client(self):
        """Test adapter creates GraphitiEdgeClient internally."""
        with patch("app.clients.neo4j_client.get_neo4j_client") as mock_get:
            mock_neo4j = MagicMock(spec=Neo4jClient)
            mock_neo4j.stats = {"mode": "BOLT"}
            mock_neo4j.enabled = True
            mock_neo4j.is_fallback_mode = False
            mock_get.return_value = mock_neo4j

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                adapter = GraphitiEdgeClientAdapter()

                assert hasattr(adapter, "_client")
                assert isinstance(adapter._client, GraphitiEdgeClient)

    @pytest.mark.asyncio
    async def test_adapter_delegates_methods(self):
        """Test adapter delegates method calls to internal client."""
        with patch("app.clients.neo4j_client.get_neo4j_client") as mock_get:
            mock_neo4j = MagicMock(spec=Neo4jClient)
            mock_neo4j.stats = {"mode": "BOLT"}
            mock_neo4j.enabled = True
            mock_neo4j.is_fallback_mode = False
            mock_neo4j.initialize = AsyncMock(return_value=True)
            mock_neo4j.create_edge_relationship = AsyncMock(return_value=True)
            mock_get.return_value = mock_neo4j

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                adapter = GraphitiEdgeClientAdapter()

                # Test initialize
                result = await adapter.initialize()
                assert result is True
                mock_neo4j.initialize.assert_awaited_once()

                # Test add_edge_relationship
                rel = EdgeRelationship(
                    canvas_path="test.canvas",
                    from_node_id="a",
                    to_node_id="b",
                )
                edge_result = await adapter.add_edge_relationship(rel)
                assert edge_result is True


# =============================================================================
# Test Import Paths (AC-36.1.5)
# =============================================================================

class TestUnifiedImports:
    """Test unified import paths work correctly - AC-36.1.5."""

    def test_import_from_backend_clients(self):
        """Test imports from backend/app/clients work."""
        from app.clients.graphiti_client_base import (
            GraphitiClientBase,
            EdgeRelationship,
        )
        from app.clients.graphiti_client import (
            GraphitiEdgeClient,
            GraphitiEdgeClientAdapter,
        )

        assert GraphitiClientBase is not None
        assert EdgeRelationship is not None
        assert GraphitiEdgeClient is not None
        assert GraphitiEdgeClientAdapter is not None

    def test_edgerelationship_fields(self):
        """Test EdgeRelationship has expected fields from schema."""
        rel = EdgeRelationship(
            canvas_path="test.canvas",
            from_node_id="a",
            to_node_id="b",
            edge_label="TEST",
            edge_id="e1",
            group_id="math",
        )

        # Verify all fields from graphiti-entity.schema.json
        assert hasattr(rel, "canvas_path")
        assert hasattr(rel, "from_node_id")
        assert hasattr(rel, "to_node_id")
        assert hasattr(rel, "edge_label")
        assert hasattr(rel, "edge_id")
        assert hasattr(rel, "group_id")  # AC-30.8.1 multi-subject isolation


# =============================================================================
# Test Connection Pool Reuse (AC-36.1.3)
# =============================================================================

class TestConnectionPoolReuse:
    """Test that GraphitiEdgeClient reuses Neo4jClient connection pool."""

    def test_multiple_clients_same_pool(self):
        """Test multiple GraphitiEdgeClients share same Neo4jClient."""
        # Single Neo4jClient instance
        mock_neo4j = MagicMock(spec=Neo4jClient)
        mock_neo4j.stats = {"mode": "BOLT", "pool_size": 50}
        mock_neo4j.enabled = True
        mock_neo4j.is_fallback_mode = False

        # Create multiple GraphitiEdgeClients with same Neo4jClient
        client1 = GraphitiEdgeClient(neo4j_client=mock_neo4j)
        client2 = GraphitiEdgeClient(neo4j_client=mock_neo4j)
        client3 = GraphitiEdgeClient(neo4j_client=mock_neo4j)

        # All should reference the same Neo4jClient
        assert client1._neo4j is client2._neo4j
        assert client2._neo4j is client3._neo4j
        assert client1._neo4j is mock_neo4j

    def test_no_direct_driver_creation(self):
        """Test GraphitiEdgeClient doesn't create its own driver."""
        mock_neo4j = MagicMock(spec=Neo4jClient)
        mock_neo4j.stats = {"mode": "BOLT"}
        mock_neo4j.enabled = True
        mock_neo4j.is_fallback_mode = False

        client = GraphitiEdgeClient(neo4j_client=mock_neo4j)

        # Should not have _driver attribute (uses _neo4j instead)
        assert not hasattr(client, "_driver")
        assert hasattr(client, "_neo4j")
