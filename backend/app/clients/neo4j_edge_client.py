# Canvas Learning System - Neo4j Edge Client
# Story 36.1: Unified Learning Client Architecture
# S34 G-FAKE-001: renamed from Neo4jEdgeClient → Neo4jEdgeClient (actual backend is Neo4j Cypher, not graphiti-core)
"""
Neo4j-backed client for Canvas Edge synchronization.

Story 36.1: Unified Learning Client Architecture
- AC-36.1.2: Neo4jEdgeClient inherits from Neo4jLearningBase
- AC-36.1.3: Neo4jClient injection via constructor (dependency injection)
- AC-36.1.4: Backward compatibility via Neo4jEdgeClientAdapter

Features:
- Neo4j storage via injected Neo4jClient (Story 30.2)
- JSON fallback mode when NEO4J_MOCK=true or NEO4J_ENABLED=false
- Async non-blocking edge sync with 2-second timeout
- Graceful degradation on timeout

[Source: docs/stories/36.1.story.md]
[Source: docs/architecture/decisions/ADR-003-AGENTIC-RAG-ARCHITECTURE.md]
"""

import asyncio
import json
import logging
import warnings
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

# Story 36.1: Import unified base class
from .graphiti_client_base import EdgeRelationship, Neo4jLearningBase

if TYPE_CHECKING:
    from .neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)

# Storage path for learning memories (LearningMemoryClient - independent)
LEARNING_MEMORY_PATH = (
    Path(__file__).parent.parent.parent / "data" / "learning_memories.json"
)

# Re-export EdgeRelationship for backward compatibility
__all__ = [
    "EdgeRelationship",
    "Neo4jEdgeClient",
    "Neo4jEdgeClientAdapter",
    "get_neo4j_edge_client",
    "get_legacy_edge_client",  # Deprecated alias
    "reset_neo4j_edge_client",
    "LearningMemory",
    "LearningMemoryClient",
    "get_learning_memory_client",
    "reset_learning_memory_client",
    # Backward compat aliases (S34 G-FAKE-001) — remove after full migration
    "GraphitiEdgeClient",
    "GraphitiEdgeClientAdapter",
    "get_graphiti_edge_client",
    "get_graphiti_client",
    "reset_graphiti_client",
]


class Neo4jEdgeClient(Neo4jLearningBase):
    """
    Graphiti client for Canvas Edge synchronization.

    Story 36.1 AC-36.1.2: Refactored to inherit from Neo4jLearningBase.

    This client:
    1. Inherits from Neo4jLearningBase (AC-36.1.1)
    2. Receives Neo4jClient via constructor (AC-36.1.3)
    3. Uses self._neo4j.create_edge_relationship() for Neo4j operations
    4. Supports JSON fallback mode when Neo4j is unavailable

    ✅ Verified from ADR-003: Graphiti as knowledge graph middleware
    ✅ Verified from ADR-009: All external calls use tenacity retry (via Neo4jClient)

    [Source: docs/stories/36.1.story.md#Task-2]
    [Source: src/agentic_rag/clients/graphiti_client.py (pattern reference)]
    """

    def __init__(
        self,
        neo4j_client: "Neo4jClient",
        timeout_ms: int = 2000,
        batch_size: int = 10,
    ):
        """
        Initialize Neo4jEdgeClient with Neo4jClient injection.

        Story 36.1 AC-36.1.3: Neo4jClient injection

        Args:
            neo4j_client: Neo4jClient instance from Story 30.2
                         Reuses connection pool (50 connections, 30s timeout)
                         Reuses retry mechanism (tenacity 3x exponential backoff)
            timeout_ms: Timeout for sync operations in milliseconds (default: 2000)
            batch_size: Maximum edges to sync per batch (default: 10)

        Raises:
            ValueError: If neo4j_client is None

        [Source: docs/stories/36.1.story.md#AC-36.1.3]
        """
        super().__init__(neo4j_client)

        self._timeout_ms = timeout_ms
        self._batch_size = batch_size
        self._sync_count = 0
        self._error_count = 0

        logger.debug(
            f"Neo4jEdgeClient initialized with Neo4jClient: "
            f"mode={self._neo4j.stats.get('mode', 'unknown')}, "
            f"timeout={timeout_ms}ms, batch_size={batch_size}"
        )

    @property
    def enabled(self) -> bool:
        """Check if edge sync is enabled (Neo4j or fallback available)."""
        return self._initialized or not self.is_fallback_mode

    @property
    def stats(self) -> Dict[str, Any]:
        """
        Get sync statistics.

        Returns:
            Statistics dict including sync counts and Neo4j stats
        """
        base_stats = self.get_stats()
        return {
            **base_stats,
            "sync_count": self._sync_count,
            "error_count": self._error_count,
            "timeout_ms": self._timeout_ms,
            "batch_size": self._batch_size,
        }

    async def add_edge_relationship(self, relationship: EdgeRelationship) -> bool:
        """
        Add a single edge relationship to the knowledge graph.

        Story 36.1 AC-36.1.2 Task 2.3: Use self._neo4j.run_query() instead of JSON

        Args:
            relationship: EdgeRelationship to add

        Returns:
            True if successful

        [Source: docs/stories/36.1.story.md#Task-2.3]
        """
        if not self._initialized:
            await self.initialize()

        try:
            # ✅ Story 36.1: Delegate to Neo4jClient.create_edge_relationship()
            # This handles both real Neo4j and JSON fallback mode
            success = await self._neo4j.create_edge_relationship(
                canvas_path=relationship.canvas_path,
                edge_id=relationship.edge_id
                or f"edge-{relationship.from_node_id}-{relationship.to_node_id}",
                from_node_id=relationship.from_node_id,
                to_node_id=relationship.to_node_id,
                edge_label=relationship.edge_label,
            )

            if success:
                self._sync_count += 1
                logger.info(
                    f"Graphiti edge sync: {relationship.entity1} "
                    f"--[{relationship.relationship_type}]--> {relationship.entity2}"
                )
            else:
                self._error_count += 1
                logger.warning(
                    f"Graphiti edge sync failed: {relationship.entity1} --> {relationship.entity2}"
                )

            return success

        except (RuntimeError, ConnectionError, asyncio.TimeoutError) as e:
            logger.warning(f"add_edge_relationship failed: {e}")
            self._error_count += 1
            return False

    async def search_nodes(
        self,
        query: str,
        canvas_path: Optional[str] = None,
        group_id: Optional[str] = None,
        entity_types: Optional[List[str]] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Search for nodes in the knowledge graph.

        Story 36.1 AC-36.1.1: Abstract interface implementation
        Enhanced: supports entity_types filter for Claude Code compatibility

        Args:
            query: Search query string
            canvas_path: Optional Canvas file path filter
            group_id: Optional group_id filter for multi-subject isolation
            entity_types: Optional list of entity types (e.g., ["Misconception", "ProblemTrap"])
            limit: Maximum number of results

        Returns:
            List of search results
        """
        if not self._initialized:
            await self.initialize()

        # Round-23 Story 7.3 · Patch 3 — Fulltext fast path (O(log N) Lucene)
        # Fallback to CONTAINS (O(N) 全表扫) if fulltext fails / empty / index missing.
        # Index 'node_search_unified' 在 memory_service.ensure_fulltext_index() startup 创建.
        try:
            ft_results = await self._search_nodes_fulltext(
                query=query,
                canvas_path=canvas_path,
                group_id=group_id,
                entity_types=entity_types,
                limit=limit,
            )
            if ft_results:
                return ft_results
            # 空结果可能 index 不存在 OR 真无命中 — fallback CONTAINS 兜底
        except Exception as e:
            logger.debug(
                f"[Patch 3] fulltext search_nodes failed, falling back to CONTAINS: {e}"
            )

        try:
            # Build Cypher query based on filters
            where_clauses = []
            params: Dict[str, Any] = {"searchTerm": query, "limit": limit}

            if canvas_path:
                where_clauses.append("n.canvas_path = $canvasPath")
                params["canvasPath"] = canvas_path

            if group_id:
                where_clauses.append("n.group_id = $groupId")
                params["groupId"] = group_id

            if entity_types:
                where_clauses.append("n.entity_type IN $entityTypes")
                params["entityTypes"] = entity_types

            # Build text search condition
            text_search = (
                "(n.text CONTAINS $searchTerm OR n.id CONTAINS $searchTerm"
                " OR n.name CONTAINS $searchTerm OR n.episode_body CONTAINS $searchTerm"
                " OR n.concept CONTAINS $searchTerm)"
            )
            if where_clauses:
                combined_where = (
                    f"WHERE {' AND '.join(where_clauses)} AND {text_search}"
                )
            else:
                combined_where = f"WHERE {text_search}"

            # Search both :Node and :EntityNode labels for cross-system compatibility
            cypher_query = f"""
            MATCH (n)
            {combined_where}
            RETURN n.id as node_id, coalesce(n.text, n.episode_body) as content,
                   n.canvas_path as canvas_path, n.group_id as group_id,
                   n.entity_type as entity_type, n.name as name,
                   n.source as source
            LIMIT $limit
            """

            results = await self._neo4j.run_query(cypher_query, **params)

            query_len = max(len(query), 1)
            scored_results = []
            for r in results:
                content = r.get("content", "")
                content_len = max(len(content), 1)
                score = min(query_len / content_len, 1.0)
                scored_results.append(
                    {
                        "doc_id": r.get("node_id", ""),
                        "content": content,
                        "score": round(score, 3),
                        "metadata": {
                            "canvas_path": r.get("canvas_path"),
                            "group_id": r.get("group_id"),
                            "entity_type": r.get("entity_type"),
                            "name": r.get("name"),
                            "source": r.get("source"),
                        },
                    }
                )

            scored_results.sort(key=lambda x: x["score"], reverse=True)
            return scored_results

        except Exception as e:
            # Round-23 Patch 3: 扩大兜底范围 — 任何异常 (含 Exception 基类) 返回 []
            # AC-36.2.4 fail-soft: search_nodes 不应让上层失败, Neo4j 不可用时降级为空结果
            logger.warning(f"search_nodes failed: {e}")
            return []

    async def _search_nodes_fulltext(
        self,
        query: str,
        canvas_path: Optional[str] = None,
        group_id: Optional[str] = None,
        entity_types: Optional[List[str]] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Round-23 Story 7.3 · Patch 3 — fulltext fast path for search_nodes.

        Uses Neo4j fulltext index 'node_search_unified' (覆盖 Node/EntityNode 多字段),
        avoiding O(N) CONTAINS scan. Lucene score 直接返回 (无需长度比启发式).

        Returns empty list if:
        - Fulltext index 'node_search_unified' missing
        - No matches
        - Filter (canvas_path/group_id/entity_types) excludes all results

        Caller (search_nodes) should fallback to CONTAINS on empty/exception.
        """
        # 安全转义 Lucene 保留字符 (+ - && || ! ( ) { } [ ] ^ " ~ * ? : \ /)
        # 简单策略: 加引号 → 整体 phrase match
        escaped = query.replace('"', '\\"')
        lucene_query = (
            f'"{escaped}"'
            if any(c in query for c in '+-&|!(){}[]^"~*?:\\/')
            else escaped
        )

        post_filters = []
        params: Dict[str, Any] = {"searchTerm": lucene_query, "limit": limit}

        if canvas_path:
            post_filters.append("n.canvas_path = $canvasPath")
            params["canvasPath"] = canvas_path
        if group_id:
            post_filters.append("n.group_id = $groupId")
            params["groupId"] = group_id
        if entity_types:
            post_filters.append("n.entity_type IN $entityTypes")
            params["entityTypes"] = entity_types

        where_clause = f"WHERE {' AND '.join(post_filters)}" if post_filters else ""

        cypher_query = f"""
        CALL db.index.fulltext.queryNodes('node_search_unified', $searchTerm)
        YIELD node AS n, score
        {where_clause}
        RETURN n.id as node_id, coalesce(n.text, n.episode_body) as content,
               n.canvas_path as canvas_path, n.group_id as group_id,
               n.entity_type as entity_type, n.name as name,
               n.source as source, score as relevance
        ORDER BY score DESC
        LIMIT $limit
        """

        results = await self._neo4j.run_query(cypher_query, **params)

        scored_results = []
        for r in results:
            content = r.get("content", "") or ""
            raw_score = r.get("relevance", 0.0) or 0.0
            normalized_score = min(float(raw_score) / 10.0, 1.0)
            scored_results.append(
                {
                    "doc_id": r.get("node_id", ""),
                    "content": content,
                    "score": round(normalized_score, 3),
                    "metadata": {
                        "canvas_path": r.get("canvas_path"),
                        "group_id": r.get("group_id"),
                        "entity_type": r.get("entity_type"),
                        "name": r.get("name"),
                        "source": r.get("source"),
                        "search_method": "fulltext",
                    },
                }
            )
        return scored_results

    async def get_related_memories(
        self, node_id: str, canvas_path: Optional[str] = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get memories related to a specific node.

        Story 36.1 AC-36.1.1: Abstract interface implementation

        Args:
            node_id: Node ID to find related memories for
            canvas_path: Optional Canvas file path context
            limit: Maximum number of results

        Returns:
            List of related memory records

        [Source: docs/stories/36.1.story.md#AC-36.1.1]
        """
        if not self._initialized:
            await self.initialize()

        try:
            # Query for connected nodes via edges
            params: Dict[str, Any] = {"nodeId": node_id, "limit": limit}

            if canvas_path:
                cypher_query = """
                MATCH (n:Node {id: $nodeId})-[r:CONNECTS_TO]-(related:Node)
                WHERE n.canvas_path = $canvasPath OR related.canvas_path = $canvasPath
                RETURN related.id as node_id, related.text as content,
                       r.label as relationship, related.canvas_path as canvas_path
                LIMIT $limit
                """
                params["canvasPath"] = canvas_path
            else:
                cypher_query = """
                MATCH (n:Node {id: $nodeId})-[r:CONNECTS_TO]-(related:Node)
                RETURN related.id as node_id, related.text as content,
                       r.label as relationship, related.canvas_path as canvas_path
                LIMIT $limit
                """

            results = await self._neo4j.run_query(cypher_query, **params)

            return [
                {
                    "node_id": r.get("node_id", ""),
                    "content": r.get("content", ""),
                    "relationship": r.get("relationship", "CONNECTED_TO"),
                    "canvas_path": r.get("canvas_path"),
                }
                for r in results
            ]

        except (RuntimeError, ConnectionError, asyncio.TimeoutError) as e:
            logger.warning(f"get_related_memories failed: {e}")
            return []

    async def add_episode_for_edge(
        self, canvas_name: str, edge: Dict[str, Any]
    ) -> bool:
        """
        Add an episode record for an edge (historical tracking).

        Args:
            canvas_name: Canvas file name
            edge: Edge data dict

        Returns:
            True if successful
        """
        try:
            from_node = edge.get("fromNode", "unknown")
            to_node = edge.get("toNode", "unknown")
            label = edge.get("label", "connects")
            edge_id = edge.get("id", f"edge-{from_node}-{to_node}")

            # Create edge relationship
            relationship = EdgeRelationship(
                canvas_path=canvas_name,
                from_node_id=from_node,
                to_node_id=to_node,
                edge_label=label,
                edge_id=edge_id,
            )

            return await self.add_edge_relationship(relationship)

        except (KeyError, AttributeError, TypeError) as e:
            logger.warning(f"add_episode_for_edge failed: {e}")
            return False

    async def sync_canvas_edges(
        self, canvas_name: str, edges: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Sync all edges from a Canvas to Graphiti.

        This is the main entry point for edge synchronization.
        Uses batch processing and timeout for graceful degradation.

        Args:
            canvas_name: Canvas file name
            edges: List of edge dicts from Canvas

        Returns:
            Sync result with success count and errors
        """
        if not edges:
            return {"synced": 0, "skipped": 0, "reason": "no_edges"}

        result = {
            "synced": 0,
            "failed": 0,
            "skipped": 0,
            "timeout": False,
        }

        try:
            timeout_seconds = self._timeout_ms / 1000.0

            async with asyncio.timeout(timeout_seconds):
                if not self._initialized:
                    await self.initialize()

                # Process edges in batches
                for i in range(0, len(edges), self._batch_size):
                    batch = edges[i : i + self._batch_size]

                    for edge in batch:
                        relationship = EdgeRelationship(
                            canvas_path=canvas_name,
                            from_node_id=edge.get("fromNode", ""),
                            to_node_id=edge.get("toNode", ""),
                            edge_label=edge.get("label", ""),
                            edge_id=edge.get("id"),
                        )

                        if await self.add_edge_relationship(relationship):
                            result["synced"] += 1
                        else:
                            result["failed"] += 1

                logger.info(
                    f"Canvas edge sync complete for {canvas_name}: "
                    f"{result['synced']} synced, {result['failed']} failed"
                )

        except asyncio.TimeoutError:
            result["timeout"] = True
            result["skipped"] = len(edges) - result["synced"] - result["failed"]
            logger.warning(
                f"Canvas edge sync timeout for {canvas_name} after {self._timeout_ms}ms"
            )
        except (RuntimeError, ConnectionError) as e:
            result["error"] = str(e)
            logger.error(f"Canvas edge sync error: {e}")

        return result


# =============================================================================
# Story 36.1 AC-36.1.4: Backward Compatibility Adapter
# =============================================================================


class Neo4jEdgeClientAdapter:
    """
    Backward-compatible adapter for legacy Neo4jEdgeClient usage.

    Story 36.1 AC-36.1.4: Allows existing code using old Neo4jEdgeClient()
    signature to continue working while emitting deprecation warnings.

    DEPRECATED: Use Neo4jEdgeClient(neo4j_client) instead.

    [Source: docs/stories/36.1.story.md#Task-5]
    """

    def __init__(
        self,
        timeout_ms: int = 2000,
        enabled: bool = True,
        batch_size: int = 10,
        storage_path: Optional[Path] = None,
    ):
        """
        Initialize adapter with legacy signature.

        Args:
            timeout_ms: Timeout for sync operations in milliseconds
            enabled: Whether edge sync is enabled
            batch_size: Maximum edges to sync per batch
            storage_path: IGNORED - kept for backward compatibility

        DEPRECATED: Use get_neo4j_edge_client() or Neo4jEdgeClient(neo4j_client)
        """
        warnings.warn(
            "Neo4jEdgeClientAdapter is deprecated. "
            "Use get_neo4j_edge_client() from dependencies.py "
            "or Neo4jEdgeClient(neo4j_client) directly.",
            DeprecationWarning,
            stacklevel=2,
        )

        # Import Neo4jClient here to avoid circular imports
        from .neo4j_client import get_neo4j_client

        self._neo4j_client = get_neo4j_client()
        self._client = Neo4jEdgeClient(
            neo4j_client=self._neo4j_client,
            timeout_ms=timeout_ms,
            batch_size=batch_size,
        )
        self._enabled = enabled

    @property
    def enabled(self) -> bool:
        return self._enabled and self._client.enabled

    @property
    def stats(self) -> Dict[str, Any]:
        return self._client.stats

    async def initialize(self) -> bool:
        return await self._client.initialize()

    async def add_edge_relationship(self, relationship) -> bool:
        """Accept both old EdgeRelationship format and new format."""
        # Convert old format to new if needed
        if hasattr(relationship, "canvas_name"):
            # Old format: canvas_name, from_node, to_node
            new_rel = EdgeRelationship(
                canvas_path=relationship.canvas_name,
                from_node_id=relationship.from_node,
                to_node_id=relationship.to_node,
                edge_label=relationship.label,
                edge_id=relationship.edge_id,
            )
            return await self._client.add_edge_relationship(new_rel)
        else:
            return await self._client.add_edge_relationship(relationship)

    async def add_episode_for_edge(self, canvas_name: str, edge: Dict) -> bool:
        return await self._client.add_episode_for_edge(canvas_name, edge)

    async def sync_canvas_edges(self, canvas_name: str, edges: List[Dict]) -> Dict:
        return await self._client.sync_canvas_edges(canvas_name, edges)

    async def cleanup(self) -> None:
        return await self._client.cleanup()


# =============================================================================
# Singleton management
# =============================================================================

_client_instance: Optional[Neo4jEdgeClient] = None


def get_neo4j_edge_client(
    neo4j_client: Optional["Neo4jClient"] = None,
    timeout_ms: int = 2000,
    batch_size: int = 10,
) -> Neo4jEdgeClient:
    """
    Get or create Neo4jEdgeClient singleton.

    Story 36.1: Factory function with Neo4jClient dependency injection.

    Args:
        neo4j_client: Optional Neo4jClient instance (created if not provided)
        timeout_ms: Timeout in milliseconds
        batch_size: Batch size for edge sync

    Returns:
        Neo4jEdgeClient instance

    [Source: docs/stories/36.1.story.md#Task-4.2]
    """
    global _client_instance

    if _client_instance is None:
        if neo4j_client is None:
            from .neo4j_client import get_neo4j_client

            neo4j_client = get_neo4j_client()

        _client_instance = Neo4jEdgeClient(
            neo4j_client=neo4j_client,
            timeout_ms=timeout_ms,
            batch_size=batch_size,
        )

    return _client_instance


def get_legacy_edge_client(
    timeout_ms: int = 2000, enabled: bool = True
) -> Neo4jEdgeClientAdapter:
    """
    DEPRECATED: Get Neo4jEdgeClient with legacy signature.

    Use get_neo4j_edge_client() instead.

    Args:
        timeout_ms: Timeout in milliseconds
        enabled: Whether sync is enabled

    Returns:
        Neo4jEdgeClientAdapter for backward compatibility
    """
    warnings.warn(
        "get_legacy_edge_client() is deprecated. Use get_neo4j_edge_client() instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return Neo4jEdgeClientAdapter(timeout_ms=timeout_ms, enabled=enabled)


def reset_neo4j_edge_client() -> None:
    """Reset singleton instance (for testing)."""
    global _client_instance
    _client_instance = None


# =============================================================================
# LearningMemoryClient - FIX-4.1: 实现真正的记忆系统
# [Source: docs/prd/sprint-change-proposal-20251208.md - Phase 4]
# =============================================================================


@dataclass
class LearningMemory:
    """
    Represents a learning memory/episode.

    Attributes:
        canvas_name: Source canvas file name
        node_id: Node ID being analyzed
        concept: Concept or topic name
        user_understanding: User's understanding/explanation
        score: Score result (if scored)
        agent_feedback: Agent feedback/response
        timestamp: When the learning occurred
    """

    canvas_name: str
    node_id: str
    concept: str
    user_understanding: Optional[str] = None
    score: Optional[float] = None
    agent_feedback: Optional[str] = None
    timestamp: Optional[str] = None

    @property
    def memory_key(self) -> str:
        """Unique key for this memory: canvas:node:timestamp"""
        ts = self.timestamp or datetime.now().isoformat()
        return f"{self.canvas_name}:{self.node_id}:{ts}"


class LearningMemoryClient:
    """
    Client for storing and retrieving learning memories.

    FIX-4.1: Replaces mock memory implementation with actual storage.
    Provides search functionality for context injection into Agent prompts.

    [Source: docs/prd/sprint-change-proposal-20251208.md - Phase 4]
    """

    def __init__(
        self, storage_path: Optional[Path] = None, max_search_results: int = 5
    ):
        """
        Initialize LearningMemoryClient.

        Args:
            storage_path: Path to JSON storage file
            max_search_results: Maximum memories to return from search
        """
        self._storage_path = storage_path or LEARNING_MEMORY_PATH
        self._max_results = max_search_results
        self._data: Dict[str, Any] = {"memories": [], "metadata": {}}
        self._initialized = False
        logger.debug(f"LearningMemoryClient initialized: storage={self._storage_path}")

    async def initialize(self) -> bool:
        """
        Initialize client and load existing data.

        Returns:
            True if initialization successful
        """
        if self._initialized:
            return True

        try:
            self._storage_path.parent.mkdir(parents=True, exist_ok=True)

            if self._storage_path.exists():
                with open(self._storage_path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
                logger.info(
                    f"Loaded {len(self._data.get('memories', []))} learning memories"
                )
            else:
                self._data = {
                    "memories": [],
                    "metadata": {
                        "created_at": datetime.now().isoformat(),
                        "version": "1.0",
                    },
                }
                await self._save_data()
                logger.info(f"Created new memory storage: {self._storage_path}")

            self._initialized = True
            return True
        except (json.JSONDecodeError, ValueError, OSError, IOError) as e:
            logger.error(f"LearningMemoryClient init failed: {e}")
            return False

    async def _save_data(self) -> None:
        """Save data to JSON storage file."""
        try:
            with open(self._storage_path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
        except (OSError, IOError, TypeError) as e:
            logger.error(f"Failed to save learning memories: {e}")

    async def add_learning_episode(self, memory: LearningMemory) -> bool:
        """
        Add a learning episode to memory.

        Args:
            memory: LearningMemory to store

        Returns:
            True if successful
        """
        if not self._initialized:
            await self.initialize()

        try:
            memory_data = {
                "key": memory.memory_key,
                "canvas_name": memory.canvas_name,
                "node_id": memory.node_id,
                "concept": memory.concept,
                "user_understanding": memory.user_understanding,
                "score": memory.score,
                "agent_feedback": memory.agent_feedback,
                "timestamp": memory.timestamp or datetime.now().isoformat(),
            }

            self._data["memories"].append(memory_data)
            await self._save_data()

            logger.info(
                f"Added learning episode: {memory.canvas_name}/{memory.concept}"
            )
            return True
        except (OSError, IOError, TypeError, ValueError) as e:
            logger.error(f"Failed to add learning episode: {e}")
            return False

    async def search_memories(
        self,
        query: str,
        canvas_name: Optional[str] = None,
        node_id: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant learning memories.

        FIX-4.1: Enables Agent to access historical learning context.

        Args:
            query: Search query (matches concept, user_understanding)
            canvas_name: Optional filter by canvas
            node_id: Optional filter by node
            limit: Maximum results (default: self._max_results)

        Returns:
            List of matching memory dicts, sorted by relevance
        """
        if not self._initialized:
            await self.initialize()

        max_results = limit or self._max_results
        query_lower = query.lower()
        results = []

        for memory in self._data.get("memories", []):
            # Filter by canvas if specified
            if canvas_name and memory.get("canvas_name") != canvas_name:
                continue

            # Filter by node if specified
            if node_id and memory.get("node_id") != node_id:
                continue

            # Calculate relevance score
            relevance = 0.0
            concept = memory.get("concept", "").lower()
            understanding = memory.get("user_understanding", "").lower()

            # Exact match on concept
            if query_lower == concept:
                relevance = 1.0
            elif query_lower in concept:
                relevance = 0.8
            elif query_lower in understanding:
                relevance = 0.6
            else:
                # Word overlap
                query_words = set(query_lower.split())
                concept_words = set(concept.split())
                understanding_words = set(understanding.split())

                concept_overlap = len(query_words & concept_words) / max(
                    len(query_words), 1
                )
                understanding_overlap = len(query_words & understanding_words) / max(
                    len(query_words), 1
                )
                relevance = max(concept_overlap * 0.7, understanding_overlap * 0.5)

            if relevance > 0.1:
                results.append({**memory, "relevance": relevance})

        # Sort by relevance (descending) and timestamp (recent first)
        results.sort(
            key=lambda x: (-x["relevance"], x.get("timestamp", "")), reverse=False
        )

        return results[:max_results]

    async def get_learning_history(
        self, canvas_name: str, node_id: Optional[str] = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get learning history for a canvas/node.

        Args:
            canvas_name: Canvas file name
            node_id: Optional node ID filter
            limit: Maximum records

        Returns:
            List of learning memories, most recent first
        """
        if not self._initialized:
            await self.initialize()

        results = []
        for memory in self._data.get("memories", []):
            if memory.get("canvas_name") != canvas_name:
                continue
            if node_id and memory.get("node_id") != node_id:
                continue
            results.append(memory)

        # Sort by timestamp (recent first)
        results.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return results[:limit]

    def format_for_context(
        self, memories: List[Dict[str, Any]], max_chars: int = 1000
    ) -> str:
        """
        Format memories for inclusion in Agent context.

        Args:
            memories: List of memory dicts
            max_chars: Maximum characters in output

        Returns:
            Formatted context string
        """
        if not memories:
            return ""

        parts = ["--- 历史学习记录 (Learning History) ---"]
        total_chars = len(parts[0])

        for memory in memories:
            entry = (
                f"[{memory.get('timestamp', 'unknown')[:10]}] "
                f"{memory.get('concept', '未知概念')}"
            )

            # Add score if available
            if memory.get("score") is not None:
                entry += f" (得分: {memory['score']:.1f}/40)"

            # Add brief understanding if available
            understanding = memory.get("user_understanding", "")
            if understanding:
                preview = (
                    understanding[:100] + "..."
                    if len(understanding) > 100
                    else understanding
                )
                entry += f"\n  理解: {preview}"

            if total_chars + len(entry) + 1 > max_chars:
                break

            parts.append(entry)
            total_chars += len(entry) + 1

        return "\n".join(parts)

    @property
    def stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        return {
            "total_memories": len(self._data.get("memories", [])),
            "storage_path": str(self._storage_path),
            "initialized": self._initialized,
        }

    async def cleanup(self) -> None:
        """Cleanup client resources."""
        logger.debug(
            f"LearningMemoryClient cleanup: {self.stats['total_memories']} memories"
        )
        self._initialized = False


# Singleton instance for LearningMemoryClient
_learning_memory_instance: Optional[LearningMemoryClient] = None


def get_learning_memory_client(
    storage_path: Optional[Path] = None,
) -> LearningMemoryClient:
    """
    Get or create LearningMemoryClient singleton.

    Args:
        storage_path: Optional storage path override

    Returns:
        LearningMemoryClient instance
    """
    global _learning_memory_instance

    if _learning_memory_instance is None:
        _learning_memory_instance = LearningMemoryClient(storage_path=storage_path)

    return _learning_memory_instance


def reset_learning_memory_client() -> None:
    """Reset singleton instance (for testing)."""
    global _learning_memory_instance
    _learning_memory_instance = None


# =============================================================================
# Backward compatibility aliases (S34 G-FAKE-001 migration)
# Remove after all imports are updated to new names
# =============================================================================
GraphitiEdgeClient = Neo4jEdgeClient
GraphitiEdgeClientAdapter = Neo4jEdgeClientAdapter
get_graphiti_edge_client = get_neo4j_edge_client
get_graphiti_client = get_legacy_edge_client
reset_graphiti_client = reset_neo4j_edge_client
