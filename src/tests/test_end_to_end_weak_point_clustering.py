#!/usr/bin/env python3
"""
端到端测试: 薄弱点聚类 → 检验白板生成完整流程

Story GDS.1 - Subtask 3.3: 添加端到端测试

测试范围:
1. 完整流程: Canvas → Neo4j GDS聚类 → 生成检验白板
2. 检验白板文件正确生成
3. 社区概念正确分组（验证Canvas JSON结构）
4. 性能测试: 完整流程<2秒
"""

import json
import os
import time
from typing import Dict

import pytest

from canvas_utils import CanvasBusinessLogic

# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_cluster_results() -> Dict:
    """
    模拟Neo4j GDS Leiden聚类结果

    Story GDS.1格式 (trigger_point_4.py输出)
    """
    return {
        "trigger_point": 4,
        "trigger_name": "薄弱点聚类",
        "clusters": [
            {
                "cluster_id": 42,
                "concepts": [
                    {"id": 101, "name": "逆否命题", "score": 55, "reviews": 5},
                    {"id": 102, "name": "充分条件", "score": 58, "reviews": 4}
                ],
                "cluster_score": 56.5,
                "cluster_size": 2,
                "recommended_review_urgency": "urgent"
            },
            {
                "cluster_id": 88,
                "concepts": [
                    {"id": 201, "name": "德摩根律", "score": 65, "reviews": 3},
                    {"id": 202, "name": "真值表", "score": 68, "reviews": 3},
                    {"id": 203, "name": "合取范式", "score": 62, "reviews": 4}
                ],
                "cluster_score": 65.0,
                "cluster_size": 3,
                "recommended_review_urgency": "high"
            },
            {
                "cluster_id": 99,
                "concepts": [
                    {"id": 301, "name": "全称量词", "score": 72, "reviews": 2},
                    {"id": 302, "name": "存在量词", "score": 75, "reviews": 2}
                ],
                "cluster_score": 73.5,
                "cluster_size": 2,
                "recommended_review_urgency": "medium"
            }
        ],
        "total_weak_concepts": 7,
        "total_clusters": 3,
        "timestamp": "2025-01-15T10:30:00"
    }


@pytest.fixture
def temp_canvas_file(tmp_path) -> str:
    """创建临时Canvas文件用于测试"""
    canvas_dir = tmp_path / "test_canvas"
    canvas_dir.mkdir()

    canvas_path = canvas_dir / "离散数学.canvas"

    # 创建最小Canvas结构
    canvas_data = {
        "nodes": [],
        "edges": []
    }

    with open(canvas_path, 'w', encoding='utf-8') as f:
        json.dump(canvas_data, f, ensure_ascii=False, indent=2)

    return str(canvas_path)


# ============================================================================
# Test Cases - Task 3.3
# ============================================================================

class TestEndToEndWeakPointClustering:
    """端到端测试: 薄弱点聚类完整流程"""

    def test_full_workflow_clustering_to_review_canvas(
        self,
        temp_canvas_file: str,
        sample_cluster_results: Dict
    ):
        """
        测试用例1: 完整流程（Canvas → 聚类结果 → 生成检验白板）

        Story GDS.1 - Subtask 3.3

        验证点:
        1. 接受cluster_results参数
        2. 生成检验白板文件
        3. 返回正确的元数据
        """
        # Arrange
        logic = CanvasBusinessLogic(temp_canvas_file)

        # Act
        result = logic.generate_review_canvas_file(
            cluster_results=sample_cluster_results
        )

        # Assert - 验证返回结果
        assert result is not None
        assert "review_canvas_path" in result
        assert "cluster_count" in result
        assert "total_questions" in result
        assert "generation_time" in result

        # 验证聚类数量
        assert result["cluster_count"] == 3
        assert result["total_questions"] == 7  # 7个薄弱概念 = 7个问题

        # 验证文件生成
        review_canvas_path = result["review_canvas_path"]
        assert os.path.exists(review_canvas_path)
        assert "薄弱点检验" in review_canvas_path

    def test_review_canvas_file_structure_correct(
        self,
        temp_canvas_file: str,
        sample_cluster_results: Dict
    ):
        """
        测试用例2: 验证检验白板文件结构正确

        验证点:
        1. Canvas JSON格式正确
        2. 包含nodes和edges
        3. 节点类型正确
        4. 元数据完整
        """
        # Arrange
        logic = CanvasBusinessLogic(temp_canvas_file)

        # Act
        result = logic.generate_review_canvas_file(
            cluster_results=sample_cluster_results
        )

        # 读取生成的Canvas文件
        review_canvas_path = result["review_canvas_path"]
        with open(review_canvas_path, 'r', encoding='utf-8') as f:
            canvas_data = json.load(f)

        # Assert - 验证Canvas结构
        assert "nodes" in canvas_data
        assert "edges" in canvas_data
        assert isinstance(canvas_data["nodes"], list)
        assert isinstance(canvas_data["edges"], list)

        # 验证节点总数
        # 1个说明节点 + 3个分隔符 + 7个问题 + 7个黄色节点 = 18个节点
        assert len(canvas_data["nodes"]) == 18

        # 验证边总数 (7个问题→黄色连接)
        assert len(canvas_data["edges"]) == 7

    def test_community_grouping_with_separators(
        self,
        temp_canvas_file: str,
        sample_cluster_results: Dict
    ):
        """
        测试用例3: 验证社区概念正确分组（手动检查Canvas JSON）

        Story GDS.1 - Subtask 3.3

        验证点:
        1. 社区分隔符节点存在
        2. 分隔符颜色根据紧急度设置
        3. 问题节点包含元数据 (conceptName, urgency, clusterId)
        4. 同一社区节点相邻布局
        """
        # Arrange
        logic = CanvasBusinessLogic(temp_canvas_file)

        # Act
        result = logic.generate_review_canvas_file(
            cluster_results=sample_cluster_results
        )

        # 读取生成的Canvas文件
        review_canvas_path = result["review_canvas_path"]
        with open(review_canvas_path, 'r', encoding='utf-8') as f:
            canvas_data = json.load(f)

        # 提取节点
        nodes = canvas_data["nodes"]

        # 验证说明节点
        description_nodes = [n for n in nodes if "薄弱点检验白板" in n.get("text", "")]
        assert len(description_nodes) == 1
        assert description_nodes[0]["color"] == "5"  # 蓝色
        assert "triggerPoint" in description_nodes[0]
        assert description_nodes[0]["triggerPoint"] == 4

        # 验证分隔符节点
        separator_nodes = [n for n in nodes if n["id"].startswith("separator-")]
        assert len(separator_nodes) == 3  # 3个社区

        # 验证分隔符颜色映射
        separator_colors = {n["color"] for n in separator_nodes}
        # urgent=红色(1), high=紫色(3), medium=黄色(6)
        assert separator_colors == {"1", "3", "6"}

        # 验证问题节点元数据
        question_nodes = [n for n in nodes if n["id"].startswith("question-")]
        assert len(question_nodes) == 7  # 7个薄弱概念

        # 验证第一个问题节点的元数据
        first_question = question_nodes[0]
        assert "conceptName" in first_question
        assert "conceptScore" in first_question
        assert "urgency" in first_question
        assert "clusterId" in first_question

        # 验证问题文本格式
        assert "请解释【" in first_question["text"]
        assert "当前分数:" in first_question["text"]

        # 验证黄色理解节点
        yellow_nodes = [n for n in nodes if n["color"] == "6" and n["id"].startswith("understanding-")]
        assert len(yellow_nodes) == 7  # 每个问题配套1个黄色节点

    def test_urgency_based_separator_colors(
        self,
        temp_canvas_file: str,
        sample_cluster_results: Dict
    ):
        """
        测试用例4: 验证紧急度颜色映射正确

        验证点:
        - urgent社区 → 红色分隔符 (color="1")
        - high社区 → 紫色分隔符 (color="3")
        - medium社区 → 黄色分隔符 (color="6")
        """
        # Arrange
        logic = CanvasBusinessLogic(temp_canvas_file)

        # Act
        result = logic.generate_review_canvas_file(
            cluster_results=sample_cluster_results
        )

        # 读取Canvas
        with open(result["review_canvas_path"], 'r', encoding='utf-8') as f:
            canvas_data = json.load(f)

        # 提取分隔符
        separators = [n for n in canvas_data["nodes"] if n["id"].startswith("separator-")]

        # 验证紧急度映射
        urgency_color_map = {
            "urgent": "1",   # 红色
            "high": "3",     # 紫色
            "medium": "6"    # 黄色
        }

        # 社区42 (urgent) → 红色分隔符
        cluster_42_sep = [s for s in separators if "社区42" in s["text"]][0]
        assert cluster_42_sep["color"] == urgency_color_map["urgent"]

        # 社区88 (high) → 紫色分隔符
        cluster_88_sep = [s for s in separators if "社区88" in s["text"]][0]
        assert cluster_88_sep["color"] == urgency_color_map["high"]

        # 社区99 (medium) → 黄色分隔符
        cluster_99_sep = [s for s in separators if "社区99" in s["text"]][0]
        assert cluster_99_sep["color"] == urgency_color_map["medium"]

    def test_performance_full_workflow_under_2_seconds(
        self,
        temp_canvas_file: str,
        sample_cluster_results: Dict
    ):
        """
        测试用例5: 性能测试 - 完整流程<2秒

        Story GDS.1 - Subtask 3.3

        验收标准: 端到端响应时间<2秒
        """
        # Arrange
        logic = CanvasBusinessLogic(temp_canvas_file)

        # Act
        start_time = time.time()
        result = logic.generate_review_canvas_file(
            cluster_results=sample_cluster_results
        )
        end_time = time.time()

        # Assert
        execution_time = end_time - start_time
        assert execution_time < 2.0, f"执行时间{execution_time:.2f}秒超过2秒阈值"

        # 验证返回的generation_time也在合理范围内
        assert result["generation_time"] < 2.0

    def test_backward_compatibility_with_story_4_3(
        self,
        temp_canvas_file: str
    ):
        """
        测试用例6: 验证向后兼容性 - Story 4.3原有功能不受影响

        验证点:
        1. clustered_questions参数仍然工作
        2. 生成的文件名不包含"薄弱点"
        3. 节点结构与原逻辑一致
        """
        # Arrange
        logic = CanvasBusinessLogic(temp_canvas_file)

        # Story 4.3格式的clustered_questions
        story_4_3_questions = {
            "逻辑基础": [
                {"question_text": "什么是逆否命题？"},
                {"question_text": "充分条件如何判断？"}
            ],
            "集合论": [
                {"question_text": "德摩根律的应用？"}
            ]
        }

        # Act
        result = logic.generate_review_canvas_file(
            clustered_questions=story_4_3_questions
        )

        # Assert - 验证文件名不包含"薄弱点"
        assert "薄弱点" not in result["review_canvas_path"]
        assert "检验白板" in result["review_canvas_path"]

        # 验证文件生成成功
        assert os.path.exists(result["review_canvas_path"])

        # 验证聚类数量和问题数量
        assert result["cluster_count"] == 2
        assert result["total_questions"] == 3

    def test_empty_cluster_results_handling(
        self,
        temp_canvas_file: str
    ):
        """
        测试用例7: 空聚类结果处理

        验证点:
        - 空clusters数组不会导致崩溃
        - 生成的Canvas只包含说明节点
        """
        # Arrange
        logic = CanvasBusinessLogic(temp_canvas_file)

        empty_cluster_results = {
            "trigger_point": 4,
            "trigger_name": "薄弱点聚类",
            "clusters": [],
            "total_weak_concepts": 0,
            "total_clusters": 0,
            "timestamp": "2025-01-15T10:30:00"
        }

        # Act
        result = logic.generate_review_canvas_file(
            cluster_results=empty_cluster_results
        )

        # Assert
        assert result["cluster_count"] == 0
        assert result["total_questions"] == 0
        assert os.path.exists(result["review_canvas_path"])

        # 验证Canvas只有说明节点
        with open(result["review_canvas_path"], 'r', encoding='utf-8') as f:
            canvas_data = json.load(f)

        # 只有1个说明节点
        assert len(canvas_data["nodes"]) == 1
        assert len(canvas_data["edges"]) == 0

    def test_validation_error_when_both_parameters_none(
        self,
        temp_canvas_file: str
    ):
        """
        测试用例8: 验证输入参数校验

        验证点:
        - clustered_questions和cluster_results都为None时抛出ValueError
        """
        # Arrange
        logic = CanvasBusinessLogic(temp_canvas_file)

        # Act & Assert
        with pytest.raises(ValueError, match="clustered_questions和cluster_results不能同时为空"):
            logic.generate_review_canvas_file(
                clustered_questions=None,
                cluster_results=None
            )

    def test_metadata_in_description_node(
        self,
        temp_canvas_file: str,
        sample_cluster_results: Dict
    ):
        """
        测试用例9: 验证说明节点元数据完整

        验证点:
        - triggerPoint = 4
        - triggerName = "薄弱点聚类"
        - originalCanvasPath正确
        - generationTimestamp存在
        """
        # Arrange
        logic = CanvasBusinessLogic(temp_canvas_file)

        # Act
        result = logic.generate_review_canvas_file(
            cluster_results=sample_cluster_results
        )

        # 读取Canvas
        with open(result["review_canvas_path"], 'r', encoding='utf-8') as f:
            canvas_data = json.load(f)

        # 提取说明节点
        description = [n for n in canvas_data["nodes"] if "薄弱点检验白板" in n.get("text", "")][0]

        # Assert
        assert description["triggerPoint"] == 4
        assert description["triggerName"] == "薄弱点聚类"
        assert description["originalCanvasPath"] == temp_canvas_file
        assert "generationTimestamp" in description

        # 验证说明文本包含关键信息
        text = description["text"]
        assert "艾宾浩斯触发点4" in text
        assert "薄弱概念总数: 7" in text
        assert "社区总数: 3" in text
        assert "检验问题: 7" in text
        assert "紧急度分布" in text
        assert "复习建议" in text


# ============================================================================
# Test Cases - Helper Functions
# ============================================================================

class TestHelperFunctions:
    """测试新增的辅助函数"""

    def test_convert_cluster_results_to_questions(
        self,
        temp_canvas_file: str,
        sample_cluster_results: Dict
    ):
        """
        测试_convert_cluster_results_to_questions()格式转换

        验证点:
        1. 返回Dict[str, List[Dict]]格式
        2. cluster_name格式正确
        3. question_text格式正确
        4. 包含所有必需字段
        """
        # Arrange
        logic = CanvasBusinessLogic(temp_canvas_file)

        # Act
        clustered_questions = logic._convert_cluster_results_to_questions(
            sample_cluster_results
        )

        # Assert - 验证返回类型
        assert isinstance(clustered_questions, dict)
        assert len(clustered_questions) == 3  # 3个社区

        # 验证cluster_name格式
        cluster_names = list(clustered_questions.keys())
        assert "社区42" in cluster_names[0]
        assert "紧急度: 紧急" in cluster_names[0]
        assert "平均分: 56.5" in cluster_names[0]

        # 验证问题列表
        cluster_42_questions = clustered_questions[cluster_names[0]]
        assert len(cluster_42_questions) == 2  # 2个概念

        # 验证问题结构
        first_question = cluster_42_questions[0]
        assert "question_text" in first_question
        assert "urgency" in first_question
        assert "cluster_id" in first_question
        assert "concept_name" in first_question
        assert "concept_score" in first_question

        # 验证问题文本格式
        assert "请解释【逆否命题】的核心原理和应用场景" in first_question["question_text"]
        assert "当前分数: 55" in first_question["question_text"]

    def test_generate_weak_point_review_canvas_filename(
        self,
        temp_canvas_file: str
    ):
        """
        测试_generate_weak_point_review_canvas_filename()文件名生成

        验证点:
        - 文件名格式: {basename}-薄弱点检验-{date}.canvas
        - 路径正确
        """
        # Arrange
        logic = CanvasBusinessLogic(temp_canvas_file)

        # Act
        filename = logic._generate_weak_point_review_canvas_filename()

        # Assert
        assert "薄弱点检验" in filename
        assert filename.endswith(".canvas")
        assert os.path.dirname(filename) == os.path.dirname(temp_canvas_file)

        # 验证日期格式 (YYYYMMDD)
        import re
        assert re.search(r"-\d{8}\.canvas$", filename) is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
