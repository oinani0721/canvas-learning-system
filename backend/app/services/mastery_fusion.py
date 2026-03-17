"""
Mastery Fusion Engine - Multi-Signal Weighted Average Fusion

Story 5.6: Fuses 5 core signals into a single mastery dimension.

Algorithm (MVP — weighted average):
  1. Filter signals with data (get_value != None)
  2. Renormalize weights: w_i_norm = w_i / sum(w_j for all active j)
  3. Fused = sum(w_i_norm * value_i)
  4. Clamp to [0.0, 1.0]

Fallback: min(p_mastery, R) when fusion engine unavailable or no signals.

Phase 2+: Beta-Bayesian fusion (architecture reserved, not implemented here).

[Source: _bmad-output/implementation-artifacts/5-6-multi-signal-fusion.md]
[Source: _bmad-output/planning-artifacts/architecture.md#能力域5]
"""

import logging
import math
from typing import Dict, List, Optional

from app.models.mastery_models import (
    FusionResult,
    SignalCorrelationResult,
    SignalDetail,
)
from app.services.signal_registry import SignalRegistry

logger = logging.getLogger(__name__)


class MasteryFusionEngine:
    """Multi-signal fusion engine for computing unified mastery score.

    Replaces the simple min(p_mastery, R) with a weighted average
    of N registered signals.
    """

    def __init__(self, registry: SignalRegistry):
        self._registry = registry

    def compute_fused_mastery(self, node_id: str) -> FusionResult:
        """Compute fused mastery from all registered signals.

        Algorithm:
          1. Collect all signals with data for this node
          2. If no signals have data, return 0.0 (unassessed)
          3. Renormalize weights among active signals
          4. Compute weighted average
          5. Clamp to [0.0, 1.0]

        Args:
            node_id: Concept node ID

        Returns:
            FusionResult with fused_mastery and per-signal details
        """
        active = self._registry.get_active_signals(node_id)
        all_signals = self._registry.get_all_signals()

        # Build signal details for all registered signals (including inactive)
        signal_details = []
        for name, signal in all_signals.items():
            value = signal.get_value(node_id)
            weight = signal.get_weight(node_id)
            reliability = signal.get_reliability(node_id)
            signal_details.append(
                SignalDetail(
                    signal_name=name,
                    value=value,
                    weight=weight,
                    normalized_weight=0.0,
                    reliability=reliability,
                )
            )

        if not active:
            # No signals with data — return 0.0 (unassessed)
            return FusionResult(
                fused_mastery=0.0,
                signal_details=signal_details,
                active_signal_count=0,
                is_fallback=False,
            )

        # Compute weight sum for active signals
        weight_sum = sum(w for _, _, w, _ in active)

        if weight_sum <= 0:
            return FusionResult(
                fused_mastery=0.0,
                signal_details=signal_details,
                active_signal_count=len(active),
                is_fallback=False,
            )

        # Compute weighted average with renormalized weights
        fused = 0.0
        for name, value, weight, _reliability in active:
            norm_weight = weight / weight_sum
            fused += norm_weight * value
            # Update normalized weight in signal_details
            for sd in signal_details:
                if sd.signal_name == name:
                    sd.normalized_weight = round(norm_weight, 3)

        # Clamp to [0.0, 1.0]
        fused = max(0.0, min(1.0, fused))

        return FusionResult(
            fused_mastery=round(fused, 3),
            signal_details=signal_details,
            active_signal_count=len(active),
            is_fallback=False,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Signal Complementarity Diagnostics (Pearson r)
# ═══════════════════════════════════════════════════════════════════════════════


def compute_pearson_r(values_a: List[float], values_b: List[float]) -> Optional[float]:
    """Compute Pearson correlation coefficient between two value series.

    Formula: r = Σ((x_i - x̄)(y_i - ȳ)) / sqrt(Σ(x_i - x̄)² * Σ(y_i - ȳ)²)

    Args:
        values_a: First signal values
        values_b: Second signal values (same length as values_a)

    Returns:
        Pearson r in [-1.0, 1.0], or None if computation is impossible
        (e.g., fewer than 3 data points or zero variance).
    """
    n = min(len(values_a), len(values_b))
    if n < 3:
        return None

    a = values_a[:n]
    b = values_b[:n]

    mean_a = sum(a) / n
    mean_b = sum(b) / n

    cov = sum((a[i] - mean_a) * (b[i] - mean_b) for i in range(n))
    var_a = sum((a[i] - mean_a) ** 2 for i in range(n))
    var_b = sum((b[i] - mean_b) ** 2 for i in range(n))

    denominator = math.sqrt(var_a * var_b)
    if denominator == 0:
        return None

    return round(cov / denominator, 3)


def run_complementarity_check(
    signal_values: Dict[str, List[float]],
) -> List[SignalCorrelationResult]:
    """Run pairwise Pearson correlation check on all signal pairs.

    Signals with |r| >= 0.7 are flagged as potentially redundant.

    Args:
        signal_values: Dict mapping signal_name to list of values
                       (same ordering across signals for paired comparison)

    Returns:
        List of SignalCorrelationResult for each pair
    """
    names = list(signal_values.keys())
    results = []

    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            name_a = names[i]
            name_b = names[j]
            values_a = signal_values[name_a]
            values_b = signal_values[name_b]

            r = compute_pearson_r(values_a, values_b)
            if r is None:
                continue

            is_redundant = abs(r) >= 0.7
            if is_redundant:
                logger.warning(
                    f"Signal complementarity warning: '{name_a}' and '{name_b}' "
                    f"are highly correlated (r={r:.3f}). Consider reviewing redundancy."
                )

            results.append(
                SignalCorrelationResult(
                    signal_a=name_a,
                    signal_b=name_b,
                    pearson_r=r,
                    sample_count=min(len(values_a), len(values_b)),
                    is_redundant=is_redundant,
                )
            )

    return results
