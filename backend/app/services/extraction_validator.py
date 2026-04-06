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
import sqlite3
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

import aiosqlite
import structlog

from app.models.qa_models import (
    ExtractionRecord,
    ExtractionRecordPage,
    ExtractionStats,
    TypeStats,
)

logger = structlog.get_logger(__name__)

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
    annotated_at TEXT,
    updated_at TEXT,
    deleted_at TEXT
);
"""

_CREATE_INDICES = [
    "CREATE INDEX IF NOT EXISTS idx_extraction_type ON qa_extraction_records(extraction_type);",
    "CREATE INDEX IF NOT EXISTS idx_extraction_annotation ON qa_extraction_records(annotation);",
    "CREATE INDEX IF NOT EXISTS idx_extraction_created ON qa_extraction_records(created_at);",
    "CREATE INDEX IF NOT EXISTS idx_extraction_deleted ON qa_extraction_records(deleted_at);",
]

# Migration: add updated_at and deleted_at columns to existing tables
_MIGRATE_ADD_COLUMNS = [
    "ALTER TABLE qa_extraction_records ADD COLUMN updated_at TEXT;",
    "ALTER TABLE qa_extraction_records ADD COLUMN deleted_at TEXT;",
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
WHERE id = ? AND deleted_at IS NULL;
"""

_UPDATE_CONTENT = """
UPDATE qa_extraction_records
SET extracted_content = ?, updated_at = ?
WHERE id = ? AND deleted_at IS NULL;
"""

_SOFT_DELETE = """
UPDATE qa_extraction_records
SET deleted_at = ?
WHERE id = ? AND deleted_at IS NULL;
"""

_RESET_ANNOTATION = """
UPDATE qa_extraction_records
SET annotation = NULL, annotated_at = NULL
WHERE id = ? AND deleted_at IS NULL;
"""

_GET_RECORD_BY_ID = """
SELECT id, source_session_id, source_node_id, original_text, extracted_content,
       extraction_type, extraction_subtype, created_at, annotation, annotated_at,
       updated_at, deleted_at
FROM qa_extraction_records
WHERE id = ? AND deleted_at IS NULL;
"""

_SELECT_PAGE_BASE = """
SELECT id, source_session_id, source_node_id, original_text, extracted_content,
       extraction_type, extraction_subtype, created_at, annotation, annotated_at,
       updated_at
FROM qa_extraction_records
WHERE deleted_at IS NULL
"""

_SELECT_PAGE_ORDER = """
ORDER BY created_at DESC
LIMIT ? OFFSET ?;
"""

_COUNT_BASE = """
SELECT COUNT(*) FROM qa_extraction_records WHERE deleted_at IS NULL
"""

_STATS_TOTAL = "SELECT COUNT(*) FROM qa_extraction_records WHERE deleted_at IS NULL;"

_STATS_ANNOTATED = "SELECT COUNT(*) FROM qa_extraction_records WHERE annotation IS NOT NULL AND deleted_at IS NULL;"

_STATS_CORRECT = "SELECT COUNT(*) FROM qa_extraction_records WHERE annotation = 'correct' AND deleted_at IS NULL;"

_STATS_BY_TYPE = """
SELECT extraction_type,
       COUNT(*) AS total,
       SUM(CASE WHEN annotation = 'correct' THEN 1 ELSE 0 END) AS correct_count
FROM qa_extraction_records
WHERE annotation IS NOT NULL AND deleted_at IS NULL
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
                # Migrate: add updated_at and deleted_at columns if missing
                for migrate_sql in _MIGRATE_ADD_COLUMNS:
                    try:
                        await db.execute(migrate_sql)
                    except sqlite3.OperationalError:
                        pass  # Column already exists
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

        logger.info(
            f"[Story 7.4] Annotated extraction record {record_id} as '{annotation}'"
        )
        return True

    # ───────────────────────────────────────────────────────────────────────
    # Write: update content (Story 5.8 Task 1.1)
    # ───────────────────────────────────────────────────────────────────────

    async def update_content(
        self, record_id: str, new_content: str
    ) -> Optional[ExtractionRecord]:
        """Update the extracted_content field of a record.

        Args:
            record_id: UUID of the extraction record.
            new_content: New extracted content string.

        Returns:
            Updated ExtractionRecord, or None if not found.

        [Source: Story 5.8 Task 1.1]
        """
        await self._ensure_init()
        now = datetime.now(timezone.utc).isoformat()

        async with aiosqlite.connect(self._db_path) as db:
            cursor = await db.execute(_UPDATE_CONTENT, (new_content, now, record_id))
            await db.commit()
            if cursor.rowcount == 0:
                return None

            cursor = await db.execute(_GET_RECORD_BY_ID, (record_id,))
            row = await cursor.fetchone()

        if not row:
            return None

        logger.info(f"[Story 5.8] Updated extraction content for record {record_id}")
        return ExtractionRecord(
            id=row[0],
            source_session_id=row[1],
            source_node_id=row[2],
            original_text=row[3],
            extracted_content=row[4],
            extraction_type=row[5],
            extraction_subtype=row[6],
            created_at=row[7],
            annotation=row[8],
            annotated_at=row[9],
            updated_at=row[10],
        )

    # ───────────────────────────────────────────────────────────────────────
    # Write: soft delete (Story 5.8 Task 1.2)
    # ───────────────────────────────────────────────────────────────────────

    async def delete_record(self, record_id: str) -> bool:
        """Soft-delete an extraction record by setting deleted_at.

        Subsequent queries automatically exclude deleted records.

        Args:
            record_id: UUID of the extraction record.

        Returns:
            True if record was found and soft-deleted, False otherwise.

        [Source: Story 5.8 Task 1.2]
        """
        await self._ensure_init()
        now = datetime.now(timezone.utc).isoformat()

        async with aiosqlite.connect(self._db_path) as db:
            cursor = await db.execute(_SOFT_DELETE, (now, record_id))
            await db.commit()
            if cursor.rowcount == 0:
                return False

        logger.info(f"[Story 5.8] Soft-deleted extraction record {record_id}")
        return True

    # ───────────────────────────────────────────────────────────────────────
    # Write: reset annotation (Story 5.8 Task 1.3)
    # ───────────────────────────────────────────────────────────────────────

    async def reset_annotation(self, record_id: str) -> bool:
        """Clear annotation and annotated_at fields (revoke annotation).

        Allows re-annotation after reset.

        Args:
            record_id: UUID of the extraction record.

        Returns:
            True if record was found and annotation was reset, False otherwise.

        [Source: Story 5.8 Task 1.3]
        """
        await self._ensure_init()

        async with aiosqlite.connect(self._db_path) as db:
            cursor = await db.execute(_RESET_ANNOTATION, (record_id,))
            await db.commit()
            if cursor.rowcount == 0:
                return False

        logger.info(f"[Story 5.8] Reset annotation for record {record_id}")
        return True

    # ───────────────────────────────────────────────────────────────────────
    # Read: paginated query
    # ───────────────────────────────────────────────────────────────────────

    async def get_records(
        self,
        extraction_type: Optional[str] = None,
        annotation_filter: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> ExtractionRecordPage:
        """Query extraction records with pagination and optional filters.

        Args:
            extraction_type: Filter by type ('error', 'tip', 'key_qa') or None for all.
            annotation_filter: Filter by annotation status:
                'annotated' — only records with annotation set.
                'unannotated' — only records without annotation.
                None — all records.
            page: Page number (1-based).
            page_size: Records per page.

        Returns:
            ExtractionRecordPage with records and pagination metadata.

        [Source: Story 7.4 Task 2.4, Story 5.8 Task 1.5]
        """
        await self._ensure_init()

        # Build WHERE clauses using only parameterized static fragments
        extra_clauses: list[str] = []
        params: list = []
        if extraction_type:
            extra_clauses.append(" AND extraction_type = ?")
            params.append(extraction_type)
        if annotation_filter == "annotated":
            extra_clauses.append(" AND annotation IS NOT NULL")
        elif annotation_filter == "unannotated":
            extra_clauses.append(" AND annotation IS NULL")

        extra_sql = "".join(extra_clauses)
        offset = (page - 1) * page_size

        async with aiosqlite.connect(self._db_path) as db:
            # Count total
            count_sql = _COUNT_BASE + extra_sql + ";"
            cursor = await db.execute(count_sql, params)
            row = await cursor.fetchone()
            total = row[0] if row else 0

            # Fetch page (includes updated_at column — fix 5-8 M3)
            select_sql = _SELECT_PAGE_BASE + extra_sql + _SELECT_PAGE_ORDER
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
                updated_at=r[10],
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
