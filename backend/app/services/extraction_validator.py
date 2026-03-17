# Canvas Learning System - Extraction Validator Service
# Story 7.4: 出题难度匹配与提取质量验证
# [Source: _bmad-output/implementation-artifacts/7-4-difficulty-matching-extraction-validation.md]
"""
Human-review service for structured extraction results from conversation archives.

Provides:
  - Storage of extraction records (original text + extracted content + type)
  - Annotation submission (correct / incorrect / partial)
  - Per-type accuracy statistics with alerting
  - Paginated query with type filtering

Data source: conversation_archive.py Hot->Warm archival pipeline extracts
errors, tips, and key Q&A pairs via LLM. This service stores them for
human spot-check validation.

[Source: Story 7.4 AC-3, AC-4]
[Source: architecture.md#Cross-Cutting — 算法管道完整性]
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

import aiosqlite

from app.models.qa_models import (
    ExtractionRecord,
    ExtractionRecordPage,
    ExtractionStats,
    TypeStats,
)

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# SQL Statements
# ═══════════════════════════════════════════════════════════════════════════════

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS qa_extraction_records (
    id TEXT PRIMARY KEY,
    source_session_id TEXT NOT NULL,
    source_node_id TEXT NOT NULL,
    original_text TEXT NOT NULL,
    extracted_content TEXT NOT NULL,
    extraction_type TEXT NOT NULL,
    extraction_subtype TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    annotation TEXT,
    annotated_at TEXT
);
"""

_CREATE_INDICES = [
    "CREATE INDEX IF NOT EXISTS idx_extraction_type ON qa_extraction_records(extraction_type);",
    "CREATE INDEX IF NOT EXISTS idx_extraction_annotation ON qa_extraction_records(annotation);",
    "CREATE INDEX IF NOT EXISTS idx_extraction_created ON qa_extraction_records(created_at);",
]

_INSERT_RECORD = """
INSERT INTO qa_extraction_records
    (id, source_session_id, source_node_id, original_text, extracted_content,
     extraction_type, extraction_subtype, created_at)
VALUES (?, ?, ?, ?, ?, ?, ?, ?);
"""

_UPDATE_ANNOTATION = """
UPDATE qa_extraction_records
SET annotation = ?, annotated_at = ?
WHERE id = ?;
"""

_SELECT_PAGE = """
SELECT id, source_session_id, source_node_id, original_text, extracted_content,
       extraction_type, extraction_subtype, created_at, annotation, annotated_at
FROM qa_extraction_records
{where}
ORDER BY created_at DESC
LIMIT ? OFFSET ?;
"""

_COUNT = """
SELECT COUNT(*) FROM qa_extraction_records {where};
"""

_STATS_TOTAL = "SELECT COUNT(*) FROM qa_extraction_records;"

_STATS_ANNOTATED = "SELECT COUNT(*) FROM qa_extraction_records WHERE annotation IS NOT NULL;"

_STATS_CORRECT = "SELECT COUNT(*) FROM qa_extraction_records WHERE annotation = 'correct';"

_STATS_BY_TYPE = """
SELECT extraction_type,
       COUNT(*) AS total,
       SUM(CASE WHEN annotation = 'correct' THEN 1 ELSE 0 END) AS correct_count
FROM qa_extraction_records
WHERE annotation IS NOT NULL
GROUP BY extraction_type;
"""

ACCURACY_ALERT_THRESHOLD = 0.8


# ═══════════════════════════════════════════════════════════════════════════════
# ExtractionValidator
# ═══════════════════════════════════════════════════════════════════════════════


class ExtractionValidator:
    """Stores and validates structured extraction results for human review.

    [Source: Story 7.4 Task 2]
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
                for idx_sql in _CREATE_INDICES:
                    await db.execute(idx_sql)
                await db.commit()
            self._initialized = True
            logger.info("[Story 7.4] ExtractionValidator initialized")

    # ───────────────────────────────────────────────────────────────────────
    # Write: store extraction record
    # ───────────────────────────────────────────────────────────────────────

    async def store_record(
        self,
        source_session_id: str,
        source_node_id: str,
        original_text: str,
        extracted_content: str,
        extraction_type: str,
        extraction_subtype: Optional[str] = None,
    ) -> ExtractionRecord:
        """Store a new extraction record for later human review.

        Called by conversation_archive.py during Hot->Warm archival.

        Args:
            source_session_id: Conversation session ID.
            source_node_id: Canvas node ID.
            original_text: Original conversation fragment.
            extracted_content: LLM-extracted structured content.
            extraction_type: One of 'error', 'tip', 'key_qa'.
            extraction_subtype: Optional error subtype.

        Returns:
            The created ExtractionRecord.

        [Source: Story 7.4 Task 2.3]
        """
        await self._ensure_init()

        record_id = str(uuid4())
        now = datetime.now(timezone.utc).isoformat()

        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                _INSERT_RECORD,
                (
                    record_id,
                    source_session_id,
                    source_node_id,
                    original_text,
                    extracted_content,
                    extraction_type,
                    extraction_subtype,
                    now,
                ),
            )
            await db.commit()

        logger.info(
            f"[Story 7.4] Stored extraction record {record_id} type={extraction_type} subtype={extraction_subtype}"
        )

        return ExtractionRecord(
            id=record_id,
            source_session_id=source_session_id,
            source_node_id=source_node_id,
            original_text=original_text,
            extracted_content=extracted_content,
            extraction_type=extraction_type,
            extraction_subtype=extraction_subtype,
            created_at=now,
            annotation=None,
            annotated_at=None,
        )

    # ───────────────────────────────────────────────────────────────────────
    # Write: annotate
    # ───────────────────────────────────────────────────────────────────────

    async def annotate(self, record_id: str, annotation: str) -> bool:
        """Submit human annotation for an extraction record.

        Args:
            record_id: UUID of the extraction record.
            annotation: One of 'correct', 'incorrect', 'partial'.

        Returns:
            True if record was found and updated, False otherwise.

        [Source: Story 7.4 Task 2.5]
        """
        if annotation not in ("correct", "incorrect", "partial"):
            raise ValueError(f"Invalid annotation value: {annotation}")

        await self._ensure_init()
        now = datetime.now(timezone.utc).isoformat()

        async with aiosqlite.connect(self._db_path) as db:
            cursor = await db.execute(_UPDATE_ANNOTATION, (annotation, now, record_id))
            await db.commit()
            if cursor.rowcount == 0:
                return False

        logger.info(f"[Story 7.4] Annotated extraction record {record_id} as '{annotation}'")
        return True

    # ───────────────────────────────────────────────────────────────────────
    # Read: paginated query
    # ───────────────────────────────────────────────────────────────────────

    async def get_records(
        self,
        extraction_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> ExtractionRecordPage:
        """Query extraction records with pagination and optional type filter.

        Args:
            extraction_type: Filter by type ('error', 'tip', 'key_qa') or None for all.
            page: Page number (1-based).
            page_size: Records per page.

        Returns:
            ExtractionRecordPage with records and pagination metadata.

        [Source: Story 7.4 Task 2.4]
        """
        await self._ensure_init()

        where_clause = ""
        params: list = []
        if extraction_type:
            where_clause = "WHERE extraction_type = ?"
            params.append(extraction_type)

        offset = (page - 1) * page_size

        async with aiosqlite.connect(self._db_path) as db:
            # Count total
            count_sql = _COUNT.format(where=where_clause)
            cursor = await db.execute(count_sql, params)
            row = await cursor.fetchone()
            total = row[0] if row else 0

            # Fetch page
            select_sql = _SELECT_PAGE.format(where=where_clause)
            cursor = await db.execute(select_sql, params + [page_size, offset])
            rows = await cursor.fetchall()

        records = [
            ExtractionRecord(
                id=r[0],
                source_session_id=r[1],
                source_node_id=r[2],
                original_text=r[3],
                extracted_content=r[4],
                extraction_type=r[5],
                extraction_subtype=r[6],
                created_at=r[7],
                annotation=r[8],
                annotated_at=r[9],
            )
            for r in rows
        ]

        return ExtractionRecordPage(
            records=records,
            total=total,
            page=page,
            page_size=page_size,
        )

    # ───────────────────────────────────────────────────────────────────────
    # Read: statistics
    # ───────────────────────────────────────────────────────────────────────

    async def get_stats(self) -> ExtractionStats:
        """Compute extraction quality statistics with per-type breakdown.

        Emits WARNING log if overall accuracy < 80%.

        [Source: Story 7.4 Task 2.6, AC-4]
        """
        await self._ensure_init()

        async with aiosqlite.connect(self._db_path) as db:
            cursor = await db.execute(_STATS_TOTAL)
            total = (await cursor.fetchone())[0]

            cursor = await db.execute(_STATS_ANNOTATED)
            annotated = (await cursor.fetchone())[0]

            cursor = await db.execute(_STATS_CORRECT)
            correct = (await cursor.fetchone())[0]

            cursor = await db.execute(_STATS_BY_TYPE)
            type_rows = await cursor.fetchall()

        accuracy = correct / annotated if annotated > 0 else 0.0

        by_type = {}
        for row in type_rows:
            etype = row[0]
            t_total = row[1]
            t_correct = row[2]
            by_type[etype] = TypeStats(
                total=t_total,
                correct=t_correct,
                accuracy=round(t_correct / t_total, 4) if t_total > 0 else 0.0,
            )

        if annotated > 0 and accuracy < ACCURACY_ALERT_THRESHOLD:
            logger.warning(
                f"[Story 7.4] Extraction accuracy {accuracy:.2%} "
                f"below threshold {ACCURACY_ALERT_THRESHOLD:.0%} "
                f"(annotated: {annotated}, correct: {correct})"
            )

        return ExtractionStats(
            total_records=total,
            annotated_count=annotated,
            accuracy=round(accuracy, 4),
            by_type=by_type,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Module-level singleton
# ═══════════════════════════════════════════════════════════════════════════════

_instance: Optional[ExtractionValidator] = None


def get_extraction_validator(db_path: Optional[str] = None) -> ExtractionValidator:
    """Get or create the singleton ExtractionValidator instance."""
    global _instance
    if _instance is None:
        from pathlib import Path

        if db_path is None:
            backend_dir = Path(__file__).parent.parent.parent
            data_dir = backend_dir / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(data_dir / "qa_metrics.db")
        _instance = ExtractionValidator(db_path)
    return _instance
