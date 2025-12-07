#!/usr/bin/env python3
"""
Neo4j GDS Clustering单元测试
测试canvas_memory/neo4j_gds_clustering.py模块

Story: GDS.1 - Subtask 1.3, 2.4
覆盖率目标: >90%
"""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest
from neo4j.exceptions import ClientError, ServiceUnavailable

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from canvas_memory.neo4j_gds_clustering import Neo4jGDSClustering


class TestNeo4jGDSClustering:
    """Neo4jGDSClustering类的单元测试"""

    @pytest.fixture
    def mock_driver(self):
        """创建mock Neo4j driver"""
        driver = MagicMock()
        session = MagicMock()
        driver.session.return_value.__enter__.return_value = session
        driver.session.return_value.__exit__.return_value = None
        return driver, session

    @pytest.fixture
    def clustering_service(self, mock_driver):
        """创建聚类服务实例（使用mock driver）"""
        driver, session = mock_driver

        # Mock连接测试成功
        mock_result = MagicMock()
        mock_result.single.return_value = {"num": 1}
        session.run.return_value = mock_result

        with patch('canvas_memory.neo4j_gds_clustering.GraphDatabase.driver', return_value=driver):
            service = Neo4jGDSClustering()
            service.driver = driver
            service.connected = True

            # Reset mock call counts after initialization
            session.run.reset_mock()

            return service, driver, session

    # ==================== Task 1.3: 图投影单元测试 ====================

    def test_create_graph_projection_success(self, clustering_service):
        """测试用例：正常情况创建图投影成功"""
        service, driver, session = clustering_service

        # Mock gds.graph.exists返回False（图不存在）
        exists_result = MagicMock()
        exists_result.single.return_value = {"exists": False}

        # Mock gds.graph.project返回成功结果
        project_result = MagicMock()
        project_result.single.return_value = {
            "graphName": "weak-concepts-graph",
            "nodeCount": 100,
            "relationshipCount": 250,
            "projectMillis": 150
        }

        # 设置session.run的返回值序列
        session.run.side_effect = [exists_result, project_result]

        # 执行测试
        success, message = service.create_weak_concepts_graph_projection(force_recreate=True)

        # 验证结果
        assert success is True
        assert "100 nodes" in message
        assert "250 relationships" in message

        # 验证调用
        assert session.run.call_count == 2  # exists + project

    def test_create_graph_projection_already_exists_recreate(self, clustering_service):
        """测试用例：图投影已存在时重建"""
        service, driver, session = clustering_service

        # Mock gds.graph.exists返回True（图已存在）
        exists_result = MagicMock()
        exists_result.single.return_value = {"exists": True}

        # Mock gds.graph.drop
        drop_result = MagicMock()
        drop_result.single.return_value = {"graphName": "weak-concepts-graph"}

        # Mock gds.graph.project
        project_result = MagicMock()
        project_result.single.return_value = {
            "graphName": "weak-concepts-graph",
            "nodeCount": 100,
            "relationshipCount": 250,
            "projectMillis": 150
        }

        # 设置session.run的返回值序列
        session.run.side_effect = [exists_result, drop_result, project_result]

        # 执行测试
        success, message = service.create_weak_concepts_graph_projection(force_recreate=True)

        # 验证结果
        assert success is True

        # 验证调用顺序：exists → drop → project
        assert session.run.call_count == 3

    def test_create_graph_projection_already_exists_skip(self, clustering_service):
        """测试用例：图投影已存在时跳过创建"""
        service, driver, session = clustering_service

        # Mock gds.graph.exists返回True
        exists_result = MagicMock()
        exists_result.single.return_value = {"exists": True}
        session.run.return_value = exists_result

        # 执行测试（force_recreate=False）
        success, message = service.create_weak_concepts_graph_projection(force_recreate=False)

        # 验证结果
        assert success is True
        assert "already exists" in message

        # 验证只调用了exists，没有调用drop和project
        assert session.run.call_count == 1

    def test_create_graph_projection_connection_not_established(self):
        """测试用例：Neo4j连接失败时异常处理"""
        # 创建未连接的服务实例
        with patch('canvas_memory.neo4j_gds_clustering.GraphDatabase.driver') as mock_driver_class:
            mock_driver = MagicMock()
            mock_driver_class.return_value = mock_driver

            # Mock连接测试失败
            mock_session = MagicMock()
            mock_driver.session.return_value.__enter__.return_value = mock_session
            mock_session.run.side_effect = ServiceUnavailable("Connection refused")

            # 验证初始化时抛出异常
            with pytest.raises(ServiceUnavailable):
                Neo4jGDSClustering()

    def test_create_graph_projection_client_error(self, clustering_service):
        """测试用例：Cypher查询错误时异常处理"""
        service, driver, session = clustering_service

        # Mock session.run抛出ClientError
        session.run.side_effect = ClientError("Invalid Cypher query")

        # 验证抛出ClientError
        with pytest.raises(ClientError):
            service.create_weak_concepts_graph_projection()

    # ==================== Task 2.4: Leiden聚类集成测试 ====================

    def test_run_leiden_clustering_success(self, clustering_service):
        """测试用例：Leiden聚类成功执行"""
        service, driver, session = clustering_service

        # Mock Leiden聚类结果
        mock_result = MagicMock()
        mock_result.__iter__.return_value = iter([
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
        ])
        session.run.return_value = mock_result

        # 执行测试
        clusters = service.run_leiden_clustering(
            min_weak_score=70,
            min_review_count=3,
            gamma=1.0,
            tolerance=0.0001,
            random_seed=42
        )

        # 验证结果
        assert len(clusters) == 2
        assert clusters[0]["cluster_id"] == 42
        assert clusters[0]["cluster_size"] == 2
        assert clusters[0]["cluster_score"] == 66.5
        assert clusters[1]["cluster_id"] == 108
        assert clusters[1]["cluster_size"] == 1

    def test_run_leiden_clustering_empty_result(self, clustering_service):
        """测试用例：无薄弱概念时返回空结果"""
        service, driver, session = clustering_service

        # Mock空结果
        mock_result = MagicMock()
        mock_result.__iter__.return_value = iter([])
        session.run.return_value = mock_result

        # 执行测试
        clusters = service.run_leiden_clustering()

        # 验证结果
        assert len(clusters) == 0

    def test_run_leiden_clustering_client_error(self, clustering_service):
        """测试用例：聚类失败时异常处理"""
        service, driver, session = clustering_service

        # Mock ClientError
        session.run.side_effect = ClientError("Graph not found")

        # 验证抛出ClientError
        with pytest.raises(ClientError):
            service.run_leiden_clustering()

    # ==================== Task 2.2: 结果格式化测试 ====================

    def test_format_clustering_results_urgent(self):
        """测试用例：紧急度评估 - urgent级别（<60分）"""
        service = Neo4jGDSClustering.__new__(Neo4jGDSClustering)  # 不调用__init__

        clusters = [
            {
                "cluster_id": 1,
                "concepts": [{"id": 1, "name": "概念A", "score": 55, "reviews": 5}],
                "cluster_score": 55.0,
                "cluster_size": 1
            }
        ]

        result = service.format_clustering_results(clusters)

        # 验证紧急度
        assert result["clusters"][0]["recommended_review_urgency"] == "urgent"
        assert result["total_weak_concepts"] == 1
        assert result["total_clusters"] == 1
        assert "timestamp" in result

    def test_format_clustering_results_high(self):
        """测试用例：紧急度评估 - high级别（60-69分）"""
        service = Neo4jGDSClustering.__new__(Neo4jGDSClustering)

        clusters = [
            {
                "cluster_id": 2,
                "concepts": [{"id": 2, "name": "概念B", "score": 65, "reviews": 3}],
                "cluster_score": 65.0,
                "cluster_size": 1
            }
        ]

        result = service.format_clustering_results(clusters)

        # 验证紧急度
        assert result["clusters"][0]["recommended_review_urgency"] == "high"

    def test_format_clustering_results_medium(self):
        """测试用例：紧急度评估 - medium级别（≥70分）"""
        service = Neo4jGDSClustering.__new__(Neo4jGDSClustering)

        clusters = [
            {
                "cluster_id": 3,
                "concepts": [{"id": 3, "name": "概念C", "score": 72, "reviews": 2}],
                "cluster_score": 72.0,
                "cluster_size": 1
            }
        ]

        result = service.format_clustering_results(clusters)

        # 验证紧急度
        assert result["clusters"][0]["recommended_review_urgency"] == "medium"

    def test_format_clustering_results_multiple_clusters(self):
        """测试用例：多个cluster的格式化"""
        service = Neo4jGDSClustering.__new__(Neo4jGDSClustering)

        clusters = [
            {
                "cluster_id": 1,
                "concepts": [{"id": 1, "name": "A", "score": 55, "reviews": 5}],
                "cluster_score": 55.0,
                "cluster_size": 1
            },
            {
                "cluster_id": 2,
                "concepts": [
                    {"id": 2, "name": "B", "score": 65, "reviews": 3},
                    {"id": 3, "name": "C", "score": 68, "reviews": 2}
                ],
                "cluster_score": 66.5,
                "cluster_size": 2
            },
            {
                "cluster_id": 3,
                "concepts": [{"id": 4, "name": "D", "score": 75, "reviews": 1}],
                "cluster_score": 75.0,
                "cluster_size": 1
            }
        ]

        result = service.format_clustering_results(clusters)

        # 验证统计
        assert result["total_weak_concepts"] == 4
        assert result["total_clusters"] == 3

        # 验证紧急度分布
        urgencies = [c["recommended_review_urgency"] for c in result["clusters"]]
        assert "urgent" in urgencies
        assert "high" in urgencies
        assert "medium" in urgencies

    # ==================== 额外功能测试 ====================

    def test_estimate_projection_memory(self, clustering_service):
        """测试用例：内存估算功能"""
        service, driver, session = clustering_service

        # Mock估算结果
        mock_result = MagicMock()
        mock_result.single.return_value = {
            "requiredMemory": "10 MiB",
            "nodeCount": 100,
            "relationshipCount": 250,
            "treeView": "Graph projection memory estimation"
        }
        session.run.return_value = mock_result

        # 执行测试
        estimate = service.estimate_projection_memory()

        # 验证结果
        assert estimate["required_memory"] == "10 MiB"
        assert estimate["node_count"] == 100
        assert estimate["relationship_count"] == 250

    def test_drop_graph_projection_exists(self, clustering_service):
        """测试用例：删除已存在的图投影"""
        service, driver, session = clustering_service

        # Mock exists返回True
        exists_result = MagicMock()
        exists_result.single.return_value = {"exists": True}

        # Mock drop成功
        drop_result = MagicMock()
        drop_result.single.return_value = {"graphName": "weak-concepts-graph"}

        session.run.side_effect = [exists_result, drop_result]

        # 执行测试
        success = service.drop_graph_projection()

        # 验证结果
        assert success is True
        assert session.run.call_count == 2  # exists + drop

    def test_drop_graph_projection_not_exists(self, clustering_service):
        """测试用例：删除不存在的图投影"""
        service, driver, session = clustering_service

        # Mock exists返回False
        exists_result = MagicMock()
        exists_result.single.return_value = {"exists": False}
        session.run.return_value = exists_result

        # 执行测试
        success = service.drop_graph_projection()

        # 验证结果
        assert success is True
        assert session.run.call_count == 1  # 只调用exists

    def test_context_manager(self, mock_driver):
        """测试用例：Context manager支持"""
        driver, session = mock_driver

        # Mock连接测试成功
        mock_result = MagicMock()
        mock_result.single.return_value = {"num": 1}
        session.run.return_value = mock_result

        with patch('canvas_memory.neo4j_gds_clustering.GraphDatabase.driver', return_value=driver):
            # 使用with语句
            with Neo4jGDSClustering() as service:
                assert service.connected is True

            # 验证close被调用
            driver.close.assert_called_once()

    def test_close_method(self, clustering_service):
        """测试用例：close方法"""
        service, driver, session = clustering_service

        # 执行close
        service.close()

        # 验证状态
        assert service.connected is False
        driver.close.assert_called_once()


# ==================== 运行测试 ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
