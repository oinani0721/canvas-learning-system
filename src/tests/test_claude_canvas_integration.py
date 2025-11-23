"""
Claude Code Canvas集成测试
Story 7.3 - Claude Code深度集成

测试Canvas智能调度器和相关组件的功能
"""

import asyncio
import json
import os
import pytest
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

# 导入被测试的模块
try:
    from canvas_utils import (
        CanvasIntelligentScheduler,
        CanvasLearningAnalyzer,
        ClaudeToolConfig,
        AgentRecommendation,
        NodeAnalysis,
        LearningAnalysisResult,
        CanvasScheduleResult,
        BatchProcessingResult,
        CLAUDE_CODE_ENABLED
    )
    from claude_canvas_tools import ClaudeCanvasToolsManager, canvas_intelligent_scheduler
except ImportError as e:
    print(f"警告: 无法导入测试模块 - {e}")
    CLAUDE_CODE_ENABLED = False


class TestCanvasLearningAnalyzer(unittest.TestCase):
    """测试Canvas学习分析器"""

    def setUp(self):
        """测试设置"""
        if not CLAUDE_CODE_ENABLED:
            self.skipTest("Claude Code SDK未安装")

        self.analyzer = CanvasLearningAnalyzer()
        self.test_canvas_data = {
            "nodes": [
                {
                    "id": "node1",
                    "type": "text",
                    "text": "这是一个红色节点，我不理解",
                    "x": 100,
                    "y": 100,
                    "width": 200,
                    "height": 100,
                    "color": "4"  # 红色
                },
                {
                    "id": "node2",
                    "type": "text",
                    "text": "这是一个紫色节点，似懂非懂",
                    "x": 300,
                    "y": 100,
                    "width": 200,
                    "height": 100,
                    "color": "3"  # 紫色
                },
                {
                    "id": "node3",
                    "type": "text",
                    "text": "这是一个黄色节点，我的理解",
                    "x": 500,
                    "y": 100,
                    "width": 200,
                    "height": 100,
                    "color": "6"  # 黄色
                },
                {
                    "id": "node4",
                    "type": "text",
                    "text": "这是一个绿色节点，已掌握",
                    "x": 700,
                    "y": 100,
                    "width": 200,
                    "height": 100,
                    "color": "2"  # 绿色
                }
            ],
            "edges": []
        }

    def create_temp_canvas_file(self, canvas_data):
        """创建临时Canvas文件"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.canvas', delete=False, encoding='utf-8')
        json.dump(canvas_data, temp_file, ensure_ascii=False, indent=2)
        temp_file.close()
        return temp_file.name

    def tearDown(self):
        """清理测试文件"""
        pass

    def test_analyze_canvas_file_success(self):
        """测试成功分析Canvas文件"""
        # 创建临时Canvas文件
        canvas_path = self.create_temp_canvas_file(self.test_canvas_data)

        try:
            # 执行分析
            result = self.analyzer.analyze_canvas_file(canvas_path)

            # 验证结果
            self.assertIsInstance(result, LearningAnalysisResult)
            self.assertEqual(result.canvas_path, canvas_path)
            self.assertIsInstance(result.node_analysis, NodeAnalysis)
            self.assertIsInstance(result.recommendations, list)
            self.assertIsInstance(result.analysis_timestamp, datetime)
            self.assertGreater(result.confidence_score, 0.0)
            self.assertLessEqual(result.confidence_score, 1.0)

        finally:
            # 清理临时文件
            os.unlink(canvas_path)

    def test_analyze_canvas_file_not_found(self):
        """测试Canvas文件不存在的情况"""
        with self.assertRaises(FileNotFoundError):
            self.analyzer.analyze_canvas_file("nonexistent.canvas")

    def test_analyze_canvas_file_invalid_json(self):
        """测试无效JSON文件的情况"""
        # 创建无效JSON文件
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.canvas', delete=False)
        temp_file.write("invalid json content")
        temp_file.close()

        try:
            with self.assertRaises(ValueError):
                self.analyzer.analyze_canvas_file(temp_file.name)
        finally:
            os.unlink(temp_file.name)

    def test_analyze_nodes(self):
        """测试节点分析功能"""
        nodes = self.test_canvas_data["nodes"]
        result = self.analyzer._analyze_nodes(nodes)

        # 验证节点分析结果
        self.assertEqual(result.total_nodes, 4)
        self.assertEqual(result.color_counts["4"], 1)  # 红色
        self.assertEqual(result.color_counts["3"], 1)  # 紫色
        self.assertEqual(result.color_counts["6"], 1)  # 黄色
        self.assertEqual(result.color_counts["2"], 1)  # 绿色

        # 验证比例计算（基于实际颜色计数）
        self.assertEqual(result.red_ratio, 0.25)
        self.assertEqual(result.purple_ratio, 0.25)
        self.assertEqual(result.yellow_ratio, 0.25)
        self.assertEqual(result.green_ratio, 0.25)  # 有一个绿色节点

        # 验证学习瓶颈识别
        self.assertGreater(len(result.learning_bottlenecks), 0)

        # 验证复杂度评分
        self.assertGreater(result.complexity_score, 0.0)
        self.assertLessEqual(result.complexity_score, 1.0)

    def test_generate_recommendations(self):
        """测试Agent推荐生成"""
        # 创建包含红色节点的分析结果
        node_analysis = NodeAnalysis(
            total_nodes=4,
            color_counts={"1": 2, "3": 1, "4": 0, "6": 1},
            red_ratio=0.5,
            purple_ratio=0.25,
            yellow_ratio=0.25,
            green_ratio=0.0,
            learning_bottlenecks=["红色节点: 不理解"],
            complexity_score=0.7,
            target_node_ids=["node1", "node2", "node3", "node4"]
        )

        recommendations = self.analyzer._generate_recommendations(node_analysis)

        # 验证推荐结果
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)

        # 验证推荐内容
        for rec in recommendations:
            self.assertIsInstance(rec, AgentRecommendation)
            self.assertIsInstance(rec.agent_type, str)
            self.assertGreater(rec.confidence, 0.0)
            self.assertLessEqual(rec.confidence, 1.0)
            self.assertIsInstance(rec.reason, str)
            self.assertIsInstance(rec.target_nodes, list)
            self.assertIsInstance(rec.priority, int)

    def test_calculate_confidence_score(self):
        """测试置信度计算"""
        node_analysis = NodeAnalysis(
            total_nodes=10,
            color_counts={"1": 2, "3": 2, "4": 3, "6": 3},
            red_ratio=0.2,
            purple_ratio=0.2,
            yellow_ratio=0.3,
            green_ratio=0.3,
            learning_bottlenecks=[],
            complexity_score=0.5,
            target_node_ids=[]
        )

        recommendations = [
            AgentRecommendation("basic-decomposition", 0.8, "测试", [], 1),
            AgentRecommendation("scoring-agent", 0.7, "测试", [], 2)
        ]

        confidence = self.analyzer._calculate_confidence_score(node_analysis, recommendations)

        # 验证置信度范围
        self.assertGreater(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)


class TestCanvasIntelligentScheduler(unittest.TestCase):
    """测试Canvas智能调度器"""

    def setUp(self):
        """测试设置"""
        if not CLAUDE_CODE_ENABLED:
            self.skipTest("Claude Code SDK未安装")

        self.scheduler = CanvasIntelligentScheduler()

    def test_initialization(self):
        """测试调度器初始化"""
        # 验证组件已正确初始化
        self.assertIsNotNone(self.scheduler.learning_analyzer)
        self.assertIsNone(self.scheduler.claude_client)
        self.assertIsNone(self.scheduler.client_config)

    @pytest.mark.asyncio
    async def test_initialize_claude_client(self):
        """测试Claude客户端初始化"""
        config = ClaudeToolConfig(
            tool_name="test_tool",
            description="测试工具",
            parameters={"test": "string"},
            permission_mode="acceptEdits"
        )

        try:
            await self.scheduler.initialize_claude_client(config)
            # 注意：由于可能没有真实的Claude API密钥，这里可能会失败
            # 但至少可以验证配置设置
            self.assertEqual(self.scheduler.client_config.tool_name, "test_tool")
        except Exception as e:
            # 预期可能会失败，因为没有真实的API配置
            self.assertIn("configuration", str(e).lower())

    def test_generate_analysis_summary(self):
        """测试分析摘要生成"""
        # 创建测试数据
        node_analysis = NodeAnalysis(
            total_nodes=10,
            color_counts={"4": 3, "3": 2, "2": 3, "6": 2},
            red_ratio=0.3,
            purple_ratio=0.2,
            yellow_ratio=0.2,
            green_ratio=0.3,
            learning_bottlenecks=["红色节点: 不理解概念A"],
            complexity_score=0.6,
            target_node_ids=[]
        )

        recommendations = [
            AgentRecommendation("basic-decomposition", 0.85, "红色节点较多，需要基础拆解", [], 1)
        ]

        learning_result = LearningAnalysisResult(
            canvas_path="test.canvas",
            node_analysis=node_analysis,
            recommendations=recommendations,
            analysis_timestamp=datetime.now(),
            confidence_score=0.8
        )

        # 生成摘要
        summary = self.scheduler._generate_analysis_summary(learning_result)

        # 验证摘要内容
        self.assertIsInstance(summary, str)
        self.assertIn("Canvas学习状态分析报告", summary)
        self.assertIn("学习状态概览", summary)
        self.assertIn("智能Agent推荐", summary)
        self.assertIn("basic-decomposition", summary)

    def test_estimate_execution_time(self):
        """测试执行时间估算"""
        recommendations = [
            AgentRecommendation("basic-decomposition", 0.8, "测试", [], 1),
            AgentRecommendation("scoring-agent", 0.9, "测试", [], 2)
        ]

        estimated_times = self.scheduler._estimate_execution_time(recommendations)

        # 验证时间估算结果
        self.assertIsInstance(estimated_times, dict)
        self.assertIn("basic-decomposition", estimated_times)
        self.assertIn("scoring-agent", estimated_times)
        self.assertIn("total", estimated_times)

        # 验证时间合理性
        for agent_type, time_estimate in estimated_times.items():
            if agent_type != "total":
                self.assertGreater(time_estimate, 0.0)
                self.assertLess(time_estimate, 100.0)  # 不应超过100秒


class TestClaudeCanvasToolsManager(unittest.TestCase):
    """测试Claude Canvas工具管理器"""

    def setUp(self):
        """测试设置"""
        if not CLAUDE_CODE_ENABLED:
            self.skipTest("Claude Code SDK未安装")

        # 创建临时配置文件
        self.temp_config = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8')
        config_data = {
            "version": "1.0.0",
            "client": {
                "model": "sonnet",
                "permission_mode": "acceptEdits",
                "allowed_tools": ["Read", "Write", "Edit"]
            },
            "tools": {
                "canvas_intelligent_scheduler": {
                    "name": "canvas_intelligent_scheduler",
                    "description": "智能Canvas学习调度工具",
                    "parameters": {
                        "canvas_path": {
                            "type": "string",
                            "required": True,
                            "description": "Canvas文件路径"
                        }
                    },
                    "enabled": True
                }
            }
        }

        import yaml
        yaml.dump(config_data, self.temp_config, default_flow_style=False, allow_unicode=True)
        self.temp_config.close()

        self.config_path = self.temp_config.name

    def tearDown(self):
        """清理测试文件"""
        os.unlink(self.config_path)

    @pytest.mark.asyncio
    async def test_manager_initialization(self):
        """测试管理器初始化"""
        manager = ClaudeCanvasToolsManager(config_path=self.config_path)

        # 测试初始化
        await manager.initialize()

        # 验证初始化结果
        self.assertIsNotNone(manager.scheduler)
        self.assertIsNotNone(manager.config)

    def test_load_config(self):
        """测试配置加载"""
        manager = ClaudeCanvasToolsManager(config_path=self.config_path)

        # 验证配置加载
        self.assertEqual(manager.config["version"], "1.0.0")
        self.assertIn("tools", manager.config)
        self.assertIn("canvas_intelligent_scheduler", manager.config["tools"])

    def test_get_available_tools(self):
        """测试获取可用工具"""
        manager = ClaudeCanvasToolsManager(config_path=self.config_path)
        tools = manager.get_available_tools()

        # 验证工具列表
        self.assertIsInstance(tools, list)
        self.assertGreater(len(tools), 0)

        # 验证工具信息
        for tool in tools:
            self.assertIn("name", tool)
            self.assertIn("description", tool)
            self.assertIn("parameters", tool)

    def test_get_tool_info(self):
        """测试获取工具信息"""
        manager = ClaudeCanvasToolsManager(config_path=self.config_path)

        # 获取工具信息
        tool_info = manager.get_tool_info("canvas_intelligent_scheduler")

        # 验证工具信息
        self.assertEqual(tool_info["name"], "canvas_intelligent_scheduler")
        self.assertIn("description", tool_info)
        self.assertIn("parameters", tool_info)
        self.assertTrue(tool_info["enabled"])

    def test_get_tool_info_not_found(self):
        """测试获取不存在的工具信息"""
        manager = ClaudeCanvasToolsManager(config_path=self.config_path)

        # 获取不存在的工具信息
        tool_info = manager.get_tool_info("nonexistent_tool")

        # 验证错误处理
        self.assertIn("error", tool_info)


class TestCanvasIntelligentSchedulerTool(unittest.TestCase):
    """测试Canvas智能调度工具函数"""

    def setUp(self):
        """测试设置"""
        if not CLAUDE_CODE_ENABLED:
            self.skipTest("Claude Code SDK未安装")

    def test_canvas_intelligent_scheduler_missing_parameter(self):
        """测试缺少必需参数的情况"""
        # 测试空参数
        async def test_empty_args():
            result = await canvas_intelligent_scheduler({})
            content = result.get("content", [])
            self.assertGreater(len(content), 0)
            self.assertIn("缺少必需参数", content[0]["text"])

        # 运行异步测试
        asyncio.run(test_empty_args())

    def test_canvas_intelligent_scheduler_file_not_found(self):
        """测试文件不存在的情况"""
        async def test_file_not_found():
            result = await canvas_intelligent_scheduler({"canvas_path": "nonexistent.canvas"})
            content = result.get("content", [])
            self.assertGreater(len(content), 0)
            self.assertIn("不存在", content[0]["text"])

        # 运行异步测试
        asyncio.run(test_file_not_found())


class TestDataModels(unittest.TestCase):
    """测试数据模型"""

    def test_agent_recommendation_model(self):
        """测试Agent推荐数据模型"""
        rec = AgentRecommendation(
            agent_type="basic-decomposition",
            confidence=0.85,
            reason="测试推荐",
            target_nodes=["node1", "node2"],
            priority=1,
            estimated_time=15.0
        )

        # 验证属性
        self.assertEqual(rec.agent_type, "basic-decomposition")
        self.assertEqual(rec.confidence, 0.85)
        self.assertEqual(rec.reason, "测试推荐")
        self.assertEqual(rec.target_nodes, ["node1", "node2"])
        self.assertEqual(rec.priority, 1)
        self.assertEqual(rec.estimated_time, 15.0)

    def test_node_analysis_model(self):
        """测试节点分析数据模型"""
        analysis = NodeAnalysis(
            total_nodes=10,
            color_counts={"1": 2, "3": 3, "4": 3, "6": 2},
            red_ratio=0.2,
            purple_ratio=0.3,
            yellow_ratio=0.2,
            green_ratio=0.3,
            learning_bottlenecks=["瓶颈1", "瓶颈2"],
            complexity_score=0.7,
            target_node_ids=["node1", "node2"]
        )

        # 验证属性
        self.assertEqual(analysis.total_nodes, 10)
        self.assertEqual(analysis.red_ratio, 0.2)
        self.assertEqual(analysis.complexity_score, 0.7)
        self.assertEqual(len(analysis.learning_bottlenecks), 2)

    def test_canvas_schedule_result_model(self):
        """测试Canvas调度结果数据模型"""
        result = CanvasScheduleResult(
            analysis_summary="测试摘要",
            agent_recommendations=[],
            estimated_time={"total": 30.0},
            success_probability=0.85,
            canvas_path="test.canvas",
            analysis_timestamp=datetime.now()
        )

        # 验证属性
        self.assertEqual(result.analysis_summary, "测试摘要")
        self.assertEqual(result.success_probability, 0.85)
        self.assertEqual(result.canvas_path, "test.canvas")
        self.assertEqual(result.estimated_time["total"], 30.0)


if __name__ == "__main__":
    # 运行所有测试
    unittest.main(verbosity=2)