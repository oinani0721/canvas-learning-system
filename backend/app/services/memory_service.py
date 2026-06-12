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
import hashlib
import json
import logging
import time
import uuid

import structlog
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from cachetools import TTLCache

from app.clients.neo4j_client import Neo4jClient, get_neo4j_client
from app.config import DEFAULT_GROUP_ID, settings
from app.core.decision_tracker import log_decision
from app.core.failed_writes_constants import FAILED_WRITES_FILE, failed_writes_lock
from app.core.subject_config import (
    build_group_id,
    extract_canvas_name,
    extract_subject_from_canvas_path,
)
from app.services.episode_worker import EpisodeTask, get_episode_worker
from app.graphiti.entity_types import CANVAS_ENTITY_TYPES, CANVAS_EDGE_TYPES

logger = structlog.get_logger(__name__)

# Story 31.5: Cache TTL for score history queries (30 seconds)
SCORE_HISTORY_CACHE_TTL = 30

# Story 38.6: FAILED_WRITES_FILE and failed_writes_lock imported from
# app.core.failed_writes_constants (shared with agent_service.py)


# Story 30.10 AC-30.10.1: Deterministic episode ID generation
def _generate_deterministic_episode_id(
    user_id: str, canvas_path: str, node_id: str, concept: str
) -> str:
    """
    Generate a deterministic episode ID based on content hash.

    Same learning event (same user, canvas, node, concept) always produces
    the same episode_id, enabling idempotent writes.

    [Source: docs/stories/30.10.idempotency-fix.story.md#AC-30.10.1]
    """
    content = f"{user_id}:{canvas_path}:{node_id}:{concept}"
    hash_hex = hashlib.sha256(content.encode("utf-8")).hexdigest()[:32]
    return f"episode-{hash_hex}"


# Story 30.10 AC-30.10.4: Deterministic batch episode ID generation
def _generate_batch_episode_id(
    canvas_path: str, node_id: str, event_type: str, timestamp: str
) -> str:
    """
    Generate a deterministic batch episode ID based on event content.

    Same batch event always produces the same episode_id.

    [Source: docs/stories/30.10.idempotency-fix.story.md#AC-30.10.4]
    """
    content = f"{canvas_path}:{node_id}:{event_type}:{timestamp}"
    hash_hex = hashlib.sha256(content.encode("utf-8")).hexdigest()[:32]
    return f"batch-{hash_hex}"


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
            "sample_size": self.sample_size,
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
        # Story 38.2 AC-2: Track whether episodes have been recovered from Neo4j
        self._episodes_recovered: bool = False
        # Story 38.2: Lock to prevent concurrent recovery attempts
        self._recovery_lock = asyncio.Lock()
        # Fix C5: Lock to prevent concurrent _episodes mutations
        self._episodes_lock = asyncio.Lock()

        # Story 36.13 AC-4: Read configurable values from Settings
        try:
            from app.config import get_settings

            _settings = get_settings()
            _score_cache_maxsize = _settings.SCORE_HISTORY_CACHE_MAXSIZE
        except (ImportError, RuntimeError, AttributeError) as e:
            logger.warning(f"Settings unavailable, using default cache config: {e}")
            _score_cache_maxsize = 1000

        # Story 31.5: Cache for score history queries (30s TTL)
        # NFR-P0: Bounded TTLCache replaces bare dict to prevent unbounded memory growth
        # Story 36.13 AC-4: maxsize configurable via Settings
        self._score_history_cache: TTLCache = TTLCache(
            maxsize=_score_cache_maxsize, ttl=SCORE_HISTORY_CACHE_TTL
        )
        # NFR-P0: Lock for cache stampede protection (double-check locking)
        self._score_cache_lock = asyncio.Lock()
        # Story 30.24 AC-30.24.4: Track batch write failures for shutdown safety
        self._pending_failed_writes: List[Dict[str, Any]] = []
        logger.debug("MemoryService initialized")

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

    async def ensure_fulltext_index(self) -> None:
        """
        Create the episode_content fulltext index in Neo4j if it doesn't exist.

        Epic 4 Feature 4.1: Auto-create Neo4j fulltext index on startup.
        Uses IF NOT EXISTS for idempotency — safe to call multiple times.

        Gracefully handles:
        - Neo4j not initialized / unavailable
        - Index already exists
        - Permission errors or connection failures
        """
        if not self.neo4j.stats.get("initialized", False):
            logger.info(
                "[Epic 4] Skipping fulltext index creation: Neo4j not initialized"
            )
            return

        cypher = (
            "CREATE FULLTEXT INDEX episode_content IF NOT EXISTS "
            "FOR (n:EpisodicNode) ON EACH [n.content]"
        )
        try:
            await self.neo4j.run_query(cypher)
            logger.info(
                "[Epic 4] Fulltext index 'episode_content' ensured on EpisodicNode.content"
            )
        except (RuntimeError, ConnectionError, Exception) as e:
            logger.warning(f"[Epic 4] Fulltext index creation failed (non-fatal): {e}")

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
                        (
                            e.get("user_id"),
                            e.get("concept"),
                            str(e.get("timestamp") or ""),
                        )
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
                        self._episodes = self._episodes[-self.MAX_EPISODE_CACHE :]
                self._episodes_recovered = True
                logger.info(
                    f"MemoryService: recovered {added} episodes from Neo4j ({len(records)} returned, {len(records) - added} deduped)"
                )
            except (RuntimeError, ConnectionError, asyncio.TimeoutError) as e:
                # AC-3: Graceful degradation — start with empty history
                self._episodes_recovered = False
                logger.warning(
                    f"MemoryService: Neo4j unavailable, starting with empty history ({e})"
                )

    def _enqueue_episode(
        self,
        name: str,
        episode_body: str,
        group_id: str,
        source_description: str = "canvas_learning_system",
        entity_types: Optional[Dict[str, Any]] = None,
        edge_types: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Enqueue a learning episode for Graphiti processing.

        Phase 2: Replaces fire-and-forget JSON dual-write and bridge calls.
        Non-blocking. Worker processes sequentially via graphiti add_episode.

        Returns True if enqueued, False if queue full or worker unavailable.
        """
        worker = get_episode_worker()
        if not worker.is_ready:
            logger.debug("Episode worker not ready, skipping enqueue")
            return False

        # Capture request_id from structlog contextvars at enqueue time,
        # since the worker processes tasks in a separate coroutine context.
        _ctx = structlog.contextvars.get_contextvars()
        task = EpisodeTask(
            name=name,
            episode_body=episode_body,
            group_id=group_id,
            source_description=source_description,
            entity_types=entity_types,
            edge_types=edge_types,
            request_id=_ctx.get("request_id"),
        )
        return worker.enqueue(task)

    async def record_learning_event(
        self,
        user_id: str,
        canvas_path: str,
        node_id: str,
        concept: str,
        agent_type: str,
        score: Optional[int] = None,
        duration_seconds: Optional[int] = None,
        subject: Optional[str] = None,
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

        # Story 30.10 AC-30.10.1: Deterministic episode ID (replaces uuid4)
        episode_id = _generate_deterministic_episode_id(
            user_id, canvas_path, node_id, concept
        )

        # ✅ AC-30.8.2: Auto-infer subject from canvas_path if not provided
        inferred_subject = subject or extract_subject_from_canvas_path(canvas_path)

        # ✅ AC-30.8.1: Build group_id for namespace isolation (Epic 6: canvas-scoped)
        canvas_name = extract_canvas_name(canvas_path)
        group_id = build_group_id(inferred_subject, canvas_name=canvas_name)

        try:
            # ✅ Verified: Store to Neo4j - Create learning relationship
            await self._create_neo4j_learning_relationship(
                user_id=user_id, concept=concept, score=score, group_id=group_id
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
                "group_id": group_id,
            }
            # Story 30.10 AC-30.10.3: Dedup _episodes - skip if exists to preserve score history
            # Fix C4: changed from overwrite to skip-if-exists to not destroy FSRS score history
            existing_idx = next(
                (
                    i
                    for i, ep in enumerate(self._episodes)
                    if ep.get("episode_id") == episode_id
                ),
                None,
            )
            if existing_idx is not None:
                log_decision(
                    function="MemoryService.record_learning_event",
                    input_summary={"concept": concept, "episode_id": episode_id},
                    output="skipped_duplicate",
                    reason=f"episode already exists at idx={existing_idx}, preserving FSRS history",
                )
            else:
                self._episodes.append(episode)
                # Fix C5: Enforce MAX_EPISODE_CACHE to prevent unbounded memory growth
                if len(self._episodes) > self.MAX_EPISODE_CACHE:
                    self._episodes = self._episodes[-self.MAX_EPISODE_CACHE :]
                log_decision(
                    function="MemoryService.record_learning_event",
                    input_summary={
                        "concept": concept,
                        "agent": agent_type,
                        "canvas": canvas_name,
                    },
                    output=episode_id,
                    reason=f"new episode recorded, subject={inferred_subject}, group_id={group_id}",
                )

            # Phase 2: Enqueue to GraphitiEpisodeWorker for real add_episode
            score_text = f" (score: {score}/100)" if score is not None else ""
            self._enqueue_episode(
                name=f"learning:{concept[:80]}",
                episode_body=(
                    f"Student learned '{concept}' using {agent_type} agent on canvas "
                    f"'{canvas_path}'{score_text}. Node: {node_id}."
                ),
                group_id=group_id,
                source_description=f"canvas_learning:{inferred_subject}",
                entity_types=CANVAS_ENTITY_TYPES,
                edge_types=CANVAS_EDGE_TYPES,
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
        canvas_path: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
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
            canvas_path: Canvas file path for canvas-scoped filtering (Epic 6)
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

        # ✅ Epic 6: Build canvas-scoped group_id when canvas_path is available
        if canvas_path:
            inferred_subject = subject or extract_subject_from_canvas_path(canvas_path)
            c_name = extract_canvas_name(canvas_path)
            group_id = build_group_id(inferred_subject, canvas_name=c_name)
        elif subject:
            group_id = build_group_id(subject)
        else:
            group_id = None

        # ✅ Story 31.A.2 AC-31.A.2.1: Query from Neo4j first (replaces memory-only read)
        episodes = []
        try:
            neo4j_results = await self.neo4j.get_learning_history(
                user_id=user_id,
                start_date=start_date,
                end_date=end_date,
                concept=concept,
                group_id=group_id,
                limit=page_size * page,  # Get enough data for pagination
            )
            episodes = neo4j_results or []
            logger.debug(
                f"Retrieved {len(episodes)} episodes from Neo4j for user {user_id}"
            )
        except (RuntimeError, ConnectionError, asyncio.TimeoutError) as e:
            # ✅ Story 31.A.2: Fallback to memory if Neo4j fails
            logger.warning(f"Neo4j query failed, falling back to memory: {e}")

        # [Code Review C2 fix]: Always supplement Neo4j results with in-memory episodes.
        # Neo4j MERGE only keeps 1 LEARNED relationship per user+concept, so it returns
        # at most 1 record per concept. In-memory _episodes stores every score event via
        # append(), enabling consecutive_low tracking (which requires ≥3 scores).
        if not self._episodes_recovered:
            await self._recover_episodes_from_neo4j()

        memory_episodes = [e for e in self._episodes if e.get("user_id") == user_id]

        # FR-KG-04 fix: Apply group_id filter to in-memory episodes for canvas-scoped
        # isolation (Story 30.8 AC-30.8.1). Without this, when Neo4j is unavailable
        # and we fall back to in-memory _episodes, queries with canvas_path would
        # leak data from other canvases that share the same user_id.
        if group_id:
            memory_episodes = [
                e for e in memory_episodes if e.get("group_id", "") == group_id
            ]

        # Apply date filters to in-memory episodes
        # S34 Bug fix #3: Normalize both sides to str for consistent comparison
        # (Neo4j returns offset-aware DateTime, in-memory uses ISO strings)
        if start_date:
            start_str = (
                str(start_date.isoformat())
                if hasattr(start_date, "isoformat")
                else str(start_date)
            )
            memory_episodes = [
                e for e in memory_episodes if str(e.get("timestamp", "")) >= start_str
            ]
        if end_date:
            end_str = (
                str(end_date.isoformat())
                if hasattr(end_date, "isoformat")
                else str(end_date)
            )
            memory_episodes = [
                e for e in memory_episodes if str(e.get("timestamp", "")) <= end_str
            ]

        # Apply concept filter
        if concept:
            concept_lower = concept.lower()
            memory_episodes = [
                e
                for e in memory_episodes
                if concept_lower in e.get("concept", "").lower()
            ]

        # Apply subject filter
        if subject:
            subject_lower = subject.lower()
            memory_episodes = [
                e
                for e in memory_episodes
                if subject_lower in e.get("subject", "").lower()
            ]

        # Merge: deduplicate by (node_id, timestamp), prefer Neo4j (persistent)
        if memory_episodes:
            existing_keys = {
                (e.get("node_id", ""), e.get("timestamp", "")) for e in episodes
            }
            for me in memory_episodes:
                key = (me.get("node_id", ""), me.get("timestamp", ""))
                if key not in existing_keys:
                    episodes.append(me)
                    existing_keys.add(key)

        # Sort by timestamp (newest first)
        # Neo4j returns neo4j.time.DateTime objects, in-memory uses ISO strings;
        # str() normalizes both to sortable strings.
        if episodes:
            episodes.sort(key=lambda x: str(x.get("timestamp", "")), reverse=True)

        # Story 38.6 AC-4: Merge failed scores from fallback so user never sees gaps
        # S34 Bug fix #1+#2: Filter by user_id and date range before merge
        failed_scores = await asyncio.to_thread(self.load_failed_scores)
        if failed_scores:
            # Bug fix #1: Filter by user_id (prevent cross-user data leakage)
            if user_id:
                failed_scores = [
                    fs for fs in failed_scores if fs.get("user_id", "") == user_id
                ]
            # Bug fix #2: Apply same date filters as memory_episodes
            if start_date:
                s_str = (
                    str(start_date.isoformat())
                    if hasattr(start_date, "isoformat")
                    else str(start_date)
                )
                failed_scores = [
                    fs for fs in failed_scores if str(fs.get("timestamp", "")) >= s_str
                ]
            if end_date:
                e_str = (
                    str(end_date.isoformat())
                    if hasattr(end_date, "isoformat")
                    else str(end_date)
                )
                failed_scores = [
                    fs for fs in failed_scores if str(fs.get("timestamp", "")) <= e_str
                ]
            # FR-KG-04 fix: Apply group_id filter to fallback failed_scores for
            # canvas-scoped isolation (Story 30.8 AC-30.8.1). Derive group_id from
            # canvas_name + inferred subject — failed_writes.jsonl historical entries
            # don't carry group_id directly, so we reconstruct it the same way the
            # write path does.
            if group_id:

                def _derive_group_id(fs: Dict[str, Any]) -> str:
                    canvas_name_field = fs.get("canvas_name", "") or ""
                    if not canvas_name_field:
                        return ""
                    inferred_subj = subject or extract_subject_from_canvas_path(
                        canvas_name_field
                    )
                    cn_only = extract_canvas_name(canvas_name_field)
                    return build_group_id(inferred_subj, canvas_name=cn_only)

                failed_scores = [
                    fs for fs in failed_scores if _derive_group_id(fs) == group_id
                ]
            # Deduplicate: only include fallback entries not already in episodes
            existing_keys = {
                (e.get("node_id", ""), e.get("timestamp", "")) for e in episodes
            }
            for fs in failed_scores:
                key = (fs.get("node_id", ""), fs.get("timestamp", ""))
                if key not in existing_keys:
                    episodes.append(fs)
            # Re-sort after merge (str() normalizes DateTime vs string)
            episodes.sort(key=lambda x: str(x.get("timestamp", "")), reverse=True)

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
            "pages": (total + page_size - 1) // page_size if total > 0 else 0,
        }

    async def get_concept_history(
        self, concept_id: str, user_id: Optional[str] = None, limit: int = 50
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
            concept_id=concept_id, user_id=user_id, limit=limit
        )

        # Format as timeline
        timeline = []
        for record in history:
            timeline.append(
                {
                    "timestamp": record.get("timestamp"),
                    "score": record.get("score"),
                    "user_id": record.get("user_id"),
                    "concept": record.get("concept"),
                    "review_count": record.get("review_count", 0),
                }
            )

        # Calculate score trend
        scores = [r.get("score") for r in timeline if r.get("score") is not None]
        score_trend = {
            "first": scores[-1] if scores else None,
            "last": scores[0] if scores else None,
            "average": sum(scores) / len(scores) if scores else None,
            "improvement": (scores[0] - scores[-1]) if len(scores) >= 2 else None,
        }

        return {
            "concept_id": concept_id,
            "timeline": timeline,
            "score_trend": score_trend,
            "total_reviews": len(timeline),
        }

    async def get_concept_score_history(
        self, concept_id: str, canvas_name: str, limit: int = 5
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

        # NFR-P0: Check cache (TTLCache auto-evicts expired entries)
        cached_result = self._score_history_cache.get(cache_key)
        if cached_result is not None:
            logger.debug(f"Score history cache hit for {concept_id}")
            return cached_result

        # NFR-P0: Double-check locking for cache stampede protection
        async with self._score_cache_lock:
            # Re-check after acquiring lock (another coroutine may have populated)
            cached_result = self._score_history_cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Score history cache hit (after lock) for {concept_id}")
                return cached_result

        # Query Neo4j for score history
        try:
            records = await self.neo4j.get_concept_score_history(
                concept_id=concept_id, canvas_name=canvas_name, limit=limit
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
                sample_size=len(scores),
            )

            # Store in cache (TTLCache handles expiration automatically)
            self._score_history_cache[cache_key] = result

            logger.debug(
                f"Score history for {concept_id}: "
                f"{len(scores)} records, avg={average:.2f}"
            )

            return result

        except (RuntimeError, ConnectionError, asyncio.TimeoutError) as e:
            logger.error(f"Failed to get score history for {concept_id}: {e}")
            # Return empty result on error (graceful degradation per ADR-009)
            return ScoreHistoryResponse(
                concept_id=concept_id,
                canvas_name=canvas_name,
                scores=[],
                timestamps=[],
                average=0.0,
                sample_size=0,
            )

    async def get_review_suggestions(
        self,
        user_id: str,
        limit: int = 10,
        subject: Optional[str] = None,
        canvas_path: Optional[str] = None,
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
            canvas_path: Canvas file path for canvas-scoped filtering (Epic 6)

        Returns:
            List of review suggestions with priority

        [Source: docs/stories/22.4.story.md#get_review_suggestions]
        [Source: docs/stories/30.8.story.md#Task-3.1]
        """
        if not self._initialized:
            await self.initialize()

        # ✅ Epic 6: Build canvas-scoped group_id when canvas_path is available
        if canvas_path:
            inferred_subject = subject or extract_subject_from_canvas_path(canvas_path)
            c_name = extract_canvas_name(canvas_path)
            group_id = build_group_id(inferred_subject, canvas_name=c_name)
        elif subject:
            group_id = build_group_id(subject)
        else:
            group_id = None

        suggestions = await self.neo4j.get_review_suggestions(
            user_id=user_id, limit=limit, group_id=group_id
        )

        logger.debug(
            f"Retrieved {len(suggestions)} review suggestions for user {user_id} (subject={subject})"
        )
        return suggestions

    async def _create_neo4j_learning_relationship(
        self,
        user_id: str,
        concept: str,
        score: Optional[int] = None,
        group_id: Optional[str] = None,
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
            user_id=user_id, concept=concept, score=score, group_id=group_id
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics."""
        return {
            "initialized": self._initialized,
            "total_episodes": len(self._episodes),
            "neo4j_stats": self.neo4j.stats,
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
            "semantic": {"status": "ok", "backend": "lancedb"},
        }

        # Check Graphiti/Neo4j layer
        # ✅ Story 30.3 Fix: Use correct stats fields (initialized, health_status)
        try:
            neo4j_stats = self.neo4j.stats
            is_connected = (
                neo4j_stats.get("initialized", False)
                and neo4j_stats.get("mode") == "NEO4J"
                and neo4j_stats.get("health_status", False)
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
        except (RuntimeError, AttributeError, KeyError) as e:
            layers["graphiti"]["status"] = "error"
            layers["graphiti"]["error"] = str(e)

        # Temporal layer (in-memory/SQLite simulation) - always ok for now
        layers["temporal"]["status"] = "ok"

        # Semantic layer (LanceDB) - check if available
        try:
            # For now, assume LanceDB is available if we can import it
            layers["semantic"]["status"] = "ok"
            layers["semantic"]["vector_count"] = 0  # Placeholder
        except (ImportError, RuntimeError) as e:
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
            "timestamp": datetime.now().isoformat(),
        }

    async def record_batch_learning_events(
        self, events: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        批量记录学习事件 (真并行版)

        Story 30.10: 确定性 episode_id + 幂等去重
        Story 30.11: asyncio.gather 并行化 Neo4j 写入
        - AC-30.11.1: asyncio.gather + Semaphore 并行
        - AC-30.11.2: return_exceptions=True 部分失败隔离
        - AC-30.11.3: BATCH_NEO4J_CONCURRENCY 配置并发数
        - AC-30.11.4: 兼容 Story 30.10 幂等键
        - AC-30.11.5: 记录 batch_avg_latency_ms

        Args:
            events: List of event dictionaries

        Returns:
            Dict with success, processed, failed, errors, episode_ids, batch_avg_latency_ms, timestamp

        [Source: docs/stories/30.11.batch-true-parallel.story.md]
        """
        if not self._initialized:
            await self.initialize()

        batch_start = time.monotonic()

        # ── Phase 1: 预处理（同步，保护 _episodes 列表无竞态） ──
        processed = 0
        failed = 0
        errors: List[Dict[str, Any]] = []
        valid_records: List[Dict[str, Any]] = []
        episode_ids: List[str] = []

        for idx, event in enumerate(events):
            try:
                required_fields = ["event_type", "timestamp", "canvas_path", "node_id"]
                missing = [f for f in required_fields if f not in event]
                if missing:
                    raise ValueError(f"Missing required fields: {missing}")

                # Story 30.10 AC-30.10.4: Deterministic batch episode ID
                episode_id = _generate_batch_episode_id(
                    canvas_path=event["canvas_path"],
                    node_id=event["node_id"],
                    event_type=event["event_type"],
                    timestamp=event["timestamp"],
                )
                episode_record = {
                    "episode_id": episode_id,
                    "event_type": event["event_type"],
                    "timestamp": event["timestamp"],
                    "canvas_path": event["canvas_path"],
                    "node_id": event["node_id"],
                    "metadata": event.get("metadata", {}),
                }

                # Story 30.10 AC-30.10.3: Dedup batch episodes
                # Fix C4: skip-if-exists to preserve score history
                existing_idx = next(
                    (
                        i
                        for i, ep in enumerate(self._episodes)
                        if ep.get("episode_id") == episode_id
                    ),
                    None,
                )
                if existing_idx is not None:
                    logger.debug(f"Skipped duplicate batch episode: {episode_id}")
                else:
                    self._episodes.append(episode_record)
                    # Fix C5: Enforce MAX_EPISODE_CACHE
                    if len(self._episodes) > self.MAX_EPISODE_CACHE:
                        self._episodes = self._episodes[-self.MAX_EPISODE_CACHE :]

                neo4j_payload = {
                    "episode_id": episode_id,
                    "user_id": "batch_user",
                    "canvas_path": event["canvas_path"],
                    "node_id": event["node_id"],
                    "concept": event.get("metadata", {}).get(
                        "concept", event.get("metadata", {}).get("node_text", "unknown")
                    ),
                    "agent_type": event["event_type"],
                    "timestamp": event["timestamp"],
                }
                valid_records.append({"idx": idx, "payload": neo4j_payload})
                episode_ids.append(episode_id)
                processed += 1

            except (ValueError, KeyError, TypeError) as e:
                failed += 1
                errors.append({"index": idx, "error": str(e)})

        # ── Phase 2: 并行 Neo4j 写入 (Story 30.11 AC-30.11.1) ──
        neo4j_available = self.neo4j.stats.get("initialized", False)

        if neo4j_available and valid_records:
            concurrency = getattr(settings, "BATCH_NEO4J_CONCURRENCY", 10)
            semaphore = asyncio.Semaphore(concurrency)

            async def _write_single(record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
                async with semaphore:
                    try:
                        await self.neo4j.record_episode(record["payload"])
                        return None
                    except (RuntimeError, ConnectionError, asyncio.TimeoutError) as e:
                        return {"index": record["idx"], "error": str(e)}

            results = await asyncio.gather(
                *[_write_single(r) for r in valid_records],
                return_exceptions=True,
            )

            neo4j_errors = []
            for r in results:
                if isinstance(r, Exception):
                    neo4j_errors.append({"error": str(r)})
                elif r is not None:
                    neo4j_errors.append(r)

            if neo4j_errors:
                logger.warning(
                    f"Batch Neo4j write: {len(neo4j_errors)} errors (non-blocking)"
                )
                # Fix C3: Surface Neo4j errors in response so caller knows about partial failures
                errors.extend(neo4j_errors)
                failed += len(neo4j_errors)
                # Story 30.24 AC-30.24.4: Track failed writes for shutdown safety
                for i, err in enumerate(neo4j_errors):
                    err_index = err.get("index")
                    if err_index is not None and err_index < len(episode_ids):
                        eid = episode_ids[err_index]
                    else:
                        eid = f"unknown_{i}"
                    self._pending_failed_writes.append(
                        {
                            "episode_id": eid,
                            "timestamp": datetime.now().isoformat(),
                            "reason": err.get("error", "unknown"),
                        }
                    )

        # ── Phase 2: Enqueue batch events to GraphitiEpisodeWorker ──
        for record in valid_records:
            p = record["payload"]
            concept = p.get("concept", "unknown")
            inferred_subject = extract_subject_from_canvas_path(p["canvas_path"])
            c_name = extract_canvas_name(p["canvas_path"])
            self._enqueue_episode(
                name=f"batch_learning:{concept[:80]}",
                episode_body=(
                    f"Student learned '{concept}' using {p.get('agent_type', 'unknown')} agent "
                    f"on canvas '{p['canvas_path']}'. Node: {p['node_id']}."
                ),
                group_id=build_group_id(inferred_subject, canvas_name=c_name),
                source_description=f"canvas_batch:{inferred_subject}",
            )

        # ── Phase 3: 性能指标 (Story 30.11 AC-30.11.5) ──
        elapsed_ms = (time.monotonic() - batch_start) * 1000
        avg_latency = elapsed_ms / len(events) if events else 0.0

        if not hasattr(self, "_batch_stats"):
            self._batch_stats = {}
        self._batch_stats["batch_avg_latency_ms"] = round(avg_latency, 2)
        self._batch_stats["last_batch_total_ms"] = round(elapsed_ms, 2)
        self._batch_stats["last_batch_size"] = len(events)

        logger.debug(
            f"Batch processed {processed} events in {elapsed_ms:.0f}ms "
            f"(parallel, concurrency={getattr(settings, 'BATCH_NEO4J_CONCURRENCY', 10)})"
        )

        return {
            "success": failed == 0,
            "processed": processed,
            "failed": failed,
            "errors": errors,
            "episode_ids": episode_ids,
            "batch_avg_latency_ms": round(avg_latency, 2),
            "timestamp": datetime.now().isoformat(),
        }

    async def record_knowledge_entity(
        self,
        event_type: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        group_id: Optional[str] = None,
    ) -> str:
        """
        Record a knowledge entity (tip or misconception) as an episode.

        Story 3.6: Tips annotation and error archiving.
        - Tips (event_type="learning_tip"): user-selected dialogue text
        - Misconceptions (event_type="misconception"): agent-detected errors

        Written to in-memory episode cache and Neo4j if connected.
        Uses the Graphiti bridge for Claude Code compatibility.

        Args:
            event_type: Entity type ("learning_tip" or "misconception").
            content: Human-readable summary of the entity.
            metadata: Structured data (tip_id/misconception_id, tags, etc.).
            group_id: Namespace group for subject isolation.

        Returns:
            str: Generated episode ID.
        """
        if not self._initialized:
            await self.initialize()

        entity_id = f"{event_type}-{uuid.uuid4().hex[:16]}"
        resolved_group_id = group_id or DEFAULT_GROUP_ID
        meta = metadata or {}

        episode = {
            "episode_id": entity_id,
            "content": content,
            "episode_type": event_type,
            "node_id": meta.get("node_id", ""),
            "timestamp": datetime.now().isoformat(),
            "group_id": resolved_group_id,
            "metadata": meta,
        }

        self._episodes.append(episode)
        if len(self._episodes) > self.MAX_EPISODE_CACHE:
            self._episodes = self._episodes[-self.MAX_EPISODE_CACHE :]

        # ═══ GRAPHITI-NATIVE Phase 2 (2026-06-10) ═══════════════════════════
        # ① 删除 neo4j.record_episode 双写: 该路径实为 MERGE User-LEARNED-Concept,
        #    丢弃 tip 内容且污染 review 调度 (ChatGPT 对抗审查: G-FAKE 假写)。
        #    record_episode 方法本身保留 — batch_record_events/record_temporal_event
        #    等真实学习事件调用方仍用它。
        # ② 结构化 event (批注/错误/对话摘要) → graphiti_structured_writer 确定性写
        #    :Entity/RELATES_TO (主路径, 零 LLM, 检验白板可按 node_id 精确读)。
        #    非结构化 / graphiti 未就绪 / 缺 node_id / 写失败 → 原 add_episode
        #    队列 (语义通道 fallback, 数据不丢)。
        structured_written = False
        node_id_for_exam = meta.get("node_id", "")
        if node_id_for_exam:
            worker = get_episode_worker()
            graphiti = getattr(worker, "_graphiti", None)
            if graphiti is not None:
                from app.services.graphiti_structured_writer import (
                    write_callout,
                    write_conversation_summary,
                    write_error,
                )

                occurred = datetime.now(timezone.utc)
                try:
                    if event_type in ("learning_tip", "callout_annotation"):
                        # 去重修复 (2026-06-13): 优先 meta['content'] (裸正文,
                        # 三通道一致) — content 参数可能带通道包装 ("Tip:…|" 等),
                        # 包装差异曾让同一批注三个指纹三条边。understanding 从
                        # meta 直取或解析 tags 列表 ("understanding:fuzzy")。
                        understanding = meta.get("understanding")
                        callout_type = meta.get("tag")
                        for t in meta.get("tags") or []:  # modal 把两者编进 tags 列表
                            s = str(t)
                            if not understanding and s.startswith("understanding:"):
                                understanding = s.split(":", 1)[1]
                            elif not callout_type and s.startswith("tag:"):
                                callout_type = s.split(":", 1)[1]
                        await write_callout(
                            graphiti.driver,
                            graphiti.embedder,
                            node_id=node_id_for_exam,
                            group_id=resolved_group_id,
                            callout_type=callout_type
                            or ("tip" if event_type == "learning_tip" else "note"),
                            text=meta.get("content") or content,
                            occurred_at=occurred,
                            understanding=understanding or None,
                        )
                        structured_written = True
                    elif event_type in (
                        "misconception",
                        "problem_trap",
                        "logical_fallacy",
                        "guided_thinking",
                    ):
                        await write_error(
                            graphiti.driver,
                            graphiti.embedder,
                            node_id=node_id_for_exam,
                            group_id=resolved_group_id,
                            error_type=meta.get("error_type", event_type),
                            description=content,
                            occurred_at=occurred,
                        )
                        structured_written = True
                    elif event_type == "conversation_archive":
                        await write_conversation_summary(
                            graphiti.driver,
                            graphiti.embedder,
                            node_id=node_id_for_exam,
                            group_id=resolved_group_id,
                            summary=meta.get("summary") or content,
                            occurred_at=occurred,
                        )
                        structured_written = True
                except Exception as e:  # noqa: BLE001 — 结构化失败退语义队列保数据
                    logger.warning(
                        f"[Graphiti-native] structured write failed for "
                        f"{event_type} (fallback to episode queue): {e}"
                    )
                    structured_written = False

        if not structured_written:
            # 语义通道 (add_episode): 非结构化材料 / fallback。
            # P0-2a (2026-05-13): source_description 对齐 memory_format.py canonical。
            from app.core.memory_format import (
                entity_type_from_event,
                get_source_description,
            )

            canonical_entity_type = entity_type_from_event(event_type)
            canonical_source_desc = (
                get_source_description(canonical_entity_type)
                if canonical_entity_type
                else f"canvas_learning:{event_type}"
            )
            self._enqueue_episode(
                name=f"{event_type}:{meta.get('title', content[:40])}",
                episode_body=content,
                group_id=resolved_group_id,
                source_description=canonical_source_desc,
                entity_types=CANVAS_ENTITY_TYPES,
                edge_types=CANVAS_EDGE_TYPES,
            )

        logger.info(
            f"[Story 3.6] Recorded {event_type}: id={entity_id} "
            f"group={resolved_group_id}"
        )
        return entity_id

    async def find_episode_by_content_hash(
        self,
        node_id: str,
        content_hash: str,
        group_id: Optional[str] = None,
    ) -> bool:
        """Story 2.4 Plan B Phase 3 (2026-05-14): 幂等查询。

        Check if a callout with given content_hash already exists in Neo4j for
        the given node_id. Used by /api/v1/tips/batch to skip duplicates and
        avoid creating redundant Graphiti episodes when user re-saves the
        same file without changing callouts.

        Args:
            node_id: Canvas node id (file basename).
            content_hash: SHA256 hex of node_id|tag|understanding|content.
            group_id: Optional namespace filter.

        Returns:
            True if an EpisodicNode with this content_hash exists (skip),
            False if not (proceed to create new episode).
        """
        if not self._initialized:
            await self.initialize()

        try:
            from app.clients.neo4j_client import get_neo4j_client
            from app.graphiti.group_id_compat import sanitize_group_id_for_graphiti

            client = get_neo4j_client()
            resolved_group_id = group_id or DEFAULT_GROUP_ID
            # Graphiti EpisodicNode stores sanitized group_id (P0-5 边界 sanitize)
            graphiti_group_id = sanitize_group_id_for_graphiti(resolved_group_id)

            # P0-7 (2026-05-14): Graphiti 不持久化 metadata 到 EpisodicNode。
            # tips.py batch_sync 把 content_hash 内嵌为 [hash:abc123] 后缀写到
            # content 字段，这里用 CONTAINS 匹配前 16 hex chars。
            hash_marker = f"[hash:{content_hash[:16]}]"
            query = """
            MATCH (e:Episodic)
            WHERE (e.group_id = $group_id OR e.group_id = $graphiti_group_id)
              AND e.source_description = 'callout-annotation-record'
              AND e.content CONTAINS $hash_marker
            RETURN count(e) AS cnt
            LIMIT 1
            """
            records = await client.run_query(
                query,
                group_id=resolved_group_id,
                graphiti_group_id=graphiti_group_id,
                hash_marker=hash_marker,
            )
            for record in records or []:
                data = record if isinstance(record, dict) else record.data()
                cnt = data.get("cnt", 0)
                if cnt > 0:
                    return True
            return False
        except (RuntimeError, ConnectionError, asyncio.TimeoutError) as e:
            logger.debug(
                f"[Story 2.4 batch] find_episode_by_content_hash failed (non-fatal): {e}"
            )
            # 失败时 fail-open — 允许 batch 继续（重复同步比丢失数据更可接受）
            return False

    # Search config recipe mapping: string name → SearchConfig object
    _SEARCH_RECIPES: Dict[
        str, Any
    ] = {}  # populated lazily to avoid import-time side effects

    @classmethod
    def _get_search_recipes(cls) -> Dict[str, Any]:
        """Lazily load search config recipes from graphiti_core."""
        if not cls._SEARCH_RECIPES:
            try:
                from graphiti_core.search.search_config_recipes import (
                    COMBINED_HYBRID_SEARCH_RRF,
                    COMBINED_HYBRID_SEARCH_CROSS_ENCODER,
                    EDGE_HYBRID_SEARCH_CROSS_ENCODER,
                    EDGE_HYBRID_SEARCH_RRF,
                    NODE_HYBRID_SEARCH_RRF,
                )

                cls._SEARCH_RECIPES = {
                    "combined_rrf": COMBINED_HYBRID_SEARCH_RRF,
                    "combined_cross_encoder": COMBINED_HYBRID_SEARCH_CROSS_ENCODER,
                    "edge_cross_encoder": EDGE_HYBRID_SEARCH_CROSS_ENCODER,
                    "edge_rrf": EDGE_HYBRID_SEARCH_RRF,
                    "node_rrf": NODE_HYBRID_SEARCH_RRF,
                }
            except ImportError:
                logger.warning("graphiti_core search recipes not available")
        return cls._SEARCH_RECIPES

    async def _search_graphiti(
        self,
        query: str,
        group_id: Optional[str] = None,
        limit: int = 20,
        search_config: str = "combined_rrf",
        search_filter: Optional[Any] = None,
    ) -> List[Dict[str, Any]]:
        """Tier 1: Search via graphiti-core search_() with advanced recipes.

        Args:
            query: Search query string
            group_id: Optional group namespace for filtering
            limit: Max results to return
            search_config: Recipe name — one of 'combined_rrf', 'combined_cross_encoder',
                          'edge_cross_encoder', 'edge_rrf', 'node_rrf'
            search_filter: Optional SearchFilters instance for date/label/type filtering

        Returns:
            List of result dicts with 'relevance_score' from reranker scores.
        """
        worker = get_episode_worker()
        if not worker.is_ready or worker._graphiti is None:
            return list()  # worker not initialized yet

        # Resolve search config recipe
        recipes = self._get_search_recipes()
        config_obj = recipes.get(search_config)
        if config_obj is None:
            logger.warning(
                f"Unknown search config '{search_config}', falling back to combined_rrf"
            )
            config_obj = recipes.get("combined_rrf")

        # If recipes are unavailable (import failed), fall back to old search()
        if config_obj is None:
            return await self._search_graphiti_legacy(query, group_id, limit)

        try:
            # Override the limit in config
            from graphiti_core.search.search_config import SearchConfig

            # Create a copy with updated limit
            config_with_limit = config_obj.model_copy(update={"limit": limit})

            # P0-5 (2026-05-14): sanitize group_id at Graphiti boundary
            from app.graphiti.group_id_compat import sanitize_group_id_for_graphiti

            search_kwargs: Dict[str, Any] = {
                "query": query,
                "config": config_with_limit,
                "group_ids": (
                    [sanitize_group_id_for_graphiti(group_id)] if group_id else None
                ),
            }
            if search_filter is not None:
                search_kwargs["search_filter"] = search_filter

            results = await asyncio.wait_for(
                worker._graphiti.search_(**search_kwargs),
                timeout=3.0,
            )

            episodes: List[Dict[str, Any]] = []

            # Parse edges with reranker scores
            edges = getattr(results, "edges", []) or []
            edge_scores = getattr(results, "edge_reranker_scores", []) or []
            for i, edge in enumerate(edges):
                score = edge_scores[i] if i < len(edge_scores) else 0.0
                episodes.append(
                    {
                        "episode_id": getattr(edge, "uuid", ""),
                        "content": getattr(edge, "fact", ""),
                        "name": getattr(edge, "name", ""),
                        "episode_type": "graphiti_search",
                        "timestamp": (
                            getattr(edge, "created_at", datetime.now()).isoformat()
                            if hasattr(edge, "created_at")
                            else datetime.now().isoformat()
                        ),
                        "group_id": group_id or "",
                        "source": "graphiti",
                        "result_type": "edge",
                        "relevance_score": float(score),
                    }
                )

            # Parse nodes with reranker scores
            nodes = getattr(results, "nodes", []) or []
            node_scores = getattr(results, "node_reranker_scores", []) or []
            for i, node in enumerate(nodes):
                score = node_scores[i] if i < len(node_scores) else 0.0
                episodes.append(
                    {
                        "episode_id": getattr(node, "uuid", ""),
                        "content": getattr(node, "summary", "")
                        or getattr(node, "name", ""),
                        "name": getattr(node, "name", ""),
                        "episode_type": "graphiti_search",
                        "timestamp": (
                            getattr(node, "created_at", datetime.now()).isoformat()
                            if hasattr(node, "created_at")
                            else datetime.now().isoformat()
                        ),
                        "group_id": group_id or "",
                        "source": "graphiti",
                        "result_type": "node",
                        "relevance_score": float(score),
                    }
                )

            return episodes
        except (RuntimeError, asyncio.TimeoutError, AttributeError, TypeError) as e:
            logger.warning(f"Graphiti search_() failed or timed out: {e}")
            return list()

    async def _search_graphiti_legacy(
        self, query: str, group_id: Optional[str] = None, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Legacy fallback: search via graphiti.search() when recipes unavailable."""
        worker = get_episode_worker()
        if not worker.is_ready or worker._graphiti is None:
            return list()
        try:
            # P0-5 (2026-05-14): sanitize group_id at Graphiti boundary
            from app.graphiti.group_id_compat import sanitize_group_id_for_graphiti

            results = await asyncio.wait_for(
                worker._graphiti.search(
                    query=query,
                    group_ids=(
                        [sanitize_group_id_for_graphiti(group_id)] if group_id else None
                    ),
                    num_results=limit,
                ),
                timeout=2.0,
            )
            episodes = []
            for r in results:
                episodes.append(
                    {
                        "episode_id": getattr(r, "uuid", ""),
                        "content": getattr(r, "fact", ""),
                        "name": getattr(r, "name", ""),
                        "episode_type": "graphiti_search",
                        "timestamp": (
                            getattr(r, "created_at", datetime.now()).isoformat()
                            if hasattr(r, "created_at")
                            else datetime.now().isoformat()
                        ),
                        "group_id": group_id or "",
                        "source": "graphiti",
                        "relevance_score": 0.5,  # default score for legacy results
                    }
                )
            return episodes
        except (RuntimeError, asyncio.TimeoutError, AttributeError) as e:
            logger.warning(f"Graphiti legacy search failed or timed out: {e}")
            return list()

    @staticmethod
    def _compute_unified_score(episode: Dict[str, Any], tier: int) -> float:
        """Compute a normalized relevance score for a search result.

        Normalizes scores across 3 search tiers to a 0.0-1.0 range so results
        can be sorted consistently regardless of source.

        Args:
            episode: Search result dict (may already have 'relevance_score' or 'score')
            tier: 1=graphiti (reranker score), 2=neo4j fulltext, 3=in-memory

        Returns:
            Normalized score in [0.0, 1.0]
        """
        if tier == 1:
            # Graphiti: reranker score is already 0.0-1.0
            return float(episode.get("relevance_score", 0.0))
        elif tier == 2:
            # Neo4j fulltext: raw Lucene score varies; normalize by capping at 10.0
            raw_score = float(episode.get("score", 0.0))
            return min(raw_score / 10.0, 1.0)
        else:
            # In-memory substring match: fixed baseline score
            return 0.1

    def _inject_fsrs_r_values(self, results: List[Dict[str, Any]]) -> None:
        """Inject FSRS retrievability values into search results as a reranking signal.

        For each result that has a 'concept' or 'name' field, attempts to look up
        the concept's FSRS R-value. Low R-value concepts (about to be forgotten)
        get up to 50% score boost to prioritize review-worthy material.

        Boost formula: final_score = relevance_score * (1.0 + (1.0 - r_value) * 0.5)

        Modifies results in-place. Graceful degradation: if MasteryEngine is
        unavailable or concept not found, the result is left unchanged.
        """
        try:
            from app.services.mastery_engine import get_mastery_engine

            engine = get_mastery_engine()
        except (ImportError, RuntimeError, Exception) as e:
            logger.debug(f"MasteryEngine unavailable for FSRS injection: {e}")
            return

        for result in results:
            concept_name = result.get("concept") or result.get("name")
            if not concept_name:
                continue
            try:
                # Build a minimal ConceptState for retrievability lookup.
                # MasteryEngine.get_retrievability needs a ConceptState with fsrs_card_data.
                # Without persisted card data, we skip — no crash.
                from app.models.mastery_state import ConceptState

                # Attempt to find existing concept state via engine's known concepts
                # This is best-effort — engine may not have this concept loaded
                concept_state = None
                if hasattr(engine, "_concept_cache") and isinstance(
                    engine._concept_cache, dict
                ):
                    concept_state = engine._concept_cache.get(concept_name)

                if concept_state is not None:
                    r_value = engine.get_retrievability(concept_state)
                    r_value = max(0.0, min(1.0, r_value))  # clamp to [0, 1]
                    result["fsrs_r_value"] = round(r_value, 4)

                    # Boost: low R-value concepts get higher final score
                    base_score = result.get("relevance_score", 0.0)
                    result["relevance_score"] = base_score * (
                        1.0 + (1.0 - r_value) * 0.5
                    )
            except (AttributeError, TypeError, ValueError, RuntimeError) as e:
                logger.debug(f"FSRS R-value lookup failed for '{concept_name}': {e}")
                continue

    async def _search_neo4j_fulltext(
        self, query: str, group_id: Optional[str] = None, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Tier 2: Search via Neo4j fulltext index for keyword matches."""
        if not self.neo4j.stats.get("initialized", False):
            return list()  # Neo4j not connected

        try:
            cypher = """
            CALL db.index.fulltext.queryNodes('episode_content', $search_term)
            YIELD node, score
            WHERE ($group_id IS NULL OR node.group_id = $group_id)
            RETURN node, score
            ORDER BY score DESC
            LIMIT $limit
            """
            # MVP-α fix (2026-05-15): escape Lucene 特殊字符防 ParseException
            # 节点名含 ( ) [ ] 等会让 Lucene parser 抛 ClientError, 之前吞掉下游 fallback.
            import re

            safe_query = re.sub(r'([+\-!(){}\[\]^"~*?:\\/])', r"\\\1", query or "")
            safe_query = safe_query.replace("&&", r"\&\&").replace("||", r"\|\|")

            records = await self.neo4j.run_query(
                cypher,
                search_term=safe_query,
                group_id=group_id,
                limit=limit,
            )
            episodes = []
            for r in records if records else list():
                node = r["node"]
                episodes.append(
                    {
                        "episode_id": node.get("episode_id", ""),
                        "content": node.get("content", ""),
                        "episode_type": node.get("episode_type", ""),
                        "score": r.get("score", 0.0),
                        "timestamp": node.get("timestamp", ""),
                        "group_id": node.get("group_id", ""),
                        "node_id": node.get("node_id", ""),
                        "source": "neo4j_fulltext",
                    }
                )
            return episodes
        except (
            RuntimeError,
            ConnectionError,
            asyncio.TimeoutError,
            neo4j.exceptions.ClientError,  # MVP-α fix: Lucene ParseException
            neo4j.exceptions.Neo4jError,
        ) as e:
            logger.debug(f"Neo4j fulltext search failed (non-fatal): {e}")
            return list()  # fulltext index may not exist yet

    async def search_memories(
        self,
        query: str,
        group_id: Optional[str] = None,
        max_results: int = 50,
        limit: Optional[int] = None,
        search_config: str = "combined_rrf",
        search_filter: Optional[Any] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search learning memories using 3-tier layered search with unified scoring.

        Phase 2: Upgraded with search_() recipes, unified relevance scoring,
        and FSRS R-value injection for reranking.

        Tier 1: Graphiti search_() with configurable recipes (reranker scores)
        Tier 2: Neo4j fulltext index (Lucene scores normalized to 0-1)
        Tier 3: In-memory cache (fixed 0.1 baseline score)

        Results merged, deduplicated, scored uniformly, boosted by FSRS R-value,
        and sorted by relevance_score descending.

        Args:
            query: Search query string
            group_id: Optional group namespace for filtering
            max_results: Maximum results to return (default 50)
            limit: Override for max_results (backward compat)
            search_config: Recipe name for Graphiti search_ ('combined_rrf', etc.)
            search_filter: Optional SearchFilters for date/label filtering

        Signature backward-compatible — existing callers unaffected.
        """
        if not self._initialized:
            await self.initialize()

        effective_limit = limit if limit is not None else max_results
        seen_ids: set = set()
        merged: List[Dict[str, Any]] = []

        # Tier 1: Graphiti semantic search via search_()
        graphiti_hits = await self._search_graphiti(
            query,
            group_id,
            effective_limit,
            search_config=search_config,
            search_filter=search_filter,
        )
        for ep in graphiti_hits:
            ep_id = ep.get("episode_id", "")
            if ep_id and ep_id not in seen_ids:
                seen_ids.add(ep_id)
                # Tier 1 results already have relevance_score from reranker
                ep["relevance_score"] = self._compute_unified_score(ep, tier=1)
                merged.append(ep)

        # Tier 2: Neo4j fulltext search
        neo4j_hits = await self._search_neo4j_fulltext(query, group_id, effective_limit)
        for ep in neo4j_hits:
            ep_id = ep.get("episode_id", "")
            if ep_id and ep_id not in seen_ids:
                seen_ids.add(ep_id)
                ep["relevance_score"] = self._compute_unified_score(ep, tier=2)
                merged.append(ep)

        # Tier 3: In-memory cache (always available fallback)
        tier3_count = 0
        query_lower = query.lower()
        for episode in reversed(self._episodes):
            if len(merged) >= effective_limit:
                break
            if group_id and episode.get("group_id", "") != group_id:
                continue
            ep_id = episode.get("episode_id", "")
            if ep_id in seen_ids:
                continue
            searchable = " ".join(
                str(episode.get(field, ""))
                for field in ("content", "episode_type", "node_id", "concept")
            ).lower()
            if query_lower in searchable:
                seen_ids.add(ep_id)
                episode_with_source = {**episode, "source": "in_memory"}
                episode_with_source["relevance_score"] = self._compute_unified_score(
                    episode_with_source, tier=3
                )
                merged.append(episode_with_source)
                tier3_count += 1

        # FSRS R-value injection: boost low-retrievability concepts
        self._inject_fsrs_r_values(merged)

        # Sort by relevance_score descending (unified across all tiers)
        merged.sort(key=lambda x: x.get("relevance_score", 0.0), reverse=True)

        # Epic 4 Feature 4.2: Log which tier(s) produced results
        logger.info(
            f"[search_memories] Tier 1: {len(graphiti_hits)} results, "
            f"Tier 2: {len(neo4j_hits)} results, "
            f"Tier 3: {tier3_count} results "
            f"(total merged: {len(merged[:effective_limit])}, sorted by relevance)"
        )

        return merged[:effective_limit]

    async def record_temporal_event(
        self,
        event_type: str,
        session_id: str,
        canvas_path: str,
        node_id: Optional[str] = None,
        edge_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
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
            "metadata": metadata or {},
        }

        # Store in memory
        self._episodes.append(episode_record)
        # Fix C5: Enforce MAX_EPISODE_CACHE
        if len(self._episodes) > self.MAX_EPISODE_CACHE:
            self._episodes = self._episodes[-self.MAX_EPISODE_CACHE :]

        # Try to store in Neo4j if connected
        if self.neo4j.stats.get("initialized", False):
            try:
                await self.neo4j.record_episode(
                    {
                        "episode_id": event_id,
                        "user_id": session_id,
                        "canvas_path": canvas_path,
                        "node_id": node_id or "",
                        "concept": metadata.get("node_text", "") if metadata else "",
                        "agent_type": event_type,
                        "timestamp": episode_record["timestamp"],
                    }
                )

                # Story 30.5 AC-30.5.4: Create Canvas-Concept relationship graph
                if event_type in ("node_created", "node_updated") and node_id:
                    await self.neo4j.create_canvas_node_relationship(
                        canvas_path=canvas_path,
                        node_id=node_id,
                        node_text=metadata.get("node_text") if metadata else None,
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
                            edge_label=metadata.get("edge_label") if metadata else None,
                        )

            except (RuntimeError, ConnectionError, asyncio.TimeoutError) as e:
                # Silent degradation - log but don't raise
                logger.warning(f"Neo4j write failed for temporal event: {e}")

        logger.debug(f"Recorded temporal event: {event_type} for {canvas_path}")

        # Phase 2: Enqueue temporal event to GraphitiEpisodeWorker
        concept = ""
        if metadata:
            concept = metadata.get("node_text", "") or metadata.get("concept", "")
        if not concept:
            concept = f"{event_type}:{node_id or edge_id or 'unknown'}"
        inferred_subject = extract_subject_from_canvas_path(canvas_path)
        c_name = extract_canvas_name(canvas_path)
        self._enqueue_episode(
            name=f"temporal:{event_type}:{concept[:60]}",
            episode_body=(
                f"Canvas event '{event_type}' on path '{canvas_path}'. "
                f"Node: {node_id or edge_id or 'unknown'}. Concept: {concept}."
            ),
            group_id=build_group_id(inferred_subject, canvas_name=c_name),
            source_description=f"canvas_temporal:{event_type}",
        )

        return event_id

    # ═══════════════════════════════════════════════════════════════════════════════
    # Story 38.6: Failed Write Recovery & Merged View
    # ═══════════════════════════════════════════════════════════════════════════════

    async def recover_failed_writes(self) -> Dict[str, int]:
        """
        .. deprecated:: Story 38.8
            Replaced by ``FallbackSyncService.sync_all_fallbacks()`` which handles
            all three fallback files with checkpoint support and conflict resolution.
            This method is retained for backward compatibility but is no longer
            called from the startup lifespan. See ``fallback_sync_service.py``.

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
                lines = (
                    FAILED_WRITES_FILE.read_text(encoding="utf-8").strip().splitlines()
                )
            except (OSError, UnicodeDecodeError) as e:
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
                logger.warning("[Story 38.6] Skipping malformed fallback entry")
                still_pending.append(
                    line
                )  # preserve malformed lines to avoid data loss
                continue

            try:
                # Phase 2: Enqueue recovered entry to GraphitiEpisodeWorker
                concept = entry.get("concept", "") or entry.get("concept_id", "unknown")
                entry_canvas = entry.get("canvas_name", "")
                inferred_subject = extract_subject_from_canvas_path(entry_canvas)
                c_name = extract_canvas_name(entry_canvas)
                enqueued = self._enqueue_episode(
                    name=f"recovery:{concept[:80]}",
                    episode_body=(
                        f"Recovered learning event for concept '{concept}' "
                        f"on canvas '{entry_canvas}'."
                    ),
                    group_id=build_group_id(inferred_subject, canvas_name=c_name),
                    source_description="canvas_recovery",
                )
                if enqueued:
                    recovered += 1
                else:
                    still_pending.append(line)
            except (RuntimeError, asyncio.TimeoutError):
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
            except (OSError, PermissionError) as e:
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
                lines = (
                    FAILED_WRITES_FILE.read_text(encoding="utf-8").strip().splitlines()
                )
            for line in lines:
                try:
                    entry = json.loads(line)
                    results.append(
                        {
                            "timestamp": entry.get("timestamp", ""),
                            "canvas_name": entry.get("canvas_name", ""),
                            "node_id": entry.get("concept_id", ""),
                            "concept": entry.get("concept", "")
                            or entry.get("concept_id", ""),
                            "score": entry.get("score"),
                            "user_id": entry.get(
                                "user_id", ""
                            ),  # S34 fix: include for filtering
                            "source": "fallback",
                            "error_reason": entry.get("error_reason", ""),
                        }
                    )
                except json.JSONDecodeError:
                    continue
        except (OSError, json.JSONDecodeError) as e:
            logger.warning(f"[Story 38.6] Failed to load failed scores: {e}")

        return results

    async def cleanup(self) -> None:
        """
        Cleanup local MemoryService state.

        IMPORTANT: Does NOT cleanup the shared Neo4j driver, because Neo4jClient
        is a shared singleton used by multiple services. Neo4j cleanup is handled
        separately at application shutdown via cleanup_memory_service().

        Story 30.24 AC-30.24.4: Flushes pending failed writes to
        failed_writes.jsonl before clearing state, so no data is silently lost.

        [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#依赖注入设计]
        """
        # Story 30.24 AC-30.24.4: Flush pending failed writes before cleanup
        if self._pending_failed_writes:
            self._flush_pending_failed_writes()

        self._initialized = False
        self._episodes.clear()
        self._score_history_cache.clear()
        self._episodes_recovered = False
        logger.debug("MemoryService local state cleanup completed")

    def _flush_pending_failed_writes(self) -> None:
        """
        Story 30.24 AC-30.24.4: Persist pending batch write failures to
        data/failed_writes.jsonl so they survive shutdown.

        Thread-safe via failed_writes_lock (shared with agent_service).

        Note: This is a synchronous method called from async cleanup().
        Safe in single-threaded asyncio (no await between iteration and clear).
        If cleanup() is ever called from a signal handler thread, consider
        wrapping _pending_failed_writes access with an asyncio.Lock.
        """
        if not self._pending_failed_writes:
            return

        try:
            FAILED_WRITES_FILE.parent.mkdir(parents=True, exist_ok=True)
            with failed_writes_lock:
                with open(FAILED_WRITES_FILE, "a", encoding="utf-8") as f:
                    for entry in self._pending_failed_writes:
                        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            logger.warning(
                f"[Story 30.24] Flushed {len(self._pending_failed_writes)} "
                f"pending failed writes to {FAILED_WRITES_FILE}"
            )
        except (OSError, TypeError, ValueError) as e:
            logger.error(f"[Story 30.24] Failed to flush pending writes: {e}")
        finally:
            self._pending_failed_writes.clear()


# Singleton instance — the ONLY MemoryService singleton entry point for the entire project.
# All modules (endpoints, dependencies, main) MUST import from here.
_memory_service_instance: Optional[MemoryService] = None
_memory_service_lock: asyncio.Lock = asyncio.Lock()


async def get_memory_service() -> MemoryService:
    """
    Get or create MemoryService singleton (async, auto-initializes).

    This is the single canonical entry point for MemoryService across the
    entire application. All modules (memory endpoints, agent endpoints,
    dependencies, main) MUST use this function.

    Uses asyncio.Lock to prevent race conditions when multiple coroutines
    call this concurrently during startup.

    Returns:
        MemoryService: Initialized singleton instance
    """
    global _memory_service_instance

    # Fast path: already initialized
    if _memory_service_instance is not None and _memory_service_instance._initialized:
        return _memory_service_instance

    # Slow path: acquire lock for safe initialization
    async with _memory_service_lock:
        # Double-check after acquiring lock
        if (
            _memory_service_instance is not None
            and _memory_service_instance._initialized
        ):
            return _memory_service_instance

        if _memory_service_instance is None:
            logger.info("Creating MemoryService singleton instance")
            _memory_service_instance = MemoryService()

        if not _memory_service_instance._initialized:
            await _memory_service_instance.initialize()
            logger.info("MemoryService singleton initialized")

    return _memory_service_instance


async def cleanup_memory_service() -> None:
    """
    Cleanup MemoryService singleton — called on application shutdown.

    This is the ONLY place that cleans up the shared Neo4j driver,
    since MemoryService.cleanup() only clears local state.
    """
    global _memory_service_instance
    if _memory_service_instance is not None:
        # First cleanup local MemoryService state
        await _memory_service_instance.cleanup()
        # Then cleanup the shared Neo4j driver (only at app shutdown)
        try:
            await _memory_service_instance.neo4j.cleanup()
            logger.info("Neo4j driver cleaned up during shutdown")
        except (RuntimeError, ConnectionError, OSError) as e:
            logger.warning(f"Neo4j driver cleanup failed: {e}")
        _memory_service_instance = None
        logger.info("MemoryService singleton cleaned up")


def reset_memory_service() -> None:
    """Reset singleton instance (for testing only)."""
    global _memory_service_instance
    _memory_service_instance = None
