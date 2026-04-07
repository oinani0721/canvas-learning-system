# RAGAS Offline Evaluation

> FR-KG-04 Phase 10 (openspec change `fix-fr-kg-04-schema-drift-and-sync-hardening`)

## Why

The Canvas Learning System's RAG pipeline exhibits silent quality drift over
time — retrieval heuristics, fusion weights, and reranker updates can all
reduce answer faithfulness without tripping any unit test. A single failing
RAGAS metric score detected early is worth a thousand user reports.

This document captures how to run the offline evaluation suite, extend the
evaluation dataset, and tune the CI gate thresholds.

## What RAGAS measures

We use [RAGAS](https://docs.ragas.io/) for its metrics that specifically target
the Canvas Learning System's failure modes:

| Metric                | Measures                                                            | Threshold |
|-----------------------|---------------------------------------------------------------------|-----------|
| **faithfulness**      | Does the answer ground every claim in the retrieved context?      | ≥ 0.70    |
| **answer_relevancy**  | Does the answer match the user's intent?                          | ≥ 0.75    |
| **context_precision** | Did retrieval return context relevant to the question?            | ≥ 0.60    |

Initial thresholds are conservative. The CI gate runs in **observation mode**
(non-blocking) for the first week of deployment, after which a baseline is
recorded to `openspec/changes/fix-fr-kg-04-schema-drift-and-sync-hardening/ragas-baseline.md`
and the CI job switches to blocking mode.

## Running the evaluation locally

```bash
cd backend
.venv/bin/python -m pip install "ragas>=0.1.0"
.venv/bin/python -m pytest tests/regression/ragas_eval/ -v
```

The fixtures live in `backend/tests/regression/ragas_eval/fixtures/` as JSON
files organized by canvas topic area. Each file contains:

```jsonc
{
  "topic": "linear-algebra",
  "cases": [
    {
      "query": "What is an eigenvalue?",
      "expected_retrieval_contexts": [
        "An eigenvalue is a scalar λ such that ...",
        "Eigenvalues arise in characteristic polynomial ..."
      ],
      "ground_truth_answer": "An eigenvalue is a scalar λ ..."
    }
  ]
}
```

`test_ragas_faithfulness.py` walks every case, calls the production RAG
pipeline with the query, and scores the result against the ground truth.

## Extending the evaluation set

To add a new topic area:

1. Create `backend/tests/regression/ragas_eval/fixtures/<topic>.json`
2. Add 10-20 query / expected-context / ground-truth tuples
3. Prefer real user queries from historical sessions over invented ones
4. Run the suite locally to collect a baseline score
5. If the baseline is below the CI threshold, investigate BEFORE committing
   — the threshold exists to catch regressions, not to mask known issues

## CI gate

`scripts/ci/ragas_gate.py` runs the full evaluation set, computes the average
score for each metric, and exits with code 1 if any metric is below the
configured threshold.

The GitHub Actions workflow adds a separate `ragas-gate` job in
`.github/workflows/test.yml`. It is initially set to
`continue-on-error: true` (observation mode) and becomes blocking after the
first-week baseline is recorded.

## Tuning thresholds

Guidelines:

- **Never lower a threshold** without a documented reason in `ragas-baseline.md`
- **Raising a threshold** should be tied to a specific pipeline improvement
  (e.g., "Upgraded reranker from bge-v1 to bge-v2, faithfulness 0.72 → 0.81;
  raising threshold to 0.78")
- **Threshold / measurement gap** (threshold minus current score) should stay
  around 0.05-0.10 so regressions trip the gate but noise does not

## Current scaffolding status

| Component                                          | Status        |
|----------------------------------------------------|---------------|
| `backend/tests/regression/ragas_eval/` directory   | ✅ created    |
| `scripts/ci/ragas_gate.py`                         | ✅ scaffolded |
| `docs/ragas-evaluation.md` (this file)             | ✅ created    |
| Evaluation fixtures                                | ⏳ needs real queries |
| `test_ragas_faithfulness.py` production wiring     | ⏳ needs RAG pipeline handle |
| `.github/workflows/test.yml` ragas-gate job        | ⏳ add after fixtures ready |
| First-week baseline + switch to blocking mode      | ⏳ post-deploy |

## References

- [RAGAS documentation](https://docs.ragas.io/)
- Phase 10 spec: `openspec/changes/fix-fr-kg-04-schema-drift-and-sync-hardening/design.md`
- Related in-flight checker: `backend/app/services/scoring_faithfulness.py`
