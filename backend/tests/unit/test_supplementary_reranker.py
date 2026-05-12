"""Story 2.2+2.9 (merged) Task 3 — supplementary_reranker T3b unit tests.

PRD §4.1.1 type weight 表（lecture_notes 1.0 > discussion 0.9 > exam_review 0.85
> wiki_concepts 0.8 > chat_session 0.7 > raw_notes 0.6）+ unknown fallback。

本文件先 ship T3b (type weight + rerank 入口)；T3c/T3d 后续扩展 query_overlap +
hub_penalty 字段时本文件追加 case。
"""

from __future__ import annotations

import pytest


class TestTypeWeights:
    """T3.2: TYPE_WEIGHTS 映射 (PRD §4.1.1)."""

    def test_six_canonical_types_present_and_descending(self):
        from app.services.supplementary_reranker import TYPE_WEIGHTS

        expected = [
            ("lecture_notes", 1.0),
            ("discussion", 0.9),
            ("exam_review", 0.85),
            ("wiki_concepts", 0.8),
            ("chat_session", 0.7),
            ("raw_notes", 0.6),
        ]
        for source_type, weight in expected:
            assert TYPE_WEIGHTS[source_type] == pytest.approx(weight), (
                f"type weight mismatch for {source_type}"
            )
        # Strictly descending
        values = [TYPE_WEIGHTS[t] for t, _ in expected]
        assert values == sorted(values, reverse=True)

    def test_default_below_all_canonical(self):
        """未知 source_type fallback 必须低于最低 canonical (raw_notes=0.6)
        — 让未知数据在 trace 中可视化暴露而非冒充某 canonical 类型."""
        from app.services.supplementary_reranker import (
            DEFAULT_TYPE_WEIGHT,
            TYPE_WEIGHTS,
        )

        min_canonical = min(TYPE_WEIGHTS.values())
        assert DEFAULT_TYPE_WEIGHT < min_canonical


class TestGetTypeWeight:
    def test_known_type_returns_table_value(self):
        from app.services.supplementary_reranker import get_type_weight

        assert get_type_weight("lecture_notes") == 1.0
        assert get_type_weight("raw_notes") == 0.6

    def test_none_returns_default(self):
        from app.services.supplementary_reranker import (
            DEFAULT_TYPE_WEIGHT,
            get_type_weight,
        )

        assert get_type_weight(None) == DEFAULT_TYPE_WEIGHT

    def test_empty_string_returns_default(self):
        from app.services.supplementary_reranker import (
            DEFAULT_TYPE_WEIGHT,
            get_type_weight,
        )

        assert get_type_weight("") == DEFAULT_TYPE_WEIGHT

    def test_unknown_type_returns_default(self):
        from app.services.supplementary_reranker import (
            DEFAULT_TYPE_WEIGHT,
            get_type_weight,
        )

        # P0-A (2026-05-12): "note" 现在是 indexer 过渡映射的 canonical 0.7
        # (lancedb_client.py 实际写入 source_type ∈ {note,video_transcript,image_ocr}).
        # 真正未识别的 source_type 才落 DEFAULT.
        assert get_type_weight("totally_unknown_xyz") == DEFAULT_TYPE_WEIGHT
        assert get_type_weight("foobar") == DEFAULT_TYPE_WEIGHT


class TestRerank:
    """T3.1 + T3.2: rerank() relevance × type_weight 排序 + tie-break."""

    def test_empty_input_returns_empty(self):
        from app.services.supplementary_reranker import rerank

        assert rerank([]) == []

    def test_higher_type_weight_wins_when_relevance_tied(self):
        """relevance 同 0.5 时 lecture_notes (1.0) 应优于 raw_notes (0.6)."""
        from app.services.supplementary_reranker import rerank

        a = {"score": 0.5, "source_type": "lecture_notes", "title": "A"}
        b = {"score": 0.5, "source_type": "raw_notes", "title": "B"}
        result = rerank([b, a])
        assert [m["title"] for m in result] == ["A", "B"]

    def test_relevance_can_overcome_type_weight(self):
        """relevance 0.9 × raw_notes 0.6 = 0.54 >> 0.5 × lecture_notes 1.0 = 0.5."""
        from app.services.supplementary_reranker import rerank

        a = {"score": 0.9, "source_type": "raw_notes", "title": "A"}
        b = {"score": 0.5, "source_type": "lecture_notes", "title": "B"}
        result = rerank([b, a])
        assert result[0]["title"] == "A"

    def test_full_tie_fallback_to_title_lexicographic(self):
        """rerank_score 完全相同时按 title 字典序升序（确定性输出）."""
        from app.services.supplementary_reranker import rerank

        a = {"score": 0.5, "source_type": "lecture_notes", "title": "B"}
        b = {"score": 0.5, "source_type": "lecture_notes", "title": "A"}
        result = rerank([a, b])
        assert [m["title"] for m in result] == ["A", "B"]

    def test_each_material_gets_rerank_score_and_type_weight_field(self):
        """rerank 输出每条材料必须含 rerank_score + type_weight (供 TraceItem)."""
        from app.services.supplementary_reranker import rerank

        m = {"score": 0.8, "source_type": "lecture_notes", "title": "X"}
        result = rerank([m])
        assert result[0]["rerank_score"] == pytest.approx(0.8 * 1.0)
        assert result[0]["type_weight"] == pytest.approx(1.0)

    def test_unknown_source_type_uses_default_weight(self):
        """LanceDB 老 schema 默认 source_type="note" 应落 DEFAULT."""
        from app.services.supplementary_reranker import (
            DEFAULT_TYPE_WEIGHT,
            rerank,
        )

        m = {"score": 0.9, "source_type": "unknown_xyz", "title": "X"}
        result = rerank([m])
        assert result[0]["type_weight"] == DEFAULT_TYPE_WEIGHT
        assert result[0]["rerank_score"] == pytest.approx(0.9 * DEFAULT_TYPE_WEIGHT)

    def test_missing_source_type_field_uses_default(self):
        """material dict 完全无 source_type key 也应安全落 DEFAULT."""
        from app.services.supplementary_reranker import (
            DEFAULT_TYPE_WEIGHT,
            rerank,
        )

        m = {"score": 0.7, "title": "noSrcType"}
        result = rerank([m])
        assert result[0]["type_weight"] == DEFAULT_TYPE_WEIGHT
        assert result[0]["rerank_score"] == pytest.approx(0.7 * DEFAULT_TYPE_WEIGHT)

    def test_missing_score_treated_as_zero(self):
        from app.services.supplementary_reranker import rerank

        m = {"source_type": "lecture_notes", "title": "noScore"}
        result = rerank([m])
        assert result[0]["rerank_score"] == 0.0

    def test_top_k_truncates(self):
        from app.services.supplementary_reranker import rerank

        materials = [
            {"score": 0.9, "source_type": "lecture_notes", "title": f"T{i:02d}"}
            for i in range(10)
        ]
        result = rerank(materials, top_k=5)
        assert len(result) == 5
        # Top-5 应是字典序最前 5（T00..T04），所有 rerank_score 相同
        assert [m["title"] for m in result] == [f"T{i:02d}" for i in range(5)]

    def test_top_k_none_returns_all(self):
        from app.services.supplementary_reranker import rerank

        materials = [
            {"score": 0.9, "source_type": "lecture_notes", "title": f"T{i}"}
            for i in range(7)
        ]
        result = rerank(materials, top_k=None)
        assert len(result) == 7

    def test_custom_type_weights_override(self):
        """type_weights 注入覆盖默认表（测试 hook + 后续 T3c/T3d 实验用）."""
        from app.services.supplementary_reranker import rerank

        # 自定义表把 raw_notes 抬到 2.0
        custom = {"raw_notes": 2.0, "lecture_notes": 0.1}
        a = {"score": 0.5, "source_type": "raw_notes", "title": "A"}
        b = {"score": 0.5, "source_type": "lecture_notes", "title": "B"}
        result = rerank([a, b], type_weights=custom)
        # A 现在 0.5×2.0=1.0, B 现在 0.5×0.1=0.05
        assert result[0]["title"] == "A"

    def test_mixed_canonical_and_unknown_ordering(self):
        """常见混合：discussion (0.9) + chat_session (0.7) + unknown (DEFAULT)."""
        from app.services.supplementary_reranker import rerank

        materials = [
            {"score": 0.6, "source_type": "chat_session", "title": "chat"},
            {"score": 0.6, "source_type": "discussion", "title": "disc"},
            {"score": 0.6, "source_type": "weird", "title": "unk"},
        ]
        result = rerank(materials)
        # rerank_score: disc 0.54 > chat 0.42 > unk 0.30 (0.6 × 0.5)
        assert [m["title"] for m in result] == ["disc", "chat", "unk"]


class TestRerankQueryOverlap:
    """T3.3 + T3.6: query-aware BM25 query_overlap 影响 final_score."""

    def test_query_overlap_field_zero_when_no_query(self):
        """Story 2.2 AC #4: mode="preload" / 空 user_question 走 default 排序."""
        from app.services.supplementary_reranker import rerank

        m = {"score": 0.5, "source_type": "lecture_notes", "title": "X"}
        result = rerank([m])
        assert result[0]["query_overlap"] == 0.0
        # rerank_score 保持 T3b 行为
        assert result[0]["rerank_score"] == pytest.approx(0.5)

    def test_query_overlap_field_zero_when_empty_query(self):
        from app.services.supplementary_reranker import rerank

        m = {"score": 0.5, "source_type": "lecture_notes", "title": "X"}
        result = rerank([m], query="")
        assert result[0]["query_overlap"] == 0.0

    def test_query_match_boosts_score(self):
        """同 type_weight + 同 relevance,query 命中的材料应排前."""
        from app.services.supplementary_reranker import rerank

        materials = [
            {
                "score": 0.5,
                "source_type": "lecture_notes",
                "title": "completely unrelated cooking notes",
                "snippet": "tomato soup recipe step by step",
            },
            {
                "score": 0.5,
                "source_type": "lecture_notes",
                "title": "admissible heuristic search",
                "snippet": "A* with admissible heuristic finds optimal path",
            },
        ]
        result = rerank(materials, query="admissible heuristic")
        # admissible 命中 → 排前
        assert result[0]["title"] == "admissible heuristic search"
        # query_overlap 应该 > 0
        assert result[0]["query_overlap"] > 0.0

    def test_query_overlap_normalized_to_unit_range(self):
        from app.services.supplementary_reranker import rerank

        materials = [
            {
                "score": 0.7,
                "source_type": "discussion",
                "title": "graph search",
                "snippet": "BFS DFS A* dijkstra",
            },
            {
                "score": 0.7,
                "source_type": "discussion",
                "title": "another",
                "snippet": "completely different content",
            },
        ]
        result = rerank(materials, query="graph BFS dijkstra")
        for m in result:
            assert 0.0 <= m["query_overlap"] <= 1.0

    def test_explicit_zero_overlap_weight_disables_query_influence(self):
        """query_overlap_weight=0 等价于 T3b 行为(纯 type_weight 排序)."""
        from app.services.supplementary_reranker import rerank

        a = {
            "score": 0.5,
            "source_type": "lecture_notes",
            "title": "no query match here",
            "snippet": "nothing",
        }
        b = {
            "score": 0.5,
            "source_type": "raw_notes",
            "title": "admissible heuristic match",
            "snippet": "admissible heuristic match",
        }
        # query 强匹配 B,但 weight=0 → 仍是 A (lecture_notes 1.0) 优于 B (raw_notes 0.6)
        result = rerank([a, b], query="admissible heuristic", query_overlap_weight=0.0)
        assert result[0]["title"] == "no query match here"

    def test_chinese_query_match(self):
        """中文 query 应通过 jieba 分词匹配中文 snippet."""
        from app.services.supplementary_reranker import rerank

        materials = [
            {
                "score": 0.6,
                "source_type": "wiki_concepts",
                "title": "启发式搜索",
                "snippet": "启发式函数 admissible 性质 保证最优解",
            },
            {
                "score": 0.6,
                "source_type": "wiki_concepts",
                "title": "动态规划",
                "snippet": "dp 状态转移方程",
            },
        ]
        result = rerank(materials, query="启发式 admissible")
        assert result[0]["title"] == "启发式搜索"
        assert result[0]["query_overlap"] > 0.0

    def test_no_match_query_overlap_zero(self):
        """query 与所有文档无重合 → query_overlap 全 0,等价于 T3b."""
        from app.services.supplementary_reranker import rerank

        materials = [
            {
                "score": 0.5,
                "source_type": "lecture_notes",
                "title": "topic A",
                "snippet": "content A",
            },
            {
                "score": 0.5,
                "source_type": "raw_notes",
                "title": "topic B",
                "snippet": "content B",
            },
        ]
        result = rerank(materials, query="totally unrelated terminology xyzqw")
        # 无匹配 → query_overlap=0, 退化到 T3b: lecture_notes 优先
        assert result[0]["title"] == "topic A"

    def test_query_overlap_combined_with_type_weight(self):
        """final_score = relevance × type_weight + query_overlap × 0.3 综合排序."""
        from app.services.supplementary_reranker import rerank

        # B 有 query 强匹配,但 A 有 type weight 优势
        # relevance 同 0.5
        # A: 0.5 × 1.0 + query_overlap × 0.3 (无匹配 → 0)
        # B: 0.5 × 0.6 + 1.0 × 0.3 = 0.3 + 0.3 = 0.6
        # B 应排前
        materials = [
            {
                "score": 0.5,
                "source_type": "lecture_notes",
                "title": "tangential lecture",
                "snippet": "covers different unrelated topic",
            },
            {
                "score": 0.5,
                "source_type": "raw_notes",
                "title": "raw search algorithm",
                "snippet": "exact admissible heuristic example",
            },
        ]
        result = rerank(materials, query="admissible heuristic")
        assert result[0]["title"] == "raw search algorithm"


class TestHubPenalty:
    """T3.4: hub_penalty = log(degree / median + 1) 防 MOC/Index 类节点垄断."""

    def test_zero_degree_no_penalty(self):
        from app.services.supplementary_reranker import compute_hub_penalty

        assert compute_hub_penalty(0, 5.0) == 0.0

    def test_zero_median_no_penalty(self):
        """空 vault / 单节点 vault → median=0 → 不施加 penalty (没有 hub 概念)."""
        from app.services.supplementary_reranker import compute_hub_penalty

        assert compute_hub_penalty(10, 0.0) == 0.0

    def test_negative_degree_clamped_to_zero(self):
        from app.services.supplementary_reranker import compute_hub_penalty

        assert compute_hub_penalty(-1, 5.0) == 0.0

    def test_degree_equal_median_yields_ln_2(self):
        from app.services.supplementary_reranker import compute_hub_penalty
        import math

        assert compute_hub_penalty(3, 3.0) == pytest.approx(math.log(2))

    def test_higher_degree_higher_penalty(self):
        from app.services.supplementary_reranker import compute_hub_penalty

        p_low = compute_hub_penalty(2, 3.0)
        p_mid = compute_hub_penalty(6, 3.0)
        p_high = compute_hub_penalty(30, 3.0)
        assert p_low < p_mid < p_high

    def test_rerank_hub_penalty_field_present(self):
        from app.services.supplementary_reranker import rerank

        m = {
            "score": 0.5,
            "source_type": "wiki_concepts",
            "title": "X",
            "degree": 5,
        }
        result = rerank([m], median_degree=3.0)
        assert "hub_penalty" in result[0]
        assert result[0]["hub_penalty"] > 0.0

    def test_rerank_default_median_no_penalty(self):
        """median_degree=0 (default) → hub_penalty 全部为 0,保持 T3b/T3c 行为."""
        from app.services.supplementary_reranker import rerank

        m = {
            "score": 0.5,
            "source_type": "wiki_concepts",
            "title": "X",
            "degree": 100,
        }
        result = rerank([m])  # 不传 median_degree
        assert result[0]["hub_penalty"] == 0.0

    def test_hub_penalty_demotes_high_degree_node(self):
        """同 relevance / type_weight: hub 节点 (高 degree) 应被低 degree 节点反超."""
        from app.services.supplementary_reranker import rerank

        # A 是 hub (degree=20), B 是 atomic 节点 (degree=2)
        # median=3 → A 扣 ln(20/3+1)=ln(7.67)≈2.04, B 扣 ln(2/3+1)=ln(1.67)≈0.51
        # 同 relevance 0.6 × type 0.8 = 0.48
        # final A = 0.48 - 2.04 = -1.56 / B = 0.48 - 0.51 = -0.03
        # B 应排前
        materials = [
            {
                "score": 0.6,
                "source_type": "wiki_concepts",
                "title": "MOC-hub",
                "degree": 20,
            },
            {
                "score": 0.6,
                "source_type": "wiki_concepts",
                "title": "atomic-concept",
                "degree": 2,
            },
        ]
        result = rerank(materials, median_degree=3.0)
        assert result[0]["title"] == "atomic-concept"

    def test_no_degree_field_means_no_penalty(self):
        """material 无 degree 字段 → 视为 degree=0 → 不施 penalty (向后兼容)."""
        from app.services.supplementary_reranker import rerank

        m = {"score": 0.5, "source_type": "wiki_concepts", "title": "X"}
        result = rerank([m], median_degree=3.0)
        assert result[0]["hub_penalty"] == 0.0

    def test_all_four_dimensions_combined(self):
        """final_score = relevance × type_weight + query_overlap × 0.3 - hub_penalty."""
        from app.services.supplementary_reranker import rerank

        materials = [
            {
                "score": 0.7,
                "source_type": "lecture_notes",
                "title": "popular but loose match",
                "snippet": "tangential content",
                "degree": 15,  # hub
            },
            {
                "score": 0.7,
                "source_type": "lecture_notes",
                "title": "atomic precise match",
                "snippet": "exact admissible heuristic proof",
                "degree": 2,
            },
        ]
        # query 匹配 B → B 提升; A 是 hub → A 扣分
        result = rerank(
            materials,
            query="admissible heuristic proof",
            median_degree=3.0,
        )
        assert result[0]["title"] == "atomic precise match"
        assert result[0]["hub_penalty"] < result[1]["hub_penalty"]


class TestFilterThreshold:
    """T3.9: filter final_score < 0.70 × min_canonical_type_weight."""

    def test_get_filter_threshold_default(self):
        from app.services.supplementary_reranker import (
            TYPE_WEIGHTS,
            get_filter_threshold,
        )

        min_canonical = min(TYPE_WEIGHTS.values())  # raw_notes 0.6
        assert get_filter_threshold() == pytest.approx(0.7 * min_canonical)

    def test_get_filter_threshold_custom_ratio(self):
        from app.services.supplementary_reranker import get_filter_threshold

        assert get_filter_threshold(0.5) == pytest.approx(0.5 * 0.6)

    def test_rerank_min_score_threshold_filters_below(self):
        from app.services.supplementary_reranker import rerank

        materials = [
            {
                "score": 0.9,
                "source_type": "lecture_notes",
                "title": "high",
            },
            {
                "score": 0.3,
                "source_type": "raw_notes",
                "title": "low",
            },
        ]
        # high: 0.9 × 1.0 = 0.9 (above 0.42)
        # low: 0.3 × 0.6 = 0.18 (below 0.42)
        # P0-B (2026-05-12): 显式 min_keep=0 关闭 floor 兜底, 验证纯 filter 语义.
        result = rerank(materials, min_score_threshold=0.42, min_keep=0)
        assert len(result) == 1
        assert result[0]["title"] == "high"

    def test_rerank_no_threshold_keeps_all(self):
        from app.services.supplementary_reranker import rerank

        materials = [
            {"score": 0.05, "source_type": "raw_notes", "title": "marginal"},
        ]
        result = rerank(materials)
        assert len(result) == 1

    def test_filter_before_truncate_preserves_quality(self):
        """T3.9+T3.10 顺序: 先过滤后截断 — 高质量 #6 不会被低质量 #5 挤掉."""
        from app.services.supplementary_reranker import rerank

        materials = [
            {"score": 0.9, "source_type": "lecture_notes", "title": f"good-{i}"}
            for i in range(5)
        ]
        # 加一个 marginal #6,在 filter 前 top_k=5 会截掉它,但过滤 0.42 阈值
        # 让 #6 通过 (它是 lecture_notes × 0.9 = 0.9)
        materials.append(
            {"score": 0.4, "source_type": "raw_notes", "title": "marginal-6"}
        )  # 0.4 × 0.6 = 0.24, 低于 0.42 → 应被过滤
        # P0-B (2026-05-12): min_keep=0 关闭 floor 验证 filter 纯逻辑.
        result = rerank(materials, min_score_threshold=0.42, top_k=5, min_keep=0)
        # marginal-6 应被过滤;剩 5 个 good-X 保留
        assert len(result) == 5
        titles = {m["title"] for m in result}
        assert "marginal-6" not in titles

    def test_top_k_applied_after_filter(self):
        from app.services.supplementary_reranker import rerank

        materials = [
            {"score": 0.9, "source_type": "lecture_notes", "title": f"hit-{i}"}
            for i in range(10)
        ]
        # P0-B (2026-05-12): min_keep=0 关闭 floor, 测试 top_k 截断行为.
        result = rerank(materials, min_score_threshold=0.42, top_k=3, min_keep=0)
        assert len(result) == 3


# ═══════════════════════════════════════════════════════════════════════════════
# P0-A (2026-05-12 hotfix): indexer 真实 source_type 过渡映射.
# lancedb_client.py:1444/1644 实际写入 {note, video_transcript, image_ocr},
# PRD §4.1.1 6 档 (lecture_notes/discussion/...) 是 indexer 升级目标.
# 这组测试锁定过渡映射, 防 PRD 6 档误删.
# ═══════════════════════════════════════════════════════════════════════════════


class TestTypeWeightsIndexerTransition:
    """P0-A: TYPE_WEIGHTS 必须覆盖 indexer 真实 source_type 防全删."""

    def test_indexer_note_mapped_to_canonical(self):
        """indexer 写入 source_type='note' 必须 → 中档 0.7 (近 chat_session)
        而不是 DEFAULT 0.5 — DEFAULT 会让真实数据被 0.42 filter 全删."""
        from app.services.supplementary_reranker import (
            DEFAULT_TYPE_WEIGHT,
            get_type_weight,
        )

        w = get_type_weight("note")
        assert w == 0.7
        assert w > DEFAULT_TYPE_WEIGHT

    def test_indexer_video_transcript_mapped_to_canonical(self):
        from app.services.supplementary_reranker import get_type_weight

        # video transcript 是核心讲义内容 → 0.9 近 discussion
        assert get_type_weight("video_transcript") == 0.9

    def test_indexer_image_ocr_mapped_to_low_canonical(self):
        from app.services.supplementary_reranker import get_type_weight

        # OCR 准确度有限 → 同 raw_notes 0.6 下限
        assert get_type_weight("image_ocr") == 0.6

    def test_prd_six_categories_still_present(self):
        """P0-A 加过渡映射后, PRD 6 档必须仍在表 (forward compat)."""
        from app.services.supplementary_reranker import TYPE_WEIGHTS

        for k in (
            "lecture_notes",
            "discussion",
            "exam_review",
            "wiki_concepts",
            "chat_session",
            "raw_notes",
        ):
            assert k in TYPE_WEIGHTS

    def test_real_indexer_data_clears_default_filter(self):
        """P0-A regression: relevance 0.5 + note 0.7 = 0.35 vs 0.42 filter
        single-shot 仍会被删 → 需要 P0-B floor 兜底; 但若 relevance 0.7+
        × note 0.7 = 0.49 通过 filter, 验证过渡映射给真实数据通道."""
        from app.services.supplementary_reranker import (
            get_filter_threshold,
            rerank,
        )

        m = {"score": 0.7, "source_type": "note", "title": "X"}
        result = rerank([m], min_score_threshold=get_filter_threshold(), min_keep=0)
        # 0.7 × 0.7 = 0.49 > 0.42 → 不被 filter 删
        assert len(result) == 1


# ═══════════════════════════════════════════════════════════════════════════════
# P0-B (2026-05-12 hotfix): filter floor 兜底 (防 P0-A note=0.7 + relevance=0.5
# = 0.35 仍 < 0.42 把材料全删).
# ═══════════════════════════════════════════════════════════════════════════════


class TestFilterFloor:
    """P0-B: filter 后剩 < min_keep 或 删 > 80% 候选 → 降级不过滤 + 标记."""

    def test_floor_triggered_marks_first_material(self):
        """所有 material 都低于 threshold → floor 触发, 返回未过滤 sorted +
        第一条注 filter_floor_triggered=True 供 logger 观测."""
        from app.services.supplementary_reranker import rerank

        # 全部 note × 0.5 = 0.35 < 0.42, 默认 min_keep=3 → floor 触发
        materials = [
            {"score": 0.5, "source_type": "note", "title": f"n{i}"} for i in range(5)
        ]
        result = rerank(materials, min_score_threshold=0.42)
        # floor 触发 → 不删, 5 条全保留
        assert len(result) == 5
        # 第一条 (sorted 后) 注 floor 旗帜
        assert result[0].get("filter_floor_triggered") is True

    def test_floor_not_triggered_when_enough_pass(self):
        """足够多材料通过 filter → floor 不触发, filter 正常.

        高分 × 高 type_weight = 通过, 低分 × 低 type_weight = 不通过."""
        from app.services.supplementary_reranker import rerank

        materials = [
            # 4 条 high: 0.9 × 1.0 = 0.9 > 0.42 → 通过
            {"score": 0.9, "source_type": "lecture_notes", "title": f"high-{i}"}
            for i in range(4)
        ] + [
            # 1 条 low: 0.3 × 0.6 = 0.18 < 0.42 → 被过滤
            {"score": 0.3, "source_type": "raw_notes", "title": "low"},
        ]
        result = rerank(materials, min_score_threshold=0.42)
        # 4 条 high 全通过 (>=min_keep=3, kill_ratio=20% <= 80%) → floor 不触发
        assert len(result) == 4
        # 无 floor 标志
        assert all("filter_floor_triggered" not in m for m in result)

    def test_min_keep_zero_disables_floor(self):
        """显式 min_keep=0 关闭 floor, 保留原 filter 语义."""
        from app.services.supplementary_reranker import rerank

        materials = [
            {"score": 0.5, "source_type": "note", "title": f"n{i}"} for i in range(5)
        ]
        result = rerank(materials, min_score_threshold=0.42, min_keep=0)
        # min_keep=0 → 全删, 返回空
        assert len(result) == 0

    def test_floor_triggered_when_kill_ratio_high(self):
        """删超 80% 也触发 floor (即使 min_keep 数量满足)."""
        from app.services.supplementary_reranker import rerank

        # 100 条都过 filter 但只剩 5 条? 我们要构造 80%+ kill 的场景:
        # 100 条 note × 0.5 = 0.35 < 0.42 全部不过 → kill_ratio=100% → floor
        materials = [
            {"score": 0.5, "source_type": "note", "title": f"n{i}"} for i in range(20)
        ]
        result = rerank(materials, min_score_threshold=0.42, min_keep=1)
        # n_post=0, n_pre=20, kill_ratio=100% > 80% → floor
        assert len(result) == 20  # 全保留
        assert result[0].get("filter_floor_triggered") is True

    def test_floor_still_respects_top_k(self):
        """floor 触发后仍走 top_k 截断."""
        from app.services.supplementary_reranker import rerank

        materials = [
            {"score": 0.5, "source_type": "note", "title": f"n{i:02d}"}
            for i in range(10)
        ]
        result = rerank(materials, min_score_threshold=0.42, top_k=5)
        assert len(result) == 5
        assert result[0].get("filter_floor_triggered") is True


# ═══════════════════════════════════════════════════════════════════════════════
# P0-3b (2026-05-12, ChatGPT v2 fail-closed real): min_keep floor must still
# exclude review/quarantine taint materials. Floor protects edge candidates
# but security review trumps quantity safety net.
# ═══════════════════════════════════════════════════════════════════════════════


class TestFilterFloorTaintExclusion:
    """P0-3b: floor 触发时也排除 review/quarantine 材料 (兜底也不能让可疑材料绕过审查)."""

    def test_min_keep_floor_excludes_review_taint(self):
        """3 个低分材料 (1 clean / 1 review / 1 clean), floor triggered →
        输出仅 clean 2 条, review 不被 floor "救活"."""
        from app.services.supplementary_reranker import rerank

        materials = [
            {
                "score": 0.5,
                "source_type": "note",  # 0.5 × 0.7 = 0.35 < 0.42 → 不通过 filter
                "title": "clean-1",
                "taint": "clean",
            },
            {
                "score": 0.5,
                "source_type": "note",
                "title": "review-malicious",
                "taint": "review",
                "injection_risk": 0.55,
            },
            {
                "score": 0.5,
                "source_type": "note",
                "title": "clean-2",
                "taint": "clean",
            },
        ]
        # filter 0.42 全删 (0.35 < 0.42) → floor triggered (n_post=0 < min_keep=3)
        result = rerank(materials, min_score_threshold=0.42, min_keep=3)
        # P0-3b: review 即使 floor 触发也被排除 → 仅剩 2 个 clean
        assert len(result) == 2
        titles = {m["title"] for m in result}
        assert "clean-1" in titles
        assert "clean-2" in titles
        assert "review-malicious" not in titles
        # floor 标志仍注入到第一条 (供 logger 观察)
        assert result[0].get("filter_floor_triggered") is True

    def test_min_keep_floor_excludes_quarantine_taint(self):
        """quarantine 材料 floor 触发时也排除."""
        from app.services.supplementary_reranker import rerank

        materials = [
            {
                "score": 0.5,
                "source_type": "note",
                "title": "clean-1",
                "taint": "clean",
            },
            {
                "score": 0.5,
                "source_type": "note",
                "title": "quarantine-mal",
                "taint": "quarantine",
                "injection_risk": 0.95,
            },
        ]
        result = rerank(materials, min_score_threshold=0.42, min_keep=3)
        # quarantine 被 P0-3b 排除
        titles = {m["title"] for m in result}
        assert "clean-1" in titles
        assert "quarantine-mal" not in titles

    def test_floor_no_taint_field_treated_as_clean(self):
        """无 taint 字段 (向后兼容) → 视为 clean, floor 保留."""
        from app.services.supplementary_reranker import rerank

        materials = [
            {"score": 0.5, "source_type": "note", "title": f"n{i}"} for i in range(5)
        ]
        result = rerank(materials, min_score_threshold=0.42, min_keep=3)
        # 无 taint 字段视为 clean → floor 保留全部 5 条
        assert len(result) == 5
        assert result[0].get("filter_floor_triggered") is True

    def test_floor_all_review_returns_empty_list(self):
        """全部材料都是 review → floor 触发后排除全部, 返回空 list (fail-closed)."""
        from app.services.supplementary_reranker import rerank

        materials = [
            {
                "score": 0.5,
                "source_type": "note",
                "title": f"mal-{i}",
                "taint": "review",
                "injection_risk": 0.6,
            }
            for i in range(5)
        ]
        result = rerank(materials, min_score_threshold=0.42, min_keep=3)
        # 全 review → floor 排除全部 → 空 list (不能 backdoor 可疑内容)
        assert len(result) == 0
