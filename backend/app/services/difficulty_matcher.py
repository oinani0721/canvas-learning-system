# Canvas Learning System - Difficulty Matcher Service
# Story 7.4: 出题难度匹配与提取质量验证
# [Source: _bmad-output/implementation-artifacts/7-4-difficulty-matching-extraction-validation.md]
"""
Evaluates whether AI-generated question difficulty matches the user's
current mastery level, using a sliding window of 50 questions.

Core logic:
  1. Get effective_proficiency from MasteryEngine (BKT p_mastery + FSRS R)
  2. Compute acceptable difficulty range: proficiency +/- 0.2 (clamped to [0,1])
  3. Estimate question difficulty via LLM (few-shot, 0.0-1.0 scale)
  4. Match: estimated difficulty falls within acceptable range
  5. Track in ring buffer (deque maxlen=50), alert if match_rate < 70%

Integration: called asynchronously after question_generator produces a question,
never blocking the question delivery to the user.

[Source: Story 7.4 AC-1, AC-2]
[Source: architecture.md#Integration Points — question_generator→autoscore→EventBus→mastery_engine]
"""

import asyncio
import logging
from collections import deque
from datetime import datetime, timezone
from typing import Deque, Optional

import aiosqlite

from app.models.qa_models import DifficultyMatchRecord, DifficultyMatchStats

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════════════════════

WINDOW_SIZE = 50
MATCH_THRESHOLD = 0.7
DIFFICULTY_MARGIN = 0.2

# Few-shot prompt for LLM difficulty estimation
_DIFFICULTY_PROMPT = """You are an educational assessment expert. Estimate the difficulty of the following question on a scale from 0.0 (trivial) to 1.0 (extremely hard).

Consider:
- 0.0-0.2: Basic recall / definition
- 0.2-0.4: Understanding / simple application
- 0.4-0.6: Analysis / comparison / moderate application
- 0.6-0.8: Synthesis / evaluation / complex application
- 0.8-1.0: Creative problem-solving / expert-level reasoning

Examples:
Q: "What is the definition of photosynthesis?"
Difficulty: 0.15

Q: "Explain the difference between TCP and UDP, and when you would choose each."
Difficulty: 0.45

Q: "Design a distributed consensus algorithm that handles Byzantine faults with at most f faulty nodes out of 3f+1 total."
Difficulty: 0.85

Now estimate the difficulty of this question:
Q: "{question}"

Respond with ONLY a single decimal number between 0.0 and 1.0, nothing else."""

# ═══════════════════════════════════════════════════════════════════════════════
# SQL for persistence
# ═══════════════════════════════════════════════════════════════════════════════

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS qa_difficulty_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    node_id TEXT NOT NULL,
    proficiency REAL NOT NULL,
    estimated_difficulty REAL NOT NULL,
    is_matched INTEGER NOT NULL,
    lower_bound REAL NOT NULL,
    upper_bound REAL NOT NULL,
    question_preview TEXT DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);
"""

_CREATE_INDEX = "CREATE INDEX IF NOT EXISTS idx_difficulty_logs_created ON qa_difficulty_logs(created_at);"

_INSERT_LOG = """
INSERT INTO qa_difficulty_logs
    (node_id, proficiency, estimated_difficulty, is_matched, lower_bound, upper_bound, question_preview, created_at)
VALUES (?, ?, ?, ?, ?, ?, ?, ?);
"""

_RECENT_LOGS = """
SELECT node_id, proficiency, estimated_difficulty, is_matched,
       lower_bound, upper_bound, question_preview, created_at
FROM qa_difficulty_logs
ORDER BY id DESC
LIMIT ?;
"""


# ═══════════════════════════════════════════════════════════════════════════════
# DifficultyMatcher
# ═══════════════════════════════════════════════════════════════════════════════


class DifficultyMatcher:
    """Evaluates question difficulty vs. user mastery and maintains sliding-window stats.

    [Source: Story 7.4 Task 1]
    """

    def __init__(self, db_path: str):
        """
        Args:
            db_path: Path to SQLite database file for qa_difficulty_logs.
        """
        self._db_path = db_path
        self._window: Deque[bool] = deque(maxlen=WINDOW_SIZE)
        self._initialized = False
        self._init_lock = asyncio.Lock()

    # ───────────────────────────────────────────────────────────────────────
    # Init
    # ───────────────────────────────────────────────────────────────────────

    async def _ensure_init(self) -> None:
        """Create table and hydrate in-memory window from persisted logs."""
        if self._initialized:
            return
        async with self._init_lock:
            if self._initialized:
                return
            async with aiosqlite.connect(self._db_path) as db:
                await db.execute(_CREATE_TABLE)
                await db.execute(_CREATE_INDEX)
                await db.commit()

                # Hydrate sliding window from last N persisted records
                cursor = await db.execute(_RECENT_LOGS, (WINDOW_SIZE,))
                rows = await cursor.fetchall()
                # Rows come in DESC order; reverse so oldest is first
                for row in reversed(rows):
                    self._window.append(bool(row[3]))

            self._initialized = True
            logger.info(f"[Story 7.4] DifficultyMatcher initialized, window hydrated with {len(self._window)} records")

    # ───────────────────────────────────────────────────────────────────────
    # Core: difficulty range
    # ───────────────────────────────────────────────────────────────────────

    @staticmethod
    def compute_difficulty_range(proficiency: float) -> tuple[float, float]:
        """Compute acceptable difficulty range for a given proficiency.

        Args:
            proficiency: effective_proficiency in [0.0, 1.0]

        Returns:
            (lower, upper) clamped to [0.0, 1.0]

        [Source: Story 7.4 Dev Notes — proficiency +/- 0.2, clamp]
        """
        lower = max(0.0, proficiency - DIFFICULTY_MARGIN)
        upper = min(1.0, proficiency + DIFFICULTY_MARGIN)
        return (round(lower, 4), round(upper, 4))

    @staticmethod
    def is_difficulty_matched(estimated_difficulty: float, lower: float, upper: float) -> bool:
        """Check if estimated difficulty falls within the acceptable range."""
        return lower <= estimated_difficulty <= upper

    # ───────────────────────────────────────────────────────────────────────
    # Core: LLM difficulty estimation
    # ───────────────────────────────────────────────────────────────────────

    async def estimate_difficulty(self, question: str) -> float:
        """Estimate question difficulty via LLM (LiteLLM unified call layer).

        Args:
            question: The question text to evaluate.

        Returns:
            Estimated difficulty in [0.0, 1.0].

        [Source: Story 7.4 Task 1.3 — LiteLLM unified call]
        [Source: architecture.md — LiteLLM SDK unified调用]
        """
        import litellm

        prompt = _DIFFICULTY_PROMPT.format(question=question[:500])

        try:
            response = await litellm.acompletion(
                model="openai/gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=10,
            )
            raw = response.choices[0].message.content.strip()
            difficulty = float(raw)
            return max(0.0, min(1.0, difficulty))
        except (ValueError, TypeError, IndexError) as e:
            logger.warning(
                f"[Story 7.4] Failed to parse difficulty estimate: {e}, raw='{raw if 'raw' in dir() else 'N/A'}'"
            )
            return 0.5  # fallback to medium difficulty
        except Exception as e:
            logger.error(f"[Story 7.4] LLM difficulty estimation failed: {e}")
            return 0.5

    # ───────────────────────────────────────────────────────────────────────
    # Core: evaluate and record
    # ───────────────────────────────────────────────────────────────────────

    async def evaluate(
        self,
        node_id: str,
        question: str,
        proficiency: float,
    ) -> DifficultyMatchRecord:
        """Evaluate a question's difficulty against user proficiency.

        Estimates difficulty via LLM, checks match, persists the result,
        and updates the sliding window. Emits WARNING if match rate drops
        below threshold.

        Args:
            node_id: Canvas node the question pertains to.
            question: Generated question text.
            proficiency: User's effective_proficiency for this node.

        Returns:
            DifficultyMatchRecord with full evaluation details.

        [Source: Story 7.4 Task 1.4, 1.5, 1.6]
        """
        await self._ensure_init()

        # 1. Compute range
        lower, upper = self.compute_difficulty_range(proficiency)

        # 2. Estimate difficulty via LLM
        estimated = await self.estimate_difficulty(question)

        # 3. Match
        matched = self.is_difficulty_matched(estimated, lower, upper)

        now = datetime.now(timezone.utc).isoformat()

        record = DifficultyMatchRecord(
            node_id=node_id,
            proficiency=round(proficiency, 4),
            estimated_difficulty=round(estimated, 4),
            is_matched=matched,
            lower_bound=lower,
            upper_bound=upper,
            question_preview=question[:100],
            timestamp=now,
        )

        # 4. Persist to SQLite
        try:
            async with aiosqlite.connect(self._db_path) as db:
                await db.execute(
                    _INSERT_LOG,
                    (
                        node_id,
                        record.proficiency,
                        record.estimated_difficulty,
                        1 if matched else 0,
                        lower,
                        upper,
                        record.question_preview,
                        now,
                    ),
                )
                await db.commit()
        except Exception as e:
            logger.error(f"[Story 7.4] Failed to persist difficulty log: {e}")

        # 5. Update sliding window
        self._window.append(matched)

        # 6. Check alert threshold
        stats = self.get_stats()
        if not stats.is_healthy:
            logger.warning(
                f"[Story 7.4] Difficulty match rate {stats.match_rate:.2%} "
                f"below threshold {MATCH_THRESHOLD:.0%} "
                f"(window: {stats.total_in_window} questions)"
            )

        return record

    # ───────────────────────────────────────────────────────────────────────
    # Statistics
    # ───────────────────────────────────────────────────────────────────────

    def get_stats(self) -> DifficultyMatchStats:
        """Return current sliding-window statistics.

        [Source: Story 7.4 AC-2 — sliding window of 50 questions, 70% threshold]
        """
        total = len(self._window)
        matched = sum(1 for m in self._window if m)
        rate = matched / total if total > 0 else 0.0

        return DifficultyMatchStats(
            window_size=WINDOW_SIZE,
            total_in_window=total,
            matched_count=matched,
            match_rate=round(rate, 4),
            is_healthy=rate >= MATCH_THRESHOLD,
        )

    async def get_stats_with_recent(self, recent_count: int = 10) -> DifficultyMatchStats:
        """Return stats with recent records attached.

        Args:
            recent_count: Number of recent records to include.
        """
        await self._ensure_init()
        stats = self.get_stats()

        try:
            async with aiosqlite.connect(self._db_path) as db:
                cursor = await db.execute(_RECENT_LOGS, (recent_count,))
                rows = await cursor.fetchall()
                stats.recent_records = [
                    DifficultyMatchRecord(
                        node_id=row[0],
                        proficiency=row[1],
                        estimated_difficulty=row[2],
                        is_matched=bool(row[3]),
                        lower_bound=row[4],
                        upper_bound=row[5],
                        question_preview=row[6] or "",
                        timestamp=row[7],
                    )
                    for row in rows
                ]
        except Exception as e:
            logger.error(f"[Story 7.4] Failed to fetch recent records: {e}")

        return stats


# ═══════════════════════════════════════════════════════════════════════════════
# Module-level singleton
# ═══════════════════════════════════════════════════════════════════════════════

_instance: Optional[DifficultyMatcher] = None


def get_difficulty_matcher(db_path: Optional[str] = None) -> DifficultyMatcher:
    """Get or create the singleton DifficultyMatcher instance.

    Args:
        db_path: SQLite database path. Defaults to backend/data/qa_metrics.db.
    """
    global _instance
    if _instance is None:
        from pathlib import Path

        if db_path is None:
            backend_dir = Path(__file__).parent.parent.parent
            data_dir = backend_dir / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(data_dir / "qa_metrics.db")
        _instance = DifficultyMatcher(db_path)
    return _instance
