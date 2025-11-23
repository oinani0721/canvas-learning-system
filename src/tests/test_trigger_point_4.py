#!/usr/bin/env python3
"""
艾宾浩斯触发点4单元测试
测试ebbinghaus/trigger_point_4.py模块

Story: GDS.1 - Subtask 3.1, 3.3
覆盖率目标: >90%
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from pathlib import Path

import sys
import os
# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ebbinghaus.trigger_point_4 import (
    trigger_weak_point_clustering,
    trigger_weak_point_clustering_with_review_canvas
)


class TestTriggerWeakPointClustering:
    """触发点4 API的单元测试"""

    @pytest.fixture
    def mock_canvas_file(self, tmp_path):
        """创建临时Canvas文件"""
        canvas_file = tmp_path / "test.canvas"
        canvas_file.write_text('{"nodes": [], "edges": []}')
        return str(canvas_file)

    @pytest.fixture
    def mock_clustering_result(self):
        """Mock聚类结果"""
        return [
            {
                "cluster_id": 42,
                "concepts": [
                    {"id": 123, "name": "逆否命题", "score": 65, "reviews": 4},
                    {"id": 124, "name": "充分必要条件", "score": 68, "reviews": 3}
                ],
                "cluster_score": 66.5,
                "cluster_size": 2
            },
            {
                "cluster_id": 108,
                "concepts": [
                    {"id": 125, "name": "逻辑等价", "score": 62, "reviews": 5}
                ],
                "cluster_score": 62.0,
                "cluster_size": 1
            }
        ]

    # ==================== Task 3.1: 触发点4 API基础测试 ====================

    def test_trigger_clustering_success(self, mock_canvas_file, mock_clustering_result):
        """测试用例：成功执行薄弱点聚类"""
        with patch('ebbinghaus.trigger_point_4.Neo4jGDSClustering') as MockClustering:
            # Mock聚类服务
            mock_service = MagicMock()
            MockClustering.return_value = mock_service

            # Mock方法返回值
            mock_service.create_weak_concepts_graph_projection.return_value = (True, "Success")
            mock_service.run_leiden_clustering.return_value = mock_clustering_result
            mock_service.format_clustering_results.return_value = {
                "trigger_point": 4,
                "trigger_name": "薄弱点聚类",
                "clusters": mock_clustering_result,
                "total_weak_concepts": 3,
                "total_clusters": 2,
                "timestamp": "2025-11-14T12:00:00"
            }

            # 执行测试
            result = trigger_weak_point_clustering(
                canvas_path=mock_canvas_file,
                min_weak_score=70,
                min_review_count=3
            )

            # 验证结果
            assert result["trigger_point"] == 4
            assert result["trigger_name"] == "薄弱点聚类"
            assert result["total_weak_concepts"] == 3
            assert result["total_clusters"] == 2
            assert len(result["clusters"]) == 2

            # 验证调用链
            mock_service.create_weak_concepts_graph_projection.assert_called_once_with(
                force_recreate=True
            )
            mock_service.run_leiden_clustering.assert_called_once_with(
                min_weak_score=70,
                min_review_count=3,
                gamma=1.0,
                tolerance=0.0001,
                random_seed=42
            )
            mock_service.format_clustering_results.assert_called_once()
            mock_service.close.assert_called_once()

    def test_trigger_clustering_canvas_not_found(self):
        """测试用例：Canvas文件不存在时抛出异常"""
        with pytest.raises(FileNotFoundError) as exc_info:
            trigger_weak_point_clustering(
                canvas_path="不存在的文件.canvas",
                min_weak_score=70,
                min_review_count=3
            )

        assert "Canvas file not found" in str(exc_info.value)

    def test_trigger_clustering_neo4j_connection_failed(self, mock_canvas_file):
        """测试用例：Neo4j连接失败时抛出异常"""
        with patch('ebbinghaus.trigger_point_4.Neo4jGDSClustering') as MockClustering:
            # Mock连接失败
            MockClustering.side_effect = RuntimeError("Neo4j connection failed")

            # 验证抛出RuntimeError
            with pytest.raises(RuntimeError) as exc_info:
                trigger_weak_point_clustering(
                    canvas_path=mock_canvas_file,
                    min_weak_score=70,
                    min_review_count=3
                )

            assert "Failed to connect to Neo4j GDS" in str(exc_info.value)

    def test_trigger_clustering_graph_projection_failed(self, mock_canvas_file):
        """测试用例：图投影创建失败时抛出异常"""
        with patch('ebbinghaus.trigger_point_4.Neo4jGDSClustering') as MockClustering:
            mock_service = MagicMock()
            MockClustering.return_value = mock_service

            # Mock图投影失败
            mock_service.create_weak_concepts_graph_projection.return_value = (False, "Projection failed")

            # 验证抛出RuntimeError
            with pytest.raises(RuntimeError) as exc_info:
                trigger_weak_point_clustering(
                    canvas_path=mock_canvas_file,
                    min_weak_score=70,
                    min_review_count=3
                )

            assert "Graph projection failed" in str(exc_info.value)
            mock_service.close.assert_called_once()  # 确保资源清理

    def test_trigger_clustering_leiden_failed(self, mock_canvas_file):
        """测试用例：Leiden聚类失败时抛出异常"""
        with patch('ebbinghaus.trigger_point_4.Neo4jGDSClustering') as MockClustering:
            mock_service = MagicMock()
            MockClustering.return_value = mock_service

            mock_service.create_weak_concepts_graph_projection.return_value = (True, "Success")
            mock_service.run_leiden_clustering.side_effect = RuntimeError("Leiden algorithm failed")

            # 验证抛出RuntimeError
            with pytest.raises(RuntimeError) as exc_info:
                trigger_weak_point_clustering(
                    canvas_path=mock_canvas_file,
                    min_weak_score=70,
                    min_review_count=3
                )

            assert "Weak point clustering failed" in str(exc_info.value)
            mock_service.close.assert_called_once()  # 确保资源清理

    def test_trigger_clustering_empty_result(self, mock_canvas_file):
        """测试用例：无薄弱概念时返回空聚类结果"""
        with patch('ebbinghaus.trigger_point_4.Neo4jGDSClustering') as MockClustering:
            mock_service = MagicMock()
            MockClustering.return_value = mock_service

            # Mock空结果
            mock_service.create_weak_concepts_graph_projection.return_value = (True, "Success")
            mock_service.run_leiden_clustering.return_value = []
            mock_service.format_clustering_results.return_value = {
                "trigger_point": 4,
                "trigger_name": "薄弱点聚类",
                "clusters": [],
                "total_weak_concepts": 0,
                "total_clusters": 0,
                "timestamp": "2025-11-14T12:00:00"
            }

            # 执行测试
            result = trigger_weak_point_clustering(
                canvas_path=mock_canvas_file,
                min_weak_score=70,
                min_review_count=3
            )

            # 验证空结果
            assert result["total_weak_concepts"] == 0
            assert result["total_clusters"] == 0
            assert len(result["clusters"]) == 0

    def test_trigger_clustering_custom_parameters(self, mock_canvas_file, mock_clustering_result):
        """测试用例：使用自定义参数"""
        with patch('ebbinghaus.trigger_point_4.Neo4jGDSClustering') as MockClustering:
            mock_service = MagicMock()
            MockClustering.return_value = mock_service

            mock_service.create_weak_concepts_graph_projection.return_value = (True, "Success")
            mock_service.run_leiden_clustering.return_value = mock_clustering_result
            mock_service.format_clustering_results.return_value = {
                "trigger_point": 4,
                "trigger_name": "薄弱点聚类",
                "clusters": mock_clustering_result,
                "total_weak_concepts": 3,
                "total_clusters": 2,
                "timestamp": "2025-11-14T12:00:00"
            }

            # 使用自定义参数
            result = trigger_weak_point_clustering(
                canvas_path=mock_canvas_file,
                min_weak_score=65,  # 自定义阈值
                min_review_count=5,  # 自定义复习次数
                neo4j_uri="bolt://custom:7687",
                neo4j_database="custom_db"
            )

            # 验证自定义参数传递
            MockClustering.assert_called_once_with(
                uri="bolt://custom:7687",
                user="neo4j",
                password="707188Fx",
                database="custom_db"
            )

            mock_service.run_leiden_clustering.assert_called_once_with(
                min_weak_score=65,
                min_review_count=5,
                gamma=1.0,
                tolerance=0.0001,
                random_seed=42
            )

    # ==================== Task 3.2预览: 检验白板集成测试 ====================

    def test_trigger_with_review_canvas_clustering_only(self, mock_canvas_file, mock_clustering_result):
        """测试用例：仅执行聚类（不生成检验白板）"""
        with patch('ebbinghaus.trigger_point_4.Neo4jGDSClustering') as MockClustering:
            mock_service = MagicMock()
            MockClustering.return_value = mock_service

            mock_service.create_weak_concepts_graph_projection.return_value = (True, "Success")
            mock_service.run_leiden_clustering.return_value = mock_clustering_result
            mock_service.format_clustering_results.return_value = {
                "trigger_point": 4,
                "trigger_name": "薄弱点聚类",
                "clusters": mock_clustering_result,
                "total_weak_concepts": 3,
                "total_clusters": 2,
                "timestamp": "2025-11-14T12:00:00"
            }

            # 执行测试（不生成检验白板）
            clustering_result, review_canvas_path = trigger_weak_point_clustering_with_review_canvas(
                canvas_path=mock_canvas_file,
                min_weak_score=70,
                min_review_count=3,
                generate_review_canvas=False
            )

            # 验证结果
            assert clustering_result["total_weak_concepts"] == 3
            assert review_canvas_path is None  # 未生成检验白板

    def test_trigger_with_review_canvas_pending_implementation(self, mock_canvas_file, mock_clustering_result):
        """测试用例：检验白板生成功能待实现（当前返回None）"""
        with patch('ebbinghaus.trigger_point_4.Neo4jGDSClustering') as MockClustering:
            mock_service = MagicMock()
            MockClustering.return_value = mock_service

            mock_service.create_weak_concepts_graph_projection.return_value = (True, "Success")
            mock_service.run_leiden_clustering.return_value = mock_clustering_result
            mock_service.format_clustering_results.return_value = {
                "trigger_point": 4,
                "trigger_name": "薄弱点聚类",
                "clusters": mock_clustering_result,
                "total_weak_concepts": 3,
                "total_clusters": 2,
                "timestamp": "2025-11-14T12:00:00"
            }

            # 执行测试（请求生成检验白板，但功能待实现）
            clustering_result, review_canvas_path = trigger_weak_point_clustering_with_review_canvas(
                canvas_path=mock_canvas_file,
                min_weak_score=70,
                min_review_count=3,
                generate_review_canvas=True
            )

            # 验证结果
            assert clustering_result["total_weak_concepts"] == 3
            # TODO: Story GDS.1 - Subtask 3.2
            # 当前检验白板生成功能待实现，返回None
            assert review_canvas_path is None


# ==================== 运行测试 ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
