"""
Unit Tests for Progress Analyzer Service

Story 19.2 AC 1-6: 进度分析算法 + 检验历史关联分析
Tests for: src/services/progress_analyzer.py

✅ Verified from pytest documentation (Context7)
"""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from src.services.progress_analyzer import (
    ProgressAnalyzer,
    SingleReviewProgress,
)


@pytest.fixture
def analyzer():
    """Create a fresh analyzer instance without Graphiti."""
    return ProgressAnalyzer(graphiti_client=None)


@pytest.fixture
def original_canvas_file(tmp_path):
    """Create a sample original canvas with red and purple nodes."""
    canvas_data = {
        "nodes": [
            {
                "id": "concept1",
                "type": "text",
                "text": "逆否命题概念",
                "x": 0,
                "y": 0,
                "width": 200,
                "height": 100,
                "color": "4"  # Red - 完全不懂
            },
            {
                "id": "concept2",
                "type": "text",
                "text": "德摩根律",
                "x": 250,
                "y": 0,
                "width": 200,
                "height": 100,
                "color": "4"  # Red
            },
            {
                "id": "concept3",
                "type": "text",
                "text": "充要条件",
                "x": 500,
                "y": 0,
                "width": 200,
                "height": 100,
                "color": "3"  # Purple - 半懂不懂
            },
            {
                "id": "concept4",
                "type": "text",
                "text": "命题逻辑",
                "x": 0,
                "y": 150,
                "width": 200,
                "height": 100,
                "color": "3"  # Purple
            }
        ],
        "edges": []
    }

    canvas_path = tmp_path / "original.canvas"
    with open(canvas_path, 'w', encoding='utf-8') as f:
        json.dump(canvas_data, f)

    return str(canvas_path)


@pytest.fixture
def review_canvas_all_pass(tmp_path, original_canvas_file):
    """Create a review canvas where all concepts passed."""
    review_data = {
        "nodes": [
            {
                "id": "q1",
                "type": "text",
                "text": "Question for concept1",
                "sourceNodeId": "concept1",
                "color": "2"  # Green - passed
            },
            {
                "id": "q2",
                "type": "text",
                "text": "Question for concept2",
                "sourceNodeId": "concept2",
                "color": "2"  # Green - passed
            },
            {
                "id": "q3",
                "type": "text",
                "text": "Question for concept3",
                "sourceNodeId": "concept3",
                "color": "2"  # Green - passed
            },
            {
                "id": "q4",
                "type": "text",
                "text": "Question for concept4",
                "sourceNodeId": "concept4",
                "color": "2"  # Green - passed
            }
        ],
        "edges": []
    }

    review_path = tmp_path / "review-all-pass.canvas"
    with open(review_path, 'w', encoding='utf-8') as f:
        json.dump(review_data, f)

    return str(review_path)


@pytest.fixture
def review_canvas_partial_pass(tmp_path, original_canvas_file):
    """Create a review canvas where some concepts passed."""
    review_data = {
        "nodes": [
            {
                "id": "q1",
                "type": "text",
                "text": "Question for concept1",
                "sourceNodeId": "concept1",
                "color": "2"  # Green - passed
            },
            {
                "id": "q2",
                "type": "text",
                "text": "Question for concept2",
                "sourceNodeId": "concept2",
                "color": "4"  # Red - failed
            },
            {
                "id": "q3",
                "type": "text",
                "text": "Question for concept3",
                "sourceNodeId": "concept3",
                "color": "2"  # Green - passed
            },
            {
                "id": "q4",
                "type": "text",
                "text": "Question for concept4",
                "sourceNodeId": "concept4",
                "color": "3"  # Purple - failed
            }
        ],
        "edges": []
    }

    review_path = tmp_path / "review-partial.canvas"
    with open(review_path, 'w', encoding='utf-8') as f:
        json.dump(review_data, f)

    return str(review_path)


@pytest.fixture
def review_canvas_none_pass(tmp_path, original_canvas_file):
    """Create a review canvas where no concepts passed."""
    review_data = {
        "nodes": [
            {
                "id": "q1",
                "type": "text",
                "text": "Question for concept1",
                "sourceNodeId": "concept1",
                "color": "4"  # Red - failed
            },
            {
                "id": "q2",
                "type": "text",
                "text": "Question for concept2",
                "sourceNodeId": "concept2",
                "color": "4"  # Red - failed
            }
        ],
        "edges": []
    }

    review_path = tmp_path / "review-none-pass.canvas"
    with open(review_path, 'w', encoding='utf-8') as f:
        json.dump(review_data, f)

    return str(review_path)


class TestSingleReviewProgress:
    """Test single review progress analysis (AC 1, 3)."""

    @pytest.mark.asyncio
    async def test_all_concepts_passed(
        self, analyzer, original_canvas_file, review_canvas_all_pass
    ):
        """All concepts passed should show 100% coverage."""
        result = await analyzer.analyze_review_progress(
            review_canvas_all_pass,
            original_canvas_file
        )

        assert result.total_concepts == 4
        assert result.passed_count == 4
        assert result.coverage_rate == 1.0
        assert result.red_nodes_total == 2
        assert result.red_nodes_passed == 2
        assert result.purple_nodes_total == 2
        assert result.purple_nodes_passed == 2

    @pytest.mark.asyncio
    async def test_partial_concepts_passed(
        self, analyzer, original_canvas_file, review_canvas_partial_pass
    ):
        """Partial pass should show correct breakdown."""
        result = await analyzer.analyze_review_progress(
            review_canvas_partial_pass,
            original_canvas_file
        )

        assert result.total_concepts == 4
        assert result.passed_count == 2
        assert result.coverage_rate == 0.5
        # concept1 (red) passed, concept2 (red) failed
        assert result.red_nodes_passed == 1
        # concept3 (purple) passed, concept4 (purple) failed
        assert result.purple_nodes_passed == 1

    @pytest.mark.asyncio
    async def test_no_concepts_passed(
        self, analyzer, original_canvas_file, review_canvas_none_pass
    ):
        """No concepts passed should show 0% coverage."""
        result = await analyzer.analyze_review_progress(
            review_canvas_none_pass,
            original_canvas_file
        )

        assert result.total_concepts == 2  # Only 2 concepts in this review
        assert result.passed_count == 0
        assert result.coverage_rate == 0.0

    @pytest.mark.asyncio
    async def test_nonexistent_canvas_file(self, analyzer, tmp_path):
        """Non-existent files should return empty result."""
        result = await analyzer.analyze_review_progress(
            str(tmp_path / "nonexistent.canvas"),
            str(tmp_path / "also-nonexistent.canvas")
        )

        assert result.total_concepts == 0

    @pytest.mark.asyncio
    async def test_empty_review_canvas(self, analyzer, original_canvas_file, tmp_path):
        """Empty review canvas should return 0 concepts."""
        empty_data = {"nodes": [], "edges": []}
        empty_path = tmp_path / "empty.canvas"
        with open(empty_path, 'w') as f:
            json.dump(empty_data, f)

        result = await analyzer.analyze_review_progress(
            str(empty_path),
            original_canvas_file
        )

        assert result.total_concepts == 0
        assert result.coverage_rate == 0.0


class TestMultiReviewProgress:
    """Test multi-review progress analysis (AC 2, 4, 5)."""

    @pytest.mark.asyncio
    async def test_improving_trend(self, analyzer, original_canvas_file):
        """Progress improving over time should show 'improving' trend."""
        # Simulate review history with improving progress
        review_history = [
            {
                "review_canvas": "review-1.canvas",
                "timestamp": "2025-01-01T10:00:00",
                "results": {
                    "total_nodes": 4,
                    "passed_nodes": 1,
                    "concept_results": {
                        "concept1": False,
                        "concept2": False,
                        "concept3": True,
                        "concept4": False
                    }
                }
            },
            {
                "review_canvas": "review-2.canvas",
                "timestamp": "2025-01-08T10:00:00",
                "results": {
                    "total_nodes": 4,
                    "passed_nodes": 2,
                    "concept_results": {
                        "concept1": True,
                        "concept2": False,
                        "concept3": True,
                        "concept4": False
                    }
                }
            },
            {
                "review_canvas": "review-3.canvas",
                "timestamp": "2025-01-15T10:00:00",
                "results": {
                    "total_nodes": 4,
                    "passed_nodes": 4,
                    "concept_results": {
                        "concept1": True,
                        "concept2": True,
                        "concept3": True,
                        "concept4": True
                    }
                }
            }
        ]

        result = await analyzer.analyze_multi_review_progress(
            original_canvas_file,
            review_history=review_history
        )

        assert result.overall_trend == "improving"
        assert result.improvement_rate > 0.1
        assert len(result.review_history) == 3

    @pytest.mark.asyncio
    async def test_declining_trend(self, analyzer, original_canvas_file):
        """Progress declining over time should show 'declining' trend."""
        review_history = [
            {
                "review_canvas": "review-1.canvas",
                "timestamp": "2025-01-01T10:00:00",
                "results": {
                    "total_nodes": 4,
                    "passed_nodes": 4,
                    "concept_results": {}
                }
            },
            {
                "review_canvas": "review-2.canvas",
                "timestamp": "2025-01-08T10:00:00",
                "results": {
                    "total_nodes": 4,
                    "passed_nodes": 1,
                    "concept_results": {}
                }
            }
        ]

        result = await analyzer.analyze_multi_review_progress(
            original_canvas_file,
            review_history=review_history
        )

        assert result.overall_trend == "declining"
        assert result.improvement_rate < -0.1

    @pytest.mark.asyncio
    async def test_stable_trend(self, analyzer, original_canvas_file):
        """Consistent progress should show 'stable' trend."""
        review_history = [
            {
                "review_canvas": "review-1.canvas",
                "timestamp": "2025-01-01T10:00:00",
                "results": {"total_nodes": 4, "passed_nodes": 2, "concept_results": {}}
            },
            {
                "review_canvas": "review-2.canvas",
                "timestamp": "2025-01-08T10:00:00",
                "results": {"total_nodes": 4, "passed_nodes": 2, "concept_results": {}}
            }
        ]

        result = await analyzer.analyze_multi_review_progress(
            original_canvas_file,
            review_history=review_history
        )

        assert result.overall_trend == "stable"
        assert -0.1 <= result.improvement_rate <= 0.1

    @pytest.mark.asyncio
    async def test_insufficient_data(self, analyzer, original_canvas_file):
        """Single review should show 'insufficient_data' trend."""
        review_history = [
            {
                "review_canvas": "review-1.canvas",
                "timestamp": "2025-01-01T10:00:00",
                "results": {"total_nodes": 4, "passed_nodes": 2, "concept_results": {}}
            }
        ]

        result = await analyzer.analyze_multi_review_progress(
            original_canvas_file,
            review_history=review_history
        )

        assert result.overall_trend == "insufficient_data"

    @pytest.mark.asyncio
    async def test_empty_history(self, analyzer, original_canvas_file):
        """Empty history should return default MultiReviewProgress."""
        result = await analyzer.analyze_multi_review_progress(
            original_canvas_file,
            review_history=[]
        )

        assert result.overall_trend == "insufficient_data"
        assert len(result.review_history) == 0


class TestConceptTrends:
    """Test per-concept trend analysis (AC 4)."""

    @pytest.mark.asyncio
    async def test_first_pass_review_calculation(self, analyzer, original_canvas_file):
        """First pass review should be calculated correctly."""
        review_history = [
            {
                "review_canvas": "review-1.canvas",
                "timestamp": "2025-01-01",
                "results": {
                    "total_nodes": 2,
                    "passed_nodes": 0,
                    "concept_results": {
                        "concept1": False,
                        "concept2": False
                    }
                }
            },
            {
                "review_canvas": "review-2.canvas",
                "timestamp": "2025-01-08",
                "results": {
                    "total_nodes": 2,
                    "passed_nodes": 1,
                    "concept_results": {
                        "concept1": True,  # First pass on review 2
                        "concept2": False
                    }
                }
            },
            {
                "review_canvas": "review-3.canvas",
                "timestamp": "2025-01-15",
                "results": {
                    "total_nodes": 2,
                    "passed_nodes": 2,
                    "concept_results": {
                        "concept1": True,
                        "concept2": True  # First pass on review 3
                    }
                }
            }
        ]

        result = await analyzer.analyze_multi_review_progress(
            original_canvas_file,
            review_history=review_history
        )

        assert "concept1" in result.concept_trends
        assert result.concept_trends["concept1"].first_pass_review == 2
        assert result.concept_trends["concept1"].history == ["失败", "通过", "通过"]

        assert "concept2" in result.concept_trends
        assert result.concept_trends["concept2"].first_pass_review == 3
        assert result.concept_trends["concept2"].history == ["失败", "失败", "通过"]

    @pytest.mark.asyncio
    async def test_never_passed_concept(self, analyzer, original_canvas_file):
        """Concept that never passed should have first_pass_review=None."""
        review_history = [
            {
                "review_canvas": "review-1.canvas",
                "timestamp": "2025-01-01",
                "results": {
                    "total_nodes": 1,
                    "passed_nodes": 0,
                    "concept_results": {"concept1": False}
                }
            },
            {
                "review_canvas": "review-2.canvas",
                "timestamp": "2025-01-08",
                "results": {
                    "total_nodes": 1,
                    "passed_nodes": 0,
                    "concept_results": {"concept1": False}
                }
            }
        ]

        result = await analyzer.analyze_multi_review_progress(
            original_canvas_file,
            review_history=review_history
        )

        assert result.concept_trends["concept1"].first_pass_review is None
        assert result.concept_trends["concept1"].history == ["失败", "失败"]


class TestGraphitiIntegration:
    """Test Graphiti knowledge graph integration (AC 6)."""

    @pytest.mark.asyncio
    async def test_no_graphiti_client(self, analyzer, original_canvas_file):
        """Without Graphiti client, should return empty history."""
        result = await analyzer.query_review_history_from_graphiti(
            original_canvas_file
        )

        assert result == {"reviews": []}

    @pytest.mark.asyncio
    async def test_with_mock_graphiti_client(self, original_canvas_file):
        """With mock Graphiti client, should query and return results."""
        # Create mock Graphiti client
        mock_graphiti = AsyncMock()
        mock_result = MagicMock()
        mock_result.data = {
            "review_data": {
                "review_canvas": "review-1.canvas",
                "timestamp": "2025-01-01",
                "results": {
                    "total_nodes": 4,
                    "passed_nodes": 2
                }
            }
        }
        mock_graphiti.search.return_value = [mock_result]

        analyzer = ProgressAnalyzer(graphiti_client=mock_graphiti)
        result = await analyzer.query_review_history_from_graphiti(
            original_canvas_file
        )

        assert len(result["reviews"]) == 1
        mock_graphiti.search.assert_called_once()

    @pytest.mark.asyncio
    async def test_store_review_without_graphiti(
        self, analyzer, original_canvas_file
    ):
        """Store without Graphiti should return False."""
        progress = SingleReviewProgress(
            total_concepts=4,
            passed_count=2,
            coverage_rate=0.5
        )

        result = await analyzer.store_review_to_graphiti(
            original_canvas_file,
            "review.canvas",
            progress
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_store_review_with_mock_graphiti(self, original_canvas_file):
        """Store with mock Graphiti should call add_episode."""
        mock_graphiti = AsyncMock()

        analyzer = ProgressAnalyzer(graphiti_client=mock_graphiti)
        progress = SingleReviewProgress(
            total_concepts=4,
            passed_count=2,
            coverage_rate=0.5
        )

        result = await analyzer.store_review_to_graphiti(
            original_canvas_file,
            "review.canvas",
            progress
        )

        assert result is True
        mock_graphiti.add_episode.assert_called_once()


class TestCacheManagement:
    """Test cache management."""

    @pytest.mark.asyncio
    async def test_cache_reuse(
        self, analyzer, original_canvas_file, review_canvas_all_pass
    ):
        """Canvas should be loaded from cache on repeated access."""
        # First call loads from file
        await analyzer.analyze_review_progress(
            review_canvas_all_pass,
            original_canvas_file
        )
        assert len(analyzer._canvas_cache) == 2

        # Second call should use cache
        await analyzer.analyze_review_progress(
            review_canvas_all_pass,
            original_canvas_file
        )
        assert len(analyzer._canvas_cache) == 2

    @pytest.mark.asyncio
    async def test_clear_cache(
        self, analyzer, original_canvas_file, review_canvas_all_pass
    ):
        """Cache should be clearable."""
        await analyzer.analyze_review_progress(
            review_canvas_all_pass,
            original_canvas_file
        )
        assert len(analyzer._canvas_cache) == 2

        analyzer.clear_cache()
        assert len(analyzer._canvas_cache) == 0
