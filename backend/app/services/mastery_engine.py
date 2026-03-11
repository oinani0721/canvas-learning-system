"""
Mastery Engine - BKT + FSRS Hybrid Mastery Computation

Core computation engine for the 5-level mastery proficiency model.

Architecture:
  Student Event (grade 1-4)
       │
  ┌────▼────┐
  │  SPLIT   │
  └──┬────┬──┘
     │    │
  ┌──▼──┐ ┌──▼────┐
  │ BKT │ │ FSRS  │
  │know?│ │recall?│
  └──┬──┘ └──┬────┘
     │       │
  ┌──▼───────▼──┐
  │ Effective   │
  │ Proficiency │
  └─────────────┘
"""

import json
import logging
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.models.mastery_state import (
    ConceptState,
    DEFAULT_BKT_PARAMS,
    MASTERY_COLORS,
    MASTERY_LABELS,
    MasteryConfig,
    OVERRIDE_LEVEL_MAP,
    SELF_ASSESS_COLOR_MAP,
)

logger = logging.getLogger(__name__)

# Import FSRSManager for FSRS computation
try:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))
    from memory.temporal.fsrs_manager import FSRSManager
    FSRS_ENGINE_AVAILABLE = True
except ImportError:
    FSRS_ENGINE_AVAILABLE = False
    logger.warning("FSRSManager not available, FSRS features disabled")


def load_mastery_config() -> MasteryConfig:
    """Load mastery config from mastery_config.json."""
    config_path = Path(__file__).parent.parent.parent.parent / "mastery_config.json"
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return MasteryConfig(
            override_lambda=data.get("override_lambda", 0.1),
            self_assess_weight_cap=data.get("self_assess_weight_cap", 0.5),
            override_weight_cap=data.get("override_weight_cap", 0.8),
            shaky_threshold=data.get("mastery_thresholds", {}).get("shaky", 0.40),
            developing_threshold=data.get("mastery_thresholds", {}).get("developing", 0.70),
            proficient_threshold=data.get("mastery_thresholds", {}).get("proficient", 0.90),
            mastered_fluent_min=data.get("mastered_fluent_min", 2),
        )
    return MasteryConfig()


def _card_attr(card, attr: str, default=0.0):
    """Extract attribute from FSRS Card (object or dict fallback)."""
    if isinstance(card, dict):
        return card.get(attr, default)
    return getattr(card, attr, default)


class MasteryEngine:
    """BKT + FSRS hybrid mastery computation engine."""

    def __init__(self, config: Optional[MasteryConfig] = None):
        self.config = config or load_mastery_config()
        self.fsrs_manager = FSRSManager() if FSRS_ENGINE_AVAILABLE else None

    # ═══════════════════════════════════════════════════════════════════════════
    # Core: Update on Interaction (Grade 1-4)
    # ═══════════════════════════════════════════════════════════════════════════

    def update_on_interaction(self, concept: ConceptState, grade: int) -> ConceptState:
        """
        Update mastery state after a student interaction.

        Grade mapping:
          1 (Forgot)     -> BKT: incorrect, FSRS: Again
          2 (Struggled)  -> BKT: incorrect, FSRS: Hard
          3 (Correct)    -> BKT: correct,   FSRS: Good
          4 (Fluent)     -> BKT: correct (P(G)=0), FSRS: Easy

        Args:
            concept: Current concept state
            grade: Student response grade (1-4)

        Returns:
            Updated concept state (mutated in place and returned)
        """
        is_correct = grade >= 3

        # 1. BKT update
        concept.p_mastery = self._bkt_update(concept, is_correct, grade)

        # 2. FSRS update
        if self.fsrs_manager:
            self._fsrs_update(concept, grade)

        # 3. Update tracking fields
        concept.last_interaction_ts = datetime.now(timezone.utc)
        concept.interaction_count += 1
        if grade == 4:
            concept.fluent_count += 1

        logger.info(
            f"Mastery updated: {concept.concept_id} grade={grade} "
            f"p_mastery={concept.p_mastery:.3f} interactions={concept.interaction_count}"
        )

        return concept

    # ═══════════════════════════════════════════════════════════════════════════
    # BKT: Bayesian Knowledge Tracing
    # ═══════════════════════════════════════════════════════════════════════════

    def _bkt_update(self, concept: ConceptState, is_correct: bool, grade: int) -> float:
        """
        Bayesian Knowledge Tracing posterior update.

        Given:
          - p_prev: prior P(mastered) before this observation
          - P_S (slip): P(incorrect | mastered)
          - P_G (guess): P(correct | not mastered)
          - P_T (transit): P(learn | not mastered, after one opportunity)

        Step 1 - Posterior after observing response:
          If correct:
            p_posterior = p_prev * (1 - P_S) / (p_prev * (1 - P_S) + (1 - p_prev) * P_G)
          If incorrect:
            p_posterior = p_prev * P_S / (p_prev * P_S + (1 - p_prev) * (1 - P_G))

        Step 2 - Learning transition:
          p_new = p_posterior + (1 - p_posterior) * P_T

        Special case: Grade 4 (Fluent) -> set P_G = 0 (no guessing when fluent)

        Args:
            concept: Current concept state
            is_correct: Whether the response was correct (grade >= 3)
            grade: Original grade (1-4), used for Grade-4 special case

        Returns:
            Updated p_mastery value (clamped to [0.001, 0.999])
        """
        params = DEFAULT_BKT_PARAMS.get(concept.bkt_difficulty, DEFAULT_BKT_PARAMS["medium"])
        p_prev = concept.p_mastery
        P_S = params["P_S"]
        P_G = params["P_G"]
        P_T = params["P_T"]

        # Grade 4 (Fluent): no guessing possible when student explains fluently
        if grade == 4:
            P_G = 0.0

        # Step 1: Bayesian posterior P(mastered | observation)
        if is_correct:
            numerator = p_prev * (1 - P_S)
            denominator = p_prev * (1 - P_S) + (1 - p_prev) * P_G
        else:
            numerator = p_prev * P_S
            denominator = p_prev * P_S + (1 - p_prev) * (1 - P_G)

        p_posterior = numerator / denominator if denominator > 0 else p_prev

        # Step 2: Learning transition — even if not mastered, student may learn
        p_new = p_posterior + (1 - p_posterior) * P_T

        return max(0.001, min(0.999, p_new))

    # ═══════════════════════════════════════════════════════════════════════════
    # FSRS: Free Spaced Repetition Scheduler
    # ═══════════════════════════════════════════════════════════════════════════

    def _fsrs_update(self, concept: ConceptState, grade: int) -> None:
        """Update FSRS card state with new review."""
        if not self.fsrs_manager:
            return

        # Restore or create FSRS card
        if concept.fsrs_card_data:
            card = self.fsrs_manager.deserialize_card(concept.fsrs_card_data)
        else:
            card = self.fsrs_manager.create_card()

        # Review with grade (1-4 maps directly to FSRS Rating)
        card, _log = self.fsrs_manager.review_card(card, grade)

        # Store updated FSRS state back to concept
        concept.fsrs_stability = float(_card_attr(card, "stability", 0.0))
        concept.fsrs_difficulty = float(_card_attr(card, "difficulty", 0.0))
        state_raw = _card_attr(card, "state", 0)
        concept.fsrs_state = int(state_raw.value if hasattr(state_raw, "value") else state_raw)
        concept.fsrs_reps = int(_card_attr(card, "reps", 0))
        concept.fsrs_lapses = int(_card_attr(card, "lapses", 0))
        concept.fsrs_card_data = self.fsrs_manager.serialize_card(card)

    def _get_retrievability(self, concept: ConceptState) -> float:
        """
        Compute current retrievability R (volatile, never stored).

        Uses FSRS scheduler if available, falls back to exponential decay.
        """
        if not self.fsrs_manager or not concept.fsrs_card_data:
            # No FSRS data yet -> use time-based decay estimate
            if concept.last_interaction_ts is None:
                return 1.0  # Never reviewed, assume fresh
            days_elapsed = (datetime.now(timezone.utc) - concept.last_interaction_ts).total_seconds() / 86400
            stability = max(concept.fsrs_stability, 1.0)
            return math.exp(-days_elapsed / stability)

        card = self.fsrs_manager.deserialize_card(concept.fsrs_card_data)
        return self.fsrs_manager.get_retrievability(card)

    # ═══════════════════════════════════════════════════════════════════════════
    # Effective Proficiency (Volatile - computed on every read)
    # ═══════════════════════════════════════════════════════════════════════════

    def effective_proficiency(self, concept: ConceptState) -> float:
        """
        Compute volatile effective proficiency (never stored).

        Blends BKT mastery probability with FSRS retrievability,
        then applies override and self-assessment decay.

        Returns:
            float in [0.0, 1.0]
        """
        if concept.interaction_count == 0:
            # Not assessed yet - only consider override/self-assess if present
            base = 0.0
        else:
            R = self._get_retrievability(concept)
            base = min(concept.p_mastery, R)  # Conservative: take lower of know vs recall

        # Apply override decay (explicit override from Sidebar)
        result = self._apply_override(concept, base)

        # Apply self-assessment signal (implicit from Canvas color)
        result = self._apply_self_assess(concept, result)

        return max(0.0, min(1.0, result))

    def _apply_override(self, concept: ConceptState, base: float) -> float:
        """Apply override with exponential decay."""
        if concept.override_value is None or concept.override_ts is None:
            return base

        days_since = (datetime.now(timezone.utc) - concept.override_ts).total_seconds() / 86400
        weight = math.exp(-self.config.override_lambda * days_since)
        weight = min(weight, self.config.override_weight_cap)

        return (1 - weight) * base + weight * concept.override_value

    def _apply_self_assess(self, concept: ConceptState, current: float) -> float:
        """Apply self-assessment with exponential decay (lower weight than override)."""
        if concept.self_assess_value is None or concept.self_assess_ts is None:
            return current

        days_since = (datetime.now(timezone.utc) - concept.self_assess_ts).total_seconds() / 86400
        # Self-assess decays faster (2x lambda) and has lower weight cap
        weight = math.exp(-self.config.override_lambda * 2 * days_since)
        weight = min(weight, self.config.self_assess_weight_cap)

        return (1 - weight) * current + weight * concept.self_assess_value

    # ═══════════════════════════════════════════════════════════════════════════
    # Mastery Level (Derived from effective_proficiency)
    # ═══════════════════════════════════════════════════════════════════════════

    def mastery_level(self, concept: ConceptState) -> int:
        """
        Compute 0-4 mastery level from effective_proficiency + explanation gate.

        Level 4 (Mastered) requires both:
          - effective_proficiency >= 0.90
          - fluent_count >= mastered_fluent_min (explanation-gated verification)
        """
        if concept.interaction_count == 0 and concept.override_value is None and concept.self_assess_value is None:
            return 0  # Not Assessed

        eff = self.effective_proficiency(concept)

        if eff < self.config.shaky_threshold:
            return 1  # Shaky
        if eff < self.config.developing_threshold:
            return 2  # Developing
        if eff < self.config.proficient_threshold:
            return 3  # Proficient

        # High score - check explanation gate
        if concept.fluent_count >= self.config.mastered_fluent_min:
            return 4  # Mastered (verified)
        return 3  # High score but unverified -> Proficient

    def mastery_label(self, concept: ConceptState) -> str:
        """Get human-readable mastery label."""
        return MASTERY_LABELS.get(self.mastery_level(concept), "Unknown")

    def mastery_color(self, concept: ConceptState) -> str:
        """Get sidebar display color hex."""
        return MASTERY_COLORS.get(self.mastery_level(concept), "#6c757d")

    # ═══════════════════════════════════════════════════════════════════════════
    # Freshness (Derived from FSRS due date)
    # ═══════════════════════════════════════════════════════════════════════════

    def freshness(self, concept: ConceptState) -> str:
        """
        Compute freshness category based on FSRS retrievability.

        Returns: "fresh" | "recent" | "due" | "overdue"
        """
        R = self._get_retrievability(concept)
        if R >= 0.90:
            return "fresh"
        if R >= 0.70:
            return "recent"
        if R >= 0.50:
            return "due"
        return "overdue"

    # ═══════════════════════════════════════════════════════════════════════════
    # Override Management
    # ═══════════════════════════════════════════════════════════════════════════

    def set_override(self, concept: ConceptState, level: str, reason: str = "") -> ConceptState:
        """Set explicit override from Sidebar (weight=0.8)."""
        value = OVERRIDE_LEVEL_MAP.get(level)
        if value is None:
            # "not_assessed" or invalid -> clear override
            concept.override_value = None
            concept.override_ts = None
        else:
            concept.override_value = value
            concept.override_ts = datetime.now(timezone.utc)
        return concept

    def clear_override(self, concept: ConceptState) -> ConceptState:
        """Reset override to model-computed value."""
        concept.override_value = None
        concept.override_ts = None
        return concept

    def set_self_assess(self, concept: ConceptState, color: str) -> ConceptState:
        """Set implicit self-assessment from Canvas color change (weight=0.5)."""
        value = SELF_ASSESS_COLOR_MAP.get(color)
        if value is not None:
            concept.self_assess_value = value
            concept.self_assess_ts = datetime.now(timezone.utc)
        return concept

    # ═══════════════════════════════════════════════════════════════════════════
    # False Mastery Risk (Phase 1: basic surprise detection only)
    # ═══════════════════════════════════════════════════════════════════════════

    def false_mastery_risk(self, concept: ConceptState) -> float:
        """
        Basic false mastery risk score (0.0-1.0).

        Phase 1: Simple heuristic based on surprise failures.
        Phase 2 will add 5-layer detection.
        """
        if concept.interaction_count < 3:
            return 0.0

        # Factor 1: Surprise failures (high mastery but wrong answer)
        surprise_factor = min(concept.surprise_failures / 3.0, 1.0)

        # Factor 2: High BKT but low retrievability
        R = self._get_retrievability(concept)
        stale_factor = max(0, concept.p_mastery - R) if concept.p_mastery > 0.7 else 0.0

        # Factor 3: High mastery but low fluent count
        unverified_factor = 0.3 if concept.p_mastery > 0.85 and concept.fluent_count < 2 else 0.0

        return min(1.0, surprise_factor * 0.4 + stale_factor * 0.3 + unverified_factor * 0.3)

    # ═══════════════════════════════════════════════════════════════════════════
    # Concept Response Serialization (for API responses)
    # ═══════════════════════════════════════════════════════════════════════════

    def concept_to_response(self, concept: ConceptState) -> dict:
        """Serialize concept state to API response dict (includes volatile fields)."""
        eff = self.effective_proficiency(concept)
        level = self.mastery_level(concept)
        return {
            "concept_id": concept.concept_id,
            "name": concept.name,
            "topic": concept.topic,
            "effective_proficiency": round(eff, 3),
            "mastery_level": level,
            "mastery_label": MASTERY_LABELS.get(level, "Unknown"),
            "mastery_color": MASTERY_COLORS.get(level, "#6c757d"),
            "retrievability": round(self._get_retrievability(concept), 3),
            "freshness": self.freshness(concept),
            "override_active": concept.override_value is not None,
            "override_value": concept.override_value,
            "self_assess_value": concept.self_assess_value,
            "false_mastery_risk": round(self.false_mastery_risk(concept), 3),
            "interaction_count": concept.interaction_count,
            "fluent_count": concept.fluent_count,
            "p_mastery": round(concept.p_mastery, 3),
        }

    def get_review_candidates(self, concepts: list[ConceptState]) -> list[ConceptState]:
        """
        Get concepts that need review (replaces color-based filtering).

        Criteria: effective_proficiency < 0.70 OR FSRS freshness is due/overdue
        """
        candidates = []
        for c in concepts:
            eff = self.effective_proficiency(c)
            fresh = self.freshness(c)
            if eff < self.config.developing_threshold or fresh in ("due", "overdue"):
                candidates.append(c)
        return candidates

    # ═══════════════════════════════════════════════════════════════════════════
    # External Signal Processing (Graphiti bridge)
    # ═══════════════════════════════════════════════════════════════════════════

    def apply_external_signal(
        self, concept: ConceptState, signal_type: str, severity: float,
    ) -> ConceptState:
        """
        Apply an external signal to adjust p_mastery directly.

        Used by /mastery/graphiti-sync when Claude Code records a Misconception
        or ProblemTrap via Graphiti, bridging the knowledge graph to mastery state.

        Args:
            concept: Current concept state
            signal_type: "misconception", "problem_trap", or "guided_thinking_correct"
            severity: Adjustment magnitude (0.0-1.0)

        Returns:
            Updated concept state with adjusted p_mastery
        """
        if signal_type == "misconception":
            # Direct penalty — misconception indicates lack of understanding
            concept.p_mastery = max(0.05, concept.p_mastery - severity)
            concept.false_mastery_flags += 1
        elif signal_type == "problem_trap":
            # Softer penalty — trap is about application, not understanding
            concept.p_mastery = max(0.05, concept.p_mastery - severity * 0.5)
        elif signal_type == "guided_thinking_correct":
            # Small boost — correct response in guided thinking
            concept.p_mastery = min(0.99, concept.p_mastery + severity)
        else:
            logger.warning(f"Unknown signal type: {signal_type}")

        return concept
