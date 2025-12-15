"""
性能基准测试系统 - Canvas学习系统

本模块实现全面的性能基准测试功能，包括：
- 并行vs串行性能对比
- 多场景基准测试
- 性能趋势分析
- 3-4倍效率验证

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-27
Story: 10.6 - Task 5
"""

import asyncio
import time
import json
import statistics
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import uuid
import psutil
import threading

# 导入性能组件
from performance_monitor import PerformanceMonitor
from intelligent_cache_manager import IntelligentCacheManager
from dynamic_instance_manager import DynamicInstanceManager
from configuration_manager import ConfigurationManager

# 尝试导入并行处理组件
try:
    from enhanced_agent_instance_pool import EnhancedGLMInstancePool
    ENHANCED_POOL_AVAILABLE = True
except ImportError:
    ENHANCED_POOL_AVAILABLE = False

# 模拟Agent类
class MockAgent:
    """模拟Agent用于基准测试"""

    def __init__(self, agent_type: str, processing_time: float = 0.1):
        self.agent_type = agent_type
        self.processing_time = processing_time

    async def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """模拟处理任务"""
        await asyncio.sleep(self.processing_time)

        return {
            "success": True,
            "task_id": task_data.get("task_id"),
            "agent_type": self.agent_type,
            "result": f"Processed {task_data.get('concept', 'default')}",
            "processing_time": self.processing_time,
            "timestamp": datetime.now().isoformat()
        }


# 基准测试数据模型


class BenchmarkType(Enum):
    """基准测试类型"""
    SERIAL = "serial"
    PARALLEL = "parallel"
    CACHED = "cached"
    OPTIMIZED = "optimized"


class TestComplexity(Enum):
    """测试复杂度"""
    SIMPLE = "simple"         # 简单任务
    MEDIUM = "medium"         # 中等复杂度
    COMPLEX = "complex"       # 复杂任务
    MIXED = "mixed"           # 混合复杂度


@dataclass
class BenchmarkScenario:
    """基准测试场景"""
    scenario_id: str
    name: str
    description: str
    task_count: int
    agent_types: List[str]
    complexity: TestComplexity
    expected_time_serial: float
    expected_time_parallel: float
    target_efficiency: float  # 目标效率提升倍数
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BenchmarkResult:
    """基准测试结果"""
    benchmark_id: str
    scenario_id: str
    test_type: BenchmarkType
    task_count: int
    successful_tasks: int
    failed_tasks: int
    total_time: float
    average_task_time: float
    throughput: float  # tasks/second
    memory_peak_mb: float
    cpu_peak_percent: float
    efficiency_ratio: float  # 相对于串行的效率比
    test_date: datetime = field(default_factory=datetime.now)
    system_info: Dict[str, str] = field(default_factory=dict)
    notes: str = ""

    @property
    def success_rate(self) -> float:
        """成功率"""
        return self.successful_tasks / self.task_count if self.task_count > 0 else 0

    @property
    def meets_target(self) -> bool:
        """是否达到效率目标"""
        return 3.0 <= self.efficiency_ratio <= 4.0


@dataclass
class BenchmarkReport:
    """基准测试报告"""
    report_id: str
    test_date: datetime
    scenarios: List[BenchmarkResult]
    summary: Dict[str, Any]
    trend_analysis: Dict[str, Any]
    recommendations: List[str]
    system_info: Dict[str, str]


class PerformanceBenchmarkSystem:
    """性能基准测试系统

    提供全面的并行处理性能基准测试，验证3-4倍效率提升目标。
    """

    def __init__(self,
                 performance_monitor: PerformanceMonitor,
                 cache_manager: IntelligentCacheManager,
                 config_manager: ConfigurationManager):
        """初始化基准测试系统

        Args:
            performance_monitor: 性能监控器
            cache_manager: 缓存管理器
            config_manager: 配置管理器
        """
        self.performance_monitor = performance_monitor
        self.cache_manager = cache_manager
        self.config_manager = config_manager

        # 测试结果存储
        self.benchmark_results: List[BenchmarkResult] = []
        self.test_scenarios: List[BenchmarkScenario] = []

        # 系统信息
        self.system_info = self._collect_system_info()

        # 监控状态
        self.monitoring_active = False
        self.monitor_task: Optional[asyncio.Task] = None

        # Agent池
        self.agent_pools: Dict[str, List[MockAgent]] = {}

        # 初始化测试场景
        self._initialize_test_scenarios()

        print("PerformanceBenchmarkSystem initialized")

    def _collect_system_info(self) -> Dict[str, str]:
        """收集系统信息"""
        return {
            "platform": psutil.platform.platform(),
            "cpu_count": str(psutil.cpu_count()),
            "memory_total_gb": f"{psutil.virtual_memory().total / 1024 / 1024 / 1024:.1f}",
            "python_version": psutil.platform.python_version(),
            "timestamp": datetime.now().isoformat()
        }

    def _initialize_test_scenarios(self) -> None:
        """初始化测试场景"""
        scenarios = [
            # 基础性能测试
            BenchmarkScenario(
                scenario_id="basic_small",
                name="小规模基础测试",
                description="4个简单任务，验证基础并行效率",
                task_count=4,
                agent_types=["basic-decomposition"],
                complexity=TestComplexity.SIMPLE,
                expected_time_serial=0.4,
                expected_time_parallel=0.15,
                target_efficiency=2.5
            ),
            BenchmarkScenario(
                scenario_id="basic_medium",
                name="中等规模基础测试",
                description="8个中等任务，验证并行处理能力",
                task_count=8,
                agent_types=["basic-decomposition", "scoring-agent"],
                complexity=TestComplexity.MEDIUM,
                expected_time_serial=1.6,
                expected_time_parallel=0.5,
                target_efficiency=3.2
            ),
            BenchmarkScenario(
                scenario_id="basic_large",
                name="大规模基础测试",
                description="16个复杂任务，验证极限并行效率",
                task_count=16,
                agent_types=["oral-explanation", "clarification-path"],
                complexity=TestComplexity.COMPLEX,
                expected_time_serial=3.2,
                expected_time_parallel=0.9,
                target_efficiency=3.5
            ),

            # 混合Agent测试
            BenchmarkScenario(
                scenario_id="mixed_agents",
                name="混合Agent测试",
                description="多种Agent类型混合处理",
                task_count=12,
                agent_types=[
                    "basic-decomposition", "deep-decomposition",
                    "oral-explanation", "scoring-agent"
                ],
                complexity=TestComplexity.MIXED,
                expected_time_serial=2.4,
                expected_time_parallel=0.7,
                target_efficiency=3.4
            ),

            # 缓存效果测试
            BenchmarkScenario(
                scenario_id="cache_effect",
                name="缓存效果测试",
                description="测试缓存对性能的影响",
                task_count=10,
                agent_types=["oral-explanation"],
                complexity=TestComplexity.MEDIUM,
                expected_time_serial=2.0,
                expected_time_parallel=0.6,
                target_efficiency=3.3,
                parameters={"enable_cache": True}
            ),

            # 性能压力测试
            BenchmarkScenario(
                scenario_id="stress_test",
                name="性能压力测试",
                description="高并发压力测试",
                task_count=20,
                agent_types=["example-teaching"],
                complexity=TestComplexity.COMPLEX,
                expected_time_serial=4.0,
                expected_time_parallel=1.2,
                target_efficiency=3.3
            )
        ]

        self.test_scenarios = scenarios

    async def run_benchmark(self, scenario_id: str, test_type: BenchmarkType = BenchmarkType.PARALLEL) -> BenchmarkResult:
        """运行单个基准测试

        Args:
            scenario_id: 场景ID
            test_type: 测试类型

        Returns:
            BenchmarkResult: 测试结果
        """
        scenario = next((s for s in self.test_scenarios if s.scenario_id == scenario_id), None)
        if not scenario:
            raise ValueError(f"Unknown scenario: {scenario_id}")

        benchmark_id = f"bench-{uuid.uuid4().hex[:8]}"
        print(f"\n--- Running Benchmark: {scenario.name} ({test_type.value}) ---")

        # 创建测试任务
        tasks = self._create_test_tasks(scenario)

        # 资源监控
        memory_tracker = ResourceTracker()
        cpu_tracker = ResourceTracker()

        memory_tracker.start()
        cpu_tracker.start()

        try:
            start_time = time.time()

            if test_type == BenchmarkType.SERIAL:
                results = await self._run_serial_test(tasks, scenario)
            elif test_type == BenchmarkType.PARALLEL:
                results = await self._run_parallel_test(tasks, scenario)
            elif test_type == BenchmarkType.CACHED:
                results = await self._run_cached_test(tasks, scenario)
            elif test_type == BenchmarkType.OPTIMIZED:
                results = await self._run_optimized_test(tasks, scenario)
            else:
                raise ValueError(f"Unknown test type: {test_type}")

            total_time = time.time() - start_time

            # 统计结果
            successful_tasks = sum(1 for r in results if r.get("success", False))
            failed_tasks = len(results) - successful_tasks
            average_task_time = total_time / len(tasks) if tasks else 0
            throughput = successful_tasks / total_time if total_time > 0 else 0

            # 获取资源使用
            memory_peak = memory_tracker.get_peak()
            cpu_peak = cpu_tracker.get_peak()

            # 计算效率比
            efficiency_ratio = self._calculate_efficiency_ratio(
                scenario, test_type, total_time
            )

            # 创建结果
            result = BenchmarkResult(
                benchmark_id=benchmark_id,
                scenario_id=scenario_id,
                test_type=test_type,
                task_count=len(tasks),
                successful_tasks=successful_tasks,
                failed_tasks=failed_tasks,
                total_time=total_time,
                average_task_time=average_task_time,
                throughput=throughput,
                memory_peak_mb=memory_peak,
                cpu_peak_percent=cpu_peak,
                efficiency_ratio=efficiency_ratio,
                system_info=self.system_info
            )

            self.benchmark_results.append(result)

            # 输出结果
            print(f"  Total time: {total_time:.3f}s")
            print(f"  Success rate: {successful_tasks}/{len(tasks)} ({result.success_rate:.1%})")
            print(f"  Throughput: {throughput:.2f} tasks/sec")
            print(f"  Efficiency ratio: {efficiency_ratio:.2f}x")
            print(f"  Target met: {'✓' if result.meets_target else '✗'}")

            return result

        finally:
            memory_tracker.stop()
            cpu_tracker.stop()

    async def run_comprehensive_benchmark(self) -> BenchmarkReport:
        """运行全面的基准测试

        Returns:
            BenchmarkReport: 综合测试报告
        """
        print("\n" + "=" * 60)
        print("Starting Comprehensive Performance Benchmark")
        print("=" * 60)

        report_id = f"report-{uuid.uuid4().hex[:8]}"
        all_results = []

        # 运行所有场景
        for scenario in self.test_scenarios:
            # 串行测试（作为基准）
            serial_result = await self.run_benchmark(scenario.scenario_id, BenchmarkType.SERIAL)
            all_results.append(serial_result)

            # 等待一段时间让系统稳定
            await asyncio.sleep(1)

            # 并行测试
            parallel_result = await self.run_benchmark(scenario.scenario_id, BenchmarkType.PARALLEL)
            all_results.append(parallel_result)

            # 如果场景支持缓存，运行缓存测试
            if scenario.parameters.get("enable_cache", False):
                await asyncio.sleep(1)
                cached_result = await self.run_benchmark(scenario.scenario_id, BenchmarkType.CACHED)
                all_results.append(cached_result)

        # 生成报告
        report = await self._generate_benchmark_report(report_id, all_results)

        # 保存报告
        await self._save_benchmark_report(report)

        return report

    def _create_test_tasks(self, scenario: BenchmarkScenario) -> List[Dict[str, Any]]:
        """创建测试任务"""
        tasks = []
        for i in range(scenario.task_count):
            # 选择Agent类型
            agent_type = scenario.agent_types[i % len(scenario.agent_types)]

            # 根据复杂度调整处理时间
            if scenario.complexity == TestComplexity.SIMPLE:
                processing_time = 0.1
            elif scenario.complexity == TestComplexity.MEDIUM:
                processing_time = 0.2
            elif scenario.complexity == TestComplexity.COMPLEX:
                processing_time = 0.3
            else:  # MIXED
                processing_time = 0.1 + (i % 3) * 0.1

            task = {
                "task_id": f"task-{scenario.scenario_id}-{i}",
                "agent_type": agent_type,
                "concept": f"Test concept {i}",
                "processing_time": processing_time,
                "complexity": scenario.complexity.value
            }
            tasks.append(task)

        return tasks

    async def _run_serial_test(self, tasks: List[Dict], scenario: BenchmarkScenario) -> List[Dict]:
        """运行串行测试"""
        print(f"  Running serial test with {len(tasks)} tasks...")
        results = []

        for task in tasks:
            # 创建Agent实例
            agent = MockAgent(task["agent_type"], task["processing_time"])
            result = await agent.process_task(task)
            results.append(result)

        return results

    async def _run_parallel_test(self, tasks: List[Dict], scenario: BenchmarkScenario) -> List[Dict]:
        """运行并行测试"""
        max_concurrent = min(6, len(tasks))  # 最多6个并发
        print(f"  Running parallel test with {len(tasks)} tasks (max concurrent: {max_concurrent})...")

        # 创建信号量
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_with_semaphore(task):
            async with semaphore:
                agent = MockAgent(task["agent_type"], task["processing_time"])
                return await agent.process_task(task)

        # 并行执行
        results = await asyncio.gather(*[process_with_semaphore(task) for task in tasks])
        return results

    async def _run_cached_test(self, tasks: List[Dict], scenario: BenchmarkScenario) -> List[Dict]:
        """运行缓存测试"""
        print(f"  Running cached test with {len(tasks)} tasks...")

        results = []
        cache_hits = 0

        for task in tasks:
            # 检查缓存
            cache_key = f"{task['agent_type']}:{task['concept']}"
            cached_result = await self.cache_manager.get_cached_result(cache_key)

            if cached_result:
                results.append(cached_result)
                cache_hits += 1
            else:
                # 处理任务
                agent = MockAgent(task["agent_type"], task["processing_time"])
                result = await agent.process_task(task)

                # 缓存结果
                await self.cache_manager.cache_result(
                    cache_key, result,
                    self.cache_manager.CacheEntryType.AGENT_RESPONSE,
                    ttl_seconds=300  # 5分钟
                )
                results.append(result)

        print(f"    Cache hits: {cache_hits}/{len(tasks)}")
        return results

    async def _run_optimized_test(self, tasks: List[Dict], scenario: BenchmarkScenario) -> List[Dict]:
        """运行优化测试（使用所有优化策略）"""
        print(f"  Running optimized test with {len(tasks)} tasks...")

        # 使用智能调度
        max_concurrent = min(8, len(tasks))
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_with_optimization(task):
            async with semaphore:
                # 1. 检查缓存
                cache_key = f"{task['agent_type']}:{task['concept']}"
                cached_result = await self.cache_manager.get_cached_result(cache_key)

                if cached_result:
                    return cached_result

                # 2. 处理任务
                agent = MockAgent(task["agent_type"], task["processing_time"])
                result = await agent.process_task(task)

                # 3. 缓存结果
                await self.cache_manager.cache_result(
                    cache_key, result,
                    self.cache_manager.CacheEntryType.AGENT_RESPONSE
                )

                return result

        # 并行执行
        results = await asyncio.gather(*[process_with_optimization(task) for task in tasks])
        return results

    def _calculate_efficiency_ratio(self, scenario: BenchmarkScenario, test_type: BenchmarkType, actual_time: float) -> float:
        """计算效率比"""
        if test_type == BenchmarkType.SERIAL:
            return 1.0

        # 获取对应的串行时间
        serial_result = next(
            (r for r in self.benchmark_results
             if r.scenario_id == scenario.scenario_id and r.test_type == BenchmarkType.SERIAL),
            None
        )

        if serial_result:
            return serial_result.total_time / actual_time
        else:
            # 使用预期时间
            return scenario.expected_time_serial / actual_time

    async def _generate_benchmark_report(self, report_id: str, results: List[BenchmarkResult]) -> BenchmarkReport:
        """生成基准测试报告"""
        print("\n" + "-" * 60)
        print("Generating Benchmark Report...")
        print("-" * 60)

        # 按场景分组结果
        scenario_results = {}
        for result in results:
            if result.scenario_id not in scenario_results:
                scenario_results[result.scenario_id] = []
            scenario_results[result.scenario_id].append(result)

        # 计算摘要
        summary = {
            "total_tests": len(results),
            "total_scenarios": len(scenario_results),
            "average_efficiency": 0,
            "target_met_count": 0,
            "average_throughput": 0,
            "average_success_rate": 0
        }

        efficiency_ratios = []
        throughputs = []
        success_rates = []

        for scenario_results_list in scenario_results.values():
            parallel_result = next(
                (r for r in scenario_results_list if r.test_type == BenchmarkType.PARALLEL),
                None
            )

            if parallel_result:
                efficiency_ratios.append(parallel_result.efficiency_ratio)
                throughputs.append(parallel_result.throughput)
                success_rates.append(parallel_result.success_rate)

                if parallel_result.meets_target:
                    summary["target_met_count"] += 1

        if efficiency_ratios:
            summary["average_efficiency"] = statistics.mean(efficiency_ratios)
            summary["max_efficiency"] = max(efficiency_ratios)
            summary["min_efficiency"] = min(efficiency_ratios)

        if throughputs:
            summary["average_throughput"] = statistics.mean(throughputs)

        if success_rates:
            summary["average_success_rate"] = statistics.mean(success_rates)

        summary["success_rate"] = summary["target_met_count"] / len(scenario_results)

        # 趋势分析
        trend_analysis = self._analyze_performance_trends(results)

        # 生成建议
        recommendations = self._generate_benchmark_recommendations(summary, trend_analysis)

        report = BenchmarkReport(
            report_id=report_id,
            test_date=datetime.now(),
            scenarios=results,
            summary=summary,
            trend_analysis=trend_analysis,
            recommendations=recommendations,
            system_info=self.system_info
        )

        # 输出摘要
        print(f"\nBenchmark Summary:")
        print(f"  Total scenarios tested: {summary['total_scenarios']}")
        print(f"  Average efficiency: {summary['average_efficiency']:.2f}x")
        print(f"  Efficiency range: {summary.get('min_efficiency', 0):.2f}x - {summary.get('max_efficiency', 0):.2f}x")
        print(f"  Scenarios meeting target: {summary['target_met_count']}/{summary['total_scenarios']}")
        print(f"  Average throughput: {summary['average_throughput']:.2f} tasks/sec")
        print(f"  Overall success rate: {summary['success_rate']:.1%}")

        return report

    def _analyze_performance_trends(self, results: List[BenchmarkResult]) -> Dict[str, Any]:
        """分析性能趋势"""
        # 按时间排序
        sorted_results = sorted(results, key=lambda r: r.test_date)

        # 效率趋势
        parallel_results = [r for r in sorted_results if r.test_type == BenchmarkType.PARALLEL]
        if len(parallel_results) > 1:
            efficiency_trend = "stable"
            if parallel_results[-1].efficiency_ratio > parallel_results[0].efficiency_ratio * 1.1:
                efficiency_trend = "improving"
            elif parallel_results[-1].efficiency_ratio < parallel_results[0].efficiency_ratio * 0.9:
                efficiency_trend = "degrading"
        else:
            efficiency_trend = "insufficient_data"

        return {
            "efficiency_trend": efficiency_trend,
            "test_count": len(sorted_results),
            "date_range": {
                "first": sorted_results[0].test_date.isoformat() if sorted_results else None,
                "last": sorted_results[-1].test_date.isoformat() if sorted_results else None
            }
        }

    def _generate_benchmark_recommendations(self, summary: Dict, trend_analysis: Dict) -> List[str]:
        """生成基准测试建议"""
        recommendations = []

        # 效率建议
        if summary["average_efficiency"] < 3.0:
            recommendations.append(
                "平均效率提升低于3倍目标，建议优化并行调度算法或增加并发数"
            )
        elif summary["average_efficiency"] > 4.0:
            recommendations.append(
                "效率提升超过4倍，建议验证测试数据的准确性"
            )

        # 成功率建议
        if summary["success_rate"] < 0.8:
            recommendations.append(
                "目标达成率较低，建议检查系统资源配置或优化测试场景"
            )

        # 吞吐量建议
        if summary["average_throughput"] < 1.0:
            recommendations.append(
                "吞吐量较低，建议优化Agent处理速度或减少任务复杂度"
            )

        # 趋势建议
        if trend_analysis["efficiency_trend"] == "degrading":
            recommendations.append(
                "性能呈下降趋势，建议检查系统资源使用或进行性能优化"
            )
        elif trend_analysis["efficiency_trend"] == "improving":
            recommendations.append(
                "性能持续改善，当前优化策略有效"
            )

        return recommendations

    async def _save_benchmark_report(self, report: BenchmarkReport) -> None:
        """保存基准测试报告"""
        # 创建报告目录
        report_dir = Path("reports/benchmarks")
        report_dir.mkdir(parents=True, exist_ok=True)

        # 生成文件名
        timestamp = report.test_date.strftime("%Y%m%d_%H%M%S")
        report_file = report_dir / f"benchmark_report_{timestamp}.json"

        # 准备报告数据
        report_data = {
            "report_id": report.report_id,
            "test_date": report.test_date.isoformat(),
            "summary": report.summary,
            "trend_analysis": report.trend_analysis,
            "recommendations": report.recommendations,
            "system_info": report.system_info,
            "scenarios": [
                {
                    "benchmark_id": r.benchmark_id,
                    "scenario_id": r.scenario_id,
                    "test_type": r.test_type.value,
                    "task_count": r.task_count,
                    "successful_tasks": r.successful_tasks,
                    "failed_tasks": r.failed_tasks,
                    "total_time": r.total_time,
                    "average_task_time": r.average_task_time,
                    "throughput": r.throughput,
                    "memory_peak_mb": r.memory_peak_mb,
                    "cpu_peak_percent": r.cpu_peak_percent,
                    "efficiency_ratio": r.efficiency_ratio,
                    "success_rate": r.success_rate,
                    "meets_target": r.meets_target,
                    "notes": r.notes
                }
                for r in report.scenarios
            ]
        }

        # 保存报告
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)

            print(f"\nBenchmark report saved to: {report_file}")
        except Exception as e:
            print(f"Failed to save benchmark report: {e}")

    async def get_benchmark_history(self, days: int = 30) -> List[BenchmarkResult]:
        """获取基准测试历史

        Args:
            days: 最近多少天的数据

        Returns:
            List[BenchmarkResult]: 历史结果列表
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        return [
            r for r in self.benchmark_results
            if r.test_date >= cutoff_date
        ]

    async def export_benchmark_data(self, file_path: str) -> bool:
        """导出基准测试数据

        Args:
            file_path: 导出文件路径

        Returns:
            bool: 是否成功
        """
        try:
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "system_info": self.system_info,
                "scenarios": [s.__dict__ for s in self.test_scenarios],
                "results": [r.__dict__ for r in self.benchmark_results]
            }

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

            return True
        except Exception as e:
            print(f"Failed to export benchmark data: {e}")
            return False


class ResourceTracker:
    """资源使用跟踪器"""

    def __init__(self):
        self.monitoring = False
        self.peak_value = 0
        self.values = []
        self._task = None
        self._stop_event = asyncio.Event()

    def start(self):
        """开始监控"""
        self.monitoring = True
        self.peak_value = 0
        self.values.clear()
        self._stop_event.clear()

    def stop(self):
        """停止监控"""
        self.monitoring = False
        self._stop_event.set()

    def get_peak(self):
        """获取峰值"""
        return self.peak_value


class MemoryTracker(ResourceTracker):
    """内存使用跟踪器"""

    def __init__(self):
        super().__init__()
        self.process = psutil.Process()

    async def track_memory(self):
        """跟踪内存使用"""
        while self.monitoring and not self._stop_event.is_set():
            memory_mb = self.process.memory_info().rss / 1024 / 1024
            self.values.append(memory_mb)
            self.peak_value = max(self.peak_value, memory_mb)
            await asyncio.sleep(0.1)

    def start(self):
        """开始跟踪"""
        super().start()
        self._task = asyncio.create_task(self.track_memory())

    def stop(self):
        """停止跟踪"""
        super().stop()
        if self._task:
            self._task.cancel()


class CPUTracker(ResourceTracker):
    """CPU使用跟踪器"""

    def __init__(self):
        super().__init__()

    async def track_cpu(self):
        """跟踪CPU使用"""
        while self.monitoring and not self._stop_event.is_set():
            cpu_percent = psutil.cpu_percent(interval=0.1)
            self.values.append(cpu_percent)
            self.peak_value = max(self.peak_value, cpu_percent)

    def start(self):
        """开始跟踪"""
        super().start()
        self._task = asyncio.create_task(self.track_cpu())

    def stop(self):
        """停止跟踪"""
        super().stop()
        if self._task:
            self._task.cancel()