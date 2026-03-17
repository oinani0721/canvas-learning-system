# Canvas Learning System - Cost Tracker
# Story 7.2: LLM 调用日志与 Token 追踪
# [Source: _bmad-output/implementation-artifacts/7-2-llm-logging-token-tracking.md]
"""
Token consumption aggregation service with SQLite persistence.

Provides:
- SQLite storage for llm_call_logs and llm_call_logs_daily tables
- Aggregation queries by time period and task type
- 90-day log rotation with daily compression
- Batch insert for high-throughput logging

[Source: Story 7.2 AC #3, #4 — Task type statistics + error aggregation]
[Source: architecture.md#Infrastructure — 100% LLM call logging + Token cost tracking]
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiosqlite

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════════════════════

# Default DB path relative to backend/
_BACKEND_DIR = Path(__file__).parent.parent.parent
_DEFAULT_DB_PATH = _BACKEND_DIR / "data" / "llm_call_logs.db"

LOG_RETENTION_DAYS = 90

# ═══════════════════════════════════════════════════════════════════════════════
# SQL Statements
# [Source: Story 7.2 Dev Notes — SQLite Storage Design]
# ═══════════════════════════════════════════════════════════════════════════════

_CREATE_LOGS_TABLE = """
CREATE TABLE IF NOT EXISTS llm_call_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id TEXT NOT NULL,
    task_type TEXT NOT NULL,
    model_name TEXT NOT NULL,
    input_tokens INTEGER NOT NULL DEFAULT 0,
    output_tokens INTEGER NOT NULL DEFAULT 0,
    total_tokens INTEGER NOT NULL DEFAULT 0,
    latency_ms INTEGER NOT NULL DEFAULT 0,
    estimated_cost_usd REAL,
    status TEXT NOT NULL DEFAULT 'success',
    error_type TEXT,
    error_message TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);
"""

_CREATE_LOGS_INDICES = [
    "CREATE INDEX IF NOT EXISTS idx_llm_logs_task_type ON llm_call_logs(task_type);",
    "CREATE INDEX IF NOT EXISTS idx_llm_logs_created_at ON llm_call_logs(created_at);",
    "CREATE INDEX IF NOT EXISTS idx_llm_logs_status ON llm_call_logs(status);",
]

_CREATE_DAILY_TABLE = """
CREATE TABLE IF NOT EXISTS llm_call_logs_daily (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    task_type TEXT NOT NULL,
    total_calls INTEGER NOT NULL DEFAULT 0,
    success_calls INTEGER NOT NULL DEFAULT 0,
    failure_calls INTEGER NOT NULL DEFAULT 0,
    total_input_tokens INTEGER NOT NULL DEFAULT 0,
    total_output_tokens INTEGER NOT NULL DEFAULT 0,
    total_tokens INTEGER NOT NULL DEFAULT 0,
    total_cost_usd REAL DEFAULT 0.0,
    avg_latency_ms REAL DEFAULT 0.0,
    error_llm_count INTEGER NOT NULL DEFAULT 0,
    error_network_count INTEGER NOT NULL DEFAULT 0,
    error_config_count INTEGER NOT NULL DEFAULT 0,
    UNIQUE(date, task_type)
);
"""

_CREATE_DAILY_INDEX = (
    "CREATE INDEX IF NOT EXISTS idx_llm_daily_date ON llm_call_logs_daily(date);"
)

_INSERT_LOG = """
INSERT INTO llm_call_logs (
    request_id, task_type, model_name,
    input_tokens, output_tokens, total_tokens,
    latency_ms, estimated_cost_usd, status,
    error_type, error_message, created_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
"""

_AGGREGATE_SUMMARY = """
SELECT
    COUNT(*) as total_calls,
    COALESCE(SUM(total_tokens), 0) as total_tokens,
    COALESCE(SUM(input_tokens), 0) as total_input_tokens,
    COALESCE(SUM(output_tokens), 0) as total_output_tokens,
    COALESCE(SUM(estimated_cost_usd), 0.0) as total_cost_usd,
    COALESCE(AVG(latency_ms), 0) as avg_latency_ms,
    COALESCE(
        CAST(SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) AS REAL)
        / NULLIF(COUNT(*), 0),
        1.0
    ) as success_rate
FROM llm_call_logs
WHERE created_at >= ? AND created_at < ?
"""

_AGGREGATE_BY_TASK = """
SELECT
    task_type,
    COUNT(*) as calls,
    COALESCE(SUM(total_tokens), 0) as tokens,
    COALESCE(SUM(estimated_cost_usd), 0.0) as cost_usd
FROM llm_call_logs
WHERE created_at >= ? AND created_at < ?
GROUP BY task_type
ORDER BY calls DESC
"""

_AGGREGATE_BY_DAY = """
SELECT
    SUBSTR(created_at, 1, 10) as date,
    COUNT(*) as calls,
    COALESCE(SUM(total_tokens), 0) as tokens,
    COALESCE(SUM(estimated_cost_usd), 0.0) as cost_usd
FROM llm_call_logs
WHERE created_at >= ? AND created_at < ?
GROUP BY SUBSTR(created_at, 1, 10)
ORDER BY date ASC
"""

_AGGREGATE_ERRORS = """
SELECT
    COALESCE(error_type, 'UNKNOWN') as error_type,
    COUNT(*) as count
FROM llm_call_logs
WHERE created_at >= ? AND created_at < ?
    AND status = 'failure'
GROUP BY error_type
"""

_COMPRESS_TO_DAILY = """
INSERT OR REPLACE INTO llm_call_logs_daily (
    date, task_type, total_calls, success_calls, failure_calls,
    total_input_tokens, total_output_tokens, total_tokens,
    total_cost_usd, avg_latency_ms,
    error_llm_count, error_network_count, error_config_count
)
SELECT
    SUBSTR(created_at, 1, 10) as date,
    task_type,
    COUNT(*) as total_calls,
    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_calls,
    SUM(CASE WHEN status = 'failure' THEN 1 ELSE 0 END) as failure_calls,
    COALESCE(SUM(input_tokens), 0) as total_input_tokens,
    COALESCE(SUM(output_tokens), 0) as total_output_tokens,
    COALESCE(SUM(total_tokens), 0) as total_tokens,
    COALESCE(SUM(estimated_cost_usd), 0.0) as total_cost_usd,
    COALESCE(AVG(latency_ms), 0) as avg_latency_ms,
    SUM(CASE WHEN error_type = 'LLM_ERROR' THEN 1 ELSE 0 END) as error_llm_count,
    SUM(CASE WHEN error_type = 'NETWORK_ERROR' THEN 1 ELSE 0 END) as error_network_count,
    SUM(CASE WHEN error_type = 'CONFIG_ERROR' THEN 1 ELSE 0 END) as error_config_count
FROM llm_call_logs
WHERE created_at < ?
GROUP BY SUBSTR(created_at, 1, 10), task_type;
"""

_DELETE_OLD_LOGS = """
DELETE FROM llm_call_logs WHERE created_at < ?;
"""


# ═══════════════════════════════════════════════════════════════════════════════
# CostTracker Service (Task 2.1, 2.3, 2.4, 2.6)
# ═══════════════════════════════════════════════════════════════════════════════


class CostTracker:
    """Token consumption aggregation service with SQLite persistence.

    [Source: Story 7.2 Task 2 — Token consumption + persistence]

    Provides:
    - Batch insert for log entries
    - Period-based aggregation queries (summary, by_task, by_day, errors)
    - 90-day log rotation with daily compression
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        """Initialize CostTracker.

        Args:
            db_path: Path to SQLite database file. Defaults to data/llm_call_logs.db
        """
        self._db_path = db_path or str(_DEFAULT_DB_PATH)
        self._initialized = False
        self._rotation_task: Optional[asyncio.Task] = None
        self._running = False

    async def initialize(self) -> None:
        """Initialize SQLite database and create tables.

        [Source: Story 7.2 Task 2.3 — SQLite table creation]
        """
        # Ensure data directory exists
        db_dir = os.path.dirname(self._db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(_CREATE_LOGS_TABLE)
            for idx_sql in _CREATE_LOGS_INDICES:
                await db.execute(idx_sql)
            await db.execute(_CREATE_DAILY_TABLE)
            await db.execute(_CREATE_DAILY_INDEX)
            await db.commit()

        self._initialized = True
        self._running = True
        logger.info(f"[Story 7.2] CostTracker initialized: {self._db_path}")

    async def start_rotation(self) -> None:
        """Start background log rotation task (runs daily).

        [Source: Story 7.2 Task 2.6 — 90-day retention with daily compression]
        """
        self._rotation_task = asyncio.create_task(self._rotation_loop())
        logger.info("[Story 7.2] Log rotation task started (daily cycle)")

    async def stop(self) -> None:
        """Stop the cost tracker and cancel rotation task."""
        self._running = False
        if self._rotation_task and not self._rotation_task.done():
            self._rotation_task.cancel()
            try:
                await self._rotation_task
            except asyncio.CancelledError:
                pass
        logger.info("[Story 7.2] CostTracker stopped")

    async def insert_logs(self, entries: List[Any]) -> None:
        """Batch insert log entries into SQLite.

        [Source: Story 7.2 Dev Notes — Batch write optimization]

        Args:
            entries: List of LLMCallLog entries to persist
        """
        if not entries:
            return

        if not self._initialized:
            logger.warning("[Story 7.2] CostTracker not initialized, skipping insert")
            return

        try:
            async with aiosqlite.connect(self._db_path) as db:
                rows = [
                    (
                        e.request_id,
                        e.task_type,
                        e.model_name,
                        e.input_tokens,
                        e.output_tokens,
                        e.total_tokens,
                        e.latency_ms,
                        e.estimated_cost_usd,
                        e.status,
                        e.error_type,
                        e.error_message,
                        e.created_at,
                    )
                    for e in entries
                ]
                await db.executemany(_INSERT_LOG, rows)
                await db.commit()

            logger.debug(f"[Story 7.2] Inserted {len(entries)} LLM call logs")
        except Exception as e:
            logger.error(f"[Story 7.2] Failed to insert logs: {e}")
            raise

    async def get_stats_by_period(
        self,
        start: str,
        end: str,
        task_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get aggregated statistics for a time period.

        [Source: Story 7.2 Task 2.4 — Aggregation queries]
        [Source: Story 7.2 AC #7 — API response format]

        Args:
            start: Period start (ISO 8601, e.g. '2026-03-10T00:00:00Z')
            end: Period end (ISO 8601)
            task_type: Optional filter by task type

        Returns:
            Dict with summary, by_task, by_day, errors keys
        """
        if not self._initialized:
            return self._empty_stats()

        try:
            async with aiosqlite.connect(self._db_path) as db:
                db.row_factory = aiosqlite.Row

                # Summary
                summary_sql = _AGGREGATE_SUMMARY
                params: List[Any] = [start, end]
                if task_type:
                    summary_sql += " AND task_type = ?"
                    params.append(task_type)

                cursor = await db.execute(summary_sql, params)
                row = await cursor.fetchone()

                summary = {
                    "total_calls": row["total_calls"] if row else 0,
                    "total_tokens": row["total_tokens"] if row else 0,
                    "total_input_tokens": row["total_input_tokens"] if row else 0,
                    "total_output_tokens": row["total_output_tokens"] if row else 0,
                    "total_cost_usd": round(row["total_cost_usd"], 4) if row else 0.0,
                    "avg_latency_ms": round(row["avg_latency_ms"], 1) if row else 0.0,
                    "success_rate": round(row["success_rate"], 4) if row else 1.0,
                }

                # By task type
                by_task_sql = _AGGREGATE_BY_TASK
                by_task_params: List[Any] = [start, end]
                if task_type:
                    by_task_sql = by_task_sql.replace(
                        "GROUP BY task_type",
                        "AND task_type = ? GROUP BY task_type",
                    )
                    by_task_params.append(task_type)

                cursor = await db.execute(by_task_sql, by_task_params)
                by_task_rows = await cursor.fetchall()
                by_task = [
                    {
                        "task_type": r["task_type"],
                        "calls": r["calls"],
                        "tokens": r["tokens"],
                        "cost_usd": round(r["cost_usd"], 4),
                    }
                    for r in by_task_rows
                ]

                # By day
                by_day_sql = _AGGREGATE_BY_DAY
                by_day_params: List[Any] = [start, end]
                if task_type:
                    by_day_sql = by_day_sql.replace(
                        "GROUP BY SUBSTR(created_at, 1, 10)",
                        "AND task_type = ? GROUP BY SUBSTR(created_at, 1, 10)",
                    )
                    by_day_params.append(task_type)

                cursor = await db.execute(by_day_sql, by_day_params)
                by_day_rows = await cursor.fetchall()
                by_day = [
                    {
                        "date": r["date"],
                        "calls": r["calls"],
                        "tokens": r["tokens"],
                        "cost_usd": round(r["cost_usd"], 4),
                    }
                    for r in by_day_rows
                ]

                # Errors
                error_sql = _AGGREGATE_ERRORS
                error_params: List[Any] = [start, end]

                cursor = await db.execute(error_sql, error_params)
                error_rows = await cursor.fetchall()

                error_total = sum(r["count"] for r in error_rows)
                by_error_type = {r["error_type"]: r["count"] for r in error_rows}

                errors = {
                    "total": error_total,
                    "by_type": by_error_type,
                }

                return {
                    "summary": summary,
                    "by_task": by_task,
                    "by_day": by_day,
                    "errors": errors,
                }

        except Exception as e:
            logger.error(f"[Story 7.2] Failed to get stats: {e}")
            return self._empty_stats()

    async def get_health_probe(self) -> Dict[str, Any]:
        """Get LLM pipeline health probe data.

        [Source: Story 7.2 Task 5.4 — Pipeline health probe]

        Returns:
            Dict with success_rate and avg_latency_ms for last 100 calls
        """
        if not self._initialized:
            return {"success_rate": 1.0, "avg_latency_ms": 0, "total_recent": 0}

        try:
            async with aiosqlite.connect(self._db_path) as db:
                db.row_factory = aiosqlite.Row

                cursor = await db.execute(
                    """
                    SELECT
                        COUNT(*) as total,
                        COALESCE(
                            CAST(SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) AS REAL)
                            / NULLIF(COUNT(*), 0),
                            1.0
                        ) as success_rate,
                        COALESCE(AVG(latency_ms), 0) as avg_latency_ms
                    FROM (
                        SELECT status, latency_ms
                        FROM llm_call_logs
                        ORDER BY id DESC
                        LIMIT 100
                    )
                    """
                )
                row = await cursor.fetchone()
                return {
                    "success_rate": round(row["success_rate"], 4) if row else 1.0,
                    "avg_latency_ms": round(row["avg_latency_ms"], 1) if row else 0.0,
                    "total_recent": row["total"] if row else 0,
                }
        except Exception as e:
            logger.warning(f"[Story 7.2] Health probe failed: {e}")
            return {"success_rate": 1.0, "avg_latency_ms": 0, "total_recent": 0}

    async def rotate_logs(self) -> Dict[str, int]:
        """Rotate logs: compress >90 day old entries to daily summaries.

        [Source: Story 7.2 Task 2.6 — 90-day retention + daily compression]

        Returns:
            Dict with compressed and deleted counts
        """
        if not self._initialized:
            return {"compressed": 0, "deleted": 0}

        cutoff = (
            datetime.now(timezone.utc) - timedelta(days=LOG_RETENTION_DAYS)
        ).strftime("%Y-%m-%dT%H:%M:%S.000Z")

        try:
            async with aiosqlite.connect(self._db_path) as db:
                # Step 1: Compress old entries into daily summaries
                await db.execute(_COMPRESS_TO_DAILY, [cutoff])

                # Step 2: Count rows to be deleted
                cursor = await db.execute(
                    "SELECT COUNT(*) FROM llm_call_logs WHERE created_at < ?",
                    [cutoff],
                )
                row = await cursor.fetchone()
                delete_count = row[0] if row else 0

                # Step 3: Delete old detail rows
                if delete_count > 0:
                    await db.execute(_DELETE_OLD_LOGS, [cutoff])

                await db.commit()

            if delete_count > 0:
                logger.info(
                    f"[Story 7.2] Log rotation: compressed and deleted {delete_count} "
                    f"entries older than {LOG_RETENTION_DAYS} days"
                )
            return {"compressed": delete_count, "deleted": delete_count}

        except Exception as e:
            logger.error(f"[Story 7.2] Log rotation failed: {e}")
            return {"compressed": 0, "deleted": 0}

    async def _rotation_loop(self) -> None:
        """Background rotation task, runs once per day."""
        while self._running:
            try:
                # Wait 24 hours between rotations
                await asyncio.sleep(86400)
                await self.rotate_logs()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"[Story 7.2] Rotation loop error: {e}")

    @staticmethod
    def _empty_stats() -> Dict[str, Any]:
        """Return empty statistics structure."""
        return {
            "summary": {
                "total_calls": 0,
                "total_tokens": 0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_cost_usd": 0.0,
                "avg_latency_ms": 0.0,
                "success_rate": 1.0,
            },
            "by_task": [],
            "by_day": [],
            "errors": {"total": 0, "by_type": {}},
        }


# ═══════════════════════════════════════════════════════════════════════════════
# Module-level singleton
# ═══════════════════════════════════════════════════════════════════════════════

_cost_tracker_instance: Optional[CostTracker] = None


async def get_cost_tracker(db_path: Optional[str] = None) -> CostTracker:
    """Get or create the CostTracker singleton.

    Args:
        db_path: Optional custom DB path (only used on first call)

    Returns:
        Initialized CostTracker instance
    """
    global _cost_tracker_instance
    if _cost_tracker_instance is None:
        _cost_tracker_instance = CostTracker(db_path=db_path)
        await _cost_tracker_instance.initialize()
    return _cost_tracker_instance


async def cleanup_cost_tracker() -> None:
    """Cleanup the CostTracker singleton."""
    global _cost_tracker_instance
    if _cost_tracker_instance is not None:
        await _cost_tracker_instance.stop()
        _cost_tracker_instance = None
