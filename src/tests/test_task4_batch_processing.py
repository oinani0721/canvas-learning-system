"""
Task 4批量Canvas处理功能测试
Story 7.3 Task 4 - 开发批量Canvas处理功能 (AC: 5)

测试BatchCanvasProcessor、批量处理工具函数和相关组件的功能
"""

import asyncio
import json
import os
import tempfile
import time
import unittest
from datetime import datetime
from pathlib import Path

# 导入pytest
try:
    import pytest
except ImportError:
    pytest = None

# 导入被测试的模块
try:
    from canvas_utils import (
        BatchCanvasProcessor,
        BatchProcessingTask,
        BatchProgressMonitor,
        BatchErrorHandler,
        BatchProcessingResult,
        CLAUDE_CODE_ENABLED
    )
    from claude_canvas_tools import canvas_batch_processor, _format_batch_processing_report
except ImportError as e:
    print(f"警告: 无法导入测试模块 - {e}")
    CLAUDE_CODE_ENABLED = False


class TestBatchProcessingTask(unittest.TestCase):
    """测试BatchProcessingTask"""

    def test_batch_processing_task_creation(self):
        """测试批量处理任务创建"""
        task = BatchProcessingTask(
            task_id="test_task_1",
            canvas_path="test.canvas",
            detail_level="detailed",
            include_recommendations=False,
            priority_threshold=0.8
        )

        self.assertEqual(task.task_id, "test_task_1")
        self.assertEqual(task.canvas_path, "test.canvas")
        self.assertEqual(task.detail_level, "detailed")
        self.assertEqual(task.include_recommendations, False)
        self.assertEqual(task.priority_threshold, 0.8)
        self.assertEqual(task.status, "pending")
        self.assertIsInstance(task.created_at, datetime)

    def test_batch_processing_task_defaults(self):
        """测试批量处理任务默认值"""
        task = BatchProcessingTask(
            task_id="test_task_2",
            canvas_path="test2.canvas"
        )

        self.assertEqual(task.detail_level, "standard")
        self.assertEqual(task.include_recommendations, True)
        self.assertEqual(task.priority_threshold, 0.7)


class TestBatchProgressMonitor(unittest.TestCase):
    """测试BatchProgressMonitor"""

    def test_progress_monitor_initialization(self):
        """测试进度监控器初始化"""
        monitor = BatchProgressMonitor()
        monitor.initialize(10)

        self.assertEqual(monitor.total_tasks, 10)
        self.assertEqual(monitor.completed_tasks, 0)
        self.assertEqual(monitor.failed_tasks, 0)
        self.assertIsNotNone(monitor.start_time)
        self.assertEqual(len(monitor.progress_history), 0)

    def test_progress_update_success(self):
        """测试成功进度更新"""
        monitor = BatchProgressMonitor()
        monitor.initialize(5)

        # 等待一小段时间确保elapsed_time > 0
        import time
        time.sleep(0.1)

        monitor.update_progress(2, failed=False)

        self.assertEqual(monitor.completed_tasks, 2)
        self.assertEqual(monitor.failed_tasks, 0)
        self.assertEqual(len(monitor.progress_history), 1)

        current = monitor.get_current_progress()
        self.assertEqual(current["completed"], 2)
        self.assertEqual(current["failed"], 0)
        self.assertEqual(current["percentage"], 40.0)

    def test_progress_update_failure(self):
        """测试失败进度更新"""
        monitor = BatchProgressMonitor()
        monitor.initialize(5)

        monitor.update_progress(1, failed=True)

        self.assertEqual(monitor.completed_tasks, 0)
        self.assertEqual(monitor.failed_tasks, 1)

        current = monitor.get_current_progress()
        self.assertEqual(current["completed"], 0)
        self.assertEqual(current["failed"], 1)
        self.assertEqual(current["percentage"], 20.0)

    def test_progress_summary(self):
        """测试进度摘要生成"""
        monitor = BatchProgressMonitor()
        monitor.initialize(10)

        # 等待一小段时间确保elapsed_time > 0
        import time
        time.sleep(0.1)

        # 模拟一些进度
        monitor.update_progress(3, failed=False)
        monitor.update_progress(1, failed=True)

        summary = monitor.get_summary()

        self.assertEqual(summary["total_tasks"], 10)
        self.assertEqual(summary["success_rate"], 30.0)
        self.assertEqual(summary["failure_rate"], 10.0)
        self.assertIsNotNone(summary["total_processing_time"])
        self.assertGreaterEqual(summary["average_time_per_task"], 0)
        self.assertLessEqual(len(summary["progress_history"]), 10)


class TestBatchErrorHandler(unittest.TestCase):
    """测试BatchErrorHandler"""

    def test_error_handler_initialization(self):
        """测试错误处理器初始化"""
        handler = BatchErrorHandler()

        self.assertEqual(len(handler.error_log), 0)
        self.assertEqual(len(handler.error_statistics), 0)

    def test_error_recording(self):
        """测试错误记录"""
        handler = BatchErrorHandler()

        # 记录一些错误
        handler.record_error("task_1", FileNotFoundError("File not found"))
        handler.record_error("task_2", ValueError("Invalid value"))
        handler.record_error("task_3", FileNotFoundError("Another file not found"))

        self.assertEqual(len(handler.error_log), 3)
        self.assertEqual(len(handler.error_statistics), 2)  # 两种错误类型
        self.assertEqual(handler.error_statistics["FileNotFoundError"], 2)
        self.assertEqual(handler.error_statistics["ValueError"], 1)

    def test_error_summary(self):
        """测试错误摘要生成"""
        handler = BatchErrorHandler()

        # 空错误摘要
        summary = handler.get_summary()
        self.assertEqual(summary["total_errors"], 0)
        self.assertIsNone(summary["most_common_error"])

        # 添加错误后的摘要
        handler.record_error("task_1", RuntimeError("Runtime error"))
        handler.record_error("task_2", RuntimeError("Another runtime error"))
        handler.record_error("task_3", MemoryError("Memory error"))

        summary = handler.get_summary()
        self.assertEqual(summary["total_errors"], 3)
        self.assertEqual(summary["most_common_error"]["type"], "RuntimeError")
        self.assertEqual(summary["most_common_error"]["count"], 2)
        self.assertEqual(len(summary["recent_errors"]), 3)


class TestBatchProcessingResult(unittest.TestCase):
    """测试BatchProcessingResult"""

    def setUp(self):
        """设置测试数据"""
        from canvas_utils import CanvasScheduleResult

        # 创建模拟的CanvasScheduleResult列表
        self.mock_results = [
            CanvasScheduleResult(
                analysis_summary="成功分析1",
                agent_recommendations=[],
                estimated_time={},
                success_probability=0.8,
                canvas_path="canvas1.canvas",
                success=True
            ),
            CanvasScheduleResult(
                analysis_summary="成功分析2",
                agent_recommendations=[],
                estimated_time={},
                success_probability=0.9,
                canvas_path="canvas2.canvas",
                success=True
            ),
            CanvasScheduleResult(
                analysis_summary="分析失败",
                agent_recommendations=[],
                estimated_time={},
                success_probability=0.0,
                canvas_path="canvas3.canvas",
                success=False,
                error="File not found"
            )
        ]

    def test_batch_processing_result_creation(self):
        """测试批量处理结果创建"""
        result = BatchProcessingResult(
            total_canvases=3,
            successful_count=2,
            failed_count=1,
            results=self.mock_results,
            processing_time=15.5,
            progress_summary={"success_rate": 66.7},
            error_summary={"total_errors": 1}
        )

        self.assertEqual(result.total_canvases, 3)
        self.assertEqual(result.successful_count, 2)
        self.assertEqual(result.failed_count, 1)
        self.assertEqual(result.processing_time, 15.5)
        self.assertIsInstance(result.timestamp, str)

    def test_success_rate_calculation(self):
        """测试成功率计算"""
        result = BatchProcessingResult(
            total_canvases=10,
            successful_count=8,
            failed_count=2,
            results=[],
            processing_time=30.0,
            progress_summary={},
            error_summary={}
        )

        self.assertEqual(result.get_success_rate(), 80.0)

    def test_average_processing_time(self):
        """测试平均处理时间计算"""
        result = BatchProcessingResult(
            total_canvases=5,
            successful_count=5,
            failed_count=0,
            results=[],
            processing_time=25.0,
            progress_summary={},
            error_summary={}
        )

        self.assertEqual(result.get_average_processing_time(), 5.0)

    def test_failed_canvases_extraction(self):
        """测试失败Canvas列表提取"""
        result = BatchProcessingResult(
            total_canvases=3,
            successful_count=2,
            failed_count=1,
            results=self.mock_results,
            processing_time=15.0,
            progress_summary={},
            error_summary={}
        )

        failed_canvases = result.get_failed_canvases()
        self.assertEqual(len(failed_canvases), 1)
        self.assertEqual(failed_canvases[0], "canvas3.canvas")

    def test_report_generation(self):
        """测试报告生成"""
        result = BatchProcessingResult(
            total_canvases=3,
            successful_count=2,
            failed_count=1,
            results=self.mock_results,
            processing_time=15.0,
            progress_summary={"success_rate": 66.7, "failure_rate": 33.3},
            error_summary={
                "total_errors": 1,
                "most_common_error": {"type": "FileNotFoundError", "count": 1}
            }
        )

        report = result.generate_report()

        self.assertIn("Canvas批量处理报告", report)
        self.assertIn("总Canvas数量: 3", report)
        self.assertIn("成功处理: 2", report)
        self.assertIn("处理失败: 1", report)
        self.assertIn("成功率: 66.7%", report)
        self.assertIn("总处理时间: 15.00秒", report)
        self.assertIn("最常见错误: FileNotFoundError", report)


class TestBatchCanvasProcessor(unittest.TestCase):
    """测试BatchCanvasProcessor"""

    def setUp(self):
        """测试设置"""
        if not CLAUDE_CODE_ENABLED:
            self.skipTest("Claude Code SDK未安装")

        # 创建测试Canvas文件
        self.test_canvas_data = {
            "nodes": [
                {
                    "id": "test_node_1",
                    "type": "text",
                    "text": "测试节点1",
                    "x": 100,
                    "y": 100,
                    "width": 200,
                    "height": 80,
                    "color": "1"
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

    def test_processor_initialization(self):
        """测试处理器初始化"""
        processor = BatchCanvasProcessor(max_concurrent=3)

        self.assertEqual(processor.max_concurrent, 3)
        self.assertIsNotNone(processor.scheduler)
        self.assertIsNotNone(processor.progress_monitor)
        self.assertIsNotNone(processor.error_handler)

    def test_single_task_processing(self):
        """测试单个任务处理"""
        processor = BatchCanvasProcessor(max_concurrent=1)

        # 创建测试Canvas文件
        temp_canvas = self.create_temp_canvas_file(self.test_canvas_data)

        try:
            async def run_test():
                task = BatchProcessingTask(
                    task_id="single_task_test",
                    canvas_path=temp_canvas
                )

                result = await processor._process_single_task(task)

                self.assertIsNotNone(result)
                self.assertEqual(result.canvas_path, temp_canvas)
                self.assertTrue(hasattr(result, 'batch_task_id'))
                self.assertEqual(result.batch_task_id, "single_task_test")

            asyncio.run(run_test())

        finally:
            # 清理临时文件
            os.unlink(temp_canvas)

    def test_file_not_found_handling(self):
        """测试文件不存在处理"""
        processor = BatchCanvasProcessor()

        async def run_test():
            task = BatchProcessingTask(
                task_id="file_not_found_test",
                canvas_path="nonexistent_file.canvas"
            )

            with self.assertRaises(FileNotFoundError):
                await processor._process_single_task(task)

            # 验证错误被记录
            error_summary = processor.error_handler.get_summary()
            self.assertEqual(error_summary["total_errors"], 1)

        asyncio.run(run_test())


class TestCanvasBatchProcessorTool(unittest.TestCase):
    """测试canvas_batch_processor工具函数"""

    def test_missing_canvas_paths_parameter(self):
        """测试缺少canvas_paths参数"""
        async def run_test():
            result = await canvas_batch_processor({})
            content = result.get("content", [])
            self.assertGreater(len(content), 0)
            self.assertIn("缺少必需参数 'canvas_paths'", content[0]["text"])

        asyncio.run(run_test())

    def test_invalid_canvas_paths_type(self):
        """测试无效的canvas_paths类型"""
        async def run_test():
            result = await canvas_batch_processor({"canvas_paths": "not_a_list"})
            content = result.get("content", [])
            self.assertGreater(len(content), 0)
            self.assertIn("必须是列表类型", content[0]["text"])

        asyncio.run(run_test())

    def test_empty_canvas_paths_list(self):
        """测试空的canvas_paths列表"""
        async def run_test():
            result = await canvas_batch_processor({"canvas_paths": []})
            content = result.get("content", [])
            self.assertGreater(len(content), 0)
            self.assertIn("列表为空", content[0]["text"])

        asyncio.run(run_test())

    def test_invalid_detail_level(self):
        """测试无效的detail_level参数"""
        async def run_test():
            result = await canvas_batch_processor({
                "canvas_paths": ["test.canvas"],
                "detail_level": "invalid_level"
            })
            content = result.get("content", [])
            self.assertGreater(len(content), 0)
            self.assertIn("detail_level' 必须是", content[0]["text"])

        asyncio.run(run_test())

    def test_invalid_priority_threshold(self):
        """测试无效的priority_threshold参数"""
        async def run_test():
            result = await canvas_batch_processor({
                "canvas_paths": ["test.canvas"],
                "priority_threshold": 1.5  # 超出0.0-1.0范围
            })
            content = result.get("content", [])
            self.assertGreater(len(content), 0)
            self.assertIn("priority_threshold' 必须是0.0-1.0之间", content[0]["text"])

        asyncio.run(run_test())

    def test_invalid_max_concurrent(self):
        """测试无效的max_concurrent参数"""
        async def run_test():
            result = await canvas_batch_processor({
                "canvas_paths": ["test.canvas"],
                "max_concurrent": 0  # 必须是正整数
            })
            content = result.get("content", [])
            self.assertGreater(len(content), 0)
            self.assertIn("max_concurrent' 必须是正整数", content[0]["text"])

        asyncio.run(run_test())

    def test_valid_parameter_combinations(self):
        """测试有效参数组合"""
        async def run_test():
            # 创建临时Canvas文件
            temp_canvas = self.create_temp_canvas_file({
                "nodes": [{"id": "test", "type": "text", "text": "test", "x": 0, "y": 0, "width": 100, "height": 50, "color": "1"}],
                "edges": []
            })

            try:
                result = await canvas_batch_processor({
                    "canvas_paths": [temp_canvas],
                    "detail_level": "basic",
                    "include_recommendations": False,
                    "priority_threshold": 0.8,
                    "max_concurrent": 2
                })

                content = result.get("content", [])
                self.assertGreater(len(content), 0)
                # 应该包含批量处理报告
                report_text = content[0]["text"]
                self.assertIn("Canvas批量处理报告", report_text)

            finally:
                os.unlink(temp_canvas)

        if not CLAUDE_CODE_ENABLED:
            self.skipTest("Claude Code SDK未安装")
        else:
            asyncio.run(run_test())


class TestBatchProcessingReportFormatting(unittest.TestCase):
    """测试批量处理报告格式化"""

    def setUp(self):
        """设置测试数据"""
        from canvas_utils import CanvasScheduleResult

        # 创建模拟结果
        self.mock_batch_result = BatchProcessingResult(
            total_canvases=5,
            successful_count=4,
            failed_count=1,
            results=[
                CanvasScheduleResult(
                    analysis_summary="成功分析",
                    agent_recommendations=[],
                    estimated_time={},
                    success_probability=0.9,
                    canvas_path="success1.canvas",
                    success=True
                ),
                CanvasScheduleResult(
                    analysis_summary="失败分析",
                    agent_recommendations=[],
                    estimated_time={},
                    success_probability=0.0,
                    canvas_path="failed.canvas",
                    success=False,
                    error="File not found"
                )
            ],
            processing_time=12.5,
            progress_summary={
                "success_rate": 80.0,
                "failure_rate": 20.0,
                "average_time_per_task": 2.5
            },
            error_summary={
                "total_errors": 1,
                "error_types": ["FileNotFoundError"],
                "most_common_error": {"type": "FileNotFoundError", "count": 1},
                "recent_errors": [
                    {"task_id": "task_1", "error_type": "FileNotFoundError", "error_message": "File not found"}
                ]
            }
        )

    def test_report_formatting_structure(self):
        """测试报告格式化结构"""
        report = _format_batch_processing_report(self.mock_batch_result)

        # 验证报告包含关键信息
        self.assertIn("Canvas批量处理报告", report)
        self.assertIn("总Canvas数量: 5", report)
        self.assertIn("成功处理: 4", report)
        self.assertIn("处理失败: 1", report)
        self.assertIn("成功率: 80.0%", report)
        self.assertIn("总处理时间: 12.50秒", report)
        self.assertIn("平均处理时间: 2.50秒/Canvas", report)

    def test_progress_summary_in_report(self):
        """测试进度摘要在报告中"""
        report = _format_batch_processing_report(self.mock_batch_result)

        self.assertIn("进度摘要", report)
        self.assertIn("成功率: 80.0%", report)
        self.assertIn("失败率: 20.0%", report)
        self.assertIn("平均任务时间: 2.50秒", report)

    def test_error_summary_in_report(self):
        """测试错误摘要在报告中"""
        report = _format_batch_processing_report(self.mock_batch_result)

        self.assertIn("错误摘要", report)
        self.assertIn("总错误数: 1", report)
        self.assertIn("最常见错误: FileNotFoundError", report)
        self.assertIn("最近错误详情", report)

    def test_performance_statistics_in_report(self):
        """测试性能统计在报告中"""
        report = _format_batch_processing_report(self.mock_batch_result)

        self.assertIn("性能统计", report)
        self.assertIn("并发效率:", report)
        self.assertIn("Canvas/秒", report)

    def test_context7_validation_in_report(self):
        """测试Context7验证标识在报告中"""
        report = _format_batch_processing_report(self.mock_batch_result)

        self.assertIn("Context7验证", report)
        self.assertIn("Trust Score 8.8", report)
        self.assertIn("生产就绪", report)


class TestBatchProcessingPerformance(unittest.TestCase):
    """测试批量处理性能"""

    def setUp(self):
        """设置测试"""
        if not CLAUDE_CODE_ENABLED:
            self.skipTest("Claude Code SDK未安装")

    def test_concurrent_processing_performance(self):
        """测试并发处理性能"""
        # 创建多个测试Canvas文件
        test_files = []
        for i in range(3):
            canvas_data = {
                "nodes": [
                    {
                        "id": f"test_node_{i}",
                        "type": "text",
                        "text": f"测试节点{i}",
                        "x": 100,
                        "y": 100,
                        "width": 200,
                        "height": 80,
                        "color": "1"
                    }
                ],
                "edges": []
            }
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.canvas', delete=False, encoding='utf-8')
            json.dump(canvas_data, temp_file, ensure_ascii=False, indent=2)
            temp_file.close()
            test_files.append(temp_file.name)

        try:
            async def run_performance_test():
                processor = BatchCanvasProcessor(max_concurrent=2)

                start_time = time.time()
                result = await processor.batch_analyze_canvases(test_files, detail_level="basic")
                end_time = time.time()

                processing_time = end_time - start_time

                # 验证性能指标
                self.assertLess(processing_time, 30.0)  # 应该在30秒内完成
                self.assertEqual(result.total_canvases, 3)
                self.assertGreaterEqual(result.successful_count, 0)

                # 验证时间合理性
                self.assertGreater(result.processing_time, 0)
                self.assertLess(result.get_average_processing_time(), processing_time + 5.0)  # 允许一定误差

            asyncio.run(run_performance_test())

        finally:
            # 清理临时文件
            for temp_file in test_files:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)


if __name__ == "__main__":
    # 运行所有测试
    unittest.main(verbosity=2)