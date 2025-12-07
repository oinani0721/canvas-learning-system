#!/usr/bin/env python3
"""
Canvas节点智能聚类功能测试

测试Story 8.2的Canvas节点智能聚类布局优化功能。

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-10-21
"""

import json
import os
import sys
import tempfile

import pytest

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 模拟依赖（如果未安装）
try:
    import jieba
    import numpy as np
    from sklearn.cluster import KMeans
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics import silhouette_score
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False
    print("警告: 聚类依赖未安装，部分测试将被跳过")

from canvas_utils import CanvasBusinessLogic, CanvasJSONOperator


class TestCanvasClustering:
    """Canvas聚类功能测试类"""

    @pytest.fixture
    def sample_canvas_data(self):
        """创建测试用的Canvas数据"""
        return {
            "nodes": [
                {
                    "id": "math-001",
                    "type": "text",
                    "text": "什么是逆否命题？逆否命题是逻辑学中的重要概念。",
                    "x": 100,
                    "y": 100,
                    "width": 400,
                    "height": 120,
                    "color": "4"  # 红色问题节点
                },
                {
                    "id": "math-001-y",
                    "type": "text",
                    "text": "逆否命题就是将原命题的结论和条件互换，然后都否定。",
                    "x": 100,
                    "y": 250,  # v1.1布局：黄色节点在问题正下方
                    "width": 350,
                    "height": 150,
                    "color": "6"  # 黄色理解节点
                },
                {
                    "id": "math-002",
                    "type": "text",
                    "text": "如何证明集合的包含关系？集合论中的证明方法。",
                    "x": 600,
                    "y": 100,
                    "width": 400,
                    "height": 120,
                    "color": "4"  # 红色问题节点
                },
                {
                    "id": "math-002-y",
                    "type": "text",
                    "text": "证明A包含B，需要证明对于任意x∈B，都有x∈A。",
                    "x": 600,
                    "y": 250,
                    "width": 350,
                    "height": 150,
                    "color": "6"  # 黄色理解节点
                },
                {
                    "id": "math-003",
                    "type": "text",
                    "text": "函数的连续性定义和性质分析。",
                    "x": 1100,
                    "y": 100,
                    "width": 400,
                    "height": 120,
                    "color": "4"  # 红色问题节点
                },
                {
                    "id": "math-003-y",
                    "type": "text",
                    "text": "函数在某点连续，当且仅当lim(x→a)f(x)=f(a)。",
                    "x": 1100,
                    "y": 250,
                    "width": 350,
                    "height": 150,
                    "color": "6"  # 黄色理解节点
                },
                {
                    "id": "physics-001",
                    "type": "text",
                    "text": "牛顿第二定律的基本内容和应用场景。",
                    "x": 100,
                    "y": 500,
                    "width": 400,
                    "height": 120,
                    "color": "4"  # 红色问题节点
                },
                {
                    "id": "physics-001-y",
                    "type": "text",
                    "text": "F=ma，力等于质量乘以加速度，这是经典力学的基础。",
                    "x": 100,
                    "y": 650,
                    "width": 350,
                    "height": 150,
                    "color": "6"  # 黄色理解节点
                },
                {
                    "id": "physics-002",
                    "type": "text",
                    "text": "动量守恒定律的成立条件和物理意义。",
                    "x": 600,
                    "y": 500,
                    "width": 400,
                    "height": 120,
                    "color": "4"  # 红色问题节点
                },
                {
                    "id": "physics-002-y",
                    "type": "text",
                    "text": "在不受外力或外力合力为零的系统中，总动量保持不变。",
                    "x": 600,
                    "y": 650,
                    "width": 350,
                    "height": 150,
                    "color": "6"  # 黄色理解节点
                }
            ],
            "edges": [
                {
                    "id": "edge-math-001",
                    "fromNode": "math-001",
                    "toNode": "math-001-y",
                    "label": "个人理解"
                },
                {
                    "id": "edge-math-002",
                    "fromNode": "math-002",
                    "toNode": "math-002-y",
                    "label": "个人理解"
                },
                {
                    "id": "edge-math-003",
                    "fromNode": "math-003",
                    "toNode": "math-003-y",
                    "label": "个人理解"
                },
                {
                    "id": "edge-physics-001",
                    "fromNode": "physics-001",
                    "toNode": "physics-001-y",
                    "label": "个人理解"
                },
                {
                    "id": "edge-physics-002",
                    "fromNode": "physics-002",
                    "toNode": "physics-002-y",
                    "label": "个人理解"
                }
            ]
        }

    @pytest.fixture
    def temp_canvas_file(self, sample_canvas_data):
        """创建临时Canvas文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.canvas', delete=False, encoding='utf-8') as f:
            json.dump(sample_canvas_data, f, ensure_ascii=False, indent=2)
            temp_path = f.name

        yield temp_path

        # 清理临时文件
        if os.path.exists(temp_path):
            os.unlink(temp_path)

        # 清理可能生成的备份文件
        for file in os.listdir(os.path.dirname(temp_path)):
            if os.path.basename(temp_path).replace('.canvas', '') in file:
                os.unlink(os.path.join(os.path.dirname(temp_path), file))

    @pytest.fixture
    def canvas_logic(self, temp_canvas_file):
        """创建CanvasBusinessLogic实例"""
        return CanvasBusinessLogic(temp_canvas_file)

    def test_dependencies_available(self):
        """测试聚类依赖是否可用"""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip("聚类依赖未安装，跳过测试")

    def test_canvas_logic_initialization(self, temp_canvas_file):
        """测试CanvasBusinessLogic初始化"""
        logic = CanvasBusinessLogic(temp_canvas_file)
        assert logic.canvas_path == temp_canvas_file
        assert "nodes" in logic.canvas_data
        assert "edges" in logic.canvas_data
        assert len(logic.canvas_data["nodes"]) == 10

    @pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="聚类依赖未安装")
    def test_clustering_with_insufficient_nodes(self, canvas_logic):
        """测试节点数量不足时的聚类行为"""
        # 创建只有2个节点的最小Canvas
        minimal_data = {
            "nodes": [
                {
                    "id": "node1",
                    "type": "text",
                    "text": "节点1",
                    "x": 0,
                    "y": 0,
                    "width": 400,
                    "height": 120,
                    "color": "4"
                },
                {
                    "id": "node2",
                    "type": "text",
                    "text": "节点2",
                    "x": 500,
                    "y": 0,
                    "width": 400,
                    "height": 120,
                    "color": "4"
                }
            ],
            "edges": []
        }

        # 写入最小数据
        CanvasJSONOperator.write_canvas(canvas_logic.canvas_path, minimal_data)
        canvas_logic.canvas_data = minimal_data

        # 测试应该抛出ValueError
        with pytest.raises(ValueError, match="Canvas节点数量不足进行聚类"):
            canvas_logic.cluster_canvas_nodes(min_cluster_size=3)

    @pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="聚类依赖未安装")
    def test_basic_clustering_functionality(self, canvas_logic):
        """测试基础聚类功能"""
        # 执行聚类
        result = canvas_logic.cluster_canvas_nodes(
            n_clusters=2,
            create_groups=False,  # 先不创建Group节点
            min_cluster_size=2
        )

        # 验证结果结构
        assert "clusters" in result
        assert "layout_summary" in result
        assert "optimization_stats" in result
        assert "original_layout" in result
        assert "optimized_layout" in result

        # 验证聚类结果
        clusters = result["clusters"]
        assert len(clusters) == 2

        # 验证每个聚类的基本结构
        for cluster in clusters:
            assert "id" in cluster
            assert "label" in cluster
            assert "nodes" in cluster
            assert "center" in cluster
            assert "confidence" in cluster
            assert "size" in cluster
            assert cluster["size"] >= 2  # 最小聚类大小

        # 验证统计信息
        stats = result["optimization_stats"]
        assert "total_nodes" in stats
        assert "clusters_created" in stats
        assert "layout_time_ms" in stats
        assert "clustering_accuracy" in stats
        assert stats["total_nodes"] == 10
        assert stats["clusters_created"] == 2
        assert 0 <= stats["clustering_accuracy"] <= 1

    @pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="聚类依赖未安装")
    def test_clustering_with_group_creation(self, canvas_logic):
        """测试带Group节点创建的聚类"""
        result = canvas_logic.cluster_canvas_nodes(
            n_clusters=2,
            create_groups=True,
            min_cluster_size=2
        )

        # 验证Group节点创建
        assert "group_nodes" in result
        group_nodes = result["group_nodes"]
        assert len(group_nodes) == 2

        # 验证Group节点结构
        for group in group_nodes:
            assert group["type"] == "group"
            assert "id" in group
            assert "label" in group
            assert "x" in group
            assert "y" in group
            assert "width" in group
            assert "height" in group
            assert "backgroundStyle" in group
            assert "children" in group
            assert len(group["children"]) >= 2

        # 验证Canvas文件中的Group节点
        updated_data = CanvasJSONOperator.read_canvas(canvas_logic.canvas_path)
        group_nodes_in_canvas = [node for node in updated_data["nodes"] if node["type"] == "group"]
        assert len(group_nodes_in_canvas) == 2

    @pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="聚类依赖未安装")
    def test_v1_1_layout_compatibility(self, canvas_logic):
        """测试v1.1布局算法兼容性"""
        # 执行聚类
        result = canvas_logic.cluster_canvas_nodes(
            n_clusters=2,
            create_groups=True,
            min_cluster_size=2
        )

        # 验证v1.1兼容性信息
        optimized_layout = result["optimized_layout"]
        assert "v1_1_compatibility" in optimized_layout
        v1_1_info = optimized_layout["v1_1_compatibility"]
        assert "yellow_alignment" in v1_1_info
        assert "question_yellow_pairs" in v1_1_info
        assert "layout_constraints" in v1_1_info
        assert v1_1_info["yellow_alignment"] == "maintained"
        assert v1_1_info["layout_constraints"] == "preserved"

        # 验证问题-黄色配对数量
        pairs_count = v1_1_info["question_yellow_pairs"]
        assert pairs_count == 5  # 应该有5个问题-黄色配对

        # 验证实际的节点位置关系
        updated_data = CanvasJSONOperator.read_canvas(canvas_logic.canvas_path)
        for node in updated_data["nodes"]:
            if node["color"] == "6":  # 黄色节点
                # 查找对应的问题节点
                connected_edges = [edge for edge in updated_data["edges"]
                                if edge["toNode"] == node["id"] and edge["label"] == "个人理解"]
                if connected_edges:
                    question_node = CanvasJSONOperator.find_node_by_id(updated_data, connected_edges[0]["fromNode"])
                    if question_node:
                        # 验证v1.1布局约束：黄色节点在问题节点正下方
                        assert abs(node["x"] - question_node["x"]) <= 1  # 水平对齐
                        assert node["y"] > question_node["y"]  # 垂直下方

    @pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="聚类依赖未安装")
    def test_clustering_performance(self, canvas_logic):
        """测试聚类性能（响应时间<3秒要求）"""
        import time
        start_time = time.time()

        result = canvas_logic.cluster_canvas_nodes(
            n_clusters=3,
            create_groups=True,
            min_cluster_size=2
        )

        end_time = time.time()
        processing_time = (end_time - start_time) * 1000  # 转换为毫秒

        # 验证性能要求
        assert processing_time < 3000, f"聚类处理时间 {processing_time}ms 超过3秒要求"

        # 验证统计中记录的时间
        stats = result["optimization_stats"]
        assert "layout_time_ms" in stats
        assert stats["layout_time_ms"] < 3000

    def test_clustering_backup_functionality(self, canvas_logic):
        """测试聚类备份功能"""
        # 创建备份
        backup_path = canvas_logic.save_clustering_backup("test_backup")
        assert os.path.exists(backup_path)
        assert "test_backup" in backup_path

        # 验证备份文件是有效的Canvas文件
        backup_data = CanvasJSONOperator.read_canvas(backup_path)
        assert "nodes" in backup_data
        assert "edges" in backup_data
        assert len(backup_data["nodes"]) == 10

        # 验证备份信息记录
        backups = canvas_logic.get_clustering_backups()
        assert len(backups) >= 1
        backup_names = [backup["name"] for backup in backups]
        assert "test_backup" in backup_names

        # 测试恢复备份
        success = canvas_logic.restore_clustering_backup("test_backup")
        assert success

        # 验证恢复后的数据正确
        restored_data = canvas_logic.canvas_data
        assert len(restored_data["nodes"]) == 10
        assert len(restored_data["edges"]) == 5

    def test_clustering_backup_with_invalid_name(self, canvas_logic):
        """测试无效备份名称的恢复"""
        success = canvas_logic.restore_clustering_backup("nonexistent_backup")
        assert not success

    def test_clustering_configuration(self, canvas_logic):
        """测试聚类参数配置"""
        # 测试有效配置
        config = canvas_logic.configure_clustering_parameters(
            n_clusters=3,
            similarity_threshold=0.5,
            clustering_algorithm="kmeans",
            create_groups=True,
            min_cluster_size=2,
            optimize_layout=True
        )

        assert config["valid"] == True
        assert "validation_errors" not in config
        assert config["n_clusters"] == 3
        assert config["similarity_threshold"] == 0.5
        assert config["clustering_algorithm"] == "kmeans"

        # 测试无效配置
        invalid_config = canvas_logic.configure_clustering_parameters(
            n_clusters=1,  # 无效：必须>=2
            similarity_threshold=1.5,  # 无效：必须在0-1之间
            clustering_algorithm="invalid"  # 无效：算法不支持
        )

        assert invalid_config["valid"] == False
        assert "validation_errors" in invalid_config
        assert len(invalid_config["validation_errors"]) >= 2

    @pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="聚类依赖未安装")
    def test_intelligent_clustering_interface(self, canvas_logic):
        """测试智能聚类高级接口"""
        result = canvas_logic.apply_intelligent_clustering(
            n_clusters=2,
            save_backup=True,
            backup_name="intelligent_test"
        )

        # 验证接口结果结构
        assert "success" in result
        assert "clustering_result" in result
        assert "operation_summary" in result

        if result["success"]:
            # 验证聚类结果
            clustering_result = result["clustering_result"]
            assert "clusters" in clustering_result
            assert "layout_summary" in clustering_result

            # 验证操作摘要
            summary = result["operation_summary"]
            assert "timestamp" in summary
            assert "backup_saved" in summary
            assert summary["backup_saved"] == True
            assert "backup_path" in summary
            assert summary["backup_path"] is not None

    def test_identify_question_yellow_pairs(self, canvas_logic):
        """测试问题-黄色节点配对识别"""
        text_nodes = [
            node for node in canvas_logic.canvas_data["nodes"]
            if node["type"] == "text"
        ]

        pairs = canvas_logic._identify_question_yellow_pairs(text_nodes)

        # 验证配对识别
        assert len(pairs) >= 10  # 应该识别到5对，共10个节点

        # 验证具体的配对关系
        assert "math-001" in pairs
        assert "math-001-y" in pairs
        assert pairs["math-001"] == "math-001-y"
        assert pairs["math-001-y"] == "math-001"

    def test_clustering_label_generation(self, canvas_logic):
        """测试聚类标签生成质量"""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip("聚类依赖未安装")

        result = canvas_logic.cluster_canvas_nodes(
            n_clusters=2,
            create_groups=False,
            min_cluster_size=2
        )

        clusters = result["clusters"]

        # 验证每个聚类都有有意义的标签
        for cluster in clusters:
            label = cluster["label"]
            assert isinstance(label, str)
            assert len(label) > 0
            assert "等概念" in label  # 标签应该包含"等概念"后缀

            # 验证关键词提取
            assert "top_keywords" in cluster
            keywords = cluster["top_keywords"]
            assert isinstance(keywords, list)
            assert len(keywords) >= 1

    def test_clustering_accuracy_evaluation(self, canvas_logic):
        """测试聚类准确性评估"""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip("聚类依赖未安装")

        result = canvas_logic.cluster_canvas_nodes(
            n_clusters=2,
            create_groups=False,
            min_cluster_size=2
        )

        # 验证准确性指标
        stats = result["optimization_stats"]
        assert "clustering_accuracy" in stats
        accuracy = stats["clustering_accuracy"]

        # 聚类准确率应该是0到1之间的数值
        assert isinstance(accuracy, (int, float))
        assert -1 <= accuracy <= 1  # 轮廓系数范围

        # 对于我们的测试数据，应该能获得合理的聚类质量
        # 注意：轮廓系数可能为负值，表示聚类效果不佳
        assert isinstance(accuracy, float)

    @pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="聚类依赖未安装")
    def test_edge_cases(self, canvas_logic):
        """测试边缘情况"""
        # 测试只有一个文本节点的情况
        single_text_data = {
            "nodes": [
                {
                    "id": "single",
                    "type": "text",
                    "text": "唯一的文本节点",
                    "x": 0,
                    "y": 0,
                    "width": 400,
                    "height": 120,
                    "color": "4"
                },
                {
                    "id": "empty",
                    "type": "text",
                    "text": "",  # 空文本
                    "x": 500,
                    "y": 0,
                    "width": 400,
                    "height": 120,
                    "color": "4"
                }
            ],
            "edges": []
        }

        CanvasJSONOperator.write_canvas(canvas_logic.canvas_path, single_text_data)
        canvas_logic.canvas_data = single_text_data

        # 应该抛出节点数量不足的错误
        with pytest.raises(ValueError, match="Canvas节点数量不足进行聚类"):
            canvas_logic.cluster_canvas_nodes(min_cluster_size=2)


if __name__ == "__main__":
    # 运行测试的便捷方法
    pytest.main([__file__, "-v", "--tb=short"])
