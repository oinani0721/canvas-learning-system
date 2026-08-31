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
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Neo4j async driver
# ✅ Verified from Context7:/websites/neo4j_cypher-manual_25 (topic: AsyncGraphDatabase)
from neo4j import AsyncDriver, AsyncGraphDatabase
from neo4j.exceptions import (
    AuthError,
    Neo4jError,
    ServiceUnavailable,
    SessionExpired,
    TransientError,
)

# Retry mechanism
# ✅ Story 30.2 AC-5: Exponential backoff retry
from tenacity import (
    RetryError,
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

# T1 统一 (2026-07-10): 物理层 group_id 单一 __ 格式 (graphiti_core validator 拒冒号),
# 所有直接读写 Neo4j group_id 属性的 Cypher 绑定前必须转换
from app.graphiti.group_id_compat import to_physical_group_id

logger = logging.getLogger(__name__)

# Default storage path for JSON fallback mode
DEFAULT_STORAGE_PATH = Path(__file__).parent.parent.parent / "data" / "neo4j_memory.json"

# Retryable exceptions for Neo4j operations
RETRYABLE_EXCEPTIONS = (ServiceUnavailable, SessionExpired, TransientError)


def _resolve_physical_group_id(group_id: Optional[str], canvas_path: Optional[str] = None) -> Optional[str]:
    """G2-3 写身份组解析: 先解析、后进 MERGE/MATCH 锚定键 (W1/W2/W5).

    解析顺序 (与 record_episode 的 wave-5 Stage B 推导链同源):
    1. 显式 group_id
    2. ContextVar 当前 vault (请求边界设置的 vault: 前缀值)
    3. canvas_path 提取 subject → vault:default 命名空间

    返回物理化 (vault__x) 的 group_id, 解析失败返回 None。
    调用方必须 fail-closed: logger.error + 拒写。null 进 MERGE 键会被
    Neo4j 服务端直接拒绝 (Cannot merge with null property), 静默降级
    DEFAULT_GROUP_ID 则是跨 vault 污染 — 两者都禁止。

    输入/输出双向校验 (2026-08-28 边界实测整改): 空白串等"看似有值实为
    空"的输入会被 canonical_group_id 静默映射成 ``vault__default``
    (正是本卡禁止的静默降级); ``"vault:"`` 这类裸前缀会产出空后缀的
    ``vault__`` 垃圾组。故先 strip 输入 (空白 → 视为未提供), 再校验
    输出形态 (必须 ``vault__`` + 非空且无空白后缀), 不合格一律返 None
    交调用方 fail-closed。
    ⚠️ 边界如实声明: 显式传入 legacy 值 (``cs188``/``canvas-dev``) 仍走
    group_id_compat 既有的 deprecated → ``vault__default`` 归一 (带
    WARNING, Story 2.5.Y AC #3 契约), 本卡不改该 compat 语义; 生产写路径
    无此类调用方 (ContextVar 的 ``general`` 默认值已在分支 2 排除)。
    """
    # C1 (Codex round-2/3): 显式传了字符串但内容为空 = 调用方 bug, **不得**
    # 静默回退推导链落到另一个 vault —— 直接 fail-closed 交调用方处理。
    # round-3 修正: 空串 "" 与空白串 "   " 口径必须一致 (原实现因 "" 为
    # 假值而漏进推导链, 两种"空"行为分裂)。想走推导链请显式传 None。
    if isinstance(group_id, str) and not group_id.strip():
        logger.error(
            "[G2-3 W3] explicit group_id is blank (%r) — refusing to infer a "
            "different vault; caller must pass a real group_id or None",
            group_id,
        )
        return None
    resolved = group_id.strip() if isinstance(group_id, str) else group_id
    if not resolved:
        from app.core.subject_config import (
            build_vault_group_id,
            canonical_group_id,
            extract_subject_from_canvas_path,
            get_current_subject_id,
            is_vault_group_id,
        )

        ctx_value = get_current_subject_id()
        ctx_value = ctx_value.strip() if isinstance(ctx_value, str) else ctx_value
        if ctx_value and ctx_value != "general":
            resolved = ctx_value if is_vault_group_id(ctx_value) else canonical_group_id(ctx_value)
        elif canvas_path:
            subject = extract_subject_from_canvas_path(canvas_path)
            resolved = build_vault_group_id("default", subject_id=subject)
    if not resolved:
        return None
    # T1 统一 (2026-07-10): 物理层 group_id 单一 __ 格式
    physical = to_physical_group_id(resolved)
    if not _is_valid_physical_group_id(physical):
        logger.error(
            "[G2-3 W3] group_id resolution produced an invalid physical value "
            "(input=%r → %r) — refusing to use it as a write identity key",
            group_id,
            physical,
        )
        return None
    return physical


_PHYSICAL_GROUP_PREFIX = "vault__"


def _is_valid_physical_group_id(value: Optional[str]) -> bool:
    """物理 group_id 形态校验: ``vault__`` + 每段非空、无空白.

    分隔符是 ``__``, 故 ``vault____x`` (来自畸形输入 ``vault::x``) 是
    "空段" —— 段级校验把它一并拒掉 (Codex round-2 C1b)。
    """
    if not isinstance(value, str):
        return False
    if not value.startswith(_PHYSICAL_GROUP_PREFIX):
        return False
    suffix = value[len(_PHYSICAL_GROUP_PREFIX) :]
    if not suffix or any(ch.isspace() for ch in suffix):
        return False
    return all(seg for seg in suffix.split("__"))


#: 概念点查的 Cypher 匹配片段 (CARD-G4-1b)。
#:
#: ⚠️ 为什么不是单纯的 ``c.id = $conceptId``: 生产写侧
#: ``create_learning_relationship`` 的 MERGE 身份是 ``{name, group_id}``,
#: **从不落 ``c.id``** —— 只按 id 点查会让 ``/concepts/{id}/history`` 端点
#: 换了真 Cypher 之后**仍然**恒空 (名实一致修了个寂寞)。而调用方手里能拿到
#: 的标识符恰恰只有名字: ``get_review_suggestions`` / ``get_learning_history``
#: 返回的 ``concept_id`` 就是 ``c.id``, 在生产数据上恒 null。
#: 因此按 id **或** name 命中; 两者都在 group 过滤之内, 不构成跨 vault 面
#: (读契约 R3 说的"name 派生 ID 只在 vault 内唯一"正好由 R1 过滤兜住)。
#: JSON 镜像 :func:`_concept_id_matches` 与本片段**逐字同语义**。
_CONCEPT_ID_MATCH_CYPHER = "(c.id = $conceptId OR c.name = $conceptId)"


def _concept_id_matches(rel: Dict[str, Any], concept_id: str) -> bool:
    """JSON 镜像侧的概念点查判定 — 与 :data:`_CONCEPT_ID_MATCH_CYPHER` 对应。

    两侧必须同一套命中规则, 否则 Neo4j 可用与降级两条路径会给出不同的历史
    条数 (本卡"镜像与 Cypher 同批同语义"的落点之一)。
    """
    return rel.get("concept_id") == concept_id or rel.get("concept_name") == concept_id


def _iso_timestamps(records: Any) -> Any:
    """把 Cypher 读回的 **temporal** 时间戳归一成 ISO-8601 字符串（原地改 records）。

    ⚠️ 独立审计 (2026-08-31) 抓出的 HIGH，本卡自己的门全绿却漏掉：

    写侧 ``create_learning_relationship`` 落的是 ``SET r.timestamp = datetime()``
    —— **temporal 值**；驱动 ``result.data()`` 不做转换, 于是 ``run_query`` 返回的是
    ``neo4j.time.DateTime`` 对象。而 API 响应模型 ``ConceptHistoryTimeline.timestamp``
    是 ``Optional[str]``, pydantic 直接 ``ValidationError`` → 端点 HTTP **500**。
    JSON 镜像那侧返回的却是 ISO **字符串** (``datetime.now().isoformat()``),
    两条路径类型不一致 —— 正是本卡"降级前后同一套可见面"要消除的那种分叉。

    **为什么本卡的门没抓到**: 所有真库门的种子都写 ``r.timestamp = $ts`` 且
    ``$ts`` 绑的是**字符串**, 与生产写侧的 ``datetime()`` 形态不同。fixture 形态
    ≠ 生产形态 —— 与本卡已经抓到的"生产从不落 ``c.id``"是同一类陷阱, 抓到了一次
    却在同一张卡里漏了第二次。门 7.8 用生产形态种子端到端锁死这条。

    归一而不是放宽响应模型: ISO 串是这套 API 既有的对外契约
    (``_handle_merge_learning`` 落的就是 ``now.isoformat()``), 改模型会让两条路径
    继续各说各话。与相邻的 ``desanitize_group_id_from_graphiti`` 同属 R5
    "输出边界还原"。
    """
    for record in records or []:
        if not isinstance(record, dict):
            continue
        ts = record.get("timestamp")
        if ts is None or isinstance(ts, str):
            continue
        iso = getattr(ts, "isoformat", None)
        record["timestamp"] = iso() if callable(iso) else str(ts)
    return records


def _as_utc(value: Any) -> Optional[datetime]:
    """把 ISO-8601 串 / datetime 归一成**带时区的 UTC** datetime。

    Codex round-3 Q3' 整改: 降级路径原先直接比 ISO **字符串**。同一格式同一
    时区时字典序确实等于时序, 但 ``datetime.isoformat()`` 允许任意偏移量
    (``2026-01-01T00:00:00+08:00`` vs ``...T00:00:00Z``), 混合偏移下字典序
    与真实时序**不一致** —— 边界条数会静默错。这里统一转 UTC 再比。

    naive (无 tzinfo) 一律按 UTC 解释并在此点名: 本仓写侧
    ``create_learning_relationship`` 落的是 ``datetime()`` (服务端时区),
    JSON 镜像落的是 ``datetime.now().isoformat()`` (本机 naive) —— 两者本就
    没有统一时区语义, 这是既有形态; 本函数只保证**同一次比较的两侧口径一致**,
    不假装解决了全仓时区统一。

    Returns:
        归一后的 aware datetime; 解析失败返回 None (调用方据此放弃该条过滤,
        而不是拿一个错的比较结果继续)。
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        try:
            dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except (TypeError, ValueError):
            return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


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
        self._data: Dict[str, Any] = {"users": [], "concepts": [], "relationships": []}

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
                logger.info(f"Neo4j driver initialized: {self._uri}, pool_size={self._max_connection_pool_size}")
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
                    f"Loaded {len(self._data.get('relationships', []))} relationships from {self._storage_path}"
                )
            else:
                self._data = {
                    "users": [],
                    "concepts": [],
                    "relationships": [],
                    "metadata": {
                        "created_at": datetime.now().isoformat(),
                        "version": "2.0",  # Story 30.2 version
                    },
                }
                await self._save_json_data()
                logger.info(f"Created new JSON storage file: {self._storage_path}")

            self._initialized = True
            self._health_status = True
            return True

        except (json.JSONDecodeError, ValueError, OSError, IOError) as e:
            logger.error(f"JSON fallback initialization failed: {e}")
            self._initialized = True  # Still mark as initialized to avoid loops
            return False

    async def _save_json_data(self) -> None:
        """Save data to JSON storage file. Round-23 Story 8.2: atomic write."""
        try:
            from app.utils.atomic_io import atomic_write_json_async

            await atomic_write_json_async(
                self._storage_path,
                self._data,
                indent=2,
                ensure_ascii=False,
                default=str,
            )
        except (OSError, IOError, TypeError) as e:
            logger.error(f"Failed to save JSON data: {e}")

    async def _close_driver(self) -> None:
        """Close Neo4j driver connection."""
        if self._driver:
            try:
                await self._driver.close()
                self._driver = None
                logger.info("Neo4j driver closed")
            except (RuntimeError, OSError) as e:
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

        except Exception as e:  # noqa: BLE001 — 健康检查必须 fail-closed:
            # driver 故障形态不可枚举 (ServiceUnavailable 属 DriverError 非
            # Neo4jError, 原窄捕获会让异常逃逸成 500), 一律返 False。
            logger.warning(f"Neo4j health check failed: {e}")
            self._health_status = False
            self._last_health_check = datetime.now()
            return False

    async def run_query(self, query: str, **params: Any) -> List[Dict[str, Any]]:
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

    async def _run_query_neo4j(self, query: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
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
            wait=wait_exponential(multiplier=self._retry_delay_base, max=self._retry_max_delay),
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

    async def _run_query_json_fallback(self, query: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
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

    async def _handle_merge_learning(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
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
        user = next((u for u in self._data["users"] if u["id"] == user_id), None)
        if not user:
            user = {"id": user_id, "created_at": datetime.now().isoformat()}
            self._data["users"].append(user)

        # Ensure concept exists — G2-3 (W1 镜像): {name, group_id} 双键匹配,
        # 与 Cypher 复合身份同型; 禁止跨组按 name 命中后改写归属 (clobber)。
        concept_node = next(
            (c for c in self._data["concepts"] if c["name"] == concept and c.get("group_id") == group_id),
            None,
        )
        if not concept_node:
            concept_id = f"concept-{len(self._data['concepts']) + 1}"
            concept_node = {
                "id": concept_id,
                "name": concept,
                "created_at": datetime.now().isoformat(),
                "group_id": group_id,
            }
            self._data["concepts"].append(concept_node)

        # Create or update relationship — 同型双键 (user, concept, group)
        now = datetime.now()
        next_review = now + timedelta(days=1)

        rel = next(
            (
                r
                for r in self._data["relationships"]
                if r["user_id"] == user_id and r["concept_name"] == concept and r.get("group_id") == group_id
            ),
            None,
        )

        if rel:
            # Update existing relationship (group_id 已在双键匹配中锚定,
            # 不做事后改写归属)
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
                "review_count": 1,
                "group_id": group_id,
            }
            self._data["relationships"].append(rel)

        await self._save_json_data()

        logger.info(f"Created learning relationship: {user_id} -> {concept} (score={score})")

        return [{"r": rel}]

    async def _handle_query_reviews(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
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

        # CARD-G4-1a / Codex round-2 (2026-08-30) — **降级模式的同一个泄漏**:
        # 本模拟器此前完全忽略 group 参数, 于是 Neo4j 一降级, Cypher 侧刚封住
        # 的跨 vault 面就整个回来 (复习建议返回全部 vault 的待复习概念)。
        # 封堵可以被"把 Neo4j 弄挂"绕过 = 等于没封。scope 取查询自带的
        # group_id 参数 (由 read_scope_params 注入, 恒存在); 缺失即 fail-closed。
        scope = params.get("group_id")
        if not scope:
            logger.error(
                "[G4-1a] JSON fallback review query without scope — refusing "
                "cross-vault full scan (user_id=%s)",
                user_id,
            )
            return []

        from app.core.vault_scope import group_in_read_scope

        now = datetime.now()
        results = []

        for rel in self._data.get("relationships", []):
            if rel["user_id"] != user_id:
                continue
            if not group_in_read_scope(rel.get("group_id"), scope):
                continue

            # Check if due for review
            next_review_str = rel.get("next_review")
            if next_review_str:
                try:
                    next_review = datetime.fromisoformat(next_review_str)
                    if next_review < now:
                        # Codex round-3 (2026-08-30): concept 反查曾按 **name
                        # 全库匹配** —— 关系过滤住了, 但两个 vault 有同名概念
                        # 时会取到他 vault 那条的 concept_id (标识符级串读)。
                        # 反查同样要过 scope; 命中不到就用关系自带的 id 兜底。
                        concept = next(
                            (
                                c
                                for c in self._data["concepts"]
                                if c["name"] == rel["concept_name"]
                                and group_in_read_scope(c.get("group_id"), scope)
                            ),
                            {
                                "id": rel.get("concept_id", ""),
                                "name": rel["concept_name"],
                            },
                        )
                        results.append(
                            {
                                "concept": rel["concept_name"],
                                "concept_id": concept.get("id", ""),
                                "last_score": rel.get("last_score"),
                                "review_count": rel.get("review_count", 0),
                                "due_date": next_review.isoformat(),
                            }
                        )
                except (ValueError, TypeError):
                    continue

        # Sort by due date (oldest first)
        results.sort(key=lambda x: x.get("due_date", ""))

        return results[:limit]

    async def _handle_query_history(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Handle query for concept learning history.

        Args:
            params: Query parameters

        Returns:
            List of learning history records
        """
        user_id = params.get("userId")
        concept_id = params.get("conceptId")

        # CARD-G4-1b (2026-08-31) — 升 fail-closed, 与 `_handle_query_reviews`
        # 完全同口径。G4-1a 当时只做"有 scope 则过滤 + 无 scope 告警", 理由是
        # 主调用方 `get_concept_history` 的 Cypher 路径尚未封堵, 单方面
        # fail-closed 会打断一个那张卡不拥有的功能。本卡把 Cypher 侧一并封了
        # (get_concept_history 补真实 Cypher 分支 + get_all_recent_episodes /
        # get_learning_history 全部注入 scope), 前提消失。
        #
        # ⚠️ 本 handler 是**关键词路由**的落点 (`_run_query_json_fallback`:
        # "MATCH" + "LEARNED" 且无 "next_review"), 而不只是 get_concept_history
        # 的镜像 —— `get_learning_history` 与 `get_all_recent_episodes` 的
        # Cypher 在**中途降级** (`_run_query_neo4j` 重试耗尽 → `_fallback_to_json`)
        # 时同样落到这里。若此处不 fail-closed, 那两条刚封的读只要"把 Neo4j 弄
        # 挂"就能整库倾倒。三个生产入口现在都经 read_scope_params 注入
        # `group_id`, 缺失即代表有人绕过了收口, 拒绝而不是全库扫。
        scope = params.get("group_id")
        if not scope:
            logger.error(
                "[G4-1b] JSON fallback history query without scope — refusing "
                "cross-vault full scan (user_id=%s, concept_id=%s)",
                user_id,
                concept_id,
            )
            return []

        from app.core.vault_scope import group_in_read_scope
        from app.graphiti.group_id_compat import desanitize_group_id_from_graphiti

        results = []

        # Codex round-2 Q3 整改: `get_learning_history` 的三个可选过滤在中途降级
        # 时被静默丢弃 —— 同一次调用"Neo4j 活着"与"跑一半挂了"返回的**条数与内容**
        # 都不同。三者的语义逐条对齐 Cypher 侧:
        #   startDate → `r.timestamp >= $startDate`
        #   endDate   → `r.timestamp <= $endDate`
        #   concept   → `toLower(c.name) CONTAINS toLower($concept)`
        # 时间比较统一转 aware UTC 再比 (``_as_utc``) —— 不依赖 ISO 字典序,
        # 混合时区偏移下字典序≠时序 (Codex round-3 Q3')。记录没有 timestamp
        # 时**不放行**(与 Cypher 的 NULL 比较结果为 null、不满足 WHERE 同口径)。
        #
        # ⚠️ **与 Cypher 侧的既有偏差, 如实登记 + 实测证据**:
        # `get_learning_history` 的 Cypher 把 `r.timestamp` (写侧
        # `create_learning_relationship` 用 `datetime()` 落的是 **temporal** 值)
        # 与 `$startDate` (调用方 `datetime.isoformat()` 落的是**字符串**) 直接
        # 比较。2026-08-31 于 7692 实测:
        #
        #     WITH datetime('2026-06-01T00:00:00Z') AS t, '2026-01-01T00:00:00' AS lo
        #     RETURN t >= lo, (t >= lo) IS NULL     →  null, true
        #
        # 即**比较运算符对不可比类型返回 null**, WHERE 不满足 ⇒ 带 startDate 的
        # 查询恒空。(Neo4j 文档里"跨类型有序"那套规则管的是 ORDER BY 的排序上下文,
        # 不是 `<`/`>=` 比较运算符 —— 这两件事容易被混为一谈, 故留实测在此。)
        #
        # 也就是说 **Cypher 路径的日期过滤本身就是坏的**(既有缺陷, G4-1a 之前
        # 即如此, 与跨库读无关)。本卡把降级路径修成**正确**语义, 因此这两条路径
        # 在带日期过滤时**不等价**: 降级侧对、Cypher 侧恒空。修 Cypher 侧要动
        # 写侧类型或读侧参数类型, 属另一张卡, 已在验收单登记。不要据此认为两侧已对齐。
        start_date = params.get("startDate")
        end_date = params.get("endDate")
        concept_filter = params.get("concept")

        for rel in self._data.get("relationships", []):
            if user_id and rel["user_id"] != user_id:
                continue
            if concept_id and not _concept_id_matches(rel, concept_id):
                continue
            if not group_in_read_scope(rel.get("group_id"), scope):
                continue
            if start_date or end_date:
                ts = _as_utc(rel.get("timestamp"))
                if ts is None:
                    continue
                # Codex round-4 Q3'' 整改: **边界**解析失败也要 fail-closed。
                # 原来 `lo/hi` 为 None 时过滤被整个跳过 —— 调用方传了个畸形
                # startDate, 结果是"过滤悄悄消失、全都放行", 正是本卡在别处反复
                # 堵的那种"把没生效当成没限制"。传了就必须能解析。
                lo = _as_utc(start_date) if start_date else None
                hi = _as_utc(end_date) if end_date else None
                if (start_date and lo is None) or (end_date and hi is None):
                    logger.error(
                        "[G4-1b] JSON fallback history query has unparseable date "
                        "bound (startDate=%r, endDate=%r) — refusing to drop the "
                        "filter silently",
                        start_date,
                        end_date,
                    )
                    continue
                if lo is not None and ts < lo:
                    continue
                if hi is not None and ts > hi:
                    continue
            if concept_filter:
                name = rel.get("concept_name") or ""
                if str(concept_filter).lower() not in str(name).lower():
                    continue

            results.append(
                {
                    "user_id": rel["user_id"],
                    "concept": rel["concept_name"],
                    "concept_id": rel.get("concept_id"),
                    "score": rel.get("last_score"),
                    "timestamp": rel.get("timestamp"),
                    # 独立审计 (2026-08-31) 抓出: 本落点原先**不返回 group_id**,
                    # 而 `_get_learning_history_json` / `_get_all_recent_episodes_json`
                    # 两个镜像都返回。中途降级时 `get_all_recent_episodes` 落到这里,
                    # 恢复进 episode 缓存的记录就带**空** group_id —— 之后每一次
                    # `group_in_read_scope` 判定都是 False (无归属不属于任何可见面),
                    # 那些 episode 永久不可见, 且 `_episodes_recovered=True` 不会重恢复。
                    # 与镜像逐字同型 (含 agent_type), 输出 D16 冒号格式 (R5 还原)。
                    "group_id": desanitize_group_id_from_graphiti(
                        rel.get("group_id") or ""
                    ),
                    "agent_type": rel.get("agent_type"),
                    "review_count": rel.get("review_count", 0),
                }
            )

        # Sort by timestamp (newest first)
        results.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        # Codex round-1 HIGH-2 整改: 尊重查询自带的 limit。本 handler 是**中途
        # 降级**的落点, 三个调用方 (learning_history / concept_history /
        # all_recent_episodes) 的 Cypher 都写了 `LIMIT $limit` 且都把 limit 放进
        # 了 params —— 降级后忽略它, 会让同一次调用在"Neo4j 活着"与"跑一半挂了"
        # 两种情况下返回不同条数。
        limit = params.get("limit")
        if isinstance(limit, int) and limit >= 0:
            return results[:limit]
        return results

    async def create_learning_relationship(
        self,
        user_id: str,
        concept: str,
        score: Optional[int] = None,
        group_id: Optional[str] = None,
        canvas_path: Optional[str] = None,
    ) -> bool:
        """
        Create a learning relationship between user and concept.

        ✅ Verified from docs/stories/22.4.story.md#_create_neo4j_learning_relationship

        G2-3 (W1): Concept 与 LEARNED 的写身份为 {name/端点, group_id} 复合键 —
        同名概念在不同 vault 是不同物理节点/边, 禁止事后 SET 归属。
        group_id 解析失败时 fail-closed 拒写 (不静默降级 DEFAULT)。

        Args:
            user_id: User ID
            concept: Concept name
            score: Optional score
            group_id: group_id for vault isolation (Story 30.8 / G2-3 W1)
            canvas_path: Optional canvas path used to resolve group_id when
                group_id is not provided (wave-5 Stage B inference chain)

        Returns:
            True if successful, False on failure or unresolved group_id
        """
        physical_group_id = _resolve_physical_group_id(group_id, canvas_path)
        if not physical_group_id:
            # G2-3 fail-closed (首日观察): 不静默降级 DEFAULT_GROUP_ID,
            # 如需降级须补 [Decision] 记录。
            logger.error(
                "[G2-3 W1 fail-closed] create_learning_relationship refused: "
                "unresolved group_id (user_id=%s, concept=%r, canvas_path=%r)",
                user_id,
                concept,
                canvas_path,
            )
            return False
        # FR-KG-04 Phase 15 Task 15.2: Increment review_count on every scoring
        # event so get_review_suggestions can prioritize concepts by review history.
        # coalesce() handles the first-time case where review_count is null → 1.
        query = """
        MERGE (u:User {id: $userId})
        MERGE (c:Concept {name: $concept, group_id: $groupId})
        MERGE (u)-[r:LEARNED {group_id: $groupId}]->(c)
        SET r.timestamp = datetime(),
            r.score = $score,
            r.next_review = datetime() + duration('P1D'),
            r.review_count = coalesce(r.review_count, 0) + 1
        RETURN r
        """
        results = await self.run_query(
            query,
            userId=user_id,
            concept=concept,
            score=score,
            groupId=physical_group_id,
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

        # G2-3: group_id inference (ContextVar → canvas_path subject →
        # vault:default) 收敛到 _resolve_physical_group_id, 由
        # create_learning_relationship 统一执行 (wave-5 Stage B 链不变)。
        return await self.create_learning_relationship(
            user_id=user_id,
            concept=concept,
            score=score,
            group_id=group_id,
            canvas_path=data.get("canvas_path"),
        )

    async def get_review_suggestions(
        self, user_id: str, limit: int = 10, group_id: Optional[str] = None
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
        # FR-KG-04 Phase 15 Task 15.1: Single source of truth for the score is
        # r.score (set by create_learning_relationship). Earlier this query
        # read r.last_score, a property no write path ever set, so the API
        # always returned null and the review scheduler operated blind.
        # The alias keeps the JSON key "last_score" for backwards compatibility.
        # CARD-G4-1a (2026-08-30) — 审计 §5 #3 (R4:violation) 的无 group 分支
        # **已删除**。Codex round-1 B-2: 保留它 = 漏洞原语仍在, 任何 CLI /
        # 后台任务 / 新 service 直接调这个公共 client 就立刻恢复"同一 user 的
        # 全 vault 扫描"。签名保持 ``group_id: Optional`` 不变 (兼容既有调用
        # 面), 但**行为**统一走 read_scope_params: 不传就按 per-request /
        # active vault 解析, 解析不出就抛 —— 无过滤分支不复存在。
        #
        # 过滤语义 = 等值 OR 前缀 (读契约 R1 的 vault 内二级 namespace 口径)。
        # 现网实证: 全库唯一的 Concept 与唯一的 LEARNED 边都落在 canvas 子组
        # `vault__canvas_vault__xn--jhqx6ce6ettpca6420ada2925d`, vault 根组零
        # 命中 —— 按根组等值查, "复习建议"会整页空。
        # `r` alias 一并过滤 (审计 §5 #2 CONDITIONAL: LEARNED 自带 group_id)。
        from app.core.vault_scope import read_group_filter, read_scope_params

        # T1 统一 (2026-07-10): 物理层 group_id 单一 __ 格式
        # (read_scope_params 内部即 to_physical_group_id)
        scope_params = read_scope_params(
            group_id, context="neo4j_client.get_review_suggestions"
        )
        query = f"""
        MATCH (u:User {{id: $userId}})-[r:LEARNED]->(c:Concept)
        WHERE r.next_review < datetime()
          AND {read_group_filter("c")}
          AND {read_group_filter("r")}
        RETURN c.name as concept,
               c.id as concept_id,
               r.score as last_score,
               r.review_count as review_count,
               r.next_review as due_date
        ORDER BY r.next_review
        LIMIT $limit
        """
        results = await self.run_query(
            query,
            userId=user_id,
            limit=limit,
            **scope_params,
        )

        # Add priority based on review count
        suggestions = []
        for r in results:
            priority = "high" if r.get("review_count", 0) < 3 else "medium"
            suggestions.append({**r, "priority": priority})

        return suggestions

    async def get_concept_history(
        self,
        concept_id: str,
        user_id: Optional[str] = None,
        limit: int = 50,
        group_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get learning history for a specific concept.

        ✅ Verified from AC-22.4.3: GET /api/v1/memory/concepts/{id}/history

        CARD-G4-1b (2026-08-31) — **名实一致修复 + 读作用域收口**。

        修复前本方法**无论是否连着 Neo4j** 都直接调 ``_handle_query_history``,
        即永远读 JSON 模拟器的 ``self._data``。真实部署走 Neo4j 模式时
        ``self._data`` 是空壳 ⇒ ``/api/v1/memory/concepts/{id}/history``
        端点**恒返回空 timeline**, 而调用方只能把它读成"这个概念没学过"。
        名字叫 "get_concept_history"、实际从不查图 —— DD-13 名实一致的典型。
        本卡补上真实 Cypher 分支 (模板取自 :meth:`get_learning_history`,
        加概念点查条件), JSON 路径退回它本来的位置: **降级** fallback。
        ⚠️ 产品可见变化: 该端点从"恒 EMPTY"变成"可能有数据"。

        读作用域走统一链 ``read_scope_params`` (显式 → per-request ContextVar
        → active vault → 解析不出即抛), ``r`` / ``c`` 两个 alias 逐一过滤
        (R1「每个 alias 逐一过滤」), 等值 OR 前缀语义 (现网存量 Concept /
        LEARNED 全在 punycode 子组, 等值锚 vault 根组会整页空)。

        Args:
            concept_id: Concept ID **或概念名** (见 :data:`_CONCEPT_ID_MATCH_CYPHER`)
            user_id: Optional user ID filter
            limit: Maximum results
            group_id: 读作用域 (G4-1b); 省略时按统一链推导

        Returns:
            List of learning history records

        Raises:
            VaultScopeUnresolved: group 解析失败 (拒绝无作用域读取)
        """
        from app.core.vault_scope import read_group_filter, read_scope_params

        scope_params = read_scope_params(
            group_id, context="neo4j_client.get_concept_history"
        )
        params: Dict[str, Any] = {
            "conceptId": concept_id,
            "limit": limit,
            **scope_params,
        }
        if user_id:
            params["userId"] = user_id

        if self._use_json_fallback:
            results = await self._handle_query_history(params)
            return results[:limit]

        user_clause = " AND u.id = $userId" if user_id else ""
        query = f"""
        MATCH (u:User)-[r:LEARNED]->(c:Concept)
        WHERE {_CONCEPT_ID_MATCH_CYPHER}
          AND {read_group_filter("r")}
          AND {read_group_filter("c")}{user_clause}
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
        results = await self.run_query(query, **params)

        # T1 统一 (2026-07-10): 物理 __ 格式读回后转 D16 冒号, 与
        # get_learning_history 的对外输出契约一致 (R5 输出边界还原)。
        from app.graphiti.group_id_compat import desanitize_group_id_from_graphiti

        for record in results or []:
            if isinstance(record, dict) and record.get("group_id"):
                record["group_id"] = desanitize_group_id_from_graphiti(
                    record["group_id"]
                )
        # 独立审计 HIGH: temporal → ISO 串, 否则响应模型校验失败 → 端点 500
        return _iso_timestamps(results or [])[:limit]

    async def get_learning_history(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        concept: Optional[str] = None,
        group_id: Optional[str] = None,
        limit: int = 100,
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
                limit=limit,
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
        # CARD-G4-1a (2026-08-30, Codex round-1 B-2): group 过滤从**可选拼接**
        # 改为**无条件**。原来 `if group_id:` 让不传 group 的调用直接跑无过滤
        # Cypher (审计 §5 #4 CONDITIONAL 的实质)。签名仍是 Optional, 但行为统一
        # 走 read_scope_params (不传 → per-request/active vault → 解析不出即抛)。
        # 语义: 等值 → 等值 OR 前缀 (与 get_review_suggestions 同因: 存量
        # LEARNED 边落在 canvas 子组, vault 根组等值查恒空); 并补 c alias ——
        # 原查询只过滤了关系 r, 概念节点侧未过滤 (R1「每个 alias 逐一过滤」)。
        # T1 统一 (2026-07-10): 物理层 group_id 单一 __ 格式
        # (read_scope_params 内部即 to_physical_group_id)
        from app.core.vault_scope import read_group_filter, read_scope_params

        query += f" AND {read_group_filter('r')} AND {read_group_filter('c')}"
        params.update(
            read_scope_params(group_id, context="neo4j_client.get_learning_history")
        )

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
        # T1 统一 (2026-07-10): 物理 __ 格式读回后转 D16 冒号, 对外输出一致
        from app.graphiti.group_id_compat import desanitize_group_id_from_graphiti

        for record in results or []:
            if isinstance(record, dict) and record.get("group_id"):
                record["group_id"] = desanitize_group_id_from_graphiti(record["group_id"])
        # 与 get_concept_history 同口径 (独立审计 HIGH): 三条 LEARNED 读的
        # timestamp 都归一成 ISO 串, 与 JSON 镜像侧逐字同型。
        return _iso_timestamps(results)

    async def _get_learning_history_json(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        concept: Optional[str] = None,
        group_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        JSON fallback implementation for get_learning_history.

        ✅ Story 31.A.2: JSON fallback mode support

        [Source: docs/stories/31.A.2.story.md#AC-31.A.2.2]
        """
        from app.core.vault_scope import group_in_read_scope, require_read_group

        # 与 Cypher 路径同一个解析链 (Codex round-1 B-2): 降级模式也 fail-closed。
        scope = require_read_group(
            group_id, context="neo4j_client._get_learning_history_json"
        )
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
            # T1 统一 (2026-07-10): 写侧 create_learning_relationship 在分派
            # JSON fallback 前已物理化 (vault__x), 而调用方传逻辑冒号格式 —
            # 两侧都过 to_physical_group_id 再比较, 顺带兼容 T1 前写入的
            # 冒号存量 JSON (免清洗)。
            # CARD-G4-1a (2026-08-30): 等值 → 前缀语义, 与上面 Cypher 侧逐字
            # 对齐 —— 本镜像是 Neo4j 不可用时的**同一个读**, 两条路径可见面
            # 不同 = 降级前后用户看到的历史条数会变。group_in_read_scope 内部
            # 同样双侧 to_physical_group_id, 上面注释的 T1 兼容口径不变。
            # (JSON 镜像层**新增** group 过滤的那几处仍移交 CARD-G4-1b;
            #  此处只是把**已有**过滤的比较语义对齐, 不新开过滤面。)
            # Codex round-1 B-2 同修: `if group_id:` 去掉 —— 降级模式下不传
            # group 同样不该变成"整个 JSON 库全返回"。作用域在函数入口统一解析。
            if not group_in_read_scope(rel.get("group_id"), scope):
                continue

            from app.graphiti.group_id_compat import (
                desanitize_group_id_from_graphiti,
            )

            results.append(
                {
                    "user_id": rel.get("user_id"),
                    "concept": rel.get("concept_name"),
                    "concept_id": rel.get("concept_id"),
                    "score": rel.get("last_score"),
                    "timestamp": rel.get("timestamp"),
                    # T1: 输出 D16 冒号, 与 Neo4j 路径 get_learning_history
                    # 的 desanitize 输出契约一致
                    "group_id": desanitize_group_id_from_graphiti(rel.get("group_id") or ""),
                    "agent_type": rel.get("agent_type"),
                    "review_count": rel.get("review_count", 0),
                }
            )

        # Sort by timestamp (newest first)
        results.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        return results[:limit]

    async def create_canvas_node_relationship(
        self,
        canvas_path: str,
        node_id: str,
        node_text: Optional[str] = None,
        group_id: Optional[str] = None,
    ) -> bool:
        """
        Create Canvas-Node relationship in Neo4j graph.

        Story 30.5 AC-30.5.4: Canvas-Concept-LearningEpisode relationship graph

        G2-3 (W1): Canvas/Node 写身份为 {path/id, group_id} 复合键 —
        跨 vault 同名 canvas path / node id 是不同物理节点。group_id
        未提供时经 canvas_path 推导 (wave-5 链), 解析失败 fail-closed。

        Creates:
        - Canvas node if not exists
        - Node entity with text as potential concept
        - CONTAINS_NODE relationship from Canvas to Node

        Args:
            canvas_path: Canvas file path
            node_id: Node ID
            node_text: Node text content (potential concept)
            group_id: group_id for vault isolation (G2-3 W1)

        Returns:
            True if successful, False on failure or unresolved group_id

        [Source: docs/stories/30.5.story.md#Task-5.1]
        """
        physical_group_id = _resolve_physical_group_id(group_id, canvas_path)
        if not physical_group_id:
            logger.error(
                "[G2-3 W1 fail-closed] create_canvas_node_relationship refused: "
                "unresolved group_id (canvas_path=%r, node_id=%s)",
                canvas_path,
                node_id,
            )
            return False
        query = """
        MERGE (c:Canvas {path: $canvasPath, group_id: $groupId})
        MERGE (n:Node {id: $nodeId, group_id: $groupId})
        SET n.text = $nodeText,
            n.updated_at = datetime()
        MERGE (c)-[r:CONTAINS_NODE {group_id: $groupId}]->(n)
        SET r.created_at = coalesce(r.created_at, datetime())
        RETURN c, n, r
        """
        results = await self.run_query(
            query,
            canvasPath=canvas_path,
            nodeId=node_id,
            nodeText=node_text or "",
            groupId=physical_group_id,
        )
        return len(results) > 0

    async def create_edge_relationship(
        self,
        canvas_path: str,
        edge_id: str,
        from_node_id: str,
        to_node_id: str,
        edge_label: Optional[str] = None,
        group_id: Optional[str] = None,
    ) -> bool:
        """
        Create edge relationship between nodes in Neo4j graph.

        Story 30.5 AC-30.5.4: Canvas-Concept-LearningEpisode relationship graph

        Creates:
        - CONNECTS_TO relationship between Node entities
        - HAS_EDGE relationship from Canvas to Edge

        G2-3 (W1): Canvas/Node/CONNECTS_TO 写身份含 group_id 复合键
        (正例同形: sync_service.py CANVAS_EDGE {id, group_id})。

        Args:
            canvas_path: Canvas file path
            edge_id: Edge ID
            from_node_id: Source node ID
            to_node_id: Target node ID
            edge_label: Optional edge label
            group_id: group_id for vault isolation (G2-3 W1)

        Returns:
            True if successful, False on failure or unresolved group_id

        [Source: docs/stories/30.5.story.md#Task-5.2]
        """
        physical_group_id = _resolve_physical_group_id(group_id, canvas_path)
        if not physical_group_id:
            logger.error(
                "[G2-3 W1 fail-closed] create_edge_relationship refused: "
                "unresolved group_id (canvas_path=%r, edge_id=%s)",
                canvas_path,
                edge_id,
            )
            return False
        query = """
        MERGE (c:Canvas {path: $canvasPath, group_id: $groupId})
        MERGE (from:Node {id: $fromNodeId, group_id: $groupId})
        MERGE (to:Node {id: $toNodeId, group_id: $groupId})
        MERGE (from)-[r:CONNECTS_TO {edge_id: $edgeId, group_id: $groupId}]->(to)
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
            edgeLabel=edge_label or "",
            groupId=physical_group_id,
        )
        return len(results) > 0

    async def delete_edge_relationship(
        self,
        edge_id: str,
        group_id: Optional[str] = None,
        canvas_path: Optional[str] = None,
    ) -> bool:
        """
        Delete edge relationship from Neo4j graph by edge_id within a group.

        Story 36.3 P0 Fix: Symmetric with create_edge_relationship.
        G2-3 (W2): edge_id 可退化为端点拼接值 (neo4j_edge_client), 全局唯一
        性不可证, 不享受 W2 uuid 点删窄例外 — MATCH 必须带 group scope。
        group_id 解析失败 fail-closed 拒删 (禁全库删)。

        Args:
            edge_id: Edge ID to delete
            group_id: group_id scope for the deletion (G2-3 W2)
            canvas_path: Optional canvas path used to resolve group_id

        Returns:
            True if a relationship was deleted, False if not found or refused
        """
        physical_group_id = _resolve_physical_group_id(group_id, canvas_path)
        if not physical_group_id:
            logger.error(
                "[G2-3 W2 fail-closed] delete_edge_relationship refused: "
                "unresolved group_id (edge_id=%s) — unscoped delete forbidden",
                edge_id,
            )
            return False
        query = """
        MATCH ()-[r:CONNECTS_TO {edge_id: $edgeId, group_id: $groupId}]->()
        DELETE r
        RETURN count(r) AS deleted
        """
        results = await self.run_query(query, edgeId=edge_id, groupId=physical_group_id)
        deleted = results[0].get("deleted", 0) if results else 0
        if deleted > 0:
            logger.info(f"Deleted CONNECTS_TO relationship: edge_id={edge_id}")
        return deleted > 0

    async def get_concept_score_history(
        self, concept_id: str, canvas_name: str, limit: int = 5, group_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get historical scores for a concept.

        Story 31.5 AC-31.5.1: Query recent N score records for difficulty adaptation.

        CARD-G4-1a (2026-08-30) — 读写对称补齐 (审计 §5 #8, R1:violation):
        本查询此前只按 ``Node.id`` + ``Canvas.path`` 定位, 零 group 过滤。两者
        都不是全局唯一 ID (canvas node id 可外部传入、缺失时仅取 UUID 前 8 位,
        属读契约 R3 明列的反例), 所以两个 vault 里同名白板的同 id 节点会互相
        读到对方的分数。写侧 ``record_score_history`` 已在 G2-3 给 Node/Canvas/
        CONTAINS_NODE/Episode/SCORED **五个**身份全部落 group_id, 本方法按同一
        锚点逐 alias 过滤 (R1「每个 alias 逐一过滤」)。

        组解析走**读侧**链 ``read_scope_params`` (显式 → per-request ContextVar
        → active vault → 解析不出即抛)。⚠️ Codex round-1 H-2 整改 (2026-08-30):
        此前复用写侧 ``_resolve_physical_group_id``, 它在无 ContextVar 时会由
        canvas_path 推导出 ``vault__default__<canvas>`` —— 后台/CLI 读会"查询成
        功但零命中", 被上层折算成正常的 ``empty`` 并进 30s 缓存, 正是本卡要防
        的静默断读。canvas_name 在本方法里**只作查询条件**, 不参与 vault 推导。

        解析失败 **抛错**而不是返回空列表 —— 上层
        ``memory_service.get_concept_score_history`` 的 except 会把它折算成
        ``status="unavailable"`` + reason, 而静默返回 [] 会被展示成"这个概念没
        有历史分数" (CARD-G4-2 禁止的假空)。

        Args:
            concept_id: Concept/Node ID
            canvas_name: Canvas file name
            limit: Maximum number of records (default: 5)
            group_id: 读作用域 (G4-1a); 省略时按写侧同链推导

        Returns:
            List of dicts with score, timestamp fields (ordered from oldest to newest)

        Raises:
            VaultScopeUnresolved: group 解析失败 (拒绝无作用域读取)

        [Source: docs/stories/31.5.story.md#Task-2.2]
        """
        if self._use_json_fallback:
            # Codex round-2: 降级路径同样按 scope 过滤 —— 否则"把 Neo4j 弄挂"
            # 就能绕过封堵。其余 JSON 镜像 (canvas associations / concepts) 仍
            # 移交 CARD-G4-1b: 它们背后的 Cypher 读方法本卡也没封, 两侧同批改。
            return await self._get_score_history_json_fallback(
                concept_id, canvas_name, limit, group_id=group_id
            )

        from app.core.vault_scope import read_group_filter, read_scope_params

        scope_params = read_scope_params(
            group_id, context="neo4j_client.get_concept_score_history"
        )

        query = f"""
        MATCH (n:Node {{id: $conceptId}})<-[cn:CONTAINS_NODE]-(c:Canvas {{path: $canvasPath}})
        WHERE {read_group_filter("n")}
          AND {read_group_filter("c")}
          AND {read_group_filter("cn")}
        MATCH (n)<-[r:SCORED]-(e:Episode)
        WHERE {read_group_filter("r")}
          AND {read_group_filter("e")}
        RETURN r.score as score, r.timestamp as timestamp
        ORDER BY r.timestamp DESC
        LIMIT $limit
        """
        results = await self.run_query(
            query,
            conceptId=concept_id,
            canvasPath=canvas_name,
            limit=limit,
            **scope_params,
        )

        # Reverse to get oldest-to-newest order
        return list(reversed(results))

    async def _get_score_history_json_fallback(
        self, concept_id: str, canvas_name: str, limit: int = 5, group_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get score history from JSON fallback storage.

        Story 31.5 AC-31.5.1: JSON fallback for score history query.

        CARD-G4-1a / Codex round-2 (2026-08-30): 本镜像原先零 group 过滤 ——
        Cypher 侧刚封住的跨 vault 面, 只要 Neo4j 一降级就整个回来 (两个 vault
        同名 canvas 的同 id 节点互相读到对方分数)。**封堵可以被"把 Neo4j 弄挂"
        绕过 = 等于没封**, 所以它不能留在 G4-1b 移交里。写侧
        ``record_score_history`` 的 JSON 分支落 ``group_id: physical``,
        本方法按同一 scope 语义过滤。

        Args:
            concept_id: Concept/Node ID
            canvas_name: Canvas file name
            limit: Maximum number of records
            group_id: 读作用域 (与 Cypher 路径同一解析链)

        Returns:
            List of dicts with score, timestamp fields

        Raises:
            VaultScopeUnresolved: group 解析失败 (拒绝无作用域读取)

        [Source: docs/stories/31.5.story.md#Task-2.2]
        """
        from app.core.vault_scope import group_in_read_scope, require_read_group

        scope = require_read_group(
            group_id, context="neo4j_client._get_score_history_json_fallback"
        )
        results = []

        # Check in-memory relationships for matching concept
        for rel in self._data.get("relationships", []):
            # Match by concept_id or concept_name containing the concept_id
            if (
                rel.get("concept_id") == concept_id
                or rel.get("concept_name", "").find(concept_id) >= 0
                or rel.get("node_id") == concept_id
            ):
                if not group_in_read_scope(rel.get("group_id"), scope):
                    continue
                score = rel.get("last_score")
                timestamp = rel.get("timestamp")

                if score is not None and timestamp:
                    results.append({"score": score, "timestamp": timestamp})

        # Also check score_history array if exists (extended storage)
        score_history = self._data.get("score_history", [])
        for record in score_history:
            if record.get("concept_id") == concept_id or record.get("node_id") == concept_id:
                if not group_in_read_scope(record.get("group_id"), scope):
                    continue
                results.append({"score": record.get("score"), "timestamp": record.get("timestamp")})

        # Sort by timestamp (oldest first) and limit
        results.sort(key=lambda x: x.get("timestamp", ""))
        return results[-limit:] if len(results) > limit else results

    async def record_score_history(
        self,
        concept_id: str,
        canvas_name: str,
        score: int,
        timestamp: Optional[str] = None,
        group_id: Optional[str] = None,
    ) -> bool:
        """
        Record a score to history for difficulty adaptation.

        Story 31.5: Store scores for historical analysis.

        G2-3 (W1): Node/Canvas MERGE 身份含 group_id 复合键; Episode/SCORED
        创建时携带 group_id 属性。解析失败 fail-closed 拒写。

        Args:
            concept_id: Concept/Node ID
            canvas_name: Canvas file name
            score: Score value (0-100)
            timestamp: Optional timestamp (defaults to now)
            group_id: group_id for vault isolation (G2-3 W1)

        Returns:
            True if successful, False on failure or unresolved group_id

        [Source: docs/stories/31.5.story.md#Task-2.2]
        """
        ts = timestamp or datetime.now().isoformat()

        physical_group_id = _resolve_physical_group_id(group_id, canvas_name)
        if not physical_group_id:
            logger.error(
                "[G2-3 W1 fail-closed] record_score_history refused: "
                "unresolved group_id (concept_id=%s, canvas_name=%r)",
                concept_id,
                canvas_name,
            )
            return False

        if self._use_json_fallback:
            # Store in score_history array
            if "score_history" not in self._data:
                self._data["score_history"] = []

            self._data["score_history"].append(
                {
                    "concept_id": concept_id,
                    "canvas_name": canvas_name,
                    "score": score,
                    "timestamp": ts,
                    "group_id": physical_group_id,
                }
            )

            # Keep only last 100 records per concept to avoid unbounded growth
            await self._save_json_data()
            return True

        query = """
        MERGE (n:Node {id: $conceptId, group_id: $groupId})
        MERGE (c:Canvas {path: $canvasPath, group_id: $groupId})
        MERGE (c)-[:CONTAINS_NODE {group_id: $groupId}]->(n)
        CREATE (e:Episode {
            id: randomUUID(),
            type: 'scoring',
            group_id: $groupId,
            timestamp: datetime($timestamp)
        })
        CREATE (e)-[:SCORED {
            score: $score,
            group_id: $groupId,
            timestamp: datetime($timestamp)
        }]->(n)
        RETURN e
        """
        results = await self.run_query(
            query,
            conceptId=concept_id,
            canvasPath=canvas_name,
            score=score,
            timestamp=ts,
            groupId=physical_group_id,
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
        metadata: Optional[Dict[str, Any]] = None,
        group_id: Optional[str] = None,
    ) -> bool:
        """
        Create Canvas association relationship in Neo4j graph.

        Story 36.5 AC-1, AC-2, AC-3: Canvas关联持久化到Neo4j

        G2-3 (W1): Canvas 端点与 ASSOCIATED_WITH 边身份含 group_id 复合键。
        group_id 未提供时经 source_canvas 推导, 解析失败 fail-closed。

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
            logger.error(f"Invalid association_type '{association_type}'. Must be one of: {valid_types}")
            return False

        physical_group_id = _resolve_physical_group_id(group_id, source_canvas)
        if not physical_group_id:
            logger.error(
                "[G2-3 W1 fail-closed] create_canvas_association refused: "
                "unresolved group_id (association_id=%s, source=%r)",
                association_id,
                source_canvas,
            )
            return False

        if self._use_json_fallback:
            return await self._create_association_json_fallback(
                association_id,
                source_canvas,
                target_canvas,
                association_type,
                confidence,
                shared_concepts,
                bidirectional,
                auto_generated,
                metadata,
                physical_group_id,
            )

        query = """
        MERGE (source:Canvas {path: $sourceCanvas, group_id: $groupId})
        MERGE (target:Canvas {path: $targetCanvas, group_id: $groupId})
        MERGE (source)-[r:ASSOCIATED_WITH {association_id: $associationId, group_id: $groupId}]->(target)
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
            autoGenerated=auto_generated,
            groupId=physical_group_id,
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
        metadata: Optional[Dict[str, Any]],
        group_id: str,
    ) -> bool:
        """
        Create canvas association in JSON fallback storage.

        Story 36.5 AC-3: JSON fallback mode preserved.
        G2-3 (W1 镜像): 记录携带 group_id, 匹配用 {association_id, group_id}
        双键 — 与 Cypher 复合身份同型。

        [Source: docs/stories/36.5.story.md#Task-1.1]
        """
        # Initialize canvas_associations list if not exists
        if "canvas_associations" not in self._data:
            self._data["canvas_associations"] = []

        # Check for existing association with same (ID, group) composite key
        existing = next(
            (
                a
                for a in self._data["canvas_associations"]
                if a.get("association_id") == association_id and a.get("group_id") == group_id
            ),
            None,
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
                "group_id": group_id,
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
        limit: int = 100,
        group_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get Canvas associations from Neo4j graph.

        Story 36.5 AC-3: Query canvas associations.

        CARD-G4-1b (2026-08-31) — 读作用域收口 (审计 §5 #11/#12/#13/#14)。
        原先四个分支按 path / type 全库扫, 零 group 过滤: 两个 vault 里同名
        白板的关联会互相读到。写侧 ``create_canvas_association`` 已在 G2-3
        给 Canvas ×2 与 ``ASSOCIATED_WITH`` 三个身份全部落 group_id, 本方法
        按同一锚点对 **source / r / target 三侧逐一过滤** (R1「每个 alias
        逐一过滤」; 只锚 source 会依赖"关联两端不跨组"这个在存量图上不可证
        的前提, 按 R1 只能判 CONDITIONAL)。

        ⚠️ 结构变更说明 (供审阅比对): 原四个分支的 MATCH / RETURN / ORDER /
        LIMIT **逐字相同**, 只有 WHERE 条件不同。四份拷贝各自加三条过滤极易
        漂移 (改三处漏一处 = 一条静默泄漏分支), 故合并为按需拼接 WHERE ——
        与同文件 :meth:`get_learning_history` 的既有写法同型。四种入参组合的
        行为**逐条等价**于原实现 + group 过滤。

        Args:
            canvas_path: Optional filter by source or target canvas path
            association_type: Optional filter by association type
            limit: Maximum results (default: 100)
            group_id: 读作用域 (G4-1b); 省略时按统一链推导

        Returns:
            List of association dicts with all properties

        Raises:
            VaultScopeUnresolved: group 解析失败 (拒绝无作用域读取)

        [Source: docs/stories/36.5.story.md#Task-1.2]
        """
        from app.core.vault_scope import read_group_filter, read_scope_params

        scope_params = read_scope_params(
            group_id, context="neo4j_client.get_canvas_associations"
        )

        if self._use_json_fallback:
            return await self._get_associations_json_fallback(
                canvas_path, association_type, limit, group_id=group_id
            )

        params: Dict[str, Any] = {"limit": limit, **scope_params}
        conditions = [
            read_group_filter("source"),
            read_group_filter("r"),
            read_group_filter("target"),
        ]
        if canvas_path:
            conditions.append("(source.path = $canvasPath OR target.path = $canvasPath)")
            params["canvasPath"] = canvas_path
        if association_type:
            conditions.append("r.association_type = $associationType")
            params["associationType"] = association_type

        where_clause = "\n              AND ".join(conditions)
        query = f"""
        MATCH (source:Canvas)-[r:ASSOCIATED_WITH]->(target:Canvas)
        WHERE {where_clause}
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
        return await self.run_query(query, **params)

    async def _get_associations_json_fallback(
        self,
        canvas_path: Optional[str],
        association_type: Optional[str],
        limit: int,
        group_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get canvas associations from JSON fallback storage.

        Story 36.5 AC-3: JSON fallback mode preserved.

        CARD-G4-1b (2026-08-31): 与 Cypher 侧**同批**加 group 过滤 —— 只封
        Cypher 一侧, "把 Neo4j 弄挂"就能把刚封的跨 vault 面整个拿回来。写侧
        ``_create_association_json_fallback`` 的记录本就带 ``group_id``
        (G2-3 W1 镜像), 本方法按同一 scope 语义过滤。

        ⚠️ **可见面等价的边界**(Codex round-1 MEDIUM, 如实声明): JSON 存储是
        **反规范化**的 —— 一条关联记录只带**一个** ``group_id``, 而 Cypher 侧
        过滤的是 ``source`` / ``r`` / ``target`` **三个** alias。对本仓写侧产出的
        数据 (三者同组) 两侧结果相同; 但对"关系在 A、端点在 B"这类**存量错组**
        数据, Cypher 会拒、JSON 会放行。镜像层无法表达 per-alias 归属, 这是存储
        形态决定的上限, 不是本卡漏改。

        Args:
            canvas_path: Optional filter by source or target canvas path
            association_type: Optional filter by association type
            limit: Maximum results
            group_id: 读作用域 (与 Cypher 路径同一解析链)

        Raises:
            VaultScopeUnresolved: group 解析失败 (拒绝无作用域读取)

        [Source: docs/stories/36.5.story.md#Task-1.2]
        """
        from app.core.vault_scope import group_in_read_scope, require_read_group

        scope = require_read_group(
            group_id, context="neo4j_client._get_associations_json_fallback"
        )
        associations = self._data.get("canvas_associations", [])
        results = []

        for assoc in associations:
            # Apply filters
            if not group_in_read_scope(assoc.get("group_id"), scope):
                continue

            if canvas_path:
                if assoc.get("source_canvas") != canvas_path and assoc.get("target_canvas") != canvas_path:
                    continue

            if association_type:
                if assoc.get("association_type") != association_type:
                    continue

            results.append(assoc)

        # Sort by created_at descending and limit
        results.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return results[:limit]

    async def delete_canvas_association(self, association_id: str, group_id: Optional[str] = None) -> bool:
        """
        Delete Canvas association from Neo4j graph within a group scope.

        Story 36.5 AC-3: Delete canvas association by ID.

        G2-3 (W2): association_id 由调用方外部传入、uuid4 来源不可证,
        不满足 W2 点删窄例外 — MATCH 必须带 group scope。
        group_id 解析失败 fail-closed 拒删。

        Args:
            association_id: Association ID to delete
            group_id: group_id scope for the deletion (G2-3 W2)

        Returns:
            True if deleted, False if not found or refused

        [Source: docs/stories/36.5.story.md#Task-1.3]
        """
        physical_group_id = _resolve_physical_group_id(group_id)
        if not physical_group_id:
            logger.error(
                "[G2-3 W2 fail-closed] delete_canvas_association refused: unresolved group_id (association_id=%s)",
                association_id,
            )
            return False

        if self._use_json_fallback:
            return await self._delete_association_json_fallback(association_id, physical_group_id)

        query = """
        MATCH (source:Canvas)-[r:ASSOCIATED_WITH {association_id: $associationId, group_id: $groupId}]->(target:Canvas)
        DELETE r
        RETURN count(r) as deleted_count
        """
        results = await self.run_query(query, associationId=association_id, groupId=physical_group_id)

        deleted = results[0].get("deleted_count", 0) if results else 0
        if deleted > 0:
            logger.info(f"Deleted canvas association: {association_id}")
            return True
        else:
            logger.warning(f"Canvas association not found: {association_id}")
            return False

    async def _delete_association_json_fallback(self, association_id: str, group_id: str) -> bool:
        """
        Delete canvas association from JSON fallback storage.

        Story 36.5 AC-3: JSON fallback mode preserved.
        G2-3 (W2 镜像): {association_id, group_id} 双键匹配删除。

        [Source: docs/stories/36.5.story.md#Task-1.3]
        """
        associations = self._data.get("canvas_associations", [])
        original_count = len(associations)

        self._data["canvas_associations"] = [
            a for a in associations if not (a.get("association_id") == association_id and a.get("group_id") == group_id)
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
        metadata: Optional[Dict[str, Any]] = None,
        group_id: Optional[str] = None,
    ) -> bool:
        """
        Update Canvas association in Neo4j graph within a group scope.

        Story 36.5 AC-3: Update canvas association properties.

        G2-3 (W5): MATCH...SET 的匹配 scope 与 W2 同口径 — association_id
        来源不可证, 必须叠加 group scope。解析失败 fail-closed 拒更。

        Args:
            association_id: Association ID to update
            association_type: New association type (optional)
            confidence: New confidence score (optional)
            shared_concepts: New shared concepts list (optional)
            bidirectional: New bidirectional flag (optional)
            metadata: Additional metadata (optional)
            group_id: group_id scope for the update (G2-3 W5)

        Returns:
            True if updated, False if not found or refused

        [Source: docs/stories/36.5.story.md#Task-1.4]
        """
        # Validate association_type if provided
        if association_type:
            valid_types = ["prerequisite", "related", "extends", "references"]
            if association_type not in valid_types:
                logger.error(f"Invalid association_type '{association_type}'. Must be one of: {valid_types}")
                return False

        physical_group_id = _resolve_physical_group_id(group_id)
        if not physical_group_id:
            logger.error(
                "[G2-3 W5 fail-closed] update_canvas_association refused: unresolved group_id (association_id=%s)",
                association_id,
            )
            return False

        if self._use_json_fallback:
            return await self._update_association_json_fallback(
                association_id,
                association_type,
                confidence,
                shared_concepts,
                bidirectional,
                metadata,
                physical_group_id,
            )

        # Build SET clause dynamically for provided fields
        set_clauses = ["r.updated_at = datetime()"]
        params: Dict[str, Any] = {
            "associationId": association_id,
            "groupId": physical_group_id,
        }

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
        MATCH (source:Canvas)-[r:ASSOCIATED_WITH {{association_id: $associationId, group_id: $groupId}}]->(target:Canvas)
        SET {", ".join(set_clauses)}
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
        metadata: Optional[Dict[str, Any]],
        group_id: str,
    ) -> bool:
        """
        Update canvas association in JSON fallback storage.

        Story 36.5 AC-3: JSON fallback mode preserved.
        G2-3 (W5 镜像): {association_id, group_id} 双键匹配更新。

        [Source: docs/stories/36.5.story.md#Task-1.4]
        """
        associations = self._data.get("canvas_associations", [])

        for assoc in associations:
            if assoc.get("association_id") == association_id and assoc.get("group_id") == group_id:
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

    async def load_all_canvas_associations(
        self, group_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Load all canvas associations at startup.

        Story 36.5 AC-4: Load existing associations from Neo4j on startup.

        CARD-G4-1b: "all" 指**本作用域内**全部, 不是全库 —— 名字里的 all
        沿用 Story 36.5 原义 (无 path/type 过滤), 作用域仍由
        :meth:`get_canvas_associations` 统一收口。

        Args:
            group_id: 读作用域 (G4-1b); 省略时按统一链推导

        Returns:
            List of all canvas associations in scope

        Raises:
            VaultScopeUnresolved: group 解析失败 (拒绝无作用域读取)

        [Source: docs/stories/36.5.story.md#Task-3.1]
        """
        return await self.get_canvas_associations(limit=10000, group_id=group_id)

    # =========================================================================
    # Canvas Concept Query Methods
    # Story 36.6: 跨Canvas讲座自动发现
    # [Source: docs/stories/36.6.story.md]
    # =========================================================================

    async def get_canvas_concepts(
        self, canvas_path: str, group_id: Optional[str] = None
    ) -> List[str]:
        """
        Get all concepts associated with a Canvas.

        Story 36.6 Task 2.1: Query concepts from Canvas via Neo4j.

        CARD-G4-1b (2026-08-31) — 读作用域收口 (审计 §5 #17)。原先按
        ``Canvas.path`` 全库扫, UNION 两个分支均无 group 过滤: canvas path
        只在 vault 内唯一 (读契约 R3 明列的反例), 两个 vault 里同名白板会
        互相读到对方的节点文本。

        逐 alias 过滤口径:
        - 分支 1 (``CONTAINS_NODE``/``Node``): ``c`` / ``cn`` / ``n`` 三个
          alias 全过滤 —— 写侧 G2-3 给 Canvas / Node / CONTAINS_NODE 三者都
          落了 group_id, 关系侧可查且必须查 (R1)。
        - 分支 2 (``CONTAINS``/``LearningNode``/``HAS_CONCEPT``): 过滤
          ``c`` / ``n`` / ``concept`` **三个节点 alias**; 两个关系类型
          **不过滤**, 因为全仓**没有任何写侧**产出它们 (grep: LearningNode /
          CONTAINS / HAS_CONCEPT 只出现在本文件的读查询与 docstring 里),
          它们身上不存在 group_id 属性 —— 给一个恒不存在的属性加等值过滤,
          只会让这条本就结构性死掉的分支变成"恒空", 掩盖它是死分支的事实,
          属于假门。两端节点都已过滤, R1 的"全覆盖"由此成立 (不依赖
          "关系不跨组"这个不可证前提)。

        Args:
            canvas_path: Canvas file path
            group_id: 读作用域 (G4-1b); 省略时按统一链推导

        Returns:
            List of concept names associated with the Canvas

        Raises:
            VaultScopeUnresolved: group 解析失败 (拒绝无作用域读取)

        [Source: docs/stories/36.6.story.md#Task-2.1]
        """
        from app.core.vault_scope import read_group_filter, read_scope_params

        scope_params = read_scope_params(
            group_id, context="neo4j_client.get_canvas_concepts"
        )

        if self._use_json_fallback:
            return await self._get_canvas_concepts_json_fallback(
                canvas_path, group_id=group_id
            )

        query = f"""
        MATCH (c:Canvas {{path: $canvasPath}})-[cn:CONTAINS_NODE]->(n:Node)
        WHERE n.text IS NOT NULL AND n.text <> ''
          AND {read_group_filter("c")}
          AND {read_group_filter("cn")}
          AND {read_group_filter("n")}
        RETURN DISTINCT n.text as concept_name
        UNION
        MATCH (c:Canvas {{path: $canvasPath}})-[:CONTAINS]->(n:LearningNode)-[:HAS_CONCEPT]->(concept:Concept)
        WHERE {read_group_filter("c")}
          AND {read_group_filter("n")}
          AND {read_group_filter("concept")}
        RETURN DISTINCT concept.name as concept_name
        """
        results = await self.run_query(query, canvasPath=canvas_path, **scope_params)

        return [r["concept_name"] for r in results if r.get("concept_name")]

    async def _get_canvas_concepts_json_fallback(
        self, canvas_path: str, group_id: Optional[str] = None
    ) -> List[str]:
        """
        Get canvas concepts from JSON fallback storage.

        Story 36.6 Task 2.1: JSON fallback mode.

        CARD-G4-1b (2026-08-31): 与 Cypher 侧同批加 group 过滤。

        ⚠️ ``canvas_concepts`` 映射表 (``{path: [names]}``) **不带任何归属
        信息** —— 它是纯 path→names 的字典, 无处施加 scope。本卡的处置是
        **停止读它**并显式记录理由, 而不是"当作本 vault 的数据放行": 后者
        在多 vault 下就是按同名 path 串读。全仓无任何写侧向该键写入 (grep
        ``canvas_concepts`` 只有本方法一处读), 故这不是功能损失。

        ⚠️⚠️ **本镜像与 Cypher 侧不是语义等价的, 本卡也不宣称等价**
        (Codex round-2 Q2 如实声明):

        - Cypher 侧走的是图遍历 ``Canvas -[CONTAINS_NODE]-> Node``;
          JSON 存储里**根本没有 Canvas/Node 实体**, 只有一张扁平的
          ``relationships`` 表, 镜像只能用 ``rel["canvas_path"]`` 近似。
        - 而全仓唯一往 ``self._data["relationships"]`` 写记录的地方是
          ``_handle_merge_learning``, 它写入的键是
          ``id / user_id / concept_id / concept_name / timestamp /
          last_score / next_review / review_count / group_id``
          —— **不含 ``canvas_path``**。也就是说本镜像在真实数据上**恒返回空**,
          它是结构性死分支 (与它背后那三个零调用方的 Cypher 方法同属
          G-PIPE-008 双料僵尸)。

        本卡对这一族给出的保证**只有作用域收口**: 凡是能被本镜像返回的记录,
        必须落在读作用域内 (单测用合成 fixture 锁死这条)。"两条路径返回同一个
        结果集"这种更强的说法在这里**不成立**, 不要据此推断降级前后体验一致。

        Args:
            canvas_path: Canvas file path
            group_id: 读作用域 (与 Cypher 路径同一解析链)

        Returns:
            List of concept names

        Raises:
            VaultScopeUnresolved: group 解析失败 (拒绝无作用域读取)

        [Source: docs/stories/36.6.story.md#Task-2.1]
        """
        from app.core.vault_scope import group_in_read_scope, require_read_group

        scope = require_read_group(
            group_id, context="neo4j_client._get_canvas_concepts_json_fallback"
        )
        concepts = set()

        # Check relationships for concepts linked to this canvas
        for rel in self._data.get("relationships", []):
            if not group_in_read_scope(rel.get("group_id"), scope):
                continue
            # Codex round-1 HIGH-1 整改: **精确**匹配, 与 Cypher 的
            # `MATCH (c:Canvas {path: $canvasPath})` 同形 (原来是子串包含,
            # `x/a.canvas.bak` 会被 `a.canvas` 命中)。
            # Codex round-2 Q2 整改: 去掉 `rel.get("source") == canvas_path`
            # 这一支 —— 全仓没有任何写侧往关系记录里放 `source`, 它是**无法证明
            # 含义**的匹配面 (读契约 R3 反对的那类"来源不可证的标识符")。
            if rel.get("canvas_path") == canvas_path:
                concept_name = rel.get("concept_name") or rel.get("concept")
                if concept_name:
                    concepts.add(concept_name)

        return list(concepts)

    async def find_common_concepts(
        self, canvas1: str, canvas2: str, group_id: Optional[str] = None
    ) -> List[str]:
        """
        Find common concepts between two Canvases.

        Story 36.6 Task 2.2: Query common concepts from Neo4j.

        CARD-G4-1b (2026-08-31) — 读作用域收口 (审计 §5 #18)。原先只按两个
        canvas path 定位、零 group 过滤 —— 而 canvas path 只在 vault 内唯一,
        "两块白板的共同概念"会把另一个 vault 里同名白板的节点算进来。
        四个 alias (``c1`` / ``cn1`` / ``n1`` / 以及 ``c2`` / ``cn2`` / ``n2``)
        逐一过滤, 与 :meth:`get_canvas_concepts` 分支 1 同口径。

        Args:
            canvas1: First Canvas file path
            canvas2: Second Canvas file path
            group_id: 读作用域 (G4-1b); 省略时按统一链推导

        Returns:
            List of common concept names

        Raises:
            VaultScopeUnresolved: group 解析失败 (拒绝无作用域读取)

        [Source: docs/stories/36.6.story.md#Task-2.2]
        """
        from app.core.vault_scope import read_group_filter, read_scope_params

        scope_params = read_scope_params(
            group_id, context="neo4j_client.find_common_concepts"
        )

        if self._use_json_fallback:
            return await self._find_common_concepts_json_fallback(
                canvas1, canvas2, group_id=group_id
            )

        query = f"""
        MATCH (c1:Canvas {{path: $canvas1}})-[cn1:CONTAINS_NODE]->(n1:Node)
        WHERE n1.text IS NOT NULL AND n1.text <> ''
          AND {read_group_filter("c1")}
          AND {read_group_filter("cn1")}
          AND {read_group_filter("n1")}
        WITH COLLECT(DISTINCT n1.text) as concepts1
        MATCH (c2:Canvas {{path: $canvas2}})-[cn2:CONTAINS_NODE]->(n2:Node)
        WHERE n2.text IS NOT NULL AND n2.text <> ''
          AND {read_group_filter("c2")}
          AND {read_group_filter("cn2")}
          AND {read_group_filter("n2")}
        WITH concepts1, COLLECT(DISTINCT n2.text) as concepts2
        RETURN [c IN concepts1 WHERE c IN concepts2] as common_concepts
        """
        results = await self.run_query(
            query, canvas1=canvas1, canvas2=canvas2, **scope_params
        )

        if results and results[0].get("common_concepts"):
            return results[0]["common_concepts"]
        return []

    async def _find_common_concepts_json_fallback(
        self, canvas1: str, canvas2: str, group_id: Optional[str] = None
    ) -> List[str]:
        """
        Find common concepts between two canvases from JSON fallback storage.

        Story 36.6 Task 2.2: JSON fallback mode.

        CARD-G4-1b: scope 透传给两次 ``_get_canvas_concepts_json_fallback``
        —— 交集的两边必须取自**同一个**可见面, 否则"共同概念"会由跨 vault
        的一侧凑出来。

        Args:
            canvas1: First Canvas file path
            canvas2: Second Canvas file path
            group_id: 读作用域 (与 Cypher 路径同一解析链)

        Returns:
            List of common concept names

        Raises:
            VaultScopeUnresolved: group 解析失败 (拒绝无作用域读取)

        [Source: docs/stories/36.6.story.md#Task-2.2]
        """
        concepts1 = set(
            await self._get_canvas_concepts_json_fallback(canvas1, group_id=group_id)
        )
        concepts2 = set(
            await self._get_canvas_concepts_json_fallback(canvas2, group_id=group_id)
        )

        return list(concepts1.intersection(concepts2))

    async def get_all_recent_episodes(
        self, limit: int = 1000, group_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all recent learning episodes across all users.

        Story 38.2 AC-2: Query recent episodes for startup recovery.
        Used by MemoryService._recover_episodes_from_neo4j() to populate
        the in-memory episode cache on restart.

        CARD-G4-1b (2026-08-31) — 读作用域收口 (审计 §5 #19)。原查询是
        ``MATCH (u:User)-[r:LEARNED]->(c:Concept)`` 全库扫 (只有 LIMIT),
        是本族里泄漏面最大的一条: 它的产物直接进**进程级** episode 缓存,
        于是 Tier 3 缓存召回、学习历史兜底全都能看到别的 vault 的记录。
        ``r`` / ``c`` 两个 alias 逐一过滤 (``u:User`` 是跨 vault 共享的身份
        节点, 无 group_id 属性, 不参与过滤 —— 归属由 LEARNED 边与 Concept
        承载)。

        ⚠️ 方法名里的 "all" 从"全库所有 vault"收窄为"**本作用域族内**所有"
        (等值 OR 前缀)。2026-08-30 现网 7691 只读实测: 全库唯一的 LEARNED
        边落在 ``vault__canvas_vault__xn--jhqx6ce6ettpca6420ada2925d``,
        即 active vault 的 punycode 子组 —— 按 active vault 根组 + 前缀语义
        装载, 与收窄前的现网返回相同。语义收窄是真的 (多 vault 部署下不再装
        别的 vault)。

        ⚠️ **"相同"是 2026-08-30 的快照结论, 不是代码不变量**(Codex round-1
        MEDIUM 整改): 它成立的前提是"当时全库只有一条 LEARNED 边且属于 active
        vault"。只要别的 vault 写入了更新的记录、或本 vault 记录数超过
        ``limit``、或同 timestamp 排序不稳定, 收窄前后的 top-N 序列就会不同。
        那属于**预期内的修复**(少装别的 vault), 不是回归 —— 但不可以拿这句
        "相同"当持续保证。

        Args:
            limit: Maximum number of episodes to return (default: 1000)
            group_id: 读作用域 (G4-1b); 省略时按统一链推导。
                恢复路径请**显式**传 active vault 根组 —— 见
                ``memory_service._recover_episodes_from_neo4j`` 的说明。

        Returns:
            List of episode dicts with user_id, concept, score, timestamp, etc.

        Raises:
            VaultScopeUnresolved: group 解析失败 (拒绝无作用域读取)

        [Source: docs/stories/38.2.story.md#Task-1]
        """
        from app.core.vault_scope import read_group_filter, read_scope_params

        scope_params = read_scope_params(
            group_id, context="neo4j_client.get_all_recent_episodes"
        )

        if self._use_json_fallback:
            return await self._get_all_recent_episodes_json(limit, group_id=group_id)

        query = f"""
        MATCH (u:User)-[r:LEARNED]->(c:Concept)
        WHERE {read_group_filter("r")}
          AND {read_group_filter("c")}
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
        # Codex round-1 HIGH-2 整改: 外层再切一次 limit。Cypher 的 `LIMIT $limit`
        # 在**中途降级**时不生效 —— 那条路走 `_run_query_json_fallback` 的关键词
        # 路由, Cypher 文本里的 LIMIT 只是字符串。不补这一刀, "启动即 JSON 模式"
        # (走 `_get_all_recent_episodes_json`, 有切片) 与"运行中切 JSON"会返回
        # 不同条数。
        rows = await self.run_query(query, limit=limit, **scope_params)
        # 同 get_concept_history (独立审计 HIGH): temporal → ISO 串。恢复进
        # 进程级 episode 缓存的记录若带 DateTime 对象, 与内存侧的字符串
        # timestamp 混在一起, 去重键 / 排序 / 与 JSON 镜像对拍全都会错型。
        return _iso_timestamps(rows or [])[:limit]

    async def _get_all_recent_episodes_json(
        self, limit: int = 1000, group_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        JSON fallback: get all recent episodes from relationships.

        Story 38.2 AC-2: JSON fallback for episode recovery.

        CARD-G4-1b: 与 Cypher 侧同批加 scope 过滤 —— 单侧封堵可被"把 Neo4j
        弄挂"绕过。

        ⚠️ **可见面等价的边界**(同 ``_get_associations_json_fallback``): 本镜像
        按记录自带的单个 ``group_id`` 过滤, Cypher 侧过滤 ``r`` / ``c`` 两个
        alias。本仓写侧两者同组 ⇒ 结果相同; 存量错组数据下 Cypher 更严。

        Args:
            limit: Maximum number of episodes to return
            group_id: 读作用域 (与 Cypher 路径同一解析链)

        Raises:
            VaultScopeUnresolved: group 解析失败 (拒绝无作用域读取)

        [Source: docs/stories/38.2.story.md#Task-1.2]
        """
        from app.core.vault_scope import group_in_read_scope, require_read_group

        scope = require_read_group(
            group_id, context="neo4j_client._get_all_recent_episodes_json"
        )
        rels = self._data.get("relationships", [])
        results = []
        for rel in rels:
            if not group_in_read_scope(rel.get("group_id"), scope):
                continue
            # Field mapping: JSON storage uses different names than Cypher output
            # JSON "concept_name" → output "concept" (matches Cypher c.name as concept)
            # JSON "last_score" → output "score" (matches Cypher r.score as score)
            results.append(
                {
                    "user_id": rel.get("user_id"),
                    "concept": rel.get("concept_name"),
                    "concept_id": rel.get("concept_id"),
                    "score": rel.get("last_score"),
                    "timestamp": rel.get("timestamp"),
                    "group_id": rel.get("group_id"),
                    "review_count": rel.get("review_count", 0),
                }
            )
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
