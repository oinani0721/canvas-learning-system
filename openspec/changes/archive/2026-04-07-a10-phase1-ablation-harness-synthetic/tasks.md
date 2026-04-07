## 1. Pre-Change Verification

- [x] 1.1 Confirm `backend/app/services/signal_registry.py` has the 5 hardcoded weights (0.30/0.25/0.25/0.10/0.10) via grep
- [x] 1.2 Confirm `backend/app/services/mastery_fusion.py::compute_fused_mastery` uses dynamic renormalization + clamp to [0,1]
- [x] 1.3 Confirm `scripts/` directory already exists
- [x] 1.4 Confirm no existing `scripts/ablation*` file or `scripts/fixtures/` directory to avoid collision
- [x] 1.5 Verify Python 3.14 standard library provides all needed modules (`json`, `argparse`, `dataclasses`, `math`, `random`, `statistics`, `pathlib`, `typing`)

## 2. Proposal + Design Authoring

- [x] 2.1 Write `proposal.md` — cite Q3 + Q4 decisions, list 6 candidate weight sets, note zero spec delta
- [x] 2.2 Write `design.md` — BKT + FSRS data rationale, metric choice, plain-std-lib rationale, risk table, parked Q-3a / Q-6a for parallel ChatGPT research

## 3. Author the Harness Script

- [ ] 3.1 Create `scripts/ablation_fusion_weights.py`:
  - [ ] 3.1.1 Module docstring citing Q3/Q4 decisions
  - [ ] 3.1.2 `@dataclass` Row with `node_id`, `y`, `signals: Dict[str, Optional[float]]`
  - [ ] 3.1.3 `generate_synthetic(n_rows, seed)` using Yudelson BKT 2013 parameters and FSRS-4.5 DSR stability
  - [ ] 3.1.4 `fuse(signals, weights) -> float` mirroring the dynamic renormalization and clamp-to-[0,1] rule used by `mastery_fusion.py::compute_fused_mastery`
  - [ ] 3.1.5 `logloss(pred, y)` plain Python with epsilon clamp
  - [ ] 3.1.6 `auc(pred, y)` plain Python (Mann-Whitney U)
  - [ ] 3.1.7 `calibration_error(pred, y, bins=10)` plain Python (expected calibration error)
  - [ ] 3.1.8 `CANDIDATES` dict with baseline / no_exam / no_cal_conf / bkt_only / fsrs_only / equal
  - [ ] 3.1.9 `run_ablation(rows) -> dict` returning `{candidate_name: {logloss, auc, ece}}`
  - [ ] 3.1.10 `load_jsonl(path) -> List[Row]`
  - [ ] 3.1.11 `main()` with `--synthetic N` / `--input PATH` / `--output PATH` / `--seed N` / `--bins N` flags
  - [ ] 3.1.12 Sanity check: a perfect predictor row set (pred = y) scores logloss near 0, AUC = 1.0, ECE near 0 — print a pass or fail banner

## 4. Author Fixture + README

- [ ] 4.1 Create `scripts/fixtures/synthetic_fusion_sample.jsonl` (30 rows, seed=42)
- [ ] 4.2 Create `scripts/README_ablation.md`:
  - [ ] 4.2.1 Purpose + Q3/Q4 decisions
  - [ ] 4.2.2 Quickstart commands (synthetic and fixture modes)
  - [ ] 4.2.3 Report schema explanation
  - [ ] 4.2.4 Metric reading guide (logloss lower is better, AUC higher is better, ECE lower is better)
  - [ ] 4.2.5 How to plug in real data (JSONL row schema)
  - [ ] 4.2.6 Warning: synthetic results do not justify shipping weight changes

## 5. Local Run Verification

- [ ] 5.1 Run `python scripts/ablation_fusion_weights.py --synthetic 1000 --seed 42` — verify the report has 6 candidates and no NaN values
- [ ] 5.2 Run `python scripts/ablation_fusion_weights.py --input scripts/fixtures/synthetic_fusion_sample.jsonl` — verify the fixture path works
- [ ] 5.3 Run `python scripts/ablation_fusion_weights.py --synthetic 100 --seed 1` — verify small-N mode still works
- [ ] 5.4 Read the printed summary table + the generated JSON, sanity-check values (all metrics in reasonable ranges, baseline is not catastrophically worse than bkt_only or fsrs_only)
- [ ] 5.5 Clean up any `ablation_report.json` test artifacts from repo root if the script wrote one

## 6. Lint + Format + Validate

- [ ] 6.1 Run `ruff format scripts/ablation_fusion_weights.py`
- [ ] 6.2 Run `ruff check scripts/ablation_fusion_weights.py` — expect 0 violations
- [ ] 6.3 Run `npx openspec validate a10-phase1-ablation-harness-synthetic --strict` — expect 0 errors
- [ ] 6.4 Run `npx openspec status --change a10-phase1-ablation-harness-synthetic` — verify progress

## 7. Archive + Commit + Push

- [ ] 7.1 Run `npx openspec archive a10-phase1-ablation-harness-synthetic -y` (use `--skip-specs` if needed)
- [ ] 7.2 Stage `scripts/ablation_fusion_weights.py`, `scripts/README_ablation.md`, `scripts/fixtures/synthetic_fusion_sample.jsonl`, and the archive directory with specific paths
- [ ] 7.3 Commit with type `chore` or `feat` (check commitlint allowed types); cite Q3/Q4 decisions; note "no backend touches, no CI integration"
- [ ] 7.4 Verify lefthook post-commit auto-push to both `backup` and `origin` succeeds
- [ ] 7.5 Verify `git rev-parse HEAD == git rev-parse origin/main`
