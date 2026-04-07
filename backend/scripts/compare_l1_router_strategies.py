#!/usr/bin/env python3
"""
Compare rule-based vs LLM-based L1 routing on a fixed benchmark suite.

Runs 10 typical queries through both strategies and prints a side-by-side
table + summary statistics. Used to validate the A9 upgrade — the
acceptance criterion from the OpenSpec design is:

    ≥6/10 of the LLM routing decisions should pick a NON-comprehensive
    subset (i.e., the LLM provides sharper routing than rule would).

Why: The rule-based classifier defaults to "comprehensive" (all 5 channels)
whenever it can't find a keyword match — the most expensive + least focused
path. An upgrade is only worth the LLM latency cost if it reliably narrows
the channel set on queries the rule misses.

Usage:
    # From backend/ directory
    .venv/bin/python scripts/compare_l1_router_strategies.py

    # With custom model (requires GEMINI_API_KEY or AI_API_KEY set)
    L1_ROUTER_MODEL=gemini/gemini-2.0-flash .venv/bin/python scripts/compare_l1_router_strategies.py

The script exits with code 0 on success (≥6/10 non-comprehensive LLM routes)
and code 1 if the acceptance criterion is not met.

[OpenSpec change: agentic-rag-l1-llm-router]
[Phase 5 of plan: C1-E Comparison Script]
"""

from __future__ import annotations

import asyncio
import os
import sys
import time
from pathlib import Path

# Allow running from repo root OR backend/
_BACKEND = Path(__file__).resolve().parent.parent
_LIB = _BACKEND / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))


# Benchmark queries — mix of clear-intent queries + queries where rule would
# default to "comprehensive" because no keyword matches.
BENCHMARK_QUERIES: list[tuple[str, str]] = [
    # (query, expected_intent_hint_for_human_reviewer)
    ("牛顿第二定律的公式推导", "knowledge_point"),
    ("我的高等数学笔记在哪？", "file_locate"),
    ("我上次学过的线性代数章节是哪些？", "learning_history"),
    ("TCP 三次握手的过程", "knowledge_point"),
    ("找到我讨论过量子力学的那份文档", "file_locate"),
    ("复习一下最近做错的题目", "learning_history"),
    ("梯度下降与随机梯度下降的区别", "knowledge_point"),
    ("给我解释一下反向传播", "knowledge_point"),
    ("上周的积分课讲了什么内容", "learning_history"),
    ("显著性水平 alpha 的含义", "knowledge_point"),
]


async def _call_rule_router(query: str) -> tuple[str, float]:
    from agentic_rag.state_graph import classify_query_intent

    start = time.perf_counter()
    intent = classify_query_intent(query)
    elapsed_ms = (time.perf_counter() - start) * 1000
    return intent, elapsed_ms


async def _call_llm_router(
    query: str, model: str, timeout_s: float
) -> tuple[str, str, float, bool, str | None]:
    from agentic_rag.llm_router import llm_route

    result = await llm_route(query, model=model, timeout_s=timeout_s)
    return (
        result.intent,
        result.reason,
        result.latency_ms,
        result.success,
        result.error,
    )


def _format_row(
    idx: int,
    query: str,
    rule_intent: str,
    rule_latency: float,
    llm_intent: str,
    llm_reason: str,
    llm_latency: float,
    llm_ok: bool,
    divergent: bool,
) -> str:
    q_short = query if len(query) <= 28 else query[:25] + "..."
    llm_status = "OK" if llm_ok else "FAIL"
    div_marker = " *" if divergent else ""
    return (
        f"{idx:2d}  {q_short:<30}  "
        f"{rule_intent:<18}  "
        f"{llm_intent:<18} [{llm_status}]  "
        f"{rule_latency:5.1f}ms / {llm_latency:7.1f}ms"
        f"{div_marker}"
    )


async def main() -> int:
    model = os.getenv("L1_ROUTER_MODEL", "gemini/gemini-2.0-flash")
    timeout_s = float(os.getenv("L1_ROUTER_TIMEOUT", "5.0"))

    print("=" * 100)
    print("L1 Router Strategy Comparison — rule vs LLM")
    print("=" * 100)
    print(f"Model:    {model}")
    print(f"Timeout:  {timeout_s}s")
    print(f"Queries:  {len(BENCHMARK_QUERIES)}")
    print()
    print(
        f"{'#':<3} {'query':<30}  "
        f"{'rule_intent':<18}  "
        f"{'llm_intent':<26}  "
        f"{'rule_ms / llm_ms':<20}"
    )
    print("-" * 100)

    rule_comprehensive_count = 0
    llm_non_comprehensive_count = 0
    llm_failures = 0
    llm_total_latency = 0.0
    divergent_count = 0

    rows: list[str] = []

    for i, (query, _hint) in enumerate(BENCHMARK_QUERIES, start=1):
        rule_intent, rule_latency = await _call_rule_router(query)
        if rule_intent == "comprehensive":
            rule_comprehensive_count += 1

        llm_intent, llm_reason, llm_latency, llm_ok, llm_err = await _call_llm_router(
            query, model, timeout_s
        )
        llm_total_latency += llm_latency

        if not llm_ok:
            llm_failures += 1
        elif llm_intent != "comprehensive":
            llm_non_comprehensive_count += 1

        divergent = rule_intent != llm_intent
        if divergent:
            divergent_count += 1

        rows.append(
            _format_row(
                i,
                query,
                rule_intent,
                rule_latency,
                llm_intent,
                llm_reason,
                llm_latency,
                llm_ok,
                divergent,
            )
        )

    for row in rows:
        print(row)

    print("-" * 100)
    print("Summary")
    print("-" * 100)
    total = len(BENCHMARK_QUERIES)
    print(f"  rule 'comprehensive' rate:         {rule_comprehensive_count}/{total}")
    print(
        f"  llm non-'comprehensive' rate:      "
        f"{llm_non_comprehensive_count}/{total} "
        f"(target ≥{int(0.6 * total)}/{total})"
    )
    print(f"  llm failures:                      {llm_failures}/{total}")
    print(f"  divergent decisions (rule ≠ llm):  {divergent_count}/{total}")
    print(f"  llm avg latency:                   {llm_total_latency / total:.1f}ms")
    print()

    # Acceptance: ≥6/10 LLM routes non-comprehensive (documented in plan)
    threshold = int(0.6 * total)
    if llm_non_comprehensive_count >= threshold:
        print(
            f"✅ PASS — LLM routes non-comprehensive {llm_non_comprehensive_count}/{total} "
            f"(≥{threshold} required)"
        )
        return 0
    else:
        print(
            f"❌ FAIL — LLM routes non-comprehensive only "
            f"{llm_non_comprehensive_count}/{total}, expected ≥{threshold}"
        )
        if llm_failures > 0:
            print(
                f"   (Note: {llm_failures} llm_failures — check GEMINI_API_KEY / network)"
            )
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
