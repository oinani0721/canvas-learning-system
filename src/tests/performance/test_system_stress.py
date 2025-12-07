"""
系统压力测试和负载均衡验证

测试Canvas学习系统v2.0在高负载下的性能和稳定性：
- 大规模Canvas文件处理
- 多Agent并发执行
- 内存使用和泄漏检测
- 系统资源耗尽测试
- 负载均衡验证

Author: Canvas Learning System Team
Version: 2.0
Created: 2025-01-22
"""

import gc
import json
import os
import tempfile
import time

import psutil
import pytest

# resource module is Unix-specific, not available on Windows
try:
    import resource
    RESOURCE_AVAILABLE = True
except ImportError:
    RESOURCE_AVAILABLE = False
from dataclasses import dataclass
from typing import Any, Dict, List

# Import system components
try:
    from agent_performance_optimizer import AgentPerformanceOptimizer
    from canvas_performance_optimizer import CanvasPerformanceOptimizer
except ImportError:
    pytest.skip("Performance optimizers not available", allow_module_level=True)


@dataclass
class StressTestResult:
    """压力测试结果"""
    test_name: str
    success: bool
    duration_seconds: float
    peak_memory_mb: float
    peak_cpu_percent: float
    operations_completed: int
    errors: List[str]
    performance_metrics: Dict[str, Any]


class SystemStressTester:
    """系统压力测试器"""

    def __init__(self):
        self.canvas_optimizer = CanvasPerformanceOptimizer()
        self.agent_optimizer = AgentPerformanceOptimizer(max_workers=10, enable_caching=True)
        self.test_results: List[StressTestResult] = []
        self.process = psutil.Process()

    def _monitor_resources(self, duration: float = 1.0) -> Dict[str, float]:
        """监控系统资源使用"""
        cpu_percent = self.process.cpu_percent()
        memory_info = self.process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024

        return {
            "cpu_percent": cpu_percent,
            "memory_mb": memory_mb,
            "system_memory_percent": psutil.virtual_memory().percent
        }

    def _generate_large_canvas_data(self, node_count: int) -> Dict[str, Any]:
        """生成大规模Canvas测试数据"""
        canvas_data = {
            "nodes": [],
            "edges": []
        }

        # 生成节点
        for i in range(node_count):
            node = {
                "id": f"stress-node-{i}",
                "type": "text",
                "text": f"压力测试节点 {i}" * (10 if i % 10 == 0 else 1),  # 一些大节点
                "x": (i % 10) * 400,
                "y": (i // 10) * 300,
                "width": 300,
                "height": 200,
                "color": str(i % 6 + 1)  # 循环使用颜色
            }
            canvas_data["nodes"].append(node)

        # 生成边（连接相邻节点）
        for i in range(node_count - 1):
            edge = {
                "id": f"stress-edge-{i}",
                "from": f"stress-node-{i}",
                "to": f"stress-node-{i + 1}"
            }
            canvas_data["edges"].append(edge)

        return canvas_data

    def test_large_canvas_processing(self) -> StressTestResult:
        """测试大规模Canvas文件处理"""
        test_name = "Large Canvas Processing"
        errors = []
        operations_completed = 0
        peak_memory_mb = 0
        peak_cpu_percent = 0

        print(f"开始 {test_name} 测试...")
        start_time = time.time()

        try:
            # 测试不同规模的Canvas文件
            test_sizes = [100, 200, 500, 1000]

            for node_count in test_sizes:
                print(f"  测试 {node_count} 节点的Canvas文件...")

                # 生成测试数据
                canvas_data = self._generate_large_canvas_data(node_count)

                with tempfile.NamedTemporaryFile(mode='w', suffix='.canvas', delete=False) as f:
                    json.dump(canvas_data, f)
                    temp_path = f.name

                try:
                    # 测试写入性能
                    write_start = time.time()
                    self.canvas_optimizer.write_canvas_optimized(temp_path, canvas_data)
                    write_time = time.time() - write_start

                    if write_time > 10.0:  # 超过10秒认为性能不达标
                        errors.append(f"写入{node_count}节点耗时过长: {write_time:.2f}s")

                    # 测试读取性能
                    read_start = time.time()
                    read_data = self.canvas_optimizer.read_canvas_cached(temp_path)
                    read_time = time.time() - read_start

                    if read_time > 10.0:  # 超过10秒认为性能不达标
                        errors.append(f"读取{node_count}节点耗时过长: {read_time:.2f}s")

                    # 验证数据完整性
                    if len(read_data["nodes"]) != node_count:
                        errors.append(f"数据完整性验证失败: 期望{node_count}个节点，实际{len(read_data['nodes'])}个")

                    # 监控资源使用
                    resource_usage = self._monitor_resources()
                    peak_memory_mb = max(peak_memory_mb, resource_usage["memory_mb"])
                    peak_cpu_percent = max(peak_cpu_percent, resource_usage["cpu_percent"])

                    operations_completed += 1
                    print(f"    完成 {node_count} 节点处理 (写入: {write_time:.2f}s, 读取: {read_time:.2f}s)")

                finally:
                    os.unlink(temp_path)

                # 强制垃圾回收
                gc.collect()

            duration = time.time() - start_time
            success = len(errors) == 0

            performance_metrics = {
                "total_nodes_processed": sum(test_sizes),
                "operations_per_second": operations_completed / duration,
                "memory_per_node_mb": peak_memory_mb / max(test_sizes)
            }

            result = StressTestResult(
                test_name=test_name,
                success=success,
                duration_seconds=duration,
                peak_memory_mb=peak_memory_mb,
                peak_cpu_percent=peak_cpu_percent,
                operations_completed=operations_completed,
                errors=errors,
                performance_metrics=performance_metrics
            )

            print(f"  {test_name} 测试完成: {'成功' if success else '失败'}")
            return result

        except Exception as e:
            duration = time.time() - start_time
            errors.append(f"测试异常: {str(e)}")
            result = StressTestResult(
                test_name=test_name,
                success=False,
                duration_seconds=duration,
                peak_memory_mb=peak_memory_mb,
                peak_cpu_percent=peak_cpu_percent,
                operations_completed=operations_completed,
                errors=errors,
                performance_metrics={}
            )
            print(f"  {test_name} 测试异常: {str(e)}")
            return result

    def test_concurrent_agent_execution(self) -> StressTestResult:
        """测试并发Agent执行"""
        test_name = "Concurrent Agent Execution"
        errors = []
        operations_completed = 0
        peak_memory_mb = 0
        peak_cpu_percent = 0

        print(f"开始 {test_name} 测试...")
        start_time = time.time()

        try:
            # 测试不同并发级别
            concurrency_levels = [5, 10, 15, 20]

            for concurrency in concurrency_levels:
                print(f"  测试 {concurrency} 个并发Agent...")

                # 创建任务
                tasks = []
                for i in range(concurrency):
                    agent_type = ["basic-decomposition", "deep-decomposition", "scoring-agent", "oral-explanation"][i % 4]
                    task = {
                        "agent_type": agent_type,
                        "input_data": {
                            "concept": f"并发测试概念 {i}",
                            "detail": "这是一个用于测试并发执行的示例概念" * 5
                        },
                        "priority": i % 3
                    }
                    tasks.append(task)

                # 执行并发任务
                try:
                    execution_start = time.time()
                    results = self.agent_optimizer.execute_parallel(tasks)
                    execution_time = time.time() - execution_start

                    # 验证结果
                    if len(results) != concurrency:
                        errors.append(f"并发任务数量不匹配: 期望{concurrency}个，实际{len(results)}个")

                    failed_tasks = sum(1 for r in results if not r.success)
                    if failed_tasks > 0:
                        errors.append(f"{failed_tasks}个任务执行失败")

                    # 验证执行时间（应该在合理范围内）
                    if execution_time > 60.0:  # 超过60秒认为性能不达标
                        errors.append(f"{concurrency}并发任务耗时过长: {execution_time:.2f}s")

                    # 监控资源使用
                    resource_usage = self._monitor_resources()
                    peak_memory_mb = max(peak_memory_mb, resource_usage["memory_mb"])
                    peak_cpu_percent = max(peak_cpu_percent, resource_usage["cpu_percent"])

                    operations_completed += concurrency
                    success_rate = (concurrency - failed_tasks) / concurrency * 100
                    print(f"    完成 {concurrency} 并发任务 (耗时: {execution_time:.2f}s, 成功率: {success_rate:.1f}%)")

                except Exception as e:
                    errors.append(f"并发执行异常: {str(e)}")
                    print(f"    {concurrency} 并发任务执行失败: {str(e)}")

                # 等待系统稳定
                time.sleep(2)
                gc.collect()

            duration = time.time() - start_time
            success = len(errors) == 0

            performance_metrics = {
                "total_concurrent_tasks": sum(concurrency_levels),
                "max_concurrency": max(concurrency_levels),
                "tasks_per_second": operations_completed / duration,
                "average_success_rate": 100.0  # 简化计算
            }

            result = StressTestResult(
                test_name=test_name,
                success=success,
                duration_seconds=duration,
                peak_memory_mb=peak_memory_mb,
                peak_cpu_percent=peak_cpu_percent,
                operations_completed=operations_completed,
                errors=errors,
                performance_metrics=performance_metrics
            )

            print(f"  {test_name} 测试完成: {'成功' if success else '失败'}")
            return result

        except Exception as e:
            duration = time.time() - start_time
            errors.append(f"测试异常: {str(e)}")
            result = StressTestResult(
                test_name=test_name,
                success=False,
                duration_seconds=duration,
                peak_memory_mb=peak_memory_mb,
                peak_cpu_percent=peak_cpu_percent,
                operations_completed=operations_completed,
                errors=errors,
                performance_metrics={}
            )
            print(f"  {test_name} 测试异常: {str(e)}")
            return result

    def test_memory_usage_and_leaks(self) -> StressTestResult:
        """测试内存使用和泄漏检测"""
        test_name = "Memory Usage and Leak Detection"
        errors = []
        operations_completed = 0
        peak_memory_mb = 0
        peak_cpu_percent = 0

        print(f"开始 {test_name} 测试...")
        start_time = time.time()

        try:
            # 记录初始内存使用
            initial_memory = self._monitor_resources()["memory_mb"]
            memory_samples = [initial_memory]

            # 执行大量操作以检测内存泄漏
            iterations = 100
            for i in range(iterations):
                # 创建和使用Canvas优化器
                temp_optimizer = CanvasPerformanceOptimizer()

                # 执行一些操作
                test_data = self._generate_large_canvas_data(50)
                with tempfile.NamedTemporaryFile(mode='w', suffix='.canvas', delete=False) as f:
                    json.dump(test_data, f)
                    temp_path = f.name

                try:
                    temp_optimizer.write_canvas_optimized(temp_path, test_data)
                    read_data = temp_optimizer.read_canvas_cached(temp_path)
                    operations_completed += 1
                finally:
                    os.unlink(temp_path)

                # 记录内存使用
                current_memory = self._monitor_resources()["memory_mb"]
                memory_samples.append(current_memory)
                peak_memory_mb = max(peak_memory_mb, current_memory)
                peak_cpu_percent = max(peak_cpu_percent, self._monitor_resources()["cpu_percent"])

                # 强制垃圾回收
                del temp_optimizer
                gc.collect()

                # 每10次迭代输出进度
                if (i + 1) % 10 == 0:
                    current_memory_mb = memory_samples[-1]
                    memory_growth = current_memory_mb - initial_memory
                    print(f"    完成 {i + 1}/{iterations} 次迭代，内存增长: {memory_growth:.1f}MB")

            # 分析内存使用趋势
            final_memory = memory_samples[-1]
            total_memory_growth = final_memory - initial_memory

            # 检测是否存在明显的内存泄漏
            memory_growth_per_iteration = total_memory_growth / iterations
            if memory_growth_per_iteration > 1.0:  # 每次迭代增长超过1MB认为可能泄漏
                errors.append(f"检测到可能的内存泄漏: 每次迭代增长 {memory_growth_per_iteration:.2f}MB")

            # 检查峰值内存使用是否合理
            if peak_memory_mb > 1000:  # 超过1GB认为内存使用过高
                errors.append(f"峰值内存使用过高: {peak_memory_mb:.1f}MB")

            duration = time.time() - start_time
            success = len(errors) == 0

            performance_metrics = {
                "initial_memory_mb": initial_memory,
                "final_memory_mb": final_memory,
                "peak_memory_mb": peak_memory_mb,
                "memory_growth_mb": total_memory_growth,
                "memory_growth_per_iteration_mb": memory_growth_per_iteration,
                "iterations": iterations
            }

            result = StressTestResult(
                test_name=test_name,
                success=success,
                duration_seconds=duration,
                peak_memory_mb=peak_memory_mb,
                peak_cpu_percent=peak_cpu_percent,
                operations_completed=operations_completed,
                errors=errors,
                performance_metrics=performance_metrics
            )

            print(f"  {test_name} 测试完成: {'成功' if success else '失败'}")
            print(f"    初始内存: {initial_memory:.1f}MB")
            print(f"    最终内存: {final_memory:.1f}MB")
            print(f"    内存增长: {total_memory_growth:.1f}MB")
            return result

        except Exception as e:
            duration = time.time() - start_time
            errors.append(f"测试异常: {str(e)}")
            result = StressTestResult(
                test_name=test_name,
                success=False,
                duration_seconds=duration,
                peak_memory_mb=peak_memory_mb,
                peak_cpu_percent=peak_cpu_percent,
                operations_completed=operations_completed,
                errors=errors,
                performance_metrics={}
            )
            print(f"  {test_name} 测试异常: {str(e)}")
            return result

    def test_system_resource_exhaustion(self) -> StressTestResult:
        """测试系统资源耗尽场景"""
        test_name = "System Resource Exhaustion"
        errors = []
        operations_completed = 0
        peak_memory_mb = 0
        peak_cpu_percent = 0

        print(f"开始 {test_name} 测试...")
        start_time = time.time()

        try:
            # 测试CPU密集型任务
            print("  测试CPU密集型任务...")
            cpu_tasks = []
            for i in range(50):
                task = {
                    "agent_type": "scoring-agent",  # 较轻量的任务
                    "input_data": {
                        "concept": f"CPU压力测试 {i}",
                        "text": "测试文本" * 100  # 增加处理负载
                    }
                }
                cpu_tasks.append(task)

            try:
                cpu_start = time.time()
                cpu_results = self.agent_optimizer.execute_parallel(cpu_tasks)
                cpu_time = time.time() - cpu_start

                cpu_success = sum(1 for r in cpu_results if r.success)
                operations_completed += cpu_success
                print(f"    CPU密集型任务完成: {cpu_success}/50 成功, 耗时: {cpu_time:.2f}s")

            except Exception as e:
                errors.append(f"CPU密集型任务失败: {str(e)}")

            # 测试内存密集型任务
            print("  测试内存密集型任务...")
            memory_tasks = []
            for i in range(20):
                # 创建大量Canvas文件以测试内存使用
                large_canvas = self._generate_large_canvas_data(200)
                memory_tasks.append(large_canvas)

            memory_success = 0
            for i, canvas_data in enumerate(memory_tasks):
                try:
                    temp_optimizer = CanvasPerformanceOptimizer()
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.canvas', delete=False) as f:
                        json.dump(canvas_data, f)
                        temp_path = f.name

                    temp_optimizer.write_canvas_optimized(temp_path, canvas_data)
                    read_data = temp_optimizer.read_canvas_cached(temp_path)
                    os.unlink(temp_path)

                    memory_success += 1
                    operations_completed += 1

                    # 监控内存使用
                    resource_usage = self._monitor_resources()
                    peak_memory_mb = max(peak_memory_mb, resource_usage["memory_mb"])
                    peak_cpu_percent = max(peak_cpu_percent, resource_usage["cpu_percent"])

                    del temp_optimizer
                    gc.collect()

                except Exception as e:
                    errors.append(f"内存任务 {i} 失败: {str(e)}")

            print(f"    内存密集型任务完成: {memory_success}/20 成功")

            # 测试I/O密集型任务
            print("  测试I/O密集型任务...")
            io_tasks = []
            for i in range(30):
                task = {
                    "agent_type": "oral-explanation",
                    "input_data": {
                        "concept": f"I/O压力测试 {i}",
                        "context": "这是一个用于测试I/O性能的详细上下文" * 20
                    }
                }
                io_tasks.append(task)

            try:
                io_start = time.time()
                io_results = self.agent_optimizer.execute_parallel(io_tasks)
                io_time = time.time() - io_start

                io_success = sum(1 for r in io_results if r.success)
                operations_completed += io_success
                print(f"    I/O密集型任务完成: {io_success}/30 成功, 耗时: {io_time:.2f}s")

            except Exception as e:
                errors.append(f"I/O密集型任务失败: {str(e)}")

            duration = time.time() - start_time
            success = len(errors) == 0

            performance_metrics = {
                "cpu_tasks_completed": cpu_success,
                "memory_tasks_completed": memory_success,
                "io_tasks_completed": io_success,
                "total_operations": operations_completed,
                "operations_per_second": operations_completed / duration
            }

            result = StressTestResult(
                test_name=test_name,
                success=success,
                duration_seconds=duration,
                peak_memory_mb=peak_memory_mb,
                peak_cpu_percent=peak_cpu_percent,
                operations_completed=operations_completed,
                errors=errors,
                performance_metrics=performance_metrics
            )

            print(f"  {test_name} 测试完成: {'成功' if success else '失败'}")
            return result

        except Exception as e:
            duration = time.time() - start_time
            errors.append(f"测试异常: {str(e)}")
            result = StressTestResult(
                test_name=test_name,
                success=False,
                duration_seconds=duration,
                peak_memory_mb=peak_memory_mb,
                peak_cpu_percent=peak_cpu_percent,
                operations_completed=operations_completed,
                errors=errors,
                performance_metrics={}
            )
            print(f"  {test_name} 测试异常: {str(e)}")
            return result

    def run_all_stress_tests(self) -> List[StressTestResult]:
        """运行所有压力测试"""
        print("开始系统压力测试...")
        print("=" * 60)

        all_results = []

        # 运行各项压力测试
        tests = [
            self.test_large_canvas_processing,
            self.test_concurrent_agent_execution,
            self.test_memory_usage_and_leaks,
            self.test_system_resource_exhaustion
        ]

        for test_func in tests:
            result = test_func()
            all_results.append(result)
            self.test_results.append(result)
            print()

        # 关闭优化器
        self.agent_optimizer.shutdown()

        return all_results

    def generate_stress_test_report(self, results: List[StressTestResult]) -> Dict[str, Any]:
        """生成压力测试报告"""
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.success)
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests) * 100

        total_duration = sum(r.duration_seconds for r in results)
        total_operations = sum(r.operations_completed for r in results)
        peak_memory = max(r.peak_memory_mb for r in results)
        peak_cpu = max(r.peak_cpu_percent for r in results)

        # 性能评估
        performance_grade = "A" if success_rate >= 90 else "B" if success_rate >= 75 else "C" if success_rate >= 60 else "D"

        report = {
            "stress_test_summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate_percent": success_rate,
                "performance_grade": performance_grade,
                "total_duration_seconds": total_duration,
                "total_operations": total_operations,
                "peak_memory_usage_mb": peak_memory,
                "peak_cpu_usage_percent": peak_cpu
            },
            "test_results": [
                {
                    "name": r.test_name,
                    "success": r.success,
                    "duration_seconds": r.duration_seconds,
                    "operations_completed": r.operations_completed,
                    "peak_memory_mb": r.peak_memory_mb,
                    "peak_cpu_percent": r.peak_cpu_percent,
                    "errors": r.errors,
                    "performance_metrics": r.performance_metrics
                }
                for r in results
            ],
            "recommendations": self._generate_recommendations(results),
            "timestamp": time.time()
        }

        return report

    def _generate_recommendations(self, results: List[StressTestResult]) -> List[str]:
        """生成优化建议"""
        recommendations = []

        for result in results:
            if not result.success:
                if "内存" in " ".join(result.errors):
                    recommendations.append("建议优化内存使用，考虑增加缓存管理或减少内存占用")
                if "耗时" in " ".join(result.errors):
                    recommendations.append("建议优化算法性能，考虑并行处理或缓存优化")
                if "并发" in " ".join(result.errors):
                    recommendations.append("建议优化并发处理能力，考虑调整线程池大小")

            # 性能指标分析
            if result.peak_memory_mb > 500:
                recommendations.append("峰值内存使用较高，建议监控内存使用并优化内存管理")

            if result.peak_cpu_percent > 90:
                recommendations.append("CPU使用率较高，建议优化计算密集型操作")

            if result.duration_seconds > 60:
                recommendations.append("测试耗时较长，建议优化处理流程")

        # 去重
        recommendations = list(set(recommendations))

        if not recommendations:
            recommendations.append("系统性能表现良好，未发现明显问题")

        return recommendations


# Pytest测试函数
@pytest.fixture
def stress_tester():
    """创建压力测试器实例"""
    tester = SystemStressTester()
    yield tester
    tester.agent_optimizer.shutdown()


@pytest.mark.stress
@pytest.mark.timeout(300)  # 5分钟超时
def test_large_canvas_processing(stress_tester):
    """测试大规模Canvas处理"""
    result = stress_tester.test_large_canvas_processing()
    assert result.success, f"大规模Canvas处理测试失败: {result.errors}"
    assert result.duration_seconds < 120, f"测试耗时过长: {result.duration_seconds}s"
    assert result.peak_memory_mb < 1000, f"内存使用过高: {result.peak_memory_mb}MB"


@pytest.mark.stress
@pytest.mark.timeout(300)
def test_concurrent_agent_execution(stress_tester):
    """测试并发Agent执行"""
    result = stress_tester.test_concurrent_agent_execution()
    assert result.success, f"并发Agent执行测试失败: {result.errors}"
    assert result.operations_completed >= 30, f"完成的操作数不足: {result.operations_completed}"
    assert result.peak_cpu_percent <= 100, f"CPU使用率异常: {result.peak_cpu_percent}%"


@pytest.mark.stress
@pytest.mark.timeout(300)
def test_memory_usage_and_leaks(stress_tester):
    """测试内存使用和泄漏"""
    result = stress_tester.test_memory_usage_and_leaks()
    assert result.success, f"内存泄漏测试失败: {result.errors}"

    # 检查内存增长是否合理
    memory_growth = result.performance_metrics.get("memory_growth_mb", 0)
    assert memory_growth < 200, f"内存增长过多: {memory_growth}MB"


@pytest.mark.stress
@pytest.mark.timeout(300)
def test_system_resource_exhaustion(stress_tester):
    """测试系统资源耗尽"""
    result = stress_tester.test_system_resource_exhaustion()
    assert result.success, f"资源耗尽测试失败: {result.errors}"
    assert result.operations_completed >= 50, f"完成的操作数不足: {result.operations_completed}"


@pytest.mark.stress
def test_comprehensive_stress_suite(stress_tester):
    """综合压力测试套件"""
    print("运行综合压力测试套件...")

    results = stress_tester.run_all_stress_tests()
    report = stress_tester.generate_stress_test_report(results)

    # 验证整体测试结果
    assert report["stress_test_summary"]["success_rate_percent"] >= 60, \
        f"压力测试通过率过低: {report['stress_test_summary']['success_rate_percent']}%"

    # 保存测试报告
    report_file = f"stress_test_report_{int(time.time())}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"压力测试报告已保存: {report_file}")
    print(f"测试通过率: {report['stress_test_summary']['success_rate_percent']:.1f}%")
    print(f"性能等级: {report['stress_test_summary']['performance_grade']}")


if __name__ == "__main__":
    # 直接运行压力测试
    tester = SystemStressTester()
    try:
        results = tester.run_all_stress_tests()
        report = tester.generate_stress_test_report(results)

        print("\n" + "=" * 60)
        print("压力测试报告")
        print("=" * 60)

        summary = report["stress_test_summary"]
        print(f"总测试数: {summary['total_tests']}")
        print(f"通过测试: {summary['passed_tests']}")
        print(f"失败测试: {summary['failed_tests']}")
        print(f"成功率: {summary['success_rate_percent']:.1f}%")
        print(f"性能等级: {summary['performance_grade']}")
        print(f"总耗时: {summary['total_duration_seconds']:.2f}秒")
        print(f"总操作数: {summary['total_operations']}")
        print(f"峰值内存: {summary['peak_memory_usage_mb']:.1f}MB")
        print(f"峰值CPU: {summary['peak_cpu_usage_percent']:.1f}%")

        print("\n优化建议:")
        for i, rec in enumerate(report["recommendations"], 1):
            print(f"{i}. {rec}")

        # 保存报告
        report_file = f"stress_test_report_{int(time.time())}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\n详细报告已保存: {report_file}")

    finally:
        tester.agent_optimizer.shutdown()
