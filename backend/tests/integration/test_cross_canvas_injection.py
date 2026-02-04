# Canvas Learning System - Story 36.8 Integration Tests
# Cross-Canvas Context Auto-Injection Tests
"""
Integration tests for Story 36.8: Cross-Canvas Context Auto-Injection.

Tests cover:
- AC1: Automatic detection of associated lecture canvases
- AC2: Top 5 knowledge point extraction with relevance scoring
- AC3: Output format specification
- AC4: Exercise canvas detection and confidence threshold
- AC5: Performance requirement (P95 < 200ms)
- AC6: Graceful degradation when Neo4j unavailable

[Source: docs/stories/36.8.story.md#Testing]
"""

import asyncio
import time
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.context_enrichment_service import ContextEnrichmentService


# ═══════════════════════════════════════════════════════════════════════════════
# Test Fixtures
# ═══════════════════════════════════════════════════════════════════════════════

# Test canvas filenames per story spec
EXERCISE_CANVASES = [
    "线性代数-习题.canvas",
    "期末复习题-离散数学.canvas",
    "exam-calculus.canvas",
    "作业-高等数学.canvas",
    "quiz-chapter1.canvas",
    "真题-2023.canvas",
]

LECTURE_CANVASES = [
    "线性代数-讲座.canvas",
    "离散数学-笔记.canvas",
    "calculus-lecture.canvas",
]

NON_EXERCISE_CANVASES = [
    "学习笔记.canvas",
    "随笔-思考.canvas",
    "outline-notes.canvas",
]


@pytest.fixture
def mock_canvas_service():
    """Create a mock canvas service."""
    service = MagicMock()
    service.canvas_base_path = "/test/vault"
    service.read_canvas = AsyncMock(return_value={
        "nodes": [
            {"id": "node1", "type": "text", "text": "矩阵乘法定义", "x": 0, "y": 100, "color": "4"},
            {"id": "node2", "type": "text", "text": "行列式计算方法", "x": 0, "y": 200, "color": "4"},
            {"id": "node3", "type": "text", "text": "特征值求解", "x": 0, "y": 300, "color": "6"},
            {"id": "node4", "type": "text", "text": "线性变换的概念", "x": 0, "y": 400, "color": "3"},
            {"id": "node5", "type": "text", "text": "矩阵分解方法", "x": 0, "y": 500, "color": "1"},
            {"id": "node6", "type": "text", "text": "向量空间基础", "x": 0, "y": 50, "color": "4"},
        ],
        "edges": []
    })
    return service


@pytest.fixture
def mock_cross_canvas_service():
    """Create a mock cross-canvas service."""
    service = MagicMock()

    # Mock association result
    mock_association = MagicMock()
    mock_association.target_canvas_path = "线性代数-讲座.canvas"
    mock_association.target_canvas_title = "线性代数-讲座"
    mock_association.confidence = 0.85
    mock_association.common_concepts = ["矩阵乘法", "行列式", "特征值"]

    service.get_lecture_for_exercise = AsyncMock(return_value=mock_association)

    return service


@pytest.fixture
def context_enrichment_service(mock_canvas_service, mock_cross_canvas_service):
    """Create ContextEnrichmentService with mocked dependencies."""
    return ContextEnrichmentService(
        canvas_service=mock_canvas_service,
        cross_canvas_service=mock_cross_canvas_service
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Task 6.1: Test automatic exercise detection
# ═══════════════════════════════════════════════════════════════════════════════

class TestExerciseCanvasDetection:
    """Tests for Story 36.8 AC4: Exercise canvas detection."""

    def test_chinese_exercise_patterns(self, context_enrichment_service):
        """Test detection of Chinese exercise filename patterns."""
        # AC4: Canvas filename matches exercise patterns
        assert context_enrichment_service.is_exercise_canvas("线性代数-习题.canvas")
        assert context_enrichment_service.is_exercise_canvas("期末复习题-离散数学.canvas")
        assert context_enrichment_service.is_exercise_canvas("作业-高等数学.canvas")
        assert context_enrichment_service.is_exercise_canvas("期中-考试.canvas")
        assert context_enrichment_service.is_exercise_canvas("真题-2023.canvas")
        assert context_enrichment_service.is_exercise_canvas("模拟题-最终.canvas")

    def test_english_exercise_patterns(self, context_enrichment_service):
        """Test detection of English exercise filename patterns."""
        # AC4: Supports English patterns
        assert context_enrichment_service.is_exercise_canvas("exam-calculus.canvas")
        assert context_enrichment_service.is_exercise_canvas("quiz-chapter1.canvas")
        assert context_enrichment_service.is_exercise_canvas("test-final.canvas")
        assert context_enrichment_service.is_exercise_canvas("exercise-set-1.canvas")
        assert context_enrichment_service.is_exercise_canvas("problem-set.canvas")

    def test_mixed_case_patterns(self, context_enrichment_service):
        """Test case-insensitive pattern matching."""
        assert context_enrichment_service.is_exercise_canvas("EXAM-FINAL.canvas")
        assert context_enrichment_service.is_exercise_canvas("Quiz-Chapter1.canvas")
        assert context_enrichment_service.is_exercise_canvas("TEST-midterm.canvas")

    def test_non_exercise_canvases(self, context_enrichment_service):
        """Test that non-exercise canvases are not detected."""
        for canvas in NON_EXERCISE_CANVASES:
            assert not context_enrichment_service.is_exercise_canvas(canvas), \
                f"Should not detect {canvas} as exercise"

    def test_all_exercise_patterns(self, context_enrichment_service):
        """Verify all EXERCISE_PATTERNS are recognized."""
        for canvas in EXERCISE_CANVASES:
            assert context_enrichment_service.is_exercise_canvas(canvas), \
                f"Should detect {canvas} as exercise"


# ═══════════════════════════════════════════════════════════════════════════════
# Task 6.2: Test top 5 knowledge point extraction
# ═══════════════════════════════════════════════════════════════════════════════

class TestKnowledgePointExtraction:
    """Tests for Story 36.8 AC2: Knowledge point extraction."""

    def test_extracts_max_5_nodes(self, context_enrichment_service):
        """Test that exactly top 5 nodes are extracted (AC2)."""
        lecture_nodes = [
            {"id": f"node{i}", "type": "text", "text": f"Concept {i}", "x": 0, "y": i * 100, "color": "4"}
            for i in range(10)
        ]

        result = context_enrichment_service.extract_top_knowledge_points(
            lecture_nodes=lecture_nodes,
            max_nodes=5
        )

        assert len(result) == 5

    def test_color_priority_scoring(self, context_enrichment_service):
        """Test color priority: green(4) > purple(6) > yellow(3) > red(1)."""
        # AC2: Green/mastered concepts prioritized for reference
        nodes = [
            {"id": "red", "type": "text", "text": "Red node", "x": 0, "y": 100, "color": "1"},
            {"id": "green", "type": "text", "text": "Green node", "x": 0, "y": 100, "color": "4"},
            {"id": "yellow", "type": "text", "text": "Yellow node", "x": 0, "y": 100, "color": "3"},
            {"id": "purple", "type": "text", "text": "Purple node", "x": 0, "y": 100, "color": "6"},
        ]

        result = context_enrichment_service.extract_top_knowledge_points(
            lecture_nodes=nodes,
            exercise_content="",
            max_nodes=4
        )

        # Green should have highest score, followed by purple, yellow, red
        ids = [n["id"] for n in result]
        green_idx = ids.index("green")
        purple_idx = ids.index("purple")
        yellow_idx = ids.index("yellow")
        red_idx = ids.index("red")

        assert green_idx < red_idx, "Green should rank higher than red"
        assert purple_idx < red_idx, "Purple should rank higher than red"

    def test_position_scoring(self, context_enrichment_service):
        """Test position scoring: earlier (smaller Y) = higher score."""
        # AC2: Position in lecture - earlier concepts prioritized
        nodes = [
            {"id": "late", "type": "text", "text": "Later concept", "x": 0, "y": 1000, "color": "4"},
            {"id": "early", "type": "text", "text": "Earlier concept", "x": 0, "y": 100, "color": "4"},
            {"id": "middle", "type": "text", "text": "Middle concept", "x": 0, "y": 500, "color": "4"},
        ]

        result = context_enrichment_service.extract_top_knowledge_points(
            lecture_nodes=nodes,
            exercise_content="",
            max_nodes=3
        )

        # Earlier nodes should rank higher (all same color, no exercise content)
        ids = [n["id"] for n in result]
        assert ids.index("early") < ids.index("late"), "Earlier concept should rank higher"

    def test_semantic_similarity_scoring(self, context_enrichment_service):
        """Test semantic similarity: nodes matching exercise content rank higher."""
        # AC2: Relevance scoring based on semantic similarity
        # Use English words to avoid Chinese character parsing variations
        nodes = [
            {"id": "unrelated", "type": "text", "text": "something completely different xyz abc", "x": 0, "y": 100, "color": "4"},
            {"id": "related", "type": "text", "text": "matrix multiplication calculation method", "x": 0, "y": 100, "color": "4"},
        ]

        result = context_enrichment_service.extract_top_knowledge_points(
            lecture_nodes=nodes,
            exercise_content="matrix multiplication",
            max_nodes=2
        )

        # Related node should rank higher due to semantic similarity (word overlap)
        ids = [n["id"] for n in result]
        assert ids.index("related") < ids.index("unrelated"), \
            f"Related content should rank higher, got order: {ids}"

    def test_content_length_limit(self, context_enrichment_service):
        """Test content truncation to max_content_length."""
        # Task 3.3: Limit to 300 chars
        long_text = "A" * 500
        nodes = [
            {"id": "long", "type": "text", "text": long_text, "x": 0, "y": 100, "color": "4"},
        ]

        result = context_enrichment_service.extract_top_knowledge_points(
            lecture_nodes=nodes,
            max_content_length=300
        )

        assert len(result[0]["text"]) == 300

    def test_only_text_nodes_extracted(self, context_enrichment_service):
        """Test that only text nodes are extracted, not file/link/group."""
        nodes = [
            {"id": "text", "type": "text", "text": "Text content", "x": 0, "y": 100},
            {"id": "file", "type": "file", "file": "note.md", "x": 0, "y": 200},
            {"id": "link", "type": "link", "url": "https://example.com", "x": 0, "y": 300},
            {"id": "group", "type": "group", "x": 0, "y": 400},
        ]

        result = context_enrichment_service.extract_top_knowledge_points(
            lecture_nodes=nodes,
            max_nodes=10
        )

        assert len(result) == 1
        assert result[0]["id"] == "text"

    def test_empty_nodes_handled(self, context_enrichment_service):
        """Test graceful handling of empty node list."""
        result = context_enrichment_service.extract_top_knowledge_points(
            lecture_nodes=[],
            max_nodes=5
        )

        assert result == []


# ═══════════════════════════════════════════════════════════════════════════════
# Task 6.3: Test format output specification
# ═══════════════════════════════════════════════════════════════════════════════

class TestFormatOutputSpecification:
    """Tests for Story 36.8 AC3: Output format specification."""

    def test_section_header_format(self, context_enrichment_service):
        """Test section header format (AC3 Task 4.2)."""
        cross_ctx = {
            "lecture_canvas_path": "线性代数-讲座.canvas",
            "lecture_canvas_title": "线性代数-讲座",
            "relevant_nodes": [],
            "confidence": 0.85,
            "common_concepts": []
        }

        result = context_enrichment_service._format_cross_canvas_context(cross_ctx)

        assert "--- 参见讲座知识点 (Lecture References) ---" in result

    def test_confidence_in_header(self, context_enrichment_service):
        """Test confidence score in header (AC3 Task 4.3)."""
        cross_ctx = {
            "lecture_canvas_path": "线性代数-讲座.canvas",
            "lecture_canvas_title": "线性代数-讲座",
            "relevant_nodes": [],
            "confidence": 0.85,
            "common_concepts": []
        }

        result = context_enrichment_service._format_cross_canvas_context(cross_ctx)

        assert "(置信度: 85%)" in result

    def test_knowledge_point_format(self, context_enrichment_service):
        """Test knowledge point format: [参见讲座: {name}] {content} (AC3 Task 4.1)."""
        cross_ctx = {
            "lecture_canvas_path": "线性代数-讲座.canvas",
            "lecture_canvas_title": "线性代数-讲座",
            "relevant_nodes": [
                {"id": "node1", "text": "矩阵乘法的定义", "color": "4"}
            ],
            "confidence": 0.85,
            "common_concepts": []
        }

        result = context_enrichment_service._format_cross_canvas_context(cross_ctx)

        assert "[参见讲座: 线性代数-讲座] 矩阵乘法的定义" in result

    def test_common_concepts_display(self, context_enrichment_service):
        """Test common concepts display in format."""
        cross_ctx = {
            "lecture_canvas_path": "线性代数-讲座.canvas",
            "lecture_canvas_title": "线性代数-讲座",
            "relevant_nodes": [],
            "confidence": 0.85,
            "common_concepts": ["矩阵乘法", "行列式", "特征值"]
        }

        result = context_enrichment_service._format_cross_canvas_context(cross_ctx)

        assert "[共同概念]" in result
        assert "矩阵乘法" in result

    def test_multiple_knowledge_points(self, context_enrichment_service):
        """Test multiple knowledge points formatting."""
        cross_ctx = {
            "lecture_canvas_path": "线性代数-讲座.canvas",
            "lecture_canvas_title": "线性代数-讲座",
            "relevant_nodes": [
                {"id": "node1", "text": "概念一", "color": "4"},
                {"id": "node2", "text": "概念二", "color": "4"},
                {"id": "node3", "text": "概念三", "color": "4"},
            ],
            "confidence": 0.85,
            "common_concepts": []
        }

        result = context_enrichment_service._format_cross_canvas_context(cross_ctx)

        # Each knowledge point should have its own line
        assert result.count("[参见讲座: 线性代数-讲座]") == 4  # Header + 3 nodes


# ═══════════════════════════════════════════════════════════════════════════════
# Task 6.4: Test fallback behavior when Neo4j unavailable
# ═══════════════════════════════════════════════════════════════════════════════

class TestNeo4jFallback:
    """Tests for Story 36.8 AC6: Graceful degradation."""

    @pytest.mark.asyncio
    async def test_works_without_neo4j_client(self, mock_canvas_service):
        """Test service works when Neo4j is unavailable."""
        # AC6: Service should work with fallback
        mock_cross_canvas = MagicMock()
        mock_cross_canvas.get_lecture_for_exercise = AsyncMock(return_value=None)

        service = ContextEnrichmentService(
            canvas_service=mock_canvas_service,
            cross_canvas_service=mock_cross_canvas
        )

        result = await service.get_cross_canvas_context("习题-测试.canvas")

        # Should return None gracefully without error
        assert result is None

    @pytest.mark.asyncio
    async def test_graceful_degradation_on_exception(self, mock_canvas_service):
        """Test graceful degradation when canvas read fails after getting association."""
        # AC6: Graceful degradation on errors - tests partial result return
        mock_association = MagicMock()
        mock_association.target_canvas_path = "lecture.canvas"
        mock_association.target_canvas_title = "Lecture"
        mock_association.confidence = 0.85
        mock_association.common_concepts = ["concept1"]

        mock_cross_canvas = MagicMock()
        mock_cross_canvas.get_lecture_for_exercise = AsyncMock(return_value=mock_association)

        # Canvas service throws exception when reading lecture
        mock_canvas_service.read_canvas = AsyncMock(
            side_effect=Exception("Failed to read canvas")
        )

        service = ContextEnrichmentService(
            canvas_service=mock_canvas_service,
            cross_canvas_service=mock_cross_canvas
        )

        # Should return partial result, not raise exception
        result = await service.get_cross_canvas_context("习题-测试.canvas")

        # Should return partial result with basic info but empty nodes
        assert result is not None
        assert result["lecture_canvas_path"] == "lecture.canvas"
        assert result["relevant_nodes"] == []  # Empty due to read failure

    @pytest.mark.asyncio
    async def test_no_cross_canvas_service(self, mock_canvas_service):
        """Test when cross_canvas_service is not provided."""
        service = ContextEnrichmentService(
            canvas_service=mock_canvas_service,
            cross_canvas_service=None  # No cross-canvas service
        )

        result = await service.get_cross_canvas_context("习题-测试.canvas")

        assert result is None


# ═══════════════════════════════════════════════════════════════════════════════
# Task 6.5: Test confidence threshold
# ═══════════════════════════════════════════════════════════════════════════════

class TestConfidenceThreshold:
    """Tests for Story 36.8 AC4: Confidence threshold check."""

    def test_should_inject_with_high_confidence(self, context_enrichment_service):
        """Test injection allowed when confidence >= 0.6."""
        # AC4: Valid lecture association with confidence >= 0.6
        assert context_enrichment_service._should_inject_cross_canvas_context(
            "习题-线性代数.canvas", 0.85
        )
        assert context_enrichment_service._should_inject_cross_canvas_context(
            "exam-calculus.canvas", 0.6
        )
        assert context_enrichment_service._should_inject_cross_canvas_context(
            "期末复习题.canvas", 1.0
        )

    def test_should_not_inject_with_low_confidence(self, context_enrichment_service):
        """Test injection blocked when confidence < 0.6."""
        # AC4: Should not inject below threshold
        assert not context_enrichment_service._should_inject_cross_canvas_context(
            "习题-线性代数.canvas", 0.5
        )
        assert not context_enrichment_service._should_inject_cross_canvas_context(
            "exam-calculus.canvas", 0.3
        )
        assert not context_enrichment_service._should_inject_cross_canvas_context(
            "期末复习题.canvas", 0.0
        )

    def test_should_not_inject_for_non_exercise(self, context_enrichment_service):
        """Test injection blocked for non-exercise canvases regardless of confidence."""
        # AC4: Only inject for exercise canvases
        assert not context_enrichment_service._should_inject_cross_canvas_context(
            "线性代数-讲座.canvas", 0.85
        )
        assert not context_enrichment_service._should_inject_cross_canvas_context(
            "学习笔记.canvas", 0.95
        )

    def test_threshold_boundary_value(self, context_enrichment_service):
        """Test boundary value at exactly 0.6."""
        # AC4: confidence >= 0.6 should pass
        assert context_enrichment_service._should_inject_cross_canvas_context(
            "习题-测试.canvas", 0.6
        )
        assert not context_enrichment_service._should_inject_cross_canvas_context(
            "习题-测试.canvas", 0.59
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Task 6.6: Test performance under 200ms
# ═══════════════════════════════════════════════════════════════════════════════

class TestPerformance:
    """Tests for Story 36.8 AC5: Performance requirement (P95 < 200ms)."""

    @pytest.mark.asyncio
    async def test_cross_canvas_retrieval_under_200ms(
        self,
        mock_canvas_service,
        mock_cross_canvas_service
    ):
        """Test cross-canvas context retrieval completes within 200ms."""
        # AC5: P95 < 200ms
        service = ContextEnrichmentService(
            canvas_service=mock_canvas_service,
            cross_canvas_service=mock_cross_canvas_service
        )

        # Measure time
        start = time.time()
        result = await service.get_cross_canvas_context("习题-线性代数.canvas")
        elapsed_ms = (time.time() - start) * 1000

        assert result is not None
        assert elapsed_ms < 200, f"Retrieval took {elapsed_ms:.2f}ms, exceeds 200ms target"

    @pytest.mark.asyncio
    async def test_caching_improves_performance(
        self,
        mock_canvas_service,
        mock_cross_canvas_service
    ):
        """Test that caching significantly improves second request."""
        # Task 5.1: 30s TTL caching
        service = ContextEnrichmentService(
            canvas_service=mock_canvas_service,
            cross_canvas_service=mock_cross_canvas_service
        )

        canvas_path = "习题-线性代数.canvas"

        # First request (cache miss)
        start1 = time.time()
        result1 = await service.get_cross_canvas_context(canvas_path)
        elapsed1_ms = (time.time() - start1) * 1000

        # Second request (cache hit)
        start2 = time.time()
        result2 = await service.get_cross_canvas_context(canvas_path)
        elapsed2_ms = (time.time() - start2) * 1000

        # Cache hit should be significantly faster
        assert elapsed2_ms < elapsed1_ms, \
            f"Cache hit ({elapsed2_ms:.2f}ms) should be faster than miss ({elapsed1_ms:.2f}ms)"

        # Cache hit should be very fast (< 10ms)
        assert elapsed2_ms < 10, f"Cache hit took {elapsed2_ms:.2f}ms, should be < 10ms"

    @pytest.mark.asyncio
    async def test_cache_ttl_expiration(
        self,
        mock_canvas_service,
        mock_cross_canvas_service
    ):
        """Test cache expires after TTL."""
        # Task 5.1: 30s TTL (we test with shorter TTL)
        service = ContextEnrichmentService(
            canvas_service=mock_canvas_service,
            cross_canvas_service=mock_cross_canvas_service
        )
        # Override TTL to 0.1 seconds for testing
        service._association_cache_ttl = 0.1

        canvas_path = "习题-测试.canvas"

        # First request
        await service.get_cross_canvas_context(canvas_path)

        # Cache should be populated
        assert canvas_path in service._association_cache

        # Wait for TTL to expire
        await asyncio.sleep(0.2)

        # Check cache - should be cleared on next access
        cached = service._get_cached_association(canvas_path)
        assert cached is None, "Cache should have expired"

    @pytest.mark.asyncio
    async def test_knowledge_point_extraction_performance(self, context_enrichment_service):
        """Test knowledge point extraction completes quickly."""
        # Create large node set
        large_node_set = [
            {"id": f"node{i}", "type": "text", "text": f"Concept {i} with some content",
             "x": 0, "y": i * 100, "color": "4"}
            for i in range(100)
        ]

        start = time.time()
        result = context_enrichment_service.extract_top_knowledge_points(
            lecture_nodes=large_node_set,
            exercise_content="Concept 50 related",
            max_nodes=5
        )
        elapsed_ms = (time.time() - start) * 1000

        assert len(result) == 5
        # Extraction of 100 nodes should be very fast (< 50ms)
        assert elapsed_ms < 50, f"Extraction took {elapsed_ms:.2f}ms, should be < 50ms"


# ═══════════════════════════════════════════════════════════════════════════════
# Integration Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestCrossCanvasIntegration:
    """Integration tests for end-to-end cross-canvas injection."""

    @pytest.mark.asyncio
    async def test_full_cross_canvas_context_retrieval(
        self,
        context_enrichment_service
    ):
        """Test full flow: detection -> extraction -> formatting."""
        canvas_path = "习题-线性代数.canvas"

        # 1. Detect exercise canvas
        assert context_enrichment_service.is_exercise_canvas(canvas_path)

        # 2. Get cross-canvas context
        cross_ctx = await context_enrichment_service.get_cross_canvas_context(canvas_path)
        assert cross_ctx is not None

        # 3. Verify context structure
        assert "lecture_canvas_path" in cross_ctx
        assert "lecture_canvas_title" in cross_ctx
        assert "relevant_nodes" in cross_ctx
        assert "confidence" in cross_ctx

        # 4. Format context
        formatted = context_enrichment_service._format_cross_canvas_context(cross_ctx)
        assert "--- 参见讲座知识点" in formatted
        assert "[参见讲座:" in formatted

    @pytest.mark.asyncio
    async def test_negative_caching(self, mock_canvas_service):
        """Test that negative results (no association) are also cached."""
        mock_cross_canvas = MagicMock()
        mock_cross_canvas.get_lecture_for_exercise = AsyncMock(return_value=None)

        service = ContextEnrichmentService(
            canvas_service=mock_canvas_service,
            cross_canvas_service=mock_cross_canvas
        )

        canvas_path = "习题-无关联.canvas"

        # First call
        result1 = await service.get_cross_canvas_context(canvas_path)
        assert result1 is None

        # Should be cached
        assert canvas_path in service._association_cache
        cached_result, _ = service._association_cache[canvas_path]
        assert cached_result is None

        # Second call should use cache (not call service again)
        result2 = await service.get_cross_canvas_context(canvas_path)
        assert result2 is None

        # Service should only be called once
        assert mock_cross_canvas.get_lecture_for_exercise.call_count == 1
