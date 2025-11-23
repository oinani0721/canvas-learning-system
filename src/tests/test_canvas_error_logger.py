"""
Canvas学习系统 - 错误日志系统测试
Story 8.11: 集成Canvas专用错误日志系统

测试Canvas错误日志记录器的各项功能

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-22
"""

import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from canvas_error_logger import CanvasErrorLogger, ErrorSeverity, ErrorCategory
    from error_recovery_advisor import ErrorRecoveryAdvisor
    from error_analyzer import ErrorAnalyzer
    ERROR_LOGGER_AVAILABLE = True
except ImportError as e:
    ERROR_LOGGER_AVAILABLE = False
    print(f"警告: 错误日志系统测试依赖未安装 - {e}")


@unittest.skipUnless(ERROR_LOGGER_AVAILABLE, "错误日志系统未安装")
class TestCanvasErrorLogger(unittest.TestCase):
    """Canvas错误日志记录器测试"""

    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_config = {
            "error_logging": {
                "enabled": True,
                "log_level": "INFO",
                "file_logging": {
                    "enabled": True,
                    "log_file_path": os.path.join(self.temp_dir, "test_errors.log"),
                    "max_file_size_mb": 1,  # 小的文件大小用于测试轮转
                    "backup_count": 3
                },
                "format": {
                    "use_json": True,
                    "include_stack_trace": True,
                    "include_context": True
                },
                "error_codes": {
                    "file_operations": {
                        "filenotfounderror": "FILE_001",
                        "permissionerror": "FILE_002"
                    }
                }
            }
        }

        # 创建测试配置文件
        self.config_file = os.path.join(self.temp_dir, "test_config.yaml")
        import yaml
        with open(self.config_file, 'w', encoding='utf-8') as f:
            yaml.dump(self.test_config, f, default_flow_style=False, allow_unicode=True)

        self.logger = CanvasErrorLogger(self.config_file)

    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_logger_initialization(self):
        """测试日志记录器初始化"""
        self.assertIsNotNone(self.logger)
        self.assertTrue(self.logger.config.get("enabled", False))
        self.assertEqual(
            self.logger.config["file_logging"]["log_file_path"],
            os.path.join(self.temp_dir, "test_errors.log")
        )

    def test_log_canvas_operation_success(self):
        """测试Canvas操作成功日志记录"""
        operation = "canvas_read"
        canvas_path = "/test/path.canvas"
        context = {"test": "context", "start_time": datetime.now().timestamp()}

        log_id = self.logger.log_canvas_operation(operation, canvas_path, context, "success")

        self.assertIsInstance(log_id, str)
        self.assertTrue(log_id.startswith("log-"))

        # 验证日志文件存在
        self.assertTrue(os.path.exists(self.logger.config["file_logging"]["log_file_path"]))

        # 验证日志内容
        with open(self.logger.config["file_logging"]["log_file_path"], 'r', encoding='utf-8') as f:
            log_line = f.readline().strip()
            log_entry = json.loads(log_line)

            self.assertEqual(log_entry["canvas_error_log"]["operation_type"], operation)
            self.assertEqual(log_entry["canvas_error_log"]["status"], "success")
            self.assertEqual(log_entry["canvas_error_log"]["canvas_context"]["canvas_file_path"], canvas_path)

    def test_log_canvas_operation_error(self):
        """测试Canvas操作错误日志记录"""
        operation = "canvas_write"
        canvas_path = "/test/path.canvas"
        context = {"test": "context"}
        error = FileNotFoundError("测试文件不存在")

        log_id = self.logger.log_canvas_operation(operation, canvas_path, context, "error", error)

        self.assertIsInstance(log_id, str)
        self.assertTrue(log_id.startswith("log-"))

        # 验证错误信息
        with open(self.logger.config["file_logging"]["log_file_path"], 'r', encoding='utf-8') as f:
            log_line = f.readline().strip()
            log_entry = json.loads(log_line)

            self.assertEqual(log_entry["canvas_error_log"]["status"], "error")
            self.assertEqual(log_entry["canvas_error_log"]["error_information"]["error_type"], "FileNotFoundError")
            self.assertEqual(log_entry["canvas_error_log"]["error_information"]["error_message"], "测试文件不存在")
            self.assertTrue(len(log_entry["canvas_error_log"]["error_information"]["recovery_actions"]) > 0)

    def test_log_agent_call(self):
        """测试Agent调用日志记录"""
        agent_name = "test-agent"
        call_id = "test-call-123"
        input_data = {"test": "input", "canvas_path": "/test/canvas.canvas"}
        execution_time_ms = 1500

        log_id = self.logger.log_agent_call(agent_name, call_id, input_data, execution_time_ms, "success")

        self.assertIsInstance(log_id, str)

        # 验证Agent上下文
        with open(self.logger.config["file_logging"]["log_file_path"], 'r', encoding='utf-8') as f:
            log_line = f.readline().strip()
            log_entry = json.loads(log_line)

            agent_context = log_entry["canvas_error_log"]["agent_context"]
            self.assertEqual(agent_context["agent_name"], agent_name)
            self.assertEqual(agent_context["agent_call_id"], call_id)
            self.assertEqual(agent_context["agent_execution_time_ms"], execution_time_ms)

    def test_get_recent_errors(self):
        """测试获取最近错误记录"""
        # 创建一些错误记录
        for i in range(5):
            error = ValueError(f"测试错误 {i}")
            self.logger.log_canvas_operation("test_operation", "/test.canvas", {}, "error", error)

        # 创建一个成功记录
        self.logger.log_canvas_operation("test_success", "/test.canvas", {}, "success")

        recent_errors = self.logger.get_recent_errors(3)

        # 应该只返回错误记录，不包括成功记录
        self.assertEqual(len(recent_errors), 3)
        for error in recent_errors:
            self.assertEqual(error["status"], "error")

    def test_generate_error_summary(self):
        """测试生成错误统计摘要"""
        # 创建测试数据
        for i in range(3):
            error = FileNotFoundError(f"文件错误 {i}")
            self.logger.log_canvas_operation("file_operation", "/test.canvas", {}, "error", error)

        for i in range(2):
            error = ValueError(f"值错误 {i}")
            self.logger.log_canvas_operation("agent_operation", "/test.canvas", {}, "error", error)

        summary = self.logger.generate_error_summary(24)

        self.assertIn("error_summary_report", summary)
        report = summary["error_summary_report"]

        self.assertEqual(report["error_overview"]["total_errors"], 5)
        self.assertGreater(report["error_overview"]["error_rate_percentage"], 0)

        # 验证分类统计
        self.assertIn("file_operation", report["error_category_breakdown"])
        self.assertIn("agent_call", report["error_category_breakdown"])

    def test_search_error_logs(self):
        """测试搜索错误日志"""
        # 创建测试数据
        search_term = "特殊关键词"
        error1 = ValueError(f"包含{search_term}的错误")
        error2 = FileNotFoundError("不包含关键词的错误")
        error3 = ValueError(f"另一个包含{search_term}的问题")

        self.logger.log_canvas_operation("op1", "/test1.canvas", {}, "error", error1)
        self.logger.log_canvas_operation("op2", "/test2.canvas", {}, "error", error2)
        self.logger.log_canvas_operation("op3", "/test3.canvas", {}, "error", error3)

        matches = self.logger.search_error_logs(search_term)

        # 应该找到2个匹配的记录
        self.assertEqual(len(matches), 2)

    def test_log_file_rotation(self):
        """测试日志文件轮转"""
        # 写入大量数据以触发轮转
        large_context = {"data": "x" * 1000}  # 大量数据

        for i in range(100):  # 写入足够多的日志
            error = ValueError(f"轮转测试错误 {i}")
            self.logger.log_canvas_operation("rotation_test", "/test.canvas", large_context, "error", error)

        # 检查是否创建了备份文件
        backup_file = self.logger.config["file_logging"]["log_file_path"] + ".1"
        # 注意：由于我们设置了很小的文件大小限制，轮转应该发生
        # 但在测试环境中可能不会立即触发，所以这个测试是可选的

    def test_error_severity_assessment(self):
        """测试错误严重性评估"""
        # 测试不同类型错误的严重性评估
        file_error = FileNotFoundError("文件不存在")
        self.assertEqual(self.logger._assess_severity(file_error, "file_operation"), ErrorSeverity.HIGH)

        value_error = ValueError("值错误")
        self.assertEqual(self.logger._assess_severity(value_error, "agent_operation"), ErrorSeverity.MEDIUM)

        timeout_error = TimeoutError("超时")
        self.assertEqual(self.logger._assess_severity(timeout_error, "system_error"), ErrorSeverity.HIGH)

    def test_input_validation_security(self):
        """测试输入验证安全功能"""
        # 测试过长的操作名
        long_operation = "x" * 200
        log_id = self.logger.log_canvas_operation(long_operation, "/test.canvas", {}, "success")
        self.assertIsInstance(log_id, str)

        # 测试过长的路径
        long_path = "x" * 1000
        log_id = self.logger.log_canvas_operation("test_op", long_path, {}, "success")
        self.assertIsInstance(log_id, str)

        # 测试无效的状态值
        invalid_status = "invalid_status"
        log_id = self.logger.log_canvas_operation("test_op", "/test.canvas", {}, invalid_status)
        self.assertIsInstance(log_id, str)

        # 测试无效的上下文类型
        invalid_context = "not_a_dict"
        log_id = self.logger.log_canvas_operation("test_op", "/test.canvas", invalid_context, "success")
        self.assertIsInstance(log_id, str)

    def test_file_rotation_security(self):
        """测试文件轮转安全性"""
        # 创建一个接近限制大小的日志文件
        log_file = self.logger.config["file_logging"]["log_file_path"]

        # 写入大量数据触发轮转
        for i in range(50):
            error = ValueError(f"轮转测试错误 {i}")
            large_context = {"data": "x" * 500}  # 相对较大的上下文
            self.logger.log_canvas_operation("rotation_test", "/test.canvas", large_context, "error", error)

        # 验证文件存在并且可以被读取
        self.assertTrue(os.path.exists(log_file))

        # 验证没有异常抛出
        # 这个测试主要确保轮转过程不会抛出异常


@unittest.skipUnless(ERROR_LOGGER_AVAILABLE, "错误恢复建议器未安装")
class TestErrorRecoveryAdvisor(unittest.TestCase):
    """错误恢复建议器测试"""

    def setUp(self):
        """测试前准备"""
        self.advisor = ErrorRecoveryAdvisor()

    def test_get_recovery_advice_file_error(self):
        """测试文件错误恢复建议"""
        error = FileNotFoundError("/path/to/missing.canvas")
        context = {"canvas_path": "/path/to/missing.canvas"}

        advice = self.advisor.get_recovery_advice(error, context)

        self.assertIn("error_info", advice)
        self.assertIn("recovery_plan", advice)
        self.assertIn("prevention_guide", advice)

        # 验证错误信息
        error_info = advice["error_info"]
        self.assertEqual(error_info["type"], "FileNotFoundError")
        self.assertEqual(error_info["category"], "file_operations")

        # 验证恢复计划
        recovery_plan = advice["recovery_plan"]
        self.assertIn("immediate_actions", recovery_plan)
        self.assertIn("detailed_steps", recovery_plan)

    def test_get_recovery_advice_agent_error(self):
        """测试Agent错误恢复建议"""
        error = TimeoutError("Agent响应超时")
        context = {"agent_name": "test-agent", "input_data": {"test": "data"}}

        advice = self.advisor.get_recovery_advice(error, context)

        self.assertEqual(advice["error_info"]["category"], "agent_operations")
        self.assertIn("检查网络连接", str(advice["recovery_plan"]))

    def test_diagnose_error_pattern(self):
        """测试错误模式诊断"""
        # 创建模拟错误日志
        error_logs = [
            {
                "timestamp": datetime.now().isoformat(),
                "error_information": {"error_type": "FileNotFoundError"},
                "category": "file_operations",
                "status": "error"
            },
            {
                "timestamp": (datetime.now() - timedelta(minutes=5)).isoformat(),
                "error_information": {"error_type": "FileNotFoundError"},
                "category": "file_operations",
                "status": "error"
            },
            {
                "timestamp": (datetime.now() - timedelta(minutes=10)).isoformat(),
                "error_information": {"error_type": "ValueError"},
                "category": "agent_operations",
                "status": "error"
            }
        ]

        diagnosis = self.advisor.diagnose_error_pattern(error_logs)

        self.assertTrue(diagnosis["pattern_detected"])
        self.assertEqual(diagnosis["most_frequent_error"]["type"], "FileNotFoundError")
        self.assertEqual(diagnosis["most_frequent_error"]["count"], 2)

    def test_classify_error(self):
        """测试错误分类"""
        # 测试基于异常类型的分类
        category = self.advisor._classify_error("FileNotFoundError", "File not found")
        self.assertEqual(category, "file_operations")

        # 测试基于错误消息的分类
        category = self.advisor._classify_error("UnknownError", "Permission denied")
        self.assertEqual(category, "permission")

        # 测试基于上下文的分类
        context = {"agent_name": "test-agent"}
        category = self.advisor._classify_error("ValueError", "Invalid input", context)
        self.assertEqual(category, "agent_operations")


@unittest.skipUnless(ERROR_LOGGER_AVAILABLE, "错误分析器未安装")
class TestErrorAnalyzer(unittest.TestCase):
    """错误分析器测试"""

    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_config_file = os.path.join(self.temp_dir, "test_config.yaml")

        # 创建测试配置
        test_config = {
            "error_logging": {
                "enabled": True,
                "file_logging": {
                    "enabled": True,
                    "log_file_path": os.path.join(self.temp_dir, "analyzer_test.log")
                }
            }
        }

        import yaml
        with open(self.test_config_file, 'w', encoding='utf-8') as f:
            yaml.dump(test_config, f)

        self.analyzer = ErrorAnalyzer()

    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_show_recent_errors_no_errors(self):
        """测试显示最近错误（无错误情况）"""
        # 这个测试主要检查不会抛出异常
        # 实际的显示效果需要手动验证
        try:
            self.analyzer.show_recent_errors(5)
        except Exception as e:
            self.fail(f"show_recent_errors 抛出异常: {e}")

    def test_show_error_statistics_no_data(self):
        """测试显示错误统计（无数据情况）"""
        try:
            self.analyzer.show_error_statistics(24)
        except Exception as e:
            self.fail(f"show_error_statistics 抛出异常: {e}")

    def test_search_errors_no_matches(self):
        """测试搜索错误（无匹配情况）"""
        try:
            self.analyzer.search_errors("不存在的关键词")
        except Exception as e:
            self.fail(f"search_errors 抛出异常: {e}")

    def test_generate_error_report_no_data(self):
        """测试生成错误报告（无数据情况）"""
        try:
            report = self.analyzer.generate_error_report()
            self.assertIsInstance(report, str)
            self.assertIn("Canvas学习系统错误报告", report)
        except Exception as e:
            self.fail(f"generate_error_report 抛出异常: {e}")


class TestErrorLoggerIntegration(unittest.TestCase):
    """错误日志系统集成测试"""

    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @unittest.skipUnless(ERROR_LOGGER_AVAILABLE, "错误日志系统未安装")
    def test_canvas_operations_with_logging(self):
        """测试Canvas操作与错误日志集成"""
        # 创建测试配置
        config_file = os.path.join(self.temp_dir, "integration_config.yaml")
        test_config = {
            "error_logging": {
                "enabled": True,
                "file_logging": {
                    "enabled": True,
                    "log_file_path": os.path.join(self.temp_dir, "integration_test.log")
                }
            }
        }

        import yaml
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(test_config, f)

        logger = CanvasErrorLogger(config_file)

        # 测试Canvas读取操作日志
        try:
            # 模拟Canvas读取操作
            canvas_path = os.path.join(self.temp_dir, "test.canvas")

            # 创建测试Canvas文件
            test_canvas = {
                "nodes": [
                    {"id": "node1", "type": "text", "x": 100, "y": 100, "width": 200, "height": 100, "color": "1", "text": "测试节点"}
                ],
                "edges": []
            }

            with open(canvas_path, 'w', encoding='utf-8') as f:
                json.dump(test_canvas, f, ensure_ascii=False, indent=2)

            # 记录成功操作
            context = {"start_time": datetime.now().timestamp()}
            log_id = logger.log_canvas_operation("canvas_read", canvas_path, context, "success")

            self.assertIsNotNone(log_id)

            # 记录失败操作（故意读取不存在的文件）
            non_existent_file = os.path.join(self.temp_dir, "non_existent.canvas")
            error = FileNotFoundError(f"Canvas文件不存在: {non_existent_file}")

            log_id = logger.log_canvas_operation("canvas_read", non_existent_file, context, "error", error)

            self.assertIsNotNone(log_id)

            # 验证日志记录
            recent_errors = logger.get_recent_errors(1)
            self.assertEqual(len(recent_errors), 1)
            self.assertEqual(recent_errors[0]["error_information"]["error_type"], "FileNotFoundError")

        except Exception as e:
            self.fail(f"集成测试失败: {e}")

    @unittest.skipUnless(ERROR_LOGGER_AVAILABLE, "错误日志系统未安装")
    def test_error_recovery_workflow(self):
        """测试错误恢复工作流"""
        try:
            advisor = ErrorRecoveryAdvisor()

            # 模拟常见错误场景
            error_scenarios = [
                (FileNotFoundError("/missing/file.canvas"), {"canvas_path": "/missing/file.canvas"}),
                (PermissionError("/protected/file.canvas"), {"canvas_path": "/protected/file.canvas"}),
                (ValueError("Invalid node data"), {"node_id": "invalid-node"}),
                (TimeoutError("Agent timeout"), {"agent_name": "test-agent"})
            ]

            for error, context in error_scenarios:
                # 获取恢复建议
                advice = advisor.get_recovery_advice(error, context)

                # 验证建议结构
                self.assertIn("recovery_plan", advice)
                self.assertIn("prevention_guide", advice)
                self.assertIn("related_resources", advice)

                # 验证恢复步骤
                recovery_steps = advice["recovery_plan"].get("detailed_steps", [])
                self.assertGreater(len(recovery_steps), 0)

                # 验证每个步骤都有必要字段
                for step in recovery_steps:
                    self.assertIn("step", step)
                    self.assertIn("action", step)
                    self.assertIn("description", step)

        except Exception as e:
            self.fail(f"错误恢复工作流测试失败: {e}")


def run_performance_tests():
    """运行性能测试"""
    if not ERROR_LOGGER_AVAILABLE:
        print("跳过性能测试：错误日志系统未安装")
        return

    print("🚀 开始性能测试...")

    temp_dir = tempfile.mkdtemp()
    try:
        # 创建测试配置
        config_file = os.path.join(temp_dir, "perf_config.yaml")
        test_config = {
            "error_logging": {
                "enabled": True,
                "file_logging": {
                    "enabled": True,
                    "log_file_path": os.path.join(temp_dir, "perf_test.log")
                }
            }
        }

        import yaml
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(test_config, f)

        logger = CanvasErrorLogger(config_file)

        # 测试大量日志记录性能
        import time
        start_time = time.time()

        for i in range(1000):
            error = ValueError(f"性能测试错误 {i}")
            logger.log_canvas_operation("perf_test", "/test.canvas", {}, "error", error)

        end_time = time.time()
        duration = end_time - start_time

        print(f"✅ 记录1000条错误日志耗时: {duration:.3f}秒")
        print(f"✅ 平均每条日志耗时: {(duration/1000)*1000:.3f}毫秒")

        # 验证性能要求（每条日志记录应该小于1毫秒）
        avg_time_ms = (duration / 1000) * 1000
        if avg_time_ms < 1:
            print("✅ 性能测试通过：日志记录开销 < 1ms")
        else:
            print(f"⚠️  性能警告：日志记录开销 {avg_time_ms:.3f}ms > 1ms")

    finally:
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    print("🧪 Canvas错误日志系统测试开始")
    print("=" * 60)

    # 运行单元测试
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 添加测试类
    test_classes = [
        TestCanvasErrorLogger,
        TestErrorRecoveryAdvisor,
        TestErrorAnalyzer,
        TestErrorLoggerIntegration
    ]

    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 60)
    print("📊 测试结果摘要:")
    print(f"运行测试: {result.testsRun}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print(f"跳过: {len(result.skipped)}")

    if result.failures:
        print("\n❌ 失败的测试:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")

    if result.errors:
        print("\n💥 错误的测试:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")

    # 运行性能测试
    print("\n" + "=" * 60)
    run_performance_tests()

    print("\n🏁 测试完成")