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

        # "note" 是 supplementary_search_service _normalize_material 的默认值
        # — 必须落到 DEFAULT 而非任何 canonical
        assert get_type_weight("note") == DEFAULT_TYPE_WEIGHT
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
        result = rerank(materials, min_score_threshold=0.42)
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
        result = rerank(materials, min_score_threshold=0.42, top_k=5)
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
        result = rerank(materials, min_score_threshold=0.42, top_k=3)
        assert len(result) == 3
