"""
Mastery State Models

Data models for the BKT + FSRS hybrid mastery proficiency system.

Three-tier property classification:
  - Stable: Updated only on interaction events (stored in Neo4j)
  - Volatile: Computed on every read (never stored)
  - Derived: Aggregated from stable/volatile (computed on demand)
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


# ═══════════════════════════════════════════════════════════════════════════════
# BKT Default Parameters (Expert Priors by Difficulty)
# ═══════════════════════════════════════════════════════════════════════════════

# P(L0) = prior probability student already knows the concept
# P(T)  = probability of learning on each opportunity
# P(G)  = probability of correct guess when not mastered
# P(S)  = probability of slip (wrong answer when mastered)

DEFAULT_BKT_PARAMS = {
    "easy": {"P_L0": 0.3, "P_T": 0.3, "P_G": 0.25, "P_S": 0.05},
    "medium": {"P_L0": 0.1, "P_T": 0.2, "P_G": 0.20, "P_S": 0.10},
    "hard": {"P_L0": 0.05, "P_T": 0.15, "P_G": 0.15, "P_S": 0.15},
}

# 5-Level mastery display
MASTERY_LABELS = {
    0: "Not Assessed",
    1: "Shaky",
    2: "Developing",
    3: "Proficient",
    4: "Mastered",
}

MASTERY_COLORS = {
    0: "#6c757d",  # Gray
    1: "#dc3545",  # Red
    2: "#fd7e14",  # Amber
    3: "#0d6efd",  # Blue
    4: "#198754",  # Green
}

# Canvas color -> implicit self-assessment value
SELF_ASSESS_COLOR_MAP = {
    "1": 0.20,  # Red -> student thinks they don't know
    "2": 0.85,  # Orange/Green -> student thinks they know
    "3": 0.55,  # Yellow/Purple -> student thinks partial
    "4": 0.85,  # Green -> student thinks they know
    "5": 0.90,  # Cyan -> student thinks mastered
    "6": 0.40,  # Purple -> student thinks weak
}

# Override level -> proficiency value
OVERRIDE_LEVEL_MAP = {
    "not_assessed": None,
    "shaky": 0.20,
    "developing": 0.55,
    "proficient": 0.80,
    "mastered": 0.95,
}


@dataclass
class ConceptState:
    """
    Represents the stable mastery state of a single concept.

    All fields are persisted to Neo4j EntityNode properties.
    Volatile values (retrievability, effective_proficiency) are computed
    on read and never stored.
    """

    concept_id: str
    topic: str
    name: str

    # BKT stable state
    p_mastery: float = 0.1
    bkt_difficulty: str = "medium"  # easy/medium/hard -> selects BKT params

    # FSRS stable state (mirrors CardState fields)
    fsrs_stability: float = 0.0
    fsrs_difficulty: float = 0.0
    fsrs_state: int = 0  # FSRS State enum value
    fsrs_reps: int = 0
    fsrs_lapses: int = 0
    fsrs_card_data: Optional[str] = None  # Serialized FSRS Card JSON

    # Interaction tracking
    last_interaction_ts: Optional[datetime] = None
    interaction_count: int = 0
    fluent_count: int = 0  # Grade-4 responses (explanation-gated)

    # Override stable state
    override_value: Optional[float] = None
    override_ts: Optional[datetime] = None

    # Self-assessment stable state
    self_assess_value: Optional[float] = None
    self_assess_ts: Optional[datetime] = None

    # False mastery tracking
    false_mastery_flags: int = 0
    surprise_failures: int = 0

    def to_neo4j_props(self) -> dict:
        """Convert to flat dict for Neo4j EntityNode property storage."""
        return {
            "mastery_concept_id": self.concept_id,
            "mastery_topic": self.topic,
            "mastery_name": self.name,
            "p_mastery": self.p_mastery,
            "bkt_difficulty": self.bkt_difficulty,
            "fsrs_stability": self.fsrs_stability,
            "fsrs_difficulty": self.fsrs_difficulty,
            "fsrs_state": self.fsrs_state,
            "fsrs_reps": self.fsrs_reps,
            "fsrs_lapses": self.fsrs_lapses,
            "fsrs_card_data": self.fsrs_card_data,
            "last_interaction_ts": self.last_interaction_ts.isoformat() if self.last_interaction_ts else None,
            "interaction_count": self.interaction_count,
            "fluent_count": self.fluent_count,
            "override_value": self.override_value,
            "override_ts": self.override_ts.isoformat() if self.override_ts else None,
            "self_assess_value": self.self_assess_value,
            "self_assess_ts": self.self_assess_ts.isoformat() if self.self_assess_ts else None,
            "false_mastery_flags": self.false_mastery_flags,
            "surprise_failures": self.surprise_failures,
        }

    @classmethod
    def from_neo4j_props(cls, props: dict) -> "ConceptState":
        """Create from Neo4j EntityNode properties dict."""
        def parse_dt(val):
            if val is None:
                return None
            if isinstance(val, datetime):
                return val
            return datetime.fromisoformat(val)

        return cls(
            concept_id=props.get("mastery_concept_id", props.get("name", "")),
            topic=props.get("mastery_topic", ""),
            name=props.get("mastery_name", props.get("name", "")),
            p_mastery=props.get("p_mastery", 0.1),
            bkt_difficulty=props.get("bkt_difficulty", "medium"),
            fsrs_stability=props.get("fsrs_stability", 0.0),
            fsrs_difficulty=props.get("fsrs_difficulty", 0.0),
            fsrs_state=props.get("fsrs_state", 0),
            fsrs_reps=props.get("fsrs_reps", 0),
            fsrs_lapses=props.get("fsrs_lapses", 0),
            fsrs_card_data=props.get("fsrs_card_data"),
            last_interaction_ts=parse_dt(props.get("last_interaction_ts")),
            interaction_count=props.get("interaction_count", 0),
            fluent_count=props.get("fluent_count", 0),
            override_value=props.get("override_value"),
            override_ts=parse_dt(props.get("override_ts")),
            self_assess_value=props.get("self_assess_value"),
            self_assess_ts=parse_dt(props.get("self_assess_ts")),
            false_mastery_flags=props.get("false_mastery_flags", 0),
            surprise_failures=props.get("surprise_failures", 0),
        )


@dataclass
class MasteryConfig:
    """Configuration for mastery computation (loaded from mastery_config.json)."""

    # Override decay rate (lambda)
    override_lambda: float = 0.1  # ~7 day half-life

    # Self-assessment weight (lower than explicit override)
    self_assess_weight_cap: float = 0.5
    override_weight_cap: float = 0.8

    # Mastery level thresholds
    shaky_threshold: float = 0.40
    developing_threshold: float = 0.70
    proficient_threshold: float = 0.90

    # Mastered requires fluent_count >= this
    mastered_fluent_min: int = 2
