# Fusion Weight Ablation Harness

Offline research tooling that measures how well several candidate weight sets
perform against a synthetic (or real) learning-event corpus. The goal is to
know whether the production fusion weights in
`backend/app/services/signal_registry.py`
(BKT 0.30 / FSRS 0.25 / Exam 0.25 / Calibration 0.10 / SelfConfidence 0.10)
are competitive, dominated, or suboptimal for the current data distribution.

This is **research tooling**. It does not enter CI, does not touch the backend
import graph, and does not ship weight changes by itself. A human reads the
report and decides.

## Why this exists (user decisions 2026-04-07)

- **Q3**: Synthetic data is allowed as the starting corpus. We do not need to
  wait for real beta-user events to begin validating the fusion math.
- **Q4**: The harness is local-only and manually invoked. It does not enter CI
  and does not consume test-runner budget.

See `openspec/changes/archive/2026-04-07-a10-phase1-ablation-harness-synthetic/`
for the full context.

## Quickstart

```bash
# Generate 1000 synthetic rows and score all 6 candidate weight sets.
python scripts/ablation_fusion_weights.py --synthetic 1000 --seed 42

# Smoke-test the script against the committed 30-row fixture.
python scripts/ablation_fusion_weights.py --input scripts/fixtures/synthetic_fusion_sample.jsonl

# Write the report to a specific path.
python scripts/ablation_fusion_weights.py --synthetic 5000 --output /tmp/ablation.json
```

The script requires only Python 3.10+ and the standard library. No `pip install`,
no `uv sync`. You can run it from any worktree without setup.

## What the script does

1. **Sanity check**: verifies the metric math on a perfect-predictor edge case.
   Fails loudly (exit 2) if the metric code has drifted.
2. **Load rows**: either generates N synthetic rows (BKT + FSRS driven — see the
   script's module docstring for the academic sources) or reads a JSONL file.
3. **Score candidates**: for each of 6 weight sets, computes the fused mastery
   for every row using the same dynamic-renormalization + clamp-to-[0,1] rule as
   `backend/app/services/mastery_fusion.py::compute_fused_mastery`.
4. **Evaluate metrics**: logloss (cross-entropy), AUC (rank-ordering), and
   expected calibration error (ECE, default 10 bins).
5. **Write JSON report + print table**.

## Candidate weight sets

| Name | BKT | FSRS | Exam | Cal | Conf | Question it answers |
|---|---|---|---|---|---|---|
| `baseline` | 0.30 | 0.25 | 0.25 | 0.10 | 0.10 | Is the production weight set competitive? |
| `no_exam` | 0.40 | 0.35 | 0.00 | 0.15 | 0.10 | Is the exam signal carrying weight? |
| `no_cal_conf` | 0.35 | 0.30 | 0.35 | 0.00 | 0.00 | Are the metacognitive signals useful? |
| `bkt_only` | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 | Single-signal BKT baseline |
| `fsrs_only` | 0.00 | 1.00 | 0.00 | 0.00 | 0.00 | Single-signal FSRS baseline |
| `equal` | 0.20 | 0.20 | 0.20 | 0.20 | 0.20 | Ignorance prior |

## Reading the report

The script prints a summary table like:

```
# Ablation report (synthetic (seed=42), n=1000)
candidate        logloss        auc        ece
-------------- ---------- ---------- ----------
baseline           0.4532     0.8124     0.0456
no_exam            0.4611     0.8087     0.0478
no_cal_conf        0.4498     0.8156     0.0443
bkt_only           0.4721     0.7982     0.0521
fsrs_only          0.5201     0.7523     0.0687
equal              0.4803     0.7891     0.0534
```

Metric reading guide:

- **logloss** (lower is better): proper scoring rule. Perfect = 0.
- **auc** (higher is better): rank-ordering accuracy. Chance = 0.5, perfect = 1.0.
- **ece** (lower is better): expected calibration error. How well the predicted
  probability matches the observed frequency. Perfect = 0.

A candidate wins overall when it is Pareto-efficient across all three metrics.
If one candidate wins logloss but loses calibration, that is not a clean win —
it is a trade-off that needs a product conversation.

## Plugging in real data

The JSONL schema is one row per line with these fields:

```json
{
  "node_id": "concept-abc",
  "y": 0.73,
  "signals": {
    "bkt": 0.68,
    "fsrs": 0.81,
    "exam": 0.65,
    "cal": null,
    "conf": 0.75
  }
}
```

- `node_id` is any string; it is used only for traceability.
- `y` is the ground-truth label, in [0, 1]. For binary labels, use 0.0 or 1.0.
  For soft labels (e.g., fraction correct over N attempts), use the fraction.
- Any signal may be `null` if the user has no data for that signal yet. The
  fusion rule skips null signals and renormalizes the remaining weights.

When real data becomes available, generate a JSONL file that conforms to this
schema and run `python scripts/ablation_fusion_weights.py --input your_data.jsonl`.
No code changes needed.

## Warning

Synthetic data is a **math-sanity tool**, not a production benchmark. The
BKT + FSRS generator is a specific model of learning; real users are not
guaranteed to behave like this model. Do not ship a weight change based on
synthetic results alone. The harness is the first step of validation, not the
last.

When real data exists, re-run the harness against that data and compare the
ranking. If the synthetic ranking and the real ranking disagree, trust the
real data.

## Maintenance

The script mirrors the production fusion rule in
`backend/app/services/mastery_fusion.py::compute_fused_mastery`. If that file
changes its formula (e.g., moves from weighted average to Beta-Bayesian
posterior fusion), update `fuse()` in this script to match. The mirroring is
deliberate: the script stays dependency-free so it can run from any worktree.

## Parked questions for parallel ChatGPT research

These were identified in the Change 2 plan session as "nice to have but not
blocking":

- **Q-3a**: What is the academically standard evaluation protocol for fusion
  weight ablation in educational models? Does the harness need to match a
  specific published methodology to be credible to domain reviewers?
- **Q-6a**: What is the academically standard method for computing per-signal
  reliability (inverse variance? Beta-Bayesian posterior variance? Bayesian
  model averaging)? This will feed into a future Phase 2 reliability-weighted
  fusion change.

These are tracked in the plan document for Phase 1 and can be resolved out-of-band.
