# ✅ Verified from Story 12.4 AC 2 - Learning Behavior Tracking
"""
Behavior Tracker Module

Tracks learning behaviors in SQLite database for temporal analysis.
Provides APIs for recording and querying learning activities.
"""

import json
import logging
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .schema import BEHAVIOR_SCHEMA

logger = logging.getLogger(__name__)


class BehaviorTracker:
    """
    Track learning behaviors for temporal memory analysis.

    Records learning activities like:
    - Node views
    - Answer attempts
    - Review sessions
    - Score updates

    Example usage:
        tracker = BehaviorTracker("./data/behaviors.db")
        tracker.record_behavior(
            canvas_file="math.canvas",
            concept="integration",
            action_type="answer_attempt",
            metadata={"score": 75, "time_spent": 120}
        )
    """

    def __init__(self, db_path: str = "./data/temporal_memory.db"):
        """
        Initialize behavior tracker.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._ensure_db_exists()
        self._init_schema()

    def _ensure_db_exists(self):
        """Ensure database directory exists."""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

    def _init_schema(self):
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            # Execute each statement separately (SQLite doesn't support multi-statement)
            for statement in BEHAVIOR_SCHEMA.split(";"):
                statement = statement.strip()
                if statement:
                    try:
                        conn.execute(statement)
                    except sqlite3.OperationalError as e:
                        # Ignore "already exists" errors for indexes
                        if "already exists" not in str(e):
                            raise
            conn.commit()
        logger.info(f"Initialized behavior database at {self.db_path}")

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def record_behavior(
        self,
        canvas_file: str,
        concept: str,
        action_type: str,
        metadata: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ) -> str:
        """
        Record a learning behavior event.

        Args:
            canvas_file: Canvas file path
            concept: Concept name
            action_type: Type of action (e.g., "view", "answer", "review")
            metadata: Optional metadata dict
            session_id: Optional session ID (auto-generated if not provided)

        Returns:
            Session ID for the recorded behavior
        """
        if session_id is None:
            session_id = str(uuid.uuid4())

        metadata_json = json.dumps(metadata) if metadata else None
        timestamp = datetime.now(timezone.utc).isoformat()

        with self._get_connection() as conn:
            try:
                conn.execute(
                    """
                    INSERT INTO learning_behaviors
                    (session_id, canvas_file, concept, action_type, timestamp, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (session_id, canvas_file, concept, action_type, timestamp, metadata_json),
                )
                conn.commit()
                logger.debug(
                    f"Recorded behavior: {action_type} for {concept} in {canvas_file}"
                )
            except sqlite3.IntegrityError:
                # Duplicate entry, skip
                logger.debug(f"Duplicate behavior entry skipped: {action_type} for {concept}")

        return session_id

    def get_behaviors(
        self,
        canvas_file: Optional[str] = None,
        concept: Optional[str] = None,
        action_type: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Query learning behaviors with optional filters.

        Args:
            canvas_file: Filter by canvas file
            concept: Filter by concept
            action_type: Filter by action type
            since: Filter by timestamp (after this time)
            limit: Maximum number of results

        Returns:
            List of behavior records
        """
        query = "SELECT * FROM learning_behaviors WHERE 1=1"
        params = []

        if canvas_file:
            query += " AND canvas_file = ?"
            params.append(canvas_file)
        if concept:
            query += " AND concept = ?"
            params.append(concept)
        if action_type:
            query += " AND action_type = ?"
            params.append(action_type)
        if since:
            query += " AND timestamp >= ?"
            params.append(since.isoformat())

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        with self._get_connection() as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

        results = []
        for row in rows:
            record = dict(row)
            if record.get("metadata"):
                record["metadata"] = json.loads(record["metadata"])
            results.append(record)

        return results

    def get_concept_stats(
        self, canvas_file: str, concept: str
    ) -> Dict[str, Any]:
        """
        Get statistics for a specific concept.

        Args:
            canvas_file: Canvas file path
            concept: Concept name

        Returns:
            Statistics dict with counts, last activity, etc.
        """
        with self._get_connection() as conn:
            # Get action counts
            cursor = conn.execute(
                """
                SELECT action_type, COUNT(*) as count
                FROM learning_behaviors
                WHERE canvas_file = ? AND concept = ?
                GROUP BY action_type
                """,
                (canvas_file, concept),
            )
            action_counts = {row["action_type"]: row["count"] for row in cursor.fetchall()}

            # Get last activity
            cursor = conn.execute(
                """
                SELECT MAX(timestamp) as last_activity
                FROM learning_behaviors
                WHERE canvas_file = ? AND concept = ?
                """,
                (canvas_file, concept),
            )
            row = cursor.fetchone()
            last_activity = row["last_activity"] if row else None

            # Get total count
            cursor = conn.execute(
                """
                SELECT COUNT(*) as total
                FROM learning_behaviors
                WHERE canvas_file = ? AND concept = ?
                """,
                (canvas_file, concept),
            )
            total = cursor.fetchone()["total"]

        return {
            "concept": concept,
            "canvas_file": canvas_file,
            "total_behaviors": total,
            "action_counts": action_counts,
            "last_activity": last_activity,
        }

    def get_canvas_concepts(self, canvas_file: str) -> List[str]:
        """
        Get all concepts tracked for a canvas file.

        Args:
            canvas_file: Canvas file path

        Returns:
            List of concept names
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT DISTINCT concept
                FROM learning_behaviors
                WHERE canvas_file = ?
                ORDER BY concept
                """,
                (canvas_file,),
            )
            return [row["concept"] for row in cursor.fetchall()]

    def get_error_rate(
        self, canvas_file: str, concept: str
    ) -> float:
        """
        Calculate error rate for a concept based on answer attempts.

        Args:
            canvas_file: Canvas file path
            concept: Concept name

        Returns:
            Error rate (0.0 to 1.0)
        """
        with self._get_connection() as conn:
            # Get all answer attempts with scores
            cursor = conn.execute(
                """
                SELECT metadata
                FROM learning_behaviors
                WHERE canvas_file = ? AND concept = ?
                AND action_type IN ('answer_attempt', 'review', 'score_update')
                ORDER BY timestamp DESC
                LIMIT 20
                """,
                (canvas_file, concept),
            )
            rows = cursor.fetchall()

        if not rows:
            return 0.5  # Default error rate for new concepts

        scores = []
        for row in rows:
            if row["metadata"]:
                try:
                    metadata = json.loads(row["metadata"])
                    if "score" in metadata:
                        scores.append(metadata["score"])
                except (json.JSONDecodeError, TypeError):
                    pass

        if not scores:
            return 0.5

        # Error rate = 1 - (average score / 100)
        avg_score = sum(scores) / len(scores)
        return 1.0 - (avg_score / 100.0)

    def cleanup_old_behaviors(self, days: int = 90) -> int:
        """
        Remove behaviors older than specified days.

        Args:
            days: Number of days to keep

        Returns:
            Number of deleted records
        """
        from datetime import timedelta

        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

        with self._get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM learning_behaviors WHERE timestamp < ?",
                (cutoff,),
            )
            deleted = cursor.rowcount
            conn.commit()

        logger.info(f"Cleaned up {deleted} old behavior records")
        return deleted
