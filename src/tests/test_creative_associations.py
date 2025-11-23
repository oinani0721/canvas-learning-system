"""
创意联想引擎测试
Canvas Learning System - Story 8.8

测试创意洞察生成、类比推理、学习路径建议等功能。
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

# 导入测试目标
from creative_association_engine import (
    CreativeAssociationEngine, CreativeInsight, Analogy,
    LearningPath, LearningPathStep
)


class TestCreativeAssociationEngine:
    """创意联想引擎测试"""

    @pytest.fixture
    def engine(self):
        """创意联想引擎fixture"""
        with patch('creative_association_engine.MCPSemanticMemory'), \
             patch('creative_association_engine.NUMPY_AVAILABLE', True):
            return CreativeAssociationEngine()

    def test_initialization_with_memory_client(self):
        """测试使用记忆客户端初始化"""
        mock_memory_client = Mock()
        engine = CreativeAssociationEngine(mock_memory_client)

        assert engine.memory_client == mock_memory_client
        assert "creativity_levels" in engine.config
        assert "domains" in engine.config

    def test_initialization_without_memory_client(self):
        """测试不使用记忆客户端初始化"""
        with patch('creative_association_engine.NUMPY_AVAILABLE', True):
            engine = CreativeAssociationEngine()

        assert engine.memory_client is None
        assert isinstance(engine.config, dict)

    def test_get_default_config(self):
        """测试获取默认配置"""
        with patch('creative_association_engine.NUMPY_AVAILABLE', True):
            engine = CreativeAssociationEngine()
            config = engine._get_default_config()

        assert "creativity_levels" in config
        assert "conservative" in config["creativity_levels"]
        assert "moderate" in config["creativity_levels"]
        assert "creative" in config["creativity_levels"]

    def test_generate_creative_associations_moderate(self, engine):
        """测试生成中等创意联想"""
        with patch.object(engine, 'find_related_concepts', return_value=[
            {"concept": "逻辑推理", "similarity_score": 0.8}
        ]):
            result = engine.generate_creative_associations("逆否命题", "moderate")

        assert "association_id" in result
        assert result["query_concept"] == "逆否命题"
        assert result["creativity_level"] == "moderate"
        assert "creative_insights" in result
        assert "analogies" in result
        assert "practical_applications" in result
        assert "learning_paths" in result
        assert "overall_creativity_score" in result

    def test_generate_creative_associations_conservative(self, engine):
        """测试生成保守创意联想"""
        with patch.object(engine, 'find_related_concepts', return_value=[]):
            result = engine.generate_creative_associations("数学", "conservative")

        assert result["creativity_level"] == "conservative"
        # 保守级别应该产生较少的联想
        assert len(result["creative_insights"]) <= 5

    def test_generate_creative_associations_creative(self, engine):
        """测试生成高创意联想"""
        with patch.object(engine, 'find_related_concepts', return_value=[
            {"concept": "编程", "similarity_score": 0.6},
            {"concept": "哲学", "similarity_score": 0.5}
        ]):
            result = engine.generate_creative_associations("逻辑", "creative")

        assert result["creativity_level"] == "creative"
        # 创意级别应该产生更多的联想
        assert len(result["creative_insights"]) >= 5

    def test_generate_analogies(self, engine):
        """测试生成类比"""
        related_concepts = [
            {"concept": "编程", "similarity_score": 0.8},
            {"concept": "建造", "similarity_score": 0.7}
        ]

        analogies = engine._generate_analogies("逻辑", related_concepts, max_count=3)

        assert len(analogies) <= 3
        for analogy in analogies:
            assert isinstance(analogy, Analogy)
            assert analogy.source_concept == "逻辑"
            assert len(analogy.analogy_description) > 0
            assert 0 <= analogy.similarity_strength <= 1

    def test_generate_cross_domain_insights(self, engine):
        """测试生成跨域洞察"""
        related_concepts = [
            {"concept": "算法", "similarity_score": 0.8}
        ]

        insights = engine._generate_cross_domain_insights("数学", related_concepts, max_count=2)

        assert len(insights) <= 2
        for insight in insights:
            assert isinstance(insight, CreativeInsight)
            assert insight.insight_type == "cross_domain_connection"
            assert len(insight.domains_connected) >= 2

    def test_generate_practical_applications(self, engine):
        """测试生成实际应用"""
        related_concepts = [
            {"concept": "问题解决", "similarity_score": 0.7}
        ]

        applications = engine._generate_practical_applications("逻辑", related_concepts, max_count=2)

        assert len(applications) <= 2
        for app in applications:
            assert "title" in app
            assert "description" in app
            assert "steps" in app
            assert "scenarios" in app

    def test_generate_learning_paths(self, engine):
        """测试生成学习路径"""
        learning_paths = engine._generate_learning_paths("编程")

        assert len(learning_paths) == 3  # beginner, intermediate, advanced

        for path in learning_paths:
            assert isinstance(path, LearningPath)
            assert path.path_id.startswith("path-")
            assert len(path.steps) > 0
            assert len(path.learning_objectives) > 0
            assert path.estimated_duration_hours > 0

    def test_generate_learning_steps(self, engine):
        """测试生成学习步骤"""
        steps = engine._generate_learning_steps("Python", "beginner")

        assert len(steps) > 0
        for step in steps:
            assert isinstance(step, LearningPathStep)
            assert step.step_number >= 1
            assert step.estimated_duration_minutes > 0
            assert step.difficulty_level == "beginner"

    def test_calculate_overall_creativity(self, engine):
        """测试计算总体创意分数"""
        insights = [
            CreativeInsight("cross_domain", "test", 0.8, ["数学", "编程"], "high", 0.9),
            CreativeInsight("analogy_based", "test", 0.7, ["逻辑", "语言"], "medium", 0.8)
        ]
        analogies = [
            Analogy("概念A", "概念B", "test", 0.85, "test explanation")
        ]
        applications = [{"test": "application"}]

        creativity_score = engine._calculate_overall_creativity(insights, analogies, applications)

        assert 0 <= creativity_score <= 1
        assert creativity_score > 0  # 应该有非零创意分数


class TestDataStructures:
    """数据结构测试"""

    def test_creative_insight(self):
        """测试创意洞察数据类"""
        insight = CreativeInsight(
            insight_type="cross_domain_connection",
            insight="数学逻辑与编程算法有相似的结构",
            confidence=0.85,
            domains_connected=["数学", "计算机科学"],
            educational_value="high",
            creativity_score=0.9
        )

        assert insight.insight_type == "cross_domain_connection"
        assert insight.confidence == 0.85
        assert len(insight.domains_connected) == 2

    def test_analogy(self):
        """测试类比数据类"""
        analogy = Analogy(
            source_concept="逆否命题",
            target_concept="编程中的条件取反",
            analogy_description="逆否命题的逻辑结构类似于编程中的条件语句取反操作",
            similarity_strength=0.82,
            explanation="两者都涉及逻辑条件的否定和结果的反转"
        )

        assert analogy.source_concept == "逆否命题"
        assert analogy.similarity_strength == 0.82
        assert len(analogy.explanation) > 0

    def test_learning_path_step(self):
        """测试学习路径步骤数据类"""
        step = LearningPathStep(
            step_number=1,
            title="理解基本概念",
            description="学习逆否命题的定义和基本特征",
            estimated_duration_minutes=60,
            difficulty_level="beginner",
            prerequisites=[],
            resources=["教材", "视频教程"]
        )

        assert step.step_number == 1
        assert step.estimated_duration_minutes == 60
        assert step.difficulty_level == "beginner"
        assert len(step.resources) == 2

    def test_learning_path(self):
        """测试学习路径数据类"""
        steps = [
            LearningPathStep(
                step_number=1,
                title="基础学习",
                description="学习基础知识",
                estimated_duration_minutes=120,
                difficulty_level="beginner",
                prerequisites=[],
                resources=["教材"]
            )
        ]

        path = LearningPath(
            path_id="path-beginner-20250122",
            title="逆否命题入门学习路径",
            description="从基础开始学习逆否命题",
            total_steps=1,
            estimated_duration_hours=2.0,
            difficulty_level="beginner",
            steps=steps,
            learning_objectives=["理解逆否命题概念", "掌握基本应用"]
        )

        assert path.path_id == "path-beginner-20250122"
        assert path.estimated_duration_hours == 2.0
        assert len(path.learning_objectives) == 2


class TestIntegrationScenarios:
    """集成场景测试"""

    def test_full_creative_association_workflow(self):
        """测试完整创意联想工作流"""
        with patch('creative_association_engine.MCPSemanticMemory'), \
             patch('creative_association_engine.NUMPY_AVAILABLE', True):

            # 创建引擎
            engine = CreativeAssociationEngine()

            # 模拟相关概念
            with patch.object(engine, 'find_related_concepts', return_value=[
                {"concept": "编程算法", "similarity_score": 0.8},
                {"concept": "哲学逻辑", "similarity_score": 0.7}
            ]):

                # 生成创意联想
                result = engine.generate_creative_associations("数学逻辑", "moderate")

                # 验证结果结构
                required_keys = [
                    "association_id", "query_concept", "creativity_level",
                    "creative_insights", "analogies", "practical_applications",
                    "learning_paths", "overall_creativity_score"
                ]

                for key in required_keys:
                    assert key in result, f"Missing key: {key}"

                # 验证创意洞察
                assert len(result["creative_insights"]) > 0
                for insight in result["creative_insights"]:
                    assert "insight_type" in insight
                    assert "insight" in insight
                    assert "confidence" in insight

                # 验证类比
                assert len(result["analogies"]) > 0
                for analogy in result["analogies"]:
                    assert "source_concept" in analogy
                    assert "target_concept" in analogy
                    assert "analogy_description" in analogy

                # 验证学习路径
                assert len(result["learning_paths"]) == 3  # 三个难度级别
                for path in result["learning_paths"]:
                    assert "title" in path
                    assert "difficulty_level" in path
                    assert "steps" in path

    def test_error_handling_invalid_creativity_level(self):
        """测试无效创意级别的错误处理"""
        with patch('creative_association_engine.MCPSemanticMemory'), \
             patch('creative_association_engine.NUMPY_AVAILABLE', True):

            engine = CreativeAssociationEngine()

            with patch.object(engine, 'find_related_concepts', return_value=[]):
                result = engine.generate_creative_associations("概念", "invalid_level")

                # 应该回退到默认级别
                assert result["creativity_level"] == "moderate"

    def test_error_handling_no_memory_client(self):
        """测试没有记忆客户端的错误处理"""
        with patch('creative_association_engine.NUMPY_AVAILABLE', True):
            engine = CreativeAssociationEngine(memory_client=None)

            # 即使没有记忆客户端也应该能工作
            with patch.object(engine, 'find_related_concepts', return_value=[]):
                result = engine.generate_creative_associations("概念", "moderate")
                assert "creative_insights" in result

    def test_performance_large_concept_set(self):
        """测试处理大量概念的性能"""
        with patch('creative_association_engine.MCPSemanticMemory'), \
             patch('creative_association_engine.NUMPY_AVAILABLE', True):

            engine = CreativeAssociationEngine()

            # 模拟大量相关概念
            large_concept_set = [
                {"concept": f"概念{i}", "similarity_score": 0.7}
                for i in range(50)
            ]

            with patch.object(engine, 'find_related_concepts', return_value=large_concept_set):
                result = engine.generate_creative_associations("核心概念", "creative")

                # 应该限制结果数量
                assert len(result["creative_insights"]) <= 12  # creative级别的最大联想数
                assert len(result["analogies"]) <= 4          # 最大类比数


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])