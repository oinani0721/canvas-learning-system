"""
GraphitiTemporalClient - Graphiti时序查询客户端

Story 36.1: Unified GraphitiClient Architecture
- AC-36.1.2: Refactored to inherit from GraphitiClientBase
- AC-36.1.3: Neo4jClient injection via constructor (dependency injection)
- AC-36.1.5: Removed duplicate Neo4j driver creation (~80 lines)

Story 22.2: TemporalClient实现 (Graphiti时序查询)
- AC-22.2.1: 能够存储学习事件 (episode) 到Graphiti
- AC-22.2.2: 能够按时间范围查询事件
- AC-22.2.3: 能够按实体类型 (Concept, CanvasNode) 查询
- AC-22.2.4: 支持时间窗口聚合查询 (日/周/月统计)
- AC-22.2.5: 与Graphiti库正确集成
- AC-22.2.6: 单元测试覆盖TemporalClient

Story 30.8: 多学科隔离与group_id支持 (Task 2)
- AC-30.8.1: group_id namespace isolation for multi-subject learning
- AC-30.8.2: Auto-extract subject from canvas_path
- AC-30.8.3: Filter queries by group_id

Author: Canvas Learning System Team
Version: 2.0.0  # Updated for Story 36.1 - Unified GraphitiClient Architecture
Created: 2025-12-12
Updated: 2026-01-20

[Source: docs/stories/36.1.story.md]
[Source: docs/stories/22.2.story.md]
[Source: docs/stories/30.8.story.md]
"""

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, TYPE_CHECKING

# Add backend to path for imports
backend_path = Path(__file__).parent.parent.parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

try:
    from loguru import logger
    LOGURU_ENABLED = True
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    LOGURU_ENABLED = False

# Story 36.1: Import unified base class
try:
    from backend.app.clients.graphiti_client_base import (
        GraphitiClientBase,
        EdgeRelationship,
    )
    GRAPHITI_BASE_AVAILABLE = True
except ImportError:
    GRAPHITI_BASE_AVAILABLE = False
    GraphitiClientBase = object  # Fallback to object

if TYPE_CHECKING:
    from backend.app.clients.neo4j_client import Neo4jClient

# graphiti-core provides temporal knowledge graph capabilities
try:
    from graphiti_core import Graphiti
    from graphiti_core.driver.neo4j_driver import Neo4jDriver
    GRAPHITI_AVAILABLE = True
except ImportError:
    GRAPHITI_AVAILABLE = False
    Graphiti = None
    Neo4jDriver = None


class GraphitiTemporalClient(GraphitiClientBase if GRAPHITI_BASE_AVAILABLE else object):
    """
    Graphiti时序查询客户端

    Story 36.1 AC-36.1.2: Refactored to inherit from GraphitiClientBase.

    支持学习事件的存储和时序查询，用于学习历史追踪和艾宾浩斯复习。

    This client:
    1. Inherits from GraphitiClientBase (AC-36.1.1)
    2. Receives Neo4jClient via constructor (AC-36.1.3)
    3. Uses Neo4jClient's connection params for graphiti_core.Neo4jDriver
    4. Supports JSON fallback mode when Neo4j is unavailable

    ✅ Verified from ADR-003: Graphiti as knowledge graph middleware
    ✅ Verified from ADR-009: All external calls use tenacity retry (via Neo4jClient)

    [Source: docs/stories/36.1.story.md#Task-3]
    [Source: docs/stories/22.2.story.md]
    """

    def __init__(
        self,
        neo4j_client: "Neo4jClient",
        timeout_ms: int = 500,
        enable_fallback: bool = True,
        default_group_id: Optional[str] = None
    ):
        """
        Initialize GraphitiTemporalClient with Neo4jClient injection.

        Story 36.1 AC-36.1.3: Neo4jClient injection

        Args:
            neo4j_client: Neo4jClient instance from Story 30.2
                         Reuses connection pool (50 connections, 30s timeout)
                         Reuses retry mechanism (tenacity 3x exponential backoff)
            timeout_ms: 操作超时时间(毫秒), 默认500ms
            enable_fallback: 启用降级(超时/错误时返回空结果或模拟ID)
            default_group_id: 默认group_id用于多学科隔离 (AC-30.8.1)

        Raises:
            ValueError: If neo4j_client is None

        [Source: docs/stories/36.1.story.md#AC-36.1.3]
        """
        # Story 36.1: Initialize base class with Neo4jClient
        if GRAPHITI_BASE_AVAILABLE:
            super().__init__(neo4j_client)
        else:
            # Fallback: store neo4j_client directly
            if neo4j_client is None:
                raise ValueError(
                    "neo4j_client cannot be None. "
                    "Use dependency injection via get_graphiti_temporal_client()"
                )
            self._neo4j = neo4j_client
            self._initialized = False

        self.timeout_ms = timeout_ms
        self.enable_fallback = enable_fallback
        self.default_group_id = default_group_id

        # graphiti_core.Graphiti instance (created in initialize())
        self._graphiti: Optional[Graphiti] = None
        self._graphiti_driver: Optional[Neo4jDriver] = None

        # Episode缓存 (用于本地查询优化和fallback模式)
        self._episode_cache: List[Dict[str, Any]] = []

        if LOGURU_ENABLED:
            logger.debug(
                f"GraphitiTemporalClient initialized with Neo4jClient: "
                f"mode={self._neo4j.stats.get('mode', 'unknown')}, "
                f"timeout={timeout_ms}ms"
            )

    def _build_group_id(
        self,
        canvas_path: Optional[str] = None,
        group_id: Optional[str] = None
    ) -> Optional[str]:
        """
        构建group_id用于多学科隔离

        ✅ Story 30.8 Task 2.2: _build_group_id helper function

        Priority order:
        1. Explicit group_id parameter (highest priority)
        2. Extract from canvas_path using subject_config
        3. Default group_id from client initialization
        4. None (no isolation)

        Args:
            canvas_path: Canvas文件路径 (e.g., "数学/离散数学.canvas")
            group_id: 显式指定的group_id

        Returns:
            Sanitized group_id string or None

        [Source: docs/stories/30.8.story.md#Task-2.2]
        """
        # Priority 1: Explicit group_id
        if group_id:
            return group_id

        # Priority 2: Extract from canvas_path
        if canvas_path:
            try:
                from backend.app.core.subject_config import (
                    build_group_id,
                    extract_subject_from_canvas_path,
                )

                subject = extract_subject_from_canvas_path(canvas_path)
                return build_group_id(subject)
            except ImportError:
                # Fallback if backend module not available
                if LOGURU_ENABLED:
                    logger.warning(
                        "subject_config not available, using canvas_path as group_id"
                    )
                # Simple fallback: use first directory as subject
                path = Path(canvas_path)
                parts = list(path.parts)
                if parts and not parts[0].endswith('.canvas'):
                    return parts[0].lower().replace(' ', '_')

        # Priority 3: Default group_id
        if self.default_group_id:
            return self.default_group_id

        # Priority 4: No isolation
        return None

    async def initialize(self) -> bool:
        """
        Initialize Graphiti client using Neo4jClient connection params.

        Story 36.1 Task 3.4: Keep graphiti_core.Graphiti integration,
        but use connection params from injected Neo4jClient.

        Returns:
            True if initialization successful
        """
        if self._initialized:
            return True

        # Initialize underlying Neo4jClient first
        if GRAPHITI_BASE_AVAILABLE:
            await super().initialize()

        if not GRAPHITI_AVAILABLE:
            if LOGURU_ENABLED:
                logger.warning(
                    "graphiti-core not available. "
                    "Install: pip install graphiti-core[neo4j]"
                )
            self._initialized = True
            return False

        try:
            # Story 36.1 Task 3.4: Get connection params from Neo4jClient
            # instead of accepting them directly
            neo4j_stats = self._neo4j.stats
            neo4j_uri = neo4j_stats.get("uri") or "bolt://localhost:7687"

            # Neo4jClient doesn't expose user/password directly for security
            # We use environment-based config instead
            from backend.app.config import settings
            neo4j_user = settings.neo4j_user
            neo4j_password = settings.neo4j_password

            # Create graphiti_core.Neo4jDriver with same connection params
            self._graphiti_driver = Neo4jDriver(
                uri=neo4j_uri,
                user=neo4j_user,
                password=neo4j_password
            )

            # Create Graphiti instance
            self._graphiti = Graphiti(self._graphiti_driver)

            self._initialized = True

            if LOGURU_ENABLED:
                logger.info(
                    f"GraphitiTemporalClient initialized: uri={neo4j_uri}"
                )

            return True

        except Exception as e:
            if LOGURU_ENABLED:
                logger.error(f"GraphitiTemporalClient initialization failed: {e}")

            self._initialized = True
            return False

    # =========================================================================
    # GraphitiClientBase abstract method implementations
    # Story 36.1 AC-36.1.1
    # =========================================================================

    async def add_edge_relationship(
        self,
        relationship: EdgeRelationship
    ) -> bool:
        """
        Add a single edge relationship to the knowledge graph.

        Story 36.1 AC-36.1.1: Abstract interface implementation

        Args:
            relationship: EdgeRelationship to add

        Returns:
            True if successful

        [Source: docs/stories/36.1.story.md#AC-36.1.1]
        """
        if not self._initialized:
            await self.initialize()

        try:
            # Delegate to Neo4jClient for edge creation
            success = await self._neo4j.create_edge_relationship(
                canvas_path=relationship.canvas_path,
                edge_id=relationship.edge_id or f"edge-{relationship.from_node_id}-{relationship.to_node_id}",
                from_node_id=relationship.from_node_id,
                to_node_id=relationship.to_node_id,
                edge_label=relationship.edge_label,
            )
            return success

        except Exception as e:
            if LOGURU_ENABLED:
                logger.warning(f"add_edge_relationship failed: {e}")
            return False

    async def search_nodes(
        self,
        query: str,
        canvas_path: Optional[str] = None,
        group_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for nodes in the knowledge graph.

        Story 36.1 AC-36.1.1: Abstract interface implementation

        Args:
            query: Search query string
            canvas_path: Optional Canvas file path filter
            group_id: Optional group_id filter for multi-subject isolation
            limit: Maximum number of results

        Returns:
            List of search results

        [Source: docs/stories/36.1.story.md#AC-36.1.1]
        """
        if not self._initialized:
            await self.initialize()

        # Build effective group_id
        effective_group_id = self._build_group_id(
            canvas_path=canvas_path,
            group_id=group_id
        )

        results = []

        if self._graphiti is not None:
            try:
                timeout_seconds = self.timeout_ms / 1000.0

                # Build search kwargs
                search_kwargs = {
                    "query": query,
                    "num_results": limit
                }

                if effective_group_id:
                    search_kwargs["group_id"] = effective_group_id

                search_results = await asyncio.wait_for(
                    self._graphiti.search(**search_kwargs),
                    timeout=timeout_seconds
                )

                # Convert results
                for item in (search_results.edges if hasattr(search_results, 'edges') else []):
                    results.append({
                        "doc_id": getattr(item, 'uuid', None) or getattr(item, 'id', ''),
                        "content": getattr(item, 'fact', '') or getattr(item, 'content', ''),
                        "score": getattr(item, 'score', 1.0),
                        "metadata": {
                            "canvas_path": canvas_path,
                            "group_id": effective_group_id,
                        }
                    })

            except asyncio.TimeoutError:
                if LOGURU_ENABLED:
                    logger.warning(f"search_nodes timeout ({self.timeout_ms}ms)")
                if not self.enable_fallback:
                    raise

            except Exception as e:
                if LOGURU_ENABLED:
                    logger.error(f"search_nodes error: {e}")
                if not self.enable_fallback:
                    raise

        return results

    async def get_related_memories(
        self,
        node_id: str,
        canvas_path: Optional[str] = None,
        limit: int = 10
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

        results = []

        if self._graphiti is not None:
            try:
                timeout_seconds = self.timeout_ms / 1000.0

                # Search for related content
                search_kwargs = {
                    "query": f"related to node {node_id}",
                    "num_results": limit
                }

                if canvas_path:
                    effective_group_id = self._build_group_id(canvas_path=canvas_path)
                    if effective_group_id:
                        search_kwargs["group_id"] = effective_group_id

                search_results = await asyncio.wait_for(
                    self._graphiti.search(**search_kwargs),
                    timeout=timeout_seconds
                )

                for item in (search_results.edges if hasattr(search_results, 'edges') else []):
                    results.append({
                        "node_id": getattr(item, 'uuid', '') or getattr(item, 'id', ''),
                        "content": getattr(item, 'fact', '') or getattr(item, 'content', ''),
                        "relationship": "RELATED_TO",
                        "canvas_path": canvas_path,
                    })

            except asyncio.TimeoutError:
                if LOGURU_ENABLED:
                    logger.warning(f"get_related_memories timeout ({self.timeout_ms}ms)")
                if not self.enable_fallback:
                    raise

            except Exception as e:
                if LOGURU_ENABLED:
                    logger.error(f"get_related_memories error: {e}")
                if not self.enable_fallback:
                    raise

        return results

    # =========================================================================
    # Temporal-specific methods (Story 22.2)
    # =========================================================================

    async def add_learning_episode(
        self,
        content: str,
        episode_type: str = "learning",
        metadata: Optional[Dict[str, Any]] = None,
        group_id: Optional[str] = None
    ) -> str:
        """
        添加学习事件

        ✅ Story 22.2 AC-22.2.1: 能够存储学习事件 (episode) 到Graphiti
        ✅ Story 30.8 Task 2.1: Added group_id parameter for namespace isolation

        Args:
            content: 学习内容描述
            episode_type: 事件类型 (learning, review, assessment)
            metadata: 额外元数据 (canvas_path, node_id, score等)
            group_id: 显式指定的group_id，如不指定则从metadata.canvas_path推断

        Returns:
            episode_id: 新创建的Episode ID

        [Source: docs/stories/30.8.story.md#Task-2.1]
        """
        if not self._initialized:
            await self.initialize()

        timestamp = datetime.now()
        episode_name = f"{episode_type}_{timestamp.isoformat()}"

        # Build effective group_id (Story 30.8 Task 2.1)
        canvas_path = (metadata or {}).get("canvas_path")
        effective_group_id = self._build_group_id(
            canvas_path=canvas_path,
            group_id=group_id
        )

        # 构建完整的episode内容(包含metadata)
        full_content = content
        if metadata:
            metadata_str = ", ".join(f"{k}={v}" for k, v in metadata.items())
            full_content = f"{content} [metadata: {metadata_str}]"

        # 缓存episode用于本地查询 (include group_id for filtering)
        episode_record = {
            "uuid": episode_name,
            "name": episode_name,
            "episode_body": content,
            "source_description": f"Canvas Learning - {episode_type}",
            "reference_time": timestamp,
            "created_at": timestamp,
            "episode_type": episode_type,
            "metadata": metadata or {},
            "group_id": effective_group_id
        }
        self._episode_cache.append(episode_record)

        if self._graphiti is not None:
            try:
                timeout_seconds = self.timeout_ms / 1000.0

                # Build kwargs for add_episode
                add_episode_kwargs = {
                    "name": episode_name,
                    "episode_body": full_content,
                    "source_description": f"Canvas Learning - {episode_type}",
                    "reference_time": timestamp
                }

                # Add group_id if available (Story 30.8 AC-30.8.1)
                if effective_group_id:
                    add_episode_kwargs["group_id"] = effective_group_id

                episode = await asyncio.wait_for(
                    self._graphiti.add_episode(**add_episode_kwargs),
                    timeout=timeout_seconds
                )

                episode_id = getattr(episode, 'uuid', episode_name)
                episode_record["uuid"] = episode_id

                if LOGURU_ENABLED:
                    logger.info(f"Added learning episode: {episode_id}")

                return episode_id

            except asyncio.TimeoutError:
                if LOGURU_ENABLED:
                    logger.warning(
                        f"add_learning_episode timeout ({self.timeout_ms}ms)"
                    )
                if self.enable_fallback:
                    return episode_name
                raise

            except Exception as e:
                if LOGURU_ENABLED:
                    logger.error(f"add_learning_episode error: {e}")
                if self.enable_fallback:
                    return episode_name
                raise
        else:
            # Fallback: 返回本地生成的ID
            if LOGURU_ENABLED:
                logger.warning(
                    "Graphiti not available, using local episode cache"
                )
            return episode_name

    async def search_by_time_range(
        self,
        start_time: datetime,
        end_time: datetime,
        entity_type: Optional[str] = None,
        limit: int = 100,
        group_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        按时间范围搜索学习事件

        ✅ Story 22.2 AC-22.2.2: 能够按时间范围查询事件
        ✅ Story 30.8 Task 2.1: Added group_id filter for namespace isolation

        Args:
            start_time: 开始时间
            end_time: 结束时间
            entity_type: 可选的实体类型过滤 (Concept, CanvasNode等)
            limit: 返回结果数量限制
            group_id: 可选的group_id过滤，用于多学科隔离 (AC-30.8.3)

        Returns:
            学习事件列表

        [Source: docs/stories/30.8.story.md#Task-2.1]
        """
        if not self._initialized:
            await self.initialize()

        # Build effective group_id for filtering
        effective_group_id = self._build_group_id(group_id=group_id)

        results = []

        if self._graphiti is not None:
            try:
                timeout_seconds = self.timeout_ms / 1000.0

                query = f"learning events from {start_time.isoformat()} to {end_time.isoformat()}"
                if entity_type:
                    query = f"{entity_type} {query}"

                search_kwargs = {
                    "query": query,
                    "num_results": limit
                }

                if effective_group_id:
                    search_kwargs["group_id"] = effective_group_id

                search_results = await asyncio.wait_for(
                    self._graphiti.search(**search_kwargs),
                    timeout=timeout_seconds
                )

                for item in (search_results.edges if hasattr(search_results, 'edges') else []):
                    created_at = getattr(item, 'created_at', None)
                    if created_at and start_time <= created_at <= end_time:
                        result_dict = self._to_dict(item)
                        if entity_type is None or result_dict.get("entity_type") == entity_type:
                            results.append(result_dict)

            except asyncio.TimeoutError:
                if LOGURU_ENABLED:
                    logger.warning(
                        f"search_by_time_range timeout ({self.timeout_ms}ms)"
                    )
                if not self.enable_fallback:
                    raise

            except Exception as e:
                if LOGURU_ENABLED:
                    logger.error(f"search_by_time_range error: {e}")
                if not self.enable_fallback:
                    raise

        # Fallback: 从本地缓存查询 (with group_id filter)
        if not results:
            for episode in self._episode_cache:
                created_at = episode.get("created_at")
                if created_at and start_time <= created_at <= end_time:
                    # Filter by group_id if specified
                    if effective_group_id:
                        ep_group_id = episode.get("group_id")
                        if ep_group_id != effective_group_id:
                            continue

                    if entity_type is None:
                        results.append(self._episode_to_dict(episode))
                    else:
                        ep_entity_type = episode.get("metadata", {}).get("entity_type")
                        if ep_entity_type == entity_type:
                            results.append(self._episode_to_dict(episode))

        return results[:limit]

    async def search_by_entity_type(
        self,
        entity_type: str,
        canvas_file: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        group_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        按实体类型搜索

        ✅ Story 22.2 AC-22.2.3: 能够按实体类型 (Concept, CanvasNode) 查询
        ✅ Story 30.8 Task 2.1: Added group_id filter for namespace isolation

        Args:
            entity_type: 实体类型 (Concept, CanvasNode, LearningSession等)
            canvas_file: Canvas文件路径过滤(可选)
            limit: 返回结果数量
            offset: 分页偏移量
            group_id: 可选的group_id过滤，用于多学科隔离 (AC-30.8.3)

        Returns:
            实体列表

        [Source: docs/stories/30.8.story.md#Task-2.1]
        """
        if not self._initialized:
            await self.initialize()

        # Build effective group_id
        effective_group_id = self._build_group_id(
            canvas_path=canvas_file,
            group_id=group_id
        )

        results = []

        if self._graphiti is not None:
            try:
                timeout_seconds = self.timeout_ms / 1000.0

                query = f"{entity_type} entities"
                if canvas_file:
                    query = f"{query} in {canvas_file}"

                search_kwargs = {
                    "query": query,
                    "num_results": limit + offset
                }

                if effective_group_id:
                    search_kwargs["group_id"] = effective_group_id

                search_results = await asyncio.wait_for(
                    self._graphiti.search(**search_kwargs),
                    timeout=timeout_seconds
                )

                all_results = []
                for item in (search_results.edges if hasattr(search_results, 'edges') else []):
                    all_results.append(self._to_dict(item))

                results = all_results[offset:offset + limit]

            except asyncio.TimeoutError:
                if LOGURU_ENABLED:
                    logger.warning(
                        f"search_by_entity_type timeout ({self.timeout_ms}ms)"
                    )
                if not self.enable_fallback:
                    raise

            except Exception as e:
                if LOGURU_ENABLED:
                    logger.error(f"search_by_entity_type error: {e}")
                if not self.enable_fallback:
                    raise

        # Fallback: 从本地缓存查询
        if not results:
            filtered = []
            for episode in self._episode_cache:
                if effective_group_id:
                    ep_group_id = episode.get("group_id")
                    if ep_group_id != effective_group_id:
                        continue

                ep_metadata = episode.get("metadata", {})
                ep_canvas = ep_metadata.get("canvas_path", "")

                if entity_type.lower() in episode.get("episode_type", "").lower():
                    if canvas_file is None or canvas_file == ep_canvas:
                        filtered.append(self._episode_to_dict(episode))

            results = filtered[offset:offset + limit]

        return results

    # =========================================================================
    # Story 31.4: Verification Question Search Methods
    # [Source: docs/stories/31.4.story.md#Task-1]
    # =========================================================================

    async def search_verification_questions(
        self,
        concept: str,
        canvas_name: Optional[str] = None,
        time_range: Optional[tuple] = None,
        limit: int = 10,
        group_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        查询概念的历史检验问题

        Story 31.4 AC-31.4.1: 问题生成前查询Graphiti检查是否已存在相同概念的验证问题

        Args:
            concept: 概念名称
            canvas_name: Canvas名称过滤(可选)
            time_range: 时间范围过滤(可选), tuple of (start_time, end_time)
            limit: 返回数量限制
            group_id: 学科隔离ID

        Returns:
            List of verification questions with metadata:
            [
                {
                    "question_id": str,
                    "question_text": str,
                    "question_type": str,  # standard/application/comparison/etc
                    "asked_at": str (ISO format),
                    "score": Optional[int],
                    "user_answer": Optional[str],
                    "canvas_name": str
                }
            ]

        [Source: ADR-0003 Graphiti Memory, Hybrid Search section]
        [Source: docs/stories/31.4.story.md#Task-1]
        """
        if not self._initialized:
            await self.initialize()

        # Build effective group_id (AC-30.8.3: multi-subject isolation)
        effective_group_id = self._build_group_id(
            canvas_path=canvas_name,
            group_id=group_id
        )

        results = []

        if self._graphiti is not None:
            try:
                timeout_seconds = self.timeout_ms / 1000.0

                # Build search query for verification questions
                # Format matches how questions are stored (see Task 6)
                query = f"验证问题 概念:{concept}"
                if canvas_name:
                    query = f"{query} Canvas:{canvas_name}"

                search_kwargs = {
                    "query": query,
                    "num_results": limit * 2  # Fetch extra for filtering
                }

                if effective_group_id:
                    search_kwargs["group_id"] = effective_group_id

                # ✅ Verified from ADR-0003: Graphiti search() supports query + filters
                search_results = await asyncio.wait_for(
                    self._graphiti.search(**search_kwargs),
                    timeout=timeout_seconds
                )

                # Filter and format results
                for item in (search_results.edges if hasattr(search_results, 'edges') else []):
                    result_dict = self._format_verification_question_result(item, concept)

                    # Apply time_range filter if specified
                    if time_range and result_dict.get("asked_at"):
                        asked_at = datetime.fromisoformat(
                            result_dict["asked_at"].replace("Z", "+00:00")
                        )
                        start_time, end_time = time_range
                        if not (start_time <= asked_at <= end_time):
                            continue

                    # Apply canvas_name filter
                    if canvas_name:
                        item_canvas = result_dict.get("canvas_name", "")
                        if canvas_name not in item_canvas:
                            continue

                    results.append(result_dict)

                    if len(results) >= limit:
                        break

                if LOGURU_ENABLED:
                    logger.info(
                        f"search_verification_questions: concept={concept}, "
                        f"found={len(results)}, limit={limit}"
                    )

            except asyncio.TimeoutError:
                # AC-31.4 ADR-009: Graceful degradation on timeout
                if LOGURU_ENABLED:
                    logger.warning(
                        f"search_verification_questions timeout ({self.timeout_ms}ms) "
                        f"for concept: {concept}"
                    )
                # Return empty results (fallback behavior)
                return []

            except Exception as e:
                if LOGURU_ENABLED:
                    logger.error(f"search_verification_questions error: {e}")
                if not self.enable_fallback:
                    raise
                return []

        # Fallback: search local episode cache
        if not results:
            for episode in self._episode_cache:
                metadata = episode.get("metadata", {})

                # Check if it's a verification question
                if metadata.get("type") != "verification_question":
                    continue

                # Check concept match
                if metadata.get("concept") != concept:
                    continue

                # Check group_id filter
                if effective_group_id:
                    ep_group_id = episode.get("group_id")
                    if ep_group_id != effective_group_id:
                        continue

                # Check canvas_name filter
                if canvas_name:
                    ep_canvas = metadata.get("canvas_name", "")
                    if canvas_name not in ep_canvas:
                        continue

                # Format result
                created_at = episode.get("created_at")
                results.append({
                    "question_id": metadata.get("question_id", episode.get("uuid")),
                    "question_text": episode.get("episode_body", ""),
                    "question_type": metadata.get("question_type", "standard"),
                    "asked_at": created_at.isoformat() if created_at else None,
                    "score": metadata.get("score"),
                    "user_answer": metadata.get("user_answer"),
                    "canvas_name": metadata.get("canvas_name", "")
                })

                if len(results) >= limit:
                    break

        return results[:limit]

    def _format_verification_question_result(
        self,
        item: Any,
        concept: str
    ) -> Dict[str, Any]:
        """
        Format a Graphiti search result as verification question dict.

        Args:
            item: Graphiti search result item
            concept: The concept being queried

        Returns:
            Formatted verification question dict
        """
        # Extract metadata from item
        metadata = getattr(item, 'metadata', {}) or {}

        # Get timestamps
        created_at = getattr(item, 'created_at', None)
        if created_at:
            asked_at = created_at.isoformat()
        else:
            asked_at = metadata.get("asked_at")

        # Extract question text from content/fact
        content = (
            getattr(item, 'fact', None) or
            getattr(item, 'content', None) or
            getattr(item, 'episode_body', None) or
            ""
        )

        # Parse question text from episode format
        # Format: "验证问题: {question} | 概念: {concept} | Canvas: {canvas}"
        question_text = content
        if "验证问题:" in content:
            parts = content.split("|")
            for part in parts:
                if "验证问题:" in part:
                    question_text = part.replace("验证问题:", "").strip()
                    break

        return {
            "question_id": (
                metadata.get("question_id") or
                getattr(item, 'uuid', None) or
                getattr(item, 'id', None) or
                ""
            ),
            "question_text": question_text,
            "question_type": metadata.get("question_type", "standard"),
            "asked_at": asked_at,
            "score": metadata.get("score"),
            "user_answer": metadata.get("user_answer"),
            "canvas_name": metadata.get("canvas_name", "")
        }

    async def add_verification_question(
        self,
        question_text: str,
        concept: str,
        canvas_name: str,
        question_type: str = "standard",
        group_id: Optional[str] = None,
        question_id: Optional[str] = None
    ) -> str:
        """
        存储检验问题到Graphiti

        Story 31.4 Task 6.1: 在问题生成后调用此方法存储检验问题

        Args:
            question_text: 问题内容
            concept: 概念名称
            canvas_name: Canvas名称
            question_type: 问题类型 (standard/application/comparison/counterexample/synthesis)
            group_id: 学科隔离ID (可选)
            question_id: 问题ID (可选，自动生成如果未提供)

        Returns:
            question_id: 存储的问题ID

        [Source: docs/stories/31.4.story.md#Task-6]
        """
        import uuid as uuid_module

        if not self._initialized:
            await self.initialize()

        # Generate question_id if not provided
        if not question_id:
            question_id = f"vq-{uuid_module.uuid4().hex[:8]}"

        # Build episode content (Task 6.2 format)
        content = (
            f"验证问题: {question_text} | "
            f"概念: {concept} | "
            f"Canvas: {canvas_name} | "
            f"类型: {question_type}"
        )

        # Build metadata (Task 6.2)
        metadata = {
            "type": "verification_question",
            "concept": concept,
            "canvas_name": canvas_name,
            "question_type": question_type,
            "question_id": question_id,
        }

        # Build effective group_id (Task 6.3)
        effective_group_id = self._build_group_id(
            canvas_path=canvas_name,
            group_id=group_id
        )

        # Store using add_learning_episode (fire-and-forget pattern from ADR-0003)
        episode_id = await self.add_learning_episode(
            content=content,
            episode_type="verification_question",
            metadata=metadata,
            group_id=effective_group_id
        )

        if LOGURU_ENABLED:
            logger.info(
                f"Stored verification question: id={question_id}, "
                f"concept={concept}, type={question_type}"
            )

        return question_id

    async def get_learning_stats(
        self,
        user_id: str,
        granularity: Literal["day", "week", "month"] = "day",
        limit: int = 30
    ) -> Dict[str, Any]:
        """
        获取学习统计数据

        ✅ Story 22.2 AC-22.2.4: 支持时间窗口聚合查询 (日/周/月统计)

        Args:
            user_id: 用户ID
            granularity: 统计粒度 (day, week, month)
            limit: 返回的时间周期数

        Returns:
            统计数据字典
        """
        if not self._initialized:
            await self.initialize()

        now = datetime.now()
        periods = []

        for i in range(limit):
            if granularity == "day":
                period_start = now - timedelta(days=i + 1)
                period_end = now - timedelta(days=i)
            elif granularity == "week":
                period_start = now - timedelta(weeks=i + 1)
                period_end = now - timedelta(weeks=i)
            else:  # month
                period_start = now - timedelta(days=30 * (i + 1))
                period_end = now - timedelta(days=30 * i)

            periods.append({
                "period_start": period_start,
                "period_end": period_end
            })

        period_stats = []
        total_episodes = 0
        all_concepts = set()

        for period in periods:
            events = await self.search_by_time_range(
                start_time=period["period_start"],
                end_time=period["period_end"],
                limit=1000
            )

            episode_count = len(events)
            concepts = set()
            total_duration = 0
            scores = []

            for event in events:
                metadata = event.get("metadata", {})

                concept = metadata.get("concept")
                if concept:
                    concepts.add(concept)
                    all_concepts.add(concept)

                duration = metadata.get("duration_seconds", 0)
                total_duration += duration

                score = metadata.get("score")
                if score is not None:
                    scores.append(score)

            avg_score = sum(scores) / len(scores) if scores else 0.0

            period_stats.append({
                "period_start": period["period_start"].isoformat(),
                "period_end": period["period_end"].isoformat(),
                "episode_count": episode_count,
                "concepts_learned": len(concepts),
                "total_duration_seconds": total_duration,
                "average_score": round(avg_score, 2)
            })

            total_episodes += episode_count

        avg_per_period = total_episodes / limit if limit > 0 else 0

        return {
            "user_id": user_id,
            "granularity": granularity,
            "periods": period_stats,
            "summary": {
                "total_episodes": total_episodes,
                "total_concepts": len(all_concepts),
                "average_episodes_per_period": round(avg_per_period, 2)
            }
        }

    def _to_dict(self, result: Any) -> Dict[str, Any]:
        """将Graphiti结果转换为字典"""
        return {
            "uuid": getattr(result, 'uuid', None) or getattr(result, 'id', None),
            "name": getattr(result, 'name', None),
            "created_at": (
                getattr(result, 'created_at', None).isoformat()
                if hasattr(result, 'created_at') and result.created_at
                else None
            ),
            "content": (
                getattr(result, 'episode_body', None) or
                getattr(result, 'fact', None) or
                getattr(result, 'content', None)
            ),
            "entity_type": getattr(result, 'entity_type', None),
            "valid_at": (
                getattr(result, 'valid_at', None).isoformat()
                if hasattr(result, 'valid_at') and result.valid_at
                else None
            ),
            "invalid_at": (
                getattr(result, 'invalid_at', None).isoformat()
                if hasattr(result, 'invalid_at') and result.invalid_at
                else None
            ),
            "metadata": getattr(result, 'metadata', {})
        }

    def _episode_to_dict(self, episode: Dict[str, Any]) -> Dict[str, Any]:
        """将本地缓存的episode转换为标准字典格式"""
        created_at = episode.get("created_at")
        return {
            "uuid": episode.get("uuid"),
            "name": episode.get("name"),
            "created_at": created_at.isoformat() if created_at else None,
            "content": episode.get("episode_body"),
            "entity_type": episode.get("episode_type"),
            "valid_at": None,
            "invalid_at": None,
            "metadata": episode.get("metadata", {})
        }

    def get_stats(self) -> Dict[str, Any]:
        """获取客户端统计信息"""
        base_stats = {}
        if GRAPHITI_BASE_AVAILABLE and hasattr(super(), 'get_stats'):
            base_stats = super().get_stats()

        return {
            **base_stats,
            "timeout_ms": self.timeout_ms,
            "enable_fallback": self.enable_fallback,
            "default_group_id": self.default_group_id,
            "graphiti_available": GRAPHITI_AVAILABLE,
            "graphiti_connected": self._graphiti is not None,
            "cached_episodes": len(self._episode_cache)
        }

    async def close(self):
        """关闭客户端连接"""
        if self._graphiti_driver is not None:
            try:
                await self._graphiti_driver.close()
            except Exception:
                pass

        self._graphiti = None
        self._graphiti_driver = None
        self._initialized = False

        if LOGURU_ENABLED:
            logger.info("GraphitiTemporalClient closed")

    async def cleanup(self) -> None:
        """Cleanup client resources (GraphitiClientBase interface)."""
        await self.close()


# =============================================================================
# Factory function and singleton management
# =============================================================================

_client_instance: Optional[GraphitiTemporalClient] = None


def get_graphiti_temporal_client(
    neo4j_client: Optional["Neo4jClient"] = None,
    timeout_ms: int = 500,
    enable_fallback: bool = True,
    default_group_id: Optional[str] = None
) -> GraphitiTemporalClient:
    """
    Get or create GraphitiTemporalClient singleton.

    Story 36.1: Factory function with Neo4jClient dependency injection.

    Args:
        neo4j_client: Optional Neo4jClient instance (created if not provided)
        timeout_ms: Operation timeout in milliseconds
        enable_fallback: Enable graceful degradation
        default_group_id: Default group_id for multi-subject isolation

    Returns:
        GraphitiTemporalClient instance

    [Source: docs/stories/36.1.story.md#Task-4.2]
    """
    global _client_instance

    if _client_instance is None:
        if neo4j_client is None:
            from backend.app.clients.neo4j_client import get_neo4j_client
            neo4j_client = get_neo4j_client()

        _client_instance = GraphitiTemporalClient(
            neo4j_client=neo4j_client,
            timeout_ms=timeout_ms,
            enable_fallback=enable_fallback,
            default_group_id=default_group_id
        )

    return _client_instance


def reset_graphiti_temporal_client() -> None:
    """Reset singleton instance (for testing)."""
    global _client_instance
    _client_instance = None
