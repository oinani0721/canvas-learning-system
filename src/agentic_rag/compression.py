"""
Story 2.10: Context Compression Module

Implements sentence-level extractive compression:
- Query-relevance scoring per sentence
- Atomic block protection (code, formulas, tables)
- Token budget enforcement (default 3000 tokens)
- Staleness check via content_hash comparison

Reference: Sentence-level extraction preserves factual accuracy
(no LLM summarization = no hallucination risk).
"""

import logging
import re
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Atomic block patterns — not to be split
_ATOMIC_PATTERN = re.compile(
    r"(```[\s\S]*?```)"  # fenced code blocks
    r"|(\$\$[\s\S]*?\$\$)"  # block math formulas
    r"|((?:^[ \t]*\|.+\|[ \t]*$\n?){2,})",  # tables
    re.MULTILINE,
)

# Sentence boundaries
_SENTENCE_PATTERN = re.compile(
    r"(?<=[。！？\.\!\?])\s*"
    r"|\n+"
)


def _count_tokens_approx(text: str) -> int:
    """
    Approximate token count: 1 token ~ 4 chars (EN) / 1.5 chars (CN).
    Uses tiktoken if available for accuracy.
    """
    try:
        import tiktoken

        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except ImportError:
        # Heuristic fallback
        cn_chars = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
        en_chars = len(text) - cn_chars
        return int(cn_chars / 1.5 + en_chars / 4)


def _split_into_units(text: str) -> List[dict]:
    """
    Split text into scoring units, protecting atomic blocks.

    Returns list of {"text": str, "is_atomic": bool, "tokens": int}.
    """
    units: List[dict] = []
    last_end = 0

    for m in _ATOMIC_PATTERN.finditer(text):
        # Non-atomic text before this block
        before = text[last_end : m.start()]
        if before.strip():
            # Split into sentences
            sentences = _SENTENCE_PATTERN.split(before)
            for s in sentences:
                s = s.strip()
                if s:
                    units.append(
                        {
                            "text": s,
                            "is_atomic": False,
                            "tokens": _count_tokens_approx(s),
                        }
                    )
        # Atomic block
        block_text = m.group(0).strip()
        if block_text:
            units.append(
                {
                    "text": block_text,
                    "is_atomic": True,
                    "tokens": _count_tokens_approx(block_text),
                }
            )
        last_end = m.end()

    # Remaining text
    remaining = text[last_end:]
    if remaining.strip():
        sentences = _SENTENCE_PATTERN.split(remaining)
        for s in sentences:
            s = s.strip()
            if s:
                units.append(
                    {
                        "text": s,
                        "is_atomic": False,
                        "tokens": _count_tokens_approx(s),
                    }
                )

    return units


def _tokenize_text(text: str) -> set:
    """
    Tokenize text using jieba for Chinese and regex for non-Chinese.

    jieba.cut handles Chinese word segmentation properly (e.g. "贝叶斯定理"
    -> ["贝叶斯", "定理"]), whereas \\w+ treats each Chinese character as a
    separate "word" and misses multi-character term matches.

    Falls back to regex \\w+ if jieba is not available.
    """
    try:
        import jieba

        # jieba.cut handles mixed Chinese/English text
        return {
            w.strip().lower()
            for w in jieba.cut(text)
            if w.strip() and len(w.strip()) > 0
        }
    except ImportError:
        return set(re.findall(r"\w+", text.lower()))


def _score_relevance(unit_text: str, query: str) -> float:
    """
    Score sentence relevance to query using keyword overlap (TF-IDF-like).
    Higher score = more relevant.

    Uses jieba for Chinese tokenization to correctly segment multi-character
    terms (e.g. "贝叶斯定理" -> ["贝叶斯", "定理"]) instead of treating each
    character as a separate token.
    """
    query_lower = query.lower()
    unit_lower = unit_text.lower()

    # Extract query terms using jieba-aware tokenization
    query_terms = _tokenize_text(query_lower)
    if not query_terms:
        return 0.0

    # Count matching terms
    unit_terms = _tokenize_text(unit_lower)
    overlap = query_terms & unit_terms

    # Score: proportion of query terms found + bonus for longer matches
    base_score = len(overlap) / len(query_terms) if query_terms else 0.0

    # Substring match bonus (for Chinese phrases)
    substring_bonus = 0.0
    for qt in query_terms:
        if len(qt) >= 2 and qt in unit_lower:
            substring_bonus += 0.1

    return min(base_score + substring_bonus, 1.0)


def compress_context(
    query: str,
    documents: List[Dict[str, Any]],
    max_tokens: int = 3000,
) -> str:
    """
    Story 2.10 AC-1: Compress retrieved context to max_tokens.

    Algorithm:
    1. Split all documents into sentence-level units (protecting atomic blocks)
    2. Score each unit for query relevance
    3. Select highest-scoring units until token budget is reached
    4. Reassemble in original document order

    Args:
        query: User query for relevance scoring.
        documents: List of SearchResult dicts with "content" key.
        max_tokens: Target token budget.

    Returns:
        Compressed context string.
    """
    start = time.perf_counter()

    # Collect all units with source tracking
    all_units: List[dict] = []
    for doc_idx, doc in enumerate(documents):
        content = doc.get("content", "")
        if not content:
            continue
        units = _split_into_units(content)
        for unit_idx, unit in enumerate(units):
            unit["doc_idx"] = doc_idx
            unit["unit_idx"] = unit_idx
            # Staleness penalty
            is_stale = doc.get("metadata", {}).get("stale", False) or doc.get(
                "stale", False
            )
            relevance = _score_relevance(unit["text"], query)
            if is_stale:
                relevance *= 0.5
            # Atomic blocks get a small bonus to preserve them
            if unit["is_atomic"]:
                relevance = max(relevance, 0.3)
            unit["relevance"] = relevance
            all_units.append(unit)

    if not all_units:
        return ""

    # Calculate input tokens
    input_tokens = sum(u["tokens"] for u in all_units)

    # Sort by relevance (descending) — keep atomic blocks prioritized
    sorted_units = sorted(all_units, key=lambda u: u["relevance"], reverse=True)

    # Select units until budget
    selected_indices: set = set()
    current_tokens = 0
    protected_blocks = 0

    for unit in sorted_units:
        unit_key = (unit["doc_idx"], unit["unit_idx"])
        if current_tokens + unit["tokens"] > max_tokens:
            continue
        selected_indices.add(unit_key)
        current_tokens += unit["tokens"]
        if unit["is_atomic"]:
            protected_blocks += 1

    # Reassemble in original order
    selected_units = [
        u for u in all_units if (u["doc_idx"], u["unit_idx"]) in selected_indices
    ]
    # Already in original order from all_units iteration

    compressed = "\n".join(u["text"] for u in selected_units)

    duration_ms = (time.perf_counter() - start) * 1000
    output_tokens = _count_tokens_approx(compressed)

    ratio = output_tokens / input_tokens if input_tokens > 0 else 1.0
    logger.info(
        f"[COMPRESS] {input_tokens} tokens -> {output_tokens} tokens "
        f"({ratio:.0%} compression), {protected_blocks} blocks protected, "
        f"{duration_ms:.0f}ms"
    )

    return compressed


def staleness_check(
    results: List[Dict[str, Any]],
    fingerprint_lookup: Optional[Dict[str, str]] = None,
) -> List[Dict[str, Any]]:
    """
    Story 2.10 AC-4: Check staleness of search results via content_hash comparison.

    Marks stale results with metadata["stale"] = True.
    Non-blocking: errors are logged and skipped.

    Args:
        results: Search results with metadata containing file_path.
        fingerprint_lookup: Dict of file_path -> current content_hash.
            If None, staleness check is skipped.

    Returns:
        Results with stale marking applied.
    """
    if not fingerprint_lookup:
        return results

    stale_count = 0
    checked = []
    for r in results:
        r_copy = dict(r)
        metadata = dict(r_copy.get("metadata", {}))
        r_copy["metadata"] = metadata

        try:
            file_path = metadata.get("file_path", "") or metadata.get("canvas_file", "")
            if not file_path:
                checked.append(r_copy)
                continue

            # Try to get metadata_json for stored hash
            metadata_json_str = metadata.get("metadata_json", "")
            stored_hash = ""
            if metadata_json_str and isinstance(metadata_json_str, str):
                import json

                try:
                    mj = json.loads(metadata_json_str)
                    stored_hash = mj.get("content_hash", "")
                except Exception:
                    pass

            current_hash = fingerprint_lookup.get(file_path, "")

            if stored_hash and current_hash and stored_hash != current_hash:
                metadata["stale"] = True
                stale_count += 1
            else:
                metadata["stale"] = False

        except Exception:
            metadata["stale"] = False

        checked.append(r_copy)

    if stale_count > 0:
        logger.info(
            f"[STALENESS] Detected {stale_count} stale results out of {len(results)}"
        )

    return checked
