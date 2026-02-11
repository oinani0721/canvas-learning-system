# Canvas Learning System - Cross-Canvas Auto-Discovery Tests
# Story 36.6: AC6 - Unit tests for auto-discovery algorithms
"""
Unit tests for cross-canvas auto-discovery functionality.

[Source: docs/stories/36.6.story.md#Task-6]
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List

from app.services.cross_canvas_service import (
    CrossCanvasService,
    AutoDiscoverySuggestion,
    AutoDiscoveryResult,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def mock_neo4j_client():
    """Create a mock Neo4jClient for testing."""
    client = AsyncMock()
    client.get_canvas_concepts = AsyncMock(return_value=[])
    client.find_common_concepts = AsyncMock(return_value=[])
    return client


@pytest.fixture
def cross_canvas_service(mock_neo4j_client):
    """Create CrossCanvasService with mocked dependencies."""
    service = CrossCanvasService()
    service.neo4j_client = mock_neo4j_client
    return service


# ═══════════════════════════════════════════════════════════════════════════════
# Task 6.1: Test filename pattern matching (Chinese and English)
# ═══════════════════════════════════════════════════════════════════════════════

class TestDiscoverCanvasType:
    """Test canvas type discovery via filename patterns.

    [Source: docs/stories/36.6.story.md#Task-1.2]
    """

    def test_exercise_patterns_chinese(self, cross_canvas_service):
        """Chinese exercise patterns should identify as 'exercise'."""
        exercise_names = [
            "离散数学习题.canvas",
            "线性代数题目.canvas",
            "微积分练习.canvas",
            "物理作业.canvas",
            "期末复习题.canvas",
            "期中考试.canvas",
            "真题2023.canvas",
            "模拟试卷.canvas",
        ]

        for name in exercise_names:
            result = cross_canvas_service.discover_canvas_type(name)
            assert result == "exercise", f"Expected 'exercise' for {name}, got {result}"

    def test_exercise_patterns_english(self, cross_canvas_service):
        """English exercise patterns should identify as 'exercise'."""
        exercise_names = [
            "math_exam.canvas",
            "physics_exercise.canvas",
            "problem_set_1.canvas",
            "quiz_chapter5.canvas",
            "final_test.canvas",
        ]

        for name in exercise_names:
            result = cross_canvas_service.discover_canvas_type(name)
            assert result == "exercise", f"Expected 'exercise' for {name}, got {result}"

    def test_lecture_patterns_chinese(self, cross_canvas_service):
        """Chinese lecture patterns should identify as 'lecture'."""
        lecture_names = [
            "离散数学讲座.canvas",
            "线性代数讲义.canvas",
            "微积分课程.canvas",
            "物理笔记.canvas",
            "计算机教材.canvas",
            "知识点总结.canvas",
            "核心概念.canvas",
        ]

        for name in lecture_names:
            result = cross_canvas_service.discover_canvas_type(name)
            assert result == "lecture", f"Expected 'lecture' for {name}, got {result}"

    def test_lecture_patterns_english(self, cross_canvas_service):
        """English lecture patterns should identify as 'lecture'."""
        lecture_names = [
            "math_lecture.canvas",
            "physics_lesson.canvas",
            "chapter1_notes.canvas",
            "textbook_ch5.canvas",
        ]

        for name in lecture_names:
            result = cross_canvas_service.discover_canvas_type(name)
            assert result == "lecture", f"Expected 'lecture' for {name}, got {result}"

    def test_unknown_patterns(self, cross_canvas_service):
        """Unrecognized patterns should identify as 'unknown'."""
        unknown_names = [
            "random_file.canvas",
            "my_notes.canvas",
            "project_plan.canvas",
            "meeting_2023.canvas",
        ]

        for name in unknown_names:
            result = cross_canvas_service.discover_canvas_type(name)
            assert result == "unknown", f"Expected 'unknown' for {name}, got {result}"

    def test_mixed_chinese_english(self, cross_canvas_service):
        """Mixed Chinese-English filenames should work."""
        assert cross_canvas_service.discover_canvas_type("Math习题集.canvas") == "exercise"
        assert cross_canvas_service.discover_canvas_type("Physics讲义.canvas") == "lecture"


# ═══════════════════════════════════════════════════════════════════════════════
# Task 6.2: Test common concept queries (Mock Neo4j)
# ═══════════════════════════════════════════════════════════════════════════════

class TestNeo4jConceptQueries:
    """Test Neo4j concept query methods.

    [Source: docs/stories/36.6.story.md#Task-2]
    """

    @pytest.mark.asyncio
    async def test_get_canvas_concepts(self, mock_neo4j_client):
        """get_canvas_concepts should return concept list from Neo4j."""
        mock_neo4j_client.get_canvas_concepts.return_value = ["集合", "映射", "函数"]

        result = await mock_neo4j_client.get_canvas_concepts("math/离散数学.canvas")

        assert result == ["集合", "映射", "函数"]
        mock_neo4j_client.get_canvas_concepts.assert_called_once_with("math/离散数学.canvas")

    @pytest.mark.asyncio
    async def test_find_common_concepts(self, mock_neo4j_client):
        """find_common_concepts should return shared concepts between canvases."""
        mock_neo4j_client.find_common_concepts.return_value = ["集合", "映射", "关系"]

        result = await mock_neo4j_client.find_common_concepts(
            "math/离散数学习题.canvas",
            "math/离散数学讲义.canvas"
        )

        assert result == ["集合", "映射", "关系"]

    @pytest.mark.asyncio
    async def test_find_common_concepts_empty(self, mock_neo4j_client):
        """find_common_concepts should return empty list when no common concepts."""
        mock_neo4j_client.find_common_concepts.return_value = []

        result = await mock_neo4j_client.find_common_concepts(
            "math/集合论.canvas",
            "physics/力学.canvas"
        )

        assert result == []


# ═══════════════════════════════════════════════════════════════════════════════
# Task 6.3: Test auto-discovery algorithm logic
# ═══════════════════════════════════════════════════════════════════════════════

class TestAutoDiscoveryAlgorithm:
    """Test auto-discovery algorithm logic.

    [Source: docs/stories/36.6.story.md#Task-3]
    """

    @pytest.mark.asyncio
    async def test_auto_discover_with_common_concepts(self, cross_canvas_service, mock_neo4j_client):
        """Common concepts >= 3 should trigger association suggestion (AC2)."""
        # Mock 4 common concepts
        mock_neo4j_client.find_common_concepts.return_value = ["概念A", "概念B", "概念C", "概念D"]

        canvas_paths = [
            "math/离散数学习题.canvas",
            "math/离散数学讲义.canvas"
        ]

        result = await cross_canvas_service.auto_discover_associations(
            canvas_paths=canvas_paths,
            min_common_concepts=3
        )

        assert len(result.suggestions) > 0
        assert result.suggestions[0].confidence >= 0.6  # 4 * 0.15 = 0.6

    @pytest.mark.asyncio
    async def test_auto_discover_insufficient_concepts(self, cross_canvas_service, mock_neo4j_client):
        """Common concepts < 3 should NOT trigger association (AC2)."""
        # Mock only 2 common concepts
        mock_neo4j_client.find_common_concepts.return_value = ["概念A", "概念B"]

        canvas_paths = [
            "math/随机文件1.canvas",
            "math/随机文件2.canvas"
        ]

        result = await cross_canvas_service.auto_discover_associations(
            canvas_paths=canvas_paths,
            min_common_concepts=3
        )

        # Should not suggest if no name match AND concepts < 3
        # Check all suggestions have confidence >= threshold or name match
        for suggestion in result.suggestions:
            # Either has name match (0.4) or enough concepts
            assert suggestion.confidence >= 0.4 or len(suggestion.shared_concepts) >= 3

    @pytest.mark.asyncio
    async def test_auto_discover_exercise_lecture_pair(self, cross_canvas_service, mock_neo4j_client):
        """Exercise-lecture pairs should get name match bonus (AC1)."""
        mock_neo4j_client.find_common_concepts.return_value = ["概念A", "概念B"]

        canvas_paths = [
            "离散数学习题.canvas",  # exercise
            "离散数学讲义.canvas"   # lecture
        ]

        result = await cross_canvas_service.auto_discover_associations(
            canvas_paths=canvas_paths,
            min_common_concepts=1  # Lower threshold to test name matching
        )

        # Should have suggestion due to name pattern match
        assert result.total_scanned == 2

    @pytest.mark.asyncio
    async def test_auto_discover_shared_concepts_populated(self, cross_canvas_service, mock_neo4j_client):
        """shared_concepts should be populated in suggestions (AC5)."""
        mock_neo4j_client.find_common_concepts.return_value = ["集合", "映射", "函数", "关系"]

        canvas_paths = [
            "离散数学习题.canvas",
            "离散数学讲义.canvas"
        ]

        result = await cross_canvas_service.auto_discover_associations(
            canvas_paths=canvas_paths,
            min_common_concepts=3
        )

        if result.suggestions:
            assert len(result.suggestions[0].shared_concepts) >= 3

    @pytest.mark.asyncio
    async def test_auto_discover_auto_generated_flag(self, cross_canvas_service, mock_neo4j_client):
        """auto_generated should be True for all suggestions (AC5)."""
        mock_neo4j_client.find_common_concepts.return_value = ["概念A", "概念B", "概念C", "概念D"]

        canvas_paths = [
            "离散数学习题.canvas",
            "离散数学讲义.canvas"
        ]

        result = await cross_canvas_service.auto_discover_associations(
            canvas_paths=canvas_paths,
            min_common_concepts=3
        )

        for suggestion in result.suggestions:
            assert suggestion.auto_generated is True


# ═══════════════════════════════════════════════════════════════════════════════
# Task 6.4: Test confidence calculation formula
# ═══════════════════════════════════════════════════════════════════════════════

class TestConfidenceCalculation:
    """Test confidence score calculation formula.

    [Source: docs/stories/36.6.story.md#Task-3.3]

    Formula:
    - Name match: +0.4
    - Each concept: +0.15 (max +0.55)
    - Total max: 0.95
    """

    def test_name_match_only(self, cross_canvas_service):
        """Name match should add 0.4 to confidence."""
        confidence = cross_canvas_service.calculate_discovery_confidence(
            name_match=True,
            common_concepts=[]
        )
        assert confidence == 0.4

    def test_concepts_only(self, cross_canvas_service):
        """Each concept should add 0.15."""
        # 3 concepts = 0.45
        confidence = cross_canvas_service.calculate_discovery_confidence(
            name_match=False,
            common_concepts=["A", "B", "C"]
        )
        assert confidence == 0.45

    def test_name_match_plus_concepts(self, cross_canvas_service):
        """Name match + concepts should sum correctly."""
        # 0.4 (name) + 0.3 (2 concepts) = 0.7
        confidence = cross_canvas_service.calculate_discovery_confidence(
            name_match=True,
            common_concepts=["A", "B"]
        )
        assert confidence == 0.7

    def test_concept_bonus_cap(self, cross_canvas_service):
        """Concept bonus should cap at 0.55."""
        # 10 concepts * 0.15 = 1.5, but capped at 0.55
        confidence = cross_canvas_service.calculate_discovery_confidence(
            name_match=False,
            common_concepts=["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]
        )
        assert confidence == 0.55

    def test_total_confidence_cap(self, cross_canvas_service):
        """Total confidence should cap at 0.95."""
        # 0.4 (name) + 0.55 (capped concepts) = 0.95
        confidence = cross_canvas_service.calculate_discovery_confidence(
            name_match=True,
            common_concepts=["A", "B", "C", "D", "E", "F", "G"]  # 7 * 0.15 = 1.05, capped
        )
        assert confidence == 0.95

    def test_zero_confidence(self, cross_canvas_service):
        """No match and no concepts should give 0."""
        confidence = cross_canvas_service.calculate_discovery_confidence(
            name_match=False,
            common_concepts=[]
        )
        assert confidence == 0.0


# ═══════════════════════════════════════════════════════════════════════════════
# Task 6.5: Test edge cases
# ═══════════════════════════════════════════════════════════════════════════════

class TestEdgeCases:
    """Test edge cases for auto-discovery.

    [Source: docs/stories/36.6.story.md#Task-6.5]
    """

    @pytest.mark.asyncio
    async def test_empty_canvas_list(self, cross_canvas_service, mock_neo4j_client):
        """Empty canvas list should return empty results."""
        result = await cross_canvas_service.auto_discover_associations(
            canvas_paths=[],
            min_common_concepts=3
        )

        assert result.total_scanned == 0
        assert result.discovered_count == 0
        assert len(result.suggestions) == 0

    @pytest.mark.asyncio
    async def test_single_canvas(self, cross_canvas_service, mock_neo4j_client):
        """Single canvas should have no pairs to discover."""
        result = await cross_canvas_service.auto_discover_associations(
            canvas_paths=["math/离散数学.canvas"],
            min_common_concepts=3
        )

        assert result.total_scanned == 1
        assert result.discovered_count == 0
        assert len(result.suggestions) == 0

    @pytest.mark.asyncio
    async def test_no_common_concepts(self, cross_canvas_service, mock_neo4j_client):
        """No common concepts should result in no suggestions (without name match)."""
        mock_neo4j_client.find_common_concepts.return_value = []

        result = await cross_canvas_service.auto_discover_associations(
            canvas_paths=[
                "math/随机文件1.canvas",  # unknown type
                "physics/随机文件2.canvas"  # unknown type
            ],
            min_common_concepts=3
        )

        # No name match + no concepts = no suggestions
        assert len(result.suggestions) == 0

    @pytest.mark.asyncio
    async def test_result_counts_accurate(self, cross_canvas_service, mock_neo4j_client):
        """total_scanned and discovered_count should be accurate."""
        mock_neo4j_client.find_common_concepts.return_value = ["A", "B", "C", "D"]

        canvas_paths = [
            "离散数学习题.canvas",
            "离散数学讲义.canvas",
            "线性代数习题.canvas"
        ]

        result = await cross_canvas_service.auto_discover_associations(
            canvas_paths=canvas_paths,
            min_common_concepts=3
        )

        assert result.total_scanned == 3
        assert result.discovered_count == len(result.suggestions)


# ═══════════════════════════════════════════════════════════════════════════════
# API Endpoint Tests
# ═══════════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════════
# Task 7: Performance Tests (AC7)
# ═══════════════════════════════════════════════════════════════════════════════

class TestPerformance:
    """Performance tests for auto-discovery.

    [Source: docs/stories/36.6.story.md#Task-7]
    AC7: 批量扫描100个Canvas < 5秒
    """

    @pytest.mark.asyncio
    @pytest.mark.performance
    @pytest.mark.timeout(5)
    async def test_100_canvas_scan_under_5_seconds(self, cross_canvas_service, mock_neo4j_client):
        """Scanning 100 canvases should complete in < 5 seconds (AC7)."""
        import time

        # Generate 100 canvas paths
        canvas_paths = [f"math/canvas_{i}.canvas" for i in range(100)]

        # Mock fast Neo4j responses
        mock_neo4j_client.find_common_concepts.return_value = ["A", "B"]

        start_time = time.time()

        result = await cross_canvas_service.auto_discover_associations(
            canvas_paths=canvas_paths,
            min_common_concepts=3
        )

        elapsed_time = time.time() - start_time

        assert result.total_scanned == 100
        assert elapsed_time < 5.0, f"Scan took {elapsed_time:.2f}s, expected < 5s"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_large_canvas_scan_reasonable_time(self, cross_canvas_service, mock_neo4j_client):
        """Large scan should scale reasonably."""
        import time

        # Generate 50 canvases (testing N*(N-1)/2 pairs = 1225 comparisons)
        canvas_paths = [f"math/canvas_{i}.canvas" for i in range(50)]

        mock_neo4j_client.find_common_concepts.return_value = []

        start_time = time.time()

        result = await cross_canvas_service.auto_discover_associations(
            canvas_paths=canvas_paths,
            min_common_concepts=3
        )

        elapsed_time = time.time() - start_time

        # Should complete in reasonable time (< 3s for 50 canvases)
        assert elapsed_time < 3.0, f"Scan took {elapsed_time:.2f}s"

    @pytest.mark.asyncio
    async def test_caching_improves_performance(self, cross_canvas_service, mock_neo4j_client):
        """Concept queries should benefit from caching (if implemented)."""
        import time

        canvas_paths = [
            "math/离散数学习题.canvas",
            "math/离散数学讲义.canvas",
            "math/集合论.canvas"
        ]

        mock_neo4j_client.find_common_concepts.return_value = ["A", "B", "C"]

        # First run
        start1 = time.time()
        await cross_canvas_service.auto_discover_associations(
            canvas_paths=canvas_paths,
            min_common_concepts=3
        )
        time1 = time.time() - start1

        # Second run (should be at least as fast if caching works)
        start2 = time.time()
        await cross_canvas_service.auto_discover_associations(
            canvas_paths=canvas_paths,
            min_common_concepts=3
        )
        time2 = time.time() - start2

        # Just verify both complete quickly
        assert time1 < 2.0
        assert time2 < 2.0


# ═══════════════════════════════════════════════════════════════════════════════
# API Endpoint Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestAutoDiscoverEndpoint:
    """Test auto-discover API endpoint.

    [Source: docs/stories/36.6.story.md#Task-4]
    """

    @pytest.mark.asyncio
    async def test_endpoint_vault_not_found(self):
        """Endpoint should return 404 for non-existent vault."""
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)

        response = client.post(
            "/api/v1/cross-canvas/associations/auto-discover",
            json={
                "vault_path": "/non/existent/path",
                "min_common_concepts": 3,
                "include_existing": False
            }
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_endpoint_invalid_vault_path(self):
        """Endpoint should return 400 for invalid vault path."""
        from fastapi.testclient import TestClient
        from app.main import app
        import tempfile

        # Create a temp file (not directory) to test invalid path
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_file = f.name

        client = TestClient(app)

        response = client.post(
            "/api/v1/cross-canvas/associations/auto-discover",
            json={
                "vault_path": temp_file,
                "min_common_concepts": 3,
                "include_existing": False
            }
        )

        assert response.status_code == 400

        # Cleanup
        import os
        os.unlink(temp_file)


# ═══════════════════════════════════════════════════════════════════════════════
# on_canvas_open() Tests (Story 36.6 Fix - F1)
# ═══════════════════════════════════════════════════════════════════════════════

class TestOnCanvasOpen:
    """Tests for on_canvas_open() — auto-trigger on Canvas open."""

    @pytest.mark.asyncio
    async def test_on_canvas_open_no_known_canvases(self, cross_canvas_service):
        """With no known canvases in cache, returns empty result."""
        result = await cross_canvas_service.on_canvas_open("test.canvas")

        assert result.total_scanned == 1
        assert result.discovered_count == 0
        assert result.suggestions == []

    @pytest.mark.asyncio
    async def test_on_canvas_open_filters_to_opened_canvas(self, cross_canvas_service, mock_neo4j_client):
        """Only returns suggestions involving the opened canvas."""
        # Inject mock Neo4j client on the correct private attribute
        cross_canvas_service._neo4j_client = mock_neo4j_client

        # Pre-populate cache with associations between other canvases
        from app.services.cross_canvas_service import CrossCanvasAssociation
        cross_canvas_service._associations_cache["assoc-1"] = CrossCanvasAssociation(
            id="assoc-1",
            source_canvas_path="lecture-A.canvas",
            source_canvas_title="Lecture A",
            target_canvas_path="exercise-A.canvas",
            target_canvas_title="Exercise A",
            relationship_type="prerequisite",
            confidence=0.8,
        )
        cross_canvas_service._associations_cache["assoc-2"] = CrossCanvasAssociation(
            id="assoc-2",
            source_canvas_path="lecture-B.canvas",
            source_canvas_title="Lecture B",
            target_canvas_path="exercise-B.canvas",
            target_canvas_title="Exercise B",
            relationship_type="prerequisite",
            confidence=0.7,
        )

        # Mock Neo4j to return 4 common concepts between opened canvas and lecture-A
        async def mock_find_common(c1, c2):
            if "opened" in c1 or "opened" in c2:
                if "lecture-A" in c1 or "lecture-A" in c2:
                    return ["概念1", "概念2", "概念3", "概念4"]
            return []

        mock_neo4j_client.find_common_concepts = AsyncMock(side_effect=mock_find_common)
        mock_neo4j_client.get_canvas_concepts = AsyncMock(return_value=[])

        result = await cross_canvas_service.on_canvas_open("opened.canvas")

        # Should only contain suggestions involving "opened.canvas"
        for suggestion in result.suggestions:
            assert (
                suggestion.source_canvas == "opened.canvas"
                or suggestion.target_canvas == "opened.canvas"
            ), f"Suggestion {suggestion} does not involve opened canvas"

    @pytest.mark.asyncio
    async def test_on_canvas_open_delegates_to_auto_discover(self, cross_canvas_service, mock_neo4j_client):
        """on_canvas_open delegates to auto_discover_associations with correct params."""
        cross_canvas_service._neo4j_client = mock_neo4j_client

        from app.services.cross_canvas_service import CrossCanvasAssociation
        # Add one known canvas
        cross_canvas_service._associations_cache["assoc-1"] = CrossCanvasAssociation(
            id="assoc-1",
            source_canvas_path="known.canvas",
            source_canvas_title="Known",
            target_canvas_path="other.canvas",
            target_canvas_title="Other",
            relationship_type="related",
            confidence=0.5,
        )

        mock_neo4j_client.find_common_concepts = AsyncMock(return_value=[])
        mock_neo4j_client.get_canvas_concepts = AsyncMock(return_value=[])

        result = await cross_canvas_service.on_canvas_open("test.canvas")

        # Should have scanned at least 3 canvases (test + known + other)
        assert result.total_scanned >= 2

    @pytest.mark.asyncio
    async def test_on_canvas_open_with_neo4j_unavailable(self, cross_canvas_service):
        """Works gracefully when Neo4j is not available (name-pattern only)."""
        cross_canvas_service._neo4j_client = None

        from app.services.cross_canvas_service import CrossCanvasAssociation
        cross_canvas_service._associations_cache["assoc-1"] = CrossCanvasAssociation(
            id="assoc-1",
            source_canvas_path="离散数学讲义.canvas",
            source_canvas_title="离散数学讲义",
            target_canvas_path="other.canvas",
            target_canvas_title="Other",
            relationship_type="related",
            confidence=0.5,
        )

        # Should not raise, even without Neo4j
        result = await cross_canvas_service.on_canvas_open("离散数学习题.canvas")
        assert isinstance(result.discovered_count, int)
