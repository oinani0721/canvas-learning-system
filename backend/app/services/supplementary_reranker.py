"""Story 2.2+2.9 (merged) Task 3 — 补充材料精排引擎.

PRD §4.1.1 (line 3707-3877): 邻居 / supplementary 候选 N 条 → final_score 综合排序.

Phase 演进（rerank() 签名保持稳定）:
- T3b (done): TYPE_WEIGHTS + relevance × type_weight 基础排序
- T3c (本提交): query_overlap 加权 (BM25 via rerank_service)
- T3d (待续): hub_penalty 衰减 (wikilink_graph_service.get_degree_stats)
- T3.7+ (待续): chat.py endpoint 把 user_question + mode 传 enrich

当前 final_score 公式:
  final_score = relevance × type_weight + query_overlap × query_overlap_weight

未来 T3d 起:
  final_score = relevance × type_weight + query_overlap × query_overlap_weight - hub_penalty

来源对照（避免膨胀）:
- type weight: PRD §4.1.1 + Story 2.2 AC #3
- hub penalty: Story 2.9 AC #2 (log(degree / median + 1))
- query overlap: Story 2.9 AC #1 (BM25 lexical + 可选 cosine)
"""

from __future__ import annotations

import math
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Type weight table (PRD §4.1.1, frozen 2026-05-11)
# ═══════════════════════════════════════════════════════════════════════════════

# P0-A 过渡映射 (2026-05-12 hotfix): indexer 当前实际写入的 source_type
# (lancedb_client.py:1444/1644) 只有 {note, video_transcript, image_ocr}, PRD §4.1.1
# 6 档分类 (lecture_notes / discussion / ...) 是 indexer 升级目标。如果只保留 PRD
# 6 keys, 所有真实数据 fallback 到 DEFAULT_TYPE_WEIGHT=0.5 → P0-B filter 0.42 几乎
# 全删材料。解法: 表里同时包含 PRD 6 档 (forward compat, indexer 升级后立刻可用)
# 加 indexer 当前真实 3 类 (过渡兜底)。indexer 升级到 PRD 6 档后, 过渡 3 类自然
# 失去命中, 行为优雅退化。
TYPE_WEIGHTS: dict[str, float] = {
    # PRD §4.1.1 frozen 2026-05-11 (forward compat for indexer 升级)
    "lecture_notes": 1.0,
    "discussion": 0.9,
    "exam_review": 0.85,
    "wiki_concepts": 0.8,
    "chat_session": 0.7,
    "raw_notes": 0.6,
    # P0-A 过渡 (indexer 升级到 PRD 6 档前的实际命中映射, 2026-05-12 hotfix):
    "video_transcript": 0.9,  # 视频 transcript → 近 discussion 价值
    "note": 0.7,  # 普通 vault 笔记 → 近 chat_session 中档
    "image_ocr": 0.6,  # OCR 出来的图片文字 → 同 raw_notes 低档 (准确度有限)
}

# Unknown / None / empty source_type fallback. Below all canonical (min 0.6) so
# unknown data surfaces visibly in trace.included.type_weight rather than
# silently being treated as a canonical category.
DEFAULT_TYPE_WEIGHT: float = 0.5


def get_type_weight(source_type: str | None) -> float:
    """Map source_type to type weight (PRD §4.1.1).

    None / empty / unknown values fall back to DEFAULT_TYPE_WEIGHT.
    """
    if not source_type:
        return DEFAULT_TYPE_WEIGHT
    return TYPE_WEIGHTS.get(source_type, DEFAULT_TYPE_WEIGHT)


# ═══════════════════════════════════════════════════════════════════════════════
# Rerank engine (Phase T3b — type weight only; future phases extend final_score)
# ═══════════════════════════════════════════════════════════════════════════════


# Story 2.2 AC #4: "user_question 无时走 Phase 1 默认排序"
# → query=None / query="" / mode!="solve" 时 query_overlap=0, 仅用 type_weight
DEFAULT_QUERY_OVERLAP_WEIGHT: float = 0.3


def compute_hub_penalty(degree: int, median_degree: float) -> float:
    """Story 2.9 AC #2: hub_penalty = log(degree / median + 1).

    Edge cases:
    - degree <= 0 → 0 (孤立节点不该被惩罚)
    - median_degree <= 0 → 0 (空图或单节点图,无 hub 概念)

    Formula uses natural log; degree=median yields ln(2)≈0.69, degree=2×median
    yields ln(3)≈1.10. Caller decide whether to apply scale factor.
    """
    if degree <= 0 or median_degree <= 0:
        return 0.0
    return math.log(degree / median_degree + 1.0)


# Story 2.2 AC #4 T3.9 filter: 最终 rerank_score 低于
# (0.70 × min_canonical_type_weight) 的材料不显示。
DEFAULT_FILTER_QUALITY_RATIO: float = 0.70


def get_filter_threshold(quality_ratio: float = DEFAULT_FILTER_QUALITY_RATIO) -> float:
    """T3.9 filter threshold = quality_ratio × min(TYPE_WEIGHTS.values()).

    DEFAULT_TYPE_WEIGHT 不参与计算（DEFAULT 表示"未知"应该被压低，
    threshold 用 canonical 最低 raw_notes=0.6 作为可接受质量下限）。
    """
    return quality_ratio * min(TYPE_WEIGHTS.values())


def rerank(
    materials: list[dict[str, Any]],
    *,
    query: str | None = None,
    query_overlap_weight: float = DEFAULT_QUERY_OVERLAP_WEIGHT,
    median_degree: float = 0.0,
    type_weights: dict[str, float] | None = None,
    min_score_threshold: float | None = None,
    top_k: int | None = None,
    min_keep: int = 3,
) -> list[dict[str, Any]]:
    """Phase T3b+T3c+T3d+T3.9+T3.10: full final_score formula (Story 2.2 AC #4 / 2.9 AC #1+#2).

    final_score = relevance × type_weight + query_overlap × query_overlap_weight - hub_penalty

    Each material is augmented in-place with four fields (consumed by TraceItem):
    - `rerank_score`: float, the final ordering score
    - `type_weight`: float, weight applied based on `source_type`
    - `query_overlap`: float in [0,1], BM25-normalized lexical overlap
    - `hub_penalty`: float >= 0, log(degree/median + 1) when material has `degree` field

    Pipeline order (T3.9 + T3.10 sequence): score → sort → filter → truncate. Sort
    first so threshold cut applies to globally ranked candidates; filter before
    truncate so a high-quality #6 isn't lost behind a marginal-quality #5.

    Tie-break: 完全相同 rerank_score 时按 `title` 字典序升序（确定性输出，
    Story 2.2 AC #4 "score 相同 fallback 字典序"）。

    Args:
        materials: candidate dicts，至少含 `score` (float, [0,1])、
            `source_type` (str | None)；可选 `degree` (int, 用于 hub_penalty)
        query: user question string. None / 空 → query_overlap=0
        query_overlap_weight: query_overlap 加权系数（默认 0.3，PRD §4.1.1）
        median_degree: degree 基线（来自 wikilink_graph_service.get_degree_stats()
            的 `median`）。0 → hub_penalty 全部为 0（小 vault 场景）
        type_weights: 覆盖默认 TYPE_WEIGHTS（仅测试 / 实验用）
        min_score_threshold: T3.9 filter — 过滤 rerank_score < 此值的材料
            （None = 不过滤；典型值 get_filter_threshold() = 0.42）
        top_k: T3.10 — 截取前 N 条（None = 不截断；典型 Top 5）
        min_keep: P0-B floor — filter 后剩 < min_keep 条 OR 删掉 > 80% candidates
            时, 兜底放弃 filter (改返回未 filter 的 sorted list, 仍 top_k 截断),
            并在第 1 条材料注入 `filter_floor_triggered=True` 供 logger 观测.
            min_keep=0 关闭兜底.

    Returns:
        重排后的 list（已 in-place sort + 字段注入；过滤+截断的可能是新 list）
    """
    if not materials:
        return []

    weights = type_weights if type_weights is not None else TYPE_WEIGHTS

    query_overlaps = _compute_query_overlap(materials, query)

    for m, query_overlap in zip(materials, query_overlaps):
        relevance = float(m.get("score", 0.0))
        source_type = m.get("source_type") or ""
        type_weight = weights.get(source_type, DEFAULT_TYPE_WEIGHT)
        degree = int(m.get("degree", 0))
        hub_pen = compute_hub_penalty(degree, median_degree)

        m["type_weight"] = type_weight
        m["query_overlap"] = query_overlap
        m["hub_penalty"] = hub_pen
        m["rerank_score"] = (
            relevance * type_weight + query_overlap * query_overlap_weight - hub_pen
        )

    materials.sort(
        key=lambda m: (-m["rerank_score"], str(m.get("title", ""))),
    )

    # P0-B (2026-05-12 hotfix): 过滤 floor 兜底.
    # 当 indexer 未升级到 PRD 6 档时, real-world 数据 source_type="note" 命中过渡
    # 表 0.7, 典型 relevance ~0.5 → final ~0.35 < filter_threshold 0.42 → 全删.
    # 用户原话: "不硬编码 5 条, 把有用的都提供给我"
    # → filter 后剩 < min_keep 或删 > 80% 候选, 视为 threshold 误杀, 自动降级为
    #   不过滤但仍 top_k 截断, 第 1 条注入 filter_floor_triggered=True 供 logger
    #   观察以便调阈值. floor=0 关闭兜底 (现有测试 + 显式 opt-out).
    #
    # P0-3b (2026-05-12 hotfix, ChatGPT v2 fail-closed real): 即使 floor_triggered,
    # 也必须过滤 taint ∈ {review, quarantine} 的材料. floor 初衷是 "保护边缘
    # candidate 不被全删", 但 review/quarantine 是安全审查决定的污染标记, 不应
    # 因 floor 而 backdoor 入选 (兜底也不能让可疑材料绕过审查).
    if min_score_threshold is not None:
        kept = [m for m in materials if m["rerank_score"] >= min_score_threshold]
        n_pre = len(materials)
        n_post = len(kept)
        floor_triggered = False
        if min_keep > 0 and n_pre > 0:
            kill_ratio = 1.0 - (n_post / n_pre)
            if n_post < min_keep or kill_ratio > 0.80:
                floor_triggered = True
        if floor_triggered:
            logger.warning(
                "[Rerank] filter_floor_triggered",
                pre=n_pre,
                post=n_post,
                threshold=round(min_score_threshold, 3),
                min_keep=min_keep,
            )
            # P0-3b: floor 仍 fail-closed 过滤 review/quarantine 材料
            materials = [
                m for m in materials if m.get("taint") not in {"review", "quarantine"}
            ]
            # 标记兜底, 仍走 top_k
            if materials:
                materials[0]["filter_floor_triggered"] = True
        else:
            materials = kept

    if top_k is not None and top_k >= 0:
        return materials[:top_k]
    return materials


def _compute_query_overlap(
    materials: list[dict[str, Any]],
    query: str | None,
) -> list[float]:
    """BM25-based query overlap, normalized [0,1] for combine.

    Combines title + snippet as the document text (title carries highest signal
    weight via lexical overlap; snippet adds body context).
    """
    if not query or not query.strip():
        return [0.0] * len(materials)

    try:
        from app.services.rerank_service import bm25_scores, normalize_to_unit
    except ImportError:
        logger.warning("[Rerank] rerank_service unavailable, skipping query_overlap")
        return [0.0] * len(materials)

    docs = [
        " ".join(
            filter(
                None,
                [str(m.get("title", "")), str(m.get("snippet", ""))],
            )
        )
        for m in materials
    ]
    raw = bm25_scores(query, docs)
    return normalize_to_unit(raw)
