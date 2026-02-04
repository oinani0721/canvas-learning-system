# Canvas Learning System - Graphiti Client Base
# Story 36.1: 统一GraphitiClient架构
# AC-36.1.1: 统一基类创建
"""
GraphitiClientBase - Abstract base class for unified Graphiti client architecture.

Story 36.1: Unified GraphitiClient Architecture
- AC-36.1.1: Create GraphitiClientBase abstract class with unified interface
- AC-36.1.3: Neo4jClient injection via constructor (dependency injection)

The base class:
1. Receives Neo4jClient via constructor (dependency injection)
2. Defines abstract interface for add_edge_relationship(), search_nodes(), get_related_memories()
3. Prohibits direct AsyncGraphDatabase.driver() creation inside GraphitiClient

Architecture:
    Neo4jClient (Story 30.2 implemented)
        ↓ dependency injection
    GraphitiClientBase (this file)
        ↓ inheritance
    ├── GraphitiEdgeClient (refactored)
    └── GraphitiTemporalClient (refactored)

[Source: docs/stories/36.1.story.md]
[Source: docs/architecture/decisions/ADR-003-AGENTIC-RAG-ARCHITECTURE.md]
[Source: docs/architecture/decisions/ADR-009-ERROR-HANDLING-RETRY-STRATEGY.md]
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import logging

# Type hint import - avoid circular dependency
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)


@dataclass
class EdgeRelationship:
    """
    Represents a Canvas edge relationship for Graphiti.

    Verified from specs/data/graphiti-entity.schema.json:
    - Required: uuid, name, entity_type, created_at
    - Optional: group_id (multi-subject isolation), attributes, summary

    Attributes:
        canvas_path: Canvas file path (e.g., "笔记库/数学/离散数学.canvas")
        from_node_id: Source node ID
        to_node_id: Target node ID
        edge_label: Edge label/relationship type (default: "CONNECTED_TO")
        edge_id: Original edge ID from Canvas
        group_id: Optional group_id for multi-subject isolation (AC-30.8.1)
    """
    canvas_path: str
    from_node_id: str
    to_node_id: str
    edge_label: str = "CONNECTED_TO"
    edge_id: Optional[str] = None
    group_id: Optional[str] = None

    @property
    def entity1(self) -> str:
        """Graphiti entity1 format: node:{canvas_path}:{nodeId}"""
        # Sanitize canvas_path for Neo4j node naming
        safe_path = self.canvas_path.replace("/", "_").replace("\\", "_")
        return f"node:{safe_path}:{self.from_node_id}"

    @property
    def entity2(self) -> str:
        """Graphiti entity2 format: node:{canvas_path}:{nodeId}"""
        safe_path = self.canvas_path.replace("/", "_").replace("\\", "_")
        return f"node:{safe_path}:{self.to_node_id}"

    @property
    def relationship_type(self) -> str:
        """
        Normalize relationship type for Neo4j.

        Verified from Cypher naming convention:
        - Uppercase with underscores
        - No spaces or hyphens
        """
        if not self.edge_label:
            return "CONNECTED_TO"
        # Convert label to uppercase with underscores
        return self.edge_label.upper().replace(" ", "_").replace("-", "_")


class GraphitiClientBase(ABC):
    """
    Abstract base class for Graphiti clients with Neo4jClient dependency injection.

    Story 36.1 AC-36.1.1: Create GraphitiClientBase abstract class

    This class:
    1. Defines unified interface for Graphiti operations
    2. Receives Neo4jClient via constructor (dependency injection)
    3. Prohibits direct AsyncGraphDatabase.driver() creation

    ✅ Verified from ADR-003: Graphiti as knowledge graph middleware, Neo4j as storage
    ✅ Verified from ADR-009: All external calls must use tenacity retry

    Usage:
        class GraphitiEdgeClient(GraphitiClientBase):
            async def add_edge_relationship(self, relationship: EdgeRelationship) -> bool:
                # Use self._neo4j.run_query() for Neo4j operations
                ...

    [Source: docs/stories/36.1.story.md#AC-36.1.1]
    [Source: docs/architecture/decisions/ADR-003-AGENTIC-RAG-ARCHITECTURE.md]
    """

    def __init__(self, neo4j_client: "Neo4jClient"):
        """
        Initialize GraphitiClientBase with Neo4jClient injection.

        Story 36.1 AC-36.1.3: Neo4jClient injection
        - Reuse Story 30.2 connection pool (50 connections, 30s timeout)
        - Reuse existing retry mechanism (tenacity 3x exponential backoff)
        - Reuse existing JSON fallback (NEO4J_MOCK=true)

        Args:
            neo4j_client: Neo4jClient instance from Story 30.2
                         Must not be None - use dependency injection

        Raises:
            ValueError: If neo4j_client is None

        [Source: docs/stories/36.1.story.md#AC-36.1.3]
        """
        if neo4j_client is None:
            raise ValueError(
                "neo4j_client cannot be None. "
                "Use dependency injection via get_graphiti_client() in dependencies.py"
            )

        self._neo4j = neo4j_client
        self._initialized = False

        logger.debug(
            f"{self.__class__.__name__} initialized with Neo4jClient: "
            f"mode={self._neo4j.stats.get('mode', 'unknown')}"
        )

    @property
    def neo4j_client(self) -> "Neo4jClient":
        """
        Expose underlying Neo4jClient instance.

        Story 36.1 AC-36.1.1 Task 1.4: @property def neo4j_client

        Returns:
            Neo4jClient: The injected Neo4j client instance
        """
        return self._neo4j

    @property
    def is_neo4j_enabled(self) -> bool:
        """Check if Neo4j is enabled (not in fallback mode)."""
        return self._neo4j.enabled

    @property
    def is_fallback_mode(self) -> bool:
        """Check if using JSON fallback mode."""
        return self._neo4j.is_fallback_mode

    async def initialize(self) -> bool:
        """
        Initialize the client.

        Calls Neo4jClient.initialize() if not already initialized.

        Returns:
            True if initialization successful
        """
        if self._initialized:
            return True

        result = await self._neo4j.initialize()
        self._initialized = result

        logger.info(
            f"{self.__class__.__name__} initialized: "
            f"neo4j_mode={self._neo4j.stats.get('mode', 'unknown')}"
        )

        return result

    # =========================================================================
    # Abstract Methods - Must be implemented by subclasses
    # Story 36.1 AC-36.1.1 Task 1.2: Define abstract interface
    # =========================================================================

    @abstractmethod
    async def add_edge_relationship(self, relationship: EdgeRelationship) -> bool:
        """
        Add a single edge relationship to the knowledge graph.

        Story 36.1 AC-36.1.1 Task 1.2: Abstract interface definition

        The implementation should:
        1. Use self._neo4j.run_query() for Neo4j operations
        2. Handle JSON fallback mode gracefully
        3. Follow retry mechanism from ADR-009

        Args:
            relationship: EdgeRelationship instance containing:
                - canvas_path: Canvas file path
                - from_node_id: Source node ID
                - to_node_id: Target node ID
                - edge_label: Relationship type
                - edge_id: Original edge ID
                - group_id: Optional multi-subject isolation ID

        Returns:
            True if relationship was created/updated successfully

        [Source: docs/stories/36.1.story.md#AC-36.1.1]
        """
        pass

    @abstractmethod
    async def search_nodes(
        self,
        query: str,
        canvas_path: Optional[str] = None,
        group_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for nodes in the knowledge graph.

        Story 36.1 AC-36.1.1 Task 1.2: Abstract interface definition

        The implementation should:
        1. Use self._neo4j.run_query() for Cypher queries
        2. Support optional canvas_path and group_id filters
        3. Return standardized SearchResult format

        Args:
            query: Search query string
            canvas_path: Optional Canvas file path filter
            group_id: Optional group_id filter for multi-subject isolation
            limit: Maximum number of results

        Returns:
            List of search results, each containing:
            - doc_id: Unique document identifier
            - content: Node content/text
            - score: Relevance score (0-1)
            - metadata: Additional metadata

        [Source: docs/stories/36.1.story.md#AC-36.1.1]
        """
        pass

    @abstractmethod
    async def get_related_memories(
        self,
        node_id: str,
        canvas_path: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get memories related to a specific node.

        Story 36.1 AC-36.1.1 Task 1.2: Abstract interface definition

        The implementation should:
        1. Query the knowledge graph for node relationships
        2. Return related concepts, learning episodes, etc.

        Args:
            node_id: Node ID to find related memories for
            canvas_path: Optional Canvas file path context
            limit: Maximum number of results

        Returns:
            List of related memory records

        [Source: docs/stories/36.1.story.md#AC-36.1.1]
        """
        pass

    # =========================================================================
    # Common Methods - Shared implementations
    # =========================================================================

    async def health_check(self) -> bool:
        """
        Perform health check on underlying Neo4j connection.

        Returns:
            True if healthy
        """
        return await self._neo4j.health_check()

    def get_stats(self) -> Dict[str, Any]:
        """
        Get client statistics.

        Returns:
            Statistics dict including:
            - class_name: Name of the concrete class
            - initialized: Whether client is initialized
            - neo4j_stats: Underlying Neo4jClient stats
        """
        return {
            "class_name": self.__class__.__name__,
            "initialized": self._initialized,
            "is_neo4j_enabled": self.is_neo4j_enabled,
            "is_fallback_mode": self.is_fallback_mode,
            "neo4j_stats": self._neo4j.stats,
        }

    async def cleanup(self) -> None:
        """
        Cleanup client resources.

        Note: Does NOT cleanup Neo4jClient as it's shared via DI.
        """
        logger.debug(f"{self.__class__.__name__} cleanup")
        self._initialized = False


# =============================================================================
# Exported symbols
# =============================================================================

__all__ = [
    "GraphitiClientBase",
    "EdgeRelationship",
]
