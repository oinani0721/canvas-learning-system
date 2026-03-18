"""
Story 2.12: RAG Pipeline Acceptance Test Framework

Runs the Golden Test Set against the search pipeline and computes:
- MRR@10 (target >= 0.70)                           [AC-2]
- Precision@5 (target >= 0.70)                       [AC-3]
- Recall@10 (target >= 0.80)                         [AC-4]
- Full rebuild performance + fingerprint/FTS verify  [AC-5]
- Reranker latency P50/P95/P99 + A/B MRR compare    [AC-6]
- CRAG trigger rate + irrelevant degradation         [AC-7]
- Chinese/English parity (diff < 0.10)               [AC-8]
- JSON acceptance report                             [AC-9]

Usage:
    python tests/test_acceptance.py --vault-path /path/to/vault

The acceptance report is saved to tests/acceptance_report.json.

Callers:
    - CLI entry point (manual invocation)
    - CI pipeline (future, not this Story)

Functions:
    match_ground_truth        -> used by mrr_at_k, precision_at_k, recall_at_k
    mrr_at_k                  -> used by run_acceptance_tests
    precision_at_k            -> used by run_acceptance_tests
    recall_at_k               -> used by run_acceptance_tests
    load_golden_test_set      -> used by run_acceptance_tests
    run_single_query          -> used by run_acceptance_tests
    run_reranker_ab_test      -> used by run_acceptance_tests [AC-6]
    run_crag_trigger_test     -> used by run_acceptance_tests [AC-7]
    verify_rebuild_integrity  -> used by run_acceptance_tests [AC-5]
    generate_acceptance_report-> used by run_acceptance_tests [AC-9]
    run_acceptance_tests      -> used by __main__
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


# ============================================================================
# Metrics Computation  [AC-2, AC-3, AC-4]
# ============================================================================


def match_ground_truth(result: Dict[str, Any], gt: Dict[str, str]) -> bool:
    """
    Check if a search result matches a ground truth entry.

    Uses fuzzy matching per spec Task 2.5:
    - result's canvas_file contains gt["file"]
    - result's heading or content contains gt["heading"]

    Args:
        result: A search result dict from LanceDBClient.search().
        gt: Ground truth dict with "file" and "heading" keys.

    Returns:
        True if the result matches the ground truth entry.
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

    Returns the reciprocal rank of the first relevant result within top-k.
    If no relevant result is found, returns 0.0.

    Args:
        results: Search result list from pipeline.
        ground_truths: List of ground truth dicts.
        k: Cutoff rank.

    Returns:
        Reciprocal rank float in [0, 1].
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

    Args:
        results: Search result list.
        ground_truths: List of ground truth dicts.
        k: Cutoff.

    Returns:
        Precision float in [0, 1].
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

    Args:
        results: Search result list.
        ground_truths: List of ground truth dicts.
        k: Cutoff.

    Returns:
        Recall float in [0, 1].
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


# ============================================================================
# Golden Test Set Loader  [AC-1]
# ============================================================================


def load_golden_test_set(path: str = "tests/golden_test_set.yaml") -> List[Dict]:
    """
    Load the golden test set from YAML file.

    Args:
        path: Path to golden_test_set.yaml.

    Returns:
        List of query dicts with id, query, language, category, ground_truth.
    """
    import yaml

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    queries = data.get("queries", [])
    logger.info(f"Loaded {len(queries)} golden test queries from {path}")
    return queries


# ============================================================================
# Single Query Runner
# ============================================================================


async def run_single_query(
    client: Any,
    query: str,
    table_name: str = "vault_notes",
    num_results: int = 10,
) -> Dict[str, Any]:
    """
    Execute a single search query and return results with timing.

    Args:
        client: Initialized LanceDBClient instance.
        query: Query text.
        table_name: LanceDB table name.
        num_results: Number of results to retrieve.

    Returns:
        Dict with "results" (List[Dict]) and "latency_ms" (float).
    """
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


# ============================================================================
# Rebuild Integrity Verification  [AC-5]
# ============================================================================


async def verify_rebuild_integrity(
    client: Any,
    vault_path: str,
    rebuild_result: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Verify rebuild correctness: fingerprint table, FTS index, file counts.

    Called by: run_acceptance_tests (AC-5 verification step).

    Args:
        client: Initialized LanceDBClient instance (post-rebuild).
        vault_path: Path to the vault.
        rebuild_result: Dict returned by client.rebuild_index().

    Returns:
        Dict with verification results:
            fingerprint_ok, fts_ok, file_count_match, details.
    """
    details = []

    # 1. Verify fingerprint table has records == total_files
    fingerprint_ok = False
    expected_files = rebuild_result.get("total_files", 0)
    try:
        fp_table_name = client.FINGERPRINT_TABLE
        if fp_table_name in client._tables_cache:
            fp_table = client._tables_cache[fp_table_name]
            fp_count = fp_table.count_rows()
            fingerprint_ok = fp_count >= expected_files
            details.append(f"Fingerprint records: {fp_count} (expected >= {expected_files})")
        else:
            details.append("Fingerprint table not in cache (may not be created yet)")
    except Exception as e:
        details.append(f"Fingerprint check error: {e}")

    # 2. Verify FTS index works by running a keyword search
    fts_ok = False
    try:
        # Use a common Chinese word that's likely in any academic vault
        fts_results = await client.search(
            query="定义",
            table_name="vault_notes",
            num_results=3,
            query_type="hybrid",
        )
        fts_ok = len(fts_results) > 0
        details.append(f"FTS verification: {len(fts_results)} results for '定义'")
    except Exception as e:
        details.append(f"FTS verification error: {e}")

    # 3. Verify file count matches filesystem
    skip_dirs = [".obsidian", ".git", ".trash", "node_modules"]
    actual_files = 0
    for _root, dirs, files in os.walk(vault_path):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        actual_files += sum(1 for f in files if f.endswith(".md"))

    file_count_match = rebuild_result.get("total_files", 0) == actual_files
    details.append(f"File count: rebuild={rebuild_result.get('total_files', 0)}, filesystem={actual_files}")

    return {
        "fingerprint_ok": fingerprint_ok,
        "fts_ok": fts_ok,
        "file_count_match": file_count_match,
        "details": details,
    }


# ============================================================================
# Reranker A/B Latency Test  [AC-6]
# ============================================================================


async def run_reranker_ab_test(
    client: Any,
    queries: List[Dict],
    max_queries: int = 20,
) -> Dict[str, Any]:
    """
    Test reranker latency and compute A/B MRR improvement.

    For each query:
    - Run search to get top-20 candidates (pre-rerank)
    - Run reranker on top-20
    - Measure reranker latency
    - Compare MRR before/after reranking

    Called by: run_acceptance_tests (AC-6 step).

    Args:
        client: Initialized LanceDBClient.
        queries: Golden test set queries (only knowledge_point used).
        max_queries: Max queries to test.

    Returns:
        Dict with p50_ms, p95_ms, p99_ms, mrr_before, mrr_after, mrr_improvement.
    """
    from agentic_rag.reranking import get_reranker

    reranker = get_reranker()
    if reranker is None:
        logger.warning("[AC-6] Reranker not available (sentence-transformers not installed)")
        return {
            "p50_ms": 0,
            "p95_ms": 0,
            "p99_ms": 0,
            "mrr_before": 0,
            "mrr_after": 0,
            "mrr_improvement": 0,
            "available": False,
        }

    # Select knowledge_point queries with non-empty ground truth
    test_queries = [q for q in queries if q.get("category") == "knowledge_point" and q.get("ground_truth")][
        :max_queries
    ]

    latencies: List[float] = []
    mrr_before_list: List[float] = []
    mrr_after_list: List[float] = []

    for q in test_queries:
        query_text = q["query"]
        ground_truths = q.get("ground_truth", [])

        try:
            # Get pre-rerank results (top-20)
            pre_results = await client.search(
                query=query_text,
                table_name="vault_notes",
                num_results=20,
                query_type="hybrid",
            )

            if not pre_results:
                continue

            # MRR before reranking
            mrr_before = mrr_at_k(pre_results, ground_truths, k=10)
            mrr_before_list.append(mrr_before)

            # Run reranker with timing
            documents = [r.get("content", "") for r in pre_results]
            start_t = time.perf_counter()
            reranked = await reranker.rerank(
                query=query_text,
                documents=documents,
                top_k=10,
                return_documents=False,
            )
            latency_ms = (time.perf_counter() - start_t) * 1000
            latencies.append(latency_ms)

            # Reconstruct results in reranked order for MRR calculation.
            # Defensive: when return_documents=False, each entry should have
            # an "index" key mapping back to the original result list.  If the
            # reranker implementation returns dicts without "index" (e.g. when
            # it inlines documents), fall back to original ordering.
            reranked_results = []
            for r in reranked:
                idx = r.get("index")
                if idx is None:
                    # Reranker returned document dict without index — skip
                    logger.debug("[AC-6] Reranked entry missing 'index' key, skipping")
                    continue
                if idx < len(pre_results):
                    reranked_results.append(pre_results[idx])

            mrr_after = mrr_at_k(reranked_results, ground_truths, k=10)
            mrr_after_list.append(mrr_after)

        except Exception as e:
            logger.warning(f"[AC-6] Reranker test failed for '{query_text[:40]}': {e}")

    if not latencies:
        return {
            "p50_ms": 0,
            "p95_ms": 0,
            "p99_ms": 0,
            "mrr_before": 0,
            "mrr_after": 0,
            "mrr_improvement": 0,
            "available": True,
            "tested_queries": 0,
        }

    latencies.sort()
    n = len(latencies)
    p50 = latencies[n // 2]
    p95 = latencies[int(n * 0.95)] if n >= 2 else latencies[-1]
    p99 = latencies[int(n * 0.99)] if n >= 2 else latencies[-1]

    avg_mrr_before = sum(mrr_before_list) / len(mrr_before_list) if mrr_before_list else 0
    avg_mrr_after = sum(mrr_after_list) / len(mrr_after_list) if mrr_after_list else 0

    return {
        "p50_ms": round(p50, 1),
        "p95_ms": round(p95, 1),
        "p99_ms": round(p99, 1),
        "mrr_before": round(avg_mrr_before, 4),
        "mrr_after": round(avg_mrr_after, 4),
        "mrr_improvement": round(avg_mrr_after - avg_mrr_before, 4),
        "available": True,
        "tested_queries": len(latencies),
    }


# ============================================================================
# CRAG Trigger Rate Test  [AC-7]
# ============================================================================


async def run_crag_trigger_test(
    client: Any,
    queries: List[Dict],
) -> Dict[str, Any]:
    """
    Test CRAG quality gate trigger rate across all query categories.

    Simulates the CRAG quality check by examining reranker scores:
    - If top-3 average score < quality_threshold -> "low" (CRAG triggered)
    - Counts trigger rate across all queries
    - Verifies irrelevant queries trigger degradation
    - Verifies relevant queries have low false-positive rate

    LIMITATION: This is a SIMULATION using raw reranker scores as a proxy
    for the real CRAG binary LLM grading pipeline (Story 2.6). The actual
    CRAG pipeline uses LLM-based yes/no document grading, which produces
    different trigger decisions than simple score thresholding. Results
    from this test approximate but do not exactly match production behavior.
    A full end-to-end CRAG test requires a running LLM backend.

    Called by: run_acceptance_tests (AC-7 step).

    Args:
        client: Initialized LanceDBClient.
        queries: Full golden test set.

    Returns:
        Dict with trigger_rate, irrelevant_degradation_rate, false_positive_rate.
    """
    from agentic_rag.config import DEFAULT_CONFIG

    quality_threshold = DEFAULT_CONFIG.get("quality_threshold", 0.7)

    total_queries = 0
    triggered_count = 0  # Queries judged "low"
    irrelevant_total = 0
    irrelevant_triggered = 0
    relevant_total = 0
    relevant_triggered = 0  # False positives (relevant query judged low)

    for q in queries:
        category = q.get("category", "unknown")
        query_text = q["query"]

        try:
            result = await run_single_query(client, query_text, num_results=10)
            search_results = result["results"]
        except Exception as e:
            logger.warning(f"[AC-7] CRAG test failed for '{query_text[:40]}': {e}")
            continue

        total_queries += 1

        # Simulate CRAG quality check: top-3 score average
        top3_scores = [r.get("score", 0.0) for r in search_results[:3]]
        avg_score = sum(top3_scores) / len(top3_scores) if top3_scores else 0.0

        is_low = avg_score < quality_threshold or len(search_results) == 0

        if is_low:
            triggered_count += 1

        if category == "irrelevant":
            irrelevant_total += 1
            if is_low or len(search_results) == 0:
                irrelevant_triggered += 1
        elif category in ("knowledge_point", "cross_lingual", "file_locate"):
            relevant_total += 1
            if is_low:
                relevant_triggered += 1

    trigger_rate = triggered_count / total_queries if total_queries > 0 else 0
    irrelevant_degradation_rate = irrelevant_triggered / irrelevant_total if irrelevant_total > 0 else 0
    false_positive_rate = relevant_triggered / relevant_total if relevant_total > 0 else 0

    return {
        "trigger_rate": round(trigger_rate, 4),
        "irrelevant_degradation_rate": round(irrelevant_degradation_rate, 4),
        "false_positive_rate": round(false_positive_rate, 4),
        "total_queries": total_queries,
        "triggered_count": triggered_count,
        "irrelevant_total": irrelevant_total,
        "irrelevant_triggered": irrelevant_triggered,
        "relevant_total": relevant_total,
        "relevant_false_positives": relevant_triggered,
    }


# ============================================================================
# Acceptance Report Generator  [AC-9]
# ============================================================================


def generate_acceptance_report(
    overall: Dict[str, float],
    lang_metrics: Dict[str, Dict],
    cat_metrics: Dict[str, Dict],
    latency_stats: Dict[str, float],
    rebuild_info: Dict[str, Any],
    rebuild_integrity: Dict[str, Any],
    reranker_info: Dict[str, Any],
    crag_info: Dict[str, Any],
    total_queries: int,
    per_query_results: List[Dict],
) -> Dict[str, Any]:
    """
    Generate the structured acceptance report per AC-9 spec.

    Called by: run_acceptance_tests.

    Args:
        overall: Overall MRR/Precision/Recall.
        lang_metrics: Per-language metrics.
        cat_metrics: Per-category metrics.
        latency_stats: P50/P95/mean latency.
        rebuild_info: Rebuild duration/files/chunks.
        rebuild_integrity: Fingerprint/FTS verification.
        reranker_info: Reranker A/B test results.
        crag_info: CRAG trigger rate results.
        total_queries: Total query count.
        per_query_results: Detailed per-query results.

    Returns:
        Complete report dict.
    """
    failed_criteria: List[str] = []

    # AC-2: MRR@10 >= 0.70
    if overall["mrr_10"] < 0.70:
        failed_criteria.append(f"MRR@10 = {overall['mrr_10']:.4f} < 0.70")

    # AC-3: Precision@5 >= 0.70
    if overall["precision_5"] < 0.70:
        failed_criteria.append(f"Precision@5 = {overall['precision_5']:.4f} < 0.70")

    # AC-4: Recall@10 >= 0.80
    if overall["recall_10"] < 0.80:
        failed_criteria.append(f"Recall@10 = {overall['recall_10']:.4f} < 0.80")

    # AC-5: Rebuild integrity
    if not rebuild_integrity.get("fingerprint_ok", False):
        failed_criteria.append("Fingerprint table incomplete after rebuild")
    if not rebuild_integrity.get("fts_ok", False):
        failed_criteria.append("FTS index not working after rebuild")

    # AC-6: Reranker latency < 200ms (P95)
    if reranker_info.get("available", False):
        if reranker_info.get("p95_ms", 0) > 200:
            failed_criteria.append(f"Reranker P95 latency = {reranker_info['p95_ms']}ms > 200ms")
        if reranker_info.get("mrr_improvement", 0) < 0.10:
            failed_criteria.append(f"Reranker MRR improvement = {reranker_info['mrr_improvement']:.4f} < 0.10")

    # AC-7: CRAG trigger rate 15-30%
    crag_rate = crag_info.get("trigger_rate", 0)
    if crag_rate < 0.15 or crag_rate > 0.30:
        failed_criteria.append(f"CRAG trigger rate = {crag_rate:.2%} outside 15-30% range")
    if crag_info.get("irrelevant_degradation_rate", 0) < 1.0:
        failed_criteria.append(
            f"Irrelevant query degradation = {crag_info.get('irrelevant_degradation_rate', 0):.0%} < 100%"
        )
    if crag_info.get("false_positive_rate", 0) > 0.05:
        failed_criteria.append(f"CRAG false positive rate = {crag_info.get('false_positive_rate', 0):.2%} > 5%")

    # AC-8: Chinese/English parity (diff < 0.10)
    zh_metrics = lang_metrics.get("zh", {})
    en_metrics = lang_metrics.get("en", {})
    if zh_metrics and en_metrics:
        for metric_key in ("mrr_10", "precision_5", "recall_10"):
            zh_val = zh_metrics.get(metric_key, 0)
            en_val = en_metrics.get(metric_key, 0)
            diff = abs(zh_val - en_val)
            if diff > 0.10:
                failed_criteria.append(f"ZH/EN {metric_key} gap = {diff:.4f} > 0.10 (zh={zh_val:.4f}, en={en_val:.4f})")

    report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "total_queries": total_queries,
        "overall": overall,
        "by_language": lang_metrics,
        "by_category": cat_metrics,
        "reranker": reranker_info,
        "crag": crag_info,
        "latency": latency_stats,
        "rebuild": {
            **rebuild_info,
            "integrity": rebuild_integrity,
        },
        "pass": len(failed_criteria) == 0,
        "failed_criteria": failed_criteria,
        "per_query_details": per_query_results,
    }

    return report


# ============================================================================
# Main Acceptance Test Runner  [AC-1 through AC-9]
# ============================================================================


async def run_acceptance_tests(
    vault_path: str,
    golden_set_path: str = "tests/golden_test_set.yaml",
    report_path: str = "tests/acceptance_report.json",
) -> Dict[str, Any]:
    """
    Run the full acceptance test suite.

    Steps:
    1. Load golden test set                              [AC-1]
    2. Rebuild index + verify integrity                  [AC-5]
    3. Execute all queries, compute MRR/Prec/Recall      [AC-2, AC-3, AC-4]
    4. Run reranker A/B test                             [AC-6]
    5. Run CRAG trigger rate test                        [AC-7]
    6. Check Chinese/English parity                      [AC-8]
    7. Generate and save report                          [AC-9]

    LIMITATION: This test exercises LanceDB search + reranker in isolation.
    It does NOT walk the full LangGraph StateGraph (retrieve -> fuse ->
    rerank -> check_quality -> compress) as a production query would.
    The CRAG trigger test uses score-threshold simulation rather than
    LLM binary grading. A full integration test against the StateGraph
    requires all services (Neo4j, Graphiti, LLM) to be running.

    Called by: __main__ CLI entry point.

    Args:
        vault_path: Obsidian vault directory path.
        golden_set_path: Path to golden_test_set.yaml.
        report_path: Output path for acceptance_report.json.

    Returns:
        Report dict (also saved to report_path).
    """
    from agentic_rag.clients.lancedb_client import LanceDBClient

    logger.info("=" * 60)
    logger.info("RAG Pipeline Acceptance Test -- Starting")
    logger.info("=" * 60)

    # ── Step 1: Load golden test set [AC-1] ──
    queries = load_golden_test_set(golden_set_path)
    if len(queries) < 50:
        logger.warning(f"Golden test set has {len(queries)} queries (spec requires 50+)")

    # ── Initialize client ──
    client = LanceDBClient()
    await client.initialize()

    # ── Step 2: Rebuild index [AC-5] ──
    logger.info(f"Rebuilding index from vault: {vault_path}")
    rebuild_start = time.perf_counter()
    rebuild_result = await client.rebuild_index(vault_path=vault_path)
    rebuild_duration_ms = (time.perf_counter() - rebuild_start) * 1000
    logger.info(
        f"Rebuild complete: {rebuild_result['total_files']} files, "
        f"{rebuild_result['total_chunks']} chunks in {rebuild_duration_ms:.0f}ms"
    )

    rebuild_info = {
        "duration_ms": round(rebuild_duration_ms),
        "total_files": rebuild_result.get("total_files", 0),
        "total_chunks": rebuild_result.get("total_chunks", 0),
    }

    # Verify rebuild integrity [AC-5]
    rebuild_integrity = await verify_rebuild_integrity(client, vault_path, rebuild_result)
    logger.info(f"Rebuild integrity: {rebuild_integrity}")

    # ── Step 3: Run all queries [AC-2, AC-3, AC-4] ──
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
            "latency_ms": round(latency, 1),
            "result_count": len(search_results),
        }

        all_results.append(entry)
        by_language[language].append(entry)
        by_category[category].append(entry)

        if (i + 1) % 10 == 0:
            logger.info(f"Progress: {i + 1}/{len(queries)} queries completed")

    logger.info(f"All {len(queries)} queries completed")

    # ── Aggregate metrics ──
    def avg_metric(entries: List[Dict], key: str) -> float:
        vals = [e[key] for e in entries]
        return sum(vals) / len(vals) if vals else 0.0

    overall = {
        "mrr_10": round(avg_metric(all_results, "mrr_10"), 4),
        "precision_5": round(avg_metric(all_results, "precision_5"), 4),
        "recall_10": round(avg_metric(all_results, "recall_10"), 4),
    }

    lang_metrics: Dict[str, Dict] = {}
    for lang, entries in by_language.items():
        lang_metrics[lang] = {
            "mrr_10": round(avg_metric(entries, "mrr_10"), 4),
            "precision_5": round(avg_metric(entries, "precision_5"), 4),
            "recall_10": round(avg_metric(entries, "recall_10"), 4),
            "count": len(entries),
        }

    cat_metrics: Dict[str, Dict] = {}
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
    n_lat = len(latencies)
    latency_stats = {
        "p50_ms": round(latencies[n_lat // 2], 1) if n_lat > 0 else 0,
        "p95_ms": round(latencies[int(n_lat * 0.95)], 1) if n_lat >= 2 else (round(latencies[-1], 1) if n_lat else 0),
        "mean_ms": round(sum(latencies) / n_lat, 1) if n_lat > 0 else 0,
    }

    # ── Step 4: Reranker A/B test [AC-6] ──
    logger.info("Running reranker A/B test...")
    reranker_info = await run_reranker_ab_test(client, queries, max_queries=20)
    logger.info(
        f"Reranker test: P50={reranker_info.get('p50_ms')}ms, improvement={reranker_info.get('mrr_improvement')}"
    )

    # ── Step 5: CRAG trigger rate test [AC-7] ──
    logger.info("Running CRAG trigger rate test...")
    crag_info = await run_crag_trigger_test(client, queries)
    logger.info(
        f"CRAG test: trigger_rate={crag_info.get('trigger_rate'):.2%}, FP={crag_info.get('false_positive_rate'):.2%}"
    )

    # ── Step 6 + 7: Generate report [AC-8, AC-9] ──
    report = generate_acceptance_report(
        overall=overall,
        lang_metrics=lang_metrics,
        cat_metrics=cat_metrics,
        latency_stats=latency_stats,
        rebuild_info=rebuild_info,
        rebuild_integrity=rebuild_integrity,
        reranker_info=reranker_info,
        crag_info=crag_info,
        total_queries=len(queries),
        per_query_results=all_results,
    )

    # Save report
    os.makedirs(os.path.dirname(os.path.abspath(report_path)) or ".", exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    logger.info(f"Acceptance report saved to {report_path}")

    # Print summary
    logger.info("=" * 60)
    logger.info("ACCEPTANCE TEST RESULTS")
    logger.info("=" * 60)
    logger.info(f"Overall MRR@10:      {overall['mrr_10']:.4f}  (target >= 0.70)")
    logger.info(f"Overall Precision@5: {overall['precision_5']:.4f}  (target >= 0.70)")
    logger.info(f"Overall Recall@10:   {overall['recall_10']:.4f}  (target >= 0.80)")
    logger.info(f"Search Latency P50:  {latency_stats['p50_ms']}ms")
    logger.info(f"Search Latency P95:  {latency_stats['p95_ms']}ms")
    logger.info(f"Rebuild Duration:    {rebuild_info['duration_ms']}ms")
    if reranker_info.get("available", False):
        logger.info(f"Reranker P50:        {reranker_info['p50_ms']}ms  (target < 200ms)")
        logger.info(f"Reranker P95:        {reranker_info['p95_ms']}ms")
        logger.info(f"Reranker MRR lift:   {reranker_info['mrr_improvement']:+.4f}  (target >= +0.10)")
    else:
        logger.info("Reranker:            NOT AVAILABLE (sentence-transformers not installed)")
    logger.info(f"CRAG trigger rate:   {crag_info['trigger_rate']:.2%}  (target 15-30%)")
    logger.info(f"CRAG irrelevant deg: {crag_info['irrelevant_degradation_rate']:.0%}  (target 100%)")
    logger.info(f"CRAG false positive: {crag_info['false_positive_rate']:.2%}  (target < 5%)")

    # Chinese/English parity summary
    zh_m = lang_metrics.get("zh", {})
    en_m = lang_metrics.get("en", {})
    if zh_m and en_m:
        for mk in ("mrr_10", "precision_5", "recall_10"):
            diff = abs(zh_m.get(mk, 0) - en_m.get(mk, 0))
            status = "OK" if diff <= 0.10 else "FAIL"
            logger.info(f"ZH/EN {mk} gap:  {diff:.4f}  ({status}, target < 0.10)")

    if report["pass"]:
        logger.info("RESULT: PASS")
    else:
        logger.warning(f"RESULT: FAIL -- {len(report['failed_criteria'])} criteria failed:")
        for fc in report["failed_criteria"]:
            logger.warning(f"  - {fc}")
    logger.info("=" * 60)

    return report


# ============================================================================
# CLI Entry Point
# ============================================================================

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
