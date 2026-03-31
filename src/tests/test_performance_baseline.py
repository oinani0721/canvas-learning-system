"""
Canvas性能基准管理和回归检测系统

该模块提供性能基准的建立、管理、比较和回归检测功能，
确保Canvas系统性能的持续监控和优化。

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-10-22
"""

import json
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from test_canvas_performance import PerformanceTestResult, TestEnvironment


@dataclass
class PerformanceBaseline:
    """性能基准数据模型"""

    baseline_id: str
    created_at: str
    test_environment: TestEnvironment
    baseline_metrics: Dict[str, Any]
    version: str = "1.0"
    description: str = ""


@dataclass
class RegressionTestResult:
    """回归测试结果"""

    test_timestamp: str
    baseline_id: str
    current_results: List[PerformanceTestResult]
    regression_detected: bool
    performance_changes: Dict[str, Any]
    recommendations: List[str]
    overall_score: float  # 0-100分，越高越好


class PerformanceBaselineManager:
    """性能基准管理器"""

    def __init__(self, baseline_file: str = "tests/performance_baseline.json"):
        """
        初始化基准管理器

        Args:
            baseline_file: 基准数据文件路径
        """
        self.baseline_file = Path(baseline_file)
        self.baseline_file.parent.mkdir(parents=True, exist_ok=True)
        self.baselines = self._load_baselines()

        # 性能回归检测阈值
        self.regression_thresholds = {
            "processing_time_degradation": 20.0,  # 处理时间增加20%视为回归
            "memory_usage_increase": 30.0,  # 内存使用增加30%视为回归
            "layout_quality_decrease": 15.0,  # 布局质量下降15%视为回归
            "overlap_count_increase": 25.0,  # 重叠数量增加25%视为回归
            "success_rate_decrease": 5.0,  # 成功率下降5%视为回归
        }

        # 性能改进奖励阈值
        self.improvement_thresholds = {
            "processing_time_improvement": 15.0,  # 处理时间减少15%视为改进
            "memory_usage_reduction": 20.0,  # 内存使用减少20%视为改进
            "layout_quality_increase": 10.0,  # 布局质量提升10%视为改进
            "overlap_count_reduction": 30.0,  # 重叠数量减少30%视为改进
            "success_rate_increase": 2.0,  # 成功率提升2%视为改进
        }

    def _load_baselines(self) -> Dict[str, PerformanceBaseline]:
        """加载已有的基准数据"""
        if not self.baseline_file.exists():
            return {}

        try:
            with open(self.baseline_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            baselines = {}
            for baseline_id, baseline_data in data.items():
                baseline = PerformanceBaseline(
                    baseline_id=baseline_data["baseline_id"],
                    created_at=baseline_data["created_at"],
                    test_environment=TestEnvironment(
                        **baseline_data["test_environment"]
                    ),
                    baseline_metrics=baseline_data["baseline_metrics"],
                    version=baseline_data.get("version", "1.0"),
                    description=baseline_data.get("description", ""),
                )
                baselines[baseline_id] = baseline

            return baselines

        except Exception as e:
            print(f"警告: 加载基准数据失败 - {e}")
            return {}

    def _save_baselines(self) -> None:
        """保存基准数据到文件"""
        try:
            data = {}
            for baseline_id, baseline in self.baselines.items():
                data[baseline_id] = {
                    "baseline_id": baseline.baseline_id,
                    "created_at": baseline.created_at,
                    "test_environment": {
                        "python_version": baseline.test_environment.python_version,
                        "platform": baseline.test_environment.platform,
                        "cpu_count": baseline.test_environment.cpu_count,
                        "memory_gb": baseline.test_environment.memory_gb,
                        "canvas_utils_version": baseline.test_environment.canvas_utils_version,
                        "test_machine_id": baseline.test_environment.test_machine_id,
                    },
                    "baseline_metrics": baseline.baseline_metrics,
                    "version": baseline.version,
                    "description": baseline.description,
                }

            with open(self.baseline_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"错误: 保存基准数据失败 - {e}")

    def establish_baseline(
        self,
        test_results: List[PerformanceTestResult],
        test_environment: TestEnvironment,
        description: str = "",
    ) -> str:
        """
        建立性能基准

        Args:
            test_results: 性能测试结果列表
            test_environment: 测试环境信息
            description: 基准描述

        Returns:
            str: 基准ID
        """
        # 过滤成功的测试结果
        successful_results = [r for r in test_results if r.success]

        if not successful_results:
            raise ValueError("没有成功的测试结果，无法建立基准")

        # 计算基准指标
        baseline_metrics = self._calculate_baseline_metrics(successful_results)

        # 创建基准
        baseline_id = f"baseline_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        baseline = PerformanceBaseline(
            baseline_id=baseline_id,
            created_at=datetime.now().isoformat(),
            test_environment=test_environment,
            baseline_metrics=baseline_metrics,
            description=description,
        )

        # 保存基准
        self.baselines[baseline_id] = baseline
        self._save_baselines()

        print(f"性能基准已建立: {baseline_id}")
        return baseline_id

    def compare_with_baseline(
        self,
        current_results: List[PerformanceTestResult],
        baseline_id: Optional[str] = None,
    ) -> RegressionTestResult:
        """
        与基准进行比较，检测性能回归

        Args:
            current_results: 当前测试结果
            baseline_id: 基准ID，如果为None则使用最新基准

        Returns:
            RegressionTestResult: 回归测试结果
        """
        if not self.baselines:
            raise ValueError("没有可用的基准数据")

        # 选择基准
        if baseline_id is None:
            # 选择最新的基准
            baseline_id = max(
                self.baselines.keys(), key=lambda k: self.baselines[k].created_at
            )

        baseline = self.baselines[baseline_id]

        # 分析性能变化
        performance_changes = self._analyze_performance_changes(
            current_results, baseline.baseline_metrics
        )

        # 检测回归
        regression_detected = self._detect_regression(performance_changes)

        # 生成建议
        recommendations = self._generate_recommendations(
            performance_changes, regression_detected
        )

        # 计算总体评分
        overall_score = self._calculate_overall_score(performance_changes)

        return RegressionTestResult(
            test_timestamp=datetime.now().isoformat(),
            baseline_id=baseline_id,
            current_results=current_results,
            regression_detected=regression_detected,
            performance_changes=performance_changes,
            recommendations=recommendations,
            overall_score=overall_score,
        )

    def update_baseline(
        self,
        new_results: List[PerformanceTestResult],
        reason: str,
        baseline_id: Optional[str] = None,
    ) -> str:
        """
        更新性能基准

        Args:
            new_results: 新的测试结果
            reason: 更新原因
            baseline_id: 要更新的基准ID，如果为None则创建新基准

        Returns:
            str: 基准ID
        """
        if baseline_id is None:
            # 创建新基准
            from test_canvas_performance import CanvasPerformanceTester

            tester = CanvasPerformanceTester()
            return self.establish_baseline(
                new_results, tester.test_environment, f"基准更新: {reason}"
            )

        if baseline_id not in self.baselines:
            raise ValueError(f"基准ID不存在: {baseline_id}")

        # 更新现有基准的指标
        baseline = self.baselines[baseline_id]
        successful_results = [r for r in new_results if r.success]

        if successful_results:
            baseline.baseline_metrics = self._calculate_baseline_metrics(
                successful_results
            )
            baseline.description = f"{baseline.description} | 更新: {reason}"
            self._save_baselines()

        return baseline_id

    def get_baseline_metrics(self, baseline_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取当前基准指标

        Args:
            baseline_id: 基准ID，如果为None则返回最新基准

        Returns:
            Dict[str, Any]: 基准指标
        """
        if not self.baselines:
            return {}

        if baseline_id is None:
            baseline_id = max(
                self.baselines.keys(), key=lambda k: self.baselines[k].created_at
            )

        return self.baselines[baseline_id].baseline_metrics

    def list_baselines(self) -> List[Dict[str, Any]]:
        """列出所有基准"""
        return [
            {
                "baseline_id": baseline.baseline_id,
                "created_at": baseline.created_at,
                "version": baseline.version,
                "description": baseline.description,
                "test_environment": {
                    "python_version": baseline.test_environment.python_version,
                    "platform": baseline.test_environment.platform,
                    "cpu_count": baseline.test_environment.cpu_count,
                    "memory_gb": baseline.test_environment.memory_gb,
                },
            }
            for baseline in sorted(
                self.baselines.values(), key=lambda b: b.created_at, reverse=True
            )
        ]

    def _calculate_baseline_metrics(
        self, results: List[PerformanceTestResult]
    ) -> Dict[str, Any]:
        """计算基准指标"""
        if not results:
            return {}

        # 按节点数量分组
        node_groups = {}
        for result in results:
            node_count = result.node_count
            if node_count not in node_groups:
                node_groups[node_count] = []
            node_groups[node_count].append(result)

        # 计算各节点数组的基准指标
        baseline_metrics = {
            "created_at": datetime.now().isoformat(),
            "total_tests": len(results),
            "success_rate": len(results) / len(results) * 100,
            "node_groups": {},
            "overall_stats": {},
        }

        processing_times = []
        memory_usages = []
        quality_scores = []

        for node_count, group_results in node_groups.items():
            group_times = [r.processing_time_ms for r in group_results]
            group_memories = [r.memory_usage_mb for r in group_results]
            group_qualities = [r.layout_quality_score for r in group_results]

            baseline_metrics["node_groups"][str(node_count)] = {
                "count": len(group_results),
                "processing_time": {
                    "avg_ms": sum(group_times) / len(group_times),
                    "min_ms": min(group_times),
                    "max_ms": max(group_times),
                    "p95_ms": sorted(group_times)[int(len(group_times) * 0.95)],
                },
                "memory_usage": {
                    "avg_mb": sum(group_memories) / len(group_memories),
                    "min_mb": min(group_memories),
                    "max_mb": max(group_memories),
                },
                "layout_quality": {
                    "avg_score": sum(group_qualities) / len(group_qualities),
                    "min_score": min(group_qualities),
                    "max_score": max(group_qualities),
                },
            }

            processing_times.extend(group_times)
            memory_usages.extend(group_memories)
            quality_scores.extend(group_qualities)

        # 计算总体统计
        baseline_metrics["overall_stats"] = {
            "processing_time": {
                "avg_ms": sum(processing_times) / len(processing_times),
                "min_ms": min(processing_times),
                "max_ms": max(processing_times),
                "p95_ms": sorted(processing_times)[int(len(processing_times) * 0.95)],
            },
            "memory_usage": {
                "avg_mb": sum(memory_usages) / len(memory_usages),
                "min_mb": min(memory_usages),
                "max_mb": max(memory_usages),
            },
            "layout_quality": {
                "avg_score": sum(quality_scores) / len(quality_scores),
                "min_score": min(quality_scores),
                "max_score": max(quality_scores),
            },
        }

        return baseline_metrics

    def _analyze_performance_changes(
        self,
        current_results: List[PerformanceTestResult],
        baseline_metrics: Dict[str, Any],
    ) -> Dict[str, Any]:
        """分析性能变化"""
        successful_current = [r for r in current_results if r.success]

        if not successful_current:
            return {"error": "没有成功的当前测试结果"}

        # 按节点数量分组当前结果
        current_node_groups = {}
        for result in successful_current:
            node_count = result.node_count
            if node_count not in current_node_groups:
                current_node_groups[node_count] = []
            current_node_groups[node_count].append(result)

        changes = {
            "overall_comparison": {},
            "node_group_comparisons": {},
            "performance_trends": {},
        }

        # 总体比较
        current_times = [r.processing_time_ms for r in successful_current]
        current_memories = [r.memory_usage_mb for r in successful_current]
        current_qualities = [r.layout_quality_score for r in successful_current]

        baseline_stats = baseline_metrics.get("overall_stats", {})

        changes["overall_comparison"] = {
            "processing_time_change_pct": self._calculate_percentage_change(
                sum(current_times) / len(current_times),
                baseline_stats.get("processing_time", {}).get("avg_ms"),
            ),
            "memory_usage_change_pct": self._calculate_percentage_change(
                sum(current_memories) / len(current_memories),
                baseline_stats.get("memory_usage", {}).get("avg_mb"),
            ),
            "layout_quality_change_pct": self._calculate_percentage_change(
                sum(current_qualities) / len(current_qualities),
                baseline_stats.get("layout_quality", {}).get("avg_score"),
            ),
        }

        # 节点组比较
        baseline_node_groups = baseline_metrics.get("node_groups", {})
        for node_count, current_group in current_node_groups.items():
            node_count_str = str(node_count)
            if node_count_str in baseline_node_groups:
                baseline_group = baseline_node_groups[node_count_str]

                current_times = [r.processing_time_ms for r in current_group]
                current_memories = [r.memory_usage_mb for r in current_group]
                current_qualities = [r.layout_quality_score for r in current_group]

                changes["node_group_comparisons"][node_count_str] = {
                    "processing_time_change_pct": self._calculate_percentage_change(
                        sum(current_times) / len(current_times),
                        baseline_group.get("processing_time", {}).get("avg_ms"),
                    ),
                    "memory_usage_change_pct": self._calculate_percentage_change(
                        sum(current_memories) / len(current_memories),
                        baseline_group.get("memory_usage", {}).get("avg_mb"),
                    ),
                    "layout_quality_change_pct": self._calculate_percentage_change(
                        sum(current_qualities) / len(current_qualities),
                        baseline_group.get("layout_quality", {}).get("avg_score"),
                    ),
                }

        return changes

    def _calculate_percentage_change(
        self, current: float, baseline: Optional[float]
    ) -> float:
        """计算百分比变化"""
        if baseline is None or baseline == 0:
            return 0.0
        return ((current - baseline) / baseline) * 100

    def _detect_regression(self, performance_changes: Dict[str, Any]) -> bool:
        """检测性能回归"""
        overall = performance_changes.get("overall_comparison", {})

        # 检查各项指标是否超过回归阈值
        regressions = []

        processing_change = overall.get("processing_time_change_pct", 0)
        if (
            processing_change
            > self.regression_thresholds["processing_time_degradation"]
        ):
            regressions.append(f"处理时间增加{processing_change:.1f}%")

        memory_change = overall.get("memory_usage_change_pct", 0)
        if memory_change > self.regression_thresholds["memory_usage_increase"]:
            regressions.append(f"内存使用增加{memory_change:.1f}%")

        quality_change = overall.get("layout_quality_change_pct", 0)
        if quality_change < -self.regression_thresholds["layout_quality_decrease"]:
            regressions.append(f"布局质量下降{abs(quality_change):.1f}%")

        return len(regressions) > 0

    def _generate_recommendations(
        self, performance_changes: Dict[str, Any], regression_detected: bool
    ) -> List[str]:
        """生成优化建议"""
        recommendations = []
        overall = performance_changes.get("overall_comparison", {})

        processing_change = overall.get("processing_time_change_pct", 0)
        memory_change = overall.get("memory_usage_change_pct", 0)
        quality_change = overall.get("layout_quality_change_pct", 0)

        if regression_detected:
            recommendations.append("⚠️ 检测到性能回归，建议检查最近的代码变更")
        else:
            recommendations.append("✅ 未检测到明显的性能回归")

        if (
            processing_change
            > self.improvement_thresholds["processing_time_improvement"]
        ):
            recommendations.append("🚀 处理时间显著改善，继续保持")
        elif (
            processing_change
            > self.regression_thresholds["processing_time_degradation"]
        ):
            recommendations.append("🐌 处理时间显著增加，建议优化算法或检查瓶颈")

        if memory_change > self.regression_thresholds["memory_usage_increase"]:
            recommendations.append("💾 内存使用增加，建议检查内存泄漏或优化数据结构")
        elif memory_change < -self.improvement_thresholds["memory_usage_reduction"]:
            recommendations.append("🎯 内存使用显著优化，表现良好")

        if quality_change < -self.regression_thresholds["layout_quality_decrease"]:
            recommendations.append("📐 布局质量下降，建议检查布局算法参数")
        elif quality_change > self.improvement_thresholds["layout_quality_increase"]:
            recommendations.append("✨ 布局质量提升，优化效果明显")

        return recommendations

    def _calculate_overall_score(self, performance_changes: Dict[str, Any]) -> float:
        """计算总体性能评分（0-100）"""
        overall = performance_changes.get("overall_comparison", {})

        processing_change = overall.get("processing_time_change_pct", 0)
        memory_change = overall.get("memory_usage_change_pct", 0)
        quality_change = overall.get("layout_quality_change_pct", 0)

        # 基础分数
        score = 50.0

        # 处理时间评分（40%权重）
        if (
            processing_change
            < -self.improvement_thresholds["processing_time_improvement"]
        ):
            score += 20  # 显著改进
        elif (
            processing_change
            > self.regression_thresholds["processing_time_degradation"]
        ):
            score -= 25  # 显著回归
        else:
            score += processing_change * 0.5  # 线性调整

        # 内存使用评分（30%权重）
        if memory_change < -self.improvement_thresholds["memory_usage_reduction"]:
            score += 15  # 显著改进
        elif memory_change > self.regression_thresholds["memory_usage_increase"]:
            score -= 20  # 显著回归
        else:
            score += memory_change * 0.3  # 线性调整

        # 布局质量评分（30%权重）
        if quality_change > self.improvement_thresholds["layout_quality_increase"]:
            score += 15  # 显著改进
        elif quality_change < -self.regression_thresholds["layout_quality_decrease"]:
            score -= 15  # 显著回归
        else:
            score += quality_change * 0.3  # 线性调整

        return max(0.0, min(100.0, score))


# 导出主要类
__all__ = ["PerformanceBaselineManager", "PerformanceBaseline", "RegressionTestResult"]
