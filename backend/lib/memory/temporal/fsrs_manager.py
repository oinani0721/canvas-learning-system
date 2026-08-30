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
    logger.warning(
        "py-fsrs not installed. FSRS features will use fallback implementation."
    )

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
    # fsrs 6.x: None = new card never reviewed (distinct from 0.0)
    difficulty: Optional[float] = 0.0
    stability: Optional[float] = 0.0
    due: Optional[datetime] = None
    state: int = 1  # State enum value (py-fsrs 4+ 三态: 1=Learning, 无 New(0))
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
            state=data.get("state") or 1,  # legacy 0/缺失 → Learning (CARD-C3)
            last_review=datetime.fromisoformat(data["last_review"])
            if data.get("last_review")
            else None,
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
            logger.info(
                f"Initialized FSRS scheduler with retention={desired_retention}"
            )
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
            # state=Learning(1) 而非 New(0): 与 py-fsrs 4+ 三态语义对齐,
            # fallback 写出的记录不得再制造 legacy state:0 (CARD-C3)
            return {
                "due": datetime.now(timezone.utc),
                "stability": 0.0,
                "difficulty": 0.0,
                "state": State.Learning,
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
        new_difficulty = max(
            1, min(10, old_difficulty + difficulty_change.get(rating, 0))
        )

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
            # fsrs 6.x: new cards carry stability/difficulty = None until first
            # review — serialize as JSON null (0.0 would make the scheduler
            # treat a new card as an already-learned one). hasattr() cannot
            # guard this: the attribute exists, its value is None.
            stability = getattr(card, "stability", None)
            difficulty = getattr(card, "difficulty", None)
            card_dict = {
                "due": card.due.isoformat() if card.due else None,
                "stability": float(stability) if stability is not None else None,
                "difficulty": float(difficulty) if difficulty is not None else None,
                # 兜底 1 而非 0: fsrs 6.x 无 New(0) 态, 写侧不得产出非法值
                "state": int(card.state.value) if hasattr(card, "state") else 1,
                "reps": int(card.reps) if hasattr(card, "reps") else 0,
                "lapses": int(card.lapses) if hasattr(card, "lapses") else 0,
                "last_review": card.last_review.isoformat()
                if hasattr(card, "last_review") and card.last_review
                else None,
            }
        else:
            card_dict = dict(card) if isinstance(card, dict) else {}
            if card_dict.get("state") == 0:
                card_dict["state"] = 1  # legacy New → Learning, 写侧不产 0
            # CARD-D4: create_card/_fallback_review 直出 raw datetime, 写侧
            # 必须 isoformat — 与 deserialize_card 的 fromisoformat 对称
            # (原样 json.dumps 直接 TypeError, 写读不对称)。
            for key in ("due", "last_review"):
                if isinstance(card_dict.get(key), datetime):
                    card_dict[key] = card_dict[key].isoformat()

        return json.dumps(card_dict)

    def deserialize_card(self, card_json: str) -> Any:
        """
        Deserialize card from JSON string.

        legacy state:0 → Learning(1) 字段级迁移: legacy 实现（官方
        py-fsrs v3 及本模块 FSRS_AVAILABLE=False fallback）会存出
        New(0) + stability/difficulty 0.0 哨兵的旧形状; 当前 py-fsrs
        4+/6.x 只有三态, State(0) 抛 ValueError。state:0 在此映射为
        Learning (官方语义: Learning == "new card being studied for the
        first time"), 且伴生哨兵 0.0 归一为 None——v6 调度器只认 None
        为未初始化, 0.0 会进稳定度幂运算抛 ZeroDivisionError。这是对
        CARD-A1 严格 roundtrip 原则的显式例外 (CARD-C3), 其余状态值
        (1/2/3) 及其字段仍严格原样还原。

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
            # JSON null → None roundtrip (new-card semantics preserved)
            if "stability" in card_dict:
                card.stability = (
                    float(card_dict["stability"])
                    if card_dict["stability"] is not None
                    else None
                )
            if "difficulty" in card_dict:
                card.difficulty = (
                    float(card_dict["difficulty"])
                    if card_dict["difficulty"] is not None
                    else None
                )
            if "state" in card_dict:
                raw_state = card_dict["state"]
                if raw_state == 0:
                    # legacy New 形状字段级迁移: state 0 → Learning; 伴生
                    # 参数哨兵 0.0 → None (v6 调度器只认 None 为未初始化,
                    # stability=0.0 会进稳定度幂运算抛 ZeroDivisionError)。
                    # 正参数属矛盾形状: 保留并告警, 不猜成 Review。
                    card.state = State.Learning
                    if not card.stability:
                        card.stability = None
                    if not card.difficulty:
                        card.difficulty = None
                    if (
                        card_dict.get("stability")
                        or card_dict.get("reps")
                        or card_dict.get("last_review")
                    ):
                        logger.warning(
                            "legacy state:0 record carries non-empty params "
                            "(stability=%s, reps=%s, last_review=%s) — mapped "
                            "to Learning with params preserved",
                            card_dict.get("stability"),
                            card_dict.get("reps"),
                            card_dict.get("last_review"),
                        )
                else:
                    card.state = State(raw_state)
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
            if card_dict.get("state") == 0:
                # legacy New → Learning (与真实分支同规则)。数值参数保留:
                # fallback 调度算术依赖数值而非 None 哨兵 (_fallback_review)。
                card_dict["state"] = 1
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
            # fsrs 6.x new-card semantics: keep None as None (see serialize_card)
            difficulty = getattr(card, "difficulty", None)
            stability = getattr(card, "stability", None)
            return CardState(
                concept=concept,
                canvas_file=canvas_file,
                difficulty=float(difficulty) if difficulty is not None else None,
                stability=float(stability) if stability is not None else None,
                due=card.due if hasattr(card, "due") else None,
                # 兜底 1 而非 0: fsrs 6.x 无 New(0) 态, 写侧不得产出非法值
                state=int(card.state.value) if hasattr(card, "state") else 1,
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
                state=card.get("state") or 1,  # 0/缺失 → Learning, 写侧不产 0
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
