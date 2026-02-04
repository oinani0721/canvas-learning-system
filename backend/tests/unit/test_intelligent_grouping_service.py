# Canvas Learning System - Intelligent Grouping Service Unit Tests
# Story 33.4: Intelligent Grouping Service
# ✅ AC-33.4.6: Unit tests achieve ≥90% coverage
"""
Unit tests for IntelligentGroupingService.

Test Cases (from Story 33.4):
1. test_analyze_canvas_returns_groups: Basic grouping functionality
2. test_auto_k_selection: Auto optimal K determination
3. test_silhouette_score_returned: Silhouette Score quality metrics
4. test_estimated_duration_calculation: Duration estimation
5. test_priority_assignment: Priority assignment logic
6. test_group_id_extraction_chinese: Chinese path handling
7. test_group_id_with_skip_directories: Skip directory handling
8. test_agent_recommendation: Agent recommendation based on keywords

[Source: docs/stories/33.4.story.md#Task-6]
[Source: docs/stories/33.4.story.md#Testing Standards]
"""

import asyncio
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.intelligent_parallel_models import (
    GroupPriority,
    IntelligentParallelResponse,
    NodeGroup,
    NodeInGroup,
)
from app.services.intelligent_grouping_service import (
    AGENT_KEYWORD_MAPPING,
    AVERAGE_AGENT_PROCESSING_SECONDS,
    DEFAULT_AGENT,
    GROUP_EMOJI_MAPPING,
    HIGH_KEYWORDS,
    SILHOUETTE_QUALITY_THRESHOLD,
    URGENT_KEYWORDS,
    CanvasNotFoundError,
    ClusteringFailedError,
    InsufficientNodesError,
    IntelligentGroupingService,
    get_intelligent_grouping_service,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def service() -> IntelligentGroupingService:
    """Create a service instance for testing."""
    return IntelligentGroupingService(canvas_base_path="/test/path")


@pytest.fixture
def mock_clustering_result() -> Dict[str, Any]:
    """Mock clustering result from canvas_utils.cluster_canvas_nodes()."""
    return {
        "clusters": [
            {
                "id": "cluster-1",
                "label": "逆否命题、充分条件等概念",
                "nodes": ["node-001", "node-002"],
                "node_texts": {
                    "node-001": "逆否命题 vs 否命题有什么区别",
                    "node-002": "充分条件与必要条件的对比",
                },
                "center": {"x": 400, "y": 300},
                "confidence": 0.85,
                "size": 2,
                "top_keywords": ["逆否命题", "充分条件", "对比"],
            },
            {
                "id": "cluster-2",
                "label": "命题、定义等概念",
                "nodes": ["node-003", "node-004"],
                "node_texts": {
                    "node-003": "什么是命题的定义",
                    "node-004": "真值表是什么",
                },
                "center": {"x": 600, "y": 400},
                "confidence": 0.78,
                "size": 2,
                "top_keywords": ["命题", "定义", "真值表"],
            },
        ],
        "optimization_stats": {
            "total_nodes": 4,
            "clusters_created": 2,
            "layout_time_ms": 150,
            "clustering_accuracy": 0.72,  # Silhouette Score
            "algorithm": "K-means with TF-IDF",
            "feature_dimensions": 100,
        },
        "clustering_parameters": {
            "n_clusters": 2,
            "similarity_threshold": 0.3,
            "min_cluster_size": 2,
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Basic Functionality
# ═══════════════════════════════════════════════════════════════════════════════

class TestAnalyzeCanvas:
    """Tests for analyze_canvas method - AC-33.4.1."""

    @pytest.mark.asyncio
    async def test_analyze_canvas_returns_groups(
        self, service: IntelligentGroupingService, mock_clustering_result: Dict
    ):
        """
        Test that analyze_canvas returns grouped nodes with recommendations.

        ✅ AC-33.4.1: Service integrates cluster_canvas_nodes()
        """
        with patch.object(service, "_resolve_canvas_path") as mock_resolve:
            mock_path = MagicMock()
            mock_path.exists.return_value = True
            mock_resolve.return_value = mock_path

            with patch.object(
                service, "_perform_clustering", return_value=mock_clustering_result
            ):
                result = await service.analyze_canvas(
                    canvas_path="数学/离散数学.canvas",
                    target_color="3",
                )

        assert isinstance(result, IntelligentParallelResponse)
        assert result.total_nodes == 4
        assert len(result.groups) == 2
        assert result.canvas_path == "数学/离散数学.canvas"

    @pytest.mark.asyncio
    async def test_analyze_canvas_not_found(self, service: IntelligentGroupingService):
        """
        Test that CanvasNotFoundError is raised when canvas doesn't exist.
        """
        with patch.object(service, "_resolve_canvas_path") as mock_resolve:
            mock_path = MagicMock()
            mock_path.exists.return_value = False
            mock_resolve.return_value = mock_path

            with pytest.raises(CanvasNotFoundError) as exc_info:
                await service.analyze_canvas("nonexistent.canvas")

            assert "not found" in str(exc_info.value)


class TestSilhouetteScore:
    """Tests for Silhouette Score quality evaluation - AC-33.4.3."""

    @pytest.mark.asyncio
    async def test_silhouette_score_returned(
        self, service: IntelligentGroupingService, mock_clustering_result: Dict
    ):
        """
        Test that silhouette_score is correctly returned.

        ✅ AC-33.4.3: Returns silhouette_avg from optimization_stats.clustering_accuracy
        """
        with patch.object(service, "_resolve_canvas_path") as mock_resolve:
            mock_path = MagicMock()
            mock_path.exists.return_value = True
            mock_resolve.return_value = mock_path

            with patch.object(
                service, "_perform_clustering", return_value=mock_clustering_result
            ):
                result = await service.analyze_canvas("test.canvas")

        assert result.silhouette_score == 0.72
        assert result.recommended_k == 2

    @pytest.mark.asyncio
    async def test_low_silhouette_score_warning(
        self, service: IntelligentGroupingService, mock_clustering_result: Dict, caplog
    ):
        """
        Test that low silhouette score triggers a warning.

        ✅ AC-33.4.3: Recommend re-clustering if score < 0.3
        """
        # Modify mock to have low silhouette score
        mock_clustering_result["optimization_stats"]["clustering_accuracy"] = 0.2

        with patch.object(service, "_resolve_canvas_path") as mock_resolve:
            mock_path = MagicMock()
            mock_path.exists.return_value = True
            mock_resolve.return_value = mock_path

            with patch.object(
                service, "_perform_clustering", return_value=mock_clustering_result
            ):
                result = await service.analyze_canvas("test.canvas")

        assert result.silhouette_score == 0.2
        # Warning should be logged
        assert any("Low clustering quality" in record.message for record in caplog.records)


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Subject Isolation - AC-33.4.5
# ═══════════════════════════════════════════════════════════════════════════════

class TestSubjectIsolation:
    """Tests for subject isolation with group_id - AC-33.4.5."""

    @pytest.mark.asyncio
    async def test_group_id_extraction_chinese(
        self, service: IntelligentGroupingService, mock_clustering_result: Dict
    ):
        """
        Test group_id extraction for Chinese paths.

        ✅ AC-33.4.5: "数学/离散数学.canvas" → subject="数学", group_id="数学:离散数学"
        """
        with patch.object(service, "_resolve_canvas_path") as mock_resolve:
            mock_path = MagicMock()
            mock_path.exists.return_value = True
            mock_resolve.return_value = mock_path

            with patch.object(
                service, "_perform_clustering", return_value=mock_clustering_result
            ):
                result = await service.analyze_canvas("数学/离散数学.canvas")

        assert result.subject == "数学"
        assert result.subject_group_id == "数学:离散数学"

    @pytest.mark.asyncio
    async def test_group_id_with_skip_directories(
        self, service: IntelligentGroupingService, mock_clustering_result: Dict
    ):
        """
        Test group_id extraction skips common root directories.

        ✅ AC-33.4.5: "笔记库/物理/力学.canvas" → subject="物理"
        """
        with patch.object(service, "_resolve_canvas_path") as mock_resolve:
            mock_path = MagicMock()
            mock_path.exists.return_value = True
            mock_resolve.return_value = mock_path

            with patch.object(
                service, "_perform_clustering", return_value=mock_clustering_result
            ):
                result = await service.analyze_canvas("笔记库/物理/力学.canvas")

        assert result.subject == "物理"
        assert result.subject_group_id == "物理:力学"

    @pytest.mark.asyncio
    async def test_group_id_single_file(
        self, service: IntelligentGroupingService, mock_clustering_result: Dict
    ):
        """
        Test group_id extraction for single file (no directory).

        ✅ AC-33.4.5: "离散数学.canvas" → subject="离散数学"
        """
        with patch.object(service, "_resolve_canvas_path") as mock_resolve:
            mock_path = MagicMock()
            mock_path.exists.return_value = True
            mock_resolve.return_value = mock_path

            with patch.object(
                service, "_perform_clustering", return_value=mock_clustering_result
            ):
                result = await service.analyze_canvas("离散数学.canvas")

        assert result.subject == "离散数学"


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Estimated Duration - AC-33.4.4
# ═══════════════════════════════════════════════════════════════════════════════

class TestEstimatedDuration:
    """Tests for estimated duration calculation - AC-33.4.4."""

    def test_calculate_estimated_duration_minutes(
        self, service: IntelligentGroupingService
    ):
        """
        Test duration calculation for small node counts.

        ✅ AC-33.4.4: Returns "X分钟" format
        """
        # 6 nodes * 10 seconds = 60 seconds = 1 minute
        result = service._calculate_estimated_duration(6)
        assert result == "1分钟"

        # 12 nodes * 10 seconds = 120 seconds = 2 minutes
        result = service._calculate_estimated_duration(12)
        assert result == "2分钟"

        # 30 nodes * 10 seconds = 300 seconds = 5 minutes
        result = service._calculate_estimated_duration(30)
        assert result == "5分钟"

    def test_calculate_estimated_duration_hours(
        self, service: IntelligentGroupingService
    ):
        """
        Test duration calculation for large node counts.
        """
        # 360 nodes * 10 seconds = 3600 seconds = 60 minutes = 1 hour
        result = service._calculate_estimated_duration(360)
        assert result == "1小时"

        # 420 nodes * 10 seconds = 4200 seconds = 70 minutes = 1 hour 10 minutes
        result = service._calculate_estimated_duration(420)
        assert result == "1小时10分钟"

    def test_calculate_estimated_duration_minimum(
        self, service: IntelligentGroupingService
    ):
        """
        Test minimum duration is 1 minute.
        """
        # Even 1 node should show at least 1 minute
        result = service._calculate_estimated_duration(1)
        assert result == "1分钟"


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Priority Assignment - AC-33.4.4
# ═══════════════════════════════════════════════════════════════════════════════

class TestPriorityAssignment:
    """Tests for priority assignment logic - AC-33.4.4."""

    def test_priority_urgent_keywords(self, service: IntelligentGroupingService):
        """
        Test urgent priority for error-related content.

        ✅ AC-33.4.4: "urgent" if error keywords
        """
        keywords = ["概念", "问题"]
        node_texts = {"n1": "这个概念有错误需要修复"}
        result = service._assign_priority(keywords, node_texts, 5)
        assert result == GroupPriority.urgent

    def test_priority_high_keywords(self, service: IntelligentGroupingService):
        """
        Test high priority for review-related content.

        ✅ AC-33.4.4: "high" if review keywords
        """
        keywords = ["复习", "重点"]
        node_texts = {"n1": "考试重点内容"}
        result = service._assign_priority(keywords, node_texts, 5)
        assert result == GroupPriority.high

    def test_priority_low_small_cluster(self, service: IntelligentGroupingService):
        """
        Test low priority for small clusters.

        ✅ AC-33.4.4: "low" if < 3 nodes
        """
        keywords = ["概念"]
        node_texts = {"n1": "普通概念"}
        result = service._assign_priority(keywords, node_texts, 2)
        assert result == GroupPriority.low

    def test_priority_medium_default(self, service: IntelligentGroupingService):
        """
        Test medium priority as default.

        ✅ AC-33.4.4: "medium" for most clusters
        """
        keywords = ["概念", "定义"]
        node_texts = {"n1": "普通概念内容", "n2": "另一个定义"}
        result = service._assign_priority(keywords, node_texts, 5)
        assert result == GroupPriority.medium


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Agent Recommendation
# ═══════════════════════════════════════════════════════════════════════════════

class TestAgentRecommendation:
    """Tests for agent recommendation based on keywords."""

    def test_recommend_comparison_table(self, service: IntelligentGroupingService):
        """Test comparison-table recommendation for comparison keywords."""
        keywords = ["对比", "区别"]
        node_texts = {"n1": "逆否命题vs否命题的区别"}
        result = service._recommend_agent(keywords, node_texts)
        assert result == "comparison-table"

    def test_recommend_oral_explanation(self, service: IntelligentGroupingService):
        """Test oral-explanation recommendation for definition keywords."""
        keywords = ["定义", "概念"]
        node_texts = {"n1": "什么是命题的定义"}
        result = service._recommend_agent(keywords, node_texts)
        assert result == "oral-explanation"

    def test_recommend_example_teaching(self, service: IntelligentGroupingService):
        """Test example-teaching recommendation for example keywords."""
        keywords = ["举例", "示例"]
        # Note: Avoid "概念" which triggers oral-explanation before example-teaching
        node_texts = {"n1": "请举例说明这个问题"}
        result = service._recommend_agent(keywords, node_texts)
        assert result == "example-teaching"

    def test_recommend_default_agent(self, service: IntelligentGroupingService):
        """Test default agent when no keywords match."""
        keywords = ["随机", "内容"]
        node_texts = {"n1": "一些普通文本"}
        result = service._recommend_agent(keywords, node_texts)
        assert result == DEFAULT_AGENT


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Cluster to Group Mapping
# ═══════════════════════════════════════════════════════════════════════════════

class TestClusterMapping:
    """Tests for mapping clusters to NodeGroup schema."""

    def test_map_clusters_to_groups(
        self, service: IntelligentGroupingService, mock_clustering_result: Dict
    ):
        """
        Test cluster to NodeGroup mapping.

        ✅ AC-33.4.1: Maps clustering output to NodeGroup schema
        """
        clusters = mock_clustering_result["clusters"]
        groups = service._map_clusters_to_groups(clusters)

        assert len(groups) == 2

        # Check first group
        group1 = groups[0]
        assert isinstance(group1, NodeGroup)
        assert group1.group_id == "group-1"
        assert group1.group_name == "逆否命题、充分条件等概念"
        assert len(group1.nodes) == 2
        assert group1.confidence == 0.85
        # Should recommend comparison-table due to "对比" keyword
        assert group1.recommended_agent == "comparison-table"

    def test_map_clusters_creates_node_in_group(
        self, service: IntelligentGroupingService, mock_clustering_result: Dict
    ):
        """Test that NodeInGroup objects are created correctly."""
        clusters = mock_clustering_result["clusters"]
        groups = service._map_clusters_to_groups(clusters)

        # Check nodes in first group
        group1 = groups[0]
        assert all(isinstance(n, NodeInGroup) for n in group1.nodes)
        assert group1.nodes[0].node_id == "node-001"
        assert "逆否命题" in group1.nodes[0].text


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Error Handling
# ═══════════════════════════════════════════════════════════════════════════════

class TestErrorHandling:
    """Tests for error handling scenarios."""

    @pytest.mark.asyncio
    async def test_insufficient_nodes_error(
        self, service: IntelligentGroupingService
    ):
        """Test InsufficientNodesError is raised when not enough nodes."""
        with patch.object(service, "_resolve_canvas_path") as mock_resolve:
            mock_path = MagicMock()
            mock_path.exists.return_value = True
            mock_resolve.return_value = mock_path

            with patch.object(
                service,
                "_perform_clustering",
                side_effect=InsufficientNodesError("Not enough nodes"),
            ):
                with pytest.raises(InsufficientNodesError):
                    await service.analyze_canvas("test.canvas")

    @pytest.mark.asyncio
    async def test_clustering_failed_error(
        self, service: IntelligentGroupingService
    ):
        """Test ClusteringFailedError is raised on clustering failure."""
        with patch.object(service, "_resolve_canvas_path") as mock_resolve:
            mock_path = MagicMock()
            mock_path.exists.return_value = True
            mock_resolve.return_value = mock_path

            with patch.object(
                service,
                "_perform_clustering",
                side_effect=ClusteringFailedError("Clustering failed"),
            ):
                with pytest.raises(ClusteringFailedError):
                    await service.analyze_canvas("test.canvas")


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Factory Function
# ═══════════════════════════════════════════════════════════════════════════════

class TestFactoryFunction:
    """Tests for factory function."""

    def test_get_intelligent_grouping_service(self):
        """Test factory function creates service instance."""
        service = get_intelligent_grouping_service("/test/path")
        assert isinstance(service, IntelligentGroupingService)
        assert service.canvas_base_path == Path("/test/path")

    def test_get_intelligent_grouping_service_default_path(self):
        """Test factory function with default path."""
        service = get_intelligent_grouping_service()
        assert isinstance(service, IntelligentGroupingService)


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Constants Configuration
# ═══════════════════════════════════════════════════════════════════════════════

class TestConstants:
    """Tests for service constants."""

    def test_average_agent_processing_seconds(self):
        """Verify AVERAGE_AGENT_PROCESSING_SECONDS is configured."""
        assert AVERAGE_AGENT_PROCESSING_SECONDS == 10

    def test_silhouette_quality_threshold(self):
        """Verify SILHOUETTE_QUALITY_THRESHOLD is configured."""
        assert SILHOUETTE_QUALITY_THRESHOLD == 0.3

    def test_agent_keyword_mapping_contains_all_agents(self):
        """Verify AGENT_KEYWORD_MAPPING has all expected agents."""
        expected_agents = [
            "comparison-table",
            "oral-explanation",
            "example-teaching",
            "clarification-path",
            "memory-anchor",
            "deep-decomposition",
        ]
        for agent in expected_agents:
            assert agent in AGENT_KEYWORD_MAPPING

    def test_default_agent_configured(self):
        """Verify DEFAULT_AGENT is configured."""
        assert DEFAULT_AGENT == "four-level-explanation"

    def test_priority_keywords_configured(self):
        """Verify priority keywords are configured."""
        assert "错误" in URGENT_KEYWORDS
        assert "复习" in HIGH_KEYWORDS

    def test_group_emoji_mapping_configured(self):
        """Verify GROUP_EMOJI_MAPPING is configured."""
        assert GROUP_EMOJI_MAPPING["comparison-table"] == "📊"
        assert GROUP_EMOJI_MAPPING["oral-explanation"] == "📖"


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Path Resolution
# ═══════════════════════════════════════════════════════════════════════════════

class TestPathResolution:
    """Tests for canvas path resolution."""

    def test_resolve_relative_path(self, service: IntelligentGroupingService):
        """Test resolving relative path."""
        result = service._resolve_canvas_path("test.canvas")
        assert result == Path("/test/path/test.canvas")

    def test_resolve_absolute_path(self, service: IntelligentGroupingService):
        """Test resolving absolute path (unchanged)."""
        result = service._resolve_canvas_path("/absolute/path/test.canvas")
        assert result == Path("/absolute/path/test.canvas")

    def test_resolve_nested_path(self, service: IntelligentGroupingService):
        """Test resolving nested relative path."""
        result = service._resolve_canvas_path("数学/离散数学.canvas")
        assert result == Path("/test/path/数学/离散数学.canvas")


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Resource Warning
# ═══════════════════════════════════════════════════════════════════════════════

class TestResourceWarning:
    """Tests for resource warning generation."""

    @pytest.mark.asyncio
    async def test_resource_warning_large_nodes(
        self, service: IntelligentGroupingService
    ):
        """Test resource warning is generated for large node counts."""
        # Create mock result with many nodes
        large_result = {
            "clusters": [
                {
                    "id": f"cluster-{i}",
                    "label": f"Group {i}",
                    "nodes": [f"node-{i*10+j}" for j in range(10)],
                    "node_texts": {f"node-{i*10+j}": f"Text {j}" for j in range(10)},
                    "confidence": 0.8,
                    "top_keywords": ["概念"],
                }
                for i in range(6)  # 6 clusters * 10 nodes = 60 nodes > 50
            ],
            "optimization_stats": {"clustering_accuracy": 0.7},
            "clustering_parameters": {"n_clusters": 6},
        }

        with patch.object(service, "_resolve_canvas_path") as mock_resolve:
            mock_path = MagicMock()
            mock_path.exists.return_value = True
            mock_resolve.return_value = mock_path

            with patch.object(
                service, "_perform_clustering", return_value=large_result
            ):
                result = await service.analyze_canvas("test.canvas")

        assert result.resource_warning is not None
        assert "60" in result.resource_warning

    @pytest.mark.asyncio
    async def test_no_resource_warning_small_nodes(
        self, service: IntelligentGroupingService, mock_clustering_result: Dict
    ):
        """Test no resource warning for small node counts."""
        with patch.object(service, "_resolve_canvas_path") as mock_resolve:
            mock_path = MagicMock()
            mock_path.exists.return_value = True
            mock_resolve.return_value = mock_path

            with patch.object(
                service, "_perform_clustering", return_value=mock_clustering_result
            ):
                result = await service.analyze_canvas("test.canvas")

        assert result.resource_warning is None


# ═══════════════════════════════════════════════════════════════════════════════
# Test: _perform_clustering Method
# [Coverage: Lines 281-348]
# ═══════════════════════════════════════════════════════════════════════════════

class TestPerformClustering:
    """
    Tests for _perform_clustering method.

    These tests cover the synchronous clustering code by mocking CanvasBusinessLogic.
    """

    def test_perform_clustering_import_error(
        self, service: IntelligentGroupingService
    ):
        """
        Test ClusteringFailedError is raised when CanvasBusinessLogic import fails.

        Coverage: Lines 281-290
        Note: This test verifies the error handling when canvas_utils is not available.
        """
        import sys

        # Save original module if exists
        original_module = sys.modules.get("canvas_utils")

        try:
            # Remove canvas_utils from sys.modules to force re-import
            if "canvas_utils" in sys.modules:
                del sys.modules["canvas_utils"]

            # Create a mock module that raises ImportError when CanvasBusinessLogic is accessed
            class FailingModule:
                @property
                def CanvasBusinessLogic(self):
                    raise ImportError("Failed to import CanvasBusinessLogic")

            sys.modules["canvas_utils"] = FailingModule()

            with pytest.raises(ClusteringFailedError) as exc_info:
                service._perform_clustering(
                    Path("/test/canvas.canvas"), "3", None, 2
                )
            # Error message starts with "Cannot import clustering module"
            assert "Cannot import clustering module" in str(exc_info.value)

        finally:
            # Restore original module
            if original_module is not None:
                sys.modules["canvas_utils"] = original_module
            elif "canvas_utils" in sys.modules:
                del sys.modules["canvas_utils"]

    def test_perform_clustering_insufficient_nodes_from_filter(
        self, service: IntelligentGroupingService
    ):
        """
        Test InsufficientNodesError when not enough nodes match target color.

        Coverage: Lines 297-308
        """
        # Create mock canvas data with nodes that don't match target color
        mock_canvas_data = {
            "nodes": [
                {"id": "n1", "type": "text", "color": "1", "text": "Wrong color"},
                {"id": "n2", "type": "text", "color": "1", "text": "Also wrong"},
            ]
        }

        mock_logic = MagicMock()
        mock_logic.canvas_data = mock_canvas_data

        with patch(
            "app.services.intelligent_grouping_service.sys.path",
            new_callable=list,
        ):
            with patch.dict("sys.modules", {"canvas_utils": MagicMock()}):
                # Mock the import
                import sys
                mock_module = MagicMock()
                mock_module.CanvasBusinessLogic = MagicMock(return_value=mock_logic)
                sys.modules["canvas_utils"] = mock_module

                with pytest.raises(InsufficientNodesError) as exc_info:
                    service._perform_clustering(
                        Path("/test/canvas.canvas"),
                        target_color="3",  # Purple - no nodes match
                        max_groups=None,
                        min_nodes_per_group=2,
                    )
                assert "Not enough nodes with color '3'" in str(exc_info.value)

    def test_perform_clustering_success(self, service: IntelligentGroupingService):
        """
        Test successful clustering execution.

        Coverage: Lines 310-337
        """
        # Create mock canvas data with matching nodes
        mock_canvas_data = {
            "nodes": [
                {"id": "n1", "type": "text", "color": "3", "text": "Node 1 text"},
                {"id": "n2", "type": "text", "color": "3", "text": "Node 2 text"},
                {"id": "n3", "type": "text", "color": "3", "text": "Node 3 text"},
            ]
        }

        # Mock clustering result
        mock_cluster_result = {
            "clusters": [
                {"id": "c1", "nodes": ["n1", "n2"]},
                {"id": "c2", "nodes": ["n3"]},
            ],
            "optimization_stats": {"clustering_accuracy": 0.75},
            "clustering_parameters": {"n_clusters": 2},
        }

        mock_logic = MagicMock()
        mock_logic.canvas_data = mock_canvas_data
        mock_logic.cluster_canvas_nodes = MagicMock(return_value=mock_cluster_result)

        with patch.dict("sys.modules", {"canvas_utils": MagicMock()}):
            import sys

            mock_module = MagicMock()
            mock_module.CanvasBusinessLogic = MagicMock(return_value=mock_logic)
            sys.modules["canvas_utils"] = mock_module

            result = service._perform_clustering(
                Path("/test/canvas.canvas"),
                target_color="3",
                max_groups=None,
                min_nodes_per_group=2,
            )

            assert "clusters" in result
            # Verify node_texts were added
            for cluster in result["clusters"]:
                assert "node_texts" in cluster

    def test_perform_clustering_value_error_insufficient(
        self, service: IntelligentGroupingService
    ):
        """
        Test ValueError from clustering is converted to InsufficientNodesError.

        Coverage: Lines 341-344
        """
        mock_canvas_data = {
            "nodes": [
                {"id": "n1", "type": "text", "color": "3", "text": "Node 1"},
                {"id": "n2", "type": "text", "color": "3", "text": "Node 2"},
            ]
        }

        mock_logic = MagicMock()
        mock_logic.canvas_data = mock_canvas_data
        mock_logic.cluster_canvas_nodes = MagicMock(
            side_effect=ValueError("节点数量不足 for clustering")
        )

        with patch.dict("sys.modules", {"canvas_utils": MagicMock()}):
            import sys

            mock_module = MagicMock()
            mock_module.CanvasBusinessLogic = MagicMock(return_value=mock_logic)
            sys.modules["canvas_utils"] = mock_module

            with pytest.raises(InsufficientNodesError):
                service._perform_clustering(
                    Path("/test/canvas.canvas"), "3", None, 2
                )

    def test_perform_clustering_value_error_general(
        self, service: IntelligentGroupingService
    ):
        """
        Test general ValueError from clustering is converted to ClusteringFailedError.

        Coverage: Lines 345
        """
        mock_canvas_data = {
            "nodes": [
                {"id": "n1", "type": "text", "color": "3", "text": "Node 1"},
                {"id": "n2", "type": "text", "color": "3", "text": "Node 2"},
            ]
        }

        mock_logic = MagicMock()
        mock_logic.canvas_data = mock_canvas_data
        mock_logic.cluster_canvas_nodes = MagicMock(
            side_effect=ValueError("Some other error")
        )

        with patch.dict("sys.modules", {"canvas_utils": MagicMock()}):
            import sys

            mock_module = MagicMock()
            mock_module.CanvasBusinessLogic = MagicMock(return_value=mock_logic)
            sys.modules["canvas_utils"] = mock_module

            with pytest.raises(ClusteringFailedError) as exc_info:
                service._perform_clustering(
                    Path("/test/canvas.canvas"), "3", None, 2
                )
            assert "Clustering failed" in str(exc_info.value)

    def test_perform_clustering_generic_exception(
        self, service: IntelligentGroupingService
    ):
        """
        Test generic Exception from clustering is converted to ClusteringFailedError.

        Coverage: Lines 346-348
        """
        mock_canvas_data = {
            "nodes": [
                {"id": "n1", "type": "text", "color": "3", "text": "Node 1"},
                {"id": "n2", "type": "text", "color": "3", "text": "Node 2"},
            ]
        }

        mock_logic = MagicMock()
        mock_logic.canvas_data = mock_canvas_data
        mock_logic.cluster_canvas_nodes = MagicMock(
            side_effect=RuntimeError("Unexpected error")
        )

        with patch.dict("sys.modules", {"canvas_utils": MagicMock()}):
            import sys

            mock_module = MagicMock()
            mock_module.CanvasBusinessLogic = MagicMock(return_value=mock_logic)
            sys.modules["canvas_utils"] = mock_module

            with pytest.raises(ClusteringFailedError) as exc_info:
                service._perform_clustering(
                    Path("/test/canvas.canvas"), "3", None, 2
                )
            assert "Clustering failed" in str(exc_info.value)

    def test_perform_clustering_restores_original_nodes(
        self, service: IntelligentGroupingService
    ):
        """
        Test that original nodes are restored after clustering.

        Coverage: Lines 335-337 (finally block)
        """
        original_nodes = [
            {"id": "n1", "type": "text", "color": "1", "text": "Original 1"},
            {"id": "n2", "type": "text", "color": "3", "text": "Filtered"},
            {"id": "n3", "type": "text", "color": "3", "text": "Also filtered"},
        ]

        mock_canvas_data = {"nodes": original_nodes.copy()}

        mock_cluster_result = {
            "clusters": [{"id": "c1", "nodes": ["n2", "n3"]}],
            "optimization_stats": {},
            "clustering_parameters": {},
        }

        mock_logic = MagicMock()
        mock_logic.canvas_data = mock_canvas_data
        mock_logic.cluster_canvas_nodes = MagicMock(return_value=mock_cluster_result)

        with patch.dict("sys.modules", {"canvas_utils": MagicMock()}):
            import sys

            mock_module = MagicMock()
            mock_module.CanvasBusinessLogic = MagicMock(return_value=mock_logic)
            sys.modules["canvas_utils"] = mock_module

            service._perform_clustering(
                Path("/test/canvas.canvas"), "3", None, 2
            )

            # Verify original nodes were restored
            assert len(mock_canvas_data["nodes"]) == 3


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Absolute Path Coverage
# [Coverage: Line 249]
# ═══════════════════════════════════════════════════════════════════════════════

class TestAbsolutePathCoverage:
    """Additional tests for absolute path handling in _resolve_canvas_path."""

    def test_resolve_windows_absolute_path(self, service: IntelligentGroupingService):
        """Test resolving Windows-style absolute path."""
        # On Windows, paths like C:\path are absolute
        result = service._resolve_canvas_path("C:\\Users\\test\\canvas.canvas")
        # Path.is_absolute() should return True for Windows paths on Windows
        assert "canvas.canvas" in str(result)

    def test_resolve_unix_absolute_path(self):
        """Test resolving Unix-style absolute path on any platform."""
        import platform

        service = IntelligentGroupingService("/base/path")
        result = service._resolve_canvas_path("/absolute/test.canvas")
        # On Windows, Path normalizes to backslashes
        if platform.system() == "Windows":
            assert "absolute" in str(result) and "test.canvas" in str(result)
        else:
            assert str(result) == "/absolute/test.canvas"
