"""
GraphitiTemporalClient - Graphiti时序查询客户端

Story 22.2: TemporalClient实现 (Graphiti时序查询)
- AC-22.2.1: 能够存储学习事件 (episode) 到Graphiti
- AC-22.2.2: 能够按时间范围查询事件
- AC-22.2.3: 能够按实体类型 (Concept, CanvasNode) 查询
- AC-22.2.4: 支持时间窗口聚合查询 (日/周/月统计)
- AC-22.2.5: 与Graphiti库正确集成
- AC-22.2.6: 单元测试覆盖TemporalClient

✅ Verified from Graphiti Skill (SKILL.md - Quick Reference > Installation and Setup):
- Neo4jDriver initialization pattern
- add_episode() method signature
- search() method with hybrid retrieval

Author: Canvas Learning System Team
Version: 1.0.0
Created: 2025-12-12
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Literal, Optional

try:
    from loguru import logger
    LOGURU_ENABLED = True
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    LOGURU_ENABLED = False

# ✅ Verified from Graphiti Skill (SKILL.md - Quick Reference > Installation and Setup)
# graphiti-core provides temporal knowledge graph capabilities
try:
    from graphiti_core import Graphiti
    from graphiti_core.driver.neo4j_driver import Neo4jDriver
    GRAPHITI_AVAILABLE = True
except ImportError:
    GRAPHITI_AVAILABLE = False
    Graphiti = None
    Neo4jDriver = None


class GraphitiTemporalClient:
    """
    Graphiti时序查询客户端

    支持学习事件的存储和时序查询，用于学习历史追踪和艾宾浩斯复习。

    ✅ Verified from Story 22.2 (docs/stories/22.2.story.md):
    - AC-22.2.1: add_learning_episode() 存储学习事件
    - AC-22.2.2: search_by_time_range() 时间范围查询
    - AC-22.2.3: search_by_entity_type() 实体类型查询
    - AC-22.2.4: get_learning_stats() 时间窗口聚合
    - AC-22.2.5: Graphiti集成

    ✅ Verified from Graphiti Skill (SKILL.md - Quick Reference):
    - Neo4jDriver for database connection
    - add_episode() for episodic data ingestion
    - search() for hybrid retrieval

    Usage:
        >>> client = GraphitiTemporalClient(
        ...     neo4j_uri="bolt://localhost:7687",
        ...     neo4j_user="neo4j",
        ...     neo4j_password="password"
        ... )
        >>> await client.initialize()
        >>> episode_id = await client.add_learning_episode(
        ...     content="学习了逆否命题的概念",
        ...     episode_type="learning",
        ...     metadata={"canvas_path": "离散数学.canvas", "node_id": "node_123"}
        ... )
        >>> print(f"Created episode: {episode_id}")
    """

    def __init__(
        self,
        neo4j_uri: str = "bolt://localhost:7687",
        neo4j_user: str = "neo4j",
        neo4j_password: str = "",
        timeout_ms: int = 500,
        enable_fallback: bool = True
    ):
        """
        初始化GraphitiTemporalClient

        ✅ Verified from Graphiti Skill (SKILL.md - Basic Initialization with Neo4j)

        Args:
            neo4j_uri: Neo4j数据库URI
            neo4j_user: Neo4j用户名
            neo4j_password: Neo4j密码
            timeout_ms: 操作超时时间(毫秒), 默认500ms
            enable_fallback: 启用降级(超时/错误时返回空结果或模拟ID)
        """
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
        self.timeout_ms = timeout_ms
        self.enable_fallback = enable_fallback

        self._graphiti: Optional[Graphiti] = None
        self._driver: Optional[Neo4jDriver] = None
        self._initialized = False

        # Episode缓存 (用于本地查询优化和fallback模式)
        self._episode_cache: List[Dict[str, Any]] = []

    async def initialize(self) -> bool:
        """
        初始化Graphiti客户端

        ✅ Story 22.2 AC-22.2.5: 与Graphiti库正确集成
        ✅ Verified from Graphiti Skill (SKILL.md - Basic Initialization with Neo4j):

        ```python
        driver = Neo4jDriver(
            uri="bolt://localhost:7687",
            user="neo4j",
            password="your_password"
        )
        graphiti = Graphiti(driver)
        ```

        Returns:
            True if initialization successful
        """
        if not GRAPHITI_AVAILABLE:
            if LOGURU_ENABLED:
                logger.warning(
                    "graphiti-core not available. "
                    "Install: pip install graphiti-core[neo4j]"
                )
            self._initialized = True
            return False

        try:
            # ✅ Verified from Graphiti Skill - Neo4jDriver initialization
            self._driver = Neo4jDriver(
                uri=self.neo4j_uri,
                user=self.neo4j_user,
                password=self.neo4j_password
            )

            # ✅ Verified from Graphiti Skill - Graphiti initialization
            self._graphiti = Graphiti(self._driver)

            self._initialized = True

            if LOGURU_ENABLED:
                logger.info(
                    f"GraphitiTemporalClient initialized: uri={self.neo4j_uri}"
                )

            return True

        except Exception as e:
            if LOGURU_ENABLED:
                logger.error(f"GraphitiTemporalClient initialization failed: {e}")

            self._initialized = True
            return False

    async def add_learning_episode(
        self,
        content: str,
        episode_type: str = "learning",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        添加学习事件

        ✅ Story 22.2 AC-22.2.1: 能够存储学习事件 (episode) 到Graphiti

        ✅ Verified from Graphiti Skill (SKILL.md - Adding Text Episodes):
        ```python
        await graphiti.add_episode(
            name="user_conversation",
            episode_body="Kendra mentioned she loves Adidas shoes...",
            source_description="Chat conversation",
            reference_time=datetime.now()
        )
        ```

        Args:
            content: 学习内容描述
            episode_type: 事件类型 (learning, review, assessment)
            metadata: 额外元数据 (canvas_path, node_id, score等)

        Returns:
            episode_id: 新创建的Episode ID
        """
        if not self._initialized:
            await self.initialize()

        timestamp = datetime.now()
        episode_name = f"{episode_type}_{timestamp.isoformat()}"

        # 构建完整的episode内容(包含metadata)
        full_content = content
        if metadata:
            metadata_str = ", ".join(f"{k}={v}" for k, v in metadata.items())
            full_content = f"{content} [metadata: {metadata_str}]"

        # 缓存episode用于本地查询
        episode_record = {
            "uuid": episode_name,
            "name": episode_name,
            "episode_body": content,
            "source_description": f"Canvas Learning - {episode_type}",
            "reference_time": timestamp,
            "created_at": timestamp,
            "episode_type": episode_type,
            "metadata": metadata or {}
        }
        self._episode_cache.append(episode_record)

        if self._graphiti is not None:
            try:
                # ✅ Verified from Graphiti Skill - add_episode method
                timeout_seconds = self.timeout_ms / 1000.0

                episode = await asyncio.wait_for(
                    self._graphiti.add_episode(
                        name=episode_name,
                        episode_body=full_content,
                        source_description=f"Canvas Learning - {episode_type}",
                        reference_time=timestamp
                    ),
                    timeout=timeout_seconds
                )

                # 使用Graphiti返回的UUID
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
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        按时间范围搜索学习事件

        ✅ Story 22.2 AC-22.2.2: 能够按时间范围查询事件

        ✅ Verified from Graphiti Skill (SKILL.md - Searching the Graph):
        ```python
        results = await graphiti.search(
            query="What are Kendra's preferences?",
            num_results=10,
            center_node_uuid=None
        )
        ```

        Args:
            start_time: 开始时间
            end_time: 结束时间
            entity_type: 可选的实体类型过滤 (Concept, CanvasNode等)
            limit: 返回结果数量限制

        Returns:
            学习事件列表
        """
        if not self._initialized:
            await self.initialize()

        results = []

        if self._graphiti is not None:
            try:
                # ✅ Verified from Graphiti Skill - search method
                timeout_seconds = self.timeout_ms / 1000.0

                # 使用时间范围构建查询
                query = f"learning events from {start_time.isoformat()} to {end_time.isoformat()}"
                if entity_type:
                    query = f"{entity_type} {query}"

                search_results = await asyncio.wait_for(
                    self._graphiti.search(
                        query=query,
                        num_results=limit
                    ),
                    timeout=timeout_seconds
                )

                # 转换结果并过滤时间范围
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

        # Fallback: 从本地缓存查询
        if not results:
            for episode in self._episode_cache:
                created_at = episode.get("created_at")
                if created_at and start_time <= created_at <= end_time:
                    if entity_type is None:
                        results.append(self._episode_to_dict(episode))
                    else:
                        # 检查metadata中的entity_type
                        ep_entity_type = episode.get("metadata", {}).get("entity_type")
                        if ep_entity_type == entity_type:
                            results.append(self._episode_to_dict(episode))

        return results[:limit]

    async def search_by_entity_type(
        self,
        entity_type: str,
        canvas_file: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        按实体类型搜索

        ✅ Story 22.2 AC-22.2.3: 能够按实体类型 (Concept, CanvasNode) 查询

        Args:
            entity_type: 实体类型 (Concept, CanvasNode, LearningSession等)
            canvas_file: Canvas文件路径过滤(可选)
            limit: 返回结果数量
            offset: 分页偏移量

        Returns:
            实体列表
        """
        if not self._initialized:
            await self.initialize()

        results = []

        if self._graphiti is not None:
            try:
                timeout_seconds = self.timeout_ms / 1000.0

                # 构建实体类型查询
                query = f"{entity_type} entities"
                if canvas_file:
                    query = f"{query} in {canvas_file}"

                search_results = await asyncio.wait_for(
                    self._graphiti.search(
                        query=query,
                        num_results=limit + offset
                    ),
                    timeout=timeout_seconds
                )

                # 处理结果
                all_results = []
                for item in (search_results.edges if hasattr(search_results, 'edges') else []):
                    result_dict = self._to_dict(item)
                    all_results.append(result_dict)

                # 应用分页
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
                ep_metadata = episode.get("metadata", {})
                ep_canvas = ep_metadata.get("canvas_path", "")

                if entity_type.lower() in episode.get("episode_type", "").lower():
                    if canvas_file is None or canvas_file == ep_canvas:
                        filtered.append(self._episode_to_dict(episode))

            results = filtered[offset:offset + limit]

        return results

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
            统计数据字典:
            {
                "user_id": str,
                "granularity": str,
                "periods": [
                    {
                        "period_start": str (ISO格式),
                        "period_end": str (ISO格式),
                        "episode_count": int,
                        "concepts_learned": int,
                        "total_duration_seconds": int,
                        "average_score": float
                    }
                ],
                "summary": {
                    "total_episodes": int,
                    "total_concepts": int,
                    "average_episodes_per_period": float
                }
            }
        """
        if not self._initialized:
            await self.initialize()

        # 计算时间窗口
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

        # 聚合统计
        period_stats = []
        total_episodes = 0
        all_concepts = set()

        for period in periods:
            # 查询该时间窗口的事件
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

                # 收集概念
                concept = metadata.get("concept")
                if concept:
                    concepts.add(concept)
                    all_concepts.add(concept)

                # 累计时长
                duration = metadata.get("duration_seconds", 0)
                total_duration += duration

                # 收集分数
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

        # 计算汇总
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
        """
        将Graphiti结果转换为字典

        Args:
            result: Graphiti搜索结果项

        Returns:
            标准化的字典格式
        """
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
        """
        将本地缓存的episode转换为标准字典格式

        Args:
            episode: 本地缓存的episode记录

        Returns:
            标准化的字典格式
        """
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
        return {
            "initialized": self._initialized,
            "neo4j_uri": self.neo4j_uri,
            "timeout_ms": self.timeout_ms,
            "enable_fallback": self.enable_fallback,
            "graphiti_available": GRAPHITI_AVAILABLE,
            "graphiti_connected": self._graphiti is not None,
            "cached_episodes": len(self._episode_cache)
        }

    async def close(self):
        """关闭客户端连接"""
        if self._driver is not None:
            try:
                # 关闭Neo4j驱动连接
                await self._driver.close()
            except Exception:
                pass

        self._graphiti = None
        self._driver = None
        self._initialized = False

        if LOGURU_ENABLED:
            logger.info("GraphitiTemporalClient closed")
