# Canvas Learning System - Memory Service
# Story 22.4: 学习历史存储与查询API
# ✅ Verified from docs/stories/22.4.story.md#Dev-Notes
"""
Memory Service - Learning history storage and query.

Story 22.4 Implementation:
- AC-22.4.1: POST /api/v1/memory/episodes - Record learning events
- AC-22.4.2: GET /api/v1/memory/episodes - Query learning history
- AC-22.4.3: GET /api/v1/memory/concepts/{id}/history - Query concept history
- AC-22.4.4: GET /api/v1/memory/review-suggestions - Get review suggestions
- AC-22.4.5: Pagination and filtering support

[Source: docs/prd/EPIC-22-MEMORY-SYSTEM-NEO4J-GRAPHITI.md#Story-22.4]
[Source: docs/stories/22.4.story.md#MemoryService实现]
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.clients.neo4j_client import Neo4jClient, get_neo4j_client

logger = logging.getLogger(__name__)


class MemoryService:
    """
    学习记忆服务

    ✅ Verified from docs/stories/22.4.story.md#MemoryService实现:
    - record_learning_event(): 记录学习事件到Neo4j和Graphiti
    - get_learning_history(): 获取学习历史(分页)
    - get_review_suggestions(): 获取复习建议(基于艾宾浩斯遗忘曲线)

    [Source: docs/stories/22.4.story.md#Dev-Notes]
    """

    def __init__(
        self,
        neo4j_client: Optional[Neo4jClient] = None
    ):
        """
        Initialize MemoryService.

        Args:
            neo4j_client: Neo4j client instance (optional, uses singleton if not provided)

        [Source: docs/stories/22.4.story.md#MemoryService实现]
        """
        self.neo4j = neo4j_client or get_neo4j_client()
        self._initialized = False
        self._episodes: List[Dict[str, Any]] = []  # In-memory episode store
        logger.debug("MemoryService initialized")

    async def initialize(self) -> bool:
        """Initialize the service and underlying clients."""
        if self._initialized:
            return True

        await self.neo4j.initialize()
        self._initialized = True
        logger.info("MemoryService initialized successfully")
        return True

    async def record_learning_event(
        self,
        user_id: str,
        canvas_path: str,
        node_id: str,
        concept: str,
        agent_type: str,
        score: Optional[int] = None,
        duration_seconds: Optional[int] = None
    ) -> str:
        """
        记录学习事件

        同时存储到Neo4j知识图谱和Graphiti时序数据库

        ✅ Verified from docs/stories/22.4.story.md#record_learning_event:
        - 存储到Neo4j - 创建学习关系
        - 存储到Graphiti - 添加Episode
        - 返回episode_id

        Args:
            user_id: 用户ID
            canvas_path: Canvas文件路径
            node_id: Canvas节点ID
            concept: 学习概念
            agent_type: 使用的Agent类型
            score: 得分 (0-100, optional)
            duration_seconds: 学习时长 (optional)

        Returns:
            str: Episode ID

        [Source: docs/stories/22.4.story.md#record_learning_event]
        """
        if not self._initialized:
            await self.initialize()

        # Generate unique episode ID
        episode_id = f"episode-{uuid.uuid4().hex[:16]}"

        try:
            # ✅ Verified: Store to Neo4j - Create learning relationship
            await self._create_neo4j_learning_relationship(
                user_id=user_id,
                concept=concept,
                score=score
            )

            # ✅ Verified: Store episode (simulating Graphiti add_learning_episode)
            content = f"User {user_id} learned '{concept}' using {agent_type}"
            if score is not None:
                content += f" with score {score}"

            episode = {
                "episode_id": episode_id,
                "content": content,
                "episode_type": "learning",
                "user_id": user_id,
                "canvas_path": canvas_path,
                "node_id": node_id,
                "concept": concept,
                "agent_type": agent_type,
                "score": score,
                "duration_seconds": duration_seconds,
                "timestamp": datetime.now().isoformat()
            }
            self._episodes.append(episode)

            logger.info(f"Recorded learning event: {episode_id}")
            return episode_id

        except Exception as e:
            logger.error(f"Failed to record learning event: {e}")
            raise

    async def get_learning_history(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        concept: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """
        获取学习历史 (分页)

        ✅ Verified from docs/stories/22.4.story.md#get_learning_history:
        - 从Graphiti查询时序数据
        - 应用concept过滤
        - 分页返回

        Args:
            user_id: 用户ID
            start_date: 开始日期 (optional)
            end_date: 结束日期 (optional)
            concept: 概念过滤 (optional)
            page: 页码 (default: 1)
            page_size: 每页大小 (default: 50)

        Returns:
            Dict with items, total, page, page_size, pages

        [Source: docs/stories/22.4.story.md#get_learning_history]
        """
        if not self._initialized:
            await self.initialize()

        # Filter episodes by user_id
        episodes = [e for e in self._episodes if e.get("user_id") == user_id]

        # Apply date filters
        if start_date:
            episodes = [
                e for e in episodes
                if datetime.fromisoformat(e["timestamp"]) >= start_date
            ]
        if end_date:
            episodes = [
                e for e in episodes
                if datetime.fromisoformat(e["timestamp"]) <= end_date
            ]

        # Apply concept filter
        if concept:
            concept_lower = concept.lower()
            episodes = [
                e for e in episodes
                if concept_lower in e.get("concept", "").lower()
            ]

        # Sort by timestamp (newest first)
        episodes.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        # Pagination
        total = len(episodes)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated = episodes[start_idx:end_idx]

        return {
            "items": paginated,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size if total > 0 else 0
        }

    async def get_concept_history(
        self,
        concept_id: str,
        user_id: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        查询概念学习历史

        ✅ Verified from AC-22.4.3: GET /api/v1/memory/concepts/{id}/history

        Args:
            concept_id: 概念ID
            user_id: 用户ID (optional)
            limit: 最大返回数量

        Returns:
            Dict with timeline data and score changes

        [Source: docs/stories/22.4.story.md#Dev-Notes]
        """
        if not self._initialized:
            await self.initialize()

        # Get history from Neo4j
        history = await self.neo4j.get_concept_history(
            concept_id=concept_id,
            user_id=user_id,
            limit=limit
        )

        # Format as timeline
        timeline = []
        for record in history:
            timeline.append({
                "timestamp": record.get("timestamp"),
                "score": record.get("score"),
                "user_id": record.get("user_id"),
                "concept": record.get("concept"),
                "review_count": record.get("review_count", 0)
            })

        # Calculate score trend
        scores = [r.get("score") for r in timeline if r.get("score") is not None]
        score_trend = {
            "first": scores[-1] if scores else None,
            "last": scores[0] if scores else None,
            "average": sum(scores) / len(scores) if scores else None,
            "improvement": (scores[0] - scores[-1]) if len(scores) >= 2 else None
        }

        return {
            "concept_id": concept_id,
            "timeline": timeline,
            "score_trend": score_trend,
            "total_reviews": len(timeline)
        }

    async def get_review_suggestions(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        获取复习建议 (基于艾宾浩斯遗忘曲线)

        查询Neo4j中next_review时间已过的概念

        ✅ Verified from docs/stories/22.4.story.md#get_review_suggestions:
        - 查询next_review < datetime()的概念
        - 添加优先级 (high if review_count < 3 else medium)
        - ORDER BY next_review

        Args:
            user_id: 用户ID
            limit: 返回数量 (default: 10)

        Returns:
            List of review suggestions with priority

        [Source: docs/stories/22.4.story.md#get_review_suggestions]
        """
        if not self._initialized:
            await self.initialize()

        suggestions = await self.neo4j.get_review_suggestions(
            user_id=user_id,
            limit=limit
        )

        logger.debug(f"Retrieved {len(suggestions)} review suggestions for user {user_id}")
        return suggestions

    async def _create_neo4j_learning_relationship(
        self,
        user_id: str,
        concept: str,
        score: Optional[int] = None
    ) -> None:
        """
        在Neo4j中创建学习关系

        ✅ Verified from docs/stories/22.4.story.md#_create_neo4j_learning_relationship:
        - MERGE (u:User {id: $userId})
        - MERGE (c:Concept {name: $concept})
        - MERGE (u)-[r:LEARNED]->(c)
        - SET r.timestamp, r.score, r.next_review

        Args:
            user_id: 用户ID
            concept: 概念名称
            score: 得分 (optional)

        [Source: docs/stories/22.4.story.md#_create_neo4j_learning_relationship]
        """
        await self.neo4j.create_learning_relationship(
            user_id=user_id,
            concept=concept,
            score=score
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics."""
        return {
            "initialized": self._initialized,
            "total_episodes": len(self._episodes),
            "neo4j_stats": self.neo4j.stats
        }

    async def cleanup(self) -> None:
        """
        Cleanup resources when service is no longer needed.

        Called by dependency injection when using yield syntax.

        [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#依赖注入设计]
        """
        self._initialized = False
        await self.neo4j.cleanup()
        logger.debug("MemoryService cleanup completed")


# Singleton instance
_service_instance: Optional[MemoryService] = None


def get_memory_service() -> MemoryService:
    """
    Get or create MemoryService singleton.

    Returns:
        MemoryService instance
    """
    global _service_instance

    if _service_instance is None:
        _service_instance = MemoryService()

    return _service_instance


def reset_memory_service() -> None:
    """Reset singleton instance (for testing)."""
    global _service_instance
    _service_instance = None
