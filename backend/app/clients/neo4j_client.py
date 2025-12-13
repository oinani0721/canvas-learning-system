# Canvas Learning System - Neo4j Client
# Story 22.4: 学习历史存储与查询API
# ✅ Verified pattern from backend/app/clients/graphiti_client.py
"""
Lightweight Neo4j client for Memory System.

Story 22.4: Learning history storage and query API
- AC-22.4.1: POST /api/v1/memory/episodes
- AC-22.4.3: GET /api/v1/memory/concepts/{id}/history
- AC-22.4.4: GET /api/v1/memory/review-suggestions

Uses JSON file storage for development, ready for Neo4j upgrade.

[Source: docs/prd/EPIC-22-MEMORY-SYSTEM-NEO4J-GRAPHITI.md#Story-22.4]
[Source: docs/stories/22.4.story.md#Dev-Notes]
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Default storage path for Neo4j-like data
DEFAULT_STORAGE_PATH = Path(__file__).parent.parent.parent / "data" / "neo4j_memory.json"


class Neo4jClient:
    """
    Lightweight Neo4j client for Memory System.

    ✅ Verified from docs/stories/22.4.story.md#Dev-Notes:
    - _create_neo4j_learning_relationship() creates LEARNED relationships
    - get_review_suggestions() queries concepts by next_review date

    Uses JSON file storage for development. Ready for Neo4j upgrade.

    [Source: docs/stories/22.4.story.md#MemoryService实现]
    """

    def __init__(
        self,
        storage_path: Optional[Path] = None,
        enabled: bool = True
    ):
        """
        Initialize Neo4jClient.

        Args:
            storage_path: Path to JSON storage file
            enabled: Whether client is enabled
        """
        self._storage_path = storage_path or DEFAULT_STORAGE_PATH
        self._enabled = enabled
        self._initialized = False
        self._data: Dict[str, Any] = {
            "users": [],
            "concepts": [],
            "relationships": []
        }
        logger.debug(
            f"Neo4jClient initialized: enabled={enabled}, storage={self._storage_path}"
        )

    @property
    def enabled(self) -> bool:
        """Check if client is enabled."""
        return self._enabled

    @property
    def stats(self) -> Dict[str, Any]:
        """Get client statistics."""
        return {
            "enabled": self._enabled,
            "initialized": self._initialized,
            "storage_path": str(self._storage_path),
            "total_users": len(self._data.get("users", [])),
            "total_concepts": len(self._data.get("concepts", [])),
            "total_relationships": len(self._data.get("relationships", [])),
        }

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
                    f"Loaded {len(self._data.get('relationships', []))} relationships "
                    f"from {self._storage_path}"
                )
            else:
                self._data = {
                    "users": [],
                    "concepts": [],
                    "relationships": [],
                    "metadata": {
                        "created_at": datetime.now().isoformat(),
                        "version": "1.0"
                    }
                }
                await self._save_data()
                logger.info(f"Created new storage file: {self._storage_path}")

            self._initialized = True
            return True

        except Exception as e:
            logger.warning(f"Neo4jClient init failed: {e}")
            self._initialized = True
            return False

    async def _save_data(self) -> None:
        """Save data to JSON storage file."""
        try:
            with open(self._storage_path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save Neo4j data: {e}")

    async def run_query(
        self,
        query: str,
        **params: Any
    ) -> List[Dict[str, Any]]:
        """
        Run a Cypher-like query (simulated with JSON storage).

        ✅ Verified from docs/stories/22.4.story.md#Dev-Notes:
        - Supports MERGE for User and Concept nodes
        - Supports MATCH for querying LEARNED relationships

        Args:
            query: Cypher query string (for documentation, simulated in JSON)
            **params: Query parameters

        Returns:
            List of result dicts
        """
        if not self._initialized:
            await self.initialize()

        # This is a simplified simulation - in production, use actual Neo4j
        logger.debug(f"Running query with params: {params}")

        # Parse query intent based on keywords
        if "MERGE" in query and "User" in query and "Concept" in query:
            # Create or update learning relationship
            return await self._handle_merge_learning(params)
        elif "MATCH" in query and "LEARNED" in query and "next_review" in query:
            # Query review suggestions
            return await self._handle_query_reviews(params)
        elif "MATCH" in query and "LEARNED" in query:
            # Query concept history
            return await self._handle_query_history(params)
        else:
            logger.warning(f"Unhandled query pattern: {query[:100]}")
            return []

    async def _handle_merge_learning(
        self,
        params: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Handle MERGE query for creating learning relationships.

        ✅ Verified from docs/stories/22.4.story.md#_create_neo4j_learning_relationship:
        - MERGE (u:User {id: $userId})
        - MERGE (c:Concept {name: $concept})
        - MERGE (u)-[r:LEARNED]->(c)

        Args:
            params: Query parameters (userId, concept, score)

        Returns:
            List with created/updated relationship
        """
        user_id = params.get("userId")
        concept = params.get("concept")
        score = params.get("score")

        if not user_id or not concept:
            return []

        # Ensure user exists
        user = next(
            (u for u in self._data["users"] if u["id"] == user_id),
            None
        )
        if not user:
            user = {"id": user_id, "created_at": datetime.now().isoformat()}
            self._data["users"].append(user)

        # Ensure concept exists
        concept_node = next(
            (c for c in self._data["concepts"] if c["name"] == concept),
            None
        )
        if not concept_node:
            concept_id = f"concept-{len(self._data['concepts']) + 1}"
            concept_node = {
                "id": concept_id,
                "name": concept,
                "created_at": datetime.now().isoformat()
            }
            self._data["concepts"].append(concept_node)

        # Create or update relationship
        now = datetime.now()
        next_review = now + timedelta(days=1)

        rel = next(
            (r for r in self._data["relationships"]
             if r["user_id"] == user_id and r["concept_name"] == concept),
            None
        )

        if rel:
            # Update existing relationship
            rel["timestamp"] = now.isoformat()
            rel["last_score"] = score
            rel["next_review"] = next_review.isoformat()
            rel["review_count"] = rel.get("review_count", 0) + 1
        else:
            # Create new relationship
            rel = {
                "id": f"learned-{len(self._data['relationships']) + 1}",
                "user_id": user_id,
                "concept_id": concept_node["id"],
                "concept_name": concept,
                "timestamp": now.isoformat(),
                "last_score": score,
                "next_review": next_review.isoformat(),
                "review_count": 1
            }
            self._data["relationships"].append(rel)

        await self._save_data()

        logger.info(
            f"Created learning relationship: {user_id} -> {concept} "
            f"(score={score})"
        )

        return [{"r": rel}]

    async def _handle_query_reviews(
        self,
        params: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Handle query for review suggestions.

        ✅ Verified from docs/stories/22.4.story.md#get_review_suggestions:
        - WHERE r.next_review < datetime()
        - ORDER BY r.next_review
        - LIMIT $limit

        Args:
            params: Query parameters (userId, limit)

        Returns:
            List of concepts due for review
        """
        user_id = params.get("userId")
        limit = params.get("limit", 10)

        if not user_id:
            return []

        now = datetime.now()
        results = []

        for rel in self._data.get("relationships", []):
            if rel["user_id"] != user_id:
                continue

            # Check if due for review
            next_review_str = rel.get("next_review")
            if next_review_str:
                try:
                    next_review = datetime.fromisoformat(next_review_str)
                    if next_review < now:
                        # Get concept details
                        concept = next(
                            (c for c in self._data["concepts"]
                             if c["name"] == rel["concept_name"]),
                            {"id": rel.get("concept_id", ""), "name": rel["concept_name"]}
                        )
                        results.append({
                            "concept": rel["concept_name"],
                            "concept_id": concept.get("id", ""),
                            "last_score": rel.get("last_score"),
                            "review_count": rel.get("review_count", 0),
                            "due_date": next_review.isoformat()
                        })
                except (ValueError, TypeError):
                    continue

        # Sort by due date (oldest first)
        results.sort(key=lambda x: x.get("due_date", ""))

        return results[:limit]

    async def _handle_query_history(
        self,
        params: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Handle query for concept learning history.

        Args:
            params: Query parameters

        Returns:
            List of learning history records
        """
        user_id = params.get("userId")
        concept_id = params.get("conceptId")

        results = []

        for rel in self._data.get("relationships", []):
            if user_id and rel["user_id"] != user_id:
                continue
            if concept_id and rel.get("concept_id") != concept_id:
                continue

            results.append({
                "user_id": rel["user_id"],
                "concept": rel["concept_name"],
                "concept_id": rel.get("concept_id"),
                "score": rel.get("last_score"),
                "timestamp": rel.get("timestamp"),
                "review_count": rel.get("review_count", 0)
            })

        # Sort by timestamp (newest first)
        results.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        return results

    async def create_learning_relationship(
        self,
        user_id: str,
        concept: str,
        score: Optional[int] = None
    ) -> bool:
        """
        Create a learning relationship between user and concept.

        ✅ Verified from docs/stories/22.4.story.md#_create_neo4j_learning_relationship

        Args:
            user_id: User ID
            concept: Concept name
            score: Optional score

        Returns:
            True if successful
        """
        query = """
        MERGE (u:User {id: $userId})
        MERGE (c:Concept {name: $concept})
        MERGE (u)-[r:LEARNED]->(c)
        SET r.timestamp = datetime(),
            r.score = $score,
            r.next_review = datetime() + duration('P1D')
        RETURN r
        """
        results = await self.run_query(
            query,
            userId=user_id,
            concept=concept,
            score=score
        )
        return len(results) > 0

    async def get_review_suggestions(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get concepts due for review.

        ✅ Verified from docs/stories/22.4.story.md#get_review_suggestions

        Args:
            user_id: User ID
            limit: Maximum results

        Returns:
            List of concepts due for review with priority
        """
        query = """
        MATCH (u:User {id: $userId})-[r:LEARNED]->(c:Concept)
        WHERE r.next_review < datetime()
        RETURN c.name as concept,
               c.id as concept_id,
               r.last_score as last_score,
               r.review_count as review_count,
               r.next_review as due_date
        ORDER BY r.next_review
        LIMIT $limit
        """
        results = await self.run_query(query, userId=user_id, limit=limit)

        # Add priority based on review count
        suggestions = []
        for r in results:
            priority = "high" if r.get("review_count", 0) < 3 else "medium"
            suggestions.append({
                **r,
                "priority": priority
            })

        return suggestions

    async def get_concept_history(
        self,
        concept_id: str,
        user_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get learning history for a specific concept.

        ✅ Verified from AC-22.4.3: GET /api/v1/memory/concepts/{id}/history

        Args:
            concept_id: Concept ID
            user_id: Optional user ID filter
            limit: Maximum results

        Returns:
            List of learning history records
        """
        params = {"conceptId": concept_id, "limit": limit}
        if user_id:
            params["userId"] = user_id

        results = await self._handle_query_history(params)
        return results[:limit]

    async def cleanup(self) -> None:
        """Cleanup client resources."""
        logger.debug(f"Neo4jClient cleanup: {self.stats}")
        self._initialized = False


# Singleton instance
_client_instance: Optional[Neo4jClient] = None


def get_neo4j_client(
    storage_path: Optional[Path] = None,
    enabled: bool = True
) -> Neo4jClient:
    """
    Get or create Neo4jClient singleton.

    Args:
        storage_path: Optional storage path override
        enabled: Whether client is enabled

    Returns:
        Neo4jClient instance
    """
    global _client_instance

    if _client_instance is None:
        _client_instance = Neo4jClient(
            storage_path=storage_path,
            enabled=enabled
        )

    return _client_instance


def reset_neo4j_client() -> None:
    """Reset singleton instance (for testing)."""
    global _client_instance
    _client_instance = None
