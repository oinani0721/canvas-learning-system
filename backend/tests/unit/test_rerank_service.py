"""Story 2.2+2.9 (merged) Task 3.3 — rerank_service BM25 + normalize unit tests.

覆盖:
- tokenize: jieba 中英混合分词 + 小写 + 过滤纯标点
- bm25_scores: Okapi BM25 标准排序行为 / 空输入边界
- normalize_to_unit: min-max [0,1] + tie 处理
"""

from __future__ import annotations

import math

import pytest


class TestTokenize:
    def test_english_lowercased(self):
        from app.services.rerank_service import tokenize

        toks = tokenize("Admissible Heuristic Search")
        assert "admissible" in toks
        assert "heuristic" in toks
        assert "Admissible" not in toks

    def test_chinese_segmented(self):
        from app.services.rerank_service import tokenize

        toks = tokenize("启发式搜索的可纳性证明")
        # jieba 至少能切出"启发式" / "搜索" / "可纳性" 之类
        assert len(toks) >= 2

    def test_pure_punctuation_filtered(self):
        from app.services.rerank_service import tokenize

        toks = tokenize("---")
        assert toks == []

    def test_empty_string_returns_empty(self):
        from app.services.rerank_service import tokenize

        assert tokenize("") == []
        assert tokenize("   ") == []


class TestBM25Scores:
    def test_empty_query_returns_zeros(self):
        from app.services.rerank_service import bm25_scores

        assert bm25_scores("", ["doc1", "doc2"]) == [0.0, 0.0]

    def test_empty_documents_returns_empty(self):
        from app.services.rerank_service import bm25_scores

        assert bm25_scores("query", []) == []

    def test_query_token_match_scores_higher(self):
        """含 query 词的文档 BM25 score 必须 > 不含的."""
        from app.services.rerank_service import bm25_scores

        scores = bm25_scores(
            "admissible heuristic",
            [
                "admissible heuristic guarantees optimality",  # 含 query terms
                "completely unrelated content about cooking",  # 无
            ],
        )
        assert scores[0] > scores[1]
        assert scores[1] == 0.0

    def test_higher_term_frequency_scores_higher(self):
        """同长度文档,query term 出现更频繁 → 更高 score (BM25 TF saturation)."""
        from app.services.rerank_service import bm25_scores

        scores = bm25_scores(
            "heuristic",
            [
                "heuristic heuristic heuristic search algorithm",  # 3× heuristic
                "heuristic search algorithm baseline",  # 1× heuristic
            ],
        )
        assert scores[0] > scores[1]

    def test_length_normalization(self):
        """同样 TF=1,短文档 BM25 score 应 > 长文档 (length norm penalty)."""
        from app.services.rerank_service import bm25_scores

        scores = bm25_scores(
            "heuristic",
            [
                "heuristic",  # 短
                "heuristic search algorithm baseline introduction details overview",  # 长
            ],
        )
        assert scores[0] > scores[1]

    def test_chinese_query_matches_chinese_doc(self):
        from app.services.rerank_service import bm25_scores

        scores = bm25_scores(
            "启发式",
            [
                "启发式搜索算法",
                "完全无关的烹饪笔记",
            ],
        )
        assert scores[0] > 0.0
        # 无关文档 score = 0
        assert scores[1] == 0.0

    def test_all_empty_documents_returns_zeros(self):
        from app.services.rerank_service import bm25_scores

        assert bm25_scores("query", ["", "  "]) == [0.0, 0.0]

    def test_finite_scores(self):
        """边界: 不返回 inf / nan."""
        from app.services.rerank_service import bm25_scores

        scores = bm25_scores("foo bar baz", ["foo bar", "bar baz"])
        for s in scores:
            assert math.isfinite(s)


class TestNormalizeToUnit:
    def test_empty(self):
        from app.services.rerank_service import normalize_to_unit

        assert normalize_to_unit([]) == []

    def test_min_max_basic(self):
        from app.services.rerank_service import normalize_to_unit

        result = normalize_to_unit([0.0, 5.0, 10.0])
        assert result[0] == pytest.approx(0.0)
        assert result[1] == pytest.approx(0.5)
        assert result[2] == pytest.approx(1.0)

    def test_all_zero_returns_all_zero(self):
        from app.services.rerank_service import normalize_to_unit

        assert normalize_to_unit([0.0, 0.0, 0.0]) == [0.0, 0.0, 0.0]

    def test_all_equal_nonzero_returns_half(self):
        from app.services.rerank_service import normalize_to_unit

        # 全等且 > 0: 视为"有信号无区分", 全 0.5
        result = normalize_to_unit([3.7, 3.7, 3.7])
        assert all(r == 0.5 for r in result)

    def test_single_element(self):
        from app.services.rerank_service import normalize_to_unit

        assert normalize_to_unit([4.2]) == [0.5]  # 单元素 nonzero 视作"有信号"
        assert normalize_to_unit([0.0]) == [0.0]

    def test_negative_handled(self):
        """BM25 IDF +1 smoothing 防负, 但 normalize 应能处理负输入."""
        from app.services.rerank_service import normalize_to_unit

        result = normalize_to_unit([-1.0, 0.0, 1.0])
        assert result[0] == pytest.approx(0.0)
        assert result[1] == pytest.approx(0.5)
        assert result[2] == pytest.approx(1.0)
