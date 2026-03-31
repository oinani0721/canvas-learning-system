"""
动态检验白板系统测试
Story 8.16 - 完善动态检验白板生成功能

Author: Canvas Learning System Team
Version: 1.0 (Story 8.16)
Created: 2025-01-22
"""

import os

# 导入要测试的模块
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from critical_nodes_extractor import (
    CriticalNode,
    CriticalNodesExtractor,
    SourceAnalysis,
)
from dynamic_review_canvas_generator import DynamicReviewCanvasGenerator
from intelligent_question_generator import (
    GeneratedQuestion,
    IntelligentQuestionGenerator,
    QuestionGenerationConfig,
)
from knowledge_graph_integration import KnowledgeGraphContext, KnowledgeGraphIntegration
from learning_cycle_manager import LearningCycleManager, LearningStep


class TestCriticalNodesExtractor(unittest.TestCase):
    """测试关键节点提取器"""

    def setUp(self):
        self.extractor = CriticalNodesExtractor()
        self.test_canvas_data = {
            "nodes": [
                {
                    "id": "node-001",
                    "type": "text",
                    "text": "逻辑等价性是命题逻辑中的重要概念",
                    "color": "4",  # 红色
                    "x": 100,
                    "y": 100,
                    "width": 400,
                    "height": 300,
                },
                {
                    "id": "node-002",
                    "type": "text",
                    "text": "集合运算包括并集、交集等基本操作",
                    "color": "3",  # 紫色
                    "x": 200,
                    "y": 200,
                    "width": 400,
                    "height": 300,
                },
                {
                    "id": "node-003",
                    "type": "text",
                    "text": "简短",
                    "color": "4",
                    "x": 300,
                    "y": 300,
                    "width": 200,
                    "height": 100,
                },
            ],
            "edges": [],
        }

    @patch("os.path.exists")
    def test_extract_critical_nodes_success(self, mock_exists):
        """测试成功提取关键节点"""
        mock_exists.return_value = True  # Mock file existence check

        # Mock the local CanvasJSONOperator.read_canvas method
        with patch(
            "critical_nodes_extractor.CanvasJSONOperator.read_canvas"
        ) as mock_read:
            mock_read.return_value = self.test_canvas_data

            analysis = self.extractor.extract_critical_nodes("test_canvas.canvas")

            self.assertIsInstance(analysis, SourceAnalysis)
            self.assertEqual(
                len(analysis.critical_nodes_extracted), 2
            )  # 应该提取2个节点（排除太短的）
            self.assertEqual(analysis.total_source_nodes, 3)

    def test_calculate_color_score(self):
        """测试颜色评分计算"""
        red_node = {"color": "4"}
        purple_node = {"color": "3"}
        other_node = {"color": "2"}

        red_score = self.extractor._calculate_color_score(red_node)
        purple_score = self.extractor._calculate_color_score(purple_node)
        other_score = self.extractor._calculate_color_score(other_node)

        self.assertEqual(red_score, 1.0)
        self.assertEqual(purple_score, 0.8)
        self.assertEqual(other_score, 0.3)


class TestKnowledgeGraphIntegration(unittest.TestCase):
    """测试知识图谱集成"""

    def setUp(self):
        self.integration = KnowledgeGraphIntegration()

    def test_analyze_concept_context_fallback(self):
        """测试fallback分析"""
        concepts = ["逻辑等价性", "集合运算"]
        canvas_data = {"nodes": [], "edges": []}

        context = self.integration.analyze_concept_context(concepts, canvas_data)

        self.assertIsInstance(context, KnowledgeGraphContext)
        self.assertEqual(len(context.related_concepts), 2)
        self.assertIn("逻辑等价性", context.related_concepts)
        self.assertIn("集合运算", context.related_concepts)

    def test_calculate_text_similarity(self):
        """测试文本相似度计算"""
        text1 = "hello world test"
        text2 = "hello world example"
        text3 = "completely different text"

        similarity_1_2 = self.integration._calculate_text_similarity(text1, text2)
        similarity_1_3 = self.integration._calculate_text_similarity(text1, text3)

        self.assertGreater(
            similarity_1_2, 0.0
        )  # Should have some similarity due to common words
        self.assertEqual(similarity_1_3, 0.0)  # Should have no similarity


class TestIntelligentQuestionGenerator(unittest.TestCase):
    """测试智能问题生成器"""

    def setUp(self):
        self.config = QuestionGenerationConfig(max_questions_per_node=2)
        self.generator = IntelligentQuestionGenerator(config=self.config)

    def test_generate_review_questions(self):
        """测试生成检验问题"""
        test_nodes = [
            CriticalNode(
                node_id="test-001",
                color="4",
                concept_name="逻辑等价性",
                confidence_score=0.8,
                mastery_estimation=0.3,
                reason_for_critical="测试节点",
                text_content="逻辑等价性是命题逻辑中的重要概念",
            )
        ]

        questions = self.generator.generate_review_questions(test_nodes)

        self.assertIsInstance(questions, list)
        self.assertGreater(len(questions), 0)
        self.assertLessEqual(len(questions), 2)  # 不应超过max_questions_per_node

        for question in questions:
            self.assertIsInstance(question, GeneratedQuestion)
            self.assertIn("逻辑等价性", question.question_text)
            self.assertGreater(question.quality_score, 0)

    def test_determine_base_difficulty(self):
        """测试基础难度确定"""
        low_mastery_node = CriticalNode("test", "4", "概念", 0.8, 0.2, "测试")
        high_mastery_node = CriticalNode("test", "4", "概念", 0.8, 0.9, "测试")

        low_difficulty = self.generator._determine_base_difficulty(
            low_mastery_node, None
        )
        high_difficulty = self.generator._determine_base_difficulty(
            high_mastery_node, None
        )

        self.assertEqual(low_difficulty.value, "basic")
        self.assertEqual(high_difficulty.value, "expert")

    def test_estimate_time(self):
        """测试时间估算"""
        from intelligent_question_generator import DifficultyLevel, QuestionType

        basic_time = self.generator._estimate_time(
            DifficultyLevel.BASIC, QuestionType.CONCEPTUAL_UNDERSTANDING
        )
        advanced_time = self.generator._estimate_time(
            DifficultyLevel.ADVANCED, QuestionType.PROBLEM_SOLVING
        )

        self.assertGreater(advanced_time, basic_time)
        self.assertGreater(basic_time, 0)


class TestLearningCycleManager(unittest.TestCase):
    """测试学习循环管理器"""

    def setUp(self):
        self.test_canvas = "test_canvas.canvas"
        self.manager = LearningCycleManager(self.test_canvas)

    def test_step_definitions_initialization(self):
        """测试步骤定义初始化"""
        self.assertIn(LearningStep.STEP_1_UNDERSTANDING, self.manager.step_definitions)
        self.assertIn(LearningStep.STEP_8_SUMMARY, self.manager.step_definitions)

        step_1_def = self.manager.step_definitions[LearningStep.STEP_1_UNDERSTANDING]
        self.assertEqual(step_1_def.name, "填写理解")
        self.assertIn("填写黄色理解节点", step_1_def.description)

    def test_get_next_step(self):
        """测试获取下一步"""
        next_step = self.manager._get_next_step(LearningStep.STEP_1_UNDERSTANDING)
        self.assertEqual(next_step, LearningStep.STEP_2_SCORING)

        last_step_next = self.manager._get_next_step(LearningStep.STEP_8_SUMMARY)
        self.assertIsNone(last_step_next)

    def test_validate_user_input(self):
        """测试用户输入验证"""
        valid_input = {
            "yellow_node_understanding": "这是我的详细理解，包含足够的长度来满足验证要求",
            "node_id": "test-001",
        }
        invalid_input = {"yellow_node_understanding": "太短"}

        valid_result = self.manager._validate_user_input(
            LearningStep.STEP_1_UNDERSTANDING, valid_input
        )
        invalid_result = self.manager._validate_user_input(
            LearningStep.STEP_1_UNDERSTANDING, invalid_input
        )

        self.assertTrue(valid_result["valid"])
        self.assertFalse(invalid_result["valid"])


class TestDynamicReviewCanvasGenerator(unittest.TestCase):
    """测试动态检验白板生成器"""

    def setUp(self):
        self.generator = DynamicReviewCanvasGenerator()

    @patch("dynamic_review_canvas_generator.CanvasJSONOperator.read_canvas")
    @patch("dynamic_review_canvas_generator.Path")
    @patch("os.path.exists")
    def test_create_review_canvas_success(self, mock_exists, mock_path, mock_read):
        """测试成功创建检验白板"""
        # 设置mock
        mock_exists.return_value = True  # Mock file existence check
        mock_path.return_value.parent = Path("/tmp")
        mock_path.return_value.stem = "test_canvas"

        # Mock关键节点提取
        mock_analysis = SourceAnalysis(
            canvas_id="test-canvas",
            extraction_algorithm="test",
            total_source_nodes=5,
            critical_nodes_extracted=[
                CriticalNode("node-001", "4", "测试概念", 0.8, 0.3, "测试")
            ],
            knowledge_graph_context={},
        )

        # Mock问题生成
        mock_questions = [
            GeneratedQuestion(
                question_id="q-001",
                source_node_id="node-001",
                question_type="conceptual_understanding",
                difficulty_level="basic",
                question_text="请解释测试概念",
                expected_answer_type="explanation",
                estimated_time_minutes=10,
                hint_available=True,
            )
        ]

        # Mock Canvas读取
        mock_read.return_value = {"nodes": [], "edges": []}

        # 直接mock generator实例的组件
        self.generator.nodes_extractor.extract_critical_nodes = Mock(
            return_value=mock_analysis
        )
        self.generator.question_generator.generate_review_questions = Mock(
            return_value=mock_questions
        )

        with patch("builtins.open", create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.write = Mock()

            result = self.generator.create_review_canvas(
                "test_canvas.canvas", iteration=1
            )

            self.assertIsInstance(result, str)
            self.assertTrue(result.endswith(".canvas"))

    def test_load_config_default(self):
        """测试加载默认配置"""
        config = self.generator._load_config(None)

        self.assertIn("node_extraction", config)
        self.assertIn("question_generation", config)
        self.assertIn("knowledge_graph", config)
        self.assertIn("learning_cycle", config)

        # 检查默认值
        self.assertEqual(config["node_extraction"]["confidence_threshold"], 0.7)
        self.assertEqual(config["question_generation"]["max_questions_per_node"], 3)

    def test_calculate_quality_metrics(self):
        """测试质量指标计算"""
        from intelligent_question_generator import (
            DifficultyLevel,
            GeneratedQuestion,
            QuestionType,
        )

        test_questions = [
            GeneratedQuestion(
                question_id="q-001",
                source_node_id="node-001",
                question_type=QuestionType.CONCEPTUAL_UNDERSTANDING,
                difficulty_level=DifficultyLevel.BASIC,
                question_text="测试问题",
                expected_answer_type="explanation",
                estimated_time_minutes=10,
                hint_available=False,
                quality_score=0.8,
            )
        ]

        test_analysis = SourceAnalysis(
            canvas_id="test",
            extraction_algorithm="test",
            total_source_nodes=1,
            critical_nodes_extracted=[
                CriticalNode("node-001", "4", "测试", 0.8, 0.5, "测试")
            ],
            knowledge_graph_context={},
        )

        metrics = self.generator._calculate_quality_metrics(
            test_questions, test_analysis
        )

        self.assertIn("question_relevance", metrics)
        self.assertIn("difficulty_appropriateness", metrics)
        self.assertIn("learning_effectiveness", metrics)
        self.assertGreater(metrics["question_relevance"], 0)
        self.assertLessEqual(metrics["question_relevance"], 1.0)


class TestIntegrationWorkflow(unittest.TestCase):
    """测试集成工作流"""

    @patch("dynamic_review_canvas_generator.CanvasJSONOperator.read_canvas")
    @patch("dynamic_review_canvas_generator.Path")
    @patch("os.path.exists")
    def test_complete_workflow(self, mock_exists, mock_path, mock_read):
        """测试完整工作流"""
        # 设置mock
        mock_exists.return_value = True  # Mock file existence check
        mock_path.return_value.parent = Path("/tmp")
        mock_path.return_value.stem = "test_canvas"

        # 准备测试数据
        mock_analysis = SourceAnalysis(
            canvas_id="test",
            extraction_algorithm="test",
            total_source_nodes=3,
            critical_nodes_extracted=[
                CriticalNode("node-001", "4", "概念1", 0.8, 0.3, "测试"),
                CriticalNode("node-002", "3", "概念2", 0.7, 0.6, "测试"),
            ],
            knowledge_graph_context={},
        )

        mock_questions = [
            GeneratedQuestion(
                question_id="q-001",
                source_node_id="node-001",
                question_type="conceptual_understanding",
                difficulty_level="basic",
                question_text="问题1",
                expected_answer_type="explanation",
                estimated_time_minutes=10,
                hint_available=True,
                quality_score=0.85,
            ),
            GeneratedQuestion(
                question_id="q-002",
                source_node_id="node-002",
                question_type="application_scenario",
                difficulty_level="intermediate",
                question_text="问题2",
                expected_answer_type="example",
                estimated_time_minutes=15,
                hint_available=False,
                quality_score=0.75,
            ),
        ]

        mock_read.return_value = {"nodes": [], "edges": []}

        # 创建生成器
        generator = DynamicReviewCanvasGenerator()

        # 直接mock generator实例的组件
        generator.nodes_extractor.extract_critical_nodes = Mock(
            return_value=mock_analysis
        )
        generator.question_generator.generate_review_questions = Mock(
            return_value=mock_questions
        )

        with patch("builtins.open", create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.write = Mock()

            # 执行工作流
            result = generator.create_review_canvas("test_canvas.canvas", iteration=1)

            # 验证结果
            self.assertIsInstance(result, str)
            self.assertTrue(result.endswith(".canvas"))


def run_tests():
    """运行所有测试"""
    # 创建测试套件
    test_suite = unittest.TestSuite()

    # 添加测试类
    test_classes = [
        TestCriticalNodesExtractor,
        TestKnowledgeGraphIntegration,
        TestIntelligentQuestionGenerator,
        TestLearningCycleManager,
        TestDynamicReviewCanvasGenerator,
        TestIntegrationWorkflow,
    ]

    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    # 返回测试结果
    return result.wasSuccessful()


if __name__ == "__main__":
    print("运行动态检验白板系统测试...")
    success = run_tests()

    if success:
        print("\n🎉 所有测试通过！")
    else:
        print("\n❌ 部分测试失败，请检查实现。")
        sys.exit(1)
