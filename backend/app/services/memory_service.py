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
import unicodedata
import uuid

# 终验审查红旗修复 (2026-07-24): _search_neo4j_fulltext 的 except 元组引用
# neo4j.exceptions.* 但模块从未 import — Tier2 任意异常时 except 求值先抛
# NameError, 异常处理器自己炸掉整条检索链 (「Lucene ParseException 修复」
# 自 MVP-α 起从未真正工作过)。全库 F821 扫描抓到。
import neo4j.exceptions  # noqa: E402

import structlog
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from cachetools import TTLCache

from app.clients.neo4j_client import Neo4jClient, get_neo4j_client
from app.config import settings
from app.core.decision_tracker import log_decision
from app.core.failed_writes_constants import FAILED_WRITES_FILE, failed_writes_lock

if TYPE_CHECKING:  # CARD-G4-2: 仅类型注解需要, 运行时走函数体内延迟 import
    from app.models.service_status import StatusedResult
from app.core.subject_config import (
    build_vault_group_id,
    extract_canvas_name,
    extract_subject_from_canvas_path,
)
from app.services.episode_worker import EpisodeTask, get_episode_worker
from app.graphiti.entity_types import CANVAS_ENTITY_TYPES, CANVAS_EDGE_TYPES

logger = structlog.get_logger(__name__)


def _neo4j_backend_failure(client) -> Optional[str]:
    """CARD-G4-2 / Codex round-1 BLOCKER-1: 探测「不抛异常的后端故障」。

    生产 ``Neo4jClient`` 在初始化失败或运行中降级后进入 **JSON_FALLBACK**
    模式: ``initialized`` 仍为 True、Cypher 正常返回 ``[]``、不抛任何异常。
    只靠 try/except 与 ``stats["initialized"]`` 检测, 这类故障会被四态
    误报成 ok/empty —— 正是本卡要根治的「故障假装空结果」。

    Returns:
        故障原因 (str) 或 None (后端健康)。
    """
    # ⚠️ 探针只对**能确证的故障**报警 —— 判据一律要求真实的 bool/str 类型。
    # 理由: 测试里的 MagicMock 属性是 truthy 的 Mock 对象而非 True, 用
    # truthy 判断会把每个未显式声明健康的 mock 都判成降级 (实测让 11 条
    # 既有测试变红)。「看不懂这个客户端」≠「这个客户端坏了」——
    # 后者才该 fail-closed, 前者只能放行, 否则探针自己变成假警报源。
    try:
        if getattr(client, "is_fallback_mode", False) is True:
            return "neo4j: JSON_FALLBACK mode (主库不可用, 返回值为本地兜底而非真实数据)"
        stats = getattr(client, "stats", None)
        if isinstance(stats, dict):
            if stats.get("initialized") is False:
                return "neo4j: client not initialized"
            health = stats.get("health_status")
            if isinstance(health, str) and health.lower() not in (
                "healthy",
                "ok",
                "up",
            ):
                return f"neo4j: health_status={health}"
    except Exception as e:  # noqa: BLE001 — 探测失败不得炸主链
        return f"neo4j: health probe failed ({type(e).__name__}: {e})"
    return None


def _vault_scoped_group_id(subject=None, canvas_name=None) -> str:
    """G-DEFAULT 根治 (2026-07-10, D16/C-3): 写侧统一 vault:<vault_id>[:<二级>] 前缀.

    取代本模块此前直接调 Story 1.9 legacy build_group_id(subject[, canvas])——
    legacy 格式让所有 vault 的记忆塌进同一 subject 桶(2026-07-10 cypher 实测:
    图中 88 节点 group_id 全为 default/cs188/test fallback, 零真实 vault 身份)。
    二级优先 canvas_name(D16 vault:<id>:<canvas> 规约), 无 canvas 时用 subject。

    CARD-G2-2 契约反转 (2026-08-28, C6 docstring :36-41 预告的 deliberate
    red test): vault 来源改经 vault_scope.current_vault_id() —— per-request
    作用域 (ContextVar) 优先, 未注入时回落进程 active vault。根治 C6 记录的
    "进程级单 active vault"双真相源: endpoint 409 门保证请求路径下二者一致,
    唯 hook-cwd 合法例外允许 per-request vault 与 active vault 不同。
    """
    from app.core.vault_scope import current_vault_id

    vault_id = current_vault_id()
    if canvas_name:
        return build_vault_group_id(vault_id, canvas_path=canvas_name)
    if subject:
        return build_vault_group_id(vault_id, subject_id=subject)
    return build_vault_group_id(vault_id)


# Story 31.5: Cache TTL for score history queries (30 seconds)
SCORE_HISTORY_CACHE_TTL = 30

#: CARD-G4-1a: vault 子组枚举的分页大小与硬上限 (Codex round-1 M-2)。
#: 分页保证"全部子组可见"与 Cypher/内存侧前缀语义等价; 硬上限只是防失控,
#: 真撞到就如实上报 degraded, 不静默按收窄面检索。
_SUBGROUP_PAGE_SIZE = 500
_SUBGROUP_HARD_CAP = 5000

# Story 38.6: FAILED_WRITES_FILE and failed_writes_lock imported from
# app.core.failed_writes_constants (shared with agent_service.py)


# Story 30.10 AC-30.10.1: Deterministic episode ID generation
def _generate_deterministic_episode_id(user_id: str, canvas_path: str, node_id: str, concept: str) -> str:
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
def _generate_batch_episode_id(canvas_path: str, node_id: str, event_type: str, timestamp: str) -> str:
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
    # CARD-G4-2 (2026-08-28): 加性可选字段 (带默认值, 存量构造零改动)。
    # 空 scores 此前无法区分「这个概念还没考过」与「Neo4j 挂了」。
    status: str = "ok"
    status_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "concept_id": self.concept_id,
            "canvas_name": self.canvas_name,
            "scores": self.scores,
            "timestamps": self.timestamps,
            "average": self.average,
            "sample_size": self.sample_size,
            "status": self.status,
            "status_reason": self.status_reason,
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
        self._score_history_cache: TTLCache = TTLCache(maxsize=_score_cache_maxsize, ttl=SCORE_HISTORY_CACHE_TTL)
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
            logger.info("[Epic 4] Skipping fulltext index creation: Neo4j not initialized")
            return

        # 批次4' R4 (MEM-FLYWHEEL): CJK analyzer — 中文 BM25 分词 (standard 单字
        # 切分致中文精度 -26pt)。IF NOT EXISTS 语义: 已有 cjk 版索引时跳过;
        # 全新库启动时直接建成 cjk 版 (与 scripts/rebuild_fulltext_cjk.cypher 一致)
        cypher = (
            "CREATE FULLTEXT INDEX episode_content IF NOT EXISTS "
            "FOR (n:EpisodicNode) ON EACH [n.content] "
            "OPTIONS {indexConfig: {`fulltext.analyzer`: 'cjk'}}"
        )
        try:
            await self.neo4j.run_query(cypher)
            logger.info("[Epic 4] Fulltext index 'episode_content' ensured on EpisodicNode.content")
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
                        # T1 统一 (2026-07-10): Neo4j 物理层存 `__` 格式, 恢复进
                        # 内存 cache 前转回 D16 冒号 — 否则 Tier 3 cache 过滤
                        # (冒号比较) 对 recovered episodes 恒不匹配。
                        from app.graphiti.group_id_compat import (
                            desanitize_group_id_from_graphiti,
                        )

                        episode = {
                            "episode_id": f"recovered-{idx}-{user_id or 'unknown'}-{record.get('concept_id') or 'unknown'}",
                            "user_id": user_id,
                            "concept": concept,
                            "concept_id": record.get("concept_id"),
                            "score": record.get("score"),
                            "timestamp": timestamp,
                            "group_id": desanitize_group_id_from_graphiti(record.get("group_id") or ""),
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
                logger.warning(f"MemoryService: Neo4j unavailable, starting with empty history ({e})")

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

    def enqueue_conversation_archive(
        self,
        *,
        session_id: str,
        conversation_text: str,
        group_id: str,
    ) -> bool:
        """M3 (2026-07-13): SessionEnd 会话归档 → 语义通道 (D6 非结构化材料)。

        对话全文经 worker add_episode 做 LLM 实体抽取; worker 在
        _process_episode 单点把 group 重定向到 __semantic 影子分组
        (M2 双图隔离), 本方法与调用方均无法指定主图 — 提示词被污染
        也没有通路碰到结构化主链。返回 True=已入队 (异步, 非已写入)。
        """
        return self._enqueue_episode(
            name=f"session-archive:{session_id[:16]}",
            episode_body=conversation_text,
            group_id=group_id,
            source_description="conversation-archive",
        )

    def _record_structured_outbox(self, entry: Dict[str, Any]) -> bool:
        """A7 (P2): 结构化写入彻底失败时立即落盘 outbox, 不静默丢数据。

        立即写 FAILED_WRITES_FILE (非等 shutdown flush) 抗进程崩溃。条目带
        kind='knowledge_entity' 判别符, recover_failed_writes 据此重放
        (重新走 record_knowledge_entity 的结构化写入, 此时 worker 通常已就绪)。

        注: callout/relation 的主要持久化是 frontmatter + 启动回填 (vault md 是
        真相源, backfill_vault 重建边), outbox 是非结构化材料/边界场景的兜底。
        返回 True=已落盘, False=连兜底也失败(真数据丢失风险, 已 error 日志)。
        """
        try:
            FAILED_WRITES_FILE.parent.mkdir(parents=True, exist_ok=True)
            with failed_writes_lock:
                with open(FAILED_WRITES_FILE, "a", encoding="utf-8") as f:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            return True
        except OSError as e:
            logger.error("[A7] outbox 落盘失败 (数据可能丢失): %s", e)
            return False

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
        episode_id = _generate_deterministic_episode_id(user_id, canvas_path, node_id, concept)

        # ✅ AC-30.8.2: Auto-infer subject from canvas_path if not provided
        inferred_subject = subject or extract_subject_from_canvas_path(canvas_path)

        # ✅ AC-30.8.1: Build group_id for namespace isolation (Epic 6: canvas-scoped)
        canvas_name = extract_canvas_name(canvas_path)
        group_id = _vault_scoped_group_id(inferred_subject, canvas_name=canvas_name)

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
                (i for i, ep in enumerate(self._episodes) if ep.get("episode_id") == episode_id),
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
            group_id = _vault_scoped_group_id(inferred_subject, canvas_name=c_name)
        elif subject:
            group_id = _vault_scoped_group_id(subject)
        else:
            # CARD-G4-1a (2026-08-30): 此处曾落 None —— Neo4j 侧 `if group_id`
            # 分支不成立 = 不拼 group 过滤 = 全库扫描 (读契约 R4 违规, G2-2
            # Codex BLOCKER-5 移交项)。改为 fail-closed 解析当前 vault 根组;
            # 根组经**前缀语义**可见其全部二级子组 (canvas/semantic/punycode),
            # 因此封堵不缩召回。
            from app.core.vault_scope import require_read_group

            group_id = require_read_group(
                context="memory_service.get_learning_history"
            )

        # ✅ Story 31.A.2 AC-31.A.2.1: Query from Neo4j first (replaces memory-only read)
        episodes = []
        # CARD-G4-2 四态信号 — BLOCKER-1: 探针先行, 覆盖不抛异常的降级
        retrieval_failure: Optional[str] = _neo4j_backend_failure(self.neo4j)
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
            logger.debug(f"Retrieved {len(episodes)} episodes from Neo4j for user {user_id}")
        except asyncio.CancelledError:
            raise
        except Exception as e:  # noqa: BLE001 — HIGH-6: 依赖异常族全覆盖
            # ✅ Story 31.A.2: Fallback to memory if Neo4j fails
            # CARD-G4-2 (2026-08-28): 降级不再静默 — 记录原因, 出口带四态键。
            logger.warning(f"Neo4j query failed, falling back to memory: {e}")
            retrieval_failure = f"neo4j learning history: {type(e).__name__}: {e}"

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
        #
        # CARD-G4-1a (2026-08-30): 等值比较 → 前缀语义。上面 else 分支不再落
        # None 后, group_id 恒非空; 若仍用等值, vault 根组读会把落在 canvas /
        # semantic / punycode 二级子组的 episode 全部误挡 (现网存量恰好全在
        # punycode 子组 → "学习历史突然空了")。group_in_read_scope 与 Cypher
        # 侧 read_group_filter 是同一套可见性规则, 保证 Neo4j 可用与降级两条
        # 路径的隔离结果一致。canvas 级读 (scope 已是子组) 仍只见自己, 兄弟
        # 白板不可见。
        from app.core.vault_scope import group_in_read_scope

        memory_episodes = [
            e for e in memory_episodes if group_in_read_scope(e.get("group_id"), group_id)
        ]

        # Apply date filters to in-memory episodes
        # S34 Bug fix #3: Normalize both sides to str for consistent comparison
        # (Neo4j returns offset-aware DateTime, in-memory uses ISO strings)
        if start_date:
            start_str = str(start_date.isoformat()) if hasattr(start_date, "isoformat") else str(start_date)
            memory_episodes = [e for e in memory_episodes if str(e.get("timestamp", "")) >= start_str]
        if end_date:
            end_str = str(end_date.isoformat()) if hasattr(end_date, "isoformat") else str(end_date)
            memory_episodes = [e for e in memory_episodes if str(e.get("timestamp", "")) <= end_str]

        # Apply concept filter
        if concept:
            concept_lower = concept.lower()
            memory_episodes = [e for e in memory_episodes if concept_lower in e.get("concept", "").lower()]

        # Apply subject filter
        if subject:
            subject_lower = subject.lower()
            memory_episodes = [e for e in memory_episodes if subject_lower in e.get("subject", "").lower()]

        # Merge: deduplicate by (node_id, timestamp), prefer Neo4j (persistent)
        if memory_episodes:
            existing_keys = {(e.get("node_id", ""), e.get("timestamp", "")) for e in episodes}
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
                failed_scores = [fs for fs in failed_scores if fs.get("user_id", "") == user_id]
            # Bug fix #2: Apply same date filters as memory_episodes
            if start_date:
                s_str = str(start_date.isoformat()) if hasattr(start_date, "isoformat") else str(start_date)
                failed_scores = [fs for fs in failed_scores if str(fs.get("timestamp", "")) >= s_str]
            if end_date:
                e_str = str(end_date.isoformat()) if hasattr(end_date, "isoformat") else str(end_date)
                failed_scores = [fs for fs in failed_scores if str(fs.get("timestamp", "")) <= e_str]
            # FR-KG-04 fix: Apply group_id filter to fallback failed_scores for
            # canvas-scoped isolation (Story 30.8 AC-30.8.1). Derive group_id from
            # canvas_name + inferred subject — failed_writes.jsonl historical entries
            # don't carry group_id directly, so we reconstruct it the same way the
            # write path does.
            # CARD-G4-1a (2026-08-30): 与内存 episode 同修 —— 重建出来的 group
            # 恒是 canvas 级子组 (vault:v:board), 而本次读的 scope 可能是 vault
            # 根组, 等值比较会把 fallback 条目全部误挡 (Story 38.6 AC-4 "用户
            # 永远看不到断档"的保证在根组读下失效)。改用同一套前缀语义。
            def _derive_group_id(fs: Dict[str, Any]) -> str:
                canvas_name_field = fs.get("canvas_name", "") or ""
                if not canvas_name_field:
                    return ""
                inferred_subj = subject or extract_subject_from_canvas_path(canvas_name_field)
                cn_only = extract_canvas_name(canvas_name_field)
                return _vault_scoped_group_id(inferred_subj, canvas_name=cn_only)

            failed_scores = [
                fs for fs in failed_scores if group_in_read_scope(_derive_group_id(fs), group_id)
            ]
            # Deduplicate: only include fallback entries not already in episodes
            existing_keys = {(e.get("node_id", ""), e.get("timestamp", "")) for e in episodes}
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

        # CARD-G4-2 (2026-08-28): 加性四态键 — 原契约键 byte 级不动。
        # Neo4j 失败但内存兜底接管 = degraded (结果不完整, 不是"没有");
        # 正常路径按有无命中给 ok / empty。
        from app.models.service_status import ServiceStatus

        if retrieval_failure:
            retrieval_status = ServiceStatus.DEGRADED.value
        elif total:
            retrieval_status = ServiceStatus.OK.value
        else:
            retrieval_status = ServiceStatus.EMPTY.value

        return {
            "items": paginated,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size if total > 0 else 0,
            "retrieval_status": retrieval_status,
            "retrieval_status_reason": retrieval_failure,
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

        # CARD-G4-2 Codex round-1 BLOCKER-4: 本读路径此前完全无状态 —
        # 后端降级时空 timeline 与「这个概念没学过」无法分辨。
        retrieval_failure: Optional[str] = _neo4j_backend_failure(self.neo4j)

        # Get history from Neo4j
        try:
            history = await self.neo4j.get_concept_history(
                concept_id=concept_id, user_id=user_id, limit=limit
            )
        except Exception as e:  # noqa: BLE001 — 故障如实上报, 不伪装空历史
            logger.error(f"Concept history query failed for {concept_id}: {e}")
            history = []
            retrieval_failure = f"{type(e).__name__}: {e}"

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

        # CARD-G4-2: 加性四态键 (原有键 byte 级不动)
        from app.models.service_status import ServiceStatus

        if retrieval_failure:
            # 后端不可信 → 空 timeline 不是「没学过」
            status = (
                ServiceStatus.DEGRADED.value if timeline else ServiceStatus.UNAVAILABLE.value
            )
        elif timeline:
            status = ServiceStatus.OK.value
        else:
            status = ServiceStatus.EMPTY.value

        return {
            "concept_id": concept_id,
            "timeline": timeline,
            "score_trend": score_trend,
            "total_reviews": len(timeline),
            "retrieval_status": status,
            "retrieval_status_reason": retrieval_failure,
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
        # CARD-G4-2 / Codex round-1 BLOCKER-5 (缓存面): 键必须含 vault —
        # 否则两个 vault 的同名 concept+canvas 共用一条 30s 缓存, A vault
        # 的分数会被 B vault 读到。
        from app.core.vault_scope import current_vault_id

        cache_key = f"{current_vault_id()}:{concept_id}:{canvas_name}:{limit}"

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

        # BLOCKER-1: 后端处于 JSON_FALLBACK / 未初始化时, 查询会静默返回
        # 空列表而不抛异常 —— 必须先探测, 否则 unavailable 被误报成 empty。
        backend_failure = _neo4j_backend_failure(self.neo4j)
        if backend_failure:
            logger.error(
                f"Score history backend unusable for {concept_id}: {backend_failure}"
            )
            return ScoreHistoryResponse(
                concept_id=concept_id,
                canvas_name=canvas_name,
                scores=[],
                timestamps=[],
                average=0.0,
                sample_size=0,
                status="unavailable",
                status_reason=backend_failure,
            )

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
                # CARD-G4-2: 真空是数据事实 (empty, 无 reason), 不是故障
                status="ok" if scores else "empty",
            )

            # Store in cache (TTLCache handles expiration automatically)
            self._score_history_cache[cache_key] = result

            logger.debug(f"Score history for {concept_id}: {len(scores)} records, avg={average:.2f}")

            return result

        except asyncio.CancelledError:
            raise
        except Exception as e:  # noqa: BLE001 — HIGH-6: 依赖异常族全覆盖
            logger.error(f"Failed to get score history for {concept_id}: {e}")
            # CARD-G4-2 (2026-08-28): 故障不再假装空历史 — 返回 unavailable
            # 带 reason。**不入缓存** (否则恢复后 30s 内仍报不可用)。
            return ScoreHistoryResponse(
                concept_id=concept_id,
                canvas_name=canvas_name,
                scores=[],
                timestamps=[],
                average=0.0,
                sample_size=0,
                status="unavailable",
                status_reason=f"{type(e).__name__}: {e}",
            )

    async def get_review_suggestions_with_status(
        self,
        user_id: str,
        limit: int = 10,
        subject: Optional[str] = None,
        canvas_path: Optional[str] = None,
    ) -> "StatusedResult":
        """
        获取复习建议 (基于艾宾浩斯遗忘曲线) — CARD-G4-2 四态版本

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
            group_id = _vault_scoped_group_id(inferred_subject, canvas_name=c_name)
        elif subject:
            group_id = _vault_scoped_group_id(subject)
        else:
            # CARD-G4-1a (2026-08-30): 同 get_learning_history —— 此处落 None
            # 会走 neo4j_client.get_review_suggestions 的**无 group 分支**
            # (审计 §5 #3, R4:violation), 把全库所有 vault 的待复习概念端给
            # 用户。改 fail-closed 解析 vault 根组 + 客户端前缀过滤。
            from app.core.vault_scope import require_read_group

            group_id = require_read_group(
                context="memory_service.get_review_suggestions_with_status"
            )

        # CARD-G4-2 Codex round-1 BLOCKER-4: 卡文点名的 suggestions 读路径 —
        # 后端降级/异常时此前静默返回空, 与「没有待复习概念」不可分辨。
        from app.models.service_status import StatusedResult

        backend_failure = _neo4j_backend_failure(self.neo4j)
        if backend_failure:
            return StatusedResult.unavailable(
                f"review suggestions unusable — {backend_failure}"
            )
        try:
            suggestions = await self.neo4j.get_review_suggestions(
                user_id=user_id, limit=limit, group_id=group_id
            )
        except Exception as e:  # noqa: BLE001
            logger.error(f"Review suggestions query failed for {user_id}: {e}")
            return StatusedResult.unavailable(f"{type(e).__name__}: {e}")

        logger.debug(f"Retrieved {len(suggestions or [])} review suggestions for user {user_id} (subject={subject})")
        return StatusedResult.from_items(list(suggestions or []))

    async def get_review_suggestions(
        self,
        user_id: str,
        limit: int = 10,
        subject: Optional[str] = None,
        canvas_path: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """兼容委托 — 保 list 契约 (CARD-G4-2 兼容铁律)。

        新代码应改用 ``get_review_suggestions_with_status()``: 本方法的
        空 list 无法区分「没有待复习概念」与「Neo4j 挂了」。
        """
        result = await self.get_review_suggestions_with_status(
            user_id, limit=limit, subject=subject, canvas_path=canvas_path
        )
        return result.items

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
        await self.neo4j.create_learning_relationship(user_id=user_id, concept=concept, score=score, group_id=group_id)

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
        error_count = sum(1 for layer in layers.values() if layer.get("status") == "error")

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

    async def record_batch_learning_events(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
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
                    # CARD-G4-1a (2026-08-30): 内存 episode 必须自带归属。读侧
                    # 封堵后作用域恒非空, 无 group 的条目在**任何** vault 视角
                    # 下都不可见 (fail-closed) —— 这两条 batch/temporal 写路径
                    # 此前不落 group, 于是 Tier 3 内存检索会静默丢掉它们。
                    # 归属按 canvas 推导, 与 get_learning_history 的 canvas 级
                    # 读作用域同构 (同一个白板写进去、同一个白板读得出来)。
                    "group_id": _vault_scoped_group_id(
                        extract_subject_from_canvas_path(event["canvas_path"]),
                        canvas_name=extract_canvas_name(event["canvas_path"]),
                    ),
                }

                # Story 30.10 AC-30.10.3: Dedup batch episodes
                # Fix C4: skip-if-exists to preserve score history
                existing_idx = next(
                    (i for i, ep in enumerate(self._episodes) if ep.get("episode_id") == episode_id),
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
                logger.warning(f"Batch Neo4j write: {len(neo4j_errors)} errors (non-blocking)")
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
                group_id=_vault_scoped_group_id(inferred_subject, canvas_name=c_name),
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
        _from_recovery: bool = False,
    ) -> Dict[str, Any]:
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
            dict: {"entity_id": str, "status": "written"|"enqueued"|"degraded"}.
            A7 (P2): status 诚实反映持久化结果 — written=结构化写入图,
            enqueued=进语义队列, degraded=worker 未就绪已落 outbox 待重放
            (调用方据此报告, 不再无条件 saved=True)。

            _from_recovery=True 时不重落 outbox (recover 重放路径, 避免重复堆积)。
        """
        if not self._initialized:
            await self.initialize()

        entity_id = f"{event_type}-{uuid.uuid4().hex[:16]}"
        # CARD-G2-2 (2026-08-28): 调用方未传 group_id 时经统一读取口取当前
        # 作用域 (闭合 C6 docstring 记录的 record_knowledge_entity 兜底缺口)。
        from app.core.vault_scope import current_group_id

        resolved_group_id = group_id or current_group_id()
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
                    write_relation_reason,
                )

                # P3 (A4): valid_at = 真实源事件时间(客户端 source_timestamp =
                # 用户操作时刻), 非 now(=系统入图时间)。解析失败退 now。
                occurred = datetime.now(timezone.utc)
                _src_ts = meta.get("source_timestamp")
                if _src_ts:
                    try:
                        occurred = datetime.fromisoformat(str(_src_ts).replace("Z", "+00:00"))
                    except (ValueError, TypeError):
                        pass
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
                            callout_type=callout_type or ("tip" if event_type == "learning_tip" else "note"),
                            text=meta.get("content") or content,
                            occurred_at=occurred,
                            understanding=understanding or None,
                            # P0 (A+-prime): 稳定身份, 即时上报与停笔回填同 id
                            annotation_id=meta.get("annotation_id") or None,
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
                    elif event_type in ("node_derived", "wikilink_added"):
                        # P4 (X1): 派生关系原因实时入图 (非启动回填)。node_id_for_exam =
                        # 持有 frontmatter relationships 的派生节点(出边源), target = 源节点。
                        # 走 Graphiti-native write_relation_reason, 不走 CANVAS_EDGE 投影。
                        target = meta.get("target_node_id", "")
                        if target:
                            await write_relation_reason(
                                graphiti.driver,
                                graphiti.embedder,
                                source_node_id=node_id_for_exam,
                                target_node_id=target,
                                group_id=resolved_group_id,
                                relation_type=meta.get("relation_type"),
                                reason=meta.get("reason") or content,
                                occurred_at=occurred,
                            )
                            structured_written = True
                except Exception as e:  # noqa: BLE001 — 结构化失败退语义队列保数据
                    logger.warning(
                        f"[Graphiti-native] structured write failed for {event_type} (fallback to episode queue): {e}"
                    )
                    structured_written = False

        status = "written"
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
            enqueued = self._enqueue_episode(
                name=f"{event_type}:{meta.get('title', content[:40])}",
                episode_body=content,
                group_id=resolved_group_id,
                source_description=canonical_source_desc,
                entity_types=CANVAS_ENTITY_TYPES,
                edge_types=CANVAS_EDGE_TYPES,
            )
            if enqueued:
                status = "enqueued"
            else:
                # A7 (P2): worker 未就绪 → 既不入图也未入队。诚实标 degraded +
                # 落 outbox 待重放, 不再静默返回成功。
                status = "degraded"
                if not _from_recovery:
                    self._record_structured_outbox(
                        {
                            "kind": "knowledge_entity",
                            "event_type": event_type,
                            "content": content,
                            "metadata": meta,
                            "group_id": resolved_group_id,
                            "timestamp": datetime.now().isoformat(),
                        }
                    )
                    logger.warning(
                        "[A7] %s 未入图(worker未就绪), 已落 outbox 待重放: id=%s node=%s",
                        event_type,
                        entity_id,
                        meta.get("node_id", ""),
                    )

        logger.info(f"[Story 3.6] Recorded {event_type}: id={entity_id} group={resolved_group_id} status={status}")
        return {"entity_id": entity_id, "status": status}

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
            from app.graphiti.group_id_compat import to_physical_group_id

            client = get_neo4j_client()
            # T1 统一 (2026-07-10): 物理层单一 `__` 格式, 双格式 OR 查询退役
            # CARD-G2-2 (2026-08-28): 兜底改统一读取口 (与 tips 写侧同 scope 成对)
            from app.core.vault_scope import current_group_id

            physical_group_id = to_physical_group_id(group_id or current_group_id())

            # P0-7 (2026-05-14): Graphiti 不持久化 metadata 到 EpisodicNode。
            # tips.py batch_sync 把 content_hash 内嵌为 [hash:abc123] 后缀写到
            # content 字段，这里用 CONTAINS 匹配前 16 hex chars。
            hash_marker = f"[hash:{content_hash[:16]}]"
            query = """
            MATCH (e:Episodic)
            WHERE e.group_id = $group_id
              AND e.source_description = 'callout-annotation-record'
              AND e.content CONTAINS $hash_marker
            RETURN count(e) AS cnt
            LIMIT 1
            """
            records = await client.run_query(
                query,
                group_id=physical_group_id,
                hash_marker=hash_marker,
            )
            for record in records or []:
                data = record if isinstance(record, dict) else record.data()
                cnt = data.get("cnt", 0)
                if cnt > 0:
                    return True
            return False
        except (RuntimeError, ConnectionError, asyncio.TimeoutError) as e:
            logger.debug(f"[Story 2.4 batch] find_episode_by_content_hash failed (non-fatal): {e}")
            # 失败时 fail-open — 允许 batch 继续（重复同步比丢失数据更可接受）
            return False

    # Search config recipe mapping: string name → SearchConfig object
    _SEARCH_RECIPES: Dict[str, Any] = {}  # populated lazily to avoid import-time side effects

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

                # 批次1'④ (MEM-FLYWHEEL): MMR 配方注册 — Graphiti 白送的
                # 去重配方此前闲置 (审查「三个已付钱零收益」之三)
                from graphiti_core.search.search_config_recipes import (
                    COMBINED_HYBRID_SEARCH_MMR,
                    EDGE_HYBRID_SEARCH_MMR,
                    NODE_HYBRID_SEARCH_MMR,
                )

                cls._SEARCH_RECIPES = {
                    "combined_rrf": COMBINED_HYBRID_SEARCH_RRF,
                    "combined_cross_encoder": COMBINED_HYBRID_SEARCH_CROSS_ENCODER,
                    "combined_mmr": COMBINED_HYBRID_SEARCH_MMR,
                    "edge_cross_encoder": EDGE_HYBRID_SEARCH_CROSS_ENCODER,
                    "edge_rrf": EDGE_HYBRID_SEARCH_RRF,
                    "edge_mmr": EDGE_HYBRID_SEARCH_MMR,
                    "node_rrf": NODE_HYBRID_SEARCH_RRF,
                    "node_mmr": NODE_HYBRID_SEARCH_MMR,
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
        fail_sink: Optional[List[str]] = None,
        coverage_sink: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Tier 1: Search via graphiti-core search_() with advanced recipes.

        Args:
            query: Search query string
            group_id: Optional group namespace for filtering
            limit: Max results to return
            search_config: Recipe name — one of 'combined_rrf', 'combined_cross_encoder',
                          'edge_cross_encoder', 'edge_rrf', 'node_rrf'
            search_filter: Optional SearchFilters instance for date/label/type filtering
            fail_sink: CARD-G4-2 (2026-08-28) 加性失败收集器 — 本 Tier 无法
                服务时把原因 append 进去, 让 search_memories 汇聚层区分
                「真空结果」与「这一层挂了」。**返回类型保持 list 不变**
                (存量测试直接断言 list, 契约冻结)。

        Returns:
            List of result dicts with 'relevance_score' from reranker scores.
            空 list 不代表无数据 — 须同时看 fail_sink。
        """

        def _fail(reason: str) -> List[Dict[str, Any]]:
            if fail_sink is not None:
                fail_sink.append(reason)
            return list()

        worker = get_episode_worker()
        if not worker.is_ready or worker._graphiti is None:
            return _fail("graphiti: episode worker not ready")  # not initialized yet

        # Resolve search config recipe
        recipes = self._get_search_recipes()
        config_obj = recipes.get(search_config)
        if config_obj is None:
            logger.warning(f"Unknown search config '{search_config}', falling back to combined_rrf")
            config_obj = recipes.get("combined_rrf")

        # If recipes are unavailable (import failed), fall back to old search()
        if config_obj is None:
            return await self._search_graphiti_legacy(
                query, group_id, limit, fail_sink=fail_sink
            )

        try:
            # Override the limit in config
            from graphiti_core.search.search_config import SearchConfig

            # Create a copy with updated limit
            config_with_limit = config_obj.model_copy(update={"limit": limit})

            # P0-5 (2026-05-14): sanitize group_id at Graphiti boundary
            # M2 双图检索 (2026-07-13, 路线图 v2): 主图 + 语义影子图同查 —
            # 影子图只由 LLM 抽取通道写入 (semantic_group_id 服务端固定),
            # 读侧扩展让对话上下文能召回蒸馏产物的隐式关系 fact。
            from app.graphiti.group_id_compat import (
                sanitize_group_id_for_graphiti,
                semantic_group_id,
            )

            # CARD-G4-1a (2026-08-30): 此前 group_id 为空 → _search_groups=None
            # → graphiti search_ 不带 group_ids = **搜全部 vault**。改 fail-closed
            # 必填解析 (读契约 R4)。
            from app.core.vault_scope import require_read_group

            _gid_phys = sanitize_group_id_for_graphiti(
                require_read_group(group_id, context="memory_service._search_graphiti")
            )
            # 批次1'④ (MEM-FLYWHEEL): punycode 白板级子组并入检索 — 中文白板名
            # 转码组 (vault__x__xn--*) 曾不在搜索范围, 组内 fact 逐字查不到
            # (审查实锤: q1 完美中文答案搁浅在 punycode 组)
            # —— 这正是 Tier 1 侧的"前缀语义"实现: 组集合 = 本组 + 影子组 +
            # 全部 `本组__*` 子组, 与 read_group_filter 的可见面等价。
            _search_groups = [_gid_phys, semantic_group_id(_gid_phys)]
            _search_groups += await self._expand_vault_subgroups(
                _gid_phys, fail_sink=coverage_sink
            )
            search_kwargs: Dict[str, Any] = {
                "query": query,
                "config": config_with_limit,
                "group_ids": _search_groups,
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
                        "content": getattr(node, "summary", "") or getattr(node, "name", ""),
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
        except asyncio.CancelledError:
            raise  # HIGH-6: 取消语义必须保留, 不得吞成「检索失败」
        except Exception as e:  # noqa: BLE001 — HIGH-6: 依赖边界统一归一异常
            # 白名单式捕获会漏掉 neo4j.ServiceUnavailable / SessionExpired /
            # openai.APIConnectionError 等真实依赖异常, 让它们穿透四态方法。
            logger.warning(f"Graphiti search_() failed or timed out: {e}")
            return _fail(f"graphiti: {type(e).__name__}: {e}")

    async def _search_graphiti_legacy(
        self,
        query: str,
        group_id: Optional[str] = None,
        limit: int = 20,
        fail_sink: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Legacy fallback: search via graphiti.search() when recipes unavailable.

        CARD-G4-2: fail_sink 与 _search_graphiti 同契约 (加性, list 返回不变)。
        """

        def _fail(reason: str) -> List[Dict[str, Any]]:
            if fail_sink is not None:
                fail_sink.append(reason)
            return list()

        worker = get_episode_worker()
        if not worker.is_ready or worker._graphiti is None:
            return _fail("graphiti(legacy): episode worker not ready")
        try:
            # P0-5 (2026-05-14): sanitize group_id at Graphiti boundary
            # M2 双图检索 (2026-07-13): legacy 路径与 Tier1 保持同构 — 主图+影子图
            from app.graphiti.group_id_compat import (
                sanitize_group_id_for_graphiti,
                semantic_group_id,
            )

            # CARD-G4-1a: legacy 路径与 Tier 1 同修 —— 空 group 时 group_ids=None
            # 同样是全 vault 搜索面 (它是 recipe 不可用时的实际生产路径)。
            from app.core.vault_scope import require_read_group

            _gid_phys = sanitize_group_id_for_graphiti(
                require_read_group(
                    group_id, context="memory_service._search_graphiti_legacy"
                )
            )
            _legacy_groups = [_gid_phys, semantic_group_id(_gid_phys)]
            _legacy_groups += await self._expand_vault_subgroups(_gid_phys)
            results = await asyncio.wait_for(
                worker._graphiti.search(
                    query=query,
                    group_ids=_legacy_groups,
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
        except asyncio.CancelledError:
            raise
        except Exception as e:  # noqa: BLE001 — HIGH-6: 同上, 依赖边界归一
            logger.warning(f"Graphiti legacy search failed or timed out: {e}")
            return _fail(f"graphiti(legacy): {type(e).__name__}: {e}")

    #: 批次1'④: 白板级子组枚举缓存 {前缀: (过期时间戳, 组列表)}
    _subgroup_cache: Dict[str, Any] = {}

    async def _expand_vault_subgroups(
        self, gid_phys: str, fail_sink: Optional[List[str]] = None
    ) -> List[str]:
        """枚举 vault 物理组前缀下的白板级子组 (批次1'④, MEM-FLYWHEEL)。

        中文白板名经 punycode 转码后落在 vault__x__xn--* 子组; 此前搜索只查
        [vault 组, semantic 影子组], punycode 组内 fact 逐字查不到 (2026-07-22
        对抗审查实锤)。5 分钟 TTL 缓存; Neo4j 不可用时静默返回空 — 只影响
        扩展面, 不炸主检索。
        """
        import time as _time

        prefix = gid_phys + "__"
        backend_failure = _neo4j_backend_failure(self.neo4j)
        if backend_failure:
            # BLOCKER-1: 降级模式下枚举恒空 — 不缓存, 且如实记入 fail_sink
            if fail_sink is not None:
                fail_sink.append(f"subgroup enumeration unusable — {backend_failure}")
            return []
        cached = self._subgroup_cache.get(prefix)
        if cached and cached[0] > _time.time():
            return cached[1]
        groups: List[str] = []
        try:
            # CARD-G4-1a / Codex round-1 M-2 (2026-08-30): 原实现是
            # `RETURN DISTINCT ... LIMIT 50` —— **无 ORDER BY 的截断**。一个
            # vault 超过 50 个子组 (白板 + 各自的 semantic 影子组 + punycode)
            # 时, 第 51 个之后进不进搜索面是不确定的, 于是 Graphiti 侧的"全部
            # 子组可见"与 Cypher / 内存侧的前缀语义**不等价**, 表现为根组搜索
            # 随机漏召回。改为: 确定性排序 + 分页取全量; 真的撞到硬上限才截断,
            # 且如实记入 fail_sink (= 覆盖面收窄 → degraded, 不假装完整)。
            page_size = _SUBGROUP_PAGE_SIZE
            offset = 0
            truncated = False
            while True:
                records = await self.neo4j.run_query(
                    "MATCH (n) WHERE n.group_id STARTS WITH $prefix "
                    "RETURN DISTINCT n.group_id AS gid "
                    "ORDER BY gid SKIP $offset LIMIT $limit",
                    prefix=prefix,
                    offset=offset,
                    limit=page_size,
                )
                page = []
                for rec in records or []:
                    data = rec if isinstance(rec, dict) else rec.data()
                    gid = str(data.get("gid") or "")
                    if gid:
                        page.append(gid)
                groups.extend(page)
                if len(page) < page_size:
                    break
                offset += page_size
                if len(groups) >= _SUBGROUP_HARD_CAP:
                    truncated = True
                    break
            if truncated and fail_sink is not None:
                fail_sink.append(
                    f"subgroup enumeration truncated at {_SUBGROUP_HARD_CAP} "
                    f"groups (prefix={prefix}) — 检索覆盖面不完整"
                )
        except Exception as e:  # noqa: BLE001 — 读侧扩展, 降级不炸
            logger.debug("[批次1'④] 子组枚举失败 (跳过扩展): %s", e)
            # CARD-G4-2 (2026-08-28): 枚举失败 = 检索面收窄 (punycode 白板级
            # 子组查不到), 属 degraded 信号。**不缓存**失败结果, 否则 5 分钟
            # 内持续按收窄面检索。
            if fail_sink is not None:
                fail_sink.append(f"subgroup enumeration: {type(e).__name__}: {e}")
            return groups
        self._subgroup_cache[prefix] = (_time.time() + 300, groups)
        return groups

    @staticmethod
    def _dedupe_by_text(results: List[Dict[str, Any]], ratio: float = 0.92) -> List[Dict[str, Any]]:
        """文本级近重去重 (批次1'④, MEM-FLYWHEEL): 保留分数最高条。

        dedup 只按 episode_id 收不掉不同 uuid 的近重边 (审查实测近重复率
        27%、5 对逐字节相同同屏)。入参须已按 relevance_score 降序 — 顺序
        遍历时后到的近重条即低分条, 直接丢弃。
        """
        import difflib

        kept: List[Dict[str, Any]] = []
        seen_norm: List[str] = []
        for r in results:
            text = "".join(
                unicodedata.normalize("NFKC", str(r.get("content") or r.get("name") or "")).casefold().split()
            )
            if text and any(difflib.SequenceMatcher(None, text, s).ratio() >= ratio for s in seen_norm):
                continue
            if text:
                seen_norm.append(text)
            kept.append(r)
        return kept

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
                if hasattr(engine, "_concept_cache") and isinstance(engine._concept_cache, dict):
                    concept_state = engine._concept_cache.get(concept_name)

                if concept_state is not None:
                    r_value = engine.get_retrievability(concept_state)
                    r_value = max(0.0, min(1.0, r_value))  # clamp to [0, 1]
                    result["fsrs_r_value"] = round(r_value, 4)

                    # Boost: low R-value concepts get higher final score
                    base_score = result.get("relevance_score", 0.0)
                    result["relevance_score"] = base_score * (1.0 + (1.0 - r_value) * 0.5)
            except (AttributeError, TypeError, ValueError, RuntimeError) as e:
                logger.debug(f"FSRS R-value lookup failed for '{concept_name}': {e}")
                continue

    async def _search_neo4j_fulltext(
        self,
        query: str,
        group_id: Optional[str] = None,
        limit: int = 20,
        fail_sink: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Tier 2: Search via Neo4j fulltext index for keyword matches.

        CARD-G4-2: fail_sink 加性收集失败原因 (list 返回契约不变)。
        """

        def _fail(reason: str) -> List[Dict[str, Any]]:
            if fail_sink is not None:
                fail_sink.append(reason)
            return list()

        # BLOCKER-1: 先探测「不抛异常的后端故障」(JSON_FALLBACK 等)
        backend_failure = _neo4j_backend_failure(self.neo4j)
        if backend_failure:
            return _fail(f"neo4j fulltext unusable — {backend_failure}")

        try:
            # 批次5' e2e 修正 (2026-07-24): group 过滤扩 semantic 影子组 —
            # worker 入图的 episode (批注直连/对话归档) 物理落 __semantic 组,
            # 旧单组过滤让 fulltext 兜底对这些内容恒空。
            #
            # CARD-G4-1a (2026-08-30): 删掉 group_ids 的 NULL 逃逸子句 ——
            # 那条子句让"没传 group"直接等于全库 fulltext 扫描 (读契约 R4)。
            # (逃逸子句原文见本卡 diff; 此处不复写字面量, 否则 grep 门误报。)
            # 同时把 `IN [本组, 影子组]` 白名单换成契约规范的**等值 OR 前缀**:
            # 白名单只枚举了两个组, vault 根组读依然看不到 canvas / punycode
            # 二级子组的 episode; 前缀语义一次覆盖全部 (影子组 vault__v__semantic
            # 本身也落在 `vault__v__` 前缀内)。
            from app.core.vault_scope import read_group_filter, read_scope_params

            cypher = f"""
            CALL db.index.fulltext.queryNodes('episode_content', $search_term)
            YIELD node, score
            WHERE {read_group_filter("node")}
            RETURN node, score
            ORDER BY score DESC
            LIMIT $limit
            """
            # MVP-α fix (2026-05-15): escape Lucene 特殊字符防 ParseException
            # 节点名含 ( ) [ ] 等会让 Lucene parser 抛 ClientError, 之前吞掉下游 fallback.
            import re

            safe_query = re.sub(r'([+\-!(){}\[\]^"~*?:\\/])', r"\\\1", query or "")
            safe_query = safe_query.replace("&&", r"\&\&").replace("||", r"\|\|")

            # T1 统一 (2026-07-10): episode 节点物理存 `__` 格式 — 冒号格式
            # 直查恒空 (Tier 2 断了两个月, Tier 1 降级时整条 search 静默空)。
            # read_scope_params 内部即 to_physical_group_id, 物理化保持不变。
            scope_params = read_scope_params(
                group_id, context="memory_service._search_neo4j_fulltext"
            )

            records = await self.neo4j.run_query(
                cypher,
                search_term=safe_query,
                limit=limit,
                **scope_params,
            )
            from app.graphiti.group_id_compat import (
                desanitize_group_id_from_graphiti,
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
                        # T1: 物理 `__` → 对外 D16 冒号 (与 Tier 1/3 输出一致)
                        "group_id": desanitize_group_id_from_graphiti(node.get("group_id", "")),
                        "node_id": node.get("node_id", ""),
                        "source": "neo4j_fulltext",
                    }
                )
            return episodes
        except asyncio.CancelledError:
            raise
        except Exception as e:  # noqa: BLE001 — HIGH-6: 含 ServiceUnavailable /
            # SessionExpired 等不在原白名单的 neo4j 异常族
            logger.debug(f"Neo4j fulltext search failed (non-fatal): {e}")
            # fulltext index may not exist yet — 仍如实记入 fail_sink
            return _fail(f"neo4j fulltext: {type(e).__name__}: {e}")

    async def search_memories_with_status(
        self,
        query: str,
        group_id: Optional[str] = None,
        max_results: int = 50,
        limit: Optional[int] = None,
        search_config: str = "combined_rrf",
        search_filter: Optional[Any] = None,
        # 批次1'④ 地板取 0.05: bge-reranker 跨语弱相关落在 0.05-0.2 区间
        # (0.2 实测误杀 mem-05/15/24, recall@5 -9pt); 假阳性防护主要靠
        # cross_encoder 区分度, 地板只砍趋零噪音
        min_relevance: float = 0.05,
    ) -> "StatusedResult":
        """
        Search learning memories using 3-tier layered search with unified scoring.

        CARD-G4-2 (2026-08-28): 四态版本 — 返回 StatusedResult 而非裸 list。
        Neo4j/Graphiti 故障不再静默降为空列表:
          - 全部远端 Tier 失败且内存兜底也空 → unavailable (带 reason)
          - 部分 Tier 失败 (仍有结果或有内存兜底) → degraded (带 reason)
          - 全部 Tier 正常但无命中 → empty (无 reason)
          - 有命中 → ok
        旧 ``search_memories()`` 委托本方法并返回 ``.items``, 保 list 契约
        (~12 处调用方直接迭代, 兼容铁律)。

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

        # 批次4' 检索束 (MEM-FLYWHEEL): query 命中双语术语表 → 拼接对侧语言
        # 术语束再检索 — 跨语/短词多义场景 (「极小极大」→ minimax) 召回稳态化
        from app.core.term_aliases import expand_query

        query = expand_query(query)

        # CARD-G4-1a (2026-08-30): 三层检索的作用域在**入口解析一次**, 三个
        # Tier 共用同一个 group —— 否则 Tier 1/2 各自解析、Tier 3 拿 None,
        # 同一次 search 会给出三种不同的隔离面。三个 Tier 内部仍各自
        # require_read_group (被直接调用时也 fail-closed), 解析幂等。
        from app.core.vault_scope import group_in_read_scope, require_read_group

        group_id = require_read_group(
            group_id, context="memory_service.search_memories_with_status"
        )

        effective_limit = limit if limit is not None else max_results
        seen_ids: set = set()
        merged: List[Dict[str, Any]] = []

        # Tier 1: Graphiti semantic search via search_()
        # CARD-G4-2 Codex round-1 HIGH-5: 区分「整 Tier 不可用」与「覆盖面
        # 收窄」——subgroup 枚举失败只影响检索广度, 不该让两个主 Tier 都
        # 成功的查询被报成 unavailable。
        tier_failures: List[str] = []      # 主检索 Tier 硬失败
        coverage_failures: List[str] = []  # 覆盖面收窄 (子组枚举等)
        graphiti_hits = await self._search_graphiti(
            query,
            group_id,
            effective_limit,
            search_config=search_config,
            search_filter=search_filter,
            fail_sink=tier_failures,
            coverage_sink=coverage_failures,
        )
        for ep in graphiti_hits:
            ep_id = ep.get("episode_id", "")
            if ep_id and ep_id not in seen_ids:
                seen_ids.add(ep_id)
                # Tier 1 results already have relevance_score from reranker
                ep["relevance_score"] = self._compute_unified_score(ep, tier=1)
                merged.append(ep)

        # Tier 2: Neo4j fulltext search
        neo4j_hits = await self._search_neo4j_fulltext(
            query, group_id, effective_limit, fail_sink=tier_failures
        )
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
            # CARD-G4-1a (2026-08-30): 卡文未点名、通读发现的**同类**漏点 ——
            # 入口 group 恒非空后, 这行等值比较从"常年不生效"变成"生效且过严",
            # 会把落在 canvas/semantic/punycode 子组的内存 episode 全部丢掉
            # (Tier 1/2 都改了前缀语义, 唯独 Tier 3 收窄 = 三层可见面不一致)。
            if not group_in_read_scope(episode.get("group_id"), group_id):
                continue
            ep_id = episode.get("episode_id", "")
            if ep_id in seen_ids:
                continue
            searchable = " ".join(
                str(episode.get(field, "")) for field in ("content", "episode_type", "node_id", "concept")
            ).lower()
            if query_lower in searchable:
                seen_ids.add(ep_id)
                episode_with_source = {**episode, "source": "in_memory"}
                episode_with_source["relevance_score"] = self._compute_unified_score(episode_with_source, tier=3)
                merged.append(episode_with_source)
                tier3_count += 1

        # FSRS R-value injection: boost low-retrievability concepts
        self._inject_fsrs_r_values(merged)

        # Sort by relevance_score descending (unified across all tiers)
        merged.sort(key=lambda x: x.get("relevance_score", 0.0), reverse=True)

        # 批次1'④ (MEM-FLYWHEEL): 文本级近重去重 (跨 Tier, 收不同 uuid 近重边)
        pre_dedupe = len(merged)
        merged = self._dedupe_by_text(merged)

        # 批次1'④ (MEM-FLYWHEEL): 相关度地板 — 低于阈值宁可空 (假阳性满编
        # 止血一阶手段)。Tier1/2 全空的降级场景跳过地板, 保留 Tier3 内存兜底。
        # HIGH-5: 记住**过滤前**的候选数 —— 状态折算只看「源是否可用/有没有
        # 检索到东西」, 质量地板是展示层裁剪, 不能反过来把 degraded 说成
        # unavailable (T1 挂了 + T2 命中低分被滤光 = 仍是 degraded)。
        pre_filter_count = len(merged)
        if min_relevance > 0 and (graphiti_hits or neo4j_hits):
            merged = [r for r in merged if r.get("relevance_score", 0.0) >= min_relevance]

        # Epic 4 Feature 4.2: Log which tier(s) produced results
        logger.info(
            f"[search_memories] Tier 1: {len(graphiti_hits)} results, "
            f"Tier 2: {len(neo4j_hits)} results, "
            f"Tier 3: {tier3_count} results "
            f"(deduped {pre_dedupe - len(merged) if pre_dedupe > len(merged) else 0}, "
            f"floor={min_relevance}, returned {len(merged[:effective_limit])})"
        )

        # CARD-G4-2 四态折算 (HIGH-5 修订): 判定基于**源可用性 + 过滤前候选**,
        # 不用过滤后条目数 —— 否则质量地板滤光结果会把 degraded 误升为
        # unavailable。
        #   - 主 Tier 硬失败 且 检索到 0 候选 → unavailable (空不可信)
        #   - 主 Tier 硬失败 但 有候选 (含被地板滤掉的/Tier3 兜底) → degraded
        #   - 无硬失败但覆盖面收窄 (子组枚举失败) → degraded (结果可能不全)
        #   - 全健康 → 按最终有无条目给 ok / empty
        from app.models.service_status import StatusedResult

        final_items = merged[:effective_limit]
        if tier_failures:
            reason = "; ".join(tier_failures)
            if final_items or pre_filter_count:
                return StatusedResult.degraded(final_items, reason)
            return StatusedResult.unavailable(reason)
        if coverage_failures:
            return StatusedResult.degraded(
                final_items, "; ".join(coverage_failures)
            )
        return StatusedResult.from_items(final_items)

    async def search_memories(
        self,
        query: str,
        group_id: Optional[str] = None,
        max_results: int = 50,
        limit: Optional[int] = None,
        search_config: str = "combined_rrf",
        search_filter: Optional[Any] = None,
        min_relevance: float = 0.05,
    ) -> List[Dict[str, Any]]:
        """兼容委托 — 保 list 契约 (CARD-G4-2 兼容铁律)。

        存量 ~12 处调用方直接迭代返回值, 契约不可硬换。新代码应改用
        ``search_memories_with_status()``: 本方法的空 list 无法区分
        「真的没有记忆」与「Neo4j/Graphiti 挂了」。
        """
        result = await self.search_memories_with_status(
            query,
            group_id=group_id,
            max_results=max_results,
            limit=limit,
            search_config=search_config,
            search_filter=search_filter,
            min_relevance=min_relevance,
        )
        return result.items

    async def search_error_memories_with_status(
        self,
        node_id: str,
        group_id: Optional[str] = None,
        limit: int = 5,
    ) -> "StatusedResult":
        """检索节点的历史误解/错误记录 — CARD-G4-2 四态版本。

        (Story 2.3 消费方契约, 批次2' 线3 补齐)

        chat.py /enrich-context 与 chat_context_assembler 自 2026-05-13 起调用
        此方法, 但方法本体从未实现 — 现网 500 (BUG-32DB6194, G-PIPE 实例)。
        实现: search_memories 三层融合定向查询 + 错误信号过滤, 映射为
        assembler._format_historical_errors 消费的 error_record schema
        (error_type / description / corrected_at / tags / source_session)。
        """
        # CARD-G4-2 Codex round-1 BLOCKER-4: 内部改调状态方法, 底层故障
        # 不再被剥成空 list (chat /enrich-context 消费本方法, 空历史错误
        # 与「Neo4j 挂了」必须可分辨)。
        search_result = await self.search_memories_with_status(
            query=f"{node_id} 错误 误解 mistake misconception",
            group_id=group_id,
            max_results=max(limit * 4, 20),
        )
        hits = search_result.items
        markers = (
            "error",
            "mistake",
            "misconception",
            "错误",
            "误解",
            "混淆",
            "纠正",
        )
        records: List[Dict[str, Any]] = []
        for h in hits:
            text = " ".join(str(h.get(k, "")) for k in ("content", "name", "episode_type")).lower()
            if not any(m in text for m in markers):
                continue
            records.append(
                {
                    "error_type": h.get("episode_type") or "learning_error",
                    "description": str(h.get("content") or "")[:500],
                    "corrected_at": str(h.get("timestamp") or ""),
                    "tags": [],
                    "source_session": str(h.get("group_id") or ""),
                    "_episode_id": str(h.get("episode_id") or ""),
                    "_node_id": node_id,
                }
            )
            if len(records) >= limit:
                break

        from app.models.service_status import ServiceStatus, StatusedResult

        if search_result.status is ServiceStatus.UNAVAILABLE:
            return StatusedResult.unavailable(search_result.reason or "search unavailable")
        if search_result.status is ServiceStatus.DEGRADED:
            return StatusedResult.degraded(records, search_result.reason or "degraded")
        return StatusedResult.from_items(records)

    async def search_error_memories(
        self,
        node_id: str,
        group_id: Optional[str] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """兼容委托 — 保 list 契约 (CARD-G4-2 兼容铁律)。

        新代码应改用 ``search_error_memories_with_status()``。
        """
        result = await self.search_error_memories_with_status(
            node_id, group_id=group_id, limit=limit
        )
        return result.items

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
            # CARD-G4-1a: 同 record_batch_learning_events —— 内存 episode 自带
            # 归属, 否则读侧封堵后 Tier 3 检索永远看不到时序事件。
            "group_id": _vault_scoped_group_id(
                extract_subject_from_canvas_path(canvas_path),
                canvas_name=extract_canvas_name(canvas_path),
            ),
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
            group_id=_vault_scoped_group_id(inferred_subject, canvas_name=c_name),
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
                lines = FAILED_WRITES_FILE.read_text(encoding="utf-8").strip().splitlines()
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
                still_pending.append(line)  # preserve malformed lines to avoid data loss
                continue

            try:
                # A7 (P2): 结构化条目 (callout/error/relation/对话) → 重走
                # record_knowledge_entity 的结构化写入 (启动时 worker 通常已就绪)。
                # _from_recovery=True 防止再次失败时重复落 outbox。
                if entry.get("kind") == "knowledge_entity":
                    result = await self.record_knowledge_entity(
                        event_type=entry.get("event_type", ""),
                        content=entry.get("content", ""),
                        metadata=entry.get("metadata"),
                        group_id=entry.get("group_id"),
                        _from_recovery=True,
                    )
                    if result.get("status") in ("written", "enqueued"):
                        recovered += 1
                    else:
                        still_pending.append(line)
                    continue

                # Phase 2: Enqueue recovered entry to GraphitiEpisodeWorker
                concept = entry.get("concept", "") or entry.get("concept_id", "unknown")
                entry_canvas = entry.get("canvas_name", "")
                inferred_subject = extract_subject_from_canvas_path(entry_canvas)
                c_name = extract_canvas_name(entry_canvas)
                enqueued = self._enqueue_episode(
                    name=f"recovery:{concept[:80]}",
                    episode_body=(f"Recovered learning event for concept '{concept}' on canvas '{entry_canvas}'."),
                    group_id=_vault_scoped_group_id(inferred_subject, canvas_name=c_name),
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
                    tmp_file.write_text("\n".join(still_pending) + "\n", encoding="utf-8")
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

        logger.info(f"[Story 38.6] Recovered {recovered} failed writes, {len(still_pending)} still pending")
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
                    results.append(
                        {
                            "timestamp": entry.get("timestamp", ""),
                            "canvas_name": entry.get("canvas_name", ""),
                            "node_id": entry.get("concept_id", ""),
                            "concept": entry.get("concept", "") or entry.get("concept_id", ""),
                            "score": entry.get("score"),
                            "user_id": entry.get("user_id", ""),  # S34 fix: include for filtering
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
        if _memory_service_instance is not None and _memory_service_instance._initialized:
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
