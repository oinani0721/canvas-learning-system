# algo-fusion Specification

## Purpose
TBD - created by archiving change a10-fsrs-fusion-formalization. Update Purpose after archive.
## Requirements
### Requirement: Five-Signal Mastery Fusion Engine

The `MasteryFusionEngine.compute_fused_mastery(node_id)` SHALL aggregate up to five distinct mastery signals into a single `fused_mastery: float ∈ [0.0, 1.0]` value via weighted averaging. The five signals SHALL be: BKT Mastery (base weight 0.30), FSRS Retrievability (0.25), Exam Score Average (0.25), Calibration Bias (0.10), and Self-Confidence Average (0.10). The engine SHALL return a `FusionResult` object containing `fused_mastery`, `signal_details` (per-signal value/weight/reliability), `active_signal_count`, and `is_fallback`.

This requirement codifies the contract currently implemented at `backend/app/services/mastery_fusion.py:46-121` and `backend/app/services/signal_registry.py:27-249`. It exists because the 5-signal fusion is the canonical node-level mastery aggregator that future verification/recommendation work SHOULD consume to avoid the present three-system decoupling problem.

#### Scenario: All five signals are active

- **GIVEN** a node where every Signal's `get_value(node_id)` returns a non-None float in [0,1]
- **WHEN** `compute_fused_mastery(node_id)` is invoked
- **THEN** the result `fused_mastery` equals the sum over each signal of `(weight_i / sum_of_active_weights) * value_i`
- **AND** `FusionResult.active_signal_count` equals 5
- **AND** `FusionResult.is_fallback` is `False`

#### Scenario: Subset of signals are active

- **GIVEN** a node where only 3 of the 5 signals (e.g., BKT, FSRS, Exam) return non-None values
- **AND** the other 2 signals return None from `get_value()`
- **WHEN** `compute_fused_mastery(node_id)` is invoked
- **THEN** weights are renormalized over only the active signals before averaging
- **AND** `FusionResult.active_signal_count` equals 3
- **AND** the missing signals do not contribute zero — they are excluded from both numerator and denominator

#### Scenario: Zero signals active is fail-safe

- **GIVEN** a node where every Signal returns None from `get_value(node_id)`
- **WHEN** `compute_fused_mastery(node_id)` is invoked
- **THEN** the engine returns a fallback `FusionResult` with `is_fallback=True`
- **AND** the engine does not raise an exception
- **AND** the `fused_mastery` value is a documented sentinel (currently 0.0)

### Requirement: Dynamic Weight Renormalization

When a strict subset of the 5 signals lacks valid data, the engine SHALL renormalize the remaining active signal weights so they sum to 1.0. The renormalization SHALL divide each active weight by the sum of active weights. The engine SHALL NOT treat inactive signals as contributing zero (which would bias the result toward zero).

This requirement codifies the algorithm at `backend/app/services/mastery_fusion.py:103-114`. The motivation is that signal sparsity is the common case (new nodes have BKT but not Exam/Calibration/Confidence), and a zero-treatment approach would falsely depress fused_mastery for sparsely-instrumented nodes.

#### Scenario: Two signals active out of five

- **GIVEN** only BKT (base weight 0.30) and FSRS (base weight 0.25) have valid data
- **AND** the remaining 3 signals return None
- **WHEN** fusion is computed
- **THEN** the effective weights are BKT = 0.30 / 0.55 ≈ 0.5455 and FSRS = 0.25 / 0.55 ≈ 0.4545
- **AND** the result equals `0.5455 * bkt_value + 0.4545 * fsrs_value`
- **AND** the sum of effective weights equals 1.0 (within float tolerance)

#### Scenario: Single signal active

- **GIVEN** only BKT has data and the other 4 signals return None
- **WHEN** fusion is computed
- **THEN** the effective BKT weight is 1.0 (regardless of its base 0.30)
- **AND** the result equals exactly the BKT value (clamped)

### Requirement: Reliability is Reported But Not Weighted in Phase 1

In the Phase 1 implementation each Signal SHALL compute a `reliability ∈ [0.0, 1.0]` value via `Signal.get_reliability(node_id)`. The engine SHALL record this value in `FusionResult.signal_details[i].reliability` for observability and downstream tooling. The reliability value SHALL NOT participate in the weighted average computation in Phase 1. A future Phase 2 change MAY introduce reliability-weighted fusion (e.g., Beta-Bayesian) — but the Phase 1 contract is that reliability is informational only.

This requirement codifies the present behavior at `backend/app/services/mastery_fusion.py:78` (where SignalDetail stores reliability) and the absence of reliability in the weight computation at L103-114. It is named explicitly as "Phase 1" so future Phase 2 work has a clear MODIFIED Requirements anchor.

#### Scenario: Reliability is recorded in signal details

- **GIVEN** any signal with non-None data and a non-zero reliability value
- **WHEN** fusion is computed
- **THEN** the corresponding `FusionResult.signal_details` entry has `reliability` set to that signal's `get_reliability()` return value
- **AND** the `fused_mastery` output is computed independently of the reliability values

#### Scenario: Reliability differences do not affect output

- **GIVEN** two synthetic nodes with identical signal values but with different reliability values (e.g., 0.2 vs 0.9)
- **WHEN** fusion is computed for both nodes
- **THEN** both nodes produce the same `fused_mastery`
- **AND** only the `signal_details[i].reliability` fields differ between the two FusionResults

### Requirement: Output Range Clamping

The `fused_mastery` field of `FusionResult` SHALL be clamped to the closed interval [0.0, 1.0] before being returned, even if upstream signal values temporarily fall outside this range due to defensive contract violations. This is the final invariant the engine guarantees to consumers.

This requirement codifies `mastery_fusion.py:114` (`fused = max(0.0, min(1.0, fused))`). It exists so that downstream consumers (verification, recommendation, frontend display) can rely on `fused_mastery ∈ [0,1]` without re-clamping.

#### Scenario: Output below zero is clamped to zero

- **GIVEN** a hypothetical signal returning -0.1 (out of contract but defensive)
- **WHEN** fusion is computed
- **THEN** the resulting `fused_mastery` is exactly 0.0
- **AND** no exception is raised

#### Scenario: Output above one is clamped to one

- **GIVEN** a hypothetical signal returning 1.5 (out of contract but defensive)
- **WHEN** fusion is computed
- **THEN** the resulting `fused_mastery` is exactly 1.0
- **AND** no exception is raised

