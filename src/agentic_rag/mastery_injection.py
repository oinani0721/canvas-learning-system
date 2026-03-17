"""
Story 2.10: Mastery Injection + Learning Memory + Multi-Query Rewrite

Implements:
- Mastery level prefix injection (Lost in Middle effect — prompt front position)
- Graphiti learning memory retrieval (Tips, errors, Q&A)
- Multi-Query + Decomposition query rewriting

Reference:
- Lost in Middle (Anthropic + Google papers): LLMs attend more to prompt start/end
- Multi-Query Retrieval: multiple query perspectives improve recall
"""

import asyncio
import logging
import re
from typing import Any, List, Optional

logger = logging.getLogger(__name__)


# =========================================================================
# Mastery Injection (AC-2)
# =========================================================================

# Mastery level descriptions (user-facing, non-technical)
_MASTERY_LEVELS = {
    "mastered": ("掌握", "该知识点已掌握，可直接给出进阶内容或拓展应用"),
    "learning": ("学习中", "对该知识点有一定了解，请给出清晰解释并适当拓展"),
    "weak": ("薄弱", "该知识点掌握薄弱，请从基础概念开始解释，多举例子"),
    "review": ("待复习", "该知识点记忆可能衰退，请简要回顾要点并加深理解"),
}


def build_mastery_prefix(
    p_mastery: Optional[float] = None,
    memory_retention: Optional[float] = None,
    has_exam_records: bool = False,
    needs_review: bool = False,
) -> str:
    """
    Story 2.10 AC-2: Build mastery-level prefix for prompt injection.

    Placed at the very beginning of the system prompt to leverage
    the "Lost in Middle" effect (LLMs pay more attention to prompt start).

    Args:
        p_mastery: BKT p_mastery value (0.0 - 1.0), None if no data.
        memory_retention: FSRS memory retention R (0.0 - 1.0).
        has_exam_records: Whether there are exam/quiz records.
        needs_review: Whether FSRS indicates review needed.

    Returns:
        Mastery prefix string, or empty string if no data.
    """
    if p_mastery is None:
        return ""

    # Determine mastery level
    if needs_review:
        level_key = "review"
    elif p_mastery >= 0.8 and (memory_retention is None or memory_retention >= 0.8):
        level_key = "mastered"
    elif p_mastery >= 0.5:
        level_key = "learning"
    elif has_exam_records:
        level_key = "weak"
    else:
        level_key = "learning"

    label, description = _MASTERY_LEVELS[level_key]
    return f"[学习者水平] 该知识点掌握度: {label}（{description}）。请据此调整解释深度和详细程度。\n"


# =========================================================================
# Graphiti Learning Memory (AC-3)
# =========================================================================


async def retrieve_learning_memories(
    node_id: str,
    max_tokens: int = 1000,
    graphiti_client: Optional[Any] = None,
) -> str:
    """
    Story 2.10 AC-3: Retrieve learning memories from Graphiti.

    Queries for Tips, error records, and key Q&A related to the node.
    Total output limited to max_tokens.

    Args:
        node_id: Canvas node ID.
        max_tokens: Max token budget for memories.
        graphiti_client: Graphiti client instance (optional).

    Returns:
        Formatted learning memory string, or empty string if unavailable.
    """
    if not graphiti_client:
        return ""

    try:
        # Search for memories related to this node
        search_query = f"learning node:{node_id}"
        memories = await asyncio.wait_for(
            graphiti_client.search(search_query, num_results=10),
            timeout=3.0,
        )

        if not memories:
            return ""

        tips_parts: List[str] = []
        error_parts: List[str] = []
        qa_parts: List[str] = []

        for mem in memories:
            content = ""
            if isinstance(mem, dict):
                content = mem.get("content", "") or mem.get("fact", "")
            elif hasattr(mem, "content"):
                content = mem.content or ""
            elif hasattr(mem, "fact"):
                content = mem.fact or ""

            if not content:
                continue

            content_lower = content.lower()
            if "tip" in content_lower or "提示" in content_lower:
                tips_parts.append(content[:200])
            elif "错误" in content_lower or "error" in content_lower or "mistake" in content_lower:
                error_parts.append(content[:200])
            else:
                qa_parts.append(content[:200])

        # Build formatted output
        sections: List[str] = []
        if tips_parts:
            tips_text = "\n".join(f"  {i + 1}. {t}" for i, t in enumerate(tips_parts[:3]))
            sections.append(f"[历史 Tips]\n{tips_text}")
        if error_parts:
            errors_text = "\n".join(f"  - {e}" for e in error_parts[:3])
            sections.append(f"[历史错误]\n{errors_text}")
        if qa_parts:
            qa_text = "\n".join(f"  - {q}" for q in qa_parts[:3])
            sections.append(f"[相关问答]\n{qa_text}")

        if not sections:
            return ""

        result = "\n".join(sections)

        # Token truncation
        from agentic_rag.compression import _count_tokens_approx

        while _count_tokens_approx(result) > max_tokens and sections:
            sections.pop()
            result = "\n".join(sections)

        return result

    except asyncio.TimeoutError:
        logger.warning("[MEMORY] Graphiti learning memory retrieval timed out (3s)")
        return ""
    except Exception as e:
        logger.warning(f"[MEMORY] Graphiti learning memory retrieval failed: {e}")
        return ""


# =========================================================================
# Multi-Query + Decomposition Rewrite (AC-5)
# =========================================================================


def _classify_query_complexity(query: str) -> str:
    """
    Classify query complexity for rewrite strategy selection.

    Returns: "simple", "medium", or "complex".
    """
    # Simple: short, single concept
    if len(query) < 20 and not any(w in query for w in ["和", "以及", "同时", "如何", "为什么", "and", "how"]):
        return "simple"

    # Complex: contains conjunctions or multi-part structure
    complex_markers = [
        "和",
        "以及",
        "同时",
        "另外",
        "还有",
        "如何.*同时",
        "比较.*区别",
        "and",
        "also",
        "compare",
        "difference",
    ]
    for marker in complex_markers:
        if re.search(marker, query, re.IGNORECASE):
            return "complex"

    return "medium"


async def multi_query_rewrite(
    query: str,
    model: str = "gemini/gemini-2.0-flash",
    enabled: bool = True,
) -> List[str]:
    """
    Story 2.10 AC-5: Multi-Query + Decomposition rewrite.

    Strategy:
    - Simple query (< 20 chars, no conjunctions): no rewrite
    - Medium: Multi-Query (2-3 rephrased queries)
    - Complex (conjunctions, multi-part): Decomposition (sub-questions)

    3-second timeout, fallback to original query.

    Args:
        query: Original user query.
        model: LLM model for rewriting.
        enabled: Whether rewriting is enabled.

    Returns:
        List of queries (always includes original).
    """
    if not enabled:
        return [query]

    complexity = _classify_query_complexity(query)
    if complexity == "simple":
        return [query]

    try:
        import litellm

        litellm.set_verbose = False
    except ImportError:
        logger.warning("[MULTI-QUERY] litellm not installed, skipping rewrite")
        return [query]

    if complexity == "medium":
        prompt = f"请从不同角度改写以下查询，生成2-3个等价查询。每行一个查询，不要编号，不要解释。\n原始查询：{query}"
    else:
        prompt = f"请将以下复杂查询拆分为2-3个独立的子问题。每行一个子问题，不要编号，不要解释。\n原始查询：{query}"

    try:
        response = await asyncio.wait_for(
            litellm.acompletion(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.5,
            ),
            timeout=3.0,
        )

        raw = response.choices[0].message.content.strip()
        lines = [line.strip() for line in raw.split("\n") if line.strip()]

        # Always include original query first
        queries = [query]
        for line in lines:
            # Remove numbering if present
            cleaned = re.sub(r"^\d+[\.\)]\s*", "", line).strip()
            if cleaned and cleaned != query and len(cleaned) > 3:
                queries.append(cleaned)

        # Cap at 4 total queries
        queries = queries[:4]

        logger.info(
            f"[MULTI-QUERY] complexity={complexity}, original='{query[:40]}', generated {len(queries) - 1} variants"
        )
        return queries

    except asyncio.TimeoutError:
        logger.warning("[MULTI-QUERY] LLM rewrite timed out (3s), using original query")
        return [query]
    except Exception as e:
        logger.warning(f"[MULTI-QUERY] Rewrite failed: {e}, using original query")
        return [query]
