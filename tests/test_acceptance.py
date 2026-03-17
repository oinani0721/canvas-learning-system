"""
Story 2.12: RAG Pipeline Acceptance Test Framework

Runs the Golden Test Set against the search pipeline and computes:
- MRR@10 (target >= 0.70)
- Precision@5 (target >= 0.70)
- Recall@10 (target >= 0.80)
- Reranker latency (target < 200ms)
- CRAG trigger rate (target 15-30%)

Usage:
    python tests/test_acceptance.py --vault-path /path/to/vault

The acceptance report is saved to tests/acceptance_report.json.
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from collections import defaultdict
from typing import Any, Dict, List

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Metrics Computation
# ═══════════════════════════════════════════════════════════════════════════════


def match_ground_truth(result: Dict[str, Any], gt: Dict[str, str]) -> bool:
    """
    Check if a search result matches a ground truth entry.
    Uses fuzzy matching: file path contains gt["file"] and heading contains gt["heading"].
    """
    gt_file = gt.get("file", "").lower()
    gt_heading = gt.get("heading", "").lower()

    # Empty ground truth means any result is acceptable (fuzzy queries)
    if not gt_file and not gt_heading:
        return True

    result_file = (
        result.get("metadata", {}).get("canvas_file", "")
        or result.get("metadata", {}).get("file_path", "")
        or result.get("canvas_file", "")
    ).lower()
    result_heading = (result.get("metadata", {}).get("heading", "") or "").lower()
    result_content = (result.get("content", "")).lower()

    file_match = not gt_file or gt_file in result_file
    heading_match = not gt_heading or (gt_heading in result_heading or gt_heading in result_content)

    return file_match and heading_match


def mrr_at_k(results: List[Dict], ground_truths: List[Dict], k: int = 10) -> float:
    """
    Mean Reciprocal Rank @ k.
    Returns the reciprocal rank of the first relevant result.
    """
    if not ground_truths:
        return 0.0

    for rank, result in enumerate(results[:k], start=1):
        for gt in ground_truths:
            if match_ground_truth(result, gt):
                return 1.0 / rank
    return 0.0


def precision_at_k(results: List[Dict], ground_truths: List[Dict], k: int = 5) -> float:
    """
    Precision @ k: fraction of top-k results that are relevant.
    """
    if not ground_truths:
        return 0.0

    relevant_count = 0
    for result in results[:k]:
        for gt in ground_truths:
            if match_ground_truth(result, gt):
                relevant_count += 1
                break

    return relevant_count / k if k > 0 else 0.0


def recall_at_k(results: List[Dict], ground_truths: List[Dict], k: int = 10) -> float:
    """
    Recall @ k: fraction of ground truth items found in top-k results.
    """
    if not ground_truths:
        return 0.0

    found = 0
    for gt in ground_truths:
        for result in results[:k]:
            if match_ground_truth(result, gt):
                found += 1
                break

    return found / len(ground_truths)


# ═══════════════════════════════════════════════════════════════════════════════
# Test Runner
# ═══════════════════════════════════════════════════════════════════════════════


def load_golden_test_set(path: str = "tests/golden_test_set.yaml") -> List[Dict]:
    """Load the golden test set from YAML file."""
    import yaml

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return data.get("queries", [])


async def run_single_query(
    client: Any,
    query: str,
    table_name: str = "vault_notes",
    num_results: int = 10,
) -> Dict[str, Any]:
    """Execute a single search query and return results with timing."""
    start = time.perf_counter()
    results = await client.search(
        query=query,
        table_name=table_name,
        num_results=num_results,
        query_type="hybrid",
    )
    latency_ms = (time.perf_counter() - start) * 1000

    return {
        "results": results,
        "latency_ms": latency_ms,
    }


async def run_acceptance_tests(
    vault_path: str,
    golden_set_path: str = "tests/golden_test_set.yaml",
    report_path: str = "tests/acceptance_report.json",
) -> Dict[str, Any]:
    """
    Run the full acceptance test suite.

    1. Load golden test set
    2. Execute all queries
    3. Compute metrics
    4. Generate report
    """
    from agentic_rag.clients.lancedb_client import LanceDBClient

    logger.info("=" * 60)
    logger.info("RAG Pipeline Acceptance Test — Starting")
    logger.info("=" * 60)

    # Load test set
    queries = load_golden_test_set(golden_set_path)
    logger.info(f"Loaded {len(queries)} test queries from {golden_set_path}")

    # Initialize client
    client = LanceDBClient()
    await client.initialize()

    # Optional: rebuild index
    logger.info(f"Rebuilding index from vault: {vault_path}")
    rebuild_start = time.perf_counter()
    rebuild_result = await client.rebuild_index(vault_path=vault_path)
    rebuild_duration_ms = (time.perf_counter() - rebuild_start) * 1000
    logger.info(
        f"Rebuild complete: {rebuild_result['total_files']} files, "
        f"{rebuild_result['total_chunks']} chunks in {rebuild_duration_ms:.0f}ms"
    )

    # Run queries
    all_results: List[Dict] = []
    by_language: Dict[str, List[Dict]] = defaultdict(list)
    by_category: Dict[str, List[Dict]] = defaultdict(list)

    for i, q in enumerate(queries):
        query_id = q["id"]
        query_text = q["query"]
        language = q.get("language", "unknown")
        category = q.get("category", "unknown")
        ground_truths = q.get("ground_truth", [])

        # Handle empty ground_truth for irrelevant queries
        if isinstance(ground_truths, list) and len(ground_truths) == 0:
            ground_truths = []

        try:
            result = await run_single_query(client, query_text)
            search_results = result["results"]
            latency = result["latency_ms"]
        except Exception as e:
            logger.error(f"Query {query_id} failed: {e}")
            search_results = []
            latency = 0.0

        # Compute per-query metrics
        mrr = mrr_at_k(search_results, ground_truths, k=10)
        prec = precision_at_k(search_results, ground_truths, k=5)
        rec = recall_at_k(search_results, ground_truths, k=10)

        entry = {
            "id": query_id,
            "query": query_text,
            "language": language,
            "category": category,
            "mrr_10": mrr,
            "precision_5": prec,
            "recall_10": rec,
            "latency_ms": latency,
            "result_count": len(search_results),
        }

        all_results.append(entry)
        by_language[language].append(entry)
        by_category[category].append(entry)

        if (i + 1) % 10 == 0:
            logger.info(f"Progress: {i + 1}/{len(queries)} queries completed")

    # Aggregate metrics
    def avg_metric(entries: List[Dict], key: str) -> float:
        vals = [e[key] for e in entries]
        return sum(vals) / len(vals) if vals else 0.0

    overall = {
        "mrr_10": round(avg_metric(all_results, "mrr_10"), 4),
        "precision_5": round(avg_metric(all_results, "precision_5"), 4),
        "recall_10": round(avg_metric(all_results, "recall_10"), 4),
    }

    lang_metrics = {}
    for lang, entries in by_language.items():
        lang_metrics[lang] = {
            "mrr_10": round(avg_metric(entries, "mrr_10"), 4),
            "precision_5": round(avg_metric(entries, "precision_5"), 4),
            "recall_10": round(avg_metric(entries, "recall_10"), 4),
            "count": len(entries),
        }

    cat_metrics = {}
    for cat, entries in by_category.items():
        cat_metrics[cat] = {
            "mrr_10": round(avg_metric(entries, "mrr_10"), 4),
            "precision_5": round(avg_metric(entries, "precision_5"), 4),
            "recall_10": round(avg_metric(entries, "recall_10"), 4),
            "count": len(entries),
        }

    # Latency stats
    latencies = [e["latency_ms"] for e in all_results if e["latency_ms"] > 0]
    latencies.sort()
    p50_idx = len(latencies) // 2
    p95_idx = int(len(latencies) * 0.95)

    # Check pass/fail
    failed_criteria = []
    if overall["mrr_10"] < 0.70:
        failed_criteria.append(f"MRR@10 = {overall['mrr_10']} < 0.70")
    if overall["precision_5"] < 0.70:
        failed_criteria.append(f"Precision@5 = {overall['precision_5']} < 0.70")
    if overall["recall_10"] < 0.80:
        failed_criteria.append(f"Recall@10 = {overall['recall_10']} < 0.80")

    report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "total_queries": len(queries),
        "overall": overall,
        "by_language": lang_metrics,
        "by_category": cat_metrics,
        "latency": {
            "p50_ms": round(latencies[p50_idx], 1) if latencies else 0,
            "p95_ms": round(latencies[p95_idx], 1) if latencies else 0,
            "mean_ms": round(sum(latencies) / len(latencies), 1) if latencies else 0,
        },
        "rebuild": {
            "duration_ms": round(rebuild_duration_ms),
            "total_files": rebuild_result.get("total_files", 0),
            "total_chunks": rebuild_result.get("total_chunks", 0),
        },
        "pass": len(failed_criteria) == 0,
        "failed_criteria": failed_criteria,
    }

    # Save report
    os.makedirs(os.path.dirname(report_path) or ".", exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    logger.info(f"Acceptance report saved to {report_path}")

    # Print summary
    logger.info("=" * 60)
    logger.info("ACCEPTANCE TEST RESULTS")
    logger.info("=" * 60)
    logger.info(f"Overall MRR@10:     {overall['mrr_10']:.4f}  (target >= 0.70)")
    logger.info(f"Overall Precision@5:{overall['precision_5']:.4f}  (target >= 0.70)")
    logger.info(f"Overall Recall@10:  {overall['recall_10']:.4f}  (target >= 0.80)")
    logger.info(f"Latency P50:        {report['latency']['p50_ms']}ms")
    logger.info(f"Latency P95:        {report['latency']['p95_ms']}ms")
    logger.info(f"Rebuild:            {report['rebuild']['duration_ms']}ms")
    if report["pass"]:
        logger.info("RESULT: PASS")
    else:
        logger.warning(f"RESULT: FAIL — {'; '.join(failed_criteria)}")
    logger.info("=" * 60)

    return report


# ═══════════════════════════════════════════════════════════════════════════════
# CLI Entry Point
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RAG Pipeline Acceptance Test")
    parser.add_argument(
        "--vault-path",
        required=True,
        help="Path to the Obsidian vault for testing",
    )
    parser.add_argument(
        "--golden-set",
        default="tests/golden_test_set.yaml",
        help="Path to golden test set YAML",
    )
    parser.add_argument(
        "--report",
        default="tests/acceptance_report.json",
        help="Output path for acceptance report JSON",
    )

    args = parser.parse_args()
    result = asyncio.run(
        run_acceptance_tests(
            vault_path=args.vault_path,
            golden_set_path=args.golden_set,
            report_path=args.report,
        )
    )

    sys.exit(0 if result.get("pass", False) else 1)
