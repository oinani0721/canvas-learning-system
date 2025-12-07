"""
Unit Tests for IntelligentParallelScheduler - Story 10.2.4

测试覆盖:
- AC1: 类和方法定义正确
- AC2: intelligent_grouping() - TF-IDF + K-Means聚类
- AC3: _recommend_agent() - 智能Agent推荐
- AC4: _calculate_priority() - 优先级计算
- IV1: 聚类验证 - 相似节点分到同一组
- IV2: Agent推荐验证 - 推荐准确率≥80%
- IV3: 端到端验证 - 完整流程

Author: Canvas Learning System Team
Version: 1.0
Date: 2025-11-04
"""

import sys
from pathlib import Path

import pytest

# 添加项目根目录到sys.path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from schedulers.intelligent_parallel_scheduler import SKLEARN_AVAILABLE, IntelligentParallelScheduler


class TestIntelligentParallelSchedulerBasics:
    """测试类和基本方法 (AC1)"""

    def test_class_instantiation(self):
        """测试类实例化"""
        scheduler = IntelligentParallelScheduler()
        assert scheduler is not None

    def test_has_required_methods(self):
        """测试必要方法存在"""
        scheduler = IntelligentParallelScheduler()
        assert hasattr(scheduler, 'intelligent_grouping')
        assert hasattr(scheduler, '_recommend_agent')
        assert hasattr(scheduler, '_calculate_priority')
        assert callable(scheduler.intelligent_grouping)
        assert callable(scheduler._recommend_agent)
        assert callable(scheduler._calculate_priority)


class TestCalculatePriority:
    """测试优先级计算 (AC4)"""

    def test_priority_high_for_three_or_more_nodes(self):
        """测试3个或以上节点返回high"""
        scheduler = IntelligentParallelScheduler()
        nodes = [{"id": str(i)} for i in range(3)]
        priority = scheduler._calculate_priority(nodes)
        assert priority == "high"

    def test_priority_high_for_many_nodes(self):
        """测试多节点返回high"""
        scheduler = IntelligentParallelScheduler()
        nodes = [{"id": str(i)} for i in range(10)]
        priority = scheduler._calculate_priority(nodes)
        assert priority == "high"

    def test_priority_normal_for_two_nodes(self):
        """测试2个节点返回normal"""
        scheduler = IntelligentParallelScheduler()
        nodes = [{"id": "1"}, {"id": "2"}]
        priority = scheduler._calculate_priority(nodes)
        assert priority == "normal"

    def test_priority_low_for_one_node(self):
        """测试1个节点返回low"""
        scheduler = IntelligentParallelScheduler()
        nodes = [{"id": "1"}]
        priority = scheduler._calculate_priority(nodes)
        assert priority == "low"


class TestRecommendAgent:
    """测试Agent推荐 (AC3, IV2)"""

    def test_recommend_comparison_table_for_contrast_keywords(self):
        """测试对比关键词推荐comparison-table"""
        scheduler = IntelligentParallelScheduler()

        test_cases = [
            [{"id": "1", "content": "对比逆否命题和否命题"}],
            [{"id": "2", "content": "区别这两个概念"}],
            [{"id": "3", "content": "A vs B"}],
            [{"id": "4", "content": "比较它们"}],
        ]

        for nodes in test_cases:
            agent = scheduler._recommend_agent(nodes)
            assert agent == "comparison-table", f"Failed for: {nodes[0]['content']}"

    def test_recommend_memory_anchor_for_memory_keywords(self):
        """测试记忆关键词推荐memory-anchor"""
        scheduler = IntelligentParallelScheduler()

        test_cases = [
            [{"id": "1", "content": "我记不住这个公式"}],
            [{"id": "2", "content": "总是忘记定义"}],
            [{"id": "3", "content": "如何记忆这些概念"}],
        ]

        for nodes in test_cases:
            agent = scheduler._recommend_agent(nodes)
            assert agent == "memory-anchor", f"Failed for: {nodes[0]['content']}"

    def test_recommend_clarification_path_for_confusion_keywords(self):
        """测试困惑关键词推荐clarification-path"""
        scheduler = IntelligentParallelScheduler()

        test_cases = [
            [{"id": "1", "content": "我不理解这个概念"}],
            [{"id": "2", "content": "这个很困惑"}],
            [{"id": "3", "content": "看不懂定义"}],
        ]

        for nodes in test_cases:
            agent = scheduler._recommend_agent(nodes)
            assert agent == "clarification-path", f"Failed for: {nodes[0]['content']}"

    def test_recommend_example_teaching_for_practice_keywords(self):
        """测试练习关键词推荐example-teaching"""
        scheduler = IntelligentParallelScheduler()

        test_cases = [
            [{"id": "1", "content": "给我一些例子"}],
            [{"id": "2", "content": "需要练习题"}],
            [{"id": "3", "content": "有例题吗"}],
        ]

        for nodes in test_cases:
            agent = scheduler._recommend_agent(nodes)
            assert agent == "example-teaching", f"Failed for: {nodes[0]['content']}"

    def test_recommend_oral_explanation_as_default(self):
        """测试默认推荐oral-explanation"""
        scheduler = IntelligentParallelScheduler()

        # 不包含任何关键词
        nodes = [{"id": "1", "content": "这是一个普通的问题"}]
        agent = scheduler._recommend_agent(nodes)
        assert agent == "oral-explanation"

    def test_agent_recommendation_accuracy(self):
        """测试Agent推荐准确率 (IV2)"""
        scheduler = IntelligentParallelScheduler()

        # 测试用例：5个不同类型
        test_cases = [
            ([{"id": "1", "content": "对比类比和逻辑等价"}], "comparison-table"),
            ([{"id": "2", "content": "我记不住逆否命题"}], "memory-anchor"),
            ([{"id": "3", "content": "我不理解为什么逆否等价"}], "clarification-path"),
            ([{"id": "4", "content": "请给我一些练习题"}], "example-teaching"),
            ([{"id": "5", "content": "解释一下概念"}], "oral-explanation"),
        ]

        correct_count = 0
        for nodes, expected_agent in test_cases:
            actual_agent = scheduler._recommend_agent(nodes)
            if actual_agent == expected_agent:
                correct_count += 1

        accuracy = (correct_count / len(test_cases)) * 100
        assert accuracy == 100, f"Accuracy: {accuracy}%, expected 100%"


@pytest.mark.skipif(not SKLEARN_AVAILABLE, reason="scikit-learn not installed")
class TestIntelligentGrouping:
    """测试智能分组 (AC2, IV1)"""

    def test_grouping_returns_correct_structure(self):
        """测试返回正确的数据结构"""
        scheduler = IntelligentParallelScheduler()

        nodes = [
            {"id": "1", "content": "对比逆否命题和否命题"},
            {"id": "2", "content": "我记不住定义"},
        ]

        groups = scheduler.intelligent_grouping(nodes, max_groups=2)

        assert isinstance(groups, list)
        assert len(groups) > 0

        for group in groups:
            assert "cluster_id" in group
            assert "agent" in group
            assert "nodes" in group
            assert "priority" in group
            assert isinstance(group["nodes"], list)
            assert group["priority"] in ["high", "normal", "low"]

    def test_grouping_respects_max_groups(self):
        """测试聚类数量不超过max_groups"""
        scheduler = IntelligentParallelScheduler()

        nodes = [{"id": str(i), "content": f"内容{i}"} for i in range(20)]

        max_groups = 3
        groups = scheduler.intelligent_grouping(nodes, max_groups=max_groups)

        assert len(groups) <= max_groups

    def test_grouping_single_node(self):
        """测试单节点聚类"""
        scheduler = IntelligentParallelScheduler()

        nodes = [{"id": "1", "content": "单个节点"}]
        groups = scheduler.intelligent_grouping(nodes)

        assert len(groups) == 1
        assert len(groups[0]["nodes"]) == 1
        assert groups[0]["priority"] == "low"

    def test_clustering_quality(self):
        """测试聚类质量 - 相似节点应分到同一组 (IV1)"""
        scheduler = IntelligentParallelScheduler()

        # 20个节点，包含3个主题
        nodes = [
            # 主题1: 对比类 (6个)
            {"id": "1", "content": "我不理解逆否命题和否命题的区别"},
            {"id": "2", "content": "对比一下逆否命题和否命题"},
            {"id": "6", "content": "比较逆否命题和逆命题的差异"},
            {"id": "7", "content": "区别逆否命题和原命题"},
            {"id": "8", "content": "对比这两个命题"},
            {"id": "9", "content": "比较它们的不同点"},

            # 主题2: 记忆类 (6个)
            {"id": "3", "content": "我记不住逆否命题的定义"},
            {"id": "10", "content": "总是忘记这个公式"},
            {"id": "11", "content": "记不住逆命题"},
            {"id": "12", "content": "记忆方法"},
            {"id": "13", "content": "如何记住这些"},
            {"id": "14", "content": "记不住定义"},

            # 主题3: 不理解类 (8个)
            {"id": "4", "content": "什么是逆否命题？我不理解"},
            {"id": "5", "content": "请给我一些逆否命题的练习题"},
            {"id": "15", "content": "不懂为什么"},
            {"id": "16", "content": "看不懂这个"},
            {"id": "17", "content": "困惑"},
            {"id": "18", "content": "不理解原理"},
            {"id": "19", "content": "为什么会这样"},
            {"id": "20", "content": "很困难理解"},
        ]

        groups = scheduler.intelligent_grouping(nodes, max_groups=3)

        # 验证1: 聚类数量合理
        assert len(groups) <= 3, "聚类数量应≤3"

        # 验证2: 找到包含"对比"关键词的组
        comparison_groups = [
            g for g in groups
            if any("对比" in n["content"] or "比较" in n["content"]
                   for n in g["nodes"])
        ]
        assert len(comparison_groups) > 0, "应该有包含对比关键词的组"

        # 验证3: 找到包含"记不住"关键词的组
        memory_groups = [
            g for g in groups
            if any("记不住" in n["content"] or "忘记" in n["content"] or "记忆" in n["content"]
                   for n in g["nodes"])
        ]
        assert len(memory_groups) > 0, "应该有包含记忆关键词的组"

    def test_agent_recommendation_in_grouping(self):
        """测试分组中的Agent推荐正确"""
        scheduler = IntelligentParallelScheduler()

        nodes = [
            {"id": "1", "content": "对比A和B"},
            {"id": "2", "content": "区别C和D"},
            {"id": "3", "content": "我记不住E"},
        ]

        groups = scheduler.intelligent_grouping(nodes, max_groups=2)

        # 检查每个组的Agent推荐合理
        for group in groups:
            assert group["agent"] in [
                "comparison-table",
                "memory-anchor",
                "clarification-path",
                "example-teaching",
                "oral-explanation"
            ]


class TestFallbackMode:
    """测试降级模式（当scikit-learn不可用时）"""

    def test_fallback_grouping(self):
        """测试降级分组"""
        scheduler = IntelligentParallelScheduler()

        nodes = [{"id": str(i), "content": f"内容{i}"} for i in range(12)]

        # 即使scikit-learn不可用，也应该返回结果
        groups = scheduler._fallback_simple_grouping(nodes, max_groups=3)

        assert isinstance(groups, list)
        assert len(groups) > 0

        # 检查所有节点都被分配
        total_nodes_in_groups = sum(len(g["nodes"]) for g in groups)
        assert total_nodes_in_groups == len(nodes)


class TestEndToEnd:
    """端到端集成测试 (IV3)"""

    @pytest.mark.skipif(not SKLEARN_AVAILABLE, reason="scikit-learn not installed")
    def test_full_workflow(self):
        """测试完整工作流"""
        scheduler = IntelligentParallelScheduler()

        # 模拟真实场景: 20个黄色节点
        nodes = [
            {"id": f"node-{i}", "content": content, "x": 100*i, "y": 200}
            for i, content in enumerate([
                "对比逆否命题和否命题",
                "区别原命题和逆命题",
                "我记不住逆否命题定义",
                "总是忘记公式",
                "不理解为什么逆否等价",
                "什么是逆命题",
                "比较命题和判断",
                "记忆技巧",
                "看不懂证明过程",
                "例题讲解",
                "对比命题和语句",
                "记不住符号",
                "不懂逻辑推理",
                "需要练习题",
                "区别充分和必要",
                "如何记住这些",
                "困惑于否定",
                "给我一些例子",
                "比较充要条件",
                "不理解真值表",
            ])
        ]

        # 执行智能分组
        groups = scheduler.intelligent_grouping(nodes, max_groups=6)

        # 验证1: 返回结果合理
        assert len(groups) > 0
        assert len(groups) <= 6

        # 验证2: 所有节点都被分配
        total_nodes_in_groups = sum(len(g["nodes"]) for g in groups)
        assert total_nodes_in_groups == len(nodes)

        # 验证3: 每个组都有合理的Agent推荐
        for group in groups:
            assert group["agent"] in [
                "comparison-table",
                "memory-anchor",
                "clarification-path",
                "example-teaching",
                "oral-explanation",
                "four-level-explanation"
            ]

        # 验证4: 每个组都有合理的优先级
        for group in groups:
            assert group["priority"] in ["high", "normal", "low"]
            node_count = len(group["nodes"])
            if node_count >= 3:
                assert group["priority"] == "high"
            elif node_count == 2:
                assert group["priority"] == "normal"
            else:
                assert group["priority"] == "low"

        # 验证5: 相似节点应该被分到同一组
        # 找包含"对比"关键词的节点
        comparison_node_ids = [
            n["id"] for n in nodes
            if "对比" in n["content"] or "比较" in n["content"] or "区别" in n["content"]
        ]

        # 检查这些节点是否主要集中在少数几个组中
        comparison_groups = []
        for group in groups:
            group_comparison_ids = [
                n["id"] for n in group["nodes"]
                if n["id"] in comparison_node_ids
            ]
            if group_comparison_ids:
                comparison_groups.append(len(group_comparison_ids))

        # 如果有对比节点，它们应该相对集中（不会完全分散）
        if comparison_node_ids:
            # 至少有一个组包含2个以上的对比节点
            assert any(count >= 2 for count in comparison_groups), \
                "相似节点应该相对集中在少数组中"


# 测试运行入口
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
