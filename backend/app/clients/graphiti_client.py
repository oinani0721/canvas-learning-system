# Canvas Learning System - Graphiti Edge Client
# ✅ Verified pattern from src/agentic_rag/clients/graphiti_client.py
# ✅ P1.2 FIXED: Now actually stores data to JSON file
"""
Lightweight Graphiti client for Canvas Edge synchronization.

Phase 4.2: Option B - Canvas内部Edge存入Graphiti
Syncs Canvas edges to Graphiti knowledge graph for cross-session queries.

Features:
- Async non-blocking edge sync
- 2-second timeout with graceful degradation
- JSON file storage (compatible with MCP graphiti-memory format)
- Ready for Neo4j upgrade

[Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Phase-4-Edge-Enhancement]
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Default storage path for edge relationships
DEFAULT_STORAGE_PATH = Path(__file__).parent.parent.parent / "data" / "graphiti_edges.json"
# Storage path for learning memories
LEARNING_MEMORY_PATH = Path(__file__).parent.parent.parent / "data" / "learning_memories.json"


@dataclass
class EdgeRelationship:
    """
    Represents a Canvas edge relationship for Graphiti.

    Attributes:
        canvas_name: Source canvas file name
        from_node: Source node ID
        to_node: Target node ID
        label: Edge label/relationship type
        edge_id: Original edge ID from Canvas
    """
    canvas_name: str
    from_node: str
    to_node: str
    label: str = "CONNECTED_TO"
    edge_id: Optional[str] = None

    @property
    def entity1(self) -> str:
        """Graphiti entity1 format: node:{canvas}:{nodeId}"""
        return f"node:{self.canvas_name}:{self.from_node}"

    @property
    def entity2(self) -> str:
        """Graphiti entity2 format: node:{canvas}:{nodeId}"""
        return f"node:{self.canvas_name}:{self.to_node}"

    @property
    def relationship_type(self) -> str:
        """Normalize relationship type for Neo4j"""
        if not self.label:
            return "CONNECTED_TO"
        # Convert label to uppercase with underscores
        return self.label.upper().replace(" ", "_").replace("-", "_")


class GraphitiEdgeClient:
    """
    Lightweight Graphiti client for Canvas Edge synchronization.

    This client wraps MCP tool calls for edge relationships,
    providing async support with timeout and graceful degradation.

    [Source: src/agentic_rag/clients/graphiti_client.py (pattern reference)]
    """

    def __init__(
        self,
        timeout_ms: int = 2000,
        enabled: bool = True,
        batch_size: int = 10,
        storage_path: Optional[Path] = None
    ):
        """
        Initialize GraphitiEdgeClient.

        Args:
            timeout_ms: Timeout for sync operations in milliseconds
            enabled: Whether edge sync is enabled
            batch_size: Maximum edges to sync per batch
            storage_path: Path to JSON storage file (default: backend/data/graphiti_edges.json)
        """
        self._timeout_ms = timeout_ms
        self._enabled = enabled
        self._batch_size = batch_size
        self._storage_path = storage_path or DEFAULT_STORAGE_PATH
        self._initialized = False
        self._mcp_available = False
        self._sync_count = 0
        self._error_count = 0
        self._data: Dict[str, Any] = {"relationships": [], "episodes": []}
        logger.debug(
            f"GraphitiEdgeClient initialized: "
            f"enabled={enabled}, timeout={timeout_ms}ms, storage={self._storage_path}"
        )

    @property
    def enabled(self) -> bool:
        """Check if edge sync is enabled"""
        return self._enabled

    @property
    def stats(self) -> Dict[str, Any]:
        """Get sync statistics"""
        return {
            "enabled": self._enabled,
            "initialized": self._initialized,
            "mcp_available": self._mcp_available,
            "sync_count": self._sync_count,
            "error_count": self._error_count,
            "storage_path": str(self._storage_path),
            "total_relationships": len(self._data.get("relationships", [])),
            "total_episodes": len(self._data.get("episodes", [])),
        }

    async def initialize(self) -> bool:
        """
        Initialize client and load existing data from storage.

        Returns:
            True if storage is available
        """
        if self._initialized:
            return self._mcp_available

        try:
            # Ensure storage directory exists
            self._storage_path.parent.mkdir(parents=True, exist_ok=True)

            # Load existing data if file exists
            if self._storage_path.exists():
                with open(self._storage_path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
                logger.info(
                    f"Loaded {len(self._data.get('relationships', []))} relationships "
                    f"from {self._storage_path}"
                )
            else:
                # Initialize empty storage file
                self._data = {"relationships": [], "episodes": []}
                await self._save_data()
                logger.info(f"Created new storage file: {self._storage_path}")

            self._mcp_available = self._enabled
            self._initialized = True
            logger.info(
                f"GraphitiEdgeClient initialized: storage={self._storage_path}"
            )
            return self._mcp_available
        except Exception as e:
            logger.warning(f"GraphitiEdgeClient init failed: {e}")
            self._mcp_available = False
            self._initialized = True
            return False

    async def _save_data(self) -> None:
        """Save data to JSON storage file."""
        try:
            with open(self._storage_path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save data: {e}")

    async def add_edge_relationship(
        self,
        relationship: EdgeRelationship
    ) -> bool:
        """
        Add a single edge relationship to Graphiti storage.

        Args:
            relationship: EdgeRelationship to add

        Returns:
            True if successful
        """
        if not self._enabled:
            return False

        if not self._initialized:
            await self.initialize()

        if not self._mcp_available:
            return False

        try:
            # ✅ P1.2 FIXED: Actually store the relationship
            rel_data = {
                "entity1": relationship.entity1,
                "entity2": relationship.entity2,
                "relationship_type": relationship.relationship_type,
                "canvas_name": relationship.canvas_name,
                "from_node": relationship.from_node,
                "to_node": relationship.to_node,
                "label": relationship.label,
                "edge_id": relationship.edge_id,
                "created_at": datetime.now().isoformat(),
            }

            # Check for duplicate (same entity1, entity2, relationship_type)
            existing = next(
                (r for r in self._data["relationships"]
                 if r["entity1"] == rel_data["entity1"]
                 and r["entity2"] == rel_data["entity2"]
                 and r["relationship_type"] == rel_data["relationship_type"]),
                None
            )

            if existing:
                # Update existing relationship
                existing.update(rel_data)
                logger.debug(f"Updated existing relationship: {relationship.entity1} --> {relationship.entity2}")
            else:
                # Add new relationship
                self._data["relationships"].append(rel_data)
                logger.info(
                    f"Graphiti edge sync: {relationship.entity1} "
                    f"--[{relationship.relationship_type}]--> {relationship.entity2}"
                )

            # Save to file
            await self._save_data()
            self._sync_count += 1
            return True
        except Exception as e:
            logger.warning(f"add_edge_relationship failed: {e}")
            self._error_count += 1
            return False

    async def add_episode_for_edge(
        self,
        canvas_name: str,
        edge: Dict[str, Any]
    ) -> bool:
        """
        Add an episode record for an edge (historical tracking).

        Args:
            canvas_name: Canvas file name
            edge: Edge data dict

        Returns:
            True if successful
        """
        if not self._enabled:
            return False

        if not self._initialized:
            await self.initialize()

        try:
            from_node = edge.get("fromNode", "unknown")
            to_node = edge.get("toNode", "unknown")
            label = edge.get("label", "connects")

            content = (
                f"Canvas edge in {canvas_name}: "
                f"{from_node} --[{label}]--> {to_node}"
            )

            # ✅ P1.2 FIXED: Actually store the episode
            episode_data = {
                "content": content,
                "canvas_name": canvas_name,
                "edge_id": edge.get("id"),
                "from_node": from_node,
                "to_node": to_node,
                "label": label,
                "created_at": datetime.now().isoformat(),
            }

            self._data["episodes"].append(episode_data)
            await self._save_data()

            logger.debug(f"Graphiti episode: {content}")
            return True
        except Exception as e:
            logger.warning(f"add_episode_for_edge failed: {e}")
            return False

    async def sync_canvas_edges(
        self,
        canvas_name: str,
        edges: List[Dict[str, Any]]
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
        if not self._enabled:
            return {"synced": 0, "skipped": len(edges), "reason": "disabled"}

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

                if not self._mcp_available:
                    result["skipped"] = len(edges)
                    result["reason"] = "mcp_unavailable"
                    return result

                # Process edges in batches
                for i in range(0, len(edges), self._batch_size):
                    batch = edges[i:i + self._batch_size]

                    for edge in batch:
                        relationship = EdgeRelationship(
                            canvas_name=canvas_name,
                            from_node=edge.get("fromNode", ""),
                            to_node=edge.get("toNode", ""),
                            label=edge.get("label", ""),
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
                f"Canvas edge sync timeout for {canvas_name} "
                f"after {self._timeout_ms}ms"
            )
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Canvas edge sync error: {e}")

        return result

    async def cleanup(self) -> None:
        """Cleanup client resources"""
        logger.debug(
            f"GraphitiEdgeClient cleanup: "
            f"{self._sync_count} syncs, {self._error_count} errors"
        )
        self._initialized = False


# Singleton instance
_client_instance: Optional[GraphitiEdgeClient] = None


def get_graphiti_client(
    timeout_ms: int = 2000,
    enabled: bool = True
) -> GraphitiEdgeClient:
    """
    Get or create GraphitiEdgeClient singleton.

    Args:
        timeout_ms: Timeout in milliseconds
        enabled: Whether sync is enabled

    Returns:
        GraphitiEdgeClient instance
    """
    global _client_instance

    if _client_instance is None:
        _client_instance = GraphitiEdgeClient(
            timeout_ms=timeout_ms,
            enabled=enabled
        )

    return _client_instance


def reset_graphiti_client() -> None:
    """Reset singleton instance (for testing)"""
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
        self,
        storage_path: Optional[Path] = None,
        max_search_results: int = 5
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
                        "version": "1.0"
                    }
                }
                await self._save_data()
                logger.info(f"Created new memory storage: {self._storage_path}")

            self._initialized = True
            return True
        except Exception as e:
            logger.error(f"LearningMemoryClient init failed: {e}")
            return False

    async def _save_data(self) -> None:
        """Save data to JSON storage file."""
        try:
            with open(self._storage_path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save learning memories: {e}")

    async def add_learning_episode(
        self,
        memory: LearningMemory
    ) -> bool:
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
        except Exception as e:
            logger.error(f"Failed to add learning episode: {e}")
            return False

    async def search_memories(
        self,
        query: str,
        canvas_name: Optional[str] = None,
        node_id: Optional[str] = None,
        limit: Optional[int] = None
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

                concept_overlap = len(query_words & concept_words) / max(len(query_words), 1)
                understanding_overlap = len(query_words & understanding_words) / max(len(query_words), 1)
                relevance = max(concept_overlap * 0.7, understanding_overlap * 0.5)

            if relevance > 0.1:
                results.append({
                    **memory,
                    "relevance": relevance
                })

        # Sort by relevance (descending) and timestamp (recent first)
        results.sort(key=lambda x: (-x["relevance"], x.get("timestamp", "")), reverse=False)

        return results[:max_results]

    async def get_learning_history(
        self,
        canvas_name: str,
        node_id: Optional[str] = None,
        limit: int = 10
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
        self,
        memories: List[Dict[str, Any]],
        max_chars: int = 1000
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
                preview = understanding[:100] + "..." if len(understanding) > 100 else understanding
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
        logger.debug(f"LearningMemoryClient cleanup: {self.stats['total_memories']} memories")
        self._initialized = False


# Singleton instance for LearningMemoryClient
_learning_memory_instance: Optional[LearningMemoryClient] = None


def get_learning_memory_client(
    storage_path: Optional[Path] = None
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
