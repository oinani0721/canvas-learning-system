# Canvas Learning System - Error Aggregator Service
# Story 7.4: 出题难度匹配与提取质量验证
# [Source: _bmad-output/implementation-artifacts/7-4-difficulty-matching-extraction-validation.md]
"""
Automatic error classification and time-window aggregation.

Classifies errors into 4 categories based on exception type hierarchy:
  - LLM errors: LiteLLM API errors (rate limit, auth, timeout)
  - Network errors: connection/communication failures
  - Algorithm errors: internal computation errors (BKT/FSRS ValueError, etc.)
  - Data errors: storage read/write failures (Neo4j, SQLite, LanceDB)

Classification uses exception type matching (no LLM needed):
  exact class name > parent class > module origin > default "uncategorized"

Time-window aggregation: 24h / 7d / 30d sliding windows via SQLite queries.

[Source: Story 7.4 AC-6]
[Source: architecture.md#Process Patterns — error handling layered]
"""

import asyncio
import logging
import traceback
from datetime import datetime, timedelta, timezone
from typing import Optional

import aiosqlite

from app.models.qa_models import ErrorAggregation, ErrorCategoryCounts

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# Error Classification Rules
# [Source: Story 7.4 Dev Notes — classification rules table]
# ═══════════════════════════════════════════════════════════════════════════════

# Exception class names -> category (exact match, highest priority)
_EXACT_CLASS_MAP: dict[str, str] = {
    # LLM errors (LiteLLM / OpenAI)
    "APIError": "llm_error",
    "RateLimitError": "llm_error",
    "AuthenticationError": "llm_error",
    "APIConnectionError": "llm_error",
    "APITimeoutError": "llm_error",
    "ServiceUnavailableError": "llm_error",
    "BadRequestError": "llm_error",
    "InternalServerError": "llm_error",
    "NotFoundError": "llm_error",
    "UnprocessableEntityError": "llm_error",
    "ContextWindowExceededError": "llm_error",
    "ContentPolicyViolationError": "llm_error",
    "OpenAIError": "llm_error",
    # Network errors
    "ConnectionError": "network_error",
    "TimeoutError": "network_error",
    "ConnectTimeout": "network_error",
    "ReadTimeout": "network_error",
    "HTTPError": "network_error",
    "ConnectionRefusedError": "network_error",
    "ConnectionResetError": "network_error",
    "BrokenPipeError": "network_error",
    "HTTPStatusError": "network_error",
    "ConnectError": "network_error",
    # Algorithm errors
    "ValueError": "algorithm_error",
    "KeyError": "algorithm_error",
    "IndexError": "algorithm_error",
    "ZeroDivisionError": "algorithm_error",
    "ArithmeticError": "algorithm_error",
    "OverflowError": "algorithm_error",
    "FloatingPointError": "algorithm_error",
    # Data errors
    "DatabaseError": "data_error",
    "OperationalError": "data_error",
    "IntegrityError": "data_error",
    "ProgrammingError": "data_error",
    "DataError": "data_error",
    "Neo4jError": "data_error",
    "ServiceUnavailable": "data_error",
    "SessionExpired": "data_error",
}

# Module name substrings -> category (fallback when exact match fails)
_MODULE_HINT_MAP: dict[str, str] = {
    "litellm": "llm_error",
    "openai": "llm_error",
    "httpx": "network_error",
    "aiohttp": "network_error",
    "urllib": "network_error",
    "requests": "network_error",
    "neo4j": "data_error",
    "aiosqlite": "data_error",
    "sqlite3": "data_error",
    "lancedb": "data_error",
}


def classify_error(exc: BaseException) -> str:
    """Classify an exception into one of the 4 error categories.

    Priority: exact class name > parent class names > module origin > 'uncategorized'.

    Args:
        exc: The exception to classify.

    Returns:
        Error category string.

    [Source: Story 7.4 Task 4.2 — error classifier]
    """
    # 1. Exact class name match
    cls_name = type(exc).__name__
    if cls_name in _EXACT_CLASS_MAP:
        return _EXACT_CLASS_MAP[cls_name]

    # 2. Parent class name match (MRO traversal)
    for parent in type(exc).__mro__:
        if parent.__name__ in _EXACT_CLASS_MAP:
            return _EXACT_CLASS_MAP[parent.__name__]

    # 3. Module origin hint
    module = type(exc).__module__ or ""
    for hint, category in _MODULE_HINT_MAP.items():
        if hint in module.lower():
            return category

    return "uncategorized"


# ═══════════════════════════════════════════════════════════════════════════════
# SQL
# ═══════════════════════════════════════════════════════════════════════════════

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS qa_error_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    error_type TEXT NOT NULL,
    source_module TEXT DEFAULT '',
    stack_summary TEXT DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);
"""

_CREATE_INDEX = (
    "CREATE INDEX IF NOT EXISTS idx_error_logs_created ON qa_error_logs(created_at);"
)

_INSERT_ERROR = """
INSERT INTO qa_error_logs (category, error_type, source_module, stack_summary, created_at)
VALUES (?, ?, ?, ?, ?);
"""

_COUNT_BY_CATEGORY = """
SELECT category, COUNT(*) AS cnt
FROM qa_error_logs
WHERE created_at >= ?
GROUP BY category;
"""


# ═══════════════════════════════════════════════════════════════════════════════
# ErrorAggregator
# ═══════════════════════════════════════════════════════════════════════════════


class ErrorAggregator:
    """Classifies and aggregates errors across time windows.

    [Source: Story 7.4 Task 4]
    """

    def __init__(self, db_path: str):
        self._db_path = db_path
        self._initialized = False
        self._init_lock = asyncio.Lock()

    async def _ensure_init(self) -> None:
        if self._initialized:
            return
        async with self._init_lock:
            if self._initialized:
                return
            async with aiosqlite.connect(self._db_path) as db:
                await db.execute(_CREATE_TABLE)
                await db.execute(_CREATE_INDEX)
                await db.commit()
            self._initialized = True
            logger.info("[Story 7.4] ErrorAggregator initialized")

    # ───────────────────────────────────────────────────────────────────────
    # Record an error
    # ───────────────────────────────────────────────────────────────────────

    async def record_error(self, exc: BaseException) -> str:
        """Classify and persist an error occurrence.

        Args:
            exc: The exception that occurred.

        Returns:
            The category the error was classified into.

        [Source: Story 7.4 Task 4.2, 4.4]
        """
        await self._ensure_init()

        category = classify_error(exc)
        error_type = type(exc).__name__
        source_module = type(exc).__module__ or ""

        # Compact stack summary (last 3 frames)
        tb_lines = traceback.format_exception(type(exc), exc, exc.__traceback__)
        stack_summary = "".join(tb_lines[-3:])[:500] if tb_lines else ""

        now = datetime.now(timezone.utc).isoformat()

        try:
            async with aiosqlite.connect(self._db_path) as db:
                await db.execute(
                    _INSERT_ERROR,
                    (category, error_type, source_module, stack_summary, now),
                )
                await db.commit()
        except (OSError, aiosqlite.Error) as e:
            logger.error(f"[Story 7.4] Failed to persist error log: {e}")

        logger.debug(
            f"[Story 7.4] Error recorded: category={category} type={error_type}"
        )

        return category

    # ───────────────────────────────────────────────────────────────────────
    # Aggregation
    # ───────────────────────────────────────────────────────────────────────

    async def get_aggregation(self) -> ErrorAggregation:
        """Compute error aggregation across 24h / 7d / 30d windows.

        [Source: Story 7.4 Task 4.3, 4.5 — time-window aggregation]
        """
        await self._ensure_init()

        now = datetime.now(timezone.utc)

        async with aiosqlite.connect(self._db_path) as db:
            counts_24h = await self._count_since(db, now - timedelta(hours=24))
            counts_7d = await self._count_since(db, now - timedelta(days=7))
            counts_30d = await self._count_since(db, now - timedelta(days=30))

        return ErrorAggregation(
            last_24h=counts_24h,
            last_7d=counts_7d,
            last_30d=counts_30d,
        )

    async def _count_since(
        self, db: aiosqlite.Connection, since: datetime
    ) -> ErrorCategoryCounts:
        """Count errors by category since a given timestamp."""
        since_iso = since.isoformat()
        cursor = await db.execute(_COUNT_BY_CATEGORY, (since_iso,))
        rows = await cursor.fetchall()

        counts = ErrorCategoryCounts()
        for row in rows:
            category, cnt = row[0], row[1]
            if category == "llm_error":
                counts.llm_errors = cnt
            elif category == "network_error":
                counts.network_errors = cnt
            elif category == "algorithm_error":
                counts.algorithm_errors = cnt
            elif category == "data_error":
                counts.data_errors = cnt
            else:
                counts.uncategorized = cnt

        return counts


# ═══════════════════════════════════════════════════════════════════════════════
# Module-level singleton
# ═══════════════════════════════════════════════════════════════════════════════

_instance: Optional[ErrorAggregator] = None


def get_error_aggregator(db_path: Optional[str] = None) -> ErrorAggregator:
    """Get or create the singleton ErrorAggregator instance."""
    global _instance
    if _instance is None:
        from pathlib import Path

        if db_path is None:
            backend_dir = Path(__file__).parent.parent.parent
            data_dir = backend_dir / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(data_dir / "qa_metrics.db")
        _instance = ErrorAggregator(db_path)
    return _instance
