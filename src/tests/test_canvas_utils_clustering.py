"""
Canvas Utils 单元测试 - 问题聚类功能 (Story 4.3)

测试 CanvasBusinessLogic 类的问题聚类方法
"""

import pytest
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from canvas_utils import CanvasBusinessLogic


class TestQuestionClustering:
    """测试问题聚类功能 (Story 4.3)"""

    @pytest.fixture
    def sample_questions_and_nodes(self):
        """包含多个主题的问题和节点示例数据"""
        questions = [
            {
                "source_node_id": "red-1",
                "question_text": "什么是逆否命题?",
                "question_type": "突破型",
                "difficulty": "基础",
                "guidance": "💡 从定义出发",
                "rationale": "帮助理解基础概念"
            },
            {
                "source_node_id": "red-2",
                "question_text": "逆否命题和原命题等价吗?",
                "question_type": "检验型",
                "difficulty": "深度",
                "guidance": "",
                "rationale": "检验是否真正理解"
            },
            {
                "source_node_id": "purple-1",
                "question_text": "什么是布尔代数?",
                "question_type": "突破型",
                "difficulty": "基础",
                "guidance": "💡 从集合运算类比",
                "rationale": "建立直观理解"
            },
            {
                "source_node_id": "purple-2",
                "question_text": "如何用布尔代数化简表达式?",
                "question_type": "应用型",
                "difficulty": "深度",
                "guidance": "",
                "rationale": "检验应用能力"
            }
        ]

        extracted_nodes = {
            "red_nodes": [
                {
                    "id": "red-1",
                    "content": "逆否命题定义",
                    "parent_nodes": [{"id": "material-1", "content": "命题逻辑基础"}],
                    "related_yellow": [],
                    "level": 1
                },
                {
                    "id": "red-2",
                    "content": "命题等价性",
                    "parent_nodes": [{"id": "material-1", "content": "命题逻辑基础"}],
                    "related_yellow": [],
                    "level": 1
                }
            ],
            "purple_nodes": [
                {
                    "id": "purple-1",
                    "content": "布尔代数定义",
                    "parent_nodes": [{"id": "material-2", "content": "布尔代数"}],
                    "related_yellow": [],
                    "level": 1
                },
                {
                    "id": "purple-2",
                    "content": "布尔表达式化简",
                    "parent_nodes": [{"id": "material-2", "content": "布尔代数"}],
                    "related_yellow": [],
                    "level": 1
                }
            ],
            "stats": {
                "red_count": 2,
                "purple_count": 2,
                "red_with_yellow": 0,
                "purple_with_yellow": 0
            }
        }

        return questions, extracted_nodes

    def test_cluster_questions_by_common_parent(self, sample_questions_and_nodes):
        """测试基于共同父节点聚类 (AC: 1)"""
        questions, extracted_nodes = sample_questions_and_nodes

        # Act
        logic = CanvasBusinessLogic("src/tests/fixtures/test-basic.canvas")
        clusters = logic.cluster_questions_by_topic(questions, extracted_nodes)

        # Assert: 应该聚类为至少2个主题
        assert len(clusters) >= 2, f"应至少有2个聚类,实际{len(clusters)}个"

        # 验证相关问题被聚到一起
        # 找到包含red-1和red-2的聚类
        found_common_cluster = False
        for topic, qs in clusters.items():
            q_ids = [q["source_node_id"] for q in qs]
            if "red-1" in q_ids and "red-2" in q_ids:
                found_common_cluster = True
                break

        assert found_common_cluster, "共同父节点的问题应聚类到一起"

    def test_topic_labels_are_clear(self, sample_questions_and_nodes):
        """测试主题标签清晰易懂 (AC: 3)"""
        questions, extracted_nodes = sample_questions_and_nodes

        # Act
        logic = CanvasBusinessLogic("src/tests/fixtures/test-basic.canvas")
        clusters = logic.cluster_questions_by_topic(questions, extracted_nodes)

        # Assert: 主题标签长度合理(2-10个字符)
        for topic in clusters.keys():
            assert 2 <= len(topic) <= 10, f"主题标签'{topic}'长度应为2-10字符"
            assert topic != "", "主题标签不能为空"

    def test_no_over_fragmentation(self):
        """测试不会过度细分 (AC: 4)"""
        # Arrange: 准备10个问题
        questions = []
        extracted_nodes = {"red_nodes": [], "purple_nodes": [], "stats": {}}

        for i in range(10):
            questions.append({
                "source_node_id": f"red-{i}",
                "question_text": f"问题{i}",
                "question_type": "突破型",
                "difficulty": "基础"
            })

            extracted_nodes["red_nodes"].append({
                "id": f"red-{i}",
                "content": f"内容{i}",
                "parent_nodes": [{"id": f"p{i//3}", "content": f"主题{i//3}"}],  # 3-4个问题共享一个父节点
                "related_yellow": [],
                "level": 1
            })

        # Act
        logic = CanvasBusinessLogic("src/tests/fixtures/test-basic.canvas")
        clusters = logic.cluster_questions_by_topic(questions, extracted_nodes)

        # Assert: 聚类数不应超过问题数的50%
        assert len(clusters) <= len(questions) / 2, \
            f"聚类数{len(clusters)}过多,问题数{len(questions)},比例{len(clusters)/len(questions)*100:.1f}%"

        # 验证大部分聚类有至少2个问题
        single_question_clusters = sum(1 for qs in clusters.values() if len(qs) == 1)
        assert single_question_clusters <= len(clusters) * 0.3, \
            f"过多孤立问题聚类({single_question_clusters}/{len(clusters)})"

    def test_cluster_layout_calculation(self):
        """测试聚类空间布局计算 (AC: 2)"""
        # Arrange
        clusters = {
            "命题逻辑": [{"q": 1}, {"q": 2}, {"q": 3}],  # 3个问题
            "布尔代数": [{"q": 4}, {"q": 5}]  # 2个问题
        }

        # Act
        logic = CanvasBusinessLogic("src/tests/fixtures/test-basic.canvas")
        layout = logic._calculate_cluster_layout(clusters, base_x=100, base_y=200)

        # Assert
        assert "命题逻辑" in layout
        assert "布尔代数" in layout

        # 验证第一个聚类位置
        assert layout["命题逻辑"]["x"] == 100
        assert layout["命题逻辑"]["y"] == 200

        # 验证聚类高度计算 (3个问题 * 380px)
        assert layout["命题逻辑"]["height"] == 3 * 380

        # 验证聚类间有间隔 (至少100px)
        cluster1_end = layout["命题逻辑"]["y"] + layout["命题逻辑"]["height"]
        cluster2_start = layout["布尔代数"]["y"]
        gap = cluster2_start - cluster1_end
        assert gap >= 100, f"聚类间隔{gap}px应≥100px"

    def test_handles_empty_parent_nodes(self):
        """测试处理没有父节点的问题"""
        # Arrange: 问题没有父节点信息
        questions = [
            {
                "source_node_id": "red-1",
                "question_text": "孤立问题",
                "question_type": "突破型",
                "difficulty": "基础"
            }
        ]

        extracted_nodes = {
            "red_nodes": [
                {
                    "id": "red-1",
                    "content": "孤立内容",
                    "parent_nodes": [],  # 空父节点列表
                    "related_yellow": [],
                    "level": 1
                }
            ],
            "purple_nodes": [],
            "stats": {"red_count": 1, "purple_count": 0}
        }

        # Act & Assert: 应该能正常处理,不抛出异常
        logic = CanvasBusinessLogic("src/tests/fixtures/test-basic.canvas")
        clusters = logic.cluster_questions_by_topic(questions, extracted_nodes)

        assert len(clusters) >= 1, "应至少有1个聚类(如'未分类')"

    def test_input_validation(self):
        """测试输入验证"""
        logic = CanvasBusinessLogic("src/tests/fixtures/test-basic.canvas")

        # 测试空问题列表
        with pytest.raises(ValueError, match="questions列表不能为空"):
            logic.cluster_questions_by_topic([], {"red_nodes": [], "purple_nodes": []})

        # 测试空extracted_nodes
        with pytest.raises(ValueError, match="extracted_nodes不能为空"):
            logic.cluster_questions_by_topic([{"q": 1}], {})

        # 测试缺少必要字段
        with pytest.raises(ValueError, match="缺少必要字段"):
            logic.cluster_questions_by_topic(
                [{"source_node_id": "red-1"}],  # 缺少question_text
                {"red_nodes": [], "purple_nodes": []}
            )

    def test_extract_question_topics(self, sample_questions_and_nodes):
        """测试主题提取方法"""
        questions, extracted_nodes = sample_questions_and_nodes

        # Act
        logic = CanvasBusinessLogic("src/tests/fixtures/test-basic.canvas")
        question_topics = logic._extract_question_topics(questions, extracted_nodes)

        # Assert
        assert "red-1" in question_topics
        assert "red-2" in question_topics
        assert "purple-1" in question_topics
        assert "purple-2" in question_topics

        # 验证来自同一父节点的问题有相同主题
        assert question_topics["red-1"] == question_topics["red-2"], \
            "共同父节点的问题应有相同主题"

    def test_merge_small_clusters(self):
        """测试合并小聚类功能"""
        logic = CanvasBusinessLogic("src/tests/fixtures/test-basic.canvas")

        # Arrange: 包含一些单问题聚类
        clusters = {
            "主题A": [{"q": 1}, {"q": 2}, {"q": 3}],
            "主题B": [{"q": 4}],  # 单个问题
            "主题C": [{"q": 5}, {"q": 6}],
            "主题D": [{"q": 7}]   # 单个问题
        }

        # Act
        merged = logic._merge_small_clusters(clusters, min_size=2)

        # Assert
        # 单问题聚类应被合并到"未分类"
        assert "未分类" in merged
        assert len(merged["未分类"]) >= 2  # 至少包含主题B和主题D的问题

    def test_refine_topic_labels(self):
        """测试优化主题标签功能"""
        logic = CanvasBusinessLogic("src/tests/fixtures/test-basic.canvas")

        # Arrange
        clusters = {
            "命题逻辑基": [
                {"source_node_id": "r1", "question_text": "什么是逆否命题?"},
                {"source_node_id": "r2", "question_text": "什么是原命题?"}
            ],
            "未分类": [
                {"source_node_id": "r3", "question_text": "其他问题"}
            ]
        }

        # Act
        refined = logic._refine_topic_labels(clusters)

        # Assert
        # 未分类标签应保持不变
        assert "未分类" in refined

        # 所有标签长度应在2-10个字符
        for topic in refined.keys():
            assert 2 <= len(topic) <= 10, f"标签'{topic}'长度不合规"

    def test_clustering_preserves_question_data(self, sample_questions_and_nodes):
        """测试聚类过程保留完整的问题数据"""
        questions, extracted_nodes = sample_questions_and_nodes

        # Act
        logic = CanvasBusinessLogic("src/tests/fixtures/test-basic.canvas")
        clusters = logic.cluster_questions_by_topic(questions, extracted_nodes)

        # Assert: 验证所有问题都被保留
        total_clustered = sum(len(qs) for qs in clusters.values())
        assert total_clustered == len(questions), \
            f"聚类后问题数({total_clustered})应等于原问题数({len(questions)})"

        # 验证问题的所有字段都被保留
        for topic, qs in clusters.items():
            for q in qs:
                assert "source_node_id" in q
                assert "question_text" in q
                assert "question_type" in q
                assert "difficulty" in q
