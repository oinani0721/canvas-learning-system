"""
Temporal Memory System for Canvas Learning System

Story 12.4: Temporal Memory实现 (Epic 12)
Purpose: 追踪学习行为时序和FSRS遗忘曲线，支持艾宾浩斯复习系统的薄弱点智能推荐

Architecture:
    - Layer 3 of 3-layer memory system (Temporal: FSRS + SQLite)
    - Integrates with Graphiti (knowledge graph) and LanceDB (vector storage)
    - Uses FSRS-4.5 algorithm for spaced repetition scheduling

Dependencies:
    - fsrs>=4.1.0 (FSRS-4.5 algorithm)
    - aiosqlite>=0.19.0 (async SQLite operations)
    - Python 3.9+ standard library (sqlite3, datetime, typing)

Author: Canvas Development Team
Date: 2025-11-29
Epic: 12 (3层记忆系统 + Agentic RAG集成)
Story: 12.4 (Temporal Memory实现)
"""

# ✅ Verified from PyPI: fsrs (Free Spaced Repetition Scheduler)
# Package: fsrs>=4.1.0, Docs: https://pypi.org/project/fsrs/
# API: Scheduler class (not FSRS), Card, Rating, ReviewLog
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from fsrs import Card, Rating, Scheduler

# ✅ Verified from Python 3.9+ standard library
# Docs: https://docs.python.org/3/library/logging.html
# ✅ Verified from Canvas tech-stack.md (Enterprise Error Monitoring)
# Package: loguru>=0.7.0
from loguru import logger


class TemporalMemory:
    """
    Temporal Memory System for tracking learning behavior and FSRS forgetting curves.

    This class implements Layer 3 of the 3-layer memory system, focusing on:
    - Temporal tracking of learning sessions and behaviors
    - FSRS-4.5 algorithm for spaced repetition scheduling
    - Weak concept detection based on stability and error rates
    - SQLite persistence for learning history

    Acceptance Criteria:
        AC 4.1: FSRS库集成成功 (install py-fsrs, create Card objects, call FSRS().repeat())
        AC 4.2: 学习行为时序追踪 (SQLite database with session_id, canvas_file, concept, etc.)
        AC 4.3: get_weak_concepts() returns low stability concepts (70% low stability + 30% high error rate)
        AC 4.4: update_behavior() updates FSRS cards (inputs: concept, rating 1-4)
        AC 4.5: Performance and persistence (1000 concepts stored, <50ms query, <10MB database)

    Usage:
        >>> tm = TemporalMemory(db_path="learning_behavior.db")
        >>> tm.record_behavior(
        ...     canvas_file="离散数学.canvas",
        ...     concept="逆否命题",
        ...     action_type="explanation",
        ...     session_id="session-001"
        ... )
        >>> weak_concepts = tm.get_weak_concepts(canvas_file="离散数学.canvas", limit=10)
        >>> tm.update_behavior(concept="逆否命题", rating=Rating.Good, canvas_file="离散数学.canvas")
    """

    def __init__(self, db_path: str = "learning_behavior.db"):
        """
        Initialize Temporal Memory System.

        Args:
            db_path: Path to SQLite database file (default: "learning_behavior.db")

        Side Effects:
            - Creates SQLite database if it doesn't exist
            - Initializes FSRS Scheduler
            - Creates tables: fsrs_cards, learning_behavior

        Performance:
            - Initialization time: <100ms
            - Database size: <10MB for 1000 concepts (AC 4.5)
        """
        # ✅ Verified from fsrs package documentation
        # Scheduler() creates FSRS scheduler with default parameters
        self.fsrs = Scheduler()

        # ✅ Verified from Python 3.9+ sqlite3 module
        # Docs: https://docs.python.org/3/library/sqlite3.html
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row  # Enable column access by name

        # Initialize database schema (AC 4.2)
        self._init_schema()

        logger.info(f"TemporalMemory initialized with database: {self.db_path}")

    def _init_schema(self) -> None:
        """
        Initialize SQLite database schema for temporal memory.

        Creates two tables:
            1. fsrs_cards: Stores FSRS card state for each concept
            2. learning_behavior: Stores learning behavior history

        Schema Design (AC 4.2):
            fsrs_cards:
                - concept (TEXT PRIMARY KEY): Concept identifier
                - canvas_file (TEXT): Canvas file path
                - difficulty (REAL): FSRS difficulty parameter
                - stability (REAL): FSRS stability parameter (days)
                - due (TEXT): Next review due date (ISO format)
                - elapsed_days (INTEGER): Days since last review
                - scheduled_days (INTEGER): Scheduled interval days
                - reps (INTEGER): Number of repetitions
                - lapses (INTEGER): Number of lapses
                - state (INTEGER): Card state (0=New, 1=Learning, 2=Review, 3=Relearning)
                - last_review (TEXT): Last review timestamp (ISO format)

            learning_behavior:
                - id (INTEGER PRIMARY KEY): Auto-increment ID
                - session_id (TEXT): Learning session identifier
                - canvas_file (TEXT): Canvas file path
                - concept (TEXT): Concept being learned
                - action_type (TEXT): Type of action (explanation, decomposition, verification, etc.)
                - timestamp (TEXT): Action timestamp (ISO format)
                - metadata (TEXT): JSON metadata (optional)

        Performance:
            - Query latency: <50ms for 1000 concepts (AC 4.5)
            - Indexes on: concept, canvas_file, timestamp
        """
        cursor = self.conn.cursor()

        # Create fsrs_cards table (stores FSRS algorithm state)
        # ✅ Verified from fsrs package: Card has difficulty, stability, due, last_review, state, step
        # Note: reps and lapses are tracked separately since FSRS Card doesn't include them
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fsrs_cards (
                concept TEXT PRIMARY KEY,
                canvas_file TEXT NOT NULL,
                difficulty REAL NOT NULL DEFAULT 0,
                stability REAL NOT NULL DEFAULT 0,
                due TEXT NOT NULL,
                state INTEGER NOT NULL DEFAULT 0,
                step INTEGER NOT NULL DEFAULT 0,
                last_review TEXT NOT NULL,
                reps INTEGER NOT NULL DEFAULT 0,
                lapses INTEGER NOT NULL DEFAULT 0,
                UNIQUE(concept, canvas_file)
            )
        """)

        # Create learning_behavior table (stores learning history)
        # ✅ Verified from EPIC-12-STORY-MAP.md lines 826-834
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learning_behavior (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                canvas_file TEXT NOT NULL,
                concept TEXT NOT NULL,
                action_type TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                metadata TEXT,
                FOREIGN KEY (concept) REFERENCES fsrs_cards(concept)
            )
        """)

        # Create indexes for performance (AC 4.5: <50ms query latency)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_fsrs_stability
            ON fsrs_cards(stability)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_fsrs_canvas
            ON fsrs_cards(canvas_file)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_behavior_timestamp
            ON learning_behavior(timestamp DESC)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_behavior_concept
            ON learning_behavior(concept, action_type)
        """)

        self.conn.commit()
        logger.debug("Database schema initialized successfully")

    def get_weak_concepts(
        self,
        canvas_file: str,
        limit: int = 10,
        stability_weight: float = 0.7,
        error_rate_weight: float = 0.3
    ) -> List[Dict[str, any]]:
        """
        Get weak concepts based on FSRS stability and error rates.

        Algorithm (AC 4.3):
            - 70% weight on low stability (indicates high forgetting risk)
            - 30% weight on high error rate (indicates comprehension issues)
            - Combined score = stability_weight * (1 - normalized_stability)
                             + error_rate_weight * normalized_error_rate

        Args:
            canvas_file: Canvas file path to filter concepts
            limit: Maximum number of weak concepts to return (default: 10)
            stability_weight: Weight for stability factor (default: 0.7)
            error_rate_weight: Weight for error rate factor (default: 0.3)

        Returns:
            List of weak concept dictionaries with keys:
                - concept (str): Concept name
                - stability (float): FSRS stability in days
                - error_rate (float): Error rate (0.0 to 1.0)
                - weakness_score (float): Combined weakness score (0.0 to 1.0, higher = weaker)
                - last_review (str): ISO timestamp of last review
                - reps (int): Number of repetitions

        Performance:
            - Query latency: <50ms for 1000 concepts (AC 4.5)

        Example:
            >>> weak = tm.get_weak_concepts("离散数学.canvas", limit=5)
            >>> print(weak[0])
            {
                'concept': '逆否命题',
                'stability': 1.2,
                'error_rate': 0.6,
                'weakness_score': 0.82,
                'last_review': '2025-11-28T10:30:00',
                'reps': 3
            }
        """
        cursor = self.conn.cursor()

        # Step 1: Get all concepts with FSRS stats
        # ✅ Verified from EPIC-12-STORY-MAP.md lines 836-866
        cursor.execute("""
            SELECT
                c.concept,
                c.stability,
                c.reps,
                c.lapses,
                c.last_review,
                CAST(c.lapses AS REAL) / NULLIF(c.reps, 0) as error_rate
            FROM fsrs_cards c
            WHERE c.canvas_file = ?
            AND c.reps > 0
        """, (canvas_file,))

        concepts = cursor.fetchall()

        if not concepts:
            logger.warning(f"No concepts found for canvas_file: {canvas_file}")
            return []

        # Step 2: Normalize stability and error_rate to [0, 1]
        max_stability = max(row['stability'] for row in concepts)
        min_stability = min(row['stability'] for row in concepts)
        stability_range = max_stability - min_stability if max_stability > min_stability else 1.0

        # Step 3: Calculate weakness scores (AC 4.3: 70% stability + 30% error rate)
        weak_concepts = []
        for row in concepts:
            # Normalize stability (invert: lower stability = higher weakness)
            normalized_stability = (row['stability'] - min_stability) / stability_range
            stability_component = stability_weight * (1.0 - normalized_stability)

            # Error rate is already [0, 1]
            error_rate = row['error_rate'] if row['error_rate'] else 0.0
            error_component = error_rate_weight * error_rate

            # Combined weakness score
            weakness_score = stability_component + error_component

            weak_concepts.append({
                'concept': row['concept'],
                'stability': row['stability'],
                'error_rate': error_rate,
                'weakness_score': weakness_score,
                'last_review': row['last_review'],
                'reps': row['reps']
            })

        # Step 4: Sort by weakness_score (descending) and return top N
        weak_concepts.sort(key=lambda x: x['weakness_score'], reverse=True)

        logger.info(
            f"Found {len(weak_concepts)} concepts, returning top {limit} weak concepts "
            f"for {canvas_file}"
        )

        return weak_concepts[:limit]

    def update_behavior(
        self,
        concept: str,
        rating: Rating,
        canvas_file: str,
        session_id: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Update FSRS card with new rating after review.

        Args:
            concept: Concept name
            rating: FSRS rating (Rating.Again=1, Rating.Hard=2, Rating.Good=3, Rating.Easy=4)
            canvas_file: Canvas file path
            session_id: Optional session identifier (auto-generated if None)

        Returns:
            Dictionary with updated card state:
                - concept (str): Concept name
                - difficulty (float): Updated FSRS difficulty
                - stability (float): Updated FSRS stability (days)
                - due (str): Next review due date (ISO format)
                - reps (int): Total repetitions
                - lapses (int): Total lapses

        Side Effects:
            - Updates fsrs_cards table with new FSRS parameters
            - Records behavior in learning_behavior table

        Algorithm (AC 4.4):
            1. Retrieve existing FSRS card or create new one
            2. Call FSRS().repeat() with rating
            3. Update Card.difficulty, Card.stability, Card.due
            4. Increment reps or lapses based on rating
            5. Persist to SQLite

        Performance:
            - Update latency: <50ms (AC 4.5)

        Example:
            >>> result = tm.update_behavior(
            ...     concept="逆否命题",
            ...     rating=Rating.Good,
            ...     canvas_file="离散数学.canvas"
            ... )
            >>> print(result['stability'])  # e.g., 3.5 days
        """
        cursor = self.conn.cursor()
        # FSRS requires timezone-aware UTC datetime
        now = datetime.now(timezone.utc)

        # Step 1: Retrieve existing card or create new one
        # ✅ Verified from EPIC-12-STORY-MAP.md lines 868-905
        cursor.execute("""
            SELECT * FROM fsrs_cards
            WHERE concept = ? AND canvas_file = ?
        """, (concept, canvas_file))

        row = cursor.fetchone()

        if row:
            # Reconstruct FSRS Card from database
            # ✅ Verified from fsrs package: Card class has difficulty, stability, due, last_review, state, step
            # Note: Card.__init__ doesn't accept these as constructor args, so we set them manually
            card = Card()
            card.difficulty = row['difficulty']
            card.stability = row['stability']
            card.due = datetime.fromisoformat(row['due']).replace(tzinfo=timezone.utc)
            card.last_review = datetime.fromisoformat(row['last_review']).replace(tzinfo=timezone.utc)
            card.state = row['state']
            card.step = row['step']
            reps = row['reps']
            lapses = row['lapses']
        else:
            # Create new card for first review
            # ✅ Verified from fsrs package: Card() creates new card with defaults
            card = Card()
            reps = 0
            lapses = 0

        # Step 2: Apply FSRS algorithm (AC 4.1)
        # ✅ Verified from fsrs package: Scheduler.review_card() method
        # Returns: (updated_card, review_log) tuple
        updated_card, review_log = self.fsrs.review_card(
            card=card,
            rating=rating,
            review_datetime=now
        )

        # Step 3: Update reps and lapses counters
        # Rating.Again = 1 means forgot (lapse), otherwise increment reps
        reps += 1
        if rating == Rating.Again:
            lapses += 1

        # Step 4: Update database (AC 4.4)
        cursor.execute("""
            INSERT OR REPLACE INTO fsrs_cards
            (concept, canvas_file, difficulty, stability, due, state, step,
             last_review, reps, lapses)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            concept,
            canvas_file,
            updated_card.difficulty,
            updated_card.stability,
            updated_card.due.isoformat(),
            updated_card.state,
            updated_card.step,
            updated_card.last_review.isoformat(),
            reps,
            lapses
        ))

        # Step 4: Record behavior (AC 4.2)
        if session_id is None:
            session_id = f"session-{now.strftime('%Y%m%d-%H%M%S')}"

        self.record_behavior(
            canvas_file=canvas_file,
            concept=concept,
            action_type=f"review_rating_{rating.value}",
            session_id=session_id,
            metadata=f'{{"rating": {rating.value}, "stability": {updated_card.stability}}}'
        )

        self.conn.commit()

        logger.info(
            f"Updated FSRS card for concept '{concept}': "
            f"stability={updated_card.stability:.2f}, difficulty={updated_card.difficulty:.2f}, "
            f"reps={reps}, lapses={lapses}"
        )

        return {
            'concept': concept,
            'difficulty': updated_card.difficulty,
            'stability': updated_card.stability,
            'due': updated_card.due.isoformat(),
            'reps': reps,
            'lapses': lapses,
            'state': updated_card.state
        }

    def record_behavior(
        self,
        canvas_file: str,
        concept: str,
        action_type: str,
        session_id: str,
        metadata: Optional[str] = None
    ) -> int:
        """
        Record learning behavior in temporal history.

        Args:
            canvas_file: Canvas file path
            concept: Concept being learned
            action_type: Type of action (e.g., "explanation", "decomposition", "verification")
            session_id: Learning session identifier
            metadata: Optional JSON metadata string

        Returns:
            Row ID of inserted behavior record

        Side Effects:
            - Inserts record into learning_behavior table

        Performance:
            - Insert latency: <50ms (AC 4.5)

        Example:
            >>> row_id = tm.record_behavior(
            ...     canvas_file="离散数学.canvas",
            ...     concept="逆否命题",
            ...     action_type="oral_explanation",
            ...     session_id="session-001",
            ...     metadata='{"agent": "oral-explanation", "score": 0.85}'
            ... )
        """
        cursor = self.conn.cursor()
        # Use UTC timezone for consistency with FSRS
        now = datetime.now(timezone.utc)

        # ✅ Verified from EPIC-12-STORY-MAP.md lines 826-834
        cursor.execute("""
            INSERT INTO learning_behavior
            (session_id, canvas_file, concept, action_type, timestamp, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            session_id,
            canvas_file,
            concept,
            action_type,
            now.isoformat(),
            metadata
        ))

        self.conn.commit()
        row_id = cursor.lastrowid

        logger.debug(
            f"Recorded behavior: concept={concept}, action={action_type}, "
            f"session={session_id}, row_id={row_id}"
        )

        return row_id

    def get_review_due_concepts(
        self,
        canvas_file: str,
        limit: int = 20
    ) -> List[Dict[str, any]]:
        """
        Get concepts that are due for review based on FSRS scheduling.

        Args:
            canvas_file: Canvas file path to filter concepts
            limit: Maximum number of due concepts to return (default: 20)

        Returns:
            List of due concept dictionaries with keys:
                - concept (str): Concept name
                - due (str): Due date (ISO format)
                - stability (float): FSRS stability in days
                - difficulty (float): FSRS difficulty
                - days_overdue (int): Days past due date (0 if not overdue)

        Performance:
            - Query latency: <50ms for 1000 concepts (AC 4.5)

        Example:
            >>> due_concepts = tm.get_review_due_concepts("离散数学.canvas")
            >>> for c in due_concepts:
            ...     print(f"{c['concept']} due {c['days_overdue']} days ago")
        """
        cursor = self.conn.cursor()
        # Use UTC timezone for consistency with FSRS
        now = datetime.now(timezone.utc)

        cursor.execute("""
            SELECT
                concept,
                due,
                stability,
                difficulty,
                CAST(julianday(?) - julianday(due) AS INTEGER) as days_overdue
            FROM fsrs_cards
            WHERE canvas_file = ?
            AND julianday(?) >= julianday(due)
            ORDER BY days_overdue DESC, stability ASC
            LIMIT ?
        """, (now.isoformat(), canvas_file, now.isoformat(), limit))

        results = []
        for row in cursor.fetchall():
            results.append({
                'concept': row['concept'],
                'due': row['due'],
                'stability': row['stability'],
                'difficulty': row['difficulty'],
                'days_overdue': max(0, row['days_overdue'])
            })

        logger.info(f"Found {len(results)} concepts due for review in {canvas_file}")

        return results

    def get_concept_stats(self, concept: str, canvas_file: str) -> Optional[Dict[str, any]]:
        """
        Get detailed statistics for a specific concept.

        Args:
            concept: Concept name
            canvas_file: Canvas file path

        Returns:
            Dictionary with concept statistics or None if not found:
                - concept (str): Concept name
                - stability (float): FSRS stability in days
                - difficulty (float): FSRS difficulty
                - due (str): Next review due date
                - reps (int): Total repetitions
                - lapses (int): Total lapses
                - error_rate (float): Lapse rate
                - last_review (str): Last review timestamp
                - total_behaviors (int): Total behavior records

        Example:
            >>> stats = tm.get_concept_stats("逆否命题", "离散数学.canvas")
            >>> print(f"Error rate: {stats['error_rate']:.2%}")
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT
                c.*,
                COUNT(b.id) as total_behaviors
            FROM fsrs_cards c
            LEFT JOIN learning_behavior b
                ON c.concept = b.concept
            WHERE c.concept = ? AND c.canvas_file = ?
            GROUP BY c.concept
        """, (concept, canvas_file))

        row = cursor.fetchone()

        if not row:
            logger.warning(f"Concept '{concept}' not found in {canvas_file}")
            return None

        error_rate = row['lapses'] / row['reps'] if row['reps'] > 0 else 0.0

        return {
            'concept': row['concept'],
            'stability': row['stability'],
            'difficulty': row['difficulty'],
            'due': row['due'],
            'reps': row['reps'],
            'lapses': row['lapses'],
            'error_rate': error_rate,
            'last_review': row['last_review'],
            'total_behaviors': row['total_behaviors']
        }

    def close(self) -> None:
        """
        Close database connection.

        Side Effects:
            - Commits any pending transactions
            - Closes SQLite connection
        """
        if hasattr(self, 'conn') and self.conn:
            try:
                self.conn.commit()
                self.conn.close()
                logger.info("TemporalMemory database connection closed")
            except sqlite3.ProgrammingError:
                # Database already closed
                pass
            finally:
                self.conn = None

    def __del__(self):
        """Destructor to ensure database connection is closed."""
        try:
            self.close()
        except Exception:
            # Ignore errors during cleanup
            pass

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
