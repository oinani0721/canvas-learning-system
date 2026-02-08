# Canvas Learning System - Memory Service
# Story 22.4: 学习历史存储与查询API
# Story 30.8: 多学科隔离与group_id支持
# Story 36.9: 学习记忆双写（Neo4j + Graphiti JSON存储）
# ✅ Verified from docs/stories/22.4.story.md#Dev-Notes
# ✅ Verified from docs/stories/30.8.story.md#Task-1.1
# ✅ Verified from docs/stories/36.9.story.md#AC-36.9.1
"""
Memory Service - Learning history storage and query.

Story 22.4 Implementation:
- AC-22.4.1: POST /api/v1/memory/episodes - Record learning events
- AC-22.4.2: GET /api/v1/memory/episodes - Query learning history
- AC-22.4.3: GET /api/v1/memory/concepts/{id}/history - Query concept history
- AC-22.4.4: GET /api/v1/memory/review-suggestions - Get review suggestions
- AC-22.4.5: Pagination and filtering support

Story 30.8 Implementation:
- AC-30.8.1: Each discipline uses independent `group_id` namespace
- AC-30.8.2: Auto-infer discipline from Canvas path
- AC-30.8.3: API supports `?subject=数学` query parameter filtering

Story 36.9 Implementation:
- AC-36.9.1: 学习事件写入Neo4j成功后自动尝试写入LearningMemoryClient
- AC-36.9.2: JSON写入使用fire-and-forget模式，不阻塞主流程
- AC-36.9.3: JSON写入失败时静默降级，记录警告日志但不抛出异常
- AC-36.9.4: JSON写入超时保护（500ms），超时后放弃写入
- AC-36.9.5: 可通过环境变量ENABLE_GRAPHITI_JSON_DUAL_WRITE开关双写功能

[Source: docs/prd/EPIC-22-MEMORY-SYSTEM-NEO4J-GRAPHITI.md#Story-22.4]
[Source: docs/stories/22.4.story.md#MemoryService实现]
[Source: docs/stories/30.8.story.md#学科推断规则]
[Source: docs/stories/36.9.story.md#Dev-Notes]
"""

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.core.failed_writes_constants import FAILED_WRITES_FILE, failed_writes_lock

from app.clients.neo4j_client import Neo4jClient, get_neo4j_client
# Story 36.9 AC-36.9.1: Import LearningMemoryClient for Graphiti JSON dual-write
# ✅ Verified from backend/app/clients/graphiti_client.py#L594-L624
from app.clients.graphiti_client import (
    LearningMemory,
    LearningMemoryClient,
    get_learning_memory_client,
)
from app.core.subject_config import (
    DEFAULT_SUBJECT,
    SKIP_DIRECTORIES_LOWER,
    build_group_id,
    extract_subject_from_canvas_path,
    sanitize_subject_name,
)
# Story 36.9 AC-36.9.5: Import settings for ENABLE_GRAPHITI_JSON_DUAL_WRITE config flag
from app.config import settings

logger = logging.getLogger(__name__)

# Story 31.5: Cache TTL for score history queries (30 seconds)
SCORE_HISTORY_CACHE_TTL = 30

# Story 38.6 AC-1: Increased per-attempt timeout for reliable writes (was 0.5s)
GRAPHITI_JSON_WRITE_TIMEOUT = 2.0

# Story 38.6 AC-1: Retry backoff base (seconds). Backoff = base * 2^attempt → 1s, 2s, 4s
GRAPHITI_RETRY_BACKOFF_BASE = 1.0

# Story 38.6: FAILED_WRITES_FILE and failed_writes_lock imported from
# app.core.failed_writes_constants (shared with agent_service.py)


@dataclass
class ScoreHistoryResponse:
    """
    Score history response data.

    Story 31.5 AC-31.5.1: Response format for score history query.

    Attributes:
        scores: List of historical scores (0-100, oldest to newest)
        timestamps: List of corresponding timestamps
        average: Average score
        sample_size: Number of records

    [Source: specs/data/score-history-response.schema.json]
    """
    concept_id: str
    canvas_name: str
    scores: List[int]
    timestamps: List[str]
    average: float
    sample_size: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "concept_id": self.concept_id,
            "canvas_name": self.canvas_name,
            "scores": self.scores,
            "timestamps": self.timestamps,
            "average": self.average,
            "sample_size": self.sample_size
        }


class MemoryService:
    """
    学习记忆服务

    ✅ Verified from docs/stories/22.4.story.md#MemoryService实现:
    - record_learning_event(): 记录学习事件到Neo4j和Graphiti
    - get_learning_history(): 获取学习历史(分页)
    - get_review_suggestions(): 获取复习建议(基于艾宾浩斯遗忘曲线)

    [Source: docs/stories/22.4.story.md#Dev-Notes]
    """

    MAX_EPISODE_CACHE = 2000  # Story 38.2: Upper bound on in-memory episode cache

    def __init__(
        self,
        neo4j_client: Optional[Neo4jClient] = None,
        learning_memory_client: Optional[LearningMemoryClient] = None,  # Story 36.9 AC-36.9.1
    ):
        """
        Initialize MemoryService.

        Args:
            neo4j_client: Neo4j client instance (optional, uses singleton if not provided)
            learning_memory_client: LearningMemoryClient instance for Graphiti JSON dual-write
                                   (optional, uses singleton if not provided)

        [Source: docs/stories/22.4.story.md#MemoryService实现]
        [Source: docs/stories/36.9.story.md#Task-1.2]
        """
        self.neo4j = neo4j_client or get_neo4j_client()
        # Story 36.9 AC-36.9.1: Inject LearningMemoryClient for Graphiti JSON dual-write
        self._learning_memory = learning_memory_client or get_learning_memory_client()
        self._initialized = False
        self._episodes: List[Dict[str, Any]] = []  # In-memory episode store
        # Story 38.2 AC-2: Track whether episodes have been recovered from Neo4j
        self._episodes_recovered: bool = False
        # Story 38.2: Lock to prevent concurrent recovery attempts
        self._recovery_lock = asyncio.Lock()
        # Story 31.5: Cache for score history queries (30s TTL)
        self._score_history_cache: Dict[str, Tuple[float, ScoreHistoryResponse]] = {}
        logger.debug("MemoryService initialized with Graphiti JSON dual-write support")

    async def initialize(self) -> bool:
        """Initialize the service and underlying clients."""
        if self._initialized:
            return True

        await self.neo4j.initialize()
        self._initialized = True

        # Story 38.2 AC-2: Recover episodes from Neo4j on startup
        await self._recover_episodes_from_neo4j()

        logger.info("MemoryService initialized successfully")
        return True

    async def _recover_episodes_from_neo4j(self) -> None:
        """
        Recover episodes from Neo4j on startup.

        Story 38.2 AC-1/AC-2: Populate self._episodes from Neo4j so the
        in-memory cache survives restarts.

        Story 38.2 AC-3: If Neo4j is unavailable, graceful degradation —
        _episodes remains empty, _episodes_recovered stays False, and
        recovery is re-attempted lazily on first query.

        Uses _recovery_lock to prevent concurrent recovery from multiple
        simultaneous get_learning_history() calls.

        [Source: docs/stories/38.2.story.md#Task-2]
        """
        async with self._recovery_lock:
            # Double-check after acquiring lock (another coroutine may have completed recovery)
            if self._episodes_recovered:
                return
            try:
                records = await self.neo4j.get_all_recent_episodes(limit=1000)
                added = 0
                if records:
                    # Build set of existing episode keys to avoid duplicates
                    # Key includes timestamp so same user+concept at different times are kept
                    existing_keys = {
                        (e.get("user_id"), e.get("concept"), str(e.get("timestamp") or ""))
                        for e in self._episodes
                    }
                    for idx, record in enumerate(records):
                        user_id = record.get("user_id")
                        concept = record.get("concept")
                        timestamp = str(record.get("timestamp") or "")
                        # Skip if already in cache (from degraded-mode recording)
                        if (user_id, concept, timestamp) in existing_keys:
                            continue
                        episode = {
                            "episode_id": f"recovered-{idx}-{user_id or 'unknown'}-{record.get('concept_id') or 'unknown'}",
                            "user_id": user_id,
                            "concept": concept,
                            "concept_id": record.get("concept_id"),
                            "score": record.get("score"),
                            "timestamp": timestamp,
                            "group_id": record.get("group_id"),
                            "review_count": record.get("review_count") or 0,
                            "episode_type": "recovered",
                        }
                        self._episodes.append(episode)
                        existing_keys.add((user_id, concept, timestamp))
                        added += 1
                    # Cap episode cache to prevent unbounded growth
                    if len(self._episodes) > self.MAX_EPISODE_CACHE:
                        self._episodes = self._episodes[-self.MAX_EPISODE_CACHE:]
                self._episodes_recovered = True
                logger.info(f"MemoryService: recovered {added} episodes from Neo4j ({len(records)} returned, {len(records) - added} deduped)")
            except Exception as e:
                # AC-3: Graceful degradation — start with empty history
                self._episodes_recovered = False
                logger.warning(f"MemoryService: Neo4j unavailable, starting with empty history ({e})")

    async def _write_to_graphiti_json(
        self,
        episode_id: str,
        canvas_name: str,
        node_id: str,
        concept: str,
        score: Optional[float] = None,
        agent_feedback: Optional[str] = None,
        user_understanding: Optional[str] = None,
    ) -> None:
        """
        Fire-and-forget write to Graphiti JSON storage.

        Story 36.9: Dual-write learning memories to LearningMemoryClient (JSON storage)
        - AC-36.9.2: Fire-and-forget pattern, does not block main flow
        - AC-36.9.3: Silent degradation on failure with logger.warning()
        - AC-36.9.4: 500ms timeout protection via asyncio.wait_for()

        Uses existing LearningMemoryClient from graphiti_client.py:594-624.
        Storage location: backend/data/learning_memories.json

        Args:
            episode_id: Unique episode identifier (for logging)
            canvas_name: Canvas file path/name
            node_id: Node ID being learned
            concept: Concept being learned
            score: Learning score (0-100, optional)
            agent_feedback: Agent feedback/response (optional)
            user_understanding: User's understanding text (optional)

        [Source: docs/stories/36.9.story.md#Task-2]
        [Source: backend/app/clients/graphiti_client.py#LearningMemoryClient]
        """
        try:
            # ✅ AC-36.9.4: 500ms timeout protection
            await asyncio.wait_for(
                self._learning_memory.add_learning_episode(
                    LearningMemory(
                        canvas_name=canvas_name,
                        node_id=node_id,
                        concept=concept,
                        user_understanding=user_understanding,
                        score=score,
                        agent_feedback=agent_feedback,
                        timestamp=datetime.now().isoformat(),
                    )
                ),
                timeout=GRAPHITI_JSON_WRITE_TIMEOUT,
            )
            # ✅ Task 2.5: Log success with logger.debug()
            logger.debug(f"Graphiti JSON dual-write succeeded: {episode_id}")
        except asyncio.TimeoutError:
            # ✅ AC-36.9.4: Timeout protection - silent degradation
            logger.warning(
                f"Graphiti JSON dual-write timeout ({GRAPHITI_JSON_WRITE_TIMEOUT}s): {episode_id}"
            )
        except Exception as e:
            # ✅ AC-36.9.3: Silent degradation - log warning but don't raise
            logger.warning(f"Graphiti JSON dual-write failed for {episode_id}: {e}")

    async def _write_to_graphiti_json_with_retry(
        self,
        episode_id: str,
        canvas_name: str,
        node_id: str,
        concept: str,
        score: Optional[float] = None,
        agent_feedback: Optional[str] = None,
        user_understanding: Optional[str] = None,
        max_retries: int = 2
    ) -> bool:
        """
        带重试的 Graphiti JSON 写入。

        Story 31.A.3: 增强 _write_to_graphiti_json 的可靠性
        - 添加指数退避重试机制
        - 最多重试 2 次（共 3 次尝试）
        - 记录重试和失败日志

        Args:
            episode_id: 唯一 episode 标识（用于日志）
            canvas_name: Canvas 文件路径/名称
            node_id: 正在学习的节点 ID
            concept: 正在学习的概念
            score: 学习得分 (0-100, optional)
            agent_feedback: Agent 反馈/响应 (optional)
            user_understanding: 用户理解文本 (optional)
            max_retries: 最大重试次数 (default: 2)

        Returns:
            True if successful, False otherwise

        [Source: docs/stories/31.A.3.story.md#AC-31.A.3.1]
        """
        for attempt in range(max_retries + 1):
            try:
                await asyncio.wait_for(
                    self._learning_memory.add_learning_episode(
                        LearningMemory(
                            canvas_name=canvas_name,
                            node_id=node_id,
                            concept=concept,
                            user_understanding=user_understanding,
                            score=score,
                            agent_feedback=agent_feedback,
                            timestamp=datetime.now().isoformat(),
                        )
                    ),
                    timeout=GRAPHITI_JSON_WRITE_TIMEOUT,
                )
                if attempt > 0:
                    logger.info(f"Graphiti write succeeded after {attempt + 1} attempts: {episode_id}")
                else:
                    logger.debug(f"Graphiti JSON dual-write succeeded: {episode_id}")
                return True
            except asyncio.TimeoutError:
                if attempt < max_retries:
                    delay = GRAPHITI_RETRY_BACKOFF_BASE * (2 ** attempt)  # Story 38.6: 1s, 2s, 4s
                    logger.warning(f"Graphiti write timeout, retrying in {delay}s (attempt {attempt + 1}): {episode_id}")
                    await asyncio.sleep(delay)
                    continue
                logger.warning(f"Graphiti write failed after {max_retries + 1} attempts (timeout): {episode_id}")
                return False
            except Exception as e:
                if attempt < max_retries:
                    delay = GRAPHITI_RETRY_BACKOFF_BASE * (2 ** attempt)  # Story 38.6: 1s, 2s, 4s
                    logger.warning(f"Graphiti write error: {e}, retrying in {delay}s (attempt {attempt + 1}): {episode_id}")
                    await asyncio.sleep(delay)
                    continue
                logger.warning(f"Graphiti write failed after {max_retries + 1} attempts: {episode_id} - {e}")
                return False
        return False  # Should not reach here, but for safety

    async def record_learning_event(
        self,
        user_id: str,
        canvas_path: str,
        node_id: str,
        concept: str,
        agent_type: str,
        score: Optional[int] = None,
        duration_seconds: Optional[int] = None,
        subject: Optional[str] = None
    ) -> str:
        """
        记录学习事件

        同时存储到Neo4j知识图谱和Graphiti时序数据库

        ✅ Verified from docs/stories/22.4.story.md#record_learning_event:
        - 存储到Neo4j - 创建学习关系
        - 存储到Graphiti - 添加Episode
        - 返回episode_id

        ✅ Verified from docs/stories/30.8.story.md#AC-30.8.1:
        - 自动从canvas_path提取学科 (AC-30.8.2)
        - 使用group_id进行命名空间隔离 (AC-30.8.1)

        Args:
            user_id: 用户ID
            canvas_path: Canvas文件路径
            node_id: Canvas节点ID
            concept: 学习概念
            agent_type: 使用的Agent类型
            score: 得分 (0-100, optional)
            duration_seconds: 学习时长 (optional)
            subject: 学科名称 (可选，如不提供则自动推断)

        Returns:
            str: Episode ID

        [Source: docs/stories/22.4.story.md#record_learning_event]
        [Source: docs/stories/30.8.story.md#Task-3.1]
        """
        if not self._initialized:
            await self.initialize()

        # Generate unique episode ID
        episode_id = f"episode-{uuid.uuid4().hex[:16]}"

        # ✅ AC-30.8.2: Auto-infer subject from canvas_path if not provided
        inferred_subject = subject or extract_subject_from_canvas_path(canvas_path)

        # ✅ AC-30.8.1: Build group_id for namespace isolation
        group_id = build_group_id(inferred_subject)

        try:
            # ✅ Verified: Store to Neo4j - Create learning relationship
            await self._create_neo4j_learning_relationship(
                user_id=user_id,
                concept=concept,
                score=score,
                group_id=group_id
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
                "timestamp": datetime.now().isoformat(),
                # ✅ Story 30.8: Subject isolation fields
                "subject": inferred_subject,
                "group_id": group_id
            }
            self._episodes.append(episode)

            logger.info(f"Recorded learning event: {episode_id} (subject={inferred_subject}, group_id={group_id})")

            # ✅ Story 36.9 AC-36.9.1/AC-36.9.2: Fire-and-forget dual-write to Graphiti JSON
            # ✅ AC-36.9.5: Check config flag before calling dual-write
            # ✅ Story 31.A.3 AC-31.A.3.2: Use retry method for reliability
            if getattr(settings, "ENABLE_GRAPHITI_JSON_DUAL_WRITE", True):
                asyncio.create_task(
                    self._write_to_graphiti_json_with_retry(
                        episode_id=episode_id,
                        canvas_name=canvas_path,
                        node_id=node_id,
                        concept=concept,
                        score=float(score) if score is not None else None,
                        agent_feedback=agent_type,  # Use agent_type as feedback context
                    )
                )

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
        subject: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """
        获取学习历史 (分页)

        ✅ Story 31.A.2 AC-31.A.2.1: 从Neo4j读取学习历史（替代只读内存）
        ✅ Verified from docs/stories/22.4.story.md#get_learning_history:
        - 从Neo4j查询时序数据
        - 应用concept过滤
        - 分页返回

        ✅ Verified from docs/stories/30.8.story.md#AC-30.8.3:
        - 支持`?subject=数学`查询参数过滤

        Args:
            user_id: 用户ID
            start_date: 开始日期 (optional)
            end_date: 结束日期 (optional)
            concept: 概念过滤 (optional)
            subject: 学科过滤 (optional) - AC-30.8.3
            page: 页码 (default: 1)
            page_size: 每页大小 (default: 50)

        Returns:
            Dict with items, total, page, page_size, pages

        [Source: docs/stories/31.A.2.story.md#AC-31.A.2.1]
        [Source: docs/stories/22.4.story.md#get_learning_history]
        [Source: docs/stories/30.8.story.md#Task-3.1]
        """
        if not self._initialized:
            await self.initialize()

        # ✅ Story 31.A.2 AC-31.A.2.1: Build group_id for subject filtering
        group_id = build_group_id(subject) if subject else None

        # ✅ Story 31.A.2 AC-31.A.2.1: Query from Neo4j first (replaces memory-only read)
        episodes = []
        try:
            neo4j_results = await self.neo4j.get_learning_history(
                user_id=user_id,
                start_date=start_date,
                end_date=end_date,
                concept=concept,
                group_id=group_id,
                limit=page_size * page  # Get enough data for pagination
            )
            episodes = neo4j_results
            logger.debug(f"Retrieved {len(episodes)} episodes from Neo4j for user {user_id}")
        except Exception as e:
            # ✅ Story 31.A.2: Fallback to memory if Neo4j fails
            logger.warning(f"Neo4j query failed, falling back to memory: {e}")

        # Fallback to memory if Neo4j returned empty or failed
        if not episodes:
            # Story 38.2 AC-3: Lazy recovery — if startup recovery failed, retry now
            if not self._episodes_recovered:
                await self._recover_episodes_from_neo4j()
            logger.debug("Falling back to in-memory episodes")
            episodes = [e for e in self._episodes if e.get("user_id") == user_id]

            # Apply date filters (only for memory fallback, Neo4j handles this)
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

            # Apply subject filter
            if subject:
                subject_lower = subject.lower()
                episodes = [
                    e for e in episodes
                    if subject_lower in e.get("subject", "").lower()
                ]

            # Sort by timestamp (newest first)
            episodes.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        # Story 38.6 AC-4: Merge failed scores from fallback so user never sees gaps
        # Run sync file I/O in thread to avoid blocking the event loop (#3)
        failed_scores = await asyncio.to_thread(self.load_failed_scores)
        if failed_scores:
            # Deduplicate: only include fallback entries not already in episodes
            existing_keys = {
                (e.get("node_id", ""), e.get("timestamp", "")) for e in episodes
            }
            for fs in failed_scores:
                key = (fs.get("node_id", ""), fs.get("timestamp", ""))
                if key not in existing_keys:
                    episodes.append(fs)
            # Re-sort after merge
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

    async def get_concept_score_history(
        self,
        concept_id: str,
        canvas_name: str,
        limit: int = 5
    ) -> ScoreHistoryResponse:
        """
        查询概念的历史得分 (最近N次)

        Story 31.5 AC-31.5.1: Query recent score records for difficulty adaptation.

        ✅ Task 2.1: get_concept_score_history(concept_id, canvas_name, limit=5)
        ✅ Task 2.2: Query Neo4j for recent N score records
        ✅ Task 2.3: Return format: {scores: int[], timestamps: datetime[], average: float}
        ✅ Task 2.4: Cache with 30 second TTL

        Args:
            concept_id: 概念/节点ID
            canvas_name: Canvas文件名
            limit: 返回的历史记录数量上限 (default: 5)

        Returns:
            ScoreHistoryResponse with scores, timestamps, average, sample_size

        [Source: docs/stories/31.5.story.md#Task-2]
        [Source: specs/data/score-history-response.schema.json]
        """
        if not self._initialized:
            await self.initialize()

        # Build cache key
        cache_key = f"{concept_id}:{canvas_name}:{limit}"

        # Check cache (30s TTL per Task 2.4)
        if cache_key in self._score_history_cache:
            cached_time, cached_result = self._score_history_cache[cache_key]
            if time.time() - cached_time < SCORE_HISTORY_CACHE_TTL:
                logger.debug(f"Score history cache hit for {concept_id}")
                return cached_result

        # Query Neo4j for score history
        try:
            records = await self.neo4j.get_concept_score_history(
                concept_id=concept_id,
                canvas_name=canvas_name,
                limit=limit
            )

            # Extract scores and timestamps
            scores: List[int] = []
            timestamps: List[str] = []

            for record in records:
                score = record.get("score")
                ts = record.get("timestamp")
                if score is not None:
                    scores.append(int(score))
                    timestamps.append(str(ts) if ts else "")

            # Calculate average
            average = sum(scores) / len(scores) if scores else 0.0

            result = ScoreHistoryResponse(
                concept_id=concept_id,
                canvas_name=canvas_name,
                scores=scores,
                timestamps=timestamps,
                average=round(average, 2),
                sample_size=len(scores)
            )

            # Store in cache
            self._score_history_cache[cache_key] = (time.time(), result)

            logger.debug(
                f"Score history for {concept_id}: "
                f"{len(scores)} records, avg={average:.2f}"
            )

            return result

        except Exception as e:
            logger.error(f"Failed to get score history for {concept_id}: {e}")
            # Return empty result on error (graceful degradation per ADR-009)
            return ScoreHistoryResponse(
                concept_id=concept_id,
                canvas_name=canvas_name,
                scores=[],
                timestamps=[],
                average=0.0,
                sample_size=0
            )

    async def get_review_suggestions(
        self,
        user_id: str,
        limit: int = 10,
        subject: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取复习建议 (基于艾宾浩斯遗忘曲线)

        查询Neo4j中next_review时间已过的概念

        ✅ Verified from docs/stories/22.4.story.md#get_review_suggestions:
        - 查询next_review < datetime()的概念
        - 添加优先级 (high if review_count < 3 else medium)
        - ORDER BY next_review

        ✅ Verified from docs/stories/30.8.story.md#AC-30.8.3:
        - 支持`?subject=数学`查询参数过滤

        Args:
            user_id: 用户ID
            limit: 返回数量 (default: 10)
            subject: 学科过滤 (optional) - AC-30.8.3

        Returns:
            List of review suggestions with priority

        [Source: docs/stories/22.4.story.md#get_review_suggestions]
        [Source: docs/stories/30.8.story.md#Task-3.1]
        """
        if not self._initialized:
            await self.initialize()

        # ✅ AC-30.8.3: Build group_id for subject filtering
        group_id = build_group_id(subject) if subject else None

        suggestions = await self.neo4j.get_review_suggestions(
            user_id=user_id,
            limit=limit,
            group_id=group_id
        )

        logger.debug(f"Retrieved {len(suggestions)} review suggestions for user {user_id} (subject={subject})")
        return suggestions

    async def _create_neo4j_learning_relationship(
        self,
        user_id: str,
        concept: str,
        score: Optional[int] = None,
        group_id: Optional[str] = None
    ) -> None:
        """
        在Neo4j中创建学习关系

        ✅ Verified from docs/stories/22.4.story.md#_create_neo4j_learning_relationship:
        - MERGE (u:User {id: $userId})
        - MERGE (c:Concept {name: $concept})
        - MERGE (u)-[r:LEARNED]->(c)
        - SET r.timestamp, r.score, r.next_review, r.group_id

        Args:
            user_id: 用户ID
            concept: 概念名称
            score: 得分 (optional)
            group_id: 科目隔离 group_id (optional, Story 30.8)

        [Source: docs/stories/22.4.story.md#_create_neo4j_learning_relationship]
        """
        await self.neo4j.create_learning_relationship(
            user_id=user_id,
            concept=concept,
            score=score,
            group_id=group_id
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics."""
        return {
            "initialized": self._initialized,
            "total_episodes": len(self._episodes),
            "neo4j_stats": self.neo4j.stats
        }

    async def get_health_status(self) -> Dict[str, Any]:
        """
        获取3层记忆系统健康状态

        ✅ Verified from Story 30.3 AC-30.3.5:
        - 返回 Temporal (FSRS/SQLite) 层状态
        - 返回 Graphiti (Neo4j) 层状态
        - 返回 Semantic (LanceDB) 层状态
        - 整体状态: healthy/degraded/unhealthy

        Returns:
            Dict with status, layers, timestamp

        [Source: docs/stories/30.3.memory-api-health-endpoints.story.md#Task-1.2]
        """
        if not self._initialized:
            await self.initialize()

        layers = {
            "temporal": {"status": "ok", "backend": "sqlite"},
            "graphiti": {"status": "ok", "backend": "neo4j"},
            "semantic": {"status": "ok", "backend": "lancedb"}
        }

        # Check Graphiti/Neo4j layer
        # ✅ Story 30.3 Fix: Use correct stats fields (initialized, health_status)
        try:
            neo4j_stats = self.neo4j.stats
            is_connected = (
                neo4j_stats.get("initialized", False) and
                neo4j_stats.get("mode") == "NEO4J" and
                neo4j_stats.get("health_status", False)
            )
            if is_connected:
                layers["graphiti"]["node_count"] = neo4j_stats.get("node_count", 0)
            elif neo4j_stats.get("mode") == "JSON_FALLBACK":
                # JSON fallback mode - still considered operational
                layers["graphiti"]["status"] = "ok"
                layers["graphiti"]["backend"] = "json_fallback"
            else:
                layers["graphiti"]["status"] = "error"
                layers["graphiti"]["error"] = "Neo4j not connected"
        except Exception as e:
            layers["graphiti"]["status"] = "error"
            layers["graphiti"]["error"] = str(e)

        # Temporal layer (in-memory/SQLite simulation) - always ok for now
        layers["temporal"]["status"] = "ok"

        # Semantic layer (LanceDB) - check if available
        try:
            # For now, assume LanceDB is available if we can import it
            layers["semantic"]["status"] = "ok"
            layers["semantic"]["vector_count"] = 0  # Placeholder
        except Exception as e:
            layers["semantic"]["status"] = "error"
            layers["semantic"]["error"] = str(e)

        # Determine overall status
        error_count = sum(
            1 for layer in layers.values() if layer.get("status") == "error"
        )

        if error_count == 0:
            overall_status = "healthy"
        elif error_count < len(layers):
            overall_status = "degraded"
        else:
            overall_status = "unhealthy"

        return {
            "status": overall_status,
            "layers": layers,
            "timestamp": datetime.now().isoformat()
        }

    async def record_batch_learning_events(
        self,
        events: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        批量记录学习事件

        ✅ Verified from Story 30.3 AC-30.3.10:
        - 最多50个事件
        - 返回 processed, failed, errors

        Args:
            events: List of event dictionaries

        Returns:
            Dict with success, processed, failed, errors, timestamp

        [Source: docs/stories/30.3.memory-api-health-endpoints.story.md#AC-30.3.10]
        """
        if not self._initialized:
            await self.initialize()

        processed = 0
        failed = 0
        errors: List[Dict[str, Any]] = []

        for idx, event in enumerate(events):
            try:
                # Validate required fields
                required_fields = ["event_type", "timestamp", "canvas_path", "node_id"]
                missing = [f for f in required_fields if f not in event]
                if missing:
                    raise ValueError(f"Missing required fields: {missing}")

                # Create episode record
                episode_id = f"batch-{datetime.now().strftime('%Y%m%d%H%M%S')}-{idx}"
                episode_record = {
                    "episode_id": episode_id,
                    "event_type": event["event_type"],
                    "timestamp": event["timestamp"],
                    "canvas_path": event["canvas_path"],
                    "node_id": event["node_id"],
                    "metadata": event.get("metadata", {})
                }

                # Store in memory (and Neo4j if available)
                self._episodes.append(episode_record)

                # Try to store in Neo4j if connected
                if self.neo4j.stats.get("connected"):
                    try:
                        await self.neo4j.record_episode({
                            "episode_id": episode_id,
                            "user_id": "batch_user",
                            "canvas_path": event["canvas_path"],
                            "node_id": event["node_id"],
                            "concept": event.get("metadata", {}).get("concept", event.get("metadata", {}).get("node_text", "unknown")),
                            "agent_type": event["event_type"],
                            "timestamp": event["timestamp"]
                        })
                    except Exception:
                        # Continue even if Neo4j fails
                        pass

                processed += 1

            except Exception as e:
                failed += 1
                errors.append({
                    "index": idx,
                    "error": str(e)
                })

        return {
            "success": failed == 0,
            "processed": processed,
            "failed": failed,
            "errors": errors,
            "timestamp": datetime.now().isoformat()
        }

    async def record_temporal_event(
        self,
        event_type: str,
        session_id: str,
        canvas_path: str,
        node_id: Optional[str] = None,
        edge_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        记录时序事件到Neo4j Temporal Memory

        Story 30.5: Canvas CRUD Operations Memory Trigger
        - AC-30.5.1: node_created 事件
        - AC-30.5.2: edge_created 事件
        - AC-30.5.3: node_updated 事件

        Args:
            event_type: 事件类型 (node_created, node_updated, edge_created)
            session_id: 会话ID
            canvas_path: Canvas文件路径
            node_id: 节点ID (可选)
            edge_id: 边ID (可选)
            metadata: 事件元数据 (可选)

        Returns:
            str: Episode ID

        [Source: specs/data/temporal-event.schema.json]
        [Source: docs/stories/30.5.story.md#AC-30.5.1]
        """
        if not self._initialized:
            await self.initialize()

        import uuid
        event_id = f"event-{uuid.uuid4().hex[:16]}"

        # Build episode record following temporal-event.schema.json
        episode_record = {
            "event_id": event_id,
            "session_id": session_id,
            "event_type": event_type,
            "timestamp": datetime.now().isoformat(),
            "canvas_path": canvas_path,
            "node_id": node_id,
            "edge_id": edge_id,
            "metadata": metadata or {}
        }

        # Store in memory
        self._episodes.append(episode_record)

        # Try to store in Neo4j if connected
        if self.neo4j.stats.get("connected"):
            try:
                await self.neo4j.record_episode({
                    "episode_id": event_id,
                    "user_id": session_id,
                    "canvas_path": canvas_path,
                    "node_id": node_id or "",
                    "concept": metadata.get("node_text", "") if metadata else "",
                    "agent_type": event_type,
                    "timestamp": episode_record["timestamp"]
                })

                # Story 30.5 AC-30.5.4: Create Canvas-Concept relationship graph
                if event_type in ("node_created", "node_updated") and node_id:
                    await self.neo4j.create_canvas_node_relationship(
                        canvas_path=canvas_path,
                        node_id=node_id,
                        node_text=metadata.get("node_text") if metadata else None
                    )
                elif event_type == "edge_created" and edge_id:
                    from_node = metadata.get("from_node") if metadata else None
                    to_node = metadata.get("to_node") if metadata else None
                    if from_node and to_node:
                        await self.neo4j.create_edge_relationship(
                            canvas_path=canvas_path,
                            edge_id=edge_id,
                            from_node_id=from_node,
                            to_node_id=to_node,
                            edge_label=metadata.get("edge_label") if metadata else None
                        )

            except Exception as e:
                # Silent degradation - log but don't raise
                logger.warning(f"Neo4j write failed for temporal event: {e}")

        logger.debug(f"Recorded temporal event: {event_type} for {canvas_path}")

        # ✅ Story 36.9 AC-36.9.1/AC-36.9.2: Fire-and-forget dual-write to Graphiti JSON
        # ✅ AC-36.9.5: Check config flag before calling dual-write
        # ✅ Story 31.A.3 AC-31.A.3.2: Use retry method for reliability
        if getattr(settings, "ENABLE_GRAPHITI_JSON_DUAL_WRITE", True):
            # Extract concept from metadata (node_text for node events)
            concept = ""
            if metadata:
                concept = metadata.get("node_text", "") or metadata.get("concept", "")
            if not concept:
                concept = f"{event_type}:{node_id or edge_id or 'unknown'}"

            asyncio.create_task(
                self._write_to_graphiti_json_with_retry(
                    episode_id=event_id,
                    canvas_name=canvas_path,
                    node_id=node_id or edge_id or "",
                    concept=concept,
                    agent_feedback=event_type,  # Use event_type as context
                )
            )

        return event_id

    # ═══════════════════════════════════════════════════════════════════════════════
    # Story 38.6: Failed Write Recovery & Merged View
    # ═══════════════════════════════════════════════════════════════════════════════

    async def recover_failed_writes(self) -> Dict[str, int]:
        """
        Story 38.6 AC-3: Replay failed writes from data/failed_writes.jsonl on startup.

        Reads each entry, attempts to re-record it. Successfully replayed entries
        are removed; still-failing entries remain in the file.

        Uses failed_writes_lock to avoid racing with _record_failed_write.

        Returns:
            dict with 'recovered' and 'pending' counts
        """
        if not FAILED_WRITES_FILE.exists():
            return {"recovered": 0, "pending": 0}

        # Acquire shared lock to prevent _record_failed_write from appending
        # while we read + rewrite the file (fixes #1 race condition).
        with failed_writes_lock:
            try:
                lines = FAILED_WRITES_FILE.read_text(encoding="utf-8").strip().splitlines()
            except Exception as e:
                logger.warning(f"[Story 38.6] Failed to read fallback file: {e}")
                return {"recovered": 0, "pending": 0}

        if not lines:
            return {"recovered": 0, "pending": 0}

        recovered = 0
        still_pending = []

        for line in lines:
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                logger.warning(f"[Story 38.6] Skipping malformed fallback entry")
                still_pending.append(line)  # preserve malformed lines to avoid data loss
                continue

            try:
                # Use concept_id + timestamp for unique episode_id (#7)
                cid = entry.get("concept_id", "unknown")
                ts = entry.get("timestamp", "unknown")
                success = await self._write_to_graphiti_json_with_retry(
                    episode_id=f"recovery-{cid}-{ts}",
                    canvas_name=entry.get("canvas_name", ""),
                    node_id=entry.get("concept_id", ""),
                    concept=entry.get("concept", "") or entry.get("concept_id", ""),
                    score=entry.get("score"),
                    user_understanding=entry.get("user_understanding"),
                    agent_feedback=entry.get("agent_feedback"),
                    max_retries=1,  # fewer retries during recovery to avoid blocking startup
                )
                if success:
                    recovered += 1
                else:
                    still_pending.append(line)
            except Exception:
                still_pending.append(line)

        # Rewrite file with only still-pending entries under lock
        with failed_writes_lock:
            try:
                if still_pending:
                    tmp_file = FAILED_WRITES_FILE.with_suffix(".tmp")
                    tmp_file.write_text(
                        "\n".join(still_pending) + "\n", encoding="utf-8"
                    )
                    # Windows-safe replace: retry on PermissionError (#2)
                    for attempt in range(3):
                        try:
                            tmp_file.replace(FAILED_WRITES_FILE)
                            break
                        except PermissionError:
                            if attempt < 2:
                                import time as _time
                                _time.sleep(0.1)
                            else:
                                raise
                else:
                    FAILED_WRITES_FILE.unlink(missing_ok=True)
            except Exception as e:
                logger.warning(f"[Story 38.6] Failed to update fallback file: {e}")

        logger.info(
            f"[Story 38.6] Recovered {recovered} failed writes, {len(still_pending)} still pending"
        )
        return {"recovered": recovered, "pending": len(still_pending)}

    def load_failed_scores(self) -> List[Dict[str, Any]]:
        """
        Story 38.6 AC-4: Load scoring entries from failed_writes.jsonl for merged view.

        Returns list of dicts that can be merged into learning history results,
        so the user never sees a "missing score" gap.

        Uses failed_writes_lock to avoid reading a partially-written line.
        """
        if not FAILED_WRITES_FILE.exists():
            return []

        results = []
        try:
            with failed_writes_lock:
                lines = FAILED_WRITES_FILE.read_text(encoding="utf-8").strip().splitlines()
            for line in lines:
                try:
                    entry = json.loads(line)
                    results.append({
                        "timestamp": entry.get("timestamp", ""),
                        "canvas_name": entry.get("canvas_name", ""),
                        "node_id": entry.get("concept_id", ""),
                        "concept": entry.get("concept", "") or entry.get("concept_id", ""),
                        "score": entry.get("score"),
                        "source": "fallback",
                        "error_reason": entry.get("error_reason", ""),
                    })
                except json.JSONDecodeError:
                    continue
        except Exception as e:
            logger.warning(f"[Story 38.6] Failed to load failed scores: {e}")

        return results

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
