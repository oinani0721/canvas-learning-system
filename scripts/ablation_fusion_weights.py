"""Ablation harness for 5-signal fusion weights (A10 Phase 1 Change 2).

Offline research tooling. Measures the accuracy of several weight sets for the
`compute_fused_mastery` dynamic-renormalization fusion rule against a synthetic
learning-event dataset grounded in published BKT and FSRS parameters.

This script is research tooling. It does not import anything from `backend/app/`
and is not invoked by any production code path.

User decisions (2026-04-07, A10 Phase 1 plan session 3):
  - Q3: synthetic data is allowed as the starting corpus (no real user data yet).
  - Q4: run locally and manually only. This is not a CI check.

Usage:

    # Generate 1000 synthetic rows (BKT + FSRS driven) and run all candidates.
    python scripts/ablation_fusion_weights.py --synthetic 1000 --seed 42

    # Score against the committed fixture (smoke test).
    python scripts/ablation_fusion_weights.py --input scripts/fixtures/synthetic_fusion_sample.jsonl

    # Write report to a specific path instead of ablation_report.json.
    python scripts/ablation_fusion_weights.py --synthetic 5000 --output /tmp/ablation.json

The fusion math mirrors `backend/app/services/mastery_fusion.py::compute_fused_mastery`:

  1. Gather signals that have a value (skip signals whose value is None).
  2. If no signal has a value, the output is 0.0 (unassessed).
  3. Renormalize weights across the active signals so they sum to 1.
  4. Take the weighted average.
  5. Clamp the result into [0, 1].

If the production fusion rule changes, this file needs a manual matching update.
The check is included in this file's `sanity_check_math()` function so drift is
caught the next time a human runs the harness.

Synthetic data sources:
  - Yudelson et al. 2013, "Individualized Bayesian Knowledge Tracing Models" (IEDM)
    Default BKT parameters: P(L0)=0.5, P(T)=0.1, P(S)=0.1, P(G)=0.2.
  - Open-source FSRS project (FSRS-4.5, DSR):
    Retrievability R = exp(ln(0.9) * t / S) with initial stability S_0 drawn from
    2-5 days uniform.
  - Exam scores are noisy observations of the latent mastery with N(0, 0.15) noise.
  - Calibration bias and self-confidence are modeled as weaker noise signals.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import statistics
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


SIGNAL_NAMES = ["bkt", "fsrs", "exam", "cal", "conf"]

CANDIDATES: Dict[str, Dict[str, float]] = {
    "baseline": {"bkt": 0.30, "fsrs": 0.25, "exam": 0.25, "cal": 0.10, "conf": 0.10},
    "no_exam": {"bkt": 0.40, "fsrs": 0.35, "exam": 0.00, "cal": 0.15, "conf": 0.10},
    "no_cal_conf": {"bkt": 0.35, "fsrs": 0.30, "exam": 0.35, "cal": 0.00, "conf": 0.00},
    "bkt_only": {"bkt": 1.00, "fsrs": 0.00, "exam": 0.00, "cal": 0.00, "conf": 0.00},
    "fsrs_only": {"bkt": 0.00, "fsrs": 1.00, "exam": 0.00, "cal": 0.00, "conf": 0.00},
    "equal": {"bkt": 0.20, "fsrs": 0.20, "exam": 0.20, "cal": 0.20, "conf": 0.20},
}


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class Row:
    """One evaluation row: a node's observed signals and the ground-truth label.

    Fields:
      node_id: identifier for the row (used only for traceability).
      y: ground-truth label (probability of success on next attempt), in [0, 1].
      signals: per-signal observed values keyed by `SIGNAL_NAMES`. A None value
               means the signal has no data for this row (the fusion rule will
               skip it via dynamic renormalization).
    """

    node_id: str
    y: float
    signals: Dict[str, Optional[float]] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Synthetic data generator — BKT + FSRS parameters from published literature
# ---------------------------------------------------------------------------

BKT_P_L0 = 0.5  # prior knowledge (Yudelson 2013 default)
BKT_P_T = 0.1  # probability of transitioning from unlearned -> learned per step
BKT_P_S = 0.1  # slip: knew it but answered wrong
BKT_P_G = 0.2  # guess: didn't know it but answered right

FSRS_LN_RETENTION = math.log(0.9)  # FSRS desired retention target is 90%


def _bkt_step(p_learned: float, correct: bool) -> float:
    """Bayesian update of P(learned) given an observation.

    Mirrors the standard BKT posterior used by Yudelson 2013:
      - if correct: P(learned | correct) = P(correct | learned) * P(learned) / P(correct)
      - if wrong:   P(learned | wrong)   = P(wrong | learned)   * P(learned) / P(wrong)

    Then the transition step: P(learned next) = P(learned) + (1 - P(learned)) * P(T).
    """
    if correct:
        p_correct_given_learned = 1.0 - BKT_P_S
        p_correct_given_unlearned = BKT_P_G
    else:
        p_correct_given_learned = BKT_P_S
        p_correct_given_unlearned = 1.0 - BKT_P_G

    numerator = p_correct_given_learned * p_learned
    denominator = numerator + p_correct_given_unlearned * (1.0 - p_learned)
    if denominator < 1e-12:
        posterior = p_learned
    else:
        posterior = numerator / denominator
    return posterior + (1.0 - posterior) * BKT_P_T


def _fsrs_retrievability(days_since_last_review: float, stability: float) -> float:
    """FSRS retrievability formula (FSRS-4.5 DSR)."""
    if stability <= 0:
        return 0.0
    return math.exp(FSRS_LN_RETENTION * days_since_last_review / stability)


def generate_synthetic(n_rows: int, seed: int = 42) -> List[Row]:
    """Generate a synthetic corpus by simulating BKT + FSRS-driven learners.

    Each row models one (student, concept) pair at a point in time. The latent
    "true mastery" p_true is the BKT posterior after a random number of attempts.
    Each signal is an observation of p_true filtered through the signal's own
    noise model.

    Args:
        n_rows: number of synthetic rows to generate.
        seed: random seed for reproducibility.

    Returns:
        List of `Row` objects, each carrying a label `y` and 5 signal values
        (any subset may be None to simulate sparse signals).
    """
    rng = random.Random(seed)
    rows: List[Row] = []

    for i in range(n_rows):
        # --- Latent state: BKT-driven true mastery after some attempts ---
        p_learned = BKT_P_L0
        n_attempts = rng.randint(0, 20)
        for _ in range(n_attempts):
            correct = rng.random() < (
                p_learned * (1.0 - BKT_P_S) + (1.0 - p_learned) * BKT_P_G
            )
            p_learned = _bkt_step(p_learned, correct)
        p_true = max(0.0, min(1.0, p_learned))

        # --- Ground-truth label: next-attempt success probability ---
        y = p_true * (1.0 - BKT_P_S) + (1.0 - p_true) * BKT_P_G

        # --- Signal observations (each with its own noise model) ---
        # BKT signal: perfectly tracks p_true since the generator IS BKT.
        bkt_val: Optional[float] = max(0.0, min(1.0, p_true + rng.gauss(0.0, 0.05)))

        # FSRS signal: retrievability at a random time since last review.
        stability = rng.uniform(2.0, 5.0)  # DSR initial stability window
        days_since = rng.uniform(0.0, stability * 2.0)
        fsrs_val: Optional[float] = _fsrs_retrievability(
            days_since, stability * (0.5 + p_true)
        )

        # Exam signal: noisy linear observation of p_true.
        exam_val: Optional[float] = max(0.0, min(1.0, p_true + rng.gauss(0.0, 0.15)))

        # Calibration signal: weaker — half of its variance is independent noise.
        cal_val: Optional[float] = max(0.0, min(1.0, 0.5 * p_true + 0.5 * rng.random()))

        # Self-confidence: biased toward optimism, high noise.
        conf_val: Optional[float] = max(0.0, min(1.0, p_true + rng.gauss(0.1, 0.2)))

        # Simulate signal sparsity — drop each optional signal 15% of the time.
        if rng.random() < 0.15:
            exam_val = None
        if rng.random() < 0.15:
            cal_val = None
        if rng.random() < 0.15:
            conf_val = None

        rows.append(
            Row(
                node_id=f"synthetic-{i:06d}",
                y=y,
                signals={
                    "bkt": bkt_val,
                    "fsrs": fsrs_val,
                    "exam": exam_val,
                    "cal": cal_val,
                    "conf": conf_val,
                },
            )
        )

    return rows


# ---------------------------------------------------------------------------
# Fusion math — mirrors `mastery_fusion.py::compute_fused_mastery`
# ---------------------------------------------------------------------------


def fuse(signals: Dict[str, Optional[float]], weights: Dict[str, float]) -> float:
    """Weighted-average fusion with dynamic renormalization.

    Mirrors `backend/app/services/mastery_fusion.py::compute_fused_mastery`:
      1. Collect signals whose value is not None AND whose weight is > 0.
      2. Renormalize those signals' weights across the active subset.
      3. Take the weighted average.
      4. Clamp the result into [0, 1].

    Args:
        signals: per-signal value dict. Keys not in `weights` are ignored.
        weights: per-signal weight dict. Signals with weight 0 are treated
                 as absent even if they have a value (this matches the way
                 candidate weight sets zero out specific signals).

    Returns:
        Fused mastery in [0, 1]. Zero if no signal was active.
    """
    active: List[tuple[float, float]] = []  # list of (value, weight)
    for name, value in signals.items():
        if value is None:
            continue
        weight = weights.get(name, 0.0)
        if weight <= 0.0:
            continue
        active.append((value, weight))

    if not active:
        return 0.0

    total_weight = sum(w for _, w in active)
    if total_weight <= 0.0:
        return 0.0

    fused = sum(v * w for v, w in active) / total_weight
    return max(0.0, min(1.0, fused))


# ---------------------------------------------------------------------------
# Evaluation metrics — plain Python, no external libraries
# ---------------------------------------------------------------------------


def logloss(preds: List[float], labels: List[float], eps: float = 1e-15) -> float:
    """Binary cross-entropy-style logloss for continuous labels in [0, 1].

    Lower is better. Matches scikit-learn's `log_loss` behavior for soft labels.
    """
    if not preds:
        return float("nan")
    total = 0.0
    for p, y in zip(preds, labels):
        p_clamped = max(eps, min(1.0 - eps, p))
        total += -(y * math.log(p_clamped) + (1.0 - y) * math.log(1.0 - p_clamped))
    return total / len(preds)


def auc(preds: List[float], labels: List[float]) -> float:
    """ROC AUC via the Mann-Whitney U relationship.

    For continuous labels in [0, 1], the label is binarized by round(y >= 0.5)
    so the rank statistic is well-defined.

    Higher is better. Chance level is 0.5, perfect is 1.0.
    """
    if not preds:
        return float("nan")
    positives = [p for p, y in zip(preds, labels) if y >= 0.5]
    negatives = [p for p, y in zip(preds, labels) if y < 0.5]
    if not positives or not negatives:
        return float("nan")
    wins = 0.0
    for pos in positives:
        for neg in negatives:
            if pos > neg:
                wins += 1.0
            elif pos == neg:
                wins += 0.5
    return wins / (len(positives) * len(negatives))


def calibration_error(preds: List[float], labels: List[float], bins: int = 10) -> float:
    """Expected calibration error (ECE) using equal-width bins.

    For each bin, compute |avg_pred_in_bin - avg_label_in_bin| weighted by bin
    size, then sum. Lower is better, 0.0 is perfect calibration.
    """
    if not preds:
        return float("nan")
    bin_preds: List[List[float]] = [[] for _ in range(bins)]
    bin_labels: List[List[float]] = [[] for _ in range(bins)]
    for p, y in zip(preds, labels):
        idx = min(bins - 1, int(p * bins))
        bin_preds[idx].append(p)
        bin_labels[idx].append(y)

    total = len(preds)
    ece = 0.0
    for bp, bl in zip(bin_preds, bin_labels):
        if not bp:
            continue
        avg_p = statistics.fmean(bp)
        avg_y = statistics.fmean(bl)
        ece += (len(bp) / total) * abs(avg_p - avg_y)
    return ece


# ---------------------------------------------------------------------------
# Ablation driver
# ---------------------------------------------------------------------------


def run_ablation(rows: List[Row], bins: int = 10) -> Dict[str, Dict[str, float]]:
    """Score every candidate weight set against the given rows.

    Args:
        rows: evaluation corpus.
        bins: number of ECE bins.

    Returns:
        Dict keyed by candidate name, each value is `{logloss, auc, ece}`.
    """
    labels = [r.y for r in rows]
    results: Dict[str, Dict[str, float]] = {}
    for name, weights in CANDIDATES.items():
        preds = [fuse(r.signals, weights) for r in rows]
        results[name] = {
            "logloss": logloss(preds, labels),
            "auc": auc(preds, labels),
            "ece": calibration_error(preds, labels, bins=bins),
        }
    return results


def sanity_check_math() -> bool:
    """Verify the metric math against a perfect-predictor edge case.

    A perfect predictor (preds == labels) should yield:
      - logloss near 0
      - AUC exactly 1.0 (or NaN if the label set has no split)
      - ECE near 0
    """
    perfect_labels = [0.0, 0.1, 0.3, 0.6, 0.8, 1.0]
    ll = logloss(perfect_labels, perfect_labels)
    ec = calibration_error(perfect_labels, perfect_labels)
    a = auc(perfect_labels, perfect_labels)
    checks = [
        ll < 0.5,  # perfect cross-entropy with soft labels is small but not 0
        ec < 0.01,  # perfect alignment: ECE should be near zero
        a == 1.0 or math.isnan(a),
    ]
    return all(checks)


# ---------------------------------------------------------------------------
# JSONL loading
# ---------------------------------------------------------------------------


def load_jsonl(path: Path) -> List[Row]:
    """Load rows from a JSONL file.

    Each line is a JSON object with keys: `node_id`, `y`, `signals`.
    Missing or null signal values are preserved as None.
    """
    rows: List[Row] = []
    with path.open("r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                raise ValueError(f"{path}:{line_num}: invalid JSON: {e}") from e
            signals = obj.get("signals", {})
            for name in SIGNAL_NAMES:
                signals.setdefault(name, None)
            rows.append(
                Row(
                    node_id=str(obj.get("node_id", f"row-{line_num}")),
                    y=float(obj["y"]),
                    signals={
                        k: (None if v is None else float(v)) for k, v in signals.items()
                    },
                )
            )
    return rows


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _format_summary_table(
    results: Dict[str, Dict[str, float]], data_source: str, n_rows: int
) -> str:
    lines = [
        f"# Ablation report ({data_source}, n={n_rows})",
        f"{'candidate':<14} {'logloss':>10} {'auc':>10} {'ece':>10}",
        f"{'-' * 14} {'-' * 10:>10} {'-' * 10:>10} {'-' * 10:>10}",
    ]
    for name, metrics in results.items():
        lines.append(
            f"{name:<14} "
            f"{metrics['logloss']:>10.4f} "
            f"{metrics['auc']:>10.4f} "
            f"{metrics['ece']:>10.4f}"
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Offline ablation harness for 5-signal fusion weights.",
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument(
        "--synthetic",
        type=int,
        metavar="N",
        help="Generate N synthetic rows (BKT + FSRS driven).",
    )
    source.add_argument(
        "--input",
        type=Path,
        metavar="PATH",
        help="Load rows from a JSONL file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("ablation_report.json"),
        help="Output report path (default: ./ablation_report.json).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="RNG seed for synthetic data (default: 42).",
    )
    parser.add_argument(
        "--bins",
        type=int,
        default=10,
        help="Number of bins for expected calibration error (default: 10).",
    )
    args = parser.parse_args()

    if not sanity_check_math():
        print("[FAIL] sanity_check_math() rejected the metric impls — aborting.")
        return 2
    print("[OK] sanity_check_math() passed.")

    if args.synthetic is not None:
        rows = generate_synthetic(args.synthetic, seed=args.seed)
        data_source = f"synthetic (seed={args.seed})"
    else:
        rows = load_jsonl(args.input)
        data_source = f"jsonl (path={args.input})"

    if not rows:
        print("[FAIL] no rows loaded — aborting.")
        return 2

    results = run_ablation(rows, bins=args.bins)
    report = {
        "data_source": data_source,
        "n_rows": len(rows),
        "seed": args.seed if args.synthetic is not None else None,
        "bins": args.bins,
        "candidates": results,
        "warning": (
            "Synthetic-data results do not justify shipping weight changes. "
            "This harness is a math-sanity tool, not a production benchmark."
        ),
    }
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print()
    print(_format_summary_table(results, data_source, len(rows)))
    print()
    print(f"Report written to: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
