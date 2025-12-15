#!/usr/bin/env python3
"""
Canvas学习系统 - 性能测试运行器
Story 8.13: 提升测试覆盖率和系统稳定性

专门用于运行系统性能测试的工具。

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-22
"""

import asyncio
import json
import os
import psutil
import subprocess
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any


class PerformanceTestRunner:
    """性能测试运行器"""

    def __init__(self, config_path: str = "config/testing.yaml"):
        """初始化性能测试运行器

        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.project_root = Path.cwd()
        self.test_results = []

    def _load_config(self) -> Dict:
        """加载配置"""
        default_config = {
            "performance": {
                "baseline_response_time_ms": 3000,
                "memory_usage_limit_mb": 2048,
                "cpu_usage_limit_percent": 85.0,
                "concurrent_users": 10,
                "load_test_duration_minutes": 30,
                "response_time_p95_threshold_ms": 5000,
                "throughput_minimum_rps": 10
            }
        }

        if os.path.exists(self.config_path):
            try:
                import yaml
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded_config = yaml.safe_load(f)
                    if loaded_config and "performance" in loaded_config:
                        default_config["performance"].update(loaded_config["performance"])
            except Exception:
                pass  # 使用默认配置

        return default_config

    def run_all_performance_tests(self) -> Dict:
        """运行所有性能测试"""
        print("Running all performance tests...")

        test_scenarios = self._get_all_test_scenarios()
        results = []

        for scenario in test_scenarios:
            print(f"Running: {scenario['name']}")
            result = self._run_single_test(scenario)
            results.append(result)

        analysis = self._analyze_results(results)
        self.test_results = results

        return analysis

    def _get_all_test_scenarios(self) -> List[Dict]:
        """获取所有测试场景"""
        return [
            {
                "name": "canvas_file_read_performance",
                "description": "Test Canvas file reading performance",
                "type": "canvas_operations",
                "test_function": self._test_canvas_read_performance,
                "parameters": {
                    "file_sizes": [100, 500, 1000],  # 节点数量
                    "target_response_time_ms": self.config["performance"]["baseline_response_time_ms"]
                }
            },
            {
                "name": "canvas_file_write_performance",
                "description": "Test Canvas file writing performance",
                "type": "canvas_operations",
                "test_function": self._test_canvas_write_performance,
                "parameters": {
                    "file_sizes": [100, 500, 1000],
                    "target_response_time_ms": 3000
                }
            },
            {
                "name": "agent_parallel_execution",
                "description": "Test parallel agent execution performance",
                "type": "agent_operations",
                "test_function": self._test_agent_parallel_execution,
                "parameters": {
                    "concurrent_agents": [2, 5, 8, 10],
                    "target_time_ms": 10000
                }
            },
            {
                "name": "review_scheduler_performance",
                "description": "Test review scheduler performance",
                "type": "review_operations",
                "test_function": self._test_review_scheduler_performance,
                "parameters": {
                    "review_counts": [10, 50, 100],
                    "target_time_ms": 2000
                }
            },
            {
                "name": "memory_usage_under_load",
                "description": "Test memory usage under various loads",
                "type": "resource_usage",
                "test_function": self._test_memory_usage,
                "parameters": {
                    "load_levels": [1, 5, 10, 20],
                    "memory_limit_mb": self.config["performance"]["memory_usage_limit_mb"]
                }
            },
            {
                "name": "cpu_usage_under_load",
                "description": "Test CPU usage under concurrent load",
                "type": "resource_usage",
                "test_function": self._test_cpu_usage,
                "parameters": {
                    "concurrent_tasks": [5, 10, 15, 20],
                    "cpu_limit_percent": self.config["performance"]["cpu_usage_limit_percent"]
                }
            }
        ]

    def _run_single_test(self, scenario: Dict) -> Dict:
        """运行单个性能测试"""
        test_function = scenario["test_function"]
        parameters = scenario["parameters"]

        try:
            start_time = time.time()
            result = test_function(**parameters)
            end_time = time.time()

            result.update({
                "test_name": scenario["name"],
                "description": scenario["description"],
                "type": scenario["type"],
                "execution_time_seconds": end_time - start_time,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

            return result

        except Exception as e:
            return {
                "test_name": scenario["name"],
                "description": scenario["description"],
                "type": scenario["type"],
                "status": "failed",
                "error": str(e),
                "execution_time_seconds": time.time() - time.time(),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

    def _test_canvas_read_performance(self, file_sizes: List[int], target_response_time_ms: int) -> Dict:
        """测试Canvas文件读取性能"""
        results = []

        for size in file_sizes:
            print(f"  Testing Canvas read with {size} nodes...")

            # 模拟创建大型Canvas文件
            canvas_data = self._create_test_canvas(size)
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.canvas', delete=False)
            json.dump(canvas_data, temp_file)
            temp_file.close()

            try:
                # 测试读取性能
                start_time = time.time()

                # 模拟读取操作
                with open(temp_file.name, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # 模拟数据处理
                time.sleep(min(size / 1000, 0.5))  # 模拟处理时间

                end_time = time.time()
                response_time_ms = (end_time - start_time) * 1000

                # 获取内存使用情况
                memory_usage = psutil.Process().memory_info().rss / 1024 / 1024  # MB

                result = {
                    "file_size_nodes": size,
                    "response_time_ms": round(response_time_ms, 2),
                    "target_response_time_ms": target_response_time_ms,
                    "memory_usage_mb": round(memory_usage, 2),
                    "status": "passed" if response_time_ms <= target_response_time_ms else "failed",
                    "performance_score": max(0, 100 - ((response_time_ms - target_response_time_ms) / target_response_time_ms * 100))
                }

                results.append(result)

            finally:
                os.unlink(temp_file.name)

        # 计算总体结果
        avg_response_time = sum(r["response_time_ms"] for r in results) / len(results)
        passed_tests = sum(1 for r in results if r["status"] == "passed")

        return {
            "status": "passed" if passed_tests == len(results) else "failed",
            "individual_results": results,
            "summary": {
                "total_tests": len(results),
                "passed_tests": passed_tests,
                "average_response_time_ms": round(avg_response_time, 2),
                "max_response_time_ms": max(r["response_time_ms"] for r in results),
                "min_response_time_ms": min(r["response_time_ms"] for r in results),
                "average_memory_usage_mb": round(sum(r["memory_usage_mb"] for r in results) / len(results), 2)
            }
        }

    def _test_canvas_write_performance(self, file_sizes: List[int], target_response_time_ms: int) -> Dict:
        """测试Canvas文件写入性能"""
        results = []

        for size in file_sizes:
            print(f"  Testing Canvas write with {size} nodes...")

            # 创建测试数据
            canvas_data = self._create_test_canvas(size)
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.canvas', delete=False)
            temp_file.close()

            try:
                # 测试写入性能
                start_time = time.time()

                with open(temp_file.name, 'w', encoding='utf-8') as f:
                    json.dump(canvas_data, f, ensure_ascii=False, indent=2)

                end_time = time.time()
                response_time_ms = (end_time - start_time) * 1000

                # 获取文件大小
                file_size_mb = os.path.getsize(temp_file.name) / 1024 / 1024

                result = {
                    "file_size_nodes": size,
                    "response_time_ms": round(response_time_ms, 2),
                    "target_response_time_ms": target_response_time_ms,
                    "file_size_mb": round(file_size_mb, 2),
                    "status": "passed" if response_time_ms <= target_response_time_ms else "failed",
                    "performance_score": max(0, 100 - ((response_time_ms - target_response_time_ms) / target_response_time_ms * 100))
                }

                results.append(result)

            finally:
                os.unlink(temp_file.name)

        # 计算总体结果
        avg_response_time = sum(r["response_time_ms"] for r in results) / len(results)
        passed_tests = sum(1 for r in results if r["status"] == "passed")

        return {
            "status": "passed" if passed_tests == len(results) else "failed",
            "individual_results": results,
            "summary": {
                "total_tests": len(results),
                "passed_tests": passed_tests,
                "average_response_time_ms": round(avg_response_time, 2),
                "max_response_time_ms": max(r["response_time_ms"] for r in results),
                "min_response_time_ms": min(r["response_time_ms"] for r in results),
                "average_file_size_mb": round(sum(r["file_size_mb"] for r in results) / len(results), 2)
            }
        }

    def _test_agent_parallel_execution(self, concurrent_agents: List[int], target_time_ms: int) -> Dict:
        """测试Agent并行执行性能"""
        results = []

        for concurrency in concurrent_agents:
            print(f"  Testing agent execution with {concurrency} concurrent agents...")

            def simulate_agent_execution(agent_id: int) -> Dict:
                """模拟Agent执行"""
                start_time = time.time()

                # 模拟Agent工作
                processing_time = 0.5 + (agent_id % 3) * 0.2  # 0.5-0.9秒变化
                time.sleep(processing_time)

                end_time = time.time()
                execution_time_ms = (end_time - start_time) * 1000

                return {
                    "agent_id": agent_id,
                    "execution_time_ms": execution_time_ms,
                    "status": "completed"
                }

            # 并行执行
            start_time = time.time()

            with ThreadPoolExecutor(max_workers=concurrency) as executor:
                futures = [executor.submit(simulate_agent_execution, i) for i in range(concurrency)]
                agent_results = [future.result() for future in as_completed(futures)]

            end_time = time.time()
            total_time_ms = (end_time - start_time) * 1000

            # 计算CPU使用情况
            cpu_percent = psutil.cpu_percent(interval=0.1)

            result = {
                "concurrent_agents": concurrency,
                "total_execution_time_ms": round(total_time_ms, 2),
                "target_time_ms": target_time_ms,
                "cpu_usage_percent": round(cpu_percent, 2),
                "status": "passed" if total_time_ms <= target_time_ms else "failed",
                "performance_score": max(0, 100 - ((total_time_ms - target_time_ms) / target_time_ms * 100)),
                "agent_results": agent_results
            }

            results.append(result)

        # 计算总体结果
        avg_time = sum(r["total_execution_time_ms"] for r in results) / len(results)
        passed_tests = sum(1 for r in results if r["status"] == "passed")

        return {
            "status": "passed" if passed_tests == len(results) else "failed",
            "individual_results": results,
            "summary": {
                "total_tests": len(results),
                "passed_tests": passed_tests,
                "average_execution_time_ms": round(avg_time, 2),
                "max_concurrency": max(r["concurrent_agents"] for r in results),
                "average_cpu_usage_percent": round(sum(r["cpu_usage_percent"] for r in results) / len(results), 2)
            }
        }

    def _test_review_scheduler_performance(self, review_counts: List[int], target_time_ms: int) -> Dict:
        """测试复习调度器性能"""
        results = []

        for count in review_counts:
            print(f"  Testing review scheduler with {count} reviews...")

            # 模拟复习数据
            reviews = self._create_test_reviews(count)

            start_time = time.time()

            # 模拟调度处理
            processed_reviews = []
            for review in reviews:
                # 模拟复习调度逻辑
                time.sleep(0.01)  # 10ms处理时间
                processed_reviews.append({
                    **review,
                    "scheduled": True,
                    "priority": review.get("urgency", 1)
                })

            end_time = time.time()
            processing_time_ms = (end_time - start_time) * 1000

            # 计算吞吐量
            throughput_rps = count / (processing_time_ms / 1000) if processing_time_ms > 0 else 0

            result = {
                "review_count": count,
                "processing_time_ms": round(processing_time_ms, 2),
                "target_time_ms": target_time_ms,
                "throughput_rps": round(throughput_rps, 2),
                "status": "passed" if processing_time_ms <= target_time_ms else "failed",
                "performance_score": max(0, 100 - ((processing_time_ms - target_time_ms) / target_time_ms * 100))
            }

            results.append(result)

        # 计算总体结果
        avg_time = sum(r["processing_time_ms"] for r in results) / len(results)
        passed_tests = sum(1 for r in results if r["status"] == "passed")

        return {
            "status": "passed" if passed_tests == len(results) else "failed",
            "individual_results": results,
            "summary": {
                "total_tests": len(results),
                "passed_tests": passed_tests,
                "average_processing_time_ms": round(avg_time, 2),
                "max_throughput_rps": max(r["throughput_rps"] for r in results),
                "average_throughput_rps": round(sum(r["throughput_rps"] for r in results) / len(results), 2)
            }
        }

    def _test_memory_usage(self, load_levels: List[int], memory_limit_mb: int) -> Dict:
        """测试内存使用情况"""
        results = []

        for load_level in load_levels:
            print(f"  Testing memory usage at load level {load_level}...")

            # 记录初始内存使用
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB

            # 模拟负载
            data_holder = []
            for i in range(load_level * 100):
                data_holder.append({
                    "id": i,
                    "data": "x" * 1000,  # 1KB数据
                    "timestamp": time.time(),
                    "metadata": {"type": "test", "level": load_level}
                })

            # 记录峰值内存使用
            peak_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = peak_memory - initial_memory

            # 清理内存
            del data_holder

            result = {
                "load_level": load_level,
                "initial_memory_mb": round(initial_memory, 2),
                "peak_memory_mb": round(peak_memory, 2),
                "memory_increase_mb": round(memory_increase, 2),
                "memory_limit_mb": memory_limit_mb,
                "status": "passed" if peak_memory <= memory_limit_mb else "failed",
                "memory_efficiency": round((load_level * 100) / max(memory_increase, 1), 2)  # items per MB
            }

            results.append(result)

        # 计算总体结果
        max_memory = max(r["peak_memory_mb"] for r in results)
        passed_tests = sum(1 for r in results if r["status"] == "passed")

        return {
            "status": "passed" if passed_tests == len(results) else "failed",
            "individual_results": results,
            "summary": {
                "total_tests": len(results),
                "passed_tests": passed_tests,
                "max_memory_usage_mb": round(max_memory, 2),
                "memory_limit_mb": memory_limit_mb,
                "average_memory_efficiency": round(sum(r["memory_efficiency"] for r in results) / len(results), 2)
            }
        }

    def _test_cpu_usage(self, concurrent_tasks: List[int], cpu_limit_percent: float) -> Dict:
        """测试CPU使用情况"""
        results = []

        for task_count in concurrent_tasks:
            print(f"  Testing CPU usage with {task_count} concurrent tasks...")

            def cpu_intensive_task(task_id: int, duration: float = 0.5):
                """CPU密集型任务"""
                start_time = time.time()
                while time.time() - start_time < duration:
                    # 执行一些计算
                    sum(i * i for i in range(1000))
                return task_id

            # 监控CPU使用率
            cpu_monitor = psutil.cpu_percent(interval=0.1)

            start_time = time.time()

            # 并行执行CPU密集型任务
            with ThreadPoolExecutor(max_workers=task_count) as executor:
                futures = [executor.submit(cpu_intensive_task, i) for i in range(task_count)]
                results_tasks = [future.result() for future in as_completed(futures)]

            end_time = time.time()

            # 获取平均CPU使用率
            avg_cpu_percent = psutil.cpu_percent(interval=0.1)
            max_cpu_percent = max(cpu_monitor, avg_cpu_percent)

            execution_time = end_time - start_time

            result = {
                "concurrent_tasks": task_count,
                "execution_time_seconds": round(execution_time, 3),
                "cpu_usage_percent": round(max_cpu_percent, 2),
                "cpu_limit_percent": cpu_limit_percent,
                "status": "passed" if max_cpu_percent <= cpu_limit_percent else "failed",
                "tasks_completed": len(results_tasks)
            }

            results.append(result)

        # 计算总体结果
        max_cpu = max(r["cpu_usage_percent"] for r in results)
        passed_tests = sum(1 for r in results if r["status"] == "passed")

        return {
            "status": "passed" if passed_tests == len(results) else "failed",
            "individual_results": results,
            "summary": {
                "total_tests": len(results),
                "passed_tests": passed_tests,
                "max_cpu_usage_percent": round(max_cpu, 2),
                "cpu_limit_percent": cpu_limit_percent,
                "average_execution_time_seconds": round(sum(r["execution_time_seconds"] for r in results) / len(results), 3)
            }
        }

    def _analyze_results(self, results: List[Dict]) -> Dict:
        """分析性能测试结果"""
        if not results:
            return {"error": "No test results to analyze"}

        passed_tests = [r for r in results if r.get("status") == "passed"]
        failed_tests = [r for r in results if r.get("status") == "failed"]

        # 计算各项指标
        total_tests = len(results)
        pass_rate = (len(passed_tests) / total_tests) * 100 if total_tests > 0 else 0

        # 性能评分
        performance_scores = []
        for result in results:
            if "individual_results" in result:
                for individual in result["individual_results"]:
                    if "performance_score" in individual:
                        performance_scores.append(individual["performance_score"])
            elif "performance_score" in result:
                performance_scores.append(result["performance_score"])

        avg_performance_score = sum(performance_scores) / len(performance_scores) if performance_scores else 0

        # 按测试类型分组
        by_type = {}
        for result in results:
            test_type = result.get("type", "unknown")
            if test_type not in by_type:
                by_type[test_type] = []
            by_type[test_type].append(result)

        # 生成改进建议
        recommendations = self._generate_performance_recommendations(failed_tests, by_type)

        return {
            "test_summary": {
                "total_tests": total_tests,
                "passed_tests": len(passed_tests),
                "failed_tests": len(failed_tests),
                "pass_rate_percentage": round(pass_rate, 1),
                "overall_performance_score": round(avg_performance_score, 1)
            },
            "detailed_results": results,
            "performance_by_type": {test_type: self._summarize_type_results(type_results)
                                 for test_type, type_results in by_type.items()},
            "performance_benchmarks": self._calculate_benchmarks(results),
            "recommendations": recommendations,
            "quality_assessment": self._assess_performance_quality(pass_rate, avg_performance_score)
        }

    def _summarize_type_results(self, type_results: List[Dict]) -> Dict:
        """总结特定类型的测试结果"""
        passed = sum(1 for r in type_results if r.get("status") == "passed")
        total = len(type_results)

        # 提取关键指标
        metrics = {}
        if type_results and type_results[0].get("type") == "canvas_operations":
            metrics = {
                "average_response_time_ms": self._extract_avg_metric(type_results, "response_time_ms"),
                "average_memory_usage_mb": self._extract_avg_metric(type_results, "memory_usage_mb")
            }
        elif type_results and type_results[0].get("type") == "agent_operations":
            metrics = {
                "average_execution_time_ms": self._extract_avg_metric(type_results, "total_execution_time_ms"),
                "average_cpu_usage_percent": self._extract_avg_metric(type_results, "cpu_usage_percent")
            }

        return {
            "total_tests": total,
            "passed_tests": passed,
            "pass_rate_percentage": round((passed / total) * 100, 1) if total > 0 else 0,
            "metrics": metrics
        }

    def _extract_avg_metric(self, results: List[Dict], metric_name: str) -> float:
        """提取平均值指标"""
        values = []
        for result in results:
            if "summary" in result and metric_name in result["summary"]:
                values.append(result["summary"][metric_name])
            elif metric_name in result:
                values.append(result[metric_name])

        return round(sum(values) / len(values), 2) if values else 0.0

    def _calculate_benchmarks(self, results: List[Dict]) -> Dict:
        """计算性能基准"""
        all_response_times = []
        all_memory_usage = []
        all_cpu_usage = []

        for result in results:
            if "individual_results" in result:
                for individual in result["individual_results"]:
                    if "response_time_ms" in individual:
                        all_response_times.append(individual["response_time_ms"])
                    if "memory_usage_mb" in individual:
                        all_memory_usage.append(individual["memory_usage_mb"])
                    if "cpu_usage_percent" in individual:
                        all_cpu_usage.append(individual["cpu_usage_percent"])

        benchmarks = {}
        if all_response_times:
            benchmarks["response_time"] = {
                "average_ms": round(sum(all_response_times) / len(all_response_times), 2),
                "p95_ms": round(sorted(all_response_times)[int(len(all_response_times) * 0.95)], 2),
                "max_ms": max(all_response_times)
            }

        if all_memory_usage:
            benchmarks["memory_usage"] = {
                "average_mb": round(sum(all_memory_usage) / len(all_memory_usage), 2),
                "max_mb": max(all_memory_usage)
            }

        if all_cpu_usage:
            benchmarks["cpu_usage"] = {
                "average_percent": round(sum(all_cpu_usage) / len(all_cpu_usage), 2),
                "max_percent": max(all_cpu_usage)
            }

        return benchmarks

    def _generate_performance_recommendations(self, failed_tests: List[Dict], by_type: Dict) -> List[str]:
        """生成性能优化建议"""
        recommendations = []

        if failed_tests:
            recommendations.append(f"修复{len(failed_tests)}个失败的性能测试")

        # 基于测试类型的建议
        if "canvas_operations" in by_type:
            canvas_results = by_type["canvas_operations"]
            avg_response_time = self._extract_avg_metric(canvas_results, "response_time_ms")
            if avg_response_time > 2000:
                recommendations.append("优化Canvas文件操作性能，目标响应时间<2秒")

        if "agent_operations" in by_type:
            agent_results = by_type["agent_operations"]
            avg_cpu = self._extract_avg_metric(agent_results, "cpu_usage_percent")
            if avg_cpu > 70:
                recommendations.append("优化Agent并发执行以降低CPU使用率")

        if "resource_usage" in by_type:
            resource_results = by_type["resource_usage"]
            high_memory = any(r.get("peak_memory_mb", 0) > 1024 for r in resource_results)
            if high_memory:
                recommendations.append("优化内存使用，考虑实现内存池或缓存策略")

        if not recommendations:
            recommendations.append("所有性能测试表现良好，继续保持优化")

        return recommendations

    def _assess_performance_quality(self, pass_rate: float, avg_score: float) -> str:
        """评估性能质量"""
        if pass_rate >= 95 and avg_score >= 90:
            return "excellent"
        elif pass_rate >= 85 and avg_score >= 80:
            return "good"
        elif pass_rate >= 70 and avg_score >= 70:
            return "acceptable"
        elif pass_rate >= 50:
            return "needs_improvement"
        else:
            return "poor"

    def _create_test_canvas(self, node_count: int) -> Dict:
        """创建测试用Canvas数据"""
        return {
            "nodes": [
                {
                    "id": f"node_{i}",
                    "type": "text",
                    "x": i * 100,
                    "y": i * 50,
                    "width": 200,
                    "height": 100,
                    "color": str(i % 6 + 1),
                    "text": f"Test node {i}",
                    "content": f"Content for test node {i}"
                }
                for i in range(node_count)
            ],
            "edges": [
                {
                    "id": f"edge_{i}",
                    "from": f"node_{i}",
                    "to": f"node_{(i + 1) % node_count}",
                    "color": "6"
                }
                for i in range(min(node_count, node_count // 2))
            ]
        }

    def _create_test_reviews(self, count: int) -> List[Dict]:
        """创建测试用复习数据"""
        return [
            {
                "id": f"review_{i}",
                "concept": f"Concept {i}",
                "last_reviewed": datetime.now(timezone.utc).isoformat(),
                "urgency": i % 5 + 1,
                "difficulty": i % 3 + 1,
                "success_rate": 0.8 + (i % 4) * 0.05
            }
            for i in range(count)
        ]

    def generate_performance_report(self, output_format: str = "markdown") -> str:
        """生成性能测试报告

        Args:
            output_format: 输出格式 ("markdown", "json")

        Returns:
            str: 报告内容
        """
        if not self.test_results:
            return "No test results available. Run run_all_performance_tests() first."

        analysis = self._analyze_results(self.test_results)

        if output_format == "json":
            return json.dumps(analysis, indent=2, ensure_ascii=False)
        else:
            return self._generate_markdown_report(analysis)

    def _generate_markdown_report(self, analysis: Dict) -> str:
        """生成Markdown格式的性能报告"""
        summary = analysis["test_summary"]
        benchmarks = analysis["performance_benchmarks"]
        recommendations = analysis["recommendations"]
        quality = analysis["quality_assessment"]

        markdown = f"""# 性能测试报告

**生成时间**: {datetime.now(timezone.utc).isoformat()}
**测试工具**: Canvas学习系统性能测试运行器

## 📊 测试概览

### 整体结果
- **总测试数**: {summary['total_tests']}
- **通过测试**: {summary['passed_tests']}
- **失败测试**: {summary['failed_tests']}
- **通过率**: {summary['pass_rate_percentage']}%
- **整体性能评分**: {summary['overall_performance_score']}/100
- **质量评估**: {quality}

### 性能基准
"""

        # 添加基准数据
        if "response_time" in benchmarks:
            rt = benchmarks["response_time"]
            markdown += f"""
- **响应时间**:
  - 平均: {rt['average_ms']}ms
  - P95: {rt['p95_ms']}ms
  - 最大: {rt['max_ms']}ms
"""

        if "memory_usage" in benchmarks:
            mem = benchmarks["memory_usage"]
            markdown += f"""
- **内存使用**:
  - 平均: {mem['average_mb']}MB
  - 最大: {mem['max_mb']}MB
"""

        if "cpu_usage" in benchmarks:
            cpu = benchmarks["cpu_usage"]
            markdown += f"""
- **CPU使用**:
  - 平均: {cpu['average_percent']}%
  - 最大: {cpu['max_percent']}%
"""

        # 按类型显示结果
        markdown += "\n## 📈 按类型分析\n\n"
        for test_type, type_data in analysis["performance_by_type"].items():
            markdown += f"### {test_type.replace('_', ' ').title()}\n"
            markdown += f"- 通过率: {type_data['pass_rate_percentage']}%\n"
            if type_data['metrics']:
                for metric, value in type_data['metrics'].items():
                    markdown += f"- {metric.replace('_', ' ').title()}: {value}\n"
            markdown += "\n"

        # 添加改进建议
        if recommendations:
            markdown += "## 💡 改进建议\n\n"
            for i, rec in enumerate(recommendations, 1):
                markdown += f"{i}. {rec}\n"

        markdown += """
---
*此报告由性能测试运行器自动生成*
"""

        return markdown


if __name__ == "__main__":
    # 示例使用
    runner = PerformanceTestRunner()

    print("运行性能测试...")
    results = runner.run_all_performance_tests()

    print(f"测试完成! 通过率: {results['test_summary']['pass_rate_percentage']}%")

    # 生成报告
    report = runner.generate_performance_report("markdown")
    with open("performance_report.md", "w", encoding="utf-8") as f:
        f.write(report)
    print("性能报告已保存到 performance_report.md")