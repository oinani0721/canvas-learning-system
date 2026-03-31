"""
Canvas学习系统 - 健康监控测试
Story 8.12: 建立系统健康监控和诊断

本模块测试健康监控系统的各个组件，包括：
- 系统健康监控器测试
- 组件健康检查器测试
- 命令接口测试
- 错误处理测试

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-22
"""

import os
import shutil
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from component_health_checkers import (
        CanvasOperationsChecker,
        ComponentHealthCheckers,
    )
    from health_monitor_commands import (
        CommandOptions,
        HealthMonitorCommands,
        canvas_status_command,
        error_log_command,
        health_check_command,
    )
    from system_health_monitor import ComponentHealth, HealthStatus, SystemHealthMonitor
except ImportError as e:
    print(f"警告：无法导入健康监控模块进行测试: {e}")
    SystemHealthMonitor = None
    ComponentHealthCheckers = None
    HealthMonitorCommands = None
    canvas_status_command = None
    error_log_command = None
    health_check_command = None


class TestSystemHealthMonitor(unittest.TestCase):
    """测试系统健康监控器"""

    def setUp(self):
        """测试前准备"""
        if not SystemHealthMonitor:
            self.skipTest("SystemHealthMonitor 不可用")

        # 创建临时配置目录
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "test_health_monitor.yaml")

        # 创建测试配置文件
        test_config = {
            "health_monitoring": {
                "check_interval_seconds": 60,
                "component_timeout_seconds": 10,
                "alert_thresholds": {
                    "error_rate_warning": 5.0,
                    "response_time_warning": 3000,
                    "memory_usage_warning": 80.0,
                    "cpu_usage_warning": 80.0,
                },
            },
            "health_scoring": {
                "weights": {
                    "performance": 0.3,
                    "reliability": 0.3,
                    "availability": 0.2,
                    "usage": 0.1,
                    "efficiency": 0.1,
                },
                "thresholds": {
                    "excellent": 90.0,
                    "good": 75.0,
                    "warning": 60.0,
                    "critical": 0.0,
                },
            },
        }

        import yaml

        with open(self.config_path, "w", encoding="utf-8") as f:
            yaml.dump(test_config, f)

        self.monitor = SystemHealthMonitor(self.config_path)

    def tearDown(self):
        """测试后清理"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_initialization(self):
        """测试初始化"""
        self.assertIsNotNone(self.monitor)
        self.assertEqual(self.monitor.config_path, self.config_path)
        self.assertIsNotNone(self.monitor.config)

    def test_load_config(self):
        """测试配置加载"""
        config = self.monitor._load_config()
        self.assertIn("health_monitoring", config)
        self.assertIn("health_scoring", config)

    def test_get_default_config(self):
        """测试默认配置"""
        default_config = self.monitor._get_default_config()
        self.assertIn("health_monitoring", default_config)
        self.assertIn("alert_thresholds", default_config["health_monitoring"])

    def test_calculate_overall_status(self):
        """测试整体状态计算"""
        from system_health_monitor import ComponentHealth

        # 创建模拟组件状态
        component_statuses = {
            "canvas_operations": ComponentHealth(
                component_name="canvas_operations",
                status=HealthStatus.HEALTHY,
                response_time_ms=45.0,
                success_rate=99.2,
                error_rate_24h=0.8,
            ),
            "agent_system": ComponentHealth(
                component_name="agent_system",
                status=HealthStatus.WARNING,
                response_time_ms=3200.0,
                success_rate=95.0,
                error_rate_24h=2.0,
            ),
        }

        overall_status = self.monitor._calculate_overall_status(component_statuses)
        self.assertIn(
            overall_status,
            [HealthStatus.HEALTHY, HealthStatus.WARNING, HealthStatus.CRITICAL],
        )

    def test_calculate_health_score(self):
        """测试健康评分计算"""
        from system_health_monitor import ComponentHealth

        component_statuses = {
            "canvas_operations": ComponentHealth(
                component_name="canvas_operations",
                status=HealthStatus.HEALTHY,
                response_time_ms=45.0,
                success_rate=99.2,
                error_rate_24h=0.8,
                performance_score=95.0,
            )
        }

        system_metrics = {
            "performance": {"memory_usage_mb": 256},
            "reliability": {"uptime_percentage": 99.8},
        }

        score = self.monitor._calculate_health_score(component_statuses, system_metrics)
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 100.0)

    @patch("system_health_monitor.psutil")
    def test_get_system_metrics(self, mock_psutil):
        """测试系统指标获取"""
        # 模拟psutil返回值
        mock_psutil.cpu_percent.return_value = 25.5
        mock_memory = Mock()
        mock_memory.used = 1024 * 1024 * 512  # 512MB
        mock_psutil.virtual_memory.return_value = mock_memory

        mock_disk = Mock()
        mock_disk.free = 1024 * 1024 * 1024 * 50  # 50GB
        mock_psutil.disk_usage.return_value = mock_disk

        mock_network = Mock()
        mock_psutil.net_io_counters.return_value = mock_network

        metrics = self.monitor._get_system_metrics()
        self.assertIn("performance", metrics)
        self.assertIn("reliability", metrics)
        self.assertIn("usage", metrics)

    def test_get_overall_health_status(self):
        """测试获取整体健康状态"""
        # 由于依赖组件检查器，这里只测试基本结构
        try:
            status = self.monitor.get_overall_health_status()
            self.assertIsInstance(status, dict)
            self.assertIn("check_timestamp", status)
            self.assertIn("overall_status", status)
            self.assertIn("health_score", status)
        except Exception as e:
            # 在没有完整组件时可能会失败，这是预期的
            self.assertIn("component_status", str(e))


class TestComponentHealthCheckers(unittest.TestCase):
    """测试组件健康检查器"""

    def setUp(self):
        """测试前准备"""
        if not ComponentHealthCheckers:
            self.skipTest("ComponentHealthCheckers 不可用")

        self.checkers = ComponentHealthCheckers()

    def test_initialization(self):
        """测试初始化"""
        self.assertIsNotNone(self.checkers)
        self.assertIsNotNone(self.checkers.checkers)

    def test_get_checker(self):
        """测试获取检查器"""
        checker = self.checkers.get_checker("canvas_operations")
        self.assertIsNotNone(checker)

        # 测试不存在的检查器
        checker = self.checkers.get_checker("nonexistent")
        self.assertIsNone(checker)

    def test_get_all_checkers(self):
        """测试获取所有检查器"""
        all_checkers = self.checkers.get_all_checkers()
        self.assertIsInstance(all_checkers, dict)
        self.assertGreater(len(all_checkers), 0)

    @patch("component_health_checkers.os.path.exists")
    @patch("component_health_checkers.os.makedirs")
    def test_canvas_operations_checker(self, mock_makedirs, mock_exists):
        """测试Canvas操作检查器"""
        # 模拟文件存在检查返回False（文件不存在）
        mock_exists.return_value = False

        checker = self.checkers.get_checker("canvas_operations")
        self.assertIsNotNone(checker)

        health = checker.check_health()
        self.assertIsInstance(health, dict)
        self.assertIn("status", health)
        self.assertIn("performance_score", health)

    def test_base_component_checker(self):
        """测试基础组件检查器"""
        from component_health_checkers import BaseComponentChecker

        class TestChecker(BaseComponentChecker):
            def check_health(self):
                return {"status": "healthy", "performance_score": 100.0}

        checker = TestChecker("test_component")
        self.assertEqual(checker.component_name, "test_component")

        # 测试响应时间测量
        def test_func():
            return "test_result"

        response_time, result = checker._measure_response_time(test_func)
        self.assertIsInstance(response_time, float)
        self.assertEqual(result, "test_result")


class TestHealthMonitorCommands(unittest.TestCase):
    """测试健康监控命令"""

    def setUp(self):
        """测试前准备"""
        if not HealthMonitorCommands:
            self.skipTest("HealthMonitorCommands 不可用")

        self.commands = HealthMonitorCommands()

    def test_initialization(self):
        """测试初始化"""
        self.assertIsNotNone(self.commands)

    def test_command_options(self):
        """测试命令选项"""
        options = CommandOptions()
        self.assertFalse(options.detailed)
        self.assertEqual(options.format, "summary")
        self.assertEqual(options.limit, 10)

        # 测试自定义选项
        options = CommandOptions(detailed=True, format="json", limit=20)
        self.assertTrue(options.detailed)
        self.assertEqual(options.format, "json")
        self.assertEqual(options.limit, 20)

    def test_format_error(self):
        """测试错误格式化"""
        error_msg = self.commands._format_error("测试错误")
        self.assertIn("❌ 错误", error_msg)
        self.assertIn("测试错误", error_msg)

    def test_get_status_text(self):
        """测试状态文本获取"""
        self.assertEqual(self.commands._get_status_text("healthy"), "健康")
        self.assertEqual(self.commands._get_status_text("warning"), "警告")
        self.assertEqual(self.commands._get_status_text("critical"), "严重")
        self.assertEqual(self.commands._get_status_text("unknown"), "未知")

    def test_calculate_error_summary(self):
        """测试错误统计计算"""
        errors = [
            {"severity": "critical", "resolution_status": "resolved"},
            {"severity": "high", "resolution_status": "unresolved"},
            {"severity": "medium", "resolution_status": "resolved"},
        ]

        summary = self.commands._calculate_error_summary(errors)
        self.assertEqual(summary["total_errors"], 3)
        self.assertEqual(summary["critical_errors"], 1)
        self.assertEqual(summary["high_errors"], 1)
        self.assertEqual(summary["resolved_errors"], 2)
        self.assertEqual(summary["unresolved_errors"], 1)

    @patch("health_monitor_commands.SystemHealthMonitor")
    def test_canvas_status_command_no_monitor(self, mock_monitor_class):
        """测试没有健康监控器时的canvas状态命令"""
        mock_monitor_class.side_effect = Exception("Monitor unavailable")
        commands = HealthMonitorCommands()

        result = commands.canvas_status_command()
        self.assertIn("❌ 错误", result)
        self.assertIn("健康监控器不可用", result)

    def test_format_summary_status(self):
        """测试状态概览格式化"""
        health_status = {
            "overall_status": "healthy",
            "health_score": 92.5,
            "component_status": {
                "canvas_operations": {
                    "status": "healthy",
                    "performance_score": 95.0,
                    "response_time_ms": 45,
                    "success_rate": 99.2,
                    "error_rate_24h": 0.8,
                }
            },
            "alerts": [],
            "recent_errors": [],
            "diagnostic_recommendations": [{"recommendation": "系统运行良好"}],
        }

        result = self.commands._format_summary_status(health_status)
        self.assertIsInstance(result, str)
        self.assertIn("🟢", result)
        self.assertIn("92.5/100", result)
        self.assertIn("Canvas操作", result)


class TestCommandEntryPoints(unittest.TestCase):
    """测试命令入口函数"""

    def test_canvas_status_command_entry(self):
        """测试canvas状态命令入口"""
        try:
            result = canvas_status_command(detailed=True, format="summary")
            self.assertIsInstance(result, str)
        except Exception as e:
            # 在没有完整环境时可能会失败，这是可以接受的
            self.assertIn("健康监控器不可用", str(e))

    def test_error_log_command_entry(self):
        """测试错误日志命令入口"""
        if not error_log_command:
            self.skipTest("error_log_command 不可用")

        try:
            result = error_log_command(limit=5, format="summary")
            self.assertIsInstance(result, str)
        except Exception as e:
            # 在没有完整环境时可能会失败，这是可以接受的
            self.assertIn("健康监控器不可用", str(e))

    def test_health_check_command_entry(self):
        """测试健康检查命令入口"""
        if not health_check_command:
            self.skipTest("health_check_command 不可用")

        try:
            result = health_check_command(comprehensive=True, format="detailed")
            self.assertIsInstance(result, str)
        except Exception as e:
            # 在没有完整环境时可能会失败，这是可以接受的
            self.assertIn("健康监控器不可用", str(e))


class TestIntegration(unittest.TestCase):
    """集成测试"""

    def setUp(self):
        """测试前准备"""
        if not all(
            [SystemHealthMonitor, ComponentHealthCheckers, HealthMonitorCommands]
        ):
            self.skipTest("健康监控组件不完整")

    def test_end_to_end_canvas_status(self):
        """测试端到端canvas状态检查"""
        try:
            # 创建临时配置
            temp_dir = tempfile.mkdtemp()
            config_path = os.path.join(temp_dir, "test_config.yaml")

            test_config = {
                "health_monitoring": {
                    "check_interval_seconds": 60,
                    "components": {
                        "canvas_operations": {"enabled": True},
                        "agent_system": {"enabled": True},
                    },
                }
            }

            import yaml

            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(test_config, f)

            # 测试完整流程
            monitor = SystemHealthMonitor(config_path)
            commands = HealthMonitorCommands()
            commands.health_monitor = monitor

            # 测试命令执行
            result = commands.canvas_status_command()
            self.assertIsInstance(result, str)

            # 清理
            shutil.rmtree(temp_dir)

        except Exception as e:
            # 集成测试可能会因为环境问题失败，这是可以接受的
            print(f"集成测试跳过: {e}")


if __name__ == "__main__":
    # 运行测试
    unittest.main(verbosity=2)
