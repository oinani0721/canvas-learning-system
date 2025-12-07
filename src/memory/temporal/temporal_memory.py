# ✅ Verified from Story 12.4 AC 1-5 - TemporalMemory Core Class
"""
Temporal Memory Module

Core class that integrates:
- FSRS card management for spaced repetition
- Learning behavior tracking
- Weak concept identification

This is Layer 1 of the 3-layer memory system.
"""

import logging
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .behavior_tracker import BehaviorTracker
from .fsrs_manager import CardState, FSRSManager, get_rating_from_score
from .schema import FSRS_CARD_SCHEMA

logger = logging.getLogger(__name__)


@dataclass
class WeakConcept:
    """Represents a weak concept that needs review."""

    concept: str
    canvas_file: str
    stability: float
    error_rate: float
    combined_score: float  # Lower = weaker
    last_review: Optional[datetime] = None
    due: Optional[datetime] = None


class TemporalMemory:
    """
    Core Temporal Memory class for Canvas Learning System.

    Integrates FSRS scheduling with learning behavior tracking
    to identify weak concepts and schedule reviews.

    Architecture:
        TemporalMemory
            ├── FSRSManager (card scheduling)
            ├── BehaviorTracker (activity tracking)
            └── SQLite (persistence)

    Example usage:
        tm = TemporalMemory()

        # Record learning behavior
        tm.record_behavior("math.canvas", "integration", "answer_attempt", {"score": 65})

        # Get weak concepts for review
        weak = tm.get_weak_concepts("math.canvas", limit=5)

        # Update concept after review
        tm.update_concept_score("integration", 85)
    """

    # ✅ Verified from Story 12.4 AC 5 - Weighted ranking
    # Weights: 70% stability (FSRS), 30% error rate (behavior)
    STABILITY_WEIGHT = 0.7
    ERROR_RATE_WEIGHT = 0.3

    def __init__(
        self,
        db_path: str = "./data/temporal_memory.db",
        desired_retention: float = 0.9,
    ):
        """
        Initialize Temporal Memory.

        Args:
            db_path: Path to SQLite database
            desired_retention: Target retention rate for FSRS (0.0 to 1.0)
        """
        self.db_path = db_path
        self.fsrs = FSRSManager(desired_retention=desired_retention)
        self.tracker = BehaviorTracker(db_path=db_path)
        self._init_fsrs_schema()
        logger.info(f"Initialized TemporalMemory with db={db_path}")

    def _init_fsrs_schema(self):
        """Initialize FSRS cards table."""
        with sqlite3.connect(self.db_path) as conn:
            for statement in FSRS_CARD_SCHEMA.split(";"):
                statement = statement.strip()
                if statement:
                    try:
                        conn.execute(statement)
                    except sqlite3.OperationalError as e:
                        if "already exists" not in str(e):
                            raise
            conn.commit()

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # =========================================================================
    # AC 2: Learning Behavior Tracking
    # =========================================================================

    def record_behavior(
        self,
        canvas_file: str,
        concept: str,
        action_type: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Record a learning behavior event.

        Args:
            canvas_file: Canvas file path
            concept: Concept name
            action_type: Type of action (view, answer_attempt, review, etc.)
            metadata: Optional metadata (e.g., {"score": 75})

        Returns:
            Session ID for the recorded behavior
        """
        session_id = self.tracker.record_behavior(
            canvas_file=canvas_file,
            concept=concept,
            action_type=action_type,
            metadata=metadata,
        )

        # If this is an answer attempt with a score, update FSRS card
        if action_type in ("answer_attempt", "review", "score_update"):
            if metadata and "score" in metadata:
                self._update_fsrs_card(canvas_file, concept, metadata["score"])

        return session_id

    def _update_fsrs_card(
        self, canvas_file: str, concept: str, score: float
    ):
        """
        Update FSRS card based on score.

        Args:
            canvas_file: Canvas file path
            concept: Concept name
            score: Score from 0-100
        """
        # Get or create card
        card_state = self._get_card_state(concept, canvas_file)

        if card_state:
            # Existing card - review it
            card = self.fsrs.state_to_card(card_state)
        else:
            # New card
            card = self.fsrs.create_card()

        # Convert score to FSRS rating and review
        rating = get_rating_from_score(score)
        updated_card, _ = self.fsrs.review_card(card, rating)

        # Save updated card state
        new_state = self.fsrs.card_to_state(updated_card, concept, canvas_file)
        self._save_card_state(new_state)

    def _get_card_state(
        self, concept: str, canvas_file: str
    ) -> Optional[CardState]:
        """Get card state from database."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM fsrs_cards WHERE concept = ?",
                (concept,),
            )
            row = cursor.fetchone()

        if not row:
            return None

        return CardState(
            concept=row["concept"],
            canvas_file=row["canvas_file"],
            difficulty=row["difficulty"],
            stability=row["stability"],
            due=datetime.fromisoformat(row["due"]) if row["due"] else None,
            state=row["state"],
            last_review=datetime.fromisoformat(row["last_review"]) if row["last_review"] else None,
            reps=row["reps"],
            lapses=row["lapses"],
            card_data=row["card_data"],
        )

    def _save_card_state(self, state: CardState):
        """Save card state to database."""
        now = datetime.now(timezone.utc).isoformat()

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO fsrs_cards
                (concept, canvas_file, difficulty, stability, due, state,
                 last_review, reps, lapses, card_data, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    state.concept,
                    state.canvas_file,
                    state.difficulty,
                    state.stability,
                    state.due.isoformat() if state.due else None,
                    state.state,
                    state.last_review.isoformat() if state.last_review else None,
                    state.reps,
                    state.lapses,
                    state.card_data,
                    now,
                ),
            )
            conn.commit()

    # =========================================================================
    # AC 3: Weak Concept Identification
    # =========================================================================

    def get_weak_concepts(
        self,
        canvas_file: str,
        limit: int = 10,
    ) -> List[WeakConcept]:
        """
        Get weak concepts that need review.

        Ranking formula (from Story 12.4 AC 5):
            combined_score = 0.7 * (1 - stability) + 0.3 * error_rate

        Lower stability = weaker (needs review)
        Higher error rate = weaker (needs practice)

        Args:
            canvas_file: Canvas file path
            limit: Maximum number of concepts to return

        Returns:
            List of WeakConcept objects, sorted by weakness (weakest first)
        """
        # Get all concepts for this canvas
        concepts = self.tracker.get_canvas_concepts(canvas_file)

        if not concepts:
            return []

        weak_concepts = []

        for concept in concepts:
            # Get FSRS stability
            card_state = self._get_card_state(concept, canvas_file)
            stability = card_state.stability if card_state else 0.0

            # Normalize stability to 0-1 range (assuming max stability ~365 days)
            normalized_stability = min(stability / 365.0, 1.0)

            # Get error rate from behavior tracking
            error_rate = self.tracker.get_error_rate(canvas_file, concept)

            # Calculate combined score (lower = weaker)
            combined_score = (
                self.STABILITY_WEIGHT * (1 - normalized_stability)
                + self.ERROR_RATE_WEIGHT * error_rate
            )

            weak_concepts.append(
                WeakConcept(
                    concept=concept,
                    canvas_file=canvas_file,
                    stability=stability,
                    error_rate=error_rate,
                    combined_score=combined_score,
                    last_review=card_state.last_review if card_state else None,
                    due=card_state.due if card_state else None,
                )
            )

        # Sort by combined_score descending (weakest first)
        weak_concepts.sort(key=lambda x: x.combined_score, reverse=True)

        return weak_concepts[:limit]

    # =========================================================================
    # AC 4: Score Update API
    # =========================================================================

    def update_concept_score(
        self,
        concept: str,
        score: float,
        canvas_file: Optional[str] = None,
    ) -> bool:
        """
        Update concept score after review.

        Args:
            concept: Concept name
            score: Score from 0-100
            canvas_file: Optional canvas file (if not provided, looks up from DB)

        Returns:
            True if update successful
        """
        # Get canvas file if not provided
        if not canvas_file:
            card_state = self._get_card_state(concept, "")
            if card_state:
                canvas_file = card_state.canvas_file
            else:
                logger.warning(f"No canvas file found for concept: {concept}")
                return False

        # Record behavior and update FSRS
        self.record_behavior(
            canvas_file=canvas_file,
            concept=concept,
            action_type="score_update",
            metadata={"score": score},
        )

        logger.info(f"Updated score for {concept}: {score}")
        return True

    # =========================================================================
    # Additional Utility Methods
    # =========================================================================

    def get_due_concepts(
        self,
        canvas_file: Optional[str] = None,
        limit: int = 20,
    ) -> List[CardState]:
        """
        Get concepts that are due for review.

        Args:
            canvas_file: Optional filter by canvas file
            limit: Maximum number of concepts

        Returns:
            List of CardState objects for due concepts
        """
        now = datetime.now(timezone.utc).isoformat()

        with self._get_connection() as conn:
            if canvas_file:
                cursor = conn.execute(
                    """
                    SELECT * FROM fsrs_cards
                    WHERE canvas_file = ? AND (due IS NULL OR due <= ?)
                    ORDER BY due ASC
                    LIMIT ?
                    """,
                    (canvas_file, now, limit),
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT * FROM fsrs_cards
                    WHERE due IS NULL OR due <= ?
                    ORDER BY due ASC
                    LIMIT ?
                    """,
                    (now, limit),
                )
            rows = cursor.fetchall()

        return [
            CardState(
                concept=row["concept"],
                canvas_file=row["canvas_file"],
                difficulty=row["difficulty"],
                stability=row["stability"],
                due=datetime.fromisoformat(row["due"]) if row["due"] else None,
                state=row["state"],
                last_review=datetime.fromisoformat(row["last_review"]) if row["last_review"] else None,
                reps=row["reps"],
                lapses=row["lapses"],
                card_data=row["card_data"],
            )
            for row in rows
        ]

    def get_concept_retrievability(self, concept: str) -> float:
        """
        Get current retrievability for a concept.

        Args:
            concept: Concept name

        Returns:
            Retrievability probability (0.0 to 1.0)
        """
        card_state = self._get_card_state(concept, "")
        if not card_state:
            return 0.5  # Default for unknown concepts

        card = self.fsrs.state_to_card(card_state)
        return self.fsrs.get_retrievability(card)

    def get_canvas_stats(self, canvas_file: str) -> Dict[str, Any]:
        """
        Get learning statistics for a canvas.

        Args:
            canvas_file: Canvas file path

        Returns:
            Statistics dict
        """
        concepts = self.tracker.get_canvas_concepts(canvas_file)

        with self._get_connection() as conn:
            # Get card statistics
            cursor = conn.execute(
                """
                SELECT
                    COUNT(*) as total_cards,
                    AVG(stability) as avg_stability,
                    AVG(difficulty) as avg_difficulty,
                    SUM(CASE WHEN due <= datetime('now') THEN 1 ELSE 0 END) as due_count
                FROM fsrs_cards
                WHERE canvas_file = ?
                """,
                (canvas_file,),
            )
            row = cursor.fetchone()

        weak_concepts = self.get_weak_concepts(canvas_file, limit=5)

        return {
            "canvas_file": canvas_file,
            "total_concepts": len(concepts),
            "total_cards": row["total_cards"] or 0,
            "avg_stability": row["avg_stability"] or 0.0,
            "avg_difficulty": row["avg_difficulty"] or 0.0,
            "due_count": row["due_count"] or 0,
            "weakest_concepts": [wc.concept for wc in weak_concepts[:3]],
        }

    def export_data(self) -> Dict[str, Any]:
        """
        Export all temporal memory data.

        Returns:
            Dict with behaviors and cards data
        """
        behaviors = self.tracker.get_behaviors(limit=10000)

        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM fsrs_cards")
            cards = [dict(row) for row in cursor.fetchall()]

        return {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "behaviors": behaviors,
            "cards": cards,
        }
