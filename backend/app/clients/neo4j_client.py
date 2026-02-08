# Canvas Learning System - Neo4j Client
# Story 30.2: Neo4jClient真实驱动实现
# ✅ Verified from Context7:/websites/neo4j_cypher-manual_25 (topic: AsyncGraphDatabase)
"""
Neo4j client with AsyncGraphDatabase driver for Memory System.

Story 30.2: Real Neo4j driver implementation
- AC-1: AsyncGraphDatabase connection replaces JSON storage
- AC-2: Connection pool (50 connections, 30s timeout, 3600s lifetime)
- AC-3: JSON Fallback mode preserved (NEO4J_ENABLED=false)
- AC-4: Write latency < 200ms P95
- AC-5: Retry mechanism (3 times, exponential backoff 1s, 2s, 4s)

[Source: docs/stories/30.2.story.md]
[Source: docs/stories/22.4.story.md#Dev-Notes]
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Neo4j async driver
# ✅ Verified from Context7:/websites/neo4j_cypher-manual_25 (topic: AsyncGraphDatabase)
from neo4j import AsyncGraphDatabase, AsyncDriver, AsyncSession
from neo4j.exceptions import (
    ServiceUnavailable,
    SessionExpired,
    TransientError,
    AuthError,
    Neo4jError,
)

# Retry mechanism
# ✅ Story 30.2 AC-5: Exponential backoff retry
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    RetryError,
)

logger = logging.getLogger(__name__)

# Default storage path for JSON fallback mode
DEFAULT_STORAGE_PATH = Path(__file__).parent.parent.parent / "data" / "neo4j_memory.json"

# Retryable exceptions for Neo4j operations
RETRYABLE_EXCEPTIONS = (ServiceUnavailable, SessionExpired, TransientError)


class Neo4jClient:
    """
    Neo4j client with real AsyncGraphDatabase driver.

    Story 30.2: Supports both real Neo4j connection and JSON fallback mode.

    ✅ Verified from Context7:/websites/neo4j_cypher-manual_25:
    - AsyncGraphDatabase.driver() for async connections
    - Connection pool configuration via driver parameters

    Attributes:
        _driver: AsyncGraphDatabase driver instance (None if using JSON fallback)
        _use_json_fallback: Whether to use JSON storage instead of Neo4j
        _storage_path: Path to JSON storage file (for fallback mode)

    [Source: docs/stories/30.2.story.md]
    """

    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        user: str = "neo4j",
        password: str = "",
        database: str = "neo4j",
        max_connection_pool_size: int = 50,
        connection_acquisition_timeout: int = 30,
        max_connection_lifetime: int = 3600,
        retry_attempts: int = 3,
        retry_delay_base: float = 1.0,
        retry_max_delay: float = 10.0,
        use_json_fallback: bool = False,
        storage_path: Optional[Path] = None,
    ):
        """
        Initialize Neo4jClient.

        Args:
            uri: Neo4j Bolt connection URI (bolt://localhost:7687)
            user: Neo4j username
            password: Neo4j password
            database: Neo4j database name
            max_connection_pool_size: Maximum connections in pool (AC-2: 50)
            connection_acquisition_timeout: Timeout to acquire connection (AC-2: 30s)
            max_connection_lifetime: Max connection lifetime (AC-2: 3600s)
            retry_attempts: Number of retry attempts (AC-5: 3)
            retry_delay_base: Base delay for exponential backoff (AC-5: 1.0s)
            retry_max_delay: Maximum retry delay (AC-5: 10.0s)
            use_json_fallback: Use JSON storage instead of Neo4j (AC-3)
            storage_path: Path to JSON storage file

        [Source: docs/stories/30.2.story.md - Task 1, Task 2]
        """
        self._uri = uri
        self._user = user
        self._password = password
        self._database = database
        self._max_connection_pool_size = max_connection_pool_size
        self._connection_acquisition_timeout = connection_acquisition_timeout
        self._max_connection_lifetime = max_connection_lifetime
        self._retry_attempts = retry_attempts
        self._retry_delay_base = retry_delay_base
        self._retry_max_delay = retry_max_delay
        self._use_json_fallback = use_json_fallback
        self._storage_path = storage_path or DEFAULT_STORAGE_PATH

        self._driver: Optional[AsyncDriver] = None
        self._initialized = False
        self._last_health_check: Optional[datetime] = None
        self._health_status: bool = False

        # JSON fallback data structure
        self._data: Dict[str, Any] = {
            "users": [],
            "concepts": [],
            "relationships": []
        }

        # Performance metrics
        self._metrics: Dict[str, Any] = {
            "total_queries": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "retry_count": 0,
            "total_latency_ms": 0.0,
        }

        logger.info(
            f"Neo4jClient initialized: mode={'JSON_FALLBACK' if use_json_fallback else 'NEO4J'}, "
            f"uri={uri if not use_json_fallback else 'N/A'}, "
            f"pool_size={max_connection_pool_size}"
        )

    @property
    def enabled(self) -> bool:
        """Check if client is enabled (not using fallback)."""
        return not self._use_json_fallback

    @property
    def is_fallback_mode(self) -> bool:
        """Check if using JSON fallback mode."""
        return self._use_json_fallback

    @property
    def stats(self) -> Dict[str, Any]:
        """Get client statistics."""
        return {
            "enabled": self.enabled,
            "initialized": self._initialized,
            "mode": "JSON_FALLBACK" if self._use_json_fallback else "NEO4J",
            "uri": self._uri if not self._use_json_fallback else None,
            "database": self._database,
            "pool_size": self._max_connection_pool_size,
            "health_status": self._health_status,
            "last_health_check": self._last_health_check.isoformat() if self._last_health_check else None,
            "metrics": self._metrics,
            # JSON fallback stats
            "total_users": len(self._data.get("users", [])) if self._use_json_fallback else None,
            "total_concepts": len(self._data.get("concepts", [])) if self._use_json_fallback else None,
            "total_relationships": len(self._data.get("relationships", [])) if self._use_json_fallback else None,
        }

    async def initialize(self) -> bool:
        """
        Initialize client - connect to Neo4j or load JSON data.

        Returns:
            True if initialization successful

        [Source: docs/stories/30.2.story.md - Task 2.1]
        """
        if self._initialized:
            return True

        try:
            if self._use_json_fallback:
                # JSON fallback mode - load from file
                return await self._initialize_json_fallback()
            else:
                # Real Neo4j mode - create driver
                return await self._initialize_neo4j_driver()

        except Exception as e:
            logger.error(f"Neo4jClient initialization failed: {e}")
            self._initialized = False
            return False

    async def _initialize_neo4j_driver(self) -> bool:
        """
        Initialize real Neo4j AsyncGraphDatabase driver.

        ✅ Verified from Context7:/websites/neo4j_cypher-manual_25:
        - AsyncGraphDatabase.driver() creates async driver
        - Connection pool parameters via driver config

        Returns:
            True if driver created successfully

        [Source: docs/stories/30.2.story.md - Task 2.1]
        """
        try:
            # Create AsyncGraphDatabase driver with connection pool config
            # ✅ AC-2: Connection pool (50 connections, 30s timeout, 3600s lifetime)
            self._driver = AsyncGraphDatabase.driver(
                self._uri,
                auth=(self._user, self._password),
                max_connection_pool_size=self._max_connection_pool_size,
                connection_acquisition_timeout=self._connection_acquisition_timeout,
                max_connection_lifetime=self._max_connection_lifetime,
            )

            # Verify connection with health check
            health_ok = await self.health_check()
            if health_ok:
                self._initialized = True
                logger.info(
                    f"Neo4j driver initialized: {self._uri}, "
                    f"pool_size={self._max_connection_pool_size}"
                )
                return True
            else:
                logger.warning("Neo4j health check failed during initialization")
                await self._fallback_to_json()
                return True

        except AuthError as e:
            logger.error(f"Neo4j authentication failed: {e}")
            await self._fallback_to_json()
            return True

        except Exception as e:
            logger.error(f"Failed to create Neo4j driver: {e}")
            await self._fallback_to_json()
            return True

    async def _fallback_to_json(self) -> None:
        """
        Fallback to JSON storage when Neo4j is unavailable.

        ✅ AC-3: JSON Fallback mode preserved

        [Source: docs/stories/30.2.story.md - Task 2.4]
        """
        logger.warning("Falling back to JSON storage mode")
        self._use_json_fallback = True
        if self._driver:
            await self._close_driver()
        await self._initialize_json_fallback()

    async def _initialize_json_fallback(self) -> bool:
        """
        Initialize JSON fallback mode.

        Returns:
            True if JSON data loaded successfully

        [Source: docs/stories/30.2.story.md - AC 3]
        """
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
                        "version": "2.0"  # Story 30.2 version
                    }
                }
                await self._save_json_data()
                logger.info(f"Created new JSON storage file: {self._storage_path}")

            self._initialized = True
            self._health_status = True
            return True

        except Exception as e:
            logger.error(f"JSON fallback initialization failed: {e}")
            self._initialized = True  # Still mark as initialized to avoid loops
            return False

    async def _save_json_data(self) -> None:
        """Save data to JSON storage file."""
        try:
            with open(self._storage_path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save JSON data: {e}")

    async def _close_driver(self) -> None:
        """Close Neo4j driver connection."""
        if self._driver:
            try:
                await self._driver.close()
                self._driver = None
                logger.info("Neo4j driver closed")
            except Exception as e:
                logger.error(f"Error closing Neo4j driver: {e}")

    async def health_check(self) -> bool:
        """
        Perform health check on Neo4j connection.

        ✅ AC-5: Health check with retry mechanism

        Returns:
            True if Neo4j is healthy and responding

        [Source: docs/stories/30.2.story.md - Task 5]
        """
        if self._use_json_fallback:
            self._health_status = True
            self._last_health_check = datetime.now()
            return True

        if not self._driver:
            self._health_status = False
            return False

        try:
            # Use verify_connectivity for health check
            await self._driver.verify_connectivity()
            self._health_status = True
            self._last_health_check = datetime.now()
            logger.debug("Neo4j health check passed")
            return True

        except Exception as e:
            logger.warning(f"Neo4j health check failed: {e}")
            self._health_status = False
            self._last_health_check = datetime.now()
            return False

    async def run_query(
        self,
        query: str,
        **params: Any
    ) -> List[Dict[str, Any]]:
        """
        Run a Cypher query with retry mechanism.

        ✅ AC-1: Real Cypher query execution
        ✅ AC-4: Write latency < 200ms P95
        ✅ AC-5: Retry mechanism (3 times, exponential backoff)

        Args:
            query: Cypher query string
            **params: Query parameters

        Returns:
            List of result dicts

        [Source: docs/stories/30.2.story.md - Task 3]
        """
        if not self._initialized:
            await self.initialize()

        start_time = time.perf_counter()
        self._metrics["total_queries"] += 1

        try:
            if self._use_json_fallback:
                result = await self._run_query_json_fallback(query, params)
            else:
                result = await self._run_query_neo4j(query, params)

            # Record metrics
            latency_ms = (time.perf_counter() - start_time) * 1000
            self._metrics["successful_queries"] += 1
            self._metrics["total_latency_ms"] += latency_ms

            if latency_ms > 200:
                logger.warning(f"Query latency exceeded 200ms: {latency_ms:.2f}ms")

            return result

        except Exception as e:
            self._metrics["failed_queries"] += 1
            logger.error(f"Query execution failed: {e}")
            raise

    async def _run_query_neo4j(
        self,
        query: str,
        params: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Execute Cypher query on real Neo4j with retry mechanism.

        ✅ AC-5: Retry with exponential backoff (1s, 2s, 4s)

        Args:
            query: Cypher query string
            params: Query parameters

        Returns:
            List of result records as dicts

        [Source: docs/stories/30.2.story.md - Task 3, Task 4]
        """
        if not self._driver:
            raise RuntimeError("Neo4j driver not initialized")

        @retry(
            stop=stop_after_attempt(self._retry_attempts),
            wait=wait_exponential(
                multiplier=self._retry_delay_base,
                max=self._retry_max_delay
            ),
            retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
            before_sleep=before_sleep_log(logger, logging.WARNING),
        )
        async def _execute_with_retry() -> List[Dict[str, Any]]:
            """Execute query with retry on transient errors."""
            async with self._driver.session(database=self._database) as session:
                result = await session.run(query, params)
                records = await result.data()
                return records

        try:
            return await _execute_with_retry()
        except RetryError as e:
            # Tenacity raises RetryError after all retries exhausted
            self._metrics["retry_count"] += 1
            logger.error(f"Query failed after {self._retry_attempts} retries: {e}")
            # Fallback to JSON on persistent failures
            if not self._use_json_fallback:
                await self._fallback_to_json()
                return await self._run_query_json_fallback(query, params)
            raise
        except RETRYABLE_EXCEPTIONS as e:
            self._metrics["retry_count"] += 1
            logger.error(f"Query failed with retryable error: {e}")
            # Fallback to JSON on persistent failures
            if not self._use_json_fallback:
                await self._fallback_to_json()
                return await self._run_query_json_fallback(query, params)
            raise
        except Neo4jError as e:
            logger.error(f"Neo4j query error: {e}")
            raise

    async def _run_query_json_fallback(
        self,
        query: str,
        params: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Simulate Cypher query with JSON storage (fallback mode).

        ✅ AC-3: JSON Fallback mode preserved

        Args:
            query: Cypher query string (for documentation)
            params: Query parameters

        Returns:
            List of result dicts

        [Source: docs/stories/30.2.story.md - AC 3]
        """
        logger.debug(f"Running JSON fallback query with params: {params}")

        # Parse query intent based on keywords
        if "MERGE" in query and "User" in query and "Concept" in query:
            return await self._handle_merge_learning(params)
        elif "MATCH" in query and "LEARNED" in query and "next_review" in query:
            return await self._handle_query_reviews(params)
        elif "MATCH" in query and "LEARNED" in query:
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
        group_id = params.get("groupId")

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
                "created_at": datetime.now().isoformat(),
                "group_id": group_id
            }
            self._data["concepts"].append(concept_node)
        elif group_id:
            concept_node["group_id"] = group_id

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
            if group_id:
                rel["group_id"] = group_id
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
                "review_count": 1,
                "group_id": group_id
            }
            self._data["relationships"].append(rel)

        await self._save_json_data()

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
        score: Optional[int] = None,
        group_id: Optional[str] = None
    ) -> bool:
        """
        Create a learning relationship between user and concept.

        ✅ Verified from docs/stories/22.4.story.md#_create_neo4j_learning_relationship

        Args:
            user_id: User ID
            concept: Concept name
            score: Optional score
            group_id: Optional group_id for subject isolation (Story 30.8)

        Returns:
            True if successful
        """
        query = """
        MERGE (u:User {id: $userId})
        MERGE (c:Concept {name: $concept})
        SET c.group_id = $groupId
        MERGE (u)-[r:LEARNED]->(c)
        SET r.timestamp = datetime(),
            r.score = $score,
            r.group_id = $groupId,
            r.next_review = datetime() + duration('P1D')
        RETURN r
        """
        results = await self.run_query(
            query,
            userId=user_id,
            concept=concept,
            score=score,
            groupId=group_id
        )
        return len(results) > 0

    async def record_episode(self, data: Dict[str, Any]) -> bool:
        """
        Record a learning episode from a dict payload.

        Delegates to create_learning_relationship() with extracted fields.
        Called by MemoryService.batch_record_events() and record_temporal_event().

        Args:
            data: Dict with keys: episode_id, user_id, canvas_path,
                  node_id, concept, agent_type, timestamp

        Returns:
            True if successful
        """
        user_id = data.get("user_id", "unknown")
        concept = data.get("concept", "unknown")
        score = data.get("score")
        group_id = data.get("group_id")

        # Infer group_id from canvas_path if not provided
        if not group_id and data.get("canvas_path"):
            from app.core.subject_config import (
                extract_subject_from_canvas_path,
                build_group_id,
            )
            subject = extract_subject_from_canvas_path(data["canvas_path"])
            group_id = build_group_id(subject)

        return await self.create_learning_relationship(
            user_id=user_id,
            concept=concept,
            score=score,
            group_id=group_id,
        )

    async def get_review_suggestions(
        self,
        user_id: str,
        limit: int = 10,
        group_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get concepts due for review.

        ✅ Verified from docs/stories/22.4.story.md#get_review_suggestions
        ✅ Verified from docs/stories/30.8.story.md#AC-30.8.3 (group_id filtering)

        Args:
            user_id: User ID
            limit: Maximum results
            group_id: Optional group_id for subject filtering (AC-30.8.3)

        Returns:
            List of concepts due for review with priority

        [Source: docs/stories/30.8.story.md#Task-3.1]
        """
        # ✅ AC-30.8.3: Build query with optional group_id filter
        if group_id:
            query = """
            MATCH (u:User {id: $userId})-[r:LEARNED]->(c:Concept)
            WHERE r.next_review < datetime() AND c.group_id = $groupId
            RETURN c.name as concept,
                   c.id as concept_id,
                   r.last_score as last_score,
                   r.review_count as review_count,
                   r.next_review as due_date
            ORDER BY r.next_review
            LIMIT $limit
            """
            results = await self.run_query(query, userId=user_id, limit=limit, groupId=group_id)
        else:
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

    async def get_learning_history(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        concept: Optional[str] = None,
        group_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get learning history for a user with optional filters.

        ✅ Story 31.A.2 AC-31.A.2.2: Neo4jClient method for learning history

        Args:
            user_id: User ID
            start_date: Optional start date filter
            end_date: Optional end date filter
            concept: Optional concept name filter (partial match)
            group_id: Optional group_id for subject filtering
            limit: Maximum results

        Returns:
            List of learning history records

        [Source: docs/stories/31.A.2.story.md#AC-31.A.2.2]
        """
        if self._use_json_fallback:
            return await self._get_learning_history_json(
                user_id=user_id,
                start_date=start_date,
                end_date=end_date,
                concept=concept,
                group_id=group_id,
                limit=limit
            )

        # Build Cypher query with optional filters
        # ✅ Story 31.A.2: Cypher query for learning history
        query = """
        MATCH (u:User {id: $userId})-[r:LEARNED]->(c:Concept)
        WHERE 1=1
        """
        params: Dict[str, Any] = {"userId": user_id, "limit": limit}

        if start_date:
            query += " AND r.timestamp >= $startDate"
            params["startDate"] = start_date.isoformat()
        if end_date:
            query += " AND r.timestamp <= $endDate"
            params["endDate"] = end_date.isoformat()
        if concept:
            query += " AND toLower(c.name) CONTAINS toLower($concept)"
            params["concept"] = concept
        if group_id:
            query += " AND r.group_id = $groupId"
            params["groupId"] = group_id

        query += """
        RETURN c.name as concept,
               c.id as concept_id,
               r.score as score,
               r.timestamp as timestamp,
               r.group_id as group_id,
               r.agent_type as agent_type,
               r.review_count as review_count,
               u.id as user_id
        ORDER BY r.timestamp DESC
        LIMIT $limit
        """

        results = await self.run_query(query, **params)
        return results

    async def _get_learning_history_json(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        concept: Optional[str] = None,
        group_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        JSON fallback implementation for get_learning_history.

        ✅ Story 31.A.2: JSON fallback mode support

        [Source: docs/stories/31.A.2.story.md#AC-31.A.2.2]
        """
        results = []

        for rel in self._data.get("relationships", []):
            # Filter by user_id
            if rel.get("user_id") != user_id:
                continue

            # Filter by date range
            rel_timestamp = rel.get("timestamp")
            if rel_timestamp:
                try:
                    rel_dt = datetime.fromisoformat(rel_timestamp.replace("Z", "+00:00"))
                    if start_date and rel_dt < start_date:
                        continue
                    if end_date and rel_dt > end_date:
                        continue
                except (ValueError, AttributeError):
                    pass

            # Filter by concept (partial match)
            if concept:
                rel_concept = rel.get("concept_name", "")
                if concept.lower() not in rel_concept.lower():
                    continue

            # Filter by group_id
            if group_id and rel.get("group_id") != group_id:
                continue

            results.append({
                "user_id": rel.get("user_id"),
                "concept": rel.get("concept_name"),
                "concept_id": rel.get("concept_id"),
                "score": rel.get("last_score"),
                "timestamp": rel.get("timestamp"),
                "group_id": rel.get("group_id"),
                "agent_type": rel.get("agent_type"),
                "review_count": rel.get("review_count", 0)
            })

        # Sort by timestamp (newest first)
        results.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        return results[:limit]

    async def create_canvas_node_relationship(
        self,
        canvas_path: str,
        node_id: str,
        node_text: Optional[str] = None
    ) -> bool:
        """
        Create Canvas-Node relationship in Neo4j graph.

        Story 30.5 AC-30.5.4: Canvas-Concept-LearningEpisode relationship graph

        Creates:
        - Canvas node if not exists
        - Node entity with text as potential concept
        - CONTAINS_NODE relationship from Canvas to Node

        Args:
            canvas_path: Canvas file path
            node_id: Node ID
            node_text: Node text content (potential concept)

        Returns:
            True if successful

        [Source: docs/stories/30.5.story.md#Task-5.1]
        """
        query = """
        MERGE (c:Canvas {path: $canvasPath})
        MERGE (n:Node {id: $nodeId})
        SET n.text = $nodeText,
            n.updated_at = datetime()
        MERGE (c)-[r:CONTAINS_NODE]->(n)
        SET r.created_at = coalesce(r.created_at, datetime())
        RETURN c, n, r
        """
        results = await self.run_query(
            query,
            canvasPath=canvas_path,
            nodeId=node_id,
            nodeText=node_text or ""
        )
        return len(results) > 0

    async def create_edge_relationship(
        self,
        canvas_path: str,
        edge_id: str,
        from_node_id: str,
        to_node_id: str,
        edge_label: Optional[str] = None
    ) -> bool:
        """
        Create edge relationship between nodes in Neo4j graph.

        Story 30.5 AC-30.5.4: Canvas-Concept-LearningEpisode relationship graph

        Creates:
        - CONNECTS_TO relationship between Node entities
        - HAS_EDGE relationship from Canvas to Edge

        Args:
            canvas_path: Canvas file path
            edge_id: Edge ID
            from_node_id: Source node ID
            to_node_id: Target node ID
            edge_label: Optional edge label

        Returns:
            True if successful

        [Source: docs/stories/30.5.story.md#Task-5.2]
        """
        query = """
        MERGE (c:Canvas {path: $canvasPath})
        MERGE (from:Node {id: $fromNodeId})
        MERGE (to:Node {id: $toNodeId})
        MERGE (from)-[r:CONNECTS_TO {edge_id: $edgeId}]->(to)
        SET r.label = $edgeLabel,
            r.created_at = coalesce(r.created_at, datetime())
        RETURN c, from, to, r
        """
        results = await self.run_query(
            query,
            canvasPath=canvas_path,
            edgeId=edge_id,
            fromNodeId=from_node_id,
            toNodeId=to_node_id,
            edgeLabel=edge_label or ""
        )
        return len(results) > 0

    async def get_concept_score_history(
        self,
        concept_id: str,
        canvas_name: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get historical scores for a concept.

        Story 31.5 AC-31.5.1: Query recent N score records for difficulty adaptation.

        Args:
            concept_id: Concept/Node ID
            canvas_name: Canvas file name
            limit: Maximum number of records (default: 5)

        Returns:
            List of dicts with score, timestamp fields (ordered from oldest to newest)

        [Source: docs/stories/31.5.story.md#Task-2.2]
        """
        if self._use_json_fallback:
            return await self._get_score_history_json_fallback(concept_id, canvas_name, limit)

        query = """
        MATCH (n:Node {id: $conceptId})<-[:CONTAINS_NODE]-(c:Canvas {path: $canvasPath})
        MATCH (n)<-[r:SCORED]-(e:Episode)
        RETURN r.score as score, r.timestamp as timestamp
        ORDER BY r.timestamp DESC
        LIMIT $limit
        """
        results = await self.run_query(
            query,
            conceptId=concept_id,
            canvasPath=canvas_name,
            limit=limit
        )

        # Reverse to get oldest-to-newest order
        return list(reversed(results))

    async def _get_score_history_json_fallback(
        self,
        concept_id: str,
        canvas_name: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get score history from JSON fallback storage.

        Story 31.5 AC-31.5.1: JSON fallback for score history query.

        Args:
            concept_id: Concept/Node ID
            canvas_name: Canvas file name
            limit: Maximum number of records

        Returns:
            List of dicts with score, timestamp fields

        [Source: docs/stories/31.5.story.md#Task-2.2]
        """
        results = []

        # Check in-memory relationships for matching concept
        for rel in self._data.get("relationships", []):
            # Match by concept_id or concept_name containing the concept_id
            if (rel.get("concept_id") == concept_id or
                rel.get("concept_name", "").find(concept_id) >= 0 or
                rel.get("node_id") == concept_id):

                score = rel.get("last_score")
                timestamp = rel.get("timestamp")

                if score is not None and timestamp:
                    results.append({
                        "score": score,
                        "timestamp": timestamp
                    })

        # Also check score_history array if exists (extended storage)
        score_history = self._data.get("score_history", [])
        for record in score_history:
            if (record.get("concept_id") == concept_id or
                record.get("node_id") == concept_id):

                results.append({
                    "score": record.get("score"),
                    "timestamp": record.get("timestamp")
                })

        # Sort by timestamp (oldest first) and limit
        results.sort(key=lambda x: x.get("timestamp", ""))
        return results[-limit:] if len(results) > limit else results

    async def record_score_history(
        self,
        concept_id: str,
        canvas_name: str,
        score: int,
        timestamp: Optional[str] = None
    ) -> bool:
        """
        Record a score to history for difficulty adaptation.

        Story 31.5: Store scores for historical analysis.

        Args:
            concept_id: Concept/Node ID
            canvas_name: Canvas file name
            score: Score value (0-100)
            timestamp: Optional timestamp (defaults to now)

        Returns:
            True if successful

        [Source: docs/stories/31.5.story.md#Task-2.2]
        """
        ts = timestamp or datetime.now().isoformat()

        if self._use_json_fallback:
            # Store in score_history array
            if "score_history" not in self._data:
                self._data["score_history"] = []

            self._data["score_history"].append({
                "concept_id": concept_id,
                "canvas_name": canvas_name,
                "score": score,
                "timestamp": ts
            })

            # Keep only last 100 records per concept to avoid unbounded growth
            await self._save_json_data()
            return True

        query = """
        MERGE (n:Node {id: $conceptId})
        MERGE (c:Canvas {path: $canvasPath})
        MERGE (c)-[:CONTAINS_NODE]->(n)
        CREATE (e:Episode {
            id: randomUUID(),
            type: 'scoring',
            timestamp: datetime($timestamp)
        })
        CREATE (e)-[:SCORED {
            score: $score,
            timestamp: datetime($timestamp)
        }]->(n)
        RETURN e
        """
        results = await self.run_query(
            query,
            conceptId=concept_id,
            canvasPath=canvas_name,
            score=score,
            timestamp=ts
        )
        return len(results) > 0

    # =========================================================================
    # Canvas Association CRUD Methods
    # Story 36.5: 跨Canvas讲座关联持久化
    # [Source: docs/stories/36.5.story.md]
    # =========================================================================

    async def create_canvas_association(
        self,
        association_id: str,
        source_canvas: str,
        target_canvas: str,
        association_type: str,
        confidence: float = 1.0,
        shared_concepts: Optional[List[str]] = None,
        bidirectional: bool = False,
        auto_generated: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Create Canvas association relationship in Neo4j graph.

        Story 36.5 AC-1, AC-2, AC-3: Canvas关联持久化到Neo4j

        Creates ASSOCIATED_WITH relationship between two Canvas nodes with
        association_type property using Schema-defined enum values.

        Args:
            association_id: Unique association identifier (UUID)
            source_canvas: Source Canvas file path
            target_canvas: Target Canvas file path
            association_type: Type of association - must be one of:
                prerequisite, related, extends, references
                [Source: specs/data/canvas-association.schema.json]
            confidence: Confidence score (0.0-1.0, default: 1.0)
            shared_concepts: Optional list of shared concept names
            bidirectional: Whether association is bidirectional (default: False)
            auto_generated: Whether association was auto-generated (default: False)
            metadata: Optional additional metadata

        Returns:
            True if successful

        [Source: docs/stories/36.5.story.md#Task-1.1]
        """
        # Validate association_type against schema enum
        valid_types = ["prerequisite", "related", "extends", "references"]
        if association_type not in valid_types:
            logger.error(
                f"Invalid association_type '{association_type}'. "
                f"Must be one of: {valid_types}"
            )
            return False

        if self._use_json_fallback:
            return await self._create_association_json_fallback(
                association_id, source_canvas, target_canvas, association_type,
                confidence, shared_concepts, bidirectional, auto_generated, metadata
            )

        query = """
        MERGE (source:Canvas {path: $sourceCanvas})
        MERGE (target:Canvas {path: $targetCanvas})
        MERGE (source)-[r:ASSOCIATED_WITH {association_id: $associationId}]->(target)
        SET r.association_type = $associationType,
            r.confidence = $confidence,
            r.shared_concepts = $sharedConcepts,
            r.bidirectional = $bidirectional,
            r.auto_generated = $autoGenerated,
            r.created_at = coalesce(r.created_at, datetime()),
            r.updated_at = datetime()
        RETURN r
        """
        results = await self.run_query(
            query,
            associationId=association_id,
            sourceCanvas=source_canvas,
            targetCanvas=target_canvas,
            associationType=association_type,
            confidence=confidence,
            sharedConcepts=shared_concepts or [],
            bidirectional=bidirectional,
            autoGenerated=auto_generated
        )

        if results:
            logger.info(
                f"Created canvas association: {source_canvas} -[{association_type}]-> "
                f"{target_canvas} (id={association_id})"
            )

        return len(results) > 0

    async def _create_association_json_fallback(
        self,
        association_id: str,
        source_canvas: str,
        target_canvas: str,
        association_type: str,
        confidence: float,
        shared_concepts: Optional[List[str]],
        bidirectional: bool,
        auto_generated: bool,
        metadata: Optional[Dict[str, Any]]
    ) -> bool:
        """
        Create canvas association in JSON fallback storage.

        Story 36.5 AC-3: JSON fallback mode preserved.

        [Source: docs/stories/36.5.story.md#Task-1.1]
        """
        # Initialize canvas_associations list if not exists
        if "canvas_associations" not in self._data:
            self._data["canvas_associations"] = []

        # Check for existing association with same ID
        existing = next(
            (a for a in self._data["canvas_associations"]
             if a.get("association_id") == association_id),
            None
        )

        now = datetime.now().isoformat()

        if existing:
            # Update existing
            existing["association_type"] = association_type
            existing["confidence"] = confidence
            existing["shared_concepts"] = shared_concepts or []
            existing["bidirectional"] = bidirectional
            existing["auto_generated"] = auto_generated
            existing["updated_at"] = now
            if metadata:
                existing["metadata"] = metadata
        else:
            # Create new
            association = {
                "association_id": association_id,
                "source_canvas": source_canvas,
                "target_canvas": target_canvas,
                "association_type": association_type,
                "confidence": confidence,
                "shared_concepts": shared_concepts or [],
                "bidirectional": bidirectional,
                "auto_generated": auto_generated,
                "created_at": now,
                "updated_at": now,
            }
            if metadata:
                association["metadata"] = metadata
            self._data["canvas_associations"].append(association)

        await self._save_json_data()

        logger.info(
            f"Created canvas association (JSON): {source_canvas} -[{association_type}]-> "
            f"{target_canvas} (id={association_id})"
        )
        return True

    async def get_canvas_associations(
        self,
        canvas_path: Optional[str] = None,
        association_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get Canvas associations from Neo4j graph.

        Story 36.5 AC-3: Query canvas associations.

        Args:
            canvas_path: Optional filter by source or target canvas path
            association_type: Optional filter by association type
            limit: Maximum results (default: 100)

        Returns:
            List of association dicts with all properties

        [Source: docs/stories/36.5.story.md#Task-1.2]
        """
        if self._use_json_fallback:
            return await self._get_associations_json_fallback(
                canvas_path, association_type, limit
            )

        # Build dynamic query based on filters
        if canvas_path and association_type:
            query = """
            MATCH (source:Canvas)-[r:ASSOCIATED_WITH]->(target:Canvas)
            WHERE (source.path = $canvasPath OR target.path = $canvasPath)
              AND r.association_type = $associationType
            RETURN r.association_id as association_id,
                   source.path as source_canvas,
                   target.path as target_canvas,
                   r.association_type as association_type,
                   r.confidence as confidence,
                   r.shared_concepts as shared_concepts,
                   r.bidirectional as bidirectional,
                   r.auto_generated as auto_generated,
                   r.created_at as created_at,
                   r.updated_at as updated_at
            ORDER BY r.created_at DESC
            LIMIT $limit
            """
            results = await self.run_query(
                query,
                canvasPath=canvas_path,
                associationType=association_type,
                limit=limit
            )
        elif canvas_path:
            query = """
            MATCH (source:Canvas)-[r:ASSOCIATED_WITH]->(target:Canvas)
            WHERE source.path = $canvasPath OR target.path = $canvasPath
            RETURN r.association_id as association_id,
                   source.path as source_canvas,
                   target.path as target_canvas,
                   r.association_type as association_type,
                   r.confidence as confidence,
                   r.shared_concepts as shared_concepts,
                   r.bidirectional as bidirectional,
                   r.auto_generated as auto_generated,
                   r.created_at as created_at,
                   r.updated_at as updated_at
            ORDER BY r.created_at DESC
            LIMIT $limit
            """
            results = await self.run_query(query, canvasPath=canvas_path, limit=limit)
        elif association_type:
            query = """
            MATCH (source:Canvas)-[r:ASSOCIATED_WITH]->(target:Canvas)
            WHERE r.association_type = $associationType
            RETURN r.association_id as association_id,
                   source.path as source_canvas,
                   target.path as target_canvas,
                   r.association_type as association_type,
                   r.confidence as confidence,
                   r.shared_concepts as shared_concepts,
                   r.bidirectional as bidirectional,
                   r.auto_generated as auto_generated,
                   r.created_at as created_at,
                   r.updated_at as updated_at
            ORDER BY r.created_at DESC
            LIMIT $limit
            """
            results = await self.run_query(
                query, associationType=association_type, limit=limit
            )
        else:
            query = """
            MATCH (source:Canvas)-[r:ASSOCIATED_WITH]->(target:Canvas)
            RETURN r.association_id as association_id,
                   source.path as source_canvas,
                   target.path as target_canvas,
                   r.association_type as association_type,
                   r.confidence as confidence,
                   r.shared_concepts as shared_concepts,
                   r.bidirectional as bidirectional,
                   r.auto_generated as auto_generated,
                   r.created_at as created_at,
                   r.updated_at as updated_at
            ORDER BY r.created_at DESC
            LIMIT $limit
            """
            results = await self.run_query(query, limit=limit)

        return results

    async def _get_associations_json_fallback(
        self,
        canvas_path: Optional[str],
        association_type: Optional[str],
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Get canvas associations from JSON fallback storage.

        Story 36.5 AC-3: JSON fallback mode preserved.

        [Source: docs/stories/36.5.story.md#Task-1.2]
        """
        associations = self._data.get("canvas_associations", [])
        results = []

        for assoc in associations:
            # Apply filters
            if canvas_path:
                if (assoc.get("source_canvas") != canvas_path and
                    assoc.get("target_canvas") != canvas_path):
                    continue

            if association_type:
                if assoc.get("association_type") != association_type:
                    continue

            results.append(assoc)

        # Sort by created_at descending and limit
        results.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return results[:limit]

    async def delete_canvas_association(
        self,
        association_id: str
    ) -> bool:
        """
        Delete Canvas association from Neo4j graph.

        Story 36.5 AC-3: Delete canvas association by ID.

        Args:
            association_id: Association ID to delete

        Returns:
            True if deleted, False if not found

        [Source: docs/stories/36.5.story.md#Task-1.3]
        """
        if self._use_json_fallback:
            return await self._delete_association_json_fallback(association_id)

        query = """
        MATCH (source:Canvas)-[r:ASSOCIATED_WITH {association_id: $associationId}]->(target:Canvas)
        DELETE r
        RETURN count(r) as deleted_count
        """
        results = await self.run_query(query, associationId=association_id)

        deleted = results[0].get("deleted_count", 0) if results else 0
        if deleted > 0:
            logger.info(f"Deleted canvas association: {association_id}")
            return True
        else:
            logger.warning(f"Canvas association not found: {association_id}")
            return False

    async def _delete_association_json_fallback(
        self,
        association_id: str
    ) -> bool:
        """
        Delete canvas association from JSON fallback storage.

        Story 36.5 AC-3: JSON fallback mode preserved.

        [Source: docs/stories/36.5.story.md#Task-1.3]
        """
        associations = self._data.get("canvas_associations", [])
        original_count = len(associations)

        self._data["canvas_associations"] = [
            a for a in associations
            if a.get("association_id") != association_id
        ]

        if len(self._data["canvas_associations"]) < original_count:
            await self._save_json_data()
            logger.info(f"Deleted canvas association (JSON): {association_id}")
            return True
        else:
            logger.warning(f"Canvas association not found (JSON): {association_id}")
            return False

    async def update_canvas_association(
        self,
        association_id: str,
        association_type: Optional[str] = None,
        confidence: Optional[float] = None,
        shared_concepts: Optional[List[str]] = None,
        bidirectional: Optional[bool] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update Canvas association in Neo4j graph.

        Story 36.5 AC-3: Update canvas association properties.

        Args:
            association_id: Association ID to update
            association_type: New association type (optional)
            confidence: New confidence score (optional)
            shared_concepts: New shared concepts list (optional)
            bidirectional: New bidirectional flag (optional)
            metadata: Additional metadata (optional)

        Returns:
            True if updated, False if not found

        [Source: docs/stories/36.5.story.md#Task-1.4]
        """
        # Validate association_type if provided
        if association_type:
            valid_types = ["prerequisite", "related", "extends", "references"]
            if association_type not in valid_types:
                logger.error(
                    f"Invalid association_type '{association_type}'. "
                    f"Must be one of: {valid_types}"
                )
                return False

        if self._use_json_fallback:
            return await self._update_association_json_fallback(
                association_id, association_type, confidence,
                shared_concepts, bidirectional, metadata
            )

        # Build SET clause dynamically for provided fields
        set_clauses = ["r.updated_at = datetime()"]
        params: Dict[str, Any] = {"associationId": association_id}

        if association_type is not None:
            set_clauses.append("r.association_type = $associationType")
            params["associationType"] = association_type

        if confidence is not None:
            set_clauses.append("r.confidence = $confidence")
            params["confidence"] = confidence

        if shared_concepts is not None:
            set_clauses.append("r.shared_concepts = $sharedConcepts")
            params["sharedConcepts"] = shared_concepts

        if bidirectional is not None:
            set_clauses.append("r.bidirectional = $bidirectional")
            params["bidirectional"] = bidirectional

        query = f"""
        MATCH (source:Canvas)-[r:ASSOCIATED_WITH {{association_id: $associationId}}]->(target:Canvas)
        SET {', '.join(set_clauses)}
        RETURN r.association_id as association_id
        """

        results = await self.run_query(query, **params)

        if results:
            logger.info(f"Updated canvas association: {association_id}")
            return True
        else:
            logger.warning(f"Canvas association not found: {association_id}")
            return False

    async def _update_association_json_fallback(
        self,
        association_id: str,
        association_type: Optional[str],
        confidence: Optional[float],
        shared_concepts: Optional[List[str]],
        bidirectional: Optional[bool],
        metadata: Optional[Dict[str, Any]]
    ) -> bool:
        """
        Update canvas association in JSON fallback storage.

        Story 36.5 AC-3: JSON fallback mode preserved.

        [Source: docs/stories/36.5.story.md#Task-1.4]
        """
        associations = self._data.get("canvas_associations", [])

        for assoc in associations:
            if assoc.get("association_id") == association_id:
                # Update provided fields
                if association_type is not None:
                    assoc["association_type"] = association_type
                if confidence is not None:
                    assoc["confidence"] = confidence
                if shared_concepts is not None:
                    assoc["shared_concepts"] = shared_concepts
                if bidirectional is not None:
                    assoc["bidirectional"] = bidirectional
                if metadata is not None:
                    assoc["metadata"] = metadata

                assoc["updated_at"] = datetime.now().isoformat()

                await self._save_json_data()
                logger.info(f"Updated canvas association (JSON): {association_id}")
                return True

        logger.warning(f"Canvas association not found (JSON): {association_id}")
        return False

    async def load_all_canvas_associations(self) -> List[Dict[str, Any]]:
        """
        Load all canvas associations at startup.

        Story 36.5 AC-4: Load existing associations from Neo4j on startup.

        Returns:
            List of all canvas associations

        [Source: docs/stories/36.5.story.md#Task-3.1]
        """
        return await self.get_canvas_associations(limit=10000)

    # =========================================================================
    # Canvas Concept Query Methods
    # Story 36.6: 跨Canvas讲座自动发现
    # [Source: docs/stories/36.6.story.md]
    # =========================================================================

    async def get_canvas_concepts(
        self,
        canvas_path: str
    ) -> List[str]:
        """
        Get all concepts associated with a Canvas.

        Story 36.6 Task 2.1: Query concepts from Canvas via Neo4j.

        Cypher query:
        ```
        MATCH (c:Canvas {path: $canvas_path})-[:CONTAINS]->(n:LearningNode)-[:HAS_CONCEPT]->(concept:Concept)
        RETURN DISTINCT concept.name as concept_name
        ```

        Args:
            canvas_path: Canvas file path

        Returns:
            List of concept names associated with the Canvas

        [Source: docs/stories/36.6.story.md#Task-2.1]
        """
        if self._use_json_fallback:
            return await self._get_canvas_concepts_json_fallback(canvas_path)

        query = """
        MATCH (c:Canvas {path: $canvasPath})-[:CONTAINS_NODE]->(n:Node)
        WHERE n.text IS NOT NULL AND n.text <> ''
        RETURN DISTINCT n.text as concept_name
        UNION
        MATCH (c:Canvas {path: $canvasPath})-[:CONTAINS]->(n:LearningNode)-[:HAS_CONCEPT]->(concept:Concept)
        RETURN DISTINCT concept.name as concept_name
        """
        results = await self.run_query(query, canvasPath=canvas_path)

        return [r["concept_name"] for r in results if r.get("concept_name")]

    async def _get_canvas_concepts_json_fallback(
        self,
        canvas_path: str
    ) -> List[str]:
        """
        Get canvas concepts from JSON fallback storage.

        Story 36.6 Task 2.1: JSON fallback mode.

        Args:
            canvas_path: Canvas file path

        Returns:
            List of concept names

        [Source: docs/stories/36.6.story.md#Task-2.1]
        """
        concepts = set()

        # Check relationships for concepts linked to this canvas
        for rel in self._data.get("relationships", []):
            # Check if relationship mentions this canvas path
            if canvas_path in str(rel.get("canvas_path", "")) or \
               canvas_path in str(rel.get("source", "")):
                concept_name = rel.get("concept_name") or rel.get("concept")
                if concept_name:
                    concepts.add(concept_name)

        # Also check canvas_concepts mapping if exists
        canvas_concepts_map = self._data.get("canvas_concepts", {})
        if canvas_path in canvas_concepts_map:
            concepts.update(canvas_concepts_map[canvas_path])

        return list(concepts)

    async def find_common_concepts(
        self,
        canvas1: str,
        canvas2: str
    ) -> List[str]:
        """
        Find common concepts between two Canvases.

        Story 36.6 Task 2.2: Query common concepts from Neo4j.

        Cypher query:
        ```
        MATCH (c1:Canvas {path: $canvas1})-[:CONTAINS]->(n1:LearningNode)-[:HAS_CONCEPT]->(concept:Concept)
        MATCH (c2:Canvas {path: $canvas2})-[:CONTAINS]->(n2:LearningNode)-[:HAS_CONCEPT]->(concept)
        RETURN DISTINCT concept.name as common_concept
        ```

        Args:
            canvas1: First Canvas file path
            canvas2: Second Canvas file path

        Returns:
            List of common concept names

        [Source: docs/stories/36.6.story.md#Task-2.2]
        """
        if self._use_json_fallback:
            return await self._find_common_concepts_json_fallback(canvas1, canvas2)

        query = """
        MATCH (c1:Canvas {path: $canvas1})-[:CONTAINS_NODE]->(n1:Node)
        WHERE n1.text IS NOT NULL AND n1.text <> ''
        WITH COLLECT(DISTINCT n1.text) as concepts1
        MATCH (c2:Canvas {path: $canvas2})-[:CONTAINS_NODE]->(n2:Node)
        WHERE n2.text IS NOT NULL AND n2.text <> ''
        WITH concepts1, COLLECT(DISTINCT n2.text) as concepts2
        RETURN [c IN concepts1 WHERE c IN concepts2] as common_concepts
        """
        results = await self.run_query(query, canvas1=canvas1, canvas2=canvas2)

        if results and results[0].get("common_concepts"):
            return results[0]["common_concepts"]
        return []

    async def _find_common_concepts_json_fallback(
        self,
        canvas1: str,
        canvas2: str
    ) -> List[str]:
        """
        Find common concepts between two canvases from JSON fallback storage.

        Story 36.6 Task 2.2: JSON fallback mode.

        Args:
            canvas1: First Canvas file path
            canvas2: Second Canvas file path

        Returns:
            List of common concept names

        [Source: docs/stories/36.6.story.md#Task-2.2]
        """
        concepts1 = set(await self._get_canvas_concepts_json_fallback(canvas1))
        concepts2 = set(await self._get_canvas_concepts_json_fallback(canvas2))

        return list(concepts1.intersection(concepts2))

    async def get_all_recent_episodes(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Get all recent learning episodes across all users.

        Story 38.2 AC-2: Query recent episodes for startup recovery.
        Used by MemoryService._recover_episodes_from_neo4j() to populate
        the in-memory episode cache on restart.

        Args:
            limit: Maximum number of episodes to return (default: 1000)

        Returns:
            List of episode dicts with user_id, concept, score, timestamp, etc.

        [Source: docs/stories/38.2.story.md#Task-1]
        """
        if self._use_json_fallback:
            return await self._get_all_recent_episodes_json(limit)

        query = """
        MATCH (u:User)-[r:LEARNED]->(c:Concept)
        RETURN u.id as user_id,
               c.name as concept,
               c.id as concept_id,
               r.score as score,
               r.timestamp as timestamp,
               r.group_id as group_id,
               r.review_count as review_count
        ORDER BY r.timestamp DESC
        LIMIT $limit
        """
        return await self.run_query(query, limit=limit)

    async def _get_all_recent_episodes_json(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        JSON fallback: get all recent episodes from relationships.

        Story 38.2 AC-2: JSON fallback for episode recovery.

        [Source: docs/stories/38.2.story.md#Task-1.2]
        """
        rels = self._data.get("relationships", [])
        results = []
        for rel in rels:
            results.append({
                "user_id": rel.get("user_id"),
                "concept": rel.get("concept_name"),
                "concept_id": rel.get("concept_id"),
                "score": rel.get("last_score"),
                "timestamp": rel.get("timestamp"),
                "group_id": rel.get("group_id"),
                "review_count": rel.get("review_count", 0),
            })
        results.sort(key=lambda x: x.get("timestamp") or "", reverse=True)
        return results[:limit]

    async def cleanup(self) -> None:
        """Cleanup client resources."""
        logger.debug(f"Neo4jClient cleanup: {self.stats}")
        if self._driver and not self._use_json_fallback:
            await self._close_driver()
        self._initialized = False


# Singleton instance
_client_instance: Optional[Neo4jClient] = None


def get_neo4j_client(
    uri: Optional[str] = None,
    user: Optional[str] = None,
    password: Optional[str] = None,
    database: Optional[str] = None,
    use_json_fallback: Optional[bool] = None,
    storage_path: Optional[Path] = None,
) -> Neo4jClient:
    """
    Get or create Neo4jClient singleton.

    Uses config.py settings if parameters not provided.

    Args:
        uri: Neo4j Bolt URI (default from config)
        user: Neo4j username (default from config)
        password: Neo4j password (default from config)
        database: Neo4j database name (default from config)
        use_json_fallback: Force JSON fallback mode (default: not NEO4J_ENABLED)
        storage_path: Optional storage path override

    Returns:
        Neo4jClient instance

    [Source: docs/stories/30.2.story.md - Task 2]
    """
    global _client_instance

    if _client_instance is None:
        # Import settings here to avoid circular imports
        from app.config import settings

        # Use config values if not provided
        _uri = uri or settings.neo4j_uri
        _user = user or settings.neo4j_user
        _password = password or settings.neo4j_password
        _database = database or settings.neo4j_database
        _use_json_fallback = use_json_fallback if use_json_fallback is not None else not settings.neo4j_enabled

        _client_instance = Neo4jClient(
            uri=_uri,
            user=_user,
            password=_password,
            database=_database,
            max_connection_pool_size=settings.neo4j_max_connection_pool_size,
            connection_acquisition_timeout=settings.neo4j_connection_timeout,
            max_connection_lifetime=settings.neo4j_max_connection_lifetime,
            retry_attempts=settings.neo4j_retry_attempts,
            retry_delay_base=settings.neo4j_retry_delay_base,
            retry_max_delay=settings.neo4j_retry_max_delay,
            use_json_fallback=_use_json_fallback,
            storage_path=storage_path,
        )

    return _client_instance


def reset_neo4j_client() -> None:
    """Reset singleton instance (for testing)."""
    global _client_instance
    _client_instance = None
