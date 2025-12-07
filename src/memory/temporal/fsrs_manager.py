# ✅ Verified from Story 12.4 AC 1 - FSRS Integration
# ✅ Verified from Context7 /open-spaced-repetition/py-fsrs
"""
FSRS Manager Module

Provides FSRS (Free Spaced Repetition Scheduler) integration for
managing learning card states and scheduling reviews.

Based on py-fsrs library (FSRS-4.5 algorithm).
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# Try to import fsrs, provide fallback if not installed
try:
    from fsrs import Card, Rating, ReviewLog, Scheduler, State

    FSRS_AVAILABLE = True
except ImportError:
    FSRS_AVAILABLE = False
    logger.warning("py-fsrs not installed. FSRS features will use fallback implementation.")

    # Fallback implementations
    class Rating:
        Again = 1
        Hard = 2
        Good = 3
        Easy = 4

    class State:
        New = 0
        Learning = 1
        Review = 2
        Relearning = 3


@dataclass
class CardState:
    """Serializable representation of FSRS card state."""

    concept: str
    canvas_file: str
    difficulty: float = 0.0
    stability: float = 0.0
    due: Optional[datetime] = None
    state: int = 0  # State enum value
    last_review: Optional[datetime] = None
    reps: int = 0
    lapses: int = 0
    card_data: Optional[str] = None  # Serialized Card object

    def to_dict(self) -> Dict[str, Any]:
        return {
            "concept": self.concept,
            "canvas_file": self.canvas_file,
            "difficulty": self.difficulty,
            "stability": self.stability,
            "due": self.due.isoformat() if self.due else None,
            "state": self.state,
            "last_review": self.last_review.isoformat() if self.last_review else None,
            "reps": self.reps,
            "lapses": self.lapses,
            "card_data": self.card_data,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CardState":
        return cls(
            concept=data["concept"],
            canvas_file=data["canvas_file"],
            difficulty=data.get("difficulty", 0.0),
            stability=data.get("stability", 0.0),
            due=datetime.fromisoformat(data["due"]) if data.get("due") else None,
            state=data.get("state", 0),
            last_review=datetime.fromisoformat(data["last_review"]) if data.get("last_review") else None,
            reps=data.get("reps", 0),
            lapses=data.get("lapses", 0),
            card_data=data.get("card_data"),
        )


class FSRSManager:
    """
    Manage FSRS cards for spaced repetition scheduling.

    Provides:
    - Card creation and initialization
    - Review scheduling with ratings
    - Retrievability calculation
    - Card state serialization/deserialization

    Example usage:
        manager = FSRSManager()
        card = manager.create_card()
        card, log = manager.review_card(card, Rating.Good)
        retrievability = manager.get_retrievability(card)
    """

    def __init__(self, desired_retention: float = 0.9):
        """
        Initialize FSRS manager.

        Args:
            desired_retention: Target retention rate (0.0 to 1.0)
        """
        self.desired_retention = desired_retention
        self._scheduler = None

        if FSRS_AVAILABLE:
            # ✅ Verified from Context7 - Initialize FSRS Scheduler
            self._scheduler = Scheduler(desired_retention=desired_retention)
            logger.info(f"Initialized FSRS scheduler with retention={desired_retention}")
        else:
            logger.warning("FSRS not available, using fallback scheduler")

    @property
    def scheduler(self):
        """Get the FSRS scheduler instance."""
        return self._scheduler

    def create_card(self) -> Any:
        """
        Create a new FSRS card.

        Returns:
            New Card object (immediately due for first review)
        """
        if FSRS_AVAILABLE:
            # ✅ Verified from Context7 - Create Card
            # note: all new cards are 'due' immediately upon creation
            return Card()
        else:
            # Fallback: return a dict-based card
            return {
                "due": datetime.now(timezone.utc),
                "stability": 0.0,
                "difficulty": 0.0,
                "state": State.New,
                "reps": 0,
                "lapses": 0,
            }

    def review_card(self, card: Any, rating: int) -> Tuple[Any, Any]:
        """
        Review a card with a rating.

        Args:
            card: FSRS Card object
            rating: Rating value (1=Again, 2=Hard, 3=Good, 4=Easy)

        Returns:
            Tuple of (updated_card, review_log)
        """
        if FSRS_AVAILABLE:
            # ✅ Verified from Context7 - Review Card with Rating
            # Rating.Again (==1) forgot the card
            # Rating.Hard (==2) remembered with serious difficulty
            # Rating.Good (==3) remembered after hesitation
            # Rating.Easy (==4) remembered easily
            rating_enum = Rating(rating)
            return self._scheduler.review_card(card, rating_enum)
        else:
            # Fallback: simple interval calculation
            return self._fallback_review(card, rating)

    def _fallback_review(self, card: Dict, rating: int) -> Tuple[Dict, Dict]:
        """Fallback review implementation when py-fsrs is not available."""
        from datetime import timedelta

        now = datetime.now(timezone.utc)

        # Simple interval multipliers based on rating
        multipliers = {1: 0.5, 2: 1.0, 3: 2.5, 4: 4.0}
        base_interval = max(1, card.get("stability", 1))

        # Calculate new interval
        new_interval = base_interval * multipliers.get(rating, 1.0)

        # Update difficulty based on rating
        old_difficulty = card.get("difficulty", 5.0)
        difficulty_change = {1: 0.5, 2: 0.25, 3: 0, 4: -0.25}
        new_difficulty = max(1, min(10, old_difficulty + difficulty_change.get(rating, 0)))

        # Update card state
        updated_card = {
            "due": now + timedelta(days=new_interval),
            "stability": new_interval,
            "difficulty": new_difficulty,
            "state": State.Review if rating >= 2 else State.Relearning,
            "reps": card.get("reps", 0) + 1,
            "lapses": card.get("lapses", 0) + (1 if rating == 1 else 0),
        }

        review_log = {
            "rating": rating,
            "review_datetime": now,
            "elapsed_days": 0,
        }

        return updated_card, review_log

    def get_retrievability(self, card: Any) -> float:
        """
        Get the current retrievability of a card.

        Retrievability is the probability of correctly recalling the card.

        Args:
            card: FSRS Card object

        Returns:
            Probability value between 0.0 and 1.0
        """
        if FSRS_AVAILABLE and self._scheduler:
            # ✅ Verified from Context7 - Get Retrievability
            try:
                return self._scheduler.get_card_retrievability(card)
            except Exception:
                return 0.5  # Default if calculation fails
        else:
            # Fallback: estimate based on time since last review
            if isinstance(card, dict):
                stability = card.get("stability", 1.0)
                due = card.get("due")
                if due and stability > 0:
                    now = datetime.now(timezone.utc)
                    days_overdue = (now - due).days if now > due else 0
                    # Simple exponential decay
                    import math
                    return math.exp(-days_overdue / max(stability, 1))
            return 0.5

    def get_due_date(self, card: Any) -> Optional[datetime]:
        """
        Get the due date of a card.

        Args:
            card: FSRS Card object

        Returns:
            Due datetime or None
        """
        if FSRS_AVAILABLE:
            # ✅ Verified from Context7 - Check Next Due Date
            return getattr(card, "due", None)
        else:
            return card.get("due") if isinstance(card, dict) else None

    def serialize_card(self, card: Any) -> str:
        """
        Serialize card to JSON string for storage.

        Args:
            card: FSRS Card object

        Returns:
            JSON string representation
        """
        if FSRS_AVAILABLE:
            # Extract relevant attributes from Card object
            card_dict = {
                "due": card.due.isoformat() if card.due else None,
                "stability": float(card.stability) if hasattr(card, "stability") else 0.0,
                "difficulty": float(card.difficulty) if hasattr(card, "difficulty") else 0.0,
                "state": int(card.state.value) if hasattr(card, "state") else 0,
                "reps": int(card.reps) if hasattr(card, "reps") else 0,
                "lapses": int(card.lapses) if hasattr(card, "lapses") else 0,
                "last_review": card.last_review.isoformat() if hasattr(card, "last_review") and card.last_review else None,
            }
        else:
            card_dict = card if isinstance(card, dict) else {}

        return json.dumps(card_dict)

    def deserialize_card(self, card_json: str) -> Any:
        """
        Deserialize card from JSON string.

        Args:
            card_json: JSON string representation

        Returns:
            FSRS Card object
        """
        card_dict = json.loads(card_json)

        if FSRS_AVAILABLE:
            # Create new card and set attributes
            card = Card()

            if card_dict.get("due"):
                card.due = datetime.fromisoformat(card_dict["due"])
            if "stability" in card_dict:
                card.stability = card_dict["stability"]
            if "difficulty" in card_dict:
                card.difficulty = card_dict["difficulty"]
            if "state" in card_dict:
                card.state = State(card_dict["state"])
            if "reps" in card_dict:
                card.reps = card_dict["reps"]
            if "lapses" in card_dict:
                card.lapses = card_dict["lapses"]
            if card_dict.get("last_review"):
                card.last_review = datetime.fromisoformat(card_dict["last_review"])

            return card
        else:
            # Return dict for fallback
            if card_dict.get("due"):
                card_dict["due"] = datetime.fromisoformat(card_dict["due"])
            return card_dict

    def card_to_state(self, card: Any, concept: str, canvas_file: str) -> CardState:
        """
        Convert FSRS card to CardState for database storage.

        Args:
            card: FSRS Card object
            concept: Concept name
            canvas_file: Canvas file path

        Returns:
            CardState object
        """
        if FSRS_AVAILABLE:
            return CardState(
                concept=concept,
                canvas_file=canvas_file,
                difficulty=float(card.difficulty) if hasattr(card, "difficulty") else 0.0,
                stability=float(card.stability) if hasattr(card, "stability") else 0.0,
                due=card.due if hasattr(card, "due") else None,
                state=int(card.state.value) if hasattr(card, "state") else 0,
                last_review=card.last_review if hasattr(card, "last_review") else None,
                reps=int(card.reps) if hasattr(card, "reps") else 0,
                lapses=int(card.lapses) if hasattr(card, "lapses") else 0,
                card_data=self.serialize_card(card),
            )
        else:
            return CardState(
                concept=concept,
                canvas_file=canvas_file,
                difficulty=card.get("difficulty", 0.0),
                stability=card.get("stability", 0.0),
                due=card.get("due"),
                state=card.get("state", 0),
                last_review=card.get("last_review"),
                reps=card.get("reps", 0),
                lapses=card.get("lapses", 0),
                card_data=self.serialize_card(card),
            )

    def state_to_card(self, state: CardState) -> Any:
        """
        Convert CardState back to FSRS card.

        Args:
            state: CardState object

        Returns:
            FSRS Card object
        """
        if state.card_data:
            return self.deserialize_card(state.card_data)
        else:
            return self.create_card()


def get_rating_from_score(score: float) -> int:
    """
    Convert a 0-100 score to FSRS Rating.

    Args:
        score: Score from 0 to 100

    Returns:
        Rating value (1-4)
    """
    # ✅ Verified from Context7 - Rating Values
    # Rating.Again (==1) - forgot
    # Rating.Hard (==2) - serious difficulty
    # Rating.Good (==3) - hesitation
    # Rating.Easy (==4) - easily
    if score < 40:
        return Rating.Again  # 1
    elif score < 60:
        return Rating.Hard  # 2
    elif score < 85:
        return Rating.Good  # 3
    else:
        return Rating.Easy  # 4
