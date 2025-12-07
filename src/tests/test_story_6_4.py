"""
测试Story 6.4: 智能检验白板生成优化

Test Smart Review Board Generation (Story 6.4)
"""

import asyncio
import json
import os
import tempfile
from datetime import datetime, timedelta

import pytest

from canvas_utils import (
    COLOR_CODE_PURPLE,
    COLOR_CODE_RED,
    KnowledgeGraphLayer,
    SmartReviewBoardGenerator,
)


class TestSmartReviewBoardGeneration:
    """测试智能检验白板生成功能"""

    @pytest.fixture
    def setup_test_environment(self):
        """设置测试环境"""
        # 创建临时Canvas文件
        test_canvas_data = {
            "nodes": [
                {
                    "id": "material-001",
                    "type": "text",
                    "text": "逆否命题定义和基本性质",
                    "x": 100, "y": 100,
                    "width": 400, "height": 200,
                    "color": COLOR_CODE_RED
                },
                {
                    "id": "question-001",
                    "type": "text",
                    "text": "如何判断两个命题是否为逆否关系？",
                    "x": 600, "y": 150,
                    "width": 350, "height": 120,
                    "color": COLOR_CODE_RED
                },
                {
                    "id": "question-002",
                    "type": "text",
                    "text": "逆否命题在实际证明中的应用",
                    "x": 1000, "y": 150,
                    "width": 350, "height": 120,
                    "color": COLOR_CODE_PURPLE
                }
            ],
            "edges": [
                {
                    "id": "edge-001",
                    "fromNode": "material-001",
                    "toNode": "question-001",
                    "label": "基础拆解"
                },
                {
                    "id": "edge-002",
                    "fromNode": "material-001",
                    "toNode": "question-002",
                    "label": "应用拓展"
                }
            ]
        }

        # 创建临时文件
        temp_dir = tempfile.mkdtemp()
        canvas_path = os.path.join(temp_dir, "test-canvas.canvas")

        with open(canvas_path, 'w', encoding='utf-8') as f:
            json.dump(test_canvas_data, f, ensure_ascii=False, indent=2)

        # 初始化知识图谱层（模拟禁用状态）
        kg_layer = KnowledgeGraphLayer()
        kg_layer.enabled = False  # 测试时禁用知识图谱连接

        # 创建智能生成器
        smart_generator = SmartReviewBoardGenerator(kg_layer)

        yield {
            "kg_layer": kg_layer,
            "smart_generator": smart_generator,
            "canvas_path": canvas_path,
            "canvas_data": test_canvas_data,
            "temp_dir": temp_dir
        }

        # 清理
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_analyze_user_learning_state(self, setup_test_environment):
        """测试用户学习状态分析"""
        env = setup_test_environment

        # Act: 分析学习状态
        learning_analysis = await env["smart_generator"].analyze_user_learning_state(
            user_id="test-user",
            canvas_path=env["canvas_path"]
        )

        # Assert: 验证分析结果结构
        assert "user_id" in learning_analysis
        assert "canvas_id" in learning_analysis
        assert "canvas_data" in learning_analysis
        assert "node_progress" in learning_analysis
        assert "user_profile" in learning_analysis
        assert "bottlenecks" in learning_analysis
        assert "time_patterns" in learning_analysis
        assert "analysis_timestamp" in learning_analysis

        # 验证数据内容
        assert learning_analysis["user_id"] == "test-user"
        assert learning_analysis["canvas_id"] == env["canvas_path"]
        assert len(learning_analysis["canvas_data"]["nodes"]) == 3
        assert len(learning_analysis["canvas_data"]["edges"]) == 2

    @pytest.mark.asyncio
    async def test_select_review_nodes(self, setup_test_environment):
        """测试复习节点选择"""
        env = setup_test_environment

        # 准备学习分析数据
        learning_analysis = await env["smart_generator"].analyze_user_learning_state(
            user_id="test-user",
            canvas_path=env["canvas_path"]
        )

        # Act: 选择复习节点
        selected_nodes = await env["smart_generator"].select_review_nodes(
            learning_analysis=learning_analysis,
            options={"max_nodes": 5}
        )

        # Assert: 验证选择结果
        assert len(selected_nodes) > 0
        assert len(selected_nodes) <= 5

        # 验证节点类型（应该只包含红/紫色节点）
        for node in selected_nodes:
            assert node.get("color") in [COLOR_CODE_RED, COLOR_CODE_PURPLE]

        # 验证优先级排序
        if len(selected_nodes) > 1:
            scores = [await env["smart_generator"].calculate_review_priority(node, learning_analysis)
                     for node in selected_nodes]
            scores = [score["total_score"] for score in scores]
            assert scores == sorted(scores, reverse=True)

    @pytest.mark.asyncio
    async def test_generate_personalized_questions(self, setup_test_environment):
        """测试个性化问题生成"""
        env = setup_test_environment

        # 准备测试数据
        learning_analysis = await env["smart_generator"].analyze_user_learning_state(
            user_id="test-user",
            canvas_path=env["canvas_path"]
        )

        review_nodes = [
            {
                "id": "question-001",
                "text": "如何判断两个命题是否为逆否关系？",
                "color": COLOR_CODE_RED,
                "progress": {
                    "mastery_level": 25.0,
                    "difficulty_score": 7.0,
                    "review_count": 2
                }
            }
        ]

        # Act: 生成个性化问题
        questions = await env["smart_generator"].generate_personalized_questions(
            review_nodes=review_nodes,
            learning_analysis=learning_analysis
        )

        # Assert: 验证问题生成结果
        assert len(questions) > 0

        for question in questions:
            assert "question_text" in question
            assert "question_type" in question
            assert "difficulty" in question
            assert "source_node_id" in question
            assert "personalization" in question

            # 验证个性化信息
            personalization = question["personalization"]
            assert "based_on_mastery" in personalization
            assert "difficulty_adjustment" in personalization
            assert "learning_style_match" in personalization

    @pytest.mark.asyncio
    async def test_calculate_review_priority(self, setup_test_environment):
        """测试复习优先级计算"""
        env = setup_test_environment

        learning_analysis = await env["smart_generator"].analyze_user_learning_state(
            user_id="test-user",
            canvas_path=env["canvas_path"]
        )

        # 测试节点
        test_node = {
            "id": "test-node",
            "text": "测试节点",
            "color": COLOR_CODE_RED,
            "progress": {
                "mastery_level": 30.0,
                "review_count": 2,
                "last_interaction": datetime.now() - timedelta(days=5),
                "difficulty_score": 6.0,
                "error_rate": 0.3
            }
        }

        # Act: 计算优先级
        priority_result = await env["smart_generator"].calculate_review_priority(
            node=test_node,
            learning_analysis=learning_analysis
        )

        # Assert: 验证优先级结果
        assert "total_score" in priority_result
        assert "components" in priority_result

        components = priority_result["components"]
        assert "forgetting_score" in components
        assert "mastery_score" in components
        assert "difficulty_score" in components
        assert "error_score" in components
        assert "importance_score" in components
        assert "recency_score" in components

        # 验证分数范围
        assert 0 <= priority_result["total_score"] <= 1
        assert 0 <= components["forgetting_score"] <= 1
        assert 0 <= components["mastery_score"] <= 1

    def test_calculate_node_importance(self, setup_test_environment):
        """测试节点重要性计算"""
        env = setup_test_environment

        learning_analysis = {
            "canvas_data": env["canvas_data"]
        }

        # 测试不同类型的节点
        test_nodes = [
            {
                "id": "connected-node",
                "text": "这是一个连接度很高的节点内容，足够长来测试重要性计算算法的功能",
                "color": COLOR_CODE_RED
            },
            {
                "id": "isolated-node",
                "text": "孤立节点",
                "color": COLOR_CODE_GREEN
            }
        ]

        # Act & Assert: 计算重要性
        for node in test_nodes:
            importance = asyncio.run(env["smart_generator"].calculate_node_importance(
                node, learning_analysis
            ))

            # 验证重要性分数范围
            assert 0 <= importance <= 1

        # 验证连接度高的节点重要性更高
        connected_importance = asyncio.run(env["smart_generator"].calculate_node_importance(
            test_nodes[0], learning_analysis
        ))
        isolated_importance = asyncio.run(env["smart_generator"].calculate_node_importance(
            test_nodes[1], learning_analysis
        ))

        # 红色节点应该比绿色节点重要性高
        assert connected_importance > isolated_importance

    @pytest.mark.asyncio
    async def test_identify_learning_bottlenecks(self, setup_test_environment):
        """测试学习瓶颈识别"""
        env = setup_test_environment

        # 模拟节点进度数据
        node_progress = {
            "low-mastery-node": {
                "mastery_level": 20.0,
                "difficulty_score": 8.0
            },
            "high-error-node": {
                "mastery_level": 60.0,
                "error_rate": 0.5,
                "error_patterns": ["概念混淆"]
            },
            "repeated-review-node": {
                "mastery_level": 50.0,
                "review_count": 8
            },
            "normal-node": {
                "mastery_level": 80.0,
                "error_rate": 0.1,
                "review_count": 2
            }
        }

        canvas_data = {"nodes": []}

        # Act: 识别瓶颈
        bottlenecks = await env["smart_generator"].identify_learning_bottlenecks(
            node_progress, canvas_data
        )

        # Assert: 验证瓶颈识别结果
        assert len(bottlenecks) > 0

        # 验证瓶颈类型
        bottleneck_types = [b["type"] for b in bottlenecks]
        assert "low_mastery" in bottleneck_types
        assert "high_error_rate" in bottleneck_types

        # 验证瓶颈信息结构
        for bottleneck in bottlenecks:
            assert "type" in bottleneck
            assert "node_id" in bottleneck
            assert "severity" in bottleneck
            assert "data" in bottleneck
            assert "description" in bottleneck

    @pytest.mark.asyncio
    async def test_generate_intelligent_layout(self, setup_test_environment):
        """测试智能布局生成"""
        env = setup_test_environment

        learning_analysis = await env["smart_generator"].analyze_user_learning_state(
            user_id="test-user",
            canvas_path=env["canvas_path"]
        )

        review_nodes = [
            {"id": "node-1", "color": COLOR_CODE_RED},
            {"id": "node-2", "color": COLOR_CODE_PURPLE}
        ]

        questions = [
            {
                "question_text": "测试问题1",
                "question_type": "检验型",
                "difficulty": "基础",
                "source_node_id": "node-1"
            },
            {
                "question_text": "测试问题2",
                "question_type": "应用型",
                "difficulty": "中等",
                "source_node_id": "node-2"
            }
        ]

        # Act: 生成智能布局
        layout_plan = await env["smart_generator"].generate_intelligent_layout(
            review_nodes=review_nodes,
            questions=questions,
            learning_analysis=learning_analysis
        )

        # Assert: 验证布局计划结构
        assert "strategy" in layout_plan
        assert "nodes" in layout_plan
        assert "edges" in layout_plan
        assert "metadata" in layout_plan

        # 验证节点生成
        assert len(layout_plan["nodes"]) >= 4  # 2个问题 + 2个黄色节点

        # 验证问题节点
        question_nodes = [n for n in layout_plan["nodes"] if n.get("type") == "question"]
        assert len(question_nodes) == 2

        for node in question_nodes:
            assert "content" in node
            assert "question_type" in node
            assert "difficulty" in node
            assert "source_node_id" in node
            assert "style" in node

    def test_calculate_style_match(self, setup_test_environment):
        """测试学习风格匹配计算"""
        env = setup_test_environment

        # 测试不同用户档案
        user_profiles = [
            {"learning_style": "visual"},
            {"learning_style": "auditory"},
            {"learning_style": "reading"},
            {"learning_style": "kinesthetic"}
        ]

        # 测试不同问题类型
        questions = [
            {"question_type": "comparison"},
            {"question_type": "explanation"},
            {"question_type": "application"},
            {"question_type": "diagram"}
        ]

        # Act & Assert: 测试风格匹配
        for profile in user_profiles:
            learning_style = profile["learning_style"]
            for question in questions:
                match_level = env["smart_generator"]._calculate_style_match(
                    question, profile
                )

                # 验证匹配级别
                assert match_level in ["high", "medium", "low"]

    @pytest.mark.asyncio
    async def test_complete_review_board_generation(self, setup_test_environment):
        """测试完整的检验白板生成流程"""
        env = setup_test_environment

        # Act: 生成完整的智能检验白板
        result = await env["smart_generator"].generate_personalized_review_board(
            user_id="test-user",
            original_canvas_path=env["canvas_path"],
            options={"max_nodes": 3}
        )

        # Assert: 验证生成结果
        assert "review_board_path" in result
        assert "learning_analysis" in result
        assert "quality_score" in result
        assert "statistics" in result

        # 验证统计数据
        stats = result["statistics"]
        assert "nodes_selected" in stats
        assert "questions_generated" in stats
        assert "generation_time" in stats
        assert "personalization_score" in stats

        # 验证文件实际创建
        assert os.path.exists(result["review_board_path"])

        # 验证质量评分
        quality_score = result["quality_score"]
        assert "total_score" in quality_score
        assert "component_scores" in quality_score
        assert "grade" in quality_score

        # 验证性能要求 (AC: 6)
        assert stats["generation_time"] < 10, f"生成时间{stats['generation_time']:.2f}s超过10秒限制"

    def test_fallback_question_generation(self, setup_test_environment):
        """测试降级问题生成"""
        env = setup_test_environment

        test_node = {
            "id": "test-node",
            "text": "这是一个测试节点内容，用于验证降级问题生成功能是否正常工作",
            "color": COLOR_CODE_RED
        }

        # Act: 生成降级问题
        fallback_questions = env["smart_generator"]._generate_fallback_questions(
            node=test_node,
            question_count=2
        )

        # Assert: 验证降级问题
        assert len(fallback_questions) == 2

        for question in fallback_questions:
            assert "question_text" in question
            assert "question_type" in question
            assert "difficulty" in question
            assert "personalization" in question
            assert "source_node_id" in question
            assert question["source_node_id"] == test_node["id"]
            assert question.get("fallback") == True

if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
