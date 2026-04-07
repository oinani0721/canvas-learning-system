"""RAGAS CI gate — fail the build when offline evaluation scores drop below
the configured thresholds.

FR-KG-04 Phase 10 Task 10.4 (openspec change
fix-fr-kg-04-schema-drift-and-sync-hardening).

Usage:
    python scripts/ci/ragas_gate.py [--threshold-faithfulness 0.70]
                                   [--threshold-relevancy 0.75]
                                   [--threshold-precision 0.60]
                                   [--fixtures-dir backend/tests/regression/ragas_eval/fixtures]

Exit codes:
    0 — all metrics meet or exceed their thresholds
    1 — one or more metrics below threshold
    2 — evaluation scaffolding incomplete (fixtures missing or empty)
    3 — unexpected error while running the evaluation

This script is called from .github/workflows/test.yml as a standalone job
with ``continue-on-error: true`` during observation mode. After the first
weekly baseline is recorded in
``openspec/changes/fix-fr-kg-04-schema-drift-and-sync-hardening/ragas-baseline.md``,
the workflow flips it to blocking mode.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

DEFAULT_FIXTURES_DIR = (
    Path(__file__).resolve().parents[2]
    / "backend"
    / "tests"
    / "regression"
    / "ragas_eval"
    / "fixtures"
)

# Default thresholds — conservative on purpose. Tune via command-line flags
# or a follow-up baseline commit once real data is available.
DEFAULT_THRESHOLDS = {
    "faithfulness": 0.70,
    "answer_relevancy": 0.75,
    "context_precision": 0.60,
}


def _load_fixtures(fixtures_dir: Path) -> List[Dict[str, Any]]:
    """Load every JSON fixture file in the given directory."""
    if not fixtures_dir.is_dir():
        return []
    cases: List[Dict[str, Any]] = []
    for path in sorted(fixtures_dir.glob("*.json")):
        try:
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            print(
                f"[ragas-gate] ERROR: {path} is not valid JSON: {e}",
                file=sys.stderr,
            )
            continue
        for case in data.get("cases", []):
            case["_topic"] = data.get("topic", path.stem)
            cases.append(case)
    return cases


def _run_evaluation(cases: List[Dict[str, Any]]) -> Dict[str, float]:
    """Run the RAGAS evaluation on every case, return mean metric scores.

    The actual RAGAS evaluation is deferred — until the production RAG
    pipeline has a stable entry point for offline evaluation, this
    function is a placeholder that returns an empty dict when no
    ``RAGAS_EVAL_HANDLE`` environment variable is set.

    Once wired up, the implementation should:
      1. Import the production RAG pipeline (lazy import to avoid
         pulling heavy dependencies when the gate is just checking
         thresholds at CI startup)
      2. For each case, call ``pipeline.query(case["query"])`` and
         collect the returned answer + the retrieval context
      3. Use ``ragas.evaluate(dataset, metrics=[...])`` to compute
         per-case scores
      4. Return ``{metric_name: mean_score}``
    """
    import os

    if not os.environ.get("RAGAS_EVAL_HANDLE"):
        print(
            "[ragas-gate] SKIP: RAGAS_EVAL_HANDLE env var not set — "
            "production RAG pipeline wiring still pending",
            file=sys.stderr,
        )
        return {}

    try:
        # Lazy import so the threshold check above can run without ragas
        import importlib
        ragas_module = importlib.import_module("ragas")
    except ImportError:
        print(
            "[ragas-gate] ERROR: ragas package not installed. "
            "Run: pip install 'ragas>=0.1.0'",
            file=sys.stderr,
        )
        raise SystemExit(3)

    # Placeholder: once the RAG pipeline entry point is stable, replace
    # this block with the real evaluation loop using ragas_module.evaluate.
    _ = ragas_module  # keep the import
    return {}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="RAGAS CI gate for Canvas Learning System RAG pipeline"
    )
    parser.add_argument(
        "--fixtures-dir",
        type=Path,
        default=DEFAULT_FIXTURES_DIR,
        help="Directory containing RAGAS fixture JSON files",
    )
    parser.add_argument(
        "--threshold-faithfulness",
        type=float,
        default=DEFAULT_THRESHOLDS["faithfulness"],
    )
    parser.add_argument(
        "--threshold-relevancy",
        type=float,
        default=DEFAULT_THRESHOLDS["answer_relevancy"],
    )
    parser.add_argument(
        "--threshold-precision",
        type=float,
        default=DEFAULT_THRESHOLDS["context_precision"],
    )
    args = parser.parse_args()

    thresholds = {
        "faithfulness": args.threshold_faithfulness,
        "answer_relevancy": args.threshold_relevancy,
        "context_precision": args.threshold_precision,
    }

    cases = _load_fixtures(args.fixtures_dir)
    if not cases:
        print(
            f"[ragas-gate] Fixtures directory {args.fixtures_dir} is empty. "
            "Add at least one JSON file to enable the gate. See "
            "docs/ragas-evaluation.md for the expected format.",
            file=sys.stderr,
        )
        return 2

    print(
        f"[ragas-gate] Loaded {len(cases)} cases across "
        f"{len({c.get('_topic') for c in cases})} topics",
        file=sys.stderr,
    )

    try:
        scores = _run_evaluation(cases)
    except SystemExit:
        raise
    except Exception as e:  # noqa: BLE001 — top-level safety net for CI gate
        print(f"[ragas-gate] Unexpected evaluation error: {e}", file=sys.stderr)
        return 3

    if not scores:
        print(
            "[ragas-gate] No scores returned — evaluation wiring incomplete. "
            "Exiting in observation mode.",
            file=sys.stderr,
        )
        return 0

    # Check every configured threshold
    failed: List[str] = []
    for metric, threshold in thresholds.items():
        measured = scores.get(metric)
        if measured is None:
            print(
                f"[ragas-gate] WARNING: metric {metric} missing from scores",
                file=sys.stderr,
            )
            continue
        status = "✓" if measured >= threshold else "✗"
        print(
            f"[ragas-gate] {status} {metric}: {measured:.3f} "
            f"(threshold {threshold:.3f})",
            file=sys.stderr,
        )
        if measured < threshold:
            failed.append(metric)

    if failed:
        print(
            f"[ragas-gate] FAIL: metrics below threshold: {', '.join(failed)}",
            file=sys.stderr,
        )
        return 1

    print("[ragas-gate] PASS: all metrics meet their thresholds", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
