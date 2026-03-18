"""
Signal Registry + 5 MVP Signal Adapters

Story 5.6: Multi-signal fusion — N-signal dynamic registration architecture.

Signals:
  1. BKT Mastery Probability (bkt_mastery) — weight 0.30
  2. FSRS Retrievability (fsrs_retrievability) — weight 0.25
  3. Exam Score Average (exam_score_avg) — weight 0.25
  4. Calibration Bias (calibration_bias) — weight 0.10
  5. Self-Confidence Average (self_confidence_avg) — weight 0.10

[Source: _bmad-output/implementation-artifacts/5-6-multi-signal-fusion.md]
[Source: _bmad-output/planning-artifacts/architecture.md#能力域5]
"""

import logging
from typing import Dict, List, Optional, Tuple

from app.models.mastery_models import MasterySignal

logger = logging.getLogger(__name__)


class SignalRegistry:
    """Registry for mastery signal sources.

    Supports dynamic registration/unregistration of MasterySignal implementations.
    Fusion engine pulls active signals from here.
    """

    def __init__(self):
        self._signals: Dict[str, MasterySignal] = {}

    def register(self, signal: MasterySignal) -> None:
        """Register a signal source."""
        name = signal.signal_name
        if name in self._signals:
            logger.warning(f"SignalRegistry: overwriting existing signal '{name}'")
        self._signals[name] = signal
        logger.info(f"SignalRegistry: registered signal '{name}'")

    def unregister(self, signal_name: str) -> None:
        """Unregister a signal source."""
        if signal_name in self._signals:
            del self._signals[signal_name]
            logger.info(f"SignalRegistry: unregistered signal '{signal_name}'")
        else:
            logger.warning(f"SignalRegistry: signal '{signal_name}' not found for unregister")

    def get_all_signals(self) -> Dict[str, MasterySignal]:
        """Return all registered signals."""
        return dict(self._signals)

    def get_active_signals(self, node_id: str) -> List[Tuple[str, float, float, float]]:
        """Get signals that have data for the given node.

        Returns:
            List of (signal_name, value, weight, reliability) tuples
            for signals where get_value returns non-None.
        """
        active = []
        for name, signal in self._signals.items():
            value = signal.get_value(node_id)
            if value is not None:
                weight = signal.get_weight(node_id)
                reliability = signal.get_reliability(node_id)
                active.append((name, value, weight, reliability))
        return active

    @property
    def signal_count(self) -> int:
        return len(self._signals)


# ═══════════════════════════════════════════════════════════════════════════════
# 5 MVP Signal Adapters
# ═══════════════════════════════════════════════════════════════════════════════


class BKTMasterySignal:
    """BKT mastery probability signal (p_mastery from ConceptState).

    Weight: 0.30 (highest — BKT is the core knowledge estimation).
    """

    def __init__(self, mastery_engine, mastery_store):
        self._engine = mastery_engine
        self._store = mastery_store
        self._cache: Dict[str, Optional[float]] = {}

    @property
    def signal_name(self) -> str:
        return "bkt_mastery"

    def get_value(self, node_id: str) -> Optional[float]:
        """Return BKT p_mastery for the node."""
        return self._cache.get(node_id)

    def get_weight(self, node_id: str) -> float:
        return 0.30

    def get_reliability(self, node_id: str) -> float:
        """Reliability increases with interaction count."""
        return min(1.0, self._cache.get(f"{node_id}_interactions", 0) / 10.0)

    def preload(self, concept) -> None:
        """Preload signal value from a ConceptState object (avoids async in get_value)."""
        if concept.interaction_count > 0:
            self._cache[concept.concept_id] = concept.p_mastery
            self._cache[f"{concept.concept_id}_interactions"] = concept.interaction_count
        else:
            self._cache[concept.concept_id] = None


class FSRSRetrievabilitySignal:
    """FSRS retrievability signal (current R value from FSRS Card).

    Weight: 0.25 (captures retention/recall dimension).
    """

    def __init__(self, mastery_engine):
        self._engine = mastery_engine
        self._cache: Dict[str, Optional[float]] = {}

    @property
    def signal_name(self) -> str:
        return "fsrs_retrievability"

    def get_value(self, node_id: str) -> Optional[float]:
        return self._cache.get(node_id)

    def get_weight(self, node_id: str) -> float:
        return 0.25

    def get_reliability(self, node_id: str) -> float:
        """Reliability depends on FSRS reps count."""
        return min(1.0, self._cache.get(f"{node_id}_reps", 0) / 5.0)

    def preload(self, concept) -> None:
        """Preload R value from a ConceptState using mastery_engine.get_retrievability."""
        if concept.fsrs_card_data or concept.last_interaction_ts:
            r_value = self._engine.get_retrievability(concept)
            self._cache[concept.concept_id] = r_value
            self._cache[f"{concept.concept_id}_reps"] = concept.fsrs_reps
        else:
            self._cache[concept.concept_id] = None


class ExamScoreSignal:
    """Exam score average signal (from AutoSCORE 4-dim normalized).

    Weight: 0.25 (direct assessment evidence).
    Reads from calibration records' actual_performance (AutoSCORE normalized).
    """

    def __init__(self):
        self._cache: Dict[str, Optional[float]] = {}

    @property
    def signal_name(self) -> str:
        return "exam_score_avg"

    def get_value(self, node_id: str) -> Optional[float]:
        return self._cache.get(node_id)

    def get_weight(self, node_id: str) -> float:
        return 0.25

    def get_reliability(self, node_id: str) -> float:
        count = self._cache.get(f"{node_id}_count", 0)
        return min(1.0, count / 5.0)

    def preload_from_calibration_records(self, node_id: str, records) -> None:
        """Preload from calibration records (actual_performance values)."""
        if not records:
            self._cache[node_id] = None
            return
        # Use recent N records (up to 10)
        recent = records[-10:] if len(records) > 10 else records
        avg = sum(r.actual_performance for r in recent) / len(recent)
        self._cache[node_id] = round(avg, 3)
        self._cache[f"{node_id}_count"] = len(recent)


class CalibrationBiasSignal:
    """Calibration bias signal (Story 5.5 signed_bias, inverted).

    Weight: 0.10 (metacognitive correction factor).
    Value = 1.0 - |signed_bias| (larger bias = lower mastery reliability).
    When signed_bias is 0 (well calibrated), signal value is 1.0.
    When signed_bias is large, signal value approaches 0.0.
    """

    def __init__(self):
        self._cache: Dict[str, Optional[float]] = {}

    @property
    def signal_name(self) -> str:
        return "calibration_bias"

    def get_value(self, node_id: str) -> Optional[float]:
        return self._cache.get(node_id)

    def get_weight(self, node_id: str) -> float:
        return 0.10

    def get_reliability(self, node_id: str) -> float:
        count = self._cache.get(f"{node_id}_count", 0)
        return min(1.0, count / 10.0)

    def preload_from_calibration_records(self, node_id: str, records) -> None:
        """Preload from calibration records (compute signed_bias, invert to signal)."""
        if not records or len(records) < 3:
            self._cache[node_id] = None
            return
        from app.services.calibration_tracker import compute_signed_bias

        bias = compute_signed_bias(records)
        # Invert: larger |bias| → lower signal value (less reliable mastery)
        signal_value = max(0.0, 1.0 - abs(bias))
        self._cache[node_id] = round(signal_value, 3)
        self._cache[f"{node_id}_count"] = len(records)


class SelfConfidenceSignal:
    """Self-confidence average signal (from calibration records).

    Weight: 0.10 (user's self-perception).
    """

    def __init__(self):
        self._cache: Dict[str, Optional[float]] = {}

    @property
    def signal_name(self) -> str:
        return "self_confidence_avg"

    def get_value(self, node_id: str) -> Optional[float]:
        return self._cache.get(node_id)

    def get_weight(self, node_id: str) -> float:
        return 0.10

    def get_reliability(self, node_id: str) -> float:
        count = self._cache.get(f"{node_id}_count", 0)
        return min(1.0, count / 5.0)

    def preload_from_calibration_records(self, node_id: str, records) -> None:
        """Preload from calibration records (self_confidence values)."""
        if not records:
            self._cache[node_id] = None
            return
        recent = records[-10:] if len(records) > 10 else records
        avg = sum(r.self_confidence for r in recent) / len(recent)
        self._cache[node_id] = round(avg, 3)
        self._cache[f"{node_id}_count"] = len(recent)
