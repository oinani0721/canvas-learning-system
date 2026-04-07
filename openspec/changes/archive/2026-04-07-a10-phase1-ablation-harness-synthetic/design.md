## Context

### The fusion weights today

`backend/app/services/signal_registry.py` hardcodes the weights:

| Signal | Class | Weight |
|---|---|---|
| BKT mastery probability | `BKTMasterySignal` | 0.30 |
| FSRS retrievability | `FSRSRetrievabilitySignal` | 0.25 |
| Exam score average | `ExamScoreAvgSignal` | 0.25 |
| Calibration bias | `CalibrationBiasSignal` | 0.10 |
| Self-confidence average | `SelfConfidenceAvgSignal` | 0.10 |

These weights are literature-informed guesses. There has never been a measurement run — not on real data, not on synthetic data, not on any data — that says "these weights minimize fused-mastery prediction error on a held-out learning event distribution." Phase 0 formalized the fusion math (`mastery_fusion.py`). Phase 1 needs to formalize the evaluation.

### The two user decisions that unblock this

**Q3 (2026-04-07):** "Can we start with synthetic data?" Answer: yes. The synthetic distribution does not need to match the eventual real-user distribution — it only needs to be internally consistent and parameterized against published learning models, so that the ablation is measuring the math and not the data quality. When real data arrives, the harness flips a switch and re-runs.

**Q4 (2026-04-07):** "Should the harness run in CI or locally?" Answer: locally, manually. The ablation's purpose is to inform architectural decisions (which weights to ship, which signals to keep, when to move to Beta-Bayesian fusion). That is a human-in-the-loop activity, not a continuous check. Running it in CI would consume test-runner budget for zero incremental signal between developer checks.

### What the harness is NOT

- **Not a unit test.** The harness does not assert any property — it writes a report. A human reads the report and draws a conclusion.
- **Not a production codepath.** No backend code imports from `scripts/`. The backend never sees this file.
- **Not a benchmark of the live stack.** The harness reimplements the fusion math in plain Python so it stays dependency-free. If `mastery_fusion.py` changes, the harness may need to be updated manually — this is acceptable, because the fusion math is simple and stable.

## Goals

1. **Empirically rank the 6 candidate weight sets** on a synthetic corpus where ground-truth next-attempt success is derivable.
2. **Produce a JSON report** that lists, for each candidate, the logloss, AUC, and calibration error against the ground truth.
3. **Make the harness runnable from any developer laptop** without needing to install anything beyond Python's standard library.
4. **Make the synthetic data reproducible** by fixing the random seed.
5. **Document how to plug in real data** in the README, using a JSONL schema that matches the synthetic data's row format.

## Non-Goals

- Not picking a winning weight set. The output is a table, not a decision. The decision is a later plan session after the user reads the report.
- Not running the harness against real backend data. That is a future change, triggered when beta users exist.
- Not touching the hardcoded weights in `signal_registry.py`. Even if the harness shows a better configuration, shipping the change is out of scope for this change.
- Not validating the synthetic distribution against the real-user distribution. There is no real-user distribution yet.
- Not adding CI integration. Q4 is explicit.
- Not adding a spec delta. There is no capability behavior being defined.

## Key Decisions

### Decision 1: Synthetic data distribution is BKT + FSRS, not ad-hoc

**Options considered:**

- **(A) Draw ground truth from an ad-hoc beta distribution** (e.g., `p_true ~ Beta(2, 2)` and 5 signal noises layered on top). Fast to write, fully arbitrary.
- **(B) Drive ground truth through a BKT latent state transition** and derive signal observations from the published BKT + FSRS measurement equations. Slower to write, grounded in learning science.

**Decision: (B) BKT + FSRS.**

**Rationale:**

- Using published learning models means the reviewer who runs the harness sees a report whose numbers match an established literature baseline. The first question any reviewer will ask is "where does the synthetic data come from?" — the BKT + FSRS answer is defensible without further justification.
- The BKT parameters we use (`P(L0)=0.5`, `P(T)=0.1`, `P(S)=0.1`, `P(G)=0.2`) are from Yudelson et al. 2013 "Individualized Bayesian Knowledge Tracing Models", IEDM — the canonical reference for "reasonable default BKT parameters when you don't have per-student fits."
- The FSRS retrievability `R = exp(ln(0.9) * t / S)` formula with initial stability `S_0 ~ 2-5 days` comes from FSRS-4.5 / DSR (Default Spaced Repetition) — the formulation used by Anki's official FSRS implementation.
- Exam score is modeled as `p_true + N(0, 0.15)` clipped to [0, 1] — a noisy observation of true mastery.
- Calibration bias and self-confidence are modeled as weaker noise signals (lower reliability), on purpose, so that the ablation can detect whether they carry signal or just drag the fused score toward 0.5.

**Trade-off accepted:** This is still a toy dataset. It cannot tell us whether the weights are optimal for real learners. It can only tell us whether the weights are optimal for a particular published model of learners. That is one level better than "no evaluation whatsoever."

### Decision 2: 6 candidate weight sets, chosen for comparative power

The harness evaluates:

```python
CANDIDATES = {
    "baseline":     {bkt: 0.30, fsrs: 0.25, exam: 0.25, cal: 0.10, conf: 0.10},  # current production
    "no_exam":      {bkt: 0.40, fsrs: 0.35, exam: 0.00, cal: 0.15, conf: 0.10},  # "is exam score useful?"
    "no_cal_conf":  {bkt: 0.35, fsrs: 0.30, exam: 0.35, cal: 0.00, conf: 0.00},  # "are the metacognitive signals useful?"
    "bkt_only":     {bkt: 1.00, fsrs: 0.00, exam: 0.00, cal: 0.00, conf: 0.00},  # BKT baseline
    "fsrs_only":    {bkt: 0.00, fsrs: 1.00, exam: 0.00, cal: 0.00, conf: 0.00},  # FSRS baseline
    "equal":        {bkt: 0.20, fsrs: 0.20, exam: 0.20, cal: 0.20, conf: 0.20},  # ignorance prior
}
```

Each candidate answers a specific "if we changed X, would it matter?" question. A reviewer looking at the report can see whether the baseline is on the Pareto frontier or dominated by a simpler set.

### Decision 3: Three evaluation metrics, not one

**Options considered:**

- **(A) logloss only** — simplest, but hides calibration failures (a well-calibrated model can have the same logloss as a sharp-but-miscalibrated one).
- **(B) logloss + AUC + calibration error** — redundant but complementary. Logloss is the proper scoring rule. AUC is the discrimination measure (can you rank two nodes correctly?). Calibration error is the bias measure (when you predict 0.7, does 70% of the time the event actually happen?).

**Decision: (B) all three.**

**Rationale:** Each metric fails in a different way. Reporting all three protects against a candidate winning on one metric while silently losing on another. The cost is ~10 lines of extra Python per metric.

### Decision 4: Pure standard library, zero pip packages

**Options considered:**

- **(A) Use scikit-learn** for AUC / calibration curves. Pros: well-tested, fast. Cons: requires `uv sync scripts/` or a separate venv.
- **(B) Implement all three metrics in plain Python.** Pros: zero install footprint, can run from any worktree. Cons: ~40 lines of extra code.

**Decision: (B) plain Python.**

**Rationale:** The harness should be runnable immediately after `git clone`, from any worktree, without a setup step. The three metrics are textbook implementations that fit comfortably in 40 lines. The marginal benefit of scikit-learn's battle-tested versions is real but small for this scale (~1000-10000 rows, not millions). The benefit of "no dependency drift" is large.

### Decision 5: JSONL fixture + `--input` flag, not Python-only

**Options considered:**

- **(A) Synthetic-only harness**, no way to plug in real data.
- **(B) Support both `--synthetic N` and `--input <jsonl>`** from day one.

**Decision: (B).**

**Rationale:** The day the harness gains a real dataset, there should be zero code changes between "running on synthetic" and "running on real." The schema is fixed now so the future self doesn't have to retrofit it. Cost: ~20 lines of Python to add the JSONL loader. The included fixture (`scripts/fixtures/synthetic_fusion_sample.jsonl`) also doubles as a smoke test — you can run `python scripts/ablation_fusion_weights.py --input scripts/fixtures/synthetic_fusion_sample.jsonl` to verify the script works.

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| The ablation math drifts from `mastery_fusion.py::compute_fused_mastery` over time | Medium | Medium — harness reports become untrustworthy | Both implementations are small (<30 lines each); the script copies the exact dynamic-renormalization + clamp rule with an inline comment "mirrors mastery_fusion.py::compute_fused_mastery" |
| Synthetic distribution is not representative and misleads decisions | High | Medium | README warns explicitly "baseline for math sanity, not real-user truth"; report includes "synthetic" marker; future change re-runs against real data |
| Reviewer treats the harness output as gospel and ships weight changes without real-data validation | Medium | Medium | README has a prominent "do not ship based on synthetic alone" warning; the first line of the report JSON includes a `"data_source": "synthetic"` field |
| Script has a silent bug in metric computation | Low | High — decisions based on wrong numbers | Include a sanity-check: a perfect predictor (label == prediction) should score logloss≈0, AUC=1.0, calibration error≈0 |
| Future Phase 2+ work forgets the harness exists | Low | Low — not blocking | Link to the README from `docs/project-status/fr-exploration/A10-resolution-summary.md` Section 15 |

## Migration Plan

No migration. New files land; existing files untouched.

## Rollback Plan

`git revert` of the archive commit + `rm -rf scripts/ablation_fusion_weights.py scripts/README_ablation.md scripts/fixtures/synthetic_fusion_sample.jsonl`. No persistent state is written, no database row is created.

## Open Questions Parked for Later

- **Q-3a** (parallel ChatGPT research, not blocking this change): What is the academically standard evaluation protocol for fusion weight ablation in educational models? Does the harness need to match a specific published methodology to be credible to domain reviewers?
- **Q-6a** (parallel ChatGPT research, not blocking this change): What is the academically standard method for computing per-signal reliability (inverse variance? Beta-Bayesian posterior variance? Bayesian model averaging)? This will feed into the Phase 2 reliability-weighted fusion change.

Neither question blocks Change 2. Both are tracked in the plan document so the user can paste them to ChatGPT in parallel.
