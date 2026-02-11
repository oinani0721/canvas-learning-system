# Canvas Learning System - Perform Clustering Tests
# Split from test_intelligent_grouping_service.py (EPIC-33 P1-6)
# P1-4: sys.modules patches replaced with safe monkeypatch fixtures
"""Tests for _perform_clustering, error handling, and resource warnings."""

from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

from app.services.intelligent_grouping_service import (
    CanvasNotFoundError,
    ClusteringFailedError,
    InsufficientNodesError,
    IntelligentGroupingService,
)


class TestPerformClustering:
    """
    Tests for _perform_clustering method.

    P1-4 fix: All sys.modules manipulation now uses monkeypatch fixtures
    from conftest.py (mock_canvas_utils_fail, mock_canvas_utils_success)
    instead of fragile manual save/delete/restore patterns.
    """

    def test_perform_clustering_import_error(
        self, service: IntelligentGroupingService, mock_canvas_utils_fail
    ):
        """
        Test ClusteringFailedError is raised when CanvasBusinessLogic import fails.

        P1-4 fix: Uses mock_canvas_utils_fail fixture instead of manual sys.modules manipulation.
        """
        with pytest.raises(ClusteringFailedError) as exc_info:
            service._perform_clustering(
                Path("/test/canvas.canvas"), "3", None, 2
            )
        assert "Cannot import clustering module" in str(exc_info.value)

    def test_perform_clustering_insufficient_nodes_from_filter(
        self, service: IntelligentGroupingService, mock_canvas_utils_success
    ):
        """
        Test InsufficientNodesError when not enough nodes match target color.

        P1-4 fix: Uses mock_canvas_utils_success fixture.
        """
        mock_canvas_data = {
            "nodes": [
                {"id": "n1", "type": "text", "color": "1", "text": "Wrong color"},
                {"id": "n2", "type": "text", "color": "1", "text": "Also wrong"},
            ]
        }

        mock_logic = MagicMock()
        mock_logic.canvas_data = mock_canvas_data
        mock_canvas_utils_success(mock_logic)

        with pytest.raises(InsufficientNodesError) as exc_info:
            service._perform_clustering(
                Path("/test/canvas.canvas"),
                target_color="3",
                max_groups=None,
                min_nodes_per_group=2,
            )
        assert "Not enough nodes with color '3'" in str(exc_info.value)

    def test_perform_clustering_success(
        self, service: IntelligentGroupingService, mock_canvas_utils_success
    ):
        """
        Test successful clustering execution.

        P1-4 fix: Uses mock_canvas_utils_success fixture.
        """
        mock_canvas_data = {
            "nodes": [
                {"id": "n1", "type": "text", "color": "3", "text": "Node 1 text"},
                {"id": "n2", "type": "text", "color": "3", "text": "Node 2 text"},
                {"id": "n3", "type": "text", "color": "3", "text": "Node 3 text"},
            ]
        }

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
        mock_canvas_utils_success(mock_logic)

        result = service._perform_clustering(
            Path("/test/canvas.canvas"),
            target_color="3",
            max_groups=None,
            min_nodes_per_group=2,
        )

        assert "clusters" in result
        for cluster in result["clusters"]:
            assert "node_texts" in cluster

    def test_perform_clustering_value_error_insufficient(
        self, service: IntelligentGroupingService, mock_canvas_utils_success
    ):
        """
        Test ValueError from clustering is converted to InsufficientNodesError.

        P1-4 fix: Uses mock_canvas_utils_success fixture.
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
        mock_canvas_utils_success(mock_logic)

        with pytest.raises(InsufficientNodesError):
            service._perform_clustering(
                Path("/test/canvas.canvas"), "3", None, 2
            )

    def test_perform_clustering_value_error_general(
        self, service: IntelligentGroupingService, mock_canvas_utils_success
    ):
        """
        Test general ValueError from clustering is converted to ClusteringFailedError.

        P1-4 fix: Uses mock_canvas_utils_success fixture.
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
        mock_canvas_utils_success(mock_logic)

        with pytest.raises(ClusteringFailedError) as exc_info:
            service._perform_clustering(
                Path("/test/canvas.canvas"), "3", None, 2
            )
        assert "Clustering failed" in str(exc_info.value)

    def test_perform_clustering_generic_exception(
        self, service: IntelligentGroupingService, mock_canvas_utils_success
    ):
        """
        Test generic Exception from clustering is converted to ClusteringFailedError.

        P1-4 fix: Uses mock_canvas_utils_success fixture.
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
        mock_canvas_utils_success(mock_logic)

        with pytest.raises(ClusteringFailedError) as exc_info:
            service._perform_clustering(
                Path("/test/canvas.canvas"), "3", None, 2
            )
        assert "Clustering failed" in str(exc_info.value)

    def test_perform_clustering_restores_original_nodes(
        self, service: IntelligentGroupingService, mock_canvas_utils_success
    ):
        """
        Test that original nodes are restored after clustering.

        P1-4 fix: Uses mock_canvas_utils_success fixture.
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
        mock_canvas_utils_success(mock_logic)

        service._perform_clustering(
            Path("/test/canvas.canvas"), "3", None, 2
        )

        assert len(mock_canvas_data["nodes"]) == 3


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


class TestResourceWarning:
    """Tests for resource warning generation."""

    @pytest.mark.asyncio
    async def test_resource_warning_large_nodes(
        self, service: IntelligentGroupingService
    ):
        """Test resource warning is generated for large node counts."""
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
                for i in range(6)
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
