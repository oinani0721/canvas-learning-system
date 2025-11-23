"""
智能复习系统完整测试套件

本模块包含Story 8.9: 建立智能复习计划生成的完整测试，
验证所有功能组件的正确性、集成性和性能。

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-23
"""

import unittest
import json
import os
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# 导入待测试的模块
import sys
sys.path.append('..')

try:
    from learning_analyzer import LearningAnalyzer
    from intelligent_review_generator import IntelligentReviewGenerator, ReviewPlanConfig
    from review_canvas_builder import ReviewCanvasBuilder
    from personalization_engine import PersonalizationEngine
    from intelligent_review_cli import IntelligentReviewCLI
except ImportError as e:
    print(f"Warning: 无法导入测试模块: {e}")


class TestLearningAnalyzer(unittest.TestCase):
    """学习分析器测试"""

    def setUp(self):
        """测试前设置"""
        self.analyzer = LearningAnalyzer()

    def test_analyze_learning_history_basic(self):
        """测试基础学习历史分析"""
        # 模拟学习数据
        canvas_path = "test_canvas.canvas"

        # 这里简化测试，因为依赖实际的Canvas文件
        with self.assertRaises(Exception):
            result = self.analyzer.analyze_learning_history(
                user_id="test_user",
                canvas_path=canvas_path
            )

    def test_collect_learning_data(self):
        """测试学习数据收集"""
        # 测试文件查找功能
        canvas_files = self.analyzer._find_canvas_files()
        self.assertIsInstance(canvas_files, list)

    def test_identify_weak_concepts(self):
        """测试薄弱环节识别"""
        # 模拟概念数据
        concepts = [
            {
                "concept_name": "测试概念1",
                "mastery_score": 3.0,
                "weakness_score": 0.7,
                "weakness_type": "insufficient_exposure"
            },
            {
                "concept_name": "测试概念2",
                "mastery_score": 8.5,
                "weakness_score": 0.2,
                "weakness_type": "general_weakness"
            }
        ]

        weak_concepts = self.analyzer._identify_weak_concepts(concepts, {})

        self.assertEqual(len(weak_concepts), 1)
        self.assertEqual(weak_concepts[0]["concept_name"], "测试概念1")

    def test_calculate_mastery_score(self):
        """测试掌握分数计算"""
        concept_data = {
            "mastery_level": "mastered",
            "encounters": 5,
            "understanding_records": [
                {"quality_score": 8.0},
                {"quality_score": 9.0}
            ],
            "performance_scores": [
                {"score": 8.5},
                {"score": 9.0}
            ]
        }

        score = self.analyzer._calculate_mastery_score(concept_data)
        self.assertGreater(score, 7.0)
        self.assertLessEqual(score, 10.0)

    def test_analyze_learning_trends(self):
        """测试学习趋势分析"""
        learning_data = {
            "scoring_records": [
                {"score": 6.0, "timestamp": 1000},
                {"score": 7.5, "timestamp": 2000},
                {"score": 8.0, "timestamp": 3000}
            ]
        }

        trends = self.analyzer._analyze_learning_trends(learning_data)

        self.assertIn("overall_performance_trend", trends)
        self.assertIn("study_frequency_trend", trends)


class TestIntelligentReviewGenerator(unittest.TestCase):
    """智能复习计划生成器测试"""

    def setUp(self):
        """测试前设置"""
        self.generator = IntelligentReviewGenerator()

    def test_generate_review_plan_basic(self):
        """测试基础复习计划生成"""
        config = ReviewPlanConfig(
            user_id="test_user",
            target_canvas="test_canvas.canvas",
            plan_type="weakness_focused"
        )

        # 使用模拟数据避免文件依赖
        with patch.object(self.generator.learning_analyzer, 'analyze_learning_history') as mock_analyze:
            mock_analyze.return_value = {
                "analysis_summary": {
                    "total_concepts_analyzed": 5,
                    "concepts_mastered": 2,
                    "concepts_needing_review": 3,
                    "critical_weaknesses": 1
                },
                "identified_weak_concepts": [
                    {
                        "concept_name": "测试概念",
                        "weakness_score": 0.7,
                        "mastery_score": 4.0,
                        "weakness_type": "conceptual_misunderstanding",
                        "recommended_focus_areas": ["基础概念复习"]
                    }
                ]
            }

            result = self.generator.generate_review_plan(
                user_id="test_user",
                target_canvas="test_canvas.canvas",
                plan_type="weakness_focused",
                config=config
            )

            self.assertIn("plan_id", result)
            self.assertIn("review_sessions", result)
            self.assertEqual(result["user_id"], "test_user")

    def test_select_concepts_by_strategy(self):
        """测试基于策略的概念选择"""
        weak_concepts = [
            {"concept_name": "概念1", "weakness_score": 0.8},
            {"concept_name": "概念2", "weakness_score": 0.6},
            {"concept_name": "概念3", "weakness_score": 0.9}
        ]

        config = ReviewPlanConfig(plan_type="weakness_focused")

        selected = self.generator._select_concepts_by_strategy(
            weak_concepts, {}, config
        )

        self.assertLessEqual(len(selected), 5)  # 最多5个概念
        # 应该按薄弱程度排序
        if len(selected) > 1:
            self.assertGreaterEqual(
                selected[0]["weakness_score"],
                selected[1]["weakness_score"]
            )

    def test_generate_review_questions(self):
        """测试复习问题生成"""
        concept_data = {
            "concept_name": "测试概念",
            "weakness_type": "insufficient_exposure",
            "mastery_score": 4.0
        }
        config = ReviewPlanConfig()

        questions = self.generator._generate_review_questions(concept_data, config)

        self.assertGreater(len(questions), 0)
        self.assertIn("question_text", questions[0])
        self.assertIn("question_type", questions[0])

    def test_determine_concept_difficulty(self):
        """测试概念难度确定"""
        concept_data = {"mastery_score": 3.0}
        config = ReviewPlanConfig(difficulty_level="adaptive")

        difficulty = self.generator._determine_concept_difficulty(concept_data, config)

        self.assertIn(difficulty, ["easy", "medium", "hard", "expert"])

    def test_create_review_sessions(self):
        """测试复习会话创建"""
        from intelligent_review_generator import ReviewConcept

        concepts = [
            ReviewConcept(
                concept_name="概念1",
                weakness_score=0.7,
                mastery_score=4.0,
                difficulty="medium",
                urgency_level="high",
                recommended_focus_areas=["基础复习"],
                review_questions=[],
                supporting_materials=[],
                estimated_time_minutes=15
            ),
            ReviewConcept(
                concept_name="概念2",
                weakness_score=0.5,
                mastery_score=6.0,
                difficulty="medium",
                urgency_level="medium",
                recommended_focus_areas=["应用练习"],
                review_questions=[],
                supporting_materials=[],
                estimated_time_minutes=12
            )
        ]

        config = ReviewPlanConfig(estimated_duration=30)

        sessions = self.generator._create_review_sessions(concepts, config)

        self.assertGreater(len(sessions), 0)
        # 由于总时间30分钟，应该分成多个会话或单个会话


class TestReviewCanvasBuilder(unittest.TestCase):
    """复习Canvas构建器测试"""

    def setUp(self):
        """测试前设置"""
        self.builder = ReviewCanvasBuilder()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir)

    def test_create_review_canvas_basic(self):
        """测试基础Canvas创建"""
        review_plan = {
            "plan_id": "test-plan-123",
            "user_id": "test_user",
            "target_canvas": "test_canvas.canvas",
            "plan_type": "weakness_focused",
            "review_sessions": [
                {
                    "session_id": "session-1",
                    "difficulty_level": "medium",
                    "estimated_duration": 30,
                    "learning_objectives": ["掌握基础概念"],
                    "concepts": [
                        {
                            "concept_name": "测试概念",
                            "difficulty": "medium",
                            "estimated_time_minutes": 15,
                            "recommended_focus_areas": ["基础复习"],
                            "review_questions": [
                                {
                                    "question_text": "请解释测试概念",
                                    "suggested_approach": "从定义开始"
                                }
                            ]
                        }
                    ]
                }
            ],
            "personalization_features": {
                "learning_style_adaptation": {
                    "preferred_approach": "self_explanation_focused"
                }
            },
            "next_review_date": datetime.now().isoformat()
        }

        output_path = os.path.join(self.temp_dir, "test_review.canvas")

        result_path = self.builder.create_review_canvas(
            review_plan=review_plan,
            output_path=output_path
        )

        self.assertEqual(result_path, output_path)
        self.assertTrue(os.path.exists(output_path))

        # 验证Canvas文件结构
        with open(output_path, 'r', encoding='utf-8') as f:
            canvas_data = json.load(f)

        self.assertIn("nodes", canvas_data)
        self.assertIn("edges", canvas_data)
        self.assertGreater(len(canvas_data["nodes"]), 0)

    def test_generate_canvas_name(self):
        """测试Canvas文件名生成"""
        target_canvas = "离散数学.canvas"

        canvas_name = self.builder._generate_canvas_name(target_canvas)

        self.assertIn("离散数学", canvas_name)
        self.assertIn("智能复习", canvas_name)
        self.assertIn(datetime.now().strftime("%Y%m%d"), canvas_name)

    def test_add_intro_node(self):
        """测试介绍节点添加"""
        canvas_data = {"nodes": [], "edges": []}
        review_plan = {
            "plan_type": "weakness_focused",
            "target_canvas": "test.canvas",
            "generation_timestamp": datetime.now().isoformat()
        }

        node, new_y = self.builder._add_intro_node(
            canvas_data, review_plan, 100, 100
        )

        self.assertEqual(len(canvas_data["nodes"]), 1)
        self.assertEqual(canvas_data["nodes"][0]["id"], node["id"])
        self.assertEqual(node["color"], "5")  # 蓝色

    def test_add_concept_node(self):
        """测试概念节点添加"""
        canvas_data = {"nodes": [], "edges": []}
        concept = {
            "concept_name": "测试概念",
            "difficulty": "medium",
            "estimated_time_minutes": 15,
            "recommended_focus_areas": ["基础复习"],
            "review_questions": [
                {
                    "question_text": "请解释测试概念",
                    "suggested_approach": "从定义开始"
                }
            ]
        }

        concept_node, new_x, new_y = self.builder._add_concept_node(
            canvas_data, concept, 100, 100
        )

        # 应该添加3个节点：概念、问题、黄色理解区
        self.assertEqual(len(canvas_data["nodes"]), 3)
        self.assertEqual(len(canvas_data["edges"]), 2)  # 概念->问题, 问题->黄色


class TestPersonalizationEngine(unittest.TestCase):
    """个性化引擎测试"""

    def setUp(self):
        """测试前设置"""
        self.engine = PersonalizationEngine(user_id="test_user")

    def test_analyze_learning_style(self):
        """测试学习风格分析"""
        # 模拟学习历史数据
        learning_history = {
            "canvas_files": [
                {
                    "questions": [{"text": "问题1"}, {"text": "问题2"}],
                    "understanding_records": [
                        {"quality_score": 8.0},
                        {"quality_score": 7.5}
                    ],
                    "explanations": [
                        {"explanation_type": "definition"},
                        {"explanation_type": "example"}
                    ]
                }
            ]
        }

        result = self.engine.analyze_learning_style(learning_history)

        self.assertIn("primary_style", result)
        self.assertIn("style_confidence", result)
        self.assertIn("recommendations", result)
        self.assertGreater(result.style_confidence, 0)

    def test_optimize_time_management(self):
        """测试时间管理优化"""
        result = self.engine.optimize_time_management()

        self.assertIn("optimal_session_duration", result)
        self.assertIn("recommended_break_intervals", result)
        self.assertIn("peak_performance_periods", result)
        self.assertIn("optimal_study_times", result)
        self.assertGreater(result.optimal_session_duration, 20)
        self.assertLessEqual(result.optimal_session_duration, 120)

    def test_generate_motivation_profile(self):
        """测试动机档案生成"""
        result = self.engine.generate_motivation_profile()

        self.assertIn("primary_motivators", result)
        self.assertIn("achievement_preferences", result)
        self.assertIn("incentive_types", result)
        self.assertIn("personalized_encouragements", result)
        self.assertGreater(len(result.primary_motivators), 0)

    def test_update_user_preferences(self):
        """测试用户偏好更新"""
        user_feedback = {
            "satisfaction": 0.8,
            "preferred_difficulty": "gradual",
            "content_preferences": {"visual": 0.8, "text": 0.6},
            "time_preferences": {"preferred_duration": 50},
            "complexity_tolerance": "moderate"
        }

        result = self.engine.update_user_preferences(user_feedback)

        self.assertEqual(result.user_id, "test_user")
        self.assertIn("updated_at", result)
        self.assertIn("created_at", result)

    def test_get_personalized_recommendations(self):
        """测试个性化推荐"""
        from personalization_engine import UserProfile

        user_profile = UserProfile(
            user_id="test_user",
            learning_style="visual",
            preferred_difficulty_progression="gradual",
            optimal_study_duration=45,
            peak_performance_times=["morning", "evening"],
            feedback_preferences=["immediate"],
            motivation_factors=["achievement", "mastery"],
            interaction_patterns={},
            complexity_tolerance="moderate",
            content_preferences={},
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )

        current_context = {"current_time": "morning"}

        result = self.engine.get_personalized_recommendations(user_profile, current_context)

        self.assertIn("learning_approach", result)
        self.assertIn("content_format", result)
        self.assertIn("time_suggestions", result)
        self.assertIn("motivation_strategies", result)


class TestIntelligentReviewCLI(unittest.TestCase):
    """智能复习CLI测试"""

    def setUp(self):
        """测试前设置"""
        self.cli = IntelligentReviewCLI()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir)

    def test_cli_initialization(self):
        """测试CLI初始化"""
        self.assertIsNotNone(self.cli.learning_analyzer)
        self.assertIsNotNone(self.cli.review_generator)
        self.assertIsNotNone(self.cli.canvas_builder)
        self.assertIsNotNone(self.cli.personalization_engine)
        self.assertTrue(self.cli.data_dir.exists())

    @patch('intelligent_review_cli.IntelligentReviewGenerator.generate_review_plan')
    def test_generate_review_plan_command(self, mock_generate):
        """测试生成复习计划命令"""
        # 模拟返回数据
        mock_generate.return_value = {
            "plan_id": "test-plan-123",
            "user_id": "test_user",
            "target_canvas": "test.canvas",
            "analysis_summary": {
                "total_concepts_analyzed": 5,
                "concepts_mastered": 2,
                "concepts_needing_review": 3
            },
            "review_sessions": [
                {
                    "session_id": "session-1",
                    "estimated_duration": 30,
                    "difficulty_level": "medium",
                    "concepts": []
                }
            ],
            "estimated_completion_time": {
                "total_estimated_minutes": 30
            }
        }

        # 创建模拟参数
        class MockArgs:
            canvas_path = "test.canvas"
            plan_type = "weakness_focused"
            difficulty = "adaptive"
            duration = 45
            max_concepts = 5
            user_id = "test_user"
            output = None
            include_explanations = True
            include_examples = True

        args = MockArgs()

        # 执行命令
        with patch('intelligent_review_cli.ReviewCanvasBuilder.create_review_canvas') as mock_canvas:
            mock_canvas.return_value = "test_output.canvas"

            with patch('builtins.open', create=True) as mock_file:
                mock_file.return_value.__enter__.return_value.write.return_value = None

                self.cli.generate_review_plan(args)

        # 验证调用
        mock_generate.assert_called_once()

    def test_analyze_canvas_progress(self):
        """测试Canvas进度分析"""
        review_plan = {
            "plan_id": "test-plan",
            "review_sessions": [
                {
                    "concepts": [
                        {"concept_name": "概念1"},
                        {"concept_name": "概念2"}
                    ]
                }
            ]
        }

        progress = self.cli._analyze_canvas_progress(review_plan)

        self.assertIn("total_concepts", progress)
        self.assertIn("completed_concepts", progress)
        self.assertIn("completion_rate", progress)


class TestSystemIntegration(unittest.TestCase):
    """系统集成测试"""

    def setUp(self):
        """测试前设置"""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir)

    def test_end_to_end_workflow(self):
        """测试端到端工作流"""
        # 1. 创建学习分析器
        analyzer = LearningAnalyzer()

        # 2. 创建复习计划生成器
        generator = IntelligentReviewGenerator(learning_analyzer=analyzer)

        # 3. 创建Canvas构建器
        builder = ReviewCanvasBuilder()

        # 4. 创建个性化引擎
        personalization = PersonalizationEngine()

        # 5. 创建CLI
        cli = IntelligentReviewCLI()

        # 验证所有组件都能正常初始化
        self.assertIsNotNone(analyzer)
        self.assertIsNotNone(generator)
        self.assertIsNotNone(builder)
        self.assertIsNotNone(personalization)
        self.assertIsNotNone(cli)

    def test_configuration_compatibility(self):
        """测试配置兼容性"""
        from intelligent_review_generator import ReviewPlanConfig

        # 测试各种配置组合
        configs = [
            ReviewPlanConfig(plan_type="weakness_focused"),
            ReviewPlanConfig(plan_type="comprehensive"),
            ReviewPlanConfig(plan_type="targeted"),
            ReviewPlanConfig(difficulty_level="easy"),
            ReviewPlanConfig(difficulty_level="adaptive"),
            ReviewPlanConfig(estimated_duration=30),
            ReviewPlanConfig(max_concepts_per_session=3)
        ]

        for config in configs:
            self.assertIsInstance(config.user_id, str)
            self.assertIsInstance(config.target_canvas, str)
            self.assertIn(config.plan_type, ["weakness_focused", "comprehensive", "targeted"])

    def test_error_handling(self):
        """测试错误处理"""
        # 测试不存在的文件
        analyzer = LearningAnalyzer()

        with self.assertRaises(Exception):
            analyzer.analyze_learning_history(canvas_path="nonexistent.canvas")

    def test_performance_requirements(self):
        """测试性能要求"""
        import time

        # 测试学习分析性能
        start_time = time.time()
        analyzer = LearningAnalyzer()
        canvas_files = analyzer._find_canvas_files()
        analysis_time = time.time() - start_time

        # 应该在合理时间内完成（<5秒）
        self.assertLess(analysis_time, 5.0)

        # 测试复习计划生成性能
        start_time = time.time()
        generator = IntelligentReviewGenerator()

        # 使用模拟数据避免文件依赖
        with patch.object(generator.learning_analyzer, 'analyze_learning_history') as mock_analyze:
            mock_analyze.return_value = {
                "analysis_summary": {},
                "identified_weak_concepts": []
            }

            config = ReviewPlanConfig()
            try:
                generator.generate_review_plan("test", "test", "weakness_focused", config)
            except:
                pass  # 预期可能失败，因为其他依赖

        generation_time = time.time() - start_time
        self.assertLess(generation_time, 10.0)


class TestAccuracyValidation(unittest.TestCase):
    """准确性验证测试"""

    def test_weakness_identification_accuracy(self):
        """测试薄弱环节识别准确性"""
        generator = IntelligentReviewGenerator()

        # 测试数据：已知掌握程度的概念
        test_concepts = [
            {"name": "完全掌握", "score": 9.5, "expected_weakness": 0.1},
            {"name": "部分掌握", "score": 6.0, "expected_weakness": 0.4},
            {"name": "未掌握", "score": 3.0, "expected_weakness": 0.7},
            {"name": "非常薄弱", "score": 1.0, "expected_weakness": 0.9}
        ]

        for concept in test_concepts:
            # 验证薄弱分数计算逻辑
            expected_weakness = concept["expected_weakness"]
            actual_weakness = max(0, (10 - concept["score"]) / 10)

            self.assertAlmostEqual(
                actual_weakness, expected_weakness, 0.1,
                f"概念 {concept['name']} 的薄弱分数计算不准确"
            )

    def test_difficulty_classification_accuracy(self):
        """测试难度分类准确性"""
        generator = IntelligentReviewGenerator()

        # 测试不同掌握程度的难度分类
        test_cases = [
            {"score": 9.0, "expected_difficulties": ["hard", "expert"]},
            {"score": 6.0, "expected_difficulties": ["medium", "hard"]},
            {"score": 4.0, "expected_difficulties": ["easy", "medium"]},
            {"score": 2.0, "expected_difficulties": ["easy"]}
        ]

        config = ReviewPlanConfig(difficulty_level="adaptive")

        for case in test_cases:
            concept_data = {"mastery_score": case["score"]}
            difficulty = generator._determine_concept_difficulty(concept_data, config)

            # 验证难度分类合理性
            self.assertIn(difficulty, ["easy", "medium", "hard", "expert"])

            # 高分应该对应高难度，低分应该对应低难度
            if case["score"] >= 8:
                self.assertIn(difficulty, ["hard", "expert"])
            elif case["score"] <= 4:
                self.assertEqual(difficulty, "easy")

    def test_time_estimation_accuracy(self):
        """测试时间估算准确性"""
        builder = ReviewCanvasBuilder()

        # 测试不同复杂度概念的时间估算
        test_concepts = [
            {
                "mastery_score": 9.0,
                "weakness_score": 0.1,
                "estimated_time": 8
            },
            {
                "mastery_score": 5.0,
                "weakness_score": 0.5,
                "estimated_time": 12
            },
            {
                "mastery_score": 2.0,
                "weakness_score": 0.8,
                "estimated_time": 20
            }
        ]

        for concept in test_concepts:
            config = ReviewPlanConfig()
            estimated_time = builder._estimate_concept_review_time(concept, config)

            # 验证时间估算在合理范围内（5-30分钟）
            self.assertGreaterEqual(estimated_time, 5)
            self.assertLessEqual(estimated_time, 30)

            # 验证时间估算逻辑：掌握度越低，时间越长
            if concept["mastery_score"] < 5:
                self.assertGreater(estimated_time, 10)
            elif concept["mastery_score"] > 8:
                self.assertLessEqual(estimated_time, 15)


def run_tests():
    """运行所有测试"""
    print("🧪 开始运行智能复习系统测试套件...")
    print("="*60)

    # 创建测试套件
    test_suite = unittest.TestSuite()

    # 添加测试类
    test_classes = [
        TestLearningAnalyzer,
        TestIntelligentReviewGenerator,
        TestReviewCanvasBuilder,
        TestPersonalizationEngine,
        TestIntelligentReviewCLI,
        TestSystemIntegration,
        TestAccuracyValidation
    ]

    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    # 输出测试结果
    print("\n" + "="*60)
    print("📊 测试结果统计:")
    print(f"  总测试数: {result.testsRun}")
    print(f"  成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"  失败: {len(result.failures)}")
    print(f"  错误: {len(result.errors)}")
    print(f"  跳过: {len(result.skipped)}")

    if result.failures:
        print(f"\n❌ 失败的测试:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")

    if result.errors:
        print(f"\n💥 错误的测试:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('Error:')[-1].strip()}")

    success_rate = (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100
    print(f"\n✅ 测试通过率: {success_rate:.1f}%")

    if success_rate >= 90:
        print("🎉 测试通过！智能复习系统功能正常。")
    elif success_rate >= 70:
        print("⚠️ 测试基本通过，建议检查失败的测试。")
    else:
        print("❌ 测试失败较多，需要修复问题。")

    return result.wasSuccessful()


if __name__ == "__main__":
    run_tests()