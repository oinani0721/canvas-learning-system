## Why

The 5-signal fusion weights in `signal_registry.py` (BKT 0.30 / FSRS 0.25 / Exam 0.25 / Calibration 0.10 / SelfConfidence 0.10) are hardcoded literature-guided defaults. They have never been empirically validated against any data — real or synthetic. If the calibration and self-confidence signals are effectively noise, `0.20` of the fused-mastery budget is being spent on them for no measurable accuracy gain. If BKT and FSRS are redundant, their combined `0.55` weight is overinvested. We have no way to know without an evaluation harness.

User decisions 2026-04-07 (A10 Phase 1 plan session 3) unblocked building that harness immediately:

- **Q3**: Synthetic data is allowed as the starting corpus. We do not need to wait for real beta-user data before building the first version of the harness.
- **Q4**: The harness runs **only locally and manually**. It is tooling, not a production codepath. It does not enter CI, does not block deploys, and consumes zero shared budget.

These two decisions together mean the harness can be written today, validated against synthetic data today, and sit dormant until we have real data to plug in — at which point the only work is swapping the data source.

This change also creates the evaluation contract that future Phase 2 work (reliability-weighted fusion, advance strategies, ReviewPriorityEngine) can reuse. Without this harness, those later decisions would have no ground-truth baseline to measure against.

## What Changes

- Add `scripts/ablation_fusion_weights.py` — a self-contained offline harness that:
  - Generates synthetic learning events using published BKT + FSRS parameters
  - Implements the same fusion math as `mastery_fusion.py::compute_fused_mastery` (dynamic renormalization + clamp) in plain Python (no backend imports, to stay dependency-free)
  - Scores 6 candidate weight sets against the data using logloss, AUC, and calibration error
  - Writes a JSON report (`ablation_report.json`) and prints a summary table to stdout
  - Accepts either `--synthetic N` (generate N rows on the fly) or `--input <jsonl>` (load real data)
- Add `scripts/fixtures/synthetic_fusion_sample.jsonl` — a tiny ~30-row fixture to exercise the `--input` code path and give a quick smoke-test command
- Add `scripts/README_ablation.md` — a user-facing runbook covering the run command, report interpretation, and how to plug in real data later
- **No `specs/` delta**: This is pure research tooling. It does not define any capability behavior that could regress, and it does not interact with any existing spec. Per OpenSpec conventions, tooling-only changes archive without a spec delta.
- **No `lefthook.yml` change**: Per user decision Q4 this stays out of CI.

## Capabilities

### New Capabilities

None. This change is research tooling only.

### Modified Capabilities

None. No existing capability's requirements are touched.

## Impact

- **New files**: `scripts/ablation_fusion_weights.py` (~400 lines), `scripts/README_ablation.md` (~100 lines), `scripts/fixtures/synthetic_fusion_sample.jsonl` (~30 rows).
- **Existing code**: Zero touches to `backend/app/services/`, `backend/tests/`, `frontend/`, or any other production path.
- **Dependencies**: Uses only Python standard library (`json`, `argparse`, `dataclasses`, `math`, `random`, `statistics`, `pathlib`). No new `pip` packages, no new system packages. This keeps the script runnable from any worktree without `uv sync`.
- **CI**: None. The script is invoked manually by the developer. `lefthook.yml` is untouched, A11 pre-push gate is untouched.
- **Documentation**: The README and the inline docstrings are the primary documentation. The change's `design.md` records the academic citations for the synthetic data distribution.
- **Rollback**: `git revert` of the archive commit plus deletion of the three new files. No state is stored, no DB rows written.
- **Risk**: Low. The script cannot break anything it does not own. A bug in the ablation math would mislead a human reader but cannot affect production behavior.
