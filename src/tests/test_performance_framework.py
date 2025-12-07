"""
Canvas性能测试框架 - 完整测试套件

该模块提供性能测试框架的完整单元测试、集成测试和端到端测试，
确保所有组件的正确性和可靠性。

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-10-22
"""

import json
import os

# 导入要测试的模块
import sys
import tempfile
import unittest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.test_canvas_performance import (
    CanvasPerformanceTester,
    MemoryMonitor,
    PerformanceReportGenerator,
    PerformanceTestResult,
    StressTestResult,
    TestCanvasGenerator,
)
from tests.test_performance_baseline import PerformanceBaselineManager, RegressionTestResult


class TestMemoryMonitor(unittest.TestCase):
    """内存监控器测试"""

    def setUp(self):
        self.monitor = MemoryMonitor()

    def test_start_monitoring(self):
        """测试开始监控"""
        self.monitor.start_monitoring()
        self.assertIsNotNone(self.monitor.start_memory)
        self.assertIsNotNone(self.monitor.peak_memory)
        self.assertEqual(len(self.monitor.measurements), 1)

    def test_get_memory_usage(self):
        """测试获取内存使用情况"""
        self.monitor.start_monitoring()
        current, peak, growth = self.monitor.get_memory_usage()
        self.assertIsInstance(current, float)
        self.assertIsInstance(peak, float)
        self.assertIsInstance(growth, float)
        self.assertGreaterEqual(peak, current)


class TestTestCanvasGenerator(unittest.TestCase):
    """测试Canvas生成器测试"""

    def setUp(self):
        self.generator = TestCanvasGenerator()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        # 清理临时文件
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_generate_simple_canvas(self):
        """测试生成简单Canvas"""
        node_count = 10
        canvas_path = os.path.join(self.temp_dir, "test_simple.canvas")

        result_path = self.generator.generate_test_canvas(
            node_count, "simple", canvas_path
        )

        self.assertTrue(os.path.exists(result_path))
        self.assertEqual(result_path, canvas_path)

        # 验证Canvas结构
        with open(result_path, 'r', encoding='utf-8') as f:
            canvas_data = json.load(f)

        self.assertIn('nodes', canvas_data)
        self.assertIn('edges', canvas_data)
        self.assertEqual(len(canvas_data['nodes']), node_count)
        self.assertGreater(len(canvas_data['edges']), 0)

    def test_generate_medium_canvas(self):
        """测试生成中等复杂Canvas"""
        node_count = 50
        result_path = self.generator.generate_test_canvas(node_count, "medium")

        self.assertTrue(os.path.exists(result_path))

        # 验证聚类结构
        with open(result_path, 'r', encoding='utf-8') as f:
            canvas_data = json.load(f)

        self.assertEqual(len(canvas_data['nodes']), node_count)

    def test_generate_complex_canvas(self):
        """测试生成复杂Canvas"""
        node_count = 100
        result_path = self.generator.generate_test_canvas(node_count, "complex")

        self.assertTrue(os.path.exists(result_path))

        with open(result_path, 'r', encoding='utf-8') as f:
            canvas_data = json.load(f)

        self.assertEqual(len(canvas_data['nodes']), node_count)

    def test_generate_chaotic_canvas(self):
        """测试生成混乱Canvas"""
        node_count = 20
        result_path = self.generator.generate_test_canvas(node_count, "chaotic")

        self.assertTrue(os.path.exists(result_path))

        with open(result_path, 'r', encoding='utf-8') as f:
            canvas_data = json.load(f)

        self.assertEqual(len(canvas_data['nodes']), node_count)
        # 混乱模式应该有更多的连接
        self.assertGreater(len(canvas_data['edges']), node_count)

    def test_invalid_complexity(self):
        """测试无效的复杂度级别"""
        with self.assertRaises(ValueError):
            self.generator.generate_test_canvas(10, "invalid_complexity")


class TestCanvasPerformanceTester(unittest.TestCase):
    """Canvas性能测试器测试"""

    def setUp(self):
        self.tester = CanvasPerformanceTester()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        # 清理临时文件
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_generate_test_canvas(self):
        """测试生成测试Canvas"""
        result_path = self.tester.generate_test_canvas(50, "medium")
        self.assertTrue(os.path.exists(result_path))

    def test_run_performance_test(self):
        """测试运行性能测试"""
        # 生成测试Canvas
        canvas_path = self.tester.generate_test_canvas(20, "simple")

        # 运行性能测试
        result = self.tester.run_performance_test(canvas_path)

        self.assertIsInstance(result, PerformanceTestResult)
        self.assertEqual(result.node_count, 20)
        self.assertGreater(result.processing_time_ms, 0)

        # 清理
        try:
            os.remove(canvas_path)
        except:
            pass

    def test_run_stress_test(self):
        """测试运行压力测试"""
        node_counts = [10, 20]
        result = self.tester.run_stress_test(node_counts, iterations=1)

        self.assertIsInstance(result, StressTestResult)
        self.assertEqual(len(result.node_counts), 2)
        self.assertEqual(len(result.results), 2)
        self.assertIsNotNone(result.summary_statistics)

    def test_monitor_memory_usage(self):
        """测试内存监控"""
        canvas_path = self.tester.generate_test_canvas(10, "simple")
        result = self.tester.monitor_memory_usage(canvas_path)

        self.assertIsInstance(result, dict)
        self.assertIn('memory_usage_mb', result)
        self.assertIn('memory_peak_mb', result)
        self.assertIn('node_count', result)

        # 清理
        try:
            os.remove(canvas_path)
        except:
            pass


class TestPerformanceBaselineManager(unittest.TestCase):
    """性能基准管理器测试"""

    def setUp(self):
        self.temp_file = tempfile.mktemp(suffix='.json')
        self.manager = PerformanceBaselineManager(self.temp_file)

    def tearDown(self):
        # 清理临时文件
        try:
            os.remove(self.temp_file)
        except:
            pass

    def test_establish_baseline(self):
        """测试建立基准"""
        from tests.test_canvas_performance import TestEnvironment

        # 创建测试结果
        results = [
            PerformanceTestResult(
                test_name="test1",
                node_count=10,
                edge_count=5,
                processing_time_ms=100.0,
                memory_usage_mb=50.0,
                memory_peak_mb=55.0,
                layout_quality_score=8.5,
                overlap_count=0,
                optimizations_applied=3,
                success=True
            )
        ]

        test_env = TestEnvironment(
            python_version="3.9.0",
            platform="test",
            cpu_count=4,
            memory_gb=8.0
        )

        baseline_id = self.manager.establish_baseline(results, test_env, "测试基准")
        self.assertIsNotNone(baseline_id)
        self.assertIn(baseline_id, self.manager.baselines)

    def test_list_baselines(self):
        """测试列出基准"""
        baselines = self.manager.list_baselines()
        self.assertIsInstance(baselines, list)

    def test_get_baseline_metrics(self):
        """测试获取基准指标"""
        # 先建立基准
        self.test_establish_baseline()

        metrics = self.manager.get_baseline_metrics()
        self.assertIsInstance(metrics, dict)


class TestPerformanceReportGenerator(unittest.TestCase):
    """性能报告生成器测试"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.generator = PerformanceReportGenerator()

    def tearDown(self):
        # 清理临时文件
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_generate_simple_report(self):
        """测试生成简单报告"""
        # 创建测试结果
        results = [
            PerformanceTestResult(
                test_name="test1",
                node_count=10,
                edge_count=5,
                processing_time_ms=100.0,
                memory_usage_mb=50.0,
                memory_peak_mb=55.0,
                layout_quality_score=8.5,
                overlap_count=0,
                optimizations_applied=3,
                success=True
            )
        ]

        from tests.test_canvas_performance import TestEnvironment
        test_env = TestEnvironment(
            python_version="3.9.0",
            platform="test",
            cpu_count=4,
            memory_gb=8.0
        )

        # 生成报告
        output_path = os.path.join(self.temp_dir, "test_report.html")
        result_path = self.generator.generate_performance_report(
            results, test_env, output_path=output_path
        )

        self.assertTrue(os.path.exists(result_path))
        self.assertTrue(result_path.endswith('.html'))

        # 检查JSON报告是否也生成
        json_path = result_path.replace('.html', '.json')
        self.assertTrue(os.path.exists(json_path))

    def test_calculate_summary_statistics(self):
        """测试计算汇总统计"""
        results = [
            PerformanceTestResult(
                test_name="test1",
                node_count=10,
                edge_count=5,
                processing_time_ms=100.0,
                memory_usage_mb=50.0,
                memory_peak_mb=55.0,
                layout_quality_score=8.5,
                overlap_count=0,
                optimizations_applied=3,
                success=True
            ),
            PerformanceTestResult(
                test_name="test2",
                node_count=20,
                edge_count=10,
                processing_time_ms=200.0,
                memory_usage_mb=60.0,
                memory_peak_mb=65.0,
                layout_quality_score=9.0,
                overlap_count=1,
                optimizations_applied=5,
                success=True
            )
        ]

        summary = self.generator._calculate_summary_statistics(results)

        self.assertEqual(summary['total_tests'], 2)
        self.assertEqual(summary['successful_tests'], 2)
        self.assertEqual(summary['failed_tests'], 0)
        self.assertEqual(summary['success_rate'], 100.0)
        self.assertIn('processing_time_stats', summary)
        self.assertIn('memory_usage_stats', summary)


class TestIntegration(unittest.TestCase):
    """集成测试"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        # 清理临时文件
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_end_to_end_performance_test(self):
        """端到端性能测试"""
        # 创建性能测试器
        tester = CanvasPerformanceTester()

        # 生成测试Canvas
        canvas_path = tester.generate_test_canvas(15, "simple")
        self.assertTrue(os.path.exists(canvas_path))

        # 运行性能测试
        result = tester.run_performance_test(canvas_path)
        self.assertTrue(result.success)
        self.assertEqual(result.node_count, 15)

        # 创建基准管理器
        baseline_manager = PerformanceBaselineManager()

        # 建立基准
        baseline_id = baseline_manager.establish_baseline(
            [result],
            tester.test_environment,
            "集成测试基准"
        )
        self.assertIsNotNone(baseline_id)

        # 比较性能
        comparison_result = baseline_manager.compare_with_baseline([result])
        self.assertIsInstance(comparison_result, RegressionTestResult)

        # 生成报告
        report_generator = PerformanceReportGenerator()
        report_path = report_generator.generate_performance_report(
            [result],
            tester.test_environment,
            comparison_result
        )
        self.assertTrue(os.path.exists(report_path))

        # 清理
        try:
            os.remove(canvas_path)
        except:
            pass

    def test_stress_test_with_multiple_sizes(self):
        """多规模压力测试"""
        tester = CanvasPerformanceTester()

        # 运行小规模压力测试
        node_counts = [5, 10, 15]
        result = tester.run_stress_test(node_counts, iterations=1)

        self.assertIsInstance(result, StressTestResult)
        self.assertEqual(len(result.results), 3)

        # 验证所有测试都有结果
        successful_results = [r for r in result.results if r.success]
        self.assertGreater(len(successful_results), 0)


def create_performance_test_suite():
    """创建性能测试测试套件"""
    suite = unittest.TestSuite()

    # 添加各个测试类
    test_classes = [
        TestMemoryMonitor,
        TestTestCanvasGenerator,
        TestCanvasPerformanceTester,
        TestPerformanceBaselineManager,
        TestPerformanceReportGenerator,
        TestIntegration
    ]

    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)

    return suite


def run_performance_tests():
    """运行所有性能测试"""
    suite = create_performance_test_suite()
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print(f"\n{'='*50}")
    print("性能测试框架测试结果:")
    print(f"运行测试: {result.testsRun}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print(f"跳过: {len(result.skipped)}")

    if result.failures:
        print("\n失败的测试:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")

    if result.errors:
        print("\n错误的测试:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('Exception:')[-1].strip()}")

    success_rate = (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100
    print(f"\n成功率: {success_rate:.1f}%")

    return result.wasSuccessful()


if __name__ == '__main__':
    # 运行测试
    success = run_performance_tests()
    sys.exit(0 if success else 1)
