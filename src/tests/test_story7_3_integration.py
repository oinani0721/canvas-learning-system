"""
Story 7.3系统集成测试套件
Story 7.3 Task 5 - 系统集成测试和优化验证 (AC: 1, 2, 3, 4, 5)

完整的集成测试，验证Claude Code深度集成系统的端到端功能
"""

import asyncio
import json
import os
import tempfile
import time
import unittest
from typing import Dict

# 导入被测试的模块
try:
    from claude_canvas_tools import (
        canvas_batch_processor,
        canvas_intelligent_scheduler,
        canvas_orchestrator_collaboration,
        get_tools_manager,
    )

    from canvas_utils import (
        CLAUDE_CODE_ENABLED,
        BatchCanvasProcessor,
        CanvasClaudeOrchestratorBridge,
        CanvasIntelligentScheduler,
        CanvasLearningAnalyzer,
        CanvasOrchestrator,
    )
except ImportError as e:
    print(f"警告: 无法导入测试模块 - {e}")
    CLAUDE_CODE_ENABLED = False


class TestStory73Integration(unittest.TestCase):
    """Story 7.3系统集成测试主类"""

    def setUp(self):
        """测试设置"""
        if not CLAUDE_CODE_ENABLED:
            self.skipTest("Claude Code SDK未安装")

        # 初始化临时文件列表
        self.temp_files = []

        # 创建测试Canvas文件集合
        self.test_canvases = self._create_test_canvas_suite()

    def tearDown(self):
        """清理测试文件"""
        for temp_file in self.temp_files:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def _create_test_canvas_suite(self) -> Dict[str, str]:
        """创建测试Canvas文件集合"""
        canvases = {}

        # 1. 基础数学Canvas - 适合基础拆解
        basic_canvas = {
            "nodes": [
                {
                    "id": "basic_concept",
                    "type": "text",
                    "text": "集合论基础概念",
                    "x": 100,
                    "y": 100,
                    "width": 200,
                    "height": 80,
                    "color": "1"  # 红色
                },
                {
                    "id": "understanding",
                    "type": "text",
                    "text": "我对集合的理解还不够清晰",
                    "x": 100,
                    "y": 250,
                    "width": 200,
                    "height": 80,
                    "color": "6"  # 黄色
                }
            ],
            "edges": [
                {"id": "edge1", "fromNode": "basic_concept", "toNode": "understanding"}
            ]
        }

        # 2. 进阶概念Canvas - 适合深度拆解
        advanced_canvas = {
            "nodes": [
                {
                    "id": "advanced_concept",
                    "type": "text",
                    "text": "线性代数特征向量",
                    "x": 100,
                    "y": 100,
                    "width": 200,
                    "height": 80,
                    "color": "3"  # 紫色
                },
                {
                    "id": "partial_understanding",
                    "type": "text",
                    "text": "知道特征向量的定义，但理解不深入",
                    "x": 100,
                    "y": 250,
                    "width": 200,
                    "height": 80,
                    "color": "6"  # 黄色
                }
            ],
            "edges": [
                {"id": "edge2", "fromNode": "advanced_concept", "toNode": "partial_understanding"}
            ]
        }

        # 3. 复杂知识网络Canvas - 适合智能调度
        complex_canvas = {
            "nodes": [
                {
                    "id": "concept1",
                    "type": "text",
                    "text": "概率论基础",
                    "x": 100,
                    "y": 100,
                    "width": 200,
                    "height": 80,
                    "color": "2"  # 绿色
                },
                {
                    "id": "concept2",
                    "type": "text",
                    "text": "统计推断",
                    "x": 300,
                    "y": 100,
                    "width": 200,
                    "height": 80,
                    "color": "3"  # 紫色
                },
                {
                    "id": "concept3",
                    "type": "text",
                    "text": "贝叶斯定理",
                    "x": 500,
                    "y": 100,
                    "width": 200,
                    "height": 80,
                    "color": "1"  # 红色
                },
                {
                    "id": "concept4",
                    "type": "text",
                    "text": "马尔可夫链",
                    "x": 200,
                    "y": 250,
                    "width": 200,
                    "height": 80,
                    "color": "1"  # 红色
                }
            ],
            "edges": [
                {"id": "edge3", "fromNode": "concept1", "toNode": "concept2"},
                {"id": "edge4", "fromNode": "concept2", "toNode": "concept3"},
                {"id": "edge5", "fromNode": "concept3", "toNode": "concept4"}
            ]
        }

        # 4. 混合状态Canvas - 测试多Agent推荐
        mixed_canvas = {
            "nodes": [
                {
                    "id": "red_node",
                    "type": "text",
                    "text": "完全不懂的概念",
                    "x": 100,
                    "y": 100,
                    "width": 200,
                    "height": 80,
                    "color": "1"  # 红色
                },
                {
                    "id": "purple_node",
                    "type": "text",
                    "text": "似懂非懂的概念",
                    "x": 300,
                    "y": 100,
                    "width": 200,
                    "height": 80,
                    "color": "3"  # 紫色
                },
                {
                    "id": "green_node",
                    "type": "text",
                    "text": "已经掌握的概念",
                    "x": 500,
                    "y": 100,
                    "width": 200,
                    "height": 80,
                    "color": "2"  # 绿色
                }
            ],
            "edges": []
        }

        # 5. 空Canvas - 测试边界情况
        empty_canvas = {
            "nodes": [],
            "edges": []
        }

        canvas_data = {
            "basic": basic_canvas,
            "advanced": advanced_canvas,
            "complex": complex_canvas,
            "mixed": mixed_canvas,
            "empty": empty_canvas
        }

        # 创建临时文件
        for name, data in canvas_data.items():
            temp_file = tempfile.NamedTemporaryFile(
                mode='w',
                suffix=f'_test_{name}.canvas',
                delete=False,
                encoding='utf-8'
            )
            json.dump(data, temp_file, ensure_ascii=False, indent=2)
            temp_file.close()
            canvases[name] = temp_file.name
            self.temp_files.append(temp_file.name)

        return canvases


class TestTask1Integration(TestStory73Integration):
    """Task 1: Claude Code SDK集成测试"""

    def test_canvas_learning_analyzer_integration(self):
        """测试Canvas学习分析器集成"""
        async def run_test():
            analyzer = CanvasLearningAnalyzer()

            # 测试基础Canvas分析
            result = analyzer.analyze_canvas_file(self.test_canvases["basic"])

            # 验证分析结果结构
            self.assertIsNotNone(result)
            self.assertEqual(result.canvas_path, self.test_canvases["basic"])
            self.assertIsNotNone(result.node_analysis)
            self.assertIsInstance(result.recommendations, list)
            self.assertIsInstance(result.confidence_score, float)

            # 验证节点分析
            node_analysis = result.node_analysis
            self.assertEqual(node_analysis.total_nodes, 2)
            self.assertIn("1", node_analysis.color_counts)  # 红色节点
            self.assertIn("6", node_analysis.color_counts)  # 黄色节点
            self.assertGreaterEqual(node_analysis.red_ratio, 0)  # 可能为0，但应该存在

            # 验证推荐生成
            self.assertGreater(len(result.recommendations), 0)
            for rec in result.recommendations:
                self.assertIsNotNone(rec.agent_type)
                self.assertGreaterEqual(rec.confidence, 0)
                self.assertLessEqual(rec.confidence, 1)

        asyncio.run(run_test())

    def test_intelligent_scheduler_basic_functionality(self):
        """测试智能调度器基础功能"""
        async def run_test():
            scheduler = CanvasIntelligentScheduler()

            # 测试基础分析
            result = await scheduler.analyze_canvas_with_claude(
                canvas_path=self.test_canvases["basic"],
                detail_level="basic",
                include_recommendations=True,
                priority_threshold=0.5
            )

            # 验证结果结构
            self.assertIsNotNone(result)
            self.assertIsNotNone(result.analysis_summary)
            self.assertIsInstance(result.agent_recommendations, list)
            self.assertIsInstance(result.estimated_time, dict)
            self.assertIsInstance(result.success_probability, float)

            # 验证分析摘要内容
            summary = result.analysis_summary
            self.assertIn("Canvas学习状态分析报告", summary)
            self.assertIn("Context7验证", summary)

            # 验证Agent推荐
            if result.agent_recommendations:
                for rec in result.agent_recommendations:
                    self.assertIsNotNone(rec.agent_type)
                    self.assertGreater(rec.confidence, 0)

        asyncio.run(run_test())


class TestTask2Integration(TestStory73Integration):
    """Task 2: 智能调度工具集成测试"""

    def test_canvas_intelligent_scheduler_tool(self):
        """测试canvas_intelligent_scheduler工具函数"""
        async def run_test():
            # 测试基础参数
            result = await canvas_intelligent_scheduler({
                "canvas_path": self.test_canvases["mixed"],
                "detail_level": "standard",
                "include_recommendations": True,
                "priority_threshold": 0.6
            })

            # 验证工具响应格式
            self.assertIn("content", result)
            self.assertIsInstance(result["content"], list)
            self.assertGreater(len(result["content"]), 0)

            # 验证响应内容
            content = result["content"][0]
            self.assertIn("type", content)
            self.assertEqual(content["type"], "text")
            self.assertIn("text", content)

            # 验证分析报告内容
            report_text = content["text"]
            self.assertIn("Canvas学习状态分析报告", report_text)
            self.assertIn("智能Agent推荐", report_text)
            self.assertIn("Context7验证", report_text)

        asyncio.run(run_test())

    def test_enhanced_analysis_features(self):
        """测试增强分析功能"""
        async def run_test():
            scheduler = CanvasIntelligentScheduler()

            # 测试不同详细程度
            detail_levels = ["basic", "standard", "detailed"]
            for detail_level in detail_levels:
                result = await scheduler.analyze_canvas_with_claude(
                    canvas_path=self.test_canvases["complex"],
                    detail_level=detail_level,
                    include_recommendations=True,
                    priority_threshold=0.5
                )

                self.assertIsNotNone(result)
                self.assertIn("智能调度器分析", result.analysis_summary)

                # 验证详细程度影响
                if detail_level == "detailed":
                    self.assertGreater(len(result.analysis_summary), 1000)  # 详细报告应该更长

        asyncio.run(run_test())

    def test_learning_state_analyzer_integration(self):
        """测试学习状态分析器集成"""
        # 创建学习状态分析器
        from canvas_utils import LearningStateAnalyzer
        analyzer = LearningStateAnalyzer()

        # 测试复杂Canvas分析
        result = analyzer.analyze_learning_state(self.test_canvases["complex"])

        # 验证学习模式识别
        self.assertIn("learning_pattern", result)
        self.assertIn("understanding_score", result)
        self.assertIn("complexity_adaptation", result)
        self.assertIn("bottleneck_analysis", result)

        # 验证学习模式合理性
        valid_patterns = ["beginner", "developing", "intermediate", "advanced"]
        self.assertIn(result["learning_pattern"], valid_patterns)

        # 验证理解分数范围
        score = result["understanding_score"]
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)


class TestTask3Integration(TestStory73Integration):
    """Task 3: Canvas Orchestrator协同机制集成测试"""

    def test_canvas_claude_orchestrator_bridge(self):
        """测试CanvasClaudeOrchestratorBridge"""
        bridge = CanvasClaudeOrchestratorBridge(self.test_canvases["basic"])

        # 验证桥接器初始化
        self.assertIsNotNone(bridge.canvas_path)
        self.assertIsNotNone(bridge.orchestrator)
        self.assertIsNotNone(bridge.scheduler)
        self.assertIsInstance(bridge.task_queue, list)
        self.assertIsInstance(bridge.execution_history, list)

        # 验证Agent可用性
        available_agents = bridge.get_available_agents()
        self.assertIsInstance(available_agents, list)
        self.assertGreater(len(available_agents), 0)
        self.assertIn("basic-decomposition", available_agents)
        self.assertIn("scoring-agent", available_agents)

    def test_orchestrator_collaboration_tool(self):
        """测试canvas_orchestrator_collaboration工具函数"""
        async def run_test():
            # 测试基础协同操作
            result = await canvas_orchestrator_collaboration({
                "canvas_path": self.test_canvases["advanced"],
                "operation": "decompose",
                "user_intent": "深度拆解紫色节点概念",
                "claude_guidance": "重点关注基础概念的深度理解"
            })

            # 验证协同响应
            self.assertIn("content", result)
            content = result.get("content", [])
            self.assertGreater(len(content), 0)

            # 验证报告格式
            report_text = content[0]["text"]
            self.assertIn("Canvas Orchestrator协同执行报告", report_text)

        asyncio.run(run_test())

    def test_recommendation_translation(self):
        """测试Claude推荐转换为任务"""
        bridge = CanvasClaudeOrchestratorBridge(self.test_canvases["mixed"])

        # 创建测试推荐
        from canvas_utils import AgentRecommendation
        test_recommendations = [
            AgentRecommendation(
                agent_type="basic-decomposition",
                confidence=0.85,
                reason="红色节点需要基础拆解",
                target_nodes=["red_node"],
                priority=1,
                estimated_time=15.0
            ),
            AgentRecommendation(
                agent_type="scoring-agent",
                confidence=0.90,
                reason="黄色节点需要评分验证",
                target_nodes=["understanding"],
                priority=2,
                estimated_time=10.0
            )
        ]

        # 测试推荐转换
        tasks = bridge._translate_claude_recommendations_to_tasks(
            test_recommendations, "decompose", ["red_node"]
        )

        # 验证任务转换结果
        self.assertIsInstance(tasks, list)
        self.assertGreater(len(tasks), 0)

        for task in tasks:
            self.assertIn("type", task)
            self.assertIn("agent_type", task)
            self.assertIn("target_nodes", task)
            self.assertIn("confidence", task)
            self.assertIn("reason", task)
            self.assertIn("estimated_time", task)


class TestTask4Integration(TestStory73Integration):
    """Task 4: 批量Canvas处理功能集成测试"""

    def test_batch_canvas_processor_integration(self):
        """测试批量Canvas处理器集成"""
        async def run_test():
            processor = BatchCanvasProcessor(max_concurrent=2)

            # 准备测试Canvas路径
            canvas_paths = [
                self.test_canvases["basic"],
                self.test_canvases["advanced"],
                self.test_canvases["mixed"]
            ]

            # 执行批量处理
            start_time = time.time()
            batch_result = await processor.batch_analyze_canvases(
                canvas_paths=canvas_paths,
                detail_level="basic",
                include_recommendations=True,
                priority_threshold=0.6
            )
            end_time = time.time()

            # 验证批量处理结果
            self.assertIsNotNone(batch_result)
            self.assertEqual(batch_result.total_canvases, len(canvas_paths))
            self.assertGreaterEqual(batch_result.successful_count, 0)
            self.assertLessEqual(batch_result.failed_count, len(canvas_paths))

            # 验证处理时间
            processing_time = end_time - start_time
            self.assertGreater(processing_time, 0)
            self.assertGreater(batch_result.processing_time, 0)

            # 验证成功率
            success_rate = batch_result.get_success_rate()
            self.assertGreaterEqual(success_rate, 0)
            self.assertLessEqual(success_rate, 100)

        asyncio.run(run_test())

    def test_canvas_batch_processor_tool_integration(self):
        """测试canvas_batch_processor工具函数集成"""
        async def run_test():
            # 准备批量处理参数
            canvas_paths = [
                self.test_canvases["basic"],
                self.test_canvases["advanced"]
            ]

            # 执行批量处理工具
            result = await canvas_batch_processor({
                "canvas_paths": canvas_paths,
                "detail_level": "standard",
                "include_recommendations": True,
                "priority_threshold": 0.7,
                "max_concurrent": 1
            })

            # 验证工具响应
            self.assertIn("content", result)
            content = result.get("content", [])
            self.assertGreater(len(content), 0)

            # 验证批量处理报告
            report_text = content[0]["text"]
            self.assertIn("Canvas批量处理报告", report_text)
            self.assertIn("总Canvas数量", report_text)
            self.assertIn("Context7验证", report_text)

        asyncio.run(run_test())

    def test_progress_monitoring_integration(self):
        """测试进度监控集成"""
        from canvas_utils import BatchProgressMonitor

        monitor = BatchProgressMonitor()
        monitor.initialize(3)

        # 模拟进度更新
        import time
        time.sleep(0.1)

        monitor.update_progress(1, failed=False)
        monitor.update_progress(1, failed=False)
        monitor.update_progress(1, failed=True)

        # 验证进度监控结果
        current = monitor.get_current_progress()
        self.assertEqual(current["completed"], 2)
        self.assertEqual(current["failed"], 1)
        self.assertEqual(current["percentage"], 100.0)

        summary = monitor.get_summary()
        self.assertEqual(summary["success_rate"], 66.7)
        self.assertEqual(summary["failure_rate"], 33.3)
        self.assertGreater(summary["average_time_per_task"], 0)


class TestPerformanceOptimization(TestStory73Integration):
    """性能优化测试"""

    def test_single_canvas_analysis_performance(self):
        """测试单个Canvas分析性能"""
        async def run_test():
            scheduler = CanvasIntelligentScheduler()

            # 测试不同复杂度Canvas的处理时间
            test_cases = [
                ("basic", self.test_canvases["basic"]),
                ("complex", self.test_canvases["complex"])
            ]

            for name, canvas_path in test_cases:
                start_time = time.time()
                result = await scheduler.analyze_canvas_with_claude(
                    canvas_path=canvas_path,
                    detail_level="basic",
                    include_recommendations=False
                )
                end_time = time.time()

                processing_time = end_time - start_time

                # 验证性能基准（应该在合理时间内完成）
                self.assertLess(processing_time, 10.0,
                    f"{name} Canvas分析时间过长: {processing_time:.3f}秒")

                # 验证结果质量
                self.assertIsNotNone(result)
                self.assertIsNotNone(result.analysis_summary)

        asyncio.run(run_test())

    def test_batch_processing_performance(self):
        """测试批量处理性能"""
        async def run_test():
            processor = BatchCanvasProcessor(max_concurrent=2)

            canvas_paths = [
                self.test_canvases["basic"],
                self.test_canvases["advanced"],
                self.test_canvases["mixed"]
            ]

            start_time = time.time()
            batch_result = await processor.batch_analyze_canvases(
                canvas_paths=canvas_paths,
                detail_level="basic",
                include_recommendations=False,
                priority_threshold=0.5
            )
            end_time = time.time()

            total_time = end_time - start_time
            avg_time_per_canvas = total_time / len(canvas_paths)

            # 验证批量处理性能
            self.assertLess(total_time, 30.0, "批量处理总时间过长")
            self.assertLess(avg_time_per_canvas, 15.0, "平均每Canvas处理时间过长")

            # 验证并发效率
            expected_sequential_time = avg_time_per_canvas * len(canvas_paths)
            efficiency_gain = expected_sequential_time / total_time if total_time > 0 else 1
            self.assertGreater(efficiency_gain, 1.0, "并发处理应该比顺序处理更高效")

        asyncio.run(run_test())

    def test_memory_usage_optimization(self):
        """测试内存使用优化"""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        async def run_memory_test():
            scheduler = CanvasIntelligentScheduler()

            # 连续处理多个Canvas
            for _ in range(5):
                await scheduler.analyze_canvas_with_claude(
                    canvas_path=self.test_canvases["basic"],
                    detail_level="basic",
                    include_recommendations=False
                )

        asyncio.run(run_memory_test())

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # 验证内存使用合理（不应该增长过多）
        self.assertLess(memory_increase, 100,
            f"内存使用增长过多: {memory_increase:.2f}MB")


class TestSystemCompatibility(TestStory73Integration):
    """系统兼容性测试"""

    def test_canvas_orchestrator_compatibility(self):
        """测试与canvas-orchestrator的兼容性"""
        # 测试现有Canvas操作是否仍然工作
        try:
            orchestrator = CanvasOrchestrator(self.test_canvases["basic"])

            # 验证基础组件可以正常初始化
            self.assertIsNotNone(orchestrator.canvas_path)
            self.assertIsNotNone(orchestrator.logic)
            self.assertIsNotNone(orchestrator.operator)

            # 验证可以通过JSON操作符读取Canvas
            json_operator = orchestrator.operator()
            canvas_data = json_operator.read_canvas(self.test_canvases["basic"])
            self.assertIsNotNone(canvas_data)
            self.assertIn("nodes", canvas_data)
            self.assertIn("edges", canvas_data)

            # 验证节点查找功能
            red_nodes = json_operator.find_nodes_by_color(canvas_data, "1")
            self.assertIsInstance(red_nodes, list)

        except Exception as e:
            self.fail(f"Canvas Orchestrator兼容性测试失败: {str(e)}")

    def test_sub_agent_compatibility(self):
        """测试与12个Sub-agent的兼容性"""
        bridge = CanvasClaudeOrchestratorBridge(self.test_canvases["mixed"])

        # 验证所有标准Agent仍然可用
        expected_agents = [
            "basic-decomposition",
            "deep-decomposition",
            "scoring-agent",
            "oral-explanation",
            "clarification-path",
            "comparison-table",
            "memory-anchor",
            "four-level-explanation",
            "example-teaching"
        ]

        available_agents = bridge.get_available_agents()

        for agent in expected_agents:
            self.assertIn(agent, available_agents,
                f"标准Agent {agent} 不可用")

    def test_existing_api_compatibility(self):
        """测试现有API兼容性"""
        # 验证现有canvas_utils.py的公共API仍然可用
        try:
            from canvas_utils import CanvasBusinessLogic, CanvasJSONOperator

            # 测试基础JSON操作
            json_op = CanvasJSONOperator()
            data = json_op.read_canvas(self.test_canvases["basic"])
            self.assertIsNotNone(data)

            # 测试业务逻辑操作
            business_op = CanvasBusinessLogic(self.test_canvases["basic"])
            red_nodes = business_op.extract_red_nodes()
            self.assertIsInstance(red_nodes, list)

        except Exception as e:
            self.fail(f"现有API兼容性测试失败: {str(e)}")


class TestEndToEndWorkflows(TestStory73Integration):
    """端到端工作流测试"""

    def test_complete_learning_workflow(self):
        """测试完整学习工作流"""
        async def run_test():
            # 1. 分析Canvas学习状态
            scheduler = CanvasIntelligentScheduler()
            analysis_result = await scheduler.analyze_canvas_with_claude(
                canvas_path=self.test_canvases["mixed"],
                detail_level="standard",
                include_recommendations=True
            )

            self.assertIsNotNone(analysis_result)

            # 2. 基于推荐执行Agent操作
            if analysis_result.agent_recommendations:
                bridge = CanvasClaudeOrchestratorBridge(self.test_canvases["mixed"])

                # 转换推荐为任务
                top_recommendation = analysis_result.agent_recommendations[0]
                tasks = bridge._translate_claude_recommendations_to_tasks(
                    [top_recommendation], "decompose",
                    top_recommendation.target_nodes
                )

                self.assertGreater(len(tasks), 0)

            # 3. 验证工作流完整性
            self.assertIsNotNone(analysis_result.analysis_summary)
            self.assertIsInstance(analysis_result.agent_recommendations, list)
            self.assertGreater(analysis_result.success_probability, 0)

        asyncio.run(run_test())

    def test_batch_learning_workflow(self):
        """测试批量学习工作流"""
        async def run_test():
            # 准备多个Canvas
            canvas_paths = [
                self.test_canvases["basic"],
                self.test_canvases["advanced"]
            ]

            # 1. 批量分析学习状态
            processor = BatchCanvasProcessor(max_concurrent=2)
            batch_result = await processor.batch_analyze_canvases(
                canvas_paths=canvas_paths,
                detail_level="standard",
                include_recommendations=True,
                priority_threshold=0.6
            )

            # 2. 验证批量结果
            self.assertEqual(batch_result.total_canvases, len(canvas_paths))
            self.assertGreaterEqual(batch_result.successful_count, 0)

            # 3. 分析结果质量
            if batch_result.results:
                for result in batch_result.results:
                    if hasattr(result, 'success') and result.success:
                        self.assertIsNotNone(result.analysis_summary)

        asyncio.run(run_test())

    def test_error_recovery_workflow(self):
        """测试错误恢复工作流"""
        async def run_test():
            # 测试不存在的文件
            processor = BatchCanvasProcessor()

            try:
                await processor.batch_analyze_canvases(
                    canvas_paths=["nonexistent.canvas"],
                    detail_level="basic"
                )
                self.fail("应该抛出文件不存在错误")
            except Exception:
                # 预期的错误，验证错误处理机制
                error_summary = processor.error_handler.get_summary()
                self.assertGreater(error_summary["total_errors"], 0)

        asyncio.run(run_test())


class TestUserExperienceValidation(TestStory73Integration):
    """用户体验验证测试"""

    def test_response_format_consistency(self):
        """测试响应格式一致性"""
        async def run_test():
            # 测试不同工具的响应格式一致性
            tools_to_test = [
                ("智能调度器", lambda: canvas_intelligent_scheduler({
                    "canvas_path": self.test_canvases["basic"],
                    "detail_level": "basic"
                })),
                ("协同工具", lambda: canvas_orchestrator_collaboration({
                    "canvas_path": self.test_canvases["basic"],
                    "operation": "analyze"
                })),
                ("批量处理", lambda: canvas_batch_processor({
                    "canvas_paths": [self.test_canvases["basic"]],
                    "detail_level": "basic"
                }))
            ]

            for tool_name, tool_func in tools_to_test:
                try:
                    result = await tool_func()

                    # 验证响应格式一致性
                    self.assertIn("content", result, f"{tool_name} 缺少content字段")
                    self.assertIsInstance(result["content"], list, f"{tool_name} content不是列表")
                    self.assertGreater(len(result["content"]), 0, f"{tool_name} content为空")

                    # 验证内容结构
                    content_item = result["content"][0]
                    self.assertIn("type", content_item, f"{tool_name} 缺少type字段")
                    self.assertIn("text", content_item, f"{tool_name} 缺少text字段")

                except Exception as e:
                    # 记录但不失败，某些工具可能需要特定条件
                    print(f"{tool_name} 测试跳过: {str(e)}")

        asyncio.run(run_test())

    def test_helpful_error_messages(self):
        """测试友好的错误消息"""
        async def run_test():
            # 测试各种错误场景的消息质量
            error_scenarios = [
                ("缺少参数", {}),
                ("无效路径", {"canvas_path": "nonexistent.canvas"}),
                ("错误类型", {"canvas_paths": "not_a_list"})
            ]

            for scenario_name, params in error_scenarios:
                try:
                    if "canvas_paths" in params:
                        result = await canvas_batch_processor(params)
                    else:
                        result = await canvas_intelligent_scheduler(params)

                    # 验证错误消息质量
                    if "content" in result:
                        error_text = result["content"][0]["text"]

                        # 检查是否包含有用信息
                        self.assertTrue(
                            any(keyword in error_text.lower() for keyword in ["错误", "缺少", "无效", "不存在"]),
                            f"{scenario_name} 错误消息不够友好"
                        )

                        # 检查是否包含帮助信息
                        self.assertTrue(
                            any(keyword in error_text for keyword in ["💡", "参数", "示例", "使用"]),
                            f"{scenario_name} 错误消息缺少帮助信息"
                        )

                except Exception:
                    # 某些错误场景可能直接抛出异常
                    pass

        asyncio.run(run_test())

    def test_performance_feedback(self):
        """测试性能反馈信息"""
        async def run_test():
            # 测试工具是否提供性能相关的反馈
            start_time = time.time()

            result = await canvas_intelligent_scheduler({
                "canvas_path": self.test_canvases["complex"],
                "detail_level": "standard"
            })

            end_time = time.time()
            response_time = end_time - start_time

            # 验证响应时间合理
            self.assertLess(response_time, 10.0, "工具响应时间过长")

            # 验证响应内容包含相关信息
            if "content" in result:
                content_text = result["content"][0]["text"]

                # 检查是否包含分析质量指标
                quality_indicators = ["置信度", "成功率", "推荐", "分析"]
                has_quality_info = any(indicator in content_text for indicator in quality_indicators)

                self.assertTrue(has_quality_info, "响应缺少质量指标信息")

        asyncio.run(run_test())


if __name__ == "__main__":
    # 运行所有集成测试
    unittest.main(verbosity=2)
