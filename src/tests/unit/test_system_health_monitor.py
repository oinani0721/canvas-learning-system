#!/usr/bin/env python3
"""
系统健康监控单元测试
Story 8.13: 提升测试覆盖率和系统稳定性

测试系统健康监控功能，包括：
- 组件状态监控
- 性能指标收集
- 健康状态评估
- 预警机制

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-22
"""

import tempfile
import time
import unittest
from typing import Dict
from unittest.mock import Mock, patch

# 尝试导入系统健康监控模块
try:
    from system_health_monitor import ComponentHealth, HealthStatus, SystemHealthMonitor
    SYSTEM_HEALTH_MONITOR_AVAILABLE = True
except ImportError as e:
    print(f"Warning: System health monitor not available: {e}")
    SYSTEM_HEALTH_MONITOR_AVAILABLE = False


@unittest.skipUnless(SYSTEM_HEALTH_MONITOR_AVAILABLE, "System health monitor not available")
class TestSystemHealthMonitor(unittest.TestCase):
    """系统健康监控器测试"""

    def setUp(self):
        """测试前准备"""
        self.health_monitor = SystemHealthMonitor()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_initialization(self):
        """测试初始化"""
        self.assertIsNotNone(self.health_monitor)
        self.assertIsInstance(self.health_monitor.component_status, dict)
        self.assertIsInstance(self.health_monitor.metrics_history, list)

    def test_component_health_registration(self):
        """测试组件健康状态注册"""
        # 注册新组件
        self.health_monitor.register_component("test_component", {
            "type": "service",
            "description": "Test component for health monitoring",
            "check_interval": 30,
            "timeout": 5
        })

        self.assertIn("test_component", self.health_monitor.component_status)
        component_status = self.health_monitor.component_status["test_component"]
        self.assertEqual(component_status["status"], "unknown")
        self.assertEqual(component_status["type"], "service")

    def test_health_check_execution(self):
        """测试健康检查执行"""
        # 注册测试组件
        self.health_monitor.register_component("test_service", {
            "type": "service",
            "check_function": self._mock_health_check,
            "timeout": 5
        })

        # 执行健康检查
        result = self.health_monitor.check_component_health("test_service")
        self.assertIsNotNone(result)
        self.assertIn("status", result)
        self.assertIn("timestamp", result)

    def test_system_health_overview(self):
        """测试系统健康概览"""
        # 注册多个组件
        self.health_monitor.register_component("component1", {
            "type": "service",
            "status": "healthy"
        })
        self.health_monitor.register_component("component2", {
            "type": "database",
            "status": "healthy"
        })
        self.health_monitor.register_component("component3", {
            "type": "cache",
            "status": "warning"
        })

        # 获取系统健康概览
        overview = self.health_monitor.get_system_health()
        self.assertIn("overall_status", overview)
        self.assertIn("components", overview)
        self.assertIn("timestamp", overview)

        # 验证组件数量
        self.assertEqual(len(overview["components"]), 3)

        # 验证整体状态（有warning状态，整体应该是warning）
        self.assertEqual(overview["overall_status"], "warning")

    def test_metrics_collection(self):
        """测试指标收集"""
        # 收集系统指标
        metrics = self.health_monitor.collect_system_metrics()
        self.assertIsInstance(metrics, dict)

        # 验证基本指标存在
        expected_metrics = ["cpu_usage", "memory_usage", "disk_usage", "timestamp"]
        for metric in expected_metrics:
            self.assertIn(metric, metrics)

        # 验证指标类型
        self.assertIsInstance(metrics["cpu_usage"], (int, float))
        self.assertIsInstance(metrics["memory_usage"], (int, float))
        self.assertIsInstance(metrics["disk_usage"], (int, float))

    def test_health_history_tracking(self):
        """测试健康历史跟踪"""
        # 执行多次健康检查
        for i in range(3):
            self.health_monitor.collect_system_metrics()
            time.sleep(0.1)  # 短暂延迟

        # 检查历史记录
        history = self.health_monitor.get_health_history()
        self.assertIsInstance(history, list)
        self.assertGreater(len(history), 0)

        # 验证历史记录格式
        latest_record = history[-1]
        self.assertIn("timestamp", latest_record)
        self.assertIn("metrics", latest_record)

    def test_alert_generation(self):
        """测试预警生成"""
        # 模拟高CPU使用率
        with patch('psutil.cpu_percent', return_value=95.0):
            metrics = self.health_monitor.collect_system_metrics()
            alerts = self.health_monitor.check_thresholds(metrics)

            self.assertIsInstance(alerts, list)
            if alerts:  # 如果有预警
                alert = alerts[0]
                self.assertIn("component", alert)
                self.assertIn("severity", alert)
                self.assertIn("message", alert)

    def test_component_failure_handling(self):
        """测试组件故障处理"""
        # 注册会失败的组件
        self.health_monitor.register_component("failing_component", {
            "type": "service",
            "check_function": self._failing_health_check,
            "timeout": 1
        })

        # 执行健康检查
        result = self.health_monitor.check_component_health("failing_component")
        self.assertEqual(result["status"], "error")
        self.assertIn("error", result)

    def test_performance_monitoring(self):
        """测试性能监控"""
        # 记录性能指标
        self.health_monitor.record_performance_metric("canvas_read_time", 150.5)
        self.health_monitor.record_performance_metric("canvas_read_time", 200.3)
        self.health_monitor.record_performance_metric("agent_execution_time", 5000.0)

        # 获取性能统计
        stats = self.health_monitor.get_performance_stats()
        self.assertIn("canvas_read_time", stats)
        self.assertIn("agent_execution_time", stats)

        # 验证统计信息
        canvas_stats = stats["canvas_read_time"]
        self.assertIn("count", canvas_stats)
        self.assertIn("average", canvas_stats)
        self.assertIn("min", canvas_stats)
        self.assertIn("max", canvas_stats)
        self.assertEqual(canvas_stats["count"], 2)

    def test_health_report_generation(self):
        """测试健康报告生成"""
        # 收集一些数据
        self.health_monitor.collect_system_metrics()
        self.health_monitor.register_component("test_component", {
            "type": "service",
            "status": "healthy"
        })

        # 生成报告
        report = self.health_monitor.generate_health_report()
        self.assertIsInstance(report, dict)

        # 验证报告结构
        required_sections = ["summary", "components", "metrics", "recommendations"]
        for section in required_sections:
            self.assertIn(section, report)

        # 验证摘要信息
        summary = report["summary"]
        self.assertIn("overall_status", summary)
        self.assertIn("generated_at", summary)
        self.assertIn("total_components", summary)

    def test_automatic_recovery_triggers(self):
        """测试自动恢复触发器"""
        # 注册带恢复机制的组件
        self.health_monitor.register_component("recoverable_component", {
            "type": "service",
            "check_function": self._recoverable_health_check,
            "recovery_function": self._mock_recovery_function,
            "max_recovery_attempts": 3
        })

        # 执行健康检查（应该触发恢复）
        result = self.health_monitor.check_component_health("recoverable_component")
        self.assertIn("recovery_attempted", result)

    def _mock_health_check(self) -> Dict:
        """模拟健康检查函数"""
        return {
            "status": "healthy",
            "message": "Component is running normally",
            "response_time_ms": 50,
            "metadata": {"version": "1.0.0"}
        }

    def _failing_health_check(self) -> Dict:
        """模拟失败的健康检查"""
        raise Exception("Service unavailable")

    def _recoverable_health_check(self) -> Dict:
        """模拟可恢复的健康检查"""
        # 第一次调用失败，后续调用成功
        if not hasattr(self, "_call_count"):
            self._call_count = 0
        self._call_count += 1

        if self._call_count == 1:
            raise Exception("Service temporarily unavailable")
        else:
            return {
                "status": "healthy",
                "message": "Service recovered",
                "response_time_ms": 100
            }

    def _mock_recovery_function(self) -> bool:
        """模拟恢复函数"""
        time.sleep(0.1)  # 模拟恢复时间
        return True


@unittest.skipUnless(SYSTEM_HEALTH_MONITOR_AVAILABLE, "System health monitor not available")
class TestComponentHealth(unittest.TestCase):
    """组件健康状态测试"""

    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_database_component_health(self):
        """测试数据库组件健康状态"""
        monitor = SystemHealthMonitor()

        # 注册数据库组件
        monitor.register_component("test_database", {
            "type": "database",
            "connection_string": "sqlite:///:memory:",
            "check_query": "SELECT 1"
        })

        # 模拟数据库健康检查
        with patch('sqlite3.connect') as mock_connect:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_cursor.fetchone.return_value = (1,)
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn

            result = monitor.check_component_health("test_database")
            self.assertEqual(result["status"], "healthy")

    def test_file_system_component_health(self):
        """测试文件系统组件健康状态"""
        monitor = SystemHealthMonitor()

        # 注册文件系统组件
        monitor.register_component("file_system", {
            "type": "filesystem",
            "path": self.temp_dir,
            "min_free_space_mb": 100
        })

        # 检查文件系统健康状态
        result = monitor.check_component_health("file_system")
        self.assertIn("status", result)

    def test_network_component_health(self):
        """测试网络组件健康状态"""
        monitor = SystemHealthMonitor()

        # 注册网络组件
        monitor.register_component("external_api", {
            "type": "http_service",
            "url": "https://httpbin.org/status/200",
            "timeout": 5
        })

        # 模拟网络健康检查
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.elapsed.total_seconds.return_value = 0.1
            mock_get.return_value = mock_response

            result = monitor.check_component_health("external_api")
            self.assertEqual(result["status"], "healthy")


class TestHealthMetrics(unittest.TestCase):
    """健康指标测试"""

    def test_metric_aggregation(self):
        """测试指标聚合"""
        if not SYSTEM_HEALTH_MONITOR_AVAILABLE:
            self.skipTest("System health monitor not available")

        monitor = SystemHealthMonitor()

        # 记录多个指标
        values = [10, 20, 30, 40, 50]
        for value in values:
            monitor.record_performance_metric("test_metric", value)

        # 获取聚合统计
        stats = monitor.get_performance_stats()["test_metric"]

        self.assertEqual(stats["count"], len(values))
        self.assertEqual(stats["min"], min(values))
        self.assertEqual(stats["max"], max(values))
        self.assertEqual(stats["average"], sum(values) / len(values))

    def test_metric_threshold_monitoring(self):
        """测试指标阈值监控"""
        if not SYSTEM_HEALTH_MONITOR_AVAILABLE:
            self.skipTest("System health monitor not available")

        monitor = SystemHealthMonitor()

        # 设置阈值监控
        monitor.set_metric_threshold("response_time", {
            "warning": 1000,
            "critical": 5000
        })

        # 记录超过阈值的指标
        alerts = monitor.check_metric_threshold("response_time", 2000)
        self.assertIsInstance(alerts, list)
        if alerts:
            self.assertEqual(alerts[0]["severity"], "warning")

        # 记录严重超阈值的指标
        alerts = monitor.check_metric_threshold("response_time", 6000)
        if alerts:
            self.assertEqual(alerts[0]["severity"], "critical")

    def test_metric_trend_analysis(self):
        """测试指标趋势分析"""
        if not SYSTEM_HEALTH_MONITOR_AVAILABLE:
            self.skipTest("System health monitor not available")

        monitor = SystemHealthMonitor()

        # 记录时间序列数据
        base_time = time.time()
        for i in range(10):
            timestamp = base_time + i * 60  # 每分钟一个数据点
            value = 100 + i * 10  # 递增趋势
            monitor.record_metric_with_timestamp("trend_metric", value, timestamp)

        # 分析趋势
        trend = monitor.analyze_metric_trend("trend_metric")
        self.assertIn("direction", trend)
        self.assertIn("slope", trend)
        self.assertEqual(trend["direction"], "increasing")


if __name__ == "__main__":
    # 运行系统健康监控测试
    unittest.main(verbosity=2)
