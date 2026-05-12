"""Story 2.2+2.9 (merged) Task 3.3 — query-aware rerank helpers.

Phase T3c 范围（本提交）:
- BM25 Okapi lexical query_overlap (jieba 中英分词, 自实现)
- Min-max normalize 到 [0,1] 供下游 final_score 加权

设计决策（why 自实现 BM25 而非 rank_bm25 包）:
- 候选集 N ≤ 30 (Story 2.2 elbow_cut hard_cap=15)，纯 Python BM25 < 1ms
- 自实现 ~30 行清晰可读 (Okapi 标准公式)，避免引入未声明 third-party
- jieba tokenizer 与 LanceDB hybrid 搜索召回阶段保持一致 (防 query 在 rerank
  阶段丢 token 导致假阴性)

公式 (Robertson & Zaragoza 2009 "The Probabilistic Relevance Framework"):
  score(q, d) = Σ IDF(qi) × ( f(qi,d) × (k1+1) ) / ( f(qi,d) + k1 × (1 - b + b × |d|/avgdl) )
  IDF(qi) = log( (N - n(qi) + 0.5) / (n(qi) + 0.5) + 1 )

Future T3.x (可选): cosine similarity via sentence-transformers bge-m3 cache.
"""

from __future__ import annotations

import math
from collections import Counter
from typing import Sequence

import structlog

logger = structlog.get_logger(__name__)


# Okapi BM25 standard hyperparameters (Robertson 2009 recommended defaults)
BM25_K1 = 1.5
BM25_B = 0.75


def tokenize(text: str) -> list[str]:
    """jieba 混合中英分词 + 小写化 + 过滤纯标点 token.

    与 LanceDB hybrid 搜索分词一致 (Story 2.4 chinese-search-hybrid-retrieval done),
    确保 query 在召回与 rerank 阶段切词结果对齐.
    """
    if not text:
        return []
    try:
        import jieba
    except ImportError:
        # 降级：纯 split (中文场景表现差但保活)
        logger.warning("[Rerank] jieba 不可用,降级到 whitespace split")
        return [t.lower() for t in text.split() if any(c.isalnum() for c in t)]

    tokens: list[str] = []
    for tok in jieba.cut(text):
        tok = tok.strip().lower()
        if tok and any(c.isalnum() for c in tok):
            tokens.append(tok)
    return tokens


def bm25_scores(
    query: str,
    documents: Sequence[str],
    *,
    k1: float = BM25_K1,
    b: float = BM25_B,
) -> list[float]:
    """Okapi BM25 score each document against query.

    Args:
        query: user query string
        documents: candidate document texts (e.g. title + snippet concat)
        k1: term frequency saturation (default 1.5, Robertson recommended)
        b: document length normalization (default 0.75)

    Returns:
        list of float scores, same order as documents.
        Empty query / empty corpus / all-empty docs → list of zeros.
    """
    if not query or not documents:
        return [0.0] * len(documents)

    query_tokens = tokenize(query)
    if not query_tokens:
        return [0.0] * len(documents)

    doc_tokens = [tokenize(d) for d in documents]
    doc_lengths = [len(d) for d in doc_tokens]
    total_length = sum(doc_lengths)
    if total_length == 0:
        return [0.0] * len(documents)

    avgdl = total_length / len(doc_tokens)
    n_docs = len(doc_tokens)

    # IDF for each unique query term (document frequency-based)
    unique_q = set(query_tokens)
    idf: dict[str, float] = {}
    for q in unique_q:
        df = sum(1 for d in doc_tokens if q in d)
        # +1 inside log → BM25+ smoothing, prevents negative IDF for very common terms
        idf[q] = math.log((n_docs - df + 0.5) / (df + 0.5) + 1.0)

    scores: list[float] = []
    for tokens, dl in zip(doc_tokens, doc_lengths):
        if dl == 0:
            scores.append(0.0)
            continue
        tf = Counter(tokens)
        score = 0.0
        norm = 1 - b + b * dl / avgdl
        for q in query_tokens:
            f = tf.get(q, 0)
            if f == 0:
                continue
            score += idf[q] * (f * (k1 + 1)) / (f + k1 * norm)
        scores.append(score)
    return scores


def normalize_to_unit(scores: Sequence[float]) -> list[float]:
    """Min-max normalize raw BM25 scores to [0,1] for downstream weighted combine.

    Edge cases:
    - 空输入: []
    - 全相同 (含全 0): 全 0.0 (无相对区分度)
    - 单元素 / 范围 < 1e-9: 全 0.5 (有信号但不分高低) OR 全 0.0 (无信号)
    """
    if not scores:
        return []
    mn, mx = min(scores), max(scores)
    span = mx - mn
    if span < 1e-9:
        # 全相同: max=0 视为"无信号" → 0; max>0 视为"等同有信号" → 0.5
        return [0.0 if mx < 1e-9 else 0.5] * len(scores)
    return [(s - mn) / span for s in scores]
