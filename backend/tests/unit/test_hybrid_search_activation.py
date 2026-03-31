# Epic 5: Chinese Hybrid Search Activation
# Features 5.1 + 5.2: Default hybrid mode + jieba tokenization wired
#
# Verification tests confirming that hybrid search is correctly configured
# and jieba tokenization is wired into both index-time and query-time paths.
"""
Tests for Epic 5: Chinese Hybrid Search Activation.

Feature 5.1: Default search mode is "hybrid" (not "vector").
Feature 5.2: jieba tokenization wired into search pipeline at index and query time.
"""

import inspect

import pytest

from src.agentic_rag.clients.lancedb_client import (
    JIEBA_AVAILABLE,
    LanceDBClient,
    _jieba_tokenize,
)
from src.agentic_rag.config import DEFAULT_CONFIG


# ---------------------------------------------------------------------------
# Feature 5.1: Default search mode is hybrid
# ---------------------------------------------------------------------------


class TestDefaultSearchModeIsHybrid:
    """Feature 5.1: Verify system defaults to hybrid search everywhere."""

    def test_default_config_search_type_is_hybrid(self) -> None:
        """AC: DEFAULT_CONFIG['search_type'] == 'hybrid'."""
        assert DEFAULT_CONFIG.get("search_type") == "hybrid", (
            f"Expected DEFAULT_CONFIG search_type='hybrid', "
            f"got '{DEFAULT_CONFIG.get('search_type')}'"
        )

    def test_lancedb_client_search_default_query_type_is_hybrid(self) -> None:
        """AC: LanceDBClient.search() default query_type parameter is 'hybrid'."""
        sig = inspect.signature(LanceDBClient.search)
        param = sig.parameters.get("query_type")
        assert param is not None, "search() missing query_type parameter"
        assert param.default == "hybrid", (
            f"Expected search() query_type default='hybrid', got '{param.default}'"
        )

    def test_lancedb_client_search_internal_default_query_type_is_hybrid(self) -> None:
        """AC: LanceDBClient._search_internal() default query_type is 'hybrid'."""
        sig = inspect.signature(LanceDBClient._search_internal)
        param = sig.parameters.get("query_type")
        assert param is not None, "_search_internal() missing query_type parameter"
        assert param.default == "hybrid", (
            f"Expected _search_internal() query_type default='hybrid', "
            f"got '{param.default}'"
        )


# ---------------------------------------------------------------------------
# Feature 5.2: jieba tokenization wired into search pipeline
# ---------------------------------------------------------------------------


class TestJiebaTokenizationFunction:
    """Feature 5.2: _jieba_tokenize works for Chinese, English, and mixed text."""

    def test_jieba_is_available(self) -> None:
        """AC: jieba library is installed and importable."""
        assert JIEBA_AVAILABLE is True, (
            "jieba is not available — install with: pip install jieba"
        )

    def test_jieba_tokenize_chinese(self) -> None:
        """AC: Chinese text is segmented into space-separated tokens."""
        result = _jieba_tokenize("机器学习是人工智能的子集")
        # jieba segments Chinese into words; result must have spaces
        assert " " in result, (
            f"Expected tokenized Chinese to contain spaces, got: '{result}'"
        )
        # Key tokens that jieba precise mode produces
        assert "机器" in result
        assert "学习" in result
        assert "人工智能" in result

    def test_jieba_tokenize_english(self) -> None:
        """AC: English text passes through correctly (jieba splits on spaces)."""
        text = "machine learning is a subset of AI"
        result = _jieba_tokenize(text)
        # English words should be preserved
        assert "machine" in result
        assert "learning" in result
        assert "AI" in result

    def test_jieba_tokenize_mixed_chinese_english(self) -> None:
        """AC: Mixed Chinese+English text is properly tokenized."""
        text = "深度学习deep learning是machine learning的分支"
        result = _jieba_tokenize(text)
        # Chinese tokens
        assert "深度" in result
        assert "学习" in result
        # English tokens preserved
        assert "deep" in result
        assert "learning" in result

    def test_jieba_tokenize_empty_string(self) -> None:
        """AC: Empty string returns empty string (no crash)."""
        assert _jieba_tokenize("") == ""

    def test_jieba_tokenize_whitespace_only(self) -> None:
        """AC: Whitespace-only string returns itself (no crash)."""
        result = _jieba_tokenize("   ")
        assert result == "   "

    def test_jieba_tokenize_returns_string(self) -> None:
        """AC: Return type is always str."""
        result = _jieba_tokenize("测试文本")
        assert isinstance(result, str)


class TestContentTokenizedAtIndexTime:
    """Feature 5.2: content_tokenized column is populated during add_documents."""

    def test_add_documents_builds_content_tokenized_field(self) -> None:
        """AC: add_documents injects content_tokenized via _jieba_tokenize.

        Verifies by inspecting the source code of add_documents to confirm
        that _jieba_tokenize(content) is called to populate content_tokenized.
        This is a structural verification — the actual column creation requires
        a live LanceDB instance which is covered by integration tests.
        """
        source = inspect.getsource(LanceDBClient.add_documents)
        # The line: "content_tokenized": _jieba_tokenize(content),
        assert "_jieba_tokenize(content)" in source, (
            "add_documents must call _jieba_tokenize(content) to populate "
            "content_tokenized column"
        )
        assert '"content_tokenized"' in source, (
            "add_documents must produce a 'content_tokenized' field"
        )


class TestHybridSearchUsesJieba:
    """Feature 5.2: Hybrid search branch tokenizes queries with jieba."""

    def test_search_internal_calls_jieba_on_fts_query(self) -> None:
        """AC: _search_internal hybrid branch calls _jieba_tokenize on the query.

        Structural verification that the FTS branch uses jieba tokenization.
        """
        source = inspect.getsource(LanceDBClient._search_internal)
        # Must tokenize query for FTS
        assert "_jieba_tokenize(query)" in source, (
            "_search_internal must call _jieba_tokenize(query) for FTS branch"
        )

    def test_search_internal_has_rrf_fusion(self) -> None:
        """AC: _search_internal uses RRF fusion to combine vector + FTS results."""
        source = inspect.getsource(LanceDBClient._search_internal)
        assert "_rrf_fuse" in source, (
            "_search_internal must call _rrf_fuse to combine vector and FTS results"
        )

    def test_rrf_fuse_method_exists(self) -> None:
        """AC: LanceDBClient has a _rrf_fuse static method."""
        assert hasattr(LanceDBClient, "_rrf_fuse"), (
            "LanceDBClient must have _rrf_fuse method for RRF fusion"
        )
        assert callable(LanceDBClient._rrf_fuse)


class TestRRFFusion:
    """Feature 5.1: RRF fusion correctly merges vector and FTS results."""

    def test_rrf_fuse_merges_two_lists(self) -> None:
        """AC: _rrf_fuse combines vector and FTS results into a ranked list."""
        vector_results = [
            {"doc_id": "a", "content": "alpha", "_distance": 0.1},
            {"doc_id": "b", "content": "beta", "_distance": 0.3},
        ]
        fts_results = [
            {"doc_id": "b", "content": "beta", "_distance": 0.2},
            {"doc_id": "c", "content": "gamma", "_distance": 0.4},
        ]
        merged = LanceDBClient._rrf_fuse(vector_results, fts_results, limit=10, k=60)
        doc_ids = [r["doc_id"] for r in merged]
        # 'b' appears in both lists, should rank highest (highest RRF score)
        assert doc_ids[0] == "b", (
            f"Doc 'b' (in both lists) should rank first, got: {doc_ids}"
        )
        # All three docs should appear
        assert set(doc_ids) == {"a", "b", "c"}

    def test_rrf_fuse_single_source_vector_only(self) -> None:
        """AC: RRF degrades gracefully when only vector results exist."""
        vector_results = [
            {"doc_id": "a", "content": "alpha"},
            {"doc_id": "b", "content": "beta"},
        ]
        merged = LanceDBClient._rrf_fuse(vector_results, [], limit=10, k=60)
        assert len(merged) == 2
        assert merged[0]["doc_id"] == "a"

    def test_rrf_fuse_single_source_fts_only(self) -> None:
        """AC: RRF degrades gracefully when only FTS results exist."""
        fts_results = [
            {"doc_id": "x", "content": "x-ray"},
            {"doc_id": "y", "content": "yellow"},
        ]
        merged = LanceDBClient._rrf_fuse([], fts_results, limit=10, k=60)
        assert len(merged) == 2
        assert merged[0]["doc_id"] == "x"

    def test_rrf_fuse_respects_limit(self) -> None:
        """AC: RRF fusion respects the limit parameter."""
        vector_results = [{"doc_id": f"v{i}", "content": f"v{i}"} for i in range(5)]
        fts_results = [{"doc_id": f"f{i}", "content": f"f{i}"} for i in range(5)]
        merged = LanceDBClient._rrf_fuse(vector_results, fts_results, limit=3, k=60)
        assert len(merged) == 3

    def test_rrf_fuse_empty_inputs(self) -> None:
        """AC: RRF fusion with both empty lists returns empty."""
        merged = LanceDBClient._rrf_fuse([], [], limit=10, k=60)
        assert merged == []


class TestFTSIndexRebuild:
    """Feature 5.2: FTS index is rebuilt on content_tokenized after indexing."""

    def test_rebuild_fts_index_method_exists(self) -> None:
        """AC: _rebuild_fts_index method exists on LanceDBClient."""
        assert hasattr(LanceDBClient, "_rebuild_fts_index")
        assert callable(LanceDBClient._rebuild_fts_index)

    def test_rebuild_fts_index_targets_content_tokenized(self) -> None:
        """AC: _rebuild_fts_index creates FTS index on content_tokenized column."""
        source = inspect.getsource(LanceDBClient._rebuild_fts_index)
        assert '"content_tokenized"' in source, (
            "_rebuild_fts_index must target the 'content_tokenized' column"
        )

    def test_index_canvas_rebuilds_fts(self) -> None:
        """AC: index_canvas calls _rebuild_fts_index after indexing."""
        source = inspect.getsource(LanceDBClient.index_canvas)
        assert "_rebuild_fts_index" in source, (
            "index_canvas must call _rebuild_fts_index to enable hybrid search"
        )

    def test_index_vault_notes_rebuilds_fts(self) -> None:
        """AC: index_vault_notes calls _rebuild_fts_index after indexing."""
        source = inspect.getsource(LanceDBClient.index_vault_notes)
        assert "_rebuild_fts_index" in source, (
            "index_vault_notes must call _rebuild_fts_index to enable hybrid search"
        )
